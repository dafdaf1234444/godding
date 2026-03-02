"""
Phase 3: Synthetic Daphnia-like Population Collapse

Uses a fold bifurcation model (harvested population with slowly increasing
mortality/harvest rate) to generate a time series with a known tipping point.

Model: dx/dt = r*x*(1 - x/K) - h*x^2/(x^2 + s^2) + sigma*dW

This is a standard fold bifurcation model from the EWS literature (Scheffer 2009,
Dakos et al. 2012). The harvest rate h increases slowly over time, driving the
system toward a fold bifurcation where the stable equilibrium disappears.

NOTE: This uses SYNTHETIC data, not the real Drake & Griffen 2010 dataset.
"""

import sys
import os
import time
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ei_compute import estimate_transition_matrix, effective_information
from src.ews_standard import compute_ews
from src.analysis import kendall_tau
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def simulate_fold_bifurcation(r=1.0, K=10.0, s=1.0, h_start=0.5, h_end=2.8,
                               x0=8.0, dt=0.01, n_steps=50000, sigma=0.1,
                               seed=42):
    """
    Simulate a harvested population approaching a fold bifurcation.

    dx = [r*x*(1 - x/K) - h*x^2/(x^2 + s^2)] * dt + sigma * dW

    h increases linearly from h_start to h_end over n_steps.

    Parameters
    ----------
    r : float
        Intrinsic growth rate.
    K : float
        Carrying capacity.
    s : float
        Half-saturation constant for harvest function.
    h_start, h_end : float
        Harvest rate at start and end of simulation.
    x0 : float
        Initial population.
    dt : float
        Timestep.
    n_steps : int
        Total number of timesteps.
    sigma : float
        Noise intensity.
    seed : int
        Random seed.

    Returns
    -------
    x : ndarray of shape (n_steps,)
        Population time series.
    h_values : ndarray of shape (n_steps,)
        Harvest rate at each timestep (the control parameter).
    times : ndarray of shape (n_steps,)
        Time values.
    """
    rng = np.random.RandomState(seed)

    x = np.empty(n_steps)
    h_values = np.linspace(h_start, h_end, n_steps)
    times = np.arange(n_steps) * dt

    x[0] = x0
    sqrt_dt = np.sqrt(dt)

    for t in range(1, n_steps):
        h = h_values[t - 1]
        x_curr = max(x[t - 1], 0.001)  # Avoid division by zero

        # Deterministic drift
        growth = r * x_curr * (1.0 - x_curr / K)
        harvest = h * x_curr ** 2 / (x_curr ** 2 + s ** 2)
        drift = growth - harvest

        # Stochastic term
        noise = sigma * sqrt_dt * rng.randn()

        x[t] = x_curr + drift * dt + noise
        x[t] = max(x[t], 0.001)  # Population can't go negative

    return x, h_values, times


def find_bifurcation_point(r=1.0, K=10.0, s=1.0, h_range=None):
    """
    Numerically find the fold bifurcation point h_c.

    At the fold bifurcation, the stable and unstable equilibria coalesce.
    We find it by looking for where dx/dt = 0 has a double root.

    Returns
    -------
    h_c : float
        Critical harvest rate.
    x_c : float
        Population at the bifurcation.
    """
    from scipy.optimize import brentq

    if h_range is None:
        h_range = np.linspace(0.5, 3.0, 1000)

    # For each h, find equilibria where f(x) = r*x*(1-x/K) - h*x^2/(x^2+s^2) = 0
    # Divide by x (since x>0): r*(1-x/K) - h*x/(x^2+s^2) = 0
    # The fold happens when f'(x) = 0 simultaneously

    # Simpler approach: sweep h and check if stable equilibrium exists
    h_c = None
    x_c = None

    for h in h_range:
        def f(x):
            return r * x * (1 - x / K) - h * x ** 2 / (x ** 2 + s ** 2)

        # Check for equilibria in (0, K)
        x_test = np.linspace(0.01, K, 1000)
        f_vals = np.array([f(x) for x in x_test])

        # Count sign changes (roots)
        sign_changes = np.where(np.diff(np.sign(f_vals)))[0]

        # If no positive equilibria, we've passed the bifurcation
        # Before bifurcation: 2 positive roots (stable high, unstable low)
        # After: 0 positive roots
        if len(sign_changes) == 0:
            h_c = h
            break

    if h_c is None:
        print("  WARNING: Bifurcation point not found in range. Using h=2.5 as estimate.")
        h_c = 2.5
        x_c = 3.0
    else:
        # Find the approximate x at bifurcation (the last positive equilibrium)
        # Use the h just before bifurcation
        h_pre = h - (h_range[1] - h_range[0])
        def f_pre(x):
            return r * x * (1 - x / K) - h_pre * x ** 2 / (x ** 2 + s ** 2)
        x_test = np.linspace(0.01, K, 1000)
        f_vals = np.array([f_pre(x) for x in x_test])
        sign_changes = np.where(np.diff(np.sign(f_vals)))[0]
        if len(sign_changes) > 0:
            x_c = x_test[sign_changes[-1]]
        else:
            x_c = 3.0

    return h_c, x_c


