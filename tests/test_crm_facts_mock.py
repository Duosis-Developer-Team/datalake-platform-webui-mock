"""CRM facts mock contract — GET /api/v1/crm/facts* shape."""

from __future__ import annotations

import os

import pytest

from src.services import api_client, mock_client
from src.services.mock_data import crm as mock_crm


@pytest.fixture(autouse=True)
def _mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_MODE", "mock")
    os.environ["APP_MODE"] = "mock"


def test_facts_by_dc_equals_by_service() -> None:
    bundle = mock_crm.crm_facts("*")
    dc_sum = sum(float(r["sellable_tl"]) for r in bundle["by_dc"])
    svc_sum = sum(float(r["sellable_tl"]) for r in bundle["by_service"])
    assert abs(dc_sum - svc_sum) < 0.01
    assert abs(dc_sum - float(bundle["sellable_tl"])) < 0.01
    assert abs(dc_sum - 5580.0) < 0.01


def test_mock_client_and_api_client_summary() -> None:
    via_client = mock_client.get_crm_facts_summary("*")
    via_api = api_client.get_crm_facts_summary("*")
    assert via_client["sellable_tl"] == via_api["sellable_tl"] == 5580.0
    assert via_api["status"] == "ok"
    assert "etag" in via_api


def test_fact_row_schema() -> None:
    rows = mock_client.get_crm_facts("*")["facts"]
    required = {
        "dc_code",
        "panel_key",
        "service_group",
        "family",
        "resource_kind",
        "unit",
        "total",
        "used",
        "used_max",
        "used_avg",
        "used_cur",
        "threshold",
        "sellable_qty",
        "unit_price_tl",
        "sellable_tl",
        "sold_qty",
        "sold_tl",
        "status",
        "reason",
        "basis",
        "measured_at",
    }
    assert required <= set(rows[0])
    assert {r["dc_code"] for r in rows} == {"DC13", "DC14"}
    missing_price = [r for r in rows if r["status"] == "fiyat_yok"]
    assert missing_price
    assert missing_price[0]["sellable_qty"] > 0
    assert missing_price[0]["sellable_tl"] is None


def test_envelope_has_both_tl_fields_and_scope_filter() -> None:
    by_dc = mock_client.get_crm_facts_by_dc("*")
    assert by_dc["sellable_tl"] == by_dc["total_sellable_tl"] == 5580.0
    assert by_dc["unassigned_share"] == 0.0
    assert "region" in by_dc["rows"][0]
    scoped = mock_crm.crm_facts("DC13")
    assert abs(float(scoped["sellable_tl"]) - 360.0) < 0.01
    assert {r["dc_code"] for r in scoped["facts"]} == {"DC13"}

