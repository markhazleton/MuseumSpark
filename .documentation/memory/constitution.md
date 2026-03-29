<!--
SYNC IMPACT REPORT
==================
Version change: (new) → 1.0.0
Modified principles: N/A (initial ratification)
Added sections:
  - Core Principles (8 principles)
  - Document Hierarchy
  - Controlled Vocabularies
  - Development Workflow
  - Governance
Removed sections: N/A
Templates requiring updates:
  ✅ .specify/templates/plan-template.md - "Constitution Check" section compatible
  ✅ .specify/templates/spec-template.md - No changes needed
  ✅ .specify/templates/tasks-template.md - No changes needed
Follow-up TODOs: None
-->

# MuseumSpark Constitution

## Core Principles

### I. Schema Validation (NON-NEGOTIABLE)

All museum data files MUST validate against the canonical JSON Schema before acceptance into the repository.

- All state files (`data/states/{state}.json`) MUST pass validation against `data/schema/museum.schema.json` before commit
- Validation MUST be run via `python scripts/validation/validate-json.py`
- Validation output MUST use `[OK]`, `[ERROR]`, `[WARNING]` format
- Schema changes require semantic versioning (MAJOR for breaking changes, MINOR for additions, PATCH for clarifications)

### II. Python Standards (NON-NEGOTIABLE)

All Python scripts in the data pipeline MUST follow consistent patterns for maintainability and Windows compatibility.

- Python 3.11+ MUST be used with modern type hints (`list[str]`, `Optional`, dataclasses)
- Windows UTF-8 encoding wrapper MUST be included at script start
- Comprehensive docstrings with usage examples MUST be provided
- CLI scripts MUST use `argparse` for argument parsing
- Scripts MUST return exit code 0 on success, 1 on error

### III. TypeScript Standards (NON-NEGOTIABLE)

All frontend TypeScript code MUST use strict mode and pass linting before build.

- TypeScript `strict: true` mode MUST be enabled in `tsconfig.json`
- ESLint with `typescript-eslint` rules MUST pass before production build
- Build script enforces lint: `npm run lint && vite build`

### IV. Data-First Architecture (NON-NEGOTIABLE)

The dataset structure is authoritative. All application layers conform to the canonical data model.

- State files (`data/states/{state}.json`) are the canonical source of truth
- Index files (`data/index/`) MUST be derived via rebuild scripts, never edited directly
- JSON Schema (`data/schema/museum.schema.json`) is the authoritative definition of record structure
- Schema changes require formal documentation update in `Documentation/architecture/DataSetDesign.md`
- All API, frontend, and service layers MUST conform to the canonical data model

### V. Data Provenance (NON-NEGOTIABLE)

All data enrichment MUST maintain traceability and preserve existing information.

- Every enriched field MUST include provenance metadata: `data_sources`, `address_source`, `confidence`, `created_at`, `updated_at`
- **Never Replace Known With Null**: Existing non-null values MUST NOT be overwritten with null during enrichment
- Scoring provenance MUST include `scoring_version`, `scored_by`, `score_last_verified`
- Generated data MUST be reproducible from source data and pipeline scripts

### VI. Algorithmic Integrity (NON-NEGOTIABLE)

The priority scoring algorithm is canonical and deterministic.

- Priority scoring formula defined in `Documentation/architecture/MasterRequirements.md` (Section 5) is authoritative
- Algorithm changes MUST update MRD + version bump + migration plan
- All implementations MUST produce identical results given identical inputs
- Algorithm version MUST be tracked in `scoring_version` field

### VII. Testing (RECOMMENDED)

Testing is strongly encouraged to ensure pipeline and application reliability.

- Unit tests for scoring logic and data transformations SHOULD be implemented
- Integration tests for pipeline phases SHOULD validate end-to-end enrichment
- JSON Schema validation serves as the primary data integrity test (see Principle I)
- Test coverage requirements may become NON-NEGOTIABLE in later development phases

### VIII. Documentation Structure (NON-NEGOTIABLE)

All documentation MUST reside in the `/Documentation/` folder with defined structure.

- NEVER create markdown documents outside `/Documentation/` folder (except `.github/copilot-instructions.md` and `CLAUDE.md`)
- AI-generated session documentation MUST go to `/Documentation/copilot/session-YYYYMMDD/`
- Feature documentation MUST be placed in `/Documentation/features/`
- Architecture documentation MUST be placed in `/Documentation/architecture/`
- Update `/Documentation/README.md` when adding new sections

## Document Hierarchy

When making decisions, respect this authority chain:

1. **This Constitution** — Project law, supersedes all other docs
2. **[Documentation/architecture/MasterRequirements.md](Documentation/architecture/MasterRequirements.md)** — Authoritative product requirements (Product Owner)
3. **[Documentation/architecture/DataSetDesign.md](Documentation/architecture/DataSetDesign.md)** — Dataset structure and methodology
4. **[data/schema/museum.schema.json](data/schema/museum.schema.json)** — Validation rules and field definitions
5. **[Documentation/architecture/ApplicationArchitecture.md](Documentation/architecture/ApplicationArchitecture.md)** — System design
6. **[Documentation/architecture/MuseumAPI.md](Documentation/architecture/MuseumAPI.md)** — API specification (Phase 4)

## Controlled Vocabularies

When generating museum records, use exact enum values:

| Field | Values | Type |
|-------|--------|------|
| `reputation` | 0 (International), 1 (National), 2 (Regional), 3 (Local) | integer |
| `collection_tier` | 0 (Flagship), 1 (Strong), 2 (Moderate), 3 (Small) | integer |
| `city_tier` | 1 (Major hub), 2 (Medium city), 3 (Small town) | integer |
| `primary_domain` | "Art", "History", "Science", "Culture", "Specialty", "Mixed" | string |
| `status` | "active", "closed", "seasonal", "unknown" | string |
| `address_source` | "official_website", "google_places", "wikidata", "wikipedia", "manual", "unknown" | string |
| `scored_by` | "assistant", "manual", "hybrid" | string |

## Development Workflow

This project uses **SpecKit** for specification-driven development:

1. **Specify**: Create specification in `.specify/specs/`
2. **Clarify**: Identify underspecified areas
3. **Plan**: Execute implementation planning
4. **Tasks**: Generate actionable, dependency-ordered tasks
5. **Implement**: Execute implementation
6. **Analyze**: Cross-artifact consistency check

No code implementation without approved specification in `.specify/specs/` (RECOMMENDED).

## Governance

- Constitution supersedes all other practices
- Constitution amendments require:
  1. Documentation of proposed change
  2. Team/stakeholder review
  3. Update to this document with version increment (semantic versioning)
- Amendments follow semantic versioning:
  - MAJOR: Backward-incompatible governance/principle removals or redefinitions
  - MINOR: New principle/section added or materially expanded guidance
  - PATCH: Clarifications, wording, typo fixes, non-semantic refinements
- Use [CLAUDE.md](CLAUDE.md) for runtime development guidance
- Compliance reviews SHOULD occur quarterly or after major milestones
- All PRs/reviews SHOULD verify compliance with this constitution

**Version**: 1.0.0 | **Ratified**: 2026-01-30 | **Last Amended**: 2026-01-30
