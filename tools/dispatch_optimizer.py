#!/usr/bin/env python3
"""
Dispatch Optimizer — Expert Economy Tool (F-ECO4)
Scores and ranks domain experiments by expected yield (Sharpe × ISO × maturity).
Addresses structural unemployment of expert capacity (63 unrun experiments, 2% throughput).

Usage:
    python3 tools/dispatch_optimizer.py                 # Top-10 recommendations
    python3 tools/dispatch_optimizer.py --all           # Full ranked list
    python3 tools/dispatch_optimizer.py --domain X      # Score single domain
    python3 tools/dispatch_optimizer.py --json          # JSON output
"""

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from swarm_io import session_number as _session_number
except ImportError:
    def _session_number() -> int:
        import subprocess
        r = subprocess.run(["git", "log", "--oneline", "-50"], capture_output=True, text=True)
        nums = [int(m) for m in re.findall(r"\[S(\d+)\]", r.stdout)]
        return max(nums) if nums else 340


DOMAINS_DIR = Path("domains")
EXPERIMENTS_DIR = Path("experiments")
LANES_FILE = Path("tasks/SWARM-LANES.md")
LANES_ARCHIVE = Path("tasks/SWARM-LANES-ARCHIVE.md")

# Domain heat: evaporation constant per session gap (S340 council: 5/5 convergence)
# Domains touched recently get a penalty; dormant domains get a bonus.
HEAT_DECAY = 0.85  # pheromone decays by 15% per session gap
HEAT_PENALTY_MAX = 6.0  # max score penalty for hot domains
DORMANT_BONUS = 3.0  # bonus for domains untouched >5 sessions
FIRST_VISIT_BONUS = 5.0  # extra bonus for domains with zero DOMEX history (L-548: 90% first-visit merge rate)
SELF_DISPATCH_INTERVAL = 10  # expert-swarm must dispatch to itself every N sessions (L-501 P6)

# Visit saturation (F-ECO5, L-571): diminishing returns for repeatedly visiting same domains.
# Dispatch without this amplifies exploitation, not exploration (Gini 0.36→0.55).
VISIT_SATURATION_SCALE = 1.5  # penalty = scale * ln(1 + visit_count)
EXPLORATION_GINI_THRESHOLD = 0.45  # when visit Gini exceeds this, enter exploration mode
EXPLORATION_NEW_BOOST = 8.0  # extra bonus for unvisited domains in exploration mode
EXPLORATION_COLD_BOOST = 4.0  # extra bonus for dormant domains in exploration mode

# Cooldown window (F-ECO5, L-671): hard penalty for domains dispatched in last N sessions.
# Advisory scoring (heat + saturation) was insufficient: visit Gini 0.459→0.827 (S358-S368).
# Score fixes do NOT equal behavior fixes (L-671 core finding). Cooldown forces rotation
# by making recently-visited domains uncompetitive regardless of structural advantage.
# Graduated: gap=1 → full penalty, decays linearly to 0 at gap=COOLDOWN_SESSIONS+1.
COOLDOWN_SESSIONS = 3         # window: domain blocked for 3 sessions after dispatch
COOLDOWN_MAX_PENALTY = 15.0   # strong enough to drop #1 below #2 (meta gap was ~9.4)

# Outcome feedback (F-EXP10, L-501 P1): reward consistently productive domains.
# Closes PHIL-2 self-application gap — expert dispatch learns from its own outcomes.
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
    "FRA": "fractals", "FRACTALS": "fractals", "GT": "game-theory",
    "GTH": "graph-theory", "GAME": "game-theory", "GAMING": "gaming",
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
OUTCOME_MIN_N = 3          # minimum completed lanes before feedback kicks in
OUTCOME_SUCCESS_THRESHOLD = 0.75  # MERGED rate above which domain is PROVEN
OUTCOME_FAILURE_THRESHOLD = 0.50  # MERGED rate below which domain is STRUGGLING
OUTCOME_BONUS = 0.5        # score bonus for PROVEN domains (reduced from 1.5 — L-654 diminishing returns)
OUTCOME_MIXED_BONUS = 2.0  # score bonus for MIXED domains (L-654: highest L/lane yield at 1.42)
OUTCOME_PENALTY = 1.0      # score penalty for STRUGGLING domains


