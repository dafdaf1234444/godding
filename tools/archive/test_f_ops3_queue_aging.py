#!/usr/bin/env python3
"""Regression tests for F-OPS3 queue-aging replay tool."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ops3_queue_aging as mod


class TestFOps3QueueAging(unittest.TestCase):
    def _sample_lanes(self) -> str:
        return "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S180 | codex | local | - | GPT-5 | codex-cli | x | setup=x focus=global | READY | queued |",
                "| 2026-02-27 | L-A | S182 | codex | local | - | GPT-5 | codex-cli | x | setup=x focus=global | ACTIVE | progress |",
                "| 2026-02-27 | L-B | S181 | codex | local | - | GPT-5 | codex-cli | y | setup=x focus=domains/statistics | READY | queued |",
                "| 2026-02-27 | L-B | S181 | codex | local | - | GPT-5 | codex-cli | y | setup=x focus=domains/statistics | ACTIVE | progress |",
                "| 2026-02-27 | L-C | S182 | codex | local | - | GPT-5 | codex-cli | z | setup=x focus=domains/ai | READY | queued |",
            ]
        )

    def test_build_jobs(self):
        jobs = mod.build_jobs(mod.parse_lane_rows(self._sample_lanes()), session_min=170)
        self.assertEqual(len(jobs), 3)
        self.assertEqual(jobs[0].lane, "L-A")
        self.assertEqual(jobs[0].ready_session, 180)
        self.assertEqual(jobs[0].observed_progress_session, 182)

    def test_policy_simulation(self):
        jobs = mod.build_jobs(mod.parse_lane_rows(self._sample_lanes()), session_min=170)
        analysis = mod.analyze(jobs, stale_threshold=1)
        self.assertEqual(analysis["job_count"], 3)
        self.assertIn(analysis["best_policy"], {"recency_bias", "queue_aging"})
        self.assertEqual(len(analysis["policies"]), 2)

    def test_run_writes_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lanes = root / "LANES.md"
            out = root / "out.json"
            lanes.write_text(self._sample_lanes(), encoding="utf-8")
            payload = mod.run(lanes, out, session_min=170, stale_threshold=1)
            self.assertTrue(out.exists())
            self.assertEqual(payload["frontier_id"], "F-OPS3")
            self.assertEqual(payload["analysis"]["job_count"], 3)


if __name__ == "__main__":
    unittest.main()

