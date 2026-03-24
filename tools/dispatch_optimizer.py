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
    from closeable_frontiers import section_closeable_frontiers as _section_closeable
    _CLOSEABLE_IMPORTED = True
except ImportError:
    _CLOSEABLE_IMPORTED = False

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


def _load_closure_verdicts() -> dict[str, dict]:
    """Load frontier closure-readiness from cached classifier (#L-1117).

    Returns {frontier_id: {score, verdict}} for active frontiers.
    """
    if not _CLOSEABLE_IMPORTED:
        return {}
    try:
        classifier_files = sorted(
            Path("experiments/nk-complexity").glob("f-nk6-closure-classifier-s*.json")
        )
        if not classifier_files:
            return {}
        data = json.loads(classifier_files[-1].read_text())
        scores = data.get("results", {}).get("frontier_scores", {}) or data.get("frontier_scores", {})
        verdicts = {}
        for fid, info in scores.items():
            total = info.get("total", 0)
            if total >= 8:
                verdict = "CLOSEABLE"
            elif total >= 6:
                verdict = "APPROACHING"
            elif total >= 4:
                verdict = "NEEDS_WORK"
            else:
                verdict = "BLOCKED"
            verdicts[fid] = {"score": total, "verdict": verdict}
        return verdicts
    except Exception:
        return {}


def _enrich_closure(results: list[dict], verdicts: dict) -> None:
    """Add frontier closure-readiness fields to results (#L-1117)."""
    if not verdicts:
        return
    for r in results:
        tf = r.get("top_frontier", "")
        m = re.search(r"\*\*(F-\w+)\*\*", tf)
        if m:
            fid = m.group(1)
            if fid in verdicts:
                r["frontier_closure_score"] = verdicts[fid]["score"]
                r["frontier_closure_verdict"] = verdicts[fid]["verdict"]


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

    closure_verdicts = _load_closure_verdicts()
    _enrich_closure(results, closure_verdicts)

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

        # Recombination readiness boost (L-1375: advisory → scoring)
        # Domains with high-scoring cross-domain missing-edge partners get
        # a boost, turning recombination from display-only to dispatch driver.
        _enrich_recombination(ucb1_results)
        RECOMB_BOOST_PER_TARGET = 0.15  # per top-2 target
        RECOMB_BOOST_CAP = 0.4
        for r in ucb1_results:
            targets = r.get("recombination_targets", [])
            if targets:
                boost = min(
                    sum(min(t.get("score", 0), 1.0) * RECOMB_BOOST_PER_TARGET
                        for t in targets[:3]),
                    RECOMB_BOOST_CAP)
                r["score"] += boost
                r["recombination_boost"] = round(boost, 3)
            else:
                r["recombination_boost"] = 0.0
        ucb1_results.sort(key=lambda x: x["score"], reverse=True)

        # Concentration rebalancing (S499 bottleneck repair, F-STR5 S503 fix)
        # Problem: additive penalty (-3.4 for META) is insufficient against base
        # scores of 30-50. Fix: multiplicative penalty scales with score magnitude.
        # meta +2.0 maint bonus + expert-swarm +2.0 self-dispatch = 57% lane share
        CONCENTRATION_THRESHOLD = 0.10
        CONCENTRATION_DECAY_RATE = 3.0  # excess share × rate = penalty fraction
        total_n = sum(r.get("outcome_n", 0) for r in ucb1_results)
        if total_n > 20:
            for r in ucb1_results:
                share = r.get("outcome_n", 0) / total_n
                if share > CONCENTRATION_THRESHOLD:
                    excess = share - CONCENTRATION_THRESHOLD
                    # Multiplicative: reduce score by fraction proportional to excess
                    # 10% excess → 30% reduction, 15% excess → 45% reduction
                    penalty_frac = min(excess * CONCENTRATION_DECAY_RATE, 0.60)
                    penalty = r["score"] * penalty_frac
                    r["score"] -= penalty
                    r["concentration_penalty"] = round(penalty, 2)
                else:
                    r["concentration_penalty"] = 0.0
                r["concentration_pct"] = round(share * 100, 1)
            ucb1_results.sort(key=lambda x: x["score"], reverse=True)

        if compare:
            heuristic_results = results
        elif not compare:
            results = ucb1_results
            # ε-greedy override (F-RAND1): with prob ε, swap top domain with a random pick
            epsilon = getattr(args, "epsilon", 0.0)
            epsilon_note = None
            if epsilon > 0.0 and len(results) > 1:
                import random as _random
                _rng = _random.Random(current_session)
                if _rng.random() < epsilon:
                    rand_idx = _rng.randint(1, len(results) - 1)
                    results[0], results[rand_idx] = results[rand_idx], results[0]
                    epsilon_note = (f"⚡ ε-dispatch (ε={epsilon}): swapped top domain to "
                                   f"'{results[0]['domain']}' (was '{results[rand_idx]['domain']}')")
            # ISO-33 stochastic falsification (L-1373, von Neumann minimax):
            # When falsification rate is below 20% target, assign mode=falsification
            # to the top domain with probability = (target - actual) / target.
            # Mixed strategies are game-theoretically optimal for adversarial testing.
            falsif_note = None
            if len(results) > 0:
                falsif_note = _stochastic_falsification(results, current_session)

            results_limited = results if args.all or args.domain else results[:10]
            for r in results:
                if r["domain"] == "meta":
                    try: r["meta_roles"] = _get_meta_role_stats()
                    except Exception: pass
                    break
            if args.json:
                print(json.dumps(results_limited, indent=2, default=str))
                return
            if epsilon_note:
                print(f"\n{epsilon_note}")
            if falsif_note:
                print(f"\n{falsif_note}")
            _print_ucb1_output(results, results_limited, active_lanes, session_merged,
                               current_session, campaign_waves,
                               auto_fix=getattr(args, "fix", False))
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


