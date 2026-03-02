#!/usr/bin/env python3
"""
swarm_dependency_map.py — Unified dependency graph for the swarm.

Maps six dependency layers:
  1. Tool→tool (subprocess calls + Python imports)
  2. Lesson→lesson (citation graph)
  3. Frontier→frontier (cross-references between F-XXX IDs)
  4. Domain→domain (via frontier cross-refs)
  5. Lane conflicts (F-GT2: chromatic number for concurrent scheduling)
  6. Cross-layer (tool→frontier, lesson→tool)

Outputs: hub/bottleneck analysis, chromatic number, cross-layer edges.
Produces JSON artifact for experiment tracking.

Usage:
    python3 tools/swarm_dependency_map.py
    python3 tools/swarm_dependency_map.py --layer tools|lessons|frontiers|lanes
    python3 tools/swarm_dependency_map.py --json experiments/graph-theory/output.json
"""
import argparse, json, re, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
LESSONS_DIR = REPO / "memory" / "lessons"
DOMAINS_DIR = REPO / "domains"
GLOBAL_FRONTIER = REPO / "tasks" / "FRONTIER.md"
LANES_FILE = REPO / "tasks" / "SWARM-LANES.md"
LANES_ARCHIVE = REPO / "tasks" / "SWARM-LANES-ARCHIVE.md"

TOOL_REF_RE = re.compile(r"tools/(\w+\.py)")
CITE_RE = re.compile(r"\bL-(\d+)\b")
FRONTIER_RE = re.compile(r"F-([A-Z]+\d+)")
IMPORT_LOCAL_RE = re.compile(r"^from (swarm_io|swarm_state)\b", re.MULTILINE)


def map_tool_deps() -> dict:
    """Map tool→tool dependencies via subprocess references and local imports."""
    graph = {}  # tool_name → set of tool_names it calls
    for p in sorted(TOOLS_DIR.glob("*.py")):
        name = p.stem
        text = p.read_text(errors="replace")
        refs = set()
        for m in TOOL_REF_RE.finditer(text):
            target = m.group(1).replace(".py", "")
            if target != name:  # exclude self-refs
                refs.add(target)
        for m in IMPORT_LOCAL_RE.finditer(text):
            refs.add(m.group(1))
        if refs:
            graph[name] = sorted(refs)
    # Compute metrics
    out_degree = {k: len(v) for k, v in graph.items()}
    in_count = Counter()
    for targets in graph.values():
        for t in targets:
            in_count[t] += 1
    all_tools = set(graph.keys()) | set(in_count.keys())
    return {
        "nodes": len(all_tools),
        "edges": sum(len(v) for v in graph.values()),
        "graph": graph,
        "top_out_degree": sorted(out_degree.items(), key=lambda x: -x[1])[:10],
        "top_in_degree": sorted(in_count.items(), key=lambda x: -x[1])[:10],
        "orphans": sorted(t for t in (set(p.stem for p in TOOLS_DIR.glob("*.py")) - all_tools)),
        "hubs": sorted([t for t, d in in_count.items() if d >= 5], key=lambda t: -in_count[t]),
    }


def map_lesson_deps() -> dict:
    """Map lesson→lesson citation dependencies."""
    existing = set()
    for p in LESSONS_DIR.glob("L-*.md"):
        m = re.match(r"L-(\d+)\.md$", p.name)
        if m:
            existing.add(int(m.group(1)))
    graph = {}
    for num in sorted(existing):
        p = LESSONS_DIR / f"L-{num:03d}.md"
        if not p.exists():
            p = LESSONS_DIR / f"L-{num}.md"
            if not p.exists():
                continue
        text = p.read_text(errors="replace")
        cites = set()
        for m in CITE_RE.finditer(text):
            cited = int(m.group(1))
            if cited != num and cited in existing:
                cites.add(cited)
        if cites:
            graph[num] = sorted(cites)
    in_count = Counter()
    for targets in graph.values():
        for t in targets:
            in_count[t] += 1
    orphans = sorted(n for n in existing if n not in graph and n not in in_count)
    return {
        "nodes": len(existing),
        "edges": sum(len(v) for v in graph.values()),
        "citing_lessons": len(graph),
        "cited_lessons": len(in_count),
        "orphans_count": len(orphans),
        "orphan_rate": round(len(orphans) / max(len(existing), 1), 3),
        "top_cited": sorted(in_count.items(), key=lambda x: -x[1])[:10],
        "top_citers": sorted(((k, len(v)) for k, v in graph.items()), key=lambda x: -x[1])[:10],
        "k_avg": round(sum(len(v) for v in graph.values()) / max(len(existing), 1), 3),
    }


