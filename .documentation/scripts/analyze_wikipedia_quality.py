"""Analyze Wikipedia cache quality for art museums."""

import json
from pathlib import Path
from collections import Counter

STATES_DIR = Path("data/states")

def main():
    print("=== Wikipedia Cache Quality Analysis ===\n")
    
    # Load all museums from state files
    all_museums = []
    for state_file in STATES_DIR.glob("*.json"):
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
            museums = state_data.get("museums", [])
            state_code = state_file.stem
            for museum in museums:
                museum["state_code"] = state_code
                all_museums.append(museum)
        except Exception as e:
            print(f"Error loading {state_file}: {e}")
    
    print(f"Total museums loaded: {len(all_museums)}")
    
    # Filter art museums
    art_museums = [m for m in all_museums if m.get("is_scoreable")]
    print(f"Art museums (is_scoreable=True): {len(art_museums)}")
    
    # Analyze Wikipedia cache quality
    has_score_count = 0
    no_score_count = 0
    wrong_article = []
    city_article = []
    good_article = []
    no_wiki_cache = []
    
    for museum in art_museums:
        museum_id = museum.get("museum_id", "")
        state_code = museum.get("state_code", "")
        museum_name = museum.get("museum_name", "")
        city = museum.get("city", "")
        
        # Check if has scores
        has_score = museum.get("impressionist_art_strength") is not None
        if has_score:
            has_score_count += 1
        else:
            no_score_count += 1
        
        # Check Wikipedia cache
        wiki_cache = STATES_DIR / state_code / museum_id / "cache" / "wikipedia.json"
        if not wiki_cache.exists():
            no_wiki_cache.append((museum_name, city, has_score))
            continue
        
        try:
            wiki_data = json.loads(wiki_cache.read_text(encoding="utf-8"))
            
            # Analyze Wikipedia article quality
            if not wiki_data.get("found"):
                no_wiki_cache.append((museum_name, city, has_score))
                continue
                
            extract = wiki_data.get("extract", "").lower()
            title = wiki_data.get("title", "")
            
            # Check for wrong article indicators
            if "city" in extract[:200] and "population" in extract[:400]:
                city_article.append((museum_name, city, title, has_score))
            elif "airport" in extract[:200] or "station" in extract[:200]:
                wrong_article.append((museum_name, city, title, has_score))
            else:
                good_article.append((museum_name, city, title, has_score))
                
        except Exception as e:
            print(f"Error processing Wikipedia cache for {museum_name}: {e}")
    
    print(f"\n=== Scoring Status ===")
    print(f"Museums with scores: {has_score_count}")
    print(f"Museums without scores: {no_score_count}")
    
    print(f"\n=== Wikipedia Cache Status ===")
    print(f"Has Wikipedia cache: {len(good_article) + len(city_article) + len(wrong_article)}")
    print(f"No Wikipedia cache: {len(no_wiki_cache)}")
    
    print(f"\n=== Wikipedia Article Quality ===")
    print(f"Good museum articles: {len(good_article)}")
    print(f"City articles (wrong): {len(city_article)}")
    print(f"Other wrong articles: {len(wrong_article)}")
    
    # Show examples of city articles
    print(f"\n=== Sample City Articles (Should be Museum) ===")
    for name, city, title, has_score in city_article[:10]:
        score_status = "✓ HAS SCORES" if has_score else "✗ NO SCORES"
        print(f"  {name} ({city}) → {title} [{score_status}]")
    
    # Show examples of wrong articles
    if wrong_article:
        print(f"\n=== Sample Wrong Articles ===")
        for name, city, title, has_score in wrong_article[:5]:
            score_status = "✓ HAS SCORES" if has_score else "✗ NO SCORES"
            print(f"  {name} ({city}) → {title} [{score_status}]")
    
    # Count museums with good articles but no scores
    good_no_score = [x for x in good_article if not x[3]]
    print(f"\n=== Good Wikipedia BUT No Scores ===")
    print(f"Count: {len(good_no_score)}")
    if good_no_score:
        print("Sample:")
        for name, city, title, _ in good_no_score[:10]:
            print(f"  {name} ({city}) → {title}")
    
    # Museums with no Wikipedia cache but no scores
    no_wiki_no_score = [x for x in no_wiki_cache if not x[2]]
    print(f"\n=== No Wikipedia Cache AND No Scores ===")
    print(f"Count: {len(no_wiki_no_score)}")
    if no_wiki_no_score:
        print("Sample:")
        for name, city, _ in no_wiki_no_score[:10]:
            print(f"  {name} ({city})")

if __name__ == "__main__":
    main()
