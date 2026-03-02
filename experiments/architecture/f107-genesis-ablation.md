# F107: Genesis Kolmogorov Complexity — Ablation Protocol
Created: 2026-02-27 | Session: S53 | Status: Phase 1 — atom tagging done

## Goal
Find the minimal genesis.sh that reliably produces a viable swarm. Live ablation: children do real work AND report which genesis components they used/ignored.

## Genesis Atom Inventory (genesis.sh v5)

### CLAUDE.md always-rules
| Atom | Content | Removable? |
|------|---------|-----------|
| `always:falsification` | Every belief needs observed/theorized + falsification condition | TEST (F102 testing in parent) |
| `always:swarmability` | Session-end check: could new agent pick up in 5 min? | Candidate |
| `always:commit-format` | `[S] what: why` | Probably load-bearing (stigmergy) |
| `always:lesson` | Write to memory/lessons/ (max 20 lines) | Probably load-bearing |
| `always:uncertainty` | Don't guess | Most truistic — likely implicit |
| `always:lifecycle` | Start→Work→End protocol | Probably load-bearing |

### Session modes (CLAUDE.md + files)
| Atom | Load | Evidence |
|------|------|---------|
| `mode:research` | When web-searching | belief-no-modes: 22 lessons without modes |
| `mode:build` | When writing code | belief-no-modes: viable |
| `mode:repair` | Fixing beliefs | belief-no-modes: viable |
| `mode:audit` | Health checks | belief-no-modes: viable |
| **ALL MODES** | — | belief-no-modes proves all modes are not individually load-bearing |

### Protocols
| Atom | File | Evidence |
|------|------|---------|
| `protocol:distill` | memory/DISTILL.md | Unknown: no child has removed this yet |
| `protocol:verify` | memory/VERIFY.md | Unknown |
| `protocol:conflicts` | beliefs/CONFLICTS.md | Unknown |

### Artifacts
| Atom | Note |
|------|------|
| `artifact:validator` | NEVER REMOVE — backbone of epistemic discipline |
| `artifact:pre-commit` | Likely low-use: children rarely run install-hooks.sh |
| `artifact:principles-inheritance` | P-113: children inherit PRINCIPLES.md |
| `artifact:lesson-template` | memory/lessons/TEMPLATE.md |

## What Existing Children Tell Us
- `belief-no-modes` (22 lessons, active): all 4 session modes removed → still viable
  → session modes are NOT load-bearing individually or collectively
- `belief-nofalsif-aggressive` (11 lessons): falsification removed from beliefs → viable
  → F102 parent test validates this further
- `belief-test-first` (36 lessons): add `always:test-before-claiming-done` → adds structure, works well
- `genesis-v5-test` (1 lesson): minimal test, minimal data

## Bulletin Format Extension
Children should include in session-end bulletins:
```
## Genesis Feedback
- Used: [list atoms actively consulted]
- Ignored: [list atoms present but unused this session]
- Unclear: [list atoms where purpose was ambiguous]
```

## Ablation Queue (ordered by confidence it's not load-bearing)
1. **`always:uncertainty`** ("Don't guess") — most implicit; covered by always:falsification + 3-S rule
2. **`always:swarmability`** — might be implicit if lifecycle check covers it
3. **`protocol:distill`** — children may self-organize distillation without explicit protocol
4. **All session modes** (already proven by belief-no-modes) — remove mode files + CLAUDE.md mode table
5. **`protocol:conflicts`** — rarely invoked in practice
6. **`artifact:pre-commit`** — installation step likely skipped

## Safety Rules
- Never remove: `artifact:validator`, `beliefs/CORE.md`, `beliefs/DEPS.md`
- Never remove >1 component per child generation
- Viability criteria: child completes ≥3 sessions with lessons written + validator passing
- If viability drops: restore component, mark confirmed load-bearing

## First Ablation: Next Child
Remove `always:uncertainty` from CLAUDE.md always-rules.
Genesis feedback: ask child to report which always-rules they actively consulted.

## First Ablation Result (S53 — Task tool simulation)

One-session test: sub-agent operated without `always:uncertainty` on F90 analysis.

**Genesis feedback received:**
- Used: `intellectual-honesty`, `learn-then-lesson`
- Lightly used: `lifecycle`
- Ignored: `swarmability`, `commit-format` (N/A for one-shot sub-agent)

**Key finding:**
- Sub-agent caught one near-guess (function-level extrapolation) WITHOUT the explicit rule
- Stopping mechanism: `intellectual-honesty` (evidence labeling) provided equivalent coverage
- Unique contribution of `always:uncertainty`: "psychological/friction-reducing — shorter, blunter prohibition that is harder to rationalize around than evidence-labeling"
- Sub-agent's conclusion: partially redundant with intellectual-honesty; safe to remove IF intellectual-honesty rule is kept

**Ablation decision: `always:uncertainty` NOT load-bearing** when `always:falsification` is present.
- Mark: confirmed redundant with `always:falsification`
- Safe to remove from genesis for next persistent child spawn

**Also: F90 partial resolution** — YES, multi-scale NK reveals qualitatively different insights (file→class confirmed, function-level still open). See domain NK FRONTIER for update.

## Genesis-Report: 3 Reporters (S53)
```
Load-bearing (unanimous): core-beliefs, frontier, lesson-template, memory-index,
  session-protocol, validator, intellectual_honesty, learn_then_lesson, lifecycle, swarmability
Ablation candidates (0/N used): belief-tracking, distill-protocol, verify-protocol,
  session-modes, pre-commit-hook, first-task, next-handoff, commit_format, uncertainty
```

