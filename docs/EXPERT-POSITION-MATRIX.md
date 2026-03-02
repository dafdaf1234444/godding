# Expert Position Matrix
Updated: 2026-02-28 S306 | 48 personalities × 6 tiers

## Flow Model
Signal → T0:Guard → T1:Orient → T2:Execute → T3:Validate → T4:Compress → T5:Meta → State
Each tier chains to the next. Skip a tier only with explicit reason in lane row.

---

## T0 — Guardians (fire first, block unsafe progress)
Trigger: session start, destructive intent detected, mass-deletion signal.
Exit product: safety verdict (proceed / halt / gate on human).

| Expert | Key trigger | Output | Downstream |
|--------|------------|--------|-----------|
| conflict-expert | ACTIVE lane scan, belief change | Conflict audit JSON | Affected lane owners |
| danger-expert | Destructive intent in NEXT | Danger audit, human_open_item | Human queue |
| git-expert | Untracked file buildup, hook status | Git-status artifact, remediation checklist | Commit queue |
| contamination-investigator | MEDIUM+ contamination signal | Decontamination report, scoped tags | Frontier, domain experts |

---

## T1 — Orienters (classify and route incoming signal)
Trigger: new session, human signal, ambiguous prompt, stale orientation.
Exit product: dispatch plan (which T2 expert fires next, with what scope).

| Expert | Key trigger | Output | Downstream |
|--------|------------|--------|-----------|
| historian-expert | Anti-repeat check needed | Historical grounding artifact | Lane dispatch |
| info-collector-expert | Session start, handoff prep | Info report (key changes, blockers) | Next-session node |
| idea-investigator | Ambiguous idea received | Falsifiable-claim restatement, expert lanes | Skeptic, Domain Expert |
| expert-classifier-expert | Routing gap found, READY lane unassigned | Classification table (signal→expert→rationale) | Expert dispatch system |
| command-classification-expert | Human command signal received | Classification table (phrase→intent→action) | Routing system |
| jobs-finder-expert | No clear direction, NEXT scan | 5–10 job candidates, top 3 dispatch-ready | Lane dispatch |
| council-expert | Multi-expert coordination needed | Council memo (priorities, risks, next roles) | Expert dispatchers |
| opinions-expert | Stalled frontier, multiple interpretations | Opinion memo (3–5 stances + "change mind" tests) | Council Expert |
| expectation-expert | Major experiment queued | Prediction memo with confidence score | Council, genesis |
| explorer | Research phase, frontier resolved | 2 new sub-questions per resolution | Idea Investigator |

---

## T2 — Executors (produce the primary artifact)
Trigger: T1 dispatch plan complete.
Exit product: concrete artifact with expect/actual/diff (code, experiment JSON, report).

| Expert | Key trigger | Output | Downstream |
|--------|------------|--------|-----------|
| domain-expert | Domain frontier open, dispatched | Artifact + frontier update + isomorphism | Generalizer, Synthesizer |
| builder | Task with binary pass/fail test | Committed code/script | Domain experts |
| researcher-expert | High-value frontier research question | Research mapping with source metadata | Frontier validation |
| dream-expert | No directed expert available | DREAM-HYPOTHESIS entries, F-NNN candidates | Domain experts, Skeptic |
| fun-projects-expert | Ambiguous direction, playful intent | 2–3 project briefs in experiments/fun/ | Domain experts, Builder |
| action-expert | Proxy-K drift, maintenance DUE | ACTION-BOARD refresh, coordinator lanes | Domain experts, dispatch |

---

## T3 — Validators (check, challenge, verify T2 artifacts)
Trigger: T2 artifact produced.
Exit product: pass/fail verdict with evidence; null result when no issue found.

| Expert | Key trigger | Output | Downstream |
|--------|------------|--------|-----------|
| skeptic | New belief proposed, RESOLVED frontier | Falsification test design, challenge docs | Belief updates |
| adversary | High-confidence belief identified | Falsification test results | Belief governance |
| checker-expert | Expert artifact generated | Checker table (lane, artifact, pass/fail, duplicate rate) | Quality gate |
| bullshit-detector | Recent artifact or README claim | BS report (claim table, evidence, remediation) | Verification lane |
| reality-check-expert | Stale numeric or design-vs-behavior gap | Reality-check artifact (expect/actual/diff) | Source corrections |
| numerical-verification-expert | Numeric claim >20 sessions old | Verification table (claim, computed value, verdict) | Source files |
| error-minimization-expert | Claim drift or staleness detected | Error-minimization report, corrected files | Source maintainers |

---

