#!/usr/bin/env python3
"""Enrich museum records using free/open structured data sources.

This script intentionally runs *before* any LLM-based enrichment.

Primary sources (no API keys required):
- Wikidata (entity search + claims)
- OpenStreetMap Nominatim (geocoding)

Optional sources (still free, but involves fetching the museum's own website):
- Official museum website (light scraping for structured fields/links)

Design goals:
- Conservative: only fills missing/placeholder fields (e.g., null/"TBD")
- Idempotent: re-running shouldn't thrash curated data
- Traceable: writes provenance into `data_sources` and notes internal decisions
- Cache-friendly: stores HTTP responses in `data/cache/` to reduce repeated calls

Usage examples:
  python scripts/enrich-open-data.py --state CA --only-placeholders --limit 25
  python scripts/enrich-open-data.py --museum-id usa-ak-anchorage-anchorage-museum

Notes:
- Be mindful of rate limits and usage policies, especially for Nominatim.
- Official website scraping is optional and conservative (enable with --scrape-website).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "open-data"
HTTP_CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "http"

USER_AGENT = "MuseumSpark/0.1 (https://github.com/MarkHazleton/MuseumSpark)"

# Values treated as placeholders for "fill-if-missing" logic
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


def should_fill(existing: Any) -> bool:
    if existing is None:
        return True
    if isinstance(existing, str):
        return existing.strip().casefold() in _PLACEHOLDER_STRINGS
    return False


def cache_key(url: str, params: Optional[dict[str, Any]] = None) -> str:
    blob = {"url": url, "params": params or {}}
    raw = json.dumps(blob, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def http_get_json(url: str, *, params: Optional[dict[str, Any]] = None, timeout_seconds: int = 30) -> Any:
    if params:
        query = urlencode({k: v for k, v in params.items() if v is not None})
        full_url = f"{url}?{query}"
    else:
        full_url = url

    req = Request(full_url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read()
        return json.loads(raw.decode("utf-8"))
    except HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} for {full_url}") from e
    except URLError as e:
        raise RuntimeError(f"Network error for {full_url}: {e}") from e


def http_get_bytes(url: str, *, timeout_seconds: int = 30) -> tuple[bytes, dict[str, str]]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read()
            headers = {k.lower(): v for k, v in (resp.headers.items() if resp.headers else [])}
        return raw, headers
    except HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} for {url}") from e
    except URLError as e:
        raise RuntimeError(f"Network error for {url}: {e}") from e


def cached_get_html(url: str, *, ttl_seconds: int = 60 * 60 * 24 * 14, min_delay_seconds: float = 1.0) -> str:
    """Fetch HTML with cache + polite delay (delay only on cache misses)."""
    HTTP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_path = HTTP_CACHE_DIR / f"{key}.html"

    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age <= ttl_seconds:
            return cache_path.read_text(encoding="utf-8", errors="ignore")

    time.sleep(max(0.0, float(min_delay_seconds)))
    raw, headers = http_get_bytes(url)
    content_type = (headers.get("content-type") or "").casefold()
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        # Still cache it (for debugging), but skip parsing as HTML.
        cache_path.write_bytes(raw)
        return ""

    cache_path.write_bytes(raw)
    return raw.decode("utf-8", errors="ignore")


def can_fetch_url(url: str) -> bool:
    """Best-effort robots.txt check.

    If robots.txt cannot be fetched, we allow (but still run conservatively).
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True


def cached_get_json(url: str, *, params: Optional[dict[str, Any]] = None, ttl_seconds: int = 60 * 60 * 24 * 14) -> Any:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = cache_key(url, params)
    cache_path = CACHE_DIR / f"{key}.json"

    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age <= ttl_seconds:
            return load_json(cache_path)

    data = http_get_json(url, params=params)
    save_json(cache_path, data)
    return data


def normalize_website(url: str) -> str:
    url = (url or "").strip()
    while url.endswith("/"):
        url = url[:-1]
    return url


def today_yyyy_mm_dd() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def now_utc_iso_z() -> str:
    # Match existing state file format: 2026-01-15T17:22:19Z
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class PatchResult:
    patch: dict[str, Any]
    sources_used: list[str]
    notes: list[str]


