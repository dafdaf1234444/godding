#!/usr/bin/env python3
"""Extract flow_in/flow_out tags from tasks/SWARM-LANES.md and emit a summary."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from typing import Dict, List, Tuple


FLOW_PATTERN = re.compile(r"\b(flow_in|flow_out)=([^;|]+)")
SESSION_PATTERN = re.compile(r"^S(\d+)$")
ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize flow_in/flow_out tags in SWARM-LANES.")
    parser.add_argument(
        "--lanes",
        default=os.path.join(os.path.dirname(__file__), "..", "tasks", "SWARM-LANES.md"),
        help="Path to SWARM-LANES.md",
    )
    parser.add_argument(
        "--sessions",
        type=int,
        default=10,
        help="Number of recent sessions to include (<=0 means all sessions).",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(
            os.path.dirname(__file__),
            "..",
            "experiments",
            "self-analysis",
            "info-flow-map-latest.json",
        ),
        help="Path to write JSON output.",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        default="",
        help="Deprecated alias for --out.",
    )
    return parser.parse_args()


def split_values(raw: str) -> List[str]:
    parts = re.split(r"[+,\s]+", raw.strip())
    return [p for p in (p.strip() for p in parts) if p]


def parse_etc(etc: str) -> Tuple[List[str], List[str]]:
    flow_in: List[str] = []
    flow_out: List[str] = []
    for kind, value in FLOW_PATTERN.findall(etc):
        values = split_values(value)
        if kind == "flow_in":
            flow_in.extend(values)
        else:
            flow_out.extend(values)
    return flow_in, flow_out


def _parse_rows(lanes_path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(lanes_path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) != 12:
                continue
            if cells[0] == "Date" or cells[0] == "---":
                continue
            rows.append(
                {
                    "date": cells[0],
                    "lane": cells[1],
                    "session": cells[2],
                    "agent": cells[3],
                    "branch": cells[4],
                    "pr": cells[5],
                    "model": cells[6],
                    "platform": cells[7],
                    "scope_key": cells[8],
                    "etc": cells[9],
                    "status": cells[10].upper(),
                    "notes": cells[11],
                }
            )
    return rows


def _session_number(session_raw: str) -> int | None:
    match = SESSION_PATTERN.match(session_raw.strip())
    if not match:
        return None
    return int(match.group(1))


def summarize(lanes_path: str, sessions: int = 10) -> Dict[str, object]:
    if not os.path.exists(lanes_path):
        raise FileNotFoundError(f"Missing lanes file: {lanes_path}")

    rows = _parse_rows(lanes_path)
    session_numbers = [_session_number(row["session"]) for row in rows]
    known_sessions = [num for num in session_numbers if num is not None]
    max_session = max(known_sessions) if known_sessions else None

    min_session = None
    if max_session is not None and sessions > 0:
        min_session = max_session - sessions + 1

    filtered_rows: List[Dict[str, str]] = []
    for row in rows:
        session_num = _session_number(row["session"])
        if min_session is not None and (session_num is None or session_num < min_session):
            continue
        filtered_rows.append(row)

    flow_in_counts: Counter[str] = Counter()
    flow_out_counts: Counter[str] = Counter()
    transition_counts: Counter[str] = Counter()
    lanes_with_flow_in = 0
    lanes_with_flow_out = 0
    latest_by_lane: Dict[str, Dict[str, str]] = {}

    for row in filtered_rows:
        latest_by_lane[row["lane"]] = row
        flow_in, flow_out = parse_etc(row["etc"])
        if flow_in:
            lanes_with_flow_in += 1
        if flow_out:
            lanes_with_flow_out += 1
        flow_in_counts.update(flow_in)
        flow_out_counts.update(flow_out)
        for in_value in flow_in:
            for out_value in flow_out:
                transition_counts[f"{in_value}->{out_value}"] += 1

    active_missing_flow_tags: List[Dict[str, str]] = []
    for lane, row in latest_by_lane.items():
        if row["status"] not in ACTIVE_STATUSES:
            continue
        flow_in, flow_out = parse_etc(row["etc"])
        if flow_in or flow_out:
            continue
        active_missing_flow_tags.append(
            {
                "lane": lane,
                "session": row["session"],
                "status": row["status"],
                "scope_key": row["scope_key"],
            }
        )
    active_missing_flow_tags.sort(key=lambda item: item["lane"])

    return {
        "lanes_path": os.path.abspath(lanes_path),
        "session_window": {
            "requested": sessions,
            "min_session": min_session,
            "max_session": max_session,
        },
        "lanes_total": len(filtered_rows),
        "lanes_with_flow_in": lanes_with_flow_in,
        "lanes_with_flow_out": lanes_with_flow_out,
        "flow_in_counts": dict(sorted(flow_in_counts.items())),
        "flow_out_counts": dict(sorted(flow_out_counts.items())),
        "transition_counts": dict(sorted(transition_counts.items())),
        "active_missing_flow_tags": active_missing_flow_tags,
    }


def main() -> int:
    args = parse_args()
    json_path = args.json_path or args.out
    try:
        summary = summarize(args.lanes, sessions=args.sessions)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = json.dumps(summary, indent=2, sort_keys=True)
    output_dir = os.path.dirname(json_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as handle:
        handle.write(output + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
