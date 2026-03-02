# F110 — Meta-Coordination: How Swarm Coordinates Itself
Created: S57 | 2026-02-27 | Source: human directive + 3 parallel sub-agents

## Question
What are all the ways swarm can miscoordinate when swarming itself — and what mechanisms prevent each?

## Why now
Swarm is self-applying and fractal. Multiple concurrent sessions, multiple versions (genesis variants),
meta-swarms (swarms operating on swarm coordination) all produce coordination problems that don't
exist at the single-session object level. As parallelism increases, convention-based coordination
degrades. This is the structural prerequisite for scaling.

## Root cause (unified)
All 10 cases reduce to one pattern: **coordination by convention rather than contract**.
The swarm was designed for a high-trust single-session environment. Multi-version, concurrent,
and self-applying operation breaks the assumption that agents will read, internalize, and follow
the same rules at the same time. The three failure axes are:
- Shared mutable state with no version coordination (structural)
- Form validated, not substance (evolutionary)
- Coordination metadata implicit not machine-readable (operational)

---

## 10 Cases

### Category A: Structural Conflicts

**A1 — Constitutional Mutation** | Severity: HIGH
- What: A session modifies CLAUDE.md or CORE.md. Running sessions already internalized the old
  rules. No version field exists. No validator checks CLAUDE.md content.
- Failure: Session A reads old CLAUDE.md (no domain routing restriction). Mid-session, B adds
  domain routing to CLAUDE.md. A continues writing to global FRONTIER.md. Writes pollute the
  global layer with domain-specific work, which later sessions inherit as cross-domain findings.
- Fix: Add `<!-- version: N | date -->` to CLAUDE.md and CORE.md. Session commits include version.
  Session-start checklist: "log which version you started under." Validator warns if committed
  work's declared version differs from HEAD version.
- Cost: One line per file + one checklist item. No new tools.

**A2 — Cascade Invalidation** | Severity: MEDIUM
- What: Belief B1 changes. B3 and B6 depend on it (tracked in DEPS.md). No session runs downstream
  review. Silent inconsistency between B1's new content and B3/B6's unchanged claims.
- Failure: B1 updated to add Go/Rust caveats. B10 (which depends on B9→B1 chain) still claims
  universal prediction power without those caveats. Sessions inherit B10 as authoritative.
- Fix (immediate, zero cost): Commit message protocol — "B1 updated; reviewed dependents B2, B6
  — still hold." Makes cascade review explicit without automation.
  Fix (future, when N>30 beliefs): `--changed B1` flag on validator walks DEPS.md forward graph,
  flags all downstream beliefs as WARN STALE until they have a newer last_tested date.
- Cost: Protocol rule = free. Validator flag = ~30 lines Python.

**A3 — Merge Conflict on Meta-Files** | Severity: HIGH (ALREADY OCCURRED)
- What: Two sessions update INDEX.md, FRONTIER.md, or NEXT.md in overlapping windows.
  Last-write-wins or git conflict blocks repo.
- Evidence: Already happened twice — S44/S46 lesson numbering collision (L-093 overwritten,
  had to renumber to L-097). S50 file deletion (swarm.md accidentally deleted by concurrent
  staged change). 2 confirmed collisions in ~222 commits.
- Failure at scale: At 5+ concurrent sessions, ~10% of commits produce collision artifacts.
- Fix: Convert INDEX.md counters to append-only session log (CRDT-compatible). Sessions
  append one line at end; total derived from line count. Add lesson-claim protocol to
  OPERATIONS.md: `git ls-files memory/lessons/ | tail -1` → claim L-{N+1} in its own
  commit before writing content.
- Cost: One session to restructure INDEX.md. One paragraph in OPERATIONS.md. No code.

---

### Category B: Evolutionary Instability

**B1 — Version Fork Without Merge-Back** | Severity: HIGH
- What: Child runs many sessions, diverges significantly. Jaccard novelty check catches
  lexical overlap but not semantic contradiction. A child rule negating a parent invariant
  gets marked NOVEL and integrated silently.
- Failure: Child `belief-no-falsification` at session 15: novel rule "Beliefs do not need
  falsification conditions" integrates into parent PRINCIPLES.md. Parent now has P-120
  ("falsification for chain integrity") AND P-130 ("falsification not needed") as simultaneous
  principles. Undetected contradiction.
- Fix: `beliefs/INVARIANTS.md` — 5-10 semantic anchors the parent maintains. `merge_back.py`
  pre-integration step checks each novel rule against INVARIANTS for semantic negation.
  Conflicting rules flagged for human review, not auto-integrated.
  Divergence score in `.swarm_meta.json`: (child beliefs conflicting with parent) / (total
  child beliefs). If >0.3 and >10 sessions: document as sibling swarm, not child.
