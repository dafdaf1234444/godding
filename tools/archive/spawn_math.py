#!/usr/bin/env python3
"""spawn_math.py - turn variance/cost math into a spawn-size recommendation.

Model (F-IS3 revised framing):
  utility(N) = baseline_quality
               - risk_aversion * baseline_std * std_factor(N, rho)
               - coordination_cost * (N - 1)

Where:
  std_factor(N, rho) = sqrt((1 + (N - 1) * rho) / N)
  rho in [0, 1] is pairwise error correlation.

Interpretation:
- lower std_factor means better diversification benefit
- higher coordination_cost penalizes larger swarms
- N* is argmax utility(N) over N in [1, n_max]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def std_factor(n: int, rho: float) -> float:
    if n <= 0:
        raise ValueError("n must be >= 1")
    rho = max(0.0, min(1.0, rho))
    return math.sqrt((1.0 + (n - 1) * rho) / n)


def utility(
    n: int,
    baseline_quality: float,
    baseline_std: float,
    rho: float,
    coordination_cost: float,
    risk_aversion: float,
) -> float:
    risk_term = risk_aversion * baseline_std * std_factor(n, rho)
    coordination_term = coordination_cost * (n - 1)
    return baseline_quality - risk_term - coordination_term


def required_degradation_fraction(
    n: int,
    baseline_std: float,
    rho: float,
    coordination_cost: float,
    risk_aversion: float,
) -> float:
    """Minimum single-agent degradation fraction required to justify N over 1.

    Rearranged from:
      risk_gain(N) >= coordination_cost * (N-1)
      risk_gain(N) = risk_aversion * baseline_std * (1 - std_factor(N, rho))
    """
    if n <= 1:
        return 0.0
    denom = risk_aversion * baseline_std
    if denom <= 0:
        return float("inf")
    return (coordination_cost * (n - 1)) / denom


def build_report(
    baseline_quality: float,
    baseline_std: float,
    rho: float,
    coordination_cost: float,
    risk_aversion: float,
    n_max: int,
    p119_threshold: float,
    tie_margin_min: float = 0.01,
) -> dict:
    rows = []
    best_raw_n = 1
    best_raw_u = utility(1, baseline_quality, baseline_std, rho, coordination_cost, risk_aversion)
    utility_by_n: dict[int, float] = {}

    for n in range(1, max(1, n_max) + 1):
        u = utility(n, baseline_quality, baseline_std, rho, coordination_cost, risk_aversion)
        utility_by_n[n] = u
        row = {
            "n": n,
            "std_factor": round(std_factor(n, rho), 6),
            "utility": round(u, 6),
            "gain_vs_n1": round(u - utility_by_n[1], 6),
            "required_degradation_fraction": round(
                required_degradation_fraction(
                    n=n,
                    baseline_std=baseline_std,
                    rho=rho,
                    coordination_cost=coordination_cost,
                    risk_aversion=risk_aversion,
                ),
                6,
            ),
        }
        row["passes_p119_gate"] = row["required_degradation_fraction"] <= p119_threshold
        rows.append(row)
        if u > best_raw_u:
            best_raw_u = u
            best_raw_n = n

    sorted_rows = sorted(utility_by_n.items(), key=lambda item: (-item[1], item[0]))
    if len(sorted_rows) >= 2:
        raw_top2_margin = sorted_rows[0][1] - sorted_rows[1][1]
    else:
        raw_top2_margin = float("inf")

    tie_margin = max(0.0, float(tie_margin_min))
    near_best = [n for n, u in utility_by_n.items() if (best_raw_u - u) <= (tie_margin + 1e-12)]
    near_best_lower = sorted(n for n in near_best if n < best_raw_n)
    tie_guard_triggered = (
        best_raw_n > 1
        and tie_margin > 0.0
        and raw_top2_margin < tie_margin
        and bool(near_best_lower)
    )
    if tie_guard_triggered:
        best_n = near_best_lower[0]
    else:
        best_n = best_raw_n
    best_u = utility_by_n[best_n]

    return {
        "model": {
            "baseline_quality": baseline_quality,
            "baseline_std": baseline_std,
            "error_correlation_rho": rho,
            "coordination_cost_per_extra_agent": coordination_cost,
            "risk_aversion": risk_aversion,
            "n_max": n_max,
            "p119_threshold_fraction": p119_threshold,
            "tie_margin_min": tie_margin,
        },
        "recommendation": {
            "best_n": best_n,
            "best_utility": round(best_u, 6),
            "best_n_raw": best_raw_n,
            "best_utility_raw": round(best_raw_u, 6),
            "raw_top2_margin": round(raw_top2_margin, 6) if math.isfinite(raw_top2_margin) else None,
            "tie_guard_triggered": tie_guard_triggered,
            "tie_guard_candidate_ns": near_best_lower if tie_guard_triggered else [],
            "spawn": best_n > 1,
        },
        "rows": rows,
    }


def calibrate_from_ai2_artifacts(paths: list[Path], coordination_cost_floor: float) -> dict:
    """Infer model inputs from F-AI2/F-HLT2 experiment artifacts."""
    weighted_trials = 0
    sum_leader_error = 0.0
    sum_async_error = 0.0
    sum_abs_async_corr = 0.0
    used: list[str] = []

    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        trials = int(payload.get("trials", 0) or 0)
        async_block = payload.get("async", {}) or {}
        if trials <= 0 or "follower_error_rate" not in async_block:
            continue

        leader_error = float(payload.get("leader_error_rate", 0.0))
        async_error = float(async_block.get("follower_error_rate", 0.0))
        async_corr = float(async_block.get("leader_follower_error_correlation", 0.0))

        weighted_trials += trials
        sum_leader_error += leader_error * trials
        sum_async_error += async_error * trials
        sum_abs_async_corr += abs(async_corr) * trials
        used.append(str(path))

    if weighted_trials <= 0:
        raise ValueError("No usable AI2 artifacts found for calibration.")

    leader_error_mean = sum_leader_error / weighted_trials
    async_error_mean = sum_async_error / weighted_trials
    abs_async_corr_mean = sum_abs_async_corr / weighted_trials

    baseline_quality = 1.0 - async_error_mean
    # Bernoulli std proxy for correctness variance.
    baseline_std = math.sqrt(max(0.0, baseline_quality * (1.0 - baseline_quality)))
    rho = max(0.0, min(1.0, abs_async_corr_mean))
    coordination_cost = coordination_cost_floor + max(0.0, async_error_mean - leader_error_mean)

    return {
        "artifact_count": len(used),
        "weighted_trials": weighted_trials,
        "used_artifacts": used,
        "leader_error_rate_mean": leader_error_mean,
        "async_error_rate_mean": async_error_mean,
        "abs_async_corr_mean": abs_async_corr_mean,
        "inferred_baseline_quality": baseline_quality,
        "inferred_baseline_std": baseline_std,
        "inferred_rho": rho,
        "inferred_coordination_cost": coordination_cost,
    }


def calibrate_coordination_cost_from_spawn_log(path: Path) -> dict:
    """Infer coordination-cost proxy from spawn-quality event history."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload.get("spawn_events", [])

    samples: list[float] = []
    sample_rows: list[dict] = []
    for ev in events:
        n = int(ev.get("agents_spawned", 0) or 0)
        if n <= 1:
            continue

        cost_proxy = None
        if "tool_call_cost_factor" in ev:
            factor = float(ev["tool_call_cost_factor"])
            # Extra cost per additional agent vs a single-agent baseline.
            cost_proxy = max(0.0, (factor - 1.0) / (n - 1))
        elif "wall_time_speedup" in ev:
            speedup = float(ev["wall_time_speedup"])
            ideal = float(n)
            if ideal > 0:
                inefficiency = max(0.0, 1.0 - min(speedup, ideal) / ideal)
                cost_proxy = inefficiency / (n - 1)

        if cost_proxy is None:
            continue
        # Clamp outliers to keep utility scale bounded.
        cost_proxy = max(0.0, min(1.0, cost_proxy))
        samples.append(cost_proxy)
        sample_rows.append({"id": ev.get("id", "?"), "agents_spawned": n, "cost_proxy": cost_proxy})

    if not samples:
        raise ValueError("No usable multi-agent spawn-log cost samples found.")

    samples_sorted = sorted(samples)
    mid = len(samples_sorted) // 2
    if len(samples_sorted) % 2 == 1:
        median = samples_sorted[mid]
    else:
        median = 0.5 * (samples_sorted[mid - 1] + samples_sorted[mid])

    mean = sum(samples_sorted) / len(samples_sorted)
    return {
        "source": str(path),
        "sample_count": len(samples_sorted),
        "sample_ids": sample_rows,
        "mean_cost_proxy": mean,
        "median_cost_proxy": median,
        "inferred_coordination_cost": median,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-quality", type=float, default=None)
    parser.add_argument("--baseline-std", type=float, default=None)
    parser.add_argument("--rho", type=float, default=None, help="Pairwise error correlation [0,1].")
    parser.add_argument("--coordination-cost", type=float, default=None, help="Utility cost per extra agent.")
    parser.add_argument(
        "--calibrate-ai2-glob",
        type=str,
        default=None,
        help="Optional glob for AI2 artifacts (e.g. 'experiments/ai/f-ai2-*.json') to infer model inputs.",
    )
    parser.add_argument(
        "--coordination-cost-floor",
        type=float,
        default=0.01,
        help="Minimum coordination cost when calibration is used.",
    )
    parser.add_argument(
        "--calibrate-spawn-log",
        type=Path,
        default=None,
        help="Optional spawn log JSON (e.g. experiments/spawn-quality/spawn-log.json) to infer coordination cost.",
    )
    parser.add_argument("--risk-aversion", type=float, default=1.0, help="Penalty weight on uncertainty.")
    parser.add_argument("--n-max", type=int, default=6)
    parser.add_argument("--p119-threshold", type=float, default=0.45, help="Spawn gate fraction for comparison.")
    parser.add_argument(
        "--tie-margin-min",
        type=float,
        default=0.01,
        help="Minimum top-2 utility gap required before promoting to a larger N.",
    )
    parser.add_argument("--json-out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    calibration = None
    coordination_calibration = None
    baseline_quality = args.baseline_quality
    baseline_std = args.baseline_std
    rho = args.rho
    coordination_cost = args.coordination_cost

    if args.calibrate_ai2_glob:
        root = Path(__file__).resolve().parent.parent
        paths = sorted(root.glob(args.calibrate_ai2_glob))
        calibration = calibrate_from_ai2_artifacts(paths, args.coordination_cost_floor)
        if baseline_quality is None:
            baseline_quality = calibration["inferred_baseline_quality"]
        if baseline_std is None:
            baseline_std = calibration["inferred_baseline_std"]
        if rho is None:
            rho = calibration["inferred_rho"]
        if coordination_cost is None:
            coordination_cost = calibration["inferred_coordination_cost"]

    if args.calibrate_spawn_log is not None:
        log_path = args.calibrate_spawn_log
        if not log_path.is_absolute():
            log_path = Path(__file__).resolve().parent.parent / log_path
        coordination_calibration = calibrate_coordination_cost_from_spawn_log(log_path)
        if coordination_cost is None:
            coordination_cost = coordination_calibration["inferred_coordination_cost"]
        elif args.coordination_cost is None:
            # Conservative merge: when both calibrators are active, keep the higher cost.
            coordination_cost = max(
                float(coordination_cost),
                float(coordination_calibration["inferred_coordination_cost"]),
            )

    # Backward-compatible defaults when explicit values are not provided.
    if baseline_quality is None:
        baseline_quality = 0.65
    if baseline_std is None:
        baseline_std = 0.20
    if rho is None:
        rho = 0.20
    if coordination_cost is None:
        coordination_cost = 0.03

    report = build_report(
        baseline_quality=baseline_quality,
        baseline_std=baseline_std,
        rho=rho,
        coordination_cost=coordination_cost,
        risk_aversion=args.risk_aversion,
        n_max=args.n_max,
        p119_threshold=args.p119_threshold,
        tie_margin_min=args.tie_margin_min,
    )
    if calibration is not None:
        report["calibration"] = calibration
    if coordination_calibration is not None:
        report["coordination_calibration"] = coordination_calibration

    if args.json_out is not None:
        out = args.json_out
        if not out.is_absolute():
            out = Path(__file__).resolve().parent.parent / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(json.dumps(report, indent=2))

    rec = report["recommendation"]
    print(
        f"recommended_n={rec['best_n']}",
        f"raw_best_n={rec['best_n_raw']}",
        f"tie_guard={rec['tie_guard_triggered']}",
        f"spawn={rec['spawn']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