def map_frontier_deps() -> dict:
    """Map frontier→frontier cross-references across all FRONTIER.md files."""
    # Collect all frontiers and their cross-refs
    frontier_files = list(DOMAINS_DIR.glob("*/tasks/FRONTIER.md"))
    if GLOBAL_FRONTIER.exists():
        frontier_files.append(GLOBAL_FRONTIER)

    # Parse: which frontiers are DEFINED vs REFERENCED in each file
    defined = {}    # F-ID → domain
    references = defaultdict(set)  # F-ID → set of F-IDs it references
    domain_of = {}  # F-ID → domain

    for fp in frontier_files:
        if "domains/" in str(fp):
            domain = fp.parent.parent.name
        else:
            domain = "GLOBAL"
        text = fp.read_text(errors="replace")

        # Find defined frontiers (lines starting with "- **F-XXX**:")
        defined_here = set()
        for line in text.split("\n"):
            m = re.match(r"^- \*\*F-([A-Z]+\d+)\*\*", line.strip())
            if m:
                fid = f"F-{m.group(1)}"
                defined_here.add(fid)
                defined[fid] = domain
                domain_of[fid] = domain

        # Find all F-XXX references in each frontier's text block
        current_fid = None
        for line in text.split("\n"):
            m = re.match(r"^- \*\*F-([A-Z]+\d+)\*\*", line.strip())
            if m:
                current_fid = f"F-{m.group(1)}"
                continue
            if current_fid and line.strip().startswith("- **F-"):
                current_fid = None
                continue
            if current_fid:
                for ref in FRONTIER_RE.finditer(line):
                    ref_id = f"F-{ref.group(1)}"
                    if ref_id != current_fid:
                        references[current_fid].add(ref_id)

    # Cross-domain references
    cross_domain = 0
    same_domain = 0
    cross_pairs = []
    for fid, refs in references.items():
        src_domain = domain_of.get(fid, "?")
        for ref_id in refs:
            tgt_domain = domain_of.get(ref_id, "?")
            if src_domain != tgt_domain and src_domain != "?" and tgt_domain != "?":
                cross_domain += 1
                cross_pairs.append((fid, ref_id, src_domain, tgt_domain))
            elif src_domain == tgt_domain:
                same_domain += 1

    total_edges = sum(len(v) for v in references.values())
    implicit_rate = 1.0 - (len(references) / max(len(defined), 1))

    return {
        "total_frontiers": len(defined),
        "with_cross_refs": len(references),
        "total_edges": total_edges,
        "implicit_rate": round(implicit_rate, 3),
        "cross_domain_edges": cross_domain,
        "same_domain_edges": same_domain,
        "cross_domain_pairs": cross_pairs[:20],
        "top_referenced": sorted(
            Counter(r for refs in references.values() for r in refs).items(),
            key=lambda x: -x[1]
        )[:10],
        "isolated": sorted(f for f in defined if f not in references and
                          f not in set(r for refs in references.values() for r in refs)),
    }


def _parse_lane_rows(text: str) -> list:
    """Parse markdown table rows from SWARM-LANES files into lane dicts."""
    lanes = []
    for line in text.split("\n"):
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 13:
            continue
        if cols[1] in ("Date", "---", "") or cols[1].startswith("-"):
            continue
        session_raw = cols[3]
        m = re.search(r"S?(\d+)", session_raw)
        snum = int(m.group(1)) if m else 0
        lanes.append({
            "date": cols[1],
            "id": cols[2],
            "session": snum,
            "scope_key": cols[9],
            "etc": cols[10] if len(cols) > 10 else "",
            "status": cols[11] if len(cols) > 11 else "",
        })
    return lanes


def _extract_focus(etc: str) -> str:
    """Extract focus= value from Etc field."""
    m = re.search(r"focus=([^;]+)", etc)
    return m.group(1).strip() if m else ""


_FALSE_SCOPES = {"close_lane.py", "claude-code+wsl", "wsl", "codex-cli+powershell",
                  "codex-windows+powershell+bash", "master", ""}


