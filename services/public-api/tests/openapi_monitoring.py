"""The /v1/monitoring/* part of a public-api OpenAPI document, printed as JSON (run in a subprocess).

    python openapi_monitoring.py gui  <Datalake-Platform-GUI checkout root>
    python openapi_monitoring.py mock <this repo's services/public-api>

Prints ``{"paths": {...}, "schemas": {...}}``: every ``/v1/monitoring/`` path object and every
``#/components/schemas`` entry those paths reference (transitively). The GUI app is built with
stub stores and upstreams (nothing is called); only its OpenAPI document is read.
"""
from __future__ import annotations

import json
import os
import sys

PREFIX = "/v1/monitoring/"
_REF = "#/components/schemas/"


def _refs(node, out: set) -> None:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(_REF):
            out.add(ref[len(_REF):])
        for v in node.values():
            _refs(v, out)
    elif isinstance(node, list):
        for v in node:
            _refs(v, out)


def monitoring_part(schema: dict) -> dict:
    paths = {p: v for p, v in schema["paths"].items() if p.startswith(PREFIX)}
    components = schema.get("components", {}).get("schemas", {})
    names: set = set()
    _refs(paths, names)
    todo = set(names)
    while todo:
        found: set = set()
        _refs({n: components.get(n) for n in todo}, found)
        todo = found - names
        names |= found
    return {"paths": paths, "schemas": {n: components.get(n) for n in sorted(names)}}


class _Upstream:
    def get(self, *a, **k):
        return {}


class _Store:
    def authenticate(self, presented):
        return None


class _Limiter:
    def check(self, key):
        return True, 0


def _gui_app(root: str):
    sys.path[:0] = [os.path.join(root, "services", "public-api"), root]
    from public_api.main import create_app

    return create_app(store=_Store(), limiter=_Limiter(), customer_api=_Upstream(), datacenter_api=_Upstream(),
                      hmdl_api=_Upstream())


def _mock_app(service_dir: str):
    sys.path[:0] = [service_dir]
    from public_api.main import create_app

    return create_app(hmdl_api=_Upstream())


if __name__ == "__main__":
    kind, root = sys.argv[1], os.path.abspath(sys.argv[2])
    app = {"gui": _gui_app, "mock": _mock_app}[kind](root)
    print(json.dumps(monitoring_part(app.openapi()), ensure_ascii=False, sort_keys=True, indent=1))
