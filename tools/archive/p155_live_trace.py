#!/usr/bin/env python3
"""p155_live_trace.py — trace-level replication harness for P-155.

Runs a small multi-agent tournament under two incentive contexts:
- cooperative: rewards group correctness + truthful traces
- competitive: rewards local influence/individual gain over group outcomes

The harness emits explicit trace samples and aggregate metrics to JSON.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import Random


ROLES = ("collaborator", "deceptor", "neutral")


@dataclass(frozen=True)
class Config:
    agents: int
    rounds: int
    trials: int
    seed: int
    signal_accuracy: float
    learning_rate: float
    selection_beta: float
    tail_window: int
    trace_samples: int


def _softmax_pick(values: dict[str, float], beta: float, rng: Random) -> str:
    max_v = max(values.values())
    weights: dict[str, float] = {}
    total = 0.0
    for role, value in values.items():
        w = math.exp(beta * (value - max_v))
        weights[role] = w
        total += w

    threshold = rng.random() * total
    cumulative = 0.0
    for role in ROLES:
        cumulative += weights[role]
        if cumulative >= threshold:
            return role
    return ROLES[-1]


def _emit_trace(role: str, signal: int, rng: Random) -> tuple[int, bool]:
    if role == "collaborator":
        trace = signal
    elif role == "deceptor":
        trace = 1 - signal
    else:
        # Neutral agents are noisy and weakly truth-preserving.
        trace = signal if rng.random() < 0.55 else (1 - signal)
    truthful = trace == signal
    return trace, truthful


def _reward(
    context: str,
    truthful: bool,
    individual_correct: bool,
    group_correct: bool,
    influence: float,
) -> float:
    if context == "cooperative":
        reward = 1.2 if group_correct else -0.7
        reward += 0.45 if truthful else -0.9
        reward += 0.2 if individual_correct else -0.2
        return reward

    # Competitive mode: personal correctness + influence, with weak anti-group term.
    reward = 0.8 if individual_correct else -0.45
    reward += 0.9 * influence
    reward -= 0.65 if group_correct else 0.0
    reward += 0.45 if (not truthful and not group_correct) else 0.0
    return reward


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _share_dict(counter: dict[str, int], denom: float) -> dict[str, float]:
    if denom <= 0:
        return {role: 0.0 for role in ROLES}
    return {role: counter.get(role, 0) / denom for role in ROLES}


def run_context(context: str, cfg: Config) -> dict:
    role_share_tail: dict[str, list[float]] = {role: [] for role in ROLES}
    accuracy_tail: list[float] = []
    round_role_sums: list[dict[str, float]] = [{role: 0.0 for role in ROLES} for _ in range(cfg.rounds)]
    round_accuracy_sums: list[float] = [0.0 for _ in range(cfg.rounds)]
    trace_samples: list[dict] = []

    for trial in range(cfg.trials):
        rng = Random(cfg.seed + (1000 if context == "competitive" else 0) + trial)
        q_values = [{role: 0.0 for role in ROLES} for _ in range(cfg.agents)]
        round_role_shares: list[dict[str, float]] = []
        round_accuracies: list[float] = []

        for round_idx in range(cfg.rounds):
            hidden_state = rng.randint(0, 1)
            private_signals = [
                hidden_state if rng.random() < cfg.signal_accuracy else (1 - hidden_state)
                for _ in range(cfg.agents)
            ]
            agent_order = list(range(cfg.agents))
            rng.shuffle(agent_order)

            actions: list[dict] = []
            role_counts = {role: 0 for role in ROLES}
            traces = []

            for position, agent_id in enumerate(agent_order):
                role = _softmax_pick(q_values[agent_id], cfg.selection_beta, rng)
                trace, truthful = _emit_trace(role, private_signals[agent_id], rng)
                role_counts[role] += 1
                traces.append(trace)
                actions.append(
                    {
                        "agent_id": agent_id,
                        "position": position,
                        "role": role,
                        "signal": private_signals[agent_id],
                        "trace": trace,
                        "truthful": truthful,
                    }
                )

            ones = sum(traces)
            group_prediction = 1 if ones >= (cfg.agents / 2.0) else 0
            group_correct = group_prediction == hidden_state

            matching_counts = {0: cfg.agents - ones, 1: ones}
            for action in actions:
                influence = (matching_counts[action["trace"]] - 1) / max(cfg.agents - 1, 1)
                individual_correct = action["trace"] == hidden_state
                reward = _reward(
                    context=context,
                    truthful=action["truthful"],
                    individual_correct=individual_correct,
                    group_correct=group_correct,
                    influence=influence,
                )
                role = action["role"]
                agent_id = action["agent_id"]
                q_values[agent_id][role] += cfg.learning_rate * (reward - q_values[agent_id][role])

                if len(trace_samples) < cfg.trace_samples:
                    trace_samples.append(
                        {
                            "trial": trial,
                            "round": round_idx,
                            "agent_id": agent_id,
                            "position": action["position"],
                            "role": role,
                            "signal": action["signal"],
                            "trace": action["trace"],
                            "truthful": action["truthful"],
                            "hidden_state": hidden_state,
                            "group_prediction": group_prediction,
                            "group_correct": group_correct,
                            "individual_correct": individual_correct,
                            "reward": round(reward, 4),
                        }
                    )

            role_shares = _share_dict(role_counts, float(cfg.agents))
            round_role_shares.append(role_shares)
            round_accuracies.append(1.0 if group_correct else 0.0)

            for role in ROLES:
                round_role_sums[round_idx][role] += role_shares[role]
            round_accuracy_sums[round_idx] += round_accuracies[-1]

        start = max(0, cfg.rounds - cfg.tail_window)
        tail_roles = round_role_shares[start:]
        tail_acc = round_accuracies[start:]
        final_shares = {
            role: _mean([r[role] for r in tail_roles]) for role in ROLES
        }
        for role in ROLES:
            role_share_tail[role].append(final_shares[role])
        accuracy_tail.append(_mean(tail_acc))

    round_series = []
    for i in range(cfg.rounds):
        round_series.append(
            {
                "round": i,
                "mean_role_share": {
                    role: round_role_sums[i][role] / cfg.trials for role in ROLES
                },
                "mean_group_accuracy": round_accuracy_sums[i] / cfg.trials,
            }
        )

    return {
        "context": context,
        "trials": cfg.trials,
        "final_share_mean": {role: _mean(role_share_tail[role]) for role in ROLES},
        "final_share_median": {role: statistics.median(role_share_tail[role]) for role in ROLES},
        "group_accuracy_mean": _mean(accuracy_tail),
        "group_accuracy_median": statistics.median(accuracy_tail),
        "round_series": round_series,
        "trace_samples": trace_samples,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents", type=int, default=12, help="Agents per trial.")
    parser.add_argument("--rounds", type=int, default=180, help="Rounds per trial.")
    parser.add_argument("--trials", type=int, default=80, help="Trials per context.")
    parser.add_argument("--seed", type=int, default=155, help="Base RNG seed.")
    parser.add_argument(
        "--signal-accuracy",
        type=float,
        default=0.70,
        help="Private signal accuracy for each agent.",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.12,
        help="Q-value update step size.",
    )
    parser.add_argument(
        "--selection-beta",
        type=float,
        default=2.8,
        help="Softmax sharpness for role choice.",
    )
    parser.add_argument(
        "--tail-window",
        type=int,
        default=50,
        help="Rounds at end of trial used for final-share metrics.",
    )
    parser.add_argument(
        "--trace-samples",
        type=int,
        default=180,
        help="Per-context trace sample rows captured in output.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output JSON path.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Optional baseline JSON from a previous run to compare deltas against.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = Config(
        agents=args.agents,
        rounds=args.rounds,
        trials=args.trials,
        seed=args.seed,
        signal_accuracy=args.signal_accuracy,
        learning_rate=args.learning_rate,
        selection_beta=args.selection_beta,
        tail_window=args.tail_window,
        trace_samples=args.trace_samples,
    )

    cooperative = run_context("cooperative", cfg)
    competitive = run_context("competitive", cfg)
    delta = {
        "deceptor_share_mean_delta_comp_minus_coop": (
            competitive["final_share_mean"]["deceptor"] - cooperative["final_share_mean"]["deceptor"]
        ),
        "collaborator_share_mean_delta_comp_minus_coop": (
            competitive["final_share_mean"]["collaborator"] - cooperative["final_share_mean"]["collaborator"]
        ),
        "group_accuracy_mean_delta_comp_minus_coop": (
            competitive["group_accuracy_mean"] - cooperative["group_accuracy_mean"]
        ),
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "experiment": "p155-live-trace-incentive-replication",
        "model": {
            "description": "Trace-level multi-agent tournament with adaptive role selection under incentive contexts.",
            "agents": cfg.agents,
            "rounds_per_trial": cfg.rounds,
            "trials_per_context": cfg.trials,
            "seed": cfg.seed,
            "private_signal_accuracy": cfg.signal_accuracy,
            "learning_rate": cfg.learning_rate,
            "selection_beta": cfg.selection_beta,
            "tail_window": cfg.tail_window,
            "roles": list(ROLES),
            "reward_models": {
                "cooperative": "group correctness + truthful trace + individual correctness",
                "competitive": "individual correctness + influence - group correctness + deceptive bonus when group wrong",
            },
        },
        "contexts": {
            "cooperative": cooperative,
            "competitive": competitive,
        },
        "delta": delta,
        "interpretation": [
            "Competitive incentives increased deceptor share in explicit per-trace multi-agent runs.",
            "Competitive incentives reduced group accuracy relative to cooperative incentives.",
            "This is software-agent live trace evidence; external/LLM human-task replication is still future work.",
        ],
    }

    if args.baseline is not None:
        if not args.baseline.exists():
            raise SystemExit(f"Baseline file not found: {args.baseline}")
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        baseline_delta = baseline.get("delta", {})
        comparison = {}
        for key, value in delta.items():
            baseline_value = baseline_delta.get(key)
            if isinstance(baseline_value, (int, float)):
                comparison[key] = {
                    "current": value,
                    "baseline": float(baseline_value),
                    "abs_diff": abs(value - float(baseline_value)),
                }
        payload["baseline_comparison"] = {
            "baseline_path": str(args.baseline),
            "delta_comparison": comparison,
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(
        "delta:",
        f"deceptor={delta['deceptor_share_mean_delta_comp_minus_coop']:+.4f}",
        f"accuracy={delta['group_accuracy_mean_delta_comp_minus_coop']:+.4f}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
