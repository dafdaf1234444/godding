#!/usr/bin/env python3
"""complexity_measure.py — Operational complexity theory measurements on the swarm.

Measures real complexity-theoretic quantities on the citation graph and uses them
to produce actionable recommendations. Moves complexity from Tier 1 (analogy) to
Tier 2 (measurement) and Tier 3 (control).

Quantities measured:
  1. Percolation threshold — fraction of nodes whose removal fragments the giant component
  2. Clustering coefficient — local transitivity (how cliquey the network is)
  3. Correlation length — average shortest path in giant component
  4. Criticality indicators — distance from critical point (phase transition)
  5. Robustness — targeted vs random attack resilience (scale-free vulnerability)
  6. Small-world coefficient — clustering/path ratio vs random graph

Usage:
    python3 tools/complexity_measure.py                    # full report
    python3 tools/complexity_measure.py --json             # JSON output
    python3 tools/complexity_measure.py --recommend        # actionable recommendations only
    python3 tools/complexity_measure.py --percolation      # percolation analysis only
    python3 tools/complexity_measure.py --save S515        # save experiment artifact

DOMEX-CPLX-S515: Human directive to operationalize complexity theory for swarm.
"""

import argparse
import json
import random
import sys
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cite_parse import parse_all_refs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"


def build_undirected_graph():
    """Build undirected citation graph from lesson files."""
    adj = defaultdict(set)
    titles = {}
    in_degree = defaultdict(int)

    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        lid = f.stem
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        titles[lid] = lines[0].lstrip("# ").strip() if lines else lid

        for target in parse_all_refs(text):
            if target != lid:
                adj[lid].add(target)
                adj[target].add(lid)
                in_degree[target] += 1

    all_ids = set(titles.keys())
    # Filter to existing lessons only
    for lid in list(adj.keys()):
        adj[lid] = adj[lid] & all_ids
    return dict(adj), titles, dict(in_degree), all_ids


def giant_component(adj, nodes):
    """Find the largest connected component. Returns set of node IDs."""
    visited = set()
    largest = set()

    for start in nodes:
        if start in visited or start not in adj:
            continue
        component = set()
        queue = deque([start])
        while queue:
            node = queue.popleft()
            if node in component:
                continue
            component.add(node)
            for neighbor in adj.get(node, set()):
                if neighbor not in component:
                    queue.append(neighbor)
        visited |= component
        if len(component) > len(largest):
            largest = component

    # Include isolated nodes in visited count
    return largest


