#!/usr/bin/env python3
"""Regression tests for F-STAT1 gate calibration."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_stat1_experiment_gates as mod


class TestFSTAT1ExperimentGates(unittest.TestCase):
    def test_bootstrap_ci_single_value(self):
        lo, hi = mod._bootstrap_ci_mean([0.12], resamples=100, seed=1)
        self.assertEqual(lo, 0.12)
        self.assertEqual(hi, 0.12)

    def test_stability_all_positive(self):
        self.assertEqual(mod._stability([0.1, 0.2, 0.3]), 1.0)

    def test_summarize_class_unstable_requires_more_runs(self):
        runs = [
            mod.RunPoint("live_query", "a.json", 0.1, 5),
            mod.RunPoint("live_query", "b.json", -0.1, 5),
            mod.RunPoint("live_query", "c.json", 0.0, 5),
        ]
        summary = mod._summarize_class("live_query", runs)
        self.assertGreaterEqual(summary["recommended_gate"]["min_runs"], 6)

    def test_recommended_min_sample_floor(self):
        self.assertEqual(mod._recommended_min_sample("live_query", 2), 8)
        self.assertEqual(mod._recommended_min_sample("lane_log_extraction", 10), 20)
        self.assertEqual(mod._recommended_min_sample("simulation_control", 12), 30)


if __name__ == "__main__":
    unittest.main()
