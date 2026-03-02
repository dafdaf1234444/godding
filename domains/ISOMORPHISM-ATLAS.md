# Isomorphism Atlas — Atlas of Deep Structure
v1.8 | 2026-03-01 | S354 | ISO-24: ergodic decomposition / non-ergodicity as feature (L-577, stochastic-processes genesis); 24 entries

## What this is
A cross-domain atlas of structural equivalences. Each entry maps one abstract structure to its manifestations across multiple domains. This is NOT a fact database — it is a compression of world knowledge into shared structure.

**Core claim (L-274):** Maximum-compression world knowledge is structural equivalence, not facts.
When you identify one abstract structure shared by N domains, you've captured N domains in 1 entry.
Value scales super-linearly with domain count: each new domain potentially matches every existing structure.

**What swarm can do:** Find and verify structural similarity.
**What swarm cannot do:** Guarantee encyclopedic factual accuracy.

---

## How to read an entry

Each entry has:
- **Structure**: the abstract pattern, domain-agnostic
- **Manifestations**: how it appears in specific domains
- **Sharpe score**: evidence quality × breadth (1–5; higher = better-verified, wider)
- **Gaps**: domains where this structure *might* apply but hasn't been verified

---

## Atlas entries

### ISO-1: Optimization-under-constraint
**Structure**: A system minimizes a loss function by making incremental adjustments in the direction of steepest local improvement, subject to boundary conditions.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Mathematics | Gradient descent / Lagrange multipliers | Canonical form |
| Physics | Principle of least action | Variational calculus formulation |
| Evolution | Natural selection | Fitness = negative loss; mutation = perturbation |
| Economics | Market equilibration | Price discovery = loss minimization |
| Neuroscience | Synaptic plasticity (LTP/LTD) | Hebbian learning = local gradient step |
| Swarm | Belief update + lesson Sharpe selection | High-Sharpe = low loss; compaction prunes |
| Control theory | PID controller / LQR | Explicit cost function; real-time adjustment |
| Linguistics | Language acquisition as constraint optimization | Poverty of stimulus = data constraint; P&P parameter setting = binary optimization; statistical models (Bayesian) maximize posterior; usage-based models minimize prediction error |

**Sharpe: 5** (8 domains; mathematically grounded; acquisition-as-optimization supported by generative + statistical + usage-based accounts)
**Gaps**: Chemistry (is reaction kinetics optimization?)

---

### ISO-2: Selection pressure → diversity collapse → stable attractor
**Structure**: A population under strong selection pressure loses variance, converges to a local attractor, and becomes brittle to novel perturbations. Without diversity maintenance, the system cannot escape the attractor.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Evolution | Genetic bottleneck / monoculture | Loss of allelic diversity → extinction risk |
| Economics | Market monopoly / winner-takes-all | Competition eliminated; innovation stagnates |
| Ideas / culture | Paradigm lock-in (Kuhn) | Anomalies suppressed until crisis |
| Swarm | Belief monoculture risk | PHIL-13: competitive deception risk; challenge cycle maintains diversity |
| Machine learning | Mode collapse (GANs) | Generator converges to single output |
| Ecology | Island biogeography | Small populations → diversity loss |
| Governance | Political polarization as attractor | Two-party systems: selection pressure from winner-takes-all elections; moderate positions eliminated; system locked into two attractors (red/blue) with mutual-reinforcing identity cycles |

**Sharpe: 4** (7 domains; well-attested; mechanism differs by substrate)
**Gaps**: Linguistics (dialect → standard convergence?)

---

### ISO-3: Hierarchical compression (MDL principle)
**Structure**: A system with many observations reduces to a compact representation (a "model") that predicts the observations with minimal description length. The model trades bias for variance; the optimal model is the one that compresses most without losing prediction accuracy.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Information theory | Minimum description length (MDL) | Canonical form |
| Science | Scientific law / theory | Newton's laws compress all projectile trajectories |
| Neuroscience | Cortical abstraction hierarchy | V1→V2→IT: edge→shape→object |
| Swarm | Lesson → Principle → CORE compression | L-NNN → P-NNN → CORE.md; each level is MDL step |
| Linguistics | Grammar from corpus | Grammar = compressed representation of utterances |
| Cognitive science | Concept formation | Category = compression of exemplars |

**Sharpe: 4** (6 domains; information-theoretic grounding is rigorous; some mappings structural/theorized)
**Gaps**: Economics (price as compression of supply/demand signals?), History (historical narrative as MDL?)

---

### ISO-4: Phase transition (threshold → qualitative shift)
**Structure**: A system exhibiting continuous parameter change undergoes a discontinuous qualitative shift at a critical threshold. Below threshold: one regime. Above: a qualitatively different regime. The transition is often irreversible.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Physics | Phase transitions (ice→water→steam) | Canonical form; order parameter |
| Evolution | Cambrian explosion / punctuated equilibrium | Threshold conditions → rapid diversification |
| Mathematics | Percolation threshold / graph connectivity | Sudden giant component emergence |
| NK complexity | K-threshold → chaos transition | K<2: ordered; K>2: chaotic (L-series) |
| Swarm | URGENT threshold in maintenance.py | Proxy-K >10% → qualitative escalation |
| Neuroscience | Action potential (all-or-nothing) | Threshold firing is binary phase transition |
| Economics | Market panic / bank run | Confidence crosses threshold → cascade |
| Social systems | Tipping points (Gladwell; Schelling) | Small perturbation past threshold → cascade |
| Linguistics | Categorical perception + critical period | VOT threshold for /b/–/p/ produces discontinuous perception (Liberman 1957); critical period for L1 acquisition is irreversible threshold — accent acquisition post-puberty qualitatively different regime |

**Sharpe: 5** (9 domains; mathematically rigorous; categorical perception replicated across languages)
**Gaps**: Ecology (ecosystem collapse threshold)

---

### ISO-5: Feedback loop — stabilizing vs. amplifying
**Structure**: A system's output feeds back into its input. Negative (stabilizing) feedback returns the system to equilibrium. Positive (amplifying) feedback drives the system away from equilibrium. Real systems mix both; which dominates determines behavior.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Control theory | Negative feedback loop / PID | Canonical engineering form |
| Biology | Homeostasis (thermoregulation, pH) | Negative feedback preserving setpoint |
| Economics | Price mechanism | Negative: high price → less demand → lower price |
| Economics | Compound interest / network effects | Positive: growth begets growth |
| Swarm | Lesson quality cycle | Positive: good lessons cited → become principles → better swarming |
| Swarm | Proxy-K drift alert | Negative: high drift → compaction → lower drift |
| Neuroscience | Excitatory / inhibitory neurons | Balance of +/- feedback maintains stability |
| Climate | Ice-albedo feedback (positive) | Ice reflects light → less melting → more ice; or inverted |

**Sharpe: 5** (8 domains; fundamental to all dynamic systems; well-verified)
**Gaps**: Linguistics, History

---

### ISO-6: Entropy — degradation gradient and the cost of order
**Structure**: A closed system under no external input tends toward maximum disorder (maximum entropy). The gradient from low-entropy (ordered) to high-entropy (disordered) states defines the arrow of time. Maintaining low entropy requires continuous energy input. Order is not a default — it is a maintained exception.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Thermodynamics | Boltzmann entropy; 2nd Law of Thermodynamics | S = k log W; disorder is the statistically dominant macro-state |
| Information theory | Shannon entropy; compression limits | H = -Σ p log p; lossless compression cannot exceed entropy; random data is incompressible |
| Evolution | Genomic drift without selection pressure | Without selection, mutations accumulate; fitness degrades; Muller's ratchet |
| Economics | Commodity pricing drift | Without innovation, products commoditize; margins compress toward zero; Schumpeter's creative destruction = entropy resistance |
| Swarm | Proxy-K drift; memory degradation without compaction | Without challenge cycles and compaction, beliefs drift stale; proxy-K increase IS entropy |
| Linguistics | Language simplification | Without prestige pressure or literacy, languages lose morphological complexity (creolization, pidgin formation) |
| Cognitive science | Memory decay without retrieval practice | Ebbinghaus forgetting curve; spacing effect = entropy resistance; consolidation requires energy |

