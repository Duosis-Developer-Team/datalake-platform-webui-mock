"""In-memory admin API stand-in for mock Settings IAM (no auth DB)."""

from __future__ import annotations

from typing import Any

# Mutable in-memory state (module-level)
_users: list[dict[str, Any]] = [
    {
        "id": 1,
        "username": "admin",
        "display_name": "Admin User",
        "email": "admin@example.com",
        "source": "local",
        "is_active": True,
        "ldap_dn": None,
        "role_ids": [1],
        "team_ids": [1],
    },
    {
        "id": 2,
        "username": "jdoe",
        "display_name": "Jane Doe",
        "email": "jdoe@example.com",
        "source": "ldap",
        "is_active": True,
        "ldap_dn": "CN=jdoe,OU=Users,DC=mock,DC=local",
        "role_ids": [2],
        "team_ids": [1],
    },
]

_roles: list[dict[str, Any]] = [
    {"id": 1, "name": "Admin", "description": "Full access", "is_system": True},
    {"id": 2, "name": "Viewer", "description": "Read-only", "is_system": False},
]

_teams: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Data Analysts",
        "description": "Analytics",
        "role_ids": [2],
        "parent_id": None,
        "created_by": 1,
        "created_by_name": "admin",
    },
    {
        "id": 2,
        "name": "Data Engineering",
        "description": None,
        "role_ids": [],
        "parent_id": None,
        "created_by": 2,
        "created_by_name": "jdoe",
    },
]

_team_members: set[tuple[int, int]] = {(1, 1), (1, 2)}

_permissions: list[dict[str, Any]] = [
    {
        "id": 1,
        "code": "page:home",
        "name": "Home",
        "description": "Main dashboard entry point.",
        "parent_id": None,
        "resource_type": "page",
        "sort_order": 0,
        "is_dynamic": False,
    },
    {
        "id": 2,
        "code": "action:export:customers",
        "name": "Export customers",
        "description": "Export customer records to file.",
        "parent_id": None,
        "resource_type": "action",
        "sort_order": 1,
        "is_dynamic": False,
    },
    {
        "id": 3,
        "code": "page:settings_audit",
        "name": "Audit Log",
        "description": "View administrative audit trail.",
        "parent_id": None,
        "resource_type": "config",
        "sort_order": 2,
        "is_dynamic": False,
    },
]

_role_permissions: dict[tuple[int, int], dict[str, bool]] = {}

_next_uid = 3
_next_rid = 3
_next_tid = 3


def _effective_user_role_ids(u: dict[str, Any]) -> set[int]:
    """Direct roles plus roles granted via team membership."""
    rids = set(int(x) for x in u.get("role_ids") or [])
    for tid in u.get("team_ids") or []:
        for t in _teams:
            if int(t["id"]) == int(tid):
                rids.update(int(x) for x in t.get("role_ids") or [])
                break
    return rids


def list_users_with_roles() -> list[dict[str, Any]]:
    out = []
    for u in _users:
        eff = _effective_user_role_ids(u)
        names = [r["name"] for r in _roles if r["id"] in eff]
        out.append(
            {
                "id": u["id"],
                "username": u["username"],
                "display_name": u["display_name"],
                "email": u["email"],
                "source": u["source"],
                "is_active": u["is_active"],
                "roles": ", ".join(sorted(names)),
            }
        )
    return out


def list_roles() -> list[dict[str, Any]]:
    return [dict(r) for r in _roles]


def list_permissions_flat() -> list[dict[str, Any]]:
    return [dict(p) for p in _permissions]


def get_role_permission_rows(role_id: int) -> list[dict[str, Any]]:
    rows = []
    for (rid, pid), flags in _role_permissions.items():
        if rid == role_id:
            rows.append(
                {
                    "permission_id": pid,
                    "can_view": flags.get("can_view", False),
                    "can_edit": flags.get("can_edit", False),
                    "can_export": flags.get("can_export", False),
                }
            )
    return rows


def bulk_set_role_matrix(role_id: int, triplets: list[tuple[int, bool, bool, bool]]) -> None:
    for pid, v, e, x in triplets:
        _role_permissions[(role_id, pid)] = {"can_view": v, "can_edit": e, "can_export": x}


