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
        tasks.append({
            "priority": P_COMMIT,
            "tier": "COMMIT",
            "score": 100,
            "action": f"Commit untracked artifacts: {'; '.join(desc_parts)}",
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
                tasks.append({
                    "priority": P_COMMIT,
                    "tier": "COMMIT",
                    "score": 95,
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
    """Generate L3+ strategy task when level imbalance fires (L-601 enforcement).

    The level imbalance (L-895, SIG-46) means 0 recent L3+ lessons. The swarm's
    pipeline (dispatch→DOMEX→measurement) structurally excludes strategic work.
    This function injects a STRATEGY-tier task that scores above DISPATCH,
    creating a structural path for L3+ work per L-601 (voluntary → enforcement).
    """
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
    """Route stale/partially-resolved signals to actionable tasks (SIG-2 closure).

    Closes the signal-to-action gap identified in SIG-2 (71 sessions PARTIALLY
    RESOLVED): signals inform but don't trigger lanes or actions. This function
    reads SIGNALS.md and generates specific tasks for signals that need work.
    """
    tasks = []
    signals_file = ROOT / "tasks" / "SIGNALS.md"
    if not signals_file.exists():
        return tasks

    try:
        # Get current session number for age calculation
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
            sig_type = cols[6]   # directive, observation, question
            priority = cols[7]
            content = cols[8][:80]
            status = cols[9]
            resolution = cols[10] if len(cols) > 10 else ""

            sess_m = re.search(r"S?(\d+)", session_str)
            sig_session = int(sess_m.group(1)) if sess_m else 0
            age = current_session - sig_session

            # Route PARTIALLY RESOLVED signals with identified gaps
            if status == "PARTIALLY RESOLVED" and age > 15:
                gap_m = re.search(r"[Gg]ap:\s*(.{10,80})", resolution)
                gap = gap_m.group(1).rstrip(". |") if gap_m else "incomplete implementation"
                score = 76 if priority == "P1" else 72
                tasks.append({
                    "priority": P_STRATEGY,
                    "tier": "SIGNAL-ACTION",
                    "score": score,
                    "action": f"Close {sig_id} gap ({age}s stale): {gap[:60]}",
                    "detail": f"[{sig_type}] {content}",
                    "command": None,
                })

            # Route OPEN question signals targeting human
            elif status == "OPEN" and sig_type == "question":
                tasks.append({
                    "priority": P_DUE,
                    "tier": "SIGNAL-QUESTION",
                    "score": 82,
                    "action": f"Escalate {sig_id} to human: {content[:50]}",
                    "detail": f"OPEN question signal, age {age}s — needs human decision",
                    "command": None,
                })
    except Exception:
        pass

    return tasks[:5]  # cap at 5 signal-derived tasks


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
    """Get overdue periodic maintenance from maintenance output."""
    tasks = []
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "maintenance.py"), "--quick"],
            capture_output=True, text=True, cwd=ROOT, timeout=20
        )
        output = r.stdout + r.stderr
    except Exception:
        return tasks

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
            tasks.append({
                "priority": P_PERIODIC,
                "tier": "PERIODIC",
                "score": 30,
                "action": f"Periodic: {label}",
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


def _get_task_fingerprint(task: dict) -> str:
    """Generate a stable fingerprint from a task for claim deconfliction.

    Fingerprints map tasks to claim.py task claims so concurrent sessions
    avoid duplicating work (L-686).
    """
    action = task["action"]
    # Extract bracketed label from maintenance items: "[state-sync]" → "state-sync"
    m = re.match(r".*\[([^\]]+)\]", action)
    if m:
        return m.group(1).lower().strip()
    # Dispatch tasks: "Open DOMEX lane for cryptography" → "dispatch:cryptography"
    m = re.search(r"DOMEX.*?for\s+(\S+)", action)
    if m:
        return f"dispatch:{m.group(1).lower()}"
    # Close tasks: "Close lane DOMEX-CRY-S373" → "close:domex-cry-s373"
    m = re.search(r"Close lane\s+(\S+)", action)
    if m:
        return f"close:{m.group(1).lower()}"
    # Periodic tasks: "Periodic: health-check" → "periodic:health-check"
    m = re.match(r"Periodic:\s*(\S+)", action)
    if m:
        return f"periodic:{m.group(1).lower()}"
    # Trim tasks: "Lesson over 20 lines: L-925.md" → "trim:L-925" (L-933: unique per-lesson)
    m = re.match(r"Lesson over 20 lines:\s*(L-\d+)", action)
    if m:
        return f"trim:{m.group(1)}"
    # Fallback: normalized first 40 chars
    return re.sub(r"[^a-z0-9]+", "-", action[:40].lower()).strip("-")


def _check_task_claims(tasks: list[dict]) -> list[dict]:
    """Mark tasks claimed by other sessions (L-686).

    Imports claim.py to check active task claims. Claimed tasks get
    deprioritized (score -100) so concurrent sessions pick different work.
    """
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from claim import get_active_task_claims, get_session_id
        my_session = get_session_id()
        claimed = get_active_task_claims(exclude_session=my_session)
    except Exception:
        return tasks  # graceful degradation if claim.py unavailable

    for task in tasks:
        fp = _get_task_fingerprint(task)
        task["fingerprint"] = fp
        if fp in claimed:
            claim_data = claimed[fp]
            task["claimed_by"] = claim_data["session"]
            task["score"] -= 100  # push to bottom
            task["tier"] = f"{task['tier']} [CLAIMED]"
    return tasks


def _auto_claim_task(task: dict) -> None:
    """Automatically claim the top task (L-686).

    Called when --claim-top is used. Claims the task fingerprint so
    concurrent sessions will see it as taken.
    """
    fp = task.get("fingerprint") or _get_task_fingerprint(task)
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from claim import cmd_claim_task, get_session_id
        session = get_session_id()
        cmd_claim_task(fp, session, task["action"][:80])
    except Exception:
        pass  # best-effort


def build_task_list(top_n: int = 8) -> list[dict]:
    """Build ranked task list for current session."""
    all_tasks = []
    all_tasks.extend(get_untracked_artifacts())
    all_tasks.extend(get_due_items())
    all_tasks.extend(get_closeable_lanes())
    all_tasks.extend(get_strategy_tasks())
    all_tasks.extend(get_signal_tasks())
    all_tasks.extend(get_dispatch_tasks())
    all_tasks.extend(get_periodic_tasks())
    all_tasks.extend(get_meta_tasks())

    # Check task claims from other sessions (L-686)
    all_tasks = _check_task_claims(all_tasks)

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

        print(f"  [{i}] {color}[{tier}]{RESET} (score={score:.0f}) {action}")
        if claimed:
            print(f"       ⚠ claimed by {claimed}")
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
