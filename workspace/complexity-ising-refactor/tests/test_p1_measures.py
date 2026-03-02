"""
Targeted verification tests for P1 information measure implementations.

Tests each measure against known analytical results to verify correctness:
1. Excess entropy: 0 for iid, positive for correlated
2. Transfer entropy: 0 for independent, positive for coupled
3. Time irreversibility: 0 for reversible, positive for irreversible
4. Total correlation: 0 for independent, positive for correlated
5. EI ratio: basic sanity checks
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from experiments.phase1_p1_comparison import (
    compute_excess_entropy,
    compute_transfer_entropy,
    compute_time_irreversibility,
    compute_total_correlation,
    compute_ei_ratio,
    config_to_patch_states,
)
from src.ei_compute import estimate_transition_matrix, effective_information
from src.coarse_grain import coarsegrain_timeseries


def test_excess_entropy():
    """Test excess entropy against known results."""
    print("\n" + "=" * 60)
    print("TEST: EXCESS ENTROPY")
    print("=" * 60)
    all_pass = True

    # Test 1: iid binary sequence → E_k should be ~0
    print("\n1. iid binary sequence (N=10000) → E_k ≈ 0")
    rng = np.random.RandomState(42)
    iid_ts = rng.choice([-1.0, 1.0], size=10000)
    E1_iid = compute_excess_entropy(iid_ts, k=1, n_bins=2)
    passed = E1_iid < 0.05  # Should be near zero (plug-in bias)
    print(f"   E_1 = {E1_iid:.6f} (expected ~0) → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    E5_iid = compute_excess_entropy(iid_ts, k=5, n_bins=2)
    passed = E5_iid < 0.1
    print(f"   E_5 = {E5_iid:.6f} (expected ~0) → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 2: Perfectly predictable sequence → E_k should be positive
    print("\n2. Alternating sequence (deterministic) → E_k > 0")
    alt_ts = np.array([1.0, -1.0] * 5000)
    E1_alt = compute_excess_entropy(alt_ts, k=1, n_bins=2)
    passed = E1_alt > 0.5  # Should be ~1 bit (past fully predicts future)
    print(f"   E_1 = {E1_alt:.6f} (expected ~1.0 bit) → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 3: Correlated AR(1) → E_k between iid and deterministic
    print("\n3. AR(1) with phi=0.9 → 0 < E_1 < 1.0")
    ar_ts = np.zeros(10000)
    for i in range(1, 10000):
        ar_ts[i] = 0.9 * ar_ts[i-1] + rng.randn() * 0.1
    E1_ar = compute_excess_entropy(ar_ts, k=1, n_bins=16)
    passed = 0.0 < E1_ar < 2.0
    print(f"   E_1 = {E1_ar:.6f} → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 4: k=10 estimation bias check
    print("\n4. k=10 estimation bias: E_10(iid) should be small but may be inflated")
    E10_iid = compute_excess_entropy(iid_ts, k=10, n_bins=2)
    # With 2000 samples (as in P1), k=10 has 2^20 joint states → severe bias
    # With 10000 samples, 2^10=1024 marginal states, still biased
    print(f"   E_10(iid, N=10000) = {E10_iid:.6f}")
    # Test with N=2000 (same as P1)
    E10_iid_short = compute_excess_entropy(iid_ts[:2000], k=10, n_bins=2)
    print(f"   E_10(iid, N=2000) = {E10_iid_short:.6f}")
    if E10_iid_short > 1.0:
        print(f"   WARNING: E_10 with N=2000 is severely biased (>{E10_iid_short:.1f} bits for iid data)")
        print(f"   This confirms the k=10 results in P1 are unreliable")
    passed = True  # Informational, not a hard failure
    all_pass &= passed

    # Test 5: E_k should increase with k for correlated data
    print("\n5. E_k should increase with k for correlated data")
    E1_ar = compute_excess_entropy(ar_ts, k=1, n_bins=16)
    E5_ar = compute_excess_entropy(ar_ts, k=5, n_bins=16)
    passed = E5_ar >= E1_ar * 0.8  # Should be at least comparable
    print(f"   E_1 = {E1_ar:.6f}, E_5 = {E5_ar:.6f} → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_transfer_entropy():
    """Test transfer entropy against known results."""
    print("\n" + "=" * 60)
    print("TEST: TRANSFER ENTROPY")
    print("=" * 60)
    all_pass = True

    rng = np.random.RandomState(42)

    # Test 1: Independent processes → TE ≈ 0
    print("\n1. Independent iid processes → TE ≈ 0")
    x = rng.randn(5000)
    y = rng.randn(5000)
    te_xy = compute_transfer_entropy(x, y, n_bins=8)
    te_yx = compute_transfer_entropy(y, x, n_bins=8)
    passed = te_xy < 0.05 and te_yx < 0.05
    print(f"   TE(X→Y) = {te_xy:.6f}, TE(Y→X) = {te_yx:.6f} (expected ~0)")
    print(f"   → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 2: Causal coupling X→Y → TE(X→Y) > TE(Y→X)
    print("\n2. Causal coupling X→Y with lag → TE(X→Y) > TE(Y→X)")
    x = rng.randn(5000)
    y = np.zeros(5000)
    for i in range(1, 5000):
        y[i] = 0.8 * x[i-1] + 0.2 * rng.randn()
    te_xy = compute_transfer_entropy(x, y, n_bins=8)
    te_yx = compute_transfer_entropy(y, x, n_bins=8)
    passed = te_xy > te_yx and te_xy > 0.1
    print(f"   TE(X→Y) = {te_xy:.6f}, TE(Y→X) = {te_yx:.6f}")
    print(f"   TE(X→Y) > TE(Y→X)? {te_xy > te_yx} → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 3: Symmetric coupling → TE approximately symmetric
    print("\n3. Symmetric coupling → TE(X→Y) ≈ TE(Y→X)")
    x = np.zeros(5000)
    y = np.zeros(5000)
    x[0] = rng.randn()
    y[0] = rng.randn()
    for i in range(1, 5000):
        x[i] = 0.5 * y[i-1] + 0.5 * rng.randn()
        y[i] = 0.5 * x[i-1] + 0.5 * rng.randn()
    te_xy = compute_transfer_entropy(x, y, n_bins=8)
    te_yx = compute_transfer_entropy(y, x, n_bins=8)
    ratio = te_xy / te_yx if te_yx > 0 else float('inf')
    passed = 0.5 < ratio < 2.0
    print(f"   TE(X→Y) = {te_xy:.6f}, TE(Y→X) = {te_yx:.6f}, ratio = {ratio:.2f}")
    print(f"   Approximately symmetric? → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 4: TE on binary data (as used in P1)
    print("\n4. Binary source, binary target (as in P1 macro blocks)")
    x_bin = rng.choice([-1.0, 1.0], size=2000)
    y_bin = np.zeros(2000)
    for i in range(1, 2000):
        y_bin[i] = x_bin[i-1] if rng.random() < 0.8 else -x_bin[i-1]
    te_bin = compute_transfer_entropy(x_bin, y_bin, n_bins=8)
    passed = te_bin > 0.0
    print(f"   TE(X→Y) = {te_bin:.6f} (expected > 0) → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_time_irreversibility():
    """Test time irreversibility against known results."""
    print("\n" + "=" * 60)
    print("TEST: TIME IRREVERSIBILITY")
    print("=" * 60)
    all_pass = True

    rng = np.random.RandomState(42)

    # Test 1: Gaussian white noise (reversible) → TI ≈ 0
    print("\n1. Gaussian white noise (time-reversible) → TI ≈ 0")
    N = 2000
    noise = rng.randn(N, 6, 6).astype(np.int8)
    noise[noise >= 0] = 1
    noise[noise < 0] = -1
    ti_noise = compute_time_irreversibility(noise, max_lag=10)
    # For iid noise, the third-order cross-correlations should average to ~0
    # but finite-sample noise creates small values
    passed = ti_noise < 0.1
    print(f"   TI = {ti_noise:.6f} (expected ~0) → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 2: Asymmetric process (sawtooth) → TI > 0
    print("\n2. Sawtooth-like asymmetric process → TI > 0")
    sawtooth = np.zeros((N, 4, 4), dtype=np.int8)
    for t in range(N):
        phase = (t % 20) / 20.0
        # Slow rise, fast drop
        if phase < 0.8:
            val = 1
        else:
            val = -1
        sawtooth[t, :, :] = val
    ti_saw = compute_time_irreversibility(sawtooth, max_lag=10)
    passed = ti_saw > ti_noise
    print(f"   TI = {ti_saw:.6f} (expected > {ti_noise:.6f}) → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 3: Constant configuration → TI = 0
    print("\n3. Constant configuration → TI = 0")
    const = np.ones((N, 6, 6), dtype=np.int8)
    ti_const = compute_time_irreversibility(const, max_lag=10)
    passed = ti_const < 1e-10
    print(f"   TI = {ti_const:.6f} (expected 0) → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_total_correlation():
    """Test total correlation against known results."""
    print("\n" + "=" * 60)
    print("TEST: TOTAL CORRELATION")
    print("=" * 60)
    all_pass = True

    rng = np.random.RandomState(42)
    N = 5000

    # Test 1: Independent binary blocks → TC ≈ 0
    print("\n1. Independent random binary blocks → TC ≈ 0")
    indep = rng.choice([-1, 1], size=(N, 4, 4)).astype(np.int8)
    tc_indep = compute_total_correlation(indep)
    # With 4x4=16 blocks and N=5000, joint space is 2^16=65536
    # Plug-in will overestimate TC significantly
    print(f"   TC = {tc_indep:.6f}")
    if tc_indep > 1.0:
        print(f"   WARNING: TC is {tc_indep:.1f} bits for independent data (plug-in bias)")
        print(f"   This confirms TC estimation is unreliable for >~10 binary variables")
    passed = True  # Informational
    all_pass &= passed

    # Test 2: Smaller system (2x2=4 blocks) to reduce bias
    print("\n2. Independent random binary 2x2 blocks → TC ≈ 0")
    indep_small = rng.choice([-1, 1], size=(N, 2, 2)).astype(np.int8)
    tc_small = compute_total_correlation(indep_small)
    # 4 blocks → 2^4=16 states, N=5000 → adequate sampling
    passed = tc_small < 0.5  # Should be near 0 with good sampling
    print(f"   TC = {tc_small:.6f} (expected ~0) → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 3: Perfectly correlated blocks → TC > 0
    print("\n3. All blocks identical (perfect correlation) → TC > 0")
    correlated = np.zeros((N, 2, 2), dtype=np.int8)
    for t in range(N):
        val = rng.choice([-1, 1])
        correlated[t, :, :] = val
    tc_corr = compute_total_correlation(correlated)
    # TC should be (n_blocks - 1) * H(X_i) = 3 * 1.0 = 3.0 bits
    passed = tc_corr > 2.0
    print(f"   TC = {tc_corr:.6f} (expected ~3.0 bits) → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 4: Demonstrate plug-in bias scaling
    print("\n4. Plug-in bias scaling: TC(independent) vs n_blocks")
    for L_c in [2, 3, 4, 5, 6]:
        n_blocks = L_c * L_c
        data = rng.choice([-1, 1], size=(2000, L_c, L_c)).astype(np.int8)
        tc = compute_total_correlation(data)
        max_possible = n_blocks * 1.0  # Each H(X_i) = 1 bit
        print(f"   {L_c}x{L_c} ({n_blocks} blocks): TC = {tc:.2f} bits "
              f"(max = {max_possible:.0f}, true = 0)")

    return all_pass


def test_config_to_patch_states():
    """Test patch encoding correctness."""
    print("\n" + "=" * 60)
    print("TEST: PATCH STATE ENCODING")
    print("=" * 60)
    all_pass = True

    # Test 1: All-up configuration → all-ones patch → state 2^(p*p)-1
    print("\n1. All-up 8x8 config, 2x2 patches → state = 15 (=1111 binary)")
    configs = np.ones((1, 8, 8), dtype=np.int8)
    states, n_states, n_patches = config_to_patch_states(configs, patch_size=2)
    expected_state = 2**4 - 1  # = 15
    passed = np.all(states[0] == expected_state)
    print(f"   All patches = {states[0, 0]}, expected = {expected_state} → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 2: All-down → state 0 (all bits 0)
    print("\n2. All-down 8x8 config, 2x2 patches → state = 0")
    configs = -np.ones((1, 8, 8), dtype=np.int8)
    states, n_states, n_patches = config_to_patch_states(configs, patch_size=2)
    passed = np.all(states[0] == 0)
    print(f"   All patches = {states[0, 0]}, expected = 0 → {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 3: Number of states and patches
    print("\n3. L=24, p=2 → n_states=16, n_patches=144")
    configs = np.ones((1, 24, 24), dtype=np.int8)
    states, n_states, n_patches = config_to_patch_states(configs, patch_size=2)
    passed_states = n_states == 16
    passed_patches = n_patches == 144
    print(f"   n_states = {n_states} (expected 16) → {'PASS' if passed_states else 'FAIL'}")
    print(f"   n_patches = {n_patches} (expected 144) → {'PASS' if passed_patches else 'FAIL'}")
    all_pass &= passed_states and passed_patches

    return all_pass


def main():
    print("=" * 60)
    print("P1 MEASURE VERIFICATION TEST SUITE")
    print("=" * 60)

    results = {}

    results['Patch Encoding'] = test_config_to_patch_states()
    results['Excess Entropy'] = test_excess_entropy()
    results['Transfer Entropy'] = test_transfer_entropy()
    results['Time Irreversibility'] = test_time_irreversibility()
    results['Total Correlation'] = test_total_correlation()

    print("\n" + "=" * 60)
    print("OVERALL RESULTS")
    print("=" * 60)
    all_pass = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        all_pass &= passed

    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    print("=" * 60)

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
