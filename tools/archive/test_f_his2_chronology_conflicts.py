#!/usr/bin/env python3
"""Regression tests for F-HIS2 chronology-conflict analyzer."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_his2_chronology_conflicts as mod


class TestFHis2ChronologyConflicts(unittest.TestCase):
    def test_parse_next_events_extracts_session_and_refs(self):
        text = "\n".join(
            [
                "# State",
                "## What just happened",
                "S186: ran tool `tools/x.py` and wrote `experiments/x.json`.",
                "S185: no refs here",
                "## For next session",
                "1. next",
            ]
        )
        events = mod.parse_next_events(text)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].session, 186)
        self.assertIn("tools/x.py", events[0].refs)
        self.assertIn("experiments/x.json", events[0].refs)

    def test_analyze_flags_missing_links_and_inversions(self):
        next_text = "\n".join(
            [
                "# State",
                "## What just happened",
                "S186: produced `experiments/a.json` via `tools/a.py`",
                "S186: produced `experiments/missing.json` via `tools/missing.py`",
                "## For next session",
                "1. next",
            ]
        )
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-A | S187 | codex | local | - | GPT-5 | codex-cli | tools/a.py | setup=x artifact=experiments/a.json | MERGED | done |",
            ]
        )
        next_events = mod.parse_next_events(next_text)
        lane_rows = mod.parse_lane_rows(lanes_text)
        analysis = mod.analyze(next_events, lane_rows, repo_root=Path("."))
        self.assertEqual(analysis["next_events_with_refs"], 2)
        self.assertEqual(len(analysis["inversion_events"]), 1)
        self.assertIn(analysis["inversion_events"][0]["ref"], {"experiments/a.json", "tools/a.py"})
        self.assertEqual(len(analysis["missing_link_events"]), 1)
        self.assertIn("experiments/missing.json", analysis["missing_artifacts"])

    def test_run_writes_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            next_path = root / "NEXT.md"
            lanes_path = root / "LANES.md"
            out = root / "out.json"
            next_path.write_text(
                "\n".join(
                    [
                        "# State",
                        "## What just happened",
                        "S186: emitted `experiments/a.json`",
                        "## For next session",
                        "1. next",
                    ]
                ),
                encoding="utf-8",
            )
            lanes_path.write_text(
                "\n".join(
                    [
                        "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| 2026-02-27 | L-A | S186 | codex | local | - | GPT-5 | codex-cli | tools/a.py | setup=x artifact=experiments/a.json | MERGED | done |",
                    ]
                ),
                encoding="utf-8",
            )
            payload = mod.run(next_path, lanes_path, out)
            self.assertTrue(out.exists())
            self.assertEqual(payload["frontier_id"], "F-HIS2")
            self.assertEqual(payload["analysis"]["next_events_total"], 1)


if __name__ == "__main__":
    unittest.main()
