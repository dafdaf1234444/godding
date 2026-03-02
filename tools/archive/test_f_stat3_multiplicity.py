#!/usr/bin/env python3
"""Regression tests for F-STAT3 multiplicity controls."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_stat3_multiplicity as mod


class TestFStat3Multiplicity(unittest.TestCase):
    def test_z_to_p_two_sided(self):
        self.assertAlmostEqual(mod._z_to_p_two_sided(0.0), 1.0, places=6)
        self.assertLess(mod._z_to_p_two_sided(3.0), 0.01)

    def test_bh_monotone_bounds(self):
        p = [0.001, 0.02, 0.04, 0.9]
        q = mod.benjamini_hochberg(p)
        self.assertEqual(len(q), len(p))
        self.assertTrue(all(0.0 <= x <= 1.0 for x in q))
        self.assertLessEqual(q[0], q[1])

    def test_family_summary_requires_replication_and_bh(self):
        rows = [
            {
                "effect": 0.2,
                "se": 0.05,
                "p_two_sided": 0.01,
                "q_bh": 0.02,
                "p_bonferroni": 0.04,
            },
            {
                "effect": 0.1,
                "se": 0.05,
                "p_two_sided": 0.04,
                "q_bh": 0.03,
                "p_bonferroni": 0.08,
            },
        ]
        out = mod._family_summary(rows, alpha=0.05, nominal_alpha=0.1, min_replications=2)
        self.assertTrue(out["promotion_ready"])
        self.assertEqual(out["bh_discoveries"], 2)
        self.assertEqual(out["replication_count"], 2)


if __name__ == "__main__":
    unittest.main()
