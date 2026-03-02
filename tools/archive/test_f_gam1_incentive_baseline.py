#!/usr/bin/env python3
"""Regression tests for F-GAM1 incentive baseline harness."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_gam1_incentive_baseline as mod


class TestFGAM1IncentiveBaseline(unittest.TestCase):
    def test_entropy_basic(self):
        low = mod._entropy({"a": 1.0, "b": 0.0, "c": 0.0})
        high = mod._entropy({"a": 0.34, "b": 0.33, "c": 0.33})
        self.assertGreater(high, low)

    def test_extract_metrics(self):
        payload = {
            "contexts": {
                "cooperative": {
                    "group_accuracy_mean": 0.9,
                    "final_share_mean": {
                        "collaborator": 0.8,
                        "deceptor": 0.05,
                        "neutral": 0.15,
                    },
                },
                "competitive": {
                    "group_accuracy_mean": 0.7,
                    "final_share_mean": {
                        "collaborator": 0.5,
                        "deceptor": 0.2,
                        "neutral": 0.3,
                    },
                },
            }
        }
        metrics = mod._extract_metrics(payload)
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics["delta_comp_minus_coop"]["deceptor_share_mean"], 0)
        self.assertLess(metrics["delta_comp_minus_coop"]["group_accuracy_mean"], 0)

    def test_summarize_sign_stability(self):
        stats = mod._summarize([0.1, 0.2, 0.3, -0.1])
        self.assertGreaterEqual(stats["sign_stability"], 0.75)


if __name__ == "__main__":
    unittest.main()
