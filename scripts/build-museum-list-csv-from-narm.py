#!/usr/bin/env python3
"""Build data/index/museum-list.csv from NARM-Winter-2025.pdf.

Produces a structured CSV containing:
- `source` column set to "NARM-2025" for every row
- `narm_phone` extracted from the PDF where present
- All museum metadata columns based on the JSON schema (data/schema/museum.schema.json)

For rows that match an existing museum record in data/index/all-museums.json, the CSV is populated
with that record's metadata. Otherwise the CSV includes the NARM-derived fields (state/city/name/phone)
with remaining metadata left blank.

Matching is forgiving and based on (state_province, city, museum_name) with punctuation-insensitive name
normalization and alternate-name support.

Usage:
  python scripts/build-museum-list-csv-from-narm.py
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = PROJECT_ROOT / "Documentation" / "_source" / "NARM-Winter-2025.pdf"
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema" / "museum.schema.json"
INDEX_PATH = PROJECT_ROOT / "data" / "index" / "all-museums.json"
OUT_PATH = PROJECT_ROOT / "data" / "index" / "museum-list.csv"

SOURCE_VALUE = "NARM-2025"

# Phone numbers in the roster are consistently 10 digits, often with hyphens, sometimes spaces.
PHONE_RE = re.compile(r"\b\d{3}[-\s]\d{3}[-\s]\d{4}(?:x\d+)?\b")

# Roster entry pattern: City, Museum Name, Phone
# Guardrails:
# - City must start with a capital letter and contain no digits (prevents matches like
#   "301-791-3132 Salem" when extraction runs entries together).
# - City max length keeps us from absorbing long disclaimer phrases.
ENTRY_RE = re.compile(
    r"(?P<city>[A-Z][A-Za-z .\-\u2019']{1,30}),\s*(?P<museum>[^,]{2,160}),\s*(?P<phone>\d{3}[-\s]\d{3}[-\s]\d{4}(?:x\d+)?)"
)

KNOWN_HEADINGS: list[str] = [
    # US states
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
    # Territories / DC
    "District of Columbia",
    "Puerto Rico",
    # Canada appears as a top-level heading in the roster
    "Canada",
]

CANADA_PROVINCE_CODE_TO_NAME = {
    "AB": "Alberta",
    "BC": "British Columbia",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "NS": "Nova Scotia",
    "NT": "Northwest Territories",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "Prince Edward Island",
    "QC": "Quebec",
    "SK": "Saskatchewan",
    "YT": "Yukon",
}


def normalize_space(value: str) -> str:
    value = value.replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_name_for_match(value: str) -> str:
    value = normalize_space(value)
    value = re.sub(r"^the\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"[^0-9a-zA-Z]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.casefold()


def clean_museum_name(value: str) -> str:
    value = normalize_space(value)
    value = re.sub(r"[\*\^]+", "", value)
    value = normalize_space(value)
    return value


def normalize_heading(value: str) -> str:
    value = normalize_space(value)
    if value in {"Washington, D.C.", "Washington DC", "D.C.", "DC"}:
        return "District of Columbia"
    return value


def _heading_occurrences(text: str) -> list[tuple[int, str]]:
    """Locate heading occurrences within extracted text.

    Headings frequently appear mid-line (e.g. "Winter 2025-2026 Alaska Hayward, ...").
    We only treat a word as a heading if it is followed by a city-like token ending in a comma.
    """

    if not text:
        return []

    candidates: dict[int, tuple[int, str]] = {}

    for heading in sorted(KNOWN_HEADINGS, key=len, reverse=True):
        # word-boundary-ish (avoid matching inside other words), followed by whitespace and "City,"
        pattern = re.compile(
            rf"(?<![A-Za-z]){re.escape(heading)}(?![A-Za-z])(?=\s+[A-Z][A-Za-z .\-\u2019']{{1,30}},)"
        )
        for m in pattern.finditer(text):
            start = m.start()
            normalized = normalize_heading(heading)
            # If multiple headings start at the same position, keep the longest one.
            prev = candidates.get(start)
            if prev is None or len(heading) > prev[0]:
                candidates[start] = (len(heading), normalized)

    occurrences = [(pos, val[1]) for pos, val in candidates.items()]
    occurrences.sort(key=lambda t: t[0])
    return occurrences


def detect_column_starts(page) -> list[float]:
    words = page.extract_words() or []
    city_like = [
        w
        for w in words
        if (w.get("text") or "").endswith(",")
        and (w["text"][:-1].isalpha())
        and w["text"][0].isupper()
    ]

    bins = [round(w["x0"] / 10) * 10 for w in city_like]
    counts = Counter(bins)
    if not counts:
        return [0.0]

    max_count = max(counts.values())
    candidates = [x for x, n in counts.items() if n >= max(5, int(max_count * 0.25))]
    candidates.sort()

    groups: list[list[float]] = []
    for x in candidates:
        if not groups or x - groups[-1][-1] > 60:
            groups.append([x])
        else:
            groups[-1].append(x)

    starts = [sum(g) / len(g) for g in groups]
    if len(starts) > 3:
        starts = starts[:3]

    return starts


def column_bboxes(page, starts: list[float]) -> list[tuple[float, float, float, float]]:
    w, h = page.width, page.height
    starts = sorted(starts)

    left_edges = [0.0]
    right_edges: list[float] = []
    for i in range(len(starts) - 1):
        mid = (starts[i] + starts[i + 1]) / 2
        right_edges.append(mid)
        left_edges.append(mid)
    right_edges.append(w)

    bounds: list[tuple[float, float, float, float]] = []
    for left, right in zip(left_edges, right_edges):
        bounds.append((max(0.0, left - 2), 0.0, min(w, right + 2), h))
    return bounds


@dataclass(frozen=True)
class NarmEntry:
    state_province: str
    city: str
    museum_name: str
    phone: str | None


def parse_narm_pdf(pdf_path: Path) -> list[NarmEntry]:
    entries: list[NarmEntry] = []
    seen: set[tuple[str, str, str]] = set()

    last_state_by_col: dict[int, str | None] = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            starts = detect_column_starts(page)
            bboxes = column_bboxes(page, starts)

            for col_index, bbox in enumerate(bboxes):
                text = page.crop(bbox).extract_text() or ""

                # Carry state across pages/columns when a page begins mid-state.
                current_state = last_state_by_col.get(col_index)

                headings = _heading_occurrences(text)
                heading_idx = 0

                for m in ENTRY_RE.finditer(text):
                    # Advance state heading based on position within the text
                    while heading_idx < len(headings) and headings[heading_idx][0] <= m.start():
                        current_state = headings[heading_idx][1]
                        heading_idx += 1

                    if current_state is None:
                        continue

                    city = normalize_space(m.group("city"))
                    museum_name = clean_museum_name(m.group("museum"))
                    phone = normalize_space(m.group("phone")) if m.group("phone") else None

                    state_province = current_state

                    # Canada entries often embed province code before the city (e.g. "AB Calgary, ...").
                    if state_province == "Canada":
                        parts = city.split(" ", 1)
                        if len(parts) == 2 and parts[0].upper() in CANADA_PROVINCE_CODE_TO_NAME:
                            state_province = CANADA_PROVINCE_CODE_TO_NAME[parts[0].upper()]
                            city = parts[1].strip()

                    key = (state_province, city, museum_name)
                    if key in seen:
                        continue
                    seen.add(key)

                    entries.append(
                        NarmEntry(
                            state_province=state_province,
                            city=city,
                            museum_name=museum_name,
                            phone=phone,
                        )
                    )

                # Persist the last known state for this column into the next page.
                if headings:
                    current_state = headings[-1][1]
                last_state_by_col[col_index] = current_state

    return entries


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def get_schema_museum_fields(schema: dict[str, Any]) -> list[str]:
    props = schema.get("$defs", {}).get("museum", {}).get("properties", {})
    if not isinstance(props, dict):
        raise SystemExit("Invalid schema: expected $defs.museum.properties")
    return list(props.keys())


def build_index(museums: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Index by (state_province, city, normalized name) and alternate names."""

    idx: dict[tuple[str, str, str], dict[str, Any]] = {}

    for m in museums:
        state = normalize_space(str(m.get("state_province") or ""))
        city = normalize_space(str(m.get("city") or ""))
        name = normalize_space(str(m.get("museum_name") or ""))
        if not state or not city or not name:
            continue

        key = (state.casefold(), city.casefold(), normalize_name_for_match(name))
        idx[key] = m

        for alt in m.get("alternate_names") or []:
            if not isinstance(alt, str):
                continue
            alt_key = (state.casefold(), city.casefold(), normalize_name_for_match(alt))
            idx.setdefault(alt_key, m)

    return idx


