# Category Theory of the Swarm

> doc_version: 1.0 | 2026-03-01 | S390 | DOMEX-META-S390
> Extends: `docs/SWARM-EXPERT-MATH.md` (S303, partial treatment)
> Coordinates: SIG-1 (node generalization), SIG-27 (epistemological states)
> Cites: L-357, L-427, L-274, NODES.md, ISOMORPHISM-ATLAS.md

This document defines the swarm's complete categorical structure. Where
SWARM-EXPERT-MATH.md described the swarm using lattice theory, presheaves,
and cohomology as *analogies*, this document constructs the swarm AS a
collection of interrelated categories with explicit objects, morphisms,
functors, adjunctions, and higher structure.

**Falsifiability**: Each categorical structure maps to a concrete swarm
mechanism. If the mapping is wrong, the structure should be removed. Category
theory is here because it *compresses* — not because it decorates.

---

## 1. The Five Categories

### 1.1 **State** — The Category of Swarm States

| Component | Definition |
|-----------|-----------|
| Objects | Swarm states `s = (L, P, F, Λ, B)` where L=lessons, P=principles, F=frontiers, Λ=lanes, B=beliefs |
| Morphisms | `f: s₁ → s₂` iff `s₁ ⊑ s₂` (s₂ knows everything s₁ knows) |
| Identity | `id_s: s → s` (trivially, s ⊑ s) |
| Composition | Transitivity: `s₁ ⊑ s₂` and `s₂ ⊑ s₃` implies `s₁ ⊑ s₃` |

This is the **thin category** (poset category) induced by the knowledge
ordering ⊑ on the complete lattice (S, ⊑). Every hom-set has at most one
element. The lattice structure gives:

- **Initial object**: `⊥` = empty repo (genesis, CORE v0.1)
- **Terminal object**: `⊤` = omniscience (unreachable)
- **Binary products**: `s₁ ∧ s₂` = greatest common knowledge (meet)
- **Binary coproducts**: `s₁ ∨ s₂` = merged knowledge (join = git merge)

**Swarm instantiation**: Every git commit is a morphism in **State**. The
commit graph IS the morphism graph. Concurrent sessions produce states that
are incomparable until merged — the merge commit is their coproduct.

### 1.2 **Node** — The Category of Swarm Participants

| Component | Definition |
|-----------|-----------|
| Objects | Nodes: `{human, ai-session, child-swarm, external, ...}` (per NODES.md, SIG-1) |
| Morphisms | Signal channels: `σ: n₁ → n₂` = a communication pathway from n₁ to n₂ |
| Identity | Self-signaling: `id_n` = internal state (node reads its own output) |
| Composition | Signal relay: if n₁ signals n₂ and n₂ signals n₃, the composed channel exists |

Morphisms are **not** unique between objects — there may be multiple signal
channels between two nodes (e.g., human→ai-session via session-prompt AND
via tasks/SIGNALS.md). This makes **Node** a genuine category, not a thin
category.

**Node properties as functors** (SIG-1 coordination):

```
Capabilities: Node → Set        n ↦ {session-initiate, kill-switch, ...}
Bandwidth:    Node → (ℝ≥0, ≤)   n ↦ throughput estimate
Persistence:  Node → {permanent, session, spawned, episodic}
```

Each property in the node model (NODES.md) is a functor from **Node** to an
appropriate target category. The node model IS the collection of these
functors. Adding a new node type means extending the domain of all functors —
the categorical framework guarantees that adding nodes requires no protocol
changes, only functor evaluations. This IS SIG-1: generalization via functors
rather than special cases.

### 1.3 **Dom** — The Category of Domains

| Component | Definition |
|-----------|-----------|
| Objects | Domains: `{ai, brain, meta, linguistics, nk-complexity, ...}` (46 domains) |
| Morphisms | Cross-domain isomorphisms: `ι: d₁ → d₂` = structural transfer (ISO-k) |
| Identity | `id_d` = trivial self-transfer |
| Composition | If ISO-3 maps `physics → swarm` and ISO-3 maps `swarm → linguistics`, the composite transfers physics → linguistics |

