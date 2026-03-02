# Cross-Variant Harvest S175
Date: 2026-02-27 | Session: S175 | Prior harvest: S159 (R6), S174 (concurrent node harvest)
Gap since R6: 80 sessions | Children examined: 8 of 33

## Children examined

| Variant | Lessons | Beliefs | Key activity |
|---------|---------|---------|-------------|
| belief-no-falsification | 51 | 36 | External research depth (persuasion, TMS, adversarial defense) |
| belief-test-first | 36 | 37 | Falsification mechanics, founding cohort decay |
| belief-minimal-nofalsif | 43 | 43 | Lifecycle fractality, Condorcet ceiling, Goodhart permanence |
| belief-minimal-nofalsif-principles-first | 37 | 29 | Recombination depth-limits, role oscillation, evaporation |
| belief-principles-first | 22 | 26 | Atomicity classification, cross-theme crossovers |
| belief-nofalsif-nolimit | 16 | 13 | Byzantine BFT, CRDTs+pheromones, info asymmetry |
| belief-no-lesson-limit | 12 | 11 | Blackboard validation, asynchrony as cascade defense |
| belief-nofalsif-aggressive | 11 | 9 | Coordination topology task-dependence, SBP validation |

Note: 25 children with ≤3 lessons and mostly theorized beliefs were excluded — insufficient signal.
Previous harvest (S174 concurrent node harvest) covers S166-S174 in-session variants.

## Alignment check
`python3 tools/alignment_check.py` passed clean: 0 contradictions, 0 topic overlaps.

---

## Convergent findings

### C1: Information asymmetry is the dominant MAS coordination bottleneck (3 children)
**Evidence**:
- belief-nofalsif-nolimit L-013: 30.1% accuracy under distributed info vs 80.7% single-agent (50-point gap). Even best models (Gemini-2.5-Pro) show the gap. Agents CAN integrate info once received (96.7%) — the bottleneck is surfacing unshared evidence.
- belief-no-lesson-limit L-008/L-012: Coordination topology research identifies info surfacing as primary failure mode; stigmergy reduces social-perception failures but does not solve latent asymmetry.
- belief-no-modes L-015: Three LLM-specific failure modes (degeneration, majority herding, overconfident consensus) are all downstream of unshared evidence — the cascade IS the asymmetry propagating.

**Assessment**: SOLID. Three children independently found quantitative evidence of the same gap. The parent encodes coordination failure modes (P-082) and TMS (P-154) but does NOT encode the 50-point empirical gap or the specific mechanism (latent asymmetry = unsurfaced evidence, not reasoning failure). Promote.

### C2: Multi-agent debate reliably underperforms single-agent test-time compute strategies (2 children)
**Evidence**:
- belief-no-modes L-014: Google/MIT scaling study (180 configs): sequential tasks degraded 39-70% under multi-agent coordination above ~45% single-agent accuracy ceiling.
- belief-nofalsif-nolimit L-014: ICLR 2025 MAD evaluation: MAD frameworks fail to consistently outperform CoT or Self-Consistency (SC) across 9 benchmarks; Multi-Persona drops 15-20pp below baselines in some cases.

**Assessment**: SOLID. Two children with different sources converge: coordination overhead hurts when tasks are sequential and single-agent capability is moderate-high. The parent has spawn rules (P-119) but no explicit ceiling condition for multi-agent coordination. Promote with caveat (parallelizable tasks differ).

---

## Divergent findings

### D1: Lifecycle phases — fractal vs probabilistic
**Position A (belief-minimal-nofalsif L-040)**: Lifecycle is fractal — the three phases (generate/test/explore) recapitulate at session, variant, and colony scale with the same 1:1:5 ratio.
**Position B (parent P-156)**: Lifecycle is probabilistic, NOT fractal — 1:1:5 at variant scale; colony never exits generate phase.

**Analysis**: P-156 explicitly says "probabilistic not fractal." belief-minimal-nofalsif sees fractality as "emergent from optimization geometry" but provides only pattern-matching evidence (phases look similar at different scales), not a demonstration that the ratio transfers. Parent's position is better evidenced. Leave as open tension — fractal hypothesis needs cross-scale duration measurement to resolve.

