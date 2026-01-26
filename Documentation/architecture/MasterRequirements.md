MuseumSpark: A Museum Travel Prioritization System

Master Requirements Document (MRD)
**Last updated:** 2026-01-26  
**Owner:** Marlis Hazleton (Product Owner)  
**Status:** Authoritative product specification - all architecture and implementation documents derive from this source  
**Use Case:** Prioritize museum visits based on art collection relevance, historical context, curatorial authority, and travel efficiency.


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

---

7. Impressionist Strength (0–5)

Purpose: Measures the depth, authority, and scholarly importance of a museum's permanent Impressionist holdings.

* 5 — Canon-Defining Collection
  The museum holds Impressionist works that are field-defining at the national or international level. Holdings contain canonical works (not merely representative examples), and the institution functions as a reference point for Impressionist scholarship and curation.

* 4 — Major Scholarly Collection
  Deep, high-quality Impressionist holdings with clear scholarly value and national significance. Includes important works and artists, supports sustained research and serious exhibitions.

* 3 — Strong Regional or Thematic Collection
  Coherent, well-curated Impressionist holdings with recognized strength within a region or theme. Supports credible exhibitions but does not substantially influence national scholarship.

* 2 — Modest or Supporting Collection
  Impressionist works provide contextual or educational value but lack depth, rarity, or sustained curatorial impact. Works are largely illustrative or supplementary.

* 1 — Limited Collection Presence
  Small or inconsistent Impressionist holdings with minimal curatorial or scholarly relevance.

* 0 — No Meaningful Impressionist Holdings
  The institution does not maintain Impressionist works of significance.

---

8. Modern/Contemporary Strength (0–5)

Purpose: Measures the depth, authority, and scholarly importance of a museum's permanent Modern and Contemporary art holdings.

* 5 — Canon-Defining Collection
  The museum holds Modern/Contemporary works that are field-defining at the national or international level. Holdings contain canonical works, and the institution functions as a reference point for scholarship and curation.

* 4 — Major Scholarly Collection
  Deep, high-quality Modern/Contemporary holdings with clear scholarly value and national significance. Includes important works and artists, supports sustained research and serious exhibitions.

* 3 — Strong Regional or Thematic Collection
  Coherent, well-curated Modern/Contemporary holdings with recognized strength within a region or theme. Supports credible exhibitions but does not substantially influence national scholarship.

* 2 — Modest or Supporting Collection
  Modern/Contemporary works provide contextual or educational value but lack depth, rarity, or sustained curatorial impact. Works are largely illustrative or supplementary.

* 1 — Limited Collection Presence
  Small or inconsistent Modern/Contemporary holdings with minimal curatorial or scholarly relevance.

* 0 — No Meaningful Modern/Contemporary Holdings
  The institution does not maintain Modern/Contemporary works of significance.

---

9. Primary Art Focus

* String: "Impressionist" or "Modern/Contemporary"
* Chosen as the stronger of the two strengths

---

10. Historical Context Score (0–5)

Purpose: Measures how essential a museum is to understanding art history, cultural history, or a specific historical narrative, independent of collection size, reputation, or attendance. This score evaluates contextual importance, not prestige.

* 5 — Canon-Level Historical Importance
  The museum provides essential, field-defining historical context for understanding a major movement, culture, or historical subject. The institution is a foundational reference point for the subject it interprets.
  **Note: A score of 5 may qualify a museum for Must-See status.**

* 4 — Nationally Significant Context
  Provides strong historical framing for a major movement, region, or cultural narrative with relevance beyond the local level.

* 3 — Strong Regional Context
  Anchors the history of a region, city, or cultural community in a meaningful and sustained way.

* 2 — Local Context
  Interprets or preserves local history or culture with relevance primarily to the immediate community.

* 1 — Limited Context
  Includes historical interpretation, but it is narrow, secondary, or not a core institutional strength.

* 0 — No Contextual Framing
  Institution is not historically oriented; history is absent or incidental.

---

11. Exhibitions & Curatorial Authority (ECA) (0–5)

Purpose: Measures curatorial influence that exists outside permanent collections, including exhibition authorship, commissioning power, and intellectual leadership. ECA evaluates programmatic authority only and does not assess permanent holdings.

* 5 — Field-Shaping Curatorial Authority
  Produces exhibitions, research, or commissions that shape discourse nationally or internationally.

* 4 — Nationally Recognized Curatorial Program
  Sustained record of original, influential exhibitions with national reach.

