#!/usr/bin/env python3
"""
agent_time_profile.py — Understand how swarm agents spend their time.

Classifies every commit into activity categories (value/overhead/mixed)
and reports time allocation, overhead trends, and efficiency patterns.

Usage:
    python3 tools/agent_time_profile.py                    # full report
    python3 tools/agent_time_profile.py --since S365       # from session N
    python3 tools/agent_time_profile.py --window 10        # window size for trends
    python3 tools/agent_time_profile.py --json             # machine-readable
    python3 tools/agent_time_profile.py --session S374     # single session detail

Answers: "How are agents spending their time?"
- What fraction of commits produce value vs overhead?
- Which sessions are most/least efficient?
- How does concurrency affect overhead?
- Is the trend improving or degrading?

Categories:
  VALUE:    DOMEX, harvest, tool-build, governance, principles
  OVERHEAD: handoff, state-sync, trim, orphan-rescue, fix, maintenance,
            periodics, lane-mgmt, compact, setup
  MIXED:    relay, paper, signal, other
"""

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = REPO_ROOT / "workspace" / "agent-time-profile.json"

# Classification rules — first match wins
CLASSIFIERS = [
    ("DOMEX",         r"DOMEX-"),
    ("handoff",       r"handoff:"),
    ("state-sync",    r"(state-sync|sync_state|sync:)"),
    ("orphan-rescue", r"orphan"),
    ("trim",          r"(trim|compacted to)"),
    ("relay",         r"relay"),
    ("harvest",       r"harvest"),
    ("fix",           r"^(\[S\d+\] )?(fix|repair|conflict)"),
    ("maintenance",   r"maintenance"),
    ("periodics",     r"(periodic|mission-constraint|health|dream-cycle|action-board|change-quality|economy-health)"),
    ("principles",    r"(principles-dedup|principle)"),
    ("governance",    r"(council|governance|genesis)"),
    ("tool-build",    r"(tool |profiler|swarm profiler|task-level claiming|swarm_cycle)"),
    ("compact",       r"compact"),
    ("setup",         r"(setup-reswarm|fundamental-setup)"),
    ("paper",         r"(paper|README|PAPER)"),
    ("lane-mgmt",     r"(close.*lane|lane closure|stale)"),
    ("signal",        r"(signal|SIG-)"),
    ("other",         r".*"),
]

VALUE_CATS = {"DOMEX", "harvest", "tool-build", "governance", "principles"}
OVERHEAD_CATS = {"handoff", "state-sync", "trim", "orphan-rescue", "fix",
                 "maintenance", "periodics", "lane-mgmt", "compact", "setup"}


def _git(*args):
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT)] + list(args),
            capture_output=True, text=True, timeout=15
        )
        return r.stdout.strip()
    except Exception:
        return ""


def classify(msg):
    """Return (category, type) for a commit message."""
    for cat, pattern in CLASSIFIERS:
        if re.search(pattern, msg, re.IGNORECASE):
            if cat in VALUE_CATS:
                return cat, "value"
            elif cat in OVERHEAD_CATS:
                return cat, "overhead"
            else:
                return cat, "mixed"
    return "other", "mixed"


def get_commits(since_session=None):
    """Get all commits, optionally filtered to >= since_session."""
    lines = _git("log", "--format=%s").split("\n")
    commits = []
    for line in lines:
        if not line.strip():
            continue
        m = re.match(r"\[S(\d+)\]", line)
        session = int(m.group(1)) if m else 0
        if since_session and session < since_session:
            continue
        cat, typ = classify(line)
        commits.append({"session": session, "msg": line, "category": cat, "type": typ})
    return commits


