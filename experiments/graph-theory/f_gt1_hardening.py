#!/usr/bin/env python3
"""
F-GT1 hardening: scale-free re-measurement at S390.

Prior measurements:
  S306 (N=329): alpha=1.903, orphan=57.8%, K_avg=0.809
  S331 (N=397): orphan=5.3%, giant_component=92.9%, K_avg=1.76

Hardening test: is alpha trajectory converging toward or diverging from
scale-free [2.0, 3.0]? Is the hub-spoke topology stable?
"""
import json, math, re, sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "tools"))
from nk_null_model import parse_citations, in_degrees, gini


def degree_distribution(degs):
    return dict(sorted(Counter(degs).items()))


def mle_alpha(degs, k_min=1):
    """MLE power-law exponent for discrete data (Clauset et al. 2009)."""
    filtered = [d for d in degs if d >= k_min]
    n = len(filtered)
    if n < 5:
        return None, n
    alpha = 1.0 + n / sum(math.log(d / (k_min - 0.5)) for d in filtered)
    return alpha, n


def connected_components(graph, all_nodes):
    """Find connected components in undirected version of graph."""
    adj = {n: set() for n in all_nodes}
    for s in all_nodes:
        for t in graph.get(s, set()):
            if t in adj:
                adj[s].add(t)
                adj[t].add(s)
    visited = set()
    components = []
    for n in all_nodes:
        if n in visited:
            continue
        comp = set()
        stack = [n]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            comp.add(node)
            for nb in adj[node]:
                if nb not in visited:
                    stack.append(nb)
        components.append(comp)
    return components


