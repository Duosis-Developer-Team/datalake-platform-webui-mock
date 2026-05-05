"""Mock AuraNotify-style DC availability item for Availability tab."""

from __future__ import annotations

from typing import Any, Optional

from src.services.mock_data.datacenters import get_dc_detail
from src.utils.dc_display import format_dc_display_name


def _norm_dc(dc_code: str) -> str:
    return (dc_code or "").strip().upper()


def get_dc_availability_sla_item(
    dc_code: str, dc_display_name: str, _tr: dict | None = None
) -> Optional[dict[str, Any]]:
    """Minimal item so the Availability tab shows SLA header without external API."""
    key = _norm_dc(dc_code)
    meta_name = (get_dc_detail(key).get("meta") or {}).get("name") or dc_display_name
    pct = {"IST-DC1": 99.982, "ANK-DC1": 99.91, "IZM-DC1": 99.85, "FRA-DC1": 99.995}.get(key, 99.9)
    return {
        "group_name": meta_name,
        "availability_pct": pct,
        "period_min": 10080,
        "total_downtime_min": max(0, int((100 - pct) * 6)),
        "categories": [],
    }


def get_dc_availability_sla_items_for_dcs(
    dc_rows: list[dict[str, Any]],
    tr: dict | None = None,
) -> dict[str, Optional[dict[str, Any]]]:
    """One lookup per DC using mock SLA rows (same shape as live batch helper)."""
    out: dict[str, Optional[dict[str, Any]]] = {}
    for row in dc_rows:
        rid = row.get("id")
        if rid is None:
            continue
        sid = str(rid)
        dc_name = format_dc_display_name(row.get("name"), row.get("description")) or str(row.get("name") or sid)
        out[sid] = get_dc_availability_sla_item(sid, dc_name, tr)
    return out
