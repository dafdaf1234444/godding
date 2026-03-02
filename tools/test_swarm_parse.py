#!/usr/bin/env python3
"""Regression tests for shared swarm parsing helpers."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import swarm_parse  # noqa: E402


class TestSwarmParse(unittest.TestCase):
    def test_active_principle_ids_tracks_superseded_patterns(self):
        text = """
P-100 remains active.
P-101→P-120 migration complete.
(P-103 absorbed) into consolidated guidance.
P-104+P-105 merged into one principle.
"""
        all_ids, superseded = swarm_parse.active_principle_ids(text)

        self.assertEqual(all_ids, {100, 101, 103, 104, 105, 120})
        self.assertEqual(superseded, {101, 103, 104, 105})

    def test_active_frontier_ids_extracts_open_frontier_bullets(self):
        text = """
- **F101**: Domain sharding follow-through.
- **F115**: Living self-paper checks.
- **F9** no colon, should not match.
"""
        self.assertEqual(swarm_parse.active_frontier_ids(text), {101, 115})

    def test_archived_frontier_ids_extracts_table_rows(self):
        text = """
| F92 | RESOLVED | Colony-size conditional rule |
| F118 | RESOLVED | Multi-tool node capability |
| X1 | ignore | not a frontier id |
"""
        self.assertEqual(swarm_parse.archived_frontier_ids(text), {92, 118})


if __name__ == "__main__":
    unittest.main()
