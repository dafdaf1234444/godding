#!/usr/bin/env python3
"""F-GAM3: quantify signaling-contract impact on lane coordination outcomes.

Compares lanes whose active rows explicitly include coordination fields
(`setup`, `focus`, `available`, `blocked`, `next_step`, `human_open_item`)
against lanes that do not.
Primary outcomes:
- closure lag (sessions) from first active row to first closed row
- ready-to-progress lag (sessions) when READY exists
- update count per lane (status-noise proxy)
- update density per lifecycle session (normalizes long-lived lanes)
- stale active rate at current max session
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean, median
from typing import Any

ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
CLOSED_STATUSES = {"MERGED", "ABANDONED"}
PROGRESS_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "MERGED", "ABANDONED"}
CONTRACT_KEYS = ("setup", "focus", "available", "blocked", "next_step", "human_open_item")
LEGACY_CONTRACT_KEYS = ("available", "blocked", "human_open_item")
F121_CONTRACT_KEYS = ("capabilities", "available", "blocked", "next_step", "human_open_item")
MATURE_READY_WINDOW_SESSIONS = 1
DEFAULT_MIN_MATURITY_SESSIONS = 2
IMPACT_DELTA_EPSILON = 1e-4
LOWER_IS_BETTER_METRICS = {
    "mean_closure_lag_sessions",
    "mean_ready_to_progress_lag_sessions",
    "mean_ready_to_close_lag_sessions",
    "mature_ready_unresolved_rate",
    "mean_updates_per_lane",
    "mean_updates_per_lifecycle_session",
    "stale_active_rate",
}
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


def _parse_session(raw: str) -> int | None:
    m = re.search(r"S(\d+)", raw or "")
    return int(m.group(1)) if m else None


def _parse_tags(value: str) -> dict[str, str]:
    return {
        k.strip().lower(): v.strip()
        for k, v in re.findall(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)", value or "")
    }


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


def suppress_same_session_status_noops(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Collapse repeated same lane/session/status rows and keep latest details.

    This treats repeated same-session status appends as no-op lifecycle churn for
    pickup/lag analysis while preserving the latest row payload for that tuple.
    """
    latest_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    key_order: list[tuple[str, str, str]] = []
    suppressed = 0

    for row in rows:
        key = (
            row.get("lane", "").strip(),
            row.get("session", "").strip(),
            row.get("status", "").strip().upper(),
        )
        if key in latest_by_key:
            suppressed += 1
            latest_by_key[key] = row
            continue
        key_order.append(key)
        latest_by_key[key] = row

    return (
        [latest_by_key[key] for key in key_order],
        {
            "input_row_count": len(rows),
            "output_row_count": len(key_order),
            "suppressed_row_count": suppressed,
        },
    )


def apply_latest_session_holdout(
    rows: list[dict[str, str]],
    *,
    holdout_latest_sessions: int,
) -> tuple[list[dict[str, str]], dict[str, int | None]]:
    """Drop rows from the latest N sessions to reduce same-session censoring."""
    if holdout_latest_sessions <= 0:
        return (
            rows,
            {
                "holdout_latest_sessions": 0,
                "max_session": None,
                "session_cutoff": None,
                "input_row_count": len(rows),
                "output_row_count": len(rows),
                "suppressed_row_count": 0,
            },
        )

    parsed_sessions = [_parse_session(row.get("session", "")) for row in rows]
    session_values = [s for s in parsed_sessions if s is not None]
    if not session_values:
        return (
            rows,
            {
                "holdout_latest_sessions": holdout_latest_sessions,
                "max_session": None,
                "session_cutoff": None,
                "input_row_count": len(rows),
                "output_row_count": len(rows),
                "suppressed_row_count": 0,
            },
        )

    max_session = max(session_values)
    session_cutoff = max_session - holdout_latest_sessions
    filtered = [
        row
        for row in rows
        if (_parse_session(row.get("session", "")) is None)
        or (int(_parse_session(row.get("session", "")) or 0) <= session_cutoff)
    ]
    suppressed = len(rows) - len(filtered)
    return (
        filtered,
        {
            "holdout_latest_sessions": holdout_latest_sessions,
            "max_session": max_session,
            "session_cutoff": session_cutoff,
            "input_row_count": len(rows),
            "output_row_count": len(filtered),
            "suppressed_row_count": suppressed,
        },
    )


