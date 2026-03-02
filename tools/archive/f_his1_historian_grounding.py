#!/usr/bin/env python3
"""F-HIS1: score historian-grounding coverage in active swarm lanes."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any

ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
LANE_KEYS = (
    "date",
    "lane",
    "session",
    "agent",
    "branch",
    "pr",
    "model",
    "platform",
    "scope_key",
    "etc",
    "status",
    "notes",
)
TAG_RE = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)")
ARTIFACT_RE = re.compile(r"\b(?:experiments/[^\s|`]+|artifact=[^\s|`]+)", re.IGNORECASE)
SESSION_ANCHOR_RE = re.compile(r"\bS\d+\b")


@dataclass(frozen=True)
class GroundingRow:
    lane: str
    session: str
    status: str
    scope_key: str
    focus: str
    historian_check: bool
    artifact_ref: bool
    session_anchor: bool

    @property
    def score(self) -> float:
        present = int(self.historian_check) + int(self.artifact_ref) + int(self.session_anchor)
        return round(present / 3.0, 4)

    @property
    def missing(self) -> list[str]:
        miss: list[str] = []
        if not self.historian_check:
            miss.append("historian_check")
        if not self.artifact_ref:
            miss.append("artifact_ref")
        if not self.session_anchor:
            miss.append("session_anchor")
        return miss


def _parse_tags(raw: str) -> dict[str, str]:
    return {k.strip().lower(): v.strip() for k, v in TAG_RE.findall(raw or "")}


def parse_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|\s*(Date\s*\||[-: ]+\|)", line, re.IGNORECASE):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < len(LANE_KEYS):
            continue
        row = dict(zip(LANE_KEYS, parts))
        row["status"] = row["status"].upper()
        rows.append(row)
    return rows


def latest_rows_by_lane(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        lane = row.get("lane", "")
        if not lane:
            continue
        latest[lane] = row
    return list(latest.values())


def _to_grounding_row(row: dict[str, str]) -> GroundingRow:
    tags = _parse_tags(row.get("etc", ""))
    notes_and_etc = f"{row.get('etc', '')} {row.get('notes', '')}"
    session_value = row.get("session", "")
    return GroundingRow(
        lane=row.get("lane", ""),
        session=session_value,
        status=row.get("status", ""),
        scope_key=row.get("scope_key", ""),
        focus=tags.get("focus", "unspecified"),
        historian_check=("historian_check" in tags),
        artifact_ref=bool(ARTIFACT_RE.search(notes_and_etc)),
        session_anchor=bool(
            SESSION_ANCHOR_RE.search(notes_and_etc)
            and not (session_value and notes_and_etc.strip() == session_value.strip())
        ),
    )


def analyze(
    rows: list[dict[str, str]],
    *,
    low_score_threshold: float = 0.67,
    latest_only: bool = True,
) -> dict[str, Any]:
    source_rows = latest_rows_by_lane(rows) if latest_only else rows
    row_mode = "latest_per_lane" if latest_only else "all_rows"
    active = [row for row in source_rows if row.get("status", "") in ACTIVE_STATUSES]
    grounded = [_to_grounding_row(row) for row in active]

    if not grounded:
        return {
            "row_mode": row_mode,
            "rows_considered": len(source_rows),
            "active_row_count": 0,
            "active_lane_count": 0,
            "historian_check_coverage": 0.0,
            "artifact_ref_coverage": 0.0,
            "session_anchor_coverage": 0.0,
            "mean_grounding_score": 0.0,
            "high_grounding_rate": 0.0,
            "low_grounding_threshold": low_score_threshold,
            "low_grounding_rows": [],
            "focus_breakdown": {},
            "scope_hotspots": [],
        }

    total = len(grounded)
    lanes = {item.lane for item in grounded}
    h_cov = sum(1 for item in grounded if item.historian_check) / total
    a_cov = sum(1 for item in grounded if item.artifact_ref) / total
    s_cov = sum(1 for item in grounded if item.session_anchor) / total
    mean_score = fmean(item.score for item in grounded)
    high_rate = sum(1 for item in grounded if item.score >= 0.99) / total

    low_rows = [item for item in grounded if item.score < low_score_threshold]
    low_rows.sort(key=lambda item: (item.score, item.session, item.lane))

    focus_groups: dict[str, list[float]] = defaultdict(list)
    for item in grounded:
        focus_groups[item.focus].append(item.score)

    scope_missing: dict[str, int] = defaultdict(int)
    for item in low_rows:
        scope_missing[item.scope_key] += 1

    return {
        "row_mode": row_mode,
        "rows_considered": len(source_rows),
        "active_row_count": total,
        "active_lane_count": len(lanes),
        "historian_check_coverage": round(h_cov, 4),
        "artifact_ref_coverage": round(a_cov, 4),
        "session_anchor_coverage": round(s_cov, 4),
        "mean_grounding_score": round(mean_score, 4),
        "high_grounding_rate": round(high_rate, 4),
        "low_grounding_threshold": low_score_threshold,
        "low_grounding_rows": [
            {
                "lane": item.lane,
                "session": item.session,
                "status": item.status,
                "focus": item.focus,
                "scope_key": item.scope_key,
                "score": item.score,
                "missing": item.missing,
            }
            for item in low_rows[:40]
        ],
        "focus_breakdown": {
            focus: {
                "row_count": len(scores),
                "mean_score": round(fmean(scores), 4),
            }
            for focus, scores in sorted(focus_groups.items(), key=lambda x: x[0])
        },
        "scope_hotspots": [
            {"scope_key": scope, "low_grounding_rows": count}
            for scope, count in sorted(scope_missing.items(), key=lambda x: (-x[1], x[0]))[:20]
        ],
    }


def run(
    lanes_path: Path,
    out_path: Path,
    *,
    low_score_threshold: float = 0.67,
    latest_only: bool = True,
) -> dict[str, Any]:
    rows = parse_rows(lanes_path.read_text(encoding="utf-8", errors="replace"))
    analysis = analyze(rows, low_score_threshold=low_score_threshold, latest_only=latest_only)
    payload = {
        "frontier_id": "F-HIS1",
        "title": "Historian-grounding coverage in active lane rows",
        "input": str(lanes_path).replace("\\", "/"),
        "analysis": analysis,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _current_session() -> int:
    """Detect current session number from SESSION-LOG.md or git log."""
    import subprocess
    numbers = []
    try:
        log_text = Path("memory/SESSION-LOG.md").read_text(encoding="utf-8", errors="replace")
        numbers = [int(m) for m in re.findall(r"^S(\d+)", log_text, re.MULTILINE)]
    except Exception:
        pass
    try:
        git_out = subprocess.run(
            ["git", "log", "--oneline", "-50"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        numbers.extend(int(m) for m in re.findall(r"\[S(\d+)\]", git_out))
    except Exception:
        pass
    return max(numbers) if numbers else 0


def parse_args() -> argparse.Namespace:
    session = _current_session()
    session_tag = f"s{session}" if session else "latest"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanes", type=Path, default=Path("tasks/SWARM-LANES.md"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(f"experiments/history/f-his1-historian-grounding-{session_tag}.json"),
    )
    parser.add_argument("--low-score-threshold", type=float, default=0.67)
    parser.add_argument(
        "--all-rows",
        action="store_true",
        help="Score all historical rows instead of latest row per lane.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(
        args.lanes,
        args.out,
        low_score_threshold=args.low_score_threshold,
        latest_only=not args.all_rows,
    )
    analysis = result["analysis"]
    print(f"Wrote {args.out}")
    print(
        "row_mode=",
        analysis["row_mode"],
        "rows_considered=",
        analysis["rows_considered"],
        "active_rows=",
        analysis["active_row_count"],
        "hist_cov=",
        analysis["historian_check_coverage"],
        "artifact_cov=",
        analysis["artifact_ref_coverage"],
        "session_cov=",
        analysis["session_anchor_coverage"],
        "mean_score=",
        analysis["mean_grounding_score"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
