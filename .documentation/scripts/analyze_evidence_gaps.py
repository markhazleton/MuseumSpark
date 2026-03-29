#!/usr/bin/env python3
"""Analyze evidence gaps for museums missing Phase 2 scores."""

import json
from pathlib import Path

# Load all museums
museums = []
for state_file in Path('data/states').glob('*.json'):
    with open(state_file, encoding='utf-8') as f:
        state_data = json.load(f)
    museums.extend(state_data['museums'])

# Art museums missing scores
missing_scores = [
    m for m in museums 
    if m.get('primary_domain') == 'Art'
    and m.get('reputation') is not None  # Has some data
    and not (m.get('impressionist_strength') or m.get('modern_contemporary_strength'))  # But no art scores
]

print(f"Art museums missing scores: {len(missing_scores)}\n")

# Check evidence availability
wiki_cache_dir = Path('data/cache/phase1_5')
http_cache_dir = Path('data/cache/http')

evidence_stats = {
    'has_wikipedia': 0,
    'has_website_content': 0,
    'has_topics': 0,
    'has_notes': 0,
    'has_nothing': 0,
}

for museum in missing_scores:
    museum_id = museum.get('museum_id')
    state = museum.get('state_province')
    
    has_evidence = False
    
    # Check Wikipedia cache
    if wiki_cache_dir.exists() and museum_id:
        wiki_file = wiki_cache_dir / f"{museum_id}.json"
        if wiki_file.exists():
            wiki_data = json.load(open(wiki_file, encoding='utf-8'))
            if wiki_data.get('found') and wiki_data.get('extract'):
                evidence_stats['has_wikipedia'] += 1
                has_evidence = True
    
    # Check HTTP cache
    website = museum.get('website')
    if website and http_cache_dir.exists():
        # Website content might be cached
        # Just check if directory exists with any files
        if any(http_cache_dir.glob('*.json')):
            evidence_stats['has_website_content'] += 1
            has_evidence = True
    
    # Check structured data
    if museum.get('topics'):
        evidence_stats['has_topics'] += 1
        has_evidence = True
    
    if museum.get('notes') and len(museum.get('notes', '')) > 50:
        evidence_stats['has_notes'] += 1
        has_evidence = True
    
    if not has_evidence:
        evidence_stats['has_nothing'] += 1

print("Evidence availability for museums missing scores:")
print(f"  Has Wikipedia data: {evidence_stats['has_wikipedia']}")
print(f"  Has website content cache: {evidence_stats['has_website_content']}")
print(f"  Has topics field: {evidence_stats['has_topics']}")
print(f"  Has useful notes: {evidence_stats['has_notes']}")
print(f"  Has NO evidence: {evidence_stats['has_nothing']}")

print("\n" + "="*60)
print("RECOMMENDATIONS:")
print("="*60)

# Analyze score_notes for common patterns
insufficient_patterns = {
    'wrong_museum': 0,
    'city_only': 0,
    'no_collection': 0,
    'other': 0,
}

print("\nAnalyzing why Phase 2 returned null:")
for museum in missing_scores[:50]:  # Sample 50
    notes = (museum.get('score_notes') or '').lower()
    if 'wrong' in notes or 'airport' in notes or 'instrument' in notes:
        insufficient_patterns['wrong_museum'] += 1
    elif 'city' in notes and 'not the museum' in notes:
        insufficient_patterns['city_only'] += 1
    elif 'no' in notes and ('collection' in notes or 'permanent' in notes):
        insufficient_patterns['no_collection'] += 1
    else:
        insufficient_patterns['other'] += 1

print(f"  Wrong Wikipedia article matched: {insufficient_patterns['wrong_museum']}")
print(f"  Only city data, not museum: {insufficient_patterns['city_only']}")
print(f"  No collection information: {insufficient_patterns['no_collection']}")
print(f"  Other insufficient evidence: {insufficient_patterns['other']}")

print("\n" + "="*60)
print("IMPROVEMENT STRATEGIES:")
print("="*60)
print("""
1. IMPROVE WIKIPEDIA MATCHING (Phase 1.5):
   - Add better search query disambiguation
   - Try "Museum Name + City + Museum" in search
   - Validate result contains museum keywords
   - Cost: $0 (free Wikipedia API)
   
2. EXTRACT WEBSITE CONTENT (Phase 0.7):
   - Run phase0_7_website.py on missing museums
   - Extract collection/about pages
   - Parse homepage for collection highlights
   - Cost: $0 (just server time)
   
3. IMPROVE PHASE 2 PROMPT:
   - Allow more inference from museum type/name
   - "Impressionist Museum" → likely imp strength 4+
   - "Contemporary Arts Center" → likely mod strength 4+
   - Cost: ~$3 to rescore 147 museums
   
4. MANUAL CURATION (targeted):
   - Focus on major museums with missing scores
   - Add collection_highlights field manually
   - Phoenix Art Museum, Dallas Museum of Art, etc.
   - Cost: human time for ~20-30 flagships

RECOMMENDED NEXT STEPS:
1. Run Phase 1.5 with improved Wikipedia search on all-states
2. Run Phase 0.7 website extraction on museums with websites
3. Re-run Phase 2 with --force on states with improved evidence
4. Accept remaining gaps (likely small/regional museums)
""")

# Show museums that would benefit most from better evidence
print("\nHigh-value museums to prioritize for evidence gathering:")
top_priority = [
    m for m in missing_scores
    if m.get('reputation', 3) <= 2  # National or better
    and 'Museum of Art' in m.get('museum_name', '')
][:15]

for i, m in enumerate(top_priority, 1):
    print(f"{i:2}. {m['museum_name']} ({m['state_province']})")
    print(f"    Reputation: {m.get('reputation')}, Website: {m.get('website', 'None')[:50]}")
