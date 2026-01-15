# AI / LLM Enrichment Plan

## Goals

- Add per-museum canonical detail (LLM-assisted) without breaking current state/index pipelines.
- Keep state files canonical for museums without a per-museum file; when a per-museum file exists, it becomes the source of truth for that museum.
- Produce two LLM summary variants (short via mini model, long via deep model), both size-capped for review and storage.
- Automate triage/batching starting with the top 10 highest-priority museums; support manual include/exclude overrides.

## Data Tiers & Canonical Sources

- **Index (derived):** data/index/all-museums.json rebuilt from merged state bundles; used for browse/search.
- **State (canonical unless overridden):** data/states/{STATE}.json remains canonical for museums without per-museum detail.
- **Per-museum (canonical when present):** data/states/{STATE}/{museum_id}/ holds multi-file detail; overrides the corresponding entry in the state bundle when rebuilding.

## Naming & Paths

- **museum_id slug:** `{country}-{state}-{city_slug}-{museum_slug}`, lowercase, ASCII, hyphen-separated; strip/replace spaces and punctuation to ensure path safety on Linux/macOS/Windows.
- **Folder layout:**
  - data/states/{STATE}/{museum_id}/
    - core.json (canonical museum record aligned to schema)
    - summaries.json (LLM short/long summaries)
    - analysis.json (optional deeper notes/structured analysis)
    - provenance.json (optional expanded sources/decisions)
- Avoid versioned filenames; keep versions via fields inside JSON (e.g., `summary_short.generated_at`, `scoring_version`).

## LLM Content Policy

- Two variants per museum:
  - **Short (mini model):** concise overview; cap ≤ 5,000 characters (or ~2 KB min allowance).
  - **Long (deep model):** richer narrative/analysis; same cap per field.
- Store inline in summaries.json; include provenance (model, prompt, source URLs, confidence) and timestamps.
- Keep content human-reviewable; no embeddings or binaries in these files.

## Scoring (MRD v1.0)

- Applies to art museums only.
- Inputs: impressionist_strength, modern_contemporary_strength, historical_context_score, reputation_tier, collection_tier; derive primary_art = max(impressionist_strength, modern_contemporary_strength).
- Dual-strength bonus: subtract 2 if both art strengths ≥ 4.
- Formula (lower is better):
  $$\text{priority\_score} = (6 - \text{primary\_art}) \times 3 + (6 - \text{historical\_context\_score}) \times 2 + \text{reputation\_penalty} + \text{collection\_penalty} - \text{dual\_strength\_bonus}$$
- Tag computed scores with `scoring_version` (e.g., `v1.0`); leave unscored museums with null score and `is_scored: false`.

## Agent Workflow

1. **Ingest:** Load museum from index/state; hydrate Pydantic model aligned to data/schema/museum.schema.json.
2. **Triage:** Use low-cost model to propose short summary and identify missing/placeholder fields.
3. **Deep pass (selected museums):** High-end model generates long summary, refines scores, and structured analysis.
4. **Scoring:** Apply MRD formula; recompute `priority_score`, set `primary_art`, update `scoring_version`.
5. **Write outputs:** core.json (canonical), summaries.json (short/long), optional analysis/provenance; update `last_updated`, `updated_at`, and `data_sources`.
6. **Protect human data:** Do not overwrite non-placeholder human-entered fields; only fill null/placeholder values unless explicitly curated.

## Selection & Batching

- **Pilot:** Generate per-museum files for the top 10 lowest `priority_score` museums from the current index.
- **Batch mode:** Accept sorted subsets (by score) and manual include/exclude lists to extend coverage beyond the pilot.
- **Fallback:** Museums without per-museum folders continue to rely on the canonical state file entry.

## Merge & Build Flow

1. Merge step assembles each state bundle from:
   - Per-museum folders (override records for museums that have them).
   - Remaining canonical entries in data/states/{STATE}.json.
2. Run schema validation.
3. Feed merged bundles into scripts/build-index.py to recompute derived fields (priority_score, nearby_museum_count, primary_art) and emit data/index/all-museums.json.

## Provenance & Review

- Track sources, models, prompts, and timestamps in provenance fields; mark LLM outputs as untrusted until reviewed.
- Human-in-the-loop review for scores and long summaries, especially for high-impact museums.
- Store multiple LLM variants in summaries.json with metadata (e.g., `summary_short.model`, `summary_long.model`, `generated_at`).

## Open Decisions

- Exact slug normalization rules (allowed chars, max length) to guarantee cross-platform safety.
- Whether to keep analysis.json/provenance.json separate or co-locate in core.json for simplicity.
- Thresholds for expanding batches after the top-10 pilot (e.g., top-N by score or score ≤ X).
