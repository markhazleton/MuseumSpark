# GitHub Copilot Instructions for MuseumSpark

**Version**: 2.0.0  
**Created**: 2026-01-24  
**Last Updated**: 2026-01-26  
**Authority**: Aligned with Constitution v2.0.0 and MasterRequirements.md v1.0

This document provides comprehensive guidance for GitHub Copilot when working with the MuseumSpark codebase. It integrates GitHub Copilot best practices with MuseumSpark's constitutional principles and repository patterns.

## 🎯 Project Context

MuseumSpark is a Museum Trip Planning Application designed to help **Walker Art Reciprocal Program members** rank, document, and plan visits to every museum in the reciprocal program. The application enables filtering, sorting, and evaluating reciprocal museums based on collection relevance, cultural significance, and visit practicality.

**Key Characteristics**:
- **Early-stage project**: Comprehensive design documentation with evolving implementation
- **Specification-driven**: Uses SpecKit workflow (Specify → Clarify → Plan → Tasks → Implement → Analyze)
- **Data-first architecture**: All features grounded in museum dataset as single source of truth
- **Quality-focused**: Non-negotiable schema validation and data provenance requirements
- **Current Phase**: Phase 1 (backbone data enrichment) — 1,269 museums, 0.08% fully enriched

**Technology Stack**:
- **Frontend**: React 19 + Vite 7 + Tailwind CSS 4 + React Router 7
- **Data Pipeline**: Python 3.11+ with Pydantic 2.x, BeautifulSoup4, html2text
- **Future Backend (Phase 4)**: FastAPI + SQLite + PydanticAI + OpenAI/Anthropic APIs
- **Deployment**: GitHub Pages (Phase 1 static site), Azure Windows VM (Phase 4 full-stack)

## � Document Hierarchy (Critical)

When making suggestions, always respect this authority chain:

1. **[.specify/memory/constitution.md](../.specify/memory/constitution.md)** — Project law, supersedes all other docs
2. **[Documentation/architecture/MasterRequirements.md](architecture/MasterRequirements.md)** — Authoritative product requirements (Product Owner)
3. **[Documentation/architecture/DataSetDesign.md](architecture/DataSetDesign.md)** — Dataset structure and methodology
4. **[data/schema/museum.schema.json](../data/schema/museum.schema.json)** — Validation rules and field definitions
5. **[Documentation/architecture/ApplicationArchitecture.md](architecture/ApplicationArchitecture.md)** — System design
6. **[Documentation/architecture/MuseumAPI.md](architecture/MuseumAPI.md)** — API specification (Phase 4)

**Never suggest changes that conflict with these documents without explicit user confirmation.**

## �📋 Constitutional Principles (NON-NEGOTIABLE)

These principles from `.specify/memory/constitution.md` override all other guidance:

### 1. Data-First Architecture
- Dataset structure in `data/schema/museum.schema.json` is authoritative
- All API, frontend, and service layers MUST conform to canonical data model
- Schema changes require formal approval and migration planning

### 2. Schema Validation (REQUIRED)
- Every museum record MUST validate against JSON Schema before acceptance
- All state files MUST pass validation via `validate-json.py` or `validate-json.ps1`
- **Validation workflow** (before every commit):
  ```bash
  python scripts/validate-json.py
  ```

### 3. Specification-Driven Development
- No code implementation without approved specification in `.specify/specs/`
- Follow SpecKit workflow: Specify → Clarify → Plan → Tasks → Implement → Analyze
- Specifications MUST reference `Documentation/architecture/DataSetDesign.md` and `Documentation/architecture/MuseumAPI.md`

### 4. Algorithmic Integrity
- Priority scoring algorithm in `Documentation/architecture/DataSetDesign.md` is canonical
- MUST NOT alter without documentation update and versioning
- All implementations MUST produce identical results given identical inputs
- Track algorithm version in `scoring_version` field

**Priority Score Formula** (MRD Section 5):
```python
# Step 1: Primary Art Strength
primary_art_strength = max(impressionist_strength, modern_contemporary_strength)

# Step 2: Base Score
priority_score = (
    (5 - primary_art_strength) * 3
    + (5 - historical_context_score) * 2
    + (5 - collection_based_strength) * 2
    + reputation_tier  # 0-3 scale: 0=International, 1=National, 2=Regional, 3=Local
)

# Step 3: Apply Bonuses (subtract from score)
if impressionist_strength >= 4 and modern_contemporary_strength >= 4:
    priority_score -= 2  # Dual-Strength Bonus

if exhibitions_curatorial_authority >= 4:
    priority_score -= 1  # ECA Bonus
```

