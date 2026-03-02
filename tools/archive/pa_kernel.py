#!/usr/bin/env python3
"""F-SP4: Measure citation preferential attachment kernel.

Build the citation DAG from Cites: headers. For each citation event,
record the in-degree of the cited lesson at the time it was cited.
Fit three PA models: pure PA, shifted PA, zero-inflated PA.
Compare via BIC. Estimate attachment exponent γ.

Usage:
    python3 tools/pa_kernel.py [--json]
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


def parse_cites(filepath: Path) -> list[int]:
    """Extract L-NNN references from Cites: header."""
    refs = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("Cites:"):
                refs.extend(int(x) for x in re.findall(r"\bL-(\d+)\b", line))
                break
    return refs


def build_citation_dag(lessons_dir: Path) -> dict:
    """Build DAG: for each lesson L_n, record which prior lessons it cites.
    Returns: {lesson_num: [cited_lesson_nums]}"""
    dag = {}
    for fname in sorted(os.listdir(lessons_dir)):
        num = extract_lesson_number(fname)
        if num is None:
            continue
        cites = parse_cites(lessons_dir / fname)
        # Only keep citations to prior lessons (temporal ordering)
        prior_cites = [c for c in cites if c < num]
        dag[num] = prior_cites
    return dag


def measure_attachment_events(dag: dict) -> list[int]:
    """For each citation event, record the in-degree of the target
    at the time it was cited (before this citation is added).

    Process lessons in order. Track in-degree. When L_n cites L_k,
    record degree[k] before incrementing it.
    """
    degree = defaultdict(int)
    attachment_degrees = []

    for src in sorted(dag.keys()):
        for target in dag[src]:
            attachment_degrees.append(degree[target])
            degree[target] += 1

    return attachment_degrees


def fit_pa_models(attachment_degrees: list[int], dag: dict) -> dict:
    """Fit three models to the attachment degree distribution.

    Model 1 - Pure PA: P(cite node with degree k) ∝ k^γ
    Model 2 - Shifted PA: P(cite node with degree k) ∝ (k + a)^γ
    Model 3 - Zero-inflated PA: mixture of uniform (for k=0) and PA (for k≥1)

    Use maximum likelihood estimation via grid search.
    """
    n = len(attachment_degrees)
    if n == 0:
        return {"error": "no attachment events"}

    # Degree distribution at attachment time
    degree_counts = defaultdict(int)
    for d in attachment_degrees:
        degree_counts[d] += 1

    max_deg = max(attachment_degrees)
    k_zero_count = degree_counts[0]
    k_positive = [d for d in attachment_degrees if d > 0]

    results = {}

    # --- Model 1: Pure PA (linear) ---
    # P(k) ∝ k for k≥1, separate probability for k=0
    # This is just checking if attachment rate is proportional to degree
    # Mean degree at attachment
    if k_positive:
        mean_k = sum(k_positive) / len(k_positive)
    else:
        mean_k = 0

    results["mean_degree_at_attachment"] = sum(attachment_degrees) / n
    results["fraction_k0"] = k_zero_count / n
    results["n_events"] = n
    results["n_k0"] = k_zero_count
    results["n_k_positive"] = len(k_positive)
    results["max_degree"] = max_deg

    # --- Non-parametric kernel estimate ---
    # For degree k: rate(k) = attachments_at_k / pool_exposure_at_k
    # Pool exposure = sum over all citation events of (nodes with degree k at that moment)
    degree = defaultdict(int)
    attachments_at_k = defaultdict(int)  # how many times a node with degree k got cited
    exposure_at_k = defaultdict(int)  # total pool-size at degree k across all events

    all_nodes = set()

    for src in sorted(dag.keys()):
        all_nodes.add(src)
        # Pool: all nodes that existed before src
        pool_nodes = [nd for nd in all_nodes if nd < src]

        if dag[src]:  # this lesson has citations
            # Count pool distribution at this moment
            pool_degree_dist = defaultdict(int)
            for nd in pool_nodes:
                pool_degree_dist[degree[nd]] += 1

            # Add exposure for each citation event from this lesson
            n_cites = len(dag[src])
            for k, cnt in pool_degree_dist.items():
                exposure_at_k[k] += cnt * n_cites

            # Record attachments
            for target in dag[src]:
                d = degree[target]
                attachments_at_k[d] += 1
                degree[target] += 1

    # Compute rate(k) = attachments / exposure
    kernel_rates = {}
    for k in sorted(set(list(attachments_at_k.keys()) + list(exposure_at_k.keys()))):
        att = attachments_at_k.get(k, 0)
        exp = exposure_at_k.get(k, 0)
        if exp > 0:
            kernel_rates[k] = att / exp
    results["kernel_rates"] = {str(k): round(v, 6) for k, v in sorted(kernel_rates.items())}

    # Log-log regression of rate vs k for k≥1 (the PA kernel)
    rate_k1_plus = {k: r for k, r in kernel_rates.items() if k >= 1 and r > 0}
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

            results["gamma_kernel"] = round(gamma, 4)
            results["r_squared_kernel"] = round(r_squared, 4)
        else:
            results["gamma_kernel"] = None
            results["r_squared_kernel"] = None
    else:
        results["gamma_kernel"] = None
        results["r_squared_kernel"] = None

    # Rate at k=0 vs k≥1 (zero-inflation diagnostic)
    rate_0 = kernel_rates.get(0, 0)
    rates_pos = [r for k, r in kernel_rates.items() if k >= 1]
    if rates_pos:
        results["rate_k0"] = round(rate_0, 6)
        results["rate_k1_mean"] = round(sum(rates_pos) / len(rates_pos), 6)
        results["rate_ratio_k1_k0"] = round(
            (sum(rates_pos) / len(rates_pos)) / rate_0, 4
        ) if rate_0 > 0 else None

    # --- BIC model comparison ---
    # Model A: Uniform — rate(k) = constant
    # Model B: Linear PA — rate(k) ∝ (k + 1)
    # Model C: Power-law PA — rate(k) ∝ (k + 1)^γ
    # Compute log-likelihood for each using attachment_degrees

    # Model A: uniform
    ll_uniform = 0
    for k, att in attachments_at_k.items():
        exp = exposure_at_k.get(k, 0)
        if exp > 0:
            p = 1.0  # constant rate (all nodes equal)
            # Under uniform: P(cite node i) = 1/N_pool
            # Aggregated: P(cite node at degree k) = pool_k / N_pool
            # This is equivalent to rate = const across all k
    # Use aggregate BIC: compare fit of rate(k) to constant vs power-law
    all_k = sorted(kernel_rates.keys())
    if len(all_k) >= 3:
        rates = [kernel_rates[k] for k in all_k]
        mean_rate = sum(rates) / len(rates)
        # Residual sum of squares for uniform model
        rss_uniform = sum((r - mean_rate) ** 2 for r in rates)
        n_k = len(rates)

        # For power-law model (k+1)^γ: already have gamma from above
        gamma_k = results.get("gamma_kernel")
        if gamma_k is not None:
            intercept_k = results.get("r_squared_kernel", 0)
            # Predict rates
            predicted = []
            for k in all_k:
                if k >= 1:
                    predicted.append(math.exp(
                        results.get("gamma_kernel", 0) * math.log(k)
                        + (sum(math.log(r) for k2, r in kernel_rates.items()
                            if k2 >= 1 and r > 0) / max(1, len(rate_k1_plus))
                           - results.get("gamma_kernel", 0) *
                           sum(math.log(k2) for k2 in rate_k1_plus.keys()) /
                           max(1, len(rate_k1_plus)))
                    ))
                else:
                    predicted.append(rate_0)
            rss_pa = sum((r - p) ** 2 for r, p in zip(rates, predicted))

            # BIC = n * ln(RSS/n) + k * ln(n)
            if rss_uniform > 0 and rss_pa > 0:
                bic_uniform = n_k * math.log(rss_uniform / n_k) + 1 * math.log(n_k)
                bic_pa = n_k * math.log(rss_pa / n_k) + 2 * math.log(n_k)
                results["bic_uniform"] = round(bic_uniform, 2)
                results["bic_pa"] = round(bic_pa, 2)
                results["delta_bic"] = round(bic_uniform - bic_pa, 2)

    # --- Summary statistics ---
    results["degree_distribution_at_attachment"] = dict(sorted(degree_counts.items()))

    # Gini coefficient of attachment degrees (inequality = PA signature)
    sorted_degrees = sorted(attachment_degrees)
    n_d = len(sorted_degrees)
    if n_d > 1:
        cumsum = 0
        weighted_sum = 0
        for i, d in enumerate(sorted_degrees):
            cumsum += d
            weighted_sum += (2 * (i + 1) - n_d - 1) * d
        gini = weighted_sum / (n_d * cumsum) if cumsum > 0 else 0
        results["gini_attachment_degree"] = round(gini, 4)
    else:
        results["gini_attachment_degree"] = 0

    # --- Barabasi-Albert test: compare to random attachment ---
    # Under random: expected attachment degree distribution = degree distribution
    # Under PA: attachments skew toward high-degree nodes
    # Compute ratio: mean(attachment_degree) / mean(all_degrees)
    # If PA: ratio > 1 (citing nodes with above-average degree)
    final_degrees = list(degree.values())
    if final_degrees:
        mean_final = sum(final_degrees) / len(final_degrees)
        mean_attach = sum(attachment_degrees) / len(attachment_degrees) if attachment_degrees else 0
        results["pa_ratio"] = round(mean_attach / mean_final, 4) if mean_final > 0 else None
        results["mean_final_degree"] = round(mean_final, 4)
    else:
        results["pa_ratio"] = None

    return results


def main():
    parser = argparse.ArgumentParser(description="F-SP4: Citation PA kernel measurement")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--lessons-dir", default="memory/lessons", help="Lessons directory")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    lessons_dir = repo_root / args.lessons_dir

    if not lessons_dir.is_dir():
        print(f"ERROR: {lessons_dir} not found", file=sys.stderr)
        sys.exit(1)

    # Build citation DAG
    dag = build_citation_dag(lessons_dir)
    total_lessons = len(dag)
    lessons_with_cites = sum(1 for v in dag.values() if v)
    total_edges = sum(len(v) for v in dag.values())

    # Measure attachment events
    attachment_degrees = measure_attachment_events(dag)

    # Fit PA models
    results = fit_pa_models(attachment_degrees, dag)

    # Add DAG summary
    results["total_lessons"] = total_lessons
    results["lessons_with_cites"] = lessons_with_cites
    results["total_edges"] = total_edges
    results["coverage"] = round(lessons_with_cites / total_lessons, 4) if total_lessons > 0 else 0

    # Degree distribution of final graph
    final_degree = defaultdict(int)
    for src in sorted(dag.keys()):
        for target in dag[src]:
            final_degree[target] += 1

    # In-degree distribution
    in_degrees = [final_degree.get(k, 0) for k in sorted(dag.keys())]
    orphans = sum(1 for d in in_degrees if d == 0)
    results["orphan_fraction"] = round(orphans / len(in_degrees), 4) if in_degrees else 0

    # Top-cited lessons
    top_cited = sorted(final_degree.items(), key=lambda x: -x[1])[:10]
    results["top_10_cited"] = [{"lesson": f"L-{k}", "in_degree": v} for k, v in top_cited]

    # Verdict
    gamma = results.get("gamma_kernel")
    r2 = results.get("r_squared_kernel")
    gini = results.get("gini_attachment_degree")
    pa_ratio = results.get("pa_ratio")
    rate_ratio = results.get("rate_ratio_k1_k0")

    verdict_parts = []
    if gamma is not None:
        if gamma > 0.5:
            verdict_parts.append(f"PA kernel γ={gamma:.2f} (superlinear)")
        elif gamma > 0:
            verdict_parts.append(f"PA kernel γ={gamma:.2f} (sublinear)")
        else:
            verdict_parts.append(f"PA kernel γ={gamma:.2f} (anti-preferential)")
    if r2 is not None:
        verdict_parts.append(f"R²={r2:.3f}")
    if rate_ratio is not None:
        verdict_parts.append(f"rate(k≥1)/rate(k=0)={rate_ratio:.2f}")
    if gini is not None:
        verdict_parts.append(f"Gini={gini:.3f}")
    if pa_ratio is not None:
        if pa_ratio > 1.2:
            verdict_parts.append(f"PA ratio={pa_ratio:.2f} (CONFIRMED)")
        elif pa_ratio > 1.0:
            verdict_parts.append(f"PA ratio={pa_ratio:.2f} (weak PA)")
        else:
            verdict_parts.append(f"PA ratio={pa_ratio:.2f} (no PA)")

    results["verdict"] = "; ".join(verdict_parts) if verdict_parts else "insufficient data"

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"=== F-SP4: Citation Preferential Attachment Kernel ===")
        print(f"DAG: {total_lessons} lessons, {lessons_with_cites} with Cites: headers ({results['coverage']*100:.1f}%)")
        print(f"Edges: {total_edges} total citations")
        print(f"Orphan fraction: {results['orphan_fraction']*100:.1f}%")
        print()
        print(f"--- Attachment events ---")
        print(f"N events: {results['n_events']}")
        print(f"Mean degree at attachment: {results['mean_degree_at_attachment']:.3f}")
        print(f"Fraction k=0: {results['fraction_k0']*100:.1f}%")
        print(f"Max degree at attachment: {results['max_degree']}")
        print()
        if gamma is not None:
            print(f"--- PA kernel (pool-normalized rate, log-log k>=1) ---")
            print(f"γ = {gamma:.4f}")
            print(f"R² = {r2:.4f}")
            print(f"Interpretation: rate(k) ∝ k^{gamma:.2f}")
        print()
        print(f"--- Zero-inflation diagnostic ---")
        print(f"rate(k=0) = {results.get('rate_k0', 'N/A')}")
        print(f"mean rate(k>=1) = {results.get('rate_k1_mean', 'N/A')}")
        print(f"rate ratio k>=1 / k=0 = {rate_ratio}")
        print()
        print(f"--- PA diagnostics ---")
        print(f"Gini coefficient: {gini:.4f}")
        print(f"PA ratio (mean attach / mean final): {pa_ratio}")
        if results.get("bic_uniform") is not None:
            print(f"BIC uniform: {results['bic_uniform']:.2f}")
            print(f"BIC PA: {results['bic_pa']:.2f}")
            print(f"ΔBIC (uniform - PA): {results['delta_bic']:.2f} {'(PA better)' if results['delta_bic'] > 0 else '(uniform better)'}")
        print()
        print(f"--- Non-parametric kernel rates ---")
        kr = results.get("kernel_rates", {})
        for k in sorted(kr.keys(), key=lambda x: int(x)):
            rate = kr[k]
            bar = "█" * int(rate * 5000)
            print(f"  k={int(k):3d}: rate={rate:.6f} {bar}")
        print()
        print(f"--- Top 10 most cited ---")
        for item in results.get("top_10_cited", []):
            print(f"  {item['lesson']}: {item['in_degree']} citations")
        print()
        print(f"--- Degree distribution at attachment ---")
        dist = results.get("degree_distribution_at_attachment", {})
        for k in sorted(dist.keys(), key=int):
            bar = "█" * min(dist[k], 60)
            print(f"  k={k:3d}: {dist[k]:4d} {bar}")
        print()
        print(f"VERDICT: {results['verdict']}")


if __name__ == "__main__":
    main()
