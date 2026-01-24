#!/usr/bin/env python3
"""Phase 3: Priority Score Calculation (MRD v2 Reboot).

This module is the FOURTH phase of the rebooted MuseumSpark pipeline.
It computes the deterministic priority score using the MRD formula.

IMPORTANT: This phase is DETERMINISTIC. No LLM involvement.
The priority score is computed entirely from the scoring fields set in Phase 2.

Priority Score Formula (from MRD Section 5):
    Primary Art Strength = max(impressionist_strength, modern_contemporary_strength)

    Priority Score =
        (6 - Primary Art Strength) * 3
        + (6 - Historical Context Score) * 2
        + Reputation Penalty (0-3)
        + Collection Penalty (0-3)
        - Dual Strength Bonus (2 if both >= 4)
        - Nearby Cluster Bonus (1 if 3+ museums in city)

    Lower score = Higher priority for visiting

Design Principles:
    1. DETERMINISTIC: No LLM, no external API calls
    2. NULL HANDLING: If required fields are null, priority_score stays null
    3. AUDITABLE: Score breakdown logged for verification
    4. IDEMPOTENT: Re-running produces identical results

Usage:
    # Compute priority scores for a state
    python scripts/phase3_priority.py --state CO

    # Compute for all states
    python scripts/phase3_priority.py --all-states

    # Dry run (show scores without saving)
    python scripts/phase3_priority.py --state CO --dry-run

    # Force recalculation
    python scripts/phase3_priority.py --state CO --force
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of priority score calculation."""
    museum_id: str
    can_score: bool = False

    # Input values
    impressionist_strength: Optional[int] = None
    modern_contemporary_strength: Optional[int] = None
    historical_context_score: Optional[int] = None
    reputation: Optional[int] = None
    collection_tier: Optional[int] = None
    nearby_museum_count: Optional[int] = None

    # Computed values
    primary_art_strength: Optional[int] = None
    art_component: Optional[int] = None
    history_component: Optional[int] = None
    reputation_penalty: Optional[int] = None
    collection_penalty: Optional[int] = None
    dual_strength_bonus: int = 0
    nearby_cluster_bonus: int = 0

    # Final scores
    priority_score: Optional[int] = None  # Hidden gem score (lower = better)
    overall_quality_score: Optional[int] = None  # Best museum score (higher = better)
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "museum_id": self.museum_id,
            "can_score": self.can_score,
            "priority_score": self.priority_score,
            "overall_quality_score": self.overall_quality_score,
            "breakdown": {
                "primary_art_strength": self.primary_art_strength,
                "art_component": self.art_component,
                "history_component": self.history_component,
                "reputation_penalty": self.reputation_penalty,
                "collection_penalty": self.collection_penalty,
                "dual_strength_bonus": self.dual_strength_bonus,
                "nearby_cluster_bonus": self.nearby_cluster_bonus,
            },
            "missing_fields": self.missing_fields,
        }


@dataclass
class Phase3Stats:
    """Statistics for a Phase 3 run."""
    total_processed: int = 0
    scored: int = 0
    skipped_not_art: int = 0
    skipped_missing_fields: int = 0
    already_scored: int = 0


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


