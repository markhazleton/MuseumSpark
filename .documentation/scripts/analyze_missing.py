#!/usr/bin/env python3
"""Analyze museums with missing scoring data."""

import json
from pathlib import Path

# Load all museums
museums = []
for state_file in Path('data/states').glob('*.json'):
    with open(state_file, encoding='utf-8') as f:
        state_data = json.load(f)
    museums.extend(state_data['museums'])

print(f"Total museums: {len(museums)}")

# Art museums
art_museums = [m for m in museums if m.get('primary_domain') == 'Art']
print(f"Art museums: {len(art_museums)}")

# Fully scored (has art strength scores)
scored = [m for m in art_museums if m.get('impressionist_strength') or m.get('modern_contemporary_strength')]
print(f"With art scores: {len(scored)}")

# Missing data for Phase 3
missing_for_phase3 = [
    m for m in art_museums 
    if m.get('reputation') is not None  # Has reputation
    and (
        m.get('collection_tier') is None  # Missing tier
        or (not m.get('impressionist_strength') and not m.get('modern_contemporary_strength'))  # No art scores
    )
]

print(f"\nMuseums that could be rescored:")
print(f"  Total: {len(missing_for_phase3)}")

# Break down by what's missing
missing_tier_only = [m for m in missing_for_phase3 if m.get('collection_tier') is None and (m.get('impressionist_strength') or m.get('modern_contemporary_strength'))]
missing_art_only = [m for m in missing_for_phase3 if m.get('collection_tier') is not None and not (m.get('impressionist_strength') or m.get('modern_contemporary_strength'))]
missing_both = [m for m in missing_for_phase3 if m.get('collection_tier') is None and not (m.get('impressionist_strength') or m.get('modern_contemporary_strength'))]

print(f"  Missing only collection_tier: {len(missing_tier_only)}")
print(f"  Missing only art scores: {len(missing_art_only)}")
print(f"  Missing both: {len(missing_both)}")

print(f"\nSample museums missing data:")
for m in missing_for_phase3[:10]:
    print(f"  {m['museum_name']} ({m['state_province']})")
    print(f"    reputation: {m.get('reputation')}, tier: {m.get('collection_tier')}")
    print(f"    imp: {m.get('impressionist_strength')}, mod: {m.get('modern_contemporary_strength')}")
    print(f"    score_notes: {m.get('score_notes', 'N/A')[:100]}...")
