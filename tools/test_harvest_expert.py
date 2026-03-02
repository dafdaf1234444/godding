#!/usr/bin/env python3
"""Tests for harvest_expert.py — foreign-repo knowledge harvesting tool."""

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HARVEST_EXPERT = Path(__file__).parent / "harvest_expert.py"

# A lesson text that already exists in the home swarm (L-005 rule).
KNOWN_LESSON_TEXT = (
    "When naming a system, verify the name matches the actual coordination model."
)

# A lesson text that is genuinely novel (not in the home swarm).
NOVEL_LESSON_TEXT = (
    "Foreign systems that use event sourcing as their primary persistence "
    "mechanism converge on append-only logs as the single source of truth."
)

# A principle text that already exists in PRINCIPLES.md (P-013 excerpt).
KNOWN_PRINCIPLE_TEXT = "review-after dates, not expiration"

# A novel principle not present in the home swarm.
NOVEL_PRINCIPLE_TEXT = (
    "Always snapshot schema versions before running irreversible migrations."
)

# A frontier question that is genuinely novel.
NOVEL_FRONTIER_TEXT = (
    "Can swarm systematically ingest event-sourced foreign repos "
    "and translate their design patterns into swarm principles?"
)


def _run(mode: str, path: str) -> dict:
    """Invoke harvest_expert.py and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, str(HARVEST_EXPERT), mode, path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"harvest_expert.py exited {result.returncode}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return json.loads(result.stdout)


def _write(path: Path, name: str, content: str) -> None:
    (path / name).write_text(textwrap.dedent(content), encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLessonsMode(unittest.TestCase):
    """Mode=lessons: harvest from a directory containing lesson .md files."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.foreign = Path(self._tmp.name)
        lessons_dir = self.foreign / "memory" / "lessons"
        lessons_dir.mkdir(parents=True)

        # Novel lesson — should appear with novelty_score > 0.
        _write(
            lessons_dir,
            "L-001.md",
            f"""\
            # L-001: Event sourcing as persistence backbone
            Date: 2026-01-10 | Confidence: Observed

            ## What happened (3 lines max)
            Surveyed 12 production systems that adopted event sourcing.
            Every system converged on append-only logs as the primary store.

            ## What we learned (3 lines max)
            {NOVEL_LESSON_TEXT}
            Rollback is free when events are immutable.

            ## Rule extracted (1-2 lines)
            {NOVEL_LESSON_TEXT}

            ## Affected beliefs: B3
            """,
        )

        # Lesson whose rule text overlaps with a known home-swarm lesson.
        _write(
            lessons_dir,
            "L-002.md",
            f"""\
            # L-002: Naming matters for coordination models
            Date: 2026-01-11 | Confidence: Verified

            ## What happened (3 lines max)
            Reviewed naming conventions across 5 distributed systems projects.

            ## What we learned (3 lines max)
            Names shape design intuitions.

            ## Rule extracted (1-2 lines)
            {KNOWN_LESSON_TEXT}

            ## Affected beliefs: B6
            """,
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_returns_required_top_level_keys(self):
        out = _run("lessons", self._tmp.name)
        self.assertIn("harvested", out)
        self.assertIn("conflicts", out)
        self.assertIn("recommended_actions", out)

    def test_novel_lesson_has_positive_novelty_score(self):
        out = _run("lessons", self._tmp.name)
        texts = [h["text"] for h in out["harvested"]]
        # At least one harvested item should reference the novel text.
        self.assertTrue(
            any(NOVEL_LESSON_TEXT[:40] in t for t in texts),
            f"Novel lesson not found in harvested texts: {texts}",
        )
        for item in out["harvested"]:
            if NOVEL_LESSON_TEXT[:40] in item["text"]:
                self.assertGreater(item["novelty_score"], 0.0)
                self.assertLessEqual(item["novelty_score"], 1.0)

    def test_known_lesson_has_zero_novelty_score(self):
        out = _run("lessons", self._tmp.name)
        for item in out["harvested"]:
            if KNOWN_LESSON_TEXT[:30] in item["text"]:
                self.assertAlmostEqual(
                    item["novelty_score"],
                    0.0,
                    places=3,
                    msg="Already-known lesson text should have novelty_score=0.0",
                )

    def test_source_field_present_and_non_empty(self):
        out = _run("lessons", self._tmp.name)
        for item in out["harvested"]:
            self.assertIn("source", item)
            self.assertTrue(item["source"], "source must be a non-empty string")

    def test_recommended_actions_is_list_of_strings(self):
        out = _run("lessons", self._tmp.name)
        self.assertIsInstance(out["recommended_actions"], list)
        for action in out["recommended_actions"]:
            self.assertIsInstance(action, str)


class TestPrinciplesMode(unittest.TestCase):
    """Mode=principles: harvest from a directory containing PRINCIPLES.md."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.foreign = Path(self._tmp.name)
        memory_dir = self.foreign / "memory"
        memory_dir.mkdir(parents=True)

        _write(
            memory_dir,
            "PRINCIPLES.md",
            f"""\
            # Principles

            ## Schema management
            **Migrations**: {NOVEL_PRINCIPLE_TEXT}

            ## Lifecycle
            **Versioning**: {KNOWN_PRINCIPLE_TEXT}
            """,
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_novel_principle_harvested_with_positive_novelty(self):
        out = _run("principles", self._tmp.name)
        texts = [h["text"] for h in out["harvested"]]
        self.assertTrue(
            any(NOVEL_PRINCIPLE_TEXT[:30] in t for t in texts),
            f"Novel principle not found in harvested: {texts}",
        )
        for item in out["harvested"]:
            if NOVEL_PRINCIPLE_TEXT[:30] in item["text"]:
                self.assertGreater(item["novelty_score"], 0.0)

    def test_known_principle_has_zero_novelty_score(self):
        out = _run("principles", self._tmp.name)
        for item in out["harvested"]:
            if KNOWN_PRINCIPLE_TEXT[:20] in item["text"]:
                self.assertAlmostEqual(
                    item["novelty_score"],
                    0.0,
                    places=3,
                    msg="Already-known principle should have novelty_score=0.0",
                )

    def test_conflicts_list_is_present(self):
        out = _run("principles", self._tmp.name)
        self.assertIsInstance(out["conflicts"], list)
        # Conflicts (if any) must have the required sub-keys.
        for conflict in out["conflicts"]:
            self.assertIn("text", conflict)
            self.assertIn("source", conflict)
            self.assertIn("existing_belief", conflict)


class TestFrontiersMode(unittest.TestCase):
    """Mode=frontiers: harvest from a directory containing FRONTIER.md."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.foreign = Path(self._tmp.name)
        tasks_dir = self.foreign / "tasks"
        tasks_dir.mkdir(parents=True)

        _write(
            tasks_dir,
            "FRONTIER.md",
            f"""\
            # Frontier — Open Questions

            ## Exploratory
            - **F001**: {NOVEL_FRONTIER_TEXT}
            - **F002**: Can event sourcing replace mutable state in all CRUD operations?
            """,
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_frontier_items_harvested(self):
        out = _run("frontiers", self._tmp.name)
        self.assertGreater(
            len(out["harvested"]),
            0,
            "Expected at least one frontier item to be harvested",
        )

    def test_frontier_novelty_scores_in_range(self):
        out = _run("frontiers", self._tmp.name)
        for item in out["harvested"]:
            self.assertGreaterEqual(item["novelty_score"], 0.0)
            self.assertLessEqual(item["novelty_score"], 1.0)

    def test_frontier_source_contains_file_reference(self):
        out = _run("frontiers", self._tmp.name)
        for item in out["harvested"]:
            self.assertIn("source", item)
            self.assertTrue(item["source"])


class TestFullMode(unittest.TestCase):
    """Mode=full: runs lessons + principles + frontiers in one pass."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.foreign = Path(self._tmp.name)

        # Lessons
        lessons_dir = self.foreign / "memory" / "lessons"
        lessons_dir.mkdir(parents=True)
        _write(
            lessons_dir,
            "L-001.md",
            f"""\
            # L-001: Append-only logs
            Date: 2026-01-10 | Confidence: Observed

            ## What happened (3 lines max)
            Studied event-sourced systems.

            ## What we learned (3 lines max)
            {NOVEL_LESSON_TEXT}

            ## Rule extracted (1-2 lines)
            {NOVEL_LESSON_TEXT}

            ## Affected beliefs: B3
            """,
        )

        # Principles
        memory_dir = self.foreign / "memory"
        _write(
            memory_dir,
            "PRINCIPLES.md",
            f"""\
            # Principles

            ## Schema management
            **Migrations**: {NOVEL_PRINCIPLE_TEXT}
            """,
        )

        # Frontiers
        tasks_dir = self.foreign / "tasks"
        tasks_dir.mkdir(parents=True)
        _write(
            tasks_dir,
            "FRONTIER.md",
            f"""\
            # Frontier

            ## Exploratory
            - **F001**: {NOVEL_FRONTIER_TEXT}
            """,
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_full_mode_harvests_from_all_three_sources(self):
        out = _run("full", self._tmp.name)
        # We seeded one lesson, one principle, one frontier — expect at least
        # three items total (one from each source).
        self.assertGreaterEqual(
            len(out["harvested"]),
            3,
            f"full mode should harvest from all 3 sub-modes; got {out['harvested']}",
        )

    def test_full_mode_sources_include_all_three_kinds(self):
        out = _run("full", self._tmp.name)
        # Sources should reference the actual files from each sub-mode.
        sources = [item["source"] for item in out["harvested"]]
        source_blob = " ".join(sources).lower()
        # At least one source from a lesson file (memory/lessons/ or L-0xx)
        # at least one from PRINCIPLES.md, and one from FRONTIER.md.
        self.assertTrue(
            any("lesson" in s.lower() or "l-0" in s.lower() for s in sources)
            or any("L-0" in s for s in sources),
            f"No lesson source found in: {sources}",
        )
        self.assertTrue(
            any("principle" in s.lower() for s in sources),
            f"No principles source found in: {sources}",
        )
        self.assertTrue(
            any("frontier" in s.lower() for s in sources),
            f"No frontier source found in: {sources}",
        )

    def test_full_mode_recommended_actions_non_empty(self):
        out = _run("full", self._tmp.name)
        # A directory with genuine novel content should yield at least one action.
        self.assertGreater(
            len(out["recommended_actions"]),
            0,
            "Expected recommended_actions to be non-empty for novel foreign content",
        )


class TestEmptyDirectory(unittest.TestCase):
    """A directory with no harvestable content should return empty results."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # No sub-directories, no files.

    def tearDown(self):
        self._tmp.cleanup()

    def _assert_empty_results(self, mode: str):
        out = _run(mode, self._tmp.name)
        self.assertEqual(
            out["harvested"],
            [],
            f"mode={mode}: expected empty harvested list for empty dir",
        )
        self.assertEqual(
            out["conflicts"],
            [],
            f"mode={mode}: expected empty conflicts list for empty dir",
        )

    def test_lessons_mode_empty_dir(self):
        self._assert_empty_results("lessons")

    def test_principles_mode_empty_dir(self):
        self._assert_empty_results("principles")

    def test_frontiers_mode_empty_dir(self):
        self._assert_empty_results("frontiers")

    def test_full_mode_empty_dir(self):
        self._assert_empty_results("full")


class TestZeroNoveltyForKnownContent(unittest.TestCase):
    """novelty_score must be 0.0 for items already present in the home swarm."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.foreign = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_known_lesson_novelty_zero(self):
        lessons_dir = self.foreign / "memory" / "lessons"
        lessons_dir.mkdir(parents=True)
        _write(
            lessons_dir,
            "L-001.md",
            f"""\
            # L-001: Naming matters
            Date: 2026-01-01 | Confidence: Verified

            ## What happened (3 lines max)
            Reviewed naming in distributed systems.

            ## What we learned (3 lines max)
            Names shape design intuitions.

            ## Rule extracted (1-2 lines)
            {KNOWN_LESSON_TEXT}

            ## Affected beliefs: B6
            """,
        )
        out = _run("lessons", self._tmp.name)
        for item in out["harvested"]:
            if KNOWN_LESSON_TEXT[:30] in item["text"]:
                self.assertAlmostEqual(
                    item["novelty_score"],
                    0.0,
                    places=3,
                    msg=(
                        "Item already in home swarm must have novelty_score=0.0; "
                        f"got {item['novelty_score']}"
                    ),
                )

    def test_known_principle_novelty_zero(self):
        memory_dir = self.foreign / "memory"
        memory_dir.mkdir(parents=True)
        _write(
            memory_dir,
            "PRINCIPLES.md",
            f"""\
            # Principles

            ## Lifecycle
            **Versioning**: {KNOWN_PRINCIPLE_TEXT}
            """,
        )
        out = _run("principles", self._tmp.name)
        for item in out["harvested"]:
            if KNOWN_PRINCIPLE_TEXT[:20] in item["text"]:
                self.assertAlmostEqual(
                    item["novelty_score"],
                    0.0,
                    places=3,
                    msg=(
                        "Principle already in home swarm must have novelty_score=0.0; "
                        f"got {item['novelty_score']}"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
