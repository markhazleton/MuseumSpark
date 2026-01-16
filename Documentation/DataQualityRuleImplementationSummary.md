# Data Quality Rule Implementation Summary

## Date: January 16, 2026

## Problem Discovered

During LLM enrichment testing on Oklahoma (18 museums), we discovered a **critical data loss bug**:

- Running `enrich-llm.py` **cleared enriched data** from `enrich-open-data.py`
- Example: 108|Contemporary lost `street_address`, `postal_code`, `latitude`, `longitude`
- Root cause: LLM couldn't extract these fields (robots.txt blocking) and returned `null`, which overwrote existing values

## Solution Implemented

### Core Rule

**NEVER replace a known value (non-null, non-placeholder) with null**

### Modified Files

1. **scripts/enrich-open-data.py**
   - Modified `merge_patch()` function (line ~2330)
   - Added check: Skip applying `null` if existing value is known
   - Allows: null→value, placeholder→null, value→better value
   - Blocks: value→null

2. **scripts/agents/provenance.py**
   - Modified `merge_field()` function (line ~60)
   - Added early rejection: If `new_field.value is None` and `current_value` is known
   - Returns: `"cannot_replace_known_with_null"` rejection reason
   - Logs rejection for transparency

### Test Suite Created

**File:** `scripts/test_data_quality_rule.py`

**Tests:**

1. ✅ Known values preserved when patch has null
2. ✅ Null values replaced with known values
3. ✅ Placeholder values replaceable with null  
4. ✅ merge_field rejects null when current value exists
5. ✅ merge_field accepts known value when current is null
6. ✅ Rejects null even with provenance tracking

**Result:** All tests pass ✅

### Documentation Created

**File:** `Documentation/DataQualityRule-NeverReplaceKnownWithNull.md`

- Detailed problem statement
- Implementation details with code examples
- Before/after comparison
- Testing instructions
- Future enhancement ideas

## Validation

### Dry-Run Test (Oklahoma)

```bash
python scripts\enrich-open-data.py --state OK --dry-run
```

Result: `[OK] Changed: 0` (as expected, data already correct)

### Unit Test Suite

```bash
cd scripts
..\.venv\Scripts\python test_data_quality_rule.py
```

Result: All 6 tests passed ✅

## Impact

### Prevents Data Loss

- Oklahoma recovery cost $0.00 (thanks to 14-day Google Places cache)
- Without cache, would have cost $0.31 per state ($0.017 × 18 museums)
- Nationwide: $15.70 potential waste (51 states × avg museums per state)

### Enables Safe Multi-Pass Enrichment

Before fix:

```
CSV → Google Places → LLM → ❌ Data loss!
```

After fix:

```
CSV → Google Places → Yelp → Web Scraping → LLM → ✅ Cumulative improvement
```

### Workflow Confidence

- Can rerun enrichment pipelines without fear
- Each pass **adds** or **upgrades** data
- Never **removes** or **downgrades** data

## Next Steps

### Immediate (Completed)

- ✅ Implement never-replace-known-with-null rule
- ✅ Create comprehensive test suite
- ✅ Document implementation
- ✅ Validate with dry-run

### Recommended (Future)

1. **Test LLM enrichment on Oklahoma** with fixed code
2. **Verify rejection logging** shows `"cannot_replace_known_with_null"` for protected fields
3. **Run full pipeline on California** (179 museums) to see cumulative effect
4. **Monitor rejection reasons** to understand what LLM can't extract

### Optional Enhancements

- **Trust level protection**: Don't replace OFFICIAL_EXTRACT with LLM_GUESS
- **Confidence protection**: Don't replace confidence=5 with confidence=1
- **Manual approval workflow**: Flag high-impact downgrades for review

## Technical Details

### What Counts as "Known Value"?

**Known (protected from null):**

- Non-empty strings: `"123 Main St"`, `"Tulsa"`, `"Art"`
- Numbers: `36.1234`, `123`, `5.0`
- Booleans: `true`, `false`
- Objects/Arrays: `{"rating": 4.5}`, `["tag1", "tag2"]`

**Not Known (can be set to null):**

- `null` itself
- Empty string: `""`
- Placeholders: `"TBD"`, `"unknown"`, `"N/A"`, etc. (17 patterns total)

### Edge Cases Handled

1. **Empty string:** Treated as placeholder, can be set to `null`
2. **Zero/False:** Protected (these are valid values!)
3. **Whitespace-only strings:** Treated as empty, can be set to `null`
4. **Mixed types:** String vs Number - original type preserved

## Lessons Learned

1. **Cache is essential** - Saved $0.31 on Oklahoma recovery
2. **Test with small states first** - Oklahoma (18 museums) perfect for testing
3. **Data loss is silent** - Only noticed by manual inspection
4. **Additive pipelines** - Each step should only improve data quality
5. **Document immediately** - Easy to forget why a rule exists

## Files Modified

- `scripts/enrich-open-data.py` (+10 lines, 1 function modified)
- `scripts/agents/provenance.py` (+12 lines, 1 function modified)
- `scripts/test_data_quality_rule.py` (NEW, 195 lines)
- `Documentation/DataQualityRule-NeverReplaceKnownWithNull.md` (NEW, 200+ lines)
- `Documentation/DataQualityRuleImplementationSummary.md` (THIS FILE)

## Status

✅ **IMPLEMENTED AND VALIDATED**

Ready for:

- LLM enrichment testing on Oklahoma
- Full pipeline testing on California
- Nationwide enrichment rollout
