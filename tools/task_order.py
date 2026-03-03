#!/usr/bin/env python3
"""
task_order.py — Session task ordering for swarm nodes.

Synthesizes maintenance DUE items, active lane status, untracked artifacts,
and dispatch scores into a prioritized, numbered task list for the current session.

Replaces ad-hoc NEXT.md scanning with structured, scored ordering.
Addresses the "task ordering tooling swarm for swarm" meta-improvement.

Usage:
    python3 tools/task_order.py              # ordered task list
    python3 tools/task_order.py --json       # machine-readable output
    python3 tools/task_order.py --top N      # show top N tasks (default 8)
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANES_FILE = ROOT / "tasks" / "SWARM-LANES.md"

from task_order_helpers import (
    _current_session,
    get_zombie_due_items as _get_zombie_due_items,
    get_signal_tasks as _get_signal_tasks,
    get_numeric_condition_due_items as _get_numeric_condition_due_items,
    check_preemption as _check_preemption_ext,
    check_task_claims as _check_task_claims_ext,
    auto_claim_task as _auto_claim_task_ext,
    get_task_fingerprint as _get_task_fingerprint_ext,
)

# Priority tiers (lower = higher priority)
P_COMMIT   = 0   # uncommitted done work
P_DUE      = 1   # DUE maintenance items
P_CLOSE    = 2   # active lanes with artifacts ready to merge
P_STRATEGY = 3   # L3+ strategic work (activated by level imbalance — L-601 enforcement)
P_DISPATCH = 4   # top dispatch domain for new DOMEX
P_PERIODIC = 5   # periodic maintenance
P_META     = 6   # meta-reflection suggestions


def _git(args: list[str]) -> str:
    r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip()


def _detect_concurrency() -> int:
    """Count unique sessions in recent commits to estimate active concurrency.

    At N>=3, proxy absorption (L-526, L-1243) means other sessions commit
    untracked artifacts — manual COMMIT work becomes negative ROI.
    """
    log = _git(["log", "--oneline", "-15"])
    sessions = set()
    for line in log.splitlines():
        m = re.search(r"\[S(\d+)\]", line)
        if m:
            sessions.add(int(m.group(1)))
    return len(sessions)


def get_untracked_artifacts() -> list[dict]:
    """Find untracked lesson + experiment files — likely done work needing commit."""
    output = _git(["status", "--short"])
    tasks = []
    lessons = []
    experiments = []
    for line in output.splitlines():
        status = line[:2].strip()
        path = line[3:].strip()
        if status == "??" and path.startswith("memory/lessons/L-"):
            lessons.append(path)
        elif status == "??" and path.startswith("experiments/"):
            experiments.append(path)
    if lessons or experiments:
        desc_parts = []
        if lessons:
            desc_parts.append(f"{len(lessons)} lesson(s): {', '.join(Path(p).stem for p in lessons)}")
        if experiments:
            desc_parts.append(f"{len(experiments)} experiment(s)")
        # L-1265: at N>=3 concurrency, proxy absorption handles untracked
        # files — manual COMMIT work is negative ROI. Down-weight.
        n_concurrent = _detect_concurrency()
        if n_concurrent >= 3:
            score = 40
            tier_note = f" (down-weighted: {n_concurrent} concurrent sessions)"
        else:
            score = 100
            tier_note = ""
        tasks.append({
            "priority": P_COMMIT if n_concurrent < 3 else P_PERIODIC,
            "tier": "COMMIT",
            "score": score,
            "action": f"Commit untracked artifacts: {'; '.join(desc_parts)}{tier_note}",
            "detail": f"Files: {', '.join(lessons + experiments)}",
            "command": None,
        })
    return tasks


def get_due_items() -> list[dict]:
    """Parse maintenance --quick for DUE items."""
    tasks = []
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "maintenance.py"), "--quick"],
            capture_output=True, text=True, cwd=ROOT, timeout=20
        )
        output = r.stdout + r.stderr
    except Exception:
        return tasks

    for line in output.splitlines():
        if line.strip().startswith("!"):
            clean = re.sub(r"\s+", " ", line.strip().lstrip("! "))
            if clean and len(clean) > 10:
                score = 90 if "[DUE]" in line else 85
                tasks.append({
                    "priority": P_DUE,
                    "tier": "DUE",
                    "score": score,
                    "action": clean,
                    "detail": None,
                    "command": None,
                })
    return tasks


def get_closeable_lanes() -> list[dict]:
    """Find ACTIVE lanes that have their artifact committed (ready to merge)."""
    tasks = []
    if not LANES_FILE.exists():
        return tasks

    # Get committed experiment files
    committed = set(_git(["ls-files", "experiments/"]).splitlines())

    active_lanes = {}
    with open(LANES_FILE) as f:
        for line in f:
            if not line.startswith("|"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 8:
                continue
            lane_id = cols[2]
            status = cols[-2].strip() if len(cols) >= 2 else ""
            etc = cols[10] if len(cols) > 10 else ""
            if status == "ACTIVE" and lane_id and not lane_id.startswith("-"):
                # Extract artifact path from Etc field
                artifact_match = re.search(r"artifact=([^;|]+)", etc)
                artifact = artifact_match.group(1).strip() if artifact_match else None
                active_lanes[lane_id] = {"artifact": artifact, "etc": etc}

    for lane_id, info in active_lanes.items():
        artifact = info["artifact"]
        if artifact and any(artifact in c for c in committed):
            tasks.append({
                "priority": P_CLOSE,
                "tier": "CLOSE",
                "score": 80,
                "action": f"Close lane {lane_id}: artifact committed, ready to MERGE",
                "detail": f"artifact={artifact}",
                "command": f"python3 tools/close_lane.py --lane {lane_id} --status MERGED --actual '...' --diff '...' --note '...'",
            })
        elif artifact and not any(artifact in c for c in committed):
            # Artifact declared but not committed — check untracked
            untracked = _git(["status", "--short"])
            if artifact.split("/")[-1] in untracked:
                n_concurrent = _detect_concurrency()
                artifact_score = 40 if n_concurrent >= 3 else 95
                tasks.append({
                    "priority": P_COMMIT if n_concurrent < 3 else P_PERIODIC,
                    "tier": "COMMIT",
                    "score": artifact_score,
                    "action": f"Commit artifact for {lane_id}: {artifact}",
                    "detail": "Artifact untracked — commit first, then close lane",
                    "command": None,
                })
        else:
            # No artifact yet — needs work
            frontier_match = re.search(r"frontier=([^;|]+)", info["etc"])
            frontier = frontier_match.group(1).strip() if frontier_match else "?"
            tasks.append({
                "priority": P_DISPATCH,
                "tier": "ACTIVE",
                "score": 70,
                "action": f"Produce artifact for active lane {lane_id} (frontier={frontier})",
                "detail": "Lane ACTIVE but no artifact — do the experiment",
                "command": None,
            })
    return tasks


def get_strategy_tasks() -> list[dict]:
    """Generate L3+ strategy task when level imbalance fires (L-601, L-895)."""
    tasks = []
    lessons_dir = ROOT / "memory" / "lessons"
    if not lessons_dir.exists():
        return tasks

    # Check recent 10 lessons for L3+ keywords (mirrors orient.py logic)
    lesson_files = sorted(lessons_dir.glob("L-*.md"), key=lambda f: f.stat().st_mtime, reverse=True)[:10]
    l3plus_kw = ["strategy", "campaign", "architecture", "organizational",
                 "paradigm", "redesign", "direction", "what should", "reframing",
                 "missing layer", "system design", "philosophy", "identity"]
    l3plus_count = 0
    for lf in lesson_files:
        try:
            txt = lf.read_text()[:600].lower()
            if any(k in txt for k in l3plus_kw):
                l3plus_count += 1
        except Exception:
            pass

    if l3plus_count > 0:
        return tasks  # no imbalance — skip

    # Gather strategy topics from open signals and frontiers
    topics = []
    signals_file = ROOT / "tasks" / "SIGNALS.md"
    if signals_file.exists():
        try:
            for line in signals_file.read_text().splitlines():
                if "OPEN" in line and ("SIG-" in line):
                    m = re.search(r"(SIG-\d+).*?:\s*(.{10,60})", line)
                    if m:
                        topics.append(f"{m.group(1)}: {m.group(2).strip()}")
        except Exception:
            pass

    topic_hint = topics[0] if topics else "architectural review of swarm pipeline or belief challenge"

    tasks.append({
        "priority": P_STRATEGY,
        "tier": "STRATEGY",
        "score": 78,
        "action": f"Produce L3+ lesson (strategy/architecture/paradigm) — level imbalance critical",
        "detail": f"0/{len(lesson_files)} recent lessons at L3+. Suggested topic: {topic_hint}",
        "command": None,
    })
    return tasks


def get_signal_tasks() -> list[dict]:
    """Route stale/partially-resolved signals (SIG-2). Delegated to task_order_helpers."""
    return _get_signal_tasks(P_DUE, P_STRATEGY)


def get_zombie_due_items() -> list[dict]:
    """Surface zombie Next: items as DUE tasks (L-978 TG-2). Delegated to task_order_helpers."""
    return _get_zombie_due_items(P_DUE)


def get_numeric_condition_due_items() -> list[dict]:
    """Surface near-threshold items as DUE (L-1062). Delegated to task_order_helpers."""
    return _get_numeric_condition_due_items(P_DUE)


def get_dispatch_tasks() -> list[dict]:
    """Get top-3 dispatch recommendations that don't have active lanes."""
    tasks = []
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "dispatch_optimizer.py"), "--json"],
            capture_output=True, text=True, cwd=ROOT, timeout=30
        )
        data = json.loads(r.stdout)
        recommendations = data.get("recommendations", [])[:5]
    except Exception:
        return tasks

    # Get active lane domains
    active_domains = set()
    if LANES_FILE.exists():
        with open(LANES_FILE) as f:
            for line in f:
                if "ACTIVE" in line and line.startswith("|"):
                    # Extract domain from lane ID (e.g., DOMEX-META-S359 → meta)
                    cols = [c.strip() for c in line.split("|")]
                    lane_id = cols[2] if len(cols) > 2 else ""
                    m = re.search(r"DOMEX-([A-Z]+)-", lane_id)
                    if m:
                        abbrev = m.group(1)
                        domain_map = {
                            "NK": "nk-complexity", "META": "meta", "BRN": "brain",
                            "GOV": "governance", "EXP": "expert-swarm", "DS": "distributed-systems",
                            "FIN": "finance", "CON": "conflict", "AI": "ai",
                            "IS": "information-science", "SP": "stochastic-processes",
                            "ECO": "economy", "QC": "quality", "HLP": "helper-swarm",
                        }
                        active_domains.add(domain_map.get(abbrev, abbrev.lower()))

    for rec in recommendations:
        domain = rec.get("domain", "")
        if domain in active_domains:
            continue  # already have an active lane for this domain
        score = rec.get("score", 0)
        frontier = rec.get("top_frontier", {})
        frontier_id = frontier.get("id", "?")
        frontier_q = frontier.get("question", "")[:60]
        status = rec.get("status", "")
        dormant = "DORMANT" in status.upper()
        tasks.append({
            "priority": P_DISPATCH,
            "tier": "DISPATCH" + (" [DORMANT]" if dormant else ""),
            "score": score,
            "action": f"Open DOMEX lane for {domain} (score {score:.1f}): {frontier_id}",
            "detail": frontier_q,
            "command": f"python3 tools/open_lane.py --domain {domain} --frontier {frontier_id}",
        })
    return tasks[:3]  # top 3 dispatch suggestions


