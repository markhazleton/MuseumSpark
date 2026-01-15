# Pre-MRD Phase Guide: Open Data Enrichment

**Version**: 1.0  
**Created**: 2026-01-15  
**Aligned with**: MRD v1.0, museum.schema.json v1.0

## Purpose

The **Pre-MRD Phase** is a new enrichment phase that runs **before** MRD Phase 1 to populate as many MRD-required fields as possible using **free/open data sources** (Wikidata, Wikipedia, OpenStreetMap). This reduces reliance on LLM-assisted enrichment and improves data quality by leveraging structured, verifiable sources.

---

## Why Pre-MRD Phase?

### Benefits
1. **Cost Reduction**: Free open data sources eliminate LLM API costs for basic fields
2. **Data Quality**: Structured sources (Wikidata) provide verifiable, traceable data
3. **Efficiency**: Batch processing with caching reduces repetitive API calls
4. **MRD Readiness**: Populates city_tier, reputation, collection_tier automatically

### Fields Populated from Open Data

| Field | Source | Method |
|-------|--------|--------|
| `city_tier` | Wikipedia + Manual List | Population lookup (1=Major hub, 2=Medium, 3=Small town) |
| `reputation` | Wikidata | Sitelink count heuristic (0=International, 1=National, 2=Regional, 3=Local) |
| `collection_tier` | Wikidata | Collection size claim (0=Flagship 100k+, 1=Strong 10k-100k, 2=Moderate 1k-10k, 3=Small <1k) |
| `time_needed` | Computed | Keyword matching on `museum_type` ("Quick stop", "Half day", "Full day") |
| `street_address` | Wikidata, Nominatim | P969 claim or geocoding |
| `postal_code` | Wikidata, Nominatim | P281 claim or address data |
| `latitude`, `longitude` | Wikidata, Nominatim | P625 coordinates or geocoding |
| `website` | Wikidata | P856 official website claim |

---

## Script: enrich-open-data.py

### Overview
Updated to support **Pre-MRD Phase** with `--compute-mrd-fields` flag.

### Key Features
- **Conservative**: Only fills missing/placeholder fields (never overwrites curated data)
- **Idempotent**: Safe to re-run without data thrashing
- **Cached**: HTTP responses stored in `data/cache/` to avoid rate limits
- **Traceable**: Records data sources in `data_sources` field

### Usage Examples

#### 1. Basic Pre-MRD Enrichment (Single State)
```bash
python scripts/enrich-open-data.py \
  --state IL \
  --compute-mrd-fields \
  --rebuild-index \
  --rebuild-reports
```

**What it does**:
- Looks up each museum in Wikidata
- Computes `city_tier` from Chicago → 1 (major hub)
- Infers `reputation` from Wikidata sitelinks (e.g., Art Institute of Chicago → 0 International)
- Infers `collection_tier` from Wikidata collection size
- Infers `time_needed` from museum_type
- Rebuilds master index with `nearby_museum_count` computed
- Updates progress report

#### 2. Dry Run (Preview Changes)
```bash
python scripts/enrich-open-data.py \
  --state CA \
  --only-placeholders \
  --compute-mrd-fields \
  --dry-run
```

**What it does**:
- Shows what would be changed without writing files
- Good for validation before committing changes

#### 3. Enrich with Website Scraping (Slower, More Comprehensive)
```bash
python scripts/enrich-open-data.py \
  --state NY \
  --compute-mrd-fields \
  --scrape-website \
  --rebuild-index
```

**What it does**:
- Everything in example 1
- PLUS: Fetches official museum website to extract structured address data
- PLUS: Extracts `open_hours_url`, `tickets_url`, `accessibility_url` from navigation links
- PLUS: Detects `reservation_required` from visit/ticket pages

#### 4. Enrich Specific Museum
```bash
python scripts/enrich-open-data.py \
  --museum-id usa-il-chicago-art-institute \
  --compute-mrd-fields \
  --rebuild-index
```

**What it does**:
- Enriches single museum by ID
- Useful for testing or fixing individual records

---

## Workflow: Pre-MRD Phase → MRD Phase 1 → Phase 2 → Phase 3

