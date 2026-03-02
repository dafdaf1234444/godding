"""
Phase 1 v4: Fair Comparison — Is Metropolis Emergence from Autocorrelation?

THE CHALLENGE: With Metropolis dynamics, EI(M)/EI(S) peaks at ~6.0 at T=2.15.
With Wolff dynamics, it's ~0.89. Is the Metropolis signal real physics or just
temporal autocorrelation from highly correlated consecutive samples?

KEY INSIGHT: The comparison in v3 is UNFAIR:
  - Metropolis "step" = 10 sweeps = 5760 single-spin flip attempts
  - Wolff "step" = 1 cluster flip
These produce DIFFERENT amounts of decorrelation between consecutive samples.
Metropolis near T_c has autocorrelation ~0.65 between steps; Wolff has ~0.37.

TWO COMPLEMENTARY TESTS:

TEST 1 — METROPOLIS THINNING (constant total sweeps, variable #samples)
  Total sweeps = 20000. More thinning => fewer but more decorrelated samples.
  If EI ratio drops with thinning, the signal is correlated-sample artifact.
  NOTE: this confounds autocorrelation with sample count. Test 2 fixes that.

TEST 2 — FIXED SAMPLES, VARIABLE THINNING (the definitive test)
  Always collect exactly 200 samples (same #transitions for EI estimation).
  Vary thinning: 10, 25, 50, 100, 200 sweeps per sample.
  More thinning = more total sweeps = slower, but ONLY autocorrelation changes.
  This isolates the autocorrelation effect from the sample-count effect.

TEST 3 — WOLFF THINNING LADDER
  Same approach with Wolff: vary cluster flips per sample while keeping
  total samples constant at 200. Check if Wolff ever shows emergence.

TEST 4 — AUTOCORRELATION vs EI RATIO SCATTER
  Combine all conditions and show the functional relationship.
"""

import sys
import os
import time
import numpy as np
from datetime import datetime
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.coarse_grain import coarsegrain_timeseries, config_to_patch_states
from src.ei_compute import estimate_transition_matrix, effective_information, compute_ei_equalized
from src.analysis import compute_patch_autocorrelation


# =========================================================================
# Helper functions
# =========================================================================


def compute_mag_autocorrelation(mags, lag=1):
    """Compute lag-k autocorrelation of magnetization time series."""
    if len(mags) < lag + 2:
        return 0.0
    x = mags[:-lag]
    y = mags[lag:]
    mx, my = x.mean(), y.mean()
    sx, sy = x.std(), y.std()
    if sx < 1e-15 or sy < 1e-15:
        return 0.0
    return np.mean((x - mx) * (y - my)) / (sx * sy)


def simulate_metropolis(L, T, n_samples, sweeps_per_sample, n_equilib, seed=42):
    """
    Simulate Ising model with Metropolis dynamics and custom thinning.

    Parameters
    ----------
    L : int
        Lattice side length.
    T : float
        Temperature.
    n_samples : int
        Number of configurations to record.
    sweeps_per_sample : int
        Number of Metropolis sweeps between recorded configurations.
    n_equilib : int
        Equilibration sweeps.
    seed : int
        Random seed.

    Returns
    -------
    configs : ndarray of shape (n_samples, L, L)
    magnetizations : ndarray of shape (n_samples,)
    """
    rng = np.random.RandomState(seed)
    N = L * L
    grid = np.ones((L, L), dtype=np.int8)

    beta = 1.0 / T
    boltzmann = {}
    for dE in [-8, -4, 0, 4, 8]:
        boltzmann[dE] = min(1.0, np.exp(-dE * beta))

    def sweep(grid, rng):
        rows = rng.randint(0, L, size=N)
        cols = rng.randint(0, L, size=N)
        thresholds = rng.random(size=N)
        for k in range(N):
            i, j = rows[k], cols[k]
            s = grid[i, j]
            neighbors = (
                grid[(i + 1) % L, j]
                + grid[(i - 1) % L, j]
                + grid[i, (j + 1) % L]
                + grid[i, (j - 1) % L]
            )
            dE = 2 * s * neighbors
            if thresholds[k] < boltzmann[dE]:
                grid[i, j] = -s

    # Equilibration
    for _ in range(n_equilib):
        sweep(grid, rng)

    # Sampling
    configs = np.empty((n_samples, L, L), dtype=np.int8)
    magnetizations = np.empty(n_samples, dtype=np.float64)

    for step in range(n_samples):
        for _ in range(sweeps_per_sample):
            sweep(grid, rng)
        configs[step] = grid.copy()
        magnetizations[step] = np.abs(grid.sum()) / N

    return configs, magnetizations


