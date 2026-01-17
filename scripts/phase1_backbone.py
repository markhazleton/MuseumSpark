#!/usr/bin/env python3
"""Phase 1: Backbone Enrichment (MRD v2 Reboot).

This module is the SECOND phase of the rebooted MuseumSpark pipeline.
It populates deterministic backbone fields for ALL museums (not just art museums).

Fields Populated:
    - city_tier: 1 (Major hub), 2 (Medium city), 3 (Small town)
    - time_needed: "Quick stop (<1 hr)", "Half day", "Full day"
    - nearby_museum_count: Count of other museums in the same city
    - museum_type: Normalized classification

Design Principles:
    1. NO LLM involvement - all fields are deterministic
    2. city_tier uses population lookup + manual cultural hub list
    3. time_needed is derived from museum_type
    4. nearby_museum_count is computed from the state file itself
    5. Idempotent - re-running doesn't thrash existing data

Why This Matters:
    These backbone fields are required for ALL museums (not just art museums).
    They enable city-level planning and filtering even for non-scored museums.

Usage:
    # Process single state
    python scripts/phase1_backbone.py --state CO

    # Process all states
    python scripts/phase1_backbone.py --all-states

    # Dry run (show what would change)
    python scripts/phase1_backbone.py --state CO --dry-run

    # Force recalculation even if fields exist
    python scripts/phase1_backbone.py --state CO --force
"""

from __future__ import annotations

import argparse
import json
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

# =============================================================================
# CITY TIER CLASSIFICATION (MRD Section 3)
# =============================================================================

# Tier 1: Major metropolitan hubs (population 500K+ or major cultural significance)
TIER_1_CITIES = {
    # Top 50 US cities by population
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Washington", "Boston", "Detroit", "Nashville",
    "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee",
    "Albuquerque", "Tucson", "Fresno", "Sacramento", "Kansas City", "Atlanta",
    "Miami", "Minneapolis", "Cleveland", "New Orleans", "Oakland", "Tampa",
    "Honolulu", "Omaha", "Wichita", "Arlington", "Raleigh", "Virginia Beach",
    "Long Beach", "Colorado Springs", "Tulsa", "Oklahoma City",
    # Major cultural hubs regardless of population
    "Santa Fe", "Williamsburg", "Cambridge", "Berkeley", "Ann Arbor",
    "Sarasota", "Palm Beach", "Pasadena", "Santa Barbara", "Savannah",
    "Charleston", "Newport", "Providence", "New Haven", "Pittsburgh",
    "St. Louis", "Cincinnati", "Buffalo", "Richmond", "Hartford",
}

# Tier 2: Medium cities (population 50K-500K)
# These are computed dynamically, but we have some manual overrides
TIER_2_CITIES = {
    # State capitals and regional centers
    "Boise", "Salt Lake City", "Des Moines", "Madison", "Little Rock",
    "Jackson", "Montgomery", "Tallahassee", "Springfield", "Lansing",
    "Harrisburg", "Trenton", "Albany", "Concord", "Montpelier", "Augusta",
    "Olympia", "Salem", "Carson City", "Helena", "Bismarck", "Pierre",
    "Cheyenne", "Topeka", "Lincoln", "Jefferson City", "Frankfort",
    # College towns with cultural significance
    "Ithaca", "Chapel Hill", "Charlottesville", "Princeton", "Amherst",
    "Hanover", "Oberlin", "Bloomington", "Eugene", "Boulder", "Durham",
    # Regional art centers
    "Bentonville", "Marfa", "Taos", "Sedona", "Asheville", "Woodstock",
    "Ogunquit", "Provincetown", "Carmel", "Laguna Beach", "St. Petersburg",
}

# =============================================================================
# TIME NEEDED CLASSIFICATION (MRD Section 4)
# =============================================================================

# Keywords that indicate visit duration based on museum type
TIME_NEEDED_RULES = {
    "Full day": [
        "encyclopedic", "natural history", "science center", "large complex",
        "museum campus", "smithsonian", "metropolitan", "national gallery",
    ],
    "Quick stop (<1 hr)": [
        "historic house", "historic site", "house museum", "small gallery",
        "local history", "heritage center", "memorial", "monument",
    ],
    # Default for most museums
    "Half day": [
        "art museum", "art center", "contemporary art", "modern art",
        "history museum", "science museum", "children's museum",
        "university museum", "gallery", "cultural center",
    ],
}

