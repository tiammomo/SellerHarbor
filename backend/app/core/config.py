from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float
    connect_timeout_seconds: float

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)


@dataclass(frozen=True)
class ObjectStorageSettings:
    endpoint: str
    bucket: str
    region: str
    access_key: str
    secret_key: str
    public_api_base_url: str

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.bucket and self.access_key and self.secret_key)


@dataclass(frozen=True)
class TemuSettings:
    api_base_url: str
    app_key: str
    app_secret: str
    access_token: str
    seller_id: str
    region: str
    sandbox: bool

    @property
    def configured(self) -> bool:
        return bool(self.api_base_url and self.app_key and self.app_secret and self.access_token)

    @property
    def partially_configured(self) -> bool:
        return any([self.app_key, self.app_secret, self.access_token, self.seller_id])


@dataclass(frozen=True)
class StoreSettings:
    default_store_id: str
    default_store_name: str
    default_store_platform: str
    default_store_region: str
    default_store_warehouse: str
    allowed_store_ids: list[str]
    multi_store_enabled: bool


@dataclass(frozen=True)
class Settings:
    environment: str
    port: int
    db_path: Path
    seed_demo: bool
    cors_allow_origins: list[str]
    default_tenant_id: str
    allowed_tenant_ids: list[str]
    auth_required: bool
    api_keys: list[str]
    rate_limit_enabled: bool
    requests_per_minute: int
    generation_jobs_per_minute: int
    generation_task_timeout_seconds: int
    llm: LLMSettings
    object_storage: ObjectStorageSettings
    temu: TemuSettings
    store: StoreSettings