### Step 1: Pre-MRD Phase (Open Data Enrichment)

**Goal**: Populate MRD fields from open data sources

**Regional Priority (MRD Section 3.5)**:
1. Illinois / Midwest
2. Northeast
3. California
4. Remaining U.S.
5. Canada, Mexico, Bermuda

**Command Sequence** (example for Illinois):
```bash
# 1. Enrich Illinois museums with open data
python scripts/enrich-open-data.py \
  --state IL \
  --compute-mrd-fields \
  --scrape-website \
  --rebuild-index \
  --rebuild-reports

# 2. Validate schema compliance
python scripts/validate-json.py --state IL

# 3. Check progress
python scripts/build-progress.py

# 4. Commit changes
git add data/states/IL.json data/index/all-museums.json data/index/progress.json
git commit -m "Pre-MRD Phase: Enrich Illinois museums with open data"
```

**Expected Outcome**:
- `city_tier` populated for all museums
- `reputation` and `collection_tier` estimated for museums with Wikidata entries
- `time_needed` inferred from museum_type
- Address/coordinate fields filled where available

### Step 2: MRD Phase 1 (Master Dataset Backbone)

**Goal**: Complete all MRD core fields (may require LLM for gaps)

**Remaining Fields to Populate**:
- Refine `reputation` and `collection_tier` where Wikidata heuristic is low-confidence
- Populate `museum_type` and `primary_domain` if missing
- Complete address fields where open data failed

**Method**: LLM-assisted enrichment for remaining gaps

### Step 3: MRD Phase 2 (Art Museum Scoring)

**Goal**: Expert scoring of art museums

**Scope**: Museums where `primary_domain == "Art"`

**Fields to Populate**:
- `impressionist_strength` (1-5)
- `modern_contemporary_strength` (1-5)
- `historical_context_score` (1-5)
- `primary_art` (derived: "Impressionist" or "Modern/Contemporary")
- `priority_score` (computed via MRD formula)
- `is_scored` (set to `true`)

**Method**: Expert curator review + LLM assistance

### Step 4: MRD Phase 3 (Regional Rollout)

**Goal**: Complete Pre-MRD → Phase 1 → Phase 2 for all regions

**Execution**: Repeat Steps 1-3 for each geographic region in priority order

---

## city_tier Computation Details

### Tier 1: Major Cultural Hubs (Manual List)
```python
TIER_1_CITIES = {
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Washington", "Boston", "Detroit", "Nashville",
    "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee",
    "Albuquerque", "Tucson", "Fresno", "Sacramento", "Kansas City", "Atlanta",
    "Miami", "Minneapolis", "Cleveland", "New Orleans", "Oakland", "Tampa",
    "Honolulu", "Omaha", "Wichita", "Arlington",
    # Special cultural hubs (regardless of population)
    "Santa Fe", "Williamsburg", "Cambridge", "Berkeley", "Ann Arbor",
}
```

### Tier 2: Medium Cities (Population-Based)
- Population: 50,000 - 500,000
- Source: Wikipedia city infobox population
- Examples: Ann Arbor, Santa Barbara, Boulder

### Tier 3: Small Towns (Default)
- Population: < 50,000
- All remaining cities default to Tier 3

### Override Logic
1. Check if city is in TIER_1_CITIES manual list → return 1
2. Lookup population from Wikipedia API
3. If population >= 50,000 → return 2
4. Else → return 3

---

## reputation Inference Heuristic

Wikidata sitelink count correlates with museum prominence:

| Sitelinks | Reputation | Examples |
|-----------|------------|----------|
| 50+ | 0 (International) | MoMA, Louvre, British Museum, Met, Getty |
| 10-49 | 1 (National) | Walker Art Center, Denver Art Museum |
| 3-9 | 2 (Regional) | Sheldon Museum of Art, Weisman Art Museum |
| 1-2 | 3 (Local) | Small community museums |

**Note**: This is a heuristic starting point. LLM enrichment in Phase 1 will refine low-confidence classifications.

---

## collection_tier Inference Heuristic

