"""Response shapes of the real hmdl-api (Datalake-Platform-GUI origin/development e9f39020, DLP-020).

Read from the GUI code, not from the mock:
- host row:      services/hmdl-api/app/services/zabbix_sync_runs.py ``host_row``
- snapshot host: services/hmdl-api/app/services/zabbix_sync_snapshot.py ``refresh_now`` / ``mark_latest_complete``
- run group:     zabbix_sync_runs.py ``run_view``; summary keys ``SUMMARY_KEYS``; sections ``_SECTIONS``
- DQ entity:     services/hmdl-api/app/services/dq_state.py ``_FIELDS`` + ``advance`` + ``dq_entities_response``
- DQ run:        dq_state.py ``runs_view``
- automation:    services/hmdl-api/app/services/automation_state.py ``advance_automation``
- AWX job:       services/hmdl-api/app/services/awx_revisions.py ``collect_jobs`` + ``revision_report``

``test_contract_parity_with_gui`` checks these sets against the GUI functions themselves
when a GUI checkout is given (``DLP_GUI_REPO``).
"""

HOST_ROW_KEYS = frozenset({
    "host_key", "entity_type", "entity_type_inferred", "source_device_id", "name", "device_type", "device_role",
    "manufacturer", "dc_code", "site", "location", "tenant", "ownership", "ip", "zabbix_hostid", "zabbix_hostname",
    "status", "operation", "reason", "reason_code", "update_reasons", "field_changes", "tag_changes", "preserved",
    "error_detail", "run_id", "processed_at",
})
SNAPSHOT_HOST_KEYS = HOST_ROW_KEYS | {"status_since", "runs_in_status", "last_seen_at", "last_run_id",
                                      "seen_in_latest_complete_run"}
RUN_VIEW_KEYS = frozenset({"run_id", "entity_type", "started_at", "last_row_at", "state", "complete",
                           "coverage_ratio", "dry_run", "row_count", "counts"})
SUMMARY_KEYS = ("eklendi", "güncellendi", "güncel", "eklenemedi", "güncellenemedi", "atlandı",
                "dry_run_create", "dry_run_update")
SECTIONS = ("failed", "update_failed", "skipped", "added", "updated", "dry_run_create", "dry_run_update")
SNAPSHOT_META_KEYS = frozenset({"generated_at", "status", "stale"})
RESOLUTION_KEYS = frozenset({"inferred_rows", "unresolved_rows", "role_conflicts"})

DQ_FIELDS = ("entity_key", "family", "entity_type", "entity_name", "dc_code", "platform", "metric_source",
             "kok_neden", "kok_neden_aciklama", "last_seen_at", "is_customer")
DQ_ENTITY_KEYS = frozenset(DQ_FIELDS) | {"status_since", "runs_in_status", "last_run_id",
                                         "seen_in_latest_complete_run", "age_hours", "future_timestamp"}
DQ_RUN_KEYS = frozenset({"run_id", "started_at", "finished_at", "status", "entity_count", "coverage_ratio",
                         "complete"})

AUTOMATION_KEYS = frozenset({"key", "label", "cadence", "last_run_at", "age_hours", "warn_hours", "dead_hours",
                             "state", "status_since"})
AWX_JOB_KEYS = frozenset({"job_template", "job_template_name", "project", "project_name", "branch",
                          "last_job_id", "last_job_finished", "last_job_status", "scm_revision", "on_main",
                          "reason"})

STATUSES = ("eklendi", "güncellendi", "güncel", "eklenemedi", "güncellenemedi", "atlandı", "dry_run")
PROBLEM_STATUSES = frozenset({"eklenemedi", "güncellenemedi"})
REASON_CODES = ("ip_missing", "vfw_location_missing", "vfw_vendor_missing", "no_platform_mapping", "no_vfw_mapping",
                "nonstandard_site_code", "template_missing", "no_template_for_device_type", "device_type_not_found",
                "proxy_group_missing", "duplicate_host", "zabbix_api_error", "not_monitored", "other_error", "none")
DQ_PROBLEM_KOK = frozenset({"live_no_data", "stale", "missing", "unavailable"})
DQ_LEAF_TYPES = frozenset({"vm", "ibm_lpar"})
AUTOMATION_STATES = frozenset({"fresh", "stale", "dead", "unknown"})
