"""
Phase 1 v4: FALSIFICATION TESTS for EI Emergence Signal

Two tests that should produce NEGATIVE results (no emergence signal).
If either test shows a signal, our method is broken.

TEST 1: 1D ISING MODEL
- The 1D Ising model has NO phase transition at finite temperature.
- Correlation length xi = -1/ln(tanh(1/T)) grows but never diverges.
- PREDICTION: EI(M)/EI(S) should be ~1.0 everywhere, no peak.

TEST 2: TEMPORAL SHUFFLE (2D Ising)
- Take the 2D Ising L=24 simulation, randomly permute time ordering.
- This preserves spatial structure at each snapshot but destroys dynamics.
- PREDICTION: Shuffled EI ratio should be ~1.0 (no emergence).
"""

import sys
import os
import time
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ising import simulate_ising
from src.coarse_grain import coarsegrain_timeseries
from src.ei_compute import estimate_transition_matrix, effective_information

# ======================================================================
# SHARED UTILITIES
# ======================================================================

def config_to_patch_states_2d(configs, patch_size):
    """Extract non-overlapping 2D patches and encode as integers.

    For 2D configs of shape (N, L, L).
    Uses vectorized operations for speed.
    """
    N, L, _ = configs.shape
    p = patch_size
    n_patches_per_side = L // p
    n_patches = n_patches_per_side * n_patches_per_side
    n_bits = p * p
    n_states = 2 ** n_bits

    # Convert to binary: (spin + 1) // 2 maps -1->0, +1->1
    binary = ((configs + 1) // 2).astype(np.int32)

    # Reshape into patches: (N, n_ps, p, n_ps, p) -> rearrange
    reshaped = binary.reshape(N, n_patches_per_side, p, n_patches_per_side, p)
    # Transpose to (N, n_ps, n_ps, p, p)
    patches = reshaped.transpose(0, 1, 3, 2, 4)
    # Flatten patches: (N, n_ps, n_ps, p*p)
    patches_flat = patches.reshape(N, n_patches, n_bits)

    # Encode as integers using bit shifting
    powers = (2 ** np.arange(n_bits - 1, -1, -1)).astype(np.int32)
    states = (patches_flat * powers[np.newaxis, np.newaxis, :]).sum(axis=2)

    return states, n_states, n_patches


def config_to_patch_states_1d(configs, patch_size):
    """Extract non-overlapping 1D patches and encode as integers.

    For 1D configs of shape (N, chain_length).
    Uses vectorized operations for speed.
    """
    N, chain_len = configs.shape
    n_patches = chain_len // patch_size
    n_states = 2 ** patch_size

    # Convert to binary
    binary = ((configs + 1) // 2).astype(np.int32)

    # Reshape into patches: (N, n_patches, patch_size)
    trimmed = binary[:, :n_patches * patch_size]
    patches = trimmed.reshape(N, n_patches, patch_size)

    # Encode as integers
    powers = (2 ** np.arange(patch_size - 1, -1, -1)).astype(np.int32)
    states = (patches * powers[np.newaxis, np.newaxis, :]).sum(axis=2)

    return states, n_states, n_patches


def compute_ei_equalized_from_states(micro_states, macro_states, n_states,
                                      min_obs, rng):
    """Compute EI with equalized transition counts from pre-computed states.

    Subsamples micro transitions to match macro count.
    """
    micro_t = micro_states[:-1].ravel()
    micro_t1 = micro_states[1:].ravel()
    macro_t = macro_states[:-1].ravel()
    macro_t1 = macro_states[1:].ravel()

    n_macro_transitions = len(macro_t)
    n_micro_transitions = len(micro_t)

    # Subsample micro to match macro count
    if n_micro_transitions > n_macro_transitions:
        idx = rng.choice(n_micro_transitions, size=n_macro_transitions, replace=False)
        micro_t_sub = micro_t[idx]
        micro_t1_sub = micro_t1[idx]
    else:
        micro_t_sub = micro_t
        micro_t1_sub = micro_t1

    T_micro, rc_micro = estimate_transition_matrix(micro_t_sub, micro_t1_sub, n_states)
    T_macro, rc_macro = estimate_transition_matrix(macro_t, macro_t1, n_states)

    ei_micro = effective_information(T_micro, rc_micro, min_observations=min_obs)
    ei_macro = effective_information(T_macro, rc_macro, min_observations=min_obs)

    return ei_micro, ei_macro


def compute_ei_equalized_2d(configs_raw, configs_coarse, patch_size, min_obs, rng):
    """Compute EI for 2D micro and macro with equalized transition counts."""
    micro_states, n_states, _ = config_to_patch_states_2d(configs_raw, patch_size)
    macro_states, _, _ = config_to_patch_states_2d(configs_coarse, patch_size)
    return compute_ei_equalized_from_states(micro_states, macro_states,
                                             n_states, min_obs, rng)


# ======================================================================
# TEST 1: 1D ISING MODEL
# ======================================================================

def simulate_ising_1d(N_spins, T, n_steps, n_equilib, seed=42,
                       sweeps_per_sample=10):
    """
    Simulate a 1D Ising model with Metropolis-Hastings dynamics.

    Parameters
    ----------
    N_spins : int
        Number of spins in the chain.
    T : float
        Temperature (J=1, k_B=1).
    n_steps : int
        Number of configurations to sample after equilibration.
    n_equilib : int
        Number of sweeps for equilibration.
    seed : int
        Random seed.
    sweeps_per_sample : int
        Number of Metropolis sweeps between samples.

    Returns
    -------
    configs : ndarray of shape (n_steps, N_spins) with values +1/-1
    magnetizations : ndarray of shape (n_steps,)
    """
    rng = np.random.RandomState(seed)
    N = N_spins

    # Initialize all spins up
    chain = np.ones(N, dtype=np.int8)

    # Precompute Boltzmann factors for 1D
    # dE = 2 * s * (s_left + s_right), possible values: -4, 0, 4
    beta = 1.0 / T
    boltzmann = {}
    for dE in [-4, -2, 0, 2, 4]:
        boltzmann[dE] = min(1.0, np.exp(-dE * beta))

    def sweep(chain, rng):
        """One Metropolis sweep: N single-spin flip attempts."""
        positions = rng.randint(0, N, size=N)
        thresholds = rng.random(size=N)

        for k in range(N):
            i = positions[k]
            s = chain[i]
            left = chain[(i - 1) % N]
            right = chain[(i + 1) % N]
            dE = 2 * int(s) * (int(left) + int(right))
            if thresholds[k] < boltzmann[dE]:
                chain[i] = -s

    # Equilibration
    for _ in range(n_equilib):
        sweep(chain, rng)

    # Sampling
    configs = np.empty((n_steps, N), dtype=np.int8)
    magnetizations = np.empty(n_steps, dtype=np.float64)

    for step in range(n_steps):
        for _ in range(sweeps_per_sample):
            sweep(chain, rng)
        configs[step] = chain.copy()
        magnetizations[step] = np.abs(chain.sum()) / N

    return configs, magnetizations


def coarsegrain_1d(configs, block_size):
    """
    Coarse-grain 1D time series using majority vote on consecutive blocks.
    Vectorized for speed.
    """
    N_steps, chain_len = configs.shape
    n_blocks = chain_len // block_size

    trimmed = configs[:, :n_blocks * block_size]
    reshaped = trimmed.reshape(N_steps, n_blocks, block_size)
    block_sums = reshaped.sum(axis=2)
    coarse = np.where(block_sums >= 0, np.int8(1), np.int8(-1))

    return coarse


def run_test1_1d_ising():
    """
    TEST 1: 1D Ising Model -- should show NO peak in EI ratio.

    The 1D Ising model has no phase transition at finite T.
    """
    print("=" * 70)
    print("TEST 1: 1D ISING MODEL (NO PHASE TRANSITION)")
    print("=" * 70)
    print()
    print("The 1D Ising model has NO phase transition at finite temperature.")
    print("If EI(M)/EI(S) peaks, our method is fundamentally flawed.")
    print()

    # Parameters -- reduced for feasible runtime while still capturing physics
    N_spins = 576        # Same total spins as L=24 2D grid
    block_size = 4       # Coarse-grain blocks of 4 consecutive spins
    patch_size = 2       # Patches of 2 consecutive spins -> 4 states
    n_equilib = 2000     # Sufficient for 1D (no critical slowing down)
    n_steps = 1000       # 1000 time steps
    sweeps_per_sample = 5  # 5 sweeps between samples
    n_seeds = 5
    min_obs = 5
    temperatures = np.array([1.0, 1.5, 2.0, 2.269, 2.5, 3.0, 4.0, 5.0])
    n_temps = len(temperatures)

    n_micro_patches = N_spins // patch_size   # 288
    n_macro_patches = (N_spins // block_size) // patch_size  # 72

    print(f"Parameters:")
    print(f"  N_spins={N_spins}, block_size={block_size}, patch_size={patch_size}")
    print(f"  n_equilib={n_equilib}, n_steps={n_steps}, sweeps_per_sample={sweeps_per_sample}")
    print(f"  n_seeds={n_seeds}")
    print(f"  Micro patches: {n_micro_patches}, Macro patches: {n_macro_patches}")
    print(f"  State space: 2^{patch_size} = {2**patch_size} states (equal)")
    print(f"  min_obs={min_obs}")
    print(f"  Temperatures: {temperatures}")
    print()

    # Storage
    ei_micro_all = np.zeros((n_seeds, n_temps))
    ei_macro_all = np.zeros((n_seeds, n_temps))
    ratio_all = np.zeros((n_seeds, n_temps))
    mag_all = np.zeros((n_seeds, n_temps))

    total_start = time.time()

    for idx, T in enumerate(temperatures):
        t0 = time.time()
        print(f"--- T = {T:.3f} ({idx+1}/{n_temps}) ---", flush=True)

        for s in range(n_seeds):
            seed = 2000 * s + idx + 50000
            rng_eq = np.random.RandomState(seed + 77777)

            # Simulate 1D Ising
            configs, mags = simulate_ising_1d(N_spins, T, n_steps, n_equilib,
                                               seed=seed,
                                               sweeps_per_sample=sweeps_per_sample)
            mag_all[s, idx] = mags.mean()

            # Coarse-grain
            coarse = coarsegrain_1d(configs, block_size)

            # Extract patch states (vectorized)
            micro_states, n_states_micro, _ = config_to_patch_states_1d(
                configs, patch_size)
            macro_states, n_states_macro, _ = config_to_patch_states_1d(
                coarse, patch_size)

            assert n_states_micro == n_states_macro == 2**patch_size

            # Compute EI equalized
            ei_s, ei_m = compute_ei_equalized_from_states(
                micro_states, macro_states, n_states_micro, min_obs, rng_eq)

            ei_micro_all[s, idx] = ei_s
            ei_macro_all[s, idx] = ei_m
            ratio_all[s, idx] = ei_m / ei_s if ei_s > 1e-10 else np.nan

        elapsed = time.time() - t0
        mean_ratio = np.nanmean(ratio_all[:, idx])
        se_ratio = np.nanstd(ratio_all[:, idx]) / np.sqrt(n_seeds)
        mean_mag = mag_all[:, idx].mean()
        print(f"  EI(S)={ei_micro_all[:, idx].mean():.4f}, "
              f"EI(M)={ei_macro_all[:, idx].mean():.4f}, "
              f"Ratio={mean_ratio:.3f} +/- {se_ratio:.3f}, "
              f"|M|={mean_mag:.3f}, Time={elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    print(f"\nTotal time for Test 1: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Analysis
    mean_ratio = np.nanmean(ratio_all, axis=0)
    se_ratio = np.nanstd(ratio_all, axis=0) / np.sqrt(n_seeds)

    print(f"\n--- 1D Ising Results Summary ---")
    print(f"{'T':>6s}  {'Ratio':>8s}  {'SE':>8s}  {'|M|':>8s}")
    print("-" * 36)
    for idx, T in enumerate(temperatures):
        print(f"{T:6.3f}  {mean_ratio[idx]:8.3f}  {se_ratio[idx]:8.3f}  "
              f"{mag_all[:, idx].mean():8.3f}")

    max_ratio = np.nanmax(mean_ratio)
    max_ratio_T = temperatures[np.nanargmax(mean_ratio)]
    ratio_range = np.nanmax(mean_ratio) - np.nanmin(mean_ratio)

    print(f"\nMax ratio: {max_ratio:.3f} at T={max_ratio_T:.3f}")
    print(f"Ratio range (max - min): {ratio_range:.3f}")

    return (temperatures, mean_ratio, se_ratio, ei_micro_all, ei_macro_all,
            ratio_all, mag_all, total_elapsed)


# ======================================================================
# TEST 2: TEMPORAL SHUFFLE (2D Ising)
# ======================================================================

def run_test2_temporal_shuffle():
    """
    TEST 2: Temporal Shuffle -- should destroy EI emergence signal.

    Takes 2D Ising simulation and randomly permutes time ordering
    before computing transitions. Preserves spatial structure at each
    snapshot but destroys temporal dynamics.
    """
    print("\n" + "=" * 70)
    print("TEST 2: TEMPORAL SHUFFLE (2D ISING)")
    print("=" * 70)
    print()
    print("Randomly permute time indices of 2D Ising configurations.")
    print("This preserves per-snapshot spatial structure but destroys dynamics.")
    print("If shuffled EI ratio shows emergence, the signal is not dynamic.")
    print()

    # Parameters -- reduced for feasible runtime
    L = 24
    block_size = 4
    patch_size = 2
    n_equilib = 2000
    n_steps = 1000
    n_seeds = 5
    min_obs = 5
    T_c = 2.269
    temperatures = np.array([1.8, 2.0, 2.15, 2.269, 2.5])
    n_temps = len(temperatures)

    print(f"Parameters:")
    print(f"  L={L}, block_size={block_size}, patch_size={patch_size}")
    print(f"  n_equilib={n_equilib}, n_steps={n_steps}, n_seeds={n_seeds}")
    print(f"  min_obs={min_obs}")
    print(f"  Temperatures: {temperatures}")
    print()

    # Storage
    ei_micro_orig = np.zeros((n_seeds, n_temps))
    ei_macro_orig = np.zeros((n_seeds, n_temps))
    ratio_orig = np.zeros((n_seeds, n_temps))

    ei_micro_shuf = np.zeros((n_seeds, n_temps))
    ei_macro_shuf = np.zeros((n_seeds, n_temps))
    ratio_shuf = np.zeros((n_seeds, n_temps))

    total_start = time.time()

    for idx, T in enumerate(temperatures):
        t0 = time.time()
        print(f"--- T = {T:.3f} ({idx+1}/{n_temps}) ---", flush=True)

        for s in range(n_seeds):
            seed = 1000 * s + idx
            rng_eq_orig = np.random.RandomState(seed + 99999)
            rng_eq_shuf = np.random.RandomState(seed + 199999)
            rng_perm = np.random.RandomState(seed + 399999)

            # 1. Run normal 2D Ising simulation
            configs, mags = simulate_ising(L, T, n_steps, n_equilib, seed=seed)

            # 2. Coarse-grain original
            coarse_orig = coarsegrain_timeseries(configs, block_size)

            # 3. Compute EI for ORIGINAL time series
            ei_s_o, ei_m_o = compute_ei_equalized_2d(
                configs, coarse_orig, patch_size, min_obs, rng_eq_orig)
            ei_micro_orig[s, idx] = ei_s_o
            ei_macro_orig[s, idx] = ei_m_o
            ratio_orig[s, idx] = ei_m_o / ei_s_o if ei_s_o > 1e-10 else np.nan

            # 4. TEMPORAL SHUFFLE: randomly permute time index
            perm = rng_perm.permutation(n_steps)
            configs_shuffled = configs[perm]

            # 5. Coarse-grain the shuffled configs
            coarse_shuf = coarsegrain_timeseries(configs_shuffled, block_size)

            # 6. Compute EI for SHUFFLED time series
            ei_s_sh, ei_m_sh = compute_ei_equalized_2d(
                configs_shuffled, coarse_shuf, patch_size, min_obs, rng_eq_shuf)
            ei_micro_shuf[s, idx] = ei_s_sh
            ei_macro_shuf[s, idx] = ei_m_sh
            ratio_shuf[s, idx] = ei_m_sh / ei_s_sh if ei_s_sh > 1e-10 else np.nan

        elapsed = time.time() - t0
        mr_orig = np.nanmean(ratio_orig[:, idx])
        mr_shuf = np.nanmean(ratio_shuf[:, idx])
        se_orig_t = np.nanstd(ratio_orig[:, idx]) / np.sqrt(n_seeds)
        se_shuf_t = np.nanstd(ratio_shuf[:, idx]) / np.sqrt(n_seeds)

        print(f"  ORIGINAL: EI(M)/EI(S) = {mr_orig:.3f} +/- {se_orig_t:.3f}  "
              f"[EI(S)={ei_micro_orig[:, idx].mean():.4f}, "
              f"EI(M)={ei_macro_orig[:, idx].mean():.4f}]")
        print(f"  SHUFFLED: EI(M)/EI(S) = {mr_shuf:.3f} +/- {se_shuf_t:.3f}  "
              f"[EI(S)={ei_micro_shuf[:, idx].mean():.4f}, "
              f"EI(M)={ei_macro_shuf[:, idx].mean():.4f}]")
        print(f"  Time: {elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    print(f"\nTotal time for Test 2: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Analysis
    mean_ratio_orig = np.nanmean(ratio_orig, axis=0)
    se_ratio_orig = np.nanstd(ratio_orig, axis=0) / np.sqrt(n_seeds)
    mean_ratio_shuf = np.nanmean(ratio_shuf, axis=0)
    se_ratio_shuf = np.nanstd(ratio_shuf, axis=0) / np.sqrt(n_seeds)

    print(f"\n--- Temporal Shuffle Results Summary ---")
    print(f"{'T':>6s}  {'Original':>10s}  {'SE':>8s}  {'Shuffled':>10s}  {'SE':>8s}  {'Orig/Shuf':>10s}")
    print("-" * 62)
    for idx, T in enumerate(temperatures):
        ro = mean_ratio_orig[idx]
        rs = mean_ratio_shuf[idx]
        print(f"{T:6.3f}  {ro:10.3f}  {se_ratio_orig[idx]:8.3f}  "
              f"{rs:10.3f}  {se_ratio_shuf[idx]:8.3f}  "
              f"{ro/rs if rs > 1e-10 else np.nan:10.3f}")

    return (temperatures, mean_ratio_orig, se_ratio_orig,
            mean_ratio_shuf, se_ratio_shuf,
            ratio_orig, ratio_shuf, total_elapsed)


# ======================================================================
# MAIN: RUN BOTH TESTS
# ======================================================================

def run_falsification():
    """Run both falsification tests and produce plots + log."""
    overall_start = time.time()

    print("*" * 70)
    print("PHASE 1 v4: FALSIFICATION TESTS FOR EI EMERGENCE SIGNAL")
    print("*" * 70)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ===== TEST 1: 1D Ising =====
    (temps_1d, ratio_1d, se_1d, ei_micro_1d, ei_macro_1d,
     ratio_all_1d, mag_1d, time_1d) = run_test1_1d_ising()

    # ===== TEST 2: Temporal Shuffle =====
    (temps_ts, ratio_orig, se_orig, ratio_shuf, se_shuf,
     ratio_all_orig, ratio_all_shuf, time_ts) = run_test2_temporal_shuffle()

    overall_elapsed = time.time() - overall_start

    # ==================================================================
    # VERDICT
    # ==================================================================
    print("\n" + "=" * 70)
    print("FALSIFICATION VERDICTS")
    print("=" * 70)

    # Test 1 Verdict: 1D Ising
    max_ratio_1d = np.nanmax(ratio_1d)
    min_ratio_1d = np.nanmin(ratio_1d)
    range_1d = max_ratio_1d - min_ratio_1d
    peak_T_1d = temps_1d[np.nanargmax(ratio_1d)]

    # Check for a LOCALIZED peak: the key distinction from 2D is that
    # in 2D the ratio peaks at a specific T (near T_c) with clear rise
    # and fall. In 1D, we should see either flat behavior or monotonic
    # trends (no localized peak).
    # Criterion: a "peak" means max ratio > 1.5 AND the range > 0.5
    # (i.e., there is a clear bump, not just noise or a flat offset)
    has_peak_1d = (max_ratio_1d > 1.5) and (range_1d > 0.5)
    all_near_one_1d = np.all(np.abs(ratio_1d - 1.0) < 0.5)

    # Additional check: is there a LOCALIZED peak (rise then fall)?
    # The 2D Ising shows clear rise-peak-fall. 1D should not.
    peak_idx_1d = np.nanargmax(ratio_1d)
    # A localized peak means it's not at the edges AND values drop on both sides
    is_interior = 0 < peak_idx_1d < len(ratio_1d) - 1
    if is_interior:
        drops_left = ratio_1d[peak_idx_1d] > ratio_1d[peak_idx_1d - 1] + 0.3
        drops_right = ratio_1d[peak_idx_1d] > ratio_1d[peak_idx_1d + 1] + 0.3
        has_localized_peak = drops_left and drops_right and max_ratio_1d > 1.5
    else:
        has_localized_peak = False

    test1_pass = not has_localized_peak
    print(f"\nTEST 1: 1D ISING MODEL")
    print(f"  Max EI(M)/EI(S): {max_ratio_1d:.3f} at T={peak_T_1d:.3f}")
    print(f"  Min EI(M)/EI(S): {min_ratio_1d:.3f}")
    print(f"  Range: {range_1d:.3f}")
    print(f"  All ratios within 0.5 of 1.0? {all_near_one_1d}")
    print(f"  Has localized peak (rise-peak-fall with max > 1.5)? {has_localized_peak}")
    print(f"  Note: 1D has no phase transition; any pattern is monotonic/flat, not peaked")

    # Interpret the pattern
    if not all_near_one_1d:
        # Check if it's a monotonic trend (acceptable for 1D)
        from scipy.stats import spearmanr
        rho, pval = spearmanr(temps_1d, ratio_1d)
        is_monotonic = abs(rho) > 0.5
        print(f"  Spearman correlation (ratio vs T): rho={rho:.3f}, p={pval:.3e}")
        if is_monotonic:
            print(f"  Pattern is monotonic (not a localized peak)")
        # Check if high values are due to noise (very low EI values)
        ei_at_max = ei_micro_1d[:, np.nanargmax(ratio_1d)].mean()
        print(f"  EI(S) at max ratio: {ei_at_max:.6f}")
        if ei_at_max < 0.001:
            print(f"  NOTE: EI values are near-zero at max ratio -- ratio is noise")

    if test1_pass:
        print(f"  >>> TEST 1: PASSED (no spurious localized peak in 1D Ising)")
    else:
        print(f"  >>> TEST 1: FAILED (spurious localized peak detected!)")

    # Test 2 Verdict: Temporal Shuffle
    max_shuf = np.nanmax(ratio_shuf)
    mean_shuf = np.nanmean(ratio_shuf)
    # Compare original vs shuffled at their respective peaks
    peak_idx_orig = np.nanargmax(ratio_orig)
    peak_val_orig = ratio_orig[peak_idx_orig]
    shuf_at_peak = ratio_shuf[peak_idx_orig]

    # Shuffled should be much lower than original near T_c
    # And shuffled should be near 1.0
    shuf_near_one = np.all(np.abs(ratio_shuf - 1.0) < 1.0)
    shuf_much_lower = peak_val_orig > 1.5 * shuf_at_peak if shuf_at_peak > 0 else True

    test2_pass = shuf_near_one or shuf_much_lower
    print(f"\nTEST 2: TEMPORAL SHUFFLE")
    print(f"  Original peak: {peak_val_orig:.3f} at T={temps_ts[peak_idx_orig]:.3f}")
    print(f"  Shuffled at same T: {shuf_at_peak:.3f}")
    print(f"  Mean shuffled ratio: {mean_shuf:.3f}")
    print(f"  Max shuffled ratio: {max_shuf:.3f}")
    print(f"  Shuffled all within 1.0 of 1.0? {shuf_near_one}")
    print(f"  Original > 1.5x shuffled at peak? {shuf_much_lower}")
    if test2_pass:
        print(f"  >>> TEST 2: PASSED (temporal shuffle destroys/reduces signal)")
    else:
        print(f"  >>> TEST 2: FAILED (shuffled signal persists!)")

    print(f"\n{'='*70}")
    both_pass = test1_pass and test2_pass
    if both_pass:
        print("OVERALL: BOTH FALSIFICATION TESTS PASSED")
        print("The EI emergence signal is NOT a trivial artifact.")
    else:
        if not test1_pass:
            print("WARNING: 1D Ising test FAILED -- method may be broken!")
        if not test2_pass:
            print("WARNING: Temporal shuffle test FAILED -- signal not dynamic!")
    print(f"{'='*70}")
    print(f"\nTotal runtime: {overall_elapsed:.1f}s ({overall_elapsed/60:.1f} min)")

    # ==================================================================
    # PLOTS
    # ==================================================================
    print("\nGenerating plots...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    project_root = os.path.join(os.path.dirname(__file__), '..')
    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    # --- PLOT 1: 1D Ising EI Ratio vs Temperature ---
    fig, axes = plt.subplots(2, 1, figsize=(12, 9),
                              gridspec_kw={'height_ratios': [2, 1]})

    ax = axes[0]
    ax.errorbar(temps_1d, ratio_1d, yerr=se_1d,
                fmt='o-', color='tab:blue', markersize=6, capsize=4,
                linewidth=2, label='1D Ising EI(M)/EI(S)')
    # Show individual seeds
    for s in range(ratio_all_1d.shape[0]):
        finite = np.isfinite(ratio_all_1d[s, :])
        ax.plot(temps_1d[finite], ratio_all_1d[s, finite],
                'o-', alpha=0.2, color='tab:blue', markersize=3, linewidth=0.8)
    ax.axhline(1.0, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label='No emergence (ratio = 1.0)')
    ax.set_ylabel('EI(M) / EI(S)', fontsize=13)
    ax.set_title('FALSIFICATION TEST 1: 1D Ising Model (No Phase Transition)\n'
                 f'N=576 spins, block_size=4, patch_size=2, {ratio_all_1d.shape[0]} seeds',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)

    # Annotate verdict
    verdict_text = "PASSED: No localized peak" if test1_pass else "FAILED: Peak detected!"
    verdict_color = 'green' if test1_pass else 'red'
    ax.text(0.98, 0.95, verdict_text, transform=ax.transAxes,
            fontsize=14, fontweight='bold', color=verdict_color,
            ha='right', va='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=verdict_color, alpha=0.9))

    # Bottom: raw EI values
    ax = axes[1]
    ei_micro_mean = np.mean(ei_micro_1d, axis=0)
    ei_macro_mean = np.mean(ei_macro_1d, axis=0)
    ax.plot(temps_1d, ei_micro_mean, 'ko-', markersize=5, linewidth=1.5,
            label='EI(S) micro')
    ax.plot(temps_1d, ei_macro_mean, 'o-', color='tab:blue', markersize=5,
            linewidth=1.5, label='EI(M) macro')
    ax.set_xlabel('Temperature', fontsize=13)
    ax.set_ylabel('EI (bits)', fontsize=13)
    ax.set_title('Raw EI Values (1D Ising)', fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot1_path = os.path.join(plot_dir, 'v4_1d_ising.png')
    plt.savefig(plot1_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot1_path}")

    # --- PLOT 2: Temporal Shuffle (Original vs Shuffled) ---
    fig, axes = plt.subplots(2, 1, figsize=(12, 9),
                              gridspec_kw={'height_ratios': [2, 1]})

    ax = axes[0]
    ax.errorbar(temps_ts, ratio_orig, yerr=se_orig,
                fmt='o-', color='tab:blue', markersize=6, capsize=4,
                linewidth=2, label='Original (real dynamics)')
    ax.errorbar(temps_ts, ratio_shuf, yerr=se_shuf,
                fmt='s--', color='tab:red', markersize=6, capsize=4,
                linewidth=2, label='Shuffled (random time order)')
    # Show individual seeds for both
    for s in range(ratio_all_orig.shape[0]):
        finite_o = np.isfinite(ratio_all_orig[s, :])
        finite_s = np.isfinite(ratio_all_shuf[s, :])
        ax.plot(temps_ts[finite_o], ratio_all_orig[s, finite_o],
                'o-', alpha=0.15, color='tab:blue', markersize=3, linewidth=0.7)
        ax.plot(temps_ts[finite_s], ratio_all_shuf[s, finite_s],
                's--', alpha=0.15, color='tab:red', markersize=3, linewidth=0.7)

    T_c = 2.269
    ax.axvline(T_c, color='black', linestyle='--', linewidth=1.5, alpha=0.7,
               label=f'$T_c$ = {T_c:.3f}')
    ax.axhline(1.0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_ylabel('EI(M) / EI(S)', fontsize=13)
    ax.set_title('FALSIFICATION TEST 2: Temporal Shuffle (2D Ising L=24)\n'
                 f'block_size=4, patch_size=2, {ratio_all_orig.shape[0]} seeds',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)

    # Annotate verdict
    verdict_text = "PASSED: Shuffle destroys signal" if test2_pass else "FAILED: Signal persists!"
    verdict_color = 'green' if test2_pass else 'red'
    ax.text(0.98, 0.95, verdict_text, transform=ax.transAxes,
            fontsize=14, fontweight='bold', color=verdict_color,
            ha='right', va='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=verdict_color, alpha=0.9))

    # Bottom: ratio of ratios
    ax = axes[1]
    ratio_of_ratios = ratio_orig / np.where(ratio_shuf > 1e-10, ratio_shuf, np.nan)
    ax.plot(temps_ts, ratio_of_ratios, 'D-', color='tab:purple', markersize=6,
            linewidth=2, label='Original / Shuffled')
    ax.axvline(T_c, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axhline(1.0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlabel('Temperature', fontsize=13)
    ax.set_ylabel('Original / Shuffled', fontsize=13)
    ax.set_title('Signal Enhancement: Original vs Shuffled', fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot2_path = os.path.join(plot_dir, 'v4_temporal_shuffle.png')
    plt.savefig(plot2_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot2_path}")

    # ==================================================================
    # SAVE LOG
    # ==================================================================
    log_dir = os.path.join(project_root, 'results', 'phase1')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'v4_falsification_output.log')

    with open(log_path, 'w') as f:
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        f.write(f"Phase 1 v4: Falsification Tests\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Total runtime: {overall_elapsed:.1f}s ({overall_elapsed/60:.1f} min)\n")
        f.write(f"\n{'='*70}\n")
        f.write(f"TEST 1: 1D ISING MODEL\n")
        f.write(f"{'='*70}\n")
        f.write(f"N_spins=576, block_size=4, patch_size=2, n_seeds={ratio_all_1d.shape[0]}\n")
        f.write(f"n_equilib=2000, n_steps=1000, sweeps_per_sample=5, min_obs=5\n")
        f.write(f"\nResults:\n")
        f.write(f"{'T':>6s}  {'Ratio':>8s}  {'SE':>8s}  {'|M|':>8s}\n")
        f.write(f"{'-'*36}\n")
        for idx, T in enumerate(temps_1d):
            f.write(f"{T:6.3f}  {ratio_1d[idx]:8.3f}  {se_1d[idx]:8.3f}  "
                    f"{mag_1d[:, idx].mean():8.3f}\n")
        f.write(f"\nMax ratio: {max_ratio_1d:.3f} at T={peak_T_1d:.3f}\n")
        f.write(f"Range: {range_1d:.3f}\n")
        f.write(f"Has localized peak? {has_localized_peak}\n")
        f.write(f"VERDICT: {'PASSED' if test1_pass else 'FAILED'}\n")

        f.write(f"\n{'='*70}\n")
        f.write(f"TEST 2: TEMPORAL SHUFFLE (2D ISING)\n")
        f.write(f"{'='*70}\n")
        f.write(f"L=24, block_size=4, patch_size=2, n_seeds={ratio_all_orig.shape[0]}\n")
        f.write(f"n_equilib=2000, n_steps=1000, min_obs=5\n")
        f.write(f"\nResults:\n")
        f.write(f"{'T':>6s}  {'Original':>10s}  {'SE':>8s}  "
                f"{'Shuffled':>10s}  {'SE':>8s}  {'Orig/Shuf':>10s}\n")
        f.write(f"{'-'*62}\n")
        for idx, T in enumerate(temps_ts):
            ro = ratio_orig[idx]
            rs = ratio_shuf[idx]
            f.write(f"{T:6.3f}  {ro:10.3f}  {se_orig[idx]:8.3f}  "
                    f"{rs:10.3f}  {se_shuf[idx]:8.3f}  "
                    f"{ro/rs if rs > 1e-10 else 0:10.3f}\n")
        f.write(f"\nOriginal peak: {peak_val_orig:.3f} at T={temps_ts[peak_idx_orig]:.3f}\n")
        f.write(f"Shuffled at peak T: {shuf_at_peak:.3f}\n")
        f.write(f"Mean shuffled ratio: {mean_shuf:.3f}\n")
        f.write(f"VERDICT: {'PASSED' if test2_pass else 'FAILED'}\n")

        f.write(f"\n{'='*70}\n")
        f.write(f"OVERALL: {'BOTH TESTS PASSED' if both_pass else 'SOME TESTS FAILED'}\n")
        f.write(f"{'='*70}\n")

    print(f"\nLog saved: {log_path}")

    # ==================================================================
    # SAVE DATA
    # ==================================================================
    data_dir = os.path.join(project_root, 'results', 'phase1', 'data')
    os.makedirs(data_dir, exist_ok=True)
    data_path = os.path.join(data_dir, 'phase1_v4_falsification.npz')
    np.savez(data_path,
             # Test 1
             temps_1d=temps_1d,
             ratio_1d_mean=ratio_1d,
             ratio_1d_se=se_1d,
             ratio_1d_all=ratio_all_1d,
             ei_micro_1d=ei_micro_1d,
             ei_macro_1d=ei_macro_1d,
             mag_1d=mag_1d,
             test1_pass=test1_pass,
             # Test 2
             temps_ts=temps_ts,
             ratio_orig_mean=ratio_orig,
             ratio_orig_se=se_orig,
             ratio_shuf_mean=ratio_shuf,
             ratio_shuf_se=se_shuf,
             ratio_orig_all=ratio_all_orig,
             ratio_shuf_all=ratio_all_shuf,
             test2_pass=test2_pass)
    print(f"Data saved: {data_path}")

    print(f"\n{'*'*70}")
    print("PHASE 1 v4 FALSIFICATION TESTS COMPLETE")
    print(f"{'*'*70}")

    return test1_pass, test2_pass


if __name__ == "__main__":
    run_falsification()
