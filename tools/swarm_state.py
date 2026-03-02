#!/usr/bin/env python3
"""Compact state estimator for stigmergy observability (Council S4, L-484).

Generates workspace/swarm_state.json — a ~500-byte machine-readable snapshot
of the swarm's key control variables. Replaces 30k tokens of orient.py sensor
data with a compact state vector that any tool or session can read instantly.

Usage:
    python3 tools/swarm_state.py          # write workspace/swarm_state.json
    python3 tools/swarm_state.py --print  # print to stdout only
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from swarm_io import REPO_ROOT, read_text, session_number, git_cmd

def compute_state() -> dict:
    session = session_number()

    # Lesson count + sink nodes (zero inbound citations)
    lesson_dir = REPO_ROOT / "memory" / "lessons"
    lessons = sorted(lesson_dir.glob("L-[0-9]*.md"))
    lesson_ids = {f.stem for f in lessons}
    cited = set()
    for lf in lessons:
        text = read_text(lf)
        for m in re.findall(r"L-(\d{3})", text):
            lid = f"L-{m}"
            if lid != lf.stem:
                cited.add(lid)
    sink_count = len(lesson_ids - cited)
    sink_pct = round(sink_count / len(lesson_ids) * 100, 1) if lesson_ids else 0

    # EAD compliance: session notes in NEXT.md with expect: field
    next_text = read_text(REPO_ROOT / "tasks" / "NEXT.md")
    session_notes = re.findall(r"^## S\d+ session note", next_text, re.MULTILINE)
    ead_notes = re.findall(r"^\- \*\*expect\*\*:", next_text, re.MULTILINE)
    ead_compliance = round(len(ead_notes) / len(session_notes) * 100, 1) if session_notes else 0

    # Proxy-K drift (from compact.py --dry-run or maintenance output)
    drift_pct = None
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "compact.py"), "--dry-run"],
            capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT),
        )
        m = re.search(r"(\d+\.?\d*)%", r.stdout)
        if m:
            drift_pct = float(m.group(1))
    except Exception:
        pass

    # Open lanes (active vs stale)
    lanes_text = read_text(REPO_ROOT / "tasks" / "SWARM-LANES.md")
    active_lanes = len(re.findall(r"\|\s*(CLAIMED|ACTIVE|BLOCKED|READY)\s*\|", lanes_text))
    stale_lanes = 0  # lanes active but >5 sessions old
    for m in re.finditer(r"\|\s*S?(\d+)\s*\|.*\|\s*(CLAIMED|ACTIVE|BLOCKED|READY)\s*\|", lanes_text):
        lane_session = int(m.group(1))
        if session - lane_session > 5:
            stale_lanes += 1

    # Tool utilization (from git log last 20 sessions)
    log_text = git_cmd("log", "--oneline", "-100")
    tools_dir = REPO_ROOT / "tools"
    all_tools = sorted(f.name for f in tools_dir.glob("*.py") if not f.name.startswith("test_"))
    used_tools = set()
    for line in log_text.splitlines():
        for t in all_tools:
            if t.replace(".py", "") in line.lower():
                used_tools.add(t)
    tool_util_pct = round(len(used_tools) / len(all_tools) * 100, 1) if all_tools else 0

    # Principle count (from header, not pattern-matching removed principles)
    princ_text = read_text(REPO_ROOT / "memory" / "PRINCIPLES.md")
    pm = re.search(r"(\d+) live principles", princ_text)
    princ_count = int(pm.group(1)) if pm else len(set(re.findall(r"P-\d{3}", princ_text)))

    # Domain activation (has DOMEX lane merged in last 20 sessions = active)
    domains_dir = REPO_ROOT / "domains"
    all_domains = sorted(d.name for d in domains_dir.iterdir() if d.is_dir()) if domains_dir.exists() else []
    active_domains = 0
    for d in all_domains:
        # Check if domain has any DOMEX lane activity in SWARM-LANES.md
        pattern = f"DOMEX.*{d[:4]}" if len(d) > 4 else d
        if re.search(pattern, lanes_text, re.IGNORECASE):
            active_domains += 1

    return {
        "session": session,
        "lessons": len(lesson_ids),
        "principles": princ_count,
        "sink_nodes": sink_count,
        "sink_pct": sink_pct,
        "ead_compliance_pct": ead_compliance,
        "proxy_k_drift_pct": drift_pct,
        "active_lanes": active_lanes,
        "stale_lanes": stale_lanes,
        "tool_utilization_pct": tool_util_pct,
        "domains_total": len(all_domains),
        "domains_active": active_domains,
        "domain_activation_pct": round(active_domains / len(all_domains) * 100, 1) if all_domains else 0,
    }


def main():
    state = compute_state()
    out = json.dumps(state, indent=2)

    if "--print" in sys.argv:
        print(out)
        return

    out_path = REPO_ROOT / "workspace" / "swarm_state.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out + "\n")
    print(f"State written to {out_path}")
    print(out)


if __name__ == "__main__":
    main()