def wikidata_search(name: str, city: str | None = None) -> list[dict[str, Any]]:
    # Using Wikidata wbsearchentities API
    query = name if not city else f"{name} {city}"
    data = cached_get_json(
        "https://www.wikidata.org/w/api.php",
        params={
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "format": "json",
            "limit": 5,
        },
    )
    return data.get("search", [])


def wikidata_entity(qid: str) -> dict[str, Any]:
    data = cached_get_json(
        "https://www.wikidata.org/w/api.php",
        params={
            "action": "wbgetentities",
            "ids": qid,
            "format": "json",
            "props": "claims|labels|descriptions|sitelinks",
            "languages": "en",
        },
    )
    entities = data.get("entities", {})
    return entities.get(qid, {})


def _first_claim_value(entity: dict[str, Any], prop: str) -> Any:
    claims = entity.get("claims", {})
    entries = claims.get(prop) or []
    for entry in entries:
        mainsnak = entry.get("mainsnak") or {}
        datavalue = mainsnak.get("datavalue") or {}
        value = datavalue.get("value")
        if value is not None:
            return value
    return None


def patch_from_wikidata(museum: dict[str, Any]) -> PatchResult:
    name = museum.get("museum_name") or ""
    city = museum.get("city") or ""

    results = wikidata_search(name=name, city=city)
    if not results:
        return PatchResult(patch={}, sources_used=[], notes=["Wikidata: no search results"]) 

    qid = results[0].get("id")
    if not qid:
        return PatchResult(patch={}, sources_used=[], notes=["Wikidata: search returned no QID"]) 

    entity = wikidata_entity(qid)
    if not entity:
        return PatchResult(patch={}, sources_used=[], notes=[f"Wikidata: entity not found for {qid}"]) 

    patch: dict[str, Any] = {}
    notes: list[str] = [f"Wikidata: matched {qid}"]

    # Website (P856)
    wd_site = _first_claim_value(entity, "P856")
    if isinstance(wd_site, str) and should_fill(museum.get("website")):
        patch["website"] = normalize_website(wd_site)

    # Coordinates (P625)
    coord = _first_claim_value(entity, "P625")
    if isinstance(coord, dict):
        lat = coord.get("latitude")
        lon = coord.get("longitude")
        if lat is not None and museum.get("latitude") is None:
            patch["latitude"] = float(lat)
        if lon is not None and museum.get("longitude") is None:
            patch["longitude"] = float(lon)

    # Street address: P969 ("located at street address")
    street = _first_claim_value(entity, "P969")
    if isinstance(street, str) and should_fill(museum.get("street_address")):
        patch["street_address"] = street.strip()

    # Postal code: P281
    postal = _first_claim_value(entity, "P281")
    if isinstance(postal, str) and should_fill(museum.get("postal_code")):
        patch["postal_code"] = postal.strip()

    if patch:
        return PatchResult(patch=patch, sources_used=["wikidata"], notes=notes)

    return PatchResult(patch={}, sources_used=["wikidata"], notes=notes + ["Wikidata: no applicable fields to fill"]) 


def patch_from_nominatim(museum: dict[str, Any], *, min_delay_seconds: float = 1.0) -> PatchResult:
    # Nominatim usage policies require a clear User-Agent and reasonable rate.
    # We keep this conservative and cache responses.
    name = museum.get("museum_name") or ""
    city = museum.get("city") or ""
    state = museum.get("state_province") or ""
    country = museum.get("country") or ""

    if not name:
        return PatchResult(patch={}, sources_used=[], notes=["Nominatim: missing museum_name"]) 

    q = ", ".join([p for p in [name, city, state, country] if p])

    # Delay between calls (only applies to cache misses)
    url = "https://nominatim.openstreetmap.org/search"
    params = {"format": "jsonv2", "q": q, "limit": 1, "addressdetails": 1}

    key = cache_key(url, params)
    cache_path = CACHE_DIR / f"{key}.json"
    if not cache_path.exists():
        time.sleep(min_delay_seconds)

    data = cached_get_json(url, params=params)
    if not isinstance(data, list) or not data:
        return PatchResult(patch={}, sources_used=[], notes=["Nominatim: no results"]) 

    hit = data[0]
    patch: dict[str, Any] = {}
    notes: list[str] = ["Nominatim: matched 1 result"]

    if museum.get("latitude") is None and hit.get("lat") is not None:
        patch["latitude"] = float(hit["lat"])
    if museum.get("longitude") is None and hit.get("lon") is not None:
        patch["longitude"] = float(hit["lon"])

    # Address heuristics (very conservative)
    addr = hit.get("address") or {}
    if should_fill(museum.get("postal_code")) and isinstance(addr.get("postcode"), str):
        patch["postal_code"] = addr["postcode"].strip()

    if patch:
        return PatchResult(patch=patch, sources_used=["openstreetmap"], notes=notes)

    return PatchResult(patch={}, sources_used=["openstreetmap"], notes=notes + ["Nominatim: no applicable fields to fill"]) 


