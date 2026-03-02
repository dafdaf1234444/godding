#!/usr/bin/env python3
"""Regression tests for F-GAM2 reputation/integrity analyzer."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_gam2_reputation_integrity as mod


class TestFGam2ReputationIntegrity(unittest.TestCase):
    def test_has_reputation_signal_requires_keys(self):
        row = {
            "etc": (
                "setup=x focus=global reliability=high evidence_quality=strong "
                "available=yes blocked=none next_step=run human_open_item=none"
            )
        }
        self.assertTrue(mod.has_reputation_signal(row))
        self.assertFalse(mod.has_reputation_signal({"etc": "setup=x reliability=high"}))

    def test_parse_rows_and_analyze_groups(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S180 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global reliability=high evidence_quality=strong available=yes blocked=none next_step=run human_open_item=none | CLAIMED | queued |",
                "| 2026-02-27 | L-A | S181 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global reliability=high evidence_quality=strong available=yes blocked=none next_step=run human_open_item=none | ACTIVE | working |",
                "| 2026-02-27 | L-A | S182 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global reliability=high evidence_quality=strong available=yes blocked=none next_step=close human_open_item=none | MERGED | done |",
                "| 2026-02-27 | L-B | S180 | codex | b | - | GPT-5 | codex-cli | b | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | CLAIMED | queued |",
                "| 2026-02-27 | L-B | S182 | codex | b | - | GPT-5 | codex-cli | b | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | ACTIVE | working |",
                "| 2026-02-27 | L-B | S183 | codex | b | - | GPT-5 | codex-cli | b | setup=x focus=global available=yes blocked=none next_step=close human_open_item=none | MERGED | done |",
            ]
        )
        rows = mod.parse_rows(text)
        result = mod.analyze(rows)
        self.assertEqual(result["reputation_group"]["lane_count"], 1)
        self.assertEqual(result["untagged_group"]["lane_count"], 1)
        self.assertEqual(result["reputation_group"]["mean_handoff_lag_sessions"], 1.0)
        self.assertEqual(result["untagged_group"]["mean_handoff_lag_sessions"], 2.0)
        self.assertEqual(result["integrity_summary"]["lane_count_total"], 2)
        self.assertIn("ab_assignment_plan", result)

    def test_ab_assignment_plan_recommends_tagged_and_holdout_lanes(self):
        lane_rows = [
            {
                "lane": "L-TAGGED",
                "reputation_signal": True,
                "contract_explicit": True,
                "human_open_item_active": False,
                "conflict_events": 0,
                "latest_status": "ACTIVE",
                "latest_session": 186,
            },
            {
                "lane": "L-U1",
                "reputation_signal": False,
                "contract_explicit": True,
                "human_open_item_active": False,
                "conflict_events": 2,
                "latest_status": "BLOCKED",
                "latest_session": 185,
            },
            {
                "lane": "L-U2",
                "reputation_signal": False,
                "contract_explicit": True,
                "human_open_item_active": False,
                "conflict_events": 0,
                "latest_status": "READY",
                "latest_session": 186,
            },
            {
                "lane": "L-U3",
                "reputation_signal": False,
                "contract_explicit": True,
                "human_open_item_active": False,
                "conflict_events": 1,
                "latest_status": "ACTIVE",
                "latest_session": 184,
            },
        ]
        plan = mod.build_ab_assignment_plan(lane_rows, max_session=186, min_per_cohort=3)
        self.assertTrue(plan["feasible_for_ab"])
        self.assertEqual(plan["target_per_cohort"], 2)
        self.assertEqual(plan["additional_tagged_needed"], 1)
        self.assertEqual(len(plan["recommended_tagged_lanes"]), 1)
        self.assertEqual(plan["recommended_tagged_lanes"][0]["lane"], "L-U1")
        self.assertGreaterEqual(len(plan["holdout_untagged_lanes"]), 1)

    def test_challenge_questions_include_low_coverage_prompt(self):
        questions = mod.build_challenge_questions(
            integrity_summary={
                "reputation_signal_rate_active": 0.0,
                "contract_rate_active": 0.5,
                "stale_active_rate": 0.3,
                "blocked_active_rate": 0.25,
                "integrity_score": 0.5,
            },
            reputation_group={"lane_count": 1, "mean_handoff_lag_sessions": 2.0, "conflict_lane_rate": 0.5},
            untagged_group={"lane_count": 5, "mean_handoff_lag_sessions": 1.0, "conflict_lane_rate": 0.2},
        )
        blob = " ".join(q["question"] for q in questions)
        self.assertIn("reliability", blob)
        self.assertGreaterEqual(len(questions), 5)

    def test_run_writes_output(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            lanes = base / "lanes.md"
            out = base / "out.json"
            lanes.write_text(
                "\n".join(
                    [
                        "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| 2026-02-27 | L-A | S186 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global reliability=high evidence_quality=strong available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                    ]
                ),
                encoding="utf-8",
            )
            payload = mod.run(lanes, out)
            self.assertTrue(out.exists())
            self.assertEqual(payload["frontier_id"], "F-GAM2")
            self.assertIn("swarm_to_swarm_challenge_questions", payload)


if __name__ == "__main__":
    unittest.main()