def has_contract(row: dict[str, str], required_keys: tuple[str, ...] = CONTRACT_KEYS) -> bool:
    tags = _parse_tags(row.get("etc", ""))
    # Accept explicit key presence even when value is "none".
    return all(key in tags for key in required_keys)


def _mean(values: list[float]) -> float:
    return round(fmean(values), 4) if values else 0.0


def _median(values: list[float]) -> float:
    return round(float(median(values)), 4) if values else 0.0


def _impact_label(metric: str, delta: float) -> str:
    if abs(delta) <= IMPACT_DELTA_EPSILON:
        return "unchanged"
    if metric in LOWER_IS_BETTER_METRICS:
        return "improved" if delta < 0 else "worsened"
    return "improved" if delta > 0 else "worsened"


def historian_analysis(deltas: dict[str, float]) -> dict[str, Any]:
    unchanged: list[str] = []
    changed: list[dict[str, Any]] = []
    for metric, raw_delta in deltas.items():
        delta = float(raw_delta)
        if abs(delta) <= IMPACT_DELTA_EPSILON:
            unchanged.append(metric)
            continue
        changed.append(
            {
                "metric": metric,
                "delta_contract_minus_free_form": round(delta, 4),
                "absolute_delta": round(abs(delta), 4),
                "impact_on_contract_outcome": _impact_label(metric, delta),
            }
        )

    changed.sort(key=lambda item: (-float(item["absolute_delta"]), str(item["metric"])))
    return {
        "delta_epsilon": IMPACT_DELTA_EPSILON,
        "unchanged_metric_count": len(unchanged),
        "unchanged_metrics": unchanged,
        "changed_metric_count": len(changed),
        "changed_metrics_ranked": changed,
        "most_impactful_change": changed[0] if changed else None,
    }


def summarize_group(items: list[dict[str, Any]], *, max_session: int) -> dict[str, Any]:
    closure_lags = [x["closure_lag"] for x in items if x["closure_lag"] is not None]
    ready_lags = [x["ready_to_progress_lag"] for x in items if x["ready_to_progress_lag"] is not None]
    updates = [x["update_count"] for x in items]
    update_density = [x["updates_per_lifecycle_session"] for x in items if x["updates_per_lifecycle_session"] is not None]
    active_items = [x for x in items if x["latest_status"] in ACTIVE_STATUSES and x["latest_session"] is not None]
    stale = [x for x in active_items if (max_session - int(x["latest_session"])) > 1]
    same_session_closed = [x for x in closure_lags if x == 0]
    mature_ready_cutoff = max_session - MATURE_READY_WINDOW_SESSIONS
    mature_ready_items = [
        x
        for x in items
        if x["first_ready_session"] is not None and int(x["first_ready_session"]) <= mature_ready_cutoff
    ]
    mature_ready_lags = [x["ready_to_progress_lag"] for x in mature_ready_items if x["ready_to_progress_lag"] is not None]
    mature_ready_unresolved_count = len(mature_ready_items) - len(mature_ready_lags)

    return {
        "lane_count": len(items),
        "closed_lane_count": len(closure_lags),
        "mean_closure_lag_sessions": _mean([float(v) for v in closure_lags]),
        "median_closure_lag_sessions": _median([float(v) for v in closure_lags]),
        "same_session_close_rate": round(len(same_session_closed) / len(closure_lags), 4) if closure_lags else 0.0,
        "mean_ready_to_progress_lag_sessions": _mean([float(v) for v in ready_lags]),
        "median_ready_to_progress_lag_sessions": _median([float(v) for v in ready_lags]),
        "mean_ready_to_close_lag_sessions": _mean([float(v) for v in ready_lags]),
        "median_ready_to_close_lag_sessions": _median([float(v) for v in ready_lags]),
        "ready_to_progress_count": len(ready_lags),
        "mature_ready_window_sessions": MATURE_READY_WINDOW_SESSIONS,
        "mature_ready_eligible_count": len(mature_ready_items),
        "mature_ready_unresolved_count": mature_ready_unresolved_count,
        "mature_ready_unresolved_rate": (
            round(mature_ready_unresolved_count / len(mature_ready_items), 4) if mature_ready_items else 0.0
        ),
        "mature_mean_ready_to_progress_lag_sessions": _mean([float(v) for v in mature_ready_lags]),
        "mean_updates_per_lane": _mean([float(v) for v in updates]),
        "mean_updates_per_lifecycle_session": _mean([float(v) for v in update_density]),
        "median_updates_per_lifecycle_session": _median([float(v) for v in update_density]),
        "stale_active_rate": round(len(stale) / len(active_items), 4) if active_items else 0.0,
    }


