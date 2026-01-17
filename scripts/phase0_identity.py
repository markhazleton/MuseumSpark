#!/usr/bin/env python3
"""Phase 0: Canonical Identity Resolution (MRD v2 Reboot).

This module is the FIRST phase of the rebooted MuseumSpark pipeline.
Its sole purpose is to establish canonical identity for each museum:

    Input:  museum_name, state_province, website (from seed roster)
    Output: city, street_address, postal_code, lat, lng, place_id

Design Principles:
    1. Google Places is the ONLY source for identity resolution
    2. City MUST be extracted from address_components.locality
    3. If city cannot be resolved → record is FLAGGED, not enriched
    4. No LLM involvement - this is purely deterministic
    5. Idempotent - re-running preserves manual overrides

Why This Matters:
    The previous pipeline extracted "Colorado" as city for Aspen Art Museum
    because it parsed the state from formatted_address instead of locality.
    This module fixes that by using Google Places address_components correctly.

Usage:
    # Process single museum
    python scripts/phase0_identity.py --museum-id usa-co-aspen-aspen-art-museum

    # Process all museums in a state
    python scripts/phase0_identity.py --state CO

    # Process all states (full rebuild)
    python scripts/phase0_identity.py --all-states

    # Dry run (show what would change without writing)
    python scripts/phase0_identity.py --state CO --dry-run

    # Force re-resolution even if city exists
    python scripts/phase0_identity.py --state CO --force
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Optional: Google Maps client
try:
    import googlemaps
    HAS_GOOGLE_MAPS = True
except ImportError:
    HAS_GOOGLE_MAPS = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "phase0"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

# Address component types that represent "city" in Google Places API
# Ordered by preference - locality is most reliable
CITY_COMPONENT_TYPES = [
    "locality",                    # Standard city (e.g., "Aspen")
    "sublocality_level_1",         # NYC boroughs, etc.
    "postal_town",                 # UK-style postal towns
    "administrative_area_level_3", # Some countries use this for cities
]

# Component type for state/province
STATE_COMPONENT_TYPES = [
    "administrative_area_level_1",
]


@dataclass
class IdentityResult:
    """Result of identity resolution for a single museum."""
    museum_id: str
    success: bool
    city: Optional[str] = None
    street_address: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    state_from_google: Optional[str] = None  # For validation
    error: Optional[str] = None
    source: str = "google_places"
    resolved_at: Optional[str] = None
    notes: list[str] = field(default_factory=list)

    def to_patch(self) -> dict[str, Any]:
        """Convert to patch dict for state file update."""
        if not self.success:
            return {}

        patch: dict[str, Any] = {}
        if self.city:
            patch["city"] = self.city
        if self.street_address:
            patch["street_address"] = self.street_address
        if self.postal_code:
            patch["postal_code"] = self.postal_code
        if self.latitude is not None:
            patch["latitude"] = self.latitude
        if self.longitude is not None:
            patch["longitude"] = self.longitude
        if self.place_id:
            patch["place_id"] = self.place_id

        return patch


@dataclass
class Phase0Stats:
    """Statistics for a Phase 0 run."""
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    flagged: list[str] = field(default_factory=list)  # museum_ids that need manual review


def load_json(path: Path) -> Any:
    """Load JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_utc_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def cache_key(museum_name: str, state: str) -> str:
    """Generate cache key for Google Places lookup."""
    blob = f"{museum_name}|{state}".lower()
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def extract_city_from_components(address_components: list[dict]) -> Optional[str]:
    """Extract city name from Google Places address_components.

    This is the CRITICAL function that fixes the city extraction bug.
    We iterate through component types in order of preference.
    """
    for component_type in CITY_COMPONENT_TYPES:
        for component in address_components:
            types = component.get("types", [])
            if component_type in types:
                return component.get("long_name")
    return None


def extract_state_from_components(address_components: list[dict]) -> Optional[str]:
    """Extract state/province from address_components for validation."""
    for component_type in STATE_COMPONENT_TYPES:
        for component in address_components:
            types = component.get("types", [])
            if component_type in types:
                return component.get("short_name")  # e.g., "CO" not "Colorado"
    return None


def extract_postal_code_from_components(address_components: list[dict]) -> Optional[str]:
    """Extract postal code from address_components."""
    for component in address_components:
        types = component.get("types", [])
        if "postal_code" in types:
            return component.get("long_name")
    return None


