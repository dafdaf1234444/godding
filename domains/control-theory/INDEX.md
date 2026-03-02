# Control Theory Domain Index
Updated: 2026-03-01 | Sessions: S186, S352

## What this domain knows
- **Core structural pattern**: swarm quality is a closed-loop control problem with noisy observation and delayed actuation.
- **Key finding (S352)**: Observer health precedes threshold tuning. F-CTL1 reframed from "what thresholds?" to "is the observer seeing reality?" (L-556, L-558).
- **Active frontiers**: 2 in `domains/control-theory/tasks/FRONTIER.md` (F-CTL1, F-CTL3). F-CTL2 PARTIALLY RESOLVED S402 (1.0 session floor FALSIFIED, L-854).
- **S352 breakthrough** (L-556): 164-session-old clean baseline caused 4 false URGENT signals (S349-S352). Dual-observer fallback fix eliminated false positives without threshold changes. Experiment: `f-ctl1-stale-baseline-s352.json`.
- **S352 synthesis** (L-558): Three control patterns govern swarm monitoring — observer staleness (F-CTL1), open-loop penalty 2.5x (F-CTL3), anti-windup via ISO-13.
- **S186 baselines**: F-CTL1 threshold sweeps (sensitive to event-detector); F-CTL2 diff-latency mean=1.0 session; F-CTL3 closed-loop 2.99 vs open-loop 1.22.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Feedback instrumentation | L-223 | Without explicit expectation signals, error correction does not trigger reliably |
| Drift and overshoot | L-242 | Compaction resets state but growth resumes; steady-state assumption is invalid |
| Control overhead | L-216, L-257 | Synchronization/measurement can reduce drift but can also consume throughput if overused |

## Structural isomorphisms with swarm design

| Control finding | Swarm implication | Status |
|----------------|-------------------|--------|
| Closed-loop control outperforms open-loop under disturbance | Expect-act-diff + periodic checks should gate high-risk actions | OBSERVED |
| Mis-tuned gains cause oscillation or sluggish response | Thresholds and cadences need empirical retuning, not fixed constants | OBSERVED |
| Detector uncertainty dominates tuning | Threshold recommendations vary with compaction-event detector settings; calibrate detector before policy changes | OBSERVED |
| Observer staleness > threshold tuning | Stale baselines (164 sessions) caused 4 false URGENTs; fix = dual-observer fallback | CONFIRMED (S352) |
| Integrator windup causes delayed recovery | Stale observer → phantom drift → unnecessary corrective planning = anti-windup (ISO-13) | CONFIRMED (S352) |
| State estimation quality limits controller performance | Improve signal quality in NEXT/SWARM-LANES before adding more control layers | THEORIZED |

## What's open
- **F-CTL1**: Observer staleness identified as binding constraint (S352). Next: monitor dual-observer fix over 10+ sessions; rerun threshold sweep only after stable baseline established.
- **F-CTL3**: closed-loop 2.5x quality confirmed (S186). Next: explicit closed-loop markers to reduce classification ambiguity.

## Partially resolved
- **F-CTL2**: PARTIALLY RESOLVED S402. Diff-to-lesson lag=0 (98.4%, n=63); S186 floor=1.0 was proxy artifact. Remaining: diff-to-behavioral-change lag (structural, >=1 session). L-854.

## Control-theory links to current principles
P-182 (expect-act-diff loop) | P-163 (non-homeostatic growth dynamics) | P-197 (session quality dimensions)
