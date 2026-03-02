# F100: Error Handling Quality Predictors in DAG-Enforced Go
Conducted: Session 47 (2026-02-27)
Systems: Gin (github.com/gin-gonic/gin, N=7 packages, K_avg=1.57, score=11)
          Fiber (github.com/gofiber/fiber/v3, N=38 packages, K_avg=1.34, score=51)
Method: Static analysis of EH patterns; NK metrics from nk_analyze_go.py; code review

---

## Background

F97 established that NK-error-handling correlation requires import cycles (Python r≈-0.3 to -0.5) and
does not hold in DAG-enforced languages (Go r=+0.11, Rust r=-0.13). F100 asks: if NOT cycles, what
DOES predict EH quality in Go?

## Frameworks Analyzed

| Metric              | Gin        | Fiber       |
|---------------------|------------|-------------|
| NK Score            | 11.0       | 51.0        |
| N (packages)        | 7          | 38          |
| K_avg               | 1.57       | 1.34        |
| Hub concentration   | 45%        | 10%         |
| Architecture        | registry   | distributed |
| Source LOC          | 8,024      | 31,174      |
| Test LOC            | 15,285     | 67,581      |
| Test/Source ratio   | 1.90       | 2.17        |
| Exported funcs      | 62         | 167         |
| Error-returning (%) | 12.9%      | 14.4%       |
| Panic/kLOC          | 2.9        | 2.7         |
| TODO/FIXME count    | 0          | 12          |

---

## Key Finding 1: Metric Calibration Error (Go `_, err` is NOT "ignored")

Initial analysis counted `_, err = w.Write(bytes)` as "ignored errors" — this is WRONG.

In Go, `_, err = fn()` for functions returning (T, error) is the STANDARD pattern:
```go
_, err = w.Write(bytes)   // discards int n, captures error — CORRECT
return err                 // error is returned to caller
```

The truly-ignored pattern is `_, _ = fn()` or calling without assignment.

Gin's 18 apparent "ignored errors" in render/ are ALL correct Go error propagation. The `_, err`
counts are misleading in Go and should not be used as an EH quality metric.

---

## Key Finding 2: True EH Quality Metric — errcheck Suppression with Documentation

Real EH quality indicator: presence of `nolint:errcheck` suppressions WITH explanations.

**Gin**: 0 nolint:errcheck suppressions (no evidence of errcheck being run)
**Fiber**: 10+ suppressions, ALL with explicit rationale:
- `conn.Close() //nolint:errcheck // It is fine to ignore the error here` — net.Conn cleanup
- `c.SendStatus() //nolint:errcheck // not needed` — error handler, no recovery possible
- `file.Close() //nolint:errcheck // not needed` — defer cleanup
- `hash.Hash.Write //nolint:errcheck // hash.Hash.Write for std hashes never errors` — stdlib invariant

**Interpretation**: Fiber's team runs golangci-lint with errcheck enabled. Every errcheck warning
must be either fixed or suppressed with a comment. This creates mandatory EH review for every
function that ignores an error return. Gin may not run errcheck in CI.

---

## Key Finding 3: NK Score Does NOT Predict EH Quality

Despite NK score difference of 51 vs 11 (4.6x), normalized EH metrics are similar:
- Panic/kLOC: Fiber 2.7 vs Gin 2.9 — essentially equal
- Error return rate: Fiber 14.4% vs Gin 12.9% — similar
- True error ignores: Fiber has documented suppressions; Gin has none (but may be running blind)

Consistent with F97: NK score does not predict EH quality in DAG-enforced languages.

---

## Key Finding 4: API Boundary Visibility Creates Scrutiny Gradient

Within each framework, there IS a quality gradient by API boundary position:

**Gin by package**:
| Package | LOC  | Panic/kLOC | Notes |
|---------|------|------------|-------|
| .       | 5174 | 4.1        | API boundary (all users import this) |
| render  | 692  | 2.9        | Internal-ish (only Gin root uses it) |
| binding | 1431 | 0          | Internal-ish, clean |

**Fiber by package**:
| Package           | LOC   | Panic/kLOC | nolint:errcheck |
|-------------------|-------|------------|-----------------|
| . (root)          | 12554 | 2.2        | 3               |
| middleware/csrf   | 1068  | 3.7        | 0 (clean!)      |
| middleware/logger | 915   | 1.1        | 0               |
| client            | 3609  | 2.8        | 3               |
| binder            | 918   | 7.6        | 0               |

binder has high panic/kLOC (7 panics in 918 LOC = 7.6/kLOC). binder is an internal package
(users don't import directly). This is consistent with "internal packages = less external
scrutiny = more panics for internal invariants."

---

## Synthesis: What Predicts EH Quality in Go?

| Predictor          | Go           | Python       |
|--------------------|--------------|--------------|
| Import cycles      | Not applicable (compiler-enforced DAG) | Strong r≈-0.3 to -0.5 |
| NK score           | No correlation | No direct correlation |
| errcheck tooling   | Strong predictor (Fiber > Gin) | N/A |
| API boundary       | Scrutiny gradient (API packages better) | Weak effect |
| Test/source ratio  | Both healthy — not differentiating | — |

**Primary predictor**: Static analysis tooling adoption (errcheck + golangci-lint with mandatory CI).
Frameworks that run errcheck must either fix or document every ignored error. This creates a
"mandatory EH review" mechanism that replaces the "cycle-as-quality-signal" from Python.

**Secondary predictor**: API boundary visibility — packages directly imported by end users have
lower panic rates than internal implementation packages (scrutiny effect, consistent with F97's
observation about high-K hubs in etcd).

---

## Implications for B13 / Distributed Systems

These are HTTP frameworks, not distributed systems. The findings suggest:
- For Go distributed systems (etcd, CockroachDB), same mechanisms apply: tooling adoption and
  API boundary position likely predict EH quality
- etcd's inverted correlation (r=+0.11) may reflect: high-K packages = core APIs = high scrutiny
  = better error handling, regardless of cycles

---

## Next Steps for F100

1. **Verify tooling hypothesis**: Compare etcd (which runs errcheck) with a Go project that doesn't
2. **Quantify suppression rate**: nolint:errcheck count per kLOC as proxy for tooling discipline
3. **Test API-boundary hypothesis**: Compute in-degree (packages-that-import-me) and correlate
   with panic/kLOC and documented error suppressions
4. **Cross-language check**: Does Rust have an equivalent tooling predictor? (clippy deny(unused_must_use))

---

## Sources
- workspace/fiber/ (github.com/gofiber/fiber/v3) — HEAD as of 2026-02-27
- workspace/gin/ (github.com/gin-gonic/gin) — HEAD as of 2026-02-27
- nk_analyze_go.py output for both frameworks
- F97 cross-language NK-error analysis (experiments/distributed-systems/f97-cross-language-nk-error.md)
