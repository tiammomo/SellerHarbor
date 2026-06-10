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
class Settings:
    port: int
    db_path: Path
    seed_demo: bool
    llm: LLMSettings
    object_storage: ObjectStorageSettings


def load_settings() -> Settings:
    claude = _read_claude_code_settings()
    env = claude.get("env", {})
    port = int(_first(os.getenv("REVIEWPILOT_PORT"), "38081"))

    model = _first(
        os.getenv("REVIEWPILOT_LLM_MODEL"),
        os.getenv("ANTHROPIC_MODEL"),
        env.get("ANTHROPIC_MODEL"),
        claude.get("selected_model"),
        _read_claude_model(),
        "mimo-v2.5-pro",
    )
    base_url = _first(os.getenv("REVIEWPILOT_LLM_BASE_URL"), os.getenv("ANTHROPIC_BASE_URL"), env.get("ANTHROPIC_BASE_URL"))
    api_key = _first(
        os.getenv("REVIEWPILOT_LLM_API_KEY"),
        os.getenv("ANTHROPIC_AUTH_TOKEN"),
        os.getenv("ANTHROPIC_API_KEY"),
        env.get("ANTHROPIC_AUTH_TOKEN"),
        env.get("ANTHROPIC_API_KEY"),
    )
    provider = _first(os.getenv("REVIEWPILOT_LLM_PROVIDER"), "anthropic" if base_url else "anthropic")

    return Settings(
        port=port,
        db_path=Path(_first(os.getenv("REVIEWPILOT_DB_PATH"), "data/reviewpilot.db")),
        seed_demo=_truthy(_first(os.getenv("REVIEWPILOT_SEED_DEMO"), "true")),
        llm=LLMSettings(
            provider=provider.lower(),
            base_url=base_url.rstrip("/") if base_url else "",
            api_key=api_key,
            model=model,
            timeout_seconds=float(_first(os.getenv("REVIEWPILOT_LLM_TIMEOUT_SECONDS"), "180")),
        ),
        object_storage=ObjectStorageSettings(
            endpoint=_first(os.getenv("REVIEWPILOT_OBJECT_STORAGE_ENDPOINT")),
            bucket=_first(os.getenv("REVIEWPILOT_OBJECT_STORAGE_BUCKET"), "reviewpilot-assets"),
            region=_first(os.getenv("REVIEWPILOT_OBJECT_STORAGE_REGION"), "us-east-1"),
            access_key=_first(os.getenv("REVIEWPILOT_OBJECT_STORAGE_ACCESS_KEY")),
            secret_key=_first(os.getenv("REVIEWPILOT_OBJECT_STORAGE_SECRET_KEY")),
            public_api_base_url=_first(os.getenv("REVIEWPILOT_PUBLIC_API_BASE_URL"), f"http://localhost:{port}").rstrip("/"),
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


settings = load_settings()
