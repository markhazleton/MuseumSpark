"""Check Wikipedia cache coverage for art museums."""

import json
from pathlib import Path

STATES_DIR = Path("data/states")
INDEX_FILE = Path("data/index/all-museums.json")

def main():
    # Load all museums
    index_data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    museums = index_data.get("museums", [])
    
    # Filter art museums
    art_museums = [m for m in museums if m.get("is_scoreable")]
    
    print(f"\n=== Wikipedia Cache Coverage ===")
    print(f"Total art museums: {len(art_museums)}")
    
    # Check Wikipedia cache
    has_wiki = []
    no_wiki = []
    has_scores = []
    no_scores = []
    
    for museum in art_museums:
        museum_id = museum.get("id")
        state_code = museum.get("state")
        
        # Skip if missing required fields
        if not museum_id or not state_code:
            continue
        
        # Check Wikipedia cache
        wiki_cache = STATES_DIR / state_code / museum_id / "cache" / "wikipedia.json"
        
        # Check scores
        has_score = museum.get("impressionist_art_strength") is not None
        
        if wiki_cache.exists():
            has_wiki.append(museum_id)
            if has_score:
                has_scores.append(museum_id)
        else:
            no_wiki.append(museum_id)
            if not has_score:
                no_scores.append(museum_id)
    
    print(f"\nHas Wikipedia cache: {len(has_wiki)}")
    print(f"No Wikipedia cache: {len(no_wiki)}")
    print(f"\nHas Wikipedia + scores: {len(has_scores)}")
    print(f"No Wikipedia + no scores: {len(no_scores)}")
    
    # Correlation analysis
    print(f"\n=== Correlation Analysis ===")
    print(f"Museums with Wikipedia cache that have scores: {len(has_scores)}/{len(has_wiki)} ({len(has_scores)/len(has_wiki)*100:.1f}%)")
    print(f"Museums without Wikipedia cache that have no scores: {len(no_scores)}/{len(no_wiki)} ({len(no_scores)/len(no_wiki)*100:.1f}%)")
    
    # Sample museums without Wikipedia
    print(f"\n=== Sample Museums Without Wikipedia Cache ===")
    for museum_id in no_wiki[:10]:
        museum = next(m for m in art_museums if m.get("id") == museum_id)
        name = museum.get("museum_name")
        city = museum.get("city")
        state = museum.get("state")
        print(f"  {name} ({city}, {state})")

if __name__ == "__main__":
    main()
