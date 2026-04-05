"""Mock Zabbix network dashboard filters, port summary, percentile, and interface table."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from src.services.mock_data.datacenters import MOCK_DC_CODES


def _norm(dc_code: str) -> str:
    return (dc_code or "").strip().upper()


def _bps(gbps: float) -> float:
    return gbps * 1e9


def get_dc_network_filters(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {}
    return {
        "manufacturers": ["Cisco", "Arista", "Juniper"],
        "roles_by_manufacturer": {
            "Cisco": ["Core", "Aggregation", "Access"],
            "Arista": ["Leaf", "Spine"],
            "Juniper": ["Edge", "Core"],
        },
        "devices_by_manufacturer_role": {
            "Cisco": {
                "Core": [f"{k.lower()}-cisco-core-01", f"{k.lower()}-cisco-core-02"],
                "Aggregation": [f"{k.lower()}-cisco-aggr-01"],
                "Access": [f"{k.lower()}-cisco-acc-01", f"{k.lower()}-cisco-acc-02"],
            },
            "Arista": {
                "Leaf": [f"{k.lower()}-arista-leaf-01", f"{k.lower()}-arista-leaf-02"],
                "Spine": [f"{k.lower()}-arista-spine-01"],
            },
            "Juniper": {
                "Edge": [f"{k.lower()}-juniper-edge-01"],
                "Core": [f"{k.lower()}-juniper-core-01"],
            },
        },
    }


def get_dc_network_port_summary(
    dc_code: str,
    _tr: dict | None = None,
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {}
    base_devices = 18 if k == "IST-DC1" else 12 if k in ("ANK-DC1", "FRA-DC1") else 10
    if device_name:
        base_devices = 1
    elif device_role:
        base_devices = max(2, base_devices // 3)
    elif manufacturer:
        base_devices = max(4, base_devices // 2)
    total_ports = base_devices * 48
    active_ports = int(total_ports * 0.81)
    return {
        "device_count": base_devices,
        "total_ports": total_ports,
        "active_ports": active_ports,
        "avg_icmp_loss_pct": 0.35 if k == "IZM-DC1" else 0.08,
    }


def get_dc_network_95th_percentile(
    dc_code: str,
    _tr: dict | None = None,
    top_n: int = 20,
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {}
    top: list[dict[str, Any]] = []
    for i in range(min(top_n, 8)):
        gbps = 8.5 - i * 0.35 + (0.1 if k == "IZM-DC1" else 0)
        top.append(
            {
                "interface_name": f"xe-0/0/{i}",
                "p95_total_bps": _bps(gbps),
                "speed_bps": _bps(10.0),
                "utilization_pct": min(99.0, 55.0 + i * 3.2),
            }
        )
    util = 62.0 if k == "IZM-DC1" else 48.0
    return {"overall_port_utilization_pct": util, "top_interfaces": top}


def get_dc_network_interface_table(
    dc_code: str,
    _tr: dict | None = None,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}
    items = []
    for i in range(12):
        items.append(
            {
                "interface_name": f"eth1/{i}",
                "interface_alias": f"uplink-{k}-{i}",
                "p95_total_bps": _bps(3.2 + i * 0.15),
                "speed_bps": _bps(10.0),
                "utilization_pct": 22.0 + i * 2.1,
            }
        )
    if search:
        q = search.lower()
        items = [x for x in items if q in (x.get("interface_name") or "").lower() or q in (x.get("interface_alias") or "").lower()]
    total = len(items)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return {"items": items[start:end], "total": total, "page": page, "page_size": page_size}
