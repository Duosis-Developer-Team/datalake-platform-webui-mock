"""Mock admin client mirrors the GUI role-client functions (DLP-023 K16).

``create_role`` / ``role_usage`` / ``role_usage_counts`` follow ``src/services/admin_client.py`` of the
GUI: same return shapes, same errors (``RoleNameTaken`` / ``ValueError`` / ``LookupError``).
State is isolated per test with ``monkeypatch.setattr`` (the module keeps mutable globals).
"""

from __future__ import annotations

import pytest

from src.auth.role_errors import RoleNameTaken
from src.services import mock_admin_client as m


@pytest.fixture
def state(monkeypatch):
    """Small, fully controlled IAM state: roles 1 (system), 2, 3; next role id 10."""
    monkeypatch.setattr(
        m,
        "_roles",
        [
            {"id": 1, "name": "Admin", "description": "Full access", "is_system": True},
            {"id": 2, "name": "Viewer", "description": "Read-only", "is_system": False},
            {"id": 3, "name": "Auditor", "description": None, "is_system": False},
        ],
    )
    monkeypatch.setattr(
        m,
        "_users",
        [
            {"id": 1, "username": "zed", "display_name": "Zed", "email": None, "source": "local",
             "is_active": True, "ldap_dn": None, "role_ids": [2], "team_ids": [1]},
            {"id": 2, "username": "amy", "display_name": None, "email": None, "source": "local",
             "is_active": True, "ldap_dn": None, "role_ids": [], "team_ids": [1]},
            {"id": 3, "username": "bob", "display_name": "Bob", "email": None, "source": "local",
             "is_active": False, "ldap_dn": None, "role_ids": [], "team_ids": []},
        ],
    )
    monkeypatch.setattr(
        m,
        "_teams",
        [
            {"id": 1, "name": "Zeta", "description": None, "role_ids": [2], "parent_id": None,
             "created_by": 1, "created_by_name": "zed"},
            {"id": 2, "name": "Alpha", "description": None, "role_ids": [2, 3], "parent_id": None,
             "created_by": 1, "created_by_name": "zed"},
        ],
    )
    # team 1 = {zed, amy}; team 2 = {amy}
    monkeypatch.setattr(m, "_team_members", {(1, 1), (1, 2), (2, 2)})
    monkeypatch.setattr(
        m,
        "_role_permissions",
        {
            (2, 100): {"can_view": True, "can_edit": False, "can_export": False},
            (2, 101): {"can_view": True, "can_edit": True, "can_export": False},
            (3, 100): {"can_view": False, "can_edit": False, "can_export": True},
        },
    )
    monkeypatch.setattr(m, "_next_rid", 10)
    return m


# --- create_role -----------------------------------------------------------------------------


def test_create_role_returns_id_name_copied_rows_and_appends_non_system(state):
    out = m.create_role("  Operator  ", "Ops team")
    assert out == {"id": 10, "name": "Operator", "copied_rows": 0}
    row = next(r for r in m._roles if r["id"] == 10)
    assert row == {"id": 10, "name": "Operator", "description": "Ops team", "is_system": False}
    assert m._next_rid == 11


def test_create_role_defaults_description_none(state):
    m.create_role("Operator")
    assert next(r for r in m._roles if r["id"] == 10)["description"] is None


def test_create_role_ids_increase(state):
    assert m.create_role("A1")["id"] == 10
    assert m.create_role("A2")["id"] == 11


def test_create_role_visible_in_list_roles(state):
    m.create_role("Operator")
    assert "Operator" in [r["name"] for r in m.list_roles()]


@pytest.mark.parametrize("taken", ["viewer", "VIEWER", "  Viewer  ", "aDmIn"])
def test_create_role_taken_name_case_insensitive_after_trim(state, taken):
    before = [dict(r) for r in m._roles]
    with pytest.raises(RoleNameTaken):
        m.create_role(taken)
    assert m._roles == before
    assert m._next_rid == 10  # a rejected create does not burn an id


@pytest.mark.parametrize("bad", [None, "", "   "])
def test_create_role_empty_name_is_value_error(state, bad):
    with pytest.raises(ValueError):
        m.create_role(bad)
    assert m._next_rid == 10


def test_create_role_name_length_limits(state):
    with pytest.raises(ValueError):
        m.create_role("x" * 101)
    assert m.create_role("y" * 100)["name"] == "y" * 100
    # 100 chars after trimming is fine even if the raw string is longer
    assert m.create_role("  " + "z" * 100 + "  ")["name"] == "z" * 100


def test_role_name_taken_is_not_a_value_error():
    # GUI distinguishes 409 (taken) from 422 (invalid); the mock must too.
    assert not issubclass(RoleNameTaken, ValueError)