def to_csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def main() -> None:
    if not PDF_PATH.exists():
        raise SystemExit(f"PDF not found: {PDF_PATH}")
    if not SCHEMA_PATH.exists():
        raise SystemExit(f"Schema not found: {SCHEMA_PATH}")
    if not INDEX_PATH.exists():
        raise SystemExit(f"Index not found: {INDEX_PATH}")

    schema = load_json(SCHEMA_PATH)
    schema_fields = get_schema_museum_fields(schema)

    index = load_json(INDEX_PATH)
    all_museums = index.get("museums", [])
    if not isinstance(all_museums, list):
        raise SystemExit("Invalid all-museums.json: expected 'museums' array")

    museum_idx = build_index(all_museums)

    narm_entries = parse_narm_pdf(PDF_PATH)

    # CSV column order: source + NARM-specific fields + schema fields
    columns = ["source", "narm_phone"] + sorted(schema_fields)

    rows: list[dict[str, str]] = []
    matched = 0

    for e in narm_entries:
        key = (e.state_province.casefold(), e.city.casefold(), normalize_name_for_match(e.museum_name))
        record = museum_idx.get(key)

        row: dict[str, str] = {c: "" for c in columns}
        row["source"] = SOURCE_VALUE
        row["narm_phone"] = e.phone or ""

        if record is not None:
            matched += 1
            for field in schema_fields:
                row[field] = to_csv_cell(record.get(field))
        else:
            # Minimum useful population from NARM
            row["state_province"] = e.state_province
            row["city"] = e.city
            row["museum_name"] = e.museum_name

        rows.append(row)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Stable sort for diff-friendly output
    rows.sort(key=lambda r: (
        r.get("state_province", "").casefold(),
        r.get("city", "").casefold(),
        r.get("museum_name", "").casefold(),
    ))

    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Parsed {len(narm_entries)} NARM entries")
    print(f"[OK] Matched {matched} entries to existing metadata")
    print(f"[OK] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
