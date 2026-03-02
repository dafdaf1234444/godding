"""
Phase 1 v3: Ising Model Experiment — Addressing Challenger Findings

Fixes applied from challenger analysis of v2:
1. EQUALIZED TRANSITION COUNTS: Subsample micro transitions to match macro count.
   v2 had 288K micro vs 18K macro transitions — a 16x confound.
2. MORE SEEDS: 20 seeds per temperature (up from 5) for reliable error estimation.
3. PAIRED RATIO: Compute EI(M)/EI(S) per-seed, then average — not ratio of means.
4. PER-SEED PEAK TRACKING: Record where each seed's EI ratio peaks for bootstrap CI.
5. min_obs SENSITIVITY: Test {0, 1, 5, 10, 20} to check robustness.
6. EFFECTIVE SAMPLE SIZE: Report number of rows passing min_obs filter at each T.
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


def run_phase1_v3():
    """Execute Phase 1 v3 — addressing challenger findings."""
    print("=" * 70)
    print("PHASE 1 v3: ISING MODEL (TRANSITION-COUNT EQUALIZED)")
    print("=" * 70)

    # Parameters
    L = 24
    temperatures = np.arange(1.5, 3.01, 0.05)
    n_equilib = 5000
    n_steps = 2000
    block_size = 4  # Coarse-graining block
    patch_size = 2  # 2x2 patches → 16 states (equal for both scales)
    n_seeds = 20
    T_c = 2.269
    min_obs_values = [0, 1, 5, 10, 20]

    n_temps = len(temperatures)
    print(f"\nParameters:")
    print(f"  L={L}, n_equilib={n_equilib}, n_steps={n_steps}")
    print(f"  Seeds: {n_seeds}, block_size={block_size}, patch_size={patch_size}")
    print(f"  State space: 2^(2x2) = 16 states (equal for micro and macro)")
    print(f"  min_obs sensitivity: {min_obs_values}")
    print(f"  KEY FIX: Micro transitions subsampled to match macro count")

    # Storage: per-seed, per-temperature results
    # We store per-seed EI values for all min_obs thresholds
    results_by_minobs = {}
    for mo in min_obs_values:
        results_by_minobs[mo] = {
            'ei_micro': np.zeros((n_seeds, n_temps)),
            'ei_macro': np.zeros((n_seeds, n_temps)),
            'ratio': np.zeros((n_seeds, n_temps)),
            'n_rows_micro': np.zeros((n_seeds, n_temps), dtype=int),
            'n_rows_macro': np.zeros((n_seeds, n_temps), dtype=int),
        }

    # Standard EWS per seed
    mag_var_runs = np.zeros((n_seeds, n_temps))
    mag_ac_runs = np.zeros((n_seeds, n_temps))
    n_transitions_used = np.zeros((n_seeds, n_temps), dtype=int)

    # Also compute un-equalized (full micro) for comparison
    ei_micro_full_runs = np.zeros((n_seeds, n_temps))

    total_start = time.time()

    for idx, T in enumerate(temperatures):
        t0 = time.time()
        print(f"\n--- T = {T:.3f} ({idx+1}/{n_temps}) ---", flush=True)

        for s in range(n_seeds):
            seed = 1000 * s + idx
            rng = np.random.RandomState(seed + 99999)

            configs, mags = simulate_ising(L, T, n_steps, n_equilib, seed=seed)

            # Standard EWS
            mag_var_runs[s, idx] = mags.var()
            x, y = mags[:-1], mags[1:]
            mx, my, sx, sy = x.mean(), y.mean(), x.std(), y.std()
            mag_ac_runs[s, idx] = np.mean((x-mx)*(y-my))/(sx*sy) if sx > 0 and sy > 0 else 0.0

            # Coarse-grain
            coarse = coarsegrain_timeseries(configs, block_size)

            # Compute EI at all min_obs thresholds
            for mo in min_obs_values:
                ei_s, ei_m, n_trans, nr_s, nr_m = compute_ei_equalized(
                    configs, coarse, patch_size, mo, rng
                )
                results_by_minobs[mo]['ei_micro'][s, idx] = ei_s
                results_by_minobs[mo]['ei_macro'][s, idx] = ei_m
                results_by_minobs[mo]['ratio'][s, idx] = ei_m / ei_s if ei_s > 1e-10 else np.nan
                results_by_minobs[mo]['n_rows_micro'][s, idx] = nr_s
                results_by_minobs[mo]['n_rows_macro'][s, idx] = nr_m
                n_transitions_used[s, idx] = n_trans

            # Full micro (un-equalized) for comparison
            micro_states, n_states, _ = config_to_patch_states(configs, patch_size)
            all_t = micro_states[:-1].ravel()
            all_t1 = micro_states[1:].ravel()
            T_mat, rc = estimate_transition_matrix(all_t, all_t1, n_states)
            ei_micro_full_runs[s, idx] = effective_information(T_mat, rc, min_observations=5)

        elapsed = time.time() - t0
        # Summary for min_obs=5 (primary)
        mo5 = results_by_minobs[5]
        mean_ratio = np.nanmean(mo5['ratio'][:, idx])
        mean_micro = mo5['ei_micro'][:, idx].mean()
        mean_macro = mo5['ei_macro'][:, idx].mean()
        mean_rows_s = mo5['n_rows_micro'][:, idx].mean()
        mean_rows_m = mo5['n_rows_macro'][:, idx].mean()
        print(f"  EI(S)={mean_micro:.4f}, EI(M)={mean_macro:.4f}, "
              f"Ratio(paired)={mean_ratio:.3f}")
        print(f"  Rows: micro={mean_rows_s:.1f}/16, macro={mean_rows_m:.1f}/16, "
              f"trans={n_transitions_used[0,idx]}")
        print(f"  Time: {elapsed:.1f}s ({n_seeds} seeds)")

    total_elapsed = time.time() - total_start
    print(f"\nTotal time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # ====================================================================
    # ANALYSIS
    # ====================================================================
    print("\n" + "=" * 70)
    print("PHASE 1 v3 ANALYSIS")
    print("=" * 70)

    project_root = os.path.join(os.path.dirname(__file__), '..')

    # --- Per-seed peak location analysis (primary: min_obs=5) ---
    mo5 = results_by_minobs[5]
    per_seed_peaks = []
    for s in range(n_seeds):
        ratio_curve = mo5['ratio'][s, :]
        # Only consider T < T_c + 0.1 to find peaks in the relevant region
        mask = temperatures < T_c + 0.1
        valid = ratio_curve[mask]
        if np.any(np.isfinite(valid)):
            peak_idx = np.nanargmax(valid)
            per_seed_peaks.append(temperatures[mask][peak_idx])
        else:
            per_seed_peaks.append(np.nan)
    per_seed_peaks = np.array(per_seed_peaks)
    valid_peaks = per_seed_peaks[np.isfinite(per_seed_peaks)]

    print(f"\n--- Per-seed peak locations (min_obs=5, T < T_c+0.1) ---")
    print(f"  N valid seeds: {len(valid_peaks)}/{n_seeds}")
    if len(valid_peaks) > 0:
        print(f"  Mean peak T: {valid_peaks.mean():.3f} ± {valid_peaks.std():.3f}")
        print(f"  Median peak T: {np.median(valid_peaks):.3f}")
        print(f"  Range: [{valid_peaks.min():.3f}, {valid_peaks.max():.3f}]")
        print(f"  T_c = {T_c:.3f}")
        print(f"  Lead time (T_c - mean peak): {T_c - valid_peaks.mean():.3f}")

        # Bootstrap CI on mean peak location
        n_bootstrap = 10000
        boot_means = np.empty(n_bootstrap)
        boot_rng = np.random.RandomState(42)
        for i in range(n_bootstrap):
            sample = boot_rng.choice(valid_peaks, size=len(valid_peaks), replace=True)
            boot_means[i] = sample.mean()
        ci_lo = np.percentile(boot_means, 2.5)
        ci_hi = np.percentile(boot_means, 97.5)
        print(f"  Bootstrap 95% CI on mean peak: [{ci_lo:.3f}, {ci_hi:.3f}]")
        peak_before_Tc = ci_hi < T_c
        print(f"  Is CI entirely below T_c? {'YES' if peak_before_Tc else 'NO'}")

    # --- min_obs sensitivity analysis ---
    print(f"\n--- min_obs sensitivity analysis ---")
    from src.analysis import kendall_tau
    mag_vars_mean = mag_var_runs.mean(axis=0)
    mag_acs_mean = mag_ac_runs.mean(axis=0)

    for mo in min_obs_values:
        data = results_by_minobs[mo]
        # Paired ratio: average of per-seed ratios
        paired_ratio = np.nanmean(data['ratio'], axis=0)
        paired_ratio_se = np.nanstd(data['ratio'], axis=0) / np.sqrt(n_seeds)

        # Kendall tau
        finite_mask = np.isfinite(paired_ratio)
        if finite_mask.sum() > 5:
            tau_ac, p_ac = kendall_tau(paired_ratio[finite_mask], mag_acs_mean[finite_mask])
            tau_var, p_var = kendall_tau(paired_ratio[finite_mask], mag_vars_mean[finite_mask])
        else:
            tau_ac, p_ac, tau_var, p_var = 0, 1, 0, 1

        # Emergence count
        emergence = np.sum(paired_ratio > 1.0)

        # Effective rows
        mean_rows_s = data['n_rows_micro'].mean(axis=0).mean()
        mean_rows_m = data['n_rows_macro'].mean(axis=0).mean()

        # Peak location
        mask = temperatures < T_c + 0.1
        valid = paired_ratio[mask]
        if np.any(np.isfinite(valid)):
            peak_T = temperatures[mask][np.nanargmax(valid)]
        else:
            peak_T = np.nan

        print(f"\n  min_obs={mo:2d}: tau(AC)={tau_ac:+.4f} (p={p_ac:.3e}), "
              f"tau(Var)={tau_var:+.4f} (p={p_var:.3e})")
        print(f"    Emergence: {emergence}/{n_temps}, Peak T: {peak_T:.3f}, "
              f"Rows: micro={mean_rows_s:.1f}, macro={mean_rows_m:.1f}")

    # --- v2 vs v3 comparison (full micro vs equalized micro) ---
    print(f"\n--- v3 Equalized vs v2 Un-equalized (min_obs=5) ---")
    mo5 = results_by_minobs[5]
    ei_macro_mean = mo5['ei_macro'].mean(axis=0)
    ei_micro_eq_mean = mo5['ei_micro'].mean(axis=0)
    ei_micro_full_mean = ei_micro_full_runs.mean(axis=0)

    ratio_equalized = np.nanmean(mo5['ratio'], axis=0)
    ratio_uneq = ei_macro_mean / np.where(ei_micro_full_mean > 1e-10, ei_micro_full_mean, 1e-10)

    mask_f = np.isfinite(ratio_equalized)
    tau_eq_ac, p_eq_ac = kendall_tau(ratio_equalized[mask_f], mag_acs_mean[mask_f])
    tau_uneq_ac, p_uneq_ac = kendall_tau(ratio_uneq, mag_acs_mean)

    print(f"  Equalized:   tau(AC)={tau_eq_ac:+.4f} (p={p_eq_ac:.3e}), "
          f"mean micro EI={ei_micro_eq_mean.mean():.4f}")
    print(f"  Un-equalized: tau(AC)={tau_uneq_ac:+.4f} (p={p_uneq_ac:.3e}), "
          f"mean micro EI={ei_micro_full_mean.mean():.4f}")

    # ====================================================================
    # PLOTS
    # ====================================================================
    print("\n\nGenerating plots...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    # --- Plot 1: Money plot with equalized transitions ---
    mo5 = results_by_minobs[5]
    paired_ratio = np.nanmean(mo5['ratio'], axis=0)
    paired_ratio_se = np.nanstd(mo5['ratio'], axis=0) / np.sqrt(n_seeds)
    mag_vars_se = mag_var_runs.std(axis=0) / np.sqrt(n_seeds)
    mag_acs_se = mag_ac_runs.std(axis=0) / np.sqrt(n_seeds)

    from src.visualize import plot_money
    plot_money(temperatures, paired_ratio, mag_vars_mean, mag_acs_mean, T_c,
               os.path.join(plot_dir, 'v3_money_equalized.png'),
               system_name='2D Ising (Equalized Transitions, 16 vs 16)',
               ei_err=paired_ratio_se, var_err=mag_vars_se, ac_err=mag_acs_se)

    # --- Plot 2: min_obs sensitivity ---
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.ravel()

    for i, mo in enumerate(min_obs_values):
        ax = axes[i]
        data = results_by_minobs[mo]
        ratio_mean = np.nanmean(data['ratio'], axis=0)
        ratio_se = np.nanstd(data['ratio'], axis=0) / np.sqrt(n_seeds)
        finite = np.isfinite(ratio_mean)

        ax.errorbar(temperatures[finite], ratio_mean[finite], yerr=ratio_se[finite],
                    fmt='o-', markersize=3, capsize=2, color='tab:blue')
        ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
        ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5)

        # Annotate with stats
        if finite.sum() > 5:
            tau, p = kendall_tau(ratio_mean[finite], mag_acs_mean[finite])
            emergence = np.sum(ratio_mean[finite] > 1.0)
            ax.set_title(f'min_obs={mo}\ntau(AC)={tau:.3f}, p={p:.3e}\n'
                        f'emergence={emergence}/{finite.sum()}', fontsize=10)
        else:
            ax.set_title(f'min_obs={mo}\nInsufficient data', fontsize=10)

        ax.set_ylabel('EI(M)/EI(S)' if i % 3 == 0 else '')
        ax.set_xlabel('Temperature' if i >= 3 else '')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # Use last subplot for summary
    ax = axes[5]
    ax.axis('off')
    summary_text = "min_obs sensitivity summary\n(Equalized transitions)\n\n"
    for mo in min_obs_values:
        data = results_by_minobs[mo]
        ratio_mean = np.nanmean(data['ratio'], axis=0)
        finite = np.isfinite(ratio_mean)
        if finite.sum() > 5:
            tau, p = kendall_tau(ratio_mean[finite], mag_acs_mean[finite])
            summary_text += f"min_obs={mo:2d}: tau={tau:+.3f} (p={p:.2e})\n"
    ax.text(0.1, 0.5, summary_text, fontsize=12, family='monospace',
            verticalalignment='center', transform=ax.transAxes)

    plt.suptitle('min_obs Sensitivity Analysis — Equalized Transition Counts', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'v3_minobs_sensitivity.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: v3_minobs_sensitivity.png")

    # --- Plot 3: Per-seed peak distribution ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    if len(valid_peaks) > 0:
        ax.hist(valid_peaks, bins=np.arange(1.45, 2.35, 0.05), color='tab:blue',
                edgecolor='white', alpha=0.8)
        ax.axvline(T_c, color='red', linestyle='--', linewidth=2, label=f'$T_c$ = {T_c:.3f}')
        ax.axvline(valid_peaks.mean(), color='blue', linestyle='-', linewidth=2,
                   label=f'Mean peak = {valid_peaks.mean():.3f}')
        ax.axvspan(ci_lo, ci_hi, alpha=0.2, color='blue', label=f'95% CI [{ci_lo:.3f}, {ci_hi:.3f}]')
        ax.set_xlabel('Peak Temperature')
        ax.set_ylabel('Count')
        ax.set_title(f'Distribution of Per-Seed Peak Locations (n={len(valid_peaks)})')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    ax = axes[1]
    # Show individual seed curves
    mo5 = results_by_minobs[5]
    for s in range(min(n_seeds, 10)):  # Show first 10 for clarity
        ratio_s = mo5['ratio'][s, :]
        finite = np.isfinite(ratio_s)
        ax.plot(temperatures[finite], ratio_s[finite], '-', alpha=0.3, linewidth=0.8)
    # Mean with error bars
    paired_ratio = np.nanmean(mo5['ratio'], axis=0)
    paired_ratio_se = np.nanstd(mo5['ratio'], axis=0) / np.sqrt(n_seeds)
    finite = np.isfinite(paired_ratio)
    ax.errorbar(temperatures[finite], paired_ratio[finite], yerr=paired_ratio_se[finite],
                fmt='ko-', markersize=4, capsize=2, linewidth=2, label='Mean ± SE')
    ax.axvline(T_c, color='red', linestyle='--', linewidth=2, alpha=0.7, label=f'$T_c$')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Temperature')
    ax.set_ylabel('EI(M)/EI(S)')
    ax.set_title('Per-Seed EI Ratio Curves (equalized transitions)')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'v3_peak_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: v3_peak_distribution.png")

    # --- Plot 4: Equalized vs un-equalized comparison ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    ax.errorbar(temperatures, ratio_equalized, yerr=paired_ratio_se,
                fmt='o-', markersize=3, capsize=2, color='tab:blue', label='Equalized micro')
    ax.plot(temperatures, ratio_uneq, 's--', markersize=3, color='tab:orange',
            label='Full micro (un-equalized)')
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Temperature')
    ax.set_ylabel('EI(M)/EI(S)')
    ax.set_title('Effect of Transition Count Equalization')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    # Effective dimensionality: rows passing filter
    mo5 = results_by_minobs[5]
    mean_rows_s = mo5['n_rows_micro'].mean(axis=0)
    mean_rows_m = mo5['n_rows_macro'].mean(axis=0)
    ax.plot(temperatures, mean_rows_s, 'o-', markersize=3, color='tab:blue',
            label='Micro rows (min_obs=5)')
    ax.plot(temperatures, mean_rows_m, 's-', markersize=3, color='tab:orange',
            label='Macro rows (min_obs=5)')
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
    ax.axhline(16, color='gray', linestyle=':', alpha=0.5, label='Max (16)')
    ax.set_xlabel('Temperature')
    ax.set_ylabel('Rows with >= 5 observations')
    ax.set_title('Effective Dimensionality of EI Computation')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 17)

    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'v3_equalized_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: v3_equalized_comparison.png")

    # --- Plot 5: Raw EI values (equalized) ---
    fig, ax = plt.subplots(figsize=(10, 6))
    mo5 = results_by_minobs[5]
    ei_micro_eq = mo5['ei_micro'].mean(axis=0)
    ei_micro_eq_se = mo5['ei_micro'].std(axis=0) / np.sqrt(n_seeds)
    ei_macro_eq = mo5['ei_macro'].mean(axis=0)
    ei_macro_eq_se = mo5['ei_macro'].std(axis=0) / np.sqrt(n_seeds)

    ax.errorbar(temperatures, ei_micro_eq, yerr=ei_micro_eq_se, fmt='ko-',
                markersize=3, capsize=2, linewidth=1.5, label='EI(S) micro [equalized, 16 states]')
    ax.errorbar(temperatures, ei_macro_eq, yerr=ei_macro_eq_se, fmt='o-',
                color='tab:blue', markersize=3, capsize=2, linewidth=1.5,
                label='EI(M) macro [16 states]')
    ax.errorbar(temperatures, ei_micro_full_mean,
                yerr=ei_micro_full_runs.std(axis=0)/np.sqrt(n_seeds),
                fmt='s--', color='gray', markersize=3, capsize=2, linewidth=1,
                label='EI(S) micro [full, 16 states]')
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$={T_c:.3f}')
    ax.set_xlabel('Temperature')
    ax.set_ylabel('Effective Information (bits)')
    ax.set_title('Raw EI Values — Equalized vs Full Micro Transitions')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'v3_raw_ei_equalized.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: v3_raw_ei_equalized.png")

    # ====================================================================
    # SAVE DATA
    # ====================================================================
    data_dir = os.path.join(project_root, 'results', 'phase1', 'data')
    os.makedirs(data_dir, exist_ok=True)

    save_dict = {
        'temperatures': temperatures, 'T_c': T_c, 'L': L,
        'n_seeds': n_seeds, 'block_size': block_size, 'patch_size': patch_size,
        'min_obs_values': np.array(min_obs_values),
        'mag_var_runs': mag_var_runs, 'mag_ac_runs': mag_ac_runs,
        'n_transitions_used': n_transitions_used,
        'ei_micro_full_runs': ei_micro_full_runs,
        'per_seed_peaks': per_seed_peaks,
    }
    # Add per-min_obs data
    for mo in min_obs_values:
        for key, arr in results_by_minobs[mo].items():
            save_dict[f'mo{mo}_{key}'] = arr

    np.savez(os.path.join(data_dir, 'phase1_v3_results.npz'), **save_dict)
    print(f"\nData saved to {data_dir}/phase1_v3_results.npz")

    # ====================================================================
    # LOG
    # ====================================================================
    log_path = os.path.join(project_root, 'results', 'phase1', 'log_v3.md')
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M')

    # Gather stats for log
    mo5 = results_by_minobs[5]
    paired_ratio = np.nanmean(mo5['ratio'], axis=0)
    finite_mask = np.isfinite(paired_ratio)
    tau_ac, p_ac = kendall_tau(paired_ratio[finite_mask], mag_acs_mean[finite_mask])
    tau_var, p_var = kendall_tau(paired_ratio[finite_mask], mag_vars_mean[finite_mask])
    emergence = np.sum(paired_ratio > 1.0)

    with open(log_path, 'w') as f:
        f.write(f"""# Phase 1 v3: Transition-Count Equalized Results

