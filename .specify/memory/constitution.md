<!--
Sync Impact Report:
- Version change: 1.0.0 → 2.0.0
- Modified principles: Scoring algorithm, data enrichment strategy, Walker Art context
- Added sections: Multi-phase pipeline architecture, evidence tracking, Walker Art Reciprocal Program context
- Removed sections: None
- Templates requiring updates:
  ✅ .specify/templates/spec-template.md (verified compatibility)
  ✅ .specify/templates/plan-template.md (verified compatibility)
  ✅ .specify/templates/tasks-template.md (verified compatibility)
  ✅ .specify/templates/checklist-template.md (verified compatibility)
- Follow-up TODOs: None
- Rationale: MAJOR version update to align constitution with MasterRequirements.md v1.0
  and actual implementation. Corrects scoring formula, adds Walker Art Reciprocal Program
  context, documents multi-phase pipeline, and updates data quality standards.
-->

# MuseumSpark Constitution

## Core Principles

### I. Walker Art Reciprocal Program Context (FOUNDATIONAL)

MuseumSpark exists to **transform the Walker Art Center Reciprocal Program membership
into an intelligent travel planning resource**. The authoritative seed list comes from
Walker's reciprocal membership page (https://walkerart.org/support/membership/reciprocal-membership/)
and is maintained in `data/index/walker-reciprocal.csv`.

**Inclusion Policy** (MRD Section 2B):
- **All museums** from the Walker reciprocal roster are included in the dataset
- **Only relevant art museums** (fine art, encyclopedic, university) receive priority scoring
- **Non-art museums** (history, science, specialty) remain in the dataset unscored to support
  city-level planning and reciprocal membership value discovery

**Rationale**: MuseumSpark's purpose is to maximize the value of Walker Art reciprocal
membership by enabling data-driven travel decisions. Every feature serves this goal.

### II. Data-First Architecture

All features and functionality must be grounded in the museum dataset as the
single source of truth. The dataset structure defined in `data/schema/museum.schema.json`
is authoritative. Any API, frontend, or service layer MUST conform to the canonical
data model. Schema changes require formal approval and migration planning.

The canonical museum records are stored per-state in `data/states/*.json`. The master
index `data/index/all-museums.json` is a derived artifact rebuilt via `scripts/builders/build-index.py`.

**Rationale**: MuseumSpark's value proposition depends on data quality and
consistency. A data-first approach ensures all layers remain synchronized.

### III. Schema Validation (NON-NEGOTIABLE)

Every museum record MUST validate against the JSON Schema before acceptance
into the dataset. All state files MUST pass validation via `scripts/validation/validate-json.py`
before commit. No exceptions.

**Required validation workflow**:
1. Add/modify museum records in state JSON files (`data/states/*.json`)
2. Run validation: `python scripts/validation/validate-json.py`
3. Fix all validation errors
4. Rebuild indices: `python scripts/builders/build-index.py`
5. Commit only when validation passes

**Rationale**: Invalid data corrupts the prioritization algorithm and user
experience. Schema enforcement is the primary quality gate.

### IV. Specification-Driven Development

All features MUST follow the Speckit workflow: Specify → Clarify → Plan →
Tasks → Implement → Analyze. No code implementation begins without an approved
specification in `.specify/specs/`. Specifications MUST reference the data model
in [Documentation/DataSetDesign.md](Documentation/DataSetDesign.md) and API design 
in [Documentation/MuseumAPI.md](Documentation/MuseumAPI.md).

**Rationale**: MuseumSpark is a complex domain requiring careful design.
Specification-first ensures stakeholder alignment and reduces rework.

### V. Algorithmic Integrity (Art Museum Scoring)

The priority scoring algorithm defined in [Documentation/MasterRequirements.md](Documentation/MasterRequirements.md)
is canonical and MUST NOT be altered without documentation update and versioning.
All implementations of the scoring formula MUST produce identical results given
identical inputs. The algorithm version MUST be tracked in generated data via
the `scoring_version` field.

**Canonical Formula** (MRD Section 5):

