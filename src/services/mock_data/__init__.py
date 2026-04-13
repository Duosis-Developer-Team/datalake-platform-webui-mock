from __future__ import annotations
"""Static mock datasets for APP_MODE=mock (demo / sales UI)."""

from src.services.mock_data.datacenters import (
    MOCK_DC_CODES,
    build_global_dashboard,
    get_all_datacenters_summary,
    get_dc_detail,
    get_sla_by_dc_payload,
)
from src.services.mock_data.customers import MOCK_CUSTOMER_NAMES

__all__ = [
    "MOCK_DC_CODES",
    "MOCK_CUSTOMER_NAMES",
    "build_global_dashboard",
    "get_all_datacenters_summary",
    "get_dc_detail",
    "get_sla_by_dc_payload",
]
