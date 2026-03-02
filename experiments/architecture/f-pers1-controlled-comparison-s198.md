# F-PERS1: Controlled Comparison — Explorer vs Skeptic on F-CON2
Session: S198 | Date: 2026-02-28
Frontier tested: F-CON2 (Can lane contracts prevent concurrent edits to shared meta-files?)
Method: Same analyst, same source material, two behavioral overlays run sequentially.
Hypothesis: Explorer produces more new questions, broader hypotheses; Skeptic produces fewer but better-evidenced claims.

---

## Subject: F-CON2 Background

F-CON2 asks whether an "intent declaration" contract (lane ID + files-touched + window) can
reduce A3 conflicts (concurrent edits to shared meta-files like tasks/SWARM-LANES.md,
tasks/NEXT.md, memory/INDEX.md). Status: OPEN — no contract schema defined.

Known data:
- A3 collisions observed: at least L-093 (first confirmed collision)
- Collision rate not measured; no baseline established
- Nash contracts from game-theory domain noted as analog
- No enforcement mechanism exists

---

## Pass 1: Explorer Lens

*Behavioral overrides active: accumulate hypotheses freely; open ≥2 sub-questions per resolved
point; cross-domain connections; mark PARTIAL not RESOLVED; adjacency notes.*

### Analysis

**Starting question**: Can lane contracts prevent concurrent edits?

Immediately opens: *What ARE lane contracts, actually?* The word "contract" hides three distinct
concepts:
- **Claim contract**: "I will touch these files" (reservation)
- **Notification contract**: "I am touching these files right now" (broadcast)
- **Integrity contract**: "These files should only be touched under these conditions" (invariant)

They have completely different enforcement mechanisms and failure modes. The F-CON2 design assumes
a *notification* contract, but what we probably want is a *claim* contract.

**Cross-domain connection — OS file locking**: Intent declarations map to advisory locks.
Advisory locks work when all agents cooperate; they fail when any agent ignores the protocol.
Swarm agents spawn without lock-checking today. This generalizes: contracts only reduce conflicts
if dispatch includes a lock-check step.

**Cross-domain connection — database transaction isolation**: The "intent declaration window" is
a transaction scope. SWARM-LANES rows ARE the transaction log. Does appending to SWARM-LANES
constitutionally guarantee serialization? If so, F-CON2 may already be partially solved.

**Cross-domain connection — Nash contracts (game theory)**: For contracts to be stable
equilibria, defecting (ignoring the contract) must have a cost. What's the cost today? None —
agents that skip contracts pay 0 penalty. Contract design must include a detection + penalty loop.

**New questions opened** (Explorer generates freely):
1. Can the existing SWARM-LANES append protocol serve as a lightweight contract log?
2. Is A3 rate actually a problem, or is it rare enough that contracts add more overhead than
   they prevent?
3. Can contracts be machine-checkable (pre-commit hook verifies no declared file edited outside
   its registered window)?
4. What's the minimum viable contract schema that doesn't add per-session overhead?
5. Does contract compliance correlate with agent type (human vs Claude vs Codex)?
6. Could contracts be "soft" (advisory, like git branches) vs "hard" (blocking)?
7. If agents run concurrently without coordination, what's the theoretical maximum
   collision-free throughput (graph coloring / file conflict problem)?

**Hypotheses (labeled THEORIZED)**:
- THEORIZED: SWARM-LANES is already functioning as a soft contract log; A3 rate is low because
  agents read it before acting (correlated with L-237 anti-repeat protocol)
- THEORIZED: Hard contracts will increase session overhead by ≥30% (each agent must read+register
  before touching any shared file)
- THEORIZED: A Nash-stable contract schema requires exactly three fields: (lane-id, files-list,
  session-start), and sessions that violate any other lane's unexpired claim should emit a bulletin

**Adjacency note**: "What else does this pattern appear in?"
- Constitution monitoring (F-CON3) uses hash-based detection after the fact. Contracts are
  proactive where F-CON3 is reactive. Together they form detect+prevent.
- CLAUDE.md itself is a contract: it defines what files are canonical and who owns them.
- F-CON2 generalizes to: "Can the swarm develop a resource-ownership protocol?"

**Explorer marking**: F-CON2 → PARTIAL (schema not defined but 3 design patterns identified;
sub-questions F-CON2a/b/c opened before any implementation begins)

### Explorer Output Metrics
- New questions generated: **7** (plus 3 THEORIZED hypotheses)
- Cross-domain links: **3** (OS locking, database transactions, Nash contracts)
- Confidence level: freely THEORIZED (no data requirement)
- Lesson candidates: 2 (contract types taxonomy; SWARM-LANES-as-contract hypothesis)
- Adjacency notes: 3
- Frontier marking: PARTIAL (not RESOLVED)
- New sub-frontiers: F-CON2a (schema types), F-CON2b (enforcement gap), F-CON2c (graph coloring)

---

## Pass 2: Skeptic Lens

*Behavioral overrides active: falsification-first; 40% belief throttle; 3 independent data
points before marking progress; 1 rigorous lesson beats 3 vague ones; no new tools without
empirical need.*

### Analysis

**First question**: Is A3 conflict actually demonstrated at a rate that justifies contract design?

