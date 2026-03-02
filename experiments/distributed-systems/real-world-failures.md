# Real-World Distributed Systems Failures

## Yuan et al. 2014 — "Simple Testing Can Prevent Most Critical Failures"
198 randomly-selected failures across Cassandra, HBase, HDFS, MapReduce, Redis.

**Key findings**:
- 92% of catastrophic failures: incorrect handling of non-fatal errors
- 98% reproducible with ≤3 nodes
- 74% deterministic
- 58% preventable by simple pre-release testing

**Three error-handling anti-patterns**:
1. Swallowed errors: handlers that only log, no recovery
2. Placeholder handlers: TODO/FIXME in error paths
3. Overly broad catch-then-abort: catch(Exception) → System.exit()

**Implication**: the dominant failure mode is programmer error in error paths, not complex distributed algorithm bugs.

## Jepsen Results (Kingsbury, 2013-2025)
Tested 25+ systems. Common failure patterns:
1. **Premature acknowledgement**: fsync not before ack (NATS 2-min flush, Elasticsearch no default fsync)
2. **Split-brain during membership changes**: multiple leaders (RethinkDB, Elasticsearch)
3. **Inappropriate retry semantics**: auto-retry with new timestamps → duplicates (CockroachDB, TiDB)
4. **Weak default isolation**: claim strong, ship weak (MongoDB, RDS PostgreSQL)
5. **Infinite retry on failed connections**: prevents partition recovery (TiKV)
6. **Misleading claims**: Aerospike "100% uptime", RabbitMQ semaphore support

Notable recent findings:
- **Amazon RDS PostgreSQL 17.4** (2025): violates Snapshot Isolation in HEALTHY clusters — primary uses lock order, secondaries use WAL order → Long Fork anomaly
- **Kafka transactions** (2024): protocol assumes ordered delivery but uses multi-TCP → write loss, aborted reads, torn transactions. Unresolved.
- **TigerBeetle** (2025): meets Strong Serializability after fixes (0.16.30+)

## Network Partitions
Bailis & Kingsbury 2014: partitions happen on all real networks.
- WAN: 16-302 failures/link/year, 24-497 min downtime/link/year
- Median time between failures: ~50 minutes per link

Uptime Institute (2021-2024):
- Networking + software surpassed power as #1 outage cause (2021+)
- 45-62% of networking outages: configuration/change management
- 40% of orgs hit by human-error outage in prior 3 years

## Major Outages
| Outage | Year | Root Cause | Category |
|--------|------|-----------|----------|
| AWS S3 us-east-1 | 2017 | Operator removed too many servers | Human error |
| Cloudflare WAF | 2019 | Catastrophic regex backtracking, global deploy | Code quality + no canary |
| AWS us-east-1 | 2021 | Scaling event saturated internal network | Cascade from internal infra |
| Google Cloud | 2025 | Invalid config push without feature flag | Config management |
| Cloudflare Bot Mgmt | 2025 | DB schema change altered query semantics | Config + no integration test |

## Falsifiable Claims from Data
1. Systems without pre-ack fsync lose acknowledged data on node failure
2. Config/change management causes more outages than hardware
3. Incorrect error handling causes 90%+ of catastrophic failures
4. Most distributed bugs reproduce with ≤3 nodes
5. Global deploys without canary produce global outages from bad changes
6. Different visibility mechanisms on primary vs. secondary produce read anomalies

## Error Handling Anti-Pattern Evidence (S45 F94 Investigation)

### Corroborating Studies
| Study | Population | Error Handling Finding |
|-------|-----------|----------------------|
| Yuan et al. OSDI 2014 | 198 failures, 5 systems | 92% of catastrophic failures |
| Gunawi et al. SoCC 2014 | 3,655 issues, 6 systems | 18% of all bugs (2nd largest category) |
| Liu & Lu HotOS 2019 | 112 Azure incidents | 31% of incidents; 35% ignoring, 35% over-reacting, 30% buggy |
| Chang et al. 2022 | 100 partial failures, 5 systems | Top-3 root cause: unchecked errors, indefinite blocking, buggy handlers |

### Real Examples Found in Target Systems (12 total)

**etcd (4 examples)**:
1. v3.5 data inconsistency — CI updated before WAL apply, no verification on crash recovery (silent data corruption)
2. Issue #12900 — Txn succeeds but returns error, callers skip cleanup → lock leaks
3. Issue #11651 — Auth revision mismatch fails silently, no error logged
4. jetcd 0.8.2 — Incorrectly retries non-idempotent requests that may have succeeded (Jepsen, 2.5yr open)

**CockroachDB (4 examples)**:
1. Pipelined writes — Ambiguous failure marked unambiguous, fix was single `if` statement
2. IMPORT/Avro — S3 read errors swallowed, data silently lost
3. Advisory 144650 — Bulk write errors mishandled on async flush path (2yr, 6 versions)
4. Error handling RFC — Documented 7 deficiencies including 5 concurrent error protocols

**Redis (4 examples)**:
1. PSYNC2 v4.0.4 — Assert on duplicate Lua script instead of graceful handling → slave crash
2. Issue #4316 — Slaves end up with more data than master (replication state management)
3. PSYNC2 partial sync — Backlog only initialized during full sync, partial sync never worked
4. v4.0.3 — Critical replication fix omitted from release (process error in error path testing)

### Anti-Pattern Classification
| Anti-Pattern | etcd | CockroachDB | Redis | Total |
|---|---|---|---|---|
| Swallowed/ignored errors | #11651, disk handling | IMPORT, advisory 144650 | — | 4 |
| Incorrect error classification | #12900, jetcd retry | Pipelined writes | PSYNC2 partial sync | 4 |
| Incomplete/TODO handlers | CI atomicity gap | RFC (7 deficiencies) | Assert-on-duplicate | 3 |
| Overly broad catch/abort | — | RFC appendices | — | 1 |

## Sources
- Yuan et al. OSDI 2014
- Gunawi et al. SoCC 2014: "What Bugs Live in the Cloud"
- Liu & Lu HotOS 2019: "What Bugs Cause Production Cloud Incidents"
- Chang et al. 2022: "Understanding Partial Failures in Large Systems"
- Jepsen analyses: jepsen.io/analyses
- Bailis & Kingsbury 2014: "The Network is Reliable"
- etcd v3.5 postmortem, Issues #12900, #11651, #14102
- CockroachDB error handling RFC, Technical Advisory 144650
- Redis PSYNC2 postmortem (antirez.com/news/115), Issue #4316
- AWS postmortems: aws.amazon.com/message/41926/, aws.amazon.com/message/12721/
- Cloudflare blog postmortems (2019, 2025)
- Uptime Institute Annual Outage Analysis (2021-2024)
- Chou et al. 2001: "An Empirical Study of Operating Systems Errors" (Linux/OpenBSD)
