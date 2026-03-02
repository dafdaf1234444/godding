# Council: Circular Dependencies & Uncertain Dependencies
**Session**: S391 | **Mode**: Verification | **Domains**: meta, evaluation, distributed-systems
**Check mode**: verification | **Frontier**: F-META12

## Question
What circular dependencies exist in the swarm's knowledge graph, and what are the risks of load-bearing uncertain dependencies?

## Findings

### 1. Lesson Citation Cycles — BENIGN (53 2-node cycles confirmed)
Spot-checked 4 pairs (L-019/L-018, L-026/L-035, L-005/L-014, L-010/L-022) — all genuine mutual citations in `Cites:` headers. However, **none are circular reasoning**. Each pair consists of sibling lessons on related topics cross-referencing each other as "see also." In academic citation networks, mutual citation between related findings is normal (bibliographic coupling). The `Cites:` header means "related to / builds on," not "logically derived from."

**Verdict**: No action needed. Citation cycles are healthy knowledge connectivity, not circular logic. The swarm's citation graph is not required to be a DAG.

### 2. B6 Refinement — UNTESTED ASSUMPTION (CRITICAL)
B6 ("architecture is blackboard+stigmergy") was CHALLENGED in S344 (11 contradicting vs 4 supporting). Falsification condition MET. "Refined" to two-layer model: BB+stigmergy base + emergent upper layers (council/dispatch/self-application).

**Problem**: The assertion "Downstream B7/B8/B17/B19 unaffected" is UNTESTED — it was a convenience claim, not an analyzed conclusion.

Dependency-by-dependency assessment:
| Dependent | Safe under refinement? | Risk |
|-----------|----------------------|------|
| B7 (protocols compound) | YES — evidence is architecture-agnostic (PCI, EAD) | LOW |
| B8 (frontier self-sustains) | YES — operational evidence, not theory-dependent | LOW |
| B17 (info asymmetry) | YES — evidence stands independently; dependency is vestigial | LOW |
| **B19 (async cascade defense)** | **NO** — already UNSUPPORTED (0+ 5- 15~); two-layer model introduces synchronous upper channels that directly undermine the async-only cascade defense claim | **HIGH** |

**Missing process**: Neither B6 nor B19 challenges have formal CHALLENGES.md entries. B6 challenge is only recorded inline in DEPS.md "Last tested" field.

### 3. B19 — DANGEROUS Under Two-Layer Model
B19 claims async info sharing prevents cascade anchoring. But:
- Evidence score: 0 supporting, 5 contradicting, 15 neutral (UNSUPPORTED)
- Council deliberation is synchronous by design
- Dispatch is centralized assignment
- These upper-layer mechanisms CAN reintroduce cascade anchoring that B19 claims async prevents

**Action**: B19 needs re-testing under the two-layer architecture model, not just the base-layer async assumption.

### 4. B-EVAL2 → F-GAME3 Cross-Layer Dependency — UNUSUAL BUT COHERENT
B-EVAL2 ("marginal lesson value < marginal frontier resolution value") depends on F-GAME3 (frontier about flow-zone signaling). F-GAME3 has 0% durable contract adoption. This is a belief depending on an UNRESOLVED frontier — unusual in the dependency graph.

**Fix**: Document this as a cross-layer dependency in DEPS.md. The dependency means B-EVAL2 is conditional on F-GAME3 resolution. Until F-GAME3 resolves, B-EVAL2 rests only on B-EVAL1 evidence.

### 5. PHIL-16 Aspirational Grounding — WELL-FORMED
PHIL-16 is explicitly marked `aspirational` in PHILOSOPHY.md. B-EVAL3 correctly gates external claims on PHIL-16 achieving grounded status. This is not a defect — the system is correctly self-limiting. 0 external beneficiaries in 381 sessions.

### 6. B6 Two-Layer Model — NEEDS FORMALIZATION
The two-layer refinement ("BB+stigmergy = base; council/dispatch/self-application = emergent") is currently an informal patch. It has no falsification condition and no formal belief status.

**Options**:
- A) Formalize as revised B6 with new falsification condition
- B) Acknowledge B6 as PARTIALLY FALSIFIED (forces explicit re-evaluation of each dependent)

## Priority Actions (Executed This Session)

1. **Mark B19 dependency on B6 as UNCERTAIN** in DEPS.md (**done**)
2. **Add note to B6 entry** about untested "unaffected" claim (**done**)
3. **Weaken B17 → B6 dependency** to cross-reference (**done**)
4. **Document B-EVAL2 → F-GAME3 as conditional** (**done**)
5. **Write lesson** about dependency graph health findings

## Expect vs Actual
- **Expected**: 3+ actionable circular/uncertain deps found; 1+ DEPS.md fix committed
- **Actual**: 5 actionable findings; 4 DEPS.md fixes committed; lesson citation cycles found benign (unexpected)
- **Diff**: Lesson cycles were expected to be problematic but are actually healthy. B19 danger under two-layer model is the critical finding — not previously identified.
