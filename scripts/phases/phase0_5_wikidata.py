#!/usr/bin/env python3
"""Phase 0.5: Wikidata Enrichment (Open Data Source).

This module enriches museum records using Wikidata's free structured data.
It runs AFTER Phase 0 (identity resolution) but BEFORE Phase 1 (backbone).

Fields Populated from Wikidata:
    - website (P856): Official website
    - postal_code (P281): Postal code (fallback if Google Places failed)
    - latitude, longitude (P625): Coordinates (fallback if Phase 0 failed)
    - street_address (P969): Located at street address
    - museum_type enhancement (P31): Instance of claims

Design Principles:
    1. FREE DATA: No API keys required - uses Wikidata public API
    2. CONSERVATIVE: Only fills missing/null fields
    3. CACHED: HTTP responses cached to reduce API load
    4. IDEMPOTENT: Re-running preserves manual overrides
    5. TRACEABLE: Records data source in provenance

Why This Matters:
    Wikidata provides high-quality structured data for many museums.
    This phase captures that free data before any paid API calls.

Usage:
    # Enrich single state
    python scripts/phases/phase0_5_wikidata.py --state CO

    # Enrich all states
    python scripts/phases/phase0_5_wikidata.py --all-states

    # Dry run (show what would change)
    python scripts/phases/phase0_5_wikidata.py --state CO --dry-run

    # Force re-enrichment even if already has data
    python scripts/phases/phase0_5_wikidata.py --state CO --force
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "wikidata"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

USER_AGENT = "MuseumSpark/1.0 (https://github.com/MarkHazleton/MuseumSpark)"

# Placeholder values that should be replaced
PLACEHOLDER_VALUES = {"", "tbd", "unknown", "n/a", "na", "not known", "not available"}


@dataclass
class WikidataResult:
    """Result from Wikidata enrichment."""
    museum_id: str
    fields_updated: dict[str, Any]
    notes: list[str]
    qid: str | None = None
    error: str | None = None


def should_fill(value: Any) -> bool:
    """Check if a field value should be filled (is None or placeholder)."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in PLACEHOLDER_VALUES
    return False


def load_json(path: Path) -> Any:
    """Load JSON file."""
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, data: Any) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8'
    )