def compute_sliding_ei(timeseries, window_size, n_bins_micro, n_bins_macro,
                        macro_window=5):
    """
    Compute sliding-window EI(S) and EI(M) for a 1D time series.

    Micro-state: raw values discretized into n_bins_micro bins.
    Macro-state: rolling mean (window=macro_window) discretized into n_bins_macro bins.

    Parameters
    ----------
    timeseries : ndarray of shape (N,)
    window_size : int
        Sliding window size for EI computation.
    n_bins_micro : int
        Number of bins for micro-state discretization.
    n_bins_macro : int
        Number of bins for macro-state discretization.
    macro_window : int
        Rolling mean window size for macro state.

    Returns
    -------
    ei_micro : ndarray
        EI(S) at each window position.
    ei_macro : ndarray
        EI(M) at each window position.
    timestamps : ndarray
        Center of each window.
    """
    N = len(timeseries)

    # Create macro time series (rolling mean)
    macro_ts = np.convolve(timeseries, np.ones(macro_window) / macro_window,
                           mode='valid')

    # Align: macro_ts is shorter by (macro_window - 1)
    offset = macro_window // 2
    micro_ts = timeseries[offset:offset + len(macro_ts)]

    # Discretize
    # Use percentile-based bins for better coverage
    micro_bins = percentile_discretize(micro_ts, n_bins_micro)
    macro_bins = percentile_discretize(macro_ts, n_bins_macro)

    # Sliding window EI
    n_windows = len(micro_ts) - window_size + 1
    if n_windows <= 0:
        raise ValueError(f"Window size {window_size} too large for series length {len(micro_ts)}")

    ei_micro_arr = np.empty(n_windows)
    ei_macro_arr = np.empty(n_windows)
    timestamps = np.empty(n_windows)

    for i in range(n_windows):
        window_micro = micro_bins[i:i + window_size]
        window_macro = macro_bins[i:i + window_size]

        # Micro EI
        states_t = window_micro[:-1]
        states_t1 = window_micro[1:]
        T_micro, rc_micro = estimate_transition_matrix(states_t, states_t1, n_bins_micro)
        ei_micro_arr[i] = effective_information(T_micro, rc_micro, min_observations=5)

        # Macro EI
        states_t = window_macro[:-1]
        states_t1 = window_macro[1:]
        T_macro, rc_macro = estimate_transition_matrix(states_t, states_t1, n_bins_macro)
        ei_macro_arr[i] = effective_information(T_macro, rc_macro, min_observations=5)

        timestamps[i] = offset + i + window_size / 2.0

    return ei_micro_arr, ei_macro_arr, timestamps


def percentile_discretize(x, n_bins):
    """
    Discretize a time series into n_bins using percentile-based boundaries.

    This ensures roughly equal counts per bin, which gives better transition
    matrix estimates than uniform-width bins.

    Parameters
    ----------
    x : ndarray
    n_bins : int

    Returns
    -------
    bins : ndarray of int in [0, n_bins-1]
    """
    percentiles = np.linspace(0, 100, n_bins + 1)
    boundaries = np.percentile(x, percentiles)
    bins = np.digitize(x, boundaries[1:-1])  # n_bins-1 boundaries → n_bins bins
    return bins.clip(0, n_bins - 1)


