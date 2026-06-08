"""Mock NetBox/Loki visualization exclusion config."""

from __future__ import annotations

from copy import deepcopy

_DEVICE_ROLES = [
    {"role": "Server"},
    {"role": "Network"},
    {"role": "Storage"},
    {"role": "Patch Panel"},
    {"role": "PDU"},
]

_EXCLUSIONS = [
    {
        "id": 1,
        "view_scope": "datacenter",
        "dimension": "device_role",
        "dimension_value": "Patch Panel",
        "notes": "Mock default exclusion",
        "updated_by": "mock",
        "updated_at": "2026-06-01T10:00:00Z",
    }
]


def get_device_roles() -> list[dict]:
    return deepcopy(_DEVICE_ROLES)


def list_exclusions() -> list[dict]:
    return deepcopy(_EXCLUSIONS)


def upsert_exclusion(
    *,
    view_scope: str,
    dimension: str,
    dimension_value: str,
    notes: str | None = None,
) -> dict:
    global _EXCLUSIONS
    for row in _EXCLUSIONS:
        if (
            row["view_scope"] == view_scope
            and row["dimension"] == dimension
            and row["dimension_value"] == dimension_value
        ):
            row["notes"] = notes
            return {"status": "ok", **row}
    new_id = max((r["id"] for r in _EXCLUSIONS), default=0) + 1
    entry = {
        "id": new_id,
        "view_scope": view_scope,
        "dimension": dimension,
        "dimension_value": dimension_value,
        "notes": notes,
        "updated_by": "mock",
        "updated_at": "2026-06-08T12:00:00Z",
    }
    _EXCLUSIONS.append(entry)
    return {"status": "ok", **entry}


def delete_exclusion(exclusion_id: int) -> dict:
    global _EXCLUSIONS
    before = len(_EXCLUSIONS)
    _EXCLUSIONS = [r for r in _EXCLUSIONS if r["id"] != exclusion_id]
    return {"status": "ok", "id": exclusion_id, "rows_deleted": before - len(_EXCLUSIONS)}