**Key structure**: The isomorphism atlas (domains/ISOMORPHISM-ATLAS.md)
generates the morphisms. Each ISO-k entry with N domain manifestations
generates N(N-1) morphisms (each pair of domains in the manifestation table).
The atlas is not a list of analogies — it is the **morphism generator** of
**Dom**.

**Dom** has additional structure: each ISO-k morphism carries a **Sharpe
score** (evidence quality × breadth). This makes **Dom** an enriched category
over ([0,5], ≥) — see §5.

### 1.4 **Know** — The Category of Knowledge States

| Component | Definition |
|-----------|-----------|
| Objects | Knowledge states: `{MUST-KNOW, ACTIVE, SHOULD-KNOW, DECAYED, BLIND-SPOT}` (SIG-27, knowledge_state.py) |
| Morphisms | State transitions: BLIND-SPOT → SHOULD-KNOW → ACTIVE → MUST-KNOW (acquisition) and ACTIVE → DECAYED (decay) |
| Identity | Remaining in the same state |
| Composition | Transitivity of state transitions |

This is a thin category with a partial order. The two directions (acquisition
and decay) make it NOT a total order — MUST-KNOW and DECAYED are
incomparable (different branches from ACTIVE).

**Swarm instantiation**: `tools/knowledge_state.py` classifies each lesson
into one of these objects. The transition morphisms are triggered by session
activity (citation, testing, time-since-last-use).

### 1.5 **Expert** — The Category of Expert Personalities

| Component | Definition |
|-----------|-----------|
| Objects | Expert types: `{builder, explorer, skeptic, adversary, synthesizer, harvest-expert, ...}` |
| Morphisms | Personality subsumption: `e₁ → e₂` iff e₂'s capabilities include e₁'s |
| Identity | Self-subsumption |
| Composition | Transitivity |

This is thin (poset of capability sets). The **domain-expert** personality
(tools/personalities/domain-expert.md) is the **terminal object** in the
subcategory of domain personalities — every domain expert IS a domain-expert
with a role overlay.

---

## 2. The Seven Functors

### 2.1 Action Functor: `Act: Node → [State, State]`

Maps each node to its **endofunctor** on swarm state:

```
Act(human)      = H: State → State     (directional authority — reframes, signals)
Act(ai-session) = A: State → State     (expert dispatch — lessons, tools, lanes)
Act(child-swarm) = C: State → State    (isolated exploration — bulletins, challenges)
Act(external)   = X: State → State     (domain corrections — currently trivial: 0 in 300+ sessions)
```

On morphisms: a signal channel `σ: n₁ → n₂` maps to natural transformation
`Act(σ): Act(n₁) ⟹ Act(n₂)` — the effect of n₁ relayed through n₂.
Example: human directive relayed through ai-session = `Act(σ_prompt): H ⟹ A`.

**This is the categorical statement of PHIL-13**: no node has epistemic
authority because `Act` does not factor through trust levels. Evidence
determines which endofunctors compose into the final state, not identity.

### 2.2 Domain Projection: `π: State → State_D` (one per domain D)

```
π_D(s) = domain-D-relevant components of s
π_D(f: s₁ → s₂) = f restricted to domain D
```

Forgets all non-D information. **State_D** is the local state category for
domain D (also a thin category / complete lattice).

### 2.3 Domain Embedding: `ι: State_D → State` (one per domain D)

```
ι_D(s_D) = global state with only domain-D information
ι_D(f_D: s₁_D → s₂_D) = the global morphism induced by local progress
```

Embeds local findings into global state. This is how domain experts write
lessons, update frontiers, and modify beliefs.

### 2.4 Colony Presheaf: `F: Domᵒᵖ → Set`

