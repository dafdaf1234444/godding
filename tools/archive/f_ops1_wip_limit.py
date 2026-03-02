#!/usr/bin/env python3
"""F-OPS1: replay lane history under WIP caps and recommend an active-lane limit.

This tool turns the F-OPS1 prompt into an executable replay:
- builds lane lifecycle jobs from `tasks/SWARM-LANES.md`
- simulates fixed-cap execution over the same historical horizon
- compares caps on:
  - `knowledge_yield` (merged lanes completed in-window)
  - `conflict_rate` (contention + spillover + coordination pressure + blocked/collision signal)
  - `overhead_ratio` (extra concurrent lane-ticks beyond single-lane baseline)

The scoring model is intentionally heuristic and should be treated as a decision
aid, not causal proof.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean


REPO_ROOT = Path(__file__).resolve().parent.parent
ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
CLOSED_STATUSES = {"MERGED", "ABANDONED"}
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


@dataclass(frozen=True)
class LaneRow:
    tick: int
    lane: str
    status: str
    session: str
    etc: str
    notes: str


@dataclass(frozen=True)
class LaneJob:
    lane: str
    start_tick: int
    duration_ticks: int
    merged: bool
    blocked_events: int
    collision_events: int
    source_rows: int

    @property
    def end_tick(self) -> int:
        return self.start_tick + self.duration_ticks - 1


try:
    from swarm_io import read_text as _read
    _has_swarm_io = True
except ImportError:
    try:
        from tools.swarm_io import read_text as _read
        _has_swarm_io = True
    except ImportError:
        _has_swarm_io = False

if not _has_swarm_io:
    def _read(path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _last_session(text: str) -> int:
    sessions = [int(x) for x in re.findall(r"\bS(\d+)\b", text or "")]
    return max(sessions) if sessions else 0


def _updated_session_from_state_header(text: str) -> int:
    m = re.search(r"^Updated:\s*[0-9]{4}-[0-9]{2}-[0-9]{2}\s+S(\d+)\b", text or "", re.MULTILINE)
    return int(m.group(1)) if m else 0


def _risk_counts(status: str, etc: str, notes: str) -> tuple[int, int]:
    low = f"{etc} {notes}".lower()
    blocked = 0
    collision = 0
    if status == "BLOCKED" or "blocker" in low or re.search(r"\bblocked\b", low):
        blocked += 1
    if any(term in low for term in ("collision", "conflict", "contention")):
        collision += 1
    return blocked, collision


def parse_lane_rows(text: str) -> list[LaneRow]:
    rows: list[LaneRow] = []
    tick = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|") or re.match(r"^\|\s*(Date\s*\||[-: ]+\|)", line, re.IGNORECASE):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < len(LANE_KEYS):
            continue
        row = dict(zip(LANE_KEYS, parts))
        status = row["status"].upper()
        rows.append(
            LaneRow(
                tick=tick,
                lane=row["lane"],
                status=status,
                session=row["session"],
                etc=row["etc"],
                notes=row["notes"],
            )
        )
        tick += 1
    return rows


def build_lane_jobs(rows: list[LaneRow]) -> list[LaneJob]:
    by_lane: dict[str, list[LaneRow]] = {}
    for row in rows:
        by_lane.setdefault(row.lane, []).append(row)

    jobs: list[LaneJob] = []
    for lane, lane_rows in by_lane.items():
        start_tick: int | None = None
        close_tick: int | None = None
        close_status: str | None = None
        blocked_events = 0
        collision_events = 0

        for row in lane_rows:
            blocked_inc, collision_inc = _risk_counts(row.status, row.etc, row.notes)
            blocked_events += blocked_inc
            collision_events += collision_inc

            if start_tick is None and row.status in ACTIVE_STATUSES:
                start_tick = row.tick
            if close_tick is None and row.status in CLOSED_STATUSES:
                close_tick = row.tick
                close_status = row.status

        if start_tick is None:
            # Lane sometimes only has a terminal row (for example MERGED snapshot).
            start_tick = close_tick if close_tick is not None else lane_rows[0].tick
        if close_tick is None:
            close_tick = lane_rows[-1].tick
            close_status = lane_rows[-1].status

        jobs.append(
            LaneJob(
                lane=lane,
                start_tick=start_tick,
                duration_ticks=max(1, close_tick - start_tick + 1),
                merged=(close_status == "MERGED"),
                blocked_events=blocked_events,
                collision_events=collision_events,
                source_rows=len(lane_rows),
            )
        )

    return sorted(jobs, key=lambda item: (item.start_tick, item.lane))


def observed_profile(jobs: list[LaneJob]) -> dict[str, float]:
    if not jobs:
        return {
            "job_count": 0,
            "horizon_start": 0,
            "horizon_end": 0,
            "horizon_ticks": 0,
            "observed_peak_wip": 0,
            "observed_mean_wip": 0.0,
        }

    horizon_start = min(job.start_tick for job in jobs)
    horizon_end = max(job.end_tick for job in jobs)
    running_levels: list[int] = []
    for tick in range(horizon_start, horizon_end + 1):
        running_levels.append(sum(1 for job in jobs if job.start_tick <= tick <= job.end_tick))

    return {
        "job_count": len(jobs),
        "horizon_start": horizon_start,
        "horizon_end": horizon_end,
        "horizon_ticks": horizon_end - horizon_start + 1,
        "observed_peak_wip": max(running_levels) if running_levels else 0,
        "observed_mean_wip": round(fmean(running_levels), 4) if running_levels else 0.0,
    }


def simulate_cap(
    jobs: list[LaneJob],
    *,
    cap: int,
    horizon_start: int,
    horizon_end: int,
    observed_peak_wip: int,
    conflict_weight: float,
    overhead_weight: float,
) -> dict:
    if cap <= 0:
        raise ValueError("cap must be >= 1")

    queue: list[dict] = []
    running: list[dict] = []
    completed: list[LaneJob] = []
    running_levels: list[int] = []
    start_count = 0
    contention_ticks = 0
    run_lane_ticks = 0
    queue_lane_ticks = 0
    extra_concurrency_ticks = 0

    cursor = 0
    total_jobs = len(jobs)
    horizon_ticks = max(1, horizon_end - horizon_start + 1)

    for tick in range(horizon_start, horizon_end + 1):
        while cursor < total_jobs and jobs[cursor].start_tick == tick:
            queue.append({"job": jobs[cursor], "remaining": jobs[cursor].duration_ticks})
            cursor += 1

        while len(running) < cap and queue:
            running.append(queue.pop(0))
            start_count += 1

        if queue and len(running) >= cap:
            contention_ticks += 1

        running_levels.append(len(running))
        run_lane_ticks += len(running)
        queue_lane_ticks += len(queue)
        extra_concurrency_ticks += max(0, len(running) - 1)

        done: list[dict] = []
        for slot in running:
            slot["remaining"] -= 1
            if slot["remaining"] <= 0:
                done.append(slot)
        if done:
            completed.extend(slot["job"] for slot in done)
            running = [slot for slot in running if slot["remaining"] > 0]

    spillover_jobs = (total_jobs - cursor) + len(queue) + len(running)
    merged_completed = sum(1 for job in completed if job.merged)
    blocked_events = sum(job.blocked_events for job in completed)
    collision_events = sum(job.collision_events for job in completed)
    blocked_per_merged = (blocked_events + collision_events) / max(1, merged_completed)

    merged_completion_rate = merged_completed / max(1, total_jobs)
    merged_per_100_ticks = merged_completed * 100.0 / horizon_ticks
    contention_rate = contention_ticks / horizon_ticks
    spillover_rate = spillover_jobs / max(1, total_jobs)
    mean_running_wip = fmean(running_levels) if running_levels else 0.0
    denom = max(1.0, float(observed_peak_wip - 1))
    coordination_pressure = max(0.0, (mean_running_wip - 1.0) / denom)
    coordination_pressure = min(1.0, coordination_pressure)

    # Conflict proxy combines:
    # - queue contention pressure
    # - unresolved spillover by horizon end
    # - coordination pressure from high concurrent active lanes
    # - explicit blocked/collision events from lane notes/status
    conflict_rate = (
        0.35 * contention_rate
        + 0.25 * spillover_rate
        + 0.20 * coordination_pressure
        + 0.20 * min(1.0, blocked_per_merged)
    )

    # Overhead ratio is extra concurrent lane-ticks above a single-lane baseline.
    overhead_ratio = extra_concurrency_ticks / horizon_ticks
    net_score = merged_completion_rate - conflict_weight * conflict_rate - overhead_weight * overhead_ratio

    return {
        "cap": cap,
        "knowledge_yield": {
            "merged_completed": merged_completed,
            "merged_completion_rate": round(merged_completion_rate, 4),
            "merged_per_100_ticks": round(merged_per_100_ticks, 4),
        },
        "conflict_rate": round(conflict_rate, 4),
        "overhead_ratio": round(overhead_ratio, 4),
        "net_score": round(net_score, 4),
        "simulation": {
            "horizon_ticks": horizon_ticks,
            "jobs_total": total_jobs,
            "jobs_completed": len(completed),
            "jobs_spillover": spillover_jobs,
            "spillover_rate": round(spillover_rate, 4),
            "contention_ticks": contention_ticks,
            "contention_rate": round(contention_rate, 4),
            "mean_running_wip": round(mean_running_wip, 4),
            "coordination_pressure": round(coordination_pressure, 4),
            "blocked_events_completed": blocked_events,
            "collision_events_completed": collision_events,
            "blocked_per_merged": round(blocked_per_merged, 4),
            "start_count": start_count,
            "run_lane_ticks": run_lane_ticks,
            "queue_lane_ticks": queue_lane_ticks,
            "extra_concurrency_ticks": extra_concurrency_ticks,
        },
    }


def evaluate_caps(
    jobs: list[LaneJob],
    *,
    min_cap: int,
    max_cap: int,
    conflict_weight: float,
    overhead_weight: float,
) -> tuple[dict[str, float], list[dict], dict]:
    profile = observed_profile(jobs)
    if profile["job_count"] == 0:
        return profile, [], {}

    results: list[dict] = []
    for cap in range(min_cap, max_cap + 1):
        result = simulate_cap(
            jobs,
            cap=cap,
            horizon_start=int(profile["horizon_start"]),
            horizon_end=int(profile["horizon_end"]),
            observed_peak_wip=int(profile["observed_peak_wip"]),
            conflict_weight=conflict_weight,
            overhead_weight=overhead_weight,
        )
        results.append(result)

    recommended = min(
        results,
        key=lambda row: (
            -row["net_score"],
            row["conflict_rate"],
            row["overhead_ratio"],
            row["cap"],
        ),
    )
    return profile, results, recommended


def _nested_float(data: dict, *path: str) -> float:
    value = data
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return 0.0
        value = value[key]
    return float(value)


def _result_by_cap(results: list[dict]) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for row in results:
        try:
            out[int(row["cap"])] = row
        except (KeyError, TypeError, ValueError):
            continue
    return out


def build_ab_comparison(results: list[dict], *, cap_a: int, cap_b: int) -> dict:
    by_cap = _result_by_cap(results)
    left = by_cap.get(cap_a)
    right = by_cap.get(cap_b)
    if left is None or right is None:
        return {
            "available": False,
            "cap_a": cap_a,
            "cap_b": cap_b,
            "reason": "requested caps are outside evaluated range",
        }

    a = {
        "cap": cap_a,
        "net_score": _nested_float(left, "net_score"),
        "merged_completion_rate": _nested_float(left, "knowledge_yield", "merged_completion_rate"),
        "conflict_rate": _nested_float(left, "conflict_rate"),
        "overhead_ratio": _nested_float(left, "overhead_ratio"),
        "blocked_per_merged": _nested_float(left, "simulation", "blocked_per_merged"),
        "spillover_rate": _nested_float(left, "simulation", "spillover_rate"),
    }
    b = {
        "cap": cap_b,
        "net_score": _nested_float(right, "net_score"),
        "merged_completion_rate": _nested_float(right, "knowledge_yield", "merged_completion_rate"),
        "conflict_rate": _nested_float(right, "conflict_rate"),
        "overhead_ratio": _nested_float(right, "overhead_ratio"),
        "blocked_per_merged": _nested_float(right, "simulation", "blocked_per_merged"),
        "spillover_rate": _nested_float(right, "simulation", "spillover_rate"),
    }
    delta = {key: round(b[key] - a[key], 4) for key in a.keys() if key != "cap"}

    # Net score is the objective used for recommendation; never hint cap_b when it is worse on that objective.
    if delta["net_score"] < 0.0:
        decision_hint = "prefer_cap_a"
    elif delta["merged_completion_rate"] >= 0.08 and delta["conflict_rate"] <= 0.06 and delta["overhead_ratio"] <= 0.8:
        decision_hint = "prefer_cap_b"
    elif delta["merged_completion_rate"] <= 0.0 and (delta["conflict_rate"] > 0.0 or delta["overhead_ratio"] > 0.0):
        decision_hint = "prefer_cap_a"
    else:
        decision_hint = "inconclusive_needs_live_ab"

    return {
        "available": True,
        "cap_a": a,
        "cap_b": b,
        "delta_b_minus_a": delta,
        "decision_hint": decision_hint,
    }


def recommendation_confidence(results: list[dict], recommended: dict, *, min_cap: int, max_cap: int) -> dict:
    if not results or not recommended:
        return {
            "level": "LOW",
            "reason": "no_results",
            "boundary_recommendation": False,
            "top_score_gap": 0.0,
        }

    ordered = sorted(results, key=lambda row: float(row.get("net_score", 0.0)), reverse=True)
    top = ordered[0]
    second = ordered[1] if len(ordered) > 1 else top
    top_gap = round(float(top.get("net_score", 0.0)) - float(second.get("net_score", 0.0)), 4)
    cap = int(recommended.get("cap", min_cap))
    boundary = cap in {min_cap, max_cap}

    if boundary or top_gap < 0.02:
        level = "LOW"
    elif top_gap < 0.05:
        level = "MEDIUM"
    else:
        level = "HIGH"

    notes: list[str] = []
    if boundary:
        notes.append("recommended cap is at evaluated boundary")
    if top_gap < 0.02:
        notes.append("top score gap is narrow")
    if not notes:
        notes.append("score separation is clear and non-boundary")

    return {
        "level": level,
        "boundary_recommendation": boundary,
        "top_score_gap": top_gap,
        "recommended_cap": cap,
        "runner_up_cap": int(second.get("cap", cap)),
        "notes": notes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanes-path", type=Path, default=Path("tasks/SWARM-LANES.md"))
    parser.add_argument("--next-path", type=Path, default=Path("tasks/NEXT.md"))
    parser.add_argument("--min-cap", type=int, default=1)
    parser.add_argument("--max-cap", type=int, default=5)
    parser.add_argument(
        "--conflict-weight",
        type=float,
        default=0.8,
        help="Weight applied to conflict_rate in net score.",
    )
    parser.add_argument(
        "--overhead-weight",
        type=float,
        default=0.27,
        help="Weight applied to overhead_ratio in net score.",
    )
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument(
        "--ab-cap-a",
        type=int,
        default=3,
        help="First cap for explicit A/B comparison block.",
    )
    parser.add_argument(
        "--ab-cap-b",
        type=int,
        default=5,
        help="Second cap for explicit A/B comparison block.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.min_cap < 1 or args.max_cap < args.min_cap:
        raise SystemExit("invalid cap range")

    lanes_path = args.lanes_path if args.lanes_path.is_absolute() else REPO_ROOT / args.lanes_path
    next_path = args.next_path if args.next_path.is_absolute() else REPO_ROOT / args.next_path
    next_text = _read(next_path)
    session = _updated_session_from_state_header(next_text)
    if session <= 0:
        session = _last_session(next_text)

    rows = parse_lane_rows(_read(lanes_path))
    jobs = build_lane_jobs(rows)
    profile, cap_results, recommended = evaluate_caps(
        jobs,
        min_cap=args.min_cap,
        max_cap=args.max_cap,
        conflict_weight=args.conflict_weight,
        overhead_weight=args.overhead_weight,
    )
    ab = build_ab_comparison(cap_results, cap_a=args.ab_cap_a, cap_b=args.ab_cap_b)
    confidence = recommendation_confidence(
        cap_results,
        recommended,
        min_cap=args.min_cap,
        max_cap=args.max_cap,
    )

    payload = {
        "frontier_id": "F-OPS1",
        "title": "Active-lane WIP cap replay",
        "session": session,
        "inputs": {
            "lanes_path": _display_path(lanes_path),
            "next_path": _display_path(next_path),
            "min_cap": args.min_cap,
            "max_cap": args.max_cap,
            "conflict_weight": args.conflict_weight,
            "overhead_weight": args.overhead_weight,
            "ab_cap_a": args.ab_cap_a,
            "ab_cap_b": args.ab_cap_b,
            "heuristic_note": (
                "Replay score is heuristic for lane-cap decisions. Treat as scheduling aid, not causal estimate."
            ),
        },
        "observed_profile": profile,
        "cap_results": cap_results,
        "recommended": recommended,
        "recommendation_confidence": confidence,
        "ab_comparison": ab,
    }

    out_path = args.json_out
    if out_path is None:
        suffix = f"-s{session}" if session > 0 else ""
        out_path = Path(f"experiments/operations-research/f-ops1-wip-limit{suffix}.json")
    out_abs = out_path if out_path.is_absolute() else REPO_ROOT / out_path
    out_abs.parent.mkdir(parents=True, exist_ok=True)
    out_abs.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {out_abs}")
    if recommended:
        print(
            "recommended_cap=",
            recommended["cap"],
            "net_score=",
            recommended["net_score"],
            "yield_rate=",
            recommended["knowledge_yield"]["merged_completion_rate"],
            "conflict_rate=",
            recommended["conflict_rate"],
            "overhead_ratio=",
            recommended["overhead_ratio"],
        )
        print("confidence=", confidence["level"], "top_score_gap=", confidence["top_score_gap"])
        if ab.get("available"):
            delta = ab["delta_b_minus_a"]
            print(
                "ab_hint=",
                ab["decision_hint"],
                "delta_yield=",
                delta["merged_completion_rate"],
                "delta_conflict=",
                delta["conflict_rate"],
                "delta_overhead=",
                delta["overhead_ratio"],
            )
    else:
        print("No lane jobs parsed from SWARM-LANES.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
