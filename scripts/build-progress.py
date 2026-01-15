#!/usr/bin/env python3
"""Build a Phase 1 progress summary artifact.

Produces a small JSON file suitable for a GitHub Pages UI dashboard:
- total museums
- FULL vs placeholder counts
- per-state totals + FULL/placeholder breakdown

Output (default):
- data/index/progress.json

Usage:
  python scripts/build-progress.py
  python scripts/build-progress.py --out data/index/progress.json

This script is intentionally deterministic and offline: no network calls.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = PROJECT_ROOT / "data" / "index" / "all-museums.json"
DEFAULT_OUT = PROJECT_ROOT / "data" / "index" / "progress.json"

_PLACEHOLDER_STRINGS = {"", "tbd", "unknown", "n/a"}

PHASE1_SCHEMA_REQUIRED_FIELDS = [
    "museum_id",
    "country",
    "state_province",
    "city",
    "museum_name",
    "website",
    "museum_type",
    "street_address",
    "postal_code",
]

MRD_CORE_FIELDS = [
    "city_tier",
    "museum_type",
    "status",
    "reputation",
    "collection_tier",
    "time_needed",
    "nearby_museum_count",
    "notes",
    "data_sources",
    "confidence",
]

ART_MUSEUM_SCORING_FIELDS = [
    "impressionist_strength",
    "modern_contemporary_strength",
    "primary_art",
    "historical_context_score",
    "priority_score",
    "is_scored",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().casefold() in _PLACEHOLDER_STRINGS:
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def is_art_museum(m: dict[str, Any]) -> bool:
    """Check if museum is an art museum requiring scoring."""
    primary_domain = m.get("primary_domain", "")
    return primary_domain == "Art"


def has_time_estimate(m: dict[str, Any]) -> bool:
    return not is_missing(m.get("time_needed")) or not is_missing(m.get("estimated_visit_minutes"))


def has_data_sources(m: dict[str, Any]) -> bool:
    ds = m.get("data_sources")
    return isinstance(ds, list) and len(ds) > 0


def has_confidence(m: dict[str, Any]) -> bool:
    c = m.get("confidence")
    if isinstance(c, bool):
        return False
    if isinstance(c, int):
        return 1 <= c <= 5
    return False


def is_full_record(m: dict[str, Any]) -> bool:
    """
    MRD-compliant FULL record definition.
    
    A museum is FULL when:
    1. All schema required fields are present
    2. All MRD core fields are present
    3. For art museums: ALL scoring fields must be present and scored
    """
    # Check schema required fields
    for f in PHASE1_SCHEMA_REQUIRED_FIELDS:
        if is_missing(m.get(f)):
            return False

    # Check MRD core fields
    for f in MRD_CORE_FIELDS:
        if f == "data_sources":
            if not has_data_sources(m):
                return False
            continue
        if f == "confidence":
            if not has_confidence(m):
                return False
            continue
        if is_missing(m.get(f)):
            return False

    # For art museums: require ALL scoring fields to be present
    if is_art_museum(m):
        for f in ART_MUSEUM_SCORING_FIELDS:
            value = m.get(f)
            
            # Special handling for is_scored: must be True
            if f == "is_scored":
                if value is not True:
                    return False
                continue
            
            # All other scoring fields must be non-null
            if is_missing(value):
                return False
        
        # Art museums must have a computed priority_score
        if m.get("priority_score") is None:
            return False

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 1 progress summary JSON")
    parser.add_argument("--in", dest="in_path", default=str(INDEX_PATH), help="Input all-museums.json path")
    parser.add_argument("--out", dest="out_path", default=str(DEFAULT_OUT), help="Output progress path")
    args = parser.parse_args()

    in_path = Path(args.in_path)
    out_path = Path(args.out_path)

    data = load_json(in_path)
    museums = data.get("museums")
    if not isinstance(museums, list):
        raise SystemExit(f"Invalid museums array in {in_path}")

    totals = {"total_museums": len(museums), "full": 0, "placeholder": 0}

    per_state: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "full": 0, "placeholder": 0})

    for m in museums:
        state = (m.get("state_province") or "ZZ").upper()
        per_state[state]["total"] += 1

        if is_full_record(m):
            totals["full"] += 1
            per_state[state]["full"] += 1
        else:
            totals["placeholder"] += 1
            per_state[state]["placeholder"] += 1

    full_pct = (totals["full"] / totals["total_museums"] * 100.0) if totals["total_museums"] else 0.0

    payload = {
        "generated_from": str(in_path.as_posix()),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_museums": totals["total_museums"],
        "full": totals["full"],
        "placeholder": totals["placeholder"],
        "full_pct": round(full_pct, 2),
        "by_state": {k: per_state[k] for k in sorted(per_state.keys())},
        "definition": {
            "notes": "MRD-compliant FULL definition: All museums require MRD core fields. Art museums MUST be scored with priority_score to be FULL.",
            "schema_required_fields": PHASE1_SCHEMA_REQUIRED_FIELDS,
            "mrd_core_fields": MRD_CORE_FIELDS,
            "art_museum_scoring_fields": ART_MUSEUM_SCORING_FIELDS,
            "art_museum_rule": "Art museums (primary_domain='Art') require ALL scoring fields + priority_score to be FULL",
        },
    }

    save_json(out_path, payload)
    print(f"[OK] Wrote {out_path}")
    print(f"[OK] FULL: {totals['full']} / {totals['total_museums']} ({payload['full_pct']}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