def cache_key(url: str, params: Optional[dict[str, Any]] = None) -> str:
    """Generate cache key for HTTP request."""
    blob = {"url": url, "params": params or {}}
    raw = json.dumps(blob, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def http_get_json(url: str, *, params: Optional[dict[str, Any]] = None, timeout_seconds: int = 30) -> Any:
    """Fetch JSON from URL."""
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
    except (HTTPError, URLError) as e:
        raise RuntimeError(f"HTTP error for {full_url}: {e}") from e


def cached_get_json(
    url: str,
    *,
    params: Optional[dict[str, Any]] = None,
    ttl_seconds: int = 60 * 60 * 24 * 14
) -> Any:
    """Fetch JSON with caching (2 week TTL by default)."""
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


def wikidata_search(name: str, city: str | None = None) -> list[dict[str, Any]]:
    """Search for Wikidata entity by museum name and city."""
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
    """Fetch full Wikidata entity by QID."""
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


def get_claim_value(entity: dict[str, Any], property_id: str) -> Any:
    """Extract first claim value for a property."""
    claims = entity.get("claims", {})
    entries = claims.get(property_id) or []
    for entry in entries:
        mainsnak = entry.get("mainsnak") or {}
        datavalue = mainsnak.get("datavalue") or {}
        value = datavalue.get("value")
        if value is not None:
            return value
    return None


def normalize_website(url: str) -> str:
    """Normalize website URL (remove trailing slashes)."""
    url = (url or "").strip()
    while url.endswith("/"):
        url = url[:-1]
    return url


def enrich_from_wikidata(
    museum: dict[str, Any],
    *,
    force: bool = False
) -> WikidataResult:
    """Enrich a single museum using Wikidata.
    
    Args:
        museum: Museum record dict
        force: If True, re-fetch even if already has Wikidata data
        
    Returns:
        WikidataResult with updated fields and notes
    """
    museum_id = museum.get("museum_id", "unknown")
    name = museum.get("museum_name") or ""
    city = museum.get("city") or ""
    
    if not name:
        return WikidataResult(
            museum_id=museum_id,
            fields_updated={},
            notes=["Skipped: missing museum_name"],
            error="missing museum_name"
        )
    
    # Check if already has wikidata source (skip unless --force)
    if not force:
        data_sources = museum.get("data_sources", [])
        if "wikidata" in data_sources:
            return WikidataResult(
                museum_id=museum_id,
                fields_updated={},
                notes=["Skipped: already has wikidata source (use --force to re-enrich)"]
            )
    
    # Search Wikidata
    try:
        results = wikidata_search(name=name, city=city)
    except Exception as e:
        return WikidataResult(
            museum_id=museum_id,
            fields_updated={},
            notes=[f"Search error: {e}"],
            error=str(e)
        )
    
    if not results:
        return WikidataResult(
            museum_id=museum_id,
            fields_updated={},
            notes=["No Wikidata search results"]
        )
    
    qid = results[0].get("id")
    if not qid:
        return WikidataResult(
            museum_id=museum_id,
            fields_updated={},
            notes=["Search returned no QID"]
        )
    
    # Fetch full entity
    try:
        entity = wikidata_entity(qid)
    except Exception as e:
        return WikidataResult(
            museum_id=museum_id,
            fields_updated={},
            notes=[f"Entity fetch error for {qid}: {e}"],
            qid=qid,
            error=str(e)
        )
    
    if not entity:
        return WikidataResult(
            museum_id=museum_id,
            fields_updated={},
            notes=[f"Entity not found for {qid}"],
            qid=qid,
            error=f"Entity not found: {qid}"
        )
    
    fields_updated: dict[str, Any] = {}
    notes: list[str] = [f"Matched Wikidata entity: {qid}"]
    
    # Extract fields from Wikidata
    
    # Website (P856: official website)
    if should_fill(museum.get("website")):
        website = get_claim_value(entity, "P856")
        if isinstance(website, str):
            fields_updated["website"] = normalize_website(website)
            notes.append("Added website from P856")
    
    # Postal code (P281: postal code)
    if should_fill(museum.get("postal_code")):
        postal = get_claim_value(entity, "P281")
        if isinstance(postal, str):
            fields_updated["postal_code"] = postal.strip()
            notes.append("Added postal_code from P281")
    
    # Street address (P969: street address)
    if should_fill(museum.get("street_address")):
        street = get_claim_value(entity, "P969")
        if isinstance(street, str):
            fields_updated["street_address"] = street.strip()
            notes.append("Added street_address from P969")
    
    # Coordinates (P625: coordinate location) - fallback if Phase 0 failed
    coord = get_claim_value(entity, "P625")
    if isinstance(coord, dict):
        lat = coord.get("latitude")
        lon = coord.get("longitude")
        if lat is not None and museum.get("latitude") is None:
            fields_updated["latitude"] = float(lat)
            notes.append("Added latitude from P625")
        if lon is not None and museum.get("longitude") is None:
            fields_updated["longitude"] = float(lon)
            notes.append("Added longitude from P625")
    
    # Add wikidata to data_sources if we updated anything
    if fields_updated:
        current_sources = museum.get("data_sources", [])
        if "wikidata" not in current_sources:
            fields_updated["data_sources"] = current_sources + ["wikidata"]
    
    return WikidataResult(
        museum_id=museum_id,
        fields_updated=fields_updated,
        notes=notes,
        qid=qid
    )


def process_state(
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False
) -> dict[str, Any]:
    """Process all museums in a state file.
    
    Returns:
        Summary statistics dict
    """
    state_path = STATES_DIR / f"{state_code}.json"
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    state_data = load_json(state_path)
    museums = state_data.get("museums", [])
    
    if not museums:
        return {
            "state": state_code,
            "total": 0,
            "processed": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }
    
    stats = {
        "state": state_code,
        "total": len(museums),
        "processed": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "details": []
    }
    
    for museum in museums:
        museum_id = museum.get("museum_id", "unknown")
        
        result = enrich_from_wikidata(museum, force=force)
        stats["processed"] += 1
        
        if result.error:
            stats["errors"] += 1
        elif result.fields_updated:
            stats["updated"] += 1
            # Apply updates
            if not dry_run:
                museum.update(result.fields_updated)
        else:
            stats["skipped"] += 1
        
        stats["details"].append({
            "museum_id": museum_id,
            "museum_name": museum.get("museum_name"),
            "qid": result.qid,
            "updated": bool(result.fields_updated),
            "fields": list(result.fields_updated.keys()),
            "notes": result.notes
        })
    
    # Write updated state file
    if not dry_run and stats["updated"] > 0:
        state_data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        save_json(state_path, state_data)
        print(f"✅ Wrote {state_path}")
    
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 0.5: Enrich museums using Wikidata"
    )
    
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Process all states")
    
    parser.add_argument("--force", action="store_true", help="Re-enrich even if already has wikidata source")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    
    args = parser.parse_args()
    
    # Determine states to process
    state_codes: list[str] = []
    if args.all_states:
        state_codes = sorted([p.stem.upper() for p in STATES_DIR.glob("*.json")
                             if len(p.stem) == 2 and p.stem.isalpha()])
    elif args.states:
        state_codes = [s.strip().upper() for s in args.states.split(",")]
    elif args.state:
        state_codes = [args.state.upper()]
    
    if not state_codes:
        print("❌ No states to process")
        return 1
    
    # Create run directory
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"phase0_5-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Phase 0.5: Wikidata Enrichment")
    print(f"   States: {', '.join(state_codes)}")
    print(f"   Force: {args.force}")
    print(f"   Dry run: {args.dry_run}")
    print(f"   Run ID: phase0_5-{run_id}")
    print()
    
    all_stats = []
    
    for state_code in state_codes:
        print(f"Processing {state_code}...")
        try:
            stats = process_state(
                state_code,
                force=args.force,
                dry_run=args.dry_run
            )
            all_stats.append(stats)
            
            print(f"  Total: {stats['total']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Skipped: {stats['skipped']}")
            print(f"  Errors: {stats['errors']}")
            print()
            
        except Exception as e:
            print(f"❌ Error processing {state_code}: {e}")
            all_stats.append({
                "state": state_code,
                "error": str(e)
            })
    
    # Save run summary
    summary = {
        "run_id": run_id,
        "phase": "0.5_wikidata",
        "states": state_codes,
        "force": args.force,
        "dry_run": args.dry_run,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "total_states": len(state_codes),
        "total_processed": sum(s.get("processed", 0) for s in all_stats),
        "total_updated": sum(s.get("updated", 0) for s in all_stats),
        "total_skipped": sum(s.get("skipped", 0) for s in all_stats),
        "total_errors": sum(s.get("errors", 0) for s in all_stats),
        "states_summary": all_stats
    }
    
    save_json(run_dir / "summary.json", summary)
    print(f"📊 Run summary saved to {run_dir / 'summary.json'}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
