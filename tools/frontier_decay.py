#!/usr/bin/env python3
"""
frontier_decay.py — Signal decay for frontier questions.

Usage:
    python3 tools/frontier_decay.py show
    python3 tools/frontier_decay.py touch <F-id>
    python3 tools/frontier_decay.py archive

Old questions that nobody works on should weaken and eventually archive.
Implements stigmergic signal decay (pheromone evaporation).

Strength = 0.9^(days_since_last_active). Below 0.1 → candidate for archive.
"""

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTIER_PATH = REPO_ROOT / "tasks" / "FRONTIER.md"
DECAY_FILE = REPO_ROOT / "experiments" / "frontier-decay.json"


def _load_decay_data() -> dict:
    if DECAY_FILE.exists():
        return json.loads(DECAY_FILE.read_text())
    return {}


def _save_decay_data(data: dict):
    DECAY_FILE.parent.mkdir(parents=True, exist_ok=True)
    DECAY_FILE.write_text(json.dumps(data, indent=2))


def _get_open_questions() -> list[dict]:
    if not FRONTIER_PATH.exists():
        return []
    text = FRONTIER_PATH.read_text()
    # Only parse open questions (before ## Resolved)
    resolved_pos = text.find("## Resolved")
    open_text = text[:resolved_pos] if resolved_pos > 0 else text
    questions = []
    for m in re.finditer(r"^- \*\*F(\d+)\*\*:\s*(.+)$", open_text, re.MULTILINE):
        questions.append({"id": f"F{m.group(1)}", "text": m.group(2).strip()})
    return questions


def show():
    """Show all open questions with their signal strength."""
    questions = _get_open_questions()
    decay = _load_decay_data()
    today = date.today().isoformat()

    print("=== FRONTIER SIGNAL STRENGTH ===\n")
    print(f"{'ID':<6} {'Strength':<10} {'Last Active':<14} {'Question':<60}")
    print("-" * 90)

    weak = []
    for q in questions:
        fid = q["id"]
        last_active = decay.get(fid, {}).get("last_active", today)
        days = (date.fromisoformat(today) - date.fromisoformat(last_active)).days
        strength = 0.9 ** days

        # Initialize if not tracked
        if fid not in decay:
            decay[fid] = {"last_active": today}

        marker = ""
        if strength < 0.1:
            marker = " [ARCHIVE?]"
            weak.append(fid)
        elif strength < 0.3:
            marker = " [WEAK]"

        print(f"{fid:<6} {strength:<10.2f} {last_active:<14} {q['text'][:60]}{marker}")

    _save_decay_data(decay)

    if weak:
        print(f"\n{len(weak)} question(s) below archive threshold (strength < 0.1)")
        print(f"Run: python3 tools/frontier_decay.py archive")
    else:
        print(f"\nAll {len(questions)} questions above archive threshold.")


def touch(fid: str):
    """Refresh a frontier question's timestamp (someone is working on it)."""
    decay = _load_decay_data()
    today = date.today().isoformat()
    decay[fid] = {"last_active": today}
    _save_decay_data(decay)
    print(f"{fid} refreshed to {today} (strength = 1.0)")


def archive():
    """Move weak questions (strength < 0.1) to an archive section."""
    questions = _get_open_questions()
    decay = _load_decay_data()
    today = date.today().isoformat()

    to_archive = []
    for q in questions:
        fid = q["id"]
        last_active = decay.get(fid, {}).get("last_active", today)
        days = (date.fromisoformat(today) - date.fromisoformat(last_active)).days
        strength = 0.9 ** days
        if strength < 0.1:
            to_archive.append(q)

    if not to_archive:
        print("No questions below archive threshold.")
        return

    print(f"Archiving {len(to_archive)} question(s):")
    for q in to_archive:
        print(f"  {q['id']}: {q['text'][:70]}")

    # Remove from FRONTIER.md open sections
    text = FRONTIER_PATH.read_text()
    for q in to_archive:
        pattern = re.compile(
            r"^- \*\*" + re.escape(q["id"]) + r"\*\*:.*$\n?",
            re.MULTILINE
        )
        text = pattern.sub("", text)

    FRONTIER_PATH.write_text(text)
    print(f"\nArchived. Questions removed from FRONTIER.md open sections.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "show":
        show()
    elif cmd == "touch":
        if len(sys.argv) < 3:
            print("Usage: frontier_decay.py touch <F-id>")
            sys.exit(1)
        touch(sys.argv[2])
    elif cmd == "archive":
        archive()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
