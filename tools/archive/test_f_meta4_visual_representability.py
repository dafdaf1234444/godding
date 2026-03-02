#!/usr/bin/env python3
"""Regression tests for F-META4 visual representability baseline tool."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_meta4_visual_representability as mod


class TestFMeta4VisualRepresentability(unittest.TestCase):
    def test_analyze_contract_full_coverage(self):
        text = "\n".join(mod.EXPECTED_PRIMITIVES + mod.EXPECTED_VIEWS + mod.FRESHNESS_MARKERS)
        result = mod.analyze_contract(text)
        self.assertEqual(result["primitive_coverage"]["coverage_ratio"], 1.0)
        self.assertEqual(result["view_coverage"]["coverage_ratio"], 1.0)
        self.assertEqual(result["freshness_rule_coverage"]["coverage_ratio"], 1.0)
        self.assertEqual(result["contract_score"], 1.0)

    def test_analyze_contract_reports_missing(self):
        text = "Node: `Frontier`\n### 1) Human Orientation View\n`session`"
        result = mod.analyze_contract(text)
        self.assertLess(result["primitive_coverage"]["coverage_ratio"], 1.0)
        self.assertGreater(len(result["primitive_coverage"]["missing"]), 0)
        self.assertLess(result["view_coverage"]["coverage_ratio"], 1.0)

    def test_analyze_adoption_counts_checks(self):
        texts = {
            "README.md": "SWARM-VISUAL-REPRESENTABILITY.md",
            "memory/INDEX.md": "SWARM-VISUAL-REPRESENTABILITY.md",
            "domains/meta/tasks/FRONTIER.md": "F-META4",
            "domains/meta/INDEX.md": "F-META4",
            "tasks/SWARM-LANES.md": "F-META4",
        }
        result = mod.analyze_adoption(texts)
        self.assertEqual(result["passed"], result["total"])
        self.assertEqual(result["adoption_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