def _effective_scope(lane: dict) -> str:
    """Return the real write surface: prefer focus= over Scope-Key, skip false scopes."""
    focus = _extract_focus(lane["etc"])
    sk = lane["scope_key"]
    if sk in _FALSE_SCOPES:
        return focus if focus else ""
    return sk if sk else focus


def _scope_overlaps(l1: dict, l2: dict) -> bool:
    """Check if two lanes have overlapping write surfaces."""
    e1, e2 = _effective_scope(l1), _effective_scope(l2)
    if not e1 or not e2:
        return False
    # Exact match
    if e1 == e2:
        return True
    # Both target global
    if e1 == "global" and e2 == "global":
        return True
    # Same domain directory
    if e1.startswith("domains/") and e2.startswith("domains/"):
        d1 = e1.split("/")[1] if "/" in e1 else ""
        d2 = e2.split("/")[1] if "/" in e2 else ""
        if d1 and d2 and d1 == d2:
            return True
    return False


def _greedy_color(adj: dict) -> dict:
    """Greedy graph coloring by degree (largest-first)."""
    colors = {}
    for node in sorted(adj.keys(), key=lambda n: -len(adj.get(n, set()))):
        used = {colors[nb] for nb in adj.get(node, set()) if nb in colors}
        c = 0
        while c in used:
            c += 1
        colors[node] = c
    # Also color isolated nodes (not in adj)
    return colors


def _connected_components(adj: dict, all_nodes: set) -> list:
    """BFS connected components for an undirected graph."""
    visited = set()
    components = []
    for start in sorted(all_nodes):
        if start in visited:
            continue
        comp = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            comp.add(node)
            for nb in adj.get(node, set()):
                if nb not in visited:
                    queue.append(nb)
        components.append(sorted(comp, key=str))
    return components


def map_lane_conflicts() -> dict:
    """Build SWARM-LANES conflict graph and compute chromatic number (F-GT2).

    Conflict = two lanes in the same session (or <=1 session apart) with
    overlapping scope-keys or focus areas.  Chromatic number = minimum
    parallel independent sessions for safe concurrent execution.
    """
    lanes = []
    for fp in [LANES_FILE, LANES_ARCHIVE]:
        if fp.exists():
            lanes.extend(_parse_lane_rows(fp.read_text(errors="replace")))

    if not lanes:
        return {"error": "No lanes parsed"}

    # Deduplicate: keep latest row per lane ID (append-only log)
    latest = {}
    for lane in lanes:
        lid = lane["id"]
        if lid not in latest or lane["session"] >= latest[lid]["session"]:
            latest[lid] = lane

    active_statuses = {"ACTIVE", "CLAIMED", "BLOCKED", "READY"}
    all_lanes = list(latest.values())
    active_lanes = [l for l in all_lanes if l["status"] in active_statuses]
    merged_lanes = [l for l in all_lanes if l["status"] == "MERGED"]

    # Build conflict graph: concurrent lanes with scope overlap
    # Concurrent = same session or |session_diff| <= 1
    def _build_conflict(lane_list):
        adj = defaultdict(set)
        for i, l1 in enumerate(lane_list):
            for j, l2 in enumerate(lane_list):
                if i >= j:
                    continue
                if l1["id"] == l2["id"]:
                    continue
                if abs(l1["session"] - l2["session"]) <= 1:
                    if _scope_overlaps(l1, l2):
                        adj[l1["id"]].add(l2["id"])
                        adj[l2["id"]].add(l1["id"])
        return adj

    # Active lanes conflict graph
    active_adj = _build_conflict(active_lanes)
    active_colors = _greedy_color(active_adj)
    # Include non-conflicting active lanes as color 0
    for l in active_lanes:
        if l["id"] not in active_colors:
            active_colors[l["id"]] = 0
    active_chi = (max(active_colors.values()) + 1) if active_colors else 0

    # Historical analysis: all merged lanes by session window
    # Group merged lanes into concurrent windows
    session_groups = defaultdict(list)
    for l in merged_lanes:
        session_groups[l["session"]].append(l)

    # Count max concurrent conflicts per session window
    window_sizes = []
    for snum in sorted(session_groups.keys()):
        group = session_groups[snum]
        adj = _build_conflict(group)
        colors = _greedy_color(adj)
        for l in group:
            if l["id"] not in colors:
                colors[l["id"]] = 0
        chi = (max(colors.values()) + 1) if colors else 1
        window_sizes.append({"session": snum, "lanes": len(group), "chi": chi})

    # Overall historical conflict graph
    hist_adj = _build_conflict(merged_lanes)
    hist_all = set(l["id"] for l in merged_lanes)
    hist_components = _connected_components(hist_adj, hist_all)

    # Scope-key frequency
    scope_freq = Counter(l["scope_key"] for l in all_lanes if l["scope_key"])

    return {
        "total_lanes_parsed": len(all_lanes),
        "active_lanes": len(active_lanes),
        "merged_lanes": len(merged_lanes),
        "active_conflict_edges": sum(len(v) for v in active_adj.values()) // 2,
        "active_chromatic_number": active_chi,
        "active_coloring": dict(sorted(active_colors.items())),
        "historical_conflict_edges": sum(len(v) for v in hist_adj.values()) // 2,
        "historical_components": len(hist_components),
        "largest_component": len(hist_components[0]) if hist_components else 0,
        "session_window_chi": sorted(window_sizes, key=lambda x: -x["chi"])[:10],
        "scope_hotspots": scope_freq.most_common(10),
        "max_historical_chi": max((w["chi"] for w in window_sizes), default=0),
        "mean_historical_chi": round(
            sum(w["chi"] for w in window_sizes) / max(len(window_sizes), 1), 2
        ),
    }


