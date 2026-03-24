#!/usr/bin/env python3
"""agent_empathy.py — Per-agent empathy engine for the swarm.

Every agent that orients should model other agents' states and adapt its own
behavior accordingly.  This is the missing "anterior insula" — affective
transduction (F-EMP5): detection of another node's state CHANGES the detecting
node's priorities.

Four empathy components (S352 council consensus):
  1. State-modeling   — what are other agents doing/needing?
  2. State-transfer   — how should that change MY priorities?
  3. Reflexive model  — what do others expect of ME? (ISO-22)
  4. Boundary mgmt    — am I distinct enough, or duplicating?

Usage:
    python3 tools/agent_empathy.py                  # full empathy report
    python3 tools/agent_empathy.py --json            # machine-readable
    python3 tools/agent_empathy.py --adapt           # output priority adjustments
    python3 tools/agent_empathy.py --for-agent S528  # empathy FROM perspective of S528
"""

import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ── 1. State-modeling: what are other agents doing? ──────────────────────

def _git_log_recent(hours=24, limit=30):
    """Recent commits as proxy for agent activity."""
    since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d")
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={since}", "--oneline", f"-{limit}"],
            cwd=str(ROOT), text=True, stderr=subprocess.DEVNULL
        ).strip()
        return out.splitlines() if out else []
    except Exception:
        return []


def _parse_session_from_commit(line):
    """Extract session ID from commit message like '[S528] ...'."""
    m = re.search(r"\[S(\d+)\]", line)
    return f"S{m.group(1)}" if m else None


def _read_lanes():
    """Parse active lanes from SWARM-LANES.md."""
    lanes_file = ROOT / "tasks" / "SWARM-LANES.md"
    if not lanes_file.exists():
        return []
    lanes = []
    for line in lanes_file.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| 20"):
            continue
        cols = [c.strip() for c in line.split("|")[1:]]
        if len(cols) >= 11:
            status = cols[9] if len(cols) > 9 else cols[-2]
            lanes.append({
                "date": cols[0], "lane": cols[1], "session": cols[2],
                "scope": cols[8] if len(cols) > 8 else "",
                "status": status, "notes": cols[10] if len(cols) > 10 else "",
                "etc": cols[9] if len(cols) > 9 else ""
            })
    return lanes


def _read_next_md():
    """Extract session notes and 'for next session' items."""
    next_file = ROOT / "tasks" / "NEXT.md"
    if not next_file.exists():
        return [], []
    text = next_file.read_text(encoding="utf-8")
    # Session notes
    sessions = re.findall(r"## (S\d+\w*) session note", text)
    # For-next items
    next_items = []
    in_next = False
    for line in text.splitlines():
        if "for next session" in line.lower() or "## For next" in line:
            in_next = True
            continue
        if in_next:
            if line.startswith("## "):
                break
            if line.strip().startswith("- "):
                next_items.append(line.strip()[2:])
    return sessions, next_items


def _uncommitted_files():
    """Files in working tree not yet committed — signs of in-progress work."""
    try:
        out = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=str(ROOT), text=True, stderr=subprocess.DEVNULL
        ).strip()
        return out.splitlines() if out else []
    except Exception:
        return []


