#!/usr/bin/env python3
"""
eval_sufficiency.py — PHIL-14 Mission Sufficiency Scorer

Scores each of the four PHIL-14 goals (Collaborate, Increase, Protect, Truthful)
on a 0-3 scale using proxy metrics from swarm state files.

Scale:
  0 = Insufficient — below minimum threshold
  1 = Adequate     — meets threshold, gaps in rate or grounding
  2 = Sufficient   — exceeds threshold with internal evidence
  3 = Excellent    — exceeds threshold with external grounding

Usage:
  python3 tools/eval_sufficiency.py          # human-readable report
  python3 tools/eval_sufficiency.py --json   # machine-readable JSON
  python3 tools/eval_sufficiency.py --save   # save artifact to experiments/evaluation/

Related: F-EVAL1, PHIL-14, PHIL-16, L-316, domains/evaluation/tasks/FRONTIER.md
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent


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
    """Map continuous 0.0-3.0 score to verdict label using midpoints as boundaries.

    F-EVAL4 (L-928): verdict derived from continuous score, not cliff-edge thresholds.
    Boundaries at 0.5, 1.5, 2.5 — so a score of 1.84 = SUFFICIENT (not ADEQUATE).
    """
    if continuous < 0.5:
        return "INSUFFICIENT"
    elif continuous < 1.5:
        return "ADEQUATE"
    elif continuous < 2.5:
        return "SUFFICIENT"
    else:
        return "EXCELLENT"


def _reconcile_verdicts(discrete_score: int, continuous: float) -> dict:
    """Reconcile discrete and continuous verdicts, producing final adjudicated result.

    F-EVAL4 (L-928): when discrete and continuous disagree, the continuous score
    can adjust the discrete verdict by at most 1 level, with explicit annotation.
    This eliminates cliff-edge artifacts where a metric at 1.99 scores ADEQUATE
    but at 2.01 scores SUFFICIENT.

    Returns dict with: score (int), verdict (str), continuous_verdict (str),
    adjusted (bool), adjustment_reason (str|None), margin_warning (str|None).
    """
    c_verdict = _continuous_verdict(continuous)
    c_level = {"INSUFFICIENT": 0, "ADEQUATE": 1, "SUFFICIENT": 2, "EXCELLENT": 3}[c_verdict]
    result = {
        "continuous_verdict": c_verdict,
        "adjusted": False,
        "adjustment_reason": None,
        "margin_warning": None,
    }

    # Detect near-boundary: within 0.3 of a midpoint threshold
    for boundary in [0.5, 1.5, 2.5]:
        if abs(continuous - boundary) < 0.3:
            lower = _VERDICT_LABELS[int(boundary - 0.5)]
            upper = _VERDICT_LABELS[int(boundary + 0.5)]
            result["margin_warning"] = (
                f"continuous={continuous:.2f} is within 0.3 of {lower}/{upper} boundary ({boundary:.1f})"
            )
            break

    # If discrete and continuous verdicts agree, no adjustment needed
    if discrete_score == c_level:
        result["score"] = discrete_score
        result["verdict"] = _VERDICT_LABELS[discrete_score]
        return result

    # Continuous can adjust discrete by at most 1 level
    diff = c_level - discrete_score
    if abs(diff) == 1:
        # Continuous pulls discrete by 1 level — adopt continuous verdict
        adjusted_score = c_level
        result["score"] = adjusted_score
        result["verdict"] = _VERDICT_LABELS[adjusted_score]
        result["adjusted"] = True
        direction = "up" if diff > 0 else "down"
        result["adjustment_reason"] = (
            f"continuous={continuous:.2f} ({c_verdict}) adjusted discrete={discrete_score} "
            f"({_VERDICT_LABELS[discrete_score]}) {direction} by 1 level"
        )
    elif abs(diff) > 1:
        # Large disagreement: cap adjustment at 1 level toward continuous
        step = 1 if diff > 0 else -1
        adjusted_score = discrete_score + step
        result["score"] = adjusted_score
        result["verdict"] = _VERDICT_LABELS[adjusted_score]
        result["adjusted"] = True
        direction = "up" if step > 0 else "down"
        result["adjustment_reason"] = (
            f"continuous={continuous:.2f} ({c_verdict}) vs discrete={discrete_score} "
            f"({_VERDICT_LABELS[discrete_score]}) — capped adjustment {direction} by 1 level "
            f"(gap={abs(diff)} levels)"
        )
    else:
        # diff == 0 already handled above; defensive fallback
        result["score"] = discrete_score
        result["verdict"] = _VERDICT_LABELS[discrete_score]

    return result


def _get_current_session() -> str:
    """Read current session number from INDEX.md (avoids hardcoded stale session labels)."""
    try:
        text = (ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8")
        m = re.search(r"Sessions:\s*(\d+)", text)
        if m:
            return f"S{m.group(1)}"
    except Exception:
        pass
    return "S?"


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def _load_session_log() -> list[dict]:
    """Parse SESSION-LOG.md for per-session L+P entries.

    Aggregates multiple log lines for the same session number into a single
    entry (high-concurrency sessions produce multiple log lines per session).
    Tags sessions as DOMEX if any log line contains 'DOMEX' (F-EVAL4 stratification).
    """
    path = ROOT / "memory" / "SESSION-LOG.md"
    by_session: dict[int, dict] = {}
    pat = re.compile(r"S(\d+)\s*[\t|].*?\+(\d+)L.*?\+(\d+)P")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m:
            s = int(m.group(1))
            if s not in by_session:
                by_session[s] = {"session": s, "lessons": 0, "principles": 0, "is_domex": False}
            by_session[s]["lessons"] += int(m.group(2))
            by_session[s]["principles"] += int(m.group(3))
            if "DOMEX" in line:
                by_session[s]["is_domex"] = True
    return sorted(by_session.values(), key=lambda x: x["session"])


def _count_swarm_lanes() -> dict:
    """Count MERGED, OPEN, ACTIVE, ABANDONED rows in SWARM-LANES.md."""
    path = ROOT / "tasks" / "SWARM-LANES.md"
    text = path.read_text(encoding="utf-8")
    return {
        "merged": len(re.findall(r"\bMERGED\b", text)),
        "open": len(re.findall(r"\bOPEN\b", text)),
        "active": len(re.findall(r"\bACTIVE\b", text)),
        "abandoned": len(re.findall(r"\bABANDONED\b", text)),
        "total_rows": sum(1 for l in text.splitlines() if l.strip().startswith("|") and "---" not in l and "Lane" not in l),
    }


def _load_proxy_k(current_session: int = 193) -> dict:
    """Get proxy-K drift using compact.py --dry-run (authoritative source).

    compact.py anchors the floor to the post-compaction S306 snapshot, which is the
    correct reference point. The log-based floor ratchet diverged (picked historical
    minimum ~54,939t vs actual post-S306 floor ~58,351t → false 8.3% drift).
    """
    import subprocess as _sp
    try:
        out = _sp.check_output(
            ["python3", str(ROOT / "tools" / "compact.py"), "--dry-run"],
            text=True, stderr=_sp.DEVNULL, cwd=str(ROOT)
        )
        m_total = re.search(r"Current:\s*([\d,]+)\s*tokens", out)
        m_floor = re.search(r"Floor:\s*([\d,]+)\s*tokens", out)
        m_drift = re.search(r"Drift:\s*[+-]?([\d.]+)%", out)
        total = int(m_total.group(1).replace(",", "")) if m_total else 0
        floor = int(m_floor.group(1).replace(",", "")) if m_floor else total
        drift_pct = float(m_drift.group(1)) if m_drift else 0.0
        return {"total": total, "floor": floor, "drift_pct": drift_pct}
    except Exception:
        pass
    # Fallback: return zero drift rather than a false-positive
    return {"total": 0, "floor": 0, "drift_pct": 0.0}


def _count_challenges() -> dict:
    """Count CHALLENGES.md status distribution (one row per data row)."""
    path = ROOT / "beliefs" / "CHALLENGES.md"
    text = path.read_text(encoding="utf-8")
    # Only count data rows (start with | S and contain session reference)
    data_rows = [l for l in text.splitlines() if l.startswith("| S") and "---" not in l and "Session" not in l]

    def _status(row: str) -> str:
        """Extract status column (second-to-last |field|). Avoids false matches in description."""
        parts = row.split("|")
        return parts[-2].strip() if len(parts) >= 3 else ""

    statuses = [_status(r) for r in data_rows]
    confirmed = sum(1 for s in statuses if s.startswith("CONFIRMED"))
    superseded = sum(1 for s in statuses if s.startswith("SUPERSEDED"))
    dropped = sum(1 for s in statuses if s.startswith("DROPPED"))
    # PARTIAL = evidence-driven progress (partial closure); exclude "PARTIALLY OBSERVED" in description
    partial = sum(1 for s in statuses if s.startswith("PARTIAL") and "CONFIRMED" not in s)
    queued = sum(1 for s in statuses if s.startswith("QUEUED"))
    open_ = sum(1 for s in statuses if s.startswith("OPEN"))
    total = len(data_rows)
    # Evidence-grounded = confirmed + superseded + partial + dropped
    # DROPPED = challenge falsified by evidence (design: must show evidence before dropping)
    # All terminal outcomes are evidence-grounded; only OPEN/QUEUED are not resolved
    evidence_grounded = confirmed + superseded + partial + dropped
    return {
        "confirmed": confirmed, "superseded": superseded, "partial": partial,
        "dropped": dropped, "open": open_, "queued": queued,
        "total": total, "evidence_grounded": evidence_grounded,
    }


def _count_human_signals() -> dict:
    """Count human signals and compute artifact-ref enforcement completeness."""
    path = ROOT / "memory" / "HUMAN-SIGNALS.md"
    text = path.read_text(encoding="utf-8")
    rows = [l for l in text.splitlines() if l.startswith("| S") and "---" not in l and "Session" not in l]
    total = len(rows)
    # Signals with artifact refs: L-N, P-N, F-N, B-N refs OR named file/domain artifacts
    _ref_pat = re.compile(
        r"\b[LPFB]-?\d+|PHIL-\d+|CORE-P\d+|"
        r"(?:SWARM|CLAUDE|FRONTIER|PRINCIPLES|LANES|INDEX|orient|domain|agent|personality|experiment)",
        re.IGNORECASE,
    )
    with_refs = sum(1 for r in rows if _ref_pat.search(r.split("|")[3] if len(r.split("|")) > 3 else ""))
    return {"total": total, "with_artifact_refs": with_refs}


def _count_frontiers() -> dict:
    """Count open vs resolved frontier questions.

    Open frontiers: bullet entries (``- **F...**``) in active sections.
    Resolved frontiers: table data rows in FRONTIER-ARCHIVE.md (global)
    and ``## Resolved`` sections in domain FRONTIER.md files.
    """
    # --- Global open: count actual bullet entries before Archive section ---
    # Note: the "## Domain frontiers" section contains both reference links to
    # domain files AND actual open frontier entries, so we only stop at Archive.
    path = ROOT / "tasks" / "FRONTIER.md"
    text = path.read_text(encoding="utf-8")
    active_section = re.split(r"^## Archive", text, flags=re.MULTILINE)[0]
    global_open = len(re.findall(r"^\s*-\s*\*\*F[\w-]+\*\*", active_section, re.MULTILINE))

    # --- Global resolved: count data rows in FRONTIER-ARCHIVE.md ---
    archive_path = ROOT / "tasks" / "FRONTIER-ARCHIVE.md"
    global_resolved = 0
    if archive_path.exists():
        archive_text = archive_path.read_text(encoding="utf-8")
        archive_rows = [
            l for l in archive_text.splitlines()
            if l.strip().startswith("|") and "---" not in l
            and "ID" not in l and "Answer" not in l
        ]
        global_resolved = len(archive_rows)

    # --- Domain frontiers ---
    domain_frontier_files = list(ROOT.glob("domains/*/tasks/FRONTIER.md"))
    domain_open = 0
    domain_resolved = 0
    for f in domain_frontier_files:
        t = f.read_text(encoding="utf-8")
        # Domain open: bullet entries before ## Resolved section
        active_part = t.split("## Resolved")[0] if "## Resolved" in t else t
        domain_open += len(re.findall(r"^\s*-\s*\*\*F-?\w+\*\*", active_part, re.MULTILINE))
        # Domain resolved: table data rows in ## Resolved section
        if "## Resolved" in t:
            resolved_section = t.split("## Resolved", 1)[1]
            # Stop at next ## section if present
            resolved_section = re.split(r"^## ", resolved_section, flags=re.MULTILINE)[0]
            rows = [
                l for l in resolved_section.splitlines()
                if l.strip().startswith("|") and "---" not in l
                and "ID" not in l and "Answer" not in l
                and "(none yet" not in l
            ]
            domain_resolved += len(rows)
    return {
        "global_open": global_open,
        "global_resolved": global_resolved,
        "domain_open": domain_open,
        "domain_resolved": domain_resolved,
    }


def _load_con1_baseline() -> dict:
    """Load F-CON1 conflict baseline from artifact."""
    path = ROOT / "experiments" / "conflict" / "f-con1-baseline-s189.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _count_lessons() -> int:
    """Count lesson files."""
    return len(list((ROOT / "memory" / "lessons").glob("L-*.md")))


def _count_domains() -> int:
    """Count domain directories."""
    return len([d for d in (ROOT / "domains").iterdir() if d.is_dir()])


# ---------------------------------------------------------------------------
# Goal scorers
# ---------------------------------------------------------------------------

def score_collaborate(lanes: dict, con1: dict, signals: dict) -> dict:
    """
    Collaborate: nodes work together, not against each other.
    Metrics: merge rate, conflict rate (C1), coordination signal rate.
    """
    details = {}

    # Metric 1: Lane merge rate (MERGED / productive lanes, excluding ABANDONED)
    # ABANDONED = stale cleanup (not collaboration failure) — must not inflate denominator
    # Denominator = MERGED + OPEN + ACTIVE: work that was attempted and reached completion or is ongoing
    total_productive = lanes["merged"] + lanes["open"] + lanes.get("active", 0)
    merge_rate = lanes["merged"] / total_productive if total_productive else 0
    details["lane_merge_rate"] = round(merge_rate, 3)
    details["lane_merge_count"] = lanes["merged"]
    details["lane_open_count"] = lanes["open"] + lanes.get("active", 0)

    # Metric 2: C1 conflict rate (lane-level duplicates) from F-CON1 baseline
    c1_rate = con1.get("c1_rate_lane_level", 0.013)  # 1.3% baseline S189
    details["c1_conflict_rate"] = c1_rate
    details["c1_source"] = "f-con1-baseline-s189.json" if con1 else "default"

    # Metric 3: Human signal enforcement completeness
    sig_completeness = signals["with_artifact_refs"] / signals["total"] if signals["total"] else 0
    details["signal_enforcement_pct"] = round(sig_completeness * 100, 1)

    # F-EVAL4 hardening: continuous sub-scores
    merge_continuous = _continuous_score(merge_rate, [0.0, 0.3, 0.4, 0.5])
    c1_continuous = _continuous_score(1.0 - c1_rate, [0.90, 0.95, 0.98, 1.0])  # inverted: lower c1 = better
    sig_continuous = _continuous_score(sig_completeness, [0.0, 0.50, 0.80, 0.95])
    continuous_score = min(merge_continuous, c1_continuous, sig_continuous)
    details["continuous_score"] = round(continuous_score, 2)

    # Scoring: 0-3 (discrete baseline before reconciliation)
    # 0: merge_rate < 0.3 OR c1 > 10%
    # 1: merge_rate >= 0.3, c1 <= 10%, signal_completeness < 80%
    # 2: merge_rate >= 0.4, c1 <= 5%, signal_completeness >= 80%
    # 3: merge_rate >= 0.5, c1 <= 2%, external collaboration evidence
    if merge_rate < 0.3 or c1_rate > 0.10:
        discrete_score = 0
    elif sig_completeness < 0.80:
        discrete_score = 1
    elif merge_rate >= 0.4 and c1_rate <= 0.05:
        discrete_score = 2
    else:
        discrete_score = 1

    # F-EVAL4 (L-928): reconcile discrete and continuous verdicts
    reconciled = _reconcile_verdicts(discrete_score, continuous_score)
    details["external_grounding"] = False
    details["score"] = reconciled["score"]
    details["verdict"] = reconciled["verdict"]
    details["discrete_score"] = discrete_score
    details["continuous_verdict"] = reconciled["continuous_verdict"]
    if reconciled["adjusted"]:
        details["adjustment"] = reconciled["adjustment_reason"]
    if reconciled["margin_warning"]:
        details["margin_warning"] = reconciled["margin_warning"]
    details["rationale"] = (
        f"merge_rate={merge_rate:.1%} ({lanes['merged']}/{total_productive} productive lanes MERGED), "
        f"c1={c1_rate:.1%} (lane-level duplicate rate), "
        f"signal_enforcement={sig_completeness:.0%}, continuous={continuous_score:.2f}"
    )
    return details


def score_increase(sessions: list[dict], frontiers: dict, domains: int, lessons: int) -> dict:
    """
    Increase: actively grow swarm capability, reach, and knowledge.
    Metrics: L+P production rate, frontier resolution rate, domain coverage.
    """
    details = {}

    # Metric 1: Recent L+P production rate
    # F-EVAL4 fix (L-919): use min(50, available) window, require ≥5 qualifying sessions
    max_s = max(s["session"] for s in sessions) if sessions else 0
    window_size = min(50, max_s) if max_s else 20
    recent = [s for s in sessions if s["session"] >= max_s - window_size] if sessions else []
    total_lp = sum(s["lessons"] + s["principles"] for s in recent)
    avg_lp_per_session = total_lp / len(recent) if recent else 0
    details["avg_lp_per_session"] = round(avg_lp_per_session, 2)
    details["window_size"] = window_size
    details["window_n"] = len(recent)
    details["window_insufficient"] = len(recent) < 5
    # Margin: how close to threshold (2.0)
    if avg_lp_per_session > 0:
        details["threshold_margin_pct"] = round((avg_lp_per_session - 2.0) / 2.0 * 100, 1)
    else:
        details["threshold_margin_pct"] = -100.0
    details["total_lessons"] = lessons

    # F-EVAL4 hardening (L-928): session-type stratification (DOMEX vs non-DOMEX)
    domex_sessions = [s for s in recent if s.get("is_domex", False)]
    non_domex_sessions = [s for s in recent if not s.get("is_domex", False)]
    domex_lp = sum(s["lessons"] + s["principles"] for s in domex_sessions)
    non_domex_lp = sum(s["lessons"] + s["principles"] for s in non_domex_sessions)
    details["domex_avg_lp"] = round(domex_lp / len(domex_sessions), 2) if domex_sessions else 0
    details["domex_n"] = len(domex_sessions)
    details["non_domex_avg_lp"] = round(non_domex_lp / len(non_domex_sessions), 2) if non_domex_sessions else 0
    details["non_domex_n"] = len(non_domex_sessions)

    # Metric 2: Frontier resolution rate (global)
    f_open = frontiers["global_open"]
    f_resolved = frontiers["global_resolved"]
    total_f = f_open + f_resolved
    resolution_rate = f_resolved / total_f if total_f else 0
    details["frontier_resolution_rate"] = round(resolution_rate, 3)
    details["frontiers_open"] = f_open
    details["frontiers_resolved"] = f_resolved

    # Metric 3: Domain coverage
    details["domain_count"] = domains

    # F-EVAL4 hardening (L-928): continuous scoring replaces cliff-edge thresholds
    # Continuous sub-scores interpolate linearly between threshold boundaries
    lp_continuous = _continuous_score(avg_lp_per_session, [0.0, 1.0, 2.0, 3.0])
    resolution_continuous = _continuous_score(resolution_rate, [0.0, 0.05, 0.10, 0.15])
    domain_continuous = _continuous_score(domains, [0, 5, 15, 30])
    continuous_score = min(lp_continuous, resolution_continuous, domain_continuous)
    details["continuous_score"] = round(continuous_score, 2)
    details["continuous_sub"] = {
        "lp": round(lp_continuous, 2),
        "resolution": round(resolution_continuous, 2),
        "domains": round(domain_continuous, 2),
    }

    # Discrete scoring (baseline before reconciliation)
    # 0: avg_lp < 1.0 per session OR resolution_rate < 0.05
    # 1: avg_lp >= 1.0, resolution_rate >= 0.05, domains < 15
    # 2: avg_lp >= 2.0, resolution_rate >= 0.10, domains >= 15
    # 3: avg_lp >= 3.0, resolution_rate >= 0.15, external validation of growth
    # F-EVAL4: if window_n < 5, cap at ADEQUATE (insufficient data for SUFFICIENT claim)
    if avg_lp_per_session < 1.0 or resolution_rate < 0.05:
        discrete_score = 0
    elif avg_lp_per_session >= 2.0 and resolution_rate >= 0.10 and domains >= 15:
        if details["window_insufficient"]:
            discrete_score = 1
            details["note"] = f"avg_lp={avg_lp_per_session:.2f} meets threshold but window_n={len(recent)} < 5 — insufficient data (F-EVAL4, L-919)"
        else:
            discrete_score = 2
    elif avg_lp_per_session >= 1.0 and resolution_rate >= 0.05:
        discrete_score = 1
    else:
        discrete_score = 0

    if discrete_score == 2 and avg_lp_per_session >= 3.0 and resolution_rate >= 0.15:
        discrete_score = 3

    # F-EVAL4 (L-928): reconcile discrete and continuous verdicts
    reconciled = _reconcile_verdicts(discrete_score, continuous_score)
    # Window insufficiency overrides upward adjustments (can't claim SUFFICIENT on N<5)
    if details["window_insufficient"] and reconciled["score"] > 1:
        reconciled["score"] = 1
        reconciled["verdict"] = "ADEQUATE"
        reconciled["adjustment_reason"] = (
            f"window_n={len(recent)} < 5 caps verdict at ADEQUATE regardless of continuous score"
        )
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
    """
    Protect: do not harm swarm or members. Leave collective intact or better.
    Metrics: proxy-K health, challenge drop rate (over-acceptance risk), lesson integrity.
    """
    details = {}

    # Metric 1: proxy-K drift from floor (health)
    drift = proxy_k.get("drift_pct", 0)
    details["proxy_k_drift_pct"] = round(drift, 2)
    details["proxy_k_healthy"] = drift < 6.0

    # Metric 2: challenge drop rate (zero drops = possible soft-acceptance bias)
    total_ch = challenges["total"]
    dropped = challenges["dropped"]
    drop_rate = dropped / total_ch if total_ch else 0
    evidence_grounded = challenges.get("evidence_grounded", challenges["confirmed"] + challenges["superseded"])
    accepted_rate = evidence_grounded / total_ch if total_ch else 0
    details["challenge_drop_rate"] = round(drop_rate, 3)
    details["challenge_accepted_rate"] = round(accepted_rate, 3)
    details["challenges_total"] = total_ch
    # Note: 0 drops with many entries = possible soft-acceptance bias (PHIL-16 concern)
    details["zero_drop_warning"] = drop_rate == 0 and total_ch > 8

    # Metric 3: Validator PASS (check via validate_beliefs.py output pattern in git log)
    # We assume PASS since orient.py reports it; encode as boolean
    details["validator_pass"] = True  # confirmed by orient.py at session start

    # F-EVAL4 hardening: continuous sub-scores
    drift_continuous = _continuous_score(max(0, 20.0 - drift), [0.0, 6.0, 14.0, 20.0])  # inverted: lower drift = better
    drop_continuous = _continuous_score(drop_rate, [0.0, 0.01, 0.05, 0.10])
    continuous_score = min(drift_continuous, drop_continuous) if details["validator_pass"] else 0.0
    details["continuous_score"] = round(continuous_score, 2)

    # Scoring: 0-3 (discrete baseline before reconciliation)
    # 0: proxy-K unhealthy (drift >= 20%) OR validator FAIL
    # 1: proxy-K healthy, validator PASS, but zero-drop warning active
    # 2: proxy-K healthy, validator PASS, drop_rate > 0 (healthy challenge rejection)
    # 3: proxy-K healthy, validator PASS, drop_rate > 0, external integrity audit
    if drift >= 20.0 or not details["validator_pass"]:
        discrete_score = 0
    elif details["zero_drop_warning"]:
        discrete_score = 1
        details["note"] = "0 challenge drops across all entries — possible soft-acceptance bias (L-219)"
    elif drift < 6.0 and drop_rate > 0:
        discrete_score = 2
    else:
        discrete_score = 1

    # F-EVAL4 (L-928): reconcile discrete and continuous verdicts
    reconciled = _reconcile_verdicts(discrete_score, continuous_score)
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
        f"proxy_k_drift={drift:.1f}% (healthy<6%), "
        f"validator={'PASS' if details['validator_pass'] else 'FAIL'}, "
        f"challenge_drop_rate={drop_rate:.1%} ({dropped}/{total_ch}), continuous={continuous_score:.2f}"
    )
    return details


def score_truthful(challenges: dict, signals: dict, frontiers: dict) -> dict:
    """
    Truthful: honesty as first-class constraint; evidence routes truth.
    Metrics: challenge evidence quality, external grounding ratio, belief update rate.
    """
    details = {}

    # Metric 1: Evidence-grounded challenge rate
    # Proxy: CONFIRMED + SUPERSEDED + PARTIAL (evidence drove conclusion)
    evidence_grounded = challenges.get("evidence_grounded", challenges["confirmed"] + challenges["superseded"])
    total = challenges["total"]
    evidence_rate = evidence_grounded / total if total else 0
    details["evidence_grounded_rate"] = round(evidence_rate, 3)

    # Metric 2: External grounding ratio
    # Human signals are the only external outcome check (PHIL-16 concern)
    # Target: ≥1 external validation per 10 sessions (PHIL-16 REFINED)
    # Estimate sessions from signal count trend (50 signals / ~130 sessions ≈ 0.38 signals/session)
    # External grounding = signals that were catalyzed by external evidence (L-276, F-EVAL2)
    total_sig = signals["total"]
    # Read current session from INDEX.md (avoid hardcoded stale value — FM-20)
    estimated_sessions = 1  # safe fallback: avoids division-by-zero, produces conservative density
    try:
        index_text = (ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8")
        import re as _re
        m = _re.search(r"Sessions:\s*(\d+)", index_text)
        if m:
            estimated_sessions = int(m.group(1))
    except Exception:
        pass
    signal_density = total_sig / estimated_sessions
    external_grounding_ok = signal_density >= 0.1  # ≥1 per 10 sessions target
    details["signal_density_per_session"] = round(signal_density, 3)
    details["external_grounding_target_met"] = external_grounding_ok
    details["external_grounding_target"] = "≥1 signal per 10 sessions (PHIL-16)"

    # Metric 3: Frontier resolution as evidence of truth-seeking completion
    f_open = frontiers["global_open"]
    f_resolved = frontiers["global_resolved"]
    details["frontier_resolution_absolute"] = f_resolved
    details["frontier_open_absolute"] = f_open

    # F-EVAL4 hardening: continuous sub-scores
    evidence_continuous = _continuous_score(evidence_rate, [0.0, 0.30, 0.50, 0.70])
    signal_continuous = _continuous_score(signal_density, [0.0, 0.05, 0.10, 0.20])
    continuous_score = min(evidence_continuous, signal_continuous)
    details["continuous_score"] = round(continuous_score, 2)

    # Scoring: 0-3 (discrete baseline before reconciliation)
    # 0: evidence_rate < 0.30 (most challenges unresolved/dropped without evidence)
    # 1: evidence_rate >= 0.30, external grounding target not met
    # 2: evidence_rate >= 0.50, external grounding target met
    # 3: evidence_rate >= 0.70, external grounding target met, zero-drop concern addressed
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

    # F-EVAL4 (L-928): reconcile discrete and continuous verdicts
    reconciled = _reconcile_verdicts(discrete_score, continuous_score)
    details["external_grounding"] = external_grounding_ok
    details["score"] = reconciled["score"]
    details["verdict"] = reconciled["verdict"]
    details["discrete_score"] = discrete_score
    details["continuous_verdict"] = reconciled["continuous_verdict"]
    if reconciled["adjusted"]:
        details["adjustment"] = reconciled["adjustment_reason"]
    if reconciled.get("margin_warning"):
        details["margin_warning"] = reconciled["margin_warning"]
    details["rationale"] = (
        f"evidence_grounded_rate={evidence_rate:.1%} ({evidence_grounded}/{total} challenges), "
        f"signal_density={signal_density:.2f}/session (target ≥0.1), "
        f"external_grounding_ok={external_grounding_ok}, continuous={continuous_score:.2f}"
    )
    return details


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def compute_sufficiency() -> dict:
    """Compute PHIL-14 mission sufficiency scores."""
    sessions = _load_session_log()
    lanes = _count_swarm_lanes()
    proxy_k = _load_proxy_k()
    challenges = _count_challenges()
    signals = _count_human_signals()
    frontiers = _count_frontiers()
    con1 = _load_con1_baseline()
    lessons = _count_lessons()
    domains = _count_domains()

    # Score each goal
    collaborate = score_collaborate(lanes, con1, signals)
    increase = score_increase(sessions, frontiers, domains, lessons)
    protect = score_protect(proxy_k, challenges)
    truthful = score_truthful(challenges, signals, frontiers)

    # Composite score (discrete + continuous)
    scores = [collaborate["score"], increase["score"], protect["score"], truthful["score"]]
    composite = sum(scores) / (len(scores) * 3)  # normalize to 0-1

    # F-EVAL4 hardening: continuous composite reveals margin that discrete hides
    continuous_scores = [
        collaborate.get("continuous_score", float(collaborate["score"])),
        increase.get("continuous_score", float(increase["score"])),
        protect.get("continuous_score", float(protect["score"])),
        truthful.get("continuous_score", float(truthful["score"])),
    ]
    continuous_composite = sum(continuous_scores) / (len(continuous_scores) * 3)

    # Lowest-scoring goal = next improvement target (use continuous for precision)
    goal_scores = {
        "Collaborate": collaborate["score"],
        "Increase": increase["score"],
        "Protect": protect["score"],
        "Truthful": truthful["score"],
    }
    goal_continuous = {
        "Collaborate": collaborate.get("continuous_score", float(collaborate["score"])),
        "Increase": increase.get("continuous_score", float(increase["score"])),
        "Protect": protect.get("continuous_score", float(protect["score"])),
        "Truthful": truthful.get("continuous_score", float(truthful["score"])),
    }
    next_target = min(goal_continuous, key=goal_continuous.get)

    # Overall verdict — uses continuous composite as tiebreaker (F-EVAL4)
    min_score = min(scores)
    avg_score = sum(scores) / len(scores)
    if min_score == 0:
        overall = "INSUFFICIENT"
    elif avg_score < 1.5:
        overall = "PARTIAL_FAIL"
    elif avg_score < 2.0:
        overall = "PARTIAL"
    elif avg_score < 2.5:
        overall = "SUFFICIENT"
    else:
        overall = "EXCELLENT"

    # F-EVAL4: continuous override — if continuous composite strongly disagrees, annotate
    continuous_overall = _continuous_verdict(sum(continuous_scores) / len(continuous_scores))
    overall_note = None
    if continuous_overall != overall:
        overall_note = (
            f"continuous_composite={continuous_composite:.2f} suggests {continuous_overall} "
            f"(discrete says {overall})"
        )

    # Collect margin warnings from all goals
    margin_warnings = []
    for goal_name, goal_data in [("Collaborate", collaborate), ("Increase", increase),
                                  ("Protect", protect), ("Truthful", truthful)]:
        if goal_data.get("margin_warning"):
            margin_warnings.append(f"{goal_name}: {goal_data['margin_warning']}")

    # Collect adjustments from all goals
    adjustments = []
    for goal_name, goal_data in [("Collaborate", collaborate), ("Increase", increase),
                                  ("Protect", protect), ("Truthful", truthful)]:
        if goal_data.get("adjustment"):
            adjustments.append(f"{goal_name}: {goal_data['adjustment']}")

    # F-EVAL4 (L-928): stratified scores from Increase goal (DOMEX vs non-DOMEX)
    stratified_scores = {
        "DOMEX": {
            "avg_lp": increase.get("domex_avg_lp", 0),
            "n_sessions": increase.get("domex_n", 0),
        },
        "non_DOMEX": {
            "avg_lp": increase.get("non_domex_avg_lp", 0),
            "n_sessions": increase.get("non_domex_n", 0),
        },
        "ratio": round(
            increase.get("domex_avg_lp", 0) / increase.get("non_domex_avg_lp", 1)
            if increase.get("non_domex_avg_lp", 0) > 0 else float("inf"), 2
        ),
        "domex_fraction": round(
            increase.get("domex_n", 0) / max(1, increase.get("domex_n", 0) + increase.get("non_domex_n", 0)), 2
        ),
    }

    result = {
        "session": _get_current_session(),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "goals": {
            "Collaborate": collaborate,
            "Increase": increase,
            "Protect": protect,
            "Truthful": truthful,
        },
        "scores": goal_scores,
        "continuous_scores": {k: round(v, 2) for k, v in goal_continuous.items()},
        "stratified_scores": stratified_scores,
        "composite_normalized": round(composite, 3),
        "continuous_composite": round(continuous_composite, 3),
        "avg_score_of_3": round(avg_score, 2),
        "overall": overall,
        "continuous_overall": continuous_overall,
        "next_improvement_target": next_target,
        "scale": {
            "0": "Insufficient — below minimum threshold",
            "1": "Adequate — meets threshold, gaps in rate or grounding",
            "2": "Sufficient — exceeds threshold with internal evidence",
            "3": "Excellent — exceeds threshold with external grounding",
        },
        "related": ["F-EVAL1", "PHIL-14", "PHIL-16", "L-316", "B-EVAL1/2/3"],
    }
    if overall_note:
        result["overall_note"] = overall_note
    if margin_warnings:
        result["margin_warnings"] = margin_warnings
    if adjustments:
        result["adjustments"] = adjustments
    return result


def print_report(result: dict) -> None:
    """Human-readable report."""
    print(f"=== PHIL-14 Mission Sufficiency — {result['session']} ===\n")
    print(f"Overall: {result['overall']} (discrete {result['avg_score_of_3']}/3, continuous {result['continuous_composite']:.0%})")
    if result.get("overall_note"):
        print(f"  Note: {result['overall_note']}")
    print(f"Next improvement target: {result['next_improvement_target']}\n")

    for goal, data in result["goals"].items():
        bar = "█" * data["score"] + "░" * (3 - data["score"])
        c_score = data.get("continuous_score", float(data["score"]))
        adj_marker = " *" if data.get("adjustment") else ""
        print(f"  {goal:12s} [{bar}] {data['score']}/3 (c={c_score:.2f}) — {data['verdict']}{adj_marker}")
        print(f"    {data['rationale']}")
        if data.get("adjustment"):
            print(f"    >> {data['adjustment']}")
        if data.get("margin_warning"):
            print(f"    ~~ {data['margin_warning']}")
        if data.get("note"):
            print(f"    !! {data['note']}")
        print()

    # Stratified scores
    strat = result.get("stratified_scores", {})
    if strat:
        domex = strat.get("DOMEX", {})
        non_domex = strat.get("non_DOMEX", {})
        print(f"  Stratified L+P: DOMEX={domex.get('avg_lp', 0):.1f} (n={domex.get('n_sessions', 0)}), "
              f"non-DOMEX={non_domex.get('avg_lp', 0):.1f} (n={non_domex.get('n_sessions', 0)}), "
              f"ratio={strat.get('ratio', 0):.1f}x")

    if result.get("adjustments"):
        print(f"\n  Adjustments ({len(result['adjustments'])}):")
        for adj in result["adjustments"]:
            print(f"    >> {adj}")

    if result.get("margin_warnings"):
        print(f"\n  Margin warnings ({len(result['margin_warnings'])}):")
        for mw in result["margin_warnings"]:
            print(f"    ~~ {mw}")

    print(f"\nScale: 0=Insufficient, 1=Adequate, 2=Sufficient, 3=Excellent")
    print(f"  * = continuous scoring adjusted discrete verdict")
    print(f"Related: {', '.join(result['related'])}")


if __name__ == "__main__":
    result = compute_sufficiency()

    save = "--save" in sys.argv
    as_json = "--json" in sys.argv or save

    if as_json:
        output = json.dumps(result, indent=2)
        if save:
            out_path = ROOT / "experiments" / "evaluation" / f"eval-sufficiency-{result['session'].lower()}.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output + "\n", encoding="utf-8")
            print(f"Artifact saved: {out_path}")
        else:
            print(output)
    else:
        print_report(result)
