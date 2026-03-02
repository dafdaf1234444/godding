#!/usr/bin/env python3
"""PCI computation extracted from orient.py (DOMEX-META-S423).

Contains: compute_pci — Protocol Compliance Index (EAD * belief_freshness * frontier_testability).
"""

import re
from pathlib import Path


def compute_pci(current_session, ROOT, read_file):
    """Compute Protocol Compliance Index — scientific rigor gap metric.

    PCI = EAD_compliance * belief_freshness * frontier_testability

    - EAD_compliance: fraction of last 20 MERGED lanes with actual= AND diff=
      (both non-TBD) in their Etc column.
    - belief_freshness: fraction of beliefs tested within last 50 sessions.
    - frontier_testability: fraction of active frontiers with session-tagged
      evidence (S\\d+ pattern) in their entry.

    Returns dict with {ead, belief_freshness, frontier_testability, pci, details}.
    """
    details = {}

    # --- EAD compliance (from SWARM-LANES.md) ---
    lanes_text = read_file("tasks/SWARM-LANES.md")
    lane_rows = []
    for line in lanes_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 12:
            continue
        if cells[1].startswith("---") or cells[1] == "Date":
            continue
        status = cells[11] if len(cells) > 11 else ""
        etc = cells[10] if len(cells) > 10 else ""
        if not status.strip():
            continue
        lane_rows.append({"etc": etc, "status": status.strip()})

    recent_lanes = lane_rows[-20:] if len(lane_rows) > 20 else lane_rows
    ead_compliant = 0
    ead_total = len(recent_lanes)
    for lr in recent_lanes:
        etc = lr["etc"]
        has_actual = bool(re.search(r"actual=(?!TBD)", etc))
        has_diff = bool(re.search(r"diff=(?!TBD)", etc))
        if has_actual and has_diff:
            ead_compliant += 1
    ead_score = ead_compliant / ead_total if ead_total > 0 else 0.0
    details["ead"] = f"{ead_compliant}/{ead_total}"

    # --- Belief freshness (from beliefs/DEPS.md) ---
    deps_text = read_file("beliefs/DEPS.md")
    fresh_count = 0
    total_beliefs = 0
    for block in re.split(r"\n(?=### B)", deps_text):
        bid_m = re.match(r"### (B[\w-]*\d+)", block)
        if not bid_m:
            continue
        if "~~" in block.split("\n")[0]:
            continue
        total_beliefs += 1
        lt_m = re.search(r"\*\*Last tested\*\*:\s*([^\n]+)", block)
        if not lt_m:
            continue
        tested_text = lt_m.group(1)
        if "Not yet tested" in tested_text:
            continue
        sessions = [int(s) for s in re.findall(r"S(\d+)", tested_text)]
        if not sessions:
            continue
        last_session = max(sessions)
        if current_session - last_session <= 50:
            fresh_count += 1
    bf_score = fresh_count / total_beliefs if total_beliefs > 0 else 0.0
    details["belief_freshness"] = f"{fresh_count}/{total_beliefs}"

    # --- Frontier testability (from tasks/FRONTIER.md) ---
    frontier_text = read_file("tasks/FRONTIER.md")
    active_frontiers = 0
    evidenced_frontiers = 0
    in_active_section = False
    for line in frontier_text.splitlines():
        if re.match(r"^## (Critical|Important|Exploratory)", line):
            in_active_section = True
            continue
        if re.match(r"^## (Archive|Domain frontiers)", line):
            in_active_section = False
            continue
        if not in_active_section:
            continue
        if re.match(r"^- \*\*F[\w-]+\*\*:", line):
            active_frontiers += 1
            if re.search(r"\bS\d+\b", line):
                evidenced_frontiers += 1
    ft_score = evidenced_frontiers / active_frontiers if active_frontiers > 0 else 0.0
    details["frontier_testability"] = f"{evidenced_frontiers}/{active_frontiers}"

    pci = ead_score * bf_score * ft_score

    return {
        "ead": ead_score,
        "belief_freshness": bf_score,
        "frontier_testability": ft_score,
        "pci": pci,
        "details": details,
    }
