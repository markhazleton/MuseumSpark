# MuseumSpark Data Management Scripts

This directory contains scripts for validating and managing the MuseumSpark museum dataset.

## Open-data-first enrichment (Pre-MRD Phase + Phase 1)

### Pre-MRD Phase: Open Data Enrichment

**Goal**: Populate as many MRD-required fields as possible from **free/open data sources** before using LLM enrichment.

The `enrich-open-data.py` script uses Wikidata, Wikipedia, OpenStreetMap Nominatim, and optional website scraping to populate:

**MRD Fields Populated by Open Data:**
- `city_tier` (1-3): Computed from city population data + manual major hub list
- `reputation` (0-3): Inferred from Wikidata sitelink counts (International/National/Regional/Local)
- `collection_tier` (0-3): Inferred from Wikidata collection size claims (Flagship/Strong/Moderate/Small)
- `time_needed`: Heuristic inference from `museum_type` keywords
- `street_address`, `postal_code`, `latitude`, `longitude`: From Wikidata or Nominatim
- `website`: From Wikidata or Walker roster

**Usage:**

```bash
# Pre-MRD Phase: Enrich single state with MRD field computation
python scripts/enrich-open-data.py --state IL --compute-mrd-fields --rebuild-index --rebuild-reports

# Enrich placeholder museums only (conservative, dry run first)
python scripts/enrich-open-data.py --state CA --only-placeholders --compute-mrd-fields --dry-run
python scripts/enrich-open-data.py --state CA --only-placeholders --compute-mrd-fields --rebuild-index

# Enrich with website scraping (slower, more comprehensive)
python scripts/enrich-open-data.py --state NY --compute-mrd-fields --scrape-website --rebuild-index

# Enrich specific museum by ID
python scripts/enrich-open-data.py --museum-id usa-il-chicago-art-institute --compute-mrd-fields --rebuild-index
```

**Workflow (Pre-MRD Phase → Phase 1):**

1. **Pre-MRD Phase**: Run `enrich-open-data.py --compute-mrd-fields` on each state to populate MRD fields from open data
2. **Phase 1**: Fill remaining gaps using LLM-assisted enrichment (reputation, collection_tier refinement)
3. **Phase 2**: Expert scoring of art museums (impressionist_strength, modern_contemporary_strength, historical_context_score)
4. **Phase 3**: Regional rollout (Illinois/Midwest → Northeast → California → Remaining states)

**Regional Priority (MRD):**
1. Illinois / Midwest anchors
2. Northeast cluster (Boston, NYC, Philadelphia, DC)
3. California (LA, SF, San Diego)
4. Remaining U.S. states
5. Canada, Mexico, Bermuda

### Phase 1 Pipeline (after Pre-MRD enrichment)

These scripts help you fill missing fields using free/open sources first, then generate a deterministic gap report.

```bash
# 1) Enrich placeholder records in a state file (conservative fill-only)
python scripts/enrich-open-data.py --state CA --only-placeholders --limit 25

# (Optional) Also scrape the museum website to extract structured links/fields
python scripts/enrich-open-data.py --state CA --only-placeholders --limit 25 --scrape-website

# (Optional) Rebuild derived artifacts after enrichment
python scripts/enrich-open-data.py --state CA --only-placeholders --limit 25 --rebuild-index --rebuild-reports

# 2) Generate a missing-field report from the combined index
python scripts/build-missing-report.py

# 3) Generate a small progress dashboard artifact for the static site UI
python scripts/build-progress.py
```

### One-command Phase 1 pipeline

If you want the correct Phase 1 sequence (optional enrich → validate → rebuild index → rebuild reports) in a single command:

```bash
# Enrich a state then rebuild derived artifacts
python scripts/run-phase1-pipeline.py --state CA --only-placeholders --limit 25

# Rebuild derived artifacts only (no enrichment)
python scripts/run-phase1-pipeline.py --skip-enrich
```

Notes:
- `enrich-open-data.py` writes cached HTTP responses under `data/cache/` (ignored by git).
- Run `python build-index.py --calculate-scores --update-nearby-counts` after enrichment to recompute MRD fields.
- Use `--dry-run` first if you want to preview changes without writing.

MuseumSpark's primary museum universe is the **Walker Art Reciprocal Program** roster, extracted into `data/index/walker-reciprocal.csv`.

## LLM Enrichment Pipeline (Phase 2+)

The `enrich-llm.py` orchestrator runs the validation and deep dive agents described in
`Documentation/AI-LLM-Enrichment-Plan.md`.

