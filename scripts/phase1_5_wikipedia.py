#!/usr/bin/env python3
"""Phase 1.5: Wikipedia Enrichment for Art Museums (MRD v2).

This module fetches Wikipedia data for art museums only to build
a curated evidence packet for Phase 2 LLM scoring.

IMPORTANT: Only processes museums where is_scoreable=True (art museums).
Non-art museums are skipped entirely.

Data Fetched:
    - Wikipedia URL (if found)
    - Wikipedia extract (first paragraph summary)
    - Notable artists mentioned
    - Collection highlights
    - Historical founding information

Design Principles:
    1. ART MUSEUMS ONLY: Skip non-art museums (is_scoreable=False)
    2. RATE LIMITED: Respect Wikipedia API limits (polite delay)
    3. CACHED: Store Wikipedia data in museum folder cache
    4. IDEMPOTENT: Skip museums that already have Wikipedia data (unless --force)

Usage:
    # Enrich art museums in a state with Wikipedia data
    python scripts/phase1_5_wikipedia.py --state CO

    # Process all states
    python scripts/phase1_5_wikipedia.py --all-states

    # Force re-fetch even if already cached
    python scripts/phase1_5_wikipedia.py --state CO --force

    # Dry run (show what would be fetched)
    python scripts/phase1_5_wikipedia.py --state CO --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

# Wikipedia API endpoint
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

# Rate limiting: be polite to Wikipedia
REQUEST_DELAY_SECONDS = 0.5


@dataclass
class WikipediaResult:
    """Result of a Wikipedia lookup."""
    found: bool = False
    page_title: Optional[str] = None
    page_url: Optional[str] = None
    extract: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Phase1_5Stats:
    """Statistics for a Phase 1.5 run."""
    total_processed: int = 0
    wikipedia_found: int = 0
    wikipedia_not_found: int = 0
    skipped_not_art: int = 0
    skipped_already_cached: int = 0
    errors: int = 0


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


def search_wikipedia(query: str) -> WikipediaResult:
    """Search Wikipedia for a museum and return the best match.

    Args:
        query: Search query (museum name + city)

    Returns:
        WikipediaResult with page info or error
    """
    result = WikipediaResult()

    # User-Agent required by Wikipedia API policy
    headers = {
        "User-Agent": "MuseumSpark/1.0 (https://github.com/MarkHazleton/MuseumSpark; museum-enrichment-bot)"
    }

    try:
        # Step 1: Search for the page
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": "3",
            "format": "json",
        }
        search_url = f"{WIKIPEDIA_API_URL}?{urllib.parse.urlencode(search_params)}"

        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            search_data = json.loads(response.read().decode("utf-8"))

        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            result.found = False
            result.error = "No Wikipedia page found"
            return result

        # Take the first result
        page_title = search_results[0]["title"]

        # Step 2: Get the page extract
        extract_params = {
            "action": "query",
            "titles": page_title,
            "prop": "extracts|info",
            "exintro": "true",
            "explaintext": "true",
            "exsectionformat": "plain",
            "inprop": "url",
            "format": "json",
        }
        extract_url = f"{WIKIPEDIA_API_URL}?{urllib.parse.urlencode(extract_params)}"

        req = urllib.request.Request(extract_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            extract_data = json.loads(response.read().decode("utf-8"))

        pages = extract_data.get("query", {}).get("pages", {})
        if not pages:
            result.found = False
            result.error = "Page not found"
            return result

        # Get the first (and only) page
        page = list(pages.values())[0]

        if page.get("missing") is not None:
            result.found = False
            result.error = "Page missing"
            return result

        result.found = True
        result.page_title = page.get("title")
        result.page_url = page.get("fullurl")
        result.extract = page.get("extract", "")

        # Clean up extract (remove excessive whitespace)
        if result.extract:
            result.extract = re.sub(r'\s+', ' ', result.extract).strip()
            # Limit to first 2000 characters for storage
            if len(result.extract) > 2000:
                result.extract = result.extract[:2000] + "..."

        return result

    except urllib.error.URLError as e:
        result.found = False
        result.error = f"Network error: {e}"
        return result
    except json.JSONDecodeError as e:
        result.found = False
        result.error = f"JSON parse error: {e}"
        return result
    except Exception as e:
        result.found = False
        result.error = f"Error: {e}"
        return result


def get_museum_cache_dir(state_code: str, museum_id: str) -> Path:
    """Get the cache directory for a museum."""
    return STATES_DIR / state_code / museum_id / "cache"


def process_museum(
    museum: dict,
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[bool, Optional[WikipediaResult]]:
    """Process a single museum for Wikipedia enrichment.

    Args:
        museum: Museum record
        state_code: Two-letter state code
        force: Force re-fetch even if cached
        dry_run: Don't actually save

    Returns:
        Tuple of (was_processed, WikipediaResult or None)
    """
    museum_id = museum.get("museum_id", "")
    museum_name = museum.get("museum_name", "")
    city = museum.get("city", "")

    # Check cache
    cache_dir = get_museum_cache_dir(state_code, museum_id)
    cache_file = cache_dir / "wikipedia.json"

    if not force and cache_file.exists():
        return False, None  # Already cached

    # Build search query
    search_query = f"{museum_name} {city} museum"

    if dry_run:
        print(f"    [DRY RUN] Would search: {search_query}")
        return True, None

    # Rate limit
    time.sleep(REQUEST_DELAY_SECONDS)

    # Search Wikipedia
    result = search_wikipedia(search_query)

    # Save to cache
    cache_data = {
        "search_query": search_query,
        "found": result.found,
        "page_title": result.page_title,
        "page_url": result.page_url,
        "extract": result.extract,
        "error": result.error,
        "fetched_at": now_utc_iso(),
    }
    save_json(cache_file, cache_data)

    return True, result


def process_state(
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Phase1_5Stats:
    """Process all art museums in a state for Wikipedia enrichment.

    Args:
        state_code: Two-letter state code
        force: Force re-fetch even if cached
        dry_run: If True, don't make changes

    Returns:
        Phase1_5Stats with processing statistics
    """
    stats = Phase1_5Stats()

    state_file = STATES_DIR / f"{state_code}.json"
    if not state_file.exists():
        print(f"ERROR: State file not found: {state_file}")
        return stats

    state_data = load_json(state_file)
    museums = state_data.get("museums", [])
    total = len(museums)

    print(f"\n[STATE: {state_code}] Processing {total} museums")

    for idx, museum in enumerate(museums, 1):
        museum_id = museum.get("museum_id", "")
        museum_name = museum.get("museum_name", "")
        stats.total_processed += 1

        # Only process art museums (is_scoreable=True)
        if not museum.get("is_scoreable", False):
            stats.skipped_not_art += 1
            continue

        print(f"  [{idx}/{total}] {museum_name[:50]}")

        was_processed, result = process_museum(
            museum=museum,
            state_code=state_code,
            force=force,
            dry_run=dry_run,
        )

        if not was_processed:
            stats.skipped_already_cached += 1
            print(f"           SKIPPED (already cached)")
            continue

        if result is None:
            # Dry run
            continue

        if result.found:
            stats.wikipedia_found += 1
            print(f"           OK - {result.page_title}")
        else:
            stats.wikipedia_not_found += 1
            print(f"           NOT FOUND - {result.error}")

    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 1.5: Wikipedia Enrichment for Art Museums",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Scope selection
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--state", help="Two-letter state code (e.g., CO)")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Process all states")

    # Options
    parser.add_argument("--force", action="store_true", help="Force re-fetch even if cached")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    args = parser.parse_args()

    # Determine state codes to process
    state_codes: list[str] = []

    if args.all_states:
        state_codes = sorted([
            p.stem.upper() for p in STATES_DIR.glob("*.json")
            if len(p.stem) == 2 and p.stem.isalpha()
        ])
    elif args.states:
        state_codes = [s.strip().upper() for s in args.states.split(",")]
    elif args.state:
        state_codes = [args.state.upper()]

    # Create run directory for logging
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"phase1_5-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 1.5: Wikipedia Enrichment for Art Museums")
    print("=" * 60)
    print(f"States: {', '.join(state_codes)}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Run ID: {run_id}")
    print("=" * 60)

    # Process each state
    total_stats = Phase1_5Stats()

    for state_code in state_codes:
        stats = process_state(
            state_code=state_code,
            force=args.force,
            dry_run=args.dry_run,
        )

        total_stats.total_processed += stats.total_processed
        total_stats.wikipedia_found += stats.wikipedia_found
        total_stats.wikipedia_not_found += stats.wikipedia_not_found
        total_stats.skipped_not_art += stats.skipped_not_art
        total_stats.skipped_already_cached += stats.skipped_already_cached
        total_stats.errors += stats.errors

    # Save run summary
    summary = {
        "run_id": run_id,
        "states": state_codes,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "wikipedia_found": total_stats.wikipedia_found,
        "wikipedia_not_found": total_stats.wikipedia_not_found,
        "skipped_not_art": total_stats.skipped_not_art,
        "skipped_already_cached": total_stats.skipped_already_cached,
        "errors": total_stats.errors,
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)

    # Print summary
    print("\n" + "=" * 60)
    print("Phase 1.5 Complete")
    print("=" * 60)
    print(f"  Total processed:      {total_stats.total_processed}")
    print(f"  Wikipedia found:      {total_stats.wikipedia_found}")
    print(f"  Wikipedia not found:  {total_stats.wikipedia_not_found}")
    print(f"  Skipped (not art):    {total_stats.skipped_not_art}")
    print(f"  Skipped (cached):     {total_stats.skipped_already_cached}")
    print(f"  Errors:               {total_stats.errors}")
    print(f"\n  Run directory: {run_dir}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