def avg_shortest_path_sample(adj, nodes, sample_size=200):
    """Estimate average shortest path length by sampling node pairs."""
    node_list = list(nodes)
    if len(node_list) < 2:
        return 0.0

    total_dist = 0
    count = 0
    rng = random.Random(42)

    for _ in range(sample_size):
        src = rng.choice(node_list)
        tgt = rng.choice(node_list)
        if src == tgt:
            continue

        # BFS from src to tgt
        visited = {src}
        queue = deque([(src, 0)])
        found = False
        while queue:
            node, dist = queue.popleft()
            if node == tgt:
                total_dist += dist
                count += 1
                found = True
                break
            for neighbor in adj.get(node, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        # If not found, skip (disconnected pair)

    return total_dist / count if count > 0 else float("inf")


def clustering_coefficient(adj, nodes):
    """Compute average local clustering coefficient."""
    coefficients = []

    for node in nodes:
        neighbors = adj.get(node, set())
        k = len(neighbors)
        if k < 2:
            continue

        # Count edges between neighbors
        triangles = 0
        neighbor_list = list(neighbors)
        for i in range(len(neighbor_list)):
            for j in range(i + 1, len(neighbor_list)):
                if neighbor_list[j] in adj.get(neighbor_list[i], set()):
                    triangles += 1

        possible = k * (k - 1) / 2
        coefficients.append(triangles / possible)

    return sum(coefficients) / len(coefficients) if coefficients else 0.0


def percolation_analysis(adj, nodes, in_degree, steps=20):
    """Measure giant component size as nodes are removed.

    Tests both random removal (resilience) and targeted removal (vulnerability).
    The percolation threshold is the fraction removed where giant component
    drops below 50% of original.
    """
    node_list = list(nodes)
    n = len(node_list)
    gc_original = len(giant_component(adj, nodes))

    # --- Random removal ---
    rng = random.Random(42)
    random_order = list(node_list)
    rng.shuffle(random_order)

    random_curve = []
    random_threshold = 1.0
    for step in range(steps + 1):
        frac = step / steps
        remove_count = int(frac * n)
        remaining = set(node_list) - set(random_order[:remove_count])
        if not remaining:
            random_curve.append((frac, 0.0))
            continue
        # Build subgraph
        sub_adj = {}
        for node in remaining:
            sub_adj[node] = adj.get(node, set()) & remaining
        gc_size = len(giant_component(sub_adj, remaining))
        gc_frac = gc_size / gc_original if gc_original > 0 else 0
        random_curve.append((frac, gc_frac))
        if gc_frac < 0.5 and random_threshold == 1.0:
            random_threshold = frac

    # --- Targeted removal (highest degree first) ---
    degree_order = sorted(node_list, key=lambda x: in_degree.get(x, 0), reverse=True)

    targeted_curve = []
    targeted_threshold = 1.0
    for step in range(steps + 1):
        frac = step / steps
        remove_count = int(frac * n)
        remaining = set(node_list) - set(degree_order[:remove_count])
        if not remaining:
            targeted_curve.append((frac, 0.0))
            continue
        sub_adj = {}
        for node in remaining:
            sub_adj[node] = adj.get(node, set()) & remaining
        gc_size = len(giant_component(sub_adj, remaining))
        gc_frac = gc_size / gc_original if gc_original > 0 else 0
        targeted_curve.append((frac, gc_frac))
        if gc_frac < 0.5 and targeted_threshold == 1.0:
            targeted_threshold = frac

    return {
        "random_threshold": round(random_threshold, 3),
        "targeted_threshold": round(targeted_threshold, 3),
        "vulnerability_ratio": round(random_threshold / targeted_threshold, 2) if targeted_threshold > 0 else float("inf"),
        "random_curve": [(round(f, 2), round(g, 3)) for f, g in random_curve],
        "targeted_curve": [(round(f, 2), round(g, 3)) for f, g in targeted_curve],
    }


def random_graph_properties(n, m, samples=5):
    """Estimate clustering and path length for Erdos-Renyi random graph G(n,m)."""
    rng = random.Random(42)
    avg_cc = 0.0
    avg_pl = 0.0

    for _ in range(samples):
        nodes = list(range(n))
        adj_r = defaultdict(set)
        edges_added = 0
        while edges_added < m:
            a = rng.randint(0, n - 1)
            b = rng.randint(0, n - 1)
            if a != b and b not in adj_r[a]:
                adj_r[a].add(b)
                adj_r[b].add(a)
                edges_added += 1

        adj_dict = dict(adj_r)
        gc = giant_component(adj_dict, set(nodes))
        if len(gc) > 1:
            avg_cc += clustering_coefficient(adj_dict, gc)
            avg_pl += avg_shortest_path_sample(adj_dict, gc, sample_size=100)

    return avg_cc / samples, avg_pl / samples


def degree_distribution(in_degree, nodes):
    """Compute degree distribution statistics."""
    degrees = [in_degree.get(n, 0) for n in nodes]
    degrees.sort(reverse=True)
    n = len(degrees)
    if n == 0:
        return {}

    total = sum(degrees)
    mean = total / n
    max_deg = degrees[0]

    # Gini coefficient
    cumsum = 0
    gini_sum = 0
    for i, d in enumerate(sorted(degrees)):
        cumsum += d
        gini_sum += cumsum
    gini = 1 - 2 * gini_sum / (n * total) if total > 0 else 0

    # Top-5 hub concentration
    top5_share = sum(degrees[:5]) / total if total > 0 else 0

    return {
        "n_nodes": n,
        "n_edges": total,
        "mean_degree": round(mean, 3),
        "max_degree": max_deg,
        "gini": round(gini, 3),
        "top5_hub_share": round(top5_share, 3),
        "top5_hubs": degrees[:5],
        "isolated_nodes": sum(1 for d in degrees if d == 0),
    }


def criticality_assessment(clustering, path_length, percolation, degree_stats):
    """Assess how close the system is to a critical point.

    Near criticality:
    - Correlation length (path length) diverges
    - Susceptibility (component size variance) peaks
    - Power-law degree distribution (no characteristic scale)

    Returns assessment dict with distance-from-criticality estimate.
    """
    indicators = []

    # 1. Scale-free indicator: Gini > 0.5 suggests heavy-tailed degree distribution
    if degree_stats.get("gini", 0) > 0.5:
        indicators.append(("scale_free", True, "Gini > 0.5 — heavy-tailed degree distribution"))
    else:
        indicators.append(("scale_free", False, f"Gini {degree_stats.get('gini', 0):.3f} < 0.5 — not strongly scale-free"))

    # 2. Small-world: high clustering + short paths
    is_small_world = clustering > 0.1 and path_length < 6
    indicators.append(("small_world", is_small_world,
                       f"C={clustering:.3f}, L={path_length:.1f} — {'small-world' if is_small_world else 'not small-world'}"))

    # 3. Percolation vulnerability: targeted/random threshold ratio > 2 = scale-free vulnerability
    vuln = percolation.get("vulnerability_ratio", 1)
    is_vulnerable = vuln > 2
    indicators.append(("hub_vulnerable", is_vulnerable,
                       f"vulnerability ratio {vuln:.1f}x — {'hub-dependent' if is_vulnerable else 'robust'}"))

    # 4. Connectivity: is the network above percolation threshold?
    k_avg = degree_stats.get("mean_degree", 0)
    # Erdos-Renyi percolation threshold: k_avg > 1
    above_percolation = k_avg > 1.0
    indicators.append(("above_percolation", above_percolation,
                       f"k_avg={k_avg:.3f} {'>' if above_percolation else '<'} 1.0 (ER threshold)"))

    # 5. Near criticality: k_avg near 1.0 = near critical point
    distance_from_critical = abs(k_avg - 1.0)
    near_critical = distance_from_critical < 0.5
    indicators.append(("near_critical", near_critical,
                       f"distance from k=1 critical point: {distance_from_critical:.3f}"))

    # Overall assessment
    positive = sum(1 for _, v, _ in indicators if v)
    phase = "CRITICAL" if near_critical else ("ORDERED" if k_avg > 2.0 else "SUPERCRITICAL")

    return {
        "phase": phase,
        "k_avg": round(k_avg, 3),
        "distance_from_critical": round(distance_from_critical, 3),
        "indicators": [(name, val, desc) for name, val, desc in indicators],
        "positive_indicators": positive,
        "total_indicators": len(indicators),
    }


def generate_recommendations(criticality, percolation, clustering, path_length, degree_stats):
    """Generate actionable recommendations from complexity measurements."""
    recs = []

    # Hub vulnerability
    if percolation.get("vulnerability_ratio", 1) > 3:
        recs.append({
            "priority": "HIGH",
            "area": "robustness",
            "recommendation": f"Network is {percolation['vulnerability_ratio']:.1f}x more vulnerable to targeted hub removal than random. "
                             f"Targeted threshold: {percolation['targeted_threshold']:.1%} removal fragments the giant component. "
                             f"Action: increase cross-citations between non-hub lessons to add redundant paths.",
            "mechanism": "percolation_theory",
        })

    # Low clustering
    if clustering < 0.05:
        recs.append({
            "priority": "MEDIUM",
            "area": "knowledge_coherence",
            "recommendation": f"Clustering coefficient {clustering:.3f} is very low — knowledge forms chains, not clusters. "
                             f"Lessons that cite the same hub rarely cite each other. "
                             f"Action: when writing new lessons, cite sibling lessons (same parent), not just the hub.",
            "mechanism": "clustering_coefficient",
        })

    # Long paths
    if path_length > 6:
        recs.append({
            "priority": "MEDIUM",
            "area": "knowledge_access",
            "recommendation": f"Average path length {path_length:.1f} — knowledge is distant. "
                             f"Action: add shortcut citations between distant clusters (small-world wiring).",
            "mechanism": "correlation_length",
        })

    # Phase assessment
    phase = criticality.get("phase", "UNKNOWN")
    if phase == "ORDERED":
        recs.append({
            "priority": "LOW",
            "area": "innovation",
            "recommendation": f"System is in ORDERED phase (k_avg={criticality['k_avg']:.2f} > 2.0). "
                             f"High connectivity suppresses novel combinations. "
                             f"Action: allow more isolated exploration — not every lesson needs to cite existing work.",
            "mechanism": "criticality",
        })
    elif phase == "CRITICAL":
        recs.append({
            "priority": "INFO",
            "area": "operating_point",
            "recommendation": f"System is NEAR CRITICAL (k_avg={criticality['k_avg']:.2f} ≈ 1.0). "
                             f"Maximum information transfer. This is the optimal operating point for innovation.",
            "mechanism": "criticality",
        })

    # Isolation
    isolated = degree_stats.get("isolated_nodes", 0)
    n = degree_stats.get("n_nodes", 1)
    if isolated / n > 0.1:
        recs.append({
            "priority": "MEDIUM",
            "area": "integration",
            "recommendation": f"{isolated} lessons ({isolated/n:.1%}) have zero citations — below percolation threshold locally. "
                             f"Action: run citation amplification on isolated high-Sharpe lessons.",
            "mechanism": "percolation_theory",
        })

    return recs


def main():
    parser = argparse.ArgumentParser(description="Complexity theory measurements on swarm citation graph")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--recommend", action="store_true", help="Recommendations only")
    parser.add_argument("--percolation", action="store_true", help="Percolation analysis only")
    parser.add_argument("--save", metavar="SESSION", help="Save experiment artifact")
    args = parser.parse_args()

    print("Building citation graph...", file=sys.stderr)
    adj, titles, in_degree, all_ids = build_undirected_graph()

    print(f"Graph: {len(all_ids)} nodes, {sum(len(v) for v in adj.values())//2} undirected edges", file=sys.stderr)

    # Giant component
    gc = giant_component(adj, all_ids)
    gc_frac = len(gc) / len(all_ids) if all_ids else 0

    print(f"Giant component: {len(gc)} nodes ({gc_frac:.1%})", file=sys.stderr)

    # Degree distribution
    deg_stats = degree_distribution(in_degree, all_ids)

    # Clustering coefficient (on giant component for efficiency)
    print("Computing clustering coefficient...", file=sys.stderr)
    cc = clustering_coefficient(adj, gc)

    # Average shortest path (sampled)
    print("Estimating average path length...", file=sys.stderr)
    avg_path = avg_shortest_path_sample(adj, gc, sample_size=300)

    # Percolation analysis
    print("Running percolation analysis...", file=sys.stderr)
    perc = percolation_analysis(adj, all_ids, in_degree, steps=20)

    # Small-world comparison
    print("Computing random graph baseline...", file=sys.stderr)
    n_edges = sum(len(v) for v in adj.values()) // 2
    rand_cc, rand_pl = random_graph_properties(len(all_ids), n_edges, samples=3)
    sw_sigma = (cc / rand_cc) / (avg_path / rand_pl) if rand_cc > 0 and rand_pl > 0 else 0

    # Criticality assessment
    crit = criticality_assessment(cc, avg_path, perc, deg_stats)

    # Recommendations
    recs = generate_recommendations(crit, perc, cc, avg_path, deg_stats)

    results = {
        "graph": {
            "n_nodes": len(all_ids),
            "n_edges": n_edges,
            "giant_component_size": len(gc),
            "giant_component_fraction": round(gc_frac, 3),
        },
        "degree_distribution": deg_stats,
        "clustering_coefficient": round(cc, 4),
        "avg_path_length": round(avg_path, 2),
        "small_world": {
            "sigma": round(sw_sigma, 3),
            "is_small_world": sw_sigma > 1.0,
            "random_clustering": round(rand_cc, 4),
            "random_path_length": round(rand_pl, 2),
            "clustering_ratio": round(cc / rand_cc, 2) if rand_cc > 0 else 0,
            "path_ratio": round(avg_path / rand_pl, 2) if rand_pl > 0 else 0,
        },
        "percolation": perc,
        "criticality": crit,
        "recommendations": recs,
    }

    if args.json or args.save:
        output = json.dumps(results, indent=2, default=str)
        if args.save:
            out_path = ROOT / "experiments" / "nk-complexity" / f"complexity-measure-s{args.save}.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output)
            print(f"\nSaved: {out_path}", file=sys.stderr)
        if args.json:
            print(output)
    elif args.recommend:
        print("\n=== COMPLEXITY RECOMMENDATIONS ===\n")
        for r in recs:
            print(f"[{r['priority']}] {r['area']}: {r['recommendation']}")
            print(f"  mechanism: {r['mechanism']}\n")
    elif args.percolation:
        print("\n=== PERCOLATION ANALYSIS ===\n")
        print(f"Random removal threshold:   {perc['random_threshold']:.1%}")
        print(f"Targeted removal threshold: {perc['targeted_threshold']:.1%}")
        print(f"Vulnerability ratio:        {perc['vulnerability_ratio']:.1f}x")
        print(f"\nRandom removal curve (fraction removed → GC fraction):")
        for frac, gc_f in perc["random_curve"]:
            bar = "█" * int(gc_f * 40)
            print(f"  {frac:5.0%} │{bar} {gc_f:.1%}")
        print(f"\nTargeted removal curve:")
        for frac, gc_f in perc["targeted_curve"]:
            bar = "█" * int(gc_f * 40)
            print(f"  {frac:5.0%} │{bar} {gc_f:.1%}")
    else:
        # Full report
        print(f"\n{'='*60}")
        print(f"  COMPLEXITY THEORY MEASUREMENT — SWARM CITATION GRAPH")
        print(f"{'='*60}\n")

        print(f"  Nodes:              {len(all_ids)}")
        print(f"  Edges:              {n_edges}")
        print(f"  Giant component:    {len(gc)} ({gc_frac:.1%})")
        print(f"  Mean degree (k):    {deg_stats.get('mean_degree', 0):.3f}")
        print(f"  Max degree:         {deg_stats.get('max_degree', 0)}")
        print(f"  Gini coefficient:   {deg_stats.get('gini', 0):.3f}")
        print(f"  Hub concentration:  top-5 = {deg_stats.get('top5_hub_share', 0):.1%}")
        print(f"  Isolated nodes:     {deg_stats.get('isolated_nodes', 0)}")

        print(f"\n--- Complexity Measurements ---")
        print(f"  Clustering coeff:   {cc:.4f}")
        print(f"  Avg path length:    {avg_path:.2f}")
        print(f"  Small-world σ:      {sw_sigma:.3f} ({'YES' if sw_sigma > 1 else 'NO'})")
        print(f"    C/C_rand:         {results['small_world']['clustering_ratio']:.2f}x")
        print(f"    L/L_rand:         {results['small_world']['path_ratio']:.2f}x")

        print(f"\n--- Percolation ---")
        print(f"  Random threshold:   {perc['random_threshold']:.1%} removal → GC fragments")
        print(f"  Targeted threshold: {perc['targeted_threshold']:.1%} removal → GC fragments")
        print(f"  Vulnerability:      {perc['vulnerability_ratio']:.1f}x (targeted/random)")

        print(f"\n--- Criticality ---")
        print(f"  Phase:              {crit['phase']}")
        print(f"  k_avg:              {crit['k_avg']:.3f}")
        print(f"  Distance from k=1:  {crit['distance_from_critical']:.3f}")
        for name, val, desc in crit["indicators"]:
            symbol = "✓" if val else "✗"
            print(f"    {symbol} {desc}")

        if recs:
            print(f"\n--- Recommendations ---")
            for r in recs:
                print(f"\n  [{r['priority']}] {r['area']}")
                print(f"    {r['recommendation']}")
                print(f"    mechanism: {r['mechanism']}")

        print()


if __name__ == "__main__":
    main()
