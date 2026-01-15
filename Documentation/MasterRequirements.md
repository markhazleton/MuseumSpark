MuseumSpark: A Museum Travel Prioritization System:

Master Requirements Document (MRD)
Owner: Marlis Hazleton
Use Case: Prioritize museum visits based on art collection relevance, historical context, and travel efficiency.


SECTION 1: OBJECTIVE

To build a structured, sortable, and scalable dataset of museums across North America and beyond that enables informed travel planning based on personal interests, particularly in Impressionist and Modern/Contemporary art, with strong historical framing. The system must support ranking, filtering, and itinerary planning via a Priority Score.


SECTION 2: DATASET SCOPE

A. Master Museum List

* Source: User-curated list
* Geography: United States (Phase 1), Canada/Bermuda/Mexico (Phase 2)
* Type: Art museums prioritized, but all listed institutions included

B. Museum Inclusion Policy

* All museums are included in the dataset backbone
* Only relevant art museums (fine art, encyclopedic, university) are scored for prioritization
* Non-art museums remain in the dataset unscored to support city-level planning

 

SECTION 3: DATA MODEL

The dataset will include the following columns:

1. Country
2. State / Province
3. City
4. Museum Name
5. Museum Type

   * e.g., Fine Art, Contemporary Art, University Museum, History Museum, Cultural Center
6. City Tier

   * Major hub (Tier 1)
   * Medium city (Tier 2)
   * Small town (Tier 3)

 

SECTION 4: SCORING FIELDS (Art Museums Only)

These fields are used to compute Priority Score:

7. Impressionist Strength (1–5)

   * 5 = Flagship collection (major holdings, permanent galleries)
   * 4 = Strong collection
   * 3 = Moderate representation
   * 2 = Minor works only
   * 1 = None

8. Modern/Contemporary Strength (1–5)

   * Same scoring scale as above

9. Primary Art Focus

   * String: “Impressionist” or “Modern/Contemporary”
   * Chosen as the stronger of the two strengths

10. Historical Context Score (1–5)

* 5 = Strong narrative, chronology, interpretive galleries
* 3 = Inconsistent or surface-level context
* 1 = Minimal or absent historical framing

11. Reputation Tier

* International = 0
* National = 1
* Regional = 2
* Local = 3

12. Collection Tier

* Flagship = 0
* Strong = 1
* Moderate = 2
* Small = 3

13. Time Needed

* Quick stop (<1 hr)
* Half day
* Full day

14. Nearby Museum Count

* Integer count of other museums in the same city from the master list
* Excludes the current row itself

 

SECTION 5: SCORING FORMULA

Priority Score (lower = better):

Primary Art Strength = max(Impressionist Strength, Modern/Contemporary Strength)

Dual-Strength Bonus:
If Impressionist Strength ≥ 4 and Modern/Contemporary Strength ≥ 4 → subtract 2 from final score

Formula:
Priority Score =
(6 – Primary Art Strength) × 3

* (6 – Historical Context Score) × 2
* Reputation Penalty
* Collection Penalty
  – Dual Strength Bonus (if applicable)

 

SECTION 6: FIELD: Notes (Optional, Human-Written)

Used to capture:

* Signature artists or collections (e.g., Monet, Rothko, Hopper)
* Historical significance (e.g., “first museum west of Mississippi”)
* Special exhibitions or strengths
* Travel-specific context

 

SECTION 7: IMPLEMENTATION PHASES

Phase 1 — Master Dataset Backbone

* Normalize and populate all fields for all museums:

  * Country, State, City, Museum Name, Museum Type, City Tier, Reputation, Collection, Time Needed, Nearby Count

Phase 2 — Scoring (Art Museums Only)

* Apply expert scoring to:

  * Fine art museums
  * Major encyclopedic or university art museums
* Leave local history, science, and specialty museums unscored

Phase 3 — Regional Rollout

1. Illinois / Midwest anchors
2. Northeast cluster (MA, NY, PA, CT)
3. California
4. Remaining U.S. states
5. Canada, Mexico, Bermuda

Each phase includes a review checkpoint for score validation.

SECTION 8: DATASET USAGE

Primary use cases:

* Trip planning by filtering museums by city and sorting by Priority Score
* Itinerary design by clustering nearby museums
* Identifying high-impact art stops in unfamiliar cities
* Ignoring low-priority visits without manual screening
 
