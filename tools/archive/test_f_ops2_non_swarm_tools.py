#!/usr/bin/env python3
"""Tests for F-OPS2 non-swarm tool ranking."""

from __future__ import annotations

import unittest

from tools.f_ops2_non_swarm_tools import (
    CANDIDATES,
    ToolCandidate,
    availability_from_state,
    rank_candidates,
    summarize,
)


class TestAvailability(unittest.TestCase):
    def test_ready_partial_missing(self) -> None:
        state = {"git": True, "gh": False}
        status, bonus, missing = availability_from_state(("git",), state)
        self.assertEqual(status, "ready")
        self.assertEqual(bonus, 1.0)
        self.assertEqual(missing, [])

        status, bonus, missing = availability_from_state(("git", "gh"), state)
        self.assertEqual(status, "partial")
        self.assertEqual(bonus, 0.4)
        self.assertEqual(missing, ["gh"])

        status, bonus, missing = availability_from_state(("gh",), state)
        self.assertEqual(status, "missing")
        self.assertEqual(bonus, 0.0)
        self.assertEqual(missing, ["gh"])


class TestRanking(unittest.TestCase):
    def test_ranking_prefers_available_high_value_tools(self) -> None:
        state = {command: False for candidate in CANDIDATES for command in candidate.commands}
        state["git"] = True
        state["rg"] = True

        ranked = rank_candidates(CANDIDATES, state)
        self.assertGreaterEqual(len(ranked), 3)
        self.assertEqual(ranked[0]["id"], "git-worktree")
        self.assertIn("ripgrep", [row["id"] for row in ranked[:3]])
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertGreater(float(ranked[0]["score"]), float(ranked[-1]["score"]))

    def test_summarize_outputs_expected_shape(self) -> None:
        custom = (
            ToolCandidate(
                tool_id="a",
                name="A",
                commands=("a",),
                category="x",
                swarm_gain=5.0,
                automation_gain=5.0,
                observability_gain=5.0,
                portability_gain=5.0,
                setup_effort=1.0,
                risk=1.0,
                rationale="x",
                next_step="x",
            ),
            ToolCandidate(
                tool_id="b",
                name="B",
                commands=("b",),
                category="x",
                swarm_gain=1.0,
                automation_gain=1.0,
                observability_gain=1.0,
                portability_gain=1.0,
                setup_effort=3.0,
                risk=3.0,
                rationale="x",
                next_step="x",
            ),
        )
        ranked = rank_candidates(custom, {"a": True, "b": False})
        summary = summarize(ranked, top_n=1)
        self.assertEqual(summary["tool_count"], 2)
        self.assertEqual(summary["ready_count"], 1)
        self.assertEqual(summary["missing_count"], 1)
        self.assertEqual(summary["top_recommendations"], ["a"])


if __name__ == "__main__":
    unittest.main()
