"""Local-path role SQL on a real Postgres (DLP-023 K16; same semantics as the GUI / admin-api).

Mocked DB tests cannot validate SQL. ``settings_crud.create_role``, ``role_usage`` and
``role_usage_counts`` run their own SQL here against a throw-away schema built from
``sql/auth_schema.sql`` inside one rolled-back transaction (``tests/pg_auth_schema.py``).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.auth import settings_crud
from src.auth.role_errors import RoleNameTaken
from tests.pg_auth_schema import PgUnavailable, auth_pg, one


@pytest.fixture
def pg():
    try:
        cm = auth_pg("dlp023_mock")
        conn_ids = cm.__enter__()
    except PgUnavailable as exc:
        pytest.skip(f"local Postgres unavailable: {exc}")
    try:
        yield conn_ids
    finally:
        cm.__exit__(None, None, None)


def test_pg_create_copies_only_source_matrix_rows(pg):
    conn, ids = pg
    out = settings_crud.create_role("  Ops Copy  ", "copied", ids["ops"])
    assert out["copied_rows"] == 2
    assert out["name"] == "Ops Copy"
    cur = conn.cursor()
    cur.execute("SELECT name, description, is_system FROM roles WHERE id = %s", (out["id"],))
    assert cur.fetchone() == ("Ops Copy", "copied", False)
    cur.execute(
        "SELECT permission_id, can_view, can_edit, can_export FROM role_permissions "
        "WHERE role_id = %s ORDER BY permission_id", (out["id"],))
    assert cur.fetchall() == [(ids["page:a"], True, False, False), (ids["page:b"], True, True, False)]
    assert one(cur, "SELECT count(*) FROM role_permissions WHERE role_id = %s", (ids["ops"],)) == 2


def test_pg_create_without_copy_has_empty_matrix(pg):
    conn, _ = pg
    out = settings_crud.create_role("Blank", None, None)
    assert out["copied_rows"] == 0
    assert one(conn.cursor(), "SELECT count(*) FROM role_permissions WHERE role_id = %s", (out["id"],)) == 0


def test_pg_create_case_insensitive_duplicate_is_taken(pg):
    conn, _ = pg
    with pytest.raises(RoleNameTaken):
        settings_crud.create_role(" admin ", None, None)
    with pytest.raises(RoleNameTaken):
        settings_crud.create_role("OPERATION team", None, None)
    assert one(conn.cursor(), "SELECT count(*) FROM roles WHERE lower(name) = 'admin'") == 1


@pytest.mark.parametrize("bad", ["", "   ", None, "q" * 101], ids=["empty", "blank", "none", "101"])
def test_pg_create_invalid_name_is_value_error(pg, bad):
    conn, _ = pg
    before = one(conn.cursor(), "SELECT count(*) FROM roles")
    with pytest.raises(ValueError):
        settings_crud.create_role(bad, None, None)
    assert one(conn.cursor(), "SELECT count(*) FROM roles") == before


def test_pg_create_hundred_chars_after_trim_is_ok(pg):
    out = settings_crud.create_role("  " + "q" * 100 + "  ", None, None)
    assert out["name"] == "q" * 100


def test_pg_create_missing_source_is_lookup_error_and_inserts_nothing(pg):
    conn, _ = pg
    before = one(conn.cursor(), "SELECT count(*) FROM roles")
    with pytest.raises(LookupError):
        settings_crud.create_role("Orphan", None, 999999)
    assert one(conn.cursor(), "SELECT count(*) FROM roles") == before


def test_pg_unique_violation_from_engine_is_taken(pg):
    """A racing writer passes the pre-check; the engine's UNIQUE answers and maps to RoleNameTaken."""
    conn, _ = pg
    with patch.object(settings_crud, "_role_name_taken", return_value=False):
        with pytest.raises(RoleNameTaken):
            settings_crud.create_role("Admin", None, None)
    assert one(conn.cursor(), "SELECT count(*) FROM roles WHERE name = 'Admin'") == 1


def test_pg_usage_matches_hand_count_and_api_shape(pg):
    conn, ids = pg
    out = settings_crud.role_usage(ids["used"])
    assert set(out) == {"role", "users", "teams", "ldap_mappings", "counts"}
    assert out["role"] == {"id": ids["used"], "name": "Used Role", "is_system": False}
    assert out["users"] == [{"id": ids["direct"], "username": "direct", "display_name": "Direct"}]
    assert out["teams"] == [{"id": ids["team"], "name": "NOC", "member_count": 2}]
    assert out["ldap_mappings"] == [
        {"id": ids["mapping"], "ldap_config_id": ids["ldap"], "ldap_group_dn": "cn=ops,dc=example"}]
    cur = conn.cursor()
    hand = {
        "users": one(cur, "SELECT count(*) FROM user_roles WHERE role_id = %s", (ids["used"],)),
        "teams": one(cur, "SELECT count(*) FROM team_roles WHERE role_id = %s", (ids["used"],)),
        "ldap_mappings": one(cur, "SELECT count(*) FROM ldap_group_role_mapping WHERE role_id = %s", (ids["used"],)),
        "team_members": 1,  # teamonly; "direct" is in the team but holds the role directly
    }
    assert out["counts"] == hand == {"users": 1, "teams": 1, "ldap_mappings": 1, "team_members": 1}


def test_pg_team_members_excludes_direct_holder(pg):
    """R9: a team member who also holds the role directly is not a team-only member."""
    conn, ids = pg
    assert settings_crud.role_usage(ids["used"])["counts"]["team_members"] == 1
    conn.cursor().execute("DELETE FROM user_roles WHERE user_id = %s AND role_id = %s", (ids["direct"], ids["used"]))
    assert settings_crud.role_usage(ids["used"])["counts"]["team_members"] == 2


def test_pg_usage_missing_role_is_lookup_error(pg):
    with pytest.raises(LookupError):
        settings_crud.role_usage(999999)


def test_pg_usage_counts_equal_per_role_usage_for_every_role(pg):
    conn, ids = pg
    created = settings_crud.create_role("Fresh", None, None)["id"]
    bulk = settings_crud.role_usage_counts()
    cur = conn.cursor()
    cur.execute("SELECT id FROM roles ORDER BY id")
    role_ids = [r[0] for r in cur.fetchall()]
    assert sorted(bulk) == role_ids, "every role appears with an int key, zero usage included"
    for rid in role_ids:
        assert bulk[rid] == settings_crud.role_usage(rid)["counts"], rid
    zero = {"users": 0, "teams": 0, "team_members": 0, "ldap_mappings": 0}
    assert bulk[ids["guest"]] == zero
    assert bulk[created] == zero
    assert bulk[ids["used"]] == {"users": 1, "teams": 1, "team_members": 1, "ldap_mappings": 1}
    assert bulk[ids["admin"]] == {"users": 1, "teams": 0, "team_members": 0, "ldap_mappings": 0}
