#!/usr/bin/env python3
"""Spectral analysis of swarm citation graph — F-RMT1/F-RMT2.

Computes eigenvalue spectrum of the citation graph adjacency matrix and
compares against random matrix theory predictions (Marchenko-Pastur law,
Wigner surmise, universality class fitting).

Usage:
    python3 tools/spectral_analysis.py                # full report
    python3 tools/spectral_analysis.py --json         # JSON output
    python3 tools/spectral_analysis.py --spikes       # spike count only
"""
import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"
CITE_RE = re.compile(r"\bL-(\d+)\b")


def build_adjacency():
    """Build symmetric adjacency matrix from citation graph."""
    outbound = defaultdict(set)
    lessons = []

    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        lid = f.stem
        lessons.append(lid)
        text = f.read_text(errors="replace")
        refs = set(CITE_RE.findall(text))
        for r in refs:
            ref_id = f"L-{r}"
            if ref_id != lid:
                outbound[lid].add(ref_id)

    # Filter to lessons that exist as files
    lesson_set = set(lessons)
    lid_to_idx = {lid: i for i, lid in enumerate(lessons)}
    N = len(lessons)

    # Build adjacency matrix (symmetric: treat citation as undirected edge)
    A = [[0.0] * N for _ in range(N)]
    edge_count = 0
    for src, targets in outbound.items():
        if src not in lid_to_idx:
            continue
        i = lid_to_idx[src]
        for tgt in targets:
            if tgt in lid_to_idx:
                j = lid_to_idx[tgt]
                if A[i][j] == 0:
                    edge_count += 1
                A[i][j] = 1.0
                A[j][i] = 1.0

    return A, N, edge_count, lessons


def eigenvalues_power_iteration(A, N, num_eigenvalues=30, max_iter=200):
    """Compute top eigenvalues via power iteration with deflation.

    Pure Python — no numpy dependency. Suitable for N<2000.
    """
    eigenvalues = []

    # Work on a mutable copy
    M = [row[:] for row in A]

    for _ in range(min(num_eigenvalues, N)):
        # Power iteration for largest eigenvalue of M
        v = [1.0 / math.sqrt(N)] * N
        eigenval = 0.0

        for _it in range(max_iter):
            # Matrix-vector multiply
            Mv = [0.0] * N
            for i in range(N):
                s = 0.0
                for j in range(N):
                    s += M[i][j] * v[j]
                Mv[i] = s

            # Rayleigh quotient
            new_eigenval = sum(Mv[i] * v[i] for i in range(N))

            # Normalize
            norm = math.sqrt(sum(x * x for x in Mv))
            if norm < 1e-12:
                break
            v = [x / norm for x in Mv]

            if abs(new_eigenval - eigenval) < 1e-8 * max(1, abs(new_eigenval)):
                eigenval = new_eigenval
                break
            eigenval = new_eigenval

        eigenvalues.append(eigenval)

        # Deflate: M = M - eigenval * v * v^T
        for i in range(N):
            for j in range(N):
                M[i][j] -= eigenval * v[i] * v[j]

    return eigenvalues


def marchenko_pastur_bound(N, edge_count):
    """Compute MP upper bound for the symmetrized adjacency matrix.

    For a sparse binary symmetric matrix with average degree d:
    Bulk eigenvalue upper bound ≈ 2√d (from spectral theory of sparse graphs).
    MP classical formula: λ+ = σ² (1 + √γ)² where γ = N/p.
    For adjacency matrices, the relevant bound is 2√(avg_degree).
    """
    avg_degree = 2 * edge_count / N if N > 0 else 0
    # Spectral bound for sparse random graphs: 2*sqrt(d)
    sparse_bound = 2 * math.sqrt(avg_degree) if avg_degree > 0 else 0

    # Classical MP: treat each row as a sample of length N with p features
    # σ² = avg_degree / N (normalized), γ = 1
    sigma_sq = avg_degree / N if N > 0 else 0
    mp_upper = sigma_sq * (1 + math.sqrt(1)) ** 2  # γ=1 for square matrix

    return sparse_bound, mp_upper, avg_degree


def count_spikes(eigenvalues, threshold):
    """Count eigenvalues exceeding threshold (signal spikes)."""
    return sum(1 for ev in eigenvalues if ev > threshold)