# Museum types that are scoreable (art museums only)
SCOREABLE_TYPES = {
    "Fine Art",
    "Contemporary Art",
    "Modern Art",
    "University Art Museum",
    "Encyclopedic Art Museum",
    "Art Museum",
    "Art Center",
    "Art Gallery",
}

# All valid normalized museum types (for reference)
VALID_MUSEUM_TYPES = {
    # Art (scoreable)
    "Art Museum", "Fine Art", "Contemporary Art", "Modern Art",
    "Art Center", "Art Gallery", "University Art Museum", "Encyclopedic Art Museum",
    # History
    "History Museum", "Historic House", "Historic Site", "Historic Preservation",
    "Heritage Museum", "Heritage Center",
    # Science
    "Science Museum", "Science Center", "Natural History Museum",
    # Children's
    "Children's Museum",
    # Nature & Wildlife
    "Botanical Garden", "Nature Center", "Zoo/Aquarium",
    # Cultural
    "Cultural Center",
    # General & Specialty
    "General Museum", "Specialty Museum", "Memorial", "Hall of Fame",
    # Unknown
    "Unknown",
}

# Normalized museum type mappings (keys are lowercase for matching)
MUSEUM_TYPE_NORMALIZATIONS = {
    # Art museums
    "art museum": "Art Museum",
    "art": "Art Museum",
    "fine art": "Fine Art",
    "contemporary art": "Contemporary Art",
    "modern art": "Modern Art",
    "art center": "Art Center",
    "art gallery": "Art Gallery",
    "university art museum": "University Art Museum",
    "university museum": "University Art Museum",
    "college art museum": "University Art Museum",
    "art (encyclopedic)": "Encyclopedic Art Museum",
    "art (modern/contemporary)": "Contemporary Art",
    # History museums
    "history museum": "History Museum",
    "history": "History Museum",
    "historic house": "Historic House",
    "historic site": "Historic Site",
    "historic preservation": "Historic Preservation",
    "heritage museum": "Heritage Museum",
    "heritage center": "Heritage Center",
    # Science museums
    "science museum": "Science Museum",
    "science center": "Science Center",
    "science & technology museum or planetarium": "Science Museum",
    "natural history": "Natural History Museum",
    "natural history museum": "Natural History Museum",
    # Children's museums
    "children's museum": "Children's Museum",
    "childrens museum": "Children's Museum",
    "kids museum": "Children's Museum",
    # Nature & Wildlife
    "arboretum, botanical garden, or nature center": "Botanical Garden",
    "botanical garden": "Botanical Garden",
    "nature center": "Nature Center",
    "zoo, aquarium, or wildlife conservation": "Zoo/Aquarium",
    "zoo": "Zoo/Aquarium",
    "aquarium": "Zoo/Aquarium",
    # Cultural centers
    "cultural center": "Cultural Center",
    "cultural museum": "Cultural Center",
    "ethnic museum": "Cultural Center",
    # General
    "general museum": "General Museum",
    "general": "General Museum",
    # Specialty
    "specialty museum": "Specialty Museum",
    "specialty": "Specialty Museum",
    "memorial": "Memorial",
    "hall of fame": "Hall of Fame",
    # Unknown
    "unknown": "Unknown",
}


@dataclass
class BackboneResult:
    """Result of backbone enrichment for a single museum."""
    museum_id: str
    fields_updated: list[str] = field(default_factory=list)
    fields_skipped: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class Phase1Stats:
    """Statistics for a Phase 1 run."""
    total_processed: int = 0
    museums_updated: int = 0
    fields_updated: int = 0
    skipped: int = 0


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


def is_placeholder(value: Any) -> bool:
    """Check if a value is missing or a placeholder."""
    if value is None:
        return True
    if isinstance(value, str):
        placeholders = {"", "tbd", "unknown", "n/a", "null", "pending", "none"}
        return value.strip().lower() in placeholders
    return False


