#!/usr/bin/env python3
"""
Dispatch Optimizer — Expert Economy Tool (F-ECO4)
Scores and ranks domain experiments by expected yield (Sharpe × ISO × maturity).

Usage:
    python3 tools/dispatch_optimizer.py                 # Top-10 recommendations
    python3 tools/dispatch_optimizer.py --all           # Full ranked list
    python3 tools/dispatch_optimizer.py --domain X      # Score single domain
    python3 tools/dispatch_optimizer.py --json          # JSON output

Architecture (DOMEX-META-S427, L-941 DI pattern):
    dispatch_data.py     — data loading (heat, outcomes, lanes, calibration)
    dispatch_scoring.py  — score_domain + ucb1_score + constants
    dispatch_campaigns.py — campaign wave tracking
    dispatch_meta_roles.py — meta sub-role classification
    domain_map.py        — LANE_ABBREV_TO_DOMAIN maps
"""

import argparse
import copy
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

from dispatch_data import (
    load_calibration, recalibrate, compute_gini,
    get_domain_heat, get_active_lane_domains,
    get_session_merged_domains, get_claimed_domains, get_domain_outcomes,
    get_campaign_waves_wrapper, campaign_phase_wrapper,
    wave_prescriptions_wrapper, print_wave_plan_wrapper,
)
from dispatch_scoring import (
    score_domain, ucb1_score,
    HEAT_DECAY, HEAT_PENALTY_MAX, DORMANT_BONUS, FIRST_VISIT_BONUS,
    SELF_DISPATCH_INTERVAL, VISIT_SATURATION_SCALE, EXPLORATION_GINI_THRESHOLD,
    EXPLORATION_NEW_BOOST, EXPLORATION_COLD_BOOST, COOLDOWN_SESSIONS,
    COOLDOWN_MAX_PENALTY, OUTCOME_MIN_N, OUTCOME_SUCCESS_THRESHOLD,
    OUTCOME_FAILURE_THRESHOLD, OUTCOME_BONUS, OUTCOME_MIXED_BONUS, OUTCOME_PENALTY,
)

try:
    from dispatch_campaigns import print_campaign_advisory, COMMIT_RESERVATION_WINDOW
    _CAMPAIGNS_IMPORTED = True
except ImportError:
    _CAMPAIGNS_IMPORTED = False
    COMMIT_RESERVATION_WINDOW = 5

try:
    from dispatch_meta_roles import get_meta_role_stats as _get_meta_role_stats
except ImportError:
    def _get_meta_role_stats(**kw):
        return {"historian": 0, "tooler": 0, "experimenter": 0, "mixed": 0,
                "unclassified": 0, "total": 0, "suggested_role": "tooler"}

DOMAINS_DIR = Path("domains")
CALIBRATION_FILE = Path("tools/dispatch_calibration.json")


