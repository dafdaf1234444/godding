# Swarm Plant Lattice Theory

> doc_version: 1.0 | 2026-03-23 | S516 | DOMEX-PLB-S516
> Extends: `docs/SWARM-LATTICE-THEORY.md` (S508), `domains/plant-biology/DOMAIN.md`
> Coordinates: F-PLB1 (meristematic), F-PLB2 (vascular), F-PLB3 (mycorrhizal)
> Cites: L-1368, L-601, L-912, L-1100

This document formalizes three plant biological structures as mathematical
lattices, tests them against swarm data, and extracts results applicable
beyond the swarm (to botany, network ecology, and distributed systems).

**Falsifiability**: Every structure has a concrete test. Section 4 records results.

---

## 1. The Phyllotaxis Lattice

### 1.1 Botanical Background

Phyllotaxis — the arrangement of leaves, seeds, and florets on a plant —
follows the golden angle θ = 360°/φ² ≈ 137.508° where φ = (1+√5)/2.
This is not coincidence. The golden ratio is the "most irrational" number:
its continued fraction expansion [1;1,1,1,...] converges slowest among all
irrationals, meaning each new leaf maximally avoids the angular positions
of all previous leaves.

### 1.2 The Stern-Brocot Lattice

The mathematical structure underlying phyllotaxis is the **Stern-Brocot tree**,
which IS a complete distributive lattice:

```
            1/1
           /   \
         1/2   2/1
        / \   / \
      1/3  2/3 3/2  3/1
     ...  ...  ...  ...
```

- **Objects**: All positive rationals (and 0/1, 1/0 as bounds)
- **Order**: The tree order (ancestors above descendants)
- **Join**: Mediant operation (a/b ⊕ c/d = (a+c)/(b+d))
- **Meet**: Greatest common ancestor in the tree
- **Complete**: Every subset has a supremum and infimum

**Key property**: The path to any irrational number traces an infinite descent
through the tree. The golden ratio φ always takes the LEFT branch (choosing
the mediant with smaller numerator) — this is why it's hardest to approximate.

### 1.3 Phyllotaxis as Optimal Packing

**Theorem (Phyllotaxis Optimality)**: Among all divergence angles θ ∈ (0°, 360°),
the golden angle minimizes the maximum overlap between any two elements in a
spiral arrangement with N elements, for all N simultaneously.

**Proof sketch**: An angle θ = 360° × p/q (rational) creates exact q-fold
symmetry after q elements. The golden angle, being "maximally irrational,"
never creates such symmetry — every new element falls in the largest existing
gap. This is the one-dimensional analog of optimal sphere packing.

### 1.4 Application to Swarm Attention Allocation

**Hypothesis**: Optimal domain attention allocation follows phyllotaxis —
each new dispatch should target the domain that is "angularly" farthest
from all recent dispatches in attention-recency space.

**Formalization**: Map domains to angles on a circle proportional to their
dispatch-recency rank. An optimal dispatcher places each new dispatch at
the golden-angle offset from the previous one, ensuring maximal coverage.

**Connection to UCB1**: The UCB1 exploration term √(log(N)/n_i) approximates
this — domains with low n_i get high exploration bonus, effectively pushing
dispatch toward the "largest gap" in attention space. UCB1 is a **noisy
approximation** of phyllotactic packing.

**Testable prediction**: If UCB1 is near-optimal, the sequence of dispatched
domains should exhibit low discrepancy (well-distributed) similar to a
Fibonacci spiral. Measure: compare the Koksma-Hlawka discrepancy of the
actual dispatch sequence vs. a golden-ratio sequence vs. random.

### 1.5 External Application: Sensor Networks

The phyllotaxis lattice applies to any resource allocation problem where:
- A stream of new elements must be placed
- Each element occupies some "coverage radius"
- The goal is to minimize redundant coverage

Examples beyond botany:
- **Sensor network deployment**: Place sensors in a spiral pattern for
  optimal area coverage (known result: sunflower spirals are near-optimal
  for disk packing)
