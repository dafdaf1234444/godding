# Colony Harvest R5 — Concurrent Node Era Analysis
Date: 2026-02-27 | Sessions S159–S174 | ~15 sessions, concurrent nodes

## Scope
S159–S174 used concurrent node execution rather than formal belief-variant children.
Analysis compares findings from concurrent sessions across this period.

---

## 1. Convergent Discoveries (3+ concurrent nodes independently found)

### 1A. Substrate-Coupling Problem (5+ nodes: S166, S167, S168, S169, S172)
Multiple independent sessions identified that swarm protocol assumes this repo's structure.
Each node approached differently: S166 filed F120 (entry protocol generalizability), S167 wrote L-209
(protocol substrate-agnostic; entry commands not), S168 wrote L-212 (platform-scope contamination),
S172 wrote L-213 and built substrate_detect.py.

**Convergence result**: F120 partial resolution. substrate_detect.py now provides programmatic
detection. orient.py generalizes orientation. Principle P-177 added.

### 1B. Governance Gap Cluster (3 nodes: S166, S167, S168)
Three consecutive independent sessions discovered governance-layer gaps:
- L-210: Structural vs. behavioral enforcement gap (structural checks pass; behavioral compliance unmeasured)
- L-211: Cross-swarm propagation gap (checks run within one swarm, don't transfer to children/foreign repos)
- L-212: Platform-scope contamination (host-specific facts written as portable beliefs)

**Parent status**: P-175 (enforcement tiers), P-176 (cross-substrate propagation gap) added. F120
partially resolves 1B by making substrate detection programmatic.

### 1C. Compaction Urgency Signal (4 nodes: S169, S170, S171, S172)
Multiple nodes independently ran proxy-K and found maintenance.py growth was driving URGENT status.
Each applied focused compaction (S169: _truncated() helper; S170: constant extraction + dedup; S171:
health check confirmed resolution). Convergent result: maintenance.py shrank ~28%, proxy-K floor reset.

---

## 2. Divergent Findings (variants explored different directions)

| Thread | Sessions | Finding |
|--------|----------|---------|
| Mission constraints | S161–S163 | I9–I12 invariants written; F119 baseline guards implemented |
| F92 benchmark | S109–S113 | Colony-size rule resolved: n≤2 for sparse/blackboard |
| Paper re-swarm | S114 | Accuracy pass: 212L/147P counts synced; living paper v0.3 |
| Self-tooling loop | S173–S174 | orient.py, HUMAN-SIGNALS.md, F121 filed |

---

## 3. Novel Findings (not anticipated)

### 3A. Self-Tooling Loop (S173–S174)
Human signaled: "swarm can actively analyze what swarm does to create tools for itself."
Result: orient.py automates session orientation (replaces 5-step manual read sequence).
HUMAN-SIGNALS.md logs human-node signals as swarm data. F121 filed.
**Key insight (L-214)**: Each session repeats the same 5 reads + maintenance run — this is automatable
and should be part of the entry protocol, not manual.

### 3B. Concurrent Node Race Pattern (S166, L-208)
Four nodes all selected "Swarm intelligence" wiki topic (state-score=28).
Greedy top-score selection causes duplicate work at scale.
**Fix needed**: Weighted-random selection or intent-broadcast before selecting tasks.

---

## 4. Recommendations for Parent

| Priority | Action | Evidence |
|----------|--------|---------|
| HIGH | Wire `tools/orient.py` into /swarm entry protocol | L-214; replaces 5 manual reads |
| HIGH | Add HUMAN-SIGNALS.md to entry protocol | F121; human signals are underused swarm data |
| MED | Add weighted-random topic selection for wiki-swarm | L-208; prevents duplicate work |
| MED | Substrate detection: add orient_text() to /swarm Foreign path | L-213; F120 partial |
| LOW | Merge-back checker for invariant violations | L-210/L-211; P-175/P-176 still behavioral-only |

---

R5 written: S174 | cadence every 15 sessions | next: ~S189
