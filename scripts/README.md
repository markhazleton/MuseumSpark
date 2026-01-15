# MuseumSpark Data Management Scripts

This directory contains scripts for validating and managing the MuseumSpark museum dataset.

MuseumSpark’s primary museum universe is the **Walker Art Reciprocal Program** roster, extracted into `data/index/walker-reciprocal.csv`.

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

## Priority Score Calculation

The `build-index.py` script implements the MuseumSpark priority scoring algorithm:

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

**Strength Mapping:**
- None: 0, Minor: 1, Moderate: 2, Strong: 3, Flagship: 5

**Reputation Mapping:**
- Local: 1, Regional: 2, National: 3, International: 4

**Collection Tier Mapping:**
- Small: 1, Moderate: 2, Strong: 3, Flagship: 4

Lower scores indicate higher priority for visit planning.

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
