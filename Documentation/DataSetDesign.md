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

🔹 Core Identity

| Field Name       | Description                                            | Example                  |
| ---------------- | ------------------------------------------------------ | ------------------------ |
| Country          | ISO-standardized country                               | USA                      |
| State / Province | Full U.S. state name or Canadian province              | California               |
| City             | City in which the museum is located                    | Chicago                  |
| Museum Name      | Official name (hyperlinked to website where available) | Art Institute of Chicago |
| Museum Type      | Primary type (Art, History, Science, etc.)             | Art                      |

🔹 Travel Planning Metadata

| Field Name          | Description                                                             | Example  |
| ------------------- | ----------------------------------------------------------------------- | -------- |
| Time Needed         | Estimated visitor time commitment (Quick stop <1hr, Half day, Full day) | Full day |
| Nearby Museum Count | Count of other museums in the same city from user list                  | 3        |

🔹 Reputation & Scope

| Field Name      | Description                             | Values                                      |
| --------------- | --------------------------------------- | ------------------------------------------- |
| Reputation      | Cultural and national significance tier | Local / Regional / National / International |
| Collection Tier | Relative size and depth of collection   | Small / Moderate / Strong / Flagship        |

🔹 Collection Strength & Focus

| Field Name                   | Description                                                        | Example                                     |
| ---------------------------- | ------------------------------------------------------------------ | ------------------------------------------- |
| Impressionism Strength       | Depth of Impressionist holdings                                    | None / Minor / Moderate / Strong / Flagship |
| Contemporary/Modern Strength | Depth of modern and post-1950s collections                         | Strong                                      |
| Primary Art Focus            | Dominant art historical strength                                   | Impressionism / Modern / Classical / Mixed  |
| Historical Context Score     | Curatorial emphasis on historical interpretation and context (1–5) | 4                                           |

🔹 Computed Scoring

| Field Name     | Description                             | Notes                   |
| -------------- | --------------------------------------- | ----------------------- |
| Priority Score | Weighted score used for ranking museums | Lower = higher priority |

🔹 Notes

| Field Name | Description                                                                         |
| ---------- | ----------------------------------------------------------------------------------- |
| Notes      | Freeform field for travel tips, highlights, or context not captured in other fields |

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

* Impressionism/Modern Strength: None (0) to Flagship (5)
* Historical Context: 1 (low) to 5 (strong)
* Reputation: Local (1), Regional (2), National (3), International (4)
* Collection Tier: Small (1), Moderate (2), Strong (3), Flagship (4)
* Bonuses:

  * Dual Collection Bonus: –2 if both Impressionist and Modern scores ≥3
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
