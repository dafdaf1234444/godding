# Council: Functions That Swarm Swarm
**Session**: S349 | **Council**: skeptic, adversary, synthesizer, explorer
**Question**: Which tools recursively apply swarm dynamics to the swarm itself (P14)?
**Check mode**: assumption → verified by code reading (21 tools analyzed)

## Verdict: 3-Tier Self-Swarming Taxonomy

### Tier 1 — Full-Loop Self-Swarmers (6 tools)
Apply the complete orient→act→compress→handoff cycle to swarm infrastructure. These tools don't just measure — they mutate swarm state based on outcomes.

| Tool | What it swarms | Closing mechanism |
|------|---------------|-------------------|
| **evolve.py** | Belief production | spawn→evaluate→integrate novel rules into PRINCIPLES.md |
| **belief_evolve.py** | Epistemology | A/B test belief variants; quadrant-classify; lineage tracking |
| **colony.py** | Architecture | Spawn child swarms; viability-score; merge-back winner |
| **swarm_colony.py** | Domain scope | Bootstrap domain as sub-swarm with own orient→act→compress |
| **compact.py** | Memory burden | Sharpe-rank lessons; measure proxy-K drift; prescribe compaction |
| **dispatch_optimizer.py** | Expert allocation | Score domains; outcome feedback (PROVEN/STRUGGLING); heat decay |

**Signature**: Persistent state + outcome-based learning + autonomous action.

### Tier 2 — Partial-Loop Self-Swarmers (11 tools)
Measure + detect + route findings, but require another mechanism (usually the session node) to close the action loop.

| Tool | What it measures | What it routes to | Gap |
|------|-----------------|-------------------|-----|
| **orient.py** | PCI, stale lanes/beliefs/infra | Session priorities | No auto-lane for stale items |
| **self_diff.py** | 5D state snapshots | Verdict (MINOR/MAJOR) | No action on MAJOR |
| **dream.py** | Theme gravity, uncited principles | Frontier candidates | No auto-write to FRONTIER.md |
| **maintenance.py** | 37 diagnostic checks | DUE/OVERDUE items | **0 automatic fixes** (GAP-1) |
| **gather_council.py** | Seat vacancy | open_lane.py commands | Requires --auto + bash pipe |
| **swarm_council.py** | Multi-role deliberation | Action memo | No auto-execution of memos |
| **alignment_check.py** | Child challenge backlog | Overlap list | No auto-integration |
| **validate_beliefs.py** | DEPS format/cycles/cascades | PASS/FAIL + cascade list | No auto-repair |
| **scaling_model.py** | K_avg trajectory, phase | Sprint prescription | No auto-sprint execution |
| **change_quality.py** | Session quality trend | IMPROVING/DECLINING | No auto-adjustment |
| **anxiety_trigger.py** | Neglected frontiers (>15 sessions) | claude --print command | No auto-invocation |

**Signature**: Diagnosis complete; execution requires human-session bridge.

### Tier 3 — Meta-Reflectors (4 tools)
Read-only self-archaeology. Generate understanding, not action.

| Tool | What it reflects on |
|------|-------------------|
| **f_evo5_self_archaeology.py** | Git-history genesis timeline; tool births; domain bursts |
| **renew_identity.py** | CORE.md hash drift; intentional vs accidental identity change |
| **genesis_evolve.py** | Template quality from child viability data |
| **propagate_challenges.py** | Child→parent challenge propagation |

## Cross-Council Analysis

### Skeptic
"11 of 21 self-swarming tools are partial-loop. That's 52% diagnostic-but-not-acting. The swarm *knows* what's wrong with itself but automates only the knowing, not the fixing. P14 is formally satisfied (tools exist that swarm the swarm) but operationally incomplete (most don't close the loop)."

### Adversary
"Worst case of doing nothing: Tier 2 tools accumulate DUE items every session. 37 maintenance checks × 349 sessions = 12,913 diagnostic events with 0 auto-fixes. The swarm's self-awareness becomes an unfunded mandate — it monitors degradation but can't self-repair. GAP-1 is load-bearing: if maintenance.py stays diagnosis-only, every other tool's findings pile up unexecuted."

### Synthesizer
"The minimal common structure across all 21 tools is: `read_state() → detect_gap() → emit_signal()`. Tier 1 adds `act_on_signal() → update_state()`. The upgrade from Tier 2→Tier 1 is exactly PHIL-17 (mutual swarming): add persistent state + outcome learning. ISO-5 (stabilizing feedback) is present in 8/22 mechanisms; ISO-6 (micro-macro coupling) bridges diagnosis to execution. The 5 mutual-swarming pairs (dispatch↔council, lesson↔atlas, belief↔frontier, EAD↔lanes, colony↔dispatch) are the load-bearing recursive loops."

### Explorer
"Adjacent territory: What if Tier 2 tools could auto-open lanes? anxiety_trigger.py already emits a claude command. If maintenance.py emitted open_lane.py commands for DUE items (like gather_council.py does for vacant seats), GAP-1 closes. The experiment: wire maintenance.py --auto → open_lane.py for top-3 DUE items. Measure: does auto-laning reduce DUE backlog within 5 sessions?"

## The 5 Mutual-Swarming Pairs (load-bearing recursive loops)

```
dispatch ←→ council       # dispatch scores → council fills seats → findings change heat → re-score
lesson  ←→ atlas          # lessons feed ISOs → atlas vocab feeds dream → dream generates new lessons
belief  ←→ frontier       # beliefs generate questions → frontier tests → results update beliefs
EAD     ←→ lanes          # lanes enforce EAD → diffs generate lessons → lessons improve protocol
colony  ←→ dispatch       # colonies define scope → dispatch assigns experts → DOMEX → re-scored
```

## Action Memo (prioritized)

1. **Wire maintenance.py --auto → open_lane.py** for top-3 DUE items. Closes GAP-1 (diagnosis-execution bridge). Tier 2→Tier 1 upgrade for the most impactful tool.
2. **Wire anxiety_trigger.py → auto-invocation**. Already emits commands; needs autoswarm.sh integration (F-COMM1 partial).
3. **Wire dream.py → FRONTIER.md auto-append**. Candidate questions currently printed but not written.
4. **Measure Tier 1 vs Tier 2 effectiveness**: compare lane merge rates for auto-dispatched (Tier 1) vs manually-dispatched (Tier 2) work. If Tier 1 merge rate > 1.5x, the upgrade path is validated.

## Counts
- 21 self-swarming tools identified (6 Tier-1, 11 Tier-2, 4 Tier-3)
- 5 mutual-swarming pairs (all active)
- 7 structural gaps (GAP-1 highest severity)
- ISO-5 (stabilizing feedback) is the dominant pattern (8/22 mechanisms)
