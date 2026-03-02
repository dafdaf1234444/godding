#!/usr/bin/env python3
"""
propagate_challenges.py — Pull belief-challenges from child bulletins into parent files.

Usage:
    python3 tools/propagate_challenges.py          # dry-run: show pending challenges
    python3 tools/propagate_challenges.py --apply  # write new challenges

Children write challenges with:
    python3 tools/bulletin.py write <child-name> belief-challenge "PHIL-N: challenge text"
    python3 tools/bulletin.py write <child-name> belief-challenge "B-N: challenge text"

PHIL-N challenges → PHILOSOPHY.md Challenges table
B-N challenges → beliefs/CHALLENGES.md (created if absent)

This tool closes the bidirectional challenge loop (F113): children can challenge
parent beliefs, not just report discoveries. Run at harvest time or any session start.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BULLETINS_DIR = REPO_ROOT / "experiments" / "inter-swarm" / "bulletins"
PHILOSOPHY_PATH = REPO_ROOT / "beliefs" / "PHILOSOPHY.md"
CHALLENGES_PATH = REPO_ROOT / "beliefs" / "CHALLENGES.md"

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
        """Read text deterministically across runtimes/locales."""
        return path.read_text(encoding="utf-8", errors="replace")


def _write(path: Path, text: str):
    """Write UTF-8 so later reads are locale-independent."""
    path.write_text(text, encoding="utf-8")


def collect_challenges() -> list[dict]:
    """Read all bulletins and return belief-challenge entries not yet in PHILOSOPHY.md."""
    if not BULLETINS_DIR.exists():
        return []

    found = []
    for f in sorted(BULLETINS_DIR.glob("*.md")):
        child = f.stem
        text = _read(f)
        for m in re.finditer(
            r"# Bulletin from: .+?\nDate: (\S+)\nType: belief-challenge\n\n## Content\n(.+?)(?:\n---|\Z)",
            text, re.DOTALL
        ):
            date_str = m.group(1)
            content = m.group(2).strip()
            # Expect "PHIL-N: challenge text" or "B-N: challenge text"
            claim_m = re.match(r"(PHIL-\d+|B\d+):\s*(.+)", content, re.DOTALL)
            if claim_m:
                found.append({
                    "claim": claim_m.group(1),
                    "child": child,
                    "date": date_str,
                    "text": claim_m.group(2).strip(),
                })
    return found


def already_propagated(child: str, claim: str) -> bool:
    """Check if this child+claim combo is already in a Challenges table."""
    for path in [PHILOSOPHY_PATH, CHALLENGES_PATH]:
        if path.exists():
            text = _read(path)
            if re.search(rf"\|\s*{re.escape(claim)}\s*\|\s*{re.escape(child)}\s*\|", text):
                return True
    return False


def add_to_philosophy(challenges: list[dict]):
    """Append PHIL-N challenges to the Challenges table in PHILOSOPHY.md."""
    text = _read(PHILOSOPHY_PATH)
    table_end = text.rfind("\n| ")
    if table_end == -1:
        print("Could not find Challenges table in PHILOSOPHY.md")
        return 0

    insert_at = text.index("\n", table_end + 1) + 1
    rows = ""
    for c in challenges:
        short = c["text"][:80] + ("…" if len(c["text"]) > 80 else "")
        rows += f"| {c['claim']} | {c['child']} | {short} | open |\n"

    new_text = text[:insert_at] + rows + text[insert_at:]
    _write(PHILOSOPHY_PATH, new_text)
    return len(challenges)


def add_to_belief_challenges(challenges: list[dict]):
    """Append B-N challenges to beliefs/CHALLENGES.md (created if absent)."""
    if CHALLENGES_PATH.exists():
        text = _read(CHALLENGES_PATH)
    else:
        text = (
            "# Belief Challenges\n"
            "Child-to-parent challenges on beliefs in DEPS.md.\n"
            "Resolution: CONFIRMED (belief holds), SUPERSEDED (belief replaced), DROPPED (challenge wrong).\n\n"
            "| Belief | Child | Challenge | Status |\n"
            "|--------|-------|-----------|--------|\n"
        )

    rows = ""
    for c in challenges:
        short = c["text"][:80] + ("…" if len(c["text"]) > 80 else "")
        rows += f"| {c['claim']} | {c['child']} | {short} | open |\n"

    text += rows
    _write(CHALLENGES_PATH, text)
    return len(challenges)


def main():
    apply = "--apply" in sys.argv

    all_challenges = collect_challenges()
    pending = [c for c in all_challenges if not already_propagated(c["child"], c["claim"])]

    if not pending:
        print("No new belief-challenges from children.")
        return

    phil_challenges = [c for c in pending if c["claim"].startswith("PHIL-")]
    belief_challenges = [c for c in pending if c["claim"].startswith("B")]

    print(f"Found {len(pending)} new belief-challenge(s) from children:")
    for c in pending:
        print(f"  {c['claim']} from {c['child']} ({c['date']}): {c['text'][:60]}…")

    if not apply:
        print("\nDry run. Use --apply to write challenges.")
        return

    added = 0
    if phil_challenges:
        added += add_to_philosophy(phil_challenges)
        print(f"Added {len(phil_challenges)} challenge(s) to PHILOSOPHY.md.")
    if belief_challenges:
        added += add_to_belief_challenges(belief_challenges)
        print(f"Added {len(belief_challenges)} challenge(s) to beliefs/CHALLENGES.md.")
    print(f"\nTotal: {added} challenge(s) propagated.")


if __name__ == "__main__":
    main()
