#!/usr/bin/env python3
"""F-GAM1: cooperative vs competitive incentive baseline from p155 artifacts."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean, median, pstdev

REPO_ROOT = Path(__file__).resolve().parent.parent


def _entropy(shares: dict[str, float]) -> float:
    total = sum(float(max(0.0, value)) for value in shares.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in shares.values():
        p = float(max(0.0, value)) / total
        if p > 0:
            entropy -= p * math.log2(p)
    return round(entropy, 6)


def _extract_metrics(payload: dict) -> dict | None:
    contexts = payload.get("contexts")
    if not isinstance(contexts, dict):
        return None
    coop = contexts.get("cooperative")
    comp = contexts.get("competitive")
    if not isinstance(coop, dict) or not isinstance(comp, dict):
        return None

    coop_share = coop.get("final_share_mean") or {}
    comp_share = comp.get("final_share_mean") or {}
    if not isinstance(coop_share, dict) or not isinstance(comp_share, dict):
        return None

    coop_acc = float(coop.get("group_accuracy_mean") or 0.0)
    comp_acc = float(comp.get("group_accuracy_mean") or 0.0)
    coop_dep = float(coop_share.get("deceptor") or 0.0)
    comp_dep = float(comp_share.get("deceptor") or 0.0)
    coop_col = float(coop_share.get("collaborator") or 0.0)
    comp_col = float(comp_share.get("collaborator") or 0.0)
    coop_neu = float(coop_share.get("neutral") or 0.0)
    comp_neu = float(comp_share.get("neutral") or 0.0)

    # Productive-yield proxy: high collaboration share + high group correctness.
    coop_yield = coop_col * coop_acc
    comp_yield = comp_col * comp_acc

    return {
        "cooperative": {
            "group_accuracy_mean": round(coop_acc, 6),
            "deceptor_share_mean": round(coop_dep, 6),
            "collaborator_share_mean": round(coop_col, 6),
            "neutral_share_mean": round(coop_neu, 6),
            "role_entropy": _entropy(coop_share),
            "productive_yield_proxy": round(coop_yield, 6),
        },
        "competitive": {
            "group_accuracy_mean": round(comp_acc, 6),
            "deceptor_share_mean": round(comp_dep, 6),
            "collaborator_share_mean": round(comp_col, 6),
            "neutral_share_mean": round(comp_neu, 6),
            "role_entropy": _entropy(comp_share),
            "productive_yield_proxy": round(comp_yield, 6),
        },
        "delta_comp_minus_coop": {
            "group_accuracy_mean": round(comp_acc - coop_acc, 6),
            "deceptor_share_mean": round(comp_dep - coop_dep, 6),
            "collaborator_share_mean": round(comp_col - coop_col, 6),
            "neutral_share_mean": round(comp_neu - coop_neu, 6),
            "role_entropy": round(_entropy(comp_share) - _entropy(coop_share), 6),
            "productive_yield_proxy": round(comp_yield - coop_yield, 6),
        },
    }


def _summarize(values: list[float]) -> dict:
    if not values:
        return {
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "sign_stability": 0.0,
        }
    pos = sum(1 for value in values if value > 0)
    neg = sum(1 for value in values if value < 0)
    zero = len(values) - pos - neg
    sign_stability = max(pos, neg, zero) / len(values)
    return {
        "mean": round(fmean(values), 6),
        "median": round(float(median(values)), 6),
        "std": round(float(pstdev(values)), 6) if len(values) > 1 else 0.0,
        "sign_stability": round(sign_stability, 4),
    }


def run(out_path: Path) -> dict:
    paths = sorted((REPO_ROOT / "experiments" / "colonies").glob("p155-live-trace-*.json"))
    rows: list[dict] = []

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metrics = _extract_metrics(payload)
        if metrics is None:
            continue
        rows.append(
            {
                "artifact": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                **metrics,
            }
        )

    deltas = {
        "deceptor_share_mean": [row["delta_comp_minus_coop"]["deceptor_share_mean"] for row in rows],
        "group_accuracy_mean": [row["delta_comp_minus_coop"]["group_accuracy_mean"] for row in rows],
        "productive_yield_proxy": [row["delta_comp_minus_coop"]["productive_yield_proxy"] for row in rows],
        "role_entropy": [row["delta_comp_minus_coop"]["role_entropy"] for row in rows],
    }

    delta_summary = {name: _summarize(values) for name, values in deltas.items()}
    deceptor_mean = delta_summary["deceptor_share_mean"]["mean"]
    accuracy_mean = delta_summary["group_accuracy_mean"]["mean"]
    yield_mean = delta_summary["productive_yield_proxy"]["mean"]
    entropy_mean = delta_summary["role_entropy"]["mean"]

    if deceptor_mean > 0 and accuracy_mean < 0 and yield_mean < 0:
        verdict = "cooperative_dominates"
    elif deceptor_mean <= 0 and accuracy_mean >= 0:
        verdict = "competitive_viable"
    else:
        verdict = "tradeoff_regime"

    result = {
        "frontier_id": "F-GAM1",
        "title": "Incentive design baseline (cooperative vs competitive)",
        "study_count": len(rows),
        "studies": rows,
        "delta_summary_comp_minus_coop": delta_summary,
        "verdict": verdict,
        "interpretation": {
            "deception_proxy": "deceptor_share_mean (higher is worse)",
            "merge_quality_proxy": "group_accuracy_mean (higher is better)",
            "net_knowledge_yield_proxy": "collaborator_share_mean * group_accuracy_mean",
            "exploration_proxy": "role_entropy (higher can mean broader exploration mix)",
            "notes": (
                "This baseline uses p155 controlled traces as an isomorphic proxy, not live lane interventions."
            ),
            "headline": (
                "competitive incentives increase deception pressure and reduce quality/yield"
                if verdict == "cooperative_dominates"
                else "incentive tradeoff remains mixed; requires live-lane A/B"
                if verdict == "tradeoff_regime"
                else "competitive regime appears non-degrading in current proxy set"
            ),
            "mean_entropy_delta_comp_minus_coop": entropy_mean,
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/game-theory/f-gam1-incentive-baseline-s186.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(REPO_ROOT / args.out)
    print(f"Wrote {args.out}")
    print(
        "studies=",
        result["study_count"],
        "verdict=",
        result["verdict"],
        "deceptor_delta_mean=",
        result["delta_summary_comp_minus_coop"]["deceptor_share_mean"]["mean"],
        "accuracy_delta_mean=",
        result["delta_summary_comp_minus_coop"]["group_accuracy_mean"]["mean"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
