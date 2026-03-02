"""
Phase 1 v2: Ising Model Experiment — Corrected

Fixes applied from Round 1 audit:
1. Scaled Laplace smoothing (alpha=1/n_states) instead of alpha=1
2. Observed-only EI: skip rows with < 5 real transitions
3. Equal state-space comparison: 2x2 micro patches (16 states) alongside 3x3
4. Multi-seed runs (5 seeds per temperature) with error bars
5. Temporal shuffle control to verify signal is from dynamics, not static structure
6. L=24 (divisible by 2, 3, 4, 8) — no silent data loss from patch extraction
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
from src.ews_standard import compute_ews
from src.analysis import kendall_tau, detect_threshold_crossing, compute_lead_time
from src.visualize import (plot_ews_comparison, plot_ei_across_scales,
                           plot_money, plot_raw_ei)
from src.coarse_grain import config_to_patch_states


def compute_patch_ei(configs, patch_size, min_obs=5):
    """Compute EI from local patches using observed-only averaging."""
    states, n_states = config_to_patch_states(configs, patch_size)
    states_t = states[:-1].ravel()
    states_t1 = states[1:].ravel()
    T, row_counts = estimate_transition_matrix(states_t, states_t1, n_states)
    ei = effective_information(T, row_counts, min_observations=min_obs)
    return ei


def compute_patch_ei_shuffled(configs, patch_size, min_obs=5, seed=0):
    """Compute EI on temporally shuffled data (null control)."""
    rng = np.random.RandomState(seed)
    states, n_states = config_to_patch_states(configs, patch_size)
    N, n_patches = states.shape
    # Shuffle time ordering independently for each patch location
    for p in range(n_patches):
        rng.shuffle(states[:, p])
    states_t = states[:-1].ravel()
    states_t1 = states[1:].ravel()
    T, row_counts = estimate_transition_matrix(states_t, states_t1, n_states)
    ei = effective_information(T, row_counts, min_observations=min_obs)
    return ei


def run_phase1_v2():
    """Execute corrected Phase 1 Ising experiment."""
    print("=" * 70)
    print("PHASE 1 v2: ISING MODEL EXPERIMENT (CORRECTED)")
    print("=" * 70)

    # Parameters — L=24 divisible by 2, 3, 4, 8
    L = 24
    temperatures = np.arange(1.5, 3.01, 0.05)
    n_equilib = 5000
    n_steps = 2000
    block_sizes = [2, 4, 8]
    micro_patch_3 = 3   # 512 states (original)
    micro_patch_2 = 2   # 16 states (equal state-space control)
    macro_patch = 2      # 16 states on coarse grids
    n_seeds = 5
    T_c = 2.269
    min_obs = 5

    n_temps = len(temperatures)
    print(f"\nParameters:")
    print(f"  L = {L} (divisible by 2,3,4,8), n_equilib = {n_equilib}, n_steps = {n_steps}")
    print(f"  Seeds per T: {n_seeds}, min_obs = {min_obs}")
    print(f"  Micro patches: 3x3 (512 states) AND 2x2 (16 states)")
    print(f"  Macro patch: 2x2 (16 states) on coarse grids")
    print(f"  Scaled Laplace smoothing: alpha = 1/n_states")
    print(f"  Observed-only EI: rows with >= {min_obs} observations")
    print(f"  Shuffle control: temporal permutation null test")

    # Storage — means and stds across seeds
    def make_arr():
        return np.zeros((n_seeds, n_temps))

    ei_micro_3_runs = make_arr()       # 3x3 micro
    ei_micro_2_runs = make_arr()       # 2x2 micro (equal state space)
    ei_macro_runs = {b: make_arr() for b in block_sizes}
    ei_shuf_3_runs = make_arr()        # shuffled 3x3 micro
    ei_shuf_macro_runs = make_arr()    # shuffled macro b=4
    mag_mean_runs = make_arr()
    mag_var_runs = make_arr()
    mag_ac_runs = make_arr()

    total_start = time.time()

    for idx, T in enumerate(temperatures):
        print(f"\n--- T = {T:.3f} ({idx+1}/{n_temps}) ---")
        t0 = time.time()

        for s in range(n_seeds):
            seed = 1000 * s + idx
            configs, mags = simulate_ising(L, T, n_steps, n_equilib, seed=seed)

            mag_mean_runs[s, idx] = mags.mean()
            mag_var_runs[s, idx] = mags.var()

            # Lag-1 AC
            x, y = mags[:-1], mags[1:]
            mx, my, sx, sy = x.mean(), y.mean(), x.std(), y.std()
            mag_ac_runs[s, idx] = np.mean((x-mx)*(y-my))/(sx*sy) if sx > 0 and sy > 0 else 0.0

            # Micro EI — 3x3 (512 states)
            ei_micro_3_runs[s, idx] = compute_patch_ei(configs, micro_patch_3, min_obs)

            # Micro EI — 2x2 (16 states, equal state space control)
            ei_micro_2_runs[s, idx] = compute_patch_ei(configs, micro_patch_2, min_obs)

            # Macro EI at each block size
            for b in block_sizes:
                coarse = coarsegrain_timeseries(configs, b)
                ei_macro_runs[b][s, idx] = compute_patch_ei(coarse, macro_patch, min_obs)

            # Shuffle controls (one per seed)
            ei_shuf_3_runs[s, idx] = compute_patch_ei_shuffled(configs, micro_patch_3, min_obs, seed=seed)
            coarse_4 = coarsegrain_timeseries(configs, 4)
            ei_shuf_macro_runs[s, idx] = compute_patch_ei_shuffled(coarse_4, macro_patch, min_obs, seed=seed)

        elapsed = time.time() - t0
        # Print summary for this T
        print(f"  |M| = {mag_mean_runs[:, idx].mean():.4f} ± {mag_mean_runs[:, idx].std():.4f}")
        ei3_mean = ei_micro_3_runs[:, idx].mean()
        ei2_mean = ei_micro_2_runs[:, idx].mean()
        em4_mean = ei_macro_runs[4][:, idx].mean()
        print(f"  EI(S,3x3) = {ei3_mean:.4f}, EI(S,2x2) = {ei2_mean:.4f}, EI(M,b=4) = {em4_mean:.4f}")
        print(f"  Ratio(3x3) = {em4_mean/ei3_mean:.3f}, Ratio(2x2) = {em4_mean/ei2_mean:.3f}")
        print(f"  Shuffle: EI(S,3x3) = {ei_shuf_3_runs[:, idx].mean():.4f}, EI(M,b=4) = {ei_shuf_macro_runs[:, idx].mean():.4f}")
        print(f"  Time: {elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    print(f"\nTotal simulation time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Compute means and standard errors
    def mean_se(arr):
        return arr.mean(axis=0), arr.std(axis=0) / np.sqrt(n_seeds)

    ei_micro_3, ei_micro_3_se = mean_se(ei_micro_3_runs)
    ei_micro_2, ei_micro_2_se = mean_se(ei_micro_2_runs)
    ei_macro = {b: mean_se(ei_macro_runs[b]) for b in block_sizes}
    ei_shuf_3, _ = mean_se(ei_shuf_3_runs)
    ei_shuf_m4, _ = mean_se(ei_shuf_macro_runs)
    mag_means, _ = mean_se(mag_mean_runs)
    mag_vars, mag_vars_se = mean_se(mag_var_runs)
    mag_acs, mag_acs_se = mean_se(mag_ac_runs)

    # Key ratios
    # 1. Original: EI(M,b=4,16 states) / EI(S,3x3,512 states) — confounded
    ratio_confounded = ei_macro[4][0] / np.where(ei_micro_3 > 1e-6, ei_micro_3, 1e-6)
    ratio_confounded_se = ratio_confounded * np.sqrt(
        (ei_macro[4][1] / np.where(ei_macro[4][0] > 1e-6, ei_macro[4][0], 1e-6))**2 +
        (ei_micro_3_se / np.where(ei_micro_3 > 1e-6, ei_micro_3, 1e-6))**2
    )

    # 2. Equal state-space: EI(M,b=4,16 states) / EI(S,2x2,16 states)
    ratio_equal = ei_macro[4][0] / np.where(ei_micro_2 > 1e-6, ei_micro_2, 1e-6)
    ratio_equal_se = ratio_equal * np.sqrt(
        (ei_macro[4][1] / np.where(ei_macro[4][0] > 1e-6, ei_macro[4][0], 1e-6))**2 +
        (ei_micro_2_se / np.where(ei_micro_2 > 1e-6, ei_micro_2, 1e-6))**2
    )

    # 3. Shuffle control ratio
    ratio_shuffle = ei_shuf_m4 / np.where(ei_shuf_3 > 1e-6, ei_shuf_3, 1e-6)

    # Save data
    project_root = os.path.join(os.path.dirname(__file__), '..')
    data_dir = os.path.join(project_root, 'results', 'phase1', 'data')
    np.savez(os.path.join(data_dir, 'phase1_v2_results.npz'),
             temperatures=temperatures, T_c=T_c, L=L, n_seeds=n_seeds,
             ei_micro_3=ei_micro_3, ei_micro_3_se=ei_micro_3_se,
             ei_micro_2=ei_micro_2, ei_micro_2_se=ei_micro_2_se,
             ei_macro_b2=ei_macro[2][0], ei_macro_b2_se=ei_macro[2][1],
             ei_macro_b4=ei_macro[4][0], ei_macro_b4_se=ei_macro[4][1],
             ei_macro_b8=ei_macro[8][0], ei_macro_b8_se=ei_macro[8][1],
             ei_shuf_3=ei_shuf_3, ei_shuf_m4=ei_shuf_m4,
             ratio_confounded=ratio_confounded, ratio_confounded_se=ratio_confounded_se,
             ratio_equal=ratio_equal, ratio_equal_se=ratio_equal_se,
             ratio_shuffle=ratio_shuffle,
             mag_means=mag_means, mag_vars=mag_vars, mag_vars_se=mag_vars_se,
             mag_acs=mag_acs, mag_acs_se=mag_acs_se)
    print(f"\nData saved to {data_dir}/phase1_v2_results.npz")

    # ---- Analysis ----
    print("\n" + "=" * 70)
    print("PHASE 1 v2 ANALYSIS")
    print("=" * 70)

    # Kendall tau for both ratio types
    tau_conf_ac, p_conf_ac = kendall_tau(ratio_confounded, mag_acs)
    tau_equal_ac, p_equal_ac = kendall_tau(ratio_equal, mag_acs)
    tau_var_ac, p_var_ac = kendall_tau(mag_vars, mag_acs)

    print(f"\nKendall tau correlations:")
    print(f"  Confounded ratio vs AC: tau = {tau_conf_ac:.4f} (p = {p_conf_ac:.4e})")
    print(f"  Equal-space ratio vs AC: tau = {tau_equal_ac:.4f} (p = {p_equal_ac:.4e})")
    print(f"  Variance vs AC:         tau = {tau_var_ac:.4f} (p = {p_var_ac:.4e})")

    # Does equal-space ratio show EI(M) > EI(S)?
    emergence_equal = np.sum(ratio_equal > 1.0)
    print(f"\nEqual state-space emergence (EI(M,16) > EI(S,16)): {emergence_equal}/{n_temps} temps")

    # Shuffle control comparison
    print(f"\nShuffle control:")
    print(f"  Real ratio (b=4/3x3) at T_c: {ratio_confounded[np.argmin(np.abs(temperatures-T_c))]:.3f}")
    print(f"  Shuffled ratio at T_c:        {ratio_shuffle[np.argmin(np.abs(temperatures-T_c))]:.3f}")
    print(f"  Real ratio mean:    {ratio_confounded.mean():.3f}")
    print(f"  Shuffled ratio mean: {ratio_shuffle.mean():.3f}")

    # ---- Plots ----
    print("\nGenerating plots...")
    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')

    # Money plot with error bars — EQUAL state-space ratio
    plot_money(temperatures, ratio_equal, mag_vars, mag_acs, T_c,
               os.path.join(plot_dir, 'v2_money_equal_states.png'),
               system_name='2D Ising (Equal State Space, 16 vs 16)',
               ei_err=ratio_equal_se, var_err=mag_vars_se, ac_err=mag_acs_se)

    # Money plot with error bars — confounded ratio for comparison
    plot_money(temperatures, ratio_confounded, mag_vars, mag_acs, T_c,
               os.path.join(plot_dir, 'v2_money_confounded.png'),
               system_name='2D Ising (512 vs 16 States)',
               ei_err=ratio_confounded_se, var_err=mag_vars_se, ac_err=mag_acs_se)

    # Shuffle control plot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(temperatures, ratio_confounded, 'o-', color='tab:blue', markersize=4,
            linewidth=1.5, label='Real EI(M)/EI(S)')
    ax.fill_between(temperatures, ratio_confounded - ratio_confounded_se,
                     ratio_confounded + ratio_confounded_se, color='tab:blue', alpha=0.15)
    ax.plot(temperatures, ratio_shuffle, 's--', color='tab:red', markersize=4,
            linewidth=1.5, label='Shuffled (null)')
    ax.axvline(T_c, color='red', linestyle='--', linewidth=2, alpha=0.5,
               label=f'$T_c$ = {T_c:.3f}')
    ax.set_xlabel('Temperature', fontsize=12)
    ax.set_ylabel('EI(M) / EI(S)', fontsize=12)
    ax.set_title('Temporal Shuffle Control — 2D Ising Model', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'v2_shuffle_control.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot_dir}/v2_shuffle_control.png")

    # Equal vs confounded comparison plot
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax = axes[0]
    ax.errorbar(temperatures, ratio_confounded, yerr=ratio_confounded_se, fmt='o-',
                color='tab:blue', markersize=3, capsize=2, label='EI(M,16) / EI(S,512)')
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$={T_c:.3f}')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5)
    ax.set_ylabel('EI Ratio (512 vs 16)')
    ax.set_title('State-Space Size Effect on EI Ratio — 2D Ising (L=24)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.errorbar(temperatures, ratio_equal, yerr=ratio_equal_se, fmt='o-',
                color='tab:green', markersize=3, capsize=2, label='EI(M,16) / EI(S,16)')
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$={T_c:.3f}')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5)
    ax.set_ylabel('EI Ratio (16 vs 16)')
    ax.set_xlabel('Temperature')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'v2_equal_vs_confounded.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot_dir}/v2_equal_vs_confounded.png")

    # EI across scales with error bars
    ei_curves = {}
    for b in block_sizes:
        r = ei_macro[b][0] / np.where(ei_micro_2 > 1e-6, ei_micro_2, 1e-6)
        r_se = r * np.sqrt(
            (ei_macro[b][1] / np.where(ei_macro[b][0] > 1e-6, ei_macro[b][0], 1e-6))**2 +
            (ei_micro_2_se / np.where(ei_micro_2 > 1e-6, ei_micro_2, 1e-6))**2
        )
        ei_curves[b] = (r, r_se)
    plot_ei_across_scales(temperatures, ei_curves, T_c,
                          os.path.join(plot_dir, 'v2_ei_across_scales_equal.png'),
                          system_name='2D Ising (Equal State Space)')

    # Raw EI values — both micro scales
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.errorbar(temperatures, ei_micro_3, yerr=ei_micro_3_se, fmt='k-o', markersize=3,
                capsize=2, linewidth=1.5, label='EI(S) 3x3 [512 states]')
    ax.errorbar(temperatures, ei_micro_2, yerr=ei_micro_2_se, fmt='--s', color='gray',
                markersize=3, capsize=2, linewidth=1.5, label='EI(S) 2x2 [16 states]')
    for b_idx, b in enumerate(block_sizes):
        colors = ['tab:blue', 'tab:orange', 'tab:green']
        ax.errorbar(temperatures, ei_macro[b][0], yerr=ei_macro[b][1], fmt='o-',
                    color=colors[b_idx], markersize=3, capsize=2, linewidth=1,
                    label=f'EI(M, b={b}) [16 states]')
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$={T_c:.3f}')
    ax.set_xlabel('Temperature')
    ax.set_ylabel('Effective Information (bits)')
    ax.set_title('Raw EI Values with Error Bars — 2D Ising v2')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'v2_raw_ei_values.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot_dir}/v2_raw_ei_values.png")

    # ---- Write log ----
    log_path = os.path.join(project_root, 'results', 'phase1', 'log_v2.md')
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M')

    with open(log_path, 'w') as f:
        f.write(f"""# Phase 1 v2: Corrected Ising Model Results

