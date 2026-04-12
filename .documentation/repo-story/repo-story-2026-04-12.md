# Repository Story: MuseumSpark

> Generated 2026-04-12 | Window: 12 months | Scope: full

## Executive Summary
MuseumSpark is a museum trip-planning and enrichment platform focused on the Walker reciprocal museum universe. The repository combines a React site, a Python enrichment pipeline, and a large JSON-first data model to support museum discovery, scoring, and trip planning.

The project is still early but active: 81 total commits, 3 contributors, and 87 days between first and latest commit in the measured window. Activity began with an initial commit on 2026-01-15 and most recently included DevSpark command framework updates on 2026-04-12.

Delivery velocity shows a strong launch spike followed by consolidation. Monthly commits are 61 (2026-01), 1 (2026-02), 15 (2026-03), and 4 (2026-04), which indicates early foundational build-out and later stabilization/maintenance cycles.

Governance signals are mixed. Conventional commit usage is strong at 38 of 81 commits, a constitution file is present, and GitHub Actions is configured. However, there are 0 release tags and 0 merged PRs detected in the period, suggesting a workflow that is still mostly direct-commit and pre-release.

Milestone evidence comes from high-impact merge and feature commits rather than tags. A major merge introduced over 161k lines of change, and later iterations focused on schema quality, dependency alignment, and process hardening.

## Technical Analysis

### Development Velocity
Commit distribution by month was 61 in January, 1 in February, 15 in March, and 4 in April. This pattern is consistent with rapid initial implementation followed by selective improvement passes.

Volume indicators show extensive dataset-centric work: JSON file touches dominate at 4,601, followed by Markdown (393) and Python (301). One large merge commit reported 134 files changed and 161,829 total lines, which likely represents foundational pipeline and dataset assembly.

Given the high ratio of JSON touches to code-file changes, development appears data-heavy rather than purely feature-coding-heavy. Churn is concentrated in state dataset files and generated/indexed artifacts.

### Contributor Dynamics
The contributor census shows 3 contributors. Lead Architect accounts for 71 commits, Developer A for 9, and Developer B for 1.

Bus-factor risk is high: the top contributor has 71/81 commits (87.7%). The second contributor supports dependency and maintenance bursts, but ownership is still concentrated.

Team activity spread also shifted over time: January was heavily Lead Architect-led, while March and April show intermittent contributions from Developer A.

### Quality Signals
Test-related signals are present but noisy. The history scan reports 1,879 test files and 18 test-related commits; this indicates substantial test surface in the repository, though some counts may include generated or nested content.

Commit quality is reasonably strong: 38 conventional commits and 0 informal single-word commit messages detected. Subject classifications include 34 feature-like commits and balanced supporting work across docs, chore, CI/build, fixes, and refactors.

Quality-oriented commits in recent history include schema normalization, dependency compatibility fixes, and site build/dependency scanning fixes.

### Governance & Process Maturity
Constitution governance exists and is versioned, with one governance artifact detected in the scan window. GitHub Actions is present, which supports CI discipline.

PR-centric workflow signals are low: merged PR count was reported as 0 in aggregate metrics, and release tag discipline is also low with 0 tags. Operationally, this suggests process controls are present but not yet consistently enforced through tagged release cadence.

No active spec directories were detected in the current scan, implying either completion/cleanup of previous spec cycles or migration of process artifacts.

### Architecture & Technology
Language presence spans Python, JavaScript, TypeScript, PowerShell, shell, and Markdown. This aligns with a split architecture of frontend application, data processing pipeline, and command/process automation.

Repository signals show GitHub Actions enabled, no root package.json, and no Dockerfile. That reflects a polyglot monorepo where the web app and pipeline live under subdirectories, rather than a single root app package.

Hotspot concentration strongly favors data-state and index files, with periodic focus on site dependency lockfiles and enrichment scripts.

## Change Patterns
Top modified files are:
1. data/states/AK.json (19 changes)
2. data/states/OK.json (16 changes)
3. data/states/AZ.json (16 changes)
4. data/states/AL.json (16 changes)
5. data/states/CO.json (15 changes)

This pattern indicates repeated iterative enrichment and correction passes on state-level records. The additional hotspot in data/index/all-museums.json supports that interpretation, showing frequent re-aggregation.

One notable non-data hotspot is site/package-lock.json (14 changes), which indicates recurrent dependency maintenance cycles in the frontend stack.

## Milestone Timeline
No Git tags were detected in the repository history window, so a formal release timeline cannot be established from tags.

Instead, milestone-like events appear in commit history, including the initial project commit (2026-01-15), large phase-completion merge activity, and recent process/dependency hardening work in March-April 2026.

## Constitution Alignment
A constitution file exists at .documentation/memory/constitution.md, and recent history shows behavior that aligns with governance priorities: schema validation, data normalization, and process-framework updates.

Alignment is strongest in data quality and structural consistency work. Gaps are most visible in release discipline and PR-based traceability, given the absence of tags and low merged-PR signals in the measured period.

## Developer FAQ

### What does this project do?
MuseumSpark is a museum planning and enrichment project that turns reciprocal museum roster data into a searchable, scored planning dataset and companion site. The README positions it as a strategic planner for museum visits, and repository hotspots confirm heavy work in state-level museum JSON records and enrichment outputs.

### What tech stack does it use?
The repository contains Python, JavaScript, TypeScript, PowerShell, shell, and Markdown files. The README and file structure indicate a React + Vite frontend in the site folder and a Python-based pipeline in scripts and data flows, with GitHub Actions present for automation.

### Where do I start?
Start at README.md for project orientation, then inspect data/states and data/index to understand the canonical records and aggregations. For implementation flow, review scripts/README.md and scripts/enrich-open-data.py, which appears as a hotspot in commit history.

### How do I run it locally?
Based on README instructions, run the web app from the site folder with npm install and npm run dev. For data tooling, create a Python virtual environment and run the validation/build scripts under scripts, including schema validation before pipeline runs.

### How do I run the tests?
Use the Python validation and analysis scripts as the current test/quality gate baseline, especially scripts/validation/validate-json.py and related validation helpers. The history scan reports significant test-file presence and multiple test-related commits, but test execution commands are split by stack and documented mainly through scripts and README workflows.

### What is the branching/PR workflow?
Default branch is main. Governance signals show low PR-merge evidence in the measured window, so current practice appears to rely heavily on direct mainline commits or merge patterns not fully captured as PR merges. If tightening process, treat PR review and tagged releases as immediate maturity improvements.

### Who do I ask when I'm stuck?
The contributor census indicates Lead Architect authored 71 of 81 commits (87.7%), making that role the primary knowledge owner. Developer A is the secondary contributor with maintenance and dependency-change activity.

### What areas of the code change most often?
The most frequently changed areas are data/states/*.json and data/index/all-museums.json, followed by occasional frontend dependency maintenance in site/package-lock.json. This suggests dataset enrichment and curation is the dominant ongoing workload.

### Are there coding standards I must follow?
Yes. Conventional commit adoption is materially present (38 commits matched), and constitution/governance artifacts are in place. Follow schema validation and data-quality guardrails first, then align commit format and CI expectations to existing repository patterns.

### What version is currently released?
No tagged release is currently detectable in the repository history (0 tags). Operationally, the project is active and evolving, but not yet publishing formal versioned releases via Git tags.

---

Generated by /devspark.repo-story | DevSpark v1.6.0 - Adaptive System Life Cycle Development
