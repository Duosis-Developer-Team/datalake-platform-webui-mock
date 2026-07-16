"""Mock coverage for Zerto license endpoint used by Backup & Replication IA."""
from __future__ import annotations

from src.services.mock_data.backup import get_dc_zerto_license


def test_zerto_license_present_for_ist():
    payload = get_dc_zerto_license("IST-DC1")
    assert payload["has_license"] is True
    assert payload["summary"]["license_type"] == "CloudO2M"
    assert payload["summary"]["protected_vms_in_dc"] == 400


def test_zerto_license_empty_for_unknown_dc():
    payload = get_dc_zerto_license("UNKNOWN-DC")
    assert payload["has_license"] is False
    assert payload["licenses"] == []
