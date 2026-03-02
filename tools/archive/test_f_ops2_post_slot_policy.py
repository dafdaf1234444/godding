#!/usr/bin/env python3
"""Regression tests for F-OPS2 post-slot consolidation policy tool."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ops2_post_slot_policy as mod


class TestFOps2PostSlotPolicy(unittest.TestCase):
    def test_wip_policy_stays_cap4_when_net_negative(self):
        ops1 = {
            "recommended": {"cap": 4},
            "recommendation_confidence": {"level": "MEDIUM"},
            "ab_comparison": {
                "decision_hint": "inconclusive_needs_live_ab",
                "delta_b_minus_a": {
                    "net_score": -0.11,
                    "conflict_rate": 0.01,
                    "overhead_ratio": 0.62,
                },
            },
        }
        out = mod.derive_wip_policy(ops1)
        self.assertEqual(out["default_wip_cap"], 4)
        self.assertFalse(out["cap5_promotion_ready_now"])

    def test_overlap_policy_flags_disagreement_reduction(self):
        is5 = {
            "recommended": {
                "shared_per_lane": 2,
                "transfer_acceptance_rate": 0.0882,
                "merge_collision_frequency": 0.6,
                "contested_transfer_candidates": 10,
            }
        }
        out = mod.derive_overlap_policy(is5)
        self.assertEqual(out["shared_per_lane_default"], 2)
        self.assertTrue(out["disagreement_reduction_needed"])

    def test_promotion_policy_stays_unlocked_with_provisional_classes(self):
        stat1 = {
            "policy": [
                {"class_name": "live_query", "status": "PROVISIONAL"},
                {"class_name": "simulation", "status": "PROVISIONAL"},
            ],
            "summary": {"all_classes_ready": False},
        }
        stat2 = {
            "transfer_decision": {"label": "inconclusive"},
            "overall": {"I2_percent": 57.2},
            "by_family": {
                "information_science_lane_distill": {"I2_percent": 82.5}
            },
        }
        stat3 = {
            "by_family": {
                "information_science_lane_distill": {"promotion_ready": True}
            }
        }
        out = mod.derive_promotion_policy(stat1, stat2, stat3)
        self.assertFalse(out["policy_lock_recommended"])
        self.assertIn("live_query", out["provisional_classes"])
        self.assertEqual(out["transfer_decision"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