**Scoring Dimensions**:
- **Impressionist Strength** (0-5): Depth of Impressionist permanent collection
- **Modern/Contemporary Strength** (0-5): Depth of Modern/Contemporary permanent collection
- **Historical Context Score** (0-5): Quality of historical framing and interpretation
- **Exhibitions & Curatorial Authority (ECA)** (0-5): Programmatic influence beyond permanent holdings
- **Collection-Based Strength** (0-5): Overall depth/authority across all art categories
- **Reputation Tier** (0-3): 0=International, 1=National, 2=Regional, 3=Local

**Key Points**:
- Lower scores = higher priority (can be negative for world-class museums)
- Non-art museums: `priority_score: null`, `is_scored: false`
- Museums with Historical Context = 5 flagged as potential "Must-See"

### 5. Data Provenance and Multi-Phase Enrichment
MuseumSpark uses a **multi-phase enrichment pipeline**:
- **Phase 0**: Identity verification via Wikidata
- **Phase 0.5**: Wikidata structured data extraction
- **Phase 0.7**: Official website metadata harvesting
- **Phase 1**: Backbone data (address, city tier, museum type)
- **Phase 1.5**: Wikipedia article extraction
- **Phase 1.75**: Heuristic fallback for missing fields
- **Phase 1.8**: CSV lookup integration
- **Phase 1.9**: Museum planner metadata
- **Phase 2**: Expert scoring (art museums only)
- **Phase 2.5**: Rich content extraction
- **Phase 3**: Priority score calculation

**Data Quality Guardrail**: "Never Replace Known With Null" — preserve existing data during enrichment.

**Evidence Tracking**: Every enriched field MUST include `data_sources`, `confidence`, `created_at`, `updated_at`, `address_source`

**Reproducibility**: Generated data MUST be reproducible from source data and scripts

### 6. Backward Compatibility and Versioning
- JSON schema follows semantic versioning
- Breaking changes require MAJOR version increment
- Legacy fields supported for minimum 6 months during deprecation

## 🤖 GitHub Copilot Best Practices

### Code Generation Guidelines

#### 1. Context Awareness
**Before generating code, consider**:
- Current file location in repository structure
- Related files in same module/package
- Existing patterns in similar files
- Import statements and dependencies already in use

**Example prompt**: "Generate a museum validation function that follows the pattern in scripts/validation/validate_cache_vs_state.py"

#### 2. Follow Existing Patterns
**Analyze before suggesting**:
- Naming conventions (snake_case for Python, camelCase for TypeScript)
- Code organization (separate builders/, phases/, pipeline/, validation/)
- Error handling patterns (exit codes, logging format)
- Documentation style (docstrings, inline comments)

#### 3. Type Safety and Validation
**Always include**:
- Type hints in Python (Python 3.7+ compatible)
- Interface definitions in TypeScript
- Input validation before processing
- Schema validation for data transformations

**Example**:
```python
def enrich_museum_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriches a museum record with additional metadata.
    
    Args:
        record: Museum record dict conforming to museum.schema.json
        
    Returns:
        Enriched museum record
        
    Raises:
        ValueError: If record fails schema validation
    """
    # Validate against schema first
    validate_museum_record(record)
    # ... enrichment logic
```

#### 4. Documentation-First Code
**Include**:
- Function/class docstrings with usage examples
- Inline comments for complex logic
- README updates for new scripts or modules
- Command-line usage examples in docstrings

#### 5. Test-Driven Suggestions
**When generating code, also suggest**:
- Unit tests for new functions
- Integration tests for pipeline phases
- Validation tests for data transformations
- Edge case handling

### Language-Specific Standards

#### Python Standards
**All Python code MUST**:
- Support Python 3.11+ (for modern type hints and performance)
- Handle Windows console encoding (UTF-8 wrapper for `sys.stdout`/`sys.stderr`)
- Include docstrings with usage examples
- Use `argparse` for command-line interfaces
- Exit with code 0 on success, 1 on error
- Output validation messages in format: `[OK]`, `[ERROR]`, `[WARNING]`

