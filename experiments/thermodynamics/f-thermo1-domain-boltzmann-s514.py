#!/usr/bin/env python3
"""F-THERMO1 successor: Does the Boltzmann constant differ across domains?

L-1412 found H = 0.115·ln(N) + 6.09 globally. If k varies across domains,
knowledge has domain-specific thermodynamics.

Pre-registered prediction: CV(k) > 0.3 across domains with N >= 10 lessons.
Falsification: CV(k) < 0.3 — all domains have the same entropy scaling.
"""

import json
import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path


def shannon_entropy_words(text):
    """Word-level Shannon entropy in bits."""
    words = text.lower().split()
    if not words:
        return 0.0
    counts = Counter(words)
    total = len(words)
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)


def get_lesson_domain_map():
    """Map each lesson to its domain from domain INDEX.md files."""
    domain_lessons = defaultdict(list)
    domains_dir = Path("domains")

    if not domains_dir.exists():
        return domain_lessons

    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        index_file = domain_dir / "INDEX.md"
        if not index_file.exists():
            continue

        domain_name = domain_dir.name
        content = index_file.read_text(errors="replace")

        # Extract lesson references like L-123
        lesson_refs = re.findall(r'L-(\d+)', content)
        for ref in lesson_refs:
            domain_lessons[domain_name].append(f"L-{ref}")

    return domain_lessons


def get_lesson_text(lesson_id):
    """Read a lesson file."""
    # Convert L-123 to file path
    num = lesson_id.split("-")[1]
    path = Path(f"memory/lessons/{lesson_id}.md")
    if path.exists():
        return path.read_text(errors="replace")
    return None


def linear_regression(xs, ys):
    """OLS: returns slope, intercept, R²."""
    n = len(xs)
    if n < 2:
        return 0, 0, 0
    mx = sum(xs) / n
    my = sum(ys) / n
    ss_xy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    ss_xx = sum((x - mx) ** 2 for x in xs)
    ss_yy = sum((y - my) ** 2 for y in ys)
    if ss_xx == 0 or ss_yy == 0:
        return 0, my, 0
    slope = ss_xy / ss_xx
    intercept = my - slope * mx
    r_sq = (ss_xy ** 2) / (ss_xx * ss_yy)
    return slope, intercept, r_sq


def fit_boltzmann(entropies):
    """Fit H = k * ln(N) + b for cumulative lesson entropy.

    Takes list of per-lesson entropies in order added.
    Returns (k, b, r_squared).
    """
    if len(entropies) < 5:
        return None, None, None

    # Compute cumulative corpus entropy at each lesson count
    xs = []  # ln(N)
    ys = []  # H (average per-lesson entropy up to N)

    # Sample at 5 points to match L-1412 methodology
    n = len(entropies)
    sample_points = [max(1, int(n * f)) for f in [0.2, 0.4, 0.6, 0.8, 1.0]]
    sample_points = sorted(set(sample_points))

    for n_lessons in sample_points:
        subset = entropies[:n_lessons]
        avg_h = sum(subset) / len(subset)
        xs.append(math.log(n_lessons))
        ys.append(avg_h)

    if len(xs) < 3:
        return None, None, None

    slope, intercept, r_sq = linear_regression(xs, ys)
    return slope, intercept, r_sq


