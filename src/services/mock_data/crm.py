"""Mutable mock payloads for CRM Settings pages (WebUI App DB contract).

These datasets intentionally mirror the FastAPI response shapes used by `customer-api`.
"""

from __future__ import annotations

from copy import deepcopy
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