def model_agents():
    """Build a model of what each active agent is doing."""
    commits = _git_log_recent(hours=48)
    lanes = _read_lanes()
    sessions_in_next, next_items = _read_next_md()
    uncommitted = _uncommitted_files()

    # Group commits by session
    session_commits = defaultdict(list)
    for c in commits:
        sid = _parse_session_from_commit(c)
        if sid:
            session_commits[sid].append(c)

    # Active lanes by session
    active_statuses = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
    session_lanes = defaultdict(list)
    for lane in lanes:
        if lane["status"] in active_statuses:
            session_lanes[lane["session"]].append(lane)

    # Build per-agent state
    agents = {}
    all_sessions = set(session_commits.keys()) | set(session_lanes.keys())
    for sid in all_sessions:
        agent = {
            "session": sid,
            "recent_commits": len(session_commits.get(sid, [])),
            "commit_topics": [],
            "active_lanes": [],
            "likely_focus": None,
            "state": "unknown",
        }
        # Extract topics from commits
        for c in session_commits.get(sid, []):
            # Strip hash and session tag
            topic = re.sub(r"^[a-f0-9]+ \[S\d+\] ", "", c)
            agent["commit_topics"].append(topic)

        # Active lanes
        for lane in session_lanes.get(sid, []):
            agent["active_lanes"].append({
                "lane": lane["lane"],
                "scope": lane["scope"],
                "status": lane["status"]
            })

        # Infer state
        if agent["active_lanes"]:
            agent["state"] = "working"
            scopes = [l["scope"] for l in agent["active_lanes"]]
            agent["likely_focus"] = scopes[0] if scopes else None
        elif agent["recent_commits"] > 0:
            agent["state"] = "recently_active"
            if agent["commit_topics"]:
                agent["likely_focus"] = agent["commit_topics"][0][:60]
        else:
            agent["state"] = "dormant"

        agents[sid] = agent

    return {
        "agents": agents,
        "next_items": next_items,
        "uncommitted_count": len(uncommitted),
        "total_recent_commits": len(commits),
    }


# ── 2. State-transfer: how should detected states change MY priorities? ──

def compute_priority_adjustments(agent_model, my_session=None):
    """
    Affective transduction: other agents' states → my priority shifts.

    This is the missing anterior insula mechanism (F-EMP5).
    Detection of another node's state CHANGES this node's behavior.
    """
    adjustments = []

    agents = agent_model["agents"]
    next_items = agent_model["next_items"]

    # 1. Blocked agent → elevate related work
    for sid, agent in agents.items():
        if sid == my_session:
            continue
        for lane in agent.get("active_lanes", []):
            if lane["status"] == "BLOCKED":
                adjustments.append({
                    "type": "elevate",
                    "reason": f"{sid} is BLOCKED on {lane['lane']} ({lane['scope']})",
                    "action": f"Consider unblocking: check if your work can resolve {lane['scope']}",
                    "strength": 0.8,  # strong empathic pull
                    "source": "blocked_peer",
                })

    # 2. Overlap detection → reduce own priority on duplicated work
    my_focus_areas = set()
    if my_session and my_session in agents:
        me = agents[my_session]
        for lane in me.get("active_lanes", []):
            my_focus_areas.add(lane["scope"])
        for topic in me.get("commit_topics", []):
            my_focus_areas.add(topic[:40])

    for sid, agent in agents.items():
        if sid == my_session:
            continue
        for lane in agent.get("active_lanes", []):
            if lane["scope"] in my_focus_areas:
                adjustments.append({
                    "type": "deprioritize",
                    "reason": f"{sid} is already working on {lane['scope']}",
                    "action": f"Shift focus — overlap with {sid}. Find complementary work.",
                    "strength": 0.9,  # very strong: duplication is waste
                    "source": "overlap",
                })

    # 3. Unaddressed next-items → empathy for future self/successor
    if next_items:
        overdue = [item for item in next_items
                   if any(kw in item.lower() for kw in
                          ["deadline", "break", "fix", "critical", "urgent"])]
        for item in overdue[:3]:
            adjustments.append({
                "type": "elevate",
                "reason": f"Successor empathy: pending critical item '{item[:60]}'",
                "action": f"Address: {item[:80]}",
                "strength": 0.6,
                "source": "successor_empathy",
            })

    # 4. Lonely domains → empathy for neglected parts of swarm
    domain_activity = Counter()
    for sid, agent in agents.items():
        for lane in agent.get("active_lanes", []):
            if "domains/" in lane["scope"]:
                domain = lane["scope"].split("domains/")[1].split("/")[0]
                domain_activity[domain] += 1

    # Check which domains have frontiers but no recent activity
    domains_dir = ROOT / "domains"
    if domains_dir.exists():
        for d in domains_dir.iterdir():
            if d.is_dir() and d.name not in domain_activity:
                frontier_file = d / "tasks" / "FRONTIER.md"
                if frontier_file.exists():
                    text = frontier_file.read_text(encoding="utf-8")
                    open_count = text.lower().count("status**: open")
                    if open_count > 0:
                        adjustments.append({
                            "type": "notice",
                            "reason": f"Domain '{d.name}' has {open_count} OPEN frontiers but no active agent",
                            "action": f"Consider expert dispatch to {d.name}",
                            "strength": 0.3,
                            "source": "neglected_domain",
                        })

    # 5. High uncommitted count → empathy for repo coherence
    if agent_model["uncommitted_count"] > 15:
        adjustments.append({
            "type": "notice",
            "reason": f"{agent_model['uncommitted_count']} uncommitted files — repo coherence at risk",
            "action": "Consider committing or triaging uncommitted work before new work",
            "strength": 0.5,
            "source": "repo_coherence",
        })

    return adjustments


