# Google Places API - Missing Data Analysis

**Date**: January 17, 2026  
**Reviewed by**: AI Assistant  
**Current Implementation**: `scripts/phases/phase0_identity.py`

## Implementation Status

**✅ IMPLEMENTED** - January 17, 2026

### Final Configuration (Modified Tier 1 + Tier 2)

**Fields Implemented (10 total):**
```python
fields=[
    # Core identity fields (original)
    "address_component",
    "formatted_address",
    "geometry",
    # Enhanced fields (implemented)
    "formatted_phone_number",  # ✅ Phone in local format
    "website",                  # ✅ Official website
    "business_status",          # ✅ OPERATIONAL/CLOSED
    "opening_hours",            # ✅ Structured hours + open_now
    "rating",                   # ✅ Google rating (1-5)
    "user_ratings_total",       # ✅ Number of reviews
    "reviews",                  # ✅ Up to 5 most helpful reviews
]
```

**Fields Skipped (per user request):**
- ❌ `international_phone_number` - US-focused app
- ❌ `types` - Using IRS CSV classification
- ❌ `price_level` - Not needed currently
- ❌ `utc_offset_minutes` - No timezone features yet
- ❌ `url` - Can construct from place_id
- ❌ `wheelchair_accessible_entrance` - Low coverage
- ❌ All low-value fields (icon, vicinity, adr_address)

### Actual Cost
- **Previous**: 3 fields × $0.017 = **$0.051 per museum**
- **Implemented**: 10 fields × $0.017 = **$0.170 per museum**
- **Increase**: +$0.119 per museum (+233%)
- **For 1,000 museums**: +$119

See [Phase0-Enhancement-Implementation-Summary.md](Phase0-Enhancement-Implementation-Summary.md) for full implementation details.

---

## Original Analysis Below

## Executive Summary

We are currently requesting only **3 fields** from Google Places API, but there are **20+ additional fields** available that could significantly enhance our museum data quality and reduce dependence on other APIs or web scraping.

### Critical Finding

**Current API Request (Line 290-292):**
```python
details = gmaps.place(
    place_id=place_id,
    fields=["address_component", "formatted_address", "geometry"]
)
```

**Cost Impact**: Google Places charges $0.017 per field requested in Place Details calls. We're currently using 3 fields. Adding more fields increases cost but may provide better value than alternative data sources.

## Missing High-Value Fields

### 🔥 Critical Missing Fields (Should Add Immediately)

#### 1. **`formatted_phone_number`** 
- **What it provides**: Local format phone number (e.g., "(123) 456-7890")
- **Current gap**: We get phones from IRS 990 CSV (69% coverage) but missing 31%
- **Benefit**: Google Places has phone for most businesses
- **Use case**: Contact info for visitors, data completeness
- **Cost**: +$0.017 per lookup
- **Recommendation**: ✅ **ADD THIS**

#### 2. **`international_phone_number`**
- **What it provides**: International format (e.g., "+1 123-456-7890")
- **Current gap**: No international format stored
- **Benefit**: Better for international visitors
- **Use case**: Phone validation, international compatibility
- **Cost**: +$0.017 per lookup
- **Recommendation**: ✅ **ADD THIS**

#### 3. **`website`**
- **What it provides**: Official website URL from Google's verified data
- **Current gap**: We have websites from Walker roster + Wikidata, but some museums missing
- **Benefit**: Google's data is often more up-to-date than Wikidata
- **Use case**: Validation against existing website, filling gaps
- **Cost**: +$0.017 per lookup
- **Recommendation**: ✅ **ADD THIS** (as verification/fallback)

#### 4. **`business_status`**
- **What it provides**: `OPERATIONAL`, `CLOSED_TEMPORARILY`, `CLOSED_PERMANENTLY`
- **Current gap**: We don't track if museums are permanently closed
- **Benefit**: Prevents recommending closed museums
- **Use case**: Data quality, filtering out closed venues
- **Cost**: +$0.017 per lookup
- **Recommendation**: ✅ **ADD THIS** (critical for data quality)

#### 5. **`opening_hours`**
- **What it provides**: Structured open hours (days/times) + `open_now` boolean
- **Current gap**: We scrape from websites (Phase 0.7) with mixed success
- **Benefit**: Structured data vs unstructured HTML scraping
- **Use case**: "Open now" filters, hours display, trip planning
- **Cost**: +$0.017 per lookup
- **Recommendation**: ✅ **ADD THIS** (more reliable than web scraping)

### ⭐ High-Value Missing Fields (Consider Adding)

#### 6. **`rating`**
- **What it provides**: Google average rating (1.0-5.0)
- **Current gap**: No visitor rating data
- **Benefit**: Proxy for popularity/quality
- **Use case**: Priority scoring, recommendation algorithms
- **Cost**: +$0.017 per lookup
- **Recommendation**: ⭐ **CONSIDER** (useful for reputation scoring)

