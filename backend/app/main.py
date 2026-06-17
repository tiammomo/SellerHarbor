from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.core.tenant import normalize_tenant_id, reset_current_tenant, set_current_tenant, tenant_allowed, tenant_context
from app.db.repository import init_db, seed_demo, now_iso
from app.db import repository
from app.services.observability import log_access_event, runtime_metrics
from app.services.rate_limit import rate_limiter


app = FastAPI(title="SellerHarbor Backend", version="0.1.0")

cors_kwargs = (
    {"allow_origins": settings.cors_allow_origins}
    if settings.cors_allow_origins
    else {"allow_origin_regex": r"^http://(localhost|127\.0\.0\.1):\d+$"}
)
app.add_middleware(
    CORSMiddleware,
    **cors_kwargs,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_gate(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id
    tenant_id = _request_tenant_id(request)
    request.state.tenant_id = tenant_id
    tenant_token = set_current_tenant(tenant_id)
    started = time.perf_counter()
    status_code = 500
    response = None
    actor = _actor(request)
    try:
        if not tenant_allowed(tenant_id):
            response = JSONResponse({"detail": "tenant is not allowed"}, status_code=403)
            status_code = 403
            response.headers["X-Request-ID"] = request_id
            response.headers["X-SellerHarbor-Tenant-ID"] = tenant_id
            _record_request(request, request_id, actor, started, status_code)
            return response

        if _requires_api_key(request):
            provided = _request_api_key(request)
            if not settings.api_keys:
                response = JSONResponse(
                    {"detail": "API access control is enabled but SELLERHARBOR_API_KEYS is not configured"},
                    status_code=503,
                )
                status_code = 503
                response.headers["X-Request-ID"] = request_id
                response.headers["X-SellerHarbor-Tenant-ID"] = tenant_id
                _record_request(request, request_id, actor, started, status_code)
                return response
            if provided not in settings.api_keys:
                response = JSONResponse({"detail": "invalid or missing API key"}, status_code=401)
                status_code = 401
                response.headers["X-Request-ID"] = request_id
                response.headers["X-SellerHarbor-Tenant-ID"] = tenant_id
                _record_request(request, request_id, actor, started, status_code)
                return response

        limit_result = _rate_limit_result(request, actor)
        if limit_result is not None and not limit_result.allowed:
            runtime_metrics.record_rate_limited()
            response = JSONResponse(
                {
                    "detail": f"rate limit exceeded for {limit_result.scope}",
                    "retryAfterSeconds": limit_result.retry_after_seconds,
                },
                status_code=429,
            )
            response.headers["Retry-After"] = str(limit_result.retry_after_seconds)
            response.headers["X-RateLimit-Limit"] = str(limit_result.limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-Request-ID"] = request_id
            response.headers["X-SellerHarbor-Tenant-ID"] = tenant_id
            status_code = 429
            _record_request(request, request_id, actor, started, status_code)
            return response

        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-SellerHarbor-Tenant-ID"] = tenant_id
        if limit_result is not None:
            response.headers["X-RateLimit-Limit"] = str(limit_result.limit)
            response.headers["X-RateLimit-Remaining"] = str(limit_result.remaining)
        return response
    finally:
        if response is not None:
            _record_request(request, request_id, actor, started, status_code)
        reset_current_tenant(tenant_token)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    for tenant_id in _startup_tenant_ids():
        with tenant_context(tenant_id):
            recovered = repository.fail_stale_generation_tasks(settings.generation_task_timeout_seconds)
            for task in recovered:
                repository.create_audit_event(
                    actor="system",
                    action="generation.recovered_failed",
                    resource_type="generation_task",
                    resource_id=task.id,
                    metadata={"message": task.message or "stale generation task recovered"},
                )
            if settings.seed_demo:
                seed_demo()


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "time": now_iso()}


app.include_router(router, prefix="/api")


def _requires_api_key(request: Request) -> bool:
    if not settings.auth_required:
        return False
    if request.method == "OPTIONS":
        return False
    if request.url.path in {"/healthz", "/api/health"}:
        return False
    return request.url.path.startswith("/api")


def _request_api_key(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return request.headers.get("x-sellerharbor-api-key", "").strip()


def _request_tenant_id(request: Request) -> str:
    return normalize_tenant_id(request.headers.get("x-sellerharbor-tenant-id"))


def _rate_limit_result(request: Request, actor: str):
    if not settings.rate_limit_enabled or _skip_rate_limit(request):
        return None
    scope = "generation" if request.url.path in {"/api/generation-jobs", "/api/generations"} and request.method == "POST" else "api"
    limit = settings.generation_jobs_per_minute if scope == "generation" else settings.requests_per_minute
    key = f"{scope}:{request.state.tenant_id}:{actor}:{request.client.host if request.client else 'unknown'}"
    return rate_limiter.check(key=key, limit=limit, scope=scope)


def _skip_rate_limit(request: Request) -> bool:
    if request.method == "OPTIONS":
        return True
    return request.url.path in {"/healthz", "/api/health", "/api/metrics", "/api/readiness"}


def _record_request(request: Request, request_id: str, actor: str, started: float, status_code: int) -> None:
    duration_ms = (time.perf_counter() - started) * 1000
    runtime_metrics.record_request(method=request.method, status_code=status_code, duration_ms=duration_ms)
    log_access_event(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=status_code,
        duration_ms=duration_ms,
        client=request.client.host if request.client else "unknown",
        actor=f"{request.state.tenant_id}:{actor}",
    )


def _actor(request: Request) -> str:
    return (
        request.headers.get("x-sellerharbor-actor")
        or request.headers.get("x-forwarded-user")
        or request.headers.get("x-user")
        or _request_api_key(request)
        or "anonymous"
    ).strip()


def _startup_tenant_ids() -> list[str]:
    return settings.allowed_tenant_ids or [settings.default_tenant_id]
