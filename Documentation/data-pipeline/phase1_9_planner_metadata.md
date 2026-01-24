# Phase 1.9: Museum Planner Metadata Integration

## Overview

Phase 1.9 enriches museum records with product owner metadata from the `museum_planner_MASTER` spreadsheet. This phase enables the integration of manually curated scores, notes, and planning metadata that evolve over time as the product owner adds their own research and observations.

## Purpose

The product owner maintains a master planning spreadsheet (`museum_planner_MASTER_*.xlsx`) with:
- Manual priority scores and tier assignments
- Collection strength assessments (Impressionist, Modern/Contemporary, Traditional)
- Exhibition-focused vs. collection-focused advantage scores
- Curatorial notes and observations
- Planning metadata for visit prioritization

This phase syncs that spreadsheet data into the museum records, making it available for:
- Visit planning algorithms
- Priority scoring  
- Collection strength visualization
- Product owner review and validation

## Fields Added

All fields are prefixed with `planner_` to distinguish them from automated enrichment:

### Priority & Tier
- **planner_priority_score** (integer): Product owner's overall priority score
- **planner_outcome_tier** (string): Tier assignment (e.g., "High Priority", "Consider", "Maybe")
- **planner_consider_label** (string): Descriptive label (e.g., "World-Class Encyclopedic", "Regional Art Center")

### Collection Strength Scores (0-5 scale)
- **planner_historical_context** (integer): Historical context/documentation score
- **planner_impressionist_strength** (integer): Strength in Impressionist art
- **planner_modern_contemporary_strength** (integer): Strength in Modern/Contemporary art  
- **planner_traditional_strength** (integer): Strength in Traditional/Pre-Modern art

### Planning Scores
- **planner_exhibition_advantage** (integer): Exhibition-centric advantage (ECA) score
- **planner_collection_pas** (integer): Collection-based Priority Art Score
- **planner_effective_pas** (integer): Effective Priority Art Score (combined metric)

### Quality Indicators
- **planner_reputation_level** (string): Reputation level (World-Class, National, Regional, Local)
- **planner_collection_level** (string): Collection level (Exceptional, Strong, Modest, Small)
- **planner_notes** (string): Product owner notes and observations

### Metadata
- **planner_data_updated_at** (timestamp): When planner data was last synced
- **data_sources** array: Adds "museum_planner_spreadsheet" entry

## Design Principles

### 1. Product Owner Authority
The spreadsheet is the single source of truth for planner metadata. Phase 1.9 respects manual curation and doesn't override or second-guess product owner decisions.

### 2. Idempotent Updates
Running Phase 1.9 multiple times is safe and expected:
- Re-running updates museums with latest spreadsheet data
- Only updates fields that have changed
- Skips museums if spreadsheet hasn't changed since last sync (unless `--force`)
- Product owner can edit spreadsheet and re-sync at any time

### 3. Smart Caching
- Tracks spreadsheet modification time vs. last sync timestamp
- Skips museums that are already current (spreadsheet older than last sync)
- Only updates fields with actual value changes
- Reports "skipped" vs. "updated" for transparency
- `--force` flag overrides caching to force re-sync

### 4. Clean Separation
Planner fields are prefixed (`planner_*`) to avoid confusion with:
- Automated enrichment fields (phase0, phase1, phase2)
- LLM-generated content
- External API data

### 4. Flexible Matching
Museums are matched by name using:
- Normalized name comparison (case-insensitive, punctuation removed)
- Fuzzy matching for slight name variations
- Typically achieves 95%+ match rate

## Usage

### Process Single State
```bash
python scripts/phases/phase1_9_planner_metadata.py --state CA
```

### Process Multiple States
```bash
python scripts/phases/phase1_9_planner_metadata.py --states CA,NY,MA
```

### Process All States
```bash
python scripts/phases/phase1_9_planner_metadata.py --all-states
```

### Dry Run (Preview Changes)
```bash
python scripts/phases/phase1_9_planner_metadata.py --state CA --dry-run
```

### Force Re-sync (Ignore Cache)
```bash
python scripts/phases/phase1_9_planner_metadata.py --state CA --force
```

### Specify Custom Spreadsheet
```bash
python scripts/phases/phase1_9_planner_metadata.py --all-states --spreadsheet path/to/file.xlsx
```

If no spreadsheet is specified, Phase 1.9 automatically finds the most recent `museum_planner_MASTER_*.xlsx` file in `Documentation/_source/`.

## Caching & Performance

### How Caching Works

Phase 1.9 intelligently skips re-work:

1. **Spreadsheet Timestamp Check**
   - Compares spreadsheet modification time vs. `planner_data_updated_at` for each museum
   - If spreadsheet is older than last sync, skips that museum
   - Dramatically speeds up repeat runs when spreadsheet hasn't changed

2. **Field-Level Change Detection**
   - Only updates fields where values actually changed
   - Doesn't rewrite identical data
   - Reports count of fields that changed

3. **Force Override**
   - `--force` flag bypasses all caching
   - Forces re-sync of all matched museums
   - Useful after manual state file edits

### Performance Comparison

**First run** (no museums synced):
- Processes 179 museums: ~5 seconds
- Updates all 172 matched: ~3 seconds
- **Total: ~8 seconds**

**Second run** (spreadsheet unchanged):
- Processes 179 museums: ~5 seconds
- Skips all 172 (already current): instant
- **Total: ~5 seconds** (40% faster)

**Third run** (25 museums updated in spreadsheet):
- Processes 179 museums: ~5 seconds
- Updates 25 museums: ~1 second
- Skips 147 museums: instant
- **Total: ~6 seconds**

### When Museums Are Skipped

A museum is skipped as "current" when:
- It has `planner_data_updated_at` timestamp
- Spreadsheet modification time ≤ last sync timestamp
- `--force` flag is NOT used

