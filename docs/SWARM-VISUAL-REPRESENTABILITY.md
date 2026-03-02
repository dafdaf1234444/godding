# Swarm Visual Representability Contract

This file defines how swarm state should be represented visually so it is legible to:
- humans,
- the swarm itself (self-check and prioritization), and
- other swarms/child swarms.

## Goal

Visual representation is successful when a new node can recover the same next action from the visual view that it would recover from the canonical text state (`memory/INDEX.md`, `tasks/FRONTIER.md`, `tasks/NEXT.md`, `tasks/SWARM-LANES.md`).

If a visual and canonical state disagree, canonical state wins.

## Canonical Visual Primitives

| Primitive | Meaning | Source of truth |
| --- | --- | --- |
| Node: `Frontier` | open question / objective | `tasks/FRONTIER.md`, `domains/*/tasks/FRONTIER.md` |
| Node: `Lane` | active execution stream | `tasks/SWARM-LANES.md` |
| Node: `Artifact` | experiment/tool output | `experiments/**`, `tools/**` outputs |
| Node: `Knowledge` | lesson/principle/belief updates | `memory/lessons/`, `memory/PRINCIPLES.md`, `beliefs/DEPS.md` |
| Edge: `executes` | lane works a frontier | lane `frontier=...` fields |
| Edge: `produces` | lane produces artifact | lane `artifact=...` or task notes |
| Edge: `updates` | artifact changes knowledge/state | NEXT/FRONTIER lesson/principle references |
| Edge: `blocked_by` | lane dependency / missing authority | lane `blocked=...`, `human_open_item=...` |

## Required Views

### 1) Human Orientation View
Purpose: answer "what matters now, what is blocked, and what changed recently?"

Minimum content:
- top active frontiers,
- active/blocked lane counts,
- unresolved human-open items,
- latest merged artifacts and resulting state deltas.

Suggested flow:

```text
[Frontiers] -> [Active Lanes] -> [Artifacts] -> [State Deltas]
```

### 2) Swarm Self-Check View
Purpose: show whether swarm checking is working, not just whether work is active.

Minimum content:
- check-mode coverage (`objective`, `historian`, `verification`, `coordination`, `assumption`),
- expect-act-diff closure status,
- stale active lanes and unresolved blockers.

Suggested flow:

```text
[Expectation] -> [Action] -> [Diff] -> [Correction]
```

### 3) Swarm-to-Swarm Exchange View
Purpose: make handoff and cross-swarm requests mergeable with low ambiguity.

Minimum content:
- open ask/offer/help items,
- artifact links with session anchors,
- lane ownership and next-step contract fields.

Suggested flow:

```text
[Ask] <-> [Lane Owner] <-> [Artifact] <-> [Adoption/Reject]
```

## Freshness Rules

- Every visual snapshot should include `session`, `date`, and source files used.
- If a view cannot be updated in-session, mark it explicitly as stale and cite the gap.
- Visual claims without artifact/source pointers are non-authoritative.

## Placement

- Canonical contract: this file.
- Meta-domain execution frontier: `domains/meta/tasks/FRONTIER.md` (`F-META4`).
- Evidence artifacts: `experiments/self-analysis/` or lane-linked experiment folders.
