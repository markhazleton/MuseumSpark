#!/usr/bin/env python3
"""MuseumSpark Enrichment Pipeline Orchestrator (MRD v2).

This script orchestrates the complete museum enrichment pipeline,
running all phases in the correct order with proper validation.

Pipeline Phases:
    Phase 0: Identity Resolution (Google Places -> city, address, coordinates)
    Phase 1: Backbone Enrichment (city_tier, time_needed, nearby_count, museum_type normalization)
    Phase 1.5: Wikipedia Enrichment (fetch Wikipedia data for art museums only)
    Phase 2: Art Museum Scoring (LLM-as-judge for scoring fields)
    Phase 3: Priority Calculation (deterministic MRD formula)
    Phase 4: Rebuild Index (consolidate all state files into all-museums.json)

Design Principles:
    1. PHASE ORDER ENFORCED: Each phase depends on the previous
    2. VALIDATION GATES: Verify prerequisites before each phase
    3. RESUMABLE: Can restart from any phase if previous phases complete
    4. OBSERVABLE: Clear progress reporting and run logging

Usage:
    # Full pipeline for a state
    python scripts/enrich_pipeline.py --state CO

    # Full pipeline for all states
    python scripts/enrich_pipeline.py --all-states

    # Start from specific phase (assumes previous phases complete)
    python scripts/enrich_pipeline.py --state CO --start-phase 2

    # Run specific phases only
    python scripts/enrich_pipeline.py --state CO --phases 0,1

    # Dry run (show what would happen)
    python scripts/enrich_pipeline.py --state CO --dry-run

    # Force re-run all phases
    python scripts/enrich_pipeline.py --state CO --force
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
STATES_DIR = PROJECT_ROOT / "data" / "states"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

# Phase scripts
PHASE_SCRIPTS = {
    0: SCRIPTS_DIR / "phase0_identity.py",
    1: SCRIPTS_DIR / "phase1_backbone.py",
    1.5: SCRIPTS_DIR / "phase1_5_wikipedia.py",
    2: SCRIPTS_DIR / "phase2_scoring.py",
    3: SCRIPTS_DIR / "phase3_priority.py",
    4: SCRIPTS_DIR / "build-index.py",  # Rebuild consolidated index
}

PHASE_NAMES = {
    0: "Identity Resolution",
    1: "Backbone Enrichment",
    1.5: "Wikipedia Enrichment",
    2: "Art Museum Scoring",
    3: "Priority Calculation",
    4: "Rebuild Index",
}

# Ordered list of phases (for iteration)
PHASE_ORDER = [0, 1, 1.5, 2, 3]  # Phase 4 is handled separately


@dataclass
class PhaseResult:
    """Result of running a single phase."""
    phase: int
    success: bool
    return_code: int = 0
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class PipelineResult:
    """Result of running the full pipeline."""
    run_id: str
    states: list[str]
    phases_run: list[int] = field(default_factory=list)
    phases_succeeded: list[int] = field(default_factory=list)
    phases_failed: list[int] = field(default_factory=list)
    total_duration_seconds: float = 0.0


def load_json(path: Path) -> Any:
    """Load JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_utc_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def check_prerequisites() -> list[str]:
    """Check that all prerequisites are met.

    Returns:
        List of error messages (empty if all OK)
    """
    errors = []

    # Check Phase 0 prerequisites (Google Maps API)
    if not os.getenv("GOOGLE_MAPS_API_KEY"):
        errors.append("GOOGLE_MAPS_API_KEY not set (required for Phase 0)")

    # Check Phase 2 prerequisites (LLM API)
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        errors.append("Neither OPENAI_API_KEY nor ANTHROPIC_API_KEY set (required for Phase 2)")

    # Check that phase scripts exist
    for phase, script in PHASE_SCRIPTS.items():
        if not script.exists():
            errors.append(f"Phase {phase} script not found: {script}")

    return errors


