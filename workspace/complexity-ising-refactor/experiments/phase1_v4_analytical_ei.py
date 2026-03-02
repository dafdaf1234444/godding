"""
Phase 1 v4: Analytical (Semi-Analytical) Effective Information for 2D Ising Model

PURPOSE: Remove ALL estimation confounds by using very long simulations to get
essentially exact transition matrices. If the emergence signal persists with
~450K transitions (25x more than v3's ~18K), it is genuinely in the dynamics,
not an artifact of finite-sample estimation noise.

APPROACH: Semi-analytical via very long simulation
- L=24 Ising at each temperature with n_steps=50000 (vs 2000 in v3)
- 1 seed only (the long run gives enough transitions)
- Micro: 144 patches x 49999 steps = 7,199,856 transitions
- Macro: 9 patches x 49999 steps = 449,991 transitions
- Also compute equalized version (subsample micro to 449,991)
- Compare: does the ratio change significantly with 25x more data?

CONVERGENCE ANALYSIS: At T=2.15, compute EI ratio with increasing transition
counts: 1K, 5K, 10K, 50K, 100K, 450K to see if the ratio converges.

KEY QUESTION: Does emergence PERSIST when both matrices have ~450K transitions?
If ratio stays elevated -> signal is real, not estimation noise
If ratio drops to ~1 -> it was estimation noise all along
"""

import sys
import os
import time
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ising import simulate_ising
from src.coarse_grain import coarsegrain_timeseries, config_to_patch_states
from src.ei_compute import estimate_transition_matrix, effective_information



def compute_ei_from_transitions(states_t, states_t1, n_states, min_obs=5):
    """Compute EI from pre-built transition arrays."""
    T_mat, rc = estimate_transition_matrix(states_t, states_t1, n_states)
    ei = effective_information(T_mat, rc, min_observations=min_obs)
    n_rows = int(np.sum(rc >= min_obs)) if min_obs > 0 else n_states
    return ei, n_rows


def compute_ei_at_subsample(micro_t, micro_t1, macro_t, macro_t1,
                            n_states, n_sub, min_obs, rng):
    """
    Compute EI ratio at a specific subsample size.
    Both micro and macro are subsampled to n_sub transitions.
    """
    n_micro = len(micro_t)
    n_macro = len(macro_t)

    # Subsample micro
    if n_micro > n_sub:
        idx_m = rng.choice(n_micro, size=n_sub, replace=False)
        mt, mt1 = micro_t[idx_m], micro_t1[idx_m]
    else:
        mt, mt1 = micro_t, micro_t1

    # Subsample macro
    if n_macro > n_sub:
        idx_M = rng.choice(n_macro, size=n_sub, replace=False)
        Mt, Mt1 = macro_t[idx_M], macro_t1[idx_M]
    else:
        Mt, Mt1 = macro_t, macro_t1

    ei_micro, rows_micro = compute_ei_from_transitions(mt, mt1, n_states, min_obs)
    ei_macro, rows_macro = compute_ei_from_transitions(Mt, Mt1, n_states, min_obs)

    ratio = ei_macro / ei_micro if ei_micro > 1e-10 else np.nan
    return ei_micro, ei_macro, ratio, rows_micro, rows_macro