def _cohort_ab(
    lane_rows: list[dict[str, Any]],
    *,
    max_session: int,
    contract_key: str = "contract_explicit",
) -> dict[str, Any]:
    contract = [row for row in lane_rows if row.get(contract_key)]
    free_form = [row for row in lane_rows if not row.get(contract_key)]
    contract_summary = summarize_group(contract, max_session=max_session)
    free_form_summary = summarize_group(free_form, max_session=max_session)

    def _delta(key: str) -> float:
        return round(float(contract_summary.get(key, 0.0)) - float(free_form_summary.get(key, 0.0)), 4)

    deltas = {
        "mean_closure_lag_sessions": _delta("mean_closure_lag_sessions"),
        "mean_ready_to_progress_lag_sessions": _delta("mean_ready_to_progress_lag_sessions"),
        "mean_ready_to_close_lag_sessions": _delta("mean_ready_to_close_lag_sessions"),
        "mature_ready_unresolved_rate": _delta("mature_ready_unresolved_rate"),
        "mean_updates_per_lane": _delta("mean_updates_per_lane"),
        "mean_updates_per_lifecycle_session": _delta("mean_updates_per_lifecycle_session"),
        "stale_active_rate": _delta("stale_active_rate"),
    }

    return {
        "contract_group": contract_summary,
        "free_form_group": free_form_summary,
        "deltas_contract_minus_free_form": deltas,
        "historian_analysis": historian_analysis(deltas),
    }


def _adoption_trend(rows: list[dict[str, str]], *, tail_sessions: int = 12) -> list[dict[str, Any]]:
    active_by_session: dict[int, int] = defaultdict(int)
    strict_by_session: dict[int, int] = defaultdict(int)
    legacy_by_session: dict[int, int] = defaultdict(int)
    f121_by_session: dict[int, int] = defaultdict(int)

    for row in rows:
        if row.get("status", "") not in ACTIVE_STATUSES:
            continue
        session = _parse_session(row.get("session", ""))
        if session is None:
            continue
        active_by_session[session] += 1
        if has_contract(row):
            strict_by_session[session] += 1
        if has_contract(row, required_keys=LEGACY_CONTRACT_KEYS):
            legacy_by_session[session] += 1
        if has_contract(row, required_keys=F121_CONTRACT_KEYS):
            f121_by_session[session] += 1

    sessions = sorted(active_by_session.keys())[-max(1, tail_sessions) :]
    trend: list[dict[str, Any]] = []
    for session in sessions:
        active = active_by_session[session]
        strict = strict_by_session.get(session, 0)
        legacy = legacy_by_session.get(session, 0)
        f121 = f121_by_session.get(session, 0)
        trend.append(
            {
                "session": session,
                "active_rows": active,
                "strict_contract_rows": strict,
                "legacy_contract_rows": legacy,
                "f121_contract_rows": f121,
                "strict_rate": round(strict / active, 4) if active else 0.0,
                "legacy_rate": round(legacy / active, 4) if active else 0.0,
                "f121_rate": round(f121 / active, 4) if active else 0.0,
            }
        )
    return trend


