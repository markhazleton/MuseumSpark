#!/usr/bin/env python3
"""Phase 3: Priority Score and Outcome Tier Calculation (MRD v3.1.T).

This module is the FOURTH phase of the rebooted MuseumSpark pipeline.
It computes the deterministic priority score and outcome tier using the MRD v3.1.T formula.

IMPORTANT: This phase is DETERMINISTIC. No LLM involvement.
The priority score is computed entirely from the scoring fields set in Phase 2.

Priority Score Formula (MRD v3.1.T Section 5):

    Step 1: Collection-Based PAS
        Collection-Based PAS = MAX(impressionist_strength, modern_contemporary_strength, hat_strength)

    Step 2: Effective PAS
        Effective PAS = MAX(Collection-Based PAS, eca_score)

    Step 3: Dual-Strength Bonus
        -2 if impressionist_strength >= 3 AND modern_contemporary_strength >= 3
         0 otherwise
        (HAT does not qualify; threshold is >=3 not >=4)

    Step 4: Reputation Penalty
        International = +0, National = +0, Regional = +2, Supra-Local = +3, Local = +4

    Step 5: Collection Penalty
        Flagship = +0, Strong = +0, Moderate = +2, Small = +4

    Step 6: Priority Score
        MAX(1,
            (6 - Effective PAS) * 2
          + (6 - Historical Context Score)
          + Reputation Penalty
          + Collection Penalty
          + Dual-Strength Bonus
        )

Outcome Tier Assignment (MRD v3.1.T Section 6):
    Must-See       — Collection-Based PAS = 5, OR Historical Context = 5
    High Priority  — Priority Score <= 9; OR Flagship + PAS=4; OR ECA>=4; OR HC=4+Nat/Int rep
    Regionally Important — Score 10-15 AND Regional rep AND strong art/HC reference
    Detour         — Specialization signal AND (Effective PAS >= 3 OR HC >= 3)
    Consider       — Proximity-dependent value
    Background     — Default; limited travel gravity

Design Principles:
    1. DETERMINISTIC: No LLM, no external API calls
    2. NULL HANDLING: If required fields are null, priority_score stays null
    3. AUDITABLE: Score breakdown logged for verification
    4. IDEMPOTENT: Re-running produces identical results

Usage:
    # Compute priority scores for a state
    python scripts/phases/phase3_priority.py --state CO

    # Compute for all states
    python scripts/phases/phase3_priority.py --all-states

    # Dry run (show scores without saving)
    python scripts/phases/phase3_priority.py --state CO --dry-run

    # Force recalculation
    python scripts/phases/phase3_priority.py --state CO --force
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

SCORING_VERSION = "v3.1.T"

# Reputation penalty mapping (MRD v3.1.T Section 5)
REPUTATION_PENALTY: dict[str, int] = {
    "International": 0,
    "National": 0,
    "Regional": 2,
    "Supra-Local": 3,
    "Local": 4,
}

# Legacy integer reputation penalty mapping (backwards compat)
REPUTATION_PENALTY_INT: dict[int, int] = {
    0: 0,  # International
    1: 0,  # National
    2: 2,  # Regional
    3: 3,  # Supra-Local
    4: 4,  # Local
}

# Collection penalty mapping (MRD v3.1.T Section 5)
COLLECTION_PENALTY: dict[str, int] = {
    "Flagship": 0,
    "Strong": 0,
    "Moderate": 2,
    "Small": 4,
}

# Legacy integer collection penalty mapping (backwards compat)
COLLECTION_PENALTY_INT: dict[int, int] = {
    0: 0,  # Flagship
    1: 0,  # Strong
    2: 2,  # Moderate
    3: 4,  # Small
}


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of priority score calculation (MRD v3.1.T)."""
    museum_id: str
    can_score: bool = False

    # Input values
    impressionist_strength: Optional[int] = None
    modern_contemporary_strength: Optional[int] = None
    hat_strength: Optional[int] = None
    historical_context_score: Optional[int] = None
    eca_score: Optional[int] = None
    reputation_level: Optional[str] = None  # Primary: string
    reputation_int: Optional[int] = None    # Legacy fallback
    collection_level: Optional[str] = None  # Primary: string
    collection_tier_int: Optional[int] = None  # Legacy fallback

    # Computed intermediate values
    collection_based_pas: Optional[int] = None
    effective_pas: Optional[int] = None
    dual_strength_bonus: int = 0

    # Penalty components
    reputation_penalty: Optional[int] = None
    collection_penalty: Optional[int] = None

    # Final scores
    priority_score: Optional[int] = None
    outcome_tier: Optional[str] = None
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "museum_id": self.museum_id,
            "can_score": self.can_score,
            "priority_score": self.priority_score,
            "outcome_tier": self.outcome_tier,
            "breakdown": {
                "impressionist_strength": self.impressionist_strength,
                "modern_contemporary_strength": self.modern_contemporary_strength,
                "hat_strength": self.hat_strength,
                "collection_based_pas": self.collection_based_pas,
                "eca_score": self.eca_score,
                "effective_pas": self.effective_pas,
                "historical_context_score": self.historical_context_score,
                "dual_strength_bonus": self.dual_strength_bonus,
                "reputation_level": self.reputation_level,
                "reputation_penalty": self.reputation_penalty,
                "collection_level": self.collection_level,
                "collection_penalty": self.collection_penalty,
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


def resolve_reputation_penalty(museum: dict) -> tuple[Optional[str], Optional[int]]:
    """Resolve reputation level and penalty from museum record.

    Prefers reputation_level (string), falls back to legacy reputation (integer).

    Returns:
        (reputation_label, penalty) or (None, None) if unresolvable
    """
    # Prefer string reputation_level (v3.1.T)
    rep_level = museum.get("reputation_level")
    if rep_level and rep_level in REPUTATION_PENALTY:
        return rep_level, REPUTATION_PENALTY[rep_level]

    # Also check planner_reputation_level
    planner_rep = museum.get("planner_reputation_level")
    if planner_rep and planner_rep in REPUTATION_PENALTY:
        return planner_rep, REPUTATION_PENALTY[planner_rep]

    # Fall back to legacy integer reputation field
    rep_int = museum.get("reputation")
    if rep_int is not None and rep_int in REPUTATION_PENALTY_INT:
        label = {0: "International", 1: "National", 2: "Regional", 3: "Supra-Local", 4: "Local"}.get(rep_int)
        return label, REPUTATION_PENALTY_INT[rep_int]

    return None, None


def resolve_collection_penalty(museum: dict) -> tuple[Optional[str], Optional[int]]:
    """Resolve collection level and penalty from museum record.

    Prefers collection_level (string), falls back to legacy collection_tier (integer).

    Returns:
        (collection_label, penalty) or (None, None) if unresolvable
    """
    # Prefer string collection_level (v3.1.T)
    coll_level = museum.get("collection_level")
    if coll_level and coll_level in COLLECTION_PENALTY:
        return coll_level, COLLECTION_PENALTY[coll_level]

    # Also check planner_collection_level
    planner_coll = museum.get("planner_collection_level")
    if planner_coll and planner_coll in COLLECTION_PENALTY:
        return planner_coll, COLLECTION_PENALTY[planner_coll]

    # Fall back to legacy integer collection_tier field
    coll_int = museum.get("collection_tier")
    if coll_int is not None and coll_int in COLLECTION_PENALTY_INT:
        label = {0: "Flagship", 1: "Strong", 2: "Moderate", 3: "Small"}.get(coll_int)
        return label, COLLECTION_PENALTY_INT[coll_int]

    return None, None


def compute_priority_score(museum: dict) -> ScoreBreakdown:
    """Compute priority score using MRD v3.1.T formula.

    Formula:
        Collection-Based PAS = MAX(impressionist_strength, modern_contemporary_strength, hat_strength)
        Effective PAS = MAX(Collection-Based PAS, eca_score)
        Dual-Strength Bonus = -2 if imp >= 3 AND mod >= 3, else 0
        Reputation Penalty = International/National=0, Regional=2, Supra-Local=3, Local=4
        Collection Penalty = Flagship/Strong=0, Moderate=2, Small=4
        Priority Score = MAX(1, (6 - Effective PAS)*2 + (6 - HC) + Rep + Coll + Dual)

    Args:
        museum: Museum record with scoring fields

    Returns:
        ScoreBreakdown with computed score and component breakdown
    """
    museum_id = museum.get("museum_id", "")
    breakdown = ScoreBreakdown(museum_id=museum_id)

    # Gather art strength inputs
    breakdown.impressionist_strength = museum.get("impressionist_strength") or museum.get("planner_impressionist_strength")
    breakdown.modern_contemporary_strength = museum.get("modern_contemporary_strength") or museum.get("planner_modern_contemporary_strength")
    breakdown.hat_strength = museum.get("hat_strength") or museum.get("planner_traditional_strength")
    breakdown.historical_context_score = museum.get("historical_context_score") or museum.get("planner_historical_context")
    breakdown.eca_score = museum.get("eca_score") or museum.get("planner_exhibition_advantage")

    imp = breakdown.impressionist_strength
    mod = breakdown.modern_contemporary_strength
    hat = breakdown.hat_strength
    hc = breakdown.historical_context_score
    eca = breakdown.eca_score

    # Resolve reputation and collection
    rep_label, rep_penalty = resolve_reputation_penalty(museum)
    coll_label, coll_penalty = resolve_collection_penalty(museum)

    breakdown.reputation_level = rep_label
    breakdown.reputation_penalty = rep_penalty
    breakdown.collection_level = coll_label
    breakdown.collection_penalty = coll_penalty

    # Check required fields
    if imp is None and mod is None and hat is None:
        breakdown.missing_fields.append("art_strength (impressionist, modern_contemporary, and hat are all null)")
    if rep_penalty is None:
        breakdown.missing_fields.append("reputation_level (or legacy reputation)")
    if coll_penalty is None:
        breakdown.missing_fields.append("collection_level (or legacy collection_tier)")

    if breakdown.missing_fields:
        breakdown.can_score = False
        return breakdown

    # Step 1: Collection-Based PAS = MAX(imp, mod, hat)
    art_values = [v for v in [imp, mod, hat] if v is not None]
    breakdown.collection_based_pas = max(art_values) if art_values else 0

    # Step 2: Effective PAS = MAX(Collection-Based PAS, ECA)
    eca_val = eca if eca is not None else 0
    breakdown.effective_pas = max(breakdown.collection_based_pas, eca_val)

    # Step 3: Dual-Strength Bonus (-2 if both imp >= 3 AND mod >= 3)
    imp_val = imp if imp is not None else 0
    mod_val = mod if mod is not None else 0
    if imp_val >= 3 and mod_val >= 3:
        breakdown.dual_strength_bonus = -2

    # Step 4 & 5: Reputation + Collection penalties already resolved above

    # Step 6: Historical context (default to 0 if null — no history = no penalty)
    hc_val = hc if hc is not None else 0

    # Priority Score = MAX(1, (6 - Effective PAS)*2 + (6 - HC) + Rep + Coll + Dual)
    raw_score = (
        (6 - breakdown.effective_pas) * 2
        + (6 - hc_val)
        + breakdown.reputation_penalty
        + breakdown.collection_penalty
        + breakdown.dual_strength_bonus
    )
    breakdown.priority_score = max(1, raw_score)
    breakdown.can_score = True
    return breakdown


def assign_outcome_tier(museum: dict, breakdown: ScoreBreakdown) -> str:
    """Assign Outcome Tier per MRD v3.1.T Section 6 (deterministic).

    Args:
        museum: Museum record
        breakdown: Computed score breakdown

    Returns:
        Outcome tier string
    """
    cbp = breakdown.collection_based_pas or 0
    hc = breakdown.historical_context_score or 0
    ps = breakdown.priority_score or 99
    eca = breakdown.eca_score or 0
    rep = breakdown.reputation_level or "Local"
    coll = breakdown.collection_level or "Small"
    eff_pas = breakdown.effective_pas or 0

    # Must-See: Collection-Based PAS = 5, OR HC = 5
    if cbp >= 5 or hc >= 5:
        return "Must-See"

    # High Priority: PS <= 9, OR Flagship+PAS=4, OR ECA>=4, OR HC=4+Nat/Int
    if ps <= 9:
        return "High Priority"
    if coll == "Flagship" and cbp >= 4:
        return "High Priority"
    if eca >= 4:
        return "High Priority"
    if hc >= 4 and rep in ("National", "International"):
        return "High Priority"

    # Regionally Important: Score 10-15 AND Regional AND art/HC reference
    if 10 <= ps <= 15 and rep == "Regional":
        if eff_pas in (3, 4) or hc in (3, 4):
            return "Regionally Important"

    # Detour and Consider: check for specialization signals in additional_labels or planner fields
    is_specialized = _is_specialized(museum)
    if is_specialized and (eff_pas >= 3 or hc >= 3):
        return "Detour"

    if is_specialized or eff_pas >= 2 or hc >= 2 or cbp >= 2:
        return "Consider"

    # Background: default
    return "Background"


def _is_specialized(museum: dict) -> bool:
    """Check if museum has specialization signals for Detour eligibility."""
    labels = (museum.get("additional_labels") or museum.get("planner_consider_label") or "").lower()
    specialized_keywords = [
        "specialized art site",
        "specialized cultural site",
        "you won't see this again",
        "you wont see this again",
        "kunsthalle",
    ]
    return any(kw in labels for kw in specialized_keywords)


def derive_primary_art(breakdown: ScoreBreakdown) -> Optional[str]:
    """Derive primary_art field from the strongest collection axis."""
    candidates = []
    if breakdown.impressionist_strength is not None:
        candidates.append(("Impressionist", breakdown.impressionist_strength))
    if breakdown.modern_contemporary_strength is not None:
        candidates.append(("Modern/Contemporary", breakdown.modern_contemporary_strength))
    if breakdown.hat_strength is not None:
        candidates.append(("Historical Art Traditions", breakdown.hat_strength))

    if not candidates:
        return None

    # Return the category with the highest strength
    best = max(candidates, key=lambda x: x[1])
    return best[0] if best[1] > 0 else None


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

        # Assign outcome tier
        outcome_tier = assign_outcome_tier(museum, breakdown)

        # Derive primary_art
        primary_art = derive_primary_art(breakdown)

        # Print score breakdown
        print(f"  [{idx}/{total}] {museum_id}")
        print(f"           cbPAS={breakdown.collection_based_pas} effPAS={breakdown.effective_pas} HC={breakdown.historical_context_score}")
        print(f"           rep={breakdown.reputation_level}(+{breakdown.reputation_penalty}) coll={breakdown.collection_level}(+{breakdown.collection_penalty}) dual={breakdown.dual_strength_bonus}")
        print(f"           => PRIORITY {breakdown.priority_score} | TIER: {outcome_tier}")

        if not dry_run:
            # Apply scores to museum record
            museum["collection_based_pas"] = breakdown.collection_based_pas
            museum["effective_pas"] = breakdown.effective_pas
            museum["priority_score"] = breakdown.priority_score
            museum["outcome_tier"] = outcome_tier
            if primary_art:
                museum["primary_art"] = primary_art
            museum["scoring_version"] = SCORING_VERSION
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
        description="Phase 3: Priority Score and Outcome Tier Calculation (MRD v3.1.T)",
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
    print("Phase 3: Priority Score and Outcome Tier Calculation")
    print(f"Version: MRD {SCORING_VERSION}")
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
        "scoring_version": SCORING_VERSION,
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
