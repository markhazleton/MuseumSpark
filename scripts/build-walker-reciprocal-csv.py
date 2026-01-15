#!/usr/bin/env python3
"""Build data/index/walker-reciprocal.csv from data/index/walker-reciprocal.html.

The HTML is organized as repeating blocks of:
  <p>STATE</p>
  <ul>
    <li><a href="...">Museum Name, City</a></li>
    ...
  </ul>

This script extracts one CSV row per <a> entry with columns:
  STATE, NAME, CITY, URL

Usage:
  python scripts/build-walker-reciprocal-csv.py
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IN_PATH = PROJECT_ROOT / "data" / "index" / "walker-reciprocal.html"
OUT_PATH = PROJECT_ROOT / "data" / "index" / "walker-reciprocal.csv"


def normalize_space(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


def normalize_region(value: str) -> str:
    value = normalize_space(value)
    if value.casefold() in {"washington, dc", "washington dc", "washington, d.c."}:
        return "District of Columbia"
    return value


_CITY_SPLIT_RE = re.compile(r"\s*,\s*")


def split_name_city(text: str) -> tuple[str, str]:
    """Split link text into (name, city).

    The source uses "Name, City" for many entries, but some entries omit a city.
    If multiple commas exist, we split on the *last* comma.
    """

    text = normalize_space(text)
    if "," not in text:
        return text, ""

    parts = _CITY_SPLIT_RE.split(text)
    if len(parts) < 2:
        return text, ""

    city = parts[-1].strip()
    name = ", ".join(p.strip() for p in parts[:-1]).strip()
    return name, city


def main() -> None:
    if not IN_PATH.exists():
        raise SystemExit(f"Input not found: {IN_PATH}")

    html = IN_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for p in soup.find_all("p"):
        ul = p.find_next_sibling("ul")
        if ul is None or ul.find("a") is None:
            continue

        state = normalize_region(p.get_text(" ", strip=True))
        if not state:
            continue

        for a in ul.find_all("a"):
            url = (a.get("href") or "").strip()
            text = normalize_space(a.get_text(" ", strip=True))
            if not text:
                continue

            name, city = split_name_city(text)

            key = (state, name, city, url)
            if key in seen:
                continue
            seen.add(key)

            rows.append({
                "STATE": state,
                "NAME": name,
                "CITY": city,
                "URL": url,
            })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows.sort(key=lambda r: (
        r["STATE"].casefold(),
        r["CITY"].casefold(),
        r["NAME"].casefold(),
    ))

    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["STATE", "NAME", "CITY", "URL"])
        w.writeheader()
        w.writerows(rows)

    print(f"[OK] Wrote {OUT_PATH}")
    print(f"[OK] Rows {len(rows)}")


if __name__ == "__main__":
    main()