def map_cross_layer(tool_data: dict, lesson_data: dict, frontier_data: dict) -> dict:
    """Map cross-layer edges: tools referencing frontiers, lessons referencing tools."""
    tool_to_frontier = defaultdict(set)
    lesson_to_tool = defaultdict(set)

    # Tool → frontier: scan tool files for F-XXX references
    for p in sorted(TOOLS_DIR.glob("*.py")):
        text = p.read_text(errors="replace")
        frontiers = set()
        for m in FRONTIER_RE.finditer(text):
            frontiers.add(f"F-{m.group(1)}")
        if frontiers:
            tool_to_frontier[p.stem] = sorted(frontiers)

    # Lesson → tool: scan lesson files for tools/xxx.py references
    for p in sorted(LESSONS_DIR.glob("L-*.md")):
        text = p.read_text(errors="replace")
        tools = set()
        for m in TOOL_REF_RE.finditer(text):
            tools.add(m.group(1).replace(".py", ""))
        if tools:
            m2 = re.match(r"L-(\d+)\.md$", p.name)
            if m2:
                lesson_to_tool[f"L-{int(m2.group(1))}"] = sorted(tools)

    return {
        "tool_to_frontier_edges": sum(len(v) for v in tool_to_frontier.values()),
        "tools_referencing_frontiers": len(tool_to_frontier),
        "top_tool_frontier_refs": sorted(
            ((k, len(v)) for k, v in tool_to_frontier.items()),
            key=lambda x: -x[1]
        )[:10],
        "lesson_to_tool_edges": sum(len(v) for v in lesson_to_tool.values()),
        "lessons_referencing_tools": len(lesson_to_tool),
        "top_lesson_tool_refs": sorted(
            ((k, len(v)) for k, v in lesson_to_tool.items()),
            key=lambda x: -x[1]
        )[:10],
        "most_referenced_frontiers_by_tools": Counter(
            f for fs in tool_to_frontier.values() for f in fs
        ).most_common(10),
    }


def map_domain_coupling(frontier_data: dict, lesson_data: dict) -> dict:
    """Derive domain→domain coupling from frontier cross-refs."""
    domain_edges = Counter()
    for fid, ref_id, src, tgt in frontier_data.get("cross_domain_pairs", []):
        pair = tuple(sorted([src, tgt]))
        domain_edges[pair] += 1
    return {
        "coupled_domain_pairs": len(domain_edges),
        "top_coupled": sorted(domain_edges.items(), key=lambda x: -x[1])[:10],
    }


