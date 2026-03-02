#!/usr/bin/env python3
"""Regression tests for F-STAT2 random-effects analysis."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_stat2_meta_analysis as mod


class TestFStat2MetaAnalysis(unittest.TestCase):
    def test_random_effects_identical_studies(self):
        studies = [
            {"effect": 0.1, "se": 0.05},
            {"effect": 0.1, "se": 0.05},
            {"effect": 0.1, "se": 0.05},
        ]
        out = mod.random_effects(studies)
        self.assertAlmostEqual(out["pooled_effect"], 0.1, places=6)
        self.assertAlmostEqual(out["tau2"], 0.0, places=6)
        self.assertAlmostEqual(out["I2_percent"], 0.0, places=6)

    def test_random_effects_heterogeneity_increases_tau2(self):
        studies = [
            {"effect": -0.2, "se": 0.02},
            {"effect": 0.0, "se": 0.02},
            {"effect": 0.25, "se": 0.02},
        ]
        out = mod.random_effects(studies)
        self.assertGreater(out["tau2"], 0.0)
        self.assertGreater(out["I2_percent"], 0.0)

    def test_transfer_label(self):
        self.assertEqual(mod._transfer_label(0.01, 0.10, 10.0), "positive-transfer-signal")
        self.assertEqual(mod._transfer_label(0.01, 0.10, 90.0), "positive-but-heterogeneous")
        self.assertEqual(mod._transfer_label(-0.10, -0.01, 10.0), "negative-transfer-signal")
        self.assertEqual(mod._transfer_label(-0.05, 0.03, 10.0), "inconclusive")

    def test_detect_fin1_regime_prefers_mode_and_fallback_path(self):
        direct = {"mode": "live-wikipedia-capital-qa-direct-answer"}
        proxy = {"mode": "live-wikipedia-capital-qa"}
        unknown = {}
        self.assertEqual(mod._detect_fin1_regime(direct, Path("x.json")), "direct_answer")
        self.assertEqual(mod._detect_fin1_regime(proxy, Path("x.json")), "resolver_proxy")
        self.assertEqual(
            mod._detect_fin1_regime(unknown, Path("f-fin1-factual-qa-direct-rerun-s186.json")),
            "direct_answer",
        )

    def test_finance_regime_summary_emits_delta(self):
        studies = [
            {
                "family": "finance_factual_qa_direct_answer",
                "scoring_regime": "direct_answer",
                "effect": 0.1,
                "se": 0.05,
            },
            {
                "family": "finance_factual_qa_resolver_proxy",
                "scoring_regime": "resolver_proxy",
                "effect": 0.0,
                "se": 0.05,
            },
        ]
        out = mod._summarize_finance_regimes(studies)
        self.assertIn("direct_answer", out["regimes"])
        self.assertIn("resolver_proxy", out["regimes"])
        self.assertGreater(out["pooled_effect_delta_direct_minus_proxy"], 0.0)


if __name__ == "__main__":
    unittest.main()
