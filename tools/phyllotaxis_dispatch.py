#!/usr/bin/env python3
"""F-PLB4 Phyllotaxis Dispatch — Test golden-angle divergence in UCB1 dispatch.

Hypothesis: UCB1 dispatch approximates golden-angle divergence in domain-attention
space, achieving near-optimal packing (low discrepancy).

Method:
  1. Extract lesson→domain sequence ordered by session.
  2. Map domains to angular positions on a unit circle.
  3. Compute star discrepancy of actual dispatch vs golden-ratio vs random.
  4. Measure angular step distribution and compare to golden angle (137.5° = 0.382).

Cites: L-1436, L-1127, F-PLB4
"""
import json, re, random, math, sys
from collections import defaultdict, Counter
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"
GOLDEN_FRAC = 2 - (1 + 5**0.5) / 2  # ≈0.3820


def extract_dispatch_sequence():
    """Extract (session, domain) pairs from all lessons."""
    sequence = []
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()[:5]
        session = domain = None
        for line in lines:
            m = re.search(r'Session:\s*S(\d+)', line)
            if m:
                session = int(m.group(1))
            m = re.search(r'Domain:\s*(\S+)', line)
            if m:
                domain = m.group(1).strip().split(',')[0].strip()
        if session is not None and domain:
            sequence.append((session, domain))
    sequence.sort()
    return sequence


def star_discrepancy(fractions):
    """Compute star discrepancy of a 1D sequence."""
    n = len(fractions)
    if n == 0:
        return 0.0
    sf = sorted(fractions)
    disc = 0.0
    for i in range(n):
        disc = max(disc, abs(sf[i] - (i + 1) / n), abs(sf[i] - i / n))
    return disc


def angular_analysis(domains_only):
    """Map domain sequence to angular positions and analyze."""
    unique = sorted(set(domains_only))
    n_dom = len(unique)
    idx = {d: i for i, d in enumerate(unique)}
    fractions = [idx[d] / n_dom for d in domains_only]
    n = len(fractions)

    # Steps between consecutive dispatches
    steps = []
    for i in range(1, n):
        step = (fractions[i] - fractions[i - 1]) % 1.0
        steps.append(step)

    # Star discrepancy: actual
    disc_actual = star_discrepancy(fractions)

    # Golden-ratio sequence
    golden_seq = [(i * GOLDEN_FRAC) % 1.0 for i in range(n)]
    disc_golden = star_discrepancy(golden_seq)

    # Random baseline (averaged over 10 runs)
    disc_randoms = []
    for seed in range(10):
        rng = random.Random(seed)
        rseq = [rng.random() for _ in range(n)]
        disc_randoms.append(star_discrepancy(rseq))
    disc_random_mean = mean(disc_randoms)

    # Inter-visit intervals per domain
    last_visit = {}
    intervals = defaultdict(list)
    for i, d in enumerate(domains_only):
        if d in last_visit:
            intervals[d].append(i - last_visit[d])
        last_visit[d] = i

    all_intervals = [iv for ivs in intervals.values() for iv in ivs]

    return {
        "n_dispatches": n,
        "n_domains": n_dom,
        "disc_actual": disc_actual,
        "disc_golden": disc_golden,
        "disc_random_mean": disc_random_mean,
        "packing_vs_golden": disc_actual / disc_golden if disc_golden > 0 else float('inf'),
        "packing_vs_random": disc_actual / disc_random_mean if disc_random_mean > 0 else float('inf'),
        "golden_angle_fraction": GOLDEN_FRAC,
        "step_mean": mean(steps) if steps else 0,
        "step_stdev": stdev(steps) if len(steps) > 1 else 0,
        "steps_near_golden": sum(1 for s in steps if abs(s - GOLDEN_FRAC) < 0.05),
        "steps_near_golden_pct": sum(1 for s in steps if abs(s - GOLDEN_FRAC) < 0.05) / len(steps) if steps else 0,
        "interval_mean": mean(all_intervals) if all_intervals else 0,
        "interval_stdev": stdev(all_intervals) if len(all_intervals) > 1 else 0,
        "interval_cv": stdev(all_intervals) / mean(all_intervals) if all_intervals and mean(all_intervals) > 0 else 0,
        "domain_concentration": {d: c for d, c in Counter(domains_only).most_common(10)},
    }


def main():
    sequence = extract_dispatch_sequence()
    domains_only = [d for _, d in sequence]
    results = angular_analysis(domains_only)

    # Verdict
    golden_approx = results["packing_vs_golden"] < 5.0
    better_than_random = results["disc_actual"] < results["disc_random_mean"]

    results["verdict"] = {
        "golden_approximation": golden_approx,
        "better_than_random": better_than_random,
        "phyllotaxis_confirmed": golden_approx and better_than_random,
    }

    print(f"\n  F-PLB4 Phyllotaxis Dispatch — Golden Angle Analysis")
    print(f"  {'─' * 55}")
    print(f"  Dispatches: {results['n_dispatches']} across {results['n_domains']} domains")
    print(f"")
    print(f"  STAR DISCREPANCY (lower = better packing):")
    print(f"    Actual (UCB1):     {results['disc_actual']:.4f}")
    print(f"    Golden ratio:      {results['disc_golden']:.4f}")
    print(f"    Random (mean/10):  {results['disc_random_mean']:.4f}")
    print(f"    Ratio actual/golden: {results['packing_vs_golden']:.1f}x")
    print(f"    Ratio actual/random: {results['packing_vs_random']:.1f}x")
    print(f"")
    print(f"  ANGULAR STEPS:")
    print(f"    Golden angle: {GOLDEN_FRAC:.4f}")
    print(f"    Mean step:    {results['step_mean']:.4f}")
    print(f"    Steps near golden (±0.05): {results['steps_near_golden']} / {results['n_dispatches'] - 1} = {results['steps_near_golden_pct']:.1%}")
    print(f"")
    print(f"  INTER-VISIT INTERVALS:")
    print(f"    Mean: {results['interval_mean']:.1f} dispatches")
    print(f"    CV:   {results['interval_cv']:.2f} (low CV = regular, phyllotactic)")
    print(f"")
    print(f"  DOMAIN CONCENTRATION (top 10):")
    for d, c in results["domain_concentration"].items():
        pct = c / results["n_dispatches"]
        print(f"    {d:25s}  {c:4d}  ({pct:.1%})")
    print(f"")
    print(f"  VERDICT:")
    if results["verdict"]["phyllotaxis_confirmed"]:
        print(f"    ✓ PHYLLOTAXIS CONFIRMED — UCB1 approximates golden-angle packing")
    else:
        if not golden_approx:
            print(f"    ✗ NOT GOLDEN — actual discrepancy {results['packing_vs_golden']:.0f}x worse than golden ratio")
        if not better_than_random:
            print(f"    ✗ WORSE THAN RANDOM — dispatch concentration dominates packing")
        print(f"    → UCB1 is reward-seeking, not space-filling. Phyllotaxis model FALSIFIED.")
        print(f"    → Root cause: domain concentration (meta={results['domain_concentration'].get('meta', '?')} dispatches)")

    # Save
    full_results = {
        "frontier": "F-PLB4",
        "session": "S539",
        "hypothesis": "UCB1 dispatch approximates golden-angle divergence",
        **results,
    }
    out_path = ROOT / "experiments" / "plant-biology" / "f-plb4-phyllotaxis-dispatch-s539.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(full_results, f, indent=2, default=str)
    print(f"\n  Artifact: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
