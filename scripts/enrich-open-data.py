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
import os
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

# Optional imports with graceful degradation
try:
    import pyap
    HAS_PYAP = True
except ImportError:
    HAS_PYAP = False

try:
    import extruct
    HAS_EXTRUCT = True
except ImportError:
    HAS_EXTRUCT = False

try:
    import usaddress
    HAS_USADDRESS = True
except ImportError:
    HAS_USADDRESS = False

try:
    import googlemaps
    HAS_GOOGLE_MAPS = True
except ImportError:
    HAS_GOOGLE_MAPS = False

try:
    from geopy.geocoders import Nominatim
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False

try:
    from yelpapi import YelpAPI
    HAS_YELP = True
except ImportError:
    HAS_YELP = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "open-data"
HTTP_CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "http"

USER_AGENT = "MuseumSpark/0.1 (https://github.com/MarkHazleton/MuseumSpark)"

# Values treated as placeholders for "fill-if-missing" logic
# NOTE: These will be normalized to null in output - we either KNOW a value or it's null
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

# Time needed heuristics based on museum type (mapped to MRD enum)
TIME_NEEDED_KEYWORDS = {
    "Quick stop (<1 hr)": ["historic house", "historic site", "small gallery", "local history", "house museum"],
    "Half day": ["art museum", "history museum", "science museum", "children's museum", "university museum"],
    "Full day": ["encyclopedic", "major art museum", "natural history", "large complex", "campus"],
}

