#!/usr/bin/env python3
"""Regression tests for F-CTL2 diff-latency baseline tool."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ctl2_diff_latency as mod


class TestFCTL2DiffLatency(unittest.TestCase):
    def test_parse_args_accepts_output_alias(self):
        argv = [
            "f_ctl2_diff_latency.py",
            "--source",
            "lanes",
            "--output",
            "experiments/control-theory/f-ctl2-diff-latency-s186-structured.json",
        ]
        with patch.object(sys, "argv", argv):
            args = mod.parse_args()
        self.assertEqual(args.source, "lanes")
        self.assertTrue(str(args.out).endswith("f-ctl2-diff-latency-s186-structured.json"))

    def test_parse_lane_rows(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex-cli | domains/control-theory/tasks/FRONTIER.md | setup=codex focus=domains/control-theory | ACTIVE | expect=a actual=b diff=c |",
            ]
        )
        rows = mod.parse_lane_rows(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["lane"], "L-A")
        self.assertEqual(rows[0]["session"], "S186")

    def test_structured_event_detection(self):
        tags = {"expect": "a", "actual": "b", "diff": "c"}
        self.assertTrue(mod.is_structured_diff_event("expect=a actual=b diff=c", tags))
        self.assertFalse(mod.is_structured_diff_event("expect=a diff=c", {"expect": "a", "diff": "c"}))
        self.assertTrue(mod.is_structured_correction_event("correction=done", {"correction": "done"}))
        self.assertFalse(mod.is_structured_correction_event("fixed via keyword only", {}))

    def test_build_lane_session_rows_uses_structured_tags(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex-cli | domains/control-theory/tasks/FRONTIER.md | setup=codex expect=e actual=a diff=d | ACTIVE | tagged event |",
                "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex-cli | domains/control-theory/tasks/FRONTIER.md | setup=codex correction=done | MERGED | tagged correction |",
            ]
        )
        rows = mod.build_lane_session_rows(text, session_min=150)
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]["is_diff_event"])
        self.assertFalse(rows[0]["is_correction_event"])
        self.assertTrue(rows[1]["is_correction_event"])

    def test_diff_event_requires_expectation_and_large_diff(self):
        self.assertTrue(mod.is_diff_event("[S186] Expect-next prediction + diff logged, drift observed"))
        self.assertFalse(mod.is_diff_event("[S186] drift observed in session notes"))
        self.assertFalse(mod.is_diff_event("[S186] expect-next added during routine update"))

    def test_anchor_extraction_and_overlap(self):
        text = "[S186] F123 diff event for F-CTL2 with L-244 and P-182"
        anchors = mod.extract_anchors(text)
        self.assertIn("F123", anchors)
        self.assertIn("F-CTL2", anchors)
        self.assertIn("L-244", anchors)
        self.assertIn("P-182", anchors)

    def test_measure_latency_prefers_anchor_match(self):
        rows = [
            {
                "session": 180,
                "text": "[S180] expect-next drift on F-CTL2",
                "anchors": ["F-CTL2"],
                "is_diff_event": True,
                "is_correction_event": False,
            },
            {
                "session": 181,
                "text": "[S181] fixed unrelated F-FOO",
                "anchors": ["F-FOO"],
                "is_diff_event": False,
                "is_correction_event": True,
            },
            {
                "session": 182,
                "text": "[S182] corrected F-CTL2 detector settings",
                "anchors": ["F-CTL2"],
                "is_diff_event": False,
                "is_correction_event": True,
            },
        ]
        events = mod.measure_latency(rows)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["matched_correction_session"], 182)
        self.assertEqual(events[0]["lag_sessions"], 2)
        self.assertTrue(events[0]["anchor_matched"])

    def test_summarize_handles_unresolved(self):
        events = [
            {"lag_sessions": 1, "anchor_matched": True},
            {"lag_sessions": 3, "anchor_matched": False},
            {"lag_sessions": None, "anchor_matched": False},
        ]
        s = mod.summarize(events)
        self.assertEqual(s["diff_events_total"], 3)
        self.assertEqual(s["resolved_events"], 2)
        self.assertEqual(s["unresolved_events"], 1)
        self.assertEqual(s["same_session_resolved_events"], 0)
        self.assertEqual(s["cross_session_resolved_events"], 2)
        self.assertAlmostEqual(s["same_session_resolution_rate"], 0.0, places=4)
        self.assertAlmostEqual(s["mean_lag_sessions"], 2.0, places=4)
        self.assertAlmostEqual(s["cross_session_mean_lag_sessions"], 2.0, places=4)
        self.assertAlmostEqual(s["mean_lag_floor_1_sessions"], 2.0, places=4)
        self.assertAlmostEqual(s["p90_lag_sessions"], 3.0, places=4)

    def test_auto_routing_replay(self):
        events = [
            {"lag_sessions": 0},
            {"lag_sessions": 2},
            {"lag_sessions": 4},
            {"lag_sessions": None},
        ]
        replay = mod.simulate_auto_routing(events, route_after_sessions=1)
        self.assertEqual(replay["eligible_events"], 2)
        self.assertLess(replay["projected_mean_lag"], replay["baseline_mean_lag"])

    def test_summarize_exposes_same_session_clock_bias(self):
        events = [
            {"lag_sessions": 0, "anchor_matched": True},
            {"lag_sessions": 1, "anchor_matched": True},
            {"lag_sessions": 2, "anchor_matched": False},
        ]
        s = mod.summarize(events)
        self.assertEqual(s["same_session_resolved_events"], 1)
        self.assertEqual(s["cross_session_resolved_events"], 2)
        self.assertAlmostEqual(s["same_session_resolution_rate"], 0.3333, places=4)
        self.assertAlmostEqual(s["cross_session_mean_lag_sessions"], 1.5, places=4)
        self.assertAlmostEqual(s["mean_lag_floor_1_sessions"], 1.3333, places=4)


if __name__ == "__main__":
    unittest.main()