def validate_state_for_phase(state_code: str, phase: int) -> list[str]:
    """Validate that a state is ready for a given phase.

    Args:
        state_code: Two-letter state code
        phase: Phase number (0-3)

    Returns:
        List of validation errors (empty if ready)
    """
    errors = []
    state_file = STATES_DIR / f"{state_code}.json"

    if not state_file.exists():
        errors.append(f"State file not found: {state_file}")
        return errors

    state_data = load_json(state_file)
    museums = state_data.get("museums", [])

    if not museums:
        errors.append(f"No museums in state file: {state_file}")
        return errors

    # Phase-specific validation
    if phase >= 1:
        # Phase 1+ requires cities to be resolved (from Phase 0)
        missing_city = sum(1 for m in museums if not m.get("city"))
        if missing_city > len(museums) * 0.5:  # More than 50% missing
            errors.append(f"Phase 0 incomplete: {missing_city}/{len(museums)} museums missing city")

    if phase >= 2:
        # Phase 2 requires backbone fields (from Phase 1)
        missing_backbone = sum(1 for m in museums if m.get("city_tier") is None)
        if missing_backbone > 0:
            errors.append(f"Phase 1 incomplete: {missing_backbone}/{len(museums)} museums missing city_tier")

    if phase >= 3:
        # Phase 3 requires scoring (from Phase 2)
        art_museums = [m for m in museums if m.get("is_scoreable")]
        if not art_museums:
            # This is OK - state might have no art museums
            pass
        else:
            scored = sum(1 for m in art_museums if m.get("reputation") is not None)
            if scored == 0:
                errors.append(f"Phase 2 incomplete: 0/{len(art_museums)} art museums scored")

    return errors