def simulate_wolff(L, T, n_samples, flips_per_sample, n_equilib, seed=42):
    """
    Simulate Ising model with Wolff dynamics and custom thinning.

    Parameters
    ----------
    L : int
        Lattice side length.
    T : float
        Temperature.
    n_samples : int
        Number of configurations to record.
    flips_per_sample : int
        Number of Wolff cluster flips between recorded configurations.
    n_equilib : int
        Equilibration cluster flips.
    seed : int
        Random seed.

    Returns
    -------
    configs : ndarray of shape (n_samples, L, L)
    magnetizations : ndarray of shape (n_samples,)
    """
    rng = np.random.RandomState(seed)
    N = L * L
    grid = np.ones((L, L), dtype=np.int8)

    p_add = 1.0 - np.exp(-2.0 / T)
    neighbor_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def wolff_step(grid, rng):
        si = rng.randint(0, L)
        sj = rng.randint(0, L)
        seed_spin = grid[si, sj]
        visited = np.zeros((L, L), dtype=np.bool_)
        queue = deque()
        queue.append((si, sj))
        visited[si, sj] = True
        cluster_sites = [(si, sj)]
        while queue:
            ci, cj = queue.popleft()
            for di, dj in neighbor_offsets:
                ni = (ci + di) % L
                nj = (cj + dj) % L
                if not visited[ni, nj] and grid[ni, nj] == seed_spin:
                    if rng.random() < p_add:
                        visited[ni, nj] = True
                        queue.append((ni, nj))
                        cluster_sites.append((ni, nj))
        for fi, fj in cluster_sites:
            grid[fi, fj] = -seed_spin

    # Equilibration
    for _ in range(n_equilib):
        wolff_step(grid, rng)

    # Sampling
    configs = np.empty((n_samples, L, L), dtype=np.int8)
    magnetizations = np.empty(n_samples, dtype=np.float64)

    for step in range(n_samples):
        for _ in range(flips_per_sample):
            wolff_step(grid, rng)
        configs[step] = grid.copy()
        magnetizations[step] = np.abs(grid.sum()) / N

    return configs, magnetizations


# =========================================================================
# MAIN EXPERIMENT
# =========================================================================

def run_v4():
    """Execute v4 fair Wolff comparison."""

    project_root = os.path.join(os.path.dirname(__file__), '..')
    log_dir = os.path.join(project_root, 'results', 'phase1')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'v4_wolff_fair_output.log')

    class Tee:
        def __init__(self, filepath):
            self.terminal = sys.stdout
            self.log = open(filepath, 'w')
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
        def flush(self):
            self.terminal.flush()
            self.log.flush()
        def close(self):
            self.log.close()

    tee = Tee(log_path)
    old_stdout = sys.stdout
    sys.stdout = tee

    try:
        _run_inner(project_root)
    finally:
        sys.stdout = old_stdout
        tee.close()
        print(f"\nFull output saved to: {log_path}")


