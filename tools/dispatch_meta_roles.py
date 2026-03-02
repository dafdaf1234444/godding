#!/usr/bin/env python3
"""Meta-role classification for dispatch optimizer (SIG-39, L-925).

Extracted from dispatch_optimizer.py to reduce tool size (F-META17).
Classifies meta DOMEX lanes into historian/tooler/experimenter roles.
"""

import re
from pathlib import Path

LANES_FILE = Path("tasks/SWARM-LANES.md")
LANES_ARCHIVE = Path("tasks/SWARM-LANES-ARCHIVE.md")

META_ROLE_KEYWORDS: dict[str, list[str]] = {
    "historian": [
        "historian", "repair", "stale", "belief retest", "health-check",
        "freshness", "staleness", "decay", "retested", "retest belief",
    ],
    "tooler": [
        "tool", "build", "wire", "implement", "fix", "bug", "enforce",
        "wiring", "default-on", "automation", "pipeline", "refactor",
        "maintenance gate", "extraction", "module",
    ],
    "experimenter": [
        "measure", "experiment", "quantif", "falsif", "calibrat", "audit",
        "score", "analysis", "compare", "baseline", "survey", "count",
        "ratio", "test", "diagnos", "distribution", "model",
    ],
}


def classify_meta_role(intent: str, notes: str = "") -> str:
    """Classify a meta DOMEX lane into historian/tooler/experimenter role."""
    text = (intent + " " + notes).lower()
    scores = {}
    for role, keywords in META_ROLE_KEYWORDS.items():
        scores[role] = sum(1 for kw in keywords if kw in text)
    if max(scores.values()) == 0:
        return "unclassified"
    top_role = max(scores, key=scores.get)
    vals = sorted(scores.values(), reverse=True)
    if vals[0] > 0 and (len(vals) < 2 or vals[0] > vals[1]):
        return top_role
    return "mixed"


def get_meta_role_stats(lane_abbrev_to_domain: dict[str, str] | None = None) -> dict:
    """Scan SWARM-LANES for meta domain lanes and classify by role.

    Prefers explicit role= field (SIG-39, open_lane.py --role) over keyword inference.
    Returns {"historian": n, "tooler": n, "experimenter": n, "mixed": n,
             "unclassified": n, "total": n, "suggested_role": str}.
    """
    role_counts = {"historian": 0, "tooler": 0, "experimenter": 0, "mixed": 0, "unclassified": 0}
    for f in (LANES_FILE, LANES_ARCHIVE):
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if not line.startswith("|") or "Lane" in line or "---" in line:
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue
            lane_id = cols[2]
            status = cols[11] if len(cols) > 11 else ""
            etc = cols[10] if len(cols) > 10 else ""
            notes = cols[12] if len(cols) > 12 else ""
            if status not in ("MERGED", "ABANDONED", "ACTIVE"):
                continue
            # Check if this is a meta lane
            is_meta = False
            m = re.match(r"DOMEX-([A-Z]+)", lane_id)
            if m:
                abbrev = m.group(1)
                if lane_abbrev_to_domain:
                    is_meta = lane_abbrev_to_domain.get(abbrev) == "meta"
                else:
                    is_meta = abbrev in ("META", "CTX", "MECH", "DNA", "INFRA",
                                         "GEN", "AGENT", "CT", "SCHED", "PRIORITY",
                                         "UNIVERSALITY", "COORD", "README", "PRO")
            if not is_meta:
                focus_m = re.search(r"focus=(?:domains/)?([a-z0-9-]+)", etc)
                if focus_m and focus_m.group(1) == "meta":
                    is_meta = True
            if not is_meta:
                continue
            # Prefer explicit role= field
            role_m = re.search(r"\brole=(historian|tooler|experimenter)\b", etc)
            if role_m:
                role = role_m.group(1)
            else:
                intent_m = re.search(r"intent=([^;]+)", etc)
                intent = intent_m.group(1) if intent_m else ""
                role = classify_meta_role(intent, notes)
            role_counts[role] += 1
    total = sum(role_counts.values())
    # Suggest the most underserved role
    active_roles = {k: v for k, v in role_counts.items() if k not in ("mixed", "unclassified")}
    suggested = min(active_roles, key=active_roles.get) if active_roles else "tooler"
    return {**role_counts, "total": total, "suggested_role": suggested}
