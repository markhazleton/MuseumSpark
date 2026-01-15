<!--
Sync Impact Report:
- Version change: Template → 1.0.0
- Modified principles: All principles initialized from template
- Added sections: Data Quality Standards, Technology Standards
- Removed sections: None
- Templates requiring updates:
  ✅ .specify/templates/spec-template.md (verified compatibility)
  ✅ .specify/templates/plan-template.md (verified compatibility)
  ✅ .specify/templates/tasks-template.md (verified compatibility)
  ✅ .specify/templates/checklist-template.md (verified compatibility)
- Follow-up TODOs: None
- Rationale: Initial constitution establishment for MuseumSpark project.
  This is a MINOR version (1.0.0) as it establishes the foundational governance
  framework for a greenfield project using Speckit specification-driven development.
-->

# MuseumSpark Constitution

## Core Principles

### I. Data-First Architecture

All features and functionality must be grounded in the museum dataset as the
single source of truth. The dataset structure defined in `data/schema/museum.schema.json`
is authoritative. Any API, frontend, or service layer MUST conform to the canonical
data model. Schema changes require formal approval and migration planning.

**Rationale**: MuseumSpark's value proposition depends on data quality and
consistency. A data-first approach ensures all layers remain synchronized.

### II. Schema Validation (NON-NEGOTIABLE)

Every museum record MUST validate against the JSON Schema before acceptance
into the dataset. All state files MUST pass validation via `validate-json.py`
or `validate-json.ps1` before commit. No exceptions.

**Required validation workflow**:
1. Add/modify museum records in state JSON files
2. Run validation: `python scripts/validate-json.py`
3. Fix all validation errors
4. Commit only when validation passes

**Rationale**: Invalid data corrupts the prioritization algorithm and user
experience. Schema enforcement is the primary quality gate.

### III. Specification-Driven Development

All features MUST follow the Speckit workflow: Specify → Clarify → Plan →
Tasks → Implement → Analyze. No code implementation begins without an approved
specification in `.specify/specs/`. Specifications MUST reference the data model
in `Documentation/DataSetDesign.md` and API design in `Documentation/MuseumAPI.md`.

**Rationale**: MuseumSpark is a complex domain requiring careful design.
Specification-first ensures stakeholder alignment and reduces rework.

### IV. Algorithmic Integrity

The priority scoring algorithm defined in `Documentation/DataSetDesign.md` is
canonical and MUST NOT be altered without documentation update and versioning.
All implementations of the scoring formula MUST produce identical results given
identical inputs. The algorithm version MUST be tracked in generated data via
the `scoring_version` field.

**Formula invariant**:
```
Priority Score =
  (10 - Impressionism Weight × 3)
  × (10 - Modern/Contemporary Weight × 3)
  × (5 - Historical Context Score × 2)
  × (5 - Reputation Score)
  × (5 - Collection Tier Score)
  - Dual Collection Bonus (-2 if both Impressionist and Modern scores ≥3)
  - Nearby Cluster Bonus (-1 if 3+ museums in city)
```

**Rationale**: Consistency in prioritization is critical for user trust. The
algorithm is a core intellectual property asset.

### V. Data Provenance and Auditability

Every museum record MUST include data provenance tracking via required fields:
- `data_sources` (array): URLs or source identifiers
- `confidence` (1-5): Data accuracy confidence score
- `created_at`, `updated_at`: ISO date strings
- `address_source`: Origin of address data

Generated or computed data MUST be reproducible from source data and scripts.
The `build-index.py` script MUST be deterministic (same inputs → same outputs).

**Rationale**: Data quality and trustworthiness require transparent sourcing
and change tracking. Auditability enables quality improvement over time.

### VI. Backward Compatibility and Versioning

The JSON schema and data model follow semantic versioning. Breaking changes
(field removals, type changes, constraint tightening) require MAJOR version
increment. Non-breaking additions (new optional fields) require MINOR increment.
Legacy field names MUST be supported during deprecation periods (minimum 6 months
notice in CHANGELOG).

