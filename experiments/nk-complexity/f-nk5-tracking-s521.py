#!/usr/bin/env python3
"""F-NK5 tracking: S521 measurement at N=1228.

Last tracked: S481 (N=1114). Gap: 114 lessons.
Measures: K_avg, hub dynamics, sinks, PA ratio, compaction survivorship.
"""
import json, math, re, statistics, random
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[2]
LESSONS = ROOT / "memory" / "lessons"

def parse_citation_graph():
    """Build directed citation graph from lesson files."""
    cite_re = re.compile(r'\bL-(\d+)\b')
    session_re = re.compile(r'Session:\s*S?(\d+)', re.IGNORECASE)

    existing = set()
    for p in LESSONS.glob("L-*.md"):
        m = re.match(r'L-(\d+)', p.stem)
        if m:
            existing.add(int(m.group(1)))

    lessons = {}  # lid -> {session, out_citations, has_cites_header}
    edges = []    # (src, dst) directed
    in_degree = Counter()
    out_degree = Counter()

    for p in sorted(LESSONS.glob("L-*.md")):
        m = re.match(r'L-(\d+)', p.stem)
        if not m:
            continue
        lid = int(m.group(1))
        text = p.read_text(errors='replace')

        sm = session_re.search(text)
        session = int(sm.group(1)) if sm else 0

        has_cites = bool(re.search(r'^Cites:', text, re.MULTILINE))

        out = set()
        for cm in cite_re.finditer(text):
            cited = int(cm.group(1))
            if cited != lid and cited in existing:
                out.add(cited)

        lessons[lid] = {
            'session': session,
            'out': out,
            'has_cites': has_cites
        }

        for dst in out:
            edges.append((lid, dst))
            in_degree[dst] += 1
            out_degree[lid] += 1

    return lessons, edges, in_degree, out_degree, existing

def monte_carlo_z(observed, N, edges, trials=200):
    """Monte Carlo z-score: compare observed to random graphs."""
    samples = []
    nodes = list(range(N))
    for _ in range(trials):
        random.seed(_)
        rand_in = Counter()
        for _ in range(len(edges)):
            rand_in[random.choice(nodes)] += 1
        samples.append(max(rand_in.values()) if rand_in else 0)
    mu = statistics.mean(samples)
    sd = statistics.stdev(samples) if len(samples) > 1 else 1
    return (observed - mu) / sd if sd > 0 else 0

def gini_coefficient(values):
    """Compute Gini coefficient of a list of values."""
    if not values:
        return 0
    sorted_v = sorted(values)
    n = len(sorted_v)
    total = sum(sorted_v)
    if total == 0:
        return 0
    cumsum = 0
    weighted_sum = 0
    for i, v in enumerate(sorted_v):
        cumsum += v
        weighted_sum += (i + 1) * v
    return (2 * weighted_sum) / (n * total) - (n + 1) / n