def compute_city_tier(city: str, state: Optional[str] = None) -> int:
    """Compute city tier using lookup tables.

    MRD Definition:
        Tier 1: Major hub (population 500K+ or major cultural significance)
        Tier 2: Medium city (population 50K-500K)
        Tier 3: Small town (population <50K)

    Returns:
        1, 2, or 3
    """
    if not city:
        return 3  # Default to small town if no city

    city_normalized = city.strip()

    # Check Tier 1 (major hubs)
    if city_normalized in TIER_1_CITIES:
        return 1

    # Check Tier 2 (medium cities / cultural centers)
    if city_normalized in TIER_2_CITIES:
        return 2

    # Default to Tier 3 (small town)
    # In production, we could do a population lookup here
    return 3


def compute_time_needed(museum_type: Optional[str], museum_name: Optional[str] = None) -> str:
    """Compute time needed based on museum type.

    MRD Definition:
        "Quick stop (<1 hr)": Small galleries, historic houses
        "Half day": Standard art/history museums
        "Full day": Large encyclopedic museums, museum complexes

    Returns:
        One of: "Quick stop (<1 hr)", "Half day", "Full day"
    """
    # Combine museum_type and museum_name for keyword matching
    text = ""
    if museum_type:
        text += museum_type.lower() + " "
    if museum_name:
        text += museum_name.lower()

    text = text.strip()
    if not text:
        return "Half day"  # Default

    # Check keywords in order of specificity
    for duration, keywords in TIME_NEEDED_RULES.items():
        if any(kw in text for kw in keywords):
            return duration

    # Default to Half day for most museums
    return "Half day"


def normalize_museum_type(museum_type: Optional[str]) -> Optional[str]:
    """Normalize museum type to standard values.

    Returns:
        Normalized type string or None if unknown
    """
    if not museum_type:
        return None

    type_lower = museum_type.strip().lower()

    # Direct lookup
    if type_lower in MUSEUM_TYPE_NORMALIZATIONS:
        return MUSEUM_TYPE_NORMALIZATIONS[type_lower]

    # Partial match
    for key, normalized in MUSEUM_TYPE_NORMALIZATIONS.items():
        if key in type_lower:
            return normalized

    # Return original if no match (preserve existing data)
    return museum_type.strip()


def is_scoreable_type(museum_type: Optional[str]) -> bool:
    """Check if museum type is scoreable (art museums only).

    From MRD: Only art museums get priority scoring.
    Non-art museums remain in dataset for city-level planning.
    """
    if not museum_type:
        return False

    normalized = normalize_museum_type(museum_type)
    if not normalized:
        return False

    return normalized in SCOREABLE_TYPES


def compute_nearby_museum_count(museums: list[dict], current_museum_id: str, current_city: str) -> int:
    """Compute count of other museums in the same city.

    MRD Definition:
        Integer count of other museums in the same city from the master list.
        Excludes the current row itself.
    """
    if not current_city:
        return 0

    city_lower = current_city.strip().lower()
    count = 0

    for museum in museums:
        if museum.get("museum_id") == current_museum_id:
            continue  # Skip self

        museum_city = museum.get("city", "")
        if museum_city and museum_city.strip().lower() == city_lower:
            count += 1

    return count


