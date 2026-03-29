#!/usr/bin/env python3
"""Build a missing-field report for Phase 1 curation progress.

Produces a machine-readable JSON report summarizing:
- total museums
- count FULL vs placeholder (per Phase 1 spec definition, approximated)
- missing key fields (overall + per state)

Output:
- data/index/missing-report.json

Usage:
  python scripts/build-missing-report.py
  python scripts/build-missing-report.py --out data/index/missing-report.json

This script is intentionally deterministic and offline: no network calls.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_PATH = PROJECT_ROOT / "data" / "index" / "all-museums.json"
DEFAULT_OUT = PROJECT_ROOT / "data" / "index" / "missing-report.json"

_PLACEHOLDER_STRINGS = {"", "tbd", "unknown", "n/a"}


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

PHASE1_ENRICHMENT_CORE_FIELDS = [
    "primary_domain",
    "status",
    "reputation",
    "collection_tier",
    "notes",
    "data_sources",
    "confidence",
]

PHASE1_TIME_ESTIMATE_FIELDS = ["time_needed", "estimated_visit_minutes"]


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
    # Phase 1 spec “FULL” definition.
    # Intentionally ignores art-scoring fields; those can be layered later.
    for f in PHASE1_SCHEMA_REQUIRED_FIELDS:
        if is_missing(m.get(f)):
            return False

    for f in PHASE1_ENRICHMENT_CORE_FIELDS:
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

    if not has_time_estimate(m):
        return False

    return True


def missing_fields(m: dict[str, Any], fields: list[str]) -> list[str]:
    out: list[str] = []
    for f in fields:
        if is_missing(m.get(f)):
            out.append(f)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build missing-field report JSON")
    parser.add_argument("--in", dest="in_path", default=str(INDEX_PATH), help="Input all-museums.json path")
    parser.add_argument("--out", dest="out_path", default=str(DEFAULT_OUT), help="Output report path")
    args = parser.parse_args()

    in_path = Path(args.in_path)
    out_path = Path(args.out_path)

    data = load_json(in_path)
    museums = data.get("museums")
    if not isinstance(museums, list):
        raise SystemExit(f"Invalid museums array in {in_path}")

    totals = {
        "total_museums": len(museums),
        "full": 0,
        "placeholder": 0,
    }

    missing_overall = Counter()
    missing_by_state: dict[str, Counter] = defaultdict(Counter)

    # Keep a small sample list to make it easy to spot-check
    examples_by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for m in museums:
        state = (m.get("state_province") or "ZZ").upper()

        full = is_full_record(m)
        if full:
            totals["full"] += 1
        else:
            totals["placeholder"] += 1

        # Track missing Phase 1 fields (schema-required + enrichment core)
        missing: list[str] = []

        missing.extend(missing_fields(m, PHASE1_SCHEMA_REQUIRED_FIELDS))
        missing.extend(missing_fields(m, [f for f in PHASE1_ENRICHMENT_CORE_FIELDS if f not in {"data_sources", "confidence"}]))

        if not has_data_sources(m):
            missing.append("data_sources")
        if not has_confidence(m):
            missing.append("confidence")
        if not has_time_estimate(m):
            missing.append("time_estimate")

        for f in missing:
            missing_overall[f] += 1
            missing_by_state[state][f] += 1
            if len(examples_by_field[f]) < 10:
                examples_by_field[f].append(
                    {
                        "museum_id": m.get("museum_id"),
                        "museum_name": m.get("museum_name"),
                        "state_province": state,
                    }
                )

    full_pct = (totals["full"] / totals["total_museums"] * 100.0) if totals["total_museums"] else 0.0

    report = {
        "generated_from": str(in_path.as_posix()),
        "total_museums": totals["total_museums"],
        "full": totals["full"],
        "placeholder": totals["placeholder"],
        "full_pct": round(full_pct, 2),
        "missing_overall": dict(missing_overall.most_common()),
        "missing_by_state": {k: dict(v.most_common()) for k, v in sorted(missing_by_state.items())},
        "examples_by_field": examples_by_field,
        "definition": {
            "phase1_schema_required_fields": PHASE1_SCHEMA_REQUIRED_FIELDS,
            "phase1_enrichment_core_fields": PHASE1_ENRICHMENT_CORE_FIELDS,
            "phase1_time_estimate_fields": PHASE1_TIME_ESTIMATE_FIELDS,
            "notes": "FULL requires all Phase 1 schema-required + enrichment core fields, plus either time_needed or estimated_visit_minutes.",
        },
    }

    save_json(out_path, report)
    print(f"[OK] Wrote {out_path}")
    print(f"[OK] FULL: {totals['full']} / {totals['total_museums']} ({report['full_pct']}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
