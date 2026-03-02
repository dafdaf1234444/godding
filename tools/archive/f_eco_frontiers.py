#!/usr/bin/env python3
"""
f_eco_frontiers.py — Economy domain: F-ECO1/F-ECO2/F-ECO3 analysis

F-ECO1: exploration vs exploitation ratio across time
F-ECO2: helper-spawn delegation cost model — empirical verification
F-ECO3: task throughput rate as leading indicator of L+P health

Usage:
    python3 tools/f_eco_frontiers.py [--save]
"""

import json
import re
import sys
from pathlib import Path
from statistics import correlation, mean, stdev

ROOT = Path(__file__).parent.parent
ARTIFACT_DIR = ROOT / "experiments" / "economy"

try:
    from swarm_io import read_text as _read
    _has_swarm_io = True
except ImportError:
    try:
        from tools.swarm_io import read_text as _read
        _has_swarm_io = True
    except ImportError:
        _has_swarm_io = False


# ─── helpers ────────────────────────────────────────────────────────────────

if not _has_swarm_io:
    def _read(p: Path) -> str:
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""


def _ls_md() -> list[Path]:
    """Fast: tracked md files via git ls-files."""
    import subprocess
    r = subprocess.run(
        ["git", "ls-files", "*.md", "**/*.md"],
        capture_output=True, text=True, cwd=ROOT
    )
    return [ROOT / p for p in r.stdout.splitlines() if p]


# ─── F-ECO1: exploration/exploitation ratio ─────────────────────────────────

def eco1_exploration_ratio() -> dict:
    """
    Measure the exploration:exploitation ratio.

    Exploration proxy: lessons per session (new knowledge captured).
    Exploitation proxy: resolved frontiers (questions answered).
    Hypothesis (P-178): sustained knowledge growth requires continuous
    exploration; ratio near 1:2 open:close expected from F-ECO1 design.
    """
    # Current stock ratios
    frontier_open = 0
    frontier_resolved = 0
    fp = ROOT / "tasks" / "FRONTIER.md"
    ap = ROOT / "tasks" / "FRONTIER-ARCHIVE.md"
    if fp.exists():
        frontier_open = len(re.findall(r"^\s*-\s*\*\*F[\w-]+\*\*", _read(fp), re.MULTILINE))
    if ap.exists():
        lines = [l for l in _read(ap).splitlines() if l.startswith("|")]
        frontier_resolved = max(0, len(lines) - 2)  # subtract header rows

    # Domain frontiers (F-XXX prefix inside domains/)
    domain_open = 0
    domain_resolved = 0
    for domain_dir in (ROOT / "domains").iterdir():
        ff = domain_dir / "tasks" / "FRONTIER.md"
        if ff.exists():
            text = _read(ff)
            domain_open += len(re.findall(r"^\s*-\s*\*\*F-\w+\*\*", text, re.MULTILINE))
            resolved_section = text.split("## Resolved", 1)[-1] if "## Resolved" in text else ""
            domain_resolved += len(re.findall(r"^\|.*\|.*\|", resolved_section, re.MULTILINE))

    total_open = frontier_open + domain_open
    total_resolved = frontier_resolved + domain_resolved
    total_all = total_open + total_resolved

    # Per-session production: L+P from session log (exploration rate proxy)
    log = ROOT / "memory" / "SESSION-LOG.md"
    sessions = []
    if log.exists():
        pat = re.compile(r"S(\d+)\s*[\t|].*?\+(\d+)L.*?\+(\d+)P")
        for line in _read(log).splitlines():
            m = pat.search(line)
            if m:
                sessions.append({
                    "session": int(m.group(1)),
                    "L": int(m.group(2)),
                    "P": int(m.group(3)),
                })

    # Rolling 10-session exploration rate (new L+P per session)
    recent = sessions[-10:] if len(sessions) >= 10 else sessions
    recent_lp_per_session = mean(s["L"] + s["P"] for s in recent) if recent else 0
    alltime_lp_per_session = mean(s["L"] + s["P"] for s in sessions) if sessions else 0

    # Hypothesis test: is the open:resolved ratio near 1:2 (0.5)?
    obs_ratio = round(total_open / max(1, total_resolved), 3)
    target_ratio = 0.5
    ratio_gap = round(obs_ratio - target_ratio, 3)

    # Verdict
    if obs_ratio <= 0.7:
        verdict = "BALANCED — exploitation-dominant; healthy backlog pressure"
    elif obs_ratio <= 1.5:
        verdict = "SLIGHTLY_EXPLORATION_HEAVY — manageable frontier accumulation"
    else:
        verdict = "EXPLORATION_HEAVY — frontier backlog growing faster than resolution"

    return {
        "frontier_open_global": frontier_open,
        "frontier_resolved_global": frontier_resolved,
        "frontier_open_domain": domain_open,
        "frontier_resolved_domain": domain_resolved,
        "total_open": total_open,
        "total_resolved": total_resolved,
        "open_resolved_ratio": obs_ratio,
        "target_ratio_hypothesis": target_ratio,
        "ratio_gap": ratio_gap,
        "recent_lp_per_session": round(recent_lp_per_session, 3),
        "alltime_lp_per_session": round(alltime_lp_per_session, 3),
        "exploration_acceleration": round(
            recent_lp_per_session / max(0.01, alltime_lp_per_session), 3
        ),
        "sessions_analyzed": len(sessions),
        "verdict": verdict,
    }