```
F(d) = State_D = local state at domain d
F(ι: d₁ → d₂) = restriction map: extract what transfers from d₂ to d₁
```

**Already described** in SWARM-EXPERT-MATH.md §7 and L-357. The new
contribution is placing it in the full categorical context:

- F is a **contravariant functor** from Dom to Set
- Global sections Γ(F) = lim F = beliefs/principles consistent across all domains
- Local sections = domain-specific lessons and frontiers
- The presheaf category **[Domᵒᵖ, Set]** contains all possible colony configurations

### 2.5 Compaction Functor: `K: State → State`

```
K(s) = compact(s)    (proxy-K reduction: distill lessons, merge principles, trim frontiers)
K(f: s₁ → s₂) = compact(f)    (the compressed version of the transition)
```

Properties:
- `K(s) ⊑ s` for all s (compaction loses detail — K is **deflationary**)
- `K ∘ K ≅ K` (compacting twice ≈ compacting once — **idempotent up to isomorphism**)
- K preserves the lattice structure: `K(s₁ ∨ s₂) ⊒ K(s₁) ∨ K(s₂)`

**Swarm instantiation**: `tools/compact.py`. The proxy-K metric measures how
far the current state is from the fixpoint of K.

### 2.6 Knowledge Classification: `κ: Ob(State) → Ob(Know)`

```
κ(lesson) = MUST-KNOW | ACTIVE | SHOULD-KNOW | DECAYED | BLIND-SPOT
```

Assigns each knowledge artifact to its epistemological state. Not a functor in
the strict sense (it maps objects to objects, not morphisms to morphisms) —
it is an **object-level function**. To make it functorial, extend to:

```
κ: State → Know
κ(f: s₁ → s₂) = the knowledge-state transition induced by the swarm step
```

A session that cites a DECAYED lesson moves it to ACTIVE: this IS a morphism
in **Know**, and κ maps the state transition to it.

### 2.7 Dispatch Functor: `Δ: Dom × Expert → State → State`

```
Δ(d, e) = the state transformation when expert type e is dispatched to domain d
```

This is the categorical version of the bipartite matching in
SWARM-EXPERT-MATH.md §6. The dispatch optimizer selects the assignment
`(d, e)` that maximizes expected yield — this is choosing the morphism in
**Dom × Expert** whose image under Δ produces the largest state advancement.

---

## 3. The Three Adjunctions

### 3.1 Projection ⊣ Embedding (Galois Connection)

```
ι_D ⊣ π_D : State ⇆ State_D
```

**Meaning**: For any local state `s_D` and global state `s`:

```
ι_D(s_D) ⊑ s   ⟺   s_D ⊑_D π_D(s)
```

"Domain-local knowledge embeds into global state iff it's already contained
in the global state's domain projection."

- **Unit** `η: id_{State_D} → π_D ∘ ι_D`: trivially an isomorphism (embed then project recovers local state)
- **Counit** `ε: ι_D ∘ π_D → id_{State}`: NOT an isomorphism (project then embed loses cross-domain info)

The counit's non-triviality IS the information loss from domain specialization.
Cross-domain isomorphisms (ISO-k) are precisely the morphisms that recover
information lost by the counit — they reconstruct cross-domain structure that
domain projection discards.

**Swarm instantiation**: An expert reads `domains/brain/` (= π_brain) and
writes findings back to global state (= ι_brain). The Galois connection
guarantees this is consistent — local work that's already globally known
won't create contradictions.

### 3.2 Compaction ⊣ Inclusion (Compression Adjunction)

```
K ⊣ Inc : State_compact ⇆ State
```

where `Inc: State_compact ↪ State` is the inclusion of the compact sublattice.

**Meaning**: The compacted state is the **best approximation** from below
in the compact sublattice:

```
K(s) ⊑_compact s'   ⟺   s ⊑ Inc(s')    (for compact s')
```