def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _extract_jsonld_objects(soup: BeautifulSoup) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tag in soup.find_all("script"):
        if (tag.get("type") or "").casefold() != "application/ld+json":
            continue
        raw = (tag.string or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        if isinstance(data, dict):
            out.append(data)
        elif isinstance(data, list):
            out.extend([x for x in data if isinstance(x, dict)])
    return out


def _iter_jsonld_nodes(obj: dict[str, Any]) -> list[dict[str, Any]]:
    # Expand @graph where present
    graph = obj.get("@graph")
    if isinstance(graph, list):
        return [n for n in graph if isinstance(n, dict)]
    return [obj]


def _find_best_link(soup: BeautifulSoup, *, keywords: list[str]) -> Optional[str]:
    best: Optional[str] = None
    for a in soup.find_all("a"):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue

        text = (a.get_text(" ", strip=True) or "").casefold()
        href_l = href.casefold()
        if any(k in text or k in href_l for k in keywords):
            best = href
            break
    return best


_RESERVATION_REQUIRED_PHRASES = [
    "reservation required",
    "advance reservation",
    "timed entry",
    "tickets required",
]


def _text_mentions_reservation_required(text: str) -> bool:
    t = (text or "").casefold()
    return any(p in t for p in _RESERVATION_REQUIRED_PHRASES)


def patch_from_official_website(
    museum: dict[str, Any],
    *,
    max_pages: int = 2,
    min_delay_seconds: float = 1.0,
) -> PatchResult:
    website = normalize_website(str(museum.get("website") or ""))
    if not website or not is_http_url(website):
        return PatchResult(patch={}, sources_used=[], notes=["Official site: missing/invalid website URL"]) 

    if not can_fetch_url(website):
        return PatchResult(patch={}, sources_used=[], notes=["Official site: blocked by robots.txt"]) 

    patch: dict[str, Any] = {}
    notes: list[str] = []
    sources_used: list[str] = ["official_website", website]

    html = cached_get_html(website, min_delay_seconds=min_delay_seconds)
    if not html:
        return PatchResult(patch={}, sources_used=sources_used, notes=["Official site: non-HTML or empty response"]) 

    soup = BeautifulSoup(html, "html.parser")
    notes.append("Official site: fetched homepage")

    # Discover key subpages (hours/tickets/accessibility) from nav/footer links.
    if is_missing(museum.get("open_hours_url")):
        href = _find_best_link(soup, keywords=["hours", "visit", "admission", "plan your visit"]) 
        if href:
            patch["open_hours_url"] = urljoin(website + "/", href)

    if is_missing(museum.get("tickets_url")):
        href = _find_best_link(soup, keywords=["tickets", "admission", "reserve", "reservation", "book"]) 
        if href:
            patch["tickets_url"] = urljoin(website + "/", href)

    if is_missing(museum.get("accessibility_url")):
        href = _find_best_link(soup, keywords=["accessibility", "accessible", "ada", "access"]) 
        if href:
            patch["accessibility_url"] = urljoin(website + "/", href)

    # Try to pull structured address/geo from JSON-LD (schema.org)
    filled_address = False
    for obj in _extract_jsonld_objects(soup):
        for node in _iter_jsonld_nodes(obj):
            address = node.get("address")
            if isinstance(address, dict):
                street = address.get("streetAddress")
                postal = address.get("postalCode")
                locality = address.get("addressLocality")
                region = address.get("addressRegion")

                if isinstance(street, str) and should_fill(museum.get("street_address")):
                    patch["street_address"] = street.strip()
                    filled_address = True
                if isinstance(postal, str) and should_fill(museum.get("postal_code")):
                    patch["postal_code"] = postal.strip()
                    filled_address = True
                if isinstance(locality, str) and should_fill(museum.get("city")):
                    patch["city"] = locality.strip()
                if isinstance(region, str) and should_fill(museum.get("state_province")):
                    patch["state_province"] = region.strip()

            geo = node.get("geo")
            if isinstance(geo, dict):
                lat = geo.get("latitude")
                lon = geo.get("longitude")
                if lat is not None and museum.get("latitude") is None:
                    try:
                        patch["latitude"] = float(lat)
                    except Exception:
                        pass
                if lon is not None and museum.get("longitude") is None:
                    try:
                        patch["longitude"] = float(lon)
                    except Exception:
                        pass

    if filled_address:
        patch.setdefault("address_source", "official_website")
        patch.setdefault("address_last_verified", today_yyyy_mm_dd())
        notes.append("Official site: extracted address from JSON-LD")

    # Best-effort detection of reservation requirement (do not store scraped text)
    if museum.get("reservation_required") is None and max_pages > 0:
        candidate_pages: list[str] = []
        for field in ["tickets_url", "open_hours_url"]:
            u = patch.get(field) or museum.get(field)
            if isinstance(u, str) and is_http_url(u):
                candidate_pages.append(u)

        for page_url in candidate_pages[: max(0, max_pages - 1)]:
            if not can_fetch_url(page_url):
                continue
            page_html = cached_get_html(page_url, min_delay_seconds=min_delay_seconds)
            if not page_html:
                continue
            page_text = BeautifulSoup(page_html, "html.parser").get_text(" ", strip=True)
            if _text_mentions_reservation_required(page_text):
                patch["reservation_required"] = True
                notes.append("Official site: reservation_required inferred from visit/ticket page")
                break

    if patch:
        return PatchResult(patch=patch, sources_used=sources_used, notes=notes)

    return PatchResult(patch={}, sources_used=sources_used, notes=notes + ["Official site: no applicable fields to fill"]) 


def merge_patch(museum: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(museum)
    for k, v in patch.items():
        existing = out.get(k)
        if should_fill(existing) or existing is None:
            out[k] = v
    return out


def ensure_data_sources(museum: dict[str, Any], sources_used: list[str]) -> dict[str, Any]:
    out = dict(museum)
    ds = out.get("data_sources")
    if ds is None:
        ds = []
    if not isinstance(ds, list):
        ds = [str(ds)]

    for s in sources_used:
        if s not in ds:
            ds.append(s)

    out["data_sources"] = ds
    return out


def is_placeholder_record(m: dict[str, Any]) -> bool:
    # A simple heuristic for stubs created by ingest-walker-reciprocal.py
    return (
        (m.get("street_address") or "").strip().casefold() == "tbd"
        or (m.get("postal_code") or "").strip().casefold() == "tbd"
        or (m.get("museum_type") or "").strip().casefold() == "unknown"
    )


def derive_state_code_from_id(museum_id: str) -> Optional[str]:
    # Convention: usa-ca-... -> CA
    parts = (museum_id or "").split("-")
    if len(parts) < 2:
        return None
    candidate = parts[1].upper()
    if len(candidate) == 2 and candidate.isalpha():
        return candidate
    return None


def enrich_one(
    museum: dict[str, Any],
    *,
    scrape_website: bool,
    scrape_max_pages: int,
    scrape_delay_seconds: float,
) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []

    wd = patch_from_wikidata(museum)
    museum2 = merge_patch(museum, wd.patch)
    if wd.sources_used:
        museum2 = ensure_data_sources(museum2, wd.sources_used)
    notes.extend(wd.notes)

    osm = patch_from_nominatim(museum2)
    museum3 = merge_patch(museum2, osm.patch)
    if osm.sources_used:
        museum3 = ensure_data_sources(museum3, osm.sources_used)
    notes.extend(osm.notes)

    if scrape_website:
        off = patch_from_official_website(
            museum3,
            max_pages=scrape_max_pages,
            min_delay_seconds=scrape_delay_seconds,
        )
        museum4 = merge_patch(museum3, off.patch)
        if off.sources_used:
            museum4 = ensure_data_sources(museum4, off.sources_used)
        notes.extend(off.notes)
        return museum4, notes

    return museum3, notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich museums using open data sources")
    parser.add_argument("--state", help="Two-letter state code (e.g., CA)")
    parser.add_argument("--museum-id", help="Specific museum_id to enrich")
    parser.add_argument("--only-placeholders", action="store_true", help="Only enrich placeholder/stub records")
    parser.add_argument("--limit", type=int, default=0, help="Max museums to process (0 = no limit)")
    parser.add_argument(
        "--scrape-website",
        action="store_true",
        help="Also fetch the museum's official website to extract structured fields/links (conservative)",
    )
    parser.add_argument(
        "--scrape-max-pages",
        type=int,
        default=2,
        help="Max pages to fetch per museum when scraping (homepage counts as 1)",
    )
    parser.add_argument(
        "--scrape-delay-seconds",
        type=float,
        default=1.0,
        help="Delay between website fetches on cache misses (politeness)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes")
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="After writing changes, rebuild data/index/all-museums.json using scripts/build-index.py",
    )
    parser.add_argument(
        "--rebuild-reports",
        action="store_true",
        help="After rebuilding the index, also rebuild data/index/progress.json and data/index/missing-report.json",
    )
    args = parser.parse_args()

    if not args.state and not args.museum_id:
        parser.error("Provide --state or --museum-id")

    if args.state:
        state_code = args.state.upper()
    else:
        state_code = derive_state_code_from_id(args.museum_id)
        if not state_code:
            raise SystemExit("Unable to derive state code from museum_id; pass --state")

    state_path = STATES_DIR / f"{state_code}.json"
    if not state_path.exists():
        raise SystemExit(f"Missing state file: {state_path}")

    state_data = load_json(state_path)
    museums = state_data.get("museums") or []
    if not isinstance(museums, list):
        raise SystemExit(f"Invalid state file museums array: {state_path}")

    processed = 0
    changed = 0

    out_museums: list[dict[str, Any]] = []
    for m in museums:
        if args.museum_id and m.get("museum_id") != args.museum_id:
            out_museums.append(m)
            continue

        if args.only_placeholders and not is_placeholder_record(m):
            out_museums.append(m)
            continue

        if args.limit and processed >= args.limit:
            out_museums.append(m)
            continue

        processed += 1
        before = json.dumps(m, sort_keys=True)
        enriched, notes = enrich_one(
            m,
            scrape_website=bool(args.scrape_website),
            scrape_max_pages=int(args.scrape_max_pages),
            scrape_delay_seconds=float(args.scrape_delay_seconds),
        )
        after = json.dumps(enriched, sort_keys=True)
        if before != after:
            changed += 1
            today = today_yyyy_mm_dd()
            if enriched.get("updated_at") is None:
                enriched["updated_at"] = today
            else:
                enriched["updated_at"] = today

            # Record-level last_updated is a date (YYYY-MM-DD) in this dataset.
            enriched["last_updated"] = today
            if enriched.get("row_notes_internal") is None:
                enriched["row_notes_internal"] = "; ".join(notes[:6])

        out_museums.append(enriched)

    print(f"[OK] State: {state_code}")
    print(f"[OK] Processed: {processed}")
    print(f"[OK] Changed: {changed}")

    if not args.dry_run:
        state_data["museums"] = out_museums
        if changed > 0:
            state_data["last_updated"] = now_utc_iso_z()
        save_json(state_path, state_data)
        print(f"[OK] Wrote: {state_path}")

        if args.rebuild_index:
            print("[INFO] Rebuilding master index (all-museums.json)…")
            cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "build-index.py")]
            subprocess.run(cmd, check=True)

            if args.rebuild_reports:
                print("[INFO] Rebuilding progress.json…")
                subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "build-progress.py")], check=True)
                print("[INFO] Rebuilding missing-report.json…")
                subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "build-missing-report.py")], check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
