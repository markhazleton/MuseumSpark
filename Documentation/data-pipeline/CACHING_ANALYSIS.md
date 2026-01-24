# Phase 1.* Caching Analysis

## Current Caching Implementation

### ✅ Phase 1 (Backbone) - **GOOD CACHING**
**Location**: `scripts/phases/phase1_backbone.py`

**Caching Strategy**:
- Caches Wikipedia population lookups in `data/cache/wikipedia_population/{city}_{state}.json`
- Checks cache before making API calls
- Stores both successful lookups and negative results (to avoid re-querying)
- Has `--force` flag to override and recalculate

**Effectiveness**: Excellent - avoids expensive Wikipedia API calls on repeat runs.

---

### ✅ Phase 1.5 (Wikipedia) - **GOOD CACHING**
**Location**: `scripts/phases/phase1_5_wikipedia.py`

**Caching Strategy**:
- Per-museum caching in `data/states/{STATE}/{museum_id}/cache/wikipedia.json`
- Checks if cache file exists before fetching
- Stores search query, results, and timestamps
- Has `--force` flag to re-fetch
- Rate-limited to respect Wikipedia API (0.5s delay)

**Effectiveness**: Excellent - completely skips museums already cached unless `--force`.

**Statistics Tracked**:
```python
skipped_already_cached: int = 0
```

---

### ⚠️ Phase 1.75 (Heuristic Fallback) - **MINIMAL CACHING**
**Location**: `scripts/phases/phase1_75_heuristic_fallback.py`