**Step 1: Determine Primary Art Strength**
```
Primary Art Strength = max(Impressionist Strength, Modern/Contemporary Strength)
```

**Step 2: Calculate Base Score**
```
Priority Score =
  (5 – Primary Art Strength) × 3
+ (5 – Historical Context Score) × 2
+ (5 – Collection-Based Strength) × 2
+ Reputation Tier
```

**Step 3: Apply Bonuses (Subtract from Score)**
```
– Dual-Strength Bonus (–2 if both Impressionist Strength ≥4 AND Modern/Contemporary Strength ≥4)
– ECA Bonus (–1 if Exhibitions & Curatorial Authority ≥4)
```

**Scoring Dimensions** (all 0-5 scales except Reputation):
- **Impressionist Strength** (0-5): Depth of Impressionist permanent collection
- **Modern/Contemporary Strength** (0-5): Depth of Modern/Contemporary permanent collection
- **Historical Context Score** (0-5): Quality of historical framing and interpretation
- **Exhibitions & Curatorial Authority (ECA)** (0-5): Programmatic influence beyond permanent holdings
- **Collection-Based Strength** (0-5): Overall depth/authority across all categories
- **Reputation Tier** (0-3): 0=International, 1=National, 2=Regional, 3=Local

**Score Interpretation**:
- Lower scores = higher priority
- Negative scores are possible (world-class institutions with multiple bonuses)
- Museums with Historical Context = 5 flagged as potential "Must-See"
- Non-art museums have `priority_score: null` and `is_scored: false`

**Rationale**: Consistency in prioritization is critical for user trust. The
algorithm is a core intellectual property asset derived from expert art curation
knowledge.

### VI. Data Provenance and Multi-Phase Enrichment

MuseumSpark uses a **multi-phase enrichment pipeline** to build high-quality museum
records from open data sources. Every museum progresses through phases until
reaching "FULL" enrichment status.

**Multi-Phase Architecture**:
- **Phase 0**: Identity verification via Wikidata
- **Phase 0.5**: Wikidata structured data extraction  
- **Phase 0.7**: Official website metadata harvesting
- **Phase 1**: Backbone data (address, city tier, museum type)
- **Phase 1.5**: Wikipedia article extraction
- **Phase 1.75**: Heuristic fallback for missing fields
- **Phase 1.8**: CSV lookup integration for supplementary data
- **Phase 1.9**: Museum planner metadata (product owner notes)
- **Phase 2**: Expert scoring (art museums only)
- **Phase 2.5**: Rich content extraction
- **Phase 3**: Priority score calculation

**Enrichment Quality Levels**:
- **PLACEHOLDER**: Basic name/state only from Walker roster
- **FULL**: Complete enrichment with all required fields validated

**Evidence Tracking**: Every enriched field MUST include provenance metadata:
- `data_sources` (array): URLs or source identifiers (Wikidata, Wikipedia, official website, etc.)
- `confidence` (1-5): Data accuracy confidence score
- `created_at`, `updated_at`: ISO date strings
- `address_source`: Origin of address data (`official_website`, `google_places`, `wikidata`, etc.)
- `address_last_verified`: Date address was last verified

**Data Quality Guardrail** (NON-NEGOTIABLE):
**"Never Replace Known With Null"** - Enrichment phases MUST NOT overwrite populated
fields with null/empty values. Preserve existing data when new sources lack information.

**Primary Data Sources** (prioritized):
1. **Official museum websites** (highest authority for address, hours, current status)
2. **Wikidata** (structured metadata, coordinates, Wikidata IDs)
3. **Wikipedia** (article content, historical context)
4. **OpenStreetMap / Open Data sources** (geographic data)
5. **LLM-assisted extraction** (structured data from unstructured sources)

Generated or computed data MUST be reproducible from source data and scripts.
The `scripts/builders/build-index.py` script MUST be deterministic (same inputs → same outputs).

**Rationale**: Data quality and trustworthiness require transparent sourcing
and change tracking. Multi-phase enrichment enables incremental progress with
quality checkpoints. Auditability enables quality improvement over time.

