#!/usr/bin/env python3
"""
personality_audit.py — Measure personality deployment coverage and lesson alignment.

Answers F104: Does personality persistence produce different findings on the same question?

Metrics:
  1. Deployment coverage: which personalities appear in SWARM-LANES dispatch
  2. Lesson alignment: which personality-style content appears in actual lessons
  3. Deployment gap: personalities defined but never dispatched
"""

import os
import re
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PERSONALITIES_DIR = REPO_ROOT / "tools" / "personalities"
SWARM_LANES = REPO_ROOT / "tasks" / "SWARM-LANES.md"
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"

# Patterns that indicate each personality's expected output style
PERSONALITY_LESSON_PATTERNS = {
    "explorer": re.compile(
        r"(open[s ]|new frontier|further question|see also F-|at least two new)", re.I
    ),
    "skeptic": re.compile(
        r"(falsif|disprove|did NOT|was WRONG|no evidence|3 independent|not confirmed)", re.I
    ),
    "synthesizer": re.compile(
        r"(connects to L-|see also L-|subsumes|same pattern as|structural equiv)", re.I
    ),
    "builder": re.compile(
        r"(tools/|workspace/|\.py built|\.py created|script|artifact committed)", re.I
    ),
    "adversary": re.compile(
        r"(CHALLENGED:|belief test|stress.test|tried to falsify|survived scrutiny)", re.I
    ),
    "harvest-expert": re.compile(
        r"(harvest|diff classification|expect.*actual|all-outcomes)", re.I
    ),
    "domain-expert": re.compile(
        r"(domain expert|isomorphism|F-[A-Z]{2,5}\d|cross-domain)", re.I
    ),
}


def load_personalities() -> list[str]:
    """Return list of personality names (stem of .md files)."""
    return [p.stem for p in sorted(PERSONALITIES_DIR.glob("*.md"))]


def audit_swarm_lanes(personalities: list[str]) -> dict[str, int]:
    """Count how many SWARM-LANES rows reference each personality."""
    with open(SWARM_LANES) as f:
        content = f.read().lower()
    counts = {}
    for p in personalities:
        counts[p] = content.count(p.lower())
    return counts


def audit_lesson_alignment(personalities: list[str]) -> dict[str, dict]:
    """For each personality, count lessons with matching content patterns."""
    lessons = sorted(LESSONS_DIR.glob("L-*.md"))
    total = len(lessons)

    results = {}
    for p in personalities:
        if p not in PERSONALITY_LESSON_PATTERNS:
            results[p] = {"hits": 0, "total": total, "pct": 0.0, "no_pattern": True}
            continue
        pat = PERSONALITY_LESSON_PATTERNS[p]
        hits = sum(1 for ln in lessons if pat.search(ln.read_text(errors="replace")))
        results[p] = {"hits": hits, "total": total, "pct": round(100 * hits / total, 1)}
    return results


def identify_deployment_gap(lane_counts: dict[str, int]) -> list[str]:
    """Return personalities defined but with zero SWARM-LANES citations."""
    return [p for p, c in lane_counts.items() if c == 0]


def main():
    parser = argparse.ArgumentParser(description="Audit personality deployment + lesson alignment")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--gap-only", action="store_true", help="Show only undeployed personalities")
    args = parser.parse_args()

    personalities = load_personalities()
    lane_counts = audit_swarm_lanes(personalities)
    lesson_alignment = audit_lesson_alignment(personalities)
    gap = identify_deployment_gap(lane_counts)

    if args.gap_only:
        for p in gap:
            print(p)
        return

    if args.json:
        out = {
            "personalities_defined": len(personalities),
            "deployment_gap": gap,
            "gap_count": len(gap),
            "lane_counts": lane_counts,
            "lesson_alignment": lesson_alignment,
        }
        print(json.dumps(out, indent=2))
        return

    # Human-readable report
    print(f"=== Personality Audit ===")
    print(f"Personalities defined: {len(personalities)}")
    print(f"Deployment gap (zero SWARM-LANES): {len(gap)}/{len(personalities)}\n")

    print(f"{'Personality':<28} {'Lanes':>6}  {'Lesson%':>8}  {'Status'}")
    print("-" * 58)
    for p in sorted(personalities, key=lambda x: -lane_counts.get(x, 0)):
        lc = lane_counts.get(p, 0)
        la = lesson_alignment.get(p, {})
        pct = la.get("pct", "n/a")
        no_pat = la.get("no_pattern", False)
        status = "DEPLOYED" if lc > 0 else "ORPHAN"
        pct_str = f"{pct}%" if not no_pat else "  n/a"
        print(f"  {p:<26} {lc:>6}  {pct_str:>8}  {status}")

    print()
    if gap:
        print(f"ORPHANED (never dispatched): {', '.join(gap)}")
        print()

    print("Implication for F104:")
    if len(gap) > len(personalities) // 2:
        print(
            "  BLOCKED — F104 cannot be answered; majority of personalities are never dispatched.\n"
            "  Experiment requires dispatching at least Explorer + Skeptic on same frontier question."
        )
    else:
        print("  PARTIAL — some personalities deployed; cross-personality comparison possible.")


if __name__ == "__main__":
    main()