Evidence inventory:
- L-093: 1 confirmed collision (single data point)
- F-CON1 baseline: lane-level C3=0.4% (1 stale open lane in 225 unique lanes) — this measures
  orphaning, not A3 file collisions
- No measured A3 baseline rate exists

**Falsification test for "contracts prevent A3 collisions"**:
*If contracts are implemented and A3 rate drops below baseline, contracts work.*
*But: if A3 rate is already <2% without contracts, a 20% reduction brings it to <1.6% —
marginal benefit at non-trivial enforcement cost.*

**Challenge to the premise**: F-CON2's design assumes A3 collisions are a problem worth solving.
The only evidence is L-093 (1 event). Sample size = 1 is insufficient to justify protocol change.
Required: measure A3 rate over ≥10 sessions before designing solutions.

**What data exists**:
- git log can be queried for concurrent edits to shared files. A3 rate is measurable.
- No one has measured it (F-CON2 status: OPEN — contract schema not defined).
- This is a known unknown masquerading as a design problem.

**Conservative path forward**:
1. Measure A3 rate (git log analysis, 10-session window)
2. If rate ≥5% of sessions: proceed with contract design
3. If rate <5%: file as low-priority; invest effort elsewhere

**On cross-domain analogs**:
- OS advisory locks ARE relevant, but the analogy fails at enforcement: swarm agents cannot
  block each other (no coordinator). Advisory locks only work with 100% compliance. Current
  compliance rate: unknown.
- Nash contract equilibrium requires defection cost. Adding a cost mechanism is non-trivial
  and could break agent autonomy (CORE principles 1–3).

**Hypotheses (none — Skeptic does not theorize without data)**:
No hypotheses generated. The baseline data does not exist to form testable predictions.

**Skeptic lesson (1, rigorous)**:
*F-CON2 is premature specification: a solution designed before the problem is measured.
A3 collision rate must be empirically established before any contract schema is worth building.
Minimum evidence threshold: 10 sessions of git-log A3 analysis.*

**Skeptic marking**: F-CON2 remains OPEN. Not PARTIAL — no contract-relevant evidence exists.
Next step is measurement, not design.

### Skeptic Output Metrics
- New questions generated: **1** (what is A3 rate empirically?)
- Cross-domain links: **1** (advisory lock analogy, noted as FAILING)
- Confidence level: no hypotheses (data absent)
- Lesson candidates: **1** (premature specification anti-pattern)
- Adjacency notes: 0
- Frontier marking: OPEN (unchanged — no evidence justifies PARTIAL)
- New sub-frontiers: 0

---

## Comparison Table

| Metric                     | Explorer | Skeptic | Delta |
|----------------------------|----------|---------|-------|
| New questions opened       | 7        | 1       | +6    |
| Cross-domain links         | 3        | 1 (failed) | +2  |
| Hypotheses formed          | 3        | 0       | +3    |
| Lesson candidates          | 2        | 1       | +1    |
| Adjacency notes            | 3        | 0       | +3    |
| Frontier status change     | PARTIAL  | OPEN    | diverge |
| Sub-frontiers opened       | 3        | 0       | +3    |
| Caution flags raised       | 0        | 2       | -2    |

---

## F-PERS1 Finding

**Confirmed**: Explorer and Skeptic produce measurably different outputs on identical input.

Explorer output profile: high breadth, many new questions, optimistic status advancement,
cross-domain linking. Skeptic output profile: narrow, evidence-demanding, no status advancement
without data, exactly 1 high-quality lesson.

**Key divergence point**: F-CON2 status. Explorer marks PARTIAL (3 design patterns identified).
Skeptic marks OPEN unchanged (design is premature without measurement data). Both are internally
consistent. Neither is "wrong." They serve different phases:
- Skeptic is appropriate FIRST (measure A3 rate before designing)
- Explorer is appropriate SECOND (generate candidate schemas once problem is confirmed)

**This divergence is STRUCTURALLY USEFUL**: running both on the same frontier produces a
meta-recommendation: "measure first (Skeptic), then design (Explorer)." Neither alone would
produce that sequencing insight.

**Implication for F104**: Personality dispatch IS worth investing in. The value is not in
producing more output (Explorer wins on volume) but in producing phase-appropriate output.
Swarm dispatch should consider frontier phase: OPEN = Skeptic first; PARTIAL = Explorer;
RESOLVED-candidate = Skeptic again for falsification.

---

## Evidence for F-PERS2 (tangential)

The Skeptic personality produced fewer hypotheses not because of "lesson density threshold"
but because of a hard behavioral rule (falsification-first). F-PERS2's alternative hypothesis
(orphaned personalities cause low synthesizer output) may be wrong — low output may simply be
correct behavior for Skeptic on data-sparse frontiers.

---

## Next steps

1. Run A3 rate measurement (git log analysis, 10 sessions) — Skeptic prescription
2. Once measured: dispatch Explorer on F-CON2 schema design if A3 rate ≥5%
3. Test F-PERS1 finding on a second frontier (F-CON3? A domain frontier?) to confirm
   divergence pattern holds across domains
4. File L-XXX: "Phase-matched personality dispatch — Skeptic first on OPEN, Explorer on PARTIAL"

Status: F-PERS1 PARTIAL (1 controlled comparison complete, 1 frontier tested).
Artifact: experiments/architecture/f-pers1-controlled-comparison-s198.md
