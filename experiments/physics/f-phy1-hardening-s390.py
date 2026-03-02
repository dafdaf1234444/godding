"""F-PHY1 Hardening: Formal phase-transition tests on proxy-K deltas.

Prior work (S246, S351): qualitative "punctuated dynamics confirmed" (n=54).
This session: formal statistical tests to harden the claim.

Tests:
  1. Shapiro-Wilk normality test on |deltas|
  2. Kurtosis (excess kurtosis > 0 = heavier than normal)
  3. Distribution fit comparison: normal vs exponential vs log-normal
  4. Change-point detection (CUSUM on cumulative sum of deltas)
  5. Structural correlate identification for top-5 transitions
"""

import json
import sys
import numpy as np
from scipy import stats

def load_data():
    with open("experiments/proxy-k-log.json") as f:
        data = json.load(f)
    sessions = []
    for r in data:
        sessions.append({"session": r["session"], "total": r["total"]})
    sessions.sort(key=lambda x: x["session"])
    return sessions

def compute_deltas(sessions):
    deltas = []
    for i in range(1, len(sessions)):
        d = sessions[i]["total"] - sessions[i-1]["total"]
        deltas.append({
            "from_session": sessions[i-1]["session"],
            "to_session": sessions[i]["session"],
            "delta": d,
            "abs_delta": abs(d),
            "pct_change": d / sessions[i-1]["total"] * 100 if sessions[i-1]["total"] > 0 else 0
        })
    return deltas

def test_normality(abs_deltas):
    """Shapiro-Wilk test: H0 = data is normally distributed."""
    stat, p = stats.shapiro(abs_deltas)
    return {"test": "Shapiro-Wilk", "statistic": round(stat, 4), "p_value": round(p, 6),
            "reject_normal_at_005": p < 0.05, "interpretation": "NOT normal" if p < 0.05 else "consistent with normal"}

def test_kurtosis(abs_deltas):
    """Excess kurtosis: >0 = heavier tails than normal, <0 = lighter."""
    k = stats.kurtosis(abs_deltas, fisher=True)
    skew = stats.skew(abs_deltas)
    return {"excess_kurtosis": round(k, 3), "skewness": round(skew, 3),
            "heavy_tailed": k > 0, "interpretation": f"{'heavy' if k > 0 else 'light'}-tailed (kurtosis={k:.2f})"}

def test_distribution_fits(abs_deltas):
    """Compare normal, exponential, and log-normal fits via AIC."""
    results = {}

    # Normal fit
    mu, sigma = stats.norm.fit(abs_deltas)
    ll_norm = np.sum(stats.norm.logpdf(abs_deltas, mu, sigma))
    aic_norm = 2 * 2 - 2 * ll_norm  # 2 params
    results["normal"] = {"mu": round(mu, 1), "sigma": round(sigma, 1), "loglik": round(ll_norm, 2), "AIC": round(aic_norm, 2)}

    # Exponential fit
    loc, scale = stats.expon.fit(abs_deltas, floc=0)
    ll_exp = np.sum(stats.expon.logpdf(abs_deltas, loc, scale))
    aic_exp = 2 * 1 - 2 * ll_exp  # 1 param (rate)
    results["exponential"] = {"scale": round(scale, 1), "loglik": round(ll_exp, 2), "AIC": round(aic_exp, 2)}

    # Log-normal fit
    pos_deltas = abs_deltas[abs_deltas > 0]
    if len(pos_deltas) > 5:
        shape, loc, scale = stats.lognorm.fit(pos_deltas, floc=0)
        ll_ln = np.sum(stats.lognorm.logpdf(pos_deltas, shape, loc, scale))
        aic_ln = 2 * 2 - 2 * ll_ln  # 2 params
        results["lognormal"] = {"shape": round(shape, 3), "scale": round(scale, 1),
                                "loglik": round(ll_ln, 2), "AIC": round(aic_ln, 2), "n": len(pos_deltas)}

    # Rank by AIC
    best = min(results.items(), key=lambda x: x[1]["AIC"])
    results["best_fit"] = best[0]
    results["delta_AIC"] = {k: round(v["AIC"] - best[1]["AIC"], 2) for k, v in results.items() if k != "best_fit"}

    return results

