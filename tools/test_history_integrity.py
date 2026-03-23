#!/usr/bin/env python3
"""Regression tests for history_integrity false-negative handling."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import history_integrity  # noqa: E402


class TestCreationSessionSelection(unittest.TestCase):
    def test_get_session_uses_oldest_non_restore_add(self):
        log_output = "\n".join(
            [
                "67c7b311\t[S499] fix: restore 3893 files dropped by plumbing error in ba526230",
                "4a43d4f7\t[S499] fix: restore 3840 files dropped by plumbing error in f8c199d7+49171bcc",
                "2a743a8f\t[S427] fix: restore 3033 files deleted by catastrophic mass-commit 497a94ef",
                "def8a182\t[S423] principles-dedup: P-278 heterogeneous-dispatch + P-252 duplicate removed",
            ]
        )

        class Result:
            stdout = log_output

        with mock.patch.object(history_integrity.subprocess, "run", return_value=Result()):
            session, is_restore = history_integrity._get_session("memory/lessons/L-950.md")

        self.assertEqual(session, "S423")
        self.assertFalse(is_restore)


class TestSchemaDetection(unittest.TestCase):
    def test_collect_json_keys_recurses(self):
        keys = history_integrity._collect_json_keys(
            {
                "expect": "prediction",
                "summary": {
                    "validation_verdict": "CONFIRMED",
                    "nested": [{"results": {"lift": 0.2}}],
                },
            }
        )

        self.assertIn("expect", keys)
        self.assertIn("validation_verdict", keys)
        self.assertIn("results", keys)

    def test_expectation_schema_accepts_modern_fields(self):
        self.assertTrue(history_integrity._has_expectation_schema({"expect"}))
        self.assertTrue(history_integrity._has_expectation_schema({"falsification_criterion"}))

    def test_outcome_schema_accepts_verdict_and_results(self):
        self.assertTrue(history_integrity._has_outcome_schema({"validation_verdict"}))
        self.assertTrue(history_integrity._has_outcome_schema({"results"}))

    def test_diff_only_counts_with_expectation_context(self):
        self.assertFalse(history_integrity._has_outcome_schema({"diff"}))
        self.assertTrue(history_integrity._has_outcome_schema({"expect", "diff"}))


class TestLessonSampling(unittest.TestCase):
    def test_sample_lessons_sorts_numerically(self):
        files = [
            Path("memory/lessons/L-999.md"),
            Path("memory/lessons/L-1001.md"),
            Path("memory/lessons/L-1000.md"),
        ]

        with mock.patch.object(
            Path,
            "read_text",
            side_effect=[
                "Session: S999",
                "Session: S1001",
                "Session: S1000",
            ],
        ):
            sample = history_integrity._sample_lessons(files, sample_size=2)

        self.assertEqual([path.name for path, _, _ in sample], ["L-1000.md", "L-1001.md"])


if __name__ == "__main__":
    unittest.main()