## {timestamp} — PHASE 1 v2 EXPERIMENT
**Status**: COMPLETED
**Fixes applied**:
1. Scaled Laplace smoothing (alpha=1/n_states) — removes state-space size bias
2. Observed-only EI (min_obs={min_obs}) — excludes smoothing-dominated rows
3. Equal state-space control: 2x2 micro (16 states) vs 2x2 macro (16 states)
4. Multi-seed: {n_seeds} seeds per temperature with standard error bars
5. Temporal shuffle control — verifies signal from dynamics not static structure
6. L={L} (divisible by 2,3,4,8) — no silent boundary data loss

**Parameters**: L={L}, n_equilib={n_equilib}, n_steps={n_steps}, seeds={n_seeds}
**Total time**: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)

**Key Findings**:
- Kendall tau (confounded ratio vs AC): {tau_conf_ac:.4f} (p={p_conf_ac:.4e})
- Kendall tau (equal-space ratio vs AC): {tau_equal_ac:.4f} (p={p_equal_ac:.4e})
- Kendall tau (Variance vs AC): {tau_var_ac:.4f} (p={p_var_ac:.4e})
- Equal state-space emergence count: {emergence_equal}/{n_temps}
- Real ratio at T_c: {ratio_confounded[np.argmin(np.abs(temperatures-T_c))]:.3f}
- Shuffled ratio at T_c: {ratio_shuffle[np.argmin(np.abs(temperatures-T_c))]:.3f}

## Plots
- v2_money_equal_states.png — Money plot with EQUAL state-space EI ratio + error bars
- v2_money_confounded.png — Money plot with original 512-vs-16 ratio + error bars
- v2_shuffle_control.png — Real vs shuffled EI ratio
- v2_equal_vs_confounded.png — Side-by-side equal vs confounded ratios
- v2_ei_across_scales_equal.png — EI ratio at different block sizes (equal state space)
- v2_raw_ei_values.png — Raw EI values for both micro scales with error bars
""")
    print(f"\nLog written to {log_path}")
    print(f"\n{'='*70}")
    print("PHASE 1 v2 COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_phase1_v2()
