#!/usr/bin/env python3
"""
merge_back.py — Extract learnings from a child swarm for parent integration.

Usage:
    python3 tools/merge_back.py <child-swarm-dir>

Reads a child swarm's lessons, beliefs, and frontier questions,
then produces a merge report: what the child learned that the
parent doesn't already know. The parent session reviews the
report and decides what to integrate.

This is the "merge-back protocol" for knowledge forks (F21).

Invariant gate (F110-B1): novel rules are checked against beliefs/INVARIANTS.md.
Rules that semantically negate an invariant are flagged CONTESTED and require
human review before integration. They are NOT auto-merged.
"""

import json
import re
import sys
from pathlib import Path

from novelty import check_novelty, content_words, jaccard_similarity, load_parent_rules

REPO_ROOT = Path(__file__).resolve().parent.parent

INVARIANTS_PATH = REPO_ROOT / "beliefs" / "INVARIANTS.md"
# Lower threshold for negation matching — negation phrases are short and specific
CONFLICT_THRESHOLD = 0.3


def load_invariants() -> list[dict]:
    """Load invariants and their negation patterns from beliefs/INVARIANTS.md."""
    if not INVARIANTS_PATH.exists():
        return []
    text = INVARIANTS_PATH.read_text()
    invariants = []
    for block in re.split(r"^## ", text, flags=re.MULTILINE):
        id_m = re.match(r"(I\d+) — (.+)", block)
        if not id_m:
            continue
        inv_id = id_m.group(1)
        inv_name = id_m.group(2).split("\n")[0].strip()
        negated_m = re.search(r"\*\*Negated by\*\*: (.+?)(?:\n|$)", block)
        negation_text = negated_m.group(1).strip() if negated_m else ""
        # Statement = first non-empty line after the header
        body_lines = [l.strip() for l in block.split("\n")[2:] if l.strip() and not l.startswith("**")]
        statement = body_lines[0] if body_lines else ""
        invariants.append({
            "id": inv_id,
            "name": inv_name,
            "statement": statement,
            "negation": negation_text,
        })
    return invariants


def check_invariant_conflicts(rule: str, invariants: list[dict]) -> list[dict]:
    """Check if a rule semantically negates any invariant.

    Returns list of conflicting invariants (empty = no conflict).
    """
    if not rule or not invariants:
        return []
    rule_words = content_words(rule)
    if not rule_words:
        return []
    conflicts = []
    for inv in invariants:
        if not inv["negation"]:
            continue
        neg_words = content_words(inv["negation"])
        sim = jaccard_similarity(rule_words, neg_words)
        if sim >= CONFLICT_THRESHOLD:
            conflicts.append({"id": inv["id"], "name": inv["name"], "sim": sim})
    return conflicts


def extract_child_lessons(child_dir: Path) -> list[dict]:
    """Extract all lessons from a child swarm."""
    lessons = []
    lessons_dir = child_dir / "memory" / "lessons"
    if not lessons_dir.exists():
        return lessons

    for f in sorted(lessons_dir.glob("L-*.md")):
        if f.name == "TEMPLATE.md":
            continue
        text = f.read_text()

        # Extract title
        title_m = re.search(r"^# (L-\d+:.+)$", text, re.MULTILINE)
        # Extract rule
        rule_m = re.search(
            r"## Rule extracted.*?\n(.+?)(?:\n\n|\n##|\Z)",
            text, re.DOTALL
        )
        # Extract what we learned
        learned_m = re.search(
            r"## What we learned.*?\n(.+?)(?:\n\n|\n##|\Z)",
            text, re.DOTALL
        )

        lessons.append({
            "file": f.name,
            "title": title_m.group(1).strip() if title_m else f.stem,
            "rule": rule_m.group(1).strip() if rule_m else "",
            "learned": learned_m.group(1).strip() if learned_m else "",
        })
    return lessons


def extract_child_beliefs(child_dir: Path) -> list[dict]:
    """Extract beliefs from a child swarm."""
    deps = child_dir / "beliefs" / "DEPS.md"
    if not deps.exists():
        return []

    text = deps.read_text()
    beliefs = []
    for m in re.finditer(r"^### (B\d+):\s*(.+)$", text, re.MULTILINE):
        block_start = m.end()
        next_heading = re.search(r"^### B\d+:", text[block_start:], re.MULTILINE)
        block_end = block_start + next_heading.start() if next_heading else len(text)
        block = text[block_start:block_end]

        ev_m = re.search(r"\*\*Evidence\*\*:\s*(\S+)", block, re.I)
        beliefs.append({
            "id": m.group(1),
            "statement": m.group(2).strip(),
            "evidence": ev_m.group(1).strip().lower() if ev_m else "unknown",
        })
    return beliefs


