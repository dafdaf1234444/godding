"""
city_plan.py — Domain adjacency graph and city-plan diagnostics.

Reads `Adjacent:` headers from DOMAIN.md files to build a domain road network.
Reports connectivity, district classification, and zoning violations.

Usage:
    python3 tools/city_plan.py              # full city report
    python3 tools/city_plan.py --adjacency  # adjacency graph only
    python3 tools/city_plan.py --zones      # zone membership + violations
    python3 tools/city_plan.py --json       # machine-readable output

F-CITY1: adjacency routing. F-CITY2: meta decentralization. F-CITY3: commercial zone.
"""

from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOMAINS_DIR = REPO / "domains"

# Zone definitions from city plan
ZONES: dict[str, dict] = {
    "downtown": {
        "domains": ["meta", "expert-swarm", "governance"],
        "rule": "CAP: no new tools without consolidating existing",
    },
    "university": {
        "domains": ["epistemology", "mathematics", "statistics", "stochastic-processes",
                     "graph-theory", "information-science", "guesstimates"],
        "rule": "GROW: highest novelty per lesson",
    },
    "physics-campus": {
        "domains": ["physics", "thermodynamics", "fluid-dynamics", "fractals",
                     "control-theory"],
        "rule": "CONNECT: must cite ≥1 non-physics domain",
    },
    "life-sciences": {
        "domains": ["evolution", "health", "brain", "psychology", "empathy",
                     "human-systems", "linguistics"],
        "rule": "BRIDGE: strongest ISO source — extract more",
    },
    "financial-district": {
        "domains": ["finance", "forecasting", "economy", "cryptocurrency"],
        "rule": "EXPORT: every lane must produce ≥1 external claim",
    },
    "innovation-park": {
        "domains": ["ai", "nk-complexity", "distributed-systems", "claude-code"],
        "rule": "BUILD: tool production zone",
    },
    "creative-quarter": {
        "domains": ["concept-inventor", "dream"],
        "rule": "WILD: no zoning restrictions — generative zone",
    },
    "defense-perimeter": {
        "domains": ["security", "catastrophic-risks", "conflict"],
        "rule": "GUARD: red-team everything that exits the city",
    },
    "strategy-center": {
        "domains": ["strategy", "game-theory", "competitions"],
        "rule": "PLAN: feeds dispatch optimizer priorities",
    },
    "frontier-territory": {
        "domains": ["gaming", "social-media", "plant-biology", "farming",
                     "string-theory", "random-matrix-theory", "helper-swarm",
                     "filtering", "protocol-engineering", "cryptography",
                     "evaluation", "quality", "history"],
        "rule": "HOMESTEAD: claim with ≥1 experiment before building",
    },
}

# Reverse lookup: domain → zone
DOMAIN_TO_ZONE: dict[str, str] = {}
for zone_name, zone_info in ZONES.items():
    for d in zone_info["domains"]:
        DOMAIN_TO_ZONE[d] = zone_name


