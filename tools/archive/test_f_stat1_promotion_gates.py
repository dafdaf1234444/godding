#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import f_stat1_promotion_gates as mod


class TestFStat1PromotionGates(unittest.TestCase):
    def test_classify_by_mode_and_shape(self):
        live = {"mode": "live-wikipedia-capital-qa-direct-answer"}
        self.assertEqual(mod._classify(Path("experiments/finance/f-fin1.json"), live), "live_query")

        sim = {"mode": "controlled-simulation"}
        self.assertEqual(mod._classify(Path("experiments/ai/f-ai2.json"), sim), "simulation")

        lane = {"summary_metrics": {"claims_total": 12}}
        self.assertEqual(
            mod._classify(Path("experiments/information-science/f-is5-lane.json"), lane),
            "lane_log_extraction",
        )

    def test_effect_values_include_paired_deltas(self):
        payload = {
            "mode": "controlled-simulation",
            "trials": 300,
            "async": {"joint_error_rate": 0.08, "leader_follower_error_correlation": 0.01},
            "sync": {"joint_error_rate": 0.22, "leader_follower_error_correlation": 1.0},
        }
        effects = mod._effect_values(payload)
        self.assertTrue(effects)
        self.assertTrue(any(value > 0.1 for value in effects))

    def test_run_builds_class_gates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sim_path = root / "sim.json"
            live_path = root / "live.json"
            lane_path = root / "lane.json"
            out_path = root / "result.json"

            sim_path.write_text(
                json.dumps(
                    {
                        "mode": "controlled-simulation",
                        "trials": 240,
                        "async": {"joint_error_rate": 0.10},
                        "sync": {"joint_error_rate": 0.28},
                    }
                ),
                encoding="utf-8",
            )
            live_path.write_text(
                json.dumps(
                    {
                        "mode": "live-wikipedia-capital-qa-direct-answer",
                        "trials_per_condition": 20,
                        "single_agent": {"summary": {"mean": 0.22}},
                        "majority_vote": {"summary": {"mean": 0.31}},
                    }
                ),
                encoding="utf-8",
            )
            lane_path.write_text(
                json.dumps(
                    {
                        "frontier_id": "F-IS5",
                        "summary_metrics": {
                            "claims_total": 30,
                            "transfer_acceptance_rate": 0.20,
                            "merge_collision_frequency": 0.10,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = mod.run(
                output_path=out_path,
                artifact_paths=[sim_path, live_path, lane_path],
                bootstrap_samples=300,
                seed=186,
            )

            self.assertTrue(out_path.exists())
            self.assertEqual(result["artifacts_usable"], 3)
            self.assertIn("simulation", result["class_gates"])
            self.assertIn("live_query", result["class_gates"])
            self.assertIn("lane_log_extraction", result["class_gates"])
            self.assertGreaterEqual(result["class_gates"]["simulation"]["recommended_min_sample_size"], 1)


if __name__ == "__main__":
    unittest.main()
