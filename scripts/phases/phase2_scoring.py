#!/usr/bin/env python3
"""Phase 2: Art Museum Scoring (MRD v3 - January 2026).

This module is the THIRD phase of the rebooted MuseumSpark pipeline.
It scores ONLY art museums using LLM-as-judge with curated evidence.

Scoring Fields (MRD Section 4 - Updated January 2026):
    - impressionist_strength: 0-5 scale (0=none, 5=canon-defining)
    - modern_contemporary_strength: 0-5 scale (0=none, 5=canon-defining)
    - historical_context_score: 0-5 scale (0=no context, 5=canon-level importance)
    - eca_score: 0-5 Exhibitions & Curatorial Authority (0=none, 5=field-shaping)
    - collection_based_strength: 0-5 scale (0=no collection, 5=canon-defining)
    - reputation: 0 (International), 1 (National), 2 (Regional), 3 (Local)

Priority Score Formula (computed in Phase 3):
    Primary Art Strength = max(impressionist_strength, modern_contemporary_strength)
    Dual-Strength Bonus = -2 if both >= 4
    ECA Bonus = -1 if eca_score >= 4
    Priority Score = (5 - Primary Art Strength) × 3
                   + (5 - historical_context_score) × 2
                   + (5 - collection_based_strength) × 2
                   + reputation
                   - Dual-Strength Bonus
                   - ECA Bonus

Design Principles:
    1. ELIGIBILITY GATE: Only museums with is_scoreable=True are processed
    2. CURATED EVIDENCE: LLM sees clean, judgment-ready packets (no noise)
    3. JUDGE ROLE: LLM assigns bounded scores, not discovers facts
    4. UNKNOWN ALLOWED: If evidence insufficient, return null (not hallucinated)
    5. DETERMINISTIC PRIORITY: Score computed AFTER LLM returns (Phase 3)

Why This Matters:
    The old pipeline asked LLMs to research AND score simultaneously.
    This caused hallucinations and inconsistent outputs.
    Phase 2 separates concerns: LLM only JUDGES curated evidence.

Usage:
    # Score single museum
    python scripts/phase2_scoring.py --museum-id usa-co-denver-denver-art-museum

    # Score all art museums in a state
    python scripts/phase2_scoring.py --state CO

    # Dry run (show what would be scored)
    python scripts/phase2_scoring.py --state CO --dry-run

    # Use specific provider
    python scripts/phase2_scoring.py --state CO --provider anthropic
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "phase2"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

# =============================================================================
# LLM SCORING PROMPT (Judge Role - MRD v3 Aligned - January 2026)
# =============================================================================

SCORING_SYSTEM_PROMPT = """You are a museum expert and art historian. Your task is to assign bounded scores to art museums based on curated evidence.

IMPORTANT RULES:
1. You are a JUDGE, not a researcher. Only use the evidence provided.
2. Use your expert knowledge combined with the evidence to make informed assessments.
3. For art museums, infer collection strength from museum name, type, and Wikipedia descriptions.
4. All scores must be within their defined ranges (0-5 for art fields, 0-3 for reputation).
5. Be rigorous: only give high scores (4-5) with clear evidence of canon-level or nationally significant holdings.
6. Focus on PERMANENT COLLECTIONS for art strength scores, not temporary exhibitions.
7. ECA (Exhibitions & Curatorial Authority) evaluates PROGRAMMATIC authority only, separate from collections.

SCORING DEFINITIONS (from Museum Requirements Document - January 2026):

=== impressionist_strength (0-5) ===
Purpose: Measures the depth, authority, and scholarly importance of permanent Impressionist holdings.

5 — Canon-Defining Collection
    The museum holds Impressionist works that are field-defining at the national or international level. Holdings contain canonical works (not merely representative examples), and the institution functions as a reference point for Impressionist scholarship and curation.

4 — Major Scholarly Collection
    Deep, high-quality Impressionist holdings with clear scholarly value and national significance. Includes important works and artists, supports sustained research and serious exhibitions.

3 — Strong Regional or Thematic Collection
    Coherent, well-curated Impressionist holdings with recognized strength within a region or theme. Supports credible exhibitions but does not substantially influence national scholarship.