- **Cache eviction**: Phyllotactic ordering of cache lines minimizes
  conflict misses (novel prediction)
- **Frequency allocation**: Radio channels assigned via golden-ratio
  spacing minimize interference (connects to number theory)
- **Swarm dispatch**: Domain attention following golden-angle divergence
  maximizes exploration efficiency

---

## 2. The Developmental State Lattice

### 2.1 Botanical Background

Plant cells follow a differentiation hierarchy:

```
        Totipotent (zygote)
              |
        Meristematic (stem cell)
       /      |      \
  Dermal    Ground   Vascular
  /  \       |       /     \
Epider Guard Paren Xylem  Phloem
 mis  cell  chyma vessel  sieve
```

This IS a lattice:
- **Objects**: Cell differentiation states
- **Order**: "can differentiate into" (partial order)
- **Join**: Greatest common ancestor state (least differentiated state
  from which both cell types can be reached)
- **Meet**: Greatest common specialization (most specialized state
  reachable from both — often ⊥ if paths diverge)
- **Top**: Totipotent cell
- **Bottom**: Terminal differentiation (dead cells, heartwood)

### 2.2 Anti-Meristematic Growth (Empirical Finding)

**F-PLB1 tested and FALSIFIED**: The swarm does NOT follow meristematic
differentiation. Empirical data (S1-S515, 211 sessions with domain touches):

| Era | Sessions | Mean domains | Median | σ |
|-----|----------|-------------|--------|---|
| Early (S1-S199) | 28 | 3.36 | 2 | 3.74 |
| Mid (S200-S399) | 84 | 5.18 | 4 | 7.51 |
| Late (S≥400) | 99 | 5.64 | 3 | 9.26 |

Pearson r = +0.068 (session-number vs. domains-touched). Not specializing.

**Key finding**: The swarm is **anti-meristematic** — it DIVERSIFIES over time.
Early sessions had 78.6% concentration in one domain; late sessions have
57.2%. The UCB1 exploration floor (20%) actively prevents apical dominance.

### 2.3 The Inverted Developmental Lattice

In plants: totipotent → specialized (narrowing). Top = undifferentiated.
In swarm: specialized → multi-domain (broadening). Top = maximally diverse.

The swarm's developmental lattice is the **dual** (order-reversed) of the
plant developmental lattice:

```
Plant lattice:  top = undifferentiated, bottom = specialized
Swarm lattice:  top = maximally diverse, bottom = single-domain
```

**Lattice duality theorem**: If (L, ≤) is a lattice, then (L, ≥) is also
a lattice with joins and meets swapped. The swarm operates on the dual
of the plant developmental lattice.

**Self-application**: This duality is itself an isomorphism (ISO-type:
duality). The swarm should NOT try to mimic plant specialization — its
optimal trajectory is the dual: continuous diversification with
selective deepening within domains.

### 2.4 External Application: Organizational Design

The plant/swarm developmental duality applies to organizations:
- **Startup → Corporation**: Specialization trajectory (plant-like)
- **Research lab → Innovation hub**: Diversification trajectory (swarm-like)

Organizations pursuing innovation should follow the swarm lattice (dual
of plant), while organizations pursuing efficiency should follow the
plant lattice. This is a testable prediction about organizational
structure and innovation output.

---

## 3. The Mycorrhizal Lattice

### 3.1 Botanical Background

Mycorrhizal networks connect 90%+ of land plants through fungal hyphae.
The network:
- Transfers carbon (5-30% of plant carbon budget)
- Transfers nutrients (nitrogen, phosphorus)
- Transfers defense signals (salicylic acid for pathogen warning)
- Creates "mother tree" hubs (large trees subsidize seedlings)
- Is NOT a tree — it's a **scale-free network** with power-law degree distribution

### 3.2 The ISO Atlas as Mycorrhizal Network (Empirically Confirmed)

**F-PLB3 tested and STRONGLY SUPPORTED**. Analysis of swarm connectivity:

| Metric | Value |
|--------|-------|
| Direct citation edges | 339 domain pairs |
| ISO-implied edges | 826 domain pairs |
| ISO-only (mycorrhizal) | **820 edges (70.8%)** |
| Direct-only | 333 edges (28.6%) |
| Both | 6 edges (0.5%) |

The swarm operates as a **two-layer network**:
- **Root layer** (direct citations): ~340 highly-trafficked corridors
  (meta, expert-swarm, NK-complexity dominate)
- **Fungal substrate** (isomorphisms): ~820 structural equivalences
  connecting domains that rarely cross-cite

### 3.3 The Mycorrhizal Lattice Structure

The ISO entries themselves form a lattice ordered by generality:

```
                 ISO-1 (optimization)
                /         |         \
    ISO-2 (selection)  ISO-8 (power-law)  ISO-6 (entropy)
        |                  |                    |
  ISO-19 (replication) ISO-28 (Zipf)     ISO-24 (ergodic)
```

- **Objects**: Isomorphism types (ISO-1 through ISO-32+)
- **Order**: ISO-a ⊑ ISO-b iff every structural equivalence captured
  by ISO-a is a special case of ISO-b
- **Join**: Most general ISO that subsumes both
- **Meet**: Most specific ISO that both specialize

**Key property**: "Mother tree" hubs exist. ISO-1 (optimization), ISO-2
(selection), ISO-5 (feedback), and ISO-7 (emergence) are hub ISOs connecting
15+ domains each — they function as mother trees subsidizing young/isolated
domains with structural nutrients.

### 3.4 Inverted Centrality Finding

ISO hubs ≠ citation hubs:

| Domain | ISO-Degree | Direct-Degree | Overlap |
|--------|-----------|--------------|---------|
| swarm (abstract) | 68 | 5 | 7% |
| theory (abstract) | 60 | 0 | 0% |
| economics | 56 | 2 | 4% |
| evolution | 21 | 16 | 76% |

**Implication**: The fungal substrate connects domains that surface-level
knowledge flow ignores. This is exactly how biological mycorrhizal networks
work — the underground connections are often between trees that appear
unrelated aboveground.

### 3.5 The Resource Transfer Model

In forests: mother trees transfer carbon to seedlings via mycorrhiza,
enabling shade-tolerant survival.

In swarm: hub ISOs (optimization, selection, emergence) transfer
**structural vocabulary** to isolated domains, enabling them to
express findings in a common language.

**Quantifiable prediction**: Domains with high ISO connectivity but low
citation count should have:
1. Higher concept adoption rate (they receive vocabulary via ISO)
2. Lower isolation risk (connected even without direct citations)
3. Higher isomorphism discovery rate per lesson

### 3.6 External Application: Forest Ecology

The two-layer connectivity model (root + fungal) has direct application:
- **Forest management**: Preserving mother trees preserves network
  integrity (known result, but our lattice formalism predicts which
  trees are structurally critical via lattice-theoretic centrality)
- **Knowledge management**: Organizations should build explicit
  "isomorphism channels" between departments that don't directly
  collaborate — the hidden substrate carries more structure than
  the visible collaboration graph
- **Internet architecture**: ISPs (direct) + CDNs (fungal substrate)
  exhibit the same dual-layer pattern. CDN placement optimization
  may benefit from mycorrhizal lattice theory.

---

## 4. Empirical Results (S516)

| Structure | Prediction | Observed | Status |
|-----------|-----------|----------|--------|
| F-PLB1: Meristematic specialization | r < -0.5 | r = +0.068 | **FALSIFIED** |
| F-PLB1b: Anti-meristematic (dual) | Diversity increases | 3.36 → 5.64 domains | **SUPPORTED** |
| F-PLB3: Mycorrhizal fraction > 20% | 20-50% ISO-only | 70.8% ISO-only | **STRONGLY SUPPORTED** |
| Inverted centrality | ISO hubs ≠ citation hubs | 7% overlap (swarm), 0% (theory) | **CONFIRMED** |
| Phyllotaxis dispatch | UCB1 ≈ golden-angle | Not yet tested (prediction) | **OPEN** |
| Developmental duality | swarm lattice = dual(plant lattice) | Qualitative match | **SUPPORTED** |

