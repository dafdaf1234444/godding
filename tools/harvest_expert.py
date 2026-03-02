#!/usr/bin/env python3
"""
harvest_expert.py — Extract value from a foreign swarm or knowledge source.

Two-phase protocol:
  1. Harvest: scan foreign swarm for lessons, principles, frontier questions.
  2. Integrate: score novelty against home swarm; produce machine-readable
     recommended_actions that a node can execute directly.

Usage:
    python3 tools/harvest_expert.py lessons   <foreign_path>
    python3 tools/harvest_expert.py principles <foreign_path>
    python3 tools/harvest_expert.py frontiers  <foreign_path>
    python3 tools/harvest_expert.py full       <foreign_path>

Output (JSON to stdout):
    {
      "harvested":            [{"text", "source", "novelty_score"}],
      "conflicts":            [{"text", "source", "existing_belief"}],
      "recommended_actions":  ["Add lesson: ...", "Review principle ..."]
    }

novelty_score: 0.0 = already known; 1.0 = fully novel; 0.x = partial overlap.
Scoring uses token-level Jaccard similarity against the full home-swarm corpus.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterator


# ---------------------------------------------------------------------------
# Paths (relative to the home swarm root, resolved from this file's location)
# ---------------------------------------------------------------------------
HOME = Path(__file__).parent.parent  # repo root


def _home_lessons_dir() -> Path:
    return HOME / "memory" / "lessons"


def _home_principles_path() -> Path:
    return HOME / "memory" / "PRINCIPLES.md"


def _home_frontier_path() -> Path:
    return HOME / "tasks" / "FRONTIER.md"


# ---------------------------------------------------------------------------
# Tokenisation + Jaccard similarity
# ---------------------------------------------------------------------------

def _tokens(text: str) -> set[str]:
    """Lowercase word tokens, stripped of punctuation."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _max_similarity(text: str, corpus: list[str]) -> float:
    if not corpus:
        return 0.0
    return max(_jaccard(text, item) for item in corpus)


# ---------------------------------------------------------------------------
# Home-swarm corpus loaders
# ---------------------------------------------------------------------------

