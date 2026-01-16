"""
Test Google Places API for 108|Contemporary to see what it returns.
"""

import os
import googlemaps

# Check if API key is set
api_key = os.getenv("GOOGLE_MAPS_API_KEY")
if not api_key:
    print("❌ GOOGLE_MAPS_API_KEY not set!")
    exit(1)

print(f"✓ API Key found: {api_key[:10]}...")

# Test search
gmaps = googlemaps.Client(key=api_key)

# Test 1: Just museum name (no city)
print("\n" + "="*80)
print("TEST 1: Search for '108|Contemporary' (no city)")
print("="*80)
query1 = "108|Contemporary"
result1 = gmaps.places(query=query1)

if result1.get("results"):
    print(f"✓ Found {len(result1['results'])} result(s)")
    for i, r in enumerate(result1["results"][:3], 1):
        print(f"\n  Result {i}:")
        print(f"    Name: {r.get('name')}")
        print(f"    Address: {r.get('formatted_address')}")
        print(f"    Place ID: {r.get('place_id')}")
        print(f"    Types: {r.get('types', [])}")
else:
    print("❌ No results found")

# Test 2: With "Tulsa Oklahoma" added
print("\n" + "="*80)
print("TEST 2: Search for '108|Contemporary Tulsa Oklahoma'")
print("="*80)
query2 = "108|Contemporary Tulsa Oklahoma"
result2 = gmaps.places(query=query2)

if result2.get("results"):
    print(f"✓ Found {len(result2['results'])} result(s)")
    for i, r in enumerate(result2["results"][:3], 1):
        print(f"\n  Result {i}:")
        print(f"    Name: {r.get('name')}")
        print(f"    Address: {r.get('formatted_address')}")
        print(f"    Place ID: {r.get('place_id')}")
        print(f"    Types: {r.get('types', [])}")
        
        # Get coordinates
        loc = r.get('geometry', {}).get('location', {})
        if loc:
            print(f"    Coords: {loc.get('lat')}, {loc.get('lng')}")
        
        # Get Place Details
        place_id = r.get('place_id')
        if place_id:
            print(f"\n    Fetching details...")
            details = gmaps.place(
                place_id=place_id,
                fields=["address_component", "formatted_address", "geometry"]
            )
            
            result_detail = details.get("result", {})
            
            # Extract postal code
            postal_code = None
            for component in result_detail.get("address_components", []):
                if "postal_code" in component.get("types", []):
                    postal_code = component.get("long_name")
                    break
            
            print(f"    Postal Code: {postal_code}")
            print(f"    Full Address: {result_detail.get('formatted_address')}")
else:
    print("❌ No results found")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("If Test 1 returns results -> Google Places CAN find it without city")
print("If Test 1 fails but Test 2 works -> NEED city to find it")
print("If both fail -> Museum not in Google Places database")
