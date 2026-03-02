#!/usr/bin/env python3
"""F-CRY1 Merkle tree formalization: model compaction as stateful hash tree.

Tests whether SUPERSEDED chains + citation DAG form a tree structure
with measurable properties that predict compaction regime behavior.
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

LESSON_DIR = Path("memory/lessons")
ARCHIVE_DIR = Path("memory/lessons/archive")
SESSION_LOG = Path("memory/SESSION-LOG.md")
PRINCIPLES = Path("beliefs/PRINCIPLES.md")


def parse_lessons():
    """Extract metadata from all lessons."""
    lessons = {}
    for d in [LESSON_DIR, ARCHIVE_DIR]:
        if not d.exists():
            continue
        for f in d.glob("L-*.md"):
            lid = f.stem  # e.g. "L-012"
            content = f.read_text(errors="replace")
            # Extract session
            sess_match = re.search(r"session:\s*S?(\d+)", content)
            session = int(sess_match.group(1)) if sess_match else None
            # Extract domain
            dom_match = re.search(r"domain:\s*(\S+)", content)
            domain = dom_match.group(1).strip() if dom_match else None
            # Extract Cites:
            cites = []
            cite_match = re.search(r"^Cites:\s*(.+)$", content, re.MULTILINE)
            if cite_match:
                cites = re.findall(r"L-(\d+)", cite_match.group(1))
                cites = [f"L-{c}" for c in cites]
            # Check SUPERSEDED status
            is_superseded = bool(re.search(r"\*\*SUPERSEDED\*\*|<!-- SUPERSEDED", content, re.IGNORECASE))
            # Find what superseded it
            superseded_by = []
            by_match = re.search(r"SUPERSEDED BY (L-\d+)", content, re.IGNORECASE)
            if by_match:
                superseded_by.append(by_match.group(1))
            by_match2 = re.search(r"SUPERSEDED by (L-\d+)", content, re.IGNORECASE)
            if by_match2:
                superseded_by.append(by_match2.group(1))
            # Find if superseded by principle(s) — can have multiple P-NNN
            p_matches = re.findall(r"(?:SUPERSEDED\*\* by|SUPERSEDED by)\s+([^.;\n]+)", content)
            for pm in p_matches:
                for p_id in re.findall(r"P-\d+", pm):
                    superseded_by.append(p_id)
            # Body L-NNN references for broader citation graph
            body_cites = re.findall(r"\bL-(\d+)\b", content)
            body_cites = list(set(f"L-{c}" for c in body_cites if f"L-{c}" != lid))
            # Line count
            lines = len(content.strip().split("\n"))
            lessons[lid] = {
                "id": lid,
                "session": session,
                "domain": domain,
                "cites": cites,
                "body_cites": body_cites,
                "is_superseded": is_superseded,
                "superseded_by": list(set(superseded_by)),
                "lines": lines,
                "archived": str(d) == str(ARCHIVE_DIR),
            }
    return lessons


def build_superseded_dag(lessons):
    """Build DAG from SUPERSEDED relationships (L→L and L→P)."""
    edges = []  # (old, new) - old superseded by new
    l_to_l = []
    l_to_p = []
    for lid, info in lessons.items():
        for target in info["superseded_by"]:
            edges.append((lid, target))
            if target.startswith("L-"):
                l_to_l.append((lid, target))
            elif target.startswith("P-"):
                l_to_p.append((lid, target))
    return edges, l_to_l, l_to_p


def build_citation_dag(lessons):
    """Build citation DAG from Cites: headers."""
    edges = []
    for lid, info in lessons.items():
        for cited in info["cites"]:
            if cited in lessons:
                edges.append((lid, cited))
    return edges


def compute_dag_properties(edges, nodes):
    """Compute graph properties of a DAG."""
    # In-degree and out-degree
    in_deg = defaultdict(int)
    out_deg = defaultdict(int)
    children = defaultdict(list)
    parents = defaultdict(list)
    for src, dst in edges:
        out_deg[src] += 1
        in_deg[dst] += 1
        children[src].append(dst)
        parents[dst].append(src)

    # Find roots (no incoming edges) and leaves (no outgoing edges)
    all_nodes = set()
    for s, d in edges:
        all_nodes.add(s)
        all_nodes.add(d)
    roots = [n for n in all_nodes if in_deg[n] == 0]
    leaves = [n for n in all_nodes if out_deg[n] == 0]

    # Compute depth (longest path from any root)
    depth = {}
    def get_depth(node, visited=None):
        if visited is None:
            visited = set()
        if node in depth:
            return depth[node]
        if node in visited:
            return 0  # cycle protection
        visited.add(node)
        if in_deg[node] == 0:
            depth[node] = 0
            return 0
        d = max(get_depth(p, visited) for p in parents[node]) + 1
        depth[node] = d
        return d

    for n in all_nodes:
        get_depth(n)

    # Connected components
    adj = defaultdict(set)
    for s, d in edges:
        adj[s].add(d)
        adj[d].add(s)
    visited = set()
    components = []
    def dfs(node, comp):
        if node in visited:
            return
        visited.add(node)
        comp.append(node)
        for neighbor in adj[node]:
            dfs(neighbor, comp)
    for n in all_nodes:
        if n not in visited:
            comp = []
            dfs(n, comp)
            components.append(comp)

    max_depth = max(depth.values()) if depth else 0
    mean_depth = sum(depth.values()) / len(depth) if depth else 0
    in_degrees = [in_deg[n] for n in all_nodes]
    out_degrees = [out_deg[n] for n in all_nodes]
    mean_in = sum(in_degrees) / len(in_degrees) if in_degrees else 0
    mean_out = sum(out_degrees) / len(out_degrees) if out_degrees else 0
    max_fan_out = max(out_degrees) if out_degrees else 0
    max_fan_in = max(in_degrees) if in_degrees else 0

    return {
        "n_nodes": len(all_nodes),
        "n_edges": len(edges),
        "n_roots": len(roots),
        "n_leaves": len(leaves),
        "n_components": len(components),
        "component_sizes": sorted([len(c) for c in components], reverse=True),
        "max_depth": max_depth,
        "mean_depth": round(mean_depth, 2),
        "mean_fan_in": round(mean_in, 2),
        "mean_fan_out": round(mean_out, 2),
        "max_fan_out": max_fan_out,
        "max_fan_in": max_fan_in,
        "depth_distribution": dict(sorted(
            {d: sum(1 for v in depth.values() if v == d) for d in set(depth.values())}.items()
        )),
    }


def find_compaction_events(lessons):
    """Identify sessions where SUPERSEDED events occurred."""
    events = defaultdict(list)
    for lid, info in lessons.items():
        if info["is_superseded"] and info["session"]:
            events[info["session"]].append(lid)
    return dict(sorted(events.items()))


def merkle_tree_properties(superseded_edges, citation_edges, lessons):
    """Compute Merkle-tree-specific properties.

    Merkle tree analogy:
    - Leaves = raw lessons (never superseded, no SUPERSEDED children)
    - Internal nodes = lessons that supersede others (compacted representations)
    - Root = the most distilled/canonical representation
    - Hash chain = SUPERSEDED → successor chain
    - Tree branch = citation subtree feeding into a superseding lesson
    """
    # Build the full knowledge DAG (citations + SUPERSEDED)
    all_edges = set()
    for s, d in citation_edges:
        all_edges.add((s, d, "cites"))
    for old, new in superseded_edges:
        all_edges.add((old, new, "superseded"))

    # Classify nodes
    superseded_sources = set(e[0] for e in superseded_edges)
    superseded_targets = set(e[1] for e in superseded_edges)

    internal_nodes = superseded_targets  # nodes that absorb others
    leaf_nodes = set(lessons.keys()) - superseded_sources - superseded_targets
    consumed_nodes = superseded_sources  # nodes absorbed into others

    # Chain analysis: follow SUPERSEDED chains
    succ = defaultdict(list)
    for old, new in superseded_edges:
        succ[old].append(new)
    pred = defaultdict(list)
    for old, new in superseded_edges:
        pred[new].append(old)

    # Find chain lengths (longest path through SUPERSEDED edges)
    chains = []
    chain_starts = [n for n in superseded_sources if n not in superseded_targets]
    for start in chain_starts:
        chain = [start]
        current = start
        visited = {start}
        while current in succ:
            nexts = [n for n in succ[current] if n not in visited]
            if not nexts:
                break
            current = nexts[0]
            visited.add(current)
            chain.append(current)
        chains.append(chain)

    # For lessons that supersede multiple others: measure "fan-in compaction ratio"
    fan_in_ratios = {}
    for target in superseded_targets:
        sources = pred[target]
        if sources:
            # How many lessons were compacted into this one?
            total_source_lines = sum(lessons[s]["lines"] for s in sources if s in lessons)
            target_lines = lessons[target]["lines"] if target in lessons else 0
            if total_source_lines > 0 and target_lines > 0:
                fan_in_ratios[target] = {
                    "sources": sources,
                    "n_sources": len(sources),
                    "source_lines": total_source_lines,
                    "target_lines": target_lines,
                    "compression_ratio": round(target_lines / total_source_lines, 3),
                }

    # Citation-fed subtree size for superseding lessons
    # (how many unique lessons cite or transitively cite a superseding node)
    cited_by = defaultdict(set)
    for s, d in citation_edges:
        cited_by[d].add(s)

    subtree_sizes = {}
    for target in superseded_targets:
        # BFS up the citation tree
        visited_sub = set()
        queue = list(cited_by.get(target, set()))
        while queue:
            node = queue.pop(0)
            if node in visited_sub:
                continue
            visited_sub.add(node)
            queue.extend(cited_by.get(node, set()))
        subtree_sizes[target] = len(visited_sub)

    chain_lengths = [len(c) for c in chains]

    return {
        "n_leaf_nodes": len(leaf_nodes),
        "n_internal_nodes": len(internal_nodes),
        "n_consumed_nodes": len(consumed_nodes),
        "total_lessons": len(lessons),
        "pct_consumed": round(100 * len(consumed_nodes) / len(lessons), 1) if lessons else 0,
        "pct_internal": round(100 * len(internal_nodes) / len(lessons), 1) if lessons else 0,
        "n_chains": len(chains),
        "chain_lengths": chain_lengths,
        "mean_chain_length": round(sum(chain_lengths) / len(chain_lengths), 2) if chain_lengths else 0,
        "max_chain_length": max(chain_lengths) if chain_lengths else 0,
        "chains": chains[:10],  # Sample
        "fan_in_compactions": fan_in_ratios,
        "n_fan_in_compactions": len(fan_in_ratios),
        "mean_compression_ratio": round(
            sum(v["compression_ratio"] for v in fan_in_ratios.values()) / len(fan_in_ratios), 3
        ) if fan_in_ratios else 0,
        "subtree_sizes": {k: v for k, v in sorted(subtree_sizes.items(), key=lambda x: -x[1])[:10]},
    }


def hash_vs_merkle_comparison(lessons, superseded_edges, citation_edges):
    """Compare flat hash model vs Merkle tree model predictions.

    Flat hash: each lesson is independent, compaction = discard duplicates
    Merkle tree: lessons form chains, compaction = merge linked subtrees
    """
    # Flat hash model predictions
    flat_unique = sum(1 for l in lessons.values() if not l["is_superseded"])
    flat_superseded = sum(1 for l in lessons.values() if l["is_superseded"])
    flat_compression = round(flat_superseded / len(lessons), 3) if lessons else 0

    # Merkle model: connected components in SUPERSEDED graph represent compaction events
    adj = defaultdict(set)
    for s, d in superseded_edges:
        adj[s].add(d)
        adj[d].add(s)
    visited = set()
    components = []
    def dfs(node, comp):
        if node in visited:
            return
        visited.add(node)
        comp.append(node)
        for nb in adj[node]:
            dfs(nb, comp)
    all_sup_nodes = set()
    for s, d in superseded_edges:
        all_sup_nodes.add(s)
        all_sup_nodes.add(d)
    for n in all_sup_nodes:
        if n not in visited:
            comp = []
            dfs(n, comp)
            components.append(sorted(comp))

    # For each component, identify the "root" (most recent, not superseded)
    comp_roots = []
    for comp in components:
        roots = [n for n in comp if n not in set(e[0] for e in superseded_edges)]
        comp_roots.append({"component": comp, "size": len(comp), "roots": roots})

    # Citation integration: do superseded lessons lose citations to their successors?
    citation_transfer = []
    for old, new in superseded_edges:
        if old in lessons and new in lessons:
            old_cited_by = sum(1 for l in lessons.values() if old in l["cites"])
            new_cited_by = sum(1 for l in lessons.values() if new in l["cites"])
            citation_transfer.append({
                "old": old, "new": new,
                "old_citations": old_cited_by,
                "new_citations": new_cited_by,
                "transfer": new_cited_by > old_cited_by,
            })

    transfer_rate = sum(1 for t in citation_transfer if t["transfer"]) / len(citation_transfer) if citation_transfer else 0

    return {
        "flat_hash_model": {
            "unique_lessons": flat_unique,
            "superseded_lessons": flat_superseded,
            "compression_rate": flat_compression,
            "prediction": "Compaction is one-time deduplication. No history needed.",
        },
        "merkle_tree_model": {
            "n_compaction_components": len(components),
            "component_sizes": sorted([len(c) for c in components], reverse=True),
            "component_details": sorted(comp_roots, key=lambda x: -x["size"])[:10],
            "prediction": "Compaction is iterative chain-building. History (SUPERSEDED chains) is structural.",
        },
        "citation_transfer": {
            "n_transfers_measured": len(citation_transfer),
            "transfer_rate": round(transfer_rate, 3),
            "details": citation_transfer[:10],
            "interpretation": "If transfer_rate > 0.5, citations flow from old → new (Merkle model). If < 0.5, citations stick to original (flat model).",
        },
    }


def temporal_compaction_analysis(lessons):
    """Analyze when compaction events happen relative to lesson production.

    Tests: do SUPERSEDED events cluster at specific sessions (phase transitions)
    or distribute uniformly (incremental)?
    """
    # Group lessons by session
    session_counts = defaultdict(lambda: {"produced": 0, "superseded": 0, "lessons": []})
    for lid, info in lessons.items():
        if info["session"]:
            session_counts[info["session"]]["produced"] += 1
            session_counts[info["session"]]["lessons"].append(lid)
            if info["is_superseded"]:
                session_counts[info["session"]]["superseded"] += 1

    # Find sessions with SUPERSEDED events
    compaction_sessions = {s: d for s, d in session_counts.items() if d["superseded"] > 0}
    non_compaction_sessions = {s: d for s, d in session_counts.items() if d["superseded"] == 0}

    # Burst analysis: are compaction events clustered?
    comp_session_ids = sorted(compaction_sessions.keys())
    gaps = []
    for i in range(1, len(comp_session_ids)):
        gaps.append(comp_session_ids[i] - comp_session_ids[i - 1])

    # Batch size distribution
    batch_sizes = [d["superseded"] for d in compaction_sessions.values()]

    return {
        "n_compaction_sessions": len(compaction_sessions),
        "n_total_sessions": len(session_counts),
        "compaction_frequency": round(len(compaction_sessions) / len(session_counts), 3) if session_counts else 0,
        "compaction_session_ids": comp_session_ids,
        "mean_gap_between_compactions": round(sum(gaps) / len(gaps), 1) if gaps else 0,
        "batch_sizes": sorted(batch_sizes, reverse=True),
        "mean_batch_size": round(sum(batch_sizes) / len(batch_sizes), 2) if batch_sizes else 0,
        "max_batch_size": max(batch_sizes) if batch_sizes else 0,
        "regime_test": {
            "description": "If batch_size > 3 = phase-transition regime; batch_size <= 1 = incremental regime",
            "n_incremental": sum(1 for b in batch_sizes if b <= 1),
            "n_phase_transition": sum(1 for b in batch_sizes if b > 3),
            "n_intermediate": sum(1 for b in batch_sizes if 1 < b <= 3),
        },
    }


def cross_tier_compaction_analysis(lessons, l_to_p_edges, citation_edges):
    """Analyze the L→P compaction as a Merkle tree cross-tier operation.

    In a Merkle tree, internal nodes hash their children.
    In the swarm, principles "hash" (compress) their source lessons.
    This function measures whether this cross-tier compaction follows
    Merkle-tree-like properties.
    """
    # Group by target principle
    p_absorptions = defaultdict(list)
    for old, new in l_to_p_edges:
        p_absorptions[new].append(old)

    # For each principle that absorbs lessons, measure:
    # 1. Fan-in: how many lessons absorbed
    # 2. Source coverage: what % of the lesson's citations does the principle capture?
    # 3. Session span: how many sessions between source lessons and compaction

    results = {}
    for p_id, sources in p_absorptions.items():
        source_sessions = [lessons[s]["session"] for s in sources if s in lessons and lessons[s]["session"]]
        source_cites = set()
        for s in sources:
            if s in lessons:
                source_cites.update(lessons[s]["cites"])

        # Count how many other lessons cite each source
        source_cited_by = defaultdict(int)
        for lid, info in lessons.items():
            for c in info["cites"]:
                if c in sources:
                    source_cited_by[c] += 1

        results[p_id] = {
            "n_sources": len(sources),
            "sources": sources,
            "source_sessions": sorted(source_sessions) if source_sessions else [],
            "session_span": max(source_sessions) - min(source_sessions) if len(source_sessions) > 1 else 0,
            "total_source_citations": len(source_cites),
            "source_cited_by_counts": dict(source_cited_by),
            "total_downstream_citations": sum(source_cited_by.values()),
        }

    # Merkle tree metrics
    total_absorbed = sum(r["n_sources"] for r in results.values())
    mean_fan_in = sum(r["n_sources"] for r in results.values()) / len(results) if results else 0
    max_fan_in = max(r["n_sources"] for r in results.values()) if results else 0

    return {
        "n_principle_absorbers": len(results),
        "total_lessons_absorbed": total_absorbed,
        "mean_fan_in": round(mean_fan_in, 2),
        "max_fan_in": max_fan_in,
        "details": results,
        "merkle_interpretation": (
            "Principles act as Merkle internal nodes: they compress multiple lessons "
            "into a single canonical representation. The fan-in ratio indicates the "
            "compression factor. Higher fan-in = more aggressive compaction."
        ),
    }


def main():
    print("=== F-CRY1 Merkle Tree Formalization (S373) ===\n")

    # Step 1: Parse all lessons
    lessons = parse_lessons()
    print(f"Parsed {len(lessons)} lessons ({sum(1 for l in lessons.values() if l['archived'])} archived)")

    # Step 2: Build graphs
    superseded_edges, l_to_l_edges, l_to_p_edges = build_superseded_dag(lessons)
    citation_edges = build_citation_dag(lessons)
    print(f"SUPERSEDED edges: {len(superseded_edges)} (L→L: {len(l_to_l_edges)}, L→P: {len(l_to_p_edges)})")
    print(f"Citation edges: {len(citation_edges)}")

    # L→P fan-in analysis: which principles absorb multiple lessons?
    p_absorptions = defaultdict(list)
    for old, new in l_to_p_edges:
        p_absorptions[new].append(old)
    print(f"\nPrinciple absorptions (L→P):")
    for p_id, sources in sorted(p_absorptions.items(), key=lambda x: -len(x[1])):
        print(f"  {p_id}: absorbed {len(sources)} lessons: {sources}")

    # Step 3: DAG properties
    print("\n--- SUPERSEDED DAG ---")
    sup_props = compute_dag_properties(superseded_edges, lessons)
    for k, v in sup_props.items():
        if k != "depth_distribution":
            print(f"  {k}: {v}")
    print(f"  depth_distribution: {sup_props['depth_distribution']}")

    print("\n--- Citation DAG ---")
    cite_props = compute_dag_properties(citation_edges, lessons)
    for k, v in cite_props.items():
        if k not in ("depth_distribution", "component_sizes"):
            print(f"  {k}: {v}")

    # Step 3b: Cross-tier compaction (L→P)
    print("\n--- Cross-Tier Compaction (L→P) ---")
    cross_tier = cross_tier_compaction_analysis(lessons, l_to_p_edges, citation_edges)
    print(f"  Principle absorbers: {cross_tier['n_principle_absorbers']}")
    print(f"  Total lessons absorbed into principles: {cross_tier['total_lessons_absorbed']}")
    print(f"  Mean fan-in: {cross_tier['mean_fan_in']}, max: {cross_tier['max_fan_in']}")
    for p_id, detail in cross_tier['details'].items():
        print(f"  {p_id}: {detail['n_sources']} lessons, span={detail['session_span']}s, downstream={detail['total_downstream_citations']}")

    # Step 4: Merkle tree analysis
    print("\n--- Merkle Tree Properties ---")
    merkle = merkle_tree_properties(superseded_edges, citation_edges, lessons)
    print(f"  Leaf nodes (raw, never compacted): {merkle['n_leaf_nodes']}")
    print(f"  Internal nodes (absorb others): {merkle['n_internal_nodes']}")
    print(f"  Consumed nodes (absorbed): {merkle['n_consumed_nodes']}")
    print(f"  % consumed: {merkle['pct_consumed']}%")
    print(f"  % internal: {merkle['pct_internal']}%")
    print(f"  SUPERSEDED chains: {merkle['n_chains']}")
    print(f"  Chain lengths: {merkle['chain_lengths']}")
    print(f"  Mean chain length: {merkle['mean_chain_length']}")
    print(f"  Max chain length: {merkle['max_chain_length']}")
    print(f"  Fan-in compactions: {merkle['n_fan_in_compactions']}")
    print(f"  Mean compression ratio: {merkle['mean_compression_ratio']}")
    if merkle['chains']:
        print(f"  Sample chains: {merkle['chains'][:5]}")
    if merkle['fan_in_compactions']:
        print(f"  Fan-in details:")
        for k, v in list(merkle['fan_in_compactions'].items())[:5]:
            print(f"    {k}: {v['n_sources']} sources, {v['source_lines']}→{v['target_lines']} lines, ratio={v['compression_ratio']}")
    if merkle['subtree_sizes']:
        print(f"  Citation subtree sizes (top 10): {merkle['subtree_sizes']}")

    # Step 5: Hash vs Merkle comparison
    print("\n--- Flat Hash vs Merkle Tree Model ---")
    comparison = hash_vs_merkle_comparison(lessons, superseded_edges, citation_edges)
    flat = comparison["flat_hash_model"]
    print(f"  Flat hash: {flat['unique_lessons']} unique, {flat['superseded_lessons']} superseded, compression={flat['compression_rate']}")
    merk = comparison["merkle_tree_model"]
    print(f"  Merkle: {merk['n_compaction_components']} compaction components, sizes={merk['component_sizes']}")
    ct = comparison["citation_transfer"]
    print(f"  Citation transfer rate: {ct['transfer_rate']} (>0.5 = Merkle, <0.5 = flat)")
    if ct["details"]:
        print(f"  Transfer details (sample):")
        for t in ct["details"][:5]:
            print(f"    {t['old']}→{t['new']}: {t['old_citations']}→{t['new_citations']} cites {'✓' if t['transfer'] else '✗'}")

    # Step 6: Temporal analysis
    print("\n--- Temporal Compaction Analysis ---")
    temporal = temporal_compaction_analysis(lessons)
    print(f"  Compaction sessions: {temporal['n_compaction_sessions']}/{temporal['n_total_sessions']} ({temporal['compaction_frequency']})")
    print(f"  Mean gap between compactions: {temporal['mean_gap_between_compactions']} sessions")
    print(f"  Batch sizes: {temporal['batch_sizes']}")
    print(f"  Mean batch: {temporal['mean_batch_size']}, max batch: {temporal['max_batch_size']}")
    regime = temporal["regime_test"]
    print(f"  Regime test: {regime['n_incremental']} incremental, {regime['n_phase_transition']} phase-transition, {regime['n_intermediate']} intermediate")

    # Build experiment JSON
    result = {
        "session": "S373",
        "frontier": "F-CRY1",
        "domain": "cryptography",
        "experiment": "Merkle tree formalization for knowledge compaction",
        "n_lessons": len(lessons),
        "superseded_dag": sup_props,
        "superseded_breakdown": {
            "l_to_l": len(l_to_l_edges),
            "l_to_p": len(l_to_p_edges),
            "total": len(superseded_edges),
        },
        "cross_tier_compaction": {
            "n_principle_absorbers": cross_tier["n_principle_absorbers"],
            "total_absorbed": cross_tier["total_lessons_absorbed"],
            "mean_fan_in": cross_tier["mean_fan_in"],
            "max_fan_in": cross_tier["max_fan_in"],
            "details": {k: {kk: vv for kk, vv in v.items() if kk != "source_cited_by_counts"}
                       for k, v in cross_tier["details"].items()},
        },
        "citation_dag": {k: v for k, v in cite_props.items() if k != "component_sizes"},
        "merkle_tree": {
            "n_leaf_nodes": merkle["n_leaf_nodes"],
            "n_internal_nodes": merkle["n_internal_nodes"],
            "n_consumed_nodes": merkle["n_consumed_nodes"],
            "pct_consumed": merkle["pct_consumed"],
            "pct_internal": merkle["pct_internal"],
            "n_chains": merkle["n_chains"],
            "chain_lengths": merkle["chain_lengths"],
            "mean_chain_length": merkle["mean_chain_length"],
            "max_chain_length": merkle["max_chain_length"],
            "n_fan_in_compactions": merkle["n_fan_in_compactions"],
            "mean_compression_ratio": merkle["mean_compression_ratio"],
            "top_subtree_sizes": merkle["subtree_sizes"],
        },
        "model_comparison": comparison,
        "temporal_analysis": temporal,
        "verdict": "",  # will fill
        "key_findings": [],
        "unexpected": "",
        "merkle_formalization": {
            "mapping": {
                "leaf": "Raw lesson — never superseded, terminal in SUPERSEDED DAG",
                "internal_node": "Compacted lesson — absorbs one or more predecessors via SUPERSEDED",
                "hash_chain": "SUPERSEDED → successor chain (stateful compression history)",
                "root": "Most-distilled canonical representation in a compaction component",
                "fan_in": "Multiple lessons compressed into one (batch compaction)",
                "fan_out": "One lesson spawning multiple successors (rare — decomposition)",
                "citation_subtree": "Lessons citing a compacted node — the 'verification subtree'",
            },
            "hash_analogy_status": {},
        },
        "cites": ["L-413", "L-679", "L-428", "L-242"],
        "confidence": f"Measured (n={len(lessons)} lessons, {len(superseded_edges)} SUPERSEDED edges, {len(citation_edges)} citation edges)",
    }

    # Verdict synthesis
    findings = []

    # Finding 1: Tree structure
    if merkle["n_chains"] > 0:
        findings.append(f"SUPERSEDED chains exist: {merkle['n_chains']} chains, mean length {merkle['mean_chain_length']}, max {merkle['max_chain_length']}")
    else:
        findings.append("No SUPERSEDED chains found — flat model wins by default")

    # Finding 2: Compaction regime
    if temporal["regime_test"]["n_phase_transition"] > 0:
        findings.append(f"Phase-transition regime confirmed: {temporal['regime_test']['n_phase_transition']} batch-compaction events (>3 lessons)")
    findings.append(f"Incremental regime: {temporal['regime_test']['n_incremental']} single-lesson compactions")

    # Finding 3: Citation transfer
    if ct["transfer_rate"] > 0.5:
        findings.append(f"Citation transfer rate {ct['transfer_rate']} > 0.5: citations flow old→new (Merkle model supported)")
    else:
        findings.append(f"Citation transfer rate {ct['transfer_rate']} ≤ 0.5: citations stick to originals (flat model supported)")

    # Finding 4: Compression ratio
    if merkle["mean_compression_ratio"] > 0:
        findings.append(f"Mean fan-in compression ratio: {merkle['mean_compression_ratio']} (target lines / source lines)")

    # Finding 5: DAG vs tree
    if sup_props["n_components"] > 1:
        findings.append(f"SUPERSEDED graph is a FOREST ({sup_props['n_components']} components), not a single tree — compaction is local, not global")

    result["key_findings"] = findings

    # Finding: cross-tier compaction
    if cross_tier["n_principle_absorbers"] > 0:
        findings.append(f"Cross-tier compaction: {cross_tier['n_principle_absorbers']} principles absorbed {cross_tier['total_lessons_absorbed']} lessons (mean fan-in {cross_tier['mean_fan_in']})")
        findings.append(f"Two-tier Merkle: lessons=leaves, principles=internal nodes. Principles are 'hash' of lesson clusters.")

    # Determine verdict
    has_chains = merkle["n_chains"] > 0
    has_depth = merkle["max_chain_length"] > 1
    has_fan_in = merkle["n_fan_in_compactions"] > 0
    has_cross_tier = cross_tier["n_principle_absorbers"] > 0
    has_phase_transitions = temporal["regime_test"]["n_phase_transition"] > 0

    if has_cross_tier:
        total_compacted = merkle["n_consumed_nodes"] + cross_tier["total_lessons_absorbed"]
        result["verdict"] = f"TWO_TIER_MERKLE_CONFIRMED — {total_compacted} lessons compacted via L→L ({merkle['n_consumed_nodes']}) + L→P ({cross_tier['total_lessons_absorbed']}). Citation DAG (depth {cite_props['max_depth']}) provides the tree structure; SUPERSEDED+principles provide the hash chain."
    elif has_chains and (has_depth or has_fan_in):
        if has_phase_transitions:
            result["verdict"] = "MERKLE_MODEL_SUPPORTED — stateful compaction with two regimes confirmed"
        else:
            result["verdict"] = "MERKLE_MODEL_PARTIAL — chains exist but no phase-transition regime detected"
    else:
        result["verdict"] = "FLAT_MODEL_SUFFICIENT — SUPERSEDED structure too shallow for Merkle analogy"

    # Analogy status
    result["merkle_formalization"]["hash_analogy_status"] = {
        "collision_resistance": "HOLDS (L-679: 99.7% unique fingerprints)",
        "bounded_sensitivity": f"CONDITIONAL — {'two regimes confirmed' if has_phase_transitions else 'regime test inconclusive'} (L-679)",
        "evidence_recoverability": "HOLDS (L-679: 97.9% citation chain integrity)",
        "statefulness": f"{'CONFIRMED' if has_chains else 'NOT CONFIRMED'} — {'SUPERSEDED chains provide compaction history' if has_chains else 'no chains detected'}",
        "merkle_tree_fit": f"{'PARTIAL' if has_chains else 'POOR'} — {'forest structure, not single tree' if sup_props.get('n_components', 0) > 1 else 'single tree'}, depth={merkle.get('max_chain_length', 0)}",
    }

    # Check for unexpected findings
    unexpected = []
    if merkle["pct_consumed"] < 5:
        unexpected.append(f"Very low consumption rate ({merkle['pct_consumed']}%) — most lessons never compacted")
    if sup_props.get("n_components", 0) > 5:
        unexpected.append(f"Highly fragmented: {sup_props['n_components']} independent compaction components")
    if temporal.get("compaction_frequency", 0) < 0.05:
        unexpected.append(f"Compaction very rare ({temporal['compaction_frequency']}): most sessions produce but never compact")
    result["unexpected"] = "; ".join(unexpected) if unexpected else "None"

    print(f"\n=== VERDICT: {result['verdict']} ===")
    print(f"\nKey findings:")
    for f in findings:
        print(f"  • {f}")
    if unexpected:
        print(f"\nUnexpected: {result['unexpected']}")

    # Write experiment JSON
    out_path = Path("experiments/cryptography/f-cry1-merkle-tree-s373.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nArtifact: {out_path}")


if __name__ == "__main__":
    main()
