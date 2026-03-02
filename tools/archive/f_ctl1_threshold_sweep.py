#!/usr/bin/env python3
"""F-CTL1 threshold sweep for proxy-K alert tuning.

Goal:
- Sweep due/urgent drift thresholds on historical proxy-K traces.
- Minimize missed compaction warnings and alert noise.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Point:
    session: int
    total: int


def _load_points(path: Path, schema_mode: str = "latest") -> list[Point]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("proxy-k log must be a list")

    rows: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        session = int(item.get("session", 0) or 0)
        total = int(item.get("total", 0) or 0)
        if session <= 0 or total <= 0:
            continue
        rows.append(
            {
                "session": session,
                "total": total,
                "tier_schema": item.get("tier_schema", ""),
            }
        )

    if not rows:
        return []

    filtered = rows
    if schema_mode == "latest":
        latest_schema = ""
        for row in reversed(rows):
            if row.get("tier_schema"):
                latest_schema = str(row["tier_schema"])
                break
        if latest_schema:
            schema_rows = [r for r in rows if r.get("tier_schema") == latest_schema]
            if len({r["session"] for r in schema_rows}) >= 8:
                filtered = schema_rows

    # Keep last observation for each session, then sort.
    by_session: dict[int, int] = {}
    for row in filtered:
        by_session[row["session"]] = row["total"]

    points = [Point(session=s, total=t) for s, t in by_session.items()]
    points.sort(key=lambda p: p.session)
    return points


def _drift_series(points: list[Point], drop_threshold: float) -> tuple[list[float], list[int]]:
    """Return (drift values, compaction event sessions)."""
    if not points:
        return [], []

    floor = float(points[0].total)
    prev_total = float(points[0].total)
    drifts: list[float] = []
    compaction_sessions: list[int] = []

    for point in points:
        total = float(point.total)
        # Significant negative jump marks a likely compaction/reset event.
        if prev_total > 0 and total <= prev_total * (1.0 - drop_threshold):
            floor = total
            compaction_sessions.append(point.session)
        elif total < floor:
            floor = total

        drifts.append((total - floor) / floor if floor > 0 else 0.0)
        prev_total = total

    return drifts, compaction_sessions


def _levels(drifts: list[float], due: float, urgent: float) -> list[int]:
    out: list[int] = []
    for drift in drifts:
        if drift >= urgent:
            out.append(2)
        elif drift >= due:
            out.append(1)
        else:
            out.append(0)
    return out


def _episode_starts(levels: list[int]) -> list[int]:
    starts: list[int] = []
    prev = 0
    for i, lv in enumerate(levels):
        if lv > 0 and prev == 0:
            starts.append(i)
        prev = lv
    return starts


def _sweep(points: list[Point], drifts: list[float], compaction_sessions: list[int], window: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    sessions = [p.session for p in points]
    compaction_idx = [sessions.index(s) for s in compaction_sessions if s in sessions]

    for due_i in range(4, 13):  # 0.04..0.12
        due = due_i / 100.0
        for urgent_i in range(due_i + 3, 21):  # due+0.03 .. 0.20
            urgent = urgent_i / 100.0
            levels = _levels(drifts, due, urgent)
            starts = _episode_starts(levels)
            alert_sessions = sum(1 for lv in levels if lv > 0)
            urgent_sessions = sum(1 for lv in levels if lv == 2)

            missed_events = 0
            lead_distances: list[int] = []
            for ci in compaction_idx:
                start = max(0, ci - window)
                alert_positions = [i for i in range(start, ci + 1) if levels[i] > 0]
                if not alert_positions:
                    missed_events += 1
                else:
                    lead_distances.append(ci - alert_positions[0])

            false_alarm_episodes = 0
            for s in starts:
                next_compaction = next((ci for ci in compaction_idx if ci >= s), None)
                if next_compaction is None or (next_compaction - s) > window:
                    false_alarm_episodes += 1

            mean_lead = (sum(lead_distances) / len(lead_distances)) if lead_distances else 0.0
            burden = alert_sessions / len(points) if points else 0.0

            # Lower is better.
            score = (
                missed_events * 100.0
                + false_alarm_episodes * 20.0
                + burden * 10.0
                + max(0.0, 1.0 - mean_lead / max(1, window)) * 5.0
            )

            results.append(
                {
                    "due_threshold": round(due, 3),
                    "urgent_threshold": round(urgent, 3),
                    "score": round(score, 4),
                    "missed_events": missed_events,
                    "false_alarm_episodes": false_alarm_episodes,
                    "alert_sessions": alert_sessions,
                    "urgent_sessions": urgent_sessions,
                    "alert_burden": round(burden, 4),
                    "mean_lead_sessions": round(mean_lead, 4),
                }
            )

    results.sort(
        key=lambda x: (
            x["score"],
            x["missed_events"],
            x["false_alarm_episodes"],
            x["alert_burden"],
            -x["mean_lead_sessions"],
        )
    )
    return results


def _find_candidate(rows: list[dict[str, Any]], due: float, urgent: float) -> dict[str, Any] | None:
    for row in rows:
        if abs(row["due_threshold"] - due) < 1e-9 and abs(row["urgent_threshold"] - urgent) < 1e-9:
            return row
    return None


def run(
    input_path: Path,
    output_path: Path,
    window: int = 5,
    drop_threshold: float = 0.04,
    schema_mode: str = "latest",
) -> dict[str, Any]:
    points = _load_points(input_path, schema_mode=schema_mode)
    if len(points) < 8:
        raise ValueError("insufficient proxy-k sessions for threshold sweep")

    drifts, compaction_sessions = _drift_series(points, drop_threshold=drop_threshold)
    sweep = _sweep(points, drifts, compaction_sessions, window=window)
    best = sweep[0]
    current_policy = _find_candidate(sweep, 0.06, 0.10)

    result = {
        "frontier_id": "F-CTL1",
        "input": str(input_path.as_posix()),
        "session_range": {"start": points[0].session, "end": points[-1].session},
        "n_sessions": len(points),
        "schema_mode": schema_mode,
        "window_sessions": window,
        "drop_threshold": drop_threshold,
        "compaction_event_sessions": compaction_sessions,
        "compaction_event_count": len(compaction_sessions),
        "current_policy_reference": current_policy,
        "best_thresholds": best,
        "top_candidates": sweep[:12],
        "data_confidence": (
            "LOW" if len(compaction_sessions) < 2 else "MEDIUM" if len(compaction_sessions) < 5 else "HIGH"
        ),
        "notes": (
            "Objective weights missed compaction warnings highest, then false alarm episodes, "
            "then alert burden. Mean lead time is rewarded."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="F-CTL1 threshold sweep")
    p.add_argument(
        "--input",
        default="experiments/proxy-k-log.json",
        help="Path to proxy-k-log.json",
    )
    p.add_argument(
        "--output",
        default="experiments/control-theory/f-ctl1-threshold-sweep-s186.json",
        help="Output JSON path",
    )
    p.add_argument("--window", type=int, default=5, help="Compaction follow-up window (sessions)")
    p.add_argument("--drop-threshold", type=float, default=0.04, help="Drop ratio that marks compaction event")
    p.add_argument(
        "--schema-mode",
        choices=("latest", "all"),
        default="latest",
        help="Use latest tier schema only, or all rows",
    )
    return p


def main() -> int:
    args = _parser().parse_args()
    out = run(
        input_path=REPO_ROOT / args.input,
        output_path=REPO_ROOT / args.output,
        window=args.window,
        drop_threshold=args.drop_threshold,
        schema_mode=args.schema_mode,
    )
    best = out["best_thresholds"]
    print(
        "F-CTL1 best:",
        f"due={best['due_threshold']:.3f}",
        f"urgent={best['urgent_threshold']:.3f}",
        f"missed={best['missed_events']}",
        f"false_episodes={best['false_alarm_episodes']}",
        f"burden={best['alert_burden']:.3f}",
    )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
