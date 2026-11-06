"""Mock hmdl-api — fixture-backed collector read API for local GUI dev."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app import mock_data as fx
from app import monitoring_data as md

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


# ── DLP-020: Loki→Zabbix sync outputs, DQ and automation state (GUI routers/zabbix_sync.py,
# routers/monitoring_state.py). Same paths, parameters, status codes and bodies; data from
# app.monitoring_data. HMDL_MOCK_SNAPSHOT_STATE=preparing|unavailable|stale and
# HMDL_MOCK_AWX_REVISIONS=unconfigured switch to the other answers the real service gives.
_HISTORY_DAYS = 30


def _now() -> datetime:
    return datetime.now(timezone.utc)


@app.get("/api/v1/zabbix-sync/runs")
def zabbix_sync_runs(
    entity_type: str | None = Query(default=None),
    since: datetime | None = Query(default=None, description="ISO 8601; varsayılan son 30 gün"),
    state: str | None = Query(default=None, pattern="^(running|finished)$"),
    include_dry_run: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
):
    now = _now()
    since = since or now - timedelta(days=_HISTORY_DAYS)
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    runs = [g for g in md.state(now)["groups"] if g["last_row_at"] >= since
            and (entity_type is None or g["entity_type"] == entity_type)
            and (state is None or g["state"] == state)
            and (include_dry_run or not g["dry_run"])]
    return {"runs": [md.run_view(g) for g in runs[:limit]], "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ")}


@app.get("/api/v1/zabbix-sync/runs/{run_id}")
def zabbix_sync_run(run_id: str):
    st = md.state(_now())
    groups = [md.run_view(g) for g in st["groups"] if g["run_id"] == run_id]
    rows = [r for r in st["rows"] if r["run_id"] == run_id]
    if not rows:
        raise HTTPException(status_code=404, detail="run not found")
    return {"run_id": run_id, "groups": groups, **md.build_sections(rows)}


def _snapshot_or_wait():
    mode = os.getenv("HMDL_MOCK_SNAPSHOT_STATE", "").strip().lower()
    if mode == "unavailable":
        return None, JSONResponse(status_code=503, content={"detail": "datalake unavailable"})
    if mode == "preparing":
        return None, JSONResponse(status_code=202, content={"status": "preparing", "retry_after_s": 60})
    now = _now()
    st = md.state(now)
    # The refresher runs every HMDL_SYNC_SNAPSHOT_MIN minutes; stale after two missed rounds.
    every = int(md.SYNC_SNAPSHOT_MIN)
    generated = now.replace(minute=(now.minute // every) * every, second=0, microsecond=0)
    if mode == "stale":
        generated -= timedelta(minutes=3 * every)
    age = now - generated
    meta = {"generated_at": md.iso(generated), "status": "ok",
            "stale": age > timedelta(minutes=2 * md.SYNC_SNAPSHOT_MIN)}
    return (st, meta), None


def _out(h: dict) -> dict:
    return {**h, "status_since": md.iso(h.get("status_since")), "last_seen_at": md.iso(h.get("last_seen_at"))}


_I_VARIANTS = str.maketrans({"İ": "i", "I": "i", "ı": "i"})


def _fold(v) -> str:
    return str(v or "").translate(_I_VARIANTS).casefold()


@app.get("/api/v1/zabbix-sync/summary")
def zabbix_sync_summary():
    got, wait = _snapshot_or_wait()
    if wait:
        return wait
    st, meta = got
    by: dict[str, dict] = {}
    for h in st["hosts"].values():
        d = by.setdefault(h["entity_type"], {})
        d[h["status"]] = d.get(h["status"], 0) + 1
    latest: dict[str, dict] = {}
    for g in st["groups"]:  # newest first
        v = md.run_view(g)
        d = latest.setdefault(g["entity_type"], {"latest": v, "latest_complete": None})
        if d["latest_complete"] is None and g.get("complete"):
            d["latest_complete"] = v
    return {"snapshot": meta, "hosts_by_status": by, "latest_runs": latest,
            "entity_type_resolution": st["resolution"]}


@app.get("/api/v1/zabbix-sync/hosts")
def zabbix_sync_hosts(
    status: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    device_type: str | None = Query(default=None),
    device_role: str | None = Query(default=None),
    manufacturer: str | None = Query(default=None),
    dc: str | None = Query(default=None),
    reason_code: str | None = Query(default=None),
    problems_only: bool = Query(default=False),
    q: str | None = Query(default=None, description="ad, Zabbix host adı ya da IP içinde arama"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=1000),
):
    got, wait = _snapshot_or_wait()
    if wait:
        return wait
    st, meta = got
    want = md.normalize_status(status) if status else None
    items = []
    for h in st["hosts"].values():
        if want and h["status"] != want:
            continue
        if problems_only and h["status"] not in md.PROBLEM_STATUSES:
            continue
        if entity_type and h["entity_type"] != entity_type:
            continue
        if reason_code and h["reason_code"] != reason_code:
            continue
        if dc and (h.get("dc_code") or "").upper() != dc.upper():
            continue
        if device_type and _fold(h.get("device_type")) != _fold(device_type):
            continue
        if device_role and _fold(h.get("device_role")) != _fold(device_role):
            continue
        if manufacturer and _fold(h.get("manufacturer")) != _fold(manufacturer):
            continue
        if q and _fold(q) not in " ".join(_fold(h.get(k)) for k in ("name", "zabbix_hostname", "ip")):
            continue
        items.append(h)
    items.sort(key=lambda h: (h["entity_type"], _fold(h.get("name")), h["host_key"]))
    start = (page - 1) * page_size
    return {"snapshot": meta, "total": len(items), "page": page, "page_size": page_size,
            "hosts": [_out(h) for h in items[start:start + page_size]]}


@app.get("/api/v1/zabbix-sync/hosts/{host_key:path}")
def zabbix_sync_host(host_key: str, limit: int = Query(default=50, ge=1, le=500)):
    got, wait = _snapshot_or_wait()
    if wait:
        return wait
    st, meta = got
    et, _, rest = host_key.partition(":")
    if rest.startswith("name:"):
        device_id, name = None, rest[len("name:"):]
    else:
        device_id, name = (int(rest), None) if rest.isdigit() else (None, rest)
    history = [r for r in st["rows"] if r["host_entity_type"] == et
               and (r["source_device_id"] == device_id if device_id is not None
                    else r["source_device_id"] is None and r["source_device_name"] == name)]
    history = sorted(history, key=lambda r: r["processed_at"], reverse=True)[:limit]
    host = st["hosts"].get(host_key)
    if host is None and not history:
        raise HTTPException(status_code=404, detail="host not found")
    return {"snapshot": meta, "host": _out(host) if host else None, "history": [md.host_row(r) for r in history]}


@app.get("/api/v1/dq/entities")
def dq_entities(
    kok_neden: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    family: str | None = Query(default=None),
    dc: str | None = Query(default=None),
    problems_only: bool = Query(default=False),
    include_leaf: bool = Query(default=False, description="vm ve ibm_lpar satırları da gelsin"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=500, ge=1, le=2000),
):
    mode = os.getenv("HMDL_MOCK_SNAPSHOT_STATE", "").strip().lower()
    if mode == "unavailable":
        return JSONResponse(status_code=503, content={"detail": "datalake unavailable"})
    if mode == "preparing":
        return JSONResponse(status_code=202, content={"status": "preparing", "retry_after_s": 120})
    now = _now()
    st = md.state(now)
    body = md.dq_entities_response(st["dq_state"], st["dq_run"], now, kok_neden=kok_neden,
                                   entity_type=entity_type, family=family, dc=dc,
                                   problems_only=problems_only, include_leaf=include_leaf)
    start = (page - 1) * page_size
    body["entities"] = body["entities"][start:start + page_size]
    body.update(page=page, page_size=page_size)
    return body


@app.get("/api/v1/dq/runs")
def dq_runs(limit: int = Query(default=30, ge=1, le=200)):
    st = md.state(_now())
    return {"runs": md.dq_runs_view(st["dq_runs"], st["anchor"], limit)}


@app.get("/api/v1/automation/status")
def automation_status():
    st = md.state(_now())
    return {"generated_at": md.iso(_now()), "status_since_basis": "since_service_start",
            "automations": [dict(a) for a in st["automations"]]}


@app.get("/api/v1/automation/awx-revisions")
def automation_awx_revisions():
    if os.getenv("HMDL_MOCK_AWX_REVISIONS", "").strip().lower() == "unconfigured":
        raise HTTPException(status_code=503,
                            detail="AWX read is not configured (AWX_ENABLED, AWX_API_URL, AWX_TOKEN)")
    return md.state(_now())["awx"]