def cusum_changepoints(deltas_raw, threshold_sigma=2.0):
    """CUSUM change-point detection on raw deltas."""
    arr = np.array(deltas_raw)
    mu = np.mean(arr)
    sigma = np.std(arr)
    cusum_pos = np.zeros(len(arr))
    cusum_neg = np.zeros(len(arr))
    changepoints = []

    for i in range(1, len(arr)):
        cusum_pos[i] = max(0, cusum_pos[i-1] + (arr[i] - mu) / sigma)
        cusum_neg[i] = min(0, cusum_neg[i-1] + (arr[i] - mu) / sigma)
        if cusum_pos[i] > threshold_sigma or cusum_neg[i] < -threshold_sigma:
            changepoints.append(i)
            cusum_pos[i] = 0
            cusum_neg[i] = 0

    return {"n_changepoints": len(changepoints), "indices": changepoints,
            "threshold_sigma": threshold_sigma, "mean_delta": round(mu, 1), "std_delta": round(sigma, 1)}

def structural_correlates(deltas, n_top=5):
    """Identify structural correlates for top transitions by cross-referencing known events."""
    known_events = {
        (181, 182): "Domain seeding burst (S182: first domain frontiers)",
        (182, 186): "Post-domain-seeding consolidation / compaction",
        (126, 127): "Major compaction event (early era)",
        (329, 331): "Citation sprint / structural enforcement era",
        (335, 337): "Quality gate enforcement + multi-concept dispatch",
        (347, 348): "N>=10 concurrency era begins",
        (354, 355): "Bridge sync + contract_check.py (F-META8)",
        (383, 384): "Compaction session (proxy-K floor reset)",
    }

    sorted_by_abs = sorted(deltas, key=lambda d: d["abs_delta"], reverse=True)
    top = sorted_by_abs[:n_top]

    results = []
    for d in top:
        key = (d["from_session"], d["to_session"])
        correlate = known_events.get(key, "unknown — requires git log investigation")
        # Check nearby keys too
        if correlate.startswith("unknown"):
            for (s1, s2), desc in known_events.items():
                if abs(d["from_session"] - s1) <= 2:
                    correlate = f"near {desc} (±2 sessions)"
                    break
        results.append({
            "from_session": d["from_session"],
            "to_session": d["to_session"],
            "delta": d["delta"],
            "pct_change": round(d["pct_change"], 2),
            "correlate": correlate
        })
    return results

