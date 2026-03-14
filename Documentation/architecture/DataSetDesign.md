📘 MuseumSpark Dataset Design
Walker Art Reciprocal Program — Product Brief & Methodology Specification

**Version:** v3.1.T (2026-03-14)
**Authority**: This document implements the requirements defined in [MasterRequirements.md](MasterRequirements.md), which is the authoritative product specification written by the Product Owner.

## Purpose

This dataset is built to **prioritize museum visits based on art collection relevance, historical context, and travel efficiency** per the Master Requirements Document (MRD) v3.1.T.

The system enables users to:

- Discover reciprocal museums while traveling (Walker Art Reciprocal Program)
- Plan efficient multi-museum itineraries based on Priority Score ranking and Outcome Tier
- Compare visit value (time required, reputation/scope, collection strengths)
- Filter art museums by Impressionist, Modern/Contemporary, and Historical Art Traditions strengths
- Review opportunities unlocked by reciprocal membership (admission access)

Seed source: The authoritative "seed list" of museums comes from Walker's reciprocal membership page, extracted into `data/index/walker-reciprocal.csv`.

MuseumSpark enriches each seed row into a complete museum record using:
- LLM-assisted normalization and structured extraction
- Official museum websites and other public sources
- Computed fields (e.g., nearby museum count, derived ranking signals)

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
- **Computed fields**: `nearby_museum_count`, `primary_art`, `priority_score`, `outcome_tier` (derived)

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
| `museum_type` | string | Human-friendly classification (locked set per MRD Section 7). | `Art Museum` |
| `primary_domain` | `Art` \| `History` \| `Science` \| `Culture` \| `Specialty` \| `Mixed` \| null | Primary domain used for filtering and scoring eligibility. | `Art` |
| `topics` | string[] \| null | Topic tags (periods, communities, themes). | `["Native Alaskan", "Contemporary"]` |
| `audience_focus` | `General` \| `Family` \| `Academic` \| `Children` \| `Specialist` \| null | Primary audience. | `General` |
| `primary_focus` | string \| null | Concise classification phrase (neutral, factual, sortable — see MRD Section 8). | `Modern and contemporary art museum` |

### 🔹 Visit planning metadata

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `time_needed` | string \| null | Coarse visit duration estimate. Values: "Quick stop" (~1–1.25hr), "Half day" (~2.5–3hr), "Most of the Day" (~4–5hr), "All Day" (~6–7hr). | `Half day` |
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
| `reputation_level` | string \| null | Structural scope of institutional recognition (International / National / Regional / Supra-Local / Local). See MRD Section 4, field 14 for full definitions and evidence standards. | `Regional` |
| `collection_level` | string \| null | Scale and structural role of permanent holdings (Flagship / Strong / Moderate / Small). See MRD Section 4, field 15 for full definitions and evidence standards. | `Strong` |

### 🔹 Art scoring inputs (art museums only)

These fields are primarily used for visual art museums; non-art museums have these set to `null`.

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `impressionist_strength` | integer (0–5) \| null | Impressionist/Post-Impressionist collection strength (0=None, 1=Limited, 2=Modest, 3=Strong Regional, 4=Major Scholarly, 5=Canon-Defining). | `4` |
| `modern_contemporary_strength` | integer (0–5) \| null | Modern/Contemporary collection strength (same 0-5 scale). | `3` |
| `hat_strength` | integer (0–5) \| null | Historical Art Traditions collection strength (same 0-5 scale). Art grounded in sustained historical traditions; tradition-based rather than modernist. | `2` |
| `historical_context_score` | integer (0–5) \| null | Quality of historical interpretation depth (0=None, 1=Minimal, 2=Descriptive/Local, 3=Intentional Framing, 4=Deep Integrated, 5=Canon-Defining). | `5` |
| `eca_score` | integer (0–5) \| null | Exhibitions & Curatorial Authority: Programmatic influence beyond permanent holdings (0=None, 1=Minimal, 2=Competent, 3=Strong Regional, 4=Nationally Recognized, 5=Field-Shaping). | `4` |
| `collection_based_strength` | integer (0–5) \| null | Overall depth/authority across all art categories (0=None, 1=Limited, 2=Modest, 3=Strong Regional, 4=Major Scholarly, 5=Canon-Defining). | `4` |

### 🔹 Computed scoring

| Field Name | Type | Description | Notes |
| --- | --- | --- | --- |
| `collection_based_pas` | integer (0–5) \| null | MAX(impressionist_strength, modern_contemporary_strength, hat_strength). The strongest single art category. | Derived |
| `effective_pas` | integer (0–5) \| null | MAX(collection_based_pas, eca_score). ECA may elevate but does not sum. | Derived |
| `priority_score` | integer \| null | Weighted score used for ranking (v3.1.T formula, computed during data build). Floor of 1. Lower = higher priority. | Lower = higher priority |
| `outcome_tier` | string \| null | Behavioral routing tier: Must-See / High Priority / Regionally Important / Detour / Consider / Background. | Deterministic |
| `additional_labels` | string \| null | Subtype for Detour/Consider tiers (e.g., Specialized Art Site, Locally Historic, Kunsthalle). | Required for Detour/Consider |
| `audit_tracker` | string \| null | Version, date, and outcome of last audit (format: "v3.1.T | 2026-03-01 | NC"). | Informational only |
| `is_scored` | boolean \| null | Whether this museum has been scored (true for art museums, false/null otherwise). | For filtering |
| `scoring_version` | string \| null | Version label of the scoring algorithm used. | e.g. `v3.1.T` |
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
| `notes` | string \| null | Public-facing notes (factual, neutral, 2–4 sentences per MRD Section 8). | `Excellent Alaska Native art...` |

