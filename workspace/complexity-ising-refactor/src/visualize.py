"""
Visualization functions for the causal emergence EWS project.

All plots are saved as 300 DPI PNGs.
All functions accept param_name/param_symbol for correct axis labeling
across different systems (Temperature/T_c for Ising, Coupling K/K_c for Kuramoto, etc.)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_ews_comparison(temperatures, ei_ratio, variance, autocorrelation,
                        T_c, save_path, system_name="System",
                        ei_err=None, var_err=None, ac_err=None,
                        param_name="Temperature", param_symbol="T_c"):
    """
    Create a 3-panel comparison of EI ratio, variance, and autocorrelation.
    """
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    crit_label = f'${param_symbol}$ = {T_c:.3f}'

    ax = axes[0]
    if ei_err is not None:
        ax.errorbar(temperatures, ei_ratio, yerr=ei_err, fmt='o-', color='tab:blue',
                     markersize=3, capsize=2, linewidth=1)
    else:
        ax.plot(temperatures, ei_ratio, 'o-', color='tab:blue', markersize=3, linewidth=1)
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=crit_label)
    ax.set_ylabel('EI(M) / EI(S)')
    ax.legend()
    ax.set_title(f'Early Warning Signal Comparison — {system_name}')
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    if var_err is not None:
        ax.errorbar(temperatures, variance, yerr=var_err, fmt='s-', color='tab:orange',
                     markersize=3, capsize=2, linewidth=1)
    else:
        ax.plot(temperatures, variance, 's-', color='tab:orange', markersize=3, linewidth=1)
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=crit_label)
    ax.set_ylabel('Variance')
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    if ac_err is not None:
        ax.errorbar(temperatures, autocorrelation, yerr=ac_err, fmt='^-', color='tab:green',
                     markersize=3, capsize=2, linewidth=1)
    else:
        ax.plot(temperatures, autocorrelation, '^-', color='tab:green', markersize=3, linewidth=1)
    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=crit_label)
    ax.set_ylabel('Lag-1 Autocorrelation')
    ax.set_xlabel(param_name)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def plot_ei_across_scales(temperatures, ei_curves_by_blocksize, T_c, save_path,
                          system_name="System",
                          param_name="Temperature", param_symbol="T_c"):
    """
    Plot EI(M)/EI(S) for different coarse-graining block sizes.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    crit_label = f'${param_symbol}$ = {T_c:.3f}'

    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']
    for idx, (b, (ei_ratio, ei_err)) in enumerate(sorted(ei_curves_by_blocksize.items())):
        color = colors[idx % len(colors)]
        if ei_err is not None:
            ax.errorbar(temperatures, ei_ratio, yerr=ei_err, fmt='o-', color=color,
                         markersize=3, capsize=2, linewidth=1, label=f'b={b}')
        else:
            ax.plot(temperatures, ei_ratio, 'o-', color=color, markersize=3,
                     linewidth=1, label=f'b={b}')

    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=crit_label)
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5, label='EI ratio = 1')
    ax.set_xlabel(param_name)
    ax.set_ylabel('EI(M) / EI(S)')
    ax.set_title(f'EI Ratio Across Coarse-Graining Scales — {system_name}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def plot_money(temperatures, ei_ratio, variance, autocorrelation, T_c, save_path,
               system_name="System",
               param_name="Temperature", param_symbol="T_c",
               ei_err=None, var_err=None, ac_err=None):
    """
    The "money plot": all three indicators normalized to [0,1], overlaid.
    Supports optional error bars (shown as shaded bands).
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    crit_label = f'${param_symbol}$ = {T_c:.3f}'

    def normalize_01(x):
        xmin, xmax = np.nanmin(x), np.nanmax(x)
        if xmax - xmin < 1e-15:
            return np.zeros_like(x), 0.0
        return (x - xmin) / (xmax - xmin), 1.0 / (xmax - xmin)

    ei_norm, ei_scale = normalize_01(ei_ratio)
    var_norm, var_scale = normalize_01(variance)
    ac_norm, ac_scale = normalize_01(autocorrelation)

    ax.plot(temperatures, ei_norm, 'o-', color='tab:blue', markersize=4,
            linewidth=1.5, label='EI(M)/EI(S)')
    if ei_err is not None:
        ax.fill_between(temperatures, ei_norm - ei_err * ei_scale,
                         ei_norm + ei_err * ei_scale, color='tab:blue', alpha=0.15)

    ax.plot(temperatures, var_norm, 's-', color='tab:orange', markersize=4,
            linewidth=1.5, label='Variance')
    if var_err is not None:
        ax.fill_between(temperatures, var_norm - var_err * var_scale,
                         var_norm + var_err * var_scale, color='tab:orange', alpha=0.15)

    ax.plot(temperatures, ac_norm, '^-', color='tab:green', markersize=4,
            linewidth=1.5, label='Autocorrelation')
    if ac_err is not None:
        ax.fill_between(temperatures, ac_norm - ac_err * ac_scale,
                         ac_norm + ac_err * ac_scale, color='tab:green', alpha=0.15)

    ax.axvline(T_c, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=crit_label)
    ax.set_xlabel(param_name, fontsize=12)
    ax.set_ylabel('Normalized Indicator [0, 1]', fontsize=12)
    ax.set_title(f'Early Warning Signal Comparison (Normalized) — {system_name}', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def plot_raw_ei(temperatures, ei_micro, ei_macro_dict, T_c, save_path,
                system_name="System",
                param_name="Temperature", param_symbol="T_c"):
    """
    Plot raw EI(S) and EI(M) values (not ratios) across temperature.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    crit_label = f'${param_symbol}$ = {T_c:.3f}'

    ax.plot(temperatures, ei_micro, 'k-o', markersize=3, linewidth=1.5, label='EI(S) [micro]')

    colors = ['tab:blue', 'tab:orange', 'tab:green']
    for idx, (b, ei_m) in enumerate(sorted(ei_macro_dict.items())):
        ax.plot(temperatures, ei_m, 'o-', color=colors[idx % len(colors)],
                markersize=3, linewidth=1, label=f'EI(M, b={b})')

    ax.axvline(T_c, color='red', linestyle='--', alpha=0.7, label=crit_label)
    ax.set_xlabel(param_name)
    ax.set_ylabel('Effective Information (bits)')
    ax.set_title(f'Raw EI Values — {system_name}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")