def _enrich_recombination(results):
    """Attach per-domain recombination M3 targets to results (#L-1130, L-1249 yield)."""
    try:
        from knowledge_recombine import load_lessons, find_missing_edges, compute_yield_scores
        lessons = load_lessons()
        candidates = find_missing_edges(lessons, min_shared=3)
        compute_yield_scores(candidates, lessons)
        cross = [c for c in candidates if c["cross_domain"]]
        # Build domain → top candidates map (yield-ranked)
        dom_cands = {}
        for c in cross:
            for d in (c["domain_a"], c["domain_b"]):
                dom_cands.setdefault(d, []).append(c)
        for r in results:
            cands = dom_cands.get(r["domain"], [])
            if cands:
                top = sorted(cands, key=lambda x: x.get("yield_score", 0), reverse=True)[:2]
                r["recombination_targets"] = [
                    {"pair": f"{c['parent_a']}×{c['parent_b']}",
                     "partner_domain": c["domain_b"] if c["domain_a"] == r["domain"] else c["domain_a"],
                     "score": c.get("yield_score", c["score"]), "shared": c["shared_count"]}
                    for c in top
                ]
    except Exception:
        pass


def _print_ucb1_output(results, results_limited, active_lanes, session_merged,
                        current_session, campaign_waves, *, auto_fix=False):
    """Display UCB1 mode output."""
    commit_reserved = [r for r in results if r.get("commit_reservation")]
    if commit_reserved:
        crw = COMMIT_RESERVATION_WINDOW if _CAMPAIGNS_IMPORTED else 5
        print("\n=== COMMIT RESERVATION (F-STR3, L-815) ===")
        print(f"  0/{crw} recent lanes dispatched to danger-zone domains.")
        print(f"  MANDATORY: next lane must go to a COMMIT domain (L-601, L-1138 Goldstone-to-massive).")
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
        if r.get("concentration_penalty", 0) > 0: m += f" [CONC-{r['concentration_pct']:.0f}%]"
        if r.get("floor_protected"): m += " [FLOOR]"
        if r.get("commit_guarantee_boost", 0) > 0: m += " ⚡COMMIT"
        if r.get("commit_reservation"): m += " 🚨RESERVED"
        if r.get("execution_blocked"): m += " 🛑BLOCKED"
        sm = r.get("soul_multiplier", 1.0)
        if sm > 1.0: m += f" [SOULx{sm:.2f}]"
        elif sm < 1.0: m += f" [SOULx{sm:.2f}]"
        ab = r.get("adjacency_bonus", 0)
        if ab > 0: m += f" [ADJ+{ab:.1f}]"
        print(f"{ss:>6}  {r['domain']:<25}  {r.get('ucb1_exploit',0):7.3f}  {es:>7}  "
              f"{r.get('outcome_n',0):3d}  {r.get('outcome_lessons',0):3d}  {hi:>4} [{r.get('outcome_label','NEW')}]{m}")
        if r["domain"] in session_merged:
            print(f"         ✓ DONE S{current_session}: {', '.join(session_merged[r['domain']][:3])} — already MERGED this session")
        if r["domain"] in active_lanes:
            print(f"         ⚠ ACTIVE LANE(S): {', '.join(active_lanes[r['domain']][:3])} — collision risk")
        if r.get("top_frontier"):
            closure = ""
            if r.get("frontier_closure_verdict"):
                v = r["frontier_closure_verdict"]
                s = r.get("frontier_closure_score", "?")
                icon = {"CLOSEABLE": "🟢", "APPROACHING": "🟡", "NEEDS_WORK": "⚪", "BLOCKED": "🛑"}.get(v, "")
                closure = f" {icon} [{v} {s}/10]"
            print(f"         → {r['top_frontier'][:72]}{closure}")
        if r.get("recommended_mode"):
            print(f"         🎯 Recommended mode: {r['recommended_mode']} (ISO-33 minimax)")
        if r.get("reward_intent"):
            print(f"         Reward: {r['reward_intent']}")
        if r.get("recombination_targets"):
            for rt in r["recombination_targets"][:2]:
                print(f"         M3: {rt['pair']} (×{rt['partner_domain']}) score={rt['score']}")
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
    import os as _os
    total_all = len([d for d in _os.listdir(DOMAINS_DIR) if (DOMAINS_DIR / d).is_dir()]) if DOMAINS_DIR.exists() else len(results)
    invisible = total_all - len(results)
    print(f"\n--- UCB1 Coverage ---")
    print(f"  Visit Gini: {gini:.3f}")
    print(f"  Coverage: {sum(1 for v in av if v > 0)}/{total_all} domains ({len(results)} with active frontiers, {invisible} invisible — empty active sections, L-1055)")
    print(f"  Floor (20%): {len(fd)} domains protected ({', '.join(fd[:5])})")
    print(f"  Formula: avg_yield + 1.414 * sqrt(log(total_dispatches) / domain_dispatches)")
    print(f"  Unvisited domains ranked first (UCB1 = ∞), then by structural tiebreaker")
    if invisible > 0:
        print(f"  ⚠ {invisible} domains frontier-depleted (all active frontiers resolved). Run historian_repair.py to detect.")
    if _CAMPAIGNS_IMPORTED:
        print_campaign_advisory(results, campaign_waves)
    na = sum(len(v) for v in active_lanes.values())
    print(f"\n--- Bundle Mode (L-812, F-EXP2) ---")
    print(f"  Active lanes this session: {na}")
    if na == 0: print(f"  Solo mode: 0.18 L/session. Open 2+ DOMEX lanes → 1.85 L/session (10x)")
    elif na == 1: print(f"  1 lane open. Adding a 2nd DOMEX lane → bundle mode (10x throughput)")
    else: print(f"  Bundle mode active ({na} lanes). Expected: ~1.85 L/session")

    # Recombination advisory (SIG-62, F-SWARMER1, L-1127, L-1249 yield)
    try:
        from knowledge_recombine import load_lessons, find_missing_edges, compute_yield_scores
        lessons = load_lessons()
        candidates = find_missing_edges(lessons, min_shared=3)
        compute_yield_scores(candidates, lessons)
        cross = [c for c in candidates if c["cross_domain"]]
        if cross:
            print(f"\n--- Recombination Candidates (SIG-62, L-1249 yield-ranked) ---")
            print(f"  {len(cross)} cross-domain missing edges (top 3):")
            for c in cross[:3]:
                print(f"    {c['parent_a']}×{c['parent_b']} ({c['domain_a']}×{c['domain_b']}) "
                      f"shared={c['shared_count']} score={c.get('yield_score', c['score'])}")
    except Exception:
        pass

    # Falsification advisory (F-META18, P-243, L-601 structural enforcement)
    _print_falsification_advisory(results, current_session)

    # Maintenance action bridge (F-SWARMER1, diagnosis-to-action)
    _print_maintenance_actions(auto_fix=auto_fix)


