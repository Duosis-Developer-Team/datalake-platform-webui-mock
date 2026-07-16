"""Mock unique-jobs inventory fixtures."""

from src.services.mock_data import backup as mock_backup


def test_mock_dc_unique_jobs_veeam():
    payload = mock_backup.get_dc_unique_jobs("IST-DC1", "veeam")
    assert payload["vendor"] == "veeam"
    assert payload["totals"]["total_jobs"] >= 1


def test_mock_dc_unique_jobs_table_status_filter():
    payload = mock_backup.get_dc_unique_jobs_table(
        "IST-DC1", "veeam", statuses=["success"]
    )
    assert payload["total"] >= 1
    assert all(str(r.get("status")).lower() == "success" for r in payload["items"])


def test_mock_customer_unique_jobs():
    payload = mock_backup.get_customer_unique_jobs("Acme", "netbackup")
    assert payload["vendor"] == "netbackup"
    assert payload["totals"]["total_jobs"] >= 1