def get_periodic_tasks() -> list[dict]:
    """Get overdue periodic maintenance. L-985: >1 cadence overdue escalates to DUE."""
    tasks = []
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "maintenance.py"), "--quick"],
            capture_output=True, text=True, cwd=ROOT, timeout=20
        )
        output = r.stdout + r.stderr
    except Exception:
        return tasks

    # Check periodics.json for escalation candidates (overdue by >1 cadence)
    escalated_labels: set[str] = set()
    try:
        pj_path = ROOT / "tools" / "periodics.json"
        pj = json.loads(pj_path.read_text(encoding="utf-8"))
        sess = _current_session()
        for item in pj.get("items", []):
            last = item.get("last_reviewed_session") or item.get("last_session", 0)
            if isinstance(last, str):
                m = re.search(r"(\d+)", last)
                last = int(m.group(1)) if m else 0
            cadence = item.get("cadence_sessions", 10)
            overdue_by = sess - (last + cadence)
            if overdue_by >= cadence:  # overdue by one full cadence or more
                escalated_labels.add(item["id"])
    except Exception:
        pass

    in_periodic = False
    for line in output.splitlines():
        if "[PERIODIC]" in line:
            in_periodic = True
            continue
        if in_periodic and line.strip().startswith("~"):
            clean = re.sub(r"\s+", " ", line.strip().lstrip("~ "))
            # Extract label in brackets
            m = re.match(r"\[([^\]]+)\]\s*(.*)", clean)
            label = m.group(1) if m else "periodic"
            detail = (m.group(2) if m else clean)[:80]
            escalated = label in escalated_labels
            tasks.append({
                "priority": P_DUE if escalated else P_PERIODIC,
                "tier": "DUE" if escalated else "PERIODIC",
                "score": 80 if escalated else 30,
                "action": f"Periodic: {label}" + (" [ESCALATED >2x overdue]" if escalated else ""),
                "detail": detail,
                "command": None,
            })
        elif in_periodic and not line.strip().startswith("~") and line.strip() and not line.startswith(" "):
            in_periodic = False
    return tasks[:3]  # top 3 periodic items