def compute_priority_score(museum: dict) -> ScoreBreakdown:
    """Compute priority score using MRD formula.

    From MRD Section 5:
        Priority Score (lower = better):

        Primary Art Strength = max(Impressionist Strength, Modern/Contemporary Strength)

        Dual-Strength Bonus:
        If Impressionist Strength >= 4 AND Modern/Contemporary Strength >= 4 -> subtract 2

        Formula:
        Priority Score =
            (6 - Primary Art Strength) * 3
            + (6 - Historical Context Score) * 2
            + Reputation Penalty (0=International, 1=National, 2=Regional, 3=Local)
            + Collection Penalty (0=Flagship, 1=Strong, 2=Moderate, 3=Small)
            - Dual Strength Bonus (if applicable)
            - Nearby Cluster Bonus (1 if 3+ museums in same city)

    Args:
        museum: Museum record with scoring fields

    Returns:
        ScoreBreakdown with computed score and component breakdown
    """
    museum_id = museum.get("museum_id", "")
    breakdown = ScoreBreakdown(museum_id=museum_id)

    # Get input values
    breakdown.impressionist_strength = museum.get("impressionist_strength")
    breakdown.modern_contemporary_strength = museum.get("modern_contemporary_strength")
    breakdown.historical_context_score = museum.get("historical_context_score")
    breakdown.reputation = museum.get("reputation")
    breakdown.collection_tier = museum.get("collection_tier")
    breakdown.nearby_museum_count = museum.get("nearby_museum_count")

    # Check required fields for scoring
    # Per MRD: We need at least art strength and reputation/collection to score
    required_for_scoring = []

    # Need at least one art strength
    imp = breakdown.impressionist_strength
    mod = breakdown.modern_contemporary_strength
    if imp is None and mod is None:
        breakdown.missing_fields.append("art_strength (both imp and mod are null)")

    # Reputation and collection_tier are required
    if breakdown.reputation is None:
        breakdown.missing_fields.append("reputation")
    if breakdown.collection_tier is None:
        breakdown.missing_fields.append("collection_tier")

    # If missing critical fields, we cannot score
    if breakdown.missing_fields:
        breakdown.can_score = False
        return breakdown

    # Compute primary art strength
    # Use 1 as default if one is null (conservative - assume weak)
    imp_val = imp if imp is not None else 1
    mod_val = mod if mod is not None else 1
    breakdown.primary_art_strength = max(imp_val, mod_val)

    # Compute art component: (6 - Primary Art Strength) * 3
    breakdown.art_component = (6 - breakdown.primary_art_strength) * 3

    # Compute history component: (6 - Historical Context Score) * 2
    # Default to 3 (middle) if not scored
    hist = breakdown.historical_context_score if breakdown.historical_context_score is not None else 3
    breakdown.history_component = (6 - hist) * 2

    # Reputation penalty (already 0-3 from MRD)
    breakdown.reputation_penalty = breakdown.reputation

    # Collection penalty (already 0-3 from MRD)
    breakdown.collection_penalty = breakdown.collection_tier

    # Dual strength bonus: 2 if both >= 4
    if imp is not None and mod is not None and imp >= 4 and mod >= 4:
        breakdown.dual_strength_bonus = 2

    # Nearby cluster bonus: 1 if 3+ museums in same city
    nearby = breakdown.nearby_museum_count or 0
    if nearby >= 3:
        breakdown.nearby_cluster_bonus = 1

    # Compute final score
    breakdown.priority_score = (
        breakdown.art_component
        + breakdown.history_component
        + breakdown.reputation_penalty
        + breakdown.collection_penalty
        - breakdown.dual_strength_bonus
        - breakdown.nearby_cluster_bonus
    )

    # Compute overall quality score (higher = better)
    # This inverts the logic to reward strong collections and reputation
    # Quality = Art Strength + Reputation + Collection Tier + Bonuses
    breakdown.overall_quality_score = (
        breakdown.primary_art_strength * 3  # Higher art strength = better
        + (3 - breakdown.reputation)  # 0=International gets 3 points, 3=Local gets 0
        + (3 - breakdown.collection_tier)  # 0=Flagship gets 3 points, 3=Small gets 0
        + breakdown.dual_strength_bonus  # Add bonus for excellence in both
    )

    breakdown.can_score = True
    return breakdown


def derive_primary_art(museum: dict, breakdown: ScoreBreakdown) -> Optional[str]:
    """Derive primary_art field from strengths.

    From MRD Section 4:
        Primary Art Focus: String: "Impressionist" or "Modern/Contemporary"
        Chosen as the stronger of the two strengths
    """
    imp = breakdown.impressionist_strength
    mod = breakdown.modern_contemporary_strength

    if imp is None and mod is None:
        return None

    imp_val = imp if imp is not None else 0
    mod_val = mod if mod is not None else 0

    if imp_val > mod_val:
        return "Impressionist"
    elif mod_val > imp_val:
        return "Modern/Contemporary"
    elif imp_val == mod_val and imp_val > 0:
        # Tie - default to Modern/Contemporary (more common focus)
        return "Modern/Contemporary"

    return None