**Features:**
- Field-level provenance and trust enforcement
- Recommend-vs-write guardrails for high-churn ranking fields
- Evidence packet shaping and token-budget governance
- QA gates (validation failure rate, gold-set drift)

**Usage:**

```bash
# Run validation agent for a single state (OpenAI)
python scripts/enrich-llm.py --state IL --provider openai --validation-model gpt-4o-mini

# Run validation + deep dive for top 100 art museums
python scripts/enrich-llm.py --state IL --top-n 100 --provider openai --deep-dive-model gpt-4o

# Process a single museum
python scripts/enrich-llm.py --museum-id usa-il-chicago-art-institute-of-chicago
```

**Notes:**
- Requires `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.
- Run artifacts are stored under `data/runs/{run_id}/`.

## Scripts Overview

## Dataset Workflow (Walker Reciprocal → Master List → State Files)

1. **Validate the Walker reciprocal roster** (`data/index/walker-reciprocal.csv`)
2. **Add all museums to** `data/index/all-museums.json` (master list used by the app)
3. **Add museums by state to** `data/states/{state}.json` and progressively enrich records until complete

Recommended command sequence:
```bash
python scripts/validate-walker-reciprocal-csv.py
python scripts/ingest-walker-reciprocal.py --rebuild-index
```

### build-museum-list-csv-from-narm.py
Builds a structured CSV of every museum listed in `Documentation/_source/NARM-Winter-2025.pdf`.

**Features:**
- Extracts museums from the NARM roster PDF
- Writes `data/index/museum-list.csv`
- Adds a `source` column set to `NARM-2025`
- Merges in metadata from `data/index/all-museums.json` when a match is found

**Usage:**
```bash
python scripts/build-museum-list-csv-from-narm.py
```

### build-walker-reciprocal-csv.py
Builds a structured CSV of every museum listed in Walker’s reciprocal membership list (HTML snapshot stored at `Documentation/_source/walker-reciprocal.html`).

**Features:**
- Extracts one row per museum link
- Writes `data/index/walker-reciprocal.csv`
- Columns: `STATE`, `NAME`, `CITY`, `URL`

**Usage:**
```bash
python scripts/build-walker-reciprocal-csv.py
```

### validate-walker-reciprocal-csv.py
Validates `data/index/walker-reciprocal.csv` for required columns, required fields, URL shape, and common scrape artifacts.

**Usage:**
```bash
python scripts/validate-walker-reciprocal-csv.py
```

### ingest-walker-reciprocal.py
Ingests the validated roster into per-state working files under `data/states/` (adds stub records for missing museums), then optionally rebuilds `data/index/all-museums.json`.

**Usage:**
```bash
python scripts/ingest-walker-reciprocal.py --rebuild-index
```

### validate-json.py
Python script to validate state JSON files against the museum schema.

**Features:**
- Validates JSON syntax
- Validates against JSON Schema (data/schema/museum.schema.json)
- Reports detailed validation errors
- Can validate all files or a specific state

**Usage:**
```bash
# Validate all state files
python validate-json.py

# Validate specific state
python validate-json.py --state AL
python validate-json.py --state CA
```

**Requirements:**
- Python 3.7+
- jsonschema library (install via `pip install -r requirements.txt`)

### validate-json.ps1
PowerShell script to validate state JSON files.

**Features:**
- Validates JSON syntax
- Checks for required fields
- Cross-platform (Windows, macOS, Linux with PowerShell Core)
- Can validate all files or a specific state

**Usage:**
```powershell
# Validate all state files
.\validate-json.ps1

# Validate specific state
.\validate-json.ps1 -State AL
.\validate-json.ps1 -State CA
```

**Requirements:**
- PowerShell 5.1+ (Windows) or PowerShell Core 7+ (cross-platform)

### build-index.py
Python script to generate consolidated museum index file.

**Features:**
- Combines all state JSON files into single index
- Calculates priority scores using MuseumSpark formula
- Recalculates nearby_museum_count by city
- Generates timestamped output

**Usage:**
```bash
# Basic index generation (preserves existing scores)
python build-index.py

# Calculate/recalculate priority scores
python build-index.py --calculate-scores

# Update nearby museum counts
python build-index.py --update-nearby-counts

# Both operations
python build-index.py --calculate-scores --update-nearby-counts
```

**Output:**
- Creates/updates `data/index/all-museums.json`

**Requirements:**
- Python 3.7+
- No external dependencies (uses standard library only)

## Installation

### Python Dependencies

Install Python dependencies using pip:

```bash
# From the scripts directory
pip install -r requirements.txt

# Or from project root
pip install -r scripts/requirements.txt
```

**Recommended:** Use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r scripts/requirements.txt
```

