"""Load the full MuseumContext used by LLM agents."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"


def museum_id_to_folder(museum_id: str) -> str:
    hash_bytes = hashlib.sha256(museum_id.encode("utf-8")).hexdigest()
    return f"m_{hash_bytes[:8]}"


def _read_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_text(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


@dataclass
class CachedMuseumData:
    wikidata_entity: Optional[dict] = None
    wikidata_claims: Optional[dict] = None
    nominatim_result: Optional[dict] = None
    wikipedia_summary: Optional[str] = None
    website_html: Optional[str] = None
    website_json_ld: Optional[dict] = None
    subpages_scraped: list[dict] | None = None
    previous_validation: Optional[dict] = None
    previous_deep_dive: Optional[dict] = None
    cache_timestamp: Optional[datetime] = None
    cache_version: str = "v1"


@dataclass
class MuseumContext:
    museum_id: str
    museum_name: str
    state_province: str
    city: str
    country: str
    state_record: dict
    cached_data: CachedMuseumData
    folder_hash: str
    has_existing_enrichment: bool = False


def load_cached_data(museum_folder: Path) -> CachedMuseumData:
    cache_dir = museum_folder / "cache"
    meta = _read_json(cache_dir / "cache_meta.json") or {}
    cache_ts = None
    if isinstance(meta.get("cache_timestamp"), str):
        try:
            cache_ts = datetime.fromisoformat(meta["cache_timestamp"])
        except Exception:
            cache_ts = None

    return CachedMuseumData(
        wikidata_entity=_read_json(cache_dir / "wikidata_entity.json"),
        wikidata_claims=_read_json(cache_dir / "wikidata_claims.json"),
        nominatim_result=_read_json(cache_dir / "nominatim.json"),
        wikipedia_summary=_read_text(cache_dir / "wikipedia_summary.txt"),
        website_html=_read_text(cache_dir / "website_html.html"),
        website_json_ld=_read_json(cache_dir / "website_json_ld.json"),
        subpages_scraped=_read_json(cache_dir / "subpages_scraped.json") or [],
        previous_validation=_read_json(cache_dir / "validation_v1.json"),
        previous_deep_dive=_read_json(cache_dir / "deep_dive_v1.json"),
        cache_timestamp=cache_ts,
        cache_version=str(meta.get("cache_version") or "v1"),
    )


def load_museum_context(museum_id: str, state_code: str) -> MuseumContext:
    state_path = STATES_DIR / f"{state_code}.json"
    state_data = json.loads(state_path.read_text(encoding="utf-8"))
    state_record = next((m for m in state_data.get("museums", []) if m.get("museum_id") == museum_id), None)
    if not state_record:
        raise ValueError(f"Museum {museum_id} not found in {state_path}")

    folder_hash = museum_id_to_folder(museum_id)
    museum_folder = STATES_DIR / state_code / folder_hash
    cached_data = load_cached_data(museum_folder)
    has_existing = museum_folder.exists()

    return MuseumContext(
        museum_id=museum_id,
        museum_name=state_record.get("museum_name") or "",
        state_province=state_record.get("state_province") or state_code,
        city=state_record.get("city") or "Unknown",
        country=state_record.get("country") or "USA",
        state_record=state_record,
        cached_data=cached_data,
        folder_hash=folder_hash,
        has_existing_enrichment=has_existing,
    )
