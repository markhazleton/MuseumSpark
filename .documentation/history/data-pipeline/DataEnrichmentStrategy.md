# Data Enrichment Strategy — MRD Field Population

**Version**: 1.0  
**Last Updated**: 2026-01-15  
**Aligned with**: MRD v1.0, museum.schema.json v1.0

## Objective

This document defines the strategy for populating all MRD-required fields for each museum record, prioritizing **free/open data sources** before falling back to LLM-assisted enrichment.

---

## Priority: Open Data First

Per project requirements, we prioritize data sources in this order:

1. **Open/Free Sources** (Tier 1) — No API costs
2. **LLM-Assisted Extraction** (Tier 2) — Used when open sources insufficient
3. **Manual Curation** (Tier 3) — Expert review for complex/ambiguous cases

---

## Field-by-Field Enrichment Strategy

### 🔹 **Identity & Structural Fields** (Schema Required)

| Field | Strategy | Source Priority |
|-------|----------|----------------|
| `museum_id` | Generate from slug: `{country_code}-{state_code}-{city_slug}-{museum_slug}` | **Computed** |
| `museum_name` | Extract from official website, Walker roster | **Open**: Official site, IMLS, Wikipedia |
| `alternate_names` | Extract abbreviations, historical names | **Open**: Wikipedia, IMLS; **LLM**: Extract from "About" pages |
| `website` | Official URL from Walker roster or search | **Open**: Walker roster, Google Places, IMLS |
| `status` | Active/Closed/Seasonal determination | **Open**: Check website, Google Places status; **LLM**: Parse website content |

### 🔹 **Location & Geo**

| Field | Strategy | Source Priority |
|-------|----------|----------------|
| `country`, `state_province`, `city` | From Walker roster or geocoding | **Open**: Walker roster, Google Places |
| `street_address`, `postal_code` | Address extraction | **Open**: Official website footer, Google Places API |
| `latitude`, `longitude` | Geocoding from address | **Open**: Google Geocoding API (free tier) or OpenStreetMap Nominatim |
| `place_id` | Google Places lookup | **Open**: Google Places API |
| `timezone` | Derive from lat/lon | **Computed**: Python `timezonefinder` library |
| `neighborhood`, `city_region` | Local context extraction | **Open**: Wikipedia, Google Places; **LLM**: Describe location context |

**Address Provenance**:
- `address_source`: Record source used (e.g., `official_website`, `google_places`)
- `address_last_verified`: Set to current date on enrichment

### 🔹 **NEW: City Tier** (MRD Section 3.6)

| Field | Strategy | Source Priority |
|-------|----------|----------------|
| `city_tier` | Classify as 1 (Major hub), 2 (Medium city), 3 (Small town) | **Computed** + **Open** |

**City Tier Derivation Logic**:

```python
# Tier 1: Major hubs (Major metro areas)
TIER_1_CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Washington", "Boston", "Detroit", "Nashville",
    "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee",
    "Albuquerque", "Tucson", "Fresno", "Sacramento", "Kansas City", "Atlanta",
    "Miami", "Minneapolis", "Cleveland", "New Orleans", "Oakland", "Tampa",
    "Honolulu", "Omaha", "Wichita", "Arlington"
]

# Tier 2: Medium cities (Population 50k-500k or significant regional centers)
# Use US Census population data or Wikipedia infobox population
# Examples: Ann Arbor, Berkeley, Cambridge, Santa Fe, Asheville

# Tier 3: Small towns (Population < 50k)
# Remaining cities default to Tier 3

def derive_city_tier(city: str, state: str) -> int:
    """
    Derive city tier using:
    1. Known major hubs list (Tier 1)
    2. US Census population data if available (Tier 2 if 50k-500k)
    3. Default to Tier 3 for small towns
    """
    if city in TIER_1_CITIES:
        return 1
    
    # Look up population from open data (US Census API - free)
    # https://www.census.gov/data/developers/data-sets/popest-popproj/popest.html
    population = fetch_census_population(city, state)
    
    if population >= 50_000:
        return 2
    else:
        return 3
```

**Data Source**: 
- US Census Bureau Population Estimates API (free)
- Fallback: Wikipedia city infobox population
- Manual override list for known major cultural hubs (e.g., Santa Fe, Williamsburg)

### 🔹 **Classification**

