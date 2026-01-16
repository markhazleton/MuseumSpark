"""Shared utilities for the LLM enrichment pipeline."""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

PLACEHOLDER_STRINGS = {"", "tbd", "unknown", "n/a", "-", "null"}

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


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat().replace("+00:00", "Z")
    raise TypeError(f"Type {type(obj)} not serializable")


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=json_serial) + "\n", encoding="utf-8")


def is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().casefold() in PLACEHOLDER_STRINGS
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def normalize_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    value = url.strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    while value.endswith("/"):
        value = value[:-1]
    return value


def normalize_time_needed(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = value.strip().lower()
    for allowed in TIME_NEEDED_ALLOWED:
        if v == allowed.lower():
            return allowed
    return TIME_NEEDED_SYNONYMS.get(v)


def heuristic_time_needed(museum_type: Optional[str]) -> Optional[str]:
    if not museum_type:
        return None
    value = museum_type.lower()
    if any(k in value for k in ["historic house", "historic site", "small gallery", "house museum"]):
        return "Quick stop (<1 hr)"
    if any(k in value for k in ["encyclopedic", "natural history", "large complex", "campus"]):
        return "Full day"
    if any(k in value for k in ["art museum", "history museum", "science museum", "children's museum", "university museum"]):
        return "Half day"
    return "Half day"


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "unknown"


def truncate_text(value: Optional[str], max_chars: int) -> Optional[str]:
    if value is None:
        return None
    if len(value) <= max_chars:
        return value
    return value[: max(0, max_chars - 3)] + "..."


def compact_dict(data: Optional[dict[str, Any]], max_keys: int) -> Optional[dict[str, Any]]:
    if not isinstance(data, dict):
        return None
    keys = sorted(data.keys())[: max(0, max_keys)]
    return {k: data[k] for k in keys}


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


@dataclass
class BudgetState:
    total_budget: float
    spent_budget: float = 0.0
    reserve_ratio: float = 0.15

    def remaining(self) -> float:
        return max(0.0, self.total_budget - self.spent_budget)

    def reserve(self) -> float:
        return self.total_budget * self.reserve_ratio

    def can_spend(self, amount: float) -> bool:
        return self.remaining() - amount >= self.reserve()

    def spend(self, amount: float) -> None:
        self.spent_budget += max(0.0, amount)


def load_env_key(name: str) -> Optional[str]:
    return os.getenv(name)
