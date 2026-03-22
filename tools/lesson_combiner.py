#!/usr/bin/env python3
"""lesson_combiner.py — Find and propose lesson combinations (N→1 merges).

Combiner is the FOURTH knowledge mechanism (L-601, ISO-19):
  1. Selection  — compact.py (prune weak)
  2. Propagation — citation graph (spread)
  3. Recombination — knowledge_recombine.py (create novel from gaps)
  4. Combination — THIS TOOL (compress redundancy into density)

Recombination finds GAPS between unlinked lessons → new insights.
Combination finds OVERLAP between linked lessons → fewer, denser lessons.

Both reduce attention cost (N=1203, capacity=2.4x threshold), but through
opposite mechanisms: recombination adds quality, combination removes quantity.

Usage:
  python3 tools/lesson_combiner.py                  # top-10 combine clusters
  python3 tools/lesson_combiner.py --top 20         # more clusters
  python3 tools/lesson_combiner.py --min-overlap 3  # stricter overlap
  python3 tools/lesson_combiner.py --domain meta    # filter by domain
  python3 tools/lesson_combiner.py --expired-only   # only EXPIRED lessons
  python3 tools/lesson_combiner.py --json            # machine-readable
  python3 tools/lesson_combiner.py --detail L-601   # show detail for specific lesson's cluster

Output:
  Ranked clusters of lessons that overlap enough to be combined.
  Each cluster shows: member lessons, shared citations, overlap score,
  and a suggested combination strategy (absorb, merge, supersede).
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
EXPIRED_RE = re.compile(r"\b(EXPIRED|SUPERSEDED)\b", re.I)


def parse_lesson(path: Path) -> dict | None:
    """Parse a lesson file into structured data with full text."""
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

    expired = bool(EXPIRED_RE.search(text[:500]))

    # Extract keywords from title for semantic similarity
    words = set(re.findall(r"[a-z][a-z0-9_-]{2,}", title.lower()))
    stopwords = {"the", "and", "for", "that", "this", "with", "from", "are", "was",
                 "not", "but", "has", "have", "can", "does", "than", "into", "its"}
    keywords = words - stopwords

    lines = len(text.splitlines())

    return {
        "id": own_id,
        "num": int(num_m.group()),
        "title": title,
        "sharpe": sharpe,
        "level": level,
        "domain": primary_domain,
        "domains": domains,
        "session": session,
        "refs": all_refs,
        "expired": expired,
        "keywords": keywords,
        "lines": lines,
        "path": str(path),
    }


def load_lessons() -> list[dict]:
    """Load and parse all lessons."""
    lessons = []
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        parsed = parse_lesson(f)
        if parsed:
            lessons.append(parsed)
    return lessons


def compute_overlap(a: dict, b: dict) -> dict:
    """Compute overlap between two lessons — higher means more combinable."""
    shared_refs = a["refs"] & b["refs"]
    shared_kw = a["keywords"] & b["keywords"]

    # Direct citation (a cites b or vice versa) is strong overlap signal
    mutual_cite = b["id"] in a["refs"] or a["id"] in b["refs"]
    cite_bonus = 2.0 if mutual_cite else 0.0

    # Same domain bonus
    domain_bonus = 1.5 if a["domain"] == b["domain"] else 0.5

    # Keyword overlap (semantic similarity proxy)
    kw_union = a["keywords"] | b["keywords"]
    kw_jaccard = len(shared_kw) / len(kw_union) if kw_union else 0

    # Citation overlap (structural similarity)
    ref_union = a["refs"] | b["refs"]
    ref_jaccard = len(shared_refs) / len(ref_union) if ref_union else 0

    # Combined score: structural + semantic + citation + domain
    score = (
        len(shared_refs) * 2.0          # shared citations
        + kw_jaccard * 5.0              # keyword similarity
        + ref_jaccard * 3.0             # citation jaccard
        + cite_bonus                    # direct citation
        + domain_bonus                  # domain match
    )

    return {
        "shared_refs": shared_refs,
        "shared_kw": shared_kw,
        "mutual_cite": mutual_cite,
        "kw_jaccard": round(kw_jaccard, 3),
        "ref_jaccard": round(ref_jaccard, 3),
        "score": round(score, 2),
    }


def find_clusters(lessons: list[dict], min_overlap: float = 4.0,
                  domain_filter: str | None = None,
                  expired_only: bool = False) -> list[dict]:
    """Find clusters of combinable lessons using greedy agglomeration.

    Strategy: build pairwise overlap graph, then greedily merge highest-overlap
    pairs into clusters. Each cluster is a combination candidate.
    """
    filtered = lessons
    if domain_filter:
        filtered = [l for l in filtered if l["domain"] == domain_filter]
    if expired_only:
        filtered = [l for l in filtered if l["expired"]]

    by_id = {l["id"]: l for l in filtered}

    # Build overlap edges above threshold
    edges = []
    for i, a in enumerate(filtered):
        for b in filtered[i + 1:]:
            ov = compute_overlap(a, b)
            if ov["score"] >= min_overlap:
                edges.append((a["id"], b["id"], ov))

    edges.sort(key=lambda e: e[2]["score"], reverse=True)

    # Greedy agglomeration: each lesson belongs to at most one cluster
    assigned = {}  # lesson_id → cluster_id
    clusters = {}  # cluster_id → set of lesson_ids

    for a_id, b_id, ov in edges:
        a_cluster = assigned.get(a_id)
        b_cluster = assigned.get(b_id)

        if a_cluster is None and b_cluster is None:
            # New cluster
            cid = a_id
            clusters[cid] = {a_id, b_id}
            assigned[a_id] = cid
            assigned[b_id] = cid
        elif a_cluster is not None and b_cluster is None:
            # Add b to a's cluster (limit cluster size to 6)
            if len(clusters[a_cluster]) < 6:
                clusters[a_cluster].add(b_id)
                assigned[b_id] = a_cluster
        elif a_cluster is None and b_cluster is not None:
            if len(clusters[b_cluster]) < 6:
                clusters[b_cluster].add(a_id)
                assigned[a_id] = b_cluster
        # If both assigned, don't merge clusters (keeps them manageable)

    # Score and describe each cluster
    results = []
    for cid, members in clusters.items():
        if len(members) < 2:
            continue

        member_lessons = [by_id[mid] for mid in members if mid in by_id]
        if len(member_lessons) < 2:
            continue

        # Cluster-level metrics
        all_refs = set()
        all_kw = set()
        total_lines = 0
        max_sharpe = 0
        max_level = "L1"
        level_ord = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}

        for ml in member_lessons:
            all_refs |= ml["refs"]
            all_kw |= ml["keywords"]
            total_lines += ml["lines"]
            max_sharpe = max(max_sharpe, ml["sharpe"])
            if level_ord.get(ml["level"], 2) > level_ord.get(max_level, 1):
                max_level = ml["level"]

        # Internal citations (members citing each other)
        member_ids = {ml["id"] for ml in member_lessons}
        internal_cites = sum(
            1 for ml in member_lessons
            for ref in ml["refs"]
            if ref in member_ids
        )

        # Combination strategy
        if len(member_lessons) == 2:
            strategy = "merge"  # 2 lessons → 1 combined
        elif internal_cites >= len(member_lessons):
            strategy = "absorb"  # highly interconnected → absorb into strongest
        else:
            strategy = "supersede"  # loosely connected → new lesson supersedes all

        # Estimate savings
        est_combined_lines = min(20, total_lines // len(member_lessons) + 5)
        savings = total_lines - est_combined_lines

        # Cluster overlap score (average pairwise)
        pair_scores = []
        for i, a in enumerate(member_lessons):
            for b in member_lessons[i + 1:]:
                ov = compute_overlap(a, b)
                pair_scores.append(ov["score"])
        avg_overlap = sum(pair_scores) / len(pair_scores) if pair_scores else 0

        results.append({
            "cluster_id": cid,
            "members": sorted(member_ids, key=lambda x: int(re.search(r"\d+", x).group())),
            "member_count": len(member_lessons),
            "titles": {ml["id"]: ml["title"][:70] for ml in member_lessons},
            "domain": Counter(ml["domain"] for ml in member_lessons).most_common(1)[0][0],
            "strategy": strategy,
            "avg_overlap": round(avg_overlap, 2),
            "internal_cites": internal_cites,
            "total_lines": total_lines,
            "est_savings": savings,
            "max_sharpe": max_sharpe,
            "max_level": max_level,
            "shared_keywords": sorted(all_kw)[:10],
        })

    results.sort(key=lambda c: c["avg_overlap"] * c["member_count"], reverse=True)
    return results


def detail_cluster(lessons: list[dict], lesson_id: str) -> dict | None:
    """Show detailed combination info for a specific lesson's cluster."""
    by_id = {l["id"]: l for l in lessons}
    target = by_id.get(lesson_id)
    if not target:
        return None

    # Find all lessons with significant overlap to target
    related = []
    for l in lessons:
        if l["id"] == lesson_id:
            continue
        ov = compute_overlap(target, l)
        if ov["score"] >= 3.0:
            related.append({
                "id": l["id"],
                "title": l["title"][:70],
                "domain": l["domain"],
                "sharpe": l["sharpe"],
                "overlap": ov,
            })

    related.sort(key=lambda r: r["overlap"]["score"], reverse=True)

    return {
        "target": {
            "id": target["id"],
            "title": target["title"],
            "domain": target["domain"],
            "sharpe": target["sharpe"],
            "refs": sorted(target["refs"]),
        },
        "related": related[:10],
    }


