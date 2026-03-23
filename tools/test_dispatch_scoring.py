#!/usr/bin/env python3
"""Regression tests for multiplicative soul weighting in dispatch_scoring.py."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import dispatch_scoring


class TestDispatchScoring(unittest.TestCase):
    def setUp(self):
        self._orig_soul_weights = dispatch_scoring._soul_weights
        self._orig_soul_mean_ratio = dispatch_scoring._soul_mean_ratio

    def tearDown(self):
        dispatch_scoring._soul_weights = self._orig_soul_weights
        dispatch_scoring._soul_mean_ratio = self._orig_soul_mean_ratio

    def test_soul_weighting_scales_with_base_score(self):
        dispatch_scoring._soul_weights = {
            "high-base": {"good": 8, "bad": 2, "ratio": 4.0},
            "low-base": {"good": 8, "bad": 2, "ratio": 4.0},
            "control": {"good": 5, "bad": 5, "ratio": 1.0},
        }
        dispatch_scoring._soul_mean_ratio = 3.0

        results = [
            {"domain": "high-base", "score": 0.0},
            {"domain": "low-base", "score": 0.0},
            {"domain": "control", "score": 0.0},
        ]
        outcome_map = {
            "high-base": {"merged": 40, "abandoned": 10, "lessons": 40, "lessons_l3plus": 0, "sharpe_sum": 385, "sharpe_count": 50},
            "low-base": {"merged": 4, "abandoned": 1, "lessons": 4, "lessons_l3plus": 0, "sharpe_sum": 38.5, "sharpe_count": 5},
            "control": {"merged": 10, "abandoned": 10, "lessons": 10, "lessons_l3plus": 0, "sharpe_sum": 154, "sharpe_count": 20},
        }

        dispatch_scoring.ucb1_score(results, outcome_map, {}, current_session=525, claimed=set())
        scored = {row["domain"]: row for row in results}

        self.assertEqual(scored["high-base"]["soul_multiplier"], scored["low-base"]["soul_multiplier"])
        self.assertGreater(scored["high-base"]["soul_boost"], scored["low-base"]["soul_boost"])
        self.assertGreater(scored["low-base"]["soul_boost"], 0.0)
        self.assertLess(scored["control"]["soul_multiplier"], 1.0)
        self.assertLess(scored["control"]["soul_boost"], 0.0)


if __name__ == "__main__":
    unittest.main()
