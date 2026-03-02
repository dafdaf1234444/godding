#!/usr/bin/env python3
"""Scoring functions extracted from dispatch_optimizer.py (DOMEX-META-S427).

Contains: score_domain, ucb1_score.
"""

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


def score_domain(domain: str, calibration: dict | None = None) -> dict | None:
    """Compute expected yield score for a domain's open frontiers."""
    frontier_path = DOMAINS_DIR / domain / "tasks" / "FRONTIER.md"
    domain_md_path = DOMAINS_DIR / domain / "DOMAIN.md"
    index_path = DOMAINS_DIR / domain / "INDEX.md"

    if not frontier_path.exists():
        return None

    content = frontier_path.read_text()

    # Active frontier count: only lines under ## Active (or ## Open), not Evidence Archive
    active_section = ""
    active_match = re.search(r"## (?:Active|Open)\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
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

    # First open frontier description
    first_frontier = ""
    match = re.search(r"^- (\*\*F[^*\n]+\*\*.*?)(?=^- \*\*F|\Z)", content, re.MULTILINE | re.DOTALL)
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

    # Global average quality (prior for unvisited domains)
    quality_scores = []
    for oc in outcome_map.values():
        n_oc = oc["merged"] + oc["abandoned"]
        if n_oc > 0:
            mr = oc["merged"] / n_oc
            quality_scores.append(mr * (1 + math.log1p(oc.get("lessons", 0))))
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
            quality = merge_rate * (1 + math.log1p(lessons_weighted))
            explore_term = c * math.sqrt(math.log(total_dispatches) / n)
            r["ucb1_exploit"] = round(quality, 3)
            r["ucb1_explore"] = round(explore_term, 3)
            r["score"] = quality + explore_term

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

        from dispatch_campaigns import WAVE_DANGER_BOOST, WAVE_COMMITTED_BOOST
        if phase == "danger":
            r["score"] += WAVE_DANGER_BOOST
            r["campaign_boost"] = WAVE_DANGER_BOOST
        elif phase == "committed":
            r["score"] += WAVE_COMMITTED_BOOST
            r["campaign_boost"] = WAVE_COMMITTED_BOOST
        else:
            r["campaign_boost"] = 0.0

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
