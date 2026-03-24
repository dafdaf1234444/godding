#!/usr/bin/env python3
"""Regression tests for task_order.py race handling."""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import task_order  # noqa: E402
import task_order_helpers  # noqa: E402


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

    def test_check_preemption_marks_commit_task_when_git_lock_is_live(self):
        original_root = task_order_helpers.ROOT
        original_git = task_order_helpers._git
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                git_dir = root / ".git"
                git_dir.mkdir()
                (git_dir / "index.lock").write_text("", encoding="utf-8")

                task_order_helpers.ROOT = root
                task_order_helpers._git = lambda args: ""

                tasks = [{
                    "priority": task_order.P_COMMIT,
                    "tier": "COMMIT",
                    "score": 100,
                    "action": "Commit untracked artifacts: 1 lesson(s): L-1511",
                    "detail": "Files: memory/lessons/L-1511.md",
                    "command": None,
                }]

                updated = task_order_helpers.check_preemption(
                    tasks,
                    task_order.P_DISPATCH,
                    task_order.P_STRATEGY,
                )

                self.assertTrue(updated[0]["preempted"])
                self.assertIn("[PREEMPTED]", updated[0]["tier"])
                self.assertIn("Live git write detected", updated[0]["detail"])
                self.assertTrue(any(t["tier"] == "NOVEL" for t in updated))
        finally:
            task_order_helpers.ROOT = original_root
            task_order_helpers._git = original_git

    def test_check_preemption_ignores_stale_git_lock(self):
        original_root = task_order_helpers.ROOT
        original_git = task_order_helpers._git
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                git_dir = root / ".git"
                git_dir.mkdir()
                lock_path = git_dir / "index.lock"
                lock_path.write_text("", encoding="utf-8")
                stale_time = time.time() - (task_order_helpers.LIVE_GIT_LOCK_SECONDS + 30)
                os.utime(lock_path, (stale_time, stale_time))

                task_order_helpers.ROOT = root
                task_order_helpers._git = lambda args: ""

                tasks = [{
                    "priority": task_order.P_COMMIT,
                    "tier": "COMMIT",
                    "score": 100,
                    "action": "Commit untracked artifacts: 1 lesson(s): L-1511",
                    "detail": "Files: memory/lessons/L-1511.md",
                    "command": None,
                }]

                updated = task_order_helpers.check_preemption(
                    tasks,
                    task_order.P_DISPATCH,
                    task_order.P_STRATEGY,
                )

                self.assertNotIn("preempted", updated[0])
                self.assertEqual(updated[0]["tier"], "COMMIT")
                self.assertFalse(any(t["tier"] == "NOVEL" for t in updated[1:]))
        finally:
            task_order_helpers.ROOT = original_root
            task_order_helpers._git = original_git


if __name__ == "__main__":
    unittest.main()
