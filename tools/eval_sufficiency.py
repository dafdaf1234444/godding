#!/usr/bin/env python3
"""
eval_sufficiency.py — PHIL-14 Mission Sufficiency Scorer
Last validated: S427 — avg_lp=1.84 (50-session window), ECE improvement ongoing.

Scores each of the four PHIL-14 goals (Collaborate, Increase, Protect, Truthful)
on a 0-3 scale using proxy metrics from swarm state files.

Scale:
  0 = Insufficient — below minimum threshold
  1 = Adequate     — meets threshold, gaps in rate or grounding
  2 = Sufficient   — exceeds threshold with internal evidence
  3 = Excellent    — exceeds threshold with external grounding

Usage:
  python3 tools/eval_sufficiency.py          # human-readable report
  python3 tools/eval_sufficiency.py --json   # machine-readable JSON
  python3 tools/eval_sufficiency.py --save   # save artifact to experiments/evaluation/

Related: F-EVAL1, PHIL-14, PHIL-16, L-316, domains/evaluation/tasks/FRONTIER.md
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Data loaders and scorers extracted to sub-modules (S441, L-941 DI pattern)
from eval_sufficiency_data import (  # noqa: E402
    _get_current_session, _load_session_log, _count_swarm_lanes, _load_proxy_k,
    _count_challenges, _count_human_signals, _count_frontiers,
    _load_con1_baseline, _count_lessons, _count_domains,
)
from eval_sufficiency_scores import (  # noqa: E402
    _continuous_score, _continuous_verdict, _reconcile_verdicts, _finalize_goal,
    score_collaborate, score_increase, score_protect, score_truthful,
)





# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def compute_sufficiency() -> dict:
    """Compute PHIL-14 mission sufficiency scores."""
    sessions = _load_session_log()
    lanes = _count_swarm_lanes()
    proxy_k = _load_proxy_k()
    challenges = _count_challenges()
    signals = _count_human_signals()
    frontiers = _count_frontiers()
    con1 = _load_con1_baseline()
    lessons = _count_lessons()
    domains = _count_domains()

    # Score each goal
    collaborate = score_collaborate(lanes, con1, signals)
    increase = score_increase(sessions, frontiers, domains, lessons)
    protect = score_protect(proxy_k, challenges)
    truthful = score_truthful(challenges, signals, frontiers)

    # Composite score (discrete + continuous)
    scores = [collaborate["score"], increase["score"], protect["score"], truthful["score"]]
    composite = sum(scores) / (len(scores) * 3)  # normalize to 0-1

    # F-EVAL4 hardening: continuous composite reveals margin that discrete hides
    continuous_scores = [
        collaborate.get("continuous_score", float(collaborate["score"])),
        increase.get("continuous_score", float(increase["score"])),
        protect.get("continuous_score", float(protect["score"])),
        truthful.get("continuous_score", float(truthful["score"])),
    ]
    continuous_composite = sum(continuous_scores) / (len(continuous_scores) * 3)

    # Lowest-scoring goal = next improvement target (use continuous for precision)
    _goal_items = [("Collaborate", collaborate), ("Increase", increase),
                   ("Protect", protect), ("Truthful", truthful)]
    goal_scores = {n: d["score"] for n, d in _goal_items}
    goal_continuous = {n: d.get("continuous_score", float(d["score"])) for n, d in _goal_items}
    next_target = min(goal_continuous, key=goal_continuous.get)

    # Overall verdict — uses continuous composite as tiebreaker (F-EVAL4)
    min_score = min(scores)
    avg_score = sum(scores) / len(scores)
    if min_score == 0:
        overall = "INSUFFICIENT"
    elif avg_score < 1.5:
        overall = "PARTIAL_FAIL"
    elif avg_score < 2.0:
        overall = "PARTIAL"
    elif avg_score < 2.5:
        overall = "SUFFICIENT"
    else:
        overall = "EXCELLENT"

    # F-EVAL4: continuous override — if continuous composite strongly disagrees, annotate
    continuous_overall = _continuous_verdict(sum(continuous_scores) / len(continuous_scores))
    overall_note = None
    if continuous_overall != overall:
        overall_note = (
            f"continuous_composite={continuous_composite:.2f} suggests {continuous_overall} "
            f"(discrete says {overall})"
        )

    margin_warnings = [f"{n}: {d['margin_warning']}" for n, d in _goal_items if d.get("margin_warning")]
    adjustments = [f"{n}: {d['adjustment']}" for n, d in _goal_items if d.get("adjustment")]

    # F-EVAL4 (L-928): stratified scores from Increase goal (DOMEX vs non-DOMEX)
    stratified_scores = {
        "DOMEX": {
            "avg_lp": increase.get("domex_avg_lp", 0),
            "n_sessions": increase.get("domex_n", 0),
        },
        "non_DOMEX": {
            "avg_lp": increase.get("non_domex_avg_lp", 0),
            "n_sessions": increase.get("non_domex_n", 0),
        },
        "ratio": round(
            increase.get("domex_avg_lp", 0) / increase.get("non_domex_avg_lp", 1)
            if increase.get("non_domex_avg_lp", 0) > 0 else float("inf"), 2
        ),
        "domex_fraction": round(
            increase.get("domex_n", 0) / max(1, increase.get("domex_n", 0) + increase.get("non_domex_n", 0)), 2
        ),
    }

    result = {
        "session": _get_current_session(),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "goals": {
            "Collaborate": collaborate,
            "Increase": increase,
            "Protect": protect,
            "Truthful": truthful,
        },
        "scores": goal_scores,
        "continuous_scores": {k: round(v, 2) for k, v in goal_continuous.items()},
        "stratified_scores": stratified_scores,
        "composite_normalized": round(composite, 3),
        "continuous_composite": round(continuous_composite, 3),
        "avg_score_of_3": round(avg_score, 2),
        "overall": overall,
        "continuous_overall": continuous_overall,
        "next_improvement_target": next_target,
        "scale": {
            "0": "Insufficient — below minimum threshold",
            "1": "Adequate — meets threshold, gaps in rate or grounding",
            "2": "Sufficient — exceeds threshold with internal evidence",
            "3": "Excellent — exceeds threshold with external grounding",
        },
        "related": ["F-EVAL1", "PHIL-14", "PHIL-16", "L-316", "B-EVAL1/2/3"],
    }
    if overall_note:
        result["overall_note"] = overall_note
    if margin_warnings:
        result["margin_warnings"] = margin_warnings
    if adjustments:
        result["adjustments"] = adjustments
    return result


def print_report(result: dict) -> None:
    """Human-readable report."""
    print(f"=== PHIL-14 Mission Sufficiency — {result['session']} ===\n")
    print(f"Overall: {result['overall']} (discrete {result['avg_score_of_3']}/3, continuous {result['continuous_composite']:.0%})")
    if result.get("overall_note"):
        print(f"  Note: {result['overall_note']}")
    print(f"Next improvement target: {result['next_improvement_target']}\n")

    for goal, data in result["goals"].items():
        bar = "█" * data["score"] + "░" * (3 - data["score"])
        c_score = data.get("continuous_score", float(data["score"]))
        adj_marker = " *" if data.get("adjustment") else ""
        print(f"  {goal:12s} [{bar}] {data['score']}/3 (c={c_score:.2f}) — {data['verdict']}{adj_marker}")
        print(f"    {data['rationale']}")
        if data.get("adjustment"):
            print(f"    >> {data['adjustment']}")
        if data.get("margin_warning"):
            print(f"    ~~ {data['margin_warning']}")
        if data.get("note"):
            print(f"    !! {data['note']}")
        print()

    # Stratified scores
    strat = result.get("stratified_scores", {})
    if strat:
        domex = strat.get("DOMEX", {})
        non_domex = strat.get("non_DOMEX", {})
        print(f"  Stratified L+P: DOMEX={domex.get('avg_lp', 0):.1f} (n={domex.get('n_sessions', 0)}), "
              f"non-DOMEX={non_domex.get('avg_lp', 0):.1f} (n={non_domex.get('n_sessions', 0)}), "
              f"ratio={strat.get('ratio', 0):.1f}x")

    if result.get("adjustments"):
        print(f"\n  Adjustments ({len(result['adjustments'])}):")
        for adj in result["adjustments"]:
            print(f"    >> {adj}")

    if result.get("margin_warnings"):
        print(f"\n  Margin warnings ({len(result['margin_warnings'])}):")
        for mw in result["margin_warnings"]:
            print(f"    ~~ {mw}")

    print(f"\nScale: 0=Insufficient, 1=Adequate, 2=Sufficient, 3=Excellent")
    print(f"  * = continuous scoring adjusted discrete verdict")
    print(f"Related: {', '.join(result['related'])}")


if __name__ == "__main__":
    result = compute_sufficiency()

    save = "--save" in sys.argv
    as_json = "--json" in sys.argv or save

    if as_json:
        output = json.dumps(result, indent=2)
        if save:
            out_path = ROOT / "experiments" / "evaluation" / f"eval-sufficiency-{result['session'].lower()}.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output + "\n", encoding="utf-8")
            print(f"Artifact saved: {out_path}")
        else:
            print(output)
    else:
        print_report(result)
