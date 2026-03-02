#!/usr/bin/env python3
"""F-STAT3: multiplicity control and replication gating for pooled studies."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _z_to_p_two_sided(z: float) -> float:
    # p = 2 * (1 - Phi(|z|)) via complementary error function.
    return min(1.0, max(0.0, math.erfc(abs(z) / math.sqrt(2.0))))


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    q_sorted = [1.0] * m
    running = 1.0
    for i in range(m - 1, -1, -1):
        rank = i + 1
        idx, p = indexed[i]
        raw = (p * m) / rank
        running = min(running, raw)
        q_sorted[i] = min(1.0, running)
    out = [1.0] * m
    for i, (idx, _p) in enumerate(indexed):
        out[idx] = q_sorted[i]
    return out


def _family_summary(
    rows: list[dict[str, Any]],
    *,
    alpha: float,
    nominal_alpha: float,
    min_replications: int,
) -> dict[str, Any]:
    if not rows:
        return {
            "study_count": 0,
            "weighted_mean_effect": 0.0,
            "replication_count": 0,
            "replication_rate": 0.0,
            "bh_discoveries": 0,
            "bonferroni_discoveries": 0,
            "promotion_ready": False,
        }

    weights = [1.0 / max(1e-9, r["se"] ** 2) for r in rows]
    w_sum = sum(weights)
    weighted_mean = sum(w * r["effect"] for w, r in zip(weights, rows)) / w_sum if w_sum > 0 else 0.0
    sign = 1 if weighted_mean > 0 else -1 if weighted_mean < 0 else 0

    rep_rows = [
        r
        for r in rows
        if (1 if r["effect"] > 0 else -1 if r["effect"] < 0 else 0) == sign
        and r["p_two_sided"] <= nominal_alpha
    ]

    bh_discoveries = sum(1 for r in rows if r["q_bh"] <= alpha)
    bonf_discoveries = sum(1 for r in rows if r["p_bonferroni"] <= alpha)
    promotion_ready = bh_discoveries >= 1 and len(rep_rows) >= min_replications

    return {
        "study_count": len(rows),
        "weighted_mean_effect": _round(weighted_mean),
        "replication_count": len(rep_rows),
        "replication_rate": _round(len(rep_rows) / len(rows)),
        "bh_discoveries": bh_discoveries,
        "bonferroni_discoveries": bonf_discoveries,
        "promotion_ready": promotion_ready,
    }


def run(
    meta_path: Path,
    out_path: Path,
    *,
    alpha: float = 0.05,
    nominal_alpha: float = 0.1,
    min_replications: int = 2,
) -> dict[str, Any]:
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    studies = payload.get("studies") or []
    if not isinstance(studies, list):
        studies = []

    rows: list[dict[str, Any]] = []
    for item in studies:
        if not isinstance(item, dict):
            continue
        effect = _safe_float(item.get("effect"))
        se = max(1e-6, _safe_float(item.get("se"), 1e-3))
        z = effect / se
        p = _z_to_p_two_sided(z)
        rows.append(
            {
                "study_id": str(item.get("study_id", "")),
                "family": str(item.get("family", "unknown")),
                "metric": str(item.get("metric", "")),
                "n": int(_safe_float(item.get("n"), 0)),
                "effect": effect,
                "se": se,
                "z_score": z,
                "p_two_sided": p,
            }
        )

    p_values = [r["p_two_sided"] for r in rows]
    q_values = benjamini_hochberg(p_values)
    m = len(rows)
    for i, row in enumerate(rows):
        row["q_bh"] = q_values[i]
        row["p_bonferroni"] = min(1.0, row["p_two_sided"] * max(1, m))
        row["discovery_bh"] = row["q_bh"] <= alpha
        row["discovery_bonferroni"] = row["p_bonferroni"] <= alpha
        row["direction"] = "positive" if row["effect"] > 0 else "negative" if row["effect"] < 0 else "neutral"
        row["effect"] = _round(row["effect"])
        row["se"] = _round(row["se"])
        row["z_score"] = _round(row["z_score"])
        row["p_two_sided"] = _round(row["p_two_sided"])
        row["q_bh"] = _round(row["q_bh"])
        row["p_bonferroni"] = _round(row["p_bonferroni"])

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[row["family"]].append(row)
    family_summary = {
        fam: _family_summary(
            fam_rows,
            alpha=alpha,
            nominal_alpha=nominal_alpha,
            min_replications=min_replications,
        )
        for fam, fam_rows in sorted(by_family.items())
    }

    overall = {
        "study_count": len(rows),
        "bh_discoveries": sum(1 for r in rows if r["discovery_bh"]),
        "bonferroni_discoveries": sum(1 for r in rows if r["discovery_bonferroni"]),
        "bh_discovery_rate": _round(
            (sum(1 for r in rows if r["discovery_bh"]) / len(rows)) if rows else 0.0
        ),
        "bonferroni_discovery_rate": _round(
            (sum(1 for r in rows if r["discovery_bonferroni"]) / len(rows)) if rows else 0.0
        ),
    }

    promotion_candidates = [fam for fam, summary in family_summary.items() if summary["promotion_ready"]]
    result = {
        "frontier_id": "F-STAT3",
        "title": "Multiplicity control over pooled domain studies",
        "inputs": {
            "meta_analysis_artifact": str(meta_path).replace("\\", "/"),
            "alpha": alpha,
            "nominal_alpha_for_replication": nominal_alpha,
            "min_replications_for_promotion": min_replications,
        },
        "overall": overall,
        "by_family": family_summary,
        "promotion_candidates": promotion_candidates,
        "recommendation": {
            "label": "no-family-ready" if not promotion_candidates else "candidate-families-present",
            "note": (
                "Require BH discovery + replication gate before promotion. "
                "Apply class-splitting where regimes are mixed (for example FIN1 proxy/direct)."
            ),
        },
        "studies": rows,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--meta",
        type=Path,
        default=Path("experiments/statistics/f-stat2-meta-analysis-s186.json"),
        help="Input meta-analysis artifact path",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/statistics/f-stat3-multiplicity-s186.json"),
        help="Output artifact path",
    )
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--nominal-alpha", type=float, default=0.1)
    parser.add_argument("--min-replications", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(
        REPO_ROOT / args.meta,
        REPO_ROOT / args.out,
        alpha=max(0.0, min(1.0, args.alpha)),
        nominal_alpha=max(0.0, min(1.0, args.nominal_alpha)),
        min_replications=max(1, args.min_replications),
    )
    print(f"Wrote {args.out}")
    print(
        "studies=",
        result["overall"]["study_count"],
        "bh_discoveries=",
        result["overall"]["bh_discoveries"],
        "bonferroni_discoveries=",
        result["overall"]["bonferroni_discoveries"],
        "promotion_candidates=",
        len(result["promotion_candidates"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
