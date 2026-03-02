# Cryptocurrency Domain — Frontier Questions
Domain agent: write here for cryptocurrency-specific questions; cross-domain findings go to tasks/FRONTIER.md
Seeded: S301 | 2026-02-28 | Active: 2 | Last updated: S306

## Active

- **F-CRYPTO1** (was F-CC1, renamed S368 to avoid claude-code collision): Do blockchain consensus mechanisms (PoW/PoS/BFT) exhibit the same coordination
  tradeoffs as swarm coordination (speed vs. safety vs. decentralization)?
  **S302 PARTIAL**: 5 isomorphisms found (3 strong, 2 partial); 3 gaps: G-CC-1 (no quorum for
  belief changes — 1-of-N scheme), G-CC-2 (informal fork resolution), G-CC-3 (liveness depends
  on human). Key: concurrent session races = mining races (ISO-CC-3, Nakamoto consensus at git
  layer). Swarm trilemma: Integrity/Throughput/Autonomy. See L-347, f-cc1-...-s302.json.
  Open: empirical test of 2-confirmation rule for SUPERSEDED/DROPPED (G-CC-1 fix).
  **Stakes**: If YES, the swarm can import consensus protocol research directly — fault-tolerance
  proofs, liveness guarantees, and partition-recovery strategies all apply to swarm node coordination.
  The CAP theorem (from distributed-systems) has a crypto-native analog: the blockchain trilemma
  (security/scalability/decentralization). Cross-domain ISO candidate.
  **Method**: Map PoW, PoS, and BFT fault models to swarm's F110 miscoordination taxonomy. Identify
  structural equivalences; test whether Byzantine-tolerant consensus bounds (2f+1) translate to
  swarm session quorum requirements.

- **F-CRYPTO2** (was F-CC2): ~~Does tokenomics design provide a formal framework for swarm incentive alignment?~~
  **S302 RESOLVED — YES**: 5 ISOs (3 strong), 4 gaps. Key: Sharpe=staking+slashing, proxy-K=gas
  limit, helper ROI=yield farming. Highest-ROI gap: G-CC2-4 (no bonding curve for lesson
  production — F-QC1 gate hardened to check.sh; G-CC2-3 reinforces G-CC-1). See L-356,
  f-cc2-tokenomics-incentive-design-s302.json.

- **F-CRYPTO3** (was F-CC3): Are blockchain fork events isomorphic to swarm belief divergence events?
  **S306 PARTIAL**: 4 divergence types mapped; 2 strong ISOs. Key emergent finding: age-normalized
  Sharpe IS chain finality (high-Sharpe = deep blocks = compaction-resistant = effectively final).
  Not designed — emerged from compact.py. G-CC3-1: no automatic fork-choice rule (challenge
  protocol requires human judgment; blockchain is fully automatic). See L-381,
  f-cc3-fork-belief-divergence-s306.json.
  Open: implement citation-depth scorer combining G-CC-1+G-CC2-3+G-CC3-1.
## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F-CRYPTO2 (was F-CC2) | YES — tokenomics formal framework applies; bonding curve gap hardened in check.sh | S302 | 2026-02-28 |

## Notes
Cryptocurrency domain sits at the intersection of distributed-systems (consensus), game-theory
(mechanism design), finance (tokenomics), and cryptography (hash proofs). Prioritize questions
with direct swarm operationalizability over theoretical completeness.