**Example structure**:
```python
#!/usr/bin/env python3
"""
Script description and usage example.

Usage:
    python script_name.py --input data/input.json --output data/output.json
"""

import sys
import argparse
from pathlib import Path

# UTF-8 console encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--output", required=True, help="Output file path")
    args = parser.parse_args()
    
    try:
        # Script logic
        print("[OK] Operation completed successfully")
        return 0
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

#### TypeScript/JavaScript Standards (site/)
**Follow**:
- ESLint configuration in `site/eslint.config.js`
- TypeScript strict mode enabled
- Vite build configuration in `site/vite.config.ts`
- Component-based architecture in `site/src/`

#### JSON Formatting
**All JSON files MUST**:
- Use 2-space indentation
- Include UTF-8 encoding without BOM
- End with single newline
- Use ISO 8601 format for dates (`YYYY-MM-DD`) and timestamps (`YYYY-MM-DDTHH:MM:SSZ`)

### Data Quality Standards

#### Field Completeness Requirements

**Phase 1 (Required for all records)**:
```json
{
  "museum_id": "string (unique)",
  "museum_name": "string",
  "country": "string",
  "state_province": "string",
  "city": "string",
  "street_address": "string",
  "postal_code": "string",
  "museum_type": "enum",
  "status": "enum (active/closed/seasonal/unknown)",
  "website": "string (URL)"
}
```

**Phase 2 (Required for art museums with scoring)**:
```json
{
  "impressionist_strength": "integer (0-5)",
  "modern_contemporary_strength": "integer (0-5)",
  "historical_context_score": "integer (0-5)",
  "exhibitions_curatorial_authority": "integer (0-5)",
  "collection_based_strength": "integer (0-5)",
  "reputation": "integer (0-3)",
  "primary_art": "string (Impressionist|Modern/Contemporary)",
  "primary_domain": "string",
  "is_scored": "boolean",
  "priority_score": "number|null",
  "scoring_version": "string"
}
```

**Phase 3 (Recommended for travel planning)**:
```json
{
  "estimated_visit_minutes": "integer",
  "best_season": "string",
  "parking_notes": "string",
  "latitude": "number",
  "longitude": "number",
  "timezone": "string"
}
```

#### Controlled Vocabularies

**When generating museum records, use exact enum values**:

- `reputation`: 0 (International), 1 (National), 2 (Regional), 3 (Local) — **MUST use integers, not strings**
- `collection_tier`: 0 (Flagship), 1 (Strong), 2 (Moderate), 3 (Small) — integers
- `city_tier`: 1 (Major hub), 2 (Medium city), 3 (Small town) — integers
- `museum_type`: "Art (Encyclopedic)", "Art (Modern/Contemporary)", "Art (Regional)", "Art (University)", "History", "Science", "Mixed (Art & History)", "Specialty"
- `primary_domain`: "Art", "History", "Science", "Culture", "Specialty", "Mixed"
- `time_needed`: "Quick stop" (<1 hr), "Half day" (2-4 hours), "Full day" (5+ hours)
- `status`: "active", "closed", "seasonal", "unknown"
- `address_source`: "official_website", "google_places", "wikidata", "wikipedia", "manual", "unknown"
- `scored_by`: "assistant" (LLM), "manual" (human expert), "hybrid" (combination)

### Scoring Dimension Rubrics (MRD Section 4)

When suggesting scoring values, use these rubrics:

#### Impressionist Strength (0-5)
- **5**: Canon-defining collection (field-defining works, national/international authority)
- **4**: Major scholarly collection (deep holdings with national significance)
- **3**: Strong regional or thematic collection
- **2**: Modest or supporting collection
- **1**: Limited collection presence
- **0**: No meaningful Impressionist holdings

#### Modern/Contemporary Strength (0-5)
Same scale as Impressionist Strength

#### Historical Context Score (0-5)
- **5**: Canon-level historical importance (essential for understanding major movements)
- **4**: Nationally significant context
- **3**: Strong regional context
- **2**: Local context
- **1**: Limited context
- **0**: No contextual framing

#### Exhibitions & Curatorial Authority (0-5)
- **5**: Field-shaping curatorial authority (shapes discourse nationally/internationally)
- **4**: Nationally recognized curatorial program
- **3**: Strong regional curatorial program
- **2**: Competent exhibition programming
- **1**: Minimal curatorial authority
- **0**: No curatorial program of note

#### Collection-Based Strength (0-5)
- **5**: Canon-defining collection (reference point for scholarship)
- **4**: Major scholarly collection
- **3**: Strong regional/thematic collection
- **2**: Modest/supporting collection
- **1**: Limited collection presence
- **0**: No meaningful permanent collection

## 📁 Repository Structure

### Documentation Organization

**CRITICAL**: All documentation MUST be placed in `/Documentation` folder following this structure:

```
Documentation/
├── README.md                         # Documentation index
├── Home.md                           # Full navigation guide
├── architecture/                     # System design, API specs, data models
│   ├── ApplicationArchitecture.md
│   ├── DataSetDesign.md             # Canonical data model
│   └── MuseumAPI.md                 # API specification
├── data-pipeline/                    # Enrichment strategies, LLM integration
│   └── DataEnrichmentStrategy.md
├── features/                         # Feature specifications and guides
├── reference/                        # Technical references
├── setup-deployment/                 # Configuration and deployment
│   └── API-Keys-Setup.md
├── copilot/                          # Copilot-specific documentation
│   └── session-YYYYMMDD/            # Session-specific notes
└── _source/                          # Source materials for documentation
```

**Rules**:
1. **NEVER** create markdown documents outside `/Documentation` folder
2. **ALL AI-generated documentation (.md files) MUST go to `/Documentation/copilot/session-{date}/`**
   - Session notes, analysis, summaries, work logs
   - Use format: `session-YYYYMMDD/` (e.g., `session-20260126/`)
   - **NEVER place .md files in source code folders** (`scripts/`, `site/`, `data/`, etc.)
3. Place feature documentation in `/Documentation/features/`
4. Update `/Documentation/README.md` when adding new sections
5. Link to canonical documents rather than duplicating content
6. This file (`.github/copilot-instructions.md`) is the ONLY exception to the /Documentation rule

### Code Organization

```
scripts/                              # Python data pipeline scripts
├── __init__.py
├── README.md                         # Pipeline documentation
├── requirements.txt                  # Python dependencies
├── phases/                           # Pipeline phase implementations
│   ├── phase0_google_places.py
│   ├── phase0_5_wikidata.py
│   ├── phase1_backbone.py
│   └── phase2_llm_scoring.py
├── builders/                         # Data builders and processors
├── pipeline/                         # Pipeline orchestration
└── validation/                       # Validation utilities
    ├── validate_cache_vs_state.py
    └── validate-json.py

