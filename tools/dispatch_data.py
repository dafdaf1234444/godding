#!/usr/bin/env python3
"""Data-loading functions extracted from dispatch_optimizer.py (DOMEX-META-S427).

Contains: _load_calibration, _recalibrate, _compute_gini, _get_domain_heat,
_get_active_lane_domains, _get_session_merged_domains, _get_recent_lane_domains,
_get_claimed_domains, _get_domain_outcomes, campaign wrappers.
"""

import json
import math
import re
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from domain_map import LANE_ABBREV_TO_DOMAIN, COUNCIL_TOPIC_TO_DOMAIN
    _DOMAIN_MAP_IMPORTED = True
except ImportError:
    _DOMAIN_MAP_IMPORTED = False

try:
    from dispatch_campaigns import (
        get_campaign_waves, campaign_phase, wave_prescriptions,
        print_wave_plan, print_campaign_advisory,
        get_domain_resolved_frontier_ids,
        COMMIT_RESERVATION_WINDOW,
    )
    _CAMPAIGNS_IMPORTED = True
except ImportError:
    _CAMPAIGNS_IMPORTED = False
    COMMIT_RESERVATION_WINDOW = 5

LANES_FILE = Path("tasks/SWARM-LANES.md")
LANES_ARCHIVE = Path("tasks/SWARM-LANES-ARCHIVE.md")
CALIBRATION_FILE = Path("tools/dispatch_calibration.json")

