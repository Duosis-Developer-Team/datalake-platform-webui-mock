from __future__ import annotations
import os
from copy import deepcopy
from typing import Any, Optional
from urllib.parse import quote

import httpx

# Microservices: set per-service URLs, or use API_BASE_URL for a single gateway.
_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
DATACENTER_API_URL = os.getenv("DATACENTER_API_URL", _API_BASE).rstrip("/")
CUSTOMER_API_URL = os.getenv("CUSTOMER_API_URL", _API_BASE).rstrip("/")
QUERY_API_URL = os.getenv("QUERY_API_URL", _API_BASE).rstrip("/")

_EMPTY_DASHBOARD = {
    "overview": {
        "dc_count": 0,
        "total_hosts": 0,
        "total_vms": 0,
        "total_platforms": 0,
        "total_energy_kw": 0.0,
        "total_cpu_cap": 0.0,
        "total_cpu_used": 0.0,
        "total_ram_cap": 0.0,
        "total_ram_used": 0.0,
        "total_storage_cap": 0.0,
        "total_storage_used": 0.0,
    },
    "platforms": {
        "nutanix": {"hosts": 0, "vms": 0},
        "vmware": {"clusters": 0, "hosts": 0, "vms": 0},
        "ibm": {"hosts": 0, "vios": 0, "lpars": 0},
    },
    "energy_breakdown": {"ibm_kw": 0.0, "vcenter_kw": 0.0},
    "classic_totals": {
        "cpu_cap": 0.0,
        "cpu_used": 0.0,
        "mem_cap": 0.0,
        "mem_used": 0.0,
        "stor_cap": 0.0,
        "stor_used": 0.0,
    },
    "hyperconv_totals": {
        "cpu_cap": 0.0,
        "cpu_used": 0.0,
        "mem_cap": 0.0,
        "mem_used": 0.0,
        "stor_cap": 0.0,
        "stor_used": 0.0,
    },
    "ibm_totals": {
        "mem_total": 0.0,
        "mem_assigned": 0.0,
        "cpu_used": 0.0,
        "cpu_assigned": 0.0,
        "stor_cap": 0.0,
        "stor_used": 0.0,
    },
}

_EMPTY_DC_DETAIL = {
    "meta": {"name": "", "location": "", "description": ""},
    "intel": {
        "clusters": 0,
        "hosts": 0,
        "vms": 0,
        "cpu_cap": 0.0,
        "cpu_used": 0.0,
        "ram_cap": 0.0,
        "ram_used": 0.0,
        "storage_cap": 0.0,
        "storage_used": 0.0,
    },
    "power": {
        "hosts": 0,
        "vms": 0,
        "vios": 0,
        "lpar_count": 0,
        "cpu": 0,
        "cpu_used": 0.0,
        "cpu_assigned": 0.0,
        "ram": 0,
        "memory_total": 0.0,
        "memory_assigned": 0.0,
        "storage_cap_tb": 0.0,
        "storage_used_tb": 0.0,
    },
    "energy": {
        "total_kw": 0.0,
        "ibm_kw": 0.0,
        "vcenter_kw": 0.0,
        "total_kwh": 0.0,
        "ibm_kwh": 0.0,
        "vcenter_kwh": 0.0,
    },
    "platforms": {
        "nutanix": {"hosts": 0, "vms": 0},
        "vmware": {"clusters": 0, "hosts": 0, "vms": 0},
        "ibm": {"hosts": 0, "vios": 0, "lpars": 0},
    },
}

_EMPTY_CUSTOMER = {"totals": {}, "assets": {}}
_EMPTY_QUERY = {"error": "API unreachable"}
_EMPTY_DATACENTERS: list[dict[str, Any]] = []
_EMPTY_CUSTOMERS: list[str] = []
_EMPTY_SLA_BY_DC: dict[str, dict] = {}

_transport = httpx.HTTPTransport(retries=3)
_client_dc = httpx.Client(base_url=DATACENTER_API_URL, timeout=30.0, transport=_transport)
_client_cust = httpx.Client(base_url=CUSTOMER_API_URL, timeout=30.0, transport=_transport)
_client_query = httpx.Client(base_url=QUERY_API_URL, timeout=30.0, transport=_transport)


def _is_mock_mode() -> bool:
    return (os.getenv("APP_MODE") or "").strip().lower() == "mock"


