#!/usr/bin/env python3
"""Session trigger evaluation extracted from orient.py (DOMEX-META-S423).

Contains: evaluate_session_triggers, write_trigger_manifest.
"""

import re
from pathlib import Path


def evaluate_session_triggers(current_session, ROOT, maint_out="",
                               stale_infra=None, check_stale_beliefs_fn=None):
    """Read SESSION-TRIGGER.md and evaluate trigger conditions (L-640).

    Accepts pre-computed maint_out and stale_infra to avoid redundant subprocess
    calls (orient.py already runs these in main). Before this fix, maintenance.py
    was called 3 times per orient — ~60s on WSL. Now: 1 call, result reused.
    """
    trigger_path = ROOT / "domains" / "meta" / "SESSION-TRIGGER.md"
    if not trigger_path.exists():
        return None, []

    try:
        trigger_text = trigger_path.read_text(encoding="utf-8")
    except Exception:
        return None, []

    trigger_lines = []
    for line in trigger_text.splitlines():
        if line.startswith("- **") and ": " in line and " | " in line:
            trigger_lines.append(line)

    active_triggers = []
    urgency_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

    for line in trigger_lines:
        parts = line.split(" | ")
        if len(parts) < 2:
            continue

        name_desc = parts[0].replace("- **", "").replace("**", "")
        if ": " not in name_desc:
            continue

        trigger_name, description = name_desc.split(": ", 1)
        urgency = parts[1].strip()

        triggered = False

        if trigger_name == "maintenance_due":
            if "[DUE]" in maint_out:
                triggered = True

        elif trigger_name == "stale_tools":
            if stale_infra is not None:
                if len(stale_infra) > 10:
                    triggered = True

        elif trigger_name == "periodics_due":
            if "[PERIODIC]" in maint_out and maint_out.count("~") > 5:
                triggered = True

        elif trigger_name == "dispatch_imbalance":
            triggered = True

        elif trigger_name == "belief_staleness":
            if check_stale_beliefs_fn:
                stale_beliefs = check_stale_beliefs_fn(current_session, ROOT)
                if len(stale_beliefs) > 0:
                    triggered = True

        if triggered:
            active_triggers.append((trigger_name, description, urgency, urgency_order.get(urgency, 1)))

    active_triggers.sort(key=lambda x: x[3], reverse=True)

    top_trigger = active_triggers[0] if active_triggers else None
    return top_trigger, active_triggers[:5]


def write_trigger_manifest(current_session, maint_out, stale_lanes, ROOT,
                            frontier_text=""):
    """Update domains/meta/SESSION-TRIGGER.md with live trigger states (F-META6, F-META9).

    Evaluates all 7 triggers (T1-T7) and writes state to SESSION-TRIGGER.md
    so external executors (autoswarm.sh, cron) can determine if a session is needed.
    """
    trigger_path = ROOT / "domains" / "meta" / "SESSION-TRIGGER.md"
    if not trigger_path.exists():
        return
    try:
        content = trigger_path.read_text()
        now_sess = f"S{current_session}"

        def update_row(text, tid, state):
            pattern = rf"(\| {re.escape(tid)} \|[^|]+\|[^|]+\| ?)(FIRING|CLEAR|UNKNOWN)( ?\| S\d+)"
            repl = rf"\g<1>{state}\g<3>"
            new = re.sub(pattern, repl, text)
            pattern2 = rf"(\| {re.escape(tid)} \|[^|]+\|[^|]+\| ?(?:FIRING|CLEAR|UNKNOWN) ?\| )S\d+( \|)"
            return re.sub(pattern2, rf"\g<1>{now_sess}\g<2>", new)

        # T1: Stale lanes opened in prior session without update
        t1 = "FIRING" if any(sl.get("opened", current_session) < current_session for sl in stale_lanes) else "CLEAR"
        content = update_row(content, "T1-STALE-LANE", t1)

        # T2: Active lane with artifact path but file missing on disk
        t2 = "FIRING" if any(not sl.get("has_artifact") and sl.get("artifact") for sl in stale_lanes) else "CLEAR"
        content = update_row(content, "T2-ARTIFACT-MISSING", t2)

        # T3: Maintenance DUE items present
        t3 = "FIRING" if "[DUE]" in maint_out and "!" in maint_out else "CLEAR"
        content = update_row(content, "T3-MAINTENANCE-DUE", t3)

        # T4: Anxiety-zone frontiers (open >15 sessions without update)
        t4 = "CLEAR"
        if frontier_text and current_session > 0:
            anxiety_count = 0
            current_frontier_sessions = []
            for line in frontier_text.splitlines():
                if line.strip().startswith("- **F"):
                    if current_frontier_sessions:
                        max_s = max(current_frontier_sessions)
                        if current_session - max_s > 15:
                            anxiety_count += 1
                    current_frontier_sessions = []
                for m in re.finditer(r'\bS(\d{2,4})\b', line):
                    s_num = int(m.group(1))
                    if 1 <= s_num <= current_session + 5:
                        current_frontier_sessions.append(s_num)
            if current_frontier_sessions:
                max_s = max(current_frontier_sessions)
                if current_session - max_s > 15:
                    anxiety_count += 1
            if anxiety_count > 0:
                t4 = "FIRING"
        content = update_row(content, "T4-ANXIETY-ZONE", t4)

        # T5: Top-3 dispatch domain has no active DOMEX lane
        t5 = "CLEAR"
        try:
            lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
            if lanes_path.exists():
                lanes_text = lanes_path.read_text(encoding="utf-8")
                has_active_domex = bool(re.search(r'DOMEX-[^|]+\| ACTIVE', lanes_text))
                if not has_active_domex:
                    t5 = "FIRING"
        except Exception:
            pass
        content = update_row(content, "T5-DISPATCH-GAP", t5)

        # T6: Health-check periodic overdue by >2 intervals
        t6 = "CLEAR"
        hc_match = re.search(r'\[health-check\].*last: S(\d+)', maint_out)
        if hc_match:
            hc_last = int(hc_match.group(1))
            if current_session - hc_last > 10:
                t6 = "FIRING"
        content = update_row(content, "T6-HEALTH-CHECK", t6)

        # T7: Proxy-K drift > 10%
        t7 = "CLEAR"
        if "proxy" in maint_out.lower() and "URGENT" in maint_out:
            t7 = "FIRING"
        content = update_row(content, "T7-PROXY-K-DRIFT", t7)

        trigger_path.write_text(content)
    except Exception:
        pass