# ─── F-ECO2: helper spawn ROI empirical ─────────────────────────────────────

def eco2_helper_roi() -> dict:
    """
    Empirically verify the helper-spawn delegation cost model.

    Model assumptions:
      spawn_overhead = 15% session
      stall_cost = 0.5 L+P per blocked lane per session
      recovery_sessions = 3
      theoretical_ROI = (stall_cost * recovery) / spawn_overhead = 9.0x

    Empirical approach:
      - Parse session log for production per session
      - Proxy "sessions with helpers active": sessions where SWARM-LANES
        shows a DOMEX or helper lane was ACTIVE (S180+)
      - Compare avg L+P in helper-active vs helper-inactive windows
    """
    # Parse session-level data
    log = ROOT / "memory" / "SESSION-LOG.md"
    sessions: dict[int, dict] = {}
    if log.exists():
        pat = re.compile(r"S(\d+)\s*[\t|].*?\+(\d+)L.*?\+(\d+)P")
        for line in _read(log).splitlines():
            m = pat.search(line)
            if m:
                sid = int(m.group(1))
                lp = int(m.group(2)) + int(m.group(3))
                if sid not in sessions:
                    sessions[sid] = {"lp": 0}
                sessions[sid]["lp"] += lp

    # Parse SWARM-LANES for sessions that had DOMEX (helper proxy) lanes active
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    helper_sessions: set[int] = set()
    blocked_sessions: dict[int, int] = {}  # session -> blocked count
    if lanes_path.exists():
        for line in _read(lanes_path).splitlines():
            if not line.startswith("|"):
                continue
            # Extract session from "| date | lane-id | S186 |..."
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue
            sess_field = parts[3] if len(parts) > 3 else ""
            sm = re.match(r"S(\d+)", sess_field)
            if not sm:
                continue
            sid = int(sm.group(1))
            # Helper proxy: DOMEX lanes or explicit "helper" in lane name
            lane_id = parts[2] if len(parts) > 2 else ""
            if "DOMEX" in lane_id or "helper" in lane_id.lower():
                helper_sessions.add(sid)
            # Blocked: look for blocked=yes or BLOCKED status
            if "blocked=yes" in line.lower() or "| BLOCKED |" in line:
                blocked_sessions[sid] = blocked_sessions.get(sid, 0) + 1

    # Compute production in helper vs non-helper sessions (last 50 sessions)
    recent_sids = sorted(sessions.keys())[-50:]
    helper_lp = [sessions[s]["lp"] for s in recent_sids if s in helper_sessions and s in sessions]
    non_helper_lp = [sessions[s]["lp"] for s in recent_sids if s not in helper_sessions and s in sessions]

    helper_mean = round(mean(helper_lp), 3) if helper_lp else 0
    non_helper_mean = round(mean(non_helper_lp), 3) if non_helper_lp else 0
    empirical_lift = round(helper_mean / max(0.01, non_helper_mean), 3) if non_helper_lp else None

    # Theoretical model constants
    spawn_overhead = 0.15
    stall_cost_per_lane = 0.5
    recovery_sessions = 3.0
    theory_roi = round((stall_cost_per_lane * recovery_sessions - spawn_overhead) / spawn_overhead, 2)

    # Blocked lane impact estimate
    avg_blocked = mean(blocked_sessions.values()) if blocked_sessions else 0

    # Verdict
    if empirical_lift is not None:
        if empirical_lift > 1.2:
            verdict = f"CONFIRMED — helper-active sessions produce {empirical_lift:.2f}x more L+P (theory: {theory_roi:.1f}x ROI)"
        elif empirical_lift >= 0.9:
            verdict = f"NEUTRAL — no clear lift ({empirical_lift:.2f}x); DOMEX proxy may be imprecise"
        else:
            verdict = f"INCONCLUSIVE — helper sessions lower ({empirical_lift:.2f}x); DOMEX ≠ pure helper"
    else:
        verdict = "INSUFFICIENT_DATA — not enough helper sessions in recent 50 to compare"

    return {
        "theoretical_roi": theory_roi,
        "spawn_overhead_fraction": spawn_overhead,
        "stall_cost_per_lane": stall_cost_per_lane,
        "recovery_sessions": recovery_sessions,
        "sessions_with_helpers_proxy": len(helper_sessions),
        "recent_sessions_analyzed": len(recent_sids),
        "helper_sessions_in_recent": len(helper_lp),
        "non_helper_sessions_in_recent": len(non_helper_lp),
        "helper_mean_lp": helper_mean,
        "non_helper_mean_lp": non_helper_mean,
        "empirical_lift": empirical_lift,
        "avg_blocked_lanes_per_session": round(avg_blocked, 2),
        "verdict": verdict,
    }


# ─── F-ECO3: throughput as leading indicator ─────────────────────────────────

