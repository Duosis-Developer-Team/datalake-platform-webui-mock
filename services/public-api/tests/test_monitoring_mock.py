"""DLP-020 mock public API: /v1/monitoring/* behind the ``monitoring:read`` scope.

Mirrors Datalake-Platform-GUI services/public-api (origin/development e9f39020): routes.py
``_add_monitoring_routes``, main.py ``make_require`` and error handlers, errors.py envelope,
upstream.py status mapping, shared/public_api/keys.py scopes and key format, scrub.py.
"""
from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app as hmdl_app
from public_api import mock_keys
from public_api.main import create_app
from public_api.upstream import Upstream, scrub

HMDL = TestClient(hmdl_app)
client = TestClient(create_app(hmdl_api=Upstream("http://hmdl-api", client=HMDL)))
MON = {"Authorization": f"Bearer {mock_keys.MONITORING_KEY}"}
DC_ONLY = {"Authorization": f"Bearer {mock_keys.DATACENTERS_KEY}"}

ROUTES = ("summary", "runs", "runs/{run_id}", "hosts", "hosts/{host_key}")
PUBLIC_PATHS = {
    "/v1/monitoring/zabbix-sync/summary", "/v1/monitoring/zabbix-sync/runs",
    "/v1/monitoring/zabbix-sync/runs/{run_id}", "/v1/monitoring/zabbix-sync/hosts",
    "/v1/monitoring/zabbix-sync/hosts/{host_key}", "/v1/monitoring/dq/entities", "/v1/monitoring/dq/runs",
    "/v1/monitoring/automation/status", "/v1/monitoring/automation/awx-revisions",
}


def _envelope(r, status, code):
    assert r.status_code == status, (r.status_code, r.text)
    body = r.json()
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message", "request_id"}
    assert body["error"]["code"] == code
    assert r.headers["X-Request-ID"] == body["error"]["request_id"]


def _strip(body):
    return {k: v for k, v in body.items() if k != "generated_at"} if isinstance(body, dict) else body


def test_mock_keys_have_the_real_format_and_scopes():
    assert mock_keys.SCOPE_MONITORING == "monitoring:read"
    assert mock_keys.SCOPES == ("customer:read", "customers:read", "datacenters:read", "monitoring:read")
    for key in (mock_keys.MONITORING_KEY, mock_keys.DATACENTERS_KEY):
        assert mock_keys.KEY_RE.match(key), key
    assert mock_keys.lookup(mock_keys.MONITORING_KEY).scopes == frozenset({"monitoring:read"})
    assert mock_keys.lookup("dlp_0000a001_" + "x" * 43) is None  # right prefix, wrong secret


@pytest.mark.parametrize("path", sorted(PUBLIC_PATHS))
def test_no_key_is_401(path):
    url = path.replace("{run_id}", "x").replace("{host_key}", "device:1")
    _envelope(client.get(url), 401, "unauthorized")
    _envelope(client.get(url, headers={"Authorization": "Bearer not-a-key"}), 401, "unauthorized")


@pytest.mark.parametrize("path", sorted(PUBLIC_PATHS))
def test_other_scope_is_403(path):
    url = path.replace("{run_id}", "x").replace("{host_key}", "device:1")
    _envelope(client.get(url, headers=DC_ONLY), 403, "forbidden")


def test_x_api_key_header_works():
    r = client.get("/v1/monitoring/dq/runs", headers={"X-API-Key": mock_keys.MONITORING_KEY})
    assert r.status_code == 200 and r.json()["runs"]


@pytest.mark.parametrize("public, internal", [
    ("zabbix-sync/summary", "zabbix-sync/summary"),
    ("zabbix-sync/runs", "zabbix-sync/runs"),
    ("zabbix-sync/hosts", "zabbix-sync/hosts"),
    ("dq/entities", "dq/entities"),
    ("dq/runs", "dq/runs"),
    ("automation/status", "automation/status"),
    ("automation/awx-revisions", "automation/awx-revisions"),
])
def test_body_is_the_hmdl_body(public, internal):
    r = client.get(f"/v1/monitoring/{public}", headers=MON)
    assert r.status_code == 200, r.text
    assert _strip(r.json()) == _strip(HMDL.get(f"/api/v1/{internal}").json())
    assert r.headers.get("X-Request-ID")