### VII. Backward Compatibility and Versioning

The JSON schema and data model follow semantic versioning. Breaking changes
(field removals, type changes, constraint tightening) require MAJOR version
increment. Non-breaking additions (new optional fields) require MINOR increment.
Legacy field names MUST be supported during deprecation periods (minimum 6 months
notice in CHANGELOG).

**Current schema version**: Tracked in `data/schema/museum.schema.json`

**Rationale**: Third-party consumers and data processing scripts depend on
stability. Versioning enables controlled evolution.

## Dataset Scope and Scale

### Current Status (as of January 2026)
- **Total Museums**: 1,269 from Walker Art Reciprocal Program
- **Geographic Coverage**: 58 jurisdictions
  - United States: 50 states + DC + Puerto Rico
  - Canada: All provinces and territories  
  - International: Bermuda, Mexico
- **Enrichment Progress**: ~0.08% fully enriched (1/1,269 museums)
- **Current Phase**: Phase 1 (backbone data enrichment)

### Implementation Status
- ✅ React + Vite static site with browse/search/filter
- ✅ Museum detail pages with state file drill-down
- ✅ Progress dashboard (FULL vs PLACEHOLDER tracking)
- ✅ Multi-phase enrichment pipeline (Phase 0-Phase 3)
- ✅ JSON Schema validation framework
- ✅ Wikidata, Wikipedia, and website scraping infrastructure
- ⚠️ GitHub Pages deployment (not yet configured)
- 🔄 Dataset enrichment (ongoing Phase 0-1.9 runs)

## Data Quality Standards

### Field Completeness Requirements

**Required Fields** (enforced by JSON Schema for all museums):
- **Core identity**: `museum_id`, `museum_name`, `country`, `state_province`, `city`, `website`
- **Physical address**: `street_address`, `postal_code`, `museum_type`

**Art Museum Scoring Fields** (required only for art-focused museums):
- **Collection strengths**: `impressionist_strength`, `modern_contemporary_strength` (0-5)
- **Curatorial quality**: `historical_context_score` (0-5)
- **Exhibition authority**: `exhibitions_curatorial_authority` (0-5)  
- **Overall collection**: `collection_based_strength` (0-5)
- **Reputation**: `reputation` (0-3 scale: International=0, National=1, Regional=2, Local=3)
- **Classification**: `primary_domain`, `primary_art`

**Enrichment Target Fields** (recommended for travel planning):
- **Logistics**: `estimated_visit_minutes`, `time_needed`, `best_season`, `parking_notes`
- **Geolocation**: `latitude`, `longitude`, `timezone`, `place_id`
- **Context**: `city_tier` (1=Major hub, 2=Medium city, 3=Small town)
- **Discovery**: `nearby_museum_count`, `topics`, `audience_focus`
- **Status**: `status` (active/closed/seasonal/unknown)
- **Visitor links**: `open_hours_url`, `tickets_url`, `accessibility_url`

**Status Tracking Fields**:
- `last_updated`: Record-level update timestamp
- `scoring_version`: Algorithm version used for scores
- `is_scored`: Boolean flag indicating if museum has been scored
- `scored_by`: How scores were produced (assistant/manual/hybrid)

**Optional Fields**:
Null values are permitted for optional fields but MUST be explicit (`null`, not
omitted) in JSON to distinguish "unknown" from "not applicable."

### Controlled Vocabularies

Enumerated fields MUST use exact values from the schema. Common vocabularies:

**museum_type** (human-friendly, can be nuanced):
- `"Art (Encyclopedic)"`, `"Art (Modern/Contemporary)"`, `"Art (Regional)"`, `"Art (University)"`
- `"History"`, `"Science"`, `"Mixed (Art & History)"`, `"Specialty"`
- Other descriptive combinations as needed

**primary_domain** (used for filtering and scoring eligibility):
- `"Art"`, `"History"`, `"Science"`, `"Culture"`, `"Specialty"`, `"Mixed"`

**reputation** (0-3 integer):
- `0` = International
- `1` = National  
- `2` = Regional
- `3` = Local

