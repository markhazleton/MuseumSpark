# MRD Alignment Summary — Phase 1 Specification Update

**Date**: 2026-01-15  
**MRD Version**: v1.0  
**Status**: ✅ Complete

---

## Overview

This document summarizes the alignment of the Phase 1 specification with the Master Requirements Document (MRD) provided by the system owner (Mark Hazleton). All conflicting requirements have been resolved, and the specification has been updated to fully reflect MRD guidelines.

---

## Key Changes Made

### 1. **Phase Definition Clarification**

**Before**: Phases defined as application development phases (Phase 1 = Static site, Phase 2 = Backend)

**After**: Phases split into two parallel tracks:
- **Data Track** (MRD Phases 1-3): Master Backbone → Scoring → Regional Rollout
- **App Track**: Static validation site (this spec) → Future MuseumSpark app (out of scope)

**Rationale**: The MRD defines data curation milestones, while the spec defines the validation tool. Both are necessary and complementary.

---

### 2. **New Required Fields Added to Schema**

The following fields were added to `museum.schema.json` per MRD requirements:

| Field | Type | MRD Section | Description |
|-------|------|-------------|-------------|
| `city_tier` | integer (1-3) | 3.6 | City classification: 1=Major hub, 2=Medium city, 3=Small town |
| `nearby_museum_count` | integer | 4.14 | Count of other museums in same city (computed) |
| `is_scored` | boolean | Derived | Flag for filtering art vs non-art museums (computed) |

---

### 3. **Field Type Changes (Breaking Changes)**

The following fields changed from **string enums** to **numeric values** per MRD specifications:

#### `reputation` (MRD Section 4.11)
- **Before**: `"International" | "National" | "Regional" | "Local"`
- **After**: `integer (0-3)` where:
  - 0 = International
  - 1 = National
  - 2 = Regional
  - 3 = Local

#### `collection_tier` (MRD Section 4.12)
- **Before**: `"Flagship" | "Strong" | "Moderate" | "Small"`
- **After**: `integer (0-3)` where:
  - 0 = Flagship
  - 1 = Strong
  - 2 = Moderate
  - 3 = Small

**Rationale**: Numeric values simplify the Priority Score formula and enable direct arithmetic operations. UI can map numbers to labels for display.

---

### 4. **Art Scoring Scale Adjustment**

#### `impressionist_strength` and `modern_contemporary_strength` (MRD Sections 4.7-4.8)
- **Before**: `integer (0-5)` with 0 = None
- **After**: `integer (1-5)` where:
  - 1 = None
  - 2 = Minor works only
  - 3 = Moderate representation
  - 4 = Strong collection
  - 5 = Flagship collection

**Rationale**: MRD explicitly defines a 1-5 scale, not 0-5. This aligns with the Priority Score formula `(6 - Primary Art Strength)`.

---

### 5. **Updated Priority Score Formula**

The MRD provides a **revised and simplified formula** (Section 5):

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

**Changes from Previous Formula**:
- Removed "Nearby Cluster Bonus"
- Simplified dual-strength condition (≥4 for both, not ≥3)
- Direct numeric use of reputation and collection_tier (no mapping needed)

**Implementation**: Computed during data build, stored in JSON (`priority_score` field), NOT computed on-the-fly.

---

### 6. **Derived Field: `primary_art`**

**MRD Section 4.9**: Primary Art Focus

- **Type**: `"Impressionist" | "Modern/Contemporary" | null`
- **Derivation**: Determined by `max(impressionist_strength, modern_contemporary_strength)`
- **Storage**: **STORED** in JSON (not computed on-the-fly per user requirement)

**Removed Values**: `"Tie"` and `"None"` removed from enum. Ties default to "Modern/Contemporary" or flag for manual review.

---

### 7. **Museum Scoring Policy**

**MRD Section 2B**: Museum Inclusion Policy

- **All museums** are included in the dataset
- **Only art museums** (fine art, encyclopedic, university art) are scored
- **Non-art museums** (history, science, specialty) have:
  - `priority_score: null`
  - All scoring fields: `null`
  - `is_scored: false`

**Rationale**: Non-art museums support city-level trip planning without distorting art-focused rankings.

---

### 8. **FULL Record Definition Updated**

A museum record is **FULL** when it has:

1. **Schema Required Fields**: `museum_id`, `country`, `state_province`, `city`, `museum_name`, `website`, `museum_type`, `street_address`, `postal_code`

2. **MRD Core Fields**: `city_tier`, `reputation`, `collection_tier`, `time_needed`, `nearby_museum_count`, `status`, `notes`, `data_sources`, `confidence`

3. **Art Museum Scoring** (when `is_scored == true`):
   - `impressionist_strength`, `modern_contemporary_strength`, `primary_art`, `historical_context_score`, `priority_score`

**Placeholder**: Schema-valid but missing MRD core fields OR (for art museums) missing scoring inputs.

---

## Data Enrichment Strategy

A comprehensive enrichment strategy document has been created:

📄 **[DataEnrichmentStrategy.md](../../Documentation/DataEnrichmentStrategy.md)**

Key highlights:
- **Prioritize free/open data sources**: US Census (city tier), Google Places (address), IMLS (museum type), Wikipedia
- **LLM-assisted enrichment**: Reputation/collection classification, art scoring, historical context assessment
- **Manual curation**: Expert validation of all art museum scores
- **Computed fields**: `city_tier`, `nearby_museum_count`, `primary_art`, `priority_score`, `is_scored`

