#!/usr/bin/env python3
"""F-FLD2: Kolmogorov cascade analysis of swarm token economy.

Extends S336 static snapshot with:
1. Time-series spectral analysis (power spectrum of tier fluctuations)
2. Inter-tier flow dynamics (cross-correlations, directionality)
3. Compaction dissipation signatures
4. Growth rate scaling across tiers
5. Cascade fraction measurement (injection→dissipation transfer)

Kolmogorov cascade predicts:
- Unidirectional energy flow from large (T0) to small (T4) scales
- Power spectrum with -5/3 slope in inertial range
- Constant energy transfer rate ε across scales
- Dissipation concentrated at smallest scale
"""

import json
import math
import sys
from pathlib import Path
from collections import defaultdict

REPO = Path(__file__).resolve().parent.parent.parent
PROXY_K_LOG = REPO / "experiments" / "proxy-k-log.json"
TIERS = ["T0-mandatory", "T1-identity", "T2-protocols", "T3-knowledge", "T4-tools"]


def load_data():
    with open(PROXY_K_LOG) as f:
        raw = json.load(f)
    # Sort by session, deduplicate
    seen = set()
    data = []
    for entry in sorted(raw, key=lambda e: e.get("session", 0)):
        s = entry.get("session", 0)
        if s in seen or s == 0:
            continue
        seen.add(s)
        if "tiers" in entry and all(t in entry["tiers"] for t in TIERS):
            data.append(entry)
    return data


def compute_deltas(data):
    """Compute session-to-session tier deltas."""
    deltas = []
    for i in range(1, len(data)):
        d = {
            "session": data[i]["session"],
            "prev_session": data[i - 1]["session"],
            "session_gap": data[i]["session"] - data[i - 1]["session"],
        }
        for t in TIERS:
            d[t] = data[i]["tiers"][t] - data[i - 1]["tiers"][t]
        d["total"] = sum(d[t] for t in TIERS)
        deltas.append(d)
    return deltas


def identify_phases(deltas):
    """Classify sessions into growth (injection) and compaction (dissipation)."""
    growth = [d for d in deltas if d["total"] > 0]
    compaction = [d for d in deltas if d["total"] < 0]
    stable = [d for d in deltas if d["total"] == 0]
    return growth, compaction, stable


def tier_flow_correlations(deltas):
    """Compute pairwise correlation between tier deltas.

    Kolmogorov predicts: positive correlation in cascade direction (T0→T4)
    with lag. If tiers are independent, r≈0.
    """
    n = len(deltas)
    if n < 3:
        return {}

    results = {}
    for i, ti in enumerate(TIERS):
        for j, tj in enumerate(TIERS):
            if i >= j:
                continue
            vals_i = [d[ti] for d in deltas]
            vals_j = [d[tj] for d in deltas]
            mean_i = sum(vals_i) / n
            mean_j = sum(vals_j) / n
            cov = sum((a - mean_i) * (b - mean_j) for a, b in zip(vals_i, vals_j)) / n
            std_i = math.sqrt(sum((a - mean_i) ** 2 for a in vals_i) / n)
            std_j = math.sqrt(sum((b - mean_j) ** 2 for b in vals_j) / n)
            r = cov / (std_i * std_j) if std_i > 0 and std_j > 0 else 0
            results[f"{ti}_vs_{tj}"] = round(r, 4)
    return results


def cascade_fraction(data):
    """What fraction of total token growth ends up in each tier?

    In Kolmogorov cascade, injection scale receives energy, dissipation
    scale absorbs it. Measure: fraction of cumulative growth per tier.
    """
    if len(data) < 2:
        return {}
    first = data[0]["tiers"]
    last = data[-1]["tiers"]
    total_growth = sum(last[t] - first[t] for t in TIERS)
    if total_growth == 0:
        return {}
    fractions = {}
    for t in TIERS:
        growth = last[t] - first[t]
        fractions[t] = {
            "absolute_growth": growth,
            "fraction": round(growth / total_growth, 4),
            "start": first[t],
            "end": last[t],
            "growth_factor": round(last[t] / first[t], 2) if first[t] > 0 else None,
        }
    fractions["total_growth"] = total_growth
    fractions["session_span"] = f"S{data[0]['session']}-S{data[-1]['session']}"
    return fractions