# Inline fallback domain maps (only used when domain_map.py import fails)
if not _DOMAIN_MAP_IMPORTED:
    LANE_ABBREV_TO_DOMAIN = {
        "NK": "nk-complexity", "LNG": "linguistics", "EXP": "expert-swarm",
        "STAT": "statistics", "PHI": "philosophy", "CTX": "meta", "MECH": "meta",
        "FLD": "fluid-dynamics", "BRN": "brain", "HLP": "helper-swarm",
        "ECO": "economy", "PHY": "physics", "SCI": "evaluation", "EVO": "evolution",
        "DNA": "meta", "IS": "information-science", "HS": "human-systems",
        "COMP": "competitions", "INFO": "information-science",
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
    COUNCIL_TOPIC_TO_DOMAIN = {
        "AGENT-AWARE": "meta", "SCIENCE": "evaluation", "DNA": "meta",
        "EXPERT-SWARM": "expert-swarm", "USE-CASES": "meta",
    }


def _resolve_domain(lane_id: str, etc: str) -> str | None:
    """Resolve domain name from lane ID or etc/focus field."""
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
    return dom


def _parse_lanes_lines() -> list[str]:
    """Read and concatenate lines from SWARM-LANES.md and archive."""
    contents = []
    for f in (LANES_FILE, LANES_ARCHIVE):
        if f.exists():
            contents.append(f.read_text())
    return "\n".join(contents).splitlines() if contents else []


def load_calibration() -> dict | None:
    """Load empirically-derived weights from calibration artifact."""
    if not CALIBRATION_FILE.exists():
        return None
    try:
        with open(CALIBRATION_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def recalibrate() -> dict | None:
    """Re-derive dispatch weights from current outcome data."""
    import subprocess
    script = Path("experiments/expert-swarm/f_exp10_self_calibration.py")
    if not script.exists():
        print("ERROR: calibration script not found at", script, file=sys.stderr)
        return None
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, timeout=60
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return None
    return load_calibration()


def compute_gini(values: list[int | float]) -> float:
    """Compute Gini coefficient of a list of non-negative values. 0=equal, 1=max inequality."""
    n = len(values)
    if n == 0 or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    numerator = sum((2 * i - n - 1) * v for i, v in enumerate(sorted_vals, 1))
    return numerator / (n * sum(sorted_vals))


def get_domain_heat() -> dict[str, int]:
    """Parse SWARM-LANES.md + archive to find the most recent session each domain was active.

    Returns {domain_name: last_active_session_number}.
    Bug fix (L-625, S358): reads both active and archive files.
    """
    heat: dict[str, int] = {}
    for line in _parse_lanes_lines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue
        lane_id = cols[2] if len(cols) > 2 else ""
        etc = cols[10] if len(cols) > 10 else ""
        dom = _resolve_domain(lane_id, etc)
        if not dom:
            continue
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

    Returns {domain_name: [lane_id, ...]}.
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
        dom = _resolve_domain(lane_id, etc)
        latest_per_lane[lane_id] = {"domain": dom, "status": status}
    for lane_id, info in latest_per_lane.items():
        if info["status"] not in ACTIVE_STATUSES:
            continue
        dom = info["domain"]
        if dom:
            active.setdefault(dom, []).append(lane_id)
    return active


def get_session_merged_domains(session: int) -> dict[str, list[str]]:
    """Return domains with MERGED lanes from the given session."""
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


def get_recent_lane_domains(n: int = None) -> list[str]:
    """Return the domains of the most recent N closed lanes (chronological order).

    Used by COMMIT reservation (F-STR3, L-815).
    """
    if n is None:
        n = COMMIT_RESERVATION_WINDOW
    lanes: list[tuple[int, str]] = []
    for line in _parse_lanes_lines():
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
        dom = _resolve_domain(lane_id, etc)
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


def _build_lesson_sharpe_cache() -> dict[str, int]:
    """Build lesson ID → Sharpe score cache from lesson files (L-1127 Channel 3 fix)."""
    cache: dict[str, int] = {}
    lesson_dir = Path("memory/lessons")
    if not lesson_dir.exists():
        return cache
    for f in lesson_dir.iterdir():
        if f.name.startswith("L-") and f.suffix == ".md":
            lid = f.stem.split("-")[1] if "-" in f.stem else ""
            try:
                text = f.read_text(errors="replace")
                m = re.search(r"Sharpe:\s*(\d+)", text)
                if m:
                    cache[lid] = int(m.group(1))
            except Exception:
                pass
    return cache


_lesson_sharpe_cache = _build_lesson_sharpe_cache()


def get_domain_outcomes(at_session: int | None = None) -> dict[str, dict]:
    """Parse SWARM-LANES.md for MERGED/ABANDONED counts and lesson yield per domain (F-EXP10).

    Returns {domain_name: {"merged": int, "abandoned": int, "lessons": int, "lessons_l3plus": int,
             "sharpe_sum": int, "sharpe_count": int}}.

    at_session: if set, only count lanes closed at-or-before this session number.
    Use for trajectory analysis (label_at_time) to prevent retrospective label drift
    (L-946, L-948: 27.3% of domains show label drift; L-963).
    """
    outcomes: dict[str, dict] = {}
    for line in _parse_lanes_lines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue
        lane_id = cols[2] if len(cols) > 2 else ""
        status = cols[11] if len(cols) > 11 else ""
        if status not in ("MERGED", "ABANDONED"):
            continue
        # Temporal filter: label_at_time — skip lanes closed after at_session (L-946, L-963)
        if at_session is not None:
            close_col = cols[3] if len(cols) > 3 else ""
            close_m = re.match(r"S(\d+)", close_col)
            if close_m and int(close_m.group(1)) > at_session:
                continue
        etc = cols[10] if len(cols) > 10 else ""
        domain = _resolve_domain(lane_id, etc)
        if domain:
            if domain not in outcomes:
                outcomes[domain] = {"merged": 0, "abandoned": 0, "lessons": 0,
                                    "lessons_l3plus": 0, "sharpe_sum": 0, "sharpe_count": 0}
            outcomes[domain]["merged" if status == "MERGED" else "abandoned"] += 1
            notes = cols[12] if len(cols) > 12 else ""
            lesson_ids = re.findall(r"\bL-(\d{3,4})\b", notes)
            outcomes[domain]["lessons"] += len(lesson_ids)
            level_m = re.search(r"\blevel=L([1-5])\b", etc)
            if level_m and int(level_m.group(1)) >= 3:
                outcomes[domain]["lessons_l3plus"] += len(lesson_ids)
            # Track Sharpe per domain for quality-weighted dispatch (L-1127 Channel 3 fix)
            for lid in lesson_ids:
                sharpe = _lesson_sharpe_cache.get(lid)
                if sharpe is not None:
                    outcomes[domain]["sharpe_sum"] += sharpe
                    outcomes[domain]["sharpe_count"] += 1
    return outcomes


# Campaign wave wrappers — delegate to dispatch_campaigns.py
def get_domain_resolved_frontier_ids_wrapper() -> set[str]:
    if _CAMPAIGNS_IMPORTED:
        return get_domain_resolved_frontier_ids()
    return set()


def get_campaign_waves_wrapper() -> dict[str, dict]:
    if _CAMPAIGNS_IMPORTED:
        return get_campaign_waves(LANE_ABBREV_TO_DOMAIN)
    return {}


def campaign_phase_wrapper(waves: int) -> tuple[str, str]:
    if _CAMPAIGNS_IMPORTED:
        return campaign_phase(waves)
    if waves == 0: return "new", ""
    elif waves == 2: return "danger", "COMMIT 3rd wave"
    elif waves >= 4: return "veteran", f"sustained ({waves} waves)"
    return "single", ""


def wave_prescriptions_wrapper(cw: dict[str, dict]) -> list[dict]:
    if _CAMPAIGNS_IMPORTED:
        return wave_prescriptions(cw)
    return []


def print_wave_plan_wrapper(prescriptions: list[dict]) -> None:
    if _CAMPAIGNS_IMPORTED:
        print_wave_plan(prescriptions)
    elif prescriptions:
        print(f"\n--- Wave Plan: {len(prescriptions)} campaigns (dispatch_campaigns.py unavailable) ---")
