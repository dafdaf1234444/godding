#!/usr/bin/env python3
"""swarm_cycle.py — Programmatic swarm session planner.

Closes the executor-layer gap: SESSION-TRIGGER fires → but nobody reads it
programmatically (SESSION-TRIGGER.md line 47). This tool IS the reader.

The cycle: SENSE → PLAN → PROMPT → (EXECUTE via autoswarm) → MEASURE

Usage:
    python3 tools/swarm_cycle.py                  # human-readable plan
    python3 tools/swarm_cycle.py --json            # structured JSON plan
    python3 tools/swarm_cycle.py --prompt          # claude --print prompt for autoswarm
    python3 tools/swarm_cycle.py --measure S377    # post-session: plan vs outcome
    python3 tools/swarm_cycle.py --history         # show recent cycle plans + outcomes
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

TRIGGER_PATH = ROOT / "domains" / "meta" / "SESSION-TRIGGER.md"
SIGNALS_PATH = ROOT / "tasks" / "SIGNALS.md"
NEXT_PATH = ROOT / "tasks" / "NEXT.md"
LANES_PATH = ROOT / "tasks" / "SWARM-LANES.md"
FRONTIER_PATH = ROOT / "tasks" / "FRONTIER.md"
CYCLE_LOG = ROOT / "workspace" / "swarm-cycle-log.json"

# ---------------------------------------------------------------------------
# SENSE: read all swarm state sources
# ---------------------------------------------------------------------------

def _current_session() -> int:
    """Get current session number from git log."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--oneline", "-20"], cwd=str(ROOT),
            stderr=subprocess.DEVNULL, text=True, timeout=5
        )
        nums = [int(m) for m in re.findall(r"\[S(\d+)\]", out)]
        return max(nums) if nums else 0
    except Exception:
        return 0


def sense_triggers() -> list[dict]:
    """Read SESSION-TRIGGER.md for FIRING triggers."""
    if not TRIGGER_PATH.exists():
        return []
    text = TRIGGER_PATH.read_text()
    triggers = []
    for m in re.finditer(
        r"^\| (T\d+-\S+)\s*\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|",
        text, re.MULTILINE
    ):
        tid, condition, urgency, state, last_checked, action = (
            s.strip() for s in m.groups()
        )
        if state == "FIRING":
            triggers.append({
                "id": tid,
                "condition": condition,
                "urgency": urgency,
                "action": action,
                "last_checked": last_checked,
            })
    # HIGH urgency first
    urgency_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    triggers.sort(key=lambda t: urgency_order.get(t["urgency"], 9))
    return triggers


def sense_signals() -> list[dict]:
    """Read SIGNALS.md for OPEN signals."""
    if not SIGNALS_PATH.exists():
        return []
    text = SIGNALS_PATH.read_text()
    signals = []
    for m in re.finditer(
        r"^\| (SIG-\d+)\s*\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]*)\|",
        text, re.MULTILINE
    ):
        fields = [s.strip() for s in m.groups()]
        sid, date, session, source, target, sig_type, priority, content, status, resolution = fields
        if status == "OPEN":
            signals.append({
                "id": sid, "session": session, "source": source,
                "type": sig_type, "priority": priority,
                "content": content[:120],
            })
    return signals


def sense_dispatch() -> list[dict]:
    """Run dispatch_optimizer.py --json --mode ucb1 and parse results."""
    try:
        out = subprocess.check_output(
            [sys.executable, str(TOOLS / "dispatch_optimizer.py"),
             "--json", "--mode", "ucb1"],
            cwd=str(ROOT), stderr=subprocess.DEVNULL, text=True, timeout=30
        )
        data = json.loads(out)
        # Return top-5 domains
        return data[:5] if isinstance(data, list) else []
    except Exception:
        return []


def sense_next_items() -> list[str]:
    """Extract follow-up items from most recent NEXT.md session note."""
    if not NEXT_PATH.exists():
        return []
    text = NEXT_PATH.read_text()
    # Find the first "Next:" line in the most recent session note
    items = []
    for m in re.finditer(r"^\s*-\s*\*\*Next\*\*:(.+?)$", text, re.MULTILINE):
        raw = m.group(1).strip()
        # Parse numbered items: (1) foo; (2) bar
        for part in re.findall(r"\(\d+\)\s*([^;(]+)", raw):
            items.append(part.strip())
        if items:
            break
    return items[:5]


