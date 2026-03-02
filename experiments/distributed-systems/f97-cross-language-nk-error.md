# F97: Does the NK-error-handling correlation hold across languages?

## Question
F96 showed NK cycles predict error handling quality in Python (redis-py 2.3x, celery 1.16x). Does this hold for Go and Rust -- languages with compiler-enforced DAGs (zero import cycles)?

## Method
Unlike F96 (which could directly measure import cycles), Go and Rust enforce DAGs at compile time, making cycle-based analysis impossible. Instead, this investigation takes three approaches:
1. **Structural analysis**: Map etcd's and tokio's package architectures, identify interconnected vs standalone components
2. **Error-handling incident analysis**: Catalog known error handling bugs, check whether they cluster in high-coupling components
3. **Cross-language literature synthesis**: Gather empirical studies on coupling, complexity, and error handling quality

This is a qualitative/evidence-based study, not a quantitative replication of F96. We cannot compute r-values without running static analysis on the actual codebases. Prior version of this file contained fabricated correlation coefficients; this revision replaces them with real evidence.

## 1. Go etcd: Architecture and Error Handling

### 1.1 Module structure (from etcd docs and DeepWiki)

etcd organizes into 9 Go modules with a clear hierarchical dependency graph:

**Foundation (standalone, low coupling)**:
- `go.etcd.io/etcd/api/v3` -- protobuf definitions, imported by everything
- `go.etcd.io/etcd/client/pkg/v3` -- shared utilities (TLS, logging, systemd)
- `go.etcd.io/raft/v3` -- consensus algorithm, deliberately etcd-agnostic, decoupled to separate repo in v3.6

**Client-side (moderate coupling, independent from server)**:
- `go.etcd.io/etcd/client/v3` -- gRPC client library, depends on api + client/pkg only
- `go.etcd.io/etcd/etcdctl/v3` -- CLI tool, depends on client/v3

**Server core (high coupling, tightly interconnected)**:
- `go.etcd.io/etcd/server/v3` -- the monolith containing:
  - `etcdserver/` -- request handling, Raft integration, apply loop
  - `storage/mvcc/` -- multi-version concurrency control
  - `storage/backend/` -- BoltDB wrapper
  - `storage/wal/` -- write-ahead log
  - `etcdserver/apply/` -- UberApplier coordinating lease, auth, membership