def analyze(rows: list[dict[str, str]], *, min_maturity_sessions: int = DEFAULT_MIN_MATURITY_SESSIONS) -> dict[str, Any]:
    by_lane: dict[str, list[dict[str, str]]] = defaultdict(list)
    sessions: list[int] = []

    for row in rows:
        lane = row.get("lane", "").strip()
        if not lane:
            continue
        by_lane[lane].append(row)
        s = _parse_session(row.get("session", ""))
        if s is not None:
            sessions.append(s)

    max_session = max(sessions) if sessions else 0
    lane_rows: list[dict[str, Any]] = []

    for lane, seq in by_lane.items():
        first_active = None
        first_ready = None
        first_progress = None
        first_closed = None
        latest = seq[-1]
        contract_seen_on_active = False
        legacy_contract_seen_on_active = False
        f121_contract_seen_on_active = False
        capabilities_seen_on_active = False

        for row in seq:
            status = row.get("status", "")
            if first_active is None and status in ACTIVE_STATUSES:
                first_active = row
            if status in ACTIVE_STATUSES and has_contract(row):
                contract_seen_on_active = True
            if status in ACTIVE_STATUSES and has_contract(row, required_keys=LEGACY_CONTRACT_KEYS):
                legacy_contract_seen_on_active = True
            if status in ACTIVE_STATUSES and has_contract(row, required_keys=F121_CONTRACT_KEYS):
                f121_contract_seen_on_active = True
            if status in ACTIVE_STATUSES and "capabilities" in _parse_tags(row.get("etc", "")):
                capabilities_seen_on_active = True
            if first_ready is None and status == "READY":
                first_ready = row
            if first_progress is None and status in PROGRESS_STATUSES:
                first_progress = row
            if first_closed is None and status in CLOSED_STATUSES:
                first_closed = row

        active_session = _parse_session(first_active.get("session", "")) if first_active else None
        ready_session = _parse_session(first_ready.get("session", "")) if first_ready else None
        progress_session = _parse_session(first_progress.get("session", "")) if first_progress else None
        closed_session = _parse_session(first_closed.get("session", "")) if first_closed else None
        latest_session = _parse_session(latest.get("session", ""))

        closure_lag = None
        if active_session is not None and closed_session is not None and closed_session >= active_session:
            closure_lag = closed_session - active_session

        ready_lag = None
        if ready_session is not None and progress_session is not None and progress_session >= ready_session:
            ready_lag = progress_session - ready_session

        lifecycle_end = closed_session if closed_session is not None else latest_session
        lifecycle_span = None
        if active_session is not None and lifecycle_end is not None and lifecycle_end >= active_session:
            lifecycle_span = lifecycle_end - active_session + 1
        updates_per_lifecycle = None
        if lifecycle_span is not None and lifecycle_span > 0:
            updates_per_lifecycle = round(len(seq) / lifecycle_span, 4)
        matured = False
        if active_session is not None and max_session >= active_session:
            # Use observation age from global max session so same-session closes from older
            # sessions are still considered mature in retrospective analysis.
            matured = (max_session - active_session) >= min_maturity_sessions

        lane_rows.append(
            {
                "lane": lane,
                "contract_explicit": contract_seen_on_active,
                "legacy_contract_explicit": legacy_contract_seen_on_active,
                "f121_contract_explicit": f121_contract_seen_on_active,
                "capabilities_explicit": capabilities_seen_on_active,
                "first_active_status": (first_active or {}).get("status"),
                "first_active_session": active_session,
                "first_ready_session": ready_session,
                "first_progress_session": progress_session,
                "first_closed_session": closed_session,
                "closure_lag": closure_lag,
                "ready_to_progress_lag": ready_lag,
                "ready_to_close_lag": ready_lag,
                "update_count": len(seq),
                "lifecycle_span_sessions": lifecycle_span,
                "updates_per_lifecycle_session": updates_per_lifecycle,
                "matured": matured,
                "latest_status": latest.get("status"),
                "latest_session": latest_session,
            }
        )

    contract = [row for row in lane_rows if row["contract_explicit"]]
    legacy_contract_count = sum(1 for row in lane_rows if row["legacy_contract_explicit"])
    f121_contract_count = sum(1 for row in lane_rows if row["f121_contract_explicit"])
    capabilities_count = sum(1 for row in lane_rows if row["capabilities_explicit"])
    matured_rows = [row for row in lane_rows if row["matured"]]
    matured_contract_count = sum(1 for row in matured_rows if row["contract_explicit"])
    matured_f121_count = sum(1 for row in matured_rows if row["f121_contract_explicit"])

    all_ab = _cohort_ab(lane_rows, max_session=max_session)
    matured_ab = _cohort_ab(matured_rows, max_session=max_session)
    f121_all_ab = _cohort_ab(lane_rows, max_session=max_session, contract_key="f121_contract_explicit")
    f121_matured_ab = _cohort_ab(matured_rows, max_session=max_session, contract_key="f121_contract_explicit")
    matured_contract_n = int(matured_ab["contract_group"]["lane_count"])
    matured_free_form_n = int(matured_ab["free_form_group"]["lane_count"])
    matured_viable = matured_contract_n > 0 and matured_free_form_n > 0
    f121_matured_contract_n = int(f121_matured_ab["contract_group"]["lane_count"])
    f121_matured_free_form_n = int(f121_matured_ab["free_form_group"]["lane_count"])
    f121_matured_viable = f121_matured_contract_n > 0 and f121_matured_free_form_n > 0

    return {
        "max_session": max_session,
        "lane_count_total": len(lane_rows),
        "min_maturity_sessions": min_maturity_sessions,
        "contract_adoption": {
            "strict_contract_lanes": len(contract),
            "legacy_contract_lanes": legacy_contract_count,
            "strict_contract_rate": round(len(contract) / len(lane_rows), 4) if lane_rows else 0.0,
            "legacy_contract_rate": round(legacy_contract_count / len(lane_rows), 4) if lane_rows else 0.0,
            "f121_contract_lanes": f121_contract_count,
            "f121_contract_rate": round(f121_contract_count / len(lane_rows), 4) if lane_rows else 0.0,
            "capabilities_tagged_lanes": capabilities_count,
            "capabilities_tagged_rate": round(capabilities_count / len(lane_rows), 4) if lane_rows else 0.0,
            "matured_lanes": len(matured_rows),
            "matured_strict_contract_lanes": matured_contract_count,
            "matured_strict_contract_rate": round(matured_contract_count / len(matured_rows), 4)
            if matured_rows
            else 0.0,
            "matured_f121_contract_lanes": matured_f121_count,
            "matured_f121_contract_rate": round(matured_f121_count / len(matured_rows), 4) if matured_rows else 0.0,
        },
        "all_lanes_ab": all_ab,
        "matured_lanes_ab": matured_ab,
        "f121_contract_ab": {
            "contract_keys": list(F121_CONTRACT_KEYS),
            "all_lanes": f121_all_ab,
            "matured_lanes": f121_matured_ab,
            "matured_cohort_viability": {
                "contract_lane_count": f121_matured_contract_n,
                "free_form_lane_count": f121_matured_free_form_n,
                "viable_for_ab": f121_matured_viable,
                "reason": (
                    "both cohorts populated"
                    if f121_matured_viable
                    else "insufficient matured cohort coverage for F121 contract A/B"
                ),
            },
        },
        "matured_cohort_viability": {
            "contract_lane_count": matured_contract_n,
            "free_form_lane_count": matured_free_form_n,
            "viable_for_ab": matured_viable,
            "reason": (
                "both cohorts populated"
                if matured_viable
                else "insufficient matured cohort coverage for strict contract A/B"
            ),
        },
        "adoption_trend_active_rows": {
            "tail_sessions": 12,
            "rows": _adoption_trend(rows, tail_sessions=12),
        },
        "lane_samples": lane_rows[:40],
    }


