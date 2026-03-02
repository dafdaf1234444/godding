# Consensus Protocols Research

## FLP Impossibility (Fischer, Lynch, Paterson 1985)
In a fully asynchronous message-passing system, no deterministic algorithm solves consensus if even one process may crash.

**Exact assumptions** (all three required):
1. Asynchronous network: no bound on message delay
2. Fail-stop faults only: crashed process simply stops
3. Only one faulty process

**Does NOT apply when**: timing assumptions added (partial synchrony), randomness permitted, or termination requirement relaxed.

**Relationship to CAP**: FLP trades safety vs. liveness under async+crash. CAP trades consistency vs. availability under partition. FLP assumes reliable delivery (no partition) — a stronger result in some respects.

## Paxos (Lamport ~1989)
**Roles**: Proposers, Acceptors, Learners
**Two phases**:
1. Prepare: proposer sends Prepare(n) to quorum; acceptors promise not to accept lower-numbered proposals
2. Accept: proposer sends Accept(n, v); value chosen when quorum accepts

**Key insight**: quorum intersection guarantees at most one value chosen.
**Why hard to implement**: Multi-Paxos (stable leader, log compaction, config changes, gap recovery) is underspecified.

**Real systems**: Spanner (leader-based Paxos + TrueTime), Chubby, ZooKeeper (Zab variant)

## Raft (Ongaro & Ousterhout 2014)
Explicitly designed for understandability. Howard (2020): Raft and Multi-Paxos are more similar than assumed.

**Leader election**: only nodes with up-to-date logs can win (vs. Paxos: any node can win, then recovers)
**Log replication**: all writes through leader; committed when majority acknowledges
**Safety**: Leader Completeness Property — committed entries present in all future leaders

**Real systems**: etcd (Kubernetes), CockroachDB, Consul, TiKV, YugabyteDB

**Key tradeoff vs. Paxos**: cheaper elections, less flexible leader selection.

## BFT (Byzantine Fault Tolerance)
**CFT (Paxos/Raft)**: n ≥ 2f+1 nodes for f failures
**BFT (PBFT)**: n ≥ 3f+1 nodes for f Byzantine failures; O(n²) messages per round
**HotStuff**: reduces to O(n) messages via threshold signatures

**Use CFT when**: single administrative domain, crash failures expected
**Use BFT when**: mutually untrusting parties, adversarial model

## Practical Tradeoffs
| System | Protocol | Latency | Throughput |
|--------|----------|---------|------------|
| etcd | Raft | Low (single DC) | Moderate |
| CockroachDB | Multi-Raft | Moderate (geo) | High (parallel) |
| Spanner | Multi-Paxos | External consistency priority | High |

**Fundamental**: batching increases throughput but increases p99 latency. Not an implementation artifact.

## Falsifiable Predictions
1. Multi-Paxos needs exactly 2 RTTs to commit (stable leader, no contention) → measure via packet capture
2. Raft will not elect a leader missing committed entries → craft partition scenario, verify
3. Disk latency > election timeout causes spurious leader changes → throttle disk, measure churn
4. PBFT scales O(n²), HotStuff O(n) per round → benchmark at n=4,7,10,13

## Sources
- FLP 1985: JACM paper
- Paxos Made Simple: Lamport 2001
- Raft: raft.github.io, Ongaro & Ousterhout 2014
- Howard & Mortier 2020: "Paxos vs Raft: Have We Reached Consensus?"
- Castro & Liskov 1999: PBFT