TIME_NEEDED_ALLOWED = {"Quick stop (<1 hr)", "Half day", "Full day"}
TIME_NEEDED_SYNONYMS = {
    "quick stop": "Quick stop (<1 hr)",
    "quick stop (1-2 hours)": "Quick stop (<1 hr)",
    "1-2 hours": "Quick stop (<1 hr)",
    "<1 hr": "Quick stop (<1 hr)",
    "half day (2-4 hours)": "Half day",
    "2-4 hours": "Half day",
    "half-day": "Half day",
    "full day (4+ hours)": "Full day",
    "4+ hours": "Full day",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Save JSON data, normalizing all placeholder values to null."""
    # Normalize placeholders before saving
    normalized_data = normalize_placeholders(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_placeholders(data: Any) -> Any:
    """
    Recursively normalize all placeholder strings to null.
    
    We either KNOW a value or it's null - no more "TBD", "Unknown", etc.
    """
    if isinstance(data, dict):
        return {k: normalize_placeholders(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize_placeholders(item) for item in data]
    elif isinstance(data, str):
        # Convert placeholder strings to None (will become null in JSON)
        if data.strip().casefold() in _PLACEHOLDER_STRINGS:
            return None
        return data
    else:
        return data


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
            try:
                return cache_path.read_text(encoding="utf-8", errors="ignore"), None
            except OSError:
                # Corrupt or unreadable cache file; remove and fall through to refetch
                try:
                    cache_path.unlink(missing_ok=True)
                except Exception:
                    pass

    time.sleep(max(0.0, float(min_delay_seconds)))
    
    try:
        raw, headers = http_get_bytes(url)
        content_type = (headers.get("content-type") or "").casefold()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            # Still cache it (for debugging), but skip parsing as HTML.
            cache_path.write_bytes(raw)
            return "", None

        try:
            cache_path.write_bytes(raw)
        except OSError:
            # If path/write fails, still return content to caller without caching
            return raw.decode("utf-8", errors="ignore"), None

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


def normalize_time_needed(value: str | None) -> str | None:
    """Normalize time_needed to MRD enum values.

    Accepts common variants (e.g., "1-2 hours", "half day (2-4 hours)") and
    returns one of: "Quick stop (<1 hr)", "Half day", "Full day". Returns
    None if the value cannot be mapped.
    """
    if not value:
        return None

    v = value.strip().lower()
    if v in (x.lower() for x in TIME_NEEDED_ALLOWED):
        # Already an allowed value (case-insensitive)
        for allowed in TIME_NEEDED_ALLOWED:
            if v == allowed.lower():
                return allowed

    if v in TIME_NEEDED_SYNONYMS:
        return TIME_NEEDED_SYNONYMS[v]

    return None


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

    # Insufficient evidence for reputation
    return None


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
    
    Returns one of the MRD enums: "Quick stop (<1 hr)" | "Half day" | "Full day" | None
    """
    if not museum_type:
        return None
    
    museum_type_lower = museum_type.lower()
    
    for time_category, keywords in TIME_NEEDED_KEYWORDS.items():
        if any(kw in museum_type_lower for kw in keywords):
            return time_category
    
    # Default for generic "museum"
    return "Half day"


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


def _try_google_places_lookup(museum_name: str, city: str, *, detailed: bool = False) -> Optional[dict[str, Any]]:
    """Try to get data from Google Places API.
    
    Args:
        museum_name: Name of museum
        city: City name
        detailed: If True, fetch additional details (hours, phone, photos) via Place Details API
    
    Returns:
        Dict with address, coordinates, place_id, and optionally hours/phone/photos
    """
    if not HAS_GOOGLE_MAPS:
        return None
    
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return None
    
    try:
        # Check cache first (14-day TTL)
        cache_key = f"google_places_{museum_name}_{city}_{detailed}"
        cache_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        cache_path = CACHE_DIR / f"google_places_{cache_hash[:16]}.json"
        
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age <= (60 * 60 * 24 * 14):  # 14 days
                try:
                    cached_data = json.loads(cache_path.read_text(encoding="utf-8"))
                    return cached_data
                except Exception:
                    pass
        
        gmaps = googlemaps.Client(key=api_key)
        query = f"{museum_name} {city}" if city and city != "Unknown" else museum_name
        places_result = gmaps.places(query=query)
        
        if places_result.get("results"):
            result = places_result["results"][0]
            data = {
                "street_address": result.get("formatted_address"),
                "latitude": result.get("geometry", {}).get("location", {}).get("lat"),
                "longitude": result.get("geometry", {}).get("location", {}).get("lng"),
                "place_id": result.get("place_id"),
            }
            
            # If detailed=True, get comprehensive Place Details in ONE call
            place_id = result.get("place_id")
            if place_id and detailed:
                try:
                    # Request ALL useful fields in ONE API call
                    details = gmaps.place(
                        place_id=place_id,
                        fields=[
                            "address_component",           # For postal code (note: singular in API)
                            "opening_hours",               # Business hours
                            "formatted_phone_number",      # Phone
                            "website",                     # Website URL
                            "url",                         # Google Maps URL
                            "photo",                       # Photos
                            "rating",                      # Star rating
                            "user_ratings_total",          # Review count
                            "review",                      # Reviews (singular)
                            "business_status",             # OPERATIONAL, CLOSED_TEMPORARILY, etc.
                            "type",                        # Categories (singular)
                            "price_level",                 # 0-4 scale
                            "wheelchair_accessible_entrance",  # Accessibility
                            "editorial_summary",           # Google's AI summary
                        ]
                    )
                    
                    if details.get("result"):
                        detail_result = details["result"]
                        
                        # Extract postal code from address_components
                        address_components = detail_result.get("address_components", [])
                        for component in address_components:
                            if "postal_code" in component.get("types", []):
                                data["postal_code"] = component.get("long_name")
                                break
                        
                        # Extract hours
                        hours_data = detail_result.get("opening_hours", {})
                        if hours_data.get("weekday_text"):
                            data["hours"] = "\n".join(hours_data["weekday_text"])
                        
                        # Extract phone
                        if detail_result.get("formatted_phone_number"):
                            data["phone"] = detail_result["formatted_phone_number"]
                        
                        # Extract website
                        if detail_result.get("website"):
                            data["website"] = detail_result["website"]
                        
                        # Extract Google Maps URL
                        if detail_result.get("url"):
                            data["google_maps_url"] = detail_result["url"]
                        
                        # Extract photo count
                        if detail_result.get("photo"):
                            data["photo_count"] = len(detail_result["photo"])
                        
                        # Extract rating
                        if detail_result.get("rating"):
                            data["rating"] = detail_result["rating"]
                            data["review_count"] = detail_result.get("user_ratings_total", 0)
                        
                        # Extract business status (OPERATIONAL, CLOSED_TEMPORARILY, CLOSED_PERMANENTLY)
                        if detail_result.get("business_status"):
                            data["business_status"] = detail_result["business_status"]
                        
                        # Extract types/categories
                        if detail_result.get("types"):
                            data["types"] = detail_result["types"]
                        
                        # Extract price level (0=Free, 1=$, 2=$$, 3=$$$, 4=$$$$)
                        if detail_result.get("price_level") is not None:
                            data["price_level"] = detail_result["price_level"]
                        
                        # Extract accessibility
                        if detail_result.get("wheelchair_accessible_entrance") is not None:
                            data["wheelchair_accessible"] = detail_result["wheelchair_accessible_entrance"]
                        
                        # Extract editorial summary (Google's AI-generated description)
                        editorial = detail_result.get("editorial_summary", {})
                        if editorial.get("overview"):
                            data["editorial_summary"] = editorial["overview"]
                        
                        # Extract reviews (first 5)
                        reviews = detail_result.get("reviews", [])
                        if reviews:
                            data["reviews"] = reviews[:5]  # Store up to 5 reviews
                        
                except Exception:
                    # If details fetch fails, at least try to get postal code
                    try:
                        postal_details = gmaps.place(place_id=place_id, fields=["address_component"])
                        if postal_details.get("result"):
                            address_components = postal_details["result"].get("address_components", [])
                            for component in address_components:
                                if "postal_code" in component.get("types", []):
                                    data["postal_code"] = component.get("long_name")
                                    break
                    except Exception:
                        pass
            elif place_id:
                # Even if not detailed, still get postal code
                try:
                    postal_details = gmaps.place(place_id=place_id, fields=["address_component"])
                    if postal_details.get("result"):
                        address_components = postal_details["result"].get("address_components", [])
                        for component in address_components:
                            if "postal_code" in component.get("types", []):
                                data["postal_code"] = component.get("long_name")
                                break
                except Exception:
                    pass
            
            # Cache the result
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
            
            return data
    except Exception:
        pass
    
    return None


def _try_yelp_lookup(museum_name: str, city: str, state_code: str) -> Optional[dict[str, Any]]:
    """Try to get data from Yelp Fusion API.
    
    Returns:
        Dict with address, hours, phone, photos, rating, etc. from Yelp
    """
    if not HAS_YELP:
        return None
    
    api_key = os.getenv("YELP_API_KEY")
    if not api_key:
        return None
    
    try:
        yelp = YelpAPI(api_key)
        
        # Search for business
        response = yelp.search_query(
            term=museum_name,
            location=f"{city}, {state_code}",
            categories="museums",
            limit=1
        )
        
        if not response.get("businesses"):
            return None
        
        business = response["businesses"][0]
        
        data = {
            "yelp_id": business.get("id"),
            "street_address": None,
            "city": None,
            "postal_code": None,
            "latitude": None,
            "longitude": None,
            "phone": None,
            "rating": None,
            "review_count": None,
            "photo_count": None,
            "hours": None,
        }
        
        # Extract location data
        location = business.get("location", {})
        if location.get("address1"):
            data["street_address"] = location["address1"]
        if location.get("city"):
            data["city"] = location["city"]
        if location.get("zip_code"):
            data["postal_code"] = location["zip_code"]
        
        # Extract coordinates
        coords = business.get("coordinates", {})
        if coords.get("latitude"):
            data["latitude"] = coords["latitude"]
        if coords.get("longitude"):
            data["longitude"] = coords["longitude"]
        
        # Extract phone (strip +1 if present)
        phone = business.get("phone", "")
        if phone.startswith("+1"):
            phone = phone[2:]
        if phone:
            data["phone"] = phone
        
        # Extract rating and reviews
        if business.get("rating"):
            data["rating"] = business["rating"]
        if business.get("review_count"):
            data["review_count"] = business["review_count"]
        
        # Extract photo count
        if business.get("photos"):
            data["photo_count"] = len(business["photos"])
        
        # Try to get hours via Business Details API
        try:
            yelp_id = business.get("id")
            if yelp_id:
                details = yelp.business_query(id=yelp_id)
                
                hours_data = details.get("hours", [])
                if hours_data:
                    # Format hours nicely
                    hours_lines = []
                    for hour_block in hours_data:
                        if hour_block.get("open"):
                            for day_info in hour_block["open"]:
                                day = day_info.get("day", 0)
                                start = day_info.get("start", "")
                                end = day_info.get("end", "")
                                
                                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                                if 0 <= day < 7 and start and end:
                                    # Format time from 24hr to 12hr
                                    start_hr = int(start[:2])
                                    start_min = start[2:]
                                    end_hr = int(end[:2])
                                    end_min = end[2:]
                                    
                                    start_ampm = "AM" if start_hr < 12 else "PM"
                                    end_ampm = "AM" if end_hr < 12 else "PM"
                                    
                                    start_hr = start_hr if start_hr <= 12 else start_hr - 12
                                    start_hr = 12 if start_hr == 0 else start_hr
                                    end_hr = end_hr if end_hr <= 12 else end_hr - 12
                                    end_hr = 12 if end_hr == 0 else end_hr
                                    
                                    hours_lines.append(
                                        f"{day_names[day]}: {start_hr}:{start_min} {start_ampm} - {end_hr}:{end_min} {end_ampm}"
                                    )
                    
                    if hours_lines:
                        data["hours"] = "\n".join(hours_lines)
        except Exception:
            # If hours fetch fails, continue with other data
            pass
        
        return data
    
    except Exception:
        pass
    
    return None


def _extract_with_extruct(html: str, base_url: str) -> list[dict[str, Any]]:
    """Extract structured data using extruct. Returns empty list if not available."""
    if not HAS_EXTRUCT:
        return []
    
    try:
        data = extruct.extract(html, base_url=base_url)
        results = []
        
        # Collect all JSON-LD objects
        for item in data.get("json-ld", []):
            if isinstance(item, dict):
                results.append(item)
        
        # Also check microdata
        for item in data.get("microdata", []):
            if isinstance(item, dict):
                results.append(item)
        
        return results
    except Exception:
        return []


def _extract_addresses_with_pyap(html: str, state_code: str) -> list[dict[str, str]]:
    """
    Extract addresses using pyap (Python Address Parser).
    
    This is purpose-built for finding addresses in unstructured text.
    Returns list of dicts with 'street_address', 'city', 'postal_code'.
    """
    if not HAS_PYAP:
        return []
    
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get text, focusing on main content areas
        # Try footer first (addresses often there)
        text_sources = []
        footer = soup.find('footer')
        if footer:
            text_sources.append(footer.get_text(separator=' '))
        
        # Also check address/contact sections
        for elem in soup.find_all(['address', 'div'], class_=re.compile(r'address|contact|location', re.I)):
            text_sources.append(elem.get_text(separator=' '))
        
        # Fallback: full page text
        if not text_sources:
            text_sources.append(soup.get_text(separator=' '))
        
        # Parse addresses from each text source
        found_addresses = []
        for text in text_sources:
            if not text or len(text) > 10000:  # Skip if too large
                continue
                
            addresses = pyap.parse(text, country='US')
            
            for addr in addresses:
                addr_str = str(addr).strip()
                
                # Only accept if it mentions our state
                if state_code.upper() in addr_str.upper() or any(
                    state_name in addr_str 
                    for state_name in [_state_code_to_name(state_code)]
                ):
                    # Try to parse components
                    parsed = _parse_pyap_address(addr_str, state_code)
                    if parsed:
                        found_addresses.append(parsed)
        
        return found_addresses
    
    except Exception:
        return []


def _parse_pyap_address(address_str: str, state_code: str) -> Optional[dict[str, str]]:
    """Parse pyap address object into components."""
    import re
    
    # Extract ZIP code
    zip_match = re.search(r'\b(\d{5})(?:-\d{4})?\b', address_str)
    if not zip_match:
        return None
    
    postal_code = zip_match.group(1)
    
    # Extract street address (everything before city/state)
    # Look for pattern: "Number Street Type"
    street_pattern = r'(\d+\s+(?:[NSEW]\.?\s+)?[\w\s\.]+?(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Parkway|Pkwy|Plaza|Pl|Place)\.?)'
    street_match = re.search(street_pattern, address_str, re.IGNORECASE)
    if not street_match:
        return None
    
    street_address = street_match.group(1).strip()
    
    # Extract city (word(s) before state abbreviation)
    state_name = _state_code_to_name(state_code)
    city_pattern = rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,?\s*(?:{state_code}|{state_name})'
    city_match = re.search(city_pattern, address_str, re.IGNORECASE)
    
    city = city_match.group(1).strip() if city_match else None
    
    if not city or len(city) < 2:
        return None
    
    return {
        "street_address": street_address,
        "city": city,
        "postal_code": postal_code
    }


def _state_code_to_name(state_code: str) -> str:
    """Convert state code to full name."""
    states = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia"
    }
    return states.get(state_code.upper(), state_code)


