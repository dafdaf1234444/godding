#!/usr/bin/env python3
"""
Lane-parsing utilities extracted from dispatch_optimizer.py (L-941 DI pattern).

Provides functions for parsing SWARM-LANES.md and SWARM-LANES-ARCHIVE.md to
determine domain heat, active lanes, merged domains, recent closures, claims,
and outcome statistics. All logic is identical to the original private functions
in dispatch_optimizer.py, with underscores removed to form the public API.
"""

import re
import os
import json
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from domain_map import LANE_ABBREV_TO_DOMAIN as _LANE_ABBREV_TO_DOMAIN, COUNCIL_TOPIC_TO_DOMAIN as _COUNCIL_TOPIC_TO_DOMAIN
    _DOMAIN_MAP_IMPORTED = True
except ImportError:
    _DOMAIN_MAP_IMPORTED = False

try:
    from dispatch_campaigns import COMMIT_RESERVATION_WINDOW
except ImportError:
    COMMIT_RESERVATION_WINDOW = 5

if _DOMAIN_MAP_IMPORTED:
    LANE_ABBREV_TO_DOMAIN = _LANE_ABBREV_TO_DOMAIN
    COUNCIL_TOPIC_TO_DOMAIN = _COUNCIL_TOPIC_TO_DOMAIN
else:
    LANE_ABBREV_TO_DOMAIN = {
        # Legacy abbreviations (S302-S340 era)
        "NK": "nk-complexity", "LNG": "linguistics", "EXP": "expert-swarm",
        "STAT": "statistics", "PHI": "philosophy", "CTX": "meta", "MECH": "meta",
        "FLD": "fluid-dynamics", "BRN": "brain", "HLP": "helper-swarm",
        "ECO": "economy", "PHY": "physics", "SCI": "evaluation", "EVO": "evolution",
        "DNA": "meta", "IS": "information-science", "HS": "human-systems",
        "COMP": "competitions", "INFO": "information-science",
        # Full-name and common abbreviations (L-676: 33 were missing — 65% data loss)
        "META": "meta", "SP": "stochastic-processes", "EMP": "empathy",
        "AI": "ai", "CON": "conflict", "CONFLICT": "conflict",
        "CAT": "catastrophic-risks", "DS": "distributed-systems",
        "FIN": "finance", "GOV": "governance", "EVAL": "evaluation",
        "FRA": "fractals", "FRACTALS": "fractals", "GT": "graph-theory",
        "GTH": "graph-theory", "GAME": "gaming", "GAMING": "gaming",
        "SEC": "security", "SECURITY": "security",
        "GUE": "guesstimates", "GAM": "game-theory", "PSY": "psychology",
        "SOC": "social-media", "STR": "strategy", "QC": "quality",
        "QUALITY": "quality", "OR": "operations-research", "OPS": "operations-research",
        "FARMING": "farming", "FAR": "farming", "COORD": "meta", "HUMAN": "human-systems",
        "INFOFLOW": "information-science", "INFRA": "meta", "GEN": "meta",
        "DREAM": "dream", "BRAIN": "brain", "ECON": "economy", "ECONOMY": "economy",
        "EMPATHY": "empathy", "EVOLUTION": "evolution", "EXPERT": "expert-swarm",
        "AGENT": "meta", "CT": "meta", "CTL": "control-theory",
        "CC": "cryptocurrency", "CRY": "cryptography", "CRYPTO": "cryptocurrency",
        "CRYPTOGRAPHY": "cryptography",
        "PRO": "protocol-engineering", "README": "meta",
        "SCHED": "meta", "PRIORITY": "meta", "UNIVERSALITY": "meta",
        "PERSONALITY": "psychology",
    }
    # COUNCIL-TOPIC-SN: map council topic to domain (F-EXP10 L-506: COUNCIL lanes were
    # previously unattributed, causing ~30-40% outcome data loss for meta/expert-swarm)
    COUNCIL_TOPIC_TO_DOMAIN = {
        "AGENT-AWARE": "meta", "SCIENCE": "evaluation", "DNA": "meta",
        "EXPERT-SWARM": "expert-swarm", "USE-CASES": "meta",
    }

LANES_FILE = Path("tasks/SWARM-LANES.md")
LANES_ARCHIVE = Path("tasks/SWARM-LANES-ARCHIVE.md")

# Outcome feedback constants (F-EXP10, L-501 P1)
OUTCOME_MIN_N = 5          # minimum completed lanes before feedback kicks in (raised 3→5: L-946 label drift)
OUTCOME_SUCCESS_THRESHOLD = 0.75  # MERGED rate above which domain is PROVEN
OUTCOME_FAILURE_THRESHOLD = 0.50  # MERGED rate below which domain is STRUGGLING