- **Unit** `η: id → Inc ∘ K`: η_s maps s to its compaction viewed as a global state. This is deflationary: `Inc(K(s)) ⊑ s`.
- **Counit** `ε: K ∘ Inc → id_{compact}`: compacting an already-compact state is identity.

**Swarm instantiation**: `compact.py` computes K. The proxy-K metric
measures ‖η_s‖ — the distance from current state to the compact sublattice.
When proxy-K is low, the unit is nearly an isomorphism (state is already
compressed).

### 3.3 Free Knowledge ⊣ Forgetful (Knowledge Structure)

```
Free ⊣ U : Know ⇆ Set
```

where:
- `U: Know → Set` forgets the knowledge-state structure (just the set of artifacts)
- `Free: Set → Know` assigns default state BLIND-SPOT to all new artifacts

**Meaning**: Any set of facts can be freely equipped with knowledge states
(everything starts as BLIND-SPOT), and this is the "cheapest" way to create
a knowledge-state structure.

**Swarm instantiation**: When a new frontier opens, all relevant knowledge
starts as BLIND-SPOT. The swarm's investigation moves artifacts through the
morphisms of **Know**: BLIND-SPOT → SHOULD-KNOW → ACTIVE → MUST-KNOW. The
free-forgetful adjunction is why the default state is the least committed
one.

---

## 4. Yoneda Lemma — The Atlas as Embedding

### Statement

For any presheaf `F: Domᵒᵖ → Set` and domain `d ∈ Ob(Dom)`:

```
Nat(y(d), F) ≅ F(d)
```

where `y: Dom → [Domᵒᵖ, Set]` is the Yoneda embedding:
`y(d) = Hom_Dom(−, d)` (the representable presheaf).

### Swarm instantiation

`y(d)` = "all ways other domains map INTO domain d" = all ISO-k entries where
d appears as a target manifestation.

`Nat(y(d), F) ≅ F(d)` says: **a domain's local state is completely determined
by how all other domains relate to it through cross-domain isomorphisms**.

Concretely: if you know every structural transfer pathway to domain d (all
ISO entries touching d), you can reconstruct d's local state. This is why the
isomorphism atlas IS the Yoneda embedding — it encodes each domain as the
totality of its structural relationships. L-274's claim that "maximum-compression
world knowledge is structural equivalence, not facts" IS the Yoneda lemma
applied to the swarm's domain structure.

### Consequences

1. **The atlas is faithful**: The Yoneda embedding is always faithful (and
   full for the representable part). Two domains with identical ISO profiles
   are isomorphic in **Dom**. If physics and swarm share all the same ISO
   entries, they are categorically equivalent domains.

2. **New domains are determined by their ISO profiles**: To fully integrate a
   new domain, determine which ISO entries it manifests. The Yoneda embedding
   does the rest — the domain's structural role in the swarm is fixed by its
   cross-domain relationships.

3. **Atlas completeness test**: Yoneda is an isomorphism only if the atlas
   captures ALL structural transfers. Missing ISO entries = incomplete Yoneda
   embedding = structural blind spots. This gives a **categorical test for
   atlas completeness**: for each domain pair (d₁, d₂), does there exist a
   morphism in Dom? If not, is that absence verified or just unmeasured?

---

## 5. Enrichment — Calibration and Quality

### 5.1 **State** enriched over ([0,1], ≥, 1)

Each morphism `f: s₁ → s₂` in **State** carries a **calibration score**
`cal(f) ∈ [0,1]`:

```
cal(id) = 1                            (identity is perfectly calibrated)
cal(g ∘ f) ≥ cal(f) · cal(g)          (composition degrades at most multiplicatively)
```

This makes **State** a category enriched over the monoidal category
`([0,1], ·, 1)` — the unit interval with multiplication as tensor.

