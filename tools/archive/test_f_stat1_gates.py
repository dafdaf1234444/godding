#!/usr/bin/env python3
"""Regression tests for F-STAT1 gate derivation."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_stat1_gates as mod


class TestFStat1Gates(unittest.TestCase):
    def test_fin1_extraction(self):
        payload = {
            "experiment": "F-FIN1",
            "mode": "live-wikipedia-capital-qa",
            "single_agent": {"trial_accuracies": [0.1, 0.2, 0.1, 0.0]},
            "majority_vote": {"trial_accuracies": [0.2, 0.3, 0.2, 0.1]},
        }
        m = mod._m_fin1(Path("x.json"), payload)
        self.assertIsNotNone(m)
        assert m is not None
        self.assertEqual(m.exp_class, "live_query")
        self.assertGreater(m.effect, 0.0)
        self.assertEqual(m.n, 4)

    def test_ai2_threshold_multi_extract(self):
        payload = {
            "experiment": "F-AI2/F-HLT2",
            "runs": [
                {"trials": 100, "async_joint": 0.1, "sync_joint": 0.2, "sync_inherit_prob": 0.5},
                {"trials": 120, "async_joint": 0.12, "sync_joint": 0.3, "sync_inherit_prob": 0.75},
            ],
        }
        rows = mod._m_ai2_threshold(Path("t.json"), payload)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r.exp_class == "live_query" for r in rows))
        self.assertTrue(all(r.effect > 0 for r in rows))

    def test_gate_fallback_when_no_passing(self):
        rows = [
            mod.Measurement("a", "live_query", "m", 4, 0.02, -0.1, 0.1, 0.2, ""),
            mod.Measurement("b", "live_query", "m", 6, 0.03, -0.05, 0.08, 0.3, ""),
        ]
        gate = mod._derive_gate(rows)
        self.assertEqual(gate["confidence"], "LOW")
        self.assertGreaterEqual(gate["recommended_min_n"], 6)
        self.assertGreaterEqual(gate["recommended_min_abs_effect"], 0.05)

    def test_run_writes_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            # Minimal fixture files for extraction.
            root = Path(td)
            (root / "experiments/finance").mkdir(parents=True, exist_ok=True)
            fin = {
                "experiment": "F-FIN1",
                "mode": "live-wikipedia-capital-qa",
                "single_agent": {"trial_accuracies": [0.1, 0.2, 0.1, 0.0]},
                "majority_vote": {"trial_accuracies": [0.2, 0.3, 0.2, 0.1]},
            }
            (root / "experiments/finance/f-fin1-factual-qa-s186.json").write_text(
                json.dumps(fin), encoding="utf-8"
            )

            old_root = mod.REPO_ROOT
            try:
                mod.REPO_ROOT = root
                out_path = root / "experiments/statistics/f-stat1-gates-s186.json"
                payload = mod.run(out_path=out_path)
            finally:
                mod.REPO_ROOT = old_root

            self.assertTrue(out_path.exists())
            self.assertIn("classes", payload)
            self.assertIn("live_query", payload["classes"])


if __name__ == "__main__":
    unittest.main()