def growth_rate_by_tier(data):
    """Measure average growth rate per tier per session.

    Kolmogorov predicts: constant energy transfer rate ε across
    inertial range tiers. Deviations indicate injection or dissipation.
    """
    if len(data) < 2:
        return {}
    session_span = data[-1]["session"] - data[0]["session"]
    if session_span == 0:
        return {}
    rates = {}
    for t in TIERS:
        growth = data[-1]["tiers"][t] - data[0]["tiers"][t]
        rate = growth / session_span
        rates[t] = {
            "tokens_per_session": round(rate, 2),
            "total_growth": growth,
            "tier_size_mean": round(
                sum(d["tiers"][t] for d in data) / len(data), 0
            ),
        }
    return rates


def compaction_tier_profile(deltas):
    """During compaction events, which tiers lose tokens?

    Kolmogorov dissipation occurs at smallest scale. If T4 loses
    most during compaction, it's behaving as dissipation scale.
    If T3 (knowledge) loses most, knowledge is the actual dissipation.
    """
    _, compaction, _ = identify_phases(deltas)
    if not compaction:
        return {"compaction_events": 0}

    tier_losses = {t: 0 for t in TIERS}
    tier_loss_counts = {t: 0 for t in TIERS}
    for d in compaction:
        for t in TIERS:
            if d[t] < 0:
                tier_losses[t] += d[t]
                tier_loss_counts[t] += 1

    total_loss = sum(tier_losses[t] for t in TIERS)
    profile = {
        "compaction_events": len(compaction),
        "total_tokens_removed": total_loss,
        "tier_profiles": {},
    }
    for t in TIERS:
        profile["tier_profiles"][t] = {
            "tokens_removed": tier_losses[t],
            "fraction_of_total_loss": (
                round(tier_losses[t] / total_loss, 4) if total_loss != 0 else 0
            ),
            "events_affected": tier_loss_counts[t],
        }
    return profile


