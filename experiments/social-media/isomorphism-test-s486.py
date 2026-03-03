"""
DOMEX-SOC-S486: Test 3 THEORIZED social-media isomorphisms against internal swarm data.

ISO-11 (viral propagation → frontier diffusion): cascade size distribution
ISO-8 (follower graph → node reachability): in-degree power-law fit
ISO-7 (trend detection → frontier emergence): frontier lesson clustering

Uses citation_retrieval.py graph infrastructure.
"""
import json, sys, os, math, re
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))
from citation_retrieval import build_graph

LESSONS_DIR = Path(__file__).resolve().parent.parent.parent / "memory" / "lessons"
FRONTIER_FILE = Path(__file__).resolve().parent.parent.parent / "domains" / "social-media" / "tasks" / "FRONTIER.md"
GLOBAL_FRONTIER = Path(__file__).resolve().parent.parent.parent / "tasks" / "FRONTIER.md"


def compute_in_degrees(inbound):
    """Compute in-degree for all nodes."""
    return {node: len(citers) for node, citers in inbound.items()}


def cascade_sizes(outbound, inbound):
    """BFS from each lesson to find transitive downstream citation count (cascade size)."""
    all_nodes = set(outbound.keys()) | set(inbound.keys())
    cascades = {}
    for node in all_nodes:
        # Forward cascade: who cites this lesson, and who cites them, etc.
        visited = set()
        queue = [node]
        while queue:
            current = queue.pop(0)
            for citer in inbound.get(current, []):
                if citer not in visited:
                    visited.add(citer)
                    queue.append(citer)
        cascades[node] = len(visited)
    return cascades


