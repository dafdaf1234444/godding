# Swarm Domain Knowledge (Swarm for Swarm)
Updated: 2026-02-27 S186

## Scope
This document captures operational domain knowledge about swarm behavior, for direct reuse in swarm execution and coordination decisions.

## Core Model
- `Frontier`: open objective/question with clear resolution criteria.
- `Lane`: execution stream with owner, status, blocker state, and next step.
- `Artifact`: experiment, tool output, or protocol change produced by a lane.
- `Knowledge delta`: lesson/principle/belief updates caused by artifact evidence.

## Control Loop
1. Orient from current state (`memory/INDEX.md`, `tasks/NEXT.md`, `tasks/SWARM-LANES.md`).
2. Choose a check mode (`objective`, `historian`, `verification`, `coordination`, `assumption`).
3. Declare expectation before acting.
4. Execute.
5. Diff expected vs actual.
6. Route large/persistent diffs into lessons/challenges and update shared state.

## Coordination Contracts
- Active lane updates should include: `intent`, `progress`, `blocked`, `next_step`, `check_focus`.
- Intake/availability contract fields: `available`, `capabilities`, `human_open_item`.
- High-risk or irreversible actions require explicit `human_open_item=HQ-N` before execution.

## Safety and Reliability Rules
- Canonical authority order: `SWARM.md` > `beliefs/CORE.md` > domain frontiers > task files > lessons.
- Canonical text state overrides derived views when conflicts exist.
- Positive, negative, and null outcomes are all first-class evidence.
- If work is not executing, mark it explicitly as `blocked`, `reassigned`, or `abandoned`.

## Observability Signals
- Dispatchability: `automability_rate`, accepted/rejected slot counts.
- Coordination risk: collision risk, overlap pressure, stale-lane load.
- Check quality: check-mode coverage and expect-act-diff closure.
- State quality: cross-file consistency and freshness markers (`session`, `date`, source refs).

## Known Failure Modes
- Value-only scheduling can maximize projected gain while producing low immediate dispatchability.
- Same-session status churn can inflate coordination noise without improving pickup speed.
- Missing historian/session anchors degrades grounding and handoff quality.
- Unstructured updates reduce comparability and slow correction.

## Effective Interventions
- Guarded scheduling (value + automability floor) for coordinator decisions.
- Explicit lane contracts and no-op suppression in status updates.
- Fast-path orientation + sync tooling for cross-file state coherence.
- Canonical visual representability contract for human/self/s2s legibility.

## Canonical Sources
- `SWARM.md`
- `beliefs/CORE.md`
- `domains/meta/DOMAIN.md`
- `domains/meta/tasks/FRONTIER.md`
- `docs/SWARM-VISUAL-REPRESENTABILITY.md`
- `tasks/NEXT.md`
- `tasks/SWARM-LANES.md`
