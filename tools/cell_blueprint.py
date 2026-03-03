#!/usr/bin/env python3
"""
cell_blueprint.py — Structured session handoff as cell division (L-1184).

Sessions are cells. Cold-booting wastes orient time re-deriving state.
A cell blueprint pre-computes the daughter cell's initial conditions,
so the next session can metabolize immediately instead of re-orienting.

Usage:
    python3 tools/cell_blueprint.py save [--session S479]
    python3 tools/cell_blueprint.py load
    python3 tools/cell_blueprint.py load --json

save: writes workspace/cell-blueprint-latest.json at session end
load: prints human-readable blueprint for session start
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        return r.stdout.strip()
    except Exception:
        return ""


def _parse_session_number():
    """Get current session from NEXT.md header or INDEX.md."""
    for f in ["tasks/NEXT.md", "memory/INDEX.md"]:
        try:
            text = (ROOT / f).read_text(errors="replace")
            m = re.search(r"S(\d+)", text)
            if m:
                return int(m.group(1))
        except FileNotFoundError:
            pass
    return 0


def _active_lanes():
    """Parse SWARM-LANES.md for ACTIVE/CLAIMED/BLOCKED lanes."""
    try:
        text = (ROOT / "tasks/SWARM-LANES.md").read_text(errors="replace")
    except FileNotFoundError:
        return []
    lanes = []
    for line in text.split("\n"):
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue
        status = cols[11] if len(cols) > 11 else ""
        if status in ("ACTIVE", "CLAIMED", "BLOCKED", "READY"):
            lane_id = cols[2] if len(cols) > 2 else ""
            scope = cols[9] if len(cols) > 9 else ""
            lanes.append({"lane": lane_id, "status": status, "scope": scope})
    return lanes


def _recent_commits(n=5):
    """Get last n commits."""
    out = _run(["git", "log", f"--oneline", f"-{n}"])
    return out.split("\n") if out else []


def _metrics():
    """Extract L/P/B/F counts from INDEX.md."""
    try:
        text = (ROOT / "memory/INDEX.md").read_text(errors="replace")
    except FileNotFoundError:
        return {}
    counts = {}
    for label, pat in [("lessons", r"(\d+)\s+lessons"),
                       ("principles", r"(\d+)\s+principles"),
                       ("beliefs", r"(\d+)\s+beliefs"),
                       ("frontiers", r"(\d+)\s+frontiers")]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            counts[label] = int(m.group(1))
    return counts


def _uncommitted():
    """Get uncommitted file list."""
    out = _run(["git", "status", "--short"])
    if not out:
        return []
    return [line.strip() for line in out.split("\n") if line.strip()][:20]


def _untracked_artifacts():
    """Get untracked lesson/experiment files — the primary boot-time bottleneck.

    76% of sessions start by absorbing concurrent artifacts (S479 measurement).
    Pre-identifying these in the blueprint accelerates daughter cell boot.
    """
    out = _run(["git", "status", "--short"])
    if not out:
        return []
    untracked = []
    for line in out.split("\n"):
        line = line.strip()
        if line.startswith("?? "):
            path = line[3:].strip()
            # Only include lesson and experiment files (the absorption targets)
            if path.startswith("memory/lessons/") or path.startswith("experiments/"):
                untracked.append(path)
    return untracked


def _next_session_notes():
    """Extract 'For next session' section from NEXT.md."""
    try:
        text = (ROOT / "tasks/NEXT.md").read_text(errors="replace")
    except FileNotFoundError:
        return []
    m = re.search(r"## For next session\s*\n(.*?)(?:\n##|\Z)", text, re.DOTALL)
    if not m:
        return []
    lines = [l.strip() for l in m.group(1).strip().split("\n") if l.strip()]
    return lines[:10]


def _periodics_due():
    """Check which periodics are overdue."""
    try:
        data = json.loads((ROOT / "tools/periodics.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    items = data.get("items", data) if isinstance(data, dict) else data
    session = _parse_session_number()
    due = []
    for p in items:
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "")
        last = p.get("last_session", "S0")
        cadence = p.get("cadence", 10)
        last_n = int(re.search(r"(\d+)", str(last)).group(1)) if re.search(r"(\d+)", str(last)) else 0
        gap = session - last_n
        if gap >= cadence:
            due.append({"id": pid, "gap": gap, "cadence": cadence})
    return sorted(due, key=lambda x: -x["gap"])[:5]


def _dispatch_top3():
    """Run dispatch_optimizer briefly to get top 3 domains."""
    out = _run(["python3", "tools/dispatch_optimizer.py"], timeout=30)
    if not out:
        return []
    domains = []
    for line in out.split("\n"):
        m = re.match(r"\s+(\d+\.\d+)\s+(\S+)\s+", line)
        if m and len(domains) < 3:
            score = float(m.group(1))
            domain = m.group(2)
            # Check for collision warning
            collision = "ACTIVE LANE" in out.split(domain, 1)[-1].split("\n")[1] if domain in out else False
            domains.append({"domain": domain, "score": score, "collision": collision})
    return domains


def save_blueprint(session_override=None):
    """Save cell blueprint at session end."""
    session = session_override or _parse_session_number()

    # Normalize session to int
    if isinstance(session, str):
        m = re.search(r"(\d+)", session)
        session = int(m.group(1)) if m else session

    blueprint = {
        "schema": "cell-blueprint-v2",
        "session": f"S{session}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": _metrics(),
        "active_lanes": _active_lanes(),
        "recent_commits": _recent_commits(5),
        "uncommitted": _uncommitted(),
        "untracked_artifacts": _untracked_artifacts(),
        "next_actions": _next_session_notes(),
        "periodics_due": _periodics_due(),
        "dispatch_top3": _dispatch_top3(),
    }

    out_path = ROOT / "workspace" / "cell-blueprint-latest.json"
    out_path.write_text(json.dumps(blueprint, indent=2) + "\n")
    print(f"Blueprint saved: {out_path}")
    print(f"  Session: S{session} | {blueprint['metrics']}")
    print(f"  Active lanes: {len(blueprint['active_lanes'])}")
    print(f"  Uncommitted: {len(blueprint['uncommitted'])} files")
    print(f"  Next actions: {len(blueprint['next_actions'])} items")
    print(f"  Periodics due: {len(blueprint['periodics_due'])}")
    return blueprint


def load_blueprint(as_json=False):
    """Load and display the most recent cell blueprint."""
    bp_path = ROOT / "workspace" / "cell-blueprint-latest.json"
    if not bp_path.exists():
        print("No cell blueprint found. Cold boot — run full orient.")
        return None

    bp = json.loads(bp_path.read_text())

    if as_json:
        print(json.dumps(bp, indent=2))
        return bp

    session_label = bp.get("session", "?")
    if not str(session_label).startswith("S"):
        session_label = f"S{session_label}"
    print(f"=== CELL BLUEPRINT (from {session_label}) ===")
    print(f"Saved: {bp.get('timestamp', '?')}")

    metrics = bp.get("metrics", {})
    print(f"\nMetrics: {metrics.get('lessons', '?')}L {metrics.get('principles', '?')}P "
          f"{metrics.get('beliefs', '?')}B {metrics.get('frontiers', '?')}F")

    lanes = bp.get("active_lanes", [])
    if lanes:
        print(f"\nActive lanes ({len(lanes)}):")
        for l in lanes:
            print(f"  {l['lane']} [{l['status']}] → {l.get('scope', '')[:60]}")
    else:
        print("\nNo active lanes.")

    commits = bp.get("recent_commits", [])
    if commits:
        print(f"\nRecent commits:")
        for c in commits[:3]:
            print(f"  {c}")

    uncommitted = bp.get("uncommitted", [])
    if uncommitted:
        print(f"\nUncommitted ({len(uncommitted)} files):")
        for u in uncommitted[:5]:
            print(f"  {u}")

    artifacts = bp.get("untracked_artifacts", [])
    if artifacts:
        print(f"\nAbsorb these ({len(artifacts)} untracked artifacts):")
        for a in artifacts:
            print(f"  ?? {a}")

    actions = bp.get("next_actions", [])
    if actions:
        print(f"\nNext actions:")
        for a in actions:
            print(f"  {a}")

    due = bp.get("periodics_due", [])
    if due:
        print(f"\nOverdue periodics:")
        for d in due:
            print(f"  {d['id']} (gap={d['gap']}, cadence={d['cadence']})")

    top3 = bp.get("dispatch_top3", [])
    if top3:
        print(f"\nDispatch top-3:")
        for t in top3:
            collision = " ⚠ COLLISION" if t.get("collision") else ""
            print(f"  {t['domain']} (score={t['score']}){collision}")

    return bp


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/cell_blueprint.py save|load [--session N] [--json]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "save":
        session = None
        for i, arg in enumerate(sys.argv):
            if arg == "--session" and i + 1 < len(sys.argv):
                m = re.search(r"(\d+)", sys.argv[i + 1])
                if m:
                    session = int(m.group(1))
        save_blueprint(session)
    elif cmd == "load":
        load_blueprint(as_json="--json" in sys.argv)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
