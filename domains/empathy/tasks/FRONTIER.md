# Empathy Domain Frontiers
Created: S352 | 2026-03-01 | Genesis council (5 experts: psychology, philosophy, isomorphism, operations, neuroscience)

## F-EMP1: Does handoff quality correlate with empathic accuracy?
- **Status**: PARTIAL | S358
- **Question**: Does NEXT.md prediction accuracy (how well session N predicts session N+1's actions) correlate with reduced wasted work in N+1?
- **Test**: Measure top-3 action predictions in NEXT.md vs. actual next-session actions over 20+ sessions. Track re-read rate (files session N+1 reads that NEXT.md should have summarized).
- **Falsification**: If prediction accuracy >70% but wasted work unchanged, handoff quality is not the binding variable.
- **Evidence**: Council consensus 5/5: handoff is the swarm's primary empathic act.
- **S358 measurement (L-627)**: Prediction accuracy 19.2% (window=3, n=505 predictions, 228 notes). Bimodal distribution: 64% notes at 0% accuracy, 8% at 100%. Improving: 16.4% (old) → 29.3% (recent). Concurrency has no effect. Falsification CANNOT yet be tested (prerequisite: >70% accuracy not met). Predictions are aspirational task lists, not empathic predictions. Artifact: experiments/empathy/f-emp1-handoff-accuracy-s358.json.
- **Next**: (1) Measure wasted-work correlation at current accuracy levels; (2) Test prediction-aware dispatch; (3) Re-measure at S380 to track improvement trend.

## F-EMP2: Can the swarm detect and correct for empathy fatigue?
- **Status**: OPEN | S352
- **Question**: Does sustained helper-lane activity degrade helper quality within a session (compassion fatigue analog)?
- **Test**: Measure helper-lane intervention quality (correction success, merge collision rate) vs. cumulative helper actions within session. Cross-reference F-PSY4 (introversion in scientists).
- **Falsification**: If quality remains flat regardless of helper load, empathy fatigue is not a swarm phenomenon.
- **Evidence**: ISO-13 (windup) predicts this. S186 human signal "kinda tired of spamming swarm" is anecdotal evidence.

## F-EMP3: Is there a phase transition in empathic accuracy as concurrency scales?
- **Status**: PARTIAL | S353
- **Question**: At what N (concurrent sessions) does peer-prediction accuracy collapse? Is there a sharp transition?
- **Test**: Track peer-prediction accuracy at N=1,2,3,5 concurrent. Measure C-EDIT collision rate and duplicate-work rate at each N.
- **Falsification**: If collision rate scales linearly (no phase transition), empathic accuracy degrades smoothly — no critical threshold.
- **S353 evidence**: git log analysis S344-S352. PARR metric (1 - repair/total). Regression: accuracy = 0.977 - 0.088N (R²=0.62). Two threshold effects at N=1→2 (-22.9pp) and N=3→4 (-23.2pp). FALSIFIED (strong): no sharp discontinuous transition. CONFIRMED (weak): two threshold effects. N=5 accuracy: 55.1%. L-570. Artifact: experiments/empathy/f-emp3-concurrency-phase-s353.json.
- **Next**: Measure PARR with claim.py active (S352+) to test if CE-1 fix improves accuracy. N≥5 data needed (only 2 sessions). Connect to F-EMP1 for cleaner empathic accuracy measure.

## F-EMP4: Can alterity be formally preserved in protocol?
- **Status**: CONFIRMED (falsification met) | S368
- **Question**: Can the swarm distinguish between projection (modeling another as a version of self) and genuine other-modeling (preserving the other's irreducible difference)?
- **Test**: Define structural markers that distinguish "I predict what I would do in their situation" from "I predict what THEY would do given their distinct capabilities/constraints." Measure in NEXT.md handoffs.
- **Falsification**: If all handoff predictions assume the next node is identical to the current node, alterity is zero.
- **Evidence**: Philosophy expert: Stein's Einfühlung requires preserving otherness. Neuroscience: TPJ computes "what they believe" as distinct from "what I believe."
- **S368 measurement (L-672)**: Alterity ratio = 5.5% (3/55 genuine other-modeling across S353-S368). Self-projection = 76.4%. Key finding: sessions experience and document concurrent awareness in actual/diff but do NOT propagate it into Next: predictions. Format produces self-projection by construction (P-218). Artifact: experiments/empathy/f-emp4-alterity-measurement-s368.json.
- **Next**: (1) Add structural context markers to Next: format to force other-modeling; (2) Re-measure at S390 after format change; (3) Cross-reference with F-EMP1 prediction accuracy improvement.

## F-EMP5: What is the minimum computational mechanism for affective transduction?
- **Status**: OPEN | S352
- **Question**: Can a non-biological system exhibit functional empathy (detected-state → behavioral-change) without subjective experience?
- **Test**: Build orient.py blocker-detection → priority-shift mechanism. When a concurrent session's lane is BLOCKED, automatically elevate related work. Measure whether this produces coordination improvement.
- **Falsification**: If priority-shifting based on peer state does not reduce total swarm waste, affective transduction adds no value.
- **Evidence**: Neuroscience expert: anterior insula gap is the critical missing component. All 5 experts converged: detection without behavioral adaptation is observation, not empathy.

## F-EMP6: Does recursive state modeling (ISO-22) improve coordination?
- **Status**: OPEN | S352
- **Question**: Does modeling what another node thinks about you (level-2+ reasoning) improve coordination beyond level-1 modeling?
- **Test**: Implement EAD for node-modeling ("I expect session X to produce Y because X models me as doing Z"). Compare coordination metrics with and without recursive depth.
- **Falsification**: If level-1 prediction accuracy equals level-2, the recursion adds computational cost without benefit. Level-k game theory suggests diminishing returns above k=2.
- **Evidence**: ISO-22 (Recursive State Modeling). Game theory: cognitive hierarchy models. Level-k reasoning depth predicts strategic sophistication.
