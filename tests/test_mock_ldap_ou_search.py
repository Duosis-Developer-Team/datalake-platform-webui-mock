"""Mock LDAP OU-style search returns users under matching DN."""

from __future__ import annotations

from src.services import mock_admin_client as m


def test_search_ldap_users_by_name_still_works():
    rows = m.search_ldap_users("aduser")
    assert len(rows) >= 1
    assert any(r["username"] == "aduser1" for r in rows)


def test_search_ldap_users_ou_prefix_filters_by_dn():
    rows = m.search_ldap_users("OU=Developers")
    assert any("Developers" in (r.get("distinguished_name") or "") for r in rows)