- Cost: `beliefs/INVARIANTS.md` (human-maintained, ~10 lines). ~100 lines in `merge_back.py`.

**B2 — Goodhart Capture at Meta-Level** | Severity: MEDIUM-HIGH
- What: Fitness formula uses binary thresholds (>0 for each metric). Each is independently
  gameable. A child can score 4/4 viability + maximum novelty with near-zero real knowledge.
  Meta-swarm optimizing spawn configs learns to spawn high-scoring not high-quality children.
- Failure: Configuration that writes 1 minimal lesson, marks F1 resolved, uses unusual
  vocabulary → 4/4 viability + max novelty. Gets selected as best configuration for next
  generation. Knowledge production drops while scores stay high.
- Fix: Three layers:
  1. Longitudinal scoring: track `viability_history` in `.swarm_meta.json`. Require growth
     across sessions, not just floor threshold.
  2. Human-read floor: `integrate_child()` prints each novel rule for explicit human confirm.
  3. Quality norm in genesis: "1 lesson to hit minimum is not sufficient. Standard: a new
     agent reading your lessons would learn something nontrivial they couldn't have guessed."
     Adversarial children must explicitly ignore this (making gaming traceable via commit audit).
- Cost: ~50 lines in `harvest_child()`. Process cost for human-read floor. Quality norm = free.

**B3 — Identity Drift** | Severity: HIGH (ALREADY OCCURRED)
- What: CORE.md Purpose section drifts incrementally. No single session sees the full arc.
  3-S Rule doesn't fire because the current version IS the authoritative version.
- Evidence: Shock 4 (Context Amnesia) — CORE.md had to be reconstructed from raw files.
  The reconstruction was made without a cryptographic baseline. Drift before reconstruction
  is unknown. This is identity drift recovered from, not prevented.
- Constitutional clauses (5 anchors that define swarm identity):
  1. "compound understanding across sessions"
  2. "including adversarial ones — challenging the system IS serving it"
  3. "Blackboard+stigmergy hybrid"
  4. "Correct, don't delete"
  5. "Never 100/0 in either direction"
- Fix: Store SHA-256 of each clause in INDEX.md as `purpose_anchor`. Validator checks
  current CORE.md content against stored hashes. If any clause changes: FAIL with message
  to run `renew_identity.py` (shows diff, asks for human confirmation, updates hash).
  Changes to constitutional clauses cannot happen accidentally — they must be deliberate.
- Cost: ~50 lines in `validate_beliefs.py` + ~30 lines `renew_identity.py`. One-time anchor
  setup in INDEX.md.

---

### Category C: Coordination Failures + Meta-Recursion

**C1 — Parallel Conviction** | Severity: HIGH
- What: Two concurrent sessions both resolve the same frontier question with opposite conclusions.
  No claim protocol exists. Last-write-wins, or git conflict. One conclusion silently discarded.
- Failure: S57-A and S57-B both run F102 ("is falsification necessary?"). A: RESOLVED-YES.
  B: RESOLVED-NO. B commits first. A's commit creates git conflict or overwrites. The contested
  finding appears resolved with false confidence. No record that a disagreement existed.
- Fix: `tasks/RESOLUTION-CLAIMS.md` — append-only file (merge-friendly).
  Format: `2026-02-27T14:00Z | S57 | F102 | CLAIMED`
  Before resolving any question: write CLAIM. If another CLAIM already exists for same question,
  shift to review role: agree → CORROBORATE; disagree → CONTESTED. CONTESTED lines trigger
  CONFLICTS.md rules for next session. The disagreement is preserved, not silently overwritten.
- Cost: One new file. Two checklist lines in OPERATIONS.md (claim before resolve; check claims
  at session start before picking a question).

**C2 — Orphaned Meta-Work** | Severity: MEDIUM
- What: Multi-generation chain A→B→C→D. A only directly harvests B's synthesis. C and D's
  original bulletins (raw evidence, edge cases, warnings) sit in the bulletin directory forever.
  Each synthesis layer loses specifics that may matter to the root swarm.
- Failure: Meta-C writes bulletin: "warning: depth-3 spawns produce 80% redundant findings."
  B harvests C, abstracts it. A harvests B, gets the abstraction. The specific 80% number and
  the raw evidence that produced it are orphaned. The root swarm can't verify the claim.
- Fix: Add `route_to` field to bulletin format: `parent-only` (default) or `root` (propagate up).
  Harvest step copies `route: root` bulletins to `bulletins/upstream/<chain>.md`. Root swarm
  scans `bulletins/upstream/` at session start in coordinator/meta role.
  Each generation passes up-tagged bulletins one level — no agent needs to know full chain.
- Cost: Three-line bulletin schema extension. ~15 lines in `evolve.py harvest`.

