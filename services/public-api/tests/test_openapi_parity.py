"""The mock's /v1/monitoring/* OpenAPI equals the GUI public-api's (Datalake-Platform-GUI e9f39020).

``gui_openapi_monitoring.json`` is the GUI document's monitoring part, written by
``python tests/openapi_monitoring.py gui <GUI checkout> > tests/gui_openapi_monitoring.json``.
The mock is compared with it on every run (paths, parameters, limits, summaries, operationIds,
responses and the schemas they reference). FastAPI's own validation-error schemas
(``FRAMEWORK``) are left out of that check: their shape follows the installed FastAPI version,
not either repo. With ``DLP_GUI_REPO`` set to a GUI checkout, ``test_gui_document_now`` builds
the GUI document from the GUI code and compares it with the mock in full (same FastAPI on both
sides) and with the golden file.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from public_api.main import create_app
from tests.openapi_monitoring import monitoring_part

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.join(HERE, "gui_openapi_monitoring.json")
PATHS = 9
FRAMEWORK = frozenset({"HTTPValidationError", "ValidationError"})


def _golden() -> dict:
    with open(GOLDEN, encoding="utf-8") as f:
        return json.load(f)


class _Upstream:
    def get(self, *a, **k):
        return {}


def _diff(a: dict, b: dict, la: str = "gui", lb: str = "mock", *, skip=FRAMEWORK) -> dict:
    out = {}
    for part in ("paths", "schemas"):
        for k in sorted(set(a[part]) | set(b[part])):
            if part == "schemas" and k in skip:
                continue
            if a[part].get(k) != b[part].get(k):
                out[f"{part}:{k}"] = {la: a[part].get(k), lb: b[part].get(k)}
    return out


def test_golden_has_every_monitoring_route():
    g = _golden()
    assert len(g["paths"]) == PATHS
    assert all(set(v) == {"get"} for v in g["paths"].values())


def _mine() -> dict:
    return monitoring_part(create_app(hmdl_api=_Upstream()).openapi())


def test_mock_openapi_equals_gui():
    diff = _diff(_golden(), _mine())
    assert not diff, json.dumps(diff, ensure_ascii=False, indent=1)


@pytest.mark.skipif(not os.getenv("DLP_GUI_REPO"), reason="DLP_GUI_REPO (a Datalake-Platform-GUI checkout) not set")
def test_gui_document_now():
    out = subprocess.run([sys.executable, os.path.join(HERE, "openapi_monitoring.py"), "gui",
                          os.environ["DLP_GUI_REPO"]], capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    gui = json.loads(out.stdout)
    diff = _diff(gui, _mine(), skip=frozenset())
    assert not diff, json.dumps(diff, ensure_ascii=False, indent=1)
    diff = _diff(gui, _golden(), "gui", "golden")
    assert not diff, json.dumps(diff, ensure_ascii=False, indent=1)
