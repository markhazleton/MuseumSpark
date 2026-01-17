#!/usr/bin/env python3
"""Phase 1.8: CSV Database Lookup (IRS 990 Museum Data).

This module enriches museums with data from the IRS 990 museum database CSV.
Uses fuzzy matching on museum name + exact match on state.

Data Source: data/museums.csv (33,000+ museums from IRS 990 filings)

Fields Provided:
    - phone: Phone number (69% coverage, 88.7% of matches have phone)
    - museum_type: Museum type taxonomy from IRS (100% coverage)
    - coordinates: Latitude/Longitude (99.8% coverage in CSV)
    - financial data: Income/Revenue for research (stored in notes)
    - csv_museum_id: IRS Museum ID for deduplication reference

Matching Strategy:
    1. Exact state match required (uses state_province field)
    2. Try exact name match first
    3. Fall back to fuzzy match (70% similarity threshold)
    4. Normalize names: lowercase, remove common words (museum, center, etc.)
    5. Skip if no reasonable match found

Design Principles:
    1. FREE DATA: No API costs, instant enrichment
    2. HIGH MATCH RATE: 76.5% of museums match successfully
    3. CAREFUL MATCHING: Fuzzy match only within same state
    4. DATA QUALITY: Only fill missing fields (never overwrite good data)
    5. IDEMPOTENT: Skip museums already enriched from CSV

Usage:
    # Enrich single state
    python scripts/phases/phase1_8_csv_lookup.py --state CO

    # Process all states
    python scripts/phases/phase1_8_csv_lookup.py --all-states

    # Dry run (show what would match)
    python scripts/phases/phase1_8_csv_lookup.py --state CO --dry-run

    # Force re-matching even if already done
    python scripts/phases/phase1_8_csv_lookup.py --state CO --force
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
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
RUNS_DIR = PROJECT_ROOT / "data" / "runs"
CSV_PATH = PROJECT_ROOT / "data" / "museums.csv"

# Cache for CSV data
_CSV_BY_STATE_CACHE: Optional[dict[str, list[dict[str, str]]]] = None

# State name to code mapping
STATE_NAME_TO_CODE = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}

# Museum type normalizations (matches phase1_backbone.py for consistency)
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
class CSVMatch:
    """Result of CSV matching."""
    matched: bool = False
    csv_museum_id: Optional[str] = None
    phone: Optional[str] = None
    museum_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    income: Optional[str] = None
    revenue: Optional[str] = None
    match_type: Optional[str] = None  # "exact" or "fuzzy"
    match_score: Optional[float] = None  # 0.0-1.0


@dataclass
class Phase1_8Stats:
    """Statistics for a Phase 1.8 run."""
    total_processed: int = 0
    exact_matches: int = 0
    fuzzy_matches: int = 0
    no_match: int = 0
    skipped_already_done: int = 0
    fields_populated: int = 0


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


def load_csv_museums() -> dict[str, list[dict[str, str]]]:
    """Load museums.csv and create state-indexed lookup.
    
    Returns:
        Dictionary mapping state code to list of museum records
    """
    global _CSV_BY_STATE_CACHE
    
    if _CSV_BY_STATE_CACHE is not None:
        return _CSV_BY_STATE_CACHE
    
    if not CSV_PATH.exists():
        print(f"ERROR: CSV file not found: {CSV_PATH}")
        _CSV_BY_STATE_CACHE = {}
        return _CSV_BY_STATE_CACHE
    
    print(f"Loading CSV database from {CSV_PATH}...")
    
    # Index by state
    by_state: dict[str, list[dict[str, str]]] = {}
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            state = row.get('State (Administrative Location)', '').strip()
            if state:
                if state not in by_state:
                    by_state[state] = []
                by_state[state].append(row)
    
    _CSV_BY_STATE_CACHE = by_state
    
    total_museums = sum(len(museums) for museums in by_state.values())
    print(f"Loaded {total_museums:,} museums across {len(by_state)} states")
    
    return by_state


def normalize_name_for_matching(name: str) -> str:
    """Normalize museum name for fuzzy matching.
    
    Removes common museum words and punctuation to improve matching.
    """
    if not name:
        return ""
    
    # Lowercase
    name = name.lower()
    
    # Remove common museum words
    name = re.sub(
        r'\b(museum|center|centre|gallery|galleries|institute|foundation|'
        r'inc|incorporated|society|association|the|of|and|for)\b',
        '', name
    )
    
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def similarity_ratio(a: str, b: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, a, b).ratio()


def normalize_museum_type(museum_type: Optional[str]) -> Optional[str]:
    """Normalize museum type to standard values (matches phase1_backbone.py).
    
    Returns:
        Normalized type string in proper case or original if no match
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
    
    # Return original with title case if no match
    return museum_type.strip().title()


