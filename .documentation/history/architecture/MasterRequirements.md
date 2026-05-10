MuseumSpark: A Museum Travel Prioritization System

Master Requirements Document (MRD)
**Last updated:** 2026-03-14
**Version:** v3.1.T
**Owner:** Marlis Hazleton (Product Owner)
**Status:** Authoritative product specification - all architecture and implementation documents derive from this source
**Use Case:** Prioritize museum visits based on art collection relevance, historical context, curatorial authority, and travel efficiency.


SECTION 1: OBJECTIVE

To build a structured, sortable, and scalable dataset of museums across North America and beyond that enables informed travel planning based on personal interests, particularly in Impressionist and Modern/Contemporary art, with strong historical framing. The system must support ranking, filtering, and itinerary planning via a Priority Score and Outcome Tier assignment.


SECTION 2: DATASET SCOPE

A. Master Museum List

* Source: User-curated list (Walker Art Reciprocal Program)
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
5. Institution Type (locked set — see Section 9)
6. Primary Focus
7. City Tier

   * Major hub (Tier 1)
   * Medium city (Tier 2)
   * Small town (Tier 3)


SECTION 4: SCORING FIELDS (Art Museums Only)

These fields are used to compute Priority Score and Outcome Tier:

---

7. Impressionist / Post-Impressionist Strength (0–5)

Purpose: Measures the depth, authority, and scholarly importance of permanent Impressionist and Post-Impressionist holdings.
Core period: c. 1860s–1905. Core figures include Monet, Renoir, Degas, Pissarro, Morisot, Sisley, Cézanne, Gauguin, Van Gogh, Seurat, and closely affiliated circles.
What counts: Authentic Impressionist and Post-Impressionist works; American Impressionism only when explicitly treated as such.
What does NOT count: Modern works "in the spirit of" Impressionism; exhibition programming alone (that is ECA).

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

8. Modern / Contemporary Strength (0–5)

Purpose: Measures the depth, authority, and scholarly importance of permanent Modern and Contemporary art holdings.
Scope: Late Modern (roughly 1920s–1960s: Surrealism, Abstract Expressionism) and Contemporary (roughly 1970s–present: Conceptual, installation, video, socially engaged, postmodern, global movements).
What counts: Works within a modern or contemporary artistic framework; experimentation, abstraction, conceptual intent, or critique of tradition; permanent holdings by recognized artists, movements, or sustained themes.
What does NOT count: Exhibition programming alone (that is ECA); rotating shows without permanent holdings; decorative or commercial contemporary objects without curatorial intent.

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

9. Historical Art Traditions (HAT) Strength (0–5)

Purpose: Measures the depth, authority, and coherence of tradition-based artistic production — art grounded in sustained artistic traditions operating within established cultural, academic, workshop, ceremonial, courtly, or lineage-based systems.
Scope: Art defined by continuity of tradition rather than chronology alone. Includes painting, sculpture, decorative arts, textiles, ceremonial works, court art, and materially grounded visual traditions. May include non-Western canons, Indigenous lineage art, and workshop traditions when treated as art-historical traditions rather than ethnographic or anthropological material.
Critical sorting rule: When a collection aligns with a defined art movement, movement classification takes precedence. Works of the Impressionist/Post-Impressionist period belong in that category. Works defined by modernist rupture belong in Modern/Contemporary, not here.
What does NOT count: Objects presented primarily as historical artifacts without art-historical interpretation (those influence Historical Context, not HAT strength).

* 5 — Canon-Defining Collection
  The institution holds a tradition-based collection that is field-defining at the national or international level. Works are interpreted as part of an art-historical continuum and demonstrate unquestioned authority within a recognized tradition.

* 4 — Major Scholarly Collection
  Deep, high-quality tradition-based holdings with clear scholarly value. The collection advances understanding within its tradition through coherent scope and sustained curatorial engagement.

* 3 — Strong Regional or Thematic Collection
  Coherent, well-curated tradition-based holdings with recognized strength within a region, medium, or tradition. Holdings support credible exhibitions and interpretation.

