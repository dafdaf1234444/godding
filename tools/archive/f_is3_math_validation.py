#!/usr/bin/env python3
"""F-IS3 math validation: compare analytic spawn utility vs Monte Carlo replay.

This validates whether `tools/spawn_math.py` recommendations hold under a
stochastic replay model with configurable correlation and coordination cost.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import Random

import spawn_math

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Scenario:
    error_rate: float
    rho: float
    coordination_cost: float
    risk_aversion: float
    n_max: int
    trials: int
    model: str = "exchangeable"
    agent_sd: float = 0.0
    difficulty_sd: float = 0.0


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    mean = sum(values) / len(values)
    var = sum((x - mean) ** 2 for x in values) / len(values)
    return mean, math.sqrt(max(0.0, var))


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


def _simulate_quality_samples(
    *,
    n: int,
    error_rate: float,
    rho: float,
    trials: int,
    rng: Random,
) -> list[float]:
    """Return trial-quality samples using an exchangeable Bernoulli model.

    Correlation model:
    - with probability rho, all agents share one Bernoulli error draw
    - otherwise each agent draws error independently
    This gives pairwise error correlation exactly rho.
    """
    samples: list[float] = []
    p = _clamp(error_rate)
    r = _clamp(rho)
    t = max(1, int(trials))

    for _ in range(t):
        if rng.random() < r:
            shared_error = 1.0 if rng.random() < p else 0.0
            team_quality = 1.0 - shared_error
        else:
            correct = 0
            for _agent in range(n):
                if rng.random() >= p:
                    correct += 1
            team_quality = correct / n
        samples.append(team_quality)
    return samples


def _simulate_quality_samples_heterogeneous(
    *,
    n: int,
    error_rate: float,
    rho: float,
    trials: int,
    rng: Random,
    agent_sd: float,
    difficulty_sd: float,
) -> list[float]:
    """Non-exchangeable model with persistent agent heterogeneity + shared difficulty shocks."""
    samples: list[float] = []
    p = _clamp(error_rate)
    r = _clamp(rho)
    t = max(1, int(trials))
    agent_sd = max(0.0, float(agent_sd))
    difficulty_sd = max(0.0, float(difficulty_sd))

    agent_offsets = [rng.gauss(0.0, agent_sd) for _ in range(max(1, n))]

    for _ in range(t):
        difficulty = rng.gauss(0.0, difficulty_sd) if difficulty_sd > 0.0 else 0.0
        if rng.random() < r:
            mean_p = sum(_clamp(p + offset + difficulty) for offset in agent_offsets) / max(1, n)
            shared_error = 1.0 if rng.random() < mean_p else 0.0
            team_quality = 1.0 - shared_error
        else:
            correct = 0
            for offset in agent_offsets:
                p_i = _clamp(p + offset + difficulty)
                if rng.random() >= p_i:
                    correct += 1
            team_quality = correct / max(1, n)
        samples.append(team_quality)
    return samples


def simulated_utility_for_n(
    *,
    n: int,
    error_rate: float,
    rho: float,
    coordination_cost: float,
    risk_aversion: float,
    trials: int,
    rng: Random,
    model: str,
    agent_sd: float,
    difficulty_sd: float,
) -> dict:
    if model == "heterogeneous":
        samples = _simulate_quality_samples_heterogeneous(
            n=n,
            error_rate=error_rate,
            rho=rho,
            trials=trials,
            rng=rng,
            agent_sd=agent_sd,
            difficulty_sd=difficulty_sd,
        )
    else:
        samples = _simulate_quality_samples(
            n=n,
            error_rate=error_rate,
            rho=rho,
            trials=trials,
            rng=rng,
        )
    mean_quality, std_quality = _mean_std(samples)
    utility = mean_quality - risk_aversion * std_quality - coordination_cost * (n - 1)
    return {
        "mean_quality": _round(mean_quality),
        "std_quality": _round(std_quality),
        "utility": _round(utility),
    }


def evaluate_scenario(scenario: Scenario, *, seed: int) -> dict:
    q = 1.0 - max(0.0, min(1.0, scenario.error_rate))
    baseline_std = math.sqrt(max(0.0, q * (1.0 - q)))
    rng = Random(seed)

    rows: list[dict] = []
    analytic_rows: list[tuple[int, float]] = []
    best_analytic_n = 1
    best_analytic_u = -1e9
    best_sim_n = 1
    best_sim_u = -1e9

    for n in range(1, max(1, scenario.n_max) + 1):
        analytic_u = spawn_math.utility(
            n=n,
            baseline_quality=q,
            baseline_std=baseline_std,
            rho=scenario.rho,
            coordination_cost=scenario.coordination_cost,
            risk_aversion=scenario.risk_aversion,
        )
        sim = simulated_utility_for_n(
            n=n,
            error_rate=scenario.error_rate,
            rho=scenario.rho,
            coordination_cost=scenario.coordination_cost,
            risk_aversion=scenario.risk_aversion,
            trials=scenario.trials,
            rng=rng,
            model=scenario.model,
            agent_sd=scenario.agent_sd,
            difficulty_sd=scenario.difficulty_sd,
        )
        sim_u = float(sim["utility"])
        row = {
            "n": n,
            "analytic_utility": _round(analytic_u),
            "simulated_utility": sim["utility"],
            "abs_utility_error": _round(abs(analytic_u - sim_u)),
            "simulated_mean_quality": sim["mean_quality"],
            "simulated_std_quality": sim["std_quality"],
        }
        rows.append(row)
        analytic_rows.append((n, analytic_u))
        if analytic_u > best_analytic_u:
            best_analytic_u = analytic_u
            best_analytic_n = n
        if sim_u > best_sim_u:
            best_sim_u = sim_u
            best_sim_n = n

    analytic_rows.sort(key=lambda item: item[1], reverse=True)
    if len(analytic_rows) >= 2:
        top_margin = analytic_rows[0][1] - analytic_rows[1][1]
    else:
        top_margin = 0.0

    return {
        "inputs": {
            "error_rate": scenario.error_rate,
            "rho": scenario.rho,
            "coordination_cost": scenario.coordination_cost,
            "risk_aversion": scenario.risk_aversion,
            "n_max": scenario.n_max,
            "trials": scenario.trials,
            "seed": seed,
            "model": scenario.model,
            "agent_sd": scenario.agent_sd,
            "difficulty_sd": scenario.difficulty_sd,
        },
        "recommendation": {
            "analytic_best_n": best_analytic_n,
            "simulated_best_n": best_sim_n,
            "match": best_analytic_n == best_sim_n,
            "analytic_best_utility": _round(best_analytic_u),
            "simulated_best_utility": _round(best_sim_u),
            "best_n_gap": best_analytic_n - best_sim_n,
            "analytic_top2_margin": _round(top_margin),
        },
        "rows": rows,
    }


def _parse_float_list(raw: str) -> list[float]:
    values: list[float] = []
    for token in (raw or "").split(","):
        item = token.strip()
        if not item:
            continue
        values.append(float(item))
    if not values:
        raise ValueError("Expected a non-empty comma-separated float list.")
    return values


def run_grid(
    *,
    error_rates: list[float],
    rhos: list[float],
    coordination_costs: list[float],
    risk_aversion: float,
    n_max: int,
    trials: int,
    seed: int,
    model: str,
    agent_sd: float,
    difficulty_sd: float,
) -> dict:
    scenarios: list[dict] = []
    matches = 0
    within_one = 0
    abs_errors: list[float] = []
    mismatch_count = 0
    mismatch_low_margin = 0

    idx = 0
    for error_rate in error_rates:
        for rho in rhos:
            for cost in coordination_costs:
                scenario = Scenario(
                    error_rate=error_rate,
                    rho=rho,
                    coordination_cost=cost,
                    risk_aversion=risk_aversion,
                    n_max=n_max,
                    trials=trials,
                    model=model,
                    agent_sd=agent_sd,
                    difficulty_sd=difficulty_sd,
                )
                result = evaluate_scenario(scenario, seed=seed + idx)
                idx += 1
                scenarios.append(result)
                if result["recommendation"]["match"]:
                    matches += 1
                gap = abs(int(result["recommendation"]["best_n_gap"]))
                if gap <= 1:
                    within_one += 1
                if not result["recommendation"]["match"]:
                    mismatch_count += 1
                    if float(result["recommendation"]["analytic_top2_margin"]) <= 0.01:
                        mismatch_low_margin += 1
                abs_errors.extend([row["abs_utility_error"] for row in result["rows"]])

    mismatch_examples: list[dict] = []
    for item in scenarios:
        if item["recommendation"]["match"]:
            continue
        mismatch_examples.append(
            {
                "inputs": item["inputs"],
                "recommendation": item["recommendation"],
            }
        )

    return {
        "scenario_count": len(scenarios),
        "recommendation_match_count": matches,
        "recommendation_match_rate": _round(matches / max(1, len(scenarios))),
        "recommendation_within_one_n_rate": _round(within_one / max(1, len(scenarios))),
        "mismatch_low_margin_rate": _round(mismatch_low_margin / max(1, mismatch_count)),
        "mean_abs_utility_error": _round(sum(abs_errors) / max(1, len(abs_errors))),
        "max_abs_utility_error": _round(max(abs_errors) if abs_errors else 0.0),
        "mismatch_examples": mismatch_examples[:10],
        "scenarios": scenarios,
    }


def _load_model_from_spawn_artifact(path: Path) -> Scenario:
    payload = json.loads(path.read_text(encoding="utf-8"))
    model = payload.get("model", {})
    quality = float(model.get("baseline_quality", 0.7))
    quality = max(0.0, min(1.0, quality))
    error_rate = 1.0 - quality
    return Scenario(
        error_rate=error_rate,
        rho=float(model.get("error_correlation_rho", 0.0)),
        coordination_cost=float(model.get("coordination_cost_per_extra_agent", 0.02)),
        risk_aversion=float(model.get("risk_aversion", 1.0)),
        n_max=int(model.get("n_max", 6)),
        trials=3000,
    )


def run(args: argparse.Namespace) -> dict:
    grid = run_grid(
        error_rates=_parse_float_list(args.error_rates),
        rhos=_parse_float_list(args.rhos),
        coordination_costs=_parse_float_list(args.coordination_costs),
        risk_aversion=float(args.risk_aversion),
        n_max=int(args.n_max),
        trials=int(args.trials),
        seed=int(args.seed),
        model=str(args.model),
        agent_sd=float(args.agent_sd),
        difficulty_sd=float(args.difficulty_sd),
    )

    calibrated_path = Path(args.calibrated_model)
    if not calibrated_path.is_absolute():
        calibrated_path = REPO_ROOT / calibrated_path
    calibrated_scenario = _load_model_from_spawn_artifact(calibrated_path)
    calibrated_scenario = Scenario(
        error_rate=calibrated_scenario.error_rate,
        rho=calibrated_scenario.rho,
        coordination_cost=calibrated_scenario.coordination_cost,
        risk_aversion=calibrated_scenario.risk_aversion,
        n_max=calibrated_scenario.n_max,
        trials=int(args.trials),
        model=str(args.model),
        agent_sd=float(args.agent_sd),
        difficulty_sd=float(args.difficulty_sd),
    )
    calibrated_result = evaluate_scenario(calibrated_scenario, seed=int(args.seed) + 10000)

    payload = {
        "frontier_id": "F-IS3",
        "title": "Spawn math analytic-vs-simulation validation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "grid_error_rates": _parse_float_list(args.error_rates),
            "grid_rhos": _parse_float_list(args.rhos),
            "grid_coordination_costs": _parse_float_list(args.coordination_costs),
            "risk_aversion": float(args.risk_aversion),
            "n_max": int(args.n_max),
            "trials": int(args.trials),
            "seed": int(args.seed),
            "calibrated_model": str(calibrated_path),
            "model": str(args.model),
            "agent_sd": float(args.agent_sd),
            "difficulty_sd": float(args.difficulty_sd),
        },
        "summary": {
            "grid": {
                "scenario_count": grid["scenario_count"],
                "recommendation_match_rate": grid["recommendation_match_rate"],
                "recommendation_within_one_n_rate": grid["recommendation_within_one_n_rate"],
                "mismatch_low_margin_rate": grid["mismatch_low_margin_rate"],
                "mean_abs_utility_error": grid["mean_abs_utility_error"],
                "max_abs_utility_error": grid["max_abs_utility_error"],
            },
            "calibrated_model_check": calibrated_result["recommendation"],
        },
        "grid": grid,
        "calibrated_model_check": calibrated_result,
        "interpretation": (
            "If match rate is high and utility error is low, the closed-form spawn_math "
            "utility is a reliable decision proxy under the chosen error model."
        ),
    }

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="experiments/information-science/f-is3-math-validation-s186.json",
        help="Output artifact path.",
    )
    parser.add_argument("--error-rates", default="0.15,0.25,0.35")
    parser.add_argument("--rhos", default="0.0,0.1,0.2,0.35,0.5")
    parser.add_argument("--coordination-costs", default="0.01,0.03,0.05,0.08,0.12")
    parser.add_argument("--risk-aversion", type=float, default=1.0)
    parser.add_argument("--n-max", type=int, default=6)
    parser.add_argument("--trials", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=186)
    parser.add_argument(
        "--model",
        default="exchangeable",
        choices=("exchangeable", "heterogeneous"),
        help="Simulation model for error structure.",
    )
    parser.add_argument(
        "--agent-sd",
        type=float,
        default=0.0,
        help="Std dev of per-agent error offsets (heterogeneous model).",
    )
    parser.add_argument(
        "--difficulty-sd",
        type=float,
        default=0.0,
        help="Std dev of shared difficulty shocks per trial (heterogeneous model).",
    )
    parser.add_argument(
        "--calibrated-model",
        default="experiments/information-science/f-is3-spawn-math-s186-cost-calibrated.json",
        help="Spawn-math artifact used as a real-parameter consistency check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(args)
    summary = payload["summary"]["grid"]
    calibrated = payload["summary"]["calibrated_model_check"]
    print(
        "[f-is3-math-validation]",
        f"scenarios={summary['scenario_count']}",
        f"match_rate={summary['recommendation_match_rate']:.4f}",
        f"mean_abs_error={summary['mean_abs_utility_error']:.4f}",
        f"model={payload['inputs']['model']}",
        f"calibrated_best_n={calibrated['analytic_best_n']}/{calibrated['simulated_best_n']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