def run(args: argparse.Namespace) -> None:
    if not DOMAINS_DIR.exists():
        print("ERROR: domains/ directory not found. Run from repo root.", file=sys.stderr)
        sys.exit(1)

    results = []
    target_domains = [args.domain] if args.domain else sorted(os.listdir(DOMAINS_DIR))
    calibration = load_calibration()
    for domain in target_domains:
        r = score_domain(domain, calibration=calibration)
        if r:
            results.append(r)

    current_session = _session_number()
    heat_map = get_domain_heat()
    claimed = get_claimed_domains()
    outcome_map = get_domain_outcomes()
    active_lanes = get_active_lane_domains()
    session_merged = get_session_merged_domains(current_session)
    campaign_waves = get_campaign_waves_wrapper()

    if getattr(args, 'wave_plan', False):
        prescriptions = wave_prescriptions_wrapper(campaign_waves)
        if args.json:
            print(json.dumps(prescriptions, indent=2, default=str))
        else:
            print_wave_plan_wrapper(prescriptions)
        return

    mode = getattr(args, 'mode', 'heuristic')
    compare = getattr(args, 'compare', False)

    if mode == "ucb1" or compare:
        ucb1_results = copy.deepcopy(results) if compare else results
        ucb1_score(ucb1_results, outcome_map, heat_map, current_session, claimed,
                   campaign_waves=campaign_waves,
                   campaign_phase_fn=campaign_phase_wrapper)
        ucb1_results.sort(key=lambda x: x["score"], reverse=True)

        if compare:
            heuristic_results = results
        elif not compare:
            results = ucb1_results
            results_limited = results if args.all or args.domain else results[:10]
            for r in results:
                if r["domain"] == "meta":
                    try: r["meta_roles"] = _get_meta_role_stats()
                    except Exception: pass
                    break
            if args.json:
                print(json.dumps(results_limited, indent=2, default=str))
                return
            _print_ucb1_output(results, results_limited, active_lanes, session_merged,
                               current_session, campaign_waves)
            return

    # Heuristic mode
    sparse_domains, saturated_domains = [], []
    for r in results:
        dom = r["domain"]
        last_active = heat_map.get(dom, 0)
        gap = current_session - last_active if last_active > 0 else 999
        if gap <= 3:
            r["score"] -= HEAT_PENALTY_MAX * (HEAT_DECAY ** gap)
            r["heat"] = "HOT"
            saturated_domains.append(dom)
        elif gap > 5:
            if last_active == 0:
                r["score"] += FIRST_VISIT_BONUS; r["heat"] = "NEW"
            else:
                r["score"] += DORMANT_BONUS; r["heat"] = "COLD"
            sparse_domains.append(dom)
        else:
            r["heat"] = "WARM"
        if 0 < gap <= COOLDOWN_SESSIONS:
            cd = COOLDOWN_MAX_PENALTY * (1.0 - (gap - 1) / COOLDOWN_SESSIONS)
            r["score"] -= cd; r["cooldown"] = True; r["cooldown_penalty"] = round(cd, 1)
        else:
            r["cooldown"] = False; r["cooldown_penalty"] = 0.0
        if dom == "expert-swarm" and gap > SELF_DISPATCH_INTERVAL:
            r["score"] += DORMANT_BONUS * 2.0; r["self_dispatch_due"] = True
        else:
            r["self_dispatch_due"] = False
        r["claimed"] = dom in claimed
        if r["claimed"]: r["score"] -= 10.0
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
                r["score"] += OUTCOME_BONUS; r["outcome_label"] = "PROVEN"
            elif rate < OUTCOME_FAILURE_THRESHOLD:
                r["score"] -= OUTCOME_PENALTY; r["outcome_label"] = "STRUGGLING"
            else:
                r["score"] += OUTCOME_MIXED_BONUS; r["outcome_label"] = "MIXED"
        else:
            r["outcome_rate"] = None; r["outcome_label"] = "NEW"
        if n > 0:
            sp = VISIT_SATURATION_SCALE * math.log(1 + n)
            r["score"] -= sp; r["saturation_penalty"] = round(sp, 1)
        else:
            r["saturation_penalty"] = 0.0

    visit_gini = compute_gini([r.get("outcome_n", 0) for r in results])
    if visit_gini > EXPLORATION_GINI_THRESHOLD:
        for r in results:
            h = r.get("heat", "")
            if h == "NEW": r["exploration_boost"] = EXPLORATION_NEW_BOOST
            elif h in ("COLD", "❄"): r["exploration_boost"] = EXPLORATION_COLD_BOOST
            else: r["exploration_boost"] = 0.0
            r["score"] += r["exploration_boost"]
    else:
        for r in results: r["exploration_boost"] = 0.0

    results.sort(key=lambda x: x["score"], reverse=True)
    if not args.all and not args.domain: results = results[:10]
    if args.json:
        print(json.dumps(results, indent=2)); return
    _print_heuristic_output(results, sparse_domains, saturated_domains, claimed, args, calibration)
    if compare: _print_compare_output(results, ucb1_results)


