"""
Effective Information (EI) computation module.

EI measures the mutual information between cause and effect when the
intervention distribution is uniform (maximum entropy). It quantifies
how much causal structure exists in a transition matrix.

EI = H(effect repertoire) - mean row entropy of T
   = H(q) - (1/n) * sum_i H(T[i,:])

where q_j = (1/n) * sum_i T[i,j] is the column-average of T.

IMPORTANT: This module supports two EI computation modes:
1. "full" — standard EI over the full transition matrix (including unvisited states)
2. "observed" — EI computed only over states that were actually visited as sources.
   This avoids the bias where Laplace smoothing on unvisited rows inflates noise
   entropy and artificially suppresses EI for large state spaces.
"""

import numpy as np


def shannon_entropy(p):
    """
    Compute Shannon entropy in bits.

    Parameters
    ----------
    p : ndarray
        Probability distribution (must sum to ~1, entries >= 0).

    Returns
    -------
    H : float
        Shannon entropy in bits (using log base 2).
    """
    p = p[p > 0]
    return -np.sum(p * np.log2(p))


def estimate_transition_matrix(states_t, states_t1, n_states, alpha=None):
    """
    Estimate a transition probability matrix from observed state transitions.

    Parameters
    ----------
    states_t : ndarray of int, shape (N,)
        State labels at time t (values in 0..n_states-1).
    states_t1 : ndarray of int, shape (N,)
        State labels at time t+1 (values in 0..n_states-1).
    n_states : int
        Number of possible states.
    alpha : float or None
        Smoothing constant per cell. If None, uses 1/n_states (scaled Laplace).
        This ensures total pseudo-counts are constant (=1 per row) regardless
        of state space size, avoiding the bias where large state spaces get
        disproportionately smoothed.

    Returns
    -------
    T : ndarray of shape (n_states, n_states)
        Transition probability matrix. T[i,j] = P(state_{t+1}=j | state_t=i).
    row_counts : ndarray of shape (n_states,)
        Number of real (non-smoothed) observations per source state.
    """
    if alpha is None:
        alpha = 1.0 / n_states

    # Vectorized transition counting
    flat_idx = states_t.astype(np.int64) * n_states + states_t1.astype(np.int64)
    counts_flat = np.bincount(flat_idx, minlength=n_states * n_states)
    counts = counts_flat.reshape(n_states, n_states).astype(np.float64)

    # Track real observation counts per row before smoothing
    row_counts = counts.sum(axis=1)

    # Add smoothing
    counts += alpha

    # Normalize rows
    row_sums = counts.sum(axis=1, keepdims=True)
    T = counts / row_sums

    return T, row_counts


def effective_information(T, row_counts=None, min_observations=0):
    """
    Compute Effective Information from a transition probability matrix.

    EI = H(effect repertoire) - mean row entropy
    where effect repertoire q_j = (1/n_eff) * sum_{visited i} T[i,j]

    Parameters
    ----------
    T : ndarray of shape (n_states, n_states)
        Row-stochastic transition probability matrix.
    row_counts : ndarray of shape (n_states,) or None
        Number of real observations per source state. If provided,
        only rows with >= min_observations real transitions are included.
    min_observations : int
        Minimum number of real observations for a row to be included
        in the EI calculation. Default 0 includes all rows (standard EI).
        Setting this > 0 avoids bias from smoothing-dominated rows.

    Returns
    -------
    ei : float
        Effective Information in bits. Always non-negative.
    """
    n_states = T.shape[0]

    if row_counts is not None and min_observations > 0:
        # Only include well-observed rows
        mask = row_counts >= min_observations
        n_eff = mask.sum()
        if n_eff == 0:
            return 0.0
        T_eff = T[mask]
    else:
        T_eff = T
        n_eff = n_states

    # Effect repertoire: column average over included rows
    q = T_eff.mean(axis=0)

    # Entropy of effect repertoire
    H_effect = shannon_entropy(q)

    # Mean row entropy over included rows
    H_noise = 0.0
    for i in range(T_eff.shape[0]):
        H_noise += shannon_entropy(T_eff[i, :])
    H_noise /= T_eff.shape[0]

    ei = H_effect - H_noise

    # EI should be non-negative
    if ei < -1e-10:
        raise ValueError(f"EI is negative ({ei:.6f}), this is a bug!")
    ei = max(0.0, ei)

    return ei


