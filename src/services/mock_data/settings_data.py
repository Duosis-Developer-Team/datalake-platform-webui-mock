"""Static data for mock Settings UI (no auth database)."""

from __future__ import annotations

MOCK_USERS = [
    {"username": "admin", "display_name": "Admin User", "email": "admin@example.com", "source": "local", "is_active": True, "roles": "Admin"},
    {"username": "jdoe", "display_name": "Jane Doe", "email": "jdoe@example.com", "source": "ldap", "is_active": True, "roles": "Viewer"},
]

MOCK_TEAMS = [
    {"id": 1, "name": "Data Analysts", "member_count": 12, "created_by": "admin"},
    {"id": 2, "name": "Data Engineering", "member_count": 8, "created_by": "jdoe"},
]

MOCK_AUDIT = [
    {"created_at": "2025-04-12T10:00:00", "username": "admin", "action": "login", "detail": "session", "ip_address": "10.0.0.1"},
    {"created_at": "2025-04-12T09:30:00", "username": "jdoe", "action": "settings_view", "detail": "mock", "ip_address": "10.0.0.2"},
]

MOCK_SLA_ROWS = [
    {"group_name": "DC-East", "sla_percentage": 99.95, "status": "ok"},
    {"group_name": "DC-West", "sla_percentage": 99.80, "status": "ok"},
]
