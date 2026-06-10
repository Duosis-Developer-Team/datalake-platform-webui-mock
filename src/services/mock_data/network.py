"""Mock Zabbix network dashboard filters, port summary, percentile, and interface table."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from src.services.mock_data.datacenters import MOCK_DC_CODES


def _norm(dc_code: str) -> str:
    return (dc_code or "").strip().upper()


def _bps(gbps: float) -> float:
    return gbps * 1e9


def get_dc_network_filters(
    dc_code: str,
    _tr: dict | None = None,
    interface_scope: Optional[str] = None,
) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {}
    scope = interface_scope or "overview"
    all_devices = {
        "Cisco": [f"{k.lower()}-bb-sw-01", f"{k.lower()}-leaf-01", f"{k.lower()}-router-01"],
        "Arista": [f"{k.lower()}-arista-leaf-01", f"{k.lower()}-arista-spine-01"],
    }
    if scope == "backbone":
        all_devices = {"Cisco": [f"{k.lower()}-bb-sw-01"]}
    elif scope == "leaf":
        all_devices = {
            "Cisco": [f"{k.lower()}-leaf-01"],
            "Arista": [f"{k.lower()}-arista-leaf-01"],
        }
    elif scope == "spine":
        all_devices = {"Arista": [f"{k.lower()}-arista-spine-01"]}
    elif scope == "router_uplink":
        all_devices = {"Cisco": [f"{k.lower()}-router-01"]}
    return {
        "manufacturers": sorted(all_devices.keys()),
        "devices_by_manufacturer": all_devices,
        "interface_scope": scope,
    }


def get_dc_network_port_summary(
    dc_code: str,
    _tr: dict | None = None,
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
    interface_scope: Optional[str] = None,
) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {}
    base_devices = 18 if k == "IST-DC1" else 12 if k in ("ANK-DC1", "FRA-DC1") else 10
    scope = interface_scope or "overview"
    if scope == "backbone":
        base_devices = max(2, base_devices // 4)
    elif scope in ("leaf", "spine", "management"):
        base_devices = max(3, base_devices // 3)
    elif scope == "router_uplink":
        base_devices = max(1, base_devices // 6)
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
    interface_scope: Optional[str] = None,
) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {}
    top: list[dict[str, Any]] = []
    for i in range(min(top_n, 8)):
        gbps = 8.5 - i * 0.35 + (0.1 if k == "IZM-DC1" else 0)
        prefix = (interface_scope or "overview")[:4]
        top.append(
            {
                "host": f"{k.lower()}-{prefix}-sw-01",
                "interface_name": f"xe-0/0/{i}",
                "interface_alias": f"g{i}hv1{k.lower()}",
                "p95_rx_bps": _bps(gbps * 0.55),
                "p95_tx_bps": _bps(gbps * 0.45),
                "p95_total_bps": _bps(gbps),
                "speed_bps": _bps(10.0),
                "utilization_pct": min(99.0, 55.0 + i * 3.2),
            }
        )
    util = 62.0 if k == "IZM-DC1" else 48.0
    return {
        "overall_port_utilization_pct": util,
        "top_interfaces": top,
        "interface_scope": interface_scope or "overview",
    }


def get_dc_network_interface_table(
    dc_code: str,
    _tr: dict | None = None,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
    interface_scope: Optional[str] = None,
) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}
    items = []
    for i in range(12):
        items.append(
            {
                "host": f"{k.lower()}-{(interface_scope or 'overview')}-sw-01",
                "interface_name": f"eth1/{i}",
                "interface_alias": f"g{i}customer{k.lower()}",
                "p95_rx_bps": _bps(1.8 + i * 0.08),
                "p95_tx_bps": _bps(1.4 + i * 0.07),
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
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "interface_scope": interface_scope or "overview",
    }


def get_dc_network_firewall_summary(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {"devices": []}
    return {
        "devices": [
            {
                "host": f"{k.lower()}-fw-01",
                "device_name": f"{k.lower()}-fw-01",
                "manufacturer_name": "Fortinet",
                "cpu_utilization_pct": 12.5,
                "memory_utilization_pct": 41.0,
                "active_sessions": 18200,
                "intrusions_detected": 3,
                "intrusions_blocked": 3,
                "ha_mode": "active-passive",
                "icmp_loss_pct": 0.0,
            }
        ]
    }


def get_dc_network_load_balancer_summary(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in MOCK_DC_CODES:
        return {"devices": []}
    return {
        "devices": [
            {
                "host": f"{k.lower()}-lb-01",
                "device_name": f"{k.lower()}-citrix-adc-01",
                "manufacturer_name": "Citrix",
                "cpu_utilization_pct": 18.0,
                "memory_utilization_pct": 52.0,
                "icmp_loss_pct": 0.0,
                "active_ports_count": 4,
                "total_ports_count": 8,
            }
        ]
    }
