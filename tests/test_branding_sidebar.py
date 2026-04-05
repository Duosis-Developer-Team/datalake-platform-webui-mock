"""Sidebar brand title from APP_BRAND_TITLE / defaults."""

import pytest

from src.components.sidebar import create_sidebar_nav
from src.utils import branding


def _brand_span_text(nav) -> str:
    brand_div = nav.children[0]
    span = brand_div.children[1]
    ch = span.children
    return ch if isinstance(ch, str) else str(ch)


def test_get_brand_title_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_BRAND_TITLE", raising=False)
    assert branding.get_brand_title() == "Datalake WebUI"


def test_get_brand_title_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_BRAND_TITLE", "Acme Corp Demo")
    assert branding.get_brand_title() == "Acme Corp Demo"


def test_get_brand_title_strips_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_BRAND_TITLE", "  Trimmed  ")
    assert branding.get_brand_title() == "Trimmed"


def test_sidebar_shows_default_brand(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_BRAND_TITLE", raising=False)
    nav = create_sidebar_nav("/")
    assert _brand_span_text(nav) == "Datalake WebUI"


def test_sidebar_shows_custom_brand(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_BRAND_TITLE", "Custom Brand")
    nav = create_sidebar_nav("/")
    assert _brand_span_text(nav) == "Custom Brand"