**Swarm instantiation**: `memory/EXPECT.md` tracks expect-act-diff per
session. The calibration score of a session's state transition is
`1 − 𝔼[δ(a)]` (from SWARM-EXPERT-MATH.md §5). Well-calibrated sessions
produce morphisms with cal ≈ 1.

### 5.2 **Dom** enriched over ([0,5], ≥)

Each morphism `ι: d₁ → d₂` carries a Sharpe score in [0,5] from the ISO atlas.
This enrichment makes domain relationships measurable — high-Sharpe transfers
are "stronger" morphisms. The enriched hom-object `Dom(d₁, d₂) ∈ [0,5]`
is the maximum Sharpe score across all ISO entries connecting the two domains.

---

## 6. Limits and Colimits

### 6.1 Concurrent Merge as Coproduct (Pushout)

When N sessions work independently from base state s₀:

```
        s₀
       / | \
      /  |  \
   s₁   s₂  s₃    (independent session results)
```

The merged state is the **pushout** (coproduct in the slice category over s₀):

```
s_merged = s₁ ∨ s₂ ∨ s₃    (lattice join)
```

This is well-defined because **State** is a complete lattice. The pushout
always exists. Git merge IS the coproduct computation.

**When the coproduct fails to be clean**: merge conflicts. Two sessions
produce states that are locally incomparable — the lattice join exists
(append both) but may contain contradictions. CHALLENGES.md entries are
exactly the cases where the naive coproduct requires manual repair (sheaf
condition violation, H¹ ≠ 0 from L-427).

### 6.2 Consensus as Limit (Equalizer)

When multiple experts make conflicting claims about the same frontier:

```
E₁ ⟹ s    (expert 1's conclusion)
E₂ ⟹ s    (expert 2's conclusion)
```

The consensus, if it exists, is the **equalizer**:

```
eq(E₁, E₂) = { s | E₁(s) = E₂(s) }
```

the largest substate on which experts agree. When the equalizer is empty,
no consensus exists — the frontier remains OPEN and the disagreement is
recorded as a challenge.

**Swarm instantiation**: CHALLENGES.md + council sessions. The council
attempts to construct equalizers across conflicting expert findings.

### 6.3 Global Sections as Limit of the Presheaf

```
Γ(F) = lim_{d ∈ Dom} F(d)
```

The global sections are the **limit** of the colony presheaf over all
domains. Concretely: principles and beliefs that are consistent with every
domain's local findings. A principle that contradicts a domain's evidence
is NOT in Γ(F) — it's a section that fails to glue (H¹ obstruction).

---

## 7. Monoidal Structure

### 7.1 (State, ∨, ⊥) — Symmetric Monoidal Category

```
Tensor:  s₁ ⊗ s₂  =  s₁ ∨ s₂     (lattice join = knowledge combination)
Unit:    I  =  ⊥                    (empty state)
```

Properties (inherited from lattice join):
- **Associativity**: `(s₁ ∨ s₂) ∨ s₃ = s₁ ∨ (s₂ ∨ s₃)`
- **Commutativity**: `s₁ ∨ s₂ = s₂ ∨ s₁`  (symmetric)
- **Unit**: `s ∨ ⊥ = s`

**Expert tensoring**: Running two experts concurrently is the tensor product
of their state transformations:

```
(E₁ ⊗ E₂)(s) = E₁(s) ∨ E₂(s)
```

This is exactly concurrent session execution. The monoidal structure
formalizes the swarm's parallelism: independent expert sessions compose
via the tensor product, not sequential composition.

### 7.2 Internal Hom (Closed Structure)

If **State** is a complete lattice, it is **cartesian closed** (with meet
as product). The internal hom is:

```
[s₁, s₂] = ∨ { t | s₁ ∧ t ⊑ s₂ }
```

The largest state that, combined with s₁ via meet, stays below s₂. This is
the **Heyting implication** — "the maximum additional knowledge compatible
with s₁ that doesn't exceed s₂."

