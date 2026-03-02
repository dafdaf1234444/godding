#!/usr/bin/env python3
"""Tests for F-STAT1 canonical policy reconciliation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_stat1_canonical_policy as mod


class TestFStat1CanonicalPolicy(unittest.TestCase):
    def test_reconcile_live_query_marks_power_and_regime_issues(self):
        row = mod._reconcile_class(
            "live_query",
            {"min_runs": 15, "sample_size": 8, "effect_size": 0.0477},
            {
                "sample_size": 300,
                "effect_size": 0.05,
                "power_model_n_for_80pct": 1565,
                "estimated_power_at_recommended_n": 0.2315,
                "data_confidence": "HIGH",
            },
            {"sample_size": 300, "effect_size": 0.1733, "confidence": "HIGH"},
        )
        gate = row["canonical_gate"]
        self.assertEqual(gate["min_runs"], 15)
        self.assertEqual(gate["min_per_run_sample"], 300)
        self.assertEqual(gate["min_abs_effect"], 0.1733)
        self.assertEqual(row["status"], "PROVISIONAL")
        issues = row["diagnostics"]["issues"]
        self.assertIn("underpowered_practical_cap", issues)
        self.assertIn("mixed_regime_risk", issues)

    def test_reconcile_simulation_ready_when_sources_agree(self):
        row = mod._reconcile_class(
            "simulation",
            {"min_runs": 4, "sample_size": 60, "effect_size": 0.15},
            {"sample_size": 64, "effect_size": 0.16, "data_confidence": "HIGH"},
            {"sample_size": 62, "effect_size": 0.155, "confidence": "HIGH"},
        )
        self.assertEqual(row["status"], "READY")
        self.assertEqual(row["confidence"], "HIGH")
        self.assertEqual(row["canonical_gate"]["min_per_run_sample"], 64)
        self.assertEqual(row["canonical_gate"]["min_abs_effect"], 0.16)

    def test_run_writes_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            exp = base / "exp.json"
            prom = base / "prom.json"
            replay = base / "replay.json"
            out = base / "out.json"

            exp.write_text(
                json.dumps(
                    {
                        "class_summaries": [
                            {
                                "class_name": "live_query",
                                "run_count": 10,
                                "recommended_gate": {
                                    "min_runs": 12,
                                    "min_per_run_sample": 20,
                                    "min_abs_effect": 0.08,
                                },
                            },
                            {
                                "class_name": "simulation_control",
                                "run_count": 8,
                                "recommended_gate": {
                                    "min_runs": 6,
                                    "min_per_run_sample": 40,
                                    "min_abs_effect": 0.12,
                                },
                            },
                            {
                                "class_name": "lane_log_extraction",
                                "run_count": 8,
                                "recommended_gate": {
                                    "min_runs": 8,
                                    "min_per_run_sample": 30,
                                    "min_abs_effect": 0.2,
                                },
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            prom.write_text(
                json.dumps(
                    {
                        "class_gates": {
                            "live_query": {
                                "recommended_min_sample_size": 50,
                                "recommended_min_effect_size": 0.1,
                                "power_model_n_for_80pct": 50,
                                "estimated_power_at_recommended_n": 0.81,
                                "data_confidence": "HIGH",
                            },
                            "simulation": {
                                "recommended_min_sample_size": 44,
                                "recommended_min_effect_size": 0.13,
                                "data_confidence": "HIGH",
                            },
                            "lane_log_extraction": {
                                "recommended_min_sample_size": 31,
                                "recommended_min_effect_size": 0.22,
                                "data_confidence": "MEDIUM",
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            replay.write_text(
                json.dumps(
                    {
                        "classes": {
                            "live_query": {
                                "recommended_min_n": 48,
                                "recommended_min_abs_effect": 0.11,
                                "confidence": "HIGH",
                            },
                            "simulation_replay": {
                                "recommended_min_n": 43,
                                "recommended_min_abs_effect": 0.14,
                                "confidence": "MEDIUM",
                            },
                            "lane_log_extraction": {
                                "recommended_min_n": 32,
                                "recommended_min_abs_effect": 0.21,
                                "confidence": "MEDIUM",
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )

            payload = mod.run(
                experiment_path=exp,
                promotion_path=prom,
                replay_path=replay,
                out_path=out,
            )
            self.assertTrue(out.exists())
            self.assertIn("policy", payload)
            self.assertEqual(len(payload["policy"]), 3)
            self.assertEqual(payload["summary"]["all_classes_ready"], True)


if __name__ == "__main__":
    unittest.main()

