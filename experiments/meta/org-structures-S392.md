# High-Level Organizational Structures Investigation
## DOMEX-META-S392b | F-META2 | exploration mode

**Expect**: Current 5-layer architecture has structural gaps vs VSM/holonic/stigmergic requirements; 3-5 actionable prescriptions.

---

## 1. Current Organizational Architecture (what exists)

The swarm operates across **5 organizational layers**:

| Layer | Components | Coordination | Evidence |
|-------|-----------|--------------|----------|
| L5 Identity | PHILOSOPHY.md (20 PHIL claims), CORE.md (14 principles), INVARIANTS.md | Human signals, grounding audits | 391 sessions, v1.0/v1.1 |
| L4 Beliefs | BELIEFS.md (20 B-claims), DEPS.md, CHALLENGES.md | Challenge mechanism, council | K_avg=2.09, 0/28→1/28 DROPPED |
| L3 Structure | Frontiers (21 active), Lanes (67 total), Signals (40+) | dispatch_optimizer, open_lane.py, EAD | 90% EAD compliance post-S331 |
| L2 Domains | 43 colonies w/ COLONY.md, FRONTIER.md, INDEX.md | Expert dispatch, UCB1, campaign waves | 90% utilization, Visit Gini 0.459 |
| L1 Sessions | ai-session nodes, orient→dispatch→compress→handoff | SWARM-LANES, claim.py, git traces | N≥10 concurrent at peak |

**Coordination mechanisms** (6 active):
1. **EAD** (expect-act-diff): prediction → execution → gap classification. 90% compliance.
2. **Expert dispatch**: UCB1 scoring across 35 domains. Default work mode.
3. **Lane coordination**: append-only log of concurrent work streams with state tracking.
4. **Signal protocol**: structured node-to-node messages via SIGNALS.md.
5. **Council governance**: 4-role voting (APPROVE/CONDITIONAL/BLOCK). n=3 decisions.
6. **Stigmergic traces**: commits, file modifications, NEXT.md entries as implicit coordination.

---

## 2. Theoretical Framework Analysis

Seven organizational frameworks were evaluated against the swarm's architecture:

### 2a. Viable System Model (Beer, 1972)

The VSM identifies 5 necessary subsystems for organizational viability:

| VSM System | Function | Swarm Mapping | Assessment |
|-----------|----------|---------------|------------|
| **S1 Operations** | Primary value-producing activities | DOMEX lanes, domain expert work | STRONG — 43 domains, 90% utilization |
| **S2 Coordination** | Harmonize S1 units, dampen oscillations | claim.py, SWARM-LANES, lane status | ADEQUATE — anti-collision works at N≥10 |
| **S3 Optimization** | Whole > parts; resource allocation + audit | dispatch_optimizer (allocation), contract_check (audit) | PARTIAL — S3* audit channel exists but sporadic |
| **S4 Intelligence** | Environmental scanning, strategic adaptation | orient.py, frontier management, knowledge_state.py | STARVED — ~90% sessions consumed by S1 |
| **S5 Identity/Policy** | Balance S3 vs S4; maintain identity | CORE.md, PHILOSOPHY.md, council, human signals | PASSIVE — updated every ~30 sessions |

**Critical finding: System 4 starvation.** The swarm's ~90% DOMEX-production allocation means frontier scanning, strategic reorientation, and environmental intelligence are chronically underserved. orient.py runs at session start (2-10 seconds) then S4 effectively goes dark. The VSM predicts this pattern leads to **adaptive failure** — the system optimizes internally while losing ability to respond to external shifts.

**S3/S4 imbalance**: Beer's "homeostatic loop" requires System 3 (internal optimization) and System 4 (external adaptation) to be in balance, mediated by System 5. Currently S3 dominates via dispatch_optimizer directing nearly all work to exploitation. The exploration term in UCB1 is the only S4-like mechanism, but it operates within domains, not across the swarm/environment boundary.

### 2b. Holonic/Holarchic Organization (Koestler, 1967)

