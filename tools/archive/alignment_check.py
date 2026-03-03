#!/usr/bin/env python3
"""
alignment_check.py — Check alignment between parent and child swarms.

Usage:
    python3 tools/alignment_check.py           # summary
    python3 tools/alignment_check.py --detail   # show all child beliefs

Checks:
1. Pending belief-challenges from children (not yet in PHILOSOPHY.md)
2. Children with observed findings on topics where parent has theorized beliefs
3. Child belief counts and alignment summary

Part of F113: bidirectional alignment across node types.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PARENT_DEPS = REPO / "beliefs" / "DEPS.md"
CHILDREN_DIR = REPO / "experiments" / "children"
BULLETINS_DIR = REPO / "experiments" / "inter-swarm" / "bulletins"
PHILOSOPHY = REPO / "beliefs" / "PHILOSOPHY.md"

try:
    from swarm_io import read_text as _read
    _has_swarm_io = True
except ImportError:
    try:
        from tools.swarm_io import read_text as _read
        _has_swarm_io = True
    except ImportError:
        _has_swarm_io = False

if not _has_swarm_io:
    def _read(path: Path) -> str:
        """Read UTF-8 text robustly across host defaults."""
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""


def parse_beliefs(deps_path: Path) -> list[dict]:
    """Extract beliefs from a DEPS.md file."""
    if not deps_path.exists():
        return []
    text = _read(deps_path)
    beliefs = []
    current = None
    for line in text.split("\n"):
        m = re.match(r"### (B\d+):\s*(.+)", line)
        if m:
            if current and current.get("evidence"):
                beliefs.append(current)
            current = {"id": m.group(1), "text": m.group(2), "evidence": None}
        elif current and "**Evidence**" in line:
            ev = re.search(r"(observed|theorized)", line)
            if ev:
                current["evidence"] = ev.group(1)
        elif current and line.startswith("### ") and not re.match(r"### B\d+:", line):
            if current.get("evidence"):
                beliefs.append(current)
            current = None
    if current and current.get("evidence"):
        beliefs.append(current)
    return beliefs


def get_pending_challenges() -> list[dict]:
    """Find belief-challenge bulletins not yet in PHILOSOPHY.md."""
    if not BULLETINS_DIR.exists():
        return []
    phil_text = _read(PHILOSOPHY) if PHILOSOPHY.exists() else ""
    pending = []
    for f in sorted(BULLETINS_DIR.glob("*.md")):
        child = f.stem
        text = _read(f)
        for m in re.finditer(
            r"# Bulletin from: .+?\nDate: \S+\nType: belief-challenge\n\n## Content\n(.+?)(?:\n---|\Z)",
            text, re.DOTALL,
        ):
            content = m.group(1).strip()
            claim_m = re.match(r"(PHIL-\d+|B-?\d+):", content)
            claim_id = claim_m.group(1) if claim_m else ""
            # Check if child+claim combo already in Challenges table
            already = bool(re.search(
                rf"\|\s*{re.escape(claim_id)}\s*\|\s*{re.escape(child)}\s*\|",
                phil_text,
            )) if claim_id else False
            if not already:
                pending.append({"child": child, "content": content})
    return pending


def keyword_set(text: str) -> set[str]:
    """Extract meaningful keywords from text (5+ chars, no stopwords)."""
    stops = {
        "that", "this", "with", "from", "have", "been", "more", "when",
        "than", "also", "each", "they", "which", "their", "does", "into",
        "only", "most", "across", "should", "between", "without", "using",
        "every", "about", "other", "would", "could", "being", "after",
        "before", "under", "above", "while", "where", "there", "these",
        "those", "based", "first", "scale", "small", "systems", "system",
        "theorem", "sufficient", "knowledge", "memory", "belief",
    }
    words = set(w.lower() for w in re.findall(r"[a-zA-Z]\w{4,}", text))
    return words - stops


def find_topic_overlaps(parent_beliefs: list[dict], child_beliefs: list[dict]) -> list[dict]:
    """Find child observed beliefs that overlap with parent theorized beliefs."""
    parent_theorized = [b for b in parent_beliefs if b["evidence"] == "theorized"]
    child_observed = [b for b in child_beliefs if b["evidence"] == "observed"]
    overlaps = []
    for pb in parent_theorized:
        pk = keyword_set(pb["text"])
        for cb in child_observed:
            ck = keyword_set(cb["text"])
            shared = pk & ck
            if len(shared) >= 3:
                overlaps.append({
                    "parent": pb,
                    "child": cb,
                    "shared_keywords": shared,
                })
    return overlaps


def main():
    detail = "--detail" in sys.argv

    parent_beliefs = parse_beliefs(PARENT_DEPS)
    parent_theorized = [b for b in parent_beliefs if b["evidence"] == "theorized"]
    parent_observed = [b for b in parent_beliefs if b["evidence"] == "observed"]

    print("=== ALIGNMENT CHECK (F113) ===\n")
    print(f"Parent: {len(parent_beliefs)} beliefs ({len(parent_observed)} observed, {len(parent_theorized)} theorized)")

    # 1. Pending challenges
    pending = get_pending_challenges()
    if pending:
        print(f"\n!! {len(pending)} PENDING CHALLENGE(S) from children:")
        for c in pending:
            print(f"   {c['child']}: {c['content'][:80]}")
        print("   Run: python3 tools/propagate_challenges.py --apply")
    else:
        print("\nNo pending challenges from children.")

    # 2. Check each child
    if not CHILDREN_DIR.exists():
        print("\nNo children found.")
        return

    children = sorted(d for d in CHILDREN_DIR.iterdir() if d.is_dir())
    if not children:
        print("\nNo children found.")
        return

    print(f"\n--- Children ({len(children)}) ---")
    total_overlaps = 0
    for child_dir in children:
        child_name = child_dir.name
        child_beliefs = parse_beliefs(child_dir / "beliefs" / "DEPS.md")
        child_obs = [b for b in child_beliefs if b["evidence"] == "observed"]
        child_th = [b for b in child_beliefs if b["evidence"] == "theorized"]

        # Count lessons
        lessons_dir = child_dir / "memory" / "lessons"
        lesson_count = len(list(lessons_dir.glob("L-*.md"))) if lessons_dir.exists() else 0

        print(f"\n  {child_name}: {len(child_beliefs)}B ({len(child_obs)} obs, {len(child_th)} th), {lesson_count}L")

        # Find overlaps with parent theorized beliefs
        overlaps = find_topic_overlaps(parent_beliefs, child_beliefs)
        if overlaps:
            total_overlaps += len(overlaps)
            for ov in overlaps:
                kw = ", ".join(sorted(ov["shared_keywords"])[:5])
                print(f"    -> OVERLAP: child {ov['child']['id']} (observed) vs parent {ov['parent']['id']} (theorized)")
                print(f"       Keywords: {kw}")
                if detail:
                    print(f"       Parent: {ov['parent']['text'][:70]}")
                    print(f"       Child:  {ov['child']['text'][:70]}")

        if detail and child_beliefs:
            for b in child_beliefs:
                print(f"    {b['id']} [{b['evidence']}]: {b['text'][:60]}")

    # Summary
    print(f"\n--- Summary ---")
    print(f"Children: {len(children)} | Pending challenges: {len(pending)} | Topic overlaps: {total_overlaps}")
    if total_overlaps > 0:
        print("Topic overlaps = child has observed evidence on a topic where parent has theorized belief.")
        print("Review these — child may have evidence that confirms or contradicts parent.")
    if not pending and total_overlaps == 0:
        print("Alignment check clean. No contradictions detected.")


if __name__ == "__main__":
    main()
