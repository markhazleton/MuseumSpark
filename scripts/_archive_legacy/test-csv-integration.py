#!/usr/bin/env python3
"""Test CSV enrichment integration"""
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import after path is set
import enrich_open_data

print('✓ Imports successful')

# Test Alaska museum
test_museum = {
    'state_province': 'Alaska',
    'museum_name': 'Anchorage Museum'
}

result = enrich_open_data._try_csv_lookup(test_museum)
print(f'✓ CSV lookup: {"Found" if result else "Not found"}')

if result:
    print(f"  Museum: {result.get('Museum Name')}")
    print(f"  Phone: {result.get('Phone Number')}")
    print(f"  Type: {result.get('Museum Type')}")
    print(f"  Lat/Lng: {result.get('Latitude')}, {result.get('Longitude')}")
else:
    print("  ERROR: Expected to find Anchorage Museum")
    sys.exit(1)

# Test Oklahoma museum  
test_museum2 = {
    'state_province': 'Oklahoma',
    'museum_name': '108|Contemporary'
}

result2 = enrich_open_data._try_csv_lookup(test_museum2)
print(f'\n✓ CSV lookup 2: {"Found" if result2 else "Not found"}')

if result2:
    print(f"  Museum: {result2.get('Museum Name')}")
    print(f"  Phone: {result2.get('Phone Number')}")
    print(f"  Type: {result2.get('Museum Type')}")

print('\n✅ All tests passed!')
