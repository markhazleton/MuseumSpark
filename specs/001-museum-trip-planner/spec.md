# Feature Specification: Museum Travel Prioritization System — Phase 1

**Feature Branch**: `001-museum-trip-planner`
**Created**: 2026-01-15
**Last updated**: 2026-01-15
**Status**: In Progress
**Owner**: Mark Hazleton
**Master Requirements Document (MRD)**: Aligned with MRD v1.0
**Input**: Walker Art Reciprocal Program source data

## 0. Phase Definition (Strictly Scoped)

### Objective
Establish the **Open Data Public Records Baseline**. This phase focuses entirely on acquiring, structuring, and verifying the museum dataset using free and public sources, and providing a static review site for verification.

All requirements for AI/LLM scoring, user accounts, trip planning, and backend services are **Out of Scope** for this document and will be handled in future phases.

### Phase 1 Scope (This Spec)

1.  **Data Acquisition**: Migrate the Walker Art Reciprocal museum roster into the `data/states/*.json` schema.
2.  **Open Data Enrichment**: Use automated scripts (`enrich-open-data.py`) to fetch data from:
    *   **Wikidata**: Coordinates, Official Websites, Collection Size (infer Collection Tier), Sitelinks (infer Reputation).
    *   **Wikipedia**: City populations (infer City Tier).
    *   **IMLS/US Museums**: Structural data (Address, Type).
3.  **Static Review Site**: A React application hosted on GitHub Pages to:
    *   Browse and search the dataset.
    *   Review "Proprietary Scores" (Reputation, Collection, City Tier) inferred from open data.
    *   Visualize dataset completeness (Progress Dashboard).
4.  **Completion Criteria**:
    *   100% of Walker Art Reciprocal museums exist in the dataset.
    *   Enrichment script successfully populates >50% of addresses and coordinates.
    *   Static site is deployed and accessible on GitHub Pages.
    *   Pull Request merged to `main`.

### Out of Scope (Phase 1)
*   Phase 2: AI/LLM Enrichment (Claude/OpenAI scoring).
*   Phase 3: Expert Verification & User Reviews.
*   Phase 4: Accounts, Backend API, Itinerary Planning, Mobile App.

---

## Technical Implementation

### Data Pipeline
*   **Source of Truth**: `data/states/*.json` files.
*   **Indexing**: `scripts/build-index.py` compiles state files into `data/index/all-museums.json` for the frontend.
*   **Validation**: `scripts/validate-json.py` enforces `data/schema/museum.schema.json`.
*   **Enrichment**:
    *   `scripts/enrich-open-data.py`: The primary engine for Phase 1.
    *   **Logic**:
        *   `City Tier`: Based on fixed list of "Major Hubs" + Population > 150k (Tier 2) / < 150k (Tier 3).
        *   `Reputation`: Inferred from Wikidata Sitelinks count (e.g., >50 links = International).
        *   `Collection Tier`: Inferred from Wikidata "collection size" property or manual heuristics.

### Static Site (Review Tool)
*   **Stack**: React, Vite, Tailwind CSS.
*   **Hosting**: GitHub Pages (docs/ or gh-pages branch).
*   **Key Pages**:
    *   `Home`: Project overview.
    *   `Browse`: Grid view of museums with filters for all enriched fields.
    *   `Detail`: Detailed view of a single museum showing raw and enriched data.
    *   `Progress`: Dashboard showing % of "Full" vs "Placeholder" records per state.
    *   `Roadmap`: Static view of the project phases.

---

## User Scenarios

### 1. The Data Reviewer
**As a** stakeholder,
**I want to** browse the list of museums by state and see which ones are "Full" records,
**So that** I can verify the effectiveness of the automated enrichment scripts.

### 2. The Traveler (Read-Only)
**As a** user,
**I want to** search for museums in "Chicago" and see their "City Tier" and inferred "Reputation",
**So that** I can get a rough idea of the major cultural institutions before the full AI scoring is available.

---

## Acceptance Criteria

1.  **Dataset Integrity**: All JSON files pass schema validation.
2.  **Enrichment**: `enrich-open-data.py` runs without errors and produces a diff of enriched fields.
3.  **Site Functionality**: The "Browse", "Detail", and "Progress" pages function as described in User Scenarios.
4.  **Documentation**: The `Roadmap` page on the site accurately reflects the 4-phase plan.
