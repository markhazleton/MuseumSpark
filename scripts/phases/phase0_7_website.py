#!/usr/bin/env python3
"""Phase 0.7: Website Content Extraction for Scoring (MRD v2).

This module extracts content from museum websites that is:
1. NOT available from Google Places API
2. Valuable for downstream Phase 2 LLM scoring
3. Clean markdown format (no HTML tags)

Data Extracted:
    - Meta description (richer than Google editorial summary)
    - Visitor information URLs (hours/tickets/accessibility pages)
    - Detailed hours text (seasonal variations, special closures)
    - Admission pricing information
    - Accessibility features (elevators, wheelchairs, audio guides)
    - Collections/exhibitions highlights

What This Does NOT Extract (already from Google Places):
    - Basic street address
    - Coordinates
    - Phone numbers
    - Basic business hours
    - Reviews/ratings

Design Principles:
    1. CLEAN OUTPUT: All HTML converted to clean markdown
    2. SCORING-FOCUSED: Only extract content useful for reputation/quality assessment
    3. CACHED: Store extracted content in museum cache directory
    4. IDEMPOTENT: Skip museums with existing cache (unless --force)
    5. RESPECTFUL: Honor robots.txt, rate limit requests

Usage:
    # Extract website content for a state
    python scripts/phases/phase0_7_website.py --state CO

    # Process all states
    python scripts/phases/phase0_7_website.py --all-states

    # Force re-fetch even if cached
    python scripts/phases/phase0_7_website.py --state CO --force

    # Dry run (show what would be fetched)
    python scripts/phases/phase0_7_website.py --state CO --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("WARNING: BeautifulSoup4 not installed. Install with: pip install beautifulsoup4")

# html2text for clean markdown conversion
try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False
    print("WARNING: html2text not installed. Install with: pip install html2text")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"
HTTP_CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "http"

# Rate limiting: be respectful to museum websites
REQUEST_DELAY_SECONDS = 2.0

# User-Agent for web requests (specific bot name to allow targeted robots.txt rules)
USER_AGENT = "MuseumSpark-Bot/1.0 (+https://github.com/MarkHazleton/MuseumSpark; museum-research)"

# Wayback Machine API endpoint
WAYBACK_API = "https://archive.org/wayback/available"


@dataclass
class WebsiteContent:
    """Extracted website content."""
    meta_description: Optional[str] = None
    hours_url: Optional[str] = None
    tickets_url: Optional[str] = None
    accessibility_url: Optional[str] = None
    hours_text: Optional[str] = None
    admission_text: Optional[str] = None
    accessibility_text: Optional[str] = None
    collections_text: Optional[str] = None
    from_wayback: bool = False  # True if content came from Wayback Machine
    error: Optional[str] = None


@dataclass
class Phase0_7Stats:
    """Statistics for a Phase 0.7 run."""
    total_processed: int = 0
    content_extracted: int = 0
    no_website: int = 0
    robots_blocked: int = 0
    skipped_cached: int = 0
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


def get_museum_cache_dir(state_code: str, museum_id: str) -> Path:
    """Get the cache directory for a museum."""
    # Use hash-based directory structure to avoid filesystem limits
    hash_bytes = hashlib.sha256(museum_id.encode("utf-8")).hexdigest()
    folder_hash = f"m_{hash_bytes[:8]}"
    return STATES_DIR / state_code / folder_hash / "cache"


def get_http_cache_path(url: str) -> Path:
    """Get cache path for a URL."""
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return HTTP_CACHE_DIR / f"{url_hash[:16]}.html"


def check_robots_txt(url: str) -> bool:
    """Check if URL is allowed by robots.txt for MuseumSpark-Bot.
    
    Returns True if allowed, False if blocked.
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        # Check with our specific bot name
        return rp.can_fetch("MuseumSpark-Bot", url)
    except Exception:
        # If we can't read robots.txt, assume allowed
        return True


def fetch_from_wayback(url: str) -> tuple[Optional[str], Optional[str]]:
    """Fetch URL from Wayback Machine (archive.org).
    
    Returns:
        Tuple of (html_content, error_message)
    """
    try:
        # Query Wayback Machine availability API
        api_url = f"{WAYBACK_API}?url={urllib.parse.quote(url)}"
        headers = {"User-Agent": USER_AGENT}
        
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        # Check if archived snapshot exists
        archived_snapshots = data.get("archived_snapshots", {})
        closest = archived_snapshots.get("closest", {})
        
        if not closest or not closest.get("available"):
            return None, "No Wayback Machine snapshot available"
        
        # Get the archived URL
        archived_url = closest.get("url")
        if not archived_url:
            return None, "No Wayback Machine URL found"
        
        # Fetch the archived page
        req = urllib.request.Request(archived_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="ignore")
        
        return html, None
        
    except Exception as e:
        return None, f"Wayback Machine error: {str(e)}"