def compute_ei_equalized(configs_raw, configs_coarse, patch_size, min_obs, rng):
    """
    Compute EI for micro and macro with EQUALIZED transition counts.

    The macro scale has fewer patches (smaller coarse grid), so fewer transitions.
    We subsample the micro transitions to match the macro count exactly.

    Parameters
    ----------
    configs_raw : ndarray of shape (N, L, L)
        Raw (micro-scale) spin configurations.
    configs_coarse : ndarray of shape (N, L_coarse, L_coarse)
        Coarse-grained spin configurations.
    patch_size : int
        Side length of non-overlapping patches used to define states.
    min_obs : int
        Minimum number of real observations for a row to be included
        in the EI calculation.
    rng : np.random.RandomState
        Random number generator for subsampling.

    Returns
    -------
    ei_micro : float
        Effective Information at the micro scale.
    ei_macro : float
        Effective Information at the macro scale.
    n_transitions_used : int
        Number of transitions used (equal to macro transition count).
    n_rows_micro : int
        Number of micro transition-matrix rows passing the min_obs filter.
    n_rows_macro : int
        Number of macro transition-matrix rows passing the min_obs filter.
    """
    from src.coarse_grain import config_to_patch_states

    # Extract patch states
    micro_states, n_states, n_micro_patches = config_to_patch_states(configs_raw, patch_size)
    macro_states, _, n_macro_patches = config_to_patch_states(configs_coarse, patch_size)

    # Build transition arrays
    micro_t = micro_states[:-1].ravel()
    micro_t1 = micro_states[1:].ravel()
    macro_t = macro_states[:-1].ravel()
    macro_t1 = macro_states[1:].ravel()

    n_macro_transitions = len(macro_t)
    n_micro_transitions = len(micro_t)

    # Subsample micro to match macro count
    if n_micro_transitions > n_macro_transitions:
        idx = rng.choice(n_micro_transitions, size=n_macro_transitions, replace=False)
        micro_t_sub = micro_t[idx]
        micro_t1_sub = micro_t1[idx]
    else:
        micro_t_sub = micro_t
        micro_t1_sub = micro_t1

    # Compute transition matrices
    T_micro, rc_micro = estimate_transition_matrix(micro_t_sub, micro_t1_sub, n_states)
    T_macro, rc_macro = estimate_transition_matrix(macro_t, macro_t1, n_states)

    # Count rows passing filter
    n_rows_micro = np.sum(rc_micro >= min_obs) if min_obs > 0 else n_states
    n_rows_macro = np.sum(rc_macro >= min_obs) if min_obs > 0 else n_states

    # Compute EI
    ei_micro = effective_information(T_micro, rc_micro, min_observations=min_obs)
    ei_macro = effective_information(T_macro, rc_macro, min_observations=min_obs)

    return ei_micro, ei_macro, n_macro_transitions, int(n_rows_micro), int(n_rows_macro)


def test_ei():
    """Run sanity checks for EI computation."""
    print("=" * 60)
    print("EFFECTIVE INFORMATION SANITY CHECKS")
    print("=" * 60)

    all_pass = True

    # Check 1: Identity matrix → EI = log2(n_states)
    n = 8
    print(f"\nCheck 1: Identity matrix ({n}x{n}) → EI should be log2({n}) = {np.log2(n):.4f}")
    T_identity = np.eye(n)
    ei = effective_information(T_identity)
    expected = np.log2(n)
    passed = abs(ei - expected) < 1e-10
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  EI = {ei:.6f}, expected = {expected:.6f} → {status}")
    all_pass &= passed

    # Check 2: All-same-row matrix → EI = 0
    print(f"\nCheck 2: All-same-row matrix ({n}x{n}) → EI should be 0")
    row = np.ones(n) / n
    T_uniform = np.tile(row, (n, 1))
    ei = effective_information(T_uniform)
    passed = abs(ei) < 1e-10
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  EI = {ei:.6f}, expected = 0.000000 → {status}")
    all_pass &= passed

    # Check 3: Random stochastic matrix → EI between 0 and log2(n)
    print(f"\nCheck 3: Random stochastic matrix ({n}x{n}) → EI between 0 and {np.log2(n):.4f}")
    rng = np.random.RandomState(42)
    T_random = rng.random((n, n))
    T_random /= T_random.sum(axis=1, keepdims=True)
    ei = effective_information(T_random)
    passed = 0 < ei < np.log2(n)
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  EI = {ei:.6f} → {status}")
    all_pass &= passed

    # Check 4: Transition matrix estimation with scaled Laplace
    print(f"\nCheck 4: Transition matrix estimation (scaled Laplace)")
    n_obs = 10000
    states_t = np.repeat(np.arange(4), n_obs // 4)
    states_t1 = (states_t + 1) % 4
    T_est, rc = estimate_transition_matrix(states_t, states_t1, 4)
    ei = effective_information(T_est)
    expected_approx = np.log2(4)
    passed = ei > 1.95  # Tighter with scaled Laplace (less smoothing)
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  EI = {ei:.6f}, expected ≈ {expected_approx:.4f} → {status}")
    print(f"  Row counts: {rc}")
    all_pass &= passed

    # Check 5: EI is non-negative
    print(f"\nCheck 5: EI is always non-negative (100 random matrices)")
    neg_count = 0
    for i in range(100):
        rng2 = np.random.RandomState(i)
        T_test = rng2.random((16, 16))
        T_test /= T_test.sum(axis=1, keepdims=True)
        ei_test = effective_information(T_test)
        if ei_test < 0:
            neg_count += 1
    passed = neg_count == 0
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  Negative EI count: {neg_count}/100 → {status}")
    all_pass &= passed

    # Check 6: Observed-only EI excludes unvisited rows
    print(f"\nCheck 6: Observed-only EI with min_observations filter")
    # Create data where only states 0,1 are visited
    states_t_sparse = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    states_t1_sparse = np.array([1, 1, 0, 0, 1, 0, 1, 0])
    T_sparse, rc_sparse = estimate_transition_matrix(states_t_sparse, states_t1_sparse, 8)
    ei_full = effective_information(T_sparse)
    ei_obs = effective_information(T_sparse, rc_sparse, min_observations=1)
    # Observed-only should be higher since unvisited uniform rows inflate noise
    passed = ei_obs >= ei_full
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  EI (full, 8 states): {ei_full:.6f}")
    print(f"  EI (observed only):  {ei_obs:.6f}")
    print(f"  Visited rows: {(rc_sparse > 0).sum()}/8")
    print(f"  Observed >= Full? {passed} → {status}")
    all_pass &= passed

    print(f"\n{'ALL EI CHECKS PASSED ✓' if all_pass else 'SOME EI CHECKS FAILED ✗'}")
    print("=" * 60)
    return all_pass


if __name__ == "__main__":
    test_ei()
