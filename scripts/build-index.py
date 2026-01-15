#!/usr/bin/env python3
"""
Build consolidated museum index from state JSON files.

This script:
1. Reads all state JSON files from data/states/
2. Combines them into a single array
3. Optionally calculates priority scores using the MuseumSpark algorithm
4. Calculates nearby_museum_count for each museum
5. Writes the result to data/index/all-museums.json

Usage:
    python build-index.py                    # Build index without score calculation
    python build-index.py --calculate-scores # Build index and calculate priority scores
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Strength to numeric mapping
STRENGTH_MAP = {
    "None": 0,
    "Minor": 1,
    "Moderate": 2,
    "Strong": 3,
    "Flagship": 5
}

# Reputation to numeric mapping
REPUTATION_MAP = {
    "Local": 1,
    "Regional": 2,
    "National": 3,
    "International": 4
}

# Collection tier to numeric mapping
COLLECTION_TIER_MAP = {
    "Small": 1,
    "Moderate": 2,
    "Strong": 3,
    "Flagship": 4
}

def calculate_priority_score(museum):
    """
    Calculate priority score based on the MuseumSpark formula.

    Formula:
    Priority Score =
      (10 - Impressionism Weight × 3)
      × (10 - Modern/Contemporary Weight × 3)
      × (5 - Historical Context Score × 2)
      × (5 - Reputation Score)
      × (5 - Collection Tier Score)
      - Dual Collection Bonus (-2 if both Impressionist and Modern scores ≥3)
      - Nearby Cluster Bonus (-1 if 3+ museums in city)

    Lower scores = higher priority
    """

    # Get strength values (supports both integer 0-5 and string enum values)
    # New field names: impressionist_strength, modern_contemporary_strength (integers)
    # Legacy field names: impressionism_strength, modern_strength (strings)

    impressionism = museum.get('impressionist_strength')
    if impressionism is None:
        # Try legacy field name
        impressionism = STRENGTH_MAP.get(museum.get('impressionism_strength'), 0)
    elif isinstance(impressionism, str):
        # Handle string enum values
        impressionism = STRENGTH_MAP.get(impressionism, 0)
    else:
        # Already an integer
        impressionism = impressionism or 0

    modern = museum.get('modern_contemporary_strength')
    if modern is None:
        # Try legacy field name
        modern = STRENGTH_MAP.get(museum.get('modern_strength'), 0)
    elif isinstance(modern, str):
        # Handle string enum values
        modern = STRENGTH_MAP.get(modern, 0)
    else:
        # Already an integer
        modern = modern or 0

    # Get historical context score (default to 1 if missing)
    historical_context = museum.get('historical_context_score', 1)

    # Get reputation score (default to 1 if missing)
    reputation = REPUTATION_MAP.get(museum.get('reputation'), 1)

    # Get collection tier score (default to 1 if missing)
    collection_tier = COLLECTION_TIER_MAP.get(museum.get('collection_tier'), 1)

    # Calculate base score
    score = (
        (10 - impressionism * 3)
        * (10 - modern * 3)
        * (5 - historical_context * 2)
        * (5 - reputation)
        * (5 - collection_tier)
    )

    # Apply bonuses (subtract from score, making it lower/better)

    # Dual collection bonus: -2 if both Impressionist and Modern scores ≥3
    if impressionism >= 3 and modern >= 3:
        score -= 2

    # Nearby cluster bonus: -1 if 3+ museums in city
    nearby_count = museum.get('nearby_museum_count', 0)
    if nearby_count >= 3:
        score -= 1

    return round(score, 2)

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
    parser.add_argument('--update-nearby-counts', action='store_true',
                        help='Recalculate nearby_museum_count for all museums')
    args = parser.parse_args()

    # Determine script location and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

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

    # Update nearby museum counts if requested
    if args.update_nearby_counts:
        print("\nCalculating nearby museum counts...")
        nearby_counts = calculate_nearby_counts(museums)

        for museum in museums:
            city = museum.get('city', '')
            state = museum.get('state_province', '')
            key = (city, state)
            museum['nearby_museum_count'] = nearby_counts.get(key, 0)

        print(f"[OK] Updated nearby_museum_count for {len(museums)} museums")

    # Calculate priority scores if requested
    if args.calculate_scores:
        print("\nCalculating priority scores...")

        # Only calculate for museums with required fields
        calculated = 0
        skipped = 0

        for museum in museums:
            # Only calculate for art museums with scoring fields
            # Check both museum_type (legacy) and primary_domain (new)
            museum_type = museum.get('museum_type', '')
            primary_domain = museum.get('primary_domain', '')

            # Determine if this is an art museum
            is_art_museum = (
                primary_domain == 'Art' or
                'Art' in museum_type or
                museum_type in ['Fine Art', 'Art']
            )

            if is_art_museum:
                museum['priority_score'] = calculate_priority_score(museum)
                calculated += 1
            else:
                skipped += 1

        print(f"[OK] Calculated priority scores for {calculated} museums")
        if skipped > 0:
            print(f"  (Skipped {skipped} non-art museums)")

    # Build index file
    index_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
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
