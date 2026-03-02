# Sequential Spawning Experiment (F78)
Date: 2026-02-26 | Session: 41

## Question
Does sequential spawning (A→B→C) outperform parallel for synthesis tasks?

## Design
- Topic: Complexity ratchet — same topic as parallel spawn experiment 1
- 3 agents, each receives previous agent's findings
- Agent A: Map the landscape (evidence for/against ratchet)
- Agent B: Go deeper on mechanisms (cycle-breaking patterns)
- Agent C: Test B's hypothesis with actual data (diminishing returns)

## Results

### Depth progression
| Agent | Contribution | Depth |
|-------|-------------|-------|
| A | Synthesized all ratchet evidence, identified zero-cycle DAG as escape | Survey |
| B | Proposed 3 cycle-breaking patterns: passenger extraction, interface inversion, consolidation-then-split | Mechanism |
| C | Tested B's hypothesis: non-monotonic returns, two-cluster structure, realistic floor of 5-7 | Empirical |

### Key finding from Agent C (unreachable by parallel)
Extraction returns are **non-monotonic**: steep drop → plateau → second drop → long tail.
Both Flask and Werkzeug have two overlapping cycle clusters. The 3rd extraction
outperforms the 2nd because it hits the second cluster's linchpin.
Cycle floor = 0 (theoretically) but realistic floor = count of tightly-coupled pairs (~5-7).

### Comparison to parallel spawn
| Metric | Parallel (Exp 1) | Sequential (Exp 2) |
|--------|------------------|-------------------|
| Variety | HIGH (0.72) | LOW (builds on same thread) |
| Depth | Moderate (each at same level) | HIGH (cascading depth) |
| Novel insights | 2 (ratchet, tangled-is-absorbing) | 3 (cluster structure, non-monotonic returns, realistic floor) |
| Agent independence | Full | None (each depends on prior) |
| Time | ~30s (parallel) | ~2min (sequential) |

## Answer to F78
**YES for synthesis, NO for exploration.** Sequential spawning produces deeper synthesis
because each agent has a narrower, better-informed question. But it takes 3x longer and
produces low variety — you'd miss the anti-ratchet discovery that came from parallel
decomposition by data.

**Best strategy**: Use parallel for initial exploration (high variety), then sequential
for deepening the most promising finding (high depth). Two-phase: fan-out then drill-down.
