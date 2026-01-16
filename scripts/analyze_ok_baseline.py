"""
Analyze Oklahoma museums data to establish baseline for validation testing.
Creates a detailed snapshot of the current state of OK.json.
"""

import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
OK_JSON = PROJECT_ROOT / "data" / "states" / "OK.json"

def analyze_ok_state():
    with open(OK_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    museums = data.get("museums", [])
    
    print("=" * 80)
    print("OKLAHOMA BASELINE ANALYSIS")
    print("=" * 80)
    print(f"State: {data.get('state')}")
    print(f"State Code: {data.get('state_code')}")
    print(f"Last Updated: {data.get('last_updated')}")
    print(f"Total Museums: {len(museums)}")
    print()
    
    # Field coverage analysis
    fields_to_check = [
        "street_address", "postal_code", "city", "latitude", "longitude",
        "phone", "museum_type", "status", "primary_domain",
        "open_hours_url", "tickets_url", "notes"
    ]
    
    print("=" * 80)
    print("FIELD COVERAGE (non-null, non-empty values)")
    print("=" * 80)
    
    field_stats = {}
    for field in fields_to_check:
        count = 0
        for museum in museums:
            value = museum.get(field)
            if value is not None and value != "":
                count += 1
        pct = (count / len(museums) * 100) if museums else 0
        field_stats[field] = count
        print(f"{field:25} {count:2}/{len(museums):2} ({pct:5.1f}%)")
    
    print()
    
    # Data sources analysis
    print("=" * 80)
    print("DATA SOURCES")
    print("=" * 80)
    
    all_sources = []
    for museum in museums:
        sources = museum.get("data_sources", [])
        if isinstance(sources, list):
            all_sources.extend(sources)
        elif sources:
            all_sources.append(sources)
    
    source_counts = Counter(all_sources)
    for source, count in source_counts.most_common():
        print(f"{source:35} {count:2} museums")
    
    print()
    
    # Museums with critical data (address + coords)
    print("=" * 80)
    print("CRITICAL DATA COMPLETENESS")
    print("=" * 80)
    
    complete = 0
    partial = 0
    minimal = 0
    
    for museum in museums:
        has_address = museum.get("street_address") is not None
        has_postal = museum.get("postal_code") is not None
        has_coords = museum.get("latitude") is not None and museum.get("longitude") is not None
        
        score = sum([has_address, has_postal, has_coords])
        if score == 3:
            complete += 1
        elif score > 0:
            partial += 1
        else:
            minimal += 1
    
    print(f"Complete (address + postal + coords): {complete:2}/{len(museums):2} ({complete/len(museums)*100:5.1f}%)")
    print(f"Partial (some data):                   {partial:2}/{len(museums):2} ({partial/len(museums)*100:5.1f}%)")
    print(f"Minimal (no critical data):            {minimal:2}/{len(museums):2} ({minimal/len(museums)*100:5.1f}%)")
    
    print()
    
    # Museum-by-museum summary
    print("=" * 80)
    print("MUSEUM-BY-MUSEUM SUMMARY")
    print("=" * 80)
    
    for i, museum in enumerate(museums, 1):
        museum_id = museum.get("museum_id", "unknown")
        name = museum.get("museum_name", "Unknown")
        
        # Check critical fields
        address = museum.get("street_address")
        postal = museum.get("postal_code")
        city = museum.get("city")
        lat = museum.get("latitude")
        lng = museum.get("longitude")
        phone = museum.get("phone")
        museum_type = museum.get("museum_type")
        
        print(f"\n{i:2}. {name}")
        print(f"    ID: {museum_id}")
        print(f"    City: {city or 'NULL'}")
        print(f"    Address: {address or 'NULL'}")
        print(f"    Postal: {postal or 'NULL'}")
        print(f"    Coords: {'YES' if lat and lng else 'NULL'} ({lat}, {lng})")
        print(f"    Phone: {phone or 'NULL'}")
        print(f"    Type: {museum_type or 'NULL'}")
        
        sources = museum.get("data_sources", [])
        if isinstance(sources, list):
            print(f"    Sources: {', '.join(sources[:3])}")
        else:
            print(f"    Sources: {sources}")
    
    print()
    print("=" * 80)
    print("END OF BASELINE ANALYSIS")
    print("=" * 80)
    
    return field_stats

if __name__ == "__main__":
    analyze_ok_state()