| Field | Strategy | Source Priority |
|-------|----------|----------------|
| `museum_type` | Human-friendly classification | **Open**: IMLS dataset `museum_type`, website "About"; **LLM**: Classify from mission statement |
| `primary_domain` | `Art` \| `History` \| `Science` \| etc. | **Open**: IMLS `discipline`; **LLM**: Parse museum type/mission |
| `topics` | Extract subject tags | **LLM**: Extract from "Collections" page; **Open**: IMLS subject fields |
| `audience_focus` | General/Family/Academic/etc. | **LLM**: Analyze website education/visitor sections |

### 🔹 **Visit Planning Metadata**

| Field | Strategy | Source Priority |
|-------|----------|----------------|
| `time_needed` | Quick stop / Half day / Full day | **LLM**: Estimate from collection size, building sq ft, website visit guidance |
| `estimated_visit_minutes` | More precise estimate | **LLM**: Parse visitor info, infer from gallery count |
| `best_season` | Year-round / Seasonal | **Open**: Website hours; **LLM**: Consider climate, tourism patterns |
| `nearby_museum_count` | Count other museums in same city | **Computed**: Count from `all-museums.json` where `city` matches |
| `visit_priority_notes` | Travel tips | **Manual**: Curator adds contextual notes |
| `parking_notes`, `public_transit_notes` | Logistics | **Open**: Website visitor info; **LLM**: Extract from "Plan Your Visit" |

**Nearby Museum Count Computation**:
```python
def compute_nearby_museum_count(museum_id: str, all_museums: list) -> int:
    """
    Count other museums in the same city (excluding current museum).
    """
    current_museum = find_museum_by_id(museum_id, all_museums)
    city = current_museum["city"]
    state = current_museum["state_province"]
    
    nearby = [
        m for m in all_museums
        if m["city"] == city 
        and m["state_province"] == state
        and m["museum_id"] != museum_id
    ]
    
    return len(nearby)
```

### 🔹 **NEW: Reputation & Collection Tier** (MRD Numeric 0-3)

| Field | Strategy | Source Priority |
|-------|----------|----------------|
| `reputation` | 0=International, 1=National, 2=Regional, 3=Local | **LLM**: Classify based on AAM accreditation, international exhibitions, media presence |
| `collection_tier` | 0=Flagship, 1=Strong, 2=Moderate, 3=Small | **LLM**: Estimate from collection size, gallery square footage, permanent collection scope |

**Reputation Classification Heuristics** (for LLM prompts):

- **International (0)**: Top-tier global recognition (MoMA, Louvre, British Museum, Art Institute of Chicago, Metropolitan Museum, Getty, Tate, Uffizi, Rijksmuseum, Hermitage)
- **National (1)**: Major national institutions, frequently cited in art history, host traveling blockbusters
- **Regional (2)**: Significant in multi-state region, AAM-accredited, known in art community
- **Local (3)**: Community/city-level significance, serves local audience primarily

**Collection Tier Heuristics**:

- **Flagship (0)**: 100k+ objects, encyclopedic or deep specialist collection, major art historical holdings
- **Strong (1)**: 10k-100k objects, significant depth in core areas, respected collection
- **Moderate (2)**: 1k-10k objects, solid regional collection, focused scope
- **Small (3)**: <1k objects, niche focus, or emerging institution

### 🔹 **Art Scoring Inputs** (Art Museums Only — MRD Section 4)

| Field | Strategy | Source Priority |
|-------|----------|----------------|
| `impressionist_strength` | 1-5 scale | **LLM**: Analyze collection highlights, permanent galleries; **Manual**: Expert verification |
| `modern_contemporary_strength` | 1-5 scale | **LLM**: Same approach |
| `primary_art` | Derived: "Impressionist" or "Modern/Contemporary" | **Computed**: `max(impressionist_strength, modern_contemporary_strength)` |
| `historical_context_score` | 1-5 curatorial strength | **LLM**: Assess didactic labels, thematic galleries, interpretive depth |

**Impressionist/Modern Strength Scale** (MRD Section 4.7-4.8):
- **5 = Flagship**: Major permanent holdings, dedicated galleries (e.g., AIC Impressionism, MoMA Modern)
- **4 = Strong**: Significant representation, multiple key artists
- **3 = Moderate**: Representative works, rotating displays
- **2 = Minor**: Few works, not a collection focus
- **1 = None**: No holdings in this area

**Historical Context Score** (MRD Section 4.10):
- **5**: Strong chronological narrative, thematic interpretation, scholarly labels
- **3**: Inconsistent or surface-level context, basic labels
- **1**: Minimal or absent historical framing

**LLM Enrichment Approach**:
1. Fetch museum website "Collections" and "Highlights" pages
2. Prompt LLM with scoring rubric + website content
3. Generate initial scores with confidence level
4. Flag low-confidence scores for manual review
5. Expert curator validates/adjusts art scores