site/                                 # Frontend application
├── package.json
├── vite.config.ts
├── tsconfig.json
├── eslint.config.js
├── src/                              # Source code
├── public/                           # Static assets
└── scripts/                          # Build/deployment scripts

data/                                 # Dataset and artifacts
├── museums.csv                       # Legacy format
├── schema/                           # JSON schemas
├── states/                           # State-specific museum records
├── index/                            # Aggregated indexes
├── cache/                            # API response caches
└── runs/                             # Pipeline run outputs
```

## 🔄 Development Workflows

### SpecKit Workflow

**For all feature development**:

1. **Specify**: Create specification in `.specify/specs/`
   ```bash
   # Use speckit.specify skill
   ```

2. **Clarify**: Identify underspecified areas
   ```bash
   # Use speckit.clarify skill
   ```

3. **Plan**: Execute implementation planning
   ```bash
   # Use speckit.plan skill
   ```

4. **Tasks**: Generate actionable tasks
   ```bash
   # Use speckit.tasks skill
   ```

5. **Implement**: Execute implementation
   ```bash
   # Use speckit.implement skill
   ```

6. **Analyze**: Cross-artifact consistency check
   ```bash
   # Use speckit.analyze skill
   ```

### Data Pipeline Workflow

**Adding/modifying museum records**:

1. Add records to `data/states/{state}.json`
2. Validate against schema:
   ```bash
   python scripts/validate-json.py
   ```
3. Fix all validation errors (MUST pass before commit)
4. Run pipeline phase to enrich:
   ```bash
   python scripts/phases/phase0_google_places.py --state {state}
   ```
5. Rebuild aggregated indexes:
   ```bash
   python scripts/build-index.py
   ```
6. Commit only when validation passes

### Schema Evolution Workflow

**Modifying the data model**:

1. Update `data/schema/museum.schema.json` with semantic version bump
2. Update `Documentation/architecture/DataSetDesign.md`
3. Create migration script if needed
4. Update affected scripts and validators
5. Test against existing dataset
6. Document in CHANGELOG

## 💡 Copilot Prompt Patterns

### Effective Prompts

#### ✅ Good Prompts (Context-rich, specific)
```
// Generate a museum enrichment function following the phase0 pattern
// Should validate record, call API, merge results, handle errors
// Include logging with [OK]/[ERROR] format per constitution