def _extract_meta_description(html: str) -> Optional[str]:
    """
    Extract meta description from HTML head.
    
    This is often the best museum summary available.
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try og:description first (often richer)
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try standard meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Twitter description
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc['content'].strip()
        
    except Exception:
        pass
    
    return None


def _extract_contact_info(html: str) -> Dict[str, Optional[str]]:
    """
    Extract phone and email from HTML.
    
    Returns dict with 'phone' and 'email' keys.
    """
    result = {'phone': None, 'email': None}
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ')
        
        # Extract phone (US format)
        phone_pattern = r'(?:\+1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            result['phone'] = phone_match.group(0)
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            result['email'] = email_match.group(0)
        
    except Exception:
        pass
    
    return result


def _extract_hours_info(html: str) -> Optional[str]:
    """
    Extract hours of operation from HTML.
    
    Looks for common patterns like "Tuesday-Saturday 10am-5pm".
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for elements with hours-related text
        for elem in soup.find_all(['div', 'p', 'span'], class_=re.compile(r'hours?|open|schedule', re.I)):
            text = elem.get_text(separator=' ', strip=True)
            if text and len(text) < 300:  # Reasonable length
                # Check if it contains day names and time patterns
                has_days = any(day in text for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
                has_time = re.search(r'\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)', text)
                if has_days or has_time:
                    return text
        
        # Fallback: search full text for hours patterns near keywords
        text = soup.get_text(separator='\n')
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['hours', 'open', 'visit', 'schedule']):
                # Get context (this line + next few lines)
                context_lines = lines[i:i+5]
                context = ' '.join(l.strip() for l in context_lines if l.strip())
                if len(context) < 300:
                    has_days = any(day in context for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
                    has_time = re.search(r'\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)', context)
                    if has_days or has_time:
                        return context[:300]  # Truncate if too long
        
    except Exception:
        pass
    
    return None


def _extract_visitor_urls(html: str, base_url: str) -> Dict[str, Optional[str]]:
    """
    Extract visitor info URLs (hours, tickets, accessibility).
    
    Returns dict with 'hours_url', 'tickets_url', 'accessibility_url'.
    """
    from urllib.parse import urljoin
    
    result = {'hours_url': None, 'tickets_url': None, 'accessibility_url': None}
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            href_lower = href.lower()
            
            # Hours/visit links
            if not result['hours_url']:
                if any(keyword in text for keyword in ['hours', 'visit', 'plan your visit', 'visiting']):
                    result['hours_url'] = urljoin(base_url, href)
                elif any(keyword in href_lower for keyword in ['/visit', '/hours', '/plan-your-visit']):
                    result['hours_url'] = urljoin(base_url, href)
            
            # Tickets/admission links
            if not result['tickets_url']:
                if any(keyword in text for keyword in ['tickets', 'admission', 'buy tickets', 'book']):
                    result['tickets_url'] = urljoin(base_url, href)
                elif any(keyword in href_lower for keyword in ['/tickets', '/admission', '/book']):
                    result['tickets_url'] = urljoin(base_url, href)
            
            # Accessibility links
            if not result['accessibility_url']:
                if any(keyword in text for keyword in ['accessibility', 'accessible', 'ada']):
                    result['accessibility_url'] = urljoin(base_url, href)
                elif any(keyword in href_lower for keyword in ['/accessibility', '/accessible', '/ada']):
                    result['accessibility_url'] = urljoin(base_url, href)
            
            # Stop if we found all
            if all(result.values()):
                break
        
    except Exception:
        pass
    
    return result


def _fetch_and_extract_from_dedicated_page(url: str, extraction_type: str, min_delay_seconds: float = 1.0) -> Optional[str]:
    """
    Fetch a dedicated page (hours, accessibility, etc.) and extract relevant information.
    
    Args:
        url: The URL to fetch
        extraction_type: 'hours', 'accessibility', or 'parking'
        min_delay_seconds: Minimum delay between requests
        
    Returns:
        Extracted text or None if not found
    """
    try:
        # Respect rate limiting
        html, error = cached_get_html(url, min_delay_seconds=min_delay_seconds)
        if error or not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        if extraction_type == 'hours':
            # Try to find hours section - check heading tags first
            for elem in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                if re.search(r'(museum\s+)?hours(\s+of\s+operation)?', elem.get_text(), re.I):
                    # Found hours heading, get the next sibling or parent's text
                    parent = elem.find_parent(['section', 'div', 'article'])
                    if parent:
                        text = parent.get_text(separator='\n', strip=True)
                        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l) < 100]
                        relevant_lines = []
                        for line in lines:
                            if any(day in line for day in ['Monday', 'Tuesday', 'Wednesday', 
                                                          'Thursday', 'Friday', 'Saturday', 'Sunday', 'closed']):
                                relevant_lines.append(line)
                            elif re.search(r'\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.|am|pm)', line, re.I):
                                relevant_lines.append(line)
                        if relevant_lines:
                            return ' '.join(relevant_lines[:6])[:300]
            
            # Try to find hours section by class
            for elem in soup.find_all(['div', 'section', 'p', 'span'], 
                                      class_=re.compile(r'hours?|schedule|timing', re.I)):
                text = elem.get_text(separator='\n', strip=True)
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                relevant_lines = []
                for line in lines:
                    if len(line) > 5 and len(line) < 100:
                        has_day = any(day in line for day in ['Monday', 'Tuesday', 'Wednesday', 
                                                              'Thursday', 'Friday', 'Saturday', 'Sunday', 'closed'])
                        has_time = re.search(r'\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.|am|pm)', line, re.I)
                        if has_day or has_time:
                            relevant_lines.append(line)
                if relevant_lines:
                    return ' '.join(relevant_lines[:6])[:300]
            
            # Fallback: search for hours patterns in full text
            text = soup.get_text(separator='\n')
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                if re.match(r'(museum\s+)?hours(\s+of\s+operation)?', line, re.I):
                    # Grab next lines that might contain hours
                    context_lines = []
                    for j in range(i+1, min(i+10, len(lines))):
                        next_line = lines[j]
                        if len(next_line) > 5 and len(next_line) < 100:
                            has_day = any(day in next_line for day in ['Monday', 'Tuesday', 'Wednesday', 
                                                                       'Thursday', 'Friday', 'Saturday', 'Sunday', 'closed'])
                            has_time = re.search(r'\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.|am|pm)', next_line, re.I)
                            if has_day or has_time:
                                context_lines.append(next_line)
                        if len(context_lines) >= 5:
                            break
                    if context_lines:
                        return ' '.join(context_lines)[:300]
        
        elif extraction_type == 'accessibility':
            # Look for accessibility information
            for elem in soup.find_all(['div', 'section', 'p'], 
                                      class_=re.compile(r'access|ada|disability', re.I)):
                text = elem.get_text(separator=' ', strip=True)
                if text and 20 < len(text) < 500:
                    # Clean and return
                    text = re.sub(r'\s+', ' ', text)
                    return text[:300]
            
            # Look for specific accessibility keywords
            text = soup.get_text(separator='\n')
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['wheelchair', 'accessible', 'ada compliant', 'accommodation']):
                    context_lines = [l.strip() for l in lines[i:i+6] if l.strip()]
                    context = ' '.join(context_lines[:4])
                    if 20 < len(context) < 400:
                        return context[:300]
        
        elif extraction_type == 'parking':
            # Look for parking information
            for elem in soup.find_all(['div', 'section', 'p'], 
                                      class_=re.compile(r'parking|garage', re.I)):
                text = elem.get_text(separator=' ', strip=True)
                if text and 15 < len(text) < 300:
                    if any(keyword in text.lower() for keyword in ['parking', 'garage', 'lot', 'street parking']):
                        text = re.sub(r'\s+', ' ', text)
                        return text[:200]
            
            # Search in full text
            text = soup.get_text(separator='\n')
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'parking' in line.lower():
                    context_lines = [l.strip() for l in lines[i:i+4] if l.strip()]
                    context = ' '.join(context_lines[:3])
                    if 15 < len(context) < 300:
                        return context[:200]
        
    except Exception:
        pass
    
    return None


