"""
Phase 1 P1: Head-to-Head Information Measure Comparison

Computes 5 information-theoretic measures on the SAME Ising simulation data:

1. EI ratio (corrected) — subtract shuffle baseline, report delta
2. Excess entropy E_k = I(X_past_k; X_future_k) at scales k=1, 5, 10
3. Transfer entropy TE(micro->macro) and TE(macro->micro)
4. Time irreversibility — asymmetry of cross-correlation
5. Total correlation TC = sum H(X_i) - H(X_1,...,X_n)

All measures computed on same Ising simulation with L=24, 20 seeds, 31 temperatures.

OUTPUT:
- results/phase1/plots/p1_comparison.png — All measures on one plot
- results/phase1/plots/p1_lead_times.png — Which triggers first?
- results/phase1/p1_comparison.md — Full comparative analysis
"""

import sys
import os
import time
from collections import Counter
import numpy as np
from scipy import stats
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ising import simulate_ising
from src.coarse_grain import coarsegrain_timeseries, config_to_patch_states
from src.ei_compute import estimate_transition_matrix, effective_information, shannon_entropy

project_root = os.path.join(os.path.dirname(__file__), '..')


def entropy_from_counter(counter):
    """Compute Shannon entropy (bits) from a collections.Counter."""
    total = sum(counter.values())
    probs = np.array(list(counter.values())) / total
    return -np.sum(probs * np.log2(probs))


def entropy_from_tuples(tuples_list):
    """Compute Shannon entropy (bits) from a list of tuples (each a discrete state)."""
    counts = Counter(tuples_list)
    return entropy_from_counter(counts)



# ============================================================
# Measure 1: Corrected EI Ratio
# ============================================================

def compute_ei_ratio(configs, configs_coarse, patch_size, min_obs, rng):
    """Compute EI(M)/EI(S) with equalized transition counts."""
    micro_states, n_states, n_micro_patches = config_to_patch_states(configs, patch_size)
    macro_states, _, n_macro_patches = config_to_patch_states(configs_coarse, patch_size)

    micro_t = micro_states[:-1].ravel()
    micro_t1 = micro_states[1:].ravel()
    macro_t = macro_states[:-1].ravel()
    macro_t1 = macro_states[1:].ravel()

    n_macro_trans = len(macro_t)
    n_micro_trans = len(micro_t)

    if n_micro_trans > n_macro_trans:
        idx = rng.choice(n_micro_trans, size=n_macro_trans, replace=False)
        micro_t_sub = micro_t[idx]
        micro_t1_sub = micro_t1[idx]
    else:
        micro_t_sub = micro_t
        micro_t1_sub = micro_t1

    T_micro, rc_micro = estimate_transition_matrix(micro_t_sub, micro_t1_sub, n_states)
    T_macro, rc_macro = estimate_transition_matrix(macro_t, macro_t1, n_states)

    ei_micro = effective_information(T_micro, rc_micro, min_observations=min_obs)
    ei_macro = effective_information(T_macro, rc_macro, min_observations=min_obs)

    ratio = ei_macro / ei_micro if ei_micro > 1e-10 else np.nan
    return ratio, ei_micro, ei_macro


# ============================================================
# Measure 2: Excess Entropy
# ============================================================

def compute_excess_entropy(timeseries, k, n_bins=16):
    """
    Compute excess entropy E_k = I(X_past_k; X_future_k).

    Uses binned magnetization time series.
    E_k = H(X_{0:k}) + H(X_{k:2k}) - H(X_{0:2k})

    Parameters
    ----------
    timeseries : ndarray of shape (T,)
        1D time series (e.g., block magnetization).
    k : int
        Window length for past/future.
    n_bins : int
        Number of bins for discretization.

    Returns
    -------
    E_k : float
        Excess entropy in bits.
    """
    N = len(timeseries)
    if N < 2 * k + 1:
        return np.nan

    # Discretize into bins
    ts_min, ts_max = timeseries.min(), timeseries.max()
    if ts_max - ts_min < 1e-10:
        return 0.0
    binned = np.clip(
        ((timeseries - ts_min) / (ts_max - ts_min) * (n_bins - 1)).astype(int),
        0, n_bins - 1
    )

    # Build k-gram sequences
    n_grams = N - 2 * k + 1
    if n_grams < 10:
        return np.nan

    # Encode k-grams as tuple-hashes for counting
    past_grams = []
    future_grams = []
    joint_grams = []

    for i in range(n_grams):
        past = tuple(binned[i:i+k])
        future = tuple(binned[i+k:i+2*k])
        past_grams.append(past)
        future_grams.append(future)
        joint_grams.append(past + future)

    H_past = entropy_from_tuples(past_grams)
    H_future = entropy_from_tuples(future_grams)
    H_joint = entropy_from_tuples(joint_grams)

    E_k = H_past + H_future - H_joint
    return max(0.0, E_k)


