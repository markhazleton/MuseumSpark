"""Validate Phase 2 cache vs state file field consistency."""

import json
from pathlib import Path
from collections import defaultdict

STATES_DIR = Path("data/states")
CACHE_DIR = Path("data/cache/phase2")

def main():
    print("=== Phase 2 Cache vs State File Validation ===\n")
    
    # Load all museums from state files
    museums_by_id = {}
    for state_file in STATES_DIR.glob("*.json"):
        state_data = json.loads(state_file.read_text(encoding="utf-8"))
        for museum in state_data.get("museums", []):
            museum_id = museum.get("museum_id")
            if museum_id:
                museums_by_id[museum_id] = museum
    
    print(f"Total museums in state files: {len(museums_by_id)}")
    
    # Find all Phase 2 cache files
    cache_files = list(CACHE_DIR.rglob("*.json"))
    print(f"Total Phase 2 cache files: {len(cache_files)}")
    
    # Field mapping check
    cache_fields = [
        "impressionist_strength",
        "modern_contemporary_strength", 
        "historical_context_score",
        "reputation",
        "collection_tier",
        "confidence",
        "score_notes"
    ]
    
    matches = []
    mismatches = []
    cache_only = []
    state_not_found = []
    
    for cache_file in cache_files:
        try:
            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            museum_id = cache_data.get("museum_id")
            
            if not museum_id:
                continue
                
            if museum_id not in museums_by_id:
                state_not_found.append(museum_id)
                continue
            
            museum = museums_by_id[museum_id]
            
            # Check if museum in state has scores
            state_has_scores = museum.get("impressionist_strength") is not None
            cache_success = cache_data.get("success", False)
            
            if cache_success and state_has_scores:
                # Verify field values match
                all_match = True
                for field in cache_fields:
                    cache_val = cache_data.get(field)
                    state_val = museum.get(field)
                    if cache_val != state_val and not (cache_val is None and state_val is None):
                        all_match = False
                        break
                
                if all_match:
                    matches.append(museum_id)
                else:
                    mismatches.append((museum_id, cache_data, museum))
            elif cache_success and not state_has_scores:
                cache_only.append((museum_id, cache_data.get("scored_at")))
                
        except Exception as e:
            print(f"Error processing {cache_file}: {e}")
    
    print(f"\n=== Validation Results ===")
    print(f"✓ Cache matches state: {len(matches)}")
    print(f"✗ Cache/state mismatch: {len(mismatches)}")
    print(f"⚠ Cache only (not in state): {len(cache_only)}")
    print(f"! Museum not found in state: {len(state_not_found)}")
    
    # Show cache-only museums (these should have been written to state)
    if cache_only:
        print(f"\n=== Museums Scored in Cache but Missing from State ===")
        print(f"Count: {len(cache_only)}")
        print("Sample (showing first 10):")
        for museum_id, scored_at in cache_only[:10]:
            museum = museums_by_id.get(museum_id, {})
            name = museum.get("museum_name", "Unknown")
            print(f"  {name} ({museum_id})")
            print(f"    Scored at: {scored_at}")
    
    # Show mismatches
    if mismatches:
        print(f"\n=== Field Value Mismatches ===")
        print(f"Count: {len(mismatches)}")
        print("Sample (showing first 3):")
        for museum_id, cache_data, museum in mismatches[:3]:
            print(f"\n  {museum.get('museum_name')} ({museum_id})")
            for field in cache_fields:
                cache_val = cache_data.get(field)
                state_val = museum.get(field)
                if cache_val != state_val:
                    print(f"    {field}: cache={cache_val}, state={state_val}")
    
    # Summary statistics
    print(f"\n=== Summary ===")
    total_in_cache = len(matches) + len(mismatches) + len(cache_only)
    print(f"Total successful Phase 2 scores in cache: {total_in_cache}")
    print(f"Successfully synchronized to state: {len(matches) + len(mismatches)}")
    print(f"Failed to sync (cache only): {len(cache_only)}")
    
    if cache_only:
        print(f"\n⚠️  {len(cache_only)} museums have Phase 2 scores in cache but not in state files!")
        print("This suggests Phase 2 may not be writing to state files correctly.")

if __name__ == "__main__":
    main()
