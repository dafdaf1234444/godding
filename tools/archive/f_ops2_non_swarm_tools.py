#!/usr/bin/env python3
"""F-OPS2: rank high-leverage non-swarm tools for swarm execution."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parent.parent

# Score weights (sum = 1.0).
SWARM_WEIGHT = 0.35
AUTOMATION_WEIGHT = 0.25
OBSERVABILITY_WEIGHT = 0.20
PORTABILITY_WEIGHT = 0.20

EFFORT_PENALTY = 0.35
RISK_PENALTY = 0.25


@dataclass(frozen=True)
class ToolCandidate:
    tool_id: str
    name: str
    commands: tuple[str, ...]
    category: str
    swarm_gain: float
    automation_gain: float
    observability_gain: float
    portability_gain: float
    setup_effort: float
    risk: float
    rationale: str
    next_step: str


CANDIDATES: tuple[ToolCandidate, ...] = (
    ToolCandidate(
        tool_id="git-worktree",
        name="Git Worktree",
        commands=("git",),
        category="parallel-execution",
        swarm_gain=5.0,
        automation_gain=4.0,
        observability_gain=4.0,
        portability_gain=5.0,
        setup_effort=1.0,
        risk=1.0,
        rationale="Isolates lane branches without context switching collisions.",
        next_step="Use one worktree per READY lane before fan-out execution.",
    ),
    ToolCandidate(
        tool_id="ripgrep",
        name="ripgrep",
        commands=("rg",),
        category="search",
        swarm_gain=4.0,
        automation_gain=4.0,
        observability_gain=5.0,
        portability_gain=4.0,
        setup_effort=1.0,
        risk=1.0,
        rationale="Fast repo-wide retrieval keeps orientation and audits cheap.",
        next_step="Replace slow grep/find calls in scripts with `rg` where possible.",
    ),
    ToolCandidate(
        tool_id="jq",
        name="jq",
        commands=("jq",),
        category="artifact-analysis",
        swarm_gain=3.5,
        automation_gain=5.0,
        observability_gain=5.0,
        portability_gain=4.0,
        setup_effort=1.0,
        risk=1.0,
        rationale="Makes JSON artifacts queryable for quick diff and gating checks.",
        next_step="Add jq-based smoke checks for key experiment artifacts in CI.",
    ),
    ToolCandidate(
        tool_id="gh-cli",
        name="GitHub CLI",
        commands=("gh",),
        category="coordination",
        swarm_gain=4.5,
        automation_gain=5.0,
        observability_gain=4.0,
        portability_gain=4.0,
        setup_effort=2.0,
        risk=2.0,
        rationale="Bridges local swarm state with PR/issues without manual UI work.",
        next_step="Automate lane claim/status updates from issue and PR events.",
    ),
    ToolCandidate(
        tool_id="pre-commit",
        name="pre-commit",
        commands=("pre-commit",),
        category="quality-gates",
        swarm_gain=3.5,
        automation_gain=5.0,
        observability_gain=3.5,
        portability_gain=4.0,
        setup_effort=2.0,
        risk=1.0,
        rationale="Enforces consistent checks before noisy commits land.",
        next_step="Mirror `tools/check.sh --quick` in a pre-commit profile.",
    ),
    ToolCandidate(
        tool_id="uv",
        name="uv",
        commands=("uv",),
        category="runtime",
        swarm_gain=3.0,
        automation_gain=4.5,
        observability_gain=3.0,
        portability_gain=4.0,
        setup_effort=2.0,
        risk=1.0,
        rationale="Stabilizes Python environments across multi-host swarms.",
        next_step="Pin tool dependencies and run CI scripts through `uv run`.",
    ),
    ToolCandidate(
        tool_id="pytest-xdist",
        name="pytest + xdist",
        commands=("pytest",),
        category="verification-throughput",
        swarm_gain=4.5,
        automation_gain=4.0,
        observability_gain=3.5,
        portability_gain=3.5,
        setup_effort=2.5,
        risk=2.0,
        rationale="Parallel test execution cuts verification latency for lane merges.",
        next_step="Split quick/full suites and run quick suite with `-n auto`.",
    ),
    ToolCandidate(
        tool_id="just",
        name="just",
        commands=("just",),
        category="task-orchestration",
        swarm_gain=3.5,
        automation_gain=4.0,
        observability_gain=3.0,
        portability_gain=4.0,
        setup_effort=1.5,
        risk=1.0,
        rationale="Standard command recipes reduce setup variance across agents.",
        next_step="Define canonical targets (`orient`, `check`, `lane-claim`, `lane-close`).",
    ),
    ToolCandidate(
        tool_id="act",
        name="act",
        commands=("act",),
        category="ci-local-replay",
        swarm_gain=3.5,
        automation_gain=4.5,
        observability_gain=4.0,
        portability_gain=3.0,
        setup_effort=3.0,
        risk=2.5,
        rationale="Replays GitHub workflows locally before CI queue delay.",
        next_step="Replay `swarm-check` and intake workflows before pushing.",
    ),
    ToolCandidate(
        tool_id="sqlite3",
        name="sqlite3",
        commands=("sqlite3",),
        category="historical-analysis",
        swarm_gain=3.0,
        automation_gain=3.5,
        observability_gain=5.0,
        portability_gain=4.0,
        setup_effort=1.5,
        risk=1.0,
        rationale="Enables ad-hoc querying over lane/history exports for trends.",
        next_step="Export lane rows to sqlite for pickup-latency and closure analyses.",
    ),
)


def _command_state(commands: set[str], exists_fn: Callable[[str], str | None] | None = None) -> dict[str, bool]:
    resolver = exists_fn or shutil.which
    return {command: bool(resolver(command)) for command in sorted(commands)}


def availability_from_state(commands: tuple[str, ...], state: dict[str, bool]) -> tuple[str, float, list[str]]:
    present = [cmd for cmd in commands if state.get(cmd, False)]
    missing = [cmd for cmd in commands if not state.get(cmd, False)]
    if len(present) == len(commands):
        return "ready", 1.0, missing
    if present:
        return "partial", 0.4, missing
    return "missing", 0.0, missing


def score_candidate(candidate: ToolCandidate, state: dict[str, bool]) -> dict[str, object]:
    status, availability_bonus, missing_commands = availability_from_state(candidate.commands, state)
    weighted_value = (
        candidate.swarm_gain * SWARM_WEIGHT
        + candidate.automation_gain * AUTOMATION_WEIGHT
        + candidate.observability_gain * OBSERVABILITY_WEIGHT
        + candidate.portability_gain * PORTABILITY_WEIGHT
    )
    score = weighted_value + availability_bonus - candidate.setup_effort * EFFORT_PENALTY - candidate.risk * RISK_PENALTY
    return {
        "id": candidate.tool_id,
        "name": candidate.name,
        "category": candidate.category,
        "commands": list(candidate.commands),
        "status": status,
        "score": round(score, 4),
        "weighted_value": round(weighted_value, 4),
        "availability_bonus": availability_bonus,
        "setup_effort": candidate.setup_effort,
        "risk": candidate.risk,
        "missing_commands": missing_commands,
        "rationale": candidate.rationale,
        "next_step": candidate.next_step,
    }


def rank_candidates(candidates: tuple[ToolCandidate, ...], state: dict[str, bool]) -> list[dict[str, object]]:
    ranked = [score_candidate(candidate, state) for candidate in candidates]
    ranked.sort(key=lambda row: (-float(row["score"]), row["id"]))
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    return ranked


def summarize(ranked: list[dict[str, object]], top_n: int) -> dict[str, object]:
    top = ranked[: max(1, top_n)]
    ready = [row["id"] for row in ranked if row["status"] == "ready"]
    missing = [row["id"] for row in ranked if row["status"] == "missing"]
    return {
        "tool_count": len(ranked),
        "ready_count": len(ready),
        "missing_count": len(missing),
        "top_recommendations": [row["id"] for row in top],
        "top_ready": ready[:5],
        "top_missing": missing[:5],
    }


def _print_table(top_rows: list[dict[str, object]]) -> None:
    print("Rank | Tool | Status | Score | Commands")
    print("-----|------|--------|-------|---------")
    for row in top_rows:
        commands = ",".join(str(cmd) for cmd in row["commands"])
        print(f"{row['rank']:>4} | {row['id']:<14} | {row['status']:<7} | {row['score']:.3f} | {commands}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=5, help="Number of top tools to print")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=REPO_ROOT / "experiments" / "operations-research" / "f-ops2-non-swarm-tools.json",
        help="Where to write full ranking artifact",
    )
    parser.add_argument("--session", default="", help="Optional session label (for example S186)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command_universe = {command for candidate in CANDIDATES for command in candidate.commands}
    state = _command_state(command_universe)
    ranked = rank_candidates(CANDIDATES, state)
    top_rows = ranked[: max(1, args.top)]

    artifact = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "session": args.session,
        "host": {
            "platform": platform.platform(),
            "python": sys.executable,
        },
        "scoring": {
            "weights": {
                "swarm_gain": SWARM_WEIGHT,
                "automation_gain": AUTOMATION_WEIGHT,
                "observability_gain": OBSERVABILITY_WEIGHT,
                "portability_gain": PORTABILITY_WEIGHT,
            },
            "penalties": {
                "setup_effort": EFFORT_PENALTY,
                "risk": RISK_PENALTY,
            },
            "availability_bonus": {
                "ready": 1.0,
                "partial": 0.4,
                "missing": 0.0,
            },
        },
        "command_state": state,
        "summary": summarize(ranked, args.top),
        "ranked_tools": ranked,
    }

    out_path = args.json_out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote ranking artifact: {out_path}")
    _print_table(top_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
