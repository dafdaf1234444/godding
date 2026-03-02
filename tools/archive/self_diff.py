#!/usr/bin/env python3
"""
self_diff.py — Unified swarm self-diff: snapshot state, compare across sessions.

The swarm has 14+ measurement tools but no unified "state A vs state B" comparison.
This tool closes that gap. It snapshots structural, content, and metric state into
a single JSON, and diffs any two snapshots to show what changed and why it matters.

Usage:
    python3 tools/self_diff.py                # show current snapshot
    python3 tools/self_diff.py --save         # save snapshot to log
    python3 tools/self_diff.py --diff         # diff current vs last saved snapshot
    python3 tools/self_diff.py --diff N       # diff current vs snapshot N sessions ago
    python3 tools/self_diff.py --history      # show all saved snapshots (summary)

Covers 5 diff dimensions:
  1. Structural:  lesson/principle/frontier/domain/tool counts
  2. Content:     SHA hashes of key state files (detect silent edits)
  3. Topology:    K_avg, citation density, proxy-K, reach composite
  4. Belief:      principle status distribution (theorized/observed/challenged)
  5. Quality:     lane health (active/merged/abandoned), expect-act-diff compliance
"""

import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "experiments" / "self-diff-log.json"

# Key state files to hash for content-change detection
STATE_FILES = [
    "beliefs/CORE.md", "beliefs/PHILOSOPHY.md", "beliefs/DEPS.md",
    "beliefs/INVARIANTS.md", "beliefs/CONFLICTS.md",
    "memory/INDEX.md", "memory/PRINCIPLES.md", "memory/DISTILL.md",
    "tasks/NEXT.md", "tasks/FRONTIER.md", "tasks/SWARM-LANES.md",
    "SWARM.md", "CLAUDE.md",
]


try:
    from swarm_io import session_number as _current_session
except ImportError:
    def _current_session() -> int:
        r = subprocess.run(["git", "log", "--oneline", "-10"], capture_output=True, text=True, cwd=ROOT)
        for line in r.stdout.splitlines():
            m = re.search(r"\[S(\d+)\]", line)
            if m:
                return int(m.group(1))
        return 0


def _count_artifacts() -> dict:
    """Count all major artifact types."""
    lessons = len(glob.glob(str(ROOT / "memory/lessons/L-*.md")))
    principles = 0
    princ_path = ROOT / "memory" / "PRINCIPLES.md"
    if princ_path.exists():
        # Principles inline as "P-NNN word" — count unique P-IDs
        principles = len(set(re.findall(r"P-\d+", princ_path.read_text())))
    frontiers = 0
    front_path = ROOT / "tasks" / "FRONTIER.md"
    if front_path.exists():
        # Frontiers as "**F119**:" or "**F-SCALE2**:" in bullet lists
        frontiers = len(re.findall(r"\*\*F[-\w]*\d+\*\*", front_path.read_text()))
    domains = 0
    dom_dir = ROOT / "domains"
    if dom_dir.exists():
        domains = len([d for d in dom_dir.iterdir() if d.is_dir() and (d / "DOMAIN.md").exists()])
    tools = len(glob.glob(str(ROOT / "tools/*.py")))
    experiments = len(glob.glob(str(ROOT / "experiments/**/*.json"), recursive=True))
    isos = 0
    iso_path = ROOT / "domains" / "ISOMORPHISM-ATLAS.md"
    if iso_path.exists():
        # ISOs as "### ISO-N:" headings
        isos = len(re.findall(r"^### ISO-\d+", iso_path.read_text(), re.M))
    return {
        "lessons": lessons, "principles": principles, "frontiers": frontiers,
        "domains": domains, "tools": tools, "experiments": experiments, "isos": isos,
    }


def _hash_state_files() -> dict:
    """SHA256 prefix of key state files — detects content changes."""
    hashes = {}
    for f in STATE_FILES:
        p = ROOT / f
        if p.exists():
            hashes[f] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    return hashes


def _principle_statuses() -> dict:
    """Count principles by status: OBSERVED, THEORIZED, etc."""
    princ_path = ROOT / "memory" / "PRINCIPLES.md"
    if not princ_path.exists():
        return {}
    text = princ_path.read_text()
    statuses = {"observed": 0, "partially_observed": 0, "theorized": 0, "other": 0}
    for m in re.finditer(r"(PARTIALLY OBSERVED|OBSERVED|THEORIZED|CHALLENGED)", text, re.I):
        s = m.group(1).lower().replace(" ", "_")
        if s in statuses:
            statuses[s] += 1
        else:
            statuses["other"] += 1
    return statuses


def _lane_health() -> dict:
    """Count lanes by status from SWARM-LANES.md."""
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    if not lanes_path.exists():
        return {}
    text = lanes_path.read_text()
    health = {"ACTIVE": 0, "MERGED": 0, "ABANDONED": 0, "OPEN": 0}
    for m in re.finditer(r"\|\s*(ACTIVE|MERGED|ABANDONED|OPEN)\s*\|", text, re.I):
        s = m.group(1).upper()
        health[s] = health.get(s, 0) + 1
    return health


