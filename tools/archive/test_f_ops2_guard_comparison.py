#!/usr/bin/env python3
"""Regression tests for F-OPS2 guarded-vs-unguarded comparator."""

import tempfile
import unittest
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ops2_guard_comparison as mod


class TestFOps2GuardComparison(unittest.TestCase):
    def test_parse_plan_domains_uses_allocations_and_plan(self):
        payload = {
            "recommended_policy": "hybrid",
            "policies": {"hybrid": {"allocations": {"ai": 1, "ops": 0}}},
            "recommended_plan": [{"domain": "statistics"}],
        }
        domains = mod.parse_plan_domains(payload)
        self.assertEqual(domains, {"ai", "statistics"})

    def test_compute_profile_metrics_pickup_and_blocked(self):
        rows = [
            {
                "lane": "L-A",
                "session_num": 186,
                "scope": "domains/ai/tasks/FRONTIER.md",
                "etc": "available=yes; blocked=none",
                "notes": "queued",
                "status": "READY",
            },
            {
                "lane": "L-A",
                "session_num": 186,
                "scope": "domains/ai/tasks/FRONTIER.md",
                "etc": "available=yes; blocked=none",
                "notes": "working",
                "status": "ACTIVE",
            },
            {
                "lane": "L-B",
                "session_num": 186,
                "scope": "domains/ai/tasks/FRONTIER.md",
                "etc": "available=yes; blocked=conflict_with_lane_x",
                "notes": "collision noted",
                "status": "BLOCKED",
            },
            {
                "lane": "L-B",
                "session_num": 186,
                "scope": "domains/ai/tasks/FRONTIER.md",
                "etc": "available=yes; blocked=await_input",
                "notes": "still blocked",
                "status": "BLOCKED",
            },
        ]
        metrics = mod.compute_profile_metrics(
            rows,
            {"ai"},
            frontier_to_domain={},
            session_min=186,
        )
        self.assertEqual(metrics["pickup_candidates"], 1)
        self.assertEqual(metrics["pickup_success"], 1)
        self.assertEqual(metrics["blocked_transitions"], 1)
        self.assertEqual(metrics["blocked_reason_churn"], 1)
        self.assertEqual(metrics["collision_keyword_rows"], 1)

    def test_end_to_end_recommends_guarded_when_not_worse(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            domains = root / "domains" / "ai" / "tasks"
            domains.mkdir(parents=True)
            (domains / "FRONTIER.md").write_text("## Active\n- **F-AI1**: x\n", encoding="utf-8")

            guarded = {
                "session": 186,
                "recommended_policy": "hybrid",
                "policies": {"hybrid": {"allocations": {"ai": 1}}},
                "recommended_plan": [{"domain": "ai"}],
            }
            unguarded = {
                "session": 186,
                "recommended_policy": "value_density",
                "policies": {"value_density": {"allocations": {"ai": 1}}},
                "recommended_plan": [{"domain": "ai"}],
            }
            g_path = root / "guarded.json"
            u_path = root / "unguarded.json"
            g_path.write_text(json.dumps(guarded), encoding="utf-8")
            u_path.write_text(json.dumps(unguarded), encoding="utf-8")

            lanes = root / "lanes.md"
            lanes.write_text(
                "\n".join(
                    [
                        "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| 2026-02-27 | L-A | S186 | codex | b | - | GPT-5 | cli | domains/ai/tasks/FRONTIER.md | available=yes blocked=none | READY | queued |",
                        "| 2026-02-27 | L-A | S186 | codex | b | - | GPT-5 | cli | domains/ai/tasks/FRONTIER.md | available=yes blocked=none | MERGED | done |",
                    ]
                ),
                encoding="utf-8",
            )

            rows = mod._parse_lane_rows(lanes.read_text(encoding="utf-8"))
            frontier_map = mod.load_frontier_domain_map(root / "domains")
            g_metrics = mod.compute_profile_metrics(rows, {"ai"}, frontier_map, 186)
            u_metrics = mod.compute_profile_metrics(rows, {"ai"}, frontier_map, 186)
            cmp = mod.compare_profiles(g_metrics, u_metrics)
            self.assertEqual(cmp["recommendation"], "guarded")


if __name__ == "__main__":
    unittest.main()