Wikidata P3172 claim ("collection size") provides item counts:

| Collection Size | Tier | Classification |
|-----------------|------|----------------|
| 100,000+ | 0 | Flagship |
| 10,000 - 99,999 | 1 | Strong |
| 1,000 - 9,999 | 2 | Moderate |
| < 1,000 | 3 | Small |

**Note**: Many museums lack P3172 data. Phase 1 LLM enrichment will estimate collection tier from website descriptions.

---

## time_needed Inference

Keyword matching on `museum_type`:

| Time Estimate | Museum Type Keywords |
|---------------|---------------------|
| "Quick stop (1-2 hours)" | historic house, historic site, small gallery, local history |
| "Half day (2-4 hours)" | art museum, history museum, science museum, children's museum |
| "Full day (4+ hours)" | encyclopedic, major art museum, natural history, large complex |

**Default**: "Half day (2-4 hours)" for generic "museum" type

---

## Data Sources & Caching

### Wikidata
- **API**: `https://www.wikidata.org/w/api.php`
- **Cache TTL**: 14 days (2 weeks)
- **Rate Limit**: Conservative (1 second delay between uncached requests)

### Wikipedia
- **API**: `https://en.wikipedia.org/w/api.php`
- **Cache TTL**: 30 days (population data stable)
- **Rate Limit**: None (read-only API)

### OpenStreetMap Nominatim
- **API**: `https://nominatim.openstreetmap.org/search`
- **Cache TTL**: 14 days
- **Rate Limit**: 1 second delay (Nominatim usage policy)

### Cache Location
- `data/cache/open-data/*.json` (API responses)
- `data/cache/http/*.html` (website HTML)
- **Git Ignored**: Cache not committed to repo

---

## Quality Assurance

### Validation Checklist
1. **Schema Validation**: All enriched files MUST pass `validate-json.py`
2. **MRD Field Coverage**: Check progress.json for FULL record %
3. **Data Source Tracking**: Verify `data_sources` field populated
4. **Spot Checks**: Manually review 5-10 enriched museums per state

### Post-Enrichment Commands
```bash
# Validate schema compliance
python scripts/validate-json.py

# Rebuild master index with MRD field computation
python scripts/build-index.py --calculate-scores --update-nearby-counts

# Generate progress report
python scripts/build-progress.py

# Review FULL vs placeholder counts
cat data/index/progress.json | jq '.full, .placeholder, .full_pct'
```

---

## Troubleshooting

### Issue: Wikidata returns no results
**Symptom**: "Wikidata: no search results" in output  
**Cause**: Museum name not exact match or not in Wikidata  
**Solution**: Try alternative search terms or rely on Nominatim for geo data

### Issue: Wikipedia population lookup fails
**Symptom**: All cities default to Tier 3  
**Cause**: Wikipedia API query too restrictive  
**Solution**: City tier will be corrected in Phase 1 with manual review

### Issue: Rate limiting from Nominatim
**Symptom**: HTTP 429 errors  
**Cause**: Too many requests in short time  
**Solution**: Increase `--scrape-delay-seconds` or wait before retrying

### Issue: Website scraping blocked by robots.txt
**Symptom**: "Official site: blocked by robots.txt"  
**Cause**: Museum website disallows scraping  
**Solution**: Respect robots.txt, skip website scraping for that museum

---

## Next Steps After Pre-MRD Phase

1. **Review Progress**: Check `data/index/progress.json` for FULL record %
2. **Identify Gaps**: Run `build-missing-report.py` to see which fields still need LLM enrichment
3. **Phase 1 Enrichment**: Use LLM to populate remaining MRD core fields
4. **Phase 2 Scoring**: Expert curator scores art museums
5. **Iterate by Region**: Complete Pre-MRD → Phase 1 → Phase 2 for each region

---

**Document Owner**: Mark Hazleton  
**Last Updated**: 2026-01-15  
**Related Documents**:
- [MRD v1.0](specs/001-museum-trip-planner/MRD-Alignment-Summary.md)
- [Data Enrichment Strategy](Documentation/DataEnrichmentStrategy.md)
- [Scripts README](scripts/README.md)
