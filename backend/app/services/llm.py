from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import urlparse

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from app.core.config import settings


class LLMError(RuntimeError):
    pass


class LocalAnthropicClient:
    def __init__(self) -> None:
        self.settings = settings.llm

    @property
    def configured(self) -> bool:
        return self.settings.configured

    async def generate_json(self, *, system: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            raise LLMError("LLM is not configured: missing ANTHROPIC_BASE_URL or ANTHROPIC_AUTH_TOKEN")

        chain = (
            ChatPromptTemplate.from_messages(
                [
                    ("system", "{system}"),
                    ("human", "{payload}"),
                ]
            )
            | RunnableLambda(self._messages_from_prompt)
            | RunnableLambda(_parse_json_object)
        ).with_config(
            {
                "run_name": "reviewpilot_mimo_json_generation",
                "tags": ["reviewpilot", "mimo-v2.5-pro", self.settings.model],
                "metadata": {"provider": self.settings.provider, "model": self.settings.model},
            }
        )
        return await chain.ainvoke(
            {
                "system": system,
                "payload": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        )

    async def _messages_from_prompt(self, prompt_value: Any) -> str:
        messages = prompt_value.to_messages() if hasattr(prompt_value, "to_messages") else prompt_value
        if not isinstance(messages, list) or len(messages) < 2:
            raise LLMError("LangChain prompt did not produce system and user messages")
        return await self._messages(
            system=_message_content_to_text(messages[0].content),
            user=_message_content_to_text(messages[1].content),
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
        async with httpx.AsyncClient(
            timeout=self.settings.timeout_seconds,
            trust_env=_should_trust_env(self.settings.base_url),
        ) as client:
            for attempt in range(2):
                response = await client.post(url, headers=headers, json=body)
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
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM returned invalid JSON: {exc}") from exc


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


def _should_trust_env(base_url: str) -> bool:
    host = urlparse(base_url).hostname or ""
    if host == "localhost" or host == "::1" or host.startswith("127."):
        return False
    return True


llm_client = LocalAnthropicClient()