def eigenvalue_spacing_stats(eigenvalues):
    """Compute nearest-neighbor spacing distribution statistics.

    Returns mean spacing ratio <r> which discriminates:
    - Poisson (uncorrelated): <r> ≈ 0.386
    - GOE (β=1): <r> ≈ 0.536
    - GUE (β=2): <r> ≈ 0.603
    """
    if len(eigenvalues) < 3:
        return {"mean_r": None, "classification": "INSUFFICIENT_DATA"}

    sorted_ev = sorted(eigenvalues, reverse=True)
    spacings = [sorted_ev[i] - sorted_ev[i + 1] for i in range(len(sorted_ev) - 1)]

    # Spacing ratio r_i = min(s_i, s_{i+1}) / max(s_i, s_{i+1})
    ratios = []
    for i in range(len(spacings) - 1):
        s1, s2 = spacings[i], spacings[i + 1]
        if max(s1, s2) > 1e-12:
            ratios.append(min(s1, s2) / max(s1, s2))

    if not ratios:
        return {"mean_r": None, "classification": "DEGENERATE"}

    mean_r = sum(ratios) / len(ratios)

    # Classification thresholds
    if mean_r < 0.46:
        classification = "POISSON (uncorrelated, β=0)"
    elif mean_r < 0.57:
        classification = "GOE (β=1, time-reversal symmetric)"
    elif mean_r < 0.63:
        classification = "GUE (β=2, broken time-reversal)"
    else:
        classification = "GSE (β=4, symplectic)"

    return {
        "mean_r": round(mean_r, 4),
        "n_ratios": len(ratios),
        "classification": classification,
        "thresholds": {"poisson": 0.386, "GOE": 0.536, "GUE": 0.603},
    }


def main():
    parser = argparse.ArgumentParser(description="RMT spectral analysis of citation graph")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--spikes", action="store_true", help="Spike count only")
    parser.add_argument("--top", type=int, default=30, help="Number of top eigenvalues")
    args = parser.parse_args()

    print("Building adjacency matrix...", file=sys.stderr)
    A, N, edges, lessons = build_adjacency()

    print(f"N={N} lessons, {edges} edges, computing top-{args.top} eigenvalues...",
          file=sys.stderr)

    eigenvalues = eigenvalues_power_iteration(A, N, num_eigenvalues=args.top)

    sparse_bound, mp_upper, avg_degree = marchenko_pastur_bound(N, edges)

    spike_count = count_spikes(eigenvalues, sparse_bound)
    spacing = eigenvalue_spacing_stats(eigenvalues)

    result = {
        "N": N,
        "edges": edges,
        "avg_degree": round(avg_degree, 2),
        "mp_sparse_bound": round(sparse_bound, 2),
        "mp_classical_upper": round(mp_upper, 4),
        "top_eigenvalues": [round(ev, 3) for ev in eigenvalues[:10]],
        "spike_count_above_sparse_bound": spike_count,
        "spike_count_above_2x_bound": count_spikes(eigenvalues, 2 * sparse_bound),
        "spacing_stats": spacing,
        "spectral_gap": round(eigenvalues[0] - eigenvalues[1], 3) if len(eigenvalues) > 1 else None,
        "participation_ratio_estimate": round(eigenvalues[0] / sum(abs(ev) for ev in eigenvalues), 4) if eigenvalues else None,
    }

    if args.spikes:
        print(f"Spikes above sparse bound ({sparse_bound:.2f}): {spike_count}")
        print(f"Spikes above 2x bound ({2*sparse_bound:.2f}): {result['spike_count_above_2x_bound']}")
        return

    if args.json:
        print(json.dumps(result, indent=2))
        return

    # Human-readable report
    print(f"\n=== RMT SPECTRAL ANALYSIS — Citation Graph ===")
    print(f"  Lessons (N): {N}")
    print(f"  Citation edges: {edges}")
    print(f"  Average degree: {avg_degree:.2f}")
    print(f"")
    print(f"--- Marchenko-Pastur Analysis (F-RMT1) ---")
    print(f"  Sparse graph bound (2√d): {sparse_bound:.2f}")
    print(f"  Classical MP upper (σ²(1+√γ)²): {mp_upper:.4f}")
    print(f"  Spikes above sparse bound: {spike_count}")
    print(f"  Spikes above 2x bound: {result['spike_count_above_2x_bound']}")
    print(f"  → Compare to INDEX.md theme count (~20 themes)")
    print(f"")
    print(f"--- Top Eigenvalues ---")
    for i, ev in enumerate(eigenvalues[:10]):
        marker = " ◀ SPIKE" if ev > sparse_bound else ""
        print(f"  λ_{i+1} = {ev:.3f}{marker}")
    print(f"  Spectral gap (λ₁-λ₂): {result['spectral_gap']}")
    print(f"  λ₁ participation: {result['participation_ratio_estimate']:.1%}")
    print(f"")
    print(f"--- Universality Class (F-RMT2) ---")
    print(f"  Mean spacing ratio <r>: {spacing['mean_r']}")
    print(f"  Classification: {spacing['classification']}")
    print(f"  Reference: Poisson=0.386, GOE=0.536, GUE=0.603")
    if spacing.get("n_ratios"):
        print(f"  Sample size: {spacing['n_ratios']} spacing ratios")


if __name__ == "__main__":
    main()
