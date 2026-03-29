#!/usr/bin/env python3
"""Validate data/index/walker-reciprocal.csv.

This is a lightweight integrity check for the Walker Art Reciprocal Program seed roster.
It validates:
- file exists
- required headers are present
- required fields are non-empty
- URLs are http/https
- basic duplicate detection

Usage:
  python scripts/validate-walker-reciprocal-csv.py

Exit codes:
  0 = ok (no errors)
  1 = validation errors found
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "index" / "walker-reciprocal.csv"

REQUIRED_HEADERS = ["STATE", "NAME", "CITY", "URL"]


@dataclass(frozen=True)
class Issue:
    level: str  # "ERROR" | "WARN"
    message: str


def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def main() -> int:
    if not CSV_PATH.exists():
        print(f"[ERROR] Missing file: {CSV_PATH}")
        return 1

    issues: list[Issue] = []

    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        missing = [h for h in REQUIRED_HEADERS if h not in headers]
        if missing:
            issues.append(Issue("ERROR", f"Missing required headers: {missing}. Found: {headers}"))
            # If headers are wrong, row-level validation is unreliable.
            for issue in issues:
                print(f"[{issue.level}] {issue.message}")
            return 1

        row_count = 0
        seen_keys: set[tuple[str, str, str]] = set()

        for row in reader:
            row_count += 1
            state = (row.get("STATE") or "").strip()
            name = (row.get("NAME") or "").strip()
            city = (row.get("CITY") or "").strip()
            url = (row.get("URL") or "").strip()

            if not state:
                issues.append(Issue("ERROR", f"Row {row_count}: STATE is empty"))
            if not name:
                issues.append(Issue("ERROR", f"Row {row_count}: NAME is empty"))
            if not url:
                issues.append(Issue("ERROR", f"Row {row_count}: URL is empty"))
            elif not is_http_url(url):
                issues.append(Issue("ERROR", f"Row {row_count}: URL is not a valid http/https URL: {url}"))

            # Common scrape artifacts
            if url.endswith(")") or url.endswith("]"):
                issues.append(Issue("WARN", f"Row {row_count}: URL ends with a trailing bracket/paren (possible artifact): {url}"))
            if "%20" in url:
                issues.append(Issue("WARN", f"Row {row_count}: URL contains %20 (check for accidental whitespace): {url}"))

            key = (state.casefold(), name.casefold(), city.casefold())
            if key in seen_keys:
                issues.append(Issue("WARN", f"Row {row_count}: duplicate (STATE, NAME, CITY): {state} | {name} | {city}"))
            else:
                seen_keys.add(key)

    error_count = sum(1 for i in issues if i.level == "ERROR")
    warn_count = sum(1 for i in issues if i.level == "WARN")

    for issue in issues:
        print(f"[{issue.level}] {issue.message}")

    print(f"[OK] Checked {row_count} rows")
    print(f"[OK] Errors: {error_count}  Warnings: {warn_count}")

    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
