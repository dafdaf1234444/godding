#!/usr/bin/env python3
"""Regression tests for swarm lane and PR queue invariants."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LANES_PATH = REPO_ROOT / "tasks" / "SWARM-LANES.md"
QUEUE_PATH = REPO_ROOT / "tasks" / "PR-QUEUE.json"

REQUIRED_LANE_COLUMNS = [
    "Date",
    "Lane",
    "Session",
    "Agent",
    "Branch",
    "PR",
    "Model",
    "Platform",
    "Scope-Key",
    "Etc",
    "Status",
    "Notes",
]

ALLOWED_STATUSES = {
    "CLAIMED",
    "ACTIVE",
    "BLOCKED",
    "READY",
    "MERGED",
    "ABANDONED",
}
ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
PLACEHOLDER_VALUES = {"", "-", "n/a", "na", "none", "pending", "tbd", "unknown"}


def _parse_markdown_table(text: str) -> tuple[list[str], list[list[str]]]:
    lines = [line.rstrip() for line in (text or "").splitlines()]
    table_lines = [line for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 2:
        return [], []

    header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[list[str]] = []
    for raw in table_lines[2:]:
        cells = [cell.strip() for cell in raw.strip("|").split("|")]
        if len(cells) != len(header):
            continue
        rows.append(cells)
    return header, rows


class TestSwarmLanes(unittest.TestCase):
    def test_swarm_lanes_has_required_table_columns(self):
        text = LANES_PATH.read_text(encoding="utf-8")
        header, _ = _parse_markdown_table(text)
        self.assertTrue(header, "No markdown table found in SWARM-LANES.md")
        for column in REQUIRED_LANE_COLUMNS:
            self.assertIn(column, header, f"Missing required lane column: {column}")

    def test_swarm_lane_status_values_are_known(self):
        text = LANES_PATH.read_text(encoding="utf-8")
        header, rows = _parse_markdown_table(text)
        self.assertIn("Status", header, "Status column missing in SWARM-LANES.md")
        status_idx = header.index("Status")
        for row in rows:
            status = row[status_idx].strip()
            if not status:
                continue
            self.assertIn(status, ALLOWED_STATUSES, f"Unknown lane status: {status}")

    def test_active_lanes_include_required_coordination_tags(self):
        text = LANES_PATH.read_text(encoding="utf-8")
        header, rows = _parse_markdown_table(text)
        self.assertIn("Status", header, "Status column missing in SWARM-LANES.md")
        self.assertIn("Lane", header, "Lane column missing in SWARM-LANES.md")
        self.assertIn("Etc", header, "Etc column missing in SWARM-LANES.md")
        status_idx = header.index("Status")
        lane_idx = header.index("Lane")
        etc_idx = header.index("Etc")
        tag_re = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)")

        latest_by_lane: dict[str, list[str]] = {}
        for row in rows:
            lane = row[lane_idx].strip()
            if lane:
                latest_by_lane[lane] = row

        missing: list[str] = []
        for row in latest_by_lane.values():
            status = row[status_idx].strip().upper()
            if status not in ACTIVE_STATUSES:
                continue

            tags = {k.lower(): v.strip().lower() for k, v in tag_re.findall(row[etc_idx])}
            missing_keys = [
                key for key in ("setup", "focus")
                if tags.get(key, "") in PLACEHOLDER_VALUES
            ]
            missing_keys.extend(
                key for key in ("available", "blocked", "next_step", "human_open_item")
                if key not in tags
            )
            if missing_keys:
                lane = row[lane_idx].strip() or "<unknown>"
                missing.append(f"{lane}({','.join(missing_keys)})")

        self.assertFalse(
            missing,
            f"Active lanes missing required coordination tags in Etc: {', '.join(missing)}",
        )

    def test_pr_queue_schema_and_identity_invariants(self):
        data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(data.get("schema"), "swarm-pr-queue-v1")
        items = data.get("items")
        self.assertIsInstance(items, list)

        seen_ids: set[str] = set()
        open_fingerprints: set[str] = set()
        for item in items:
            self.assertIsInstance(item, dict, "Queue items must be objects")
            item_id = str(item.get("id", ""))
            self.assertRegex(item_id, r"^PRQ-\d{3}$")
            self.assertNotIn(item_id, seen_ids, f"Duplicate queue ID: {item_id}")
            seen_ids.add(item_id)

            status = str(item.get("status", ""))
            if status == "open":
                fp = str(item.get("fingerprint", ""))
                self.assertRegex(fp, r"^[0-9a-f]{16}$", f"Invalid open fingerprint: {fp}")
                self.assertNotIn(fp, open_fingerprints, f"Duplicate open fingerprint: {fp}")
                open_fingerprints.add(fp)


if __name__ == "__main__":
    unittest.main()
