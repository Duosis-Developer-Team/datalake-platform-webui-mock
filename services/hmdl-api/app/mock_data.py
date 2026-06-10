"""Static fixtures for hmdl-api mock (9/9 DC prod rollout)."""

from __future__ import annotations

from datetime import datetime, timezone

_NOW = datetime.now(timezone.utc).isoformat()
_HUB = "DC13"
_DCS = ["DC11", "DC12", "DC13", "DC14", "DC15", "DC16", "DC17", "AZ11", "ICT11"]

_PROXY_HOSTS = {
    "DC11": [("DC11-NIFI1", "10.6.116.250"), ("DC11-NIFI2", "10.6.116.251")],
    "DC12": [("DC12-NIFI1", "10.35.16.250"), ("DC12-NIFI2", "10.35.16.251")],
    "DC13": [("DC13-NIFI1", "10.134.16.10")],
    "DC14": [("DC14-NIFI1", "10.50.16.250"), ("DC14-NIFI2", "10.50.16.251")],
    "DC15": [("DC15-NIFI1", "10.40.16.250"), ("DC15-NIFI2", "10.40.16.251")],
    "DC16": [("DC16-NIFI1", "10.60.16.250"), ("DC16-NIFI2", "10.60.16.251")],
    "DC17": [("DC17-NIFI1", "10.90.16.250"), ("DC17-NIFI2", "10.90.16.251")],
    "AZ11": [("AZ11-NIFI1", "10.81.18.250"), ("AZ11-NIFI2", "10.81.18.251")],
    "ICT11": [("ICT11-NIFI1", "10.70.16.250"), ("ICT11-NIFI2", "10.70.16.251")],
}


def _nodes() -> list[dict]:
    nodes = []
    for dc in _DCS:
        proxies = [
            {
                "proxy_id": pid,
                "proxy_nifi_host": host,
                "loki_sync_status": "loki_synced",
                "target_count": 42,
                "distributed_count": 42,
                "last_sync_at": _NOW,
                "last_sync_status": "completed",
                "last_run_id": "mock-run-9of9",
            }
            for pid, host in _PROXY_HOSTS[dc]
        ]
        nodes.append(
            {
                "dc_code": dc,
                "role": "hub" if dc == _HUB else "spoke",
                "loki_sync_status": "loki_synced",
                "proxies": proxies,
            }
        )
    return nodes


TOPOLOGY = {
    "hub_dc": _HUB,
    "generated_at": _NOW,
    "last_prod_run_id": "mock-run-9of9",
    "last_prod_run_at": _NOW,
    "nodes": _nodes(),
    "edges": [{"from_dc": _HUB, "to_dc": dc} for dc in _DCS if dc != _HUB],
    "synced_dc_count": 9,
    "total_dc_count": 9,
}

SYNC_SUMMARY = {
    "generated_at": _NOW,
    "last_prod_run_id": "mock-run-9of9",
    "last_prod_run_at": _NOW,
    "synced_dc_count": 9,
    "total_dc_count": 9,
    "synced_proxy_count": 17,
    "total_proxy_count": 17,
    "dc_statuses": {dc: "loki_synced" for dc in _DCS},
}

SAMPLE_TARGETS = {
    "DC13": [
        {
            "entity_name": "nutanix-prism-dc13",
            "ip": "10.128.2.200",
            "proxy_id": "DC13-NIFI1",
            "conf_key": "nutanix",
            "inclusion_category": "not_monitored",
            "platform_status": "not_monitored",
            "last_distributed_at": _NOW,
            "last_check_status": "ok",
            "tenant_name": None,
            "manufacturer": "Nutanix",
            "extra": {"platform_status": "not_monitored"},
        },
        {
            "entity_name": "vcenter-dc13",
            "ip": "10.34.2.10",
            "proxy_id": "DC13-NIFI1",
            "conf_key": "vmware",
            "inclusion_category": "monitored",
            "platform_status": "monitored",
            "last_distributed_at": _NOW,
            "last_check_status": "ok",
            "tenant_name": None,
            "manufacturer": "VMware",
            "extra": None,
        },
    ],
    "DC15": [
        {
            "entity_name": "veeam-dc15-old",
            "ip": "10.40.2.49",
            "proxy_id": "DC15-NIFI1",
            "conf_key": "veeam",
            "inclusion_category": "missing_from_loki",
            "platform_status": None,
            "last_distributed_at": None,
            "last_check_status": None,
            "tenant_name": None,
            "manufacturer": "Veeam",
            "extra": None,
        },
    ],
}

SAMPLE_DIFFS = {
    "DC15": [
        {
            "run_id": "mock-run-9of9",
            "proxy_id": "DC15-NIFI1",
            "conf_key": "veeam",
            "action": "removed",
            "ip": "10.40.2.49",
            "reason": "not in NetBox inventory",
            "created_at": _NOW,
        }
    ],
}
