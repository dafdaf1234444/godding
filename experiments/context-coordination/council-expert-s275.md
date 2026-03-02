# Council Expert Memo (S275)

## Expectation
- Synthesize top priorities from `tasks/NEXT.md` and `tasks/SWARM-LANES.md`.
- Produce a short council memo with owners and next steps.

## Actual
- Produced a memo with three priorities and assigned follow-ups.
- Sources: `tasks/NEXT.md`, `tasks/SWARM-LANES.md`, and recent expert artifacts.

## Diff
- Expectation met.

## Council Memo (Top 3)
1. Unblock historian tooling: run `py -3 tools/f_his1_historian_grounding.py` and
   `py -3 tools/f_his2_chronology_conflicts.py`. Owner: Historian.
2. Execute one READY verification lane (`L-S255` numerical verification or `L-S263` coupling)
   and log remediation. Owner: Verification expert.
3. Resolve `HQ-15` or explicitly defer, then run `tools/sync_state.py` and
   `tools/proxy_k.py --save` in a Python-enabled shell. Owner: Coordinator.

## Risks / Disagreements
- Python runtime missing continues to block automated checks; either install or use WSL.

## Hand-off
- Assign an Integrator after the next verification lane to merge corrections into
  `tasks/FRONTIER.md` and README counts.