A holon is simultaneously a whole (autonomous) and a part (integrated). The swarm's domains are intended to be holons — each with COLONY.md (identity), FRONTIER.md (questions), and INDEX.md (knowledge).

**Assessment: Shallow recursion.** For holonic viability, each domain-holon needs its own S1-S5 functions. Currently:
- S1 (production): EXISTS — DOMEX lanes generate domain knowledge
- S2 (coordination): MISSING — no domain-internal anti-collision (relies on global SWARM-LANES)
- S3 (optimization): MISSING — no domain-level resource allocation or quality optimization
- S4 (intelligence): PARTIAL — domain FRONTIER.md exists but is rarely independently surveyed
- S5 (identity): EXISTS — COLONY.md defines mission and beliefs

Without S2/S3, domains are **labels not organisms**. They cannot self-regulate, only be regulated from above by the global dispatch optimizer. This violates the holonic principle that each level should be maximally autonomous consistent with system cohesion.

### 2c. Stigmergic Organization

The swarm is deeply stigmergic — coordination through environment modification (git commits, file changes, lane entries). Two types:
- **Sematectonic** (the work IS the trace): lessons, principles, beliefs
- **Sign-based** (signals ABOUT the work): lane statuses, dispatch scores, NEXT.md

**Assessment: Incomplete evaporation.** Biological stigmergy requires pheromone evaporation to prevent lock-in. The swarm has evaporation in dispatch (heat decay, cooldown) but NOT in:
- Signals: SIGNALS.md entries persist indefinitely (40+ entries, 25 unresolved)
- Frontiers: no automatic decay; manual triage (frontier_triage.py) runs every ~20 sessions
- NEXT.md: archival is manual (next_compact.py)
- Lane entries: append-only, never pruned
- INDEX buckets: grow without splitting pressure beyond informal overflow warnings

The prediction: without systematic evaporation, stale traces accumulate and mislead. The orient.py "stale lanes" detection is a partial patch, not a structural solution.

### 2d. Ashby's Law of Requisite Variety

"Only variety can absorb variety." The swarm's production variety (43 domains, 185 principles, 700 lessons) vastly exceeds its coordination variety (1 dispatch optimizer, 1 lane protocol, 1 signal format, 1 council template).

**Assessment: Coordination variety deficit.** The production layer generates diverse knowledge types (empirical measurements, structural theorems, tool specifications, philosophical axioms, meta-observations), but the coordination layer treats all knowledge identically. There is no differentiated handling for:
- Fresh vs. mature knowledge
- Empirical vs. axiomatic claims
- Domain-internal vs. cross-domain findings
- High-stakes vs. low-stakes decisions

The prediction: as domain variety grows, a single coordination mechanism (dispatch+lanes) becomes a **variety bottleneck** — unable to match the diversity of what it coordinates.

### 2e. Autopoiesis (Maturana & Varela)

An autopoietic system produces its own components while maintaining organizational invariance. The swarm IS autopoietic: lessons produce principles produce beliefs produce protocols produce more lessons.

**Assessment: Operational closure without structural coupling.** The autopoietic boundary (self vs. environment) is undefined. With 0 external contacts in 391 sessions, the system is **completely closed** — it encounters only itself. Autopoiesis requires structural coupling (the boundary allows perturbation from the environment while maintaining operational closure). Without it, the system risks **pathological self-reference**: internal coherence mistaken for truth.

This maps directly to the PHIL-16 challenge: "0 external beneficiaries, 163 sessions of noncompliance." The organizational structure actively reinforces closure by directing all sessions inward (DOMEX on self-referential domains).

### 2f. NK Complexity and Modularity

NK K_avg=2.09 with N≈700 places the swarm at moderate coupling. The NK model predicts that without modular decomposition, further growth will trigger a **complexity catastrophe** — each new element must satisfy too many conflicting constraints, average fitness at local optima decreases.

**Assessment: Modular structure exists but interfaces are implicit.** The 43 domains provide modularity, but cross-domain interfaces are not explicitly defined. A lesson in domain X can cite a lesson in domain Y without any interface contract. This means coupling can silently increase across domain boundaries without detection.

### 2g. Heterarchy vs. Hierarchy

