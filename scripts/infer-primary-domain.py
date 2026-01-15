#!/usr/bin/env python3
"""
Infer primary_domain from museum names and types.

This script analyzes museum names to determine their primary focus area:
- Art: Museums primarily focused on art collections
- History: Historical museums, heritage sites, etc.
- Science: Science centers, natural history, etc.
- Mixed: Multiple domains or unclear focus
"""

import json
import re
from pathlib import Path
from typing import Any

# Keywords for domain classification
DOMAIN_KEYWORDS = {
    "Art": [
        r'\bart\b', r'\barts\b', r'\bartist\b', r'\bgallery\b', r'\bgalleries\b',
        r'\bmuseum of art\b', r'\bvisual arts\b', r'\bcontemporary\b', r'\bmodern art\b',
        r'\bfine arts\b', r'\bpainting\b', r'\bsculpture\b', r'\bcrafts\b', r'\bcraft\b',
        r'\bceramics\b', r'\bphotography\b', r'\bdesign\b'
    ],
    "History": [
        r'\bhistor\w*\b', r'\bheritage\b', r'\barchaeology\b', r'\barcheology\b',
        r'\bmuseum of history\b', r'\bhistorical society\b', r'\bpreservation\b',
        r'\bfrontier\b', r'\bpioneer\b', r'\bwestern\b', r'\bnative\b', r'\bcultural center\b',
        r'\bcivil war\b', r'\bmilitary\b', r'\bwartime\b', r'\bmaritime\b', r'\baviation\b'
    ],
    "Science": [
        r'\bscience\b', r'\bnatural history\b', r'\bnature\b', r'\bplanetarium\b',
        r'\bobservatory\b', r'\baquarium\b', r'\bzoo\b', r'\bbotanic\b', r'\bbotanical\b',
        r'\bchildren\'?s museum\b', r'\bdiscovery\b', r'\bspace\b', r'\bmarine\b',
        r'\bwildlife\b', r'\benvironment\b', r'\becology\b'
    ],
    "Mixed": [
        r'\bmixed\b', r'\bcultural\b', r'\binterpretive\b', r'\bcenter for\b',
        r'\bmulti-disciplinary\b', r'\bcommunity museum\b'
    ]
}


def infer_primary_domain(museum_name: str, museum_type: str | None) -> str:
    """
    Infer primary domain from museum name and type.
    
    Returns: "Art", "History", "Science", "Mixed", or None
    """
    # Combine name and type for analysis
    text = museum_name.lower()
    if museum_type and museum_type != "Unknown":
        text += " " + museum_type.lower()
    
    # Count matches for each domain
    scores = {}
    for domain, patterns in DOMAIN_KEYWORDS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1
        if score > 0:
            scores[domain] = score
    
    if not scores:
        return None
    
    # Return domain with highest score
    max_score = max(scores.values())
    top_domains = [domain for domain, score in scores.items() if score == max_score]
    
    # If multiple domains tied, prefer Art > History > Science > Mixed
    priority = ["Art", "History", "Science", "Mixed"]
    for domain in priority:
        if domain in top_domains:
            return domain
    
    return top_domains[0]


def process_state_file(filepath: Path, dry_run: bool = False) -> tuple[int, int]:
    """
    Process a single state file and infer primary_domain for museums.
    
    Returns: (total_processed, total_updated)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    museums = data.get('museums', [])
    total_processed = 0
    total_updated = 0
    
    for museum in museums:
        total_processed += 1
        
        # Skip if already has primary_domain
        if museum.get('primary_domain'):
            continue
        
        # Infer from name and type
        inferred = infer_primary_domain(
            museum.get('museum_name', ''),
            museum.get('museum_type')
        )
        
        if inferred:
            museum['primary_domain'] = inferred
            total_updated += 1
            
            # Add to row_notes_internal
            notes = museum.get('row_notes_internal', '')
            if notes:
                notes += '; '
            notes += f'Inferred primary_domain={inferred} from name/type'
            museum['row_notes_internal'] = notes
    
    if not dry_run and total_updated > 0:
        # Update last_updated timestamp
        from datetime import datetime, timezone
        data['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return total_processed, total_updated


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Infer primary_domain from museum names')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--state', help='Process specific state code (e.g., CA)')
    args = parser.parse_args()
    
    data_dir = Path(__file__).parent.parent / 'data' / 'states'
    
    if args.state:
        state_files = [data_dir / f'{args.state}.json']
    else:
        state_files = sorted(data_dir.glob('*.json'))
    
    total_processed = 0
    total_updated = 0
    
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Inferring primary_domain from museum names...")
    print()
    
    for filepath in state_files:
        if not filepath.exists():
            print(f"[SKIP] {filepath.name} - File not found")
            continue
        
        try:
            processed, updated = process_state_file(filepath, args.dry_run)
            total_processed += processed
            total_updated += updated
            
            if updated > 0:
                print(f"[OK] {filepath.name}: {updated}/{processed} museums updated")
            else:
                print(f"[OK] {filepath.name}: No updates needed")
                
        except Exception as e:
            print(f"[ERROR] {filepath.name}: {e}")
    
    print()
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Summary:")
    print(f"  Total museums processed: {total_processed}")
    print(f"  Total museums updated: {total_updated}")
    
    if not args.dry_run and total_updated > 0:
        print()
        print("Next steps:")
        print("  1. Run: python scripts/build-index.py")
        print("  2. Review changes with: git diff data/states/")
        print("  3. Commit if satisfied")


if __name__ == '__main__':
    main()