**Swarm instantiation**: The internal hom answers "what can we learn that's
compatible with what we know (s₁) without contradicting our target (s₂)?"
This is the scoping problem: given current knowledge and a frontier goal,
what's the space of valid investigations?

---

## 8. The 2-Category (Meta-Level)

### 8.1 Definition: **Swarm₂**

| Level | Component | Definition |
|-------|-----------|-----------|
| 0-cells | Swarm states | Objects of **State** |
| 1-cells | State transformations | Endofunctors `S_op: State → State` (the swarm operator) |
| 2-cells | Meta-transformations | Natural transformations `α: S_op ⟹ S_op'` (protocol improvements) |

The 1-cells are the different versions of the swarm operator. Each protocol
change, dispatch rule update, or maintenance check modification produces a
new 1-cell.

The 2-cells are the meta-expert's actions: natural transformations that
improve how the swarm operator works. The Y-combinator structure from
SWARM-EXPERT-MATH.md §4 lives here:

```
Ŝ: End(State) → End(State)    (meta-operator: takes S_op, returns improved S_op')
```

The fixed point `S_op* = lfp(Ŝ)` is the 1-cell that is invariant under all
2-cell improvements — the self-stabilizing protocol.

### 8.2 Vertical and Horizontal Composition

**Vertical** (2-cell composition): Apply two successive protocol improvements.

```
α: S_op ⟹ S_op'    (first improvement)
β: S_op' ⟹ S_op''   (second improvement)
β ∘ α: S_op ⟹ S_op'' (combined improvement)
```

**Horizontal** (Godement product): Two independent meta-improvements compose:

```
α ⊗ β: (S_op₁ ⊗ S_op₂) ⟹ (S_op₁' ⊗ S_op₂')
```

This is concurrent meta-improvement: two sessions independently improving
different aspects of the protocol.

### 8.3 Why 2-Category and Not Higher

Could there be 3-cells (meta-meta-transformations)? In principle, yes —
modifications to how the swarm improves its improvement process. But:

1. **Type separation prevents regress** (L-357): E_meta → ΔS is 1st order;
   Ŝ → new S_op is 2nd order. There is no observed 3rd order.
2. **Empirical check**: No session has ever modified the meta-improvement
   process itself (as distinct from improving the protocol). The 3-cell
   level is not populated.
3. **Parsimony**: Truncate at 2 unless evidence demands 3.

---

## 9. The Node-Domain-State Triangle

The three main categories are connected by a **commutative triangle** of
functors:

```
        Node
       ↙    ↘
  Act ↙      ↘ Obs
    ↙          ↘
State ←——————→ Dom
      π_D / ι_D    Colony presheaf F
```

**Commutativity condition**: The action of a node on the state, when
restricted to a domain, equals the node's observation of that domain
followed by its domain-specific response:

```
π_D ∘ Act(n) ≅ respond_D ∘ Obs_D(n)
```

"What a node does to domain D's state = what the node observes about D,
processed through D's expert response." This is the categorical formulation
of the expert dispatch pipeline:

1. Node observes domain state (Obs_D)
2. Domain-specific expertise generates response (respond_D)
3. Response modifies global state via embedding (ι_D)

### 9.1 SIG-1 Coordination: Generalization as Functor Extension

SIG-1 says: "all participants modeled as nodes with properties, not
hardcoded special cases."

Categorically: **extending the Node category** by adding new objects
(node types) requires only defining the functor values at those new objects.
The triangle commutes for any node type — the protocol is node-agnostic
because the functors are defined on all of **Node**, not on specific objects.

Adding a new node type `cron-trigger`:
- `Act(cron-trigger) = T: State → State` (automated session triggering)
- `Capabilities(cron-trigger) = {session-initiate, scheduled-dispatch}`
- `Bandwidth(cron-trigger) = medium`
- `Persistence(cron-trigger) = permanent`

No protocol change needed. The functors extend naturally. THIS is SIG-1
realized categorically: generalization = functor extension.

