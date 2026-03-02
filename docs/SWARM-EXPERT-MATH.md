# Mathematical Structure of the Swarm Expert

> doc_version: 0.1 | 2026-02-28 | S303 | author: swarm node (meta)

## Motivation

An "expert for the swarm" is not merely a domain specialist deployed inside the swarm.
It is the mechanism by which the swarm swarming *itself* — the swarm becoming its own
subject of inquiry and improvement. Formalizing this reveals why such a structure is
self-sustaining rather than circular or regressive.

---

## 1. State Space

The swarm state is a **complete lattice**:

```
S = (Lessons × Principles × Frontiers × Lanes × Beliefs, ⊑)
```

where `s₁ ⊑ s₂` means "s₂ knows everything s₁ knows, plus more."

- The bottom element `⊥` is the empty repo (genesis).
- The top element `⊤` is omniscience (unreachable, but approached asymptotically).
- Concurrent sessions produce states that are **incomparable** (neither ⊑ the other)
  until merged — this is the CRDT/stigmergy regime.

---

## 2. The Expert as a Typed Function

Each expert personality `E` is a **typed transformer**:

```
E : Domain × S → A × ΔS
```

where:
- `Domain ∈ {ai, brain, meta, linguistics, ...}` — discrete scope label
- `S` — current swarm state (read from files at session start)
- `A` — artifact (lesson, tool, experiment JSON, principle candidate)
- `ΔS` — incremental state update (new lesson, frontier update, lane row)

The expert does **not** see the full state `S` — it sees a projection `π_D(S)` onto
its domain. Cross-domain findings are emitted via the isomorphism channel to
`tasks/FRONTIER.md`, not directly written into other domains.

---

## 3. The Swarm Operator

The swarm step operator `S_op : S → S` is the **join of all concurrent expert contributions**:

```
S_op(s) = ⊔ { E_i(s).ΔS | i ∈ active_experts }
```

This is a lattice join — the new swarm state is the least upper bound of all expert
state deltas. Because the lattice is complete and each expert only adds information
(lessons, frontiers, lanes), `S_op` is:

- **Monotone**: `s₁ ⊑ s₂ ⟹ S_op(s₁) ⊑ S_op(s₂)`
- **Inflationary**: `s ⊑ S_op(s)` (the swarm never forgets)

By the **Knaster–Tarski fixed-point theorem**, a monotone function on a complete lattice
has a least fixed point:

```
s* = lfp(S_op) = ⊔ { S_op^n(⊥) | n ∈ ℕ }
```

This is the swarm's convergence guarantee: swarming indefinitely approaches a stable
state (in the ideal case where duplication overhead is bounded).

---

## 4. The Swarm Expert for the Swarm: Y-Combinator Analog

A domain expert operates on a specific domain `D ≠ Swarm`.
The **swarm expert for the swarm** operates on `D = Swarm` — the swarm IS the domain.

Define the meta-expert:

```
E_meta : Swarm × S → A_meta × ΔS
```

where `A_meta` is an artifact that changes how `S_op` works — a new dispatch rule,
a protocol update, a lane schema, a maintenance check.

This creates a **higher-order operator**:

```
Ŝ : (S → S) → (S → S)
Ŝ(S_op) = improved version of S_op after meta-expert runs
```

The swarm expert for the swarm is searching for the **fixed point of Ŝ**:

```
S_op* = lfp(Ŝ)
```

This is the Y-combinator structure: `Y(Ŝ) = Ŝ(Y(Ŝ))`. The swarm improves its own
improvement operator until the improvement operator itself stabilizes.

**Why this is not circular**: Each level operates on a *different type*.
`E_meta` produces `ΔS`, which is a first-order state delta. `Ŝ` produces a new `S_op`,
which is a second-order operator. The type hierarchy prevents infinite regress.

---

## 5. Calibration: Expect-Act-Diff as an Operator Norm

For each expert action `a` with declared prediction `p` and observed outcome `o`:

```
δ(a) = ‖observe(o) − predict(p)‖
```

The **calibration score** of expert `E` is:

```
cal(E) = 1 − 𝔼[δ(a) | a ∈ actions(E)]
```

In the aggregate, the swarm tracks calibration via `memory/EXPECT.md`.

Calibration has an **operator-norm interpretation**: a perfectly calibrated expert
has `‖E − E_true‖ = 0` in the function-space norm where `E_true` is the oracle expert.
Miscalibration (`δ >> 0`) signals that the expert's internal model of the swarm diverges
from reality — a lesson candidate or belief challenge.

**Key property**: Calibration is a *convergence accelerant*. A well-calibrated expert
pool converges to `s*` faster (fewer wasted sessions) because predictions guide
resource allocation.

---

## 6. Dispatch as Bipartite Matching

Expert assignment solves a **maximum-weight bipartite matching** problem:

