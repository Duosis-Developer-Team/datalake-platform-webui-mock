"""Mock VMware classic / Nutanix hyperconverged cluster lists and aggregated metrics."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from src.services.mock_data.datacenters import get_dc_detail


def _norm(dc_code: str) -> str:
    return (dc_code or "").strip().upper()


_CLASSIC_CLUSTERS: dict[str, list[str]] = {
    "IST-DC1": ["IST-CLU-A", "IST-CLU-B", "IST-CLU-C"],
    "ANK-DC1": ["ANK-CLU-01", "ANK-CLU-02"],
    "IZM-DC1": [],
    "FRA-DC1": ["FRA-CLU-EU1", "FRA-CLU-EU2"],
}

_HYPERCONV_CLUSTERS: dict[str, list[str]] = {
    "IST-DC1": ["IST-NTX-01", "IST-NTX-02"],
    "ANK-DC1": [],
    "IZM-DC1": ["IZM-NTX-A", "IZM-NTX-B", "IZM-NTX-C"],
    "FRA-DC1": ["FRA-NTX-01"],
}


def get_classic_cluster_list(dc_code: str, _tr: dict | None = None) -> list[str]:
    return list(_CLASSIC_CLUSTERS.get(_norm(dc_code), []))


def get_hyperconv_cluster_list(dc_code: str, _tr: dict | None = None) -> list[str]:
    return list(_HYPERCONV_CLUSTERS.get(_norm(dc_code), []))


def _filter_by_clusters(payload: dict[str, Any], selected: Optional[list[str]], cluster_keys: list[str]) -> dict[str, Any]:
    if not selected:
        return deepcopy(payload)
    sel = set(selected)
    # Proportional shrink for demo when subset selected
    n = max(1, len(sel))
    total = max(1, len(cluster_keys))
    ratio = n / total
    out = deepcopy(payload)
    for k in ("hosts", "vms"):
        if k in out:
            out[k] = max(1, int(float(out[k]) * ratio))
    for k in ("cpu_cap", "cpu_used", "mem_cap", "mem_used", "stor_cap", "stor_used"):
        if k in out:
            out[k] = float(out[k]) * ratio
    return out


def get_classic_metrics_filtered(
    dc_code: str, selected_clusters: Optional[list[str]], _tr: dict | None = None
) -> dict[str, Any]:
    key = _norm(dc_code)
    base = (get_dc_detail(key) or {}).get("classic") or {}
    if not base:
        return {}
    clusters = _CLASSIC_CLUSTERS.get(key, [])
    return _filter_by_clusters(base, selected_clusters, clusters)


def get_hyperconv_metrics_filtered(
    dc_code: str, selected_clusters: Optional[list[str]], _tr: dict | None = None
) -> dict[str, Any]:
    key = _norm(dc_code)
    base = (get_dc_detail(key) or {}).get("hyperconv") or {}
    if not base:
        return {}
    clusters = _HYPERCONV_CLUSTERS.get(key, [])
    return _filter_by_clusters(base, selected_clusters, clusters)