def _get_recent_falsif_rate(current_session: int) -> tuple[int, int]:
    """Count recent falsification lanes vs total lanes in last 20 sessions."""
    recent_falsif = 0
    recent_total = 0
    base = Path(__file__).resolve().parent.parent
    for lf in (base / "tasks" / "SWARM-LANES.md", base / "tasks" / "SWARM-LANES-ARCHIVE.md"):
        if not lf.exists():
            continue
        for line in lf.read_text().splitlines():
            if not line.startswith("|") or "Date" in line or "---" in line:
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue
            sess_m = re.search(r"S?(\d+)", cols[3] if len(cols) > 3 else "")
            if not sess_m:
                continue
            sess = int(sess_m.group(1))
            if sess < max(1, current_session - 20):
                continue
            recent_total += 1
            etc = cols[10] if len(cols) > 10 else ""
            if "; mode=falsification" in etc or etc.startswith("mode=falsification"):
                recent_falsif += 1
    return recent_falsif, recent_total


def _stochastic_falsification(results: list[dict], current_session: int) -> str | None:
    """ISO-33 minimax: stochastically recommend falsification mode (L-1373).

    When falsification rate is below 20% target, recommend mode=falsification
    for the top dispatched domain with probability proportional to the deficit.
    Uses session-seeded RNG for reproducibility.
    """
    import random as _random

    FALSIF_TARGET = 0.20
    recent_falsif, recent_total = _get_recent_falsif_rate(current_session)
    if recent_total == 0:
        return None
    rate = recent_falsif / recent_total
    if rate >= FALSIF_TARGET:
        return None  # Quota met

    # Probability of recommending falsification = (target - actual) / target
    # At 0% rate: prob = 1.0. At 15%: prob = 0.25. At 20%: prob = 0.0.
    prob = min((FALSIF_TARGET - rate) / FALSIF_TARGET, 0.5)  # cap at 50%

    rng = _random.Random(current_session * 7919)  # different seed from ε-greedy
    if rng.random() < prob:
        # Assign falsification mode to top domain
        target = results[0]
        target["recommended_mode"] = "falsification"
        return (f"🎯 ISO-33 minimax dispatch: mode=falsification recommended for "
                f"'{target['domain']}' (falsif rate {rate:.0%} < {FALSIF_TARGET:.0%} target, "
                f"p={prob:.2f})")
    return None