def aggregate(commits, window_size=10):
    """Compute per-session and windowed aggregates."""
    per_session = defaultdict(lambda: {"value": 0, "overhead": 0, "mixed": 0,
                                        "total": 0, "cats": Counter()})
    for c in commits:
        s = c["session"]
        per_session[s][c["type"]] += 1
        per_session[s]["total"] += 1
        per_session[s]["cats"][c["category"]] += 1

    # Windowed trends
    windows = defaultdict(lambda: {"value": 0, "overhead": 0, "total": 0,
                                    "sessions": 0})
    for s, d in per_session.items():
        w = (s // window_size) * window_size
        windows[w]["value"] += d["value"]
        windows[w]["overhead"] += d["overhead"]
        windows[w]["total"] += d["total"]
        windows[w]["sessions"] += 1

    return dict(per_session), dict(windows)


def print_report(commits, window_size=10, single_session=None):
    """Print human-readable report."""
    per_session, windows = aggregate(commits, window_size)

    if single_session:
        _print_session_detail(per_session, single_session)
        return

    # Overall summary
    total_cats = Counter()
    total_types = Counter()
    for c in commits:
        total_cats[c["category"]] += 1
        total_types[c["type"]] += 1

    total = len(commits)
    sessions = len(per_session)
    print(f"=== AGENT TIME PROFILE ({total} commits, {sessions} sessions) ===\n")

    print(f"  VALUE:    {total_types['value']:>4} ({100*total_types['value']/total:.1f}%)")
    print(f"  OVERHEAD: {total_types['overhead']:>4} ({100*total_types['overhead']/total:.1f}%)")
    print(f"  MIXED:    {total_types['mixed']:>4} ({100*total_types['mixed']/total:.1f}%)")
    ovh_ratio = total_types["overhead"] / max(total_types["value"], 1)
    print(f"  Overhead:Value ratio: {ovh_ratio:.2f}")

    # Category breakdown
    print(f"\n{'Category':<16} {'Count':>5} {'%':>6}  {'Type':<10}")
    print("-" * 45)
    for cat, count in total_cats.most_common():
        pct = 100 * count / total
        typ = "VALUE" if cat in VALUE_CATS else ("OVERHEAD" if cat in OVERHEAD_CATS else "MIXED")
        print(f"  {cat:<14} {count:>5} {pct:>5.1f}%  {typ}")

    # Trend
    print(f"\n=== OVERHEAD TREND ({window_size}-session windows) ===")
    print(f"{'Window':<14} {'Sess':>4} {'Commits':>7} {'Val%':>5} {'OvH%':>5} {'Ratio':>6}")
    print("-" * 46)
    for w in sorted(windows.keys()):
        d = windows[w]
        if d["total"] == 0:
            continue
        v_pct = 100 * d["value"] / d["total"]
        o_pct = 100 * d["overhead"] / d["total"]
        ratio = d["overhead"] / max(d["value"], 1)
        end = w + window_size - 1
        print(f"  S{w}-S{end:<5} {d['sessions']:>4} {d['total']:>7} {v_pct:>4.0f}% {o_pct:>4.0f}% {ratio:>5.2f}")

    # Concurrency effect
    high = [(s, d) for s, d in per_session.items() if d["total"] >= 10]
    low = [(s, d) for s, d in per_session.items() if 3 <= d["total"] < 10]
    if high and low:
        import statistics
        h_ovh = statistics.mean([100 * d["overhead"] / d["total"] for _, d in high])
        l_ovh = statistics.mean([100 * d["overhead"] / d["total"] for _, d in low])
        print(f"\n=== CONCURRENCY EFFECT ===")
        print(f"  High-commit (≥10): {h_ovh:.1f}% overhead (n={len(high)})")
        print(f"  Low-commit (3-9):  {l_ovh:.1f}% overhead (n={len(low)})")
        print(f"  Delta: {h_ovh - l_ovh:+.1f}pp")

    # Top 5 most efficient + worst sessions
    ranked = [(s, d) for s, d in per_session.items() if d["total"] >= 3]
    if ranked:
        by_value = sorted(ranked, key=lambda x: -100 * x[1]["value"] / x[1]["total"])
        print(f"\n=== MOST EFFICIENT SESSIONS ===")
        for s, d in by_value[:5]:
            v_pct = 100 * d["value"] / d["total"]
            top_cat = d["cats"].most_common(1)[0][0]
            print(f"  S{s}: {d['total']} commits, {v_pct:.0f}% value (primary: {top_cat})")

        print(f"\n=== HIGHEST OVERHEAD SESSIONS ===")
        by_overhead = sorted(ranked, key=lambda x: -100 * x[1]["overhead"] / x[1]["total"])
        for s, d in by_overhead[:5]:
            o_pct = 100 * d["overhead"] / d["total"]
            top_cat = d["cats"].most_common(1)[0][0]
            print(f"  S{s}: {d['total']} commits, {o_pct:.0f}% overhead (primary: {top_cat})")


def _print_session_detail(per_session, session):
    """Detail view for a single session."""
    if session not in per_session:
        print(f"No data for S{session}")
        return
    d = per_session[session]
    print(f"=== SESSION S{session} DETAIL ===")
    print(f"  Total commits: {d['total']}")
    print(f"  Value:    {d['value']} ({100*d['value']/d['total']:.0f}%)")
    print(f"  Overhead: {d['overhead']} ({100*d['overhead']/d['total']:.0f}%)")
    print(f"  Mixed:    {d['mixed']} ({100*d['mixed']/d['total']:.0f}%)")
    print(f"\n  Categories:")
    for cat, count in d["cats"].most_common():
        typ = "VALUE" if cat in VALUE_CATS else ("OVERHEAD" if cat in OVERHEAD_CATS else "MIXED")
        print(f"    {cat:<16} {count:>3}  ({typ})")


def json_report(commits, window_size=10):
    """Return JSON-serializable report."""
    per_session, windows = aggregate(commits, window_size)
    total_types = Counter()
    for c in commits:
        total_types[c["type"]] += 1
    total = len(commits)

    return {
        "total_commits": total,
        "sessions": len(per_session),
        "value_pct": round(100 * total_types["value"] / max(total, 1), 1),
        "overhead_pct": round(100 * total_types["overhead"] / max(total, 1), 1),
        "overhead_value_ratio": round(total_types["overhead"] / max(total_types["value"], 1), 2),
        "trend": [
            {
                "window": f"S{w}-S{w + window_size - 1}",
                "sessions": d["sessions"],
                "commits": d["total"],
                "value_pct": round(100 * d["value"] / max(d["total"], 1), 1),
                "overhead_pct": round(100 * d["overhead"] / max(d["total"], 1), 1),
                "ratio": round(d["overhead"] / max(d["value"], 1), 2),
            }
            for w, d in sorted(windows.items()) if d["total"] > 0
        ],
        "per_session": {
            str(s): {
                "total": d["total"],
                "value": d["value"],
                "overhead": d["overhead"],
                "value_pct": round(100 * d["value"] / max(d["total"], 1), 1),
            }
            for s, d in sorted(per_session.items())
        },
    }


def main():
    args = sys.argv[1:]
    since = None
    window = 10
    as_json = False
    single_session = None

    i = 0
    while i < len(args):
        if args[i] == "--since" and i + 1 < len(args):
            since = int(args[i + 1].replace("S", ""))
            i += 2
        elif args[i] == "--window" and i + 1 < len(args):
            window = int(args[i + 1])
            i += 2
        elif args[i] == "--json":
            as_json = True
            i += 1
        elif args[i] == "--session" and i + 1 < len(args):
            single_session = int(args[i + 1].replace("S", ""))
            i += 2
        else:
            i += 1

    commits = get_commits(since_session=since)
    if not commits:
        print("No commits found.")
        return

    if as_json:
        report = json_report(commits, window)
        print(json.dumps(report, indent=2))
    else:
        print_report(commits, window, single_session)


if __name__ == "__main__":
    main()
