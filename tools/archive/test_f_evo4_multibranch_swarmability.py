#!/usr/bin/env python3
"""Regression tests for F-EVO4 multi-branch swarmability analyzer."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_evo4_multibranch_swarmability as mod


class TestFEvo4MultibranchSwarmability(unittest.TestCase):
    def test_parse_rows(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S186 | codex | lane-a | - | GPT-5 | codex-cli | x | setup=s focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
            ]
        )
        rows = mod.parse_rows(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["lane"], "L-A")
        self.assertEqual(rows[0]["session_num"], 186)
        self.assertEqual(rows[0]["status"], "READY")

    def test_analyze_positive_case(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-MULTI | S186 | codex | lane-a | - | GPT-5 | codex-cli | x | setup=s focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                "| 2026-02-27 | L-MULTI | S186 | codex | lane-b | - | GPT-5 | codex-cli | x | setup=s focus=global available=yes blocked=none next_step=run human_open_item=none | MERGED | done |",
                "| 2026-02-27 | L-ONE | S186 | codex | lane-c | - | GPT-5 | codex-cli | y | setup=s focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                "| 2026-02-27 | L-ONE | S186 | codex | lane-c | - | GPT-5 | codex-cli | y | setup=s focus=global available=yes blocked=none next_step=run human_open_item=none | MERGED | done |",
                "| 2026-02-27 | L-TWO | S187 | codex | lane-d | - | GPT-5 | codex-cli | z | setup=s focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                "| 2026-02-27 | L-TWO | S187 | codex | lane-d | - | GPT-5 | codex-cli | z | setup=s focus=global available=yes blocked=none next_step=run human_open_item=none | MERGED | done |",
            ]
        )
        rows = mod.parse_rows(text)
        analysis = mod.analyze(rows)
        self.assertTrue(analysis["overall_multibranch_swarmable"])
        self.assertTrue(analysis["level_verdicts"]["within_agent"]["swarmable"])
        self.assertTrue(analysis["level_verdicts"]["within_swarm"]["swarmable"])
        self.assertTrue(analysis["level_verdicts"]["overall_swarm"]["swarmable"])

    def test_analyze_negative_case(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex-cli | x | setup=s focus=global | READY | queued conflict collision |",
                "| 2026-02-27 | L-B | S186 | codex | local | - | GPT-5 | codex-cli | x | setup=s focus=global | ACTIVE | blocked by contention |",
            ]
        )
        rows = mod.parse_rows(text)
        analysis = mod.analyze(rows)
        self.assertFalse(analysis["overall_multibranch_swarmable"])
        self.assertFalse(analysis["level_verdicts"]["within_swarm"]["swarmable"])

    def test_run_writes_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            lanes = base / "lanes.md"
            out = base / "out.json"
            lanes.write_text(
                "\n".join(
                    [
                        "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| 2026-02-27 | L-A | S186 | codex | lane-a | - | GPT-5 | codex-cli | x | setup=s focus=global available=yes blocked=none next_step=run human_open_item=none | READY | queued |",
                    ]
                ),
                encoding="utf-8",
            )
            payload = mod.run(lanes, out)
            self.assertTrue(out.exists())
            self.assertEqual(payload["frontier_id"], "F-EVO4")


if __name__ == "__main__":
    unittest.main()