def _print_falsification_advisory(results, current_session):
    """Surface falsification candidates and debt status (F-META18, P-243).

    The 0% falsification rate (1/749 lanes total) is caused by:
    1. No suggestion mechanism — agents don't know WHAT to falsify
    2. Zero-cost bypass in open_lane.py
    3. No dispatch benefit for falsification lanes
    This function addresses cause #1 by surfacing testable claims.
    """
    debt_path = Path(__file__).resolve().parent.parent / "workspace" / "falsification-debt.json"
    try:
        debt = json.loads(debt_path.read_text())
    except (OSError, json.JSONDecodeError):
        debt = {"consecutive_skips": 0, "total_skips": 0}

    recent_falsif, recent_total = _get_recent_falsif_rate(current_session)
    rate = recent_falsif / recent_total if recent_total > 0 else 0
    if rate >= 0.20:
        return  # Quota met, no advisory needed

    # Build falsification candidates from PHILOSOPHY.md
    phil_path = Path(__file__).resolve().parent.parent / "beliefs" / "PHILOSOPHY.md"
    candidates = []
    if phil_path.exists():
        phil_text = phil_path.read_text()
        # Parse PHIL-N entries from claims table: | PHIL-N | claim | type | grounding | status |
        for m in re.finditer(
            r"\|\s*(PHIL-\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|",
            phil_text
        ):
            phil_id = m.group(1).strip()
            claim = m.group(2).strip()[:60]
            claim_type = m.group(3).strip().lower()  # axiom/observed
            grounding = m.group(4).strip().lower()    # grounded/partial/aspirational
            status = m.group(5).strip().lower()

            if "superseded" in status:
                continue

            # Score: lower grounding + older test = higher falsification priority
            score = 0
            if "aspirational" in grounding:
                score += 3
            elif "partial" in grounding:
                score += 2
            elif "axiom" in claim_type:
                score += 1.5

            # Age since last test (extract most recent S-number from status)
            test_sessions = [int(s) for s in re.findall(r"S(\d+)", status)]
            if test_sessions:
                latest = max(test_sessions)
                age = current_session - latest
                score += min(age / 20, 3)  # Up to +3 for staleness
            else:
                score += 3  # Never tested

            candidates.append({
                "id": phil_id,
                "claim": claim,
                "grounding": grounding,
                "score": score,
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n--- Falsification Advisory (P-243, F-META18) ---")
    print(f"  Rate: {recent_falsif}/{recent_total} ({rate:.0%} vs 20% target)")
    skips = debt.get("consecutive_skips", 0)
    max_skip = debt.get("max_consecutive_before_block", 3)
    if skips > 0:
        print(f"  Debt: {skips}/{max_skip} consecutive skips"
              f"{' — NEXT LANE MUST BE FALSIFICATION' if skips >= max_skip else ''}")
    if candidates:
        print(f"  Top falsification targets (most testable claims):")
        for c in candidates[:3]:
            print(f"    {c['id']} ({c['grounding']}): {c['claim']}")
        print(f"  Use: --mode falsification --expect '{candidates[0]['id']} is FALSE because <reason>'")


def _resolve_action(message: str) -> tuple[str, bool] | None:
    """Map a maintenance message to a concrete fix command.

    Returns (command, auto_safe) or None if no resolver matches.
    auto_safe=True means the command is idempotent and safe to auto-run.
    F-SWARMER1 intervention #2: diagnosis-to-action bridge (S465).
    """
    resolvers: list[tuple[str, str, bool]] = [
        (r"Count drift in INDEX\.md", "python3 tools/sync_state.py", True),
        (r"uncorrected citation.*falsified", "python3 tools/correction_propagation.py --classify", True),
        (r"\[lanes-compact\]", "python3 tools/lanes_compact.py --age 5", True),
        (r"active dispatch lane.*no active coordinator", "", False),
        (r"\[health-check\]", "python3 tools/maintenance.py --learn", False),
        (r"\[paper-reswarm\]", "", False),
        (r"\[fundamental-setup-reswarm\]", "", False),
        (r"\[mission-constraint-reswarm\]", "", False),
        (r"\[human-signal-harvest\]", "", False),
        (r"dark matter.*BELOW", "python3 tools/sync_state.py", True),
        (r"Council health CRITICAL", "", False),
        (r"INDEX\.md bucket overflow", "", False),
    ]
    for pattern, cmd, safe in resolvers:
        if re.search(pattern, message):
            return (cmd, safe) if cmd else None
    return None


def _print_maintenance_actions(auto_fix: bool = False):
    """Display actionable maintenance items with resolved fix commands.

    Bridges maintenance diagnostics into dispatch output so DUE/URGENT items
    are visible during domain selection. F-SWARMER1 intervention #2.

    With auto_fix=True, runs safe/idempotent fix commands automatically.
    """
    actions_path = Path(__file__).resolve().parent.parent / "workspace" / "maintenance-actions.json"
    try:
        data = json.loads(actions_path.read_text())
        items = data.get("items", [])
        if not items:
            return
        urgent = [i for i in items if i["priority"] == "URGENT"]
        due = [i for i in items if i["priority"] == "DUE"]
        print(f"\n--- Maintenance Actions ({len(urgent)} URGENT, {len(due)} DUE) ---")
        fixed = []
        for item in urgent[:3]:
            action = _resolve_action(item["message"])
            suffix = f"  → {action[0]}" if action else ""
            print(f"  !!! {item['message'][:100]}{suffix}")
        for item in due[:5]:
            action = _resolve_action(item["message"])
            suffix = f"  → {action[0]}" if action else ""
            print(f"   !  {item['message'][:100]}{suffix}")
            if auto_fix and action and action[1]:
                fixed.append((item["message"], action[0]))
        if len(items) > 8:
            print(f"  ... {len(items) - 8} more (run python3 tools/maintenance.py)")
        if fixed:
            import subprocess
            print(f"\n  AUTO-FIX: running {len(fixed)} safe command(s)...")
            for msg, cmd in fixed:
                print(f"    $ {cmd}")
                try:
                    result = subprocess.run(
                        cmd.split(), capture_output=True, text=True, timeout=30,
                        cwd=str(Path(__file__).resolve().parent.parent),
                    )
                    if result.returncode == 0:
                        print(f"      done")
                    else:
                        print(f"      exit {result.returncode}: {result.stderr[:80]}")
                except (subprocess.TimeoutExpired, OSError) as exc:
                    print(f"      error: {exc}")
    except (OSError, json.JSONDecodeError, KeyError):
        pass


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
    parser.add_argument("--epsilon", type=float, default=0.15, metavar="E",
                        help="ε-greedy dispatch: with prob E bypass UCB1 and pick randomly (F-RAND1, L-601 structural enforcement)")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-run safe/idempotent maintenance fixes (F-SWARMER1 action bridge)")
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
