# Data Quality Rule: Never Replace Known Values with Null

## Problem Statement

During LLM enrichment runs, we discovered that running `enrich-llm.py` was **clearing data** that had been populated by `enrich-open-data.py`. Specifically:

- **108|Contemporary** in Tulsa lost:
  - `street_address`: Was populated by Google Places API → became `null`
  - `postal_code`: Was populated by Google Places API → became `null`
  - `latitude`: Was populated by Google Places API → became `null`
  - `longitude`: Was populated by Google Places API → became `null`

This happened because the LLM couldn't find these fields on the museum's website (blocked by robots.txt) and returned `null`, which then overwrote the existing enriched values.

## Solution

We implemented a **critical data quality safeguard** in both enrichment pipelines:

### Rule: **NEVER replace a known value with null**

This rule applies to **every field update** in both:
- `enrich-open-data.py` (open data sources, business APIs, web scraping)
- `enrich-llm.py` (LLM-based enrichment)

## Implementation

### 1. `merge_patch()` in `enrich-open-data.py`

```python
def merge_patch(museum: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Merge patch into museum, with critical rule: NEVER replace known value with null."""
    out = dict(museum)
    for k, v in patch.items():
        existing = out.get(k)
        
        # CRITICAL DATA QUALITY RULE: Never replace a known value with null/None
        if v is None:
            # Only set to None if the field was already None or a placeholder
            if should_fill(existing) or existing is None:
                out[k] = v
            # else: skip - don't overwrite known value with null
        else:
            # New value is not None, apply if existing is empty/placeholder
            if should_fill(existing) or existing is None:
                out[k] = v
    return out
```

**Behavior:**
- ✅ `null` → `"123 Main St"`: Updates (fills missing data)
- ✅ `"TBD"` → `null`: Updates (normalizes placeholder)
- ✅ `"123 Main St"` → `"456 Elm St"`: Updates (better data)
- ❌ `"123 Main St"` → `null`: **REJECTED** (preserves known value)

### 2. `merge_field()` in `scripts/agents/provenance.py`

```python
def merge_field(
    *,
    current_value: Any,
    current_prov: Optional[dict[str, Any]],
    new_field: EnrichedField[Any],
    manual_lock: bool,
) -> Tuple[Any, Optional[dict[str, Any]], str]:
    # CRITICAL DATA QUALITY RULE: Never replace a known value with null
    if new_field.value is None and current_value is not None:
        if isinstance(current_value, str):
            if current_value.strip():  # Non-empty string
                return current_value, current_prov, "cannot_replace_known_with_null"
        else:
            # Non-string, non-None value
            return current_value, current_prov, "cannot_replace_known_with_null"
    
    # Continue with normal provenance-based merging...
```

**Behavior:**
- LLM returns `null` for `street_address` → **Rejected with reason: `cannot_replace_known_with_null`**
- Preserves existing value and provenance
- Logged in rejected_fields for transparency

## Validation

We created comprehensive tests in `scripts/test_data_quality_rule.py`:

### Test Results
```
✅ Test 1: Known values preserved when patch has null
✅ Test 2: Null values replaced with known values
✅ Test 3: Placeholder values replaceable with null
✅ Test 4: merge_field rejects null when current value exists
✅ Test 5: merge_field accepts known value when current is null
✅ Test 6: Rejects null even with provenance tracking
```

**All tests passed.** ✅

## Impact

### Before Fix
```json
{
  "museum_id": "usa-ok-unknown-108-contemporary",
  "street_address": "3405 S Peoria Ave",     // From Google Places
  "postal_code": "74105",                      // From Google Places
  "latitude": 36.1234,                         // From Google Places
  "longitude": -95.9876                        // From Google Places
}
```

After LLM enrichment:
```json
{
  "museum_id": "usa-ok-unknown-108-contemporary",
  "street_address": null,     // ❌ LOST
  "postal_code": null,         // ❌ LOST
  "latitude": null,            // ❌ LOST
  "longitude": null            // ❌ LOST
}
```

### After Fix
```json
{
  "museum_id": "usa-ok-unknown-108-contemporary",
  "street_address": "3405 S Peoria Ave",     // ✅ PRESERVED
  "postal_code": "74105",                      // ✅ PRESERVED
  "latitude": 36.1234,                         // ✅ PRESERVED
  "longitude": -95.9876                        // ✅ PRESERVED
}
```

LLM enrichment logs:
```
rejected_fields: [
  {"field": "street_address", "reason": "cannot_replace_known_with_null", "proposed": null},
  {"field": "postal_code", "reason": "cannot_replace_known_with_null", "proposed": null},
  {"field": "latitude", "reason": "cannot_replace_known_with_null", "proposed": null},
  {"field": "longitude", "reason": "cannot_replace_known_with_null", "proposed": null}
]
```

## Why This Matters

### Cost Savings
- Without this rule, we'd need to re-run `enrich-open-data.py` after every `enrich-llm.py` run
- Google Places API: $0.017/museum × 18 museums = $0.31 per recovery
- Thanks to 14-day caching, recovery was $0.00 (this time)
- **But caching expires** → would have cost real money without fix

### Data Quality
- Enrichment pipelines should be **additive**, not destructive
- Running multiple enrichment passes should **improve** data, never degrade it
- "Unknown" explicitly means we don't know; `null` from LLM means "I couldn't find it on this source"

### Workflow Safety
- Can safely run: CSV → Google Places → Yelp → Web Scraping → LLM
- Each step only **adds** or **upgrades** data
- Never loses information from previous steps

## Future Enhancements

Consider extending this rule to:
1. **Never downgrade trust level**: Don't replace `OFFICIAL_EXTRACT` with `LLM_GUESS`
2. **Never reduce confidence**: Don't replace confidence=5 with confidence=1
3. **Require manual approval** for replacing high-confidence data with low-confidence data

## Testing

Run the validation suite:
```bash
cd scripts
..\.venv\Scripts\python test_data_quality_rule.py
```

Expected output:
```
✅ ALL TESTS PASSED!
```

## Related Files

- `scripts/enrich-open-data.py` - Line 2330: `merge_patch()` function
- `scripts/agents/provenance.py` - Line 60: `merge_field()` function
- `scripts/test_data_quality_rule.py` - Comprehensive test suite

## Date Implemented

January 16, 2026

## Tested On

- Oklahoma (18 museums)
- Validation suite (6 test cases)
