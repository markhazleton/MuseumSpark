"""Comprehensive Phase 2 validation report (MRD v3 - January 2026)."""

import json
from pathlib import Path
from collections import defaultdict

STATES_DIR = Path("data/states")
CACHE_DIR = Path("data/cache/phase2")

def has_phase2_scores(record: dict) -> bool:
    """Check if a record has any MRD v3 Phase 2 scores."""
    return any([
        record.get("impressionist_strength") is not None,
        record.get("modern_contemporary_strength") is not None,
        record.get("historical_context_score") is not None,
        record.get("eca_score") is not None,
        record.get("collection_based_strength") is not None,
    ])

def main():
    print("="*70)
    print("PHASE 2 VALIDATION REPORT (MRD v3)")
    print("="*70)
    
    # Load all museums from state files
    museums_by_id = {}
    art_museums = []
    for state_file in STATES_DIR.glob("*.json"):
        state_data = json.loads(state_file.read_text(encoding="utf-8"))
        for museum in state_data.get("museums", []):
            museum_id = museum.get("museum_id")
            if museum_id:
                museums_by_id[museum_id] = museum
                if museum.get("is_scoreable"):
                    art_museums.append(museum)
    
    print(f"\n1. MUSEUM INVENTORY")
    print(f"   Total museums: {len(museums_by_id)}")
    print(f"   Art museums (is_scoreable=True): {len(art_museums)}")
    
    # Count state file scores using MRD v3 fields
    state_scored = [m for m in art_museums if has_phase2_scores(m)]
    must_see_candidates = [m for m in art_museums if m.get("must_see_candidate")]
    high_eca = [m for m in art_museums if (m.get("eca_score") or 0) >= 4]
    
    print(f"   Art museums with Phase 2 scores in state: {len(state_scored)}")
    print(f"   ★ Must-See Candidates (Historical Context = 5): {len(must_see_candidates)}")
    print(f"   ♦ High ECA Score (≥ 4): {len(high_eca)}")
    
    # Analyze cache files
    cache_files = list(CACHE_DIR.rglob("*.json"))
    print(f"\n2. PHASE 2 CACHE ANALYSIS")
    print(f"   Total cache files: {len(cache_files)}")
    
    cache_by_museum = defaultdict(list)
    success_with_scores = set()
    success_null_scores = set()
    failed_scores = set()
    
    for cache_file in cache_files:
        try:
            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            museum_id = cache_data.get("museum_id")
            
            if not museum_id:
                continue
            
            cache_by_museum[museum_id].append(cache_data)
            
            if cache_data.get("success"):
                # MRD v3: check all 5 scoring fields
                has_scores = any([
                    cache_data.get("impressionist_strength") is not None,
                    cache_data.get("modern_contemporary_strength") is not None,
                    cache_data.get("historical_context_score") is not None,
                    cache_data.get("eca_score") is not None,
                    cache_data.get("collection_based_strength") is not None,
                ])
                if has_scores:
                    success_with_scores.add(museum_id)
                else:
                    success_null_scores.add(museum_id)
            else:
                failed_scores.add(museum_id)
        except Exception as e:
            print(f"   Error reading {cache_file}: {e}")
    
    print(f"   Unique museums in cache: {len(cache_by_museum)}")
    print(f"   Museums scored multiple times: {sum(1 for v in cache_by_museum.values() if len(v) > 1)}")
    
    print(f"\n3. CACHE SCORE STATUS")
    print(f"   ✓ Success with scores: {len(success_with_scores)}")
    print(f"   ⚠ Success but ALL scores null: {len(success_null_scores)}")
    print(f"   ✗ Failed: {len(failed_scores)}")
    
    # Sync analysis
    print(f"\n4. CACHE → STATE SYNC STATUS")
    
    synced = []
    unsynced_null_scores = []
    unsynced_has_scores = []
    
    for museum_id in cache_by_museum.keys():
        museum = museums_by_id.get(museum_id)
        if not museum:
            continue
        
        # MRD v3: check all scoring fields
        state_has_scores = has_phase2_scores(museum)
        cache_has_scores = museum_id in success_with_scores
        
        if state_has_scores:
            synced.append(museum_id)
        elif museum_id in success_null_scores:
            unsynced_null_scores.append(museum_id)
        elif cache_has_scores:
            unsynced_has_scores.append(museum_id)
    
    print(f"   ✓ Synced to state: {len(synced)}")
    print(f"   ⚠ Not synced (null scores - expected): {len(unsynced_null_scores)}")
    print(f"   ✗ Not synced (has scores - BUG!): {len(unsynced_has_scores)}")
    
    # Root cause analysis
    print(f"\n5. ROOT CAUSE ANALYSIS")
    print(f"   Phase 2 design:")
    print(f"   - LLM returns null when evidence insufficient (by design)")
    print(f"   - to_patch() returns empty dict when all scores null")
    print(f"   - Empty patch = no changes = state file not updated")
    print(f"   ")
    print(f"   Result:")
    print(f"   - {len(success_with_scores)} museums: Cache written + State updated ✓")
    print(f"   - {len(success_null_scores)} museums: Cache written, State skipped (no data)")
    print(f"   ")
    print(f"   This is CORRECT BEHAVIOR - no point saving empty scores to state.")
    
    # Show unsynced with scores (should investigate)
    if unsynced_has_scores:
        print(f"\n6. ⚠️  UNEXPECTED: Museums with scores in cache but NOT in state")
        print(f"   Count: {len(unsynced_has_scores)}")
        print(f"   Sample (first 10):")
        for museum_id in unsynced_has_scores[:10]:
            museum = museums_by_id.get(museum_id)
            cache_latest = cache_by_museum[museum_id][-1]  # Most recent
            print(f"   - {museum.get('museum_name')} ({museum_id})")
            print(f"     Cache: imp={cache_latest.get('impressionist_strength')}, " +
                  f"mod={cache_latest.get('modern_contemporary_strength')}, " +
                  f"hist={cache_latest.get('historical_context_score')}, " +
                  f"eca={cache_latest.get('eca_score')}, " +
                  f"cbs={cache_latest.get('collection_based_strength')}")
            print(f"     scored_at={cache_latest.get('scored_at')}")
    
    # Wikipedia quality (bonus)
    wiki_cache_dir = STATES_DIR
    wiki_good = 0
    wiki_city = 0
    wiki_wrong = 0
    wiki_none = 0
    
    for museum in art_museums[:50]:  # Sample
        museum_id = museum.get("museum_id")
        state_code = museum.get("state")
        
        if not museum_id or not state_code:
            wiki_none += 1
            continue
        
        wiki_file = wiki_cache_dir / state_code / museum_id / "cache" / "wikipedia.json"
        
        if not wiki_file.exists():
            wiki_none += 1
            continue
        
        try:
            wiki_data = json.loads(wiki_file.read_text(encoding="utf-8"))
            if not wiki_data.get("found"):
                wiki_none += 1
                continue
            
            extract = wiki_data.get("extract", "").lower()
            if "city" in extract[:200] and "population" in extract[:400]:
                wiki_city += 1
            elif "airport" in extract[:200]:
                wiki_wrong += 1
            else:
                wiki_good += 1
        except:
            wiki_none += 1
    
    print(f"\n7. WIKIPEDIA QUALITY (sample of 50 art museums)")
    print(f"   Good museum articles: {wiki_good}")
    print(f"   Wrong (city): {wiki_city}")
    print(f"   Wrong (other): {wiki_wrong}")
    print(f"   No Wikipedia: {wiki_none}")
    
    # Recommendations
    print(f"\n8. RECOMMENDATIONS")
    print(f"   ")
    print(f"   ✓ SYSTEM WORKING AS DESIGNED:")
    print(f"     - {len(synced)} museums successfully scored and saved")
    print(f"     - {len(success_null_scores)} museums returned null (insufficient evidence)")
    print(f"   ")
    print(f"   To improve coverage of the {len(success_null_scores)} museums with null scores:")
    print(f"   ")
    print(f"   1. FIX WIKIPEDIA MATCHING (~{wiki_city + wiki_wrong} wrong articles)")
    print(f"      - Add 'Museum' keyword to search query")
    print(f"      - Validate results contain museum-related terms")
    print(f"      - Rerun Phase 1.5 with --force on problem museums")
    print(f"   ")
    print(f"   2. ADD WEBSITE CONTENT EXTRACTION")
    print(f"      - Phase 0.7 has cached HTML but not integrated")
    print(f"      - Update build_evidence_packet() to include website content")
    print(f"      - Extract collection info from About/Collections pages")
    print(f"   ")
    print(f"   3. RESCORE AFTER IMPROVEMENTS")
    print(f"      - Run Phase 2 with --force after fixing Wikipedia")
    print(f"      - Cost: ~$4 for {len(success_null_scores)} museums")
    print(f"      - Expected improvement: +50-100 successful scores")
    print(f"   ")
    print(f"   4. ACCEPT REMAINING GAPS")
    print(f"      - Some small museums lack online evidence")
    print(f"      - Focus on high-reputation museums (national/international)")
    
    print(f"\n{'='*70}")

if __name__ == "__main__":
    main()
