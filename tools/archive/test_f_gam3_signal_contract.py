#!/usr/bin/env python3
"""Tests for F-GAM3 signaling-contract analyzer."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_gam3_signal_contract as mod


class TestFGam3SignalContract(unittest.TestCase):
    def test_has_contract_detects_required_keys(self):
        row = {"etc": "setup=x focus=global available=yes blocked=none next_step=execute human_open_item=none"}
        self.assertTrue(mod.has_contract(row))
        self.assertFalse(mod.has_contract({"etc": "setup=x focus=global available=yes blocked=none human_open_item=none"}))

    def test_parse_rows_and_analyze_groups(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S180 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                "| 2026-02-27 | L-A | S181 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | MERGED | done |",
                "| 2026-02-27 | L-B | S180 | codex | b | - | GPT-5 | codex-cli | b | setup=x focus=global | READY | queued |",
                "| 2026-02-27 | L-B | S183 | codex | b | - | GPT-5 | codex-cli | b | setup=x focus=global | MERGED | done |",
            ]
        )
        rows = mod.parse_rows(text)
        result = mod.analyze(rows, min_maturity_sessions=1)
        self.assertEqual(result["all_lanes_ab"]["contract_group"]["lane_count"], 1)
        self.assertEqual(result["all_lanes_ab"]["free_form_group"]["lane_count"], 1)
        self.assertEqual(result["contract_adoption"]["legacy_contract_lanes"], 1)
        self.assertEqual(result["contract_adoption"]["f121_contract_lanes"], 0)
        self.assertEqual(result["all_lanes_ab"]["contract_group"]["mean_closure_lag_sessions"], 1.0)
        self.assertEqual(result["all_lanes_ab"]["free_form_group"]["mean_closure_lag_sessions"], 3.0)
        historian = result["all_lanes_ab"]["historian_analysis"]
        self.assertIn("mean_updates_per_lane", historian["unchanged_metrics"])
        self.assertEqual(historian["most_impactful_change"]["metric"], "mean_closure_lag_sessions")
        self.assertEqual(historian["most_impactful_change"]["impact_on_contract_outcome"], "improved")
        self.assertGreater(len(result["adoption_trend_active_rows"]["rows"]), 0)

    def test_f121_contract_metrics_include_capabilities(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-F121 | S185 | codex | b | - | GPT-5 | codex-cli | a | capabilities=python setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                "| 2026-02-27 | L-F121 | S186 | codex | b | - | GPT-5 | codex-cli | a | capabilities=python setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | MERGED | done |",
                "| 2026-02-27 | L-STRICT | S185 | codex | b | - | GPT-5 | codex-cli | b | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                "| 2026-02-27 | L-STRICT | S186 | codex | b | - | GPT-5 | codex-cli | b | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | MERGED | done |",
                "| 2026-02-27 | L-FREE | S185 | codex | b | - | GPT-5 | codex-cli | c | setup=x focus=global | READY | queued |",
                "| 2026-02-27 | L-FREE | S186 | codex | b | - | GPT-5 | codex-cli | c | MERGED | done |",
            ]
        )
        result = mod.analyze(mod.parse_rows(text), min_maturity_sessions=0)
        adoption = result["contract_adoption"]
        self.assertEqual(adoption["strict_contract_lanes"], 2)
        self.assertEqual(adoption["f121_contract_lanes"], 1)
        self.assertEqual(adoption["capabilities_tagged_lanes"], 1)
        self.assertEqual(result["f121_contract_ab"]["all_lanes"]["contract_group"]["lane_count"], 1)
        self.assertEqual(result["f121_contract_ab"]["all_lanes"]["free_form_group"]["lane_count"], 2)
        self.assertIn("matured_cohort_viability", result["f121_contract_ab"])

    def test_matured_cohort_and_density_metrics(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-C | S180 | codex | b | - | GPT-5 | codex-cli | c | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                "| 2026-02-27 | L-C | S182 | codex | b | - | GPT-5 | codex-cli | c | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | MERGED | done |",
                "| 2026-02-27 | L-D | S182 | codex | b | - | GPT-5 | codex-cli | d | setup=x focus=global | READY | queued |",
                "| 2026-02-27 | L-D | S182 | codex | b | - | GPT-5 | codex-cli | d | setup=x focus=global | MERGED | done |",
            ]
        )
        rows = mod.parse_rows(text)
        result = mod.analyze(rows, min_maturity_sessions=1)
        self.assertEqual(result["contract_adoption"]["matured_lanes"], 1)
        self.assertEqual(result["matured_lanes_ab"]["contract_group"]["lane_count"], 1)
        self.assertIn("mean_updates_per_lifecycle_session", result["matured_lanes_ab"]["contract_group"])
        self.assertIn("matured_cohort_viability", result)
        self.assertEqual(result["all_lanes_ab"]["contract_group"]["mean_ready_to_progress_lag_sessions"], 2.0)
        self.assertEqual(result["all_lanes_ab"]["free_form_group"]["mean_ready_to_progress_lag_sessions"], 0.0)

    def test_mature_ready_metrics_exclude_recent_rows(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-MATURE | S184 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                "| 2026-02-27 | L-MATURE | S185 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | ACTIVE | picked up |",
                "| 2026-02-27 | L-RECENT | S186 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
            ]
        )
        rows = mod.parse_rows(text)
        result = mod.analyze(rows)
        contract_group = result["all_lanes_ab"]["contract_group"]
        self.assertEqual(contract_group["mature_ready_window_sessions"], 1)
        self.assertEqual(contract_group["mature_ready_eligible_count"], 1)
        self.assertEqual(contract_group["mature_ready_unresolved_count"], 0)
        self.assertEqual(contract_group["ready_to_progress_count"], 1)
        self.assertEqual(contract_group["mature_ready_unresolved_rate"], 0.0)

    def test_historian_analysis_marks_no_delta_as_unchanged(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-STRICT | S180 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                "| 2026-02-27 | L-STRICT | S181 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | MERGED | done |",
                "| 2026-02-27 | L-FREE | S180 | codex | b | - | GPT-5 | codex-cli | b | setup=x focus=global | READY | queued |",
                "| 2026-02-27 | L-FREE | S181 | codex | b | - | GPT-5 | codex-cli | b | setup=x focus=global | MERGED | done |",
            ]
        )
        result = mod.analyze(mod.parse_rows(text), min_maturity_sessions=1)
        historian = result["all_lanes_ab"]["historian_analysis"]
        self.assertEqual(historian["changed_metric_count"], 0)
        self.assertIsNone(historian["most_impactful_change"])
        self.assertEqual(historian["unchanged_metric_count"], 7)

    def test_suppress_same_session_status_noops_collapses_rows(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-X | S186 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global | ACTIVE | first |",
                "| 2026-02-27 | L-X | S186 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global | ACTIVE | second |",
                "| 2026-02-27 | L-X | S186 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global | ACTIVE | third |",
                "| 2026-02-27 | L-X | S186 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global | MERGED | done |",
            ]
        )
        rows = mod.parse_rows(text)
        collapsed, stats = mod.suppress_same_session_status_noops(rows)
        self.assertEqual(stats["input_row_count"], 4)
        self.assertEqual(stats["output_row_count"], 2)
        self.assertEqual(stats["suppressed_row_count"], 2)
        result = mod.analyze(collapsed, min_maturity_sessions=0)
        self.assertEqual(result["lane_samples"][0]["update_count"], 2)

    def test_apply_latest_session_holdout_filters_latest_rows(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S185 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global | READY | queued |",
                "| 2026-02-27 | L-A | S186 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global | ACTIVE | progress |",
                "| 2026-02-27 | L-A | S186 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global | MERGED | done |",
            ]
        )
        rows = mod.parse_rows(text)
        filtered, stats = mod.apply_latest_session_holdout(rows, holdout_latest_sessions=1)
        self.assertEqual(stats["max_session"], 186)
        self.assertEqual(stats["session_cutoff"], 185)
        self.assertEqual(stats["suppressed_row_count"], 2)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["session"], "S185")

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
                        "| 2026-02-27 | L-A | S186 | codex | b | - | GPT-5 | codex-cli | a | setup=x focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                    ]
                ),
                encoding="utf-8",
            )
            payload = mod.run(lanes, out, suppress_noop_rows=True, holdout_latest_sessions=0)
            self.assertTrue(out.exists())
            self.assertEqual(payload["frontier_id"], "F-GAM3")
            self.assertIn("preprocessing", payload)
            self.assertIn("f121_contract_keys", payload)
            self.assertEqual(payload["preprocessing"]["suppressed_row_count"], 0)


if __name__ == "__main__":
    unittest.main()
