#!/usr/bin/env python3
"""
Analyze matching between all-museums.json and museums.csv
"""
import json
import csv
from pathlib import Path
import re
from difflib import SequenceMatcher

def normalize_placeholders(value):
    """Normalize placeholder values to None"""
    if value is None:
        return None
    if isinstance(value, str):
        value_lower = value.strip().lower()
        # Known placeholder patterns
        placeholders = [
            'unknown', 'not known', 'n/a', 'na', 'tbd', 'to be determined',
            'none', 'null', 'not available', 'not provided', 'not applicable',
            'pending', 'coming soon', '--', '---', 'tba', 'to be announced'
        ]
        if value_lower in placeholders or value.strip() == '':
            return None
    return value

def normalize_name(name):
    """Normalize museum name for matching"""
    if not name:
        return ""
    # Remove common museum words and punctuation
    name = name.lower()
    name = re.sub(r'\b(museum|center|gallery|institute|foundation|inc|society|association)\b', '', name)
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def similarity_ratio(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a, b).ratio()

def main():
    # Load data
    print("\n🔍 MATCHING ANALYSIS: all-museums.json vs museums.csv")
    print("(Fuzzy matching on STATE + NAME only)")
    print("━" * 60 + "\n")
    
    with open('data/index/all-museums.json', 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    csv_museums = []
    with open('data/museums.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        csv_museums = list(reader)
    
    print(f"Your data: {len(all_data['museums'])} museums")
    print(f"CSV data: {len(csv_museums)} museums\n")
    
    # State mapping
    state_map = {
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
    
    # Create CSV lookup by state
    csv_by_state = {}
    for m in csv_museums:
        state = m.get('State (Administrative Location)', '')
        if state not in csv_by_state:
            csv_by_state[state] = []
        csv_by_state[state].append(m)
    
    # Matching
    exact_matches = []
    fuzzy_matches = []
    no_matches = []
    
    for museum in all_data['museums']:
        state_code = state_map.get(museum['state_province'])
        if not state_code:
            continue
            
        csv_state_museums = csv_by_state.get(state_code, [])
        museum_name = museum['museum_name']
        museum_name_norm = normalize_name(museum_name)
        city = museum['city'].lower()
        
        # Try exact match
        exact = None
        for csv_m in csv_state_museums:
            if csv_m['Museum Name'] == museum_name:
                exact = csv_m
                break
        
        if exact:
            exact_matches.append({
                'your_name': museum_name,
                'csv_name': exact['Museum Name'],
                'city': museum['city'],
                'state': state_code,
                'csv_phone': normalize_placeholders(exact.get('Phone Number', '')),
                'csv_type': normalize_placeholders(exact.get('Museum Type', ''))
            })
            continue
        
        # Try fuzzy match (state + name only, no city requirement)
        best_match = None
        best_ratio = 0.0
        for csv_m in csv_state_museums:
            csv_name_norm = normalize_name(csv_m['Museum Name'])
            
            ratio = similarity_ratio(museum_name_norm, csv_name_norm)
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = csv_m
        
        if best_match and best_ratio >= 0.7:
            fuzzy_matches.append({
                'your_name': museum_name,
                'csv_name': best_match['Museum Name'],
                'city': museum['city'],
                'state': state_code,
                'similarity': f"{best_ratio*100:.1f}%",
                'csv_phone': normalize_placeholders(best_match.get('Phone Number', '')),
                'csv_type': normalize_placeholders(best_match.get('Museum Type', ''))
            })
        else:
            no_matches.append({
                'name': museum_name,
                'city': museum['city'],
                'state': state_code
            })
    
    total = len(exact_matches) + len(fuzzy_matches) + len(no_matches)
    matched_total = len(exact_matches) + len(fuzzy_matches)
    
    print("📊 RESULTS:")
    print(f"  Exact matches: {len(exact_matches)} ({len(exact_matches)/total*100:.1f}%)")
    print(f"  Fuzzy matches: {len(fuzzy_matches)} ({len(fuzzy_matches)/total*100:.1f}%)")
    print(f"  Total matched: {matched_total} ({matched_total/total*100:.1f}%)")
    print(f"  No match: {len(no_matches)} ({len(no_matches)/total*100:.1f}%)\n")
    
    # Show samples
    if exact_matches:
        print("✅ Sample Exact Matches (first 5):")
        for m in exact_matches[:5]:
            phone = f"Phone: {m['csv_phone']}" if m['csv_phone'] else "Phone: null"
            print(f"  • {m['your_name']} ({m['city']}, {m['state']}) - {phone}")
    
    if fuzzy_matches:
        print("\n≈ Sample Fuzzy Matches (first 5):")
        for m in fuzzy_matches[:5]:
            print(f"  • Your: {m['your_name']}")
            print(f"    CSV: {m['csv_name']} (similarity: {m['similarity']})")
            phone = f"Phone: {m['csv_phone']}" if m['csv_phone'] else "Phone: null"
            print(f"    {phone}")
    
    if no_matches:
        print(f"\n❌ Sample Unmatched (first 10 of {len(no_matches)}):")
        for m in no_matches[:10]:
            print(f"  • {m['name']} ({m['city']}, {m['state']})")
    
    # Value assessment
    print("\n" + "="*60)
    print("💡 VALUE ASSESSMENT:")
    if matched_total / total >= 0.7:
        print("  ✅ EXCELLENT match rate - CSV highly valuable for enrichment!")
        print(f"  → {matched_total} museums can get CSV data (phone, type, coords)")
    elif matched_total / total >= 0.5:
        print("  ⚠️ MODERATE match rate - CSV useful but not comprehensive")
        print(f"  → {matched_total} museums can benefit from CSV enrichment")
    else:
        print("  ❌ LOW match rate - Limited value for your dataset")
        print("  → Your museums may have different naming or be from different source")
    
    if matched_total > 0:
        with_phone = sum(1 for m in exact_matches + fuzzy_matches if m.get('csv_phone'))
        print(f"\n  📞 {with_phone} matched museums have phone numbers in CSV")
        print(f"     ({with_phone/matched_total*100:.1f}% of matches)")

if __name__ == '__main__':
    main()