def main():
    parser = argparse.ArgumentParser(description="Lesson combination engine")
    parser.add_argument("--top", type=int, default=10, help="Number of clusters")
    parser.add_argument("--min-overlap", type=float, default=4.0, help="Minimum overlap score")
    parser.add_argument("--domain", type=str, help="Filter by domain")
    parser.add_argument("--expired-only", action="store_true", help="Only EXPIRED lessons")
    parser.add_argument("--detail", type=str, help="Show detail for specific lesson")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--stats", action="store_true", help="Summary statistics only")
    args = parser.parse_args()

    lessons = load_lessons()
    if not lessons:
        print("No lessons found.", file=sys.stderr)
        return 1

    if args.detail:
        result = detail_cluster(lessons, args.detail)
        if not result:
            print(f"Lesson {args.detail} not found.", file=sys.stderr)
            return 1
        if args.json:
            # Convert sets to lists for JSON
            print(json.dumps(result, indent=2, default=list))
        else:
            t = result["target"]
            print(f"=== Combination Detail: {t['id']} ===")
            print(f"  {t['title']}")
            print(f"  Domain: {t['domain']} | Sharpe: {t['sharpe']}")
            print(f"  Refs: {', '.join(t['refs'][:8])}")
            print()
            for r in result["related"]:
                ov = r["overlap"]
                mut = " [MUTUAL]" if ov["mutual_cite"] else ""
                print(f"  → {r['id']} (overlap={ov['score']}){mut}")
                print(f"    {r['title']}")
                print(f"    shared_refs={len(ov['shared_refs'])} kw_jacc={ov['kw_jaccard']}")
                print()
        return 0

    clusters = find_clusters(
        lessons,
        min_overlap=args.min_overlap,
        domain_filter=args.domain,
        expired_only=args.expired_only,
    )

    if args.stats:
        total_combinable = sum(c["member_count"] for c in clusters)
        total_savings = sum(c["est_savings"] for c in clusters)
        if args.json:
            print(json.dumps({
                "total_lessons": len(lessons),
                "total_clusters": len(clusters),
                "total_combinable": total_combinable,
                "total_savings_lines": total_savings,
                "avg_cluster_size": round(total_combinable / len(clusters), 1) if clusters else 0,
            }, indent=2))
        else:
            print(f"=== Combination Stats ===")
            print(f"  Lessons: {len(lessons)}")
            print(f"  Clusters found: {len(clusters)}")
            print(f"  Combinable lessons: {total_combinable}")
            print(f"  Est. line savings: {total_savings}")
            print(f"  Avg cluster size: {total_combinable / len(clusters):.1f}" if clusters else "  No clusters")
        return 0

    top = clusters[:args.top]

    if args.json:
        print(json.dumps({
            "total_clusters": len(clusters),
            "showing": len(top),
            "clusters": top,
        }, indent=2, default=list))
        return 0

    strategy_icons = {"merge": "⊕", "absorb": "⊂", "supersede": "↑"}
    print(f"=== Lesson Combination Candidates ===")
    print(f"Total clusters: {len(clusters)} ({sum(c['member_count'] for c in clusters)} lessons)")
    print(f"Est. total line savings: {sum(c['est_savings'] for c in clusters)}")
    print()

    for i, c in enumerate(top, 1):
        icon = strategy_icons.get(c["strategy"], "?")
        print(f"  [{i}] {icon} {c['strategy'].upper()} — {c['member_count']} lessons, "
              f"overlap={c['avg_overlap']}, ~{c['est_savings']}L saved")
        print(f"      domain={c['domain']} max_sharpe={c['max_sharpe']} level={c['max_level']}")
        for mid, title in sorted(c["titles"].items(),
                                  key=lambda x: int(re.search(r"\d+", x[0]).group())):
            print(f"      • {mid}: {title}")
        if c["shared_keywords"]:
            print(f"      keywords: {', '.join(c['shared_keywords'][:6])}")
        print()

    if len(clusters) > args.top:
        print(f"  ... {len(clusters) - args.top} more clusters (use --top N)")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
