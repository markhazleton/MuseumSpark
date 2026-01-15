# MuseumSpark Documentation

This folder is the canonical documentation set for MuseumSpark.

MuseumSpark’s purpose is to **rank and document every museum in the Walker Art Reciprocal Program**, using the extracted seed roster in `data/index/walker-reciprocal.csv` and enriching it into complete museum records.

## Dataset workflow

1. Validate `data/index/walker-reciprocal.csv`
2. Add all museums to `data/index/all-museums.json` (master list)
3. Add museums by state to `data/states/{state}.json` and enrich records over time

## Start here

- **Application Architecture**: `ApplicationArchitecture.md`
  - Overall system design (React SPA + FastAPI + OpenAI API), single-origin hosting, Azure Windows VM deployment.

- **API Specification (Canonical)**: `MuseumAPI.md`
  - HTTP endpoints for museum browsing/search, user personalization, optional trips, and admin curation.

- **Dataset Design (Canonical)**: `DataSetDesign.md`
  - Walker reciprocal dataset field definitions, scoring methodology, and data quality/provenance requirements.

## Historical source documents

These PDFs are retained as original concept/architecture sources:

- `MuseumSpark_ React + ChatGPT-Powered Trip Planner on Azure.pdf` (historical source; older naming)
- `MuseumSpark_ Deployment and Architecture Plan.pdf`

## Deprecated

- `MusuemAPI.md` is kept as a backwards-compatible stub (typo in filename). Use `MuseumAPI.md` instead.
