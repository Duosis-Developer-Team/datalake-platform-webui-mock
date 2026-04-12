"""Mock Settings shell — same routes as GUI, no RBAC."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from src.pages.settings import dashboard as settings_dashboard
from src.pages.settings.iam import audit as iam_audit
from src.pages.settings.iam import auth as iam_auth
from src.pages.settings.iam import permissions as iam_permissions
from src.pages.settings.iam import roles as iam_roles
from src.pages.settings.iam import teams as iam_teams
from src.pages.settings.iam import users as iam_users
from src.pages.settings.integrations import auranotify as int_auranotify
from src.pages.settings.integrations import ldap as int_ldap
from src.pages.settings.integrations import overview as int_overview

IAM_TABS = [
    ("/settings/iam/users", "Users"),
    ("/settings/iam/teams", "Teams"),
    ("/settings/iam/roles", "Roles"),
    ("/settings/iam/permissions", "Permissions"),
    ("/settings/iam/auth", "Auth"),
    ("/settings/iam/audit", "Audit Log"),
]

INT_TABS = [
    ("/settings/integrations", "Overview"),
    ("/settings/integrations/ldap", "LDAP"),
    ("/settings/integrations/auranotify", "AuraNotify"),
]

LEGACY_REDIRECTS: dict[str, str] = {
    "/settings/users": "/settings/iam/users",
    "/settings/roles": "/settings/iam/roles",
    "/settings/permissions": "/settings/iam/permissions",
    "/settings/teams": "/settings/iam/teams",
    "/settings/auth": "/settings/iam/auth",
    "/settings/audit": "/settings/iam/audit",
    "/settings/ldap": "/settings/integrations/ldap",
}

_PAGE_BUILDERS: dict[str, callable] = {
    "/settings": settings_dashboard.build_layout,
    "/settings/iam/users": iam_users.build_layout,
    "/settings/iam/teams": iam_teams.build_layout,
    "/settings/iam/roles": iam_roles.build_layout,
    "/settings/iam/permissions": iam_permissions.build_layout,
    "/settings/iam/auth": iam_auth.build_layout,
    "/settings/iam/audit": iam_audit.build_layout,
    "/settings/integrations": int_overview.build_layout,
    "/settings/integrations/ldap": int_ldap.build_layout,
    "/settings/integrations/auranotify": int_auranotify.build_layout,
}


def _normalize(pathname: str) -> str:
    p = (pathname or "/settings").rstrip("/") or "/settings"
    p = LEGACY_REDIRECTS.get(p, p)
    if p == "/settings/iam":
        return "/settings/iam/users"
    return p


def _section(p: str) -> str:
    if p in ("/settings", "/settings/"):
        return "overview"
    if p.startswith("/settings/iam"):
        return "iam"
    if p.startswith("/settings/integrations"):
        return "integrations"
    return "overview"


def _breadcrumb(p: str) -> str:
    s = _section(p)
    if s == "overview":
        return "Settings › Overview"
    if s == "iam":
        return "Settings › Identity & Access Management"
    return "Settings › Integrations"


def _nav_btn_props(*, active: bool) -> dict:
    if active:
        return {
            "variant": "filled",
            "color": "indigo",
            "styles": {
                "root": {
                    "background": "linear-gradient(135deg, #552cf8 0%, #a092ff 100%)",
                    "border": "none",
                    "color": "#ffffff",
                }
            },
        }
    return {"variant": "light", "color": "indigo"}


def _top_nav(current: str) -> dmc.Group:
    cur = current.rstrip("/")
    return dmc.Group(
        gap="sm",
        children=[
            dmc.Anchor(
                dmc.Button(
                    "Overview",
                    leftSection=DashIconify(icon="solar:widget-2-bold-duotone", width=16),
                    radius="md",
                    **_nav_btn_props(active=cur in ("/settings", "")),
                ),
                href="/settings",
                underline=False,
            ),
            dmc.Anchor(
                dmc.Button(
                    "Identity & Access",
                    leftSection=DashIconify(icon="solar:shield-user-bold-duotone", width=16),
                    radius="md",
                    **_nav_btn_props(active=_section(current) == "iam"),
                ),
                href="/settings/iam/users",
                underline=False,
            ),
            dmc.Anchor(
                dmc.Button(
                    "Integrations",
                    leftSection=DashIconify(icon="solar:link-round-angle-bold-duotone", width=16),
                    radius="md",
                    **_nav_btn_props(active=_section(current) == "integrations"),
                ),
                href="/settings/integrations",
                underline=False,
            ),
        ],
    )


def _sub_nav(current: str) -> html.Div | None:
    sec = _section(current)
    if sec == "iam":
        links = []
        for href, label in IAM_TABS:
            active = current.rstrip("/") == href.rstrip("/")
            links.append(
                dmc.Anchor(
                    dmc.Button(
                        label,
                        variant="subtle" if not active else "light",
                        color="indigo",
                        size="xs",
                        style={
                            "borderBottom": "2px solid #552cf8" if active else "2px solid transparent",
                            "borderRadius": 0,
                        },
                    ),
                    href=href,
                    underline=False,
                )
            )
        return html.Div(
            style={"borderBottom": "1px solid #eef1f4", "paddingBottom": "8px", "marginBottom": "16px"},
            children=[dmc.Group(gap="xs", children=links)],
        )
    if sec == "integrations":
        links = []
        for href, label in INT_TABS:
            active = current.rstrip("/") == href.rstrip("/")
            links.append(
                dmc.Anchor(
                    dmc.Button(
                        label,
                        variant="subtle" if not active else "light",
                        color="indigo",
                        size="xs",
                        style={
                            "borderBottom": "2px solid #552cf8" if active else "2px solid transparent",
                            "borderRadius": 0,
                        },
                    ),
                    href=href,
                    underline=False,
                )
            )
        return html.Div(
            style={"borderBottom": "1px solid #eef1f4", "paddingBottom": "8px", "marginBottom": "16px"},
            children=[dmc.Group(gap="xs", children=links)],
        )
    return None


def build_settings_page(pathname: str, search: str | None = None) -> html.Div:
    p = _normalize(pathname)
    if p not in _PAGE_BUILDERS:
        p = "/settings"
    builder = _PAGE_BUILDERS[p]
    body = builder(search=search)
    sub = _sub_nav(p)
    header = dmc.Paper(
        p="md",
        radius="md",
        mb="md",
        withBorder=True,
        style={
            "position": "sticky",
            "top": 0,
            "zIndex": 20,
            "background": "rgba(255,255,255,0.92)",
            "backdropFilter": "blur(10px)",
        },
        children=[
            dmc.Group(
                justify="space-between",
                mb="sm",
                children=[
                    dmc.Stack(
                        gap=2,
                        children=[
                            dmc.Text(_breadcrumb(p), size="xs", c="dimmed", fw=600),
                            dmc.Title("Settings", order=3, c="#2B3674"),
                        ],
                    ),
                    _top_nav(p),
                ],
            ),
            sub if sub else html.Div(),
        ],
    )
    return html.Div(style={"maxWidth": "1320px", "margin": "0 auto", "padding": "0 8px 48px"}, children=[header, body])
