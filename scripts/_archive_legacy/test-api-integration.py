#!/usr/bin/env python3
"""Quick test of Yelp and enhanced Google Places integration."""

import json
import os
import sys
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import googlemaps
    HAS_GOOGLE_MAPS = True
except ImportError:
    HAS_GOOGLE_MAPS = False
    print("⚠️ googlemaps not installed")

try:
    from yelpapi import YelpAPI
    HAS_YELP = True
except ImportError:
    HAS_YELP = False
    print("⚠️ yelpapi not installed")

print("\n" + "=" * 70)
print("🧪 API INTEGRATION TEST")
print("=" * 70)

# Test museum: 108|Contemporary (Tulsa, OK)
museum_name = "108 Contemporary"
city = "Tulsa"
state_code = "OK"

print(f"\n📍 Testing: {museum_name}, {city}, {state_code}")

# Check API keys
print("\n🔑 API Key Status:")
print(f"  Google Maps API: {'✅ SET' if os.getenv('GOOGLE_MAPS_API_KEY') else '❌ NOT SET'}")
print(f"  Yelp Fusion API: {'✅ SET' if os.getenv('YELP_API_KEY') else '❌ NOT SET'}")

# Test Google Places API
print("\n" + "-" * 70)
print("🗺️  TESTING GOOGLE PLACES API (detailed=True)")
print("-" * 70)

if HAS_GOOGLE_MAPS and os.getenv("GOOGLE_MAPS_API_KEY"):
    try:
        gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
        
        # Basic search
        query = f"{museum_name} {city}"
        places_result = gmaps.places(query=query)
        
        if places_result.get("results"):
            result = places_result["results"][0]
            place_id = result.get("place_id")
            
            print(f"✅ Found on Google Places:")
            print(f"   Name: {result.get('name')}")
            print(f"   Address: {result.get('formatted_address')}")
            print(f"   Place ID: {place_id}")
            
            # Get detailed info
            if place_id:
                details = gmaps.place(
                    place_id=place_id,
                    fields=["opening_hours", "formatted_phone_number", "website", "photo", "rating", "user_ratings_total"]
                )
                
                if details.get("result"):
                    detail_result = details["result"]
                    
                    print(f"\n📊 Detailed Information:")
                    
                    # Hours
                    hours_data = detail_result.get("opening_hours", {})
                    if hours_data.get("weekday_text"):
                        print(f"   Hours:")
                        for line in hours_data["weekday_text"]:
                            print(f"     {line}")
                    else:
                        print(f"   Hours: Not available")
                    
                    # Phone
                    phone = detail_result.get("formatted_phone_number")
                    print(f"   Phone: {phone if phone else 'Not available'}")
                    
                    # Website
                    website = detail_result.get("website")
                    print(f"   Website: {website if website else 'Not available'}")
                    
                    # Photos
                    photos = detail_result.get("photo", [])
                    print(f"   Photos: {len(photos)} available")
                    
                    # Rating
                    rating = detail_result.get("rating")
                    review_count = detail_result.get("user_ratings_total", 0)
                    if rating:
                        print(f"   Rating: {rating}/5 ({review_count} reviews)")
                    else:
                        print(f"   Rating: Not available")
        else:
            print("❌ No results found on Google Places")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
else:
    print("⏭️  Skipped (no API key or library not installed)")

# Test Yelp API
print("\n" + "-" * 70)
print("⭐ TESTING YELP FUSION API")
print("-" * 70)

if HAS_YELP and os.getenv("YELP_API_KEY"):
    try:
        yelp = YelpAPI(os.getenv("YELP_API_KEY"))
        
        # Search for business
        response = yelp.search_query(
            term=museum_name,
            location=f"{city}, {state_code}",
            categories="museums",
            limit=1
        )
        
        if response.get("businesses"):
            business = response["businesses"][0]
            
            print(f"✅ Found on Yelp:")
            print(f"   Name: {business.get('name')}")
            
            # Address
            location = business.get("location", {})
            address = location.get("address1")
            city_yelp = location.get("city")
            zip_code = location.get("zip_code")
            print(f"   Address: {address}, {city_yelp}, {state_code} {zip_code}")
            
            # Coordinates
            coords = business.get("coordinates", {})
            print(f"   Coordinates: {coords.get('latitude')}, {coords.get('longitude')}")
            
            # Phone
            phone = business.get("phone", "")
            if phone.startswith("+1"):
                phone = phone[2:]
            print(f"   Phone: {phone if phone else 'Not available'}")
            
            # Rating
            rating = business.get("rating")
            review_count = business.get("review_count", 0)
            print(f"   Rating: {rating}/5 ({review_count} reviews)")
            
            # Photos
            photos = business.get("photos", [])
            print(f"   Photos: {len(photos)} available")
            
            # Try to get hours
            yelp_id = business.get("id")
            if yelp_id:
                try:
                    details = yelp.business_query(id=yelp_id)
                    hours_data = details.get("hours", [])
                    
                    if hours_data:
                        print(f"\n   Hours:")
                        for hour_block in hours_data:
                            if hour_block.get("open"):
                                for day_info in hour_block["open"]:
                                    day = day_info.get("day", 0)
                                    start = day_info.get("start", "")
                                    end = day_info.get("end", "")
                                    
                                    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                                    if 0 <= day < 7 and start and end:
                                        start_hr = int(start[:2])
                                        start_min = start[2:]
                                        end_hr = int(end[:2])
                                        end_min = end[2:]
                                        
                                        start_ampm = "AM" if start_hr < 12 else "PM"
                                        end_ampm = "AM" if end_hr < 12 else "PM"
                                        
                                        start_hr = start_hr if start_hr <= 12 else start_hr - 12
                                        start_hr = 12 if start_hr == 0 else start_hr
                                        end_hr = end_hr if end_hr <= 12 else end_hr - 12
                                        end_hr = 12 if end_hr == 0 else end_hr
                                        
                                        print(f"     {day_names[day]}: {start_hr}:{start_min} {start_ampm} - {end_hr}:{end_min} {end_ampm}")
                    else:
                        print(f"   Hours: Not available")
                except Exception:
                    print(f"   Hours: Error fetching details")
        else:
            print("❌ No results found on Yelp")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
else:
    print("⏭️  Skipped (no API key or library not installed)")

print("\n" + "=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)

if not os.getenv("YELP_API_KEY"):
    print("\n💡 TIP: Get a free Yelp API key at https://www.yelp.com/developers/v3/manage_app")
    print("   Then set: $env:YELP_API_KEY = 'YOUR_KEY_HERE'")