def run_phase1_v4():
    """Execute Phase 1 v4 -- Analytical (semi-analytical) EI computation."""
    print("=" * 70)
    print("PHASE 1 v4: ANALYTICAL (SEMI-ANALYTICAL) EFFECTIVE INFORMATION")
    print("=" * 70)

    # Parameters
    L = 24
    temperatures = np.arange(1.8, 2.55, 0.05)
    n_equilib = 10000
    n_steps = 50000
    block_size = 4
    patch_size = 2
    T_c = 2.269
    min_obs = 5
    seed = 42

    n_temps = len(temperatures)
    print(f"\nParameters:")
    print(f"  L={L}, n_equilib={n_equilib}, n_steps={n_steps}")
    print(f"  block_size={block_size}, patch_size={patch_size}")
    print(f"  State space: 2^(2x2) = 16 states (equal for micro and macro)")
    print(f"  min_obs={min_obs}, seed={seed}")
    print(f"  Temperatures: {temperatures[0]:.2f} to {temperatures[-1]:.2f} "
          f"({n_temps} values)")

    # Expected transitions
    n_micro_patches = (L // patch_size) ** 2  # 144
    n_macro_patches = (L // block_size // patch_size) ** 2  # 9
    n_micro_trans = n_micro_patches * (n_steps - 1)
    n_macro_trans = n_macro_patches * (n_steps - 1)
    print(f"\n  Expected transitions per temperature:")
    print(f"    Micro: {n_micro_patches} patches x {n_steps-1} steps = "
          f"{n_micro_trans:,} transitions")
    print(f"    Macro: {n_macro_patches} patches x {n_steps-1} steps = "
          f"{n_macro_trans:,} transitions")
    print(f"    Equalized: both subsampled to {n_macro_trans:,}")
    print(f"    v3 had: ~17,991 transitions each (equalized)")
    print(f"    Improvement: {n_macro_trans / 17991:.0f}x more data")

    # Storage
    ei_micro_full = np.zeros(n_temps)
    ei_micro_equalized = np.zeros(n_temps)
    ei_macro_full = np.zeros(n_temps)
    ratio_full = np.zeros(n_temps)
    ratio_equalized = np.zeros(n_temps)
    rows_micro_full = np.zeros(n_temps, dtype=int)
    rows_micro_eq = np.zeros(n_temps, dtype=int)
    rows_macro = np.zeros(n_temps, dtype=int)

    # For convergence analysis at T=2.15
    T_convergence = 2.15
    convergence_Ns = [1000, 5000, 10000, 50000, 100000, n_macro_trans]
    convergence_ratios = {}
    convergence_ei_micro = {}
    convergence_ei_macro = {}

    total_start = time.time()

    for idx, T in enumerate(temperatures):
        t0 = time.time()
        print(f"\n{'='*50}")
        print(f"T = {T:.3f} ({idx+1}/{n_temps})")
        print(f"{'='*50}", flush=True)

        # Run simulation
        print(f"  Simulating {n_steps} steps (this takes a while)...", flush=True)
        configs, mags = simulate_ising(L, T, n_steps, n_equilib, seed=seed)
        sim_time = time.time() - t0
        print(f"  Simulation done in {sim_time:.1f}s")

        # Coarse-grain
        coarse = coarsegrain_timeseries(configs, block_size)

        # Extract patch states
        micro_states, n_states, n_mp = config_to_patch_states(configs, patch_size)
        macro_states, _, n_Mp = config_to_patch_states(coarse, patch_size)

        # Build transition arrays
        micro_t = micro_states[:-1].ravel()
        micro_t1 = micro_states[1:].ravel()
        macro_t = macro_states[:-1].ravel()
        macro_t1 = macro_states[1:].ravel()

        actual_micro_trans = len(micro_t)
        actual_macro_trans = len(macro_t)

        # 1. EI(micro, full) -- all 7.2M transitions
        ei_mf, rows_mf = compute_ei_from_transitions(
            micro_t, micro_t1, n_states, min_obs)
        ei_micro_full[idx] = ei_mf
        rows_micro_full[idx] = rows_mf

        # 2. EI(macro) -- all 450K transitions
        ei_M, rows_M = compute_ei_from_transitions(
            macro_t, macro_t1, n_states, min_obs)
        ei_macro_full[idx] = ei_M
        rows_macro[idx] = rows_M

        # 3. EI(micro, equalized) -- subsampled to match macro count
        rng = np.random.RandomState(seed + idx * 1000 + 77777)
        if actual_micro_trans > actual_macro_trans:
            sub_idx = rng.choice(actual_micro_trans, size=actual_macro_trans,
                                 replace=False)
            micro_t_sub = micro_t[sub_idx]
            micro_t1_sub = micro_t1[sub_idx]
        else:
            micro_t_sub = micro_t
            micro_t1_sub = micro_t1

        ei_me, rows_me = compute_ei_from_transitions(
            micro_t_sub, micro_t1_sub, n_states, min_obs)
        ei_micro_equalized[idx] = ei_me
        rows_micro_eq[idx] = rows_me

        # 4. Ratios
        ratio_full[idx] = ei_M / ei_mf if ei_mf > 1e-10 else np.nan
        ratio_equalized[idx] = ei_M / ei_me if ei_me > 1e-10 else np.nan

        elapsed = time.time() - t0
        print(f"  Results:")
        print(f"    EI(micro, full):      {ei_mf:.6f} ({actual_micro_trans:,} trans, "
              f"{rows_mf}/16 rows)")
        print(f"    EI(micro, equalized): {ei_me:.6f} ({actual_macro_trans:,} trans, "
              f"{rows_me}/16 rows)")
        print(f"    EI(macro):            {ei_M:.6f} ({actual_macro_trans:,} trans, "
              f"{rows_M}/16 rows)")
        print(f"    Ratio(full):          {ratio_full[idx]:.4f}")
        print(f"    Ratio(equalized):     {ratio_equalized[idx]:.4f}")
        print(f"  Total time for T={T:.3f}: {elapsed:.1f}s")

        # Convergence analysis at T=2.15
        if abs(T - T_convergence) < 0.001:
            print(f"\n  --- CONVERGENCE ANALYSIS at T={T:.3f} ---")
            for n_sub in convergence_Ns:
                # Run multiple subsamples for stability
                ratios_at_n = []
                eis_micro_at_n = []
                eis_macro_at_n = []
                n_reps = 10
                for rep in range(n_reps):
                    rng_conv = np.random.RandomState(
                        seed + idx * 1000 + rep * 100 + 88888)
                    ei_mi, ei_Ma, r, _, _ = compute_ei_at_subsample(
                        micro_t, micro_t1, macro_t, macro_t1,
                        n_states, n_sub, min_obs, rng_conv)
                    ratios_at_n.append(r)
                    eis_micro_at_n.append(ei_mi)
                    eis_macro_at_n.append(ei_Ma)

                mean_r = np.nanmean(ratios_at_n)
                std_r = np.nanstd(ratios_at_n)
                mean_mi = np.nanmean(eis_micro_at_n)
                mean_Ma = np.nanmean(eis_macro_at_n)
                convergence_ratios[n_sub] = (mean_r, std_r, ratios_at_n)
                convergence_ei_micro[n_sub] = (mean_mi, np.nanstd(eis_micro_at_n))
                convergence_ei_macro[n_sub] = (mean_Ma, np.nanstd(eis_macro_at_n))

                print(f"    N={n_sub:>7,}: ratio={mean_r:.4f} +/- {std_r:.4f}, "
                      f"EI(micro)={mean_mi:.6f}, EI(macro)={mean_Ma:.6f}")

    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print(f"Total simulation time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"{'='*70}")

    # ====================================================================
    # ANALYSIS
    # ====================================================================
    print("\n" + "=" * 70)
    print("ANALYSIS: DOES EMERGENCE PERSIST WITH ESSENTIALLY EXACT MATRICES?")
    print("=" * 70)

    print(f"\n--- Temperature scan summary (min_obs={min_obs}) ---")
    print(f"{'T':>6s}  {'EI(micro,full)':>14s}  {'EI(micro,eq)':>12s}  "
          f"{'EI(macro)':>10s}  {'Ratio(full)':>11s}  {'Ratio(eq)':>9s}")
    print("-" * 75)
    for idx, T in enumerate(temperatures):
        print(f"{T:6.3f}  {ei_micro_full[idx]:14.6f}  {ei_micro_equalized[idx]:12.6f}  "
              f"{ei_macro_full[idx]:10.6f}  {ratio_full[idx]:11.4f}  "
              f"{ratio_equalized[idx]:9.4f}")

    # Key metrics
    print(f"\n--- Key findings ---")
    print(f"  Mean ratio (full):      {np.nanmean(ratio_full):.4f}")
    print(f"  Mean ratio (equalized): {np.nanmean(ratio_equalized):.4f}")
    print(f"  Max ratio (full):       {np.nanmax(ratio_full):.4f} at "
          f"T={temperatures[np.nanargmax(ratio_full)]:.3f}")
    print(f"  Max ratio (equalized):  {np.nanmax(ratio_equalized):.4f} at "
          f"T={temperatures[np.nanargmax(ratio_equalized)]:.3f}")

    # Check if emergence persists
    emergence_full = np.sum(ratio_full > 1.0)
    emergence_eq = np.sum(ratio_equalized > 1.0)
    print(f"\n  Emergence (ratio > 1):")
    print(f"    Full:      {emergence_full}/{n_temps} temperatures")
    print(f"    Equalized: {emergence_eq}/{n_temps} temperatures")

    # Near-critical analysis
    near_crit_mask = np.abs(temperatures - T_c) < 0.15
    if near_crit_mask.any():
        print(f"\n  Near T_c ({T_c:.3f}) analysis (|T - T_c| < 0.15):")
        print(f"    Mean ratio (full):      "
              f"{np.nanmean(ratio_full[near_crit_mask]):.4f}")
        print(f"    Mean ratio (equalized): "
              f"{np.nanmean(ratio_equalized[near_crit_mask]):.4f}")

    # Convergence analysis results
    if convergence_ratios:
        print(f"\n--- Convergence analysis at T={T_convergence:.2f} ---")
        print(f"{'N_transitions':>14s}  {'Ratio':>8s}  {'Std':>8s}  {'Converged?':>10s}")
        print("-" * 50)
        prev_ratio = None
        for n_sub in convergence_Ns:
            mean_r, std_r, _ = convergence_ratios[n_sub]
            if prev_ratio is not None:
                change = abs(mean_r - prev_ratio)
                converged = "YES" if change < 0.05 else "NO"
            else:
                converged = "-"
            print(f"{n_sub:>14,}  {mean_r:>8.4f}  {std_r:>8.4f}  {converged:>10s}")
            prev_ratio = mean_r

        # Extrapolate: is the ratio stabilizing?
        last_two = [convergence_ratios[n][0] for n in convergence_Ns[-2:]]
        delta = abs(last_two[1] - last_two[0])
        print(f"\n  Change between last two sample sizes: {delta:.4f}")
        if delta < 0.02:
            print(f"  --> CONVERGED: ratio is stable at ~{last_two[1]:.3f}")
            if last_two[1] > 1.1:
                print(f"  --> EMERGENCE IS REAL: converged ratio {last_two[1]:.3f} > 1")
            elif last_two[1] > 0.95:
                print(f"  --> MARGINAL: converged ratio {last_two[1]:.3f} is near 1")
            else:
                print(f"  --> NO EMERGENCE: converged ratio {last_two[1]:.3f} < 1")
        else:
            print(f"  --> NOT YET CONVERGED (delta={delta:.4f} > 0.02)")

    # ====================================================================
    # VERDICT
    # ====================================================================
    print(f"\n{'='*70}")
    print("VERDICT")
    print(f"{'='*70}")

    # Compare with v3 expectations
    mean_ratio_eq = np.nanmean(ratio_equalized)
    max_ratio_eq = np.nanmax(ratio_equalized)

    if max_ratio_eq > 3.0:
        print(f"  STRONG EMERGENCE: Max equalized ratio = {max_ratio_eq:.2f}")
        print(f"  Signal persists with 25x more data than v3.")
        print(f"  This is NOT estimation noise.")
    elif max_ratio_eq > 1.5:
        print(f"  MODERATE EMERGENCE: Max equalized ratio = {max_ratio_eq:.2f}")
        print(f"  Signal persists but is weaker than v3 suggested.")
        print(f"  Some inflation in v3 was likely estimation noise.")
    elif max_ratio_eq > 1.1:
        print(f"  WEAK EMERGENCE: Max equalized ratio = {max_ratio_eq:.2f}")
        print(f"  Very small effect remains. Mostly estimation noise in v3.")
    else:
        print(f"  NO EMERGENCE: Max equalized ratio = {max_ratio_eq:.2f}")
        print(f"  Signal was entirely estimation noise. Ratio -> 1 with more data.")

    # ====================================================================
    # PLOTS
    # ====================================================================
    print("\n\nGenerating plots...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    project_root = os.path.join(os.path.dirname(__file__), '..')
    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    # --- Plot 1: Ratio vs Temperature for different sample sizes ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Left: ratio curves
    ax = axes[0]
    ax.plot(temperatures, ratio_full, 'o-', color='tab:blue', markersize=5,
            linewidth=2, label=f'Full micro ({n_micro_trans:,} trans)')
    ax.plot(temperatures, ratio_equalized, 's-', color='tab:orange', markersize=5,
            linewidth=2, label=f'Equalized ({n_macro_trans:,} trans each)')
    ax.axvline(T_c, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=f'$T_c$ = {T_c:.3f}')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5, label='Ratio = 1')
    ax.set_xlabel('Temperature', fontsize=12)
    ax.set_ylabel('EI(macro) / EI(micro)', fontsize=12)
    ax.set_title('v4: Analytical EI Ratio\n(50K steps, ~450K-7.2M transitions)',
                 fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Right: raw EI values
    ax = axes[1]
    ax.plot(temperatures, ei_micro_full, 'o-', color='black', markersize=4,
            linewidth=1.5, label=f'EI(micro, full) [{n_micro_trans:,}]')
    ax.plot(temperatures, ei_micro_equalized, 's--', color='gray', markersize=4,
            linewidth=1.5, label=f'EI(micro, eq) [{n_macro_trans:,}]')
    ax.plot(temperatures, ei_macro_full, '^-', color='tab:blue', markersize=4,
            linewidth=1.5, label=f'EI(macro) [{n_macro_trans:,}]')
    ax.axvline(T_c, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=f'$T_c$ = {T_c:.3f}')
    ax.set_xlabel('Temperature', fontsize=12)
    ax.set_ylabel('Effective Information (bits)', fontsize=12)
    ax.set_title('Raw EI Values', fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot1_path = os.path.join(plot_dir, 'v4_analytical_ei.png')
    plt.savefig(plot1_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot1_path}")

    # --- Plot 2: Convergence analysis ---
    if convergence_ratios:
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # Left: ratio vs N
        ax = axes[0]
        Ns = sorted(convergence_ratios.keys())
        means = [convergence_ratios[n][0] for n in Ns]
        stds = [convergence_ratios[n][1] for n in Ns]
        ax.errorbar(Ns, means, yerr=stds, fmt='o-', color='tab:blue',
                    markersize=6, capsize=4, linewidth=2)
        ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5, label='Ratio = 1')
        ax.set_xscale('log')
        ax.set_xlabel('Number of transitions (both scales)', fontsize=12)
        ax.set_ylabel('EI(macro) / EI(micro)', fontsize=12)
        ax.set_title(f'Convergence of EI Ratio at T={T_convergence:.2f}\n'
                     f'(10 subsamples per point)', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        # Middle: EI values vs N
        ax = axes[1]
        micro_means = [convergence_ei_micro[n][0] for n in Ns]
        micro_stds = [convergence_ei_micro[n][1] for n in Ns]
        macro_means = [convergence_ei_macro[n][0] for n in Ns]
        macro_stds = [convergence_ei_macro[n][1] for n in Ns]
        ax.errorbar(Ns, micro_means, yerr=micro_stds, fmt='o-', color='black',
                    markersize=5, capsize=3, linewidth=1.5, label='EI(micro)')
        ax.errorbar(Ns, macro_means, yerr=macro_stds, fmt='s-', color='tab:blue',
                    markersize=5, capsize=3, linewidth=1.5, label='EI(macro)')
        ax.set_xscale('log')
        ax.set_xlabel('Number of transitions', fontsize=12)
        ax.set_ylabel('Effective Information (bits)', fontsize=12)
        ax.set_title(f'Raw EI Convergence at T={T_convergence:.2f}', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        # Right: ratio change between successive Ns
        ax = axes[2]
        if len(Ns) > 1:
            deltas = [abs(means[i+1] - means[i]) for i in range(len(Ns)-1)]
            mid_Ns = [(Ns[i] + Ns[i+1])/2 for i in range(len(Ns)-1)]
            ax.plot(mid_Ns, deltas, 'o-', color='tab:red', markersize=6, linewidth=2)
            ax.axhline(0.02, color='green', linestyle='--', alpha=0.7,
                       label='Convergence threshold (0.02)')
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.set_xlabel('N (midpoint)', fontsize=12)
            ax.set_ylabel('|Delta ratio|', fontsize=12)
            ax.set_title('Rate of Convergence', fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plot2_path = os.path.join(plot_dir, 'v4_convergence.png')
        plt.savefig(plot2_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {plot2_path}")

    # ====================================================================
    # SAVE DATA
    # ====================================================================
    data_dir = os.path.join(project_root, 'results', 'phase1', 'data')
    os.makedirs(data_dir, exist_ok=True)

    save_dict = {
        'temperatures': temperatures, 'T_c': T_c, 'L': L,
        'n_steps': n_steps, 'n_equilib': n_equilib,
        'block_size': block_size, 'patch_size': patch_size,
        'min_obs': min_obs, 'seed': seed,
        'ei_micro_full': ei_micro_full,
        'ei_micro_equalized': ei_micro_equalized,
        'ei_macro_full': ei_macro_full,
        'ratio_full': ratio_full,
        'ratio_equalized': ratio_equalized,
        'rows_micro_full': rows_micro_full,
        'rows_micro_eq': rows_micro_eq,
        'rows_macro': rows_macro,
    }

    # Add convergence data
    if convergence_ratios:
        save_dict['convergence_Ns'] = np.array(convergence_Ns)
        save_dict['convergence_ratio_means'] = np.array(
            [convergence_ratios[n][0] for n in convergence_Ns])
        save_dict['convergence_ratio_stds'] = np.array(
            [convergence_ratios[n][1] for n in convergence_Ns])
        save_dict['convergence_ei_micro_means'] = np.array(
            [convergence_ei_micro[n][0] for n in convergence_Ns])
        save_dict['convergence_ei_macro_means'] = np.array(
            [convergence_ei_macro[n][0] for n in convergence_Ns])

    np.savez(os.path.join(data_dir, 'phase1_v4_results.npz'), **save_dict)
    print(f"\nData saved to {data_dir}/phase1_v4_results.npz")

    # ====================================================================
    # FINAL SUMMARY
    # ====================================================================
    print(f"\n{'='*70}")
    print("PHASE 1 v4 COMPLETE: ANALYTICAL EI RESULTS")
    print(f"{'='*70}")
    print(f"  Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"  Transitions: micro={n_micro_trans:,}, macro={n_macro_trans:,}")
    print(f"  Mean ratio (full):      {np.nanmean(ratio_full):.4f}")
    print(f"  Mean ratio (equalized): {np.nanmean(ratio_equalized):.4f}")
    print(f"  Max ratio (equalized):  {np.nanmax(ratio_equalized):.4f} at "
          f"T={temperatures[np.nanargmax(ratio_equalized)]:.3f}")
    if convergence_ratios:
        final_conv = convergence_ratios[convergence_Ns[-1]][0]
        print(f"  Converged ratio at T=2.15: {final_conv:.4f}")


if __name__ == "__main__":
    run_phase1_v4()