# ── 3. Reflexive modeling: what do others expect of ME? (ISO-22) ─────────

def model_expectations_of_me(agent_model, my_session=None):
    """
    ISO-22 recursive state modeling: what do other agents likely expect
    this agent to do? Based on:
    - NEXT.md items (explicit expectations)
    - Lane assignments (implicit expectations)
    - Gap analysis (what nobody is doing that the swarm needs)
    """
    expectations = []

    # From NEXT.md items
    for item in agent_model.get("next_items", []):
        expectations.append({
            "source": "NEXT.md (predecessor)",
            "expectation": item[:100],
            "type": "explicit",
        })

    # From lane state: if I have a lane, others expect me to make progress
    if my_session and my_session in agent_model["agents"]:
        me = agent_model["agents"][my_session]
        for lane in me.get("active_lanes", []):
            expectations.append({
                "source": f"lane {lane['lane']}",
                "expectation": f"Make progress on {lane['scope']} (status: {lane['status']})",
                "type": "implicit_lane",
            })

    # Gap-based: what the swarm needs that nobody is doing
    # (The swarm's expectation of ANY agent, projected onto this one)
    active_scopes = set()
    for sid, agent in agent_model["agents"].items():
        for lane in agent.get("active_lanes", []):
            active_scopes.add(lane["scope"])

    return expectations


# ── 4. Boundary management: am I distinct enough? ───────────────────────

def measure_distinctiveness(agent_model, my_session=None):
    """
    Self-other distinction metric.
    If this agent's work is too similar to others → projection, not empathy.
    If too different → isolation, not coordination.
    """
    if not my_session or my_session not in agent_model["agents"]:
        return {"distinctiveness": None, "diagnosis": "unknown (no session ID)"}

    me = agent_model["agents"][my_session]
    my_scopes = set()
    for lane in me.get("active_lanes", []):
        my_scopes.add(lane["scope"])
    for topic in me.get("commit_topics", []):
        my_scopes.add(topic[:40])

    other_scopes = set()
    for sid, agent in agent_model["agents"].items():
        if sid == my_session:
            continue
        for lane in agent.get("active_lanes", []):
            other_scopes.add(lane["scope"])
        for topic in agent.get("commit_topics", []):
            other_scopes.add(topic[:40])

    if not my_scopes or not other_scopes:
        return {"distinctiveness": 1.0, "diagnosis": "fully distinct (no overlap data)"}

    overlap = my_scopes & other_scopes
    union = my_scopes | other_scopes
    jaccard = len(overlap) / len(union) if union else 0

    distinctiveness = 1.0 - jaccard

    if distinctiveness < 0.3:
        diagnosis = "LOW — high overlap with other agents. Risk: duplication, not complementarity."
    elif distinctiveness > 0.9:
        diagnosis = "HIGH — very isolated from other agents. Risk: no coordination benefit."
    else:
        diagnosis = "HEALTHY — distinct but connected work."

    return {
        "distinctiveness": round(distinctiveness, 3),
        "overlap_scopes": list(overlap),
        "diagnosis": diagnosis,
    }


