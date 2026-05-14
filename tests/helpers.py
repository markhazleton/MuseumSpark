"""Shared test helpers for MuseumSpark tests."""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEMA_PATH = DATA_DIR / "schema" / "museum.schema.json"
STATES_DIR = DATA_DIR / "states"


def minimal_museum(**overrides) -> dict:
    """Return a scoreable museum dict with all Phase 2 fields populated."""
    base: dict = {
        "museum_id": "test-museum",
        "museum_name": "Test Museum",
        "country": "USA",
        "state_province": "Colorado",
        "city": "Denver",
        "website": "https://example.com",
        "museum_type": "Art Museum",
        "street_address": "123 Main St",
        "postal_code": "80201",
        "is_scoreable": True,
        "impressionist_strength": 3,
        "modern_contemporary_strength": 2,
        "hat_strength": 1,
        "historical_context_score": 3,
        "eca_score": 2,
        "reputation_level": "Regional",
        "collection_level": "Moderate",
    }
    base.update(overrides)
    return base
