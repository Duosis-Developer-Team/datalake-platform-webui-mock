"""Internal call and the public form of its answer (GUI public_api/upstream.py + shared/public_api/scrub.py).

- 200: the body goes through ``scrub`` (money and internal keys removed).
- 202 (internal "preparing"): 202 + ``Retry-After``.
- 503: ``unavailable`` + ``Retry-After``. 404 / 400 / 422: ``not_found`` / ``bad_request``.
  Anything else and connection errors: ``upstream_error``. The internal body never leaks.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Mapping, Optional

import httpx

from public_api.errors import PublicError

logger = logging.getLogger(__name__)

HMDL_API_URL = os.getenv("HMDL_API_URL", "http://hmdl-api:8000").rstrip("/")
UPSTREAM_TIMEOUT_S = float(os.getenv("PUBLIC_API_UPSTREAM_TIMEOUT_S", "60"))

_MONEY = re.compile(
    r"(^|_)(tl|try|eur|usd)$|price|revenue|order_value|amount|cost|sellable|valuation|"
    r"discount|overage_loss|entitled|billing|invoice|^currency$|_currency$",
    re.IGNORECASE,
)
_INTERNAL = frozenset({
    "held_by", "lock_wait_s", "last_error", "filter_clause", "source_table", "table_name",
    "sql", "query", "traceback", "infra_patterns", "patterns", "mapping_rules",
})


def is_hidden(key: str) -> bool:
    k = str(key)
    return k in _INTERNAL or bool(_MONEY.search(k))


def scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if not is_hidden(k)}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


class Preparing(Exception):
    def __init__(self, retry_after: int = 30):
        super().__init__("preparing")
        self.retry_after = retry_after


class Upstream:
    def __init__(self, base_url: str, client: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(base_url=self.base_url, timeout=UPSTREAM_TIMEOUT_S)

    def get(self, path: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        clean = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        try:
            r = self._client.get(path, params=clean)
        except httpx.HTTPError as exc:
            logger.warning("public api mock: %s%s failed: %s", self.base_url, path, exc)
            raise PublicError("upstream_error") from exc
        if r.status_code == 202:
            raise Preparing(_retry_after(r.headers.get("retry-after"), 30))
        if r.status_code == 503:
            raise PublicError("unavailable", headers={"Retry-After": str(_retry_after(r.headers.get("retry-after"), 60))})
        if r.status_code == 404:
            raise PublicError("not_found")
        if r.status_code in (400, 422):
            raise PublicError("bad_request")
        if r.status_code != 200:
            raise PublicError("upstream_error")
        try:
            return scrub(r.json())
        except ValueError as exc:
            raise PublicError("upstream_error") from exc


def _retry_after(value: Optional[str], default: int) -> int:
    try:
        return max(1, int(float(value))) if value else default
    except (TypeError, ValueError):
        return default
