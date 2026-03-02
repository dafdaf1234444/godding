#!/usr/bin/env python3
"""Regression tests for swarm_pr intake planning and queue de-dup."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import swarm_pr


class TestSwarmPr(unittest.TestCase):
    def test_parse_name_status_supports_basic_and_rename_rows(self):
        raw = "\n".join(
            [
                "M\ttools/maintenance.py",
                "A\tdocs/REAL-WORLD-SWARMING.md",
                "R100\told/name.md\tnew/name.md",
            ]
        )
        rows = swarm_pr.parse_name_status(raw)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["status"], "M")
        self.assertEqual(rows[1]["path"], "docs/REAL-WORLD-SWARMING.md")
        self.assertEqual(rows[2]["status"], "R")
        self.assertEqual(rows[2]["old_path"], "old/name.md")
        self.assertEqual(rows[2]["path"], "new/name.md")

    def test_build_plan_marks_hybrid_when_core_state_and_fanout_mix(self):
        changes = [
            {"status": "M", "raw_status": "M", "path": "tasks/FRONTIER.md"},
            {"status": "M", "raw_status": "M", "path": "tools/swarm_pr.py"},
        ]
        plan = swarm_pr.build_plan("origin/master", "feature/x", changes)
        self.assertEqual(plan["mode"], "hybrid")
        lane_names = {lane["name"] for lane in plan["lanes"]}
        self.assertIn("core-state", lane_names)
        self.assertIn("tooling", lane_names)
        self.assertEqual(plan["summary"]["changed_files"], 2)

    def test_enqueue_range_deduplicates_open_items_by_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            queue_path = Path(td) / "PR-QUEUE.json"
            fake_plan = {
                "range": "origin/master...feature/a",
                "mode": "fanout",
                "fingerprint": "abc123deadbeef00",
                "summary": {"changed_files": 2, "status_counts": {"M": 2}, "lane_count": 1},
                "lanes": [],
            }
            with patch.object(swarm_pr, "analyze_range", return_value=fake_plan):
                first = swarm_pr.enqueue_range("origin/master", "feature/a", queue_path)
                second = swarm_pr.enqueue_range("origin/master", "feature/a", queue_path)

            self.assertTrue(first["enqueued"])
            self.assertFalse(second["enqueued"])
            self.assertEqual(second["duplicate_of"], first["entry"]["id"])

            stored = json.loads(queue_path.read_text(encoding="utf-8"))
            self.assertEqual(len(stored["items"]), 1)
            self.assertEqual(stored["items"][0]["fingerprint"], "abc123deadbeef00")


if __name__ == "__main__":
    unittest.main()
