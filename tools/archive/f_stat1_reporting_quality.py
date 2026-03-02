#!/usr/bin/env python3
"""F-STAT1: baseline how well active lanes report actionable swarm state."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean, median
from typing import Any

ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
CLOSED_STATUSES = {"MERGED", "DONE", "CLOSED", "DROPPED", "CANCELLED", "ABANDONED", "SUPERSEDED", "ARCHIVED"}
PICKUP_SOURCE_STATUSES = {"READY", "CLAIMED"}
PICKUP_TARGET_STATUSES = {"ACTIVE", "BLOCKED", "MERGED", "DONE", "CLOSED"}
PLACEHOLDERS = {"", "-", "n/a", "na", "pending", "tbd", "unknown"}
CLEAR_STATE_VALUES = {
    "none",
    "none_recorded",
    "none-recorded",
    "no",
    "false",
    "0",
    "unblocked",
    "clear",
    "not_needed",
    "not-needed",
}

REPORT_KEYS = (
    "capabilities",
    "intent",
    "progress",
    "available",
    "blocked",
    "next_step",
    "human_open_item",
)

KEY_WEIGHTS: dict[str, float] = {
    "capabilities": 0.20,
    "intent": 0.20,
    "progress": 0.15,
    "available": 0.15,
    "blocked": 0.10,
    "next_step": 0.10,
    "human_open_item": 0.10,
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


def _is_placeholder(value: str) -> bool:
    return (value or "").strip().lower() in PLACEHOLDERS


def _parse_lane_tags(value: str) -> dict[str, str]:
    return {
        k.strip().lower(): v.strip()
        for k, v in re.findall(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)", value or "")
    }


def _parse_session_number(raw: str) -> int | None:
    m = re.search(r"S(\d+)", raw or "")
    return int(m.group(1)) if m else None


def _tag_value(tags: dict[str, str], *keys: str) -> str:
    for key in keys:
        if key in tags:
            return tags.get(key, "")
    return ""


def _is_clear_state(value: str) -> bool:
    return (value or "").strip().lower() in CLEAR_STATE_VALUES


def _scope_domain(scope_key: str) -> str | None:
    m = re.search(r"domains/([^/\s]+)/", scope_key or "")
    return m.group(1) if m else None


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 4)
    ordered = sorted(values)
    rank = (len(ordered) - 1) * p
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return round(ordered[lower], 4)
    frac = rank - lower
    interp = ordered[lower] * (1.0 - frac) + ordered[upper] * frac
    return round(interp, 4)


def has_schema_contract(row: dict[str, str]) -> bool:
    tags = _parse_lane_tags(row.get("etc", ""))
    has_capabilities = not _is_placeholder(row.get("model", "")) and not _is_placeholder(row.get("platform", ""))
    has_available = "available" in tags
    has_blocked = "blocked" in tags or "blocker" in tags
    has_next_step = any(k in tags for k in ("next_step", "next", "action", "plan", "dispatch"))
    has_human_open = "human_open_item" in tags or "human_open" in tags
    return has_capabilities and has_available and has_blocked and has_next_step and has_human_open


def _build_pickup_cohort_stats(deltas: list[int]) -> dict[str, Any]:
    if not deltas:
        return {
            "count": 0,
            "mean_latency_sessions": None,
            "median_latency_sessions": None,
            "p90_latency_sessions": None,
            "same_session_rate": None,
            "within_one_session_rate": None,
            "cross_session_rate": None,
            "cross_session_mean_latency_sessions": None,
            "stale_over_two_sessions_rate": None,
        }
    cross_session = [value for value in deltas if value >= 1]
    return {
        "count": len(deltas),
        "mean_latency_sessions": round(fmean(deltas), 4),
        "median_latency_sessions": round(median(deltas), 4),
        "p90_latency_sessions": _percentile([float(v) for v in deltas], 0.90),
        "same_session_rate": round(sum(1 for value in deltas if value == 0) / len(deltas), 4),
        "within_one_session_rate": round(sum(1 for value in deltas if value <= 1) / len(deltas), 4),
        "cross_session_rate": round(len(cross_session) / len(deltas), 4),
        "cross_session_mean_latency_sessions": (
            round(fmean(cross_session), 4) if cross_session else None
        ),
        "stale_over_two_sessions_rate": round(sum(1 for value in deltas if value > 2) / len(deltas), 4),
    }


def _build_handoff_cohort_stats(
    deltas: list[int],
    *,
    eligible_count: int,
    unresolved_count: int,
) -> dict[str, Any]:
    stats = _build_pickup_cohort_stats(deltas)
    resolved_count = len(deltas)
    pickup_rate = None
    unresolved_rate = None
    if eligible_count > 0:
        pickup_rate = round(resolved_count / eligible_count, 4)
        unresolved_rate = round(unresolved_count / eligible_count, 4)
    stats.update(
        {
            "eligible_count": eligible_count,
            "resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "pickup_rate": pickup_rate,
            "unresolved_rate": unresolved_rate,
        }
    )
    return stats


def build_pickup_latency_ab(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_lane: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        lane = row.get("lane", "").strip()
        if lane:
            by_lane.setdefault(lane, []).append(row)

    schema_contract_deltas: list[int] = []
    free_form_deltas: list[int] = []
    schema_handoff_deltas: list[int] = []
    free_form_handoff_deltas: list[int] = []
    schema_handoff_eligible = 0
    free_form_handoff_eligible = 0
    schema_handoff_unresolved = 0
    free_form_handoff_unresolved = 0

    for lane_rows in by_lane.values():
        if len(lane_rows) >= 2:
            for idx in range(len(lane_rows) - 1):
                current = lane_rows[idx]
                nxt = lane_rows[idx + 1]
                current_status = (current.get("status", "") or "").upper()
                if current_status in CLOSED_STATUSES:
                    continue
                current_session = _parse_session_number(current.get("session", ""))
                next_session = _parse_session_number(nxt.get("session", ""))
                if current_session is None or next_session is None:
                    continue
                if next_session < current_session:
                    continue
                delta = next_session - current_session
                if has_schema_contract(current):
                    schema_contract_deltas.append(delta)
                else:
                    free_form_deltas.append(delta)

        for idx, current in enumerate(lane_rows):
            current_status = (current.get("status", "") or "").upper()
            if current_status not in PICKUP_SOURCE_STATUSES:
                continue
            current_session = _parse_session_number(current.get("session", ""))
            if current_session is None:
                continue
            schema_row = has_schema_contract(current)
            if schema_row:
                schema_handoff_eligible += 1
            else:
                free_form_handoff_eligible += 1

            matched_delta: int | None = None
            for follow in lane_rows[idx + 1 :]:
                follow_session = _parse_session_number(follow.get("session", ""))
                if follow_session is None or follow_session < current_session:
                    continue
                follow_status = (follow.get("status", "") or "").upper()
                if follow_status not in PICKUP_TARGET_STATUSES:
                    continue
                matched_delta = follow_session - current_session
                break

            if matched_delta is None:
                if schema_row:
                    schema_handoff_unresolved += 1
                else:
                    free_form_handoff_unresolved += 1
            elif schema_row:
                schema_handoff_deltas.append(matched_delta)
            else:
                free_form_handoff_deltas.append(matched_delta)

    schema_stats = _build_pickup_cohort_stats(schema_contract_deltas)
    free_form_stats = _build_pickup_cohort_stats(free_form_deltas)
    handoff_schema_stats = _build_handoff_cohort_stats(
        schema_handoff_deltas,
        eligible_count=schema_handoff_eligible,
        unresolved_count=schema_handoff_unresolved,
    )
    handoff_free_form_stats = _build_handoff_cohort_stats(
        free_form_handoff_deltas,
        eligible_count=free_form_handoff_eligible,
        unresolved_count=free_form_handoff_unresolved,
    )

    schema_mean = schema_stats["mean_latency_sessions"]
    free_mean = free_form_stats["mean_latency_sessions"]
    schema_median = schema_stats["median_latency_sessions"]
    free_median = free_form_stats["median_latency_sessions"]
    mean_delta = None
    median_delta = None
    if schema_mean is not None and free_mean is not None:
        mean_delta = round(free_mean - schema_mean, 4)
    if schema_median is not None and free_median is not None:
        median_delta = round(free_median - schema_median, 4)

    handoff_schema_mean = handoff_schema_stats["mean_latency_sessions"]
    handoff_free_mean = handoff_free_form_stats["mean_latency_sessions"]
    handoff_schema_median = handoff_schema_stats["median_latency_sessions"]
    handoff_free_median = handoff_free_form_stats["median_latency_sessions"]
    handoff_schema_pickup = handoff_schema_stats["pickup_rate"]
    handoff_free_pickup = handoff_free_form_stats["pickup_rate"]
    handoff_mean_delta = None
    handoff_median_delta = None
    handoff_pickup_delta = None
    if handoff_schema_mean is not None and handoff_free_mean is not None:
        handoff_mean_delta = round(handoff_free_mean - handoff_schema_mean, 4)
    if handoff_schema_median is not None and handoff_free_median is not None:
        handoff_median_delta = round(handoff_free_median - handoff_schema_median, 4)
    if handoff_schema_pickup is not None and handoff_free_pickup is not None:
        handoff_pickup_delta = round(handoff_free_pickup - handoff_schema_pickup, 4)

    return {
        "cohort_definition": {
            "schema_contract": "capabilities(model+platform)+available+blocked+next_step+human_open_item in tags",
            "free_form": "lane row without full schema contract tags",
            "latency_metric": "session delta to the next same-lane update (smaller is better)",
            "excluded_statuses": sorted(CLOSED_STATUSES),
        },
        "schema_contract": schema_stats,
        "free_form": free_form_stats,
        "comparison": {
            "mean_delta_sessions_free_minus_schema": mean_delta,
            "median_delta_sessions_free_minus_schema": median_delta,
            "schema_faster": (mean_delta is not None and mean_delta > 0),
        },
        "handoff_window_ab": {
            "source_statuses": sorted(PICKUP_SOURCE_STATUSES),
            "target_statuses": sorted(PICKUP_TARGET_STATUSES),
            "latency_metric": (
                "session delta from READY/CLAIMED rows to first same-lane ACTIVE/BLOCKED/MERGED touch"
            ),
            "schema_contract": handoff_schema_stats,
            "free_form": handoff_free_form_stats,
            "comparison": {
                "mean_delta_sessions_free_minus_schema": handoff_mean_delta,
                "median_delta_sessions_free_minus_schema": handoff_median_delta,
                "pickup_rate_delta_free_minus_schema": handoff_pickup_delta,
                "schema_faster": (handoff_mean_delta is not None and handoff_mean_delta > 0),
            },
        },
    }


def parse_lane_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|") or re.match(r"^\|\s*(Date\s*\||[-: ]+\|)", line, re.IGNORECASE):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < len(LANE_KEYS):
            continue
        row = dict(zip(LANE_KEYS, parts))
        row["status"] = row["status"].upper()
        rows.append(row)
    return rows


def latest_active_lanes(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    latest_by_lane: dict[str, dict[str, str]] = {}
    for row in rows:
        lane = row.get("lane", "").strip()
        if lane:
            latest_by_lane[lane] = row
    active = [row for row in latest_by_lane.values() if row.get("status", "") in ACTIVE_STATUSES]
    return sorted(active, key=lambda item: item.get("lane", ""))


def detect_reporting_fields(row: dict[str, str]) -> dict[str, bool]:
    tags = _parse_lane_tags(row.get("etc", ""))
    notes = (row.get("notes", "") or "").lower()
    status = (row.get("status", "") or "").upper()

    capabilities = (
        (not _is_placeholder(row.get("model", "")) and not _is_placeholder(row.get("platform", "")))
        or any(k in tags for k in ("setup", "capability", "capabilities", "tool", "tools"))
    )
    intent = (
        any(k in tags for k in ("intent", "objective", "goal", "frontier", "dispatch", "task"))
        or bool(re.search(r"\b(intent|objective|goal|frontier|queued|run|execute|measure|investigate)\b", notes))
    )
    progress = status in ACTIVE_STATUSES or bool(
        re.search(r"\b(added|ran|implemented|produced|verified|updated|queued|ready|fixed|executed)\b", notes)
    )
    available = (
        any(k in tags for k in ("available", "capacity", "availability", "ready"))
        or bool(re.search(r"\b(available|ready|queued)\b", notes))
        or status in {"CLAIMED", "ACTIVE", "READY"}
    )
    # Presence of blocked/human_open_item key counts even when value is "none":
    # that explicit "no blocker/no human ask" state is useful coordination signal.
    blocked = (
        "blocked" in tags
        or "blocker" in tags
        or status == "BLOCKED"
        or bool(re.search(r"\b(blocked|blocker|waiting|stuck|dependency|depends|requires)\b", notes))
        or bool(re.search(r"\b(no|none|unblocked)\s+(?:blocker|blockers)\b", notes))
    )
    next_step = (
        any(k in tags for k in ("next", "next_step", "action", "dispatch", "plan"))
        or bool(re.search(r"\b(next|follow-up|queued|run|execute|measure|rerun|investigate)\b", notes))
    )
    human_open_item = (
        "human_open_item" in tags
        or "human_open" in tags
        or bool(re.search(r"\bhuman[_ -]?open[_ -]?item\b", notes))
        or bool(re.search(r"\bhuman\b.*\b(needed|required|review|decision|ask|none|not needed)\b", notes))
    )

    return {
        "capabilities": capabilities,
        "intent": intent,
        "progress": progress,
        "available": available,
        "blocked": blocked,
        "next_step": next_step,
        "human_open_item": human_open_item,
    }


def detect_explicit_reporting_fields(row: dict[str, str]) -> dict[str, bool]:
    tags = _parse_lane_tags(row.get("etc", ""))

    return {
        "capabilities": (
            "setup" in tags
            and not _is_placeholder(row.get("model", ""))
            and not _is_placeholder(row.get("platform", ""))
        ),
        "intent": any(k in tags for k in ("intent", "objective", "goal", "frontier", "dispatch", "task")),
        "progress": any(k in tags for k in ("progress", "status_note", "evidence", "artifact")),
        "available": "available" in tags,
        "blocked": "blocked" in tags or "blocker" in tags,
        "next_step": any(k in tags for k in ("next_step", "next", "action", "plan")),
        "human_open_item": "human_open_item" in tags or "human_open" in tags,
    }


def reporting_score(fields: dict[str, bool]) -> float:
    return round(sum(KEY_WEIGHTS[k] for k in REPORT_KEYS if fields.get(k)), 4)


def build_report(active_rows: list[dict[str, str]], history_rows: list[dict[str, str]] | None = None) -> dict[str, Any]:
    lane_rows: list[dict[str, Any]] = []
    key_counts = {key: 0 for key in REPORT_KEYS}
    explicit_key_counts = {key: 0 for key in REPORT_KEYS}
    scores: list[float] = []
    explicit_scores: list[float] = []
    contract_ready = 0
    explicit_contract_ready = 0
    sessions: list[int] = []
    dispatchable_lanes: list[dict[str, Any]] = []
    non_dispatchable_lanes: list[dict[str, Any]] = []
    non_dispatchable_reason_counts: dict[str, int] = {}

    for row in active_rows:
        fields = detect_reporting_fields(row)
        explicit_fields = detect_explicit_reporting_fields(row)
        score = reporting_score(fields)
        explicit_score = reporting_score(explicit_fields)
        missing = [key for key in REPORT_KEYS if not fields.get(key)]
        explicit_missing = [key for key in REPORT_KEYS if not explicit_fields.get(key)]
        present = [key for key in REPORT_KEYS if fields.get(key)]
        explicit_present = [key for key in REPORT_KEYS if explicit_fields.get(key)]
        if not missing:
            contract_ready += 1
        if not explicit_missing:
            explicit_contract_ready += 1
        for key in present:
            key_counts[key] += 1
        for key in explicit_present:
            explicit_key_counts[key] += 1
        scores.append(score)
        explicit_scores.append(explicit_score)
        session_no = _parse_session_number(row.get("session", ""))
        if session_no is not None:
            sessions.append(session_no)
        lane_rows.append(
            {
                "lane": row.get("lane", ""),
                "status": row.get("status", ""),
                "session": row.get("session", ""),
                "scope_key": row.get("scope_key", ""),
                "score": score,
                "explicit_score": explicit_score,
                "present_keys": present,
                "missing_keys": missing,
                "explicit_present_keys": explicit_present,
                "explicit_missing_keys": explicit_missing,
            }
        )

        tags = _parse_lane_tags(row.get("etc", ""))
        blocked_value = _tag_value(tags, "blocked", "blocker")
        human_open_value = _tag_value(tags, "human_open_item", "human_open")
        next_step_value = _tag_value(tags, "next_step", "next", "action", "plan", "dispatch")

        reasons: list[str] = []
        if not fields.get("capabilities", False):
            reasons.append("missing_capability_signal")
        if not fields.get("intent", False):
            reasons.append("missing_intent_signal")
        if not fields.get("available", False):
            reasons.append("missing_availability_signal")
        if not any(k in tags for k in ("blocked", "blocker")):
            reasons.append("missing_blocked_tag")
        elif not _is_clear_state(blocked_value):
            reasons.append("blocked_not_clear")
        if not any(k in tags for k in ("human_open_item", "human_open")):
            reasons.append("missing_human_open_item_tag")
        elif not _is_clear_state(human_open_value):
            reasons.append("human_open_item_requires_action")
        if _is_placeholder(next_step_value):
            if fields.get("next_step", False):
                next_step_value = "inferred_from_notes_or_status"
            else:
                reasons.append("missing_next_step_signal")

        lane_item: dict[str, Any] = {
            "lane": row.get("lane", ""),
            "session": row.get("session", ""),
            "status": row.get("status", ""),
            "domain": _scope_domain(row.get("scope_key", "")),
            "scope_key": row.get("scope_key", ""),
            "score": score,
            "explicit_score": explicit_score,
            "next_step": next_step_value,
            "explicit_missing_keys": explicit_missing,
        }
        if reasons:
            reason_set = sorted(set(reasons))
            lane_item["reasons"] = reason_set
            lane_item["blocked"] = blocked_value or None
            lane_item["human_open_item"] = human_open_value or None
            non_dispatchable_lanes.append(lane_item)
            for reason in reason_set:
                non_dispatchable_reason_counts[reason] = non_dispatchable_reason_counts.get(reason, 0) + 1
        else:
            dispatchable_lanes.append(lane_item)

    lane_count = len(active_rows)
    coverage = {key: round(key_counts[key] / lane_count, 4) if lane_count else 0.0 for key in REPORT_KEYS}
    explicit_coverage = {
        key: round(explicit_key_counts[key] / lane_count, 4) if lane_count else 0.0
        for key in REPORT_KEYS
    }
    deficit_rank = sorted(coverage.items(), key=lambda item: (item[1], item[0]))
    explicit_deficit_rank = sorted(explicit_coverage.items(), key=lambda item: (item[1], item[0]))
    reason_rank = sorted(non_dispatchable_reason_counts.items(), key=lambda item: (-item[1], item[0]))

    session_range = {
        "start": min(sessions) if sessions else None,
        "end": max(sessions) if sessions else None,
    }

    pickup_latency_ab = build_pickup_latency_ab(history_rows if history_rows is not None else active_rows)

    return {
        "lane_count": lane_count,
        "session_range": session_range,
        "mean_score": round(fmean(scores), 4) if scores else 0.0,
        "median_score": round(median(scores), 4) if scores else 0.0,
        "contract_ready_rate": round(contract_ready / lane_count, 4) if lane_count else 0.0,
        "explicit_mean_score": round(fmean(explicit_scores), 4) if explicit_scores else 0.0,
        "explicit_median_score": round(median(explicit_scores), 4) if explicit_scores else 0.0,
        "explicit_contract_ready_rate": (
            round(explicit_contract_ready / lane_count, 4) if lane_count else 0.0
        ),
        "key_coverage": coverage,
        "explicit_key_coverage": explicit_coverage,
        "lowest_coverage_keys": [name for name, _ in deficit_rank[:3]],
        "explicit_lowest_coverage_keys": [name for name, _ in explicit_deficit_rank[:3]],
        "recommended_contract": (
            "intent=... progress=... available=... blocked=none|... next_step=... "
            "human_open_item=none|HQ-N setup=... (plus model/platform columns)"
        ),
        "lanes": lane_rows,
        "pickup_latency_ab": pickup_latency_ab,
        "programmatic_swarm_plan": {
            "dispatch_contract": (
                "capability/intent/availability signals present + blocked=none + "
                "human_open_item=none + next_step signal"
            ),
            "dispatchable_count": len(dispatchable_lanes),
            "dispatchable_rate": round(len(dispatchable_lanes) / lane_count, 4) if lane_count else 0.0,
            "dispatchable_lanes": sorted(
                dispatchable_lanes,
                key=lambda item: (-item.get("explicit_score", 0.0), item.get("lane", "")),
            ),
            "non_dispatchable_count": len(non_dispatchable_lanes),
            "non_dispatchable_lanes": sorted(
                non_dispatchable_lanes,
                key=lambda item: (-item.get("explicit_score", 0.0), item.get("lane", "")),
            ),
            "top_non_dispatchable_reasons": [reason for reason, _ in reason_rank[:3]],
        },
    }


def run(lanes_path: Path, out_path: Path) -> dict[str, Any]:
    lanes_text = lanes_path.read_text(encoding="utf-8", errors="replace")
    rows = parse_lane_rows(lanes_text)
    active_rows = latest_active_lanes(rows)

    report = build_report(active_rows, history_rows=rows)
    swarm_plan = report["programmatic_swarm_plan"]
    pickup_latency = report["pickup_latency_ab"]
    pickup_mean_delta = pickup_latency["comparison"]["mean_delta_sessions_free_minus_schema"]
    if pickup_mean_delta is None:
        pickup_note = "Insufficient cohort history to compare schema-contract versus free-form pickup latency."
    elif pickup_mean_delta > 0:
        pickup_note = (
            f"Schema-contract rows are picked up faster by about {pickup_mean_delta} sessions on mean latency."
        )
    elif pickup_mean_delta < 0:
        pickup_note = (
            f"Free-form rows are currently picked up faster by about {abs(pickup_mean_delta)} sessions; "
            "contract adoption may be correlated with harder work."
        )
    else:
        pickup_note = "Schema-contract and free-form rows have identical mean pickup latency in this snapshot."
    result: dict[str, Any] = {
        "frontier_id": "F-STAT1",
        "title": "Agent reporting quality baseline for active lanes",
        "inputs": {
            "lanes_path": str(lanes_path).replace("\\", "/"),
            "active_statuses": sorted(ACTIVE_STATUSES),
            "report_keys": list(REPORT_KEYS),
            "weights": KEY_WEIGHTS,
        },
        "summary": {
            "active_lanes": report["lane_count"],
            "mean_score": report["mean_score"],
            "median_score": report["median_score"],
            "contract_ready_rate": report["contract_ready_rate"],
            "explicit_mean_score": report["explicit_mean_score"],
            "explicit_median_score": report["explicit_median_score"],
            "explicit_contract_ready_rate": report["explicit_contract_ready_rate"],
            "key_coverage": report["key_coverage"],
            "explicit_key_coverage": report["explicit_key_coverage"],
            "lowest_coverage_keys": report["lowest_coverage_keys"],
            "explicit_lowest_coverage_keys": report["explicit_lowest_coverage_keys"],
            "recommended_contract": report["recommended_contract"],
            "programmatic_swarmable_lanes": swarm_plan["dispatchable_count"],
            "programmatic_swarmable_rate": swarm_plan["dispatchable_rate"],
            "top_non_dispatchable_reasons": swarm_plan["top_non_dispatchable_reasons"],
            "pickup_latency_ab": pickup_latency,
        },
        "session_range": report["session_range"],
        "lanes": report["lanes"],
        "programmatic_swarm_plan": swarm_plan,
        "pickup_latency_ab": pickup_latency,
        "interpretation": {
            "score_band": (
                "strong" if report["mean_score"] >= 0.85 else
                "partial" if report["mean_score"] >= 0.60 else
                "weak"
            ),
            "explicit_score_band": (
                "strong" if report["explicit_mean_score"] >= 0.85 else
                "partial" if report["explicit_mean_score"] >= 0.60 else
                "weak"
            ),
            "note": (
                "Inferred score can be optimistic from notes/status alone; use explicit score as the promotion "
                "gate and auto-dispatch only lanes with blocked=none, human_open_item=none, and a next_step signal."
            ),
            "pickup_latency_note": pickup_note,
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
        default=Path("experiments/statistics/f-stat1-reporting-quality-s186.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(args.lanes, args.out)
    summary = result["summary"]
    print(f"Wrote {args.out}")
    print(
        "active_lanes=",
        summary["active_lanes"],
        "mean_score=",
        summary["mean_score"],
        "contract_ready_rate=",
        summary["contract_ready_rate"],
        "dispatchable_lanes=",
        summary["programmatic_swarmable_lanes"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
