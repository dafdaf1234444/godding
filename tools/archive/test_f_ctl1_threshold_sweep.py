#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ctl1_threshold_sweep as mod


class TestFCTL1ThresholdSweep(unittest.TestCase):
    def test_load_points_latest_schema(self):
        rows = [
            {"session": 1, "total": 1000, "tier_schema": "A"},
            {"session": 2, "total": 1100, "tier_schema": "A"},
            {"session": 3, "total": 1200, "tier_schema": "B"},
            {"session": 4, "total": 1300, "tier_schema": "B"},
            {"session": 5, "total": 1400, "tier_schema": "B"},
            {"session": 6, "total": 1500, "tier_schema": "B"},
            {"session": 7, "total": 1600, "tier_schema": "B"},
            {"session": 8, "total": 1700, "tier_schema": "B"},
            {"session": 9, "total": 1800, "tier_schema": "B"},
            {"session": 10, "total": 1900, "tier_schema": "B"},
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "log.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            points = mod._load_points(path, schema_mode="latest")
        self.assertEqual(points[0].session, 3)
        self.assertEqual(points[-1].session, 10)

    def test_drift_series_detects_compaction_drop(self):
        points = [
            mod.Point(1, 1000),
            mod.Point(2, 1100),
            mod.Point(3, 1200),
            mod.Point(4, 900),  # 25% drop => compaction event
            mod.Point(5, 990),
        ]
        drifts, events = mod._drift_series(points, drop_threshold=0.04)
        self.assertEqual(events, [4])
        self.assertAlmostEqual(drifts[3], 0.0, places=6)
        self.assertGreater(drifts[4], 0.09)

    def test_run_writes_result(self):
        rows = []
        total = 10000
        for session in range(1, 15):
            if session in (6, 11):
                total = int(total * 0.9)
            else:
                total += 300
            rows.append({"session": session, "total": total, "tier_schema": "X"})

        with tempfile.TemporaryDirectory() as td:
            inp = Path(td) / "proxy-k-log.json"
            out = Path(td) / "result.json"
            inp.write_text(json.dumps(rows), encoding="utf-8")
            result = mod.run(inp, out, schema_mode="all")

            self.assertTrue(out.exists())
            self.assertIn("best_thresholds", result)
            self.assertIn("top_candidates", result)
            self.assertGreaterEqual(len(result["top_candidates"]), 1)


if __name__ == "__main__":
    unittest.main()
