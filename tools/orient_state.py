#!/usr/bin/env python3
"""
orient_state.py — State extraction utilities for orient.py.

Extracted from orient.py (DOMEX-META-S426) to reduce monolith size.
Handles: file reading, state line parsing, NEXT.md extraction, frontier parsing,
maintenance classification, session log parsing, git queries, signal parsing.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_file(relpath):
    try:
        return (ROOT / relpath).read_text(encoding="utf-8")
    except Exception:
        return ""


def extract_state_line(index_text):
    """Extract session + counts from INDEX.md header."""
    session = "S?"
    m = re.search(r"Sessions:\s*(\d+)", index_text[:300])
    if m:
        session = f"S{m.group(1)}"
    counts = "?"
    m2 = re.search(r"(\d+)\s+lessons", index_text[:500])
    m3 = re.search(r"(\d+)\s+principles", index_text[:500])
    m4 = re.search(r"(\d+)\s+beliefs", index_text[:500])
    m5 = re.search(r"(\d+)\s+frontier", index_text[:500])
    parts = []
    if m2: parts.append(f"{m2.group(1)}L")
    if m3: parts.append(f"{m3.group(1)}P")
    if m4: parts.append(f"{m4.group(1)}B")
    if m5: parts.append(f"{m5.group(1)}F")
    counts = " ".join(parts) if parts else "?"
    return session, counts


def extract_next_priorities(next_text):
    """Extract numbered items from 'For next session' section."""
    m = re.search(r"## For next session\n(.*?)(?:\n##|\Z)", next_text, re.DOTALL)
    if not m:
        return []
    items = re.findall(r"^\d+\.\s+\*\*(.+?)\*\*", m.group(1), re.MULTILINE)
    if not items:
        items = re.findall(r"^\d+\.\s+(.+)$", m.group(1), re.MULTILINE)
    return [i[:100] for i in items[:6]]


def extract_key_state(next_text):
    """Extract key state lines (compact URGENT, counts, etc.)."""
    m = re.search(r"## Key state\n(.*?)(?:\n##|\Z)", next_text, re.DOTALL)
    if not m:
        return []
    lines = [l.strip("- ").strip() for l in m.group(1).splitlines()
             if l.strip().startswith("-")]
    return [l[:100] for l in lines[:4]]


def extract_critical_frontiers(frontier_text):
    """Extract Critical and Important frontier titles."""
    items = []
    for section in ("## Critical", "## Important"):
        m = re.search(rf"{re.escape(section)}\n(.*?)(?:\n##|\Z)", frontier_text, re.DOTALL)
        if not m:
            continue
        bullets = re.findall(r"^- \*\*(F\d+)\*\*:(.+)", m.group(1), re.MULTILINE)
        for fid, desc in bullets:
            first = desc.strip().split(".")[0][:80]
            items.append(f"{fid}: {first}")
    return items


def classify_maint(maint_out):
    """Return urgency level string from maintenance output."""
    if "URGENT" in maint_out:
        return "URGENT"
    if "[DUE]" in maint_out:
        return "DUE items present"
    if "[PERIODIC]" in maint_out:
        return "periodics due"
    return "NOTICE-only"


def extract_session_log_tail(log_text, n=10):
    """Return last N non-header session log lines (behavioral pattern signal)."""
    lines = [l for l in log_text.splitlines()
             if l.strip() and not l.startswith("#") and "|" in l]
    return lines[-n:]


def get_recent_commits(n=6):
    """Get recent commit summaries for collision-avoidance (L-251, L-283)."""
    result = subprocess.run(
        ["git", "log", "--oneline", f"-{n}"],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        return []
    commits = []
    for line in result.stdout.strip().splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append(parts[1])
    return commits


def get_current_session_from_git() -> int:
    """Derive current session number from git log (last committed session + 1).

    Fixes stale-lane detection bug: INDEX.md Sessions: N lags by one session,
    so lanes from session N aren't flagged as stale until sync_state.py runs.
    Using git log directly gives the correct boundary. (L-515, S347)
    """
    result = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode == 0:
        m = re.search(r"\[S(\d+)\]", result.stdout)
        if m:
            return int(m.group(1)) + 1
    return 0


def extract_open_signals(signals_text: str, current_session: int = 0) -> list:
    """Parse SIGNALS.md and return OPEN signals sorted by priority then recency."""
    results = []
    for line in signals_text.splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| ID"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 11:
            continue
        sig_id, _date, sess, _src, _tgt, sig_type, priority, content, status = (
            cols[1], cols[2], cols[3], cols[4], cols[5], cols[6], cols[7], cols[8], cols[9]
        )
        if status.upper() not in ("OPEN", "PARTIALLY RESOLVED"):
            continue
        age = 0
        m = re.search(r"S(\d+)", sess)
        if m and current_session > 0:
            age = current_session - int(m.group(1))
        results.append({"id": sig_id, "session": sess, "priority": priority,
                         "content": content, "age": age, "type": sig_type})
    # Sort: P1 first, then by age DESCENDING (oldest/most-neglected first within priority)
    # L-803: prior ascending sort buried 55-session-old P1 directives behind recent ones
    results.sort(key=lambda x: (0 if x["priority"] == "P1" else 1, -x["age"]))
    return results


def run_maintenance():
    """Run maintenance --quick and return stdout."""
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "maintenance.py"), "--quick"],
            capture_output=True, text=True, cwd=ROOT, timeout=15
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "[NOTICE] maintenance.py timed out (>15s) — check_uncommitted or check_mission_constraints likely slow on WSL"
