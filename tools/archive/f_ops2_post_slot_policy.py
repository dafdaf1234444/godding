#!/usr/bin/env python3
"""F-OPS2 post-slot consolidation policy synthesizer."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def derive_wip_policy(ops1: dict) -> dict:
    recommended_cap = int(ops1.get("recommended", {}).get("cap", 4))
    confidence = str(ops1.get("recommendation_confidence", {}).get("level", "UNKNOWN"))
    delta = ops1.get("ab_comparison", {}).get("delta_b_minus_a", {})
    delta_net = float(delta.get("net_score", 0.0))
    delta_conflict = float(delta.get("conflict_rate", 0.0))
    delta_overhead = float(delta.get("overhead_ratio", 0.0))
    decision_hint = str(ops1.get("ab_comparison", {}).get("decision_hint", "unknown"))

    cap5_promotion_ready = (
        decision_hint == "prefer_cap_b"
        and delta_net >= 0.0
        and delta_conflict <= 0.0
        and delta_overhead <= 0.0
    )
    return {
        "default_wip_cap": recommended_cap,
        "confidence": confidence,
        "ab_hint": decision_hint,
        "delta_b_minus_a": {
            "net_score": delta_net,
            "conflict_rate": delta_conflict,
            "overhead_ratio": delta_overhead,
        },
        "cap5_promotion_ready_now": cap5_promotion_ready,
        "cap5_promotion_rule": (
            "Require two consecutive reruns with delta_net_score>=0 and non-worsening "
            "conflict/overhead before promoting cap 5."
        ),
    }


def derive_overlap_policy(is5: dict) -> dict:
    rec = is5.get("recommended", {})
    shared_per_lane = int(rec.get("shared_per_lane", 0))
    collision = float(rec.get("merge_collision_frequency", 1.0))
    transfer = float(rec.get("transfer_acceptance_rate", 0.0))
    contested = int(rec.get("contested_transfer_candidates", 0))
    return {
        "shared_per_lane_default": shared_per_lane,
        "transfer_acceptance_rate": transfer,
        "merge_collision_frequency": collision,
        "contested_transfer_candidates": contested,
        "target_collision_frequency_max": 0.5,
        "disagreement_reduction_needed": collision >= 0.6,
        "rule": (
            "Keep explicit decision tags mandatory. If two consecutive reruns stay at "
            "collision>=0.6, run disagreement reduction before increasing overlap."
        ),
    }


def derive_promotion_policy(stat1: dict, stat2: dict, stat3: dict) -> dict:
    policy_rows = stat1.get("policy", [])
    all_classes_ready = bool(stat1.get("summary", {}).get("all_classes_ready", False))
    provisional = [row.get("class_name") for row in policy_rows if row.get("status") == "PROVISIONAL"]
    transfer_label = str(stat2.get("transfer_decision", {}).get("label", "inconclusive"))
    overall_i2 = float(stat2.get("overall", {}).get("I2_percent", 100.0))

    candidate = None
    families = stat3.get("by_family", {})
    if "information_science_lane_distill" in families:
        candidate = families["information_science_lane_distill"]
    family_i2 = float(stat2.get("by_family", {}).get("information_science_lane_distill", {}).get("I2_percent", 100.0))
    promotion_ready_flag = bool(candidate.get("promotion_ready", False)) if candidate else False

    policy_lock = all_classes_ready and transfer_label == "positive" and overall_i2 < 50.0
    return {
        "policy_lock_recommended": policy_lock,
        "all_classes_ready": all_classes_ready,
        "provisional_classes": [c for c in provisional if c],
        "transfer_decision": transfer_label,
        "overall_i2_percent": overall_i2,
        "candidate_family": "information_science_lane_distill" if candidate else None,
        "candidate_family_promotion_ready": promotion_ready_flag,
        "candidate_family_i2_percent": family_i2 if candidate else None,
        "rule": (
            "Keep promotion provisional unless canonical class gates are READY, pooled transfer "
            "decision is positive, and heterogeneity is controlled (overall I2<50 and family I2<70)."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ops1",
        type=Path,
        default=Path("experiments/operations-research/f-ops1-wip-limit-s186-msw2-s3-rerun3.json"),
    )
    parser.add_argument(
        "--is5",
        type=Path,
        default=Path("experiments/information-science/f-is5-lane-distill-tags-s186-overlap-sweep.json"),
    )
    parser.add_argument(
        "--stat1",
        type=Path,
        default=Path("experiments/statistics/f-stat1-canonical-policy-s186.json"),
    )
    parser.add_argument(
        "--stat2",
        type=Path,
        default=Path("experiments/statistics/f-stat2-meta-analysis-domain-integrity-s186.json"),
    )
    parser.add_argument(
        "--stat3",
        type=Path,
        default=Path("experiments/statistics/f-stat3-multiplicity-domain-integrity-s186.json"),
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ops1 = json.loads(args.ops1.read_text(encoding="utf-8"))
    is5 = json.loads(args.is5.read_text(encoding="utf-8"))
    stat1 = json.loads(args.stat1.read_text(encoding="utf-8"))
    stat2 = json.loads(args.stat2.read_text(encoding="utf-8"))
    stat3 = json.loads(args.stat3.read_text(encoding="utf-8"))

    payload = {
        "frontier_id": "F-OPS2",
        "title": "Post-slot policy consolidation",
        "inputs": {
            "ops1": str(args.ops1),
            "is5": str(args.is5),
            "stat1": str(args.stat1),
            "stat2": str(args.stat2),
            "stat3": str(args.stat3),
        },
        "policy": {
            "wip_cap": derive_wip_policy(ops1),
            "overlap": derive_overlap_policy(is5),
            "promotion": derive_promotion_policy(stat1, stat2, stat3),
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
