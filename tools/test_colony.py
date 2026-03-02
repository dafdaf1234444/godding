#!/usr/bin/env python3
"""Regression tests for colony experiment discovery and fan-out."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import colony


class TestColony(unittest.TestCase):
    def test_is_colony_config_requires_named_children(self):
        self.assertTrue(colony.is_colony_config({"children": [{"name": "a"}]}))
        self.assertFalse(colony.is_colony_config({"children": []}))
        self.assertFalse(colony.is_colony_config({"children": [{"topic": "x"}]}))
        self.assertFalse(colony.is_colony_config({"generated_at_utc": "2026-02-27T00:00:00Z"}))

    def test_discover_experiments_filters_non_colony_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "valid-a.json").write_text(
                '{"children":[{"name":"valid-a-1"},{"name":"valid-a-2"}]}'
            )
            (root / "valid-b.json").write_text('{"children":[{"name":"valid-b-1"}]}')
            (root / "not-a-colony.json").write_text('{"contexts":{"cooperative":{}}}')
            (root / "broken.json").write_text("{invalid-json")

            with patch.object(colony, "COLONIES_DIR", root):
                valid, skipped = colony.discover_experiments()

        self.assertEqual(valid, ["valid-a", "valid-b"])
        self.assertEqual(set(skipped), {"not-a-colony", "broken"})

    def test_swarm_all_experiments_runs_each_valid_experiment(self):
        with patch.object(
            colony, "discover_experiments", return_value=(["exp-a", "exp-b"], ["ignored"])
        ), patch.object(colony, "swarm_experiment") as swarm_experiment:
            colony.swarm_all_experiments()

        self.assertEqual(
            [call.args[0] for call in swarm_experiment.call_args_list],
            ["exp-a", "exp-b"],
        )

    def test_inventory_constraints_extracts_runtime_gaps(self):
        inventory = {
            "host": {
                "platform": "TestOS",
                "python_executable": "/usr/bin/python3",
                "python_command_hint": "python3",
                "commands": {"python3": True, "bash": False},
            },
            "bridges": [
                {"path": "SWARM.md", "exists": True},
                {"path": "AGENTS.md", "exists": False},
            ],
            "core_state": [
                {"path": "memory/INDEX.md", "exists": True},
                {"path": "tasks/NEXT.md", "exists": False},
            ],
            "capabilities": {
                "evolution": {"present": 4, "total": 5, "files": ["tools/colony.py"]},
                "validation": {"present": 2, "total": 2},
            },
            "inter_swarm_connectivity": {
                "ready": False,
                "missing": ["experiments/inter-swarm/PROTOCOL.md"],
            },
        }

        constraints = colony._inventory_constraints(inventory, "2026-02-27T00:00:00Z")
        self.assertEqual(constraints["source"], "maintenance_inventory")
        self.assertEqual(constraints["platform"], "TestOS")
        self.assertEqual(constraints["python_command_hint"], "python3")
        self.assertEqual(constraints["missing_bridges"], ["AGENTS.md"])
        self.assertEqual(constraints["missing_core_state"], ["tasks/NEXT.md"])
        self.assertEqual(constraints["capabilities"]["evolution"], {"present": 4, "total": 5})
        self.assertEqual(constraints["commands"]["bash"], False)
        self.assertFalse(constraints["inter_swarm_connectivity_ready"])
        self.assertEqual(constraints["inter_swarm_missing"], ["experiments/inter-swarm/PROTOCOL.md"])

    def test_environment_signature_ignores_capture_timestamp(self):
        a = {
            "captured_at_utc": "2026-02-27T01:00:00Z",
            "platform": "X",
            "python_command_hint": "python3",
            "commands": {"python3": True, "bash": False},
            "capabilities": {"evolution": {"present": 4, "total": 5}},
            "missing_bridges": ["AGENTS.md"],
            "missing_core_state": [],
            "inter_swarm_connectivity_ready": True,
            "inter_swarm_missing": [],
        }
        b = dict(a)
        b["captured_at_utc"] = "2026-02-27T02:00:00Z"
        self.assertEqual(colony.environment_signature(a), colony.environment_signature(b))

    def test_capture_environment_constraints_falls_back_on_subprocess_error(self):
        fake_root = Path("/tmp/swarm-missing-root-for-test")
        with patch.object(colony, "REPO_ROOT", fake_root):
            constraints = colony.capture_environment_constraints()
        self.assertEqual(constraints["source"], "fallback")
        self.assertIn("python", constraints["commands"])


if __name__ == "__main__":
    unittest.main()
