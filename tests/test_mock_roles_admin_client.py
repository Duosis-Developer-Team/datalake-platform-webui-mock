"""``src/services/admin_client.py`` role functions: the path the mock pages really use (DLP-023 K16).

API branch: the HTTP call is patched at ``httpx`` level so ``_post``/``_get`` and the status mapping
run for real. Local branch: delegation to ``settings_crud``.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from src.auth.role_errors import RoleNameTaken
from src.services import admin_client as ac


def _resp(status: int, body=None, method="POST", url="http://admin-api/api/v1/roles") -> httpx.Response:
    return httpx.Response(status, json=body, request=httpx.Request(method, url))


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setattr(ac, "_USE_API", True)
    monkeypatch.setattr(ac, "_ADMIN_API_URL", "http://admin-api")


# --- create_role: API branch -----------------------------------------------------------------


def test_api_create_role_posts_payload_and_returns_json(api):
    ok = {"id": 7, "name": "Ops", "copied_rows": 2}
    with patch.object(httpx, "post", return_value=_resp(200, ok)) as post:
        assert ac.create_role("Ops", "d", 3) == ok
    assert post.call_args.args[0] == "http://admin-api/api/v1/roles"
    assert post.call_args.kwargs["json"] == {"name": "Ops", "description": "d", "copy_from_role_id": 3}


def test_api_create_role_409_is_role_name_taken(api):
    with patch.object(httpx, "post", return_value=_resp(409, {"detail": "Role name already exists"})):
        with pytest.raises(RoleNameTaken, match="already exists"):
            ac.create_role("Admin", None, None)


def test_api_create_role_422_string_detail_is_value_error(api):
    with patch.object(httpx, "post", return_value=_resp(422, {"detail": "Name is required"})):
        with pytest.raises(ValueError, match="Name is required"):
            ac.create_role(" ", None, None)


def test_api_create_role_422_list_detail_is_value_error_with_joined_messages(api):
    body = {"detail": [{"loc": ["body", "name"], "msg": "String should have at most 100 characters"},
                       {"loc": ["body", "x"], "msg": "second problem"}]}
    with patch.object(httpx, "post", return_value=_resp(422, body)):
        with pytest.raises(ValueError) as ei:
            ac.create_role("q" * 101, None, None)
    assert str(ei.value) == "String should have at most 100 characters; second problem"


def test_api_create_role_404_is_lookup_error(api):
    with patch.object(httpx, "post", return_value=_resp(404, {"detail": "Source role not found"})):
        with pytest.raises(LookupError, match="Source role not found"):
            ac.create_role("X", None, 999)


def test_api_create_role_unmapped_status_propagates_http_error(api):
    with patch.object(httpx, "post", return_value=_resp(500, {"detail": "boom"})):
        with pytest.raises(httpx.HTTPStatusError):
            ac.create_role("X", None, None)


def test_api_create_role_non_json_error_body_still_maps(api):
    resp = httpx.Response(409, text="conflict", request=httpx.Request("POST", "http://admin-api/api/v1/roles"))
    with patch.object(httpx, "post", return_value=resp):
        with pytest.raises(RoleNameTaken, match="conflict"):
            ac.create_role("Admin", None, None)


# --- role_usage / role_usage_counts: API branch -----------------------------------------------


def test_api_role_usage_gets_and_returns_json(api):
    body = {"role": {"id": 4, "name": "R", "is_system": False}, "users": [], "teams": [],
            "ldap_mappings": [], "counts": {"users": 0, "teams": 0, "team_members": 0, "ldap_mappings": 0}}
    with patch.object(httpx, "get", return_value=_resp(200, body, "GET")) as get:
        assert ac.role_usage(4) == body
    assert get.call_args.args[0] == "http://admin-api/api/v1/roles/4/usage"


def test_api_role_usage_404_is_lookup_error(api):
    with patch.object(httpx, "get", return_value=_resp(404, {"detail": "Role not found"}, "GET")):
        with pytest.raises(LookupError, match="Role not found"):
            ac.role_usage(999)


def test_api_role_usage_other_error_propagates(api):
    with patch.object(httpx, "get", return_value=_resp(500, {"detail": "boom"}, "GET")):
        with pytest.raises(httpx.HTTPStatusError):
            ac.role_usage(1)


def test_api_role_usage_counts_converts_json_string_keys_to_int(api):
    zero = {"users": 0, "teams": 0, "team_members": 0, "ldap_mappings": 0}
    body = {"1": zero, "12": {**zero, "users": 3}}
    with patch.object(httpx, "get", return_value=_resp(200, body, "GET")) as get:
        out = ac.role_usage_counts()
    assert get.call_args.args[0] == "http://admin-api/api/v1/roles/usage-counts"
    assert out == {1: zero, 12: {**zero, "users": 3}}
    assert all(isinstance(k, int) for k in out)


def test_api_role_usage_counts_empty_body_is_empty_dict(api):
    with patch.object(httpx, "get", return_value=_resp(200, {}, "GET")):
        assert ac.role_usage_counts() == {}


# --- local branch: delegation ------------------------------------------------------------------


def test_local_branch_delegates_to_settings_crud(monkeypatch):
    monkeypatch.setattr(ac, "_USE_API", False)
    with patch("src.auth.settings_crud.create_role", return_value={"id": 1, "name": "N", "copied_rows": 0}) as c:
        assert ac.create_role("N", "d", 2) == {"id": 1, "name": "N", "copied_rows": 0}
    c.assert_called_once_with("N", "d", 2)
    with patch("src.auth.settings_crud.role_usage", return_value={"x": 1}) as u:
        assert ac.role_usage(5) == {"x": 1}
    u.assert_called_once_with(5)
    with patch("src.auth.settings_crud.role_usage_counts", return_value={1: {}}) as n:
        assert ac.role_usage_counts() == {1: {}}
    n.assert_called_once_with()


def test_local_branch_does_not_touch_http(monkeypatch):
    monkeypatch.setattr(ac, "_USE_API", False)
    with patch.object(httpx, "post", side_effect=AssertionError("no HTTP on the local path")), \
         patch.object(httpx, "get", side_effect=AssertionError("no HTTP on the local path")), \
         patch("src.auth.settings_crud.create_role", return_value={}), \
         patch("src.auth.settings_crud.role_usage", return_value={}), \
         patch("src.auth.settings_crud.role_usage_counts", return_value={}):
        ac.create_role("N", None, None)
        ac.role_usage(1)
        ac.role_usage_counts()
