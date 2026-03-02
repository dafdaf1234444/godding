#!/usr/bin/env python3
"""Regression tests for F-HIS1 historian-grounding analyzer."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_his1_historian_grounding as mod


class TestFHis1HistorianGrounding(unittest.TestCase):
    def test_parse_rows(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex-cli | tools/x.py | setup=x focus=global | READY | notes |",
            ]
        )
        rows = mod.parse_rows(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["lane"], "L-A")
        self.assertEqual(rows[0]["status"], "READY")

    def test_analyze_scores_grounding_components(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                (
                    "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex-cli | "
                    "tools/a.py | setup=x focus=global historian_check=NEXT+LANES artifact=experiments/x.json | READY | S185 baseline |"
                ),
                (
                    "| 2026-02-27 | L-B | S186 | codex | local | - | GPT-5 | codex-cli | "
                    "tools/b.py | setup=x focus=domains/game-theory available=yes blocked=none | READY | queued |"
                ),
            ]
        )
        rows = mod.parse_rows(text)
        analysis = mod.analyze(rows, low_score_threshold=0.67)
        self.assertEqual(analysis["active_row_count"], 2)
        self.assertEqual(analysis["active_lane_count"], 2)
        self.assertAlmostEqual(analysis["historian_check_coverage"], 0.5, places=4)
        self.assertAlmostEqual(analysis["artifact_ref_coverage"], 0.5, places=4)
        self.assertAlmostEqual(analysis["session_anchor_coverage"], 0.5, places=4)
        self.assertEqual(len(analysis["low_grounding_rows"]), 1)
        self.assertEqual(analysis["low_grounding_rows"][0]["lane"], "L-B")
        self.assertIn("historian_check", analysis["low_grounding_rows"][0]["missing"])

    def test_analyze_defaults_to_latest_row_per_lane(self):
        text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                (
                    "| 2026-02-27 | L-A | S185 | codex | local | - | GPT-5 | codex-cli | "
                    "tools/a.py | setup=x focus=global available=yes blocked=none | READY | queued |"
                ),
                (
                    "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex-cli | "
                    "tools/a.py | setup=x focus=global historian_check=NEXT+LANES artifact=experiments/a.json | READY | S186 linked |"
                ),
            ]
        )
        rows = mod.parse_rows(text)
        analysis = mod.analyze(rows)
        self.assertEqual(analysis["row_mode"], "latest_per_lane")
        self.assertEqual(analysis["rows_considered"], 1)
        self.assertEqual(analysis["active_row_count"], 1)
        self.assertAlmostEqual(analysis["historian_check_coverage"], 1.0, places=4)

        all_rows = mod.analyze(rows, latest_only=False)
        self.assertEqual(all_rows["row_mode"], "all_rows")
        self.assertEqual(all_rows["rows_considered"], 2)
        self.assertEqual(all_rows["active_row_count"], 2)
        self.assertAlmostEqual(all_rows["historian_check_coverage"], 0.5, places=4)

    def test_run_writes_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lanes = root / "lanes.md"
            out = root / "out.json"
            lanes.write_text(
                "\n".join(
                    [
                        "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        (
                            "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex-cli | "
                            "tools/a.py | setup=x focus=global historian_check=ref artifact=experiments/x.json | READY | S185 linked |"
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            payload = mod.run(lanes, out)
            self.assertTrue(out.exists())
            self.assertEqual(payload["frontier_id"], "F-HIS1")
            self.assertEqual(payload["analysis"]["active_row_count"], 1)
            self.assertEqual(payload["analysis"]["row_mode"], "latest_per_lane")


if __name__ == "__main__":
    unittest.main()
