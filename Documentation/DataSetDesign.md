Here is a product brief that outlines the full scope, field definitions, methodology, and design principles used to construct the Museum Prioritization Dataset.

—

📘 Museum Prioritization Dataset
Product Brief & Methodology Specification

Purpose
This dataset was developed to support intelligent travel planning, prioritization, and analysis of museums across the United States (and selected international sites), with an emphasis on visual art museums. It allows users to filter, sort, and evaluate institutions based on collection relevance, cultural significance, and visit practicality.

Scope

* Full normalization of every museum on a user-supplied list (~2,000+ museums)
* Prioritization scoring applied to relevant visual art museums only (e.g., fine art, modern/contemporary, encyclopedic, university museums)
* Geographic focus: U.S. primary, Canada and international secondary
* Modular structure designed to accommodate future phases (e.g., deeper international scoring, education/travel integrations)

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

Scoring applies only to qualifying art museums. Local history or niche-interest museums are excluded from scoring but retained in the dataset for planning purposes.

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

1. Museum list was parsed into geographic segments by state and city for accuracy
2. Core fields (country, state, city, name, type) were normalized to eliminate duplicates or formatting inconsistencies
3. Reputational tiers were assigned based on national prominence, institutional affiliations, and curatorial leadership
4. Collection tier and art period strength were evaluated based on public collection data, academic references, and institutional publications
5. Historical context scores were assigned based on the degree of interpretive material, exhibition design, and curatorial framing
6. Travel logistics (e.g., time needed, cluster size) were assessed from official websites, Google Maps proximity, and third-party travel sites
7. All data was manually verified and cross-validated for consistency
8. Hyperlinks were added to official museum websites for instant lookup

—

🧩 Output Format

Available as a clean, structured spreadsheet (CSV or Excel) with:

* Fully filterable columns
* Sortable priority scores
* Hyperlinked museum names
* Ready for itinerary planning, analysis, or expansion

—

Let me know if you'd like this delivered as a downloadable spreadsheet, API schema, or embedded database model.