def extract_child_frontier(child_dir: Path) -> list[str]:
    """Extract open frontier questions from a child swarm."""
    frontier = child_dir / "tasks" / "FRONTIER.md"
    if not frontier.exists():
        return []

    text = frontier.read_text()
    return re.findall(r"^\- \*\*F\d+\*\*:\s*(.+)$", text, re.MULTILINE)


def _load_parent_rules() -> list[str]:
    """Load parent's existing principles for dedup."""
    return load_parent_rules(REPO_ROOT / "memory" / "PRINCIPLES.md")


def generate_report(child_dir: Path) -> str:
    """Generate a merge-back report for a child swarm."""
    child_dir = Path(child_dir).resolve()
    lessons = extract_child_lessons(child_dir)
    beliefs = extract_child_beliefs(child_dir)
    frontier = extract_child_frontier(child_dir)
    parent_rules = _load_parent_rules()
    invariants = load_invariants()

    lines = [
        f"# Merge-Back Report: {child_dir.name}",
        f"Generated from: {child_dir}",
        "",
    ]

    # Meta
    meta_path = child_dir / ".swarm_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        lines.append(f"Topic: {meta.get('topic', 'unknown')}")
        lines.append(f"Parent lessons at spawn: {meta.get('spawned_from_lesson_count', '?')}")
        lines.append("")

    # Lessons — novelty check + invariant gate
    lines.append(f"## Lessons ({len(lessons)})")
    novel_count = 0
    contested_count = 0
    for lesson in lessons:
        is_novel, sim, closest = check_novelty(lesson["rule"], parent_rules)
        if is_novel:
            conflicts = check_invariant_conflicts(lesson["rule"], invariants)
            if conflicts:
                contested_count += 1
                inv_ids = ", ".join(c["id"] for c in conflicts)
                marker = f" [CONTESTED: {inv_ids}]"
            else:
                novel_count += 1
                marker = " [NOVEL]"
        else:
            marker = f" [sim={sim:.0%}]"
        lines.append(f"- **{lesson['title']}**{marker}")
        if lesson["rule"]:
            lines.append(f"  Rule: {lesson['rule']}")
        lines.append("")

    lines.append(f"Novel rules: {novel_count}/{len(lessons)}")
    if contested_count:
        lines.append(f"Contested rules (invariant conflicts): {contested_count}/{len(lessons)} — HUMAN REVIEW REQUIRED")
    lines.append("")

    # Beliefs
    lines.append(f"## Beliefs ({len(beliefs)})")
    for b in beliefs:
        lines.append(f"- **{b['id']}**: {b['statement']} ({b['evidence']})")
    lines.append("")

    # Frontier
    if frontier:
        lines.append(f"## Open Frontier Questions ({len(frontier)})")
        for q in frontier:
            lines.append(f"- {q}")
        lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    if contested_count > 0:
        lines.append(
            f"- ⚠ {contested_count} rule(s) CONTESTED — conflict with INVARIANTS.md. "
            "Do NOT auto-integrate. Requires human review and explicit override."
        )
    if novel_count > 0:
        lines.append(f"- {novel_count} novel rule(s) found — review for parent integration")
    if not novel_count and not contested_count:
        lines.append("- No novel rules — child confirmed existing knowledge")

    observed = sum(1 for b in beliefs if b["evidence"] == "observed")
    if observed > 0:
        lines.append(f"- {observed} belief(s) upgraded to observed — cross-validate with parent")

    if frontier:
        lines.append(f"- {len(frontier)} open question(s) — consider adding to parent FRONTIER")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    child_dir = Path(sys.argv[1])
    if not child_dir.exists():
        print(f"Error: {child_dir} does not exist")
        sys.exit(1)

    report = generate_report(child_dir)
    print(report)

    # Also save the report
    report_path = REPO_ROOT / "experiments" / "merge-reports" / f"{child_dir.name}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report + "\n")
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