def get_all_domains() -> list[str]:
    """List all domain directories."""
    result = []
    for entry in sorted(DOMAINS_DIR.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            result.append(entry.name)
    return result


def parse_adjacency(domain: str) -> list[str]:
    """Read Adjacent: header from a domain's DOMAIN.md."""
    domain_md = DOMAINS_DIR / domain / "DOMAIN.md"
    if not domain_md.exists():
        return []
    text = domain_md.read_text(errors="replace")
    # Look for Adjacent: or Adjacent Domains: header
    m = re.search(r"^Adjacent(?:\s+Domains)?:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return []
    raw = m.group(1).strip()
    # Parse comma-separated domain names
    return [d.strip().lower() for d in raw.split(",") if d.strip()]


def build_adjacency_graph() -> dict[str, list[str]]:
    """Build full adjacency graph from all DOMAIN.md files."""
    graph: dict[str, list[str]] = {}
    all_domains = get_all_domains()
    for d in all_domains:
        graph[d] = parse_adjacency(d)
    return graph


def count_lessons_in_domain(domain: str) -> int:
    """Count unique L-NNN references in a domain's DOMAIN.md."""
    domain_md = DOMAINS_DIR / domain / "DOMAIN.md"
    if not domain_md.exists():
        return 0
    text = domain_md.read_text(errors="replace")
    return len(set(re.findall(r"L-\d+", text)))


def report_adjacency(graph: dict[str, list[str]]) -> None:
    """Print adjacency graph report."""
    total_edges = sum(len(v) for v in graph.values())
    connected = sum(1 for v in graph.values() if v)
    total = len(graph)

    print(f"\n=== DOMAIN ADJACENCY GRAPH ===")
    print(f"  Domains: {total}")
    print(f"  With adjacency declarations: {connected} ({100*connected/total:.0f}%)")
    print(f"  Total directed edges: {total_edges}")
    print(f"  Disconnected: {total - connected}")

    if connected > 0:
        print(f"\n  Connections:")
        for d in sorted(graph):
            if graph[d]:
                print(f"    {d:30s} → {', '.join(graph[d])}")

    # Disconnected domains
    disconnected = [d for d in sorted(graph) if not graph[d]]
    if disconnected:
        print(f"\n  No roads to: {', '.join(disconnected[:10])}{'...' if len(disconnected) > 10 else ''}")


def report_zones(graph: dict[str, list[str]]) -> None:
    """Print zone membership and violations."""
    print(f"\n=== ZONING REPORT ===")
    all_domains = get_all_domains()
    unzoned = [d for d in all_domains if d not in DOMAIN_TO_ZONE
               and d != "ISOMORPHISM-ATLAS.md" and d != "city-plan"]

    for zone_name, zone_info in ZONES.items():
        members = zone_info["domains"]
        existing = [d for d in members if (DOMAINS_DIR / d).is_dir()]
        lesson_counts = {d: count_lessons_in_domain(d) for d in existing}
        total_lessons = sum(lesson_counts.values())
        print(f"\n  [{zone_name}] {len(existing)} domains, {total_lessons} lessons")
        print(f"    Rule: {zone_info['rule']}")
        for d in existing:
            adj = graph.get(d, [])
            zone = DOMAIN_TO_ZONE.get(d, "?")
            print(f"      {d:25s} {lesson_counts[d]:3d}L  adj={len(adj)}")

    if unzoned:
        print(f"\n  [UNZONED] {len(unzoned)} domains: {', '.join(unzoned)}")


def report_full(graph: dict[str, list[str]]) -> None:
    """Full city plan report."""
    print("=" * 60)
    print("  SWARM CITY PLAN — SPATIAL DIAGNOSTICS")
    print("=" * 60)

    report_adjacency(graph)
    report_zones(graph)

    # Meta concentration
    all_domains = get_all_domains()
    meta_domains = ZONES.get("downtown", {}).get("domains", [])
    meta_lessons = sum(count_lessons_in_domain(d) for d in meta_domains
                       if (DOMAINS_DIR / d).is_dir())
    total_lessons = sum(count_lessons_in_domain(d) for d in all_domains)
    if total_lessons > 0:
        pct = 100 * meta_lessons / total_lessons
        print(f"\n=== DOWNTOWN CONCENTRATION ===")
        print(f"  Downtown lessons: {meta_lessons}/{total_lessons} ({pct:.1f}%)")
        print(f"  Target: ≤40% (Zipf rank-size distribution)")
        if pct > 40:
            print(f"  ⚠ CONGESTED — {pct - 40:.1f}pp over target")

    # Empty lots
    empty = [d for d in all_domains if count_lessons_in_domain(d) == 0
             and d != "ISOMORPHISM-ATLAS.md" and d != "city-plan"]
    if empty:
        print(f"\n=== EMPTY LOTS ({len(empty)} domains with 0 lessons) ===")
        for d in empty:
            zone = DOMAIN_TO_ZONE.get(d, "unzoned")
            print(f"    {d:25s} zone={zone}")


def main() -> None:
    graph = build_adjacency_graph()

    if "--json" in sys.argv:
        data = {
            "adjacency": graph,
            "zones": {z: info["domains"] for z, info in ZONES.items()},
            "domain_to_zone": DOMAIN_TO_ZONE,
            "connected": sum(1 for v in graph.values() if v),
            "total": len(graph),
            "edges": sum(len(v) for v in graph.values()),
        }
        print(json.dumps(data, indent=2))
    elif "--adjacency" in sys.argv:
        report_adjacency(graph)
    elif "--zones" in sys.argv:
        report_zones(graph)
    else:
        report_full(graph)


if __name__ == "__main__":
    main()
