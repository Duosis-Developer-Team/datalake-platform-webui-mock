"""Mock NetBackup, Zerto, and Veeam datasets per datacenter."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

def _norm(dc_code: str) -> str:
    return (dc_code or "").strip().upper()


_NETBACKUP: dict[str, dict[str, Any]] = {
    "IST-DC1": {
        "pools": ["NBU-IST-PROD", "NBU-IST-DR", "NBU-IST-ARCH"],
        "rows": [
            {"pool": "NBU-IST-PROD", "used_tb": 420.0, "cap_tb": 600.0, "policies": 48},
            {"pool": "NBU-IST-DR", "used_tb": 180.0, "cap_tb": 400.0, "policies": 22},
            {"pool": "NBU-IST-ARCH", "used_tb": 95.0, "cap_tb": 200.0, "policies": 12},
        ],
    },
    "ANK-DC1": {
        "pools": ["NBU-ANK-01", "NBU-ANK-02"],
        "rows": [
            {"pool": "NBU-ANK-01", "used_tb": 310.0, "cap_tb": 400.0, "policies": 31},
            {"pool": "NBU-ANK-02", "used_tb": 120.0, "cap_tb": 180.0, "policies": 14},
        ],
    },
    "IZM-DC1": {"pools": [], "rows": []},
    "FRA-DC1": {"pools": [], "rows": []},
}

_ZERTO: dict[str, dict[str, Any]] = {
    "IST-DC1": {
        "sites": ["IST-ZR-PRIMARY", "IST-ZR-SECONDARY"],
        "rows": [
            {"site": "IST-ZR-PRIMARY", "vpg_count": 18, "protected_vms": 240},
            {"site": "IST-ZR-SECONDARY", "vpg_count": 12, "protected_vms": 160},
        ],
    },
    "ANK-DC1": {"sites": [], "rows": []},
    "IZM-DC1": {"sites": [], "rows": []},
    "FRA-DC1": {
        "sites": ["FRA-ZR-HUB", "FRA-ZR-EDGE-A", "FRA-ZR-EDGE-B"],
        "rows": [
            {"site": "FRA-ZR-HUB", "vpg_count": 24, "protected_vms": 320},
            {"site": "FRA-ZR-EDGE-A", "vpg_count": 8, "protected_vms": 90},
            {"site": "FRA-ZR-EDGE-B", "vpg_count": 7, "protected_vms": 85},
        ],
    },
}

_VEEAM: dict[str, dict[str, Any]] = {
    "IST-DC1": {
        "repos": ["VEEAM-IST-SOBR1", "VEEAM-IST-SOBR2", "VEEAM-IST-TAPE-GW", "VEEAM-IST-CLOUD"],
        "rows": [
            {"repo": "VEEAM-IST-SOBR1", "used_tb": 210.0, "free_tb": 90.0},
            {"repo": "VEEAM-IST-SOBR2", "used_tb": 155.0, "free_tb": 45.0},
            {"repo": "VEEAM-IST-TAPE-GW", "used_tb": 480.0, "free_tb": 120.0},
            {"repo": "VEEAM-IST-CLOUD", "used_tb": 62.0, "free_tb": 138.0},
        ],
    },
    "ANK-DC1": {
        "repos": ["VEEAM-ANK-R1", "VEEAM-ANK-R2", "VEEAM-ANK-R3"],
        "rows": [
            {"repo": "VEEAM-ANK-R1", "used_tb": 140.0, "free_tb": 60.0},
            {"repo": "VEEAM-ANK-R2", "used_tb": 88.0, "free_tb": 32.0},
            {"repo": "VEEAM-ANK-R3", "used_tb": 55.0, "free_tb": 25.0},
        ],
    },
    "IZM-DC1": {
        "repos": ["VEEAM-IZM-A", "VEEAM-IZM-B"],
        "rows": [
            {"repo": "VEEAM-IZM-A", "used_tb": 190.0, "free_tb": 70.0},
            {"repo": "VEEAM-IZM-B", "used_tb": 102.0, "free_tb": 48.0},
        ],
    },
    "FRA-DC1": {
        "repos": ["VEEAM-FRA-01", "VEEAM-FRA-02", "VEEAM-FRA-03", "VEEAM-FRA-04", "VEEAM-FRA-05"],
        "rows": [
            {"repo": "VEEAM-FRA-01", "used_tb": 95.0, "free_tb": 105.0},
            {"repo": "VEEAM-FRA-02", "used_tb": 72.0, "free_tb": 78.0},
            {"repo": "VEEAM-FRA-03", "used_tb": 110.0, "free_tb": 90.0},
            {"repo": "VEEAM-FRA-04", "used_tb": 64.0, "free_tb": 56.0},
            {"repo": "VEEAM-FRA-05", "used_tb": 48.0, "free_tb": 52.0},
        ],
    },
}


def _empty_nb() -> dict[str, Any]:
    return {"pools": [], "rows": []}


def get_dc_netbackup_pools(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    return deepcopy(_NETBACKUP.get(_norm(dc_code), _empty_nb()))


def get_dc_zerto_sites(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    return deepcopy(_ZERTO.get(_norm(dc_code), {"sites": [], "rows": []}))


def get_dc_veeam_repos(dc_code: str, _tr: dict | None = None) -> dict[str, Any]:
    return deepcopy(_VEEAM.get(_norm(dc_code), {"repos": [], "rows": []}))


_ZERTO_LICENSE: dict[str, dict[str, Any]] = {
    "IST-DC1": {
        "has_license": True,
        "licenses": [
            {
                "zerto_host": "10.40.9.11",
                "license_type": "CloudO2M",
                "is_valid": True,
                "max_vms": 500,
                "total_vms_count": 115,
                "days_until_expiry": 180,
            }
        ],
        "sites": [
            {"site_name": "IST-ZR-PRIMARY", "protected_vms_count": 240},
            {"site_name": "IST-ZR-SECONDARY", "protected_vms_count": 160},
        ],
        "summary": {
            "license_type": "CloudO2M",
            "is_valid": True,
            "max_vms": 500,
            "total_vms_count": 115,
            "days_until_expiry": 180,
            "protected_vms_in_dc": 400,
            "zerto_hosts": ["10.40.9.11"],
        },
    },
}


def get_dc_zerto_license(dc_code: str) -> dict[str, Any]:
    """Mock Zerto license payload (policy-based Backup & Replication IA)."""
    empty = {
        "has_license": False,
        "licenses": [],
        "sites": [],
        "summary": {
            "license_type": None,
            "is_valid": None,
            "max_vms": None,
            "total_vms_count": None,
            "days_until_expiry": None,
            "protected_vms_in_dc": 0,
            "zerto_hosts": [],
        },
    }
    return deepcopy(_ZERTO_LICENSE.get(_norm(dc_code), empty))


_UNIQUE_JOBS: dict[str, dict[str, dict[str, Any]]] = {
    "IST-DC1": {
        "veeam": {
            "rows": [
                {
                    "id": "vj-1",
                    "name": "Acme-Backup-Daily",
                    "type": "Backup",
                    "status": "success",
                    "last_result": "Success",
                    "last_run": "2026-07-16T01:00:00",
                    "objects_count": 12,
                    "workload": "vm",
                    "source_ip": "10.1.1.1",
                },
                {
                    "id": "vj-2",
                    "name": "Acme-Replica",
                    "type": "Replica",
                    "status": "warning",
                    "last_result": "Warning",
                    "last_run": "2026-07-16T02:00:00",
                    "objects_count": 4,
                    "workload": "vm",
                    "source_ip": "10.1.1.1",
                },
            ],
            "totals": {
                "total_jobs": 2,
                "by_status": {"success": 1, "warning": 1},
                "by_type": {"Backup": 1, "Replica": 1},
            },
            "as_of": "2026-07-16T12:00:00+00:00",
            "vendor": "veeam",
        },
        "zerto": {
            "rows": [
                {
                    "id": "z-1",
                    "name": "Acme-VPG-01",
                    "status": "success",
                    "vmscount": 8,
                    "source_site": "IST-ZR-PRIMARY",
                    "target_site": "IST-ZR-SECONDARY",
                    "provisioned_storage_mb": 512000,
                    "used_storage_mb": 256000,
                    "zerto_host": "10.40.9.11",
                }
            ],
            "totals": {"total_jobs": 1, "by_status": {"success": 1}, "by_type": {"vpg": 1}},
            "as_of": "2026-07-16T12:00:00+00:00",
            "vendor": "zerto",
        },
        "netbackup": {
            "rows": [
                {
                    "jobid": 101,
                    "policyname": "Acme-VMWARE",
                    "policytype": "VMWARE",
                    "category": "image",
                    "jobtype": "BACKUP",
                    "status": "success",
                    "workloaddisplayname": "Acme-web01",
                    "clientname": "Acme-web01",
                    "destinationmediaservername": "nbmediadc13.blt.vc",
                    "kilobytestransferred": 1048576,
                    "dedupratio": 4.2,
                    "starttime": "2026-07-16T01:30:00",
                },
                {
                    "jobid": 102,
                    "policyname": "Acme-Oracle",
                    "policytype": "Oracle",
                    "category": "application",
                    "jobtype": "BACKUP",
                    "status": "failed",
                    "workloaddisplayname": "Acme-db01",
                    "clientname": "Acme-db01",
                    "destinationmediaservername": "nbmediadc13.blt.vc",
                    "kilobytestransferred": 0,
                    "dedupratio": 1.0,
                    "starttime": "2026-07-16T03:00:00",
                },
            ],
            "totals": {
                "total_jobs": 2,
                "by_status": {"success": 1, "failed": 1},
                "by_type": {"BACKUP": 2},
                "by_category": {"image": 1, "application": 1},
                "by_policy_type": {"VMWARE": 1, "Oracle": 1},
            },
            "as_of": "2026-07-16T12:00:00+00:00",
            "vendor": "netbackup",
        },
    }
}


def get_dc_unique_jobs(dc_code: str, vendor: str, _tr: dict | None = None) -> dict[str, Any]:
    empty = {"rows": [], "totals": {}, "as_of": "", "vendor": vendor}
    by_dc = _UNIQUE_JOBS.get(_norm(dc_code), {})
    return deepcopy(by_dc.get(vendor, empty))


def get_dc_unique_jobs_table(
    dc_code: str,
    vendor: str,
    _tr: dict | None = None,
    *,
    page: int = 1,
    page_size: int = 50,
    search: str = "",
    statuses: list | None = None,
    types: list | None = None,
    policy_types: list | None = None,
    categories: list | None = None,
    platforms: list | None = None,
) -> dict[str, Any]:
    base = get_dc_unique_jobs(dc_code, vendor, _tr)
    rows = list(base.get("rows") or [])
    q = (search or "").strip().lower()
    if q:
        rows = [
            r
            for r in rows
            if q in " ".join(str(r.get(k) or "").lower() for k in r.keys())
        ]
    if statuses:
        want = {str(s).lower() for s in statuses}
        rows = [r for r in rows if str(r.get("status") or "").lower() in want]
    if types:
        want = {str(t) for t in types}
        key = "policytype" if vendor == "netbackup" else "type"
        rows = [r for r in rows if str(r.get(key) or "") in want]
    if policy_types:
        want = {str(t) for t in policy_types}
        rows = [r for r in rows if str(r.get("policytype") or "") in want]
    if categories:
        want = {str(c) for c in categories}
        rows = [r for r in rows if str(r.get("category") or "") in want]
    if platforms:
        want = {str(p) for p in platforms}
        rows = [
            r
            for r in rows
            if str(
                r.get("source_ip")
                or r.get("zerto_host")
                or r.get("source_site")
                or r.get("destinationmediaservername")
                or ""
            )
            in want
        ]
    page = max(1, int(page or 1))
    page_size = max(1, min(200, int(page_size or 50)))
    total = len(rows)
    start = (page - 1) * page_size
    by_status: dict[str, int] = {}
    for r in rows:
        st = str(r.get("status") or "unknown").lower()
        by_status[st] = by_status.get(st, 0) + 1
    return {
        "items": rows[start : start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "totals": {
            "total_jobs": total,
            "by_status": by_status,
            "by_type": {},
        },
        "vendor": vendor,
    }


def get_customer_unique_jobs(customer_name: str, vendor: str, _tr: dict | None = None) -> dict[str, Any]:
    """Reuse IST-DC1 fixtures for demo customers."""
    return get_dc_unique_jobs("IST-DC1", vendor, _tr)


def get_customer_unique_jobs_table(customer_name: str, vendor: str, _tr: dict | None = None, **kwargs) -> dict[str, Any]:
    return get_dc_unique_jobs_table("IST-DC1", vendor, _tr, **kwargs)