def compute_unified(tool_data, lesson_data, frontier_data, cross_layer=None, lane_data=None) -> dict:
    """Cross-layer analysis including cross-layer edges and lane conflicts."""
    total_nodes = tool_data["nodes"] + lesson_data["nodes"] + frontier_data["total_frontiers"]
    total_edges = tool_data["edges"] + lesson_data["edges"] + frontier_data["total_edges"]

    cross_edges = 0
    if cross_layer:
        cross_edges = cross_layer["tool_to_frontier_edges"] + cross_layer["lesson_to_tool_edges"]
        total_edges += cross_edges

    tool_hubs = [h for h in tool_data["hubs"][:5]]
    lesson_hubs = [f"L-{lid}" for lid, _ in lesson_data["top_cited"][:5]]

    result = {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "density": round(total_edges / max(total_nodes * (total_nodes - 1), 1), 6),
        "layer_sizes": {
            "tools": {"nodes": tool_data["nodes"], "edges": tool_data["edges"]},
            "lessons": {"nodes": lesson_data["nodes"], "edges": lesson_data["edges"]},
            "frontiers": {"nodes": frontier_data["total_frontiers"], "edges": frontier_data["total_edges"]},
        },
        "critical_hubs": {
            "tools": tool_hubs,
            "lessons": lesson_hubs,
        },
        "cross_layer_edges": cross_edges,
        "frontier_implicit_rate": frontier_data["implicit_rate"],
    }
    if lane_data and "active_chromatic_number" in lane_data:
        result["lane_chromatic_number"] = lane_data["active_chromatic_number"]
        result["max_safe_parallel_sessions"] = lane_data["active_chromatic_number"]
    return result


def print_report(tool_data, lesson_data, frontier_data, unified, domain_data,
                 cross_layer=None, lane_data=None):
    """Human-readable report."""
    print("=" * 70)
    print("SWARM DEPENDENCY MAP — Unified Graph Analysis")
    print("=" * 70)

    print(f"\n{'Layer':<15} {'Nodes':>8} {'Edges':>8} {'Density':>10}")
    print("-" * 45)
    for layer, d in unified["layer_sizes"].items():
        n, e = d["nodes"], d["edges"]
        dens = e / max(n * (n - 1), 1)
        print(f"{layer:<15} {n:>8} {e:>8} {dens:>10.4f}")
    print("-" * 45)
    print(f"{'TOTAL':<15} {unified['total_nodes']:>8} {unified['total_edges']:>8} {unified['density']:>10.6f}")

    print("\n--- TOOL LAYER ---")
    print(f"  Hubs (in-degree >= 5): {', '.join(tool_data['hubs'][:7])}")
    print(f"  Top callers: {', '.join(f'{t}({d})' for t,d in tool_data['top_out_degree'][:5])}")
    print(f"  Orphans (no deps): {len(tool_data['orphans'])} tools")

    print("\n--- LESSON LAYER ---")
    print(f"  K_avg: {lesson_data['k_avg']}")
    print(f"  Orphan rate: {lesson_data['orphan_rate']:.1%}")
    print(f"  Top cited: {', '.join(f'L-{lid}({c})' for lid,c in lesson_data['top_cited'][:5])}")

    print("\n--- FRONTIER LAYER ---")
    print(f"  Total frontiers: {frontier_data['total_frontiers']}")
    print(f"  With cross-refs: {frontier_data['with_cross_refs']} ({1-frontier_data['implicit_rate']:.1%})")
    print(f"  Implicit (no tracked deps): {frontier_data['implicit_rate']:.1%}")
    print(f"  Cross-domain edges: {frontier_data['cross_domain_edges']}")
    print(f"  Isolated frontiers: {len(frontier_data['isolated'])}")

    if cross_layer:
        print("\n--- CROSS-LAYER EDGES ---")
        print(f"  Tool→frontier: {cross_layer['tool_to_frontier_edges']} edges ({cross_layer['tools_referencing_frontiers']} tools)")
        print(f"  Lesson→tool: {cross_layer['lesson_to_tool_edges']} edges ({cross_layer['lessons_referencing_tools']} lessons)")
        if cross_layer["top_tool_frontier_refs"]:
            print(f"  Top tool→frontier: {', '.join(f'{t}({n})' for t,n in cross_layer['top_tool_frontier_refs'][:5])}")
        if cross_layer["most_referenced_frontiers_by_tools"]:
            print(f"  Most tool-referenced frontiers: {', '.join(f'{f}({n})' for f,n in cross_layer['most_referenced_frontiers_by_tools'][:5])}")

    if lane_data and "active_chromatic_number" in lane_data:
        print("\n--- LANE CONFLICT GRAPH (F-GT2) ---")
        print(f"  Total lanes: {lane_data['total_lanes_parsed']}")
        print(f"  Active lanes: {lane_data['active_lanes']}")
        print(f"  Active conflict edges: {lane_data['active_conflict_edges']}")
        print(f"  Active chromatic number (chi): {lane_data['active_chromatic_number']}")
        print(f"  → Min parallel sessions for safe execution: {lane_data['active_chromatic_number']}")
        if lane_data.get("active_coloring"):
            colors_used = defaultdict(list)
            for lid, c in lane_data["active_coloring"].items():
                colors_used[c].append(lid)
            for c in sorted(colors_used.keys()):
                print(f"    Color {c}: {', '.join(colors_used[c])}")
        print(f"  Historical lanes analyzed: {lane_data['merged_lanes']}")
        print(f"  Historical conflict edges: {lane_data['historical_conflict_edges']}")
        print(f"  Historical components: {lane_data['historical_components']}")
        print(f"  Max historical chi (per session): {lane_data['max_historical_chi']}")
        print(f"  Mean historical chi: {lane_data['mean_historical_chi']}")
        if lane_data.get("scope_hotspots"):
            print(f"  Scope hotspots: {', '.join(f'{s}({n})' for s,n in lane_data['scope_hotspots'][:5])}")

    print("\n--- DOMAIN COUPLING ---")
    if domain_data["top_coupled"]:
        for pair, count in domain_data["top_coupled"][:5]:
            print(f"  {pair[0]} <-> {pair[1]}: {count} edges")
    else:
        print("  No cross-domain frontier references detected")

    print("\n--- BOTTLENECK ANALYSIS ---")
    print(f"  Tool hubs: {unified['critical_hubs']['tools']}")
    print(f"  Lesson hubs: {unified['critical_hubs']['lessons']}")
    xl = unified.get("cross_layer_edges", 0)
    print(f"  Cross-layer edges: {xl}")

    # Actionable findings
    print("\n--- ACTIONABLE FINDINGS ---")
    if frontier_data["implicit_rate"] > 0.7:
        print(f"  [URGENT] {frontier_data['implicit_rate']:.0%} of frontiers have NO dependency tracking")
        print(f"           → Add prerequisite fields to FRONTIER.md format")
    if len(frontier_data["isolated"]) > frontier_data["total_frontiers"] * 0.3:
        print(f"  [WARN] {len(frontier_data['isolated'])} isolated frontiers — no connections")
    if tool_data["top_out_degree"] and tool_data["top_out_degree"][0][1] > 15:
        top = tool_data["top_out_degree"][0]
        print(f"  [WARN] {top[0]} has {top[1]} outgoing deps — fragile hub")
    if lane_data and lane_data.get("active_chromatic_number", 0) > 3:
        print(f"  [WARN] Lane chi={lane_data['active_chromatic_number']} — scope contention among active lanes")


