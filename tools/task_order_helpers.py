#!/usr/bin/env python3
"""
task_order_helpers.py — Extracted helpers for task_order.py.

Contains: zombie detection, claim management, and preemption checking.
Split from task_order.py for T4 anti-cascade compliance (<5000t ceiling).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _git(args: list[str]) -> str:
    r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip()


def _current_session() -> int:
    try:
        idx = (ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8")
        m = re.search(r"Sessions:\s*(\d+)", idx)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0


def get_resolved_signal_ids() -> set:
    """Return set of SIG-NNN IDs that have RESOLVED status in SIGNALS.md."""
    resolved = set()
    signals_file = ROOT / "tasks" / "SIGNALS.md"
    if not signals_file.exists():
        return resolved
    for line in signals_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("| SIG-"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 8:
            continue
        sig_id = parts[1]
        status = parts[7] if len(parts) > 7 else ""
        if "RESOLVED" in status.upper() or "ABANDONED" in status.upper():
            resolved.add(sig_id)
    return resolved


def get_done_periodic_ids() -> set:
    """Return set of periodic IDs that are NOT overdue per periodics.json."""
    done = set()
    try:
        periodics_path = ROOT / "tools" / "periodics.json"
        if not periodics_path.exists():
            return done
        data = json.loads(periodics_path.read_text(encoding="utf-8", errors="replace"))
        sess = _current_session()
        for pid, entry in data.items():
            last = entry.get("last_reviewed_session", 0)
            cadence = entry.get("cadence_sessions", 20)
            if sess - last < cadence:
                done.add(pid)
    except Exception:
        pass
    return done


def get_dropped_zombies() -> set:
    """Return set of canonical zombie items explicitly dropped in zombie_drops.json."""
    dropped = set()
    try:
        drops_path = ROOT / "tools" / "zombie_drops.json"
        if not drops_path.exists():
            return dropped
        data = json.loads(drops_path.read_text(encoding="utf-8"))
        for entry in data.get("drops", []):
            canon = entry.get("canonical", "")
            if canon:
                dropped.add(canon)
    except Exception:
        pass
    return dropped


def get_zombie_due_items(P_DUE: int) -> list[dict]:
    """Surface zombie Next: items as DUE tasks (L-978 TG-2)."""
    tasks = []
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from trails_generalizer import parse_session_notes, canonicalize
        from collections import Counter

        next_path = ROOT / "tasks" / "NEXT.md"
        if not next_path.exists():
            return tasks
        notes = parse_session_notes(next_path.read_text(encoding="utf-8"))
        if len(notes) < 3:
            return tasks

        item_counter = Counter()
        for note in notes:
            seen: set[str] = set()
            for item in note["next_items"]:
                canon = canonicalize(item)
                if canon not in seen:
                    item_counter[canon] += 1
                    seen.add(canon)

        resolved_sigs = get_resolved_signal_ids()
        done_periodics = get_done_periodic_ids()
        dropped_zombies = get_dropped_zombies()

        for item, count in item_counter.most_common():
            if count < 5:
                break
            sig_match = re.search(r"SIG-(\d+)", item, re.IGNORECASE)
            if sig_match and f"SIG-{sig_match.group(1)}" in resolved_sigs:
                continue
            per_match = re.search(r"\[([a-z][a-z0-9-]+)\]", item)
            if per_match and per_match.group(1) in done_periodics:
                continue
            if item in dropped_zombies:
                continue
            tasks.append({
                "priority": P_DUE,
                "tier": "DUE",
                "score": min(85, 70 + count),
                "action": f"Zombie ({count}x): {item[:60]} — execute or drop",
                "detail": f"Recurring {count} sessions without resolution (L-978 TG-2)",
                "command": None,
            })
    except Exception:
        pass
    return tasks[:5]


def extract_task_anchors(action: str) -> set[str]:
    """Extract anchor identifiers from a task action string for preemption matching."""
    anchors = set()
    for m in re.finditer(r'\b([A-Za-z][-A-Za-z0-9_]*\.(?:md|py|json))\b', action):
        anchors.add(m.group(1).lower())
    for m in re.finditer(r'\b(L-\d+)\b', action):
        anchors.add(m.group(1).lower())
    for m in re.finditer(r'\b(DOMEX-[A-Z]+-S\d+)\b', action):
        anchors.add(m.group(1).lower())
    for m in re.finditer(r'\b(F-[A-Z]+\d+|FM-\d+|SIG-\d+)\b', action):
        anchors.add(m.group(1).lower())
    return anchors


def check_preemption(tasks: list[dict], P_DISPATCH: int, P_STRATEGY: int) -> list[dict]:
    """Mark tasks preempted by recent commits (FM-28 hardening)."""
    recent_commits = _git(["log", "--oneline", "-5"])
    changed_files = _git(["diff", "--name-only", "HEAD~5..HEAD"])
    if not recent_commits:
        return tasks

    commit_text = (recent_commits + "\n" + changed_files).lower()
    preempted_count = 0
    actionable_count = 0

    for task in tasks:
        if task.get("claimed_by") or task["priority"] > P_DISPATCH:
            continue
        actionable_count += 1
        anchors = extract_task_anchors(task["action"])
        if task.get("detail"):
            anchors |= extract_task_anchors(task["detail"])
        if not anchors:
            continue
        matched = sum(1 for a in anchors if a in commit_text)
        if matched >= 1 and len(anchors) > 0 and matched / len(anchors) >= 0.5:
            task["preempted"] = True
            task["score"] -= 50
            if "[PREEMPTED]" not in task["tier"]:
                task["tier"] = f"{task['tier']} [PREEMPTED]"
            preempted_count += 1

    if actionable_count > 0 and preempted_count / actionable_count > 0.5:
        tasks.append({
            "priority": P_STRATEGY,
            "tier": "NOVEL",
            "score": 85,
            "action": "High preemption detected — switch to novel/meta work concurrent sessions cannot anticipate",
            "detail": f"{preempted_count}/{actionable_count} top tasks preempted by recent commits (FM-28, L-526)",
            "command": None,
        })
    return tasks


def get_task_fingerprint(task: dict) -> str:
    """Generate a stable fingerprint from a task for claim deconfliction."""
    action = task["action"]
    m = re.match(r".*\[([^\]]+)\]", action)
    if m:
        return m.group(1).lower().strip()
    m = re.search(r"DOMEX.*?for\s+(\S+)", action)
    if m:
        return f"dispatch:{m.group(1).lower()}"
    m = re.search(r"Close lane\s+(\S+)", action)
    if m:
        return f"close:{m.group(1).lower()}"
    m = re.match(r"Periodic:\s*(\S+)", action)
    if m:
        return f"periodic:{m.group(1).lower()}"
    m = re.match(r"Lesson over 20 lines:\s*(L-\d+)", action)
    if m:
        return f"trim:{m.group(1)}"
    return re.sub(r"[^a-z0-9]+", "-", action[:40].lower()).strip("-")


def check_task_claims(tasks: list[dict]) -> list[dict]:
    """Mark tasks claimed by other sessions (L-686)."""
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from claim import get_active_task_claims, get_session_id
        my_session = get_session_id()
        claimed = get_active_task_claims(exclude_session=my_session)
    except Exception:
        return tasks

    for task in tasks:
        fp = get_task_fingerprint(task)
        task["fingerprint"] = fp
        if fp in claimed:
            claim_data = claimed[fp]
            task["claimed_by"] = claim_data["session"]
            task["score"] -= 100
            task["tier"] = f"{task['tier']} [CLAIMED]"
    return tasks


def auto_claim_task(task: dict) -> None:
    """Automatically claim the top task (L-686)."""
    fp = task.get("fingerprint") or get_task_fingerprint(task)
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from claim import cmd_claim_task, get_session_id
        session = get_session_id()
        cmd_claim_task(fp, session, task["action"][:80])
    except Exception:
        pass


def get_signal_tasks(P_DUE: int, P_STRATEGY: int) -> list[dict]:
    """Route stale/partially-resolved signals to actionable tasks (SIG-2 closure)."""
    tasks = []
    signals_file = ROOT / "tasks" / "SIGNALS.md"
    if not signals_file.exists():
        return tasks
    try:
        log_out = _git(["log", "--oneline", "-3"])
        sn_m = re.search(r"\[S(\d+)\]", log_out)
        current_session = int(sn_m.group(1)) if sn_m else 400

        for line in signals_file.read_text().splitlines():
            if not line.startswith("| SIG-"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 11:
                continue
            sig_id = cols[1]
            session_str = cols[3]
            sig_type = cols[6]
            priority = cols[7]
            content = cols[8][:80]
            status = cols[9]
            resolution = cols[10] if len(cols) > 10 else ""

            sess_m = re.search(r"S?(\d+)", session_str)
            sig_session = int(sess_m.group(1)) if sess_m else 0
            age = current_session - sig_session

            if status == "PARTIALLY RESOLVED" and age > 15:
                gap_m = re.search(r"[Gg]ap:\s*(.{10,80})", resolution)
                gap = gap_m.group(1).rstrip(". |") if gap_m else "incomplete implementation"
                score = 76 if priority == "P1" else 72
                tasks.append({
                    "priority": P_STRATEGY, "tier": "SIGNAL-ACTION", "score": score,
                    "action": f"Close {sig_id} gap ({age}s stale): {gap[:60]}",
                    "detail": f"[{sig_type}] {content}", "command": None,
                })
            elif status == "OPEN" and sig_type == "question":
                tasks.append({
                    "priority": P_DUE, "tier": "SIGNAL-QUESTION", "score": 82,
                    "action": f"Escalate {sig_id} to human: {content[:50]}",
                    "detail": f"OPEN question signal, age {age}s — needs human decision",
                    "command": None,
                })
    except Exception:
        pass
    return tasks[:5]


def get_numeric_condition_due_items(P_DUE: int) -> list[dict]:
    """Surface near-threshold numeric-condition items as DUE (S445, L-1062)."""
    tasks = []
    try:
        idx_path = ROOT / "memory" / "INDEX.md"
        current_n = 0
        if idx_path.exists():
            m = re.search(r"(\d+)\s+lessons", idx_path.read_text(encoding="utf-8")[:500])
            if m:
                current_n = int(m.group(1))
        if current_n == 0:
            return tasks

        next_path = ROOT / "tasks" / "NEXT.md"
        if not next_path.exists():
            return tasks

        threshold_pat = re.compile(r'\bN[=≈~]\s*(\d{3,})\b')
        seen: set[int] = set()
        for line in next_path.read_text(encoding="utf-8").splitlines():
            if not ("N=" in line or "N≈" in line or "N~" in line):
                continue
            if "e.g." in line or "(e.g" in line:
                continue
            if re.search(r"F-\w+\b.*?RESOLVED|RESOLVED.*?F-\w+\b", line):
                continue
            if re.match(r'\s*-\s+\*\*(actual|diff|expect|state|meta-swarm|check_mode|mode)\*\*:', line):
                continue
            for m in threshold_pat.finditer(line):
                threshold = int(m.group(1))
                if threshold in seen or threshold <= current_n:
                    continue
                if current_n >= 0.95 * threshold:
                    seen.add(threshold)
                    pct = current_n / threshold * 100
                    context = line.strip()[:80]
                    tasks.append({
                        "priority": P_DUE, "tier": "DUE", "score": 88,
                        "action": f"95%-rule: N={threshold} threshold at {pct:.0f}% ({current_n}/{threshold}) — act now",
                        "detail": context, "command": None,
                    })
    except Exception:
        pass
    return tasks
