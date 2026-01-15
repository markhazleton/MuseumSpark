# Feature Specification: MuseumSpark Phase 1 — Static Dataset Browser (GitHub Pages)

**Feature Branch**: `001-museum-trip-planner` (Phase 1 scope update)
**Created**: 2026-01-15
**Last updated**: 2026-01-15
**Status**: Approved (Phase 1)
**Input**: Update scope to a first release that is a read-only static web application on GitHub Pages.

## 0. Phase Definition (Non-negotiable)

### Phase 1 (this spec / Priority One)

1) **Data gathering and validation** in the repo (`data/` + `scripts/`).
2) A **lightweight, read-only static web app** hosted on **GitHub Pages** that:
   - browses/searches/filters the master index `data/index/all-museums.json`
   - drills down to a museum detail view using `data/states/{STATE}.json` records
   - shows progress/completeness status (FULL vs placeholder) across the dataset.

### Phase 2+ (explicitly out of scope for this spec)

- FastAPI backend, SQLite, authentication, personalization, trips/itineraries, admin CRUD, AI/OpenAI integration.
- These will be specified in subsequent specs.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Browse/Search/Filter Museums (Priority: P1)

A Walker Art Reciprocal Program member wants to browse and search the entire reciprocal museum roster and quickly narrow results with multi-criteria filters.

**Independent Test**: Fully testable in a browser against the repo’s static JSON artifacts.

**Acceptance Scenarios**:

1. **Given** the site is loaded, **When** the user searches for a partial museum name, **Then** results update with case-insensitive matching.
2. **Given** the user selects filters (e.g., state + reputation + time_needed), **When** they apply multiple filters, **Then** the result set matches AND logic across all selected filters.
3. **Given** the user sorts by `priority_score`, **When** there are ties or null scores, **Then** sorting is stable and deterministic (e.g., `priority_score asc`, nulls last, then `museum_name asc`).
4. **Given** a large dataset, **When** the user pages through results, **Then** paging is responsive and does not reload the entire application.

---

### User Story 2 — View Data Collection Progress (Priority: P1)

A curator/maintainer wants a dashboard view that summarizes how much of the dataset is fully enriched vs still placeholder/minimal.

**Independent Test**: Compare displayed counts to counts computed from the JSON dataset.

**Acceptance Scenarios**:

1. **Given** the dataset is loaded, **When** the user opens the Progress view, **Then** they see counts for total museums, FULL records, and placeholder records.
2. **Given** the user selects a state, **When** they view state progress, **Then** they see per-state totals and FULL/placeholder breakdown.
3. **Given** the dataset changes (commit updates), **When** GitHub Pages deploys, **Then** the Progress view reflects the updated counts with no manual edits.

---

### User Story 3 — Drill Down to Museum Detail via State Files (Priority: P1)

A user wants to click a museum in the master list and view a detail page that reflects the canonical state-curated record.

**Independent Test**: Click-through from index results to a detail page that fetches `data/states/{STATE}.json` and renders the matching `museum_id`.

**Acceptance Scenarios**:

1. **Given** a museum result row, **When** the user opens its detail page, **Then** the app loads the museum record from `data/states/{STATE}.json` (by `museum_id`) and renders all fields.
2. **Given** the state file is missing or does not contain the museum, **When** the user opens the detail page, **Then** the app shows a clear error state and MAY fall back to the `all-museums.json` record.
3. **Given** a museum has partial data, **When** the user opens detail, **Then** missing fields render as “Not available” (no blank UI gaps).

---

### Edge Cases

- Museums with `priority_score: null` (unscored) should remain discoverable and sort after scored museums.
- GitHub Pages base path must be handled correctly (relative fetch paths must work on repo pages URLs).
- Large JSON files: first load should show a loading state and remain usable.

---

## Requirements *(mandatory)*

### Functional Requirements (Phase 1)

- **FR-001**: The Phase 1 release MUST be a **static web application** hosted on **GitHub Pages**.
- **FR-002**: The Phase 1 web app MUST be **read-only** (no user accounts, no writes, no server-side API).
- **FR-003**: The app MUST load and browse museums from `data/index/all-museums.json`.
- **FR-004**: The app MUST support robust search and filtering against the master list, including at minimum:
  - text search over `museum_name` (and `alternate_names` when present)
  - location filters: `country`, `state_province`, `city`
  - classification filters: `primary_domain`, `museum_type`, `status`
  - quality filters: `reputation`, `collection_tier`
  - travel filters: `time_needed`
  - art/scoring filters: `min_impressionist_strength`, `min_modern_contemporary_strength`, `primary_art`, and `priority_score` range
- **FR-005**: The app MUST support sorting by at least: `priority_score`, `museum_name`, `reputation`, `collection_tier`.
- **FR-006**: The app MUST support pagination/virtualization to keep the UI responsive for large result sets.
- **FR-007**: Museum detail pages MUST be addressable by a stable route using `museum_id`.
- **FR-008**: Museum detail pages MUST fetch canonical detail from the relevant state file `data/states/{STATE}.json`.
  - The state code MUST be derived from the `museum_id` prefix convention (e.g., `usa-ak-*` → `AK.json`) or an equivalent deterministic mapping.
- **FR-009**: The app MUST display dataset progress metrics:
  - total museum count
  - FULL record count
  - placeholder record count
  - per-state breakdown (at minimum totals and FULL/placeholder)
