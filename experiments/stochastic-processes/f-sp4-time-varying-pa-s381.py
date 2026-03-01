#!/usr/bin/env python3
"""F-SP4 time-varying PA kernel: era-specific γ estimates.

Tests whether the citation preferential attachment kernel changes across
protocol eras (Early/Mid/DOMEX/Recent). Hypothesis: EAD enforcement and
DOMEX mode changed citation dynamics.

Usage:
    python3 experiments/stochastic-processes/f-sp4-time-varying-pa-s381.py
"""

import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LESSONS_DIR = REPO / "memory" / "lessons"

ERA_BOUNDARIES = {
    "early": (0, 186),      # S1-S186: pre-structure
    "mid": (187, 330),       # S187-S330: structured, pre-DOMEX
    "domex": (331, 360),     # S331-S360: expert mode + EAD enforcement
    "recent": (361, 9999),   # S361+: mature
}


def parse_lesson(filepath: Path) -> dict:
    """Extract lesson number, session, and Cites: from a lesson file."""
    m = re.match(r"L-(\d+)\.md", filepath.name)
    if not m:
        return {}
    num = int(m.group(1))
    session = None
    cites = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if session is None:
                sm = re.search(r"[Ss]ession:\s*S(\d+)", line)
                if sm:
                    session = int(sm.group(1))
            if line.startswith("Cites:"):
                cites = [int(x) for x in re.findall(r"\bL-(\d+)\b", line)]
                break
    return {"num": num, "session": session, "cites": cites}


def classify_era(session: int | None) -> str:
    """Assign era based on session number."""
    if session is None:
        return "unknown"
    for era, (lo, hi) in ERA_BOUNDARIES.items():
        if lo <= session <= hi:
            return era
    return "unknown"


def compute_pa_kernel(dag: dict, node_set: set) -> dict:
    """Compute PA kernel metrics for a subset of the DAG.

    dag: {lesson_num: [cited_lesson_nums]} — full DAG
    node_set: set of lesson numbers to consider as sources
    """
    degree = defaultdict(int)
    attachments_at_k = defaultdict(int)
    exposure_at_k = defaultdict(int)
    attachment_degrees = []
    all_nodes = set()

    for src in sorted(dag.keys()):
        all_nodes.add(src)
        if src not in node_set:
            # Still update degrees from non-era citations
            for target in dag[src]:
                degree[target] += 1
            continue

        pool_nodes = [nd for nd in all_nodes if nd < src]
        if dag[src]:
            pool_degree_dist = defaultdict(int)
            for nd in pool_nodes:
                pool_degree_dist[degree[nd]] += 1

            n_cites = len(dag[src])
            for k, cnt in pool_degree_dist.items():
                exposure_at_k[k] += cnt * n_cites

            for target in dag[src]:
                d = degree[target]
                attachments_at_k[d] += 1
                attachment_degrees.append(d)
                degree[target] += 1

    n = len(attachment_degrees)
    if n < 5:
        return {"n_events": n, "gamma": None, "r_squared": None, "error": "too few events"}

    # Kernel rates
    kernel_rates = {}
    for k in sorted(set(list(attachments_at_k.keys()) + list(exposure_at_k.keys()))):
        att = attachments_at_k.get(k, 0)
        exp = exposure_at_k.get(k, 0)
        if exp > 0:
            kernel_rates[k] = att / exp

    # Log-log regression for k>=1
    rate_k1_plus = {k: r for k, r in kernel_rates.items() if k >= 1 and r > 0}
    gamma, r_squared = None, None
    if len(rate_k1_plus) >= 3:
        log_k = [math.log(k) for k in rate_k1_plus.keys()]
        log_r = [math.log(r) for r in rate_k1_plus.values()]
        n_pts = len(log_k)
        sum_x = sum(log_k)
        sum_y = sum(log_r)
        sum_xy = sum(x * y for x, y in zip(log_k, log_r))
        sum_x2 = sum(x * x for x in log_k)
        denom = n_pts * sum_x2 - sum_x ** 2
        if abs(denom) > 1e-10:
            gamma = (n_pts * sum_xy - sum_x * sum_y) / denom
            intercept = (sum_y - gamma * sum_x) / n_pts
            y_mean = sum_y / n_pts
            ss_tot = sum((y - y_mean) ** 2 for y in log_r)
            ss_res = sum((y - (intercept + gamma * x)) ** 2
                         for x, y in zip(log_k, log_r))
            r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    # Zero-inflation
    rate_0 = kernel_rates.get(0, 0)
    rates_pos = [r for k, r in kernel_rates.items() if k >= 1]
    rate_ratio = None
    if rate_0 > 0 and rates_pos:
        rate_ratio = round((sum(rates_pos) / len(rates_pos)) / rate_0, 4)

    # PA ratio
    final_degrees = list(degree.values())
    mean_final = sum(final_degrees) / len(final_degrees) if final_degrees else 0
    mean_attach = sum(attachment_degrees) / n if n > 0 else 0
    pa_ratio = round(mean_attach / mean_final, 4) if mean_final > 0 else None

    # Gini
    sorted_degrees = sorted(attachment_degrees)
    n_d = len(sorted_degrees)
    gini = 0
    if n_d > 1:
        cumsum = sum(sorted_degrees)
        weighted_sum = sum((2 * (i + 1) - n_d - 1) * d for i, d in enumerate(sorted_degrees))
        gini = weighted_sum / (n_d * cumsum) if cumsum > 0 else 0

    # Fraction k=0
    k0_count = sum(1 for d in attachment_degrees if d == 0)

    return {
        "n_events": n,
        "gamma": round(gamma, 4) if gamma is not None else None,
        "r_squared": round(r_squared, 4) if r_squared is not None else None,
        "rate_ratio_k1_k0": rate_ratio,
        "pa_ratio": pa_ratio,
        "gini": round(gini, 4),
        "fraction_k0": round(k0_count / n, 4),
        "mean_degree_at_attachment": round(mean_attach, 3),
        "rate_k0": round(rate_0, 6) if rate_0 else 0,
        "n_kernel_points": len(rate_k1_plus),
        "kernel_rates": {str(k): round(v, 6) for k, v in sorted(kernel_rates.items())},
    }