---

## Updated Documents

The following documents have been updated to reflect MRD requirements:

1. ✅ **[spec.md](spec.md)** — Phase 1 specification
   - Phase definition clarified
   - Functional requirements updated (FR-012, FR-013, FR-014)
   - FULL record definition aligned with MRD
   - Success criteria updated

2. ✅ **[museum.schema.json](../../data/schema/museum.schema.json)** — Data schema
   - `reputation` → numeric 0-3
   - `collection_tier` → numeric 0-3
   - `city_tier` → integer 1-3 (new)
   - `is_scored` → boolean (new)
   - `impressionist_strength`, `modern_contemporary_strength` → 1-5 scale
   - `primary_art` → enum simplified

3. ✅ **[DataSetDesign.md](../../Documentation/DataSetDesign.md)** — Dataset documentation
   - Purpose updated to reference MRD objectives
   - Scope section aligned with MRD inclusion policy
   - Field definitions updated with numeric types and MRD mappings
   - Scoring methodology replaced with exact MRD formula

4. ✅ **[DataEnrichmentStrategy.md](../../Documentation/DataEnrichmentStrategy.md)** — NEW
   - Field-by-field enrichment strategies
   - Open data source prioritization
   - LLM prompt strategies
   - Phased rollout approach (MRD Phases 1-3)
   - Quality assurance checkpoints

---

## Breaking Changes & Migration Path

### Schema Changes Require Data Migration

The following fields changed type from **string** to **integer**:

- `reputation`: `"International"` → `0`, `"National"` → `1`, `"Regional"` → `2`, `"Local"` → `3`
- `collection_tier`: `"Flagship"` → `0`, `"Strong"` → `1`, `"Moderate"` → `2`, `"Small"` → `3`

### Migration Script Needed

A migration script should be created to convert existing state files:

```python
# scripts/migrate-to-mrd-schema.py

REPUTATION_MAP = {
    "International": 0,
    "National": 1,
    "Regional": 2,
    "Local": 3
}

COLLECTION_MAP = {
    "Flagship": 0,
    "Strong": 1,
    "Moderate": 2,
    "Small": 3
}

def migrate_museum(museum: dict) -> dict:
    """Convert string enums to numeric MRD values."""
    if isinstance(museum.get("reputation"), str):
        museum["reputation"] = REPUTATION_MAP.get(museum["reputation"])
    
    if isinstance(museum.get("collection_tier"), str):
        museum["collection_tier"] = COLLECTION_MAP.get(museum["collection_tier"])
    
    return museum
```

**Action Required**: Run migration on all `data/states/*.json` files before schema validation.

---

## Next Steps

### Immediate Actions

1. **Migrate existing data** to new schema (convert string enums to numeric)
2. **Update build scripts**:
   - `build-index.py`: Add computation for `city_tier`, `nearby_museum_count`, `primary_art`, `is_scored`, `priority_score`
   - `build-progress.py`: Update FULL record detection logic
3. **Update validation scripts**: Ensure schema validation uses updated `museum.schema.json`

### Phase 1 Execution (Data Track)

Per MRD Phase 1 (Master Dataset Backbone):
1. Enrich Illinois/Midwest museums with all MRD core fields
2. Compute `city_tier` using US Census data
3. Classify `reputation` and `collection_tier` via LLM
4. Set `confidence` levels for all records
5. Validate against updated schema

### Phase 2 Execution (Data Track)

Per MRD Phase 2 (Scoring):
1. Filter art museums in Illinois/Midwest
2. LLM-generate initial art strength scores
3. Expert curator validates and adjusts
4. Compute `priority_score` via MRD formula
5. Set `is_scored = true` for scored museums

### Static Site Updates

The static validation site (App Track) should:
1. Update filters to use numeric `reputation`/`collection_tier` (with label mapping for UI)
2. Add `city_tier` filter (1-3 with "Major hub"/"Medium"/"Small town" labels)
3. Add `is_scored` filter (checkbox: "Show only scored art museums")
4. Display `primary_art` badge on museum cards
5. Show FULL vs placeholder indicator based on updated definition

---

## Questions & Clarifications Resolved

All questions posed to the system owner have been answered:

✅ **Q1: Phase conflict?** → Resolved: Parallel Data Track (MRD) + App Track (spec)  
✅ **Q2: New field storage?** → Resolved: All computed fields stored (not on-the-fly)  
✅ **Q3: Reputation/collection storage?** → Resolved: Numeric 0-3 with enum validation  
✅ **Q4: Priority score computation?** → Resolved: Computed during data build, stored  
✅ **Q5: Unscored museums?** → Resolved: `priority_score: null`, `is_scored: false`

---

## Summary

The Phase 1 specification is now **fully aligned** with the Master Requirements Document. Key changes include:

- 📊 **3 new fields**: `city_tier`, `nearby_museum_count`, `is_scored`
- 🔢 **2 type changes**: `reputation`, `collection_tier` now numeric 0-3
- 📐 **Updated formula**: MRD Priority Score formula implemented
- 📖 **New enrichment strategy**: Comprehensive open-data-first approach documented
- ✅ **Schema validation**: All changes reflected in `museum.schema.json`

All specifications, schemas, and documentation are ready for implementation.

---

**Approved by**: System Owner (Mark Hazleton)  
**Implementation Status**: Ready to begin Phase 1 data enrichment  
**Next Milestone**: Complete Illinois/Midwest enrichment (MRD Phase 1)
