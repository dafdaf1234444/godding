#!/usr/bin/env python3
"""Compare guarded vs unguarded F-OPS2 plans on realized lane signals.

This tool evaluates two scheduler artifacts against lane-history outcomes:
- pickup behavior (READY/CLAIMED -> ACTIVE/MERGED)
- blocked-lane churn
- collision/conflict keyword frequency
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ACTIVE_STATUSES = {"READY", "CLAIMED", "ACTIVE", "BLOCKED"}
PICKUP_START = {"READY", "CLAIMED"}
PICKUP_DONE = {"ACTIVE", "MERGED"}

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
        return path.read_text(encoding="utf-8", errors="replace")


def _parse_lane_rows(lanes_text: str) -> list[dict[str, str]]:
    keys = ("date", "lane", "session", "agent", "branch", "pr", "model", "platform", "scope", "etc", "status", "notes")
    rows: list[dict[str, str]] = []
    for raw in lanes_text.splitlines():
        line = raw.strip()
        if not line.startswith("|") or re.match(r"^\|\s*(Date\s*\||[-: ]+\|)", line, re.IGNORECASE):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 12:
            continue
        row = dict(zip(keys, parts))
        row["status"] = row["status"].upper()
        m = re.search(r"\bS(\d+)\b", row.get("session", ""))
        row["session_num"] = int(m.group(1)) if m else 0
        rows.append(row)
    return rows


def _parse_etc_fields(etc: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for part in re.split(r"[;,]", etc or ""):
        chunk = part.strip()
        if not chunk or "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        fields[key.strip().lower()] = value.strip().lower()
    return fields


def load_frontier_domain_map(domains_root: Path) -> dict[str, str]:
    frontier_to_domain: dict[str, str] = {}
    for domain_dir in sorted(domains_root.iterdir(), key=lambda p: p.name):
        if not domain_dir.is_dir():
            continue
        frontier_path = domain_dir / "tasks" / "FRONTIER.md"
        if not frontier_path.exists():
            continue
        text = _read(frontier_path)
        for fid in re.findall(r"\bF-[A-Z0-9]+\b", text):
            frontier_to_domain.setdefault(fid, domain_dir.name)
    return frontier_to_domain


def row_domain(row: dict[str, str], frontier_to_domain: dict[str, str]) -> str | None:
    scope = row.get("scope", "")
    m_scope = re.search(r"domains/([^/\s]+)/", scope)
    if m_scope:
        return m_scope.group(1)

    etc = row.get("etc", "")
    m_fid = re.search(r"frontier=(F-[A-Z0-9]+)", etc)
    if m_fid:
        return frontier_to_domain.get(m_fid.group(1))
    return None


def parse_plan_domains(payload: dict) -> set[str]:
    domains: set[str] = set()
    policy = str(payload.get("recommended_policy", ""))
    allocations = payload.get("policies", {}).get(policy, {}).get("allocations", {})
    for domain, slots in allocations.items():
        if int(slots) > 0:
            domains.add(domain)
    for row in payload.get("recommended_plan", []):
        domain = row.get("domain")
        if isinstance(domain, str) and domain:
            domains.add(domain)
    return domains


def compute_profile_metrics(
    rows: list[dict[str, str]],
    plan_domains: set[str],
    frontier_to_domain: dict[str, str],
    session_min: int,
) -> dict:
    filtered: list[dict[str, str]] = []
    for row in rows:
        if int(row.get("session_num", 0)) < session_min:
            continue
        domain = row_domain(row, frontier_to_domain)
        if domain is None or domain not in plan_domains:
            continue
        filtered.append(row)

    by_lane: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in filtered:
        lane = row.get("lane", "")
        if lane:
            by_lane[lane].append(row)

    pickup_candidates = 0
    pickup_success = 0
    blocked_entries = 0
    blocked_transitions = 0
    blocked_reason_churn = 0
    merged_lanes = 0
    open_lanes = 0
    collision_rows = 0

    collision_re = re.compile(r"\b(collision|conflict|contend|clash)\b", re.IGNORECASE)

    for lane_rows in by_lane.values():
        statuses = [r.get("status", "") for r in lane_rows]
        if any(s in PICKUP_START for s in statuses):
            pickup_candidates += 1
            start_ix = min(i for i, s in enumerate(statuses) if s in PICKUP_START)
            if any(s in PICKUP_DONE for s in statuses[start_ix + 1 :]):
                pickup_success += 1

        if any(s == "MERGED" for s in statuses):
            merged_lanes += 1
        if statuses and statuses[-1] in ACTIVE_STATUSES:
            open_lanes += 1

        blocked_reasons: list[str] = []
        prev = None
        for row in lane_rows:
            status = row.get("status", "")
            etc = row.get("etc", "")
            notes = row.get("notes", "")
            if collision_re.search(f"{etc} {notes}"):
                collision_rows += 1
            if status == "BLOCKED":
                blocked_entries += 1
                if prev != "BLOCKED":
                    blocked_transitions += 1
            prev = status
            fields = _parse_etc_fields(etc)
            reason = fields.get("blocked", "none")
            if reason != "none":
                blocked_reasons.append(reason)
        for i in range(1, len(blocked_reasons)):
            if blocked_reasons[i] != blocked_reasons[i - 1]:
                blocked_reason_churn += 1

    pickup_rate = (pickup_success / pickup_candidates) if pickup_candidates > 0 else 0.0
    blocked_transition_rate = (blocked_transitions / len(by_lane)) if by_lane else 0.0
    collision_rate = (collision_rows / len(filtered)) if filtered else 0.0
    open_lane_rate = (open_lanes / len(by_lane)) if by_lane else 0.0
    return {
        "domains": sorted(plan_domains),
        "session_min": session_min,
        "rows_observed": len(filtered),
        "lanes_observed": len(by_lane),
        "pickup_candidates": pickup_candidates,
        "pickup_success": pickup_success,
        "pickup_rate": round(pickup_rate, 4),
        "blocked_entries": blocked_entries,
        "blocked_transitions": blocked_transitions,
        "blocked_transition_rate_per_lane": round(blocked_transition_rate, 4),
        "blocked_reason_churn": blocked_reason_churn,
        "collision_keyword_rows": collision_rows,
        "collision_keyword_rate_per_row": round(collision_rate, 4),
        "merged_lanes": merged_lanes,
        "open_lanes": open_lanes,
        "open_lane_rate": round(open_lane_rate, 4),
    }


def compare_profiles(guarded: dict, unguarded: dict) -> dict:
    delta = {
        "pickup_rate": round(guarded["pickup_rate"] - unguarded["pickup_rate"], 4),
        "blocked_transition_rate_per_lane": round(
            guarded["blocked_transition_rate_per_lane"] - unguarded["blocked_transition_rate_per_lane"], 4
        ),
        "blocked_reason_churn": guarded["blocked_reason_churn"] - unguarded["blocked_reason_churn"],
        "collision_keyword_rate_per_row": round(
            guarded["collision_keyword_rate_per_row"] - unguarded["collision_keyword_rate_per_row"], 4
        ),
    }
    score = 0
    if delta["pickup_rate"] >= 0.0:
        score += 1
    if delta["blocked_transition_rate_per_lane"] <= 0.0:
        score += 1
    if delta["collision_keyword_rate_per_row"] <= 0.0:
        score += 1
    recommendation = "guarded" if score >= 2 else "unguarded"
    return {
        "delta_guarded_minus_unguarded": delta,
        "recommendation": recommendation,
        "recommendation_score": score,
        "rule": "Prefer guarded when pickup does not regress and normalized blocking/collision rates do not worsen.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--guarded",
        type=Path,
        default=Path("experiments/operations-research/f-ops2-domain-priority-automability-floor50-live-s186.json"),
    )
    parser.add_argument(
        "--unguarded",
        type=Path,
        default=Path("experiments/operations-research/f-ops2-domain-priority-automability-live-unguarded-s186.json"),
    )
    parser.add_argument("--lanes", type=Path, default=Path("tasks/SWARM-LANES.md"))
    parser.add_argument("--domains-root", type=Path, default=Path("domains"))
    parser.add_argument(
        "--session-min",
        type=int,
        default=0,
        help="Minimum session number for lane rows (default uses min of guarded/unguarded session).",
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    guarded_payload = json.loads(_read(args.guarded))
    unguarded_payload = json.loads(_read(args.unguarded))
    rows = _parse_lane_rows(_read(args.lanes))
    frontier_to_domain = load_frontier_domain_map(args.domains_root)

    guarded_domains = parse_plan_domains(guarded_payload)
    unguarded_domains = parse_plan_domains(unguarded_payload)
    session_min = args.session_min or min(int(guarded_payload.get("session", 0)), int(unguarded_payload.get("session", 0)))

    guarded_metrics = compute_profile_metrics(rows, guarded_domains, frontier_to_domain, session_min)
    unguarded_metrics = compute_profile_metrics(rows, unguarded_domains, frontier_to_domain, session_min)
    comparison = compare_profiles(guarded_metrics, unguarded_metrics)

    out_payload = {
        "frontier_id": "F-OPS2",
        "title": "Guarded vs unguarded live-dispatch comparison",
        "inputs": {
            "guarded_artifact": str(args.guarded),
            "unguarded_artifact": str(args.unguarded),
            "lanes_path": str(args.lanes),
            "domains_root": str(args.domains_root),
            "session_min": session_min,
        },
        "profiles": {
            "guarded": guarded_metrics,
            "unguarded": unguarded_metrics,
        },
        "comparison": comparison,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out_payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(
        "comparison="
        f"{comparison['recommendation']} "
        f"pickup_delta={comparison['delta_guarded_minus_unguarded']['pickup_rate']:.4f} "
        f"blocked_rate_delta={comparison['delta_guarded_minus_unguarded']['blocked_transition_rate_per_lane']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
