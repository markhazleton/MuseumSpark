#!/usr/bin/env python3
"""
Enrich all-museums.json with data from museums.csv (Priority 0A enrichment).

This standalone script shows the impact of CSV enrichment before running
the full enrich-open-data.py pipeline. Uses fuzzy matching on state + name.

Usage:
    python scripts/enrich-from-csv.py --dry-run           # Show stats only
    python scripts/enrich-from-csv.py --apply             # Update files
"""

import argparse
import csv
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALL_MUSEUMS_PATH = PROJECT_ROOT / "data" / "index" / "all-museums.json"
MUSEUMS_CSV_PATH = PROJECT_ROOT / "data" / "museums.csv"
STATES_DIR = PROJECT_ROOT / "data" / "states"

STATE_NAME_TO_CODE = {
    'Alaska': 'AK', 'Alabama': 'AL', 'Arkansas': 'AR', 'Arizona': 'AZ',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Iowa': 'IA',
    'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Massachusetts': 'MA', 'Maryland': 'MD',
    'Maine': 'ME', 'Michigan': 'MI', 'Minnesota': 'MN', 'Missouri': 'MO',
    'Mississippi': 'MS', 'Montana': 'MT', 'North Carolina': 'NC', 'North Dakota': 'ND',
    'Nebraska': 'NE', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
    'Nevada': 'NV', 'New York': 'NY', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Virginia': 'VA', 'Vermont': 'VT', 'Washington': 'WA', 'Wisconsin': 'WI',
    'West Virginia': 'WV', 'Wyoming': 'WY', 'District of Columbia': 'DC'
}

PLACEHOLDER_STRINGS = {
    "", "tbd", "unknown", "n/a", "na", "not known", "not available",
    "not provided", "not applicable", "none", "null", "pending",
    "coming soon", "--", "---", "tba", "to be announced", "to be determined"
}