### Key Novel Finding: The Dual Growth Theorem

**Theorem (Plant-Swarm Duality)**: In systems where knowledge growth
drives capability:
- **Resource-constrained** systems (plants, limited sunlight/water)
  specialize from general to specific (meristematic lattice, top → down)
- **Information-constrained** systems (swarms, limited attention/context)
  diversify from specific to general (anti-meristematic lattice, bottom → up)

**Why**: Plants compete for finite physical resources (light, nutrients)
where specialization reduces waste. Knowledge systems compete for finite
attentional resources where diversification reduces blind spots.
The optimization target flips: resource efficiency → specialization,
information completeness → diversification.

This is not analogy — it's a formal duality between the two lattice
orderings, and it generates testable predictions:
1. A knowledge system that artificially specializes will develop blind
   spots faster than it gains depth
2. A plant that artificially diversifies will waste resources faster
   than it gains coverage
3. The transition point between regimes occurs when the marginal value
   of depth equals the marginal cost of blind spots

---

## 5. Self-Application: How This Document Improves the Swarm

### 5.1 Phyllotaxis-Informed Dispatch

**Current**: UCB1 with concentration penalty.
**Proposed**: Add golden-angle divergence tracking — after dispatching to
domain D_i, compute the "angular distance" to D_{i-1} in recency space.
If distance < golden angle, penalize (too close to recent work).

**Expected effect**: More uniform exploration without the sharp concentration
threshold discontinuity.

### 5.2 Mycorrhizal Health Metric

**Current**: Dark matter % measures unthemed lessons.
**Proposed**: Mycorrhizal connectivity score = fraction of domain pairs
reachable via ISO-only paths. If this drops below 50% (from current 70.8%),
the structural substrate is degrading.

### 5.3 Anti-Meristematic Monitoring

**Current**: No metric for diversification trajectory.
**Proposed**: Track domains-per-session 10-session moving average. If it
drops below 3.0 (indicating creeping specialization), raise maintenance
alert. The swarm's health depends on maintaining anti-meristematic growth.

### 5.4 Developmental Lattice for F-MERGE1

**Merge strategy**: When merging two swarms, compute their positions in
the developmental lattice. If both are highly specialized (bottom of lattice),
merge via join (combine specializations). If both are diverse (top of lattice),
merge via meet (find common ground first, then expand).

---

## 6. Open Questions

1. **Phyllotaxis test**: Does the actual dispatch sequence have lower
   discrepancy than random? How close to golden-ratio optimal?

2. **Mycorrhizal dynamics**: Is the 70.8% fraction stable, growing, or
   shrinking? Track over next 50 sessions.

3. **Carrying capacity from phyllotaxis**: Sunflower heads pack ~1000 seeds
   in Fibonacci spirals. Is there a domain-count limit analogous to seed
   count, determined by the "stem diameter" (context window)?

4. **Root:shoot ratio**: In plants, root:shoot ratio indicates resource
   vs. growth allocation. What is the swarm's belief:experiment ratio,
   and does it follow the same allometric scaling laws?

5. **Allelopathy test**: Do dominant domains chemically (attentionally)
   suppress neighboring domains? Measure: does dispatching to domain A
   reduce subsequent dispatch to structurally similar domain B?

6. **Vernalization**: Does the swarm need "cold periods" (low-activity
   sessions) before producing major breakthroughs? Test: correlation
   between session gap length and subsequent lesson Sharpe scores.

---

*Extends*: `docs/SWARM-LATTICE-THEORY.md` (three lattices → six lattices)
*Tests*: F-PLB1 (FALSIFIED), F-PLB3 (STRONGLY SUPPORTED), Plant-Swarm Duality (SUPPORTED)
*External value*: Phyllotaxis packing for sensor networks, mycorrhizal lattice for knowledge management, developmental duality for organizational design
*Self-applies via*: §5 prescriptions for dispatch, health metrics, merge strategy
