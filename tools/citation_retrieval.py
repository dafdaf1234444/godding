#!/usr/bin/env python3
"""Citation-graph retrieval tool — F-BRN7 intervention (b).

Given a lesson ID or keyword, find related lessons via citation graph traversal.
Coverage: 86.6% of lessons reachable via giant component (vs 29.5% INDEX pointers).
Zero maintenance cost — edges from Cites: headers are self-updating.

Usage:
    python3 tools/citation_retrieval.py L-601               # 2-hop neighbors
    python3 tools/citation_retrieval.py L-601 --hops 3      # 3-hop neighbors
    python3 tools/citation_retrieval.py --keyword retrieval  # keyword → graph walk
    python3 tools/citation_retrieval.py --stats              # graph statistics
"""
import argparse, re, sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"
CITE_RE = re.compile(r"\bL-(\d+)\b")


def build_graph():
    """Parse all lessons and return adjacency lists + metadata."""
    outbound = defaultdict(set)   # lesson → set of cited lessons
    inbound = defaultdict(set)    # lesson → set of lessons that cite it
    titles = {}                   # lesson → title line

    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        lid = f.stem  # e.g. "L-601"
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        titles[lid] = lines[0].lstrip("# ").strip() if lines else lid

        # Extract citations from Cites: header and body
        for line in lines:
            for m in CITE_RE.finditer(line):
                target = f"L-{m.group(1)}"
                if target != lid:
                    outbound[lid].add(target)
                    inbound[target].add(lid)

    # Filter edges to existing lessons only
    all_ids = set(titles.keys())
    for lid in list(outbound.keys()):
        outbound[lid] = outbound[lid] & all_ids
    for lid in list(inbound.keys()):
        if lid not in all_ids:
            del inbound[lid]
        else:
            inbound[lid] = inbound[lid] & all_ids

    return outbound, inbound, titles


def bfs(start_set, outbound, inbound, max_hops):
    """BFS from start_set, following edges in both directions."""
    visited = {}  # node → hop distance
    queue = deque()
    for s in start_set:
        visited[s] = 0
        queue.append((s, 0))

    while queue:
        node, dist = queue.popleft()
        if dist >= max_hops:
            continue
        neighbors = outbound.get(node, set()) | inbound.get(node, set())
        for nb in neighbors:
            if nb not in visited:
                visited[nb] = dist + 1
                queue.append((nb, dist + 1))

    return visited


def keyword_search(keyword, titles):
    """Find lessons whose title contains the keyword."""
    kw = keyword.lower()
    return [lid for lid, t in titles.items() if kw in t.lower()]


def print_results(visited, titles, start_set, max_hops):
    """Print retrieval results grouped by hop distance."""
    by_hop = defaultdict(list)
    for lid, dist in sorted(visited.items(), key=lambda x: (x[1], x[0])):
        by_hop[dist].append(lid)

    total = len(visited) - len(start_set)
    print(f"\n  Found {total} related lessons within {max_hops} hops\n")

    for hop in range(max_hops + 1):
        nodes = by_hop.get(hop, [])
        if not nodes:
            continue
        label = "Seeds" if hop == 0 else f"Hop {hop}"
        print(f"  --- {label} ({len(nodes)}) ---")
        for lid in nodes[:15]:
            title = titles.get(lid, lid)
            if len(title) > 80:
                title = title[:77] + "..."
            print(f"    {lid}: {title}")
        if len(nodes) > 15:
            print(f"    ... +{len(nodes) - 15} more")
        print()


def print_stats(outbound, inbound, titles):
    """Print citation graph statistics."""
    all_nodes = set(titles.keys())
    n = len(all_nodes)
    edges = sum(len(v) for v in outbound.values())
    zero_out = sum(1 for lid in all_nodes if not outbound.get(lid))
    zero_in = sum(1 for lid in all_nodes if not inbound.get(lid))
    isolated = sum(1 for lid in all_nodes
                   if not outbound.get(lid) and not inbound.get(lid))

    # Giant component via BFS from most-cited node
    top = sorted(inbound.keys(), key=lambda x: len(inbound[x]), reverse=True)
    if top:
        gc = bfs({top[0]}, outbound, inbound, max_hops=999)
    else:
        gc = {}

    print(f"\n  Citation Graph Statistics (N={n})")
    print(f"  {'─' * 40}")
    print(f"  Edges:              {edges}")
    print(f"  Avg out-degree:     {edges / n:.2f}")
    print(f"  Zero outbound:      {zero_out} ({zero_out * 100 / n:.1f}%)")
    print(f"  Zero inbound:       {zero_in} ({zero_in * 100 / n:.1f}%)")
    print(f"  Isolated:           {isolated} ({isolated * 100 / n:.1f}%)")
    print(f"  Giant component:    {len(gc)} ({len(gc) * 100 / n:.1f}%)")
    print()

    # Top-10 most cited
    top10 = sorted(all_nodes, key=lambda x: len(inbound.get(x, set())),
                   reverse=True)[:10]
    print(f"  Top-10 most cited:")
    for lid in top10:
        ic = len(inbound.get(lid, set()))
        title = titles.get(lid, lid)
        if len(title) > 60:
            title = title[:57] + "..."
        print(f"    {lid} ({ic} citations): {title}")
    print()


def main():
    ap = argparse.ArgumentParser(description="Citation-graph retrieval (F-BRN7)")
    ap.add_argument("lesson", nargs="?", help="Lesson ID (e.g. L-601)")
    ap.add_argument("--hops", type=int, default=2, help="Max hops (default 2)")
    ap.add_argument("--keyword", "-k", help="Search by keyword in titles")
    ap.add_argument("--stats", action="store_true", help="Show graph statistics")
    args = ap.parse_args()

    outbound, inbound, titles = build_graph()

    if args.stats:
        print_stats(outbound, inbound, titles)
        return

    seeds = set()
    if args.lesson:
        lid = args.lesson.upper()
        if not lid.startswith("L-"):
            lid = f"L-{lid}"
        if lid not in titles:
            print(f"  Lesson {lid} not found.", file=sys.stderr)
            sys.exit(1)
        seeds.add(lid)

    if args.keyword:
        matches = keyword_search(args.keyword, titles)
        if not matches:
            print(f"  No lessons match keyword '{args.keyword}'", file=sys.stderr)
            sys.exit(1)
        print(f"  Keyword '{args.keyword}' matched {len(matches)} lesson(s)")
        seeds.update(matches)

    if not seeds:
        ap.print_help()
        sys.exit(1)

    visited = bfs(seeds, outbound, inbound, args.hops)
    print_results(visited, titles, seeds, args.hops)


if __name__ == "__main__":
    main()
