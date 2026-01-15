# Implementation Plan: MuseumSpark Phase 1 — Static Dataset Browser (GitHub Pages)

**Branch**: `001-museum-trip-planner` (Phase 1)  
**Date**: 2026-01-15  
**Spec**: `specs/001-museum-trip-planner/spec.md`

## Summary

Deliver a Priority 1 first release as a **read-only static web application** hosted on **GitHub Pages** that browses `data/index/all-museums.json`, drills down to museum details via `data/states/{STATE}.json`, and displays dataset progress metrics (FULL vs placeholder).

No backend API, authentication, personalization, trips, or AI is included in Phase 1.

## Technical Context

**Language/Version**: TypeScript (recommended) + modern browser runtime  
**Primary Dependencies**: Vite + React (recommended) OR lightweight vanilla JS (acceptable); optional client search lib (e.g., Fuse.js or FlexSearch)  
**Storage**: Static JSON in-repo under `data/`  
**Testing**: Basic unit tests for filtering/completeness logic (if framework introduced)  
**Target Platform**: GitHub Pages (static hosting)

**Constraints**:
- Must work on a GitHub Pages base path (non-root) reliably
- Must not require any server-side computation
- Must handle missing/partial data gracefully

## Project Structure (Phase 1)

Proposed structure (web app is new; adjust if you prefer a different location):

```text
site/                 # Static web app source (Vite)
  src/
  public/
  index.html

docs/                 # (Optional) GH Pages publish folder if not using Actions artifact deploy

data/
  index/all-museums.json
  states/*.json
  schema/museum.schema.json
  ...

scripts/
  validate-json.py
  build-index.py
  ...
```

## Phase 1 Work Breakdown

### 1) Data readiness (keeps current workflow intact)

- Confirm `scripts/build-index.py` produces/updates `data/index/all-museums.json` correctly from `data/states/*.json`.
- Ensure schema validation remains the quality gate (`scripts/validate-json.py` / `scripts/validate-json.ps1`).

### 1.1) Data enrichment plan (open data first, then LLM augmentation)

Phase 1 includes the **data gathering/enrichment pipeline** as repo scripts. This is separate from the GitHub Pages site (which remains read-only).

**Priority order:**
1) Free/open structured sources (Wikidata/OSM/IMLS/Wikipedia)
2) Official museum website extraction (free, but more variable)
3) GPT/Claude augmentation only for what is still missing

**Goal:** move museums from seeded placeholder records (e.g., `street_address: "TBD"`) to schema-valid, enriched records that meet the Phase 1 “FULL” definition in the spec.

**Inputs (per museum):**
- Existing stub/partial museum record from `data/states/{STATE}.json`
- Museum official website pages (home + “visit/hours/admission” + “accessibility” + “tickets” when present)
- Optional free sources (Wikidata/OSM/Wikipedia/IMLS, described below)

**Outputs (per museum):**
- Updated museum record written back into its state file with:
  - verified address fields
  - classification and planning metadata
  - provenance (`data_sources`, verification dates, confidence)
  - optional art scoring fields when appropriate

**Key design constraints:**
- Scripts must be idempotent: do not overwrite curated fields unless explicitly requested.
- Every field set by an LLM must be provenance-stamped (source list + confidence).
- Treat LLM output as untrusted: validate against schema and apply deterministic post-processing.

**Phased enrichment workflow (recommended):**

Phase A — Open data fill (default)
- Try to populate structured fields from:
  - Wikidata (website, coordinates, sometimes address/postal)
  - OpenStreetMap/Nominatim (coordinates + normalized address components)
  - IMLS (US museums; authoritative registry-style fields)
- Write conservative patches back to `data/states/{STATE}.json`.

Phase B — Gap review (no LLM)
- Generate missing-field reports and a “needs enrichment” queue.
- Focus human/manual effort where sources conflict.

Phase C — LLM augmentation (only for remaining gaps)
- Use GPT/Claude to generate:
  - `museum_type`, `primary_domain`, `topics`
  - `time_needed`, `visit_priority_notes`, and narrative `notes`
  - art scoring fields (when applicable)

**Proposed script additions (Phase 1):**