def _auth_headers() -> dict[str, str]:
    """Attach JWT for microservices when Flask request has an authenticated user."""
    if _is_mock_mode():
        return {}
    try:
        from flask import g, has_request_context

        if has_request_context():
            uid = getattr(g, "auth_user_id", None)
            if uid is not None:
                from src.auth.api_jwt import create_api_token

                tok = create_api_token(int(uid))
                return {"Authorization": f"Bearer {tok}"}
    except Exception:
        pass
    return {}


def _clone(value: Any) -> Any:
    return deepcopy(value)


def _build_time_params(tr: Optional[dict]) -> dict[str, str]:
    if not tr:
        return {}
    preset = tr.get("preset")
    if preset in {"1h", "1d", "7d", "30d"}:
        return {"preset": preset}
    start = tr.get("start")
    end = tr.get("end")
    if start and end:
        return {"start": str(start), "end": str(end)}
    return {}


def _get_json(client: httpx.Client, path: str, params: Optional[dict[str, str]] = None) -> Any:
    response = client.get(path, params=params, headers=_auth_headers())
    response.raise_for_status()
    return response.json()


def _put_json(client: httpx.Client, path: str, body: dict[str, Any]) -> Any:
    response = client.put(path, json=body, headers=_auth_headers())
    response.raise_for_status()
    return response.json()


def _delete_json(client: httpx.Client, path: str) -> Any:
    response = client.delete(path, headers=_auth_headers())
    response.raise_for_status()
    if not response.content:
        return {}
    return response.json()


def get_global_dashboard(tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_global_dashboard(tr)
    try:
        data = _get_json(_client_dc, "/api/v1/dashboard/overview", params=_build_time_params(tr))
        return data if isinstance(data, dict) else _clone(_EMPTY_DASHBOARD)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return _clone(_EMPTY_DASHBOARD)


def get_all_datacenters_summary(tr: Optional[dict]) -> list[dict]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_all_datacenters_summary(tr)
    try:
        data = _get_json(_client_dc, "/api/v1/datacenters/summary", params=_build_time_params(tr))
        return data if isinstance(data, list) else _clone(_EMPTY_DATACENTERS)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return _clone(_EMPTY_DATACENTERS)


def get_dc_details(dc_id: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_details(dc_id, tr)
    try:
        encoded_dc_id = quote(dc_id, safe="")
        data = _get_json(_client_dc, f"/api/v1/datacenters/{encoded_dc_id}", params=_build_time_params(tr))
        return data if isinstance(data, dict) else _clone(_EMPTY_DC_DETAIL)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return _clone(_EMPTY_DC_DETAIL)


def get_customer_list() -> list[str]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_customer_list()
    try:
        data = _get_json(_client_cust, "/api/v1/customers")
        return data if isinstance(data, list) else _clone(_EMPTY_CUSTOMERS)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return _clone(_EMPTY_CUSTOMERS)


def get_customer_resources(name: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_customer_resources(name, tr)
    try:
        encoded_name = quote(name, safe="")
        data = _get_json(
            _client_cust,
            f"/api/v1/customers/{encoded_name}/resources",
            params=_build_time_params(tr),
        )
        return data if isinstance(data, dict) else _clone(_EMPTY_CUSTOMER)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return _clone(_EMPTY_CUSTOMER)


def execute_registered_query(key: str, params: str) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.execute_registered_query(key, params)
    try:
        encoded_key = quote(key, safe="")
        data = _get_json(_client_query, f"/api/v1/queries/{encoded_key}", params={"params": params or ""})
        return data if isinstance(data, dict) else _clone(_EMPTY_QUERY)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return _clone(_EMPTY_QUERY)


def get_sla_by_dc(tr: Optional[dict]) -> dict[str, dict]:
    """Return SLA entries keyed by DC code (uppercase)."""
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_sla_by_dc(tr)
    try:
        data = _get_json(_client_dc, "/api/v1/sla", params=_build_time_params(tr))
        by_dc = (data or {}).get("by_dc") if isinstance(data, dict) else None
        return by_dc if isinstance(by_dc, dict) else _clone(_EMPTY_SLA_BY_DC)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return _clone(_EMPTY_SLA_BY_DC)


def get_dc_racks(dc_id: str) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_racks(dc_id)
    try:
        from urllib.parse import quote as _quote
        enc = _quote(dc_id, safe="")
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/racks")
        return data if isinstance(data, dict) else {"racks": [], "summary": {}}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"racks": [], "summary": {}}


def get_rack_devices(dc_id: str, rack_name: str) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_rack_devices(dc_id, rack_name)
    try:
        from urllib.parse import quote as _quote
        enc_dc = _quote(dc_id, safe="")
        enc_rack = _quote(rack_name, safe="")
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc_dc}/racks/{enc_rack}/devices")
        return data if isinstance(data, dict) else {"devices": []}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"devices": []}


