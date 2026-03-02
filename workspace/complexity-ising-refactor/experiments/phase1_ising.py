"""
Phase 1: Ising Model Experiment

Measures how EI(M)/EI(S) varies across the critical temperature,
and compares against standard early warning signals (variance, autocorrelation).

Design decisions:
- Micro EI(S) uses 3x3 patches (512 possible states = 2^9).
  Rationale: 4x4 patches give 65536 states, which is too sparse for ~200k transition
  samples. 3x3 with 512 states gives ~400 samples per state on average, which is
  adequate for transition matrix estimation with Laplace smoothing.
- Macro EI(M) uses 2x2 patches on coarse-grained grids (16 possible states).
- One sample every 10 sweeps to reduce autocorrelation.
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


def compute_patch_ei(configs, patch_size):
    """
    Compute EI from local patches of a configuration time series.

    For each pair of consecutive configurations (t, t+1), transitions between
    same-location patches are recorded. The transition matrix is estimated
    from all patch transitions across all timesteps.

    Parameters
    ----------
    configs : ndarray of shape (N, L, L)
    patch_size : int

    Returns
    -------
    ei : float
        Effective Information in bits.
    """
    states, n_states = config_to_patch_states(configs, patch_size)
    N, n_patches = states.shape

    # Collect all transitions
    states_t = states[:-1].ravel()
    states_t1 = states[1:].ravel()

    T = estimate_transition_matrix(states_t, states_t1, n_states)
    ei = effective_information(T)
    return ei


def run_phase1():
    """Execute the Phase 1 Ising model experiment."""
    print("=" * 70)
    print("PHASE 1: ISING MODEL EXPERIMENT")
    print("=" * 70)

    # Parameters
    L = 32
    temperatures = np.arange(1.5, 3.01, 0.05)
    n_equilib = 5000
    n_steps = 2000
    block_sizes = [2, 4, 8]
    micro_patch_size = 3  # 512 states (see docstring for rationale)
    macro_patch_size = 2  # 16 states on coarse-grained grids
    seed_base = 42
    T_c = 2.269

    n_temps = len(temperatures)
    print(f"\nParameters:")
    print(f"  L = {L}, n_equilib = {n_equilib}, n_steps = {n_steps}")
    print(f"  Temperatures: {temperatures[0]:.2f} to {temperatures[-1]:.2f}, {n_temps} points")
    print(f"  Micro patch: {micro_patch_size}x{micro_patch_size} ({2**(micro_patch_size**2)} states)")
    print(f"  Macro patch: {macro_patch_size}x{macro_patch_size} (16 states)")
    print(f"  Block sizes: {block_sizes}")
    print(f"  T_c = {T_c}")

    # Storage
    ei_micro = np.zeros(n_temps)
    ei_macro = {b: np.zeros(n_temps) for b in block_sizes}
    mag_means = np.zeros(n_temps)
    mag_vars = np.zeros(n_temps)
    mag_acs = np.zeros(n_temps)

    total_start = time.time()

    for idx, T in enumerate(temperatures):
        t0 = time.time()
        print(f"\n--- T = {T:.3f} ({idx+1}/{n_temps}) ---")

        # Simulate
        configs, mags = simulate_ising(L, T, n_steps, n_equilib, seed=seed_base + idx)
        mag_means[idx] = mags.mean()
        mag_vars[idx] = mags.var()

        # Autocorrelation of magnetization (lag-1)
        if len(mags) > 1:
            x = mags[:-1]
            y = mags[1:]
            mx, my = x.mean(), y.mean()
            sx, sy = x.std(), y.std()
            if sx > 0 and sy > 0:
                mag_acs[idx] = np.mean((x - mx) * (y - my)) / (sx * sy)
            else:
                mag_acs[idx] = 0.0

        # Micro EI(S)
        ei_micro[idx] = compute_patch_ei(configs, micro_patch_size)

        # Macro EI(M) at each block size
        for b in block_sizes:
            coarse = coarsegrain_timeseries(configs, b)
            ei_macro[b][idx] = compute_patch_ei(coarse, macro_patch_size)

        elapsed = time.time() - t0
        print(f"  |M| = {mag_means[idx]:.4f}, Var(M) = {mag_vars[idx]:.6f}, AC = {mag_acs[idx]:.4f}")
        print(f"  EI(S) = {ei_micro[idx]:.4f} bits")
        for b in block_sizes:
            ratio = ei_macro[b][idx] / ei_micro[idx] if ei_micro[idx] > 0 else float('nan')
            print(f"  EI(M,b={b}) = {ei_macro[b][idx]:.4f} bits, ratio = {ratio:.4f}")
        print(f"  Time: {elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    print(f"\nTotal simulation time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Save raw data
    project_root = os.path.join(os.path.dirname(__file__), '..')
    data_dir = os.path.join(project_root, 'results', 'phase1', 'data')
    np.savez(os.path.join(data_dir, 'phase1_results.npz'),
             temperatures=temperatures,
             ei_micro=ei_micro,
             ei_macro_b2=ei_macro[2],
             ei_macro_b4=ei_macro[4],
             ei_macro_b8=ei_macro[8],
             mag_means=mag_means,
             mag_vars=mag_vars,
             mag_acs=mag_acs,
             T_c=T_c, L=L, n_steps=n_steps, n_equilib=n_equilib,
             micro_patch_size=micro_patch_size,
             macro_patch_size=macro_patch_size)
    print(f"\nData saved to {data_dir}/phase1_results.npz")

    # ---- Analysis ----
    print("\n" + "=" * 70)
    print("PHASE 1 ANALYSIS")
    print("=" * 70)

    # Use b=4 as the primary macro scale for comparisons
    primary_b = 4
    ei_ratio = ei_macro[primary_b] / np.where(ei_micro > 0, ei_micro, 1e-10)

    # Kendall tau correlations
    tau_ei_var, p_ei_var = kendall_tau(ei_ratio, mag_vars)
    tau_ei_ac, p_ei_ac = kendall_tau(ei_ratio, mag_acs)
    tau_var_ac, p_var_ac = kendall_tau(mag_vars, mag_acs)

    print(f"\nKendall tau correlations:")
    print(f"  EI ratio vs Variance:       tau = {tau_ei_var:.4f}, p = {p_ei_var:.4e}")
    print(f"  EI ratio vs Autocorrelation: tau = {tau_ei_ac:.4f}, p = {p_ei_ac:.4e}")
    print(f"  Variance vs Autocorrelation: tau = {tau_var_ac:.4f}, p = {p_var_ac:.4e}")

    # Threshold detection (baseline: T < 1.8)
    baseline_mask = temperatures < 1.8
    T_trigger_ei, thresh_ei = detect_threshold_crossing(temperatures, ei_ratio, baseline_mask)
    T_trigger_var, thresh_var = detect_threshold_crossing(temperatures, mag_vars, baseline_mask)
    T_trigger_ac, thresh_ac = detect_threshold_crossing(temperatures, mag_acs, baseline_mask)

    lead_ei = compute_lead_time(T_trigger_ei, T_c)
    lead_var = compute_lead_time(T_trigger_var, T_c)
    lead_ac = compute_lead_time(T_trigger_ac, T_c)

    print(f"\nThreshold crossing (2σ above baseline):")
    print(f"  EI ratio:       T_trigger = {T_trigger_ei}, lead time = {lead_ei}")
    print(f"  Variance:       T_trigger = {T_trigger_var}, lead time = {lead_var}")
    print(f"  Autocorrelation: T_trigger = {T_trigger_ac}, lead time = {lead_ac}")

    # Does EI(M) > EI(S) ever?
    emergence_temps = []
    for i, T in enumerate(temperatures):
        for b in block_sizes:
            if ei_macro[b][i] > ei_micro[i]:
                emergence_temps.append((T, b, ei_macro[b][i], ei_micro[i]))

    print(f"\nCausal emergence (EI(M) > EI(S)): {len(emergence_temps)} occurrences")
    for T, b, ei_m, ei_s in emergence_temps[:10]:
        print(f"  T={T:.3f}, b={b}: EI(M)={ei_m:.4f} > EI(S)={ei_s:.4f}")

    # ---- Plots ----
    print("\nGenerating plots...")
    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')

    # 1. Three-panel comparison
    plot_ews_comparison(temperatures, ei_ratio, mag_vars, mag_acs, T_c,
                        os.path.join(plot_dir, 'ews_comparison.png'),
                        system_name='2D Ising Model')

    # 2. EI across scales
    ei_curves = {}
    for b in block_sizes:
        ratio_b = ei_macro[b] / np.where(ei_micro > 0, ei_micro, 1e-10)
        ei_curves[b] = (ratio_b, None)
    plot_ei_across_scales(temperatures, ei_curves, T_c,
                          os.path.join(plot_dir, 'ei_across_scales.png'),
                          system_name='2D Ising Model')

    # 3. Money plot
    plot_money(temperatures, ei_ratio, mag_vars, mag_acs, T_c,
               os.path.join(plot_dir, 'money_plot.png'),
               system_name='2D Ising Model')

    # 4. Raw EI values
    plot_raw_ei(temperatures, ei_micro, {b: ei_macro[b] for b in block_sizes}, T_c,
                os.path.join(plot_dir, 'raw_ei_values.png'),
                system_name='2D Ising Model')

    # ---- Phase Log ----
    log_path = os.path.join(project_root, 'results', 'phase1', 'log.md')
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M')

    log_content = f"""# Phase 1: Ising Model Results