def fetch_html(url: str, use_cache: bool = True) -> tuple[Optional[str], Optional[str]]:
    """Fetch HTML from URL with caching and Wayback Machine fallback.
    
    If blocked by robots.txt, automatically falls back to Wayback Machine.
    
    Returns:
        Tuple of (html_content, error_message)
    """
    # Check cache first
    cache_path = get_http_cache_path(url)
    if use_cache and cache_path.exists():
        try:
            return cache_path.read_text(encoding="utf-8"), None
        except Exception:
            pass  # Cache corrupted, refetch
    
    # Check robots.txt
    robots_allowed = check_robots_txt(url)
    
    if robots_allowed:
        # Fetch URL directly
        headers = {"User-Agent": USER_AGENT}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode("utf-8", errors="ignore")
                
                # Cache the response
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(html, encoding="utf-8")
                
                return html, None
        except urllib.error.HTTPError as e:
            # Try Wayback Machine as fallback for HTTP errors too
            html, wayback_error = fetch_from_wayback(url)
            if html:
                # Cache the Wayback Machine response
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(html, encoding="utf-8")
                return html, None
            return None, f"HTTP {e.code} (Wayback fallback failed: {wayback_error})"
        except urllib.error.URLError as e:
            return None, f"Connection error: {e.reason}"
        except Exception as e:
            return None, f"Error: {str(e)}"
    else:
        # Blocked by robots.txt - try Wayback Machine
        html, wayback_error = fetch_from_wayback(url)
        if html:
            # Cache the Wayback Machine response
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(html, encoding="utf-8")
            return html, None
        return None, f"Blocked by robots.txt (Wayback fallback: {wayback_error})"


def html_to_clean_markdown(html: str, max_length: int = 2000) -> str:
    """Convert HTML to clean markdown text.
    
    Removes navigation, ads, and other clutter.
    """
    if not HAS_HTML2TEXT or not HAS_BS4:
        # Fallback: simple tag stripping
        soup = BeautifulSoup(html, "html.parser") if HAS_BS4 else None
        if soup:
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            text = soup.get_text(separator="\n", strip=True)
        else:
            text = re.sub(r'<[^>]+>', '', html)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = text.strip()
        
        # Truncate
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    
    # Use html2text for proper markdown conversion
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove clutter elements
    for element in soup(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
        element.decompose()
    
    # Convert to markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap
    
    markdown = h.handle(str(soup))
    
    # Clean up excessive whitespace
    markdown = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown)
    markdown = markdown.strip()
    
    # Truncate if too long
    if len(markdown) > max_length:
        markdown = markdown[:max_length] + "..."
    
    return markdown


def extract_meta_description(html: str) -> Optional[str]:
    """Extract meta description from HTML head."""
    if not HAS_BS4:
        return None
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Try og:description first (often richer)
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"].strip()
        
        # Try standard meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"].strip()
        
        # Try Twitter description
        twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
        if twitter_desc and twitter_desc.get("content"):
            return twitter_desc["content"].strip()
        
    except Exception:
        pass
    
    return None


def find_visitor_urls(html: str, base_url: str) -> dict[str, Optional[str]]:
    """Find URLs for visitor information pages.
    
    Returns dict with keys: hours_url, tickets_url, accessibility_url
    """
    if not HAS_BS4:
        return {"hours_url": None, "tickets_url": None, "accessibility_url": None}
    
    result = {"hours_url": None, "tickets_url": None, "accessibility_url": None}
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Find all links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True).lower()
            href_lower = href.lower()
            
            # Hours/visit links
            if not result["hours_url"]:
                if any(kw in text for kw in ["hours", "visit", "plan your visit", "plan visit"]) or \
                   any(kw in href_lower for kw in ["/visit", "/hours", "/plan"]):
                    result["hours_url"] = urljoin(base_url, href)
            
            # Tickets/admission links
            if not result["tickets_url"]:
                if any(kw in text for kw in ["tickets", "admission", "pricing", "membership"]) or \
                   any(kw in href_lower for kw in ["/tickets", "/admission", "/visit"]):
                    result["tickets_url"] = urljoin(base_url, href)
            
            # Accessibility links
            if not result["accessibility_url"]:
                if any(kw in text for kw in ["accessibility", "accessible", "ada"]) or \
                   any(kw in href_lower for kw in ["/accessibility", "/accessible"]):
                    result["accessibility_url"] = urljoin(base_url, href)
        
    except Exception:
        pass
    
    return result