def main():
    print("=== F-THERMO1 Successor: Domain-Specific Boltzmann Constants ===\n")

    # Get domain -> lesson mapping
    domain_lessons = get_lesson_domain_map()
    print(f"Found {len(domain_lessons)} domains with lesson references\n")

    results = []
    all_ks = []

    for domain in sorted(domain_lessons.keys()):
        lessons = list(set(domain_lessons[domain]))  # deduplicate

        if len(lessons) < 10:
            continue

        # Get entropy for each lesson
        entropies = []
        for lid in sorted(lessons, key=lambda x: int(x.split("-")[1])):
            text = get_lesson_text(lid)
            if text:
                h = shannon_entropy_words(text)
                entropies.append(h)

        if len(entropies) < 10:
            continue

        # Fit Boltzmann: H = k * ln(N) + b
        k, b, r2 = fit_boltzmann(entropies)
        if k is None:
            continue

        # Also compute raw stats
        avg_h = sum(entropies) / len(entropies)
        std_h = (sum((h - avg_h) ** 2 for h in entropies) / len(entropies)) ** 0.5

        # Vocabulary diversity (unique words / total words for the domain)
        all_text = ""
        for lid in sorted(lessons, key=lambda x: int(x.split("-")[1])):
            text = get_lesson_text(lid)
            if text:
                all_text += text + "\n"
        words = all_text.lower().split()
        vocab_diversity = len(set(words)) / len(words) if words else 0

        result = {
            "domain": domain,
            "n_lessons": len(entropies),
            "boltzmann_k": round(k, 4),
            "intercept_b": round(b, 4),
            "r_squared": round(r2, 4),
            "avg_entropy": round(avg_h, 4),
            "std_entropy": round(std_h, 4),
            "vocab_diversity": round(vocab_diversity, 4),
        }
        results.append(result)
        all_ks.append(k)

        print(f"  {domain:30s} N={len(entropies):4d}  k={k:+.4f}  b={b:.3f}  R²={r2:.3f}  H̄={avg_h:.3f}  vocab={vocab_diversity:.3f}")

    if not results:
        print("No domains with sufficient data (>=10 lessons)")
        return

    # Compute CV of k values
    mean_k = sum(all_ks) / len(all_ks)
    std_k = (sum((k - mean_k) ** 2 for k in all_ks) / len(all_ks)) ** 0.5
    cv_k = std_k / abs(mean_k) if mean_k != 0 else float("inf")

    print(f"\n=== Analysis ===")
    print(f"Domains analyzed: {len(results)} (with N >= 10 lessons)")
    print(f"Global k (L-1412): 0.115")
    print(f"Domain k: mean={mean_k:.4f}, std={std_k:.4f}, CV={cv_k:.3f}")
    print(f"k range: [{min(all_ks):.4f}, {max(all_ks):.4f}]")

    # Sort by k
    results_sorted = sorted(results, key=lambda r: r["boltzmann_k"])
    print(f"\nLowest k: {results_sorted[0]['domain']} (k={results_sorted[0]['boltzmann_k']:.4f})")
    print(f"Highest k: {results_sorted[-1]['domain']} (k={results_sorted[-1]['boltzmann_k']:.4f})")

    # Correlation: k vs vocab_diversity
    vocab_divs = [r["vocab_diversity"] for r in results]
    ks = [r["boltzmann_k"] for r in results]
    _, _, r2_kv = linear_regression(vocab_divs, ks)
    print(f"\nCorrelation k vs vocab_diversity: R²={r2_kv:.3f}")

    # Correlation: k vs N
    ns = [r["n_lessons"] for r in results]
    _, _, r2_kn = linear_regression(ns, ks)
    print(f"Correlation k vs N: R²={r2_kn:.3f}")

    # Verdict
    print(f"\n=== Verdict ===")
    if cv_k > 0.3:
        verdict = "SUPPORTED"
        detail = f"CV(k) = {cv_k:.3f} > 0.3. Domains have significantly different entropy scaling constants. Knowledge thermodynamics is domain-specific."
    else:
        verdict = "FALSIFIED"
        detail = f"CV(k) = {cv_k:.3f} < 0.3. Domains share approximately the same entropy scaling. Knowledge thermodynamics is universal."

    # Check if any R² < 0.3 (Boltzmann doesn't fit some domains)
    poor_fit = [r for r in results if r["r_squared"] < 0.3]
    if poor_fit:
        detail += f" Caveat: {len(poor_fit)} domains have R² < 0.3 (Boltzmann model doesn't fit)."

    print(f"{verdict}: {detail}")

    # Save artifact
    artifact = {
        "experiment": "F-THERMO1-domain-boltzmann",
        "session": "S514",
        "date": "2026-03-23",
        "predecessor": "L-1412",
        "prediction": "CV(k) > 0.3 across domains with N >= 10",
        "falsification": "CV(k) < 0.3",
        "global_k": 0.115,
        "domain_k_mean": round(mean_k, 4),
        "domain_k_std": round(std_k, 4),
        "domain_k_cv": round(cv_k, 3),
        "k_range": [round(min(all_ks), 4), round(max(all_ks), 4)],
        "correlation_k_vocab": round(r2_kv, 3),
        "correlation_k_n": round(r2_kn, 3),
        "domains": results,
        "verdict": verdict,
        "detail": detail,
    }

    out_path = Path("experiments/thermodynamics/f-thermo1-domain-boltzmann-s514.json")
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact saved: {out_path}")


if __name__ == "__main__":
    main()