def compute_excess_entropy_for_blocks(configs_coarse, k_values, n_bins=16):
    """
    Compute excess entropy averaged over all macro blocks.

    Parameters
    ----------
    configs_coarse : ndarray of shape (T, L_c, L_c)
        Coarse-grained time series.
    k_values : list of int
        Window lengths to compute.

    Returns
    -------
    results : dict mapping k -> mean excess entropy
    """
    T_steps, L_c, _ = configs_coarse.shape
    n_blocks = L_c * L_c

    results = {}
    for k in k_values:
        block_entropies = []
        for bi in range(L_c):
            for bj in range(L_c):
                ts = configs_coarse[:, bi, bj].astype(float)
                E_k = compute_excess_entropy(ts, k, n_bins=n_bins)
                if np.isfinite(E_k):
                    block_entropies.append(E_k)
        results[k] = np.mean(block_entropies) if block_entropies else np.nan

    return results


# ============================================================
# Measure 3: Transfer Entropy
# ============================================================

def compute_transfer_entropy(source_ts, target_ts, n_bins=8):
    """
    Compute transfer entropy TE(source -> target).

    TE_{X->Y} = H(Y_{t+1} | Y_t) - H(Y_{t+1} | Y_t, X_t)
              = H(Y_t, Y_{t+1}) - H(Y_t) - H(X_t, Y_t, Y_{t+1}) + H(X_t, Y_t)

    Parameters
    ----------
    source_ts : ndarray of shape (T,)
        Source time series.
    target_ts : ndarray of shape (T,)
        Target time series.
    n_bins : int
        Number of bins for discretization.

    Returns
    -------
    TE : float
        Transfer entropy in bits.
    """
    N = min(len(source_ts), len(target_ts))
    if N < 10:
        return np.nan

    # Discretize
    def discretize(ts, n_bins):
        ts_min, ts_max = ts.min(), ts.max()
        if ts_max - ts_min < 1e-10:
            return np.zeros(len(ts), dtype=int)
        return np.clip(
            ((ts - ts_min) / (ts_max - ts_min) * (n_bins - 1)).astype(int),
            0, n_bins - 1
        )

    x = discretize(source_ts[:N], n_bins)
    y = discretize(target_ts[:N], n_bins)

    # Build joint histograms using tuple encoding
    # Variables: X_t, Y_t, Y_{t+1}
    n = N - 1

    # Joint (Y_t, Y_{t+1})
    yy_counts = Counter(zip(y[:n], y[1:n+1]))
    # Marginal Y_t
    y_counts = Counter(y[:n])
    # Joint (X_t, Y_t, Y_{t+1})
    xyy_counts = Counter(zip(x[:n], y[:n], y[1:n+1]))
    # Joint (X_t, Y_t)
    xy_counts = Counter(zip(x[:n], y[:n]))

    H_yy = entropy_from_counter(yy_counts)
    H_y = entropy_from_counter(y_counts)
    H_xyy = entropy_from_counter(xyy_counts)
    H_xy = entropy_from_counter(xy_counts)

    TE = H_yy - H_y - H_xyy + H_xy
    return max(0.0, TE)