def create_local_user(username: str, password: str, display_name: str | None) -> int:
    global _next_uid
    uid = _next_uid
    _next_uid += 1
    _users.append(
        {
            "id": uid,
            "username": username.strip(),
            "display_name": display_name or username.strip(),
            "email": None,
            "source": "local",
            "is_active": True,
            "ldap_dn": None,
            "role_ids": [],
            "team_ids": [],
        }
    )
    return uid


def set_user_roles(user_id: int, role_ids: list[int]) -> None:
    for u in _users:
        if u["id"] == user_id:
            u["role_ids"] = list(role_ids)
            return


def set_user_active(user_id: int, active: bool) -> None:
    for u in _users:
        if u["id"] == user_id:
            u["is_active"] = active
            return


def list_ldap_configs() -> list[dict[str, Any]]:
    return [{"id": 1, "name": "mock", "is_active": True}]


def upsert_ldap_config(*_a, **_kw) -> None:
    return


def test_ldap_connection(*_a, **_kw) -> dict[str, Any]:
    """Mock response for Settings LDAP 'Test connection' (no real bind)."""
    return {
        "ok": True,
        "bind": True,
        "search_count": 1,
        "message": "Mock: Bind OK, 1 user(s) found for query 'test'.",
    }


def list_ldap_group_mappings(_ldap_config_id: int) -> list[dict[str, Any]]:
    return []


def add_ldap_group_mapping(*_a) -> None:
    return


def delete_ldap_group_mapping(_mid: int) -> None:
    return


def list_teams() -> list[dict[str, Any]]:
    out = []
    for t in _teams:
        mc = sum(1 for (tid, _u) in _team_members if tid == t["id"])
        row = dict(t)
        row["member_count"] = mc
        rids = [int(x) for x in row.get("role_ids") or []]
        row["role_ids"] = rids
        row["roles"] = ", ".join(
            sorted(r["name"] for r in _roles if r["id"] in rids),
        )
        out.append(row)
    return out


def create_team(
    name: str,
    parent_id: int | None,
    created_by: int | None,
    description: str | None = None,
    role_ids: list[int] | None = None,
) -> int:
    global _next_tid
    tid = _next_tid
    _next_tid += 1
    _teams.append(
        {
            "id": tid,
            "name": name.strip(),
            "description": (description or "").strip() or None,
            "role_ids": list(role_ids or []),
            "parent_id": parent_id,
            "created_by": created_by,
            "created_by_name": None,
        }
    )
    return tid


def list_audit_log(limit: int = 200) -> list[dict[str, Any]]:
    from src.services.mock_data import settings_data as sd

    return sd.MOCK_AUDIT[:limit]


def insert_dynamic_permission(*_a, **_kw) -> None:
    return


def search_ldap_users(query: str) -> list[dict[str, Any]]:
    q_raw = (query or "").strip()
    q = q_raw.lower()
    sample = [
        {
            "username": "aduser1",
            "display_name": "AD User One",
            "email": "aduser1@mock.local",
            "distinguished_name": "CN=aduser1,OU=Users,DC=mock,DC=local",
        },
        {
            "username": "aduser2",
            "display_name": "AD User Two",
            "email": "aduser2@mock.local",
            "distinguished_name": "CN=aduser2,OU=Users,DC=mock,DC=local",
        },
        {
            "username": "devuser",
            "display_name": "Dev User",
            "email": "dev@mock.local",
            "distinguished_name": "CN=devuser,OU=Developers,OU=Users,DC=mock,DC=local",
        },
        {
            "username": "sales1",
            "display_name": "Sales One",
            "email": "sales1@mock.local",
            "distinguished_name": "CN=sales1,OU=Sales,DC=mock,DC=local",
        },
    ]
    if q_raw.upper().startswith("OU="):
        qdn = q_raw.lower()
        return [u for u in sample if qdn in (u.get("distinguished_name") or "").lower()]
    return [u for u in sample if q in u["username"].lower() or q in (u.get("display_name") or "").lower()]


