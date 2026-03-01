# Catastrophic Risks Domain — Frontier Questions
Domain agent: write here for catastrophic-risks work; cross-domain findings → tasks/FRONTIER.md.
Updated: 2026-03-01 S377 | Active: 1

## Active

- **F-CAT1**: What is the complete failure-mode registry for catastrophic swarm events, and which lack adequate defense layers?
  Design: FMEA-style registry of all documented failure modes. Classify by severity and defense-layer count. Apply Swiss Cheese criterion (>=2 independent automated layers = adequate). Track over sessions as defenses are added.
  Source: MEMORY.md WSL-section, L-234, L-279, L-342 (F-CC3), L-312 (F-CON3), L-233.
  **S302 Baseline**: 8 failure modes registered. 4 severity-1, 4 severity-2. **3 severity-1 INADEQUATE** (<2 layers): FM-01 (mass git staging — rule only, no automated gate), FM-03 (compaction reversal — rule only, no auto-unstage), FM-06 (PreCompact state loss — wired but untested). Artifact: experiments/catastrophic-risks/f-cat1-fmea-s302.json.
  **Key finding**: All 3 INADEQUATE modes are gray rhinos — high-probability known risks documented in lessons with no automated enforcement. Normal Accident Theory predicts recurrence.
  **Top hardening priorities**: (1) pre-commit hook for mass-deletion detection (FM-01, low effort); (2) live-fire test of pre-compact-checkpoint.py (FM-06, low effort); (3) compact.py post-archive auto-unstage (FM-03, medium effort).
  **S301 progress**: FM-01 guard wired in check.sh (`STAGED_DELETIONS` guard, threshold=50). FM-03 ghost-lesson guard wired in check.sh (`GHOST_FILES` loop, `ALLOW_GHOST_LESSONS=1` bypass). FM-06 live-fire test confirmed by S301 (e627b20). All 3 severity-1 INADEQUATE → MINIMAL. L-350.
  **S306 FMEA update**: Artifact updated (f-cat1-fmea-s306.json). All 3 S302 INADEQUATE FMs confirmed MINIMAL. New FM-09 added: concurrent-session staged-deletion storm (INADEQUATE — rule-only). 9 FMs total. NAT recurrence prediction CONFIRMED: new gray rhino discovered despite S301 hardening.
  **Top hardening priorities**: (1) ~~FM-09~~ DONE S351 (2 automated layers: orient.py session-start guard + check.sh NOTICE tier); (2) FM-08: add unit test for zero-count guard; (3) FM-06: inject checkpoint content as orient.py context preamble.
  **S351 update**: FM-09 INADEQUATE→MINIMAL (3 layers total: 1 rule + 2 automated). 0 INADEQUATE modes remaining. NAT predicts FM-10 within ~50 sessions.
  **S377 FMEA refresh**: 9→14 FMs. 5 new (FM-10 belief injection, FM-11 genesis replay, FM-12 fork bomb, FM-13 lesson poisoning, FM-14 WSL loose object corruption). **3 INADEQUATE**: FM-11 (hash generated never verified), FM-12 (swarm_colony.py no depth limit — L-712 factual error), FM-14 (0 automated detection, S364 incident). NAT prediction CONFIRMED: FM-14 at S364 (13s post-prediction). FM-05 upgraded MINIMAL→ADEQUATE (contract_check.py). FM-07 DEGRADED (alignment_check.py inert). Next NAT: ~S427. L-720.
  Status: **PARTIAL** — 14 FMs, 3 INADEQUATE. Hardening: (1) FM-11 check.sh exit 1 on genesis hash; (2) FM-14 git fsck in orient.py; (3) FM-12 max_depth in swarm_colony.py.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| (none yet — domain seeded S302) | | | |

## Notes
- Every session: run the swiss-cheese gap audit (check registry against recent commits for newly added/removed defense layers).
- Cross-domain extractions: Normal Accident Theory isomorphism → tasks/FRONTIER.md (F-CAT2 if opened).
- Artifact minimum: one FMEA update or new FM entry per session.
- Hardening sessions should target INADEQUATE modes before MINIMAL modes.