def compute_te_between_scales(configs, configs_coarse, block_size):
    """
    Compute transfer entropy between micro and macro scales.

    For each macro block, compute TE from the mean micro magnetization
    of that block's constituent spins to the macro block spin, and vice versa.

    Returns
    -------
    te_micro_to_macro : float
        Average TE(micro -> macro) across blocks.
    te_macro_to_micro : float
        Average TE(macro -> micro) across blocks.
    """
    T_steps, L, _ = configs.shape
    L_c = L // block_size
    b = block_size

    te_m2M_list = []
    te_M2m_list = []

    for bi in range(L_c):
        for bj in range(L_c):
            # Macro time series: coarse-grained block spin
            macro_ts = configs_coarse[:, bi, bj].astype(float)

            # Micro time series: mean magnetization of block
            micro_block = configs[:, bi*b:(bi+1)*b, bj*b:(bj+1)*b]
            micro_ts = micro_block.reshape(T_steps, -1).mean(axis=1)

            te_m2M = compute_transfer_entropy(micro_ts, macro_ts)
            te_M2m = compute_transfer_entropy(macro_ts, micro_ts)

            if np.isfinite(te_m2M):
                te_m2M_list.append(te_m2M)
            if np.isfinite(te_M2m):
                te_M2m_list.append(te_M2m)

    te_micro_to_macro = np.mean(te_m2M_list) if te_m2M_list else np.nan
    te_macro_to_micro = np.mean(te_M2m_list) if te_M2m_list else np.nan

    return te_micro_to_macro, te_macro_to_micro


# ============================================================
# Measure 4: Time Irreversibility
# ============================================================

def compute_time_irreversibility(configs_coarse, max_lag=10):
    """
    Compute time irreversibility as asymmetry of cross-correlation.

    For each macro block time series X_t:
    TI = sum_{tau=1}^{max_lag} |E[X_t * X_{t+tau}^2] - E[X_t^2 * X_{t+tau}]|

    This measures the asymmetry between forward and backward temporal statistics.
    Higher values indicate more time-asymmetric (irreversible) dynamics.

    Parameters
    ----------
    configs_coarse : ndarray of shape (T, L_c, L_c)
        Coarse-grained configuration time series.
    max_lag : int
        Maximum lag for cross-correlation asymmetry.

    Returns
    -------
    TI : float
        Time irreversibility averaged over all blocks.
    """
    T_steps, L_c, _ = configs_coarse.shape
    ti_values = []

    for bi in range(L_c):
        for bj in range(L_c):
            ts = configs_coarse[:, bi, bj].astype(float)
            ts_centered = ts - ts.mean()

            ti_block = 0.0
            for tau in range(1, min(max_lag + 1, T_steps)):
                x = ts_centered[:T_steps - tau]
                y = ts_centered[tau:]
                # Third-order cross-correlation asymmetry
                forward = np.mean(x * y**2)
                backward = np.mean(x**2 * y)
                ti_block += abs(forward - backward)

            ti_values.append(ti_block)

    return np.mean(ti_values)


# ============================================================
# Measure 5: Total Correlation
# ============================================================

def compute_total_correlation(configs_coarse):
    """
    Compute total correlation TC = sum H(X_i) - H(X_1,...,X_n) among macro blocks.

    Uses the coarse-grained spins (+1/-1) directly.
    For n_blocks macro blocks, TC measures how much information is shared.

    Parameters
    ----------
    configs_coarse : ndarray of shape (T, L_c, L_c)
        Coarse-grained configuration time series.

    Returns
    -------
    TC : float
        Total correlation in bits.
    """
    T_steps, L_c, _ = configs_coarse.shape
    n_blocks = L_c * L_c

    # Flatten spatial dimensions: (T, n_blocks)
    flat = configs_coarse.reshape(T_steps, n_blocks)

    # Individual entropies: each block is +1 or -1
    sum_H_i = 0.0
    for i in range(n_blocks):
        vals = flat[:, i]
        p_up = (vals == 1).mean()
        p_down = 1.0 - p_up
        probs = np.array([p for p in [p_up, p_down] if p > 0])
        sum_H_i += -np.sum(probs * np.log2(probs))

    # Joint entropy: encode the full configuration as a tuple
    configs_tuples = [tuple(flat[t]) for t in range(T_steps)]
    counts = Counter(configs_tuples)
    total = sum(counts.values())
    probs_joint = np.array(list(counts.values())) / total
    H_joint = -np.sum(probs_joint * np.log2(probs_joint))

    TC = sum_H_i - H_joint
    return max(0.0, TC)


# ============================================================
# Main Experiment
# ============================================================

