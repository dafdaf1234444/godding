"""
Phase 1 v4: Finite-Size Scaling of the EI Emergence Signal

Motivation:
  v3 showed EI(M)/EI(S) peaks at T~2.15 for L=24, b=4.
  We need to determine if this is a finite-size artifact.
  The peak occurs where xi ~ 10 ~ 2.5*b. Since xi=10 << L=24,
  the peak SHOULD persist at larger L. But if it shifts or
  disappears, it is an artifact.

Predictions:
  - L=16: Peak at 2.10-2.15 (xi ~ L, might shift)
  - L=24: Peak at 2.15 (already measured)
  - L=32: Peak at 2.15 (xi << L, no shift)
  - L=48: Peak at 2.15 (xi << L, no shift)

Design:
  - L_values = [16, 24, 32, 48]
  - block_size = 4 (consistent with v3)
  - patch_size = 2 (16 states)
  - 5 seeds per temperature
  - Temperatures: np.arange(1.8, 2.55, 0.05) = 15 temps
  - min_obs = 5
  - EQUALIZED transitions: subsample micro to match macro count
  - For each L: macro grid = (L/4) x (L/4), patches = (L/4/2)^2
  - n_steps=500, n_equilib=2000 (reduced for tractability; still sufficient
    for transition statistics with multiple seeds)

Transition counts by L (per seed, n_steps=500):
  - L=16: macro grid 4x4, patches 2x2=4  -> 4*499 =  1,996 (VERY few)
  - L=24: macro grid 6x6, patches 3x3=9  -> 9*499 =  4,491
  - L=32: macro grid 8x8, patches 4x4=16 -> 16*499=  7,984
  - L=48: macro grid 12x12, patches 6x6=36-> 36*499= 17,964

CAVEAT: L=16 has very few macro transitions (~2K). Results may be noisy.
NOTE: Fewer steps than v3 (500 vs 2000) but 5 seeds provide replication.
"""

import sys
import os
import time
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ising import simulate_ising
from src.coarse_grain import coarsegrain_timeseries, config_to_patch_states
from src.ei_compute import estimate_transition_matrix, effective_information, compute_ei_equalized