def run_phase(
    phase: int,
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False,
    provider: str = "openai",
) -> PhaseResult:
    """Run a single phase for a state.

    Args:
        phase: Phase number (0-3)
        state_code: Two-letter state code
        force: Force re-run even if already complete
        dry_run: Don't actually make changes
        provider: LLM provider for Phase 2

    Returns:
        PhaseResult with success/failure info
    """
    script = PHASE_SCRIPTS.get(phase)
    if not script or not script.exists():
        return PhaseResult(phase=phase, success=False, error=f"Script not found: {script}")

    # Build command - Phase 4 (index rebuild) doesn't take --state
    if phase == 4:
        cmd = [sys.executable, str(script)]
    else:
        cmd = [sys.executable, str(script), "--state", state_code]

    if force and phase != 4:
        cmd.append("--force")
    if dry_run and phase != 4:
        cmd.append("--dry-run")

    # Phase-specific options
    if phase == 2:
        cmd.extend(["--provider", provider])

    # Run the phase
    start_time = datetime.now(timezone.utc)

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Let output go to console
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        return PhaseResult(
            phase=phase,
            success=result.returncode == 0,
            return_code=result.returncode,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        return PhaseResult(
            phase=phase,
            success=False,
            error=str(e),
            duration_seconds=duration,
        )


def run_pipeline(
    state_codes: list[str],
    *,
    phases: Optional[list[int]] = None,
    start_phase: int = 0,
    force: bool = False,
    dry_run: bool = False,
    provider: str = "openai",
    skip_validation: bool = False,
) -> PipelineResult:
    """Run the enrichment pipeline for given states.

    Args:
        state_codes: List of two-letter state codes
        phases: Specific phases to run (default: all)
        start_phase: Phase to start from (default: 0)
        force: Force re-run all phases
        dry_run: Don't actually make changes
        provider: LLM provider for Phase 2
        skip_validation: Skip prerequisite validation

    Returns:
        PipelineResult with overall results
    """
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"pipeline-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Determine which phases to run
    # Phases 0-3 (including 1.5) run per-state, Phase 4 (index rebuild) runs once at the end
    if phases is not None:
        # Filter to requested phases that are in PHASE_ORDER
        phases_to_run = [p for p in PHASE_ORDER if p in phases]
        run_phase_4 = 4 in phases
    else:
        # Run from start_phase through all phases
        phases_to_run = [p for p in PHASE_ORDER if p >= start_phase]
        run_phase_4 = True  # Always rebuild index after enrichment

    result = PipelineResult(
        run_id=run_id,
        states=state_codes,
    )

    start_time = datetime.now(timezone.utc)

    print("=" * 70)
    print("MuseumSpark Enrichment Pipeline")
    print("=" * 70)
    print(f"Run ID:     {run_id}")
    print(f"States:     {', '.join(state_codes)}")
    phases_display = ', '.join(str(p) for p in phases_to_run)
    if run_phase_4:
        phases_display += ", 4 (index rebuild)"
    print(f"Phases:     {phases_display}")
    print(f"Force:      {force}")
    print(f"Dry run:    {dry_run}")
    print(f"Provider:   {provider}")
    print("=" * 70)

    # Check prerequisites
    if not skip_validation:
        prereq_errors = check_prerequisites()
        if prereq_errors:
            print("\nPREREQUISITE ERRORS:")
            for err in prereq_errors:
                print(f"  - {err}")
            print("\nFix the above errors before running the pipeline.")
            return result

    # Process each state
    for state_code in state_codes:
        print(f"\n{'='*70}")
        print(f"STATE: {state_code}")
        print("=" * 70)

        # Run each phase
        for phase in phases_to_run:
            result.phases_run.append(phase)

            print(f"\n--- Phase {phase}: {PHASE_NAMES[phase]} ---")

            # Validate state is ready for this phase
            if not skip_validation and phase > 0:
                validation_errors = validate_state_for_phase(state_code, phase)
                if validation_errors:
                    print(f"VALIDATION FAILED:")
                    for err in validation_errors:
                        print(f"  - {err}")
                    result.phases_failed.append(phase)
                    print(f"\nSkipping remaining phases for {state_code}")
                    break

            # Run the phase
            phase_result = run_phase(
                phase=phase,
                state_code=state_code,
                force=force,
                dry_run=dry_run,
                provider=provider,
            )

            if phase_result.success:
                result.phases_succeeded.append(phase)
                print(f"\nPhase {phase} completed in {phase_result.duration_seconds:.1f}s")
            else:
                result.phases_failed.append(phase)
                print(f"\nPhase {phase} FAILED: {phase_result.error or f'exit code {phase_result.return_code}'}")
                print(f"Stopping pipeline for {state_code}")
                break

    # Run Phase 4 (index rebuild) once after all states are processed
    if run_phase_4 and not result.phases_failed:
        print(f"\n{'='*70}")
        print("PHASE 4: Rebuild Index (all states)")
        print("=" * 70)

        phase_result = run_phase(
            phase=4,
            state_code="",  # Not used for Phase 4
            force=force,
            dry_run=dry_run,
            provider=provider,
        )

        result.phases_run.append(4)
        if phase_result.success:
            result.phases_succeeded.append(4)
            print(f"\nPhase 4 completed in {phase_result.duration_seconds:.1f}s")
        else:
            result.phases_failed.append(4)
            print(f"\nPhase 4 FAILED: {phase_result.error or f'exit code {phase_result.return_code}'}")
    elif run_phase_4 and result.phases_failed:
        print(f"\n[SKIPPED] Phase 4 (index rebuild) - previous phases had failures")

    result.total_duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()

    # Save run summary
    summary = {
        "run_id": run_id,
        "states": state_codes,
        "phases_to_run": phases_to_run,
        "phases_succeeded": list(set(result.phases_succeeded)),
        "phases_failed": list(set(result.phases_failed)),
        "force": force,
        "dry_run": dry_run,
        "provider": provider,
        "total_duration_seconds": result.total_duration_seconds,
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)

    # Print final summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Run ID:           {run_id}")
    print(f"  States processed: {len(state_codes)}")
    print(f"  Phases run:       {len(set(result.phases_run))}")
    print(f"  Phases succeeded: {len(set(result.phases_succeeded))}")
    print(f"  Phases failed:    {len(set(result.phases_failed))}")
    index_status = "rebuilt" if 4 in result.phases_succeeded else ("skipped" if run_phase_4 else "not requested")
    print(f"  Index rebuild:    {index_status}")
    print(f"  Total duration:   {result.total_duration_seconds:.1f}s")
    print(f"  Run directory:    {run_dir}")
    print("=" * 70)

    return result


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MuseumSpark Enrichment Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Scope selection
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Process all states")

    # Phase control
    parser.add_argument("--phases", help="Comma-separated phase numbers to run (e.g., 0,1,1.5,2,3,4)")
    parser.add_argument("--start-phase", type=float, default=0, choices=[0, 1, 1.5, 2, 3],
                        help="Phase to start from (default: 0)")

    # LLM options
    parser.add_argument("--provider", default="openai", choices=["openai", "anthropic"],
                        help="LLM provider for Phase 2 (default: openai)")

    # Execution options
    parser.add_argument("--force", action="store_true", help="Force re-run all phases")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")
    parser.add_argument("--skip-validation", action="store_true", help="Skip prerequisite validation")

    args = parser.parse_args()

    # Determine state codes
    state_codes: list[str] = []

    if args.all_states:
        state_codes = sorted([
            p.stem.upper() for p in STATES_DIR.glob("*.json")
            if len(p.stem) == 2 and p.stem.isalpha()
        ])
    elif args.states:
        state_codes = [s.strip().upper() for s in args.states.split(",")]
    elif args.state:
        state_codes = [args.state.upper()]

    # Determine phases (support float phases like 1.5)
    phases = None
    if args.phases:
        phases = [float(p.strip()) for p in args.phases.split(",")]
        # Convert whole numbers to int for cleaner display
        phases = [int(p) if p == int(p) else p for p in phases]

    # Run pipeline
    result = run_pipeline(
        state_codes=state_codes,
        phases=phases,
        start_phase=args.start_phase,
        force=args.force,
        dry_run=args.dry_run,
        provider=args.provider,
        skip_validation=args.skip_validation,
    )

    # Return success if no failures
    return 0 if not result.phases_failed else 1


if __name__ == "__main__":
    sys.exit(main())