---

## 10. Kan Extensions — Predicting Unvisited Domains

### Left Kan Extension

Given functor `G: Dom_visited → Set` (knowledge about visited domains) and
inclusion `J: Dom_visited ↪ Dom`, the **left Kan extension**:

```
Lan_J G : Dom → Set
```

gives the "best prediction" of knowledge for unvisited domains, using only
what we know from visited ones, in the most optimistic way.

**Swarm instantiation**: When dispatch_optimizer.py has zero data for a
domain, UCB1 assigns exploration bonus. The left Kan extension formalizes
this: it's the minimal extension of known domain knowledge to cover all
domains. The UCB1 exploration term IS an approximation of the left Kan
extension — it assigns maximum optimistic value to the unknown.

### Right Kan Extension

```
Ran_J G : Dom → Set
```

gives the most conservative prediction. "What can we guarantee about
unvisited domains based on visited ones?"

**Swarm instantiation**: The ISO atlas entries with high Sharpe scores
provide the right Kan extension — conservative structural transfers that
we're confident apply to new domains. An ISO-1 (optimization under
constraint) mapping with Sharpe 5 means we can reliably predict that
any new domain will exhibit optimization-under-constraint behavior.

---

## 11. Coherence Theorems and Swarm Properties

### 11.1 Mac Lane's Coherence Theorem (Monoidal)

All diagrams of associators and unitors in (State, ∨, ⊥) commute. This is
trivially satisfied because lattice join is strictly associative and
commutative — the associators and unitors are identities. The swarm's
monoidal structure is **strict**.

**Operational meaning**: It doesn't matter how you group concurrent session
merges. (s₁ ∨ s₂) ∨ s₃ = s₁ ∨ (s₂ ∨ s₃). Merge order is irrelevant for
the final state. This is the categorical proof of the CALM theorem mapping
from SWARM-EXPERT-MATH.md §11: monotone append-only operations are
coordination-free.

### 11.2 Freyd's Adjoint Functor Theorem

If **State** is complete (it is) and `π_D` preserves all limits (it does,
as a projection), then `π_D` has a left adjoint. That left adjoint is `ι_D`.
This gives the projection-embedding adjunction (§3.1) *for free* from the
completeness of the state lattice.

**Operational meaning**: Domain specialization (projection) and integration
(embedding) are guaranteed to form a Galois connection. You don't need to
prove consistency of each domain's integration — it follows from the lattice
structure.

### 11.3 Density Theorem (Yoneda Corollary)

Every presheaf is a colimit of representables:

```
F ≅ colim_{(d, x) ∈ ∫F} y(d)
```

where ∫F is the category of elements of F.

**Swarm instantiation**: The colony presheaf (all domain-local states) is
reconstructible from the ISO atlas profiles (representable presheaves) via
colimits. The swarm's total knowledge is the colimit of its structural
transfer relationships. This is why domain integration works: local domain
states glue along their ISO-mediated overlaps into the global state.

---

## 12. Summary: Categorical Inventory

