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
        "Deep research on this museum using only the evidence provided.\n\n"
        "CRITICAL: Extract ALL available information. This is the premium enrichment pass.\n\n"
        "REQUIRED EXTRACTIONS:\n"
        "1. CORE FIELDS (same as validation agent - verify and enhance):\n"
        "   - All identity, location, classification, and quality fields\n"
        "   - art_scoring (ONLY for art museums): impressionist_strength, modern_contemporary_strength, historical_context_score\n\n"
        "2. RICH CONTENT (REQUIRED - extract from evidence):\n"
        "   - summary_short: 100-500 chars, compelling 1-sentence hook\n"
        "   - summary_long: 500-2000 chars, comprehensive overview covering history, collection, significance\n"
        "   - collection_highlights: List 3-10 notable pieces/collections with titles and descriptions\n"
        "   - signature_artists: List 5-20 key artists represented (for art museums)\n"
        "   - visitor_tips: 3-7 practical tips (best time to visit, must-see exhibits, skip lines, etc.)\n"
        "   - best_for: Who should visit? (e.g., 'Art lovers', 'Families with kids', 'History buffs')\n"
        "   - historical_significance: Why is this museum important? When founded? Key milestones?\n"
        "   - architectural_notes: Notable building features, architect, architectural style\n"
        "   - curatorial_approach: Exhibition style, educational programs, research focus\n\n"
        "3. ART SCORING (art museums only):\n"
        "   - Provide ArtScoring object with detailed 1-5 ratings and justification\n\n"
        "EXTRACTION RULES:\n"
        "- Confidence scale: 1-5 ONLY (never use percentages or 0-100 scale)\n"
        "- Sources: Be specific and cite where each fact came from\n"
        "- Trust levels: OFFICIAL_EXTRACT (5) for website, WIKIPEDIA (3), LLM_EXTRACTED (2) for synthesis\n"
        "- CRITICAL: If a field has no evidence, OMIT it entirely from state_file_updates (set to null, not an object with null values)\n"
        "- Use ALL evidence: website_text, website_json_ld, wikipedia_summary, wikidata, subpages_scraped\n"
        "- sources_consulted: List all evidence sources you actually used\n\n"
        "Evidence Packet:\n"
        f"{json.dumps(evidence_packet, indent=2)}\n\n"
        "Return JSON matching the DeepDiveAgentOutput schema with MAXIMUM fields populated."
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

