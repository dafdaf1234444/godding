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
        self._orig_integration_backlog = dispatch_scoring._integration_backlog

    def tearDown(self):
        dispatch_scoring._soul_weights = self._orig_soul_weights
        dispatch_scoring._soul_mean_ratio = self._orig_soul_mean_ratio
        dispatch_scoring._integration_backlog = self._orig_integration_backlog

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

    def test_integration_backlog_bonus_only_hits_meta_and_decays_with_age(self):
        dispatch_scoring._soul_weights = {}
        dispatch_scoring._soul_mean_ratio = 1.0

        outcome_map = {
            "meta": {"merged": 10, "abandoned": 5, "lessons": 10, "lessons_l3plus": 0, "sharpe_sum": 115.5, "sharpe_count": 15},
            "physics": {"merged": 10, "abandoned": 5, "lessons": 10, "lessons_l3plus": 0, "sharpe_sum": 115.5, "sharpe_count": 15},
        }

        dispatch_scoring._integration_backlog = {
            "session": 536,
            "true_unreferenced": 58,
            "wire_count": 15,
            "archive_count": 21,
        }
        fresh_results = [
            {"domain": "meta", "score": 0.0},
            {"domain": "physics", "score": 0.0},
        ]
        dispatch_scoring.ucb1_score(fresh_results, outcome_map, {}, current_session=536, claimed=set())
        fresh = {row["domain"]: row for row in fresh_results}

        self.assertGreater(fresh["meta"]["integration_boost"], 0.8)
        self.assertEqual(fresh["physics"]["integration_boost"], 0.0)

        dispatch_scoring._integration_backlog = {
            "session": 526,
            "true_unreferenced": 58,
            "wire_count": 15,
            "archive_count": 21,
        }
        stale_results = [
            {"domain": "meta", "score": 0.0},
            {"domain": "physics", "score": 0.0},
        ]
        dispatch_scoring.ucb1_score(stale_results, outcome_map, {}, current_session=536, claimed=set())
        stale = {row["domain"]: row for row in stale_results}

        self.assertLess(stale["meta"]["integration_boost"], 0.2)
        self.assertEqual(stale["physics"]["integration_boost"], 0.0)


if __name__ == "__main__":
    unittest.main()