def extract_content_from_page(html: str, content_type: str) -> Optional[str]:
    """Extract relevant content from a specialized page.
    
    Args:
        html: HTML content
        content_type: One of 'hours', 'admission', 'accessibility', 'collections'
    
    Returns:
        Clean markdown text with relevant content
    """
    if not HAS_BS4:
        return None
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove clutter
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Find main content area (common selectors)
        main_content = None
        for selector in ["main", "article", ".content", "#content", ".main", "#main"]:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find("body")
        
        if not main_content:
            return None
        
        # Look for sections matching the content type
        keywords = {
            "hours": ["hours", "open", "schedule", "when to visit"],
            "admission": ["admission", "tickets", "pricing", "fees", "cost"],
            "accessibility": ["accessibility", "accessible", "ada", "wheelchair"],
            "collections": ["collection", "exhibitions", "galleries", "permanent"]
        }
        
        target_keywords = keywords.get(content_type, [])
        relevant_sections = []
        
        # Find sections with relevant keywords
        for section in main_content.find_all(["section", "div", "article"]):
            section_text = section.get_text().lower()
            if any(kw in section_text for kw in target_keywords):
                relevant_sections.append(section)
        
        # If we found specific sections, use those
        if relevant_sections:
            combined_html = "".join(str(section) for section in relevant_sections[:3])  # Max 3 sections
            return html_to_clean_markdown(combined_html, max_length=1500)
        
        # Fallback: convert entire main content
        return html_to_clean_markdown(str(main_content), max_length=1500)
        
    except Exception:
        return None


def extract_website_content(
    website: str,
    *,
    force: bool = False
) -> WebsiteContent:
    """Extract content from museum website.
    
    Args:
        website: Museum website URL
        force: Force re-fetch even if cached
        
    Returns:
        WebsiteContent with extracted data
    """
    result = WebsiteContent()
    
    if not website or not website.startswith("http"):
        result.error = "Invalid website URL"
        return result
    
    # Rate limit
    time.sleep(REQUEST_DELAY_SECONDS)
    
    # Fetch homepage
    html, error = fetch_html(website, use_cache=not force)
    
    # Check if we got content from Wayback Machine
    if html and error and "Wayback" not in error:
        result.error = error
        return result
    elif html:
        # Successfully got content (either direct or from Wayback)
        if error and "Wayback" in error:
            result.from_wayback = True
    else:
        result.error = error if error else "Empty response"
        return result
    
    # Extract meta description
    result.meta_description = extract_meta_description(html)
    
    # Find visitor URLs
    visitor_urls = find_visitor_urls(html, website)
    result.hours_url = visitor_urls["hours_url"]
    result.tickets_url = visitor_urls["tickets_url"]
    result.accessibility_url = visitor_urls["accessibility_url"]
    
    # Fetch and extract from dedicated pages
    if result.hours_url and result.hours_url != website:
        time.sleep(REQUEST_DELAY_SECONDS)
        hours_html, _ = fetch_html(result.hours_url, use_cache=not force)
        if hours_html:
            result.hours_text = extract_content_from_page(hours_html, "hours")
    
    if result.tickets_url and result.tickets_url != website:
        time.sleep(REQUEST_DELAY_SECONDS)
        admission_html, _ = fetch_html(result.tickets_url, use_cache=not force)
        if admission_html:
            result.admission_text = extract_content_from_page(admission_html, "admission")
    
    if result.accessibility_url and result.accessibility_url != website:
        time.sleep(REQUEST_DELAY_SECONDS)
        access_html, _ = fetch_html(result.accessibility_url, use_cache=not force)
        if access_html:
            result.accessibility_text = extract_content_from_page(access_html, "accessibility")
    
    # Try to extract collections info from homepage
    result.collections_text = extract_content_from_page(html, "collections")
    
    return result


