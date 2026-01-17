"""Build compact evidence packets for LLM calls."""

from __future__ import annotations

import json
import re
from typing import Any

try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False

from .context import MuseumContext
from .utils import compact_dict, estimate_tokens, truncate_text


def _html_to_markdown(value: str) -> str:
    """Convert HTML to clean markdown text."""
    if not value:
        return ""
    
    # Remove noise sections first
    text = re.sub(r"<(script|style|svg|noscript)[^>]*>.*?</\1>", " ", value, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<(nav|header|footer|aside)[^>]*>.*?</\1>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    
    if HAS_HTML2TEXT:
        # Use html2text library for clean conversion
        h = html2text.HTML2Text()
        h.ignore_links = False  # Keep links for context
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap text
        h.unicode_snob = True
        h.skip_internal_links = True
        markdown = h.handle(text)
    else:
        # Fallback: basic tag stripping
        markdown = re.sub(r"<[^>]+>", " ", text)
    
    # Remove common boilerplate phrases
    noise_patterns = [
        r"accept.*?cookies?",
        r"privacy policy",
        r"terms of service",
        r"newsletter signup",
        r"follow us on",
        r"share this page",
        r"click here",
        r"read more",
        r"skip to content",
        r"accessibility",
    ]
    for pattern in noise_patterns:
        markdown = re.sub(pattern, " ", markdown, flags=re.IGNORECASE)
    
    # Clean up excessive whitespace and blank lines
    markdown = re.sub(r"\n\s*\n\s*\n+", "\n\n", markdown)
    markdown = re.sub(r"[ \t]+", " ", markdown)
    
    # Remove lines that are too short (likely navigation)
    lines = []
    for line in markdown.split("\n"):
        stripped = line.strip()
        # Keep markdown headers, list items, or lines with substantial content
        if stripped.startswith("#") or stripped.startswith("*") or stripped.startswith("-") or len(stripped) > 20:
            lines.append(line)
    
    return "\n".join(lines).strip()


def _strip_html(value: str) -> str:
    """Legacy fallback - strips HTML tags without markdown conversion."""
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _safe_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def build_evidence_packet(
    context: MuseumContext,
    *,
    max_chars: int = 8000,
    max_json_fields: int = 30,
) -> dict[str, Any]:
    record = context.state_record or {}
    cached = context.cached_data

    # Skip wikidata entity overhead, keep only claims for collection info
    wikidata_claims = compact_dict((cached.wikidata_claims or {}).get("claims", {}), max_json_fields)

    wikipedia_summary = truncate_text(cached.wikipedia_summary, 1200)
    website_json_ld = compact_dict(cached.website_json_ld or {}, max_json_fields)
    website_text = None
    if cached.website_html:
        website_text = truncate_text(_html_to_markdown(cached.website_html), 1200)

    packet = {
        "identity": {
            "museum_id": context.museum_id,
            "museum_name": context.museum_name,
            "city": context.city,
            "state_province": context.state_province,
            "country": context.country,
            "website": record.get("website"),
            "primary_domain": record.get("primary_domain"),
        },
        "state_record_subset": {
            "museum_type": record.get("museum_type"),
            "audience_focus": record.get("audience_focus"),
            "city_tier": record.get("city_tier"),
            "reputation": record.get("reputation"),
            "collection_tier": record.get("collection_tier"),
            "time_needed": record.get("time_needed"),
            "notes": record.get("notes"),
        },
        "wikidata_claims": wikidata_claims,
        "wikipedia_summary": wikipedia_summary,
        "website_json_ld": website_json_ld,
        "website_text_snippet": website_text,
        "subpages_scraped": (cached.subpages_scraped or [])[:3],
    }

    serialized = _safe_json(packet)
    if len(serialized) > max_chars:
        # Trim large text fields deterministically.
        if packet.get("wikipedia_summary"):
            packet["wikipedia_summary"] = truncate_text(packet["wikipedia_summary"], 600)
        if packet.get("website_text_snippet"):
            packet["website_text_snippet"] = truncate_text(packet["website_text_snippet"], 600)
        serialized = _safe_json(packet)
        if len(serialized) > max_chars:
            packet["wikidata_claims"] = compact_dict(packet["wikidata_claims"], 15) or {}

    packet["packet_metadata"] = {
        "approx_tokens": estimate_tokens(serialized),
        "max_chars": max_chars,
    }
    return packet

