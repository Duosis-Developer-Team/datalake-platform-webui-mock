"""DLP-014 (16.10): mock twin of customer-api's resources freshness / 202 contract."""
from __future__ import annotations

from src.services import mock_client
from src.services.mock_data import customers as mc

TR = {"start": "2026-10-10", "end": "2026-10-16", "preset": "7d"}


def test_default_answer_is_fresh_with_window(monkeypatch):
    monkeypatch.delenv(mc.MOCK_FRESHNESS_ENV, raising=False)
    data = mock_client.get_customer_resources("Akbank", TR)
    assert data["freshness"] == {"state": "fresh", "computed_at": mc.MOCK_COMPUTED_AT,
                                 "window": {"start": "2026-10-10", "end": "2026-10-16"}}
    assert data["totals"]


def test_previous_window_is_one_day_earlier(monkeypatch):
    monkeypatch.setenv(mc.MOCK_FRESHNESS_ENV, "previous_window")
    data = mock_client.get_customer_resources("Akbank", TR)
    assert data["freshness"]["state"] == "previous_window"
    assert data["freshness"]["window"] == {"start": "2026-10-09", "end": "2026-10-15"}


def test_preparing_is_the_202_body_not_an_empty_bundle(monkeypatch):
    monkeypatch.setenv(mc.MOCK_FRESHNESS_ENV, "preparing")
    data = mock_client.get_customer_resources("Akbank", TR)
    assert set(data) == {"status", "customer", "window", "eta_s", "queued_at", "position"}
    assert data["status"] == "preparing"
    assert "totals" not in data


def test_failed_is_the_503_body_not_an_empty_bundle(monkeypatch):
    """Faz 0 (19.10): MOCK_CUSTOMER_FRESHNESS=failed answers the failed body."""
    monkeypatch.setenv(mc.MOCK_FRESHNESS_ENV, "failed")
    data = mock_client.get_customer_resources("Akbank", TR)
    assert set(data) == {"status", "reason", "customer", "window", "failed_at", "retry_after_s"}
    assert data["status"] == "failed" and data["reason"] in ("timeout", "db_error", "other")
    assert data["window"] == {"start": "2026-10-10", "end": "2026-10-16"}
    assert data["retry_after_s"] > 0
    assert "totals" not in data and "assets" not in data
