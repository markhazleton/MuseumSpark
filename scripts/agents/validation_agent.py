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
        "CRITICAL: Extract ALL available fields from the evidence. Do not leave fields empty if evidence exists.\n\n"
        "REQUIRED FIELDS TO EXTRACT (if evidence exists):\n"
        "1. IDENTITY & LOCATION:\n"
        "   - museum_name: Official name from website/Wikipedia\n"
        "   - city: City name (verify from address, website, or nominatim)\n"
        "   - street_address: Full street address from 'Contact', 'Visit', 'Location', 'Hours', 'About' pages\n"
        "   - postal_code: ZIP/postal code from address\n"
        "   - website: Validated URL (ensure it's active)\n"
        "   - latitude, longitude: Coordinates from nominatim or website\n\n"
        "2. CLASSIFICATION:\n"
        "   - primary_domain: Art|History|Science|Culture|Specialty|Mixed (analyze collection focus)\n"
        "   - museum_type: Specific category (e.g., 'Art Museum', 'History Museum', 'Children\\'s Museum')\n"
        "   - audience_focus: Target audience (e.g., 'General', 'Families', 'Scholars')\n\n"
        "3. QUALITY INDICATORS:\n"
        "   - city_tier: 1-5 (1=major metro, 5=small town) based on city population/prominence\n"
        "   - reputation: 1-5 (1=world-renowned, 5=local) based on Wikipedia presence, awards, size\n"
        "   - collection_tier: 1-5 (1=world-class, 5=modest) based on collection description\n"
        "   - time_needed: '1-2 hours'|'Half day'|'Full day'|'Multiple days' (estimate from collection size)\n\n"
        "4. ART SCORING (ONLY if primary_domain is Art):\n"
        "   - impressionist_strength: 1-5 (strength of impressionist collection)\n"
        "   - modern_contemporary_strength: 1-5 (strength of modern/contemporary collection)\n"
        "   - historical_context_score: 1-5 (historical significance of the institution)\n\n"
        "5. SUMMARY:\n"
        "   - notes: 2-3 sentence summary covering: type of museum, notable collections, unique features\n\n"
        "EXTRACTION RULES:\n"
        "- Confidence scale: 1-5 ONLY (1=very uncertain, 5=highly certain from official source)\n"
        "- Trust levels: Use OFFICIAL_EXTRACT (5) for website data, WIKIPEDIA (3) for Wikipedia, LLM_EXTRACTED (2) for inference\n"
        "- Sources: Be specific ('official_website/visit', 'wikipedia', 'nominatim', 'wikidata')\n"
        "- Do not guess - only extract what you can verify from evidence\n"
        "- CRITICAL: If a field has no evidence, OMIT it entirely from state_file_updates (set to null, not an object with null values)\n"
        "- Check ALL evidence sources: website_text, website_json_ld, wikipedia, wikidata, nominatim\n\n"
        "Evidence Packet:\n"
        f"{json.dumps(evidence_packet, indent=2)}\n\n"
        "Return JSON matching the ValidationAgentOutput schema with as many fields populated as evidence supports."
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
    
    # Save the full prompt for debugging/inspection
    prompt_debug = {
        "museum_id": context.museum_id,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "system_prompt": _system_prompt(),
        "user_prompt": _user_prompt(evidence_packet),
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
            messages=[{"role": "user", "content": _user_prompt(evidence_packet)}],
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