**collection_tier** (0-3 integer):
- `0` = Flagship (world-class)
- `1` = Strong (substantial holdings)
- `2` = Moderate (solid but limited)
- `3` = Small (modest collection)

**city_tier** (1-3 integer):
- `1` = Major hub (metropolitan areas)
- `2` = Medium city
- `3` = Small town

**time_needed**:
- `"Quick stop"` (<1 hr)
- `"Half day"` (2-4 hours)
- `"Full day"` (5+ hours)

**status**:
- `"active"`, `"closed"`, `"seasonal"`, `"unknown"`

**address_source**:
- `"official_website"`, `"google_places"`, `"wikidata"`, `"wikipedia"`, `"manual"`, `"unknown"`

**scored_by**:
- `"assistant"` (LLM-generated), `"manual"` (human expert), `"hybrid"` (combination)

**Rationale**: Consistent vocabularies enable reliable filtering and aggregation.

### Data Entry and Verification

**Automated Enrichment** (preferred):
- Automated pipeline scripts extract data from Wikidata, Wikipedia, and official websites
- LLM-assisted extraction structures unstructured web content
- All automated enrichments track provenance via `data_sources` arrays

**Manual Data Entry** (when needed):
- MUST be verified against official museum websites or authoritative sources
- The `address_source` field MUST document the verification source
- Batch imports require spot-check validation of 10% sample before acceptance

**Quality Verification**:
- Run `python scripts/validation/validate-json.py` before committing
- Check progress dashboard for completeness metrics
- Review evidence gaps via `python scripts/analyze_missing.py`

## Technology Standards

### Python Data Pipeline

**Required Environment**:
- Python 3.11+ (for modern type hints and performance)
- Virtual environment (`.venv/`) for dependency isolation
- Dependencies managed via `scripts/requirements.txt`

**Key Libraries**:
- **Pydantic 2.x**: Data validation and structured parsing
- **BeautifulSoup4**: HTML parsing and web scraping
- **html2text**: Clean markdown conversion for LLM input
- **requests**: HTTP client for API calls and web fetching
- **json**: Standard library for JSON processing

**Script Standards**:
All Python scripts MUST:
- Support Python 3.11+
- Handle Windows console encoding (UTF-8 wrapper for `sys.stdout`/`sys.stderr`)
- Include docstrings with usage examples
- Use `argparse` for command-line interfaces
- Exit with code 0 on success, 1 on error
- Output validation/error messages in standard format: `[OK]`, `[ERROR]`, `[WARNING]`
- Log enrichment operations with phase, museum_id, and timestamp

**Pipeline Architecture**:
- Phase scripts in `scripts/phases/` (phase0_identity.py, phase1_backbone.py, etc.)
- Builder scripts in `scripts/builders/` (build-index.py, build-progress.py)
- Validation scripts in `scripts/validation/` (validate-json.py)
- Main orchestrator: `scripts/pipeline/run-complete-pipeline.py`

### Frontend (React)

**Technology Stack**:
- **React 19**: Modern UI library with hooks
- **Vite 7**: Lightning-fast build tool
- **Tailwind CSS 4**: Utility-first styling framework
- **React Router 7**: Client-side routing for SPA

**Build Output**:
- Static site with all assets in `site/dist/`
- Data synced from `data/` to `site/public/data/` before build
- Deployable to GitHub Pages or any static hosting

**Development Server**:
- `npm run dev` starts local dev server at http://localhost:5173
- Hot module replacement for rapid iteration
- Automatic data sync on startup

### Future Backend (Phase 4)

**Planned Technology**:
- **FastAPI**: Modern Python web framework
- **SQLite**: Embedded database for user data
- **PydanticAI**: Structured LLM interactions
- **OpenAI/Anthropic APIs**: AI-powered content generation
- **Uvicorn**: ASGI server for FastAPI

### JSON Formatting

All JSON files MUST:
- Use 2-space indentation
- Include UTF-8 encoding without BOM
- End with single newline
- Use ISO 8601 format for dates (`YYYY-MM-DD`) and timestamps (`YYYY-MM-DDTHH:MM:SSZ`)
- Preserve explicit `null` for unknown values (do not omit fields)

