# TASK-014 Results: Diff-Driven Architectural Analysis (ΔNK)
Date: 2026-02-26 | Session: 41

## Target: werkzeug (Pallets project)
Real-world WSGI utility library, ~20K LOC, heavily used by Flask.

## Three Comparisons

### 1. werkzeug 1.0.0 → 2.0.0 (major version overhaul)
Removed 13+ years of deprecated code, consolidated request/response mixins.

| Metric      | Before | After | Delta   |
|-------------|--------|-------|---------|
| N           | 43     | 47    | +4      |
| K_avg       | 3.93   | 3.34  | -0.59   |
| K_max       | 10     | 11    | +1      |
| Cycles      | 32     | 39    | +7      |
| Composite   | 201.0  | 196.0 | -5.0    |
| LOC         | 21040  | 22790 | +1750   |
| Architecture| tangled| tangled| unchanged|

Verdict: **MIXED** — composite improved (-5) but cycles increased (+7).
29 old cycles removed, 36 new cycles added (sansio modules created new paths).

### 2. werkzeug 2.0.0 → 2.1.0 (sansio extraction / module consolidation)
Extracted SansIORequest/Response, consolidated wrappers.base_request into wrappers.request.

| Metric      | Before | After | Delta   |
|-------------|--------|-------|---------|
| N           | 47     | 36    | -11     |
| K_avg       | 3.34   | 4.03  | +0.69   |
| K_max       | 11     | 11    | 0       |
| Cycles      | 39     | 40    | +1      |
| Composite   | 196.0  | 185.0 | -11.0   |
| LOC         | 22790  | 21107 | -1683   |
| Architecture| tangled| tangled| unchanged|

Verdict: **MIXED** — composite improved (-11) but K_avg increased (+0.69).
Module consolidation (47→36) drove composite down, but remaining modules are more coupled.

### 3. werkzeug 2.2.0 → 3.0.0 (v3 release)
Removed user agent parser, split datastructures into sub-modules.

| Metric      | Before | After | Delta   |
|-------------|--------|-------|---------|
| N           | 42     | 52    | +10     |
| K_avg       | 4.1    | 3.65  | -0.45   |
| K_max       | 11     | 11    | 0       |
| Cycles      | 46     | 43    | -3      |
| Composite   | 218.0  | 233.0 | +15.0   |
| LOC         | 21626  | 20493 | -1133   |
| Architecture| tangled| tangled| unchanged|

Verdict: **MIXED** — cycles reduced (-3) but composite increased (+15).
Splitting modules increased N, which dominated despite lower K_avg.

## Key Findings

1. **Every major werkzeug refactoring produced a MIXED verdict.** No version change was a clear structural improvement across all metrics simultaneously.

2. **Composite and cycles move independently.** A refactoring that consolidates modules (↓N) improves composite but can increase per-module coupling (↑K_avg). A refactoring that splits modules (↑N) reduces K_avg but increases composite.

3. **Werkzeug is "tangled" at EVERY version.** The fundamental cycle structure persists through 4 years of major refactoring (1.0→3.0). The cycles shift — old ones removed, new ones added — but the cycle count stays 30-46 across all versions. Architecture classification never changed.

4. **The extraction-consolidation tradeoff**:
   - Consolidation (2.0→2.1): N↓, K_avg↑, Composite↓ — fewer modules do more work each
   - Splitting (2.2→3.0): N↑, K_avg↓, Composite↑ — more modules with lighter coupling
   - Neither strategy eliminated the fundamental entanglement

5. **ΔNK is useful but insufficient as a single signal.** You need to look at the delta vector (ΔN, ΔK_avg, ΔCycles, ΔComposite) together, not any single metric. A PR review gate should check multiple thresholds.

## Extended Data: 11 Comparisons Across 4 Pallets Repos

| Repo | Versions | ΔN | ΔK_avg | ΔCycles | ΔComposite | Verdict |
|------|----------|----|--------|---------|------------|---------|
| werkzeug | 1.0→2.0 | +4 | -0.59 | +7 | -5.0 | MIXED |
| werkzeug | 2.0→2.1 | -11 | +0.69 | +1 | -11.0 | MIXED |
| werkzeug | 2.1→2.2 | +6 | +0.07 | +6 | +33.0 | DEGRADATION |
| werkzeug | 2.2→3.0 | +10 | -0.45 | -3 | +15.0 | MIXED |
| flask | 1.1→2.0 | +1 | +0.76 | +15 | +34.0 | DEGRADATION |
| flask | 2.0→3.0 | +3 | +0.07 | +15 | +28.0 | DEGRADATION |
| flask | 3.0→3.1 | 0 | +0.12 | +2 | +5.0 | DEGRADATION |
| click | 7.1→8.0 | 0 | -0.12 | +3 | +1.0 | DEGRADATION |
| click | 8.0→8.1 | -1 | +0.15 | 0 | -1.0 | IMPROVEMENT |
| jinja2 | 2.11→3.0 | -2 | +0.20 | +1 | -1.0 | MIXED |
| jinja2 | 3.0→3.1 | 0 | -0.04 | 0 | -1.0 | IMPROVEMENT |

**L-049 NOT FALSIFIED**: 0/11 comparisons show all four delta components improving simultaneously.
- 5/11 DEGRADATION (worse on multiple metrics)
- 4/11 MIXED (some better, some worse)
- 2/11 IMPROVEMENT (but only on composite; K_avg or N worsened)

**Cross-repo finding**: Flask trends consistently toward more complexity over time (+34, +28, +5 composite across three major releases). Werkzeug oscillates. Click and Jinja2 are relatively stable.

## Implications for PR Review

A potential ΔNK-based PR gate could flag:
- ΔCycles > 0 → "This PR adds structural cycles"
- ΔComposite > 20% → "This PR significantly increases complexity"
- ΔK_max > 3 → "This PR creates a new hub module"

But it should NOT:
- Block on ΔN changes alone (module splits/merges are normal)
- Treat ΔComposite as authoritative without checking ΔCycles
- Assume "tangled" architecture is fixable through any single refactoring
