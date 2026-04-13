"""
HTTP-free API twin of api_client for APP_MODE=mock.

All functions mirror src.services.api_client public signatures and return deep copies
of static datasets from src.services.mock_data.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from src.services.mock_data import backup as mock_backup
from src.services.mock_data import customers as mock_customers
from src.services.mock_data import datacenters as mock_dc
from src.services.mock_data import network as mock_net
from src.services.mock_data import physical_inventory as mock_phys
from src.services.mock_data import sla as mock_sla
from src.services.mock_data import storage as mock_storage
from src.services.mock_data import virtualization as mock_virt


def get_global_dashboard(tr: Optional[dict]) -> dict:
    return deepcopy(mock_dc.build_global_dashboard(tr))


def get_all_datacenters_summary(tr: Optional[dict]) -> list[dict]:
    return mock_dc.get_all_datacenters_summary(tr)


def get_dc_details(dc_id: str, tr: Optional[dict]) -> dict:
    return mock_dc.get_dc_detail(dc_id, tr)


def get_dc_racks(dc_id: str) -> dict:
    return mock_dc.get_dc_racks(dc_id)


def get_rack_devices(dc_id: str, rack_name: str) -> dict:
    return mock_dc.get_rack_devices(dc_id, rack_name)


def get_customer_list() -> list[str]:
    return mock_customers.get_customer_list()


def get_customer_resources(name: str, tr: Optional[dict]) -> dict:
    return mock_customers.get_customer_resources(name, tr)


def execute_registered_query(key: str, params: str) -> dict:
    _ = params
    return {
        "result_type": "table",
        "columns": ["query_key", "mock_row", "note"],
        "data": [
            [key, 1, "Mock mode: no query-api call"],
            [key, 2, "Replace APP_MODE to hit real services"],
        ],
    }


def get_sla_by_dc(tr: Optional[dict]) -> dict[str, dict]:
    return deepcopy(mock_dc.get_sla_by_dc_payload(tr))


def get_dc_s3_pools(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_storage.get_dc_s3_pools(dc_code, tr)


def get_customer_s3_vaults(customer_name: str, tr: Optional[dict]) -> dict:
    return mock_customers.get_customer_s3_vaults(customer_name, tr)


def get_dc_netbackup_pools(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_backup.get_dc_netbackup_pools(dc_code, tr)


def get_dc_zerto_sites(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_backup.get_dc_zerto_sites(dc_code, tr)


def get_dc_veeam_repos(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_backup.get_dc_veeam_repos(dc_code, tr)


def get_classic_cluster_list(dc_code: str, tr: Optional[dict]) -> list[str]:
    return mock_virt.get_classic_cluster_list(dc_code, tr)


def get_hyperconv_cluster_list(dc_code: str, tr: Optional[dict]) -> list[str]:
    return mock_virt.get_hyperconv_cluster_list(dc_code, tr)


def get_classic_metrics_filtered(
    dc_code: str, selected_clusters: Optional[list[str]], tr: Optional[dict]
) -> dict:
    return mock_virt.get_classic_metrics_filtered(dc_code, selected_clusters, tr)


def get_hyperconv_metrics_filtered(
    dc_code: str, selected_clusters: Optional[list[str]], tr: Optional[dict]
) -> dict:
    return mock_virt.get_hyperconv_metrics_filtered(dc_code, selected_clusters, tr)


def get_physical_inventory_dc(dc_name: str) -> dict:
    return mock_phys.get_physical_inventory_dc(dc_name)


def get_physical_inventory_overview_by_role() -> list[dict]:
    return mock_phys.get_physical_inventory_overview_by_role()


def get_physical_inventory_overview_manufacturer(role: str) -> list[dict]:
    return mock_phys.get_physical_inventory_overview_manufacturer(role)


def get_physical_inventory_overview_location(role: str, manufacturer: str) -> list[dict]:
    return mock_phys.get_physical_inventory_overview_location(role, manufacturer)


def get_physical_inventory_customer() -> list[dict]:
    return mock_phys.get_physical_inventory_customer()


def get_dc_san_switches(dc_code: str, tr: Optional[dict]) -> list[str]:
    return mock_storage.get_dc_san_switches(dc_code, tr)


def get_dc_san_port_usage(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_storage.get_dc_san_port_usage(dc_code, tr)


def get_dc_san_health(dc_code: str, tr: Optional[dict]) -> list[dict]:
    return mock_storage.get_dc_san_health(dc_code, tr)


def get_dc_san_traffic_trend(dc_code: str, tr: Optional[dict]) -> list[dict]:
    return mock_storage.get_dc_san_traffic_trend(dc_code, tr)


def get_dc_san_bottleneck(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_storage.get_dc_san_bottleneck(dc_code, tr)


def get_dc_storage_capacity(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_storage.get_dc_storage_capacity(dc_code, tr)


def get_dc_storage_performance(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_storage.get_dc_storage_performance(dc_code, tr)


def get_dc_network_filters(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_net.get_dc_network_filters(dc_code, tr)


def get_dc_network_port_summary(
    dc_code: str,
    tr: Optional[dict],
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
) -> dict:
    return mock_net.get_dc_network_port_summary(dc_code, tr, manufacturer, device_role, device_name)


def get_dc_network_95th_percentile(
    dc_code: str,
    tr: Optional[dict],
    top_n: int = 20,
    manufacturer: Optional[str] = None,
    device_role: Optional[str] = None,
    device_name: Optional[str] = None,
) -> dict:
    return mock_net.get_dc_network_95th_percentile(
        dc_code, tr, top_n, manufacturer, device_role, device_name
    )


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
    return mock_net.get_dc_network_interface_table(
        dc_code, tr, page, page_size, search, manufacturer, device_role, device_name
    )


def get_dc_zabbix_storage_capacity(dc_code: str, tr: Optional[dict], host: Optional[str] = None) -> dict:
    return mock_storage.get_dc_zabbix_storage_capacity(dc_code, tr, host)


def get_dc_zabbix_storage_trend(dc_code: str, tr: Optional[dict], host: Optional[str] = None) -> dict:
    return mock_storage.get_dc_zabbix_storage_trend(dc_code, tr, host)


def get_dc_zabbix_storage_devices(dc_code: str, tr: Optional[dict]) -> list[dict]:
    return mock_storage.get_dc_zabbix_storage_devices(dc_code, tr)


def get_dc_zabbix_disk_list(dc_code: str, tr: Optional[dict], host: Optional[str] = None) -> dict:
    return mock_storage.get_dc_zabbix_disk_list(dc_code, tr, host)


def get_dc_zabbix_disk_trend(
    dc_code: str,
    tr: Optional[dict],
    host: Optional[str] = None,
    disk_name: Optional[str] = None,
) -> dict:
    return mock_storage.get_dc_zabbix_disk_trend(dc_code, tr, host, disk_name)


def get_dc_zabbix_disk_health(dc_code: str, tr: Optional[dict]) -> dict:
    return mock_storage.get_dc_zabbix_disk_health(dc_code, tr)


def get_customer_availability_bundle(customer_name: str, tr: Optional[dict]) -> dict[str, Any]:
    return mock_customers.get_customer_availability_bundle(customer_name, tr)


def get_dc_availability_sla_item(
    dc_code: str, dc_display_name: str, tr: Optional[dict]
) -> Optional[dict[str, Any]]:
    return mock_sla.get_dc_availability_sla_item(dc_code, dc_display_name, tr)
