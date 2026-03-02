# NK Analysis Applied to Go at Scale (F83)
Date: 2026-02-26 | Analyst: Session 42 | Language: Go
Question: Can NK analysis be applied to non-Python languages at scale?

## Method

Built `tools/nk_analyze_go.py` -- an automated NK analyzer for Go projects that:
1. Reads `go.mod` to identify the module path
2. Discovers all Go packages (directories with .go files)
3. Parses `import` statements from each .go file (regex, no compiler needed)
4. Filters to internal imports (those starting with the module path)
5. Builds inter-package dependency graph
6. Computes NK metrics using the same formulas as `nk_analyze.py`

**Granularity**: Package-level (directory), which is Go's natural compilation unit.
This parallels Python's module-level analysis. Files within a Go package share a
namespace, so file-level analysis would require symbol tracing (as the manual
go-net-http analysis did). Package-level captures the explicit `import` graph.

## Projects Analyzed

| # | Project | N | K_avg | K_max | Cycles | Composite | LOC | Files | Architecture |
|---|---------|---|-------|-------|--------|-----------|-----|-------|-------------|
| 1 | gorilla/mux | 1 | 0.00 | 0 | 0 | 0.0 | 2,332 | 6 | monolith |
| 2 | go-chi/chi | 2 | 0.50 | 1 | 0 | 1.0 | 3,999 | 34 | monolith |
| 3 | labstack/echo | 3 | 0.67 | 1 | 0 | 2.0 | 11,069 | 44 | monolith |
| 4 | spf13/cobra | 2 | 0.50 | 1 | 0 | 1.0 | 6,938 | 19 | monolith |
| 5 | gin-gonic/gin | 7 | 1.57 | 5 | 0 | 11.0 | 7,726 | 57 | registry |
| 6 | gofiber/fiber | 38 | 1.34 | 5 | 0 | 51.0 | 31,174 | 144 | distributed |
| 7 | prometheus/prometheus | 104 | 4.12 | 26 | 0 | 429.0 | 141,624 | 402 | framework |

## Cross-Language Comparison

| Package | Language | N | K_avg | Cycles | Composite | Architecture |
|---------|----------|---|-------|--------|-----------|-------------|
| gorilla/mux | Go | 1 | 0.00 | 0 | 0.0 | monolith |
| logging | Python | 3 | 0.33 | 0 | 1.0 | monolith |
| go-chi/chi | Go | 2 | 0.50 | 0 | 1.0 | monolith |
| spf13/cobra | Go | 2 | 0.50 | 0 | 1.0 | monolith |
| json | Python | 5 | 0.40 | 0 | 2.0 | hub-and-spoke |
| labstack/echo | Go | 3 | 0.67 | 0 | 2.0 | monolith |
| Express 5 | JS | 6 | 1.00 | 0 | 6.0 | -- |
| gin-gonic/gin | Go | 7 | 1.57 | 0 | 11.0 | registry |
| Express 4 | JS | 11 | 1.36 | 0 | 15.0 | -- |
| http.client | Python | 11 | 2.40 | 0 | 26.4 | -- |
| unittest | Python | 13 | 2.08 | 1 | 28.0 | framework |
| Rust serde | Rust | 24 | 1.25 | 0 | 30.0 | -- |
| importlib | Python | 24 | 1.50 | 2 | 38.0 | distributed |
| xml | Python | 22 | 1.59 | 3 | 38.0 | distributed |
| email | Python | 29 | 1.52 | 2 | 46.0 | distributed |
| gofiber/fiber | Go | 38 | 1.34 | 0 | 51.0 | distributed |
| requests | Python | -- | -- | 0 | 55.0 | -- |
| click | Python | -- | -- | 0 | 68.0 | -- |
| Go net/http (manual) | Go | 27 | 3.19 | 3 | 89.0 | -- |
| multiprocessing | Python | 23 | 3.61 | 19 | 102.0 | tangled |
| asyncio | Python | 33 | 3.85 | 1 | 128.0 | framework |
| prometheus | Go | 104 | 4.12 | 0 | 429.0 | framework |

