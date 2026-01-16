#!/usr/bin/env python3
"""LLM enrichment pipeline orchestrator."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.context import load_museum_context, museum_id_to_folder
from agents.evidence import build_evidence_packet
from agents.deep_dive_agent import run_deep_dive_agent
from agents.output import apply_state_file_updates, write_museum_subfolder
from agents.quality import compute_gold_set_drift
from agents.utils import BudgetState, estimate_tokens, load_env_key, load_json, save_json
from agents.validation_agent import run_validation_agent

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATES_DIR = PROJECT_ROOT / "data" / "states"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"


MODEL_COSTS = {
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "gpt-4o": {"in": 2.50, "out": 10.00},
    "claude-3-haiku-20240307": {"in": 0.25, "out": 1.25},
    "claude-3-sonnet-20240229": {"in": 3.00, "out": 15.00},
}


def _list_state_codes() -> list[str]:
    codes: list[str] = []
    for p in sorted(STATES_DIR.glob("*.json")):
        code = p.stem.upper()
        if len(code) == 2 and code.isalpha():
            codes.append(code)
    return codes


def _parse_states(value: str) -> list[str]:
    parts = [p.strip().upper() for p in (value or "").split(",") if p.strip()]
    out: list[str] = []
    for p in parts:
        if len(p) != 2 or not p.isalpha():
            raise SystemExit(f"Invalid state code: {p!r}")
        out.append(p)
    return out


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = MODEL_COSTS.get(model)
    if not rates:
        return 0.0
    return (prompt_tokens / 1_000_000) * rates["in"] + (completion_tokens / 1_000_000) * rates["out"]


def _load_state_museums(state_code: str) -> list[dict[str, Any]]:
    data = load_json(STATES_DIR / f"{state_code}.json")
    return data.get("museums", [])


def _select_deep_dive_targets(top_n: int) -> set[str]:
    index_path = PROJECT_ROOT / "data" / "index" / "all-museums.json"
    if not index_path.exists() or top_n <= 0:
        return set()

    index = load_json(index_path)
    museums = index.get("museums", [])
    art = [m for m in museums if m.get("primary_domain") == "Art"]

    def _sort_key(m: dict[str, Any]) -> tuple:
        score = m.get("priority_score")
        if score is None:
            score = 1e9

        rep = m.get("reputation")
        if rep is None:
            rep = 9
            
        coll = m.get("collection_tier")
        if coll is None:
            coll = 9

        return (score, rep, coll, m.get("museum_id", ""))

    art_sorted = sorted(art, key=_sort_key)
    return {m.get("museum_id") for m in art_sorted[:top_n] if m.get("museum_id")}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MuseumSpark LLM enrichment pipeline")
    scope = parser.add_mutually_exclusive_group(required=False)
    scope.add_argument("--state", help="Two-letter state code")
    scope.add_argument("--states", help="Comma-separated state codes")
    scope.add_argument("--all-states", action="store_true", help="Run all states")
    parser.add_argument("--museum-id", help="Process a single museum_id")

    parser.add_argument("--provider", default="openai", choices=["openai", "anthropic"])
    parser.add_argument("--validation-model", default="gpt-4o-mini")
    parser.add_argument("--deep-dive-model", default="gpt-4o")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--validation-max-tokens", type=int, default=900)
    parser.add_argument("--deep-dive-max-tokens", type=int, default=1800)
    parser.add_argument("--budget", type=float, default=5.0, help="Total budget ceiling")
    parser.add_argument("--confidence-threshold", type=int, default=4)
    parser.add_argument("--top-n", type=int, default=100, help="Deep dive top N art museums")
    parser.add_argument("--use-cache", action="store_true", help="Use cached LLM responses")
    drift_group = parser.add_mutually_exclusive_group()
    drift_group.add_argument("--fail-on-drift", action="store_true", default=True)
    drift_group.add_argument("--no-fail-on-drift", action="store_false", dest="fail_on_drift")
    parser.add_argument("--gold-set", default=str(PROJECT_ROOT / "data" / "qa" / "gold-set.json"))
    parser.add_argument("--failure-threshold", type=float, default=0.10, help="Validation failure rate gate")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.provider == "openai" and not load_env_key("OPENAI_API_KEY"):
        raise SystemExit("Error: OPENAI_API_KEY environment variable not set.")
    if args.provider == "anthropic" and not load_env_key("ANTHROPIC_API_KEY"):
        raise SystemExit("Error: ANTHROPIC_API_KEY environment variable not set.")

    if not args.state and not args.states and not args.all_states and not args.museum_id:
        raise SystemExit("Provide --state/--states/--all-states or --museum-id")

    state_codes: list[str] = []
    if args.museum_id:
        state_codes = [args.museum_id.split("-")[1].upper()]
    elif args.all_states:
        state_codes = _list_state_codes()
    elif args.states:
        state_codes = _parse_states(args.states)
    elif args.state:
        state_codes = _parse_states(args.state)

    deep_dive_targets = _select_deep_dive_targets(args.top_n)

    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    budget = BudgetState(total_budget=float(args.budget))
    total_processed = 0
    total_failed = 0
    review_queue: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []

    for state_code in state_codes:
        museums = _load_state_museums(state_code)
        for museum in museums:
            museum_id = museum.get("museum_id")
            if not museum_id:
                continue
            if args.museum_id and museum_id != args.museum_id:
                continue

            context = load_museum_context(museum_id, state_code)
            folder_hash = museum_id_to_folder(museum_id)
            cache_dir = STATES_DIR / state_code / folder_hash / "cache"
            provenance_path = STATES_DIR / state_code / folder_hash / "provenance.json"

            evidence_packet = build_evidence_packet(context)
            estimated_prompt_tokens = estimate_tokens(json.dumps(evidence_packet, ensure_ascii=False))
            estimated_cost = _estimate_cost(
                args.validation_model, estimated_prompt_tokens, args.validation_max_tokens
            )
            if not budget.can_spend(estimated_cost):
                raise SystemExit("Budget gate reached. Aborting run.")

            try:
                validation_output = run_validation_agent(
                    context=context,
                    provider=args.provider,
                    model=args.validation_model,
                    temperature=args.temperature,
                    max_tokens=args.validation_max_tokens,
                    cache_dir=cache_dir,
                    use_cache=args.use_cache,
                )
            except Exception as exc:
                total_failed += 1
                review_queue.append(
                    {"museum_id": museum_id, "stage": "validation", "reason": str(exc)}
                )
                continue

            total_processed += 1

            budget.spend(estimated_cost)

            if args.dry_run:
                continue

            apply_result = apply_state_file_updates(
                state_code=state_code,
                museum_id=museum_id,
                updates=validation_output.state_file_updates,
                confidence_threshold=int(args.confidence_threshold),
                provenance_path=provenance_path,
            )

            write_museum_subfolder(
                state_code=state_code,
                museum_id=museum_id,
                folder_hash=folder_hash,
                output=validation_output,
                apply_result=apply_result,
                fallback_city=context.city,
                fallback_name=context.museum_name,
            )

            for rec in validation_output.recommendations:
                review_queue.append(
                    {
                        "museum_id": museum_id,
                        "field": rec.field_name,
                        "proposed": rec.proposed_value,
                        "confidence": rec.confidence,
                        "reason": rec.reason,
                    }
                )
            for rejection in apply_result.rejected_fields:
                review_queue.append({"museum_id": museum_id, **rejection})

            changes.append(
                {
                    "museum_id": museum_id,
                    "stage": "validation",
                    "applied_fields": apply_result.applied_fields,
                    "rejected_fields": apply_result.rejected_fields,
                }
            )

            if museum_id in deep_dive_targets:
                deep_evidence = build_evidence_packet(context, max_chars=12000)
                deep_prompt_tokens = estimate_tokens(json.dumps(deep_evidence, ensure_ascii=False))
                deep_cost = _estimate_cost(
                    args.deep_dive_model, deep_prompt_tokens, args.deep_dive_max_tokens
                )
                if not budget.can_spend(deep_cost):
                    raise SystemExit("Budget gate reached (deep dive). Aborting run.")

                try:
                    deep_output = run_deep_dive_agent(
                        context=context,
                        provider=args.provider,
                        model=args.deep_dive_model,
                        temperature=args.temperature,
                        max_tokens=args.deep_dive_max_tokens,
                        cache_dir=cache_dir,
                        use_cache=args.use_cache,
                    )
                except Exception as exc:
                    total_failed += 1
                    review_queue.append(
                        {"museum_id": museum_id, "stage": "deep_dive", "reason": str(exc)}
                    )
                    continue

                budget.spend(deep_cost)

                deep_apply = apply_state_file_updates(
                    state_code=state_code,
                    museum_id=museum_id,
                    updates=deep_output.state_file_updates,
                    confidence_threshold=int(args.confidence_threshold),
                    provenance_path=provenance_path,
                )

                write_museum_subfolder(
                    state_code=state_code,
                    museum_id=museum_id,
                    folder_hash=folder_hash,
                    output=deep_output,
                    apply_result=deep_apply,
                    fallback_city=context.city,
                    fallback_name=context.museum_name,
                )

                changes.append(
                    {
                        "museum_id": museum_id,
                        "stage": "deep_dive",
                        "applied_fields": deep_apply.applied_fields,
                        "rejected_fields": deep_apply.rejected_fields,
                    }
                )

            failure_rate = total_failed / max(1, total_processed)
            if failure_rate > float(args.failure_threshold):
                raise SystemExit("Validation failure rate gate exceeded.")

    save_json(run_dir / "changes.json", {"run_id": run_id, "changes": changes})
    save_json(run_dir / "review_queue.json", {"run_id": run_id, "items": review_queue})
    save_json(
        run_dir / "metrics.json",
        {
            "run_id": run_id,
            "total_processed": total_processed,
            "total_failed": total_failed,
            "failure_rate": total_failed / max(1, total_processed),
            "budget_total": budget.total_budget,
            "budget_spent": budget.spent_budget,
            "budget_remaining": budget.remaining(),
        },
    )

    if args.fail_on_drift:
        gold_path = Path(args.gold_set)
        drift_reports = []
        for state_code in state_codes:
            state_path = STATES_DIR / f"{state_code}.json"
            if not state_path.exists():
                continue
            report = compute_gold_set_drift(state_path, gold_path)
            drift_reports.append(
                {
                    "state": state_code,
                    "drift_rate": report.drift_rate,
                    "drifted_fields": report.drifted_fields,
                    "total_fields": report.total_fields,
                }
            )
            if report.drift_rate > 0.02:
                raise SystemExit("Gold-set drift gate exceeded.")

        save_json(run_dir / "gold_drift.json", {"run_id": run_id, "reports": drift_reports})

    print(f"[OK] Run complete: {run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
