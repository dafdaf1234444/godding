#!/usr/bin/env python3
"""Regression tests for F-OPS1 WIP-cap replay."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ops1_wip_limit as mod


class TestFOps1WipLimit(unittest.TestCase):
    def test_parse_lane_rows(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-1 | S186 | codex | local | - | GPT-5 | codex | tasks/NEXT.md | setup=x | READY | queued |",
                "| 2026-02-27 | L-1 | S186 | codex | local | - | GPT-5 | codex | tasks/NEXT.md | setup=x | MERGED | done |",
            ]
        )
        rows = mod.parse_lane_rows(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].tick, 0)
        self.assertEqual(rows[1].status, "MERGED")

    def test_build_lane_jobs_accepts_merge_only_rows(self):
        rows = mod.parse_lane_rows(
            "\n".join(
                [
                    "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex | x | setup=x | MERGED | direct close |",
                    "| 2026-02-27 | L-B | S186 | codex | local | - | GPT-5 | codex | y | setup=y | READY | queued |",
                ]
            )
        )
        jobs = mod.build_lane_jobs(rows)
        self.assertEqual(len(jobs), 2)
        by_lane = {job.lane: job for job in jobs}
        self.assertEqual(by_lane["L-A"].duration_ticks, 1)
        self.assertTrue(by_lane["L-A"].merged)
        self.assertFalse(by_lane["L-B"].merged)

    def test_simulate_cap_reduces_spillover_when_cap_increases(self):
        jobs = [
            mod.LaneJob("L1", start_tick=0, duration_ticks=4, merged=True, blocked_events=0, collision_events=0, source_rows=1),
            mod.LaneJob("L2", start_tick=0, duration_ticks=4, merged=True, blocked_events=0, collision_events=0, source_rows=1),
            mod.LaneJob("L3", start_tick=0, duration_ticks=4, merged=True, blocked_events=0, collision_events=0, source_rows=1),
        ]
        profile = mod.observed_profile(jobs)
        low = mod.simulate_cap(
            jobs,
            cap=1,
            horizon_start=int(profile["horizon_start"]),
            horizon_end=int(profile["horizon_end"]),
            observed_peak_wip=int(profile["observed_peak_wip"]),
            conflict_weight=0.8,
            overhead_weight=0.28,
        )
        high = mod.simulate_cap(
            jobs,
            cap=2,
            horizon_start=int(profile["horizon_start"]),
            horizon_end=int(profile["horizon_end"]),
            observed_peak_wip=int(profile["observed_peak_wip"]),
            conflict_weight=0.8,
            overhead_weight=0.28,
        )
        self.assertGreater(
            high["knowledge_yield"]["merged_completed"],
            low["knowledge_yield"]["merged_completed"],
        )
        self.assertLess(high["simulation"]["spillover_rate"], low["simulation"]["spillover_rate"])

    def test_evaluate_caps_prefers_lower_cap_on_exact_tie(self):
        jobs = [
            mod.LaneJob("L1", start_tick=0, duration_ticks=1, merged=True, blocked_events=0, collision_events=0, source_rows=1),
            mod.LaneJob("L2", start_tick=2, duration_ticks=1, merged=True, blocked_events=0, collision_events=0, source_rows=1),
        ]
        _, results, recommended = mod.evaluate_caps(
            jobs,
            min_cap=2,
            max_cap=4,
            conflict_weight=0.8,
            overhead_weight=0.28,
        )
        self.assertEqual(len(results), 3)
        self.assertEqual(recommended["cap"], 2)

    def test_build_ab_comparison_has_expected_delta_keys(self):
        results = [
            {
                "cap": 3,
                "net_score": 0.1,
                "knowledge_yield": {"merged_completion_rate": 0.6},
                "conflict_rate": 0.2,
                "overhead_ratio": 0.4,
                "simulation": {"blocked_per_merged": 0.1, "spillover_rate": 0.2},
            },
            {
                "cap": 5,
                "net_score": 0.2,
                "knowledge_yield": {"merged_completion_rate": 0.8},
                "conflict_rate": 0.22,
                "overhead_ratio": 0.9,
                "simulation": {"blocked_per_merged": 0.3, "spillover_rate": 0.1},
            },
        ]
        ab = mod.build_ab_comparison(results, cap_a=3, cap_b=5)
        self.assertTrue(ab["available"])
        self.assertAlmostEqual(ab["delta_b_minus_a"]["merged_completion_rate"], 0.2)
        self.assertIn("decision_hint", ab)

    def test_build_ab_comparison_prefers_cap_a_when_net_score_is_worse(self):
        results = [
            {
                "cap": 4,
                "net_score": 0.4,
                "knowledge_yield": {"merged_completion_rate": 0.6},
                "conflict_rate": 0.25,
                "overhead_ratio": 0.35,
                "simulation": {"blocked_per_merged": 0.1, "spillover_rate": 0.2},
            },
            {
                "cap": 5,
                "net_score": 0.3,
                "knowledge_yield": {"merged_completion_rate": 0.75},
                "conflict_rate": 0.28,
                "overhead_ratio": 0.65,
                "simulation": {"blocked_per_merged": 0.2, "spillover_rate": 0.15},
            },
        ]
        ab = mod.build_ab_comparison(results, cap_a=4, cap_b=5)
        self.assertTrue(ab["available"])
        self.assertLess(ab["delta_b_minus_a"]["net_score"], 0.0)
        self.assertEqual(ab["decision_hint"], "prefer_cap_a")

    def test_recommendation_confidence_flags_boundary(self):
        results = [
            {"cap": 1, "net_score": 0.35},
            {"cap": 2, "net_score": 0.34},
            {"cap": 3, "net_score": 0.2},
        ]
        conf = mod.recommendation_confidence(results, {"cap": 1, "net_score": 0.35}, min_cap=1, max_cap=3)
        self.assertEqual(conf["level"], "LOW")
        self.assertTrue(conf["boundary_recommendation"])


if __name__ == "__main__":
    unittest.main()
