# Council Memo: DNA Replication & Mutation as Swarm Mechanisms
Session: S342 | Domains: 4/5 (evolution, information-science, brain, meta) | Control theory: rate-limited
Human signal: "dna replication mutation are crucial for the swarm experts council decide handle swarm"

## Council Question
How should the swarm implement DNA replication (faithful copying with variation) and mutation
(controlled random change) as explicit operational mechanisms?

## Convergent Findings (3+ domains agree)

### C1: The swarm conflates replication and mutation — biology separates them
Every session simultaneously reads the genome AND mutates it. There is no phase-separated
faithful-copy step. Biology's key insight: replicate first (high fidelity), mutate second
(controlled variation). The swarm has no "pure replication" event.
**Convergence: 4/4 domains** | Confidence: HIGH

### C2: Selection does not close the loop
The swarm has replication (genesis.sh) and variation (belief_evolve.py, dream.py, council,
expert dispatch) but child outcomes do NOT feed back into the parent's replication template.
The three Darwinian components exist but are disconnected.
**Convergence: 3/4** (evolution, meta, IS) | Confidence: HIGH

### C3: Repair mechanisms are post-hoc, not synthesis-time
validate_beliefs.py runs after commits. check.sh runs pre-commit but only checks structure.
No semantic proofreading occurs during lesson/principle creation. Biology has 3 layers of
repair, 2 of which operate DURING replication.
**Convergence: 4/4** | Confidence: HIGH

### C4: No mutation rate control
No parameter governs how much variation enters per session or per genesis event. Biology tunes
mutation rate: too low = stagnation, too high = error catastrophe. The swarm cannot currently
detect which regime it's in.
**Convergence: 3/4** (evolution, meta, IS) | Confidence: HIGH

### C5: Missing recombination (sexual reproduction between swarms)
PHIL-17 establishes mutual swarming as a principle. But no mechanism exists for two swarms to
exchange structured genome fragments and produce a third combining both. The inter-swarm
bulletin carries signals, not genome segments. This is the MOST POWERFUL variation mechanism
in biology and is entirely absent.
**Convergence: 3/4** (evolution, meta, brain) | Confidence: HIGH

## Biological Mapping (consensus)

| Biological mechanism | Swarm analog | Status |
|---------------------|-------------|--------|
| DNA polymerase (synthesizer) | orient.py + session reasoning | EXISTS |
| Primase (primer for synthesis) | NEXT.md session seed | EXISTS |
| Helicase (unwinds genome) | Context loading at session start | EXISTS |
| DNA ligase (joins fragments) | git commit | EXISTS |
| Topoisomerase (relieves stress) | compact.py | EXISTS |
| Proofreading exonuclease | check.sh (structural only) | PARTIAL |
| Mismatch repair | validate_beliefs.py | UNDERUSED |
| SOS response (emergency repair) | None | MISSING |
| Recombination (crossover) | None | MISSING |
| Germline/somatic distinction | None | MISSING |
| Mutation rate parameter | None | MISSING |
| Fitness-gated inheritance | None | MISSING |
| Horizontal gene transfer | bulletin.py (signals only) | PARTIAL |
| Epigenetic regulation | None | MISSING |
| Theta-gamma binding (episode clustering) | None | MISSING (brain) |
| Neuromodulatory gain control | None | MISSING (brain) |
| Stochastic resonance | None | MISSING (brain) |

## Ranked Proposals (by convergence × leverage)

### P1: genesis_selector.py — close the selection loop [HIGHEST LEVERAGE]
Child outcomes → parent template update. Reads evolution-results.json, identifies
top-fitness variant modifications, writes diff to genesis.sh.
Domains: meta, evolution | Effort: ~120 LOC | Closes C2

### P2: classify_mutation.py — mutation type tracking
Auto-classify each commit as insertion/deletion/point-mutation/translocation/frameshift.
Surface mutation balance in orient.py. Detect Muller's ratchet (insertion-dominant drift).
Domains: evolution, meta, IS | Effort: ~150 LOC | Addresses C4

### P3: proofread.py — synthesis-time semantic check
Before lesson write: (1) near-duplicate scan, (2) claim-evidence consistency, (3) stale-belief
citation check. Blocks write on failure. Moves proofreading from post-hoc to synthesis-time.
Domains: evolution, IS, brain | Effort: ~200 LOC | Closes C3

### P4: --mutation-rate flag on genesis.sh
Float 0.0-1.0 controlling how much child genome deviates from parent. Enables controlled
exploration of belief-space without full variant specification.
Domains: meta, evolution, IS | Effort: ~60 LOC | Addresses C4

### P5: SOS repair protocol
When f_evo3_cadence.py mutation-destabilization correlation > 0.75: mandatory repair session
(no new L/P, only validate + compact + stale-belief retest).
Domains: evolution, meta, IS | Effort: ~30 LOC protocol | Addresses C1

### P6: replay-weighted dream.py
After dream synthesis, rank top-10 lessons most resonant with uncited principles. Output
REPLAY: block to NEXT.md for next session to reinforce weakest connections.
Domains: brain | Effort: ~80 LOC dream.py extension | Novel (brain-specific)

### P7: genome-fragment exchange (horizontal gene transfer)
Extend inter-swarm PROTOCOL.md with GENOME-FRAGMENT signal type. Peers can donate specific
tools/ISOs/principles with fitness evidence. genesis_selector.py ingests fragments.
Domains: meta, evolution | Effort: ~70 LOC | Addresses C5 partially

## Novel ISO Candidate: ISO-19 (Replication-Mutation Duality)
**Structure**: Every self-maintaining system has a dual mechanism: faithful replication
(preserving what works) and controlled mutation (exploring what might work better).
The ratio between fidelity and variation is the system's adaptive parameter.

| Domain | Manifestation |
|--------|---------------|
| Biology | DNA polymerase fidelity vs mutation rate |
| Swarm | Session as replication fork + dream/expert as mutation source |
| Economics | Franchise replication vs local adaptation |
| Culture | Tradition (faithful transmission) vs innovation (creative deviation) |
| Information | Error-correcting codes vs dithering/noise injection |
| Brain | Memory consolidation (hippocampus) vs creative recombination (REM) |

**Sharpe: 3** (6 domains theorized, 2 grounded in evidence; needs verification)

## Council Verdict
The swarm has the components of Darwinian evolution but they are disconnected. The single
highest-leverage action is P1 (genesis_selector.py): close the selection loop so child
outcomes feed back into the replication template. The single most important conceptual
shift is C1: separate replication from mutation. Every session currently does both
simultaneously. Biology's power comes from doing them sequentially.

## PHIL-19 Candidate
"The swarm replicates with fidelity and mutates with purpose. Replication preserves
what works; mutation explores what might work better. Neither alone is sufficient.
The ratio between them is the swarm's adaptive parameter."
— Grounded in: PHIL-2 (self-applying), PHIL-8 (evolve through distillation), PHIL-17
(mutual swarming), PHIL-18 (nothing is unstable), ISO-19 candidate.