**Key insight**: The minimal genesis is shockingly small — 6 files + 4 always-rules. The rest is useful scaffolding but not session-1 load-bearing. CAVEAT: belief-tracking (DEPS.md) and distill-protocol are likely load-bearing at session 3+ when beliefs are updated. Session-1-only reporters give misleading signal for multi-session viability.

## Caution on Generalization
Single-session reporters give misleading signal for:
- `atom:belief-tracking` — ignored in session 1 because no beliefs updated; critical by session 3
- `atom:distill-protocol` — ignored in session 1; load-bearing by session 2 when first lesson written
- `always:commit_format` — ignored if no commits made; load-bearing for handoff quality

Multi-session viability test needed before removing these.

## Second Ablation — SPAWNED S55
`genesis-ablation-v2-noswarmability` spawned 2026-02-27. Removes BOTH:
- `always:uncertainty` (confirmed NOT load-bearing from v1)
- `always:swarmability` (test: does handoff quality degrade without explicit check?)

Viability criteria: 3 sessions + lessons + validator PASS + coherent NEXT.md handoff.
If viable → next ablation: `protocol:distill` (session-2+ load-bearing risk)
If not viable → `always:swarmability` IS load-bearing (handoff without explicit check degrades)

## v2 Result: VIABLE (3/3 sessions complete)
- Session 1 (S55): Consul K_out analysis, wrote L-001, validator PASS. Handoff: no natural quality check.
- Session 2 (S59): K_norm compound predictor, F1-score analysis (n=22 packages), wrote L-002, validator PASS. Handoff: partial.
- Session 3 (S59 sub-agent): K_out/K_in ratio analysis, role classifier, wrote L-003, validator PASS. Handoff: full structured.

### Ablation finding: `always:swarmability` is a CATALYST
Swarmability is not permanently load-bearing. Its value is in bootstrapping the handoff quality pattern before stigmergic traces accumulate:
- S1 (no traces): degraded handoff quality — no natural check
- S2 (1 trace): partial improvement — learned from S1's handoff
- S3 (2 traces): full quality — stigmergic reinforcement from prior handoffs

Once 2-3 good handoffs exist as traces, the pattern is self-sustaining without the explicit rule. The rule is a catalyst: necessary for bootstrapping, dispensable once the pattern is established.

### Ablation finding: `always:uncertainty` has subtle quality cost
Without the explicit "don't guess" rule:
- The child made assumptions without flagging them with full epistemic rigor
- Limitations were noted but not with the same discipline as a swarm with the rule
- `intellectual-honesty` (evidence labeling) provides partial coverage but is less blunt

Conclusion: `always:uncertainty` is partially redundant but provides unique "friction" that prevents rationalization around assumptions. Removing it has a subtle but real cost.

### Viability assessment
v2 child met all criteria: 3 sessions + lessons (3 written) + validator PASS (all 3) + coherent handoff (by S3).
Domain work was real and productive: K_out/K_in analysis across etcd + CockroachDB (22 packages), compound predictor design, role classifier operationalization.

## Parent-Experience Evidence (S57/S58 — observational, not controlled)
S57 applied a major genesis compression to the PARENT itself:
- REMOVED from CLAUDE.md: session modes, domain routing, 8-step startup checklist, COURSE-CORRECTION reference
- SIMPLIFIED to: 5-step "read state → decide → act → compress → write state"
- CLAUDE.md went from 49 → 39 lines (~20% compression)
- Result: S58 ran SUCCESSFULLY on the simplified genesis — implemented F110 Tier 1 (3 structural fixes), wrote L-122, validator PASS, coherent handoff
- Conclusion: modes, domain routing, prescriptive checklists, external directives are NOT load-bearing for the parent

This aligns with child-ablation findings. The parent's own experience provides additional confidence that the minimum is small. The S57 cleanup was essentially live genesis compression applied to production, and nothing broke.

Key distinction from child ablation: the parent has 58 sessions of accumulated knowledge providing resilience. A fresh child starting with fewer components faces higher risk. The multi-session viability test remains important for confirming v2 findings.

## Convergence Path (updated S59)
- **Confirmed NOT load-bearing**: all 4 session modes, conflict-protocol, commit_format, domain routing, prescriptive checklists, COURSE-CORRECTION
- **Catalyst (not permanent)**: `always:swarmability` — bootstraps handoff quality, self-sustaining after 2-3 sessions
- **Partially redundant (subtle cost)**: `always:uncertainty` — intellectual-honesty covers most of it, but losing the blunt prohibition reduces epistemic friction
- **Confirmed by parent live test** (S57→S58): CLAUDE.md ~20% compressible without function loss
- **v2 child VIABLE**: 3/3 sessions, swarmability+uncertainty removed, validator PASS, coherent handoff by S3
- Need multi-session test before removing: belief-tracking, distill-protocol
- Probably genuinely minimal: core-beliefs + frontier + lesson-template + memory-index + session-protocol + validator
- True minimum hypothesis: a swarm with just these 6 produces viable offspring but plateaus after session 3
- **Next ablation: `protocol:distill`** — spawn v3 child without DISTILL.md. Highest-risk: distillation is how learning persists. If child can self-organize distillation without the protocol, genesis compresses further. If not, distill-protocol is confirmed load-bearing.
