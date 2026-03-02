#!/usr/bin/env python3
"""Unit tests for local-place routing in context_router."""

from __future__ import annotations

import unittest

try:
    from tools import context_router  # type: ignore
except Exception:
    import context_router  # type: ignore


class TestContextRouterLocalPlace(unittest.TestCase):
    def test_domain_path_local_context_detects_domain(self):
        result = context_router.route_context(
            "lane handoff coordination",
            budget_lines=10000,
            local_context="domains/game-theory/tasks/FRONTIER.md",
        )
        local = result.get("local_context", {})
        self.assertEqual(local.get("detected_domain"), "domain_game_theory")
        domain_names = [item["name"] for item in result.get("domains", [])]
        self.assertIn("domain_game_theory", domain_names)

    def test_tool_prefix_local_context_detects_domain_and_keeps_file(self):
        result = context_router.route_context(
            "reputation integrity check",
            budget_lines=10000,
            local_context="tools/f_gam2_reputation_integrity.py",
        )
        local = result.get("local_context", {})
        self.assertEqual(local.get("detected_domain"), "domain_game_theory")
        selected_paths = [item["path"] for item in result.get("selected_files", [])]
        self.assertIn("tools/f_gam2_reputation_integrity.py", selected_paths)

    def test_core_swarm_path_maps_to_meta_domain(self):
        result = context_router.route_context(
            "state handoff",
            budget_lines=4000,
            local_context="tasks/NEXT.md",
        )
        local = result.get("local_context", {})
        self.assertEqual(local.get("detected_domain"), "domain_meta")
        self.assertTrue(local.get("boost_applied"))


if __name__ == "__main__":
    unittest.main()
