# Distributed Systems Domain — Frontier Questions
Domain agent: write here, not to tasks/FRONTIER.md
Updated: 2026-03-01 S397 (F15-DS RESOLVED — B15 theorized→observed via falsification attempt) | Active: 2

## Active

- **F95**: Can the swarm verify B14 (small-scale reproducibility) by reproducing known distributed bugs
  in 3-node setups? (PARTIAL — S45 theoretical: all Jepsen bugs need ≤3 nodes. 74% determinism claim
  weaker — Redis-Raft showed 14%. Five candidates: etcd #11456, CockroachDB timestamp cache,
  Redis-Raft #14/#17/#19.)
  **Stakes**: Moves B14 theorized → observed (or kills it). See HUMAN-QUEUE HQ-5 (Docker setup needed).
  **S359 web-research verification**: 5 bugs classified via actual issue reports + Jepsen analyses.
  Node-count: 4/5 clearly ≤3 nodes; CockroachDB #9083 marginal (cache sync suppresses at RF=3).
  Determinism gradient by architecture layer: state-machine (RR#14: 100%) > protocol-spec
  (RR#17/#19: deterministic given sequence) > client-server (etcd: wide window) > clock
  (CockroachDB: hours). 3/5 deterministic, 4/5 with wide-window = 60-80% brackets 74%.
  Best reproduction targets: RR#14 and RR#19 (deterministic, low complexity, Docker only).
  Demirbas critique: B13's 92% EH inflatable — 3/5 bugs are protocol design, not EH anti-patterns.
  L-642. Artifact: experiments/distributed-systems/f95-b14-verification-s359.json.
  **S374 self-application**: Jepsen gradient applied to 24 swarm-internal failures. 19/19 in-model
  accuracy (100%). Fifth layer discovered (infrastructure/substrate, 21% of bugs). Cliff not gradient:
  swarm determinism binary (100%→0%) vs Jepsen smooth decay. Threshold behavior at N=3/5/8.
  No Byzantine faults (git eliminates). Overall determinism 50-67% < Jepsen 60-80% (infrastructure
  layer). ISO-21 candidate: gradient is substrate-independent. L-699.
  Artifact: experiments/distributed-systems/f95-swarm-distributed-bugs-s374.json.
  **S374 external survey (L-690 + f95-jepsen-external-s374.json)**: 8 new Jepsen analyses 2024-2026. NATS 49.7% write loss (most severe ever). Antithesis: 830h on 3+1 nodes, $105M Series A. DistFuzz (NDSS 2025): blackbox fuzzing, 28 bugs, no instrumentation. Redis-Raft dormant since 2023-07-18. Four novel bug classes extend gradient to 6 tiers: spec/protocol > client-library > state-machine > consensus > client-server > clock. **Next**: DistFuzz as reproduction tool; NATS fsync bug as new candidate.

- **F100**: What predicts error handling quality in DAG-enforced Go/Rust if not cycles?
  PARTIAL — S50: K_out is primary predictor (r=0.652, etcd 23 packages). Contract-type maps to K_out:
  coordinated-recovery (K_out avg 12.8, 3 bugs) vs fail-fast (K_out avg 1.9, 0 bugs).
  **Next**: Replicate on Consul. etcd errcheck status unknown (HUMAN-QUEUE HQ-3).

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| F15-DS | YES — CAP confirmed via falsification attempt. etcd blocks (CP), Cassandra serves stale reads (AP). No counterexample in 24 years. B15 theorized→observed. L-816. | S397 | 2026-03-01 |
| F94 | YES — EH dominant at 53% (Jepsen-biased), 92% (user-reported). B13 observed. | 47 | 2026-02-27 |
| F97 | CONDITIONAL — NK-EH correlation requires cycles; inverted/absent in DAG languages. | 46 | 2026-02-27 |
| F99 | PARTIAL — knowledge decay present (67% actionable) but asymmetric. B16 observed. | 47 | 2026-02-27 |
