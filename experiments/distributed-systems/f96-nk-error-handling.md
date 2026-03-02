# F96: Does NK complexity predict error handling quality?

## Question
If B13 (error handling dominates failures) and B9 (NK predictive power) are both true, do high-cycle modules have disproportionately bad error paths?

## Method
1. NK analysis on redis-py and celery (distributed systems Python packages)
2. Classified modules into HIGH-CYCLE (appearing in multiple import cycles) and LOW-CYCLE (zero cycles)
3. Counted error handling patterns per module:
   - Broad catches: `except:` or `except Exception:` (BAD)
   - Swallowed exceptions: catch + log/pass only, no recovery (BAD)
   - TODO/FIXME in error paths (BAD)
   - Proper handling: specific types, re-raise with context, retry/fallback (GOOD)
4. Quality score = proper / total_try_except

## Results

### redis-py (N=111, 95 cycles, composite=569)

| Group | Modules | Avg Quality | Total Blocks | Broad | Swallowed |
|-------|---------|-------------|--------------|-------|-----------|
| HIGH-CYCLE | 7 | **0.391** | 163 | 28 (17%) | 35 (21%) |
| LOW-CYCLE | 4* | **0.908** | 13 | 0 (0%) | 1 (8%) |

*4 of 7 low-cycle modules had try/except blocks

**Delta: 0.517 (2.3x). Strong effect.**

Worst: cache.py (0.000, 1 block swallowed), client.py (0.267, 7 broad catches)
Best outlier: asyncio/connection.py (0.714 despite many cycles — enforced `raise X from exc` convention)

### celery (N=161, 30 cycles, composite=649)

| Group | Modules | Avg Quality | Total Blocks | Broad | Swallowed |
|-------|---------|-------------|--------------|-------|-----------|
| HIGH-CYCLE | 7 | **0.724** | 64 | 20 (31%) | 13 (20%) |
| LOW-CYCLE | 7 | **0.842** | 53 | 8 (15%) | 8 (15%) |

**Delta: 0.118 (1.16x). Moderate effect.**

Worst: backends/base.py (0.462, 26 blocks, 10 broad catches — chord error handling)
Best outlier: _state.py and app/task.py (both 1.000 despite high cycles — small modules)

## Analysis

### Direction: Consistent
Both packages show high-cycle modules with worse error handling. Effect is always in the predicted direction.

### Magnitude: Scales with tangledness
- redis-py (95 cycles): 2.3x difference
- celery (30 cycles): 1.16x difference
- More cycles → stronger effect

### Mechanism
Tangled modules face complexity pressure from multiple callers/call paths. This leads to:
1. **Broad catches as defensive programming** — when you can't predict all callers, catch everything
2. **Swallowed exceptions in cleanup paths** — teardown code in tangled modules can't propagate safely
3. **Import cycle pressure** — can't import specific exception types from entangled modules
4. **Cleanup-only except blocks** — `except Exception: pass` in `__del__`, `finally`, disconnect paths

### Outliers (important caveats)
- asyncio/connection.py (high-cycle, 0.714): Discipline enforced via consistent `raise X from exc` convention
- _state.py, app/task.py (high-cycle, 1.000): Small modules with few except blocks
- beat.py (low-cycle, 0.625): Scheduler has complexity pressure from time-based failure modes

### Relationship to B9 and B13
This is a **cross-domain connection**: B9 (NK predicts maintenance burden) + B13 (error handling dominates failures) → cycle count predicts error handling quality. The implication: NK analysis can prioritize error handling audits. Audit high-cycle modules first.

## Answer
**YES** — NK cycle count predicts error handling quality. Effect is directionally consistent across 2 packages (2.3x in redis-py, 1.16x in celery). Scales with total cycle count. Not deterministic — discipline can override (asyncio/connection.py).

## Sources
- redis-py 7.2.1 NK analysis + manual error handling classification
- celery 5.6.2 NK analysis + manual error handling classification
- Yuan et al. OSDI 2014 (error handling anti-pattern framework)
