#!/usr/bin/env python3
"""F-EVO2: extract variation-selection-retention signals from swarm artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def parse_session(text: str) -> int | None:
    m = re.search(r"S(\d+)", text or "")
    return int(m.group(1)) if m else None


def base_lane_id(lane: str) -> str:
    lane = (lane or "").strip()
    lane = re.sub(r"^L-S\d+-", "L-", lane)
    lane = re.sub(r"-S\d+$", "", lane)
    return lane


def read_lane_rows(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    table_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| Date | Lane | Session |"):
            table_start = i + 2
            break
    if table_start is None:
        return []

    rows: list[dict[str, str]] = []
    for line in lines[table_start:]:
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 12:
            continue
        rows.append(
            {
                "date": parts[0],
                "lane": parts[1],
                "session": parts[2],
                "agent": parts[3],
                "branch": parts[4],
                "pr": parts[5],
                "model": parts[6],
                "platform": parts[7],
                "scope_key": parts[8],
                "etc": parts[9],
                "status": parts[10],
                "notes": parts[11],
            }
        )
    return rows


def build_report(rows: list[dict[str, str]], min_sessions: int) -> dict:
    status_counts = Counter(r["status"] for r in rows)
    by_base: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_base[base_lane_id(r["lane"])].append(r)

    retained = []
    for base, grp in by_base.items():
        sessions = sorted({parse_session(r["session"]) for r in grp if parse_session(r["session"]) is not None})
        if len(sessions) < min_sessions:
            continue
        retained.append(
            {
                "base_lane": base,
                "events": len(grp),
                "sessions": sessions,
                "status_counts": dict(Counter(r["status"] for r in grp)),
                "dominant_scope": Counter(r["scope_key"] for r in grp).most_common(1)[0][0] if grp else "",
            }
        )
    retained.sort(key=lambda x: (-x["events"], x["base_lane"]))

    scope_counts = Counter(r["scope_key"] for r in rows)
    top_scopes = [{"scope_key": k, "events": v} for k, v in scope_counts.most_common(10)]

    return {
        "experiment": "F-EVO2",
        "title": "Variation-selection-retention extraction from SWARM-LANES",
        "rows_analyzed": len(rows),
        "status_counts": dict(status_counts),
        "retention_threshold_sessions": min_sessions,
        "retained_mutations": retained,
        "top_scopes": top_scopes,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lanes", type=Path, default=Path("tasks/SWARM-LANES.md"))
    p.add_argument("--min-sessions", type=int, default=2)
    p.add_argument("--out", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_lane_rows(args.lanes)
    report = build_report(rows, max(1, args.min_sessions))
    report["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"rows={report['rows_analyzed']} retained={len(report['retained_mutations'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
