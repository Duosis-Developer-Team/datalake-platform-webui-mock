"""Mock hmdl-api — fixture-backed collector read API for local GUI dev."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from app import mock_data as fx

app = FastAPI(title="HMDL API Mock", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "db": "mock"}


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.get("/api/v1/collectors/topology")
def topology():
    return fx.TOPOLOGY


@app.get("/api/v1/collectors/sync-summary")
def sync_summary():
    return fx.SYNC_SUMMARY


@app.get("/api/v1/collectors/dc/{dc_code}")
def dc_summary(dc_code: str):
    dc = dc_code.upper()
    node = next((n for n in fx.TOPOLOGY["nodes"] if n["dc_code"] == dc), None)
    if not node:
        raise HTTPException(status_code=404, detail="Datacenter not found")
    targets = fx.SAMPLE_TARGETS.get(dc, [])
    return {
        "dc_code": dc,
        "loki_sync_status": node["loki_sync_status"],
        "proxy_count": len(node["proxies"]),
        "target_count": len(targets) or 42,
        "last_prod_run_id": fx.TOPOLOGY["last_prod_run_id"],
        "last_prod_run_at": fx.TOPOLOGY["last_prod_run_at"],
        "recent_diffs": fx.SAMPLE_DIFFS.get(dc, []),
        "category_counts": {
            "monitored": sum(1 for t in targets if t["inclusion_category"] == "monitored"),
            "not_monitored": sum(1 for t in targets if t["inclusion_category"] == "not_monitored"),
            "missing_from_loki": sum(1 for t in targets if t["inclusion_category"] == "missing_from_loki"),
        },
    }


@app.get("/api/v1/collectors/dc/{dc_code}/targets")
def dc_targets(
    dc_code: str,
    category: str | None = Query(default=None),
    entity_name: str | None = Query(default=None),
    ip: str | None = Query(default=None),
):
    dc = dc_code.upper()
    if dc not in {n["dc_code"] for n in fx.TOPOLOGY["nodes"]}:
        raise HTTPException(status_code=404, detail="Datacenter not found")
    items = list(fx.SAMPLE_TARGETS.get(dc, []))
    if not items and dc in fx._DCS:
        items = list(fx.SAMPLE_TARGETS.get("DC13", []))
    if category:
        items = [t for t in items if t["inclusion_category"] == category]
    if entity_name:
        items = [t for t in items if entity_name.lower() in (t.get("entity_name") or "").lower()]
    if ip:
        items = [t for t in items if ip in t.get("ip", "")]
    return {"dc_code": dc, "total": len(items), "items": items, "category_filter": category}


@app.get("/api/v1/collectors/proxies/{proxy_id}")
def proxy_detail(proxy_id: str):
    for node in fx.TOPOLOGY["nodes"]:
        for p in node["proxies"]:
            if p["proxy_id"] == proxy_id:
                return {
                    "proxy_id": proxy_id,
                    "dc_code": node["dc_code"],
                    "proxy_nifi_host": p["proxy_nifi_host"],
                    "loki_sync_status": p["loki_sync_status"],
                    "target_count": p["target_count"],
                    "distributed_count": p["distributed_count"],
                    "last_sync": {
                        "id": 1,
                        "run_id": "mock-run-9of9",
                        "proxy_id": proxy_id,
                        "status": "completed",
                        "dry_run": False,
                        "added_count": 0,
                        "removed_count": 0,
                        "unchanged_count": 42,
                    },
                    "recent_syncs": [],
                }
    raise HTTPException(status_code=404, detail="Proxy not found")


@app.get("/api/v1/collectors/runs")
def runs(limit: int = Query(default=20, ge=1, le=100)):
    return {
        "items": [
            {
                "id": 1,
                "run_id": "mock-run-9of9",
                "awx_job_id": "110031",
                "proxy_id": "ICT11-NIFI1",
                "status": "completed",
                "dry_run": False,
                "added_count": 2,
                "removed_count": 1,
                "unchanged_count": 40,
            }
        ][:limit]
    }