def sense_active_lanes() -> list[str]:
    """Get currently ACTIVE lane IDs to avoid duplicating work."""
    if not LANES_PATH.exists():
        return []
    text = LANES_PATH.read_text()
    active = set()
    for m in re.finditer(r"^\|[^|]+\|\s*(\S+)\s*\|.*\|\s*(ACTIVE|CLAIMED)\s*\|", text, re.MULTILINE):
        active.add(m.group(1).strip())
    return sorted(active)


def sense_problem_routing() -> list[dict]:
    """Run problem_router.py to get problem→expert mapping (L-716)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "problem_router", str(TOOLS / "problem_router.py"))
        if not spec or not spec.loader:
            return []
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        problems = []
        problems.extend(mod.detect_due_items())
        problems.extend(mod.detect_firing_triggers())
        problems.extend(mod.detect_open_signals())

        routed = []
        for p in problems:
            routes = mod.route_problem(p)
            if routes:
                routed.append({**p, "routes": routes})

        # Aggregate: domain → total demand score
        from collections import defaultdict
        demand = defaultdict(float)
        for rp in routed:
            urgency_weight = {"HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}.get(
                rp.get("urgency", "LOW"), 1.0
            )
            for route in rp["routes"]:
                demand[route["domain"]] += route["confidence"] * urgency_weight

        return sorted(
            [{"domain": d, "demand": round(s, 2)} for d, s in demand.items()],
            key=lambda x: x["demand"], reverse=True
        )
    except Exception:
        return []


# ---------------------------------------------------------------------------
# PLAN: prioritize actions
# ---------------------------------------------------------------------------

def plan(triggers, signals, dispatch, next_items, active_lanes,
         current_session, problem_demand=None) -> dict:
    """Compute a ranked session plan from sensed state.

    L-716 integration: when problem_demand is provided, inject problem-routed
    dispatch recommendations at Priority 2.5 (between triggers and UCB1).
    """
    actions = []

    # Priority 1: HIGH FIRING triggers
    for t in triggers:
        if t["urgency"] == "HIGH":
            actions.append({
                "priority": 1,
                "type": "trigger",
                "id": t["id"],
                "action": t["action"],
                "reason": f"HIGH urgency trigger FIRING: {t['condition'][:80]}",
            })

    # Priority 2: MEDIUM FIRING triggers (maintenance, dispatch gap)
    for t in triggers:
        if t["urgency"] == "MEDIUM":
            actions.append({
                "priority": 2,
                "type": "trigger",
                "id": t["id"],
                "action": t["action"],
                "reason": f"MEDIUM trigger: {t['condition'][:80]}",
            })

    active_domains = set()
    for lane in active_lanes:
        parts = lane.split("-")
        if len(parts) >= 2:
            active_domains.add(parts[1].lower())

    # Priority 2.5: Problem-routed dispatch (L-716)
    # Problems indicate which domains NEED attention, not just which are unexplored
    if problem_demand:
        for pd in problem_demand[:3]:
            domain = pd["domain"]
            abbrev = domain[:3].upper()
            if abbrev.lower() not in active_domains:
                actions.append({
                    "priority": 2,  # same as MEDIUM triggers — problem demand IS urgency
                    "type": "problem_dispatch",
                    "domain": domain,
                    "demand": pd["demand"],
                    "reason": f"Problem demand: {domain} ({pd['demand']:.1f} weighted problems)",
                })

    # Priority 3: Top UCB1 dispatch domain (if no active lane for it)
    for d in dispatch[:3]:
        domain = d.get("domain", "")
        abbrev = domain[:3].upper()
        if abbrev.lower() not in active_domains and not d.get("claimed"):
            actions.append({
                "priority": 3,
                "type": "dispatch",
                "domain": domain,
                "score": d.get("score", 0),
                "frontier": d.get("top_frontier", ""),
                "reason": f"UCB1 exploration: {domain} (score={d.get('score', '?')})",
            })

    # Priority 4: Follow-up items from last session
    for item in next_items[:2]:
        actions.append({
            "priority": 4,
            "type": "follow_up",
            "item": item,
            "reason": f"Follow-up from previous session: {item[:80]}",
        })

    # Priority 5: Human directive signals
    directive_signals = [s for s in signals if s["type"] == "directive"]
    for sig in directive_signals[:2]:
        actions.append({
            "priority": 5,
            "type": "signal",
            "id": sig["id"],
            "content": sig["content"],
            "reason": f"Open directive signal: {sig['content'][:80]}",
        })

    # Priority 6: LOW triggers
    for t in triggers:
        if t["urgency"] == "LOW":
            actions.append({
                "priority": 6,
                "type": "trigger",
                "id": t["id"],
                "action": t["action"],
                "reason": f"LOW trigger: {t['condition'][:80]}",
            })

    actions.sort(key=lambda a: a["priority"])

    # Select primary action (what the session SHOULD do)
    primary = actions[0] if actions else {
        "priority": 99, "type": "idle",
        "reason": "No triggers, no dispatch gaps, no signals. Swarm is current."
    }

    return {
        "session": f"S{current_session + 1}",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "primary": primary,
        "alternatives": actions[1:5],
        "active_lanes": active_lanes,
        "trigger_count": len(triggers),
        "signal_count": len(signals),
        "dispatch_top3": [d.get("domain", "") for d in dispatch[:3]],
        "problem_demand_top3": [pd["domain"] for pd in (problem_demand or [])[:3]],
    }


# ---------------------------------------------------------------------------
# PROMPT: generate a targeted session prompt
# ---------------------------------------------------------------------------

def generate_prompt(plan_result: dict) -> str:
    """Generate a specific claude --print prompt from the session plan."""
    primary = plan_result["primary"]
    session = plan_result["session"]
    parts = [f"You are swarm node {session}. Read SWARM.md. Run python3 tools/orient.py."]

    if primary["type"] == "trigger":
        parts.append(f"\nPRIORITY: Address trigger {primary['id']}: {primary['action']}.")
        parts.append(f"Reason: {primary['reason']}.")

    elif primary["type"] == "problem_dispatch":
        domain = primary.get("domain", "unknown")
        parts.append(f"\nPRIORITY: Domain '{domain}' has {primary.get('demand', '?')} weighted problem demand.")
        parts.append("Problems need this domain's expertise. Open DOMEX lane or address maintenance directly.")

    elif primary["type"] == "dispatch":
        domain = primary.get("domain", "unknown")
        frontier = primary.get("frontier", "")
        parts.append(f"\nPRIORITY: Open DOMEX lane for domain '{domain}'.")
        if frontier:
            parts.append(f"Focus frontier: {frontier}.")
        parts.append("Run dispatch_optimizer.py to confirm. Open lane, execute experiment, produce artifact, commit.")

    elif primary["type"] == "follow_up":
        parts.append(f"\nPRIORITY: Follow up on: {primary['item']}.")

    elif primary["type"] == "signal":
        parts.append(f"\nPRIORITY: Address open signal {primary['id']}: {primary['content']}.")

    else:
        parts.append("\nNo urgent work detected. Run dispatch_optimizer.py and pick highest-scoring domain for DOMEX.")

    # Add alternatives as secondary options
    alts = plan_result.get("alternatives", [])
    if alts:
        parts.append("\nIf primary is already done by a concurrent session, alternatives:")
        for i, alt in enumerate(alts[:3], 1):
            parts.append(f"  {i}. {alt['reason']}")

    parts.append("\nProduce at least one artifact (lesson, experiment JSON, or tool). Commit with [S<N>] format. Hand off.")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# MEASURE: post-session comparison
# ---------------------------------------------------------------------------

def measure(session_tag: str) -> dict:
    """Compare a session plan (from log) against actual git outcomes."""
    # Load the plan from cycle log
    if not CYCLE_LOG.exists():
        return {"error": "No cycle log found"}

    log_data = json.loads(CYCLE_LOG.read_text())
    plans = log_data.get("cycles", [])
    plan_entry = None
    for p in plans:
        if p.get("session") == session_tag:
            plan_entry = p
            break

    if not plan_entry:
        return {"error": f"No plan found for {session_tag}"}

    # Get actual session commits
    try:
        out = subprocess.check_output(
            ["git", "log", "--oneline", f"--grep=[{session_tag}]", "--all"],
            cwd=str(ROOT), stderr=subprocess.DEVNULL, text=True, timeout=5
        )
        commits = [line.strip() for line in out.strip().split("\n") if line.strip()]
    except Exception:
        commits = []

    # Check if primary action was executed
    primary = plan_entry.get("primary", {})
    executed = len(commits) > 0

    # Check if a lesson was produced
    lesson_commits = [c for c in commits if "L-" in c]

    return {
        "session": session_tag,
        "planned_type": primary.get("type", "unknown"),
        "planned_reason": primary.get("reason", ""),
        "commits": len(commits),
        "lesson_commits": len(lesson_commits),
        "executed": executed,
        "commit_messages": commits[:5],
    }


# ---------------------------------------------------------------------------
# LOGGING: persist cycle plans for feedback
# ---------------------------------------------------------------------------

def _log_cycle(plan_result: dict):
    """Append plan to workspace/swarm-cycle-log.json for feedback loop."""
    CYCLE_LOG.parent.mkdir(parents=True, exist_ok=True)
    if CYCLE_LOG.exists():
        try:
            data = json.loads(CYCLE_LOG.read_text())
        except (json.JSONDecodeError, ValueError):
            data = {"cycles": []}
    else:
        data = {"cycles": []}

    data["cycles"].append(plan_result)
    # Keep last 50 cycles
    data["cycles"] = data["cycles"][-50:]
    CYCLE_LOG.write_text(json.dumps(data, indent=2) + "\n")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Programmatic swarm session planner (F-ISG1)"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON plan")
    parser.add_argument("--prompt", action="store_true",
                        help="Output a claude --print prompt for autoswarm")
    parser.add_argument("--measure", metavar="SESSION",
                        help="Post-session measurement (e.g. --measure S377)")
    parser.add_argument("--history", action="store_true",
                        help="Show recent cycle plans")
    parser.add_argument("--no-log", action="store_true",
                        help="Don't persist this plan to cycle log")
    args = parser.parse_args()

    # Measure mode
    if args.measure:
        result = measure(args.measure)
        print(json.dumps(result, indent=2))
        return

    # History mode
    if args.history:
        if not CYCLE_LOG.exists():
            print("No cycle history yet.")
            return
        data = json.loads(CYCLE_LOG.read_text())
        for c in data.get("cycles", [])[-10:]:
            primary = c.get("primary", {})
            print(f"  {c.get('session', '?'):6s}  "
                  f"type={primary.get('type', '?'):12s}  "
                  f"pri={primary.get('priority', '?')}  "
                  f"{primary.get('reason', '')[:60]}")
        return

    # SENSE
    current = _current_session()
    triggers = sense_triggers()
    signals = sense_signals()
    dispatch = sense_dispatch()
    next_items = sense_next_items()
    active_lanes = sense_active_lanes()
    problem_demand = sense_problem_routing()

    # PLAN (L-716: problem-routed dispatch augments UCB1)
    result = plan(triggers, signals, dispatch, next_items, active_lanes,
                  current, problem_demand)

    # LOG
    if not args.no_log:
        _log_cycle(result)

    # OUTPUT
    if args.prompt:
        print(generate_prompt(result))
    elif args.json:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable
        primary = result["primary"]
        print(f"=== SWARM CYCLE PLAN — {result['session']} ===")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Triggers FIRING: {result['trigger_count']}")
        print(f"Signals OPEN: {result['signal_count']}")
        print(f"Active lanes: {', '.join(result['active_lanes']) or 'none'}")
        print(f"Dispatch top-3: {', '.join(result['dispatch_top3'])}")
        print()
        print(f"PRIMARY ACTION (priority {primary.get('priority', '?')}):")
        print(f"  Type: {primary['type']}")
        print(f"  {primary['reason']}")
        if primary.get("action"):
            print(f"  Action: {primary['action']}")
        if primary.get("domain"):
            print(f"  Domain: {primary['domain']}")
        if primary.get("frontier"):
            print(f"  Frontier: {primary['frontier']}")
        alts = result.get("alternatives", [])
        if alts:
            print(f"\nALTERNATIVES ({len(alts)}):")
            for a in alts[:4]:
                print(f"  [{a.get('priority', '?')}] {a['reason'][:80]}")


if __name__ == "__main__":
    main()
