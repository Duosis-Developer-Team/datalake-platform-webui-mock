"""Static Q&A scenarios for Datalake Assistant Agent (DAA) and page chatbot."""

from __future__ import annotations

from typing import Any

from src.services.mock_data.analytics import get_capacity_forecast_series, get_risk_radar
from src.services.mock_data.datacenters import get_all_datacenters_summary


def _path_kind(pathname: str) -> str:
    p = pathname or "/"
    if p.startswith("/datacenter/"):
        return "dc_detail"
    if p == "/analytics":
        return "analytics"
    if p == "/daa":
        return "daa"
    if p == "/customer-view":
        return "customer"
    if p == "/datacenters":
        return "datacenters"
    return "general"


def _dc_from_path(pathname: str) -> str | None:
    if not pathname or not pathname.startswith("/datacenter/"):
        return None
    return pathname.replace("/datacenter/", "").strip("/").upper() or None


def match_scenario(user_text: str, pathname: str) -> str | None:
    """Return canned answer key if user message matches a known pattern."""
    t = (user_text or "").strip().lower()
    if not t:
        return None
    kind = _path_kind(pathname)
    if any(k in t for k in ("health", "sağlık", "durum")):
        return "health_overview"
    if "summarize" in t or "summary" in t or "özet" in t:
        return "health_overview"
    if "dikkat" in t or "uyarı" in t or "alert" in t or "watch" in t:
        return "weekly_alerts"
    if "kapasite" in t or "capacity" in t:
        return "capacity_pressure" if kind == "dc_detail" else "capacity_multi"
    if (
        "optimizasyon" in t
        or "tasarruf" in t
        or "cost" in t
        or "maliyet" in t
        or "waste" in t
        or "idle" in t
    ):
        return "cost_save"
    if "rapor" in t or "report" in t:
        return "exec_report"
    if "90 gün" in t or "90 day" in t or "90-day" in t or "projeksiyon" in t:
        return "forecast_90"
    return None


def get_canned_answer(key: str, pathname: str) -> str:
    dc = _dc_from_path(pathname)
    summaries = get_all_datacenters_summary()
    names = ", ".join(s["id"] for s in summaries)

    if key == "health_overview":
        return (
            f"Mock assessment across {names}: FRA-DC1 and IST-DC1 are green. "
            "IZM-DC1 shows elevated CPU (Nutanix). ANK-DC1 object storage utilisation is high — plan expansion within 90 days."
        )
    if key == "weekly_alerts":
        return (
            "This week (mock): IZM-DC1 CPU trend +2.8% WoW; ANK-DC1 S3 primary vault crossed 81% utilisation; "
            "IST-DC1 SAN shows minor CRC deltas on one edge port — no customer impact."
        )
    if key == "capacity_pressure":
        if dc == "IZM-DC1":
            return (
                "Izmir DC (mock): Hyperconverged CPU at ~83% fleet average; forecast crosses 90% in ~45 days at current growth. "
                "Recommend host add or workload rebalance to FRA-DC1."
            )
        return f"Selected site {dc or 'N/A'}: use Analytics > Capacity Forecast for 90-day projection (mock data)."
    if key == "capacity_multi":
        return "Multi-DC view (mock): Worst headroom is IZM-DC1 (CPU). Best headroom FRA-DC1 — candidate for bursty workloads."
    if key == "cost_save":
        return (
            "Mock savings opportunity: 2 zombie VMs (~225 EUR/mo) + ~24 TB idle tier — total ~12.8k EUR/mo if reclaimed "
            "(see Analytics > Cost Optimization)."
        )
    if key == "exec_report":
        return "Executive report (mock): Export from DAA page after generating a table — Excel/CSV buttons attach metadata headers."
    if key == "forecast_90":
        ser = get_capacity_forecast_series()
        return (
            f"90-day projection (mock): IZM-DC1 CPU trajectory steepest; "
            f"{len(ser.get('by_dc', {}))} sites modelled. Open Analytics for charts."
        )
    return "I can help with health, capacity, cost, and reports (mock assistant). Try a quick-action button or rephrase your question."


def quick_actions_for_path(pathname: str) -> list[dict[str, str]]:
    """Buttons: label (UI), id (scenario key), user_text (message shown in chat)."""
    kind = _path_kind(pathname)
    dc = _dc_from_path(pathname)
    base = [
        {
            "id": "health_overview",
            "label": "Overall environment health?",
            "user_text": "How is overall environment health across our datacenters?",
        },
        {
            "id": "weekly_alerts",
            "label": "Anything to watch this week?",
            "user_text": "Is there anything I should watch closely this week?",
        },
    ]
    if kind == "dc_detail":
        return base + [
            {
                "id": "capacity_pressure",
                "label": f"Capacity risk for {dc or 'this DC'}?",
                "user_text": f"What is the capacity outlook for {dc or 'this datacenter'}?",
            },
            {
                "id": "cost_save",
                "label": "Cost optimization ideas?",
                "user_text": "What cost optimization ideas do you suggest for this site?",
            },
        ]
    if kind == "analytics":
        return base + [
            {
                "id": "capacity_multi",
                "label": "Which DC needs growth first?",
                "user_text": "Which datacenter needs capacity growth first?",
            },
            {
                "id": "cost_save",
                "label": "Estimated savings potential?",
                "user_text": "What estimated savings potential do you see in the estate?",
            },
        ]
    if kind == "daa":
        return [
            {
                "id": "exec_report",
                "label": "How do I export an executive report?",
                "user_text": "How do I export an executive report from this platform?",
            },
            {
                "id": "forecast_90",
                "label": "Explain 90-day capacity outlook",
                "user_text": "Can you explain the 90-day capacity outlook for our infrastructure?",
            },
            {
                "id": "health_overview",
                "label": "Summarize all datacenters",
                "user_text": "Please summarize health and load across all datacenters.",
            },
            {
                "id": "cost_save",
                "label": "Where is waste in the estate?",
                "user_text": "Where is waste or idle capacity in our estate?",
            },
        ]
    return base + [
        {
            "id": "capacity_multi",
            "label": "Compare capacity across DCs",
            "user_text": "How does capacity compare across our datacenters?",
        }
    ]


def daa_report_rows(report_type: str, dc_code: str | None) -> tuple[list[str], list[list[Any]]]:
    """Columns and rows for DAA report generator."""
    rt = (report_type or "summary").lower().strip()
    summaries = get_all_datacenters_summary()
    if rt == "capacity":
        cols = ["dc", "cpu_pct", "ram_pct", "forecast_note"]
        rows = []
        for s in summaries:
            note = "Critical path" if s["id"] == "IZM-DC1" else "Within SLO"
            rows.append([s["id"], s["stats"]["used_cpu_pct"], s["stats"]["used_ram_pct"], note])
        if dc_code:
            dcu = dc_code.strip().upper()
            rows = [r for r in rows if r[0] == dcu] or rows
        return cols, rows
    if rt == "risk":
        cols = ["dc", "risk", "severity", "eta_days"]
        return cols, [[r["dc"], r["risk"], r["severity"], r["eta_days"]] for r in get_risk_radar()]
    cols = ["dc", "location", "hosts", "vms", "status"]
    rows = [[s["id"], s["location"], s["host_count"], s["vm_count"], "OK"] for s in summaries]
    if dc_code:
        dcu = dc_code.strip().upper()
        rows = [r for r in rows if r[0] == dcu] or rows
    return cols, rows