* 2 — Modest or Supporting Collection
  Tradition-based works provide contextual value but lack depth, rarity, or sustained curatorial impact.

* 1 — Limited Collection Presence
  Small or inconsistent tradition-based holdings with minimal curatorial or scholarly relevance.

* 0 — No Meaningful HAT Holdings
  The institution does not maintain tradition-based works of significance.

---

10. Primary Art Focus

* Derived from the strongest of the three collection axes: Impressionist, Modern/Contemporary, or Historical Art Traditions
* String: "Impressionist", "Modern/Contemporary", or "Historical Art Traditions"

---

11. Historical Context Score (0–5)

Purpose: Measures the quality and depth of historical interpretation a museum presents — how clearly, rigorously, and insightfully it constructs historical understanding. Evaluates interpretive strength, not collection size, reputation, attendance, or institutional scale. Applies to art, science, cultural, or social history when interpretation meets rubric depth criteria.

* 5 — Canon-Defining Historical Interpretation
  The museum presents history with exceptional depth and rigor such that its interpretation defines or reshapes understanding of a major historical subject. Interpretation is grounded in exceptionally strong primary historical material, is multi-layered, analytical, and field-shaping. The institution functions as a reference point for historical understanding.
  **Note: A score of 5 may qualify a museum for Must-See status.**

* 4 — Deep, Integrated Historical Interpretation
  The museum presents history with substantial depth and coherence, integrating multiple layers of context into a well-structured historical narrative. Interpretation goes beyond explanation into analysis and synthesis. Supported by substantial and appropriate historical material.

* 3 — Intentional Historical Framing
  The museum presents history with clear intent and solid explanatory structure. Explains what happened and why it matters, but remains limited in depth or layering. Supported by adequate historical material.

* 2 — Descriptive or Place-Based Historical Presentation
  Interprets or preserves local history or culture with relevance primarily to the immediate community. Primarily descriptive or documentary; focuses on facts, chronology, or preservation with limited analytical depth.

* 1 — Minimal Historical Presence
  The museum includes limited or incidental historical content that does not meaningfully construct a historical narrative.

* 0 — No Historical Interpretation
  Institution is not historically oriented; history is absent or incidental.

---

12. Exhibitions & Curatorial Authority (ECA) (0–5)

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

13. Collection-Based Strength (0–5)

Purpose: Measures the depth, authority, and scholarly importance of a museum's permanent holdings across all relevant art categories. Art-first; does not evaluate popularity, attendance, branding, or reputation. Scores assigned based on the strongest applicable category or combination of categories.

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

14. Reputation Level

Reputation measures the structural scope of institutional recognition and role — not collection strength, interpretive quality, attendance, or media visibility.

Allowed evidence (must be structural): governance or funding beyond the local level; national or international touring exhibitions originated by the institution; formal designation with national or international institutional roles; participation in multi-state or international institutional networks.
Explicit exclusions: media praise or reviews; rankings, listicles, or travel guides; awards or popularity metrics.
Media guardrail: Media may never increase Reputation Level. Media may only confirm a level already supported by structural evidence.
Sovereign Jurisdiction Clause: Reputation for sovereign governmental cultural institutions (including federally recognized tribal nations) is evaluated based on jurisdictional authority, not land area.
Default rule: If recognition does not clearly extend beyond the local area → Local.

* International
  Sustained cross-border institutional role. Originating exhibitions/research/programs with ongoing international circulation; formal cross-national governance roles; leadership in multi-national institutional networks.

* National
  National-scale institutional role. National governance, funding, or formal designation; sustained record of multi-state exhibition/research reach; leadership in national institutional networks.

* Regional
  Institution functions as a recognized anchor across a broader region (multi-metro, multi-state, or culturally defined region). Regional status does not require influence beyond the defined region; the test is whether the institution functions as a recognized anchor within that region across multiple metropolitan areas or a cultural region.

* Supra-Local
  Institution operates meaningfully beyond its immediate locality (multi-city participation, statewide or cross-local governance/funding, originated programming with reach beyond one city), but does not constitute a recognized regional anchor.

* Local (default)
  Institutional recognition and operational role confined primarily to the immediate city or locality. In the absence of clear structural evidence meeting higher criteria, Reputation defaults to Local.

