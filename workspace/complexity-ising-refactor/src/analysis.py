"""
Analysis and comparison functions for early warning signals.

Includes Kendall tau correlation, early warning detection,
statistical comparisons between EI-based and standard indicators,
and patch autocorrelation for equilibrium detection.
"""

import numpy as np
from scipy import stats


def kendall_tau(x, y):
    """
    Compute Kendall tau rank correlation between two arrays.

    Parameters
    ----------
    x, y : ndarray
        Arrays of the same length.

    Returns
    -------
    tau : float
        Kendall tau correlation coefficient.
    pvalue : float
        Two-sided p-value.
    """
    tau, p = stats.kendalltau(x, y)
    return tau, p


def detect_threshold_crossing(temperatures, indicator, baseline_mask, n_sigma=2):
    """
    Find the first temperature at which an indicator exceeds
    n_sigma standard deviations above its baseline.

    Parameters
    ----------
    temperatures : ndarray
        Temperature values.
    indicator : ndarray
        Indicator values at each temperature.
    baseline_mask : ndarray of bool
        Boolean mask indicating which temperatures are "baseline" (far from transition).
    n_sigma : float
        Number of standard deviations above baseline for threshold.

    Returns
    -------
    T_trigger : float or None
        Temperature at which threshold is first exceeded.
        None if never exceeded.
    threshold : float
        The threshold value used.
    """
    baseline_vals = indicator[baseline_mask]
    baseline_mean = baseline_vals.mean()
    baseline_std = baseline_vals.std()

    threshold = baseline_mean + n_sigma * baseline_std

    # Find first crossing
    for i, (T, val) in enumerate(zip(temperatures, indicator)):
        if not baseline_mask[i] and val > threshold:
            return T, threshold

    return None, threshold


def compute_lead_time(T_trigger, T_c):
    """
    Compute how far before the critical point an indicator triggers.

    Parameters
    ----------
    T_trigger : float or None
        Temperature at which indicator triggered.
    T_c : float
        Known critical temperature.

    Returns
    -------
    lead : float or None
        T_c - T_trigger (positive means trigger came before T_c).
        None if indicator never triggered.
    """
    if T_trigger is None:
        return None
    return T_c - T_trigger


def compute_patch_autocorrelation(configs, patch_size):
    """Compute fraction of patches unchanged between consecutive steps.

    Useful for detecting equilibration: high autocorrelation means the
    system is "frozen" (ordered phase or insufficient dynamics).

    Parameters
    ----------
    configs : ndarray of shape (N, L, L) with values +1/-1
        Time series of spin configurations.
    patch_size : int
        Side length of each patch.

    Returns
    -------
    autocorrelation : float
        Mean fraction of patches unchanged between consecutive timesteps.
    """
    from src.coarse_grain import config_to_patch_states
    states, n_states, n_patches = config_to_patch_states(configs, patch_size)
    N = states.shape[0]
    if N < 2:
        return 0.0
    same = (states[:-1] == states[1:]).astype(np.float64)
    return same.mean()