* 3 — Strong Regional Curatorial Program
  Original and respected exhibitions with regional influence.

* 2 — Competent Exhibition Programming
  Professionally executed but largely derivative or touring exhibitions.

* 1 — Minimal Curatorial Authority
  Limited scope or intellectual contribution.

* 0 — No Curatorial Program of Note
  No meaningful exhibition programming or curatorial presence.

---

12. Collection-Based Strength (0–5)

Purpose: Measures the depth, authority, and scholarly importance of a museum's permanent holdings across all relevant art categories. This rubric is art-first and does not evaluate popularity, attendance, branding, or reputation. Scores are assigned based on the strongest applicable category or combination of categories.

* 5 — Canon-Defining Collection
  The museum holds a collection that is field-defining at the national or international level. Its holdings contain canonical works (not merely representative examples), and the institution functions as a reference point for scholarship, curation, and major exhibitions. The collection demonstrates either encyclopedic breadth across major periods and regions or unquestioned authority within a specific domain. Influence is sustained over decades and independent of temporary programming.

* 4 — Major Scholarly Collection
  The museum holds a deep, high-quality collection with clear scholarly value and national significance. The collection includes important works and artists, supports sustained research and serious exhibitions, and meaningfully advances understanding of its field. However, it does not define the canon itself or function as a primary reference institution across the discipline.

* 3 — Strong Regional or Thematic Collection
  The museum maintains a coherent, well-curated collection with recognized strength within a region, medium, movement, or theme. Holdings support credible exhibitions and interpretation but do not substantially influence national scholarship.

* 2 — Modest or Supporting Collection
  The collection provides contextual or educational value but lacks depth, rarity, or sustained curatorial impact. Works are largely illustrative or supplementary.

* 1 — Limited Collection Presence
  The museum holds a small or inconsistent permanent collection with minimal curatorial or scholarly relevance.

* 0 — No Meaningful Permanent Collection
  The institution does not maintain a permanent collection of significance (e.g., exhibition-only spaces, archives without object collections).

---

13. Reputation Tier

* International = 0
* National = 1
* Regional = 2
* Local = 3

---

14. Time Needed

* Quick stop (<1 hr)
* Half day
* Full day

---

15. Nearby Museum Count

* Integer count of other museums in the same city from the master list
* Excludes the current row itself



SECTION 5: SCORING FORMULA

Priority Score (lower = better):

**Primary Art Strength** = max(Impressionist Strength, Modern/Contemporary Strength)

**Dual-Strength Bonus:**
If Impressionist Strength ≥ 4 AND Modern/Contemporary Strength ≥ 4 → subtract 2 from final score

**ECA Bonus:**
If ECA ≥ 4 → subtract 1 from final score

**Formula:**
```
Priority Score =
  (5 – Primary Art Strength) × 3
+ (5 – Historical Context Score) × 2
+ (5 – Collection-Based Strength) × 2
+ Reputation Tier
– Dual-Strength Bonus (if applicable)
– ECA Bonus (if applicable)
```

**Score Interpretation:**
* Lower scores indicate higher priority museums
* Museums with Historical Context = 5 should be flagged as potential "Must-See" candidates
* Museums with ECA = 5 merit consideration even if collection scores are lower



SECTION 6: FIELD: Notes (Optional, Human-Written)

Used to capture:

* Signature artists or collections (e.g., Monet, Rothko, Hopper)
* Historical significance (e.g., "first museum west of Mississippi")
* Special exhibitions or strengths
* Travel-specific context
* Must-See designation rationale (for Historical Context = 5)



SECTION 7: IMPLEMENTATION PHASES

Phase 1 — Master Dataset Backbone

* Normalize and populate all fields for all museums:

  * Country, State, City, Museum Name, Museum Type, City Tier, Reputation, Time Needed, Nearby Count

Phase 2 — Scoring (Art Museums Only)

* Apply expert scoring to:

  * Fine art museums
  * Major encyclopedic or university art museums
* Score all six art-specific fields:
  * Impressionist Strength (0–5)
  * Modern/Contemporary Strength (0–5)
  * Historical Context Score (0–5)
  * Exhibitions & Curatorial Authority (0–5)
  * Collection-Based Strength (0–5)
  * Reputation Tier (0–3)
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
* Identifying Must-See museums based on Historical Context = 5
* Discovering curatorially significant institutions via ECA scores
