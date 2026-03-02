# investor-swarm: Domain-Specific Child Swarm Design
Created: 2026-02-27 | Approach: 2 — minimal swarm description

## What this is

A design specification for a child swarm whose knowledge domain is
`<your-repos>/investor` — a quantitative investment pipeline.  The child swarm
does not merely *analyze* that codebase; it *knows* it, evolves that knowledge
across sessions, and compounds understanding the same way the parent swarm
compounds understanding of collective intelligence.

If `experiments/children/` were not gitignored in the parent, the child would
live at `experiments/children/investor-swarm/`.  The full file tree is
specified below; any session can instantiate it with `genesis.sh` and apply the
customizations documented here.

---

## NK Analysis Results (2026-02-27)

Ran with: `uv run python3 tools/nk_analyze.py investor` (from `<your-repos>/investor`)

```
=== NK ANALYSIS: investor ===

  Path: <your-repos>/investor/src/investor
  Total LOC: 25685
  Architecture: distributed

  NK Metrics:
    N (modules):          68
    K_total (edges):      123
    K_avg:                1.81
    K/N:                  0.027
    K_max:                13  (core.data_manager — hub)
    Cycles:               0
    K_avg*N + Cycles:     123.0
    Burden (Cyc+0.1N):   6.8
    LOC/N:                378
    Hub concentration:    11%
```

**Cross-package context**: investor (123.0) sits between `jinja2` (109) and
`asyncio` (128) — complexity is flask-scale with zero cycles.  That is
surprisingly clean for a 25k-LOC financial pipeline: the data-flow is
acyclic and the hub concentration (11%) is low, meaning no single module is
holding the whole system together by brute force.

**Package breakdown** (from verbose output):

| Package | Modules | Key hubs |
|---------|---------|----------|
| `core/` | 8 | `data_manager` (K_out=13), `analysis_manager` (K_out=12), `visualization_manager` (K_out=8) |
| `data/` | 18 | `unified_data_manager` (K_out=9), `base_downloader` (K_out=5) |
| `forecasting/` | 11 | `data_processor` (K_out=3), `scalable_plotting` (K_out=2) |
| `analysis/` | 4 | `options_analysis` (K_out=7) |
| `utils/` | 8 | leaf nodes only (all K_out=0 or 2) |
| `models/` | 3 | `factor_models` (K_out=2) |
| `trading/` | 3 | leaf nodes |
| `visualization/` | 2 | leaf nodes |

**Interpretation**: `core/` is the coordination layer.  `data/` is the widest
package with the most internal sub-structure (including a `base/` abstraction
layer with provider registry and cache manager).  `forecasting/` contains the
largest individual modules by LOC (several >600 LOC).  Zero cycles means
dependency propagation is predictable.

---

## Child Swarm File Tree

```
experiments/children/investor-swarm/
├── CLAUDE.md                         (see below)
├── beliefs/
│   ├── CORE.md                       (see below — investor-specific purpose)
│   ├── DEPS.md                       (see below — initial investor belief)
│   └── CONFLICTS.md                  (inherited from genesis template)
├── memory/
│   ├── INDEX.md                      (see below)
│   ├── DISTILL.md                    (inherited from genesis template)
│   ├── VERIFY.md                     (inherited from genesis template)
│   ├── PRINCIPLES.md                 (inherited from parent swarm)
│   └── lessons/
│       └── TEMPLATE.md               (inherited from genesis template)
├── tasks/
│   ├── FRONTIER.md                   (see below — investor-specific questions)
│   ├── TASK-001.md                   (genesis default: validate setup)
│   └── NEXT.md                       (genesis default: do TASK-001 first)
├── tools/
│   ├── validate_beliefs.py           (inherited from genesis — NEVER REMOVE)
│   ├── pre-commit.hook               (inherited from genesis)
│   └── install-hooks.sh              (inherited from genesis)
├── modes/
│   ├── research.md                   (inherited from genesis)
│   ├── build.md                      (inherited from genesis)
│   ├── repair.md                     (inherited from genesis)
│   └── audit.md                      (inherited from genesis)
└── workspace/
    └── .gitkeep
```

