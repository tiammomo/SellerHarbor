from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.db import repository
from app.services import object_storage
from app.services.llm import llm_client


async def build_readiness_report() -> dict[str, Any]:
    checks = [
        _database_check(),
        await _llm_check(),
        _object_storage_check(),
        _tenant_check(),
        _auth_check(),
        _rate_limit_check(),
        _generation_queue_check(),
        _seed_demo_check(),
        _cors_check(),
    ]
    critical_failures = [check for check in checks if check["severity"] == "critical" and check["status"] != "healthy"]
    warnings = [
        check
        for check in checks
        if check["severity"] == "warning" and check["status"] not in {"healthy", "skipped"}
    ]

    if critical_failures:
        status = "unavailable"
    elif warnings:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "environment": settings.environment,
        "time": repository.now_iso(),
        "checks": checks,
    }


def _database_check() -> dict[str, Any]:
    try:
        with repository.connect() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception as exc:
        return {
            "key": "database",
            "label": "Database",
            "status": "unavailable",
            "severity": "critical",
            "detail": str(exc),
        }
    return {
        "key": "database",
        "label": "Database",
        "status": "healthy",
        "severity": "critical",
        "detail": f"SQLite database ready at {settings.db_path}",
    }


async def _llm_check() -> dict[str, Any]:
    status = await llm_client.health()
    check_status = status["status"]
    detail = status["detail"]
    if not status["configured"] and settings.environment != "production":
        check_status = "skipped"
        detail = "LLM gateway is optional in local development; configure it to enable generation"
    return {
        "key": "llm",
        "label": "LLM Gateway",
        "status": check_status,
        "severity": "warning",
        "detail": detail,
        "metadata": {
            "configured": status["configured"],
            "provider": status["provider"],
            "model": status["model"],
            "baseUrl": status["baseUrl"],
            "latencyMs": status["latencyMs"],
        },
    }


def _object_storage_check() -> dict[str, Any]:
    status = object_storage.status()
    configured = bool(status["configured"])
    if configured:
        state = "healthy"
        detail = f"Object storage configured for bucket {status['bucket']}"
    elif settings.environment == "production":
        state = "unconfigured"
        detail = "Object storage is required for production image and export assets"
    else:
        state = "skipped"
        detail = "Object storage is optional in local development"
    return {
        "key": "object_storage",
        "label": "Object Storage",
        "status": state,
        "severity": "warning",
        "detail": detail,
        "metadata": status,
    }


def _tenant_check() -> dict[str, Any]:
    if settings.environment == "production" and not settings.allowed_tenant_ids:
        return {
            "key": "tenant",
            "label": "Tenant Isolation",
            "status": "unconfigured",
            "severity": "warning",
            "detail": "Set SELLERHARBOR_ALLOWED_TENANT_IDS in production",
            "metadata": {"defaultTenantId": settings.default_tenant_id, "allowedTenantIds": settings.allowed_tenant_ids},
        }
    return {
        "key": "tenant",
        "label": "Tenant Isolation",
        "status": "healthy",
        "severity": "warning",
        "detail": f"default tenant: {settings.default_tenant_id}",
        "metadata": {"defaultTenantId": settings.default_tenant_id, "allowedTenantIds": settings.allowed_tenant_ids},
    }


def _auth_check() -> dict[str, Any]:
    if settings.auth_required and settings.api_keys:
        return {
            "key": "auth",
            "label": "API Access Control",
            "status": "healthy",
            "severity": "critical",
            "detail": "API key gate is enabled",
        }
    if settings.environment == "production":
        return {
            "key": "auth",
            "label": "API Access Control",
            "status": "unconfigured",
            "severity": "critical",
            "detail": "Set SELLERHARBOR_AUTH_REQUIRED=true and SELLERHARBOR_API_KEYS in production",
        }
    return {
        "key": "auth",
        "label": "API Access Control",
        "status": "skipped",
        "severity": "warning",
        "detail": "API key gate is optional in local development",
    }


def _rate_limit_check() -> dict[str, Any]:
    if not settings.rate_limit_enabled:
        return {
            "key": "rate_limit",
            "label": "Rate Limit",
            "status": "unconfigured" if settings.environment == "production" else "skipped",
            "severity": "warning",
            "detail": "Rate limiting is disabled",
        }
    return {
        "key": "rate_limit",
        "label": "Rate Limit",
        "status": "healthy",
        "severity": "warning",
        "detail": (
            f"{settings.requests_per_minute} api requests/min, "
            f"{settings.generation_jobs_per_minute} generation jobs/min"
        ),
    }


def _generation_queue_check() -> dict[str, Any]:
    counts = repository.generation_task_status_counts()
    stale_count = repository.stale_generation_task_count(settings.generation_task_timeout_seconds)
    if stale_count:
        status = "degraded"
        detail = f"{stale_count} generation task(s) appear stale"
    else:
        status = "healthy"
        detail = "generation queue has no stale tasks"
    return {
        "key": "generation_queue",
        "label": "Generation Queue",
        "status": status,
        "severity": "warning",
        "detail": detail,
        "metadata": {
            "counts": counts,
            "timeoutSeconds": settings.generation_task_timeout_seconds,
        },
    }


def _seed_demo_check() -> dict[str, Any]:
    if settings.environment == "production" and settings.seed_demo:
        return {
            "key": "seed_demo",
            "label": "Demo Seed Data",
            "status": "enabled",
            "severity": "warning",
            "detail": "Disable SELLERHARBOR_SEED_DEMO in production",
        }
    return {
        "key": "seed_demo",
        "label": "Demo Seed Data",
        "status": "healthy",
        "severity": "warning",
        "detail": f"seedDemo={settings.seed_demo}",
    }


def _cors_check() -> dict[str, Any]:
    if settings.environment == "production" and not settings.cors_allow_origins:
        return {
            "key": "cors",
            "label": "CORS Allowlist",
            "status": "unconfigured",
            "severity": "warning",
            "detail": "Set SELLERHARBOR_CORS_ALLOW_ORIGINS for production frontend domains",
        }
    detail = (
        f"allowed origins: {', '.join(settings.cors_allow_origins)}"
        if settings.cors_allow_origins
        else "localhost development origin regex enabled"
    )
    return {
        "key": "cors",
        "label": "CORS Allowlist",
        "status": "healthy",
        "severity": "warning",
        "detail": detail,
    }
