# Changelog

## [v0.1.0] - 2026-05-14

### Phase 1 Milestone — Public Site + Data Pipeline

This release marks the completion of the Phase 0–1 data foundation: a live
React site served from a custom domain with a functional multi-phase enrichment
pipeline and a validated dataset of 1,269 reciprocal museums.

### Added

- **Live site** at [https://museum.makeboldspark.com/](https://museum.makeboldspark.com/)
  (React 19 + Vite 7, served via GitHub Pages custom domain).
- **Custom domain** `museum.makeboldspark.com` with `CNAME` and SPA routing via
  `404.html` redirect shim.
- **pytest suite** (`tests/`) covering Phase 3 priority scoring formula
  (`compute_priority_score`, `assign_outcome_tier`) and JSON Schema validation
  — 37 tests, 0 failures.
- **CI test workflow** (`.github/workflows/test.yml`) running pytest on every
  push/PR that touches `scripts/`, `tests/`, or `data/schema/`.
- **RELEASING** section in `CONTRIBUTING.md` documenting how future tags are cut.
- **Social preview source** SVG under `docs/branding/` for reproducible
  1280×640 Open Graph image.
- GitHub repository topics: `museums`, `travel-planning`, `react`, `python`,
  `data-enrichment`, `tailwindcss`, `pydantic`, `walker-art-center`.

### Changed

- Updated GitHub Pages workflow to target `museum.makeboldspark.com`; pinned
  action versions to current stable (`checkout@v4`, `setup-node@v4`,
  `upload-pages-artifact@v3`, `deploy-pages@v4`).
- `vite.config.ts` base changed from `/MuseumSpark/` to `/` for custom domain.
- README attribution updated to `Make Bold Spark` portfolio name and
  `Solutions Architect` title.

### Fixed

- Footer company name link text corrected to "Make Bold Solutions".

### Contributors

- Mark Hazleton
- dependabot[bot]

---

## [v0.0.1] - 2026-04-28

### Added

- Initial release documentation and archival structure under `.documentation/releases/`.
- Repository history and governance documentation to support ongoing DevSpark workflows.

### Changed

- Upgraded the repository to the current DevSpark framework layout with defaults, scripts, templates, and agent shims.
- Refactored oversized documentation pages and the Phase 2 scoring entrypoint into thin wrappers backed by implementation modules.
- Normalized invalid dataset values to satisfy schema validation requirements.

### Fixed

- Cleared site-audit TODO and BUG marker findings in pipeline comments.
- Aligned dependency versions for the site build and refreshed Dependabot-managed package groups.

### Architectural Decisions

- No new ADRs were captured for this release.

### Contributors

- Mark Hazleton
- dependabot[bot]