def main():
    ap = argparse.ArgumentParser(description="Unified swarm dependency map")
    ap.add_argument("--layer", choices=["tools", "lessons", "frontiers", "lanes", "all"], default="all")
    ap.add_argument("--json", help="Write JSON artifact to this path")
    args = ap.parse_args()

    results = {}
    if args.layer in ("tools", "all"):
        results["tools"] = map_tool_deps()
    if args.layer in ("lessons", "all"):
        results["lessons"] = map_lesson_deps()
    if args.layer in ("frontiers", "all"):
        results["frontiers"] = map_frontier_deps()
    if args.layer in ("lanes", "all"):
        results["lanes"] = map_lane_conflicts()

    if args.layer == "all":
        results["cross_layer"] = map_cross_layer(results["tools"], results["lessons"], results["frontiers"])
        results["domain_coupling"] = map_domain_coupling(results["frontiers"], results["lessons"])
        results["unified"] = compute_unified(
            results["tools"], results["lessons"], results["frontiers"],
            cross_layer=results["cross_layer"], lane_data=results.get("lanes"),
        )
        print_report(results["tools"], results["lessons"], results["frontiers"],
                    results["unified"], results["domain_coupling"],
                    cross_layer=results["cross_layer"], lane_data=results.get("lanes"))
    else:
        print(json.dumps(results, indent=2, default=str))

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nArtifact written: {args.json}")


if __name__ == "__main__":
    main()