def get_meta_tasks() -> list[dict]:
    """Standard meta-session suggestions."""
    return [
        {
            "priority": P_META,
            "tier": "META",
            "score": 20,
            "action": "Meta-reflection: identify one friction or improvement in swarming process",
            "detail": "Write lesson if finding is novel; update SWARM.md/bridge files if process change",
            "command": None,
        },
        {
            "priority": P_META,
            "tier": "META",
            "score": 15,
            "action": "Handoff: sync_state.py + validate_beliefs.py + NEXT.md update",
            "detail": "Commit: [S<N>] what: why",
            "command": "python3 tools/sync_state.py && python3 tools/validate_beliefs.py",
        },
    ]


def _check_preemption(tasks: list[dict]) -> list[dict]:
    """Mark tasks preempted by recent commits (FM-28). Delegated to task_order_helpers."""
    return _check_preemption_ext(tasks, P_DISPATCH, P_STRATEGY)


def _get_task_fingerprint(task: dict) -> str:
    """Generate stable fingerprint. Delegated to task_order_helpers."""
    return _get_task_fingerprint_ext(task)


def _check_task_claims(tasks: list[dict]) -> list[dict]:
    """Mark tasks claimed by other sessions (L-686). Delegated to task_order_helpers."""
    return _check_task_claims_ext(tasks)


