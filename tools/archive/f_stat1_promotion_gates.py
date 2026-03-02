#!/usr/bin/env python3
"""F-STAT1 promotion gates from recent domain artifacts.

Build practical sample-size and effect-size gates by experiment class:
- simulation
- live_query
- lane_log_extraction
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from random import Random
from statistics import median
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GLOBS = [
    "experiments/ai/f-*.json",
    "experiments/finance/f-*.json",
    "experiments/information-science/f-*.json",
    "experiments/control-theory/f-*.json",
    "experiments/operations-research/f-*.json",
    "experiments/evolution/f-*.json",
    "experiments/colonies/p155-*.json",
]


@dataclass(frozen=True)
class Observation:
    artifact: str
    experiment_class: str
    sample_size: int
    effect_abs: float
    effect_metric_count: int


def _nested(obj: dict[str, Any], *path: str) -> Any:
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float) and float(value).is_integer():
        v = int(value)
        return v if v > 0 else None
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("quantile requires non-empty values")
    if len(values) == 1:
        return values[0]
    idx = q * (len(values) - 1)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return values[lo]
    frac = idx - lo
    return values[lo] * (1.0 - frac) + values[hi] * frac


def _iter_paths(globs: list[str], base_dir: Path = REPO_ROOT) -> list[Path]:
    paths: set[Path] = set()
    for pattern in globs:
        paths.update(base_dir.glob(pattern))
    return sorted(path for path in paths if path.is_file())


def _classify(path: Path, data: dict[str, Any]) -> str:
    name = path.as_posix().lower()
    mode = str(data.get("mode", "")).lower()
    model = data.get("model")

    if isinstance(model, dict) and "private_signal_accuracy" in model:
        return "simulation"
    if "controlled" in mode or "simulation" in mode:
        return "simulation"
    if "live" in mode or "query" in mode or "wikipedia" in mode:
        return "live_query"

    if any(
        key in data
        for key in (
            "summary_metrics",
            "matched_pairs",
            "session_filter_min",
            "auto_routing",
            "lane_plan",
            "classification_rule",
        )
    ):
        return "lane_log_extraction"

    if "/colonies/" in name:
        return "simulation"
    if any(
        token in name
        for token in (
            "lane",
            "history",
            "retention",
            "priority",
            "latency",
            "cadence",
            "threshold",
            "distill",
            "spawn",
        )
    ):
        return "lane_log_extraction"
    if any(token in name for token in ("live", "query", "wiki", "perturb")):
        return "live_query"
    return "simulation"


def _sample_size(data: dict[str, Any], experiment_class: str) -> int:
    candidates: list[int] = []

    def push(value: Any) -> None:
        v = _as_int(value)
        if v is not None:
            candidates.append(v)

    # Shared fields
    push(data.get("trials"))
    push(data.get("trial_count"))
    push(data.get("trials_per_condition"))
    push(_nested(data, "model", "trials_per_context"))

    if experiment_class == "lane_log_extraction":
        push(data.get("n_sessions"))
        push(_nested(data, "summary", "diff_events_total"))
        push(_nested(data, "summary_metrics", "claims_total"))
        push(_nested(data, "matched_pairs", "n_pairs"))
        push(data.get("input_papers"))
        push(data.get("input_lanes"))
        open_n = _as_int(_nested(data, "open_loop", "n_sessions"))
        closed_n = _as_int(_nested(data, "closed_loop", "n_sessions"))
        if open_n and closed_n:
            candidates.append(open_n + closed_n)

    return max(candidates) if candidates else 0


def _collect_metrics(
    obj: Any,
    path: str,
    key_predicate: callable,  # type: ignore[type-arg]
    out: list[float],
) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            next_path = f"{path}.{key}" if path else str(key)
            if key_predicate(str(key), value):
                numeric = _as_float(value)
                if numeric is not None:
                    out.append(numeric)
            _collect_metrics(value, next_path, key_predicate, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_metrics(item, path, key_predicate, out)


def _effect_values(data: dict[str, Any]) -> list[float]:
    effects: list[float] = []

    def is_delta_key(key: str, value: Any) -> bool:
        key_l = key.lower()
        if _as_float(value) is None:
            return False
        return any(
            token in key_l
            for token in ("delta", "difference", "improvement", "reduction", "gain", "lift")
        )

    _collect_metrics(data, "", is_delta_key, effects)

    async_block = data.get("async")
    sync_block = data.get("sync")
    if isinstance(async_block, dict) and isinstance(sync_block, dict):
        for key in set(async_block.keys()) & set(sync_block.keys()):
            left = _as_float(async_block.get(key))
            right = _as_float(sync_block.get(key))
            if left is None or right is None:
                continue
            effects.append(right - left)

    single_mean = _as_float(_nested(data, "single_agent", "summary", "mean"))
    majority_mean = _as_float(_nested(data, "majority_vote", "summary", "mean"))
    if single_mean is not None and majority_mean is not None:
        effects.append(majority_mean - single_mean)

    open_score = _as_float(_nested(data, "open_loop", "mean_score"))
    closed_score = _as_float(_nested(data, "closed_loop", "mean_score"))
    if open_score is not None and closed_score is not None:
        effects.append(closed_score - open_score)

    coop_acc = _as_float(_nested(data, "contexts", "cooperative", "group_accuracy_mean"))
    comp_acc = _as_float(_nested(data, "contexts", "competitive", "group_accuracy_mean"))
    if coop_acc is not None and comp_acc is not None:
        effects.append(comp_acc - coop_acc)

    # Fallback for artifacts without explicit deltas: use bounded rates/correlations.
    if not effects:
        rate_values: list[float] = []

        def is_rate_key(key: str, value: Any) -> bool:
            key_l = key.lower()
            numeric = _as_float(value)
            if numeric is None:
                return False
            if abs(numeric) > 1.0:
                return False
            return "rate" in key_l or "correlation" in key_l

        _collect_metrics(data, "", is_rate_key, rate_values)
        effects.extend(rate_values)

    normalized: list[float] = []
    for value in effects:
        if not math.isfinite(value):
            continue
        abs_value = abs(value)
        if abs_value == 0:
            continue
        # Keep all metrics in [0,1] so class gates are comparable.
        bounded = abs_value if abs_value <= 1.0 else abs_value / (1.0 + abs_value)
        normalized.append(bounded)
    return normalized


def _build_observation(path: Path, data: dict[str, Any]) -> Observation | None:
    experiment_class = _classify(path, data)
    sample_size = _sample_size(data, experiment_class)
    effect_values = _effect_values(data)
    if sample_size <= 0 or not effect_values:
        return None
    return Observation(
        artifact=path.as_posix(),
        experiment_class=experiment_class,
        sample_size=sample_size,
        effect_abs=round(float(median(effect_values)), 6),
        effect_metric_count=len(effect_values),
    )


def _bootstrap_ci_mean(values: list[float], seed: int, samples: int) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        return (values[0], values[0])

    rng = Random(seed)
    n = len(values)
    means: list[float] = []
    for _ in range(samples):
        total = 0.0
        for _ in range(n):
            total += values[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    low = means[int(round((samples - 1) * 0.025))]
    high = means[int(round((samples - 1) * 0.975))]
    return low, high


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _power_for_effect(effect: float, n_per_arm: int) -> float:
    if effect <= 0 or n_per_arm <= 0:
        return 0.0
    se = math.sqrt(0.5 / n_per_arm)
    z = (effect / se) - 1.96
    return max(0.0, min(1.0, _norm_cdf(z)))


def _n_for_target_power(effect: float, target_power: float = 0.8) -> int:
    if effect <= 0:
        return 0
    z_beta = 0.84 if target_power >= 0.8 else 0.52
    n = 0.5 * ((1.96 + z_beta) / effect) ** 2
    return int(math.ceil(n))


def _summarize_class(name: str, observations: list[Observation], seed: int, bootstrap_samples: int) -> dict[str, Any]:
    by_class = [row for row in observations if row.experiment_class == name]
    if not by_class:
        return {
            "observations": 0,
            "recommended_min_sample_size": None,
            "recommended_min_effect_size": None,
        }

    sample_sizes = sorted(float(row.sample_size) for row in by_class)
    effects = sorted(float(row.effect_abs) for row in by_class)
    ci_low, ci_high = _bootstrap_ci_mean(effects, seed=seed, samples=bootstrap_samples)

    q40_n = int(math.ceil(_quantile(sample_sizes, 0.40)))
    q50_n = int(math.ceil(_quantile(sample_sizes, 0.50)))
    effect_gate = max(0.03, _quantile(effects, 0.25))

    if name in ("simulation", "live_query"):
        power_n = _n_for_target_power(effect_gate, target_power=0.8)
        practical_cap = max(
            int(sample_sizes[-1]),
            int(math.ceil(_quantile(sample_sizes, 0.75) * 1.5)),
        )
        recommended_n = max(q40_n, min(power_n, practical_cap))
        expected_power = _power_for_effect(effect_gate, recommended_n)
    else:
        power_n = None
        practical_cap = None
        recommended_n = max(20, q50_n)
        expected_power = None

    confidence = "LOW" if len(by_class) < 4 else "MEDIUM" if len(by_class) < 8 else "HIGH"
    return {
        "observations": len(by_class),
        "sample_size_distribution": {
            "min": int(sample_sizes[0]),
            "median": int(round(_quantile(sample_sizes, 0.5))),
            "q75": int(math.ceil(_quantile(sample_sizes, 0.75))),
            "max": int(sample_sizes[-1]),
        },
        "effect_abs_distribution": {
            "min": round(effects[0], 4),
            "median": round(_quantile(effects, 0.5), 4),
            "q75": round(_quantile(effects, 0.75), 4),
            "max": round(effects[-1], 4),
            "bootstrap_mean_ci95": [round(ci_low, 4), round(ci_high, 4)],
        },
        "recommended_min_sample_size": recommended_n,
        "recommended_min_effect_size": round(effect_gate, 4),
        "practical_cap_n": practical_cap,
        "power_model_n_for_80pct": power_n,
        "estimated_power_at_recommended_n": None if expected_power is None else round(expected_power, 4),
        "data_confidence": confidence,
    }


def run(
    *,
    output_path: Path,
    glob_patterns: list[str] | None = None,
    artifact_paths: list[Path] | None = None,
    bootstrap_samples: int = 3000,
    seed: int = 186,
) -> dict[str, Any]:
    patterns = glob_patterns or DEFAULT_GLOBS
    paths = artifact_paths or _iter_paths(patterns)
    observations: list[Observation] = []
    skipped: list[str] = []

    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                skipped.append(path.as_posix())
                continue
            obs = _build_observation(path, data)
            if obs is None:
                skipped.append(path.as_posix())
                continue
            observations.append(obs)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            skipped.append(path.as_posix())

    class_names = ["simulation", "live_query", "lane_log_extraction"]
    class_gates = {
        name: _summarize_class(name, observations, seed=seed, bootstrap_samples=bootstrap_samples)
        for name in class_names
    }

    result = {
        "frontier_id": "F-STAT1",
        "title": "Promotion gates by experiment class",
        "seed": seed,
        "bootstrap_samples": bootstrap_samples,
        "artifact_globs": patterns,
        "artifacts_considered": len(paths),
        "artifacts_usable": len(observations),
        "artifacts_skipped": len(skipped),
        "class_gates": class_gates,
        "observations": [
            {
                "artifact": row.artifact,
                "experiment_class": row.experiment_class,
                "sample_size": row.sample_size,
                "effect_abs": row.effect_abs,
                "effect_metric_count": row.effect_metric_count,
            }
            for row in sorted(
                observations,
                key=lambda r: (r.experiment_class, -r.sample_size, r.artifact),
            )
        ],
        "notes": [
            "Effect size uses median absolute bounded effect per artifact from explicit deltas, paired comparisons, and fallback rates/correlations.",
            "Power model uses normal approximation for two-arm proportion-like comparisons; lane-log extraction uses empirical gates only.",
            "These are promotion gates (minimums), not optimal design points.",
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="F-STAT1 promotion gate calibration")
    parser.add_argument(
        "--output",
        default="experiments/statistics/f-stat1-promotion-gates-s186.json",
        help="Output artifact path",
    )
    parser.add_argument(
        "--glob",
        dest="globs",
        action="append",
        help="Additional artifact glob relative to repo root (can be repeated)",
    )
    parser.add_argument("--bootstrap-samples", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=186)
    return parser


def main() -> int:
    args = _parser().parse_args()
    globs = args.globs if args.globs else DEFAULT_GLOBS
    output = Path(args.output)
    output_path = output if output.is_absolute() else REPO_ROOT / output
    result = run(
        output_path=output_path,
        glob_patterns=globs,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )
    print(f"F-STAT1 artifacts usable: {result['artifacts_usable']}/{result['artifacts_considered']}")
    for name, row in result["class_gates"].items():
        gate_n = row["recommended_min_sample_size"]
        gate_effect = row["recommended_min_effect_size"]
        print(f"{name}: n>={gate_n}, |effect|>={gate_effect}")
    print(f"Wrote {output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
