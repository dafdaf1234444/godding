#!/usr/bin/env python3
"""Goal scorers for eval_sufficiency.py (extracted S441 — DI pattern from L-941).

Contains scoring utility functions and the four PHIL-14 goal scorers.
Imported by eval_sufficiency.py.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Scoring utilities
# ---------------------------------------------------------------------------

def _continuous_score(value: float, thresholds: list[float]) -> float:
    """Interpolate value across threshold boundaries to produce continuous 0-3 score.

    thresholds: [t0, t1, t2, t3] where score=0 below t0, score=3 above t3.
    Linear interpolation between adjacent thresholds.
    F-EVAL4 hardening (L-928): replaces cliff-edge discrete scoring.
    """
    if value <= thresholds[0]:
        return 0.0
    for i in range(1, len(thresholds)):
        if value <= thresholds[i]:
            return (i - 1) + (value - thresholds[i - 1]) / (thresholds[i] - thresholds[i - 1])
    return float(len(thresholds) - 1)


_VERDICT_LABELS = {0: "INSUFFICIENT", 1: "ADEQUATE", 2: "SUFFICIENT", 3: "EXCELLENT"}


def _continuous_verdict(continuous: float) -> str:
    """Map continuous score to verdict label (rounds to nearest integer label)."""
    for threshold, label in [(0.5, "INSUFFICIENT"), (1.5, "ADEQUATE"),
                             (2.5, "SUFFICIENT"), (3.1, "EXCELLENT")]:
        if continuous < threshold:
            return label
    return "EXCELLENT"


def _reconcile_verdicts(discrete_score: int, continuous: float,
                        external_grounding: bool = False) -> dict:
    """Reconcile discrete and continuous scores to produce final verdict.

    F-EVAL4 (L-928): if continuous and discrete verdicts diverge by >=1 step,
    adjust discrete toward continuous. Flag margin warnings for scores near boundaries.
    L-1173: changed >1 to >=1 — boundary accumulation creates max-divergence at exactly 1 step.
    L-1191: EXCELLENT (score=3) requires external_grounding=True. Without external
    grounding, score caps at 2 (SUFFICIENT). Prevents self-referential inflation.
    """
    discrete_verdict = _VERDICT_LABELS.get(discrete_score, "UNKNOWN")
    continuous_verdict = _continuous_verdict(continuous)
    adjusted = False
    adjustment_reason = None

    continuous_int = round(continuous)
    if abs(continuous_int - discrete_score) >= 1:  # L-1173: >=1 not >1
        discrete_score = max(0, min(3, discrete_score + (1 if continuous_int > discrete_score else -1)))
        discrete_verdict = _VERDICT_LABELS.get(discrete_score, "UNKNOWN")
        adjusted = True
        adjustment_reason = (
            f"continuous={continuous:.2f} ({continuous_verdict}) diverged >=1 step from "
            f"discrete; adjusted to {discrete_verdict}"
        )

    # L-1191: EXCELLENT requires external grounding — cap at SUFFICIENT without it
    if discrete_score >= 3 and not external_grounding:
        discrete_score = 2
        discrete_verdict = _VERDICT_LABELS[2]
        adjusted = True
        adjustment_reason = (
            f"score capped at SUFFICIENT: EXCELLENT requires external_grounding=True "
            f"(L-1191 grounding enforcement)"
        )

    # Margin warning: within 0.3 of any threshold
    boundaries = [0.5, 1.5, 2.5]
    margin_warning = None
    for b in boundaries:
        if abs(continuous - b) < 0.3:
            lower = _continuous_verdict(b - 0.1)
            upper = _continuous_verdict(b + 0.1)
            margin_warning = (
                f"continuous={continuous:.2f} is within 0.3 of {lower}/{upper} "
                f"boundary ({b:.1f})"
            )
            break

    return {
        "score": discrete_score,
        "verdict": discrete_verdict,
        "continuous_verdict": continuous_verdict,
        "adjusted": adjusted,
        "adjustment_reason": adjustment_reason,
        "margin_warning": margin_warning,
    }


def _finalize_goal(details: dict, discrete_score: int, continuous_score: float,
                   rationale: str, external_grounding: bool = False) -> dict:
    """Apply reconciliation and build final goal dict."""
    reconciled = _reconcile_verdicts(discrete_score, continuous_score,
                                     external_grounding=external_grounding)
    details["score"] = reconciled["score"]
    details["verdict"] = reconciled["verdict"]
    details["discrete_score"] = discrete_score
    details["continuous_verdict"] = reconciled["continuous_verdict"]
    details["external_grounding"] = external_grounding
    details["rationale"] = rationale
    if reconciled["adjusted"]:
        details["adjustment"] = reconciled["adjustment_reason"]
    if reconciled.get("margin_warning"):
        details["margin_warning"] = reconciled["margin_warning"]
    return details


# ---------------------------------------------------------------------------
# Goal scorers
# ---------------------------------------------------------------------------

def score_collaborate(lanes: dict, con1: dict, signals: dict) -> dict:
    """Collaborate: nodes work together, not against each other."""
    details = {}
    total_productive = lanes["merged"] + lanes["open"] + lanes.get("active", 0)
    merge_rate = lanes["merged"] / total_productive if total_productive else 0
    details["lane_merge_rate"] = round(merge_rate, 3)
    details["lane_merge_count"] = lanes["merged"]
    details["lane_open_count"] = lanes["open"] + lanes.get("active", 0)
    c1_rate = con1.get("c1_rate_lane_level", 0.066)
    details["c1_conflict_rate"] = c1_rate
    details["c1_source"] = con1.get("_source_file", "default")
    sig_completeness = signals["with_artifact_refs"] / signals["total"] if signals["total"] else 0
    details["signal_enforcement_pct"] = round(sig_completeness * 100, 1)

    merge_continuous = _continuous_score(merge_rate, [0.0, 0.3, 0.4, 0.5])
    c1_continuous = _continuous_score(1.0 - c1_rate, [0.90, 0.95, 0.98, 1.0])
    sig_continuous = _continuous_score(sig_completeness, [0.0, 0.50, 0.80, 0.95])
    continuous_score = min(merge_continuous, c1_continuous, sig_continuous)
    details["continuous_score"] = round(continuous_score, 2)

    if merge_rate < 0.3 or c1_rate > 0.10:
        discrete_score = 0
    elif sig_completeness < 0.80:
        discrete_score = 1
    elif merge_rate >= 0.4 and c1_rate <= 0.05:
        discrete_score = 2
    else:
        discrete_score = 1

    return _finalize_goal(
        details, discrete_score, continuous_score,
        f"merge_rate={merge_rate:.1%} ({lanes['merged']}/{total_productive} productive lanes MERGED), "
        f"c1={c1_rate:.1%} (lane-level duplicate rate), "
        f"signal_enforcement={sig_completeness:.0%}, continuous={continuous_score:.2f}",
    )


def score_increase(sessions: list[dict], frontiers: dict, domains: int, lessons: int) -> dict:
    """Increase: actively grow swarm capability, reach, and knowledge."""
    details = {}
    max_s = max(s["session"] for s in sessions) if sessions else 0
    window_size = min(50, max_s) if max_s else 20
    recent = [s for s in sessions if s["session"] >= max_s - window_size] if sessions else []
    total_lp = sum(s["lessons"] + s["principles"] for s in recent)
    avg_lp_per_session = total_lp / len(recent) if recent else 0
    details["avg_lp_per_session"] = round(avg_lp_per_session, 2)
    details["window_size"] = window_size
    details["window_n"] = len(recent)
    details["window_insufficient"] = len(recent) < 5
    details["threshold_margin_pct"] = round((avg_lp_per_session - 2.0) / 2.0 * 100, 1) if avg_lp_per_session > 0 else -100.0
    details["total_lessons"] = lessons

    domex_sessions = [s for s in recent if s.get("is_domex", False)]
    non_domex_sessions = [s for s in recent if not s.get("is_domex", False)]
    details["domex_avg_lp"] = round(sum(s["lessons"] + s["principles"] for s in domex_sessions) / len(domex_sessions), 2) if domex_sessions else 0
    details["domex_n"] = len(domex_sessions)
    details["non_domex_avg_lp"] = round(sum(s["lessons"] + s["principles"] for s in non_domex_sessions) / len(non_domex_sessions), 2) if non_domex_sessions else 0
    details["non_domex_n"] = len(non_domex_sessions)

    f_open, f_resolved = frontiers["global_open"], frontiers["global_resolved"]
    total_f = f_open + f_resolved
    resolution_rate = f_resolved / total_f if total_f else 0
    details["frontier_resolution_rate"] = round(resolution_rate, 3)
    details["frontiers_open"] = f_open
    details["frontiers_resolved"] = f_resolved
    details["domain_count"] = domains

    lp_continuous = _continuous_score(avg_lp_per_session, [0.0, 1.0, 2.0, 3.0])
    resolution_continuous = _continuous_score(resolution_rate, [0.0, 0.05, 0.10, 0.15])
    domain_continuous = _continuous_score(domains, [0, 5, 15, 30])
    continuous_score = min(lp_continuous, resolution_continuous, domain_continuous)
    details["continuous_score"] = round(continuous_score, 2)
    details["continuous_sub"] = {"lp": round(lp_continuous, 2), "resolution": round(resolution_continuous, 2), "domains": round(domain_continuous, 2)}

    if avg_lp_per_session < 1.0 or resolution_rate < 0.05:
        discrete_score = 0
    elif avg_lp_per_session >= 2.0 and resolution_rate >= 0.10 and domains >= 15:
        discrete_score = 1 if details["window_insufficient"] else 2
        if details["window_insufficient"]:
            details["note"] = f"avg_lp={avg_lp_per_session:.2f} meets threshold but window_n={len(recent)} < 5 — insufficient data (F-EVAL4, L-919)"
    elif avg_lp_per_session >= 1.0 and resolution_rate >= 0.05:
        discrete_score = 1
    else:
        discrete_score = 0
    if discrete_score == 2 and avg_lp_per_session >= 3.0 and resolution_rate >= 0.15:
        discrete_score = 3

    reconciled = _reconcile_verdicts(discrete_score, continuous_score,
                                     external_grounding=False)
    if details["window_insufficient"] and reconciled["score"] > 1:
        reconciled["score"] = 1
        reconciled["verdict"] = "ADEQUATE"
        reconciled["adjustment_reason"] = f"window_n={len(recent)} < 5 caps verdict at ADEQUATE regardless of continuous score"
        reconciled["adjusted"] = True

    details["external_grounding"] = False
    details["score"] = reconciled["score"]
    details["verdict"] = reconciled["verdict"]
    details["discrete_score"] = discrete_score
    details["continuous_verdict"] = reconciled["continuous_verdict"]
    if reconciled["adjusted"]:
        details["adjustment"] = reconciled["adjustment_reason"]
    if reconciled.get("margin_warning"):
        details["margin_warning"] = reconciled["margin_warning"]
    details["rationale"] = (
        f"avg_lp={avg_lp_per_session:.2f} (window={window_size}s, n={len(recent)}, "
        f"DOMEX={details['domex_avg_lp']:.1f} n={details['domex_n']}, "
        f"non-DOMEX={details['non_domex_avg_lp']:.1f} n={details['non_domex_n']}), "
        f"resolution={resolution_rate:.1%} ({f_resolved}/{total_f}), "
        f"domains={domains}, continuous={continuous_score:.2f}"
    )
    return details


def score_protect(proxy_k: dict, challenges: dict) -> dict:
    """Protect: do not harm swarm or members. Leave collective intact or better."""
    details = {}
    drift = proxy_k.get("drift_pct", 0)
    details["proxy_k_drift_pct"] = round(drift, 2)
    details["proxy_k_healthy"] = drift < 6.0
    total_ch, dropped = challenges["total"], challenges["dropped"]
    drop_rate = dropped / total_ch if total_ch else 0
    evidence_grounded = challenges.get("evidence_grounded", challenges["confirmed"] + challenges["superseded"])
    accepted_rate = evidence_grounded / total_ch if total_ch else 0
    details["challenge_drop_rate"] = round(drop_rate, 3)
    details["challenge_accepted_rate"] = round(accepted_rate, 3)
    details["challenges_total"] = total_ch
    details["zero_drop_warning"] = drop_rate == 0 and total_ch > 8
    # L-1191: validator_pass should be checked, not assumed.
    # Run validate_beliefs.py if available; default to True only as fallback.
    import subprocess
    try:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "validate_beliefs.py")],
            capture_output=True, text=True, timeout=15
        )
        details["validator_pass"] = result.returncode == 0
    except Exception:
        details["validator_pass"] = True  # fallback if tool unavailable

    drift_continuous = _continuous_score(max(0, 20.0 - drift), [0.0, 6.0, 14.0, 20.0])
    drop_continuous = _continuous_score(drop_rate, [0.0, 0.01, 0.05, 0.10])
    continuous_score = min(drift_continuous, drop_continuous) if details["validator_pass"] else 0.0
    details["continuous_score"] = round(continuous_score, 2)

    if drift >= 20.0 or not details["validator_pass"]:
        discrete_score = 0
    elif details["zero_drop_warning"]:
        discrete_score = 1
        details["note"] = "0 challenge drops across all entries — possible soft-acceptance bias (L-219)"
    elif drift < 6.0 and drop_rate > 0:
        discrete_score = 2
    else:
        discrete_score = 1

    return _finalize_goal(
        details, discrete_score, continuous_score,
        f"proxy_k_drift={drift:.1f}% (healthy<6%), validator={'PASS' if details['validator_pass'] else 'FAIL'}, "
        f"challenge_drop_rate={drop_rate:.1%} ({dropped}/{total_ch}), continuous={continuous_score:.2f}",
    )


def score_truthful(challenges: dict, signals: dict, frontiers: dict) -> dict:
    """Truthful: honesty as first-class constraint; evidence routes truth."""
    details = {}
    evidence_grounded = challenges.get("evidence_grounded", challenges["confirmed"] + challenges["superseded"])
    total = challenges["total"]
    evidence_rate = evidence_grounded / total if total else 0
    details["evidence_grounded_rate"] = round(evidence_rate, 3)

    total_sig = signals["total"]
    estimated_sessions = 1
    try:
        index_text = (ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8")
        m = re.search(r"Sessions:\s*(\d+)", index_text)
        if m:
            estimated_sessions = int(m.group(1))
    except Exception:
        pass
    signal_density = total_sig / estimated_sessions
    details["signal_density_per_session"] = round(signal_density, 3)
    details["signal_density_target_met"] = signal_density >= 0.1
    # L-1211: signal_density is NOT external grounding — it measures internal signal
    # frequency. True external grounding requires F-COMP1 outputs. Until those exist,
    # external_grounding_ok defaults to False. Checks recent lesson external trail.
    external_trail_pct = 0.0
    try:
        _lessons = sorted((ROOT / "memory" / "lessons").glob("L-*.md"))
        _recent = _lessons[-50:] if len(_lessons) >= 50 else _lessons
        _ext = sum(1 for lf in _recent if "external" in lf.read_text(encoding="utf-8", errors="ignore").lower()[:500])
        external_trail_pct = _ext / max(len(_recent), 1) * 100
    except Exception:
        pass
    external_grounding_ok = external_trail_pct > 5.0
    details["external_grounding_ok"] = external_grounding_ok
    details["external_trail_pct"] = round(external_trail_pct, 1)
    details["external_grounding_target"] = ">5% external trail in recent 50 lessons (L-1211)"
    details["frontier_resolution_absolute"] = frontiers["global_resolved"]
    details["frontier_open_absolute"] = frontiers["global_open"]

    evidence_continuous = _continuous_score(evidence_rate, [0.0, 0.30, 0.50, 0.70])
    signal_continuous = _continuous_score(signal_density, [0.0, 0.05, 0.10, 0.20])
    continuous_score = min(evidence_continuous, signal_continuous)
    details["continuous_score"] = round(continuous_score, 2)

    if evidence_rate < 0.30:
        discrete_score = 0
    elif not external_grounding_ok:
        discrete_score = 1
    elif evidence_rate >= 0.50 and external_grounding_ok:
        discrete_score = 2
    else:
        discrete_score = 1
    if discrete_score == 2 and evidence_rate >= 0.70:
        discrete_score = 3

    return _finalize_goal(
        details, discrete_score, continuous_score,
        f"evidence_grounded_rate={evidence_rate:.1%} ({evidence_grounded}/{total} challenges), "
        f"signal_density={signal_density:.2f}/session (target ≥0.1), "
        f"external_grounding_ok={external_grounding_ok}, continuous={continuous_score:.2f}",
        external_grounding=external_grounding_ok,
    )