---

15. Collection Level

Collection Level classifies the documented scale and structural role of a museum's permanent holdings. Applies to all institution types, not art-only. Non-owned works may qualify only when the institution exercises exclusive, long-term custodial control and the installation functions as a singular destination asset inseparable from the museum's identity.

Allowed evidence (at least one required): published descriptions of permanent holdings; named collection divisions or departments; public collection catalogs or databases; institutional documentation clearly distinguishing permanent collections from exhibitions; university or municipal records describing owned collections.
Explicit exclusions: exhibition volume or ambition; media language; visitor numbers; building size or prominence; awards or rankings.
Default rule: If permanent holdings are undocumented or minimal → Small.

* Flagship (Strict Standard)
  Permanent holdings exhibit field-shaping depth or breadth. The collection functions as an active scholarly reference, supported by institutional capacity appropriate to research-grade holdings. The collection contains substantial primary evidence whose loss would materially reduce the field's accessible research base. If any condition is unmet, classify as Strong.

* Strong
  Permanent holdings are clearly documented and form a central institutional asset. The collection demonstrates coherent scope across artists, makers, periods, media, or themes. Holdings are used in sustained curatorial, interpretive, or research contexts. If any condition is unmet, the collection is not Strong.

* Moderate
  Permanent holdings are documented and identifiable as a discrete collection. The collection demonstrates some internal structure or focus, but limited depth or breadth. Holdings support interpretation or exhibitions in a sustained and recurring way. If any condition is unmet, the collection is not Moderate.

* Small (default / floor)
  Permanent holdings are minimal, fragmented, weakly documented, or incidental. The institution is exhibition-driven, or permanent holdings are secondary to programming. The collection does not sustain ongoing interpretation or institutional identity.

---

16. Time Needed

Visit duration categories calibrated to the fact that most museums are open approximately 7 hours per day. Time Needed is a planning dimension only and does not affect scoring, priority, or outcome tiers.

* Quick Stop (approximately 1–1.25 hours)
  Fits easily before or after other activities. Low fatigue, limited scope. Visitor can meaningfully see the full offering in one pass.

* Half Day (approximately 2.5–3 hours)
  Roughly half of a standard museum day. Primary visit block without requiring pacing. Moderate depth and breadth.

* Most of the Day (approximately 4–5 hours)
  Dominates the day's schedule. Requires pacing and selective viewing. Broad or dense collections with multiple layers.

* All Day (approximately 6–7 hours)
  Plausibly fills an open-to-close visit. Requires breaks and prioritization. Flagship-scale or exceptionally dense institutions.

---

17. Nearby Museum Count

* Integer count of other museums in the same city from the master list
* Excludes the current row itself


SECTION 5: SCORING FORMULA (v3.1.T)

Priority Score (lower = better). All inputs derive from the fields defined in Section 4.

**Step 1: Collection-Based PAS (Primary Art Strength)**
```
Collection-Based PAS = MAX(Impressionist Strength, Modern/Contemporary Strength, HAT Strength)
```
Only the single strongest applicable art category is used; strengths are never summed.

**Step 2: Effective PAS**
```
Effective PAS = MAX(Collection-Based PAS, ECA)
```
ECA may elevate PAS; it does not add to it.

**Step 3: Dual-Strength Bonus (All-or-Nothing)**
```
Dual-Strength Bonus = -2  if Impressionist Strength >= 3 AND Modern/Contemporary Strength >= 3
                    =  0  otherwise
```
HAT Strength does not qualify for this bonus.

**Step 4: Reputation Penalty**
```
International  = +0
National       = +0
Regional       = +2
Supra-Local    = +3
Local          = +4
```

**Step 5: Collection Penalty**
```
Flagship = +0
Strong   = +0
Moderate = +2
Small    = +4
```

**Step 6: Priority Score**
```
Priority Score = MAX(1,
    (6 - Effective PAS) × 2
  + (6 - Historical Context Score)
  + Reputation Penalty
  + Collection Penalty
  + Dual-Strength Bonus
)
```

