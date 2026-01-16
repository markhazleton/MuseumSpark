# 🛡️ Data Quality Rule: Never Replace Known with Null

## The Rule (One Line)
**NEVER replace a known value (non-null, non-placeholder) with null**

---

## Quick Reference

### ✅ Allowed Updates
| From | To | Result |
|------|----|----|
| `null` | `"123 Main St"` | ✅ APPLIED - Fills missing data |
| `"TBD"` | `null` | ✅ APPLIED - Normalizes placeholder |
| `"123 Main St"` | `"456 Elm St"` | ✅ APPLIED - Better data (if provenance allows) |
| `""` (empty) | `"Chicago"` | ✅ APPLIED - Fills empty field |

### ❌ Blocked Updates
| From | To | Reason |
|------|----|----|
| `"123 Main St"` | `null` | ❌ **REJECTED** - Would lose data |
| `"Tulsa"` | `null` | ❌ **REJECTED** - Would lose data |
| `36.1234` | `null` | ❌ **REJECTED** - Would lose data |
| `true` | `null` | ❌ **REJECTED** - Would lose data |

---

## Where It's Enforced

### 1. `enrich-open-data.py`
**Function:** `merge_patch(museum, patch)` (line ~2330)
- Applied during: CSV, Google Places, Yelp, web scraping
- Blocks: Patch values that are `null` from overwriting known values

### 2. `enrich-llm.py` 
**Function:** `merge_field()` in `agents/provenance.py` (line ~60)
- Applied during: LLM validation and deep dive enrichment
- Returns: `"cannot_replace_known_with_null"` rejection reason
- Logged in: `rejected_fields` array for transparency

---

## What Counts as "Known"?

### Known (Protected)
- ✅ Non-empty strings: `"Art"`, `"123 Main St"`, `"http://example.com"`
- ✅ Numbers: `36.1234`, `123`, `0`, `5.0` 
- ✅ Booleans: `true`, `false`
- ✅ Objects/Arrays: `{"rating": 4.5}`, `["tag1"]`

### Not Known (Replaceable)
- ❌ `null` or `None`
- ❌ Empty string: `""`
- ❌ Placeholders (17 patterns):
  - `"TBD"`, `"tbd"`, `"unknown"`, `"n/a"`, `"na"`
  - `"not known"`, `"not available"`, `"not provided"`
  - `"not applicable"`, `"none"`, `"null"`, `"pending"`
  - `"coming soon"`, `"--"`, `"---"`, `"tba"`
  - `"to be announced"`, `"to be determined"`

---

## Why This Matters

### Cost Impact
- **Oklahoma recovery**: $0.00 (cached) vs $0.31 (18 museums × $0.017)
- **Nationwide**: ~$15.70 potential waste per full enrichment cycle
- **Over time**: Hundreds of dollars saved by not re-fetching

### Data Quality Impact
- **Before**: LLM enrichment cleared 4 fields from 108|Contemporary
- **After**: All fields preserved, LLM adds/upgrades only
- **Result**: Cumulative improvement, never degradation

### Workflow Confidence
```
CSV → Google Places → Yelp → Web Scraping → LLM
  ↓         ↓           ↓           ↓           ↓
 +813     +180        +50         +30         +15
phones    coords     hours      summaries   types

TOTAL: +1,088 enriched fields (no losses!)
```

---

## Testing

### Run Unit Tests
```bash
cd scripts
..\.venv\Scripts\python test_data_quality_rule.py
```

Expected: ✅ All 6 tests pass

### Verify on Oklahoma (Dry Run)
```bash
python scripts\enrich-open-data.py --state OK --dry-run
```

Expected: `[OK] Changed: 0` (data already correct)

### Test LLM Enrichment
```bash
python scripts\enrich-llm.py --state OK
```

Expected: See `"cannot_replace_known_with_null"` in rejected_fields

---

## Common Scenarios

### Scenario 1: LLM Can't Extract Address
**Museum:** 108|Contemporary (robots.txt blocks LLM)
- **Current:** `street_address: "3405 S Peoria Ave"` (from Google Places)
- **LLM Returns:** `street_address: null` (couldn't find on website)
- **Result:** ✅ **Rejected** - Original value preserved

### Scenario 2: Google Places Finds Coordinates
**Museum:** Any museum with coords from Google
- **Current:** `latitude: null`, `longitude: null`
- **Google Returns:** `latitude: 36.1234`, `longitude: -95.9876`
- **Result:** ✅ **Applied** - Null replaced with data

### Scenario 3: CSV Normalizes Placeholder
**Museum:** Museum with "TBD" in database
- **Current:** `postal_code: "TBD"`
- **CSV Returns:** `postal_code: null` (no match in IRS 990)
- **Result:** ✅ **Applied** - Placeholder normalized to null

### Scenario 4: LLM Updates Notes
**Museum:** Any museum
- **Current:** `notes: "CSV: phone from IRS 990"`
- **LLM Returns:** `notes: "Modern art museum focused on contemporary works."`
- **Result:** ✅ **Applied** - Better data (provenance may reject but not due to null rule)

---

## Error Messages

### In enrich-open-data.py
Blocked updates are **silent** (just skipped in merge_patch)
- No explicit error message
- Field simply not updated
- Original value preserved

### In enrich-llm.py (LLM enrichment)
Blocked updates are **logged** in rejected_fields:
```json
{
  "field": "street_address",
  "reason": "cannot_replace_known_with_null",
  "proposed": null
}
```

---

## Documentation Files

- 📄 **Full Details:** `Documentation/DataQualityRule-NeverReplaceKnownWithNull.md`
- 📊 **Implementation Summary:** `Documentation/DataQualityRuleImplementationSummary.md`
- 🃏 **This Card:** `Documentation/DataQualityRule-QuickReference.md`
- 🧪 **Test Suite:** `scripts/test_data_quality_rule.py`

---

## Status: ✅ IMPLEMENTED & VALIDATED

**Date:** January 16, 2026
**Tested:** Oklahoma (18 museums)
**Result:** All tests pass, no data loss
