"""Scopes and key format of the real public API (GUI shared/public_api/keys.py, e9f39020), with fixed demo keys.

The real service reads ``gui_public_api_key`` from the WebUI DB; the mock has two keys in
code instead. They are demo values for local UI work and say so in the secret part; they
open nothing outside this mock.
"""
from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Optional

KEY_RE = re.compile(r"^dlp_([0-9a-f]{8})_([A-Za-z0-9_-]{43})$")

SCOPE_CUSTOMER = "customer:read"
SCOPE_CUSTOMERS = "customers:read"
SCOPE_DATACENTERS = "datacenters:read"
SCOPE_MONITORING = "monitoring:read"    # HMDL sync / DQ / otomasyon son durumu (DLP-020)
SCOPES = (SCOPE_CUSTOMER, SCOPE_CUSTOMERS, SCOPE_DATACENTERS, SCOPE_MONITORING)

MONITORING_KEY = "dlp_0000a001_mock-monitoring-read-demo-key-not-a-secret-"
DATACENTERS_KEY = "dlp_0000a002_mock-datacenters-read-demo-key-not-a-secret"


@dataclass(frozen=True)
class Caller:
    key_id: int
    prefix: str
    name: str
    scopes: frozenset[str]
    crm_accountid: Optional[str]


def _hash(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


# prefix -> the row the real service would read (key_hash, never the key itself)
_ROWS = {
    "0000a001": {"id": 1, "name": "Mock monitoring", "key_hash": _hash(MONITORING_KEY),
                 "scopes": (SCOPE_MONITORING,), "crm_accountid": None},
    "0000a002": {"id": 2, "name": "Mock data centers", "key_hash": _hash(DATACENTERS_KEY),
                 "scopes": (SCOPE_DATACENTERS,), "crm_accountid": None},
}


def lookup(plaintext: Optional[str]) -> Optional[Caller]:
    """The caller of a key, or None: unknown format, unknown prefix or wrong secret (all 401)."""
    m = KEY_RE.match((plaintext or "").strip())
    if not m:
        return None
    row = _ROWS.get(m.group(1))
    if not row or not hmac.compare_digest(_hash(plaintext.strip()), row["key_hash"]):
        return None
    return Caller(key_id=row["id"], prefix=m.group(1), name=row["name"], scopes=frozenset(row["scopes"]),
                  crm_accountid=row["crm_accountid"])


def key_from_headers(headers) -> Optional[str]:
    auth = headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return (headers.get("x-api-key") or "").strip() or None
