# F111 Test 2 — Builder Proposal: complexity_ising_idea Refactoring
Session: S73b+ | Date: 2026-02-27 | Status: PROPOSAL (read-only per HQ-2)

## Target
`<your-repos>/complexity_ising_idea/` — 12,251 lines Python.
Ising model + Effective Information research. 7 src/ modules, 18 experiment scripts, 2 test files.

## Problem: Hidden coupling via copy-paste (L-143)
Formal NK: K_avg=0 (no import cycles). Actual coupling: severe. Three functions are
duplicated across experiment files, creating inconsistency-propagation risk.

| Function | Copies | Lines/copy | Total waste | Destination |
|----------|--------|------------|-------------|-------------|
| `config_to_patch_states` | 11 identical + 2 variants | ~20 | ~220 | `src/coarse_grain.py` |
| `compute_ei_equalized` | 6 identical + 2 variants | ~45 | ~270 | `src/ei_compute.py` |
| `compute_patch_autocorrelation` | 2 identical | ~10 | ~20 | `src/analysis.py` |
| **Total** | **21 duplicates** | | **~510 lines** | |

510 lines = 4.2% of codebase is pure duplication.

## Proposed changes (4 steps)

### Step 1: Extract functions to src/

**src/coarse_grain.py** — add after existing `coarsegrain_timeseries`:
```python
def config_to_patch_states(configs, patch_size):
    """Extract non-overlapping patches and encode as integers."""
    # Use the vectorized 2D implementation from phase1_v4_falsification.py
    # (identical output to loop version, 10-50x faster on large grids)
    N, L, _ = configs.shape
    p = patch_size
    n_p = L // p
    n_patches = n_p * n_p
    n_bits = p * p
    n_states = 2 ** n_bits
    patches = configs.reshape(N, n_p, p, n_p, p).transpose(0, 1, 3, 2, 4)
    patches = patches.reshape(N, n_patches, n_bits)
    bits = ((patches + 1) // 2).astype(np.int32)
    powers = (1 << np.arange(n_bits - 1, -1, -1)).astype(np.int32)
    states = (bits * powers).sum(axis=2)
    return states, n_states, n_patches

def config_to_patch_states_1d(configs, patch_size):
    """Extract patches from 1D chain and encode as integers."""
    N, L = configs.shape
    n_patches = L // patch_size
    n_bits = patch_size
    n_states = 2 ** n_bits
    patches = configs[:, :n_patches * patch_size].reshape(N, n_patches, n_bits)
    bits = ((patches + 1) // 2).astype(np.int32)
    powers = (1 << np.arange(n_bits - 1, -1, -1)).astype(np.int32)
    states = (bits * powers).sum(axis=2)
    return states, n_states, n_patches
```

**src/ei_compute.py** — add `compute_ei_equalized` (the shared core algorithm):
```python
def compute_ei_equalized(configs_raw, configs_coarse, patch_size, min_obs, rng):
    """Compute EI at micro and macro scales with equalized transition counts."""
    # Body from phase1_v3_ising.py:51-96 (canonical implementation)
    # Uses config_to_patch_states, estimate_transition_matrix, effective_information
    ...
```

**src/analysis.py** — add `compute_patch_autocorrelation`:
```python
def compute_patch_autocorrelation(configs, patch_size):
    """Fraction of patches unchanged between consecutive steps."""
    from src.coarse_grain import config_to_patch_states
    states, _, _ = config_to_patch_states(configs, patch_size)
    if states.shape[0] < 2:
        return 0.0
    return (states[:-1] == states[1:]).astype(np.float64).mean()
```

### Step 2: Update 15 experiment files
Replace local function definitions with imports:
```python
from src.coarse_grain import config_to_patch_states  # was: def config_to_patch_states...
from src.ei_compute import compute_ei_equalized       # was: def compute_ei_equalized...
```

Files to update:
- phase1_ising.py, phase1_v2_ising.py, phase1_v3_ising.py, phase1_v3b_multiblock.py
- phase1_v3c_shuffle_control.py, phase1_v3d_diagnostics.py
- phase1_v4_analytical_ei.py, phase1_v4_falsification.py (keep _1d, import _2d as alias)
- phase1_v4_finite_size.py, phase1_v4_wolff_fair.py
- phase1_p0_analytical_ei.py, phase1_p0_rolling_ews.py, phase1_p1_comparison.py
- wolff_validation.py

### Step 3: Add pyproject.toml
```toml
[project]
name = "complexity-ising"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = ["numpy>=1.20", "matplotlib>=3.0", "scipy>=1.7"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Step 4: Convert tests to pytest
- Remove `sys.path.insert` hacks from test files
- Replace manual `print(PASS/FAIL)` with `assert` statements
- Remove `if __name__ == "__main__"` blocks from test_coarse_grain (already in src/)
- Run with `python -m pytest tests/`

## Impact
- **Lines removed**: ~510 (duplication)
- **Lines added**: ~80 (extracted functions + pyproject.toml)
- **Net**: ~430 lines fewer, same functionality
- **NK change**: K_avg rises from 0 to ~0.3 (experiment files now depend on src/),
  but this is REAL coupling replacing HIDDEN coupling — better for maintenance
- **Inconsistency risk**: eliminated. Single source of truth for each algorithm.

## Risk
- Experiment files are historical records (v1→v5 methodology evolution). Modifying
  them could break reproducibility if any copy had a subtle variation.
  **Mitigation**: the analysis confirms all 11 copies of config_to_patch_states are
  identical. All 6 copies of compute_ei_equalized are identical. Safe to extract.
- phase1_v4_falsification.py has intentionally different variants (_2d, _1d, _from_states).
  These should be extracted as separate functions, not merged.

## Evidence for F111
This proposal demonstrates the full F111 builder pattern:
1. **Analyze**: NK + code quality (L-143, S72+)
2. **Diagnose**: 3 duplicated functions, 21 total copies, 510 wasted lines
3. **Propose**: 4-step refactoring with exact code and file lists
4. **Predict impact**: -430 lines, K_avg 0→0.3 (honest coupling), eliminated inconsistency risk

Fix phase not applied (read-only per HQ-2). Human can apply via branch or approve modification.
