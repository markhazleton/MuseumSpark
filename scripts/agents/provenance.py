"""Field-level provenance and trust enforcement."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from .models import EnrichedField, TrustLevel
from .utils import is_placeholder


def should_overwrite(
    *,
    old_prov: Optional[dict[str, Any]],
    new_field: EnrichedField[Any],
    manual_lock: bool,
) -> Tuple[bool, str]:
    if manual_lock and new_field.trust_level < TrustLevel.MANUAL_OVERRIDE:
        return False, "manual_lock"

    if is_placeholder(new_field.value):
        return False, "placeholder_blocked"

    if not old_prov:
        return True, "no_existing_provenance"

    old_trust = TrustLevel(old_prov.get("trust_level", TrustLevel.UNKNOWN))
    new_trust = new_field.trust_level

    if new_trust > old_trust:
        return True, "higher_trust"

    if new_trust == old_trust:
        old_time = old_prov.get("retrieved_at")
        if isinstance(old_time, str):
            try:
                old_dt = datetime.fromisoformat(old_time)
                # Make timezone-aware if naive
                if old_dt.tzinfo is None:
                    old_dt = old_dt.replace(tzinfo=timezone.utc)
            except Exception:
                old_dt = None
        elif isinstance(old_time, datetime):
            old_dt = old_time
            # Make timezone-aware if naive
            if old_dt.tzinfo is None:
                old_dt = old_dt.replace(tzinfo=timezone.utc)
        else:
            old_dt = None

        if old_dt is None:
            return True, "equal_trust_no_timestamp"
        
        # Ensure new_field.retrieved_at is also timezone-aware
        new_dt = new_field.retrieved_at
        if new_dt.tzinfo is None:
            new_dt = new_dt.replace(tzinfo=timezone.utc)
            
        if new_dt > old_dt:
            return True, "equal_trust_newer"

    return False, "lower_trust_or_older"


def merge_field(
    *,
    current_value: Any,
    current_prov: Optional[dict[str, Any]],
    new_field: EnrichedField[Any],
    manual_lock: bool,
) -> Tuple[Any, Optional[dict[str, Any]], str]:
    # CRITICAL DATA QUALITY RULE: Never replace a known value with null
    # This prevents data loss when LLM returns null for fields it couldn't extract
    if new_field.value is None and current_value is not None:
        # Check if current_value is actually meaningful (not empty string, not placeholder)
        if isinstance(current_value, str):
            if current_value.strip():  # Non-empty string
                return current_value, current_prov, "cannot_replace_known_with_null"
        else:
            # Non-string, non-None value (e.g., number, boolean, dict, list)
            return current_value, current_prov, "cannot_replace_known_with_null"
    
    allowed, reason = should_overwrite(old_prov=current_prov, new_field=new_field, manual_lock=manual_lock)
    if not allowed:
        return current_value, current_prov, reason

    new_prov = {
        "source": new_field.source,
        "trust_level": int(new_field.trust_level),
        "retrieved_at": new_field.retrieved_at.isoformat(),
        "confidence": new_field.confidence,
    }
    return new_field.value, new_prov, reason

