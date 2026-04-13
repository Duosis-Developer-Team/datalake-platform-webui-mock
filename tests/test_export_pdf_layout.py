"""PDF export clientside wiring and assets."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture(scope="module")
def app_module():
    import app as app_module

    return app_module


def test_pdf_export_clientside_callback_registered(app_module: Any) -> None:
    """PDF triggers live in page content (not root layout); clientside wiring must exist."""
    cmap = getattr(app_module.app, "callback_map", {}) or {}
    keys = [str(k) for k in cmap.keys()]
    assert any("export-pdf-clientside-dummy" in k for k in keys), "expected PDF clientside output in callback_map"


def test_pdf_export_asset_exists() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    p = root / "assets" / "pdf_export_trigger.js"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "data-pdf-target" in text