def run(
    lanes_path: Path,
    out_path: Path,
    *,
    min_maturity_sessions: int = DEFAULT_MIN_MATURITY_SESSIONS,
    holdout_latest_sessions: int = 0,
    suppress_noop_rows: bool = False,
) -> dict[str, Any]:
    rows = parse_rows(lanes_path.read_text(encoding="utf-8", errors="replace"))
    preprocessing = {
        "holdout_latest_sessions": max(0, int(holdout_latest_sessions)),
        "holdout_input_row_count": len(rows),
        "holdout_output_row_count": len(rows),
        "holdout_suppressed_row_count": 0,
        "holdout_max_session": None,
        "holdout_session_cutoff": None,
        "suppress_noop_rows": bool(suppress_noop_rows),
        "input_row_count": len(rows),
        "output_row_count": len(rows),
        "suppressed_row_count": 0,
    }
    if holdout_latest_sessions > 0:
        rows, holdout_stats = apply_latest_session_holdout(
            rows,
            holdout_latest_sessions=max(0, int(holdout_latest_sessions)),
        )
        preprocessing.update(
            {
                "holdout_latest_sessions": holdout_stats["holdout_latest_sessions"],
                "holdout_input_row_count": holdout_stats["input_row_count"],
                "holdout_output_row_count": holdout_stats["output_row_count"],
                "holdout_suppressed_row_count": holdout_stats["suppressed_row_count"],
                "holdout_max_session": holdout_stats["max_session"],
                "holdout_session_cutoff": holdout_stats["session_cutoff"],
            }
        )
        preprocessing.update(
            {
                "input_row_count": len(rows),
                "output_row_count": len(rows),
                "suppressed_row_count": 0,
            }
        )
    if suppress_noop_rows:
        rows, stats = suppress_same_session_status_noops(rows)
        preprocessing.update(stats)
    analysis = analyze(rows, min_maturity_sessions=min_maturity_sessions)

    result = {
        "frontier_id": "F-GAM3",
        "title": "Signaling-contract A/B against lane-history outcomes",
        "input": str(lanes_path).replace("\\", "/"),
        "contract_keys": list(CONTRACT_KEYS),
        "legacy_contract_keys": list(LEGACY_CONTRACT_KEYS),
        "f121_contract_keys": list(F121_CONTRACT_KEYS),
        "preprocessing": preprocessing,
        "analysis": analysis,
        "interpretation": {
            "note": (
                "Lower lag/stale rates are better; lower updates-per-lane is lower status noise."
            ),
            "matured_note": (
                "Matured-lane A/B reduces censoring by requiring lifecycle age >= min_maturity_sessions."
            ),
            "mature_ready_note": (
                "Mature-ready metrics exclude lanes whose first READY session is within 1 session of current max "
                "to reduce same-session censoring."
            ),
            "caveat": (
                "Observational lane-history analysis, not randomized assignment; causal claims remain limited."
            ),
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanes", type=Path, default=Path("tasks/SWARM-LANES.md"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/game-theory/f-gam3-signaling-contract-s186.json"),
    )
    parser.add_argument(
        "--min-maturity-sessions",
        type=int,
        default=DEFAULT_MIN_MATURITY_SESSIONS,
        help="Minimum lifecycle age (sessions) for matured-lane A/B cohort.",
    )
    parser.add_argument(
        "--suppress-noop-rows",
        action="store_true",
        help="Collapse repeated same lane/session/status rows before analysis.",
    )
    parser.add_argument(
        "--holdout-latest-sessions",
        type=int,
        default=0,
        help="Exclude rows from the latest N sessions before analysis.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(
        args.lanes,
        args.out,
        min_maturity_sessions=max(0, args.min_maturity_sessions),
        holdout_latest_sessions=max(0, args.holdout_latest_sessions),
        suppress_noop_rows=bool(args.suppress_noop_rows),
    )
    cg = result["analysis"]["all_lanes_ab"]["contract_group"]
    fg = result["analysis"]["all_lanes_ab"]["free_form_group"]
    mg = result["analysis"]["matured_lanes_ab"]["contract_group"]
    mf = result["analysis"]["matured_lanes_ab"]["free_form_group"]
    print(f"Wrote {args.out}")
    print(
        "contract_lanes=",
        cg["lane_count"],
        "free_form_lanes=",
        fg["lane_count"],
        "contract_mean_closure_lag=",
        cg["mean_closure_lag_sessions"],
        "free_form_mean_closure_lag=",
        fg["mean_closure_lag_sessions"],
    )
    print(
        "matured_contract_lanes=",
        mg["lane_count"],
        "matured_free_form_lanes=",
        mf["lane_count"],
        "matured_contract_update_density=",
        mg["mean_updates_per_lifecycle_session"],
        "matured_free_form_update_density=",
        mf["mean_updates_per_lifecycle_session"],
    )
    f121 = result["analysis"]["f121_contract_ab"]["all_lanes"]
    print(
        "f121_contract_lanes=",
        f121["contract_group"]["lane_count"],
        "f121_free_form_lanes=",
        f121["free_form_group"]["lane_count"],
        "f121_mean_updates_delta=",
        f121["deltas_contract_minus_free_form"]["mean_updates_per_lane"],
    )
    pre = result.get("preprocessing", {})
    print(
        "holdout_latest_sessions=",
        pre.get("holdout_latest_sessions", 0),
        "holdout_suppressed_rows=",
        pre.get("holdout_suppressed_row_count", 0),
        "holdout_session_cutoff=",
        pre.get("holdout_session_cutoff"),
    )
    print(
        "suppressed_rows=",
        pre.get("suppressed_row_count", 0),
        "input_rows=",
        pre.get("input_row_count", 0),
        "output_rows=",
        pre.get("output_row_count", 0),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