def load_settings() -> Settings:
    claude = _read_claude_code_settings()
    env = claude.get("env", {})
    environment = _first(os.getenv("SELLERHARBOR_ENV"), "development").lower()
    port = int(_first(os.getenv("SELLERHARBOR_PORT"), "38081"))

    model = _first(
        os.getenv("SELLERHARBOR_LLM_MODEL"),
        os.getenv("ANTHROPIC_MODEL"),
        env.get("ANTHROPIC_MODEL"),
        claude.get("selected_model"),
        _read_claude_model(),
        "mimo-v2.5-pro",
    )
    base_url = _first(
        os.getenv("SELLERHARBOR_LLM_BASE_URL"),
        os.getenv("ANTHROPIC_BASE_URL"),
        env.get("ANTHROPIC_BASE_URL"),
    )
    api_key = _first(
        os.getenv("SELLERHARBOR_LLM_API_KEY"),
        os.getenv("ANTHROPIC_AUTH_TOKEN"),
        os.getenv("ANTHROPIC_API_KEY"),
        env.get("ANTHROPIC_AUTH_TOKEN"),
        env.get("ANTHROPIC_API_KEY"),
    )
    provider = _first(os.getenv("SELLERHARBOR_LLM_PROVIDER"), "anthropic" if base_url else "anthropic")

    return Settings(
        environment=environment,
        port=port,
        db_path=Path(_first(os.getenv("SELLERHARBOR_DB_PATH"), "data/sellerharbor.db")),
        seed_demo=_truthy(_first(os.getenv("SELLERHARBOR_SEED_DEMO"), "true")),
        cors_allow_origins=_csv(os.getenv("SELLERHARBOR_CORS_ALLOW_ORIGINS")),
        default_tenant_id=_first(os.getenv("SELLERHARBOR_DEFAULT_TENANT_ID"), "local"),
        allowed_tenant_ids=_csv(os.getenv("SELLERHARBOR_ALLOWED_TENANT_IDS")),
        auth_required=_truthy(_first(os.getenv("SELLERHARBOR_AUTH_REQUIRED"), "true" if environment == "production" else "false")),
        api_keys=_csv(os.getenv("SELLERHARBOR_API_KEYS")),
        rate_limit_enabled=_truthy(_first(os.getenv("SELLERHARBOR_RATE_LIMIT_ENABLED"), "true")),
        requests_per_minute=int(_first(os.getenv("SELLERHARBOR_RATE_LIMIT_REQUESTS_PER_MINUTE"), "180")),
        generation_jobs_per_minute=int(_first(os.getenv("SELLERHARBOR_RATE_LIMIT_GENERATION_JOBS_PER_MINUTE"), "12")),
        generation_task_timeout_seconds=int(_first(os.getenv("SELLERHARBOR_GENERATION_TASK_TIMEOUT_SECONDS"), "600")),
        llm=LLMSettings(
            provider=provider.lower(),
            base_url=base_url.rstrip("/") if base_url else "",
            api_key=api_key,
            model=model,
            timeout_seconds=float(_first(os.getenv("SELLERHARBOR_LLM_TIMEOUT_SECONDS"), "180")),
            connect_timeout_seconds=float(_first(os.getenv("SELLERHARBOR_LLM_CONNECT_TIMEOUT_SECONDS"), "5")),
        ),
        object_storage=ObjectStorageSettings(
            endpoint=_first(os.getenv("SELLERHARBOR_OBJECT_STORAGE_ENDPOINT")),
            bucket=_first(os.getenv("SELLERHARBOR_OBJECT_STORAGE_BUCKET"), "sellerharbor-assets"),
            region=_first(os.getenv("SELLERHARBOR_OBJECT_STORAGE_REGION"), "us-east-1"),
            access_key=_first(os.getenv("SELLERHARBOR_OBJECT_STORAGE_ACCESS_KEY")),
            secret_key=_first(os.getenv("SELLERHARBOR_OBJECT_STORAGE_SECRET_KEY")),
            public_api_base_url=_first(os.getenv("SELLERHARBOR_PUBLIC_API_BASE_URL"), f"http://localhost:{port}").rstrip("/"),
        ),
        temu=TemuSettings(
            api_base_url=_first(os.getenv("SELLERHARBOR_TEMU_API_BASE_URL"), "https://openapi.temu.com"),
            app_key=_first(os.getenv("SELLERHARBOR_TEMU_APP_KEY")),
            app_secret=_first(os.getenv("SELLERHARBOR_TEMU_APP_SECRET")),
            access_token=_first(os.getenv("SELLERHARBOR_TEMU_ACCESS_TOKEN")),
            seller_id=_first(os.getenv("SELLERHARBOR_TEMU_SELLER_ID")),
            region=_first(os.getenv("SELLERHARBOR_TEMU_REGION"), "global"),
            sandbox=_truthy(_first(os.getenv("SELLERHARBOR_TEMU_SANDBOX"), "false")),
        ),
        store=StoreSettings(
            default_store_id=_first(os.getenv("SELLERHARBOR_DEFAULT_STORE_ID"), "primary-store"),
            default_store_name=_first(os.getenv("SELLERHARBOR_DEFAULT_STORE_NAME"), "SellerHarbor 默认店铺"),
            default_store_platform=_first(os.getenv("SELLERHARBOR_DEFAULT_STORE_PLATFORM"), "temu"),
            default_store_region=_first(os.getenv("SELLERHARBOR_DEFAULT_STORE_REGION"), "global"),
            default_store_warehouse=_first(os.getenv("SELLERHARBOR_DEFAULT_STORE_WAREHOUSE"), "US-West LA 3PL"),
            allowed_store_ids=_csv(os.getenv("SELLERHARBOR_ALLOWED_STORE_IDS")),
            multi_store_enabled=_truthy(_first(os.getenv("SELLERHARBOR_MULTI_STORE_ENABLED"), "false")),
        ),
    )


def _read_claude_code_settings() -> dict:
    path = Path.home() / ".config" / "Code" / "User" / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"env": {}}

    env = {}
    for item in data.get("claudeCode.environmentVariables", []):
        name = str(item.get("name", "")).strip()
        if name:
            env[name] = str(item.get("value", "")).strip()
    return {"selected_model": str(data.get("claudeCode.selectedModel", "")).strip(), "env": env}


def _read_claude_model() -> str:
    path = Path.home() / ".claude" / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(data.get("model", "")).strip()


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _first(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]


settings = load_settings()
