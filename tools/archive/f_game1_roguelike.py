#!/usr/bin/env python3
"""F-GAME1: Roguelike meta-progression model for swarm sessions.

Parses SESSION-LOG to classify runs (sessions) as early-deaths vs deep-runs,
computes meta-progression carry-over (L+P persistence), and tests whether
early-death rate predicts future session productivity (roguelike learning curve).

Usage:
  python3 tools/f_game1_roguelike.py [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from collections import Counter
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).parent.parent

SESSION_RE = re.compile(r"^(S\d+[a-z]*)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\+(\d+)L[^|]*\+(\d+)P", re.MULTILINE)


def parse_sessions(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    for m in SESSION_RE.finditer(text):
        sid, date, lessons, principles = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        # Extract session number for ordering
        num_match = re.match(r"S(\d+)", sid)
        num = int(num_match.group(1)) if num_match else 0
        rows.append({"id": sid, "session_num": num, "date": date, "lessons": lessons, "principles": principles, "lp": lessons + principles})
    # Deduplicate: keep max-lp entry per session number (concurrent entries)
    by_num: dict[int, dict] = {}
    for r in rows:
        n = r["session_num"]
        if n not in by_num or r["lp"] > by_num[n]["lp"]:
            by_num[n] = r
    return sorted(by_num.values(), key=lambda x: x["session_num"])


def classify_run(lp: int) -> str:
    if lp == 0:
        return "early_death"
    elif lp <= 2:
        return "short_run"
    elif lp <= 6:
        return "medium_run"
    else:
        return "deep_run"


def run_roguelike_analysis(sessions: list[dict]) -> dict:
    n = len(sessions)
    classified = [(s, classify_run(s["lp"])) for s in sessions]
    type_counts = Counter(c for _, c in classified)

    # Productivity stats
    lp_values = [s["lp"] for s in sessions]
    productive = [s for s in sessions if s["lp"] > 0]
    early_deaths = [s for s in sessions if s["lp"] == 0]
    deep_runs = [s for s in sessions if s["lp"] > 6]

    # Meta-progression: cumulative L+P (carry-over)
    cumulative = []
    running = 0
    for s in sessions:
        running += s["lp"]
        cumulative.append(running)

    # "Roguelike learning curve" test: does early-death rate in window W predict productivity in window W+1?
    window = 10
    learning_curve = []
    for i in range(window, n - window, 5):
        past_window = sessions[i - window:i]
        future_window = sessions[i:i + window]
        past_death_rate = sum(1 for s in past_window if s["lp"] == 0) / window
        future_avg_lp = mean(s["lp"] for s in future_window)
        learning_curve.append({"start_session": sessions[i]["session_num"], "past_death_rate": round(past_death_rate, 3), "future_avg_lp": round(future_avg_lp, 3)})

    # Streak analysis: longest productive streak vs longest death streak
    max_productive_streak = max_death_streak = 0
    cur_p = cur_d = 0
    for s in sessions:
        if s["lp"] > 0:
            cur_p += 1
            cur_d = 0
        else:
            cur_d += 1
            cur_p = 0
        max_productive_streak = max(max_productive_streak, cur_p)
        max_death_streak = max(max_death_streak, cur_d)

    # Sharpe proxy: L+P per session for productive sessions
    if len(productive) >= 2:
        lp_productive = [s["lp"] for s in productive]
        lp_mean = mean(lp_productive)
        lp_std = stdev(lp_productive)
        sharpe_proxy = lp_mean / lp_std if lp_std > 0 else 0.0
    else:
        sharpe_proxy = 0.0

    # Recent trend (last 20 sessions)
    recent = sessions[-20:] if len(sessions) >= 20 else sessions
    recent_death_rate = sum(1 for s in recent if s["lp"] == 0) / len(recent)
    recent_avg_lp = mean(s["lp"] for s in recent)

    return {
        "total_sessions": n,
        "productive_sessions": len(productive),
        "early_death_sessions": len(early_deaths),
        "early_death_rate": round(len(early_deaths) / n, 4),
        "deep_run_sessions": len(deep_runs),
        "deep_run_rate": round(len(deep_runs) / n, 4),
        "run_type_distribution": dict(type_counts),
        "lp_stats": {
            "mean": round(mean(lp_values), 3),
            "max": max(lp_values),
            "total": sum(lp_values),
            "sharpe_proxy": round(sharpe_proxy, 3),
        },
        "meta_progression": {
            "final_cumulative_lp": cumulative[-1] if cumulative else 0,
            "cumulative_by_session_10": cumulative[9] if len(cumulative) > 9 else None,
            "cumulative_by_session_50": cumulative[49] if len(cumulative) > 49 else None,
            "acceleration_factor": round(recent_avg_lp / mean(lp_values), 3) if mean(lp_values) > 0 else 0,
        },
        "streak_analysis": {
            "max_productive_streak": max_productive_streak,
            "max_death_streak": max_death_streak,
        },
        "learning_curve": learning_curve,
        "recent_20_sessions": {
            "death_rate": round(recent_death_rate, 4),
            "avg_lp": round(recent_avg_lp, 3),
        },
        "interpretation": (
            f"Swarm session architecture shows roguelike structure: {100*len(early_deaths)//n}% early deaths "
            f"({len(early_deaths)}/{n}), {100*len(deep_runs)//n}% deep runs ({len(deep_runs)}/{n}). "
            f"Meta-progression carry-over total: {cumulative[-1] if cumulative else 0} L+P across {n} sessions. "
            f"Recent 20-session acceleration: {round(recent_avg_lp / mean(lp_values), 2) if mean(lp_values) > 0 else 0}x above historical average."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="F-GAME1: roguelike meta-progression analysis")
    parser.add_argument("--out", default="experiments/gaming/f-game1-roguelike-s189.json", help="Output artifact path")
    parser.add_argument("--session", help="Override session id (default: last session in SESSION-LOG)")
    parser.add_argument("--date", help="Override session date (YYYY-MM-DD; default: last session date)")
    args = parser.parse_args()

    sessions = parse_sessions(ROOT / "memory" / "SESSION-LOG.md")
    result = run_roguelike_analysis(sessions)
    last_session = sessions[-1] if sessions else None
    session_id = args.session or (last_session["id"] if last_session else "S0")
    session_date = args.date or (last_session["date"] if last_session else date.today().isoformat())

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "experiment": "F-GAME1",
        "title": "Roguelike meta-progression model for swarm sessions",
        "session": session_id,
        "date": session_date,
        **result,
    }
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    # Print summary
    print(f"\nSessions analyzed: {result['total_sessions']}")
    print(f"Early deaths: {result['early_death_sessions']} ({100*result['early_death_rate']:.1f}%)")
    print(f"Deep runs: {result['deep_run_sessions']} ({100*result['deep_run_rate']:.1f}%)")
    print(f"Meta-progression total L+P: {result['meta_progression']['final_cumulative_lp']}")
    print(f"Recent 20-session avg L+P: {result['recent_20_sessions']['avg_lp']}")
    print(f"Sharpe proxy: {result['lp_stats']['sharpe_proxy']}")


if __name__ == "__main__":
    main()