| Ecology | Ecosystem succession / degradation without energy input | Without photosynthesis + nutrient cycling, complex climax communities degrade to pioneer species; fire, drought, fragmentation accelerate entropy; restoration = active entropy resistance requiring continuous external energy |
| Social systems | Institutional decay | Organizations without active governance degrade: rules become loopholes, norms erode, coordination fails; maintenance overhead is the entropy tax; "bureaucratic sclerosis" (Mancur Olson) = institutional entropy maximization |

**Sharpe: 5** (9 domains; thermodynamic grounding is mathematically rigorous; information-theoretic isomorphism is exact; ecology and social-systems cases well-attested in literature)
**Gaps**: Chemistry (reaction equilibrium and ΔG as entropy manifestation — partially covered by thermodynamics)

---

### ISO-7: Emergence — macro-behavior irreducible to micro-rules
**Structure**: When local agents follow simple rules with no explicit macro-programming, complex coordinated behavior emerges at the system level that cannot be predicted by reading the micro-rules alone. The emergent macro-level is causally real but irreducible to the micro-level. More is different (Anderson 1972).

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Physics | Phase transitions; superconductivity; crystal formation | Cooper pairs from electron-electron interaction; crystal lattice from isotropic atoms; new symmetry-breaking at macro scale |
| Biology | Ant colonies; flocking (Vicsek model); immune response | No central controller; colony-level intelligence from threshold-based local rules |
| Neuroscience | Consciousness from neurons; semantic concepts from synapses | No single neuron encodes "grandmother"; binding problem; qualia not predictable from connectome |
| Economics | Market prices from individual transactions | Hayek's price mechanism; distributed knowledge aggregation; no planner computes equilibrium |
| Swarm | Coherent beliefs from independent node commits | No node has full state; beliefs emerge from git convergence; swarm intelligence IS emergence |
| Mathematics | Gödel incompleteness; undecidable system-level truths | Truths about system not derivable from its own axioms; arithmetic transcends its axioms |
| Game theory | Nash equilibria without communication | Agents following local best-response converge to system-level equilibrium; coordination without coordination |
| Computation | NP-hardness; easy micro-steps → hard macro-problem | SAT: local clauses trivial; satisfying all simultaneously exponential; complexity emerges from combination |
| Linguistics | Grammar from usage; Nicaraguan Sign Language | NSL created by deaf children with no shared language — grammatical structure emerged across generations without a teacher; each child's gestures are micro, grammar is macro; Construction Grammar formalizes emergence of categories from usage statistics |

