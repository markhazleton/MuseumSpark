"""LLM client helpers (OpenAI / Anthropic)."""

from __future__ import annotations

import json
from typing import Any, Optional


def _parse_json(text: str) -> Any:
    return json.loads(text)


def call_openai_json(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    json_schema: Optional[dict[str, Any]] = None,
) -> Any:
    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError("OpenAI SDK not installed. Run `pip install openai`.") from exc

    client = OpenAI(api_key=api_key)
    response_format = {"type": "json_object"}
    if json_schema:
        response_format = {"type": "json_schema", "json_schema": {"name": "output", "schema": json_schema}}

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
    )
    content = response.choices[0].message.content or ""
    return _parse_json(content)


def call_anthropic_json(
    *,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Any:
    try:
        from anthropic import Anthropic
    except Exception as exc:
        raise RuntimeError("Anthropic SDK not installed. Run `pip install anthropic`.") from exc

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        system=system,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    text_chunks = [block.text for block in response.content if getattr(block, "text", None)]
    content = "".join(text_chunks).strip()
    return _parse_json(content)

