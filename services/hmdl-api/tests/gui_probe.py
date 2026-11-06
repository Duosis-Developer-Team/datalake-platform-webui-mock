"""Shapes of the REAL hmdl-api monitoring responses, printed as JSON (run in a subprocess).

    python gui_probe.py <GUI checkout root>

Mounts the GUI's own routers (``app.routers.zabbix_sync`` and ``monitoring_state``) on a bare
FastAPI app, feeds them through the GUI's own state builders (``fold_streaks``, ``classify_runs``,
``dq_state.advance``, ``awx_revisions.collect_jobs``) with the database and AWX calls replaced by
one sample row each, and prints ``shape.shape(endpoint, body)`` for every endpoint. No DB, no AWX.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone

gui = os.path.abspath(sys.argv[1])
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(gui, "services", "hmdl-api"), gui, here]
for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
    del sys.modules[name]

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import shape  # noqa: E402
from app.config import settings  # noqa: E402
from app.db.queries import zabbix_sync as zq  # noqa: E402
from app.routers import monitoring_state, zabbix_sync  # noqa: E402
from app.services import automation_state, awx_client, awx_revisions, dq_state  # noqa: E402
from app.services import zabbix_sync_snapshot as snap  # noqa: E402
from app.services.zabbix_sync_runs import classify_runs, run_view  # noqa: E402

NOW = datetime.now(timezone.utc)
T = NOW - timedelta(hours=2)
ROW = {"host_entity_type": "device", "source_device_id": 7, "source_device_name": "dc13-sw-07",
       "device_type": "N9K", "device_role": "SWITCH", "manufacturer_name": "Cisco", "root_location_name": "DC13",
       "location_name": "DC13-A", "site_name": "DC13", "tenant_name": None, "zabbix_host_ip": "10.0.0.7",
       "zabbix_hostid": "1007", "zabbix_hostname": "dc13-sw-07", "status": "güncellendi", "operation": "update",
       "reason": "ip_changed:10.0.0.6->10.0.0.7", "field_merge_actions": None, "error_payload": None,
       "run_id": "r5", "processed_at": T, "dry_run": False}
FAILED = {**ROW, "source_device_id": 8, "source_device_name": "dc13-sw-08", "status": "eklenemedi",
          "operation": "create", "reason": "IP adresi bulunamadı"}
GROUPS = [{"run_id": f"r{i}", "entity_type": "device", "started_at": NOW - timedelta(hours=8 * (6 - i), minutes=30),
           "last_row_at": NOW - timedelta(hours=8 * (6 - i)), "row_count": 100, "dry_run": False,
           "counts": {"güncel": 98, "güncellendi": 1, "eklenemedi": 1}} for i in range(1, 6)]

zq.fetch_run_groups = lambda since: [dict(g) for g in GROUPS]
zq.fetch_run_rows = lambda run_id: [ROW, FAILED] if run_id == "r5" else []
zq.fetch_host_history = lambda **kw: [ROW]

hosts = snap.fold_streaks([ROW, FAILED])
snap.mark_latest_complete(hosts, {"device": set(hosts)})
snap._set_for_test({"status": "ok", "generated_at": NOW, "hosts": hosts,
                    "runs": [run_view(g) for g in classify_runs([dict(g) for g in GROUPS], NOW, 45, 0.9)],
                    "entity_type_resolution": {"inferred_rows": 0, "unresolved_rows": 0, "role_conflicts": 0}})

dq_state.dq_q.list_runs = lambda n: [{"run_id": f"dq-{i}", "started_at": NOW - timedelta(hours=2 * i, minutes=40),
                                      "finished_at": NOW - timedelta(hours=2 * i), "status": "ok",
                                      "entity_count": 6600} for i in range(1, 8)]
_run = dq_state.runs_view(1)[0]
_entity = {"entity_key": "k", "family": "virt", "entity_type": "cluster", "entity_name": "DC13-CL-01",
           "dc_code": "DC13", "platform": "vmware", "metric_source": "cluster_metrics", "kok_neden": "stale",
           "kok_neden_aciklama": "x", "last_seen_at": NOW - timedelta(hours=30), "is_customer": False}
dq_state._set_for_test(dq_state.advance({}, _run["run_id"], NOW, [_entity], True), _run)

automation_state.ah_q.build_automation_health = lambda: {"automations": [
    {"key": "zabbix_sync", "label": "NetBox → Zabbix Sync", "cadence": "~8 saatte bir", "status": "fresh",
     "last_run_at": T, "age_hours": 2.0, "warn_hours": 12.0, "dead_hours": 24.0, "extra": {}}]}


def _awx(path, params=None):
    if path.startswith("/projects/"):
        return {"name": "HMDL", "scm_branch": "development"}
    if path == "/job_templates/":
        return {"results": [{"id": 26, "name": "jt"}]}
    return {"results": [{"id": 1, "finished": "2026-11-05T01:23:00Z", "status": "successful", "scm_revision": "abc"}]}


awx_client.is_read_configured = lambda: True
awx_client.get_json = _awx
awx_revisions.github_compare = lambda rev: "identical"
settings.awx_prod_project_ids = "18"

api = FastAPI()
api.include_router(zabbix_sync.router, prefix="/api/v1")
api.include_router(monitoring_state.router, prefix="/api/v1")
client = TestClient(api)

URLS = {"zabbix-sync/summary": "zabbix-sync/summary", "zabbix-sync/runs": "zabbix-sync/runs",
        "zabbix-sync/runs/{run_id}": "zabbix-sync/runs/r5", "zabbix-sync/hosts": "zabbix-sync/hosts",
        "zabbix-sync/hosts/{host_key}": "zabbix-sync/hosts/device:7", "dq/entities": "dq/entities",
        "dq/runs": "dq/runs", "automation/status": "automation/status",
        "automation/awx-revisions": "automation/awx-revisions"}
out = {}
for endpoint, url in URLS.items():
    r = client.get(f"/api/v1/{url}")
    if r.status_code != 200:
        raise SystemExit(f"{url}: {r.status_code} {r.text}")
    out[endpoint] = shape.shape(endpoint, r.json())
print(json.dumps(out, ensure_ascii=False, sort_keys=True))
