"""Rank Colorado museums by tour-planning scores."""

import json
from pathlib import Path

def main():
    # Load all Colorado museums with scoring
    museums = []
    co_file = Path('data/states/CO.json')
    co_dir = Path('data/states/CO')
    state_json = json.loads(co_file.read_text(encoding='utf-8'))
    state_data = state_json.get('museums', [])

    for museum in state_data:
        museum_id = museum.get('museum_id')
        if not museum_id:
            continue
        
        # Find museum folder (by hash)
        museum_folders = list(co_dir.glob('m_*'))
        for folder in museum_folders:
            cache_dir = folder / 'cache'
            deep_dive_file = cache_dir / 'deep_dive_v1.json'
            if deep_dive_file.exists():
                deep_dive = json.loads(deep_dive_file.read_text(encoding='utf-8'))
                if deep_dive.get('state_file_updates', {}).get('museum_id') == museum_id:
                    scores = deep_dive.get('tour_planning_scores', {})
                    if scores:
                        museums.append({
                            'name': museum.get('museum_name', 'Unknown'),
                            'city': museum.get('city', 'Unknown'),
                            'museum_type': museum.get('museum_type', 'Unknown'),
                            'collection_quality': scores.get('collection_quality', 0),
                            'collection_depth': scores.get('collection_depth', 0),
                            'contemporary': scores.get('contemporary_score'),
                            'modern': scores.get('modern_score'),
                            'impressionist': scores.get('impressionist_score'),
                            'educational': scores.get('educational_value_score', 0),
                            'family_friendly': scores.get('family_friendly_score', 0),
                            'architecture': scores.get('architecture_score'),
                            'rationale': scores.get('scoring_rationale', '')
                        })
                    break

    # Sort by collection quality (primary), then collection depth
    museums.sort(key=lambda m: (m['collection_quality'], m['collection_depth']), reverse=True)

    print('\n' + '='*100)
    print('COLORADO MUSEUMS RANKED BY COLLECTION QUALITY')
    print('='*100)
    print()

    for i, m in enumerate(museums, 1):
        print(f"{i:2d}. {m['name']} ({m['city']})")
        print(f"    Type: {m['museum_type']}")
        print(f"    Quality: {m['collection_quality']}/10  |  Depth: {m['collection_depth']}/10  |  Educational: {m['educational']}/10  |  Family: {m['family_friendly']}/10")
        
        # Show specialty scores if present
        specialties = []
        if m['contemporary']: specialties.append(f"Contemporary: {m['contemporary']}/10")
        if m['modern']: specialties.append(f"Modern: {m['modern']}/10")
        if m['impressionist']: specialties.append(f"Impressionist: {m['impressionist']}/10")
        if m['architecture']: specialties.append(f"Architecture: {m['architecture']}/10")
        if specialties:
            print(f"    Specialties: {' | '.join(specialties)}")
        
        rationale = m['rationale']
        if len(rationale) > 150:
            print(f"    Rationale: {rationale[:150]}...")
        else:
            print(f"    Rationale: {rationale}")
        print()

    print(f'Total museums scored: {len(museums)}/19')
    print()

if __name__ == '__main__':
    main()