def find_csv_match(museum: dict, csv_by_state: dict[str, list[dict[str, str]]]) -> CSVMatch:
    """Find matching museum in CSV database.
    
    Args:
        museum: Museum record from state file
        csv_by_state: CSV museums indexed by state
        
    Returns:
        CSVMatch with match results
    """
    result = CSVMatch()
    
    # Get state code
    state_province = museum.get('state_province', '')
    state_code = STATE_NAME_TO_CODE.get(state_province)
    
    if not state_code:
        return result  # No state match possible
    
    csv_state_museums = csv_by_state.get(state_code, [])
    if not csv_state_museums:
        return result  # No museums in this state in CSV
    
    museum_name = museum.get('museum_name', '')
    if not museum_name:
        return result  # No name to match
    
    # Try exact match first
    for csv_m in csv_state_museums:
        csv_name = csv_m.get('Museum Name', '').strip()
        if csv_name and csv_name.lower() == museum_name.lower():
            result.matched = True
            result.match_type = "exact"
            result.match_score = 1.0
            result = _extract_csv_fields(result, csv_m)
            return result
    
    # Try fuzzy match (70% threshold)
    museum_name_norm = normalize_name_for_matching(museum_name)
    
    best_match = None
    best_ratio = 0.0
    
    for csv_m in csv_state_museums:
        csv_name = csv_m.get('Museum Name', '').strip()
        if not csv_name:
            continue
        
        csv_name_norm = normalize_name_for_matching(csv_name)
        ratio = similarity_ratio(museum_name_norm, csv_name_norm)
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = csv_m
    
    # Only accept matches >= 70% similarity
    if best_match and best_ratio >= 0.7:
        result.matched = True
        result.match_type = "fuzzy"
        result.match_score = best_ratio
        result = _extract_csv_fields(result, best_match)
    
    return result


def _extract_csv_fields(result: CSVMatch, csv_record: dict[str, str]) -> CSVMatch:
    """Extract fields from CSV record into CSVMatch."""
    result.csv_museum_id = csv_record.get('Museum ID', '').strip() or None
    result.phone = csv_record.get('Phone Number', '').strip() or None
    
    # Normalize museum type to proper case
    raw_type = csv_record.get('Museum Type', '').strip()
    result.museum_type = normalize_museum_type(raw_type) if raw_type else None
    
    # Coordinates
    lat_str = csv_record.get('Latitude', '').strip()
    lng_str = csv_record.get('Longitude', '').strip()
    if lat_str and lng_str:
        try:
            result.latitude = float(lat_str)
            result.longitude = float(lng_str)
        except ValueError:
            pass
    
    # Address (physical location preferred, fall back to administrative)
    result.street_address = (
        csv_record.get('Street Address (Physical Location)', '').strip() or
        csv_record.get('Street Address (Administrative Location)', '').strip() or
        None
    )
    result.city = (
        csv_record.get('City (Physical Location)', '').strip() or
        csv_record.get('City (Administrative Location)', '').strip() or
        None
    )
    result.postal_code = (
        csv_record.get('Zip Code (Physical Location)', '').strip() or
        csv_record.get('Zip Code (Administrative Location)', '').strip() or
        None
    )
    
    # Financial data (for research purposes)
    result.income = csv_record.get('Income', '').strip() or None
    result.revenue = csv_record.get('Revenue', '').strip() or None
    
    return result


def should_fill_field(museum: dict, field: str) -> bool:
    """Check if a field should be filled (is missing or placeholder)."""
    value = museum.get(field)
    
    if value is None:
        return True
    
    if isinstance(value, str):
        value_lower = value.strip().lower()
        if value_lower in {"", "tbd", "unknown", "n/a", "null", "pending", "none"}:
            return True
    
    return False