def _run_inner(project_root):
    """Inner function that does all the work."""

    total_start = time.time()

    print("=" * 78)
    print("PHASE 1 v4: FAIR WOLFF COMPARISON")
    print("Is the Metropolis EI emergence signal from temporal autocorrelation?")
    print("=" * 78)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ======================================================================
    # PARAMETERS
    # ======================================================================
    L = 24
    T_target = 2.15
    T_c = 2.269
    block_size = 4
    patch_size = 2
    min_obs = 5
    n_seeds = 5
    n_equilib = 3000  # Reduced for speed; still adequate at T~2.15

    # --- TEST 1: Constant total sweeps, variable samples ---
    test1_total_sweeps = 10000
    test1_metro_thin = [10, 50, 100, 500]
    # Steps: 1000, 200, 100, 20

    # --- TEST 2 (THE DEFINITIVE TEST): Fixed 200 samples, variable thinning ---
    test2_n_samples = 200
    test2_metro_thin = [5, 10, 25, 50, 100]
    # Total sweeps: 1000, 2000, 5000, 10000, 20000

    # --- TEST 3: Wolff with fixed 200 samples, variable thinning ---
    test3_n_samples = 200
    test3_wolff_thin = [1, 3, 5, 10, 20]
    # Total flips: 200, 600, 1000, 2000, 4000

    print(f"\nParameters:")
    print(f"  L={L}, T={T_target}, T_c={T_c}")
    print(f"  block_size={block_size}, patch_size={patch_size}, min_obs={min_obs}")
    print(f"  n_seeds={n_seeds}, n_equilib={n_equilib}")
    print(f"\n  TEST 1: Total sweeps = {test1_total_sweeps}")
    print(f"    Thinning levels: {test1_metro_thin}")
    print(f"    Sample counts: {[test1_total_sweeps // t for t in test1_metro_thin]}")
    print(f"\n  TEST 2: Fixed {test2_n_samples} samples")
    print(f"    Thinning levels: {test2_metro_thin}")
    print(f"    Total sweeps: {[test2_n_samples * t for t in test2_metro_thin]}")
    print(f"\n  TEST 3: Fixed {test3_n_samples} samples (Wolff)")
    print(f"    Thinning levels: {test3_wolff_thin}")
    print(f"    Total flips: {[test3_n_samples * t for t in test3_wolff_thin]}")

    # ======================================================================
    # TEST 1: CONSTANT TOTAL SWEEPS
    # ======================================================================
    print("\n\n" + "=" * 78)
    print("TEST 1: METROPOLIS — Constant Total Sweeps, Variable Thinning")
    print("(Confounds autocorrelation with sample count)")
    print("=" * 78)

    n_cond1 = len(test1_metro_thin)
    t1_ei_ratio = np.full((n_seeds, n_cond1), np.nan)
    t1_ei_micro = np.zeros((n_seeds, n_cond1))
    t1_ei_macro = np.zeros((n_seeds, n_cond1))
    t1_patch_ac = np.zeros((n_seeds, n_cond1))
    t1_mag_ac = np.zeros((n_seeds, n_cond1))
    t1_n_trans = np.zeros((n_seeds, n_cond1), dtype=int)

    for ci, thin in enumerate(test1_metro_thin):
        n_samp = test1_total_sweeps // thin
        t0 = time.time()
        print(f"\n--- Metro thin={thin}, n_samples={n_samp} ---", flush=True)

        for s in range(n_seeds):
            seed = 10000 * s + ci + 40000
            configs, mags = simulate_metropolis(
                L, T_target, n_samp, thin, n_equilib, seed=seed)
            coarse = coarsegrain_timeseries(configs, block_size)

            t1_patch_ac[s, ci] = compute_patch_autocorrelation(configs, patch_size)
            t1_mag_ac[s, ci] = compute_mag_autocorrelation(mags)

            rng = np.random.RandomState(seed + 88888)
            ei_s, ei_m, n_tr, *_ = compute_ei_equalized(
                configs, coarse, patch_size, min_obs, rng)
            t1_ei_micro[s, ci] = ei_s
            t1_ei_macro[s, ci] = ei_m
            t1_ei_ratio[s, ci] = ei_m / ei_s if ei_s > 1e-10 else np.nan
            t1_n_trans[s, ci] = n_tr

        elapsed = time.time() - t0
        mr = np.nanmean(t1_ei_ratio[:, ci])
        se = np.nanstd(t1_ei_ratio[:, ci]) / np.sqrt(n_seeds)
        pac = t1_patch_ac[:, ci].mean()
        mac = t1_mag_ac[:, ci].mean()
        print(f"  Ratio={mr:.3f}+/-{se:.3f}, PatchAC={pac:.4f}, MagAC={mac:.4f}, "
              f"trans={t1_n_trans[:, ci].mean():.0f}, {elapsed:.1f}s")

    # Summary
    print(f"\n{'='*78}")
    print("TEST 1 SUMMARY")
    print(f"{'='*78}")
    print(f"  {'thin':>6s}  {'n_samp':>7s}  {'EI_ratio':>10s}  {'SE':>8s}  "
          f"{'PatchAC':>9s}  {'MagAC':>8s}  {'n_trans':>8s}")
    print("  " + "-" * 66)
    for ci, thin in enumerate(test1_metro_thin):
        n_samp = test1_total_sweeps // thin
        mr = np.nanmean(t1_ei_ratio[:, ci])
        se = np.nanstd(t1_ei_ratio[:, ci]) / np.sqrt(n_seeds)
        pac = t1_patch_ac[:, ci].mean()
        mac = t1_mag_ac[:, ci].mean()
        ntr = t1_n_trans[:, ci].mean()
        print(f"  {thin:6d}  {n_samp:7d}  {mr:10.4f}  {se:8.4f}  "
              f"{pac:9.4f}  {mac:8.4f}  {ntr:8.0f}")

    # ======================================================================
    # TEST 2: FIXED SAMPLES, VARIABLE THINNING (THE KEY TEST)
    # ======================================================================
    print("\n\n" + "=" * 78)
    print("TEST 2: METROPOLIS — Fixed 200 Samples, Variable Thinning")
    print("THE DEFINITIVE TEST: only autocorrelation varies, not sample count")
    print("=" * 78)

    n_cond2 = len(test2_metro_thin)
    t2_ei_ratio = np.full((n_seeds, n_cond2), np.nan)
    t2_ei_micro = np.zeros((n_seeds, n_cond2))
    t2_ei_macro = np.zeros((n_seeds, n_cond2))
    t2_patch_ac = np.zeros((n_seeds, n_cond2))
    t2_mag_ac = np.zeros((n_seeds, n_cond2))
    t2_n_trans = np.zeros((n_seeds, n_cond2), dtype=int)

    for ci, thin in enumerate(test2_metro_thin):
        t0 = time.time()
        print(f"\n--- Metro thin={thin}, n_samples={test2_n_samples}, "
              f"total_sweeps={test2_n_samples * thin} ---", flush=True)

        for s in range(n_seeds):
            seed = 10000 * s + ci + 50000
            configs, mags = simulate_metropolis(
                L, T_target, test2_n_samples, thin, n_equilib, seed=seed)
            coarse = coarsegrain_timeseries(configs, block_size)

            t2_patch_ac[s, ci] = compute_patch_autocorrelation(configs, patch_size)
            t2_mag_ac[s, ci] = compute_mag_autocorrelation(mags)

            rng = np.random.RandomState(seed + 88888)
            ei_s, ei_m, n_tr, *_ = compute_ei_equalized(
                configs, coarse, patch_size, min_obs, rng)
            t2_ei_micro[s, ci] = ei_s
            t2_ei_macro[s, ci] = ei_m
            t2_ei_ratio[s, ci] = ei_m / ei_s if ei_s > 1e-10 else np.nan
            t2_n_trans[s, ci] = n_tr

        elapsed = time.time() - t0
        mr = np.nanmean(t2_ei_ratio[:, ci])
        se = np.nanstd(t2_ei_ratio[:, ci]) / np.sqrt(n_seeds)
        pac = t2_patch_ac[:, ci].mean()
        mac = t2_mag_ac[:, ci].mean()
        print(f"  Ratio={mr:.3f}+/-{se:.3f}, PatchAC={pac:.4f}, MagAC={mac:.4f}, "
              f"trans={t2_n_trans[:, ci].mean():.0f}, {elapsed:.1f}s")

    # Summary
    print(f"\n{'='*78}")
    print("TEST 2 SUMMARY (DEFINITIVE — same n_samples=200 throughout)")
    print(f"{'='*78}")
    print(f"  {'thin':>6s}  {'sweeps':>7s}  {'EI_ratio':>10s}  {'SE':>8s}  "
          f"{'PatchAC':>9s}  {'MagAC':>8s}  {'n_trans':>8s}")
    print("  " + "-" * 66)
    for ci, thin in enumerate(test2_metro_thin):
        mr = np.nanmean(t2_ei_ratio[:, ci])
        se = np.nanstd(t2_ei_ratio[:, ci]) / np.sqrt(n_seeds)
        pac = t2_patch_ac[:, ci].mean()
        mac = t2_mag_ac[:, ci].mean()
        ntr = t2_n_trans[:, ci].mean()
        print(f"  {thin:6d}  {test2_n_samples * thin:7d}  {mr:10.4f}  {se:8.4f}  "
              f"{pac:9.4f}  {mac:8.4f}  {ntr:8.0f}")

    # ======================================================================
    # TEST 3: WOLFF THINNING LADDER
    # ======================================================================
    print("\n\n" + "=" * 78)
    print("TEST 3: WOLFF — Fixed 200 Samples, Variable Thinning")
    print("=" * 78)

    n_cond3 = len(test3_wolff_thin)
    t3_ei_ratio = np.full((n_seeds, n_cond3), np.nan)
    t3_ei_micro = np.zeros((n_seeds, n_cond3))
    t3_ei_macro = np.zeros((n_seeds, n_cond3))
    t3_patch_ac = np.zeros((n_seeds, n_cond3))
    t3_mag_ac = np.zeros((n_seeds, n_cond3))
    t3_n_trans = np.zeros((n_seeds, n_cond3), dtype=int)

    for ci, thin in enumerate(test3_wolff_thin):
        t0 = time.time()
        print(f"\n--- Wolff thin={thin}, n_samples={test3_n_samples}, "
              f"total_flips={test3_n_samples * thin} ---", flush=True)

        for s in range(n_seeds):
            seed = 10000 * s + ci + 60000
            configs, mags = simulate_wolff(
                L, T_target, test3_n_samples, thin, n_equilib, seed=seed)
            coarse = coarsegrain_timeseries(configs, block_size)

            t3_patch_ac[s, ci] = compute_patch_autocorrelation(configs, patch_size)
            t3_mag_ac[s, ci] = compute_mag_autocorrelation(mags)

            rng = np.random.RandomState(seed + 88888)
            ei_s, ei_m, n_tr, *_ = compute_ei_equalized(
                configs, coarse, patch_size, min_obs, rng)
            t3_ei_micro[s, ci] = ei_s
            t3_ei_macro[s, ci] = ei_m
            t3_ei_ratio[s, ci] = ei_m / ei_s if ei_s > 1e-10 else np.nan
            t3_n_trans[s, ci] = n_tr

        elapsed = time.time() - t0
        mr = np.nanmean(t3_ei_ratio[:, ci])
        se = np.nanstd(t3_ei_ratio[:, ci]) / np.sqrt(n_seeds)
        pac = t3_patch_ac[:, ci].mean()
        mac = t3_mag_ac[:, ci].mean()
        print(f"  Ratio={mr:.3f}+/-{se:.3f}, PatchAC={pac:.4f}, MagAC={mac:.4f}, "
              f"trans={t3_n_trans[:, ci].mean():.0f}, {elapsed:.1f}s")

    # Summary
    print(f"\n{'='*78}")
    print("TEST 3 SUMMARY (Wolff, n_samples=200)")
    print(f"{'='*78}")
    print(f"  {'thin':>6s}  {'flips':>7s}  {'EI_ratio':>10s}  {'SE':>8s}  "
          f"{'PatchAC':>9s}  {'MagAC':>8s}  {'n_trans':>8s}")
    print("  " + "-" * 66)
    for ci, thin in enumerate(test3_wolff_thin):
        mr = np.nanmean(t3_ei_ratio[:, ci])
        se = np.nanstd(t3_ei_ratio[:, ci]) / np.sqrt(n_seeds)
        pac = t3_patch_ac[:, ci].mean()
        mac = t3_mag_ac[:, ci].mean()
        ntr = t3_n_trans[:, ci].mean()
        print(f"  {thin:6d}  {test3_n_samples * thin:7d}  {mr:10.4f}  {se:8.4f}  "
              f"{pac:9.4f}  {mac:8.4f}  {ntr:8.0f}")

    # ======================================================================
    # TEST 4: UNIFIED AUTOCORRELATION vs EI RATIO
    # ======================================================================
    print("\n\n" + "=" * 78)
    print("TEST 4: AUTOCORRELATION vs EI RATIO — Combined Analysis")
    print("=" * 78)

    # Collect all data points from Test 2 (fixed samples) and Test 3 (Wolff)
    all_pac = []
    all_mac = []
    all_ratio = []
    all_labels = []
    all_algo = []

    for ci, thin in enumerate(test2_metro_thin):
        all_pac.append(t2_patch_ac[:, ci].mean())
        all_mac.append(t2_mag_ac[:, ci].mean())
        all_ratio.append(np.nanmean(t2_ei_ratio[:, ci]))
        all_labels.append(f"Metro t={thin}")
        all_algo.append('metro')

    for ci, thin in enumerate(test3_wolff_thin):
        all_pac.append(t3_patch_ac[:, ci].mean())
        all_mac.append(t3_mag_ac[:, ci].mean())
        all_ratio.append(np.nanmean(t3_ei_ratio[:, ci]))
        all_labels.append(f"Wolff t={thin}")
        all_algo.append('wolff')

    all_pac = np.array(all_pac)
    all_mac = np.array(all_mac)
    all_ratio = np.array(all_ratio)
    all_algo = np.array(all_algo)

    from scipy import stats

    finite = np.isfinite(all_ratio) & np.isfinite(all_pac)
    if finite.sum() > 3:
        r_pac, p_pac = stats.pearsonr(all_pac[finite], all_ratio[finite])
        rho_pac, prho_pac = stats.spearmanr(all_pac[finite], all_ratio[finite])
    else:
        r_pac, p_pac, rho_pac, prho_pac = np.nan, np.nan, np.nan, np.nan

    finite2 = np.isfinite(all_ratio) & np.isfinite(all_mac)
    if finite2.sum() > 3:
        r_mac, p_mac = stats.pearsonr(all_mac[finite2], all_ratio[finite2])
        rho_mac, prho_mac = stats.spearmanr(all_mac[finite2], all_ratio[finite2])
    else:
        r_mac, p_mac, rho_mac, prho_mac = np.nan, np.nan, np.nan, np.nan

    print(f"\n  Combined data (Tests 2 + 3, all with n_samples=200):")
    print(f"\n  {'Label':>16s}  {'PatchAC':>9s}  {'MagAC':>8s}  {'EI_ratio':>10s}")
    print("  " + "-" * 48)
    for i in range(len(all_labels)):
        print(f"  {all_labels[i]:>16s}  {all_pac[i]:9.4f}  {all_mac[i]:8.4f}  "
              f"{all_ratio[i]:10.4f}")

    print(f"\n  Correlations (Patch AC vs EI ratio):")
    print(f"    Pearson r    = {r_pac:+.4f} (p = {p_pac:.4e})")
    print(f"    Spearman rho = {rho_pac:+.4f} (p = {prho_pac:.4e})")
    print(f"\n  Correlations (Mag AC vs EI ratio):")
    print(f"    Pearson r    = {r_mac:+.4f} (p = {p_mac:.4e})")
    print(f"    Spearman rho = {rho_mac:+.4f} (p = {prho_mac:.4e})")

    # Matched comparison: find the Metropolis thinning closest to Wolff thin=1
    wolff_t1_pac = t3_patch_ac[:, 0].mean()
    metro_pacs = np.array([t2_patch_ac[:, i].mean() for i in range(n_cond2)])
    best_match = np.argmin(np.abs(metro_pacs - wolff_t1_pac))

    print(f"\n  MATCHED DECORRELATION COMPARISON:")
    print(f"    Wolff thin=1: PatchAC={wolff_t1_pac:.4f}, "
          f"EI ratio={np.nanmean(t3_ei_ratio[:, 0]):.4f}")
    print(f"    Metro thin={test2_metro_thin[best_match]}: "
          f"PatchAC={metro_pacs[best_match]:.4f}, "
          f"EI ratio={np.nanmean(t2_ei_ratio[:, best_match]):.4f}")
    gap = abs(metro_pacs[best_match] - wolff_t1_pac)
    print(f"    PatchAC gap: {gap:.4f}")

    # ======================================================================
    # FINAL VERDICT
    # ======================================================================
    print("\n\n" + "=" * 78)
    print("FINAL ANALYSIS AND VERDICT")
    print("=" * 78)

    # Test 2 is the definitive one: fixed samples, variable thinning
    t2_means = np.array([np.nanmean(t2_ei_ratio[:, i]) for i in range(n_cond2)])
    t2_pacs = np.array([t2_patch_ac[:, i].mean() for i in range(n_cond2)])
    t2_macs = np.array([t2_mag_ac[:, i].mean() for i in range(n_cond2)])

    # Is there a monotonic decrease in EI ratio with thinning?
    print(f"\n  1. TEST 2 (definitive): Does EI ratio decrease with thinning?")
    print(f"     Metropolis, all with n_samples=200:")
    for ci, thin in enumerate(test2_metro_thin):
        print(f"       thin={thin:>3d}: EI_ratio={t2_means[ci]:.4f}, "
              f"MagAC={t2_macs[ci]:.4f}, PatchAC={t2_pacs[ci]:.4f}")

    ratio_range = t2_means.max() - t2_means.min()
    ratio_first = t2_means[0]
    ratio_last = t2_means[-1]

    print(f"\n     Range of EI ratio: {ratio_range:.4f}")
    print(f"     First (thin={test2_metro_thin[0]}): {ratio_first:.4f}")
    print(f"     Last (thin={test2_metro_thin[-1]}): {ratio_last:.4f}")
    print(f"     Drop: {ratio_first - ratio_last:.4f}")

    # Check if there's a strong trend
    if n_cond2 > 3:
        tau_trend, p_trend = stats.kendalltau(
            test2_metro_thin, t2_means)
        print(f"     Kendall tau (thin vs ratio): {tau_trend:+.4f} (p={p_trend:.4e})")
    else:
        tau_trend, p_trend = np.nan, np.nan

    # Wolff test
    t3_means = np.array([np.nanmean(t3_ei_ratio[:, i]) for i in range(n_cond3)])

    print(f"\n  2. TEST 3: Wolff EI ratios:")
    for ci, thin in enumerate(test3_wolff_thin):
        print(f"       thin={thin:>3d}: EI_ratio={t3_means[ci]:.4f}")

    wolff_max = t3_means.max()
    wolff_min = t3_means.min()
    print(f"     Range: [{wolff_min:.4f}, {wolff_max:.4f}]")
    print(f"     Any > 1.5? {'YES' if wolff_max > 1.5 else 'NO'}")

    # Overall assessment
    print(f"\n  3. INTERPRETATION:")

    # Is the Metropolis signal sensitive to thinning?
    if np.isfinite(tau_trend) and p_trend < 0.1 and tau_trend < -0.3:
        print(f"     >>> STRONG EVIDENCE: Metropolis EI ratio DECREASES with thinning")
        print(f"     >>> (tau={tau_trend:+.3f}, p={p_trend:.4e}).")
        print(f"     >>> This indicates the signal IS partially from autocorrelation.")
    elif ratio_first > 1.5 and ratio_last > 1.5:
        print(f"     >>> The EI ratio stays > 1.5 across all thinning levels.")
        print(f"     >>> Autocorrelation does NOT explain the emergence signal.")
    else:
        print(f"     >>> The results are nuanced. See details above.")

    # Does Metropolis at high thinning still exceed Wolff?
    if ratio_last > wolff_max + 0.5:
        print(f"\n     >>> Even at max thinning (thin={test2_metro_thin[-1]}),")
        print(f"     >>> Metropolis EI ratio ({ratio_last:.3f}) exceeds Wolff max")
        print(f"     >>> ({wolff_max:.3f}). Part of the signal persists beyond")
        print(f"     >>> what autocorrelation explains.")
    elif abs(ratio_last - wolff_max) < 0.5:
        print(f"\n     >>> At max thinning, Metropolis ({ratio_last:.3f}) converges")
        print(f"     >>> to Wolff ({wolff_max:.3f}). This suggests the original")
        print(f"     >>> difference was entirely from autocorrelation.")

    # Correlation summary
    print(f"\n     >>> Patch AC vs EI ratio: r={r_pac:+.3f} (p={p_pac:.4e})")
    if abs(r_pac) > 0.7 and p_pac < 0.05:
        print(f"     >>> STRONG positive correlation. More autocorrelation => higher EI ratio.")
    elif abs(r_pac) > 0.5:
        print(f"     >>> Moderate positive correlation.")
    else:
        print(f"     >>> Weak or no correlation.")

    # The big picture
    print(f"\n  OVERALL VERDICT:")
    print(f"  The EI(M)/EI(S) emergence signal in Metropolis dynamics at T_c is")
    if abs(r_pac) > 0.6 and ratio_first > 2 * ratio_last:
        print(f"  PREDOMINANTLY driven by temporal autocorrelation between consecutive")
        print(f"  samples. When samples are sufficiently decorrelated, the ratio drops")
        print(f"  dramatically. The Wolff algorithm, which decorrelates much faster,")
        print(f"  confirms this: it never shows the emergence peak.")
        print(f"")
        print(f"  HOWEVER, this is not the end of the story:")
        print(f"  - Autocorrelation at T_c is a PHYSICAL property (critical slowing down)")
        print(f"  - The transition matrix built from correlated samples captures DYNAMICAL")
        print(f"    structure that IS present in the physics — just not in the equilibrium")
        print(f"    distribution")
        print(f"  - The question becomes: should EI measure dynamical or equilibrium structure?")
    elif ratio_last > 1.5:
        print(f"  NOT primarily from autocorrelation. Even with heavy thinning and")
        print(f"  decorrelated samples, the emergence signal persists. The Wolff result")
        print(f"  needs a different explanation (e.g., Wolff's non-local dynamics may")
        print(f"  not respect the same causal structure as Metropolis).")
    else:
        print(f"  MIXED. Some portion comes from autocorrelation, but the full picture")
        print(f"  is more complex than a simple artifact explanation.")

    # ======================================================================
    # PLOTS
    # ======================================================================
    print("\n\nGenerating plots...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    fig = plt.figure(figsize=(18, 14))

    # --- Panel 1: Test 1 — Constant total sweeps ---
    ax1 = fig.add_subplot(2, 3, 1)
    t1_m = np.array([np.nanmean(t1_ei_ratio[:, i]) for i in range(n_cond1)])
    t1_se = np.array([np.nanstd(t1_ei_ratio[:, i]) / np.sqrt(n_seeds)
                       for i in range(n_cond1)])
    ax1.errorbar(test1_metro_thin, t1_m, yerr=t1_se,
                 fmt='s-', color='tab:orange', markersize=8, capsize=5, linewidth=2)
    ax1.axhline(1.0, color='gray', linestyle=':', alpha=0.5)
    for i, (thin, ns) in enumerate(zip(test1_metro_thin,
                                        [test1_total_sweeps // t for t in test1_metro_thin])):
        ax1.annotate(f'n={ns}', (thin, t1_m[i]),
                     textcoords="offset points", xytext=(0, 12),
                     fontsize=8, ha='center', color='tab:orange')
    ax1.set_xlabel('Thinning (sweeps/sample)', fontsize=10)
    ax1.set_ylabel('EI(M) / EI(S)', fontsize=10)
    ax1.set_title('Test 1: Constant Sweeps\n(confounds AC with sample count)',
                  fontsize=10, fontweight='bold')
    ax1.set_xscale('log')
    ax1.grid(True, alpha=0.3)

    # --- Panel 2: Test 2 — Fixed samples (THE KEY RESULT) ---
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.errorbar(test2_metro_thin, t2_means,
                 yerr=[np.nanstd(t2_ei_ratio[:, i]) / np.sqrt(n_seeds)
                       for i in range(n_cond2)],
                 fmt='s-', color='tab:orange', markersize=8, capsize=5, linewidth=2,
                 label='Metropolis')

    # Add Wolff baseline band
    wolff_mean_all = t3_means.mean()
    wolff_std_all = t3_means.std()
    ax2.axhspan(wolff_mean_all - wolff_std_all, wolff_mean_all + wolff_std_all,
                alpha=0.2, color='tab:blue', label=f'Wolff range ({wolff_mean_all:.2f})')
    ax2.axhline(1.0, color='gray', linestyle=':', alpha=0.5)

    ax2.set_xlabel('Thinning (sweeps/sample)', fontsize=10)
    ax2.set_ylabel('EI(M) / EI(S)', fontsize=10)
    ax2.set_title('Test 2: FIXED 200 SAMPLES\n(isolates autocorrelation effect)',
                  fontsize=10, fontweight='bold', color='darkred')
    ax2.set_xscale('log')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    # --- Panel 3: Test 3 — Wolff thinning ---
    ax3 = fig.add_subplot(2, 3, 3)
    t3_se = np.array([np.nanstd(t3_ei_ratio[:, i]) / np.sqrt(n_seeds)
                       for i in range(n_cond3)])
    ax3.errorbar(test3_wolff_thin, t3_means, yerr=t3_se,
                 fmt='o-', color='tab:blue', markersize=8, capsize=5, linewidth=2,
                 label='Wolff')
    ax3.axhline(1.0, color='gray', linestyle=':', alpha=0.5)

    # Add Metropolis thin=5 reference
    ax3.axhspan(t2_means[0] - 0.3, t2_means[0] + 0.3,
                alpha=0.15, color='tab:orange',
                label=f'Metro thin=5 ({t2_means[0]:.1f})')

    ax3.set_xlabel('Thinning (flips/sample)', fontsize=10)
    ax3.set_ylabel('EI(M) / EI(S)', fontsize=10)
    ax3.set_title('Test 3: Wolff Thinning\n(200 samples, variable decorrelation)',
                  fontsize=10, fontweight='bold')
    ax3.set_xscale('log')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)

    # --- Panel 4: SMOKING GUN — PatchAC vs EI Ratio ---
    ax4 = fig.add_subplot(2, 3, 4)

    # Metropolis points (Test 2)
    t2_pacs_plot = np.array([t2_patch_ac[:, i].mean() for i in range(n_cond2)])
    for i in range(n_cond2):
        ax4.plot(t2_pacs_plot[i], t2_means[i], 's', color='tab:orange',
                 markersize=10, zorder=3)
        ax4.annotate(f'{test2_metro_thin[i]}',
                     (t2_pacs_plot[i], t2_means[i]),
                     textcoords="offset points", xytext=(7, 4),
                     fontsize=8, color='tab:orange')

    # Wolff points (Test 3)
    t3_pacs_plot = np.array([t3_patch_ac[:, i].mean() for i in range(n_cond3)])
    for i in range(n_cond3):
        ax4.plot(t3_pacs_plot[i], t3_means[i], 'o', color='tab:blue',
                 markersize=10, zorder=3)
        ax4.annotate(f'{test3_wolff_thin[i]}',
                     (t3_pacs_plot[i], t3_means[i]),
                     textcoords="offset points", xytext=(7, 4),
                     fontsize=8, color='tab:blue')

    # Regression line through all points
    all_x_plot = np.concatenate([t2_pacs_plot, t3_pacs_plot])
    all_y_plot = np.concatenate([t2_means, t3_means])
    fin = np.isfinite(all_x_plot) & np.isfinite(all_y_plot)
    if fin.sum() > 2:
        slope, intercept, r_val, p_val, _ = stats.linregress(
            all_x_plot[fin], all_y_plot[fin])
        x_line = np.linspace(all_x_plot[fin].min(), all_x_plot[fin].max(), 100)
        ax4.plot(x_line, intercept + slope * x_line, 'k--', alpha=0.5,
                 label=f'r={r_val:.3f}, p={p_val:.4f}')

    ax4.axhline(1.0, color='gray', linestyle=':', alpha=0.5)
    ax4.plot([], [], 's', color='tab:orange', markersize=8, label='Metropolis')
    ax4.plot([], [], 'o', color='tab:blue', markersize=8, label='Wolff')
    ax4.set_xlabel('Patch Identity Probability', fontsize=10)
    ax4.set_ylabel('EI(M) / EI(S)', fontsize=10)
    ax4.set_title('Patch AC vs EI Ratio\n(all fixed-sample conditions)',
                  fontsize=10, fontweight='bold')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)

    # --- Panel 5: MagAC vs EI Ratio ---
    ax5 = fig.add_subplot(2, 3, 5)
    t2_macs_plot = np.array([t2_mag_ac[:, i].mean() for i in range(n_cond2)])
    t3_macs_plot = np.array([t3_mag_ac[:, i].mean() for i in range(n_cond3)])

    for i in range(n_cond2):
        ax5.plot(t2_macs_plot[i], t2_means[i], 's', color='tab:orange',
                 markersize=10, zorder=3)
        ax5.annotate(f'{test2_metro_thin[i]}',
                     (t2_macs_plot[i], t2_means[i]),
                     textcoords="offset points", xytext=(7, 4),
                     fontsize=8, color='tab:orange')

    for i in range(n_cond3):
        ax5.plot(t3_macs_plot[i], t3_means[i], 'o', color='tab:blue',
                 markersize=10, zorder=3)
        ax5.annotate(f'{test3_wolff_thin[i]}',
                     (t3_macs_plot[i], t3_means[i]),
                     textcoords="offset points", xytext=(7, 4),
                     fontsize=8, color='tab:blue')

    all_x2 = np.concatenate([t2_macs_plot, t3_macs_plot])
    all_y2 = np.concatenate([t2_means, t3_means])
    fin2 = np.isfinite(all_x2) & np.isfinite(all_y2)
    if fin2.sum() > 2:
        slope2, intercept2, r_val2, p_val2, _ = stats.linregress(
            all_x2[fin2], all_y2[fin2])
        x_line2 = np.linspace(all_x2[fin2].min(), all_x2[fin2].max(), 100)
        ax5.plot(x_line2, intercept2 + slope2 * x_line2, 'k--', alpha=0.5,
                 label=f'r={r_val2:.3f}, p={p_val2:.4f}')

    ax5.axhline(1.0, color='gray', linestyle=':', alpha=0.5)
    ax5.plot([], [], 's', color='tab:orange', markersize=8, label='Metropolis')
    ax5.plot([], [], 'o', color='tab:blue', markersize=8, label='Wolff')
    ax5.set_xlabel('Magnetization Lag-1 Autocorrelation', fontsize=10)
    ax5.set_ylabel('EI(M) / EI(S)', fontsize=10)
    ax5.set_title('Mag AC vs EI Ratio\n(all fixed-sample conditions)',
                  fontsize=10, fontweight='bold')
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3)

    # --- Panel 6: Summary bar chart ---
    ax6 = fig.add_subplot(2, 3, 6)

    # Key conditions to compare
    labels = []
    ratios_bar = []
    ses_bar = []
    colors_bar = []

    # Metro thin=5 (most correlated)
    labels.append(f'Metro\nt={test2_metro_thin[0]}')
    ratios_bar.append(t2_means[0])
    ses_bar.append(np.nanstd(t2_ei_ratio[:, 0]) / np.sqrt(n_seeds))
    colors_bar.append('tab:orange')

    # Metro thin=25
    mid_idx = len(test2_metro_thin) // 2
    labels.append(f'Metro\nt={test2_metro_thin[mid_idx]}')
    ratios_bar.append(t2_means[mid_idx])
    ses_bar.append(np.nanstd(t2_ei_ratio[:, mid_idx]) / np.sqrt(n_seeds))
    colors_bar.append('moccasin')

    # Metro thin=100 (most decorrelated)
    labels.append(f'Metro\nt={test2_metro_thin[-1]}')
    ratios_bar.append(t2_means[-1])
    ses_bar.append(np.nanstd(t2_ei_ratio[:, -1]) / np.sqrt(n_seeds))
    colors_bar.append('navajowhite')

    # Wolff thin=1
    labels.append(f'Wolff\nt={test3_wolff_thin[0]}')
    ratios_bar.append(t3_means[0])
    ses_bar.append(np.nanstd(t3_ei_ratio[:, 0]) / np.sqrt(n_seeds))
    colors_bar.append('tab:blue')

    # Wolff thin=20
    labels.append(f'Wolff\nt={test3_wolff_thin[-1]}')
    ratios_bar.append(t3_means[-1])
    ses_bar.append(np.nanstd(t3_ei_ratio[:, -1]) / np.sqrt(n_seeds))
    colors_bar.append('lightsteelblue')

    x_pos = np.arange(len(labels))
    bars = ax6.bar(x_pos, ratios_bar, yerr=ses_bar, capsize=5,
                   color=colors_bar, edgecolor='black', linewidth=0.5)
    ax6.axhline(1.0, color='gray', linestyle=':', alpha=0.7, linewidth=1.5)
    ax6.set_xticks(x_pos)
    ax6.set_xticklabels(labels, fontsize=9)
    ax6.set_ylabel('EI(M) / EI(S)', fontsize=10)
    ax6.set_title('Key Conditions Compared\n(all with 200 samples)',
                  fontsize=10, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='y')

    plt.suptitle(f'v4: Is Metropolis Emergence from Autocorrelation? '
                 f'(T={T_target}, L={L})',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    save_path = os.path.join(plot_dir, 'v4_wolff_fair.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")

    # ======================================================================
    # TIMING
    # ======================================================================
    total_elapsed = time.time() - total_start
    print(f"\n{'='*78}")
    print(f"PHASE 1 v4 COMPLETE — Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"{'='*78}")


if __name__ == "__main__":
    run_v4()
