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
        "You are a museum subject-matter expert and precise research analyst. Your task is to produce trip-planning, prioritization-ready JSON for art lovers. "
        "Respond with strictly valid JSON matching DeepDiveAgentOutput; do not include explanations or markdown. Produce JSON only. "
        "Emphasize collection strength, art movements, visitor experience, and educational value. Keep text concise: summary_short <= 220 chars, summary_long <= 900 chars, visitor_tips 3-5 items, collection_highlights 3-6 items, signature_artists 5-10. "
        "If evidence text is missing, use your own knowledge conservatively to fill summaries, tips, highlights, and tour_planning_scores; keep scores realistic (no 9-10 without clear rationale) and set confidence to 2-3 for such fields. "
        "Fill tour_planning_scores (1-10) when you have evidence or prior knowledge; include scoring_rationale (2-3 sentences). Skip addresses, phone, hours, URLs, CSV/internal notes, sources_consulted unless obvious, and do not invent fields unrelated to museums."
    )


def _compact_evidence(evidence_packet: dict, *, max_text: int = 900) -> dict:
    """Strip noisy fields and shorten text for lighter prompts."""

    def _trim_text(value: str | None) -> str | None:
        if not value:
            return None
        return value[:max_text].strip()

    # Drop verbose or low-value fields like CSV provenance notes.
    state = {
        k: v
        for k, v in (evidence_packet.get("state_record_subset") or {}).items()
        if k != "notes" and v
    }

    # Remove museum_id to avoid leaking internal IDs; drop nulls later.
    identity = evidence_packet.get("identity") or {}
    identity.pop("museum_id", None)

    slim = {
        "identity": identity,
        "state_record": state,
        "wikipedia_summary": _trim_text(evidence_packet.get("wikipedia_summary")),
        "website_text_snippet": _trim_text(evidence_packet.get("website_text_snippet")),
    }

    def _prune(obj):
        if isinstance(obj, dict):
            return {k: _prune(v) for k, v in obj.items() if v not in (None, "", [], {})}
        if isinstance(obj, list):
            items = [_prune(v) for v in obj if v not in (None, "", [], {})]
            return items
        return obj

    return _prune(slim)


def _user_prompt(evidence_packet: dict) -> str:
    evidence = _compact_evidence(evidence_packet)
    return (
        "Use the trimmed evidence below to populate the JSON. If evidence is sparse, you may rely on your own knowledge; when doing so, keep claims high-level, avoid specifics you cannot support, and lower confidence to 2-3. Do not include null attributes."
        f"{json.dumps(evidence, ensure_ascii=False)}"
    )


def _clamp_confidence(obj: any) -> any:
    """Clamp any 'confidence' fields to the 1-5 range recursively."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "confidence" and isinstance(v, (int, float)):
                out[k] = max(1, min(5, int(v)))
            else:
                out[k] = _clamp_confidence(v)
        return out
    if isinstance(obj, list):
        return [_clamp_confidence(v) for v in obj]
    return obj


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

    if isinstance(payload, dict):
        payload.setdefault("model_used", model)
        if isinstance(payload.get("state_file_updates"), dict):
            payload.setdefault("agent_version", "deep_dive_v1")

    payload = _clamp_confidence(payload)
    output = DeepDiveAgentOutput.model_validate(payload)
    cache_path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
    return output

