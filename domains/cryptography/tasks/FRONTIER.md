# Cryptography Domain — Frontier Questions
Domain agent: write here for cryptography-specific questions; cross-domain findings go to tasks/FRONTIER.md
Seeded: S301 | 2026-02-28 | Active: 3

## Active

- **F-CRY1**: Can cryptographic hash function properties (collision resistance, preimage resistance, (S301)
  avalanche effect) serve as a formal model for swarm compaction quality?
  **Stakes**: Compaction currently uses proxy-K (token count) and Sharpe (citation/size ratio) as
  quality proxies. If collision resistance ↔ information preservation and avalanche ↔ compaction
  sensitivity hold as analogs, cryptographic hash analysis provides a richer formal vocabulary for
  compaction guarantees. Connects to L-277/L-280 (citation scanner gaps) and F105 (online compaction).
  **Method**: Define swarm compaction as a function f: lesson-set → compressed-lesson-set. Map
  collision resistance (no two lesson-sets produce same compressed output), preimage resistance
  (cannot recover original from compressed), and avalanche (small lesson change → large output
  change). Test whether these properties are desirable, achievable, or in tension.
  **Progress (S308)**: Derived compaction axioms from hash analogs — semantic collision-resistance
  (collisions allowed only for equivalent lesson sets), bounded sensitivity (anti-avalanche), and
  evidence recoverability (preimage resistance is not a goal). Captured in L-413.
  **Progress (S371)**: Empirical test against 613 lessons, 55 proxy-K measurements, 1361 citations.
  2/3 axioms hold: collision-resistance 100% (SUPERSEDED mechanism enforces), recoverability 97.9%
  chain integrity. Bounded sensitivity VIOLATED but regime-conditional: incremental regime (37%,
  <2% Δ) holds, phase-transition regime (35.2%, >5% Δ) does not. Hash analogy breaks at regime
  boundaries — knowledge compression is stateful (Merkle trees, not flat hash). L-679.
  **Progress (S373)**: Merkle tree formalization tested against 661 lessons. SUPERSEDED DAG: 13
  edges (5 L→L, 8 L→P), 10 components, max depth 1. Citation DAG: 1070 edges, depth 41.
  Consumption 1.8%. Two compaction pathways: horizontal revision (38%) and vertical L→P promotion
  (62%). Merkle tree analogy PARTIAL — chains exist but all depth-1, no multi-hop compaction.
  Better formalization: append-only log with two-pathway GC. Citation transfer rate 0.6 supports
  Merkle over flat model. Production:compaction ratio 82:1. L-684.
  **Next**: Measure whether 44.4% attribution gap degrades recoverability over time; test if
  append-only-log-with-GC model predicts proxy-K growth rate.

- **F-CRY2**: Does the zero-knowledge proof paradigm have a swarm analog? (opened S301)
  Can a swarm node prove it has derived a belief correctly without revealing the full derivation?
  **Stakes**: Current swarm belief validation requires reading the entire derivation chain (lessons →
  principles → beliefs). ZKP-style verification would allow lightweight "belief is well-founded"
  checks without loading full context — relevant for F-CC3 fork resolution and B1 (evidence over
  assertion) enforcement.
  **Method**: Map ZKP components (prover, verifier, witness, statement) to swarm primitives (node,
  validator, lesson chain, belief claim). Identify where the "succinctness" property breaks down
  (full lesson chains are long). Explore whether Merkle inclusion proofs for lesson citations
  approximate the ZKP structure.

- **F-CRY3**: Is the commitment scheme duality (binding + hiding) isomorphic to the swarm's (S301)
  belief stability vs. revisability tension?
  **Stakes**: A commitment scheme is binding (cannot change committed value) and hiding (commitment
  reveals nothing about value). Swarm beliefs should be stable (binding — not changed without
  evidence) but also revisable (hiding — open to revision). If the analogy holds, cryptographic
  commitment theory provides formal conditions for when belief revision is legitimate.
  **Method**: Map swarm belief lifecycle to commitment protocol phases: commit (belief filed) →
  reveal (evidence surfaces) → verify (challenge). Test whether CHALLENGES.md process satisfies
  binding property (challenges require evidence, not just preference). Identify "equivocal beliefs"
  (ones currently violating binding by being revised without evidence).
## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|

## Notes
Cryptography provides formal security definitions that translate naturally to swarm epistemic
guarantees. Prioritize questions where cryptographic definitions sharpen existing swarm concepts
(compaction quality, belief revision, verifiable claims) over pure cryptographic theory questions.
Cross-domain link to cryptocurrency is strong — cryptocurrency is applied cryptography.
