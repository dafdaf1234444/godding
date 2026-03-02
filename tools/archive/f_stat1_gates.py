#!/usr/bin/env python3
"""F-STAT1: derive practical promotion gates by experiment class.

This tool replays recent experiment artifacts, extracts effect estimates,
computes confidence/power proxies, and proposes sample/effect gates for:
- live_query
- simulation_replay
- lane_log_extraction
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean, median
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Measurement:
    artifact: str
    exp_class: str
    metric: str
    n: int
    effect: float
    ci_low: float
    ci_high: float
    power: float
    notes: str


def _cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    v = sorted(values)
    if len(v) == 1:
        return float(v[0])
    pos = (len(v) - 1) * min(1.0, max(0.0, q))
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(v[lo])
    frac = pos - lo
    return float(v[lo] * (1.0 - frac) + v[hi] * frac)


def _bootstrap_diff_ci(a: list[float], b: list[float], *, seed: int = 186, resamples: int = 3000) -> tuple[float, float]:
    if not a or not b:
        return (0.0, 0.0)
    rng = random.Random(seed)
    diffs: list[float] = []
    for _ in range(max(200, resamples)):
        sa = [a[rng.randrange(len(a))] for _ in range(len(a))]
        sb = [b[rng.randrange(len(b))] for _ in range(len(b))]
        diffs.append(fmean(sb) - fmean(sa))
    return (_quantile(diffs, 0.025), _quantile(diffs, 0.975))


def _power_two_mean(a: list[float], b: list[float], alpha: float = 0.05) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    ma = fmean(a)
    mb = fmean(b)
    va = fmean([(x - ma) ** 2 for x in a])
    vb = fmean([(x - mb) ** 2 for x in b])
    pooled = math.sqrt(max(1e-9, (va + vb) / 2.0))
    d = abs(mb - ma) / pooled if pooled > 0 else 0.0
    n = min(len(a), len(b))
    z_alpha = 1.959963984540054
    return max(0.0, min(1.0, _cdf(math.sqrt(n / 2.0) * d - z_alpha)))


def _ci_diff_proportion(p1: float, n1: int, p2: float, n2: int) -> tuple[float, float]:
    if n1 <= 0 or n2 <= 0:
        return (0.0, 0.0)
    diff = p2 - p1
    se = math.sqrt(max(1e-12, p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2))
    z = 1.959963984540054
    return (diff - z * se, diff + z * se)


def _power_two_proportion(p1: float, n1: int, p2: float, n2: int, alpha: float = 0.05) -> float:
    if n1 <= 0 or n2 <= 0:
        return 0.0
    diff = abs(p2 - p1)
    se = math.sqrt(max(1e-12, p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2))
    z_alpha = 1.959963984540054 if alpha == 0.05 else 1.959963984540054
    return max(0.0, min(1.0, _cdf(diff / se - z_alpha)))


def _ci_one_proportion_vs_null(p: float, n: int, p0: float) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    se = math.sqrt(max(1e-12, p * (1 - p) / n))
    return ((p - p0) - z * se, (p - p0) + z * se)


def _power_one_proportion_vs_null(p: float, n: int, p0: float, alpha: float = 0.05) -> float:
    if n <= 0:
        return 0.0
    z_alpha = 1.959963984540054
    se0 = math.sqrt(max(1e-12, p0 * (1 - p0) / n))
    z = abs(p - p0) / se0
    return max(0.0, min(1.0, _cdf(z - z_alpha)))


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _m_fin1(path: Path, payload: dict[str, Any]) -> Measurement | None:
    if payload.get("experiment") != "F-FIN1":
        return None
    single = payload.get("single_agent", {})
    maj = payload.get("majority_vote", {})
    a = single.get("trial_accuracies")
    b = maj.get("trial_accuracies")
    if not isinstance(a, list) or not isinstance(b, list) or not a or not b:
        return None
    a_f = [float(x) for x in a]
    b_f = [float(x) for x in b]
    effect = fmean(b_f) - fmean(a_f)
    ci_low, ci_high = _bootstrap_diff_ci(a_f, b_f)
    power = _power_two_mean(a_f, b_f)
    return Measurement(
        artifact=str(path.as_posix()),
        exp_class="live_query",
        metric="accuracy_delta_n3_minus_n1",
        n=min(len(a_f), len(b_f)),
        effect=round(effect, 6),
        ci_low=round(ci_low, 6),
        ci_high=round(ci_high, 6),
        power=round(power, 6),
        notes=f"mode={payload.get('mode', 'unknown')}",
    )


def _m_ai1(path: Path, payload: dict[str, Any]) -> Measurement | None:
    if payload.get("experiment") != "F-AI1":
        return None
    async_p = payload.get("async", {})
    surf = payload.get("evidence_surfacing", {})
    n = int(payload.get("trials", 0) or 0)
    p1 = async_p.get("follower_error_rate")
    p2 = surf.get("follower_error_rate")
    if n <= 0 or p1 is None or p2 is None:
        return None
    p1f = float(p1)
    p2f = float(p2)
    # Positive = error reduction.
    effect = p1f - p2f
    ci_low, ci_high = _ci_diff_proportion(p2f, n, p1f, n)
    # `p1 - p2` direction; swap bounds.
    ci_low, ci_high = -ci_high, -ci_low
    power = _power_two_proportion(p1f, n, p2f, n)
    exp_class = "live_query" if "live" in str(payload.get("mode", "")).lower() else "simulation_replay"
    return Measurement(
        artifact=str(path.as_posix()),
        exp_class=exp_class,
        metric="error_reduction_async_minus_surfacing",
        n=n,
        effect=round(effect, 6),
        ci_low=round(ci_low, 6),
        ci_high=round(ci_high, 6),
        power=round(power, 6),
        notes="binomial-approx",
    )


def _m_ai2_threshold(path: Path, payload: dict[str, Any]) -> list[Measurement]:
    if payload.get("experiment") != "F-AI2/F-HLT2":
        return []
    runs = payload.get("runs")
    if not isinstance(runs, list):
        return []
    out: list[Measurement] = []
    for idx, row in enumerate(runs):
        if not isinstance(row, dict):
            continue
        n = int(row.get("trials", 0) or 0)
        aj = row.get("async_joint")
        sj = row.get("sync_joint")
        if n <= 0 or aj is None or sj is None:
            continue
        ajf = float(aj)
        sjf = float(sj)
        # Positive = sync penalty (cascade amplification).
        effect = sjf - ajf
        ci_low, ci_high = _ci_diff_proportion(ajf, n, sjf, n)
        power = _power_two_proportion(ajf, n, sjf, n)
        out.append(
            Measurement(
                artifact=f"{path.as_posix()}#run{idx}",
                exp_class="live_query",
                metric="joint_error_sync_minus_async",
                n=n,
                effect=round(effect, 6),
                ci_low=round(ci_low, 6),
                ci_high=round(ci_high, 6),
                power=round(power, 6),
                notes=f"sync_inherit_prob={row.get('sync_inherit_prob', 'na')}",
            )
        )
    return out


def _m_ctl1(path: Path, payload: dict[str, Any]) -> Measurement | None:
    if payload.get("frontier_id") != "F-CTL1":
        return None
    n = int(payload.get("n_sessions", 0) or 0)
    best = payload.get("best_thresholds", {})
    cur = payload.get("current_policy_reference", {})
    if n <= 0 or "alert_burden" not in best or "alert_burden" not in cur:
        return None
    p_best = float(best["alert_burden"])
    p_cur = float(cur["alert_burden"])
    effect = p_cur - p_best  # positive => burden improvement
    alert_best = int(best.get("alert_sessions", round(p_best * n)))
    alert_cur = int(cur.get("alert_sessions", round(p_cur * n)))
    ci_low, ci_high = _ci_diff_proportion(alert_best / n, n, alert_cur / n, n)
    power = _power_two_proportion(alert_best / n, n, alert_cur / n, n)
    return Measurement(
        artifact=str(path.as_posix()),
        exp_class="simulation_replay",
        metric="alert_burden_reduction_current_minus_best",
        n=n,
        effect=round(effect, 6),
        ci_low=round(ci_low, 6),
        ci_high=round(ci_high, 6),
        power=round(power, 6),
        notes=f"confidence={payload.get('data_confidence', 'unknown')}",
    )


def _m_ctl3(path: Path, payload: dict[str, Any]) -> Measurement | None:
    if payload.get("frontier_id") != "F-CTL3":
        return None
    open_s = payload.get("open_loop", {})
    closed_s = payload.get("closed_loop", {})
    n1 = int(open_s.get("n_sessions", 0) or 0)
    n2 = int(closed_s.get("n_sessions", 0) or 0)
    if n1 <= 0 or n2 <= 0:
        return None
    m_open = float(open_s.get("mean_score", 0.0) or 0.0)
    m_closed = float(closed_s.get("mean_score", 0.0) or 0.0)
    sd_open = float(open_s.get("std_score", 0.0) or 0.0)
    sd_closed = float(closed_s.get("std_score", 0.0) or 0.0)
    effect = m_closed - m_open
    se = math.sqrt(max(1e-12, (sd_open**2) / n1 + (sd_closed**2) / n2))
    z = 1.959963984540054
    ci_low, ci_high = effect - z * se, effect + z * se
    # Approximate power via standardized effect.
    pooled = math.sqrt(max(1e-12, (sd_open**2 + sd_closed**2) / 2.0))
    d = abs(effect) / pooled if pooled > 0 else 0.0
    power = _cdf(math.sqrt(min(n1, n2) / 2.0) * d - z)
    return Measurement(
        artifact=str(path.as_posix()),
        exp_class="lane_log_extraction",
        metric="quality_closed_minus_open",
        n=min(n1, n2),
        effect=round(effect, 6),
        ci_low=round(ci_low, 6),
        ci_high=round(ci_high, 6),
        power=round(max(0.0, min(1.0, power)), 6),
        notes="commit-log-proxy",
    )


def _m_is5_tags(path: Path, payload: dict[str, Any]) -> Measurement | None:
    if payload.get("experiment") != "F-IS5":
        return None
    summary = payload.get("summary_metrics", {})
    n = int(summary.get("contested_transfer_candidates", 0) or 0)
    if n <= 0:
        return None
    collision_freq = float(summary.get("merge_collision_frequency", 0.0) or 0.0)
    quality_rate = 1.0 - collision_freq
    p0 = 0.5
    effect = quality_rate - p0
    ci_low, ci_high = _ci_one_proportion_vs_null(quality_rate, n, p0)
    power = _power_one_proportion_vs_null(quality_rate, n, p0)
    return Measurement(
        artifact=str(path.as_posix()),
        exp_class="lane_log_extraction",
        metric="non_collision_rate_minus_0.5",
        n=n,
        effect=round(effect, 6),
        ci_low=round(ci_low, 6),
        ci_high=round(ci_high, 6),
        power=round(power, 6),
        notes="target=contested transfers",
    )


def _m_ctl2(path: Path, payload: dict[str, Any]) -> Measurement | None:
    if payload.get("frontier_id") != "F-CTL2":
        return None
    summary = payload.get("summary", {})
    n = int(summary.get("diff_events_total", 0) or 0)
    p = summary.get("within_1_session_rate")
    if n <= 0 or p is None:
        return None
    pf = float(p)
    p0 = 0.5
    effect = pf - p0
    ci_low, ci_high = _ci_one_proportion_vs_null(pf, n, p0)
    power = _power_one_proportion_vs_null(pf, n, p0)
    return Measurement(
        artifact=str(path.as_posix()),
        exp_class="lane_log_extraction",
        metric="within_1_session_rate_minus_0.5",
        n=n,
        effect=round(effect, 6),
        ci_low=round(ci_low, 6),
        ci_high=round(ci_high, 6),
        power=round(power, 6),
        notes="structured latency summary",
    )


def _m_evo2(path: Path, payload: dict[str, Any]) -> Measurement | None:
    if payload.get("experiment") != "F-EVO2":
        return None
    if "metrics" in payload and isinstance(payload["metrics"], dict):
        metrics = payload["metrics"]
        n = int(metrics.get("total_s186_lanes", 0) or 0)
        p = metrics.get("selection_rate_merged")
    else:
        status = payload.get("status_counts", {})
        n = int(payload.get("rows_analyzed", 0) or 0)
        merged = int(status.get("MERGED", 0) or 0)
        p = (merged / n) if n > 0 else None
    if n <= 0 or p is None:
        return None
    pf = float(p)
    p0 = 0.5
    effect = pf - p0
    ci_low, ci_high = _ci_one_proportion_vs_null(pf, n, p0)
    power = _power_one_proportion_vs_null(pf, n, p0)
    return Measurement(
        artifact=str(path.as_posix()),
        exp_class="lane_log_extraction",
        metric="selection_rate_minus_0.5",
        n=n,
        effect=round(effect, 6),
        ci_low=round(ci_low, 6),
        ci_high=round(ci_high, 6),
        power=round(power, 6),
        notes="lane-log extraction",
    )


def extract_measurements(root: Path) -> list[Measurement]:
    patterns = [
        "experiments/finance/f-fin1-factual-qa-*.json",
        "experiments/ai/f-ai1-live-evidence-surfacing-s186.json",
        "experiments/ai/f-ai2-live-partial-sync-threshold-s186.json",
        "experiments/control-theory/f-ctl1-threshold-sweep-s186*.json",
        "experiments/control-theory/f-ctl2-diff-latency-s186.json",
        "experiments/control-theory/f-ctl3-open-loop-vs-closed-loop-s186.json",
        "experiments/information-science/f-is5-lane-distill-tags-s186.json",
        "experiments/evolution/f-evo2-*.json",
    ]
    files: list[Path] = []
    for pat in patterns:
        files.extend(sorted(root.glob(pat)))
    # Remove duplicates while preserving order.
    seen: set[str] = set()
    unique_files: list[Path] = []
    for f in files:
        key = str(f.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique_files.append(f)

    measurements: list[Measurement] = []
    for path in unique_files:
        payload = _load_json(path)
        if payload is None:
            continue
        for fn in (
            _m_fin1,
            _m_ai1,
            _m_ctl1,
            _m_ctl2,
            _m_ctl3,
            _m_is5_tags,
            _m_evo2,
        ):
            m = fn(path, payload)
            if m is not None:
                measurements.append(m)
                break
        else:
            # Some extractors return multiple rows.
            ai2_rows = _m_ai2_threshold(path, payload)
            measurements.extend(ai2_rows)
    return measurements


def _derive_gate(class_rows: list[Measurement]) -> dict[str, Any]:
    n_values = [m.n for m in class_rows]
    abs_effects = [abs(m.effect) for m in class_rows]
    passing = [
        m for m in class_rows if m.power >= 0.8 and (m.ci_low > 0.0 or m.ci_high < 0.0)
    ]

    if passing:
        gate_n = int(round(median([m.n for m in passing])))
        gate_effect = round(float(median([abs(m.effect) for m in passing])), 4)
        confidence = "HIGH" if len(passing) >= 3 else "MEDIUM"
    else:
        gate_n = int(round(max(6.0, _quantile([float(n) for n in n_values], 0.75))))
        gate_effect = round(max(0.05, _quantile(abs_effects, 0.75)), 4)
        confidence = "LOW"

    return {
        "recommended_min_n": max(1, gate_n),
        "recommended_min_abs_effect": gate_effect,
        "confidence": confidence,
        "evidence_rows": len(class_rows),
        "passing_rows": len(passing),
        "median_observed_n": round(float(median(n_values)), 2) if n_values else 0.0,
        "median_observed_abs_effect": round(float(median(abs_effects)), 4) if abs_effects else 0.0,
    }


def derive_gates(measurements: list[Measurement]) -> dict[str, Any]:
    grouped: dict[str, list[Measurement]] = {
        "live_query": [],
        "simulation_replay": [],
        "lane_log_extraction": [],
    }
    for m in measurements:
        grouped.setdefault(m.exp_class, []).append(m)

    gates = {key: _derive_gate(rows) for key, rows in grouped.items() if rows}
    # Ensure all expected classes exist.
    for key in ("live_query", "simulation_replay", "lane_log_extraction"):
        gates.setdefault(
            key,
            {
                "recommended_min_n": 0,
                "recommended_min_abs_effect": 0.0,
                "confidence": "NONE",
                "evidence_rows": 0,
                "passing_rows": 0,
                "median_observed_n": 0.0,
                "median_observed_abs_effect": 0.0,
            },
        )
    return gates


def run(*, out_path: Path) -> dict[str, Any]:
    measurements = extract_measurements(REPO_ROOT)
    gates = derive_gates(measurements)
    payload = {
        "frontier_id": "F-STAT1",
        "title": "Sample-size and effect-size promotion gates by experiment class",
        "classes": gates,
        "measurements": [asdict(m) for m in measurements],
        "notes": (
            "Gate pass criterion for evidence rows: power>=0.8 and CI excludes 0. "
            "When no rows pass, fallback uses 75th-percentile n/effect for conservative provisional gates."
        ),
    }
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        default="experiments/statistics/f-stat1-gates-s186.json",
        help="Output artifact path",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out = run(out_path=REPO_ROOT / args.out)
    print(f"Wrote {args.out}")
    for key, row in out["classes"].items():
        print(
            key,
            f"n>={row['recommended_min_n']}",
            f"|effect|>={row['recommended_min_abs_effect']}",
            f"confidence={row['confidence']}",
            f"rows={row['evidence_rows']}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