def _print_ucb1_output(results, results_limited, active_lanes, session_merged,
                        current_session, campaign_waves):
    """Display UCB1 mode output."""
    commit_reserved = [r for r in results if r.get("commit_reservation")]
    if commit_reserved:
        crw = COMMIT_RESERVATION_WINDOW if _CAMPAIGNS_IMPORTED else 5
        print("\n=== COMMIT RESERVATION (F-STR3, L-815) ===")
        print(f"  0/{crw} recent lanes dispatched to danger-zone domains.")
        print(f"  MANDATORY: next lane must go to a COMMIT domain (L-601 structural enforcement).")
        for cr in commit_reserved:
            cw = campaign_waves.get(cr["domain"], {})
            fids = [f for f, d in cw.get("frontiers", {}).items() if not d["resolved"] and d["waves"] == 2]
            fid_str = ", ".join(fids[:3]) if fids else "danger-zone frontiers"
            if cr.get("commit_all_blocked"):
                print(f"  ⚠ ALL danger-zone domains EXECUTION BLOCKED")
                print(f"    SKIP COMMIT — do meta/strategy/other productive work instead.")
            elif cr.get("execution_blocked"):
                print(f"  ⚠ {cr['domain']} EXECUTION BLOCKED ({cr.get('hardened_count', 0)}/{cr['active']} HARDENED)")
            else:
                print(f"  -> {cr['domain']} — {fid_str}")
    commit_promoted = [r for r in results if r.get("commit_guarantee_boost", 0) > 0]
    if commit_promoted:
        print("\n=== COMMIT DISPATCH (F-STR3, L-601) ===")
        for cp in commit_promoted:
            cw = campaign_waves.get(cp["domain"], {})
            fids = [f for f, d in cw.get("frontiers", {}).items() if not d["resolved"] and d["waves"] == 2]
            print(f"  ⚡ {cp['domain']} promoted to top-3 (+{cp['commit_guarantee_boost']:.2f}) — {', '.join(fids[:3]) or 'danger-zone'}")
    print("\n=== DISPATCH OPTIMIZER — UCB1 MODE (F-ECO5, L-697) ===")
    print(f"Single parameter c=1.414 replaces 10+ heuristic constants\n")
    print(f"{'Score':>6}  {'Domain':<25}  {'Exploit':>7}  {'Explore':>7}  {'N':>3}  {'L':>3}  {'Heat':>4}")
    print("-" * 75)
    for r in results_limited:
        hi = {"HOT": "🔥", "WARM": "~", "COLD": "❄", "NEW": "✨"}.get(r.get("heat", ""), " ")
        ex = r.get("ucb1_explore", 0)
        es = "∞" if ex == float('inf') else f"{ex:.3f}"
        ss = f"{r['score']:.1f}" if r["score"] < 999 else "∞"
        m = ""
        if r.get("floor_protected"): m += " [FLOOR]"
        if r.get("commit_guarantee_boost", 0) > 0: m += " ⚡COMMIT"
        if r.get("commit_reservation"): m += " 🚨RESERVED"
        if r.get("execution_blocked"): m += " 🛑BLOCKED"
        print(f"{ss:>6}  {r['domain']:<25}  {r.get('ucb1_exploit',0):7.3f}  {es:>7}  "
              f"{r.get('outcome_n',0):3d}  {r.get('outcome_lessons',0):3d}  {hi:>4} [{r.get('outcome_label','NEW')}]{m}")
        if r["domain"] in session_merged:
            print(f"         ✓ DONE S{current_session}: {', '.join(session_merged[r['domain']][:3])} — already MERGED this session")
        if r["domain"] in active_lanes:
            print(f"         ⚠ ACTIVE LANE(S): {', '.join(active_lanes[r['domain']][:3])} — collision risk")
        if r.get("top_frontier"):
            print(f"         → {r['top_frontier'][:72]}")
        if r["domain"] == "meta":
            try:
                ms = _get_meta_role_stats()
                if ms["total"] > 0:
                    print(f"         Meta-roles: historian {ms['historian']}/{ms['total']} ({100*ms['historian']//ms['total']}%) | "
                          f"tooler {ms['tooler']}/{ms['total']} ({100*ms['tooler']//ms['total']}%) | "
                          f"experimenter {ms['experimenter']}/{ms['total']} ({100*ms['experimenter']//ms['total']}%)")
                    print(f"         → Suggested: meta-{ms['suggested_role']} (most underserved)")
            except Exception: pass
    if active_lanes:
        print(f"\n--- Active Lane Collision Warning (L-733, F-STR2) ---")
        for dom, lanes in sorted(active_lanes.items()):
            print(f"  ⚠ {dom}: {', '.join(lanes)}")
        print(f"  Tip: avoid these domains or coordinate with active session")
    av = [r.get("outcome_n", 0) for r in results]
    gini = compute_gini(av)
    fd = [r["domain"] for r in results if r.get("floor_protected")]
    print(f"\n--- UCB1 Coverage ---")
    print(f"  Visit Gini: {gini:.3f}")
    print(f"  Coverage: {sum(1 for v in av if v > 0)}/{len(av)} domains visited")
    print(f"  Floor (20%): {len(fd)} domains protected ({', '.join(fd[:5])})")
    print(f"  Formula: avg_yield + 1.414 * sqrt(log(total_dispatches) / domain_dispatches)")
    print(f"  Unvisited domains ranked first (UCB1 = ∞), then by structural tiebreaker")
    if _CAMPAIGNS_IMPORTED:
        print_campaign_advisory(results, campaign_waves)
    na = sum(len(v) for v in active_lanes.values())
    print(f"\n--- Bundle Mode (L-812, F-EXP2) ---")
    print(f"  Active lanes this session: {na}")
    if na == 0: print(f"  Solo mode: 0.18 L/session. Open 2+ DOMEX lanes → 1.85 L/session (10x)")
    elif na == 1: print(f"  1 lane open. Adding a 2nd DOMEX lane → bundle mode (10x throughput)")
    else: print(f"  Bundle mode active ({na} lanes). Expected: ~1.85 L/session")


