"""Quality gates and gold-set drift checks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DriftReport:
    total_fields: int = 0
    drifted_fields: int = 0
    drift_rate: float = 0.0
    diffs: list[dict[str, Any]] = field(default_factory=list)


def load_gold_set(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("museums", data)
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        museum_id = item.get("museum_id")
        if museum_id:
            expected = item.get("expected", item)
            out[museum_id] = expected
    return out


def compute_gold_set_drift(state_path: Path, gold_path: Path) -> DriftReport:
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold set file not found: {gold_path}")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    museums = {m.get("museum_id"): m for m in state.get("museums", [])}
    gold = load_gold_set(gold_path)

    report = DriftReport()
    for museum_id, expected_fields in gold.items():
        actual = museums.get(museum_id)
        if not actual:
            continue
        for field_name, expected_value in expected_fields.items():
            if field_name == "museum_id":
                continue
            report.total_fields += 1
            actual_value = actual.get(field_name)
            if actual_value != expected_value:
                report.drifted_fields += 1
                report.diffs.append(
                    {
                        "museum_id": museum_id,
                        "field": field_name,
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )

    if report.total_fields:
        report.drift_rate = report.drifted_fields / report.total_fields
    return report

