#!/usr/bin/env python3
"""Complete Museum Enrichment Pipeline Orchestrator.

This script runs the entire MuseumSpark enrichment pipeline end-to-end:
    Phase 0:   Google Places (identity, coordinates, basic address)
    Phase 0.5: Wikidata (website, postal_code, street_address, coordinates)
    Phase 0.7: Website Content (hours, admission, accessibility, collections)
    Phase 1:   Backbone (city_tier, time_needed, nearby_museum_count)
    Phase 1.5: Wikipedia (art museum enrichment)
    Phase 1.8: CSV Database (IRS 990 phone, museum_type, coordinates)
    Phase 2:   LLM Scoring (reputation, collection_tier, strengths)
    Phase 3:   Priority Scoring (trip planning)

Usage:
    # Run complete pipeline for a state
    python scripts/pipeline/run-complete-pipeline.py --state CO

    # Run for multiple states
    python scripts/pipeline/run-complete-pipeline.py --states CO,UT,WY

    # Run all states
    python scripts/pipeline/run-complete-pipeline.py --all-states

    # Skip certain phases
    python scripts/pipeline/run-complete-pipeline.py --state CO --skip-llm

    # Dry run (show what would execute)
    python scripts/pipeline/run-complete-pipeline.py --state CO --dry-run

    # Force re-run even if data exists
    python scripts/pipeline/run-complete-pipeline.py --state CO --force
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PHASES_DIR = PROJECT_ROOT / "scripts" / "phases"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"


@dataclass
class PhaseConfig:
    """Configuration for a pipeline phase."""
    name: str
    script: str
    description: str
    required: bool = True
    skip_flag: Optional[str] = None


@dataclass
class PhaseResult:
    """Result of running a phase."""
    phase_name: str
    success: bool
    duration_seconds: float
    error: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None


@dataclass
class PipelineStats:
    """Statistics for the complete pipeline run."""
    total_phases: int = 0
    successful_phases: int = 0
    failed_phases: int = 0
    skipped_phases: int = 0
    total_duration_seconds: float = 0.0
    phase_results: list[PhaseResult] = field(default_factory=list)


# Pipeline phase definitions
PIPELINE_PHASES = [
    PhaseConfig(
        name="Phase 0: Identity (Google Places)",
        script="phase0_identity.py",
        description="Google Places API for address, coordinates, place_id",
        skip_flag="skip-google-places",
    ),
    PhaseConfig(
        name="Phase 0.5: Wikidata Enrichment",
        script="phase0_5_wikidata.py",
        description="Wikidata for website, postal_code, street_address, coordinates",
        skip_flag="skip-wikidata",
    ),
    PhaseConfig(
        name="Phase 0.7: Website Content",
        script="phase0_7_website.py",
        description="Website scraping for hours, admission, accessibility, collections",
        skip_flag="skip-website",
    ),
    PhaseConfig(
        name="Phase 1: Backbone Fields",
        script="phase1_backbone.py",
        description="Deterministic fields: city_tier, time_needed, nearby_museum_count",
        required=True,
    ),
    PhaseConfig(
        name="Phase 1.5: Wikipedia (Art Museums)",
        script="phase1_5_wikipedia.py",
        description="Wikipedia enrichment for art museums only",
        skip_flag="skip-wikipedia",
    ),
    PhaseConfig(
        name="Phase 1.8: CSV Database (IRS 990)",
        script="phase1_8_csv_lookup.py",
        description="IRS 990 database for phone, museum_type, coordinates",
        skip_flag="skip-csv",
    ),
    PhaseConfig(
        name="Phase 2: LLM Scoring",
        script="phase2_scoring.py",
        description="OpenAI/Anthropic scoring for reputation, collection_tier",
        skip_flag="skip-llm",
    ),
    PhaseConfig(
        name="Phase 3: Priority Scoring",
        script="phase3_priority.py",
        description="Trip planning priority scores",
        required=True,
    ),
]


def now_utc_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def save_json(path: Path, data: Any) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_phase(
    phase: PhaseConfig,
    states: list[str],
    *,
    force: bool = False,
    dry_run: bool = False,
    skip_flags: set[str],
) -> PhaseResult:
    """Run a single pipeline phase.
    
    Args:
        phase: Phase configuration
        states: List of state codes to process
        force: Force re-processing
        dry_run: Dry run mode
        skip_flags: Set of skip flags to check
        
    Returns:
        PhaseResult with execution details
    """
    # Check if phase should be skipped
    if phase.skip_flag and phase.skip_flag in skip_flags:
        return PhaseResult(
            phase_name=phase.name,
            success=True,
            duration_seconds=0.0,
            skipped=True,
            skip_reason=f"Skipped by --{phase.skip_flag} flag",
        )
    
    # Build command
    script_path = PHASES_DIR / phase.script
    
    if not script_path.exists():
        return PhaseResult(
            phase_name=phase.name,
            success=False,
            duration_seconds=0.0,
            error=f"Script not found: {script_path}",
        )
    
    # Build arguments
    cmd = [sys.executable, str(script_path)]
    
    # Add state arguments
    if len(states) == 1:
        cmd.extend(["--state", states[0]])
    else:
        cmd.extend(["--states", ",".join(states)])
    
    # Add flags
    if force:
        cmd.append("--force")
    if dry_run:
        cmd.append("--dry-run")
    
    # Execute phase
    print(f"\n{'=' * 70}")
    print(f"▶ {phase.name}")
    print(f"{'=' * 70}")
    print(f"  Script: {phase.script}")
    print(f"  Description: {phase.description}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'=' * 70}\n")
    
    if dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd)}\n")
        return PhaseResult(
            phase_name=phase.name,
            success=True,
            duration_seconds=0.0,
            skipped=True,
            skip_reason="Dry run mode",
        )
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            check=True,
        )
        
        duration = time.time() - start_time
        
        print(f"\n✓ {phase.name} completed in {duration:.1f}s")
        
        return PhaseResult(
            phase_name=phase.name,
            success=True,
            duration_seconds=duration,
        )
        
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        error_msg = f"Exit code {e.returncode}"
        
        print(f"\n✗ {phase.name} failed after {duration:.1f}s: {error_msg}")
        
        return PhaseResult(
            phase_name=phase.name,
            success=False,
            duration_seconds=duration,
            error=error_msg,
        )
    
    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        
        print(f"\n✗ {phase.name} failed after {duration:.1f}s: {error_msg}")
        
        return PhaseResult(
            phase_name=phase.name,
            success=False,
            duration_seconds=duration,
            error=error_msg,
        )


def run_pipeline(
    states: list[str],
    *,
    force: bool = False,
    dry_run: bool = False,
    skip_flags: set[str],
    stop_on_error: bool = True,
) -> PipelineStats:
    """Run the complete enrichment pipeline.
    
    Args:
        states: List of state codes to process
        force: Force re-processing
        dry_run: Dry run mode
        skip_flags: Set of skip flags
        stop_on_error: Stop pipeline on first error
        
    Returns:
        PipelineStats with execution summary
    """
    stats = PipelineStats()
    stats.total_phases = len(PIPELINE_PHASES)
    
    pipeline_start = time.time()
    
    for phase in PIPELINE_PHASES:
        result = run_phase(
            phase=phase,
            states=states,
            force=force,
            dry_run=dry_run,
            skip_flags=skip_flags,
        )
        
        stats.phase_results.append(result)
        
        if result.skipped:
            stats.skipped_phases += 1
        elif result.success:
            stats.successful_phases += 1
        else:
            stats.failed_phases += 1
            
            # Stop on error if required phase fails
            if stop_on_error and phase.required:
                print(f"\n⚠️  Required phase failed. Stopping pipeline.")
                break
    
    stats.total_duration_seconds = time.time() - pipeline_start
    
    return stats


def print_summary(stats: PipelineStats, states: list[str], run_dir: Path) -> None:
    """Print pipeline execution summary.
    
    Args:
        stats: Pipeline statistics
        states: State codes processed
        run_dir: Run directory path
    """
    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    print(f"States: {', '.join(states)}")
    print(f"Total Duration: {stats.total_duration_seconds:.1f}s ({stats.total_duration_seconds/60:.1f} min)")
    print()
    print(f"Phases:")
    print(f"  Total:      {stats.total_phases}")
    print(f"  Successful: {stats.successful_phases} ✓")
    print(f"  Failed:     {stats.failed_phases} ✗")
    print(f"  Skipped:    {stats.skipped_phases} ⊘")
    print()
    
    # Show individual phase results
    print("Phase Results:")
    for result in stats.phase_results:
        if result.skipped:
            status = "⊘ SKIPPED"
            details = f"({result.skip_reason})"
        elif result.success:
            status = "✓ SUCCESS"
            details = f"({result.duration_seconds:.1f}s)"
        else:
            status = "✗ FAILED "
            details = f"({result.error})"
        
        print(f"  {status} {result.phase_name:40} {details}")
    
    print()
    print(f"Run directory: {run_dir}")
    print("=" * 70)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Complete Museum Enrichment Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    # Scope selection (required)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes (e.g., CO,UT,WY)")
    scope.add_argument("--all-states", action="store_true", help="Process all states")
    
    # Global options
    parser.add_argument("--force", action="store_true", help="Force re-processing even if data exists")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be executed without running")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue pipeline even if a phase fails")
    
    # Skip flags for optional phases
    parser.add_argument("--skip-google-places", action="store_true", help="Skip Phase 0 (Google Places)")
    parser.add_argument("--skip-wikidata", action="store_true", help="Skip Phase 0.5 (Wikidata)")
    parser.add_argument("--skip-website", action="store_true", help="Skip Phase 0.7 (Website scraping)")
    parser.add_argument("--skip-wikipedia", action="store_true", help="Skip Phase 1.5 (Wikipedia)")
    parser.add_argument("--skip-csv", action="store_true", help="Skip Phase 1.8 (CSV database)")
    parser.add_argument("--skip-llm", action="store_true", help="Skip Phase 2 (LLM scoring)")
    
    args = parser.parse_args()
    
    # Determine state codes to process
    states: list[str] = []
    
    if args.all_states:
        # Get all state files
        states_dir = PROJECT_ROOT / "data" / "states"
        states = sorted([
            p.stem.upper() for p in states_dir.glob("*.json")
            if len(p.stem) == 2 and p.stem.isalpha()
        ])
    elif args.states:
        states = [s.strip().upper() for s in args.states.split(",")]
    elif args.state:
        states = [args.state.upper()]
    
    # Collect skip flags
    skip_flags = set()
    if args.skip_google_places:
        skip_flags.add("skip-google-places")
    if args.skip_wikidata:
        skip_flags.add("skip-wikidata")
    if args.skip_website:
        skip_flags.add("skip-website")
    if args.skip_wikipedia:
        skip_flags.add("skip-wikipedia")
    if args.skip_csv:
        skip_flags.add("skip-csv")
    if args.skip_llm:
        skip_flags.add("skip-llm")
    
    # Create run directory
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"pipeline-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Print header
    print("=" * 70)
    print("MUSEUMPARK COMPLETE ENRICHMENT PIPELINE")
    print("=" * 70)
    print(f"States: {', '.join(states)}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Continue on error: {args.continue_on_error}")
    if skip_flags:
        print(f"Skipping: {', '.join(sorted(skip_flags))}")
    print(f"Run ID: {run_id}")
    print("=" * 70)
    
    # Run pipeline
    stats = run_pipeline(
        states=states,
        force=args.force,
        dry_run=args.dry_run,
        skip_flags=skip_flags,
        stop_on_error=not args.continue_on_error,
    )
    
    # Save summary
    summary = {
        "run_id": run_id,
        "states": states,
        "force": args.force,
        "dry_run": args.dry_run,
        "skip_flags": list(skip_flags),
        "total_phases": stats.total_phases,
        "successful_phases": stats.successful_phases,
        "failed_phases": stats.failed_phases,
        "skipped_phases": stats.skipped_phases,
        "total_duration_seconds": stats.total_duration_seconds,
        "phase_results": [
            {
                "phase_name": r.phase_name,
                "success": r.success,
                "duration_seconds": r.duration_seconds,
                "error": r.error,
                "skipped": r.skipped,
                "skip_reason": r.skip_reason,
            }
            for r in stats.phase_results
        ],
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)
    
    # Print summary
    print_summary(stats, states, run_dir)
    
    # Return appropriate exit code
    if stats.failed_phases > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
