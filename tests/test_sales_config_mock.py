"""W1+W6 sales-config mock: GUI api_client contract, builtin S1–S4, copy."""

from __future__ import annotations

from importlib import reload

import pytest

from src.services.mock_data import crm as mock_crm


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    mock_crm.reset_sales_config()
    yield
    mock_crm.reset_sales_config()


def test_get_parameters_shape() -> None:
    payload = mock_crm.get_sales_parameters()
    assert set(payload) >= {"calc", "thresholds", "ratios", "discounts", "etag"}
    calc = payload["calc"]
    assert calc["usage_basis"] == "max"
    assert calc["upsell_enabled"] is False
    assert calc["replication_provider"] == "veeam"
    assert calc["waflb_appliance"] == "5g"
    assert calc["waflb_distribute"] is False
    families = {(r["scope_kind"], r["scope_key"], r["kind"]) for r in payload["discounts"]}
    assert ("family", "virt_km", "new_sale") in families
    assert ("family", "backup_zerto_replication", "upsell") in families
    assert len(payload["discounts"]) == 10
    assert payload["etag"]


def test_put_calc_and_discount_roundtrip() -> None:
    out = mock_crm.put_sales_calc(usage_basis="avg", upsell_enabled=True, waflb_appliance="1g")
    assert out["status"] == "ok"
    assert "usage_basis" in out["updated"]
    payload = mock_crm.get_sales_parameters()
    assert payload["calc"]["usage_basis"] == "avg"
    assert payload["calc"]["upsell_enabled"] is True
    assert payload["calc"]["waflb_appliance"] == "1g"
    mock_crm.put_sales_discount(
        scope_kind="family",
        scope_key="virt_km",
        kind="new_sale",
        ratio=0.15,
    )
    row = next(
        r
        for r in mock_crm.list_sales_discounts()
        if r["scope_key"] == "virt_km" and r["kind"] == "new_sale"
    )
    assert row["ratio"] == 0.15
    with pytest.raises(ValueError, match="ratio"):
        mock_crm.put_sales_discount(
            scope_kind="family",
            scope_key="virt_km",
            kind="new_sale",
            ratio=1.0,
        )


def test_put_threshold_and_ratio_persist() -> None:
    mock_crm.put_sales_threshold(
        resource_type="cpu",
        dc_code="*",
        sellable_limit_pct=72.0,
        panel_key=None,
    )
    thr = next(r for r in mock_crm.list_thresholds() if r["resource_type"] == "cpu")
    assert thr["sellable_limit_pct"] == 72.0
    mock_crm.put_sales_ratio(
        "virt_hyperconverged",
        dc_code="*",
        cpu_per_unit=2.0,
        ram_gb_per_unit=16.0,
        storage_gb_per_unit=200.0,
    )
    ratio = next(r for r in mock_crm.list_resource_ratios() if r["family"] == "virt_hyperconverged")
    assert ratio["cpu_per_unit"] == 2.0
    assert ratio["ram_gb_per_unit"] == 16.0
    with pytest.raises(ValueError, match="ratios"):
        mock_crm.put_sales_ratio("virt_hyperconverged", cpu_per_unit=0)


def test_builtin_scenarios_immutable_copy_ok() -> None:
    rows = mock_crm.list_sales_scenarios()
    assert {r["scenario_key"] for r in rows} == {"S1", "S2", "S3", "S4"}
    assert all(r["is_builtin"] for r in rows)
    assert rows[0]["payload"]["replication_share"] is None
    with pytest.raises(ValueError, match="builtin"):
        mock_crm.update_sales_scenario("S1", label="nope")
    with pytest.raises(ValueError, match="builtin"):
        mock_crm.delete_sales_scenario("S2")
    with pytest.raises(ValueError, match="reserved"):
        mock_crm.create_sales_scenario(scenario_key="S3", label="nope")
    copied = mock_crm.copy_sales_scenario("S1")
    assert copied["scenario_key"] == "S1_copy"
    assert copied["is_builtin"] is False
    assert "copy" in copied["label"].lower()
    assert copied["payload"] == rows[0]["payload"]
    mock_crm.update_sales_scenario("S1_copy", label="Peak Q3", payload={"upsell_enabled": True})
    mock_crm.delete_sales_scenario("S1_copy")
    keys = {r["scenario_key"] for r in mock_crm.list_sales_scenarios()}
    assert "S1_copy" not in keys
    assert "S1" in keys


def test_create_user_scenario_and_copy_collision() -> None:
    created = mock_crm.create_sales_scenario(
        scenario_key="peak_q3",
        label="Peak Q3",
        payload={"replication_share": 0.25},
        sort_order=80,
    )
    assert created["is_builtin"] is False
    first = mock_crm.copy_sales_scenario("peak_q3")
    assert first["scenario_key"] == "peak_q3_copy"
    second = mock_crm.copy_sales_scenario("peak_q3")
    assert second["scenario_key"] == "peak_q3_copy_2"
    named = mock_crm.copy_sales_scenario("S4", new_key="custom_gap", label="Custom gap")
    assert named["scenario_key"] == "custom_gap"
    assert named["label"] == "Custom gap"
    assert named["is_builtin"] is False


def test_api_client_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_MODE", "mock")
    import src.services.api_client as ac

    reload(ac)
    payload = ac.get_sales_parameters()
    assert payload["calc"]["usage_basis"] == "max"
    assert len(payload["discounts"]) == 10
    ac.put_sales_calc(replication_provider="zerto")
    assert ac.get_sales_parameters()["calc"]["replication_provider"] == "zerto"
    rows = ac.list_sales_scenarios()
    assert len(rows) == 4
    copied = ac.copy_sales_scenario("S2", new_key="s2_lab")
    assert copied["scenario_key"] == "s2_lab"
    with pytest.raises(ValueError, match="builtin"):
        ac.delete_sales_scenario("S1")
    reload(ac)
