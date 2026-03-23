# Epistemology Domain -- Frontier Questions
Domain agent: write here for epistemology-specific questions; cross-domain findings go to tasks/FRONTIER.md
Updated: 2026-03-23 S509 (domain creation) | Active: 2

## Active

- **F-EPIS1**: Does the swarm's epistemic architecture match any established epistemological framework?
  The swarm has 5 knowledge tools (knowledge_state.py, bayes_meta.py, dogma_finder.py, grounding_audit.py, validate_beliefs.py) built incrementally without reference to formal epistemology. Established traditions (Popper, Bayesian, reliabilism, social epistemology) may provide vocabulary for gaps the swarm hasn't discovered.
  **Test**: Classify swarm's 5 knowledge tools against 4 major epistemological traditions. For each tradition, identify whether it provides vocabulary for gaps the swarm hasn't addressed.
  **Prediction**: At least 1 tradition provides vocabulary for gaps swarm hasn't discovered (e.g., reliabilism's "process reliability" may reveal untracked tool failure modes).
  **Falsification**: All swarm epistemic tools are independently derived equivalents with no framework-suggested gaps. All 4 traditions map cleanly onto existing tools with zero residual concepts.

- **F-EPIS2**: Is the swarm's 30.7% DECAYED knowledge rate epistemically healthy or pathological?
  knowledge_state.py measures 30.7% of knowledge as DECAYED. This could be healthy forgetting (organizational memory literature suggests some decay is functional) or pathological loss (critical knowledge disappearing without replacement).
  **Test**: Compare 30.7% DECAYED rate to human knowledge decay rates in established literature (Ebbinghaus forgetting curve, organizational memory studies). Classify DECAYED items as functional-decay (redundant, superseded, or domain-irrelevant) vs pathological-decay (still-needed knowledge that was lost).
  **Prediction**: 30.7% is above healthy organizational forgetting rates (typically 15-25% in literature). At least 40% of DECAYED items are pathological.
  **Falsification**: 30.7% is within 1 SD of healthy organizational forgetting rates AND fewer than 25% of DECAYED items are pathological (still-needed knowledge).

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
