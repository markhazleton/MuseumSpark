"""Build enriched museum index with tour-planning scores for the web app."""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INDEX_DIR = DATA_DIR / "index"
STATES_DIR = DATA_DIR / "states"


def load_json(path: Path) -> Any:
    """Load JSON file."""
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, data: Any) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8'
    )


def load_museum_scores(state_code: str) -> dict[str, dict]:
    """Load tour-planning scores for all museums in a state."""
    scores_map = {}
    state_dir = STATES_DIR / state_code
    
    if not state_dir.exists():
        return scores_map
    
    # Iterate through museum folders
    for museum_folder in state_dir.glob('m_*'):
        cache_dir = museum_folder / 'cache'
        deep_dive_file = cache_dir / 'deep_dive_v1.json'
        
        if deep_dive_file.exists():
            try:
                deep_dive = load_json(deep_dive_file)
                museum_id = deep_dive.get('state_file_updates', {}).get('museum_id')
                tour_scores = deep_dive.get('tour_planning_scores')
                
                if museum_id and tour_scores:
                    # Extract all scoring dimensions
                    scores_map[museum_id] = {
                        # Art Movement Scores (1-10)
                        'contemporary_score': tour_scores.get('contemporary_score'),
                        'modern_score': tour_scores.get('modern_score'),
                        'impressionist_score': tour_scores.get('impressionist_score'),
                        'expressionist_score': tour_scores.get('expressionist_score'),
                        'classical_score': tour_scores.get('classical_score'),
                        
                        # Geographic/Cultural Focus (1-10)
                        'american_art_score': tour_scores.get('american_art_score'),
                        'european_art_score': tour_scores.get('european_art_score'),
                        'asian_art_score': tour_scores.get('asian_art_score'),
                        'african_art_score': tour_scores.get('african_art_score'),
                        
                        # Medium Scores (1-10)
                        'painting_score': tour_scores.get('painting_score'),
                        'sculpture_score': tour_scores.get('sculpture_score'),
                        'decorative_arts_score': tour_scores.get('decorative_arts_score'),
                        'photography_score': tour_scores.get('photography_score'),
                        
                        # Collection & Experience (1-10)
                        'collection_depth': tour_scores.get('collection_depth'),
                        'collection_quality': tour_scores.get('collection_quality'),
                        'exhibition_frequency': tour_scores.get('exhibition_frequency'),
                        'family_friendly_score': tour_scores.get('family_friendly_score'),
                        'educational_value_score': tour_scores.get('educational_value_score'),
                        'architecture_score': tour_scores.get('architecture_score'),
                        
                        # Context
                        'scoring_rationale': tour_scores.get('scoring_rationale'),
                    }
                    
                    # Also extract summaries if available
                    summaries_file = museum_folder / 'summaries.json'
                    if summaries_file.exists():
                        summaries = load_json(summaries_file)
                        scores_map[museum_id].update({
                            'summary_short': summaries.get('summary_short'),
                            'summary_long': summaries.get('summary_long'),
                            'collection_highlights': summaries.get('collection_highlights', []),
                            'signature_artists': summaries.get('signature_artists', []),
                            'visitor_tips': summaries.get('visitor_tips', []),
                            'best_for': summaries.get('best_for'),
                        })
                        
            except Exception as e:
                print(f"Warning: Failed to load scores for {museum_folder.name}: {e}")
    
    return scores_map


def main():
    """Build enriched all-museums.json with tour-planning scores."""
    
    print("Building enriched museum index...")
    
    # Load base index
    all_museums_file = INDEX_DIR / 'all-museums.json'
    if not all_museums_file.exists():
        raise FileNotFoundError(f"Missing {all_museums_file}")
    
    base_index = load_json(all_museums_file)
    museums = base_index.get('museums', [])
    
    # Track scoring stats
    scored_count = 0
    states_with_scores = set()
    
    # Load scores for all states
    print(f"Loading scores from {len(museums)} museums...")
    # Extract state codes from museum_id (e.g., "usa-co-..." -> "CO")
    state_codes = set()
    for m in museums:
        museum_id = m.get('museum_id', '')
        if museum_id and museum_id.startswith('usa-'):
            parts = museum_id.split('-')
            if len(parts) >= 2:
                state_code = parts[1].upper()
                state_codes.add(state_code)
    
    all_scores = {}
    for state_code in sorted(state_codes):
        state_scores = load_museum_scores(state_code)
        if state_scores:
            all_scores.update(state_scores)
            states_with_scores.add(state_code)
            print(f"  {state_code}: {len(state_scores)} museums scored")
    
    # Enrich museums with scoring data
    enriched_museums = []
    for museum in museums:
        museum_id = museum.get('museum_id')
        enriched = museum.copy()
        
        if museum_id in all_scores:
            scored_count += 1
            scores = all_scores[museum_id]
            
            # Add tour_planning_scores object
            enriched['tour_planning_scores'] = {
                k: v for k, v in scores.items() 
                if k not in ['summary_short', 'summary_long', 'collection_highlights', 
                            'signature_artists', 'visitor_tips', 'best_for']
            }
            
            # Add summary fields at top level for easy access
            if scores.get('summary_short'):
                enriched['summary_short'] = scores['summary_short']
            if scores.get('summary_long'):
                enriched['summary_long'] = scores['summary_long']
            if scores.get('collection_highlights'):
                enriched['collection_highlights'] = scores['collection_highlights']
            if scores.get('signature_artists'):
                enriched['signature_artists'] = scores['signature_artists']
            if scores.get('visitor_tips'):
                enriched['visitor_tips'] = scores['visitor_tips']
            if scores.get('best_for'):
                enriched['best_for'] = scores['best_for']
            
            # Mark as scored
            enriched['is_scored'] = True
            enriched['scoring_version'] = 'v2_tour_planning'
            
        enriched_museums.append(enriched)
    
    # Build enriched index
    enriched_index = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_museums': len(enriched_museums),
        'scored_museums': scored_count,
        'states_with_scores': sorted(list(states_with_scores)),
        'scoring_coverage': f"{scored_count}/{len(enriched_museums)} ({100 * scored_count / len(enriched_museums):.1f}%)",
        'museums': enriched_museums
    }
    
    # Save enriched index
    output_file = INDEX_DIR / 'all-museums-enriched.json'
    save_json(output_file, enriched_index)
    
    print(f"\n✓ Enriched index saved to: {output_file}")
    print(f"  Total museums: {len(enriched_museums)}")
    print(f"  Scored museums: {scored_count}")
    print(f"  States with scores: {', '.join(sorted(states_with_scores))}")
    print(f"  Coverage: {100 * scored_count / len(enriched_museums):.1f}%")
    
    # Also create a scores-only index for faster querying
    scores_index = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_scored': scored_count,
        'states': sorted(list(states_with_scores)),
        'scores': {
            museum_id: scores 
            for museum_id, scores in all_scores.items()
        }
    }
    
    scores_file = INDEX_DIR / 'tour-planning-scores.json'
    save_json(scores_file, scores_index)
    print(f"\n✓ Scores index saved to: {scores_file}")
    

if __name__ == '__main__':
    main()
