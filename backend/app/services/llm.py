from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings


class LLMError(RuntimeError):
    pass


class LLMUnavailableError(LLMError):
    pass


class LLMInvalidJSONError(LLMError):
    pass


class LocalAnthropicClient:
    def __init__(self) -> None:
        self.settings = settings.llm

    @property
    def configured(self) -> bool:
        return self.settings.configured

    async def health(self) -> dict[str, Any]:
        if not self.configured:
            missing = [
                name
                for name, value in (
                    ("baseUrl", self.settings.base_url),
                    ("apiKey", self.settings.api_key),
                    ("model", self.settings.model),
                )
                if not value
            ]
            return {
                "status": "unconfigured",
                "configured": False,
                "provider": self.settings.provider,
                "model": self.settings.model,
                "baseUrl": self.settings.base_url,
                "detail": f"missing {', '.join(missing)}",
                "latencyMs": None,
            }

        target = _connection_target(self.settings.base_url)
        if not target:
            return {
                "status": "unconfigured",
                "configured": False,
                "provider": self.settings.provider,
                "model": self.settings.model,
                "baseUrl": self.settings.base_url,
                "detail": "invalid LLM base URL",
                "latencyMs": None,
            }

        host, port = target
        started = time.perf_counter()
        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.settings.connect_timeout_seconds,
            )
            writer.close()
            await writer.wait_closed()
        except TimeoutError:
            return self._health_failure(started, "unavailable", f"connection timed out: {host}:{port}")
        except OSError as exc:
            return self._health_failure(started, "unavailable", f"connection failed: {exc}")

        return {
            "status": "healthy",
            "configured": True,
            "provider": self.settings.provider,
            "model": self.settings.model,
            "baseUrl": self.settings.base_url,
            "detail": f"TCP connection ready: {host}:{port}",
            "latencyMs": _elapsed_ms(started),
        }

    async def ensure_ready(self) -> None:
        status = await self.health()
        if status.get("status") != "healthy":
            detail = status.get("detail") or "LLM service is not ready"
            raise LLMUnavailableError(f"LLM unavailable: {detail}")

    def _health_failure(self, started: float, status: str, detail: str) -> dict[str, Any]:
        return {
            "status": status,
            "configured": True,
            "provider": self.settings.provider,
            "model": self.settings.model,
            "baseUrl": self.settings.base_url,
            "detail": detail,
            "latencyMs": _elapsed_ms(started),
        }

    async def generate_json(self, *, system: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            raise LLMError("LLM is not configured: missing ANTHROPIC_BASE_URL or ANTHROPIC_AUTH_TOKEN")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system}"),
                ("human", "{payload}"),
            ]
        )
        prompt_value = prompt.invoke(
            {
                "system": system,
                "payload": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        )
        text = await self._messages_from_prompt(prompt_value)
        try:
            return _parse_json_object(text)
        except LLMInvalidJSONError as exc:
            repair_text = await self._repair_json(text, str(exc))
            return _parse_json_object(repair_text)

    async def _messages_from_prompt(self, prompt_value: Any) -> str:
        messages = prompt_value.to_messages() if hasattr(prompt_value, "to_messages") else prompt_value
        if not isinstance(messages, list) or len(messages) < 2:
            raise LLMError("LangChain prompt did not produce system and user messages")
        return await self._messages(
            system=_message_content_to_text(messages[0].content),
            user=_message_content_to_text(messages[1].content),
        )

    async def _repair_json(self, invalid_output: str, parse_error: str) -> str:
        repair_system = """你是 JSON 修复器。
只把输入中的模型输出修复为严格 JSON。
不要新增事实、不要解释、不要 Markdown、不要代码块。
输出必须是一个 JSON object，且顶层必须包含 items 数组。
"""
        repair_payload = {
            "parseError": parse_error,
            "requiredTopLevelShape": {"items": []},
            "invalidOutput": invalid_output[:12000],
        }
        return await self._messages(
            system=repair_system,
            user=json.dumps(repair_payload, ensure_ascii=False, indent=2),
        )

    async def _messages(self, *, system: str, user: str) -> str:
        url = f"{self.settings.base_url}/v1/messages"
        body = {
            "model": self.settings.model,
            "max_tokens": 2400,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
            "authorization": f"Bearer {self.settings.api_key}",
            "x-api-key": self.settings.api_key,
        }
        last_data: dict[str, Any] | None = None
        timeout = httpx.Timeout(
            self.settings.timeout_seconds,
            connect=self.settings.connect_timeout_seconds,
            write=self.settings.connect_timeout_seconds,
            pool=self.settings.connect_timeout_seconds,
        )
        async with httpx.AsyncClient(
            timeout=timeout,
            trust_env=_should_trust_env(self.settings.base_url),
        ) as client:
            for attempt in range(2):
                try:
                    response = await client.post(url, headers=headers, json=body)
                except (
                    httpx.ConnectError,
                    httpx.ConnectTimeout,
                    httpx.PoolTimeout,
                    httpx.ReadError,
                    httpx.RemoteProtocolError,
                    httpx.WriteError,
                ) as exc:
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                        continue
                    raise LLMUnavailableError(f"LLM connection failed: {exc}") from exc
                except httpx.TimeoutException as exc:
                    raise LLMError(f"LLM request timed out after {self.settings.timeout_seconds:g}s") from exc
                except httpx.HTTPError as exc:
                    raise LLMError(f"LLM request failed: {exc}") from exc
                if response.status_code < 200 or response.status_code >= 300:
                    raise LLMError(f"LLM HTTP {response.status_code}: {response.text[:500]}")
                data = response.json()
                last_data = data
                if data.get("error"):
                    raise LLMError(str(data["error"].get("message") or data["error"]))
                text = _extract_text_content(data)
                if text:
                    return text
                if attempt == 0:
                    await asyncio.sleep(0.5)
        raise LLMError(f"LLM returned no text content: {_response_shape(last_data)}")


def _parse_json_object(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```json"):
        raw = raw.removeprefix("```json").strip()
    if raw.startswith("```"):
        raw = raw.removeprefix("```").strip()
    if raw.endswith("```"):
        raw = raw.removesuffix("```").strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    for candidate in _json_repair_candidates(raw):
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
        raise LLMInvalidJSONError(f"LLM returned JSON {type(data).__name__}, expected object")
    try:
        json.loads(raw)
    except json.JSONDecodeError as exc:
        snippet = raw[max(0, exc.pos - 120) : exc.pos + 120].replace("\n", "\\n")
        raise LLMInvalidJSONError(f"LLM returned invalid JSON: {exc}; near: {snippet}") from exc
    raise LLMInvalidJSONError("LLM returned invalid JSON object")


def _json_repair_candidates(raw: str) -> list[str]:
    without_trailing_commas = re.sub(r",(\s*[}\]])", r"\1", raw)
    escaped_controls = _escape_control_chars_in_strings(raw)
    escaped_without_trailing_commas = re.sub(r",(\s*[}\]])", r"\1", escaped_controls)
    return _unique_candidates([raw, without_trailing_commas, escaped_controls, escaped_without_trailing_commas])


def _escape_control_chars_in_strings(raw: str) -> str:
    replacements = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}
    output: list[str] = []
    in_string = False
    escaped = False
    for char in raw:
        if escaped:
            output.append(char)
            escaped = False
            continue
        if char == "\\":
            output.append(char)
            escaped = True
            continue
        if char == '"':
            output.append(char)
            in_string = not in_string
            continue
        if in_string and char in replacements:
            output.append(replacements[char])
            continue
        output.append(char)
    return "".join(output)


def _unique_candidates(candidates: list[str]) -> list[str]:
    seen = set()
    result = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        result.append(candidate)
    return result


def _message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False)