## {timestamp} — PHASE 1 v3 EXPERIMENT
**Status**: COMPLETED
**Addressing**: Challenger findings from v2 audit

### Key methodological changes from v2:
1. **Equalized transitions**: Micro subsampled to match macro count (~18K each)
2. **20 seeds** per temperature (up from 5)
3. **Paired ratio**: EI(M)/EI(S) computed per-seed, then averaged
4. **Per-seed peak tracking** with bootstrap 95% CI
5. **min_obs sensitivity**: tested {{0, 1, 5, 10, 20}}

### Parameters
L={L}, n_equilib={n_equilib}, n_steps={n_steps}, seeds={n_seeds}
Block size: {block_size}, Patch size: {patch_size} (16 states each)
Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)

### Key Results (min_obs=5, equalized)
- Kendall tau (EI ratio vs AC): {tau_ac:+.4f} (p={p_ac:.3e})
- Kendall tau (EI ratio vs Var): {tau_var:+.4f} (p={p_var:.3e})
- Emergence count: {emergence}/{n_temps}
""")
        if len(valid_peaks) > 0:
            f.write(f"""
### Per-seed peak analysis
- Mean peak T: {valid_peaks.mean():.3f} ± {valid_peaks.std():.3f}
- Median peak T: {np.median(valid_peaks):.3f}
- Bootstrap 95% CI: [{ci_lo:.3f}, {ci_hi:.3f}]
- T_c = {T_c:.3f}
- CI entirely below T_c? {'YES' if peak_before_Tc else 'NO'}
""")
        f.write(f"""
### min_obs sensitivity
""")
        for mo in min_obs_values:
            data = results_by_minobs[mo]
            ratio_mean = np.nanmean(data['ratio'], axis=0)
            finite = np.isfinite(ratio_mean)
            if finite.sum() > 5:
                tau, p = kendall_tau(ratio_mean[finite], mag_acs_mean[finite])
                em = np.sum(ratio_mean[finite] > 1.0)
                f.write(f"- min_obs={mo:2d}: tau(AC)={tau:+.4f} (p={p:.3e}), "
                       f"emergence={em}/{finite.sum()}\n")

        f.write(f"""
### Plots
- v3_money_equalized.png — Money plot with equalized transitions
- v3_minobs_sensitivity.png — min_obs sensitivity panels
- v3_peak_distribution.png — Per-seed peak histogram + individual curves
- v3_equalized_comparison.png — Equalized vs un-equalized + effective dimensionality
- v3_raw_ei_equalized.png — Raw EI values for equalized computation
""")
    print(f"\nLog written to {log_path}")
    print(f"\n{'='*70}")
    print("PHASE 1 v3 COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_phase1_v3()
