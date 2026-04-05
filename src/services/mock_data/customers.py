"""Mock customer list, resources, S3 vaults, and availability bundle."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

MOCK_CUSTOMER_NAMES: tuple[str, ...] = ("Akbank", "Pegasus Airlines", "Turk Telekom")


def get_customer_list() -> list[str]:
    return list(MOCK_CUSTOMER_NAMES)


def _resources_akbank() -> dict[str, Any]:
    return {
        "totals": {"vms": 120, "classic_vms": 70, "hyperconv_vms": 40, "lpars": 10, "storage_tb": 45.0},
        "assets": {
            "classic_vms": [
                {"name": "akb-app-01", "dc": "IST-DC1", "cpu": 8, "ram_gb": 32, "disk_gb": 512},
                {"name": "akb-db-01", "dc": "FRA-DC1", "cpu": 16, "ram_gb": 128, "disk_gb": 2048},
            ],
            "hyperconv_vms": [{"name": "akb-ntx-01", "dc": "IST-DC1", "cpu": 12, "ram_gb": 64, "disk_gb": 1024}],
            "lpars": [{"name": "akb-lpar-a", "dc": "IST-DC1", "cpu": 4, "mem_gb": 128}],
        },
    }


def _resources_pegasus() -> dict[str, Any]:
    return {
        "totals": {"vms": 80, "classic_vms": 55, "hyperconv_vms": 25, "lpars": 0, "storage_tb": 60.0},
        "assets": {
            "classic_vms": [
                {"name": "pcg-web-01", "dc": "IST-DC1", "cpu": 4, "ram_gb": 16, "disk_gb": 200},
                {"name": "pcg-api-02", "dc": "ANK-DC1", "cpu": 8, "ram_gb": 32, "disk_gb": 400},
            ],
            "hyperconv_vms": [{"name": "pcg-ntx-01", "dc": "IZM-DC1", "cpu": 6, "ram_gb": 24, "disk_gb": 300}],
            "lpars": [],
        },
    }


def _resources_turk() -> dict[str, Any]:
    return {
        "totals": {"vms": 200, "classic_vms": 90, "hyperconv_vms": 95, "lpars": 15, "storage_tb": 120.0},
        "assets": {
            "classic_vms": [{"name": "tt-core-01", "dc": "IST-DC1", "cpu": 16, "ram_gb": 64, "disk_gb": 800}],
            "hyperconv_vms": [{"name": "tt-edge-01", "dc": "FRA-DC1", "cpu": 8, "ram_gb": 32, "disk_gb": 500}],
            "lpars": [{"name": "tt-lpar-1", "dc": "ANK-DC1", "cpu": 8, "mem_gb": 256}],
        },
    }


def get_customer_resources(name: str, _tr: dict | None = None) -> dict[str, Any]:
    key = (name or "").strip().lower()
    if "akbank" in key:
        return deepcopy(_resources_akbank())
    if "pegasus" in key:
        return deepcopy(_resources_pegasus())
    if "turk" in key or "telekom" in key:
        return deepcopy(_resources_turk())
    return deepcopy(_resources_akbank())


def get_customer_s3_vaults(customer_name: str, _tr: dict | None = None) -> dict[str, Any]:
    key = (customer_name or "").strip().lower()
    if "pegasus" in key or "turk" in key:
        vaults = ["vault-prod", "vault-analytics", "vault-archive"]
        latest = {
            "vault-prod": {"usable_bytes": 80 * 1024**4, "used_bytes": 62 * 1024**4},
            "vault-analytics": {"usable_bytes": 40 * 1024**4, "used_bytes": 28 * 1024**4},
            "vault-archive": {"usable_bytes": 120 * 1024**4, "used_bytes": 55 * 1024**4},
        }
        growth = {v: {"delta_used_bytes": 2 * 1024**3} for v in vaults}
    else:
        vaults = ["vault-primary", "vault-dr"]
        latest = {
            "vault-primary": {"usable_bytes": 50 * 1024**4, "used_bytes": 33 * 1024**4},
            "vault-dr": {"usable_bytes": 50 * 1024**4, "used_bytes": 21 * 1024**4},
        }
        growth = {v: {"delta_used_bytes": 512 * 1024**2} for v in vaults}
    return {"vaults": vaults, "latest": latest, "growth": growth}


def get_customer_availability_bundle(customer_name: str, _tr: dict | None = None) -> dict[str, Any]:
    return {
        "service_downtimes": [{"service": "API Gateway", "minutes": 12}],
        "vm_downtimes": [{"vm": "demo-vm-01", "minutes": 45}],
        "vm_outage_counts": {"demo-vm-01": 2},
        "customer_id": "mock-1",
        "customer_ids": ["mock-1"],
    }
