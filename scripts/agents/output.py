"""Write state updates and museum subfolder artifacts with provenance enforcement."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .models import DeepDiveAgentOutput, EnrichedField, MuseumRecordUpdate, TrustLevel, ValidationAgentOutput
from .provenance import merge_field
from .utils import normalize_time_needed, normalize_url, save_json, slugify, utcnow_iso

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"

SCORING_FIELDS = {
    "impressionist_strength",
    "modern_contemporary_strength",
    "historical_context_score",
}

HIGH_CHURN_FIELDS = {
    "reputation",
    "collection_tier",
    "time_needed",
    "city_tier",
    *SCORING_FIELDS,
}


@dataclass
class ApplyResult:
    applied_fields: list[str] = field(default_factory=list)
    rejected_fields: list[dict[str, Any]] = field(default_factory=list)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _manual_lock_fields(museum: dict[str, Any]) -> set[str]:
    raw = museum.get("manual_lock_fields") or museum.get("locked_fields") or []
    if isinstance(raw, str):
        raw = [raw]
    return {str(item) for item in raw if item}


def _current_primary_domain(museum: dict[str, Any], updates: dict[str, Any]) -> Optional[str]:
    if "primary_domain" in updates:
        field = updates["primary_domain"]
        if isinstance(field, dict) and "value" in field:
            return str(field["value"])
    return museum.get("primary_domain")


def _should_auto_apply(field_name: str, field_wrapper: dict[str, Any], confidence_threshold: int) -> bool:
    if field_name not in HIGH_CHURN_FIELDS:
        return True
    trust = TrustLevel(field_wrapper.get("trust_level", TrustLevel.UNKNOWN))
    confidence = int(field_wrapper.get("confidence", 1))
    if trust >= TrustLevel.WIKIPEDIA and confidence >= confidence_threshold:
        return True
    return False


def _normalize_field(field_name: str, field_wrapper: dict[str, Any]) -> tuple[dict[str, Any], Optional[str]]:
    value = field_wrapper.get("value")
    if field_name == "website":
        normalized = normalize_url(str(value) if value is not None else None)
        if normalized:
            field_wrapper["value"] = normalized
            return field_wrapper, None
        return field_wrapper, "invalid_website"
    if field_name == "time_needed":
        normalized = normalize_time_needed(str(value) if value is not None else None)
        if normalized:
            field_wrapper["value"] = normalized
            return field_wrapper, None
        return field_wrapper, "invalid_time_needed"
    return field_wrapper, None


def apply_state_file_updates(
    *,
    state_code: str,
    museum_id: str,
    updates: MuseumRecordUpdate,
    confidence_threshold: int,
    provenance_path: Path,
) -> ApplyResult:
    state_path = STATES_DIR / f"{state_code}.json"
    state_data = _load_json(state_path)
    museums = state_data.get("museums", [])

    provenance_data = _load_json(provenance_path)
    field_prov = provenance_data.get("field_provenance", {})

    result = ApplyResult()

    update_dict = updates.model_dump(exclude_none=True, exclude={"museum_id"})
    for i, museum in enumerate(museums):
        if museum.get("museum_id") != museum_id:
            continue

        manual_locks = _manual_lock_fields(museum)
        current_domain = _current_primary_domain(museum, update_dict)

        data_sources = update_dict.pop("data_sources", None)
        if data_sources:
            existing_sources = museum.get("data_sources") or []
            if not isinstance(existing_sources, list):
                existing_sources = [existing_sources]
            for source in data_sources:
                if source not in existing_sources:
                    existing_sources.append(source)
            museum["data_sources"] = existing_sources

        for key, field_wrapper in update_dict.items():
            if not isinstance(field_wrapper, dict) or "trust_level" not in field_wrapper:
                continue

            if key in SCORING_FIELDS and current_domain != "Art":
                result.rejected_fields.append(
                    {"field": key, "reason": "art_only_scoring", "proposed": field_wrapper.get("value")}
                )
                continue

            if not _should_auto_apply(key, field_wrapper, confidence_threshold):
                result.rejected_fields.append(
                    {"field": key, "reason": "low_confidence", "proposed": field_wrapper.get("value")}
                )
                continue

            field_wrapper, norm_error = _normalize_field(key, field_wrapper)
            if norm_error:
                result.rejected_fields.append(
                    {"field": key, "reason": norm_error, "proposed": field_wrapper.get("value")}
                )
                continue

            try:
                new_field = EnrichedField.model_validate(field_wrapper)
            except Exception:
                result.rejected_fields.append(
                    {"field": key, "reason": "invalid_field_wrapper", "proposed": field_wrapper.get("value")}
                )
                continue

            current_value = museum.get(key)
            current_prov = field_prov.get(key)
            new_value, new_prov, reason = merge_field(
                current_value=current_value,
                current_prov=current_prov,
                new_field=new_field,
                manual_lock=key in manual_locks,
            )

            if new_value != current_value:
                museum[key] = new_value
                field_prov[key] = new_prov
                result.applied_fields.append(key)
            else:
                result.rejected_fields.append(
                    {"field": key, "reason": reason, "proposed": field_wrapper.get("value")}
                )

        museum["updated_at"] = utcnow_iso()
        museum["last_updated"] = datetime.now(timezone.utc).date().isoformat()
        museums[i] = museum
        break

    state_data["museums"] = museums
    save_json(state_path, state_data)

    provenance_data["field_provenance"] = field_prov
    save_json(provenance_path, provenance_data)
    return result


def _slug_alias(museum_id: str, city: str, museum_name: str) -> str:
    city_slug = slugify(city)
    museum_slug = slugify(museum_name)
    suffix = museum_id.split("-")[-1][-6:]
    return f"{city_slug}-{museum_slug}--{suffix}"


def write_museum_subfolder(
    *,
    state_code: str,
    museum_id: str,
    folder_hash: str,
    output: ValidationAgentOutput | DeepDiveAgentOutput,
    apply_result: ApplyResult,
    fallback_city: str = "",
    fallback_name: str = "",
) -> None:
    museum_folder = STATES_DIR / state_code / folder_hash
    museum_folder.mkdir(parents=True, exist_ok=True)

    lookup_path = STATES_DIR / state_code / "_museum_lookup.json"
    lookup = _load_json(lookup_path)
    lookup[folder_hash] = museum_id
    save_json(lookup_path, lookup)

    alias_path = STATES_DIR / state_code / "_museum_alias.json"
    alias_lookup = _load_json(alias_path)
    city = fallback_city
    name = fallback_name
    if output.state_file_updates.city:
        city = output.state_file_updates.city.value
    if output.state_file_updates.museum_name:
        name = output.state_file_updates.museum_name.value
    alias = _slug_alias(museum_id, city or "", name or "")
    alias_lookup[alias] = folder_hash
    save_json(alias_path, alias_lookup)

    core_data = {
        "museum_id": museum_id,
        "folder_hash": folder_hash,
        "slug_alias": alias,
        "state_file_updates": output.state_file_updates.model_dump(exclude_none=True),
        "applied_fields": apply_result.applied_fields,
        "processed_at": output.processed_at.isoformat(),
        "agent_version": output.agent_version,
        "model_used": output.model_used,
    }
    save_json(museum_folder / "core.json", core_data)

    provenance_path = museum_folder / "provenance.json"
    provenance_data = _load_json(provenance_path)
    provenance_data.setdefault("run_metadata", {})
    provenance_data["run_metadata"].update(
        {
            "agent_version": output.agent_version,
            "model_used": output.model_used,
            "processed_at": output.processed_at.isoformat(),
            "confidence": output.confidence,
        }
    )
    save_json(provenance_path, provenance_data)

    if isinstance(output, DeepDiveAgentOutput):
        summaries_data = {
            "museum_id": museum_id,
            "summary_short": output.summary_short,
            "summary_long": output.summary_long,
            "collection_highlights": [h.model_dump() for h in output.collection_highlights],
            "signature_artists": output.signature_artists,
            "visitor_tips": output.visitor_tips,
            "best_for": output.best_for,
            "historical_significance": output.historical_significance,
            "architectural_notes": output.architectural_notes,
            "generated_at": output.processed_at.isoformat(),
            "model": output.model_used,
        }
        save_json(museum_folder / "summaries.json", summaries_data)

        if output.art_scoring:
            analysis_data = {
                "museum_id": museum_id,
                "art_scoring": output.art_scoring.model_dump(),
                "curatorial_approach": output.curatorial_approach,
                "generated_at": output.processed_at.isoformat(),
            }
            save_json(museum_folder / "analysis.json", analysis_data)
