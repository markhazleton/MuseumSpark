#!/usr/bin/env python3
"""
Validate MuseumSpark state JSON files against the museum schema.

Usage:
    python validate-json.py              # Validate all state files
    python validate-json.py --state AL   # Validate specific state
"""

import json
import sys
import argparse
from pathlib import Path
from jsonschema import validate, ValidationError, SchemaError

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_schema(schema_path):
    """Load the JSON schema from file."""
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Schema file not found at {schema_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in schema file: {e}")
        sys.exit(1)

def load_state_file(file_path):
    """Load a state JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {file_path}: {e}")
        return None

def validate_state_file(file_path, schema):
    """Validate a single state file against the schema."""
    data = load_state_file(file_path)
    if data is None:
        return False

    try:
        validate(instance=data, schema=schema)
        print(f"[OK] {file_path.name}: Valid")
        return True
    except ValidationError as e:
        print(f"[ERROR] {file_path.name}: Validation failed")
        print(f"   Error: {e.message}")
        if e.path:
            print(f"   Path: {' -> '.join(str(p) for p in e.path)}")
        return False
    except SchemaError as e:
        print(f"[ERROR] Schema error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Validate MuseumSpark state JSON files')
    parser.add_argument('--state', type=str, help='Validate specific state (e.g., AL, CA)')
    args = parser.parse_args()

    # Determine script location and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    schema_path = project_root / 'data' / 'schema' / 'museum.schema.json'
    states_dir = project_root / 'data' / 'states'

    # Load schema
    print("Loading schema...")
    schema = load_schema(schema_path)
    print(f"[OK] Schema loaded from {schema_path}\n")

    # Determine which files to validate
    if args.state:
        state_code = args.state.upper()
        files = [states_dir / f"{state_code}.json"]
        if not files[0].exists():
            print(f"[ERROR] State file not found: {files[0]}")
            sys.exit(1)
    else:
        files = sorted(states_dir.glob('*.json'))
        if not files:
            print(f"[ERROR] No JSON files found in {states_dir}")
            sys.exit(1)

    # Validate files
    print(f"Validating {len(files)} file(s)...\n")
    valid_count = 0
    invalid_count = 0

    for file_path in files:
        if validate_state_file(file_path, schema):
            valid_count += 1
        else:
            invalid_count += 1

    # Summary
    print(f"\n{'='*50}")
    print(f"Validation Summary:")
    print(f"  [OK] Valid files: {valid_count}")
    print(f"  [ERROR] Invalid files: {invalid_count}")
    print(f"{'='*50}")

    if invalid_count > 0:
        sys.exit(1)
    else:
        print("\nAll files are valid!")
        sys.exit(0)

if __name__ == '__main__':
    main()