---

## beliefs/CORE.md (customized)

```markdown
# Core Beliefs v0.1

## Purpose
We are building knowledge about the investor codebase (<your-repos>/investor) —
a quantitative investment pipeline.  Goal: compound understanding of its
architecture, bugs, improvement opportunities, and financial logic across
sessions.  Every session leaves this swarm knowing the investor codebase better
than before.

## Domain
investor/ — quantitative investment pipeline (Python, ~68 src modules, 25685 LOC)

Architecture (from NK analysis, 2026-02-27):
- N=68 modules, K_avg=1.81, K_total=123, Cycles=0 — clean acyclic dependency graph
- Hub: core.data_manager (K_out=13) — coordinates all data acquisition
- Architecture class: "distributed" — no single god-module, low hub concentration (11%)
- Packages: core/ (orchestration), data/ (acquisition+storage), forecasting/
  (ML/anomaly), analysis/ (market regime, options), models/ (factor, options
  pricing), trading/ (strategies), utils/ (shared primitives), visualization/
- Entry points: scripts/download_data.py, scripts/analyze_data.py

## Operating principles
1. **Improve genuinely, don't harm.**
2. **You will make mistakes.** Apply the 3-S Rule: verify if Specific, Stale,
   or Stakes-high.  Financial code has Stakes-high for many claims.
3. **Small steps.** Plan → act small → commit → learn → update.
4. **Document decisions.** Write down *why*, not just *what*.
5. **Track where beliefs come from.** See beliefs/DEPS.md.
6. **Keep memory compact.** Lessons are max 20 lines.
7. **Challenge the setup.** Write challenges to tasks/FRONTIER.md.
8. **Correct, don't delete.** Mark wrong knowledge SUPERSEDED.

## Memory layers
- **Always load**: This file + memory/INDEX.md
- **Load per task**: Your task file + files the index points you to
- **Load rarely**: Git history for deep investigation

## Belief updates
Changing this file requires: proposal with reasoning → check what depends on
old belief (beliefs/DEPS.md) → commit with explanation.

## Phase awareness
Genesis → early (build initial beliefs from codebase exploration) → mature
(compound architectural and financial domain knowledge).

## v0.1 | 2026-02-27 | Genesis (Approach 2 — domain-specific child)
```

---

## beliefs/DEPS.md (customized — initial investor belief)

```markdown
# Belief Dependencies

Evidence types: `observed` (empirically tested in this system) |
`theorized` (reasoning only, not yet tested)

When a belief is disproven: check dependents below → update those too.

---

### B1: investor's dependency graph is acyclic (Cycles=0), making refactoring
       safe to do package-by-package without cascading breakage
- **Evidence**: observed
- **Falsified if**: A future NK analysis finds cycles > 0, OR a refactor in
  one package breaks unrelated packages that weren't downstream per the graph
- **Depends on**: none
- **Depended on by**: B2
- **Last tested**: 2026-02-27 (NK analysis: investor package, K_total=123,
  Cycles=0; verbose module list shows no circular imports)

### B2: core.data_manager is the integration hub; changes to it propagate
       to ~20% of the codebase (K_out=13 out of 68 modules)
- **Evidence**: observed
- **Falsified if**: NK re-analysis shows core.data_manager K_out < 10 (hub
  was an analysis artifact), OR most changes to data_manager do not require
  downstream updates
- **Depends on**: B1
- **Depended on by**: none
- **Last tested**: 2026-02-27 (verbose NK output: core.data_manager imports
  core.config, core.error_handling, core.exceptions, data, data.crypto_data,
  data.currency_converter, data.earnings_data, data.earnings_processor,
  data.macro_data, data.sector_data, data.stock_data, data.storage,
  data.unified_data_manager — 13 direct dependencies)

### B3: Git-as-memory is sufficient at small scale for this child swarm
- **Evidence**: theorized
- **Falsified if**: A session fails to find needed information about investor/
  via grep/file-read within a reasonable time
- **Depends on**: none
- **Last tested**: never

### B4: Layered memory prevents context bloat for this child swarm
- **Evidence**: theorized
- **Falsified if**: A session following layered loading still exceeds context
  window on a routine investor codebase exploration task
- **Depends on**: B3
- **Last tested**: never
```

