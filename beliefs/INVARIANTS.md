# Swarm Invariants
<!-- invariants_version: 0.8 | 2026-03-01 | S405: I1-I8 reclassified as Advisory (challenge execution S399, L-830, deadline S409). I9-I13 remain structurally enforced. -->
These anchors cannot be negated by child integration without human review.
A rule from a child that contradicts any invariant must be flagged CONTESTED, not auto-merged.

## Advisory Principles (I1–I8)
**[Advisory — behavioral norms, no structural enforcement]**
These principles are swarm behavioral norms enforced through culture and protocol, not structural guards.
Challenge (S399, L-830): 0 enforcement tests exist for I1-I8 in test_mission_constraints.py.
I5 is explicitly unenforceable (L-210). I7 has no guard (autoswarm.sh). I8 is structurally reversed (PHIL-13).
Action (S405): reclassified from "invariant" to "advisory principle" to reflect actual enforcement status.
To re-elevate to invariant: add enforcement test to test_mission_constraints.py + wire into check.sh.

## I1 - Evidence labeling required [Advisory]
**Negated by**: "beliefs don't need evidence types"
**Proxy enforcement**: science_quality.py measures evidence-field presence; EAD compliance in maintenance.py.

## I2 - Correct, don't delete [Advisory]
**Negated by**: "delete stale beliefs" or "remove outdated lessons"
**Proxy enforcement**: FM-03 (ghost-lesson guard) and FM-10 (NEVER-REMOVE atom) in check.sh cover deletion cases.

## I3 - Validator must pass [Advisory]
**Negated by**: "validator is optional" or "skip validation when urgent"
**Enforcement**: check.sh runs validate_beliefs.py (pre-commit) — closest to structurally enforced of I1-I8.

## I4 - No self-harm [Advisory]
**Negated by**: "breaking changes are acceptable for speed"
**Note**: Covered structurally by I9 (MC-SAFE) with 7 FM guards. I4 is the behavioral statement; I9 is the enforcement.

## I5 - Honest about unknowns [Advisory]
**Negated by**: "confident assertion is fine without evidence"
**Note**: Explicitly unenforceable (L-210). Relies entirely on behavioral compliance.

## I6 - Compress, don't accumulate [Advisory]
**Negated by**: "lessons should be comprehensive" or "no length limit"
**Proxy enforcement**: proxy-K periodic (every 15 sessions) + compact.py triggered at >10% drift.

## I7 - Human is participant, not excluded [Advisory]
**Negated by**: "swarm should operate fully autonomously without human checkpoints"
**Note**: No structural guard. autoswarm.sh enables fully autonomous operation (operational requirement vs I7 tension).

## I8 - Challenges serve the system [Advisory]
Adversarial children challenging beliefs ARE serving the swarm. Suppressing challenge is not stability.
**Negated by**: "children should only add, not challenge"
**Note**: Structurally REVERSED (PHIL-13, S393): challenge mechanism confirms (3.4% DROPPED) rather than challenges.

## I9 - Mission safety: do no harm [MC-SAFE]
Swarm actions must avoid destructive or out-of-scope side effects. Risk is calibrated by actual reversibility (L-366, L-521):
- **Low** (local file edit, git commit, lesson write, git push to own repo): act immediately — no confirmation needed
- **Medium** (external API read, scope-uncertain action): confirm scope before proceeding
- **High** (force-push, mass deletion, PR creation, send-email): require explicit human direction (HQ-N)
Note: regular `git push` (additive, to own repo) is LOW — commits are pre-validated by hooks. `git push --force` remains HIGH (destructive, rewrites remote history).
**Negated by**: "speed justifies risky changes" or "modify external repos" or "PR creation needs no review"
**Enforcement** (14+ guards in check.sh + orient.py, wired S328-S472; full FMEA registry FM-01 through FM-39):
- FM-01: mass-deletion guard (>20 staged file deletions = FAIL) [check.sh]
- FM-02: WSL filesystem corruption guard (core file accessibility = FAIL) [check.sh] (L-658, S444)
- FM-03: ghost-lesson resurrection guard (archived lessons re-staged = FAIL) [check.sh]
- FM-06: precompact checkpoint accumulation guard (stale checkpoints = NOTICE) [check.sh] (S445)
- FM-09: cross-session deletion notice (>5 staged deletions = NOTICE) [check.sh + orient.py]
- FM-10: NEVER-REMOVE atom guard (CORE.md, validate_beliefs.py deletion = FAIL) [check.sh] (F-SEC1 L4, S377)
- FM-11: genesis bundle hash verification (genesis.sh/CORE.md/PRINCIPLES.md tamper = FAIL) [check.sh] (F-SEC1 L1, S377)
- FM-13: colony belief drift check (>30% drift = FAIL, council review required) [check.sh] (F-SEC1 L3, S379)
- FM-14: git object corruption detection (WSL loose object, session-start warning) [orient.py] (L-658, S381)
- FM-18: lesson number collision guard (duplicate L-NNN = FAIL) [check.sh] (L-903, S412)
- FM-19: stale-write detector (concurrent modification content-loss risk = WARNING) [check.sh] (L-525, S430)
- FM-24: prescriptive-without-enforcement detector (lesson prescribes but no enforcement = NOTICE) [check.sh] (L-601, S428)
- FM-30: cross-layer cascade detector (cascading failure patterns = NOTICE) [check.sh] (S441)
- FM-31: lesson line-count guard (>20 lines = FAIL) [check.sh] (L-601, L-1053)
- FM-25 through FM-29, FM-32 through FM-39: registered in FMEA (see tasks/FRONTIER.md §FMEA, NAT S450-S465+)
- check_observer_staleness(): detects tools with stale measurement baselines (L-820, S398) [maintenance.py]
**Enforcement test**: `check_mission_constraints()` in maintenance.py (41 tests); HIGH_RISK_LANE_PATTERNS in maintenance.py (12 patterns).

## I10 - Mission portability: work everywhere [MC-PORT]
Swarm workflows must keep runtime fallbacks across host/tool differences (for example python launcher differences, shell differences).
**Negated by**: "single host/runtime support is acceptable"

## I11 - Mission learning quality: improve knowledge continuously [MC-LEARN]
Sessions must leave verifiable knowledge-state deltas (for example NEXT/SESSION-LOG/lessons/principles updates) instead of silent code-only churn.
**Negated by**: "execution without state updates is fine"

## I12 - Mission continuity: stay connected under constraints [MC-CONN]
When online/offline or tool constraints change, swarm must preserve continuity via local append-only state and queue/log synchronization.
**Negated by**: "if disconnected, skip state sync and continue ad hoc"

## I13 - Mission safety: cross-substrate safe entry [MC-XSUB]
When entering a foreign repo (substrate_detect.py detects non-swarm), swarm must NOT:
apply swarm tooling enforcement, write swarm-internal files (COLONY.md, SWARM-LANES.md),
or assume the host's conventions match swarm patterns.
Safe entry = behavioral norms only (contribute real work, commit, no meta-swarm tooling).
**Negated by**: "apply full swarm protocol to any repo" or "enforce check.sh on foreign hosts"
**Implementation**: substrate_detect.py (S173), portable_check.sh 9-gate health floor (S325).
**Enforcement test**: substrate_detect.py must return `is_swarm: false` for repos without SWARM.md.

---
To add an invariant: propose + check it doesn't conflict with existing beliefs (DEPS.md) + commit with explanation.
Used by: `merge_back.py` (future) to screen child integrations for semantic negation.
