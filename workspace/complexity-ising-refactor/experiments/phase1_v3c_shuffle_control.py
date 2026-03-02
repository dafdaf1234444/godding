"""
Phase 1 v3c: Spatial Shuffle Control Experiment

MOTIVATION:
Phase 1 v3 showed EI(M)/EI(S) peaks at ~6.45 at T=2.15 using block_size=4
spatial coarse-graining. The claim is that majority-vote of SPATIALLY ADJACENT
spins filters noise because of spatial correlations near criticality.

THE CONTROL:
If we randomly reassign which spins belong to which macro "block" (destroying
spatial locality), the emergence signal should VANISH. If it persists, the
signal is a trivial consequence of majority vote, not spatial correlations.

METHOD:
For each (T, seed):
1. Run Ising simulation on L=24
2. REAL macro: standard coarsegrain with block_size=4 (spatially adjacent 4x4 blocks)
3. SHUFFLED macro:
   - Take the L*L spin grid at each time step
   - Create a fixed random permutation of all L*L=576 spin indices
     (same permutation for all time steps within a seed)
   - Reshape the permuted spins into (L,L) grid
   - Apply the SAME coarsegrain_timeseries(permuted_grid, block_size=4)
   - Preserves: spin statistics, majority-vote operation, number of macro patches
   - Destroys: spatial correlations between spins within a block
4. Compute EI for equalized micro, real macro, and shuffled macro
5. Compare EI(M)/EI(S) for real vs shuffled
"""

import sys
import os
import time
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ising import simulate_ising
from src.coarse_grain import coarsegrain_timeseries
from src.ei_compute import estimate_transition_matrix, effective_information, compute_ei_equalized
from src.coarse_grain import config_to_patch_states


def shuffle_configs(configs, rng):
    """
    Spatially shuffle spin configurations, destroying spatial locality.

    Creates a fixed random permutation of all L*L spin indices, then
    applies this SAME permutation to every time step. This preserves:
    - The distribution of spin values at each time step
    - The temporal dynamics of individual spins
    - The total number of +1/-1 spins per step
    But destroys spatial correlations between spins within any block.

    Parameters
    ----------
    configs : ndarray of shape (N, L, L) with values +1/-1
    rng : np.random.RandomState

    Returns
    -------
    shuffled : ndarray of shape (N, L, L) with values +1/-1
    """
    N, L, _ = configs.shape
    n_spins = L * L

    # Create one fixed permutation for all time steps
    perm = rng.permutation(n_spins)

    # Apply permutation: flatten each config, permute, reshape
    flat = configs.reshape(N, n_spins)
    shuffled_flat = flat[:, perm]
    shuffled = shuffled_flat.reshape(N, L, L)

    return shuffled