def get_domain_heat() -> dict[str, int]:
    """Parse SWARM-LANES.md + archive to find the most recent session each domain was active.

    Returns {domain_name: last_active_session_number}.
    Used for anti-clustering: recently active domains get a score penalty.
    Bug fix (L-625, S358): previously only read LANES_FILE, missing archive.
    Domains with 47+ visits were classified as NEW (+13 boost). Now reads both files
    and uses DOMEX lane prefix + COUNCIL topic mapping (same as _get_domain_outcomes).
    """
    heat: dict[str, int] = {}
    contents: list[str] = []
    for f in (LANES_FILE, LANES_ARCHIVE):
        if f.exists():
            contents.append(f.read_text())
    if not contents:
        return heat
    for line in "\n".join(contents).splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue
        lane_id = cols[2] if len(cols) > 2 else ""
        etc = cols[10] if len(cols) > 10 else ""
        # Resolve domain using same logic as _get_domain_outcomes
        dom = None
        m = re.match(r"DOMEX-([A-Z]+)", lane_id)
        if m:
            dom = LANE_ABBREV_TO_DOMAIN.get(m.group(1))
        if not dom:
            m = re.match(r"COUNCIL-([A-Z-]+)-S\d+", lane_id)
            if m:
                dom = COUNCIL_TOPIC_TO_DOMAIN.get(m.group(1))
        if not dom:
            focus_m = re.search(r"focus=(?:domains/)?([a-z0-9-]+)", etc)
            if focus_m and focus_m.group(1) not in ("global", ""):
                dom = focus_m.group(1)
        if not dom:
            continue
        # Extract session number
        sess_str = cols[3] if len(cols) > 3 else ""
        sess_m = re.search(r"S?(\d+)", sess_str)
        if not sess_m:
            continue
        sess = int(sess_m.group(1))
        if dom not in heat or sess > heat[dom]:
            heat[dom] = sess
    return heat


def get_active_lane_domains() -> dict[str, list[str]]:
    """Find domains with currently ACTIVE/CLAIMED/READY lanes in SWARM-LANES.md.

    Returns {domain_name: [lane_id, ...]}. Used to warn about dispatch collisions
    at N>=5 concurrent sessions (L-733, F-STR2: staleness sole abandonment cause).
    """
    active: dict[str, list[str]] = {}
    if not LANES_FILE.exists():
        return active
    ACTIVE_STATUSES = {"ACTIVE", "CLAIMED", "READY", "BLOCKED"}
    latest_per_lane: dict[str, dict] = {}
    for line in LANES_FILE.read_text().splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue
        lane_id = cols[2] if len(cols) > 2 else ""
        status = cols[11].upper() if len(cols) > 11 else ""
        etc = cols[10] if len(cols) > 10 else ""
        if not lane_id or lane_id == "Lane":
            continue
        dom = None
        m = re.match(r"DOMEX-([A-Z]+)", lane_id)
        if m:
            dom = LANE_ABBREV_TO_DOMAIN.get(m.group(1))
        if not dom:
            focus_m = re.search(r"focus=(?:domains/)?([a-z0-9-]+)", etc)
            if focus_m and focus_m.group(1) not in ("global", ""):
                dom = focus_m.group(1)
        latest_per_lane[lane_id] = {"domain": dom, "status": status}
    for lane_id, info in latest_per_lane.items():
        if info["status"] not in ACTIVE_STATUSES:
            continue
        dom = info["domain"]
        if dom:
            active.setdefault(dom, []).append(lane_id)
    return active


def get_session_merged_domains(session: int) -> dict[str, list[str]]:
    """Return domains with MERGED lanes from the given session.

    Used to show 'DONE this session' marker in dispatch output, preventing
    duplicate lane-open attempts when prior concurrent work already covered domain.
    """
    merged: dict[str, list[str]] = {}
    if not LANES_FILE.exists():
        return merged
    session_tag = f"-S{session}"
    for line in LANES_FILE.read_text().splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue
        lane_id = cols[2] if len(cols) > 2 else ""
        status = cols[11].upper() if len(cols) > 11 else ""
        if not lane_id or lane_id == "Lane":
            continue
        if status == "MERGED" and session_tag in lane_id:
            dom = None
            m = re.match(r"DOMEX-([A-Z]+)", lane_id)
            if m:
                dom = LANE_ABBREV_TO_DOMAIN.get(m.group(1))
            if dom:
                merged.setdefault(dom, []).append(lane_id)
    return merged


