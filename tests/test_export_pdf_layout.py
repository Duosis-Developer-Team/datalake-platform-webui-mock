"""Ensure PDF clientside callback inputs always exist in the app layout tree."""

from __future__ import annotations

from typing import Any

import pytest

_PDF_EXPORT_IDS = frozenset(
    {
        "home-export-pdf",
        "datacenters-export-pdf",
        "dc-export-pdf",
        "global-export-pdf",
        "customer-export-pdf",
        "qe-export-pdf",
    }
)


def _normalize_node(obj: Any) -> Any:
    """Turn Dash components in a to_plotly_json() tree into plain dicts."""
    if hasattr(obj, "to_plotly_json") and callable(obj.to_plotly_json):
        return obj.to_plotly_json()
    return obj


def _walk_collect_string_ids(obj: Any, out: set[str]) -> None:
    obj = _normalize_node(obj)
    if obj is None:
        return
    if isinstance(obj, dict):
        props = obj.get("props")
        if isinstance(props, dict):
            cid = props.get("id")
            if isinstance(cid, str):
                out.add(cid)
            _walk_collect_string_ids(props.get("children"), out)
        for k, v in obj.items():
            if k != "props":
                _walk_collect_string_ids(v, out)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _walk_collect_string_ids(item, out)


@pytest.fixture(scope="module")
def app_layout_root() -> Any:
    import app as app_module

    return app_module.app.layout.to_plotly_json()


def test_pdf_export_hidden_button_ids_in_layout(app_layout_root: Any) -> None:
    ids: set[str] = set()
    _walk_collect_string_ids(app_layout_root, ids)
    missing = _PDF_EXPORT_IDS - ids
    assert not missing, f"Layout missing PDF trigger ids: {sorted(missing)}"


def test_pdf_export_asset_exists() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    p = root / "assets" / "pdf_export_trigger.js"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "data-pdf-target" in text
