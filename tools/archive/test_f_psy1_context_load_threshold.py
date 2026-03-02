#!/usr/bin/env python3
"""Regression tests for F-PSY1 context-load threshold analysis."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_psy1_context_load_threshold as mod


class TestFPsy1ContextLoadThreshold(unittest.TestCase):
    def test_parse_lane_rows_and_session_number(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-1 | S186 | codex | local | - | GPT-5 | cli | tasks/NEXT.md | setup=x focus=global | ACTIVE | running baseline |",
            ]
        )
        rows = mod.parse_lane_rows(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["lane"], "L-1")
        self.assertEqual(mod.parse_session_number(rows[0]["session"]), 186)

    def test_session_lane_metrics_computes_density_and_load(self):
        rows = [
            {
                "lane": "L-1",
                "session": "S186",
                "status": "ACTIVE",
                "etc": "setup=x focus=global intent=run",
                "notes": "run one baseline pass",
            },
            {
                "lane": "L-1",
                "session": "S186",
                "status": "READY",
                "etc": "setup=x focus=global next_step=rerun",
                "notes": "queued rerun",
            },
            {
                "lane": "L-2",
                "session": "S186",
                "status": "BLOCKED",
                "etc": "setup=x focus=global blocked=none",
                "notes": "wait on dependency clear",
            },
        ]
        out = mod.session_lane_metrics(rows, session_min=180)
        self.assertIn(186, out)
        self.assertAlmostEqual(out[186]["lane_rows"], 3.0, places=4)
        self.assertAlmostEqual(out[186]["unique_lanes"], 2.0, places=4)
        self.assertAlmostEqual(out[186]["update_density"], 1.5, places=4)
        self.assertGreater(out[186]["context_load_score"], 0.0)

    def test_parse_next_updates_counts_events(self):
        text = "\n".join(
            [
                "S186: first event line here",
                "S186: second event line here",
                "S185: older event line",
                "not a session event",
            ]
        )
        out = mod.parse_next_updates(text, session_min=186)
        self.assertIn(186, out)
        self.assertAlmostEqual(out[186]["next_event_count"], 2.0, places=4)
        self.assertGreater(out[186]["next_event_mean_words"], 0.0)
        self.assertNotIn(185, out)

    def test_threshold_sweep_prefers_quality_drop_split(self):
        records = []
        # Lower-load/high-quality cluster
        for i, load in enumerate([0.8, 0.9, 1.0, 1.1, 1.2], start=1):
            records.append(
                {
                    "session": 170 + i,
                    "context_load_score": load,
                    "quality_score": 5.0 - i * 0.1,
                }
            )
        # Higher-load/lower-quality cluster
        for i, load in enumerate([2.5, 2.7, 2.9, 3.1, 3.3], start=1):
            records.append(
                {
                    "session": 180 + i,
                    "context_load_score": load,
                    "quality_score": 2.5 - i * 0.1,
                }
            )

        sweep = mod.threshold_sweep(records, min_bucket=3)
        self.assertGreater(sweep["evaluated"], 0)
        self.assertIsNotNone(sweep["best"])
        self.assertGreater(sweep["best"]["delta_low_minus_high"], 0.0)


if __name__ == "__main__":
    unittest.main()
