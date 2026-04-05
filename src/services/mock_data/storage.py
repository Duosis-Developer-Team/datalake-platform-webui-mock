"""Mock S3, SAN, block storage, and Zabbix storage APIs per datacenter."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from src.services.mock_data.datacenters import MOCK_DC_CODES


def _norm(dc_code: str) -> str:
    return (dc_code or "").strip().upper()


def _tb_to_bytes(tb: float) -> int:
    return int(tb * 1024 * 1024 * 1024 * 1024)


_S3: dict[str, dict[str, Any]] = {
    "IST-DC1": {
        "pools": ["s3-ist-prod", "s3-ist-analytics"],
        "latest": {
            "s3-ist-prod": {"usable_bytes": _tb_to_bytes(320), "used_bytes": _tb_to_bytes(188)},
            "s3-ist-analytics": {"usable_bytes": _tb_to_bytes(160), "used_bytes": _tb_to_bytes(96)},
        },
        "growth": {
            "s3-ist-prod": {"delta_used_bytes": _tb_to_bytes(2.4)},
            "s3-ist-analytics": {"delta_used_bytes": _tb_to_bytes(1.1)},
        },
    },
    "ANK-DC1": {
        "pools": ["s3-ank-primary"],
        "latest": {
            "s3-ank-primary": {"usable_bytes": _tb_to_bytes(240), "used_bytes": _tb_to_bytes(195)},
        },
        "growth": {"s3-ank-primary": {"delta_used_bytes": _tb_to_bytes(4.2)}},
    },
    "IZM-DC1": {
        "pools": ["s3-izm-edge"],
        "latest": {"s3-izm-edge": {"usable_bytes": _tb_to_bytes(180), "used_bytes": _tb_to_bytes(94)}},
        "growth": {"s3-izm-edge": {"delta_used_bytes": _tb_to_bytes(0.8)}},
    },
    "FRA-DC1": {
        "pools": ["s3-fra-tier1", "s3-fra-tier2"],
        "latest": {
            "s3-fra-tier1": {"usable_bytes": _tb_to_bytes(200), "used_bytes": _tb_to_bytes(90)},
            "s3-fra-tier2": {"usable_bytes": _tb_to_bytes(160), "used_bytes": _tb_to_bytes(72)},
        },
        "growth": {
            "s3-fra-tier1": {"delta_used_bytes": _tb_to_bytes(0.5)},
            "s3-fra-tier2": {"delta_used_bytes": _tb_to_bytes(0.4)},
        },
    },
}

_SAN_SWITCHES: dict[str, list[str]] = {
    "IST-DC1": ["brocade-ist-01", "brocade-ist-02", "brocade-ist-03", "brocade-ist-04"],
    "ANK-DC1": ["brocade-ank-01", "brocade-ank-02"],
    "IZM-DC1": ["brocade-izm-01", "brocade-izm-02"],
    "FRA-DC1": ["brocade-fra-01", "brocade-fra-02", "brocade-fra-03"],
}


def get_dc_s3_pools(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    return deepcopy(_S3.get(_norm(dc_code), {"pools": [], "latest": {}, "growth": {}}))


def get_dc_san_switches(dc_code: str, _tr: dict | None = None) -> list[str]:
    return list(_SAN_SWITCHES.get(_norm(dc_code), []))


def get_dc_san_port_usage(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    k = _norm(dc_code)
    n = len(_SAN_SWITCHES.get(k, []))
    if not n:
        return {}
    total = n * 48
    licensed = int(total * 0.92)
    active = int(licensed * 0.78)
    return {
        "total_ports": total,
        "licensed_ports": licensed,
        "active_ports": active,
        "no_link_ports": max(0, licensed - active - 4),
        "disabled_ports": max(0, total - licensed),
    }


def get_dc_san_health(dc_code: str, _tr: dict | None = None) -> list[dict[str, Any]]:
    k = _norm(dc_code)
    if not _SAN_SWITCHES.get(k):
        return []
    sw = _SAN_SWITCHES[k][0]
    return [
        {
            "switch_host": sw,
            "port_name": "0/12",
            "crc_errors_delta": 3,
            "link_failures_delta": 0,
            "loss_of_sync_delta": 0,
            "loss_of_signal_delta": 0,
        },
        {
            "switch_host": sw,
            "port_name": "0/15",
            "crc_errors_delta": 0,
            "link_failures_delta": 2,
            "loss_of_sync_delta": 0,
            "loss_of_signal_delta": 0,
        },
    ]


def get_dc_san_traffic_trend(dc_code: str, _tr: dict | None = None) -> list[dict[str, Any]]:
    if not _SAN_SWITCHES.get(_norm(dc_code), []):
        return []
    out = []
    base_in = 1200.0 + hash(dc_code) % 200
    for i in range(14):
        out.append({"ts": f"2025-03-{i+1:02d}T12:00:00Z", "in_rate": base_in + i * 12, "out_rate": base_in * 0.92 + i * 10})
    return out


def get_dc_san_bottleneck(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    k = _norm(dc_code)
    if k == "IZM-DC1":
        return {
            "has_issue": True,
            "issues": [
                {"portname": "brocade-izm-01:0/8", "swfcportnotxcredits": 4, "swfcporttoomanyrdys": 1},
                {"portname": "brocade-izm-02:0/3", "swfcportnotxcredits": 2, "swfcporttoomanyrdys": 0},
            ],
        }
    if not _SAN_SWITCHES.get(k):
        return {}
    return {"has_issue": False, "issues": []}


def get_dc_storage_capacity(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in ("IST-DC1", "ANK-DC1"):
        return {"systems": []}
    systems = [
        {
            "name": f"IBM-FS-{k}-A",
            "total_mdisk_capacity": "512.00 TB",
            "total_used_capacity": "318.50 TB",
            "total_free_space": "193.50 TB",
        },
        {
            "name": f"IBM-FS-{k}-B",
            "total_mdisk_capacity": "256.00 TB",
            "total_used_capacity": "142.00 TB",
            "total_free_space": "114.00 TB",
        },
    ]
    if k == "IST-DC1":
        systems.append(
            {
                "name": "NetApp-IST-01",
                "total_mdisk_capacity": "128.00 TB",
                "total_used_capacity": "61.00 TB",
                "total_free_space": "67.00 TB",
            }
        )
    return {"systems": systems}


def get_dc_storage_performance(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    k = _norm(dc_code)
    if k not in ("IST-DC1", "ANK-DC1"):
        return {"series": []}
    series = []
    for i in range(10):
        series.append({"iops": 8500 + i * 120, "throughput_mb": 420.0 + i * 8, "latency_ms": 3.2 + (i % 3) * 0.1})
    return {"series": series}


_ZABBIX_CAP: dict[str, dict[str, Any]] = {
    "IST-DC1": {"storage_device_count": 4, "total_usable_tb": 880.0, "used_tb": 512.0},
    "ANK-DC1": {"storage_device_count": 2, "total_usable_tb": 400.0, "used_tb": 305.0},
    "IZM-DC1": {"storage_device_count": 3, "total_usable_tb": 620.0, "used_tb": 341.0},
    "FRA-DC1": {"storage_device_count": 5, "total_usable_tb": 720.0, "used_tb": 338.0},
}

_ZABBIX_DEVICES: dict[str, list[dict[str, Any]]] = {
    "IST-DC1": [
        {"host": "zbx-store-ist-01", "role": "Primary"},
        {"host": "zbx-store-ist-02", "role": "Secondary"},
        {"host": "zbx-store-ist-03", "role": "Archive"},
        {"host": "zbx-store-ist-04", "role": "Cache"},
    ],
    "ANK-DC1": [
        {"host": "zbx-store-ank-01", "role": "Primary"},
        {"host": "zbx-store-ank-02", "role": "Secondary"},
    ],
    "IZM-DC1": [
        {"host": "zbx-store-izm-01", "role": "A"},
        {"host": "zbx-store-izm-02", "role": "B"},
        {"host": "zbx-store-izm-03", "role": "C"},
    ],
    "FRA-DC1": [
        {"host": "zbx-store-fra-01", "role": "Tier1"},
        {"host": "zbx-store-fra-02", "role": "Tier1"},
        {"host": "zbx-store-fra-03", "role": "Tier2"},
        {"host": "zbx-store-fra-04", "role": "Backup"},
        {"host": "zbx-store-fra-05", "role": "Lab"},
    ],
}


def get_dc_zabbix_storage_capacity(dc_code: str, _tr: dict | None = None, host: Optional[str] = None) -> dict[str, Any]:
    base = deepcopy(_ZABBIX_CAP.get(_norm(dc_code), {"storage_device_count": 0, "total_usable_tb": 0.0, "used_tb": 0.0}))
    if host:
        base["host"] = host
    return base


def get_dc_zabbix_storage_trend(dc_code: str, _tr: dict | None = None, host: Optional[str] = None) -> dict[str, Any]:
    if _norm(dc_code) not in MOCK_DC_CODES:
        return {}
    pts = [{"ts": f"d{i}", "used_pct": 52.0 + i * 0.4} for i in range(12)]
    return {"series": pts, "host": host}


def get_dc_zabbix_storage_devices(dc_code: str, _tr: dict | None = None) -> list[dict[str, Any]]:
    return deepcopy(_ZABBIX_DEVICES.get(_norm(dc_code), []))


def get_dc_zabbix_disk_list(dc_code: str, _tr: dict | None = None, host: Optional[str] = None) -> dict[str, Any]:
    if not host:
        return {"items": []}
    return {
        "items": [
            {"name": "mdisk0", "size_tb": 24.0},
            {"name": "mdisk1", "size_tb": 24.0},
            {"name": "mdisk2", "size_tb": 48.0},
        ]
    }


def get_dc_zabbix_disk_trend(
    dc_code: str, _tr: dict | None = None, host: Optional[str] = None, disk_name: Optional[str] = None
) -> dict[str, Any]:
    if not host or not disk_name:
        return {"series": []}
    return {"series": [{"ts": f"h{i}", "util_pct": 60.0 + i * 0.5} for i in range(8)]}


def get_dc_zabbix_disk_health(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    k = _norm(dc_code)
    return {
        "summary_ok": k != "IZM-DC1",
        "degraded_disks": 1 if k == "IZM-DC1" else 0,
        "hosts_checked": len(_ZABBIX_DEVICES.get(k, [])),
    }