## {timestamp} — PHASE 1 EXPERIMENT
**Status**: COMPLETED
**What happened**: Ran 2D Ising model (L={L}) across {n_temps} temperatures from {temperatures[0]:.2f} to {temperatures[-1]:.2f}. Computed micro EI (3x3 patches, 512 states) and macro EI (2x2 patches on coarse-grained grids, 16 states) at block sizes {block_sizes}. Compared against variance and lag-1 autocorrelation of magnetization.

**Parameters**:
- L = {L}, n_equilib = {n_equilib}, n_steps = {n_steps}
- Micro patch: {micro_patch_size}x{micro_patch_size} (512 states)
- Macro patch: {macro_patch_size}x{macro_patch_size} (16 states) on coarse-grained grids
- Sampling: 1 config per 10 sweeps
- Total simulation time: {total_elapsed:.1f}s

**Key Numbers**:
- Kendall tau (EI ratio vs Variance): {tau_ei_var:.4f} (p={p_ei_var:.4e})
- Kendall tau (EI ratio vs Autocorrelation): {tau_ei_ac:.4f} (p={p_ei_ac:.4e})
- Kendall tau (Variance vs Autocorrelation): {tau_var_ac:.4f} (p={p_var_ac:.4e})
- EI ratio trigger temp: {T_trigger_ei} (lead time: {lead_ei})
- Variance trigger temp: {T_trigger_var} (lead time: {lead_var})
- Autocorrelation trigger temp: {T_trigger_ac} (lead time: {lead_ac})
- Causal emergence (EI(M) > EI(S)): {len(emergence_temps)} occurrences

