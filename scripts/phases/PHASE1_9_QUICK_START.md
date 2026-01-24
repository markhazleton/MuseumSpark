# Phase 1.9 Quick Reference

## What It Does

Phase 1.9 syncs product owner metadata from the `museum_planner_MASTER` spreadsheet into museum records. This lets you maintain manual curation, scores, and notes in an Excel spreadsheet and automatically integrate them into the museum data pipeline.

## Quick Start

### Update All Museums
```bash
python scripts/phases/phase1_9_planner_metadata.py --all-states
```

### Update One State
```bash
python scripts/phases/phase1_9_planner_metadata.py --state CA
```

### Preview Changes (Dry Run)
```bash
python scripts/phases/phase1_9_planner_metadata.py --state CA --dry-run
```

### Force Re-sync (Bypass Cache)
```bash
python scripts/phases/phase1_9_planner_metadata.py --state CA --force
```

## Typical Workflow

1. **Update the Spreadsheet**
   - Open `Documentation/_source/museum_planner_MASTER_*.xlsx`
   - Add/update scores, notes, tier assignments
   - Save the file

2. **Run Phase 1.9**
   ```bash
   python scripts/phases/phase1_9_planner_metadata.py --all-states
   ```

3. **Review Results**
   - Check match rate (should be 95%+)
   - Look for museums not matched
   - Verify updates in state JSON files

4. **Commit Changes**
   - State files are updated with `planner_*` fields
   - Safe to commit to version control

## Fields Added

All fields go into museum records with `planner_` prefix:

### Scores & Tiers
- `planner_priority_score` - Your manual priority (integer)
- `planner_outcome_tier` - Tier label (e.g., "High Priority")
- `planner_consider_label` - Description (e.g., "World-Class Encyclopedic")

### Collection Strengths (0-5 scale)
- `planner_impressionist_strength`
- `planner_modern_contemporary_strength`
- `planner_traditional_strength`
- `planner_historical_context`

### Planning Metrics
- `planner_exhibition_advantage` - Exhibition vs. collection focus
- `planner_collection_pas` - Collection-based priority score
- `planner_effective_pas` - Effective priority score

### Quality
- `planner_reputation_level` - World-Class, National, Regional, Local
- `planner_collection_level` - Exceptional, Strong, Modest, Small

### Notes
- `planner_notes` - Your observations and research

### Metadata
- `planner_data_updated_at` - Sync timestamp

## Spreadsheet Format

The spreadsheet should have these columns (case-insensitive):
- **Museum Name** (required for matching)
- Priority Score
- Outcome Tier
- Consider Label
- Historical Context
- Impressionist Strength
- Modern/ Contemporary Strength
- Traditional / Pre‑Modern Art Strength
- Exhibition-Centric Advantage (ECA)
- Collection-Based PAS
- Effective PAS
- Reputation Level
- Collection Level
- Notes

Blank cells are OK - they're treated as null and not added to museum records.

## Name Matching

Phase 1.9 matches museums by name:
- Case-insensitive
- Ignores punctuation
- Removes common words (museum, center, etc.)
- Tries exact match first
- Falls back to fuzzy matching

Typical match rate: **95-96%**

## Troubleshooting

### Museums Showing "Skipped (current)"?
✅ **This is good!** It means:
- Spreadsheet hasn't changed since last sync
- Museums are already up-to-date
- Phase 1.9 is saving time by not re-processing

If you want to force re-sync anyway:
```bash
python scripts/phases/phase1_9_planner_metadata.py --state CA --force
```

### Museum Not Matching?
Check for:
- Spelling differences
- Extra words (e.g., "The" at start)
- Punctuation differences
- Use exact name from state JSON file

### No Spreadsheet Found?
- Verify file is in `Documentation/_source/`
- Filename should start with `museum_planner_MASTER`
- Must be `.xlsx` format
- Or specify path: `--spreadsheet path/to/file.xlsx`

### Fields Not Updating?
- Check spreadsheet has values in those columns (not blank)
- Verify column names match expected format
- Make sure file is saved

## Example Output

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

**What the stats mean**:
- **Museums matched**: Found in spreadsheet
- **Museums updated**: Had field changes applied
- **Skipped (current)**: Already synced (spreadsheet unchanged)
- **Skipped (no changes)**: Matched but all fields identical
- **Museums not found**: In state file but not in spreadsheet

## Integration with Other Phases

Phase 1.9 works alongside all other phases:
- Doesn't overwrite automated enrichment
- Adds product owner perspective
- Can supplement or override automated scores
- Idempotent - safe to re-run anytime

## When to Run Phase 1.9

Run Phase 1.9 whenever you:
- Update the spreadsheet with new data
- Add new museums to the spreadsheet
- Revise scores or notes
- Want to sync latest product owner metadata

**Performance tips**:
- ✅ Run normally: Skips unchanged museums (fast)
- ✅ Use `--force`: Re-syncs everything (slower, but thorough)
- ✅ Multiple runs: Very fast if spreadsheet unchanged
- ✅ Dry run first: Preview changes before committing

It's safe to run multiple times - only updates changed fields.

## Files Modified

Phase 1.9 updates:
- `data/states/{STATE}.json` - Adds `planner_*` fields to museums
- `data/runs/phase1_9-{TIMESTAMP}/summary.json` - Run statistics

Original spreadsheet is never modified.

## Full Documentation

See [Documentation/data-pipeline/phase1_9_planner_metadata.md](../Documentation/data-pipeline/phase1_9_planner_metadata.md) for complete details.
