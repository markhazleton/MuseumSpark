#!/usr/bin/env python3
"""Enrich museum records using free/open structured data sources (Pre-MRD Phase).

This script runs as part of the Pre-MRD Phase to populate as many MRD-required fields
as possible from open data sources, before any LLM-based enrichment.

MRD Fields Populated:
- city_tier (1-3): Computed from city population (US Census API) + manual override list
- reputation (0-3): Heuristic classification from Wikidata claims (founder, collections)
- collection_tier (0-3): Estimated from facility size, collection count in Wikidata
- time_needed: Inferred from collection size and facility type
- nearby_museum_count: Computed by counting other museums in same city
- museum_type: Enhanced from Wikidata instance_of claims

Primary sources (no API keys required):
- Wikidata (entity search + claims)
- OpenStreetMap Nominatim (geocoding)
- Wikipedia (population, city data)

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
  python scripts/enrich-open-data.py --state IL --compute-mrd-fields --rebuild-index

Notes:
- Be mindful of rate limits and usage policies, especially for Nominatim.
- Official website scraping is optional and conservative (enable with --scrape-website).
- Use --compute-mrd-fields to populate city_tier, reputation, collection_tier from open data.
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

# MRD city_tier classification (Tier 1: Major hubs)
TIER_1_CITIES = {
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Washington", "Boston", "Detroit", "Nashville",
    "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee",
    "Albuquerque", "Tucson", "Fresno", "Sacramento", "Kansas City", "Atlanta",
    "Miami", "Minneapolis", "Cleveland", "New Orleans", "Oakland", "Tampa",
    "Honolulu", "Omaha", "Wichita", "Arlington",
    # Additional cultural hubs regardless of size
    "Santa Fe", "Williamsburg", "Cambridge", "Berkeley", "Ann Arbor",
}

# Time needed heuristics based on museum type
TIME_NEEDED_KEYWORDS = {
    "Quick stop (1-2 hours)": ["historic house", "historic site", "small gallery", "local history"],
    "Half day (2-4 hours)": ["art museum", "history museum", "science museum", "children's museum"],
    "Full day (4+ hours)": ["encyclopedic", "major art museum", "natural history", "large complex"],
}


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


def cached_get_html(url: str, *, ttl_seconds: int = 60 * 60 * 24 * 14, min_delay_seconds: float = 1.0) -> tuple[str, str | None]:
    """Fetch HTML with cache + polite delay (delay only on cache misses).
    
    Returns:
        tuple[str, str | None]: (html_content, error_message)
        If successful, error_message is None. If failed, html_content is empty string.
    """
    HTTP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_path = HTTP_CACHE_DIR / f"{key}.html"

    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age <= ttl_seconds:
            return cache_path.read_text(encoding="utf-8", errors="ignore"), None

    time.sleep(max(0.0, float(min_delay_seconds)))
    
    try:
        raw, headers = http_get_bytes(url)
        content_type = (headers.get("content-type") or "").casefold()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            # Still cache it (for debugging), but skip parsing as HTML.
            cache_path.write_bytes(raw)
            return "", None

        cache_path.write_bytes(raw)
        return raw.decode("utf-8", errors="ignore"), None
    except Exception as e:
        # Return error message for caller to log
        error_msg = str(e)
        if "getaddrinfo failed" in error_msg or "11001" in error_msg:
            return "", f"DNS lookup failed for {url}"
        elif "timed out" in error_msg.lower():
            return "", f"Timeout accessing {url}"
        elif "403" in error_msg or "Forbidden" in error_msg:
            return "", f"Access forbidden (403) for {url}"
        elif "404" in error_msg:
            return "", f"Page not found (404) at {url}"
        else:
            return "", f"Network error accessing {url}: {error_msg[:100]}"


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


def compute_city_tier(city: str, state: str | None = None) -> int:
    """Compute MRD city_tier (1=Major hub, 2=Medium city, 3=Small town).
    
    Uses:
    1. TIER_1_CITIES manual list (major cultural hubs)
    2. Wikipedia population lookup (Tier 2 if 50k-500k, Tier 3 if <50k)
    3. Default to Tier 3 for small towns
    """
    city_normalized = (city or "").strip()
    
    # Check Tier 1 list
    if city_normalized in TIER_1_CITIES:
        return 1
    
    # Try to fetch population from Wikipedia infobox
    try:
        # Search Wikipedia for city page
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{city} {state or ''} city population",
            "format": "json",
            "srlimit": 1,
        }
        search_data = cached_get_json(search_url, params=search_params, ttl_seconds=60*60*24*30)
        
        if search_data.get("query", {}).get("search"):
            page_title = search_data["query"]["search"][0]["title"]
            
            # Get page content
            page_url = "https://en.wikipedia.org/w/api.php"
            page_params = {
                "action": "query",
                "titles": page_title,
                "prop": "revisions",
                "rvprop": "content",
                "format": "json",
                "rvslots": "main",
            }
            page_data = cached_get_json(page_url, params=page_params, ttl_seconds=60*60*24*30)
            
            # Try to extract population from infobox
            pages = page_data.get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                if page_id == "-1":
                    continue
                revisions = page.get("revisions", [])
                if revisions:
                    content = revisions[0].get("slots", {}).get("main", {}).get("*", "")
                    
                    # Simple regex to find population in infobox
                    import re
                    pop_match = re.search(r"population[_\s]*total\s*=\s*([0-9,]+)", content, re.IGNORECASE)
                    if pop_match:
                        pop_str = pop_match.group(1).replace(",", "")
                        try:
                            population = int(pop_str)
                            if population >= 50_000:
                                return 2  # Tier 2: Medium city
                            else:
                                return 3  # Tier 3: Small town
                        except ValueError:
                            pass
    except Exception:
        # If Wikipedia lookup fails, default to Tier 3
        pass
    
    # Default to Tier 3 (small town)
    return 3


def infer_reputation_from_wikidata(entity: dict[str, Any]) -> int | None:
    """Infer MRD reputation (0=International, 1=National, 2=Regional, 3=Local) from Wikidata.
    
    Heuristics:
    - Has significant sitelinks (50+) → International (0)
    - Has multiple language versions (10+) → National (1)
    - Has 3-10 language versions → Regional (2)
    - Has <3 language versions → Local (3)
    """
    sitelinks = entity.get("sitelinks", {})
    num_sitelinks = len(sitelinks)
    
    if num_sitelinks >= 50:
        return 0  # International
    elif num_sitelinks >= 10:
        return 1  # National
    elif num_sitelinks >= 3:
        return 2  # Regional
    elif num_sitelinks > 0:
        return 3  # Local
    
    return None  # Cannot determine


def infer_collection_tier_from_wikidata(entity: dict[str, Any]) -> int | None:
    """Infer MRD collection_tier (0=Flagship, 1=Strong, 2=Moderate, 3=Small) from Wikidata.
    
    Heuristics:
    - Has "collection size" claim (P3172) → Use thresholds
    - No data → Cannot determine
    
    Thresholds:
    - 100k+ items → Flagship (0)
    - 10k-100k items → Strong (1)
    - 1k-10k items → Moderate (2)
    - <1k items → Small (3)
    """
    # P3172: collection size
    collection_size = _first_claim_value(entity, "P3172")
    if isinstance(collection_size, (int, float)):
        size = int(collection_size)
        if size >= 100_000:
            return 0  # Flagship
        elif size >= 10_000:
            return 1  # Strong
        elif size >= 1_000:
            return 2  # Moderate
        else:
            return 3  # Small
    
    return None  # Cannot determine


def infer_time_needed_from_type(museum_type: str | None) -> str | None:
    """Infer time_needed from museum_type using keyword matching.
    
    Returns: "Quick stop (1-2 hours)" | "Half day (2-4 hours)" | "Full day (4+ hours)" | None
    """
    if not museum_type:
        return None
    
    museum_type_lower = museum_type.lower()
    
    for time_category, keywords in TIME_NEEDED_KEYWORDS.items():
        if any(kw in museum_type_lower for kw in keywords):
            return time_category
    
    # Default for generic "museum"
    return "Half day (2-4 hours)"


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


def patch_from_wikidata(museum: dict[str, Any], *, compute_mrd_fields: bool = False) -> PatchResult:
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
    
    # MRD-specific fields (only if compute_mrd_fields=True)
    if compute_mrd_fields:
        # Reputation (0-3) from sitelink count
        if museum.get("reputation") is None:
            reputation = infer_reputation_from_wikidata(entity)
            if reputation is not None:
                patch["reputation"] = reputation
                notes.append(f"Wikidata: inferred reputation={reputation} from sitelinks")
        
        # Collection tier (0-3) from collection size
        if museum.get("collection_tier") is None:
            collection_tier = infer_collection_tier_from_wikidata(entity)
            if collection_tier is not None:
                patch["collection_tier"] = collection_tier
                notes.append(f"Wikidata: inferred collection_tier={collection_tier} from collection size")

    if patch:
        return PatchResult(patch=patch, sources_used=["wikidata"], notes=notes)

    return PatchResult(patch={}, sources_used=["wikidata"], notes=notes + ["Wikidata: no applicable fields to fill"]) 


def extract_city_from_open_data(museum: dict[str, Any], *, min_delay_seconds: float = 1.0) -> str | None:
    """Try to extract city from multiple open data sources when city is Unknown.
    
    Attempts:
    1. Wikidata P131 claim (located in administrative territorial entity)
    2. Nominatim reverse geocoding (if lat/lon available)
    3. Nominatim forward geocoding from address
    4. Parse from museum_id slug
    """
    current_city = (museum.get("city") or "").strip()
    if current_city and current_city.lower() != "unknown":
        return None  # City already known
    
    # Strategy 1: Try Wikidata P131 (located in administrative entity)
    name = museum.get("museum_name") or ""
    state = museum.get("state_province") or ""
    if name:
        try:
            results = wikidata_search(name=name, city=None)
            if results:
                qid = results[0].get("id")
                if qid:
                    entity = wikidata_entity(qid)
                    # P131: located in the administrative territorial entity
                    location_claim = _first_claim_value(entity, "P131")
                    if isinstance(location_claim, dict):
                        city_qid = location_claim.get("id")
                        if city_qid:
                            # Get the city name from the entity
                            city_entity = wikidata_entity(city_qid)
                            city_label = city_entity.get("labels", {}).get("en", {}).get("value")
                            if city_label:
                                return city_label
        except Exception:
            pass
    
    # Strategy 2: Reverse geocoding if we have coordinates
    lat = museum.get("latitude")
    lon = museum.get("longitude")
    if lat is not None and lon is not None:
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {"format": "jsonv2", "lat": lat, "lon": lon, "addressdetails": 1}
            
            key = cache_key(url, params)
            cache_path = CACHE_DIR / f"{key}.json"
            if not cache_path.exists():
                time.sleep(min_delay_seconds)
            
            data = cached_get_json(url, params=params)
            addr = data.get("address", {})
            city = addr.get("city") or addr.get("town") or addr.get("village")
            if city:
                return city
        except Exception:
            pass
    
    # Strategy 3: Forward geocoding with just address + state
    street = museum.get("street_address") or ""
    if street and street.lower() != "tbd":
        try:
            q = ", ".join([p for p in [street, state] if p])
            url = "https://nominatim.openstreetmap.org/search"
            params = {"format": "jsonv2", "q": q, "limit": 1, "addressdetails": 1}
            
            key = cache_key(url, params)
            cache_path = CACHE_DIR / f"{key}.json"
            if not cache_path.exists():
                time.sleep(min_delay_seconds)
            
            data = cached_get_json(url, params=params)
            if isinstance(data, list) and data:
                addr = data[0].get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village")
                if city:
                    return city
        except Exception:
            pass
    
    # Strategy 4: Parse from museum_id slug (e.g., usa-ar-bentonville-crystal-bridges)
    museum_id = museum.get("museum_id") or ""
    parts = museum_id.split("-")
    if len(parts) >= 3:
        # Format: country-state-city-museum-name
        potential_city = parts[2]
        # Capitalize and return if it looks reasonable
        if potential_city and potential_city != "unknown" and len(potential_city) > 2:
            return potential_city.replace("-", " ").title()
    
    return None


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

    try:
        data = cached_get_json(url, params=params)
    except Exception as e:
        error_msg = f"Nominatim: network error - {str(e)[:100]}"
        return PatchResult(patch={}, sources_used=[], notes=[error_msg])
    
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
    
    # Try to extract city from Nominatim response
    if should_fill(museum.get("city")):
        city_name = addr.get("city") or addr.get("town") or addr.get("village")
        if city_name:
            patch["city"] = city_name.strip()
            notes.append(f"Nominatim: extracted city '{city_name}'")

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
    return any(
        phrase in text.lower()
        for phrase in ["reservation required", "tickets required", "advance booking", "must book", "pre-book"]
    )


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
    errors: list[str] = []

    html, error = cached_get_html(website, min_delay_seconds=min_delay_seconds)
    if error:
        notes.append(f"Official site: {error}")
        errors.append(error)
        # Add error to row_notes_internal
        patch["row_notes_internal"] = f"Website scraping errors: {error}"
        return PatchResult(patch=patch, sources_used=sources_used, notes=notes)
    
    if not html:
        return PatchResult(patch={}, sources_used=sources_used, notes=["Official site: non-HTML or empty response"]) 

    try:
        soup = BeautifulSoup(html, "html.parser")
        notes.append("Official site: fetched homepage")
    except Exception as e:
        error_msg = f"Failed to parse HTML: {str(e)[:100]}"
        notes.append(f"Official site: {error_msg}")
        errors.append(error_msg)
        patch["row_notes_internal"] = f"Website scraping errors: {error_msg}"
        return PatchResult(patch=patch, sources_used=sources_used, notes=notes)

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
                    notes.append(f"Official site: extracted city '{locality}' from JSON-LD")
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
    
    # Fallback: Try to extract address and city from visible text
    page_text = soup.get_text(" ", strip=True)
    import re
    
    # Extract state abbreviation from museum_id (e.g., "usa-ks-..." -> "KS")
    state_code = None
    museum_id = museum.get("museum_id", "")
    if isinstance(museum_id, str):
        parts = museum_id.split("-")
        if len(parts) >= 2 and parts[0] == "usa":
            state_code = parts[1].upper()
    
    # Try to extract full address first (e.g., "701 Beach Lane, Manhattan, KS 66506" or "242 S Santa Fe Ave<br>Salina, KS 67401")
    if should_fill(museum.get("street_address")) and state_code:
        # Pattern variations for different address formats
        # Capture full street names including type suffixes (Ave, St, Lane, etc.)
        # Allow for <br> tags or commas between street and city
        address_patterns = [
            # With street type suffix: "Number Street Type<br>City, ST ZIP" or "Number Street Type, City, ST ZIP"
            rf"(\d+\s+[NSEWnse]?\.?\s*[\w\s\.\-]+?(?:Avenue|Ave|Street|St|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Circle|Cir)\.?)\s*(?:,|<br>|<br/>)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*{state_code}\s+(\d{{5}})",
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                street = match.group(1).strip().rstrip(',')
                city = match.group(2).strip()
                zipcode = match.group(3).strip()
                
                # Validate street address (should have number and reasonable length)
                if len(street) > 3 and len(street) < 100 and any(c.isdigit() for c in street):
                    patch["street_address"] = street
                    patch["city"] = city
                    patch["postal_code"] = zipcode
                    patch.setdefault("address_source", "official_website")
                    patch.setdefault("address_last_verified", today_yyyy_mm_dd())
                    notes.append(f"Official site: extracted full address from page text")
                    break
    
    # If no full address found, try to extract just city
    if should_fill(museum.get("city")) and should_fill(patch.get("city")) and state_code:
        # Try to find patterns like "Bentonville, AR 72712" or "Fort Smith, Arkansas"
        patterns = [
            rf"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*{state_code}\s+\d{{5}}",  # "City, AR 12345"
            rf"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*{state_code}",  # "City, AR"
            rf"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*{re.escape(state_code)}",  # Escaped version
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_text)
            if match:
                city_candidate = match.group(1).strip()
                # Basic validation: city name should be 2+ chars and not common false positives
                if len(city_candidate) >= 2 and city_candidate.lower() not in ["the", "and", "for"]:
                    patch["city"] = city_candidate
                    notes.append(f"Official site: extracted city '{city_candidate}' from page text")
                    break

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
            page_html, page_error = cached_get_html(page_url, min_delay_seconds=min_delay_seconds)
            if page_error:
                notes.append(f"Official site: {page_error}")
                errors.append(page_error)
                continue
            if not page_html:
                continue
                continue
            page_text = BeautifulSoup(page_html, "html.parser").get_text(" ", strip=True)
            page_text = BeautifulSoup(page_html, "html.parser").get_text(" ", strip=True)
            if _text_mentions_reservation_required(page_text):
                patch["reservation_required"] = True
                notes.append("Official site: reservation_required inferred from visit/ticket page")
                break
    
    # Add error summary to patch if any errors occurred
    if errors:
        error_summary = "; ".join(errors[:3])  # Limit to first 3 errors
        if not patch.get("row_notes_internal"):
            patch["row_notes_internal"] = f"Website scraping errors: {error_summary}"

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
    compute_mrd_fields: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []

    # Wikidata enrichment (with optional MRD fields)
    wd = patch_from_wikidata(museum, compute_mrd_fields=compute_mrd_fields)
    museum2 = merge_patch(museum, wd.patch)
    if wd.sources_used:
        museum2 = ensure_data_sources(museum2, wd.sources_used)
    notes.extend(wd.notes)

    osm = patch_from_nominatim(museum2)
    museum3 = merge_patch(museum2, osm.patch)
    if osm.sources_used:
        museum3 = ensure_data_sources(museum3, osm.sources_used)
    notes.extend(osm.notes)

    # Try to extract city if Unknown (before MRD field computation)
    if should_fill(museum3.get("city")):
        extracted_city = extract_city_from_open_data(museum3)
        if extracted_city:
            museum3["city"] = extracted_city
            notes.append(f"City extraction: found '{extracted_city}' from open data")
    
    # MRD-specific computed fields
    if compute_mrd_fields:
        # city_tier (1-3)
        if museum3.get("city_tier") is None:
            city = museum3.get("city") or ""
            state = museum3.get("state_province") or ""
            city_tier = compute_city_tier(city, state)
            museum3["city_tier"] = city_tier
            notes.append(f"MRD: computed city_tier={city_tier} for {city}")
        
        # time_needed inference from museum_type
        if should_fill(museum3.get("time_needed")):
            museum_type = museum3.get("museum_type")
            time_needed = infer_time_needed_from_type(museum_type)
            if time_needed:
                museum3["time_needed"] = time_needed
                notes.append(f"MRD: inferred time_needed='{time_needed}' from museum_type")

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


def validate_consistency_with_index(state_code: str, museums: list[dict[str, Any]]) -> list[str]:
    """
    Validate consistency between state file museums and the all-museums.json index.
    Returns a list of validation error messages.
    """
    errors = []
    
    # Load all-museums index if it exists
    index_path = PROJECT_ROOT / "data" / "index" / "all-museums.json"
    if not index_path.exists():
        errors.append(f"all-museums.json not found at {index_path} - run with --rebuild-index to create")
        return errors
    
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)
    except Exception as e:
        errors.append(f"Failed to load all-museums.json: {e}")
        return errors
    
    # Build a lookup of museums by museum_id from the index
    index_museums = {m.get("museum_id"): m for m in index_data.get("museums", [])}
    
    # Check for museums in state file
    state_museum_ids = {m.get("museum_id") for m in museums if m.get("museum_id")}
    
    # Validate each museum
    for museum in museums:
        museum_id = museum.get("museum_id")
        if not museum_id:
            errors.append(f"Museum missing museum_id: {museum.get('museum_name', 'Unknown')}")
            continue
        
        # Check if museum exists in index
        index_museum = index_museums.get(museum_id)
        if not index_museum:
            errors.append(f"Museum {museum_id} in state file but missing from all-museums.json")
            continue
        
        # Validate critical fields match
        critical_fields = ["museum_name", "state_province", "city", "country"]
        for field in critical_fields:
            state_value = museum.get(field)
            index_value = index_museum.get(field)
            if state_value != index_value:
                errors.append(
                    f"Mismatch in {museum_id}.{field}: "
                    f"state='{state_value}' vs index='{index_value}'"
                )
    
    # Check for museums in index that should be in this state file
    for museum_id, index_museum in index_museums.items():
        if index_museum.get("country") == "USA":
            # Extract state code from museum_id (e.g., "usa-ks-..." -> "KS")
            id_parts = museum_id.split("-")
            if len(id_parts) >= 2 and id_parts[0] == "usa":
                museum_state_code = id_parts[1].upper()
                if museum_state_code == state_code.upper() and museum_id not in state_museum_ids:
                    errors.append(
                        f"Museum {museum_id} ({index_museum.get('museum_name')}) "
                        f"in all-museums.json but missing from {state_code}.json"
                    )
    
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich museums using open data sources (Pre-MRD Phase)")
    parser.add_argument("--state", help="Two-letter state code (e.g., CA)")
    parser.add_argument("--museum-id", help="Specific museum_id to enrich")
    parser.add_argument("--only-placeholders", action="store_true", help="Only enrich placeholder/stub records")
    parser.add_argument("--limit", type=int, default=0, help="Max museums to process (0 = no limit)")
    parser.add_argument(
        "--compute-mrd-fields",
        action="store_true",
        help="Compute MRD fields: city_tier, reputation, collection_tier, time_needed from open data",
    )
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
            compute_mrd_fields=bool(args.compute_mrd_fields),
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
            
            # Preserve existing row_notes_internal and append new notes
            existing_notes = enriched.get("row_notes_internal") or ""
            new_notes = "; ".join(notes[:6])
            
            if existing_notes and "enrichment" in existing_notes.lower():
                # Already has enrichment notes, append new ones
                enriched["row_notes_internal"] = f"{existing_notes}; {new_notes}"
            elif not existing_notes:
                # No existing notes
                enriched["row_notes_internal"] = new_notes
            # else: keep existing notes (like "Seeded from walker-reciprocal")
            if enriched.get("row_notes_internal") is None:
                enriched["row_notes_internal"] = "; ".join(notes[:6])

        out_museums.append(enriched)

    print(f"[OK] State: {state_code}")
    print(f"[OK] Processed: {processed}")
    print(f"[OK] Changed: {changed}")

    if not args.dry_run:
        # Validate consistency before writing
        if changed > 0:
            print("[INFO] Validating consistency with all-museums index...")
            validation_errors = validate_consistency_with_index(state_code, out_museums)
            if validation_errors:
                print(f"[WARN] Found {len(validation_errors)} consistency issue(s) with all-museums.json:")
                for error in validation_errors[:5]:  # Show first 5 warnings
                    print(f"  - {error}")
                if len(validation_errors) > 5:
                    print(f"  ... and {len(validation_errors) - 5} more warnings")
                print("[INFO] Proceeding with write. Run with --rebuild-index to synchronize.")
            else:
                print("[OK] Consistency validated - state file matches all-museums.json")
        
        state_data["museums"] = out_museums
        if changed > 0:
            state_data["last_updated"] = now_utc_iso_z()
        save_json(state_path, state_data)
        print(f"[OK] Wrote: {state_path}")

        if args.rebuild_index:
            print("[INFO] Rebuilding master index (all-museums.json)…")
            cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "build-index.py")]
            if args.compute_mrd_fields:
                cmd.extend(["--calculate-scores", "--update-nearby-counts"])
            subprocess.run(cmd, check=True)

            if args.rebuild_reports:
                print("[INFO] Rebuilding progress.json…")
                subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "build-progress.py")], check=True)
                print("[INFO] Rebuilding missing-report.json…")
                subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "build-missing-report.py")], check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
