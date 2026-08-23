"""Mutable mock payloads for CRM Settings pages (WebUI App DB contract).

These datasets intentionally mirror the FastAPI response shapes used by `customer-api`.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

_THRESH_ID_SEQ = 3

_THRESHOLDS: list[dict[str, Any]] = [
    {"id": 1, "resource_type": "cpu", "dc_code": "*", "panel_key": None, "sellable_limit_pct": 80.0, "notes": "seed", "updated_by": "mock"},
    {"id": 2, "resource_type": "ram", "dc_code": "*", "panel_key": None, "sellable_limit_pct": 80.0, "notes": "seed", "updated_by": "mock"},
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
    "usage_basis": {
        "config_key": "usage_basis",
        "config_value": "max",
        "value_type": "enum",
        "description": "Sellable usage basis: max / avg / cur.",
        "updated_by": "seed",
    },
    "upsell_enabled": {
        "config_key": "upsell_enabled",
        "config_value": "false",
        "value_type": "bool",
        "description": "Platform default for upsell. false = new-sale TL only.",
        "updated_by": "seed",
    },
    "replication_provider": {
        "config_key": "replication_provider",
        "config_value": "veeam",
        "value_type": "enum",
        "description": "Exclusive replication product: veeam or zerto.",
        "updated_by": "seed",
    },
    "waflb_appliance": {
        "config_key": "waflb_appliance",
        "config_value": "5g",
        "value_type": "enum",
        "description": "WAF/LB appliance size: 5g / 1g / 200m.",
        "updated_by": "seed",
    },
    "waflb_distribute": {
        "config_key": "waflb_distribute",
        "config_value": "false",
        "value_type": "bool",
        "description": "When true, WAF/LB units are distributed across DCs.",
        "updated_by": "seed",
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

def _page(page_key: str, label: str, binding: str, unit: str) -> dict[str, Any]:
    return {
        "page_key": page_key,
        "panel_key": page_key,
        "category_label": label,
        "gui_tab_binding": binding,
        "resource_unit": unit,
        "icon": None,
        "route_hint": None,
        "tab_hint": None,
        "sub_tab_hint": None,
    }


# Granular page registry mirrors gui_crm_service_pages (see config/crm_service_mapping.yaml).
_PAGES: list[dict[str, Any]] = [
    _page("virt_classic", "Classic virtualization", "virtualization.classic", "vCPU"),
    _page("virt_classic_cpu", "Classic virtualization — CPU", "virtualization.classic", "vCPU"),
    _page("virt_classic_ram", "Classic virtualization — RAM", "virtualization.classic", "GB"),
    _page("virt_classic_storage", "Classic virtualization — Storage", "virtualization.classic", "GB"),
    _page("virt_hyperconverged", "Hyperconverged virtualization", "virtualization.hyperconverged", "vCPU"),
    _page("virt_hyperconverged_cpu", "Hyperconverged virtualization — CPU", "virtualization.hyperconverged", "vCPU"),
    _page("virt_hyperconverged_ram", "Hyperconverged virtualization — RAM", "virtualization.hyperconverged", "GB"),
    _page("virt_hyperconverged_storage", "Hyperconverged virtualization — Storage", "virtualization.hyperconverged", "GB"),
    _page("virt_nutanix", "Pure Nutanix (AHV)", "virtualization.nutanix", "vCPU"),
    _page("virt_nutanix_cpu", "Pure Nutanix — CPU", "virtualization.nutanix", "vCPU"),
    _page("virt_nutanix_ram", "Pure Nutanix — RAM", "virtualization.nutanix", "GB"),
    _page("virt_nutanix_storage", "Pure Nutanix — Storage", "virtualization.nutanix", "GB"),
    _page("virt_power", "IBM Power LPAR", "virtualization.power", "core"),
    _page("virt_power_cpu", "IBM Power — CPU", "virtualization.power", "core"),
    _page("virt_power_ram", "IBM Power — RAM", "virtualization.power", "GB"),
    _page("virt_power_storage", "IBM Power — Storage", "virtualization.power", "GB"),
    _page("backup_veeam", "Veeam backup", "backup.veeam", "per VM"),
    _page("backup_veeam_cpu", "Veeam replication — CPU", "backup.veeam", "vCPU"),
    _page("backup_veeam_ram", "Veeam replication — RAM", "backup.veeam", "GB"),
    _page("backup_veeam_storage", "Veeam backup — Storage", "backup.veeam", "GB"),
    _page("backup_zerto", "Zerto replication", "backup.zerto", "vCPU"),
    _page("backup_zerto_cpu", "Zerto replication — CPU", "backup.zerto", "vCPU"),
    _page("backup_zerto_ram", "Zerto replication — RAM", "backup.zerto", "GB"),
    _page("backup_zerto_storage", "Zerto replication — Storage", "backup.zerto", "GB"),
    _page("backup_netbackup", "NetBackup", "backup.netbackup", "GB"),
    _page("backup_netbackup_storage", "NetBackup — Storage", "backup.netbackup", "GB"),
    _page("storage_s3", "Object storage (S3)", "storage.s3", "GB"),
    _page("firewall_fortigate", "FortiGate", "security.firewall", "Adet"),
    _page("firewall_paloalto", "Palo Alto", "security.firewall", "Adet"),
    _page("firewall_sophos", "Sophos", "security.firewall", "Adet"),
    _page("firewall_citrix", "Citrix ADC", "security.firewall", "Adet"),
    _page("licensing_microsoft", "Microsoft CSP / M365 / SPLA", "licensing.microsoft", "per User"),
    _page("licensing_redhat", "Red Hat", "licensing.redhat", "Adet"),
    _page("dc_hosting", "Colocation / hosting", "datacenter.hosting", "Adet"),
    _page("dc_energy", "Datacenter energy", "datacenter.energy", "kW"),
    _page("monitoring", "Monitoring", "operations.monitoring", "per VM"),
    _page("database_managed", "Managed database", "data.database", "Adet"),
    _page("other", "Other / uncategorized", "other", "Adet"),
]

_MAPPINGS: dict[str, dict[str, Any]] = {
    # Example seed: HCI RAM SKU mapped to its dedicated panel.
    "1e635018-5c6d-f011-b4cc-6045bd93381c": {
        "productid": "1e635018-5c6d-f011-b4cc-6045bd93381c",
        "product_name": "Hyperconverged Mimari Intel RAM",
        "product_number": "000BLT-52",
        "category_code": "virt_hyperconverged_ram",
        "category_label": "Hyperconverged virtualization — RAM",
        "gui_tab_binding": "virtualization.hyperconverged",
        "resource_unit": "GB",
        "source": "yaml",
    },
    # Example unmatched product so the UI can render the orange badge.
    "edb3353a-aae2-f011-8406-000d3a2b6ad9": {
        "productid": "edb3353a-aae2-f011-8406-000d3a2b6ad9",
        "product_name": "Dummy Product",
        "product_number": "DMY.PRD.001",
        "category_code": None,
        "category_label": None,
        "gui_tab_binding": None,
        "resource_unit": None,
        "source": "unmatched",
    },
}


def list_discovery_counts() -> list[dict[str, Any]]:
    return deepcopy(_DISCOVERY_COUNTS)


def list_thresholds() -> list[dict[str, Any]]:
    return deepcopy(_THRESHOLDS)


def upsert_threshold(
    *,
    resource_type: str,
    dc_code: str,
    sellable_limit_pct: float,
    notes: Optional[str],
    panel_key: Optional[str] = None,
) -> dict[str, Any]:
    global _THRESH_ID_SEQ  # noqa: PLW0603
    dc = (dc_code or "*").strip() or "*"
    pk = panel_key or None
    for row in _THRESHOLDS:
        if (
            row["resource_type"] == resource_type
            and row["dc_code"] == dc
            and (row.get("panel_key") or None) == pk
        ):
            row["sellable_limit_pct"] = float(sellable_limit_pct)
            row["notes"] = notes
            row["panel_key"] = pk
            return {"status": "ok", "id": int(row["id"])}

    _THRESH_ID_SEQ += 1
    new_id = _THRESH_ID_SEQ
    _THRESHOLDS.append(
        {
            "id": new_id,
            "resource_type": resource_type,
            "dc_code": dc,
            "panel_key": pk,
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


def _page_meta(page_key: str) -> dict[str, Any]:
    for p in _PAGES:
        if p["page_key"] == page_key:
            return p
    return {
        "page_key": page_key,
        "category_label": page_key,
        "gui_tab_binding": "other",
        "resource_unit": "Adet",
    }


def upsert_service_mapping(*, productid: str, page_key: str, notes: Optional[str]) -> dict[str, Any]:
    pid = str(productid)
    cur = _MAPPINGS.get(pid) or {
        "productid": pid,
        "product_name": "Unknown product",
        "product_number": "",
    }
    meta = _page_meta(page_key)
    cur["category_code"] = page_key
    cur["category_label"] = meta["category_label"]
    cur["gui_tab_binding"] = meta["gui_tab_binding"]
    cur["resource_unit"] = meta["resource_unit"]
    cur["source"] = "override"
    if notes:
        cur["_notes"] = notes
    _MAPPINGS[pid] = cur
    return {"status": "ok", "productid": pid}


def delete_service_mapping_override(productid: str) -> dict[str, Any]:
    """Reset to unmatched (mock seed has no fallback page_key)."""
    pid = str(productid)
    row = _MAPPINGS.get(pid)
    if not row:
        return {"status": "ok", "rows_deleted": 0}
    row["source"] = "unmatched"
    row["category_code"] = None
    row["category_label"] = None
    row["gui_tab_binding"] = None
    row["resource_unit"] = None
    _MAPPINGS[pid] = row
    return {"status": "ok", "rows_deleted": 1}


# ---------------------------------------------------------------------------
# Sellable Potential (customer-api contract) — static canned math
# ---------------------------------------------------------------------------

_PANEL_DEFS: list[dict[str, Any]] = [
    {
        "panel_key": "virt_hyperconverged_cpu",
        "label": "Hyperconverged — CPU",
        "family": "virt_hyperconverged",
        "resource_kind": "cpu",
        "display_unit": "vCPU",
        "sort_order": 110,
        "enabled": True,
        "notes": "mock",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
    {
        "panel_key": "virt_hyperconverged_ram",
        "label": "Hyperconverged — RAM",
        "family": "virt_hyperconverged",
        "resource_kind": "ram",
        "display_unit": "GB",
        "sort_order": 111,
        "enabled": True,
        "notes": "mock",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
    {
        "panel_key": "virt_hyperconverged_storage",
        "label": "Hyperconverged — Storage",
        "family": "virt_hyperconverged",
        "resource_kind": "storage",
        "display_unit": "GB",
        "sort_order": 112,
        "enabled": True,
        "notes": "mock",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
]

_RESOURCE_RATIOS: list[dict[str, Any]] = [
    {
        "family": "virt_hyperconverged",
        "dc_code": "*",
        "cpu_per_unit": 1.0,
        "ram_gb_per_unit": 8.0,
        "storage_gb_per_unit": 100.0,
        "notes": "mock",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
    {
        "family": "virt_classic",
        "dc_code": "*",
        "cpu_per_unit": 1.0,
        "ram_gb_per_unit": 4.0,
        "storage_gb_per_unit": 100.0,
        "notes": "mock",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
    {
        "family": "backup_veeam_replication_classic",
        "dc_code": "*",
        "cpu_per_unit": 1.0,
        "ram_gb_per_unit": 4.0,
        "storage_gb_per_unit": 50.0,
        "notes": "mock — independent of virt_classic",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
    {
        "family": "backup_zerto_replication_classic",
        "dc_code": "*",
        "cpu_per_unit": 1.0,
        "ram_gb_per_unit": 4.0,
        "storage_gb_per_unit": 50.0,
        "notes": "mock — independent of virt_classic",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
    {
        "family": "backup_veeam_replication_hyperconverged",
        "dc_code": "*",
        "cpu_per_unit": 1.0,
        "ram_gb_per_unit": 4.0,
        "storage_gb_per_unit": 50.0,
        "notes": "mock — independent of virt_hyperconverged",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
    {
        "family": "backup_zerto_replication_hyperconverged",
        "dc_code": "*",
        "cpu_per_unit": 1.0,
        "ram_gb_per_unit": 4.0,
        "storage_gb_per_unit": 50.0,
        "notes": "mock — independent of virt_hyperconverged",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
]

_UNIT_CONVERSIONS: list[dict[str, Any]] = [
    {
        "from_unit": "GHz",
        "to_unit": "vCPU",
        "factor": 8.0,
        "operation": "divide",
        "ceil_result": True,
        "notes": "mock",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    },
]


def _hc_panels() -> list[dict[str, Any]]:
    """Return the three canonical virt_hyperconverged panels (ADR-0014 example)."""
    return [
        {
            "panel_key": "virt_hyperconverged_cpu",
            "label": "Hyperconverged — CPU",
            "family": "virt_hyperconverged",
            "resource_kind": "cpu",
            "display_unit": "vCPU",
            "dc_code": "*",
            "total": 10.0,
            "allocated": 4.0,
            "threshold_pct": 80.0,
            "sellable_raw": 4.0,
            "sellable_constrained": 3.0,
            "unit_price_tl": 1500.0,
            "potential_tl": 4500.0,
            "ratio_bound": True,
            "has_infra_source": True,
            "has_price": True,
            "notes": [],
        },
        {
            "panel_key": "virt_hyperconverged_ram",
            "label": "Hyperconverged — RAM",
            "family": "virt_hyperconverged",
            "resource_kind": "ram",
            "display_unit": "GB",
            "dc_code": "*",
            "total": 80.0,
            "allocated": 40.0,
            "threshold_pct": 80.0,
            "sellable_raw": 24.0,
            "sellable_constrained": 24.0,
            "unit_price_tl": 20.0,
            "potential_tl": 480.0,
            "ratio_bound": False,
            "has_infra_source": True,
            "has_price": True,
            "notes": [],
        },
        {
            "panel_key": "virt_hyperconverged_storage",
            "label": "Hyperconverged — Storage",
            "family": "virt_hyperconverged",
            "resource_kind": "storage",
            "display_unit": "GB",
            "dc_code": "*",
            "total": 1000.0,
            "allocated": 300.0,
            "threshold_pct": 80.0,
            "sellable_raw": 500.0,
            "sellable_constrained": 300.0,
            "unit_price_tl": 2.0,
            "potential_tl": 600.0,
            "ratio_bound": True,
            "has_infra_source": True,
            "has_price": True,
            "notes": [],
        },
    ]


def sellable_summary(dc_code: str = "*") -> dict[str, Any]:
    panels = _hc_panels()
    fam = {
        "family": "virt_hyperconverged",
        "label": "Hyperconverged",
        "dc_code": dc_code,
        "panels": panels,
        "total_potential_tl": 5580.0,
        "total_sellable_constrained_units": {"cpu": 3.0, "ram": 24.0, "storage": 300.0},
        "constrained_loss_tl": 1900.0,
    }
    return {
        "dc_code": dc_code,
        "total_potential_tl": 5580.0,
        "constrained_loss_tl": 1900.0,
        "ytd_sales_tl": 250000.0,
        "unmapped_product_count": 2,
        "families": [fam],
    }


def sellable_by_panel(dc_code: str = "*", family: Optional[str] = None) -> list[dict[str, Any]]:
    panels = [deepcopy(p) for p in _hc_panels()]
    for p in panels:
        p["dc_code"] = dc_code or "*"
    if family:
        return [p for p in panels if p.get("family") == family]
    return panels


def sellable_by_family(dc_code: str = "*") -> list[dict[str, Any]]:
    summary = sellable_summary(dc_code)
    return deepcopy(summary.get("families") or [])


def inventory_overview(dc_code: str = "*") -> dict[str, Any]:
    """Global CRM inventory overview fixture (capacity vs CRM sold vs used)."""
    panels = [
        {
            "panel_key": "virt_hyperconverged_cpu",
            "label": "Hyperconverged Mimari — CPU",
            "service_label": "Hyperconverged Mimari — CPU",
            "family": "virt_hyperconverged",
            "family_label": "Hyperconverged",
            "resource_kind": "cpu",
            "display_unit": "vCPU",
            "total": 10.0,
            "crm_sold_qty": 8.0,
            "crm_sold_tl": 12000.0,
            "used_qty": 6.0,
            "free_qty": 4.0,
            "sellable_qty": 3.0,
            "potential_tl": 4500.0,
            "unit_price_tl": 1500.0,
            "used_tl": 9000.0,
            "sellable_profile": "dual_track",
            "sellable_alloc_qty": 3.0,
            "sellable_max_qty": 4.0,
            "potential_tl_alloc": 4500.0,
            "potential_tl_max": 6000.0,
            "has_infra_source": True,
            "has_price": True,
            "infra_binding": "bound",
            "status": "ok",
            "delta_used_vs_crm": -2.0,
            "overage_qty": 0.0,
            "efficiency_pct": 75.0,
            "crm_products_summary": "HC CPU SKU",
            "computation_mode": "host_based",
        },
        {
            "panel_key": "virt_hyperconverged_ram",
            "label": "Hyperconverged Mimari — RAM",
            "service_label": "Hyperconverged Mimari — RAM",
            "family": "virt_hyperconverged",
            "family_label": "Hyperconverged",
            "resource_kind": "ram",
            "display_unit": "GB",
            "total": 80.0,
            "crm_sold_qty": 50.0,
            "crm_sold_tl": 1000.0,
            "used_qty": 55.0,
            "free_qty": 25.0,
            "sellable_qty": 24.0,
            "potential_tl": 480.0,
            "unit_price_tl": 20.0,
            "used_tl": 1100.0,
            "sellable_profile": "dual_track",
            "sellable_alloc_qty": 20.0,
            "sellable_max_qty": 24.0,
            "potential_tl_alloc": 400.0,
            "potential_tl_max": 480.0,
            "has_infra_source": True,
            "has_price": True,
            "infra_binding": "bound",
            "status": "over",
            "delta_used_vs_crm": 5.0,
            "overage_qty": 5.0,
            "efficiency_pct": 110.0,
            "crm_products_summary": "HC RAM SKU",
            "computation_mode": "host_based",
        },
        {
            "panel_key": "backup_netbackup_storage",
            "label": "NetBackup — Storage",
            "service_label": "NetBackup — Storage",
            "family": "backup_netbackup",
            "family_label": "NetBackup",
            "resource_kind": "storage",
            "display_unit": "GB",
            "total": 12000.0,
            "crm_sold_qty": 800.0,
            "crm_sold_tl": 184000.0,
            "used_qty": 4500.0,
            "free_qty": 7500.0,
            "sellable_qty": 5100.0,
            "potential_tl": 1173000.0,
            "unit_price_tl": 230.0,
            "used_tl": 1035000.0,
            "sellable_profile": "standard",
            "sellable_alloc_qty": None,
            "sellable_max_qty": None,
            "potential_tl_alloc": 1173000.0,
            "potential_tl_max": None,
            "has_infra_source": True,
            "has_price": True,
            "infra_binding": "bound",
            "status": "ok",
            "delta_used_vs_crm": 3700.0,
            "overage_qty": 3700.0,
            "efficiency_pct": 562.5,
            "crm_products_summary": "NetBackup Storage SKU",
            "computation_mode": "aggregated",
        },
        {
            "panel_key": "storage_s3",
            "label": "IBM ICOS S3",
            "service_label": "IBM ICOS S3",
            "family": "storage_s3",
            "family_label": "IBM ICOS S3",
            "resource_kind": "storage",
            "display_unit": "TB",
            "total": 200.0,
            "crm_sold_qty": 20.0,
            "crm_sold_tl": 40000.0,
            "used_qty": 60.0,
            "free_qty": 140.0,
            "sellable_qty": 100.0,
            "potential_tl": 200000.0,
            "unit_price_tl": 2000.0,
            "used_tl": 120000.0,
            "sellable_profile": "standard",
            "sellable_alloc_qty": None,
            "sellable_max_qty": None,
            "potential_tl_alloc": 200000.0,
            "potential_tl_max": None,
            "has_infra_source": True,
            "has_price": True,
            "infra_binding": "bound",
            "status": "over",
            "delta_used_vs_crm": 40.0,
            "overage_qty": 40.0,
            "efficiency_pct": 300.0,
            "crm_products_summary": "S3 Ankara SKU, S3 Istanbul SKU",
            "computation_mode": "aggregated",
            "data_quality": None,
        },
        {
            "panel_key": "backup_veeam",
            "label": "Veeam Cloud Connect Backup",
            "service_label": "Veeam Cloud Connect Backup",
            "family": "backup_veeam",
            "family_label": "Veeam",
            "resource_kind": "other",
            "display_unit": "Adet",
            "total": None,
            "crm_sold_qty": 25.0,
            "crm_sold_tl": 5000.0,
            "used_qty": None,
            "free_qty": None,
            "sellable_qty": None,
            "potential_tl": 0.0,
            "has_infra_source": False,
            "has_price": True,
            "infra_binding": "crm_only",
            "status": "crm_only",
            "delta_used_vs_crm": None,
            "overage_qty": 0.0,
            "efficiency_pct": None,
            "crm_products_summary": "Veeam Backup SKU",
            "computation_mode": None,
        },
        {
            "panel_key": "license_windows_os",
            "label": "MS Windows Lisans",
            "service_label": "MS Windows Lisans",
            "family": "license_os",
            "family_label": "OS Lisans",
            "resource_kind": "other",
            "display_unit": "per VM",
            "total": 100.0,
            "crm_sold_qty": 40.0,
            "crm_sold_tl": 16700.0,
            "used_qty": None,
            "free_qty": None,
            "unsold_qty": None,
            "sellable_qty": None,
            "potential_tl": 0.0,
            "unit_price_tl": 417.5,
            "sellable_profile": "os_licence",
            "licence_detected_qty": 100.0,
            "licence_gap_qty": 60.0,
            "licence_gap_tl": 25050.0,
            "has_infra_source": True,
            "has_price": True,
            "infra_binding": "bound",
            "status": "over",
            "crm_products_summary": "MS Windows Lisans",
            "computation_mode": "aggregated",
        },
        {
            "panel_key": "license_redhat",
            "label": "Red Hat (CCSP)",
            "service_label": "Red Hat (CCSP)",
            "family": "license_redhat",
            "family_label": "OS Lisans",
            "resource_kind": "other",
            "display_unit": "Adet",
            "total": 20.0,
            "crm_sold_qty": 0.0,
            "crm_sold_tl": 0.0,
            "used_qty": None,
            "free_qty": None,
            "unsold_qty": None,
            "sellable_qty": None,
            "potential_tl": 0.0,
            "unit_price_tl": 531.0,
            "sellable_profile": "os_licence",
            "licence_detected_qty": 20.0,
            "licence_gap_qty": 20.0,
            "licence_gap_tl": 10620.0,
            "has_infra_source": True,
            "has_price": True,
            "infra_binding": "bound",
            "status": "unsold_usage",
            "crm_products_summary": "CCSP-RH",
            "computation_mode": "aggregated",
        },
        {
            "panel_key": "license_suse",
            "label": "SUSE Linux",
            "service_label": "SUSE Linux",
            "family": "license_other",
            "family_label": "OS Lisans",
            "resource_kind": "other",
            "display_unit": "Adet",
            "total": 15.0,
            "crm_sold_qty": 6.0,
            "crm_sold_tl": 65454.0,
            "used_qty": None,
            "free_qty": None,
            "unsold_qty": None,
            "sellable_qty": None,
            "potential_tl": 0.0,
            "unit_price_tl": 10909.0,
            "sellable_profile": "os_licence",
            "licence_detected_qty": 15.0,
            "licence_gap_qty": 9.0,
            "licence_gap_tl": 98181.0,
            "has_infra_source": True,
            "has_price": True,
            "infra_binding": "bound",
            "status": "over",
            "crm_products_summary": "SUSE Lisans Bedeli",
            "computation_mode": "aggregated",
        },
        {
            "panel_key": "mgmt_os_windows",
            "label": "Windows İşletim Sistemi Yönetimi",
            "service_label": "Windows İşletim Sistemi Yönetimi",
            "family": "mgmt_os",
            "family_label": "Os",
            "resource_kind": "other",
            "display_unit": "per VM",
            "total": None,
            "crm_sold_qty": 30.0,
            "crm_sold_tl": 142377.0,
            "used_qty": None,
            "free_qty": None,
            "sellable_qty": None,
            "potential_tl": 0.0,
            "has_infra_source": False,
            "has_price": True,
            "infra_binding": "crm_only",
            "status": "crm_only",
            "crm_products_summary": "Windows OS Yönetimi",
            "computation_mode": None,
        },
    ]
    crm_only = [p for p in panels if p["infra_binding"] == "crm_only"]
    fam_hc = {
        "family": "virt_hyperconverged",
        "label": "Hyperconverged",
        "family_label": "Hyperconverged",
        "dc_code": dc_code,
        "has_infra": True,
        "panel_count": 2,
        "panels": panels[:2],
    }
    fam_nb = {
        "family": "backup_netbackup",
        "label": "NetBackup",
        "family_label": "NetBackup",
        "dc_code": dc_code,
        "has_infra": True,
        "panel_count": 1,
        "panels": [panels[2]],
    }
    fam_s3 = {
        "family": "storage_s3",
        "label": "IBM ICOS S3",
        "family_label": "IBM ICOS S3",
        "dc_code": dc_code,
        "has_infra": True,
        "panel_count": 1,
        "panels": [panels[3]],
    }
    fam_os = {
        "family": "os_licence",
        "label": "OS Lisans",
        "family_label": "OS Lisans",
        "dc_code": dc_code,
        "has_infra": True,
        "panel_count": 3,
        "sellable_profile": "os_licence",
        "panels": panels[5:8],
    }
    return {
        "dc_code": dc_code,
        "summary": {
            "dc_code": dc_code,
            "infra_panel_count": 7,
            "panel_count": 9,
            "crm_only_count": 2,
            "crm_entitled_tl": 18000.0,
            "unmapped_product_count": 2,
            "unmapped_entitled_count": 1,
            "overage_panel_count": 1,
            "unsold_usage_count": 0,
            "total_potential_tl": 4980.0,
            "note": (
                "Capacity units are heterogeneous across panels; compare quantities in the service list."
                + (
                    " Global view sums DC-scoped infra totals across bound DCs, then "
                    "recomputes sellable per family; global-only panels are counted once."
                    if dc_code in (None, "", "*")
                    else ""
                )
            ),
        },
        "families": [fam_hc, fam_nb, fam_s3, fam_os],
        "panels": panels,
        "crm_only_panels": crm_only,
        "unmapped_products": [
            {
                "productid": "unmapped-1",
                "product_name": "Legacy SKU",
                "resource_unit": "Adet",
                "entitled_qty": 3.0,
                "entitled_amount_tl": 300.0,
            }
        ],
        "product_matching": {
            "registry_version": 1,
            "methodology": "ADR-0024",
            "summary": {
                "product_count": 2,
                "with_sold_count": 2,
                "capacity_count": 1,
                "documented_count": 1,
                "customer_phase_count": 0,
                "by_status": {"capacity": 1, "documented": 1},
            },
            "products": [
                {
                    "productnumber": "000BLT-46",
                    "product_name": "Hyperconverged Mimari Intel CPU",
                    "resource_unit": "vCPU",
                    "crm_sold_qty": 8.0,
                    "crm_sold_tl": 12000.0,
                    "usage_source": "Loki - Virutal Machines",
                    "matching_rule": "Hyperconverged Sunucu cpu totali",
                    "match_status": "capacity",
                    "panel_key": "virt_hyperconverged_cpu",
                    "family": "virt_hyperconverged",
                    "infra_tables": ["nutanix_vm_metrics"],
                    "notes": "",
                    "in_registry": True,
                    "infra_total": 10.0,
                    "infra_used": 6.0,
                    "infra_free": 4.0,
                    "panel_status": "ok",
                },
                {
                    "productnumber": "000BLT-123",
                    "product_name": "Sophos UTM",
                    "resource_unit": "Adet",
                    "crm_sold_qty": 2.0,
                    "crm_sold_tl": 400.0,
                    "usage_source": "Loki- Virutal Firewall",
                    "matching_rule": "Müşteri Sophos FW x Hizmet Adedi",
                    "match_status": "documented",
                    "panel_key": None,
                    "family": "security",
                    "infra_tables": ["discovery_netbox_inventory_device"],
                    "notes": "",
                    "in_registry": True,
                    "infra_total": None,
                    "infra_used": None,
                    "infra_free": None,
                    "panel_status": None,
                },
            ],
        },
    }


def metric_tags(prefix: Optional[str] = None, scope_type: str = "global", scope_id: str = "*") -> list[dict[str, Any]]:
    rows = [
        {
            "metric_key": "crm.sellable_potential.total_tl",
            "value": 5580.0,
            "unit": "TL",
            "scope_type": scope_type,
            "scope_id": scope_id,
        },
        {
            "metric_key": "virtualization.hyperconverged.cpu.sellable_constrained",
            "value": 3.0,
            "unit": "vCPU",
            "scope_type": scope_type,
            "scope_id": scope_id,
        },
    ]
    if prefix:
        rows = [r for r in rows if str(r["metric_key"]).startswith(prefix)]
    return rows


def metric_snapshots(metric_key: str, hours: int = 720, scope_id: str = "*") -> list[dict[str, Any]]:
    _ = hours
    return [
        {
            "metric_key": metric_key,
            "scope_type": "global",
            "scope_id": scope_id,
            "value": 5580.0,
            "unit": "TL",
            "captured_at": "2026-05-04T00:00:00Z",
        }
    ]


def list_panel_definitions() -> list[dict[str, Any]]:
    return deepcopy(_PANEL_DEFS)


def upsert_panel_definition(
    panel_key: str,
    *,
    label: str,
    family: str,
    resource_kind: str,
    display_unit: str = "GB",
    sort_order: int = 100,
    enabled: bool = True,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    row = {
        "panel_key": panel_key,
        "label": label,
        "family": family,
        "resource_kind": resource_kind,
        "display_unit": display_unit,
        "sort_order": int(sort_order),
        "enabled": bool(enabled),
        "notes": notes,
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    }
    replaced = False
    for i, cur in enumerate(_PANEL_DEFS):
        if cur["panel_key"] == panel_key:
            _PANEL_DEFS[i] = row
            replaced = True
            break
    if not replaced:
        _PANEL_DEFS.append(row)
    return {"status": "ok", "panel_key": panel_key}


def get_panel_infra_source(panel_key: str, dc_code: str = "*") -> dict[str, Any]:
    return {
        "panel_key": panel_key,
        "dc_code": dc_code,
        "source_table": "nutanix_cluster_metrics",
        "total_column": "total_cpu_capacity",
        "total_unit": "vCPU",
        "allocated_table": "nutanix_vm_metrics",
        "allocated_column": "cpu_count",
        "allocated_unit": "vCPU",
        "filter_clause": "datacenter_name ILIKE :dc_pattern",
        "manual_total": None,
        "manual_allocated": None,
        "notes": "mock",
        "updated_by": "mock",
        "updated_at": "2026-05-04T00:00:00Z",
    }


def upsert_panel_infra_source(
    panel_key: str,
    dc_code: str = "*",
    *,
    source_table: Optional[str] = None,
    total_column: Optional[str] = None,
    total_unit: Optional[str] = None,
    allocated_table: Optional[str] = None,
    allocated_column: Optional[str] = None,
    allocated_unit: Optional[str] = None,
    filter_clause: Optional[str] = None,
    manual_total: Optional[float] = None,
    manual_allocated: Optional[float] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "status": "ok",
        "panel_key": panel_key,
        "dc_code": dc_code,
        "source_table": source_table,
        "total_column": total_column,
        "total_unit": total_unit,
        "allocated_table": allocated_table,
        "allocated_column": allocated_column,
        "allocated_unit": allocated_unit,
        "filter_clause": filter_clause,
        "manual_total": manual_total,
        "manual_allocated": manual_allocated,
        "notes": notes,
    }


def get_sellable_snapshot_meta(
    dc_code: str = "*",
    family: str = "*",
    clusters: Optional[str] = None,
) -> dict[str, Any]:
    return {"computed_at": "2026-05-04T12:00:00Z"}


def force_refresh_sellable() -> dict[str, Any]:
    return {"status": "ok", "metrics_written": 0}


def list_resource_ratios() -> list[dict[str, Any]]:
    return deepcopy(_RESOURCE_RATIOS)


def upsert_resource_ratio(
    family: str,
    *,
    dc_code: str = "*",
    cpu_per_unit: float = 1.0,
    ram_gb_per_unit: float = 8.0,
    storage_gb_per_unit: float = 100.0,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "status": "ok",
        "family": family,
        "dc_code": dc_code,
        "cpu_per_unit": float(cpu_per_unit),
        "ram_gb_per_unit": float(ram_gb_per_unit),
        "storage_gb_per_unit": float(storage_gb_per_unit),
        "notes": notes,
    }


def list_unit_conversions() -> list[dict[str, Any]]:
    return deepcopy(_UNIT_CONVERSIONS)


def upsert_unit_conversion(
    from_unit: str,
    to_unit: str,
    *,
    factor: float,
    operation: str = "divide",
    ceil_result: bool = False,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "status": "ok",
        "from_unit": from_unit,
        "to_unit": to_unit,
        "factor": float(factor),
        "operation": operation,
        "ceil_result": bool(ceil_result),
        "notes": notes,
    }


def delete_unit_conversion(from_unit: str, to_unit: str) -> dict[str, Any]:
    return {"status": "ok", "rows_deleted": 1, "from_unit": from_unit, "to_unit": to_unit}


# ---------------------------------------------------------------------------
# Static capacity (W0) — Network / OpenStack / GPU. Mirrors crm-engine
# GET/PUT /crm/config/static-capacity, GET .../template, POST .../import.
# ---------------------------------------------------------------------------

_KNOWN_DCS = frozenset(
    {
        "DC11",
        "DC12",
        "DC13",
        "DC14",
        "DC15",
        "DC16",
        "DC17",
        "DC18",
        "AZ11",
        "UZ11",
        "ICT11",
        "ICT21",
    }
)
_OS_KINDS = frozenset({"package", "public_ip", "ceph"})
_NETWORK_HEADERS = (
    "dc",
    "public_ip",
    "subnet_30",
    "spine_port",
    "leaf_port",
    "mgmt_port",
    "internet_total_mbps",
    "internet_sellable_mbps",
    "ddos_capable",
    "ddos_sellable_mbps",
)
_OPENSTACK_HEADERS = ("kind", "key", "label", "quantity", "unit", "hypervisor", "notes")
_GPU_HEADERS = ("gpu_model", "package_key", "quantity", "hypervisor", "notes")
_TRUE = frozenset({"true", "1", "yes", "y", "on", "evet", "e"})
_FALSE = frozenset({"false", "0", "no", "n", "off", "hayir", "h"})


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _net(
    dc: str,
    public_ip: int,
    subnet_30: int,
    spine_port: int,
    leaf_port: int,
    mgmt_port: int,
    internet_total_mbps: float,
    internet_sellable_mbps: float,
    ddos_capable: bool,
    ddos_sellable_mbps: float,
) -> dict[str, Any]:
    return {
        "dc": dc,
        "public_ip": public_ip,
        "subnet_30": subnet_30,
        "spine_port": spine_port,
        "leaf_port": leaf_port,
        "mgmt_port": mgmt_port,
        "internet_total_mbps": internet_total_mbps,
        "internet_sellable_mbps": internet_sellable_mbps,
        "ddos_capable": ddos_capable,
        "ddos_sellable_mbps": ddos_sellable_mbps,
        "notes": "09.08 workbook seed",
        "source": "seed",
        "updated_by": "mock",
        "updated_at": "2026-08-23T09:00:00+00:00",
    }


_STATIC_SEED: dict[str, Any] = {
    "network": [
        _net("DC11", 40, 10, 54, 94, 40, 4000, 1500, True, 1500),
        _net("DC12", 200, 50, 0, 11, 40, 3000, 2000, True, 2000),
        _net("DC13", 232, 58, 8, 139, 200, 100000, 85000, True, 85000),
        _net("DC14", 104, 26, 40, 102, 120, 6000, 1000, True, 1000),
        _net("DC15", 24, 6, 40, 94, 50, 2000, 100, True, 100),
        _net("DC16", 256, 64, 40, 94, 26, 4000, 1500, True, 1500),
        _net("DC17", 168, 42, 54, 64, 88, 1000, 600, True, 600),
        _net("DC18", 0, 0, 40, 60, 28, 0, 0, True, 0),
        _net("AZ11", 160, 40, 0, 68, 80, 200, 20, True, 20),
        _net("UZ11", 160, 40, 0, 76, 24, 500, 300, True, 300),
        _net("ICT11", 0, 0, 0, 48, 66, 2000, 400, True, 400),
        _net("ICT21", 188, 47, 0, 40, 46, 2000, 1000, True, 1000),
    ],
    "waf_lb": {
        "total_throughput_gbps": 350.0,
        "appliance_size": "5g",
        "max_units_5g": None,
        "max_units_1g": None,
        "max_units_200m": 900,
        "distribute_across_dcs": False,
        "source": "seed",
        "updated_by": "mock",
        "updated_at": "2026-08-23T09:00:00+00:00",
    },
    "openstack": [
        {
            "kind": "package",
            "key": "os_accel_n1h96s",
            "label": "Accelerated_N1H96s",
            "quantity": 1.0,
            "unit": "adet",
            "hypervisor": "hv07",
            "aux_total": None,
            "aux_used": None,
            "notes": "09.08 workbook",
            "source": "seed",
            "updated_by": "mock",
            "updated_at": "2026-08-23T09:00:00+00:00",
        },
        {
            "kind": "public_ip",
            "key": "os_public_ip",
            "label": "public",
            "quantity": 3.0,
            "unit": "adet",
            "hypervisor": "",
            "aux_total": 228.0,
            "aux_used": 225.0,
            "notes": "empty IP; total 228 / used 225",
            "source": "seed",
            "updated_by": "mock",
            "updated_at": "2026-08-23T09:00:00+00:00",
        },
        {
            "kind": "ceph",
            "key": "ceph_sellable_tib",
            "label": "KALAN SATILABILIR",
            "quantity": 288.2,
            "unit": "TiB",
            "hypervisor": "",
            "aux_total": None,
            "aux_used": None,
            "notes": "do not re-apply disk threshold (Y10)",
            "source": "seed",
            "updated_by": "mock",
            "updated_at": "2026-08-23T09:00:00+00:00",
        },
    ],
    "gpu": [
        {
            "gpu_model": "H100",
            "package_key": "os_accel_n1h96s",
            "quantity": 1.0,
            "hypervisor": "hv07",
            "notes": "09.08 Accelerated_N1H96s",
            "source": "seed",
            "updated_by": "mock",
            "updated_at": "2026-08-23T09:00:00+00:00",
        },
        {
            "gpu_model": "L40s",
            "package_key": "os_accel_g1ls8dm",
            "quantity": 1.0,
            "hypervisor": "hw06",
            "notes": "09.08 Accelerated_G1Ls8Dm",
            "source": "seed",
            "updated_by": "mock",
            "updated_at": "2026-08-23T09:00:00+00:00",
        },
    ],
    "imports": [],
}

_STATIC: dict[str, Any] = deepcopy(_STATIC_SEED)


def reset_static_capacity() -> None:
    """Test helper: restore the W0 seed snapshot."""
    global _STATIC
    _STATIC = deepcopy(_STATIC_SEED)


def list_static_capacity() -> dict[str, Any]:
    return deepcopy(_STATIC)


def save_static_capacity(payload: dict[str, Any], updated_by: str = "mock") -> dict[str, Any]:
    stamp = _iso_now()
    if payload.get("network") is not None:
        rows = []
        for rec in payload["network"]:
            row = deepcopy(rec)
            row["updated_by"] = updated_by
            row["updated_at"] = stamp
            row.setdefault("source", "manual")
            rows.append(row)
        _STATIC["network"] = rows
    if payload.get("waf_lb") is not None:
        cfg = deepcopy(_STATIC["waf_lb"])
        cfg.update(payload["waf_lb"])
        cfg["updated_by"] = updated_by
        cfg["updated_at"] = stamp
        cfg.setdefault("source", "manual")
        _STATIC["waf_lb"] = cfg
    if payload.get("openstack") is not None:
        rows = []
        for rec in payload["openstack"]:
            row = deepcopy(rec)
            row["updated_by"] = updated_by
            row["updated_at"] = stamp
            row.setdefault("source", "manual")
            rows.append(row)
        _STATIC["openstack"] = rows
    if payload.get("gpu") is not None:
        rows = []
        for rec in payload["gpu"]:
            row = deepcopy(rec)
            row["updated_by"] = updated_by
            row["updated_at"] = stamp
            row.setdefault("source", "manual")
            rows.append(row)
        _STATIC["gpu"] = rows
    return list_static_capacity()


def static_capacity_template(dataset: str) -> str:
    name = (dataset or "network").strip().lower()
    if name == "network":
        headers, rows = _NETWORK_HEADERS, _STATIC["network"]
        body = [
            [
                r["dc"],
                r["public_ip"],
                r["subnet_30"],
                r["spine_port"],
                r["leaf_port"],
                r["mgmt_port"],
                r["internet_total_mbps"],
                r["internet_sellable_mbps"],
                "true" if r["ddos_capable"] else "false",
                r["ddos_sellable_mbps"],
            ]
            for r in rows
        ]
    elif name == "openstack":
        headers, rows = _OPENSTACK_HEADERS, _STATIC["openstack"]
        body = [
            [r["kind"], r["key"], r["label"], r["quantity"], r["unit"], r.get("hypervisor") or "", r.get("notes") or ""]
            for r in rows
        ]
    elif name == "gpu":
        headers, rows = _GPU_HEADERS, _STATIC["gpu"]
        body = [
            [r["gpu_model"], r["package_key"], r["quantity"], r.get("hypervisor") or "", r.get("notes") or ""]
            for r in rows
        ]
    else:
        raise ValueError(f"unknown dataset '{dataset}'")
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(body)
    return buf.getvalue()


def import_static_capacity_csv(
    dataset: str,
    csv_text: str,
    *,
    filename: Optional[str] = None,
    confirm: bool = False,
    updated_by: str = "mock",
) -> dict[str, Any]:
    name = (dataset or "").strip().lower()
    parsers = {
        "network": _parse_network_csv,
        "openstack": _parse_openstack_csv,
        "gpu": _parse_gpu_csv,
    }
    if name not in parsers:
        return {
            "ok": False,
            "status": "error",
            "errors": [{"line": 0, "message": f"unknown dataset '{dataset}'"}],
            "message": "Unknown dataset — nothing was saved",
        }
    parsed = parsers[name](csv_text)
    if parsed.get("errors"):
        errors = parsed["errors"]
        return {
            "ok": False,
            "status": "error",
            "errors": errors,
            "message": f"{len(errors)} row(s) invalid — nothing was saved",
        }
    incoming: list[dict[str, Any]] = parsed["rows"]
    if name == "network":
        current = _STATIC["network"]
        keyfn = lambda r: str(r["dc"])
    elif name == "openstack":
        current = _STATIC["openstack"]
        keyfn = lambda r: (str(r["kind"]), str(r["key"]))
    else:
        current = _STATIC["gpu"]
        keyfn = lambda r: (str(r["gpu_model"]), str(r["package_key"]))
    added, changed, unchanged = _diff_counts(current, incoming, keyfn)
    preview = {
        "ok": True,
        "status": "preview",
        "dataset": name,
        "filename": filename,
        "added": added,
        "changed": changed,
        "unchanged": unchanged,
        "rows": incoming,
        "warnings": parsed.get("warnings") or [],
        "message": f"+{added} new · {changed} changed · {unchanged} same",
    }
    if not confirm:
        return preview
    merged = _upsert_rows(current, incoming, keyfn, updated_by=updated_by)
    _STATIC[name] = merged
    audit = {
        "imported_at": _iso_now(),
        "imported_by": updated_by,
        "filename": filename,
        "dataset": name,
        "added": added,
        "changed": changed,
        "unchanged": unchanged,
    }
    _STATIC["imports"] = [audit, *(_STATIC.get("imports") or [])][:5]
    return {
        **preview,
        "status": "imported",
        "message": f"{len(incoming)} row(s) applied",
        "payload": list_static_capacity(),
    }


def _diff_counts(
    current: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
    keyfn,
) -> tuple[int, int, int]:
    index = {keyfn(r): r for r in current}
    added = changed = unchanged = 0
    for row in incoming:
        key = keyfn(row)
        if key not in index:
            added += 1
        elif _row_qty_equal(index[key], row):
            unchanged += 1
        else:
            changed += 1
    return added, changed, unchanged


def _row_qty_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    skip = {"source", "updated_by", "updated_at", "notes"}
    keys = set(left) | set(right)
    for key in keys:
        if key in skip:
            continue
        if left.get(key) != right.get(key):
            return False
    return True


def _upsert_rows(
    current: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
    keyfn,
    *,
    updated_by: str,
) -> list[dict[str, Any]]:
    stamp = _iso_now()
    by_key = {keyfn(r): deepcopy(r) for r in current}
    for row in incoming:
        merged = deepcopy(row)
        merged["source"] = "csv"
        merged["updated_by"] = updated_by
        merged["updated_at"] = stamp
        by_key[keyfn(row)] = merged
    # Keep original order, then append brand-new keys.
    seen: set[Any] = set()
    out: list[dict[str, Any]] = []
    for row in current:
        key = keyfn(row)
        out.append(by_key[key])
        seen.add(key)
    for row in incoming:
        key = keyfn(row)
        if key not in seen:
            out.append(by_key[key])
            seen.add(key)
    return out


def _read_csv_table(text: str) -> tuple[list[str], list[tuple[int, dict[str, str]]]]:
    stream = io.StringIO((text or "").lstrip("\ufeff"))
    reader = csv.reader(stream)
    try:
        raw_header = next(reader)
    except StopIteration:
        return [], []
    headers = [h.strip().lstrip("\ufeff").lower() for h in raw_header]
    rows: list[tuple[int, dict[str, str]]] = []
    for line_no, cells in enumerate(reader, start=2):
        if not any(str(c).strip() for c in cells):
            continue
        rec = {headers[i]: (cells[i] if i < len(cells) else "") for i in range(len(headers))}
        rows.append((line_no, rec))
    return headers, rows


def _missing(headers: list[str], required: tuple[str, ...]) -> list[str]:
    present = set(headers)
    return [c for c in required if c not in present]


def _parse_bool(raw: str, *, line: int, field: str) -> tuple[bool | None, dict[str, Any] | None]:
    token = str(raw).strip().lower()
    if token in _TRUE:
        return True, None
    if token in _FALSE:
        return False, None
    return None, {"line": line, "message": f"Line {line}: '{field}' is not boolean ({raw!r})"}


def _parse_number(raw: str, *, line: int, field: str, integer: bool = False) -> tuple[float | None, dict[str, Any] | None]:
    text = str(raw).strip().replace(" ", "").replace(",", ".")
    if text == "":
        return None, {"line": line, "message": f"Line {line}: '{field}' cannot be empty"}
    try:
        value = float(text)
    except ValueError:
        return None, {"line": line, "message": f"Line {line}: '{field}' is not a number ({raw!r})"}
    if value < 0:
        return None, {"line": line, "message": f"Line {line}: {field} cannot be negative"}
    if integer and not float(value).is_integer():
        return None, {"line": line, "message": f"Line {line}: {field} must be an integer"}
    return value, None


def _parse_network_csv(text: str) -> dict[str, Any]:
    headers, records = _read_csv_table(text)
    missing = _missing(headers, _NETWORK_HEADERS)
    if missing:
        return {"errors": [{"line": 1, "message": f"Missing column '{name}'"} for name in missing], "rows": []}
    errors: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for line, rec in records:
        dc = "".join(str(rec.get("dc") or "").split()).upper()
        if dc not in _KNOWN_DCS:
            errors.append({"line": line, "message": f"Line {line}: unknown DC '{rec.get('dc')}'"})
            continue
        if dc in seen:
            errors.append({"line": line, "message": f"Line {line}: DC {dc} duplicated"})
            continue
        seen[dc] = line
        ints: dict[str, int] = {}
        ok_row = True
        for field in ("public_ip", "subnet_30", "spine_port", "leaf_port", "mgmt_port"):
            val, err = _parse_number(rec.get(field, ""), line=line, field=field, integer=True)
            if err:
                errors.append(err)
                ok_row = False
            else:
                ints[field] = int(val or 0)
        floats: dict[str, float] = {}
        for field in ("internet_total_mbps", "internet_sellable_mbps", "ddos_sellable_mbps"):
            val, err = _parse_number(rec.get(field, ""), line=line, field=field)
            if err:
                errors.append(err)
                ok_row = False
            else:
                floats[field] = float(val or 0)
        capable, err = _parse_bool(rec.get("ddos_capable", ""), line=line, field="ddos_capable")
        if err:
            errors.append(err)
            ok_row = False
        if not ok_row:
            continue
        if floats["internet_sellable_mbps"] > floats["internet_total_mbps"]:
            errors.append({"line": line, "message": f"Line {line}: internet_sellable exceeds internet_total"})
            continue
        if capable is False and floats["ddos_sellable_mbps"] > 0:
            errors.append(
                {
                    "line": line,
                    "message": f"Line {line}: ddos_capable=false cannot have ddos_sellable_mbps > 0",
                }
            )
            continue
        rows.append(
            {
                "dc": dc,
                "public_ip": ints["public_ip"],
                "subnet_30": ints["subnet_30"],
                "spine_port": ints["spine_port"],
                "leaf_port": ints["leaf_port"],
                "mgmt_port": ints["mgmt_port"],
                "internet_total_mbps": floats["internet_total_mbps"],
                "internet_sellable_mbps": floats["internet_sellable_mbps"],
                "ddos_capable": bool(capable),
                "ddos_sellable_mbps": floats["ddos_sellable_mbps"],
                "notes": "",
                "source": "csv",
            }
        )
    return {"errors": errors, "rows": rows}


def _parse_openstack_csv(text: str) -> dict[str, Any]:
    headers, records = _read_csv_table(text)
    missing = _missing(headers, _OPENSTACK_HEADERS)
    if missing:
        return {"errors": [{"line": 1, "message": f"Missing column '{name}'"} for name in missing], "rows": []}
    errors: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], int] = {}
    for line, rec in records:
        kind = str(rec.get("kind") or "").strip().lower()
        key = str(rec.get("key") or "").strip()
        if kind not in _OS_KINDS:
            errors.append({"line": line, "message": f"Line {line}: unknown kind '{rec.get('kind')}'"})
            continue
        if not key:
            errors.append({"line": line, "message": f"Line {line}: 'key' is required"})
            continue
        ident = (kind, key)
        if ident in seen:
            errors.append({"line": line, "message": f"Line {line}: {kind}/{key} duplicated"})
            continue
        seen[ident] = line
        qty, err = _parse_number(rec.get("quantity", ""), line=line, field="quantity")
        if err:
            errors.append(err)
            continue
        rows.append(
            {
                "kind": kind,
                "key": key,
                "label": str(rec.get("label") or key),
                "quantity": float(qty or 0),
                "unit": str(rec.get("unit") or ""),
                "hypervisor": str(rec.get("hypervisor") or ""),
                "notes": str(rec.get("notes") or ""),
                "aux_total": None,
                "aux_used": None,
                "source": "csv",
            }
        )
    return {"errors": errors, "rows": rows}


def _parse_gpu_csv(text: str) -> dict[str, Any]:
    headers, records = _read_csv_table(text)
    missing = _missing(headers, _GPU_HEADERS)
    if missing:
        return {"errors": [{"line": 1, "message": f"Missing column '{name}'"} for name in missing], "rows": []}
    errors: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], int] = {}
    for line, rec in records:
        model = str(rec.get("gpu_model") or "").strip()
        package = str(rec.get("package_key") or "").strip()
        if not model:
            errors.append({"line": line, "message": f"Line {line}: 'gpu_model' is required"})
            continue
        if not package:
            errors.append({"line": line, "message": f"Line {line}: 'package_key' is required"})
            continue
        ident = (model, package)
        if ident in seen:
            errors.append({"line": line, "message": f"Line {line}: {model}/{package} duplicated"})
            continue
        seen[ident] = line
        qty, err = _parse_number(rec.get("quantity", ""), line=line, field="quantity")
        if err:
            errors.append(err)
            continue
        rows.append(
            {
                "gpu_model": model,
                "package_key": package,
                "quantity": float(qty or 0),
                "hypervisor": str(rec.get("hypervisor") or ""),
                "notes": str(rec.get("notes") or ""),
                "source": "csv",
            }
        )
    return {"errors": errors, "rows": rows}


# ---------------------------------------------------------------------------
# Sales parameters + scenarios (W1 + W6) — GUI crm-engine /crm/config/sales-*
# ---------------------------------------------------------------------------

_USAGE_BASIS_VALUES = frozenset({"max", "avg", "cur"})
_REPLICATION_PROVIDERS = frozenset({"veeam", "zerto"})
_WAFLB_APPLIANCES = frozenset({"5g", "1g", "200m"})
_SCOPE_KINDS = frozenset({"panel", "family", "line"})
_DISCOUNT_KINDS = frozenset({"new_sale", "upsell"})
_BUILTIN_SCENARIO_KEYS = frozenset({"S1", "S2", "S3", "S4"})
_SCENARIO_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,31}$")
_SALES_CALC_TYPES = {
    "usage_basis": "enum",
    "upsell_enabled": "bool",
    "replication_provider": "enum",
    "waflb_appliance": "enum",
    "waflb_distribute": "bool",
}
_GAP_PAYLOAD = {"replication_share": None, "ibm_ambiguous_disk_share": None}
_FAMILY_DISCOUNT_KEYS = (
    "virt_km",
    "virt_hyperconverged",
    "virt_power",
    "backup_veeam_replication",
    "backup_zerto_replication",
)


def _discount_row(scope_kind: str, scope_key: str, kind: str, ratio: float = 0.0, updated_by: str = "seed") -> dict[str, Any]:
    return {
        "scope_kind": scope_kind,
        "scope_key": scope_key,
        "kind": kind,
        "ratio": float(ratio),
        "updated_by": updated_by,
        "updated_at": "2026-08-23T09:00:00+00:00",
    }


_DISCOUNT_SEED: list[dict[str, Any]] = [
    _discount_row("family", fam, kind)
    for fam in _FAMILY_DISCOUNT_KEYS
    for kind in ("new_sale", "upsell")
]


def _scenario_seed_row(key: str, sort_order: int) -> dict[str, Any]:
    return {
        "scenario_key": key,
        "label": key,
        "payload": deepcopy(_GAP_PAYLOAD),
        "is_builtin": True,
        "sort_order": sort_order,
        "created_by": "seed",
        "created_at": "2026-08-23T09:00:00+00:00",
    }


_SCENARIO_SEED: list[dict[str, Any]] = [
    _scenario_seed_row("S1", 10),
    _scenario_seed_row("S2", 20),
    _scenario_seed_row("S3", 30),
    _scenario_seed_row("S4", 40),
]

_DISCOUNTS: list[dict[str, Any]] = deepcopy(_DISCOUNT_SEED)
_SCENARIOS: dict[str, dict[str, Any]] = {r["scenario_key"]: deepcopy(r) for r in _SCENARIO_SEED}
_THRESHOLDS_SEED = deepcopy(_THRESHOLDS)
_RESOURCE_RATIOS_SEED = deepcopy(_RESOURCE_RATIOS)
_CALC_CONFIG_SEED = deepcopy(_CALC_CONFIG)
_THRESH_ID_SEQ_SEED = 3


def reset_sales_config() -> None:
    """Test helper: restore W1 calc keys, discounts, scenarios, thresholds, ratios."""
    global _DISCOUNTS, _SCENARIOS, _THRESHOLDS, _RESOURCE_RATIOS, _THRESH_ID_SEQ, _CALC_CONFIG
    _DISCOUNTS = deepcopy(_DISCOUNT_SEED)
    _SCENARIOS = {r["scenario_key"]: deepcopy(r) for r in _SCENARIO_SEED}
    _THRESHOLDS = deepcopy(_THRESHOLDS_SEED)
    _RESOURCE_RATIOS = deepcopy(_RESOURCE_RATIOS_SEED)
    _CALC_CONFIG = deepcopy(_CALC_CONFIG_SEED)
    _THRESH_ID_SEQ = _THRESH_ID_SEQ_SEED


def _as_bool(raw: Any) -> bool:
    return str(raw).strip().lower() in {"true", "1", "yes", "on"}


def _sales_calc_dict() -> dict[str, Any]:
    def _val(key: str, default: str) -> str:
        row = _CALC_CONFIG.get(key) or {}
        return str(row.get("config_value", default))

    return {
        "usage_basis": _val("usage_basis", "max"),
        "upsell_enabled": _as_bool(_val("upsell_enabled", "false")),
        "replication_provider": _val("replication_provider", "veeam"),
        "waflb_appliance": _val("waflb_appliance", "5g"),
        "waflb_distribute": _as_bool(_val("waflb_distribute", "false")),
    }


def _sales_etag() -> str:
    blob = json.dumps(
        {
            "calc": _sales_calc_dict(),
            "discounts": _DISCOUNTS,
            "thresholds": _THRESHOLDS,
            "ratios": _RESOURCE_RATIOS,
        },
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.blake2s(blob.encode("utf-8"), digest_size=4).hexdigest()


def list_sales_discounts() -> list[dict[str, Any]]:
    return deepcopy(_DISCOUNTS)


def get_sales_parameters() -> dict[str, Any]:
    return {
        "calc": _sales_calc_dict(),
        "thresholds": deepcopy(_THRESHOLDS),
        "ratios": deepcopy(_RESOURCE_RATIOS),
        "discounts": deepcopy(_DISCOUNTS),
        "etag": _sales_etag(),
    }


def put_sales_calc(
    *,
    usage_basis: Optional[str] = None,
    upsell_enabled: Optional[bool] = None,
    replication_provider: Optional[str] = None,
    waflb_appliance: Optional[str] = None,
    waflb_distribute: Optional[bool] = None,
) -> dict[str, Any]:
    updated: list[str] = []
    pairs: list[tuple[str, str]] = []
    if usage_basis is not None:
        if usage_basis not in _USAGE_BASIS_VALUES:
            raise ValueError("usage_basis must be max/avg/cur")
        pairs.append(("usage_basis", usage_basis))
    if upsell_enabled is not None:
        pairs.append(("upsell_enabled", "true" if upsell_enabled else "false"))
    if replication_provider is not None:
        if replication_provider not in _REPLICATION_PROVIDERS:
            raise ValueError("replication_provider must be veeam or zerto")
        pairs.append(("replication_provider", replication_provider))
    if waflb_appliance is not None:
        if waflb_appliance not in _WAFLB_APPLIANCES:
            raise ValueError("waflb_appliance must be 5g/1g/200m")
        pairs.append(("waflb_appliance", waflb_appliance))
    if waflb_distribute is not None:
        pairs.append(("waflb_distribute", "true" if waflb_distribute else "false"))
    for key, value in pairs:
        upsert_calc_config(
            config_key=key,
            config_value=value,
            value_type=_SALES_CALC_TYPES[key],
            description=None,
        )
        updated.append(key)
    return {"status": "ok", "updated": updated, "sales_defaults_deleted": 0}


def put_sales_discount(
    *,
    scope_kind: str,
    scope_key: str,
    kind: str,
    ratio: float,
) -> dict[str, Any]:
    if scope_kind not in _SCOPE_KINDS:
        raise ValueError("scope_kind must be panel/family/line")
    if kind not in _DISCOUNT_KINDS:
        raise ValueError("kind must be new_sale or upsell")
    if ratio < 0 or ratio >= 1:
        raise ValueError("ratio must be >= 0 and < 1")
    key = str(scope_key or "").strip()
    if not key:
        raise ValueError("scope_key is required")
    stamp = _iso_now()
    for row in _DISCOUNTS:
        if row["scope_kind"] == scope_kind and row["scope_key"] == key and row["kind"] == kind:
            row["ratio"] = float(ratio)
            row["updated_by"] = "mock"
            row["updated_at"] = stamp
            return {"status": "ok", "sales_defaults_deleted": 0}
    _DISCOUNTS.append(
        _discount_row(scope_kind, key, kind, float(ratio), updated_by="mock")
    )
    _DISCOUNTS[-1]["updated_at"] = stamp
    return {"status": "ok", "sales_defaults_deleted": 0}


def put_sales_threshold(
    *,
    resource_type: str,
    dc_code: str,
    sellable_limit_pct: float,
    notes: Optional[str] = None,
    panel_key: Optional[str] = None,
) -> dict[str, Any]:
    if sellable_limit_pct < 0 or sellable_limit_pct > 100:
        raise ValueError("sellable_limit_pct must be between 0 and 100")
    upsert_threshold(
        resource_type=resource_type,
        dc_code=dc_code or "*",
        sellable_limit_pct=sellable_limit_pct,
        notes=notes,
        panel_key=panel_key,
    )
    return {"status": "ok", "sales_defaults_deleted": 0}


def put_sales_ratio(
    family: str,
    *,
    dc_code: str = "*",
    cpu_per_unit: float = 1.0,
    ram_gb_per_unit: float = 8.0,
    storage_gb_per_unit: float = 100.0,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    if cpu_per_unit <= 0 or ram_gb_per_unit <= 0 or storage_gb_per_unit <= 0:
        raise ValueError("ratios must be > 0")
    fam = str(family or "").strip()
    if not fam:
        raise ValueError("family is required")
    dc = (dc_code or "*").strip() or "*"
    stamp = _iso_now()
    for row in _RESOURCE_RATIOS:
        if row["family"] == fam and row["dc_code"] == dc:
            row["cpu_per_unit"] = float(cpu_per_unit)
            row["ram_gb_per_unit"] = float(ram_gb_per_unit)
            row["storage_gb_per_unit"] = float(storage_gb_per_unit)
            row["notes"] = notes
            row["updated_by"] = "mock"
            row["updated_at"] = stamp
            return {"status": "ok", "family": fam, "sales_defaults_deleted": 0}
    _RESOURCE_RATIOS.append(
        {
            "family": fam,
            "dc_code": dc,
            "cpu_per_unit": float(cpu_per_unit),
            "ram_gb_per_unit": float(ram_gb_per_unit),
            "storage_gb_per_unit": float(storage_gb_per_unit),
            "notes": notes,
            "updated_by": "mock",
            "updated_at": stamp,
        }
    )
    return {"status": "ok", "family": fam, "sales_defaults_deleted": 0}


def _scenario_public(row: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(row)


def list_sales_scenarios() -> list[dict[str, Any]]:
    rows = [_scenario_public(r) for r in _SCENARIOS.values()]
    rows.sort(key=lambda r: (int(r.get("sort_order") or 100), str(r.get("scenario_key") or "")))
    return rows


def _is_builtin_scenario(key: str, row: Optional[dict[str, Any]] = None) -> bool:
    if key in _BUILTIN_SCENARIO_KEYS:
        return True
    return bool(row and row.get("is_builtin"))


def _validate_scenario_key(key: str, *, allow_builtin: bool = False) -> str:
    cleaned = str(key or "").strip()
    if not cleaned or not _SCENARIO_KEY_RE.match(cleaned):
        raise ValueError("scenario_key must be 1–32 chars [A-Za-z][A-Za-z0-9_-]*")
    if not allow_builtin and cleaned in _BUILTIN_SCENARIO_KEYS:
        raise ValueError(f"{cleaned} is reserved for builtin S1–S4")
    return cleaned


def _parse_scenario_payload(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError) as exc:
            raise ValueError("payload must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return dict(payload)


def create_sales_scenario(
    *,
    scenario_key: str,
    label: str,
    payload: Optional[dict[str, Any]] = None,
    sort_order: int = 100,
    created_by: str = "mock",
) -> dict[str, Any]:
    key = _validate_scenario_key(scenario_key)
    if key in _SCENARIOS:
        raise ValueError(f"{key} already exists")
    body = _parse_scenario_payload(payload)
    title = (label or key).strip() or key
    row = {
        "scenario_key": key,
        "label": title,
        "payload": body,
        "is_builtin": False,
        "sort_order": int(sort_order or 100),
        "created_by": created_by,
        "created_at": _iso_now(),
    }
    _SCENARIOS[key] = row
    return _scenario_public(row)


def update_sales_scenario(
    scenario_key: str,
    *,
    label: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
    sort_order: Optional[int] = None,
) -> dict[str, Any]:
    key = str(scenario_key or "").strip()
    row = _SCENARIOS.get(key)
    if not row:
        raise ValueError(f"unknown scenario {key}")
    if _is_builtin_scenario(key, row):
        raise ValueError(f"{key} is builtin and cannot be changed")
    if label is not None:
        row["label"] = (label or row["label"]).strip() or row["label"]
    if payload is not None:
        row["payload"] = _parse_scenario_payload(payload)
    if sort_order is not None:
        row["sort_order"] = int(sort_order)
    return _scenario_public(row)


def delete_sales_scenario(scenario_key: str) -> dict[str, Any]:
    key = str(scenario_key or "").strip()
    row = _SCENARIOS.get(key)
    if not row:
        raise ValueError(f"unknown scenario {key}")
    if _is_builtin_scenario(key, row):
        raise ValueError(f"{key} is builtin and cannot be deleted")
    del _SCENARIOS[key]
    return {"status": "ok", "scenario_key": key}


def _suggest_copy_key(source_key: str) -> str:
    taken = set(_SCENARIOS)
    candidate = f"{source_key}_copy"
    if candidate not in taken:
        return candidate
    n = 2
    while f"{source_key}_copy_{n}" in taken:
        n += 1
    return f"{source_key}_copy_{n}"


def copy_sales_scenario(
    scenario_key: str,
    *,
    new_key: Optional[str] = None,
    label: Optional[str] = None,
    created_by: str = "mock",
) -> dict[str, Any]:
    src_key = str(scenario_key or "").strip()
    src = _SCENARIOS.get(src_key)
    if not src:
        raise ValueError(f"unknown scenario {src_key}")
    dest = _validate_scenario_key(new_key) if new_key else _validate_scenario_key(_suggest_copy_key(src_key))
    if dest in _SCENARIOS:
        raise ValueError(f"{dest} already exists")
    src_label = str(src.get("label") or src_key)
    row = {
        "scenario_key": dest,
        "label": (label or f"{src_label} (copy)").strip() or f"{src_label} (copy)",
        "payload": deepcopy(src.get("payload") or {}),
        "is_builtin": False,
        "sort_order": int(src.get("sort_order") or 100),
        "created_by": created_by,
        "created_at": _iso_now(),
    }
    _SCENARIOS[dest] = row
    return _scenario_public(row)


def customer_sales_summary(_customer_name: str) -> dict[str, Any]:
    """Mock payload aligned with customer-api SalesSummary (YTD + lifetime)."""
    return {
        "ytd_revenue_total": 125000.0,
        "invoice_count": 3,
        "currency": "TRY",
        "lifetime_revenue_total": 480000.0,
        "lifetime_order_count": 11,
        "pipeline_value": 0.0,
        "opportunity_count": 0,
        "active_order_count": 1,
        "active_order_value": 15000.0,
        "active_contract_count": 0,
        "total_contract_value": 0.0,
        "estimated_mrr": 0.0,
    }


def customer_sales_service_breakdown(_customer_name: str) -> list[dict[str, Any]]:
    return [
        {"service_code": "virt_hyperconverged", "service_label": "Hyperconverged", "amount_tl": 82000.0},
        {"service_code": "backup_veeam", "service_label": "Veeam backup", "amount_tl": 43000.0},
    ]


def customer_sales_items(_customer_name: str) -> list[dict[str, Any]]:
    return [
        {
            "source_type": "salesorder",
            "reference_number": "PRJ-MOCK-001",
            "date": "2026-03-18",
            "status": "Fulfilled",
            "product_name": "Hyperconverged Mimari Intel RAM",
            "quantity": 16.0,
            "line_total": 42000.0,
            "currency": "TRY",
        }
    ]


def customer_sales_active_orders(_customer_name: str) -> list[dict[str, Any]]:
    return [
        {
            "source_type": "salesorder",
            "reference_number": "PRJ-MOCK-OPEN-001",
            "date": "2026-05-01",
            "status": "Active",
            "order_total": 15000.0,
            "line_count": 2,
            "currency": "TRY",
        }
    ]


def customer_catalog() -> dict[str, Any]:
    """Mock catalog row with active order fields for /customers page."""
    return {
        "customers": [
            {
                "crm_accountid": "00000000-0000-0000-0000-00000000ACC1",
                "crm_account_name": "Mock Customer A",
                "display_name": "Mock Customer A",
                "is_vip": False,
                "cache_pinned": False,
                "mapped": True,
                "mapping_status": "seed",
                "mapping_count": 1,
                "real_data_cached": False,
                "overuse_status": "overuse",
                "ytd_revenue": 125000.0,
                "active_order_value": 15000.0,
                "active_order_count": 1,
                "currency": "TRY",
                "list_group": "mapped",
            }
        ],
        "groups": {
            "vip": [],
            "mapped": [],
            "unmapped": [],
        },
    }


def customer_resource_compliance(_customer_name: str, scope: str = "virtualization") -> dict[str, Any]:
    """ASELSANNET-style mock: hyperconverged overage + classic unsold usage."""
    if scope != "virtualization":
        return {"scope": scope, "rows": [], "summary": {"total_overage_loss_tl": 0.0, "has_overuse": False, "overuse_categories": [], "overuse_status": "ok"}}
    rows = [
        {
            "category_code": "virt_hyperconverged_cpu",
            "category_label": "Hyperconverged Mimari — CPU",
            "gui_tab_binding": "virtualization.hyperconverged",
            "resource_unit": "vCPU",
            "entitled_qty": 18.0,
            "entitled_amount_tl": 1899.12,
            "used_qty": 550.0,
            "overage_qty": 532.0,
            "unit_price_tl": 105.57,
            "price_source": "order_weighted",
            "overage_loss_tl": round(532.0 * 105.57, 2),
            "efficiency_pct": round(550.0 / 18.0 * 100.0, 2),
            "status": "over",
            "usage_note": None,
        },
        {
            "category_code": "virt_hyperconverged_ram",
            "category_label": "Hyperconverged Mimari — RAM",
            "gui_tab_binding": "virtualization.hyperconverged",
            "resource_unit": "GB",
            "entitled_qty": 128.0,
            "entitled_amount_tl": 7717.12,
            "used_qty": 1996.8,
            "overage_qty": 1868.8,
            "unit_price_tl": 60.29,
            "price_source": "order_weighted",
            "overage_loss_tl": round(1868.8 * 60.29, 2),
            "efficiency_pct": round(1996.8 / 128.0 * 100.0, 2),
            "status": "over",
            "usage_note": None,
        },
        {
            "category_code": "virt_classic_cpu",
            "category_label": "Klasik Mimari (KM) — CPU",
            "gui_tab_binding": "virtualization.classic",
            "resource_unit": "vCPU",
            "entitled_qty": 0.0,
            "entitled_amount_tl": 0.0,
            "used_qty": 42.0,
            "overage_qty": 42.0,
            "unit_price_tl": 50.0,
            "price_source": "catalog_name",
            "overage_loss_tl": 2100.0,
            "efficiency_pct": None,
            "status": "unsold_usage",
            "usage_note": None,
        },
    ]
    total_loss = round(sum(float(r["overage_loss_tl"]) for r in rows), 2)
    return {
        "scope": scope,
        "rows": rows,
        "summary": {
            "total_overage_loss_tl": total_loss,
            "has_overuse": True,
            "overuse_categories": [r["category_code"] for r in rows if r["status"] in ("over", "unsold_usage")],
            "overuse_status": "overuse",
        },
    }


def customer_sales_active_items(_customer_name: str) -> list[dict[str, Any]]:
    return [
        {
            "source_type": "salesorder",
            "reference_number": "PRJ-MOCK-OPEN-001",
            "date": "2026-05-01",
            "status": "Active",
            "product_name": "Managed backup storage",
            "quantity": 500.0,
            "unit_price": 20.0,
            "line_total": 10000.0,
            "currency": "TRY",
        },
        {
            "source_type": "salesorder",
            "reference_number": "PRJ-MOCK-OPEN-001",
            "date": "2026-05-01",
            "status": "Active",
            "product_name": "Monitoring per VM",
            "quantity": 50.0,
            "unit_price": 100.0,
            "line_total": 5000.0,
            "currency": "TRY",
        },
    ]
