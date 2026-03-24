#!/usr/bin/env python3
"""Regression tests for compact.py EXPIRED-candidate visibility."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compact  # noqa: E402


class TestCompactExpiredVisibility(unittest.TestCase):
    def test_format_expired_section_reports_summary_and_omissions(self):
        candidates = [
            {"id": "L-100", "age": 200, "est_tokens": 55, "sharpe": -1, "action": "archive", "title": "Old lesson"},
            {"id": "L-101", "age": 150, "est_tokens": 45, "sharpe": 1, "action": "archive", "title": "Older lesson"},
        ]

        lines = compact._format_expired_section(candidates, total_count=4, total_tokens=180, limit=2)

        self.assertIn("EXPIRED lesson candidates (4, ~180t total):", lines[0])
        self.assertIn("Criteria: zero inbound citations", lines[1])
        self.assertTrue(any("L-100" in line and "-> archive" in line for line in lines))
        self.assertEqual(lines[-1], "    ... and 2 more (full list: python3 tools/knowledge_swarm.py --json)")

    def test_knowledge_swarm_expired_candidates_respects_limit(self):
        original = {
            "_HAS_KNOWLEDGE_SWARM": compact._HAS_KNOWLEDGE_SWARM,
            "_ks_lesson_paths": compact._ks_lesson_paths,
            "_ks_parse_lesson_meta": compact._ks_parse_lesson_meta,
            "_ks_build_citation_maps": compact._ks_build_citation_maps,
            "_ks_classify_items": compact._ks_classify_items,
            "_ks_compress_candidates": compact._ks_compress_candidates,
            "_ks_session_number": compact._ks_session_number,
        }
        try:
            compact._HAS_KNOWLEDGE_SWARM = True
            compact._ks_lesson_paths = lambda: [Path("L-100.md"), Path("L-101.md")]
            compact._ks_parse_lesson_meta = lambda path: {
                "id": path.stem,
                "title": path.stem,
                "session": 400,
                "domain": "meta",
                "sharpe": -1,
                "cites": set(),
                "line_count": 10,
            }
            compact._ks_build_citation_maps = lambda lessons: ({}, {})
            compact._ks_classify_items = lambda lessons, inbound, current: {lid: "DECAYED" for lid in lessons}
            compact._ks_compress_candidates = lambda lessons, states, inbound, current: [
                {"id": "L-100", "title": "First", "sharpe": -1, "age": 200, "est_tokens": 55, "action": "archive"},
                {"id": "L-101", "title": "Second", "sharpe": 1, "age": 150, "est_tokens": 45, "action": "archive"},
                {"id": "L-102", "title": "Third", "sharpe": 0, "age": 125, "est_tokens": 65, "action": "archive"},
            ]
            compact._ks_session_number = lambda: 532

            candidates, total_count, total_tokens = compact._knowledge_swarm_expired_candidates(limit=2)

            self.assertEqual(len(candidates), 2)
            self.assertEqual(total_count, 3)
            self.assertEqual(total_tokens, 165)
            self.assertEqual([c["id"] for c in candidates], ["L-100", "L-101"])
        finally:
            for name, value in original.items():
                setattr(compact, name, value)


if __name__ == "__main__":
    unittest.main()
