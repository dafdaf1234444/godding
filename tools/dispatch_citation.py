#!/usr/bin/env python3
"""Citation-based quality signal for dispatch scoring (L-1622).

L-1622 FALSIFIED self-rated Sharpe as a quality signal (rho=0.154, CV=0.168).
This module provides citation in-degree as an externalized alternative:
lessons cited more by other lessons are empirically more useful.

Used by dispatch_scoring.py to blend citation quality with dampened Sharpe.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"

_citation_cache = None


def build_citation_indegree():
    """Build citation in-degree map: L-NNN -> count of lessons that cite it."""
    global _citation_cache
    if _citation_cache is not None:
        return _citation_cache

    indegree = {}
    if not LESSONS_DIR.exists():
        _citation_cache = {}
        return {}

    for f in LESSONS_DIR.iterdir():
        if not f.name.startswith("L-") or not f.name.endswith(".md"):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if text.startswith("<!--"):
            continue
        lid = f.name.replace(".md", "")
        refs = set(re.findall(r"L-\d+", text))
        refs.discard(lid)
        for ref in refs:
            indegree[ref] = indegree.get(ref, 0) + 1

    _citation_cache = indegree
    return indegree


def get_lesson_citation_count(lid):
    """Return citation in-degree for a lesson ID (e.g. '1622' or 'L-1622')."""
    indegree = build_citation_indegree()
    key = lid if lid.startswith("L-") else f"L-{lid}"
    return indegree.get(key, 0)


if __name__ == "__main__":
    indegree = build_citation_indegree()
    total_cites = sum(indegree.values())
    avg = total_cites / len(indegree) if indegree else 0

    print(f"Citation graph: {len(indegree)} cited lessons")
    print(f"Total citations: {total_cites}")
    print(f"Average in-degree: {avg:.2f}")

    top = sorted(indegree.items(), key=lambda x: -x[1])[:10]
    print("\nTop 10 most-cited:")
    for lid, count in top:
        print(f"  {lid}: {count}")