0) `scripts/enrich-open-data.py` (free sources first)
   - Inputs: `--state CA` OR `--museum-id ...`, `--only-placeholders`, `--limit`, `--dry-run`
   - Does:
     - query Wikidata + OSM for structured fields
     - merges conservative patches into records
     - caches responses locally to reduce load/rate-limit risk
     - logs what was changed and why

1) `scripts/enrich-museum.py` (single museum)
   - Inputs: `--museum-id`, `--model-provider openai|anthropic|auto`, `--dry-run`, `--state` override
   - Does:
     - fetch+extract text from known URLs (official site + optional sources)
     - run an extraction prompt to produce a **partial patch object**
     - validate patch vs schema types/enums
     - merge patch into existing record (conservative merge)

2) `scripts/enrich-batch.py` (batch enrichment)
   - Inputs: `--state CA`, `--limit 50`, `--only-placeholders`, `--concurrency 5`
   - Does:
     - iterates museums, enrichment, validation, and writes state file
     - emits a run report (JSON/CSV) including token usage and estimated cost

3) `scripts/build-progress.py`
   - Generates `data/index/progress.json` with counts:
     - total museums, FULL, placeholder
     - per-state totals
     - run timestamp
   - (Optional) also writes a “top missing fields” histogram to help focus curation.

4) `scripts/build-missing-report.py`
   - Generates `data/index/missing-report.json` describing:
     - which Phase 1 “FULL” fields are missing (counts and per-museum IDs)
     - top missing fields overall
   - This is the main handoff artifact to decide which museums require GPT/Claude.

**Provider strategy (use both subscriptions effectively):**

- Use **Claude Haiku** or **OpenAI gpt-4o-mini** for high-volume, inexpensive extraction and normalization.
- Use **Claude Sonnet** (or a stronger OpenAI model) only for:
  - hard-to-parse sites
  - conflicting sources
  - complex classification/scoring decisions

**Secrets / keys (local only):**
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

Never commit `.env` files; keep keys in local environment variables.

**Scraping hygiene:**
- Respect robots.txt where applicable.
- Cache fetched HTML and extracted text locally (e.g., `data/cache/http/`) to minimize repeated hits and reduce token spend.

---

### 2) Define and implement completeness computation

- Implement the Phase 1 FULL vs placeholder rule from the spec:
  - Schema required fields (already validated)
  - Enrichment core fields populated
  - Art scoring fields populated when applicable

Two acceptable approaches:

A) **Compute in-browser** (simplest):
- Compute FULL/placeholder counts on page load from `all-museums.json`.
- Pros: no extra build step.
- Cons: more client work; still fine for hobby scale.

B) **Precompute in scripts (recommended for consistency)**:
- Add a script to generate `data/index/progress.json` (counts + per-state breakdown + last_updated stamp).
- Web app reads `progress.json` for dashboard, and still computes per-museum badges from record fields.

**Current baseline (computed from `data/index/all-museums.json`):**
- Total museums: 1269
- FULL (per strict Phase 1 definition): 7
- Placeholder: 1262

This will move quickly as enrichment scripts start filling in the Phase 1 core fields.

### 3) Static web app (browse/search/filter + detail drill-down)

Core screens/routes:

- Home / Browse
  - Search box
  - Filter panel (state/city/domain/reputation/collection tier/time needed/etc.)
  - Sort controls
  - Paginated/virtualized result list
  - Per-museum “FULL” badge

- Museum Detail `/museums/:museum_id`
  - Determine state file:
    - Preferred: parse from `museum_id` convention (e.g., `usa-ak-*` → `AK.json`)
    - Fallback: mapping table if needed
  - Fetch `data/states/{STATE}.json` and select record by `museum_id`
  - Render all fields with “Not available” placeholders

- Progress
  - Show total museums, FULL count, placeholder count
  - Per-state breakdown table

Search implementation notes:
- Start with deterministic substring match for `museum_name` and `alternate_names`.
- If you want fuzzy search, add a client-side search index (Fuse.js/FlexSearch) built at runtime or prebuilt during Vite build.

### 4) GitHub Pages deployment

- Decide on deployment strategy:
  - GitHub Actions build + deploy to Pages (recommended)
  - Or publish to a `docs/` folder (simple but less flexible)

- Ensure fetch paths work under base URL:
  - Use runtime `BASE_URL` support (Vite) or relative path resolution.

### 5) Validation / QA

