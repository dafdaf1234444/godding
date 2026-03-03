#!/usr/bin/env python3
"""genesis_seeds.py — Select citation-central seed lessons for genesis DNA (L-1247).

Genesis DNA transmits 3.7% of knowledge (abstract/protocol layer) but 0% operative
recursion substrate. Children produce 0% L→L citations across 33 swarms (n=313).

This tool selects 5-10 seed lessons by citation centrality that, when included in
genesis bundles, provide children with a structural backbone for L→L recursion.

Composite score: in_degree * log2(domain_reach + 1) * bridge_bonus * dna_weight
  - in_degree: how many lessons cite this one
  - domain_reach: unique domains of citing lessons (cross-domain breadth)
  - bridge_bonus: 1.5x if lesson has both in-degree >=10 and out-degree >=5
  - dna_weight: 1.0 + 0.5 * (DNA files referencing this lesson) (L-1259)

Usage:
  python3 tools/genesis_seeds.py              # Print top 10 seeds
  python3 tools/genesis_seeds.py --diverse    # Domain-diverse seeds (max 2/domain, L-1262)
  python3 tools/genesis_seeds.py --max-per-domain 3  # Custom domain cap
  python3 tools/genesis_seeds.py --top 5      # Print top N seeds
  python3 tools/genesis_seeds.py --json       # JSON output
  python3 tools/genesis_seeds.py --copy DIR   # Copy seed lessons to DIR/memory/lessons/
"""
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LESSONS_DIR = REPO / "memory" / "lessons"
DNA_FILES = [
    REPO / "beliefs" / "CORE.md",
    REPO / "memory" / "PRINCIPLES.md",
    REPO / "beliefs" / "PHILOSOPHY.md",
    REPO / "beliefs" / "DEPS.md",
]


def parse_lesson(path: Path) -> dict:
    """Extract lesson metadata: ID, title, session, domain, cites list."""
    text = path.read_text(errors="replace")
    lines = text.strip().split("\n")
    result = {"path": path, "id": "", "title": "", "session": "", "domain": "",
              "cites": [], "sharpe": 0}

    # ID + title from first line
    m = re.match(r"#\s+(L-\d+):\s*(.+)", lines[0] if lines else "")
    if m:
        result["id"] = m.group(1)
        result["title"] = m.group(2).strip()

    for line in lines[:10]:
        # Session
        sm = re.search(r"Session:\s*S(\d+)", line)
        if sm:
            result["session"] = f"S{sm.group(1)}"
        # Domain
        dm = re.search(r"Domain:\s*(\S+)", line)
        if dm:
            result["domain"] = dm.group(1)
        # Cites
        cm = re.match(r"Cites:\s*(.+)", line)
        if cm:
            result["cites"] = re.findall(r"L-\d+", cm.group(1))
        # Sharpe
        shm = re.search(r"Sharpe:\s*(\d+)", line)
        if shm:
            result["sharpe"] = int(shm.group(1))

    return result


def build_citation_graph(lessons: list[dict]) -> dict:
    """Build in-degree, out-degree, and domain-reach maps."""
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    # Track which domains cite each lesson
    cited_by_domains = defaultdict(set)
    # Track which lesson IDs cite each lesson
    cited_by = defaultdict(set)

    id_to_domain = {l["id"]: l["domain"] for l in lessons if l["id"]}

    for lesson in lessons:
        lid = lesson["id"]
        if not lid:
            continue
        out_degree[lid] = len(lesson["cites"])
        for cited in lesson["cites"]:
            in_degree[cited] += 1
            cited_by[cited].add(lid)
            if lesson["domain"]:
                cited_by_domains[cited].add(lesson["domain"])

    return {
        "in_degree": dict(in_degree),
        "out_degree": dict(out_degree),
        "cited_by_domains": {k: list(v) for k, v in cited_by_domains.items()},
        "cited_by": {k: list(v) for k, v in cited_by.items()},
        "id_to_domain": id_to_domain,
    }


def count_dna_references() -> dict[str, int]:
    """Count how many DNA files reference each L-NNN lesson (L-1259)."""
    ref_counts: dict[str, int] = defaultdict(int)
    for f in DNA_FILES:
        if not f.exists():
            continue
        text = f.read_text(errors="replace")
        for lid in set(re.findall(r"\bL-\d+\b", text)):
            ref_counts[lid] += 1
    return dict(ref_counts)