def run_phase1_v4():
    """Execute Phase 1 v4 -- Finite-Size Scaling experiment."""
    print("=" * 70)
    print("PHASE 1 v4: FINITE-SIZE SCALING OF EI EMERGENCE SIGNAL")
    print("=" * 70)

    # Parameters
    L_values = [16, 24, 32, 48]
    temperatures = np.arange(1.8, 2.55, 0.05)
    n_equilib = 2000   # Reduced from 5000 for tractability
    n_steps = 500      # Reduced from 2000; still gives enough transitions
    block_size = 4
    patch_size = 2  # 2x2 patches -> 16 states
    n_seeds = 5
    T_c = 2.269
    min_obs = 5

    n_temps = len(temperatures)
    print(f"\nParameters:")
    print(f"  L_values = {L_values}")
    print(f"  Temperatures: {temperatures[0]:.2f} to {temperatures[-1]:.2f}, "
          f"step=0.05, n_temps={n_temps}")
    print(f"  n_equilib={n_equilib}, n_steps={n_steps}")
    print(f"  Seeds: {n_seeds}, block_size={block_size}, patch_size={patch_size}")
    print(f"  State space: 2^(2x2) = 16 states")
    print(f"  min_obs={min_obs}")
    print(f"  KEY: Micro transitions subsampled to match macro count")
    print(f"  T_c = {T_c:.3f}")

    # Report expected transition counts
    print(f"\nExpected macro transition counts per seed:")
    for L in L_values:
        L_coarse = L // block_size
        n_macro_patches = (L_coarse // patch_size) ** 2
        n_trans = n_macro_patches * (n_steps - 1)
        print(f"  L={L:2d}: macro grid {L_coarse}x{L_coarse}, "
              f"patches {L_coarse//patch_size}x{L_coarse//patch_size}={n_macro_patches}, "
              f"transitions={n_trans:,}")
    print(f"  CAVEAT: L=16 has very few macro transitions (7,996). Results may be noisy.")

    # Storage: per L, per seed, per temperature
    all_results = {}
    for L in L_values:
        all_results[L] = {
            'ei_micro': np.zeros((n_seeds, n_temps)),
            'ei_macro': np.zeros((n_seeds, n_temps)),
            'ratio': np.zeros((n_seeds, n_temps)),
            'n_rows_micro': np.zeros((n_seeds, n_temps), dtype=int),
            'n_rows_macro': np.zeros((n_seeds, n_temps), dtype=int),
            'n_transitions': np.zeros((n_seeds, n_temps), dtype=int),
            'mag_var': np.zeros((n_seeds, n_temps)),
            'mag_ac': np.zeros((n_seeds, n_temps)),
        }

    total_start = time.time()

    for li, L in enumerate(L_values):
        L_start = time.time()
        print(f"\n{'='*60}")
        print(f"  L = {L}  ({li+1}/{len(L_values)})")
        print(f"{'='*60}")

        for idx, T in enumerate(temperatures):
            t0 = time.time()

            for s in range(n_seeds):
                # Seed scheme: unique per (L, T, seed)
                seed = 10000 * li + 1000 * s + idx
                rng = np.random.RandomState(seed + 99999)

                configs, mags = simulate_ising(L, T, n_steps, n_equilib, seed=seed)

                # Standard EWS
                all_results[L]['mag_var'][s, idx] = mags.var()
                x, y = mags[:-1], mags[1:]
                mx, my, sx, sy = x.mean(), y.mean(), x.std(), y.std()
                if sx > 0 and sy > 0:
                    all_results[L]['mag_ac'][s, idx] = np.mean((x-mx)*(y-my))/(sx*sy)
                else:
                    all_results[L]['mag_ac'][s, idx] = 0.0

                # Coarse-grain
                coarse = coarsegrain_timeseries(configs, block_size)

                # Compute EI
                ei_s, ei_m, n_trans, nr_s, nr_m = compute_ei_equalized(
                    configs, coarse, patch_size, min_obs, rng
                )

                all_results[L]['ei_micro'][s, idx] = ei_s
                all_results[L]['ei_macro'][s, idx] = ei_m
                all_results[L]['ratio'][s, idx] = ei_m / ei_s if ei_s > 1e-10 else np.nan
                all_results[L]['n_rows_micro'][s, idx] = nr_s
                all_results[L]['n_rows_macro'][s, idx] = nr_m
                all_results[L]['n_transitions'][s, idx] = n_trans

            elapsed = time.time() - t0
            res = all_results[L]
            mean_ratio = np.nanmean(res['ratio'][:, idx])
            mean_micro = res['ei_micro'][:, idx].mean()
            mean_macro = res['ei_macro'][:, idx].mean()
            print(f"  T={T:.3f}: EI(S)={mean_micro:.4f}, EI(M)={mean_macro:.4f}, "
                  f"Ratio={mean_ratio:.3f}, trans={res['n_transitions'][0,idx]}, "
                  f"{elapsed:.1f}s", flush=True)

        L_elapsed = time.time() - L_start
        print(f"  L={L} total: {L_elapsed:.1f}s ({L_elapsed/60:.1f} min)")

    total_elapsed = time.time() - total_start
    print(f"\nTotal time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # ====================================================================
    # ANALYSIS
    # ====================================================================
    print("\n" + "=" * 70)
    print("PHASE 1 v4 ANALYSIS: FINITE-SIZE SCALING")
    print("=" * 70)

    project_root = os.path.join(os.path.dirname(__file__), '..')

    # --- Per-L peak analysis ---
    print(f"\n--- Peak Temperature vs System Size ---")
    peak_temps_by_L = {}
    per_seed_peaks_by_L = {}
    peak_ratios_by_L = {}

    for L in L_values:
        res = all_results[L]
        ratio_mean = np.nanmean(res['ratio'], axis=0)
        ratio_se = np.nanstd(res['ratio'], axis=0) / np.sqrt(n_seeds)

        # Mean curve peak (T < T_c + 0.1)
        mask = temperatures < T_c + 0.1
        valid = ratio_mean[mask]
        if np.any(np.isfinite(valid)):
            peak_idx = np.nanargmax(valid)
            peak_T = temperatures[mask][peak_idx]
            peak_ratio = valid[peak_idx]
            peak_se = ratio_se[mask][peak_idx]
        else:
            peak_T = np.nan
            peak_ratio = np.nan
            peak_se = np.nan

        # Per-seed peak locations
        seed_peaks = []
        seed_peak_ratios = []
        for s in range(n_seeds):
            ratio_curve = res['ratio'][s, :]
            v = ratio_curve[mask]
            if np.any(np.isfinite(v)):
                pidx = np.nanargmax(v)
                seed_peaks.append(temperatures[mask][pidx])
                seed_peak_ratios.append(v[pidx])
            else:
                seed_peaks.append(np.nan)
                seed_peak_ratios.append(np.nan)

        seed_peaks = np.array(seed_peaks)
        seed_peak_ratios = np.array(seed_peak_ratios)
        valid_peaks = seed_peaks[np.isfinite(seed_peaks)]

        peak_temps_by_L[L] = peak_T
        per_seed_peaks_by_L[L] = seed_peaks
        peak_ratios_by_L[L] = peak_ratio

        n_macro_patches = (L // block_size // patch_size) ** 2
        n_trans = n_macro_patches * (n_steps - 1)

        print(f"\n  L={L:2d}:")
        print(f"    Mean curve peak T: {peak_T:.3f}, ratio={peak_ratio:.3f} +/- {peak_se:.3f}")
        if len(valid_peaks) > 0:
            print(f"    Per-seed peaks: mean={valid_peaks.mean():.3f} +/- {valid_peaks.std():.3f}, "
                  f"median={np.median(valid_peaks):.3f}")
            print(f"    Per-seed range: [{valid_peaks.min():.3f}, {valid_peaks.max():.3f}]")
            print(f"    Per-seed peak ratios: mean={np.nanmean(seed_peak_ratios):.3f}")
        print(f"    Macro transitions per seed: {n_trans:,}")

    # --- Finite-size scaling checks ---
    print(f"\n--- FINITE-SIZE SCALING CHECKS ---")
    L_arr = np.array(L_values)
    peak_arr = np.array([peak_temps_by_L[L] for L in L_values])
    ratio_arr = np.array([peak_ratios_by_L[L] for L in L_values])

    print(f"\n  Peak T by L: {dict(zip(L_values, [f'{p:.3f}' for p in peak_arr]))}")
    print(f"  Peak ratio by L: {dict(zip(L_values, [f'{r:.3f}' for r in ratio_arr]))}")

    # Check 1: Does peak T stay constant?
    peak_spread = np.nanmax(peak_arr) - np.nanmin(peak_arr)
    print(f"\n  CHECK 1: Peak T spread across L values = {peak_spread:.3f}")
    if peak_spread <= 0.05:
        print(f"    RESULT: Peak T is CONSTANT (spread <= 0.05) -> Supports H6")
    elif peak_spread <= 0.10:
        print(f"    RESULT: Peak T is APPROXIMATELY constant (spread <= 0.10)")
    else:
        print(f"    RESULT: Peak T SHIFTS with L (spread > 0.10)")

    # Check 2: Does peak shift toward T_c?
    if len(L_arr) >= 3:
        from scipy import stats
        valid_mask = np.isfinite(peak_arr)
        if valid_mask.sum() >= 3:
            slope, intercept, r, p, se = stats.linregress(L_arr[valid_mask], peak_arr[valid_mask])
            print(f"\n  CHECK 2: Linear regression of peak T vs L:")
            print(f"    Slope = {slope:.6f} per lattice unit (p={p:.4f})")
            print(f"    Intercept = {intercept:.3f}")
            if p < 0.05 and slope > 0:
                print(f"    RESULT: Peak T INCREASES with L -> RG convergence toward T_c")
            elif p < 0.05 and slope < 0:
                print(f"    RESULT: Peak T DECREASES with L -> Possible artifact")
            else:
                print(f"    RESULT: No significant trend (p={p:.4f} >= 0.05)")

    # Check 3: Does peak ratio change with L?
    print(f"\n  CHECK 3: Peak EI ratio vs L:")
    for L in L_values:
        print(f"    L={L:2d}: ratio = {peak_ratios_by_L[L]:.3f}")
    ratio_spread = np.nanmax(ratio_arr) - np.nanmin(ratio_arr)
    print(f"    Ratio spread: {ratio_spread:.3f}")

    # Check 4: Is peak above 1.0 for all L?
    print(f"\n  CHECK 4: Is peak ratio > 1.0 for all L?")
    all_above_one = True
    for L in L_values:
        above = peak_ratios_by_L[L] > 1.0
        if not above:
            all_above_one = False
        print(f"    L={L:2d}: ratio={peak_ratios_by_L[L]:.3f} {'> 1.0' if above else '<= 1.0'}")
    if all_above_one:
        print(f"    RESULT: YES, emergence signal present at ALL system sizes")
    else:
        print(f"    RESULT: NO, emergence signal ABSENT at some system sizes")

    # ====================================================================
    # PLOTS
    # ====================================================================
    print("\n\nGenerating plots...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    # --- Plot 1: EI ratio vs T for all L values ---
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = {'16': 'tab:green', '24': 'tab:blue', '32': 'tab:orange', '48': 'tab:red'}
    markers = {'16': 'v', '24': 'o', '32': 's', '48': 'D'}

    for L in L_values:
        res = all_results[L]
        ratio_mean = np.nanmean(res['ratio'], axis=0)
        ratio_se = np.nanstd(res['ratio'], axis=0) / np.sqrt(n_seeds)
        finite = np.isfinite(ratio_mean)

        c = colors[str(L)]
        m = markers[str(L)]

        ax.errorbar(temperatures[finite], ratio_mean[finite], yerr=ratio_se[finite],
                    fmt=f'{m}-', color=c, markersize=5, capsize=2, linewidth=1.5,
                    label=f'L={L}')

        # Mark peak
        mask_t = temperatures < T_c + 0.1
        v = ratio_mean[mask_t]
        if np.any(np.isfinite(v)):
            pidx = np.nanargmax(v)
            ax.plot(temperatures[mask_t][pidx], v[pidx], '*', color=c,
                    markersize=15, markeredgecolor='black', markeredgewidth=0.5, zorder=5)

    ax.axvline(T_c, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=f'$T_c$ = {T_c:.3f}')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5, label='EI ratio = 1')
    ax.set_xlabel('Temperature', fontsize=13)
    ax.set_ylabel('EI(M) / EI(S)', fontsize=13)
    ax.set_title('Finite-Size Scaling of EI Emergence Signal\n'
                 f'(b={block_size}, patch={patch_size}x{patch_size}, '
                 f'{n_seeds} seeds, min_obs={min_obs}, equalized transitions)',
                 fontsize=13)
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(temperatures[0] - 0.02, temperatures[-1] + 0.02)

    plt.tight_layout()
    fpath_main = os.path.join(plot_dir, 'v4_finite_size.png')
    plt.savefig(fpath_main, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {fpath_main}")

    # --- Plot 2: Peak T vs L ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel A: Peak T vs L
    ax = axes[0]
    L_plot = np.array(L_values)
    peak_T_plot = np.array([peak_temps_by_L[L] for L in L_values])

    # Per-seed spread as error bars
    peak_se = []
    for L in L_values:
        sp = per_seed_peaks_by_L[L]
        valid = sp[np.isfinite(sp)]
        if len(valid) > 1:
            peak_se.append(valid.std() / np.sqrt(len(valid)))
        else:
            peak_se.append(0.0)
    peak_se = np.array(peak_se)

    ax.errorbar(L_plot, peak_T_plot, yerr=peak_se, fmt='ko-', markersize=8,
                capsize=5, linewidth=2, markerfacecolor='tab:blue')
    ax.axhline(T_c, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=f'$T_c$ = {T_c:.3f}')
    ax.set_xlabel('System Size L', fontsize=13)
    ax.set_ylabel('Peak Temperature', fontsize=13)
    ax.set_title('Peak T of EI Ratio vs System Size', fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(L_values)

    # Panel B: Peak ratio vs L
    ax = axes[1]
    peak_ratio_plot = np.array([peak_ratios_by_L[L] for L in L_values])

    # Per-seed spread for ratio
    ratio_se_peak = []
    for L in L_values:
        res = all_results[L]
        mask_t = temperatures < T_c + 0.1
        ratio_curves = res['ratio'][:, mask_t]
        peak_ratios_seeds = []
        for s in range(n_seeds):
            v = ratio_curves[s]
            if np.any(np.isfinite(v)):
                peak_ratios_seeds.append(np.nanmax(v))
            else:
                peak_ratios_seeds.append(np.nan)
        peak_ratios_seeds = np.array(peak_ratios_seeds)
        valid_r = peak_ratios_seeds[np.isfinite(peak_ratios_seeds)]
        if len(valid_r) > 1:
            ratio_se_peak.append(valid_r.std() / np.sqrt(len(valid_r)))
        else:
            ratio_se_peak.append(0.0)
    ratio_se_peak = np.array(ratio_se_peak)

    ax.errorbar(L_plot, peak_ratio_plot, yerr=ratio_se_peak, fmt='ko-', markersize=8,
                capsize=5, linewidth=2, markerfacecolor='tab:orange')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5, label='EI ratio = 1')
    ax.set_xlabel('System Size L', fontsize=13)
    ax.set_ylabel('Peak EI(M)/EI(S)', fontsize=13)
    ax.set_title('Peak EI Ratio vs System Size', fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(L_values)

    plt.tight_layout()
    fpath_peak = os.path.join(plot_dir, 'v4_peak_vs_L.png')
    plt.savefig(fpath_peak, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {fpath_peak}")

    # --- Plot 3: Per-seed peak distributions ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for i, L in enumerate(L_values):
        ax = axes[i // 2][i % 2]
        sp = per_seed_peaks_by_L[L]
        valid = sp[np.isfinite(sp)]

        if len(valid) > 0:
            bins = np.arange(1.775, 2.575, 0.05)
            ax.hist(valid, bins=bins, color=colors[str(L)], edgecolor='white', alpha=0.8)
            ax.axvline(T_c, color='red', linestyle='--', linewidth=2,
                       label=f'$T_c$ = {T_c:.3f}')
            ax.axvline(valid.mean(), color='black', linestyle='-', linewidth=2,
                       label=f'Mean = {valid.mean():.3f}')
            ax.set_title(f'L={L}: Per-Seed Peak Distribution (n={len(valid)})')
        else:
            ax.text(0.5, 0.5, 'No valid peaks', transform=ax.transAxes,
                    ha='center', va='center')
            ax.set_title(f'L={L}')

        ax.set_xlabel('Peak Temperature')
        ax.set_ylabel('Count')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.suptitle('Per-Seed Peak Temperature Distributions by System Size', fontsize=14)
    plt.tight_layout()
    fpath_dist = os.path.join(plot_dir, 'v4_peak_distributions.png')
    plt.savefig(fpath_dist, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {fpath_dist}")

    # --- Plot 4: Raw EI values for each L ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for i, L in enumerate(L_values):
        ax = axes[i // 2][i % 2]
        res = all_results[L]

        ei_micro_mean = res['ei_micro'].mean(axis=0)
        ei_macro_mean = res['ei_macro'].mean(axis=0)
        ei_micro_se = res['ei_micro'].std(axis=0) / np.sqrt(n_seeds)
        ei_macro_se = res['ei_macro'].std(axis=0) / np.sqrt(n_seeds)

        ax.errorbar(temperatures, ei_micro_mean, yerr=ei_micro_se, fmt='ko-',
                    markersize=3, capsize=2, linewidth=1.5, label='EI(S) micro [equalized]')
        ax.errorbar(temperatures, ei_macro_mean, yerr=ei_macro_se, fmt='o-',
                    color=colors[str(L)], markersize=3, capsize=2, linewidth=1.5,
                    label='EI(M) macro')
        ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
        ax.set_xlabel('Temperature')
        ax.set_ylabel('EI (bits)')
        n_macro_patches = (L // block_size // patch_size) ** 2
        ax.set_title(f'L={L} (macro patches={n_macro_patches})')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.suptitle('Raw EI Values by System Size (equalized transitions)', fontsize=14)
    plt.tight_layout()
    fpath_raw = os.path.join(plot_dir, 'v4_raw_ei_by_L.png')
    plt.savefig(fpath_raw, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {fpath_raw}")

    # ====================================================================
    # SAVE DATA
    # ====================================================================
    data_dir = os.path.join(project_root, 'results', 'phase1', 'data')
    os.makedirs(data_dir, exist_ok=True)

    save_dict = {
        'temperatures': temperatures, 'T_c': T_c,
        'L_values': np.array(L_values),
        'n_seeds': n_seeds, 'block_size': block_size, 'patch_size': patch_size,
        'min_obs': min_obs,
        'n_equilib': n_equilib, 'n_steps': n_steps,
    }
    for L in L_values:
        for key, arr in all_results[L].items():
            save_dict[f'L{L}_{key}'] = arr
        save_dict[f'L{L}_peak_T'] = peak_temps_by_L[L]
        save_dict[f'L{L}_peak_ratio'] = peak_ratios_by_L[L]
        save_dict[f'L{L}_per_seed_peaks'] = per_seed_peaks_by_L[L]

    data_path = os.path.join(data_dir, 'phase1_v4_finite_size.npz')
    np.savez(data_path, **save_dict)
    print(f"\nData saved to {data_path}")

    # ====================================================================
    # SUMMARY
    # ====================================================================
    print("\n" + "=" * 70)
    print("PHASE 1 v4 SUMMARY: FINITE-SIZE SCALING")
    print("=" * 70)

    print(f"\n  {'L':>4s} | {'Peak T':>8s} | {'Peak Ratio':>11s} | {'Macro Trans':>12s} | {'Status':>20s}")
    print(f"  {'----':>4s} | {'--------':>8s} | {'-----------':>11s} | {'------------':>12s} | {'--------------------':>20s}")
    for L in L_values:
        n_macro_patches = (L // block_size // patch_size) ** 2
        n_trans = n_macro_patches * (n_steps - 1)
        status = "OK"
        if L == 16:
            status = "CAVEAT: few trans"
        print(f"  {L:4d} | {peak_temps_by_L[L]:8.3f} | {peak_ratios_by_L[L]:11.3f} | "
              f"{n_trans:12,} | {status:>20s}")

    print(f"\n  Peak T spread: {peak_spread:.3f}")
    if peak_spread <= 0.05:
        print(f"  CONCLUSION: Peak is SIZE-INDEPENDENT -> NOT a finite-size artifact")
        print(f"  This SUPPORTS H6 (causal emergence as early warning)")
    elif peak_spread <= 0.10:
        print(f"  CONCLUSION: Peak is APPROXIMATELY size-independent")
        print(f"  Mild finite-size effects (likely from L=16)")
    else:
        print(f"  CONCLUSION: Peak SHIFTS with L -> finite-size effects present")

    # Check if large-L peaks converge
    if len(L_values) >= 2:
        large_L_peaks = [peak_temps_by_L[L] for L in L_values if L >= 24]
        if len(large_L_peaks) >= 2:
            spread_large = max(large_L_peaks) - min(large_L_peaks)
            print(f"\n  For L >= 24: peak T spread = {spread_large:.3f}")
            if spread_large <= 0.05:
                print(f"  Large-L peaks are CONVERGED")

    print(f"\n  Total runtime: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"\n{'='*70}")
    print("PHASE 1 v4 COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_phase1_v4()