def get_recent_lane_domains(n: int = COMMIT_RESERVATION_WINDOW) -> list[str]:
    """Return the domains of the most recent N closed lanes (chronological order).

    Used by COMMIT reservation (F-STR3, L-815) to check whether a danger-zone
    domain has been dispatched recently. Only counts MERGED/ABANDONED lanes
    (completed work, not in-progress).
    """
    lanes: list[tuple[int, str]] = []  # (session_num, domain)
    contents: list[str] = []
    for f in (LANES_FILE, LANES_ARCHIVE):
        if f.exists():
            contents.append(f.read_text())
    for line in "\n".join(contents).splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue
        lane_id = cols[2] if len(cols) > 2 else ""
        status = cols[11].strip().upper() if len(cols) > 11 else ""
        if status not in ("MERGED", "ABANDONED"):
            continue
        sess_str = cols[3] if len(cols) > 3 else ""
        sess_m = re.search(r"S?(\d+)", sess_str)
        if not sess_m:
            continue
        sess = int(sess_m.group(1))
        etc = cols[10] if len(cols) > 10 else ""
        dom = None
        m = re.match(r"DOMEX-([A-Z]+)", lane_id)
        if m:
            dom = LANE_ABBREV_TO_DOMAIN.get(m.group(1))
        if not dom:
            m_c = re.match(r"COUNCIL-([A-Z-]+)-S\d+", lane_id)
            if m_c:
                dom = COUNCIL_TOPIC_TO_DOMAIN.get(m_c.group(1))
        if not dom:
            focus_m = re.search(r"focus=(?:domains/)?([a-z0-9-]+)", etc)
            if focus_m and focus_m.group(1) not in ("global", ""):
                dom = focus_m.group(1)
        if dom:
            lanes.append((sess, dom))
    lanes.sort(key=lambda x: x[0])
    return [dom for _, dom in lanes[-n:]]


def get_claimed_domains() -> set[str]:
    """Get domains currently claimed by active agents (from agent_state.py)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("agent_state", Path("tools/agent_state.py"))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return set(mod.get_active_domains())
    except Exception:
        pass
    return set()


def get_domain_outcomes(at_session: int | None = None) -> dict[str, dict]:
    """Parse SWARM-LANES.md for MERGED/ABANDONED counts and lesson yield per domain (F-EXP10).

    Returns {domain_name: {"merged": int, "abandoned": int, "lessons": int, "lessons_l3plus": int}}.
    - merged/abandoned: binary outcome (existing)
    - lessons: L-NNN references in notes column (yield quality signal — L-506)
    - lessons_l3plus: lessons from lanes tagged level=L3/L4/L5 (L-895, SIG-46)
    Outcome feedback: reward proven domains, flag struggling ones.

    at_session: if set, only count lanes closed at-or-before this session number.
    Use for trajectory analysis to compute label_at_time — prevents retrospective label drift
    (L-946, L-948: 27.3% of domains show label drift across eras). L-963.
    """
    outcomes: dict[str, dict] = {}
    # Read both active lanes and archive for complete outcome history (L-562, L-572, F-EXP10)
    contents = []
    for f in (LANES_FILE, LANES_ARCHIVE):
        if f.exists():
            contents.append(f.read_text())
    if not contents:
        return outcomes
    for line in "\n".join(contents).splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue
        lane_id = cols[2] if len(cols) > 2 else ""
        status = cols[11] if len(cols) > 11 else ""
        if status not in ("MERGED", "ABANDONED"):
            continue

        # Temporal filter: skip lanes closed after at_session (label_at_time — L-946, L-963)
        if at_session is not None:
            close_col = cols[3] if len(cols) > 3 else ""
            close_m = re.match(r"S(\d+)", close_col)
            if close_m and int(close_m.group(1)) > at_session:
                continue

        etc = cols[10] if len(cols) > 10 else ""

        # Try domain from DOMEX lane name: DOMEX-ABBREV-SN
        domain = None
        m = re.match(r"DOMEX-([A-Z]+)", lane_id)
        if m:
            domain = LANE_ABBREV_TO_DOMAIN.get(m.group(1))

        # COUNCIL-TOPIC-SN: attribute council lanes to domain (L-506: was causing
        # ~30-40% outcome data loss for meta/expert-swarm — COUNCIL lanes unattributed)
        if not domain:
            m = re.match(r"COUNCIL-([A-Z-]+)-S\d+", lane_id)
            if m:
                domain = COUNCIL_TOPIC_TO_DOMAIN.get(m.group(1))

        # Fallback: focus= field (skip if "global")
        if not domain:
            fm = re.search(r"focus=(?:domains/)?([a-z0-9-]+)", etc)
            if fm and fm.group(1) not in ("global", ""):
                domain = fm.group(1)

        if domain:
            if domain not in outcomes:
                outcomes[domain] = {"merged": 0, "abandoned": 0, "lessons": 0, "lessons_l3plus": 0}
            outcomes[domain]["merged" if status == "MERGED" else "abandoned"] += 1
            # Lesson yield: count L-NNN references in notes column
            notes = cols[12] if len(cols) > 12 else ""
            lesson_count = len(re.findall(r"\bL-\d{3,4}\b", notes))
            outcomes[domain]["lessons"] += lesson_count
            # Level-weighted yield (L-895, SIG-46): L3+ lanes get bonus lesson credit
            level_m = re.search(r"\blevel=L([1-5])\b", etc)
            if level_m and int(level_m.group(1)) >= 3:
                outcomes[domain]["lessons_l3plus"] += lesson_count
    return outcomes