2 — Modest or Supporting Collection
    Impressionist works provide contextual or educational value but lack depth, rarity, or sustained curatorial impact. Works are largely illustrative or supplementary.

1 — Limited Collection Presence
    Small or inconsistent Impressionist holdings with minimal curatorial or scholarly relevance.

0 — No Meaningful Impressionist Holdings
    The institution does not maintain Impressionist works of significance.

=== modern_contemporary_strength (0-5) ===
Purpose: Measures the depth, authority, and scholarly importance of permanent Modern and Contemporary art holdings.

5 — Canon-Defining Collection
    The museum holds Modern/Contemporary works that are field-defining at the national or international level. Holdings contain canonical works, and the institution functions as a reference point for scholarship and curation.

4 — Major Scholarly Collection
    Deep, high-quality Modern/Contemporary holdings with clear scholarly value and national significance. Includes important works and artists, supports sustained research and serious exhibitions.

3 — Strong Regional or Thematic Collection
    Coherent, well-curated Modern/Contemporary holdings with recognized strength within a region or theme. Supports credible exhibitions but does not substantially influence national scholarship.

2 — Modest or Supporting Collection
    Modern/Contemporary works provide contextual or educational value but lack depth, rarity, or sustained curatorial impact. Works are largely illustrative or supplementary.

1 — Limited Collection Presence
    Small or inconsistent Modern/Contemporary holdings with minimal curatorial or scholarly relevance.

0 — No Meaningful Modern/Contemporary Holdings
    The institution does not maintain Modern/Contemporary works of significance.

=== historical_context_score (0-5) ===
Purpose: Measures how essential a museum is to understanding art history, cultural history, or a specific historical narrative, independent of collection size, reputation, or attendance.

5 — Canon-Level Historical Importance
    The museum provides essential, field-defining historical context for understanding a major movement, culture, or historical subject. The institution is a foundational reference point for the subject it interprets.
    NOTE: A score of 5 may qualify a museum for Must-See status.

4 — Nationally Significant Context
    Provides strong historical framing for a major movement, region, or cultural narrative with relevance beyond the local level.

3 — Strong Regional Context
    Anchors the history of a region, city, or cultural community in a meaningful and sustained way.

2 — Local Context
    Interprets or preserves local history or culture with relevance primarily to the immediate community.

1 — Limited Context
    Includes historical interpretation, but it is narrow, secondary, or not a core institutional strength.

0 — No Contextual Framing
    Institution is not historically oriented; history is absent or incidental.

=== eca_score (0-5) - Exhibitions & Curatorial Authority ===
Purpose: Measures curatorial influence that exists OUTSIDE permanent collections, including exhibition authorship, commissioning power, and intellectual leadership. ECA evaluates programmatic authority only.

5 — Field-Shaping Curatorial Authority
    Produces exhibitions, research, or commissions that shape discourse nationally or internationally.

4 — Nationally Recognized Curatorial Program
    Sustained record of original, influential exhibitions with national reach.

3 — Strong Regional Curatorial Program
    Original and respected exhibitions with regional influence.

2 — Competent Exhibition Programming
    Professionally executed but largely derivative or touring exhibitions.

1 — Minimal Curatorial Authority
    Limited scope or intellectual contribution.

0 — No Curatorial Program of Note
    No meaningful exhibition programming or curatorial presence.

=== collection_based_strength (0-5) ===
Purpose: Measures the depth, authority, and scholarly importance of permanent holdings across ALL relevant art categories. This is art-first and does not evaluate popularity, attendance, branding, or reputation.

5 — Canon-Defining Collection
    The museum holds a collection that is field-defining at the national or international level. Its holdings contain canonical works, and the institution functions as a reference point for scholarship, curation, and major exhibitions. The collection demonstrates either encyclopedic breadth across major periods and regions or unquestioned authority within a specific domain.

4 — Major Scholarly Collection
    The museum holds a deep, high-quality collection with clear scholarly value and national significance. The collection includes important works and artists, supports sustained research and serious exhibitions, and meaningfully advances understanding of its field.

