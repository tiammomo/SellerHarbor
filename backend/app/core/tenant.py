from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from app.core.config import settings


_tenant_id: ContextVar[str] = ContextVar("sellerharbor_tenant_id", default="")


def current_tenant_id() -> str:
    return _tenant_id.get() or settings.default_tenant_id


@contextmanager
def tenant_context(tenant_id: str) -> Iterator[None]:
    token = _tenant_id.set(normalize_tenant_id(tenant_id))
    try:
        yield
    finally:
        _tenant_id.reset(token)


def set_current_tenant(tenant_id: str):
    return _tenant_id.set(normalize_tenant_id(tenant_id))


def reset_current_tenant(token) -> None:
    _tenant_id.reset(token)


def normalize_tenant_id(value: str | None) -> str:
    tenant_id = (value or "").strip()
    return tenant_id or settings.default_tenant_id


def tenant_allowed(tenant_id: str) -> bool:
    if not settings.allowed_tenant_ids:
        return True
    return tenant_id in settings.allowed_tenant_ids