**Current schema version**: Tracked in `data/schema/museum.schema.json`

**Rationale**: Third-party consumers and data processing scripts depend on
stability. Versioning enables controlled evolution.

## Data Quality Standards

### Field Completeness Requirements

**Phase 1 (Required for all records)**:
- Core identity: `museum_id`, `museum_name`, `country`, `state_province`, `city`, `website`
- Physical address: `street_address`, `postal_code`, `museum_type`
- Status: `status` (active/closed/seasonal/unknown)

**Phase 2 (Required for art museums with scoring)**:
- Collection strength: `impressionist_strength`, `modern_contemporary_strength` (integers 0-5)
- Curatorial quality: `historical_context_score` (integer 1-5)
- Classification: `primary_domain`, `topics`

**Phase 3 (Recommended for travel planning)**:
- Logistics: `estimated_visit_minutes`, `best_season`, `parking_notes`
- Geolocation: `latitude`, `longitude`, `timezone`

Null values are permitted for optional fields but MUST be explicit (`null`, not
omitted) to distinguish "unknown" from "not applicable."

### Controlled Vocabularies

Enumerated fields MUST use exact values from the schema. Common vocabularies:
- `museum_type`: "Art (Encyclopedic)", "Art (Modern/Contemporary)", "Art (Regional)",
  "Art (University)", "History", "Science", "Mixed (Art & History)", "Specialty"
- `reputation`: "Local", "Regional", "National", "International"
- `collection_tier`: "Small", "Moderate", "Strong", "Flagship"
- `primary_domain`: "Art", "History", "Science", "Culture", "Specialty", "Mixed"

**Rationale**: Consistent vocabularies enable reliable filtering and aggregation.

### Data Entry and Verification

Manual data entry MUST be verified against official museum websites or authoritative
sources. The `address_source` field MUST document the verification source.
Batch imports require spot-check validation of 10% sample before acceptance.

## Technology Standards

### Python Scripts

All Python scripts MUST:
- Support Python 3.7+
- Handle Windows console encoding (UTF-8 wrapper for `sys.stdout`/`sys.stderr`)
- Include docstrings with usage examples
- Use `argparse` for command-line interfaces
- Exit with code 0 on success, 1 on error
- Output validation/error messages in format: `[OK]`, `[ERROR]`, `[WARNING]`

### JSON Formatting

All JSON files MUST:
- Use 2-space indentation
- Include UTF-8 encoding without BOM
- End with single newline
- Use ISO 8601 format for dates (`YYYY-MM-DD`) and timestamps (`YYYY-MM-DDTHH:MM:SSZ`)

### Documentation

User-facing documentation MUST:
- Include concrete examples (not abstract descriptions)
- Provide command-line usage with actual commands
- Document both Windows (PowerShell) and cross-platform (Python) workflows
- Link to canonical data model documentation

## Governance

### Amendment Process

Constitution amendments require:
1. Proposal documenting rationale and impact analysis
2. Review of affected templates in `.specify/templates/`
3. Version increment following semantic versioning
4. Update of Sync Impact Report (HTML comment at top of file)
5. Commit message format: `docs: amend constitution to vX.Y.Z (summary)`

### Compliance Verification

All pull requests MUST verify compliance with:
- Data schema validation (automated via `validate-json.py`)
- Speckit workflow adherence (spec file presence for features)
- Algorithmic integrity (scoring formula unchanged unless documented)
- Data provenance completeness (required fields populated)

### Conflict Resolution

When this constitution conflicts with other guidance:
1. Constitution supersedes all other documentation
2. `Documentation/DataSetDesign.md` supersedes implementation details
3. JSON schema supersedes code comments or informal specs

For runtime development guidance, consult `CLAUDE.md`.

**Version**: 1.0.0 | **Ratified**: 2026-01-15 | **Last Amended**: 2026-01-15
