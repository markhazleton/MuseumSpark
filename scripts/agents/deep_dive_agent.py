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
        "Analyze this museum for tour planning and visitor guidance.\n\n"
        "YOUR MISSION: Score this museum across multiple dimensions to enable queries like:\n"
        "  'Show me best Impressionist museums in Southeast (impressionist_score >= 7)'\n"
        "  'Plan Contemporary Art road trip from DC to Miami (contemporary_score >= 8)'\n"
        "  'Family-friendly art museums with high educational value'\n\n"
        "SCORING FOCUS (1-10 scale, required for tour_planning_scores):\n\n"
        "1. ART MOVEMENT SPECIALIZATIONS (art museums only, omit if not applicable):\n"
        "   - contemporary_score (1950-present): Rothko, Warhol, Pollock, contemporary installations\n"
        "   - modern_score (1860s-1950): Cubism, Surrealism, early abstraction, Picasso era\n"
        "   - impressionist_score: Monet, Renoir, Degas, Post-Impressionists like Van Gogh\n"
        "   - expressionist_score: German Expressionism, Munch, Kandinsky, Die Brücke\n"
        "   - classical_score: Renaissance, Baroque, Neoclassical works\n\n"
        "2. GEOGRAPHIC/CULTURAL FOCUS (1-10, all relevant museums):\n"
        "   - american_art_score: American artists, Hudson River School, regionalism\n"
        "   - european_art_score: European masters and movements\n"
        "   - asian_art_score: Asian traditions, ceramics, scrolls\n"
        "   - african_art_score: African & Indigenous art traditions\n\n"
        "3. MEDIUM SPECIALIZATIONS (1-10):\n"
        "   - painting_score, sculpture_score, decorative_arts_score, photography_score\n\n"
        "4. COLLECTION CHARACTERISTICS (1-10, REQUIRED for all museums):\n"
        "   - collection_depth: 1=narrow specialist (single artist/period), 10=encyclopedic (all periods/regions)\n"
        "   - collection_quality: 1=local importance, 5=strong regional, 8=nationally significant, 10=world-class\n"
        "   - exhibition_frequency: How often new temporary exhibitions (1=rarely, 10=constantly rotating)\n\n"
        "5. VISITOR EXPERIENCE (1-10, REQUIRED):\n"
        "   - family_friendly_score: Interactive exhibits, kids programs, accessibility\n"
        "   - educational_value_score: Docent tours, labels, educational programs\n"
        "   - architecture_score: Is the building itself notable? Frank Lloyd Wright = 10, generic = 3\n\n"
        "SCORING GUIDELINES:\n"
        "  • 1-3: Minimal/No focus    • 4-6: Moderate representation    • 7-8: Strong focus    • 9-10: World-class\n"
        "  • Trust your training: You KNOW what makes Impressionism vs Expressionism\n"
        "  • Use evidence: 'world-class Wedgwood collection' → decorative_arts_score: 9\n"
        "  • Be discriminating: Not every museum deserves 8+\n"
        "  • OMIT scores when insufficient evidence (better null than guess)\n\n"
        "RICH CONTENT (still required):\n"
        "  - summary_short: 1-sentence compelling hook (100-500 chars)\n"
        "  - summary_long: Comprehensive overview (500-2000 chars)\n"
        "  - collection_highlights: 3-10 must-see pieces/collections\n"
        "  - signature_artists: 5-20 key artists (for art museums)\n"
        "  - visitor_tips: 3-7 practical tips (timing, must-sees, skip-the-line)\n"
        "  - best_for: Target audience (e.g., 'Serious art historians', 'Families with young kids')\n"
        "  - scoring_rationale: 2-3 sentences explaining KEY scores\n\n"
        "DO NOT try to extract:\n"
        "  ❌ Addresses, phone numbers, hours (APIs handle this)\n"
        "  ❌ City names, museum names (already in database)\n"
        "  ❌ Website URLs (already have them)\n\n"
        "EXTRACTION RULES:\n"
        "  - Confidence scale: 1-5 (1=guess, 3=inferred, 5=explicit in source)\n"
        "  - OMIT fields with no evidence (return null, not empty object)\n"
        "  - sources_consulted: List what you actually used\n\n"
        "Evidence Packet:\n"
        f"{json.dumps(evidence_packet, indent=2)}\n\n"
        "Return JSON with tour_planning_scores fully populated for filtering and routing!"
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
    (cache_dir / "deep_dive_prompt.json").write_text(
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

    # Save the raw response for debugging/inspection
    response_debug = {
        "museum_id": context.museum_id,
        "provider": provider,
        "model": model,
        "raw_response": payload,
    }
    (cache_dir / "deep_dive_response.json").write_text(
        json.dumps(response_debug, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    output = DeepDiveAgentOutput.model_validate(payload)
    cache_path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
    return output

