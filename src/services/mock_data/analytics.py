"""Mock analytics datasets (capacity forecast, efficiency, risk, cost optimization)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.services.mock_data.datacenters import MOCK_DC_CODES, get_all_datacenters_summary


def get_capacity_forecast_series() -> dict[str, Any]:
    """Historical + forecast points for CPU/RAM/Storage (percent or absolute per DC)."""
    days_hist = 60
    days_fc = 30
    out: dict[str, Any] = {"days_historical": days_hist, "days_forecast": days_fc, "by_dc": {}}
    for s in get_all_datacenters_summary():
        dc = s["id"]
        cpu = float(s["stats"]["used_cpu_pct"])
        series = []
        for i in range(days_hist):
            series.append({"day": i, "cpu_pct": max(0, cpu - 8 + i * 0.12), "phase": "hist"})
        for j in range(days_fc):
            series.append(
                {
                    "day": days_hist + j,
                    "cpu_pct": min(98.0, cpu + j * 0.28),
                    "phase": "forecast",
                }
            )
        out["by_dc"][dc] = series
    return out


def get_efficiency_scores() -> list[dict[str, Any]]:
    rows = []
    for s in get_all_datacenters_summary():
        dc = s["id"]
        base = 88.0 - {"IST-DC1": 6, "ANK-DC1": 18, "IZM-DC1": 2, "FRA-DC1": 22}[dc]
        rows.append(
            {
                "dc": dc,
                "efficiency_score": base,
                "waste_cpu_pct": max(0, 15 - base * 0.1),
                "waste_ram_pct": max(0, 12 - base * 0.08),
                "headroom_score": min(100, base + 5),
            }
        )
    return rows


def get_risk_radar() -> list[dict[str, Any]]:
    return [
        {"dc": "IZM-DC1", "risk": "CPU saturation", "severity": "high", "eta_days": 45},
        {"dc": "ANK-DC1", "risk": "S3 pool fill", "severity": "medium", "eta_days": 90},
        {"dc": "IST-DC1", "risk": "SAN CRC noise", "severity": "low", "eta_days": None},
        {"dc": "FRA-DC1", "risk": "None critical", "severity": "info", "eta_days": None},
    ]


def get_cost_optimization() -> dict[str, Any]:
    return {
        "zombie_vms": [
            {"name": "old-test-42", "dc": "IST-DC1", "cpu": 4, "monthly_cost_eur": 85},
            {"name": "pilot-2023-a", "dc": "ANK-DC1", "cpu": 8, "monthly_cost_eur": 140},
        ],
        "idle_storage_tb": 24.5,
        "potential_monthly_savings_eur": 12800,
    }


def get_executive_summary_table() -> list[dict[str, Any]]:
    rows = []
    for s in get_all_datacenters_summary():
        rows.append(
            {
                "dc": s["id"],
                "location": s["location"],
                "hosts": s["host_count"],
                "vms": s["vm_count"],
                "cpu_pct": s["stats"]["used_cpu_pct"],
                "health": "attention" if s["id"] == "IZM-DC1" else "healthy",
            }
        )
    return deepcopy(rows)