def _compute_gini(values: list[int | float]) -> float:
    """Compute Gini coefficient of a list of non-negative values. 0=equal, 1=max inequality."""
    n = len(values)
    if n == 0 or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    numerator = sum((2 * i - n - 1) * v for i, v in enumerate(sorted_vals, 1))
    return numerator / (n * sum(sorted_vals))


def _get_domain_heat() -> dict[str, int]:
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



def _get_claimed_domains() -> set[str]:
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


def _get_domain_outcomes() -> dict[str, dict]:
    """Parse SWARM-LANES.md for MERGED/ABANDONED counts and lesson yield per domain (F-EXP10).

    Returns {domain_name: {"merged": int, "abandoned": int, "lessons": int}}.
    - merged/abandoned: binary outcome (existing)
    - lessons: L-NNN references in notes column (yield quality signal — L-506)
    Outcome feedback: reward proven domains, flag struggling ones.
    """
    outcomes: dict[str, dict] = {}
    # Read both active lanes and archive for complete outcome history (L-562, F-EXP10)
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
            etc = cols[10] if len(cols) > 10 else ""
            fm = re.search(r"focus=(?:domains/)?([a-z0-9-]+)", etc)
            if fm and fm.group(1) not in ("global", ""):
                domain = fm.group(1)

        if domain:
            if domain not in outcomes:
                outcomes[domain] = {"merged": 0, "abandoned": 0, "lessons": 0}
            outcomes[domain]["merged" if status == "MERGED" else "abandoned"] += 1
            # Lesson yield: count L-NNN references in notes column
            notes = cols[12] if len(cols) > 12 else ""
            lesson_count = len(re.findall(r"\bL-\d{3,4}\b", notes))
            outcomes[domain]["lessons"] += lesson_count
    return outcomes


