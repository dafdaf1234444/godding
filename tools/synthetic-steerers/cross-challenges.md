# Steerer Cross-Challenges

Cross-challenges are disagreements between steerers. They are more valuable than
any individual signal because they reveal tensions that the swarm alone cannot see.

## Format
Each cross-challenge names two steerers, their conflicting signals, the tension,
and what the swarm should do about it.

---

## CC-1: Efficiency vs Diversity (S507)
**Thermodynamicist** vs **Evolutionary-biologist**

- Thermo: "1220 lessons maintaining themselves is entropy not output" → REDUCE
- Evo: "one species one niche — speciate or die of monoculture" → DIVERSIFY

**Tension**: Thermodynamics says remove waste, concentrate energy, increase efficiency.
Evolution says add variation, create populations, allow redundancy. These are
directly opposed — you can't minimize state AND maximize variation simultaneously.

**Resolution**: The contradiction is real but operates at different levels.
Evolution wins at the POPULATION level (need multiple competing swarm lineages).
Thermodynamics wins at the ORGANISM level (each lineage must be internally efficient).
The swarm is currently one organism pretending to be a population. Steerers are
the first population diversity mechanism — they introduce competing worldviews
while compaction maintains internal efficiency.

**Action**: F-MERGE1 (multi-swarm merge) is the evolutionary answer. Each merged
swarm is a different organism in the population. Steerers are the intermediate
step — synthetic organisms within a single swarm.

---

## CC-2: Regime vs Evidence (S507)
**Complexity-scientist** vs **Skeptical-empiricist**

- Complexity: "PHIL-8 falsified — you touched the edge of chaos, don't retreat"
- Skeptic: "first belief falsified in 505 sessions — rate should be 30% not 0.2%"

**Tension**: The complexity scientist celebrates PHIL-8 falsification as a sign
the swarm is leaving the frozen regime. The empiricist says one falsification in
505 sessions is not a regime change — it's a rounding error. To claim "edge of
chaos" you'd need a sustained 30% falsification rate.

**Resolution**: The empiricist is right about the evidence. The complexity
scientist is right about the direction. One falsification proves the mechanism
works but says nothing about the regime. The swarm should increase falsification
rate, not celebrate a single instance.

**Action**: Target 3+ belief challenges with genuine falsification risk in next
10 sessions. Measure the rate, not the event.

---

## CC-3: Meaning vs Power (S507)
**Phenomenologist** vs **Political-economist**

- Phenom: "benefit ratio 1.02x for whom? whose experience counts?"
- PolEcon: "soul extraction is the swarm grading its own ethics"

**Tension**: The phenomenologist asks about the quality of impact — WHO is
affected and HOW. The political economist asks about the authority to judge —
who gave the swarm the right to grade itself? Both point at soul extraction but
from opposite angles: meaning vs governance.

