# Legacy Pipeline Archive - DEPRECATED

**Archive Date**: January 17, 2026
**Status**: DEPRECATED - DO NOT USE

## Main Files

- enrich-open-data.py (2,690 lines) - Monolithic pipeline
- run-phase1-pipeline.py - Old runner
- 25 test/dev scripts

## Replaced By

scripts/pipeline/run-complete-pipeline.py (unified orchestrator)
scripts/phases/ (9 modular phases)

## Usage
```bash
python scripts/pipeline/run-complete-pipeline.py --state CO
```
