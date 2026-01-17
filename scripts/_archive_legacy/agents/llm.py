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
        max_completion_tokens=max_tokens,
        response_format=response_format,
    )

    choice = response.choices[0].message
    choice_dict = choice.model_dump() if hasattr(choice, "model_dump") else None

    # Prefer parsed output when json_schema is used (available in newer SDKs)
    parsed = getattr(choice, "parsed", None)
    if parsed is None and isinstance(choice_dict, dict):
        parsed = choice_dict.get("parsed")
    if parsed is not None:
        return parsed

    content = choice.content if choice.content is not None else (choice_dict.get("content") if isinstance(choice_dict, dict) else None)
    if content is None:
        raise ValueError("OpenAI response had no content")

    # If structured output is returned as output_json blocks, use it directly
    if isinstance(content, list) and content:
        for part in content:
            if isinstance(part, dict) and part.get("type") == "output_json" and "json" in part:
                return part.get("json")

    # content may be a list of content parts; join their text
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part.get("text", ""))
            else:
                text_parts.append(str(part))
        content_str = "".join(text_parts).strip()
    else:
        content_str = str(content).strip()

    if not content_str:
        debug_keys = list(choice_dict.keys()) if isinstance(choice_dict, dict) else []
        raise ValueError(f"OpenAI response content is empty (message keys: {debug_keys})")

    return _parse_json(content_str)


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