def import_ldap_users(users: list[dict[str, Any]], role_ids: list[int], team_ids: list[int]) -> dict[str, Any]:
    global _next_uid
    imported: list[int] = []
    for entry in users:
        uname = str(entry.get("username") or "").strip()
        if not uname:
            continue
        uid: int | None = None
        for u in _users:
            if u["username"].lower() == uname.lower():
                uid = u["id"]
                u["display_name"] = entry.get("display_name") or u["display_name"]
                u["email"] = entry.get("email")
                u["ldap_dn"] = entry.get("distinguished_name")
                u["source"] = "ldap"
                break
        if uid is None:
            uid = _next_uid
            _next_uid += 1
            _users.append(
                {
                    "id": uid,
                    "username": uname,
                    "display_name": entry.get("display_name") or uname,
                    "email": entry.get("email"),
                    "source": "ldap",
                    "is_active": True,
                    "ldap_dn": entry.get("distinguished_name"),
                    "role_ids": [],
                    "team_ids": [],
                }
            )
        for u in _users:
            if u["id"] == uid:
                u["role_ids"] = list(role_ids)
                u["team_ids"] = list(team_ids)
        for tid in team_ids:
            _team_members.add((tid, uid))
        imported.append(uid)
    return {"ok": True, "user_ids": imported, "count": len(imported)}


def get_user_detail(user_id: int) -> dict[str, Any] | None:
    for u in _users:
        if u["id"] == user_id:
            names = [r["name"] for r in _roles if r["id"] in u["role_ids"]]
            return {
                "id": u["id"],
                "username": u["username"],
                "display_name": u["display_name"],
                "email": u["email"],
                "source": u["source"],
                "is_active": u["is_active"],
                "roles": ", ".join(sorted(names)),
                "role_ids": list(u["role_ids"]),
                "team_ids": list(u["team_ids"]),
            }
    return None


def update_user_profile(user_id: int, display_name: str | None, email: str | None) -> None:
    for u in _users:
        if u["id"] == user_id:
            if display_name is not None:
                u["display_name"] = display_name
            if email is not None:
                u["email"] = email
            return


def set_user_teams(user_id: int, team_ids: list[int]) -> None:
    global _team_members
    _team_members = {(t, u) for (t, u) in _team_members if u != user_id}
    for tid in team_ids:
        _team_members.add((tid, user_id))
    for u in _users:
        if u["id"] == user_id:
            u["team_ids"] = list(team_ids)
            return


def update_team(
    team_id: int,
    name: str,
    description: str | None = None,
    role_ids: list[int] | None = None,
) -> None:
    for t in _teams:
        if t["id"] == team_id:
            t["name"] = name.strip()
            if description is not None:
                t["description"] = (description or "").strip() or None
            if role_ids is not None:
                t["role_ids"] = list(role_ids)
            return


def list_team_members(team_id: int) -> list[dict[str, Any]]:
    uids = [u for (t, u) in _team_members if t == team_id]
    out = []
    for uid in sorted(uids):
        for u in _users:
            if u["id"] == uid:
                out.append(
                    {
                        "user_id": uid,
                        "username": u["username"],
                        "display_name": u["display_name"],
                        "email": u["email"],
                    }
                )
                break
    return out


def add_team_members(team_id: int, user_ids: list[int]) -> None:
    for uid in user_ids:
        _team_members.add((team_id, uid))
        for u in _users:
            if u["id"] == uid and team_id not in u["team_ids"]:
                u["team_ids"].append(team_id)


def remove_team_member(team_id: int, user_id: int) -> None:
    global _team_members
    _team_members.discard((team_id, user_id))
    for u in _users:
        if u["id"] == user_id and team_id in u["team_ids"]:
            u["team_ids"] = [t for t in u["team_ids"] if t != team_id]


def update_role(role_id: int, name: str | None, description: str | None) -> None:
    for r in _roles:
        if r["id"] == role_id and not r.get("is_system"):
            if name is not None:
                r["name"] = name
            if description is not None:
                r["description"] = description
            return


def delete_role(role_id: int) -> None:
    global _roles, _users
    _roles = [r for r in _roles if r["id"] != role_id or r.get("is_system")]
    for u in _users:
        u["role_ids"] = [x for x in u["role_ids"] if x != role_id]
