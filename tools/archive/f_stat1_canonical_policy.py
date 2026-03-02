#!/usr/bin/env python3
"""F-STAT1: reconcile gate artifacts into one canonical promotion policy.

Combines:
- experiments/statistics/f-stat1-experiment-gates-s186.json
- experiments/statistics/f-stat1-promotion-gates-s186.json
- experiments/statistics/f-stat1-gates-s186.json

Outputs a canonical class policy with explicit caveats and readiness state.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_CLASSES = ("live_query", "simulation", "lane_log_extraction")
CLASS_ALIASES = {
    "live_query": "live_query",
    "simulation": "simulation",
    "simulation_control": "simulation",
    "simulation_replay": "simulation",
    "lane_log_extraction": "lane_log_extraction",
}


def _norm_class(name: str) -> str | None:
    return CLASS_ALIASES.get((name or "").strip().lower())


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float) and value.is_integer():
        iv = int(value)
        return iv if iv > 0 else None
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _extract_experiment_gates(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload.get("class_summaries")
    if not isinstance(rows, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        cls = _norm_class(str(row.get("class_name", "")))
        if cls not in EXPECTED_CLASSES:
            continue
        gate = row.get("recommended_gate", {})
        if not isinstance(gate, dict):
            gate = {}
        out[cls] = {
            "min_runs": _as_int(gate.get("min_runs")),
            "sample_size": _as_int(gate.get("min_per_run_sample")),
            "effect_size": _as_float(gate.get("min_abs_effect")),
            "run_count": _as_int(row.get("run_count")),
        }
    return out


def _extract_promotion_gates(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    classes = payload.get("class_gates")
    if not isinstance(classes, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for raw, row in classes.items():
        if not isinstance(row, dict):
            continue
        cls = _norm_class(str(raw))
        if cls not in EXPECTED_CLASSES:
            continue
        out[cls] = {
            "sample_size": _as_int(row.get("recommended_min_sample_size")),
            "effect_size": _as_float(row.get("recommended_min_effect_size")),
            "power_model_n_for_80pct": _as_int(row.get("power_model_n_for_80pct")),
            "estimated_power_at_recommended_n": _as_float(row.get("estimated_power_at_recommended_n")),
            "data_confidence": str(row.get("data_confidence", "") or "").upper(),
        }
    return out


def _extract_replay_gates(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    classes = payload.get("classes")
    if not isinstance(classes, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for raw, row in classes.items():
        if not isinstance(row, dict):
            continue
        cls = _norm_class(str(raw))
        if cls not in EXPECTED_CLASSES:
            continue
        out[cls] = {
            "sample_size": _as_int(row.get("recommended_min_n")),
            "effect_size": _as_float(row.get("recommended_min_abs_effect")),
            "confidence": str(row.get("confidence", "") or "").upper(),
            "evidence_rows": _as_int(row.get("evidence_rows")),
            "passing_rows": _as_int(row.get("passing_rows")),
        }
    return out


def _ratio(values: list[float]) -> float:
    positive = [v for v in values if v > 0.0]
    if len(positive) < 2:
        return 1.0
    return max(positive) / min(positive)


def _confidence_label(source_count: int, issue_count: int) -> str:
    if source_count == 3 and issue_count == 0:
        return "HIGH"
    if source_count >= 2 and issue_count <= 1:
        return "MEDIUM"
    return "LOW"


def _reconcile_class(
    cls: str,
    exp_row: dict[str, Any] | None,
    prom_row: dict[str, Any] | None,
    replay_row: dict[str, Any] | None,
) -> dict[str, Any]:
    exp_row = exp_row or {}
    prom_row = prom_row or {}
    replay_row = replay_row or {}

    sample_sources = {
        "experiment_gates": _as_int(exp_row.get("sample_size")),
        "promotion_gates": _as_int(prom_row.get("sample_size")),
        "replay_gates": _as_int(replay_row.get("sample_size")),
    }
    effect_sources = {
        "experiment_gates": _as_float(exp_row.get("effect_size")),
        "promotion_gates": _as_float(prom_row.get("effect_size")),
        "replay_gates": _as_float(replay_row.get("effect_size")),
    }
    run_sources = {"experiment_gates": _as_int(exp_row.get("min_runs"))}

    sample_candidates = [v for v in sample_sources.values() if v is not None]
    effect_candidates = [v for v in effect_sources.values() if v is not None]

    canonical_runs = max(v for v in run_sources.values() if v is not None) if any(
        v is not None for v in run_sources.values()
    ) else None
    canonical_sample = max(sample_candidates) if sample_candidates else None
    canonical_effect = round(max(effect_candidates), 4) if effect_candidates else None

    issues: list[str] = []
    prerequisites: list[str] = []

    available_sources = sum(
        1 for src in ("experiment_gates", "promotion_gates", "replay_gates")
        if sample_sources.get(src) is not None and effect_sources.get(src) is not None
    )
    if available_sources < 2:
        issues.append("insufficient_source_overlap")

    effect_ratio = _ratio(effect_candidates)
    if effect_ratio >= 2.0:
        issues.append("effect_threshold_dispersion")

    if cls == "live_query":
        power_target = _as_int(prom_row.get("power_model_n_for_80pct"))
        promoted_n = _as_int(prom_row.get("sample_size"))
        if power_target and promoted_n and power_target > promoted_n:
            issues.append("underpowered_practical_cap")
            prerequisites.append("Increase live_query sample target toward power-model n_for_80pct or keep practical-cap caveat explicit.")
        exp_sample = sample_sources.get("experiment_gates")
        larger_sample = max(
            sample_sources.get("promotion_gates") or 0,
            sample_sources.get("replay_gates") or 0,
        )
        if exp_sample and larger_sample and exp_sample * 4 <= larger_sample:
            issues.append("mixed_regime_risk")
            prerequisites.append("Split live_query by scoring regime (resolver-proxy vs direct-answer) before hard-locking gates.")

    if cls == "lane_log_extraction" and effect_ratio >= 2.0:
        prerequisites.append("Add independent replications with explicit transfer tags until lane threshold spread narrows.")

    status = "READY" if not issues else "PROVISIONAL"
    return {
        "class_name": cls,
        "status": status,
        "confidence": _confidence_label(available_sources, len(issues)),
        "canonical_gate": {
            "min_runs": canonical_runs,
            "min_per_run_sample": canonical_sample,
            "min_abs_effect": canonical_effect,
            "promotion_rule": (
                "Promote only when independent run count, per-run sample, and absolute effect all meet or exceed this class gate."
            ),
        },
        "source_gates": {
            "experiment_gates": {
                "min_runs": run_sources.get("experiment_gates"),
                "min_per_run_sample": sample_sources.get("experiment_gates"),
                "min_abs_effect": effect_sources.get("experiment_gates"),
            },
            "promotion_gates": {
                "min_per_run_sample": sample_sources.get("promotion_gates"),
                "min_abs_effect": effect_sources.get("promotion_gates"),
            },
            "replay_gates": {
                "min_per_run_sample": sample_sources.get("replay_gates"),
                "min_abs_effect": effect_sources.get("replay_gates"),
            },
        },
        "diagnostics": {
            "effect_threshold_ratio_max_over_min": round(effect_ratio, 4),
            "issues": issues,
            "prerequisites": prerequisites,
            "promotion_data_confidence": str(prom_row.get("data_confidence", "") or "").upper(),
            "replay_confidence": str(replay_row.get("confidence", "") or "").upper(),
            "estimated_power_at_recommended_n": _as_float(prom_row.get("estimated_power_at_recommended_n")),
            "power_model_n_for_80pct": _as_int(prom_row.get("power_model_n_for_80pct")),
        },
    }


def run(
    *,
    experiment_path: Path,
    promotion_path: Path,
    replay_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    exp = _extract_experiment_gates(_load_json(experiment_path))
    prom = _extract_promotion_gates(_load_json(promotion_path))
    replay = _extract_replay_gates(_load_json(replay_path))

    class_rows = [
        _reconcile_class(cls, exp.get(cls), prom.get(cls), replay.get(cls))
        for cls in EXPECTED_CLASSES
    ]
    ready = [row["class_name"] for row in class_rows if row["status"] == "READY"]
    provisional = [row["class_name"] for row in class_rows if row["status"] == "PROVISIONAL"]

    payload = {
        "frontier_id": "F-STAT1",
        "title": "Canonical promotion policy reconciliation",
        "inputs": {
            "experiment_gates": str(experiment_path.as_posix()),
            "promotion_gates": str(promotion_path.as_posix()),
            "replay_gates": str(replay_path.as_posix()),
        },
        "policy": class_rows,
        "summary": {
            "ready_classes": ready,
            "provisional_classes": provisional,
            "all_classes_ready": len(provisional) == 0,
            "policy_lock_recommended": len(provisional) == 0,
        },
        "notes": [
            "Canonical gate picks the strictest threshold (max sample, max effect) across available source gates.",
            "A class is PROVISIONAL when source dispersion or known methodological caveats remain unresolved.",
            "Live-query class remains provisional until regime split and power-gap handling are explicit.",
        ],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment-gates",
        default="experiments/statistics/f-stat1-experiment-gates-s186.json",
        help="Path to class experiment gates artifact.",
    )
    parser.add_argument(
        "--promotion-gates",
        default="experiments/statistics/f-stat1-promotion-gates-s186.json",
        help="Path to promotion gates artifact.",
    )
    parser.add_argument(
        "--replay-gates",
        default="experiments/statistics/f-stat1-gates-s186.json",
        help="Path to replay gates artifact.",
    )
    parser.add_argument(
        "--out",
        default="experiments/statistics/f-stat1-canonical-policy-s186.json",
        help="Output artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(
        experiment_path=REPO_ROOT / args.experiment_gates,
        promotion_path=REPO_ROOT / args.promotion_gates,
        replay_path=REPO_ROOT / args.replay_gates,
        out_path=REPO_ROOT / args.out,
    )
    print(f"Wrote {args.out}")
    summary = payload["summary"]
    print("ready_classes=", ",".join(summary["ready_classes"]) or "none")
    print("provisional_classes=", ",".join(summary["provisional_classes"]) or "none")
    print("policy_lock_recommended=", summary["policy_lock_recommended"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