A museum is skipped as "no changes" when:
- All planner fields already match spreadsheet values
- No fields need updating

## Typical Workflow

1. **Product Owner Updates Spreadsheet**
   - Adds new museums
   - Updates scores and notes
   - Revises tier assignments
   - Adds curatorial observations

2. **Run Phase 1.9**
   ```bash
   python scripts/phases/phase1_9_planner_metadata.py --all-states
   ```

3. **Review Results**
   - Check match rate (typically 95%+)
   - Review museums not matched (if any)
   - Verify updates in state files

4. **Iterate as Needed**
   - Product owner continues refining spreadsheet
   - Re-run Phase 1.9 to sync latest changes
   - Rinse and repeat

## Spreadsheet Format

Expected columns (case-insensitive, flexible matching):
- **Museum Name** (required): Used for matching
- **Priority Score**: Overall priority (integer)
- **Outcome Tier**: Tier assignment (string)
- **Consider Label**: Descriptive label (string)
- **Historical Context**: Score 0-5
- **Impressionist Strength**: Score 0-5
- **Modern/ Contemporary Strength**: Score 0-5
- **Traditional / Pre‑Modern Art Strength**: Score 0-5
- **Exhibition-Centric Advantage (ECA)**: Integer score
- **Collection-Based PAS**: Integer score
- **Effective PAS**: Integer score
- **Reputation Level**: Text (World-Class, National, etc.)
- **Collection Level**: Text (Exceptional, Strong, etc.)
- **Notes**: Product owner observations (text)

Additional columns in the spreadsheet are ignored. Missing/blank values are treated as null (not added to museum record).

## Output

### Run Summary
After each run, Phase 1.9 creates a run directory:
```
data/runs/phase1_9-YYYYMMDD-HHMMSS/
  summary.json     # Statistics and metadata
```

### Statistics Reported
- Total museums processed
- Museums matched successfully
- Museums updated (had changes)
- Museums not found in state files
- Fields updated (count)
- Match rate (percentage)

### Example Output
```
============================================================
Phase 1.9 Complete
============================================================
  Total processed:      179
  Museums matched:      172  
  Museums updated:      23
  Skipped (current):    142
  Skipped (no changes): 7
  Museums not found:    7
  Fields updated:       276
  Match rate:           96.1%
```

## Integration with Other Phases

Phase 1.9 is designed to work alongside other enrichment phases:

- **Phase 0**: Identity and backbone data (doesn't conflict)
- **Phase 1**: Wikipedia, Wikidata, CSV enrichment (doesn't conflict)
- **Phase 2**: LLM scoring (planner scores can override or supplement)
- **Future phases**: Planner metadata can inform prioritization and planning

## Troubleshooting

### Low Match Rate
If match rate is below 90%:
1. Check museum names in spreadsheet match state file names
2. Look for typos or formatting differences
3. Review "museums not found" list in output
4. Consider adding alternate names to museum records

### No Spreadsheet Found
If Phase 1.9 can't find the spreadsheet:
1. Verify file exists in `Documentation/_source/`
2. Check filename starts with `museum_planner_MASTER`
3. Ensure file extension is `.xlsx`
4. Or specify path explicitly with `--spreadsheet`

### Fields Not Updating
If museums match but fields don't update:
1. Check spreadsheet has values in those columns
2. Verify column names match expected format
3. Look for blank/NaN values in spreadsheet
4. Try `--force` to bypass caching
5. Check if spreadsheet is newer than last sync (file modification time)
6. Review run output for specific museum details

### Museums Showing as "Skipped (current)"?
This is normal and good for performance:
- Means spreadsheet hasn't changed since last sync
- Museums are already up-to-date
- Use `--force` if you want to re-sync anyway
- Edit spreadsheet to trigger updates on next run

## Future Enhancements

Potential improvements for Phase 1.9:

1. **Bidirectional Sync**: Export state file data back to spreadsheet for review
2. **Conflict Resolution**: Flag where planner scores differ significantly from automated scores
3. **Change Tracking**: Log what changed between runs for audit trail
4. **Match Quality**: Report fuzzy match confidence scores
5. **Bulk Import**: Support multiple spreadsheet tabs or files for different museum types

## Example: Before and After

### Before Phase 1.9
```json
{
  "museum_name": "Anchorage Museum",
  "city": "Anchorage",
  "state_province": "Alaska",
  "museum_type": "Art Museum",
  "reputation": 3,
  "collection_tier": 3
}
```

### After Phase 1.9
```json
{
  "museum_name": "Anchorage Museum",
  "city": "Anchorage",
  "state_province": "Alaska",
  "museum_type": "Art Museum",
  "reputation": 3,
  "collection_tier": 3,
  "planner_priority_score": 8,
  "planner_outcome_tier": "High Priority",
  "planner_reputation_level": "National",
  "planner_collection_level": "Strong",
  "planner_historical_context": 4,
  "planner_impressionist_strength": 2,
  "planner_modern_contemporary_strength": 3,
  "planner_traditional_strength": 2,
  "planner_exhibition_advantage": 4,
  "planner_collection_pas": 3,
  "planner_effective_pas": 4,
  "planner_notes": "Flagship multidisciplinary institution...",
  "planner_data_updated_at": "2026-01-24T21:25:52Z",
  "data_sources": ["...", "museum_planner_spreadsheet"]
}
```

## See Also

- [Phase 1 Backbone](phase1_backbone.py) - Deterministic enrichment
- [Phase 1.8 CSV Lookup](phase1_8_csv_lookup.py) - IRS 990 database enrichment
- [Phase 2 Scoring](phase2_scoring.py) - Automated LLM scoring
- [Data Pipeline Overview](../../Documentation/data-pipeline/README.md)
