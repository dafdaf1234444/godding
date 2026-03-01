#!/usr/bin/env python3
"""F-SP4: Proximity-conditioned preferential attachment model.

Decomposes citation probability into degree-driven (PA) vs recency-driven
(proximity) components. Tests whether PA signal survives when session gap
is controlled for.

Three models compared via conditional log-likelihood + BIC:
  - PA only:      weight(i) ∝ (k_i + 1)^γ
  - Proximity only: weight(i) ∝ exp(-λ * Δs_i)
  - Joint:        weight(i) ∝ (k_i + 1)^γ * exp(-λ * Δs_i)

Usage:
    python3 tools/proximity_pa.py          # human-readable report
    python3 tools/proximity_pa.py --json   # JSON output
"""

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def extract_lesson_number(filename: str) -> int | None:
    m = re.match(r"L-(\d+)\.md", filename)
    return int(m.group(1)) if m else None


def parse_session(filepath: Path) -> int | None:
    """Extract session number from lesson file, handling format variations."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read(2000)  # first 2KB is sufficient

    # Try structured comment: <!-- lesson: ... | session: S375 | ... -->
    m = re.search(r"session:\s*S?(\d+)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # Try header line: Session: S355 or **Session**: S307 or Session: 48
    m = re.search(r"\*{0,2}Session\*{0,2}:\s*S?(\d+)", text)
    if m:
        return int(m.group(1))

    return None


def parse_cites(filepath: Path) -> list[int]:
    """Extract L-NNN references from Cites: header."""
    refs = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("Cites:"):
                refs.extend(int(x) for x in re.findall(r"\bL-(\d+)\b", line))
                break
    return refs


def build_citation_dag(lessons_dir: Path) -> tuple[dict, dict]:
    """Build DAG and session map.

    Returns:
        dag: {lesson_num: [cited_lesson_nums]}
        sessions: {lesson_num: session_number}
    """
    dag = {}
    sessions = {}
    for fname in sorted(os.listdir(lessons_dir)):
        num = extract_lesson_number(fname)
        if num is None:
            continue
        cites = parse_cites(lessons_dir / fname)
        prior_cites = [c for c in cites if c < num]
        dag[num] = prior_cites
        sess = parse_session(lessons_dir / fname)
        if sess is not None:
            sessions[num] = sess
    return dag, sessions


def conditional_log_likelihood(dag, sessions, gamma, lam, model="joint"):
    """Compute conditional log-likelihood for a choice model.

    For each citation event (src cites target), the probability is:
        P(target | pool) = w(target) / sum(w(i) for i in pool)

    where w(i) depends on the model:
        PA:        w = (k_i + 1)^gamma
        Proximity: w = exp(-lambda * delta_s)
        Joint:     w = (k_i + 1)^gamma * exp(-lambda * delta_s)
    """
    degree = defaultdict(int)
    all_nodes = set()
    ll = 0.0
    n_events = 0

    for src in sorted(dag.keys()):
        all_nodes.add(src)
        src_sess = sessions.get(src)

        if not dag[src]:
            continue

        # Pool: all nodes before src
        pool = [nd for nd in all_nodes if nd < src]
        if not pool:
            continue

        for target in dag[src]:
            if target not in all_nodes:
                continue

            # Compute weights for all pool members
            target_sess = sessions.get(target)

            # Target weight
            k_t = degree[target]
            w_target = _weight(k_t, src, target, src_sess, target_sess,
                               sessions, gamma, lam, model)

            # Pool sum
            w_sum = 0.0
            for nd in pool:
                k_nd = degree[nd]
                nd_sess = sessions.get(nd)
                w_nd = _weight(k_nd, src, nd, src_sess, nd_sess,
                               sessions, gamma, lam, model)
                w_sum += w_nd

            if w_sum > 0 and w_target > 0:
                ll += math.log(w_target / w_sum)
                n_events += 1

            degree[target] += 1

    return ll, n_events


def _weight(k, src, nd, src_sess, nd_sess, sessions, gamma, lam, model):
    """Compute weight for a pool member under the given model."""
    if model == "pa":
        return (k + 1) ** gamma
    elif model == "proximity":
        ds = _session_gap(src, nd, src_sess, nd_sess)
        return math.exp(-lam * ds)
    elif model == "joint":
        ds = _session_gap(src, nd, src_sess, nd_sess)
        return ((k + 1) ** gamma) * math.exp(-lam * ds)
    elif model == "uniform":
        return 1.0
    else:
        return 1.0


def _session_gap(src, nd, src_sess, nd_sess):
    """Compute session gap, falling back to lesson-number gap scaled."""
    if src_sess is not None and nd_sess is not None:
        return abs(src_sess - nd_sess)
    # Fallback: lesson number gap / 2 (rough proxy: ~2 lessons per session)
    return abs(src - nd) / 2.0


def grid_search(dag, sessions, model, gamma_range=None, lam_range=None):
    """Find optimal parameters via grid search on conditional LL."""
    best_ll = -float("inf")
    best_params = {}

    if model == "uniform":
        ll, n = conditional_log_likelihood(dag, sessions, 0, 0, "uniform")
        return {"ll": ll, "n_events": n, "params": {}}

    if model == "pa":
        if gamma_range is None:
            gamma_range = [x * 0.1 for x in range(-5, 25)]
        for g in gamma_range:
            ll, n = conditional_log_likelihood(dag, sessions, g, 0, "pa")
            if ll > best_ll:
                best_ll = ll
                best_params = {"gamma": g, "ll": ll, "n_events": n}
        # Refine around best
        g0 = best_params["gamma"]
        for g in [g0 + x * 0.02 for x in range(-5, 6)]:
            ll, n = conditional_log_likelihood(dag, sessions, g, 0, "pa")
            if ll > best_ll:
                best_ll = ll
                best_params = {"gamma": round(g, 3), "ll": ll, "n_events": n}
        return best_params

    if model == "proximity":
        if lam_range is None:
            lam_range = [x * 0.005 for x in range(1, 40)]
        for l in lam_range:
            ll, n = conditional_log_likelihood(dag, sessions, 0, l, "proximity")
            if ll > best_ll:
                best_ll = ll
                best_params = {"lambda": l, "ll": ll, "n_events": n}
        # Refine
        l0 = best_params["lambda"]
        for l in [l0 + x * 0.001 for x in range(-5, 6)]:
            if l > 0:
                ll, n = conditional_log_likelihood(dag, sessions, 0, l, "proximity")
                if ll > best_ll:
                    best_ll = ll
                    best_params = {"lambda": round(l, 4), "ll": ll, "n_events": n}
        return best_params

    if model == "joint":
        if gamma_range is None:
            gamma_range = [x * 0.1 for x in range(-5, 20)]
        if lam_range is None:
            lam_range = [x * 0.01 for x in range(1, 30)]
        for g in gamma_range:
            for l in lam_range:
                ll, n = conditional_log_likelihood(dag, sessions, g, l, "joint")
                if ll > best_ll:
                    best_ll = ll
                    best_params = {"gamma": g, "lambda": l, "ll": ll, "n_events": n}
        # Refine
        g0, l0 = best_params["gamma"], best_params["lambda"]
        for g in [g0 + x * 0.02 for x in range(-5, 6)]:
            for l in [l0 + x * 0.002 for x in range(-5, 6)]:
                if l > 0:
                    ll, n = conditional_log_likelihood(dag, sessions, g, l, "joint")
                    if ll > best_ll:
                        best_ll = ll
                        best_params = {"gamma": round(g, 3), "lambda": round(l, 4),
                                       "ll": ll, "n_events": n}
        return best_params

    return best_params


def compute_bic(ll, k_params, n_events):
    """BIC = -2*LL + k*ln(n)"""
    if n_events <= 0:
        return float("inf")
    return -2 * ll + k_params * math.log(n_events)


def proximity_profile(dag, sessions):
    """Compute citation rate as a function of session gap."""
    degree = defaultdict(int)
    all_nodes = set()

    # Bin by session gap
    gap_citations = defaultdict(int)  # gap_bin -> count of citations
    gap_exposure = defaultdict(int)   # gap_bin -> total pool exposure at this gap

    for src in sorted(dag.keys()):
        all_nodes.add(src)
        src_sess = sessions.get(src)
        if not dag[src]:
            continue

        pool = [nd for nd in all_nodes if nd < src]
        if not pool:
            continue

        # Compute gap distribution for pool
        pool_gaps = {}
        for nd in pool:
            gap = _session_gap(src, nd, src_sess, sessions.get(nd))
            gap_bin = int(gap)
            pool_gaps[nd] = gap_bin

        # Exposure: for each citation from this lesson, all pool members contribute
        n_cites = len(dag[src])
        gap_dist = defaultdict(int)
        for nd in pool:
            gap_dist[pool_gaps[nd]] += 1
        for gb, cnt in gap_dist.items():
            gap_exposure[gb] += cnt * n_cites

        # Citations
        for target in dag[src]:
            if target in pool_gaps:
                gap_citations[pool_gaps[target]] += 1

        # Update degrees
        for target in dag[src]:
            degree[target] += 1

    # Compute rates
    rates = {}
    for gb in sorted(set(list(gap_citations.keys()) + list(gap_exposure.keys()))):
        att = gap_citations.get(gb, 0)
        exp = gap_exposure.get(gb, 0)
        if exp > 0:
            rates[gb] = {"rate": att / exp, "citations": att, "exposure": exp}
    return rates


def degree_conditional_gamma(dag, sessions, gap_bins):
    """Compute PA gamma conditional on session gap bin.

    For each gap bin, compute the pool-normalized PA kernel rate
    restricted to citations within that gap range.
    """
    degree = defaultdict(int)
    all_nodes = set()

    results = {}
    for bin_label, (gap_lo, gap_hi) in gap_bins.items():
        attachments_at_k = defaultdict(int)
        exposure_at_k = defaultdict(int)

        degree_local = defaultdict(int)
        all_nodes_local = set()

        for src in sorted(dag.keys()):
            all_nodes_local.add(src)
            src_sess = sessions.get(src)
            if not dag[src]:
                continue

            pool = [nd for nd in all_nodes_local if nd < src]
            if not pool:
                continue

            # Filter pool to nodes within gap range
            pool_in_gap = []
            for nd in pool:
                gap = _session_gap(src, nd, src_sess, sessions.get(nd))
                if gap_lo <= gap < gap_hi:
                    pool_in_gap.append(nd)

            if not pool_in_gap:
                continue

            # Count citations to nodes within this gap range
            targets_in_gap = [t for t in dag[src] if t in set(pool_in_gap)]
            if not targets_in_gap:
                # Still add exposure
                for nd in pool_in_gap:
                    exposure_at_k[degree_local[nd]] += len(targets_in_gap) or 1
                for target in dag[src]:
                    degree_local[target] += 1
                continue

            # Exposure from this source's citations
            pool_deg_dist = defaultdict(int)
            for nd in pool_in_gap:
                pool_deg_dist[degree_local[nd]] += 1
            for k, cnt in pool_deg_dist.items():
                exposure_at_k[k] += cnt * len(targets_in_gap)

            # Attachments
            for target in targets_in_gap:
                attachments_at_k[degree_local[target]] += 1

            for target in dag[src]:
                degree_local[target] += 1

        # Fit gamma for this gap bin
        kernel_rates = {}
        for k in sorted(set(list(attachments_at_k.keys()) + list(exposure_at_k.keys()))):
            att = attachments_at_k.get(k, 0)
            exp = exposure_at_k.get(k, 0)
            if exp > 0:
                kernel_rates[k] = att / exp

        # Log-log regression k>=1 with n>=5 filter (L-736 methodology)
        rate_k1 = {k: r for k, r in kernel_rates.items()
                   if k >= 1 and r > 0 and attachments_at_k.get(k, 0) >= 5}

        gamma = None
        r_sq = None
        n_pts = 0
        if len(rate_k1) >= 3:
            log_k = [math.log(k) for k in rate_k1.keys()]
            log_r = [math.log(r) for r in rate_k1.values()]
            n_pts = len(log_k)
            sx = sum(log_k)
            sy = sum(log_r)
            sxy = sum(x * y for x, y in zip(log_k, log_r))
            sx2 = sum(x * x for x in log_k)
            denom = n_pts * sx2 - sx ** 2
            if abs(denom) > 1e-10:
                gamma = (n_pts * sxy - sx * sy) / denom
                intercept = (sy - gamma * sx) / n_pts
                y_mean = sy / n_pts
                ss_tot = sum((y - y_mean) ** 2 for y in log_r)
                ss_res = sum((y - (intercept + gamma * x)) ** 2
                             for x, y in zip(log_k, log_r))
                r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        n_events = sum(attachments_at_k.values())
        results[bin_label] = {
            "gamma": round(gamma, 4) if gamma is not None else None,
            "r_squared": round(r_sq, 4) if r_sq is not None else None,
            "n_events": n_events,
            "n_regression_points": n_pts,
            "gap_range": [gap_lo, gap_hi],
        }

    return results


def main():
    parser = argparse.ArgumentParser(
        description="F-SP4: Proximity-conditioned PA model"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--lessons-dir", default="memory/lessons")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    lessons_dir = repo_root / args.lessons_dir

    if not lessons_dir.is_dir():
        print(f"ERROR: {lessons_dir} not found", file=sys.stderr)
        sys.exit(1)

    # Build DAG with session info
    dag, sessions = build_citation_dag(lessons_dir)
    total_lessons = len(dag)
    lessons_with_sessions = sum(1 for v in sessions.values() if v is not None)
    total_edges = sum(len(v) for v in dag.values())
    lessons_with_cites = sum(1 for v in dag.values() if v)

    print("=== F-SP4: Proximity-Conditioned PA Model ===", file=sys.stderr)
    print(f"Lessons: {total_lessons} ({lessons_with_sessions} with sessions, "
          f"{lessons_with_cites} with citations)", file=sys.stderr)
    print(f"Citation events: {total_edges}", file=sys.stderr)
    print(f"Session coverage: {lessons_with_sessions/total_lessons*100:.1f}%",
          file=sys.stderr)

    # --- Model fitting via conditional log-likelihood ---
    print("\nFitting models (grid search)...", file=sys.stderr)

    uniform_fit = grid_search(dag, sessions, "uniform")
    pa_fit = grid_search(dag, sessions, "pa")
    prox_fit = grid_search(dag, sessions, "proximity")
    joint_fit = grid_search(dag, sessions, "joint")

    n = pa_fit.get("n_events", joint_fit.get("n_events", 1))

    bic_uniform = compute_bic(uniform_fit["ll"], 0, n)
    bic_pa = compute_bic(pa_fit["ll"], 1, n)
    bic_prox = compute_bic(prox_fit["ll"], 1, n)
    bic_joint = compute_bic(joint_fit["ll"], 2, n)

    # --- Proximity profile ---
    print("Computing proximity profile...", file=sys.stderr)
    prox_profile = proximity_profile(dag, sessions)

    # --- Conditional gamma (PA within proximity bins) ---
    print("Computing conditional gamma by gap bin...", file=sys.stderr)
    gap_bins = {
        "near (0-5)": (0, 6),
        "mid (6-20)": (6, 21),
        "far (21-50)": (21, 51),
        "distant (51+)": (51, 9999),
    }
    cond_gamma = degree_conditional_gamma(dag, sessions, gap_bins)

    # --- Assemble results ---
    results = {
        "metadata": {
            "tool": "proximity_pa.py",
            "frontier": "F-SP4",
            "session": "S383",
            "total_lessons": total_lessons,
            "lessons_with_sessions": lessons_with_sessions,
            "session_coverage": round(lessons_with_sessions / total_lessons, 4),
            "total_edges": total_edges,
            "n_events": n,
        },
        "models": {
            "uniform": {
                "params": {},
                "ll": round(uniform_fit["ll"], 2),
                "bic": round(bic_uniform, 2),
                "n_params": 0,
            },
            "pa_only": {
                "params": {"gamma": pa_fit.get("gamma")},
                "ll": round(pa_fit["ll"], 2),
                "bic": round(bic_pa, 2),
                "n_params": 1,
            },
            "proximity_only": {
                "params": {"lambda": prox_fit.get("lambda")},
                "ll": round(prox_fit["ll"], 2),
                "bic": round(bic_prox, 2),
                "n_params": 1,
            },
            "joint": {
                "params": {
                    "gamma": joint_fit.get("gamma"),
                    "lambda": joint_fit.get("lambda"),
                },
                "ll": round(joint_fit["ll"], 2),
                "bic": round(bic_joint, 2),
                "n_params": 2,
            },
        },
        "model_comparison": {
            "delta_bic_pa_vs_uniform": round(bic_uniform - bic_pa, 2),
            "delta_bic_prox_vs_uniform": round(bic_uniform - bic_prox, 2),
            "delta_bic_joint_vs_uniform": round(bic_uniform - bic_joint, 2),
            "delta_bic_joint_vs_pa": round(bic_pa - bic_joint, 2),
            "delta_bic_joint_vs_prox": round(bic_prox - bic_joint, 2),
            "delta_bic_prox_vs_pa": round(bic_pa - bic_prox, 2),
            "best_model": min(
                [("uniform", bic_uniform), ("pa_only", bic_pa),
                 ("proximity_only", bic_prox), ("joint", bic_joint)],
                key=lambda x: x[1]
            )[0],
        },
        "conditional_gamma": cond_gamma,
        "proximity_profile": {
            str(k): {
                "rate": round(v["rate"], 6),
                "citations": v["citations"],
                "exposure": v["exposure"],
            }
            for k, v in sorted(prox_profile.items())[:30]  # top 30 gap bins
        },
    }

    # --- Confounding analysis ---
    marginal_gamma = pa_fit.get("gamma", 0)
    near_gamma = cond_gamma.get("near (0-5)", {}).get("gamma")
    mid_gamma = cond_gamma.get("mid (6-20)", {}).get("gamma")
    far_gamma = cond_gamma.get("far (21-50)", {}).get("gamma")

    confounding = {
        "marginal_gamma": marginal_gamma,
        "near_gamma": near_gamma,
        "mid_gamma": mid_gamma,
        "far_gamma": far_gamma,
    }

    if near_gamma is not None and marginal_gamma is not None:
        confounding["gamma_reduction_near"] = round(
            marginal_gamma - near_gamma, 4)
        confounding["confounding_fraction"] = round(
            (marginal_gamma - near_gamma) / marginal_gamma, 4
        ) if marginal_gamma != 0 else None

    # Proximity share: fraction of LL explained by proximity vs PA
    ll_gain_pa = pa_fit["ll"] - uniform_fit["ll"]
    ll_gain_prox = prox_fit["ll"] - uniform_fit["ll"]
    ll_gain_joint = joint_fit["ll"] - uniform_fit["ll"]

    confounding["ll_gain_pa"] = round(ll_gain_pa, 2)
    confounding["ll_gain_prox"] = round(ll_gain_prox, 2)
    confounding["ll_gain_joint"] = round(ll_gain_joint, 2)

    if ll_gain_joint > 0:
        confounding["proximity_share_of_joint"] = round(
            ll_gain_prox / ll_gain_joint, 4)
        confounding["pa_share_of_joint"] = round(
            ll_gain_pa / ll_gain_joint, 4)
    else:
        confounding["proximity_share_of_joint"] = None
        confounding["pa_share_of_joint"] = None

    results["confounding_analysis"] = confounding

    # --- Verdict ---
    best = results["model_comparison"]["best_model"]
    joint_gamma = joint_fit.get("gamma", 0)
    joint_lam = joint_fit.get("lambda", 0)

    verdict_parts = []
    verdict_parts.append(f"Best model: {best}")
    verdict_parts.append(
        f"PA gamma: marginal={marginal_gamma}, joint={joint_gamma}")
    if near_gamma is not None:
        verdict_parts.append(f"Near-conditional gamma={near_gamma}")
    if confounding.get("proximity_share_of_joint") is not None:
        prox_pct = confounding["proximity_share_of_joint"] * 100
        verdict_parts.append(f"Proximity explains {prox_pct:.0f}% of joint LL gain")

    delta_joint_pa = results["model_comparison"]["delta_bic_joint_vs_pa"]
    if delta_joint_pa > 10:
        verdict_parts.append("Joint STRONGLY better than PA-only")
    elif delta_joint_pa > 2:
        verdict_parts.append("Joint better than PA-only")
    elif delta_joint_pa > -2:
        verdict_parts.append("Joint ≈ PA-only (inconclusive)")
    else:
        verdict_parts.append("PA-only better than joint (proximity adds noise)")

    results["verdict"] = "; ".join(verdict_parts)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"F-SP4: PROXIMITY-CONDITIONED PA MODEL")
        print(f"{'='*60}")
        print(f"\nData: {total_lessons} lessons, {total_edges} citations, "
              f"{n} conditional events")
        print(f"Session coverage: {lessons_with_sessions}/{total_lessons} "
              f"({results['metadata']['session_coverage']*100:.1f}%)")

        print(f"\n--- Model Comparison (BIC, lower=better) ---")
        for name in ["uniform", "pa_only", "proximity_only", "joint"]:
            m = results["models"][name]
            params = ", ".join(f"{k}={v}" for k, v in m["params"].items()) if m["params"] else "none"
            marker = " <-- BEST" if name == best else ""
            print(f"  {name:18s}: BIC={m['bic']:10.2f}  LL={m['ll']:10.2f}  "
                  f"params=[{params}]{marker}")

        print(f"\n--- BIC Deltas (positive = first model worse) ---")
        mc = results["model_comparison"]
        print(f"  Joint vs PA-only:     ΔBIC = {mc['delta_bic_joint_vs_pa']:+.2f}")
        print(f"  Joint vs Proximity:   ΔBIC = {mc['delta_bic_joint_vs_prox']:+.2f}")
        print(f"  Proximity vs PA-only: ΔBIC = {mc['delta_bic_prox_vs_pa']:+.2f}")
        print(f"  Joint vs Uniform:     ΔBIC = {mc['delta_bic_joint_vs_uniform']:+.2f}")

        print(f"\n--- Confounding Analysis ---")
        print(f"  Marginal gamma (PA-only):  {marginal_gamma}")
        print(f"  Joint gamma:               {joint_gamma}")
        print(f"  Gamma by proximity bin:")
        for label, data in cond_gamma.items():
            g = data.get("gamma")
            r2 = data.get("r_squared")
            n_ev = data.get("n_events", 0)
            g_str = f"{g:.4f}" if g is not None else "N/A"
            r2_str = f"{r2:.4f}" if r2 is not None else "N/A"
            print(f"    {label:20s}: γ={g_str}, R²={r2_str}, n={n_ev}")

        cf = results["confounding_analysis"]
        if cf.get("gamma_reduction_near") is not None:
            print(f"  Gamma reduction (near): {cf['gamma_reduction_near']:+.4f}")
        if cf.get("confounding_fraction") is not None:
            print(f"  Confounding fraction:   {cf['confounding_fraction']*100:.1f}% "
                  f"of gamma explained by proximity")

        print(f"\n--- LL Decomposition ---")
        print(f"  LL gain from PA:        {cf['ll_gain_pa']:+.2f}")
        print(f"  LL gain from Proximity: {cf['ll_gain_prox']:+.2f}")
        print(f"  LL gain from Joint:     {cf['ll_gain_joint']:+.2f}")
        if cf.get("proximity_share_of_joint") is not None:
            print(f"  Proximity share:        {cf['proximity_share_of_joint']*100:.1f}%")
            print(f"  PA share:               {cf['pa_share_of_joint']*100:.1f}%")

        print(f"\n--- Proximity Profile (top 15 gap bins) ---")
        pp = results["proximity_profile"]
        for i, (gap, data) in enumerate(sorted(pp.items(), key=lambda x: int(x[0]))):
            if i >= 15:
                break
            rate = data["rate"]
            n_c = data["citations"]
            bar = "█" * min(int(rate * 3000), 40)
            print(f"  Δs={int(gap):3d}: rate={rate:.6f} ({n_c:3d} cites) {bar}")

        print(f"\n{'='*60}")
        print(f"VERDICT: {results['verdict']}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
