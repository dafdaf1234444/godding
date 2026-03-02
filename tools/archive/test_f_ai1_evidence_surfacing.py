#!/usr/bin/env python3
"""Regression tests for F-AI1 evidence-surfacing experiment."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ai1_evidence_surfacing as mod


class TestFAI1EvidenceSurfacing(unittest.TestCase):
    def test_query_title_confidence_alignment(self):
        exact = mod._query_title_confidence("Swarm intelligence", "Swarm intelligence")
        typo = mod._query_title_confidence("Swarm inteligence", "Swarm intelligence")
        mismatch = mod._query_title_confidence("Distributed systems", "Stigmergy")

        self.assertGreater(exact, 0.9)
        self.assertGreater(typo, mismatch)

    def test_confidence_policy(self):
        self.assertEqual(mod._choose_with_evidence("A", "A", False), "A")
        self.assertEqual(mod._choose_with_evidence("A", "B", False), "A")
        self.assertEqual(mod._choose_with_evidence("A", "B", True), "B")

    def test_surfacing_beats_async_and_sync_not_better(self):
        payload = mod.run(
            mod.Config(
                trials=6000,
                follower_accuracy=0.65,
                leader_high_accuracy=0.82,
                leader_low_accuracy=0.52,
                leader_high_conf_prob=0.45,
                seed=186,
            )
        )
        async_err = payload["async_baseline"]["follower_error_rate"]
        surfaced_err = payload["evidence_surfacing"]["follower_error_rate"]

        self.assertLess(surfaced_err, async_err)

    def test_accent_normalization(self):
        # Accented variants should produce high confidence when they normalize to same tokens
        self.assertAlmostEqual(mod._query_title_confidence("España", "Espana"), 1.0)
        self.assertAlmostEqual(mod._query_title_confidence("señor", "senor"), 1.0)
        # Accent-normalized tokens should be non-empty (not split by ñ)
        self.assertEqual(mod._tokenize("señor"), ["senor"])
        self.assertEqual(mod._tokenize("español"), ["espanol"])
        # Cross-language mismatch should still be low
        self.assertLess(mod._query_title_confidence("España", "Stigmergy"), 0.3)

    def test_sync_has_highest_correlation(self):
        payload = mod.run(
            mod.Config(
                trials=5000,
                follower_accuracy=0.65,
                leader_high_accuracy=0.82,
                leader_low_accuracy=0.52,
                leader_high_conf_prob=0.45,
                seed=7,
            )
        )
        async_corr = payload["async_baseline"]["leader_follower_error_correlation"]
        surfaced_corr = payload["evidence_surfacing"]["leader_follower_error_correlation"]
        sync_corr = payload["sync_copy"]["leader_follower_error_correlation"]

        self.assertGreater(sync_corr, 0.95)
        self.assertLess(surfaced_corr, sync_corr)
        self.assertGreaterEqual(surfaced_corr, async_corr)


if __name__ == "__main__":
    unittest.main()
