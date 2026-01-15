#!/usr/bin/env python3
"""Run the Phase 1 dataset pipeline end-to-end.

This is a convenience wrapper that runs the scripts in the correct order:

1) (Optional) Enrich state files using free/open sources
2) (Optional) Validate touched state files against the JSON Schema
3) Rebuild the master index: data/index/all-museums.json
4) Rebuild deterministic Phase 1 reports:
   - data/index/missing-report.json
   - data/index/progress.json

Examples:
  # Enrich one state (placeholders only), then rebuild index + reports
  python scripts/run-phase1-pipeline.py --state CA --only-placeholders --limit 25

  # Enrich multiple states
  python scripts/run-phase1-pipeline.py --states CA,AK --only-placeholders --limit 10

  # Enrich all states (be mindful: this may take a long time)
  python scripts/run-phase1-pipeline.py --all-states --only-placeholders

  # Include conservative official-site scraping
  python scripts/run-phase1-pipeline.py --state CA --only-placeholders --scrape-website

  # Skip enrichment (just rebuild derived artifacts)
  python scripts/run-phase1-pipeline.py --skip-enrich

Notes:
- Enrichment performs network calls and writes caches under data/cache/.
- This runner uses the active Python interpreter (sys.executable).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
STATES_DIR = PROJECT_ROOT / "data" / "states"


def _script(name: str) -> Path:
    path = SCRIPTS_DIR / name
    if not path.exists():
        raise SystemExit(f"Missing script: {path}")
    return path


def run(cmd: list[str]) -> None:
    printable = " ".join(cmd)
    print(f"\n[RUN] {printable}")
    subprocess.run(cmd, check=True)


def list_all_state_codes() -> list[str]:
    codes: list[str] = []
    for p in sorted(STATES_DIR.glob("*.json")):
        code = p.stem.upper()
        if len(code) == 2 and code.isalpha():
            codes.append(code)
    return codes


def parse_states_arg(value: str) -> list[str]:
    parts = [p.strip().upper() for p in (value or "").split(",") if p.strip()]
    out: list[str] = []
    for p in parts:
        if len(p) != 2 or not p.isalpha():
            raise SystemExit(f"Invalid state code in --states: {p!r}")
        out.append(p)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MuseumSpark Phase 1 pipeline")

    scope = parser.add_mutually_exclusive_group(required=False)
    scope.add_argument("--state", help="Two-letter state code (e.g., CA)")
    scope.add_argument("--states", help="Comma-separated state codes (e.g., CA,AK)")
    scope.add_argument("--all-states", action="store_true", help="Run enrichment for all states")

    parser.add_argument("--skip-enrich", action="store_true", help="Skip enrichment step")
    parser.add_argument("--only-placeholders", action="store_true", help="Only enrich placeholder/stub records")
    parser.add_argument("--limit", type=int, default=0, help="Max museums per state to process (0 = no limit)")

    parser.add_argument(
        "--scrape-website",
        action="store_true",
        help="Also fetch the museum's official website to extract structured fields/links (conservative)",
    )
    parser.add_argument(
        "--scrape-max-pages",
        type=int,
        default=2,
        help="Max pages to fetch per museum when scraping (homepage counts as 1)",
    )
    parser.add_argument(
        "--scrape-delay-seconds",
        type=float,
        default=1.0,
        help="Delay between website fetches on cache misses (politeness)",
    )

    parser.add_argument("--dry-run", action="store_true", help="Do not write enrichment changes")

    parser.add_argument("--skip-validate", action="store_true", help="Skip schema validation")
    parser.add_argument("--skip-index", action="store_true", help="Skip rebuilding all-museums.json")
    parser.add_argument("--skip-reports", action="store_true", help="Skip rebuilding progress/missing reports")

    parser.add_argument(
        "--calculate-scores",
        action="store_true",
        help="Pass --calculate-scores to build-index.py (art museums only)",
    )
    parser.add_argument(
        "--update-nearby-counts",
        action="store_true",
        help="Pass --update-nearby-counts to build-index.py",
    )

    args = parser.parse_args()

    python = sys.executable

    # Determine which states to enrich.
    state_codes: list[str] = []
    if not args.skip_enrich:
        if args.all_states:
            state_codes = list_all_state_codes()
        elif args.states:
            state_codes = parse_states_arg(args.states)
        elif args.state:
            state_codes = parse_states_arg(args.state)
        else:
            raise SystemExit("Provide --state/--states/--all-states or use --skip-enrich")

        # Sanity-check state files exist.
        for code in state_codes:
            path = STATES_DIR / f"{code}.json"
            if not path.exists():
                raise SystemExit(f"Missing state file: {path}")

    enrich_script = _script("enrich-open-data.py")
    validate_script = _script("validate-json.py")
    build_index_script = _script("build-index.py")
    missing_report_script = _script("build-missing-report.py")
    progress_script = _script("build-progress.py")

    if not args.skip_enrich:
        for code in state_codes:
            cmd = [python, str(enrich_script), "--state", code]
            if args.only_placeholders:
                cmd.append("--only-placeholders")
            if args.limit:
                cmd.extend(["--limit", str(int(args.limit))])
            if args.scrape_website:
                cmd.append("--scrape-website")
                cmd.extend(["--scrape-max-pages", str(int(args.scrape_max_pages))])
                cmd.extend(["--scrape-delay-seconds", str(float(args.scrape_delay_seconds))])
            if args.dry_run:
                cmd.append("--dry-run")
            run(cmd)

            if not args.skip_validate:
                run([python, str(validate_script), "--state", code])

    # Derived artifacts should only be rebuilt after writes.
    if args.dry_run:
        print("\n[INFO] Dry-run selected; skipping index/reports rebuild.")
        return 0

    if not args.skip_index:
        cmd = [python, str(build_index_script)]
        if args.calculate_scores:
            cmd.append("--calculate-scores")
        if args.update_nearby_counts:
            cmd.append("--update-nearby-counts")
        run(cmd)

    if not args.skip_reports:
        run([python, str(missing_report_script)])
        run([python, str(progress_script)])

    print("\n[OK] Phase 1 pipeline completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