def main():
    graph = parse_citations()
    nodes = sorted(graph.keys())
    N = len(nodes)
    degs = in_degrees(nodes, graph)
    deg_map = dict(zip(nodes, degs))

    # Basic metrics
    total_edges = sum(len(v) for v in graph.values())
    k_avg = total_edges / N if N > 0 else 0
    orphan_count = sum(1 for d in degs if d == 0)
    orphan_pct = 100.0 * orphan_count / N if N > 0 else 0
    g = gini(degs)
    dist = degree_distribution(degs)

    # Power-law fit
    alpha, n_fit = mle_alpha(degs, k_min=1)

    # Also try k_min=2 for robustness
    alpha_k2, n_fit_k2 = mle_alpha(degs, k_min=2)

    # Top hubs (in-degree)
    sorted_hubs = sorted(deg_map.items(), key=lambda x: -x[1])
    top_15 = [(f"L-{num:03d}", deg) for num, deg in sorted_hubs[:15]]

    # Out-degree hubs
    out_deg = {n: len(graph.get(n, set())) for n in nodes}
    sorted_out = sorted(out_deg.items(), key=lambda x: -x[1])
    top_10_out = [(f"L-{num:03d}", deg) for num, deg in sorted_out[:10]]

    # Connected components
    comps = connected_components(graph, set(nodes))
    comps.sort(key=len, reverse=True)
    giant_size = len(comps[0]) if comps else 0
    giant_pct = 100.0 * giant_size / N if N > 0 else 0
    n_isolates = sum(1 for c in comps if len(c) == 1)

    # Hub stability vs S306/S331
    s306_hubs = {"L-001": 10, "L-304": 7, "L-219": 5, "L-218": 5, "L-251": 5}
    s331_hubs = {"L-001": 23, "L-039": 20, "L-042": 15, "L-044": 14, "L-025": 13}
    hub_stability = {}
    for label, deg in top_15[:5]:
        num = int(label.split("-")[1])
        s306_key = f"L-{num:03d}"
        hub_stability[label] = {
            "s390_in_degree": deg,
            "in_s306_top5": s306_key in s306_hubs,
            "in_s331_top5": s306_key in s331_hubs,
        }

    # Trajectory analysis
    trajectory = {
        "S306": {"N": 329, "alpha": 1.903, "orphan_pct": 57.8, "K_avg": 0.809,
                 "top_hub_indeg": 10},
        "S331": {"N": 397, "alpha": 1.751, "orphan_pct": 5.3, "K_avg": 1.76,
                 "giant_pct": 92.9, "top_hub_indeg": 23},
        "S390": {"N": N, "alpha": round(alpha, 4) if alpha else None,
                 "orphan_pct": round(orphan_pct, 1), "K_avg": round(k_avg, 4),
                 "giant_pct": round(giant_pct, 1),
                 "top_hub_indeg": top_15[0][1] if top_15 else 0},
    }

    # Alpha trend: S306→S331→S390
    if alpha:
        alpha_trend = "diverging_from_scale_free" if alpha < 1.751 else (
            "converging_toward_scale_free" if alpha > 1.903 else "stable_below_threshold"
        )
    else:
        alpha_trend = "insufficient_data"

    # Scale-free verdict
    scale_free = alpha is not None and 2.0 <= alpha <= 3.0
    verdict = {
        "scale_free": scale_free,
        "alpha": round(alpha, 4) if alpha else None,
        "alpha_k2": round(alpha_k2, 4) if alpha_k2 else None,
        "n_fitted_k1": n_fit,
        "n_fitted_k2": n_fit_k2,
        "alpha_trend": alpha_trend,
        "threshold": "[2.0, 3.0]",
    }

    if scale_free:
        verdict["conclusion"] = f"CONFIRMED: alpha={alpha:.3f} within scale-free range"
    elif alpha and alpha < 2.0:
        verdict["conclusion"] = (
            f"NOT SCALE-FREE: alpha={alpha:.3f} < 2.0. "
            f"Hub-spoke topology confirmed (hubs dominate more than classical scale-free). "
            f"Trend: {alpha_trend}."
        )
    else:
        verdict["conclusion"] = "Insufficient data for power-law fit"

    result = {
        "experiment": "F-GT1",
        "title": "F-GT1 hardening: scale-free re-measurement at S390",
        "session": "S390",
        "date": "2026-03-01",
        "domain": "graph-theory",
        "check_mode": "objective",
        "mode": "hardening",
        "prior_waves": ["S306 (exploration)", "S331 (exploration)"],
        "expect": "alpha still <2.0, orphan rate <10%, hub set stable",
        "metrics": {
            "N": N,
            "total_edges": total_edges,
            "K_avg": round(k_avg, 4),
            "orphan_count": orphan_count,
            "orphan_pct": round(orphan_pct, 1),
            "gini": round(g, 4),
            "giant_component_size": giant_size,
            "giant_component_pct": round(giant_pct, 1),
            "n_components": len(comps),
            "n_isolates": n_isolates,
            "degree_distribution": dist,
        },
        "power_law": verdict,
        "top_15_hubs_in": top_15,
        "top_10_hubs_out": top_10_out,
        "hub_stability_vs_prior": hub_stability,
        "trajectory": trajectory,
        "actual": None,  # filled after analysis
        "diff": None,
    }

    # Print summary
    print(f"=== F-GT1 HARDENING — S390 ===")
    print(f"N={N}  edges={total_edges}  K_avg={k_avg:.3f}")
    print(f"Orphan: {orphan_count} ({orphan_pct:.1f}%)")
    print(f"Giant component: {giant_size} ({giant_pct:.1f}%)")
    print(f"Gini: {g:.4f}")
    print(f"Alpha (k_min=1): {alpha:.4f} (n={n_fit})" if alpha else "Alpha: insufficient data")
    print(f"Alpha (k_min=2): {alpha_k2:.4f} (n={n_fit_k2})" if alpha_k2 else "")
    print(f"Scale-free: {verdict['conclusion']}")
    print(f"Alpha trend: {alpha_trend}")
    print(f"\nTop 10 hubs (in-degree):")
    for label, deg in top_15[:10]:
        print(f"  {label}: {deg}")
    print(f"\nTrajectory:")
    for sess, data in trajectory.items():
        print(f"  {sess}: N={data['N']}, alpha={data.get('alpha', '?')}, "
              f"orphan={data.get('orphan_pct', '?')}%, K_avg={data.get('K_avg', '?')}")

    # Write artifact
    out = REPO / "experiments" / "graph-theory" / "f-gt1-hardening-s390.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nArtifact: {out}")
    return result


if __name__ == "__main__":
    main()
