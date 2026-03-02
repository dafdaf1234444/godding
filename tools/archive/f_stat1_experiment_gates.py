#!/usr/bin/env python3
"""F-STAT1: calibrate experiment promotion gates from recent domain artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import Random
from statistics import fmean, median, pstdev
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class RunPoint:
    class_name: str
    artifact: str
    effect: float
    sample_size: int


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def _bootstrap_ci_mean(
    values: list[float], *, resamples: int = 4000, seed: int = 186
) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        return (_round(values[0]), _round(values[0]))
    rng = Random(seed)
    means: list[float] = []
    n = len(values)
    for _ in range(max(500, resamples)):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(fmean(sample))
    means.sort()
    lo = means[int(0.025 * (len(means) - 1))]
    hi = means[int(0.975 * (len(means) - 1))]
    return (_round(lo), _round(hi))


def _sign(value: float, eps: float = 1e-9) -> int:
    if value > eps:
        return 1
    if value < -eps:
        return -1
    return 0


def _stability(values: list[float]) -> float:
    if not values:
        return 0.0
    buckets = {-1: 0, 0: 0, 1: 0}
    for value in values:
        buckets[_sign(value)] += 1
    return _round(max(buckets.values()) / len(values))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_live_query_runs() -> list[RunPoint]:
    roots = sorted((REPO_ROOT / "experiments" / "finance").glob("f-fin1-factual-qa*.json"))
    points: list[RunPoint] = []
    for path in roots:
        payload = _load_json(path)
        effect: float | None = None
        sample_size = 0
        if "delta" in payload and isinstance(payload["delta"], dict):
            raw = payload["delta"].get("mean_accuracy_n3_minus_n1")
            if raw is not None:
                effect = float(raw)
            sample_size = int(payload.get("trials_per_condition", 0) or 0)
        elif "observed" in payload and isinstance(payload["observed"], dict):
            raw = payload["observed"].get("delta_n3_minus_n1")
            if raw is not None:
                effect = float(raw)
            sample_size = int(payload.get("n_trials_per_condition", 0) or 0)

        if effect is None:
            continue
        if sample_size <= 0:
            sample_size = 1
        points.append(
            RunPoint(
                class_name="live_query",
                artifact=str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                effect=_round(effect),
                sample_size=sample_size,
            )
        )
    return points


def _collect_lane_log_runs() -> list[RunPoint]:
    roots = sorted(
        (REPO_ROOT / "experiments" / "information-science").glob(
            "f-is5-lane-distill*.json"
        )
    )
    points: list[RunPoint] = []
    for path in roots:
        payload = _load_json(path)
        summary = payload.get("summary_metrics")
        if not isinstance(summary, dict):
            continue
        acc = summary.get("transfer_acceptance_rate")
        coll = summary.get("merge_collision_frequency")
        claims = summary.get("claims_total")
        if acc is None or coll is None:
            continue
        effect = float(acc) - float(coll)
        sample_size = int(claims or 0)
        if sample_size <= 0:
            sample_size = 1
        points.append(
            RunPoint(
                class_name="lane_log_extraction",
                artifact=str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                effect=_round(effect),
                sample_size=sample_size,
            )
        )
    return points


def _collect_simulation_runs() -> list[RunPoint]:
    roots = sorted(
        (REPO_ROOT / "experiments" / "control-theory").glob(
            "f-ctl1-threshold-sweep-s186*.json"
        )
    )
    points: list[RunPoint] = []
    for path in roots:
        payload = _load_json(path)
        current = payload.get("current_policy_reference") or {}
        best = payload.get("best_thresholds") or {}
        cur_burden = current.get("alert_burden")
        best_burden = best.get("alert_burden")
        if cur_burden is None or best_burden is None:
            continue
        effect = float(cur_burden) - float(best_burden)
        sample_size = int(payload.get("n_sessions", 0) or 0)
        if sample_size <= 0:
            sample_size = 1
        points.append(
            RunPoint(
                class_name="simulation_control",
                artifact=str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                effect=_round(effect),
                sample_size=sample_size,
            )
        )
    return points


def _recommended_min_sample(class_name: str, observed: int) -> int:
    if class_name == "live_query":
        return max(8, observed)
    if class_name == "lane_log_extraction":
        return max(20, observed)
    return max(30, observed)


def _summarize_class(class_name: str, runs: list[RunPoint]) -> dict:
    effects = [row.effect for row in runs]
    samples = [row.sample_size for row in runs]
    if not effects:
        return {
            "class_name": class_name,
            "run_count": 0,
            "recommended_gate": {
                "min_runs": 6,
                "min_per_run_sample": _recommended_min_sample(class_name, 0),
                "min_abs_effect": 0.05,
                "promotion_rule": "insufficient data",
            },
            "runs": [],
        }

    mean_effect = fmean(effects)
    std_effect = pstdev(effects) if len(effects) > 1 else 0.0
    ci_low, ci_high = _bootstrap_ci_mean(effects)
    ci_cross_zero = ci_low <= 0.0 <= ci_high
    stability = _stability(effects)
    observed_med_sample = int(round(median(samples)))

    min_runs = max(4, len(runs))
    if ci_cross_zero or stability < 0.7:
        min_runs = max(6, len(runs) + 2)

    min_abs_effect = max(0.02, abs(mean_effect) * 0.5, std_effect * 0.5)
    min_abs_effect = _round(min_abs_effect)
    min_per_run = _recommended_min_sample(class_name, observed_med_sample)

    return {
        "class_name": class_name,
        "run_count": len(runs),
        "effect_metric": {
            "live_query": "mean_accuracy_n3_minus_n1",
            "lane_log_extraction": "transfer_acceptance_rate_minus_collision_frequency",
            "simulation_control": "current_alert_burden_minus_best_alert_burden",
        }[class_name],
        "observed": {
            "mean_effect": _round(mean_effect),
            "median_effect": _round(median(effects)),
            "std_effect": _round(std_effect),
            "ci95_mean_effect": [ci_low, ci_high],
            "sign_stability": stability,
            "median_sample_size": observed_med_sample,
        },
        "recommended_gate": {
            "min_runs": int(min_runs),
            "min_per_run_sample": int(min_per_run),
            "min_abs_effect": min_abs_effect,
            "promotion_rule": (
                f"Promote class claim only if >= {min_runs} independent runs, "
                f"per-run sample >= {min_per_run}, and |effect| >= {min_abs_effect}."
            ),
        },
        "runs": [
            {
                "artifact": run.artifact,
                "effect": run.effect,
                "sample_size": run.sample_size,
            }
            for run in runs
        ],
    }


def run(out_path: Path) -> dict:
    collectors: list[Callable[[], list[RunPoint]]] = [
        _collect_live_query_runs,
        _collect_lane_log_runs,
        _collect_simulation_runs,
    ]
    all_runs: list[RunPoint] = []
    for collect in collectors:
        all_runs.extend(collect())

    grouped: dict[str, list[RunPoint]] = {
        "live_query": [],
        "lane_log_extraction": [],
        "simulation_control": [],
    }
    for run_point in all_runs:
        grouped[run_point.class_name].append(run_point)

    payload = {
        "frontier_id": "F-STAT1",
        "title": "Class-specific experiment promotion gates",
        "class_summaries": [
            _summarize_class(name, grouped[name]) for name in grouped.keys()
        ],
        "generated_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "notes": (
            "Gates are first-pass calibration from S186 artifacts; update as more "
            "independent runs arrive and as scoring contracts become stricter."
        ),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/statistics/f-stat1-experiment-gates-s186.json"),
        help="Output artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(REPO_ROOT / args.out)
    print(f"Wrote {args.out}")
    for row in payload["class_summaries"]:
        gate = row["recommended_gate"]
        print(
            row["class_name"],
            "runs=",
            row["run_count"],
            "min_runs=",
            gate["min_runs"],
            "min_abs_effect=",
            gate["min_abs_effect"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