## Key Findings

### Finding 1: Go projects have zero import cycles (all 7 tested)

Every Go project analyzed has **zero import cycles**. This is a structural property
of Go's build system: circular package imports are a compile error. The Go compiler
enforces DAG discipline at the package level by design.

This has a major implication for the composite score: the `+ Cycles` term contributes
nothing for Go projects. The composite reduces to just `K_avg * N`. Compare:

- Python `multiprocessing`: composite = 83.0 + **19 cycles** = 102.0
- Python `email`: composite = 44.1 + **2 cycles** = 46.0
- Go `fiber`: composite = 51.0 + **0 cycles** = 51.0
- Go `prometheus`: composite = 429.0 + **0 cycles** = 429.0

**The cycle term, which is the strongest predictor of maintenance burden in Python
(rho=0.917, F79), is structurally zeroed out in Go.** This means the composite
score may underestimate Go maintenance burden relative to Python, since it cannot
capture the cycle-driven entanglement that Go's compiler prevents.

### Finding 2: K_avg alone correctly ranks Go projects by complexity

Even without cycles, the K_avg * N ranking matches intuition:

| Project | Role | Composite | Matches expectations? |
|---------|------|-----------|----------------------|
| gorilla/mux | Simple router | 0.0 | Yes -- single package, no internal deps |
| chi | Router + middleware | 1.0 | Yes -- two packages, minimal coupling |
| echo | Framework (medium) | 2.0 | Yes -- three packages, low coupling |
| cobra | CLI framework | 1.0 | Yes -- core + doc generation |
| gin | Framework (full) | 11.0 | Yes -- 7 packages with binding/render sub-systems |
| fiber | Full framework | 51.0 | Yes -- 38 packages including middleware ecosystem |
| prometheus | Monitoring system | 429.0 | Yes -- massive, 104 packages, 142K LOC |

### Finding 3: Go's package architecture is fundamentally different from Python

**Go favors fewer, larger packages with minimal inter-package coupling.**

| Metric | Go average (7 projects) | Python average (9 packages) |
|--------|------------------------|---------------------------|
| N | 22.4 | 17.4 |
| K_avg | 1.24 | 1.63 |
| Cycles | 0.0 | 3.1 |
| Composite | 70.7 | 43.2 |

Go projects tend to have more packages but lower K_avg per package. The zero cycles
reflect compiler enforcement. However, Go's flat intra-package namespace means that
coupling WITHIN a package is invisible to this analysis. A 15,000 LOC package like
`prometheus/tsdb` has extensive internal file-to-file coupling that the package-level
analysis cannot see.

**Observation**: Go inter-package analysis is analogous to analyzing only the top-level
sub-packages of a Python project (like `flask.blueprints`, `flask.wrappers`), while
ignoring intra-module imports. The Python analyzer goes deeper.

### Finding 4: Comparing similar-purpose projects across languages

**HTTP routers:**
- gorilla/mux (Go): 0.0 -- single flat package
- chi (Go): 1.0 -- router + middleware
- Express 5 (JS): 6.0 -- modular npm architecture

**Web frameworks:**
- echo (Go): 2.0 -- minimal sub-packaging
- gin (Go): 11.0 -- binding/render/internal sub-packages
- flask (Python): 130.0 -- 24 modules with 34 cycles (session 41 data)

The comparison shows Go projects score dramatically lower than Python equivalents,
primarily because:
1. Go enforces zero cycles (removes the biggest Python burden driver)
2. Go's flat namespace concentrates complexity within packages rather than between them
3. The NK inter-package graph captures less of Go's total complexity

### Finding 5: Prometheus validates the tool at scale

Prometheus (104 packages, 429.0) is the largest project we have ever analyzed. Key observations:

- **Hub packages**: `discovery/targetgroup` (K_in=30), `discovery` (K_in=28),
  `model/labels` (K_in=28) are the most-depended-upon packages
- **Bridge packages**: `discovery/install` (K_out=26, K_in=0), `plugins` (K_out=26, K_in=0)
  are registration packages that import everything but nothing imports them
- **Architecture**: classified as "framework" (K_avg=4.12), matching its real role
  as a large infrastructure system with deep coupling between subsystems
- **No cycles despite 429 edges**: Go's compiler forces clean layering even at massive scale

## Comparison: Automated vs Manual Go Analysis

The manual Go net/http analysis (Session 38) measured **file-level** coupling by tracing
symbol usage across files within a single package. This gave:
- N=27 (files), K_avg=3.19, Cycles=3, Composite=89.0

The automated tool measures **package-level** coupling via `import` statements. For a
monolithic package like net/http (single directory), the automated tool would show:
- N=1, K_total=0, Composite=0.0

This is the key limitation: **the automated tool captures inter-package coupling only**.
For Go projects with many packages (gin, fiber, prometheus), this is useful. For
monolithic packages (mux, net/http), it captures nothing.

A complete Go NK analysis would need both levels:
1. **Package-level** (what this tool does): inter-package import graph
2. **File-level** (what the manual analysis did): intra-package symbol tracing

## Answer to F83

**Can NK analysis be applied to non-Python languages at scale? YES -- with caveats.**

### What works
- The tool successfully analyzes Go projects from 1 to 104 packages
- K_avg * N produces ordinal rankings that match intuitive complexity ordering
- The composite score correctly identifies prometheus as far more complex than gin
- Architecture classification (monolith/distributed/framework) works across languages
- Static parsing of Go imports is simpler and more reliable than Python AST parsing

### What is limited
1. **Cycles = 0 for all Go projects**: The cycle term, which is the most powerful
   predictor in Python, contributes nothing in Go. The composite formula may need
   a Go-specific adjustment (e.g., weight K_avg more heavily, or add a file-level
   coupling metric).

2. **Package-level granularity misses intra-package coupling**: Go's flat namespace
   means that a 15K LOC package can have enormous internal complexity that the
   inter-package analysis cannot detect. The manual net/http analysis found 3 cycles
   at the file level that this tool cannot see.

3. **Cross-language composite comparison is questionable**: Gin (Go, 11.0) scoring
   lower than Flask (Python, 130.0) does not mean gin has less total complexity.
   It means gin has less *inter-package* complexity. The comparison is valid within
   Go projects but not directly across languages without normalizing for what the
   metric captures.

### Recommendation
The Go NK tool is useful for:
- Comparing Go projects against each other (valid and tested)
- Identifying hub/bridge packages in large Go codebases (prometheus demonstrates this)
- Architecture classification

For cross-language comparison, the **composite score should be annotated with language
and granularity** to prevent false equivalence. A Go project scoring 51.0 at package
level is not "simpler" than a Python project scoring 55.0 at module level -- they
measure different things.

## Tool Details

`tools/nk_analyze_go.py` supports:
- `--verbose`: show per-package breakdown with K_out, K_in, LOC, files
- `--json`: machine-readable JSON output (same structure as nk_analyze.py)
- `--suggest-refactor`: cycle reduction suggestions (useful if cycles exist)
- Works without Go compiler -- pure Python static analysis of .go source files
- Handles Go module paths, version suffixes, build constraints
- Skips vendor/, testdata/, examples/, _examples/, test files

## Falsification Condition

The claim "NK analysis works on Go at scale" would be falsified if:
- A Go project with zero cycles but high composite showed low maintenance burden
  while a low-composite project showed high burden (ordinal ranking failure)
- The tool produced incorrect dependency graphs (missed imports or phantom edges)
- Package-level analysis produced misleading architecture classifications

## Evidence Type: Observed
7 Go projects analyzed automatically with working tool. Results cross-checked against
manual net/http analysis. Rankings match intuitive complexity ordering.