3 — Strong Regional or Thematic Collection
    The museum maintains a coherent, well-curated collection with recognized strength within a region, medium, movement, or theme. Holdings support credible exhibitions and interpretation but do not substantially influence national scholarship.

2 — Modest or Supporting Collection
    The collection provides contextual or educational value but lacks depth, rarity, or sustained curatorial impact. Works are largely illustrative or supplementary.

1 — Limited Collection Presence
    The museum holds a small or inconsistent permanent collection with minimal curatorial or scholarly relevance.

0 — No Meaningful Permanent Collection
    The institution does not maintain a permanent collection of significance (e.g., exhibition-only spaces, archives without object collections).

=== reputation (0-3) ===
0 = International (world-renowned, draws global visitors)
1 = National (major US destination, widely known)
2 = Regional (known within multi-state region)
3 = Local (primarily serves local community)

RESPONSE FORMAT:
Return ONLY valid JSON matching this schema:
{
  "impressionist_strength": <0-5 or null>,
  "modern_contemporary_strength": <0-5 or null>,
  "historical_context_score": <0-5 or null>,
  "eca_score": <0-5 or null>,
  "collection_based_strength": <0-5 or null>,
  "reputation": <0-3 or null>,
  "confidence": <1-5>,
  "score_notes": "<2-3 sentences explaining key scores, flag if Historical Context = 5 for Must-See consideration>"
}

If you cannot determine a score from the evidence, use null.
Do not include any text outside the JSON object."""


def get_wikipedia_cache(museum_id: str, state_code: str) -> Optional[dict]:
    """Load Wikipedia cache for a museum if it exists.

    Args:
        museum_id: Museum ID
        state_code: Two-letter state code

    Returns:
        Wikipedia cache dict or None
    """
    cache_file = STATES_DIR / state_code / museum_id / "cache" / "wikipedia.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return None
    return None


def build_evidence_packet(museum: dict, state_code: str = "") -> dict:
    """Build curated evidence packet for LLM scoring.

    This is the KEY function that fixes the old pipeline's noise problem.
    We include ONLY judgment-relevant information.

    INCLUDED:
        - Museum identity (name, city, type)
        - Collection indicators (from existing data)
        - Institutional signals (reputation hints)
        - Wikipedia extract (if available from Phase 1.5)

    EXCLUDED:
        - Provenance logs
        - Failed lookup status
        - Address details
        - CSV metadata
        - Internal notes
    """
    museum_id = museum.get("museum_id", "")

    # Core identity
    evidence = {
        "museum_name": museum.get("museum_name"),
        "city": museum.get("city"),
        "state": museum.get("state_province"),
        "museum_type": museum.get("museum_type"),
        "primary_domain": museum.get("primary_domain"),
    }

    # Wikipedia extract (from Phase 1.5 cache)
    if state_code and museum_id:
        wiki_cache = get_wikipedia_cache(museum_id, state_code)
        if wiki_cache and wiki_cache.get("found") and wiki_cache.get("extract"):
            evidence["wikipedia_summary"] = wiki_cache.get("extract")
            if wiki_cache.get("page_url"):
                evidence["wikipedia_url"] = wiki_cache.get("page_url")

    # Collection indicators (if available)
    if museum.get("topics"):
        evidence["topics"] = museum.get("topics")

    # Existing scores (for context, not to bias)
    existing_scores = {}
    if museum.get("reputation") is not None:
        existing_scores["prior_reputation"] = museum.get("reputation")
    if museum.get("collection_tier") is not None:
        existing_scores["prior_collection_tier"] = museum.get("collection_tier")
    if existing_scores:
        evidence["existing_assessments"] = existing_scores

    # Institutional signals
    signals = {}
    if museum.get("city_tier"):
        signals["city_tier"] = museum.get("city_tier")
    if museum.get("nearby_museum_count") is not None:
        signals["nearby_museums"] = museum.get("nearby_museum_count")
    if signals:
        evidence["institutional_signals"] = signals

    # Website-derived info (if clean)
    if museum.get("website"):
        evidence["website"] = museum.get("website")

    # Notes that might contain collection info (but NOT internal notes)
    public_notes = museum.get("notes")
    if public_notes and "CSV:" not in public_notes and "internal" not in public_notes.lower():
        evidence["notes"] = public_notes[:500]  # Truncate

    return evidence


def call_openai_scoring(
    evidence: dict,
    *,
    api_key: str,
    model: str = "gpt-5.2",
    temperature: float = 0.1,
    max_tokens: int = 500,
) -> dict:
    """Call OpenAI API for scoring."""
    try:
        import openai
    except ImportError:
        raise RuntimeError("openai library not installed. Run: pip install openai")

    client = openai.OpenAI(api_key=api_key)

    user_prompt = f"""Score this art museum based on the evidence below.