def process_museum(
    museum: dict,
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[bool, Optional[WebsiteContent]]:
    """Process a single museum for website content extraction.
    
    Args:
        museum: Museum record
        state_code: Two-letter state code
        force: Force re-fetch even if cached
        dry_run: Don't actually save
        
    Returns:
        Tuple of (was_processed, WebsiteContent or None)
    """
    museum_id = museum.get("museum_id", "")
    museum_name = museum.get("museum_name", "")
    website = museum.get("website", "")
    
    if not website:
        return False, None  # No website to scrape
    
    # Check cache
    cache_dir = get_museum_cache_dir(state_code, museum_id)
    cache_file = cache_dir / "website_content.json"
    
    if not force and cache_file.exists():
        return False, None  # Already cached
    
    if dry_run:
        print(f"    [DRY RUN] Would fetch: {website}")
        return True, None
    
    # Extract content
    content = extract_website_content(website, force=force)
    
    # Save to cache
    cache_data = {
        "website": website,
        "meta_description": content.meta_description,
        "hours_url": content.hours_url,
        "tickets_url": content.tickets_url,
        "accessibility_url": content.accessibility_url,
        "hours_text": content.hours_text,
        "admission_text": content.admission_text,
        "accessibility_text": content.accessibility_text,
        "collections_text": content.collections_text,
        "from_wayback": content.from_wayback,
        "error": content.error,
        "fetched_at": now_utc_iso(),
    }
    save_json(cache_file, cache_data)
    
    return True, content


def process_state(
    state_code: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Phase0_7Stats:
    """Process all museums in a state for website content extraction.
    
    Args:
        state_code: Two-letter state code
        force: Force re-fetch even if cached
        dry_run: If True, don't make changes
        
    Returns:
        Phase0_7Stats with processing statistics
    """
    stats = Phase0_7Stats()
    
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
        website = museum.get("website", "")
        stats.total_processed += 1
        
        if not website:
            stats.no_website += 1
            continue
        
        print(f"  [{idx}/{total}] {museum_name[:50]}")
        
        was_processed, content = process_museum(
            museum=museum,
            state_code=state_code,
            force=force,
            dry_run=dry_run,
        )
        
        if not was_processed:
            stats.skipped_cached += 1
            print(f"           SKIPPED (already cached)")
            continue
        
        if content is None:
            # Dry run
            continue
        
        if content.error:
            if "robots.txt" in content.error:
                stats.robots_blocked += 1
            else:
                stats.errors += 1
            print(f"           ERROR - {content.error}")
        else:
            stats.content_extracted += 1
            extracted = []
            if content.meta_description:
                extracted.append("meta")
            if content.hours_text:
                extracted.append("hours")
            if content.admission_text:
                extracted.append("admission")
            if content.accessibility_text:
                extracted.append("accessibility")
            source = " (from Wayback Machine)" if content.from_wayback else ""
            print(f"           OK - Extracted: {', '.join(extracted) if extracted else 'URLs only'}{source}")
    
    return stats


def main() -> int:
    """Main entry point."""
    if not HAS_BS4:
        print("ERROR: BeautifulSoup4 is required. Install with: pip install beautifulsoup4")
        return 1
    
    parser = argparse.ArgumentParser(
        description="Phase 0.7: Website Content Extraction for Scoring",
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
    run_dir = RUNS_DIR / f"phase0_7-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Phase 0.7: Website Content Extraction for Scoring")
    print("=" * 60)
    print(f"States: {', '.join(state_codes)}")
    print(f"Force: {args.force}")
    print(f"Dry run: {args.dry_run}")
    print(f"Run ID: {run_id}")
    print("=" * 60)
    
    # Process each state
    total_stats = Phase0_7Stats()
    
    for state_code in state_codes:
        stats = process_state(
            state_code=state_code,
            force=args.force,
            dry_run=args.dry_run,
        )
        
        total_stats.total_processed += stats.total_processed
        total_stats.content_extracted += stats.content_extracted
        total_stats.no_website += stats.no_website
        total_stats.robots_blocked += stats.robots_blocked
        total_stats.skipped_cached += stats.skipped_cached
        total_stats.errors += stats.errors
    
    # Save run summary
    summary = {
        "run_id": run_id,
        "states": state_codes,
        "force": args.force,
        "dry_run": args.dry_run,
        "total_processed": total_stats.total_processed,
        "content_extracted": total_stats.content_extracted,
        "no_website": total_stats.no_website,
        "robots_blocked": total_stats.robots_blocked,
        "skipped_cached": total_stats.skipped_cached,
        "errors": total_stats.errors,
        "completed_at": now_utc_iso(),
    }
    save_json(run_dir / "summary.json", summary)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Phase 0.7 Complete")
    print("=" * 60)
    print(f"  Total processed:      {total_stats.total_processed}")
    print(f"  Content extracted:    {total_stats.content_extracted}")
    print(f"  No website:           {total_stats.no_website}")
    print(f"  Blocked by robots:    {total_stats.robots_blocked}")
    print(f"  Skipped (cached):     {total_stats.skipped_cached}")
    print(f"  Errors:               {total_stats.errors}")
    print(f"\n  Run directory: {run_dir}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