// Add a new controlled vocabulary field to museum schema
// Follow semantic versioning, update validators, add migration script
// Ensure backward compatibility per constitution principle VI
```

#### ❌ Avoid (Vague, no context)
```
// Add a function
// Fix this
// Make it better
```

### Common Tasks and Prompts

#### Adding a New Pipeline Phase
```
// Create a new pipeline phase following scripts/phases/phase0_google_places.py pattern
// Phase name: phase4_accessibility_audit
// Purpose: Audit museum websites for accessibility compliance
// Input: Museum record with website field
// Output: Add accessibility_score (1-5) and accessibility_features array
// Include: CLI args, validation, caching, error handling, logging
// Test: Validate against schema after enrichment
```

#### Adding a New Validation Rule
```
// Add validation rule to scripts/validate-json.py
// Rule: Ensure museums with reputation="International" have collection_tier="Flagship" or "Strong"
// Output: [WARNING] format per constitution
// Include: Line number reference, suggested fix
```

#### Implementing API Endpoint
```
// Implement GET /museums endpoint per Documentation/architecture/MuseumAPI.md
// Include: Query filtering, pagination, JWT auth check
// Validate: Response matches schema, error handling for malformed queries
// Test: Create integration test with sample queries
```

## 🧪 Testing Guidelines

### Testing Principles

1. **Data Validation Tests**: All data transformations must validate against schema
2. **Deterministic Tests**: Pipeline outputs must be reproducible
3. **Edge Case Coverage**: Test boundary conditions, missing data, invalid inputs
4. **Integration Tests**: Test full pipeline phases end-to-end
5. **Performance Tests**: Ensure pipeline scales to full dataset

### Test Organization

```
tests/
├── unit/                             # Unit tests for individual functions
│   ├── test_validators.py
│   ├── test_scoring.py
│   └── test_enrichment.py
├── integration/                      # Integration tests for pipeline phases
│   ├── test_phase0_integration.py
│   └── test_phase2_integration.py
└── fixtures/                         # Test data and fixtures
    ├── sample_museums.json
    └── expected_outputs.json
```

## 🚨 Common Pitfalls to Avoid

### Data Quality Issues

❌ **Don't**:
- Commit records that fail schema validation
- Modify priority scoring formula without documentation update
- Add fields without schema update
- Use inconsistent controlled vocabulary values

✅ **Do**:
- Always validate before commit
- Version schema changes semantically
- Document data sources in `address_source` and `data_sources` fields
- Use exact enum values from schema

### Code Quality Issues

❌ **Don't**:
- Implement features without specification
- Create documentation outside `/Documentation` folder
- Skip error handling in pipeline scripts
- Use hardcoded paths or credentials

✅ **Do**:
- Follow SpecKit workflow
- Place all docs in `/Documentation` with proper structure
- Use try-except with informative error messages
- Use environment variables or config files for credentials

### Documentation Violations

❌ **Don't**:
- Create .md files in `scripts/`, `site/`, `data/`, or any source code folder
- Save session notes or AI analysis outside `/Documentation/copilot/session-{date}/`
- Create README.md files in feature branches (update existing docs instead)
- Generate documentation summaries in working directories

✅ **Do**:
- Always use `/Documentation/copilot/session-YYYYMMDD/` for AI-generated content
- Update existing documentation files rather than creating new ones
- Link to canonical docs in `/Documentation/architecture/` when referencing specs

### Architecture Violations

❌ **Don't**:
- Bypass schema validation for "temporary" data
- Implement non-deterministic pipeline phases
- Create duplicate data sources
- Modify canonical documents without constitution review

✅ **Do**:
- Respect data-first architecture
- Ensure reproducibility in all data transformations
- Maintain single source of truth
- Follow amendment process for constitutional changes

## 📚 Key Reference Documents

**Always consult these before generating code**:

1. **Data Model**: [Documentation/architecture/DataSetDesign.md](architecture/DataSetDesign.md)
   - Canonical field definitions
   - Priority scoring algorithm
   - Data quality standards

2. **API Specification**: [Documentation/architecture/MuseumAPI.md](architecture/MuseumAPI.md)
   - Endpoint definitions
   - Request/response schemas
   - Authentication requirements

3. **Constitution**: `.specify/memory/constitution.md`
   - Non-negotiable principles
   - Governance and compliance
   - Amendment process

4. **Pipeline Guide**: [scripts/README.md](../scripts/README.md)
   - Phase descriptions
   - Dependencies and ordering
   - Usage examples

5. **SpecKit Templates**: `.specify/templates/`
   - Specification template
   - Plan template
   - Tasks template

## 🔍 Quick Decision Tree

**"Should I generate this code?"**

```
Is there a specification in .specify/specs/?
├─ No → Create specification first (use speckit.specify)
└─ Yes → Continue