**Score Interpretation:**
* Lower scores = higher priority
* Score has a floor of 1
* Museums with Historical Context = 5 are flagged as Must-See candidates
* Museums with Collection-Based PAS = 5 (not elevated solely by ECA) are Must-See candidates


SECTION 6: OUTCOME TIERS

Outcome tiers reflect predicted visitor routing behavior and institutional merit (ordered highest to lowest):

**1. Must-See**
Assigned if either is true:
* Collection-Based PAS = 5 (not elevated solely by ECA), OR
* Historical Context = 5

**2. High Priority**
Assigned if ANY is true (and Must-See is not met):
* Priority Score ≤ 9
* Flagship Collection + Primary Art Strength = 4
* ECA ≥ 4
* Historical Context = 4 with National or International reputation

Guardrail: Priority Score ≤ 9 is sufficient on its own to assign High Priority, regardless of reputation scope or institution type.

**3. Regionally Important**
Assigned if ALL are true (and Must-See / High Priority are not met):
* Priority Score between 10–15 (inclusive), AND
* Reputation = Regional, AND
* At least one of:
  - A) Effective PAS = 3 or 4 and functions as a primary regional art reference
  - B) Historical Context = 3 or 4 and presents a subject at regional reference depth

**4. Detour**
Assigned to museums for which a culturally motivated traveler would plausibly alter their route.
Qualification requires BOTH:
* Specialization or Experiential Singularity: qualifies as one of:
  - You Won't See This Again — experience defined by specific combination of place, format, and presentation such that no other museum meaningfully substitutes
  - Specialized Art Site — mission and permanent holdings narrowly focused on a single artist, movement, medium, or tradition; does not function as a general regional art reference
  - Specialized Cultural Site — mission narrowly focused on a specific culture, heritage, community, or non-art domain where subject-matter depth is the primary value
* AND Institutional Strength Signal: at least one of:
  - Effective PAS ≥ 3
  - Historical Context ≥ 3

Critical Rule: Specialization alone is insufficient for Detour; institutional strength must also be present.

**5. Consider**
Museums worth visiting when already in the area but unlikely to alter travel routing. Proximity-dependent value.
Subtypes (record in Additional Labels):
* Generalized Collection Museum — broad or multi-category permanent collection supporting credible visitation without sufficient gravity to influence travel plans
* Locally Historic — institution preserves or interprets history foundational to the immediate area; significance is primarily place-bound
* Quirky / Memorable — notably eccentric, unusual, idiosyncratic, or novelty-forward in a way that makes the experience memorable
* Kunsthalle — a non-collecting exhibition institution whose primary function is presentation of curated temporary exhibitions rather than stewardship of a permanent collection

**6. Background**
Assigned to institutions with limited travel gravity. May provide local value but typically do not influence visitor routing decisions. Background is the default classification for community-oriented institutions unless supporting signals are present.

**Note:** Museums assigned to Detour or Consider must have their corresponding subtype recorded in the Additional Labels field.


SECTION 7: LOCKED INSTITUTION TYPES

The following institution types are locked (no additions without a versioned amendment):

* Art Museum
* History Museum
* Cultural Museum
* Academic Museum
* Hybrid Museum
* Historic Site / House Museum
* Science / Natural History Museum
* Specialty / Industry Museum
* Arboretum / Botanical / Outdoor Cultural Site
* Exhibition Center / Kunsthalle
* Archive / Research Institution
* Children's / Family Museum
* Kunsthalle Museum (added v3.1.T)
* Community Art Center (added v3.1.T)

Existing Art Museums and Hybrid Museums should be evaluated for potential reclassification under Community Art Center where appropriate.


SECTION 8: NOTES FIELD — WRITING STANDARDS

Purpose: Notes describe what a visitor encounters at the museum. Factual, neutral, and written to support trip planning and contextual understanding.