def main():
    lessons, edges, in_degree, out_degree, existing = parse_citation_graph()
    N = len(lessons)

    # Basic metrics
    total_edges = len(edges)
    K_avg = total_edges / N if N > 0 else 0

    # Hub analysis
    K_max_lid = max(in_degree, key=in_degree.get) if in_degree else 0
    K_max = in_degree[K_max_lid] if in_degree else 0

    # Top hubs
    top_hubs = in_degree.most_common(10)

    # Sinks (zero out-degree)
    sinks = [lid for lid in lessons if out_degree[lid] == 0]
    sinks_pct = len(sinks) / N * 100 if N > 0 else 0

    # Orphans (zero in-degree)
    orphans = [lid for lid in lessons if in_degree[lid] == 0]
    orphan_pct = len(orphans) / N * 100 if N > 0 else 0

    # Gini
    all_in = [in_degree.get(lid, 0) for lid in lessons]
    gini = gini_coefficient(all_in)

    # Hub fraction
    hub_fraction = K_max / N if N > 0 else 0
    top3_sum = sum(c for _, c in top_hubs[:3])
    top3_fraction = top3_sum / N if N > 0 else 0

    # Monte Carlo z-scores
    hub_z = monte_carlo_z(K_max, N, edges, trials=200)

    # Dominance ratio (L-601 vs #2)
    if len(top_hubs) >= 2:
        dom_ratio = top_hubs[0][1] / top_hubs[1][1]
    else:
        dom_ratio = float('inf')

    # Edge decomposition: old (<=S481/L-1224 boundary) vs new
    # S481 was at N=1114, so approximate old = L-1..L-1224 (or whatever existed)
    # More precise: lessons with id <= 1224 that still exist
    old_boundary = 1224  # approximate last lesson at S481
    old_lids = {lid for lid in lessons if lid <= old_boundary}
    new_lids = {lid for lid in lessons if lid > old_boundary}

    old_to_old = sum(1 for s, d in edges if s in old_lids and d in old_lids)
    old_to_new = sum(1 for s, d in edges if s in old_lids and d in new_lids)
    new_to_old = sum(1 for s, d in edges if s in new_lids and d in old_lids)
    new_to_new = sum(1 for s, d in edges if s in new_lids and d in new_lids)

    avg_degree_new = (sum(out_degree[lid] for lid in new_lids) / len(new_lids)) if new_lids else 0
    avg_degree_old = (sum(out_degree[lid] for lid in old_lids) / len(old_lids)) if old_lids else 0

    # Cites header rate
    cites_rate_new = sum(1 for lid in new_lids if lessons[lid]['has_cites']) / len(new_lids) if new_lids else 0
    cites_rate_old = sum(1 for lid in old_lids if lessons[lid]['has_cites']) / len(old_lids) if old_lids else 0

    # PA ratio: K_max growth rate vs N growth rate
    # S481: K_max=327, N=1114. Now: K_max=K_max, N=N
    pa_raw = (K_max / 327) / (N / 1114) if N > 0 else 0

    # Compaction effect: count how many old lessons were removed since S481
    # S481 had 1114 lessons. Count how many of L-1..L-1224 no longer exist.
    # old_boundary covers potential range; count existing vs expected
    expected_old_count = 1114  # approximate count at S481
    actual_old_count = len(old_lids)
    removed_count = max(0, expected_old_count - actual_old_count)

    # Rate calculations
    delta_N = N - 1114
    delta_K = K_avg - 3.2253
    rate = delta_K / delta_N if delta_N > 0 else 0

    # Asymptote progress (target ~4.5 from S396 model)
    asymptote_pct = K_avg / 4.5 * 100

    # L-601 specific metrics
    L601_in = in_degree.get(601, 0)
    L601_cite_rate_new = sum(1 for lid in new_lids if 601 in lessons[lid]['out']) / len(new_lids) if new_lids else 0
    L601_cite_rate_old = sum(1 for lid in old_lids if 601 in lessons[lid]['out']) / len(old_lids) if old_lids else 0

    result = {
        "experiment": "DOMEX-NK-S521",
        "frontier": "F-NK5",
        "session": "S521",
        "domain": "nk-complexity",
        "date": "2026-03-23",
        "level": "L2",
        "mode": "exploration",
        "expect": "K_avg 3.3-3.5 (compaction-corrected). Hub L-601 >350 in-degree. Sinks stable 24-26%. PA ratio continues decelerating toward 1.0x.",
        "actual": {
            "N": N,
            "edges_unique": total_edges,
            "K_avg": round(K_avg, 4),
            "K_max_inbound": K_max,
            "K_max_lesson": f"L-{K_max_lid}",
            "top_hubs": [{"lesson": f"L-{lid}", "in_degree": deg} for lid, deg in top_hubs[:5]],
            "sinks_pct": round(sinks_pct, 1),
            "orphan_pct": round(orphan_pct, 1),
            "gini": round(gini, 3),
            "hub_z_mc200": round(hub_z, 1),
            "hub_fraction": round(hub_fraction, 3),
            "top3_hub_fraction": round(top3_fraction, 3),
            "dominance_ratio": round(dom_ratio, 1),
            "edge_decomposition": {
                "old_to_old": old_to_old,
                "old_to_new": old_to_new,
                "new_to_old": new_to_old,
                "new_to_new": new_to_new,
                "old_lessons": len(old_lids),
                "new_lessons": len(new_lids),
                "avg_degree_new": round(avg_degree_new, 2),
                "avg_degree_old": round(avg_degree_old, 2),
                "removed_since_s481": removed_count
            },
            "pa_ratio_raw": round(pa_raw, 2),
            "rate_per_lesson": round(rate, 6),
            "asymptote_pct": round(asymptote_pct, 1),
            "cites_header_rate_new": round(cites_rate_new, 3),
            "cites_header_rate_old": round(cites_rate_old, 3),
            "L601_inbound": L601_in,
            "L601_cite_rate_new": round(L601_cite_rate_new, 3),
            "L601_cite_rate_old": round(L601_cite_rate_old, 3),
            "delta_N": delta_N,
            "delta_K_avg": round(delta_K, 4),
            "prev_K_avg_s481": 3.2253,
            "prev_N_s481": 1114,
            "prev_K_max_s481": 327
        },
        "diff": "TBD",
        "effect_size": "TBD",
        "falsification_criteria": "FALSIFIED if: (1) K_avg outside 3.3-3.5 range, (2) PA ratio increases (>1.38), (3) L-601 hub fraction >35% (monopoly), (4) sinks >30% (fragmentation).",
        "self_apply": "Citation network measurement IS the swarm knowing itself — K_avg trajectory directly measures integration health. This measurement will create L-601 citations, feeding the hub attractor.",
        "cites": ["L-601", "L-613", "L-1012", "L-912", "L-1224"]
    }

    # Print summary
    print(f"=== F-NK5 Tracking S521 (N={N}) ===")
    print(f"K_avg: {K_avg:.4f} (prev 3.2253, delta {delta_K:+.4f}, rate {rate:.6f}/L)")
    print(f"K_max: L-{K_max_lid} = {K_max} in-degree (prev 327)")
    print(f"Sinks: {sinks_pct:.1f}% (prev 24.9%)")
    print(f"Orphans: {orphan_pct:.1f}%")
    print(f"Gini: {gini:.3f} (prev 0.647)")
    print(f"Hub z (MC200): {hub_z:.1f} (prev 341.4)")
    print(f"Hub fraction: {hub_fraction:.3f} (prev 0.294)")
    print(f"Top-3 fraction: {top3_fraction:.3f} (prev 0.117, safe <0.200)")
    print(f"Dominance ratio: {dom_ratio:.1f}x (prev 6.8x)")
    print(f"PA ratio (raw): {pa_raw:.2f}x (prev corrected 1.38x)")
    print(f"Asymptote: {asymptote_pct:.1f}% of 4.5 target")
    print(f"\nEdge decomposition (old <= L-{old_boundary}):")
    print(f"  old→old: {old_to_old}, old→new: {old_to_new}")
    print(f"  new→old: {new_to_old}, new→new: {new_to_new}")
    print(f"  Avg degree old: {avg_degree_old:.2f}, new: {avg_degree_new:.2f}")
    print(f"  Removed since S481: {removed_count}")
    print(f"\nL-601: {L601_in} inbound, cite rate new={L601_cite_rate_new:.3f} old={L601_cite_rate_old:.3f}")
    print(f"\nTop 5 hubs:")
    for lid, deg in top_hubs[:5]:
        print(f"  L-{lid}: {deg}")

    return result

if __name__ == "__main__":
    result = main()
    out_path = Path(__file__).with_suffix('.json')
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=4)
    print(f"\nSaved to {out_path}")