### 🔹 **Computed Scoring Fields**

| Field | Strategy | Source Priority |
|-------|----------|----------------|
| `priority_score` | Computed via MRD formula | **Computed**: Apply formula when all inputs available |
| `is_scored` | Boolean flag | **Computed**: `true` if art museum with complete scoring inputs, else `false` or `null` |
| `scoring_version` | Algorithm version tag | **Computed**: Set to `v1.0` (MRD formula) |
| `scored_by` | `assistant` \| `manual` \| `hybrid` | **Metadata**: Track enrichment method |

**Priority Score Computation** (MRD Section 5):

```python
def compute_priority_score(museum: dict) -> float | None:
    """
    Compute Priority Score per MRD formula.
    Returns None if museum is not scored (non-art or missing inputs).
    """
    # Only score art museums with complete inputs
    if not museum.get("is_scored"):
        return None
    
    imp_strength = museum.get("impressionist_strength")
    mod_strength = museum.get("modern_contemporary_strength")
    hist_score = museum.get("historical_context_score")
    reputation = museum.get("reputation")
    collection = museum.get("collection_tier")
    
    # Require all inputs
    if None in [imp_strength, mod_strength, hist_score, reputation, collection]:
        return None
    
    # MRD Formula
    primary_art_strength = max(imp_strength, mod_strength)
    
    dual_bonus = 2 if (imp_strength >= 4 and mod_strength >= 4) else 0
    
    priority_score = (
        (6 - primary_art_strength) * 3
        + (6 - hist_score) * 2
        + reputation  # 0-3 numeric penalty
        + collection  # 0-3 numeric penalty
        - dual_bonus
    )
    
    return priority_score
```

**Primary Art Derivation**:
```python
def derive_primary_art(museum: dict) -> str | None:
    """
    Derive primary_art from strength scores (MRD Section 4.9).
    """
    imp = museum.get("impressionist_strength")
    mod = museum.get("modern_contemporary_strength")
    
    if imp is None and mod is None:
        return None
    
    if imp is None:
        return "Modern/Contemporary"
    if mod is None:
        return "Impressionist"
    
    if imp > mod:
        return "Impressionist"
    elif mod > imp:
        return "Modern/Contemporary"
    else:
        # Tie: default to Modern/Contemporary (or flag for manual review)
        return "Modern/Contemporary"
```

### 🔹 **Provenance & Quality**

| Field | Strategy | Source Priority |
|-------|----------|----------------|
| `data_sources` | List of URLs/source tags | **Metadata**: Track all sources used (e.g., `["official_website", "imls_dataset", "wikipedia"]`) |
| `confidence` | 1-5 overall confidence | **Computed**: Assess source quality, completeness, verification status |
| `row_notes_internal` | Maintenance notes | **Manual**: Curators flag issues, TODOs |
| `created_at`, `updated_at` | Record timestamps | **Computed**: Set on initial creation and updates |
| `notes` | Public-facing highlights | **Manual**: Curator adds context, signature artists, travel tips |

**Confidence Scoring**:
- **5**: All fields verified from official sources, address confirmed, scoring validated
- **4**: Most fields from reliable sources, minor gaps in optional fields
- **3**: Mix of sources, some LLM-generated content, not fully verified
- **2**: Largely LLM-inferred, missing several optional fields
- **1**: Minimal data, placeholder quality, needs substantial enrichment

---

## Enrichment Workflow (Phased Approach)

### Phase 1: Master Dataset Backbone (MRD Phase 1)

**Goal**: Populate all structural + MRD core fields for every museum

**Priority Fields**:
1. Identity: `museum_id`, `museum_name`, `website`, `status`
2. Location: `country`, `state_province`, `city`, `city_tier`, `street_address`, `postal_code`, `lat/lon`
3. Classification: `museum_type`, `primary_domain`
4. Quality: `reputation`, `collection_tier`, `time_needed`, `nearby_museum_count`
5. Provenance: `data_sources`, `confidence`, `created_at`

**Execution**:
1. Extract seed list from Walker roster
2. Normalize addresses via Google Places API
3. Geocode all museums
4. Compute `city_tier` using Census API + manual overrides
5. Compute `nearby_museum_count` from master list
6. LLM-classify `reputation` and `collection_tier`
7. Validate against schema

**Output**: All museums have FULL backbone (not yet scored)

### Phase 2: Scoring (Art Museums Only — MRD Phase 2)

**Goal**: Apply expert scoring to art museums

**Scope**: Fine art, encyclopedic, university art museums

