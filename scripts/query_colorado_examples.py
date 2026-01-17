"""Query Colorado museums by tour-planning scores."""

import json
from pathlib import Path

def load_colorado_scores():
    """Load all Colorado museums with their tour planning scores."""
    museums = []
    co_file = Path('data/states/CO.json')
    co_dir = Path('data/states/CO')
    state_json = json.loads(co_file.read_text(encoding='utf-8'))
    state_data = state_json.get('museums', [])

    for museum in state_data:
        museum_id = museum.get('museum_id')
        if not museum_id:
            continue
        
        # Find museum folder
        for folder in co_dir.glob('m_*'):
            deep_dive_file = folder / 'cache' / 'deep_dive_v1.json'
            if deep_dive_file.exists():
                deep_dive = json.loads(deep_dive_file.read_text(encoding='utf-8'))
                if deep_dive.get('state_file_updates', {}).get('museum_id') == museum_id:
                    scores = deep_dive.get('tour_planning_scores', {})
                    if scores:
                        museums.append({
                            'museum_id': museum_id,
                            'name': museum.get('museum_name', 'Unknown'),
                            'city': museum.get('city', 'Unknown'),
                            'museum_type': museum.get('museum_type', 'Unknown'),
                            'website': museum.get('website'),
                            'scores': scores
                        })
                    break
    
    return museums

def main():
    museums = load_colorado_scores()
    
    print('\n' + '='*100)
    print('QUERY EXAMPLES: Tour Planning with Scoring Filters')
    print('='*100)
    
    # Query 1: Best Contemporary Art Museums
    print('\n🎨 QUERY 1: Best Contemporary Art Museums (contemporary_score >= 8)')
    print('-'*100)
    contemporary = [m for m in museums if (m['scores'].get('contemporary_score') or 0) >= 8]
    contemporary.sort(key=lambda m: m['scores'].get('contemporary_score') or 0, reverse=True)
    for m in contemporary:
        score = m['scores'].get('contemporary_score')
        quality = m['scores'].get('collection_quality')
        print(f"  • {m['name']} ({m['city']}) - Contemporary: {score}/10, Quality: {quality}/10")
        print(f"    {m['website']}")
    
    # Query 2: Family-Friendly Museums
    print('\n👨‍👩‍👧‍👦 QUERY 2: Family-Friendly Museums (family_friendly >= 8)')
    print('-'*100)
    family = [m for m in museums if (m['scores'].get('family_friendly_score') or 0) >= 8]
    family.sort(key=lambda m: m['scores'].get('family_friendly_score') or 0, reverse=True)
    for m in family:
        score = m['scores'].get('family_friendly_score')
        edu = m['scores'].get('educational_value_score')
        print(f"  • {m['name']} ({m['city']}) - Family: {score}/10, Educational: {edu}/10")
    
    # Query 3: World-Class Collections
    print('\n⭐ QUERY 3: World-Class Collections (collection_quality >= 8)')
    print('-'*100)
    world_class = [m for m in museums if (m['scores'].get('collection_quality') or 0) >= 8]
    world_class.sort(key=lambda m: m['scores'].get('collection_quality') or 0, reverse=True)
    for m in world_class:
        quality = m['scores'].get('collection_quality')
        depth = m['scores'].get('collection_depth')
        print(f"  • {m['name']} ({m['city']}) - Quality: {quality}/10, Depth: {depth}/10")
    
    # Query 4: Architectural Highlights
    print('\n🏛️ QUERY 4: Architectural Highlights (architecture_score >= 7)')
    print('-'*100)
    architecture = [m for m in museums if (m['scores'].get('architecture_score') or 0) >= 7]
    architecture.sort(key=lambda m: m['scores'].get('architecture_score') or 0, reverse=True)
    for m in architecture:
        arch = m['scores'].get('architecture_score')
        print(f"  • {m['name']} ({m['city']}) - Architecture: {arch}/10")
    
    # Query 5: Impressionist Art
    print('\n🌅 QUERY 5: Impressionist Collections (impressionist_score >= 5)')
    print('-'*100)
    impressionist = [m for m in museums if (m['scores'].get('impressionist_score') or 0) >= 5]
    if impressionist:
        impressionist.sort(key=lambda m: m['scores'].get('impressionist_score') or 0, reverse=True)
        for m in impressionist:
            score = m['scores'].get('impressionist_score')
            print(f"  • {m['name']} ({m['city']}) - Impressionist: {score}/10")
    else:
        print("  (No museums in Colorado with significant Impressionist collections)")
    
    # Query 6: Educational Value Leaders
    print('\n📚 QUERY 6: Educational Leaders (educational_value >= 8)')
    print('-'*100)
    educational = [m for m in museums if (m['scores'].get('educational_value_score') or 0) >= 8]
    educational.sort(key=lambda m: m['scores'].get('educational_value_score') or 0, reverse=True)
    for m in educational:
        edu = m['scores'].get('educational_value_score')
        museum_type = m['museum_type'] or 'Unknown Type'
        print(f"  • {m['name']} ({m['city']}) - Educational: {edu}/10 | {museum_type}")
    
    print('\n' + '='*100)
    print(f'Total museums available for querying: {len(museums)}')
    print('='*100)
    print()

if __name__ == '__main__':
    main()
