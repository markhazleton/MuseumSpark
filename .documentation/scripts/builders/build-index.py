#!/usr/bin/env python3
"""
Build consolidated museum index from state JSON files.

This script:
1. Reads all state JSON files from data/states/
2. Combines them into a single array
3. Validates MRD-aligned fields (time_needed enum, art-only scoring)
4. Calculates nearby_museum_count for each museum (always recomputed)
5. Optionally calculates priority scores using the MuseumSpark algorithm
6. Writes the result to data/index/all-museums.json

Usage:
    python build-index.py                    # Build index (recomputes nearby_museum_count)
    python build-index.py --calculate-scores # Build index and calculate priority scores
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# MRD Tier 1 cities (Major hubs)
TIER_1_CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Washington", "Boston", "Detroit", "Nashville",
    "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee",
    "Albuquerque", "Tucson", "Fresno", "Sacramento", "Kansas City", "Atlanta",
    "Miami", "Minneapolis", "Cleveland", "New Orleans", "Oakland", "Tampa",
    "Honolulu", "Omaha", "Wichita", "Arlington"
]

# MRD Tier 2 cities (Medium cities - special cultural significance)
TIER_2_SPECIAL = [
    "Santa Fe", "Williamsburg", "Annapolis", "Cambridge", "Berkeley",
    "Ann Arbor", "Asheville", "Savannah", "Charleston"
]

PRIMARY_DOMAIN_ALLOWED = {"Art", "History", "Science", "Culture", "Specialty", "Mixed"}
TIME_NEEDED_ALLOWED = {"Quick stop (<1 hr)", "Half day", "Full day"}
TIME_NEEDED_SYNONYMS = {
    "quick stop": "Quick stop (<1 hr)",
    "quick stop (1-2 hours)": "Quick stop (<1 hr)",
    "1-2 hours": "Quick stop (<1 hr)",
    "<1 hr": "Quick stop (<1 hr)",
    "half day (2-4 hours)": "Half day",
    "2-4 hours": "Half day",
    "half-day": "Half day",
    "full day (4+ hours)": "Full day",
    "4+ hours": "Full day",
}

def calculate_priority_score(museum):
    """
    Calculate priority score using the MRD v1.0 formula (Section 5).

    MRD Formula:
    Primary Art Strength = max(impressionist_strength, modern_contemporary_strength)
    Dual-Strength Bonus = (impressionist_strength ≥ 4 AND modern_contemporary_strength ≥ 4) ? 2 : 0
    
    Priority Score = 
      (6 – Primary Art Strength) × 3
      + (6 – Historical Context Score) × 2
      + Reputation Penalty (0-3)
      + Collection Penalty (0-3)
      – Dual Strength Bonus

    Lower scores = higher priority
    """
    # Get strength values (MRD 1-5 scale)
    impressionist = museum.get('impressionist_strength')
    modern = museum.get('modern_contemporary_strength')
    historical = museum.get('historical_context_score')
    reputation = museum.get('reputation')  # Already numeric 0-3
    collection = museum.get('collection_tier')  # Already numeric 0-3

    # Require all inputs for scoring
    if None in [impressionist, modern, historical, reputation, collection]:
        return None

    # MRD Formula
    primary_art_strength = max(impressionist, modern)
    
    dual_bonus = 2 if (impressionist >= 4 and modern >= 4) else 0
    
    score = (
        (6 - primary_art_strength) * 3
        + (6 - historical) * 2
        + reputation  # 0-3 numeric penalty
        + collection  # 0-3 numeric penalty
        - dual_bonus
    )

    return round(score, 2)


def derive_primary_art(museum):
    """
    Derive primary_art from strength scores per MRD Section 4.9.
    Returns "Impressionist", "Modern/Contemporary", or None.
    """
    imp = museum.get('impressionist_strength')
    mod = museum.get('modern_contemporary_strength')
    
    if imp is None and mod is None:
        return None
    
    if imp is None:
        return "Modern/Contemporary"
    if mod is None:
        return "Impressionist"
    
    if imp > mod:
        return "Impressionist"
    elif mod > imp:
        return "Modern/Contemporary"
    else:
        # Tie: default to Modern/Contemporary
        return "Modern/Contemporary"


class MuseumRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    primary_domain: Optional[str] = None
    time_needed: Optional[str] = None
    impressionist_strength: Optional[int] = None
    modern_contemporary_strength: Optional[int] = None
    historical_context_score: Optional[int] = None

    @field_validator("primary_domain")
    @classmethod
    def validate_primary_domain(cls, v):
        if v is None:
            return v
        if v not in PRIMARY_DOMAIN_ALLOWED:
            raise ValueError(f"primary_domain must be one of {sorted(PRIMARY_DOMAIN_ALLOWED)}")
        return v

    @field_validator("time_needed")
    @classmethod
    def validate_time_needed(cls, v):
        if v is None:
            return v
        normalized = normalize_time_needed(v)
        if normalized is None:
            raise ValueError("time_needed must be one of the MRD enums: Quick stop (<1 hr), Half day, Full day")
        return normalized

    @model_validator(mode="after")
    def check_art_scoring(self):
        # Relaxed validation: allow art scores if is_scoreable=True OR primary_domain="Art"
        # The new pipeline uses is_scoreable as the gatekeeper, not primary_domain
        extras = getattr(self, "__pydantic_extra__", {}) or {}
        is_scoreable = extras.get("is_scoreable", False)

        if self.primary_domain != "Art" and not is_scoreable:
            for field in (
                "impressionist_strength",
                "modern_contemporary_strength",
                "historical_context_score",
            ):
                if getattr(self, field) is not None:
                    raise ValueError(
                        "Art scoring fields (impressionist_strength/modern_contemporary_strength/"
                        "historical_context_score) must be empty when primary_domain is not 'Art' "
                        "and is_scoreable is not True"
                    )
        return self


def validate_and_normalize_museums(museums):
    """Validate museums against MRD guardrails and normalize time_needed.

    Raises on the first validation error to prevent writing non-compliant data.
    """
    validated = []
    for museum in museums:
        try:
            model = MuseumRecord.model_validate(museum)
        except ValidationError as exc:
            museum_id = museum.get("museum_id") or museum.get("museum_name") or "<unknown>"
            print(f"[ERROR] Validation failed for {museum_id}:")
            for err in exc.errors():
                loc = "->".join(str(p) for p in err.get("loc", []))
                print(f"  - {loc}: {err.get('msg')}")
            sys.exit(1)

        # Preserve extras while keeping normalized/validated fields
        extras = getattr(model, "__pydantic_extra__", {}) or {}
        merged = {**extras, **model.model_dump(exclude_none=False)}
        validated.append(merged)

    return validated


def compute_city_tier(city, state):
    """
    Compute city_tier per MRD Section 3.6.
    Returns 1 (Major hub), 2 (Medium city), or 3 (Small town).
    """
    if not city or city.strip().upper() in ['UNKNOWN', 'TBD', '']:
        return None
    
    city_normalized = city.strip()
    
    # Tier 1: Major hubs
    if city_normalized in TIER_1_CITIES:
        return 1
    
    # Tier 2: Special cultural significance
    if city_normalized in TIER_2_SPECIAL:
        return 2
    
    # TODO: Add US Census population lookup for dynamic tier 2/3 classification
    # For now, default to Tier 3 (Small town)
    return 3


def normalize_time_needed(value: Optional[str]) -> Optional[str]:
    """Normalize time_needed to MRD enum values or return None.

    Accepts common variants (e.g., "1-2 hours", "half day (2-4 hours)") and
    returns one of: "Quick stop (<1 hr)", "Half day", "Full day".
    """
    if not value:
        return None

    v = value.strip().lower()
    for allowed in TIME_NEEDED_ALLOWED:
        if v == allowed.lower():
            return allowed

    if v in TIME_NEEDED_SYNONYMS:
        return TIME_NEEDED_SYNONYMS[v]

    return None

def calculate_nearby_counts(museums):
    """
    Calculate nearby_museum_count for each museum by grouping by city.
    Returns a dictionary mapping (city, state_province) -> count
    """
    city_counts = defaultdict(int)

    # Count museums per city
    for museum in museums:
        city = museum.get('city', '')
        state = museum.get('state_province', '')
        key = (city, state)
        city_counts[key] += 1

    # Subtract 1 from each count (exclude the museum itself)
    return {key: max(0, count - 1) for key, count in city_counts.items()}

def load_state_files(states_dir):
    """Load all state JSON files and extract museums."""
    all_museums = []
    state_count = 0

    state_files = sorted(states_dir.glob('*.json'))

    if not state_files:
        print(f"[ERROR] Error: No JSON files found in {states_dir}")
        sys.exit(1)

    for file_path in state_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            museums = data.get('museums', [])
            all_museums.extend(museums)
            state_count += 1

            print(f"[OK] Loaded {len(museums)} museums from {file_path.name}")

        except json.JSONDecodeError as e:
            print(f"[ERROR] Error: Invalid JSON in {file_path}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Error loading {file_path}: {e}")
            sys.exit(1)

    print(f"\n[OK] Loaded {len(all_museums)} museums from {state_count} state files")
    return all_museums

def main():
    parser = argparse.ArgumentParser(description='Build MuseumSpark consolidated index')
    parser.add_argument('--calculate-scores', action='store_true',
                        help='Calculate priority scores for all museums')
    args = parser.parse_args()

    # Determine script location and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    states_dir = project_root / 'data' / 'states'
    index_dir = project_root / 'data' / 'index'
    output_file = index_dir / 'all-museums.json'

    # Ensure index directory exists
    index_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("MuseumSpark Index Builder")
    print("=" * 60)
    print()

    # Load all state files
    museums = load_state_files(states_dir)

    # Validate and normalize MRD-sensitive fields
    museums = validate_and_normalize_museums(museums)

    # Always recompute nearby museum counts (ignore any pre-filled values)
    print("\nCalculating nearby museum counts...")
    nearby_counts = calculate_nearby_counts(museums)

    for museum in museums:
        city = museum.get('city', '')
        state = museum.get('state_province', '')
        key = (city, state)
        museum['nearby_museum_count'] = nearby_counts.get(key, 0)

    print(f"[OK] Updated nearby_museum_count for {len(museums)} museums")

    # Compute MRD fields for all museums
    print("\nComputing MRD fields...")
    
    # Compute city_tier and primary_art for all museums
    for museum in museums:
        city = museum.get('city', '')
        state = museum.get('state_province', '')
        
        # Compute city_tier
        if museum.get('city_tier') is None:
            museum['city_tier'] = compute_city_tier(city, state)
        
        # Derive primary_art from strength scores (art museums only)
        if museum.get('primary_domain') == 'Art':
            if museum.get('primary_art') is None:
                museum['primary_art'] = derive_primary_art(museum)
        else:
            museum['primary_art'] = None
    
    print(f"[OK] Computed city_tier and primary_art for all museums")

    # Calculate priority scores if requested
    if args.calculate_scores:
        print("\nCalculating priority scores...")

        calculated = 0
        skipped = 0

        for museum in museums:
            # Determine if this is an art museum eligible for scoring
            primary_domain = museum.get('primary_domain', '')
            
            is_art_museum = primary_domain == 'Art'

            if is_art_museum:
                score = calculate_priority_score(museum)
                museum['priority_score'] = score
                museum['is_scored'] = (score is not None)
                
                if score is not None:
                    calculated += 1
                    if museum.get('scoring_version') is None:
                        museum['scoring_version'] = 'v1.0'
            else:
                museum['is_scored'] = False
                skipped += 1

        print(f"[OK] Calculated priority scores for {calculated} museums")
        if skipped > 0:
            print(f"  (Skipped {skipped} non-art museums)")

    # Build index file
    index_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "total_museums": len(museums),
        "museums": museums
    }

    # Write output file
    print(f"\nWriting index to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Index file created: {output_file}")
    print(f"\n{'=' * 60}")
    print("Summary:")
    print(f"  Total museums: {len(museums)}")
    print(f"  Output file: {output_file}")
    print("=" * 60)
    print("\n Index build complete!")

if __name__ == '__main__':
    main()