def score_domain(domain: str) -> dict | None:
    """Compute expected yield score for a domain's open frontiers."""
    frontier_path = DOMAINS_DIR / domain / "tasks" / "FRONTIER.md"
    domain_md_path = DOMAINS_DIR / domain / "DOMAIN.md"
    index_path = DOMAINS_DIR / domain / "INDEX.md"

    if not frontier_path.exists():
        return None

    content = frontier_path.read_text()

    # Active frontier count: only lines under ## Active, not Evidence Archive
    active_section = ""
    active_match = re.search(r"## Active\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if active_match:
        active_section = active_match.group(1)
    active_count = len(re.findall(r"^- \*\*F", active_section, re.MULTILINE))
    if active_count == 0:
        return None  # Skip domains with no open work

    # Resolved count (rows in Resolved table)
    resolved_count = 0
    resolved_match = re.search(r"## Resolved.*", content, re.DOTALL)
    if resolved_match:
        resolved_count = len(re.findall(r"^\| F", resolved_match.group(), re.MULTILINE))

    # Concept counts from DOMAIN.md (multi-concept expertise — S346 human signal)
    iso_count = 0
    lesson_count = 0
    belief_count = 0
    principle_count = 0
    if domain_md_path.exists():
        dm = domain_md_path.read_text()
        iso_count = len(set(re.findall(r"ISO-\d+", dm)))
        lesson_count = len(set(re.findall(r"\bL-\d{3,4}\b", dm)))
        belief_count = len(set(re.findall(r"\bB-?\d+\b", dm)))
        principle_count = len(set(re.findall(r"\bP-\d{3}\b", dm)))

    # Experiment count (JSON artifacts produced)
    exp_dir = EXPERIMENTS_DIR / domain
    exp_count = 0
    if exp_dir.exists():
        exp_count = len(list(exp_dir.glob("*.json")))

    # Has domain INDEX (team has oriented and knows state)
    has_index = index_path.exists()

    # --- Yield score formula ---
    # Multi-concept scoring (S346 human signal: expertise beyond isomorphisms)
    # S347 rebalancing: reduce ISO hegemony, weight principles (was unweighted bug),
    # increase lesson weight, lower belief weight (rare/sparse), boost diversity bonus.
    # iso_count * 1.5      : cross-domain leverage (down from 2.0 — still highest per-item)
    # lesson_count * 0.8   : empirical grounding (up from 0.5 — 32% of concept signal)
    # belief_count * 1.5   : tested claims (down from 2.0 — sparse, shouldn't over-reward)
    # principle_count * 1.5 : distilled knowledge (NEW — was 0, fixing unweighted bug)
    # resolved * 2.0       : domain maturity (team knows how to extract lessons here)
    # active * 1.5         : open work (demand signal)
    # novelty +2.0         : uncharted territory bonus (exp_count == 0)
    # has_index +1.0       : orientation artifact present
    # concept_diversity * 2.5 : breadth reward (up from 2.0 — mastering multiple types)
    novelty_bonus = 2.0 if exp_count == 0 else 0.0
    concept_types = sum([
        iso_count > 0,
        lesson_count > 0,
        belief_count > 0,
        principle_count > 0,
        exp_count > 0,
    ])
    score = (
        iso_count * 1.5
        + lesson_count * 0.8
        + belief_count * 1.5
        + principle_count * 1.5
        + concept_types * 2.5
        + resolved_count * 2.0
        + active_count * 1.5
        + novelty_bonus
        + (1.0 if has_index else 0.0)
    )

    # Extract first open frontier description (dispatch target)
    first_frontier = ""
    match = re.search(r"^- (\*\*F[^*\n]+\*\*.*?)(?=^- \*\*F|\Z)", content, re.MULTILINE | re.DOTALL)
    if match:
        first_frontier = match.group(1).strip()[:120].replace("\n", " ")

    return {
        "domain": domain,
        "score": round(score, 1),
        "active": active_count,
        "resolved": resolved_count,
        "iso": iso_count,
        "lessons": lesson_count,
        "beliefs": belief_count,
        "principles": principle_count,
        "concept_types": concept_types,
        "experiments": exp_count,
        "has_index": has_index,
        "novelty_bonus": novelty_bonus > 0,
        "top_frontier": first_frontier,
    }


def _ucb1_score(results: list[dict], outcome_map: dict, heat_map: dict,
                current_session: int, claimed: set[str],
                c: float = 1.414, cold_floor_pct: float = 0.20) -> list[dict]:
    """Score domains using UCB1 multi-armed bandit formula (F-ECO5, L-697).

    Replaces 10+ heuristic constants (HEAT_DECAY, COOLDOWN_MAX_PENALTY,
    DORMANT_BONUS, VISIT_SATURATION_SCALE, EXPLORATION_GINI_THRESHOLD, etc.)
    with a single parameter c (exploration weight).

    Formula: score = avg_yield + c * sqrt(log(total_dispatches) / domain_dispatches)
    For unvisited domains: score = infinity (always explore first).

    Args:
        c: Exploration parameter. sqrt(2)=1.414 is theoretically optimal (Auer et al. 2002).
        cold_floor_pct: Hard floor — at least this fraction of recommendations go to
            domains with <3 visits (DARPA 20% model).
    """
    # Compute total dispatches across all domains
    total_dispatches = sum(
        oc["merged"] + oc["abandoned"]
        for oc in outcome_map.values()
    )
    if total_dispatches == 0:
        total_dispatches = 1  # avoid log(0)

    # Global average yield (prior for unvisited domains)
    total_lessons = sum(oc.get("lessons", 0) for oc in outcome_map.values())
    global_avg = total_lessons / total_dispatches if total_dispatches > 0 else 1.0

    for r in results:
        dom = r["domain"]
        oc = outcome_map.get(dom, {"merged": 0, "abandoned": 0, "lessons": 0})
        n = oc["merged"] + oc["abandoned"]
        lessons = oc.get("lessons", 0)

        last_active = heat_map.get(dom, 0)
        gap = current_session - last_active if last_active > 0 else 999

        # Classify heat (for display only — UCB1 handles exploration natively)
        if gap <= 3:
            r["heat"] = "HOT"
        elif gap > 5:
            r["heat"] = "NEW" if last_active == 0 else "COLD"
        else:
            r["heat"] = "WARM"

        if n == 0:
            # Unvisited: infinite UCB1 score. Use structural score as tiebreaker.
            r["ucb1_exploit"] = global_avg
            r["ucb1_explore"] = float('inf')
            r["score"] = 1000.0 + r["score"]  # structural base as tiebreaker
        else:
            avg_yield = lessons / n
            explore_term = c * math.sqrt(math.log(total_dispatches) / n)
            r["ucb1_exploit"] = round(avg_yield, 3)
            r["ucb1_explore"] = round(explore_term, 3)
            r["score"] = avg_yield + explore_term

        # Keep: claimed domain penalty (multi-agent coordination)
        if dom in claimed:
            r["claimed"] = True
            r["score"] -= 10.0
        else:
            r["claimed"] = False

        # Keep: self-dispatch norm (philosophical, not economic)
        if dom == "expert-swarm" and gap > SELF_DISPATCH_INTERVAL:
            r["self_dispatch_due"] = True
            r["score"] += 2.0
        else:
            r["self_dispatch_due"] = False

        # Outcome label (display only)
        if n >= OUTCOME_MIN_N:
            rate = oc["merged"] / n
            r["outcome_rate"] = round(rate, 2)
            if rate >= OUTCOME_SUCCESS_THRESHOLD:
                r["outcome_label"] = "PROVEN"
            elif rate < OUTCOME_FAILURE_THRESHOLD:
                r["outcome_label"] = "STRUGGLING"
            else:
                r["outcome_label"] = "MIXED"
        else:
            r["outcome_rate"] = None
            r["outcome_label"] = "NEW"

        r["outcome_merged"] = oc["merged"]
        r["outcome_abandoned"] = oc["abandoned"]
        r["outcome_lessons"] = oc.get("lessons", 0)
        r["outcome_n"] = n
        r["cooldown"] = False
        r["cooldown_penalty"] = 0.0
        r["saturation_penalty"] = 0.0
        r["exploration_boost"] = 0.0

    # 20% exploration floor (DARPA model, L-697): ensure underexplored domains
    # appear in recommendations regardless of UCB1 score. Domains with <3 visits
    # are floor-eligible; at least cold_floor_pct of results get floor protection.
    floor_min_n = 3
    floor_eligible = [r for r in results if r.get("outcome_n", 0) < floor_min_n]
    floor_target = max(1, int(len(results) * cold_floor_pct))
    # Sort floor-eligible by visit count (ascending), then structural score (descending)
    floor_eligible.sort(key=lambda x: (x.get("outcome_n", 0), -x.get("score", 0)))
    floor_domains = {r["domain"] for r in floor_eligible[:floor_target]}
    for r in results:
        r["floor_protected"] = r["domain"] in floor_domains

    return results


def run(args: argparse.Namespace) -> None:
    if not DOMAINS_DIR.exists():
        print("ERROR: domains/ directory not found. Run from repo root.", file=sys.stderr)
        sys.exit(1)

    results = []
    target_domains = [args.domain] if args.domain else sorted(os.listdir(DOMAINS_DIR))

    for domain in target_domains:
        r = score_domain(domain)
        if r:
            results.append(r)

    # Shared data for both modes
    current_session = _session_number()
    heat_map = _get_domain_heat()
    claimed = _get_claimed_domains()
    outcome_map = _get_domain_outcomes()

    mode = getattr(args, 'mode', 'heuristic')
    compare = getattr(args, 'compare', False)

    if mode == "ucb1" or compare:
        import copy
        ucb1_results = copy.deepcopy(results) if compare else results
        _ucb1_score(ucb1_results, outcome_map, heat_map, current_session, claimed)
        ucb1_results.sort(key=lambda x: x["score"], reverse=True)

        if compare:
            # Run heuristic on original results, then print comparison
            heuristic_results = results
        elif not compare:
            # Pure UCB1 mode
            results = ucb1_results
            results_limited = results if args.all or args.domain else results[:10]
            if args.json:
                print(json.dumps(results_limited, indent=2, default=str))
                return
            print("\n=== DISPATCH OPTIMIZER — UCB1 MODE (F-ECO5, L-697) ===")
            print(f"Single parameter c=1.414 replaces 10+ heuristic constants\n")
            print(f"{'Score':>6}  {'Domain':<25}  {'Exploit':>7}  {'Explore':>7}  {'N':>3}  {'L':>3}  {'Heat':>4}")
            print("-" * 75)
            for r in results_limited:
                heat_icon = {"HOT": "🔥", "WARM": "~", "COLD": "❄", "NEW": "✨"}.get(r.get("heat", ""), " ")
                exploit = r.get("ucb1_exploit", 0)
                explore = r.get("ucb1_explore", 0)
                explore_str = "∞" if explore == float('inf') else f"{explore:.3f}"
                label = r.get("outcome_label", "NEW")
                n = r.get("outcome_n", 0)
                score_str = f"{r['score']:.1f}" if r["score"] < 999 else "∞"
                floor_mark = " [FLOOR]" if r.get("floor_protected") else ""
                print(
                    f"{score_str:>6}  {r['domain']:<25}  {exploit:7.3f}  {explore_str:>7}  "
                    f"{n:3d}  {r.get('outcome_lessons', 0):3d}  {heat_icon:>4}"
                    f" [{label}]{floor_mark}"
                )
                if r.get("top_frontier"):
                    print(f"         → {r['top_frontier'][:72]}")
            # Coverage
            all_visits = [r.get("outcome_n", 0) for r in results]
            gini = _compute_gini(all_visits)
            visited = sum(1 for v in all_visits if v > 0)
            floor_count = sum(1 for r in results if r.get("floor_protected"))
            floor_doms = [r["domain"] for r in results if r.get("floor_protected")]
            print(f"\n--- UCB1 Coverage ---")
            print(f"  Visit Gini: {gini:.3f}")
            print(f"  Coverage: {visited}/{len(all_visits)} domains visited")
            print(f"  Floor (20%): {floor_count} domains protected ({', '.join(floor_doms[:5])})")
            print(f"  Formula: avg_yield + {1.414:.3f} * sqrt(log(total_dispatches) / domain_dispatches)")
            print(f"  Unvisited domains ranked first (UCB1 = ∞), then by structural tiebreaker")
            return

    # Heuristic mode (default) — apply domain heat
    sparse_domains = []
    saturated_domains = []

    for r in results:
        dom = r["domain"]
        last_active = heat_map.get(dom, 0)
        gap = current_session - last_active if last_active > 0 else 999

        # Heat penalty for recently active domains
        if gap <= 3:
            penalty = HEAT_PENALTY_MAX * (HEAT_DECAY ** gap)
            r["score"] -= penalty
            r["heat"] = "HOT"
            saturated_domains.append(dom)
        elif gap > 5:
            if last_active == 0:
                # Never visited: highest priority — 90% first-visit merge rate (L-548)
                r["score"] += FIRST_VISIT_BONUS
                r["heat"] = "NEW"
            else:
                r["score"] += DORMANT_BONUS
                r["heat"] = "COLD"
            sparse_domains.append(dom)
        else:
            r["heat"] = "WARM"

        # Cooldown window (F-ECO5, L-671): graduated penalty for recently-visited domains.
        # Stacks with heat penalty. Heat = mild anti-clustering (max -6.0).
        # Cooldown = hard rotation enforcement (max -15.0). Combined: -21.0 at gap=1.
        if 0 < gap <= COOLDOWN_SESSIONS:
            cooldown = COOLDOWN_MAX_PENALTY * (1.0 - (gap - 1) / COOLDOWN_SESSIONS)
            r["score"] -= cooldown
            r["cooldown"] = True
            r["cooldown_penalty"] = round(cooldown, 1)
        else:
            r["cooldown"] = False
            r["cooldown_penalty"] = 0.0

        # Self-dispatch norm (L-501 P6, PHIL-2): expert-swarm must dispatch to itself
        # every SELF_DISPATCH_INTERVAL sessions. The dispatcher dispatching to itself
        # closes the self-application gap identified by 5-domain council (S343).
        if dom == "expert-swarm" and gap > SELF_DISPATCH_INTERVAL:
            self_bonus = DORMANT_BONUS * 2.0  # double dormant bonus for self-application
            r["score"] += self_bonus
            r["self_dispatch_due"] = True
        else:
            r["self_dispatch_due"] = False

        # Mark if currently claimed by another agent
        if dom in claimed:
            r["claimed"] = True
            r["score"] -= 10.0  # strong penalty — agent already there
        else:
            r["claimed"] = False

        # Outcome feedback (F-EXP10): adjust score based on historical lane success
        oc = outcome_map.get(dom, {"merged": 0, "abandoned": 0, "lessons": 0})
        n = oc["merged"] + oc["abandoned"]
        r["outcome_merged"] = oc["merged"]
        r["outcome_abandoned"] = oc["abandoned"]
        r["outcome_lessons"] = oc.get("lessons", 0)
        r["outcome_n"] = n
        if n >= OUTCOME_MIN_N:
            rate = oc["merged"] / n
            r["outcome_rate"] = round(rate, 2)
            if rate >= OUTCOME_SUCCESS_THRESHOLD:
                r["score"] += OUTCOME_BONUS
                r["outcome_label"] = "PROVEN"
            elif rate < OUTCOME_FAILURE_THRESHOLD:
                r["score"] -= OUTCOME_PENALTY
                r["outcome_label"] = "STRUGGLING"
            else:
                r["score"] += OUTCOME_MIXED_BONUS
                r["outcome_label"] = "MIXED"
        else:
            r["outcome_rate"] = None
            r["outcome_label"] = "NEW"

        # Visit saturation penalty (F-ECO5, L-571): diminishing returns for repeated visits.
        # log(1+n) grows slowly: n=4→2.4, n=12→3.9, n=24→4.8, n=33→5.3
        if n > 0:
            sat_penalty = VISIT_SATURATION_SCALE * math.log(1 + n)
            r["score"] -= sat_penalty
            r["saturation_penalty"] = round(sat_penalty, 1)
        else:
            r["saturation_penalty"] = 0.0

    # Exploration mode (F-ECO5): when visit concentration exceeds threshold,
    # boost undervisited domains to counteract exploitation amplification.
    all_visit_counts = [r.get("outcome_n", 0) for r in results]
    visit_gini = _compute_gini(all_visit_counts)
    exploration_mode = visit_gini > EXPLORATION_GINI_THRESHOLD

    if exploration_mode:
        for r in results:
            heat = r.get("heat", "")
            if heat == "NEW":
                r["score"] += EXPLORATION_NEW_BOOST
                r["exploration_boost"] = EXPLORATION_NEW_BOOST
            elif heat in ("COLD", "❄"):
                r["score"] += EXPLORATION_COLD_BOOST
                r["exploration_boost"] = EXPLORATION_COLD_BOOST
            else:
                r["exploration_boost"] = 0.0
    else:
        for r in results:
            r["exploration_boost"] = 0.0

    results.sort(key=lambda x: x["score"], reverse=True)

    if not args.all and not args.domain:
        results = results[:10]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    # Human-readable output
    print("\n=== DISPATCH OPTIMIZER (F-ECO4) ===")
    print(f"Expert economy: rank open frontiers by expected yield\n")

    # Domain gradient (S340 council: 4/5 convergence on visibility)
    if sparse_domains or saturated_domains:
        if sparse_domains:
            new_doms = [r["domain"] for r in results if r.get("heat") == "NEW"]
            cold_doms = [r["domain"] for r in results if r.get("heat") == "COLD"]
            if new_doms:
                print(f"  NEW/UNVISITED (bonus +{FIRST_VISIT_BONUS}): {', '.join(new_doms[:6])}")
            if cold_doms:
                print(f"  DORMANT (bonus +{DORMANT_BONUS}): {', '.join(cold_doms[:6])}")
        if saturated_domains:
            print(f"  SATURATED (penalty): {', '.join(saturated_domains[:6])}")
        if claimed:
            print(f"  CLAIMED (by active agent): {', '.join(claimed)}")
        print()

    print(f"{'Score':>6}  {'Domain':<25}  {'Act':>3}  {'Res':>3}  {'ISO':>3}  {'L':>3}  {'B':>2}  {'P':>3}  {'CT':>2}  {'Heat':>4}")
    print("-" * 85)

    for r in results:
        heat_icon = {"HOT": "🔥", "WARM": "~", "COLD": "❄", "NEW": "✨"}.get(r.get("heat", ""), " ")
        cooldown_mark = f" [CD-{r.get('cooldown_penalty', 0)}]" if r.get("cooldown") else ""
        claimed_mark = " [CLAIMED]" if r.get("claimed") else (" [SELF-DUE]" if r.get("self_dispatch_due") else cooldown_mark)
        label = r.get("outcome_label", "NEW")
        n = r.get("outcome_n", 0)
        lessons_str = f" {r.get('outcome_lessons', 0)}L" if r.get("outcome_lessons", 0) > 0 else ""
        outcome_tag = f" [{label} {r['outcome_merged']}/{n}{lessons_str}]" if n >= OUTCOME_MIN_N else ""
        print(
            f"{r['score']:6.1f}  {r['domain']:<25}  {r['active']:3d}  {r['resolved']:3d}  "
            f"{r['iso']:3d}  {r['lessons']:3d}  {r['beliefs']:2d}  {r['principles']:3d}  "
            f"{r['concept_types']:2d}  {heat_icon:>4}{claimed_mark}{outcome_tag}"
        )
        if r["top_frontier"]:
            print(f"         → {r['top_frontier'][:72]}")

    # Coverage metrics (F-ECO5)
    all_visits = [r.get("outcome_n", 0) for r in results]
    gini = _compute_gini(all_visits)
    visited_count = sum(1 for v in all_visits if v > 0)
    total_count = len(all_visits)
    coverage_pct = (visited_count / total_count * 100) if total_count > 0 else 0
    exploration_on = gini > EXPLORATION_GINI_THRESHOLD

    print(f"\n--- Coverage (F-ECO5, L-571) ---")
    print(f"  Visit Gini: {gini:.3f} {'← EXPLORATION MODE ON' if exploration_on else ''}")
    print(f"  Coverage: {coverage_pct:.0f}% ({visited_count}/{total_count} domains visited)")
    print(f"  Saturation: visit penalty = {VISIT_SATURATION_SCALE} × ln(1+visits)")
    if exploration_on:
        print(f"  Exploration boost: +{EXPLORATION_NEW_BOOST} unvisited, +{EXPLORATION_COLD_BOOST} dormant")

    print(f"\n--- Scoring formula (multi-concept, S347 + coverage S358 + cooldown S370) ---")
    print("  Columns: Act=active frontiers, Res=resolved, ISO=isomorphisms, L=lessons, B=beliefs, P=principles, CT=concept types")
    print("  score = iso*1.5 + lessons*0.8 + beliefs*1.5 + principles*1.5 + concept_types*2.5 + resolved*2 + active*1.5 + novelty(2) + index(1)")
    print(f"  + dormant_bonus(+{DORMANT_BONUS} if >5 sessions cold, +{FIRST_VISIT_BONUS} if never visited) - heat_penalty(up to -{HEAT_PENALTY_MAX} if <3 sessions)")
    print(f"  - cooldown(max -{COOLDOWN_MAX_PENALTY}, linear decay over {COOLDOWN_SESSIONS} sessions) [L-671: hard rotation]")
    print(f"  - visit_saturation({VISIT_SATURATION_SCALE} × ln(1+n)) + exploration_boost(Gini>{EXPLORATION_GINI_THRESHOLD})")
    print(f"  + outcome_bonus(+{OUTCOME_BONUS} PROVEN, +{OUTCOME_MIXED_BONUS} MIXED: ≥{OUTCOME_MIN_N} lanes)")
    print(f"  - outcome_penalty(-{OUTCOME_PENALTY} STRUGGLING: ≥{OUTCOME_MIN_N} lanes, rate<{OUTCOME_FAILURE_THRESHOLD})")
    print(f"  Heat map: {len(saturated_domains)} HOT, {len(sparse_domains)} COLD, {len(claimed)} claimed")
    print(f"\n  Showing {'all' if args.all else 'top 10'} of {len(results)} domains with open work.")

    # Compare mode: show UCB1 side-by-side
    if compare:
        print(f"\n\n=== UCB1 COMPARISON (F-ECO5, L-697) ===")
        ucb1_top = ucb1_results[:10]
        heur_top = results[:10]
        heur_order = [r["domain"] for r in heur_top]
        ucb1_order = [r["domain"] for r in ucb1_top]
        print(f"\n  Top-10 ranking comparison:")
        print(f"  {'Rank':>4}  {'Heuristic':<25}  {'UCB1':<25}  {'Match'}")
        print(f"  " + "-" * 75)
        for i in range(10):
            h = heur_order[i] if i < len(heur_order) else "-"
            u = ucb1_order[i] if i < len(ucb1_order) else "-"
            match = "=" if h == u else "≠"
            print(f"  {i+1:>4}  {h:<25}  {u:<25}  {match}")
        overlap = set(heur_order) & set(ucb1_order)
        print(f"\n  Top-10 overlap: {len(overlap)}/10 domains in common")

        # Score Gini comparison
        heur_scores = [r["score"] for r in heuristic_results]
        ucb1_scores = [r["score"] for r in ucb1_results if r["score"] < 999]
        heur_gini = _compute_gini([max(0, s) for s in heur_scores])
        ucb1_gini = _compute_gini([max(0, s) for s in ucb1_scores])
        print(f"\n  Score Gini (lower = more uniform):")
        print(f"    Heuristic: {heur_gini:.3f}")
        print(f"    UCB1:      {ucb1_gini:.3f}")
        pct_change = ((ucb1_gini - heur_gini) / heur_gini * 100) if heur_gini > 0 else 0
        print(f"    Change:    {pct_change:+.1f}%")

        # Score spread comparison
        heur_spread = max(heur_scores) - min(heur_scores) if heur_scores else 0
        ucb1_spread = max(ucb1_scores) - min(ucb1_scores) if ucb1_scores else 0
        print(f"\n  Score spread (max-min):")
        print(f"    Heuristic: {heur_spread:.1f}")
        print(f"    UCB1:      {ucb1_spread:.1f}")

        # Constants comparison
        print(f"\n  Constants: heuristic uses 12+, UCB1 uses 1 (c=1.414)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch Optimizer — rank domain experiments by expected yield")
    parser.add_argument("--all", action="store_true", help="Show all domains, not just top 10")
    parser.add_argument("--domain", metavar="NAME", help="Score a single domain")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--mode", choices=["heuristic", "ucb1"], default="ucb1",
                       help="Scoring mode: ucb1 (single parameter, default) or heuristic (12+ constants, legacy)")
    parser.add_argument("--compare", action="store_true",
                       help="Run both modes and show comparison")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
