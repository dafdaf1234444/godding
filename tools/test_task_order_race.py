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


if __name__ == "__main__":
    unittest.main()
