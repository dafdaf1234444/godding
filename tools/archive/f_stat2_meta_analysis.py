#!/usr/bin/env python3
"""F-STAT2: random-effects pooling across domain swarm artifacts."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SE_FLOOR = 1e-3


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sample_variance(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = fmean(values)
    return sum((x - mean) ** 2 for x in values) / (len(values) - 1)


def _se_floor_for_n(n: int) -> float:
    # Prevent tiny-N artifacts from dominating pooled weights.
    n = max(1, n)
    return max(0.02, 0.2 / math.sqrt(n))


def _se_from_var(v1: float, n1: int, v2: float, n2: int) -> float:
    n1 = max(1, n1)
    n2 = max(1, n2)
    se = math.sqrt(max(0.0, v1 / n1 + v2 / n2))
    return max(SE_FLOOR, _se_floor_for_n(min(n1, n2)), se)


def _detect_fin1_regime(payload: dict[str, Any], path: Path) -> str:
    mode = str(payload.get("mode", "")).strip().lower()
    if "direct-answer" in mode or "direct_answer" in mode:
        return "direct_answer"
    if mode:
        return "resolver_proxy"

    interpretation = str(payload.get("interpretation", "")).lower()
    if "direct answer" in interpretation or "direct capital answers" in interpretation:
        return "direct_answer"
    if "resolver proxy" in interpretation:
        return "resolver_proxy"

    name = path.name.lower()
    if "-direct-" in name or name.startswith("f-fin1-factual-qa-direct"):
        return "direct_answer"
    return "unknown"


def fin1_studies() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((REPO_ROOT / "experiments" / "finance").glob("f-fin1-factual-qa*.json")):
        payload = _load_json(path)
        single = payload.get("single_agent") or {}
        majority = payload.get("majority_vote") or {}
        if not isinstance(single, dict) or not isinstance(majority, dict):
            continue

        mean1 = _safe_float((single.get("summary") or {}).get("mean"), math.nan)
        mean3 = _safe_float((majority.get("summary") or {}).get("mean"), math.nan)
        if math.isnan(mean1) or math.isnan(mean3):
            continue
        effect = mean3 - mean1

        acc1 = [float(x) for x in (single.get("trial_accuracies") or []) if isinstance(x, (int, float))]
        acc3 = [float(x) for x in (majority.get("trial_accuracies") or []) if isinstance(x, (int, float))]
        n1 = len(acc1)
        n3 = len(acc3)

        v1 = _sample_variance(acc1)
        v3 = _sample_variance(acc3)
        if v1 is None:
            v1 = _safe_float((single.get("summary") or {}).get("variance"), 0.0)
        if v3 is None:
            v3 = _safe_float((majority.get("summary") or {}).get("variance"), 0.0)

        if n1 <= 0:
            n1 = _safe_int(payload.get("trials_per_condition"), 1)
        if n3 <= 0:
            n3 = _safe_int(payload.get("trials_per_condition"), 1)
        se = _se_from_var(v1, n1, v3, n3)
        regime = _detect_fin1_regime(payload, path)
        family = f"finance_factual_qa_{regime}"

        rows.append(
            {
                "study_id": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "family": family,
                "scoring_regime": regime,
                "effect": _round(effect),
                "se": _round(se),
                "n": int(max(n1, n3)),
                "metric": "mean_accuracy_n3_minus_n1",
            }
        )
    return rows


def is5_studies() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((REPO_ROOT / "experiments" / "information-science").glob("f-is5-lane-distill*.json")):
        payload = _load_json(path)
        summary = payload.get("summary_metrics")
        if not isinstance(summary, dict):
            continue
        p_accept = _safe_float(summary.get("transfer_acceptance_rate"), math.nan)
        p_collide = _safe_float(summary.get("merge_collision_frequency"), math.nan)
        if math.isnan(p_accept) or math.isnan(p_collide):
            continue
        effect = p_accept - p_collide

        n_accept = _safe_int(summary.get("transfer_candidates"), 0)
        if n_accept <= 0:
            n_accept = _safe_int(summary.get("claims_total"), 1)
        n_collide = _safe_int(summary.get("contested_transfer_candidates"), 0)
        if n_collide <= 0:
            n_collide = n_accept

        v_accept = max(0.0, p_accept * (1.0 - p_accept) / max(1, n_accept))
        v_collide = max(0.0, p_collide * (1.0 - p_collide) / max(1, n_collide))
        n_eff = min(n_accept, n_collide)
        se = max(SE_FLOOR, _se_floor_for_n(n_eff), math.sqrt(v_accept + v_collide))

        rows.append(
            {
                "study_id": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "family": "information_science_lane_distill",
                "effect": _round(effect),
                "se": _round(se),
                "n": int(max(n_accept, n_collide)),
                "metric": "transfer_acceptance_rate_minus_collision_frequency",
            }
        )
    return rows


def ctl1_studies() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((REPO_ROOT / "experiments" / "control-theory").glob("f-ctl1-threshold-sweep*.json")):
        payload = _load_json(path)
        current = payload.get("current_policy_reference") or {}
        best = payload.get("best_thresholds") or {}
        p_current = _safe_float(current.get("alert_burden"), math.nan)
        p_best = _safe_float(best.get("alert_burden"), math.nan)
        if math.isnan(p_current) or math.isnan(p_best):
            continue
        n = max(1, _safe_int(payload.get("n_sessions"), 1))
        effect = p_current - p_best
        se = max(
            SE_FLOOR,
            _se_floor_for_n(n),
            math.sqrt(
                max(0.0, p_current * (1.0 - p_current) / n)
                + max(0.0, p_best * (1.0 - p_best) / n)
            ),
        )
        rows.append(
            {
                "study_id": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "family": "control_threshold_sweep",
                "effect": _round(effect),
                "se": _round(se),
                "n": n,
                "metric": "current_alert_burden_minus_best_alert_burden",
            }
        )
    return rows


def random_effects(studies: list[dict[str, Any]]) -> dict[str, Any]:
    if not studies:
        return {
            "k": 0,
            "pooled_effect": 0.0,
            "pooled_se": 0.0,
            "ci95": [0.0, 0.0],
            "tau2": 0.0,
            "Q": 0.0,
            "I2_percent": 0.0,
        }

    y = [_safe_float(s["effect"]) for s in studies]
    v = [max(SE_FLOOR**2, _safe_float(s["se"]) ** 2) for s in studies]
    w = [1.0 / vi for vi in v]
    w_sum = sum(w)
    mu_fixed = sum(wi * yi for wi, yi in zip(w, y)) / w_sum
    q = sum(wi * ((yi - mu_fixed) ** 2) for wi, yi in zip(w, y))
    df = len(studies) - 1
    c = w_sum - (sum(wi**2 for wi in w) / w_sum) if w_sum > 0 else 0.0
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0

    w_star = [1.0 / (vi + tau2) for vi in v]
    w_star_sum = sum(w_star)
    mu = sum(ws * yi for ws, yi in zip(w_star, y)) / w_star_sum
    se_mu = math.sqrt(1.0 / w_star_sum)
    ci = [mu - 1.96 * se_mu, mu + 1.96 * se_mu]
    i2 = max(0.0, ((q - df) / q) * 100.0) if q > 0 and df > 0 else 0.0

    return {
        "k": len(studies),
        "pooled_effect": _round(mu),
        "pooled_se": _round(se_mu),
        "ci95": [_round(ci[0]), _round(ci[1])],
        "tau2": _round(tau2),
        "Q": _round(q),
        "I2_percent": _round(i2),
    }


def _summarize_finance_regimes(studies: list[dict[str, Any]]) -> dict[str, Any]:
    by_regime: dict[str, list[dict[str, Any]]] = {}
    for row in studies:
        family = str(row.get("family", ""))
        if not family.startswith("finance_factual_qa_"):
            continue
        regime = str(row.get("scoring_regime", "unknown"))
        by_regime.setdefault(regime, []).append(row)

    regimes = {regime: random_effects(rows) for regime, rows in sorted(by_regime.items())}
    delta = None
    if "direct_answer" in regimes and "resolver_proxy" in regimes:
        delta = _round(regimes["direct_answer"]["pooled_effect"] - regimes["resolver_proxy"]["pooled_effect"])

    return {
        "regimes": regimes,
        "pooled_effect_delta_direct_minus_proxy": delta,
    }


def _transfer_label(ci_low: float, ci_high: float, i2: float) -> str:
    if ci_low > 0:
        return "positive-transfer-signal" if i2 < 75 else "positive-but-heterogeneous"
    if ci_high < 0:
        return "negative-transfer-signal"
    return "inconclusive"


def run(out_path: Path) -> dict[str, Any]:
    studies = fin1_studies() + is5_studies() + ctl1_studies()
    overall = random_effects(studies)

    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in studies:
        by_family.setdefault(row["family"], []).append(row)
    family_summaries = {
        family: random_effects(rows) for family, rows in sorted(by_family.items())
    }
    finance_regime_split = _summarize_finance_regimes(studies)

    ci_low, ci_high = overall["ci95"]
    result = {
        "frontier_id": "F-STAT2",
        "title": "Cross-domain random-effects meta-analysis",
        "study_count": len(studies),
        "families": {k: len(v) for k, v in sorted(by_family.items())},
        "overall": overall,
        "by_family": family_summaries,
        "finance_regime_split": finance_regime_split,
        "transfer_decision": {
            "label": _transfer_label(ci_low, ci_high, overall["I2_percent"]),
            "rule": "ci95 above zero => positive; below zero => negative; crossing zero => inconclusive",
        },
        "studies": studies,
        "notes": (
            "Effects are normalized as improvement deltas from each artifact family. "
            "FIN1 studies are split into direct-answer vs resolver-proxy regimes. "
            "SEs are approximated from available trial/count fields; interpretation should be "
            "paired with F-STAT3 multiplicity controls."
        ),
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
        default=Path("experiments/statistics/f-stat2-meta-analysis-s186.json"),
        help="Output artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(REPO_ROOT / args.out)
    print(f"Wrote {args.out}")
    print(
        "studies=",
        result["study_count"],
        "pooled_effect=",
        result["overall"]["pooled_effect"],
        "ci95=",
        result["overall"]["ci95"],
        "decision=",
        result["transfer_decision"]["label"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