def enrich_from_csv(
    museum: dict,
    csv_by_state: dict[str, list[dict[str, str]]],
    *,
    force: bool = False
) -> tuple[CSVMatch, int]:
    """Enrich museum with CSV data.
    
    Args:
        museum: Museum record
        csv_by_state: CSV museums indexed by state
        force: Force re-enrichment even if already done
        
    Returns:
        Tuple of (CSVMatch, fields_populated_count)
    """
    # Check if already enriched from CSV (unless force)
    if not force and "museums_csv" in museum.get("data_sources", []):
        return CSVMatch(matched=False), 0
    
    # Find match
    match = find_csv_match(museum, csv_by_state)
    
    if not match.matched:
        return match, 0
    
    fields_populated = 0
    
    # Populate phone
    if match.phone and should_fill_field(museum, 'phone'):
        museum['phone'] = match.phone
        fields_populated += 1
    
    # Populate museum_type
    if match.museum_type and should_fill_field(museum, 'museum_type'):
        museum['museum_type'] = match.museum_type
        fields_populated += 1
    
    # Populate coordinates (only if both are missing)
    if match.latitude is not None and match.longitude is not None:
        if should_fill_field(museum, 'latitude') and should_fill_field(museum, 'longitude'):
            museum['latitude'] = match.latitude
            museum['longitude'] = match.longitude
            fields_populated += 2
    
    # Populate address (only if current source is weak or missing)
    current_address_source = museum.get('address_source', '')
    if match.street_address and (not current_address_source or current_address_source == 'narm'):
        if should_fill_field(museum, 'street_address'):
            museum['street_address'] = match.street_address
            museum['address_source'] = 'museums_csv'
            museum['address_last_verified'] = datetime.now().strftime("%Y-%m-%d")
            fields_populated += 1
    
    # Populate city and postal code
    if match.city and should_fill_field(museum, 'city'):
        museum['city'] = match.city
        fields_populated += 1
    
    if match.postal_code and should_fill_field(museum, 'postal_code'):
        museum['postal_code'] = match.postal_code
        fields_populated += 1
    
    # Add to notes field (CSV Museum ID and financial data)
    notes_additions = []
    
    if match.csv_museum_id:
        notes_additions.append(f"CSV: IRS Museum ID {match.csv_museum_id}")
    
    if match.phone:
        notes_additions.append("CSV: phone from IRS 990 database")
    
    if match.museum_type:
        notes_additions.append(f"CSV: museum type '{match.museum_type}'")
    
    if match.latitude and match.longitude:
        notes_additions.append("CSV: coordinates from IRS 990 database")
    
    if match.street_address:
        notes_additions.append("CSV: physical address from IRS 990")
    
    if match.income or match.revenue:
        notes_additions.append(
            f"CSV: financial data available (income: {match.income or 'N/A'}, "
            f"revenue: {match.revenue or 'N/A'})"
        )
    
    if notes_additions:
        current_notes = museum.get('notes', '') or ''
        new_notes = ' '.join(notes_additions)
        if current_notes:
            museum['notes'] = f"{current_notes} {new_notes}"
        else:
            museum['notes'] = new_notes
    
    # Add to data_sources
    data_sources = museum.get('data_sources', [])
    if not isinstance(data_sources, list):
        data_sources = []
    if 'museums_csv' not in data_sources:
        data_sources.append('museums_csv')
        museum['data_sources'] = data_sources
    
    # Update timestamp
    museum['updated_at'] = now_utc_iso()
    
    return match, fields_populated