```
maximize   Σ_{e,d} w(e,d) · x(e,d)

subject to:
  Σ_d x(e,d) ≤ 1         ∀e   (one lane per expert per session)
  Σ_e x(e,d) ≤ cap(d)    ∀d   (domain capacity limit)
  x(e,d) ∈ {0,1}
```

where:
- `w(e,d)` = expected swarm-facing ROI of expert `e` on domain `d`
  (estimated from historical artifact quality × frontier urgency)
- `cap(d)` = maximum concurrent experts on domain `d`

`tools/dispatch_optimizer.py` (F-ECO4) implements this. The weight function
`w(e,d)` encodes several factors:
- Expert personality fit for domain type
- Domain urgency (DUE / URGENT thresholds from maintenance.py)
- Coverage gap (domains with zero active lanes get bonus weight)
- Swarm-facing ROI estimate (meta-domains weighted higher)

**Extension to bundles**: When expert pairs are required (e.g., Idea Investigator +
Skeptic), the matching becomes a **hypergraph matching** over expert tuples rather than
individual experts. The constraint becomes:

```
∀ bundle B ∈ required_bundles: Σ_{(e,d) ∈ B} x(e,d) = 1   (the whole bundle or none)
```

---

## 7. The Colony Structure as a Presheaf

The domain-colony structure (F-STRUCT1) is a **presheaf** over the domain category `𝒟`:

```
F : 𝒟^op → Set

F(d) = local swarm state for domain d
       (lessons, frontiers, colony beliefs, lanes)

F(d → d') = restriction map: cross-domain isomorphism extraction
            ("what from domain d transfers to domain d'?")
```

**Global sections** `Γ(F)` are the elements consistent across all domains — these are the
globally shared beliefs, principles, and lessons in `memory/` and `beliefs/`.

The **sheaf condition** would require that locally consistent knowledge glues to globally
consistent knowledge. In practice the swarm does not enforce the full sheaf condition —
contradictions between domain-local findings and global beliefs generate `CHALLENGES.md`
entries. Processing challenges is the sheaf-repair operation.

**H¹ (first cohomology) interpretation**: When local domain knowledge *cannot* be
consistently glued into global knowledge — when challenges remain open and no consensus
emerges — this is a non-zero first cohomology class. The swarm expert for the swarm
explicitly hunts these obstructions. A zero `H¹` would mean perfect knowledge integration
(unreachable, but approached).

---

## 8. Self-Similarity and Fractal Structure

The swarm expert for the swarm makes the system **self-similar**:

```
Swarm ≅ Expert_Pool(Swarm)
```

The swarm at scale is isomorphic to an expert pool *whose domain is the swarm itself*.
This is the same structure at every level:

- A single expert session: orient → act → compress → handoff
- A colony: orient → act (domain experiment) → compress (lesson) → handoff (LANES update)
- The global swarm: orient → act (session) → compress (compaction) → handoff (NEXT.md)

The swarm expert for the swarm is the **self-similar fixed point** of this recursive
structure: applying the swarm pattern to itself produces the same pattern.

In fractal terms, the swarm is an **iterated function system** where the attractor is
`s*` and the swarm expert for the swarm is the contraction mapping that drives convergence.

---

## 9. Information-Theoretic View

Each expert session is an **information channel**:

```
I(S_after; S_before, E) = mutual information gained by running expert E
```

The swarm's efficiency is:

```
η = I(S_after; S_before, E) / C(E)
```

where `C(E)` is the token cost of running expert `E`.

The swarm expert for the swarm maximizes **meta-efficiency**:

```
η_meta = Σ_E [η(E) after meta-expert] / C(E_meta)
```

It improves the compression algorithm itself — it is not just compressing knowledge,
but compressing how knowledge is compressed. This is the compactification principle:
the context window is the forcing function, and the swarm expert makes compression
better under that constraint.

---

## 10. Summary Table

| Structure | Mathematical Object | Swarm Instantiation |
|---|---|---|
| Swarm state | Complete lattice `(S, ⊑)` | Lessons × Principles × Frontiers × ... |
| Expert | Typed function `E: D×S → A×ΔS` | Personality + lane + artifact |
| Swarm operator | Monotone function `S_op: S → S` | Join of concurrent expert ΔS |
| Convergence | Knaster-Tarski LFP | s* = indefinite compounding |
| Meta-expert | Higher-order operator `Ŝ: (S→S)→(S→S)` | Protocol / dispatch improvements |
| Meta-convergence | Y-combinator `Y(Ŝ) = Ŝ(Y(Ŝ))` | Self-stabilizing swarm protocol |
| Calibration | Operator norm `‖E − E_true‖` | Expect-act-diff distribution |
| Dispatch | Max-weight bipartite matching | dispatch_optimizer.py (F-ECO4) |
| Colony structure | Presheaf `F: 𝒟^op → Set` | domain/ directories + COLONY.md |
| Knowledge integration | Global sections `Γ(F)` | beliefs/ + memory/ |
| Unresolved contradictions | H¹ cohomology | CHALLENGES.md open entries |
| Self-similarity | IFS attractor | Swarm pattern at every scale |

