"""
Wolff Algorithm Validation & Mini EI Experiment

Validates the Wolff single-cluster implementation against Metropolis-Hastings:
1. Magnetization comparison at T_c (histograms should overlap)
2. Autocorrelation time comparison (Wolff should be much shorter)
3. Mini EI experiment at 5 temperatures comparing EI(M)/EI(S) between algorithms

Produces: results/phase1/plots/wolff_validation.png
"""

import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ising import simulate_ising, simulate_ising_wolff
from src.coarse_grain import coarsegrain_timeseries, config_to_patch_states
from src.ei_compute import estimate_transition_matrix, effective_information, compute_ei_equalized


# =========================================================================
# Helper: Autocorrelation function
# =========================================================================
def compute_autocorrelation(m, max_lag=None):
    """
    Compute normalized autocorrelation function C(tau)/C(0).

    Parameters
    ----------
    m : ndarray of shape (N,)
        Magnetization time series.
    max_lag : int or None
        Maximum lag to compute. Defaults to N//4.

    Returns
    -------
    lags : ndarray of int
        Lag values.
    acf : ndarray of float
        Normalized autocorrelation C(tau)/C(0).
    """
    m = m - m.mean()
    N = len(m)
    if max_lag is None:
        max_lag = min(N // 4, 500)

    # C(0) = variance
    c0 = np.mean(m * m)
    if c0 < 1e-15:
        return np.arange(max_lag + 1), np.zeros(max_lag + 1)

    acf = np.empty(max_lag + 1)
    for tau in range(max_lag + 1):
        acf[tau] = np.mean(m[:N - tau] * m[tau:]) / c0

    return np.arange(max_lag + 1), acf


def find_tau_int(acf):
    """
    Find integrated autocorrelation time: first lag where acf < 1/e.
    If never crosses 1/e, return max_lag.
    """
    threshold = 1.0 / np.e
    for tau in range(len(acf)):
        if acf[tau] < threshold:
            return tau
    return len(acf) - 1


# =========================================================================
# MAIN VALIDATION
# =========================================================================
def run_wolff_validation():
    print("=" * 70)
    print("WOLFF ALGORITHM VALIDATION & MINI EI EXPERIMENT")
    print("=" * 70)

    total_start = time.time()

    # Parameters
    L = 24
    T_c = 2.269
    block_size = 4
    patch_size = 2
    min_obs = 5

    project_root = os.path.join(os.path.dirname(__file__), '..')
    plot_dir = os.path.join(project_root, 'results', 'phase1', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    # ==================================================================
    # PART 1: Magnetization comparison at T_c
    # ==================================================================
    print("\n" + "=" * 70)
    print("PART 1: Magnetization comparison at T_c")
    print("=" * 70)

    # Use long runs for good statistics
    n_steps_mag = 2000
    n_equilib_mag = 5000

    print(f"  L={L}, T=T_c={T_c}, n_steps={n_steps_mag}, n_equilib={n_equilib_mag}")

    t0 = time.time()
    print("  Running Metropolis...", flush=True)
    _, mags_metro = simulate_ising(L, T_c, n_steps_mag, n_equilib_mag, seed=42)
    t_metro = time.time() - t0
    print(f"    Done in {t_metro:.1f}s. Mean |m| = {mags_metro.mean():.4f} +/- {mags_metro.std():.4f}")

    t0 = time.time()
    print("  Running Wolff...", flush=True)
    _, mags_wolff = simulate_ising_wolff(L, T_c, n_steps_mag, n_equilib_mag, seed=42)
    t_wolff = time.time() - t0
    print(f"    Done in {t_wolff:.1f}s. Mean |m| = {mags_wolff.mean():.4f} +/- {mags_wolff.std():.4f}")

    # Statistical comparison
    from scipy import stats
    ks_stat, ks_pval = stats.ks_2samp(mags_metro, mags_wolff)
    print(f"  KS test: statistic={ks_stat:.4f}, p-value={ks_pval:.4f}")
    print(f"  Distributions {'consistent' if ks_pval > 0.01 else 'differ'} at 1% level")

    # ==================================================================
    # PART 2: Autocorrelation time comparison at T_c
    # ==================================================================
    print("\n" + "=" * 70)
    print("PART 2: Autocorrelation time comparison at T_c")
    print("=" * 70)

    max_lag = 200  # plenty for both

    print("  Computing Metropolis autocorrelation...")
    lags_m, acf_metro = compute_autocorrelation(mags_metro, max_lag=max_lag)
    tau_metro = find_tau_int(acf_metro)

    print("  Computing Wolff autocorrelation...")
    lags_w, acf_wolff = compute_autocorrelation(mags_wolff, max_lag=max_lag)
    tau_wolff = find_tau_int(acf_wolff)

    print(f"  Metropolis tau_int (1/e crossing): {tau_metro} steps")
    print(f"  Wolff tau_int (1/e crossing):      {tau_wolff} steps")
    print(f"  Speedup factor: {tau_metro / max(tau_wolff, 1):.1f}x")

    # Note: Metropolis samples every 10 sweeps, so "steps" are 10-sweep units
    # Wolff samples every cluster flip. For fair comparison at T_c with L=24:
    # Metropolis: each step = 10 sweeps = 10*576 = 5760 spin updates
    # Wolff: each step = 1 cluster flip ~ N*p_add / (1-p_add) spins at T_c
    print(f"\n  NOTE: Metropolis 'step' = 10 sweeps = {10*L*L} spin flip attempts")
    print(f"        Wolff 'step' = 1 cluster flip (variable size)")

    # ==================================================================
    # PART 3: Mini EI experiment
    # ==================================================================
    print("\n" + "=" * 70)
    print("PART 3: Mini EI experiment (5 temperatures, 5 seeds each)")
    print("=" * 70)

    temperatures = np.array([1.8, 2.0, 2.15, 2.269, 2.5])
    n_seeds = 5
    n_steps_ei = 2000
    n_equilib_ei = 5000
    n_temps = len(temperatures)

    print(f"  L={L}, block_size={block_size}, patch_size={patch_size}, min_obs={min_obs}")
    print(f"  n_steps={n_steps_ei}, n_equilib={n_equilib_ei}, n_seeds={n_seeds}")

    # Storage
    ei_ratio_metro = np.zeros((n_seeds, n_temps))
    ei_ratio_wolff = np.zeros((n_seeds, n_temps))
    ei_micro_metro = np.zeros((n_seeds, n_temps))
    ei_macro_metro = np.zeros((n_seeds, n_temps))
    ei_micro_wolff = np.zeros((n_seeds, n_temps))
    ei_macro_wolff = np.zeros((n_seeds, n_temps))

    for idx, T in enumerate(temperatures):
        t0 = time.time()
        print(f"\n  --- T = {T:.3f} ({idx+1}/{n_temps}) ---", flush=True)

        for s in range(n_seeds):
            seed_base = 1000 * s + idx

            # --- Metropolis ---
            configs_m, _ = simulate_ising(L, T, n_steps_ei, n_equilib_ei, seed=seed_base)
            coarse_m = coarsegrain_timeseries(configs_m, block_size)
            rng_m = np.random.RandomState(seed_base + 77777)
            ei_s_m, ei_m_m, *_ = compute_ei_equalized(configs_m, coarse_m, patch_size, min_obs, rng_m)
            ei_micro_metro[s, idx] = ei_s_m
            ei_macro_metro[s, idx] = ei_m_m
            ei_ratio_metro[s, idx] = ei_m_m / ei_s_m if ei_s_m > 1e-10 else np.nan

            # --- Wolff ---
            configs_w, _ = simulate_ising_wolff(L, T, n_steps_ei, n_equilib_ei, seed=seed_base)
            coarse_w = coarsegrain_timeseries(configs_w, block_size)
            rng_w = np.random.RandomState(seed_base + 77777)
            ei_s_w, ei_m_w, *_ = compute_ei_equalized(configs_w, coarse_w, patch_size, min_obs, rng_w)
            ei_micro_wolff[s, idx] = ei_s_w
            ei_macro_wolff[s, idx] = ei_m_w
            ei_ratio_wolff[s, idx] = ei_m_w / ei_s_w if ei_s_w > 1e-10 else np.nan

        elapsed = time.time() - t0
        metro_mean = np.nanmean(ei_ratio_metro[:, idx])
        wolff_mean = np.nanmean(ei_ratio_wolff[:, idx])
        print(f"    Metro EI(M)/EI(S) = {metro_mean:.4f} +/- {np.nanstd(ei_ratio_metro[:, idx]):.4f}")
        print(f"    Wolff EI(M)/EI(S) = {wolff_mean:.4f} +/- {np.nanstd(ei_ratio_wolff[:, idx]):.4f}")
        print(f"    Time: {elapsed:.1f}s")

    # ==================================================================
    # SUMMARY TABLE
    # ==================================================================
    print("\n" + "=" * 70)
    print("SUMMARY: EI(M)/EI(S) comparison")
    print("=" * 70)
    print(f"  {'T':>6s}  {'Metro mean':>12s}  {'Metro SE':>10s}  {'Wolff mean':>12s}  {'Wolff SE':>10s}  {'Diff':>8s}")
    print("  " + "-" * 66)
    for idx, T in enumerate(temperatures):
        m_mean = np.nanmean(ei_ratio_metro[:, idx])
        m_se = np.nanstd(ei_ratio_metro[:, idx]) / np.sqrt(n_seeds)
        w_mean = np.nanmean(ei_ratio_wolff[:, idx])
        w_se = np.nanstd(ei_ratio_wolff[:, idx]) / np.sqrt(n_seeds)
        diff = w_mean - m_mean
        print(f"  {T:6.3f}  {m_mean:12.4f}  {m_se:10.4f}  {w_mean:12.4f}  {w_se:10.4f}  {diff:+8.4f}")

    # ==================================================================
    # PLOT
    # ==================================================================
    print("\n\nGenerating validation plot...")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    # --- Panel 1: Magnetization histograms at T_c ---
    ax = axes[0]
    bins = np.linspace(0, 1, 40)
    ax.hist(mags_metro, bins=bins, alpha=0.6, density=True, color='tab:orange',
            edgecolor='white', label=f'Metropolis (mean={mags_metro.mean():.3f})')
    ax.hist(mags_wolff, bins=bins, alpha=0.6, density=True, color='tab:blue',
            edgecolor='white', label=f'Wolff (mean={mags_wolff.mean():.3f})')
    ax.set_xlabel('|Magnetization| per spin')
    ax.set_ylabel('Probability density')
    ax.set_title(f'Magnetization at $T_c$ = {T_c:.3f}\nKS p={ks_pval:.3f}')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # --- Panel 2: Autocorrelation functions ---
    ax = axes[1]
    ax.plot(lags_m, acf_metro, '-', color='tab:orange', linewidth=1.5,
            label=f'Metropolis ($\\tau$ = {tau_metro})')
    ax.plot(lags_w, acf_wolff, '-', color='tab:blue', linewidth=1.5,
            label=f'Wolff ($\\tau$ = {tau_wolff})')
    ax.axhline(1.0 / np.e, color='gray', linestyle=':', alpha=0.7, label='1/e threshold')
    ax.set_xlabel('Lag (sampling steps)')
    ax.set_ylabel('Autocorrelation C($\\tau$)/C(0)')
    ax.set_title(f'Autocorrelation at $T_c$\nWolff speedup: {tau_metro / max(tau_wolff, 1):.0f}x')
    ax.set_xlim(0, max_lag)
    ax.set_ylim(-0.2, 1.05)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # --- Panel 3: EI ratio comparison ---
    ax = axes[2]
    metro_mean_ratio = np.nanmean(ei_ratio_metro, axis=0)
    metro_se_ratio = np.nanstd(ei_ratio_metro, axis=0) / np.sqrt(n_seeds)
    wolff_mean_ratio = np.nanmean(ei_ratio_wolff, axis=0)
    wolff_se_ratio = np.nanstd(ei_ratio_wolff, axis=0) / np.sqrt(n_seeds)

    x_offset = 0.015  # slight horizontal offset for readability
    ax.errorbar(temperatures - x_offset, metro_mean_ratio, yerr=metro_se_ratio,
                fmt='s-', color='tab:orange', markersize=6, capsize=4, linewidth=1.5,
                label='Metropolis')
    ax.errorbar(temperatures + x_offset, wolff_mean_ratio, yerr=wolff_se_ratio,
                fmt='o-', color='tab:blue', markersize=6, capsize=4, linewidth=1.5,
                label='Wolff')
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, linewidth=1.5, label=f'$T_c$')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Temperature')
    ax.set_ylabel('EI(M) / EI(S)')
    ax.set_title('EI Ratio: Metropolis vs Wolff\n(equalized transitions, min_obs=5)')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.suptitle('Wolff Single-Cluster Algorithm Validation', fontsize=14, y=1.02)
    plt.tight_layout()
    save_path = os.path.join(plot_dir, 'wolff_validation.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")

    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print(f"WOLFF VALIDATION COMPLETE — Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_wolff_validation()
