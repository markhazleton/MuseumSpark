# Legacy Scripts Archive

This folder contains deprecated scripts from the original MuseumSpark pipeline that have been replaced by the rebooted phase-based architecture.

**Archive Date**: 2026-01-17

## Deprecated Pipeline Scripts

### Core Enrichment (replaced by phase-based pipeline)
- **enrich-llm.py** → Replaced by [phase1_backbone.py](../phase1_backbone.py)
- **enrich-from-csv.py** → Replaced by [phase0_identity.py](../phase0_identity.py)
- **enrich_pipeline.py** → Replaced by [run-phase1-pipeline.py](../run-phase1-pipeline.py)
- **run-full-enrichment-phase.ps1** → Replaced by phase-specific scripts

### Migration Scripts (one-time use)
- **migrate-to-mrd-schema.py** - MRD v1.0 schema migration (completed)

### Analysis & Testing Scripts
- **analyze_ok_baseline.py** - Oklahoma baseline analysis
- **analyze-website.py** - Website analysis utilities
- **debug-postal.py** - Postal code debugging
- **infer-primary-domain.py** - Domain inference (now in phase1_backbone)
- **query_colorado_examples.py** - Colorado query examples
- **rank_colorado_museums.py** - Colorado ranking prototype
- **match-csv-analysis.py** - CSV matching analysis

### Utility Modules
- **address_extraction_strategies.py** - Address extraction (integrated into enrich-open-data.py)

### Test Scripts
- **test-address-extraction.py**
- **test-api-integration.py**
- **test-csv-integration.py**
- **test-google-detailed.py**
- **test-metadata-extraction.py**
- **test-normalization.py**
- **test_108_contemporary_google.py**
- **test_data_quality_rule.py**
- **test_google_with_state.py**

## Why These Were Deprecated

The original pipeline had several issues:
1. **Mixed Concerns**: Single scripts tried to do research AND scoring
2. **Hallucinations**: LLMs fabricated data when evidence was unclear
3. **Non-Idempotent**: Re-running scripts could overwrite good data
4. **Poor Traceability**: Hard to track data provenance

## Current Architecture (Rebooted Pipeline)

### Active Phase-Based Scripts
1. **Phase 0**: [phase0_identity.py](../phase0_identity.py) - Museum identity resolution
2. **Pre-MRD**: [enrich-open-data.py](../enrich-open-data.py) - Open data enrichment
3. **Phase 1**: [phase1_backbone.py](../phase1_backbone.py) - Core MRD fields
4. **Phase 1.5**: [phase1_5_wikipedia.py](../phase1_5_wikipedia.py) - Wikipedia enrichment
5. **Phase 2**: [phase2_scoring.py](../phase2_scoring.py) - Art museum scoring
6. **Phase 3**: [phase3_priority.py](../phase3_priority.py) - Priority calculation

### Active Utilities
- [build-index.py](../build-index.py) - Master index builder
- [build-progress.py](../build-progress.py) - Progress tracking
- [validate-json.py](../validate-json.py) - Schema validation
- [build-missing-report.py](../build-missing-report.py) - Gap analysis

## Recovery Instructions

If you need to reference these scripts:
1. Check git history for the last known working version
2. Review the replacement script's functionality
3. Port specific logic to current architecture if needed

**Do not restore these scripts to active use without updating them to follow current MRD patterns.**

---

**Last Updated**: 2026-01-17  
**Documentation**: [PreMRDPhaseGuide.md](../../Documentation/PreMRDPhaseGuide.md)
