#!/usr/bin/env python3
"""Regression tests for F-CTL3 open-loop quality analysis."""

import statistics
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ctl3_open_loop_quality as mod


class TestFCTL3OpenLoopQuality(unittest.TestCase):
    def test_classify_closed_loop_with_check_signal(self):
        sig = {
            "msgs": [
                "[S186] run check.sh --quick",
                "[S186] Beliefs: PASS maintenance notice-only",
            ]
        }
        out = mod.classify_session(sig)
        self.assertTrue(out["closed_loop"])
        self.assertTrue(out["has_check"])

    def test_classify_open_loop_when_orient_missing(self):
        sig = {"msgs": ["[S186] claim-vs-evidence audit and docs update"]}
        out = mod.classify_session(sig)
        self.assertFalse(out["closed_loop"])
        self.assertFalse(out["has_orient"])

    def test_summarize_empty(self):
        out = mod.summarize([])
        self.assertEqual(out["n_sessions"], 0)
        self.assertEqual(out["mean_score"], 0.0)

    def test_nearest_pair_delta(self):
        open_rows = [
            {"session": 180, "score": 1.0},
            {"session": 183, "score": 2.0},
        ]
        closed_rows = [
            {"session": 181, "score": 3.0},
            {"session": 190, "score": 9.0},
        ]
        out = mod.nearest_pair_delta(open_rows, closed_rows)
        self.assertEqual(out["n_pairs"], 2)
        self.assertAlmostEqual(
            out["mean_closed_minus_open"],
            round(statistics.fmean([2.0, 1.0]), 4),
            places=4,
        )


if __name__ == "__main__":
    unittest.main()
