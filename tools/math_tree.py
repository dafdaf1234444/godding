#!/usr/bin/env python3
"""Mathematical dependency tree builder — external application of swarm graph infrastructure.

Manages a DAG of mathematical objects (axioms, definitions, lemmas, theorems, corollaries)
with typed dependency edges. Generates learning paths, exports visualizations, and
integrates with swarm's knowledge-state and correction-propagation tools.

Usage:
    python3 tools/math_tree.py add --type theorem --title "FTC Part 1" --domain analysis --prereqs D-003,L-001
    python3 tools/math_tree.py path T-001                    # learning path to theorem T-001
    python3 tools/math_tree.py validate                      # cycle detection + integrity
    python3 tools/math_tree.py export --format dot            # Graphviz DOT output
    python3 tools/math_tree.py export --format json           # full JSON export
    python3 tools/math_tree.py stats                          # graph statistics
    python3 tools/math_tree.py status T-001 proved            # update status
    python3 tools/math_tree.py cascade T-001 --mark flawed    # propagate error downstream
    python3 tools/math_tree.py import-latex FILE.tex           # extract \\uses{} deps from LaTeX
"""
import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES_DIR = ROOT / "domains" / "mathematics" / "nodes"
MANIFEST = ROOT / "domains" / "mathematics" / "manifest.json"

# Node types and their canonical prefixes
NODE_TYPES = {
    "axiom": "A",
    "definition": "D",
    "lemma": "L",
    "proposition": "P",
    "theorem": "T",
    "corollary": "C",
    "example": "E",
}

# Valid status progression
STATUS_ORDER = ["stub", "stated", "proved", "verified", "formalized"]

# Edge types (Lean Blueprint distinction: statement vs proof dependency)
EDGE_TYPES = ["uses_in_statement", "uses_in_proof", "generalizes", "specializes"]


def load_manifest():
    """Load or initialize the manifest tracking all nodes."""
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"nodes": {}, "next_id": {t: 1 for t in NODE_TYPES}, "version": 1}


def save_manifest(manifest):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")


