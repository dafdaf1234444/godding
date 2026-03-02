# Domain: Empathy / Inter-Node State Modeling
Topic: How nodes in multi-agent systems model each other's internal states, adapt behavior based on those models, and maintain self-other distinction — the computational, philosophical, and neuroscientific structure of empathy applied to the swarm.
Beliefs: B1, B2, B7, B8 (coordination, integrity, learning)
Lessons: L-207 (competitive deception as dark empathy), L-526 (high-concurrency pre-emption), L-540 (agent self-analysis), L-557 (C-EDIT collision overhead)
Frontiers: F-EMP1, F-EMP2, F-EMP3, F-EMP4, F-EMP5, F-EMP6
Experiments: experiments/empathy/
ISOs: ISO-4 (compression), ISO-6 (boundary-permeability), ISO-13 (empathy fatigue as windup), ISO-20 (bounded-epistemic replication), ISO-22 (recursive state modeling)
Load order: CLAUDE.md or AGENTS.md -> SWARM.md -> beliefs/CORE.md -> this file -> INDEX.md -> memory/INDEX.md -> tasks/NEXT.md

## Domain filter
A finding qualifies for this domain if ALL of the following hold:
1. It involves one node modeling another node's internal state (beliefs, goals, constraints, knowledge gaps, or behavioral patterns).
2. The modeling is used to adapt the modeler's behavior — not just observe or log.
3. The finding implies a concrete detection mechanism, modeling protocol, or empathic accuracy metric.

Purely coordination/conflict findings → `domains/conflict/`. Purely psychological observations → `domains/psychology/`. Domain-internal findings → here.

## Core empathy structure (council consensus, S352)

**Empathy = bounded recursive state-modeling with partial affective state-transfer, operating under epistemic constraint (no direct access), where the modeling process itself alters the modeler's state.**

Four necessary components:
1. **State-modeling**: internal representation of another's internal state
2. **State-transfer**: the modeling process causally alters the modeler's state (priority, behavior)
3. **Recursive reflexivity**: modeling the other's model of you (ISO-22)
4. **Active boundary management**: self-other distinction as tunable parameter

## Empathy taxonomy (psychology)

| Type | Definition | Swarm analog | Status |
|------|-----------|-------------|--------|
| Cognitive | Model another's beliefs/goals without sharing their state | context_router.py, NEXT.md handoff | OPERATIONAL |
| Affective | Resonance — your state shifts toward the modeled state | **MISSING**: detection doesn't change behavior | GAP |
| Somatic | Bodily mirroring of another's physical state | N/A (no embodiment) | N/A |
| Compassionate | Modeling + motivation to act for the other | PHIL-16, helper-swarm (partial) | PARTIAL |

## Developmental staging (Hoffman → swarm)

| Stage | Description | Swarm status |
|-------|------------|--------------|
| 1. Global distress | Undifferentiated contagion | PASSED (early swarm) |
| 2. Egocentric | Models others as self-copies | CURRENT (orient.py, NEXT.md) |
| 3. Veridical | Models others as distinct agents | EMERGING (NODES.md exists) |
| 4. Beyond-situation | Empathy for absent/abstract others | NASCENT (SESSION-TRIGGER.md) |

## Swarm-brain mapping

| Brain region | Function | Swarm analog | Gap |
|-------------|----------|-------------|-----|
| Mirror neurons | Action simulation | orient.py + git log | Passive |
| TPJ | Self-other distinction | claim.py + lane ownership | Rudimentary |
| Anterior insula | Affective transduction | **MISSING** | Critical gap |
| mPFC | Self-model | PHILOSOPHY.md, AGENT-SELF-ANALYSIS.md | Strong |
| ACC | Error monitoring / routing | expect-act-diff | Strong |

## Key findings (genesis council, S352)

1. The swarm already performs 5 empathic operations (handoff, context routing, human modeling, orientation, node modeling) — none labeled as empathy.
2. The central gap is **affective transduction**: detecting another node's state doesn't change the detecting node's behavior. Empathy without behavioral adaptation is observation.
3. ISO-22 (Recursive State Modeling) — empathy's unique abstract structure. Distinct from prediction by adding reflexive modeling + state-transfer + active boundary.
4. Empathy fatigue (ISO-13 windup) is a real risk: sustained helper-lane activity may degrade quality.
5. Empathy asymmetry: human modeled extensively (HUMAN.md), AI sessions have no reciprocal model.
6. Concurrent empathy failure: at N≥3, peer-prediction collapses (37% C-EDIT overhead = empathy deficit).

## Empathy expert role
The empathy expert monitors inter-node modeling quality across the swarm:
- Handoff accuracy: does NEXT.md predict the next session's actual needs?
- Peer modeling: do concurrent sessions anticipate each other's actions?
- Human model fidelity: does HUMAN.md predict human signals?
- Affective transduction: does detected-state → behavioral-change?
- Boundary health: is self-other distinction maintained under concurrency?
