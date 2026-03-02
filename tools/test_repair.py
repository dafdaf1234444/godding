#!/usr/bin/env python3
"""Regression tests for deterministic repair planning."""

import unittest

import repair


class TestRepairPlanning(unittest.TestCase):
    def test_plans_hook_install_once_for_multiple_signals(self):
        output = "\n".join(
            [
                "Missing hook(s): commit-msg — run: bash tools/install-hooks.sh",
                "Hook drift detected (pre-commit) — run: bash tools/install-hooks.sh",
            ]
        )
        actions = repair.plan_repairs(
            output,
            has_bash=True,
            clean_tree=False,
            python_executable="python3",
        )
        self.assertEqual([a.action_id for a in actions], ["install-hooks"])

    def test_skips_hook_install_without_bash(self):
        output = "Missing hook(s): commit-msg — run: bash tools/install-hooks.sh"
        actions = repair.plan_repairs(
            output,
            has_bash=False,
            clean_tree=False,
            python_executable="python3",
        )
        self.assertEqual(actions, [])

    def test_plans_proxy_snapshot_only_when_tree_is_clean(self):
        output = (
            "Proxy K baseline S145 is stale on dirty tree (current S157); "
            "re-save clean snapshot when stable: python3 tools/proxy_k.py --save"
        )
        clean_actions = repair.plan_repairs(
            output,
            has_bash=True,
            clean_tree=True,
            python_executable="/usr/bin/python3",
        )
        dirty_actions = repair.plan_repairs(
            output,
            has_bash=True,
            clean_tree=False,
            python_executable="/usr/bin/python3",
        )
        self.assertIn("proxy-k-save", [a.action_id for a in clean_actions])
        self.assertNotIn("proxy-k-save", [a.action_id for a in dirty_actions])

    def test_plans_identity_renewal_only_when_tree_is_clean(self):
        output = "FAIL IDENTITY: CORE.md changed without renewal"
        clean_actions = repair.plan_repairs(
            output,
            has_bash=True,
            clean_tree=True,
            python_executable="python3",
        )
        dirty_actions = repair.plan_repairs(
            output,
            has_bash=True,
            clean_tree=False,
            python_executable="python3",
        )
        self.assertIn("renew-identity", [a.action_id for a in clean_actions])
        self.assertNotIn("renew-identity", [a.action_id for a in dirty_actions])


if __name__ == "__main__":
    unittest.main()
