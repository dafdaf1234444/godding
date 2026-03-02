#!/usr/bin/env python3
"""Regression tests for p155_live_trace simulation behavior."""

import sys
import unittest
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p155_live_trace as p155


class TestP155LiveTrace(unittest.TestCase):
    def test_emit_trace_collaborator_is_truthful(self):
        trace, truthful = p155._emit_trace("collaborator", signal=1, rng=Random(1))
        self.assertEqual(trace, 1)
        self.assertTrue(truthful)

    def test_emit_trace_deceptor_flips_signal(self):
        trace, truthful = p155._emit_trace("deceptor", signal=1, rng=Random(1))
        self.assertEqual(trace, 0)
        self.assertFalse(truthful)

    def test_emit_trace_neutral_consistency(self):
        trace, truthful = p155._emit_trace("neutral", signal=0, rng=Random(7))
        self.assertIn(trace, (0, 1))
        self.assertEqual(truthful, trace == 0)

    def test_softmax_pick_prefers_high_value_with_sharp_beta(self):
        values = {"collaborator": 3.0, "deceptor": -1.0, "neutral": -1.0}
        picks = [p155._softmax_pick(values, beta=10.0, rng=Random(i)) for i in range(50)]
        collaborator_share = picks.count("collaborator") / len(picks)
        self.assertGreater(collaborator_share, 0.95)

    def test_incentive_shift_direction(self):
        cfg = p155.Config(
            agents=10,
            rounds=120,
            trials=40,
            seed=155,
            signal_accuracy=0.70,
            learning_rate=0.12,
            selection_beta=2.8,
            tail_window=40,
            trace_samples=20,
        )
        cooperative = p155.run_context("cooperative", cfg)
        competitive = p155.run_context("competitive", cfg)

        deceptor_delta = (
            competitive["final_share_mean"]["deceptor"]
            - cooperative["final_share_mean"]["deceptor"]
        )
        accuracy_delta = (
            competitive["group_accuracy_mean"]
            - cooperative["group_accuracy_mean"]
        )

        self.assertGreater(deceptor_delta, 0.10)
        self.assertLess(accuracy_delta, -0.10)


if __name__ == "__main__":
    unittest.main()
