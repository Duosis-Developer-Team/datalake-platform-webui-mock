"""Smoke tests for mock Settings routing and page modules."""

from __future__ import annotations

import pytest

from src.pages.settings import shell as settings_shell


def test_legacy_redirects_map_to_new_paths():
    for old, new in settings_shell.LEGACY_REDIRECTS.items():
        assert settings_shell._normalize_path(old) == new


@pytest.mark.parametrize(
    "pathname,expected_key",
    [
        ("/settings", "/settings"),
        ("/settings/iam/users", "/settings/iam/users"),
        ("/settings/integrations/auranotify", "/settings/integrations/auranotify"),
        ("/settings/users", "/settings/iam/users"),
    ],
)
def test_normalize_resolves_known_routes(pathname: str, expected_key: str):
    assert settings_shell._normalize_path(pathname) == expected_key


def test_page_builders_are_permission_tuples_with_callables():
    for path, entry in settings_shell._PAGE_BUILDERS.items():
        assert isinstance(path, str)
        assert isinstance(entry, tuple) and len(entry) == 2
        code, builder = entry
        assert isinstance(code, str)
        assert callable(builder)
