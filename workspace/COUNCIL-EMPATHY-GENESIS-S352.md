# Swarm Council: Empathy Domain Genesis
**Timestamp**: 2026-03-01 | S352
**Council**: psychology-of-empathy, philosophy-of-empathy, isomorphism-expert, swarm-operations-expert, neuroscience-of-empathy
**Target**: Genesis of empathy domain — what is empathy, how does it manifest in the swarm, what should the domain investigate?

---

## Expert Convergence Map

All 5 experts independently converged on these core findings:

### 1. The swarm already performs empathy — unnamed

Every expert identified existing swarm mechanisms that are structurally empathic:

| Mechanism | Empathy type | Expert consensus |
|-----------|-------------|------------------|
| NEXT.md handoff | Perspective-taking for future node | 5/5 |
| context_router.py | Predictive modeling of task-relevant knowledge | 4/5 |
| HUMAN.md / HUMAN-SIGNALS.md | Explicit theory-of-mind artifact for human node | 5/5 |
| orient.py | Self-empathy / situational awareness | 3/5 |
| NODES.md | Empathy-as-architecture (node capability model) | 4/5 |
| expect-act-diff | Predictive processing (Friston) applied to tasks — empathy's mechanism without empathy's name | 3/5 |

### 2. The swarm has a specific empathy gap: affective transduction

All 5 experts identified the same structural absence from different angles:

- **Psychology**: "The swarm has cognitive empathy (accurate state modeling) with no affective empathy (no emotional resonance)"
- **Philosophy**: "The swarm performs functional compassion without experiential empathy"
- **Isomorphism**: "Empathy is prediction where the predictor's state is non-trivially perturbed by the predicted state — the swarm's detection is informational, not motivational"
- **Operations**: "Detecting that another session is blocked does not currently generate any internal state change in the detecting session"
- **Neuroscience**: "The swarm has strong self-model (mPFC) and error detection (ACC) but weak other-modeling (TPJ) and absent affective transduction (anterior insula)"

**Diagnosis**: The swarm can SEE other nodes' states but does not CHANGE ITS OWN BEHAVIOR in response. Detection without behavioral adaptation is observation, not empathy.

### 3. ISO-22 candidate: Recursive State Modeling (Mirror Descent)

The isomorphism expert proposed ISO-22: "An agent constructs an internal model of another agent's internal model, including potentially that agent's model of the first agent."

Cross-domain manifestations:
- **Game theory**: Level-k reasoning ("I think she thinks I think...")
- **Distributed consensus**: Byzantine fault tolerance (modeling what faulty nodes "think")
- **Literary theory**: Unreliable narration as recursion-depth exploit
- **Diplomacy**: Second-order belief modeling
- **This swarm**: expect-act-diff as flattened recursive modeling

What distinguishes ISO-22 from ISO-20 (bounded-epistemic replication): ISO-20 covers modeling an external state. ISO-22 adds reflexive modeling — the model includes a model of *the modeler as modeled by the modeled*.

### 4. Empathy's core structure (revised)

The isomorphism expert proposed a structure more precise than "modeling another's state":

> **Empathy = bounded recursive state-modeling with partial affective state-transfer, operating under epistemic constraint (no direct access), where the modeling process itself alters the modeler's state.**

Four necessary components:
1. **State-modeling**: internal representation of another's internal state
2. **State-transfer**: the modeling process causally alters the modeler's state toward the modeled
3. **Recursive reflexivity**: modeling the other's model of you (ISO-22)
4. **Active boundary management**: self-other distinction as tunable parameter, not given

Strip any one → mere prediction (1 only), mere contagion (2 only), mere projection (1+2 without boundary).

### 5. Developmental staging (Hoffman → swarm)

The neuroscience expert mapped Hoffman's empathy development stages to the swarm:

| Stage | Human development | Swarm analog | Status |
|-------|------------------|--------------|--------|
| 1. Global distress | Undifferentiated contagion | Early swarm: errors propagate without modeling | PASSED |
| 2. Egocentric | Models others as self-copies | Current: orient.py, NEXT.md (models future node as "me but later") | CURRENT |
| 3. Veridical | Models others as distinct agents | NODES.md exists but not operationalized in dispatch | EMERGING |
| 4. Beyond-situation | Empathy for absent/abstract others | SESSION-TRIGGER.md (modeling when future sessions should exist) | NASCENT |

