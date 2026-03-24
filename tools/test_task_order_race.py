#!/usr/bin/env python3
"""Regression tests for task_order.py race handling."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import task_order  # noqa: E402


class TestTaskOrderRace(unittest.TestCase):
    def test_safe_mtime_handles_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            existing = root / "L-1.md"
            missing = root / "L-2.md"
            existing.write_text("present", encoding="utf-8")

            ordered = sorted([missing, existing], key=task_order._safe_mtime, reverse=True)

            self.assertEqual(ordered[0], existing)
            self.assertEqual(task_order._safe_mtime(missing), -1.0)

    def test_get_due_items_skips_working_tree_cleared_lesson_trim(self):
        class Result:
            stdout = "! Lesson over 20 lines: L-1489.md\n"
            stderr = ""

        original_root = task_order.ROOT
        original_run = task_order.subprocess.run
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                lessons_dir = root / "memory" / "lessons"
                lessons_dir.mkdir(parents=True)
                lesson = lessons_dir / "L-1489.md"
                lesson.write_text("\n".join(f"line {i}" for i in range(15)), encoding="utf-8")

                task_order.ROOT = root
                task_order.subprocess.run = lambda *args, **kwargs: Result()

                self.assertEqual(task_order.get_due_items(), [])
        finally:
            task_order.ROOT = original_root
            task_order.subprocess.run = original_run

    def test_get_due_items_keeps_uncleared_lesson_trim(self):
        class Result:
            stdout = "! Lesson over 20 lines: L-1489.md\n"
            stderr = ""

        original_root = task_order.ROOT
        original_run = task_order.subprocess.run
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                lessons_dir = root / "memory" / "lessons"
                lessons_dir.mkdir(parents=True)
                lesson = lessons_dir / "L-1489.md"
                lesson.write_text("\n".join(f"line {i}" for i in range(21)), encoding="utf-8")

                task_order.ROOT = root
                task_order.subprocess.run = lambda *args, **kwargs: Result()

                due_items = task_order.get_due_items()
                self.assertEqual(len(due_items), 1)
                self.assertEqual(due_items[0]["action"], "Lesson over 20 lines: L-1489.md")
        finally:
            task_order.ROOT = original_root
            task_order.subprocess.run = original_run


if __name__ == "__main__":
    unittest.main()
