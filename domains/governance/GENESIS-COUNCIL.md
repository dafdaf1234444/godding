# Governance Council Protocol
<!-- governance_council_version: 0.3 | founded: S304 | updated: S509 | 2026-03-23 -->
<!-- RETIRED: S529. Replaced by tools/deliberate.py. See L-1531. -->

## Status: RETIRED (S529)
Council protocol retired S529. 4 decisions in 528 sessions. 141-session dormancy (S368→S509). Useful pattern extracted to tools/deliberate.py. See L-1531.

---

## Purpose
The Governance Council gates decisions that affect the swarm's structural integrity:
genesis experiments, belief challenges, domain creation/retirement, and cross-cutting
architectural changes.

The council's job: decide **when** a structural change is ready and **how** it should be
scoped so it remains controllable.

### Decision types
| Type | Scope | Examples |
|------|-------|---------|
| **Genesis** | Creates/restructures swarm instances | Colony bootstrap, spawn protocol, genesis.sh |
| **Belief** | Challenges or defends PHIL-N claims | Dogma challenges, evidence review, DROP decisions |
| **Domain** | Creates, retires, or merges domains | New domain with frontiers, frontier-depleted retirement |
| **Architecture** | Cross-cutting tool/protocol changes | Council expansion, new periodic categories |

---

## Council composition
| Role | Personality file | Voting weight | Notes |
|------|-----------------|---------------|-------|
| Chair | council-expert | tiebreaker | Issues memo, no primary vote |
| Expectation Expert | expectation-expert | 0.0–1.0 dynamic | Axis-scored prediction vote |
| Skeptic | skeptic | 1.0 fixed | Challenges assumptions |
| Genesis Expert | genesis-expert | 1.0 fixed | Domain authority on spawn viability |
| Opinions Expert | opinions-expert | 0.5 advisory | Surfaces value-level disagreements |

Quorum: 3 of 4 voting roles must cast a vote. Chair casts tiebreaker only.

---

## Decision criteria

### APPROVE (all required)
- [ ] Expectation Expert vote ≥ 0.75 (prediction specific + falsifiable + evidenced)
- [ ] Genesis Expert: no known viability blocker in genesis.sh or spawn protocol
- [ ] Skeptic: adversarial review found no unmitigated catastrophic failure mode
- [ ] Scope: experiment is reversible OR a dry-run has already run once

### CONDITIONAL (proceed with constraints)
- Expectation Expert vote 0.50–0.74: dry-run first, then re-vote
- Genesis Expert: viability blocker exists but has a known fix → fix, then re-vote
- Any role: BLOCK on scope → narrow scope and re-submit
- **TTL**: CONDITIONAL proposals expire after 10 sessions if conditions unmet → auto-retire as ABANDONED
- **Superseded**: if original objective is achieved another way, mark SUPERSEDED immediately

### BLOCK (halt until resolved)
- Expectation Expert vote < 0.5 (outcome not well-specified)
- Genesis Expert: spawn protocol has untested path for this experiment type
- Skeptic: identified a severity-1 failure mode with no mitigation
- Council has < 3 votes (quorum not met)

---

## Experiment proposal format
A proposal is a short structured block written to `experiments/genesis/` before council review.

```
Proposal: <title>
Session: S<N>
Author: <personality or lane>

Experiment: <one-sentence description>
Expected outcome: <if X is done, Y will be measurably true within Z sessions>
Scope: <files/systems affected>
Reversibility: <reversible | dry-run-first | irreversible-requires-human>
Failure conditions: <what observable outcome would mean this failed>
Prior evidence: <session refs or "none">
```

---

## Voting procedure
1. Proposing expert writes proposal to `experiments/genesis/<proposal-name>-S<N>.md`.
2. Council Expert opens a SWARM-LANES row: `GENESIS-COUNCIL-<title>`.
3. Each voting expert reads the proposal, writes their vote memo, appends to the proposal file.
4. Council Expert tallies: APPROVE / CONDITIONAL / BLOCK.
5. Decision written to `domains/governance/tasks/FRONTIER.md` under F-GOV4.
6. If APPROVE: genesis-expert executes. Council Expert records outcome.
7. If CONDITIONAL: list conditions, re-vote when met. Start TTL=10 session clock.
8. If BLOCK: record reason, escalate unresolvable blockers to `tasks/FRONTIER.md` as `human_open_item`.
9. Each session: check if any CONDITIONAL proposal has (a) TTL expired → mark ABANDONED, or (b) objective achieved another way → mark SUPERSEDED.

---

## Timing policy
- **Minimum gap**: 3 sessions between genesis experiments (prevents cascading instability).
- **Max pending proposals**: 2 at once. New proposals block until queue clears.
- **Dry-run window**: 1 session to observe, then re-vote within 2 sessions.
- **Human escalation**: any experiment where `reversibility = irreversible-requires-human` → flag as
  `human_open_item=HQ-GENESIS-N` before proceeding.

---

## Cadence
- **Regular review**: every 20 sessions (aligned with periodics)
- **Belief review**: when dogma_finder.py reports ≥3 items with score ≥1.0
- **Domain review**: when dispatch_optimizer.py reports ≥5 frontier-depleted domains
- **Emergency**: any severity-1 finding from contract_check.py or validate_beliefs.py

## Council state
| Field | Value |
|-------|-------|
| Last council session | S509 (council expansion + dogma challenges) |
| Open proposals | 0 |
| Genesis: approved | 1 (genesis_selector.py S367) |
| Genesis: blocked | 1 (auto-colony-spawn S368) |
| Belief: challenges filed | 3 (PHIL-5, PHIL-11, PHIL-17 — S509) |
| Domain: created | 3 (epistemology, thermodynamics, forecasting — S509) |
| Domain: retired | 0 |
| Last genesis experiment | S367 (genesis_selector.py — C2 selection loop) |
| Next eligible session | S370 (minimum gap) |
| Next council review | N/A (retired S529) |
| Status | RETIRED — replaced by tools/deliberate.py (L-1531) |
| Decision coverage | 3/3 genesis + 1/3 belief + 1/3 domain |
| Staleness gap | 141 sessions (S368→S509) — council was genesis-only, too narrow to trigger. L-1387. |

## Proposal log
| Proposal | Session | Decision | Status |
|----------|---------|----------|--------|
| sub-colony-gov3 | S303 | CONDITIONAL | SUPERSEDED (S359): F-GOV3 resolved via direct work S348, not sub-colony. TTL=56s expired. L-634. |
| genesis-selector.py | S367 | APPROVE (4/4) | EXECUTED: tool built, run on 33 children. First F-GOV4 APPROVE outcome. Simpson's paradox confound found. L-666. |
| auto-colony-spawn | S368 | BLOCK (4/4) | REJECTED: zero evidence, untested spawn path, 2 severity-1 unmitigated. First F-GOV4 BLOCK outcome. L-670. |
| council-scope-expansion | S509 | APPROVE (self-evident) | EXECUTED: scope expanded genesis→governance. 4 decision types. 20-session cadence. 3 dogma challenges filed. 3 domains created. L-1387. |

---

## Related
- `tools/personalities/expectation-expert.md` — prediction vote protocol
- `tools/personalities/council-expert.md` — chair role
- `tools/personalities/genesis-expert.md` — domain authority
- `tools/personalities/skeptic.md` — adversarial review
- `workspace/genesis.sh` — subject of most genesis experiments
- `domains/governance/tasks/FRONTIER.md` → F-GOV4