def test_parameters_pass_through():
    p = {"entity_type": "device", "include_dry_run": "true", "limit": "4"}
    runs = client.get("/v1/monitoring/zabbix-sync/runs", headers=MON, params=p).json()
    assert _strip(runs) == _strip(HMDL.get("/api/v1/zabbix-sync/runs", params=p).json())
    assert any(g["dry_run"] for g in runs["runs"]) and {g["entity_type"] for g in runs["runs"]} == {"device"}
    p = {"problems_only": "true", "dc": "DC13", "page_size": "5", "q": "dc13"}
    assert client.get("/v1/monitoring/zabbix-sync/hosts", headers=MON, params=p).json() == \
        HMDL.get("/api/v1/zabbix-sync/hosts", params=p).json()
    p = {"include_leaf": "true", "family": "virt", "page": "1", "page_size": "2"}
    assert client.get("/v1/monitoring/dq/entities", headers=MON, params=p).json() == \
        HMDL.get("/api/v1/dq/entities", params=p).json()


def test_run_and_host_detail():
    run_id = HMDL.get("/api/v1/zabbix-sync/runs").json()["runs"][0]["run_id"]
    assert client.get(f"/v1/monitoring/zabbix-sync/runs/{run_id}", headers=MON).json() == \
        HMDL.get(f"/api/v1/zabbix-sync/runs/{run_id}").json()
    for key in ("virtual_fw:884", "device:name:dc16-pdu-a3"):
        r = client.get(f"/v1/monitoring/zabbix-sync/hosts/{key}", headers=MON, params={"limit": 2})
        assert r.status_code == 200, r.text
        assert r.json() == HMDL.get(f"/api/v1/zabbix-sync/hosts/{key}", params={"limit": 2}).json()
        assert len(r.json()["history"]) == 2


def test_not_found_is_the_envelope():
    _envelope(client.get("/v1/monitoring/zabbix-sync/runs/19990101000000", headers=MON), 404, "not_found")
    _envelope(client.get("/v1/monitoring/zabbix-sync/hosts/device:999999", headers=MON), 404, "not_found")
    _envelope(client.get("/v1/monitoring/nothing-here", headers=MON), 404, "not_found")


def test_bad_parameter_is_400():
    _envelope(client.get("/v1/monitoring/zabbix-sync/runs", headers=MON, params={"limit": 0}), 400, "bad_request")
    _envelope(client.get("/v1/monitoring/zabbix-sync/runs", headers=MON, params={"state": "done"}), 400,
              "bad_request")
    _envelope(client.get("/v1/monitoring/dq/entities", headers=MON, params={"page_size": 2001}), 400, "bad_request")


def test_preparing_is_202_with_retry_after(monkeypatch):
    monkeypatch.setenv("HMDL_MOCK_SNAPSHOT_STATE", "preparing")
    r = client.get("/v1/monitoring/zabbix-sync/hosts", headers=MON)
    assert r.status_code == 202 and r.headers["Retry-After"] == "30"
    body = r.json()
    assert body["status"] == "preparing" and body["retry_after"] == 30 and body["request_id"]


def test_unavailable_is_503(monkeypatch):
    monkeypatch.setenv("HMDL_MOCK_SNAPSHOT_STATE", "unavailable")
    r = client.get("/v1/monitoring/zabbix-sync/summary", headers=MON)
    _envelope(r, 503, "unavailable")
    assert r.headers["Retry-After"] == "60"
    monkeypatch.setenv("HMDL_MOCK_SNAPSHOT_STATE", "")
    monkeypatch.setenv("HMDL_MOCK_AWX_REVISIONS", "unconfigured")
    _envelope(client.get("/v1/monitoring/automation/awx-revisions", headers=MON), 503, "unavailable")


def test_upstream_down_is_502():
    def refuse(request):
        raise httpx.ConnectError("refused", request=request)

    down = TestClient(create_app(hmdl_api=Upstream("http://hmdl-api", client=httpx.Client(
        base_url="http://hmdl-api", transport=httpx.MockTransport(refuse)))))
    _envelope(down.get("/v1/monitoring/dq/runs", headers=MON), 502, "upstream_error")


def test_scrub_drops_money_and_internal_keys():
    assert scrub({"unit_price_tl": 1, "x": [{"cost": 2, "ok": 3, "sql": "select"}], "currency": "TRY",
                  "retry_after_s": 60}) == {"x": [{"ok": 3}], "retry_after_s": 60}


def test_openapi_lists_the_monitoring_routes():
    schema = client.get("/openapi.json").json()
    mine = {p for p in schema["paths"] if p.startswith("/v1/monitoring/")}
    assert mine == PUBLIC_PATHS
    for p in mine:
        assert schema["paths"][p]["get"]["tags"] == ["monitoring"]
    assert "monitoring:read" in schema["info"]["description"]
    assert schema["components"]["securitySchemes"]["bearer"]["scheme"] == "bearer"
