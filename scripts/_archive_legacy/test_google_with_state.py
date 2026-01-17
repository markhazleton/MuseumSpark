#!/usr/bin/env python3
"""
Test Google Places API with museum name + state (no city)
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path

# Set up paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

# Import from local module
import googlemaps

def _try_google_places_lookup_test(museum_name: str, city: str, state: str):
    """Test version of Google Places lookup"""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_MAPS_API_KEY not set")
        return None
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        
        # Build query as per updated logic
        if city and city != "Unknown":
            query = f"{museum_name} {city}"
        elif state:
            query = f"{museum_name} {state}"
        else:
            query = museum_name
        
        print(f"Query: '{query}'")
        
        places_result = gmaps.places(query=query)
        
        if places_result.get("results"):
            result = places_result["results"][0]
            return {
                "street_address": result.get("formatted_address"),
                "latitude": result.get("geometry", {}).get("location", {}).get("lat"),
                "longitude": result.get("geometry", {}).get("location", {}).get("lng"),
                "place_id": result.get("place_id"),
            }
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    museum_name = "108|Contemporary"
    city = None  # NULL city
    state = "OK"
    
    print(f"Testing Google Places API...")
    print(f"Museum: {museum_name}")
    print(f"City: {city}")
    print(f"State: {state}")
    print()
    
    result = _try_google_places_lookup_test(museum_name, city, state)
    
    if result:
        print("✓ Google Places returned data:")
        print(f"  Address: {result.get('street_address')}")
        print(f"  Postal: {result.get('postal_code')}")
        print(f"  Lat/Lng: {result.get('latitude')}, {result.get('longitude')}")
        print(f"  Place ID: {result.get('place_id')}")
        print(f"  Hours: {result.get('hours')}")
        print(f"  Phone: {result.get('phone')}")
    else:
        print("✗ Google Places returned None")
        print("  Check if:")
        print("  1. HAS_GOOGLE_MAPS is True")
        print("  2. GOOGLE_MAPS_API_KEY is set")
        print("  3. API key is valid")

if __name__ == "__main__":
    main()