Does it modify the data model?
├─ Yes → Update schema + DataSetDesign.md + version bump
└─ No → Continue

Does it process museum records?
├─ Yes → Validate against schema before and after
└─ No → Continue

Does it create documentation?
├─ Yes → Is it AI-generated session notes/analysis?
│   ├─ Yes → Place in /Documentation/copilot/session-YYYYMMDD/
│   └─ No → Place in /Documentation/features/ or /Documentation/architecture/
└─ No → Continue

Generate code following:
- Language-specific standards (Python/TypeScript)
- Existing patterns in similar files
- Error handling and logging conventions
- Test coverage requirements
```

## 🎓 Learning Resources

### GitHub Copilot Features to Leverage

1. **Copilot Chat**: Ask clarifying questions about patterns
2. **Inline Suggestions**: Review suggestions against constitution
3. **Code Explanations**: Understand existing patterns before extending
4. **Test Generation**: Generate tests following repository patterns

### MuseumSpark-Specific Commands

```bash
# Validate dataset
python scripts/validate-json.py

# Run pipeline phase
python scripts/phases/phase0_google_places.py --state California

# Build aggregated indexes
python scripts/build-index.py

# Check field completeness
python scripts/analyze_missing.py

# Validate cache consistency
python scripts/validate_cache_vs_state.py
```

## 📝 Version History

| Version | Date       | Changes                                      |
|---------|------------|----------------------------------------------|
| 2.0.0   | 2026-01-26 | MAJOR: Corrected scoring algorithm to match MRD v1.0, added document hierarchy, updated to Constitution v2.0, added ECA and collection_based_strength fields, clarified reputation as integer scale |
| 1.0.0   | 2026-01-24 | Initial creation integrating constitution    |

---

## 🎓 Summary: Key Points for AI Assistants

### Always Remember
1. **MasterRequirements.md drives all decisions** — it's the Product Owner's authoritative spec
2. **Constitution v2.0.0 is project law** — never contradict it
3. **Reputation uses integers (0-3)** — not strings like "International"
4. **Scoring uses 6 dimensions** — don't forget ECA and collection_based_strength
5. **Lower priority scores = higher priority** — can be negative
6. **Validate before every commit** — `python scripts/validation/validate-json.py`
7. **State files are canonical** — index files are derived (rebuild via build-index.py)
8. **Never Replace Known With Null** — preserve existing data during enrichment
9. **Python 3.11+ required** — use modern type hints
10. **AI-generated docs ONLY in /Documentation/copilot/session-{date}/** — never in source folders

### Quick Validation Checklist
- [ ] Does this change align with the constitution?
- [ ] Does this respect the MasterRequirements.md scoring algorithm?
- [ ] Have I used integer scales for reputation/collection_tier/city_tier?
- [ ] Have I validated against the JSON schema?
- [ ] Have I preserved existing non-null values?
- [ ] Have I tracked provenance with data_sources/address_source?
- [ ] Have I followed the Python 3.11+ standards?
- [ ] Have I placed AI-generated docs in /Documentation/copilot/session-YYYYMMDD/ (not in source folders)?

---

**For runtime development guidance, consult [CLAUDE.md](../CLAUDE.md).**

**For constitutional principles, consult [.specify/memory/constitution.md](../.specify/memory/constitution.md).**

**For product requirements, consult [Documentation/architecture/MasterRequirements.md](architecture/MasterRequirements.md).**

**For complete documentation index, visit [Documentation/README.md](README.md).**
