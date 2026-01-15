📘 MuseumSpark Dataset Design
Walker Art Reciprocal Program — Product Brief & Methodology Specification

Purpose
This dataset is built to **rank and document every museum in the Walker Art Reciprocal Program**, so members can:

- discover reciprocal museums while traveling
- plan efficient multi-museum itineraries
- compare visit value (time required, reputation/scope, collection strengths)
- review opportunities unlocked by reciprocal membership (admission access, reciprocal coverage while on trips)

Seed source
The authoritative “seed list” of museums comes from Walker’s reciprocal membership page (https://walkerart.org/support/membership/reciprocal-membership/), extracted into:

- `data/index/walker-reciprocal.csv`

Walker’s main site is https://walkerart.org/.

MuseumSpark then enriches each seed row into a complete museum record using:

- LLM-assisted normalization and structured extraction
- official museum websites and other public sources
- computed fields (e.g., nearby museum count, derived ranking signals)

Scope

- Include **all** museums listed in the Walker Art Reciprocal Program (including non‑US entries where present)
- Normalize and de-duplicate institutions (stable IDs, canonical names, consistent location fields)
- Populate the full field set defined by `data/schema/museum.schema.json`
- Compute ranking fields when inputs are available; allow partial data and progressively improve records over time

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
| `time_needed` | `Quick stop` \| `Half day` \| `Full day` \| null | Coarse visit duration estimate. | `Half day` |
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
| `reputation` | `Local` \| `Regional` \| `National` \| `International` \| null | Cultural significance tier. | `Regional` |
| `collection_tier` | `Small` \| `Moderate` \| `Strong` \| `Flagship` \| null | Relative size/depth of collections (where applicable). | `Moderate` |

### 🔹 Art scoring inputs (art museums only)

These fields are primarily used for visual art museums; non-art museums may have these set to `null`.

| Field Name | Type | Description | Example |
| --- | --- | --- | --- |
| `impressionist_strength` | integer (0–5) \| null | Impressionist collection strength. | `4` |
| `modern_contemporary_strength` | integer (0–5) \| null | Modern/contemporary collection strength. | `3` |
| `primary_art` | `Impressionist` \| `Modern/Contemporary` \| `Tie` \| `None` \| null | Dominant art strength category derived from strengths. | `Modern/Contemporary` |
| `historical_context_score` | integer (1–5) \| null | Interpretive/curatorial strength. | `5` |

### 🔹 Computed scoring

| Field Name | Type | Description | Notes |
| --- | --- | --- | --- |
| `priority_score` | number \| null | Weighted score used for ranking. | Lower = higher priority |
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

Priority Score =
(10 − Impressionism Weight × 3)

* (10 − Modern/Contemporary Weight × 3)
* (5 − Historical Context Score × 2)
* (5 − Reputation Score)
* (5 − Collection Tier Score)
  − Dual Collection Bonus
  − Nearby Cluster Bonus

All inputs normalized to 5-point or 4-tier systems:

* Impressionist/Modern strengths: integer 0–5
  * 0 = None
  * 1 = Minor
  * 2 = Moderate
  * 3 = Strong
  * 4–5 = Flagship (reserved for truly exceptional holdings)
* Historical Context: 1 (low) to 5 (strong)
* Reputation: Local (1), Regional (2), National (3), International (4)
* Collection Tier: Small (1), Moderate (2), Strong (3), Flagship (4)
* Bonuses:

  * Dual Collection Bonus: –2 if both `impressionist_strength` and `modern_contemporary_strength` are ≥3
  * Cluster Bonus: –1 if 3+ museums in city

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
