"""Deep dive agent for rich museum summaries and scoring."""

from __future__ import annotations

import json
from pathlib import Path

from .context import MuseumContext
from .evidence import build_evidence_packet
from .llm import call_anthropic_json, call_openai_json
from .models import DeepDiveAgentOutput
from .utils import load_env_key


def _system_prompt() -> str:
    return (
        "You are a precise research analyst. "
        "Respond with strictly valid JSON matching the provided schema. "
        "Do not include explanations or markdown."
    )


def _user_prompt(evidence_packet: dict) -> str:
    return (
        "Research this museum using only the evidence provided.\n\n"
        "Rules:\n"
        "- Use field-level provenance (source, trust_level, confidence).\n"
        "- Do not guess missing facts.\n"
        "- If this is not an art museum, do not provide art_scoring.\n"
        "- summary_short should be 100-500 chars.\n"
        "- summary_long should be <= 2000 chars.\n"
        "- Extract address information (street, city, postal code) from the website content if present.\n"
        "- Look for common address patterns like 'FIND US', 'LOCATION', 'ADDRESS', 'VISIT US' sections.\n\n"
        "Evidence Packet:\n"
        f"{json.dumps(evidence_packet, indent=2)}\n\n"
        "Return JSON matching the DeepDiveAgentOutput schema."
    )


def run_deep_dive_agent(
    *,
    context: MuseumContext,
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    cache_dir: Path,
    use_cache: bool = True,
) -> DeepDiveAgentOutput:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "deep_dive_v1.json"
    if use_cache and cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        return DeepDiveAgentOutput.model_validate(cached)

    evidence_packet = build_evidence_packet(context, max_chars=12000)
    schema = DeepDiveAgentOutput.model_json_schema()

    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": _user_prompt(evidence_packet)},
    ]

    if provider == "openai":
        api_key = load_env_key("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        payload = call_openai_json(
            api_key=api_key,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_schema=schema,
        )
    elif provider == "anthropic":
        api_key = load_env_key("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        payload = call_anthropic_json(
            api_key=api_key,
            model=model,
            system=_system_prompt(),
            messages=[{"role": "user", "content": _user_prompt(evidence_packet)}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    output = DeepDiveAgentOutput.model_validate(payload)
    cache_path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
    return output