def permutation_test_gamma(dag, sets_a, sets_b, observed_diff, n_perm=1000):
    """Permutation test for difference in γ between two era sets."""
    import random
    combined = list(sets_a | sets_b)
    n_a = len(sets_a)
    count_more_extreme = 0

    for _ in range(n_perm):
        random.shuffle(combined)
        perm_a = set(combined[:n_a])
        perm_b = set(combined[n_a:])
        res_a = compute_pa_kernel(dag, perm_a)
        res_b = compute_pa_kernel(dag, perm_b)
        g_a = res_a.get("gamma")
        g_b = res_b.get("gamma")
        if g_a is not None and g_b is not None:
            if abs(g_a - g_b) >= abs(observed_diff):
                count_more_extreme += 1

    return count_more_extreme / n_perm


def main():
    # Parse all lessons
    lessons = {}
    for fname in sorted(os.listdir(LESSONS_DIR)):
        info = parse_lesson(LESSONS_DIR / fname)
        if info and "num" in info:
            lessons[info["num"]] = info

    # Build full DAG (only prior citations)
    dag = {}
    for num, info in sorted(lessons.items()):
        prior_cites = [c for c in info["cites"] if c < num and c in lessons]
        dag[num] = prior_cites

    # Classify by era
    era_lessons = defaultdict(set)
    for num, info in lessons.items():
        era = classify_era(info["session"])
        era_lessons[era].add(num)

    # Compute per-era PA kernel
    era_results = {}
    for era in ["early", "mid", "domex", "recent"]:
        nodes = era_lessons.get(era, set())
        if not nodes:
            era_results[era] = {"error": "no lessons", "n_lessons": 0}
            continue
        result = compute_pa_kernel(dag, nodes)
        result["n_lessons"] = len(nodes)
        result["session_range"] = f"S{ERA_BOUNDARIES[era][0]}-S{ERA_BOUNDARIES[era][1]}"
        era_results[era] = result

    # Compute pooled (all known-era lessons)
    all_known = set()
    for era in ["early", "mid", "domex", "recent"]:
        all_known |= era_lessons.get(era, set())
    pooled = compute_pa_kernel(dag, all_known)
    pooled["n_lessons"] = len(all_known)

    # Pre-EAD vs post-EAD split (EAD enforcement at S331)
    pre_ead = era_lessons.get("early", set()) | era_lessons.get("mid", set())
    post_ead = era_lessons.get("domex", set()) | era_lessons.get("recent", set())
    pre_ead_result = compute_pa_kernel(dag, pre_ead)
    pre_ead_result["n_lessons"] = len(pre_ead)
    post_ead_result = compute_pa_kernel(dag, post_ead)
    post_ead_result["n_lessons"] = len(post_ead)

    # γ trend test: is there a monotonic shift?
    gammas = []
    for era in ["early", "mid", "domex", "recent"]:
        g = era_results[era].get("gamma")
        if g is not None:
            gammas.append((era, g))

    gamma_trend = "insufficient data"
    if len(gammas) >= 3:
        g_values = [g for _, g in gammas]
        # Check monotonicity
        diffs = [g_values[i+1] - g_values[i] for i in range(len(g_values)-1)]
        if all(d > 0 for d in diffs):
            gamma_trend = "monotonically increasing"
        elif all(d < 0 for d in diffs):
            gamma_trend = "monotonically decreasing"
        else:
            gamma_trend = "non-monotonic"

    # Permutation test: pre-EAD vs post-EAD γ difference
    pre_g = pre_ead_result.get("gamma")
    post_g = post_ead_result.get("gamma")
    perm_p = None
    if pre_g is not None and post_g is not None:
        observed_diff = post_g - pre_g
        perm_p = permutation_test_gamma(dag, pre_ead, post_ead, observed_diff, n_perm=500)

    # Summary
    print("=== F-SP4: Time-Varying PA Kernel ===\n")
    print(f"Pooled: γ={pooled.get('gamma')}, R²={pooled.get('r_squared')}, "
          f"PA ratio={pooled.get('pa_ratio')}, n={pooled['n_events']} events\n")

    print("--- Per-Era Results ---")
    for era in ["early", "mid", "domex", "recent"]:
        r = era_results[era]
        g = r.get("gamma", "N/A")
        r2 = r.get("r_squared", "N/A")
        pa = r.get("pa_ratio", "N/A")
        rr = r.get("rate_ratio_k1_k0", "N/A")
        n_e = r.get("n_events", 0)
        n_l = r.get("n_lessons", 0)
        print(f"  {era:8s}: γ={g:>7s} R²={r2:>7s} PA_ratio={pa:>6s} "
              f"rate_ratio={rr:>6s} n_events={n_e:4d} n_lessons={n_l:3d}"
              if isinstance(g, str) else
              f"  {era:8s}: γ={g:7.4f} R²={r2:7.4f} PA_ratio={pa if pa is None else pa:>6} "
              f"rate_ratio={rr if rr is None else rr:>6} n_events={n_e:4d} n_lessons={n_l:3d}")

    print(f"\nγ trend: {gamma_trend}")
    print(f"γ values: {', '.join(f'{era}={g:.4f}' for era, g in gammas)}")

    print(f"\n--- Pre-EAD vs Post-EAD ---")
    print(f"  Pre-EAD  (S1-S330):  γ={pre_g}, R²={pre_ead_result.get('r_squared')}, "
          f"PA ratio={pre_ead_result.get('pa_ratio')}, n={pre_ead_result['n_events']}")
    print(f"  Post-EAD (S331+):    γ={post_g}, R²={post_ead_result.get('r_squared')}, "
          f"PA ratio={post_ead_result.get('pa_ratio')}, n={post_ead_result['n_events']}")
    if pre_g is not None and post_g is not None:
        print(f"  Δγ = {post_g - pre_g:+.4f}")
        if perm_p is not None:
            print(f"  Permutation p-value (n=500): {perm_p:.3f} "
                  f"{'(significant at 0.05)' if perm_p < 0.05 else '(not significant)'}")

    # Build experiment JSON
    experiment = {
        "experiment_id": "f-sp4-time-varying-pa-s381",
        "frontier": "F-SP4",
        "session": "S381",
        "date": "2026-03-01",
        "domain": "stochastic-processes",
        "question": "Does the citation PA kernel γ change across protocol eras?",
        "hypothesis": "Time-varying PA reveals era-specific γ shifts. Post-EAD (S331+) "
                      "shows higher PA ratio but similar sublinear γ. R² improves within "
                      "eras (era mixing inflated variance in pooled estimate).",
        "method": f"Split {len(all_known)} lessons into 4 eras by session number. "
                  f"Compute pool-normalized PA kernel per era. Log-log regression for γ. "
                  f"Pre/post EAD permutation test (n=500). Compare PA ratio, rate ratio, "
                  f"and Gini across eras.",
        "era_boundaries": ERA_BOUNDARIES,
        "data": {
            "pooled": {k: v for k, v in pooled.items() if k != "kernel_rates"},
            "per_era": {era: {k: v for k, v in era_results[era].items() if k != "kernel_rates"}
                        for era in ["early", "mid", "domex", "recent"]},
            "pre_ead": {k: v for k, v in pre_ead_result.items() if k != "kernel_rates"},
            "post_ead": {k: v for k, v in post_ead_result.items() if k != "kernel_rates"},
        },
        "results": {
            "gamma_trend": gamma_trend,
            "gamma_values": {era: g for era, g in gammas},
            "ead_delta_gamma": round(post_g - pre_g, 4) if pre_g and post_g else None,
            "ead_permutation_p": perm_p,
            "r_squared_improvement_within_era": None,  # filled below
        },
        "expect": "Time-varying PA reveals era-specific γ shifts. Post-EAD shows "
                  "higher PA ratio. R² improves within eras.",
        "actual": "",  # filled below
        "diff": "",    # filled below
        "outcome": "", # filled below
    }

    # R² comparison
    era_r2 = [era_results[era].get("r_squared") for era in ["early", "mid", "domex", "recent"]
              if era_results[era].get("r_squared") is not None]
    pooled_r2 = pooled.get("r_squared")
    if era_r2 and pooled_r2 is not None:
        mean_era_r2 = sum(era_r2) / len(era_r2)
        experiment["results"]["r_squared_improvement_within_era"] = round(mean_era_r2 - pooled_r2, 4)
        r2_improved = mean_era_r2 > pooled_r2
    else:
        r2_improved = None

    # Build actual/diff/outcome
    actual_parts = []
    actual_parts.append(f"Pooled γ={pooled.get('gamma')}, R²={pooled.get('r_squared')}")
    for era, g in gammas:
        r2 = era_results[era].get("r_squared")
        actual_parts.append(f"{era} γ={g:.4f} R²={r2}")
    actual_parts.append(f"γ trend: {gamma_trend}")
    if pre_g and post_g:
        actual_parts.append(f"Pre-EAD γ={pre_g:.4f}, Post-EAD γ={post_g:.4f}, Δ={post_g-pre_g:+.4f}")
    if perm_p is not None:
        actual_parts.append(f"Permutation p={perm_p:.3f}")
    if r2_improved is not None:
        actual_parts.append(f"Mean era R²={mean_era_r2:.4f} vs pooled R²={pooled_r2} "
                            f"({'improved' if r2_improved else 'not improved'})")
    pa_pre = pre_ead_result.get("pa_ratio")
    pa_post = post_ead_result.get("pa_ratio")
    if pa_pre and pa_post:
        actual_parts.append(f"PA ratio pre-EAD={pa_pre} vs post-EAD={pa_post}")

    experiment["actual"] = ". ".join(actual_parts)

    # Diff
    diff_parts = []
    if gamma_trend != "insufficient data":
        diff_parts.append(f"Predicted era-specific γ shifts — {gamma_trend} trend observed")
    if pa_pre and pa_post:
        if pa_post > pa_pre:
            diff_parts.append(f"Predicted higher post-EAD PA ratio — CONFIRMED ({pa_post} > {pa_pre})")
        else:
            diff_parts.append(f"Predicted higher post-EAD PA ratio — WRONG ({pa_post} <= {pa_pre})")
    if r2_improved is not None:
        if r2_improved:
            diff_parts.append(f"Predicted R² improvement within eras — CONFIRMED (Δ={mean_era_r2-pooled_r2:+.4f})")
        else:
            diff_parts.append(f"Predicted R² improvement within eras — WRONG (Δ={mean_era_r2-pooled_r2:+.4f})")
    if perm_p is not None:
        if perm_p < 0.05:
            diff_parts.append(f"EAD effect on γ is statistically significant (p={perm_p:.3f})")
        else:
            diff_parts.append(f"EAD effect on γ is NOT statistically significant (p={perm_p:.3f})")

    experiment["diff"] = ". ".join(diff_parts)

    # Outcome
    confirmed = 0
    total = 0
    if gamma_trend != "insufficient data":
        total += 1
        if gamma_trend != "non-monotonic":
            confirmed += 1
    if pa_pre and pa_post:
        total += 1
        if pa_post > pa_pre:
            confirmed += 1
    if r2_improved is not None:
        total += 1
        if r2_improved:
            confirmed += 1

    if total == 0:
        experiment["outcome"] = "INSUFFICIENT DATA"
    elif confirmed == total:
        experiment["outcome"] = "CONFIRMED"
    elif confirmed > 0:
        experiment["outcome"] = "PARTIALLY CONFIRMED"
    else:
        experiment["outcome"] = "FALSIFIED"

    # Save experiment JSON
    out_path = REPO / "experiments" / "stochastic-processes" / "f-sp4-time-varying-pa-s381.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(experiment, f, indent=2)
    print(f"\nExperiment saved: {out_path.relative_to(REPO)}")
    print(f"Outcome: {experiment['outcome']}")


if __name__ == "__main__":
    main()