**Priority Fields**:
1. `impressionist_strength`, `modern_contemporary_strength`, `historical_context_score`
2. `primary_art` (derived)
3. `priority_score` (computed)
4. `is_scored` (set to `true`)
5. `scoring_version`, `scored_by`

**Execution**:
1. Filter museums where `primary_domain == "Art"` or manually flagged
2. Fetch collection/highlights pages
3. LLM-generate initial scores with rubric
4. Expert curator reviews and adjusts
5. Compute `priority_score` via MRD formula
6. Set `is_scored = true`
7. Validate scoring outputs

**Output**: Art museums have complete scoring, non-art museums remain `is_scored = false`

### Phase 3: Regional Rollout (MRD Phase 3)

**Geographic Priority**:
1. Illinois / Midwest anchors (Chicago, Milwaukee, Indianapolis, etc.)
2. Northeast cluster (Boston, NYC, Philadelphia, DC, etc.)
3. California (LA, SF, San Diego, etc.)
4. Remaining U.S. states
5. Canada, Mexico, Bermuda

**Execution**: Apply Phases 1+2 sequentially to each region, with review checkpoints after each geographic cluster.

---

## Data Sources Reference

### Free/Open Data Sources (Tier 1)

| Source | API/Access | Use Cases | Cost |
|--------|-----------|-----------|------|
| **IMLS Museum Dataset** | CSV download | Museum type, discipline, address | Free |
| **Google Places API** | REST API (free tier) | Address, lat/lon, `place_id`, status | Free (limited quota) |
| **OpenStreetMap Nominatim** | REST API | Geocoding (fallback) | Free |
| **US Census Population API** | REST API | City population for `city_tier` | Free |
| **Wikipedia API** | REST API | Museum info, history, collection highlights | Free |
| **Official Museum Websites** | Web scraping | Address, hours, collection info | Free (scrape ethically) |

### LLM-Assisted (Tier 2)

| Task | LLM Prompt Strategy | Validation |
|------|---------------------|------------|
| **Reputation Classification** | Provide museum name, website, Wikipedia summary → Classify 0-3 with reasoning | Manual spot-checks on 10% sample |
| **Collection Tier** | Parse collection size, gallery count, scope → Classify 0-3 | Cross-reference with IMLS data |
| **Art Strength Scoring** | Provide collection highlights, permanent galleries → Score 1-5 with rubric | Expert curator validates all art museums |
| **Historical Context Score** | Analyze didactic labels, thematic organization → Score 1-5 | Manual review of low-confidence scores |
| **Visit Time Estimation** | Parse visitor info, gallery count → Estimate Quick stop/Half day/Full day | Compare with user reviews |

### Manual Curation (Tier 3)

| Task | When Required | Owner |
|------|---------------|-------|
| **Art Scoring Validation** | All art museums after LLM initial pass | Expert curator (Mark Hazleton) |
| **Notes (highlights/tips)** | Optional, adds value for planning | Curator |
| **Ambiguous Cases** | Museum type unclear, historical context complex | Curator reviews LLM output |
| **Score Disputes** | When LLM confidence < 0.7 or stakeholder questions | Expert adjudication |

---

## Quality Assurance

### Validation Checkpoints

1. **Schema Validation**: All records MUST pass `museum.schema.json` validation
2. **Completeness Check**: FULL vs placeholder counts tracked in `data/index/progress.json`
3. **Scoring Integrity**: Priority scores recomputed on every data build, verified against formula
4. **Geographic Coverage**: Per-state FULL record % tracked
5. **Expert Review**: Curator validates all art museum scores before regional rollout completion

### Automated Checks (CI/CD)

```bash
# Pre-commit hooks
python scripts/validate-json.py  # Schema validation
python scripts/build-index.py    # Rebuild master list with computed fields
python scripts/build-progress.py # Track FULL vs placeholder counts

# CI on PR
- Validate all state files against schema
- Check for duplicate museum_ids
- Verify priority_score formula correctness
- Flag museums with confidence < 3
```

---

## Implementation Priority (Next Steps)

1. **Immediate**: Update `build-index.py` to compute new MRD fields (`city_tier`, `primary_art`, `is_scored`, `priority_score`)
2. **Phase 1 Focus**: Enrich Illinois/Midwest museums with full MRD backbone
3. **Phase 2 Focus**: Score art museums in Illinois/Midwest region
4. **Iterate**: Expand to Northeast, then remaining regions per MRD Phase 3

---

**Last Updated**: 2026-01-15  
**Next Review**: After Phase 1 completion (Illinois/Midwest enrichment)
