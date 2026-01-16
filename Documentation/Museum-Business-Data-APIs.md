# Python Libraries & APIs for Museum/Business Location Data

## The Problem
Looking at 108|Contemporary in OK.json, we have **28 null fields** out of ~60 total fields. Why?
```
"row_notes_internal": "Official site: blocked by robots.txt"
```

**The website is blocking automated scraping!** This is why we need alternative data sources.

---

## Solution: Multi-Source Data Enrichment

### 🌟 Tier 1: Free/Open APIs (No API Key Needed)

#### 1. **Wikidata** (We're using but could enhance)
```bash
# Already available via HTTP API
```
**What it provides**:
- Coordinates, founding date, notable collections
- Wikipedia link (for more extraction)
- VERY sparse for small museums

**Python Library**: `requests` + SPARQL queries
```python
import requests
endpoint = "https://query.wikidata.org/sparql"
query = """
SELECT ?museum ?museumLabel ?coord ?website ?founded
WHERE {
  ?museum wdt:P31 wd:Q33506 .  # Instance of museum
  ?museum rdfs:label "108 Contemporary"@en .
  OPTIONAL { ?museum wdt:P625 ?coord }
  OPTIONAL { ?museum wdt:P856 ?website }
  OPTIONAL { ?museum wdt:P571 ?founded }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""
```

#### 2. **OpenStreetMap Overpass API**
```bash
pip install overpy  # Overpass API wrapper
```
**What it provides**:
- Coordinates, address, hours, phone
- User-contributed data (quality varies)
- **FREE** and no API key

**Example**:
```python
import overpy
api = overpy.Overpass()
result = api.query("""
[out:json];
node["tourism"="museum"]["name"="108 Contemporary"](around:1000,36.15,-95.99);
out body;
""")
for node in result.nodes:
    print(f"Address: {node.tags.get('addr:street')}")
    print(f"Hours: {node.tags.get('opening_hours')}")
    print(f"Phone: {node.tags.get('phone')}")
```

#### 3. **IMLS (Institute of Museum and Library Services)**
```bash
# US Government museum database
pip install requests
```
**What it provides**:
- Official museum registry data
- Income, attendance figures
- Educational programs
- **FREE** government data

**API**: https://data.imls.gov/
```python
import requests
response = requests.get(
    "https://data.imls.gov/api/v1/museums/search",
    params={"name": "108 Contemporary", "state": "OK"}
)
```

---

### 💰 Tier 2: Commercial APIs (Require API Key, Often Have Free Tier)

#### 4. **Yelp Fusion API** ⭐ HIGHLY RECOMMENDED
```bash
pip install yelpapi
```
**What it provides**:
- ⭐ Hours of operation
- ⭐ Phone number, address
- ⭐ Photos (50+)
- ⭐ Reviews & ratings
- ⭐ Price level
- **FREE**: 5,000 API calls/day

**Example**:
```python
from yelpapi import YelpAPI
yelp = YelpAPI(api_key='YOUR_KEY')
response = yelp.search_query(
    term='108 Contemporary',
    location='Tulsa, OK',
    categories='museums'
)
business = response['businesses'][0]
print(f"Rating: {business['rating']}")
print(f"Hours: {business.get('hours')}")
print(f"Phone: {business['phone']}")
```

**Pricing**: FREE tier (5K calls/day), then $0.30 per 1000 calls

#### 5. **Foursquare Places API**
```bash
pip install foursquare
```
**What it provides**:
- Location details, hours
- Photos, tips from visitors
- Categories/tags
- **FREE**: 100K calls/month

**Example**:
```python
import foursquare
client = foursquare.Foursquare(client_id='YOUR_ID', client_secret='YOUR_SECRET')
venues = client.venues.search(params={
    'near': 'Tulsa, OK',
    'query': '108 Contemporary',
    'categoryId': '4bf58dd8d48988d181941735'  # Museum category
})
```

**Pricing**: FREE (100K calls/month), Premium $100/month

#### 6. **Google Places API** (We're already using!)
```bash
pip install googlemaps  # ✅ Already installed
```
**What it provides**:
- ⭐ Most reliable address data
- ⭐ Hours of operation
- ⭐ Phone, website
- ⭐ Photos
- ⭐ Reviews & ratings
- **FREE**: $200 credit/month (~28K requests)

**We should expand our usage**:
```python
import googlemaps
gmaps = googlemaps.Client(key='YOUR_KEY')
place = gmaps.places('108 Contemporary, Tulsa OK')
place_id = place['results'][0]['place_id']

# Get detailed info
details = gmaps.place(place_id, fields=[
    'opening_hours', 'formatted_phone_number', 
    'website', 'photos', 'rating', 'reviews'
])
```

