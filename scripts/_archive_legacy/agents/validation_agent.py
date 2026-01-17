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


def _user_prompt(evidence_packet: dict, model: str) -> str:
    return (
        "Validate and enrich the museum record using only the evidence provided.\n\n"
        "YOUR FOCUS: Extract ONLY fields where you have clear evidence. Skip fields with no evidence.\n\n"
        "FIELDS TO EXTRACT (only if evidence exists):\n"
        "1. IDENTITY & LOCATION:\n"
        "   - museum_name: Official name from website/Wikipedia\n"
        "   - city: City name\n"
        "   - street_address: Full street address\n"
        "   - postal_code: ZIP/postal code\n"
        "   - website: Validated URL\n"
        "   - latitude, longitude: Coordinates\n\n"
        "2. CLASSIFICATION:\n"
        "   - primary_domain: Art|History|Science|Culture|Specialty|Mixed\n"
        "   - museum_type: Specific category\n"
        "   - audience_focus: Target audience\n\n"
        "3. QUALITY INDICATORS:\n"
        "   - city_tier: 1-5 (1=major metro, 5=small town)\n"
        "   - reputation: 1-5 (1=world-renowned, 5=local)\n"
        "   - collection_tier: 1-5 (1=world-class, 5=modest)\n"
        "   - time_needed: '1-2 hours'|'Half day'|'Full day'|'Multiple days'\n\n"
        "4. SUMMARY:\n"
        "   - notes: 2-3 sentence summary if you have collection/context info\n\n"
        "CRITICAL FORMATTING RULES:\n"
        "✓ CORRECT - Field with evidence:\n"
        "  \"museum_name\": {\n"
        "    \"value\": \"Denver Art Museum\",\n"
        "    \"source\": \"official_website\",\n"
        "    \"trust_level\": 5,\n"
        "    \"confidence\": 5\n"
        "  }\n\n"
        "✓ CORRECT - Field with no evidence:\n"
        "  \"museum_name\": null\n\n"
        "✗ WRONG - Never do this:\n"
        "  \"museum_name\": {\"value\": null}  ❌ INVALID\n"
        "  \"museum_name\": {\"value\": \"Not provided\"}  ❌ INVALID\n\n"
        "If you don't have evidence for a field, set it to null (not an object).\n"
        "Only create EnrichedField objects when you have actual data.\n\n"
        "Trust levels: OFFICIAL_EXTRACT (5), WIKIPEDIA (3), LLM_EXTRACTED (2)\n"
        "Confidence: 1-5 (how certain are you about this value)\n\n"
        "REQUIRED TOP-LEVEL FIELDS:\n"
        f"  \"confidence\": 1-5 (overall confidence in this analysis)\n"
        f"  \"model_used\": \"{model}\"\n"
        "  \"needs_deep_dive\": true|false (if scoring/deeper analysis needed)\n\n"
        "Evidence Packet:\n"
        f"{json.dumps(evidence_packet, indent=2)}\n\n"
        "Return JSON with properly formatted EnrichedField objects (or null if no evidence)."
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
        {"role": "user", "content": _user_prompt(evidence_packet, model)},
    ]
    
    # Save the full prompt for debugging/inspection
    prompt_debug = {
        "museum_id": context.museum_id,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "system_prompt": _system_prompt(),
        "user_prompt": _user_prompt(evidence_packet, model),
        "evidence_packet": evidence_packet,
    }
    (cache_dir / "validation_prompt.json").write_text(
        json.dumps(prompt_debug, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

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
            messages=[{"role": "user", "content": _user_prompt(evidence_packet, model)}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Save the raw response for debugging/inspection
    response_debug = {
        "museum_id": context.museum_id,
        "provider": provider,
        "model": model,
        "raw_response": payload,
    }
    (cache_dir / "validation_response.json").write_text(
        json.dumps(response_debug, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

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