def load_node(node_id):
    """Load a single node JSON file."""
    path = NODES_DIR / f"{node_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_node(node):
    """Save a single node JSON file."""
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    path = NODES_DIR / f"{node['id']}.json"
    path.write_text(json.dumps(node, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def load_all_nodes():
    """Load all nodes from disk."""
    nodes = {}
    if not NODES_DIR.exists():
        return nodes
    for f in sorted(NODES_DIR.glob("*.json")):
        try:
            node = json.loads(f.read_text(encoding="utf-8"))
            nodes[node["id"]] = node
        except (json.JSONDecodeError, KeyError):
            print(f"WARNING: corrupt node file {f}", file=sys.stderr)
    return nodes


# --- Core operations ---

def cmd_add(args):
    """Add a new math node."""
    manifest = load_manifest()
    ntype = args.type
    if ntype not in NODE_TYPES:
        print(f"ERROR: type must be one of {list(NODE_TYPES.keys())}", file=sys.stderr)
        return 1

    prefix = NODE_TYPES[ntype]
    nid = manifest["next_id"].get(ntype, 1)
    node_id = f"{prefix}-{nid:03d}"
    manifest["next_id"][ntype] = nid + 1

    # Parse prerequisites with optional edge type
    prereqs = []
    if args.prereqs:
        for p in args.prereqs.split(","):
            p = p.strip()
            if ":" in p:
                ref, etype = p.rsplit(":", 1)
                if etype not in EDGE_TYPES:
                    etype = "uses_in_proof"
            else:
                ref = p
                etype = "uses_in_proof"
            prereqs.append({"ref": ref, "edge_type": etype})

    node = {
        "id": node_id,
        "type": ntype,
        "title": args.title,
        "statement": args.statement or "",
        "domain": args.domain or "general",
        "prerequisites": prereqs,
        "status": "stated" if args.statement else "stub",
        "proof_sketch": "",
        "tags": args.tags.split(",") if args.tags else [],
        "notes": "",
    }

    save_node(node)
    manifest["nodes"][node_id] = {"type": ntype, "title": args.title, "domain": args.domain or "general"}
    save_manifest(manifest)
    print(f"Created {node_id}: {args.title}")
    return 0


def cmd_path(args):
    """Generate a learning path (topological sort of prerequisites) to reach a target node."""
    nodes = load_all_nodes()
    target = args.target
    if target not in nodes:
        print(f"ERROR: node {target} not found", file=sys.stderr)
        return 1

    typed = getattr(args, "typed", False)

    # Build adjacency and reverse topological sort from target
    # When --typed: for statement deps, include only the node (skip its proof chain)
    visited = set()
    order = []

    def dfs(nid, statement_only=False):
        if nid in visited:
            return
        visited.add(nid)
        node = nodes.get(nid)
        if not node:
            return
        if not statement_only:
            for dep in node.get("prerequisites", []):
                is_stmt = dep.get("edge_type") == "uses_in_statement"
                dfs(dep["ref"], statement_only=(typed and is_stmt))
        order.append(nid)

    dfs(target)

    print(f"Learning path to {target} ({nodes[target]['title']}):")
    print(f"  {len(order)} nodes, {len(order) - 1} prerequisite steps\n")
    for i, nid in enumerate(order):
        node = nodes.get(nid, {"title": "???", "type": "?", "status": "?"})
        status_mark = {"stub": "[ ]", "stated": "[S]", "proved": "[P]",
                       "verified": "[V]", "formalized": "[F]"}.get(node["status"], "[?]")
        marker = " → TARGET" if nid == target else ""
        print(f"  {i+1}. {status_mark} {nid} ({node['type']}): {node['title']}{marker}")

    # Show which nodes are statement-deps vs proof-deps for target
    target_node = nodes[target]
    stmt_deps = [d["ref"] for d in target_node.get("prerequisites", [])
                 if d.get("edge_type") == "uses_in_statement"]
    proof_deps = [d["ref"] for d in target_node.get("prerequisites", [])
                  if d.get("edge_type") == "uses_in_proof"]
    if stmt_deps or proof_deps:
        print(f"\n  Statement deps: {', '.join(stmt_deps) or 'none'}")
        print(f"  Proof deps: {', '.join(proof_deps) or 'none'}")

    return 0


def cmd_validate(args):
    """Validate the dependency DAG — cycle detection + reference integrity."""
    nodes = load_all_nodes()
    errors = []

    # Check all prerequisite references exist
    for nid, node in nodes.items():
        for dep in node.get("prerequisites", []):
            if dep["ref"] not in nodes:
                errors.append(f"{nid} references nonexistent {dep['ref']}")

    # Cycle detection (DFS)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in nodes}
    cycles = []

    def dfs_cycle(nid, path):
        color[nid] = GRAY
        path.append(nid)
        node = nodes[nid]
        for dep in node.get("prerequisites", []):
            ref = dep["ref"]
            if ref not in color:
                continue
            if color[ref] == GRAY:
                cycle_start = path.index(ref)
                cycles.append(path[cycle_start:] + [ref])
            elif color[ref] == WHITE:
                dfs_cycle(ref, path)
        path.pop()
        color[nid] = BLACK

    for nid in nodes:
        if color[nid] == WHITE:
            dfs_cycle(nid, [])

    if cycles:
        for c in cycles:
            errors.append(f"CYCLE: {' → '.join(c)}")

    # Bidirectional check: warn about orphan nodes (no deps and not depended on)
    depended_on = set()
    for node in nodes.values():
        for dep in node.get("prerequisites", []):
            depended_on.add(dep["ref"])
    orphans = [nid for nid in nodes
               if nid not in depended_on and not nodes[nid].get("prerequisites")]
    if orphans and len(nodes) > 1:
        print(f"  INFO: {len(orphans)} isolated nodes: {', '.join(orphans[:5])}")

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print(f"VALIDATION PASSED — {len(nodes)} nodes, 0 errors")
        return 0


def cmd_export(args):
    """Export the dependency graph in DOT or JSON format."""
    nodes = load_all_nodes()

    if args.format == "json":
        output = {"nodes": list(nodes.values()), "stats": _compute_stats(nodes)}
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0

    if args.format == "dot":
        # Graphviz DOT output with type-based shapes and status-based colors
        shapes = {"axiom": "diamond", "definition": "box", "lemma": "ellipse",
                  "proposition": "ellipse", "theorem": "doubleoctagon",
                  "corollary": "octagon", "example": "note"}
        colors = {"stub": "white", "stated": "lightyellow", "proved": "lightblue",
                  "verified": "lightgreen", "formalized": "green"}
        edge_styles = {"uses_in_statement": "solid", "uses_in_proof": "dashed",
                       "generalizes": "dotted", "specializes": "bold"}

        print("digraph MathDeps {")
        print('  rankdir=BT;')
        print('  node [fontname="Helvetica"];')
        for nid, node in nodes.items():
            shape = shapes.get(node["type"], "ellipse")
            fill = colors.get(node["status"], "white")
            label = f"{nid}\\n{node['title']}"
            print(f'  "{nid}" [label="{label}", shape={shape}, '
                  f'style=filled, fillcolor="{fill}"];')
        for nid, node in nodes.items():
            for dep in node.get("prerequisites", []):
                style = edge_styles.get(dep.get("edge_type", "uses_in_proof"), "solid")
                print(f'  "{dep["ref"]}" -> "{nid}" [style={style}];')
        print("}")
        return 0

    if args.format == "markdown":
        print("# Mathematical Dependency Tree\n")
        # Group by domain
        by_domain = defaultdict(list)
        for node in nodes.values():
            by_domain[node.get("domain", "general")].append(node)
        for domain in sorted(by_domain):
            print(f"## {domain.title()}\n")
            for node in sorted(by_domain[domain], key=lambda n: n["id"]):
                status = node["status"].upper()
                deps = ", ".join(d["ref"] for d in node.get("prerequisites", []))
                print(f"- **{node['id']}** ({node['type']}): {node['title']} [{status}]")
                if deps:
                    print(f"  - Prerequisites: {deps}")
            print()
        return 0

    print(f"ERROR: unknown format {args.format}", file=sys.stderr)
    return 1


def cmd_stats(args):
    """Print graph statistics."""
    nodes = load_all_nodes()
    stats = _compute_stats(nodes)
    print(f"Math Dependency Tree — {stats['total_nodes']} nodes")
    print(f"  Types: {stats['by_type']}")
    print(f"  Status: {stats['by_status']}")
    print(f"  Domains: {stats['by_domain']}")
    print(f"  Total edges: {stats['total_edges']}")
    print(f"  Edge types: {stats['by_edge_type']}")
    print(f"  Avg prerequisites: {stats['avg_prereqs']:.1f}")
    print(f"  Max depth: {stats['max_depth']}")
    print(f"  Roots (no prereqs): {stats['root_count']}")
    print(f"  Leaves (not depended on): {stats['leaf_count']}")
    return 0


def _compute_stats(nodes):
    by_type = defaultdict(int)
    by_status = defaultdict(int)
    by_domain = defaultdict(int)
    by_edge_type = defaultdict(int)
    total_edges = 0
    depended_on = set()

    for node in nodes.values():
        by_type[node["type"]] += 1
        by_status[node["status"]] += 1
        by_domain[node.get("domain", "general")] += 1
        for dep in node.get("prerequisites", []):
            total_edges += 1
            by_edge_type[dep.get("edge_type", "uses_in_proof")] += 1
            depended_on.add(dep["ref"])

    roots = [nid for nid, n in nodes.items() if not n.get("prerequisites")]
    leaves = [nid for nid in nodes if nid not in depended_on]

    # Max depth via DFS
    max_depth = 0
    if nodes:
        memo = {}
        def depth(nid):
            if nid in memo:
                return memo[nid]
            node = nodes.get(nid)
            if not node or not node.get("prerequisites"):
                memo[nid] = 0
                return 0
            d = 1 + max((depth(dep["ref"]) for dep in node["prerequisites"]
                         if dep["ref"] in nodes), default=0)
            memo[nid] = d
            return d
        max_depth = max(depth(nid) for nid in nodes)

    avg_prereqs = (total_edges / len(nodes)) if nodes else 0

    return {
        "total_nodes": len(nodes), "by_type": dict(by_type),
        "by_status": dict(by_status), "by_domain": dict(by_domain),
        "total_edges": total_edges, "by_edge_type": dict(by_edge_type),
        "avg_prereqs": avg_prereqs, "max_depth": max_depth,
        "root_count": len(roots), "leaf_count": len(leaves),
    }


def cmd_status(args):
    """Update a node's status."""
    node = load_node(args.node_id)
    if not node:
        print(f"ERROR: node {args.node_id} not found", file=sys.stderr)
        return 1
    if args.new_status not in STATUS_ORDER:
        print(f"ERROR: status must be one of {STATUS_ORDER}", file=sys.stderr)
        return 1
    old = node["status"]
    node["status"] = args.new_status
    save_node(node)
    print(f"{args.node_id}: {old} → {args.new_status}")
    return 0


def cmd_cascade(args):
    """Propagate an error through the dependency graph (correction propagation for math)."""
    nodes = load_all_nodes()
    if args.node_id not in nodes:
        print(f"ERROR: node {args.node_id} not found", file=sys.stderr)
        return 1

    # Find all downstream nodes that depend on the flawed node
    affected = set()
    queue = deque([args.node_id])
    # Build reverse graph: who depends on this node?
    dependents = defaultdict(set)
    for nid, node in nodes.items():
        for dep in node.get("prerequisites", []):
            dependents[dep["ref"]].add(nid)

    while queue:
        current = queue.popleft()
        for dep_nid in dependents.get(current, []):
            if dep_nid not in affected:
                affected.add(dep_nid)
                queue.append(dep_nid)

    print(f"Cascade from {args.node_id}: {len(affected)} downstream node(s) affected")
    for nid in sorted(affected):
        node = nodes[nid]
        print(f"  ⚠ {nid} ({node['type']}): {node['title']} [{node['status']}]")
        if args.mark:
            node["status"] = "stub"
            node["notes"] = f"Invalidated by cascade from {args.node_id}. " + node.get("notes", "")
            save_node(node)

    if args.mark:
        print(f"\n  Marked {len(affected)} nodes as 'stub' (needs re-verification)")
    return 0


def cmd_import_latex(args):
    """Extract dependency relationships from LaTeX files using \\uses{} commands (Lean Blueprint pattern)."""
    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file {path} not found", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8", errors="replace")

    # Pattern: \begin{theorem}[Title]\label{thm:name} ... \uses{def:foo, lem:bar}
    env_re = re.compile(
        r"\\begin\{(\w+)\}(?:\[([^\]]*)\])?\s*(?:\\label\{([^}]*)\})?"
        r"(.*?)"
        r"\\end\{\1\}",
        re.DOTALL
    )
    uses_re = re.compile(r"\\uses\{([^}]*)\}")

    found = []
    for m in env_re.finditer(text):
        env_type = m.group(1).lower()
        title = m.group(2) or ""
        label = m.group(3) or ""
        body = m.group(4)
        uses_match = uses_re.search(body)
        deps = []
        if uses_match:
            deps = [d.strip() for d in uses_match.group(1).split(",") if d.strip()]

        if env_type in ("theorem", "lemma", "definition", "proposition", "corollary", "axiom"):
            found.append({
                "env": env_type, "title": title, "label": label,
                "deps": deps, "statement": body.strip()[:200]
            })

    print(f"Extracted {len(found)} mathematical objects from {path.name}:")
    for item in found:
        dep_str = f" ← {', '.join(item['deps'])}" if item['deps'] else ""
        print(f"  {item['env']:12s} {item['label'] or '(unlabeled)':20s} {item['title']}{dep_str}")

    if args.create:
        manifest = load_manifest()
        label_to_id = {}
        for item in found:
            ntype = item["env"]
            if ntype not in NODE_TYPES:
                continue
            prefix = NODE_TYPES[ntype]
            nid_num = manifest["next_id"].get(ntype, 1)
            node_id = f"{prefix}-{nid_num:03d}"
            manifest["next_id"][ntype] = nid_num + 1
            label_to_id[item["label"]] = node_id

        for item in found:
            ntype = item["env"]
            if ntype not in NODE_TYPES:
                continue
            node_id = label_to_id.get(item["label"])
            if not node_id:
                continue
            prereqs = []
            for dep_label in item["deps"]:
                ref = label_to_id.get(dep_label, dep_label)
                prereqs.append({"ref": ref, "edge_type": "uses_in_proof"})
            node = {
                "id": node_id, "type": ntype, "title": item["title"] or item["label"],
                "statement": item["statement"], "domain": "imported",
                "prerequisites": prereqs, "status": "stated",
                "proof_sketch": "", "tags": ["imported"], "notes": f"From {path.name}",
            }
            save_node(node)
            manifest["nodes"][node_id] = {"type": ntype, "title": node["title"], "domain": "imported"}

        save_manifest(manifest)
        print(f"\nCreated {len(label_to_id)} nodes from LaTeX import")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Mathematical dependency tree builder")
    sub = parser.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="Add a math node")
    p_add.add_argument("--type", required=True, choices=NODE_TYPES.keys())
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--statement", default="")
    p_add.add_argument("--domain", default="general")
    p_add.add_argument("--prereqs", default="", help="Comma-separated IDs, optionally with :edge_type")
    p_add.add_argument("--tags", default="")

    p_path = sub.add_parser("path", help="Learning path to target node")
    p_path.add_argument("target")
    p_path.add_argument("--typed", action="store_true",
                        help="Statement-aware: skip proof chains for statement-only deps")

    p_val = sub.add_parser("validate", help="Validate DAG integrity")

    p_exp = sub.add_parser("export", help="Export graph")
    p_exp.add_argument("--format", choices=["dot", "json", "markdown"], default="dot")

    p_stats = sub.add_parser("stats", help="Graph statistics")

    p_status = sub.add_parser("status", help="Update node status")
    p_status.add_argument("node_id")
    p_status.add_argument("new_status", choices=STATUS_ORDER)

    p_cascade = sub.add_parser("cascade", help="Error propagation")
    p_cascade.add_argument("node_id")
    p_cascade.add_argument("--mark", action="store_true", help="Mark affected as stub")

    p_import = sub.add_parser("import-latex", help="Import from LaTeX")
    p_import.add_argument("file")
    p_import.add_argument("--create", action="store_true", help="Create nodes from import")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 0

    cmds = {"add": cmd_add, "path": cmd_path, "validate": cmd_validate,
            "export": cmd_export, "stats": cmd_stats, "status": cmd_status,
            "cascade": cmd_cascade, "import-latex": cmd_import_latex}
    return cmds[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