def get_dc_s3_pools(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_s3_pools(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/s3/pools", params=_build_time_params(tr))
        return data if isinstance(data, dict) else {"pools": [], "latest": {}, "growth": {}}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"pools": [], "latest": {}, "growth": {}}


def get_customer_s3_vaults(customer_name: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_customer_s3_vaults(customer_name, tr)
    try:
        enc = quote(customer_name, safe="")
        data = _get_json(_client_cust, f"/api/v1/customers/{enc}/s3/vaults", params=_build_time_params(tr))
        return data if isinstance(data, dict) else {"vaults": [], "latest": {}, "growth": {}}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"vaults": [], "latest": {}, "growth": {}}


def get_dc_netbackup_pools(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_netbackup_pools(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/backup/netbackup", params=_build_time_params(tr))
        return data if isinstance(data, dict) else {"pools": [], "rows": []}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"pools": [], "rows": []}


def get_dc_zerto_sites(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_zerto_sites(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/backup/zerto", params=_build_time_params(tr))
        return data if isinstance(data, dict) else {"sites": [], "rows": []}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"sites": [], "rows": []}


def get_dc_veeam_repos(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_veeam_repos(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/backup/veeam", params=_build_time_params(tr))
        return data if isinstance(data, dict) else {"repos": [], "rows": []}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"repos": [], "rows": []}


def get_classic_cluster_list(dc_code: str, tr: Optional[dict]) -> list[str]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_classic_cluster_list(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/clusters/classic", params=_build_time_params(tr))
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_hyperconv_cluster_list(dc_code: str, tr: Optional[dict]) -> list[str]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_hyperconv_cluster_list(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        data = _get_json(
            _client_dc,
            f"/api/v1/datacenters/{enc}/clusters/hyperconverged",
            params=_build_time_params(tr),
        )
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def _clusters_param(selected: Optional[list[str]]) -> dict[str, str]:
    if not selected:
        return {}
    return {"clusters": ",".join(selected)}


def get_classic_metrics_filtered(
    dc_code: str, selected_clusters: Optional[list[str]], tr: Optional[dict]
) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_classic_metrics_filtered(dc_code, selected_clusters, tr)
    try:
        enc = quote(dc_code, safe="")
        params = {**_build_time_params(tr), **_clusters_param(selected_clusters)}
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/compute/classic", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_hyperconv_metrics_filtered(
    dc_code: str, selected_clusters: Optional[list[str]], tr: Optional[dict]
) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_hyperconv_metrics_filtered(dc_code, selected_clusters, tr)
    try:
        enc = quote(dc_code, safe="")
        params = {**_build_time_params(tr), **_clusters_param(selected_clusters)}
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/compute/hyperconverged", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_physical_inventory_dc(dc_name: str) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_physical_inventory_dc(dc_name)
    try:
        enc = quote(dc_name, safe="")
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/physical-inventory")
        return data if isinstance(data, dict) else {"total": 0, "by_role": [], "by_role_manufacturer": []}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"total": 0, "by_role": [], "by_role_manufacturer": []}


def get_physical_inventory_overview_by_role() -> list[dict]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_physical_inventory_overview_by_role()
    try:
        data = _get_json(_client_dc, "/api/v1/physical-inventory/overview/by-role")
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_physical_inventory_overview_manufacturer(role: str) -> list[dict]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_physical_inventory_overview_manufacturer(role)
    try:
        enc = quote(role, safe="")
        data = _get_json(_client_dc, "/api/v1/physical-inventory/overview/manufacturer", params={"role": enc})
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_physical_inventory_overview_location(role: str, manufacturer: str) -> list[dict]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_physical_inventory_overview_location(role, manufacturer)
    try:
        data = _get_json(
            _client_dc,
            "/api/v1/physical-inventory/overview/location",
            params={"role": role, "manufacturer": manufacturer},
        )
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_physical_inventory_customer() -> list[dict]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_physical_inventory_customer()
    try:
        data = _get_json(_client_dc, "/api/v1/physical-inventory/customer")
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


# ---------------------------------------------------------------------------
# Network > SAN (Brocade) + Power Mimari Storage (IBM)
# ---------------------------------------------------------------------------


def get_dc_san_switches(dc_code: str, tr: Optional[dict]) -> list[str]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_san_switches(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/san/switches", params=params)
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_dc_san_port_usage(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_san_port_usage(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/san/port-usage", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_dc_san_health(dc_code: str, tr: Optional[dict]) -> list[dict]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_san_health(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/san/health", params=params)
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_dc_san_traffic_trend(dc_code: str, tr: Optional[dict]) -> list[dict]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_san_traffic_trend(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/san/traffic-trend", params=params)
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_dc_san_bottleneck(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_san_bottleneck(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/san/bottleneck", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_dc_storage_capacity(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_storage_capacity(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/storage/capacity", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_dc_storage_performance(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_storage_performance(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/storage/performance", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


# ---------------------------------------------------------------------------
# Network Dashboard (Zabbix) + Intel Storage (Zabbix) - DC scoped
# ---------------------------------------------------------------------------


def _build_optional_params(base: dict[str, str], **kwargs: Optional[Any]) -> dict[str, str]:
    """Add non-None query params to base dict."""
    for k, v in kwargs.items():
        if v is not None:
            base[k] = str(v)
    return base


def get_dc_network_filters(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_network_filters(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/network/filters", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_dc_network_port_summary(
    dc_code: str,
    tr: Optional[dict],
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_network_port_summary(
            dc_code, tr, manufacturer, device_role, device_name
        )
    try:
        enc = quote(dc_code, safe="")
        params = _build_optional_params(
            _build_time_params(tr),
            manufacturer=manufacturer,
            device_role=device_role,
            device_name=device_name,
        )
        data = _get_json(
            _client_dc,
            f"/api/v1/datacenters/{enc}/network/port-summary",
            params=params,
        )
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_dc_network_95th_percentile(
    dc_code: str,
    tr: Optional[dict],
    top_n: int = 20,
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_network_95th_percentile(
            dc_code, tr, top_n, manufacturer, device_role, device_name
        )
    try:
        enc = quote(dc_code, safe="")
        params = _build_optional_params(
            _build_time_params(tr),
            top_n=top_n,
            manufacturer=manufacturer,
            device_role=device_role,
            device_name=device_name,
        )
        data = _get_json(
            _client_dc,
            f"/api/v1/datacenters/{enc}/network/95th-percentile",
            params=params,
        )
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_dc_network_interface_table(
    dc_code: str,
    tr: Optional[dict],
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_network_interface_table(
            dc_code,
            tr,
            page,
            page_size,
            search,
            manufacturer,
            device_role,
            device_name,
        )
    try:
        enc = quote(dc_code, safe="")
        params = _build_optional_params(
            _build_time_params(tr),
            page=page,
            page_size=page_size,
            search=search or "",
            manufacturer=manufacturer,
            device_role=device_role,
            device_name=device_name,
        )
        data = _get_json(
            _client_dc,
            f"/api/v1/datacenters/{enc}/network/interface-table",
            params=params,
        )
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_dc_zabbix_storage_capacity(dc_code: str, tr: Optional[dict], host: Optional[str] = None) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_zabbix_storage_capacity(dc_code, tr, host)
    try:
        enc = quote(dc_code, safe="")
        params = _build_optional_params(_build_time_params(tr), host=host)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/zabbix-storage/capacity", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_dc_zabbix_storage_trend(dc_code: str, tr: Optional[dict], host: Optional[str] = None) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_zabbix_storage_trend(dc_code, tr, host)
    try:
        enc = quote(dc_code, safe="")
        params = _build_optional_params(_build_time_params(tr), host=host)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/zabbix-storage/trend", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_dc_zabbix_storage_devices(dc_code: str, tr: Optional[dict]) -> list[dict]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_zabbix_storage_devices(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/zabbix-storage/devices", params=params)
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_dc_zabbix_disk_list(dc_code: str, tr: Optional[dict], host: Optional[str] = None) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_zabbix_disk_list(dc_code, tr, host)
    if host is None:
        return {"items": []}
    try:
        enc = quote(dc_code, safe="")
        params = _build_optional_params(_build_time_params(tr), host=host)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/zabbix-storage/disk-list", params=params)
        return data if isinstance(data, dict) else {"items": []}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"items": []}


def get_dc_zabbix_disk_trend(
    dc_code: str,
    tr: Optional[dict],
    host: Optional[str] = None,
    disk_name: Optional[str] = None,
) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_zabbix_disk_trend(dc_code, tr, host, disk_name)
    if host is None or disk_name is None:
        return {"series": []}
    try:
        enc = quote(dc_code, safe="")
        params = _build_optional_params(_build_time_params(tr), host=host, disk=disk_name)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/zabbix-storage/disk-trend", params=params)
        return data if isinstance(data, dict) else {"series": []}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {"series": []}


def get_dc_zabbix_disk_health(dc_code: str, tr: Optional[dict]) -> dict:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_zabbix_disk_health(dc_code, tr)
    try:
        enc = quote(dc_code, safe="")
        params = _build_time_params(tr)
        data = _get_json(_client_dc, f"/api/v1/datacenters/{enc}/zabbix-storage/disk-health", params=params)
        return data if isinstance(data, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def _auranotify_start_date(tr: Optional[dict]) -> str:
    from src.utils.time_range import time_range_to_bounds

    start_ts, _ = time_range_to_bounds(tr)
    return start_ts.strftime("%Y-%m-%dT%H:%M:%S")


def get_customer_availability_bundle(customer_name: str, tr: Optional[dict]) -> dict[str, Any]:
    """AuraNotify: service + VM downtimes and per-VM outage counts for the selected customer."""
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_customer_availability_bundle(customer_name, tr)
    try:
        from src.services import auranotify_client as aura

        return aura.get_customer_availability_bundle(customer_name or "", _auranotify_start_date(tr))
    except Exception:
        return {
            "service_downtimes": [],
            "vm_downtimes": [],
            "vm_outage_counts": {},
            "customer_id": None,
            "customer_ids": [],
        }


def get_dc_availability_sla_item(dc_code: str, dc_display_name: str, tr: Optional[dict]) -> Optional[dict[str, Any]]:
    """AuraNotify: one datacenter-services item matched to this DC (by name or code)."""
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_dc_availability_sla_item(dc_code, dc_display_name, tr)
    try:
        from src.services import auranotify_client as aura

        items = aura.get_dc_services_availability(_auranotify_start_date(tr))
        for hint in (dc_display_name or "", dc_code or ""):
            it = aura.match_dc_group_item(items, hint)
            if it:
                return it
        return None
    except Exception:
        return None


def get_crm_service_mapping_pages() -> list:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_crm_service_mapping_pages()
    try:
        data = _get_json(_client_cust, "/api/v1/crm/service-mapping/pages")
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_crm_service_mappings() -> list:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_crm_service_mappings()
    try:
        data = _get_json(_client_cust, "/api/v1/crm/service-mapping")
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def put_crm_service_mapping(
    productid: str,
    *,
    page_key: str,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.put_crm_service_mapping(productid, page_key=page_key, notes=notes)
    enc = quote(productid, safe="")
    body: dict[str, Any] = {"page_key": page_key}
    if notes is not None:
        body["notes"] = notes
    try:
        out = _put_json(_client_cust, f"/api/v1/crm/service-mapping/{enc}", body)
        return out if isinstance(out, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def delete_crm_service_mapping_override(productid: str) -> dict[str, Any]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.delete_crm_service_mapping_override(productid)
    enc = quote(productid, safe="")
    try:
        out = _delete_json(_client_cust, f"/api/v1/crm/service-mapping/{enc}/override")
        return out if isinstance(out, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_crm_aliases() -> list:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_crm_aliases()
    try:
        data = _get_json(_client_cust, "/api/v1/crm/aliases")
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def put_crm_alias(
    crm_accountid: str,
    *,
    canonical_customer_key: Optional[str] = None,
    netbox_musteri_value: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.put_crm_alias(
            crm_accountid,
            canonical_customer_key=canonical_customer_key,
            netbox_musteri_value=netbox_musteri_value,
            notes=notes,
        )
    enc = quote(crm_accountid, safe="")
    body = {
        "canonical_customer_key": canonical_customer_key,
        "netbox_musteri_value": netbox_musteri_value,
        "notes": notes,
    }
    try:
        out = _put_json(_client_cust, f"/api/v1/crm/aliases/{enc}", body)
        return out if isinstance(out, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def delete_crm_alias(crm_accountid: str) -> dict[str, Any]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.delete_crm_alias(crm_accountid)
    enc = quote(crm_accountid, safe="")
    try:
        out = _delete_json(_client_cust, f"/api/v1/crm/aliases/{enc}")
        return out if isinstance(out, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_crm_discovery_counts() -> list:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_crm_discovery_counts()
    try:
        data = _get_json(_client_cust, "/api/v1/crm/config/discovery-counts")
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def get_crm_config_thresholds() -> list:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_crm_config_thresholds()
    try:
        data = _get_json(_client_cust, "/api/v1/crm/config/thresholds")
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def put_crm_config_threshold(
    *,
    resource_type: str,
    dc_code: str,
    sellable_limit_pct: float,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.put_crm_config_threshold(
            resource_type=resource_type,
            dc_code=dc_code,
            sellable_limit_pct=sellable_limit_pct,
            notes=notes,
        )
    body = {
        "resource_type": resource_type,
        "dc_code": dc_code,
        "sellable_limit_pct": sellable_limit_pct,
        "notes": notes,
    }
    try:
        out = _put_json(_client_cust, "/api/v1/crm/config/thresholds", body)
        return out if isinstance(out, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def delete_crm_config_threshold(threshold_id: int) -> dict[str, Any]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.delete_crm_config_threshold(threshold_id)
    try:
        out = _delete_json(_client_cust, f"/api/v1/crm/config/thresholds/{int(threshold_id)}")
        return out if isinstance(out, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_crm_price_overrides() -> list:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_crm_price_overrides()
    try:
        data = _get_json(_client_cust, "/api/v1/crm/config/price-overrides")
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def put_crm_price_override(
    productid: str,
    *,
    product_name: Optional[str],
    unit_price_tl: float,
    resource_unit: Optional[str] = None,
    currency: Optional[str] = "TL",
    notes: Optional[str] = None,
) -> dict[str, Any]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.put_crm_price_override(
            productid,
            product_name=product_name,
            unit_price_tl=unit_price_tl,
            resource_unit=resource_unit,
            currency=currency,
            notes=notes,
        )
    enc = quote(productid, safe="")
    body: dict[str, Any] = {
        "product_name": product_name,
        "unit_price_tl": unit_price_tl,
        "resource_unit": resource_unit,
        "currency": currency,
        "notes": notes,
    }
    try:
        out = _put_json(_client_cust, f"/api/v1/crm/config/price-overrides/{enc}", body)
        return out if isinstance(out, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def delete_crm_price_override(productid: str) -> dict[str, Any]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.delete_crm_price_override(productid)
    enc = quote(productid, safe="")
    try:
        out = _delete_json(_client_cust, f"/api/v1/crm/config/price-overrides/{enc}")
        return out if isinstance(out, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}


def get_crm_calc_config() -> list:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.get_crm_calc_config()
    try:
        data = _get_json(_client_cust, "/api/v1/crm/config/variables")
        return data if isinstance(data, list) else []
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return []


def put_crm_calc_config(
    config_key: str,
    *,
    config_value: str,
    value_type: Optional[str] = None,
    description: Optional[str] = None,
) -> dict[str, Any]:
    if _is_mock_mode():
        from src.services import mock_client as _mock_client

        return _mock_client.put_crm_calc_config(
            config_key,
            config_value=config_value,
            value_type=value_type,
            description=description,
        )
    enc = quote(config_key, safe="")
    body: dict[str, Any] = {"config_value": config_value}
    if value_type is not None:
        body["value_type"] = value_type
    if description is not None:
        body["description"] = description
    try:
        out = _put_json(_client_cust, f"/api/v1/crm/config/variables/{enc}", body)
        return out if isinstance(out, dict) else {}
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, ValueError):
        return {}
