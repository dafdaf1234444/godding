#!/usr/bin/env python3
"""Regression tests for info-flow map extraction."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import info_flow_map


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestInfoFlowMap(unittest.TestCase):
    def test_split_values_supports_plus_comma_and_spaces(self):
        values = info_flow_map.split_values("experiment+maintenance, doc tool-change")
        self.assertEqual(values, ["experiment", "maintenance", "doc", "tool-change"])

    def test_summarize_recent_window_and_active_missing_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            lanes_path = Path(tmp) / "SWARM-LANES.md"
            _write(
                lanes_path,
                "\n".join(
                    [
                        "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| 2026-02-28 | L1 | S200 | codex | lane1 | - | GPT-5 | cli | a | flow_in=experiment; flow_out=frontier-update | ACTIVE | older |",
                        "| 2026-02-28 | L2 | S201 | codex | lane2 | - | GPT-5 | cli | b | setup=codex; available=yes | READY | missing flow tags |",
                        "| 2026-02-28 | L1 | S202 | codex | lane1 | - | GPT-5 | cli | c | flow_in=maintenance; flow_out=doc+tool-change | MERGED | latest |",
                        "| 2026-02-28 | L3 | S190 | codex | lane3 | - | GPT-5 | cli | d | flow_in=old; flow_out=old-out | ACTIVE | out of window |",
                    ]
                ),
            )

            summary = info_flow_map.summarize(str(lanes_path), sessions=2)

            self.assertEqual(summary["lanes_total"], 2)
            self.assertEqual(summary["session_window"]["max_session"], 202)
            self.assertEqual(summary["session_window"]["min_session"], 201)
            self.assertEqual(summary["flow_in_counts"], {"maintenance": 1})
            self.assertEqual(summary["flow_out_counts"], {"doc": 1, "tool-change": 1})
            self.assertEqual(
                summary["transition_counts"],
                {"maintenance->doc": 1, "maintenance->tool-change": 1},
            )
            self.assertEqual(
                summary["active_missing_flow_tags"],
                [
                    {
                        "lane": "L2",
                        "scope_key": "b",
                        "session": "S201",
                        "status": "READY",
                    }
                ],
            )

    def test_summarize_all_sessions_does_not_count_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            lanes_path = Path(tmp) / "SWARM-LANES.md"
            _write(
                lanes_path,
                "\n".join(
                    [
                        "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| 2026-02-28 | L1 | S100 | codex | lane1 | - | GPT-5 | cli | a | flow_in=experiment; flow_out=frontier-update | ACTIVE | n1 |",
                        "| 2026-02-28 | L2 | S101 | codex | lane2 | - | GPT-5 | cli | b | flow_in=maintenance; flow_out=doc | MERGED | n2 |",
                    ]
                ),
            )

            summary = info_flow_map.summarize(str(lanes_path), sessions=0)
            self.assertEqual(summary["lanes_total"], 2)


if __name__ == "__main__":
    unittest.main()
