#!/usr/bin/env python3
"""F-STR1 policy backtest: compare 5 priority policies against historical DOMEX outcomes.

Method:
1. Extract all DOMEX lanes from SWARM-LANES.md + archive
2. Compute per-domain outcome metrics (MERGED rate, lessons/lane)
3. Run 5 ranking policies on current state
4. Compute Spearman rho between policy rankings and actual outcome quality
5. Answer: which policy best predicts productive domains?
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from scipy import stats  # type: ignore

REPO = Path(__file__).resolve().parent.parent.parent
LANES_FILES = [REPO / "tasks" / "SWARM-LANES.md", REPO / "tasks" / "SWARM-LANES-ARCHIVE.md"]

# Abbreviation map (must match dispatch_optimizer.py after S379 fix)
ABBREV = {
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
    "FRA": "fractals", "GT": "graph-theory", "GTH": "graph-theory",
    "GAME": "gaming", "GAMING": "gaming", "GAM": "game-theory",
    "GUE": "guesstimates", "PSY": "psychology",
    "SOC": "social-media", "STR": "strategy", "QC": "quality",
    "OR": "operations-research", "OPS": "operations-research",
    "FAR": "farming", "SEC": "security", "SECURITY": "security",
    "CC": "cryptocurrency", "CRY": "cryptography", "CRYPTO": "cryptocurrency",
    "CRYPTOGRAPHY": "cryptography",
}


def parse_domex_lanes():
    """Extract all DOMEX lanes with status and lesson count."""
    lanes = []
    for f in LANES_FILES:
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.startswith("|") or "DOMEX" not in line:
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue
            lane_id = cols[2]
            status = cols[11].strip().upper() if len(cols) > 11 else ""
            notes = cols[12] if len(cols) > 12 else ""
            etc = cols[10] if len(cols) > 10 else ""

            # Extract domain from lane ID
            m = re.match(r"DOMEX-([A-Z]+)", lane_id)
            if not m:
                continue
            domain = ABBREV.get(m.group(1))
            if not domain:
                continue

            # Extract session
            sm = re.search(r"S(\d+)", lane_id)
            session = int(sm.group(1)) if sm else 0

            # Count lessons in notes
            lesson_ids = re.findall(r"\bL-\d+\b", notes)

            # Check for EAD fields
            has_expect = "expect=" in etc and "expect=none" not in etc.lower()
            has_actual = "actual=" in etc and "actual=none" not in etc.lower()
            has_diff = "diff=" in etc and "diff=none" not in etc.lower()
            ead_score = sum([has_expect, has_actual, has_diff])

            lanes.append({
                "lane_id": lane_id,
                "domain": domain,
                "session": session,
                "status": status,
                "lessons": len(lesson_ids),
                "lesson_ids": lesson_ids,
                "ead_score": ead_score,
            })
    return lanes


def compute_domain_outcomes(lanes):
    """Per-domain: MERGED rate, avg lessons/lane, total lanes."""
    domain_stats = defaultdict(lambda: {"total": 0, "merged": 0, "abandoned": 0,
                                         "lessons": 0, "ead_sum": 0})
    for lane in lanes:
        d = lane["domain"]
        s = domain_stats[d]
        s["total"] += 1
        if "MERGED" in lane["status"]:
            s["merged"] += 1
        elif "ABANDONED" in lane["status"]:
            s["abandoned"] += 1
        s["lessons"] += lane["lessons"]
        s["ead_sum"] += lane["ead_score"]

    outcomes = {}
    for domain, s in domain_stats.items():
        completed = s["merged"] + s["abandoned"]
        merge_rate = s["merged"] / completed if completed > 0 else 0
        l_per_lane = s["lessons"] / s["total"] if s["total"] > 0 else 0
        avg_ead = s["ead_sum"] / s["total"] if s["total"] > 0 else 0
        # Composite quality = merge_rate * (1 + log(lessons+1))
        import math
        quality = merge_rate * (1 + math.log1p(s["lessons"]))
        outcomes[domain] = {
            "total_lanes": s["total"],
            "merged": s["merged"],
            "abandoned": s["abandoned"],
            "merge_rate": round(merge_rate, 3),
            "total_lessons": s["lessons"],
            "lessons_per_lane": round(l_per_lane, 2),
            "avg_ead": round(avg_ead, 2),
            "quality_score": round(quality, 3),
        }
    return outcomes


def load_domain_frontiers():
    """Load active frontier counts and age per domain."""
    domains_dir = REPO / "domains"
    info = {}
    for d in sorted(domains_dir.iterdir()):
        if not d.is_dir():
            continue
        frontier_file = d / "tasks" / "FRONTIER.md"
        if not frontier_file.exists():
            continue
        text = frontier_file.read_text(encoding="utf-8", errors="replace")
        # Count active frontiers
        active_section = re.search(r"## Active(.*?)(?:\n## |\Z)", text, re.DOTALL)
        active_count = 0
        if active_section:
            for line in active_section.group(1).splitlines():
                if re.match(r"\s*[-*]\s+\*\*F-", line):
                    active_count += 1
        # Get updated session
        um = re.search(r"Updated:.*S(\d+)", text)
        updated = int(um.group(1)) if um else 0
        age = max(0, 379 - updated) if updated > 0 else 999
        info[d.name] = {
            "active_frontiers": active_count,
            "updated_session": updated,
            "age": age,
        }
    return info


def policy_fifo(domain_info):
    """Oldest-first: high age = high priority."""
    return {d: info["age"] + 0.1 * info["active_frontiers"]
            for d, info in domain_info.items()}


def policy_risk_first(domain_info):
    """Risk = unresolved pressure + aging."""
    return {d: 2.0 * info["active_frontiers"] + info["age"]
            for d, info in domain_info.items()}


def policy_value_density(domain_info, outcomes):
    """Value = historical quality score / (1 + active pressure)."""
    scores = {}
    for d, info in domain_info.items():
        quality = outcomes.get(d, {}).get("quality_score", 0)
        scores[d] = quality / (1 + info["active_frontiers"] * 0.5)
    return scores


def policy_hybrid(domain_info, outcomes):
    """Balanced: quality + frontier count + age, normalized."""
    scores = {}
    for d, info in domain_info.items():
        quality = outcomes.get(d, {}).get("quality_score", 0)
        scores[d] = quality + info["active_frontiers"] + 0.5 * min(info["age"], 50)
    return scores


def policy_ucb1(domain_info, outcomes):
    """UCB1 as implemented in dispatch_optimizer: exploit + explore."""
    import math
    total_dispatches = sum(outcomes.get(d, {}).get("total_lanes", 0) for d in domain_info)
    if total_dispatches == 0:
        total_dispatches = 1
    scores = {}
    for d, info in domain_info.items():
        n = outcomes.get(d, {}).get("total_lanes", 0)
        if n == 0:
            scores[d] = float("inf")
            continue
        avg_yield = outcomes.get(d, {}).get("lessons_per_lane", 0)
        explore = 1.414 * math.sqrt(math.log(total_dispatches) / n)
        scores[d] = avg_yield + explore
    return scores


def rank_domains(scores):
    """Return domains sorted by score descending."""
    return sorted(scores.keys(), key=lambda d: scores[d], reverse=True)


def compute_correlations(policy_rankings, outcome_rankings, common_domains):
    """Spearman rho between policy rank order and outcome rank order."""
    if len(common_domains) < 4:
        return {"rho": None, "p": None, "n": len(common_domains), "note": "too few domains"}
    policy_ranks = [policy_rankings.index(d) for d in common_domains]
    outcome_ranks = [outcome_rankings.index(d) for d in common_domains]
    rho, p = stats.spearmanr(policy_ranks, outcome_ranks)
    return {"rho": round(float(rho), 4), "p": round(float(p), 6), "n": len(common_domains)}


def main():
    print("=== F-STR1 Policy Backtest ===\n")

    # 1. Extract DOMEX lane outcomes
    lanes = parse_domex_lanes()
    print(f"Parsed {len(lanes)} DOMEX lanes")
    outcomes = compute_domain_outcomes(lanes)
    print(f"Outcomes for {len(outcomes)} domains")

    # 2. Load current domain state
    domain_info = load_domain_frontiers()
    print(f"Domain state for {len(domain_info)} domains\n")

    # 3. Run all 5 policies
    policies = {
        "fifo": policy_fifo(domain_info),
        "risk_first": policy_risk_first(domain_info),
        "value_density": policy_value_density(domain_info, outcomes),
        "hybrid": policy_hybrid(domain_info, outcomes),
        "ucb1": policy_ucb1(domain_info, outcomes),
    }

    # 4. Rank by quality_score for ground truth
    outcome_ranked = sorted(outcomes.keys(),
                            key=lambda d: outcomes[d]["quality_score"], reverse=True)
    print("--- Domain Outcomes (ground truth) ---")
    for i, d in enumerate(outcome_ranked):
        o = outcomes[d]
        print(f"  {i+1:2d}. {d:25s} quality={o['quality_score']:5.2f} "
              f"merge={o['merge_rate']:.0%} L={o['total_lessons']} "
              f"lanes={o['total_lanes']} L/lane={o['lessons_per_lane']:.1f}")

    # 5. Compare each policy
    print("\n--- Policy Rankings & Correlation ---")
    results = {}
    for name, scores in policies.items():
        ranked = rank_domains(scores)
        common = [d for d in ranked if d in outcomes]
        corr = compute_correlations(ranked, outcome_ranked, common)
        results[name] = {
            "top_5": ranked[:5],
            "correlation": corr,
            "scores_top10": {d: round(scores[d], 3) for d in ranked[:10]},
        }
        rho_str = f"{corr['rho']:.3f}" if corr['rho'] is not None else "N/A"
        p_str = f"{corr['p']:.4f}" if corr['p'] is not None else "N/A"
        print(f"\n  {name:15s}  rho={rho_str}  p={p_str}  n={corr['n']}")
        print(f"    top-5: {', '.join(ranked[:5])}")

    # 6. Best policy
    valid = {k: v for k, v in results.items() if v["correlation"]["rho"] is not None}
    if valid:
        best = max(valid, key=lambda k: valid[k]["correlation"]["rho"])
        worst = min(valid, key=lambda k: valid[k]["correlation"]["rho"])
        print(f"\n--- Best policy: {best} (rho={valid[best]['correlation']['rho']:.3f}) ---")
        print(f"--- Worst policy: {worst} (rho={valid[worst]['correlation']['rho']:.3f}) ---")
    else:
        best = "inconclusive"
        worst = "inconclusive"

    # 7. Secondary analysis: L/lane ranking correlation
    ll_ranked = sorted(outcomes.keys(),
                       key=lambda d: outcomes[d]["lessons_per_lane"], reverse=True)
    print("\n--- L/lane Ranking Correlation ---")
    ll_results = {}
    for name, scores in policies.items():
        ranked = rank_domains(scores)
        common = [d for d in ranked if d in outcomes]
        corr = compute_correlations(ranked, ll_ranked, common)
        ll_results[name] = corr
        rho_str = f"{corr['rho']:.3f}" if corr['rho'] is not None else "N/A"
        print(f"  {name:15s}  rho={rho_str}  (vs L/lane)")

    # 8. Top-3 overlap analysis
    print("\n--- Top-3 Overlap ---")
    for name, scores in policies.items():
        ranked = rank_domains(scores)[:3]
        overlap = len(set(ranked) & set(outcome_ranked[:3]))
        print(f"  {name:15s}  overlap={overlap}/3  top-3={ranked}")

    # 9. Write artifact
    artifact = {
        "experiment": "F-STR1 policy backtest",
        "session": "S379",
        "method": "Retrospective correlation: 5 priority policies ranked against historical DOMEX domain outcomes",
        "n_lanes": len(lanes),
        "n_domains_with_outcomes": len(outcomes),
        "n_domains_total": len(domain_info),
        "outcomes": {d: outcomes[d] for d in outcome_ranked},
        "policy_results": results,
        "ll_results": ll_results,
        "best_policy_quality": best,
        "best_policy_ll": max(ll_results, key=lambda k: (ll_results[k]["rho"] or -999)) if ll_results else "N/A",
        "top3_overlap": {name: len(set(rank_domains(scores)[:3]) & set(outcome_ranked[:3]))
                         for name, scores in policies.items()},
    }

    out = REPO / "experiments" / "strategy" / "f-str1-policy-backtest-s379.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n")
    print(f"\nArtifact: {out}")


if __name__ == "__main__":
    main()
