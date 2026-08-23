"""W0 static-capacity mock: GUI api_client contract + all-or-nothing CSV import."""

from __future__ import annotations

from importlib import reload

import pytest

from src.services.mock_data import crm as mock_crm

_NETWORK_HEADER = (
    "dc,public_ip,subnet_30,spine_port,leaf_port,mgmt_port,"
    "internet_total_mbps,internet_sellable_mbps,ddos_capable,ddos_sellable_mbps"
)


def _network_csv(*rows: str) -> str:
    return _NETWORK_HEADER + "\n" + "\n".join(rows) + "\n"


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    mock_crm.reset_static_capacity()
    yield
    mock_crm.reset_static_capacity()


def test_get_payload_shape() -> None:
    payload = mock_crm.list_static_capacity()
    assert set(payload) >= {"network", "waf_lb", "openstack", "gpu", "imports"}
    assert len(payload["network"]) == 12
    assert payload["network"][0]["dc"] == "DC11"
    assert payload["waf_lb"]["appliance_size"] == "5g"
    assert payload["waf_lb"]["max_units_200m"] == 900
    assert payload["waf_lb"]["total_throughput_gbps"] == 350.0
    assert any(r["kind"] == "ceph" and r["key"] == "ceph_sellable_tib" for r in payload["openstack"])
    assert any(r["gpu_model"] == "H100" for r in payload["gpu"])


def test_put_roundtrip() -> None:
    current = mock_crm.list_static_capacity()
    current["network"][0]["internet_sellable_mbps"] = 1700
    current["waf_lb"]["appliance_size"] = "200m"
    saved = mock_crm.save_static_capacity(
        {"network": current["network"], "waf_lb": current["waf_lb"]},
        updated_by="tester",
    )
    assert saved["network"][0]["internet_sellable_mbps"] == 1700
    assert saved["waf_lb"]["appliance_size"] == "200m"
    assert saved["network"][0]["updated_by"] == "tester"


def test_template_headers() -> None:
    text = mock_crm.static_capacity_template("network")
    first = text.splitlines()[0]
    assert first == _NETWORK_HEADER
    os_text = mock_crm.static_capacity_template("openstack")
    assert os_text.startswith("kind,key,label,quantity,unit,hypervisor,notes")
    gpu_text = mock_crm.static_capacity_template("gpu")
    assert gpu_text.startswith("gpu_model,package_key,quantity,hypervisor,notes")
    with pytest.raises(ValueError, match="unknown dataset"):
        mock_crm.static_capacity_template("waf")


def test_import_preview_does_not_write() -> None:
    csv_text = _network_csv("DC11,40,10,54,94,40,4000,1600,true,1500")
    preview = mock_crm.import_static_capacity_csv(
        "network", csv_text, filename="n.csv", confirm=False
    )
    assert preview["ok"] is True
    assert preview["status"] == "preview"
    assert preview["changed"] == 1
    stored = mock_crm.list_static_capacity()
    dc11 = next(r for r in stored["network"] if r["dc"] == "DC11")
    assert dc11["internet_sellable_mbps"] == 1500
    assert stored["imports"] == []


def test_import_confirm_writes() -> None:
    csv_text = _network_csv("DC11,40,10,54,94,40,4000,1600,true,1500")
    result = mock_crm.import_static_capacity_csv(
        "network", csv_text, filename="n.csv", confirm=True
    )
    assert result["ok"] is True
    assert result["status"] == "imported"
    dc11 = next(r for r in result["payload"]["network"] if r["dc"] == "DC11")
    assert dc11["internet_sellable_mbps"] == 1600
    assert len(result["payload"]["imports"]) == 1


def test_import_invalid_is_all_or_nothing() -> None:
    csv_text = _network_csv(
        "DC11,40,10,54,94,40,4000,1600,true,1500",
        "DC99,1,1,1,1,1,100,50,true,50",
    )
    before = mock_crm.list_static_capacity()
    result = mock_crm.import_static_capacity_csv(
        "network", csv_text, filename="bad.csv", confirm=True
    )
    assert result["ok"] is False
    assert result["status"] == "error"
    assert result["errors"]
    after = mock_crm.list_static_capacity()
    assert after["network"] == before["network"]
    assert after["imports"] == []


def test_api_client_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_MODE", "mock")
    import src.services.api_client as ac

    reload(ac)
    payload = ac.get_static_capacity()
    assert len(payload["network"]) == 12
    csv_text = ac.get_static_capacity_template("network")
    assert csv_text.splitlines()[0].startswith("dc,")
    preview = ac.post_static_capacity_import(
        dataset="network",
        csv_text=_network_csv("DC11,40,10,54,94,40,4000,1500,true,1500"),
        filename="same.csv",
        confirm=False,
    )
    assert preview["status"] == "preview"
    with pytest.raises(ValueError):
        ac.post_static_capacity_import(
            dataset="network",
            csv_text=_network_csv("NOPE,1,1,1,1,1,1,1,true,1"),
            confirm=True,
        )
    reload(ac)