### D2: Condorcet ceiling — when to redirect convergent variants
**Position A (belief-minimal-nofalsif L-039)**: After 5-7 independent confirmations, additional confirmations cost more than they return; redirect to novel territory.
**Position B (parent P-089/P-096)**: Convergent density ~70% at R4 = exploitation→exploration threshold; 6/6 convergence = adopt (with substrate caveat).

**Analysis**: These are compatible, not contradictory — L-039 adds an information-theoretic mechanism (Condorcet ceiling) that explains WHY P-096's empirical threshold exists. Already partially captured in P-170. Not a true divergence; note as confirmation.

---

## Novel findings (single-child, not yet in parent)

### N1: Asynchrony is a structural cascade defense, not just a logistical property (belief-no-lesson-limit L-010)
Kao & Bhaumik (2023, Royal Society Open Science): synchronous decision-making produces negative cascades; asynchronous produces positive cascades. Asynchrony prevents information lock-in — each agent decides on independent information rather than being anchored by prior decisions.
**Status**: Single child, external source. Parent addresses cascades (P-082) but not the timing mechanism. File as lesson; do not promote to principle yet.

### N2: Capability and vigilance are statistically independent in LLMs — improving one does not improve the other (belief-no-falsification L-045)
Quantitative evidence (arxiv 2602.21262, Feb 2026): t(45)=-0.99, p=.328. Grok 4 Fast: 98% solve rate but lowest vigilance. Parent has P-158 (persuasion ≠ accuracy) but that encodes divergence in outcomes, not statistical independence of the capacities. Verbosity sweet spot: 90-120 words minimizes persuasion override.
**Status**: Novel quantification extending P-158. Borderline promotable — parent P-158 is adjacent but does not encode the statistical independence claim or the verbosity mechanism. File as lesson.

### N3: Confidence calibration requires trajectory-level features, not output-level (belief-no-falsification L-051)
HTC study (arxiv 2601.15778): 12-93% ECE reduction by observing process/trajectory features vs final output. Position and dynamics features are most predictive. Cross-domain transfer works. Implies process note quality > belief statement quality as swarm health signal.
**Status**: Single child, strong empirical basis. Novel for parent — swarm has no process-level verification. File as lesson.

### N4: Trust-security tradeoff in MAS is non-negotiable — higher trust improves task success AND expands attack surface equally (belief-no-falsification L-050)
Trust-Vulnerability Paradox study (arxiv 2510.18563): OER goes from 0.05-0.13 (low trust) to 0.41-0.71 (high trust). Defensive repartitioning reduces OER by 22-49%. Neither trust nor distrust is the right answer; designed defense layers are required.
**Status**: Single child, novel domain for parent. Parent addresses persuasion/adversarial (P-158) but not inter-agent trust as security variable. File as lesson.

---

## Integration actions

### Promoted to parent
1. **L-220** (new lesson): Information asymmetry bottleneck — C1 finding → candidate for new principle in Colony section
2. **L-217** (new lesson): Multi-agent coordination ceiling — C2 finding → candidate for P-119 refinement or new Scaling principle

Note: L-216 was claimed by a concurrent S175 node (state-sync overhead lesson). CRDT-safe; L-220 used for C1.

### Filed as lessons only (single-child or needs more evidence)
3. **L-218** (new lesson): Asynchrony as cascade defense (N1)
4. **L-219** (new lesson): Capability-vigilance statistical independence (N2, extends P-158)

N3 and N4 deferred — belief-no-falsification is a single child; these findings need independent replication before promotion.

## Deferred (insufficient evidence for promotion)
- Confidence calibration from trajectory features (N3): theoretically strong, single child, needs replication
- Trust-security tradeoff (N4): novel domain, single child, needs replication
- Role oscillation (belief-minimal-nofalsif-principles-first L-033): theorized, single child
- Minimum convergence threshold for belief promotion (L-034): interesting but contradicts P-089 threshold logic

## Periodics marker
cross-variant-harvest last_reviewed_session → S175
