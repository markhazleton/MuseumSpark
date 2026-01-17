#!/usr/bin/env python3
"""Ingest the Walker Art Reciprocal roster into MuseumSpark state files and rebuild the master index.

Workflow implemented:
1) Validate walker-reciprocal.csv (basic integrity checks)
2) Ensure every roster museum exists in a per-state working file at data/states/{STATE_CODE}.json
   - Adds stub records for missing museums with placeholder values for required schema fields.
   - Uses website URL and (state,name,city) matching to avoid duplicates.
3) Rebuild data/index/all-museums.json from the state files (via scripts/build-index.py)

Usage:
  python scripts/ingest-walker-reciprocal.py --rebuild-index

Notes:
- This script is intentionally conservative: it only *adds* museums, it does not overwrite
  existing enriched records.
- Stub records use:
  - street_address: "TBD"
  - postal_code: "TBD"
  - museum_type: "Unknown"
  - status: "unknown"

Exit codes:
  0 = success
  1 = validation or processing error
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ROSTER_CSV = PROJECT_ROOT / "data" / "index" / "walker-reciprocal.csv"
STATES_DIR = PROJECT_ROOT / "data" / "states"
BUILD_INDEX = PROJECT_ROOT / "scripts" / "builders" / "build-index.py"

REQUIRED_HEADERS = ["STATE", "NAME", "CITY", "URL"]

US_STATE_TO_CODE: dict[str, str] = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}


@dataclass(frozen=True)
class RosterRow:
    state: str
    name: str
    city: str
    url: str


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_url(url: str) -> str:
    url = url.strip()
    url = re.sub(r"\s+", "", url)
    url = url.replace("://%20", "://")
    while url.endswith("/"):
        url = url[:-1]
    return url.casefold()


_slug_keep = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    value = value.casefold()
    value = _slug_keep.sub("-", value)
    return value.strip("-")


def compute_museum_id(country_code: str, state_code: str, city: str, museum_name: str) -> str:
    # Keep IDs stable and readable; align with existing convention where possible.
    return "-".join(
        part
        for part in [
            slugify(country_code),
            slugify(state_code),
            slugify(city or "unknown"),
            slugify(museum_name),
        ]
        if part
    )


def read_roster() -> list[RosterRow]:
    if not ROSTER_CSV.exists():
        raise FileNotFoundError(f"Missing roster CSV: {ROSTER_CSV}")

    rows: list[RosterRow] = []
    with ROSTER_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        missing = [h for h in REQUIRED_HEADERS if h not in headers]
        if missing:
            raise ValueError(f"Roster CSV missing headers {missing}; found: {headers}")

        for i, raw in enumerate(reader, start=1):
            state = (raw.get("STATE") or "").strip()
            name = (raw.get("NAME") or "").strip()
            city = (raw.get("CITY") or "").strip()
            url = (raw.get("URL") or "").strip()

            if not state or not name or not url:
                raise ValueError(f"Roster row {i} missing required fields (STATE/NAME/URL)")
            if not is_http_url(url):
                raise ValueError(f"Roster row {i} has invalid URL: {url}")

            rows.append(RosterRow(state=state, name=name, city=city, url=url))

    return rows


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def ensure_state_file(state_name: str, state_code: str) -> dict[str, Any]:
    path = STATES_DIR / f"{state_code}.json"
    if path.exists():
        data = load_json(path)
        # Ensure basics exist
        if "museums" not in data or not isinstance(data["museums"], list):
            data["museums"] = []
        if not data.get("state"):
            data["state"] = state_name
        if not data.get("state_code"):
            data["state_code"] = state_code
        return data

    return {
        "state": state_name,
        "state_code": state_code,
        "last_updated": now_iso(),
        "museums": [],
    }


def museum_matches(existing: dict[str, Any], row: RosterRow, state_name: str) -> bool:
    existing_url = normalize_url(str(existing.get("website") or ""))
    row_url = normalize_url(row.url)
    if existing_url and existing_url == row_url:
        return True

    # Fallback: state + name + city match (case-insensitive)
    if (existing.get("state_province") or "").casefold() != state_name.casefold():
        return False

    if (existing.get("museum_name") or "").casefold() != row.name.casefold():
        return False

    # City can be missing in roster; only compare when roster has a city.
    if row.city.strip():
        return (existing.get("city") or "").casefold() == row.city.casefold()

    return True


def add_stub_museum(state_name: str, state_code: str, row: RosterRow) -> dict[str, Any]:
    country = "USA" if state_name.casefold() in US_STATE_TO_CODE else state_name
    city = row.city.strip() or "Unknown"

    museum_id = compute_museum_id(
        country_code=("usa" if country == "USA" else country),
        state_code=state_code,
        city=city,
        museum_name=row.name,
    )

    return {
        "museum_id": museum_id,
        "country": country,
        "state_province": state_name,
        "city": city,
        "museum_name": row.name,
        "alternate_names": None,
        "website": row.url,
        "status": "unknown",
        "last_updated": datetime.now(timezone.utc).date().isoformat(),
        "street_address": "TBD",
        "address_line2": None,
        "postal_code": "TBD",
        "latitude": None,
        "longitude": None,
        "place_id": None,
        "address_source": "unknown",
        "address_last_verified": None,
        "museum_type": "Unknown",
        "primary_domain": None,
        "topics": None,
        "audience_focus": None,
        "open_hours_url": None,
        "open_hour_notes": None,
        "tickets_url": None,
        "reservation_required": None,
        "accessibility_url": None,
        "reputation": None,
        "collection_tier": None,
        "time_needed": None,
        "estimated_visit_minutes": None,
        "best_season": None,
        "nearby_museum_count": None,
        "visit_priority_notes": None,
        "parking_notes": None,
        "public_transit_notes": None,
        "impressionist_strength": None,
        "modern_contemporary_strength": None,
        "primary_art": None,
        "historical_context_score": None,
        "priority_score": None,
        "scoring_version": None,
        "scored_by": None,
        "score_notes": None,
        "score_last_verified": None,
        "data_sources": ["walker_reciprocal"],
        "confidence": None,
        "row_notes_internal": "Seeded from walker-reciprocal roster; needs enrichment.",
        "created_at": datetime.now(timezone.utc).date().isoformat(),
        "updated_at": datetime.now(timezone.utc).date().isoformat(),
        "notes": None,
    }


def classify_state(row_state: str) -> tuple[str, str]:
    """Return (state_name, state_code). Non-US entries go to International (ZZ)."""

    key = row_state.casefold().strip()
    if key in US_STATE_TO_CODE:
        return row_state, US_STATE_TO_CODE[key]

    # Non-US (e.g., Bermuda, Brazil)
    return "International", "ZZ"


def ingest(dry_run: bool) -> tuple[int, int, list[str]]:
    roster = read_roster()

    states_changed: set[str] = set()
    total_added = 0

    # Load or create state files and add missing museums
    grouped: dict[tuple[str, str], list[RosterRow]] = {}
    for row in roster:
        state_name, state_code = classify_state(row.state)
        grouped.setdefault((state_name, state_code), []).append(row)

    for (state_name, state_code), rows in grouped.items():
        state_path = STATES_DIR / f"{state_code}.json"
        state_data = ensure_state_file(state_name, state_code)
        museums: list[dict[str, Any]] = state_data.get("museums", [])

        added_here = 0
        for row in rows:
            match_state_name = row.state if state_code == "ZZ" else state_name
            if any(museum_matches(m, row=row, state_name=match_state_name) for m in museums):
                continue

            # For international stubs, keep state_province as the roster 'STATE' value when possible.
            effective_state_name = row.state if state_code == "ZZ" else state_name

            museums.append(add_stub_museum(effective_state_name, state_code, row))
            added_here += 1

        if added_here:
            total_added += added_here
            states_changed.add(state_code)
            state_data["museums"] = museums
            state_data["last_updated"] = now_iso()

            if not dry_run:
                save_json(state_path, state_data)

    return len(roster), total_added, sorted(states_changed)


def rebuild_index() -> None:
    if not BUILD_INDEX.exists():
        raise FileNotFoundError(f"Missing build-index script: {BUILD_INDEX}")

    subprocess.run(
        [sys.executable, str(BUILD_INDEX)],
        cwd=str(PROJECT_ROOT),
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Walker reciprocal roster into state files")
    parser.add_argument("--dry-run", action="store_true", help="Compute changes without writing files")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild data/index/all-museums.json after ingest")
    args = parser.parse_args()

    STATES_DIR.mkdir(parents=True, exist_ok=True)

    roster_count, added, changed_states = ingest(dry_run=args.dry_run)

    print(f"[OK] Roster rows: {roster_count}")
    print(f"[OK] Museums added (stubs): {added}")
    print(f"[OK] State files changed: {len(changed_states)}")
    if changed_states:
        print("[OK] Changed codes: " + ", ".join(changed_states))

    if args.rebuild_index and not args.dry_run:
        print("[OK] Rebuilding data/index/all-museums.json...")
        rebuild_index()
        print("[OK] Rebuilt master index")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
