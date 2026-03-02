#!/usr/bin/env python3
"""F-EVO4: evaluate multi-branch evolution swarmability from lane history.

This tool measures whether multi-branch execution is swarmable at three levels:
1) within-agent (single agent handling multiple branches),
2) within-swarm (concurrent lane coordination across branches),
3) overall swarm (history-level closure/retention quality under branch diversity).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any


ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
CLOSED_STATUSES = {"MERGED", "ABANDONED"}
BRANCH_PLACEHOLDERS = {"", "-", "n/a", "na", "none", "pending", "unknown"}
BASELINE_BRANCH_NAMES = {"local", "master", "main", "trunk", "default"}
CONTRACT_KEYS = ("available", "blocked", "next_step", "human_open_item")
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


def _is_placeholder_branch(branch: str) -> bool:
    return (branch or "").strip().lower() in BRANCH_PLACEHOLDERS


def _is_explicit_branch(branch: str) -> bool:
    low = (branch or "").strip().lower()
    return bool(low) and low not in BRANCH_PLACEHOLDERS and low not in BASELINE_BRANCH_NAMES


def _has_contract(etc: str) -> bool:
    tags = _parse_tags(etc)
    return all(key in tags for key in CONTRACT_KEYS)


def _collision_signal(etc: str, notes: str) -> bool:
    low = f"{etc} {notes}".lower()
    return any(term in low for term in ("collision", "conflict", "contention", "merge-friction"))


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def parse_rows(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
        row["session_num"] = _parse_session(row.get("session", ""))
        rows.append(row)
    return rows


def _lane_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_lane: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        lane = row.get("lane", "").strip()
        if lane:
            by_lane[lane].append(row)

    summary: dict[str, dict[str, Any]] = {}
    for lane, seq in by_lane.items():
        non_placeholder = sorted(
            {
                (row.get("branch", "") or "").strip().lower()
                for row in seq
                if not _is_placeholder_branch(row.get("branch", ""))
            }
        )
        explicit = sorted(
            {
                (row.get("branch", "") or "").strip().lower()
                for row in seq
                if _is_explicit_branch(row.get("branch", ""))
            }
        )
        statuses = [row.get("status", "") for row in seq]
        latest = seq[-1]
        summary[lane] = {
            "lane": lane,
            "row_count": len(seq),
            "branches_non_placeholder": non_placeholder,
            "branches_explicit": explicit,
            "merged": "MERGED" in statuses,
            "abandoned": "ABANDONED" in statuses,
            "closed": any(s in CLOSED_STATUSES for s in statuses),
            "latest_status": latest.get("status", ""),
            "latest_session": latest.get("session_num"),
            "collision_events": sum(1 for row in seq if _collision_signal(row.get("etc", ""), row.get("notes", ""))),
            "active_contract_seen": any(
                row.get("status", "") in ACTIVE_STATUSES and _has_contract(row.get("etc", "")) for row in seq
            ),
        }
    return summary


def _score_within_agent(
    rows: list[dict[str, Any]],
    lane_summary: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    by_agent_session: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        session_num = row.get("session_num")
        if session_num is None:
            continue
        agent = (row.get("agent", "") or "").strip() or "unknown"
        key = (agent, session_num)
        slot = by_agent_session.setdefault(
            key,
            {"agent": agent, "session": session_num, "lanes": set(), "branches": set(), "explicit_branches": set()},
        )
        lane = (row.get("lane", "") or "").strip()
        if lane:
            slot["lanes"].add(lane)
        branch = (row.get("branch", "") or "").strip().lower()
        if not _is_placeholder_branch(branch):
            slot["branches"].add(branch)
        if _is_explicit_branch(branch):
            slot["explicit_branches"].add(branch)

    samples: list[dict[str, Any]] = []
    multi_branch_flags = []
    branch_counts = []
    close_rates = []
    explicit_counts = []

    for entry in by_agent_session.values():
        lane_ids = sorted(entry["lanes"])
        branch_count = len(entry["branches"])
        explicit_count = len(entry["explicit_branches"])
        lanes_closed = sum(1 for lane in lane_ids if lane_summary.get(lane, {}).get("closed"))
        close_rate = (lanes_closed / len(lane_ids)) if lane_ids else 0.0
        is_multi_branch = branch_count >= 2

        branch_counts.append(branch_count)
        explicit_counts.append(explicit_count)
        close_rates.append(close_rate)
        multi_branch_flags.append(1.0 if is_multi_branch else 0.0)

        samples.append(
            {
                "agent": entry["agent"],
                "session": f"S{entry['session']}",
                "lane_count": len(lane_ids),
                "branch_count": branch_count,
                "explicit_branch_count": explicit_count,
                "lane_close_rate": round(close_rate, 4),
                "is_multi_branch": is_multi_branch,
            }
        )

    multi_branch_rate = fmean(multi_branch_flags) if multi_branch_flags else 0.0
    mean_branch_count = fmean(branch_counts) if branch_counts else 0.0
    mean_close_rate = fmean(close_rates) if close_rates else 0.0
    mean_explicit_branches = fmean(explicit_counts) if explicit_counts else 0.0

    score = fmean(
        [
            _clamp(multi_branch_rate / 0.5),
            _clamp(mean_branch_count / 2.0),
            _clamp(mean_close_rate),
            _clamp(mean_explicit_branches / 1.0),
        ]
    )
    swarmable = score >= 0.6

    return {
        "swarmable": swarmable,
        "score": round(score, 4),
        "threshold": 0.6,
        "metrics": {
            "agent_session_count": len(samples),
            "multi_branch_agent_session_rate": round(multi_branch_rate, 4),
            "mean_branch_count_per_agent_session": round(mean_branch_count, 4),
            "mean_explicit_branch_count_per_agent_session": round(mean_explicit_branches, 4),
            "mean_lane_close_rate": round(mean_close_rate, 4),
        },
        "samples": sorted(samples, key=lambda row: (row["session"], row["agent"]))[:40],
    }


def _score_within_swarm(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_session: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"active_lanes": set(), "active_branches": set(), "active_explicit_branches": set(), "active_rows": 0, "active_contract_rows": 0, "collision_rows": 0}
    )
    for row in rows:
        session_num = row.get("session_num")
        if session_num is None:
            continue
        slot = by_session[session_num]
        if _collision_signal(row.get("etc", ""), row.get("notes", "")):
            slot["collision_rows"] += 1
        if row.get("status", "") in ACTIVE_STATUSES:
            slot["active_rows"] += 1
            if _has_contract(row.get("etc", "")):
                slot["active_contract_rows"] += 1
            lane = (row.get("lane", "") or "").strip()
            if lane:
                slot["active_lanes"].add(lane)
            branch = (row.get("branch", "") or "").strip().lower()
            if not _is_placeholder_branch(branch):
                slot["active_branches"].add(branch)
            if _is_explicit_branch(branch):
                slot["active_explicit_branches"].add(branch)

    session_samples: list[dict[str, Any]] = []
    diversity_values = []
    explicit_diversity_values = []
    contract_values = []
    for session_num in sorted(by_session):
        slot = by_session[session_num]
        active_lane_count = len(slot["active_lanes"])
        active_branch_count = len(slot["active_branches"])
        active_explicit_count = len(slot["active_explicit_branches"])
        diversity = (active_branch_count / active_lane_count) if active_lane_count else 0.0
        explicit_diversity = (active_explicit_count / active_lane_count) if active_lane_count else 0.0
        contract_rate = (slot["active_contract_rows"] / slot["active_rows"]) if slot["active_rows"] else 0.0

        diversity_values.append(diversity)
        explicit_diversity_values.append(explicit_diversity)
        contract_values.append(contract_rate)
        session_samples.append(
            {
                "session": f"S{session_num}",
                "active_lane_count": active_lane_count,
                "active_branch_count": active_branch_count,
                "active_explicit_branch_count": active_explicit_count,
                "active_branch_diversity": round(diversity, 4),
                "active_explicit_branch_diversity": round(explicit_diversity, 4),
                "active_contract_rate": round(contract_rate, 4),
                "collision_rows": slot["collision_rows"],
            }
        )

    mean_diversity = fmean(diversity_values) if diversity_values else 0.0
    mean_explicit_diversity = fmean(explicit_diversity_values) if explicit_diversity_values else 0.0
    mean_contract_rate = fmean(contract_values) if contract_values else 0.0
    collision_row_rate = (
        sum(slot["collision_rows"] for slot in by_session.values()) / max(1, len(rows))
        if rows
        else 0.0
    )

    score = fmean(
        [
            _clamp(mean_diversity / 0.6),
            _clamp(mean_explicit_diversity / 0.3),
            _clamp(mean_contract_rate / 0.8),
            _clamp(1.0 - (collision_row_rate / 0.2)),
        ]
    )
    swarmable = score >= 0.65

    return {
        "swarmable": swarmable,
        "score": round(score, 4),
        "threshold": 0.65,
        "metrics": {
            "session_count": len(session_samples),
            "mean_active_branch_diversity": round(mean_diversity, 4),
            "mean_active_explicit_branch_diversity": round(mean_explicit_diversity, 4),
            "mean_active_contract_rate": round(mean_contract_rate, 4),
            "collision_row_rate": round(collision_row_rate, 4),
        },
        "samples": session_samples[-30:],
    }


def _branch_concentration(lane_summary: dict[str, dict[str, Any]]) -> tuple[float, float]:
    branch_lane_counts: Counter[str] = Counter()
    for lane in lane_summary.values():
        for branch in lane.get("branches_non_placeholder", []):
            branch_lane_counts[branch] += 1
    total = sum(branch_lane_counts.values())
    if total <= 0:
        return 1.0, 1.0
    shares = [count / total for count in branch_lane_counts.values()]
    hhi = sum(share * share for share in shares)
    effective = (1.0 / hhi) if hhi > 0 else 0.0
    return hhi, effective


def _score_overall(rows: list[dict[str, Any]], lane_summary: dict[str, dict[str, Any]]) -> dict[str, Any]:
    lane_items = list(lane_summary.values())
    lane_count = len(lane_items)
    merged_rate = (sum(1 for lane in lane_items if lane["merged"]) / lane_count) if lane_count else 0.0
    explicit_lane_rate = (
        sum(1 for lane in lane_items if lane["branches_explicit"]) / lane_count
    ) if lane_count else 0.0
    active_residue_rate = (
        sum(1 for lane in lane_items if lane["latest_status"] in ACTIVE_STATUSES) / lane_count
    ) if lane_count else 0.0
    multi_branch_lane_rate = (
        sum(1 for lane in lane_items if len(lane["branches_non_placeholder"]) >= 2) / lane_count
    ) if lane_count else 0.0
    hhi, effective = _branch_concentration(lane_summary)

    top_branches = Counter()
    for lane in lane_items:
        for branch in lane["branches_non_placeholder"]:
            top_branches[branch] += 1

    score = fmean(
        [
            _clamp(merged_rate / 0.75),
            _clamp(explicit_lane_rate / 0.1),
            _clamp(1.0 - (active_residue_rate / 0.25)),
            _clamp(multi_branch_lane_rate / 0.1),
            _clamp((effective - 1.0) / 2.0),
        ]
    )
    swarmable = score >= 0.65

    return {
        "swarmable": swarmable,
        "score": round(score, 4),
        "threshold": 0.65,
        "metrics": {
            "row_count": len(rows),
            "lane_count": lane_count,
            "merged_lane_rate": round(merged_rate, 4),
            "explicit_branch_lane_rate": round(explicit_lane_rate, 4),
            "active_residue_rate": round(active_residue_rate, 4),
            "multi_branch_lane_rate": round(multi_branch_lane_rate, 4),
            "branch_concentration_hhi": round(hhi, 4),
            "effective_branch_count": round(effective, 4),
            "top_branches_by_lane_count": top_branches.most_common(10),
        },
    }


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    lane_summary = _lane_summary(rows)
    by_level = {
        "within_agent": _score_within_agent(rows, lane_summary),
        "within_swarm": _score_within_swarm(rows),
        "overall_swarm": _score_overall(rows, lane_summary),
    }
    passed = sum(1 for result in by_level.values() if result["swarmable"])
    overall_swarmable = passed >= 2
    session_numbers = [row["session_num"] for row in rows if row.get("session_num") is not None]

    return {
        "max_session": max(session_numbers) if session_numbers else 0,
        "overall_multibranch_swarmable": overall_swarmable,
        "verdict_strength": round(passed / 3.0, 4),
        "level_verdicts": by_level,
        "lane_snapshot": {
            "total_lanes": len(lane_summary),
            "active_lanes": sum(1 for lane in lane_summary.values() if lane["latest_status"] in ACTIVE_STATUSES),
            "closed_lanes": sum(1 for lane in lane_summary.values() if lane["closed"]),
            "lanes_with_explicit_branch": sum(1 for lane in lane_summary.values() if lane["branches_explicit"]),
            "lanes_with_multi_branch_history": sum(
                1 for lane in lane_summary.values() if len(lane["branches_non_placeholder"]) >= 2
            ),
        },
    }


def run(lanes_path: Path, out_path: Path) -> dict[str, Any]:
    rows = parse_rows(lanes_path.read_text(encoding="utf-8", errors="replace"))
    analysis = analyze(rows)
    session_label = f"S{analysis['max_session']}" if analysis["max_session"] else "unknown"
    result = {
        "frontier_id": "F-EVO4",
        "title": "Multi-branch evolution swarmability baseline",
        "session": session_label,
        "source": str(lanes_path).replace("\\", "/"),
        "analysis": analysis,
        "interpretation": {
            "question": "Is multi-branch evolution swarmable within agents, within swarms, and overall?",
            "answer": (
                "YES" if analysis["overall_multibranch_swarmable"] else "PARTIAL/NO"
            ),
            "note": (
                "Scores are observational and proxy-based. Use for lane-policy calibration, "
                "not as causal proof."
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
    parser.add_argument("--out", type=Path, default=Path("experiments/evolution/f-evo4-multibranch-s186.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(args.lanes, args.out)
    analysis = result["analysis"]
    print(f"Wrote {args.out}")
    print(
        "overall_multibranch_swarmable=",
        analysis["overall_multibranch_swarmable"],
        "verdict_strength=",
        analysis["verdict_strength"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
