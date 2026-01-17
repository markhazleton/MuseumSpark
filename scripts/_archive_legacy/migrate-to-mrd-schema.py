#!/usr/bin/env python3
"""
Migrate existing museum data to MRD-aligned schema.

This script converts:
- reputation: string enum → numeric 0-3
- collection_tier: string enum → numeric 0-3
- Validates structure and writes back to state files

MRD Mappings:
- Reputation: International=0, National=1, Regional=2, Local=3
- Collection Tier: Flagship=0, Strong=1, Moderate=2, Small=3

Usage:
    python migrate-to-mrd-schema.py [--dry-run] [--state STATE_CODE]
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import argparse

# MRD mapping tables (Section 4.11, 4.12)
REPUTATION_MAP = {
    "International": 0,
    "National": 1,
    "Regional": 2,
    "Local": 3
}

COLLECTION_MAP = {
    "Flagship": 0,
    "Strong": 1,
    "Moderate": 2,
    "Small": 3
}


def migrate_museum(museum: Dict) -> tuple[Dict, List[str]]:
    """
    Migrate a single museum record to MRD schema.
    
    Returns:
        tuple: (migrated_museum, list of changes made)
    """
    changes = []
    
    # Migrate reputation (string → numeric)
    if isinstance(museum.get("reputation"), str):
        old_value = museum["reputation"]
        new_value = REPUTATION_MAP.get(old_value)
        if new_value is not None:
            museum["reputation"] = new_value
            changes.append(f"reputation: '{old_value}' → {new_value}")
        else:
            print(f"⚠️  WARNING: Unknown reputation value '{old_value}' in {museum.get('museum_id')}")
    
    # Migrate collection_tier (string → numeric)
    if isinstance(museum.get("collection_tier"), str):
        old_value = museum["collection_tier"]
        new_value = COLLECTION_MAP.get(old_value)
        if new_value is not None:
            museum["collection_tier"] = new_value
            changes.append(f"collection_tier: '{old_value}' → {new_value}")
        else:
            print(f"⚠️  WARNING: Unknown collection_tier value '{old_value}' in {museum.get('museum_id')}")
    
    # Migrate primary_art (remove deprecated values "None" and "Tie")
    if museum.get("primary_art") in ["None", "Tie"]:
        old_value = museum["primary_art"]
        museum["primary_art"] = None
        changes.append(f"primary_art: '{old_value}' → null (deprecated value)")
    
    # Migrate impressionist_strength (0 → 1, per MRD 1-5 scale where 1=None)
    if museum.get("impressionist_strength") == 0:
        museum["impressionist_strength"] = 1
        changes.append(f"impressionist_strength: 0 → 1 (MRD 1=None)")
    
    # Migrate modern_contemporary_strength (0 → 1, per MRD 1-5 scale where 1=None)
    if museum.get("modern_contemporary_strength") == 0:
        museum["modern_contemporary_strength"] = 1
        changes.append(f"modern_contemporary_strength: 0 → 1 (MRD 1=None)")
    
    # Update timestamp if changes were made
    if changes:
        museum["updated_at"] = datetime.now().strftime("%Y-%m-%d")
    
    return museum, changes


def migrate_state_file(state_file: Path, dry_run: bool = False) -> tuple[int, int]:
    """
    Migrate a single state file.
    
    Returns:
        tuple: (museums_migrated, total_changes)
    """
    print(f"\n📄 Processing: {state_file.name}")
    
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ ERROR reading {state_file.name}: {e}")
        return 0, 0
    
    museums_migrated = 0
    total_changes = 0
    
    # Process each museum
    for i, museum in enumerate(data.get("museums", [])):
        migrated_museum, changes = migrate_museum(museum)
        
        if changes:
            museums_migrated += 1
            total_changes += len(changes)
            print(f"  ✓ {museum.get('museum_name', 'Unknown')} ({museum.get('museum_id', 'Unknown')})")
            for change in changes:
                print(f"    - {change}")
            
            # Update the museum in place
            data["museums"][i] = migrated_museum
    
    # Write back to file if not dry run
    if not dry_run and museums_migrated > 0:
        try:
            # Update state file timestamp
            data["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  💾 Saved changes to {state_file.name}")
        except Exception as e:
            print(f"❌ ERROR writing {state_file.name}: {e}")
            return 0, 0
    
    if museums_migrated == 0:
        print(f"  ℹ️  No migrations needed")
    
    return museums_migrated, total_changes


def main():
    parser = argparse.ArgumentParser(
        description="Migrate museum data to MRD-aligned schema"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )
    parser.add_argument(
        "--state",
        type=str,
        help="Migrate only a specific state code (e.g., CA, IL)"
    )
    
    args = parser.parse_args()
    
    # Determine script location and data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data" / "states"
    
    if not data_dir.exists():
        print(f"❌ ERROR: Data directory not found: {data_dir}")
        sys.exit(1)
    
    print("=" * 60)
    print("🔄 Museum Data Migration to MRD Schema")
    print("=" * 60)
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n")
    
    # Get list of state files to process
    if args.state:
        state_files = [data_dir / f"{args.state.upper()}.json"]
        if not state_files[0].exists():
            print(f"❌ ERROR: State file not found: {state_files[0].name}")
            sys.exit(1)
    else:
        state_files = sorted(data_dir.glob("*.json"))
    
    print(f"📂 Found {len(state_files)} state file(s) to process\n")
    
    # Process all state files
    total_museums_migrated = 0
    total_changes_made = 0
    files_with_changes = 0
    
    for state_file in state_files:
        museums, changes = migrate_state_file(state_file, dry_run=args.dry_run)
        total_museums_migrated += museums
        total_changes_made += changes
        if museums > 0:
            files_with_changes += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Migration Complete")
    print("=" * 60)
    print(f"📊 Files processed: {len(state_files)}")
    print(f"📝 Files with changes: {files_with_changes}")
    print(f"🏛️  Museums migrated: {total_museums_migrated}")
    print(f"🔧 Total changes: {total_changes_made}")
    
    if args.dry_run:
        print("\n⚠️  DRY RUN: No files were modified")
        print("   Run without --dry-run to apply changes")
    
    print("\n💡 Next steps:")
    print("   1. Run validation: python scripts/validate-json.py")
    print("   2. Rebuild index: python scripts/build-index.py")
    print("   3. Review changes in git diff")


if __name__ == "__main__":
    main()