def power_spectrum(data):
    """Compute power spectrum of total proxy-K time series.

    Kolmogorov cascade predicts E(k) ~ k^(-5/3) in inertial range.
    We use the proxy-K total series, compute DFT, measure spectral slope.

    Note: non-uniform sampling — we interpolate to uniform grid first.
    """
    if len(data) < 10:
        return {"error": "too few data points"}

    # Extract total proxy-K series
    sessions = [d["session"] for d in data]
    totals = [d["total"] for d in data]

    # Simple linear interpolation to uniform session grid
    s_min, s_max = sessions[0], sessions[-1]
    n_points = min(128, s_max - s_min + 1)
    uniform_sessions = [s_min + i * (s_max - s_min) / (n_points - 1) for i in range(n_points)]

    interp_totals = []
    for s in uniform_sessions:
        # Find bracketing sessions
        idx = 0
        while idx < len(sessions) - 1 and sessions[idx + 1] < s:
            idx += 1
        if idx >= len(sessions) - 1:
            interp_totals.append(totals[-1])
        elif sessions[idx] == s:
            interp_totals.append(totals[idx])
        else:
            frac = (s - sessions[idx]) / (sessions[idx + 1] - sessions[idx])
            val = totals[idx] + frac * (totals[idx + 1] - totals[idx])
            interp_totals.append(val)

    # Detrend (remove linear trend)
    n = len(interp_totals)
    x_mean = (n - 1) / 2
    y_mean = sum(interp_totals) / n
    sx2 = sum((i - x_mean) ** 2 for i in range(n))
    sxy = sum((i - x_mean) * (interp_totals[i] - y_mean) for i in range(n))
    slope = sxy / sx2 if sx2 > 0 else 0
    detrended = [interp_totals[i] - (slope * i + (y_mean - slope * x_mean)) for i in range(n)]

    # Compute power spectrum via DFT
    power = []
    freqs = []
    for k in range(1, n // 2):
        re = sum(detrended[j] * math.cos(2 * math.pi * k * j / n) for j in range(n))
        im = sum(detrended[j] * math.sin(2 * math.pi * k * j / n) for j in range(n))
        p = (re ** 2 + im ** 2) / n
        power.append(p)
        freqs.append(k / n)

    if not power or not any(p > 0 for p in power):
        return {"error": "zero power spectrum"}

    # Fit log-log slope (spectral exponent)
    log_f = [math.log(f) for f in freqs if f > 0]
    log_p = [math.log(p) if p > 0 else math.log(1e-10) for p, f in zip(power, freqs) if f > 0]

    if len(log_f) < 3:
        return {"error": "insufficient frequency bins"}

    n_pts = len(log_f)
    xm = sum(log_f) / n_pts
    ym = sum(log_p) / n_pts
    sx2 = sum((x - xm) ** 2 for x in log_f)
    sxy = sum((x - xm) * (y - ym) for x, y in zip(log_f, log_p))
    spectral_slope = sxy / sx2 if sx2 > 0 else 0

    # R² of log-log fit
    ss_res = sum((y - (spectral_slope * x + (ym - spectral_slope * xm))) ** 2 for x, y in zip(log_f, log_p))
    ss_tot = sum((y - ym) ** 2 for y in log_p)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    return {
        "n_points_interpolated": n,
        "n_frequency_bins": len(freqs),
        "spectral_slope": round(spectral_slope, 4),
        "kolmogorov_expected": -5 / 3,
        "r_squared": round(r_squared, 4),
        "slope_interpretation": (
            "KOLMOGOROV-LIKE" if -2.0 < spectral_slope < -1.3
            else "STEEPER (red noise / random walk)" if spectral_slope < -2.0
            else "FLATTER (white/pink noise)"
        ),
        "linear_trend_removed": round(slope, 2),
        "peak_frequency_bin": freqs[power.index(max(power))],
    }


def per_tier_spectrum(data):
    """Compute spectral slopes for each tier individually.

    If cascade-like, all tiers should share similar spectral structure
    but with amplitude decreasing from injection to dissipation scale.
    """
    if len(data) < 10:
        return {}

    sessions = [d["session"] for d in data]
    results = {}

    for tier in TIERS:
        values = [d["tiers"][tier] for d in data]

        # Simple variance and autocorrelation
        n = len(values)
        mean = sum(values) / n
        var = sum((v - mean) ** 2 for v in values) / n

        # Lag-1 autocorrelation
        if n > 1 and var > 0:
            cov1 = sum((values[i] - mean) * (values[i + 1] - mean) for i in range(n - 1)) / (n - 1)
            ac1 = cov1 / var
        else:
            ac1 = 0

        # Growth monotonicity (fraction of positive deltas)
        deltas_t = [values[i + 1] - values[i] for i in range(n - 1)]
        pos_frac = sum(1 for d in deltas_t if d > 0) / len(deltas_t) if deltas_t else 0

        # Coefficient of variation
        cv = math.sqrt(var) / mean if mean > 0 else 0

        results[tier] = {
            "mean_tokens": round(mean, 0),
            "variance": round(var, 0),
            "cv": round(cv, 4),
            "lag1_autocorrelation": round(ac1, 4),
            "growth_monotonicity": round(pos_frac, 4),
            "delta_mean": round(sum(deltas_t) / len(deltas_t), 2) if deltas_t else 0,
            "delta_std": round(math.sqrt(sum((d - sum(deltas_t)/len(deltas_t))**2 for d in deltas_t) / len(deltas_t)), 2) if deltas_t else 0,
        }

    return results


def era_analysis(data):
    """Split into pre/post domain-seeding eras (S186 boundary).

    S186 was a major structural change (domain seeding). Check if
    cascade properties differ between eras.
    """
    pre = [d for d in data if d["session"] < 186]
    post = [d for d in data if d["session"] >= 186]

    def tier_shares(entries):
        if not entries:
            return {}
        shares = {t: 0 for t in TIERS}
        for e in entries:
            total = e.get("total", sum(e["tiers"].values()))
            for t in TIERS:
                shares[t] += e["tiers"][t] / total
        return {t: round(shares[t] / len(entries), 4) for t in TIERS}

    return {
        "pre_S186": {
            "n": len(pre),
            "session_range": f"S{pre[0]['session']}-S{pre[-1]['session']}" if pre else "none",
            "mean_total": round(sum(d.get("total", sum(d["tiers"].values())) for d in pre) / len(pre)) if pre else 0,
            "tier_shares": tier_shares(pre),
        },
        "post_S186": {
            "n": len(post),
            "session_range": f"S{post[0]['session']}-S{post[-1]['session']}" if post else "none",
            "mean_total": round(sum(d.get("total", sum(d["tiers"].values())) for d in post) / len(post)) if post else 0,
            "tier_shares": tier_shares(post),
        },
    }


def cascade_test_battery(data, deltas):
    """Run 5 Kolmogorov cascade criteria and score each."""
    tests = {}

    # Test 1: Unidirectional flow (T0→T4 growth fraction increases with tier)
    cf = cascade_fraction(data)
    if cf and "total_growth" in cf:
        fracs = [cf[t]["fraction"] for t in TIERS if t in cf]
        monotonic_increasing = all(fracs[i] <= fracs[i + 1] for i in range(len(fracs) - 1))
        tests["T1_unidirectional_flow"] = {
            "criterion": "Growth fraction increases from T0→T4 (energy flows to small scale)",
            "fractions": {t: cf[t]["fraction"] for t in TIERS if t in cf},
            "monotonic": monotonic_increasing,
            "verdict": "CONFIRMED" if monotonic_increasing else "FALSIFIED",
        }

    # Test 2: Spectral slope near -5/3
    ps = power_spectrum(data)
    if "spectral_slope" in ps:
        slope = ps["spectral_slope"]
        near_kolmogorov = -2.2 < slope < -1.2
        tests["T2_spectral_slope"] = {
            "criterion": "Spectral slope near -5/3 (-1.667) in detrended series",
            "measured_slope": slope,
            "expected": -5 / 3,
            "r_squared": ps.get("r_squared", 0),
            "verdict": "CONFIRMED" if near_kolmogorov else "FALSIFIED",
        }

    # Test 3: Inter-tier correlation (cascade = correlated flow)
    corrs = tier_flow_correlations(deltas)
    if corrs:
        adjacent_corrs = []
        for i in range(len(TIERS) - 1):
            key = f"{TIERS[i]}_vs_{TIERS[i + 1]}"
            if key in corrs:
                adjacent_corrs.append(corrs[key])
        mean_adj_corr = sum(adjacent_corrs) / len(adjacent_corrs) if adjacent_corrs else 0
        tests["T3_intertier_correlation"] = {
            "criterion": "Adjacent tier deltas are positively correlated (cascade coupling)",
            "adjacent_correlations": {
                f"{TIERS[i]}→{TIERS[i+1]}": corrs.get(f"{TIERS[i]}_vs_{TIERS[i+1]}", 0)
                for i in range(len(TIERS) - 1)
            },
            "mean_adjacent_r": round(mean_adj_corr, 4),
            "verdict": "CONFIRMED" if mean_adj_corr > 0.1 else "FALSIFIED",
        }

    # Test 4: Compaction dissipation at T4 (smallest scale)
    cp = compaction_tier_profile(deltas)
    if cp.get("compaction_events", 0) > 0:
        t4_frac = cp["tier_profiles"]["T4-tools"]["fraction_of_total_loss"]
        tests["T4_dissipation_at_T4"] = {
            "criterion": "Compaction (dissipation) concentrated at T4 (smallest scale)",
            "T4_loss_fraction": t4_frac,
            "compaction_events": cp["compaction_events"],
            "verdict": "CONFIRMED" if t4_frac > 0.4 else "FALSIFIED",
        }

    # Test 5: Constant transfer rate (growth rate similar across inertial tiers T1-T3)
    rates = growth_rate_by_tier(data)
    if rates:
        inertial_rates = [rates[t]["tokens_per_session"] for t in ["T1-identity", "T2-protocols", "T3-knowledge"]]
        if all(r != 0 for r in inertial_rates):
            rate_cv = (
                math.sqrt(sum((r - sum(inertial_rates)/3)**2 for r in inertial_rates) / 3)
                / abs(sum(inertial_rates) / 3)
            ) if sum(inertial_rates) != 0 else float("inf")
        else:
            rate_cv = float("inf")
        tests["T5_constant_transfer_rate"] = {
            "criterion": "Inertial range (T1-T3) growth rates are similar (constant ε)",
            "growth_rates": {t: rates[t]["tokens_per_session"] for t in TIERS},
            "inertial_cv": round(rate_cv, 4),
            "verdict": "CONFIRMED" if rate_cv < 0.5 else "FALSIFIED",
        }

    # Overall score
    confirmed = sum(1 for t in tests.values() if t["verdict"] == "CONFIRMED")
    total = len(tests)
    tests["_summary"] = {
        "confirmed": confirmed,
        "total": total,
        "score": f"{confirmed}/{total}",
        "overall_verdict": (
            "CONFIRMED" if confirmed >= 4
            else "PARTIALLY_CONFIRMED" if confirmed >= 2
            else "FALSIFIED"
        ),
    }
    return tests


def main():
    data = load_data()
    print(f"Loaded {len(data)} proxy-K measurements (S{data[0]['session']}-S{data[-1]['session']})")

    deltas = compute_deltas(data)
    growth, compaction, stable = identify_phases(deltas)
    print(f"Phases: {len(growth)} growth, {len(compaction)} compaction, {len(stable)} stable")

    # Run all analyses
    results = {
        "experiment": "F-FLD2 Kolmogorov Cascade — Dynamic Analysis",
        "session": "S389",
        "frontier": "F-FLD2",
        "n_measurements": len(data),
        "session_range": f"S{data[0]['session']}-S{data[-1]['session']}",
        "prior_work": "S336 static snapshot: slope 0.619 vs expected 1.667. T4 absorbing state.",
        "method": "5-test cascade battery: (1) unidirectional flow, (2) spectral slope, (3) inter-tier correlation, (4) dissipation at T4, (5) constant transfer rate",
    }

    print("\n--- Cascade Test Battery ---")
    tests = cascade_test_battery(data, deltas)
    results["cascade_tests"] = tests
    for name, test in tests.items():
        if name.startswith("_"):
            print(f"\n  OVERALL: {test['score']} — {test['overall_verdict']}")
        else:
            print(f"  {name}: {test['verdict']}")
            if "measured_slope" in test:
                print(f"    slope={test['measured_slope']:.3f} (expected {test['expected']:.3f})")
            if "mean_adjacent_r" in test:
                print(f"    mean_adjacent_r={test['mean_adjacent_r']:.3f}")

    print("\n--- Power Spectrum ---")
    ps = power_spectrum(data)
    results["power_spectrum"] = ps
    print(f"  slope={ps.get('spectral_slope', 'N/A')}, R²={ps.get('r_squared', 'N/A')}")
    print(f"  interpretation: {ps.get('slope_interpretation', 'N/A')}")

    print("\n--- Cascade Fraction (injection → dissipation) ---")
    cf = cascade_fraction(data)
    results["cascade_fraction"] = cf
    for t in TIERS:
        if t in cf:
            print(f"  {t}: {cf[t]['fraction']*100:.1f}% of growth ({cf[t]['growth_factor']}x)")

    print("\n--- Inter-tier Flow Correlations ---")
    corrs = tier_flow_correlations(deltas)
    results["flow_correlations"] = corrs
    for pair, r in sorted(corrs.items()):
        marker = "***" if abs(r) > 0.3 else ""
        print(f"  {pair}: r={r:.3f} {marker}")

    print("\n--- Per-Tier Dynamics ---")
    pts = per_tier_spectrum(data)
    results["per_tier_dynamics"] = pts
    for t in TIERS:
        if t in pts:
            d = pts[t]
            print(f"  {t}: mean={d['mean_tokens']:.0f}t, CV={d['cv']:.3f}, "
                  f"AC1={d['lag1_autocorrelation']:.3f}, mono={d['growth_monotonicity']:.2f}")

    print("\n--- Compaction Dissipation Profile ---")
    cp = compaction_tier_profile(deltas)
    results["compaction_profile"] = cp
    if cp.get("compaction_events", 0) > 0:
        for t in TIERS:
            tp = cp["tier_profiles"][t]
            print(f"  {t}: {tp['tokens_removed']}t ({tp['fraction_of_total_loss']*100:.1f}%) "
                  f"in {tp['events_affected']}/{cp['compaction_events']} events")

    print("\n--- Growth Rates ---")
    gr = growth_rate_by_tier(data)
    results["growth_rates"] = gr
    for t in TIERS:
        if t in gr:
            print(f"  {t}: {gr[t]['tokens_per_session']:.1f} t/session")

    print("\n--- Era Analysis (pre/post S186 domain-seeding) ---")
    ea = era_analysis(data)
    results["era_analysis"] = ea
    for era_name, era_data in ea.items():
        print(f"  {era_name}: n={era_data['n']}, mean_total={era_data['mean_total']}t")
        for t in TIERS:
            if t in era_data.get("tier_shares", {}):
                print(f"    {t}: {era_data['tier_shares'][t]*100:.1f}%")

    # Write results
    out_path = REPO / "experiments" / "fluid-dynamics" / "f-fld2-token-cascade-s389.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nArtifact written: {out_path.relative_to(REPO)}")

    return results


if __name__ == "__main__":
    main()
