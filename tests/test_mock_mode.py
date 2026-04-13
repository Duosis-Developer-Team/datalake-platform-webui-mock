"""Tests for APP_MODE=mock data layer and api_client delegation."""

from __future__ import annotations

import os
from importlib import reload

import pytest

from src.pages.global_view import CITY_COORDINATES, _build_globe_data
from src.services import mock_client
from src.services.mock_data import daa_scenarios
from src.services.mock_data.customers import MOCK_CUSTOMER_NAMES, get_customer_resources
from src.services.mock_data.datacenters import MOCK_DC_CODES, get_all_datacenters_summary, get_dc_detail


def test_mock_dc_codes_count() -> None:
    assert len(MOCK_DC_CODES) == 4
    assert "FRA-DC1" in MOCK_DC_CODES


def test_get_dc_detail_has_compute_sections() -> None:
    ist = get_dc_detail("IST-DC1")
    assert ist["meta"]["location"]
    assert ist["classic"].get("hosts", 0) > 0
    assert ist["hyperconv"].get("hosts", 0) > 0
    assert ist["power"].get("lpar_count", 0) > 0


def test_izm_is_nutanix_only() -> None:
    izm = get_dc_detail("IZM-DC1")
    assert not izm.get("classic")
    assert izm.get("hyperconv", {}).get("hosts", 0) > 0


def test_mock_global_dashboard() -> None:
    d = mock_client.get_global_dashboard({})
    assert d["overview"]["dc_count"] == 4
    assert d["overview"]["total_vms"] > 0


def test_daa_quick_actions() -> None:
    qa = daa_scenarios.quick_actions_for_path("/daa")
    assert len(qa) >= 3
    for a in qa:
        assert a.get("user_text")
        assert not str(a["user_text"]).lower().startswith("quick:")


def test_daa_report_rows() -> None:
    cols, rows = daa_scenarios.daa_report_rows("summary", None)
    assert "dc" in cols
    assert len(rows) == 4


@pytest.fixture()
def mock_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_MODE", "mock")
    import src.services.api_client as ac

    reload(ac)
    yield ac
    monkeypatch.delenv("APP_MODE", raising=False)
    reload(ac)


def test_api_client_delegates_when_mock(mock_env) -> None:
    ac = mock_env
    lst = ac.get_customer_list()
    assert "Akbank" in lst
    s = ac.get_all_datacenters_summary(None)
    assert len(s) == 4


def test_mock_summaries_site_names_on_global_map_keys() -> None:
    for s in get_all_datacenters_summary():
        sn = (s.get("site_name") or "").upper().strip()
        assert sn in CITY_COORDINATES, f"site_name {sn!r} must exist in CITY_COORDINATES"


def test_mock_global_globe_data_has_points() -> None:
    pts = _build_globe_data(get_all_datacenters_summary())
    assert isinstance(pts, list)
    assert len(pts) == len(MOCK_DC_CODES)


def test_mock_customer_resources_match_view_schema() -> None:
    for name in MOCK_CUSTOMER_NAMES:
        r = get_customer_resources(name)
        totals = r["totals"]
        assets = r["assets"]
        assert int(totals.get("vms_total", 0) or 0) > 0
        assert "classic" in assets and "hyperconv" in assets
        assert int(assets["classic"].get("vm_count", 0) or 0) >= 0
        assert int(assets["hyperconv"].get("vm_count", 0) or 0) >= 0
        assert (int(assets["classic"].get("vm_count", 0) or 0) > 0) or (
            int(assets["hyperconv"].get("vm_count", 0) or 0) > 0
        )
        backup = totals.get("backup") or {}
        assert "veeam_defined_sessions" in backup


def test_api_client_live_without_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_MODE", raising=False)
    import src.services.api_client as ac

    reload(ac)
    assert ac._is_mock_mode() is False
    reload(ac)