def main():
    sessions = load_data()
    deltas = compute_deltas(sessions)
    abs_deltas = np.array([d["abs_delta"] for d in deltas])
    raw_deltas = np.array([d["delta"] for d in deltas])

    print(f"=== F-PHY1 Hardening Tests ===")
    print(f"N sessions: {len(sessions)}, N deltas: {len(deltas)}")
    print(f"Abs delta: median={np.median(abs_deltas):.0f}, mean={np.mean(abs_deltas):.0f}, "
          f"p90={np.percentile(abs_deltas, 90):.0f}, max={np.max(abs_deltas):.0f}")
    print()

    # Test 1: Normality
    norm = test_normality(abs_deltas)
    print(f"T1 Shapiro-Wilk: W={norm['statistic']}, p={norm['p_value']} → {norm['interpretation']}")

    # Test 2: Kurtosis
    kurt = test_kurtosis(abs_deltas)
    print(f"T2 Kurtosis: excess={kurt['excess_kurtosis']}, skew={kurt['skewness']} → {kurt['interpretation']}")

    # Test 3: Distribution fits
    fits = test_distribution_fits(abs_deltas)
    print(f"T3 Best fit: {fits['best_fit']} (ΔAIC: {fits['delta_AIC']})")

    # Test 4: CUSUM changepoints
    cusum = cusum_changepoints(raw_deltas)
    print(f"T4 CUSUM: {cusum['n_changepoints']} changepoints detected (threshold={cusum['threshold_sigma']}σ)")

    # Test 5: Top-5 structural correlates
    top5 = structural_correlates(deltas)
    print(f"T5 Top-5 transitions:")
    for t in top5:
        direction = "+" if t["delta"] > 0 else ""
        print(f"   S{t['from_session']}→S{t['to_session']}: {direction}{t['delta']}t ({t['pct_change']}%) — {t['correlate']}")

    # K-S test: compare |deltas| to exponential distribution
    ks_stat, ks_p = stats.kstest(abs_deltas, 'expon', args=(0, np.mean(abs_deltas)))
    print(f"\nK-S vs exponential: D={ks_stat:.4f}, p={ks_p:.4f}")

    # Anderson-Darling normality test (more powerful for tails)
    ad_result = stats.anderson(abs_deltas, dist='norm')
    print(f"Anderson-Darling (normal): stat={ad_result.statistic:.4f}, "
          f"5% critical={ad_result.critical_values[2]:.4f} → "
          f"{'REJECT normal' if ad_result.statistic > ad_result.critical_values[2] else 'cannot reject'}")

    # Summary verdict
    tests_passed = 0
    total_tests = 5
    verdicts = []

    if norm["reject_normal_at_005"]:
        tests_passed += 1
        verdicts.append("T1: NOT normal (p<0.05)")
    else:
        verdicts.append("T1: consistent with normal — FAILS punctuated claim")

    if kurt["heavy_tailed"]:
        tests_passed += 1
        verdicts.append(f"T2: heavy-tailed (kurtosis={kurt['excess_kurtosis']})")
    else:
        verdicts.append(f"T2: NOT heavy-tailed — FAILS punctuated claim")

    if fits["best_fit"] != "normal":
        tests_passed += 1
        verdicts.append(f"T3: best fit is {fits['best_fit']}, not normal")
    else:
        verdicts.append("T3: normal is best fit — FAILS punctuated claim")

    if cusum["n_changepoints"] >= 3:
        tests_passed += 1
        verdicts.append(f"T4: {cusum['n_changepoints']} changepoints = regime shifts")
    else:
        verdicts.append(f"T4: only {cusum['n_changepoints']} changepoints — weak evidence")

    correlated = sum(1 for t in top5 if "unknown" not in t["correlate"])
    if correlated >= 3:
        tests_passed += 1
        verdicts.append(f"T5: {correlated}/5 top transitions have structural correlates")
    else:
        verdicts.append(f"T5: only {correlated}/5 correlated — needs investigation")

    overall = "CONFIRMED" if tests_passed >= 4 else "PARTIALLY CONFIRMED" if tests_passed >= 3 else "WEAKENED"
    print(f"\n=== VERDICT: {tests_passed}/{total_tests} tests support punctuated dynamics → {overall} ===")
    for v in verdicts:
        print(f"  {v}")

    # Build artifact
    artifact = {
        "experiment": "f-phy1-hardening-s390",
        "session": "S390",
        "date": "2026-03-01",
        "frontier": "F-PHY1",
        "cross_links": ["F-PHY4", "ISO-4", "ISO-6", "ISO-8", "L-428", "L-551"],
        "question": "Do proxy-K totals show punctuated jumps/drops (phase-transition-like) rather than smooth drift?",
        "method": "5-test hardening battery: Shapiro-Wilk, kurtosis, distribution fit comparison, CUSUM changepoints, structural correlates",
        "mode": "hardening",
        "n_sessions": len(sessions),
        "n_deltas": len(deltas),
        "descriptive_stats": {
            "abs_delta_median": round(float(np.median(abs_deltas)), 1),
            "abs_delta_mean": round(float(np.mean(abs_deltas)), 1),
            "abs_delta_p90": round(float(np.percentile(abs_deltas, 90)), 1),
            "abs_delta_max": int(np.max(abs_deltas)),
            "raw_delta_mean": round(float(np.mean(raw_deltas)), 1),
            "raw_delta_std": round(float(np.std(raw_deltas)), 1),
        },
        "tests": {
            "T1_normality": norm,
            "T2_kurtosis": kurt,
            "T3_distribution_fits": fits,
            "T4_cusum_changepoints": cusum,
            "T5_structural_correlates": top5,
            "supplementary": {
                "ks_vs_exponential": {"D": round(ks_stat, 4), "p": round(ks_p, 4)},
                "anderson_darling": {"statistic": round(ad_result.statistic, 4),
                                     "critical_5pct": round(ad_result.critical_values[2], 4),
                                     "reject_normal": bool(ad_result.statistic > ad_result.critical_values[2])}
            }
        },
        "verdict": {
            "tests_passed": tests_passed,
            "total_tests": total_tests,
            "overall": overall,
            "verdicts": verdicts
        },
        "prior_work": {
            "S246": "Baseline — qualitative punctuated (n=48, median |delta|=692)",
            "S351": "Advanced — 5 transition candidates (n=54), punctuated CONFIRMED qualitatively",
            "S390": f"Hardening — formal {total_tests}-test battery (n={len(deltas)}), {overall}"
        }
    }

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    with open("experiments/physics/f-phy1-hardening-s390.json", "w") as f:
        json.dump(artifact, f, indent=2, cls=NumpyEncoder)
    print(f"\nArtifact written: experiments/physics/f-phy1-hardening-s390.json")

    return artifact

if __name__ == "__main__":
    main()
