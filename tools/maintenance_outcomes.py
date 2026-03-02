#!/usr/bin/env python3
"""Maintenance outcome tracking and learning extracted from maintenance.py (DOMEX-META-S420).

Contains: _load_outcomes, _save_outcomes_direct, _learn_from_outcomes.
These functions record per-session maintenance check results, classify checks as
CHRONIC/ACTIONABLE/SILENT, and display trends for meta-periodic analysis (F-MECH1, GAP-1).
"""

import json
from pathlib import Path

PRIORITY_ORDER = {"URGENT": 0, "DUE": 1, "PERIODIC": 2, "NOTICE": 3}


def load_outcomes(outcomes_path: Path) -> dict:
    if not outcomes_path.exists():
        return {"schema": "maintenance-outcomes-v1", "sessions": []}
    try:
        return json.loads(outcomes_path.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": "maintenance-outcomes-v1", "sessions": []}


def save_outcomes_direct(
    check_items: dict[str, list[tuple[str, str]]],
    session: int,
    outcomes_path: Path,
    outcomes_max_sessions: int,
):
    data = load_outcomes(outcomes_path)
    checks = {}
    totals: dict[str, int] = {}
    for name, fn_items in check_items.items():
        severities = [sev for sev, _ in fn_items]
        checks[name] = {
            "fired": len(fn_items) > 0,
            "count": len(fn_items),
            "severities": severities,
        }
        for sev in severities:
            totals[sev] = totals.get(sev, 0) + 1
    from datetime import datetime, timezone
    entry = {
        "session": session,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "totals": totals,
    }
    # Deduplicate: replace if same session already recorded
    data["sessions"] = [s for s in data["sessions"] if s.get("session") != session]
    data["sessions"].append(entry)
    # Trim to max sessions
    data["sessions"].sort(key=lambda s: s.get("session", 0))
    if len(data["sessions"]) > outcomes_max_sessions:
        data["sessions"] = data["sessions"][-outcomes_max_sessions:]
    outcomes_path.parent.mkdir(parents=True, exist_ok=True)
    outcomes_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def learn_from_outcomes(outcomes_path: Path):
    data = load_outcomes(outcomes_path)
    sessions = data.get("sessions", [])
    if len(sessions) < 2:
        print("  Need >=2 recorded sessions to learn. Run maintenance checks first.")
        return
    # Collect all check names across sessions
    all_checks: set[str] = set()
    for s in sessions:
        all_checks.update(s.get("checks", {}).keys())
    n = len(sessions)
    print(f"=== MAINTENANCE LEARNING (n={n} sessions, S{sessions[0].get('session','?')}..S{sessions[-1].get('session','?')}) ===\n")
    # Per-check statistics
    stats: list[dict] = []
    for check_name in sorted(all_checks):
        fires = []
        for s in sessions:
            c = s.get("checks", {}).get(check_name, {})
            fires.append(c.get("fired", False))
        fire_count = sum(fires)
        fire_rate = fire_count / n if n > 0 else 0
        # Resolution: fired in session i, not fired in session i+1
        resolutions = 0
        resolution_opportunities = 0
        for i in range(len(fires) - 1):
            if fires[i]:
                resolution_opportunities += 1
                if not fires[i + 1]:
                    resolutions += 1
        resolve_rate = resolutions / resolution_opportunities if resolution_opportunities > 0 else 0
        # Max severity seen
        max_sev = "NOTICE"
        for s in sessions:
            c = s.get("checks", {}).get(check_name, {})
            for sev in c.get("severities", []):
                if PRIORITY_ORDER.get(sev, 99) < PRIORITY_ORDER.get(max_sev, 99):
                    max_sev = sev
        # Classify
        if fire_rate > 0.8 and resolve_rate < 0.2:
            label = "CHRONIC"
        elif fire_rate > 0.3 and resolve_rate > 0.5:
            label = "ACTIONABLE"
        elif fire_rate == 0:
            label = "SILENT"
        else:
            label = "-"
        stats.append({
            "name": check_name, "fire_rate": fire_rate, "resolve_rate": resolve_rate,
            "fire_count": fire_count, "max_sev": max_sev, "label": label,
            "resolutions": resolutions, "opportunities": resolution_opportunities,
        })
    # Sort: CHRONIC first (problem), then ACTIONABLE (productive), then by fire rate
    label_order = {"CHRONIC": 0, "ACTIONABLE": 1, "-": 2, "SILENT": 3}
    stats.sort(key=lambda s: (label_order.get(s["label"], 9), -s["fire_rate"]))
    # Print chronic checks (anti-windup)
    chronic = [s for s in stats if s["label"] == "CHRONIC"]
    if chronic:
        print("  CHRONIC (anti-windup -- fire >80%, resolve <20%):")
        for s in chronic:
            print(f"    {s['name']:<40} fire={s['fire_rate']:.0%}  resolve={s['resolve_rate']:.0%}  max={s['max_sev']}")
        print()
    # Print actionable checks
    actionable = [s for s in stats if s["label"] == "ACTIONABLE"]
    if actionable:
        print("  ACTIONABLE (fire >30%, resolve >50% -- these drive real fixes):")
        for s in actionable:
            print(f"    {s['name']:<40} fire={s['fire_rate']:.0%}  resolve={s['resolve_rate']:.0%}  resolved={s['resolutions']}/{s['opportunities']}")
        print()
    # Print all non-silent
    active = [s for s in stats if s["label"] != "SILENT"]
    if active:
        print(f"  All active checks ({len(active)}/{len(stats)}):")
        for s in active:
            tag = f" [{s['label']}]" if s["label"] not in ("-",) else ""
            print(f"    {s['name']:<40} fire={s['fire_rate']:.0%}  resolve={s['resolve_rate']:.0%}  max={s['max_sev']}{tag}")
        print()
    # Trend: total check items over time
    if len(sessions) >= 3:
        totals_over_time = []
        for s in sessions:
            t = s.get("totals", {})
            totals_over_time.append(sum(t.values()))
        recent_3 = totals_over_time[-3:]
        direction = "declining" if recent_3[-1] < recent_3[0] else ("rising" if recent_3[-1] > recent_3[0] else "stable")
        print(f"  Trend (last 3): {' -> '.join(str(t) for t in recent_3)} ({direction})")
    # Silent checks (never fire -- candidates for removal)
    silent = [s for s in stats if s["label"] == "SILENT"]
    if silent:
        print(f"  Silent ({len(silent)} checks never fired -- may be vestigial):")
        for s in silent[:5]:
            print(f"    {s['name']}")
    print()