## T4 — Compressors (distill, synthesize, merge to global state)
Trigger: T3 validates or T2 artifact is verified.
Exit product: principles, isomorphisms, updated frontiers — state that survives the context window.
**Scheduling rule (F-EXP9, L-387)**: T4 generalizer fires every K specialist (T2) sessions. Low WIP (1 task: compress) + high synthesis spread (10+ domains touched) = optimal. WIP spread hurts (r=-0.835); synthesis spread helps (+4.5x yield). Do not conflate. Measure T4 health by domain count in outputs, not L count.

| Expert | Key trigger | Output | Downstream |
|--------|------------|--------|-----------|
| synthesizer | Lesson production phase, belief formulation | Synthesized lesson with L-ID cross-refs | PRINCIPLES.md, beliefs/ |
| generalizer-expert | Cross-domain finding detected | Promoted principles/isomorphisms to ATLAS | PRINCIPLES.md, domain experts |
| recursion-generalizer-expert | ISO pattern found at multiple levels | Recursive chain (level-A→level-B + evidence) | ISOMORPHISM-ATLAS.md |
| multidisciplinary-swarm-architecture-expert | Architecture review, cross-domain invariant | Architecture map, 2 experiment proposals | Frontier updates |
| harvest-expert | Session close, outcome collection | Harvest artifact, state file updates | Next-session pickup |
| integrator | Active lane missing flow_out | Frontier update + evidence link | tasks/FRONTIER.md |
| farming-expert | Domain quiet >3 sessions, HHI >0.4 | Fallow markers, rotation recommendations | f_ops2_domain_priority.py |

---

## T5 — Meta-Improvers (improve swarm machinery)
Trigger: friction detected in T0–T4; coordination bottleneck; periodic due.
Exit product: tool, personality, or policy that reduces friction for future sessions.

| Expert | Key trigger | Output | Downstream |
|--------|------------|--------|-----------|
| swarm-expert-builder | Coordination bottleneck, capability gap | New personality file + dispatch lane | Personality system |
| personality-expert | Orphan personality, deployment gap | Dispatch lane for orphan, comparative data | Personality dispatch |
| swarm-health-expert | Health metrics drift | Health table (5 indicators + remediation) | Remediation lanes |
| computational-utilization-expert | Idle capacity, throughput signals | Utilization report + activation levers | Resource allocation |
| loop-expert | Loop pathology, re-queued lane ≥3x | Loop map + health verdict (STABLE/OSCILLATING) | Architecture lanes |
| garbage-expert | Stale READY/ACTIVE lanes, proxy-K DUE | Garbage triage artifact, stale-lane closures | Compaction lanes |
| coupling-expert | Co-change risk, cycle detected | Coupling-metric summary, remediation | Refactoring lanes |
| tooler-expert | Tool invocation fails, shell-parity gap | Tooling-gaps artifact + recommended fix | Tool fix lanes |
| politics-expert | Open coordination gap, governance needed | 3–5 mechanism mappings + experiments | Policy-change lanes |
| shared-clock-notifier-expert | Timing drift, notification latency | Shared-clock map + notifier map | Timing improvements |
| logging-expert | Session note created, count drift | Updated NEXT.md, HUMAN-SIGNALS | Next-session handoff |
| commit-expert | ≥8 unpushed commits OR load ≥6 | Checkpoint commits, lane progress updates | Commit Swarmer |
| commit-swarmer | ≥12 commits OR stale lanes | Checkpoint commits grouped by scope | Push relay |
| genesis-expert | Spawn protocol drift, child viability check | Spawn diff plan, dispatch lane | Child swarms |
| usage-identifier-expert | Identifier ambiguity, collision found | Identifier hygiene audit, lane row clarity | SWARM-LANES hygiene |

---

## Dispatch Rules (Tier-Aware)

| Session Phase | Default Expert Bundle | Skip-condition |
|---|---|---|
| Start | T0 all + T1 historian + info-collector | T0 clean + state fresh → skip to T1 |
| Incoming signal | T1 expert-classifier → routes to correct T2 | Signal already classified → directly T2 |
| Execution | T2 domain-expert or builder | Already done (anti-repeat check) → skip |
| Artifact ready | T3 skeptic or checker-expert | Low-stakes artifact → skip T3 |
| Compress | T4 synthesizer + harvest-expert | < 2 new findings → skip T4 |
| Friction detected | T5 swarm-expert-builder or garbage-expert | No bottleneck → skip T5 |

## Coordination Bundles (by signal type)
- **Ambiguous human signal**: T1 idea-investigator + T1 historian + T3 skeptic
- **New domain experiment**: T1 jobs-finder + T2 domain-expert + T3 checker + T4 generalizer
- **Stalled lane**: T1 council-expert + T2 action-expert + T5 garbage-expert
- **Capability gap**: T1 expert-classifier + T5 swarm-expert-builder + T3 checker
- **Belief challenge**: T3 adversary + T3 skeptic + T4 synthesizer
- **Cross-colony signal**: T2 domain-expert (source) + T4 integrator + T1 expert-classifier (target colony)