def test_create_role_copies_matrix_rows_independently(state):
    out = m.create_role("Copy of Viewer", None, copy_from_role_id=2)
    assert out == {"id": 10, "name": "Copy of Viewer", "copied_rows": 2}
    assert m._role_permissions[(10, 100)] == m._role_permissions[(2, 100)]
    assert m._role_permissions[(10, 101)] == {"can_view": True, "can_edit": True, "can_export": False}
    # independent copy: editing the new role must not touch the source
    m._role_permissions[(10, 100)]["can_edit"] = True
    assert m._role_permissions[(2, 100)]["can_edit"] is False
    # the source keeps its own rows, other roles are untouched
    assert (3, 100) in m._role_permissions
    assert not any(rid == 10 for (rid, _pid) in m._role_permissions if rid != 10)


def test_create_role_copy_from_role_without_rows_copies_zero(state):
    out = m.create_role("Empty copy", None, copy_from_role_id=1)
    assert out["copied_rows"] == 0


def test_create_role_missing_copy_source_is_lookup_error_and_creates_nothing(state):
    before = [dict(r) for r in m._roles]
    perms_before = {k: dict(v) for k, v in m._role_permissions.items()}
    with pytest.raises(LookupError):
        m.create_role("Ghost copy", None, copy_from_role_id=999)
    assert m._roles == before
    assert m._role_permissions == perms_before
    assert m._next_rid == 10


def test_create_role_name_checked_before_copy_source(state):
    # same order as the GUI path: name rules first, then the source lookup
    with pytest.raises(RoleNameTaken):
        m.create_role("Viewer", None, copy_from_role_id=999)


# --- role_usage ------------------------------------------------------------------------------


def test_role_usage_shape_and_counts(state):
    out = m.role_usage(2)
    assert set(out) == {"role", "users", "teams", "ldap_mappings", "counts"}
    assert out["role"] == {"id": 2, "name": "Viewer", "is_system": False}
    # zed holds role 2 directly; amy only through teams 1 and 2; bob has nothing
    assert out["users"] == [{"id": 1, "username": "zed", "display_name": "Zed"}]
    # teams ordered by name; member_count from team_members
    assert out["teams"] == [
        {"id": 2, "name": "Alpha", "member_count": 1},
        {"id": 1, "name": "Zeta", "member_count": 2},
    ]
    assert out["ldap_mappings"] == []
    assert out["counts"] == {"users": 1, "teams": 2, "team_members": 1, "ldap_mappings": 0}


def test_role_usage_team_members_counts_only_team_only_holders(state):
    # amy is in both role-2 teams: counted once. zed is in team 1 but holds the role directly: not counted.
    assert m.role_usage(2)["counts"]["team_members"] == 1


def test_role_usage_users_sorted_by_username(state):
    state._users[1]["role_ids"] = [2]  # amy now also direct
    names = [u["username"] for u in m.role_usage(2)["users"]]
    assert names == ["amy", "zed"]
    assert m.role_usage(2)["counts"]["team_members"] == 0


def test_role_usage_counts_inactive_users(state):
    state._users[2]["role_ids"] = [3]  # bob, inactive, direct holder of role 3
    assert [u["username"] for u in m.role_usage(3)["users"]] == ["bob"]


def test_role_usage_unused_role_is_all_zero(state):
    out = m.role_usage(1)
    assert out["users"] == [] and out["teams"] == [] and out["ldap_mappings"] == []
    assert out["counts"] == {"users": 0, "teams": 0, "team_members": 0, "ldap_mappings": 0}
    assert out["role"]["is_system"] is True


def test_role_usage_ldap_mappings_always_empty(state):
    assert m.role_usage(2)["ldap_mappings"] == []
    assert m.role_usage(3)["counts"]["ldap_mappings"] == 0


def test_role_usage_missing_role_is_lookup_error(state):
    with pytest.raises(LookupError):
        m.role_usage(999)


def test_role_usage_for_freshly_created_role_is_empty(state):
    rid = m.create_role("Fresh")["id"]
    assert m.role_usage(rid)["counts"] == {"users": 0, "teams": 0, "team_members": 0, "ldap_mappings": 0}


# --- role_usage_counts -----------------------------------------------------------------------


def test_role_usage_counts_every_role_with_int_keys_and_zeros(state):
    out = m.role_usage_counts()
    assert set(out) == {1, 2, 3}
    assert all(isinstance(k, int) for k in out)
    assert out[1] == {"users": 0, "teams": 0, "team_members": 0, "ldap_mappings": 0}
    assert out[2] == {"users": 1, "teams": 2, "team_members": 1, "ldap_mappings": 0}
    assert out[3] == {"users": 0, "teams": 1, "team_members": 1, "ldap_mappings": 0}


def test_role_usage_counts_agree_with_role_usage(state):
    for rid, counts in m.role_usage_counts().items():
        assert counts == m.role_usage(rid)["counts"]


def test_role_usage_counts_includes_new_role(state):
    rid = m.create_role("Fresh")["id"]
    assert m.role_usage_counts()[rid] == {"users": 0, "teams": 0, "team_members": 0, "ldap_mappings": 0}