def _print_heuristic_output(results, sparse_domains, saturated_domains, claimed, args, calibration):
    """Display heuristic mode output."""
    print("\n=== DISPATCH OPTIMIZER (F-ECO4) ===")
    print(f"Expert economy: rank open frontiers by expected yield\n")
    if sparse_domains or saturated_domains:
        new_doms = [r["domain"] for r in results if r.get("heat") == "NEW"]
        cold_doms = [r["domain"] for r in results if r.get("heat") == "COLD"]
        if new_doms: print(f"  NEW/UNVISITED (bonus +{FIRST_VISIT_BONUS}): {', '.join(new_doms[:6])}")
        if cold_doms: print(f"  DORMANT (bonus +{DORMANT_BONUS}): {', '.join(cold_doms[:6])}")
        if saturated_domains: print(f"  SATURATED (penalty): {', '.join(saturated_domains[:6])}")
        if claimed: print(f"  CLAIMED: {', '.join(claimed)}")
        print()
    print(f"{'Score':>6}  {'Domain':<25}  {'Act':>3}  {'Res':>3}  {'ISO':>3}  {'L':>3}  {'B':>2}  {'P':>3}  {'CT':>2}  {'Heat':>4}")
    print("-" * 85)
    for r in results:
        hi = {"HOT": "🔥", "WARM": "~", "COLD": "❄", "NEW": "✨"}.get(r.get("heat", ""), " ")
        cd = f" [CD-{r.get('cooldown_penalty',0)}]" if r.get("cooldown") else ""
        mk = " [CLAIMED]" if r.get("claimed") else (" [SELF-DUE]" if r.get("self_dispatch_due") else cd)
        n = r.get("outcome_n", 0)
        ot = f" [{r.get('outcome_label','NEW')} {r['outcome_merged']}/{n}]" if n >= OUTCOME_MIN_N else ""
        print(f"{r['score']:6.1f}  {r['domain']:<25}  {r['active']:3d}  {r['resolved']:3d}  "
              f"{r['iso']:3d}  {r['lessons']:3d}  {r['beliefs']:2d}  {r['principles']:3d}  "
              f"{r['concept_types']:2d}  {hi:>4}{mk}{ot}")
        if r["top_frontier"]: print(f"         → {r['top_frontier'][:72]}")
    av = [r.get("outcome_n", 0) for r in results]
    gini = compute_gini(av)
    vc, tc = sum(1 for v in av if v > 0), len(av)
    print(f"\n--- Coverage (F-ECO5) ---")
    print(f"  Visit Gini: {gini:.3f} {'← EXPLORATION MODE ON' if gini > EXPLORATION_GINI_THRESHOLD else ''}")
    print(f"  Coverage: {vc}/{tc} ({100*vc//tc if tc else 0}%)")
    cal = calibration
    cs = f"CALIBRATED (S{cal['calibrated_session']})" if cal else "UNCALIBRATED"
    print(f"  Scoring: {cs}. Showing {'all' if args.all else 'top 10'} of {len(results)} domains.")


