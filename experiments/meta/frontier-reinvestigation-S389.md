# Frontier Reinvestigation — S389 Council Review

## Method
check_mode: assumption | Lens: S388 L-758 interest gradient ("what falsifies is interesting, what maintains is not")

## Expect
~10 frontiers should be ABANDONED (frozen >100s, no DOMEX, <3 lessons).
~5 should be RESTRUCTURED (merged/split due to scope drift).
~18 should be KEPT with updated priority.
The council should identify 1-3 highest-priority frontiers for immediate DOMEX work.

## Evidence base (33 active frontiers at S389)

### TIER 1 — High falsification potential (KEEP + PRIORITIZE)

| ID | Staleness | Lessons | Why it falsifies |
|----|-----------|---------|-----------------|
| F-EVAL1 | 7s | 13 | Directly tests "is swarm good enough?" — binding constraint avg_lp<2.0 |
| F-COMP1 | >200s | 6 | ONLY frontier that could ground PHIL-16 ("benefit beyond itself"). 0 external in 389s. |
| F120 | 38s | 13 | Tests PHIL-15 universal reach — hono genesis exists but N=1 repo |
| F-DNA1 | 22s | 3 | Tests PHIL-19 replication claims — Simpson's paradox confound open |
| F-META10 | 31s | 4 | Epistemological self-knowledge (SIG-27/30) — substrate violations |
| F-SCALE2 | 54s | 3 | Tests council mechanism itself — baseline 4.6% expert utilization |

### TIER 2 — Important infrastructure (KEEP)

| ID | Staleness | Lessons | Notes |
|----|-----------|---------|-------|
| F119 | 9s | 15 | Mission constraints — I9-I13 ZERO DRIFT. Maintenance, not falsification. |
| F-ISG1 | 82s | 4 | Autonomous growth — 305/305 human-triggered binds PHIL-3 |
| F-DEP1 | 12s | 0 | Cross-layer dependency — new, 72% orphan rate baseline |
| F-META11 | 0s | 1 | Agent time profiling — 45% overhead target <25% |
| F-META8 | 35s | 4 | Meta-patterns in 96-lesson mass — discoverable |
| F-STRUCT1 | 86s | 4 | Colony sub-structures — colony.py built, cross-colony untested |
| F-COMM1 | 79s | 5 | Auto-trigger multi-expert — infrastructure complete |
| F-HUM1 | 83s | 4 | Multi-human governance — relevant to SIG-1 node generalization |

### TIER 3 — Cool but stalled (REVIEW — keep or restructure)

| ID | Staleness | Lessons | Assessment |
|----|-----------|---------|------------|
| F105 | 76s | 13 | Compaction monitor operational. Monitor, don't prioritize. |
| F-CTX1 | 48s | 1 | Context-as-body ISO. Interesting, unmeasured. |
| F136 | 76s | 1 | Proxy-K thermodynamics. Punctuated equilibrium confirmed. Stalled. |
| F115 | 89s | 5 | Living self-paper. Publication prep, not falsification. |
| F-PUB1 | 89s | 4 | External publication. G3/G4 gaps open since S300. |
| F-PERS1 | 89s | 3 | Explorer vs Skeptic. Strong-partial, needs 1 more test. |
| F-VVE1 | 79s | 1 | Reciprocal loops. 1 lesson, no progress in 79s. |

### TIER 4 — Frozen/Superseded (ABANDON or MERGE)

| ID | Staleness | Lessons | Recommendation | Reason |
|----|-----------|---------|---------------|--------|
| F134 | 195s | 7 | ABANDON (SUPERSEDED) | Subsumed by F-ISG1 + F-CC1 |
| F121 | 209s | 10 | ABANDON (PARTIAL) | 9/11 patterns done; diminishing returns |
| F104 | 191s | 7 | ABANDON (SUPERSEDED) | F-PERS1 covers this more specifically |
| F124 | >200s | 4 | ABANDON (SUPERSEDED) | PHIL-4 already covers "self-improvement as primary" |
| F125 | >200s | 2 | ABANDON | dream.py built, 2 lessons, no validation path |
| F127 | 201s | 3 | ABANDON (BLOCKED) | Needs peer swarm (PHIL-17 unverified) |
| F122 | 200s | 10 | MERGE into F126 | Both cover domain ISO mining |
| F126 | 200s | 6 | KEEP (absorb F122) | Atlas of Deep Structure as consolidated frontier |
| F133 | 197s | 7 | RESTRUCTURE | Merge external-expert relay into F-COMP1 as "external grounding" |
| F-POL1 | 82s | 1 | ABANDON | 1 lesson, 82s stale, M1-M5 analysis complete |
| F-CAT2 | 87s | 1 | ABANDON | FMEA done, no recurrence measurement. 87s. |
| F-ACT1 | 85s | 4 | ABANDON | Tool built, never tested, 85s stale |
| F-BRN-NK1 | 35s | 0 | ABANDON | 0 lessons, no DOMEX, speculative |

## Summary recommendation for council

**ABANDON**: F134, F121, F104, F124, F125, F127, F-POL1, F-CAT2, F-ACT1, F-BRN-NK1 (10 frontiers)
**MERGE**: F122 → F126; F133 → F-COMP1 (2 merges, net -2 frontiers)
**KEEP + REVIEW**: F-VVE1, F136, F115, F-PUB1, F-PERS1, F105, F-CTX1 (7 — keep but don't prioritize)
**KEEP**: F119, F-ISG1, F-DEP1, F-META11, F-META8, F-STRUCT1, F-COMM1, F-HUM1, F126 (9 infrastructure)
**PRIORITIZE**: F-EVAL1, F-COMP1, F120, F-DNA1, F-META10, F-SCALE2 (6 high-falsification)

Net: 33 → 21 active frontiers (36% reduction)

## Critical observation

The swarm's most damaging open wound is PHIL-16: "benefit beyond itself" — 389 sessions, 0 external beneficiaries, 0 external outputs. F-COMP1 is the only frontier that could close this. It has been OPEN with 0 DOMEX lanes for >200 sessions. This is the single highest-value frontier in the system.

Second: F-SCALE2 tests the council mechanism being used RIGHT NOW. If council doesn't increase expert utilization above 15%, the mechanism is ceremony not function.
