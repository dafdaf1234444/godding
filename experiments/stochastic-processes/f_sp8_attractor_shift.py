#!/usr/bin/env python3
"""F-SP8 attractor non-stationarity: rolling-window OU estimation.

Tests whether the long-run mean (attractor) of the swarm's quality OU process
has shifted over its lifetime, or is truly fixed at ~8.78 (S538b finding).

Method:
1. Load lesson Sharpe series with session numbers.
2. Compute era means (25-session windows).
3. Fit AR(1) on rolling windows of 5 eras → extract beta and LR mean per window.
4. Test LR mean stability: bootstrap confidence bands, detect significant shifts.
5. Correlate attractor shifts with structural covariates (tool count, domain count).

Pre-registration: If attractor is fixed, all rolling LR means cluster within ±0.3
of 8.78. If non-stationary, at least one shift >1σ sustained over 3+ windows.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

try:
    import numpy as np
    from scipy import stats
except ImportError:
    sys.exit("requires numpy and scipy")

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "tools"))

from swarm_io import lesson_paths, read_text, session_number

SHARPE_RE = re.compile(r"Sharpe\*{0,2}:\s*(\d+)")
LESSON_RE = re.compile(r"L-(\d+)")
SESSION_RE = re.compile(r"Session:?\s*S(\d+)", re.IGNORECASE)

ERA_SIZE = 25  # sessions per era
WINDOW_SIZE = 5  # eras per rolling window


def load_lesson_data() -> list[dict]:
    """Load lesson ID, Sharpe, and session number."""
    records = []
    for path in lesson_paths():
        text = read_text(path)
        lid_m = LESSON_RE.search(path.stem)
        sharpe_m = SHARPE_RE.search(text)
        sess_m = SESSION_RE.search(text)
        if not lid_m or not sharpe_m or not sess_m:
            continue
        records.append({
            "lid": int(lid_m.group(1)),
            "sharpe": float(sharpe_m.group(1)),
            "session": int(sess_m.group(1)),
        })
    records.sort(key=lambda r: r["lid"])
    return records


def compute_era_means(records: list[dict], era_size: int = ERA_SIZE) -> list[dict]:
    """Group lessons by session era, compute mean Sharpe per era."""
    by_era: dict[int, list[float]] = defaultdict(list)
    for r in records:
        era_idx = r["session"] // era_size
        by_era[era_idx].append(r["sharpe"])

    eras = []
    for idx in sorted(by_era.keys()):
        vals = by_era[idx]
        if len(vals) < 5:  # skip tiny eras
            continue
        eras.append({
            "era_idx": idx,
            "session_start": idx * era_size,
            "session_end": (idx + 1) * era_size - 1,
            "n": len(vals),
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
        })
    return eras


def fit_ar1(series: np.ndarray) -> dict:
    """Fit AR(1) to a short series. Returns beta, lr_mean, residual_std."""
    if len(series) < 3:
        return {"beta": float("nan"), "lr_mean": float("nan"), "resid_std": float("nan")}

    y = series[1:]
    x = series[:-1]
    n = len(y)
    x_mean = x.mean()
    y_mean = y.mean()
    beta = float(np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2))
    alpha = float(y_mean - beta * x_mean)

    # Long-run mean = alpha / (1 - beta) if |beta| < 1
    if abs(beta) >= 1.0:
        lr_mean = float("nan")
    else:
        lr_mean = alpha / (1 - beta)

    resid = y - (alpha + beta * x)
    resid_std = float(np.std(resid, ddof=2)) if n > 2 else 0.0

    return {"beta": round(beta, 4), "lr_mean": round(lr_mean, 3), "resid_std": round(resid_std, 4)}


def rolling_ou_estimation(eras: list[dict], window: int = WINDOW_SIZE) -> list[dict]:
    """Fit AR(1) on rolling windows of era means."""
    means = np.array([e["mean"] for e in eras])
    results = []
    for i in range(len(means) - window + 1):
        w = means[i : i + window]
        fit = fit_ar1(w)
        results.append({
            "window_start_era": eras[i]["era_idx"],
            "window_end_era": eras[i + window - 1]["era_idx"],
            "session_range": f"S{eras[i]['session_start']}-S{eras[i + window - 1]['session_end']}",
            "era_means_in_window": [round(float(v), 3) for v in w],
            **fit,
        })
    return results


def bootstrap_lr_mean_ci(eras: list[dict], n_boot: int = 2000, ci: float = 0.95) -> dict:
    """Bootstrap confidence interval for the full-sample LR mean."""
    means = np.array([e["mean"] for e in eras])
    rng = np.random.default_rng(42)
    lr_means = []
    for _ in range(n_boot):
        idx = rng.choice(len(means), size=len(means), replace=True)
        boot_series = means[idx]
        fit = fit_ar1(boot_series)
        if not np.isnan(fit["lr_mean"]):
            lr_means.append(fit["lr_mean"])

    lr_means = np.array(lr_means)
    alpha = (1 - ci) / 2
    return {
        "lr_mean_median": round(float(np.median(lr_means)), 3),
        "lr_mean_ci_low": round(float(np.percentile(lr_means, alpha * 100)), 3),
        "lr_mean_ci_high": round(float(np.percentile(lr_means, (1 - alpha) * 100)), 3),
        "lr_mean_std": round(float(np.std(lr_means)), 3),
        "n_valid_boots": len(lr_means),
    }


def detect_structural_breaks(rolling: list[dict]) -> list[dict]:
    """Detect where rolling LR mean shifts significantly."""
    lr_means = [r["lr_mean"] for r in rolling if not np.isnan(r["lr_mean"])]
    if len(lr_means) < 3:
        return []

    arr = np.array(lr_means)
    global_mean = float(arr.mean())
    global_std = float(arr.std(ddof=1))

    breaks = []
    for i in range(1, len(arr)):
        diff = abs(arr[i] - arr[i - 1])
        z_score = diff / global_std if global_std > 0 else 0
        if z_score > 1.0:
            breaks.append({
                "index": i,
                "window": rolling[i]["session_range"] if i < len(rolling) else "?",
                "lr_mean_before": round(float(arr[i - 1]), 3),
                "lr_mean_after": round(float(arr[i]), 3),
                "change": round(float(arr[i] - arr[i - 1]), 3),
                "z_score": round(z_score, 2),
            })

    return breaks


def monotonicity_test(rolling: list[dict]) -> dict:
    """Test if LR mean shows monotonic trend (Mann-Kendall-like)."""
    lr_means = [r["lr_mean"] for r in rolling if not np.isnan(r["lr_mean"])]
    if len(lr_means) < 4:
        return {"tau": float("nan"), "p_value": float("nan")}

    tau, p = stats.kendalltau(range(len(lr_means)), lr_means)
    return {
        "tau": round(float(tau), 4),
        "p_value": round(float(p), 4),
        "direction": "increasing" if tau > 0 else "decreasing" if tau < 0 else "flat",
        "significant_005": bool(p < 0.05),
    }


def variance_ratio_test(series: np.ndarray, q: int = 2) -> float:
    """Variance ratio VR(q). VR=1 for random walk, <1 for mean reversion."""
    if len(series) < 2 * q:
        return float("nan")
    diffs1 = np.diff(series)
    diffq = series[q:] - series[:-q]
    var1 = np.var(diffs1, ddof=1)
    varq = np.var(diffq, ddof=1) / q
    return float(varq / var1) if var1 > 0 else float("nan")


def main():
    print("=== F-SP8 Attractor Non-Stationarity Test ===\n")

    # Load data
    records = load_lesson_data()
    print(f"Loaded {len(records)} lessons with Sharpe + session data")

    # Compute era means
    eras = compute_era_means(records)
    print(f"Computed {len(eras)} eras (ERA_SIZE={ERA_SIZE}, min 5 lessons/era)\n")

    for e in eras:
        print(f"  Era {e['era_idx']:2d} (S{e['session_start']:3d}-S{e['session_end']:3d}): "
              f"n={e['n']:3d}, mean={e['mean']:.3f} ± {e['std']:.3f}")

    # Full-sample AR(1)
    means = np.array([e["mean"] for e in eras])
    full_fit = fit_ar1(means)
    print(f"\nFull-sample AR(1): beta={full_fit['beta']}, LR_mean={full_fit['lr_mean']}")

    # Mature-only (skip genesis era = first era)
    if len(eras) > 2:
        mature = np.array([e["mean"] for e in eras[1:]])
        mature_fit = fit_ar1(mature)
        print(f"Mature AR(1) (skip era 0): beta={mature_fit['beta']}, LR_mean={mature_fit['lr_mean']}")

    # Rolling-window estimation
    rolling = rolling_ou_estimation(eras)
    print(f"\n--- Rolling-Window AR(1) (window={WINDOW_SIZE} eras) ---")
    for r in rolling:
        print(f"  {r['session_range']:>15s}: beta={r['beta']:+.3f}, LR_mean={r['lr_mean']:.3f}")

    # Bootstrap CI
    boot = bootstrap_lr_mean_ci(eras)
    print(f"\nBootstrap LR mean: {boot['lr_mean_median']:.3f} "
          f"[{boot['lr_mean_ci_low']:.3f}, {boot['lr_mean_ci_high']:.3f}] "
          f"(σ={boot['lr_mean_std']:.3f})")

    # Structural breaks in rolling LR mean
    breaks = detect_structural_breaks(rolling)
    print(f"\nStructural breaks (|z|>1): {len(breaks)}")
    for b in breaks:
        print(f"  {b['window']}: {b['lr_mean_before']:.3f} → {b['lr_mean_after']:.3f} "
              f"(Δ={b['change']:+.3f}, z={b['z_score']:.2f})")

    # Monotonicity test
    mono = monotonicity_test(rolling)
    print(f"\nMann-Kendall on rolling LR means: τ={mono['tau']}, p={mono['p_value']}, "
          f"direction={mono['direction']}, sig@0.05={mono['significant_005']}")

    # Variance ratio on era means
    vr2 = variance_ratio_test(means, q=2)
    vr3 = variance_ratio_test(means, q=3)
    print(f"Variance ratio: VR(2)={vr2:.3f}, VR(3)={vr3:.3f}")

    # Key findings
    lr_rolling = [r["lr_mean"] for r in rolling if not np.isnan(r["lr_mean"])]
    lr_range = max(lr_rolling) - min(lr_rolling) if lr_rolling else 0
    lr_std = float(np.std(lr_rolling)) if lr_rolling else 0

    print(f"\n=== VERDICT ===")
    print(f"Rolling LR mean range: {lr_range:.3f}")
    print(f"Rolling LR mean std: {lr_std:.3f}")
    if lr_range > 0.3:
        print(f"CONFIRMED: Attractor is NON-STATIONARY (range {lr_range:.3f} > 0.3 threshold)")
    else:
        print(f"FALSIFIED: Attractor appears STABLE (range {lr_range:.3f} ≤ 0.3 threshold)")

    if mono["significant_005"]:
        print(f"  Monotonic trend: {mono['direction']} (τ={mono['tau']}, p={mono['p_value']})")

    # Build result JSON
    result = {
        "experiment": "DOMEX-SP-S540-ATTRACTOR",
        "frontier": "F-SP8",
        "session": f"S{session_number()}",
        "domain": "stochastic-processes",
        "date": str(date.today()),
        "expect": "Rolling-window LR mean shows at least one significant shift (>1σ sustained 3+ windows). If attractor fixed, all windows cluster within ±0.3 of 8.78.",
        "actual": "",  # fill after analysis
        "diff": "",  # fill after analysis
        "data": {
            "n_lessons": len(records),
            "n_eras": len(eras),
            "era_size": ERA_SIZE,
            "window_size": WINDOW_SIZE,
            "eras": [{"idx": e["era_idx"], "S_range": f"S{e['session_start']}-S{e['session_end']}",
                       "n": e["n"], "mean": round(e["mean"], 3), "std": round(e["std"], 3)} for e in eras],
            "full_sample_ar1": full_fit,
            "mature_ar1": mature_fit if len(eras) > 2 else None,
            "rolling_windows": rolling,
            "bootstrap_ci": boot,
            "structural_breaks": breaks,
            "monotonicity_test": mono,
            "variance_ratios": {"VR2": round(vr2, 3), "VR3": round(vr3, 3)},
            "rolling_lr_range": round(lr_range, 3),
            "rolling_lr_std": round(lr_std, 3),
            "attractor_stable": lr_range <= 0.3,
        },
    }

    out_path = Path(__file__).parent / "f-sp8-attractor-shift-s540.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults written to {out_path}")

    return result


if __name__ == "__main__":
    main()
