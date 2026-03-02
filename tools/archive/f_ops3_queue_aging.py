#!/usr/bin/env python3
"""F-OPS3: replay queue-aging policy against lane-ready backlog dynamics."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any

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
PROGRESS_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "MERGED", "ABANDONED"}
TAG_RE = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)")
SESSION_RE = re.compile(r"\bS(\d+)\b")


@dataclass(frozen=True)
class Job:
    lane: str
    ready_session: int
    observed_progress_session: int | None
    focus: str
    scope_key: str
    ready_order: int


def _parse_session(raw: str) -> int | None:
    m = SESSION_RE.search(raw or "")
    return int(m.group(1)) if m else None


def _parse_tags(raw: str) -> dict[str, str]:
    return {k.strip().lower(): v.strip() for k, v in TAG_RE.findall(raw or "")}


def parse_lane_rows(text: str) -> list[dict[str, str]]:
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


def build_jobs(rows: list[dict[str, str]], *, session_min: int = 0) -> list[Job]:
    by_lane: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_lane.setdefault(row.get("lane", ""), []).append(row)

    jobs: list[Job] = []
    ready_order = 0
    for lane, seq in by_lane.items():
        first_ready = None
        first_progress = None
        focus = "unspecified"
        scope_key = ""
        for row in seq:
            status = row.get("status", "")
            session = _parse_session(row.get("session", ""))
            if session is None:
                continue
            if first_ready is None and status == "READY":
                first_ready = session
                focus = _parse_tags(row.get("etc", "")).get("focus", "unspecified")
                scope_key = row.get("scope_key", "")
            if first_ready is not None and first_progress is None and status in PROGRESS_STATUSES:
                if session >= first_ready:
                    first_progress = session
        if first_ready is None or first_ready < session_min:
            continue
        jobs.append(
            Job(
                lane=lane,
                ready_session=first_ready,
                observed_progress_session=first_progress,
                focus=focus,
                scope_key=scope_key,
                ready_order=ready_order,
            )
        )
        ready_order += 1
    return sorted(jobs, key=lambda job: (job.ready_session, job.ready_order, job.lane))


def observed_capacity(jobs: list[Job], *, start: int, end: int) -> dict[int, int]:
    capacity = {session: 0 for session in range(start, end + 1)}
    for job in jobs:
        if job.observed_progress_session is None:
            continue
        if start <= job.observed_progress_session <= end:
            capacity[job.observed_progress_session] += 1
    return capacity


def _summarize_dispatch(
    jobs: list[Job],
    dispatch: dict[str, int],
    *,
    horizon_end: int,
    stale_threshold: int,
) -> dict[str, Any]:
    lags: list[int] = []
    unresolved_ages: list[int] = []
    shifts: list[int] = []
    global_delays = 0
    global_count = 0
    for job in jobs:
        disp = dispatch.get(job.lane)
        if disp is None:
            unresolved_ages.append(max(0, horizon_end - job.ready_session))
            continue
        lags.append(max(0, disp - job.ready_session))
        if job.observed_progress_session is not None:
            shift = disp - job.observed_progress_session
            shifts.append(shift)
            if job.focus == "global":
                global_count += 1
                if shift > 0:
                    global_delays += 1

    stale_unresolved = [age for age in unresolved_ages if age > stale_threshold]
    positive_shifts = [shift for shift in shifts if shift > 0]
    return {
        "dispatched_count": len(dispatch),
        "dispatched_rate": round(len(dispatch) / max(1, len(jobs)), 4),
        "mean_ready_to_progress_lag": round(fmean(lags), 4) if lags else 0.0,
        "p90_ready_to_progress_lag": round(sorted(lags)[max(0, int(0.9 * (len(lags) - 1)))], 4) if lags else 0.0,
        "unresolved_count": len(unresolved_ages),
        "stale_unresolved_rate": round(len(stale_unresolved) / max(1, len(jobs)), 4),
        "mean_dispatch_shift_vs_observed": round(fmean(shifts), 4) if shifts else 0.0,
        "mean_positive_shift": round(fmean(positive_shifts), 4) if positive_shifts else 0.0,
        "global_delay_rate": round(global_delays / max(1, global_count), 4),
    }


def _policy_pick(
    queue: list[Job],
    *,
    policy: str,
    session: int,
    aging_weight: float,
) -> list[Job]:
    if policy == "recency_bias":
        return sorted(queue, key=lambda job: (-job.ready_session, -job.ready_order, job.lane))
    if policy == "queue_aging":
        return sorted(
            queue,
            key=lambda job: (
                -((session - job.ready_session) * aging_weight),
                job.ready_session,
                job.ready_order,
                job.lane,
            ),
        )
    raise ValueError(f"unknown policy: {policy}")


def simulate_policy(
    jobs: list[Job],
    *,
    capacity_by_session: dict[int, int],
    policy: str,
    stale_threshold: int,
    aging_weight: float,
) -> dict[str, Any]:
    if not jobs:
        return {
            "policy": policy,
            "metrics": _summarize_dispatch([], {}, horizon_end=0, stale_threshold=stale_threshold),
            "score": 0.0,
        }

    start = min(capacity_by_session) if capacity_by_session else min(job.ready_session for job in jobs)
    end = max(capacity_by_session) if capacity_by_session else max(job.ready_session for job in jobs)
    arrivals: dict[int, list[Job]] = {}
    for job in jobs:
        arrivals.setdefault(job.ready_session, []).append(job)

    queue: list[Job] = []
    dispatch: dict[str, int] = {}
    for session in range(start, end + 1):
        queue.extend(arrivals.get(session, []))
        capacity = capacity_by_session.get(session, 0)
        if capacity <= 0 or not queue:
            continue
        ranked = _policy_pick(queue, policy=policy, session=session, aging_weight=aging_weight)
        selected = ranked[:capacity]
        selected_lanes = {job.lane for job in selected}
        queue = [job for job in queue if job.lane not in selected_lanes]
        for job in selected:
            dispatch[job.lane] = session

    metrics = _summarize_dispatch(jobs, dispatch, horizon_end=end, stale_threshold=stale_threshold)
    # Higher score is better.
    score = (
        metrics["dispatched_rate"]
        - 0.20 * metrics["mean_ready_to_progress_lag"]
        - 1.25 * metrics["stale_unresolved_rate"]
        - 0.50 * metrics["global_delay_rate"]
        - 0.15 * metrics["mean_positive_shift"]
    )
    return {"policy": policy, "metrics": metrics, "score": round(score, 4)}


def analyze(
    jobs: list[Job],
    *,
    stale_threshold: int = 2,
    aging_weight: float = 1.0,
) -> dict[str, Any]:
    if not jobs:
        return {"job_count": 0, "ready_session_min": 0, "ready_session_max": 0, "observed": {}, "policies": [], "best_policy": None}

    start = min(job.ready_session for job in jobs)
    end_candidates = [job.observed_progress_session for job in jobs if job.observed_progress_session is not None]
    end = max(end_candidates) if end_candidates else start
    capacities = observed_capacity(jobs, start=start, end=end)

    observed_dispatch = {
        job.lane: job.observed_progress_session
        for job in jobs
        if job.observed_progress_session is not None
    }
    observed_metrics = _summarize_dispatch(jobs, observed_dispatch, horizon_end=end, stale_threshold=stale_threshold)

    policies = [
        simulate_policy(
            jobs,
            capacity_by_session=capacities,
            policy="recency_bias",
            stale_threshold=stale_threshold,
            aging_weight=aging_weight,
        ),
        simulate_policy(
            jobs,
            capacity_by_session=capacities,
            policy="queue_aging",
            stale_threshold=stale_threshold,
            aging_weight=aging_weight,
        ),
    ]
    policies.sort(key=lambda row: (-float(row["score"]), str(row["policy"])))
    best = policies[0] if policies else None
    return {
        "job_count": len(jobs),
        "ready_session_min": start,
        "ready_session_max": max(job.ready_session for job in jobs),
        "horizon_end": end,
        "observed": observed_metrics,
        "policies": policies,
        "best_policy": best["policy"] if best else None,
        "best_policy_score": best["score"] if best else None,
    }


SWEEP_AGING_WEIGHTS = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
SWEEP_STALE_THRESHOLDS = [1, 2, 3]


def run_sweep(
    lanes_path: Path,
    out_path: Path,
    *,
    session_min: int = 150,
    aging_weights: list[float] | None = None,
    stale_thresholds: list[int] | None = None,
) -> dict[str, Any]:
    if aging_weights is None:
        aging_weights = SWEEP_AGING_WEIGHTS
    if stale_thresholds is None:
        stale_thresholds = SWEEP_STALE_THRESHOLDS

    rows = parse_lane_rows(lanes_path.read_text(encoding="utf-8", errors="replace"))
    jobs = build_jobs(rows, session_min=session_min)

    sweep_results: list[dict[str, Any]] = []
    for weight in aging_weights:
        for threshold in stale_thresholds:
            analysis = analyze(jobs, stale_threshold=threshold, aging_weight=weight)
            policies_by_name = {p["policy"]: p for p in analysis.get("policies", [])}
            recency = policies_by_name.get("recency_bias", {})
            aging = policies_by_name.get("queue_aging", {})
            recency_score = recency.get("score", 0.0)
            aging_score = aging.get("score", 0.0)
            if recency_score > aging_score:
                winner = "recency_bias"
                margin = round(recency_score - aging_score, 4)
            elif aging_score > recency_score:
                winner = "queue_aging"
                margin = round(aging_score - recency_score, 4)
            else:
                winner = "tie"
                margin = 0.0
            sweep_results.append(
                {
                    "aging_weight": weight,
                    "stale_threshold": threshold,
                    "recency_score": recency_score,
                    "aging_score": aging_score,
                    "winner": winner,
                    "margin": margin,
                    "recency_metrics": recency.get("metrics", {}),
                    "aging_metrics": aging.get("metrics", {}),
                }
            )

    payload = {
        "frontier_id": "F-OPS3",
        "title": "Queue-aging policy sweep over aging_weight × stale_threshold",
        "inputs": {
            "lanes": str(lanes_path).replace("\\", "/"),
            "session_min": session_min,
            "aging_weights": aging_weights,
            "stale_thresholds": stale_thresholds,
        },
        "job_count": len(jobs),
        "sweep": sweep_results,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def run(
    lanes_path: Path,
    out_path: Path,
    *,
    session_min: int = 150,
    stale_threshold: int = 2,
    aging_weight: float = 1.0,
) -> dict[str, Any]:
    rows = parse_lane_rows(lanes_path.read_text(encoding="utf-8", errors="replace"))
    jobs = build_jobs(rows, session_min=session_min)
    analysis = analyze(jobs, stale_threshold=stale_threshold, aging_weight=aging_weight)
    payload = {
        "frontier_id": "F-OPS3",
        "title": "Queue-aging policy replay over lane-ready backlog",
        "inputs": {
            "lanes": str(lanes_path).replace("\\", "/"),
            "session_min": session_min,
            "stale_threshold": stale_threshold,
            "aging_weight": aging_weight,
        },
        "analysis": analysis,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanes", type=Path, default=Path("tasks/SWARM-LANES.md"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/operations-research/f-ops3-queue-aging-s186.json"),
    )
    parser.add_argument("--session-min", type=int, default=150)
    parser.add_argument("--stale-threshold", type=int, default=2)
    parser.add_argument("--aging-weight", type=float, default=1.0)
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Run a grid sweep over aging_weight × stale_threshold and write summary JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.sweep:
        payload = run_sweep(
            args.lanes,
            args.out,
            session_min=args.session_min,
        )
        print(f"Wrote {args.out}")
        sweep = payload.get("sweep", [])
        aging_wins = [r for r in sweep if r["winner"] == "queue_aging"]
        print(f"sweep_combinations={len(sweep)}, queue_aging_wins={len(aging_wins)}")
        if aging_wins:
            best = max(aging_wins, key=lambda r: r["aging_score"])
            print(
                f"best_aging_combo: weight={best['aging_weight']} threshold={best['stale_threshold']}"
                f" aging_score={best['aging_score']} margin={best['margin']}"
            )
        return 0
    payload = run(
        args.lanes,
        args.out,
        session_min=args.session_min,
        stale_threshold=args.stale_threshold,
        aging_weight=args.aging_weight,
    )
    analysis = payload["analysis"]
    print(f"Wrote {args.out}")
    print(
        "jobs=",
        analysis.get("job_count", 0),
        "best_policy=",
        analysis.get("best_policy"),
        "best_score=",
        analysis.get("best_policy_score"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

