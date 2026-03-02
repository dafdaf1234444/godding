#!/usr/bin/env python3
"""Regression tests for F-STAT1 reporting-quality baseline."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_stat1_reporting_quality as mod


class TestFStat1ReportingQuality(unittest.TestCase):
    def test_latest_active_lanes_uses_latest_row_state(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-1 | S186 | codex | b1 | - | GPT-5 | codex-cli | tools/x.py | setup=a focus=global | ACTIVE | work |",
                "| 2026-02-27 | L-1 | S186 | codex | b1 | - | GPT-5 | codex-cli | tools/x.py | setup=a focus=global | MERGED | done |",
                "| 2026-02-27 | L-2 | S186 | codex | b2 | - | GPT-5 | codex-cli | tools/y.py | setup=a focus=global | READY | queued |",
            ]
        )
        rows = mod.parse_lane_rows(text)
        active = mod.latest_active_lanes(rows)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["lane"], "L-2")

    def test_detect_fields_accepts_explicit_none_for_blocked_and_human(self):
        row = {
            "lane": "L-X",
            "status": "READY",
            "session": "S186",
            "model": "GPT-5",
            "platform": "codex-cli",
            "scope_key": "tasks/SWARM-LANES.md",
            "etc": (
                "setup=codex focus=global intent=baseline available=yes blocked=none "
                "next_step=run human_open_item=none"
            ),
            "notes": "Queued run for reporting quality baseline.",
        }
        fields = mod.detect_reporting_fields(row)
        explicit = mod.detect_explicit_reporting_fields(row)
        self.assertTrue(all(fields.values()), fields)
        self.assertFalse(explicit["progress"])
        self.assertAlmostEqual(mod.reporting_score(fields), 1.0, places=4)
        self.assertAlmostEqual(mod.reporting_score(explicit), 0.85, places=4)

    def test_missing_blocked_and_human_fields_reduce_score(self):
        row = {
            "lane": "L-Y",
            "status": "READY",
            "session": "S186",
            "model": "GPT-5",
            "platform": "codex-cli",
            "scope_key": "domains/statistics/tasks/FRONTIER.md",
            "etc": "setup=codex focus=global frontier=F-STAT1 dispatch=domain-expert",
            "notes": "Domain lane queued: run baseline measurement.",
        }
        fields = mod.detect_reporting_fields(row)
        explicit = mod.detect_explicit_reporting_fields(row)
        self.assertFalse(fields["blocked"])
        self.assertFalse(fields["human_open_item"])
        self.assertFalse(explicit["blocked"])
        self.assertFalse(explicit["human_open_item"])
        self.assertAlmostEqual(mod.reporting_score(fields), 0.8, places=4)
        self.assertAlmostEqual(mod.reporting_score(explicit), 0.4, places=4)

    def test_build_report_computes_key_coverage(self):
        full = {
            "lane": "L-FULL",
            "status": "ACTIVE",
            "session": "S186",
            "model": "GPT-5",
            "platform": "codex-cli",
            "scope_key": "a",
            "etc": "setup=codex focus=global intent=x available=yes blocked=none next_step=run human_open_item=none",
            "notes": "Ready and executing.",
        }
        partial = {
            "lane": "L-PART",
            "status": "READY",
            "session": "S186",
            "model": "GPT-5",
            "platform": "codex-cli",
            "scope_key": "b",
            "etc": "setup=codex focus=global frontier=F-STAT1",
            "notes": "Queued run.",
        }
        report = mod.build_report([full, partial])
        self.assertEqual(report["lane_count"], 2)
        self.assertAlmostEqual(report["key_coverage"]["blocked"], 0.5, places=4)
        self.assertAlmostEqual(report["key_coverage"]["human_open_item"], 0.5, places=4)
        self.assertEqual(report["lowest_coverage_keys"][0], "blocked")
        self.assertAlmostEqual(report["explicit_key_coverage"]["progress"], 0.0, places=4)
        self.assertAlmostEqual(report["explicit_contract_ready_rate"], 0.0, places=4)

    def test_programmatic_swarm_plan_only_dispatches_clear_contract_lanes(self):
        dispatchable = {
            "lane": "L-AUTO",
            "status": "READY",
            "session": "S186",
            "model": "GPT-5",
            "platform": "codex-cli",
            "scope_key": "domains/finance/tasks/FRONTIER.md",
            "etc": (
                "setup=codex focus=global intent=run progress=executing available=yes "
                "blocked=none next_step=rerun human_open_item=none"
            ),
            "notes": "Queued rerun.",
        }
        blocked = {
            "lane": "L-HUMAN",
            "status": "BLOCKED",
            "session": "S186",
            "model": "GPT-5",
            "platform": "codex-cli",
            "scope_key": "domains/ai/tasks/FRONTIER.md",
            "etc": (
                "setup=codex focus=global intent=run progress=waiting available=no "
                "blocked=authority_wait next_step=hold human_open_item=HQ-12"
            ),
            "notes": "Waiting for human decision.",
        }

        report = mod.build_report([dispatchable, blocked])
        plan = report["programmatic_swarm_plan"]
        self.assertEqual(plan["dispatchable_count"], 1)
        self.assertEqual(plan["dispatchable_lanes"][0]["lane"], "L-AUTO")
        self.assertEqual(plan["dispatchable_lanes"][0]["domain"], "finance")
        self.assertEqual(plan["non_dispatchable_count"], 1)
        self.assertEqual(plan["non_dispatchable_lanes"][0]["lane"], "L-HUMAN")
        self.assertIn("blocked_not_clear", plan["non_dispatchable_lanes"][0]["reasons"])
        self.assertIn("human_open_item_requires_action", plan["non_dispatchable_lanes"][0]["reasons"])

    def test_has_schema_contract_requires_full_core_fields(self):
        complete = {
            "lane": "L-C1",
            "status": "READY",
            "session": "S186",
            "model": "GPT-5",
            "platform": "codex-cli",
            "scope_key": "domains/statistics/tasks/FRONTIER.md",
            "etc": "available=yes blocked=none next_step=run human_open_item=none",
            "notes": "queued",
        }
        missing_available = dict(complete)
        missing_available["etc"] = "blocked=none next_step=run human_open_item=none"
        self.assertTrue(mod.has_schema_contract(complete))
        self.assertFalse(mod.has_schema_contract(missing_available))

    def test_pickup_latency_ab_reports_schema_vs_free_form_delta(self):
        rows = [
            {
                "lane": "L-SCHEMA-A",
                "status": "READY",
                "session": "S180",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/statistics/tasks/FRONTIER.md",
                "etc": "available=yes blocked=none next_step=run human_open_item=none",
                "notes": "queued",
            },
            {
                "lane": "L-SCHEMA-A",
                "status": "ACTIVE",
                "session": "S181",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/statistics/tasks/FRONTIER.md",
                "etc": "available=yes blocked=none next_step=run human_open_item=none",
                "notes": "working",
            },
            {
                "lane": "L-SCHEMA-B",
                "status": "READY",
                "session": "S180",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/statistics/tasks/FRONTIER.md",
                "etc": "available=yes blocked=none next_step=run human_open_item=none",
                "notes": "queued",
            },
            {
                "lane": "L-SCHEMA-B",
                "status": "ACTIVE",
                "session": "S180",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/statistics/tasks/FRONTIER.md",
                "etc": "available=yes blocked=none next_step=run human_open_item=none",
                "notes": "picked up same session",
            },
            {
                "lane": "L-FREE-A",
                "status": "READY",
                "session": "S180",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/finance/tasks/FRONTIER.md",
                "etc": "intent=run blocked=none",
                "notes": "queued",
            },
            {
                "lane": "L-FREE-A",
                "status": "ACTIVE",
                "session": "S183",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/finance/tasks/FRONTIER.md",
                "etc": "intent=run blocked=none",
                "notes": "late pickup",
            },
            {
                "lane": "L-FREE-B",
                "status": "READY",
                "session": "S180",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/finance/tasks/FRONTIER.md",
                "etc": "intent=run blocked=none",
                "notes": "queued",
            },
            {
                "lane": "L-FREE-B",
                "status": "ACTIVE",
                "session": "S182",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/finance/tasks/FRONTIER.md",
                "etc": "intent=run blocked=none",
                "notes": "pickup",
            },
        ]

        ab = mod.build_pickup_latency_ab(rows)
        self.assertEqual(ab["schema_contract"]["count"], 2)
        self.assertEqual(ab["free_form"]["count"], 2)
        self.assertAlmostEqual(ab["schema_contract"]["mean_latency_sessions"], 0.5, places=4)
        self.assertAlmostEqual(ab["free_form"]["mean_latency_sessions"], 2.5, places=4)
        self.assertAlmostEqual(ab["schema_contract"]["cross_session_rate"], 0.5, places=4)
        self.assertAlmostEqual(ab["free_form"]["cross_session_rate"], 1.0, places=4)
        self.assertAlmostEqual(ab["comparison"]["mean_delta_sessions_free_minus_schema"], 2.0, places=4)
        self.assertTrue(ab["comparison"]["schema_faster"])
        handoff = ab["handoff_window_ab"]
        self.assertEqual(handoff["schema_contract"]["eligible_count"], 2)
        self.assertEqual(handoff["free_form"]["eligible_count"], 2)
        self.assertAlmostEqual(handoff["schema_contract"]["pickup_rate"], 1.0, places=4)
        self.assertAlmostEqual(handoff["free_form"]["pickup_rate"], 1.0, places=4)
        self.assertAlmostEqual(handoff["comparison"]["mean_delta_sessions_free_minus_schema"], 2.0, places=4)

    def test_programmatic_plan_treats_none_recorded_as_clear_human_state(self):
        row = {
            "lane": "L-CLEAR",
            "status": "READY",
            "session": "S186",
            "model": "GPT-5",
            "platform": "codex-cli",
            "scope_key": "domains/statistics/tasks/FRONTIER.md",
            "etc": (
                "setup=codex intent=run progress=queued available=ready blocked=clear "
                "next_step=execute human_open_item=none_recorded"
            ),
            "notes": "queued",
        }
        report = mod.build_report([row])
        plan = report["programmatic_swarm_plan"]
        self.assertEqual(plan["dispatchable_count"], 1)
        self.assertEqual(plan["non_dispatchable_count"], 0)

    def test_handoff_window_counts_unresolved_ready_rows(self):
        rows = [
            {
                "lane": "L-SCHEMA-STUCK",
                "status": "READY",
                "session": "S180",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/statistics/tasks/FRONTIER.md",
                "etc": "available=yes blocked=none next_step=run human_open_item=none",
                "notes": "queued",
            },
            {
                "lane": "L-FREE-OK",
                "status": "READY",
                "session": "S180",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/finance/tasks/FRONTIER.md",
                "etc": "intent=run blocked=none",
                "notes": "queued",
            },
            {
                "lane": "L-FREE-OK",
                "status": "ACTIVE",
                "session": "S182",
                "model": "GPT-5",
                "platform": "codex-cli",
                "scope_key": "domains/finance/tasks/FRONTIER.md",
                "etc": "intent=run blocked=none",
                "notes": "picked up",
            },
        ]

        handoff = mod.build_pickup_latency_ab(rows)["handoff_window_ab"]
        self.assertEqual(handoff["schema_contract"]["eligible_count"], 1)
        self.assertEqual(handoff["schema_contract"]["resolved_count"], 0)
        self.assertEqual(handoff["schema_contract"]["unresolved_count"], 1)
        self.assertAlmostEqual(handoff["schema_contract"]["pickup_rate"], 0.0, places=4)
        self.assertEqual(handoff["free_form"]["eligible_count"], 1)
        self.assertEqual(handoff["free_form"]["resolved_count"], 1)
        self.assertEqual(handoff["free_form"]["unresolved_count"], 0)
        self.assertAlmostEqual(handoff["free_form"]["pickup_rate"], 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
