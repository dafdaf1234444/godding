"""
Tests for analysis module and Wolff algorithm.

Covers critical untested functions:
1. kendall_tau — rank correlation used throughout project
2. detect_threshold_crossing — all lead-time claims depend on this
3. compute_lead_time — converts trigger temperature to lead time
4. simulate_ising_wolff — Wolff cluster algorithm central to findings
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analysis import kendall_tau, detect_threshold_crossing, compute_lead_time
from src.ising import simulate_ising_wolff


def test_kendall_tau():
    """Test Kendall tau rank correlation against known values."""
    print("\n" + "=" * 60)
    print("TEST: KENDALL TAU")
    print("=" * 60)
    all_pass = True

    # Test 1: Perfectly concordant pairs -> tau = 1.0
    print("\n1. Perfectly concordant pairs -> tau = 1.0")
    x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
    y = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
    tau, p = kendall_tau(x, y)
    passed = abs(tau - 1.0) < 1e-10
    print(f"   tau = {tau:.6f}, p = {p:.6e} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 2: Perfectly discordant pairs -> tau = -1.0
    print("\n2. Perfectly discordant pairs -> tau = -1.0")
    x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
    y = np.array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1], dtype=float)
    tau, p = kendall_tau(x, y)
    passed = abs(tau - (-1.0)) < 1e-10
    print(f"   tau = {tau:.6f}, p = {p:.6e} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 3: Random data -> |tau| < 0.5 typically
    print("\n3. Random data -> |tau| < 0.5")
    rng = np.random.RandomState(42)
    x = rng.randn(100)
    y = rng.randn(100)
    tau, p = kendall_tau(x, y)
    passed = abs(tau) < 0.5
    print(f"   tau = {tau:.6f}, p = {p:.6e} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 4: Constant input -> should handle gracefully (tau=NaN or 0)
    print("\n4. Constant input -> handles gracefully (NaN or 0, no crash)")
    x = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    try:
        tau, p = kendall_tau(x, y)
        # scipy.stats.kendalltau returns nan for constant input
        passed = np.isnan(tau) or abs(tau) < 1e-10
        print(f"   tau = {tau}, p = {p} -> {'PASS' if passed else 'FAIL'}")
    except Exception as e:
        print(f"   Raised exception: {e} -> FAIL (should handle gracefully)")
        passed = False
    all_pass &= passed

    # Test 5: p-value significance for perfectly correlated
    print("\n5. Perfect correlation -> p-value very small")
    x = np.arange(20, dtype=float)
    y = np.arange(20, dtype=float)
    tau, p = kendall_tau(x, y)
    passed = p < 0.001
    print(f"   tau = {tau:.6f}, p = {p:.6e} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_detect_threshold_crossing():
    """Test threshold crossing detection -- all lead-time claims depend on this."""
    print("\n" + "=" * 60)
    print("TEST: DETECT THRESHOLD CROSSING")
    print("=" * 60)
    all_pass = True

    # Test 1: Normal case -- indicator rises at T=2.2
    print("\n1. Normal case: indicator rises at T=2.2 -> trigger at T=2.2")
    temperatures = np.array([3.0, 2.8, 2.6, 2.4, 2.2, 2.0])
    # Baseline at high T (flat, low values), rises at T=2.2
    indicator = np.array([1.0, 1.0, 1.0, 1.1, 5.0, 8.0])
    # Baseline mask: first 3 points are baseline (T >= 2.6)
    baseline_mask = np.array([True, True, True, False, False, False])
    T_trigger, threshold = detect_threshold_crossing(temperatures, indicator, baseline_mask, n_sigma=2)
    # Baseline mean = 1.0, std = 0.0, threshold = 1.0 + 2*0 = 1.0
    # First non-baseline point exceeding 1.0: T=2.4 (val=1.1 > 1.0)
    # Actually with std=0, threshold=1.0, and val=1.1 > 1.0, T_trigger=2.4
    passed = T_trigger == 2.4
    print(f"   T_trigger = {T_trigger}, threshold = {threshold:.4f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 1b: With non-zero baseline std, trigger at expected point
    print("\n1b. Indicator rises clearly at T=2.2 with noisy baseline")
    indicator_noisy = np.array([1.0, 1.2, 0.8, 1.5, 5.0, 8.0])
    baseline_mask_noisy = np.array([True, True, True, False, False, False])
    T_trigger, threshold = detect_threshold_crossing(
        temperatures, indicator_noisy, baseline_mask_noisy, n_sigma=2
    )
    # Baseline: [1.0, 1.2, 0.8], mean=1.0, std~0.163
    # Threshold = 1.0 + 2*0.163 = 1.327
    # First non-baseline exceeding: T=2.4 (val=1.5 > 1.327) or T=2.2 (val=5.0)?
    # T=2.4 val=1.5 > 1.327 -> trigger at 2.4
    passed = T_trigger == 2.4
    print(f"   T_trigger = {T_trigger}, threshold = {threshold:.4f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 2: Never crosses -- indicator stays flat
    print("\n2. Never crosses: indicator stays flat -> returns None")
    indicator_flat = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    baseline_mask_all = np.array([True, True, True, False, False, False])
    T_trigger, threshold = detect_threshold_crossing(
        temperatures, indicator_flat, baseline_mask_all, n_sigma=2
    )
    # Baseline mean=1.0, std=0.0, threshold=1.0
    # Non-baseline values are all 1.0, which is NOT strictly > 1.0
    passed = T_trigger is None
    print(f"   T_trigger = {T_trigger}, threshold = {threshold:.4f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 3: Immediate cross -- first non-baseline point exceeds threshold
    print("\n3. Immediate cross: first non-baseline point exceeds threshold")
    indicator_immediate = np.array([1.0, 1.0, 1.0, 10.0, 10.0, 10.0])
    T_trigger, threshold = detect_threshold_crossing(
        temperatures, indicator_immediate, baseline_mask, n_sigma=2
    )
    # Baseline std=0, threshold=1.0, first non-baseline (T=2.4) val=10.0 > 1.0
    passed = T_trigger == 2.4
    print(f"   T_trigger = {T_trigger}, threshold = {threshold:.4f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 4: Zero std baseline -- all baseline values identical
    print("\n4. Zero std baseline: all baseline values identical -> threshold = baseline value")
    indicator_zero_std = np.array([2.0, 2.0, 2.0, 2.5, 3.0, 4.0])
    T_trigger, threshold = detect_threshold_crossing(
        temperatures, indicator_zero_std, baseline_mask, n_sigma=2
    )
    # Baseline: [2.0, 2.0, 2.0], mean=2.0, std=0.0
    # Threshold = 2.0 + 2*0 = 2.0
    # First non-baseline exceeding 2.0: T=2.4 (val=2.5 > 2.0)
    passed = T_trigger == 2.4 and abs(threshold - 2.0) < 1e-10
    print(f"   T_trigger = {T_trigger}, threshold = {threshold:.4f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 5: Baseline mask excludes baseline points from being returned
    print("\n5. Baseline mask: points IN baseline are never returned as triggers")
    # Even if a baseline point exceeds threshold (e.g., due to weird data), it should not trigger
    indicator_weird = np.array([1.0, 1.0, 50.0, 1.5, 5.0, 8.0])
    # Third point (T=2.6) is baseline but has high value
    baseline_mask_weird = np.array([True, True, True, False, False, False])
    T_trigger, threshold = detect_threshold_crossing(
        temperatures, indicator_weird, baseline_mask_weird, n_sigma=2
    )
    # Baseline: [1.0, 1.0, 50.0], mean=17.33, std=23.09
    # Threshold = 17.33 + 2*23.09 = 63.52
    # Non-baseline: T=2.4 (1.5), T=2.2 (5.0), T=2.0 (8.0) -> none exceed 63.52
    passed = T_trigger is None
    print(f"   T_trigger = {T_trigger}, threshold = {threshold:.4f}")
    print(f"   Baseline outlier correctly inflates threshold -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 5b: Verify trigger is always non-baseline
    print("\n5b. Trigger must be non-baseline even with high baseline points")
    indicator_cross_in_baseline = np.array([1.0, 1.0, 1.0, 0.5, 0.5, 0.5])
    # All non-baseline below threshold
    T_trigger, threshold = detect_threshold_crossing(
        temperatures, indicator_cross_in_baseline, baseline_mask, n_sigma=2
    )
    passed = T_trigger is None
    print(f"   T_trigger = {T_trigger} (non-baseline values below threshold) -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 6: n_sigma parameter -- different sigma levels
    print("\n6a. n_sigma=1: lower threshold -> earlier trigger")
    indicator_gradual = np.array([1.0, 1.1, 0.9, 1.8, 3.0, 5.0])
    baseline_mask_grad = np.array([True, True, True, False, False, False])
    T_trigger_1, threshold_1 = detect_threshold_crossing(
        temperatures, indicator_gradual, baseline_mask_grad, n_sigma=1
    )
    # Baseline: [1.0, 1.1, 0.9], mean=1.0, std~0.082
    # Threshold(1sigma) = 1.0 + 1*0.082 = 1.082
    # First non-baseline exceeding: T=2.4 (val=1.8 > 1.082)
    passed_1 = T_trigger_1 == 2.4
    print(f"   T_trigger(1sigma) = {T_trigger_1}, threshold = {threshold_1:.4f} -> {'PASS' if passed_1 else 'FAIL'}")
    all_pass &= passed_1

    print("\n6b. n_sigma=3: higher threshold -> later trigger (or no trigger)")
    T_trigger_3, threshold_3 = detect_threshold_crossing(
        temperatures, indicator_gradual, baseline_mask_grad, n_sigma=3
    )
    # Threshold(3sigma) = 1.0 + 3*0.082 = 1.245
    # First non-baseline exceeding: T=2.4 (val=1.8 > 1.245)
    passed_3 = T_trigger_3 is not None
    print(f"   T_trigger(3sigma) = {T_trigger_3}, threshold = {threshold_3:.4f} -> {'PASS' if passed_3 else 'FAIL'}")
    all_pass &= passed_3

    # Verify threshold ordering: higher n_sigma -> higher threshold
    passed_order = threshold_3 > threshold_1
    print(f"   threshold(3sigma) > threshold(1sigma): {threshold_3:.4f} > {threshold_1:.4f} -> {'PASS' if passed_order else 'FAIL'}")
    all_pass &= passed_order

    # Test 7: Large n_sigma suppresses trigger
    print("\n7. n_sigma=100: extremely high threshold -> no trigger")
    T_trigger_100, threshold_100 = detect_threshold_crossing(
        temperatures, indicator_gradual, baseline_mask_grad, n_sigma=100
    )
    passed = T_trigger_100 is None
    print(f"   T_trigger(100sigma) = {T_trigger_100}, threshold = {threshold_100:.4f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_compute_lead_time():
    """Test lead time computation."""
    print("\n" + "=" * 60)
    print("TEST: COMPUTE LEAD TIME")
    print("=" * 60)
    all_pass = True

    T_c = 2.269185

    # Test 1: Early warning (trigger before T_c)
    print("\n1. T_trigger=2.15, T_c=2.269 -> lead = +0.119 (early warning)")
    lead = compute_lead_time(2.15, T_c)
    expected = T_c - 2.15
    passed = abs(lead - expected) < 1e-6
    print(f"   lead = {lead:.6f}, expected = {expected:.6f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 2: Late warning (trigger after T_c)
    print("\n2. T_trigger=2.30, T_c=2.269 -> lead = -0.031 (late warning)")
    lead = compute_lead_time(2.30, T_c)
    expected = T_c - 2.30
    passed = abs(lead - expected) < 1e-6 and lead < 0
    print(f"   lead = {lead:.6f}, expected = {expected:.6f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 3: T_trigger=None -> returns None
    print("\n3. T_trigger=None -> returns None")
    lead = compute_lead_time(None, T_c)
    passed = lead is None
    print(f"   lead = {lead} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 4: Trigger exactly at T_c -> lead = 0
    print("\n4. T_trigger=T_c -> lead = 0.0")
    lead = compute_lead_time(T_c, T_c)
    passed = abs(lead) < 1e-10
    print(f"   lead = {lead:.10f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_wolff_ordered_phase():
    """Test Wolff algorithm in ordered (low T) phase."""
    print("\n" + "=" * 60)
    print("TEST: WOLFF ORDERED PHASE")
    print("=" * 60)
    all_pass = True

    print("\n1. T=1.0, L=16 -> mean |magnetization| > 0.90")
    configs, mags = simulate_ising_wolff(L=16, T=1.0, n_steps=100, n_equilib=200, seed=42)
    mean_mag = mags.mean()
    passed = mean_mag > 0.90
    print(f"   Mean |M| = {mean_mag:.4f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_wolff_disordered_phase():
    """Test Wolff algorithm in disordered (high T) phase."""
    print("\n" + "=" * 60)
    print("TEST: WOLFF DISORDERED PHASE")
    print("=" * 60)
    all_pass = True

    print("\n1. T=4.0, L=16 -> mean |magnetization| < 0.15")
    configs, mags = simulate_ising_wolff(L=16, T=4.0, n_steps=100, n_equilib=200, seed=42)
    mean_mag = mags.mean()
    passed = mean_mag < 0.15
    print(f"   Mean |M| = {mean_mag:.4f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_wolff_near_critical():
    """Test Wolff algorithm near the critical temperature."""
    print("\n" + "=" * 60)
    print("TEST: WOLFF NEAR CRITICAL")
    print("=" * 60)
    all_pass = True

    print("\n1. T=2.27, L=16 -> mean |magnetization| between 0.1 and 0.8")
    configs, mags = simulate_ising_wolff(L=16, T=2.27, n_steps=100, n_equilib=200, seed=42)
    mean_mag = mags.mean()
    passed = 0.1 < mean_mag < 0.8
    print(f"   Mean |M| = {mean_mag:.4f} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_wolff_output_shape():
    """Test Wolff output shapes and value constraints."""
    print("\n" + "=" * 60)
    print("TEST: WOLFF OUTPUT SHAPE")
    print("=" * 60)
    all_pass = True

    L = 12
    n_steps = 50
    configs, mags = simulate_ising_wolff(L=L, T=2.0, n_steps=n_steps, n_equilib=100, seed=42)

    # Test 1: configs shape
    print(f"\n1. configs shape = ({n_steps}, {L}, {L})")
    passed = configs.shape == (n_steps, L, L)
    print(f"   Actual shape = {configs.shape} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 2: magnetizations shape
    print(f"\n2. magnetizations shape = ({n_steps},)")
    passed = mags.shape == (n_steps,)
    print(f"   Actual shape = {mags.shape} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 3: Values are +1/-1 only
    print("\n3. Spin values are +1/-1 only")
    unique_vals = np.unique(configs)
    passed = set(unique_vals).issubset({-1, 1})
    print(f"   Unique values = {sorted(unique_vals)} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 4: Magnetization values in [0, 1]
    print("\n4. Magnetization values in [0, 1]")
    passed = np.all(mags >= 0.0) and np.all(mags <= 1.0)
    print(f"   Range = [{mags.min():.4f}, {mags.max():.4f}] -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 5: Magnetization consistent with configs
    print("\n5. Magnetization consistent with spin configurations")
    expected_mags = np.abs(configs.sum(axis=(1, 2))) / (L * L)
    max_diff = np.max(np.abs(mags - expected_mags))
    passed = max_diff < 1e-10
    print(f"   Max |mag - recomputed| = {max_diff:.2e} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def test_wolff_reproducibility():
    """Test that same seed produces identical Wolff results."""
    print("\n" + "=" * 60)
    print("TEST: WOLFF REPRODUCIBILITY")
    print("=" * 60)
    all_pass = True

    print("\n1. Same seed -> identical configs and magnetizations")
    configs1, mags1 = simulate_ising_wolff(L=12, T=2.0, n_steps=50, n_equilib=100, seed=123)
    configs2, mags2 = simulate_ising_wolff(L=12, T=2.0, n_steps=50, n_equilib=100, seed=123)

    configs_match = np.array_equal(configs1, configs2)
    mags_match = np.array_equal(mags1, mags2)
    passed = configs_match and mags_match
    print(f"   Configs identical: {configs_match}, Mags identical: {mags_match} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    # Test 2: Different seeds -> different results
    print("\n2. Different seeds -> different results")
    configs3, mags3 = simulate_ising_wolff(L=12, T=2.0, n_steps=50, n_equilib=100, seed=456)
    configs_differ = not np.array_equal(configs1, configs3)
    passed = configs_differ
    print(f"   Configs differ: {configs_differ} -> {'PASS' if passed else 'FAIL'}")
    all_pass &= passed

    return all_pass


def main():
    print("=" * 60)
    print("ANALYSIS & WOLFF ALGORITHM TEST SUITE")
    print("=" * 60)

    results = {}

    # Analysis module tests
    results['Kendall Tau'] = test_kendall_tau()
    results['Threshold Crossing'] = test_detect_threshold_crossing()
    results['Lead Time'] = test_compute_lead_time()

    # Wolff algorithm tests
    results['Wolff Ordered Phase'] = test_wolff_ordered_phase()
    results['Wolff Disordered Phase'] = test_wolff_disordered_phase()
    results['Wolff Near Critical'] = test_wolff_near_critical()
    results['Wolff Output Shape'] = test_wolff_output_shape()
    results['Wolff Reproducibility'] = test_wolff_reproducibility()

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
