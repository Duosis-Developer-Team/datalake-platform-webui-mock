"""Mock physical inventory endpoints."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.services.mock_data.datacenters import get_dc_detail


def _norm(name: str) -> str:
    return (name or "").strip()


def get_physical_inventory_dc(dc_name: str) -> dict[str, Any]:
    """Match API: keyed by DC display name from meta."""
    code = None
    for c in ("IST-DC1", "ANK-DC1", "IZM-DC1", "FRA-DC1"):
        d = get_dc_detail(c)
        if _norm(d.get("meta", {}).get("name", "")) == _norm(dc_name):
            code = c
            break
    if not code:
        return {"total": 0, "by_role": [], "by_role_manufacturer": []}

    mult = {"IST-DC1": 1.0, "ANK-DC1": 0.65, "IZM-DC1": 0.55, "FRA-DC1": 0.72}[code]

    by_role = [
        {"role": "Server", "count": int(120 * mult)},
        {"role": "Storage", "count": int(28 * mult)},
        {"role": "Network", "count": int(64 * mult)},
        {"role": "Chassis", "count": int(18 * mult)},
    ]
    total = sum(r["count"] for r in by_role)
    brm = []
    for role_row in by_role:
        role = role_row["role"]
        brm.append(
            {
                "role": role,
                "manufacturer": "Dell",
                "count": int(role_row["count"] * 0.45),
            }
        )
        brm.append(
            {
                "role": role,
                "manufacturer": "HPE",
                "count": int(role_row["count"] * 0.35),
            }
        )
        brm.append(
            {
                "role": role,
                "manufacturer": "Cisco",
                "count": max(0, role_row["count"] - int(role_row["count"] * 0.45) - int(role_row["count"] * 0.35)),
            }
        )
    return {"total": total, "by_role": by_role, "by_role_manufacturer": brm}


def get_physical_inventory_overview_by_role() -> list[dict[str, Any]]:
    return deepcopy(
        [
            {"role": "Server", "count": 412},
            {"role": "Network", "count": 228},
            {"role": "Storage", "count": 96},
            {"role": "Chassis", "count": 58},
            {"role": "PDU", "count": 44},
        ]
    )


def get_physical_inventory_overview_manufacturer(role: str) -> list[dict[str, Any]]:
    r = (role or "").strip().lower()
    data = {
        "server": [{"manufacturer": "Dell", "count": 180}, {"manufacturer": "HPE", "count": 140}, {"manufacturer": "Lenovo", "count": 92}],
        "network": [{"manufacturer": "Cisco", "count": 110}, {"manufacturer": "Arista", "count": 72}, {"manufacturer": "Juniper", "count": 46}],
    }
    return deepcopy(data.get(r, [{"manufacturer": "Various", "count": 24}]))


def get_physical_inventory_overview_location(role: str, manufacturer: str) -> list[dict[str, Any]]:
    return deepcopy(
        [
            {"location": "IST-DC1", "count": 42},
            {"location": "ANK-DC1", "count": 28},
            {"location": "IZM-DC1", "count": 19},
            {"location": "FRA-DC1", "count": 31},
        ]
    )


def get_physical_inventory_customer() -> list[dict[str, Any]]:
    return deepcopy(
        [
            {"device_name": "boyner-esxi-01", "role": "Server", "site": "IST-DC1"},
            {"device_name": "boyner-db-02", "role": "Server", "site": "IST-DC1"},
            {"device_name": "boyner-sw-03", "role": "Network", "site": "ANK-DC1"},
        ]
    )
