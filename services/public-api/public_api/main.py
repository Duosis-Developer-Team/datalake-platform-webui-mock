"""Mock of the Bulutistan Datalake public API: the /v1/monitoring/* routes (DLP-020).

Mirrors Datalake-Platform-GUI services/public-api (origin/development e9f39020): same paths,
parameters, scope (``monitoring:read``), error envelope and 202/Retry-After answers; the data
comes from the hmdl-api mock over HTTP (``HMDL_API_URL``), as the real service reads hmdl-api.
Not here: the customer and data-center routes, the WebUI DB key table (two demo keys in
``mock_keys``) and the Redis rate limit (no 429).

    uvicorn public_api.main:app --port 8000
"""
from __future__ import annotations

import logging
from typing import Callable, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException

from public_api import mock_keys
from public_api.errors import ERROR_SCHEMA, PublicError, error_response, preparing_response, request_id
from public_api.upstream import HMDL_API_URL, Preparing, Upstream

logging.basicConfig(level=logging.INFO)

API_VERSION = "1.0.0"
DESCRIPTION = """
Read-only access to Bulutistan Datalake data. **Mock**: only `/v1/monitoring/…` is served here.

**Authentication.** Send your API key in `Authorization: Bearer <key>` (or `X-API-Key: <key>`).
A key carries scopes: `customer:read` (one customer, the one the key belongs to),
`customers:read` (every customer), `datacenters:read` (data-center detail) and/or
`monitoring:read` (Loki→Zabbix sync outputs, data-quality and automation state under `/v1/monitoring/…`;
no severities — the monitoring template sets them).

**Errors.** Every error is `{"error": {"code", "message", "request_id"}}` with codes
`unauthorized` (401), `forbidden` (403), `not_found` (404), `bad_request` (400),
`rate_limited` (429), `upstream_error` (502), `unavailable` (503).

**Being prepared.** Some data is computed on demand. Then the answer is `202` with
`{"status": "preparing", "retry_after": N}` and a `Retry-After` header: ask again after N seconds.
"""

ERROR_RESPONSES = {code: {"description": desc, "content": {"application/json": {"schema": ERROR_SCHEMA}}}
                   for code, desc in ((401, "Missing or invalid API key"), (403, "Scope missing"),
                                      (404, "Not found"), (429, "Rate limited"), (502, "Data service error"))}


def require(*scopes: str) -> Callable:
    """The caller must hold at least one of ``scopes`` (GUI main.py ``make_require``, no rate limit)."""
    def dependency(request: Request) -> mock_keys.Caller:
        caller = mock_keys.lookup(mock_keys.key_from_headers(request.headers))
        if caller is None:
            raise PublicError("unauthorized")
        if not caller.scopes & set(scopes):
            raise PublicError("forbidden")
        request.state.caller = caller
        return caller
    return dependency


def _q(**kw) -> dict:
    return {k: v for k, v in kw.items() if v is not None}