def score_lessons(lessons: list[dict], graph: dict, top_n: int = 10,
                   max_per_domain: int = 0) -> list[dict]:
    """Score and rank lessons by citation centrality composite.

    Args:
        max_per_domain: If >0, cap seeds per domain to ensure diversity (L-1262).
            Without this, meta dominates (7/10 seeds). With max_per_domain=2,
            domain coverage increases 3x with <10% citation loss.
    """
    dna_refs = count_dna_references()
    scored = []
    for lesson in lessons:
        lid = lesson["id"]
        if not lid:
            continue
        in_deg = graph["in_degree"].get(lid, 0)
        out_deg = graph["out_degree"].get(lid, 0)
        domain_reach = len(graph["cited_by_domains"].get(lid, []))
        # Bridge bonus: lessons that both receive and produce citations
        bridge = 1.5 if in_deg >= 10 and out_deg >= 5 else 1.0
        # DNA weight: boost lessons referenced in genesis DNA files (L-1259)
        dna_count = dna_refs.get(lid, 0)
        dna_weight = 1.0 + 0.5 * dna_count
        # Composite: in_degree * log2(domain_reach + 1) * bridge * dna_weight
        score = in_deg * math.log2(domain_reach + 1) * bridge * dna_weight
        if score > 0:
            scored.append({
                "id": lid,
                "title": lesson["title"],
                "session": lesson["session"],
                "domain": lesson["domain"],
                "in_degree": in_deg,
                "out_degree": out_deg,
                "domain_reach": domain_reach,
                "bridge": bridge > 1.0,
                "dna_refs": dna_count,
                "score": round(score, 1),
                "path": str(lesson["path"].relative_to(REPO)),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)

    if max_per_domain > 0:
        selected = []
        domain_counts: dict[str, int] = defaultdict(int)
        for s in scored:
            dom = s["domain"] or "unknown"
            if domain_counts[dom] < max_per_domain:
                selected.append(s)
                domain_counts[dom] += 1
            if len(selected) >= top_n:
                break
        return selected

    return scored[:top_n]


def main():
    top_n = 10
    json_mode = "--json" in sys.argv
    diverse = "--diverse" in sys.argv
    copy_dir = None
    max_per_domain = 2 if diverse else 0

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--top" and i < len(sys.argv) - 1:
            top_n = int(sys.argv[i + 1])
        if arg == "--copy" and i < len(sys.argv) - 1:
            copy_dir = Path(sys.argv[i + 1])
        if arg == "--max-per-domain" and i < len(sys.argv) - 1:
            max_per_domain = int(sys.argv[i + 1])

    # Parse all lessons
    lesson_files = sorted(LESSONS_DIR.glob("L-*.md"))
    lessons = [parse_lesson(f) for f in lesson_files]

    # Build citation graph
    graph = build_citation_graph(lessons)

    # Score and rank
    seeds = score_lessons(lessons, graph, top_n, max_per_domain=max_per_domain)

    if json_mode:
        unique_domains = len({s["domain"] for s in seeds if s["domain"]})
        print(json.dumps({"seeds": seeds, "total_lessons": len(lessons),
                          "total_edges": sum(graph["in_degree"].values()),
                          "unique_seed_domains": unique_domains,
                          "max_per_domain": max_per_domain}, indent=2))
        return 0

    # Print report
    total_edges = sum(graph["in_degree"].values())
    mode = f" --diverse (max {max_per_domain}/domain)" if max_per_domain > 0 else ""
    print(f"=== GENESIS SEED SELECTOR (L-1247){mode} ===")
    print(f"Corpus: {len(lessons)} lessons, {total_edges} citation edges")
    unique_domains = len({s["domain"] for s in seeds if s["domain"]})
    print(f"Seed domains: {unique_domains} unique")
    print(f"\nTop {top_n} seed lessons by citation centrality:\n")
    print(f"{'Rank':>4}  {'Score':>7}  {'InDeg':>5}  {'OutDeg':>6}  {'Domains':>7}  {'Bridge':>6}  {'DNA':>4}  {'ID':<8}  Title")
    print("-" * 110)
    for i, s in enumerate(seeds, 1):
        bridge_str = "YES" if s["bridge"] else ""
        print(f"{i:4d}  {s['score']:7.1f}  {s['in_degree']:5d}  {s['out_degree']:6d}  {s['domain_reach']:7d}  {bridge_str:>6}  {s.get('dna_refs', 0):4d}  {s['id']:<8}  {s['title'][:50]}")

    # Copy if requested
    if copy_dir:
        dest = copy_dir / "memory" / "lessons"
        dest.mkdir(parents=True, exist_ok=True)
        copied = 0
        for s in seeds:
            src = REPO / s["path"]
            dst = dest / src.name
            dst.write_text(src.read_text())
            copied += 1
        print(f"\nCopied {copied} seed lessons to {dest}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
