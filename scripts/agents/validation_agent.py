"""Validation/cleaning agent (fast/cheap model)."""

from __future__ import annotations

import json
from pathlib import Path

from .context import MuseumContext
from .evidence import build_evidence_packet
from .llm import call_anthropic_json, call_openai_json
from .models import EnrichedField, Recommendation, TrustLevel, ValidationAgentOutput
from .utils import heuristic_time_needed, load_env_key


def _system_prompt() -> str:
    return (
        "You are a precise research analyst. "
        "Respond with strictly valid JSON matching the provided schema. "
        "Do not include explanations or markdown."
    )


def _user_prompt(evidence_packet: dict) -> str:
    return (
        "Validate and enrich the museum record using only the evidence provided.\n\n"
        "Rules:\n"
        "- Use field-level provenance (source, trust_level, confidence).\n"
        "- Do not guess missing facts.\n"
        "- For scoring fields, only set if primary_domain is Art.\n"
        "- For time_needed, use only the allowed values.\n"
        "- Extract address information (street, city, postal code) from the website content if present.\n"
        "- Look for common address patterns like 'FIND US', 'LOCATION', 'ADDRESS', 'VISIT US' sections.\n"
        "- Populate the 'notes' field with a 2-3 sentence summary of the museum based on the evidence.\n\n"
        "Evidence Packet:\n"
        f"{json.dumps(evidence_packet, indent=2)}\n\n"
        "Return JSON matching the ValidationAgentOutput schema."
    )


def run_validation_agent(
    *,
    context: MuseumContext,
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    cache_dir: Path,
    use_cache: bool = True,
) -> ValidationAgentOutput:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "validation_v1.json"
    if use_cache and cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        return ValidationAgentOutput.model_validate(cached)

    evidence_packet = build_evidence_packet(context)
    schema = ValidationAgentOutput.model_json_schema()

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
        
        # Inject schema into system prompt for Anthropic
        system_with_schema = _system_prompt() + f"\n\nJSON Schema:\n{json.dumps(schema, indent=2)}"
        
        payload = call_anthropic_json(
            api_key=api_key,
            model=model,
            system=system_with_schema,
            messages=[{"role": "user", "content": _user_prompt(evidence_packet)}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    output = ValidationAgentOutput.model_validate(payload)

    # Deterministic baseline suggestion for time_needed if missing
    if output.state_file_updates.time_needed is None:
        baseline = heuristic_time_needed(context.state_record.get("museum_type"))
        if baseline:
            rec = Recommendation(
                field_name="time_needed",
                current_value=context.state_record.get("time_needed"),
                proposed_value=baseline,
                reason="Deterministic heuristic from museum_type.",
                confidence=3,
                evidence="museum_type keyword mapping",
                source="heuristic",
                trust_level=TrustLevel.LLM_EXTRACTED,
            )
            output.recommendations.append(rec)

    cache_path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
    return output