def eco3_throughput_indicator() -> dict:
    """
    Test if task throughput rate is a better leading indicator than L+P rate.

    Method:
      - Parse SWARM-LANES for MERGED lane counts per session
      - Parse SESSION-LOG for L+P per session
      - Compute rolling throughput (merged/total) per session
      - Test lag correlation: does throughput at T predict L+P at T+1 and T+2?
    """
    # Parse L+P per session
    log = ROOT / "memory" / "SESSION-LOG.md"
    session_lp: dict[int, float] = {}
    if log.exists():
        pat = re.compile(r"S(\d+)\s*[\t|].*?\+(\d+)L.*?\+(\d+)P")
        for line in _read(log).splitlines():
            m = pat.search(line)
            if m:
                sid = int(m.group(1))
                lp = int(m.group(2)) + int(m.group(3))
                session_lp[sid] = session_lp.get(sid, 0) + lp

    # Parse MERGED lanes per session from SWARM-LANES
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    session_merged: dict[int, int] = {}
    session_total: dict[int, int] = {}
    if lanes_path.exists():
        for line in _read(lanes_path).splitlines():
            if not line.startswith("|"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue
            sess_field = parts[3] if len(parts) > 3 else ""
            sm = re.match(r"S(\d+)", sess_field)
            if not sm:
                continue
            sid = int(sm.group(1))
            session_total[sid] = session_total.get(sid, 0) + 1
            if "| MERGED |" in line or "| DONE |" in line:
                session_merged[sid] = session_merged.get(sid, 0) + 1

    # Build aligned time series (sessions with both data)
    all_sids = sorted(set(session_lp) & set(session_total))
    if len(all_sids) < 10:
        return {
            "verdict": "INSUFFICIENT_DATA",
            "sessions_with_both": len(all_sids),
        }

    # Throughput per session = merged / total (floor at 0 if no merges)
    throughput_series = [
        session_merged.get(s, 0) / max(1, session_total[s]) for s in all_sids
    ]
    lp_series = [session_lp[s] for s in all_sids]

    # Lag correlations (throughput at T vs L+P at T+lag)
    def lag_corr(series_a: list, series_b: list, lag: int) -> float | None:
        if lag >= len(series_a):
            return None
        a = series_a[:len(series_a)-lag]
        b = series_b[lag:]
        if len(a) < 4:
            return None
        try:
            return round(correlation(a, b), 4)
        except Exception:
            return None

    corr_0 = lag_corr(throughput_series, lp_series, 0)   # same session
    corr_1 = lag_corr(throughput_series, lp_series, 1)   # 1 session lead
    corr_2 = lag_corr(throughput_series, lp_series, 2)   # 2 session lead

    # Also compute L+P auto-correlation for comparison
    lp_autocorr_1 = lag_corr(lp_series, lp_series, 1)

    # Current throughput (last 10 sessions)
    recent_sids = all_sids[-10:]
    recent_throughput = mean(
        session_merged.get(s, 0) / max(1, session_total[s]) for s in recent_sids
    )
    recent_lp = mean(session_lp[s] for s in recent_sids)

    # Verdict: is throughput a leading indicator?
    if corr_1 is not None and corr_0 is not None:
        if corr_1 > corr_0 + 0.05:
            verdict = f"CONFIRMED_LEADING — throughput leads L+P (corr@lag0={corr_0:.3f} vs corr@lag1={corr_1:.3f})"
        elif abs(corr_1 - corr_0) <= 0.05:
            verdict = f"CONCURRENT — throughput and L+P move together (lag-0={corr_0:.3f} ≈ lag-1={corr_1:.3f})"
        else:
            verdict = f"NOT_LEADING — throughput lags L+P (lag-0={corr_0:.3f} > lag-1={corr_1:.3f})"
    else:
        verdict = "INSUFFICIENT_DATA"

    return {
        "sessions_analyzed": len(all_sids),
        "throughput_lp_corr_lag0": corr_0,
        "throughput_lp_corr_lag1": corr_1,
        "throughput_lp_corr_lag2": corr_2,
        "lp_autocorr_lag1": lp_autocorr_1,
        "recent_throughput_mean": round(recent_throughput, 4),
        "recent_lp_per_session": round(recent_lp, 3),
        "current_throughput_rate": round(
            sum(session_merged.get(s, 0) for s in all_sids) /
            max(1, sum(session_total.get(s, 0) for s in all_sids)), 4
        ),
        "verdict": verdict,
    }


# ─── main ────────────────────────────────────────────────────────────────────

def run() -> dict:
    eco1 = eco1_exploration_ratio()
    eco2 = eco2_helper_roi()
    eco3 = eco3_throughput_indicator()
    return {
        "frontier": "F-ECO1/F-ECO2/F-ECO3",
        "session": "S188",
        "date": "2026-02-28",
        "F-ECO1_exploration_ratio": eco1,
        "F-ECO2_helper_roi": eco2,
        "F-ECO3_throughput_indicator": eco3,
    }


def main() -> None:
    result = run()
    save = "--save" in sys.argv
    if save:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        out = ARTIFACT_DIR / "f-eco-frontiers-s188.json"
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Saved: {out}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
