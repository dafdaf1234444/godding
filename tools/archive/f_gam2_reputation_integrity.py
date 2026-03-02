#!/usr/bin/env python3
"""F-GAM2: evaluate reputation signaling and integrity pressure in swarm lanes.

This tool measures whether explicit lane reputation tags (`reliability`,
`evidence_quality`) correlate with better coordination outcomes, and generates
swarm-to-swarm challenge questions from the weakest integrity signals.
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
REPUTATION_KEYS = ("reliability", "evidence_quality")
CONTRACT_KEYS = ("setup", "focus", "available", "blocked", "next_step", "human_open_item")
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

SESSION_RE = re.compile(r"\bS(\d+)\b", re.IGNORECASE)
TAG_RE = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)")
CONFLICT_RE = re.compile(r"\b(block(?:ed|er)?|conflict|collision|contention|stale|waiting?)\b", re.IGNORECASE)


def _parse_session(raw: str) -> int | None:
    m = SESSION_RE.search(raw or "")
    return int(m.group(1)) if m else None


def _parse_tags(text: str) -> dict[str, str]:
    return {k.strip().lower(): v.strip() for k, v in TAG_RE.findall(text or "")}


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


def has_reputation_signal(
    row: dict[str, str],
    required_keys: tuple[str, ...] = REPUTATION_KEYS,
) -> bool:
    tags = _parse_tags(row.get("etc", ""))
    return all(key in tags for key in required_keys)


def has_contract(
    row: dict[str, str],
    required_keys: tuple[str, ...] = CONTRACT_KEYS,
) -> bool:
    tags = _parse_tags(row.get("etc", ""))
    return all(key in tags for key in required_keys)


def _mean(values: list[float]) -> float:
    return round(fmean(values), 4) if values else 0.0


def _median(values: list[float]) -> float:
    return round(float(median(values)), 4) if values else 0.0


def _first_handoff_lag(seq: list[dict[str, str]]) -> int | None:
    start_idx = None
    start_session = None
    for i, row in enumerate(seq):
        if row.get("status") in {"READY", "CLAIMED"}:
            start_idx = i
            start_session = _parse_session(row.get("session", ""))
            break
    if start_idx is None or start_session is None:
        return None

    for row in seq[start_idx + 1:]:
        if row.get("status") in {"ACTIVE", "BLOCKED", "MERGED", "ABANDONED"}:
            pickup_session = _parse_session(row.get("session", ""))
            if pickup_session is not None and pickup_session >= start_session:
                return pickup_session - start_session
    return None


def _priority_score(row: dict[str, Any], *, max_session: int) -> float:
    latest_status = str(row.get("latest_status", ""))
    latest_session = row.get("latest_session")
    staleness = float(max(0, max_session - int(latest_session))) if latest_session is not None else 0.0
    blocked_bonus = 2.0 if latest_status == "BLOCKED" else 0.0
    conflict_bonus = min(3.0, float(row.get("conflict_events", 0)))
    human_open_bonus = 1.0 if bool(row.get("human_open_item_active", False)) else 0.0
    return round(blocked_bonus + conflict_bonus + human_open_bonus + 0.1 * staleness, 4)


def build_ab_assignment_plan(
    lane_rows: list[dict[str, Any]],
    *,
    max_session: int,
    min_per_cohort: int = 3,
) -> dict[str, Any]:
    active_rows = [row for row in lane_rows if row.get("latest_status") in ACTIVE_STATUSES]
    active_count = len(active_rows)
    tagged_active = [row for row in active_rows if bool(row.get("reputation_signal", False))]
    untagged_active = [row for row in active_rows if not bool(row.get("reputation_signal", False))]

    if active_count <= 1:
        return {
            "min_per_cohort": int(min_per_cohort),
            "target_per_cohort": 0,
            "active_lane_count": active_count,
            "active_tagged_count": len(tagged_active),
            "active_untagged_count": len(untagged_active),
            "additional_tagged_needed": 0,
            "feasible_for_ab": False,
            "reason": "Need at least two active lanes for tagged vs untagged A/B assignment.",
            "recommended_tagged_lanes": [],
            "holdout_untagged_lanes": [],
            "tagging_template": "reliability=provisional evidence_quality=draft",
        }

    target = min(int(min_per_cohort), active_count // 2) if active_count >= 2 else 0
    additional_tagged_needed = max(0, target - len(tagged_active))

    ranked_untagged = sorted(
        untagged_active,
        key=lambda item: (
            -_priority_score(item, max_session=max_session),
            item.get("lane", ""),
        ),
    )
    to_tag = ranked_untagged[:additional_tagged_needed]
    holdout_needed = max(0, target - len(tagged_active))
    holdout_pool = [row for row in ranked_untagged if row not in to_tag]
    holdout = holdout_pool[:holdout_needed]

    projected_tagged = len(tagged_active) + len(to_tag)
    projected_untagged = len(untagged_active) - len(to_tag)

    def _lane_stub(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "lane": row.get("lane"),
            "latest_status": row.get("latest_status"),
            "latest_session": row.get("latest_session"),
            "priority_score": _priority_score(row, max_session=max_session),
            "suggested_tags": "reliability=provisional evidence_quality=draft",
        }

    return {
        "min_per_cohort": int(min_per_cohort),
        "target_per_cohort": int(target),
        "active_lane_count": active_count,
        "active_tagged_count": len(tagged_active),
        "active_untagged_count": len(untagged_active),
        "additional_tagged_needed": int(additional_tagged_needed),
        "feasible_for_ab": bool(target > 0),
        "reason": (
            "Active-lane cohort too small to satisfy 3v3 target; using best-effort balanced split."
            if target < int(min_per_cohort)
            else "3v3 target feasible on current active lanes."
        ),
        "projected_after_assignment": {
            "tagged_count": projected_tagged,
            "untagged_count": projected_untagged,
            "balanced_for_target": projected_tagged >= target and projected_untagged >= target,
        },
        "recommended_tagged_lanes": [_lane_stub(row) for row in to_tag],
        "holdout_untagged_lanes": [_lane_stub(row) for row in holdout],
        "tagging_template": "reliability=provisional evidence_quality=draft",
        "execution_rule": (
            "Before next lane update, add `reliability` and `evidence_quality` on recommended lanes; "
            "keep holdout lanes untagged for one session to preserve A/B identifiability."
        ),
    }


def summarize_group(items: list[dict[str, Any]], *, max_session: int) -> dict[str, Any]:
    closure_lags = [float(x["closure_lag"]) for x in items if x["closure_lag"] is not None]
    handoff_lags = [float(x["handoff_lag"]) for x in items if x["handoff_lag"] is not None]
    updates = [float(x["update_count"]) for x in items]
    conflict_lanes = [x for x in items if int(x["conflict_events"]) > 0]
    active_items = [x for x in items if x["latest_status"] in ACTIVE_STATUSES and x["latest_session"] is not None]
    stale = [x for x in active_items if (max_session - int(x["latest_session"])) > 1]

    return {
        "lane_count": len(items),
        "closed_lane_count": len(closure_lags),
        "mean_closure_lag_sessions": _mean(closure_lags),
        "median_closure_lag_sessions": _median(closure_lags),
        "mean_handoff_lag_sessions": _mean(handoff_lags),
        "median_handoff_lag_sessions": _median(handoff_lags),
        "mean_updates_per_lane": _mean(updates),
        "conflict_lane_rate": round(len(conflict_lanes) / len(items), 4) if items else 0.0,
        "stale_active_rate": round(len(stale) / len(active_items), 4) if active_items else 0.0,
    }


def analyze(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_lane: dict[str, list[dict[str, str]]] = defaultdict(list)
    sessions: list[int] = []
    for row in rows:
        lane = row.get("lane", "").strip()
        if not lane:
            continue
        by_lane[lane].append(row)
        session = _parse_session(row.get("session", ""))
        if session is not None:
            sessions.append(session)

    max_session = max(sessions) if sessions else 0
    lane_rows: list[dict[str, Any]] = []

    for lane, seq in by_lane.items():
        first_active = None
        first_closed = None
        reputation_seen_on_active = False
        contract_seen_on_active = False
        human_open_item_active = False
        conflict_events = 0

        for row in seq:
            status = row.get("status", "")
            if first_active is None and status in ACTIVE_STATUSES:
                first_active = row
            if first_closed is None and status in CLOSED_STATUSES:
                first_closed = row
            if status in ACTIVE_STATUSES and has_reputation_signal(row):
                reputation_seen_on_active = True
            if status in ACTIVE_STATUSES and has_contract(row):
                contract_seen_on_active = True
            if status in ACTIVE_STATUSES:
                tags = _parse_tags(row.get("etc", ""))
                human_item = tags.get("human_open_item", "none").strip().lower()
                if human_item not in {"", "none", "none_recorded"}:
                    human_open_item_active = True

            if status == "BLOCKED" or CONFLICT_RE.search(f"{row.get('etc', '')} {row.get('notes', '')}"):
                conflict_events += 1

        latest = seq[-1]
        active_session = _parse_session((first_active or {}).get("session", ""))
        closed_session = _parse_session((first_closed or {}).get("session", ""))
        latest_session = _parse_session(latest.get("session", ""))
        handoff_lag = _first_handoff_lag(seq)

        closure_lag = None
        if active_session is not None and closed_session is not None and closed_session >= active_session:
            closure_lag = closed_session - active_session

        lane_rows.append(
            {
                "lane": lane,
                "reputation_signal": reputation_seen_on_active,
                "contract_explicit": contract_seen_on_active,
                "human_open_item_active": human_open_item_active,
                "conflict_events": conflict_events,
                "first_active_session": active_session,
                "first_closed_session": closed_session,
                "closure_lag": closure_lag,
                "handoff_lag": handoff_lag,
                "update_count": len(seq),
                "latest_status": latest.get("status"),
                "latest_session": latest_session,
            }
        )

    tagged = [row for row in lane_rows if row["reputation_signal"]]
    untagged = [row for row in lane_rows if not row["reputation_signal"]]

    tagged_summary = summarize_group(tagged, max_session=max_session)
    untagged_summary = summarize_group(untagged, max_session=max_session)

    def _delta(key: str) -> float:
        return round(float(tagged_summary.get(key, 0.0)) - float(untagged_summary.get(key, 0.0)), 4)

    active_lanes = [row for row in lane_rows if row["latest_status"] in ACTIVE_STATUSES]
    active_count = len(active_lanes)
    contract_rate = (
        round(sum(1 for row in active_lanes if row["contract_explicit"]) / active_count, 4)
        if active_count
        else 0.0
    )
    reputation_rate = (
        round(sum(1 for row in active_lanes if row["reputation_signal"]) / active_count, 4)
        if active_count
        else 0.0
    )
    blocked_rate = (
        round(sum(1 for row in active_lanes if row["latest_status"] == "BLOCKED") / active_count, 4)
        if active_count
        else 0.0
    )
    stale_rate = (
        round(
            sum(
                1
                for row in active_lanes
                if row["latest_session"] is not None and (max_session - int(row["latest_session"])) > 1
            )
            / active_count,
            4,
        )
        if active_count
        else 0.0
    )
    human_open_rate = (
        round(sum(1 for row in active_lanes if row["human_open_item_active"]) / active_count, 4)
        if active_count
        else 0.0
    )

    integrity_score = round(
        (0.35 * contract_rate)
        + (0.25 * (1.0 - stale_rate))
        + (0.20 * (1.0 - blocked_rate))
        + (0.10 * (1.0 - human_open_rate))
        + (0.10 * reputation_rate),
        4,
    )
    integrity_band = "STRONG" if integrity_score >= 0.8 else "WATCH" if integrity_score >= 0.6 else "FRAGILE"

    integrity_summary = {
        "lane_count_total": len(lane_rows),
        "active_lane_count": active_count,
        "contract_rate_active": contract_rate,
        "reputation_signal_rate_active": reputation_rate,
        "blocked_active_rate": blocked_rate,
        "stale_active_rate": stale_rate,
        "human_open_item_rate_active": human_open_rate,
        "integrity_score": integrity_score,
        "integrity_band": integrity_band,
    }
    assignment_plan = build_ab_assignment_plan(lane_rows, max_session=max_session, min_per_cohort=3)

    return {
        "max_session": max_session,
        "lane_count_total": len(lane_rows),
        "integrity_summary": integrity_summary,
        "ab_assignment_plan": assignment_plan,
        "reputation_group": tagged_summary,
        "untagged_group": untagged_summary,
        "deltas_reputation_minus_untagged": {
            "mean_closure_lag_sessions": _delta("mean_closure_lag_sessions"),
            "mean_handoff_lag_sessions": _delta("mean_handoff_lag_sessions"),
            "mean_updates_per_lane": _delta("mean_updates_per_lane"),
            "conflict_lane_rate": _delta("conflict_lane_rate"),
            "stale_active_rate": _delta("stale_active_rate"),
        },
        "lane_samples": lane_rows[:50],
    }


def build_challenge_questions(
    integrity_summary: dict[str, Any],
    reputation_group: dict[str, Any],
    untagged_group: dict[str, Any],
) -> list[dict[str, str]]:
    prompts: list[tuple[str, str]] = []

    reputation_rate = float(integrity_summary.get("reputation_signal_rate_active", 0.0))
    contract_rate = float(integrity_summary.get("contract_rate_active", 0.0))
    stale_rate = float(integrity_summary.get("stale_active_rate", 0.0))
    blocked_rate = float(integrity_summary.get("blocked_active_rate", 0.0))
    integrity_score = float(integrity_summary.get("integrity_score", 0.0))
    tagged_count = int(reputation_group.get("lane_count", 0))

    if reputation_rate < 0.3:
        prompts.append(
            (
                "What minimum `reliability`+`evidence_quality` schema can every active lane publish next session?",
                "Low active-lane reputation coverage",
            )
        )
    if contract_rate < 0.8:
        prompts.append(
            (
                "Which contract key is most often missing at handoff time, and who owns automatic correction?",
                "Contract coverage below coordination target",
            )
        )
    if stale_rate > 0.15:
        prompts.append(
            (
                "Which stale lanes should be force-closed versus reassigned to restore flow within one session?",
                "Stale active-lane pressure",
            )
        )
    if blocked_rate > 0.2:
        prompts.append(
            (
                "Are blockers mostly dependency waits or signaling failures, and what single protocol change would remove both?",
                "High blocked-active rate",
            )
        )
    if (
        tagged_count > 0
        and int(untagged_group.get("lane_count", 0)) > 0
        and float(reputation_group.get("mean_handoff_lag_sessions", 0.0))
        >= float(untagged_group.get("mean_handoff_lag_sessions", 0.0))
    ):
        prompts.append(
            (
                "Why are tagged lanes not faster at pickup, and are tags being added only after trouble begins?",
                "Tagged cohort does not improve handoff latency",
            )
        )
    if (
        tagged_count > 0
        and int(untagged_group.get("lane_count", 0)) > 0
        and float(reputation_group.get("conflict_lane_rate", 0.0))
        >= float(untagged_group.get("conflict_lane_rate", 0.0))
    ):
        prompts.append(
            (
                "Are reputation tags predictive or merely reactive, and what pre-lane signal would make them anticipatory?",
                "Tagged cohort conflict rate not lower",
            )
        )
    if tagged_count < 3:
        prompts.append(
            (
                "What A/B assignment rule guarantees at least 3 tagged and 3 untagged lanes per run for estimable comparisons?",
                "Tagged sample too small for stable inference",
            )
        )
    if integrity_score < 0.8:
        prompts.append(
            (
                "What single integrity intervention gives the largest expected score gain next session: contract enforcement, stale-lane pruning, or blocker triage?",
                "Overall integrity score below strong band",
            )
        )

    if tagged_count == 0:
        prompts.append(
            (
                "Should reputation tags be required on lane claim rather than optional on updates, to avoid zero-cohort blind spots?",
                "No tagged cohort exists in current history",
            )
        )

    fallback_prompts = [
        (
            "Which inter-swarm failure mode would we miss if we only monitor merge success but not handoff lag and conflict events?",
            "Baseline adversarial probing",
        ),
        (
            "What evidence would falsify the claim that current contract discipline is sufficient for cross-swarm pickup quality?",
            "Need explicit falsification target",
        ),
        (
            "If one swarm withholds uncertainty tags for one session, how quickly can sibling swarms detect and correct the integrity loss?",
            "Stress test for uncertainty propagation",
        ),
        (
            "Which metric should trigger automatic bulletin escalation first: stale lag, blocker density, or unresolved human open items?",
            "Escalation policy ambiguity",
        ),
    ]
    for question, trigger in fallback_prompts:
        if len(prompts) >= 5:
            break
        prompts.append((question, trigger))

    questions: list[dict[str, str]] = []
    for i, (question, trigger) in enumerate(prompts[:8], start=1):
        questions.append({"id": f"Q{i}", "question": question, "trigger": trigger})
    return questions


def run(lanes_path: Path, out_path: Path) -> dict[str, Any]:
    rows = parse_rows(lanes_path.read_text(encoding="utf-8", errors="replace"))
    analysis = analyze(rows)
    integrity = analysis["integrity_summary"]
    questions = build_challenge_questions(
        integrity_summary=integrity,
        reputation_group=analysis["reputation_group"],
        untagged_group=analysis["untagged_group"],
    )

    result = {
        "frontier_id": "F-GAM2",
        "title": "Reputation signaling and swarm integrity pressure-test",
        "input": str(lanes_path).replace("\\", "/"),
        "reputation_required_keys": list(REPUTATION_KEYS),
        "contract_required_keys": list(CONTRACT_KEYS),
        "analysis": analysis,
        "swarm_to_swarm_challenge_questions": questions,
        "interpretation": {
            "note": "Lower lag/conflict/staleness is better.",
            "caveat": (
                "Observational lane-history analysis; tagged lanes may be selected into harder coordination work."
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
        default=Path("experiments/game-theory/f-gam2-reputation-signals-s186.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(args.lanes, args.out)
    summary = result["analysis"]["integrity_summary"]
    print(f"Wrote {args.out}")
    print(
        "integrity_score=",
        summary["integrity_score"],
        "band=",
        summary["integrity_band"],
        "active_lanes=",
        summary["active_lane_count"],
        "reputation_rate_active=",
        summary["reputation_signal_rate_active"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