def _parse_address_with_usaddress(text: str) -> Optional[dict[str, str]]:
    """Try to parse address from text using usaddress. Returns None if not available."""
    if not HAS_USADDRESS:
        return None
    
    try:
        parsed, addr_type = usaddress.tag(text)
        
        # Only return if it looks like a complete address
        if "AddressNumber" in parsed and "StreetName" in parsed:
            street_parts = []
            if parsed.get("AddressNumber"):
                street_parts.append(parsed["AddressNumber"])
            if parsed.get("StreetNamePreDirectional"):
                street_parts.append(parsed["StreetNamePreDirectional"])
            if parsed.get("StreetName"):
                street_parts.append(parsed["StreetName"])
            if parsed.get("StreetNamePostType"):
                street_parts.append(parsed["StreetNamePostType"])
            
            return {
                "street_address": " ".join(street_parts),
                "city": parsed.get("PlaceName"),
                "state": parsed.get("StateName"),
                "postal_code": parsed.get("ZipCode"),
            }
    except Exception:
        pass
    
    return None


def patch_from_official_website(
    museum: dict[str, Any],
    *,
    max_pages: int = 2,
    min_delay_seconds: float = 1.0,
) -> PatchResult:
    website = normalize_website(str(museum.get("website") or ""))
    if not website or not is_http_url(website):
        return PatchResult(patch={}, sources_used=[], notes=["Official site: missing/invalid website URL"]) 

    patch: dict[str, Any] = {}
    notes: list[str] = []
    sources_used: list[str] = []
    errors: list[str] = []

    # ===================================================================
    # PRIORITY 0: Business Location APIs (Yelp, Google Places)
    # Try these FIRST before web scraping - they're more reliable and 
    # don't burn LLM tokens on basic data like addresses and hours
    # ===================================================================
    
    museum_name = museum.get("museum_name")
    city = museum.get("city")
    
    # Extract state code from museum_id
    state_code = None
    museum_id = museum.get("museum_id", "")
    if isinstance(museum_id, str) and museum_id.startswith("usa-"):
        parts = museum_id.split("-")
        if len(parts) >= 2:
            state_code = parts[1].upper()
    
    # Try Yelp Fusion API (5K free calls/day, excellent for museum data)
    if HAS_YELP and state_code:
        yelp_data = _try_yelp_lookup(museum_name, city, state_code)
        if yelp_data:
            sources_used.append("yelp_fusion_api")
            
            # Address data
            if yelp_data.get("street_address") and should_fill(museum.get("street_address")):
                patch["street_address"] = yelp_data["street_address"]
                patch.setdefault("address_source", "yelp")
                patch.setdefault("address_last_verified", today_yyyy_mm_dd())
                notes.append("Yelp: extracted street address")
            
            if yelp_data.get("city") and should_fill(museum.get("city")):
                patch["city"] = yelp_data["city"]
            
            if yelp_data.get("postal_code") and should_fill(museum.get("postal_code")):
                patch["postal_code"] = yelp_data["postal_code"]
            
            # Coordinates
            if yelp_data.get("latitude") and museum.get("latitude") is None:
                patch["latitude"] = yelp_data["latitude"]
            
            if yelp_data.get("longitude") and museum.get("longitude") is None:
                patch["longitude"] = yelp_data["longitude"]
            
            # Hours
            if yelp_data.get("hours") and should_fill(museum.get("open_hour_notes")):
                patch["open_hour_notes"] = yelp_data["hours"]
                notes.append("Yelp: extracted operating hours")
            
            # Phone
            if yelp_data.get("phone"):
                # Add to notes field
                phone_note = f"\nPhone: {yelp_data['phone']}"
                if patch.get("notes"):
                    patch["notes"] += phone_note
                else:
                    patch["notes"] = phone_note.strip()
            
            # Rating & reviews (for reputation assessment)
            if yelp_data.get("rating") and yelp_data.get("review_count"):
                rating_note = f"\nYelp Rating: {yelp_data['rating']}/5 ({yelp_data['review_count']} reviews)"
                if patch.get("notes"):
                    patch["notes"] += rating_note
                else:
                    patch["notes"] = rating_note.strip()
                notes.append(f"Yelp: {yelp_data['rating']}/5 rating with {yelp_data['review_count']} reviews")
    
    # Try Google Places API with detailed=True to get hours, phone, photos
    if HAS_GOOGLE_MAPS:
        google_data = _try_google_places_lookup(museum_name, city, detailed=True)
        if google_data:
            sources_used.append("google_places_api")
            
            # Address data (if Yelp didn't fill it)
            if google_data.get("street_address") and should_fill(patch.get("street_address", museum.get("street_address"))):
                patch["street_address"] = google_data["street_address"]
                patch.setdefault("address_source", "google_places")
                patch.setdefault("address_last_verified", today_yyyy_mm_dd())
                notes.append("Google Places: extracted street address")
            
            # Postal code (if available from Google)
            if google_data.get("postal_code") and should_fill(patch.get("postal_code", museum.get("postal_code"))):
                patch["postal_code"] = google_data["postal_code"]
                notes.append("Google Places: extracted postal code")
            
            # Coordinates (if Yelp didn't fill it)
            if google_data.get("latitude") and patch.get("latitude") is None and museum.get("latitude") is None:
                patch["latitude"] = google_data["latitude"]
            
            if google_data.get("longitude") and patch.get("longitude") is None and museum.get("longitude") is None:
                patch["longitude"] = google_data["longitude"]
            
            if google_data.get("place_id") and museum.get("place_id") is None:
                patch["place_id"] = google_data["place_id"]
            
            # Hours (if Yelp didn't fill it)
            if google_data.get("hours") and should_fill(patch.get("open_hour_notes", museum.get("open_hour_notes"))):
                patch["open_hour_notes"] = google_data["hours"]
                notes.append("Google Places: extracted operating hours")
            
            # Phone (if Yelp didn't provide it)
            if google_data.get("phone") and "Phone:" not in (patch.get("notes") or ""):
                phone_note = f"\nPhone: {google_data['phone']}"
                if patch.get("notes"):
                    patch["notes"] += phone_note
                else:
                    patch["notes"] = phone_note.strip()
            
            # Rating & photo count
            if google_data.get("rating") and google_data.get("review_count"):
                rating_note = f"\nGoogle Rating: {google_data['rating']}/5 ({google_data['review_count']} reviews)"
                if patch.get("notes"):
                    patch["notes"] += rating_note
                else:
                    patch["notes"] = rating_note.strip()
                notes.append(f"Google Places: {google_data['rating']}/5 rating with {google_data['review_count']} reviews")
            
            if google_data.get("photo_count"):
                notes.append(f"Google Places: {google_data['photo_count']} photos available")
            
            # Business status (operational, closed temporarily, closed permanently)
            if google_data.get("business_status"):
                status_map = {
                    "OPERATIONAL": "Active",
                    "CLOSED_TEMPORARILY": "Temporarily Closed",
                    "CLOSED_PERMANENTLY": "Permanently Closed"
                }
                status = status_map.get(google_data["business_status"], google_data["business_status"])
                if should_fill(museum.get("status")):
                    patch["status"] = status
                    notes.append(f"Google Places: business status is {status}")
            
            # Editorial summary (Google's AI-generated description)
            if google_data.get("editorial_summary") and should_fill(patch.get("notes", museum.get("notes"))):
                summary = google_data["editorial_summary"]
                if patch.get("notes"):
                    patch["notes"] = summary + "\n\n" + patch["notes"]
                else:
                    patch["notes"] = summary
                notes.append("Google Places: extracted editorial summary")
            
            # Wheelchair accessibility
            if google_data.get("wheelchair_accessible") is not None:
                accessible = google_data["wheelchair_accessible"]
                if accessible and "accessibility" not in (patch.get("notes") or "").lower():
                    access_note = "\n♿ Wheelchair accessible entrance available" if accessible else "\n⚠️ No wheelchair accessible entrance"
                    if patch.get("notes"):
                        patch["notes"] += access_note
                    else:
                        patch["notes"] = access_note.strip()
                    notes.append(f"Google Places: wheelchair accessibility = {accessible}")
    
    # If business APIs filled all critical fields, we might skip web scraping
    # But we still want to check for specific URLs (hours page, tickets page, etc.)
    # So continue to web scraping section...
    
    # ===================================================================
    # WEB SCRAPING (fallback if APIs didn't provide everything)
    # ===================================================================
    
    if not can_fetch_url(website):
        # robots.txt blocks us, but we may have gotten data from APIs
        if sources_used:
            notes.append("Official site: blocked by robots.txt (but got data from business APIs)")
            return PatchResult(patch=patch, sources_used=sources_used, notes=notes)
        else:
            return PatchResult(patch={}, sources_used=[], notes=["Official site: blocked by robots.txt"]) 
    
    sources_used.append("official_website")
    sources_used.append(website)

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
        
        # Cache the HTML for LLM enrichment use
        museum_id = museum.get("museum_id")
        state_code = None
        if isinstance(museum_id, str) and museum_id.startswith("usa-"):
            parts = museum_id.split("-")
            if len(parts) >= 2:
                state_code = parts[1].upper()
                
        if state_code and museum_id:
            import hashlib
            hash_bytes = hashlib.sha256(museum_id.encode("utf-8")).hexdigest()
            folder_hash = f"m_{hash_bytes[:8]}"
            cache_dir = PROJECT_ROOT / "data" / "states" / state_code / folder_hash / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the HTML for LLM use
            html_path = cache_dir / "website_html.html"
            html_path.write_text(html, encoding="utf-8")
            notes.append(f"Official site: cached HTML for LLM enrichment")
        
        # Extract rich metadata from website
        # 1. Meta description for notes field
        if should_fill(museum.get("notes")):
            meta_desc = _extract_meta_description(html)
            if meta_desc and len(meta_desc) > 20:  # Meaningful description
                patch["notes"] = meta_desc
                notes.append("Official site: extracted meta description")
        
        # 2. Contact information
        contact = _extract_contact_info(html)
        contact_parts = []
        if contact['phone']:
            contact_parts.append(f"Phone: {contact['phone']}")
        if contact['email']:
            contact_parts.append(f"Email: {contact['email']}")
        
        # 3. Hours information
        hours_text = _extract_hours_info(html)
        if hours_text and should_fill(museum.get("open_hour_notes")):
            patch["open_hour_notes"] = hours_text
            notes.append("Official site: extracted hours information")
        
        # Append contact info to notes if we have description
        if contact_parts and patch.get("notes"):
            patch["notes"] = patch["notes"] + "\n\n" + "\n".join(contact_parts)
            notes.append(f"Official site: extracted {len(contact_parts)} contact detail(s)")
        
        # 4. Visitor information URLs
        visitor_urls = _extract_visitor_urls(html, url)
        if visitor_urls['hours_url'] and should_fill(museum.get("open_hours_url")):
            patch["open_hours_url"] = visitor_urls['hours_url']
            notes.append("Official site: found hours/visit URL")
        
        # Fetch the hours page to extract actual hours text (always try if URL found)
        if visitor_urls['hours_url'] and should_fill(museum.get("open_hour_notes")):
            hours_from_page = _fetch_and_extract_from_dedicated_page(
                visitor_urls['hours_url'], 
                'hours', 
                min_delay_seconds=min_delay_seconds
            )
            if hours_from_page:
                patch["open_hour_notes"] = hours_from_page
                notes.append("Official site: extracted hours from dedicated page")
        
        if visitor_urls['tickets_url'] and should_fill(museum.get("tickets_url")):
            patch["tickets_url"] = visitor_urls['tickets_url']
            notes.append("Official site: found tickets URL")
            
        if visitor_urls['accessibility_url'] and should_fill(museum.get("accessibility_url")):
            patch["accessibility_url"] = visitor_urls['accessibility_url']
            notes.append("Official site: found accessibility URL")
            
        # Fetch accessibility page for detailed info (always try if URL found)
        if visitor_urls['accessibility_url']:
            accessibility_text = _fetch_and_extract_from_dedicated_page(
                visitor_urls['accessibility_url'],
                'accessibility',
                min_delay_seconds=min_delay_seconds
            )
            if accessibility_text:
                # Append to notes or create separate field
                if patch.get("notes"):
                    patch["notes"] = patch["notes"] + f"\n\nAccessibility: {accessibility_text}"
                notes.append("Official site: extracted accessibility info")
        
        # Try to extract parking info from hours/visit page (always try if URL found)
        if visitor_urls['hours_url'] and should_fill(museum.get("parking_notes")):
            parking_info = _fetch_and_extract_from_dedicated_page(
                visitor_urls['hours_url'],
                'parking',
                min_delay_seconds=min_delay_seconds
            )
            if parking_info:
                patch["parking_notes"] = parking_info
                notes.append("Official site: extracted parking information")
            
    except Exception as e:
        error_msg = f"Failed to parse HTML: {str(e)[:100]}"
        notes.append(f"Official site: {error_msg}")
        errors.append(error_msg)
        patch["row_notes_internal"] = f"Website scraping errors: {error_msg}"
        return PatchResult(patch=patch, sources_used=sources_used, notes=notes)

    # Priority 2: Try extruct for better structured data extraction
    if should_fill(museum.get("street_address")) or should_fill(patch.get("street_address")):
        structured_data = _extract_with_extruct(html, website)
        
        for item in structured_data:
            # Look for schema.org address objects
            address = item.get("address")
            if isinstance(address, dict):
                street = address.get("streetAddress")
                postal = address.get("postalCode")
                locality = address.get("addressLocality")
                
                if street and should_fill(patch.get("street_address")):
                    patch["street_address"] = street.strip()
                    patch.setdefault("address_source", "structured_data")
                    patch.setdefault("address_last_verified", today_yyyy_mm_dd())
                    notes.append("Extruct: extracted street address from structured data")
                
                if postal and should_fill(patch.get("postal_code")):
                    patch["postal_code"] = postal.strip()
                
                if locality and should_fill(patch.get("city")):
                    patch["city"] = locality.strip()
                    notes.append(f"Extruct: extracted city '{locality}' from structured data")
                
                break  # Use first valid address found

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
    
    # Priority 2.5: Try pyap (Python Address Parser) - purpose-built for finding addresses
    if should_fill(museum.get("street_address")) or should_fill(patch.get("street_address")):
        state_code = None
        museum_id = museum.get("museum_id", "")
        if isinstance(museum_id, str):
            parts = museum_id.split("-")
            if len(parts) >= 2 and parts[0] == "usa":
                state_code = parts[1].upper()
        
        if state_code:
            pyap_addresses = _extract_addresses_with_pyap(html, state_code)
            if pyap_addresses:
                # Use the first address found
                addr = pyap_addresses[0]
                if addr.get("street_address") and should_fill(patch.get("street_address")):
                    patch["street_address"] = addr["street_address"]
                    patch.setdefault("address_source", "pyap_parser")
                    patch.setdefault("address_last_verified", today_yyyy_mm_dd())
                    notes.append("Pyap: extracted street address from page text")
                
                if addr.get("city") and should_fill(patch.get("city")):
                    patch["city"] = addr["city"]
                
                if addr.get("postal_code") and should_fill(patch.get("postal_code")):
                    patch["postal_code"] = addr["postal_code"]
    
    # Priority 3: Try usaddress parser on the page text
    if should_fill(museum.get("street_address")) and should_fill(patch.get("street_address")):
        parsed_addr = _parse_address_with_usaddress(page_text)
        if parsed_addr and parsed_addr.get("street_address"):
            if should_fill(patch.get("street_address")):
                patch["street_address"] = parsed_addr["street_address"]
                patch.setdefault("address_source", "usaddress_parser")
                patch.setdefault("address_last_verified", today_yyyy_mm_dd())
                notes.append("usaddress: parsed street address from page text")
            
            if parsed_addr.get("city") and should_fill(patch.get("city")):
                patch["city"] = parsed_addr["city"]
            
            if parsed_addr.get("postal_code") and should_fill(patch.get("postal_code")):
                patch["postal_code"] = parsed_addr["postal_code"]
    
    # Extract state abbreviation from museum_id (e.g., "usa-ks-..." -> "KS")
    state_code = None
    museum_id = museum.get("museum_id", "")
    if isinstance(museum_id, str):
        parts = museum_id.split("-")
        if len(parts) >= 2 and parts[0] == "usa":
            state_code = parts[1].upper()
    
    # Priority 4: Regex-based extraction as final fallback
    # Try to extract full address first (e.g., "701 Beach Lane, Manhattan, KS 66506" or "242 S Santa Fe Ave<br>Salina, KS 67401")
    if should_fill(museum.get("street_address")) and should_fill(patch.get("street_address")) and state_code:
        # Get state name for pattern matching (e.g., "Oklahoma")
        state_names = {
            "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
            "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
            "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
            "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
            "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
            "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
            "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
            "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
            "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
            "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
            "DC": "District of Columbia"
        }
        state_name = state_names.get(state_code, state_code)
        
        # Pattern variations for different address formats
        # Capture full street names including type suffixes (Ave, St, Lane, etc.)
        # Use word boundaries and better constraints to avoid capturing too much text
        address_patterns = [
            # With full state name: "Number Street Type City, StateName ZIP"
            rf"\b(\d+\s+[NSEWnse]?\.?\s*[\w\s\.\-]+?(?:Avenue|Ave|Street|St|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Circle|Cir)\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*{state_name}\s+(\d{{5}})\b",
            # With state abbreviation: "Number Street Type City, ST ZIP"
            rf"\b(\d+\s+[NSEWnse]?\.?\s*[\w\s\.\-]+?(?:Avenue|Ave|Street|St|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Circle|Cir)\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*{state_code}\s+(\d{{5}})\b",
        ]
        
        # Find all matches and pick the shortest/cleanest one
        best_match = None
        best_length = float('inf')
        
        for pattern in address_patterns:
            for match in re.finditer(pattern, page_text, re.IGNORECASE):
                street = match.group(1).strip().rstrip(',')
                city = match.group(2).strip()
                zipcode = match.group(3).strip()
                
                # Validate street address (should have number and reasonable length)
                # Prefer shorter matches (less likely to have captured extra text)
                if (len(street) > 3 and len(street) < 100 and any(c.isdigit() for c in street) and len(street) < best_length):
                    best_match = (street, city, zipcode)
                    best_length = len(street)
        
        if best_match:
            patch["street_address"] = best_match[0]
            patch["city"] = best_match[1]
            patch["postal_code"] = best_match[2]
            patch.setdefault("address_source", "official_website")
            patch.setdefault("address_last_verified", today_yyyy_mm_dd())
            notes.append(f"Official site: extracted full address from page text")
    
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

    # Normalize time_needed to MRD enum; clear invalid values
    current_time_needed = museum3.get("time_needed")
    if isinstance(current_time_needed, str):
        normalized_time_needed = normalize_time_needed(current_time_needed)
        if normalized_time_needed:
            if normalized_time_needed != current_time_needed:
                museum3["time_needed"] = normalized_time_needed
                notes.append(
                    f"MRD: normalized time_needed '{current_time_needed}' -> '{normalized_time_needed}'"
                )
        else:
            museum3["time_needed"] = None
            notes.append(f"MRD: cleared invalid time_needed '{current_time_needed}' (not in enum)")

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