Requirements:
* Length: 2–4 sentences
* Tone: neutral, descriptive, non-promotional
* Subject-anchored, not institution-led (meaning should remain clear if the museum's name is replaced with "this museum")
* Describe observable reality: objects and materials, spatial arrangement, operational use or display conditions

Prohibited:
* Interpretation, theory, or curatorial rationale
* Statements of importance, reputation, or intent
* Promotional or prestige-signaling language
* Repeated syntactic frames across entries (e.g., "The collection emphasizes…", "Interpretation emphasizes…")
* Full sentences in Primary Focus

Architecture, site, or exhibition conditions may be referenced only when integral to how material is encountered. Do not imply permanent holdings where none exist.


SECTION 9: AUDIT TRACKER FIELD

The Audit Tracker field records the provenance and outcome of the most recent audit applied to a museum entry. It is informational only and does not affect scoring, Priority Score, Outcome Tier assignment, or label eligibility.

Format: Version | Date | Outcome Code

Outcome Codes:
* CH — Changed
* NC — No Change

If the Audit Tracker field is blank or references an earlier version, the entry may still be used but has not been audited under the current Documentation and Rubrics.


SECTION 10: IMPLEMENTATION PHASES

Phase 1 — Master Dataset Backbone

* Normalize and populate all fields for all museums:
  Country, State, City, Museum Name, Institution Type, City Tier, Reputation, Time Needed, Nearby Count

Phase 2 — Scoring (Art Museums Only)

* Apply expert scoring to fine art museums and major encyclopedic or university art museums
* Score all art-specific fields:
  * Impressionist Strength (0–5)
  * Modern/Contemporary Strength (0–5)
  * Historical Art Traditions Strength (0–5)
  * Historical Context Score (0–5)
  * Exhibitions & Curatorial Authority (0–5)
  * Collection-Based Strength (0–5)
  * Reputation Level (International / National / Regional / Supra-Local / Local)
  * Collection Level (Flagship / Strong / Moderate / Small)
* Leave local history, science, and specialty museums unscored

Phase 3 — Priority Score & Outcome Tier Computation (Deterministic)

* Compute Collection-Based PAS, Effective PAS, Priority Score, and Outcome Tier
* Assign Additional Labels for Detour and Consider tiers
* Record Audit Tracker on each row

Phase 4 — Regional Rollout

1. Illinois / Midwest anchors
2. Northeast cluster (MA, NY, PA, CT)
3. California
4. Remaining U.S. states
5. Canada, Mexico, Bermuda

Each phase includes a review checkpoint for score validation.


SECTION 11: DATASET USAGE

Primary use cases:
* Trip planning by filtering museums by city and sorting by Priority Score
* Itinerary design by clustering nearby museums
* Identifying high-impact art stops in unfamiliar cities
* Ignoring low-priority visits without manual screening
* Identifying Must-See museums based on Historical Context = 5 or Collection-Based PAS = 5
* Discovering curatorially significant institutions via ECA scores
* Routing decisions using Outcome Tier (Must-See through Background)

VERSION HISTORY

| Version | Key Change |
|---------|-----------|
| v1.0–v1.6H | Baseline system formation |
| v1.7 | Traditional/Pre-Modern art scope clarification (Indigenous/non-Western inclusion) |
| v1.8 | High Priority expansion: ECA ≥ 4 qualifies |
| v1.9 | Historical Context rubric rewritten to interpretive depth |
| v2.0 | Supra-Local reputation tier added; Collection Level definitions formalized; Background as default outcome |
| v2.0.R | Regionally Important score range adjusted to 10–15 |
| v2.0.RC | Collection Level applicability clarified for all institution types |
| v2.1 | Flagship Collection definition tightened |
| v2.1.A | HAT taxonomy clarified; replaced Traditional/Pre-Modern with Historical Art Traditions |
| v1.2.AS | Specialized Art Site definition clarified (subject-based) |
| v2.2 | Sovereign Jurisdiction reputation clause added |
| v2.2.R | Regional reputation clarified as anchor within region |
| v3.0 | Behavioral Gravity Framework: Detour tier introduced; Consider/Background redefined |
| v3.1 | Kunsthalle label added for Consider-tier non-collecting institutions |
| v3.1.C | Functional Permanent Collection Clause: non-owned works may qualify under strict custodial criteria |
| v3.1.T | Institution Type Expansion: Kunsthalle Museum and Community Art Center added |
