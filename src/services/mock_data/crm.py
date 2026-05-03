"""Mutable mock payloads for CRM Settings pages (WebUI App DB contract).

These datasets intentionally mirror the FastAPI response shapes used by `customer-api`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

_THRESH_ID_SEQ = 3

_THRESHOLDS: list[dict[str, Any]] = [
    {"id": 1, "resource_type": "cpu", "dc_code": "*", "sellable_limit_pct": 80.0, "notes": "seed", "updated_by": "mock"},
    {"id": 2, "resource_type": "ram", "dc_code": "*", "sellable_limit_pct": 80.0, "notes": "seed", "updated_by": "mock"},
]

_PRICE_OVERRIDES: dict[str, dict[str, Any]] = {
    "00000000-0000-0000-0000-000000000001": {
        "productid": "00000000-0000-0000-0000-000000000001",
        "product_name": "Mock vCPU",
        "unit_price_tl": 12.5,
        "resource_unit": "core",
        "currency": "TL",
        "notes": "seed",
        "updated_by": "mock",
    }
}

_CALC_CONFIG: dict[str, dict[str, Any]] = {
    "efficiency_under_pct": {
        "config_key": "efficiency_under_pct",
        "config_value": "80",
        "value_type": "float",
        "description": "Below this sold/used ratio, efficiency is considered under-utilized.",
        "updated_by": "mock",
    },
    "efficiency_over_pct": {
        "config_key": "efficiency_over_pct",
        "config_value": "110",
        "value_type": "float",
        "description": "Above this ratio, efficiency is considered over-utilized.",
        "updated_by": "mock",
    },
}

_ALIASES: dict[str, dict[str, Any]] = {
    "00000000-0000-0000-0000-00000000ACC1": {
        "crm_accountid": "00000000-0000-0000-0000-00000000ACC1",
        "crm_account_name": "Mock Customer A",
        "canonical_customer_key": "mock_customer_a",
        "netbox_musteri_value": "tenant-a",
        "notes": "seed",
        "source": "manual",
    }
}

_DISCOVERY_COUNTS: list[dict[str, Any]] = [
    {"table_name": "discovery_crm_accounts", "row_count": 42, "last_collected": "2026-05-03T12:00:00Z"},
    {"table_name": "discovery_crm_products", "row_count": 128, "last_collected": "2026-05-03T12:00:00Z"},
]

_PAGES: list[dict[str, Any]] = [
    {
        "page_key": "compute_cpu",
        "category_label": "Compute — CPU",
        "gui_tab_binding": "customer.resources.cpu",
        "resource_unit": "core",
        "icon": "cpu",
        "route_hint": "/customer-view",
        "tab_hint": "Resources",
        "sub_tab_hint": "CPU",
    }
]

_MAPPINGS: dict[str, dict[str, Any]] = {
    "00000000-0000-0000-0000-000000000001": {
        "productid": "00000000-0000-0000-0000-000000000001",
        "product_name": "Mock vCPU",
        "product_number": "SKU-CPU-001",
        "category_code": "compute_cpu",
        "category_label": "Compute — CPU",
        "gui_tab_binding": "customer.resources.cpu",
        "resource_unit": "core",
        "source": "seed",
    }
}


def list_discovery_counts() -> list[dict[str, Any]]:
    return deepcopy(_DISCOVERY_COUNTS)


def list_thresholds() -> list[dict[str, Any]]:
    return deepcopy(_THRESHOLDS)


def upsert_threshold(*, resource_type: str, dc_code: str, sellable_limit_pct: float, notes: Optional[str]) -> dict[str, Any]:
    global _THRESH_ID_SEQ  # noqa: PLW0603
    dc = (dc_code or "*").strip() or "*"
    for row in _THRESHOLDS:
        if row["resource_type"] == resource_type and row["dc_code"] == dc:
            row["sellable_limit_pct"] = float(sellable_limit_pct)
            row["notes"] = notes
            return {"status": "ok", "id": int(row["id"])}

    _THRESH_ID_SEQ += 1
    new_id = _THRESH_ID_SEQ
    _THRESHOLDS.append(
        {
            "id": new_id,
            "resource_type": resource_type,
            "dc_code": dc,
            "sellable_limit_pct": float(sellable_limit_pct),
            "notes": notes,
            "updated_by": "mock",
        }
    )
    return {"status": "ok", "id": new_id}


def delete_threshold(threshold_id: int) -> dict[str, Any]:
    global _THRESHOLDS  # noqa: PLW0603
    before = len(_THRESHOLDS)
    _THRESHOLDS = [r for r in _THRESHOLDS if int(r["id"]) != int(threshold_id)]
    return {"status": "ok", "rows_deleted": before - len(_THRESHOLDS)}


def list_price_overrides() -> list[dict[str, Any]]:
    return deepcopy(list(_PRICE_OVERRIDES.values()))


def upsert_price_override(
    *,
    productid: str,
    product_name: Optional[str],
    unit_price_tl: float,
    resource_unit: Optional[str],
    currency: Optional[str],
    notes: Optional[str],
) -> dict[str, Any]:
    pid = str(productid)
    row = {
        "productid": pid,
        "product_name": product_name,
        "unit_price_tl": float(unit_price_tl),
        "resource_unit": resource_unit,
        "currency": (currency or "TL"),
        "notes": notes,
        "updated_by": "mock",
    }
    _PRICE_OVERRIDES[pid] = row
    return {"status": "ok", "productid": pid}


def delete_price_override(productid: str) -> dict[str, Any]:
    return {"status": "ok", "rows_deleted": 1 if _PRICE_OVERRIDES.pop(str(productid), None) else 0}


def list_calc_config() -> list[dict[str, Any]]:
    return deepcopy(list(_CALC_CONFIG.values()))


def upsert_calc_config(
    *,
    config_key: str,
    config_value: str,
    value_type: Optional[str],
    description: Optional[str],
) -> dict[str, Any]:
    key = str(config_key)
    cur = _CALC_CONFIG.get(key, {"config_key": key})
    cur["config_value"] = str(config_value)
    if value_type is not None:
        cur["value_type"] = str(value_type)
    if description is not None:
        cur["description"] = str(description)
    cur.setdefault("value_type", "string")
    cur.setdefault("updated_by", "mock")
    _CALC_CONFIG[key] = cur
    return {"status": "ok", "config_key": key}


def list_aliases() -> list[dict[str, Any]]:
    return deepcopy(list(_ALIASES.values()))


def upsert_alias(
    *,
    crm_accountid: str,
    canonical_customer_key: Optional[str],
    netbox_musteri_value: Optional[str],
    notes: Optional[str],
) -> dict[str, Any]:
    aid = str(crm_accountid)
    cur = _ALIASES.get(aid, {"crm_accountid": aid, "crm_account_name": aid})
    if canonical_customer_key is not None:
        cur["canonical_customer_key"] = canonical_customer_key
    if netbox_musteri_value is not None:
        cur["netbox_musteri_value"] = netbox_musteri_value
    if notes is not None:
        cur["notes"] = notes
    cur["source"] = "manual"
    _ALIASES[aid] = cur
    return {"status": "ok", "crm_accountid": aid}


def delete_alias(crm_accountid: str) -> dict[str, Any]:
    aid = str(crm_accountid)
    return {"status": "ok", "rows_deleted": 1 if _ALIASES.pop(aid, None) else 0}


def list_service_mapping_pages() -> list[dict[str, Any]]:
    return deepcopy(_PAGES)


def list_service_mappings() -> list[dict[str, Any]]:
    return deepcopy(list(_MAPPINGS.values()))


def upsert_service_mapping(*, productid: str, page_key: str, notes: Optional[str]) -> dict[str, Any]:
    pid = str(productid)
    cur = _MAPPINGS.get(pid)
    if not cur:
        cur = {
            "productid": pid,
            "product_name": "Unknown product",
            "product_number": "",
            "category_code": page_key,
            "category_label": page_key,
            "gui_tab_binding": "customer.resources.unknown",
            "resource_unit": "unit",
            "source": "override",
        }
    cur["category_code"] = page_key
    cur["source"] = "override"
    if notes:
        cur.setdefault("_notes", notes)
    _MAPPINGS[pid] = cur
    return {"status": "ok", "productid": pid}


def delete_service_mapping_override(productid: str) -> dict[str, Any]:
    pid = str(productid)
    row = _MAPPINGS.get(pid)
    if not row:
        return {"status": "ok", "rows_deleted": 0}
    row["source"] = "seed"
    row["category_code"] = "compute_cpu"
    _MAPPINGS[pid] = row
    return {"status": "ok", "rows_deleted": 1}