- **FR-010**: The definition of **FULL vs placeholder** MUST be deterministic and implemented consistently across:
  - the progress dashboard counts
  - the museum list UI (badge/indicator)
  - any exported progress summary artifacts (if produced)
- **FR-011**: The dataset pipeline MUST continue to enforce schema validation using `data/schema/museum.schema.json` (pre-commit and/or CI).

### Definition: FULL record (Phase 1)

A museum record is considered **FULL** when:

1) It satisfies the schema required fields (already required by validation):
   - `museum_id`, `country`, `state_province`, `city`, `museum_name`, `website`, `museum_type`, `street_address`, `postal_code`

2) And it has the Phase 1 enrichment “core” fields populated (non-null / non-empty):
   - `primary_domain`, `status`
   - `reputation`, `collection_tier`
   - `time_needed` OR `estimated_visit_minutes`
   - `notes`
   - `data_sources` (at least 1)
   - `confidence` (1–5)

3) And for museums with `primary_domain == "Art"` (or art-scored records), it SHOULD also include scoring inputs (non-null):
   - `impressionist_strength`, `modern_contemporary_strength`, `historical_context_score`
   - and computed fields when present: `priority_score`, `scoring_version`

If a museum is schema-valid but does not meet the enrichment core fields, it is considered **placeholder** for progress reporting.

---

## Success Criteria *(mandatory)*

- **SC-001**: The GitHub Pages site loads and renders a museum list without any backend services.
- **SC-002**: Searching and applying filters remains responsive for the full dataset (target: interactive filter update < 200ms after initial load on a typical laptop).
- **SC-003**: The Progress view displays FULL vs placeholder counts that match the dataset-derived computation.
- **SC-004**: A museum detail page loads from `data/states/{STATE}.json` and displays a complete field set with graceful handling of missing optional fields.

---

## Scope and Boundaries *(mandatory)*

### In Scope (Phase 1)

- Data gathering workflow (validate roster, curate state files, rebuild master index)
- Static GitHub Pages site for browsing/search/filter + museum detail drill-down
- Progress/completeness reporting (FULL vs placeholder)

### Out of Scope (Phase 1)

- FastAPI/SQLite backend and any `/api/v1/*` implementation
- Authentication, favorites/visited, trips/itinerary planning
- Admin CRUD UI
- Any OpenAI/LLM integration

---

## Dependencies *(mandatory)*

### External Dependencies (Phase 1)

- GitHub Pages (static hosting)

### Data Dependencies

- `data/index/all-museums.json` (master list for browsing/search)
- `data/states/{STATE}.json` (canonical per-state curated museum records)
- `data/schema/museum.schema.json` (validation rules)

---

## Assumptions *(mandatory)*

- Users have modern browsers with JavaScript enabled.
- Large JSON fetch + in-browser filtering is acceptable at hobby scale.
- The `museum_id` naming convention can be used to determine the state file for drill-down (or a deterministic mapping is introduced).

---

## Non-Functional Requirements *(include if applicable)*

### Performance

- The app MUST show a loading state during initial JSON fetch.
- Filter interactions SHOULD be responsive after initial load; avoid re-fetching large JSON assets on every interaction.

### Reliability

- Missing fields MUST render as “Not available”.
- Missing state file or missing museum in state file MUST not crash the app.

### Maintainability

- Phase 1 UI MUST treat JSON files as source-of-truth artifacts; no hidden/manual progress numbers.

## Non-Functional Requirements *(include if applicable)*

### Performance

- Search and filter operations complete in under 1 second for typical dataset size
- Museum detail page loads in under 2 seconds with all metadata
- System supports 1,000 concurrent users without degradation
- Priority score calculation for full dataset completes in under 5 seconds
- Database queries use appropriate indexing for location, type, reputation, collection tier fields

### Security

- User authentication uses JWT bearer tokens (OAuth2-style)
- All data transmissions use HTTPS/TLS encryption
- Administrative operations require role-based access control (admin/editor/viewer roles)
- Personal user lists and visit history are private and not shared
- Data modification events are logged for audit trail
- Input validation prevents injection attacks and malformed data

### Usability

- Interface uses clear, consistent terminology (matching museum domain language: "Impressionism", "Modern", "Collection Tier", etc.)
- Filter controls are prominently displayed and easy to understand
- Search results show most relevant information at a glance (name, location, priority score, reputation)
- Museum detail pages organize information logically (identity → location → collection → travel tips)
- Error messages are user-friendly and suggest corrective actions
- System provides helpful hints for empty search results (suggest adjusting filters)

### Reliability

- 99.9% uptime for read operations (browse, search, view)
- Data validation prevents corrupt records from entering dataset
- Graceful degradation if optional fields are missing (display "Not available" rather than hiding museums)
- System recovers automatically from transient failures

### Maintainability

- Data model follows JSON Schema with versioning support
- Algorithm changes are documented with version numbers
- Legacy field names supported during deprecation periods (6 months minimum)
- Code follows project constitution principles (data-first architecture, schema validation, specification-driven development)
- All changes go through validation workflow before commit

### Scalability

- Database design supports growth to 10,000+ museums without architecture changes
- Pagination prevents performance issues with large result sets
- Caching strategies for frequently accessed data (museum details, popular searches)
- Index generation script handles full dataset efficiently (build-index.py)