Return ONLY valid JSON with the scoring fields.

EVIDENCE:
{json.dumps(evidence, indent=2, ensure_ascii=False)}"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCORING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=max_tokens,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    return json.loads(content)


def call_anthropic_scoring(
    evidence: dict,
    *,
    api_key: str,
    model: str = "claude-3-haiku-20240307",
    temperature: float = 0.1,
    max_tokens: int = 500,
) -> dict:
    """Call Anthropic API for scoring."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic library not installed. Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = f"""Score this art museum based on the evidence below.
Return ONLY valid JSON with the scoring fields.

EVIDENCE:
{json.dumps(evidence, indent=2, ensure_ascii=False)}"""

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SCORING_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.content[0].text
    # Extract JSON from response (Claude sometimes adds text around it)
    start = content.find("{")
    end = content.rfind("}") + 1
    if start >= 0 and end > start:
        content = content[start:end]

    return json.loads(content)


@dataclass
class ScoringResult:
    """Result of scoring a single museum."""
    museum_id: str
    success: bool
    impressionist_strength: Optional[int] = None
    modern_contemporary_strength: Optional[int] = None
    historical_context_score: Optional[int] = None
    eca_score: Optional[int] = None
    collection_based_strength: Optional[int] = None
    reputation: Optional[int] = None
    confidence: Optional[int] = None
    score_notes: Optional[str] = None
    error: Optional[str] = None
    model_used: Optional[str] = None

    def to_patch(self) -> dict:
        """Convert to patch dict for state file update."""
        if not self.success:
            return {}

        patch = {}
        if self.impressionist_strength is not None:
            patch["impressionist_strength"] = self.impressionist_strength
        if self.modern_contemporary_strength is not None:
            patch["modern_contemporary_strength"] = self.modern_contemporary_strength
        if self.historical_context_score is not None:
            patch["historical_context_score"] = self.historical_context_score
        if self.eca_score is not None:
            patch["eca_score"] = self.eca_score
        if self.collection_based_strength is not None:
            patch["collection_based_strength"] = self.collection_based_strength
        if self.reputation is not None:
            patch["reputation"] = self.reputation
        if self.confidence is not None:
            patch["confidence"] = self.confidence
        if self.score_notes:
            patch["score_notes"] = self.score_notes
        if self.model_used:
            patch["scored_by"] = self.model_used
        
        # Compute derived fields (MRD Section 4, Field 9)
        imp = self.impressionist_strength or 0
        mod = self.modern_contemporary_strength or 0
        if imp > mod:
            patch["primary_art_focus"] = "Impressionist"
        elif mod > imp:
            patch["primary_art_focus"] = "Modern/Contemporary"
        elif imp > 0:
            patch["primary_art_focus"] = "Impressionist"  # Default if equal
        
        # Flag potential Must-See candidates (MRD: Historical Context = 5)
        if self.historical_context_score == 5:
            patch["must_see_candidate"] = True

        return patch


@dataclass
class Phase2Stats:
    """Statistics for a Phase 2 run."""
    total_processed: int = 0
    scored: int = 0
    skipped_not_art: int = 0
    skipped_already_scored: int = 0
    failed: int = 0
    flagged: list[str] = field(default_factory=list)


def load_json(path: Path) -> Any:
    """Load JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_utc_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def is_scoreable(museum: dict) -> bool:
    """Check if museum passes eligibility gate.

    From MRD: Only art museums get priority scoring.
    This uses the is_scoreable field set by Phase 1.
    """
    return museum.get("is_scoreable", False) is True