def enrich_museum_backbone(
    museum: dict,
    all_museums: list[dict],
    *,
    force: bool = False,
) -> BackboneResult:
    """Enrich a single museum with backbone fields.

    Args:
        museum: Museum record to enrich
        all_museums: All museums in the state (for nearby count)
        force: If True, overwrite existing values

    Returns:
        BackboneResult with details of what was updated
    """
    museum_id = museum.get("museum_id", "")
    result = BackboneResult(museum_id=museum_id)

    city = museum.get("city", "")
    state = museum.get("state_province", "")
    museum_type = museum.get("museum_type", "")
    museum_name = museum.get("museum_name", "")

    # 1. City Tier
    current_tier = museum.get("city_tier")
    if force or is_placeholder(current_tier) or current_tier is None:
        new_tier = compute_city_tier(city, state)
        museum["city_tier"] = new_tier
        result.fields_updated.append(f"city_tier={new_tier}")
    else:
        result.fields_skipped.append("city_tier (exists)")

    # 2. Time Needed
    current_time = museum.get("time_needed")
    if force or is_placeholder(current_time):
        new_time = compute_time_needed(museum_type, museum_name)
        museum["time_needed"] = new_time
        result.fields_updated.append(f"time_needed={new_time}")
    else:
        result.fields_skipped.append("time_needed (exists)")

    # 3. Nearby Museum Count (always recompute - it's derived)
    new_count = compute_nearby_museum_count(all_museums, museum_id, city)
    old_count = museum.get("nearby_museum_count")
    if old_count != new_count:
        museum["nearby_museum_count"] = new_count
        result.fields_updated.append(f"nearby_museum_count={new_count}")
    else:
        result.fields_skipped.append(f"nearby_museum_count (unchanged={new_count})")

    # 4. Normalize Museum Type
    current_type = museum.get("museum_type")
    if current_type:
        normalized_type = normalize_museum_type(current_type)
        if normalized_type and normalized_type != current_type:
            museum["museum_type"] = normalized_type
            result.fields_updated.append(f"museum_type={normalized_type}")
            result.notes.append(f"Normalized from '{current_type}'")

    # 5. Mark if scoreable (for Phase 2 filtering)
    is_art = is_scoreable_type(museum.get("museum_type"))
    museum["is_scoreable"] = is_art
    if is_art:
        result.notes.append("Marked as scoreable (art museum)")

    return result


def process_state(
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Phase1Stats:
    """Process all museums in a state for backbone enrichment.

    Args:
        state_code: Two-letter state code (e.g., "CO")
        force: Force recalculation even if fields exist
        dry_run: If True, don't write changes

    Returns:
        Phase1Stats with processing statistics
    """
    stats = Phase1Stats()

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

        result = enrich_museum_backbone(museum, museums, force=force)

        if result.fields_updated:
            stats.museums_updated += 1
            stats.fields_updated += len(result.fields_updated)
            changes_made = True

            # Print summary
            updates_str = ", ".join(result.fields_updated[:3])
            if len(result.fields_updated) > 3:
                updates_str += f" (+{len(result.fields_updated) - 3} more)"
            print(f"  [{idx}/{total}] {museum_id}: {updates_str}")

            # Update timestamp
            if not dry_run:
                museum["updated_at"] = now_utc_iso()
        else:
            stats.skipped += 1

    # Save state file if changes were made
    if changes_made and not dry_run:
        state_data["updated_at"] = now_utc_iso()
        save_json(state_file, state_data)
        print(f"\n  Saved changes to {state_file}")
    elif dry_run and changes_made:
        print(f"\n  [DRY RUN] Would save changes to {state_file}")

    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 1: Backbone Enrichment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Scope selection
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Process all states")

    # Options
    parser.add_argument("--force", action="store_true", help="Force recalculation even if fields exist")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")

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
    run_dir = RUNS_DIR / f"phase1-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 1: Backbone Enrichment")
    print("=" * 60)
    print(f"States: {', '.join(state_codes)}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Run ID: {run_id}")
    print("=" * 60)

    # Process each state
    total_stats = Phase1Stats()

    for state_code in state_codes:
        stats = process_state(
            state_code=state_code,
            force=args.force,
            dry_run=args.dry_run,
        )

        total_stats.total_processed += stats.total_processed
        total_stats.museums_updated += stats.museums_updated
        total_stats.fields_updated += stats.fields_updated
        total_stats.skipped += stats.skipped

    # Save run summary
    summary = {
        "run_id": run_id,
        "states": state_codes,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "museums_updated": total_stats.museums_updated,
        "fields_updated": total_stats.fields_updated,
        "skipped": total_stats.skipped,
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)

    # Print summary
    print("\n" + "=" * 60)
    print("Phase 1 Complete")
    print("=" * 60)
    print(f"  Total processed:  {total_stats.total_processed}")
    print(f"  Museums updated:  {total_stats.museums_updated}")
    print(f"  Fields updated:   {total_stats.fields_updated}")
    print(f"  Skipped:          {total_stats.skipped}")
    print(f"\n  Run directory: {run_dir}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