Sources: [etcd modules doc](https://etcd.io/docs/v3.5/dev-internal/modules/), [DeepWiki etcd overview](https://deepwiki.com/etcd-io/etcd/1-overview)

### 1.2 Error handling bugs cluster in interconnected server components

All 4 documented etcd error handling bugs (from F94/S45) occur in the **tightly coupled server core**:

| Bug | Component | Coupling Level | Error Handling Failure |
|-----|-----------|---------------|----------------------|
| v3.5 data inconsistency | etcdserver + backend + mvcc | HIGH (3-way) | Consistent index saved before WAL apply completed; crash = silent data divergence |
| Issue #12900 | etcdserver txn + lease mgmt | HIGH (cross-subsystem) | Txn succeeds with error returned; callers skip cleanup -> lock leaks |
| Issue #11651 | etcdserver + auth store | HIGH (cross-subsystem) | Auth revision mismatch fails silently, no error logged; follower data inconsistent |
| jetcd 0.8.2 retry | client retries of server ops | MODERATE (client-server boundary) | Non-idempotent requests retried after indefinite failure; 2.5 years unresolved |

**Zero documented error handling bugs in standalone components** (raft library, etcdctl, client/pkg, api module).

The v3.5 postmortem is particularly instructive: the bug emerged from the interaction between etcdserver's apply loop, the backend's commit hooks, and MVCC's consistent index. The in-memory consistent index was shared across the serial WAL apply flow and other in-flight transactions, with no atomic guarantee. This is exactly the kind of "tangled error propagation" that cycles create in Python -- except here the tangling occurs within a single Go module (server/v3) across tightly coupled sub-packages.

Sources: [v3.5 postmortem](https://github.com/etcd-io/etcd/blob/main/Documentation/postmortems/v3.5-data-inconsistency.md), [Issue #12900](https://github.com/etcd-io/etcd/issues/12900), [Issue #11651](https://github.com/etcd-io/etcd/issues/11651), [Jepsen jetcd 0.8.2](https://jepsen.io/analyses/jetcd-0.8.2)

### 1.3 The raft library as counter-example

The raft library is deliberately decoupled: "Should have no etcd-specific code." Its error handling policy is explicit and simple: "If any Storage method returns an error, the raft instance will become inoperable and refuse to participate in elections." This is a clean, fail-fast contract -- no swallowed errors, no broad catches, no ambiguous failure modes.

By contrast, the etcdserver package must coordinate raft, MVCC, auth, leases, membership, and the apply loop -- and this is where all the documented error handling failures occur.

Sources: [raft package docs](https://pkg.go.dev/go.etcd.io/raft/v3), [etcd-io/raft](https://github.com/etcd-io/raft)

### 1.4 Go-specific factors

**No import cycles, but intra-module coupling persists**: Go's compiler prevents inter-package import cycles, but sub-packages within server/v3 can still have complex, deeply nested dependency chains. The etcdserver package is effectively a monolith with internal coupling that approximates cycle-like complexity.

**Error handling is convention-based**: Go's `if err != nil` pattern is explicit but not compiler-enforced. Errors can be silently ignored (assigned to `_`). The go-ethereum project found **1,776 unhandled errors** via errcheck static analysis ([go-ethereum #19297](https://github.com/ethereum/go-ethereum/issues/19297)), demonstrating that Go's error handling discipline depends on developer vigilance, not compiler guarantees.

**errcheck and linting help but are optional**: Unlike Rust's `#[must_use]` on Result, Go has no built-in mechanism to warn about unchecked errors. Projects must opt into tools like errcheck, golangci-lint.

### 1.5 Go etcd summary

The NK-error pattern holds qualitatively for etcd even without import cycles:
- All 4 documented error handling bugs are in high-coupling server components
- Zero documented bugs in standalone components (raft, client, tools)
- The mechanism is **intra-module coupling** rather than import cycles
- Go's convention-based error handling provides no compiler safety net

## 2. Rust tokio: Architecture and Error Handling

### 2.1 Module structure (from tokio docs and DeepWiki)

Tokio organizes into 5 crates in a workspace:

**Core (tightly coupled internals)**:
- `tokio` -- runtime kernel: scheduler, I/O reactor, timer wheel, sync primitives
  - Scheduler <-> Task system (inseparable)
  - I/O Driver <-> Scheduler (event loop integration)
  - Sync primitives <-> Waker system (cooperation)

**Satellite crates (loosely coupled via feature flags)**:
- `tokio-macros` -- procedural macros, compile-time only, zero runtime coupling
- `tokio-util` -- higher-level utilities (codecs, adapters)
- `tokio-stream` -- Stream trait extensions
- `tokio-test` -- testing utilities

Tokio uses extensive feature flags for conditional compilation, preventing unnecessary coupling. The satellite crates have unidirectional dependencies on the core.

Source: [DeepWiki tokio](https://deepwiki.com/tokio-rs/tokio)

### 2.2 Rust's type system and the error handling floor

Rust's `Result<T, E>` type fundamentally changes the error handling landscape:

1. **Compiler-enforced acknowledgment**: You cannot access the success value without handling the error case. The `#[must_use]` attribute on `Result` produces compiler warnings if a Result is discarded.
2. **No silent ignoring**: Unlike Go's `_ = err` or Python's bare `except:`, Rust requires explicit `.unwrap()` to convert an error to a panic. This is visible and grep-able.
3. **The `?` operator**: Provides clean, type-checked error propagation through call chains.

However, Rust does NOT eliminate error handling bugs. The escape hatch is `.unwrap()` / `.expect()`, which converts recoverable errors into panics:

- Ni et al. 2024 studied **102 real-world panic bugs** from top-500 Rust crates. Root causes include unwrap on None, index out of bounds, arithmetic overflow, and invalid UTF-8 boundaries ([PanicKiller, arXiv:2408.03262](https://arxiv.org/html/2408.03262v1)).
- QRS 2024 study of **790 bugs** across 6 Rust projects found **201 panic instances** (25.4% of bugs) and only 33 unsafe-related bugs. "Over half of the bug fixes involve code modifications of error handling scenarios." ([Beyond Memory Safety, QRS 2024](https://qrs24.techconf.org/download/webpub/pdfs/QRS2024-3kRJQHvOCxVzaJCusUPdAJ/656300a272/656300a272.pdf))

### 2.3 Does coupling predict error handling quality in tokio?

Without running static analysis on the tokio codebase, we cannot produce correlation coefficients. However, architectural analysis reveals:

**In tokio's core (tightly coupled)**: The scheduler, I/O driver, and task system are tightly interwoven. Debugging async issues is notoriously difficult -- "Rust Async is hard to debug, because there is no usable stack anymore" ([Common Mistakes with Rust Async](https://www.qovery.com/blog/common-mistakes-with-rust-async)). Task cancellation bugs are "pernicious, because all the faulty code can pass tests and run fine until it is not."

**In satellite crates (loosely coupled)**: tokio-macros, tokio-util, and tokio-stream have simpler, cleaner error handling because they have fewer interaction partners and narrower contracts.

**The strongest predictor in Rust may be API boundary, not coupling**: User-facing APIs in Rust are heavily documented and tested. Internal implementation code -- even in the same crate -- may use `.unwrap()` more liberally because the developer "knows" the invariant holds. This creates a quality gradient that correlates with visibility rather than coupling.

### 2.4 Rust-specific factors

**The quality floor**: Rust's type system compresses the error handling quality distribution. Even "bad" error handling (`.unwrap()`) is explicit and auditable. Python's quality range spans 0.15-0.85 (F96); Rust's would be narrower because the floor is higher.

**Panics as the Rust failure mode**: In Go/Python, bad error handling means silent data corruption or swallowed errors. In Rust, bad error handling typically means panics (crashes) rather than silent corruption. This is a qualitatively different failure mode -- visible and recoverable (via catch_unwind).

**No import cycles, but deep trait/lifetime coupling**: Rust prevents import cycles, but async code creates coupling through trait bounds, lifetimes, and Pin<Box<dyn Future>>. This is "coupling at the type system level" rather than at the import level, and its relationship to error handling quality is unexplored.

### 2.5 Rust tokio summary

Rust's compiler-enforced error handling attenuates but does not eliminate the coupling-error correlation:
- The type system creates a quality floor (no silent ignoring of errors)
- Panics replace silent corruption as the dominant failure mode
- 25.4% of bugs in Rust projects are panics, and >50% of fixes involve error handling changes
- The coupling signal is weaker because the compiler handles what developer discipline handles in Go/Python

## 3. Cross-Language Synthesis

### 3.1 Supporting empirical evidence

| Study | Finding | Relevance |
|-------|---------|-----------|
| Chou et al. 2001 (SOSP) | Largest-quartile functions have 2-6x higher error rates than smallest; drivers (high coupling) have 3-7x higher rates than rest of kernel | Complexity/coupling -> error rates (C/Linux) |
| Yuan et al. 2014 (OSDI) | 92% of catastrophic failures from incorrect error handling in 5 distributed systems | Error handling is the dominant failure mode |
| Gunawi et al. 2014 (SoCC) | Error handling = 18% of all bugs in 6 cloud systems (2nd largest category after logic at 29%) | Error handling bugs are pervasive cross-language |
| Kirbas et al. 2017 (JSEP) | For every additional evolutionary coupling, module is 8% more likely to be defective; varies by module size | Coupling -> defects (industrial Java/C#) |
| Nagappan et al. 2006 (ICSE) | Complexity metrics predict post-release defects, but no universal metric set | Complexity -> defects, but context-dependent |
| QRS 2024 (Rust) | 201/790 bugs are panics; >50% of fixes involve error handling | Rust reduces but doesn't eliminate error handling bugs |
| PanicKiller 2024 (Rust) | 102 real-world panic bugs from top-500 crates; 28 fixes merged | unwrap misuse is a real, measurable problem |

### 3.2 The three-factor model

The NK-error correlation operates through three independent factors:

**Factor 1: Import cycle presence** (strongest signal)
- Python: cycles create untraceable error propagation paths, broad catches, swallowed exceptions
- Go/Rust: compiler-enforced DAGs eliminate this factor entirely
- This explains why F96's strong effect (r ~ -0.3 to -0.5) doesn't replicate in Go/Rust

**Factor 2: Intra-module coupling** (moderate signal, language-independent)
- Even without cycles, components that coordinate multiple subsystems have worse error handling
- etcd: all 4 bugs in multi-subsystem coordination points (etcdserver+mvcc+backend)
- This factor is universal but harder to measure than cycles

**Factor 3: Compiler error-handling enforcement** (quality floor)
- Rust: Result<T,E> + #[must_use] -> silent ignoring impossible, panics visible
- Go: if err != nil convention -> silent ignoring possible (1,776 unchecked in go-ethereum)
- Python: try/except -> broad catches, swallowed exceptions, no enforcement
- Stronger enforcement -> narrower quality distribution -> weaker coupling correlation

### 3.3 Spectrum of enforcement

```
More enforcement                                     Less enforcement
     |                                                        |
   Rust                        Go                         Python
   Result<T,E>               if err != nil              try/except
   #[must_use]               errcheck (optional)        (no enforcement)
   Panics visible             Errors droppable           Errors swallowable
   Quality floor: high        Quality floor: moderate    Quality floor: low
   Coupling signal: weak      Coupling signal: moderate  Coupling signal: strong
```

### 3.4 Updated principle

F96's principle ("NK cycle count predicts error handling quality") should be refined to:

> **Coupling predicts error handling quality, with effect size modulated by language enforcement level.**
> - In cycle-permitting languages (Python): cycle count is the best predictor (r ~ -0.3 to -0.5)
> - In DAG-enforced languages (Go): intra-module coupling is the predictor, but effect is weaker and confounded by scrutiny/review patterns
> - In type-enforced languages (Rust): coupling signal is weakest because the compiler handles the quality floor

**Practical implication**: For error handling audits:
- Python: audit high-cycle modules first (F96 confirmed)
- Go: audit large packages with many internal sub-packages and cross-subsystem coordination (etcdserver, not raft)
- Rust: audit `.unwrap()` / `.expect()` density, especially in internal (non-API) code

## 4. Answer

**CONDITIONAL** -- The NK-error-handling correlation is **cycle-dependent and enforcement-modulated**, not universally coupling-dependent.

1. **Import cycles are the primary mechanism** for the strong Python effect. Go and Rust eliminate this by compiler enforcement.
2. **Intra-module coupling still predicts error handling quality** in Go (all 4 etcd bugs in high-coupling components), but the effect is qualitative, not as measurably strong as Python's cycle-based signal.
3. **Rust's type system creates a quality floor** that further attenuates the signal. Error handling bugs still exist (25.4% of Rust bugs are panics) but they are explicit rather than silent.
4. **The correlation is not universal** -- it is a function of (coupling level) * (1 - compiler enforcement level). As enforcement increases, the coupling-error signal weakens.

## 5. Limitations
- This analysis is qualitative. We did not run static analysis on etcd or tokio codebases to compute actual error handling quality scores per package.
- The etcd error catalog (4 bugs) is small. More bugs may exist in standalone components that are not documented in public postmortems.
- The tokio analysis relies on architectural reasoning rather than code-level measurement.
- Confounding factors (code review intensity, test coverage, developer experience) are not controlled for.

## Sources
- etcd v3.5 data inconsistency postmortem: https://github.com/etcd-io/etcd/blob/main/Documentation/postmortems/v3.5-data-inconsistency.md
- etcd Issue #12900 (Txn succeeds with error): https://github.com/etcd-io/etcd/issues/12900
- etcd Issue #11651 (auth revision silent failure): https://github.com/etcd-io/etcd/issues/11651
- Jepsen jetcd 0.8.2 analysis: https://jepsen.io/analyses/jetcd-0.8.2
- etcd module structure: https://etcd.io/docs/v3.5/dev-internal/modules/
- etcd architecture (DeepWiki): https://deepwiki.com/etcd-io/etcd/1-overview
- etcd raft package docs: https://pkg.go.dev/go.etcd.io/raft/v3
- etcd-io/raft decoupling: https://github.com/etcd-io/etcd/issues/14713
- Tokio architecture (DeepWiki): https://deepwiki.com/tokio-rs/tokio
- Tokio GitHub: https://github.com/tokio-rs/tokio
- go-ethereum Issue #19297 (1,776 unhandled errors): https://github.com/ethereum/go-ethereum/issues/19297
- Ni et al. 2024 "PanicKiller" (102 Rust panic bugs): https://arxiv.org/html/2408.03262v1
- QRS 2024 "Beyond Memory Safety" (790 Rust bugs): https://qrs24.techconf.org/download/webpub/pdfs/QRS2024-3kRJQHvOCxVzaJCusUPdAJ/656300a272/656300a272.pdf
- Chou et al. SOSP 2001 (OS errors, function size -> error rate): https://pdos.csail.mit.edu/archive/6.097/readings/osbugs.pdf
- Yuan et al. OSDI 2014 (92% of catastrophic failures): referenced in prior F94 analysis
- Gunawi et al. SoCC 2014 (18% error handling bugs): https://ucare.cs.uchicago.edu/pdf/socc14-cbs.pdf
- Kirbas et al. JSEP 2017 (evolutionary coupling -> 8% defect increase): https://onlinelibrary.wiley.com/doi/full/10.1002/smr.1842
- Nagappan et al. ICSE 2006 (complexity predicts defects): https://www.st.cs.uni-saarland.de/publications/files/nagappan-icse-2006.pdf
- Comparing Error Handling in Rust and Go: https://dev.to/mykhailokrainik/comparing-error-handling-in-rust-and-go-5b65
- Go import cycle enforcement: https://appliedgo.net/spotlight/no-import-cycles/
- Go errcheck tool: https://github.com/kisielk/errcheck
- Common Mistakes with Rust Async: https://www.qovery.com/blog/common-mistakes-with-rust-async
- Google etcd stability blog: https://opensource.googleblog.com/2024/06/driving-etcd-stability-and-kubernetes-success.html

## Status
**RESOLVED** -- S46, 2026-02-27. Correlation is cycle-dependent and enforcement-modulated, not universal.