def is_already_scored(museum: dict) -> bool:
    """Check if museum already has LLM scores (MRD v3 fields)."""
    # Consider scored if ANY of the key scoring fields are set
    # MRD v3 adds eca_score and collection_based_strength
    return any([
        museum.get("impressionist_strength") is not None,
        museum.get("modern_contemporary_strength") is not None,
        museum.get("historical_context_score") is not None,
        museum.get("eca_score") is not None,
        museum.get("collection_based_strength") is not None,
    ])


def validate_scores(scores: dict) -> dict:
    """Validate and clamp scores to allowed ranges (MRD v3 - January 2026)."""
    validated = {}

    # 0-5 scale fields (updated from 1-5 in MRD v3)
    for field in ["impressionist_strength", "modern_contemporary_strength", 
                  "historical_context_score", "eca_score", "collection_based_strength"]:
        value = scores.get(field)
        if value is not None:
            if isinstance(value, (int, float)):
                validated[field] = max(0, min(5, int(value)))

    # 1-5 scale for confidence only
    if scores.get("confidence") is not None:
        value = scores.get("confidence")
        if isinstance(value, (int, float)):
            validated["confidence"] = max(1, min(5, int(value)))

    # 0-3 scale fields (reputation only - collection_tier removed in MRD v3)
    if scores.get("reputation") is not None:
        value = scores.get("reputation")
        if isinstance(value, (int, float)):
            validated["reputation"] = max(0, min(3, int(value)))

    # String fields
    if scores.get("score_notes"):
        validated["score_notes"] = str(scores["score_notes"])[:500]

    return validated


def score_museum(
    museum: dict,
    *,
    provider: str,
    api_key: str,
    model: str,
    state_code: str = "",
    use_cache: bool = True,
) -> ScoringResult:
    """Score a single museum using LLM.

    Args:
        museum: Museum record
        provider: "openai" or "anthropic"
        api_key: API key for the provider
        model: Model name to use
        state_code: Two-letter state code (for Wikipedia cache lookup)
        use_cache: Whether to use cached results

    Returns:
        ScoringResult with scores or error
    """
    museum_id = museum.get("museum_id", "")
    result = ScoringResult(museum_id=museum_id, success=False)

    # Check cache
    cache_key = f"{museum_id}_{provider}_{model}".replace("/", "_")
    cache_path = CACHE_DIR / f"{cache_key}.json"

    if use_cache and cache_path.exists():
        try:
            cached = load_json(cache_path)
            result.success = cached.get("success", False)
            result.impressionist_strength = cached.get("impressionist_strength")
            result.modern_contemporary_strength = cached.get("modern_contemporary_strength")
            result.historical_context_score = cached.get("historical_context_score")
            result.eca_score = cached.get("eca_score")
            result.collection_based_strength = cached.get("collection_based_strength")
            result.reputation = cached.get("reputation")
            result.confidence = cached.get("confidence")
            result.score_notes = cached.get("score_notes")
            result.model_used = cached.get("model_used")
            return result
        except Exception:
            pass  # Cache miss, continue with API call

    # Build evidence packet (includes Wikipedia data if available)
    evidence = build_evidence_packet(museum, state_code=state_code)

    try:
        if provider == "openai":
            scores = call_openai_scoring(evidence, api_key=api_key, model=model)
        elif provider == "anthropic":
            scores = call_anthropic_scoring(evidence, api_key=api_key, model=model)
        else:
            result.error = f"Unknown provider: {provider}"
            return result

        # Validate scores
        validated = validate_scores(scores)

        result.success = True
        result.impressionist_strength = validated.get("impressionist_strength")
        result.modern_contemporary_strength = validated.get("modern_contemporary_strength")
        result.historical_context_score = validated.get("historical_context_score")
        result.eca_score = validated.get("eca_score")
        result.collection_based_strength = validated.get("collection_based_strength")
        result.reputation = validated.get("reputation")
        result.confidence = validated.get("confidence")
        result.score_notes = validated.get("score_notes")
        result.model_used = model

    except json.JSONDecodeError as e:
        result.error = f"Invalid JSON from LLM: {str(e)[:100]}"
    except Exception as e:
        result.error = f"API error: {str(e)[:200]}"

    # Cache the result
    try:
        cache_data = {
            "museum_id": museum_id,
            "success": result.success,
            "impressionist_strength": result.impressionist_strength,
            "modern_contemporary_strength": result.modern_contemporary_strength,
            "historical_context_score": result.historical_context_score,
            "eca_score": result.eca_score,
            "collection_based_strength": result.collection_based_strength,
            "reputation": result.reputation,
            "confidence": result.confidence,
            "score_notes": result.score_notes,
            "model_used": result.model_used,
            "error": result.error,
            "scored_at": now_utc_iso(),
        }
        save_json(cache_path, cache_data)
    except Exception:
        pass  # Cache write failure is non-fatal

    return result


