#!/usr/bin/env python3
"""genesis_seeds.py — Select citation-central seed lessons for genesis DNA (L-1247).

Genesis DNA transmits 3.7% of knowledge (abstract/protocol layer) but 0% operative
recursion substrate. Children produce 0% L→L citations across 33 swarms (n=313).

This tool selects 5-10 seed lessons by dual-objective scoring (L-1259):
  Pool 1 (centrality): structural backbone — high in-degree, cross-domain reach
  Pool 2 (DNA coverage): resolve dangling L-refs in CORE/PRINCIPLES/PHILOSOPHY/DEPS

Composite score: in_degree * log2(domain_reach + 1) * bridge_bonus * dna_weight
  - in_degree: how many lessons cite this one
  - domain_reach: unique domains of citing lessons (cross-domain breadth)
  - bridge_bonus: 1.5x if lesson has both in-degree >=10 and out-degree >=5
  - dna_weight: 1.0 + 0.5 * (DNA files referencing this lesson) (L-1259)

Yield scoring (L-1249, L-1261): --yield adds recombination potential per lesson.
  Computes yield density (total_yield / sqrt(pair_count)) per lesson — measures
  bridge quality, not hub degree. Added as scaled additive component to avoid
  correlation with centrality (high-degree nodes accumulate yield passively).

Usage:
  python3 tools/genesis_seeds.py              # Dual-objective (default: 5 centrality + 5 DNA)
  python3 tools/genesis_seeds.py --yield      # Yield-scored seeds (L-1249/L-1261)
  python3 tools/genesis_seeds.py --no-dna-reserve  # Pure centrality (legacy)
  python3 tools/genesis_seeds.py --dna-reserve 3   # Custom DNA reserve slots
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


def _normalize_lid(lid: str) -> str:
    """Normalize L-NNN IDs: strip leading zeros for consistent matching (L-1271)."""
    m = re.match(r"L-0*(\d+)", lid)
    return f"L-{m.group(1)}" if m else lid


def parse_lesson(path: Path) -> dict:
    """Extract lesson metadata: ID, title, session, domain, cites list."""
    text = path.read_text(errors="replace")
    lines = text.strip().split("\n")
    result = {"path": path, "id": "", "title": "", "session": "", "domain": "",
              "cites": [], "sharpe": 0, "level": "L2"}

    # ID + title from first line
    m = re.match(r"#\s+(L-\d+):\s*(.+)", lines[0] if lines else "")
    if m:
        result["id"] = _normalize_lid(m.group(1))
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
            result["cites"] = [_normalize_lid(c) for c in re.findall(r"L-\d+", cm.group(1))]
        # Sharpe
        shm = re.search(r"Sharpe:\s*(\d+)", line)
        if shm:
            result["sharpe"] = int(shm.group(1))
        # Level
        lm = re.search(r"Level:\s*(L\d)", line)
        if lm:
            result["level"] = lm.group(1)

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
            ref_counts[_normalize_lid(lid)] += 1
    return dict(ref_counts)


def compute_yield_potential(lessons: list[dict], graph: dict,
                            min_shared: int = 2) -> dict[str, dict]:
    """Compute per-lesson recombination yield density (L-1249, L-1261).

    For each lesson, computes:
      - total_yield: sum of yield scores across all recombination pairs
      - pair_count: number of recombination pairs this lesson participates in
      - yield_density: total_yield / sqrt(pair_count) — rewards bridge quality

    Yield density decorrelates from centrality: high-degree hubs participate
    in many low-yield pairs; bridge nodes participate in fewer high-yield pairs.
    """
    by_id = {l["id"]: l for l in lessons if l["id"]}
    level_num = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}

    # Build cited-set per lesson
    cited_sets: dict[str, set] = {}
    for l in lessons:
        if l["id"]:
            cited_sets[l["id"]] = set(l["cites"])

    # Only check lessons with enough citations to form pairs
    active_ids = [lid for lid, cs in cited_sets.items() if len(cs) >= min_shared]

    yield_total: dict[str, float] = defaultdict(float)
    pair_count: dict[str, int] = defaultdict(int)

    for i, a_id in enumerate(active_ids):
        a_cites = cited_sets[a_id]
        a_domain = by_id[a_id].get("domain", "")
        a_sharpe = by_id[a_id].get("sharpe", 0)
        a_level = level_num.get(by_id[a_id].get("level", "L2"), 2)

        for b_id in active_ids[i + 1:]:
            # Skip if already connected
            if b_id in a_cites or a_id in cited_sets.get(b_id, set()):
                continue
            shared = len(a_cites & cited_sets[b_id])
            if shared < min_shared:
                continue

            b_domain = by_id[b_id].get("domain", "")
            b_sharpe = by_id[b_id].get("sharpe", 0)
            b_level = level_num.get(by_id[b_id].get("level", "L2"), 2)

            avg_sharpe = (a_sharpe + b_sharpe) / 2
            avg_level = (a_level + b_level) / 2
            sharpe_bonus = 1 + 0.15 * (avg_sharpe - 7)
            level_bonus = 1 + 0.4 * (avg_level - 2)
            cross = a_domain != b_domain and a_domain and b_domain
            cross_factor = 0.80 if cross else 1.0

            y = 0.058 * (shared / 2) ** 1.5 * sharpe_bonus * level_bonus * cross_factor
            yield_total[a_id] += y
            yield_total[b_id] += y
            pair_count[a_id] += 1
            pair_count[b_id] += 1

    result = {}
    for lid in set(yield_total) | set(pair_count):
        yt = yield_total.get(lid, 0.0)
        pc = pair_count.get(lid, 0)
        density = yt / math.sqrt(max(pc, 1))
        result[lid] = {"total": round(yt, 4), "pairs": pc, "density": round(density, 4)}
    return result


def _score_all(lessons: list[dict], graph: dict,
               yield_data: dict[str, dict] | None = None) -> list[dict]:
    """Score all lessons by centrality composite with optional yield density."""
    dna_refs = count_dna_references()
    scored = []
    for lesson in lessons:
        lid = lesson["id"]
        if not lid:
            continue
        in_deg = graph["in_degree"].get(lid, 0)
        out_deg = graph["out_degree"].get(lid, 0)
        domain_reach = len(graph["cited_by_domains"].get(lid, []))
        bridge = 1.5 if in_deg >= 10 and out_deg >= 5 else 1.0
        dna_count = dna_refs.get(lid, 0)
        dna_weight = 1.0 + 0.5 * dna_count
        centrality = in_deg * math.log2(domain_reach + 1) * bridge * dna_weight

        yld_density = 0.0
        yld_total = 0.0
        yld_pairs = 0
        if yield_data and lid in yield_data:
            yd = yield_data[lid]
            yld_density = yd["density"]
            yld_total = yd["total"]
            yld_pairs = yd["pairs"]
            # Additive yield: scale density so max yield contribution ~= median centrality
            # This lets yield genuinely reshuffle mid-range seeds without overwhelming L-601
            score = centrality + 100.0 * yld_density
        else:
            score = centrality

        if score > 0:
            entry = {
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
                "pool": "",
            }
            if yield_data is not None:
                entry["yield_density"] = round(yld_density, 3)
                entry["yield_total"] = round(yld_total, 3)
                entry["yield_pairs"] = yld_pairs
            scored.append(entry)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def score_lessons(lessons: list[dict], graph: dict, top_n: int = 10,
                   max_per_domain: int = 0, dna_reserve: int = 0,
                   yield_data: dict[str, dict] | None = None) -> list[dict]:
    """Score and rank lessons by dual-objective: centrality + DNA coverage (L-1259).

    Two-pool selection when dna_reserve > 0:
      Pool 1: top (top_n - dna_reserve) by centrality (structural backbone)
      Pool 2: top dna_reserve by DNA-ref count among non-pool-1 lessons (resolve dangling)

    Args:
        max_per_domain: If >0, cap seeds per domain to ensure diversity (L-1262).
        dna_reserve: Slots reserved for DNA-coverage seeds. Default 0 (legacy mode).
        yield_data: Per-lesson yield density from compute_yield_potential (L-1249).
    """
    scored = _score_all(lessons, graph, yield_data)

    if dna_reserve > 0:
        centrality_n = top_n - dna_reserve
        # Pool 1: top by centrality score
        pool1 = scored[:centrality_n]
        for s in pool1:
            s["pool"] = "centrality"
        pool1_ids = {s["id"] for s in pool1}
        # Pool 2: top by DNA ref count among remaining, with centrality as tiebreaker
        remaining = [s for s in scored if s["id"] not in pool1_ids and s["dna_refs"] > 0]
        remaining.sort(key=lambda x: (-x["dna_refs"], -x["score"]))
        pool2 = remaining[:dna_reserve]
        for s in pool2:
            s["pool"] = "dna"
        selected = pool1 + pool2
        if max_per_domain > 0:
            selected = _apply_domain_cap(selected, max_per_domain, top_n)
        return selected

    if max_per_domain > 0:
        return _apply_domain_cap(scored, max_per_domain, top_n)

    return scored[:top_n]


def _apply_domain_cap(scored: list[dict], max_per_domain: int,
                      top_n: int) -> list[dict]:
    """Cap seeds per domain for diversity (L-1262)."""
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


def main():
    top_n = 10
    json_mode = "--json" in sys.argv
    diverse = "--diverse" in sys.argv
    no_dna = "--no-dna-reserve" in sys.argv
    use_yield = "--yield" in sys.argv
    copy_dir = None
    max_per_domain = 2 if diverse else 0
    dna_reserve = 0 if no_dna else top_n // 2

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--top" and i < len(sys.argv) - 1:
            top_n = int(sys.argv[i + 1])
            if not no_dna and "--dna-reserve" not in sys.argv:
                dna_reserve = top_n // 2
        if arg == "--copy" and i < len(sys.argv) - 1:
            copy_dir = Path(sys.argv[i + 1])
        if arg == "--max-per-domain" and i < len(sys.argv) - 1:
            max_per_domain = int(sys.argv[i + 1])
        if arg == "--dna-reserve" and i < len(sys.argv) - 1:
            dna_reserve = int(sys.argv[i + 1])

    # Parse all lessons
    lesson_files = sorted(LESSONS_DIR.glob("L-*.md"))
    lessons = [parse_lesson(f) for f in lesson_files]

    # Build citation graph
    graph = build_citation_graph(lessons)

    # Compute yield potentials if requested (L-1249, L-1261)
    yield_data = None
    if use_yield:
        yield_data = compute_yield_potential(lessons, graph)

    # Score and rank
    seeds = score_lessons(lessons, graph, top_n, max_per_domain=max_per_domain,
                          dna_reserve=dna_reserve, yield_data=yield_data)

    if json_mode:
        unique_domains = len({s["domain"] for s in seeds if s["domain"]})
        dna_refs_map = count_dna_references()
        all_dna_lrefs = set(dna_refs_map.keys())
        seed_ids = {s["id"] for s in seeds}
        dna_coverage = len(seed_ids & all_dna_lrefs)
        out = {"seeds": seeds, "total_lessons": len(lessons),
               "total_edges": sum(graph["in_degree"].values()),
               "unique_seed_domains": unique_domains,
               "max_per_domain": max_per_domain,
               "dna_reserve": dna_reserve,
               "yield_scoring": use_yield,
               "dna_coverage": f"{dna_coverage}/{len(all_dna_lrefs)}",
               "dna_coverage_pct": round(100 * dna_coverage / max(len(all_dna_lrefs), 1), 1)}
        print(json.dumps(out, indent=2))
        return 0

    # Print report
    total_edges = sum(graph["in_degree"].values())
    mode_parts = []
    if use_yield:
        mode_parts.append("yield-scored")
    if max_per_domain > 0:
        mode_parts.append(f"max {max_per_domain}/domain")
    if dna_reserve > 0:
        mode_parts.append(f"{dna_reserve} DNA-reserve slots")
    mode = f" ({', '.join(mode_parts)})" if mode_parts else ""
    print(f"=== GENESIS SEED SELECTOR (L-1247, L-1259){mode} ===")
    print(f"Corpus: {len(lessons)} lessons, {total_edges} citation edges")
    unique_domains = len({s["domain"] for s in seeds if s["domain"]})
    print(f"Seed domains: {unique_domains} unique")

    # DNA coverage stats
    dna_refs_map = count_dna_references()
    all_dna_lrefs = set(dna_refs_map.keys())
    seed_ids = {s["id"] for s in seeds}
    dna_coverage = len(seed_ids & all_dna_lrefs)
    print(f"DNA coverage: {dna_coverage}/{len(all_dna_lrefs)} L-refs resolved ({100 * dna_coverage / max(len(all_dna_lrefs), 1):.1f}%)")

    if use_yield:
        yield_col = f"  {'Density':>7}  {'Pairs':>5}"
    else:
        yield_col = ""
    print(f"\nTop {len(seeds)} seed lessons:\n")
    print(f"{'Rank':>4}  {'Score':>7}  {'InDeg':>5}  {'OutDeg':>6}  {'Domains':>7}  {'Bridge':>6}  {'DNA':>4}{yield_col}  {'Pool':>10}  {'ID':<8}  Title")
    print("-" * (135 if use_yield else 120))
    for i, s in enumerate(seeds, 1):
        bridge_str = "YES" if s["bridge"] else ""
        pool = s.get("pool", "")
        yc = f"  {s.get('yield_density', 0):7.3f}  {s.get('yield_pairs', 0):5d}" if use_yield else ""
        print(f"{i:4d}  {s['score']:7.1f}  {s['in_degree']:5d}  {s['out_degree']:6d}  {s['domain_reach']:7d}  {bridge_str:>6}  {s.get('dna_refs', 0):4d}{yc}  {pool:>10}  {s['id']:<8}  {s['title'][:45]}")

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