def normalize_placeholders(data):
    """Recursively normalize placeholder strings to None."""
    if isinstance(data, dict):
        return {k: normalize_placeholders(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize_placeholders(item) for item in data]
    elif isinstance(data, str):
        if data.strip().lower() in PLACEHOLDER_STRINGS:
            return None
        return data
    return data


def should_fill(value):
    """Check if field should be filled (is None or placeholder)."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in PLACEHOLDER_STRINGS:
        return True
    return False


def normalize_name_for_matching(name):
    """Normalize museum name for fuzzy matching."""
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'\b(museum|center|gallery|institute|foundation|inc|society|association)\b', '', name)
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def similarity_ratio(a, b):
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def load_csv_museums():
    """Load and index museums.csv by state."""
    print(f"Loading {MUSEUMS_CSV_PATH}...")
    
    museums = []
    with open(MUSEUMS_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        museums = list(reader)
    
    # Index by state
    by_state = {}
    for m in museums:
        state = m.get('State (Administrative Location)', '')
        if state not in by_state:
            by_state[state] = []
        by_state[state].append(m)
    
    print(f"  Loaded {len(museums)} museums")
    print(f"  Indexed {len(by_state)} states\n")
    
    return museums, by_state


def try_csv_lookup(museum, csv_by_state):
    """Try to find museum in CSV using fuzzy matching."""
    state_province = museum.get('state_province', '')
    state_code = STATE_NAME_TO_CODE.get(state_province)
    if not state_code:
        return None
    
    csv_state_museums = csv_by_state.get(state_code, [])
    if not csv_state_museums:
        return None
    
    museum_name = museum.get('museum_name', '')
    if not museum_name:
        return None
    
    museum_name_norm = normalize_name_for_matching(museum_name)
    
    # Try exact match first
    for csv_m in csv_state_museums:
        if csv_m.get('Museum Name') == museum_name:
            return csv_m
    
    # Try fuzzy match (70% threshold)
    best_match = None
    best_ratio = 0.0
    for csv_m in csv_state_museums:
        csv_name_norm = normalize_name_for_matching(csv_m.get('Museum Name', ''))
        ratio = similarity_ratio(museum_name_norm, csv_name_norm)
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = csv_m
    
    if best_match and best_ratio >= 0.7:
        return best_match
    
    return None


def enrich_museum(museum, csv_match):
    """Enrich museum with CSV data."""
    changed = False
    notes_additions = []
    
    # Phone number
    csv_phone = csv_match.get('Phone Number', '').strip()
    if csv_phone and should_fill(museum.get('phone')):
        museum['phone'] = csv_phone
        notes_additions.append("CSV: phone from IRS 990 database")
        changed = True
    
    # Museum Type
    csv_type = csv_match.get('Museum Type', '').strip()
    if csv_type and should_fill(museum.get('museum_type')):
        museum['museum_type'] = csv_type
        notes_additions.append(f"CSV: museum type '{csv_type}'")
        changed = True
    
    # Coordinates
    csv_lat = csv_match.get('Latitude', '').strip()
    csv_lng = csv_match.get('Longitude', '').strip()
    if csv_lat and csv_lng:
        try:
            lat = float(csv_lat)
            lng = float(csv_lng)
            if should_fill(museum.get('latitude')):
                museum['latitude'] = lat
                changed = True
            if should_fill(museum.get('longitude')):
                museum['longitude'] = lng
                changed = True
            if changed:
                notes_additions.append("CSV: coordinates from IRS 990 database")
        except (ValueError, TypeError):
            pass
    
    # Postal Code
    csv_zip = csv_match.get('Zip Code (Physical Location)', '').strip()
    if csv_zip and should_fill(museum.get('postal_code')):
        museum['postal_code'] = csv_zip
        changed = True
    
    # City (only if missing/unknown)
    csv_city = csv_match.get('City (Physical Location)', '').strip()
    if csv_city and should_fill(museum.get('city')):
        museum['city'] = csv_city
        changed = True
    
    # Address (lower priority - only if nothing better)
    csv_addr = csv_match.get('Street Address (Physical Location)', '').strip()
    if csv_addr and should_fill(museum.get('street_address')):
        # Only use if no existing address source or source is NARM
        existing_source = museum.get('address_source', '')
        if not existing_source or existing_source == 'narm':
            museum['street_address'] = csv_addr
            museum['address_source'] = 'museums_csv'
            museum['address_last_verified'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            notes_additions.append("CSV: physical address from IRS 990")
            changed = True
    
    # Add to data sources
    if changed:
        if 'data_sources' not in museum:
            museum['data_sources'] = []
        if 'museums_csv' not in museum['data_sources']:
            museum['data_sources'].append('museums_csv')
        
        # Add notes
        if notes_additions:
            existing_notes = museum.get('notes', '')
            if existing_notes:
                museum['notes'] = existing_notes + ' ' + ' '.join(notes_additions)
            else:
                museum['notes'] = ' '.join(notes_additions)
        
        # Update last_updated
        museum['last_updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    return changed


def main():
    parser = argparse.ArgumentParser(description='Enrich museums from CSV database')
    parser.add_argument('--dry-run', action='store_true', help='Show statistics only, do not save')
    parser.add_argument('--apply', action='store_true', help='Apply changes and save files')
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("ERROR: Must specify either --dry-run or --apply")
        return 1
    
    # Load data
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       CSV ENRICHMENT: Standalone Impact Analysis          ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    _, csv_by_state = load_csv_museums()
    
    print(f"Loading {ALL_MUSEUMS_PATH}...")
    with open(ALL_MUSEUMS_PATH, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    museums = all_data['museums']
    print(f"  Loaded {len(museums)} museums\n")
    
    # Track statistics
    stats = {
        'total': len(museums),
        'matched': 0,
        'enriched': 0,
        'phone_added': 0,
        'type_added': 0,
        'coords_added': 0,
        'postal_added': 0,
        'address_added': 0,
    }
    
    # Count before
    before = {
        'phone': sum(1 for m in museums if m.get('phone') and not should_fill(m.get('phone'))),
        'type': sum(1 for m in museums if m.get('museum_type') and not should_fill(m.get('museum_type'))),
        'coords': sum(1 for m in museums if m.get('latitude') and m.get('longitude')),
        'postal': sum(1 for m in museums if m.get('postal_code') and not should_fill(m.get('postal_code'))),
        'address': sum(1 for m in museums if m.get('street_address') and not should_fill(m.get('street_address'))),
    }
    
    print("Processing museums...")
    for i, museum in enumerate(museums, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(museums)}...")
        
        csv_match = try_csv_lookup(museum, csv_by_state)
        if csv_match:
            stats['matched'] += 1
            
            # Track what we're adding
            will_add_phone = csv_match.get('Phone Number', '').strip() and should_fill(museum.get('phone'))
            will_add_type = csv_match.get('Museum Type', '').strip() and should_fill(museum.get('museum_type'))
            will_add_coords = csv_match.get('Latitude', '').strip() and should_fill(museum.get('latitude'))
            will_add_postal = csv_match.get('Zip Code (Physical Location)', '').strip() and should_fill(museum.get('postal_code'))
            will_add_address = csv_match.get('Street Address (Physical Location)', '').strip() and should_fill(museum.get('street_address'))
            
            changed = enrich_museum(museum, csv_match)
            
            if changed:
                stats['enriched'] += 1
                if will_add_phone:
                    stats['phone_added'] += 1
                if will_add_type:
                    stats['type_added'] += 1
                if will_add_coords:
                    stats['coords_added'] += 1
                if will_add_postal:
                    stats['postal_added'] += 1
                if will_add_address:
                    stats['address_added'] += 1
    
    # Normalize all placeholders
    all_data = normalize_placeholders(all_data)
    museums = all_data['museums']
    
    # Count after
    after = {
        'phone': sum(1 for m in museums if m.get('phone')),
        'type': sum(1 for m in museums if m.get('museum_type')),
        'coords': sum(1 for m in museums if m.get('latitude') and m.get('longitude')),
        'postal': sum(1 for m in museums if m.get('postal_code')),
        'address': sum(1 for m in museums if m.get('street_address')),
    }
    
    # Print results
    print("\n" + "="*60)
    print("📊 CSV ENRICHMENT IMPACT REPORT")
    print("="*60 + "\n")
    
    print(f"Total museums: {stats['total']}")
    print(f"CSV matches: {stats['matched']} ({stats['matched']/stats['total']*100:.1f}%)")
    print(f"Museums enriched: {stats['enriched']} ({stats['enriched']/stats['total']*100:.1f}%)\n")
    
    print("FIELD COVERAGE (Before → After):\n")
    
    fields = [
        ('Phone numbers', 'phone'),
        ('Museum types', 'type'),
        ('Coordinates', 'coords'),
        ('Postal codes', 'postal'),
        ('Street addresses', 'address'),
    ]
    
    for label, key in fields:
        b = before[key]
        a = after[key]
        added = stats[f'{key}_added']
        b_pct = b/stats['total']*100
        a_pct = a/stats['total']*100
        improvement = a_pct - b_pct
        
        status = "✅" if improvement > 10 else "📈" if improvement > 0 else "→"
        print(f"{status} {label:20} {b:4} ({b_pct:5.1f}%) → {a:4} ({a_pct:5.1f}%) [+{added:3}]")
    
    print("\n" + "="*60)
    
    if args.apply:
        print("\n💾 Saving changes...")
        
        # Update all-museums.json
        all_data['generated_at'] = datetime.now(timezone.utc).isoformat() + 'Z'
        all_data['total_museums'] = len(museums)
        
        with open(ALL_MUSEUMS_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ Updated {ALL_MUSEUMS_PATH}")
        
        # Update state files
        museums_by_state = {}
        for m in museums:
            state_code = STATE_NAME_TO_CODE.get(m.get('state_province', ''))
            if state_code:
                if state_code not in museums_by_state:
                    museums_by_state[state_code] = []
                museums_by_state[state_code].append(m)
        
        for state_code, state_museums in museums_by_state.items():
            state_file = STATES_DIR / f"{state_code}.json"
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                # Update museums
                state_data['museums'] = state_museums
                state_data['last_updated'] = datetime.now(timezone.utc).isoformat() + 'Z'
                
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ Updated {len(museums_by_state)} state files")
        print("\n✅ All files saved successfully!")
    
    else:
        print("\n🔍 Dry run complete. Use --apply to save changes.")
    
    return 0


if __name__ == '__main__':
    exit(main())