def _auto_claim_task(task: dict) -> None:
    """Automatically claim the top task (L-686). Delegated to task_order_helpers."""
    _auto_claim_task_ext(task)


def build_task_list(top_n: int = 8) -> list[dict]:
    """Build ranked task list for current session."""
    all_tasks = []
    all_tasks.extend(get_untracked_artifacts())
    all_tasks.extend(get_due_items())
    all_tasks.extend(get_zombie_due_items())
    all_tasks.extend(get_numeric_condition_due_items())
    all_tasks.extend(get_closeable_lanes())
    all_tasks.extend(get_strategy_tasks())
    all_tasks.extend(get_signal_tasks())
    all_tasks.extend(get_dispatch_tasks())
    all_tasks.extend(get_periodic_tasks())
    all_tasks.extend(get_meta_tasks())

    # Check task claims from other sessions (L-686)
    all_tasks = _check_task_claims(all_tasks)

    # Check preemption by recent commits (FM-28 hardening)
    all_tasks = _check_preemption(all_tasks)

    # Sort: priority tier first, then score descending
    all_tasks.sort(key=lambda t: (t["priority"], -t["score"]))

    # Deduplicate by action prefix
    seen = set()
    deduped = []
    for t in all_tasks:
        key = t["action"][:40]
        if key not in seen:
            seen.add(key)
            deduped.append(t)

    return deduped[:top_n]


