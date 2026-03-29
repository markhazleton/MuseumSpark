#!/usr/bin/env python3
"""Phase 1.75: Heuristic Scoring Fallback.

Provides reputation and collection_tier scores for museums without LLM scoring.
Uses Wikidata sitelink counts and collection size claims as heuristics.

This phase runs AFTER Phase 2 (LLM scoring) to fill gaps for:
- Non-art museums (history, science, children's museums)
- Museums where LLM scoring failed
- Museums where LLM scoring was skipped

Heuristics:
- Reputation (0-3): Based on Wikidata sitelink counts (international reach)
- Collection Tier (0-3): Based on Wikidata collection size claims (P3172)

Usage:
    # Process single state
    python scripts/phases/phase1_75_heuristic_fallback.py --state CO

    # Process multiple states
    python scripts/phases/phase1_75_heuristic_fallback.py --states CO,UT,WY

    # Process all states
    python scripts/phases/phase1_75_heuristic_fallback.py --all-states

    # Dry run (show what would change)
    python scripts/phases/phase1_75_heuristic_fallback.py --state CO --dry-run

    # Force re-scoring even if heuristic scores exist
    python scripts/phases/phase1_75_heuristic_fallback.py --state CO --force
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
class HeuristicResult:
    """Result of heuristic scoring for a single museum."""
    museum_id: str
    reputation: Optional[int] = None  # 0=International, 1=National, 2=Regional, 3=Local
    collection_tier: Optional[int] = None  # 0=Flagship, 1=Strong, 2=Moderate, 3=Small
    reputation_source: Optional[str] = None
    collection_source: Optional[str] = None
    notes: list[str] = field(default_factory=list)
    
    def has_changes(self) -> bool:
        """Check if any scores were inferred."""
        return self.reputation is not None or self.collection_tier is not None
    
    def to_patch(self) -> dict[str, Any]:
        """Convert to museum record patch."""
        patch: dict[str, Any] = {}
        
        if self.reputation is not None:
            patch["reputation"] = self.reputation
            patch["reputation_source"] = self.reputation_source or "wikidata_heuristic"
        
        if self.collection_tier is not None:
            patch["collection_tier"] = self.collection_tier
            patch["collection_source"] = self.collection_source or "wikidata_heuristic"
        
        return patch


@dataclass
class Phase175Stats:
    """Statistics for a Phase 1.75 run."""
    total_processed: int = 0
    reputation_inferred: int = 0
    collection_tier_inferred: int = 0
    skipped_has_scores: int = 0
    skipped_no_wikidata: int = 0
    errors: int = 0


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


def infer_reputation_from_wikidata(entity: dict[str, Any]) -> Optional[int]:
    """Infer MRD reputation (0=International, 1=National, 2=Regional, 3=Local) from Wikidata.
    
    Heuristics:
    - Has significant sitelinks (50+) → International (0)
    - Has multiple language versions (10-49) → National (1)
    - Has 3-9 language versions → Regional (2)
    - Has <3 language versions → Insufficient evidence (None)
    
    Sitelinks represent Wikipedia articles in different languages, which
    correlates with international recognition and prominence.
    """
    sitelinks = entity.get("sitelinks", {})
    num_sitelinks = len(sitelinks)
    
    if num_sitelinks >= 50:
        return 0  # International (e.g., Metropolitan Museum, Louvre)
    elif num_sitelinks >= 10:
        return 1  # National (e.g., major national museums)
    elif num_sitelinks >= 3:
        return 2  # Regional (e.g., significant state/regional museums)
    
    # <3 sitelinks: insufficient evidence for reputation scoring
    return None


def infer_collection_tier_from_wikidata(entity: dict[str, Any]) -> Optional[int]:
    """Infer MRD collection_tier (0=Flagship, 1=Strong, 2=Moderate, 3=Small) from Wikidata.
    
    Heuristics:
    - Uses "collection size" claim (P3172) if available
    - Thresholds:
      - 100k+ items → Flagship (0)
      - 10k-100k items → Strong (1)
      - 1k-10k items → Moderate (2)
      - <1k items → Small (3)
    - No data → Cannot determine (None)
    """
    # P3172: collection size (number of items in collection)
    claims = entity.get("claims", {})
    
    if "P3172" not in claims:
        return None
    
    # Get first collection size claim
    p3172_claims = claims["P3172"]
    if not p3172_claims:
        return None
    
    try:
        # Extract numeric value from claim
        mainsnak = p3172_claims[0].get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        value = datavalue.get("value", {})
        
        # Handle both direct numbers and amounts
        if isinstance(value, (int, float)):
            size = int(value)
        elif isinstance(value, dict) and "amount" in value:
            # Amount is usually a string like "+100000"
            amount = value["amount"]
            if isinstance(amount, str):
                amount = amount.lstrip("+")
            size = int(float(amount))
        else:
            return None
        
        # Apply thresholds
        if size >= 100_000:
            return 0  # Flagship
        elif size >= 10_000:
            return 1  # Strong
        elif size >= 1_000:
            return 2  # Moderate
        else:
            return 3  # Small
    
    except (ValueError, KeyError, TypeError):
        return None


def get_wikidata_entity(museum_id: str, state_code: str) -> Optional[dict[str, Any]]:
    """Load Wikidata entity from Phase 0.5 cache."""
    # Wikidata cache is stored in museum-specific directories
    # Pattern: data/states/{STATE}/{museum_hash}/cache/wikidata/{qid}.json
    
    # We need to find the museum's cache directory
    # For now, we'll search for wikidata cache files
    state_dir = STATES_DIR.parent / "states" / state_code
    
    if not state_dir.exists():
        return None
    
    # Look for wikidata cache in all museum directories
    for museum_dir in state_dir.iterdir():
        if not museum_dir.is_dir():
            continue
        
        wikidata_cache_dir = museum_dir / "cache" / "wikidata"
        if not wikidata_cache_dir.exists():
            continue
        
        # Check all QID files in this museum's wikidata cache
        for qid_file in wikidata_cache_dir.glob("Q*.json"):
            try:
                entity = load_json(qid_file)
                # Verify this entity might match (basic sanity check)
                if entity.get("id"):
                    return entity
            except Exception:
                continue
    
    return None


def process_museum(
    museum: dict[str, Any],
    state_code: str,
    *,
    force: bool = False,
) -> HeuristicResult:
    """Apply heuristic scoring fallback for a single museum.
    
    Args:
        museum: Museum record
        state_code: State code for cache lookup
        force: Force re-scoring even if scores exist
        
    Returns:
        HeuristicResult with inferred scores
    """
    museum_id = museum.get("museum_id", "unknown")
    result = HeuristicResult(museum_id=museum_id)
    
    # Check if museum already has scores (unless force=True)
    has_reputation = museum.get("reputation") is not None
    has_collection_tier = museum.get("collection_tier") is not None
    
    if not force and has_reputation and has_collection_tier:
        result.notes.append("Already has both scores")
        return result
    
    # Get Wikidata QID from museum record
    wikidata_id = museum.get("wikidata_id")
    
    if not wikidata_id:
        result.notes.append("No Wikidata ID")
        return result
    
    # Try to load entity from Phase 0.5 cache
    # First try direct path if we have it
    museum_hash = museum_id.replace("usa-", "").replace("-", "_")
    wikidata_cache_path = (
        STATES_DIR.parent / "states" / state_code / museum_hash / 
        "cache" / "wikidata" / f"{wikidata_id}.json"
    )
    
    entity = None
    if wikidata_cache_path.exists():
        try:
            entity = load_json(wikidata_cache_path)
        except Exception as e:
            result.notes.append(f"Error loading Wikidata cache: {e}")
            return result
    
    if not entity:
        result.notes.append(f"Wikidata entity {wikidata_id} not cached (run Phase 0.5 first)")
        return result
    
    # Infer reputation if missing or forced
    if not has_reputation or force:
        reputation = infer_reputation_from_wikidata(entity)
        if reputation is not None:
            result.reputation = reputation
            result.reputation_source = "wikidata_heuristic"
            
            reputation_labels = {0: "International", 1: "National", 2: "Regional", 3: "Local"}
            sitelinks_count = len(entity.get("sitelinks", {}))
            result.notes.append(
                f"Inferred reputation={reputation} ({reputation_labels[reputation]}) "
                f"from {sitelinks_count} Wikidata sitelinks"
            )
        else:
            result.notes.append("Insufficient Wikidata sitelinks for reputation inference")
    
    # Infer collection_tier if missing or forced
    if not has_collection_tier or force:
        collection_tier = infer_collection_tier_from_wikidata(entity)
        if collection_tier is not None:
            result.collection_tier = collection_tier
            result.collection_source = "wikidata_heuristic"
            
            tier_labels = {0: "Flagship", 1: "Strong", 2: "Moderate", 3: "Small"}
            result.notes.append(
                f"Inferred collection_tier={collection_tier} ({tier_labels[collection_tier]}) "
                f"from Wikidata collection size"
            )
        else:
            result.notes.append("No Wikidata collection size (P3172) for tier inference")
    
    return result


def process_state(
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Phase175Stats:
    """Process all museums in a state.
    
    Args:
        state_code: Two-letter state code
        force: Force re-scoring even if scores exist
        dry_run: Don't write changes
        
    Returns:
        Phase175Stats with processing statistics
    """
    stats = Phase175Stats()
    
    state_path = STATES_DIR / f"{state_code}.json"
    if not state_path.exists():
        print(f"⚠️  State file not found: {state_path}")
        return stats
    
    # Load state data
    state_data = load_json(state_path)
    museums = state_data.get("museums", [])
    
    print(f"[STATE: {state_code}] Processing {len(museums)} museums")
    
    updated_museums = []
    
    for museum in museums:
        stats.total_processed += 1
        museum_id = museum.get("museum_id", "unknown")
        
        # Check if already has both scores
        has_reputation = museum.get("reputation") is not None
        has_collection_tier = museum.get("collection_tier") is not None
        
        if not force and has_reputation and has_collection_tier:
            stats.skipped_has_scores += 1
            updated_museums.append(museum)
            continue
        
        # Check if has Wikidata ID
        if not museum.get("wikidata_id"):
            stats.skipped_no_wikidata += 1
            updated_museums.append(museum)
            continue
        
        # Process museum
        try:
            result = process_museum(museum, state_code, force=force)
            
            # Apply patch if changes were made
            if result.has_changes():
                patch = result.to_patch()
                updated_museum = {**museum, **patch}
                updated_museum["updated_at"] = now_utc_iso()
                
                # Track what was inferred
                if result.reputation is not None:
                    stats.reputation_inferred += 1
                if result.collection_tier is not None:
                    stats.collection_tier_inferred += 1
                
                # Print progress
                changes = []
                if result.reputation is not None:
                    changes.append(f"reputation={result.reputation}")
                if result.collection_tier is not None:
                    changes.append(f"collection_tier={result.collection_tier}")
                
                print(f"  [{stats.total_processed}/{len(museums)}] {museum_id} - {', '.join(changes)}")
                
                updated_museums.append(updated_museum)
            else:
                updated_museums.append(museum)
        
        except Exception as e:
            stats.errors += 1
            print(f"  ✗ Error processing {museum_id}: {e}")
            updated_museums.append(museum)
    
    # Write updated state file
    if not dry_run and (stats.reputation_inferred > 0 or stats.collection_tier_inferred > 0):
        state_data["museums"] = updated_museums
        state_data["updated_at"] = now_utc_iso()
        save_json(state_path, state_data)
        print(f"✓ Updated {state_path}")
    
    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 1.75: Heuristic Scoring Fallback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    # Scope selection (required)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes (e.g., CO,UT,WY)")
    scope.add_argument("--all-states", action="store_true", help="Process all states")
    
    # Options
    parser.add_argument("--force", action="store_true", help="Force re-scoring even if scores exist")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes")
    
    args = parser.parse_args()
    
    # Determine state codes to process
    states: list[str] = []
    
    if args.all_states:
        # Get all state files
        states = sorted([
            p.stem.upper() for p in STATES_DIR.glob("*.json")
            if len(p.stem) == 2 and p.stem.isalpha()
        ])
    elif args.states:
        states = [s.strip().upper() for s in args.states.split(",")]
    elif args.state:
        states = [args.state.upper()]
    
    # Create run directory
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"phase1_75-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Print header
    print("=" * 60)
    print("Phase 1.75: Heuristic Scoring Fallback")
    print("=" * 60)
    print(f"States: {', '.join(states)}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Run ID: {run_id}")
    print("=" * 60)
    print()
    
    # Process each state
    total_stats = Phase175Stats()
    
    for state_code in states:
        stats = process_state(state_code, force=args.force, dry_run=args.dry_run)
        
        # Aggregate statistics
        total_stats.total_processed += stats.total_processed
        total_stats.reputation_inferred += stats.reputation_inferred
        total_stats.collection_tier_inferred += stats.collection_tier_inferred
        total_stats.skipped_has_scores += stats.skipped_has_scores
        total_stats.skipped_no_wikidata += stats.skipped_no_wikidata
        total_stats.errors += stats.errors
    
    # Print summary
    print()
    print("=" * 60)
    print("Phase 1.75 Complete")
    print("=" * 60)
    print(f"  Total processed:          {total_stats.total_processed}")
    print(f"  Reputation inferred:      {total_stats.reputation_inferred}")
    print(f"  Collection tier inferred: {total_stats.collection_tier_inferred}")
    print(f"  Skipped (has scores):     {total_stats.skipped_has_scores}")
    print(f"  Skipped (no Wikidata):    {total_stats.skipped_no_wikidata}")
    print(f"  Errors:                   {total_stats.errors}")
    print()
    print(f"  Run directory: {run_dir}")
    print("=" * 60)
    
    # Save summary
    summary = {
        "run_id": run_id,
        "states": states,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "reputation_inferred": total_stats.reputation_inferred,
        "collection_tier_inferred": total_stats.collection_tier_inferred,
        "skipped_has_scores": total_stats.skipped_has_scores,
        "skipped_no_wikidata": total_stats.skipped_no_wikidata,
        "errors": total_stats.errors,
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)
    
    return 0 if total_stats.errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