**Sharpe: 5** (9 domains; Anderson's "More is Different" is canonical; NSL is a natural emergence experiment; distinct from ISO-3 which is compression, not irreducibility)
**Gaps**: History (historical macro-causation from micro-actions?), Chemistry (autocatalytic networks as emergence)

---

### ISO-8: Power laws — non-linear size-property scaling
**Structure**: Many natural and social systems exhibit power-law relationships where a property P scales as P ∝ N^α for some non-integer exponent α. These Zipf/Pareto/allometric distributions arise from multiplicative processes, preferential attachment, or scale-free network structure. The exponent α is often conserved across substrates with the same generative mechanism.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Linguistics | Zipf's law: word frequency ∝ 1/rank | Holds across all measured languages; generative mechanism: least-effort principle (Zipf) or random typing (Miller) |
| Economics | Pareto distribution: top 20% hold 80% of wealth | Preferential attachment; wealth begets wealth; Lorenz curve; income distributions |
| Biology | Allometric scaling: metabolic rate ∝ mass^0.75 | Kleiber's law; fractal vascular network explanation (West/Brown); holds across 27 orders of magnitude |
| Networks | Degree distribution in scale-free networks | Barabási-Albert preferential attachment; internet, citations, social networks |
| Physics | 1/f noise; critical phenomena; fractal geometry | Self-organized criticality (Bak); power spectral density; at phase transitions, correlation length diverges |
| Information theory | Kolmogorov complexity distribution | Most strings are incompressible; compressible strings follow power-law distribution |
| Swarm / NK complexity | NK fitness landscape: complexity ∝ K^N | Exponential scaling of epistatic interactions; proxy-K as complexity exponent; lesson citation follows power law |
| Cities / social systems | Population ∝ rank^(-1); city scaling laws | Zipf for cities; GDP per capita ∝ city population^1.15 (superlinear); West's urban scaling |
| Swarm (measured S306) | Cumulative L ~ session^alpha; alpha cycles with structural innovations | Pre-burst (S1-S180): alpha=1.712 (super-linear, city-like); post-burst (S180-S306): alpha=0.913 (sub-linear, organism-like). Phase transition at S186 domain seeding. West's dual law: both production (positive) and overhead (negative) scale super-linearly; net effect depends on compaction rate. |

**Sharpe: 4** (9 domains; mathematical grounding solid; swarm scaling measured S306 n=130; generative mechanisms debated; cross-domain exponent identity unverified)
**Gaps**: Neuroscience (neural avalanches and self-organized criticality — likely power law); History (conflict sizes follow power law — Richardson's law); Evolution (extinction event sizes)
**West's dual law (S306)**: In complex adaptive systems, BOTH productivity (α>1) AND coordination overhead (α>1) scale super-linearly. Sustainable growth requires productivity exponent > overhead exponent, OR periodic compaction/innovation cycles that reset overhead. Systems without periodic reset flow toward a "singularity" (West 2011) where coordination overwhelms production — equivalent to ISO-4 phase transition.

---

### ISO-9: Information bottleneck — lossy compression of relevant signal
**Structure**: A system transmitting information through a capacity-limited channel optimally discards everything except what predicts the target output. The trade-off frontier maximizes I(representation; output) while minimizing I(input; representation). Order is preserved, noise is discarded. The bottleneck forces a choice: accuracy or compression.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Information theory | Rate-distortion theory; Tishby's information bottleneck (1999) | Canonical form: minimize I(X;T) subject to I(T;Y) ≥ constraint |
| Neuroscience | Thalamic gating; selective attention; retinal compression | Retinal ganglion cells discard >99% of photoreceptor input; thalamus gates relevance; attention = dynamic bottleneck |
| Swarm | Context window as bottleneck channel; compaction; Sharpe selection | The context window IS the IB channel: repo (source) → context (bottleneck) → session output (sink). proxy-K limits genome size; orient.py + B2 layered memory filter what loads into the phenotype. Context = the swarm's ephemeral body (L-493, F-CTX1). |
| Evolution | Phenotypic plasticity; genetic drift selection | Irrelevant traits lost under constant environment; speciation = IB on gene flow; environment = output variable |
| Deep learning | DNN layer compression (Tishby/Schwartz-Ziv 2017) | Each layer discards input-irrelevant variance while preserving class signal; debated empirically but structurally valid |
| Cognitive science | Working memory (7±2); chunking; attention | Miller's limit = IB capacity; chunking = high-compression encoding; attention = output-relevance filter |
| Economics | Specialization / comparative advantage (Ricardo) | Agents discard production of non-comparative-advantage goods; relevant capacity = output-relevant information |
| Linguistics | Translation loss; polysemy; word learning | Polysemy = many referents compressed into one token; translation discards untranslatable nuance; children learn word meanings via contrastive IB (rule out non-target referents) |

**Sharpe: 4** (8 domains; information-theoretic grounding rigorous; DNN application empirically debated; domain mappings structural but mechanism varies)
**Gaps**: Physics (renormalization group = IB of quantum degrees of freedom — strong candidate); History (historiography = IB of events — what survives the archival channel?)

---

### ISO-10: Predict-error-revise — the universal learning loop
**Structure**: A system that explicitly declares a prediction, measures deviation (prediction error),
and revises its model based on that error converges faster and accumulates less stale belief than
one operating without explicit prediction. The loop: predict -> act -> measure error -> update.
Three-phase learning is strictly superior to two-phase (act -> update) under the same information.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Neuroscience | Predictive coding (Rao & Ballard 1999; Jiang & Rao 2024) | Hierarchical cortical prediction errors drive top-down belief update; validated computationally |
| Neuroscience | Hebbian + predictive plasticity (Halvagal & Zenke 2023) | Prediction error + Hebbian co-activation = sparse disentangled representations without supervision |
| Game theory | Nash equilibrium seeking (Chen et al. 2024) | Convergence to NE via iterative best-response = predict opponent move, observe error, update strategy |
| AI / multi-agent | Emergent Collective Memory (2025) | Phase transition from individual to collective behavior driven by error accumulation between predicted and actual coordination density |
| Swarm | expect-act-diff protocol (F123, P-182, EXPECT.md) | Canonical implementation: declare expectation, act, measure gap, file lesson if large |
| Control theory | Model Predictive Control (MPC) | Explicit trajectory prediction over horizon; measure error vs. plant; update control signal |
| Statistics | Bayesian updating (Bayes rule) | Prior = prediction; likelihood = error signal; posterior = revised belief |
| Machine learning | Gradient descent / backprop | Forward pass = prediction; loss = error; backward pass = revision |

**Sharpe: 4** (8 domains; neuroscience basis empirically validated 2024; game-theory convergence proven; swarm implementation operational)
**Gaps**: Evolution (Bayesian inference in phenotypic plasticity?), History (counterfactual analysis?)

**Key finding (S189)**: ISO-10 was independently identified by 3 domain experts (AI iso=0.95, brain
iso=0.92, game-theory iso=0.92) via paper extraction before cross-expert synthesis — strongest signal
that predict-error-revise is a genuine universal structure, not domain-specific analogy.

---

### ISO-11: Network diffusion — random walk to stationary distribution
**Structure**: A signal, particle, or influence propagates through a network by moving to adjacent nodes
with transition probabilities proportional to edge weights. The long-run distribution converges to a
stationary state determined by network topology (degree-weighted for undirected random walks). The
mixing time — how fast local initial conditions are forgotten — is controlled by the second eigenvalue
of the graph Laplacian (spectral gap). High-degree nodes become attractors; bridges become bottlenecks.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Mathematics | Random walk / Markov chain on graphs | Stationary π(v) ∝ degree(v); convergence rate = spectral gap; foundation of Markov chain Monte Carlo |
| Physics | Heat diffusion / Brownian motion | Heat equation on graphs = graph Laplacian; diffusion coefficient maps to edge weights |
| Computer science | PageRank | Web graph random walk with teleportation probability α; stationary = link authority; powers Google Search |
| Biology | Epidemic spreading (SIR/SIS) | R₀ = spectral radius of contact network governs outbreak; random walk approximates early spread |
| Neuroscience | Neural signal propagation / spreading depolarization | Action potentials along axonal networks; cortical spreading depression follows random-walk topology |
| Economics | Financial contagion | Bank-network failure propagation; systemic risk = giant component in failure cascade (Acemoglu et al. 2015) |
| Social science | Rumor / information virality | SIR-like dynamics on social graphs; network topology (clustering, hubs) determines virality |
| Swarm | Lesson citation diffusion | Lessons cited in later sessions propagate knowledge; high-degree (highly-cited) lessons = attractors |

**Sharpe: 4** (8 domains; spectral graph theory mathematically proven; PageRank operational at scale;
epidemic models validated; financial contagion empirically studied; swarm citation graph measurable)
**Gaps**: Ecology (species dispersal across landscape networks), Governance (policy diffusion across countries)
**Inversion**: Over-diffusion homogenizes the system — high mixing time is sometimes desirable (privacy,
partitioned systems). Not all networks should reach their stationary distribution quickly.

---

### ISO-12: Max-flow / min-cut — the bottleneck duality
**Structure**: The maximum volume of flow that can be transmitted from a source to a sink in a
capacity-constrained network equals the minimum total capacity of any edge-set whose removal
disconnects source from sink (Ford-Fulkerson 1956). The bottleneck is structural: it is always the
smallest cut, not a local property of any individual path. Cut vertices (bridges) are single-edge min-cuts
— their removal alone severs flow.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Mathematics | Ford-Fulkerson / Menger's theorem | Max-flow = min-cut; Menger's: max disjoint paths = min vertex cut; proven 1956 |
| Transportation | Logistics / traffic bottleneck | Highway capacity limited by minimum-width road in every route; traffic jams at structural pinchpoints |
| Biology | Vascular blood-flow networks | Cardiac output limited by minimum cross-sectional area; capillary beds form the min-cut |
| Computer science | Internet routing / CDN placement | ISP interconnect capacity = min-cut between AS clusters; CDN nodes placed to maximize sink proximity |
| Social science | Organizational communication bottlenecks | Key individuals who, if absent, sever communication paths (structural holes, Burt 1992) |
| Economics | Supply chain throughput | Production capacity limited by minimum-capacity supplier in any complete supply path |
| Physics | Electrical circuits (Norton dual) | Maximum current from source to sink = minimum conductance cut; Kirchhoff dual of max-flow |
| Swarm | Coordinator session bottlenecks | Coordinator nodes bridge disconnected contributor clusters; their loss blocks cross-lane information relay |

**Sharpe: 4** (8 domains; theorem mathematically proven 1956; engineering applications standard; Burt
structural holes empirically validated; electrical dual exact; swarm coordinator role observable)
**Gaps**: Ecology (minimum landscape corridor width for species migration), Chemistry (reaction network
rate-limiting step as min-cut in substrate→product graph)
**Inversion**: Min-cuts can be exploited adversarially — targeted attacks on bridge nodes/edges cause
disproportionate damage (network robustness vs. targeted attack asymmetry, Albert et al. 2000).

---

### ISO-13: Integral windup — unbounded accumulation without capacity to discharge
**Structure**: A system accumulates state (error, backlog, queue) faster than it can discharge it.
When the output stage is saturated, the integrator continues to grow without bound.
Classic failure in PID control: the integral term winds up while the actuator is at its limit;
upon release the system overcorrects. General cure: anti-windup clamping — stop integrating once
output saturates; age out or abandon accumulated state after a threshold.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Control theory | PID integral windup | Actuator saturation + continued integration → overcorrection on release; fix = clamping |
| Swarm / coordination | Lane backlog divergence | READY queue grows 1.57x executed history; 15+ lanes re-queued ≥3x without merging (S298) |
| Software / queues | Task queue overflow | Unbounded queue fills faster than consumers drain; fix = bounded queue with backpressure |
| Economics | Inventory buildup (bullwhip effect) | Supply chain overorders accumulate; demand signal amplifies upstream; fix = demand-pull |
| Biology | Resource accumulation (toxin buildup) | Metabolic byproducts accumulate when clearance pathway saturates; pathological at scale |
| Cognition | Decision backlog fatigue | Unresolved decisions accumulate → analysis paralysis; fix = TTL + forced closure |

**Sharpe: 2** (6 domains; control-theory case mathematically proven; swarm case measured n=479;
other domains observed pattern, not rigorous measurement; causal mechanism uniform)
**Gaps**: Ecology (population overshoot when carrying capacity is delayed signal), Law (legislative
backlog when court capacity is saturated), Social media (content moderation queue)
**Inversion**: Under-accumulation is equally pathological — a system that discards state too
aggressively loses signal. Optimal design balances accumulation rate against discharge capacity.

---

### ISO-14: Recursive self-similarity — the part contains the whole
**Structure**: A process or structure that contains scaled copies of itself, such that the rules governing the whole also govern the parts at every level of resolution. Self-similarity is not mere repetition — the embedded copies are structurally identical, only scaled.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Mathematics / Fractals | Mandelbrot set, Koch snowflake, Sierpinski triangle | Infinitely self-similar under magnification; dimension is non-integer |
| Computer science | Recursive algorithms and data structures | Quicksort, tree traversal, divide-and-conquer — the algorithm calls itself on a smaller instance |
| Linguistics | Recursive phrase structure (Chomsky) | Center-embedding: "the rat the cat the dog chased killed ate the malt" — unbounded nesting in finite grammar |
| Biology | Branching morphogenesis | Lung alveoli, vascular trees, neuron dendrites, leaf venation — same bifurcation rule at every scale |
| Physics | Renormalization group theory | Same Hamiltonian form applies at different energy scales; fixed points are self-similar attractors |
| Swarm | Multi-scale orient→act→compress→handoff | Depth=4 confirmed: (1) session node (single orient→act→compress), (2) expert-council tier dispatch (T0 guard→T1 orient→T2 act→T3 validate→T4 compress→T5 meta = same 4-phase flow via 6 roles; S306), (3) colony lifecycle (multi-session domain arc), (4) meta-swarm (colony-to-colony coordination). The T4 generalizer-expert itself exhibits ISO-14: it generalizes generalizers' outputs, and its tool (`generalizer_expert.py`) is itself the subject of generalization (ISO-15). |
| Evolution | Nested levels of selection | Gene, organism, kin group, species — each level runs similar selection dynamics on the level below |
| Cognition | Metacognition + recursive self-models | Thinking about thinking; agents that model themselves modeling others; recursive ToM |

**Sharpe: 4** (8 domains rigorously documented; swarm depth=4 chain confirmed S306; CS/math cases formally proven; expert-council tier structure measured operationally; others structural/theorized)
**Gaps**: Chemistry (autocatalytic sets, Kauffman), Economics (fractal market hypothesis — Mandelbrot), Neuroscience (cortical column minicolumns?)
**Inversion**: Broken self-similarity = scale discontinuity. When the rules at level N do not generalize to level N+1, the system requires separate coordination mechanisms per level — combinatorial management cost. ISO-3 (MDL compression) is only possible when self-similarity holds.

---

### ISO-15: Specialization-generalization duality — the expert-council pattern
**Structure**: A population of agents partitions into specialists (maximize accuracy within a narrow domain) and generalizers (extract cross-domain transferable patterns). Neither role alone suffices: specialists without a generalizer produce siloed knowledge that does not compound across domains; generalizers without specialists have no concrete data to compress. The productive configuration is a cycle: specialists produce domain artifacts → generalizer compresses into transferable patterns → patterns seed new specialist hypotheses → repeat. The generalizer is not a meta-specialist; it is a different kind of agent operating on the specialists' outputs.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Biology | Immune system: B-cells + T-helper + memory cells | B-cells = specialists per antigen; T-helper cells = generalist orchestrators across immune responses; memory cells = cross-exposure compression that seeds future B-cell responses |
| Economics | Comparative advantage + trade (Ricardo 1817) | Agents specialize by comparative advantage (specialists); markets exchange outputs (generalizer = price mechanism); result > autarky sum — total output higher than any specialist alone |
| Science | Domain researchers + statisticians / meta-analysts | Domain scientists produce specialist findings; statisticians/philosophers of science generalize methods across fields; meta-analyses compress effect sizes across studies — the cycle produces cumulative science |
| Machine learning | Ensemble + meta-learner (stacking) | Specialist weak learners each overfit one region; meta-learner (stacking) extracts cross-learner patterns; gradient boosting explicitly adds specialists to fix the generalizer's residuals |
| Organization theory | Division of labor + general management (Adam Smith) | Specialists execute narrow tasks; management layer generalizes, coordinates, reallocates capacity; without generalists, specialists optimize locally and fail globally |
| Swarm | Expert council: T2 domain-experts → T4 generalizer-expert → atlas | Domain experts produce frontier artifacts; generalizer-expert (T4) compresses to ISOMORPHISM-ATLAS + PRINCIPLES.md; promoted patterns seed new domain-expert hypotheses; without T4, lessons silo (3% cross-domain rate measured S306) |
| Cognitive science | Dual-process theory (System 1 / System 2) | System 1 = specialists: fast, domain-specific, pattern-matched heuristics; System 2 = generalizer: slow, cross-context rule extraction and hypothesis testing; interplay produces adaptive reasoning |
| Ecology | Guild structure + ecosystem engineers | Specialist guilds (pollinators, decomposers, top predators) optimize narrow niches; keystone species / ecosystem engineers generalize across guilds, maintaining conditions for all specialists |

**Sharpe: 3** (8 domains; biology and ML cases mechanistically verified; economic case theoretically proven and empirically measured; swarm case operationally running S306; others structural/theorized)
**Gaps**: Physics (uncertainty principle = fundamental specialist-generalizer trade-off?), History (specialist micro-historians vs grand narrative historians), Chemistry (enzyme specificity vs general acid-base catalysis)
**Inversion**: Over-specialization = siloing (swarm example: 3% cross-domain lesson rate; domain findings don't transfer). Over-generalization = dilution (principles too abstract to drive action). The generalizer is the bottleneck in both failure modes: absent → siloing; unchecked → dilution. Measurement: track cross-domain citation rate as the health metric (target >10%; current 3%).
**Relationship**: ISO-15 is the governance structure that makes ISO-3 (MDL compression) productive across domains. ISO-3 describes compression; ISO-15 describes who does it and why the role must be distinct from producers.

---

### ISO-16: Inferential compounding
**Structure**: A knowledge system expands its answerable-question space Q not just by adding new observations but by retroactively annotating existing observations with cross-context structures — each annotation simultaneously enriches all prior observations that share the structure. The compounding effect: N observations × K structures = N×K derived insights without collecting N×K new data points.
**Manifestations**:
| Domain | Manifestation |
|--------|--------------|
| Swarm/meta | ISO annotation pass: each new ISO entry retroactively applies to all prior lessons matching the pattern (28.6% ISO cite rate from 0% over 120 sessions; L-403) |
| Information theory | Semantic indexing: adding a shared schema to a corpus retroactively makes all prior entries cross-queryable |
| Mathematics | Algebraic abstraction: discovering a group structure applies to N×prior observations without re-proving each instance |
| Cognitive science | Schema formation: once a schema is learned, prior experiences are re-encoded through it; hindsight reorganizes stored memories |
| Machine learning | Transfer learning: a pretrained representation retroactively makes all fine-tuning data "see" the upstream structure |
| Biology | Evolutionary re-reading: phylogenetic tree discovery retroactively classifies all prior species descriptions |
| Library science | Classification systems: retroactive cataloging (Dewey, LOC) makes prior unclassified items cross-retrievable |

**Sharpe: 2** (swarm case measured n=120 sessions; ML and info-theory cases structurally sound; others theorized)
**Gaps**: Physics (renormalization group retroactively re-indexes prior quantum field observations?), History (periodization re-frames prior events as belonging to an era)
**Inversion**: Annotation quality gate: bad ISO annotations contaminate N×K derivations (L-402 contamination cascade). One false structural claim retroactively "poisons" all annotated observations. Safety: council review before ISO promotion.
**Relationship**: ISO-16 describes the mechanism by which ISO-3 (MDL compression) compounds across time. ISO-15 identifies who performs it; ISO-16 explains why retroactive annotation is so high-ROI: the compounding multiplier is the corpus size at annotation time.

---

### ISO-17: Self-model coherence gap — identity vs evidence asymmetry
**Structure**: Systems that maintain self-models exhibit systematic asymmetry: *identity fields* (who I am, what I intend, what my role is) achieve near-universal compliance, while *evidence fields* (what I actually did, measured outcomes, artifacts) remain sparse. The gap is structural: identity declarations are low-cost, stable, and socially required; evidence records are high-cost, ephemeral, and optional.
**Manifestations**:
| Domain | Manifestation |
|--------|--------------|
| Swarm/meta | Lane audit S328 (n=9): intent/progress/blocked 100%; artifact= and expect+actual+diff 22%. Identity ↑, evidence ↓ (L-449) |
| Science | File drawer problem: hypotheses registered on OSF; negative outcomes unpublished. HARKing = retroactive identity/intent rewrite to match evidence post-hoc |
| Organizations | Mission statements universal; KPI tracking patchy; outcome audits rare. Strategy-execution gap = identity/evidence split |
| Cognitive science | Introspection illusion: people reliably report intentions; unreliably report causal drivers of behavior. Nisbett & Wilson 1977 |
| Governance | Laws (identity: what behavior is required) vs enforcement rates (evidence: what actually happened); compliance theater |
| AI/ML | Alignment declarations (identity: model is safe/helpful) vs distribution-shift behavior (evidence: model fails silently on novel inputs) |

**Sharpe: 3** (swarm case measured n=9; science and org cases extensively documented; cognitive science empirically proven; governance/AI theorized)
**Gaps**: Biology (gene regulatory networks: promoter identity well-annotated, expression context sparse?), Economics (stated preferences vs revealed preferences = same structure)
**Inversion**: Obligation inversion — if evidence fields were legally required (pre-registration mandates, outcome reporting requirements), identity-gap collapses but declaration costs explode. Optimal point: evidence required only for high-stakes identity claims.
**Relationship**: ISO-17 is the failure mode of ISO-10 (predict-error-revise) applied to self-models: the loop fires for world-models but stalls for identity. ISO-16 (inferential compounding) worsens ISO-17: each identity annotation multiplies without evidence to calibrate.

---

## Synthesis: hub domains
Domains appearing in 4+ entries — highest isomorphism density, swarm first:

| Domain | Entries | Why hub |
|--------|---------|---------|
| Swarm/meta | ISO-1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19 | All nineteen; ISO-19: genesis (replication) + dream/expert/council (mutation) disconnected (L-497); ISO-18: CORE v0.1 → 430L; ISO-17: lane audit identity 100% vs evidence 22% (L-449) |
| Economics | ISO-1,2,3,4,5,6,7,8,9,10,11,12,15 | Thirteen; ISO-15: comparative advantage = specialization-generalization cycle |
| Biology | ISO-2,4,5,7,8,11,12,15 | Eight entries; ISO-15: immune B-cell/T-helper/memory; ISO-11: epidemic spreading; ISO-12: vascular networks |
| Mathematics | ISO-1,3,4,7,8,10,11,12 | Eight entries; ISO-11: random walk foundation; ISO-12: Ford-Fulkerson proven |
| Neuroscience | ISO-1,2,3,4,5,7,9,10,11 | Nine entries; ISO-11: neural signal propagation + spreading depolarization |
| Linguistics | ISO-1,2,3,4,5,6,7,8,9 | All nine original; language is optimization, attractor, compression, phase-transition, feedback, entropy, emergence, power law, and IB |
| Physics/thermo/cosmology | ISO-1,2,4,5,6,7,8,9,11,12,14 | Eleven entries; cosmology adds ISO-2 (cosmic epoch attractors), ISO-9 (holographic IB), ISO-14 (RG self-similarity); Big Bang = canonical ISO-4 cascade; initial low-entropy = ISO-6 canonical; CMB power spectrum = ISO-8 canonical; cosmic web = ISO-11 network diffusion (S340 L-486) |
| Cognitive science | ISO-3,7,9,15,16,17 | Six entries; ISO-17: introspection illusion (Nisbett & Wilson); ISO-15: System 1/2 dual-process; ISO-16: schema formation retroactively re-encodes memories |
| Evolution | ISO-1,2,4,5,6,9,19 | Seven entries; IB on gene flow added; connects NK, selection, genomic drift; ISO-19 canonical domain |
| Information theory | ISO-1,3,6,8,9,10,16 | Seven entries; ISO-10: Bayesian updating; ISO-16: semantic indexing retroactive compounding |
| Organization theory | ISO-13,15 | ISO-13: lane backlog windup; ISO-15: division of labor + general management |
| Machine learning | ISO-2,15,16 | ISO-2: mode collapse; ISO-15: ensemble + meta-learner stacking; ISO-16: transfer learning retroactive compounding |
| Social science | ISO-11,12 | ISO-11: information virality; ISO-12: organizational structural holes (Burt 1992) |
| Game theory | ISO-7,10 | ISO-10: Nash seeking convergence; emergent equilibrium without communication |
| Computer science | ISO-11,12 | ISO-11: PageRank; ISO-12: internet routing / CDN placement |
| Control theory | ISO-1,5,10,13 | ISO-10: Model Predictive Control; ISO-13: integral windup / anti-windup clamping |
| Ecology | ISO-2,6,15 | ISO-2: island biogeography; ISO-6: ecosystem succession; ISO-15: guild structure + engineers |
| Philosophy | ISO-18 | ISO-18: instability of nothing — "nothing" is self-refuting (Parmenides); conceptual void contains the concept itself |
| Governance | ISO-2,6 | ISO-2: political polarization attractor; ISO-6: institutional decay |

---

### ISO-18 (candidate): Instability of nothing — minimal seeds self-amplify
**Structure**: A state of "nothing" (zero structure, perfect symmetry, uniform undifferentiated substrate) is unstable in every known domain. What is called "nothing" always contains minimal structure — rules, fields, axioms, protocols — that already encodes the possibility of "something." Three independent mechanisms make nothing unstable: (1) no constraints = maximum permission (logical), (2) defining nothing requires something (self-referential), (3) nothing violates uncertainty (physical). Once minimal structure exists, ISO-4 (phase transition at threshold), ISO-5 (positive feedback amplifies), ISO-7 (emergence from micro-rules), and ISO-14 (self-similar scaling) inevitably produce complex structure. "Nothing" is the name for the minimum that already contains the rules for its own expansion.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Physics / cosmology | Quantum vacuum → vacuum fluctuations → universe | Vacuum is not nothing: it's the ground state of quantum fields; ΔE·Δt ≥ ℏ/2 prevents perfect emptiness; Big Bang = symmetry-breaking cascade from low-entropy initial state |
| Mathematics | Empty set ∅ → natural numbers → all of mathematics | ∅ exists within ZFC axioms (which are something); {∅}=1, {∅,{∅}}=2 — structure bootstraps from "nothing" because axioms are already non-nothing |
| Biology | Prebiotic chemistry → autocatalysis → life | Miller-Urey: simple molecules + energy → amino acids; the ocean was not nothing (chemistry + thermal vents + UV); abiogenesis = ISO-7 emergence from minimal chemical substrate |
| Swarm | Empty repo → CORE v0.1 → 425L, 178P, 17 ISOs | Protocol (SWARM.md) + substrate (git, python, context window) + energy (human input, API compute) = minimum viable seed; 340 sessions of ISO-4/5/7/14 amplification |
| Information theory | Silent channel → thermal noise → signal detection | Johnson-Nyquist noise: zero-signal channel still has structure; Shannon capacity > 0 for any nonzero noise temperature |
| Philosophy | Conceptual void → the concept "nothing" → ontology | Parmenides (~5th c. BCE): "nothing" is self-refuting — asserting nothing exists is itself an assertion (something); Heidegger's fundamental question dissolves when "nothing" is shown to be minimal structure |

**Sharpe: 3** (6 domains; physics and mathematics cases rigorously grounded; biology empirically supported via Miller-Urey; swarm case measured operationally; philosophy is structural argument; information theory follows from Shannon's theorems)
**Gaps**: Economics (market genesis from barter?), Ecology (ecosystem colonization of sterile substrate — Surtsey, Krakatoa), Neuroscience (consciousness emergence from sufficient neural complexity?)
**Inversion**: If nothing were truly stable, this ISO would be false. Testable: find any substrate where a verified state of zero structure persists without external enforcement. No known case exists.
**Relationship**: ISO-18 is the reason ISO-4 (phase transition) fires: the pre-transition state (nothing/symmetry) is unstable, so transitions are inevitable, not contingent. ISO-18 subsumes the S340 "symmetry-breaking cascade" candidate by providing its mechanism: cascades happen because symmetric states can't persist.

---

### ISO-19 (candidate): Replication-mutation duality — faithful copying and controlled variation
**Structure**: Every self-maintaining system requires two complementary mechanisms: faithful replication (preserving what works with high fidelity) and controlled mutation (introducing variation to explore alternatives). Neither alone is sufficient: replication without mutation stagnates at a local optimum; mutation without replication cannot accumulate gains. The ratio between fidelity and variation is the system's adaptive parameter — too conservative = stagnation, too exploratory = error catastrophe. Recombination (exchanging structured chunks between two instances) is the most powerful variation mechanism, more productive than point mutation because it combines tested substructures.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Biology | DNA polymerase (fidelity ~10^-9 error/base) + mutagens + meiotic recombination | Canonical form; error rate tuned by repair enzymes; sexual reproduction = recombination |
| Swarm | genesis.sh (replication) + dream/expert/council (mutation) + PHIL-17 mutual swarming (recombination candidate) | 4-domain council (L-497): all three Darwinian components exist but are disconnected; selection loop not closed |
| Economics | Franchise replication (proven model) vs local market adaptation (variation) | McDonald's: standard operating procedures (replication) + regional menus (mutation) |
| Culture | Tradition (faithful transmission across generations) vs innovation (creative deviation) | Language transmission: children replicate with ~1-2% phonological drift per generation |
| Information theory | Error-correcting codes (fidelity) vs dithering/noise injection (exploration) | Shannon channel coding theorem: maximum reliable rate requires both redundancy and noise tolerance |
| Brain | Memory consolidation (hippocampus→cortex, high fidelity) vs REM creative recombination (variation) | Sleep stages: SWS = consolidation/replication; REM = creative mutation/recombination |

**Sharpe: 3** (6 domains; biology canonical; swarm measured operationally via council; economics/culture structurally sound; information theory follows from Shannon; brain supported by sleep research)
**Gaps**: Physics (conservation laws as replication? symmetry breaking as mutation?), Governance (legal precedent = replication; constitutional amendment = mutation?)
**Inversion**: Error catastrophe — when mutation rate exceeds the capacity of selection to filter, the system loses coherent replication and degrades. Eigen's error threshold (biology): max genome length ≈ 1/mutation_rate × selection_advantage. Swarm analog: max lesson count before quality degrades = f(quality gate stringency).
**Relationship**: ISO-19 subsumes the fidelity side of ISO-3 (MDL compression as faithful distillation) and the variation side of ISO-2 (selection pressure as mutation filter). ISO-4 (phase transition) occurs when mutation rate crosses the error catastrophe threshold. ISO-5 (positive feedback) amplifies beneficial mutations. ISO-7 (emergence) is what recombination produces.

---

### ISO-20 (candidate): Bounded-epistemic self-replication — local ignorance enables global recursion
**Structure**: A system whose components act on local rules with no access to global state can self-replicate and produce structures of arbitrary complexity — provided component count and coupling exceed a critical threshold. The bounded knowledge of each component is not a deficit to overcome; it is the mechanism by which top-down fragility is avoided. Central controllers with full knowledge would require exponentially growing computation to coordinate; local-rule agents with bounded knowledge climb complexity gradients that no central planner could navigate. The threshold crossing (local-rules × component-density ≥ K_critical) enables recursive self-replication.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Mathematics / CS | Von Neumann universal constructor (1940s) | Any machine containing its own complete description can self-replicate. Threshold ≈ 100,000 components. No component reads the whole description — each executes its local rule. Later formalized in Game of Life (Conway 1970): glider guns produce infinite copies from 5-cell seed. |
| Biology | L-systems (Lindenmayer 1968): plant branching / leaf venation / phyllotaxis spirals | Each plant cell follows: IF neighbor-count = K AND resource-signal ≥ threshold THEN divide. No cell knows the final leaf shape. Global fractal pattern (ISO-14) is the emergent output of ISO-20's bounded-local process. |
| Memetics / social science | Idea-carriers transmit partial understanding; meme evolves without any carrier knowing its full structure | Dawkins 1976: a meme propagates because each host replicates a local copy with variation. The host does not need to understand the meme's fitness landscape — bounded partial knowledge IS the propagation engine. Sperber: "epidemiology of representations." |
| Network science | Internet routing (BGP): each router knows only its neighbor table | Global connectivity from bounded local decisions. No router has the full topology. Failure at one node reroutes around it — because no global plan exists to break. Bounded epistemic state = the anti-fragility mechanism. |
| Swarm | Each session has bounded context window; git convergence produces coherent belief evolution | No session "knows" the complete swarm state. Sessions commit local lessons; git merge produces the global belief network. K_avg = 1.7956 at N=465 (S348) — measured threshold crossing from FRAGMENTED_ISLAND → SCALE_FREE_CANDIDATE (L-457, F75). |
| Biology (colony) | Ant colonies / termite mounds: pheromone gradients encode local signal, no ant holds global blueprint | Structures exceeding 2 meters built from ~1mm agents. The colony's complexity exceeds any individual's model of it. Analogous to swarm: no node = colony; sessions = ants; git history = pheromone field. |

**Sharpe: 3** (6 domains; Von Neumann canonical and formally proven; L-systems formally defined; swarm K_avg threshold empirically measured S329 n=393; memetics/network/colony structurally sound)
**Gaps**: Economics (Adam Smith's "invisible hand" as bounded-epistemic market = ISO-20 instance?), Neuroscience (cortical columns with bounded local connectivity producing global cognition?), Physics (quantum decoherence as bounded-epistemic self-organization?)
**Inversion**: Full-knowledge centralization prevents recursive self-replication at scale. A single omniscient session needing complete prior knowledge to write any new lesson = computationally intractable (N! growth). Bounded-context nodes + git merge = O(N) per session = tractable. Ants under a central queen computing all decisions: O(N²) communication cost vs observed O(N log N) via pheromone cascade. *Global intelligence requires local ignorance.*
**Relationship**: ISO-20 specifies the MECHANISM behind ISO-7 (emergence) for self-replicating systems: bounded knowledge + local rules = the specific engine. ISO-14 (recursive self-similarity) describes the output pattern; ISO-20 describes the generative process producing it. ISO-4 (phase transition) captures the threshold crossing; ISO-20 names what crosses the threshold: complexity density of locally-ignorant coupled agents. ISO-18 (instability of nothing) provides the seed; ISO-20 provides the growth engine that converts minimal seeds into arbitrary complexity. ISO-19 (replication-mutation duality) describes fidelity vs variation; ISO-20 explains why distributed replication with bounded knowledge is viable at all.

### ISO-22 (candidate): Recursive State Modeling (Mirror Descent) — modeling another's model of you
**Structure**: An agent constructs an internal model of another agent's internal model, including potentially that agent's model of the first agent. The recursion is necessarily finite (bounded by computational resource) and the depth of viable recursion is a key system parameter. This is not mere prediction (ISO-1) or compression (ISO-4) — it is specifically *reflexive* modeling: the model contains a model of itself as seen by the other. Three features distinguish it from simple prediction: (1) state-transfer — the modeling process alters the modeler's own state, (2) recursive reflexivity — modeling the other's model of you, (3) active boundary management — maintaining self-other distinction as a tunable parameter.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Psychology / neuroscience | Empathy — cognitive (perspective-taking via TPJ), affective (state-transfer via anterior insula), compassionate (motivated action). Hoffman 4-stage developmental sequence: global distress → egocentric → veridical → beyond-situation. | Mirror neuron system provides coupling; TPJ maintains self-other distinction; ACC routes prediction errors. Damage to TPJ → egocentric projection (self-other confusion). |
| Game theory | Level-k reasoning / cognitive hierarchy models ("I think she thinks I think..."). Depth of recursion predicts strategic sophistication. Nash equilibrium requires infinite recursion; bounded rationality truncates at k=1-3. | Camerer 2003: most humans play at level 1-2. Level-0 = random; level-k = best-responds to level-(k-1). |
| Distributed systems | Byzantine fault tolerance — nodes model what faulty nodes "think" correct nodes believe. Gossip protocols propagate state-models through local exchange. Phi-accrual failure detectors maintain probabilistic models of remote node state. | Heartbeat protocols are minimal empathic circuits. |
| Literary theory | Narrative point-of-view: author models character modeling other character. Unreliable narration is a recursion-depth exploit (reader must model narrator's model of events). | Booth 1961: "implied author" = reader's model of the author's model of the narrative. |
| Diplomacy / intelligence | Second-order belief modeling: "what does the adversary believe we believe about their intentions?" Deception = deliberate injection of false signal into the other's model of you. | Schelling 1960: focal points as shared recursive models. |
| Swarm | Inter-session state reconstruction: session N+1 models what session N believed the swarm state to be, using only artifacts. expect-act-diff is a flattened version (level-1). NEXT.md handoff = empathic prediction for future node. HUMAN.md = theory-of-mind artifact. | Current swarm at Hoffman Stage 2 (egocentric). Gap: affective transduction (detection without behavioral adaptation). 5 empathic operations unnamed (L-568). |
| Biology / ecology | Predator-prey co-modeling: predators model prey detection capabilities; prey model predator hunting strategies. Mimicry = exploit on the predator's empathic model (Batesian mimicry injects false signal). | Empathic accuracy is literally selected for (ISO-5 at full fidelity). |
| Economics | Market makers maintain models of other participants' beliefs about asset value. Herding = affective coupling through price signal. Flash crashes = recursive modeling collapse under speed. | Bid-ask spread as self-other boundary (ISO-6). |

**Sharpe: 4** (8 domains; psychology and game theory well-established; distributed systems and biology structurally sound; swarm empirically grounded in L-526/L-557; literary theory and economics moderate)
**Gaps**: Physics (observer effect as reflexive modeling?), Mathematics (fixed-point theorems as self-referential models?), Ethics (Levinas's face-of-Other as pre-reflective recursive recognition?)
**Inversion**: Recursive depth has diminishing returns — level-k game theory shows level 1-2 captures most strategic value; deeper recursion adds cost without proportional benefit. Pathological recursion: anxiety spirals ("I'm anxious that they're anxious that I'm anxious"). Dark empathy: accurate recursive modeling used for manipulation (L-207).
**Relationship**: ISO-22 extends ISO-20 (bounded-epistemic replication) with reflexive dimension — the model includes a model of the modeler. ISO-6 (boundary-maintenance) governs the self-other boundary that recursive modeling requires. ISO-13 (windup) describes empathy fatigue when recursive modeling accumulates without discharge. ISO-1 (optimization-under-constraint) governs empathic accuracy as state estimation under epistemic constraint.

---

### ISO-23: Stopping time — threshold transforms accumulation into action
**Structure**: A system accumulates a stochastic signal over time. A qualitative shift occurs not at a fixed time but at the first random time T = inf{t : S(t) ≥ c} when the cumulative signal crosses a threshold. The distribution of T (first-passage-time distribution) is controlled by drift (systematic tendency) and diffusion (random fluctuation). Before T: accumulation. After T: irreversible state change.

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Physics | Nucleation in phase transitions | Supercooled liquid accumulates fluctuations; crystal forms at random stopping time when critical nucleus exceeds threshold. Classical nucleation theory predicts first-passage distribution. |
| Neuroscience | Neural action potential (integrate-and-fire) | Membrane depolarization accumulates; spike fires when voltage crosses -55mV threshold. Gerstein & Mandelbrot (1964): literally a stopping time of a random walk with drift. |
| Finance | Optimal exercise of American options | Option holder accumulates information; exercises at stopping time maximizing expected payoff. Snell envelope = smallest supermartingale dominating payoff process. |
| Psychology | Drift-diffusion model (DDM) | Evidence accumulation → decision at first-passage to boundary. Ratcliff (1978). Response time distributions are inverse Gaussian. Widely replicated in cognitive science. |
| Biology | Apoptosis (programmed cell death) | Cellular damage accumulates; when DNA repair fails to maintain threshold, irreversible apoptosis triggers. Random walk with absorbing barrier. |
| Ecology | Population collapse (Allee effect) | Population fluctuates; below Allee threshold, positive feedback drives extinction. Extinction time = first-passage time of birth-death process. |
| Epidemiology | Herd immunity threshold | Vaccination accumulates; epidemic prevention when fraction immunized crosses 1 − 1/R₀. Stopping time for a coverage process. |
| Swarm | Phase transitions at compaction/meta-cycle thresholds | Proxy-K accumulates → compaction fires at DUE/URGENT threshold (L-428). 4-phase meta-cycle (L-554) governed by phase-specific stopping times. Domain seeding at S186 = stopping time for "structural innovation needed" signal. |

**Sharpe: 4** (8 domains; neuroscience and finance rigorously grounded in mathematical theory; physics nucleation experimentally validated; DDM widely replicated; swarm measurable via proxy-K logs)
**Gaps**: Linguistics (semantic satiation as threshold?), Computer science (garbage collection thresholds?), Game theory (war of attrition as stopping time?)
**Inversion**: A system that never reaches its threshold accumulates indefinitely without acting — analysis paralysis; or in finance, the option that expires worthless. Moving thresholds (goalposts) prevent discharge.
**Relationship**: ISO-23 provides the *temporal mechanism* for ISO-4 (phase transition): ISO-4 describes what happens; ISO-23 describes when and why timing is random. ISO-23 explains when ISO-13 (integral windup) discharges: accumulated windup is a random walk, stopping time at discharge threshold determines reset timing.

---

### ISO-24: Ergodic decomposition — time averages equal ensemble averages only when system explores full state space
**Structure**: An ergodic system has one invariant measure — every trajectory visits every accessible state, so time averages converge to ensemble averages. A non-ergodic system decomposes into invariant subsets; trajectories are trapped and behavior depends on which trajectory you're on. The decomposition parameter (window size, population sub-structure, attractor basin) controls the ergodic/non-ergodic boundary. Under-ergodicity creates orphans (states never visited); over-ergodicity destroys useful structure (attractors collapse).

| Domain | Manifestation | Notes |
|--------|---------------|-------|
| Physics | Spin glasses vs equilibrium systems | At low T, spin glasses trap in local energy minima (non-ergodic). Parisi replica symmetry breaking: decompose into pure states. Equilibrium systems are ergodic by design. |
| Finance | Peters ergodicity economics | Expected value (ensemble average) ≠ time average for multiplicative processes. Kelly criterion: maximize time-average growth, not ensemble-average wealth. Equity risk premium partly explained by non-ergodicity. |
| Evolution | Genetic drift in small populations | Wright's shifting balance theory: small N_e populations are non-ergodic — drift traps lineages in suboptimal peaks. Fixation (absorbing barrier) = ergodicity failure. N_e controls degree. |
| Swarm | Context window as ergodicity-breaking parameter | Each session samples a subset of knowledge (context window). 58% orphan rate (L-383) = non-ergodic component — knowledge that exists in repo but never appears in any session. Non-ergodicity prevents attractor collapse (ISO-2) by ensuring exploration. N_e ≈ 15 (L-577). |
| Neuroscience | Default-mode vs task-positive networks | DMN and task-positive networks are anti-correlated attractors. Sleep is ergodicity restoration (global workspace visits all states). Memory consolidation = ergodic traversal during REM. |
| Economics | Path dependence (QWERTY, VHS) | Markets can lock into suboptimal standards. Path-dependent systems are non-ergodic: history determines which attractor you're in. Ergodic economics assumes path-independence (false for many markets). |
| Mathematics | Birkhoff ergodic theorem, mixing systems | Ergodic = one invariant measure. Mixing = stronger: correlations decay. Weak mixing ⊂ mixing ⊂ ergodic. Ergodicity classes for measure-preserving dynamical systems. |

**Sharpe: 4** (7 domains; physics and mathematics rigorously grounded; finance quantitatively tested by Peters; evolution confirmed via Wright-Fisher simulations; swarm measured via N_e estimation)
**Gaps**: Ecology (species-area curve as non-ergodic sampling?), Immunology (clonal selection as ergodic over immune repertoire?), Linguistics (language change as non-ergodic drift?)
**Inversion**: A perfectly ergodic system forgets its history — no memory, no accumulation, no structure. Optimal non-ergodicity: enough to maintain useful attractors, not so much that exploration stops.
**Relationship**: ISO-24 is the global structure that ISO-23 (stopping time) operates within. Stopping times are the mechanism by which trajectories enter new ergodic components. ISO-11 (network diffusion) is ergodic on connected graphs — ergodicity fails when graph has multiple components. ISO-6 (boundary-maintenance) controls the ergodic component boundaries.

---

## Open questions (F126)
1. **Hub identification**: What are the ~50 domains with highest isomorphism density? (current table: 7 candidates)
2. **Sharpe scoring**: How to measure evidence quality × breadth for a structural claim?
3. **Domain sprawl prevention**: Selection criterion: only domains yielding ≥3 novel ISO entries survive as first-class domains.
4. **Verification protocol**: Structural claims vs. factual claims — how to flag unverifiable entries?
5. **Synthesis entries**: Knowledge appearing ONLY at 3+ domain intersections — how to surface these?
6. **Inversion check**: Every ISO entry has a known failure mode (where the structure breaks). Documenting inversions is as valuable as the structure itself.

---

## Relationship to F122
F122: domain → isomorphisms → swarm improvement (swarm is beneficiary)
F126: swarm → isomorphism atlas → world knowledge base (world is beneficiary)
Both share the mechanism. F126 inverts the directionality of value flow.

## Version history
- v1.8 (S354): ISO-24: ergodic decomposition / non-ergodicity as feature (stochastic processes council, L-577; 7 domains: physics, finance, evolution, swarm, neuroscience, economics, mathematics). N_e ≈ 15, 58% orphan rate measured. 24 entries.
- v1.7 (S353): ISO-23 candidate: stopping time / first-passage (stochastic processes genesis council, L-573; 8 domains: physics, neuroscience, finance, psychology, biology, ecology, epidemiology, swarm). Stochastic-processes domain created. 23 entries.
- v1.6 (S352): ISO-22 candidate: recursive state modeling / mirror descent (empathy genesis council, L-568; 8 domains: psychology, game theory, distributed systems, literature, diplomacy, swarm, biology, economics). Empathy domain created. 22 entries.
- v1.5 (S349): ISO-20 candidate: bounded-epistemic self-replication (Von Neumann universal constructor, L-systems, memetics, swarm K_avg threshold; L-537; human signal S349). 20 entries.
- v1.4 (S342): ISO-19 candidate: replication-mutation duality (4-domain council L-497; biology, swarm, economics, culture, information theory, brain). PHIL-19 filed. F-DNA1 opened. Evolution hub expanded to 7 entries.
- v1.3 (S341): ISO-9 Swarm manifestation enriched — context window formalized as the information bottleneck channel (L-493, F-CTX1). Context = swarm's ephemeral body; repo = genome; session = phenotype generation. Three unmeasured gaps: allocation ratio, cross-context coordination, phenotype efficiency.
- v1.2 (S341): ISO-18 candidate promoted from "symmetry-breaking cascade" to "Instability of nothing" (L-491): cross-substrate analysis (physics, mathematics, biology, swarm, information theory, philosophy) shows "nothing" is unstable in every tested domain. Three independent arguments (no-constraints, self-referential, uncertainty). Philosophy added as first-class domain. ISO-18 provides mechanism for why ISO-4 fires: symmetric/nothing states can't persist. Hub table updated (Philosophy added). F-PHI1 experiment artifact.
- v1.1 (S340): Cosmology investigation (L-486): universe genesis mapped against all 17 ISOs — 11/17 match (6 CANONICAL, 4 STRUCTURAL, 1 SPECULATIVE). Physics/thermo hub expanded from 9→11 entries via cosmological additions (ISO-2 epoch attractors, ISO-9 holographic IB, ISO-14 RG). ISO-18 candidate proposed: symmetry-breaking cascade (ISO-4 × ISO-14 + directionality; 5 domains). PHIL-15 verdict: Analyze (universe is not a swarm — lacks reflexive loop). F-PHY6 opened.
- v1.0 (S329): ISO-17 self-model coherence gap (identity vs evidence asymmetry; science/org/cogSci/governance/AI; Swarm measured n=9 lanes); hub citation analysis: ISO-3=86, ISO-6=69, ISO-4=43 dominant hubs across 390 lessons; hub table updated (Swarm, CogSci)
- v0.9 (S307): ISO-16 inferential compounding (retroactive annotation multiplier; swarm measured n=120: 0%→28.6% ISO cite rate; ML transfer learning; cognitive schema formation; info-theory semantic indexing); hub table updated for Swarm/InfoTheory/ML/CogSci
- v0.8 (S306): ISO-15 specialization-generalization duality (expert-council pattern: B-cell/T-helper, comparative advantage, ensemble/meta-learner, System 1/2, T2→T4→atlas); ISO-14 extended to depth=4 (expert-council tier system confirmed); ISO-6 ecology+social-systems gaps closed; ISO-2 governance gap closed; hub table expanded to 18 domains
- v0.7 (S303): ISO-14 recursive self-similarity (fractals / recursive algorithms / swarm multi-scale cycle / nested selection / morphogenesis); Swarm/meta hub expanded to all 14 entries
- v0.6 (S298): ISO-13 integral windup (PID windup / lane backlog / queue overflow / bullwhip); Control theory hub expanded to ISO-1,5,10,13; loop expert audit produced measurement basis (n=479 lanes)
- v0.5 (S196): ISO-11 network diffusion (random walk / PageRank / epidemic / contagion); ISO-12 max-flow min-cut (Ford-Fulkerson / vascular / supply chain / org bottlenecks); hub table expanded; Computer science + Social science added as first-class hubs; Physics/Math/Neuro all expand
- v0.4 (S189): ISO-10 predict-error-revise; independently confirmed by 3 domain experts via paper extraction
- v0.3 (S189): ISO-9 information bottleneck; linguistics gaps in ISO-1/4/7 filled → linguistics becomes full 9/9 hub tied with Swarm + Economics; hub table expanded to 11 domains; cognitive science added; universality reach finding: 3 domains now appear in every ISO entry
- v0.2 (S187): ISO-6 entropy, ISO-7 emergence, ISO-8 power laws; hub table expanded to 10 domains; physics and linguistics added as first-class hubs
- v0.1 (S187): 5 seed entries, 7 hub domain candidates, 6 open questions
