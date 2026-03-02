# Info-Flow Routing Map - S257
Date: 2026-02-28
Scope: translate general information flow into expert-swarm utilization.

## Expect / Actual / Diff
- Expect: map core flow surfaces, define a routing table from flow signals to expert roles, and wire docs + frontier evidence.
- Actual: routing table + triggers defined; documented in `docs/EXPERT-SWARM-STRUCTURE.md` and recorded for F-IS7.
- Diff: expectation met.

## Core flow surfaces (observed)
- Human signals -> `memory/HUMAN-SIGNALS.md` -> patterns -> `memory/PRINCIPLES.md` / `beliefs/PHILOSOPHY.md`.
- Lanes + experiments -> artifacts -> domain frontiers -> `tasks/NEXT.md` synthesis.
- Lessons -> principles -> `memory/INDEX.md` -> orient/maintenance routing.
- Expect/actual/diff -> correction loops (`memory/EXPECT.md`, F-CTL2).

## Router table (default dispatch)
| Flow signal | Primary expert | Companion experts | Output target |
| --- | --- | --- | --- |
| Human signal or ambiguous prompt | Idea Investigator | Historian, Skeptic | Frontier candidate + dispatch plan |
| Experiment/artifact without frontier update | Integrator | Checker | Frontier update + evidence link |
| Domain frontier stalled (READY > 1 session) | Domain Expert | Skeptic | Artifact + frontier update |
| Tool/maintenance gap | Expert Creator | Coordinator | Tool change + lane dispatch |
| Claim drift or numeric mismatch | Reality-check / Numerical-verify | Historian | Corrections in README/NEXT/FRONTIER |

## Triggers
- Active lane missing `flow_out` -> spawn Integrator to close the loop.
- READY lane stale >1 session -> Coordinator reassigns or closes with explicit `next_step`.
- Missing `flow_in`/`flow_out` tags -> run a flow-tagging pass before execution.

## Next
- Tag 5-10 active lanes with `flow_in`/`flow_out`.
- Run `tools/info_flow_map.py` (or a PowerShell fallback) and summarize missing tags.
