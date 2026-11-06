"""Key sets at fixed JSON paths, the same walk for the mock and for the real GUI hmdl-api.

A path is a tuple of steps: a key, or ``"*"`` (every list item / every dict value). The
result at a path is the union of the keys of every dict found there, so lists and maps
with varying members compare by shape, not by count.
"""
from __future__ import annotations

# (endpoint, path) pairs; the endpoint is the GET path under /api/v1 used by both sides.
PATHS: dict[str, tuple[tuple, ...]] = {
    "zabbix-sync/summary": ((), ("snapshot",), ("latest_runs", "*"), ("latest_runs", "*", "latest"),
                            ("latest_runs", "*", "latest", "counts"), ("entity_type_resolution",)),
    "zabbix-sync/runs": ((), ("runs", "*"), ("runs", "*", "counts")),
    "zabbix-sync/runs/{run_id}": ((), ("groups", "*"), ("summary",), ("sections",), ("sections", "*", "*")),
    "zabbix-sync/hosts": ((), ("snapshot",), ("hosts", "*")),
    "zabbix-sync/hosts/{host_key}": ((), ("snapshot",), ("host",), ("history", "*")),
    "dq/entities": ((), ("run",), ("entities", "*")),
    "dq/runs": ((), ("runs", "*")),
    "automation/status": ((), ("automations", "*")),
    "automation/awx-revisions": ((), ("jobs", "*")),
}


def _walk(node, path):
    if not path:
        yield node
        return
    step, rest = path[0], path[1:]
    if step == "*":
        items = node.values() if isinstance(node, dict) else node if isinstance(node, list) else ()
        for item in items:
            yield from _walk(item, rest)
    elif isinstance(node, dict) and step in node:
        yield from _walk(node[step], rest)


def keys_at(body, path) -> list[str] | None:
    """Sorted union of dict keys at ``path``; None when nothing (no dict) is there."""
    found = [n for n in _walk(body, tuple(path)) if isinstance(n, dict)]
    if not found:
        return None
    return sorted({k for n in found for k in n})


def shape(endpoint: str, body) -> dict[str, list[str] | None]:
    return {"/".join(p) or ".": keys_at(body, p) for p in PATHS[endpoint]}
