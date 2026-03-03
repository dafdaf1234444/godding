#!/usr/bin/env python3
"""knowledge_recombine.py — Find knowledge recombination candidates via citation graph.

Sexual reproduction for knowledge: two lessons that share common citations but
don't cite each other have a "semantic gap" — the space between them is where
a new lesson could be born. This is the missing recombination mechanism
identified in COUNCIL-DNA-S342 (SIG-9) and requested by SIG-62.

Usage:
  python3 tools/knowledge_recombine.py              # top-10 recombination candidates
  python3 tools/knowledge_recombine.py --top 20     # top 20
  python3 tools/knowledge_recombine.py --cross-only # only cross-domain pairs
  python3 tools/knowledge_recombine.py --ranked     # yield-scored ranking (L-1249)
  python3 tools/knowledge_recombine.py --json       # JSON output for experiments
  python3 tools/knowledge_recombine.py --stats      # graph statistics

Output:
  Ranked list of lesson pairs with shared citations, domain distance, and
  recombination potential score. Each pair is a candidate for synthesizing
  a novel insight that bridges the two parent lessons.

Theory:
  Knowledge swarming requires three mechanisms (L-601, ISO-19):
    1. Selection — compact.py (exists)
    2. Propagation — citation graph (exists)
    3. Recombination — THIS TOOL (new)
  Without recombination, knowledge reproduces only asexually (sessions write
  lessons). This tool provides the mate-selection mechanism.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
CITE_RE = re.compile(r"\bL-(\d+)\b")


def parse_lesson(path: Path) -> dict | None:
    """Parse a lesson file into structured data."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    num_m = re.search(r"\d+", path.stem)
    if not num_m:
        return None

    title_m = re.match(r"^# L-\d+:\s*(.+)", text)
    title = title_m.group(1).strip() if title_m else ""

    header = "\n".join(text.splitlines()[:5])

    sharpe_m = re.search(r"Sharpe\*{0,2}:\s*(\d+)", header)
    sharpe = int(sharpe_m.group(1)) if sharpe_m else 0

    level_m = re.search(r"Level\*{0,2}:\s*(L[1-5])", header, re.I)
    if not level_m:
        level_m = re.search(r"\blevel[=:]\s*(L[1-5])\b", text[:200], re.I)
    level = level_m.group(1).upper() if level_m else "L2"

    domain_m = re.search(r"Domain\*{0,2}:\s*([^\n|]+)", header)
    domains = []
    if domain_m:
        raw = domain_m.group(1).strip()
        domains = [d.strip() for d in raw.split(",")]
    primary_domain = domains[0] if domains else "unknown"

    sess_m = re.search(r"Session\*{0,2}:\s*S(\d+)", header)
    session = int(sess_m.group(1)) if sess_m else 0

    own_id = f"L-{num_m.group()}"
    all_refs = {f"L-{m}" for m in CITE_RE.findall(text) if f"L-{m}" != own_id}

    return {
        "id": own_id,
        "title": title,
        "sharpe": sharpe,
        "level": level,
        "domain": primary_domain,
        "domains": domains,
        "session": session,
        "refs": all_refs,
    }


def load_lessons() -> list[dict]:
    """Load and parse all lessons."""
    lessons = []
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        parsed = parse_lesson(f)
        if parsed:
            lessons.append(parsed)
    return lessons


def find_missing_edges(lessons: list[dict], min_shared: int = 2) -> list[dict]:
    """Find lesson pairs with shared citations but no direct link.

    These are recombination candidates: semantically related (shared citations)
    but not yet connected (no direct citation). The gap between them is where
    a new insight could emerge.
    """
    by_id = {l["id"]: l for l in lessons}
    candidates = []

    for i, a in enumerate(lessons):
        a_refs = a["refs"]
        if len(a_refs) < min_shared:
            continue

        for b in lessons[i + 1:]:
            # Skip if they already cite each other
            if b["id"] in a_refs or a["id"] in b["refs"]:
                continue

            b_refs = b["refs"]
            if len(b_refs) < min_shared:
                continue

            shared = a_refs & b_refs
            if len(shared) < min_shared:
                continue

            # Score the recombination potential
            cross_domain = a["domain"] != b["domain"]
            domain_bonus = 2.0 if cross_domain else 1.0
            avg_sharpe = (a["sharpe"] + b["sharpe"]) / 2
            quality = max(avg_sharpe, 1)

            # Shared hub lessons (high in-degree) are less informative bridges
            # than shared niche lessons — weight by inverse frequency
            score = len(shared) * domain_bonus * quality

            candidates.append({
                "parent_a": a["id"],
                "parent_b": b["id"],
                "title_a": a["title"][:60],
                "title_b": b["title"][:60],
                "domain_a": a["domain"],
                "domain_b": b["domain"],
                "shared_refs": sorted(shared),
                "shared_count": len(shared),
                "cross_domain": cross_domain,
                "avg_sharpe": avg_sharpe,
                "score": round(score, 1),
            })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates


def compute_yield_scores(candidates: list[dict], lessons: list[dict]) -> list[dict]:
    """Apply L-1249 yield model to rank by predicted bridging probability.

    Yield: P(bridge) ≈ 0.058 × (shared/2)^1.5 × sharpe_bonus × level_bonus × cross_factor
    L-1249: cross-domain anti-correlated with bridging (0.80) but higher quality.
    """
    by_id = {l["id"]: l for l in lessons}
    level_num = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}

    for c in candidates:
        shared = c["shared_count"]
        avg_sharpe = c["avg_sharpe"]
        a_level = level_num.get(by_id.get(c["parent_a"], {}).get("level", "L2"), 2)
        b_level = level_num.get(by_id.get(c["parent_b"], {}).get("level", "L2"), 2)
        avg_level = (a_level + b_level) / 2

        sharpe_bonus = 1 + 0.15 * (avg_sharpe - 7)
        level_bonus = 1 + 0.4 * (avg_level - 2)
        cross_factor = 0.80 if c["cross_domain"] else 1.0

        c["yield_score"] = round(
            0.058 * (shared / 2) ** 1.5 * sharpe_bonus * level_bonus * cross_factor, 4
        )
        c["avg_level"] = avg_level

    candidates.sort(key=lambda c: c["yield_score"], reverse=True)
    return candidates


def graph_stats(lessons: list[dict]) -> dict:
    """Compute citation graph statistics relevant to recombination."""
    total = len(lessons)
    all_refs = set()
    orphans = []
    edges = 0
    by_id = {l["id"]: l for l in lessons}

    for l in lessons:
        valid_refs = l["refs"] & set(by_id.keys())
        edges += len(valid_refs)
        all_refs |= valid_refs
        if not valid_refs:
            orphans.append(l["id"])

    # Domain distribution
    domain_counts = Counter(l["domain"] for l in lessons)

    # Cross-domain citation rate
    cross_domain_edges = 0
    for l in lessons:
        for ref in l["refs"]:
            if ref in by_id and by_id[ref]["domain"] != l["domain"]:
                cross_domain_edges += 1

    return {
        "total_lessons": total,
        "total_edges": edges,
        "avg_out_degree": round(edges / total, 2) if total else 0,
        "orphan_count": len(orphans),
        "orphan_pct": round(100 * len(orphans) / total, 1) if total else 0,
        "cross_domain_edge_pct": round(100 * cross_domain_edges / edges, 1) if edges else 0,
        "domain_count": len(domain_counts),
        "top_domains": dict(domain_counts.most_common(5)),
    }


def main():
    parser = argparse.ArgumentParser(description="Knowledge recombination engine")
    parser.add_argument("--top", type=int, default=10, help="Number of candidates to show")
    parser.add_argument("--min-shared", type=int, default=2, help="Min shared citations")
    parser.add_argument("--cross-only", action="store_true", help="Only cross-domain pairs")
    parser.add_argument("--ranked", action="store_true", help="Yield-scored ranking (L-1249)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--stats", action="store_true", help="Graph statistics only")
    args = parser.parse_args()

    lessons = load_lessons()
    if not lessons:
        print("No lessons found.", file=sys.stderr)
        return 1

    if args.stats:
        stats = graph_stats(lessons)
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"=== Citation Graph Stats (n={stats['total_lessons']}) ===")
            print(f"  Edges: {stats['total_edges']} (avg out-degree {stats['avg_out_degree']})")
            print(f"  Orphans: {stats['orphan_count']} ({stats['orphan_pct']}%)")
            print(f"  Cross-domain edges: {stats['cross_domain_edge_pct']}%")
            print(f"  Domains: {stats['domain_count']}")
            for d, c in stats["top_domains"].items():
                print(f"    {d}: {c}")
        return 0

    candidates = find_missing_edges(lessons, min_shared=args.min_shared)

    if args.cross_only:
        candidates = [c for c in candidates if c["cross_domain"]]

    if args.ranked:
        candidates = compute_yield_scores(candidates, lessons)

    top = candidates[:args.top]

    if args.json:
        out = {
            "total_candidates": len(candidates),
            "cross_domain_candidates": sum(1 for c in candidates if c["cross_domain"]),
            "ranked": args.ranked,
            "top": top,
        }
        print(json.dumps(out, indent=2))
        return 0

    total_cross = sum(1 for c in candidates if c["cross_domain"])
    mode = "Yield-Ranked (L-1249)" if args.ranked else "Citation Overlap"
    print(f"=== Knowledge Recombination Candidates ({mode}) ===")
    print(f"Total missing edges: {len(candidates)} ({total_cross} cross-domain)")
    print()

    for i, c in enumerate(top, 1):
        cross = " [CROSS-DOMAIN]" if c["cross_domain"] else ""
        if args.ranked:
            print(f"  [{i}] yield={c['yield_score']:.4f} (raw={c['score']}){cross}")
        else:
            print(f"  [{i}] score={c['score']}{cross}")
        print(f"      A: {c['parent_a']} ({c['domain_a']}): {c['title_a']}")
        print(f"      B: {c['parent_b']} ({c['domain_b']}): {c['title_b']}")
        print(f"      Shared ({c['shared_count']}): {', '.join(c['shared_refs'])}")
        print(f"      Question: What connects {c['parent_a']} and {c['parent_b']}?")
        print()

    if len(candidates) > args.top:
        print(f"  ... {len(candidates) - args.top} more candidates (use --top N)")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