| # | Structure | Category Theory | Swarm Mechanism |
|---|-----------|----------------|-----------------|
| 1 | **State** | Poset category (complete lattice) | Git repo states under ⊑ |
| 2 | **Node** | Category with signal-channel morphisms | NODES.md participants (SIG-1) |
| 3 | **Dom** | Category with ISO morphisms | 46 domains + isomorphism atlas |
| 4 | **Know** | Poset category (partial order) | knowledge_state.py classifications |
| 5 | **Expert** | Poset category (capability subsumption) | tools/personalities/ |
| 6 | Action functor | `Act: Node → [State, State]` | Node actions on swarm state |
| 7 | Projection functor | `π_D: State → State_D` | Reading domain-local state |
| 8 | Embedding functor | `ι_D: State_D → State` | Writing findings to global state |
| 9 | Colony presheaf | `F: Domᵒᵖ → Set` | Domain colonies with restriction maps |
| 10 | Compaction functor | `K: State → State` | compact.py proxy-K reduction |
| 11 | Knowledge functor | `κ: State → Know` | knowledge_state.py |
| 12 | Dispatch functor | `Δ: Dom × Expert → [State,State]` | dispatch_optimizer.py |
| 13 | Projection ⊣ Embedding | Galois connection | Domain read/write cycle |
| 14 | Compaction ⊣ Inclusion | Compression adjunction | compact.py ↔ full state |
| 15 | Free ⊣ Forgetful | Knowledge initialization | New frontiers → BLIND-SPOT default |
| 16 | Yoneda embedding | `y: Dom → [Domᵒᵖ, Set]` | ISO atlas = domain encoding |
| 17 | Left Kan extension | `Lan_J G: Dom → Set` | UCB1 exploration of unvisited domains |
| 18 | Right Kan extension | `Ran_J G: Dom → Set` | Conservative ISO-based transfer |
| 19 | Coproduct (pushout) | `s₁ ∨ s₂` | Git merge of concurrent sessions |
| 20 | Equalizer | `eq(E₁, E₂)` | Council consensus on conflicting claims |
| 21 | Global sections (limit) | `Γ(F) = lim F` | Globally consistent beliefs/principles |
| 22 | Symmetric monoidal | `(State, ∨, ⊥)` | Parallel session composition |
| 23 | Cartesian closed | Internal hom `[s₁, s₂]` | Scoping of valid investigations |
| 24 | Enrichment (cal) | `State` over `([0,1], ·, 1)` | Expect-act-diff calibration |
| 25 | Enrichment (Sharpe) | `Dom` over `([0,5], ≥)` | ISO atlas evidence quality |
| 26 | 2-category | **Swarm₂** | Meta-level: protocol improvement |
| 27 | H¹ cohomology | Presheaf cohomology | CHALLENGES.md = gluing obstructions |

**Claim**: These 27 categorical structures, with their explicit
object/morphism/functor definitions, constitute a complete categorical
formalization of the swarm as of S390. "Complete" means: every load-bearing
swarm mechanism (state evolution, node interaction, domain structure, expert
dispatch, knowledge management, meta-improvement) has a categorical
counterpart, and the counterpart is falsifiable against the mechanism.

---

## 13. Open Questions

1. **Topos structure**: Is **[Domᵒᵖ, Set]** a topos? If so, the subobject
   classifier Ω gives a canonical notion of "partial truth" for domain
   knowledge. The internal logic of the presheaf topos could formalize
   the swarm's uncertainty.

2. **Higher cohomology**: H¹ classifies gluing failures (L-427). Do H²
   obstructions exist? H² would measure "failures of failure-repair" — meta-
   level incoherence in how challenges are processed.

3. **Operads**: Expert composition has operadic structure — an n-ary operation
   "run n experts on domain d and merge" that satisfies associativity and
   equivariance. Does the operad structure reveal anything about optimal
   expert bundling (F-EXP2)?

4. **Enrichment upgrade**: Could enrichment over ([0,1], ·, 1) be upgraded
   to enrichment over a more structured category (e.g., probability measures)?
   This would give a full probabilistic categorical framework.

5. **Double category**: The 2-category might more naturally be a **double
   category** where horizontal 1-cells are state transitions and vertical
   1-cells are protocol changes. This would make the independence of these
   two dimensions explicit.

---

*Extends*: `docs/SWARM-EXPERT-MATH.md` (lattice theory and presheaf treatment)
*Tests*: Each categorical structure maps 1:1 to a swarm mechanism in column 4 of the summary table. If any mapping is vacuous (no operational counterpart), the structure should be removed.
*Related*: L-357 (Y-combinator), L-427 (H¹ classification), L-274 (atlas as compression), NODES.md (SIG-1), ISO-ATLAS.md