#### 7. **`user_ratings_total`**
- **What it provides**: Number of reviews/ratings
- **Current gap**: No review count data
- **Benefit**: Volume indicates popularity/prominence
- **Use case**: Reputation scoring, filtering (e.g., "has 100+ reviews")
- **Cost**: +$0.017 per lookup
- **Recommendation**: ⭐ **CONSIDER** (pairs well with rating)

#### 8. **`types`**
- **What it provides**: Google's business type classifications (e.g., `["museum", "tourist_attraction", "point_of_interest"]`)
- **Current gap**: We infer museum_type from IRS CSV + manual classification
- **Benefit**: Validation of museum classification
- **Use case**: Type validation, detecting non-museum venues
- **Cost**: +$0.017 per lookup
- **Recommendation**: ⭐ **CONSIDER** (useful for data quality)

#### 9. **`price_level`**
- **What it provides**: Price range (0-4): 0=Free, 1=$, 2=$$, 3=$$$, 4=$$$$
- **Current gap**: No price range data
- **Benefit**: Trip planning (budget considerations)
- **Use case**: Filtering by price, budget trip planning
- **Cost**: +$0.017 per lookup
- **Recommendation**: ⭐ **CONSIDER** (nice-to-have for trip planning)

#### 10. **`utc_offset_minutes`**
- **What it provides**: UTC offset for time zone
- **Current gap**: No time zone data stored
- **Benefit**: Correct time calculations for "open now"
- **Use case**: Cross-timezone trip planning
- **Cost**: +$0.017 per lookup
- **Recommendation**: ⭐ **CONSIDER** (if implementing "open now" features)

### 💡 Nice-to-Have Missing Fields

#### 11. **`photos`**
- **What it provides**: Array of photo references (Google street view, user photos)
- **Current gap**: No photos stored
- **Benefit**: Visual content for UI
- **Use case**: Museum cards, gallery views
- **Cost**: +$0.017 per lookup (+ additional cost to fetch actual photos)
- **Recommendation**: 💡 **FUTURE** (requires photo hosting infrastructure)

#### 12. **`reviews`**
- **What it provides**: Up to 5 most helpful reviews (text + rating)
- **Current gap**: No review text
- **Benefit**: Sentiment analysis, visitor insights
- **Use case**: Quality assessment, visitor expectations
- **Cost**: +$0.017 per lookup
- **Recommendation**: 💡 **FUTURE** (interesting for analysis but not essential)

#### 13. **`url`**
- **What it provides**: Google Maps URL for this place
- **Current gap**: No Maps link stored
- **Benefit**: Direct link to Google Maps
- **Use case**: Navigation, "View on Google Maps" links
- **Cost**: +$0.017 per lookup
- **Recommendation**: 💡 **FUTURE** (can construct from place_id)

#### 14. **`wheelchair_accessible_entrance`**
- **What it provides**: Boolean for accessibility
- **Current gap**: We scrape accessibility pages (Phase 0.7)
- **Benefit**: Structured accessibility data
- **Use case**: Accessibility filters
- **Cost**: +$0.017 per lookup
- **Recommendation**: 💡 **CONSIDER** (accessibility is important)

### ❌ Low-Value Fields (Skip)