**EI values at T_c ≈ {T_c}**:
"""
    # Find nearest T to T_c
    tc_idx = np.argmin(np.abs(temperatures - T_c))
    log_content += f"- Nearest T to T_c: {temperatures[tc_idx]:.3f}\n"
    log_content += f"- EI(S) at T_c: {ei_micro[tc_idx]:.4f}\n"
    for b in block_sizes:
        ratio_tc = ei_macro[b][tc_idx] / ei_micro[tc_idx] if ei_micro[tc_idx] > 0 else float('nan')
        log_content += f"- EI(M, b={b}) at T_c: {ei_macro[b][tc_idx]:.4f}, ratio = {ratio_tc:.4f}\n"

    log_content += f"""
**Decision gate assessment**:
"""
    # Assess decision gate
    # Check if EI ratio curve is "clear and interpretable"
    ei_ratio_range = ei_ratio.max() - ei_ratio.min()
    ei_ratio_mean = ei_ratio.mean()
    relative_variation = ei_ratio_range / (ei_ratio_mean + 1e-10)

    log_content += f"- EI ratio range: {ei_ratio_range:.4f}\n"
    log_content += f"- EI ratio relative variation: {relative_variation:.4f}\n"

    # Decision
    if relative_variation > 0.1:
        log_content += "- **VERDICT: EI ratio shows meaningful variation across T. PROCEED to Phase 2.**\n"
        proceed = True
    else:
        log_content += "- **VERDICT: EI ratio is flat/noisy. INVESTIGATING before deciding.**\n"
        proceed = False

    log_content += f"""
## Plots generated
- ews_comparison.png: 3-panel comparison (EI ratio, variance, autocorrelation)
- ei_across_scales.png: EI ratio at different block sizes
- money_plot.png: All three indicators normalized, overlaid
- raw_ei_values.png: Raw EI(S) and EI(M) values
"""

    with open(log_path, 'w') as f:
        f.write(log_content)
    print(f"\nLog written to {log_path}")

    print(f"\n{'='*70}")
    print(f"PHASE 1 COMPLETE")
    print(f"{'='*70}")

    return proceed, {
        'temperatures': temperatures,
        'ei_micro': ei_micro,
        'ei_macro': ei_macro,
        'ei_ratio': ei_ratio,
        'mag_vars': mag_vars,
        'mag_acs': mag_acs,
        'tau_ei_ac': tau_ei_ac,
        'T_c': T_c,
    }


if __name__ == "__main__":
    proceed, results = run_phase1()
    if proceed:
        print("\n>>> DECISION: PROCEED TO PHASE 2 <<<")
    else:
        print("\n>>> DECISION: STOP — EI signal not clear enough <<<")
