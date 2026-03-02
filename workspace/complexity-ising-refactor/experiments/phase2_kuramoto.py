"""
Phase 2: Kuramoto Model Experiment

Tests whether EI-based early warning signals generalize from a lattice system
(Ising) to a non-lattice, continuous-state system (Kuramoto oscillators).

Design decisions:
- Micro EI(S): Pick 3 oscillators, discretize each phase into 8 bins.
  Joint state space: 8^3 = 512 states. This matches the micro state space
  size from Phase 1.
- Macro EI(M): Discretize the order parameter r into 8 bins.
  State space: 8 states.
- Use multiple triplets of oscillators to pool transition statistics for micro EI.
"""

import sys
import os
import time
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kuramoto import simulate_kuramoto
from src.ei_compute import estimate_transition_matrix, effective_information
from src.ews_standard import compute_ews
from src.analysis import kendall_tau, detect_threshold_crossing, compute_lead_time
from src.visualize import plot_ews_comparison, plot_money


def discretize_phases(phases, n_bins):
    """
    Discretize phases in [0, 2*pi) into integer bins.

    Parameters
    ----------
    phases : ndarray
        Phase values in [0, 2*pi).
    n_bins : int
        Number of bins.

    Returns
    -------
    bins : ndarray of int
        Bin indices in [0, n_bins-1].
    """
    return np.floor(phases / (2 * np.pi) * n_bins).astype(np.int32).clip(0, n_bins - 1)


def compute_micro_ei(phases, n_bins=8, n_triplets=20, seed=42):
    """
    Compute micro EI from oscillator phase triplets.

    Pick n_triplets random triplets of oscillators. For each triplet, the
    joint state is the concatenation of their discretized phases (8^3 = 512 states).
    Pool transition data across all triplets.

    Parameters
    ----------
    phases : ndarray of shape (n_steps, N)
        Phase time series.
    n_bins : int
        Number of bins per oscillator.
    n_triplets : int
        Number of oscillator triplets to sample.
    seed : int
        Random seed for triplet selection.

    Returns
    -------
    ei : float
        Micro Effective Information in bits.
    """
    n_steps, N = phases.shape
    n_states = n_bins ** 3
    rng = np.random.RandomState(seed)

    # Discretize all phases
    binned = discretize_phases(phases, n_bins)

    # Select random triplets
    triplets = []
    for _ in range(n_triplets):
        triplet = rng.choice(N, size=3, replace=False)
        triplets.append(triplet)

    # Collect transitions
    all_states_t = []
    all_states_t1 = []

    for triplet in triplets:
        i, j, k = triplet
        # Encode joint state as: bin_i * n_bins^2 + bin_j * n_bins + bin_k
        joint = binned[:, i] * n_bins * n_bins + binned[:, j] * n_bins + binned[:, k]
        all_states_t.append(joint[:-1])
        all_states_t1.append(joint[1:])

    states_t = np.concatenate(all_states_t)
    states_t1 = np.concatenate(all_states_t1)

    T, row_counts = estimate_transition_matrix(states_t, states_t1, n_states)
    ei = effective_information(T, row_counts, min_observations=5)
    return ei


def compute_macro_ei(order_param, n_bins=8):
    """
    Compute macro EI from the order parameter time series.

    Parameters
    ----------
    order_param : ndarray of shape (n_steps,)
        Kuramoto order parameter r(t) in [0, 1].
    n_bins : int
        Number of bins.

    Returns
    -------
    ei : float
        Macro Effective Information in bits.
    """
    # Discretize order parameter into bins
    binned = np.floor(order_param * n_bins).astype(np.int32).clip(0, n_bins - 1)

    states_t = binned[:-1]
    states_t1 = binned[1:]

    T, row_counts = estimate_transition_matrix(states_t, states_t1, n_bins)
    ei = effective_information(T, row_counts, min_observations=5)
    return ei