def resolve_identity_google_places(
    museum_name: str,
    state_province: str,
    website: Optional[str] = None,
    *,
    api_key: str,
    use_cache: bool = True,
) -> IdentityResult:
    """Resolve museum identity using Google Places API.

    This is the core identity resolution function. It:
    1. Searches Google Places for the museum
    2. Gets Place Details with address_components
    3. Extracts city from locality (not from formatted_address parsing!)
    4. Returns structured identity data or flags the record

    Args:
        museum_name: Name of the museum
        state_province: State/province name or code
        website: Optional website URL (helps disambiguation)
        api_key: Google Maps API key
        use_cache: Whether to use cached results

    Returns:
        IdentityResult with resolved identity or error
    """
    result = IdentityResult(
        museum_id="",  # Will be set by caller
        success=False,
        resolved_at=now_utc_iso(),
    )

    # Check cache first
    key = cache_key(museum_name, state_province)
    cache_path = CACHE_DIR / f"{key}.json"

    if use_cache and cache_path.exists():
        try:
            cached = load_json(cache_path)
            # Return cached result
            return IdentityResult(
                museum_id=cached.get("museum_id", ""),
                success=cached.get("success", False),
                city=cached.get("city"),
                street_address=cached.get("street_address"),
                postal_code=cached.get("postal_code"),
                latitude=cached.get("latitude"),
                longitude=cached.get("longitude"),
                place_id=cached.get("place_id"),
                state_from_google=cached.get("state_from_google"),
                error=cached.get("error"),
                source=cached.get("source", "google_places"),
                resolved_at=cached.get("resolved_at"),
                notes=cached.get("notes", []),
            )
        except Exception:
            pass  # Cache miss, continue with API call

    if not HAS_GOOGLE_MAPS:
        result.error = "googlemaps library not installed"
        result.notes.append("Install with: pip install googlemaps")
        return result

    try:
        gmaps = googlemaps.Client(key=api_key)

        # Build search query - include state to improve accuracy
        query = f"{museum_name}, {state_province}"
        result.notes.append(f"Search query: {query}")

        # Step 1: Text Search to find the place
        search_result = gmaps.places(query=query)

        if not search_result.get("results"):
            result.error = "No results from Google Places search"
            result.notes.append("Consider checking museum name spelling")
            _cache_result(cache_path, result)
            return result

        # Take first result (most relevant)
        place = search_result["results"][0]
        place_id = place.get("place_id")

        if not place_id:
            result.error = "No place_id in search result"
            _cache_result(cache_path, result)
            return result

        result.place_id = place_id
        result.notes.append(f"Found place_id: {place_id}")

        # Get basic location from search result
        geometry = place.get("geometry", {}).get("location", {})
        result.latitude = geometry.get("lat")
        result.longitude = geometry.get("lng")
        result.street_address = place.get("formatted_address")

        # Step 2: Place Details to get address_components
        # This is the KEY step that the old code was missing!
        details = gmaps.place(
            place_id=place_id,
            fields=["address_component", "formatted_address", "geometry"]
        )

        if not details.get("result"):
            result.error = "No details returned for place_id"
            _cache_result(cache_path, result)
            return result

        detail_result = details["result"]
        address_components = detail_result.get("address_components", [])

        if not address_components:
            result.error = "No address_components in Place Details"
            result.notes.append("Place exists but has no structured address")
            _cache_result(cache_path, result)
            return result

        # Step 3: Extract city from address_components (THE FIX!)
        city = extract_city_from_components(address_components)

        if not city:
            result.error = "Could not extract city from address_components"
            result.notes.append(f"Available types: {[c.get('types') for c in address_components]}")
            _cache_result(cache_path, result)
            return result

        result.city = city
        result.notes.append(f"Extracted city: {city}")

        # Extract state for validation
        state_from_google = extract_state_from_components(address_components)
        result.state_from_google = state_from_google

        # Validate state matches (warn if mismatch)
        if state_from_google:
            expected_state = state_province.upper()[:2] if len(state_province) >= 2 else state_province.upper()
            if state_from_google.upper() != expected_state:
                result.notes.append(f"WARNING: State mismatch - expected {expected_state}, got {state_from_google}")

        # Extract postal code
        postal_code = extract_postal_code_from_components(address_components)
        if postal_code:
            result.postal_code = postal_code

        # Update street_address from details if available
        if detail_result.get("formatted_address"):
            result.street_address = detail_result["formatted_address"]

        # Success!
        result.success = True
        result.notes.append("Identity resolution successful")

    except Exception as e:
        result.error = f"API error: {str(e)[:200]}"
        result.notes.append("Check API key and quota")

    # Cache the result
    _cache_result(cache_path, result)

    return result


