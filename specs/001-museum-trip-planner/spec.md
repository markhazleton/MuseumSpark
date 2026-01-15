# Feature Specification: Museum Travel Prioritization System — Phase 1

**Feature Branch**: `001-museum-trip-planner` ✅ **MERGED TO MAIN**
**Created**: 2026-01-15
**Last updated**: 2026-01-15
**Status**: ✅ **PHASE 1 COMPLETE** - Ready for Phase 2
**Owner**: Mark Hazleton
**Master Requirements Document (MRD)**: Aligned with MRD v1.0
**Input**: Walker Art Reciprocal Program source data

---

## ✅ Phase 1 Completion Summary

**Completed**: January 15, 2026  
**Duration**: 2 hours 29 minutes (automated enrichment)

### Achievements
- ✅ **All 52 states enriched**: 1,269 museums processed with official website scraping
- ✅ **Address extraction**: 455 street addresses (36% improvement)
- ✅ **Postal codes**: 630 postal codes extracted (99% improvement)
- ✅ **City data**: 114 cities enriched (74% improvement)
- ✅ **City tier**: 100% computed for all museums
- ✅ **Time estimates**: 100% computed for all museums
- ✅ **Validation site**: React app created with Browse, Detail, Progress, Home, and Roadmap pages
- ✅ **GitHub workflows**: GitHub Pages deployment workflows configured
- ✅ **Documentation**: Comprehensive guides for Pre-MRD Phase enrichment

### Ready for Phase 2
Phase 1 established the foundation using free/open data sources. The dataset is now ready for:
- **Phase 2**: LLM-based enrichment (museum_type, primary_domain, status, reputation, collection_tier, notes, confidence)
- **Phase 3**: GitHub Pages deployment and validation site launch
- **Phase 4**: Trip planning features and user interaction

---

## 0. Phase Definition (Strictly Scoped)

### ✅ Phase 1 Complete - Objective Achieved
Established the **Open Data Public Records Baseline**. This phase focused entirely on acquiring, structuring, and verifying the museum dataset using free and public sources.

**Completion Status**: All objectives met and merged to main branch.

### Phase 1 Scope - ✅ COMPLETED

1.  ✅ **Data Acquisition**: Migrated the Walker Art Reciprocal museum roster into the `data/states/*.json` schema (1,269 museums across 52 states).
2.  ✅ **Open Data Enrichment**: Used automated scripts to fetch data from:
    *   **Official Websites**: Full address extraction (street, city, postal code) via 10-page website scraping
    *   **OpenStreetMap Nominatim**: Geocoding for coordinates
    *   **Wikidata**: Museum entity lookup and basic metadata
    *   **Wikipedia**: City populations for city tier computation
3.  ✅ **Static Review Site**: A React application created with:
    *   Browse and search functionality
    *   Detail pages for individual museums
    *   Progress Dashboard showing enrichment status
    *   Home page with project overview
    *   Roadmap page showing phased approach
4.  ✅ **Completion Criteria Met**:
    *   100% of Walker Art Reciprocal museums exist in the dataset
    *   Enrichment script populated 455 addresses, 630 postal codes, 114 cities
    *   100% of museums have city_tier and time_needed computed
    *   Static site ready for GitHub Pages deployment
    *   Branch merged to `main` with comprehensive commit

### Next Steps - Phase 2
*   **LLM-based Enrichment**: Use Claude/GPT-4 to populate remaining MRD fields:
    *   museum_type (1,262 museums)
    *   primary_domain (1,262 museums)  
    *   status (1,262 museums)
    *   reputation (1,252 museums)
    *   collection_tier (1,262 museums)
    *   notes (1,262 museums)
    *   confidence (1,262 museums)
*   **Phase 3**: GitHub Pages deployment and site launch
*   **Phase 4**: Trip planning features, user accounts, backend API

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

### ✅ All Criteria Met - Phase 1 Complete

1.  ✅ **Dataset Integrity**: All JSON files pass schema validation (52 states, 1,269 museums).
2.  ✅ **Enrichment**: `enrich-open-data.py` ran successfully across all states:
    - 455 street addresses extracted
    - 630 postal codes extracted  
    - 114 cities enriched
    - 100% city_tier computed
    - 100% time_needed computed
    - Comprehensive error handling and caching implemented
3.  ✅ **Site Functionality**: All pages created and functional:
    - Browse page with filtering
    - Detail pages with full museum data
    - Progress page with enrichment dashboard
    - Home page with project overview
    - Roadmap page with phased approach
4.  ✅ **Documentation**: Complete documentation created:
    - Pre-MRD Phase guides
    - AI/LLM enrichment plans
    - GitHub Pages deployment workflows
    - Batch processing scripts

### Phase 1 Deliverables - All Merged to Main

**Scripts**:
- `enrich-open-data.py` - Core enrichment engine with website scraping
- `run-full-enrichment-phase.ps1` - Batch processing for all states
- `build-index.py` - Index aggregation with MRD field computation
- `build-progress.py` - Progress tracking and reporting
- `build-missing-report.py` - Missing data analysis

**Site** (ready for deployment):
- React + Vite + TypeScript application
- GitHub Pages workflows configured
- All pages implemented and tested

**Data**:
- 52 state files enriched with open data
- all-museums.json index with 1,269 museums
- progress.json and missing-report.json analytics

---

## Next Phase Focus: GitHub Pages Deployment

With Phase 1 complete, the immediate priority is:
1. **Deploy validation site to GitHub Pages**
2. **Verify site functionality in production**
3. **Begin Phase 2 LLM enrichment planning**
