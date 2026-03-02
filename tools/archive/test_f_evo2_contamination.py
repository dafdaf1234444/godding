#!/usr/bin/env python3
"""Regression tests for F-EVO2 contamination profiler."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_evo2_contamination as mod


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class TestFEvo2Contamination(unittest.TestCase):
    def test_lane_pressure_component(self):
        rows = [
            {"lane": "L-A", "status": "READY"},
            {"lane": "L-B", "status": "READY"},
            {"lane": "L-C", "status": "ACTIVE"},
        ]
        out = mod._lane_pressure_component(rows)
        self.assertEqual(out["ready_count"], 2)
        self.assertEqual(out["running_count"], 1)
        self.assertGreater(out["component"], 0.0)

    def test_build_report_high_contamination(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            lanes = base / "lanes.md"
            gam2 = base / "gam2.json"
            is5 = base / "is5.json"
            stat2 = base / "stat2.json"
            ops1 = base / "ops1.json"
            his2 = base / "his2.json"

            lanes.write_text(
                "\n".join(
                    [
                        "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| 2026-02-27 | L-A | S186 | c | b | - | m | p | x | setup=s focus=global | READY | q |",
                        "| 2026-02-27 | L-B | S186 | c | b | - | m | p | x | setup=s focus=global | READY | q |",
                        "| 2026-02-27 | L-C | S186 | c | b | - | m | p | x | setup=s focus=global | ACTIVE | q |",
                    ]
                ),
                encoding="utf-8",
            )

            _write_json(
                gam2,
                {
                    "frontier_id": "F-GAM2",
                    "analysis": {"integrity_summary": {"reputation_signal_rate_active": 0.1, "integrity_score": 0.9}},
                },
            )
            _write_json(
                is5,
                {
                    "experiment": "F-IS5",
                    "summary_metrics": {"merge_collision_frequency": 0.8, "transfer_acceptance_rate": 0.05},
                },
            )
            _write_json(
                stat2,
                {"frontier_id": "F-STAT2", "overall": {"I2_percent": 70.0, "pooled_effect": -0.03}},
            )
            _write_json(
                ops1,
                {"frontier_id": "F-OPS1", "recommended": {"conflict_rate": 0.5, "overhead_ratio": 1.5}, "ab_comparison": {"decision_hint": "inconclusive_needs_live_ab"}},
            )
            _write_json(
                his2,
                {"frontier_id": "F-HIS2", "analysis": {"missing_link_rate": 0.12, "inversion_rate": 0.02}},
            )

            report = mod.build_report(
                lanes_path=lanes,
                gam2_path=gam2,
                is5_path=is5,
                stat2_path=stat2,
                ops1_path=ops1,
                his2_path=his2,
            )
            self.assertEqual(report["experiment"], "F-EVO2")
            self.assertGreater(report["contamination_index"], 0.6)
            self.assertEqual(report["contamination_band"], "HIGH")
            self.assertTrue(report["decontamination_recommendations"])

    def test_classify_thresholds(self):
        self.assertEqual(mod._classify(0.2), "LOW")
        self.assertEqual(mod._classify(0.4), "MEDIUM")
        self.assertEqual(mod._classify(0.8), "HIGH")


if __name__ == "__main__":
    unittest.main()