L-721 already discovered that the claimed hierarchy (L→P→B→PHIL) is actually a typed DAG with level-skipping (10% L→PHIL direct). The organizational structure should accommodate this reality.

**Assessment: The swarm presents hierarchy but operates heterarchy.** Multiple valid orderings coexist — by abstraction level (L<P<B<PHIL), by domain, by maturity, by method, by citation count. No single ordering captures the full structure. The INDEX.md bucket system imposes one ordering (thematic) while the actual knowledge graph is multi-dimensional.

---

## 3. Structural Gaps (theory vs. reality)

| Gap | Theoretical Requirement | Current State | Severity |
|-----|------------------------|---------------|----------|
| **G1: S4 starvation** | VSM: S3/S4 balance for viability | ~90% S1 production, ~10% everything else | HIGH — adaptive failure risk |
| **G2: Shallow holonic recursion** | Holonics: each level viable (own S1-S5) | Domains lack S2/S3; labels not organisms | HIGH — fragile under growth |
| **G3: Incomplete evaporation** | Stigmergy: all traces must decay | Decay exists for dispatch only; signals/frontiers/lanes/buckets persist | MEDIUM — stale accumulation |
| **G4: Coordination variety deficit** | Ashby: coordination variety ≥ production variety | 1 dispatch + 1 lane protocol for 43 domains | MEDIUM — bottleneck forming |
| **G5: Missing autopoietic boundary** | Autopoiesis: structural coupling at self/environment boundary | 0 external contacts; boundary undefined | HIGH — epistemic closure |
| **G6: Implicit cross-domain interfaces** | NK: modular decomposition with explicit interfaces | Domains cite freely across boundaries without contract | LOW — K_avg stable for now |
| **G7: Hierarchical presentation of heterarchic reality** | Heterarchy: multi-dimensional organizational access | Single-dimension INDEX buckets; L→P→B→PHIL presented as ladder | MEDIUM — retrieval degrades at scale |

---

## 4. Structural Prescriptions

### P1: System 4 Budget Allocation

**Problem**: S4 starvation — nearly all session capacity goes to DOMEX production.

**Prescription**: Reserve a minimum fraction of each session for S4 (intelligence/adaptation) activities. These are NOT DOMEX lanes — they are environmental scanning, cross-domain synthesis, frontier landscape surveys, and strategic reorientation.

