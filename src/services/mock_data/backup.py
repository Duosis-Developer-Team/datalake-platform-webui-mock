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
