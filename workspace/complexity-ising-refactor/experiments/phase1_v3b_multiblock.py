"""
Phase 1 v3b: Multi-Block-Size EI Experiment

CORE PREDICTION: EI(M)/EI(S) peaks where correlation length xi(T) ~ block_size b.
If true, different block sizes should produce peaks at DIFFERENT temperatures:
  - Smaller b -> peak at T closer to T_c (where xi is smaller)
  - Larger b  -> peak at T farther below T_c (where xi is larger)

This is the key falsifiable prediction of the causal emergence framework.

Design:
  - L=24 (divisible by 2,3,4,6,8,12)
  - block_sizes = [2, 3, 4, 6]
  - patch_size = 2 always (16 states at both scales)
  - Transition counts equalized (micro subsampled to match macro)
  - 5 seeds per temperature
  - 15 temperatures: np.arange(1.8, 2.55, 0.05)
  - min_obs = 5

Transition counts per block size (n_steps=2000, so 1999 transitions):
  b=2: macro grid 12x12, 6x6=36 macro patches -> 36*1999=71,964
  b=3: macro grid  8x8,  4x4=16 macro patches -> 16*1999=31,984
  b=4: macro grid  6x6,  3x3= 9 macro patches ->  9*1999=17,991
  b=6: macro grid  4x4,  2x2= 4 macro patches ->  4*1999= 7,996
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


def run_multiblock():
    """Execute Phase 1 v3b: Multi-block-size EI experiment."""
    print("=" * 70)
    print("PHASE 1 v3b: MULTI-BLOCK-SIZE EI EXPERIMENT")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ====================================================================
    # Parameters
    # ====================================================================
    L = 24
    temperatures = np.arange(1.8, 2.55, 0.05)
    n_equilib = 5000
    n_steps = 2000
    block_sizes = [2, 3, 4, 6]
    patch_size = 2  # 2x2 patches -> 16 states at both scales
    n_seeds = 5
    T_c = 2.269
    min_obs = 5

    n_temps = len(temperatures)

    print(f"\nParameters:")
    print(f"  L={L}, n_equilib={n_equilib}, n_steps={n_steps}")
    print(f"  Seeds: {n_seeds}, patch_size={patch_size}")
    print(f"  Block sizes: {block_sizes}")
    print(f"  Temperatures: {temperatures[0]:.2f} to {temperatures[-1]:.2f}, "
          f"step=0.05, n={n_temps}")
    print(f"  State space: 2^(2x2) = 16 states (equal for micro and macro)")
    print(f"  min_obs={min_obs}")
    print(f"  KEY FIX: Micro transitions subsampled to match macro count")

    # Print transition count info
    print(f"\n  Transition counts per block size:")
    for b in block_sizes:
        L_coarse = L // b
        n_macro_patches_per_side = L_coarse // patch_size
        n_macro_patches = n_macro_patches_per_side ** 2
        n_micro_patches_per_side = L // patch_size
        n_micro_patches = n_micro_patches_per_side ** 2
        n_trans = n_macro_patches * (n_steps - 1)
        print(f"    b={b}: macro grid {L_coarse}x{L_coarse}, "
              f"{n_macro_patches_per_side}x{n_macro_patches_per_side}="
              f"{n_macro_patches} macro patches -> "
              f"{n_trans:,} transitions (micro subsampled to match)")

    # ====================================================================
    # Storage
    # ====================================================================
    results = {}
    for b in block_sizes:
        results[b] = {
            'ei_micro': np.zeros((n_seeds, n_temps)),
            'ei_macro': np.zeros((n_seeds, n_temps)),
            'ratio': np.zeros((n_seeds, n_temps)),
            'n_rows_micro': np.zeros((n_seeds, n_temps), dtype=int),
            'n_rows_macro': np.zeros((n_seeds, n_temps), dtype=int),
            'n_transitions': np.zeros((n_seeds, n_temps), dtype=int),
        }

    total_start = time.time()

    # ====================================================================
    # Main simulation loop
    # ====================================================================
    for idx, T in enumerate(temperatures):
        t0 = time.time()
        print(f"\n{'='*60}")
        print(f"T = {T:.3f} ({idx+1}/{n_temps})")
        print(f"{'='*60}", flush=True)

        for s in range(n_seeds):
            seed = 1000 * s + idx
            rng = np.random.RandomState(seed + 99999)

            # Simulate once, reuse across all block sizes
            configs, mags = simulate_ising(L, T, n_steps, n_equilib, seed=seed)

            for b in block_sizes:
                # Coarse-grain at this block size
                coarse = coarsegrain_timeseries(configs, b)

                # Compute equalized EI
                ei_s, ei_m, n_trans, nr_s, nr_m = compute_ei_equalized(
                    configs, coarse, patch_size, min_obs, rng
                )

                results[b]['ei_micro'][s, idx] = ei_s
                results[b]['ei_macro'][s, idx] = ei_m
                results[b]['ratio'][s, idx] = ei_m / ei_s if ei_s > 1e-10 else np.nan
                results[b]['n_rows_micro'][s, idx] = nr_s
                results[b]['n_rows_macro'][s, idx] = nr_m
                results[b]['n_transitions'][s, idx] = n_trans

        elapsed = time.time() - t0

        # Print summary for this temperature
        for b in block_sizes:
            mean_ratio = np.nanmean(results[b]['ratio'][:, idx])
            mean_micro = results[b]['ei_micro'][:, idx].mean()
            mean_macro = results[b]['ei_macro'][:, idx].mean()
            mean_rows_s = results[b]['n_rows_micro'][:, idx].mean()
            mean_rows_m = results[b]['n_rows_macro'][:, idx].mean()
            n_trans = results[b]['n_transitions'][0, idx]
            print(f"  b={b}: EI(S)={mean_micro:.4f}, EI(M)={mean_macro:.4f}, "
                  f"Ratio={mean_ratio:.3f}, "
                  f"Rows: S={mean_rows_s:.1f}/16, M={mean_rows_m:.1f}/16, "
                  f"trans={n_trans:,}")

        print(f"  Time: {elapsed:.1f}s ({n_seeds} seeds x {len(block_sizes)} block sizes)")

    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print(f"SIMULATION COMPLETE — Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"{'='*70}")

    # ====================================================================
    # ANALYSIS: EI Ratio vs Temperature for each block size
    # ====================================================================
    print(f"\n{'='*70}")
    print("ANALYSIS: EI(M)/EI(S) vs Temperature by Block Size")
    print(f"{'='*70}")

    peak_temperatures = {}

    for b in block_sizes:
        data = results[b]
        # Paired ratio: per-seed ratio, then average
        paired_ratio = np.nanmean(data['ratio'], axis=0)
        paired_ratio_se = np.nanstd(data['ratio'], axis=0) / np.sqrt(n_seeds)

        # Find peak temperature (restrict to T < T_c + 0.1)
        mask = temperatures < T_c + 0.1
        valid = paired_ratio[mask]
        if np.any(np.isfinite(valid)):
            peak_idx = np.nanargmax(valid)
            peak_T = temperatures[mask][peak_idx]
            peak_val = valid[peak_idx]
        else:
            peak_T = np.nan
            peak_val = np.nan

        peak_temperatures[b] = peak_T

        print(f"\n  Block size b={b}:")
        print(f"    Peak temperature: {peak_T:.3f}")
        print(f"    Peak EI(M)/EI(S): {peak_val:.3f}")
        print(f"    Lead time (T_c - T_peak): {T_c - peak_T:.3f}")

        # Per-seed peak analysis
        per_seed_peaks = []
        for s_idx in range(n_seeds):
            ratio_curve = data['ratio'][s_idx, :]
            v = ratio_curve[mask]
            if np.any(np.isfinite(v)):
                p_idx = np.nanargmax(v)
                per_seed_peaks.append(temperatures[mask][p_idx])
            else:
                per_seed_peaks.append(np.nan)
        per_seed_peaks = np.array(per_seed_peaks)
        valid_peaks = per_seed_peaks[np.isfinite(per_seed_peaks)]
        if len(valid_peaks) > 0:
            print(f"    Per-seed peak mean: {valid_peaks.mean():.3f} +/- {valid_peaks.std():.3f}")
            print(f"    Per-seed peak range: [{valid_peaks.min():.3f}, {valid_peaks.max():.3f}]")

        # Print full curve
        print(f"    {'T':>6s}  {'Ratio':>8s}  {'SE':>8s}  {'EI(S)':>8s}  {'EI(M)':>8s}")
        for ti in range(n_temps):
            print(f"    {temperatures[ti]:6.3f}  {paired_ratio[ti]:8.3f}  "
                  f"{paired_ratio_se[ti]:8.4f}  "
                  f"{data['ei_micro'][:, ti].mean():8.4f}  "
                  f"{data['ei_macro'][:, ti].mean():8.4f}")

    # ====================================================================
    # KEY TEST: Do peaks shift with block size?
    # ====================================================================
    print(f"\n{'='*70}")
    print("KEY TEST: Peak Temperature vs Block Size")
    print(f"{'='*70}")
    print(f"\n  {'Block Size':>10s}  {'Peak T':>8s}  {'Lead Time':>10s}")
    print(f"  {'-'*10}  {'-'*8}  {'-'*10}")
    for b in block_sizes:
        pt = peak_temperatures[b]
        lead = T_c - pt
        print(f"  {b:>10d}  {pt:>8.3f}  {lead:>10.3f}")

    sorted_peaks = [peak_temperatures[b] for b in block_sizes]
    if all(np.isfinite(sorted_peaks)):
        # Check if larger block sizes have peaks at lower temperatures
        monotonic_decreasing = all(sorted_peaks[i] >= sorted_peaks[i+1]
                                   for i in range(len(sorted_peaks)-1))
        monotonic_increasing = all(sorted_peaks[i] <= sorted_peaks[i+1]
                                   for i in range(len(sorted_peaks)-1))
        print(f"\n  Peaks monotonically decrease with b? {monotonic_decreasing}")
        print(f"  Peaks monotonically increase with b? {monotonic_increasing}")
        print(f"  T_c = {T_c:.3f}")

        if monotonic_decreasing:
            print(f"\n  RESULT: Peaks shift to LOWER T with larger b.")
            print(f"  This is CONSISTENT with the prediction xi(T_peak) ~ b:")
            print(f"  Larger b requires larger xi, which occurs farther below T_c.")
        elif monotonic_increasing:
            print(f"\n  RESULT: Peaks shift to HIGHER T with larger b.")
            print(f"  This would CONTRADICT the simple xi ~ b prediction.")
        else:
            print(f"\n  RESULT: Non-monotonic relationship between peak T and b.")
            print(f"  The xi ~ b prediction is not cleanly supported.")
    else:
        print(f"\n  WARNING: Some peak temperatures are NaN.")

    # ====================================================================
    # PLOTS
    # ====================================================================
    print(f"\n\nGenerating plots...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    project_root = os.path.join(os.path.dirname(__file__), '..')
    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    # --- Main comparison plot ---
    fig, ax = plt.subplots(figsize=(12, 7))

    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red']
    markers = ['o', 's', '^', 'D']

    for i, b in enumerate(block_sizes):
        data = results[b]
        paired_ratio = np.nanmean(data['ratio'], axis=0)
        paired_ratio_se = np.nanstd(data['ratio'], axis=0) / np.sqrt(n_seeds)
        finite = np.isfinite(paired_ratio)

        peak_T = peak_temperatures[b]
        label = f'b={b} (peak T={peak_T:.2f})'

        ax.errorbar(temperatures[finite], paired_ratio[finite],
                    yerr=paired_ratio_se[finite],
                    fmt=f'{markers[i]}-', color=colors[i],
                    markersize=5, capsize=3, linewidth=1.5,
                    label=label)

        # Mark the peak with a larger marker
        if np.isfinite(peak_T):
            peak_mask = np.abs(temperatures - peak_T) < 0.001
            if np.any(peak_mask):
                peak_val = paired_ratio[peak_mask][0]
                ax.plot(peak_T, peak_val, marker=markers[i], color=colors[i],
                        markersize=12, markeredgecolor='black', markeredgewidth=1.5,
                        zorder=5)

    ax.axvline(T_c, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=f'$T_c$ = {T_c:.3f}')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5, label='EI ratio = 1')

    ax.set_xlabel('Temperature', fontsize=13)
    ax.set_ylabel('EI(M) / EI(S)', fontsize=13)
    ax.set_title('Multi-Block-Size EI Ratio\n'
                 'Prediction: Peak shifts to lower T with larger block size b',
                 fontsize=14)
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=11)

    plt.tight_layout()
    save_path = os.path.join(plot_dir, 'v3b_multiblock_comparison.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")

    # --- Plot 2: Raw EI values for each block size ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.ravel()

    for i, b in enumerate(block_sizes):
        ax = axes[i]
        data = results[b]

        ei_micro_mean = data['ei_micro'].mean(axis=0)
        ei_micro_se = data['ei_micro'].std(axis=0) / np.sqrt(n_seeds)
        ei_macro_mean = data['ei_macro'].mean(axis=0)
        ei_macro_se = data['ei_macro'].std(axis=0) / np.sqrt(n_seeds)

        ax.errorbar(temperatures, ei_micro_mean, yerr=ei_micro_se,
                    fmt='ko-', markersize=3, capsize=2, linewidth=1,
                    label=f'EI(S) micro [equalized to {data["n_transitions"][0,0]:,}]')
        ax.errorbar(temperatures, ei_macro_mean, yerr=ei_macro_se,
                    fmt='o-', color=colors[i], markersize=3, capsize=2, linewidth=1,
                    label=f'EI(M) macro')

        ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
        ax.set_xlabel('Temperature')
        ax.set_ylabel('Effective Information (bits)')
        ax.set_title(f'Block size b={b}  |  Peak at T={peak_temperatures[b]:.2f}')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.suptitle('Raw EI Values by Block Size (equalized transitions)', fontsize=14)
    plt.tight_layout()
    save_path2 = os.path.join(plot_dir, 'v3b_multiblock_raw_ei.png')
    plt.savefig(save_path2, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path2}")

    # --- Plot 3: Peak T vs block size ---
    fig, ax = plt.subplots(figsize=(8, 6))
    bs_arr = np.array(block_sizes)
    peaks_arr = np.array([peak_temperatures[b] for b in block_sizes])

    ax.plot(bs_arr, peaks_arr, 'ko-', markersize=10, linewidth=2)
    for i, b in enumerate(block_sizes):
        ax.annotate(f'T={peaks_arr[i]:.2f}', (bs_arr[i], peaks_arr[i]),
                    textcoords="offset points", xytext=(10, 10), fontsize=11)

    ax.axhline(T_c, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=f'$T_c$ = {T_c:.3f}')
    ax.set_xlabel('Block Size b', fontsize=13)
    ax.set_ylabel('Peak Temperature', fontsize=13)
    ax.set_title('Peak Temperature vs Block Size\n'
                 'Prediction: Larger b -> peak at lower T (larger correlation length needed)',
                 fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(block_sizes)
    ax.tick_params(labelsize=11)

    plt.tight_layout()
    save_path3 = os.path.join(plot_dir, 'v3b_multiblock_peak_vs_b.png')
    plt.savefig(save_path3, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path3}")

    # ====================================================================
    # SAVE DATA
    # ====================================================================
    data_dir = os.path.join(project_root, 'results', 'phase1', 'data')
    os.makedirs(data_dir, exist_ok=True)

    save_dict = {
        'temperatures': temperatures,
        'T_c': T_c,
        'L': L,
        'n_seeds': n_seeds,
        'block_sizes': np.array(block_sizes),
        'patch_size': patch_size,
        'min_obs': min_obs,
        'n_steps': n_steps,
        'n_equilib': n_equilib,
    }

    for b in block_sizes:
        for key, arr in results[b].items():
            save_dict[f'b{b}_{key}'] = arr
        save_dict[f'b{b}_peak_T'] = peak_temperatures[b]

    npz_path = os.path.join(data_dir, 'phase1_v3b_multiblock.npz')
    np.savez(npz_path, **save_dict)
    print(f"\nData saved to {npz_path}")

    # ====================================================================
    # FINAL SUMMARY
    # ====================================================================
    print(f"\n{'='*70}")
    print("FINAL SUMMARY — MULTI-BLOCK-SIZE EI EXPERIMENT")
    print(f"{'='*70}")
    print(f"\n  T_c = {T_c:.3f}")
    print(f"\n  {'b':>3s}  {'Peak T':>8s}  {'Lead (T_c-T)':>12s}  {'Peak Ratio':>12s}")
    print(f"  {'-'*3}  {'-'*8}  {'-'*12}  {'-'*12}")
    for b in block_sizes:
        pt = peak_temperatures[b]
        lead = T_c - pt
        mask = temperatures < T_c + 0.1
        paired_ratio = np.nanmean(results[b]['ratio'], axis=0)
        valid = paired_ratio[mask]
        peak_val = np.nanmax(valid) if np.any(np.isfinite(valid)) else np.nan
        print(f"  {b:>3d}  {pt:>8.3f}  {lead:>12.3f}  {peak_val:>12.3f}")

    print(f"\n  Total runtime: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_multiblock()
