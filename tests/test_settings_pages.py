"""Smoke tests for mock Settings routing and page modules."""

from __future__ import annotations

import pytest

from src.pages.settings import shell as settings_shell


def test_legacy_redirects_map_to_new_paths():
    for old, new in settings_shell.LEGACY_REDIRECTS.items():
        assert settings_shell._normalize(old) == new


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
    assert settings_shell._normalize(pathname) == expected_key


def test_all_page_builders_return_div():
    for _path, builder in settings_shell._PAGE_BUILDERS.items():
        out = builder(search=None)
        assert out is not None
        assert hasattr(out, "children")