### Caching Strategy

**Cache Directories** (gitignored, runtime-generated):
- `data/cache/http/`: HTTP response cache for website fetches
- `data/cache/wikidata/`: Wikidata query response cache
- `data/cache/wikipedia_population/`: Wikipedia data cache  
- `data/cache/open-data/`: OpenStreetMap and other open data caches
- `data/cache/phase0/`, `data/cache/phase2/`: Phase-specific intermediate data

**Cache Invalidation**:
- Caches persist across runs to reduce API load
- Manual cache clearing via deletion of cache subdirectories
- Cache entries include timestamps for age-based invalidation (if implemented)

**Rationale**: Caching reduces load on external APIs and speeds up pipeline re-runs.

### Documentation

User-facing documentation MUST:
- Include concrete examples (not abstract descriptions)
- Provide command-line usage with actual commands
- Document both Windows (PowerShell) and cross-platform (Python) workflows
- Link to canonical data model documentation

**Key Documentation Files**:
- [README.md](README.md): Project overview, quickstart, features
- [Documentation/MasterRequirements.md](Documentation/MasterRequirements.md): Authoritative product requirements
- [Documentation/DataSetDesign.md](Documentation/DataSetDesign.md): Dataset structure and methodology
- [Documentation/ApplicationArchitecture.md](Documentation/ApplicationArchitecture.md): System architecture
- [Documentation/MuseumAPI.md](Documentation/MuseumAPI.md): API specification (future Phase 4)
- [CLAUDE.md](CLAUDE.md): AI assistant context document

## Governance

### Amendment Process

Constitution amendments require:
1. Proposal documenting rationale and impact analysis
2. Review of affected templates in `.specify/templates/`
3. Version increment following semantic versioning
4. Update of Sync Impact Report (HTML comment at top of file)
5. Commit message format: `docs: amend constitution to vX.Y.Z (summary)`

**Semantic Versioning for Constitution**:
- **MAJOR**: Breaking changes to core principles, scoring algorithm, or validation requirements
- **MINOR**: New principles, clarifications, or non-breaking additions
- **PATCH**: Typo fixes, formatting improvements, or minor clarifications

### Compliance Verification

All pull requests MUST verify compliance with:
- **Schema validation**: Automated via `python scripts/validation/validate-json.py`
- **Speckit workflow adherence**: Spec file presence for features (in `.specify/specs/`)
- **Algorithmic integrity**: Scoring formula unchanged unless documented in MRD
- **Data provenance completeness**: Required fields populated with evidence tracking
- **Index rebuild**: Run `python scripts/builders/build-index.py` after state file changes

### Conflict Resolution

When this constitution conflicts with other guidance:
1. **Constitution** supersedes all other documentation (this document is law)
2. **MasterRequirements.md** supersedes implementation details for product requirements
3. **DataSetDesign.md** supersedes code comments for dataset structure
4. **JSON schema** (`museum.schema.json`) supersedes informal specs for validation rules

For runtime development guidance, consult [CLAUDE.md](CLAUDE.md).

## Version History

**Version 2.0.0** (2026-01-26):
- MAJOR: Corrected scoring algorithm to match MRD v1.0
- MAJOR: Added Walker Art Reciprocal Program context as foundational principle
- MAJOR: Documented multi-phase enrichment pipeline (Phase 0-3)
- Added evidence tracking and "Never Replace Known With Null" guardrail
- Updated technology stack to reflect actual implementation (React 19, Vite 7, Python 3.11+)
- Added project scale context (1,269 museums, 58 jurisdictions)
- Clarified art museum vs. non-art museum scoring policy
- Updated controlled vocabularies to match schema
- Added caching strategy documentation

**Version 1.0.0** (2026-01-15):
- Initial constitution establishment
- Basic scoring formula (incorrect, superseded by v2.0.0)
- Data-first architecture principles
- Schema validation requirements

---

**Version**: 2.0.0 | **Ratified**: 2026-01-15 | **Last Amended**: 2026-01-26
