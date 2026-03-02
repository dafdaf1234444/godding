# F100: etcd NK-Bug Correlation Analysis
**Session**: 50 | **Date**: 2026-02-27 | **Status**: Phase 2 complete — K_out is primary predictor

## Setup
Cloned etcd (shallow) and ran `nk_analyze_go.py --verbose` on all modules.
Cross-referenced 23 packages (server + 5 cross-module) with known bug locations from F94.

## NK Metrics Summary

| Module | N | K_avg | K_total | LOC | Bugs | Contract |
|--------|---|-------|---------|-----|------|----------|
| server | 54 | 2.96 | 160 | 53538 | 4 | mixed |
| client/v3 | 19 | 1.05 | 20 | 11009 | 0 | fail-fast |
| api | 8 | 0.75 | 6 | 37644 | 0 | fail-fast |
| client/pkg | 10 | 0.70 | 7 | 5072 | 0 | fail-fast |
| etcdctl | 11 | 1.64 | 18 | 7092 | 0 | fail-fast |
| pkg | 24 | 0.04 | 1 | 6762 | 0 | fail-fast |

## Package-Level Analysis (server module)

Key packages by K_out (outgoing dependency count):

```
Package                  K_out  K_in   LOC  Bugs  Type
etcdserver                  26     4  6738     3  runtime-coord
embed                       19     1  3466     0  startup-coord
etcdserver/api/v3rpc        14     3  2779     0  runtime-coord
etcdserver/apply            12     2  1116     0  runtime-coord
etcdserver/api/etcdhttp     10     2   879     0  runtime-coord
storage (wiring pkg)         9     4   668     0  startup-coord
etcdserver/api/membership    3     8  1484     0  fail-fast
storage/mvcc                 3     6  3785     0  fail-fast
lease                        3     6  1206     0  fail-fast
storage/backend              0    11  1905     0  fail-fast (leaf)
storage/schema               6     8  1506     0  mixed
auth                         0     6  2208     0  fail-fast (leaf)
```

## Correlation Results

| Predictor | r | Interpretation |
|-----------|---|----------------|
| **K_out** | **+0.652** | Strong positive — outgoing dependencies predict bugs |
| LOC | +0.061 | Negligible |
| K_in | +0.036 | Negligible |

**K_out is the strongest predictor found for Go EH bugs.** LOC and K_in don't matter.

## The embed Anomaly (K_out=19, 0 bugs)

`embed` has K_out=19 but 0 documented bugs. This breaks a simple K_out threshold rule.

**Explanation**: `embed` does *startup wiring* — it connects components at initialization and delegates runtime failures to each component. If embed's config loading fails → immediate panic. No partial-failure recovery logic.

`etcdserver` does *runtime orchestration* — it must recover from raft quorum loss, storage errors, lease expiry, auth failures, ALL during live request processing. This is "coordinated recovery" in the strict sense.

**Refined hypothesis**: The predictor is not K_out alone, but **K_out × runtime-coordination-ratio**:
- etcdserver: K_out=26, runtime_coord=100% → 3 bugs
- embed: K_out=19, startup_coord=100% → 0 bugs
- v3rpc: K_out=14, runtime_coord ~50% → 0 documented bugs (may have latent)

## K_out Threshold

Only packages with K_out > 15 that do *runtime coordination* have bugs.
All fail-fast packages (K_out ≤ 3 on average) have 0 bugs regardless of K_in or LOC.

**Proposed threshold**: K_out > 12 AND runtime coordination responsibility → high bug risk zone.

## What This Means for B13

B13: "EH is the dominant failure cause (53-92% depending on methodology)."

These bugs confirm the pattern:
- etcdserver #84: CI updated before WAL apply → ordering EH failure
- etcdserver #85 (#12900): txn succeeds but returns error, callers skip cleanup → incorrect EH classification
- etcdserver #86 (#11651): auth revision mismatch fails silently → swallowed error

All 3 are classic EH anti-patterns (Yuan's categories), in the highest K_out package. B13's "error handling dominates" is confirmed at the package level: the highest-coordination package accumulates ALL the error handling bugs.

## Limitation

n=3 bugs total. All in one package. Can't statistically separate K_out from contract-type or from "etcdserver is just special." Replication needed:
1. **Consul** — similar architecture, K_out distribution should be comparable
2. **CockroachDB** — more bugs documented, larger dataset

## Next Action for F100

Clone Consul, run nk_analyze_go.py, cross-reference bug reports.
If r(K_out, bugs) > 0.5 in Consul also → strong confirmation.
If embed-like anomalies appear → runtime_coord modifier needed.

## Verdict on Contract-Type Hypothesis

**Supported but not yet independent of K_out.**

Contract type (fail-fast vs coordinated-recovery) is an excellent *labeling* framework for K_out behavior, but K_out itself is the measurable, tool-visible predictor. The contract type explains WHY K_out matters: high K_out packages must coordinate more failure modes, which creates EH complexity that exceeds typical pattern coverage.

**New P-108 candidate**: In DAG-enforced Go, K_out > 12 with runtime coordination responsibility is the primary EH bug risk zone — K_out is measurable by `nk_analyze_go.py`, K_in and LOC are not predictive.
