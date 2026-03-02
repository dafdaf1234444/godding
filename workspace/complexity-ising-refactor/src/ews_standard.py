"""
Standard early warning signals: rolling variance and lag-1 autocorrelation.

These are the classic indicators from Scheffer et al. (2009) that are expected
to increase ("critical slowing down") as a system approaches a tipping point.
"""

import numpy as np


def compute_ews(timeseries, window_size):
    """
    Compute rolling variance and lag-1 autocorrelation of a time series.

    Parameters
    ----------
    timeseries : ndarray of shape (N,)
        The 1D time series (e.g., magnetization over time).
    window_size : int
        Number of data points in each rolling window.

    Returns
    -------
    result : dict with keys:
        'variance' : ndarray — rolling variance for each window
        'autocorrelation' : ndarray — rolling lag-1 autocorrelation for each window
        'timestamps' : ndarray — center index of each window
    """
    N = len(timeseries)
    n_windows = N - window_size + 1

    if n_windows <= 0:
        raise ValueError(f"Window size {window_size} exceeds timeseries length {N}")

    variance = np.empty(n_windows)
    autocorrelation = np.empty(n_windows)
    timestamps = np.empty(n_windows)

    for i in range(n_windows):
        window = timeseries[i:i + window_size]
        timestamps[i] = i + window_size / 2.0

        # Rolling variance
        variance[i] = np.var(window)

        # Rolling lag-1 autocorrelation
        x = window[:-1]
        y = window[1:]
        mx = x.mean()
        my = y.mean()
        sx = x.std()
        sy = y.std()
        if sx > 0 and sy > 0:
            autocorrelation[i] = np.mean((x - mx) * (y - my)) / (sx * sy)
        else:
            autocorrelation[i] = 0.0

    return {
        'variance': variance,
        'autocorrelation': autocorrelation,
        'timestamps': timestamps,
    }


def test_ews():
    """Run sanity checks for standard EWS."""
    print("=" * 60)
    print("STANDARD EWS SANITY CHECKS")
    print("=" * 60)

    all_pass = True

    # Check 1: Constant timeseries → zero variance, zero autocorrelation
    print("\nCheck 1: Constant timeseries → variance ≈ 0")
    ts = np.ones(100)
    result = compute_ews(ts, window_size=20)
    mean_var = result['variance'].mean()
    passed = mean_var < 1e-10
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  Mean variance = {mean_var:.2e} → {status}")
    all_pass &= passed

    # Check 2: White noise → positive variance, low autocorrelation
    print("\nCheck 2: White noise → positive variance, |AC| < 0.2")
    rng = np.random.RandomState(42)
    ts = rng.randn(1000)
    result = compute_ews(ts, window_size=100)
    mean_var = result['variance'].mean()
    mean_ac = np.abs(result['autocorrelation']).mean()
    passed_v = mean_var > 0.5
    passed_a = mean_ac < 0.2
    status_v = "PASS ✓" if passed_v else "FAIL ✗"
    status_a = "PASS ✓" if passed_a else "FAIL ✗"
    print(f"  Mean variance = {mean_var:.4f} (expected ~1.0) → {status_v}")
    print(f"  Mean |autocorrelation| = {mean_ac:.4f} (expected < 0.2) → {status_a}")
    all_pass &= passed_v and passed_a

    # Check 3: Highly correlated timeseries → high autocorrelation
    print("\nCheck 3: AR(1) process with phi=0.95 → high autocorrelation")
    ts_ar = np.zeros(1000)
    for i in range(1, 1000):
        ts_ar[i] = 0.95 * ts_ar[i - 1] + rng.randn() * 0.1
    result = compute_ews(ts_ar, window_size=100)
    mean_ac = result['autocorrelation'].mean()
    passed = mean_ac > 0.8
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  Mean autocorrelation = {mean_ac:.4f} (expected > 0.8) → {status}")
    all_pass &= passed

    # Check 4: Output shapes
    print("\nCheck 4: Output shapes are correct")
    ts = np.ones(50)
    result = compute_ews(ts, window_size=10)
    expected_len = 41
    passed = (len(result['variance']) == expected_len and
              len(result['autocorrelation']) == expected_len and
              len(result['timestamps']) == expected_len)
    status = "PASS ✓" if passed else "FAIL ✗"
    print(f"  Lengths: var={len(result['variance'])}, ac={len(result['autocorrelation'])}, ts={len(result['timestamps'])}")
    print(f"  Expected: {expected_len} → {status}")
    all_pass &= passed

    print(f"\n{'ALL EWS CHECKS PASSED ✓' if all_pass else 'SOME EWS CHECKS FAILED ✗'}")
    print("=" * 60)
    return all_pass


if __name__ == "__main__":
    test_ews()
