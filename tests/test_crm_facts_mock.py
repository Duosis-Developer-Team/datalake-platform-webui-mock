"""CRM facts mock contract — GET /api/v1/crm/facts* shape.

Reference: crm-engine `app/routers/facts.py` and `shared/sellable/facts.py`
in Datalake-Platform-GUI (PR #18 producer, PR #24 dc_panels/global merge).
"""

from __future__ import annotations

import os

import pytest

from src.services import api_client, mock_client
from src.services.mock_data import crm as mock_crm

TOTAL_SELLABLE_TL = 1_474_305.0
TOTAL_SOLD_TL = 925_157.0
FACT_COUNT = 14

FACT_FIELDS = {
    "dc_code",
    "panel_key",
    "service_group",
    "family",
    "resource_kind",
    "unit",
    "total",
    "used",
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

AGGREGATE_ROW_FIELDS = {"sellable_tl", "sellable_qty", "sold_tl", "fact_count"}


@pytest.fixture(autouse=True)
def _mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_MODE", "mock")
    os.environ["APP_MODE"] = "mock"


@pytest.fixture(autouse=True)
def _reset_partial() -> None:
    mock_crm.set_facts_partial(False)
    yield
    mock_crm.set_facts_partial(False)


def _sum_rows(rows: list[dict]) -> float:
    return sum(float(r["sellable_tl"]) for r in rows if r["sellable_tl"] is not None)


def test_aggregates_agree_with_summary() -> None:
    """by-dc == by-service == by-region == summary, from one fact set."""
    bundle = mock_crm.crm_facts("*")
    dc_sum = _sum_rows(bundle["by_dc"])
    svc_sum = _sum_rows(bundle["by_service"])
    region_sum = _sum_rows(bundle["by_region"])
    assert dc_sum == pytest.approx(svc_sum, abs=0.01)
    assert dc_sum == pytest.approx(region_sum, abs=0.01)
    assert dc_sum == pytest.approx(float(bundle["sellable_tl"]), abs=0.01)
    assert dc_sum == pytest.approx(TOTAL_SELLABLE_TL, abs=0.01)


def test_mock_client_and_api_client_summary() -> None:
    via_client = mock_client.get_crm_facts_summary("*")
    via_api = api_client.get_crm_facts_summary("*")
    assert via_client == via_api
    assert via_api["status"] == "ok"
    assert via_api["sellable_tl"] == TOTAL_SELLABLE_TL
    assert via_api["total_sellable_tl"] == TOTAL_SELLABLE_TL
    assert via_api["min"] == via_api["max"] == TOTAL_SELLABLE_TL
    assert via_api["sold_tl"] == TOTAL_SOLD_TL
    assert via_api["fact_count"] == FACT_COUNT
    assert len(via_api["etag"]) == 16


def test_facts_envelope_has_no_internal_keys() -> None:
    """GET /crm/facts returns five keys; aggregates live on their own routes."""
    payload = mock_client.get_crm_facts("*")
    assert set(payload) == {"scope", "status", "etag", "facts", "sellable_tl"}


def test_fact_row_schema() -> None:
    rows = mock_client.get_crm_facts("*")["facts"]
    assert len(rows) == FACT_COUNT
    for row in rows:
        assert FACT_FIELDS <= set(row)


def test_global_rows_are_present_and_land_in_unassigned() -> None:
    """PR #24 keeps dc_code='*' rows; the region map has no entry for them."""
    rows = mock_client.get_crm_facts("*")["facts"]
    global_rows = [r for r in rows if r["dc_code"] == "*"]
    assert len(global_rows) == 5

    regions = {r["region"]: r for r in mock_client.get_crm_facts_by_region("*")["rows"]}
    assert set(regions) == {"Türkiye", "Asya", "Avrupa", "unassigned"}
    assert regions["unassigned"]["fact_count"] == len(global_rows)
    assert regions["unassigned"]["sellable_tl"] == pytest.approx(1_425_105.0, abs=0.01)


def test_unpriced_facts_keep_null_unit_price() -> None:
    """Network and OpenStack are genuinely unpriced — never invent a price."""
    rows = mock_client.get_crm_facts("*")["facts"]
    by_group: dict[str, list[dict]] = {}
    for row in rows:
        by_group.setdefault(row["service_group"], []).append(row)

    for group in ("network", "openstack_gpu", "management"):
        assert by_group[group], f"{group} must be represented"
        for row in by_group[group]:
            assert row["unit_price_tl"] is None

    openstack = by_group["openstack_gpu"][0]
    assert openstack["sellable_qty"] is not None
    assert openstack["sellable_tl"] is None


def test_non_normal_status_carries_no_money() -> None:
    rows = mock_client.get_crm_facts("*")["facts"]
    statuses = {r["status"] for r in rows}
    assert {"normal", "hesaplanamiyor", "satisa_bagli_degil"} <= statuses
    for row in rows:
        if row["status"] != "normal":
            assert row["sellable_tl"] is None
            assert row["reason"]


def test_aggregate_rows_expose_qty_and_sold() -> None:
    for getter, key in (
        (mock_client.get_crm_facts_by_dc, "dc_code"),
        (mock_client.get_crm_facts_by_service, "service_group"),
        (mock_client.get_crm_facts_by_region, "region"),
    ):
        payload = getter("*")
        assert set(payload) == {"scope", "status", "etag", "rows", "sellable_tl"}
        rows = payload["rows"]
        assert rows
        for row in rows:
            assert AGGREGATE_ROW_FIELDS | {key} <= set(row)
        assert sum(r["fact_count"] for r in rows) == FACT_COUNT


def test_by_service_follows_engine_group_order() -> None:
    rows = mock_client.get_crm_facts_by_service("*")["rows"]
    groups = [r["service_group"] for r in rows]
    assert groups == [
        "intel_km",
        "intel_hc",
        "ibm_power",
        "replication",
        "netbackup",
        "s3",
        "network",
        "openstack_gpu",
        "management",
    ]


def test_scope_filters_to_one_dc() -> None:
    payload = mock_client.get_crm_facts("DC13")
    assert payload["scope"] == "DC13"
    assert {r["dc_code"] for r in payload["facts"]} == {"DC13"}
    rows = mock_client.get_crm_facts_by_dc("DC13")["rows"]
    assert [r["dc_code"] for r in rows] == ["DC13"]


def test_partial_coverage_returns_status_not_a_number() -> None:
    mock_crm.set_facts_partial(True)

    facts = mock_client.get_crm_facts("*")
    assert facts["status"] == "partial"
    assert facts["reason"] == "coverage_incomplete"
    assert facts["facts"] is None
    assert facts["sellable_tl"] is None

    for getter in (
        mock_client.get_crm_facts_by_dc,
        mock_client.get_crm_facts_by_service,
        mock_client.get_crm_facts_by_region,
    ):
        payload = getter("*")
        assert payload["status"] == "partial"
        assert payload["rows"] is None
        assert payload["sellable_tl"] is None

    summary = mock_client.get_crm_facts_summary("*")
    assert summary["status"] == "partial"
    assert summary["total_sellable_tl"] is None
    assert summary["min"] is None
    assert summary["max"] is None


def test_mock_payloads_are_isolated_between_calls() -> None:
    first = mock_client.get_crm_facts("*")
    first["facts"][0]["sellable_tl"] = -1.0
    second = mock_client.get_crm_facts("*")
    assert second["facts"][0]["sellable_tl"] != -1.0
