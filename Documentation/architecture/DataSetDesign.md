📘 MuseumSpark Dataset Design
Walker Art Reciprocal Program — Product Brief & Methodology Specification

**Authority**: This document implements the requirements defined in [MasterRequirements.md](MasterRequirements.md), which is the authoritative product specification written by the Product Owner.

## Purpose

This dataset is built to **prioritize museum visits based on art collection relevance, historical context, and travel efficiency** per the Master Requirements Document (MRD) v1.0.

The system enables users to:

- Discover reciprocal museums while traveling (Walker Art Reciprocal Program)
- Plan efficient multi-museum itineraries based on Priority Score ranking
- Compare visit value (time required, reputation/scope, collection strengths)
- Filter art museums by Impressionist and Modern/Contemporary strengths
- Review opportunities unlocked by reciprocal membership (admission access)

Seed source
The authoritative “seed list” of museums comes from Walker’s reciprocal membership page (https://walkerart.org/support/membership/reciprocal-membership/), extracted into:

- `data/index/walker-reciprocal.csv`

Walker’s main site is https://walkerart.org/.

MuseumSpark then enriches each seed row into a complete museum record using:

- LLM-assisted normalization and structured extraction
- official museum websites and other public sources
- computed fields (e.g., nearby museum count, derived ranking signals)

## Scope (MRD-Aligned)

### Dataset Scope

- **Geography**: United States (Phase 1), Canada/Bermuda/Mexico (Phase 2)
- **Source**: User-curated list from Walker Art Reciprocal Program
- **Inclusion Policy** (MRD Section 2B):
  - **All museums** are included in the dataset backbone
  - **Only relevant art museums** (fine art, encyclopedic, university) are scored for prioritization
  - **Non-art museums** remain in the dataset unscored to support city-level planning

### Data Enrichment Strategy

MuseumSpark enriches each seed row into a complete museum record using:

- **Open data sources** (prioritized, free): Official museum websites, Wikipedia, Google Places, etc.
- **LLM-assisted normalization**: Structured extraction, classification, and enrichment
- **Computed fields**: `nearby_museum_count`, `primary_art`, `priority_score`, `city_tier` (derived)

—

📊 Dataset Structure

Each museum record includes the following fields:

Canonical reference: `data/schema/museum.schema.json` defines the authoritative field set and validation rules.

## Museum record fields

### 🔹 Identity

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `museum_id` | string | Stable identifier (slug-based). | `usa-ak-anchorage-anchorage-museum` |
| `museum_name` | string | Official museum name. | `Anchorage Museum` |
| `alternate_names` | string[] \| null | Common abbreviations or prior names. | `["Anchorage Museum at Rasmuson Center"]` |
| `website` | string (URL) | Museum website URL. | `https://www.anchoragemuseum.org/` |
| `status` | `active` \| `closed` \| `seasonal` \| `unknown` \| null | Operating status. | `active` |
| `last_updated` | date (YYYY-MM-DD) \| null | Date this museum record was last updated (record-level). | `2026-01-15` |

### 🔹 Location & Geo

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `country` | string | Country name (dataset values like `USA`). | `USA` |
| `state_province` | string | Full state/province name. | `Alaska` |
| `city` | string | City. | `Anchorage` |
| `city_tier` | integer (1-3) \| null | City classification (MRD: 1=Major hub, 2=Medium city, 3=Small town). | `1` |
| `street_address` | string | Primary street address. | `625 C Street` |
| `address_line2` | string \| null | Suite/building/etc. | `null` |
| `postal_code` | string | Postal/ZIP code. | `99501` |
| `latitude` | number \| null | Latitude (-90..90). | `61.2176` |
| `longitude` | number \| null | Longitude (-180..180). | `-149.8936` |
| `place_id` | string \| null | Google Places ID or equivalent. | `ChIJ...` |
| `timezone` | string \| null | IANA timezone name. | `America/Anchorage` |
| `neighborhood` | string \| null | Neighborhood or district within the city. | `Downtown` |
| `city_region` | string \| null | Multi-city region label (if applicable). | `Bay Area` |

### 🔹 Address provenance

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `address_source` | `official_website` \| `google_places` \| `wikipedia` \| `manual` \| `unknown` \| null | Source for the address fields. | `official_website` |
| `address_last_verified` | date (YYYY-MM-DD) \| null | Date the address was last verified. | `2026-01-15` |

### 🔹 Classification & discovery

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `museum_type` | string | Human-friendly classification (can be mixed/nuanced). | `Mixed (Art & History)` |
| `primary_domain` | `Art` \| `History` \| `Science` \| `Culture` \| `Specialty` \| `Mixed` \| null | Primary domain used for filtering and (if applicable) scoring eligibility. | `Mixed` |
| `topics` | string[] \| null | Topic tags (periods, communities, themes). | `["Native Alaskan", "Contemporary"]` |
| `audience_focus` | `General` \| `Family` \| `Academic` \| `Children` \| `Specialist` \| null | Primary audience. | `General` |

### 🔹 Visit planning metadata

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `time_needed` | string \| null | Coarse visit duration estimate ("Quick stop" <1hr, "Half day" 2-4hr, "Full day" 5+hr). | `Half day` |
| `estimated_visit_minutes` | integer \| null | More precise estimate in minutes. | `180` |
| `best_season` | `Year-round` \| `Spring` \| `Summer` \| `Fall` \| `Winter` \| null | Best season to visit. | `Year-round` |
| `nearby_museum_count` | integer \| null | Count of other museums in the same city (computed from dataset). | `3` |
| `visit_priority_notes` | string \| null | Travel-specific notes separate from collection notes. | `Worth a standalone day trip.` |
| `parking_notes` | string \| null | Parking logistics. | `Paid garage adjacent.` |
| `public_transit_notes` | string \| null | Transit access info. | `Bus routes 1/2 stop nearby.` |

### 🔹 Visitor links (optional)

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `open_hours_url` | string (URL) \| null | Link to official hours/admission page. | `https://.../visit` |
| `tickets_url` | string (URL) \| null | Link to ticketing/booking page. | `https://.../tickets` |
| `reservation_required` | boolean \| null | Whether reservations are required. | `false` |
| `accessibility_url` | string (URL) \| null | Link to accessibility page. | `https://.../accessibility` |

### 🔹 Reputation & scope

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `reputation` | integer (0-3) \| null | Cultural significance tier (0=International, 1=National, 2=Regional, 3=Local). | `2` |
| `collection_tier` | integer (0-3) \| null | Relative size/depth of collections (0=Flagship, 1=Strong, 2=Moderate, 3=Small). Note: Separate from collection_based_strength used in scoring. | `2` |

### 🔹 Art scoring inputs (art museums only)

These fields are primarily used for visual art museums; non-art museums have these set to `null`.

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `impressionist_strength` | integer (0–5) \| null | Impressionist collection strength (0=None, 1=Limited, 2=Modest, 3=Strong Regional, 4=Major Scholarly, 5=Canon-Defining). | `4` |
| `modern_contemporary_strength` | integer (0–5) \| null | Modern/contemporary collection strength (same 0-5 scale). | `3` |
| `primary_art` | `Impressionist` \| `Modern/Contemporary` \| null | Dominant art strength category (derived as max of strength scores). | `Impressionist` |
| `historical_context_score` | integer (0–5) \| null | Quality of historical framing (0=None, 1=Limited, 2=Local, 3=Strong Regional, 4=Nationally Significant, 5=Canon-Level). | `5` |
| `exhibitions_curatorial_authority` | integer (0–5) \| null | ECA: Programmatic influence beyond permanent holdings (0=None, 1=Minimal, 2=Competent, 3=Strong Regional, 4=Nationally Recognized, 5=Field-Shaping). | `4` |
| `collection_based_strength` | integer (0–5) \| null | Overall depth/authority across all art categories (0=None, 1=Limited, 2=Modest, 3=Strong Regional, 4=Major Scholarly, 5=Canon-Defining). | `4` |

### 🔹 Computed scoring

| Field Name | Type | Description | Notes |
| --- | --- | --- | --- |
| `priority_score` | number \| null | Weighted score used for ranking (MRD formula, computed during data build). | Lower = higher priority |
| `is_scored` | boolean \| null | Whether this museum has been scored (true for art museums, false/null otherwise). | For filtering |
| `scoring_version` | string \| null | Version label of the scoring algorithm used. | e.g. `v1.0` |
| `scored_by` | `assistant` \| `manual` \| `hybrid` \| null | How the score was produced. | `hybrid` |
| `score_notes` | string \| null | Notes about scoring decisions. |  |
| `score_last_verified` | date (YYYY-MM-DD) \| null | Date score inputs/outputs last verified. |  |

### 🔹 Provenance, quality, and maintenance

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `data_sources` | string[] \| null | URLs or source tags supporting the record. | `["official_website"]` |
| `confidence` | integer (1–5) \| null | Overall confidence in accuracy. | `4` |
| `row_notes_internal` | string \| null | Internal notes for curators/maintainers. | `Needs geo coordinates.` |
| `created_at` | date (YYYY-MM-DD) \| null | Record creation date. | `2026-01-15` |
| `updated_at` | date (YYYY-MM-DD) \| null | Record last update date. | `2026-01-15` |
| `notes` | string \| null | Public-facing notes (highlights, tips, context). | `Excellent Alaska Native art...` |

—

📐 Scoring Methodology

MuseumSpark includes all Walker Reciprocal museums in the dataset. Some ranking inputs are art-centric; museums without sufficient scoring inputs can:

- have `priority_score` left as `null` (and sort after scored records), or
- be ranked by alternate/default heuristics (e.g., reputation + visit practicality) if/when introduced

🧮 Priority Score Formula (Lower = Higher Priority)

**Step 1: Determine Primary Art Strength**
```
Primary Art Strength = max(Impressionist Strength, Modern/Contemporary Strength)
```

**Step 2: Calculate Base Score**
```
Priority Score =
  (5 – Primary Art Strength) × 3
+ (5 – Historical Context Score) × 2
+ (5 – Collection-Based Strength) × 2
+ Reputation Tier
```

**Step 3: Apply Bonuses (Subtract from Score)**
```
– Dual-Strength Bonus (–2 if both Impressionist Strength ≥4 AND Modern/Contemporary Strength ≥4)
– ECA Bonus (–1 if Exhibitions & Curatorial Authority ≥4)
```

**Scoring Dimensions** (MRD Section 4):

* **Impressionist Strength** (0–5): Depth of Impressionist permanent collection
  * 5 = Canon-Defining Collection (field-defining national/international authority)
  * 4 = Major Scholarly Collection (deep holdings with national significance)
  * 3 = Strong Regional or Thematic Collection
  * 2 = Modest or Supporting Collection
  * 1 = Limited Collection Presence
  * 0 = No Meaningful Impressionist Holdings

* **Modern/Contemporary Strength** (0–5): Depth of Modern/Contemporary permanent collection (same scale as Impressionist)

* **Historical Context Score** (0–5): Quality of historical framing and interpretation
  * 5 = Canon-Level Historical Importance (essential for understanding major movements)
  * 4 = Nationally Significant Context
  * 3 = Strong Regional Context
  * 2 = Local Context
  * 1 = Limited Context
  * 0 = No Contextual Framing

* **Exhibitions & Curatorial Authority (ECA)** (0–5): Programmatic influence beyond permanent holdings
  * 5 = Field-Shaping Curatorial Authority
  * 4 = Nationally Recognized Curatorial Program
  * 3 = Strong Regional Curatorial Program
  * 2 = Competent Exhibition Programming
  * 1 = Minimal Curatorial Authority
  * 0 = No Curatorial Program of Note

* **Collection-Based Strength** (0–5): Overall depth/authority across all art categories
  * 5 = Canon-Defining Collection
  * 4 = Major Scholarly Collection
  * 3 = Strong Regional or Thematic Collection
  * 2 = Modest or Supporting Collection
  * 1 = Limited Collection Presence
  * 0 = No Meaningful Permanent Collection

* **Reputation Tier** (0–3): Cultural significance tier
  * 0 = International
  * 1 = National
  * 2 = Regional
  * 3 = Local

**Score Interpretation**:
* Lower scores = higher priority
* Negative scores are possible (world-class institutions with multiple bonuses)
* Museums with Historical Context = 5 flagged as potential "Must-See"
* Non-art museums have `priority_score: null` and `is_scored: false`

This design ensures high-value institutions (e.g., AIC, MoMA, MFA Boston) float to the top automatically, while also revealing hidden gems with relevant strength and historical curation.

—

🛠️ Methodology & Workflow

1. Validate the Walker reciprocal roster (`data/index/walker-reciprocal.csv`) for structural integrity and scrape artifacts
2. Add every reciprocal museum to `data/index/all-museums.json` (the master list used for browsing/search)
3. Add museums by state to `data/states/{state}.json` as the primary per-state “work queue” for enrichment
4. For each state file, enrich each museum record to fully populate the schema fields (LLM-assisted + official sites + other public sources)
5. Run JSON validation for the updated state file(s) against `data/schema/museum.schema.json`
6. Rebuild/update `data/index/all-museums.json` to reflect the newly enriched per-state records

—

🧩 Output Format

Available as a clean, structured spreadsheet (CSV or Excel) with:

* Fully filterable columns
* Sortable priority scores
* Hyperlinked museum names
* Ready for itinerary planning, analysis, or expansion

—

Let me know if you'd like this delivered as a downloadable spreadsheet, API schema, or embedded database model.