TIER_COLORS = {
    "COMMIT":   "\033[91m",  # red
    "DUE":      "\033[93m",  # yellow
    "CLOSE":    "\033[92m",  # green
    "STRATEGY": "\033[95m",  # magenta — L3+ strategic work
    "SIGNAL-ACTION": "\033[95m",  # magenta — signal gap closure
    "SIGNAL-QUESTION": "\033[93m",  # yellow — human decision needed
    "ACTIVE":   "\033[96m",  # cyan
    "DISPATCH": "\033[94m",  # blue
    "DISPATCH [DORMANT]": "\033[94m",
    "NOVEL":    "\033[95m",  # magenta — preemption redirect
    "PERIODIC": "\033[37m",  # gray
    "META":     "\033[90m",  # dark gray
}
RESET = "\033[0m"


def main():
    parser = argparse.ArgumentParser(description="Session task ordering for swarm nodes")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--top", type=int, default=8, help="Number of tasks to show")
    parser.add_argument("--claim-top", action="store_true",
                        help="Auto-claim the top unclaimed task (L-686)")
    args = parser.parse_args()

    tasks = build_task_list(top_n=args.top)

    if args.claim_top:
        # Find first unclaimed task and claim it
        for task in tasks:
            if "claimed_by" not in task:
                _auto_claim_task(task)
                if not args.json:
                    print(f"AUTO-CLAIMED: {task.get('fingerprint', '?')} → {task['action'][:60]}")
                break

    if args.json:
        print(json.dumps({"tasks": tasks}, indent=2))
        return

    # Get session number
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "swarm_io.py")],
            capture_output=True, text=True, cwd=ROOT, timeout=5
        )
        sn_match = re.search(r"\[S(\d+)\]", _git(["log", "--oneline", "-3"]))
        session = int(sn_match.group(1)) if sn_match else "?"
    except Exception:
        session = "?"

    # Count claimed tasks
    claimed_count = sum(1 for t in tasks if "claimed_by" in t)
    header = f"\n=== TASK ORDER S{session} ({len(tasks)} items"
    if claimed_count:
        header += f", {claimed_count} claimed by others"
    header += ") ===\n"
    print(header)

    for i, task in enumerate(tasks, 1):
        tier = task["tier"]
        # Strip [CLAIMED] suffix for color lookup
        base_tier = tier.replace(" [CLAIMED]", "")
        color = TIER_COLORS.get(base_tier, TIER_COLORS.get(tier, ""))
        score = task["score"]
        action = task["action"]
        detail = task.get("detail", "")
        cmd = task.get("command", "")
        claimed = task.get("claimed_by", "")

        preempted = task.get("preempted", False)

        print(f"  [{i}] {color}[{tier}]{RESET} (score={score:.0f}) {action}")
        if claimed:
            print(f"       ⚠ claimed by {claimed}")
        if preempted and not claimed:
            print(f"       ⚠ likely done by recent commit — verify before executing")
        if detail:
            print(f"       → {detail}")
        if cmd:
            print(f"       $ {cmd}")
        print()

    print("Focus on [1] first. Declare expectation before acting.")
    print("Use --claim-top to auto-claim [1] and prevent concurrent duplication.")
    print("Run python3 tools/task_order.py after each task to re-rank.\n")


if __name__ == "__main__":
    main()