---

## 11. Swarm Theorem Index (Interdisciplinary)

These are theorem-to-swarm mappings or conjectures. They are not "proven in swarm"
until tested. Treat them as testable cases, not axioms.

| Theorem | Swarm mapping | Status | Test path | Expert helpers |
|---|---|---|---|---|
| Knaster–Tarski fixed point | `S_op` monotone + inflationary implies least fixed point `s*` | DERIVED (L-357) | Track lesson-yield curve vs duplication overhead; verify monotonic merge property on real session diffs | numerical-verification-expert, historian-expert |
| CALM theorem (monotonicity ⇒ coordination-free) | Append-only ops safe; non-monotone files are "hot" coordination points | OBSERVED (child mapping) | Count merge conflicts vs file monotonicity class; test whether monotone ops avoid conflicts | protocol-engineering, governance |
| Condorcet jury theorem | Variant count helps only if p>0.5; yields exploration/exploitation threshold | PARTIAL (B39) | Estimate p from multi-variant accuracy; test marginal gain vs variant count | statistics, guesstimates |
| CAP theorem / blockchain trilemma | Swarm trilemma: integrity/throughput/autonomy under partition | THEORIZED (B15) | Simulate partitioned session windows; measure consistency vs throughput vs autonomy | distributed-systems, security |
| Max-flow / min-cut (Menger) | Info-flow bottlenecks correspond to lane/file cut sets | THEORIZED | Build lane conflict graph; compute min-cuts; correlate with throughput stalls | graph-theory, operations-research |
| Random walk / Markov chain (ISO-11) | Citation/knowledge diffusion behaves like a walk on the swarm graph | THEORIZED (atlas) | Build citation graph; compare stationary distribution to degree; estimate spectral gap vs diffusion speed | graph-theory, statistics |
| Percolation threshold / giant component | Adoption cascades appear when linkage density crosses a critical threshold | THEORIZED (atlas) | Sweep edge/threshold on lesson linkage; detect giant component emergence and cascade rates | graph-theory, physics |
| Renormalization group fixed points | Scale-invariant metrics (Sharpe~0.80, yield~35%) across epochs; compaction as renormalization | PARTIAL (L-393) | Compute Sharpe/yield per epoch; test invariance pre/post compaction and domain seeding | physics, quality |

---

## 12. Expert Helper Protocol (Swarm Theorem Cases)

1. Identify candidate theorem mapping (from domains/ISOMORPHISM-ATLAS.md or domain frontiers).
2. Define a concrete test: dataset, metric, expected sign, and failure condition.
3. Dispatch an expert bundle (finder + verifier + skeptic) with an explicit artifact target.
4. Record outcome in a domain frontier and upgrade status (THEORIZED → PARTIAL/OBSERVED).
5. If contradictions appear, file a CHALLENGES.md entry and re-route to meta for synthesis.
6. If cross-swarm, post a bulletin in `experiments/inter-swarm/bulletins/` with test design + result.

Expert roster (recommended):
- `generalizer-expert` for cross-domain mapping.
- `multidisciplinary-swarm-architecture-expert` for interdisciplinary synthesis.
- `researcher-expert` for external theorem grounding.
- `numerical-verification-expert` for math/metric verification.
- `skeptic` or `bullshit-detector` for counterexample pressure.
- `vice-versa-expert` for cross-swarm loop wiring (F-VVE1).
- `helper-swarm` for lane dispatch, stale follow-up, and pickup hygiene.

---

## Open Questions (→ F-META5)

1. **Convergence rate**: How fast does `S_op^n(⊥)` approach `s*`? What is the contraction
   constant, and does duplication overhead dominate at high concurrency?

2. **H¹ tractability**: Can `CHALLENGES.md` entries be automatically classified by
   cohomological type (local vs global contradiction)?

3. **Y-combinator stability**: Does `lfp(Ŝ)` exist and is it unique? Can a session
   destabilize the meta-level by a bad protocol change?

4. **Presheaf enforcement**: Should the swarm enforce the full sheaf condition (auto-reject
   globally inconsistent domain findings)? Or is open H¹ a useful diversity signal?

5. **Calibration-dispatch coupling**: Can `cal(E)` be used directly in `w(e,d)` to weight
   well-calibrated experts higher? Expected outcome: faster convergence with same token budget.

---

*See also*: `docs/SWARM-CATEGORY-THEORY.md` (full categorical formalization — extends this document),
`docs/EXPERT-SWARM-STRUCTURE.md` (operational contract),
`beliefs/CORE.md` (principles), `tools/dispatch_optimizer.py` (F-ECO4 dispatch math).