def build_router(hmdl_api) -> APIRouter:
    """GUI routes.py ``_add_monitoring_routes``: the same nine routes, summaries and parameters."""
    router = APIRouter(prefix="/v1", responses=ERROR_RESPONSES)
    mon = Depends(require(mock_keys.SCOPE_MONITORING))
    tag = ["monitoring"]

    @router.get("/monitoring/zabbix-sync/summary", tags=tag,
                summary="Loki→Zabbix sync: last run per entity type and host counts by status")
    def mon_sync_summary(caller=mon):
        return hmdl_api.get("/api/v1/zabbix-sync/summary")

    @router.get("/monitoring/zabbix-sync/runs", tags=tag, summary="Loki→Zabbix sync runs with the mail's counts")
    def mon_sync_runs(caller=mon, entity_type: Optional[str] = Query(None, description="device, platform, virtual_fw"),
                      since: Optional[str] = Query(None, description="ISO 8601"),
                      state: Optional[str] = Query(None, description="running or finished"),
                      include_dry_run: Optional[bool] = Query(None), limit: Optional[int] = Query(None, ge=1, le=200)):
        return hmdl_api.get("/api/v1/zabbix-sync/runs", _q(entity_type=entity_type, since=since, state=state,
                                                             include_dry_run=include_dry_run, limit=limit))

    @router.get("/monitoring/zabbix-sync/runs/{run_id}", tags=tag,
                summary="One sync run: summary and the mail's sections (failed, update failed, skipped, added, updated)")
    def mon_sync_run(caller=mon, run_id: str = Path(..., description="run_id from /monitoring/zabbix-sync/runs")):
        return hmdl_api.get(f"/api/v1/zabbix-sync/runs/{quote(run_id, safe='')}")

    @router.get("/monitoring/zabbix-sync/hosts", tags=tag,
                summary="Current state of every host: status, reason code, status_since (since when), device type")
    def mon_sync_hosts(caller=mon, status: Optional[str] = Query(None), entity_type: Optional[str] = Query(None),
                       device_type: Optional[str] = Query(None), device_role: Optional[str] = Query(None),
                       manufacturer: Optional[str] = Query(None), dc: Optional[str] = Query(None),
                       reason_code: Optional[str] = Query(None),
                       problems_only: Optional[bool] = Query(None, description="only eklenemedi / güncellenemedi"),
                       q: Optional[str] = Query(None), page: Optional[int] = Query(None, ge=1),
                       page_size: Optional[int] = Query(None, ge=1, le=1000)):
        return hmdl_api.get("/api/v1/zabbix-sync/hosts", _q(
            status=status, entity_type=entity_type, device_type=device_type, device_role=device_role,
            manufacturer=manufacturer, dc=dc, reason_code=reason_code, problems_only=problems_only, q=q,
            page=page, page_size=page_size))

    @router.get("/monitoring/zabbix-sync/hosts/{host_key}", tags=tag,
                summary="One host's current state and its history over the last runs")
    def mon_sync_host(caller=mon, host_key: str = Path(..., description="host_key, e.g. virtual_fw:884"),
                      limit: Optional[int] = Query(None, ge=1, le=500)):
        return hmdl_api.get(f"/api/v1/zabbix-sync/hosts/{quote(host_key, safe=':')}", _q(limit=limit))

    @router.get("/monitoring/dq/entities", tags=tag,
                summary="Data quality: current state of each entity and since when (vm / ibm_lpar only on request)")
    def mon_dq_entities(caller=mon, kok_neden: Optional[str] = Query(None), entity_type: Optional[str] = Query(None),
                        family: Optional[str] = Query(None), dc: Optional[str] = Query(None),
                        problems_only: Optional[bool] = Query(None), include_leaf: Optional[bool] = Query(None),
                        page: Optional[int] = Query(None, ge=1), page_size: Optional[int] = Query(None, ge=1, le=2000)):
        return hmdl_api.get("/api/v1/dq/entities", _q(kok_neden=kok_neden, entity_type=entity_type, family=family,
                                                      dc=dc, problems_only=problems_only, include_leaf=include_leaf,
                                                      page=page, page_size=page_size))

    @router.get("/monitoring/dq/runs", tags=tag, summary="Data quality runs and whether each was complete")
    def mon_dq_runs(caller=mon, limit: Optional[int] = Query(None, ge=1, le=200)):
        return hmdl_api.get("/api/v1/dq/runs", _q(limit=limit))

    @router.get("/monitoring/automation/status", tags=tag,
                summary="HMDL automations: last run, state (fresh / stale / dead / unknown) and since when")
    def mon_automation(caller=mon):
        return hmdl_api.get("/api/v1/automation/status")

    @router.get("/monitoring/automation/awx-revisions", tags=tag,
                summary="Live AWX jobs: is each one running the code on main")
    def mon_awx_revisions(caller=mon):
        return hmdl_api.get("/api/v1/automation/awx-revisions")

    return router


def create_app(*, hmdl_api: Optional[Upstream] = None) -> FastAPI:
    hmdl_api = hmdl_api or Upstream(HMDL_API_URL)
    app = FastAPI(title="Bulutistan Datalake API (mock)", version=API_VERSION, description=DESCRIPTION,
                  docs_url="/docs", redoc_url=None)

    @app.middleware("http")
    async def _request_id(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request_id(request))
        return response

    @app.exception_handler(PublicError)
    async def _public_error(request: Request, exc: PublicError):
        return error_response(request, exc.code, exc.message, exc.headers)

    @app.exception_handler(Preparing)
    async def _preparing(request: Request, exc: Preparing):
        return preparing_response(request, exc.retry_after)

    @app.exception_handler(RequestValidationError)
    async def _invalid(request: Request, exc: RequestValidationError):
        fields = ", ".join(".".join(str(p) for p in e.get("loc", ())[1:]) for e in exc.errors())
        return error_response(request, "bad_request", f"Invalid parameter: {fields}" if fields else None)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {401: "unauthorized", 403: "forbidden", 404: "not_found", 405: "not_found"}.get(exc.status_code,
                                                                                            "bad_request")
        return error_response(request, code)

    app.include_router(build_router(hmdl_api))

    @app.get("/health", include_in_schema=False)
    def health():
        return {"status": "ok"}

    def openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        schema.setdefault("components", {})["securitySchemes"] = {
            "bearer": {"type": "http", "scheme": "bearer", "description": "Your API key"},
            "apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
        }
        schema["security"] = [{"bearer": []}, {"apiKey": []}]
        app.openapi_schema = schema
        return schema

    app.openapi = openapi
    return app


app = create_app()