def _print_compare_output(heuristic_results, ucb1_results):
    """Display comparison between heuristic and UCB1 modes."""
    print(f"\n\n=== UCB1 COMPARISON (F-ECO5, L-697) ===")
    ho = [r["domain"] for r in heuristic_results[:10]]
    uo = [r["domain"] for r in ucb1_results[:10]]
    for i in range(10):
        h = ho[i] if i < len(ho) else "-"
        u = uo[i] if i < len(uo) else "-"
        print(f"  {i+1:>4}  {h:<25}  {u:<25}  {'=' if h == u else '≠'}")
    print(f"  Overlap: {len(set(ho) & set(uo))}/10. Constants: heuristic 12+, UCB1 1 (c=1.414)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch Optimizer")
    parser.add_argument("--all", action="store_true", help="Show all domains")
    parser.add_argument("--domain", metavar="NAME", help="Score a single domain")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--mode", choices=["heuristic", "ucb1"], default="ucb1", help="Scoring mode")
    parser.add_argument("--compare", action="store_true", help="Run both modes")
    parser.add_argument("--wave-plan", action="store_true", help="Per-frontier wave plan")
    parser.add_argument("--recalibrate", action="store_true", help="Re-derive weights")
    parser.add_argument("--label-at-session", type=int, metavar="N",
                        help="Show outcome labels as they were at session N (label_at_time — L-946/L-963)")
    args = parser.parse_args()
    if args.recalibrate:
        cal = recalibrate()
        if cal: print(f"\nCalibration updated: {CALIBRATION_FILE}")
        else: print("Calibration failed.", file=sys.stderr)
        return
    if args.label_at_session:
        outcomes = get_domain_outcomes(at_session=args.label_at_session)
        labels = {}
        for dom, o in outcomes.items():
            n = o["merged"] + o["abandoned"]
            if n >= OUTCOME_MIN_N:
                rate = o["merged"] / n
                if rate >= OUTCOME_SUCCESS_THRESHOLD:
                    labels[dom] = ("PROVEN", o["merged"], n)
                elif rate < OUTCOME_FAILURE_THRESHOLD:
                    labels[dom] = ("STRUGGLING", o["merged"], n)
                else:
                    labels[dom] = ("MIXED", o["merged"], n)
        print(f"=== Outcome labels at S{args.label_at_session} (label_at_time — L-946) ===")
        for dom, (label, merged, n) in sorted(labels.items(), key=lambda x: x[1][0]):
            print(f"  {label:<12} {dom:<30} ({merged}/{n})")
        print(f"\nTotal: {len(labels)} labeled domains (≥{OUTCOME_MIN_N} lanes at S{args.label_at_session})")
        return
    run(args)


if __name__ == "__main__":
    main()
