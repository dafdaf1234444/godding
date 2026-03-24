#!/usr/bin/env python3
"""Scoring functions extracted from dispatch_optimizer.py (DOMEX-META-S427).

Contains: score_domain, ucb1_score.
"""

import glob
import json
import math
import os
import re
from pathlib import Path

try:
    from dispatch_campaigns import WAVE_DANGER_BOOST, WAVE_COMMITTED_BOOST
except ImportError:
    WAVE_DANGER_BOOST = 1.5
    WAVE_COMMITTED_BOOST = 0.5

DOMAINS_DIR = Path("domains")
EXPERIMENTS_DIR = Path("experiments")


def _load_knowledge_gaps():
    """Load domain knowledge gaps from latest knowledge-swarm artifact (S457)."""
    pattern = str(EXPERIMENTS_DIR / "meta" / "knowledge-swarm-s*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return {}
    try:
        with open(files[-1]) as f:
            data = json.load(f)
        return data.get("domain_gaps", {})
    except Exception:
        return {}


_knowledge_gaps = _load_knowledge_gaps()


def _load_maintenance_urgency():
    """Load maintenance urgency from workspace/maintenance-actions.json (F-SWARMER1 #3).

    Returns dict with 'urgent_count', 'due_count', 'total' for UCB1 score modification.
    Converts L-1146 passive display bridge into active dispatch pressure.
    """
    maint_path = Path("workspace") / "maintenance-actions.json"
    if not maint_path.exists():
        return {"urgent_count": 0, "due_count": 0, "total": 0}
    try:
        with open(maint_path) as f:
            data = json.load(f)
        items = data.get("items", [])
        urgent = sum(1 for i in items if i.get("priority") == "URGENT")
        due = sum(1 for i in items if i.get("priority") == "DUE")
        return {"urgent_count": urgent, "due_count": due, "total": len(items)}
    except Exception:
        return {"urgent_count": 0, "due_count": 0, "total": 0}


_maintenance_urgency = _load_maintenance_urgency()


def _load_integration_backlog():
    """Load the latest integration-backlog analysis for proactive meta dispatch pressure.

    L-1588: coarse DUE counts miss the actual integration backlog. The unreferenced-tools
    analysis already measures actionable wiring/archival debt, so dispatch can use it
    directly instead of waiting for threshold-triggered maintenance notices alone.
    """
    pattern = str(Path("workspace") / "unreferenced-tools-analysis-s*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return {"session": -1, "true_unreferenced": 0, "wire_count": 0, "archive_count": 0}
    try:
        with open(files[-1]) as f:
            data = json.load(f)
        session_value = data.get("session", -1)
        if isinstance(session_value, str) and session_value.upper().startswith("S"):
            session = int(re.sub(r"[^0-9]", "", session_value) or "-1")
        elif isinstance(session_value, int):
            session = session_value
        else:
            session = -1
        summary = data.get("summary", {})
        return {
            "session": session,
            "true_unreferenced": int(summary.get("true_unreferenced", 0) or 0),
            "wire_count": int(summary.get("wire_count", 0) or 0),
            "archive_count": int(summary.get("archive_count", 0) or 0),
        }
    except Exception:
        return {"session": -1, "true_unreferenced": 0, "wire_count": 0, "archive_count": 0}


_integration_backlog = _load_integration_backlog()


def _load_soul_weights():
    """Load per-domain human benefit scores from human_impact.py (F-SOUL1 Phase 2).

    Returns dict: domain -> {"good": N, "bad": N, "ratio": float}.
    Domains with higher ratio produce more human-good knowledge and get
    a dispatch boost. Converts soul extraction into structural selection pressure.
    """
    try:
        import sys, os
        tools_dir = os.path.dirname(os.path.abspath(__file__))
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        from human_impact import scan_lessons, extract_soul
        results = scan_lessons()
        soul = extract_soul(results)
        return soul.get("domain_benefit_scores", {})
    except Exception:
        return {}


_soul_weights = _load_soul_weights()

# Soul dispatch constants (F-SOUL1 Phase 2, SIG-81, L-1455, L-1485)
SOUL_MULTIPLIER_MAX = 1.6       # cap positive soul weighting at +60%
SOUL_MULTIPLIER_MIN = 0.6       # cap negative soul weighting at -40%
SOUL_MIN_SAMPLE = 5             # minimum good+bad lessons for scoring
SOUL_SCALE = 0.15               # multiplier delta per unit deviation from mean ratio

# Compute corpus-wide mean benefit ratio as reference point (L-1455)
# Domains below mean displace human benefit; domains above generate it.
def _compute_soul_mean():
    weighted = [(v.get("ratio", 1.0), v.get("good", 0) + v.get("bad", 0))
                for v in _soul_weights.values()
                if v.get("good", 0) + v.get("bad", 0) >= SOUL_MIN_SAMPLE]
    if not weighted:
        return 1.0
    total_n = sum(n for _, n in weighted)
    return sum(r * n for r, n in weighted) / total_n if total_n > 0 else 1.0

_soul_mean_ratio = _compute_soul_mean()


# Maintenance urgency constants (F-SWARMER1 intervention #3)
MAINT_DUE_BOOST_PER_ITEM = 0.5      # meta domain boost per DUE item
MAINT_URGENT_BOOST_PER_ITEM = 1.0   # meta domain boost per URGENT item
MAINT_BOOST_CAP = 2.0               # maximum maintenance boost

# Integration backlog constants (L-1588)
INTEGRATION_TRUE_UNREF_THRESHOLD = 32
INTEGRATION_TRUE_UNREF_WEIGHT = 0.01
INTEGRATION_WIRE_WEIGHT = 0.04
INTEGRATION_ARCHIVE_WEIGHT = 0.02
INTEGRATION_BOOST_CAP = 1.5
INTEGRATION_STALE_AFTER = 10

# Concentration penalty constants (F-COL1, L-1587 — anti-mediocrity selection)
# When a domain captures too much dispatch share with below-median quality,
# apply a penalty. Prevents the degenerative spiral where the most accessible
# domain crowds out specialists. Structural enforcement per L-601.
CONCENTRATION_SHARE_THRESHOLD = 0.10   # domain must hold >10% of total lanes
CONCENTRATION_PENALTY_SCALE = 2.0      # penalty per 1% above threshold
CONCENTRATION_PENALTY_CAP = 3.0        # max penalty


# Heuristic mode constants (shared with dispatch_optimizer.py display)
HEAT_DECAY = 0.85
HEAT_PENALTY_MAX = 6.0
DORMANT_BONUS = 3.0
FIRST_VISIT_BONUS = 5.0
SELF_DISPATCH_INTERVAL = 10
VISIT_SATURATION_SCALE = 1.5
EXPLORATION_GINI_THRESHOLD = 0.45
EXPLORATION_NEW_BOOST = 8.0
EXPLORATION_COLD_BOOST = 4.0
COOLDOWN_SESSIONS = 3
COOLDOWN_MAX_PENALTY = 15.0
OUTCOME_MIN_N = 5
OUTCOME_SUCCESS_THRESHOLD = 0.75
OUTCOME_FAILURE_THRESHOLD = 0.50
OUTCOME_BONUS = 0.5
OUTCOME_MIXED_BONUS = 2.0
OUTCOME_PENALTY = 1.0

# Adjacency bonus constants (F-CITY1, L-1510 — neighborhood spillover)
ADJ_BONUS_PER_NEIGHBOR = 0.2     # additive bonus per high-scoring adjacent domain
ADJ_BONUS_CAP = 0.6              # max adjacency bonus (3 neighbors)
ADJ_TOP_N = 10                   # consider top-N domains as "high-scoring"

# Lotka-Volterra allelopathy constants (L-1606, F-PLB5)
ALLELO_BOOST_SCALE = 0.3         # neighbor boost per unit allelopathy coefficient
ALLELO_BOOST_CAP = 0.5           # max allelopathy correction bonus


def _load_allelopathy_coefficients():
    """Load domain allelopathy coefficients from F-PLB5 experiment (L-1606)."""
    pattern = str(EXPERIMENTS_DIR / "plant-biology" / "f-plb5-allelopathy-dispatch-s*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return {}
    try:
        with open(files[-1]) as f:
            data = json.load(f)
        coeffs = {}
        for domain, coeff in data.get("top_allelopaths", []):
            coeffs[domain] = coeff
        for domain, coeff in data.get("top_facilitators", []):
            coeffs[domain] = coeff
        return coeffs
    except Exception:
        return {}


_allelopathy_coefficients = _load_allelopathy_coefficients()


def _load_adjacency_graph():
    """Load domain adjacency graph from DOMAIN.md Adjacent: headers (city_plan.py)."""
    graph: dict[str, list[str]] = {}
    if not DOMAINS_DIR.exists():
        return graph
    for entry in sorted(DOMAINS_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        domain_md = entry / "DOMAIN.md"
        if not domain_md.exists():
            continue
        try:
            text = domain_md.read_text(errors="replace")
        except Exception:
            continue
        m = re.search(r"^Adjacent(?:\s+Domains)?:\s*(.+)$", text,
                      re.MULTILINE | re.IGNORECASE)
        if m:
            graph[entry.name] = [d.strip().lower() for d in m.group(1).split(",")
                                 if d.strip()]
        else:
            graph[entry.name] = []
    return graph


_adjacency_graph = _load_adjacency_graph()


def score_domain(domain: str, calibration: dict | None = None) -> dict | None:
    """Compute expected yield score for a domain's open frontiers."""
    frontier_path = DOMAINS_DIR / domain / "tasks" / "FRONTIER.md"
    domain_md_path = DOMAINS_DIR / domain / "DOMAIN.md"
    index_path = DOMAINS_DIR / domain / "INDEX.md"

    if not frontier_path.exists():
        return None

    content = frontier_path.read_text()

    # Active frontier count: only lines under ## Active (or ## Open), not Evidence Archive
    # Use [^\S\n]* (not \s*) to prevent consuming blank lines that precede ## Resolved
    active_section = ""
    active_match = re.search(r"## (?:Active|Open)[^\S\n]*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if active_match:
        active_section = active_match.group(1)
    active_count = len(re.findall(r"(?:^- \*\*F|^### F)", active_section, re.MULTILINE))
    if active_count == 0:
        return None

    # Resolved count
    resolved_count = 0
    resolved_match = re.search(r"## Resolved.*", content, re.DOTALL)
    if resolved_match:
        resolved_count = len(re.findall(r"^\| F", resolved_match.group(), re.MULTILINE))

    # Concept counts from DOMAIN.md
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

    # Experiment count
    exp_dir = EXPERIMENTS_DIR / domain
    exp_count = 0
    if exp_dir.exists():
        exp_count = len(list(exp_dir.glob("*.json")))

    has_index = index_path.exists()

    # Yield score formula — calibration or legacy weights
    cal = calibration
    if cal and cal.get("weights"):
        w = cal["weights"]
    else:
        w = {"iso": 1.5, "lessons": 0.8, "beliefs": 1.5, "principles": 1.5,
             "concept_types": 2.5, "resolved": 2.0, "active": 1.5,
             "novelty": 2.0, "has_index": 1.0}

    novelty_bonus = w.get("novelty", 2.0) if exp_count == 0 else 0.0
    concept_types = sum([
        iso_count > 0, lesson_count > 0, belief_count > 0,
        principle_count > 0, exp_count > 0,
    ])
    score = (
        iso_count * w.get("iso", 1.5)
        + lesson_count * w.get("lessons", 0.8)
        + belief_count * w.get("beliefs", 1.5)
        + principle_count * w.get("principles", 1.5)
        + concept_types * w.get("concept_types", 2.5)
        + resolved_count * w.get("resolved", 2.0)
        + active_count * w.get("active", 1.5)
        + novelty_bonus
        + (w.get("has_index", 1.0) if has_index else 0.0)
    )

    # First open frontier description — restrict to active_section (#L-1103, FM-31)
    first_frontier = ""
    match = re.search(r"^- (\*\*F[^*\n]+\*\*.*?)(?=^- \*\*F|\Z)", active_section, re.MULTILINE | re.DOTALL)
    if match:
        first_frontier = match.group(1).strip()[:120].replace("\n", " ")

    # Execution-blocked detection (L-862)
    hardened_count = len(re.findall(r"HARDENED", active_section))
    execution_blocked = hardened_count >= active_count and active_count >= 2

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
        "execution_blocked": execution_blocked,
        "hardened_count": hardened_count,
    }


def _infer_reward_intent(r: dict, phase: str) -> str:
    """Infer what behavior a dispatch should reinforce (L-1127, F-SWARMER1).

    Makes implicit reward channels explicit so sessions can declare and audit
    whether their work matched the intended behavioral reinforcement.
    """
    if r.get("self_dispatch_due"):
        return "self-improve"
    if phase == "danger":
        return "commit"
    if r.get("outcome_label") == "STRUGGLING":
        return "pivot"
    if r.get("outcome_label") == "NEW" or r.get("floor_protected"):
        return "explore"
    if r.get("heat") == "COLD" and r.get("outcome_label") == "PROVEN":
        return "reconnect"
    if r.get("outcome_label") == "PROVEN":
        return "deepen"
    return "resolve"


def ucb1_score(results: list[dict], outcome_map: dict, heat_map: dict,
               current_session: int, claimed: set[str],
               campaign_waves: dict[str, dict] | None = None,
               campaign_phase_fn=None,
               c: float = 1.414, cold_floor_pct: float = 0.20) -> list[dict]:
    """Score domains using UCB1 multi-armed bandit formula (F-ECO5, L-543, L-697).

    Replaces 10+ heuristic constants with a single parameter c (exploration weight).
    Formula: score = avg_yield + c * sqrt(log(total_dispatches) / domain_dispatches)
    """
    total_dispatches = sum(
        oc["merged"] + oc["abandoned"] for oc in outcome_map.values()
    )
    if total_dispatches == 0:
        total_dispatches = 1

    # Compute global mean Sharpe dynamically (L-1622: hardcoded 7.7 below actual mean)
    _sharpe_total = sum(oc.get("sharpe_sum", 0) for oc in outcome_map.values())
    _sharpe_n = sum(oc.get("sharpe_count", 0) for oc in outcome_map.values())
    global_mean_sharpe = _sharpe_total / _sharpe_n if _sharpe_n > 0 else 8.0

    # Global average quality (prior for unvisited domains) — Sharpe-weighted (L-1127)
    quality_scores = []
    for oc in outcome_map.values():
        n_oc = oc["merged"] + oc["abandoned"]
        if n_oc > 0:
            mr = oc["merged"] / n_oc
            s_sum = oc.get("sharpe_sum", 0)
            s_cnt = oc.get("sharpe_count", 0)
            sf = (s_sum / s_cnt / global_mean_sharpe) if s_cnt > 0 else 1.0
            quality_scores.append(mr * (1 + math.log1p(oc.get("lessons", 0))) * sf)
    global_avg = sum(quality_scores) / len(quality_scores) if quality_scores else 1.0

    for r in results:
        dom = r["domain"]
        oc = outcome_map.get(dom, {"merged": 0, "abandoned": 0, "lessons": 0})
        n = oc["merged"] + oc["abandoned"]
        lessons = oc.get("lessons", 0)

        last_active = heat_map.get(dom, 0)
        gap = current_session - last_active if last_active > 0 else 999

        # Heat classification (display only)
        if gap <= 3:
            r["heat"] = "HOT"
        elif gap > 5:
            r["heat"] = "NEW" if last_active == 0 else "COLD"
        else:
            r["heat"] = "WARM"

        if n == 0:
            r["ucb1_exploit"] = global_avg
            r["ucb1_explore"] = float('inf')
            r["score"] = 1000.0 + r["score"]
        else:
            merge_rate = oc["merged"] / n
            lessons_l3plus = oc.get("lessons_l3plus", 0)
            lessons_weighted = lessons + lessons_l3plus
            # Sharpe-weighted quality (L-1127 Channel 3 fix, L-1141): domains producing
            # high-Sharpe lessons get a quality multiplier. Normalised against
            # dynamic global mean Sharpe (L-1622: was hardcoded 7.7, actual ~8.1).
            sharpe_sum = oc.get("sharpe_sum", 0)
            sharpe_count = oc.get("sharpe_count", 0)
            avg_sharpe = sharpe_sum / sharpe_count if sharpe_count > 0 else global_mean_sharpe
            sharpe_factor = avg_sharpe / global_mean_sharpe  # >1.0 for high-quality domains
            quality = merge_rate * (1 + math.log1p(lessons_weighted)) * sharpe_factor
            explore_term = c * math.sqrt(math.log(total_dispatches) / n)
            r["ucb1_exploit"] = round(quality, 3)
            r["ucb1_explore"] = round(explore_term, 3)
            r["score"] = quality + explore_term

        # Knowledge-gap exploration bonus (knowledge_swarm.py, S457)
        k_gap = _knowledge_gaps.get(dom, {})
        k_rate = k_gap.get("blind_spot_rate", 0) + k_gap.get("decayed_rate", 0) * 0.5
        k_bonus = min(k_rate * 0.5, 0.3)
        r["score"] += k_bonus
        r["knowledge_gap_bonus"] = round(k_bonus, 3)

        # Maintenance-urgency modifier (F-SWARMER1 #3, L-1146 → active weighting)
        # Boosts meta domain when DUE/URGENT items exist, converting passive
        # maintenance display into structural dispatch pressure.
        mu = _maintenance_urgency
        maint_boost = 0.0
        if dom == "meta" and mu["total"] > 0:
            maint_boost = (mu["due_count"] * MAINT_DUE_BOOST_PER_ITEM
                           + mu["urgent_count"] * MAINT_URGENT_BOOST_PER_ITEM)
            maint_boost = min(maint_boost, MAINT_BOOST_CAP)
        r["score"] += maint_boost
        r["maintenance_boost"] = round(maint_boost, 3)

        # Integration backlog modifier (L-1588)
        # Maintenance DUE counts are reactive and coarse. When the meta-tooler analysis
        # reports a large fresh backlog, add proactive pressure so dispatch sees the real
        # integration debt before it degrades into repeated maintenance alarms.
        integration_boost = 0.0
        ib = _integration_backlog
        if dom == "meta" and ib.get("session", -1) >= 0:
            age = max(current_session - ib["session"], 0)
            if age < INTEGRATION_STALE_AFTER:
                freshness = 1.0 - (age / INTEGRATION_STALE_AFTER)
                true_unreferenced = max(
                    0, ib.get("true_unreferenced", 0) - INTEGRATION_TRUE_UNREF_THRESHOLD
                )
                base_boost = (
                    true_unreferenced * INTEGRATION_TRUE_UNREF_WEIGHT
                    + min(ib.get("wire_count", 0), 15) * INTEGRATION_WIRE_WEIGHT
                    + min(ib.get("archive_count", 0), 15) * INTEGRATION_ARCHIVE_WEIGHT
                )
                integration_boost = min(base_boost * freshness, INTEGRATION_BOOST_CAP)
        r["score"] += integration_boost
        r["integration_boost"] = round(integration_boost, 3)

        # Soul-informed human benefit weighting (F-SOUL1 Phase 2, SIG-81, L-1455)
        # L-1485: additive corrections do not fix multiplicative Goodhart.
        # Weight the full score by human-benefit ratio instead of adding a flat nudge.
        pre_soul_score = r["score"]
        soul_multiplier = 1.0
        sw = _soul_weights.get(dom, {})
        sw_n = sw.get("good", 0) + sw.get("bad", 0)
        sw_ratio = sw.get("ratio", 1.0)
        if sw_n >= SOUL_MIN_SAMPLE:
            delta = sw_ratio - _soul_mean_ratio
            if delta > 0:
                soul_multiplier = min(1.0 + delta * SOUL_SCALE, SOUL_MULTIPLIER_MAX)
            else:
                soul_multiplier = max(1.0 + delta * SOUL_SCALE, SOUL_MULTIPLIER_MIN)
        r["score"] *= soul_multiplier
        r["soul_multiplier"] = round(soul_multiplier, 3)
        r["soul_boost"] = round(r["score"] - pre_soul_score, 3)

        # Adjacency bonus — neighborhood spillover (F-CITY1, L-1510)
        # Domains adjacent to high-scoring domains get a boost, creating
        # "agglomeration economics" — success in one area lifts neighbors.
        r["adjacency_bonus"] = 0.0
        # (computed after all individual scores are set — see post-loop block below)

        # Claimed domain penalty
        if dom in claimed:
            r["claimed"] = True
            r["score"] -= 10.0
        else:
            r["claimed"] = False

        # Self-dispatch norm
        if dom == "expert-swarm" and gap > SELF_DISPATCH_INTERVAL:
            r["self_dispatch_due"] = True
            r["score"] += 2.0
        else:
            r["self_dispatch_due"] = False

        # Outcome label
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
        # Campaign wave scoring (F-STR3, L-755)
        cw = (campaign_waves or {}).get(dom, {})
        max_unresolved_wave = 0
        wave_2_stalls = cw.get("wave_2_stalls", [])
        mode_repeats = cw.get("mode_repeats", [])
        for _fid, fdata in cw.get("frontiers", {}).items():
            if not fdata["resolved"]:
                max_unresolved_wave = max(max_unresolved_wave, fdata["waves"])
        wave_input = max_unresolved_wave if cw else n

        if campaign_phase_fn:
            phase, rx = campaign_phase_fn(wave_input)
        else:
            if wave_input == 0: phase, rx = "new", ""
            elif wave_input == 2: phase, rx = "danger", "COMMIT 3rd wave"
            elif wave_input >= 4: phase, rx = "veteran", f"sustained ({wave_input} waves)"
            else: phase, rx = "single", ""

        r["campaign_phase"] = phase
        r["campaign_rx"] = rx
        r["wave_2_stalls"] = wave_2_stalls
        r["mode_repeats"] = mode_repeats

        # Reward intent — what behavior should this dispatch reinforce? (L-1127, F-SWARMER1)
        r["reward_intent"] = _infer_reward_intent(r, phase)

        from dispatch_campaigns import WAVE_DANGER_BOOST, WAVE_COMMITTED_BOOST
        if phase == "danger":
            r["score"] += WAVE_DANGER_BOOST
            r["campaign_boost"] = WAVE_DANGER_BOOST
        elif phase == "committed":
            r["score"] += WAVE_COMMITTED_BOOST
            r["campaign_boost"] = WAVE_COMMITTED_BOOST
        else:
            r["campaign_boost"] = 0.0

    # Concentration penalty — anti-mediocrity selection (F-COL1, L-1587)
    # When a domain captures >10% of total dispatches with below-median quality,
    # penalize it. Prevents the degenerative spiral where the most accessible
    # domain crowds out specialists. Structural enforcement per L-601.
    if total_dispatches > 10:  # only meaningful with enough history
        exploit_scores = [r.get("ucb1_exploit", 0) for r in results
                          if r.get("ucb1_exploit", 0) > 0]
        median_exploit = (sorted(exploit_scores)[len(exploit_scores) // 2]
                          if exploit_scores else 0)
        for r in results:
            dom = r["domain"]
            oc = outcome_map.get(dom, {"merged": 0, "abandoned": 0})
            n_dom = oc["merged"] + oc["abandoned"]
            share = n_dom / total_dispatches
            exploit = r.get("ucb1_exploit", 0)
            if share > CONCENTRATION_SHARE_THRESHOLD and exploit < median_exploit:
                excess = (share - CONCENTRATION_SHARE_THRESHOLD) * 100
                penalty = min(excess * CONCENTRATION_PENALTY_SCALE,
                              CONCENTRATION_PENALTY_CAP)
                r["score"] -= penalty
                r["concentration_penalty"] = round(penalty, 3)
            else:
                r["concentration_penalty"] = 0.0

    # Adjacency bonus — post-loop computation (F-CITY1, L-1510)
    # After all individual scores are set, identify top-N domains and boost
    # their neighbors. This creates spatial spillover: good neighborhoods
    # lift adjacent areas, mimicking agglomeration economics in cities.
    if _adjacency_graph:
        score_by_dom = {r["domain"]: r["score"] for r in results}
        top_domains = set(sorted(score_by_dom, key=score_by_dom.get,
                                 reverse=True)[:ADJ_TOP_N])
        for r in results:
            neighbors = _adjacency_graph.get(r["domain"], [])
            high_neighbors = sum(1 for nb in neighbors if nb in top_domains)
            if high_neighbors > 0:
                bonus = min(high_neighbors * ADJ_BONUS_PER_NEIGHBOR, ADJ_BONUS_CAP)
                r["score"] += bonus
                r["adjacency_bonus"] = round(bonus, 3)

    # Lotka-Volterra allelopathy correction (L-1606, F-PLB5)
    if _allelopathy_coefficients and _adjacency_graph:
        for r in results:
            r.setdefault("allelopathy_boost", 0.0)
        hot_allelopaths = {
            r["domain"]: _allelopathy_coefficients.get(r["domain"], 0)
            for r in results
            if _allelopathy_coefficients.get(r["domain"], 0) > 0
            and r.get("heat") in ("HOT", "WARM")
        }
        for r in results:
            dom = r["domain"]
            boost = 0.0
            for allelo_dom, coeff in hot_allelopaths.items():
                if dom in _adjacency_graph.get(allelo_dom, []):
                    boost += coeff * ALLELO_BOOST_SCALE
            if boost > 0:
                boost = min(boost, ALLELO_BOOST_CAP)
                r["score"] += boost
                r["allelopathy_boost"] = round(boost, 3)

    # COMMIT floor (F-STR3, L-794)
    all_scores = sorted([r["score"] for r in results])
    median_score = all_scores[len(all_scores) // 2] if all_scores else 0.0
    for r in results:
        if r.get("campaign_phase") == "danger" and r["score"] < median_score:
            r["commit_floor_applied"] = True
            r["score"] = median_score
        else:
            r["commit_floor_applied"] = False

    # COMMIT dispatch guarantee (F-STR3, L-798)
    commit_candidates = [r for r in results if r.get("campaign_phase") == "danger"]
    for r in results:
        r["commit_guarantee_boost"] = 0.0
    if commit_candidates:
        ranked_by_score = sorted(results, key=lambda x: -x["score"])
        if len(ranked_by_score) >= 3:
            top3_threshold = ranked_by_score[2]["score"]
            executable_commits = [cc for cc in commit_candidates if not cc.get("execution_blocked")]
            boost_candidates = executable_commits if executable_commits else commit_candidates
            boost_candidates.sort(key=lambda x: -x["score"])
            top_commit = boost_candidates[0]
            if top_commit["score"] < top3_threshold:
                boost = round(top3_threshold - top_commit["score"] + 0.01, 3)
                top_commit["score"] += boost
                top_commit["commit_guarantee_boost"] = boost

    # COMMIT reservation (F-STR3, L-815)
    from dispatch_data import get_recent_lane_domains
    for r in results:
        r["commit_reservation"] = False
    if commit_candidates:
        recent_domains = get_recent_lane_domains()
        danger_domains = {r["domain"] for r in commit_candidates}
        has_recent_commit = any(d in danger_domains for d in recent_domains)
        if not has_recent_commit and recent_domains:
            commit_candidates.sort(key=lambda x: -x["score"])
            executable = [cc for cc in commit_candidates if not cc.get("execution_blocked")]
            if executable:
                executable[0]["commit_reservation"] = True
            elif commit_candidates:
                commit_candidates[0]["commit_reservation"] = True
                commit_candidates[0]["commit_all_blocked"] = True

    # 20% exploration floor (DARPA model, L-697)
    floor_min_n = 3
    floor_eligible = [r for r in results if r.get("outcome_n", 0) < floor_min_n]
    floor_target = max(1, int(len(results) * cold_floor_pct))
    floor_eligible.sort(key=lambda x: (x.get("outcome_n", 0), -x.get("score", 0)))
    floor_domains = {r["domain"] for r in floor_eligible[:floor_target]}
    for r in results:
        r["floor_protected"] = r["domain"] in floor_domains

    return results
