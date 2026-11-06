"""One error envelope: ``{"error": {"code", "message", "request_id"}}`` (GUI public_api/errors.py)."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

ERROR_CODES: dict[str, tuple[int, str]] = {
    "unauthorized": (401, "Missing or invalid API key."),
    "forbidden": (403, "This API key does not have the scope for this resource."),
    "not_found": (404, "No such resource."),
    "bad_request": (400, "The request parameters are not valid."),
    "rate_limited": (429, "Too many requests for this API key."),
    "upstream_error": (502, "The data service did not answer. Try again later."),
    "unavailable": (503, "The data is temporarily unavailable. Try again later."),
}


class PublicError(Exception):
    def __init__(self, code: str, message: str | None = None, *, headers: dict | None = None):
        super().__init__(code)
        self.code = code
        self.status = ERROR_CODES[code][0]
        self.message = message or ERROR_CODES[code][1]
        self.headers = headers or {}


def request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None)
    if not rid:
        rid = uuid.uuid4().hex[:16]
        request.state.request_id = rid
    return rid


def error_response(request: Request, code: str, message: str | None = None,
                   headers: dict | None = None) -> JSONResponse:
    status, default = ERROR_CODES[code]
    rid = request_id(request)
    return JSONResponse(status_code=status, headers={"X-Request-ID": rid, **(headers or {})},
                        content={"error": {"code": code, "message": message or default, "request_id": rid}})


def preparing_response(request: Request, retry_after: int = 30) -> JSONResponse:
    rid = request_id(request)
    return JSONResponse(status_code=202, headers={"Retry-After": str(retry_after), "X-Request-ID": rid},
                        content={"status": "preparing", "retry_after": retry_after, "request_id": rid})


ERROR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"error": {"type": "object", "properties": {
        "code": {"type": "string", "enum": list(ERROR_CODES)},
        "message": {"type": "string"},
        "request_id": {"type": "string"}}}},
}