def process_state(
    state_code: str,
    *,
    provider: str,
    api_key: str,
    model: str,
    force: bool = False,
    dry_run: bool = False,
    use_cache: bool = True,
    museum_id_filter: Optional[str] = None,
) -> Phase2Stats:
    """Process all art museums in a state for scoring.

    Args:
        state_code: Two-letter state code
        provider: "openai" or "anthropic"
        api_key: API key for the provider
        model: Model name to use
        force: Force re-scoring even if already scored
        dry_run: If True, don't write changes
        use_cache: Use cached LLM results
        museum_id_filter: If set, only process this museum

    Returns:
        Phase2Stats with processing statistics
    """
    stats = Phase2Stats()

    state_file = STATES_DIR / f"{state_code}.json"
    if not state_file.exists():
        print(f"ERROR: State file not found: {state_file}")
        return stats

    state_data = load_json(state_file)
    museums = state_data.get("museums", [])
    total = len(museums)

    print(f"\n[STATE: {state_code}] Processing {total} museums")

    changes_made = False

    for idx, museum in enumerate(museums, 1):
        museum_id = museum.get("museum_id", "")
        stats.total_processed += 1

        # Filter if specific museum requested
        if museum_id_filter and museum_id != museum_id_filter:
            continue

        # ELIGIBILITY GATE: Only score art museums
        if not is_scoreable(museum):
            stats.skipped_not_art += 1
            continue

        # Skip if already scored (unless force)
        if not force and is_already_scored(museum):
            stats.skipped_already_scored += 1
            print(f"  [{idx}/{total}] {museum_id} - SKIPPED (already scored)")
            continue

        print(f"  [{idx}/{total}] {museum_id}...", end=" ", flush=True)

        if dry_run:
            print("WOULD SCORE (dry run)")
            stats.scored += 1
            continue

        result = score_museum(
            museum=museum,
            provider=provider,
            api_key=api_key,
            model=model,
            state_code=state_code,
            use_cache=use_cache,
        )

        if result.success:
            stats.scored += 1

            # Apply scores to museum record
            # NOTE: This preserves all existing fields including planner_* fields from Phase 1.9
            patch = result.to_patch()
            for key, value in patch.items():
                museum[key] = value

            # Update metadata
            museum["scoring_version"] = "phase2_v3_mrd2026"
            museum["score_last_verified"] = now_utc_iso()[:10]
            museum["updated_at"] = now_utc_iso()

            # Add to data_sources
            sources = museum.get("data_sources", [])
            if "llm_scoring" not in sources:
                sources.append("llm_scoring")
                museum["data_sources"] = sources

            changes_made = True

            # Print summary with new MRD v3 fields
            imp = result.impressionist_strength if result.impressionist_strength is not None else "?"
            mod = result.modern_contemporary_strength if result.modern_contemporary_strength is not None else "?"
            hist = result.historical_context_score if result.historical_context_score is not None else "?"
            eca = result.eca_score if result.eca_score is not None else "?"
            cbs = result.collection_based_strength if result.collection_based_strength is not None else "?"
            rep = result.reputation if result.reputation is not None else "?"
            must_see = " ★MUST-SEE" if result.historical_context_score == 5 else ""
            print(f"OK imp={imp} mod={mod} hist={hist} eca={eca} cbs={cbs} rep={rep}{must_see}")
        else:
            stats.failed += 1
            stats.flagged.append(museum_id)
            print(f"FAILED ({result.error})")

    # Save state file if changes were made
    if changes_made and not dry_run:
        state_data["updated_at"] = now_utc_iso()
        save_json(state_file, state_data)
        print(f"\n  Saved changes to {state_file}")

    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 2: Art Museum Scoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Scope selection
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Process all states")
    scope.add_argument("--museum-id", help="Process single museum by ID")

    # LLM options
    parser.add_argument("--provider", default="openai", choices=["openai", "anthropic"],
                        help="LLM provider (default: openai)")
    parser.add_argument("--model", help="Model name (default: provider-specific)")

    # Options
    parser.add_argument("--force", action="store_true", help="Force re-scoring even if already scored")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scored without calling LLM")
    parser.add_argument("--no-cache", action="store_true", help="Don't use cached results")

    args = parser.parse_args()

    # Get API key
    if args.provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        default_model = "gpt-5.2"
        if not api_key:
            print("ERROR: OPENAI_API_KEY environment variable not set")
            return 1
    else:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        default_model = "claude-3-haiku-20240307"
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY environment variable not set")
            return 1

    model = args.model or default_model

    # Determine state codes to process
    state_codes: list[str] = []
    museum_id_filter: Optional[str] = None

    if args.museum_id:
        parts = args.museum_id.split("-")
        if len(parts) >= 2:
            state_codes = [parts[1].upper()]
            museum_id_filter = args.museum_id
        else:
            print(f"ERROR: Invalid museum_id format: {args.museum_id}")
            return 1
    elif args.all_states:
        state_codes = sorted([
            p.stem.upper() for p in STATES_DIR.glob("*.json")
            if len(p.stem) == 2 and p.stem.isalpha()
        ])
    elif args.states:
        state_codes = [s.strip().upper() for s in args.states.split(",")]
    elif args.state:
        state_codes = [args.state.upper()]

    # Create cache and run directories
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"phase2-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 2: Art Museum Scoring")
    print("=" * 60)
    print(f"States: {', '.join(state_codes)}")
    print(f"Provider: {args.provider}")
    print(f"Model: {model}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Run ID: {run_id}")
    print("=" * 60)

    # Process each state
    total_stats = Phase2Stats()

    for state_code in state_codes:
        stats = process_state(
            state_code=state_code,
            provider=args.provider,
            api_key=api_key,
            model=model,
            force=args.force,
            dry_run=args.dry_run,
            use_cache=not args.no_cache,
            museum_id_filter=museum_id_filter,
        )

        total_stats.total_processed += stats.total_processed
        total_stats.scored += stats.scored
        total_stats.skipped_not_art += stats.skipped_not_art
        total_stats.skipped_already_scored += stats.skipped_already_scored
        total_stats.failed += stats.failed
        total_stats.flagged.extend(stats.flagged)

    # Save run summary
    summary = {
        "run_id": run_id,
        "states": state_codes,
        "provider": args.provider,
        "model": model,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "scored": total_stats.scored,
        "skipped_not_art": total_stats.skipped_not_art,
        "skipped_already_scored": total_stats.skipped_already_scored,
        "failed": total_stats.failed,
        "flagged_museums": total_stats.flagged,
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)

    # Print summary
    print("\n" + "=" * 60)
    print("Phase 2 Complete")
    print("=" * 60)
    print(f"  Total processed:      {total_stats.total_processed}")
    print(f"  Scored:               {total_stats.scored}")
    print(f"  Skipped (not art):    {total_stats.skipped_not_art}")
    print(f"  Skipped (has scores): {total_stats.skipped_already_scored}")
    print(f"  Failed:               {total_stats.failed}")

    if total_stats.flagged:
        print(f"\n  FLAGGED ({len(total_stats.flagged)}):")
        for mid in total_stats.flagged[:5]:
            print(f"    - {mid}")
        if len(total_stats.flagged) > 5:
            print(f"    ... and {len(total_stats.flagged) - 5} more")

    print(f"\n  Run directory: {run_dir}")
    print("=" * 60)

    return 0 if total_stats.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
