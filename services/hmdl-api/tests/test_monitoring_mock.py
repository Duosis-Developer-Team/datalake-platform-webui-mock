"""DLP-020 mock: /api/v1/zabbix-sync/*, /api/v1/dq/*, /api/v1/automation/* (KB standart/11 §1.2).

Shapes come from tests/contract.py (read from the GUI code); with ``DLP_GUI_REPO`` set to a
GUI checkout, ``test_contract_parity_with_gui`` also compares them with the real routers.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests import contract as C
from tests import shape

client = TestClient(app)
API = "/api/v1"


def get(path, **params):
    r = client.get(f"{API}/{path}", params=params)
    assert r.status_code == 200, (path, r.status_code, r.text)
    return r.json()


def _ts(v: str) -> datetime:
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


# ── zabbix-sync ─────────────────────────────────────────────────────────────
def test_runs_shape_and_order():
    body = get("zabbix-sync/runs")
    assert set(body) == {"runs", "generated_at"}
    runs = body["runs"]
    assert runs, "fixture has runs"
    for g in runs:
        assert set(g) == C.RUN_VIEW_KEYS
        assert tuple(g["counts"]) == C.SUMMARY_KEYS
        assert g["state"] in ("running", "finished")
        assert sum(g["counts"].values()) == g["row_count"]
    last = [g["last_row_at"] for g in runs]
    assert last == sorted(last, reverse=True), "newest first"
    assert {g["entity_type"] for g in runs} == {"device", "platform", "virtual_fw"}


def test_runs_hide_dry_run_by_default_and_filter():
    default = get("zabbix-sync/runs")["runs"]
    assert not any(g["dry_run"] for g in default)
    with_dry = get("zabbix-sync/runs", include_dry_run="true")["runs"]
    assert any(g["dry_run"] for g in with_dry) and len(with_dry) > len(default)
    dry = next(g for g in with_dry if g["dry_run"])
    assert dry["complete"] is False
    assert {g["entity_type"] for g in get("zabbix-sync/runs", entity_type="platform")["runs"]} == {"platform"}
    running = get("zabbix-sync/runs", state="running")["runs"]
    assert running and all(g["state"] == "running" and g["complete"] is False for g in running)
    assert len(get("zabbix-sync/runs", limit=2)["runs"]) == 2
    assert client.get(f"{API}/zabbix-sync/runs", params={"state": "done"}).status_code == 422
    assert client.get(f"{API}/zabbix-sync/runs", params={"limit": 0}).status_code == 422


def test_runs_since_filter():
    runs = get("zabbix-sync/runs")["runs"]
    cut = _ts(runs[2]["last_row_at"])
    recent = get("zabbix-sync/runs", since=cut.isoformat())["runs"]
    assert recent and all(_ts(g["last_row_at"]) >= cut for g in recent)
    assert len(recent) < len(runs)


def test_run_detail_sections_match_counts():
    for g in get("zabbix-sync/runs", include_dry_run="true")["runs"]:
        body = get(f"zabbix-sync/runs/{g['run_id']}")
        assert set(body) == {"run_id", "groups", "summary", "sections"}
        assert tuple(body["sections"]) == C.SECTIONS
        assert tuple(body["summary"]) == C.SUMMARY_KEYS
        assert any(x["run_id"] == g["run_id"] for x in body["groups"])
        for x in body["groups"]:
            assert set(x) == C.RUN_VIEW_KEYS
        # summary counts every row of the run (all groups); listed sections match their counters
        total = {k: sum(x["counts"][k] for x in body["groups"]) for k in C.SUMMARY_KEYS}
        assert body["summary"] == total
        for sec, key in (("failed", "eklenemedi"), ("update_failed", "güncellenemedi"), ("skipped", "atlandı"),
                         ("added", "eklendi"), ("updated", "güncellendi"), ("dry_run_create", "dry_run_create"),
                         ("dry_run_update", "dry_run_update")):
            assert len(body["sections"][sec]) == body["summary"][key], (g["run_id"], sec)
            for h in body["sections"][sec]:
                assert set(h) == C.HOST_ROW_KEYS
                assert h["run_id"] == g["run_id"]


def test_run_detail_404():
    r = client.get(f"{API}/zabbix-sync/runs/19990101000000")
    assert r.status_code == 404 and r.json() == {"detail": "run not found"}


def test_summary_shape():
    body = get("zabbix-sync/summary")
    assert set(body) == {"snapshot", "hosts_by_status", "latest_runs", "entity_type_resolution"}
    assert set(body["snapshot"]) == C.SNAPSHOT_META_KEYS and body["snapshot"]["stale"] is False
    assert set(body["entity_type_resolution"]) == C.RESOLUTION_KEYS
    hosts = get("zabbix-sync/hosts", page_size=1000)["hosts"]
    by: dict = {}
    for h in hosts:
        by.setdefault(h["entity_type"], {}).setdefault(h["status"], 0)
        by[h["entity_type"]][h["status"]] += 1
    assert body["hosts_by_status"] == by
    runs = get("zabbix-sync/runs", include_dry_run="true")["runs"]
    for et, d in body["latest_runs"].items():
        assert set(d) == {"latest", "latest_complete"}
        mine = [g for g in runs if g["entity_type"] == et]
        assert d["latest"] == mine[0]
        assert d["latest_complete"] == next((g for g in mine if g["complete"]), None)


def test_hosts_shape_and_vocabulary():
    first = get("zabbix-sync/hosts")
    assert set(first) == {"snapshot", "total", "page", "page_size", "hosts"}
    assert first["page"] == 1 and first["page_size"] == 200 and len(first["hosts"]) == min(200, first["total"])
    body = get("zabbix-sync/hosts", page_size=1000)
    assert body["total"] == len(body["hosts"]) == first["total"]
    for h in body["hosts"]:
        assert set(h) == C.SNAPSHOT_HOST_KEYS
        assert h["status"] in C.STATUSES and h["status"] != "dry_run"
        assert h["reason_code"] in C.REASON_CODES
        assert h["host_key"].startswith(h["entity_type"] + ":")
        assert h["ownership"] is None  # not in zabbix_sync_log: never made up
        assert h["runs_in_status"] >= 1
        assert _ts(h["status_since"]) <= _ts(h["last_seen_at"])
        if h["status"] in ("eklendi", "güncellendi", "güncel"):
            assert h["reason_code"] == "none" and h["reason"] is None or h["status"] == "güncellendi"
        if h["status"] in C.PROBLEM_STATUSES:
            assert h["reason_code"] not in ("none", "not_monitored") and h["reason"]
    codes = {h["reason_code"] for h in body["hosts"]}
    assert {"ip_missing", "vfw_vendor_missing", "zabbix_api_error", "not_monitored"} <= codes
    assert any(h["seen_in_latest_complete_run"] is False for h in body["hosts"])
    assert any(h["host_key"].split(":", 1)[1].startswith("name:") for h in body["hosts"])
    keys = [(h["entity_type"], h["name"].casefold(), h["host_key"]) for h in body["hosts"]]
    assert keys == sorted(keys)


def test_hosts_filters():
    def keys(**p):
        return {h["host_key"] for h in get("zabbix-sync/hosts", page_size=1000, **p)["hosts"]}

    everything = get("zabbix-sync/hosts", page_size=1000)["hosts"]
    problems = {h["host_key"] for h in everything if h["status"] in C.PROBLEM_STATUSES}
    assert problems and keys(problems_only="true") == problems
    assert keys(entity_type="virtual_fw") == {h["host_key"] for h in everything if h["entity_type"] == "virtual_fw"}
    assert keys(reason_code="ip_missing") == {h["host_key"] for h in everything if h["reason_code"] == "ip_missing"}
    assert keys(dc="dc14") == {h["host_key"] for h in everything if h["dc_code"] == "DC14"}
    upd = {h["host_key"] for h in everything if h["status"] == "güncellenemedi"}
    assert upd and keys(status="GÜNCELLENEMEDİ") == upd  # normalize_status: Turkish capitals
    hpe = {h["host_key"] for h in everything if (h["manufacturer"] or "").casefold() == "hpe"}
    assert hpe and keys(manufacturer="hpe") == hpe
    one = next(h for h in everything if h["ip"])
    assert one["host_key"] in keys(q=one["ip"])
    assert keys(q="DC16-PDU") == keys(q="dc16-pdu") != set()  # case-insensitive search


def test_hosts_paging():
    total = get("zabbix-sync/hosts")["total"]
    body = get("zabbix-sync/hosts", page=2, page_size=3)
    assert body["total"] == total and body["page"] == 2 and body["page_size"] == 3
    assert len(body["hosts"]) == min(3, max(0, total - 3))
    assert client.get(f"{API}/zabbix-sync/hosts", params={"page_size": 1001}).status_code == 422


def test_host_detail():
    hosts = get("zabbix-sync/hosts", page_size=1000)["hosts"]
    for h in hosts:
        body = get(f"zabbix-sync/hosts/{h['host_key']}")
        assert set(body) == {"snapshot", "host", "history"}
        assert body["host"] == h
        assert body["history"], h["host_key"]
        for row in body["history"]:
            assert set(row) == C.HOST_ROW_KEYS and row["host_key"] == h["host_key"]
        stamps = [row["processed_at"] for row in body["history"]]
        assert stamps == sorted(stamps, reverse=True)
        assert body["history"][0]["status"] == h["status"]
        in_status = [row for row in body["history"] if _ts(row["processed_at"]) >= _ts(h["status_since"])]
        assert len(in_status) == h["runs_in_status"]
        assert all(row["status"] == h["status"] for row in in_status)
    assert len(get(f"zabbix-sync/hosts/{hosts[0]['host_key']}", limit=1)["history"]) == 1


def test_host_detail_name_key_and_404():
    named = next(h for h in get("zabbix-sync/hosts", page_size=1000)["hosts"] if ":name:" in h["host_key"])
    assert get(f"zabbix-sync/hosts/{named['host_key']}")["host"]["source_device_id"] is None
    r = client.get(f"{API}/zabbix-sync/hosts/device:999999")
    assert r.status_code == 404 and r.json() == {"detail": "host not found"}


@pytest.mark.parametrize("state, code, body", [
    ("preparing", 202, {"status": "preparing", "retry_after_s": 60}),
    ("unavailable", 503, {"detail": "datalake unavailable"}),
])
def test_snapshot_states(monkeypatch, state, code, body):
    monkeypatch.setenv("HMDL_MOCK_SNAPSHOT_STATE", state)
    for path in ("zabbix-sync/summary", "zabbix-sync/hosts", "zabbix-sync/hosts/device:15231"):
        r = client.get(f"{API}/{path}")
        assert (r.status_code, r.json()) == (code, body), path


# ── DQ ──────────────────────────────────────────────────────────────────────
def test_dq_entities_shape():
    body = get("dq/entities")
    assert set(body) == {"status_since_basis", "run", "total", "entities", "page", "page_size"}
    assert body["status_since_basis"] == "since_service_start"
    assert set(body["run"]) == C.DQ_RUN_KEYS
    assert body["page"] == 1 and body["page_size"] == 500
    for e in body["entities"]:
        assert set(e) == C.DQ_ENTITY_KEYS
        assert e["entity_type"] not in C.DQ_LEAF_TYPES
        assert e["family"] in ("virt", "backup", "storage")
        assert e["last_run_id"] == body["run"]["run_id"]
        if e["age_hours"] is not None:
            assert e["future_timestamp"] == (e["age_hours"] < 0)
    order = [(e["family"], e["entity_type"], e["entity_key"]) for e in body["entities"]]
    assert order == sorted(order)
    assert any(e["future_timestamp"] for e in body["entities"])


def test_dq_entities_filters_and_leaf():
    base = get("dq/entities")
    leaf = get("dq/entities", include_leaf="true")
    assert leaf["total"] > base["total"]
    assert {e["entity_type"] for e in leaf["entities"]} & C.DQ_LEAF_TYPES
    probs = get("dq/entities", problems_only="true")["entities"]
    assert probs and all(e["kok_neden"] in C.DQ_PROBLEM_KOK for e in probs)
    assert {e["entity_key"] for e in probs} == {e["entity_key"] for e in base["entities"]
                                                 if e["kok_neden"] in C.DQ_PROBLEM_KOK}
    assert all(e["family"] == "backup" for e in get("dq/entities", family="backup")["entities"])
    assert all(e["dc_code"] == "DC13" for e in get("dq/entities", dc="dc13")["entities"])
    assert all(e["kok_neden"] == "stale" for e in get("dq/entities", kok_neden="stale")["entities"])
    paged = get("dq/entities", page=2, page_size=2)
    assert paged["total"] == base["total"] and paged["entities"] == base["entities"][2:4]


def test_dq_runs():
    body = get("dq/runs")
    assert set(body) == {"runs"}
    runs = body["runs"]
    assert runs and all(set(r) == C.DQ_RUN_KEYS for r in runs)
    assert runs[0] == get("dq/entities")["run"]
    fin = [r["finished_at"] for r in runs]
    assert fin == sorted(fin, reverse=True)
    assert any(r["complete"] is False for r in runs), "an incomplete run is in the fixture"
    assert len(get("dq/runs", limit=3)["runs"]) == 3


# ── automation ──────────────────────────────────────────────────────────────
def test_automation_status():
    body = get("automation/status")
    assert set(body) == {"generated_at", "status_since_basis", "automations"}
    assert body["status_since_basis"] == "since_service_start"
    items = body["automations"]
    assert [a["key"] for a in items] == ["zabbix_sync", "collector_sync", "reachability_checks", "vm_reconciliation"]
    for a in items:
        assert set(a) == C.AUTOMATION_KEYS and a["state"] in C.AUTOMATION_STATES
        if a["age_hours"] is None:
            assert a["state"] == "unknown"
        elif a["age_hours"] >= a["dead_hours"]:
            assert a["state"] == "dead"
        elif a["age_hours"] >= a["warn_hours"]:
            assert a["state"] == "stale"
        else:
            assert a["state"] == "fresh"
    assert len({a["state"] for a in items}) >= 2


def test_awx_revisions():
    body = get("automation/awx-revisions")
    assert set(body) == {"repo", "jobs", "off_main", "unknown"}
    assert body["repo"] == "Duosis-Developer-Team/project-zabake"
    for j in body["jobs"]:
        assert set(j) == C.AWX_JOB_KEYS
        assert (j["on_main"] is None) == (j["reason"] is not None and "main dışı" not in j["reason"])
    assert body["off_main"] == sum(1 for j in body["jobs"] if j["on_main"] is False) >= 1
    assert body["unknown"] == sum(1 for j in body["jobs"] if j["on_main"] is None) >= 1


def test_awx_revisions_not_configured(monkeypatch):
    monkeypatch.setenv("HMDL_MOCK_AWX_REVISIONS", "unconfigured")
    r = client.get(f"{API}/automation/awx-revisions")
    assert r.status_code == 503
    assert r.json() == {"detail": "AWX read is not configured (AWX_ENABLED, AWX_API_URL, AWX_TOKEN)"}


# ── parity with the real routers ────────────────────────────────────────────
_URLS = {"zabbix-sync/summary": "zabbix-sync/summary", "zabbix-sync/runs": "zabbix-sync/runs",
         "zabbix-sync/runs/{run_id}": None, "zabbix-sync/hosts": "zabbix-sync/hosts",
         "zabbix-sync/hosts/{host_key}": None, "dq/entities": "dq/entities", "dq/runs": "dq/runs",
         "automation/status": "automation/status", "automation/awx-revisions": "automation/awx-revisions"}


def _mock_shapes() -> dict:
    run_id = get("zabbix-sync/runs")["runs"][0]["run_id"]
    host_key = get("zabbix-sync/hosts")["hosts"][0]["host_key"]
    urls = dict(_URLS, **{"zabbix-sync/runs/{run_id}": f"zabbix-sync/runs/{run_id}",
                          "zabbix-sync/hosts/{host_key}": f"zabbix-sync/hosts/{host_key}"})
    return {e: shape.shape(e, get(u)) for e, u in urls.items()}


def test_mock_shapes_cover_every_path():
    for endpoint, paths in _mock_shapes().items():
        missing = [p for p, keys in paths.items() if keys is None]
        assert not missing, (endpoint, missing)


@pytest.mark.skipif(not os.getenv("DLP_GUI_REPO"), reason="DLP_GUI_REPO (a Datalake-Platform-GUI checkout) not set")
def test_contract_parity_with_gui():
    probe = os.path.join(os.path.dirname(__file__), "gui_probe.py")
    out = subprocess.run([sys.executable, probe, os.environ["DLP_GUI_REPO"]], capture_output=True, text=True,
                         timeout=120)
    assert out.returncode == 0, out.stderr
    real = json.loads(out.stdout)
    mine = _mock_shapes()
    assert set(real) == set(mine)
    diffs = {(e, p): {"only_gui": sorted(set(real[e][p] or []) - set(mine[e][p] or [])),
                      "only_mock": sorted(set(mine[e][p] or []) - set(real[e][p] or []))}
             for e in real for p in real[e] if real[e][p] != mine[e][p]}
    assert not diffs, diffs


def test_now_relative_fixtures_are_fresh():
    """Times are relative to process start: the newest run is hours old, not days."""
    newest = _ts(get("zabbix-sync/runs")["runs"][0]["last_row_at"])
    assert datetime.now(timezone.utc) - newest < timedelta(hours=12)