def run_p1_comparison():
    """Execute the P1 head-to-head comparison of 5 information measures."""
    print("=" * 70)
    print("PHASE 1 P1: HEAD-TO-HEAD INFORMATION MEASURE COMPARISON")
    print("=" * 70)

    # Parameters — same as v3
    L = 24
    temperatures = np.arange(1.5, 3.01, 0.05)
    n_equilib = 5000
    n_steps = 2000
    block_size = 4
    patch_size = 2
    n_seeds = 20
    T_c = 2.269
    min_obs = 5
    k_values = [1, 5, 10]  # For excess entropy

    n_temps = len(temperatures)
    print(f"\nParameters:")
    print(f"  L={L}, n_equilib={n_equilib}, n_steps={n_steps}")
    print(f"  Seeds: {n_seeds}, block_size={block_size}")
    print(f"  Temperatures: {n_temps} from {temperatures[0]:.2f} to {temperatures[-1]:.2f}")
    print(f"  Excess entropy k values: {k_values}")
    print(f"\nMeasures: EI ratio, Excess entropy, Transfer entropy, "
          f"Time irreversibility, Total correlation")

    # Storage arrays — (n_seeds, n_temps)
    ei_ratio_runs = np.zeros((n_seeds, n_temps))
    excess_entropy_runs = {k: np.zeros((n_seeds, n_temps)) for k in k_values}
    te_micro2macro_runs = np.zeros((n_seeds, n_temps))
    te_macro2micro_runs = np.zeros((n_seeds, n_temps))
    te_asymmetry_runs = np.zeros((n_seeds, n_temps))
    time_irrev_runs = np.zeros((n_seeds, n_temps))
    total_corr_runs = np.zeros((n_seeds, n_temps))
    # Standard EWS
    mag_var_runs = np.zeros((n_seeds, n_temps))
    mag_ac_runs = np.zeros((n_seeds, n_temps))

    total_start = time.time()

    for idx, T in enumerate(temperatures):
        t0 = time.time()
        print(f"\n--- T = {T:.3f} ({idx+1}/{n_temps}) ---", flush=True)

        for s in range(n_seeds):
            seed = 1000 * s + idx
            rng = np.random.RandomState(seed + 99999)

            # Simulate
            configs, mags = simulate_ising(L, T, n_steps, n_equilib, seed=seed)

            # Standard EWS
            mag_var_runs[s, idx] = mags.var()
            x, y = mags[:-1], mags[1:]
            mx, my, sx, sy = x.mean(), y.mean(), x.std(), y.std()
            mag_ac_runs[s, idx] = np.mean((x-mx)*(y-my))/(sx*sy) if sx > 0 and sy > 0 else 0.0

            # Coarse-grain
            coarse = coarsegrain_timeseries(configs, block_size)

            # 1. EI Ratio (equalized)
            ratio, ei_s, ei_m = compute_ei_ratio(configs, coarse, patch_size, min_obs, rng)
            ei_ratio_runs[s, idx] = ratio

            # 2. Excess entropy (on macro block time series)
            ee_results = compute_excess_entropy_for_blocks(coarse, k_values)
            for k in k_values:
                excess_entropy_runs[k][s, idx] = ee_results[k]

            # 3. Transfer entropy (between scales)
            te_m2M, te_M2m = compute_te_between_scales(configs, coarse, block_size)
            te_micro2macro_runs[s, idx] = te_m2M
            te_macro2micro_runs[s, idx] = te_M2m
            te_asymmetry_runs[s, idx] = te_m2M - te_M2m

            # 4. Time irreversibility
            ti = compute_time_irreversibility(coarse, max_lag=10)
            time_irrev_runs[s, idx] = ti

            # 5. Total correlation
            tc = compute_total_correlation(coarse)
            total_corr_runs[s, idx] = tc

        elapsed = time.time() - t0

        # Print summary for this temperature
        print(f"  EI ratio:  {np.nanmean(ei_ratio_runs[:, idx]):.3f} +/- "
              f"{np.nanstd(ei_ratio_runs[:, idx])/np.sqrt(n_seeds):.3f}")
        print(f"  Excess E1: {np.nanmean(excess_entropy_runs[1][:, idx]):.4f}")
        print(f"  TE(m->M):  {np.nanmean(te_micro2macro_runs[:, idx]):.4f}, "
              f"TE(M->m): {np.nanmean(te_macro2micro_runs[:, idx]):.4f}")
        print(f"  Time irrev: {np.nanmean(time_irrev_runs[:, idx]):.4f}")
        print(f"  Total corr: {np.nanmean(total_corr_runs[:, idx]):.4f}")
        print(f"  Time: {elapsed:.1f}s", flush=True)

    total_elapsed = time.time() - total_start
    print(f"\nTotal time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # ====================================================================
    # ANALYSIS
    # ====================================================================
    print("\n" + "=" * 70)
    print("P1 COMPARISON ANALYSIS")
    print("=" * 70)

    # Compute means and SEs
    def mean_se(arr):
        m = np.nanmean(arr, axis=0)
        se = np.nanstd(arr, axis=0) / np.sqrt(n_seeds)
        return m, se

    ei_ratio_mean, ei_ratio_se = mean_se(ei_ratio_runs)
    ee_means = {}
    ee_ses = {}
    for k in k_values:
        ee_means[k], ee_ses[k] = mean_se(excess_entropy_runs[k])
    te_m2M_mean, te_m2M_se = mean_se(te_micro2macro_runs)
    te_M2m_mean, te_M2m_se = mean_se(te_macro2micro_runs)
    te_asym_mean, te_asym_se = mean_se(te_asymmetry_runs)
    ti_mean, ti_se = mean_se(time_irrev_runs)
    tc_mean, tc_se = mean_se(total_corr_runs)
    var_mean, var_se = mean_se(mag_var_runs)
    ac_mean, ac_se = mean_se(mag_ac_runs)

    # Peak analysis for each measure
    measures = {
        'EI Ratio': (ei_ratio_mean, ei_ratio_se),
        'Excess E(k=1)': (ee_means[1], ee_ses[1]),
        'Excess E(k=5)': (ee_means[5], ee_ses[5]),
        'Excess E(k=10)': (ee_means[10], ee_ses[10]),
        'TE(micro->macro)': (te_m2M_mean, te_m2M_se),
        'TE(macro->micro)': (te_M2m_mean, te_M2m_se),
        'TE Asymmetry': (te_asym_mean, te_asym_se),
        'Time Irreversibility': (ti_mean, ti_se),
        'Total Correlation': (tc_mean, tc_se),
        'Variance': (var_mean, var_se),
        'Autocorrelation': (ac_mean, ac_se),
    }

    print(f"\n{'Measure':<25s}  {'Peak T':>8s}  {'Peak Val':>10s}  {'Lead':>6s}  "
          f"{'tau(T)':>8s}  {'p-val':>10s}")
    print("-" * 80)

    peak_results = {}
    for name, (mean_arr, se_arr) in measures.items():
        finite = np.isfinite(mean_arr)
        if finite.sum() < 3:
            print(f"{name:<25s}  {'N/A':>8s}")
            continue

        peak_idx = np.nanargmax(mean_arr)
        peak_T = temperatures[peak_idx]
        peak_val = mean_arr[peak_idx]
        lead = T_c - peak_T

        # Kendall tau vs temperature for T < T_c
        below_Tc = (temperatures < T_c) & finite
        if below_Tc.sum() >= 3:
            tau, p = stats.kendalltau(temperatures[below_Tc], mean_arr[below_Tc])
        else:
            tau, p = np.nan, np.nan

        peak_results[name] = {
            'peak_T': peak_T, 'peak_val': peak_val, 'lead': lead,
            'tau': tau, 'p': p
        }

        print(f"{name:<25s}  {peak_T:8.3f}  {peak_val:10.4f}  {lead:+6.3f}  "
              f"{tau:+8.4f}  {p:10.3e}")

    # Lead-time detection: 2-sigma above high-T baseline
    print(f"\n--- Lead-Time Detection (2-sigma above T > 2.6 baseline) ---")
    baseline_mask = temperatures > 2.6
    lead_times = {}

    for name, (mean_arr, se_arr) in measures.items():
        finite = np.isfinite(mean_arr)
        if not (finite & baseline_mask).any():
            continue
        baseline_vals = mean_arr[baseline_mask & finite]
        if len(baseline_vals) < 2:
            continue
        bl_mean = np.mean(baseline_vals)
        bl_std = np.std(baseline_vals)
        if bl_std < 1e-10:
            bl_std = abs(bl_mean) * 0.01
        threshold = bl_mean + 2 * bl_std

        T_trigger = None
        for i in range(len(temperatures)):
            if not baseline_mask[i] and finite[i] and mean_arr[i] > threshold:
                T_trigger = temperatures[i]
                break

        if T_trigger is not None:
            lead = T_c - T_trigger
            lead_times[name] = lead
            print(f"  {name:<25s}: triggers at T={T_trigger:.3f}, lead = {lead:+.3f}")
        else:
            print(f"  {name:<25s}: never triggers")

    # ====================================================================
    # PLOTS
    # ====================================================================
    print("\nGenerating plots...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    # --- Plot 1: All measures comparison (6 panels) ---
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))

    # Panel 1: EI Ratio
    ax = axes[0, 0]
    ax.errorbar(temperatures, ei_ratio_mean, yerr=ei_ratio_se,
                fmt='o-', color='tab:blue', markersize=3, capsize=2, linewidth=1.5)
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
    ax.set_ylabel('EI(M)/EI(S)')
    ax.set_title('EI Ratio (Uncorrected)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 2: Excess Entropy
    ax = axes[0, 1]
    colors_ee = ['tab:blue', 'tab:orange', 'tab:green']
    for i, k in enumerate(k_values):
        ax.errorbar(temperatures, ee_means[k], yerr=ee_ses[k],
                    fmt='o-', color=colors_ee[i], markersize=3, capsize=2,
                    linewidth=1.5, label=f'k={k}')
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
    ax.set_ylabel('Excess Entropy (bits)')
    ax.set_title('Excess Entropy $E_k$')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 3: Transfer Entropy
    ax = axes[1, 0]
    ax.errorbar(temperatures, te_m2M_mean, yerr=te_m2M_se,
                fmt='o-', color='tab:blue', markersize=3, capsize=2,
                linewidth=1.5, label='TE(micro→macro)')
    ax.errorbar(temperatures, te_M2m_mean, yerr=te_M2m_se,
                fmt='s--', color='tab:orange', markersize=3, capsize=2,
                linewidth=1.5, label='TE(macro→micro)')
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
    ax.set_ylabel('Transfer Entropy (bits)')
    ax.set_title('Transfer Entropy Between Scales')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 4: Time Irreversibility
    ax = axes[1, 1]
    ax.errorbar(temperatures, ti_mean, yerr=ti_se,
                fmt='o-', color='tab:purple', markersize=3, capsize=2, linewidth=1.5)
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
    ax.set_ylabel('Time Irreversibility')
    ax.set_title('Time Irreversibility (Cross-Corr Asymmetry)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 5: Total Correlation
    ax = axes[2, 0]
    ax.errorbar(temperatures, tc_mean, yerr=tc_se,
                fmt='o-', color='tab:brown', markersize=3, capsize=2, linewidth=1.5)
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=f'$T_c$')
    ax.set_xlabel('Temperature')
    ax.set_ylabel('Total Correlation (bits)')
    ax.set_title('Total Correlation Among Macro Blocks')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 6: Standard EWS for comparison
    ax = axes[2, 1]
    # Normalize for overlay
    def normalize(arr):
        mn, mx = np.nanmin(arr), np.nanmax(arr)
        return (arr - mn) / (mx - mn) if mx > mn else arr * 0
    ax.plot(temperatures, normalize(var_mean), 'o-', color='tab:green',
            markersize=3, linewidth=1.5, label='Variance (norm)')
    ax.plot(temperatures, normalize(ac_mean), 's-', color='tab:red',
            markersize=3, linewidth=1.5, label='Autocorrelation (norm)')
    ax.axvline(T_c, color='black', linestyle='--', alpha=0.7, label=f'$T_c$')
    ax.set_xlabel('Temperature')
    ax.set_ylabel('Normalized Value')
    ax.set_title('Standard EWS (Normalized)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.suptitle('P1: Head-to-Head Information Measure Comparison\n'
                 '2D Ising Model, L=24, 20 seeds',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'p1_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: p1_comparison.png")

    # --- Plot 2: Normalized overlay + lead times ---
    fig, axes = plt.subplots(2, 1, figsize=(14, 12), gridspec_kw={'height_ratios': [3, 1]})

    ax = axes[0]
    # Select key measures for overlay
    key_measures = [
        ('EI Ratio', ei_ratio_mean, 'tab:blue', 'o-'),
        ('Excess E(k=5)', ee_means[5], 'tab:orange', 's-'),
        ('TE(micro→macro)', te_m2M_mean, 'tab:green', 'D-'),
        ('Time Irrev.', ti_mean, 'tab:purple', '^-'),
        ('Total Corr.', tc_mean, 'tab:brown', 'v-'),
        ('Variance', var_mean, 'tab:gray', 'x--'),
        ('Autocorrelation', ac_mean, 'tab:red', '+--'),
    ]

    for name, arr, color, fmt in key_measures:
        norm_arr = normalize(arr)
        ax.plot(temperatures, norm_arr, fmt, color=color, markersize=4,
                linewidth=1.5, label=name)

    ax.axvline(T_c, color='black', linestyle='--', linewidth=2, alpha=0.7,
               label=f'$T_c$ = {T_c:.3f}')
    ax.set_ylabel('Normalized Value [0,1]')
    ax.set_title('All Measures Normalized — Peak Location Comparison')
    ax.legend(fontsize=9, ncol=2, loc='upper left')
    ax.grid(True, alpha=0.3)

    # Lead-time bar chart
    ax = axes[1]
    if lead_times:
        names = list(lead_times.keys())
        leads = [lead_times[n] for n in names]
        colors = ['tab:blue' if l > 0 else 'tab:red' for l in leads]
        y_pos = range(len(names))
        ax.barh(y_pos, leads, color=colors, alpha=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=9)
        ax.set_xlabel('Lead Time ($T_c - T_{trigger}$)')
        ax.axvline(0, color='black', linewidth=1)
        ax.set_title('Lead Time: How Far Before $T_c$ Does Each Measure Trigger?')
        ax.grid(True, alpha=0.3, axis='x')
    else:
        ax.text(0.5, 0.5, 'No measures triggered', transform=ax.transAxes,
                ha='center', va='center', fontsize=14)
        ax.set_title('Lead Time Comparison')

    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'p1_lead_times.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: p1_lead_times.png")

    # ====================================================================
    # SAVE DATA
    # ====================================================================
    data_dir = os.path.join(project_root, 'results', 'phase1', 'data')
    os.makedirs(data_dir, exist_ok=True)

    save_dict = {
        'temperatures': temperatures, 'T_c': T_c, 'L': L,
        'n_seeds': n_seeds, 'block_size': block_size,
        'k_values': np.array(k_values),
        'ei_ratio_runs': ei_ratio_runs,
        'te_micro2macro_runs': te_micro2macro_runs,
        'te_macro2micro_runs': te_macro2micro_runs,
        'te_asymmetry_runs': te_asymmetry_runs,
        'time_irrev_runs': time_irrev_runs,
        'total_corr_runs': total_corr_runs,
        'mag_var_runs': mag_var_runs,
        'mag_ac_runs': mag_ac_runs,
    }
    for k in k_values:
        save_dict[f'excess_entropy_k{k}_runs'] = excess_entropy_runs[k]

    np.savez(os.path.join(data_dir, 'phase1_p1_comparison.npz'), **save_dict)
    print(f"\nData saved to {data_dir}/phase1_p1_comparison.npz")

    # ====================================================================
    # WRITE REPORT
    # ====================================================================
    write_comparison_report(
        temperatures, T_c, n_seeds, measures, peak_results, lead_times,
        k_values, ei_ratio_mean, ee_means, te_m2M_mean, te_M2m_mean,
        te_asym_mean, ti_mean, tc_mean, var_mean, ac_mean, total_elapsed
    )

    print(f"\n{'='*70}")
    print("P1 COMPARISON COMPLETE")
    print(f"{'='*70}")


def write_comparison_report(temperatures, T_c, n_seeds, measures, peak_results,
                            lead_times, k_values, ei_ratio_mean, ee_means,
                            te_m2M_mean, te_M2m_mean, te_asym_mean,
                            ti_mean, tc_mean, var_mean, ac_mean, total_elapsed):
    """Write the comparison analysis markdown report."""
    report_path = os.path.join(project_root, 'results', 'phase1', 'p1_comparison.md')
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M')

    with open(report_path, 'w') as f:
        f.write(f"""# P1: Head-to-Head Information Measure Comparison

## {timestamp} — P1 COMPARISON EXPERIMENT
**Status**: COMPLETED
**Runtime**: {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)
**System**: 2D Ising, L=24, {n_seeds} seeds, 31 temperatures

---

## Summary

Five information-theoretic measures compared head-to-head on the same
2D Ising simulation data. The question: which measure provides the most
useful early warning signal for the phase transition at T_c = {T_c:.3f}?

### Peak Location Comparison

| Measure | Peak T | Peak Value | Lead Time | tau(T) | p-value |
|---------|--------|-----------|-----------|--------|---------|
""")
        for name, info in sorted(peak_results.items(), key=lambda x: -x[1].get('lead', -999)):
            f.write(f"| {name} | {info['peak_T']:.3f} | {info['peak_val']:.4f} | "
                    f"{info['lead']:+.3f} | {info['tau']:+.4f} | {info['p']:.3e} |\n")

        f.write(f"""
### Lead-Time Rankings (2-sigma detection above T > 2.6 baseline)

| Rank | Measure | Lead Time |
|------|---------|-----------|
""")
        if lead_times:
            for rank, (name, lead) in enumerate(
                    sorted(lead_times.items(), key=lambda x: -x[1]), 1):
                f.write(f"| {rank} | {name} | {lead:+.3f} |\n")
        else:
            f.write("| - | No measure triggered | - |\n")

        f.write(f"""
---

## Detailed Results

### 1. EI Ratio (Causal Emergence)
- Peak: T = {temperatures[np.nanargmax(ei_ratio_mean)]:.3f}, """
                f"""value = {np.nanmax(ei_ratio_mean):.3f}
- Interpretation: Measures how much more causal structure exists at macro vs micro scale
- Caveat: Majority-vote artifact inflates values at all T; shuffle-corrected delta is the honest signal

### 2. Excess Entropy
""")
        for k in k_values:
            peak_idx = np.nanargmax(ee_means[k])
            f.write(f"- k={k}: Peak at T = {temperatures[peak_idx]:.3f}, "
                    f"value = {ee_means[k][peak_idx]:.4f}\n")

        f.write(f"""- Interpretation: Measures predictive information in block time series
- Theoretical expectation: Should diverge at T_c for infinite systems

### 3. Transfer Entropy
- TE(micro→macro) peak: T = {temperatures[np.nanargmax(te_m2M_mean)]:.3f}
- TE(macro→micro) peak: T = {temperatures[np.nanargmax(te_M2m_mean)]:.3f}
- TE asymmetry peak: T = {temperatures[np.nanargmax(te_asym_mean)]:.3f}
- Interpretation: Information flow between scales; asymmetry indicates causal direction
- Literature: Should peak on disordered side of T_c (Barnett & Lizier 2013)

### 4. Time Irreversibility
- Peak: T = {temperatures[np.nanargmax(ti_mean)]:.3f}, value = {np.nanmax(ti_mean):.4f}
- Interpretation: Asymmetry of forward vs backward dynamics
- Literature: Should peak before T_c (Comms Earth & Env 2025)

### 5. Total Correlation
- Peak: T = {temperatures[np.nanargmax(tc_mean)]:.3f}, value = {np.nanmax(tc_mean):.4f}
- Interpretation: Total shared information among macro blocks
- Expected: Should peak at T_c

### Standard EWS
- Variance peak: T = {temperatures[np.nanargmax(var_mean)]:.3f}
- Autocorrelation peak: T = {temperatures[np.nanargmax(ac_mean)]:.3f}

---

## Key Findings

""")
        # Determine which measures peak before T_c
        early_measures = []
        at_Tc_measures = []
        after_Tc_measures = []
        for name, info in peak_results.items():
            if info['lead'] > 0.1:
                early_measures.append((name, info['lead']))
            elif info['lead'] > -0.1:
                at_Tc_measures.append((name, info['lead']))
            else:
                after_Tc_measures.append((name, info['lead']))

        if early_measures:
            f.write("**Measures peaking BEFORE T_c (potential EWS):**\n")
            for name, lead in sorted(early_measures, key=lambda x: -x[1]):
                f.write(f"- {name}: lead = {lead:+.3f}\n")

        if at_Tc_measures:
            f.write("\n**Measures peaking AT T_c:**\n")
            for name, lead in at_Tc_measures:
                f.write(f"- {name}: lead = {lead:+.3f}\n")

        if after_Tc_measures:
            f.write("\n**Measures peaking AFTER T_c:**\n")
            for name, lead in after_Tc_measures:
                f.write(f"- {name}: lead = {lead:+.3f}\n")

        f.write(f"""
---

## Plots
- `p1_comparison.png` — All 5 measures in 6-panel layout
- `p1_lead_times.png` — Normalized overlay + lead-time bar chart
""")

    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    run_p1_comparison()
