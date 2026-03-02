#!/usr/bin/env python3
"""Regression tests for F-IS6 unchallenged-principles audit."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_is6_unchallenged_beliefs as mod


class TestFIs6UnchallengedBeliefs(unittest.TestCase):
    def test_parse_principles_extracts_theme_and_claim(self):
        text = "\n".join(
            [
                "## Strategy",
                "**Operations**: P-009 automate manual processes first | P-020 encode bootstrap into executable script",
                "## Governance",
                "**Scaling**: P-119 spawn discipline gates utilization (L-217, OBSERVED)",
                "Removed: P-001 old",
            ]
        )
        rows = mod.parse_principles(text)
        self.assertEqual(rows["P-009"].theme, "Strategy")
        self.assertEqual(rows["P-009"].evidence, "UNSPECIFIED")
        self.assertIn("automate manual processes first", rows["P-009"].claim)
        self.assertEqual(rows["P-119"].theme, "Governance")
        self.assertEqual(rows["P-119"].evidence, "OBSERVED")
        self.assertNotIn("P-001", rows)

    def test_analyze_ranks_unchallenged_candidates(self):
        principles = "\n".join(
            [
                "## Governance",
                "**Scaling**: P-119 spawn discipline gates utilization (L-217, OBSERVED)",
                "## Strategy",
                "**Operations**: P-009 automate manual processes first | P-020 encode bootstrap into executable script",
                "## Protocols",
                "**Verification**: P-158 persuasion != accuracy (L-158, PARTIALLY OBSERVED)",
            ]
        )
        challenges = "\n".join(
            [
                "| Session | Target | Challenge | Evidence | Proposed | Status |",
                "| --- | --- | --- | --- | --- | --- |",
                "| S65 | P-020 | test | L-1 | next | CONFIRMED |",
            ]
        )
        next_text = "Updated: 2026-02-27 S186"
        first_seen = {"P-009": 53, "P-020": 53, "P-119": 57, "P-158": 91}

        analysis = mod.analyze(
            principles,
            challenges,
            next_text,
            repo_root=Path("."),
            longstanding_cutoff=40,
            top_n=5,
            session_resolver=lambda pid: first_seen.get(pid),
        )

        self.assertEqual(analysis["total_principles"], 4)
        self.assertEqual(analysis["challenged_principles"], 1)
        self.assertEqual(analysis["longstanding_unchallenged_count"], 3)
        self.assertGreaterEqual(len(analysis["high_leverage_candidates"]), 1)
        self.assertEqual(analysis["high_leverage_candidates"][0]["id"], "P-009")

    def test_run_writes_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            principles = root / "PRINCIPLES.md"
            challenges = root / "CHALLENGES.md"
            next_md = root / "NEXT.md"
            out = root / "out.json"

            principles.write_text(
                "\n".join(
                    [
                        "## Strategy",
                        "**Operations**: P-009 automate manual processes first",
                    ]
                ),
                encoding="utf-8",
            )
            challenges.write_text(
                "\n".join(
                    [
                        "| Session | Target | Challenge | Evidence | Proposed | Status |",
                        "| --- | --- | --- | --- | --- | --- |",
                    ]
                ),
                encoding="utf-8",
            )
            next_md.write_text("Updated: 2026-02-27 S186", encoding="utf-8")

            payload = mod.run(
                principles_path=principles,
                challenges_path=challenges,
                next_path=next_md,
                out_path=out,
                longstanding_cutoff=40,
                top_n=3,
            )

            self.assertTrue(out.exists())
            self.assertEqual(payload["frontier_id"], "F-IS6")
            self.assertEqual(payload["analysis"]["total_principles"], 1)


if __name__ == "__main__":
    unittest.main()

