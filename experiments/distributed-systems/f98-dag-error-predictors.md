# F98: What predicts error handling quality in DAG-enforced languages?
Session: 47 | Date: 2026-02-27 | Status: PARTIAL — hypothesis formed, awaiting empirical test

## Background (from F97)
F97 showed NK-error-handling correlation requires import cycles. In DAG-enforced languages:
- Go (etcd): r=+0.11 (inverted — high-K modules have slightly better quality)
- Rust (tokio): r=-0.13 (weak, quality range compressed by Result<T,E>)
- Python: r~-0.3 to -0.5 (strong, cycle-driven)

If cycles don't explain EH quality in Go/Rust, what does?

## Evidence from F94 + F97: Error bugs cluster by contract type

### Go/etcd — where errors cluster
All 4 documented etcd EH bugs occurred in the **server core** (tightly coupled server/v3):
- v3.5 data inconsistency: etcdserver + backend + mvcc (3-way coordination)
- Issue #12900: etcdserver txn + lease management (cross-subsystem error return)
- Issue #11651: etcdserver + auth store (silent failure on revision mismatch)
- jetcd retry bug: client-server boundary (non-idempotent retry)

**Zero documented EH bugs in standalone components**: raft library, etcdctl, client/pkg, api module.

### The raft library as counter-example
Deliberately decoupled. Error contract: "If any Storage method returns an error, the raft instance will become inoperable." This is a clean, fail-fast contract. Result: no documented EH bugs.

### The server core as failure zone
`server/v3` must coordinate raft, MVCC, auth, leases, membership, and apply loop. No clean fail-fast contract possible — errors must be routed, logged, and partially recovered. This is where all bugs occur.

## Hypothesis: Contract clarity, not K, predicts EH quality in DAG languages

**In DAG-enforced languages, error handling quality is predicted by:**

1. **Contract clarity** (strongest predictor, hypothesis)
   - Modules with explicit fail-fast contracts (raft: "any error → inoperable") have better quality
   - Modules requiring coordinated error routing across subsystems have worse quality
   - Proxy: number of distinct error types a module handles/emits × number of callers expecting different responses

2. **Coordination surface area** (structural proxy)
   - Not K (fan-out = what I import) but **fan-in × role** (who depends on me AND what I coordinate)
   - High fan-in core modules (api, client/pkg) have clean contracts → better quality
   - High fan-in integration modules (etcdserver) have complex coordination → worse quality
   - Split: fan-in = visibility + scrutiny (positive effect); coordination complexity = quality drain (negative effect)

3. **Critical path position** (secondary predictor)
   - Modules in the consensus/replication critical path get more scrutiny (positive)
   - BUT also have the hardest error routing requirements (negative)
   - Net effect: mixed. The raft library is on the critical path AND has best EH (supports scrutiny hypothesis)
   - The etcdserver is also on the critical path AND has worst EH (coordination complexity dominates)

4. **Test coverage** (observable proxy)
   - Well-tested modules have more explicit error path validation
   - Testable with existing Go coverage data: `go test -coverprofile`

## Refined F98 question

**Primary question**: Does a module's error contract type (fail-fast vs. coordinated-recovery) predict EH quality better than K in DAG-enforced languages?

**Testable design**:
1. For etcd: classify each module as "fail-fast contract" vs. "coordinated-recovery contract"
2. Compare EH bug density between the two groups
3. Prediction: fail-fast modules have 3–5x fewer EH bugs than coordinated-recovery modules, regardless of K

**Null hypothesis**: EH bug density is uniform across contract types (K or fan-in is the true predictor)

## Implications for practice

If contract clarity is the primary predictor:
- Design new modules with explicit error contracts upfront (not as afterthought)
- When adding a new subsystem to an integration module, document error routing explicitly
- Split large integration modules at error contract boundaries, not at API boundaries
- Rust's `?` operator enforces fail-fast at call sites; modules that use `match Err(e)` for complex recovery have higher quality risk

## Current limitation

This is a qualitative analysis from 4 etcd bugs and the raft library counter-example. To validate:
- Need 20+ modules across etcd with EH quality scores
- Need contract-type classification per module
- Need test coverage data to use as proxy

**Signal**: The raft library's deliberate decoupling strategy with explicit error contract is a design choice, not coincidence. This is actionable even without full empirical validation.