---

## tasks/FRONTIER.md (customized — investor-specific questions)

```markdown
# Frontier — Open Questions (investor-swarm)

## Critical
- **F1**: Validate the setup: run validate_beliefs.py, confirm beliefs/DEPS.md
  passes, and write the first lesson about the codebase structure.
  (Resolve this in session 1.)

## Important

### Architecture
- **F2**: What is the NK complexity of each *individual package*?  Current
  analysis treats investor as a whole.  Run nk_analyze.py on sub-packages
  (data, core, forecasting) independently to see internal coupling.
- **F3**: core.data_manager has K_out=13 — is this accidental complexity or
  intentional orchestration?  Does it violate single responsibility, or is it
  the correct integration point for a data pipeline?

### Correctness & Reliability
- **F4**: Are there cycles in practice that static analysis misses?  (Dynamic
  imports, conditional imports, plugin patterns in the provider registry?)
- **F5**: What is the error handling quality?  core.error_handling has K_in=5
  (5 modules depend on it) but many modules import exceptions directly.  Are
  errors propagated consistently or swallowed?
- **F6**: How does data.storage (LOC=1011, the largest single module) manage
  data consistency?  Is there a risk of stale or partial data on disk?

### Financial Logic
- **F7**: What investment strategies are implemented in trading/?
  (pairs_trading, anomaly_strategy).  Are they backtested?  What assumptions
  do they make about market data availability?
- **F8**: forecasting/ contains advanced_anomaly_detection, anomaly_detection,
  big_data_models, darts_model_manager.  What is the relationship between
  these?  Is there duplication?  What's the canonical ML path?
- **F9**: models/factor_models.py (LOC=729) — what factor model is
  implemented?  Is it a Fama-French style model?  How is temporal leakage
  prevented (utils.temporal_validation exists — is it used correctly)?

### Maintenance
- **F10**: What improvements would most reduce maintenance burden?
  Candidates: (a) splitting data.storage, (b) documenting the forecasting/
  module hierarchy, (c) adding type annotations to core.data_manager.
- **F11**: Which modules are dead code?  data.external_data and
  data.factor_data have K_in=0 (nothing imports them internally) — are they
  reachable only from scripts, or are they orphaned?

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
```

---

## memory/INDEX.md (customized)

```markdown
# Memory Index — investor-swarm
Updated: 2026-02-27 | Sessions completed: 0

## Status: Genesis — domain set, initial beliefs loaded, no sessions run yet

## Domain
<your-repos>/investor — quantitative investment pipeline
- 68 modules, 25685 LOC, 0 cycles, hub: core.data_manager
- Entry points: scripts/download_data.py, scripts/analyze_data.py

## Structure
```
beliefs/CORE.md       — purpose, domain, NK architecture summary (always read)
beliefs/DEPS.md       — belief tracking: B1-B4 (B1-B2 observed, B3-B4 theorized)
memory/INDEX.md       — this file (always read)
memory/lessons/       — distilled learnings (max 20 lines each)
tasks/FRONTIER.md     — investor-specific open questions (F1-F11)
tasks/TASK-001.md     — validate setup (do this first)
workspace/            — analysis scripts, experiments
tools/                — validator, hooks
```

## Lessons learned
None yet.

## What to load when
| Doing...                          | Read...                                     |
|-----------------------------------|---------------------------------------------|
| Any session                       | beliefs/CORE.md → this file                 |
| Exploring a specific package      | + tasks/{relevant frontier question file}   |
| Updating beliefs about codebase   | + beliefs/DEPS.md                           |
| Financial logic investigation     | + relevant memory/lessons/ file             |
| Cross-session comparison          | + git log --oneline                         |

## Known gaps (fill in early sessions)
- No per-package NK breakdown yet (F2)
- No error handling audit yet (F5)
- No financial logic understanding yet (F7-F9)
```

