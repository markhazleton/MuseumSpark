#!/usr/bin/env python3
"""Phase 1.9: Museum Planner Metadata Integration.

This module enriches museums with product owner metadata from the museum_planner_MASTER
spreadsheet. This includes manually curated scores, notes, and planning metadata that
the product owner maintains over time.

Data Source: Documentation/_source/museum_planner_MASTER_*.xlsx

Fields Provided:
    - planner_priority_score: Product owner's priority score
    - planner_outcome_tier: Tier assignment (e.g., "Consider", "Priority")
    - planner_consider_label: Descriptive label for the museum
    - planner_historical_context: Historical context score
    - planner_impressionist_strength: Impressionist collection strength (0-5)
    - planner_modern_contemporary_strength: Modern/contemporary collection strength (0-5)
    - planner_traditional_strength: Traditional/pre-modern art strength (0-5)
    - planner_exhibition_advantage: Exhibition-centric advantage score
    - planner_collection_pas: Collection-based PAS score
    - planner_effective_pas: Effective PAS score
    - planner_reputation_level: Reputation level (World-Class, Regional, Local, etc.)
    - planner_collection_level: Collection level (Exceptional, Strong, Small, etc.)
    - planner_notes: Product owner notes and observations

Matching Strategy:
    1. Match on museum name (case-insensitive, normalized)
    2. Optionally verify by city/state for disambiguation
    3. Update existing planner fields (idempotent - safe to re-run)

Design Principles:
    1. PRODUCT OWNER DATA: Respect manual curation from spreadsheet
    2. IDEMPOTENT: Re-running updates with latest spreadsheet data
    3. PRESERVE EXISTING: Don't overwrite non-planner fields
    4. TRACEABILITY: Track when planner data was last updated

Usage:
    # Update single state
    python scripts/phases/phase1_9_planner_metadata.py --state CA

    # Update all states
    python scripts/phases/phase1_9_planner_metadata.py --all-states

    # Dry run (show what would change)
    python scripts/phases/phase1_9_planner_metadata.py --state CA --dry-run

    # Specify custom spreadsheet path
    python scripts/phases/phase1_9_planner_metadata.py --all-states --spreadsheet path/to/file.xlsx
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas is required. Install with: pip install pandas")
    sys.exit(1)

try:
    import openpyxl
except ImportError:
    print("ERROR: openpyxl is required. Install with: pip install openpyxl")
    sys.exit(1)

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"
DOC_SOURCE_DIR = PROJECT_ROOT / "Documentation" / "_source"

# Configure stdout for UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


@dataclass
class PlannerMetadata:
    """Product owner metadata from spreadsheet."""
    priority_score: Optional[int] = None
    outcome_tier: Optional[str] = None
    consider_label: Optional[str] = None
    historical_context: Optional[int] = None
    impressionist_strength: Optional[int] = None
    modern_contemporary_strength: Optional[int] = None
    traditional_strength: Optional[int] = None
    exhibition_advantage: Optional[int] = None
    collection_pas: Optional[int] = None
    effective_pas: Optional[int] = None
    reputation_level: Optional[str] = None
    collection_level: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Phase1_9Stats:
    """Statistics for a Phase 1.9 run."""
    total_processed: int = 0
    museums_updated: int = 0
    museums_matched: int = 0
    museums_not_found: int = 0
    museums_skipped_current: int = 0
    museums_skipped_no_changes: int = 0
    fields_updated: int = 0


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


def normalize_name_for_matching(name: str) -> str:
    """Normalize museum name for matching (lowercase, remove punctuation, extra spaces)."""
    if not name:
        return ""
    
    # Lowercase
    name = name.lower()
    
    # Remove possessive apostrophes
    name = name.replace("'s", "s")
    name = name.replace("'", "")
    
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def find_latest_spreadsheet() -> Optional[Path]:
    """Find the most recent museum_planner_MASTER spreadsheet."""
    if not DOC_SOURCE_DIR.exists():
        return None
    
    # Look for museum_planner_MASTER*.xlsx files
    candidates = list(DOC_SOURCE_DIR.glob("museum_planner_MASTER*.xlsx"))
    
    if not candidates:
        return None
    
    # Sort by modification time, return most recent
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def load_planner_spreadsheet(spreadsheet_path: Path) -> dict[str, PlannerMetadata]:
    """Load planner metadata from spreadsheet.
    
    Returns:
        Dictionary mapping normalized museum name to PlannerMetadata
    """
    print(f"Loading planner spreadsheet: {spreadsheet_path}")
    
    try:
        df = pd.read_excel(spreadsheet_path)
    except Exception as e:
        print(f"ERROR: Failed to read spreadsheet: {e}")
        return {}
    
    # Expected columns (with flexible matching)
    column_map = {
        "Museum Name": "museum_name",
        "Priority Score": "priority_score",
        "Outcome Tier": "outcome_tier",
        "Consider Label": "consider_label",
        "Historical Context": "historical_context",
        "Impressionist Strength": "impressionist_strength",
        "Modern/ Contemporary Strength": "modern_contemporary_strength",
        "Traditional / Pre‑Modern Art Strength": "traditional_strength",
        "Exhibition-Centric Advantage (ECA)": "exhibition_advantage",
        "Collection-Based PAS": "collection_pas",
        "Effective PAS": "effective_pas",
        "Reputation Level": "reputation_level",
        "Collection Level": "collection_level",
        "Notes": "notes",
    }
    
    # Find actual column names (case-insensitive partial match)
    actual_columns = {}
    for expected, field_name in column_map.items():
        for col in df.columns:
            if expected.lower() in col.lower():
                actual_columns[field_name] = col
                break
    
    if "museum_name" not in actual_columns:
        print("ERROR: Could not find 'Museum Name' column in spreadsheet")
        return {}
    
    # Build metadata dictionary
    metadata_by_name: dict[str, PlannerMetadata] = {}
    
    for idx, row in df.iterrows():
        museum_name = row.get(actual_columns["museum_name"])
        if pd.isna(museum_name) or not museum_name:
            continue
        
        # Normalize name for matching
        normalized_name = normalize_name_for_matching(str(museum_name))
        
        # Extract metadata
        metadata = PlannerMetadata()
        
        for field_name, col_name in actual_columns.items():
            if field_name == "museum_name":
                continue
            
            value = row.get(col_name)
            
            # Skip NaN values
            if pd.isna(value):
                continue
            
            # Convert to appropriate type
            if field_name in ["priority_score", "historical_context", "impressionist_strength",
                             "modern_contemporary_strength", "traditional_strength",
                             "exhibition_advantage", "collection_pas", "effective_pas"]:
                try:
                    setattr(metadata, field_name, int(value))
                except (ValueError, TypeError):
                    pass
            else:
                setattr(metadata, field_name, str(value).strip())
        
        metadata_by_name[normalized_name] = metadata
    
    print(f"Loaded metadata for {len(metadata_by_name)} museums from spreadsheet")
    
    return metadata_by_name


def match_museum(museum: dict, planner_data: dict[str, PlannerMetadata]) -> Optional[PlannerMetadata]:
    """Find matching planner metadata for a museum.
    
    Args:
        museum: Museum record from state file
        planner_data: Dictionary of planner metadata indexed by normalized name
        
    Returns:
        PlannerMetadata if match found, None otherwise
    """
    museum_name = museum.get("museum_name", "")
    if not museum_name:
        return None
    
    normalized_name = normalize_name_for_matching(museum_name)
    
    # Direct match
    if normalized_name in planner_data:
        return planner_data[normalized_name]
    
    # Try partial match (for cases where spreadsheet has slightly different name)
    for planner_name, metadata in planner_data.items():
        # If either name is a substring of the other (and both > 10 chars to avoid false positives)
        if len(normalized_name) > 10 and len(planner_name) > 10:
            if planner_name in normalized_name or normalized_name in planner_name:
                return metadata
    
    return None


def update_museum_with_planner_data(
    museum: dict,
    metadata: PlannerMetadata,
) -> int:
    """Update museum record with planner metadata.
    
    Args:
        museum: Museum record to update
        metadata: Planner metadata to merge in
        
    Returns:
        Number of fields updated (only counts actual changes)
    """
    fields_updated = 0
    
    # Map metadata fields to museum record field names (prefixed with planner_)
    field_mapping = {
        "priority_score": "planner_priority_score",
        "outcome_tier": "planner_outcome_tier",
        "consider_label": "planner_consider_label",
        "historical_context": "planner_historical_context",
        "impressionist_strength": "planner_impressionist_strength",
        "modern_contemporary_strength": "planner_modern_contemporary_strength",
        "traditional_strength": "planner_traditional_strength",
        "exhibition_advantage": "planner_exhibition_advantage",
        "collection_pas": "planner_collection_pas",
        "effective_pas": "planner_effective_pas",
        "reputation_level": "planner_reputation_level",
        "collection_level": "planner_collection_level",
        "notes": "planner_notes",
    }
    
    for metadata_field, museum_field in field_mapping.items():
        value = getattr(metadata, metadata_field)
        
        if value is None:
            continue
        
        # Update if different from current value
        current_value = museum.get(museum_field)
        if current_value != value:
            museum[museum_field] = value
            fields_updated += 1
    
    # Track when planner data was last updated
    museum["planner_data_updated_at"] = now_utc_iso()
    
    # Add to data sources
    data_sources = museum.get("data_sources", [])
    if not isinstance(data_sources, list):
        data_sources = []
    if "museum_planner_spreadsheet" not in data_sources:
        data_sources.append("museum_planner_spreadsheet")
        museum["data_sources"] = data_sources
    
    return fields_updated


def process_state(
    state_code: str,
    planner_data: dict[str, PlannerMetadata],
    spreadsheet_mtime: float,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Phase1_9Stats:
    """Process all museums in a state for planner metadata enrichment.
    
    Args:
        state_code: Two-letter state code
        planner_data: Dictionary of planner metadata
        spreadsheet_mtime: Modification time of spreadsheet file
        force: Force re-sync even if spreadsheet hasn't changed
        dry_run: If True, don't make changes
        
    Returns:
        Phase1_9Stats with processing statistics
    """
    stats = Phase1_9Stats()
    
    state_file = STATES_DIR / f"{state_code}.json"
    if not state_file.exists():
        print(f"ERROR: State file not found: {state_file}")
        return stats
    
    state_data = load_json(state_file)
    museums = state_data.get("museums", [])
    total = len(museums)
    
    print(f"\n[STATE: {state_code}] Processing {total} museums")
    
    changes_made = False
    
    for idx, museum in enumerate(museums, 1):
        museum_name = museum.get("museum_name", "")[:50]
        stats.total_processed += 1
        
        # Try to match with planner data
        metadata = match_museum(museum, planner_data)
        
        if not metadata:
            stats.museums_not_found += 1
            continue
        
        stats.museums_matched += 1
        
        # Check if museum is already current (unless force or dry_run)
        if not force and not dry_run:
            last_updated = museum.get("planner_data_updated_at")
            if last_updated:
                try:
                    # Parse timestamp (handle both formats: with/without timezone)
                    last_updated_str = last_updated.replace("Z", "+00:00")
                    last_sync_time = datetime.fromisoformat(last_updated_str).timestamp()
                    
                    # If spreadsheet is older than last sync, skip
                    if spreadsheet_mtime <= last_sync_time:
                        stats.museums_skipped_current += 1
                        continue
                except (ValueError, AttributeError):
                    pass  # If timestamp parsing fails, proceed with update
        
        if dry_run:
            print(f"  [{idx}/{total}] {museum_name} - MATCH FOUND (would update)")
            continue
        
        # Update museum with planner metadata
        fields_count = update_museum_with_planner_data(museum, metadata)
        
        if fields_count > 0:
            stats.museums_updated += 1
            stats.fields_updated += fields_count
            changes_made = True
            
            print(f"  [{idx}/{total}] {museum_name} - {fields_count} fields updated")
            
            # Update timestamp
            museum["updated_at"] = now_utc_iso()
        else:
            stats.museums_skipped_no_changes += 1
            # Don't print for museums with no changes to reduce noise
    
    # Save state file if changes were made
    if changes_made and not dry_run:
        state_data["updated_at"] = now_utc_iso()
        save_json(state_file, state_data)
        print(f"\n  Saved changes to {state_file}")
    elif dry_run and stats.museums_matched > 0:
        print(f"\n  [DRY RUN] Would save changes to {state_file}")
    
    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 1.9: Museum Planner Metadata Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    # Scope selection
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CA)")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Process all states")
    
    # Options
    parser.add_argument("--spreadsheet", help="Path to museum_planner_MASTER spreadsheet (auto-detect if not specified)")
    parser.add_argument("--force", action="store_true", help="Force re-sync even if spreadsheet hasn't changed")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    
    args = parser.parse_args()
    
    # Determine state codes to process
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
    
    # Find or use specified spreadsheet
    if args.spreadsheet:
        spreadsheet_path = Path(args.spreadsheet)
    else:
        spreadsheet_path = find_latest_spreadsheet()
    
    if not spreadsheet_path or not spreadsheet_path.exists():
        print("ERROR: Could not find museum_planner_MASTER spreadsheet")
        if not args.spreadsheet:
            print(f"  Searched in: {DOC_SOURCE_DIR}")
        return 1
    
    # Load planner data
    planner_data = load_planner_spreadsheet(spreadsheet_path)
    if not planner_data:
        print("ERROR: Failed to load planner data from spreadsheet")
        return 1
    
    # Create run directory for logging
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"phase1_9-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Get spreadsheet modification time
    spreadsheet_mtime = spreadsheet_path.stat().st_mtime
    
    print("="*60)
    print("Phase 1.9: Museum Planner Metadata Integration")
    print("="*60)
    print(f"Spreadsheet: {spreadsheet_path.name}")
    print(f"States: {', '.join(state_codes)}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Run ID: {run_id}")
    print("=" * 60)
    
    # Process each state
    total_stats = Phase1_9Stats()
    
    for state_code in state_codes:
        stats = process_state(
            state_code=state_code,
            planner_data=planner_data,
            spreadsheet_mtime=spreadsheet_mtime,
            force=args.force,
            dry_run=args.dry_run,
        )
        
        total_stats.total_processed += stats.total_processed
        total_stats.museums_updated += stats.museums_updated
        total_stats.museums_matched += stats.museums_matched
        total_stats.museums_not_found += stats.museums_not_found
        total_stats.museums_skipped_current += stats.museums_skipped_current
        total_stats.museums_skipped_no_changes += stats.museums_skipped_no_changes
        total_stats.fields_updated += stats.fields_updated
    
    # Save run summary
    summary = {
        "run_id": run_id,
        "spreadsheet": str(spreadsheet_path),
        "states": state_codes,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "museums_matched": total_stats.museums_matched,
        "museums_updated": total_stats.museums_updated,
        "museums_not_found": total_stats.museums_not_found,
        "museums_skipped_current": total_stats.museums_skipped_current,
        "museums_skipped_no_changes": total_stats.museums_skipped_no_changes,
        "fields_updated": total_stats.fields_updated,
        "match_rate": (
            f"{total_stats.museums_matched / total_stats.total_processed * 100:.1f}%"
            if total_stats.total_processed > 0 else "0%"
        ),
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Phase 1.9 Complete")
    print("=" * 60)
    print(f"  Total processed:      {total_stats.total_processed}")
    print(f"  Museums matched:      {total_stats.museums_matched}")
    print(f"  Museums updated:      {total_stats.museums_updated}")
    print(f"  Skipped (current):    {total_stats.museums_skipped_current}")
    print(f"  Skipped (no changes): {total_stats.museums_skipped_no_changes}")
    print(f"  Museums not found:    {total_stats.museums_not_found}")
    print(f"  Fields updated:       {total_stats.fields_updated}")
    if total_stats.total_processed > 0:
        match_rate = total_stats.museums_matched / total_stats.total_processed * 100
        print(f"  Match rate:           {match_rate:.1f}%")
    print(f"\n  Run directory: {run_dir}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