def _proxy_k_current() -> int:
    """Get current proxy-K from proxy_k.py (tokens only)."""
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "proxy_k.py")],
            capture_output=True, text=True, cwd=ROOT, timeout=15,
        )
        m = re.search(r"TOTAL\s+(\d[\d,]+)\s*tokens", r.stdout)
        if m:
            return int(m.group(1).replace(",", ""))
    except Exception:
        pass
    return 0


def _expect_act_diff_compliance() -> float:
    """Measure % of active lanes with expect/actual/diff fields."""
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    if not lanes_path.exists():
        return 0.0
    text = lanes_path.read_text()
    active_lanes = re.findall(r"\|[^|]*ACTIVE[^|]*\|(.+)", text, re.I)
    if not active_lanes:
        return 0.0
    compliant = 0
    for lane in active_lanes:
        has_expect = bool(re.search(r"expect\s*=", lane, re.I))
        has_artifact = bool(re.search(r"artifact\s*=", lane, re.I))
        if has_expect and has_artifact:
            compliant += 1
    return round(compliant / len(active_lanes), 3)


def snapshot() -> dict:
    """Capture current swarm state as a comparable snapshot."""
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "session": _current_session(),
        "counts": _count_artifacts(),
        "hashes": _hash_state_files(),
        "belief_status": _principle_statuses(),
        "lane_health": _lane_health(),
        "proxy_k": _proxy_k_current(),
        "ead_compliance": _expect_act_diff_compliance(),
    }


def diff(prev: dict, curr: dict) -> dict:
    """Compare two snapshots; return structured delta with verdicts."""
    delta = {"from_session": prev.get("session"), "to_session": curr.get("session")}

    # 1. Count deltas
    count_diff = {}
    for key in set(prev.get("counts", {})) | set(curr.get("counts", {})):
        a = prev.get("counts", {}).get(key, 0)
        b = curr.get("counts", {}).get(key, 0)
        if a != b:
            count_diff[key] = {"from": a, "to": b, "delta": b - a}
    if count_diff:
        delta["count_changes"] = count_diff

    # 2. Content changes (hash mismatches)
    changed_files = []
    for key in set(prev.get("hashes", {})) | set(curr.get("hashes", {})):
        ha = prev.get("hashes", {}).get(key)
        hb = curr.get("hashes", {}).get(key)
        if ha != hb:
            changed_files.append(key)
    if changed_files:
        delta["content_changed"] = sorted(changed_files)

    # 3. Belief status shifts
    bs_prev = prev.get("belief_status", {})
    bs_curr = curr.get("belief_status", {})
    bs_diff = {}
    for key in set(bs_prev) | set(bs_curr):
        a = bs_prev.get(key, 0)
        b = bs_curr.get(key, 0)
        if a != b:
            bs_diff[key] = {"from": a, "to": b}
    if bs_diff:
        delta["belief_shifts"] = bs_diff

    # 4. Lane health changes
    lh_prev = prev.get("lane_health", {})
    lh_curr = curr.get("lane_health", {})
    lh_diff = {}
    for key in set(lh_prev) | set(lh_curr):
        a = lh_prev.get(key, 0)
        b = lh_curr.get(key, 0)
        if a != b:
            lh_diff[key] = {"from": a, "to": b}
    if lh_diff:
        delta["lane_health_changes"] = lh_diff

    # 5. Proxy-K drift
    pk_prev = prev.get("proxy_k", 0)
    pk_curr = curr.get("proxy_k", 0)
    if pk_prev and pk_curr and pk_prev != pk_curr:
        drift_pct = round((pk_curr - pk_prev) / pk_prev * 100, 2)
        delta["proxy_k_drift"] = {
            "from": pk_prev, "to": pk_curr,
            "delta_tokens": pk_curr - pk_prev, "drift_pct": drift_pct,
        }

    # 6. EAD compliance change
    ead_prev = prev.get("ead_compliance", 0)
    ead_curr = curr.get("ead_compliance", 0)
    if ead_prev != ead_curr:
        delta["ead_compliance"] = {"from": ead_prev, "to": ead_curr}

    # Verdict
    n_changes = len(delta) - 1  # exclude from/to_session
    if n_changes == 0:
        delta["verdict"] = "IDENTICAL — no measurable change"
    elif n_changes <= 2:
        delta["verdict"] = "MINOR — incremental session"
    elif n_changes <= 4:
        delta["verdict"] = "MODERATE — multi-dimension change"
    else:
        delta["verdict"] = "MAJOR — structural phase shift"

    return delta


def load_history() -> list:
    """Load saved snapshot history."""
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text())
    return []


def save_snapshot(snap: dict) -> Path:
    """Append snapshot to log, dedup by session."""
    history = load_history()
    # Dedup: skip if same session already saved
    for entry in history:
        if entry.get("session") == snap.get("session"):
            print(f"  (session S{snap['session']} already in log — skipped)")
            return LOG_PATH
    history.append(snap)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(history, indent=2))
    return LOG_PATH