def _cache_result(cache_path: Path, result: IdentityResult) -> None:
    """Cache identity result to disk."""
    try:
        cache_data = {
            "museum_id": result.museum_id,
            "success": result.success,
            "city": result.city,
            "street_address": result.street_address,
            "postal_code": result.postal_code,
            "latitude": result.latitude,
            "longitude": result.longitude,
            "place_id": result.place_id,
            "state_from_google": result.state_from_google,
            "error": result.error,
            "source": result.source,
            "resolved_at": result.resolved_at,
            "notes": result.notes,
        }
        save_json(cache_path, cache_data)
    except Exception:
        pass  # Cache write failure is non-fatal


def should_resolve(museum: dict, *, force: bool = False) -> bool:
    """Determine if a museum needs identity resolution.

    Returns True if:
    - force=True (always re-resolve)
    - city is missing or placeholder
    - city looks like a state name (the bug we're fixing!)
    """
    if force:
        return True

    city = museum.get("city")

    # Missing city
    if not city or city.strip() == "":
        return True

    # Placeholder values
    placeholders = {"unknown", "tbd", "n/a", "null", "pending"}
    if city.strip().lower() in placeholders:
        return True

    # City looks like a state name (the bug!)
    state_names = {
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming"
    }
    if city.strip() in state_names:
        return True

    # Existing city looks valid
    return False


def process_museum(
    museum: dict,
    state_code: str,
    *,
    api_key: str,
    force: bool = False,
    dry_run: bool = False,
    use_cache: bool = True,
) -> IdentityResult:
    """Process a single museum for identity resolution.

    Args:
        museum: Museum record from state file
        state_code: Two-letter state code
        api_key: Google Maps API key
        force: Force re-resolution even if city exists
        dry_run: If True, don't write changes
        use_cache: Use cached Google Places results

    Returns:
        IdentityResult with resolution outcome
    """
    museum_id = museum.get("museum_id", "")
    museum_name = museum.get("museum_name", "")
    state_province = museum.get("state_province", state_code)
    website = museum.get("website")

    # Check if resolution needed
    if not should_resolve(museum, force=force):
        return IdentityResult(
            museum_id=museum_id,
            success=True,
            city=museum.get("city"),
            notes=["Skipped: city already valid"],
        )

    # Resolve identity
    result = resolve_identity_google_places(
        museum_name=museum_name,
        state_province=state_province,
        website=website,
        api_key=api_key,
        use_cache=use_cache,
    )
    result.museum_id = museum_id

    return result