def process_state(
    state_code: str,
    csv_by_state: dict[str, list[dict[str, str]]],
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Phase1_8Stats:
    """Process all museums in a state for CSV enrichment.
    
    Args:
        state_code: Two-letter state code
        csv_by_state: CSV museums indexed by state
        force: Force re-enrichment even if already done
        dry_run: If True, don't make changes
        
    Returns:
        Phase1_8Stats with processing statistics
    """
    stats = Phase1_8Stats()
    
    state_file = STATES_DIR / f"{state_code}.json"
    if not state_file.exists():
        print(f"ERROR: State file not found: {state_file}")
        return stats
    
    state_data = load_json(state_file)
    museums = state_data.get("museums", [])
    total = len(museums)
    
    print(f"\n[STATE: {state_code}] Processing {total} museums")
    
    for idx, museum in enumerate(museums, 1):
        museum_name = museum.get("museum_name", "")[:50]
        stats.total_processed += 1
        
        # Check if already done (unless force)
        if not force and "museums_csv" in museum.get("data_sources", []):
            stats.skipped_already_done += 1
            continue
        
        print(f"  [{idx}/{total}] {museum_name}")
        
        if dry_run:
            # Just show what would match
            match = find_csv_match(museum, csv_by_state)
            if match.matched:
                print(f"           MATCH ({match.match_type}, {match.match_score:.0%}): {match.csv_museum_id}")
            else:
                print(f"           NO MATCH")
            continue
        
        # Enrich
        match, fields_count = enrich_from_csv(museum, csv_by_state, force=force)
        
        if match.matched:
            if match.match_type == "exact":
                stats.exact_matches += 1
            else:
                stats.fuzzy_matches += 1
            stats.fields_populated += fields_count
            print(f"           OK - {match.match_type} match ({match.match_score:.0%}), {fields_count} fields")
        else:
            stats.no_match += 1
            print(f"           NO MATCH")
    
    # Save state file (unless dry run)
    if not dry_run and (stats.exact_matches > 0 or stats.fuzzy_matches > 0):
        state_data['last_updated'] = now_utc_iso()
        save_json(state_file, state_data)
        print(f"  Saved changes to {state_file}")
    elif dry_run:
        print(f"  [DRY RUN] Would save changes to {state_file}")
    
    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 1.8: CSV Database Lookup (IRS 990)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    # Scope selection
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Process all states")
    
    # Options
    parser.add_argument("--force", action="store_true", help="Force re-enrichment even if already done")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
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
    
    # Load CSV database
    csv_by_state = load_csv_museums()
    if not csv_by_state:
        print("ERROR: Failed to load CSV database")
        return 1
    
    # Create run directory for logging
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"phase1_8-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Phase 1.8: CSV Database Lookup (IRS 990)")
    print("=" * 60)
    print(f"States: {', '.join(state_codes)}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Run ID: {run_id}")
    print("=" * 60)
    
    # Process each state
    total_stats = Phase1_8Stats()
    
    for state_code in state_codes:
        stats = process_state(
            state_code=state_code,
            csv_by_state=csv_by_state,
            force=args.force,
            dry_run=args.dry_run,
        )
        
        total_stats.total_processed += stats.total_processed
        total_stats.exact_matches += stats.exact_matches
        total_stats.fuzzy_matches += stats.fuzzy_matches
        total_stats.no_match += stats.no_match
        total_stats.skipped_already_done += stats.skipped_already_done
        total_stats.fields_populated += stats.fields_populated
    
    # Save run summary
    summary = {
        "run_id": run_id,
        "states": state_codes,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "exact_matches": total_stats.exact_matches,
        "fuzzy_matches": total_stats.fuzzy_matches,
        "total_matches": total_stats.exact_matches + total_stats.fuzzy_matches,
        "no_match": total_stats.no_match,
        "skipped_already_done": total_stats.skipped_already_done,
        "fields_populated": total_stats.fields_populated,
        "match_rate": (
            f"{(total_stats.exact_matches + total_stats.fuzzy_matches) / total_stats.total_processed * 100:.1f}%"
            if total_stats.total_processed > 0 else "0%"
        ),
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Phase 1.8 Complete")
    print("=" * 60)
    print(f"  Total processed:      {total_stats.total_processed}")
    print(f"  Exact matches:        {total_stats.exact_matches}")
    print(f"  Fuzzy matches:        {total_stats.fuzzy_matches}")
    print(f"  Total matched:        {total_stats.exact_matches + total_stats.fuzzy_matches}")
    print(f"  No match:             {total_stats.no_match}")
    print(f"  Skipped (done):       {total_stats.skipped_already_done}")
    print(f"  Fields populated:     {total_stats.fields_populated}")
    if total_stats.total_processed > 0:
        match_rate = (total_stats.exact_matches + total_stats.fuzzy_matches) / total_stats.total_processed * 100
        print(f"  Match rate:           {match_rate:.1f}%")
    print(f"\n  Run directory: {run_dir}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