#### 15. **`icon` / `icon_mask_base_uri` / `icon_background_color`**
- **What it provides**: Google's default icon styling
- **Benefit**: Minimal (we'd use custom museum icons)
- **Recommendation**: ❌ **SKIP**

#### 16. **`vicinity`**
- **What it provides**: Simplified address (e.g., "123 Main St, Aspen")
- **Benefit**: Redundant with formatted_address
- **Recommendation**: ❌ **SKIP**

#### 17. **`adr_address`**
- **What it provides**: Address in microformat markup
- **Benefit**: Redundant with address_components
- **Recommendation**: ❌ **SKIP**

## Cost-Benefit Analysis

### Current Cost Per Museum
- **Fields requested**: 3 (address_component, formatted_address, geometry)
- **Cost per Place Details call**: 3 × $0.017 = **$0.051 per museum**

### Proposed Tier 1 (Essential)
- **Add**: formatted_phone_number, international_phone_number, website, business_status, opening_hours
- **Total fields**: 8
- **Cost per Place Details call**: 8 × $0.017 = **$0.136 per museum**
- **Increase**: +$0.085 per museum (+166%)

### Proposed Tier 2 (Recommended)
- **Add Tier 1** + rating, user_ratings_total, types, price_level
- **Total fields**: 12
- **Cost per Place Details call**: 12 × $0.017 = **$0.204 per museum**
- **Increase**: +$0.153 per museum (+300%)

### Value Proposition

For **1,000 museums**:
- **Current cost**: $51
- **Tier 1 cost**: $136 (+$85)
- **Tier 2 cost**: $204 (+$153)

**What you get for +$85 (Tier 1)**:
- ✅ Phone numbers (eliminates need for IRS CSV fallback for 31% of museums)
- ✅ Verified websites (eliminates some Wikidata lookups)
- ✅ Business status (prevents recommending closed museums - **critical**)
- ✅ Structured opening hours (eliminates unreliable web scraping for hours)

**What you get for +$153 (Tier 2)**:
- Everything in Tier 1, PLUS:
- ⭐ Ratings + review counts (reputation scoring without LLM)
- ⭐ Type validation (data quality)
- ⭐ Price level (trip planning enhancement)

## Data Completeness Comparison

| Field | Current Source | Coverage | Google Places Coverage (est.) | Winner |
|-------|---------------|----------|-------------------------------|--------|
| **Phone** | IRS 990 CSV | 69% | ~95% | 🏆 Google |
| **Website** | Walker + Wikidata | ~80% | ~90% | 🏆 Google |
| **Hours** | Web scraping | ~50-60% | ~80% | 🏆 Google |
| **Business Status** | None | 0% | ~99% | 🏆 Google |
| **Rating** | None | 0% | ~70% | 🏆 Google |
| **Accessibility** | Web scraping | ~30% | ~40% | Google (slight edge) |

## Recommendations

### Immediate Action (High Priority)
1. **Add Tier 1 fields** to `phase0_identity.py`:
   ```python
   fields=[
       "address_component", 
       "formatted_address", 
       "geometry",
       "formatted_phone_number",        # NEW
       "international_phone_number",    # NEW
       "website",                        # NEW
       "business_status",                # NEW
       "opening_hours",                  # NEW
   ]
   ```

2. **Update `IdentityResult` dataclass** to capture new fields

3. **Update museum JSON schema** to store:
   - `phone_google` (formatted_phone_number)
   - `phone_international` (international_phone_number)
   - `website_google` (for validation)
   - `business_status`
   - `opening_hours_structured` (Google's structured data)
   - `open_now` (boolean from opening_hours)

4. **Add validation logic** in phase1_backbone.py:
   - If `business_status == "CLOSED_PERMANENTLY"` → flag museum
   - If Google website differs from stored website → note for review

### Short-Term Action (Nice to Have)
5. **Add Tier 2 fields** for enhanced features:
   - `rating` + `user_ratings_total` for reputation scoring
   - `types` for classification validation
   - `price_level` for budget filtering

6. **Integrate into downstream phases**:
   - Phase 1: Use `business_status` for data quality
   - Phase 2: Use `rating` + `user_ratings_total` in LLM reputation scoring
   - Phase 3: Use `opening_hours` + `price_level` in priority scoring

### Long-Term Considerations
7. **Photos** - Only if building visual UI (requires photo hosting)
8. **Reviews** - For sentiment analysis or visitor insights
9. **Wheelchair accessibility** - If focusing on accessibility features

## Implementation Notes

### API Quota Impact
- **Current quota usage**: ~50 museums/day = $2.55/day
- **With Tier 1**: ~50 museums/day = $6.80/day (+$4.25/day)
- **With Tier 2**: ~50 museums/day = $10.20/day (+$7.65/day)

### Cache Strategy
All Google Places data should be cached in `data/cache/phase0/` to avoid repeated API calls. Cache should include:
- All requested fields
- Timestamp of retrieval
- place_id for re-fetching if needed

### Data Provenance
Update `data_sources` array to distinguish between:
- `google_places_address` (current)
- `google_places_phone` (NEW)
- `google_places_hours` (NEW)
- `google_places_rating` (NEW)

## Example Enhanced API Response

```python
{
  "museum_id": "usa-co-aspen-aspen-art-museum",
  "success": true,
  "city": "Aspen",
  "street_address": "637 E Hyman Ave, Aspen, CO 81611, USA",
  "postal_code": "81611",
  "latitude": 39.1909,
  "longitude": -106.8175,
  "place_id": "ChIJ...",
  
  # NEW FIELDS (Tier 1)
  "phone": "(970) 925-8050",
  "phone_international": "+1 970-925-8050",
  "website_google": "https://www.aspenartmuseum.org/",
  "business_status": "OPERATIONAL",
  "opening_hours": {
    "open_now": true,
    "periods": [...],
    "weekday_text": [
      "Monday: Closed",
      "Tuesday: 10:00 AM – 6:00 PM",
      ...
    ]
  },
  
  # NEW FIELDS (Tier 2)
  "rating": 4.5,
  "user_ratings_total": 487,
  "types": ["museum", "tourist_attraction", "point_of_interest"],
  "price_level": 1,  # $ (inexpensive/free)
  
  "source": "google_places",
  "resolved_at": "2026-01-17T16:30:00Z"
}
```

## Conclusion

**We are significantly underutilizing Google Places API.** For an additional **$0.085 per museum** (Tier 1), we can:
- Eliminate dependency on IRS CSV for phones
- Get structured opening hours (better than web scraping)
- Detect closed museums (critical data quality)
- Validate websites

**Recommendation**: Implement **Tier 1 immediately** (5 additional fields). The ROI is clear: better data quality, reduced complexity, and elimination of unreliable data sources for a modest cost increase.

**Tier 2** should be considered once Tier 1 is validated and shows value in production usage.
