"""Build compact evidence packets for LLM calls."""

from __future__ import annotations

import json
import re
from typing import Any

from .context import MuseumContext
from .utils import compact_dict, estimate_tokens, truncate_text


def _strip_html(value: str) -> str:
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

    wikidata_entity = compact_dict(cached.wikidata_entity or {}, max_json_fields)
    wikidata_claims = compact_dict((cached.wikidata_claims or {}).get("claims", {}), max_json_fields)

    wikipedia_summary = truncate_text(cached.wikipedia_summary, 1200)
    website_json_ld = compact_dict(cached.website_json_ld or {}, max_json_fields)
    website_text = None
    if cached.website_html:
        website_text = truncate_text(_strip_html(cached.website_html), 1200)

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
        "wikidata": {
            "entity": wikidata_entity,
            "claims": wikidata_claims,
        },
        "wikipedia_summary": wikipedia_summary,
        "nominatim": compact_dict(cached.nominatim_result or {}, 20),
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
            packet["wikidata"]["claims"] = compact_dict(packet["wikidata"]["claims"], 15) or {}

    packet["packet_metadata"] = {
        "approx_tokens": estimate_tokens(serialized),
        "max_chars": max_chars,
    }
    return packet