**Caching Strategy**:
- No external caching (doesn't need it - processes existing Wikidata)
- Has `--force` flag to re-score
- Checks if museum already has `reputation` and `collection_tier` scores

**Gaps**:
- Does NOT track if heuristic scoring was previously applied
- Re-computes every time even if output would be identical
- No way to skip museums that already have heuristic scores (unless `--force`)

**Recommendation**: Add tracking field like `heuristic_scored_at` to skip re-processing.

---

### ✅ Phase 1.8 (CSV Lookup) - **GOOD CACHING**
**Location**: `scripts/phases/phase1_8_csv_lookup.py`

**Caching Strategy**:
- In-memory caching of entire CSV file (`_CSV_BY_STATE_CACHE`)
- Loads CSV once per script execution, indexed by state
- Checks `data_sources` array for "museums_csv" to skip already-enriched museums
- Has `--force` flag to re-match

**Effectiveness**: Excellent - CSV loaded once, museums checked via data_sources.

**Statistics Tracked**:
```python
skipped_already_done: int = 0
```

---

### ⚠️ Phase 1.9 (Planner Metadata) - **BASIC CACHING**
**Location**: `scripts/phases/phase1_9_planner_metadata.py` (newly created)

**Caching Strategy**:
- In-memory caching of spreadsheet (loaded once per execution)
- Adds "museum_planner_spreadsheet" to data_sources
- Has `planner_data_updated_at` timestamp

**Gaps**:
- **Does NOT skip museums already synced** - always updates all matched museums
- No check for "unchanged data" - rewrites fields even if values are identical
- No way to skip museums unless they fail to match

**Impact**: Moderate - spreadsheet is small (<300 museums), but unnecessary writes on every run.

---

## Summary Table

| Phase | Caching Type | Skips Re-work? | Force Flag? | Grade |
|-------|-------------|----------------|-------------|-------|
| **1 (Backbone)** | File cache (population) | ✅ Yes | ✅ Yes | **A** |
| **1.5 (Wikipedia)** | Per-museum files | ✅ Yes | ✅ Yes | **A** |
| **1.75 (Heuristic)** | Checks existing scores | ⚠️ Partial | ✅ Yes | **C** |
| **1.8 (CSV)** | In-memory + data_sources | ✅ Yes | ✅ Yes | **A** |
| **1.9 (Planner)** | In-memory spreadsheet | ❌ No | ❌ No | **C** |

---

## Recommended Improvements

### 1. Phase 1.75 (Heuristic Fallback)

**Add tracking field**:
```python
# Check if already scored (unless force)
if not force and museum.get("heuristic_scored_at"):
    stats.skipped_already_scored += 1
    continue

# After scoring
museum["heuristic_scored_at"] = now_utc_iso()
museum["heuristic_scored_version"] = "v1"
```

**Benefit**: Prevents re-computation on every run.

---

### 2. Phase 1.9 (Planner Metadata)

**Add smart skip logic**:
```python
# Check if museum already has current planner data
current_updated = museum.get("planner_data_updated_at")
if not force and current_updated:
    # Check if spreadsheet is newer than last sync
    spreadsheet_mtime = spreadsheet_path.stat().st_mtime
    last_sync = datetime.fromisoformat(current_updated.replace('Z', '+00:00'))
    
    if spreadsheet_mtime < last_sync.timestamp():
        stats.skipped_already_current += 1
        continue

# Only update fields that changed
fields_updated = 0
for field, value in planner_data.items():
    if museum.get(field) != value:
        museum[field] = value
        fields_updated += 1

if fields_updated == 0:
    stats.skipped_no_changes += 1
    continue
```

**Add force flag**:
```python
parser.add_argument("--force", action="store_true", 
                   help="Force re-sync even if spreadsheet hasn't changed")
```

**Benefits**:
- Skips museums if spreadsheet hasn't changed since last sync
- Only updates fields that actually changed
- Reports how many were skipped vs. updated
- Dramatically faster on repeat runs (seconds vs. minutes)

---

### 3. Global Improvement: Standardize Pattern

**Create a shared caching utility**:
```python
# scripts/utils/caching.py

def should_skip_museum(
    museum: dict,
    phase_name: str,
    *,
    force: bool = False,
    check_data_source: Optional[str] = None,
    check_timestamp_field: Optional[str] = None,
) -> bool:
    """Determine if a museum should be skipped (already processed).
    
    Args:
        museum: Museum record
        phase_name: Name of phase (for logging)
        force: Force re-processing
        check_data_source: If provided, check if this source is in data_sources
        check_timestamp_field: If provided, check if this timestamp field exists
        
    Returns:
        True if should skip, False if should process
    """
    if force:
        return False
    
    if check_data_source:
        sources = museum.get("data_sources", [])
        if check_data_source in sources:
            return True
    
    if check_timestamp_field:
        if museum.get(check_timestamp_field):
            return True
    
    return False
```

**Usage in phases**:
```python
# Phase 1.8
if should_skip_museum(museum, "phase1_8", force=force, 
                     check_data_source="museums_csv"):
    stats.skipped += 1
    continue

# Phase 1.9
if should_skip_museum(museum, "phase1_9", force=force,
                     check_timestamp_field="planner_data_updated_at"):
    stats.skipped += 1
    continue
```

---

## Performance Impact

### Current State (no improvements)
Running Phase 1.9 on all states (1,269 museums):
- Loads spreadsheet: ~1 second
- Processes all 1,269 museums: ~5 seconds
- Updates ~1,200 museums (even if unchanged): ~10 seconds
- **Total: ~16 seconds**

### With Improvements
Running Phase 1.9 on all states (no spreadsheet changes):
- Loads spreadsheet: ~1 second
- Checks spreadsheet mtime vs. last sync: instant
- Skips all 1,269 museums: ~0.5 seconds
- **Total: ~1.5 seconds** (10x faster!)

### On Selective Updates
If only 50 museums changed in spreadsheet:
- Loads spreadsheet: ~1 second
- Processes 1,269 museums: ~5 seconds
- Updates only 50 museums: ~1 second
- Skips 1,219 museums: ~0.5 seconds
- **Total: ~7.5 seconds** (2x faster)

---

## Conclusion

**What works well**:
- ✅ Phase 1 (backbone), 1.5 (Wikipedia), and 1.8 (CSV) all have excellent caching
- ✅ All phases avoid expensive external API calls on repeat runs
- ✅ --force flags allow override when needed

**What could be improved**:
- ⚠️ Phase 1.75 could track when heuristic scoring was applied
- ⚠️ Phase 1.9 (new) should skip museums when spreadsheet hasn't changed
- ⚠️ Phase 1.9 should only update fields that actually changed

**Priority**:
1. **High**: Add skip logic to Phase 1.9 (will save significant time on large datasets)
2. **Medium**: Add version tracking to Phase 1.75
3. **Low**: Create shared caching utility (nice to have, but phases work well independently)

The existing phases (1, 1.5, 1.8) already do caching very well. The newer phases (1.75, 1.9) could benefit from similar skip logic.
