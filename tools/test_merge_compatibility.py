#!/usr/bin/env python3
"""Regression tests for merge_compatibility.py."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import genesis_extract  # noqa: E402
import merge_compatibility  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class TestMergeCompatibility(unittest.TestCase):
    def test_extract_principles_handles_id_only_projection(self):
        sample = (
            "# Principles - Compact Daughter Projection\n"
            "Extracted from parent principles for lightweight genesis.\n"
            "3 live principles.\n\n"
            "## Live Principles\n"
            "- P-001\n"
            "- P-002\n"
            "- P-010\n"
        )

        with tempfile.TemporaryDirectory(prefix="merge-compat-") as tmpdir:
            principles_path = Path(tmpdir) / "PRINCIPLES.md"
            principles_path.write_text(sample, encoding="utf-8")
            principles = merge_compatibility.extract_principles(principles_path)

        self.assertEqual([entry["id"] for entry in principles], ["P-001", "P-002", "P-010"])
        self.assertTrue(all(entry["title"] == "" for entry in principles))

    def test_compare_principles_matches_parent_to_projected_ids(self):
        source = (ROOT / "memory" / "PRINCIPLES.md").read_text(encoding="utf-8", errors="ignore")
        projected = genesis_extract._project_principles_text(source)
        projected_count = sum(1 for line in projected.splitlines() if line.startswith("- P-"))

        with tempfile.TemporaryDirectory(prefix="merge-compat-") as tmpdir:
            projected_path = Path(tmpdir) / "PRINCIPLES.md"
            projected_path.write_text(projected, encoding="utf-8")
            local = merge_compatibility.extract_principles(ROOT / "memory" / "PRINCIPLES.md")
            remote = merge_compatibility.extract_principles(projected_path)

        compat = merge_compatibility.compare_principles(local, remote)

        self.assertEqual(len(remote), projected_count)
        self.assertEqual(compat["matched_pairs"], projected_count)
        self.assertGreaterEqual(compat["overlap_rate"], 0.99)


if __name__ == "__main__":
    unittest.main()