def run_phase3():
    """Execute Phase 3: Synthetic Daphnia population collapse."""
    print("=" * 70)
    print("PHASE 3: SYNTHETIC DAPHNIA POPULATION COLLAPSE")
    print("(Using synthetic fold bifurcation model — NOT real data)")
    print("=" * 70)

    # Model parameters
    r = 1.0
    K_cap = 10.0
    s = 1.0
    h_start = 0.5
    h_end = 2.8
    x0 = 8.0
    dt = 0.01
    n_steps = 50000
    sigma = 0.1
    seed = 42

    # EI parameters
    ei_window = 500
    n_bins_micro = 20
    n_bins_macro = 10
    macro_smooth_window = 5
    ews_window = 500

    # Find bifurcation point
    print("\nFinding bifurcation point...")
    h_c, x_c = find_bifurcation_point(r, K_cap, s)
    print(f"  h_c ≈ {h_c:.3f}, x_c ≈ {x_c:.3f}")

    # Simulate
    print(f"\nSimulating fold bifurcation model...")
    print(f"  Parameters: r={r}, K={K_cap}, s={s}")
    print(f"  h: {h_start} → {h_end}, n_steps={n_steps}, dt={dt}")
    print(f"  sigma={sigma}")

    t0 = time.time()
    x, h_values, times = simulate_fold_bifurcation(r, K_cap, s, h_start, h_end,
                                                     x0, dt, n_steps, sigma, seed)
    elapsed = time.time() - t0
    print(f"  Simulation time: {elapsed:.1f}s")
    print(f"  x range: [{x.min():.4f}, {x.max():.4f}]")
    print(f"  Final x: {x[-1]:.4f}")

    # Subsample for analysis (take every 10th point to reduce correlation)
    subsample = 10
    x_sub = x[::subsample]
    h_sub = h_values[::subsample]
    t_sub = times[::subsample]
    print(f"  Subsampled: {len(x_sub)} points (every {subsample}th)")

    # Find the collapse point in the time series
    # (where x drops below 50% of initial value)
    collapse_idx = None
    for i in range(len(x_sub)):
        if x_sub[i] < 0.5 * x0:
            collapse_idx = i
            break
    if collapse_idx is not None:
        h_collapse = h_sub[collapse_idx]
        t_collapse = t_sub[collapse_idx]
        print(f"  Collapse at t={t_collapse:.1f}, h={h_collapse:.3f}")
    else:
        print("  No collapse detected in timeseries")
        h_collapse = h_c

    # Compute standard EWS
    print(f"\nComputing standard EWS (window={ews_window})...")
    ews = compute_ews(x_sub, window_size=ews_window)

    # Compute sliding-window EI
    print(f"Computing sliding-window EI (window={ei_window}, micro_bins={n_bins_micro}, macro_bins={n_bins_macro})...")
    ei_micro, ei_macro, ei_timestamps = compute_sliding_ei(
        x_sub, ei_window, n_bins_micro, n_bins_macro, macro_smooth_window
    )

    ei_ratio = ei_macro / np.where(ei_micro > 0, ei_micro, 1e-10)

    print(f"  EI(S) range: [{ei_micro.min():.4f}, {ei_micro.max():.4f}]")
    print(f"  EI(M) range: [{ei_macro.min():.4f}, {ei_macro.max():.4f}]")
    print(f"  EI ratio range: [{ei_ratio.min():.4f}, {ei_ratio.max():.4f}]")

    # Map EWS timestamps and EI timestamps to h values for comparison
    ews_h = np.interp(ews['timestamps'], np.arange(len(x_sub)), h_sub)
    ei_h = np.interp(ei_timestamps, np.arange(len(x_sub)), h_sub)

    # Kendall tau (use only pre-collapse data)
    if collapse_idx is not None:
        pre_collapse_ews = ews_h < h_collapse
        pre_collapse_ei = ei_h < h_collapse
    else:
        pre_collapse_ews = np.ones(len(ews_h), dtype=bool)
        pre_collapse_ei = np.ones(len(ei_h), dtype=bool)

    # For tau, correlate the indicators with h (the control parameter)
    # Increasing h should correlate with increasing indicators if they're good EWS
    tau_ei_h, p_ei_h = kendall_tau(ei_ratio[pre_collapse_ei], ei_h[pre_collapse_ei])
    tau_var_h, p_var_h = kendall_tau(ews['variance'][pre_collapse_ews], ews_h[pre_collapse_ews])
    tau_ac_h, p_ac_h = kendall_tau(ews['autocorrelation'][pre_collapse_ews], ews_h[pre_collapse_ews])

    print(f"\nKendall tau with control parameter h (pre-collapse):")
    print(f"  EI ratio vs h:       tau = {tau_ei_h:.4f}, p = {p_ei_h:.4e}")
    print(f"  Variance vs h:       tau = {tau_var_h:.4f}, p = {p_var_h:.4e}")
    print(f"  Autocorrelation vs h: tau = {tau_ac_h:.4f}, p = {p_ac_h:.4e}")

    # Also compute correlation between indicators
    # Need to align lengths
    min_len = min(len(ei_ratio), len(ews['variance']))
    ei_r_interp = np.interp(ews['timestamps'][:min_len],
                             ei_timestamps, ei_ratio)
    tau_ei_var, p_ei_var = kendall_tau(ei_r_interp, ews['variance'][:min_len])
    tau_ei_ac, p_ei_ac = kendall_tau(ei_r_interp, ews['autocorrelation'][:min_len])

    print(f"\nKendall tau between indicators:")
    print(f"  EI ratio vs Variance:       tau = {tau_ei_var:.4f}")
    print(f"  EI ratio vs Autocorrelation: tau = {tau_ei_ac:.4f}")

    # ---- Save data ----
    project_root = os.path.join(os.path.dirname(__file__), '..')
    data_dir = os.path.join(project_root, 'results', 'phase3', 'data')
    np.savez(os.path.join(data_dir, 'phase3_results.npz'),
             x=x_sub, h_values=h_sub, times=t_sub,
             ei_micro=ei_micro, ei_macro=ei_macro,
             ei_ratio=ei_ratio, ei_timestamps=ei_timestamps,
             ews_variance=ews['variance'],
             ews_autocorrelation=ews['autocorrelation'],
             ews_timestamps=ews['timestamps'],
             h_c=h_c, h_collapse=h_collapse)
    print(f"\nData saved to {data_dir}/phase3_results.npz")

    # ---- Plots ----
    print("\nGenerating plots...")
    plot_dir = os.path.join(project_root, 'results', 'phase3', 'plots')

    # Plot 1: Time series with collapse
    fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True)

    ax = axes[0]
    ax.plot(h_sub, x_sub, 'k-', linewidth=0.5, alpha=0.7)
    ax.axvline(h_c, color='red', linestyle='--', alpha=0.7, label=f'$h_c$ ≈ {h_c:.2f}')
    if collapse_idx is not None:
        ax.axvline(h_collapse, color='orange', linestyle=':', alpha=0.7, label=f'Collapse h={h_collapse:.2f}')
    ax.set_ylabel('Population x')
    ax.set_title('Synthetic Population Collapse — Fold Bifurcation Model')
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(ei_h, ei_ratio, 'b-', linewidth=0.8, alpha=0.8, label='EI(M)/EI(S)')
    ax.axvline(h_c, color='red', linestyle='--', alpha=0.7)
    ax.set_ylabel('EI Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    ax.plot(ews_h, ews['variance'], 'orange', linewidth=0.8, alpha=0.8, label='Variance')
    ax.axvline(h_c, color='red', linestyle='--', alpha=0.7)
    ax.set_ylabel('Variance')
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[3]
    ax.plot(ews_h, ews['autocorrelation'], 'g-', linewidth=0.8, alpha=0.8, label='Autocorrelation')
    ax.axvline(h_c, color='red', linestyle='--', alpha=0.7)
    ax.set_ylabel('Autocorrelation')
    ax.set_xlabel('Harvest Rate h')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'timeseries_ews.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot_dir}/timeseries_ews.png")

    # Plot 2: Money plot (normalized, aligned by h)
    fig, ax = plt.subplots(figsize=(10, 6))

    def normalize_01(x):
        xmin, xmax = np.nanmin(x), np.nanmax(x)
        if xmax - xmin < 1e-15:
            return np.zeros_like(x)
        return (x - xmin) / (xmax - xmin)

    # Interpolate all to common h grid
    h_common = np.linspace(h_start + 0.05, min(h_collapse if collapse_idx else h_end, h_end) - 0.05, 200)

    ei_r_common = np.interp(h_common, ei_h, ei_ratio)
    var_common = np.interp(h_common, ews_h, ews['variance'])
    ac_common = np.interp(h_common, ews_h, ews['autocorrelation'])

    ax.plot(h_common, normalize_01(ei_r_common), 'b-', linewidth=1.5, label='EI(M)/EI(S)')
    ax.plot(h_common, normalize_01(var_common), 'orange', linewidth=1.5, label='Variance')
    ax.plot(h_common, normalize_01(ac_common), 'g-', linewidth=1.5, label='Autocorrelation')
    ax.axvline(h_c, color='red', linestyle='--', linewidth=2, alpha=0.7, label=f'$h_c$ ≈ {h_c:.2f}')
    ax.set_xlabel('Harvest Rate h', fontsize=12)
    ax.set_ylabel('Normalized Indicator [0, 1]', fontsize=12)
    ax.set_title('Early Warning Signal Comparison — Fold Bifurcation Model', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'money_plot.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot_dir}/money_plot.png")

    # Plot 3: Raw EI values
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(ei_h, ei_micro, 'k-', linewidth=0.8, alpha=0.8, label='EI(S) [micro]')
    ax.plot(ei_h, ei_macro, 'b-', linewidth=0.8, alpha=0.8, label='EI(M) [macro]')
    ax.axvline(h_c, color='red', linestyle='--', alpha=0.7, label=f'$h_c$ ≈ {h_c:.2f}')
    ax.set_xlabel('Harvest Rate h')
    ax.set_ylabel('Effective Information (bits)')
    ax.set_title('Raw EI Values — Fold Bifurcation Model')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'raw_ei_values.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot_dir}/raw_ei_values.png")

    # ---- Phase Log ----
    log_path = os.path.join(project_root, 'results', 'phase3', 'log.md')
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M')

    log_content = f"""# Phase 3: Synthetic Daphnia Population Collapse

## {timestamp} — PHASE 3 EXPERIMENT
**Status**: COMPLETED
**What happened**: Simulated a fold bifurcation model (harvested population with slowly increasing h). Used SYNTHETIC data (not real Drake & Griffen 2010). Computed sliding-window micro EI (population discretized into {n_bins_micro} bins) and macro EI (rolling mean discretized into {n_bins_macro} bins). Window size = {ei_window} subsampled points.

**Parameters**:
- Model: dx/dt = r*x*(1-x/K) - h*x^2/(x^2+s^2) + sigma*dW
- r={r}, K={K_cap}, s={s}, sigma={sigma}
- h: {h_start} → {h_end} over {n_steps} steps (dt={dt})
- Subsampled every {subsample} steps → {len(x_sub)} points
- h_c ≈ {h_c:.3f}
- Collapse in timeseries at h ≈ {h_collapse:.3f}

**Key Numbers**:
- Kendall tau (EI ratio vs h): {tau_ei_h:.4f} (p={p_ei_h:.4e})
- Kendall tau (Variance vs h): {tau_var_h:.4f} (p={p_var_h:.4e})
- Kendall tau (AC vs h):       {tau_ac_h:.4f} (p={p_ac_h:.4e})
- Kendall tau (EI vs Variance): {tau_ei_var:.4f}
- Kendall tau (EI vs AC):       {tau_ei_ac:.4f}
- EI ratio range: [{ei_ratio.min():.4f}, {ei_ratio.max():.4f}]

**Interpretation**:
- Kendall tau with h measures how well each indicator tracks the approach to the bifurcation.
- Higher tau → better early warning signal (indicator increases as h approaches h_c).

## Plots
- timeseries_ews.png: 4-panel (population, EI ratio, variance, AC) vs h
- money_plot.png: Normalized overlay of all three indicators
- raw_ei_values.png: Raw EI(S) and EI(M) vs h
"""

    with open(log_path, 'w') as f:
        f.write(log_content)
    print(f"\nLog written to {log_path}")

    print(f"\n{'='*70}")
    print(f"PHASE 3 COMPLETE")
    print(f"{'='*70}")

    return {
        'tau_ei_h': tau_ei_h,
        'tau_var_h': tau_var_h,
        'tau_ac_h': tau_ac_h,
        'tau_ei_var': tau_ei_var,
        'tau_ei_ac': tau_ei_ac,
        'h_c': h_c,
    }


if __name__ == "__main__":
    results = run_phase3()