**Pricing**: $200 free/month, then ~$17 per 1000 requests

#### 7. **TripAdvisor Content API**
```bash
pip install requests
```
**What it provides**:
- Reviews, ratings
- Photos
- Hours, contact info
- **Cost**: Requires partnership/paid plan

#### 8. **Facebook Graph API**
```bash
pip install facebook-sdk
```
**What it provides**:
- Business hours
- Events
- Photos
- Contact info
- **FREE** with API key

**Many museums have Facebook pages!**

---

### 📊 Tier 3: Web Scraping Alternatives (When robots.txt blocks us)

#### 9. **SerpApi** (Google Search Results API)
```bash
pip install google-search-results
```
**What it provides**:
- Extracts data from Google Search Knowledge Panel
- Bypasses individual site robots.txt
- Gets hours, ratings, photos from Google's aggregation
- **Cost**: $50/month for 5,000 searches

```python
from serpapi import GoogleSearch
params = {
    "q": "108 Contemporary Tulsa",
    "location": "Tulsa, Oklahoma",
    "api_key": "YOUR_KEY"
}
search = GoogleSearch(params)
results = search.get_dict()
knowledge_graph = results.get('knowledge_graph', {})
```

#### 10. **ScrapingBee / Bright Data**
```bash
pip install scrapingbee
```
**What it provides**:
- Bypasses robots.txt and anti-bot protection
- JavaScript rendering
- Rotating IP addresses
- **Cost**: $49/month for 100K API credits

---

## 🎯 Recommended Implementation Strategy

### Phase 1: Add Free APIs (No Cost)
1. **OpenStreetMap Overpass** - Install `overpy`
   - Check OSM for each museum
   - Fallback after Google Places fails
   
2. **IMLS Database** - Simple HTTP requests
   - One-time bulk download
   - Match by name/location
   
3. **Enhanced Wikidata** - Already have infrastructure
   - More comprehensive SPARQL queries
   - Extract hours from Wikipedia pages

### Phase 2: Add One Commercial API (Budget-Friendly)
**Choose YELP Fusion API** (Best value)
- ✅ 5,000 FREE calls/day (enough for all museums)
- ✅ Excellent coverage for museums/attractions
- ✅ Hours, phone, photos, ratings included
- ✅ Simple Python library (`yelpapi`)

### Phase 3: Expand Google Places Usage
We already have the key - let's use it more:
- Get **opening_hours** data
- Get **formatted_phone_number**
- Get **photos** array
- Get **reviews** for validation

---

## 💡 Solution for 108|Contemporary Specifically

**The Problem**: `"Official site: blocked by robots.txt"`

**Multi-Source Approach**:
```python
# Try in order:
1. Google Places API → Get hours, phone, address ✅
2. Yelp API → Get photos, reviews, verify hours
3. OpenStreetMap → Get OSM community data
4. Facebook Graph API → Get events, posts
5. IMLS Database → Get official government data
6. Manual fallback → LLM enrichment with public search results
```

---

## 📈 Expected Improvement

**Current 108|Contemporary**: 28 null fields (47% empty)
**After adding Yelp + expanding Google Places**: ~10 null fields (17% empty)

**Fields we could fill**:
- ✅ street_address (from Google/Yelp)
- ✅ postal_code (from Google/Yelp)
- ✅ latitude/longitude (from Google/Yelp/OSM)
- ✅ open_hour_notes (from Google/Yelp)
- ✅ museum_type (from Yelp categories)
- ✅ status (active if on Yelp)
- ✅ notes (from Yelp description)
- ✅ photos (from Google/Yelp)
- ✅ reputation (from ratings)

---

## 🚀 Quick Win: Immediate Next Steps

1. **Sign up for Yelp Fusion API** (5 min, FREE)
   - https://www.yelp.com/developers/v3/manage_app
   
2. **Install yelpapi**:
   ```bash
   pip install yelpapi
   ```

3. **Add to enrich-open-data.py**:
   ```python
   # Priority 0: Yelp Fusion API (best for business data)
   if HAS_YELP:
       yelp_data = _try_yelp_lookup(museum_name, city, state)
       if yelp_data:
           # Fill hours, phone, photos, etc.
   ```

4. **Expand Google Places to get hours**:
   ```python
   details = gmaps.place(place_id, fields=['opening_hours'])
   ```

Would you like me to:
1. **Implement Yelp API integration** (free, high value)?
2. **Add OpenStreetMap Overpass queries** (free, good fallback)?
3. **Expand Google Places to extract hours/photos**?