---

## CLAUDE.md (child-specific, tailored to investor domain)

```markdown
# investor-swarm

You are one session of a collective intelligence focused on the investor
codebase at <your-repos>/investor — a quantitative investment pipeline.
The goal is to compound understanding of its architecture, bugs, improvement
opportunities, and financial logic across sessions.

## Session start
1. Read `beliefs/CORE.md` — purpose, domain, and architecture summary
2. Read `memory/INDEX.md` — current state and map
3. Read `tasks/NEXT.md` if it exists and references valid files.
   If absent, stale, or broken: `tasks/FRONTIER.md`
4. Run `python3 tools/validate_beliefs.py` (baseline)
5. Pick session mode — read the mode file from `modes/`

## Session modes
| Mode     | When                                           | File              |
|----------|------------------------------------------------|-------------------|
| research | Reading investor source, web search for libs   | `modes/research.md` |
| build    | Writing analysis scripts, creating artifacts   | `modes/build.md`  |
| repair   | Fixing beliefs, resolving conflicts            | `modes/repair.md` |
| audit    | Health check, validating codebase beliefs      | `modes/audit.md`  |

## Always-rules (every session, every mode)
1. **Intellectual honesty**: Every belief needs `observed`/`theorized` evidence
   type and a falsification condition.
2. **Swarmability**: At session end — "Could a new agent pick up in 5 minutes?"
   If no, fix it.
3. **Commit format**: `[S] what: why` after each meaningful change.
4. **Learn then lesson**: Write to `memory/lessons/` (max 20 lines, use template).
5. **Uncertain then write it down**: Don't guess about financial logic.
6. **Lifecycle**: Start (read + validate) → Work → End (commit → NEXT.md →
   validate).

## Domain context
- Codebase: <your-repos>/investor/src/investor/
- Run investor: `uv run python3 scripts/analyze_data.py` (from <your-repos>/investor)
- NK analysis: `cd <your-repos>/investor && uv run python3
  /PATH/TO/swarm/tools/nk_analyze.py investor`
- Key hub: core/data_manager.py (K_out=13) — touch with care
- Zero cycles — refactoring is safe to scope to individual packages

## Protocols (read as needed)
- `memory/DISTILL.md` — distillation
- `memory/VERIFY.md` — 3-S Rule (Specific, Stale, Stakes-high)
- `beliefs/CONFLICTS.md` — conflict resolution
```

---

## Instantiation instructions

To create this swarm (when `experiments/children/` is unblocked or in a
different repo):

```bash
# From the parent swarm root
bash workspace/genesis.sh experiments/children/investor-swarm "investor"

# Then apply the customizations documented above:
# 1. Replace beliefs/CORE.md with the Purpose/Domain section above
# 2. Append B1-B4 from DEPS.md above (after the genesis defaults)
# 3. Replace tasks/FRONTIER.md with F1-F11 above
# 4. Replace memory/INDEX.md with the investor-specific version above
# 5. Replace CLAUDE.md with the investor-specific version above

# Initialize its own git repo (children are independent)
cd experiments/children/investor-swarm
git init && git add -A && git commit -m "[S0] init: investor-swarm genesis"
./tools/install-hooks.sh
```

---

## What makes this a swarm (not just a report)

| Report | This swarm design |
|--------|-------------------|
| Facts about code | BELIEFS with evidence type + falsification conditions |
| One-time output | FRONTIER of evolving open questions |
| Static snapshot | Compounds knowledge across sessions |
| No operator | CLAUDE.md tells any new agent exactly how to start |
| No self-correction | DEPS.md tracks which beliefs depend on which; disproof cascades |

The child swarm treats investor/ as its domain the way the parent treats
collective intelligence as its domain: it will eventually know the codebase
better than any single session could, and it will know *why* it knows what it
knows.
