"""Mock customer list, resources, S3 vaults, and availability bundle."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

MOCK_CUSTOMER_NAMES: tuple[str, ...] = ("Akbank", "Pegasus Airlines", "Turk Telekom")


def get_customer_list() -> list[str]:
    return list(MOCK_CUSTOMER_NAMES)


def _vm(name: str, source: str, cpu: float, mem: float, disk: float, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "name": name,
        "source": source,
        "cpu": cpu,
        "memory_gb": mem,
        "disk_gb": disk,
    }
    row.update(extra)
    return row


def _customer_bundle(
    *,
    classic_vm: int,
    classic_cpu: float,
    classic_mem: float,
    classic_disk: float,
    classic_list: list[dict],
    hc_vm: int,
    hc_vmware: int,
    hc_nutanix: int,
    hc_cpu: float,
    hc_mem: float,
    hc_disk: float,
    hc_list: list[dict],
    pure_vm: int,
    pure_cpu: float,
    pure_mem: float,
    pure_disk: float,
    pure_list: list[dict],
    power_lpar: int,
    power_cpu: float,
    power_mem: float,
    power_list: list[dict],
    veeam_sessions: int,
    zerto_protected: int,
    nb_pre: float,
    nb_post: float,
    zerto_prov_gib: float,
    storage_vol_gb: float,
) -> dict[str, Any]:
    intel_vm_total = classic_vm + hc_vm + pure_vm
    intel_cpu_total = classic_cpu + hc_cpu + pure_cpu
    intel_mem_total = classic_mem + hc_mem + pure_mem
    intel_disk_total = classic_disk + hc_disk + pure_disk
    vmware_intel = max(0, classic_vm + hc_vmware)
    nutanix_intel = max(0, hc_nutanix + pure_vm)

    totals = {
        "vms_total": intel_vm_total + power_lpar,
        "intel_vms_total": intel_vm_total,
        "classic_vms_total": classic_vm,
        "hyperconv_vms_total": hc_vm,
        "power_lpar_total": power_lpar,
        "cpu_total": intel_cpu_total + power_cpu,
        "intel_cpu_total": intel_cpu_total,
        "classic_cpu_total": classic_cpu,
        "hyperconv_cpu_total": hc_cpu,
        "power_cpu_total": power_cpu,
        "backup": {
            "veeam_defined_sessions": veeam_sessions,
            "zerto_protected_vms": zerto_protected,
            "storage_volume_gb": storage_vol_gb,
            "ibm_storage_volume_gb": storage_vol_gb,
            "netbackup_pre_dedup_gib": nb_pre,
            "netbackup_post_dedup_gib": nb_post,
            "zerto_provisioned_gib": zerto_prov_gib,
        },
    }

    intel_vm_list = classic_list[:2] + hc_list[:2] if (classic_list or hc_list) else []

    assets: dict[str, Any] = {
        "intel": {
            "vms": {"vmware": vmware_intel, "nutanix": nutanix_intel, "total": intel_vm_total},
            "cpu": {
                "vmware": classic_cpu + (hc_cpu * 0.55 if hc_vm else 0.0),
                "nutanix": (hc_cpu * 0.45 if hc_vm else 0.0) + pure_cpu,
                "total": intel_cpu_total,
            },
            "memory_gb": {
                "vmware": classic_mem + hc_mem * 0.5,
                "nutanix": hc_mem * 0.5 + pure_mem,
                "total": intel_mem_total,
            },
            "disk_gb": {
                "vmware": classic_disk + hc_disk * 0.5,
                "nutanix": hc_disk * 0.5 + pure_disk,
                "total": intel_disk_total,
            },
            "vm_list": intel_vm_list,
            "vmware_vm_count": vmware_intel,
            "nutanix_vm_count": nutanix_intel,
            "vmware_cpu_total": classic_cpu + hc_cpu * 0.55,
            "nutanix_cpu_total": hc_cpu * 0.45 + pure_cpu,
        },
        "classic": {
            "vm_count": classic_vm,
            "cpu_total": classic_cpu,
            "memory_gb": classic_mem,
            "disk_gb": classic_disk,
            "vm_list": classic_list,
        },
        "hyperconv": {
            "vm_count": hc_vm,
            "vmware_only": hc_vmware,
            "nutanix_count": hc_nutanix,
            "cpu_total": hc_cpu,
            "memory_gb": hc_mem,
            "disk_gb": hc_disk,
            "vm_list": hc_list,
        },
        "pure_nutanix": (
            {
                "vm_count": pure_vm,
                "cpu_total": pure_cpu,
                "memory_gb": pure_mem,
                "disk_gb": pure_disk,
                "vm_list": pure_list,
            }
            if pure_vm > 0
            else {}
        ),
        "power": {
            "cpu_total": power_cpu,
            "lpar_count": power_lpar,
            "memory_total_gb": power_mem,
            "vm_list": power_list,
        },
        "backup": {
            "veeam": {
                "defined_sessions": veeam_sessions,
                "session_types": [{"type": "Backup", "count": max(1, veeam_sessions // 2)}],
                "platforms": [{"platform": "VMware", "count": veeam_sessions}],
            },
            "zerto": {
                "protected_total_vms": zerto_protected,
                "provisioned_storage_gib_total": zerto_prov_gib,
                "vpgs": [{"name": "mock-vpg", "provisioned_storage_gib": zerto_prov_gib}],
            },
            "storage": {"total_volume_capacity_gb": storage_vol_gb},
            "netbackup": {
                "pre_dedup_size_gib": nb_pre,
                "post_dedup_size_gib": nb_post,
                "deduplication_factor": "2.1x",
            },
        },
    }

    return {"totals": totals, "assets": assets}


def _resources_akbank() -> dict[str, Any]:
    """Retail bank: strong Classic + Power LPARs, balanced backup footprint."""
    return _customer_bundle(
        classic_vm=48,
        classic_cpu=312.0,
        classic_mem=1840.0,
        classic_disk=145_000.0,
        classic_list=[
            _vm("akb-app-01", "vmware", 8.0, 32.0, 512.0, cluster="IST-CL01"),
            _vm("akb-db-01", "vmware", 16.0, 128.0, 2048.0, cluster="FRA-CL01"),
        ],
        hc_vm=52,
        hc_vmware=22,
        hc_nutanix=30,
        hc_cpu=288.0,
        hc_mem=2100.0,
        hc_disk=168_000.0,
        hc_list=[
            _vm("akb-ntx-01", "nutanix", 12.0, 64.0, 1024.0, cluster="IST-NX01"),
        ],
        pure_vm=0,
        pure_cpu=0.0,
        pure_mem=0.0,
        pure_disk=0.0,
        pure_list=[],
        power_lpar=14,
        power_cpu=96.0,
        power_mem=3584.0,
        power_list=[
            _vm("akb-lpar-a", "ibm", 4.0, 128.0, 0.0, state="Running"),
        ],
        veeam_sessions=186,
        zerto_protected=62,
        nb_pre=42_000.0,
        nb_post=11_200.0,
        zerto_prov_gib=28_500.0,
        storage_vol_gb=12_800.0,
    )


def _resources_pegasus() -> dict[str, Any]:
    """Airline: HCI-heavy, minimal Power, some Pure AHV, aggressive object growth."""
    return _customer_bundle(
        classic_vm=22,
        classic_cpu=96.0,
        classic_mem=512.0,
        classic_disk=38_000.0,
        classic_list=[
            _vm("pcg-web-01", "vmware", 4.0, 16.0, 200.0, cluster="IST-CL02"),
            _vm("pcg-api-02", "vmware", 8.0, 32.0, 400.0, cluster="ANK-CL01"),
        ],
        hc_vm=78,
        hc_vmware=30,
        hc_nutanix=48,
        hc_cpu=412.0,
        hc_mem=3200.0,
        hc_disk=220_000.0,
        hc_list=[
            _vm("pcg-ntx-01", "nutanix", 6.0, 24.0, 300.0, cluster="IZM-NX01"),
        ],
        pure_vm=12,
        pure_cpu=48.0,
        pure_mem=384.0,
        pure_disk=18_000.0,
        pure_list=[_vm("pcg-ahv-01", "nutanix", 4.0, 32.0, 1500.0, cluster="AHV-01")],
        power_lpar=0,
        power_cpu=0.0,
        power_mem=0.0,
        power_list=[],
        veeam_sessions=94,
        zerto_protected=88,
        nb_pre=18_200.0,
        nb_post=5200.0,
        zerto_prov_gib=41_000.0,
        storage_vol_gb=48_000.0,
    )


def _resources_turk_telekom() -> dict[str, Any]:
    """Telco: largest VM estate, mixed platforms, heavy backup and DR."""
    return _customer_bundle(
        classic_vm=92,
        classic_cpu=560.0,
        classic_mem=4200.0,
        classic_disk=310_000.0,
        classic_list=[
            _vm("tt-core-01", "vmware", 16.0, 64.0, 800.0, cluster="IST-CL03"),
        ],
        hc_vm=118,
        hc_vmware=55,
        hc_nutanix=63,
        hc_cpu=620.0,
        hc_mem=5600.0,
        hc_disk=410_000.0,
        hc_list=[
            _vm("tt-edge-01", "nutanix", 8.0, 32.0, 500.0, cluster="FRA-NX01"),
        ],
        pure_vm=0,
        pure_cpu=0.0,
        pure_mem=0.0,
        pure_disk=0.0,
        pure_list=[],
        power_lpar=22,
        power_cpu=176.0,
        power_mem=8192.0,
        power_list=[
            _vm("tt-lpar-1", "ibm", 8.0, 256.0, 0.0, state="Running"),
        ],
        veeam_sessions=312,
        zerto_protected=140,
        nb_pre=96_000.0,
        nb_post=24_800.0,
        zerto_prov_gib=92_000.0,
        storage_vol_gb=28_000.0,
    )


def get_customer_resources(name: str, _tr: dict | None = None) -> dict[str, Any]:
    key = (name or "").strip().lower()
    if "akbank" in key:
        return deepcopy(_resources_akbank())
    if "pegasus" in key:
        return deepcopy(_resources_pegasus())
    if "turk" in key or "telekom" in key:
        return deepcopy(_resources_turk_telekom())
    return deepcopy(_resources_akbank())


def get_customer_s3_vaults(customer_name: str, _tr: dict | None = None) -> dict[str, Any]:
    key = (customer_name or "").strip().lower()
    if "pegasus" in key:
        vaults = ["pcg-vault-prod", "pcg-vault-analytics", "pcg-vault-archive"]
        latest = {
            "pcg-vault-prod": {"usable_bytes": 80 * 1024**4, "used_bytes": 62 * 1024**4},
            "pcg-vault-analytics": {"usable_bytes": 40 * 1024**4, "used_bytes": 28 * 1024**4},
            "pcg-vault-archive": {"usable_bytes": 120 * 1024**4, "used_bytes": 55 * 1024**4},
        }
        growth = {v: {"delta_used_bytes": 3 * 1024**3} for v in vaults}
    elif "turk" in key or "telekom" in key:
        vaults = ["tt-icos-core", "tt-icos-dr", "tt-icos-logs"]
        latest = {
            "tt-icos-core": {"usable_bytes": 200 * 1024**4, "used_bytes": 142 * 1024**4},
            "tt-icos-dr": {"usable_bytes": 200 * 1024**4, "used_bytes": 98 * 1024**4},
            "tt-icos-logs": {"usable_bytes": 60 * 1024**4, "used_bytes": 41 * 1024**4},
        }
        growth = {v: {"delta_used_bytes": 5 * 1024**3} for v in vaults}
    else:
        vaults = ["akb-vault-primary", "akb-vault-dr"]
        latest = {
            "akb-vault-primary": {"usable_bytes": 50 * 1024**4, "used_bytes": 33 * 1024**4},
            "akb-vault-dr": {"usable_bytes": 50 * 1024**4, "used_bytes": 21 * 1024**4},
        }
        growth = {v: {"delta_used_bytes": 512 * 1024**2} for v in vaults}
    return {"vaults": vaults, "latest": latest, "growth": growth}


def get_customer_availability_bundle(customer_name: str, _tr: dict | None = None) -> dict[str, Any]:
    key = (customer_name or "").strip().lower()
    if "pegasus" in key:
        return {
            "service_downtimes": [{"service": "Booking API", "minutes": 6}],
            "vm_downtimes": [{"vm": "pcg-web-01", "minutes": 18}],
            "vm_outage_counts": {"pcg-web-01": 1},
            "customer_id": "mock-pcg",
            "customer_ids": ["mock-pcg"],
        }
    if "turk" in key or "telekom" in key:
        return {
            "service_downtimes": [{"service": "Diameter GW", "minutes": 4}],
            "vm_downtimes": [{"vm": "tt-core-01", "minutes": 8}],
            "vm_outage_counts": {"tt-core-01": 1},
            "customer_id": "mock-tt",
            "customer_ids": ["mock-tt"],
        }
    return {
        "service_downtimes": [{"service": "API Gateway", "minutes": 12}],
        "vm_downtimes": [{"vm": "akb-app-01", "minutes": 45}],
        "vm_outage_counts": {"akb-app-01": 2},
        "customer_id": "mock-akb",
        "customer_ids": ["mock-akb"],
    }