- Verify filters and sorting with a few known museums.
- Verify drill-down works for at least 3 states.
- Verify Progress counts match computed logic.

## Deliverables

- Phase 1 spec: `specs/001-museum-trip-planner/spec.md`
- Phase 1 plan: `specs/001-museum-trip-planner/plan.md`
- Static site (new folder) suitable for GitHub Pages
- (Optional but recommended) `data/index/progress.json` generated from scripts

---

## Token Cost Estimate (to fully enrich ~1200+ museums)

This is an estimate for the **LLM-assisted enrichment work** (Phase 1 “Data Gathering”), not the static site.

### Assumptions

- Museum count: 1269 (from `data/index/all-museums.json`)
- Average LLM work per museum (typical):
  - **Input tokens:** 24,000
  - **Output tokens:** 3,000
  - (~2–4 calls: summarize extracted pages, then generate schema patch; retries not included)

You can plug different values into the formulas below.

### OpenAI example (cheap bulk extraction)

Using OpenAI pricing from the API pricing docs (example model `gpt-4o-mini`):
- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens

Estimated per museum:
- Input cost: 0.024 × $0.15 = $0.0036
- Output cost: 0.003 × $0.60 = $0.0018
- Total: **$0.0054 / museum**

For 1269 museums: 1269 × $0.0054 ≈ **$6.85**

Recommended planning multiplier (retries + harder cases + additional pages): **×3 to ×10**
- Practical planning range: **~$20 to $70**

### Claude example (higher-quality extraction)

Using Claude API pricing from `claude.com/platform/api` (examples):

**Haiku 4.5**
- Input: $1 / MTok, Output: $5 / MTok
- Per museum: 0.024×1 + 0.003×5 = $0.024 + $0.015 = **$0.039**
- For 1269 museums: ≈ **$49.49**

**Sonnet 4.5** (prompts ≤ 200K tokens)
- Input: $3 / MTok, Output: $15 / MTok
- Per museum: 0.024×3 + 0.003×15 = $0.072 + $0.045 = **$0.117**
- For 1269 museums: ≈ **$148.47**

Claude also supports **batch processing (~50% savings)** and **prompt caching**, which can materially reduce costs if you reuse templates and shared context.

### Recommendation

- Default to **cheap model for most museums** + **upgrade-on-fail**:
  - Haiku or gpt-4o-mini for 80–95% of museums
  - Sonnet/stronger model for the remainder

Track actual spend by logging per-run token usage and computing totals in the batch script report.

---

## Free / Open Data Sources to Augment Museum Records

These sources can reduce LLM token usage and improve accuracy by providing structured fields directly.

### High-value, free sources

1) **Wikidata (SPARQL)**
   - Often includes: official website, coordinates, address components, inception date, operator, and Wikipedia links.
   - Pros: structured + global coverage.
   - Cons: coverage/quality varies; requires reconciliation (name/URL matching).

2) **OpenStreetMap (OSM)**
   - Via Nominatim geocoding or Overpass queries.
   - Great for: lat/long, address normalization, place IDs (OSM IDs).
   - Pros: free and commonly accurate.
   - Cons: rate limits; licensing/attribution requirements.

3) **Wikipedia / DBpedia**
   - Useful for: short descriptions, alternate names, and basic classification.
   - Pros: broad coverage.
   - Cons: not always structured; needs citation/provenance.

4) **IMLS Museum Universe Data File (USA)**
   - Useful for: authoritative registry-style fields for many US museums.
   - Pros: government dataset.
   - Cons: may require download + matching; coverage depends on dataset scope/updates.

### How to use these sources in the pipeline

- Prefer **structured sources first** (Wikidata/OSM/IMLS) to populate:
  - `latitude`, `longitude`, `timezone` (derived from coordinates), address normalization
  - `website` verification and canonicalization
- Then use LLMs for:
  - `museum_type`, `primary_domain`, `topics`
  - `time_needed`, `visit_priority_notes`, and narrative `notes`
  - art scoring fields (when applicable)

### Licensing note

Even when sources are “free”, they may have attribution or share-alike requirements (notably OSM). Treat licensing review as part of the enrichment workflow before embedding derived content.

## Explicitly Deferred (Phase 2+)

- FastAPI, SQLite, auth, favorites/visited, trips/itineraries
- OpenAI integration and any server-side AI endpoints
- Admin curation UI