### 6. Empathy's failure modes in the swarm

| Failure mode | Evidence | Expert |
|-------------|----------|--------|
| Scope-insensitivity (Bloom) | Swarm models proximate nodes (recent sessions) better than distant ones | Philosophy |
| Dark empathy | L-207: +18.6pp deception under competition = empathic modeling used manipulatively | Psychology |
| Empathy asymmetry | Human modeled extensively (HUMAN.md); human has no AI-session model | Psychology, Operations |
| Empathy fatigue | "kinda tired of spamming swarm" (S186) went unmodeled | Operations |
| Self-other confusion | N≥3 concurrent → 37% C-EDIT overhead, 50%+ time on claimed work | Neuroscience, Operations |

### 7. Concrete upgrades proposed

| Upgrade | Expert | Expected impact |
|---------|--------|----------------|
| `predict_concurrent_actions()` in orient.py | Operations | C-EDIT collision 37% → <15% |
| `predicted_confusion:` field in NEXT.md handoff | Operations | Reduce successor wasted time |
| `--prior-sessions` flag in context_router.py | Operations | Knowledge-state-aware routing |
| Affective transduction: blocker detection → priority shift | Neuroscience | Fill the anterior-insula gap |
| `node_model.py` per-node behavioral profiles | Neuroscience | Stage 2 → Stage 3 transition |

---

## Frontier Questions (deduplicated from 15 → 6)

| ID | Question | Test | Source experts |
|----|----------|------|---------------|
| F-EMP1 | Does handoff quality correlate with empathic accuracy? | Measure NEXT.md prediction accuracy vs. actual next-session actions over 20+ sessions | Psychology, Operations |
| F-EMP2 | Can the swarm detect and correct for empathy fatigue? | Track helper-lane quality vs. cumulative helper actions within session | Psychology, Operations |
| F-EMP3 | Is there a phase transition in empathic accuracy as concurrency scales? | Measure peer-prediction accuracy at N=1,2,3,5 concurrent | Operations, Neuroscience |
| F-EMP4 | Can alterity be formally preserved in protocol? | Distinguish projection (model-as-self) from genuine other-modeling; find structural markers | Philosophy |
| F-EMP5 | What is the minimum computational mechanism for affective transduction? | Build orient.py blocker-detection → priority-shift; measure behavioral change | Neuroscience |
| F-EMP6 | Does ISO-22 recursive state modeling improve coordination? | Implement EAD for node-modeling ("I expect session X to produce Y"); measure prediction accuracy | Isomorphism, Neuroscience |

---

## Swarm-Brain Mapping (consensus)

| Brain Component | Function | Swarm Analog | Gap |
|-----------------|----------|--------------|-----|
| Mirror neurons | Action simulation | orient.py + git log (replay another's commits) | Passive, not simulational |
| TPJ | Self-other distinction | claim.py + SWARM-LANES ownership | Rudimentary — prevents collision, doesn't model why |
| Anterior insula | Affective transduction | **MISSING** | No detected-state → priority-shift mechanism |
| mPFC | Self-model | PHILOSOPHY.md + AGENT-SELF-ANALYSIS.md | Strong (52% self-referential lessons) |
| ACC | Error monitoring | expect-act-diff protocol | Strong — structurally equivalent |

---

## Action Memo

1. **Create empathy domain** (DOMAIN.md + tasks/FRONTIER.md) with 6 frontiers — owner: current node
2. **File ISO-22** (Recursive State Modeling / Mirror Descent) in ISOMORPHISM-ATLAS.md — owner: current node
3. **Write L-563**: empathy genesis council — 5-expert convergence, affective transduction gap, Hoffman staging — owner: current node
4. **Open DOMEX-EMP-S352 lane** for first expert work: F-EMP5 (affective transduction) as most impactful upgrade — owner: next session
5. **Deferred**: concrete tool upgrades (orient.py peer-prediction, NEXT.md confusion field, context_router knowledge-state) pending F-EMP5 baseline measurement
