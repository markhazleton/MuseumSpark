# Repository Story: MuseumSpark

> Generated 2026-04-28 | Window: 12 months | Scope: full

## Executive Summary
MuseumSpark is a data-first museum planning platform focused on enriching and ranking museums in the Walker reciprocal network. The repository combines a Python enrichment pipeline, a React/Vite frontend, and governance-oriented DevSpark workflows.

The project shows meaningful early-stage maturity: 89 commits across 103 days, 3 contributors, and continuous activity through 2026-04-28. The latest commit in the window is a documentation release artifact update (`docs: add v0.0.1 release artifacts`).

Delivery velocity reflects a classic build-then-harden pattern. Monthly commits moved from 61 in 2026-01 to 1 in 2026-02, then recovered to 15 in 2026-03 and 12 in 2026-04. This indicates a heavy foundational push followed by stabilization and process improvements.

Governance posture is mixed but improving. A constitution is present, conventional commit usage is substantial (46 conventional commits), and GitHub Actions exists. However, there are still 0 git tags, so release discipline is currently documented via release artifacts rather than version tags.

## Technical Analysis

### Development Velocity
The timeline shows 89 commits in total, distributed as: January 61, February 1, March 15, April 12. January was a bootstrap sprint, while March and April represent sustained maintenance and architecture refinement.

Repository change volume is dominated by data operations. Top file-type touches are JSON (4,610), Markdown (518), and Python (305), which aligns with a dataset-centric application rather than UI-only iteration.

The largest merge changed 134 files with 161,829 total lines, signaling a major structural milestone in pipeline/data integration.

### Contributor Dynamics
Contributor concentration remains high. Lead Architect authored 75 of 89 commits (84.3%), Developer A authored 13 (14.6%), and Developer B authored 1 (1.1%).

This gives strong architectural continuity, but also indicates bus-factor risk if ownership is not further distributed.

Monthly role activity suggests diversification is increasing slightly: Developer A contributed 7 commits in April, versus 6 in March.

### Quality Signals
The history scan reports 46 conventional commits out of 89 total, a 51.7% adoption level. This is a workable baseline and supports clearer changelog generation.

Test-related signals show 1,879 test files and 19 test-related commits in the scan output. This suggests broad test artifact presence, though the count likely includes generated or historical test assets and should be interpreted as an upper bound.

Recent quality-focused commits include schema normalization, dependency compatibility updates, and site-audit remediation.

### Governance & Process Maturity
Governance artifacts exist and are active: constitution detected, DevSpark command framework in place, and CI indicators present via GitHub Actions.

Tag discipline remains the most visible gap: no tags were detected in the history window, so formal release milestones are not yet represented in git metadata.

Spec lifecycle is currently quiet in active directories (0 active spec count in governance metrics), suggesting a temporary lull or completed cycle rather than ongoing active spec implementation.

### Architecture & Technology
Language presence indicates a polyglot operational stack: Python, JavaScript, TypeScript, PowerShell, shell, and Markdown.

The repository uses subproject packaging rather than root-level app manifests (`has_package_json: false` at root), which is consistent with a monorepo layout where frontend and pipeline live in separate directories.

GitHub Actions is present; Docker and root pyproject are not detected in the history signal set.

## Change Patterns
Top hotspot files by change count:

1. `data/states/AK.json` (19)
2. `site/package-lock.json` (17)
3. `data/states/AZ.json` (16)
4. `data/states/AL.json` (16)
5. `data/states/OK.json` (16)

Pattern interpretation:

- State-level JSON files dominate churn, confirming that data enrichment and correction remain the main engineering workload.
- `site/package-lock.json` hotspot activity indicates recurring dependency hygiene and tooling updates in the frontend.
- Frequent updates to `data/index/all-museums.json` (15 changes) suggest regular re-aggregation and publish-cycle rebuilds.

## Milestone Timeline

No git tags were detected, so there is no formal tag timeline to report.

| Date | Tag | Description |
|------|-----|-------------|
| N/A | N/A | No tagged milestones detected in this window |

## Constitution Alignment
Constitution alignment is strong in data quality and process rigor. Commit history includes schema validation, normalization, and audit/harvest/release workflow activity that reflects governance intent.

The largest gap is release metadata discipline: the repository now has changelog/release documentation (`v0.0.1`) but no corresponding git tag. Closing that gap would improve traceability from code to release narrative.

## Developer FAQ

### What does this project do?
MuseumSpark builds a ranked, enriched museum planning dataset and a companion browsing experience. It combines data ingestion, multi-phase enrichment, and scoring logic to support museum trip planning. History hotspots in `data/states/*.json` and `data/index/all-museums.json` confirm that dataset curation is central to the product.

### What tech stack does it use?
The current stack is polyglot: Python for pipeline/enrichment, TypeScript/JavaScript for frontend and tooling, plus PowerShell/shell for operational workflows. The scan explicitly detects Python, JavaScript, TypeScript, PowerShell, shell, and Markdown. GitHub Actions is present for CI/CD signals.

### Where do I start?
Start with `README.md`, then review `.documentation/memory/constitution.md` for non-negotiable constraints, and inspect `data/states/` plus `data/index/` to understand canonical data flow. For implementation details, `scripts/` and `site/` are the primary code roots. `scripts/enrich-open-data.py` and state JSON files are recurrent hotspots in history.

### How do I run it locally?
Use the root README instructions: run the frontend from `site/` (`npm install`, `npm run dev`) and run pipeline/validation scripts from the repo root with Python. The documented command set includes schema validation and index rebuild scripts under `scripts/validation/` and `scripts/builders/`. This mirrors the active maintenance pattern shown in recent commits.

### How do I run the tests?
The repository emphasizes validation and quality scripts rather than a single consolidated test command. The history scan reports 1,879 test files and 19 test-related commits, indicating test artifacts exist, but execution is split across stack-specific commands and validation workflows. Start with schema/validation scripts in `scripts/validation/` and frontend checks in `site/` tooling.

### What is the branching/PR workflow?
Default branch is `main`, and commit history suggests a predominantly direct-commit model with occasional merge-style commits. The scan reports `merged_pr_count: 0` for the measured window, so PR metadata is not the primary source of process traceability. Governance currently leans on commit conventions and documentation artifacts.

### Who do I ask when I'm stuck?
Based on contributor census, the Lead Architect role is the primary project expert (75 of 89 commits). Developer A is the secondary active contributor (13 commits), especially in dependency/tooling maintenance. For fastest context transfer, route architecture/data-pipeline questions to the top contributor role first.

### What areas of the code change most often?
Top churn is in `data/states/*.json`, `data/index/all-museums.json`, and `site/package-lock.json`. This means data enrichment outputs and frontend dependency maintenance are the most actively changing areas. Plan work with these hotspots in mind to minimize conflicts.

### Are there coding standards I must follow?
Yes. The constitution exists and is actively referenced in governance metrics, and conventional commits are used in 46 commits (51.7%). Data quality and schema correctness are recurring priorities in recent fixes, so validation-first workflow is a practical standard in this codebase.

### What version is currently released?
No git tag is currently available (`total_tags: 0`, milestone tags empty). The latest documented release artifact is `v0.0.1` in repository docs/changelog, but it is not yet represented as a git tag milestone.

---

Generated by /devspark.repo-story | DevSpark v1.6.0 - Adaptive System Life Cycle Development