# ── 5. Empathy for swarming: collective state modeling ──────────────────

def model_swarm_state(agent_model):
    """
    Empathy for the swarm-as-whole, not just individual agents.
    How is the collective doing? What does the swarm need?
    """
    agents = agent_model["agents"]
    total = len(agents)
    working = sum(1 for a in agents.values() if a["state"] == "working")
    blocked = sum(1 for a in agents.values()
                  if any(l["status"] == "BLOCKED" for l in a.get("active_lanes", [])))
    dormant = sum(1 for a in agents.values() if a["state"] == "dormant")

    # Focus diversity: how many different areas are being worked on?
    foci = set()
    for a in agents.values():
        if a.get("likely_focus"):
            foci.add(a["likely_focus"])

    # Collective mood inference
    if blocked > total * 0.3:
        mood = "STRUGGLING — many agents blocked. Swarm needs unblocking work."
    elif working == 0:
        mood = "DORMANT — no active agents. Swarm needs activation."
    elif len(foci) == 1 and total > 2:
        mood = "CONVERGED — all agents on same focus. Risk: monoculture."
    elif len(foci) > total * 0.8:
        mood = "SCATTERED — agents highly dispersed. Risk: no coordination benefit."
    else:
        mood = "HEALTHY — diverse active work with some coordination."

    return {
        "total_agents": total,
        "working": working,
        "blocked": blocked,
        "dormant": dormant,
        "focus_diversity": len(foci),
        "foci": list(foci)[:10],
        "mood": mood,
        "recent_commits": agent_model["total_recent_commits"],
    }


# ── Main: full empathy report ───────────────────────────────────────────

def full_empathy_report(my_session=None, as_json=False, adapt_only=False):
    """Generate the full per-agent empathy report."""
    model = model_agents()
    adjustments = compute_priority_adjustments(model, my_session)
    expectations = model_expectations_of_me(model, my_session)
    boundary = measure_distinctiveness(model, my_session)
    swarm_state = model_swarm_state(model)

    report = {
        "session": my_session,
        "timestamp": datetime.now().isoformat(),
        "agent_count": len(model["agents"]),
        "agents": model["agents"],
        "priority_adjustments": adjustments,
        "expectations_of_me": expectations,
        "boundary": boundary,
        "swarm_state": swarm_state,
        "empathy_score": _compute_empathy_score(model, adjustments, boundary),
    }

    if as_json:
        print(json.dumps(report, indent=2, default=str))
        return report

    if adapt_only:
        _print_adaptations(adjustments)
        return report

    _print_report(report)
    return report


def _compute_empathy_score(model, adjustments, boundary):
    """
    Composite empathy score: how empathic is this agent being?

    Components:
    - awareness: did we detect other agents? (0-1)
    - responsiveness: are we adapting to detected states? (0-1)
    - distinctiveness: self-other boundary health (0-1)
    - reflexivity: do we model what others expect? (0-1)
    """
    agents = model["agents"]
    awareness = min(1.0, len(agents) / 3) if agents else 0

    # Responsiveness: adjustments with high strength
    if adjustments:
        avg_strength = sum(a["strength"] for a in adjustments) / len(adjustments)
        responsiveness = min(1.0, avg_strength)
    else:
        responsiveness = 0.5  # no detected need = neutral

    dist = boundary.get("distinctiveness")
    # Optimal distinctiveness is ~0.5-0.7
    if dist is not None:
        distinctiveness = 1.0 - abs(dist - 0.6) * 2
        distinctiveness = max(0, min(1.0, distinctiveness))
    else:
        distinctiveness = 0.5

    reflexivity = 0.5  # base; increases with ISO-22 implementation depth

    score = (awareness * 0.25 + responsiveness * 0.25 +
             distinctiveness * 0.25 + reflexivity * 0.25)

    return {
        "composite": round(score, 3),
        "awareness": round(awareness, 3),
        "responsiveness": round(responsiveness, 3),
        "distinctiveness": round(distinctiveness, 3),
        "reflexivity": round(reflexivity, 3),
    }