def _extract_text_content(data: dict[str, Any]) -> str:
    content = data.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        for item in content:
            text = _extract_text_item(item)
            if text:
                return text

    choices = data.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message")
            if isinstance(message, dict):
                text = _extract_text_item(message.get("content")) or _extract_text_item(message)
                if text:
                    return text
            text = _extract_text_item(choice.get("text"))
            if text:
                return text

    for key in ("text", "completion", "output_text", "message"):
        text = _extract_text_item(data.get(key))
        if text:
            return text
    return ""


def _extract_text_item(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        for key in ("text", "content", "message", "output_text"):
            text = _extract_text_item(item.get(key))
            if text:
                return text
    if isinstance(item, list):
        for child in item:
            text = _extract_text_item(child)
            if text:
                return text
    return ""


def _response_shape(data: dict[str, Any] | None) -> str:
    if not data:
        return "empty response"
    shape = {key: type(value).__name__ for key, value in data.items()}
    return json.dumps(shape, ensure_ascii=False)


def _connection_target(base_url: str) -> tuple[str, int] | None:
    parsed = urlparse(base_url)
    if not parsed.hostname:
        return None
    if parsed.port:
        return parsed.hostname, parsed.port
    if parsed.scheme == "https":
        return parsed.hostname, 443
    if parsed.scheme == "http":
        return parsed.hostname, 80
    return None


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1000))


def _should_trust_env(base_url: str) -> bool:
    host = urlparse(base_url).hostname or ""
    if host == "localhost" or host == "::1" or host.startswith("127."):
        return False
    return True


llm_client = LocalAnthropicClient()