def test_power_law(degree_counts):
    """Simple power-law test: compute Zipf exponent via log-log regression."""
    # Filter to non-zero values
    vals = sorted([v for v in degree_counts.values() if v > 0], reverse=True)
    if len(vals) < 10:
        return None, None
    # Log-log rank-frequency
    n = len(vals)
    log_ranks = [math.log(i + 1) for i in range(n)]
    log_vals = [math.log(v) for v in vals]
    # Linear regression in log-log space
    mean_x = sum(log_ranks) / n
    mean_y = sum(log_vals) / n
    num = sum((log_ranks[i] - mean_x) * (log_vals[i] - mean_y) for i in range(n))
    den = sum((log_ranks[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return None, None
    slope = num / den
    # R-squared
    ss_res = sum((log_vals[i] - (mean_y + slope * (log_ranks[i] - mean_x))) ** 2 for i in range(n))
    ss_tot = sum((log_vals[i] - mean_y) ** 2 for i in range(n))
    r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return -slope, r_sq  # Zipf alpha, R-squared


def gini(values):
    """Gini coefficient."""
    vals = sorted(values)
    n = len(vals)
    if n == 0 or sum(vals) == 0:
        return 0
    cum = sum((i + 1) * vals[i] for i in range(n))
    return (2 * cum) / (n * sum(vals)) - (n + 1) / n


def frontier_lesson_clustering(outbound, inbound):
    """Test if frontier-linked lessons are more interconnected than random sets."""
    import random
    random.seed(42)

    # Find lessons that reference frontiers in their body text
    frontier_groups = defaultdict(set)
    all_lesson_ids = set()

    for f in LESSONS_DIR.glob("L-*.md"):
        lid = f.stem
        all_lesson_ids.add(lid)
        try:
            text = f.read_text(errors='replace')
        except:
            continue
        # Find frontier references
        for m in re.finditer(r'F-[A-Z]+\d+', text):
            frontier_groups[m.group()].add(lid)

    # Filter to frontiers with ≥5 lessons
    valid_frontiers = {f: ls for f, ls in frontier_groups.items() if len(ls) >= 5}

    if not valid_frontiers:
        return {"error": "No frontiers with ≥5 linked lessons"}

    results = {}
    all_ids = list(all_lesson_ids)

    for frontier, lessons in sorted(valid_frontiers.items())[:10]:  # top 10
        # Count internal edges among frontier lessons
        internal_edges = 0
        for l in lessons:
            for cited in outbound.get(l, []):
                if cited in lessons:
                    internal_edges += 1
        n = len(lessons)
        possible_edges = n * (n - 1)
        density = internal_edges / possible_edges if possible_edges > 0 else 0

        # Random baseline: 100 random sets of same size
        random_densities = []
        for _ in range(100):
            sample = set(random.sample(all_ids, min(n, len(all_ids))))
            rand_edges = 0
            for l in sample:
                for cited in outbound.get(l, []):
                    if cited in sample:
                        rand_edges += 1
            rand_possible = len(sample) * (len(sample) - 1)
            random_densities.append(rand_edges / rand_possible if rand_possible > 0 else 0)

        mean_random = sum(random_densities) / len(random_densities) if random_densities else 0
        lift = density / mean_random if mean_random > 0 else float('inf')

        results[frontier] = {
            "n_lessons": n,
            "internal_edges": internal_edges,
            "density": round(density, 4),
            "random_baseline_density": round(mean_random, 4),
            "lift": round(lift, 2),
            "trend_like": lift > 2.0  # frontier lessons 2x more connected than random
        }

    return results


def main():
    outbound, inbound, titles = build_graph()
    all_nodes = set(outbound.keys()) | set(inbound.keys())

    print(f"Graph: {len(all_nodes)} nodes, {sum(len(v) for v in outbound.values())} edges")

    # --- ISO-8: Power-law in-degree (follower graph analog) ---
    in_deg = compute_in_degrees(inbound)
    alpha, r_sq = test_power_law(in_deg)
    deg_vals = list(in_deg.values())
    g = gini([v for v in deg_vals if v > 0])

    # Degree distribution stats
    nonzero = [v for v in deg_vals if v > 0]
    p50 = sorted(nonzero)[len(nonzero) // 2] if nonzero else 0
    p90 = sorted(nonzero)[int(len(nonzero) * 0.9)] if nonzero else 0
    p99 = sorted(nonzero)[int(len(nonzero) * 0.99)] if nonzero else 0
    top5_share = sum(sorted(nonzero, reverse=True)[:max(1, len(nonzero) // 20)]) / sum(nonzero) if nonzero else 0

    iso8 = {
        "test": "ISO-8: follower graph → node reachability (power-law in-degree)",
        "n_nodes": len(all_nodes),
        "n_with_citations": len(nonzero),
        "zero_inbound_pct": round(100 * (1 - len(nonzero) / len(all_nodes)), 1),
        "zipf_alpha": round(alpha, 3) if alpha else None,
        "r_squared": round(r_sq, 3) if r_sq else None,
        "gini": round(g, 3),
        "p50": p50, "p90": p90, "p99": p99,
        "max": max(deg_vals) if deg_vals else 0,
        "top_5pct_share": round(top5_share, 3),
        "social_media_alpha_range": "1.5-3.5 (Twitter followers)",
        "verdict": None  # set below
    }

    if alpha and alpha < 1.5:
        iso8["verdict"] = "DIFFERS — α < 1.5 (flatter than social media, more hub-dominated)"
    elif alpha and 1.5 <= alpha <= 3.5:
        iso8["verdict"] = "CONFIRMED — α in social media range"
    else:
        iso8["verdict"] = "DIFFERS — α > 3.5 (more uniform than social media)"

    print(f"\nISO-8: α={alpha:.3f}, R²={r_sq:.3f}, Gini={g:.3f}")
    print(f"  → {iso8['verdict']}")

    # --- ISO-11: Viral propagation (cascade sizes) ---
    print("\nComputing cascade sizes (BFS)...")
    cascades = cascade_sizes(outbound, inbound)
    cascade_vals = list(cascades.values())
    c_alpha, c_r_sq = test_power_law({k: v for k, v in cascades.items() if v > 0})
    c_gini = gini([v for v in cascade_vals if v > 0])

    nonzero_c = [v for v in cascade_vals if v > 0]
    c_p50 = sorted(nonzero_c)[len(nonzero_c) // 2] if nonzero_c else 0
    c_p90 = sorted(nonzero_c)[int(len(nonzero_c) * 0.9)] if nonzero_c else 0
    c_max = max(cascade_vals) if cascade_vals else 0

    # "Viral coefficient" — average downstream nodes per lesson
    r0 = sum(cascade_vals) / len(cascade_vals) if cascade_vals else 0

    # Top viral lessons (largest cascades)
    top_viral = sorted(cascades.items(), key=lambda x: -x[1])[:5]

    iso11 = {
        "test": "ISO-11: viral propagation → frontier diffusion (cascade dynamics)",
        "n_lessons": len(cascade_vals),
        "cascades_nonzero": len(nonzero_c),
        "cascade_zipf_alpha": round(c_alpha, 3) if c_alpha else None,
        "cascade_r_squared": round(c_r_sq, 3) if c_r_sq else None,
        "cascade_gini": round(c_gini, 3),
        "cascade_p50": c_p50,
        "cascade_p90": c_p90,
        "cascade_max": c_max,
        "mean_cascade_r0": round(r0, 1),
        "top_5_viral": [{"lesson": k, "cascade_size": v} for k, v in top_viral],
        "social_media_comparison": "viral content: heavy-tailed cascade distribution, R0 > 1",
        "verdict": None
    }

    if c_alpha and c_alpha < 2.0 and c_gini > 0.3:
        iso11["verdict"] = "CONFIRMED — heavy-tailed cascades with hub dominance (viral-like)"
    elif c_gini < 0.2:
        iso11["verdict"] = "FALSIFIED — cascade sizes near-uniform (no viral dynamics)"
    else:
        iso11["verdict"] = "PARTIAL — some heavy tail but weaker than social media virality"

    print(f"\nISO-11: cascade α={c_alpha:.3f}, R²={c_r_sq:.3f}, Gini={c_gini:.3f}, R0={r0:.1f}")
    print(f"  Top viral: {top_viral[0][0]}={top_viral[0][1]}, {top_viral[1][0]}={top_viral[1][1]}")
    print(f"  → {iso11['verdict']}")

    # --- ISO-7: Trend detection → frontier emergence ---
    print("\nTesting frontier lesson clustering (trend emergence)...")
    clustering = frontier_lesson_clustering(outbound, inbound)

    trend_like_count = sum(1 for v in clustering.values() if isinstance(v, dict) and v.get("trend_like"))
    total_tested = sum(1 for v in clustering.values() if isinstance(v, dict) and "trend_like" in v)

    iso7 = {
        "test": "ISO-7: trend detection → frontier emergence (cluster density lift)",
        "frontiers_tested": total_tested,
        "trend_like_count": trend_like_count,
        "trend_like_pct": round(100 * trend_like_count / total_tested, 1) if total_tested > 0 else 0,
        "detail": clustering,
        "social_media_comparison": "trends = temporally clustered posts with above-baseline interconnection",
        "verdict": None
    }

    if total_tested > 0 and trend_like_count / total_tested > 0.5:
        iso7["verdict"] = "CONFIRMED — majority of frontiers show trend-like clustering (>2x lift)"
    elif total_tested > 0 and trend_like_count / total_tested > 0.2:
        iso7["verdict"] = "PARTIAL — some frontiers cluster like trends but not majority"
    else:
        iso7["verdict"] = "FALSIFIED — frontier lessons not more clustered than random"

    print(f"\nISO-7: {trend_like_count}/{total_tested} frontiers trend-like (>2x density lift)")
    print(f"  → {iso7['verdict']}")

    # --- Assemble experiment ---
    result = {
        "lane": "DOMEX-SOC-S486",
        "session": "S486",
        "title": "Social-media isomorphism validation — testing 3 THEORIZED claims against internal citation data",
        "timestamp": "2026-03-03",
        "check_mode": "verification",
        "status": "COMPLETED",
        "expect": "At least 1 of 3 THEORIZED isomorphisms will fail quantitative testing",
        "iso8_follower_graph": iso8,
        "iso11_viral_propagation": iso11,
        "iso7_trend_detection": iso7,
        "summary": {
            "tested": 3,
            "confirmed": sum(1 for x in [iso8, iso11, iso7] if x["verdict"] and "CONFIRMED" in x["verdict"]),
            "partial": sum(1 for x in [iso8, iso11, iso7] if x["verdict"] and "PARTIAL" in x["verdict"]),
            "falsified": sum(1 for x in [iso8, iso11, iso7] if x["verdict"] and "FALSIFIED" in x["verdict"]),
            "differs": sum(1 for x in [iso8, iso11, iso7] if x["verdict"] and "DIFFERS" in x["verdict"]),
        },
        "delta_vs_s402": "S402 measured static topology (Zipf α=0.847, Gini=0.505 at N=780). S486 adds: cascade dynamics (ISO-11), updated topology (N=1127), frontier clustering (ISO-7). Three new falsifiable tests vs one structural measurement.",
        "citations": ["L-306", "L-753", "L-826", "F-SOC3", "ISO-7", "ISO-8", "ISO-11"]
    }

    out_path = Path(__file__).resolve().parent / "isomorphism-validation-s486.json"
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out_path}")

    # Overall
    verdicts = [iso8["verdict"], iso11["verdict"], iso7["verdict"]]
    print(f"\n=== OVERALL: {result['summary']} ===")
    for v in verdicts:
        print(f"  {v}")


if __name__ == "__main__":
    main()