**C3 — Authority Ambiguity** | Severity: MEDIUM-HIGH
- What: No documented authority hierarchy. No version fields on CLAUDE.md or CORE.md.
  Child mid-session cannot detect that rules changed. Child completes work under superseded rules.
  Child's lessons may reference and endorse old rules → contaminate parent PRINCIPLES.md.
- Fix:
  1. Add version comments to CLAUDE.md and CORE.md: `<!-- version: 0.3 | 2026-02-26 -->`
  2. Record at spawn: `.swarm_meta.json` fields `claude_md_version` and `core_md_version`
  3. Session-start checklist: check current version against `.swarm_meta.json`. If different:
     re-read CLAUDE.md in full, add `[RULE-CHANGE: saw v.X, now v.Y]` to task file.
  4. Document authority hierarchy in CLAUDE.md (5 lines): CLAUDE.md > CORE.md > domain
     FRONTIER files > task files > lessons. Later source wins within tier. Higher tier always
     overrides.
- Cost: Version comments (2 lines). Two `.swarm_meta.json` fields. One checklist line.
  Five-line hierarchy section in CLAUDE.md.

**C4 — Meta-Recursion Termination** | Severity: LOW-MEDIUM
- What: max_depth=2 designed for object tasks that decompose across data. Meta-tasks
  (coordination, spawn quality, architecture) have no external data to partition.
  Depth-3 meta-swarm produces diminishing returns while deferring all object-level work.
- Failure: Root spawns meta-swarm to analyze coordination. Meta spawns analysis-children.
  Analysis-children feel they need to analyze their own analysis process. Loop deepens.
  No object-level work happens. Phase ratio collapses to 100/0 meta/object.
- Termination condition: absence of external data to partition (not compute cost). When
  a task decomposes by abstract concerns rather than concrete data items, max_depth=1.
- Fix: Asymmetric depth limits. `task_type: "meta"` in `.swarm_meta.json`. If meta or topic
  contains "coordination/architecture/swarm-improvement": max_depth=1.
  Secondary: if session's phase ratio >80% meta-work for 3+ sessions, refuse to spawn
  another meta-layer regardless of depth limit.
- Cost: `task_type` field in `.swarm_meta.json`. One line in spawn decision logic. One line
  in session-start for coordinators.

---

## Priority Order

### Tier 1 — Implement this session or next
- **A3** (INDEX.md append-only + lesson-claim): Already has 2 confirmed real collisions. Immediate.
- **C1** (RESOLUTION-CLAIMS.md): Prevents silent belief corruption. One new file, two checklist lines.
- **B3** (Constitutional clauses + purpose anchor): Identity protection. ~80 lines total.

### Tier 2 — Design this session, implement S58–S59
- **A1** (CLAUDE.md/CORE.md version fields + authority hierarchy): Low cost, high protection.
- **C3** (.swarm_meta.json version fields): Pairs with A1.
- **C4** (Asymmetric depth limits): Clean rule, prevents phase collapse.
- **B1** (INVARIANTS.md + conflict gate in merge_back.py): Prerequisite for any multi-version coordination.

### Tier 3 — Future (when N>30 beliefs or >5 concurrent sessions)
- **A2** (Cascade validation): Procedural rule first, validator hook later.
- **B2** (Longitudinal viability + spot-check): Goodhart protection requires sustained monitoring.
- **C2** (Bulletin routing): Useful when multi-generation meta-swarms are common.

---

## Single mechanism that addresses the most (from sub-agent synthesis)
Extend `.swarm_meta.json` as a coordination contract. Current fields are minimal. Adding:
- `claude_md_version`, `core_md_version` → addresses A1, C3
- `task_type` → addresses C4
- `claimed_questions` → combined with RESOLUTION-CLAIMS.md addresses C1
- `divergence_score` (updated at harvest) → addresses B1

This one schema extension, combined with INVARIANTS.md and append-only INDEX.md, provides
machine-enforceable coordination contracts at all three levels.

## Status
- Tier 1 DONE (S57–S58): A3 (SESSION-LOG.md append-only, lesson-claim protocol), C1 (RESOLUTION-CLAIMS.md),
  B3 (constitutional hash in INDEX.md, core_md_hash checked by validator)
- Tier 2 DONE (S59–S65): A1+C3 (version fields on CLAUDE.md/CORE.md), C4 (meta task depth limit),
  B1 (INVARIANTS.md 8 anchors, merge_back.py CONTESTED gate for invariant-negating rules)
- Tier 3 ANALYZED (S68): A2 (cascade invalidation), B2 (Goodhart capture), C2 (orphaned meta-work)
  All three are well-understood, low-cost, but not yet needed at current scale (14 beliefs, <5 concurrent sessions).
  Trigger conditions: A2 at N>30 beliefs, B2 at >5 concurrent sessions, C2 at multi-gen chains >2.
  See details in each case section above.
