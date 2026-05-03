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
from src.services.mock_data import crm as mock_crm


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


# ---------------------------------------------------------------------------
# CRM operator configuration (customer-api contract)
# ---------------------------------------------------------------------------


def get_crm_discovery_counts() -> list[dict[str, Any]]:
    return mock_crm.list_discovery_counts()


def get_crm_config_thresholds() -> list[dict[str, Any]]:
    return mock_crm.list_thresholds()


def put_crm_config_threshold(
    *,
    resource_type: str,
    dc_code: str,
    sellable_limit_pct: float,
    notes: Optional[str] = None,
    panel_key: Optional[str] = None,
) -> dict[str, Any]:
    return mock_crm.upsert_threshold(
        resource_type=resource_type,
        dc_code=dc_code,
        sellable_limit_pct=sellable_limit_pct,
        notes=notes,
        panel_key=panel_key,
    )


def delete_crm_config_threshold(threshold_id: int) -> dict[str, Any]:
    return mock_crm.delete_threshold(int(threshold_id))


def get_crm_price_overrides() -> list[dict[str, Any]]:
    return mock_crm.list_price_overrides()


def put_crm_price_override(
    productid: str,
    *,
    product_name: Optional[str],
    unit_price_tl: float,
    resource_unit: Optional[str] = None,
    currency: Optional[str] = "TL",
    notes: Optional[str] = None,
) -> dict[str, Any]:
    return mock_crm.upsert_price_override(
        productid=productid,
        product_name=product_name,
        unit_price_tl=float(unit_price_tl),
        resource_unit=resource_unit,
        currency=currency,
        notes=notes,
    )


def delete_crm_price_override(productid: str) -> dict[str, Any]:
    return mock_crm.delete_price_override(productid)


def get_crm_calc_config() -> list[dict[str, Any]]:
    return mock_crm.list_calc_config()


def put_crm_calc_config(
    config_key: str,
    *,
    config_value: str,
    value_type: Optional[str] = None,
    description: Optional[str] = None,
) -> dict[str, Any]:
    return mock_crm.upsert_calc_config(
        config_key=config_key,
        config_value=config_value,
        value_type=value_type,
        description=description,
    )


def get_crm_aliases() -> list[dict[str, Any]]:
    return mock_crm.list_aliases()


def put_crm_alias(
    crm_accountid: str,
    *,
    canonical_customer_key: Optional[str] = None,
    netbox_musteri_value: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    return mock_crm.upsert_alias(
        crm_accountid=crm_accountid,
        canonical_customer_key=canonical_customer_key,
        netbox_musteri_value=netbox_musteri_value,
        notes=notes,
    )


def delete_crm_alias(crm_accountid: str) -> dict[str, Any]:
    return mock_crm.delete_alias(crm_accountid)


def get_crm_service_mapping_pages() -> list[dict[str, Any]]:
    return mock_crm.list_service_mapping_pages()


def get_crm_service_mappings() -> list[dict[str, Any]]:
    return mock_crm.list_service_mappings()


def put_crm_service_mapping(productid: str, *, page_key: str, notes: Optional[str] = None) -> dict[str, Any]:
    return mock_crm.upsert_service_mapping(productid=productid, page_key=page_key, notes=notes)


def delete_crm_service_mapping_override(productid: str) -> dict[str, Any]:
    return mock_crm.delete_service_mapping_override(productid)


# ---------------------------------------------------------------------------
# CRM Sellable Potential (customer-api contract)
# ---------------------------------------------------------------------------


def get_sellable_summary(dc_code: str = "*") -> dict[str, Any]:
    return deepcopy(mock_crm.sellable_summary(dc_code))


def get_sellable_by_panel(dc_code: str = "*", family: Optional[str] = None) -> list[dict[str, Any]]:
    return mock_crm.sellable_by_panel(dc_code, family)


def get_sellable_by_family(dc_code: str = "*") -> list[dict[str, Any]]:
    return mock_crm.sellable_by_family(dc_code)


def get_metric_tags(prefix: Optional[str] = None, scope_type: str = "global", scope_id: str = "*") -> list[dict[str, Any]]:
    return mock_crm.metric_tags(prefix=prefix, scope_type=scope_type, scope_id=scope_id)


def get_metric_snapshots(metric_key: str, hours: int = 720, scope_id: str = "*") -> list[dict[str, Any]]:
    return mock_crm.metric_snapshots(metric_key, hours=hours, scope_id=scope_id)


def get_panel_definitions() -> list[dict[str, Any]]:
    return mock_crm.list_panel_definitions()


def put_panel_definition(
    panel_key: str,
    *,
    label: str,
    family: str,
    resource_kind: str,
    display_unit: str = "GB",
    sort_order: int = 100,
    enabled: bool = True,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    return mock_crm.upsert_panel_definition(
        panel_key,
        label=label,
        family=family,
        resource_kind=resource_kind,
        display_unit=display_unit,
        sort_order=sort_order,
        enabled=enabled,
        notes=notes,
    )


def get_panel_infra_source(panel_key: str, dc_code: str = "*") -> dict[str, Any]:
    return deepcopy(mock_crm.get_panel_infra_source(panel_key, dc_code))


def put_panel_infra_source(
    panel_key: str,
    dc_code: str = "*",
    *,
    source_table: Optional[str] = None,
    total_column: Optional[str] = None,
    total_unit: Optional[str] = None,
    allocated_table: Optional[str] = None,
    allocated_column: Optional[str] = None,
    allocated_unit: Optional[str] = None,
    filter_clause: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    return mock_crm.upsert_panel_infra_source(
        panel_key,
        dc_code,
        source_table=source_table,
        total_column=total_column,
        total_unit=total_unit,
        allocated_table=allocated_table,
        allocated_column=allocated_column,
        allocated_unit=allocated_unit,
        filter_clause=filter_clause,
        notes=notes,
    )


def get_resource_ratios() -> list[dict[str, Any]]:
    return mock_crm.list_resource_ratios()


def put_resource_ratio(
    family: str,
    *,
    dc_code: str = "*",
    cpu_per_unit: float = 1.0,
    ram_gb_per_unit: float = 8.0,
    storage_gb_per_unit: float = 100.0,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    return mock_crm.upsert_resource_ratio(
        family,
        dc_code=dc_code,
        cpu_per_unit=cpu_per_unit,
        ram_gb_per_unit=ram_gb_per_unit,
        storage_gb_per_unit=storage_gb_per_unit,
        notes=notes,
    )


def get_unit_conversions() -> list[dict[str, Any]]:
    return mock_crm.list_unit_conversions()


def put_unit_conversion(
    from_unit: str,
    to_unit: str,
    *,
    factor: float,
    operation: str = "divide",
    ceil_result: bool = False,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    return mock_crm.upsert_unit_conversion(
        from_unit,
        to_unit,
        factor=factor,
        operation=operation,
        ceil_result=ceil_result,
        notes=notes,
    )


def delete_unit_conversion(from_unit: str, to_unit: str) -> dict[str, Any]:
    return mock_crm.delete_unit_conversion(from_unit, to_unit)
