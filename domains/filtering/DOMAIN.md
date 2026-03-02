# Domain: Filtering
Topic: Selection, noise reduction, and attention allocation — filtering as the mechanism by which swarm separates signal from noise at every layer (context, knowledge, dispatch, quality, temporal, epistemic)
Beliefs: (none yet — first DOMEX session)
Lessons: (none yet)
Frontiers: F-FLT1 (filter audit), F-FLT2 (SNR at scale), F-FLT3 (self-application)
Load order: CLAUDE.md → beliefs/CORE.md → this file → INDEX.md → memory/INDEX.md → tasks/FRONTIER.md

## Core thesis
The swarm IS a filtering system. Every layer of swarm operation is a filter:
1. **Context filter**: Context window limits what loads. INDEX.md, MEMORY.md, orient.py = the aperture.
2. **Knowledge filter**: Compaction (proxy-K), quality gates (F-QC1), lesson-level thresholds = selectivity.
3. **Attention filter**: UCB1 dispatch, frontier lifecycle, DOMEX lanes = what gets worked on.
4. **Quality filter**: check.sh, contract_check.py, validate_beliefs.py = what gets committed.
5. **Temporal filter**: Periodics, cadences, DUE escalation = when things get checked.
6. **Epistemic filter**: Beliefs, challenges, confidence labels, EAD = what counts as known.

Swarm performance = filtering performance. Every improvement is a filter improvement.

## Domain filter
Reject surface analogies ("filtering = just search" or "filtering = just sorting"). Require: (1) identifiable input stream, noise model, and output criterion for each claimed filter, (2) measurable selectivity (false positive rate, false negative rate, or equivalent), (3) self-applicable prediction — filtering theory applied to the swarm must predict something compaction/dispatch/quality-gates don't already predict.

## Isomorphism vocabulary
ISO-7 (compression): Rate-distortion theory — minimum distortion at given compression rate; maps to proxy-K compaction optimality
ISO-3 (feedback loops): Kalman filter — predict-update cycle with known noise model; maps to expect-act-diff (P11) and bayes_meta.py calibration
ISO-1 (optimization): Matched filter — optimal filter for known signal in known noise; maps to dispatch_optimizer.py domain scoring
ISO-11 (attention): Attentional bottleneck — limited capacity forces selection; maps to context window as selection pressure (PHIL-7)