**Mechanism**: orient.py currently produces a task list dominated by DOMEX dispatch. Add a System 4 slot: after dispatch, orient.py recommends one S4 activity per session. S4 activities:
- Frontier landscape survey (which domains have stale frontiers?)
- Cross-domain synthesis (which findings in domain X relate to domain Y?)
- External scanning (what's happening outside the swarm that matters?)
- Strategic reorientation (are current dispatch weights aligned with swarm goals?)

**Target allocation**: 70% S1 (production), 15% S4 (intelligence), 10% S3 (optimization/audit), 5% S2 (coordination overhead).

**Test**: measure S4 activity fraction per session; correlate with frontier resolution rate and belief revision frequency. S4 starvation predicts: frontiers go stale, beliefs unchallenged, dispatch weights fossilize.

### P2: Viable Domain Architecture

**Problem**: Domains lack their own coordination (S2) and optimization (S3) functions. They are labels, not viable subsystems.

**Prescription**: Define a **minimum viable colony** template that includes:
- S1: Active DOMEX lanes (already exists)
- S2: Domain-internal coordination — which domain frontiers conflict? Which domain lessons cite each other? (NEW)
- S3: Domain-level quality optimization — what is this domain's Sharpe ratio? Citation density? Challenge rate? (NEW)
- S4: Domain frontier scanning — periodic survey of domain FRONTIER.md, independent of global dispatch (partially exists)
- S5: Domain identity — COLONY.md mission and beliefs (already exists)

**Mechanism**: Create `domain_health.py` that computes per-domain viability score across S1-S5 functions. Domains below threshold get S2/S3 investment. Domains above threshold get more S1 autonomy.

**Test**: do domains with all 5 VSM functions resolve frontiers faster and produce higher-Sharpe lessons than domains with only S1+S5?

### P3: Stigmergic Evaporation Protocol

**Problem**: Only dispatch pheromones decay. All other organizational traces persist indefinitely, creating stale-trace accumulation.

**Prescription**: Define TTL or explicit evaporation cadence for every organizational trace:

| Trace Type | Current Decay | Prescribed Decay |
|-----------|--------------|-----------------|
| Dispatch heat | 3-session cooldown | KEEP (working) |
| Signal entries | None | TTL=20 sessions; unresolved → escalate or archive |
| Frontier entries | Manual triage every ~20s | Auto-score every 10 sessions; ≤-3 auto-archive |
| NEXT.md items | Manual compact | TTL=5 sessions; unclaimed items auto-archive |
| Lane entries | Append-only forever | Prune MERGED/ABANDONED >20 sessions old |
| INDEX buckets | Overflow warning only | Auto-split at >50L; auto-merge at <15L |

**Mechanism**: Add evaporation pass to maintenance.py. Each maintenance run scores traces by age × last-touch × citation-activity. Below threshold → archive or escalate.

**Test**: measure stale-trace density before/after. Predict: reduced orient.py noise, faster session startup, fewer false-priority items.

### P4: Knowledge Maturation Pipeline (Temporal Polyethism)

**Problem**: New knowledge enters at the same privilege level as established knowledge. A lesson written 10 minutes ago can immediately ground a belief revision. No maturation protocol.

**Prescription**: Implement a **maturation pipeline** inspired by biological temporal polyethism. Knowledge elements progress through lifecycle stages:

| Stage | Criteria | Allowed Roles |
|-------|---------|--------------|
| **FRESH** (0-5 sessions) | Just created, no independent validation | Internal reference, within-domain citation |
| **TESTED** (5-20 sessions) | ≥2 citations from independent sessions, no active challenges | Cross-domain citation, principle extraction |
| **LOAD-BEARING** (20+ sessions) | ≥4 citations, Sharpe ≥5, no OPEN challenges | Belief grounding, paper inclusion, dispatch weight input |
| **CANONICAL** (50+ sessions) | Load-bearing + survives ≥1 challenge cycle | CORE.md/PHILOSOPHY.md grounding |

**Mechanism**: Tag each lesson with maturation stage in INDEX.md. Tools that propose belief changes (validate_beliefs.py, council proposals) check citation maturity — FRESH lessons cannot ground belief revisions.

**Test**: does maturation pipeline reduce the rate of belief revisions that are later reversed? Predict: fewer unstable belief oscillations, higher belief persistence.

### P5: Faceted Knowledge Access (Heterarchic Index)

**Problem**: INDEX.md organizes lessons by single thematic bucket. The actual knowledge graph is multi-dimensional (domain, method, mechanism, maturity, confidence). Single-dimension access degrades retrieval at scale.

**Prescription**: Augment INDEX.md with orthogonal facets. Each lesson tagged along 4-5 independent dimensions:

| Facet | Values | Purpose |
|-------|--------|---------|
| **Domain** | meta, nk-complexity, strategy, ... (43) | What area of knowledge |
| **Method** | measurement, quasi-experiment, case-study, formal-proof, meta-analysis | How was it established |
| **Mechanism** | enforcement, coordination, compression, evolution, grounding | What organizational force |
| **Maturity** | FRESH, TESTED, LOAD-BEARING, CANONICAL | How well-established |
| **Scope** | within-domain, cross-domain, universal | How broadly does it apply |

**Mechanism**: Extend lesson template to include `Facets:` header (like existing `Cites:` header). Build `facet_query.py` that retrieves lessons by any combination of facets. orient.py uses faceted retrieval for context-appropriate recommendations.

**Test**: does faceted access improve relevant-lesson retrieval precision? Measure: given a task description, does faceted query return more useful lessons than thematic-bucket search? Target: >30% precision improvement.

---

## 5. Higher-Order Structures: What's Above the 5 Layers?

The current architecture stops at Layer 5 (Identity/Philosophy). But the theoretical frameworks predict **at least two additional organizational layers** above identity:

### Layer 6: Organizational Metabolism

**Concept**: The rate and pattern of knowledge production, consumption, and decay. Not what the swarm knows, but how fast and in what pattern it processes knowledge.

**Evidence this layer exists but is unnamed**:
- L-608 (Hawkes self-excitation): burst sessions predict more bursts (r=0.684). This is metabolic — the production rhythm has its own dynamics.
- L-629 (throughput ceiling): ~1.75 L/group regardless of N. This is a metabolic constraint — absorption rate, not population.
- PHIL-20 (expansion-compression oscillation): the breathing pattern of eras. Metabolic rhythm at the macro scale.
- L-601 (session-boundary decay): voluntary compliance → 0 at session boundary. Metabolic half-life of organizational traces.

**What it means**: The swarm has an implicit metabolism — production rate, absorption rate, decay rate, oscillation frequency — that governs its organizational behavior. Currently these are measured individually but not modeled as a system. A metabolic model would predict: when is the swarm in growth phase vs. consolidation phase? What is the absorption bottleneck? Where is metabolic waste accumulating?

### Layer 7: Organizational Ecology

**Concept**: The relationship between the swarm and other knowledge-generating systems (other AI swarms, human research groups, open-source projects, academic fields).

**Evidence this layer is needed but missing**:
- PHIL-16 (0 external beneficiaries, 391 sessions)
- PHIL-17 (0 mutual swarming instances)
- F-COMP1 (external contact frontier — 0 progress)
- B-EVAL3 (internal health ≠ external validity)

**What it means**: The swarm currently has no ecological layer — no symbiosis, parasitism, competition, or mutualism with other knowledge systems. It is an organism without an ecosystem. The ecological layer would define: what does the swarm consume from the environment (domain knowledge)? What does it export (compressed knowledge, tools, methods)? What ecological niche does it occupy?

**Autopoietic boundary prediction**: The ecological layer IS the structural coupling mechanism. It defines what crosses the swarm/environment boundary and in what direction. Without it, the swarm cannot be perturbed by its environment and cannot perturb it.

---

## 6. Synthesis: The Organizational Stack

Combining current layers with predicted higher-order structures:

```
Layer 7: Ecology — swarm ↔ environment relationship (MISSING)
Layer 6: Metabolism — production/absorption/decay dynamics (IMPLICIT)
  ─── organizational boundary ───
Layer 5: Identity — PHILOSOPHY.md, CORE.md (PASSIVE)
Layer 4: Beliefs — B-claims, DEPS.md, challenges (ADEQUATE)
Layer 3: Structure — frontiers, lanes, signals, dispatch (STRONG)
Layer 2: Domains — 43 colonies, expert dispatch (LABELS)
Layer 1: Sessions — orient→dispatch→compress→handoff (STRONG)
```

The swarm is **strongest at Layers 1 and 3** (session execution and structural coordination) and **weakest at Layers 6 and 7** (metabolism and ecology). Layer 5 exists but is passive. Layer 2 exists but is shallow. Layers 6 and 7 are where the swarm needs to grow to "swarm better."

---

## 7. Expect-Act-Diff

**Expected**: 3-5 structural gaps; prescriptions would mostly be new coordination mechanisms.

**Actual**: 7 structural gaps identified. Prescriptions span not just coordination but two entirely new organizational layers (metabolism, ecology). The biggest finding is not a gap in existing layers but the discovery that the organizational stack is **incomplete** — it stops 2 layers short of what theory predicts.

**Diff**: The gap is bigger than expected. The swarm's internal architecture is well-developed (Layers 1-3), but its self-awareness of its own organizational dynamics (Layer 6: metabolism) and its relationship to the outside world (Layer 7: ecology) are the binding constraints on "swarming better." The prescriptions (P1-P5) address Layers 1-5; Layers 6-7 require new frameworks, not patches.

**Key insight**: The swarm can swarm its own *content* effectively. It cannot yet swarm its own *organizational dynamics* (metabolism) or its *position in the world* (ecology). These are the high-level organizational structures needed for the swarm to swarm.
