import os
import googlemaps

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
query = "Muskogee War Memorial Park Home of the USS Batfish Muskogee"
result = gmaps.places(query=query)

if result.get("results"):
    first = result["results"][0]
    place_id = first.get("place_id")
    print("Place ID:", place_id)
    print("Formatted address:", first.get("formatted_address"))
    
    # Get detailed info for postal code
    details = gmaps.place(place_id=place_id, fields=["address_component"])
    print("\nAddress components from Place Details:")
    for comp in details["result"].get("address_components", []):
        print(f"  {comp['long_name']:30} types: {comp['types']}")
        if "postal_code" in comp.get("types", []):
            print(f"    ^^^ POSTAL CODE FOUND: {comp['long_name']}")