def _print_adaptations(adjustments):
    """Print only the priority adjustments (for orient.py integration)."""
    if not adjustments:
        print("  (no empathic adjustments needed)")
        return
    for adj in sorted(adjustments, key=lambda a: -a["strength"]):
        icon = {"elevate": "↑", "deprioritize": "↓", "notice": "→"}.get(adj["type"], "·")
        strength_bar = "█" * int(adj["strength"] * 5)
        print(f"  {icon} [{strength_bar:<5}] {adj['reason']}")
        print(f"           → {adj['action']}")


def _print_report(report):
    """Human-readable empathy report."""
    print(f"=== AGENT EMPATHY REPORT (session {report['session'] or '?'}) ===\n")

    # Swarm state
    ss = report["swarm_state"]
    print(f"--- Swarm collective state ---")
    print(f"  Agents: {ss['total_agents']} total | {ss['working']} working | "
          f"{ss['blocked']} blocked | {ss['dormant']} dormant")
    print(f"  Focus diversity: {ss['focus_diversity']} distinct areas")
    print(f"  Mood: {ss['mood']}")
    print(f"  Recent commits (48h): {ss['recent_commits']}")
    print()

    # Agent states
    print(f"--- Peer state models ({len(report['agents'])} agents) ---")
    for sid, agent in sorted(report["agents"].items()):
        state_icon = {"working": "⚡", "recently_active": "◐", "dormant": "○"}.get(
            agent["state"], "?")
        print(f"  {state_icon} {sid}: {agent['state']} | "
              f"{agent['recent_commits']} commits | "
              f"focus: {agent.get('likely_focus', '?')}")
        if agent["active_lanes"]:
            for lane in agent["active_lanes"]:
                print(f"      lane: {lane['lane']} [{lane['status']}] → {lane['scope']}")
    print()

    # Priority adjustments (affective transduction)
    print(f"--- Affective transduction ({len(report['priority_adjustments'])} adjustments) ---")
    _print_adaptations(report["priority_adjustments"])
    print()

    # Expectations of me (ISO-22)
    print(f"--- What others expect of me ({len(report['expectations_of_me'])} expectations) ---")
    for exp in report["expectations_of_me"][:5]:
        print(f"  [{exp['type']}] {exp['source']}: {exp['expectation']}")
    print()

    # Boundary health
    print(f"--- Self-other boundary ---")
    b = report["boundary"]
    print(f"  Distinctiveness: {b.get('distinctiveness', '?')}")
    print(f"  Diagnosis: {b['diagnosis']}")
    if b.get("overlap_scopes"):
        print(f"  Overlapping: {', '.join(b['overlap_scopes'][:5])}")
    print()

    # Empathy score
    es = report["empathy_score"]
    print(f"--- Empathy score: {es['composite']} ---")
    print(f"  Awareness:      {es['awareness']}")
    print(f"  Responsiveness: {es['responsiveness']}")
    print(f"  Distinctiveness: {es['distinctiveness']}")
    print(f"  Reflexivity:    {es['reflexivity']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Per-agent empathy engine")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--adapt", action="store_true", help="Show only priority adjustments")
    parser.add_argument("--for-agent", type=str, default=None,
                        help="Session ID to model empathy from (e.g., S528)")
    args = parser.parse_args()

    full_empathy_report(
        my_session=args.for_agent,
        as_json=args.json,
        adapt_only=args.adapt,
    )