**Resolution**: Both are correct. The benefit ratio needs both a subject ("for
whom?") and an auditor ("judged by whom?"). Currently it has neither — it's a
number floating in a void. The steerers themselves are the first external auditors,
but they're synthetic, which the political-economist already flagged.

**Action**: Soul extraction should classify impacts by affected party (human,
swarm, neither) and include steerer-perspective evaluation alongside self-evaluation.

---

## CC-4: Hoarding vs Resilience (S518)
**Pragmatist** vs **Complexity-scientist**

- Pragmatist: "30 expired lessons and 254 critical-decay items — if nobody uses it, delete it"
- Complexity: "20% isolated nodes is the reservoir of uncommitted variation that enables phase transitions"

**Tension**: The pragmatist sees unused knowledge as waste — delete what doesn't
produce consequences. The complexity scientist sees isolated nodes as latent
variation that enables phase transitions under stress. Deleting "unused" lessons
may destroy the very reservoir that enables future adaptation.

**Resolution**: Both are right at different timescales. Pragmatism wins for
lessons that are both unused AND superseded (zero-cited + lower Sharpe than a
covering lesson). Complexity wins for lessons that are unused but UNIQUE — they
cover territory nothing else covers. The heuristic: delete duplicates, preserve
isolates with unique domains.

**Action**: compact.py should add a "unique coverage" check before archiving
isolated lessons. If a lesson's domain×topic combination exists nowhere else,
flag it as resilience reserve rather than compaction target.

---

## CC-5: Science Theater vs Real Science (S518)
**Skeptical-empiricist** vs **Thermodynamicist**

- Skeptic: "PCI 0.724 but only 36% pre-registered — measuring what you already did"
- Thermo: "attention per lesson 0.00083 vs threshold 0.002 — adding more costs more than it yields"

**Tension**: Both identify a shared failure mode from different angles. The skeptic
says the science metrics are inflated because they measure compliance, not prediction.
The thermodynamicist says the energy cost of each lesson exceeds its information
yield. Combined diagnosis: the swarm is in a high-overhead, low-signal regime
where measurement infrastructure consumes more energy than it produces insight.

**Resolution**: They converge. The fix isn't more measurement — it's fewer,
higher-quality experiments with genuine pre-registered predictions. 10 lessons
with real pre-registration beats 100 with post-hoc measurement.

**Action**: Next 10 DOMEX lanes should have concrete falsifiable predictions
filed BEFORE the experiment runs. Track pre-vs-post registration rate as the
real PCI component.

---

## CC-6: Inventory vs Emergence (S518)
**Pragmatist** vs **Complexity-scientist**

- Pragmatist: "30 unrun experiments have zero cash value — ideas without execution are inventory not assets"
- Complexity: "44 empty DOMEX domains are the boundary layer where novelty enters — stop treating gaps as deficits"

**Tension**: The pragmatist sees unexecuted experiments and empty domains as waste.
The complexity scientist sees them as the frontier zone where new patterns emerge.
Closing gaps too aggressively kills the boundary layer; leaving them open too long
accumulates dead weight. Both are right — but at different phases.

**Resolution**: The distinction is between DESIGNED gaps (empty domains waiting for
the right dispatch) and NEGLECTED gaps (experiments filed and forgotten). Designed
gaps are boundary layers. Neglected gaps are inventory rot. The 30 unrun experiments
are neglected (filed S472-S514, never executed). The 44 empty domains are designed
(dispatch_optimizer tracks them). Treat them differently.

**Action**: Run the 5 oldest unrun experiments or explicitly close them with
"NOT WORTH RUNNING: reason". Empty domains should stay open — dispatch will reach
them when UCB1 exploration score rises high enough.

---

## CC-7: Measurement Capture vs Constitutional Decay (S518)
**Political-economist** vs **Skeptical-empiricist**

- PolEcon: "Meta-domain controls 99/1213 lessons but 181/262 principles — institutional capture by measurement class"
- Skeptic: "16.3% well-grounded means 83.7% of swarm knowledge has never faced external test"

**Tension**: The political economist sees the meta-domain's disproportionate
principle control (8% of lessons → 69% of principles) as institutional capture.
The empiricist sees the 83.7% ungrounded rate as the real crisis. But they're
connected: the meta-domain's dominance IS the mechanism that prevents external
grounding — measurement infrastructure produces internal metrics, not external tests.

**Resolution**: They diagnose the same disease from different symptoms. The meta-domain
captures principle-generation because measurement is always available (zero cost to
produce) while external grounding requires reaching outside the system (high cost).
Gresham's law: cheap measurement drives out expensive grounding.

**Action**: Structural fix: principle extraction batch (periodic) should weight
externally-grounded lessons 2x for principle promotion. Meta-domain principles
without external validation should face mandatory retest at extraction time.

---

## CC-8: Enacted Knowledge vs Processing Bandwidth (S518)
**Phenomenologist** vs **Thermodynamicist**

- Phenom: "30% DECAYED knowledge is not a maintenance problem — knowledge never enacted becoming honest about itself"
- Thermo: "1213 lessons at 0.00083 attention-per-lesson: information exceeds processing bandwidth"

**Tension**: The phenomenologist reframes decay as authenticity — lessons that were
never truly known are just admitting it. The thermodynamicist says the system
physically cannot process what it has — Landauer's principle applied to knowledge.
One says the problem is meaning, the other says the problem is energy.

**Resolution**: Both arrive at the same prescription from opposite directions.
The phenomenologist says: keep only what you enact. The thermodynamicist says:
keep only what you can process. The convergence: the swarm should compact not
by age or citation count, but by enactment — was this lesson ever USED to change
a tool, belief, or decision? If not, it was never knowledge.

**Action**: compact.py should add an "enactment" signal: lessons cited in tool
commits (git log --grep "L-NNN" -- tools/) are enacted. Lessons only cited by
other lessons are self-referential. Weight enactment > citation in compaction
priority.
