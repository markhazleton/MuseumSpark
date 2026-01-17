# Pre-MRD Phase Quick Reference

## 🚀 Quick Start

### Basic Usage (Single State)
```bash
python scripts/pipeline/enrich-open-data.py \
  --state IL \
  --compute-mrd-fields \
  --rebuild-index \
  --rebuild-reports
```

### Dry Run First (Recommended)
```bash
python scripts/pipeline/enrich-open-data.py \
  --state IL \
  --compute-mrd-fields \
  --dry-run
```

---

## 📋 Command Options

| Flag | Purpose |
|------|---------|
| `--state IL` | Target state code (required) |
| `--compute-mrd-fields` | Enable MRD field computation ⭐ |
| `--only-placeholders` | Only enrich stub records |
| `--limit 25` | Limit museums processed |
| `--scrape-website` | Fetch official website (slower) |
| `--dry-run` | Preview without writing |
| `--rebuild-index` | Rebuild all-museums.json |
| `--rebuild-reports` | Rebuild progress.json |

---

## 🎯 MRD Fields Populated

| Field | Source | Auto-Computed? |
|-------|--------|----------------|
| `city_tier` | Wikipedia population | ✅ Yes (100%) |
| `reputation` | Wikidata sitelinks | ✅ Yes (~70%) |
| `collection_tier` | Wikidata P3172 | ✅ Yes (~50%) |
| `time_needed` | museum_type keywords | ✅ Yes (90%) |

---

## 📍 Regional Priority (MRD)

1. **Illinois / Midwest** ← Start here
2. Northeast (Boston, NYC, Philly, DC)
3. California (LA, SF, San Diego)
4. Remaining U.S. states
5. Canada, Mexico, Bermuda

---

## ✅ Post-Enrichment Validation

```bash
# 1. Validate schema
python scripts/validate-json.py --state IL

# 2. Rebuild index with MRD fields
python scripts/build-index.py --calculate-scores --update-nearby-counts

# 3. Check progress
python scripts/build-progress.py

# 4. View FULL record %
cat data/index/progress.json | jq '.full_pct'
```

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No Wikidata results" | Normal for small museums, will use defaults |
| Cities all Tier 3 | Wikipedia lookup may fail, will be refined in Phase 1 |
| Rate limit errors | Add `--scrape-delay-seconds 2.0` |
| No reputation/collection data | Wikidata missing data, LLM will fill in Phase 1 |

---

## 📊 Expected Results

### Before Pre-MRD Phase
- FULL: 7/1269 (0.55%)
- Missing: city_tier, reputation, collection_tier, time_needed

### After Pre-MRD Phase (Target)
- FULL: ~250/1269 (20%)
- Populated: city_tier (100%), time_needed (90%), reputation (70%), collection_tier (50%)

---

## 📚 Full Documentation

- **Comprehensive Guide**: `Documentation/PreMRDPhaseGuide.md`
- **Implementation Summary**: `Documentation/PreMRD-Phase-Summary.md`
- **Scripts README**: `scripts/README.md`
- **Spec**: `specs/001-museum-trip-planner/spec.md`

---

**Quick Tip**: Always run with `--dry-run` first to preview changes before committing!
