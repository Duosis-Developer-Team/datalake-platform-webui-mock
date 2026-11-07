"""Flask routes for login/logout and auth API."""

from __future__ import annotations

import logging
from urllib.parse import quote

from flask import Blueprint, redirect, request, session

from src.auth import service
from src.auth.config import SESSION_COOKIE_NAME
from src.auth.ldap_service import (
    apply_ldap_role_mappings,
    get_active_ldap_config,
    list_user_groups,
    map_ldap_groups_to_roles,
    try_bind_user,
    upsert_ldap_user,
)

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth_routes", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login_post():
    from src.auth.config import AUTH_DISABLED
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    nxt = request.form.get("next") or "/"
    if AUTH_DISABLED:
        return redirect(nxt or "/")
    user = service.authenticate_local(username, password)
    if not user:
        cfg = get_active_ldap_config()
        if cfg:
            ok, user_dn = try_bind_user(username, password, cfg)
            if ok and user_dn:
                uid = upsert_ldap_user(username, None, user_dn)
                groups = list_user_groups(user_dn, cfg)
                role_ids = map_ldap_groups_to_roles(int(cfg["id"]), groups)
                apply_ldap_role_mappings(uid, role_ids)
                user = service.get_user_by_id(uid)
    if not user:
        return redirect(f"/login?error=1&next={quote(nxt)}")
    token = service.create_session(
        int(user["id"]),
        request.remote_addr,
        request.headers.get("User-Agent"),
    )
    session[SESSION_COOKIE_NAME] = token
    service.audit(int(user["id"]), "login", None, request.remote_addr)
    return redirect(nxt or "/")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    tok = session.get(SESSION_COOKIE_NAME)
    service.delete_session(tok)
    session.pop(SESSION_COOKIE_NAME, None)
    return redirect("/login")


def _session_uid() -> int | None:
    tok = session.get(SESSION_COOKIE_NAME)
    u = service.get_session_user(tok)
    return int(u["id"]) if u else None


def _perm_edit(uid: int, code: str) -> bool:
    from src.auth.permission_service import can_edit

    return can_edit(uid, code)


@auth_bp.route("/settings/permission-add", methods=["POST"])
def settings_permission_add():
    uid = _session_uid()
    if uid is None:
        return redirect("/login")
    if not _perm_edit(uid, "page:settings_permissions"):
        return redirect("/settings/iam/permissions?denied=1")
    code = (request.form.get("code") or "").strip()
    name = (request.form.get("name") or "").strip()
    parent_code = (request.form.get("parent_code") or "").strip() or None
    resource_type = (request.form.get("resource_type") or "section").strip()
    route_pattern = (request.form.get("route_pattern") or "").strip() or None
    if not code or not name:
        return redirect("/settings/iam/permissions?err=1")
    from src.services import admin_client as settings_crud

    try:
        settings_crud.insert_dynamic_permission(code, name, parent_code, resource_type, route_pattern)
        service.audit(uid, "settings_permission_add", code, request.remote_addr)
    except Exception as e:
        logger.warning("permission add: %s", e)
        return redirect("/settings/iam/permissions?err=1")
    return redirect("/settings/iam/permissions")


@auth_bp.route("/settings/ldap-save", methods=["POST"])
def settings_ldap_save():
    uid = _session_uid()
    if uid is None:
        return redirect("/login")
    if not _perm_edit(uid, "page:settings_ldap"):
        return redirect("/settings/integrations/ldap?denied=1")
    ldap_id = request.form.get("ldap_id") or None
    name = request.form.get("name") or "default"
    server_primary = request.form.get("server_primary") or ""
    server_secondary = (request.form.get("server_secondary") or "").strip() or None
    port = int(request.form.get("port") or "389")
    use_ssl = (request.form.get("use_ssl") or "0").strip() in ("1", "true", "True", "on")
    bind_dn = request.form.get("bind_dn") or ""
    bind_pw = request.form.get("bind_password") or ""
    search_base = request.form.get("search_base_dn") or ""
    user_filter = request.form.get("user_search_filter") or "(sAMAccountName={username})"
    from src.services import admin_client as settings_crud

    lid = None
    if ldap_id and str(ldap_id).strip().isdigit():
        lid = int(ldap_id)
    try:
        settings_crud.upsert_ldap_config(
            lid,
            name,
            server_primary,
            server_secondary,
            port,
            use_ssl,
            bind_dn,
            bind_pw,
            search_base,
            user_filter,
            True,
        )
        service.audit(uid, "settings_ldap_save", name, request.remote_addr)
    except Exception as e:
        logger.warning("ldap save: %s", e)
        return redirect("/settings/integrations/ldap?err=1")
    return redirect("/settings/integrations/ldap")


@auth_bp.route("/settings/ldap-mapping-add", methods=["POST"])
def settings_ldap_mapping_add():
    uid = _session_uid()
    if uid is None:
        return redirect("/login")
    if not _perm_edit(uid, "page:settings_ldap"):
        return redirect("/settings/integrations/ldap?denied=1")
    cid_s = request.form.get("ldap_config_id") or ""
    dn = request.form.get("ldap_group_dn") or ""
    rid_s = request.form.get("role_id") or ""
    if not cid_s.isdigit() or not rid_s.isdigit() or not dn.strip():
        return redirect("/settings/integrations/ldap?err=1")
    from src.services import admin_client as settings_crud

    settings_crud.add_ldap_group_mapping(int(cid_s), dn, int(rid_s))
    service.audit(uid, "settings_ldap_mapping_add", dn[:120], request.remote_addr)
    return redirect("/settings/integrations/ldap")


@auth_bp.route("/settings/ldap-mapping-delete", methods=["POST"])
def settings_ldap_mapping_delete():
    uid = _session_uid()
    if uid is None:
        return redirect("/login")
    if not _perm_edit(uid, "page:settings_ldap"):
        return redirect("/settings/integrations/ldap?denied=1")
    mid = request.form.get("mapping_id") or ""
    if not mid.isdigit():
        return redirect("/settings/integrations/ldap")
    from src.services import admin_client as settings_crud

    settings_crud.delete_ldap_group_mapping(int(mid))
    return redirect("/settings/integrations/ldap")