def print_snapshot(snap: dict):
    """Pretty-print a snapshot."""
    s = snap.get("session", "?")
    ts = snap.get("timestamp", "?")
    print(f"=== SWARM SELF-DIFF SNAPSHOT | S{s} | {ts} ===\n")
    c = snap.get("counts", {})
    print(f"  Lessons: {c.get('lessons', '?')}  Principles: {c.get('principles', '?')}  "
          f"Frontiers: {c.get('frontiers', '?')}  Domains: {c.get('domains', '?')}")
    print(f"  Tools: {c.get('tools', '?')}  Experiments: {c.get('experiments', '?')}  "
          f"ISOs: {c.get('isos', '?')}")
    print(f"  Proxy-K: {snap.get('proxy_k', '?'):,} tokens")
    print(f"  EAD compliance: {snap.get('ead_compliance', '?'):.0%}" if isinstance(
        snap.get('ead_compliance'), (int, float)) else f"  EAD compliance: ?")
    bs = snap.get("belief_status", {})
    if bs:
        parts = [f"{k}={v}" for k, v in bs.items() if v > 0]
        print(f"  Principle status: {', '.join(parts) if parts else 'none parsed'}")
    lh = snap.get("lane_health", {})
    if lh:
        print(f"  Lanes: ACTIVE={lh.get('ACTIVE', 0)} MERGED={lh.get('MERGED', 0)} "
              f"ABANDONED={lh.get('ABANDONED', 0)}")
    # Content hashes (show count only)
    h = snap.get("hashes", {})
    print(f"  State files tracked: {len(h)}")


def print_diff(delta: dict):
    """Pretty-print a diff result."""
    print(f"=== SELF-DIFF: S{delta.get('from_session', '?')} → S{delta.get('to_session', '?')} ===\n")

    if "count_changes" in delta:
        print("  Count changes:")
        for k, v in delta["count_changes"].items():
            sign = "+" if v["delta"] > 0 else ""
            print(f"    {k}: {v['from']} → {v['to']} ({sign}{v['delta']})")

    if "content_changed" in delta:
        print(f"\n  Content changed ({len(delta['content_changed'])} files):")
        for f in delta["content_changed"]:
            print(f"    • {f}")

    if "belief_shifts" in delta:
        print("\n  Belief status shifts:")
        for k, v in delta["belief_shifts"].items():
            print(f"    {k}: {v['from']} → {v['to']}")

    if "lane_health_changes" in delta:
        print("\n  Lane health changes:")
        for k, v in delta["lane_health_changes"].items():
            print(f"    {k}: {v['from']} → {v['to']}")

    if "proxy_k_drift" in delta:
        pk = delta["proxy_k_drift"]
        sign = "+" if pk["delta_tokens"] > 0 else ""
        print(f"\n  Proxy-K: {pk['from']:,} → {pk['to']:,} ({sign}{pk['delta_tokens']:,}t, "
              f"{pk['drift_pct']:+.1f}%)")

    if "ead_compliance" in delta:
        ec = delta["ead_compliance"]
        print(f"\n  EAD compliance: {ec['from']:.0%} → {ec['to']:.0%}")

    print(f"\n  Verdict: {delta.get('verdict', '?')}")


def main():
    parser = argparse.ArgumentParser(
        description="Swarm self-diff: snapshot state and compare across sessions")
    parser.add_argument("--save", action="store_true", help="Save current snapshot")
    parser.add_argument("--diff", nargs="?", const="1", default=None,
                        help="Diff current vs N snapshots ago (default: 1)")
    parser.add_argument("--history", action="store_true", help="Show snapshot history")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    snap = snapshot()

    if args.history:
        history = load_history()
        if not history:
            print("No saved snapshots yet. Run --save first.")
            return
        print(f"=== SNAPSHOT HISTORY ({len(history)} entries) ===\n")
        for i, entry in enumerate(history):
            c = entry.get("counts", {})
            print(f"  [{i}] S{entry.get('session', '?')} | {entry.get('timestamp', '?')[:10]} | "
                  f"L={c.get('lessons', '?')} P={c.get('principles', '?')} "
                  f"PK={entry.get('proxy_k', '?'):,}t")
        return

    if args.diff is not None:
        history = load_history()
        if not history:
            print("No saved snapshots. Run --save first, then --diff.")
            return
        n = int(args.diff)
        idx = max(0, len(history) - n)
        prev = history[idx]
        delta = diff(prev, snap)
        if args.json:
            print(json.dumps(delta, indent=2))
        else:
            print_diff(delta)
        return

    if args.save:
        p = save_snapshot(snap)
        if args.json:
            print(json.dumps(snap, indent=2))
        else:
            print_snapshot(snap)
            print(f"\n  Saved to {p}")
        return

    # Default: show current snapshot
    if args.json:
        print(json.dumps(snap, indent=2))
    else:
        print_snapshot(snap)


if __name__ == "__main__":
    main()
