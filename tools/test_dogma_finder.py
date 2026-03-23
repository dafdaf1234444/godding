#!/usr/bin/env python3
"""Regression tests for dogma_finder PHIL sub-claim handling."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))

import dogma_finder  # type: ignore


class TestParsePhilClaims(unittest.TestCase):
    def test_parse_phil_claims_includes_suffix_section_headers(self):
        phil_text = "\n".join(
            [
                "## How it works",
                "",
                "### 1a. Always learn [PHIL-5a]",
                "Observed behavior.",
                "",
                "### 1b. Never hurt [PHIL-5b]",
                "Aspirational behavior.",
                "",
                "| PHIL-5a | Always learn | observed | observed | active |",
                "| PHIL-5b | Never hurt | axiom | aspirational | active |",
            ]
        )

        with mock.patch.object(dogma_finder, "_read", return_value=phil_text):
            claims = dogma_finder.parse_phil_claims()

        by_id = {claim["id"]: claim for claim in claims}
        self.assertIn("PHIL-5a", by_id)
        self.assertIn("PHIL-5b", by_id)
        self.assertEqual(by_id["PHIL-5b"]["statement"], "Never hurt")
        self.assertEqual(by_id["PHIL-5b"]["grounding"], "aspirational")


class TestParseChallenges(unittest.TestCase):
    def test_parse_challenges_keeps_suffix_targets(self):
        philosophy_text = (
            "| PHIL-5b | S525 | EVIDENCE-IMMUNIZED challenge text | "
            "CHALLENGE S525: DROP — absorb into PHIL-14 Goal 3. |\n"
        )

        def fake_read(path: Path) -> str:
            if path == dogma_finder.PHIL:
                return philosophy_text
            return ""

        with mock.patch.object(dogma_finder, "_read", side_effect=fake_read):
            challenges = dogma_finder.parse_challenges()

        self.assertEqual(len(challenges), 1)
        self.assertEqual(challenges[0]["target"], "PHIL-5b")
        self.assertEqual(challenges[0]["status"], "CHALLENGE")


class TestDetectDogma(unittest.TestCase):
    def test_subclaims_inherit_parent_challenge_coverage(self):
        phil_claims = [
            {
                "id": "PHIL-5a",
                "statement": "Always learn",
                "content": "Observed claim.",
                "kind": "philosophy",
                "type": "axiom",
                "grounding": "observed",
                "status": "active",
            },
            {
                "id": "PHIL-5b",
                "statement": "Never hurt",
                "content": "Aspirational claim.",
                "kind": "philosophy",
                "type": "axiom",
                "grounding": "aspirational",
                "status": "active",
            },
        ]
        challenges = [
            {
                "session": 500,
                "target": "PHIL-5",
                "challenge": "Decomposed into PHIL-5a and PHIL-5b",
                "status": "DECOMPOSED",
                "source": "PHILOSOPHY.md",
            }
        ]

        with mock.patch.object(dogma_finder, "parse_beliefs", return_value=[]), \
             mock.patch.object(dogma_finder, "parse_phil_claims", return_value=phil_claims), \
             mock.patch.object(dogma_finder, "parse_challenges", return_value=challenges), \
             mock.patch.object(dogma_finder, "parse_principles", return_value=[]), \
             mock.patch.object(dogma_finder, "get_current_session", return_value=525), \
             mock.patch.object(dogma_finder, "sample_lesson_confidence", return_value={}), \
             mock.patch.object(dogma_finder, "_top_cited_lessons", return_value=[]), \
             mock.patch.object(dogma_finder, "_detect_meta_dogma", return_value=[]):
            findings = dogma_finder.detect_dogma()

        signals_by_id = {
            row["id"]: {signal["signal"] for signal in row["signals"]}
            for row in findings
        }
        self.assertNotIn("UNCHALLENGED", signals_by_id.get("PHIL-5a", set()))
        self.assertNotIn("UNCHALLENGED", signals_by_id.get("PHIL-5b", set()))


if __name__ == "__main__":
    unittest.main()