def process_state(
    state_code: str,
    *,
    api_key: str,
    force: bool = False,
    dry_run: bool = False,
    use_cache: bool = True,
    museum_id_filter: Optional[str] = None,
) -> Phase0Stats:
    """Process all museums in a state for identity resolution.

    Args:
        state_code: Two-letter state code (e.g., "CO")
        api_key: Google Maps API key
        force: Force re-resolution for all museums
        dry_run: If True, don't write changes
        use_cache: Use cached Google Places results
        museum_id_filter: If set, only process this museum_id

    Returns:
        Phase0Stats with processing statistics
    """
    stats = Phase0Stats()

    state_file = STATES_DIR / f"{state_code}.json"
    if not state_file.exists():
        print(f"ERROR: State file not found: {state_file}")
        return stats

    state_data = load_json(state_file)
    museums = state_data.get("museums", [])
    total = len(museums)

    print(f"\n[STATE: {state_code}] Processing {total} museums")

    changes_made = False

    for idx, museum in enumerate(museums, 1):
        museum_id = museum.get("museum_id", "")

        # Filter if specific museum requested
        if museum_id_filter and museum_id != museum_id_filter:
            continue

        stats.total_processed += 1

        # Check if resolution needed
        if not should_resolve(museum, force=force):
            stats.skipped += 1
            print(f"  [{idx}/{total}] {museum_id} - SKIPPED (city valid)")
            continue

        print(f"  [{idx}/{total}] {museum_id}...", end=" ", flush=True)

        # Add small delay to respect API rate limits
        time.sleep(0.2)

        result = process_museum(
            museum=museum,
            state_code=state_code,
            api_key=api_key,
            force=force,
            dry_run=dry_run,
            use_cache=use_cache,
        )

        if result.success and result.city:
            stats.successful += 1
            print(f"OK city={result.city}")

            if not dry_run:
                # Apply patch to museum record
                patch = result.to_patch()
                for key, value in patch.items():
                    museum[key] = value

                # Update provenance
                museum["address_source"] = "google_places"
                museum["address_last_verified"] = now_utc_iso()[:10]

                # Add to data_sources if not present
                sources = museum.get("data_sources", [])
                if "google_places_api" not in sources:
                    sources.append("google_places_api")
                    museum["data_sources"] = sources

                # Update timestamp
                museum["updated_at"] = now_utc_iso()

                changes_made = True
        else:
            stats.failed += 1
            stats.flagged.append(museum_id)
            print(f"FAILED ({result.error})")

            # Log details for debugging
            if result.notes:
                for note in result.notes:
                    print(f"      {note}")

    # Save state file if changes were made
    if changes_made and not dry_run:
        state_data["updated_at"] = now_utc_iso()
        save_json(state_file, state_data)
        print(f"\n  Saved changes to {state_file}")

    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 0: Canonical Identity Resolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Scope selection
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Process all states")
    scope.add_argument("--museum-id", help="Process single museum by ID")

    # Options
    parser.add_argument("--force", action="store_true", help="Force re-resolution even if city exists")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--no-cache", action="store_true", help="Don't use cached results")

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_MAPS_API_KEY environment variable not set")
        print("Set it with: export GOOGLE_MAPS_API_KEY=your_key_here")
        return 1

    if not HAS_GOOGLE_MAPS:
        print("ERROR: googlemaps library not installed")
        print("Install with: pip install googlemaps")
        return 1

    # Determine state codes to process
    state_codes: list[str] = []
    museum_id_filter: Optional[str] = None

    if args.museum_id:
        # Extract state from museum_id (format: usa-{state}-city-name)
        parts = args.museum_id.split("-")
        if len(parts) >= 2:
            state_codes = [parts[1].upper()]
            museum_id_filter = args.museum_id
        else:
            print(f"ERROR: Invalid museum_id format: {args.museum_id}")
            return 1
    elif args.all_states:
        state_codes = sorted([
            p.stem.upper() for p in STATES_DIR.glob("*.json")
            if len(p.stem) == 2 and p.stem.isalpha()
        ])
    elif args.states:
        state_codes = [s.strip().upper() for s in args.states.split(",")]
    elif args.state:
        state_codes = [args.state.upper()]

    # Create cache directory
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Create run directory for logging
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"phase0-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 0: Canonical Identity Resolution")
    print("=" * 60)
    print(f"States: {', '.join(state_codes)}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Use cache: {not args.no_cache}")
    print(f"Run ID: {run_id}")
    print("=" * 60)

    # Process each state
    total_stats = Phase0Stats()
    all_flagged: list[dict] = []

    for state_code in state_codes:
        stats = process_state(
            state_code=state_code,
            api_key=api_key,
            force=args.force,
            dry_run=args.dry_run,
            use_cache=not args.no_cache,
            museum_id_filter=museum_id_filter,
        )

        total_stats.total_processed += stats.total_processed
        total_stats.successful += stats.successful
        total_stats.failed += stats.failed
        total_stats.skipped += stats.skipped

        for mid in stats.flagged:
            all_flagged.append({"state": state_code, "museum_id": mid})

    # Save run summary
    summary = {
        "run_id": run_id,
        "states": state_codes,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "successful": total_stats.successful,
        "failed": total_stats.failed,
        "skipped": total_stats.skipped,
        "flagged_museums": all_flagged,
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)

    # Print summary
    print("\n" + "=" * 60)
    print("Phase 0 Complete")
    print("=" * 60)
    print(f"  Total processed: {total_stats.total_processed}")
    print(f"  Successful:      {total_stats.successful}")
    print(f"  Failed:          {total_stats.failed}")
    print(f"  Skipped:         {total_stats.skipped}")

    if all_flagged:
        print(f"\n  FLAGGED MUSEUMS ({len(all_flagged)}):")
        for item in all_flagged[:10]:  # Show first 10
            print(f"    - {item['state']}: {item['museum_id']}")
        if len(all_flagged) > 10:
            print(f"    ... and {len(all_flagged) - 10} more")
        print(f"\n  Full list saved to: {run_dir / 'summary.json'}")

    print(f"\n  Run directory: {run_dir}")
    print("=" * 60)

    return 0 if total_stats.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