### PowerShell

PowerShell is pre-installed on Windows. For macOS/Linux:

```bash
# macOS (via Homebrew)
brew install powershell

# Linux (Ubuntu/Debian)
sudo apt-get install -y powershell
```

## Workflow

### Adding New Museums

1. Edit the appropriate state JSON file in `data/states/`
2. Add museum objects following the format in `data/README.md`
3. Leave `priority_score` as `null`
4. Validate your changes:
   ```bash
   python scripts/validate-json.py --state XX
   ```
5. Rebuild the index:
   ```bash
   python scripts/build-index.py --calculate-scores --update-nearby-counts
   ```
6. Commit your changes

### Creating New State Files

1. Copy an existing state file as a template (e.g., `AL.json`)
2. Update the `state`, `state_code`, and `last_updated` fields
3. Replace the museums array with your data
4. Validate:
   ```bash
   python scripts/validate-json.py --state XX
   ```
5. Rebuild the index:
   ```bash
   python scripts/build-index.py --calculate-scores --update-nearby-counts
   ```

### Bulk Validation

Before committing changes, always validate all files:

```bash
# Python
python scripts/validate-json.py

# PowerShell
.\scripts\validate-json.ps1
```

## Priority Score Calculation (MRD v1.0)

The `build-index.py` script implements the exact MRD priority scoring formula:

```
Primary Art Strength = max(impressionist_strength, modern_contemporary_strength)

Dual-Strength Bonus = (impressionist_strength ≥ 4 AND modern_contemporary_strength ≥ 4) ? 2 : 0

Priority Score = 
  (6 – Primary Art Strength) × 3
  + (6 – Historical Context Score) × 2
  + Reputation Penalty (0-3)
  + Collection Penalty (0-3)
  – Dual Strength Bonus
```

**MRD Field Mappings:**

**Impressionist/Modern Strength (1-5):**
- 1 = None, 2 = Minor, 3 = Moderate, 4 = Strong, 5 = Flagship

**Historical Context Score (1-5):**
- 1 = Minimal, 3 = Inconsistent, 5 = Strong narrative

**Reputation (0-3 numeric):**
- 0 = International, 1 = National, 2 = Regional, 3 = Local

**Collection Tier (0-3 numeric):**
- 0 = Flagship, 1 = Strong, 2 = Moderate, 3 = Small

**City Tier (1-3):**
- 1 = Major hub (Chicago, NYC, LA, etc.)
- 2 = Medium city (population 50k-500k or special cultural significance)
- 3 = Small town (<50k population)

Lower scores indicate higher priority for visit planning.

### MRD-Compliant Fields

The script automatically computes:
- `city_tier` (1-3 based on city classification)
- `nearby_museum_count` (count of other museums in same city)
- `primary_art` (derived from strength scores: "Impressionist" or "Modern/Contemporary")
- `is_scored` (boolean flag: true if art museum with complete scoring)
- `priority_score` (computed via MRD formula for art museums only)

### FULL Record Definition (MRD)

A museum is considered **FULL** when:
1. All schema required fields are present
2. All MRD core fields are present (`city_tier`, `reputation`, `collection_tier`, `time_needed`, `nearby_museum_count`, etc.)
3. **For art museums**: ALL scoring fields must be present and `priority_score` must be computed

Non-art museums remain in the dataset with `is_scored: false` and `priority_score: null`.

## Troubleshooting

### Python: ModuleNotFoundError: No module named 'jsonschema'

**Solution:** Install dependencies:
```bash
pip install -r scripts/requirements.txt
```

### Python: ModuleNotFoundError: No module named 'pdfplumber'

**Solution:** Install dependencies (includes `pdfplumber` used by `build-museum-list-csv-from-narm.py`):
```bash
pip install -r scripts/requirements.txt
```

### PowerShell: Script cannot be loaded because running scripts is disabled

**Solution:** Enable script execution (Windows):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Validation errors: "Invalid JSON"

**Solution:** Use a JSON validator/linter to check syntax:
- Online: https://jsonlint.com/
- VS Code: Install "JSON" extension for syntax highlighting
- Command line: `python -m json.tool < file.json`

### Permission denied when running scripts

**Solution:** Make scripts executable (macOS/Linux):
```bash
chmod +x scripts/validate-json.py
chmod +x scripts/build-index.py
```

## Additional Resources

- **Data Model**: See `Documentation/DataSetDesign.md` for complete data model specification
- **API Specification**: See `Documentation/MuseumAPI.md` for REST API design
- **Data README**: See `data/README.md` for field definitions and data entry guidelines
