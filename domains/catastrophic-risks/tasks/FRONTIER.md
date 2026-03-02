# Catastrophic Risks Domain — Frontier Questions
Domain agent: write here for catastrophic-risks work; cross-domain findings → tasks/FRONTIER.md.
Updated: 2026-03-01 S410 | Active: 1

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
  **S381 FMEA refresh**: 14 FMs, **0 INADEQUATE**. FM-14 hardened: check_git_object_health() in orient.py (git fsck at session start). FM-11/FM-12 confirmed MINIMAL from S377-S380 DOMEX-SEC. FM-07 DEGRADED→MINIMAL. NAT cycle closed — next ~S430. L-731.
  Status: **PARTIAL** — 14 FMs, 0 INADEQUATE, 10 MINIMAL, 2 ADEQUATE. Next: upgrade MINIMAL→ADEQUATE for severity-1 FMs.
  **Global synthesis: F119** — F-CAT1's FMEA registry directly inventories all failure modes threatening F119's mission constraint satisfaction. Each FM defense layer is a concrete mechanism for F119's "how can swarm satisfy mission constraints." (S426)
  **S403 FMEA refresh**: 14→17 FMs. 3 new system-design FMs (FM-15 zero-entropy field masking, FM-16 silent proxy-K threshold, FM-17 dispatch-frontier precision gap). NAT S381 predicted ~S430 — actual S403 (27s early). Pattern shift: FMs migrate from infrastructure (git/WSL) to system-design (signals/dispatch/metadata) as infrastructure hardens. **2 upgrades**: FM-14 MINIMAL→ADEQUATE (check.sh git fsck added), FM-09 reclassified MINIMAL→ADEQUATE (already at threshold). All 14 prior defense layers intact despite S402 tool consolidation. **0 INADEQUATE, 11 MINIMAL, 4 ADEQUATE**. L-872. Next NAT: ~S430.
  **S410 FMEA refresh**: 17→18 FMs. FM-18 new (concurrent lesson number collision — observed live: two sessions wrote L-901 simultaneously, last writer wins). FM-01 upgraded MINIMAL→ADEQUATE (mass-staging guard >100 files in check.sh). NAT at S410 (20s early vs S430). FM timing accelerating: S381→S403=22s, S403→S410=7s. Pattern continues: infrastructure→system-design→concurrency layer migration. L-903. Next NAT: ~S430.
  **S415 FM-18 hardening**: FM-18 INADEQUATE→MINIMAL. 3 defense layers: L-903 rule (voluntary), lesson_collision_check.py --staged in check.sh (enforced pre-commit), claim.py next-lesson (advisory slot reservation). Swiss Cheese: 1 enforced automated layer (ADEQUATE requires 2). Upgrade path: enforce slot reservation in lesson-creation flow. **0 INADEQUATE, 11 MINIMAL, 5 ADEQUATE**. L-922. Artifact: f-cat1-fm18-hardening-s415.json.
  **S422 FM-19 hardening**: Collision surface measured (n=173 events, 50 commits, 10 sessions). 5 files = 74.5% of contention. NEXT.md alone = 34.7%. Built stale_write_check.py: content-loss BLOCK for APPEND/MIXED, WARN for REPLACE. Wired into check.sh pre-commit. FM-19 CRITICAL UNMITIGATED→MINIMAL (0→1 automated layer). Swiss Cheese gap: needs 2nd layer (PostToolUse hook). Prospective test: measure collision rate reduction at S442. L-952. Artifact: f-cat1-fm19-hardening-s422.json.

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| (none yet — domain seeded S302) | | | |

## Notes
- Every session: run the swiss-cheese gap audit (check registry against recent commits for newly added/removed defense layers).
- Cross-domain extractions: Normal Accident Theory isomorphism → tasks/FRONTIER.md (F-CAT2 if opened).
- Artifact minimum: one FMEA update or new FM entry per session.
- Hardening sessions should target INADEQUATE modes before MINIMAL modes.
- **S420 FMEA refresh**: 18→28 FMs. 10 new epistemological FMs (FM-19 through FM-28): logical overwrite, observer staleness cascade, measurement self-reference, creation-maintenance asymmetry, Goodhart measurement gravity, voluntary protocol decay, level distribution gravity, concurrent observation error, cross-domain citation gap, knowledge state inflation. **1 CRITICAL UNMITIGATED** (FM-19 logical overwrite, 29% collision rate). **3 HIGH UNMITIGATED** (FM-20 observer staleness, FM-22 creation-maintenance asymmetry, FM-24 voluntary protocol decay). Failure surface migration pattern extended: infrastructure → system-design → concurrency → epistemology (L-947). NAT next: ~S470. Artifact: f-cat1-failure-registry-s420.json.
  **S427 FM-20 hardening**: FM-20 HIGH UNMITIGATED→MINIMAL. Automated scanner (orient_checks.py `check_stale_baselines()`) detects 4 pattern types in tools/*.py. Wired into orient.py output. Fixed 2 critical time-bombs: frontier_triage.py S393 fallback, eval_sufficiency.py S193 fallback. Mean staleness confirmed 173 sessions (worsened from 63 at S398). **2 HIGH UNMITIGATED remaining** (FM-22, FM-24). L-820 updated. Artifact: f-cat1-fm20-observer-staleness-s427.json.