def process_state(
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Phase3Stats:
    """Process all museums in a state for priority scoring.

    Args:
        state_code: Two-letter state code
        force: Force recalculation even if already scored
        dry_run: If True, don't write changes

    Returns:
        Phase3Stats with processing statistics
    """
    stats = Phase3Stats()

    state_file = STATES_DIR / f"{state_code}.json"
    if not state_file.exists():
        print(f"ERROR: State file not found: {state_file}")
        return stats

    state_data = load_json(state_file)
    museums = state_data.get("museums", [])
    total = len(museums)

    print(f"\n[STATE: {state_code}] Processing {total} museums")

    changes_made = False
    breakdowns: list[dict] = []

    for idx, museum in enumerate(museums, 1):
        museum_id = museum.get("museum_id", "")
        stats.total_processed += 1

        # Only score art museums
        if not museum.get("is_scoreable", False):
            stats.skipped_not_art += 1
            continue

        # Skip if already has priority_score (unless force)
        if not force and museum.get("priority_score") is not None:
            stats.already_scored += 1
            print(f"  [{idx}/{total}] {museum_id} - SKIPPED (already scored: {museum.get('priority_score')})")
            continue

        # Compute priority score
        breakdown = compute_priority_score(museum)
        breakdowns.append(breakdown.to_dict())

        if not breakdown.can_score:
            stats.skipped_missing_fields += 1
            missing = ", ".join(breakdown.missing_fields)
            print(f"  [{idx}/{total}] {museum_id} - CANNOT SCORE (missing: {missing})")
            continue

        stats.scored += 1

        # Derive primary_art
        primary_art = derive_primary_art(museum, breakdown)

        # Print score breakdown
        print(f"  [{idx}/{total}] {museum_id}")
        print(f"           Hidden Gem: art={breakdown.art_component} + hist={breakdown.history_component} + rep={breakdown.reputation_penalty} + tier={breakdown.collection_penalty} - dual={breakdown.dual_strength_bonus} - cluster={breakdown.nearby_cluster_bonus}")
        print(f"           = PRIORITY {breakdown.priority_score} (lower=better hidden gem)")
        print(f"           Overall Quality: {breakdown.overall_quality_score} (higher=better overall)")

        if not dry_run:
            # Apply scores to museum record (preserves all existing fields including planner_* fields from Phase 1.9)
            museum["priority_score"] = breakdown.priority_score
            museum["overall_quality_score"] = breakdown.overall_quality_score
            if primary_art:
                museum["primary_art"] = primary_art
            museum["scoring_version"] = "mrd_v2"
            museum["updated_at"] = now_utc_iso()
            changes_made = True

    # Save state file if changes were made
    if changes_made and not dry_run:
        state_data["updated_at"] = now_utc_iso()
        save_json(state_file, state_data)
        print(f"\n  Saved changes to {state_file}")
    elif dry_run and stats.scored > 0:
        print(f"\n  [DRY RUN] Would save changes to {state_file}")

    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 3: Priority Score Calculation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Scope selection
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Process all states")

    # Options
    parser.add_argument("--force", action="store_true", help="Force recalculation even if already scored")
    parser.add_argument("--dry-run", action="store_true", help="Show scores without saving")

    args = parser.parse_args()

    # Determine state codes to process
    state_codes: list[str] = []

    if args.all_states:
        state_codes = sorted([
            p.stem.upper() for p in STATES_DIR.glob("*.json")
            if len(p.stem) == 2 and p.stem.isalpha()
        ])
    elif args.states:
        state_codes = [s.strip().upper() for s in args.states.split(",")]
    elif args.state:
        state_codes = [args.state.upper()]

    # Create run directory for logging
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"phase3-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 3: Priority Score Calculation")
    print("=" * 60)
    print(f"States: {', '.join(state_codes)}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Run ID: {run_id}")
    print("=" * 60)

    # Process each state
    total_stats = Phase3Stats()

    for state_code in state_codes:
        stats = process_state(
            state_code=state_code,
            force=args.force,
            dry_run=args.dry_run,
        )

        total_stats.total_processed += stats.total_processed
        total_stats.scored += stats.scored
        total_stats.skipped_not_art += stats.skipped_not_art
        total_stats.skipped_missing_fields += stats.skipped_missing_fields
        total_stats.already_scored += stats.already_scored

    # Save run summary
    summary = {
        "run_id": run_id,
        "states": state_codes,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "scored": total_stats.scored,
        "skipped_not_art": total_stats.skipped_not_art,
        "skipped_missing_fields": total_stats.skipped_missing_fields,
        "already_scored": total_stats.already_scored,
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)

    # Print summary
    print("\n" + "=" * 60)
    print("Phase 3 Complete")
    print("=" * 60)
    print(f"  Total processed:        {total_stats.total_processed}")
    print(f"  Scored:                 {total_stats.scored}")
    print(f"  Skipped (not art):      {total_stats.skipped_not_art}")
    print(f"  Skipped (missing data): {total_stats.skipped_missing_fields}")
    print(f"  Already scored:         {total_stats.already_scored}")
    print(f"\n  Run directory: {run_dir}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