—

📐 Scoring Methodology (v3.1.T)

MuseumSpark includes all Walker Reciprocal museums in the dataset. Museums without sufficient scoring inputs have `priority_score: null` and sort after scored records.

### PAS Model

**Collection-Based PAS (Primary Art Strength)**
```
Collection-Based PAS = MAX(impressionist_strength, modern_contemporary_strength, hat_strength)
```
Only the strongest single axis feeds into the priority score. Strengths are never summed.

**Effective PAS**
```
Effective PAS = MAX(Collection-Based PAS, eca_score)
```
ECA may elevate PAS to reflect curatorial authority even when permanent holdings are weaker. The floor behavior ensures an exhibition-powerhouse institution is never penalized by a weak collection alone.

### 🧮 Priority Score Formula (Lower = Higher Priority)

**Step 1: Dual-Strength Bonus**
```
Dual-Strength Bonus = -2  if impressionist_strength >= 3 AND modern_contemporary_strength >= 3
                    =  0  otherwise
```
Note: Threshold is ≥3 (not ≥4). HAT does not qualify for this bonus.

**Step 2: Reputation Penalty**
```
International  = +0
National       = +0
Regional       = +2
Supra-Local    = +3
Local          = +4
```

**Step 3: Collection Penalty**
```
Flagship = +0
Strong   = +0
Moderate = +2
Small    = +4
```

**Step 4: Priority Score**
```
Priority Score = MAX(1,
    (6 - Effective PAS) × 2
  + (6 - Historical Context Score)
  + Reputation Penalty
  + Collection Penalty
  + Dual-Strength Bonus
)
```

### Outcome Tier Assignment (Deterministic)

| Tier | Assignment Criteria |
|------|---------------------|
| Must-See | Collection-Based PAS = 5, OR Historical Context = 5 |
| High Priority | Priority Score ≤ 9; OR Flagship + PAS = 4; OR ECA ≥ 4; OR HC = 4 + National/International rep |
| Regionally Important | Score 10–15 AND Regional rep AND strong regional art or HC reference |
| Detour | Specialization signal AND (Effective PAS ≥ 3 OR HC ≥ 3) |
| Consider | Proximity-dependent value; no routing pull |
| Background | Default; limited travel gravity |

### Score Dimensions Summary

**Impressionist/Post-Impressionist Strength** (0–5)
* 5 = Canon-Defining (field-defining national/international authority, canonical works)
* 4 = Major Scholarly (deep holdings, national significance)
* 3 = Strong Regional or Thematic
* 2 = Modest or Supporting
* 1 = Limited Presence
* 0 = None

**Modern/Contemporary Strength** (0–5) — same scale as Impressionist

**Historical Art Traditions (HAT) Strength** (0–5) — same scale; tradition-based art (pre-modern lineage, non-Western canons, workshop/court traditions); NOT defined by modernist rupture

**Historical Context Score** (0–5)
* 5 = Canon-Defining Interpretation (field-shaping, Must-See qualifier)
* 4 = Deep Integrated Interpretation
* 3 = Intentional Historical Framing
* 2 = Descriptive / Place-Based
* 1 = Minimal Historical Presence
* 0 = None

**Exhibitions & Curatorial Authority (ECA)** (0–5)
* 5 = Field-Shaping Curatorial Authority
* 4 = Nationally Recognized Curatorial Program
* 3 = Strong Regional Curatorial Program
* 2 = Competent Exhibition Programming
* 1 = Minimal Curatorial Authority
* 0 = None

**Collection-Based Strength** (0–5) — same scale; overall permanent holdings depth

**Reputation Level** (string)
* International / National — penalty +0
* Regional — penalty +2
* Supra-Local — penalty +3
* Local (default) — penalty +4

**Collection Level** (string)
* Flagship / Strong — penalty +0
* Moderate — penalty +2
* Small (default) — penalty +4

—

🛠️ Methodology & Workflow

1. Validate the Walker reciprocal roster (`data/index/walker-reciprocal.csv`) for structural integrity and scrape artifacts
2. Add every reciprocal museum to `data/index/all-museums.json` (the master list used for browsing/search)
3. Add museums by state to `data/states/{state}.json` as the primary per-state "work queue" for enrichment
4. For each state file, enrich each museum record to fully populate the schema fields (LLM-assisted + official sites + other public sources)
5. Phase 2: Run LLM scoring for art museums (impressionist_strength, hat_strength, modern_contemporary_strength, historical_context_score, eca_score, collection_based_strength, reputation_level, collection_level)
6. Phase 3: Run deterministic priority score and outcome tier computation
7. Run JSON validation for the updated state file(s) against `data/schema/museum.schema.json`
8. Rebuild/update `data/index/all-museums.json` to reflect the newly enriched per-state records

—

🧩 Output Format

Available as a clean, structured spreadsheet (CSV or Excel) with:

* Fully filterable columns
* Sortable priority scores
* Outcome tier classification
* Hyperlinked museum names
* Ready for itinerary planning, analysis, or expansion
