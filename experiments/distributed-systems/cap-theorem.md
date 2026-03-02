# CAP Theorem Research

## Formal Statement (Gilbert & Lynch 2002)
In an asynchronous network, no read/write register can simultaneously guarantee:
- **Consistency** (linearizability): reads return the most recent write
- **Availability**: every non-failing node responds to every request
- **Partition tolerance**: the system operates despite arbitrary message loss

Proof: two-node system, partition induced, client writes to G1, client reads from G2. G2 can't know about write → returns stale value → violates linearizability. QED.

## Key Clarifications
- **"Pick 2 of 3" is wrong** — Brewer himself (2012) called this "always misleading"
- **Partition tolerance is not optional** — any networked system can partition
- **CAP-C ≠ ACID-C** — CAP means linearizability, not application invariants
- **CAP says nothing about latency** — PACELC (Abadi 2012) adds the E→L|C dimension
- **Systems can't be cleanly classified CP/AP** — Kleppmann (2015): "one bit cannot capture these nuances"

## PACELC Extension (Abadi 2012)
During Partition: choose A or C. Else (normal): choose L or C.
- PA/EL: DynamoDB (default), Cassandra, Riak — available during partition, low latency normally
- PC/EC: Spanner, CockroachDB, etcd — consistent always, accept latency cost

## Real Systems
| System | CAP claim | Reality | PACELC |
|--------|-----------|---------|--------|
| Spanner | CP | CP, but >5-9s availability via private network | PC/EC |
| DynamoDB | AP | Default AP, strong-consistent reads are CP | PA/EL |
| Cassandra | AP | Tunable — quorum settings approach CP | PA/EL |
| MongoDB | CP | Non-linearizable reads at some settings (Kleppmann) | Depends on config |
| etcd | CP | Clean for KV ops (Jepsen); client bugs possible | PC/EC |

## Falsifiable Predictions
1. No system can demonstrate linearizability + availability during a partition → operationalized by Jepsen
2. Weaker consistency models (causal, eventual) escape CAP → CRDTs prove this constructively
3. Spanner would lose availability during partition on commodity network → untested but predicted

## Sources
- Gilbert & Lynch 2002: formal proof
- Brewer 2012: "CAP Twelve Years Later" (self-correction)
- Kleppmann 2015: "Please stop calling databases CP or AP"
- Abadi 2012: PACELC extension
- Brewer 2017: "Spanner, TrueTime and the CAP Theorem"
