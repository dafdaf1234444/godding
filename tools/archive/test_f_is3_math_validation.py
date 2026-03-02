#!/usr/bin/env python3
"""Regression tests for F-IS3 math validation tool."""

from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_is3_math_validation as mod


class TestFIS3MathValidation(unittest.TestCase):
    def test_simulated_utility_tracks_analytic_under_exchangeable_model(self):
        scenario = mod.Scenario(
            error_rate=0.25,
            rho=0.2,
            coordination_cost=0.03,
            risk_aversion=1.0,
            n_max=4,
            trials=6000,
        )
        result = mod.evaluate_scenario(scenario, seed=186)
        for row in result["rows"]:
            # Monte Carlo estimator should stay close to analytic baseline.
            self.assertLess(abs(row["analytic_utility"] - row["simulated_utility"]), 0.03)

    def test_heterogeneous_model_runs(self):
        scenario = mod.Scenario(
            error_rate=0.25,
            rho=0.2,
            coordination_cost=0.03,
            risk_aversion=1.0,
            n_max=4,
            trials=2000,
            model="heterogeneous",
            agent_sd=0.05,
            difficulty_sd=0.04,
        )
        result = mod.evaluate_scenario(scenario, seed=42)
        self.assertEqual(len(result["rows"]), scenario.n_max)
        for row in result["rows"]:
            self.assertIn("simulated_utility", row)

    def test_run_grid_counts_all_parameter_combinations(self):
        grid = mod.run_grid(
            error_rates=[0.2, 0.3],
            rhos=[0.0, 0.2],
            coordination_costs=[0.01, 0.04],
            risk_aversion=1.0,
            n_max=3,
            trials=1000,
            seed=7,
            model="exchangeable",
            agent_sd=0.0,
            difficulty_sd=0.0,
        )
        self.assertEqual(grid["scenario_count"], 8)
        self.assertGreaterEqual(grid["recommendation_match_rate"], 0.0)
        self.assertLessEqual(grid["recommendation_match_rate"], 1.0)
        self.assertGreater(grid["max_abs_utility_error"], 0.0)

    def test_load_model_from_spawn_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "model.json"
            p.write_text(
                json.dumps(
                    {
                        "model": {
                            "baseline_quality": 0.74,
                            "error_correlation_rho": 0.03,
                            "coordination_cost_per_extra_agent": 0.56,
                            "risk_aversion": 1.0,
                            "n_max": 6,
                        }
                    }
                ),
                encoding="utf-8",
            )
            scenario = mod._load_model_from_spawn_artifact(p)
            self.assertAlmostEqual(scenario.error_rate, 0.26, places=6)
            self.assertAlmostEqual(scenario.rho, 0.03, places=6)
            self.assertAlmostEqual(scenario.coordination_cost, 0.56, places=6)
            self.assertEqual(scenario.n_max, 6)


if __name__ == "__main__":
    unittest.main()