def _load_home_lesson_rules() -> list[str]:
    """Extract 'Rule extracted' blocks from every lesson in the home swarm."""
    rules: list[str] = []
    lessons_dir = _home_lessons_dir()
    if not lessons_dir.exists():
        return rules
    for path in lessons_dir.glob("L-*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        # Capture lines under "## Rule extracted" until next "##" heading.
        for match in re.finditer(
            r"##\s+Rule extracted.*?\n(.*?)(?:\n##|\Z)", text, re.DOTALL
        ):
            rule_text = match.group(1).strip()
            if rule_text:
                rules.append(rule_text)
    return rules


def _load_home_principles() -> list[str]:
    """Extract individual principle atoms from home PRINCIPLES.md.

    Lines use the format:
        **Category**: P-NNN text | P-NNN text | ...
    We split on ' | ' and strip leading 'P-NNN ' identifiers so that novelty
    comparison works on the semantic content, not the identifier.
    """
    path = _home_principles_path()
    if not path.exists():
        return []
    principles: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Strip leading "**Category**: " prefix if present.
        line = re.sub(r"^\*\*[^*]+\*\*:\s*", "", line)
        # Split on ` | ` separator used in PRINCIPLES.md.
        parts = re.split(r"\s*\|\s*", line)
        for part in parts:
            # Strip leading P-NNN identifier (e.g. "P-012 never delete...").
            content = re.sub(r"^P-\d+\s+", "", part.strip())
            if content:
                principles.append(content)
    return principles


def _load_home_frontiers() -> list[str]:
    """Extract frontier question text from home FRONTIER.md."""
    path = _home_frontier_path()
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    questions: list[str] = []
    for match in re.finditer(r"\*\*F[\w-]+\*\*[:\s]+(.*?)(?:\n|$)", text):
        questions.append(match.group(1).strip())
    return questions


# ---------------------------------------------------------------------------
# Foreign swarm extractors
# ---------------------------------------------------------------------------

def _foreign_lesson_rules(foreign: Path) -> Iterator[tuple[str, str]]:
    """Yield (rule_text, source_path_str) from foreign lessons."""
    lessons_dir = foreign / "memory" / "lessons"
    if not lessons_dir.exists():
        return
    for path in sorted(lessons_dir.glob("L-*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(
            r"##\s+Rule extracted.*?\n(.*?)(?:\n##|\Z)", text, re.DOTALL
        ):
            rule_text = match.group(1).strip()
            if rule_text:
                yield rule_text, str(path.relative_to(foreign))


def _foreign_principles(foreign: Path) -> Iterator[tuple[str, str]]:
    """Yield (principle_line, source_path_str) from foreign PRINCIPLES.md."""
    path = foreign / "memory" / "PRINCIPLES.md"
    if not path.exists():
        return
    source = str(path.relative_to(foreign))
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            yield line, source


def _foreign_frontiers(foreign: Path) -> Iterator[tuple[str, str]]:
    """Yield (frontier_text, source_path_str) from foreign FRONTIER.md."""
    path = foreign / "tasks" / "FRONTIER.md"
    if not path.exists():
        return
    source = str(path.relative_to(foreign))
    text = path.read_text(encoding="utf-8", errors="replace")
    for match in re.finditer(r"\*\*F[\w-]+\*\*[:\s]+(.*?)(?:\n|$)", text):
        yield match.group(1).strip(), source


# ---------------------------------------------------------------------------
# Novelty scoring threshold
# ---------------------------------------------------------------------------
KNOWN_THRESHOLD = 0.60   # Jaccard ≥ this → already known, novelty_score = 0.0
NOVEL_THRESHOLD = 0.25   # Jaccard ≤ this → fully novel, novelty_score = 1.0


def _novelty(text: str, corpus: list[str]) -> float:
    sim = _max_similarity(text, corpus)
    if sim >= KNOWN_THRESHOLD:
        return 0.0
    if sim <= NOVEL_THRESHOLD:
        return 1.0
    # Linear interpolation between the two thresholds.
    return round(1.0 - (sim - NOVEL_THRESHOLD) / (KNOWN_THRESHOLD - NOVEL_THRESHOLD), 3)


# ---------------------------------------------------------------------------
# Per-mode harvest functions
# ---------------------------------------------------------------------------

Item = dict  # {"text": str, "source": str, "novelty_score": float}
Conflict = dict  # {"text": str, "source": str, "existing_belief": str}


def harvest_lessons(foreign: Path) -> tuple[list[Item], list[Conflict]]:
    corpus = _load_home_lesson_rules()
    harvested: list[Item] = []
    conflicts: list[Conflict] = []

    for text, source in _foreign_lesson_rules(foreign):
        score = _novelty(text, corpus)
        harvested.append({"text": text, "source": source, "novelty_score": score})
        # A conflict arises when a foreign rule directly contradicts a known rule
        # (very high similarity but phrased as negation). Simple heuristic:
        # if "not" or "never" appears in one but not the other and Jaccard is high.
        sim = _max_similarity(text, corpus)
        if KNOWN_THRESHOLD * 0.7 < sim < KNOWN_THRESHOLD:
            best = max(corpus, key=lambda c: _jaccard(text, c))
            negated = ("not " in text.lower() or "never " in text.lower()) != (
                "not " in best.lower() or "never " in best.lower()
            )
            if negated:
                conflicts.append({
                    "text": text,
                    "source": source,
                    "existing_belief": best[:120],
                })

    return harvested, conflicts


def harvest_principles(foreign: Path) -> tuple[list[Item], list[Conflict]]:
    corpus = _load_home_principles()
    harvested: list[Item] = []
    conflicts: list[Conflict] = []

    for text, source in _foreign_principles(foreign):
        if len(text) < 10:
            continue
        score = _novelty(text, corpus)
        harvested.append({"text": text, "source": source, "novelty_score": score})
        sim = _max_similarity(text, corpus)
        if sim >= KNOWN_THRESHOLD * 0.6 and sim < KNOWN_THRESHOLD:
            best = max(corpus, key=lambda c: _jaccard(text, c))
            negated = ("not " in text.lower()) != ("not " in best.lower())
            if negated:
                conflicts.append({
                    "text": text,
                    "source": source,
                    "existing_belief": best[:120],
                })

    return harvested, conflicts


def harvest_frontiers(foreign: Path) -> tuple[list[Item], list[Conflict]]:
    corpus = _load_home_frontiers()
    harvested: list[Item] = []

    for text, source in _foreign_frontiers(foreign):
        score = _novelty(text, corpus)
        harvested.append({"text": text, "source": source, "novelty_score": score})

    return harvested, []


# ---------------------------------------------------------------------------
# Recommended actions builder
# ---------------------------------------------------------------------------

def _build_actions(harvested: list[Item], conflicts: list[Conflict]) -> list[str]:
    actions: list[str] = []
    novel = [h for h in harvested if h["novelty_score"] >= 0.5]
    partial = [h for h in harvested if 0.0 < h["novelty_score"] < 0.5]

    if novel:
        actions.append(
            f"Review {len(novel)} novel item(s) with novelty_score ≥ 0.5 — "
            "candidates for new lessons, principles, or frontier questions."
        )
    if partial:
        actions.append(
            f"Inspect {len(partial)} partial-overlap item(s) — "
            "may refine existing lessons or surface edge-case variants."
        )
    if conflicts:
        actions.append(
            f"Resolve {len(conflicts)} potential conflict(s) — "
            "write a CHALLENGES.md entry if contradiction is confirmed."
        )
    if not actions:
        actions.append("Nothing novel found — home swarm already covers this knowledge.")

    # Harvest→integration: always remind the node to close the gap.
    if novel or partial:
        actions.append(
            "To close the harvest→integration gap (L-278): copy high-novelty "
            "items into a draft lesson file and run validate_beliefs.py before committing."
        )

    return actions


# ---------------------------------------------------------------------------
# Full-mode dispatch
# ---------------------------------------------------------------------------

def harvest_full(foreign: Path) -> tuple[list[Item], list[Conflict]]:
    all_harvested: list[Item] = []
    all_conflicts: list[Conflict] = []
    for fn in (harvest_lessons, harvest_principles, harvest_frontiers):
        h, c = fn(foreign)
        all_harvested.extend(h)
        all_conflicts.extend(c)
    return all_harvested, all_conflicts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

MODES = {
    "lessons": harvest_lessons,
    "principles": harvest_principles,
    "frontiers": harvest_frontiers,
    "full": harvest_full,
}


def main(argv: list[str]) -> None:
    if len(argv) < 3:
        print(
            "Usage: harvest_expert.py <mode> <foreign_path>\n"
            f"Modes: {', '.join(MODES)}",
            file=sys.stderr,
        )
        sys.exit(1)

    mode, foreign_str = argv[1], argv[2]
    if mode not in MODES:
        print(f"Unknown mode {mode!r}. Modes: {', '.join(MODES)}", file=sys.stderr)
        sys.exit(1)

    foreign = Path(foreign_str)
    if not foreign.is_dir():
        print(f"Path not found or not a directory: {foreign}", file=sys.stderr)
        sys.exit(1)

    harvested, conflicts = MODES[mode](foreign)
    actions = _build_actions(harvested, conflicts)

    print(json.dumps({
        "harvested": harvested,
        "conflicts": conflicts,
        "recommended_actions": actions,
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv)
