#!/usr/bin/env python3
"""f_ops2_domain_priority.py - prioritize domain work and allocate agent slots.

This tool operationalizes F-OPS2 by turning current swarm state into a
domain-priority schedule that can be swarmed directly.

Inputs:
- domain frontier files (active frontier load + recency)
- tasks/NEXT.md ("For next session" + "What just happened" finding signal)
- tasks/SWARM-LANES.md (active lane pressure / collision risk)

Output:
- policy-by-policy ranking and slot allocation
- recommended policy and per-slot domain plan

Usage:
  python3 tools/f_ops2_domain_priority.py
  python3 tools/f_ops2_domain_priority.py --agent-count 4 --json-out experiments/operations-research/f-ops2-domain-priority-s186.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ACTIVE_LANE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
DISPATCHABLE_LANE_STATUSES = {"CLAIMED", "ACTIVE", "READY"}
POLICIES = ("fifo", "risk_first", "value_density", "hybrid")
DOMAIN_KNOWLEDGE_RULES: tuple[tuple[str, tuple[tuple[str, float], ...]], ...] = (
    (
        "meta",
        (
            (r"\bgenesis\b", 1.0),
            (r"\bkolmogorov\b", 1.2),
            (r"\bminimal viable\b", 0.8),
            (r"\bgenesis\.sh\b", 0.9),
            (r"\bswarm[- ]for[- ]swarm\b", 0.7),
            (r"\bswarm the swarm\b", 0.6),
        ),
    ),
    (
        "operations-research",
        (
            (r"\bexpert[- ]generator\b", 1.2),
            (r"\bdomain[- ]expert\b", 1.0),
            (r"\bautomability\b", 0.8),
            (r"\bslot[- ]assignment\b", 0.6),
            (r"\bdispatch(?:able)? capacity\b", 0.6),
        ),
    ),
)


@dataclass
class DomainState:
    name: str
    frontier_path: str
    active_frontiers: list[str]
    updated_session: int
    age_sessions: int
    next_mentions: int = 0
    next_priority_weight: float = 0.0
    finding_mentions: int = 0
    finding_priority_weight: float = 0.0
    knowledge_mentions: int = 0
    knowledge_priority_weight: float = 0.0
    active_lane_pressure: int = 0

    def to_json(self) -> dict:
        return {
            "domain": self.name,
            "frontier_path": self.frontier_path,
            "active_frontier_count": len(self.active_frontiers),
            "active_frontiers": self.active_frontiers,
            "updated_session": self.updated_session,
            "age_sessions": self.age_sessions,
            "next_mentions": self.next_mentions,
            "next_priority_weight": round(self.next_priority_weight, 3),
            "finding_mentions": self.finding_mentions,
            "finding_priority_weight": round(self.finding_priority_weight, 3),
            "knowledge_mentions": self.knowledge_mentions,
            "knowledge_priority_weight": round(self.knowledge_priority_weight, 3),
            "active_lane_pressure": self.active_lane_pressure,
        }


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


def _last_session(text: str) -> int:
    sessions = [int(x) for x in re.findall(r"\bS(\d+)\b", text or "")]
    return max(sessions) if sessions else 0


def _updated_session_from_state_header(text: str) -> int:
    m = re.search(r"^Updated:\s*[0-9]{4}-[0-9]{2}-[0-9]{2}\s+S(\d+)\b", text or "", re.MULTILINE)
    return int(m.group(1)) if m else 0


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def parse_active_frontiers(frontier_text: str) -> list[str]:
    active_match = re.search(r"## Active(.*?)(?:\n## |\Z)", frontier_text, re.DOTALL)
    if not active_match:
        return []
    active_block = active_match.group(1)
    ordered_unique: list[str] = []
    for line in active_block.splitlines():
        bullet_bold = re.match(r"^\s*[-*]\s+(~~)?\*\*(F-[A-Z0-9]+)\*\*(?:~~)?", line)
        bullet_plain = re.match(r"^\s*[-*]\s+(~~)?(F-[A-Z0-9]+)(?:~~)?\b", line)
        table_row = re.match(r"^\s*\|\s*(~~)?(F-[A-Z0-9]+)(?:~~)?\s*\|", line)
        m = bullet_bold or bullet_plain or table_row
        if not m:
            continue
        if m.group(1):
            # Ignore struck-through IDs inside the Active section.
            continue
        fid = m.group(2)
        if fid not in ordered_unique:
            ordered_unique.append(fid)
    return ordered_unique


def parse_updated_session(frontier_text: str) -> int:
    match = re.search(r"Updated:\s*[0-9]{4}-[0-9]{2}-[0-9]{2}\s*S(\d+)", frontier_text)
    return int(match.group(1)) if match else 0


def load_domain_frontiers(domains_root: Path, current_session: int) -> tuple[list[DomainState], dict[str, str]]:
    states: list[DomainState] = []
    frontier_to_domain: dict[str, str] = {}

    for domain_dir in sorted(domains_root.iterdir(), key=lambda p: p.name):
        if not domain_dir.is_dir():
            continue
        frontier_path = domain_dir / "tasks" / "FRONTIER.md"
        if not frontier_path.exists():
            continue

        text = _read(frontier_path)
        active = parse_active_frontiers(text)
        updated = parse_updated_session(text)
        age = max(0, current_session - updated) if current_session > 0 and updated > 0 else 0
        for fid in active:
            frontier_to_domain[fid] = domain_dir.name

        states.append(
            DomainState(
                name=domain_dir.name,
                frontier_path=_display_path(frontier_path),
                active_frontiers=active,
                updated_session=updated,
                age_sessions=age,
                next_mentions=0,
                next_priority_weight=0.0,
                finding_mentions=0,
                finding_priority_weight=0.0,
                knowledge_mentions=0,
                knowledge_priority_weight=0.0,
                active_lane_pressure=0,
            )
        )

    return states, frontier_to_domain


def parse_next_demand(next_text: str, frontier_to_domain: dict[str, str]) -> tuple[dict[str, int], dict[str, float]]:
    mentions: dict[str, int] = {}
    weights: dict[str, float] = {}

    section = re.search(r"## For next session(.*?)(?:\n## |\Z)", next_text, re.DOTALL)
    if not section:
        return mentions, weights

    lines = section.group(1).splitlines()
    rank = 0
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if not numbered:
            continue
        rank += 1
        body = numbered.group(2)
        ids = set(re.findall(r"\bF-[A-Z0-9]+\b", body))
        priority_weight = max(1.0, 5.0 - rank)
        for fid in ids:
            domain = frontier_to_domain.get(fid)
            if domain is None:
                continue
            mentions[domain] = mentions.get(domain, 0) + 1
            weights[domain] = weights.get(domain, 0.0) + priority_weight

    return mentions, weights


def parse_findings_demand(
    next_text: str,
    frontier_to_domain: dict[str, str],
    *,
    max_lines: int = 20,
) -> tuple[dict[str, int], dict[str, float]]:
    mentions: dict[str, int] = {}
    weights: dict[str, float] = {}

    section = re.search(r"## What just happened(.*?)(?:\n## |\Z)", next_text, re.DOTALL)
    if not section:
        return mentions, weights

    line_count = 0
    for raw in section.group(1).splitlines():
        line = raw.strip()
        if not line:
            continue
        if not re.match(r"^S\d+:", line):
            continue
        line_count += 1
        if line_count > max_lines:
            break

        ids = set(re.findall(r"\bF-[A-Z0-9]+\b", line))
        if not ids:
            continue

        # Newer lines in "What just happened" are higher in the section.
        recency_weight = max(0.5, 5.0 - 0.2 * (line_count - 1))
        low = line.lower()
        urgency_boost = 0.0
        if any(k in low for k in ("open", "next step", "caveat", "unstable", "pending", "deferred", "blocked")):
            urgency_boost += 0.75
        if any(k in low for k in ("resolved", "closed", "superseded")):
            urgency_boost -= 0.25
        line_weight = max(0.2, recency_weight + urgency_boost)

        for fid in ids:
            domain = frontier_to_domain.get(fid)
            if domain is None:
                continue
            mentions[domain] = mentions.get(domain, 0) + 1
            weights[domain] = weights.get(domain, 0.0) + line_weight

    return mentions, weights


def _apply_domain_knowledge_rules(
    line: str,
    *,
    base_weight: float,
    mentions: dict[str, int],
    weights: dict[str, float],
) -> None:
    low = line.lower()
    for domain, rules in DOMAIN_KNOWLEDGE_RULES:
        matched_rules = 0
        score = 0.0
        for pattern, weight in rules:
            if re.search(pattern, low):
                matched_rules += 1
                score += weight
        if matched_rules <= 0:
            continue
        mentions[domain] = mentions.get(domain, 0) + matched_rules
        weights[domain] = weights.get(domain, 0.0) + base_weight * score


def parse_domain_knowledge_demand(
    next_text: str,
    *,
    max_finding_lines: int = 20,
) -> tuple[dict[str, int], dict[str, float]]:
    """Extract non-frontier domain demand from strategic swarm terminology."""
    mentions: dict[str, int] = {}
    weights: dict[str, float] = {}

    next_section = re.search(r"## For next session(.*?)(?:\n## |\Z)", next_text, re.DOTALL)
    if next_section:
        rank = 0
        for raw in next_section.group(1).splitlines():
            line = raw.strip()
            if not line:
                continue
            numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
            if not numbered:
                continue
            rank += 1
            base_weight = max(1.0, 5.0 - rank)
            _apply_domain_knowledge_rules(
                numbered.group(2),
                base_weight=base_weight,
                mentions=mentions,
                weights=weights,
            )

    findings = re.search(r"## What just happened(.*?)(?:\n## |\Z)", next_text, re.DOTALL)
    if not findings:
        return mentions, weights

    line_count = 0
    for raw in findings.group(1).splitlines():
        line = raw.strip()
        if not line:
            continue
        if not re.match(r"^S\d+:", line):
            continue
        line_count += 1
        if line_count > max_finding_lines:
            break
        recency_weight = max(0.5, 5.0 - 0.2 * (line_count - 1))
        _apply_domain_knowledge_rules(
            line,
            base_weight=recency_weight,
            mentions=mentions,
            weights=weights,
        )
    return mentions, weights


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
        rows.append(row)
    return rows


def _latest_lane_rows(lanes_text: str) -> list[dict[str, str]]:
    latest_by_lane: dict[str, dict[str, str]] = {}
    for row in _parse_lane_rows(lanes_text):
        lane = row.get("lane", "")
        if lane:
            latest_by_lane[lane] = row
    return list(latest_by_lane.values())


def _parse_etc_fields(etc: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for part in re.split(r"[;,]", etc or ""):
        chunk = part.strip()
        if not chunk or "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        fields[key.strip().lower()] = value.strip().lower()
    return fields


def _domain_from_lane_row(row: dict[str, str], frontier_to_domain: dict[str, str]) -> str | None:
    scope = row.get("scope", "")
    etc = row.get("etc", "")

    m_scope = re.search(r"domains/([^/\s]+)/", scope)
    if m_scope:
        return m_scope.group(1)

    m_fid = re.search(r"frontier=(F-[A-Z0-9]+)", etc)
    if m_fid:
        return frontier_to_domain.get(m_fid.group(1))
    return None


def parse_active_lane_pressure(lanes_text: str, frontier_to_domain: dict[str, str]) -> dict[str, int]:
    pressure: dict[str, int] = {}
    for row in _latest_lane_rows(lanes_text):
        if row.get("status", "") not in ACTIVE_LANE_STATUSES:
            continue
        domain = _domain_from_lane_row(row, frontier_to_domain)
        if domain is None:
            continue
        pressure[domain] = pressure.get(domain, 0) + 1

    return pressure


def parse_dispatchable_capacity(lanes_text: str, frontier_to_domain: dict[str, str]) -> dict[str, float]:
    """Count domain slots immediately dispatchable from lane state.

    A lane contributes capacity when its latest status is READY/ACTIVE/CLAIMED,
    `available` is yes/partial, and `blocked=none`.
    """
    capacity: dict[str, float] = {}
    for row in _latest_lane_rows(lanes_text):
        status = row.get("status", "")
        if status not in DISPATCHABLE_LANE_STATUSES:
            continue
        domain = _domain_from_lane_row(row, frontier_to_domain)
        if domain is None:
            continue

        fields = _parse_etc_fields(row.get("etc", ""))
        blocked = fields.get("blocked", "none")
        available = fields.get("available", "yes")
        if blocked != "none":
            continue

        slot_capacity = 0.0
        if available in ("yes", "ready"):
            slot_capacity = 1.0
        elif available == "partial":
            slot_capacity = 0.5
        if slot_capacity <= 0:
            continue

        capacity[domain] = capacity.get(domain, 0.0) + slot_capacity
    return capacity


def _is_domain_expert_row(row: dict[str, str]) -> bool:
    lane = row.get("lane", "").lower()
    fields = _parse_etc_fields(row.get("etc", ""))
    dispatch = fields.get("dispatch", "")
    return "domex" in lane or "domain-expert" in dispatch or "expert-generator" in dispatch


def parse_domain_expert_coverage(
    lanes_text: str,
    frontier_to_domain: dict[str, str],
) -> tuple[dict[str, float], dict[str, int]]:
    """Estimate active and dispatchable capacity from domain-expert lanes only."""
    capacity: dict[str, float] = {}
    active_counts: dict[str, int] = {}
    for row in _latest_lane_rows(lanes_text):
        status = row.get("status", "")
        if status not in ACTIVE_LANE_STATUSES:
            continue
        if not _is_domain_expert_row(row):
            continue

        domain = _domain_from_lane_row(row, frontier_to_domain)
        if domain is None:
            continue

        active_counts[domain] = active_counts.get(domain, 0) + 1
        if status not in DISPATCHABLE_LANE_STATUSES:
            continue

        fields = _parse_etc_fields(row.get("etc", ""))
        blocked = fields.get("blocked", "none")
        available = fields.get("available", "yes")
        if blocked != "none":
            continue

        slot_capacity = 0.0
        if available in ("yes", "ready"):
            slot_capacity = 1.0
        elif available == "partial":
            slot_capacity = 0.5
        if slot_capacity <= 0:
            continue

        capacity[domain] = capacity.get(domain, 0.0) + slot_capacity
    return capacity, active_counts


def _domain_lane_code(domain: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", domain.lower()).strip("-")
    token = token.replace("-", "")
    return token[:12].upper() or "GEN"


def build_expert_generator(
    states: list[DomainState],
    recommended_alloc: dict[str, int],
    dispatchable_capacity: dict[str, float],
    domain_expert_capacity: dict[str, float],
    domain_expert_active_counts: dict[str, int],
    current_session: int,
) -> dict:
    """Emit spawn requests when recommended slots exceed current expert coverage."""
    by_name = {s.name: s for s in states}
    requests: list[dict] = []
    total_experts = 0

    ranked_domains = sorted(
        recommended_alloc.keys(),
        key=lambda name: (recommended_alloc.get(name, 0), name),
        reverse=True,
    )
    for domain in ranked_domains:
        requested_slots = int(recommended_alloc.get(domain, 0))
        if requested_slots <= 0:
            continue
        st = by_name.get(domain)
        if st is None:
            continue

        total_capacity = float(dispatchable_capacity.get(domain, 0.0))
        expert_capacity = float(domain_expert_capacity.get(domain, 0.0))
        expert_active = int(domain_expert_active_counts.get(domain, 0))

        total_shortfall = max(0.0, requested_slots - total_capacity)
        expert_shortfall = max(0.0, requested_slots - expert_capacity)
        if total_shortfall <= 0.0 and expert_shortfall <= 0.0 and expert_active > 0:
            continue

        spawn_count = int(max(1, math.ceil(max(total_shortfall, expert_shortfall))))
        total_experts += spawn_count

        frontier_hint = "/".join(st.active_frontiers[:2]) if st.active_frontiers else "none"
        lane_code = _domain_lane_code(domain)
        lane_ids = [
            f"L-S{current_session}-DOMEX-GEN-{lane_code}-{idx + 1}"
            for idx in range(spawn_count)
        ]

        triggers: list[str] = []
        if total_shortfall > 0.0:
            triggers.append("dispatch_capacity_shortfall")
        if expert_shortfall > 0.0:
            triggers.append("domain_expert_coverage_shortfall")
        if expert_active <= 0:
            triggers.append("no_active_domain_expert_lane")

        requests.append(
            {
                "domain": domain,
                "requested_slots": requested_slots,
                "dispatchable_capacity": round(total_capacity, 3),
                "domain_expert_capacity": round(expert_capacity, 3),
                "active_domain_expert_lanes": expert_active,
                "spawn_count": spawn_count,
                "trigger_reasons": triggers,
                "lane_ids": lane_ids,
                "scope_key": st.frontier_path,
                "etc_template": (
                    f"setup=<swarm-setup>, focus=domains/{domain}, frontier={frontier_hint}, "
                    f"dispatch=expert-generator-s{current_session}, progress=queued, "
                    "available=yes, blocked=none, next_step=execute-domain-expert-lane, "
                    f"human_open_item=none, domain_sync=queued, memory_target={st.frontier_path}"
                ),
            }
        )

    return {
        "spawn_required": bool(requests),
        "triggered_domains": len(requests),
        "total_new_experts": total_experts,
        "requests": requests,
    }


def compute_automability(
    allocations: dict[str, int],
    dispatchable_capacity: dict[str, float],
) -> dict:
    total_decisions = float(sum(max(0, int(v)) for v in allocations.values()))
    if total_decisions <= 0:
        return {
            "total_decisions": 0,
            "accepted_decisions": 0.0,
            "rejected_decisions": 0.0,
            "automability_rate": 0.0,
            "accepted_by_domain": {},
            "dispatchable_capacity_by_domain": {},
        }

    accepted_by_domain: dict[str, float] = {}
    accepted_total = 0.0
    for domain, slots in allocations.items():
        if slots <= 0:
            continue
        accepted = min(float(slots), max(0.0, dispatchable_capacity.get(domain, 0.0)))
        if accepted <= 0:
            continue
        accepted_total += accepted
        accepted_by_domain[domain] = round(accepted, 3)

    rejected = max(0.0, total_decisions - accepted_total)
    return {
        "total_decisions": int(total_decisions),
        "accepted_decisions": round(accepted_total, 3),
        "rejected_decisions": round(rejected, 3),
        "automability_rate": round(accepted_total / total_decisions, 4),
        "accepted_by_domain": accepted_by_domain,
        "dispatchable_capacity_by_domain": {
            domain: round(cap, 3)
            for domain, cap in sorted(dispatchable_capacity.items())
            if cap > 0
        },
    }


def apply_automability_guard(
    metrics: dict,
    automability_floor: float,
    guard_penalty: float,
) -> dict:
    floor = min(1.0, max(0.0, float(automability_floor)))
    penalty_per_unit = max(0.0, float(guard_penalty))
    rate = float(metrics.get("automability_rate", 0.0))
    shortfall = max(0.0, floor - rate)
    penalty = round(shortfall * penalty_per_unit, 4)

    guarded = dict(metrics)
    guarded["guard"] = {
        "automability_floor": round(floor, 4),
        "pass": shortfall <= 0.0,
        "shortfall": round(shortfall, 4),
        "penalty": penalty,
    }
    guarded["effective_net_score"] = round(float(metrics.get("net_score", 0.0)) - penalty, 4)
    return guarded


def policy_score(policy: str, state: DomainState) -> float:
    if policy == "fifo":
        # Oldest queue items first; slight tie-break by unresolved load.
        return float(state.age_sessions) + 0.1 * len(state.active_frontiers)
    if policy == "risk_first":
        # Risk = unresolved pressure + aging + explicit near-term demand + fresh finding pressure.
        return (
            2.0 * len(state.active_frontiers)
            + state.age_sessions
            + state.next_mentions
            + 1.25 * state.finding_mentions
            + 0.75 * state.knowledge_mentions
            - state.active_lane_pressure
        )
    if policy == "value_density":
        # Value per expected coordination unit.
        value = (
            3.0 * state.next_priority_weight
            + 2.0 * state.finding_priority_weight
            + 1.5 * state.knowledge_priority_weight
            + len(state.active_frontiers)
        )
        return value / (1.0 + state.active_lane_pressure)
    if policy == "hybrid":
        # Balanced policy: demand + findings + load + freshness normalized by lane pressure.
        value = (
            2.0 * state.next_priority_weight
            + 1.5 * state.finding_priority_weight
            + state.knowledge_priority_weight
            + len(state.active_frontiers)
            + 0.5 * state.age_sessions
        )
        return value / (1.0 + 0.5 * state.active_lane_pressure)
    raise ValueError(f"Unknown policy: {policy}")


def allocate_agents(
    states: list[DomainState],
    policy: str,
    agent_count: int,
    dispatchable_capacity: dict[str, float] | None = None,
    capacity_bias: float = 0.0,
) -> dict[str, int]:
    allocations = {s.name: 0 for s in states}
    base_scores = {s.name: max(0.0, policy_score(policy, s)) for s in states}
    capacity = dispatchable_capacity or {}
    bias = max(0.0, min(1.0, float(capacity_bias)))
    floor_factor = 0.05

    if agent_count <= 0:
        return allocations

    for _ in range(agent_count):
        best_domain = None
        best_marginal = -1.0
        for s in sorted(states, key=lambda item: item.name):
            score = base_scores[s.name]
            marginal = score / (1.0 + allocations[s.name])
            if bias > 0.0:
                remaining_capacity = max(0.0, capacity.get(s.name, 0.0) - allocations[s.name])
                if remaining_capacity > 0.0:
                    # Boost lanes that can be dispatched immediately.
                    capacity_factor = 1.0 + bias * min(1.0, remaining_capacity)
                else:
                    # Softly penalize over-capacity assignments so dispatchable lanes can win.
                    capacity_factor = max(floor_factor, 1.0 - bias)
                marginal *= capacity_factor
            if marginal > best_marginal:
                best_marginal = marginal
                best_domain = s.name
        if best_domain is None:
            break
        allocations[best_domain] += 1

    return allocations


def evaluate_policy(
    states: list[DomainState],
    allocations: dict[str, int],
    dispatchable_capacity: dict[str, float],
    automability_weight: float,
) -> dict:
    by_name = {s.name: s for s in states}
    projected_gain = 0.0
    collision_risk = 0.0
    for domain, slots in allocations.items():
        st = by_name[domain]
        value_proxy = (
            3.0 * st.next_priority_weight
            + 2.0 * st.finding_priority_weight
            + 1.2 * st.knowledge_priority_weight
            + len(st.active_frontiers)
            + 0.5 * st.age_sessions
        )
        projected_gain += slots * value_proxy
        collision_risk += max(0, slots - 1) * (1.0 + st.active_lane_pressure)
    automability = compute_automability(allocations, dispatchable_capacity)
    automability_bonus = automability_weight * automability["automability_rate"]
    net = projected_gain - 1.5 * collision_risk + automability_bonus
    return {
        "projected_gain": round(projected_gain, 4),
        "collision_risk": round(collision_risk, 4),
        "automability_rate": automability["automability_rate"],
        "accepted_decisions": automability["accepted_decisions"],
        "rejected_decisions": automability["rejected_decisions"],
        "automability_bonus": round(automability_bonus, 4),
        "net_score": round(net, 4),
        "automability": automability,
    }


def build_slot_plan(states: list[DomainState], allocations: dict[str, int], policy: str) -> list[dict]:
    by_name = {s.name: s for s in states}
    slots: list[dict] = []
    slot_number = 0
    ranked = sorted(
        allocations.keys(),
        key=lambda name: (allocations[name], policy_score(policy, by_name[name]), name),
        reverse=True,
    )
    for domain in ranked:
        count = allocations[domain]
        if count <= 0:
            continue
        st = by_name[domain]
        for k in range(count):
            slot_number += 1
            slots.append(
                {
                    "slot": slot_number,
                    "domain": domain,
                    "lane_focus": st.frontier_path,
                    "reason": (
                        f"score={policy_score(policy, st):.3f}; "
                        f"next_weight={st.next_priority_weight:.1f}; "
                        f"finding_weight={st.finding_priority_weight:.1f}; "
                        f"active_frontiers={len(st.active_frontiers)}; "
                        f"lane_pressure={st.active_lane_pressure}; "
                        f"allocation_index={k + 1}/{count}"
                    ),
                }
            )
    return slots


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-count", type=int, default=4, help="Total agent slots to allocate.")
    parser.add_argument(
        "--policy",
        choices=("all",) + POLICIES,
        default="all",
        help="Evaluate one policy or all policies.",
    )
    parser.add_argument("--next-path", type=Path, default=Path("tasks/NEXT.md"))
    parser.add_argument("--lanes-path", type=Path, default=Path("tasks/SWARM-LANES.md"))
    parser.add_argument("--domains-root", type=Path, default=Path("domains"))
    parser.add_argument(
        "--findings-window",
        type=int,
        default=20,
        help="How many recent 'What just happened' lines to scan for finding pressure.",
    )
    parser.add_argument(
        "--automability-weight",
        type=float,
        default=20.0,
        help="Weight for automability bonus in net policy score.",
    )
    parser.add_argument(
        "--automability-floor",
        type=float,
        default=0.0,
        help="Minimum automability_rate required for unpenalized policy ranking (0..1).",
    )
    parser.add_argument(
        "--guard-penalty",
        type=float,
        default=200.0,
        help="Penalty multiplier for automability shortfall when automability_floor is set.",
    )
    parser.add_argument(
        "--capacity-bias",
        type=float,
        default=0.0,
        help="Dispatchability bias in allocation (0=no bias, 1=strong boost-in-capacity + over-capacity penalty).",
    )
    parser.add_argument("--json-out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    next_path = args.next_path if args.next_path.is_absolute() else REPO_ROOT / args.next_path
    lanes_path = args.lanes_path if args.lanes_path.is_absolute() else REPO_ROOT / args.lanes_path
    domains_root = args.domains_root if args.domains_root.is_absolute() else REPO_ROOT / args.domains_root

    next_text = _read(next_path)
    current_session = _updated_session_from_state_header(next_text)
    if current_session <= 0:
        current_session = _last_session(next_text)
    if current_session <= 0:
        current_session = _last_session(_read(REPO_ROOT / "memory/SESSION-LOG.md"))

    states, frontier_to_domain = load_domain_frontiers(domains_root, current_session)
    mention_counts, mention_weights = parse_next_demand(next_text, frontier_to_domain)
    finding_counts, finding_weights = parse_findings_demand(
        next_text,
        frontier_to_domain,
        max_lines=max(1, args.findings_window),
    )
    knowledge_counts, knowledge_weights = parse_domain_knowledge_demand(
        next_text,
        max_finding_lines=max(1, args.findings_window),
    )
    lanes_text = _read(lanes_path)
    lane_pressure = parse_active_lane_pressure(lanes_text, frontier_to_domain)
    dispatchable_capacity = parse_dispatchable_capacity(lanes_text, frontier_to_domain)
    domain_expert_capacity, domain_expert_active_counts = parse_domain_expert_coverage(
        lanes_text,
        frontier_to_domain,
    )

    for st in states:
        st.next_mentions = mention_counts.get(st.name, 0)
        st.next_priority_weight = mention_weights.get(st.name, 0.0)
        st.finding_mentions = finding_counts.get(st.name, 0)
        st.finding_priority_weight = finding_weights.get(st.name, 0.0)
        st.knowledge_mentions = knowledge_counts.get(st.name, 0)
        st.knowledge_priority_weight = knowledge_weights.get(st.name, 0.0)
        st.active_lane_pressure = lane_pressure.get(st.name, 0)

    selected_policies = list(POLICIES) if args.policy == "all" else [args.policy]
    policy_payload: dict[str, dict] = {}
    for policy in selected_policies:
        scores = {s.name: round(policy_score(policy, s), 6) for s in states}
        ranked = [name for name, _ in sorted(scores.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)]
        allocations = allocate_agents(
            states,
            policy,
            args.agent_count,
            dispatchable_capacity=dispatchable_capacity,
            capacity_bias=args.capacity_bias,
        )
        raw_metrics = evaluate_policy(
            states,
            allocations,
            dispatchable_capacity=dispatchable_capacity,
            automability_weight=args.automability_weight,
        )
        metrics = apply_automability_guard(
            raw_metrics,
            automability_floor=args.automability_floor,
            guard_penalty=args.guard_penalty,
        )
        policy_payload[policy] = {
            "scores": scores,
            "ranked_domains": ranked,
            "allocations": allocations,
            "metrics": metrics,
        }

    recommended_policy = max(
        policy_payload.keys(),
        key=lambda p: (
            policy_payload[p]["metrics"]["effective_net_score"],
            policy_payload[p]["metrics"]["projected_gain"],
            p == "hybrid",
        ),
    )
    recommended_alloc = policy_payload[recommended_policy]["allocations"]
    recommended_plan = build_slot_plan(states, recommended_alloc, recommended_policy)
    expert_generator = build_expert_generator(
        states,
        recommended_alloc,
        dispatchable_capacity=dispatchable_capacity,
        domain_expert_capacity=domain_expert_capacity,
        domain_expert_active_counts=domain_expert_active_counts,
        current_session=current_session,
    )

    payload = {
        "session": current_session,
        "inputs": {
            "agent_count": args.agent_count,
            "policies_evaluated": selected_policies,
            "next_path": _display_path(next_path),
            "lanes_path": _display_path(lanes_path),
            "domains_root": _display_path(domains_root),
            "findings_window": args.findings_window,
            "automability_weight": args.automability_weight,
            "automability_floor": args.automability_floor,
            "guard_penalty": args.guard_penalty,
            "capacity_bias": args.capacity_bias,
        },
        "domain_signals": [s.to_json() for s in sorted(states, key=lambda x: x.name)],
        "dispatchable_capacity": {
            domain: round(cap, 3) for domain, cap in sorted(dispatchable_capacity.items()) if cap > 0
        },
        "domain_expert_coverage": {
            "dispatchable_capacity": {
                domain: round(cap, 3) for domain, cap in sorted(domain_expert_capacity.items()) if cap > 0
            },
            "active_lane_count": {
                domain: count for domain, count in sorted(domain_expert_active_counts.items()) if count > 0
            },
        },
        "policies": policy_payload,
        "recommended_policy": recommended_policy,
        "recommended_plan": recommended_plan,
        "expert_generator": expert_generator,
    }

    if args.json_out is not None:
        out = args.json_out if args.json_out.is_absolute() else REPO_ROOT / args.json_out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(json.dumps(payload, indent=2))

    rec_metrics = payload["policies"][recommended_policy]["metrics"]
    print(
        "recommended_policy="
        f"{recommended_policy} net={rec_metrics['net_score']:.3f} "
        f"effective_net={rec_metrics['effective_net_score']:.3f} "
        f"gain={rec_metrics['projected_gain']:.3f} risk={rec_metrics['collision_risk']:.3f}"
    )
    if expert_generator["spawn_required"]:
        print(
            "expert_generator="
            f"spawn_required domains={expert_generator['triggered_domains']} "
            f"new_experts={expert_generator['total_new_experts']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