def run_shuffle_control():
    """Execute the spatial shuffle control experiment."""
    print("=" * 70)
    print("PHASE 1 v3c: SPATIAL SHUFFLE CONTROL")
    print("=" * 70)
    print()
    print("HYPOTHESIS: The EI(M)/EI(S) peak near T_c is driven by spatial")
    print("correlations exploited by block coarse-graining. If we shuffle")
    print("spin positions (destroying spatial locality) before coarse-graining,")
    print("the emergence signal should vanish.")
    print()

    # Parameters
    L = 24
    temperatures = np.arange(1.8, 2.55, 0.05)
    n_equilib = 5000
    n_steps = 2000
    block_size = 4
    patch_size = 2
    n_seeds = 5
    T_c = 2.269
    min_obs = 5

    n_temps = len(temperatures)
    print(f"Parameters:")
    print(f"  L={L}, n_equilib={n_equilib}, n_steps={n_steps}")
    print(f"  Seeds: {n_seeds}, block_size={block_size}, patch_size={patch_size}")
    print(f"  Temperatures: {n_temps} values from {temperatures[0]:.2f} to {temperatures[-1]:.2f}")
    print(f"  min_obs={min_obs}")
    print(f"  State space: 2^(2x2) = 16 states")
    print(f"  Micro patches: {(L//patch_size)**2} = {(L//patch_size)**2}")
    print(f"  Macro patches (real & shuffled): {(L//block_size//patch_size)**2} = {(L//block_size//patch_size)**2}")
    print()

    # Storage arrays
    ei_micro_real = np.zeros((n_seeds, n_temps))     # EI(S) equalized to real macro count
    ei_macro_real = np.zeros((n_seeds, n_temps))      # EI(M) from spatially adjacent blocks
    ratio_real = np.zeros((n_seeds, n_temps))

    ei_micro_shuf = np.zeros((n_seeds, n_temps))     # EI(S) equalized to shuffled macro count
    ei_macro_shuf = np.zeros((n_seeds, n_temps))      # EI(M) from shuffled blocks
    ratio_shuf = np.zeros((n_seeds, n_temps))

    total_start = time.time()

    for idx, T in enumerate(temperatures):
        t0 = time.time()
        print(f"--- T = {T:.3f} ({idx+1}/{n_temps}) ---", flush=True)

        for s in range(n_seeds):
            seed = 1000 * s + idx
            rng_eq = np.random.RandomState(seed + 99999)       # for micro equalization (real)
            rng_eq_shuf = np.random.RandomState(seed + 199999) # for micro equalization (shuffled)
            rng_shuffle = np.random.RandomState(seed + 299999) # for spatial shuffle permutation

            # 1. Run Ising simulation
            configs, mags = simulate_ising(L, T, n_steps, n_equilib, seed=seed)

            # 2. REAL macro: standard spatial coarse-graining
            coarse_real = coarsegrain_timeseries(configs, block_size)

            # 3. SHUFFLED macro: permute spin positions, then coarse-grain
            configs_shuffled = shuffle_configs(configs, rng_shuffle)
            coarse_shuf = coarsegrain_timeseries(configs_shuffled, block_size)

            # 4. Compute EI for real macro (with equalized micro)
            ei_s_r, ei_m_r, _, _, _ = compute_ei_equalized(
                configs, coarse_real, patch_size, min_obs, rng_eq
            )
            ei_micro_real[s, idx] = ei_s_r
            ei_macro_real[s, idx] = ei_m_r
            ratio_real[s, idx] = ei_m_r / ei_s_r if ei_s_r > 1e-10 else np.nan

            # 5. Compute EI for shuffled macro (with equalized micro)
            ei_s_sh, ei_m_sh, _, _, _ = compute_ei_equalized(
                configs, coarse_shuf, patch_size, min_obs, rng_eq_shuf
            )
            ei_micro_shuf[s, idx] = ei_s_sh
            ei_macro_shuf[s, idx] = ei_m_sh
            ratio_shuf[s, idx] = ei_m_sh / ei_s_sh if ei_s_sh > 1e-10 else np.nan

        elapsed = time.time() - t0

        # Per-temperature summary
        mean_ratio_real = np.nanmean(ratio_real[:, idx])
        mean_ratio_shuf = np.nanmean(ratio_shuf[:, idx])
        se_real = np.nanstd(ratio_real[:, idx]) / np.sqrt(n_seeds)
        se_shuf = np.nanstd(ratio_shuf[:, idx]) / np.sqrt(n_seeds)

        print(f"  REAL:     EI(M)/EI(S) = {mean_ratio_real:.3f} +/- {se_real:.3f}  "
              f"[EI(S)={np.mean(ei_micro_real[:, idx]):.4f}, EI(M)={np.mean(ei_macro_real[:, idx]):.4f}]")
        print(f"  SHUFFLED: EI(M)/EI(S) = {mean_ratio_shuf:.3f} +/- {se_shuf:.3f}  "
              f"[EI(S)={np.mean(ei_micro_shuf[:, idx]):.4f}, EI(M)={np.mean(ei_macro_shuf[:, idx]):.4f}]")
        print(f"  Time: {elapsed:.1f}s", flush=True)

    total_elapsed = time.time() - total_start
    print(f"\nTotal simulation time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # ====================================================================
    # ANALYSIS
    # ====================================================================
    print("\n" + "=" * 70)
    print("ANALYSIS: REAL vs SHUFFLED")
    print("=" * 70)

    mean_ratio_real_all = np.nanmean(ratio_real, axis=0)
    se_ratio_real_all = np.nanstd(ratio_real, axis=0) / np.sqrt(n_seeds)
    mean_ratio_shuf_all = np.nanmean(ratio_shuf, axis=0)
    se_ratio_shuf_all = np.nanstd(ratio_shuf, axis=0) / np.sqrt(n_seeds)

    print(f"\n{'T':>6s}  {'Real':>10s}  {'SE':>8s}  {'Shuffled':>10s}  {'SE':>8s}  {'Real/Shuf':>10s}")
    print("-" * 62)
    for idx, T in enumerate(temperatures):
        rr = mean_ratio_real_all[idx]
        rs = mean_ratio_shuf_all[idx]
        ratio_ratio = rr / rs if rs > 1e-10 else np.nan
        print(f"{T:6.3f}  {rr:10.3f}  {se_ratio_real_all[idx]:8.3f}  "
              f"{rs:10.3f}  {se_ratio_shuf_all[idx]:8.3f}  {ratio_ratio:10.3f}")

    # Peak analysis
    peak_idx_real = np.nanargmax(mean_ratio_real_all)
    peak_idx_shuf = np.nanargmax(mean_ratio_shuf_all)
    peak_T_real = temperatures[peak_idx_real]
    peak_T_shuf = temperatures[peak_idx_shuf]
    peak_val_real = mean_ratio_real_all[peak_idx_real]
    peak_val_shuf = mean_ratio_shuf_all[peak_idx_shuf]

    print(f"\nPeak analysis:")
    print(f"  REAL:     Peak EI(M)/EI(S) = {peak_val_real:.3f} at T = {peak_T_real:.3f}")
    print(f"  SHUFFLED: Peak EI(M)/EI(S) = {peak_val_shuf:.3f} at T = {peak_T_shuf:.3f}")
    print(f"  Peak ratio (real/shuffled):   {peak_val_real/peak_val_shuf:.3f}")

    # How many temperatures show emergence (ratio > 1)?
    n_emerge_real = np.sum(mean_ratio_real_all > 1.0)
    n_emerge_shuf = np.sum(mean_ratio_shuf_all > 1.0)
    print(f"\nEmergence (ratio > 1.0):")
    print(f"  REAL:     {n_emerge_real}/{n_temps} temperatures")
    print(f"  SHUFFLED: {n_emerge_shuf}/{n_temps} temperatures")

    # Check if shuffled is consistently near 1.0
    near_one_shuf = np.sum(np.abs(mean_ratio_shuf_all - 1.0) < 0.5)
    print(f"  Shuffled near 1.0 (within 0.5): {near_one_shuf}/{n_temps} temperatures")

    # Verdict
    print(f"\n{'='*70}")
    if peak_val_real > 2.0 * peak_val_shuf:
        print("VERDICT: Spatial shuffle DESTROYS the emergence signal.")
        print("The EI(M)/EI(S) peak is driven by SPATIAL CORRELATIONS,")
        print("not a trivial artifact of majority-vote.")
    elif peak_val_real > 1.3 * peak_val_shuf:
        print("VERDICT: Spatial shuffle REDUCES the emergence signal.")
        print("Spatial correlations contribute, but majority-vote also plays a role.")
    else:
        print("VERDICT: Spatial shuffle has LITTLE EFFECT on the emergence signal.")
        print("WARNING: The signal may be a trivial consequence of majority-vote.")
    print(f"{'='*70}")

    # ====================================================================
    # PLOTS
    # ====================================================================
    print("\nGenerating plots...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    project_root = os.path.join(os.path.dirname(__file__), '..')
    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})

    # --- Top panel: Real vs Shuffled EI(M)/EI(S) ---
    ax = axes[0]
    ax.errorbar(temperatures, mean_ratio_real_all, yerr=se_ratio_real_all,
                fmt='o-', color='tab:blue', markersize=5, capsize=3, linewidth=2,
                label=f'Real (spatial blocks) — peak={peak_val_real:.2f} at T={peak_T_real:.2f}')
    ax.errorbar(temperatures, mean_ratio_shuf_all, yerr=se_ratio_shuf_all,
                fmt='s--', color='tab:red', markersize=5, capsize=3, linewidth=2,
                label=f'Shuffled (random blocks) — peak={peak_val_shuf:.2f} at T={peak_T_shuf:.2f}')
    ax.axvline(T_c, color='black', linestyle='--', linewidth=1.5, alpha=0.7,
               label=f'$T_c$ = {T_c:.3f}')
    ax.axhline(1.0, color='gray', linestyle=':', linewidth=1, alpha=0.5,
               label='EI(M)/EI(S) = 1')

    ax.set_ylabel('EI(M) / EI(S)', fontsize=13)
    ax.set_title('Spatial Shuffle Control: Does Emergence Require Spatial Locality?',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(temperatures[0] - 0.02, temperatures[-1] + 0.02)

    # --- Bottom panel: Ratio of ratios (Real/Shuffled) ---
    ax = axes[1]
    ratio_of_ratios = mean_ratio_real_all / np.where(mean_ratio_shuf_all > 1e-10,
                                                      mean_ratio_shuf_all, np.nan)
    ax.plot(temperatures, ratio_of_ratios, 'D-', color='tab:purple', markersize=5,
            linewidth=2, label='Real / Shuffled')
    ax.axvline(T_c, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axhline(1.0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlabel('Temperature', fontsize=13)
    ax.set_ylabel('Real / Shuffled', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(temperatures[0] - 0.02, temperatures[-1] + 0.02)

    plt.tight_layout()
    plot_path = os.path.join(plot_dir, 'v3c_shuffle_control.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot_path}")

    # ====================================================================
    # SAVE DATA
    # ====================================================================
    data_dir = os.path.join(project_root, 'results', 'phase1', 'data')
    os.makedirs(data_dir, exist_ok=True)

    save_path = os.path.join(data_dir, 'phase1_v3c_shuffle.npz')
    np.savez(save_path,
             temperatures=temperatures,
             T_c=T_c,
             L=L,
             n_seeds=n_seeds,
             block_size=block_size,
             patch_size=patch_size,
             min_obs=min_obs,
             # Per-seed arrays
             ei_micro_real=ei_micro_real,
             ei_macro_real=ei_macro_real,
             ratio_real=ratio_real,
             ei_micro_shuf=ei_micro_shuf,
             ei_macro_shuf=ei_macro_shuf,
             ratio_shuf=ratio_shuf,
             # Mean arrays
             mean_ratio_real=mean_ratio_real_all,
             se_ratio_real=se_ratio_real_all,
             mean_ratio_shuf=mean_ratio_shuf_all,
             se_ratio_shuf=se_ratio_shuf_all,
             ratio_of_ratios=ratio_of_ratios,
             peak_val_real=peak_val_real,
             peak_T_real=peak_T_real,
             peak_val_shuf=peak_val_shuf,
             peak_T_shuf=peak_T_shuf)
    print(f"  Saved: {save_path}")

    print(f"\n{'='*70}")
    print("PHASE 1 v3c SPATIAL SHUFFLE CONTROL COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_shuffle_control()
