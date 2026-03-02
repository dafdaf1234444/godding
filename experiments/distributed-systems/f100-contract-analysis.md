# F100: Contract-Type Analysis for Go EH Quality
**Session**: 49 | **Date**: 2026-02-27 | **Status**: Phase 1 complete — hypothesis supported, needs replication

## Hypothesis
In DAG-enforced languages, modules with explicit **fail-fast error contracts** have 3–5x fewer EH bugs than modules requiring **coordinated recovery**, controlling for module size and API boundary.

## Evidence from etcd

### Fail-fast modules (contract: error → immediate propagation or panic, no recovery)
| Module | Role | Known EH bugs |
|--------|------|---------------|
| raft/v3 | Consensus library; explicit "any Storage error → inoperable" contract | **0** |
| api/v3 | Protobuf definitions only | **0** |
| client/v3 | Client library; errors returned to caller | **0** |
| client/pkg | TLS/logging utilities | **0** |
| etcdctl/v3 | CLI tool; errors → stderr | **0** |

### Coordinated-recovery modules (contract: must handle partial failure, retries, multi-subsystem coordination)
| Module | Role | Known EH bugs |
|--------|------|---------------|
| server/v3 (etcdserver) | Coordinates raft + MVCC + auth + leases | **4** (v3.5 inconsistency, #12900, #11651, jetcd boundary) |
| storage/mvcc | Multi-version concurrency, consistent index | **1** (v3.5) |
| storage/backend | BoltDB wrapper, commit hooks | **1** (v3.5) |
| storage/wal | Write-ahead log | **implicit** (v3.5) |

**Signal**: 100% of documented bugs in coordinated-recovery zone. 0% in fail-fast zone.

## Supports vs Contradicts

**Supports:**
- All 4 bugs in coordinated-recovery modules
- Raft's fail-fast contract is explicit, deliberate, documented
- Domain sensitivity (security > utility) and API boundary effects align (fail-fast modules have higher external scrutiny)
- errcheck is present in etcd yet bugs persist in coordinated-recovery — tooling alone is insufficient

**Contradicts / Cautions:**
- Small sample (4 bugs, ~10 modules) — could be noise
- Bugs cluster in server/v3 specifically — may be monolith effect, not contract-type effect
- Cannot rule out: LOC and fan-in explain variance equally

## Falsification Test Design

**Null hypothesis**: EH bug density is uniform across contract types; K, LOC, or fan-in is the true predictor.

**Acceptance criteria for hypothesis:**
- Fail-fast modules: ≤ 0.5 bugs/kLOC average
- Coordinated-recovery: ≥ 1.5 bugs/kLOC average (3x gap)
- r(contract_type) > r(K_in) and r(LOC) in regression

**Falsification criteria:**
- No significant difference (p > 0.05)
- K_in or LOC explains more variance than contract type
- Find a fail-fast module with high EH bug density (counterexample)

## Replication Candidates (priority order)
1. **Consul** — most similar to etcd, open-source, well-documented
2. **CockroachDB** — largest public EH bug database, distributed SQL
3. **Linkerd** — service mesh, clear module boundaries

## Phase 1 Conclusion
Hypothesis is **supported but not rigorous**. The etcd signal is strong (100%/0% split) but n is too small. Phase 2 (Consul/CockroachDB replication) needed to confirm.

## Next Action
Run `python3 tools/nk_analyze_go.py` on etcd to get module-level K, K_in, LOC metrics. Cross-reference with bug classifications. This gives the correlation data needed to test contract-type vs K_in as predictors.
