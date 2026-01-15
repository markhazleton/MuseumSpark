# Museum Data Directory

This directory contains the MuseumSpark dataset (seeded from the Walker Art Reciprocal Program roster), JSON schema for validation, and generated index files.

## Directory Structure

```
data/
├── states/              # State-specific museum data files
│   ├── AL.json         # Alabama museums
│   ├── AK.json         # Alaska museums
│   ├── CA.json         # California museums
│   └── ...             # All 50 U.S. states + territories
├── schema/             # JSON Schema definitions
│   └── museum.schema.json
├── index/              # Generated index files
│   ├── all-museums.json
│   └── walker-reciprocal.csv  # Seed roster extracted from Walker reciprocal membership list
└── README.md           # This file

## Dataset Workflow (Walker Reciprocal → Master List → State Files)

1. Validate `data/index/walker-reciprocal.csv`
2. Add all museums to `data/index/all-museums.json` (master list used by the app)
3. Add museums by state to `data/states/{state}.json` and enrich each record until complete
```

## File Naming Convention

Files are named using standard two-letter state/territory abbreviations:

- **U.S. States**: `AL.json` (Alabama), `AK.json` (Alaska), `CA.json` (California), etc.
- **U.S. Territories**: `PR.json` (Puerto Rico), `VI.json` (Virgin Islands), etc.
Walker’s reciprocal membership includes international entries. The canonical record fields support non-US locations; file partitioning conventions for international records should avoid conflicts with US state codes.

## State JSON File Format

Each state file contains metadata and an array of museum objects:

```json
{
  "state": "California",
  "state_code": "CA",
  "last_updated": "2026-01-15T00:00:00Z",
  "museums": [
    {
      "country": "USA",
      "state_province": "California",
      "city": "Los Angeles",
      "museum_name": "Museum Name",
      "website": "https://example.com",
      "museum_type": "Fine Art",
      "reputation": "International",
      "collection_tier": "Flagship",
      "time_needed": "Full day",
      "impressionism_strength": "Strong",
      "modern_strength": "Flagship",
      "primary_art_focus": "Modern",
      "historical_context_score": 4,
      "priority_score": null,
      "nearby_museum_count": 5,
      "notes": "Notable collections and travel tips"
    }
  ]
}
```

## Field Definitions

### Required Fields

- **museum_name** (string): Official museum name
- **country** (string): Country name (e.g., "USA")
- **state_province** (string): Full state or province name
- **city** (string): City name
- **museum_type** (string): Primary museum type

### Optional Metadata Fields

- **website** (string): Museum website URL (must be valid HTTP/HTTPS URI)
- **reputation** (enum): Cultural significance tier
- **collection_tier** (enum): Collection size and depth
- **time_needed** (enum): Estimated visit duration

### Optional Scoring Fields

- **impressionism_strength** (enum): Impressionist collection strength
- **modern_strength** (enum): Modern/contemporary collection strength
- **primary_art_focus** (string): Dominant art period or collection focus
- **historical_context_score** (integer): Interpretive/curatorial strength (1-5)
- **priority_score** (number): Computed priority ranking (lower = higher priority, leave as `null` for auto-calculation)
- **nearby_museum_count** (integer): Number of other museums in the same city

### Additional Fields

- **notes** (string): Travel tips, highlights, or additional context

## Enum Values

### museum_type
- `Fine Art` - Visual arts museum
- `Art` - General art museum
- `History` - History museum
- `Science` - Science/natural history museum
- `Mixed` - Multiple disciplines
- `Specialty` - Specialized focus

### reputation
- `Local` - Local significance
- `Regional` - Regional significance (multi-county or state-level)
- `National` - National significance
- `International` - International significance

### collection_tier
- `Small` - Small collection
- `Moderate` - Moderate-sized collection
- `Strong` - Strong/large collection
- `Flagship` - World-class flagship collection

### time_needed
- `Quick stop` - Under 1 hour
- `Half day` - 2-4 hours
- `Full day` - 4+ hours

### impressionism_strength / modern_strength
- `None` - No significant collection
- `Minor` - Minor holdings
- `Moderate` - Moderate collection
- `Strong` - Strong collection
- `Flagship` - World-class collection

## Data Entry Guidelines

1. **Use consistent capitalization**: Follow the exact enum values listed above
2. **Validate URLs**: Ensure website URLs are complete and functional
3. **Leave priority_score as null**: Priority scores are calculated programmatically
4. **Update last_updated**: Change the timestamp when modifying a state file
5. **Use official museum names**: Use the official name as shown on the museum's website
6. **Provide notes**: Include helpful travel tips, must-see collections, or practical information

## Validation

Before committing changes, validate your JSON files:

**Using Python:**
```bash
python scripts/validate-json.py
python scripts/validate-json.py --state AL
```

**Using PowerShell:**
```powershell
.\scripts\validate-json.ps1
.\scripts\validate-json.ps1 -State AL
```

## Index Generation

Generate the consolidated `all-museums.json` index file:

```bash
# Basic index generation
python scripts/build-index.py

# With priority score calculation
python scripts/build-index.py --calculate-scores
```

The index file will be created at `data/index/all-museums.json`.

## Priority Score Calculation

Priority scores are calculated using the formula from `Documentation/DataSetDesign.md`:

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

**Strength to Numeric Mapping:**
- None: 0
- Minor: 1
- Moderate: 2
- Strong: 3
- Flagship: 5

Lower scores indicate higher priority for visit planning.

## Data Quality Standards

- All museum names must be unique within a city
- Website URLs must be valid HTTP/HTTPS URIs
- City names should match official U.S. Census naming where possible
- Enum values must match schema definitions exactly (case-sensitive)
- Historical context scores must be integers 1-5
- Nearby museum count can be auto-calculated or manually maintained