def run_phase2():
    """Execute the Phase 2 Kuramoto model experiment."""
    print("=" * 70)
    print("PHASE 2: KURAMOTO MODEL EXPERIMENT")
    print("=" * 70)

    # Parameters
    N = 50
    coupling_values = np.arange(0.5, 3.01, 0.1)
    dt = 0.05
    n_steps = 10000
    n_equilib = 5000
    n_phase_bins = 8
    n_triplets = 20
    seed = 42
    K_c = 2.0 / (np.pi * (1.0 / np.sqrt(2 * np.pi)))  # ≈ 1.596 for N(0,1)

    # Fix natural frequencies across all coupling values
    rng = np.random.RandomState(seed)
    omega = rng.randn(N)

    n_K = len(coupling_values)
    print(f"\nParameters:")
    print(f"  N = {N}, dt = {dt}, n_steps = {n_steps}, n_equilib = {n_equilib}")
    print(f"  Coupling range: {coupling_values[0]:.1f} to {coupling_values[-1]:.1f}, {n_K} points")
    print(f"  Phase bins: {n_phase_bins}, Triplets: {n_triplets}")
    print(f"  K_c ≈ {K_c:.3f}")

    # Storage
    ei_micro = np.zeros(n_K)
    ei_macro = np.zeros(n_K)
    r_means = np.zeros(n_K)
    r_vars = np.zeros(n_K)
    r_acs = np.zeros(n_K)

    total_start = time.time()

    for idx, K in enumerate(coupling_values):
        t0 = time.time()
        print(f"\n--- K = {K:.2f} ({idx+1}/{n_K}) ---")

        # Simulate
        phases, r = simulate_kuramoto(N, K, omega, dt, n_steps, n_equilib,
                                       seed=seed + idx)
        r_means[idx] = r.mean()
        r_vars[idx] = r.var()

        # Lag-1 autocorrelation of order parameter
        if len(r) > 1:
            x = r[:-1]
            y = r[1:]
            mx, my = x.mean(), y.mean()
            sx, sy = x.std(), y.std()
            if sx > 0 and sy > 0:
                r_acs[idx] = np.mean((x - mx) * (y - my)) / (sx * sy)
            else:
                r_acs[idx] = 0.0

        # Micro EI
        ei_micro[idx] = compute_micro_ei(phases, n_bins=n_phase_bins,
                                          n_triplets=n_triplets, seed=seed)

        # Macro EI
        ei_macro[idx] = compute_macro_ei(r, n_bins=n_phase_bins)

        elapsed = time.time() - t0
        ratio = ei_macro[idx] / ei_micro[idx] if ei_micro[idx] > 0 else float('nan')
        print(f"  r = {r_means[idx]:.4f}, Var(r) = {r_vars[idx]:.6f}, AC = {r_acs[idx]:.4f}")
        print(f"  EI(S) = {ei_micro[idx]:.4f}, EI(M) = {ei_macro[idx]:.4f}, ratio = {ratio:.4f}")
        print(f"  Time: {elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    print(f"\nTotal simulation time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Save raw data
    project_root = os.path.join(os.path.dirname(__file__), '..')
    data_dir = os.path.join(project_root, 'results', 'phase2', 'data')
    np.savez(os.path.join(data_dir, 'phase2_results.npz'),
             coupling_values=coupling_values,
             ei_micro=ei_micro,
             ei_macro=ei_macro,
             r_means=r_means,
             r_vars=r_vars,
             r_acs=r_acs,
             K_c=K_c, N=N, n_steps=n_steps, n_equilib=n_equilib)
    print(f"\nData saved to {data_dir}/phase2_results.npz")

    # ---- Analysis ----
    print("\n" + "=" * 70)
    print("PHASE 2 ANALYSIS")
    print("=" * 70)

    ei_ratio = ei_macro / np.where(ei_micro > 0, ei_micro, 1e-10)

    # Kendall tau correlations
    tau_ei_var, p_ei_var = kendall_tau(ei_ratio, r_vars)
    tau_ei_ac, p_ei_ac = kendall_tau(ei_ratio, r_acs)
    tau_var_ac, p_var_ac = kendall_tau(r_vars, r_acs)

    print(f"\nKendall tau correlations:")
    print(f"  EI ratio vs Variance:       tau = {tau_ei_var:.4f}, p = {p_ei_var:.4e}")
    print(f"  EI ratio vs Autocorrelation: tau = {tau_ei_ac:.4f}, p = {p_ei_ac:.4e}")
    print(f"  Variance vs Autocorrelation: tau = {tau_var_ac:.4f}, p = {p_var_ac:.4e}")

    # Threshold detection (baseline: K < 1.0)
    baseline_mask = coupling_values < 1.0
    T_trigger_ei, thresh_ei = detect_threshold_crossing(coupling_values, ei_ratio, baseline_mask)
    T_trigger_var, thresh_var = detect_threshold_crossing(coupling_values, r_vars, baseline_mask)
    T_trigger_ac, thresh_ac = detect_threshold_crossing(coupling_values, r_acs, baseline_mask)

    lead_ei = compute_lead_time(T_trigger_ei, K_c)
    lead_var = compute_lead_time(T_trigger_var, K_c)
    lead_ac = compute_lead_time(T_trigger_ac, K_c)

    print(f"\nThreshold crossing (2σ above baseline):")
    print(f"  EI ratio:       K_trigger = {T_trigger_ei}, lead time = {lead_ei}")
    print(f"  Variance:       K_trigger = {T_trigger_var}, lead time = {lead_var}")
    print(f"  Autocorrelation: K_trigger = {T_trigger_ac}, lead time = {lead_ac}")

    # Causal emergence?
    emergence_count = np.sum(ei_macro > ei_micro)
    print(f"\nCausal emergence (EI(M) > EI(S)): {emergence_count}/{n_K} coupling values")
    for i in range(n_K):
        if ei_macro[i] > ei_micro[i]:
            print(f"  K={coupling_values[i]:.2f}: EI(M)={ei_macro[i]:.4f} > EI(S)={ei_micro[i]:.4f}")

    # ---- Plots ----
    print("\nGenerating plots...")
    plot_dir = os.path.join(project_root, 'results', 'phase2', 'plots')

    # Three-panel comparison
    plot_ews_comparison(coupling_values, ei_ratio, r_vars, r_acs, K_c,
                        os.path.join(plot_dir, 'ews_comparison.png'),
                        system_name='Kuramoto Model',
                        param_name='Coupling Strength K', param_symbol='K_c')

    # Money plot
    plot_money(coupling_values, ei_ratio, r_vars, r_acs, K_c,
               os.path.join(plot_dir, 'money_plot.png'),
               system_name='Kuramoto Model',
               param_name='Coupling Strength K', param_symbol='K_c')

    # Raw EI plot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(coupling_values, ei_micro, 'k-o', markersize=3, linewidth=1.5, label='EI(S) [micro]')
    ax.plot(coupling_values, ei_macro, 'b-o', markersize=3, linewidth=1.5, label='EI(M) [macro]')
    ax.axvline(K_c, color='red', linestyle='--', alpha=0.7, label=f'$K_c$ = {K_c:.3f}')
    ax.set_xlabel('Coupling Strength K')
    ax.set_ylabel('Effective Information (bits)')
    ax.set_title('Raw EI Values — Kuramoto Model')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'raw_ei_values.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {plot_dir}/raw_ei_values.png")

    # ---- Phase Log ----
    log_path = os.path.join(project_root, 'results', 'phase2', 'log.md')
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M')

    log_content = f"""# Phase 2: Kuramoto Model Results

## {timestamp} — PHASE 2 EXPERIMENT
**Status**: COMPLETED
**What happened**: Ran Kuramoto model (N={N} oscillators) across {n_K} coupling values from {coupling_values[0]:.1f} to {coupling_values[-1]:.1f}. Computed micro EI (3-oscillator triplets, {n_phase_bins}^3={n_phase_bins**3} states, {n_triplets} triplets) and macro EI (order parameter discretized into {n_phase_bins} bins). Compared against variance and lag-1 autocorrelation of order parameter.

**Parameters**:
- N = {N}, dt = {dt}, n_steps = {n_steps}, n_equilib = {n_equilib}
- K_c ≈ {K_c:.3f}
- Noise: σ = 0.1
- Total simulation time: {total_elapsed:.1f}s

**Key Numbers**:
- Kendall tau (EI ratio vs Variance): {tau_ei_var:.4f} (p={p_ei_var:.4e})
- Kendall tau (EI ratio vs Autocorrelation): {tau_ei_ac:.4f} (p={p_ei_ac:.4e})
- Kendall tau (Variance vs Autocorrelation): {tau_var_ac:.4f} (p={p_var_ac:.4e})
- EI ratio trigger: K={T_trigger_ei} (lead={lead_ei})
- Variance trigger: K={T_trigger_var} (lead={lead_var})
- AC trigger: K={T_trigger_ac} (lead={lead_ac})
- Causal emergence: {emergence_count}/{n_K} coupling values

**Decision gate assessment**:
"""
    # Assess gate for Phase 3
    ei_ratio_range = ei_ratio.max() - ei_ratio.min()
    ei_ratio_mean = ei_ratio.mean()
    relative_variation = ei_ratio_range / (ei_ratio_mean + 1e-10)

    adds_info = abs(tau_ei_ac) < 0.95  # EI ratio not redundant with AC

    if adds_info and relative_variation > 0.1:
        log_content += f"- EI ratio shows meaningful variation (range/mean = {relative_variation:.4f}) and differs from AC (|tau| = {abs(tau_ei_ac):.4f} < 0.95).\n"
        log_content += "- **VERDICT: PROCEED to Phase 3.**\n"
        proceed = True
    else:
        log_content += f"- EI ratio variation: {relative_variation:.4f}, tau with AC: {tau_ei_ac:.4f}\n"
        log_content += "- **VERDICT: EI does not add sufficient information. Stopping.**\n"
        proceed = False

    log_content += f"""
## Plots generated
- ews_comparison.png: 3-panel comparison
- money_plot.png: Normalized overlay
- raw_ei_values.png: Raw EI(S) and EI(M)
"""

    with open(log_path, 'w') as f:
        f.write(log_content)
    print(f"\nLog written to {log_path}")

    print(f"\n{'='*70}")
    print(f"PHASE 2 COMPLETE")
    print(f"{'='*70}")

    return proceed, {
        'coupling_values': coupling_values,
        'ei_micro': ei_micro,
        'ei_macro': ei_macro,
        'ei_ratio': ei_ratio,
        'r_vars': r_vars,
        'r_acs': r_acs,
        'tau_ei_ac': tau_ei_ac,
        'K_c': K_c,
    }


if __name__ == "__main__":
    proceed, results = run_phase2()
    if proceed:
        print("\n>>> DECISION: PROCEED TO PHASE 3 <<<")
    else:
        print("\n>>> DECISION: STOP — Check Phase 2 log for details <<<")
