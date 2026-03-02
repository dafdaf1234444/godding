#!/usr/bin/env python3
"""bayes_meta.py — Bayesian meta-analysis for swarm belief updating.

Computes formal Bayesian posteriors for frontier hypotheses by aggregating
evidence across experiment JSON artifacts. Provides meta-level calibration
diagnostics, publication-bias checks, and replication consistency analysis.

Framework:
  - Prior P(H) = empirical base rate (or 0.5 uninformative)
  - Bayes factors: CONFIRMED=10, PARTIAL=3, NULL=1, FALSIFIED=0.1
  - Sequential update per frontier; pooling across related frontiers
  - Meta diagnostics: calibration, evidence Gini, domain posteriors

Usage:
    python3 tools/bayes_meta.py                   # full report
    python3 tools/bayes_meta.py --json            # machine-readable
    python3 tools/bayes_meta.py --frontier F-BRN2  # single frontier trace
    python3 tools/bayes_meta.py --domain meta     # domain-level view
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
FRONTIER_FILE = REPO_ROOT / "tasks" / "FRONTIER.md"
FRONTIER_ARCHIVE = REPO_ROOT / "tasks" / "FRONTIER-ARCHIVE.md"

# --- Bayes factors by verdict class ---
BAYES_FACTORS = {
    "CONFIRMED": 10.0,
    "PARTIAL": 3.0,
    "NULL": 1.0,
    "FALSIFIED": 0.1,
    "UNCLEAR": 1.0,  # no update if unclassifiable
}

# Quality → weight mapping (higher quality experiments carry more evidential weight)
QUALITY_WEIGHTS = {0.0: 0.5, 0.2: 0.75, 0.4: 1.0, 0.6: 1.25, 0.8: 1.5, 1.0: 2.0}


def classify_verdict(verdict: str) -> str:
    """Map raw verdict text to one of CONFIRMED/PARTIAL/NULL/FALSIFIED/UNCLEAR."""
    if not verdict or verdict == "None":
        return "UNCLEAR"
    vl = verdict.lower()
    # Falsification takes priority
    if any(x in vl for x in ["falsified", "rejected", "refuted", "disproved",
                               "failed", "wrong if", "not confirmed"]):
        return "FALSIFIED"
    # Confirmed but with qualifiers → PARTIAL
    if any(x in vl for x in ["confirmed", "resolved", "implemented", "complete",
                               "yes —", "yes,", "done —"]):
        if any(x in vl for x in ["partial", "mostly", "not fully", "not resolved",
                                   "partially", "conditionally", "with adjustment",
                                   "with caveat", "mixed"]):
            return "PARTIAL"
        return "CONFIRMED"
    # Partial/mixed evidence
    if any(x in vl for x in ["partial", "mostly", "mixed", "inconclusive",
                               "not resolved", "unstable", "mostly_resolved",
                               "partially resolved", "partially_resolved"]):
        return "PARTIAL"
    # Null findings
    if any(x in vl for x in ["null", "no effect", "no significant", "not resolved",
                               "no evidence", "abandoned", "moot"]):
        return "NULL"
    return "UNCLEAR"


def score_quality(data: dict) -> float:
    """Simple quality proxy: 0-1 based on presence of key science fields."""
    text = json.dumps(data, default=str).lower()
    score = 0.0
    if re.search(r"\d", str(data.get("expect", data.get("hypothesis", "")))):
        score += 0.2
    if any(kw in text for kw in ("baseline", "control", "before", "comparison")):
        score += 0.2
    if any(kw in text for kw in ("p-value", "p<", "bic", "effect size", "r²", "bootstrap")):
        score += 0.2
    if any(kw in text for kw in ("external", "independent", "non-swarm", "benchmark")):
        score += 0.2
    if any(kw in text for kw in ("falsified if", "falsification", "conditions for failure")):
        score += 0.2
    return round(score, 1)


def get_quality_weight(quality: float) -> float:
    """Interpolate quality → BF weight."""
    keys = sorted(QUALITY_WEIGHTS.keys())
    for i, k in enumerate(keys[:-1]):
        if quality <= keys[i + 1]:
            t = (quality - k) / (keys[i + 1] - k) if keys[i + 1] != k else 0
            return QUALITY_WEIGHTS[k] + t * (QUALITY_WEIGHTS[keys[i + 1]] - QUALITY_WEIGHTS[k])
    return QUALITY_WEIGHTS[1.0]


def bayesian_update(prior: float, bf: float, weight: float = 1.0) -> float:
    """Sequential Bayes update. Weight adjusts BF on log scale."""
    weighted_bf = bf ** weight
    prior_odds = prior / (1 - prior) if prior < 1.0 else 1e9
    posterior_odds = prior_odds * weighted_bf
    return posterior_odds / (1 + posterior_odds)


def extract_domain(frontier: str) -> str:
    """Extract domain from frontier ID like F-BRN2 → brn, F119 → generic."""
    m = re.match(r"F-([A-Z]+)\d*", frontier)
    if m:
        return m.group(1).lower()
    return "generic"


def load_experiments() -> list[dict]:
    """Load all experiment JSONs, extracting frontier, verdict, quality, session."""
    experiments = []
    skip_patterns = ["cache", "evolution", "frontier-claims", "evolution-plan"]
    for f in sorted(EXPERIMENTS_DIR.rglob("*.json")):
        if any(p in f.name for p in skip_patterns):
            continue
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        frontier = data.get("frontier", data.get("lane", ""))
        # Handle list values (some experiments have list fields)
        if isinstance(frontier, list):
            frontier = frontier[0] if frontier else ""
        frontier = str(frontier) if frontier else ""
        # Normalize: extract frontier ID from lane strings like DOMEX-BRN-S407
        if frontier and not re.match(r"^F[- ]", frontier):
            # Try to extract from file path or domain dir
            m = re.search(r"f-([\w-]+)-s\d+", f.stem)
            if m:
                frontier = ""  # can't reliably map without explicit field
            else:
                frontier = ""
        raw_verdict = str(data.get("verdict",
                          data.get("result",
                          data.get("outcome",
                          data.get("overall_verdict", "")))))
        verdict_class = classify_verdict(raw_verdict)
        quality = score_quality(data)
        session_num = 0
        m = re.search(r"[sS](\d+)", f.stem)
        if m:
            session_num = int(m.group(1))
        elif "session" in data:
            m2 = re.search(r"\d+", str(data["session"]))
            session_num = int(m2.group()) if m2 else 0
        if frontier:
            experiments.append({
                "frontier": frontier,
                "verdict": verdict_class,
                "raw_verdict": raw_verdict[:120],
                "quality": quality,
                "session": session_num,
                "file": str(f.relative_to(REPO_ROOT)),
            })
    return experiments


def compute_empirical_prior(experiments: list[dict]) -> float:
    """Estimate base rate P(H=true) from resolved experiments."""
    resolved = [e for e in experiments if e["verdict"] in ("CONFIRMED", "PARTIAL", "FALSIFIED")]
    if not resolved:
        return 0.5
    # PARTIAL counts as 0.5 evidence for H=true
    support = sum(1.0 if e["verdict"] == "CONFIRMED" else
                  0.5 if e["verdict"] == "PARTIAL" else
                  0.0 for e in resolved)
    return support / len(resolved)


def compute_frontier_posteriors(
    experiments: list[dict], base_prior: float = 0.5, quality_weighted: bool = True
) -> dict[str, dict]:
    """Compute sequential Bayesian posterior for each frontier."""
    by_frontier = defaultdict(list)
    for e in experiments:
        if e["frontier"] and e["verdict"] != "UNCLEAR":
            by_frontier[e["frontier"]].append(e)

    posteriors = {}
    for frontier, exps in by_frontier.items():
        # Sort chronologically
        exps_sorted = sorted(exps, key=lambda x: x["session"])
        prior = base_prior
        trace = []
        for e in exps_sorted:
            bf = BAYES_FACTORS[e["verdict"]]
            weight = get_quality_weight(e["quality"]) if quality_weighted else 1.0
            posterior = bayesian_update(prior, bf, weight)
            trace.append({
                "session": e["session"],
                "verdict": e["verdict"],
                "bf": bf,
                "weight": round(weight, 2),
                "prior": round(prior, 3),
                "posterior": round(posterior, 3),
            })
            prior = posterior

        final_p = round(prior, 3)
        # L-909 replication gate: cap posterior at 0.85 with <3 experiments
        replication_capped = False
        if len(exps_sorted) < 3 and final_p > 0.85:
            final_p = 0.85
            replication_capped = True
        if final_p >= 0.8:
            conclusion = "STRONG CONFIRM"
        elif final_p >= 0.65:
            conclusion = "MODERATE CONFIRM"
        elif final_p >= 0.35:
            conclusion = "UNCERTAIN"
        elif final_p >= 0.2:
            conclusion = "MODERATE DOUBT"
        else:
            conclusion = "STRONG DOUBT"

        posteriors[frontier] = {
            "domain": extract_domain(frontier),
            "prior": round(base_prior, 3),
            "posterior": final_p,
            "n_experiments": len(exps_sorted),
            "verdict_counts": {
                "CONFIRMED": sum(1 for e in exps if e["verdict"] == "CONFIRMED"),
                "PARTIAL": sum(1 for e in exps if e["verdict"] == "PARTIAL"),
                "FALSIFIED": sum(1 for e in exps if e["verdict"] == "FALSIFIED"),
            },
            "mean_quality": round(sum(e["quality"] for e in exps) / len(exps), 2),
            "conclusion": conclusion,
            "replication_capped": replication_capped,
            "trace": trace,
        }
    return posteriors


def compute_calibration(posteriors: dict[str, dict]) -> dict:
    """Compute calibration: bin posteriors and measure actual confirmation rate.

    Uses crude ground-truth: CONFIRMED verdicts in last experiment = 'actually true'.
    This is imperfect but gives a calibration signal.
    """
    bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
    bin_data = defaultdict(lambda: {"n": 0, "confirmed": 0, "mean_p": 0.0, "sum_p": 0.0})

    for frontier, data in posteriors.items():
        p = data["posterior"]
        vc = data["verdict_counts"]
        total = sum(vc.values())
        # Crude 'actual truth': fraction that were CONFIRMED
        actual = (vc["CONFIRMED"] + 0.5 * vc["PARTIAL"]) / total if total > 0 else 0.5
        for lo, hi in bins:
            if lo <= p < hi or (p == 1.0 and hi == 1.0):
                key = f"{lo:.1f}-{hi:.1f}"
                bin_data[key]["n"] += 1
                bin_data[key]["sum_p"] += p
                bin_data[key]["confirmed"] += actual
                break

    calibration = {}
    for key in sorted(bin_data.keys()):
        d = bin_data[key]
        if d["n"] > 0:
            calibration[key] = {
                "n": d["n"],
                "mean_predicted_p": round(d["sum_p"] / d["n"], 3),
                "mean_actual_rate": round(d["confirmed"] / d["n"], 3),
                "calibration_error": round(abs(d["sum_p"] / d["n"] - d["confirmed"] / d["n"]), 3),
            }
    return calibration


def gini_coefficient(values: list[float]) -> float:
    """Compute Gini coefficient for evidence concentration."""
    if not values or sum(values) == 0:
        return 0.0
    n = len(values)
    values_sorted = sorted(values)
    cumsum = 0.0
    for i, v in enumerate(values_sorted):
        cumsum += (2 * (i + 1) - n - 1) * v
    return cumsum / (n * sum(values_sorted))


def compute_domain_summary(posteriors: dict[str, dict]) -> dict[str, dict]:
    """Aggregate posteriors by domain."""
    by_domain = defaultdict(list)
    for frontier, data in posteriors.items():
        by_domain[data["domain"]].append(data)

    summary = {}
    for domain, items in sorted(by_domain.items(), key=lambda x: -len(x[1])):
        posteriors_list = [d["posterior"] for d in items]
        n_exps = [d["n_experiments"] for d in items]
        summary[domain] = {
            "n_frontiers": len(items),
            "total_experiments": sum(n_exps),
            "mean_posterior": round(sum(posteriors_list) / len(posteriors_list), 3),
            "evidence_gini": round(gini_coefficient(n_exps), 3),
            "strong_confirm": sum(1 for d in items if d["posterior"] >= 0.8),
            "strong_doubt": sum(1 for d in items if d["posterior"] <= 0.2),
        }
    return summary


def check_publication_bias(experiments: list[dict]) -> dict:
    """Check if quality correlates with confirmation (publication bias indicator).

    A positive correlation quality→CONFIRMED suggests high-quality experiments
    are not run on null results — a form of selection bias.
    """
    classified = [e for e in experiments if e["verdict"] in ("CONFIRMED", "PARTIAL", "FALSIFIED")]
    if len(classified) < 10:
        return {"status": "insufficient data", "n": len(classified)}

    qualities = [e["quality"] for e in classified]
    confirmed_binary = [1.0 if e["verdict"] == "CONFIRMED" else
                        0.5 if e["verdict"] == "PARTIAL" else 0.0 for e in classified]

    # Pearson correlation
    n = len(qualities)
    mean_q = sum(qualities) / n
    mean_c = sum(confirmed_binary) / n
    num = sum((q - mean_q) * (c - mean_c) for q, c in zip(qualities, confirmed_binary))
    den_q = (sum((q - mean_q) ** 2 for q in qualities)) ** 0.5
    den_c = (sum((c - mean_c) ** 2 for c in confirmed_binary)) ** 0.5
    r = num / (den_q * den_c) if den_q * den_c > 0 else 0.0

    return {
        "n": n,
        "r_quality_confirmed": round(r, 3),
        "interpretation": (
            "BIAS DETECTED: high-quality experiments favor confirmation" if r > 0.2 else
            "NEUTRAL: quality does not predict confirmation" if abs(r) <= 0.2 else
            "COUNTER-BIAS: high-quality experiments more likely to falsify"
        ),
    }


def replication_consistency(posteriors: dict[str, dict]) -> list[dict]:
    """Identify frontiers with inconsistent evidence across experiments."""
    inconsistent = []
    for frontier, data in posteriors.items():
        vc = data["verdict_counts"]
        total = sum(vc.values())
        if total < 2:
            continue
        # Inconsistency: has both CONFIRMED and FALSIFIED verdicts
        if vc["CONFIRMED"] > 0 and vc["FALSIFIED"] > 0:
            inconsistent.append({
                "frontier": frontier,
                "confirmed": vc["CONFIRMED"],
                "falsified": vc["FALSIFIED"],
                "partial": vc["PARTIAL"],
                "posterior": data["posterior"],
                "severity": "HIGH" if min(vc["CONFIRMED"], vc["FALSIFIED"]) >= 2 else "LOW",
            })
    return sorted(inconsistent, key=lambda x: -x["confirmed"] - x["falsified"])


def format_report(
    experiments: list[dict],
    posteriors: dict[str, dict],
    calibration: dict,
    domain_summary: dict,
    pub_bias: dict,
    inconsistencies: list[dict],
    base_prior: float,
) -> str:
    lines = []
    lines.append("=== BAYESIAN META-ANALYSIS ===")
    lines.append(f"Experiments loaded: {len(experiments)} | With frontier+verdict: "
                 f"{sum(1 for e in experiments if e['frontier'])}")
    lines.append(f"Empirical base rate P(H=true): {base_prior:.3f}  "
                 f"[used as default prior]")
    lines.append(f"Frontiers with Bayesian posteriors: {len(posteriors)}")
    lines.append("")

    # Meta-statistics
    all_posteriors = [d["posterior"] for d in posteriors.values()]
    strong_confirm = sum(1 for p in all_posteriors if p >= 0.8)
    moderate_confirm = sum(1 for p in all_posteriors if 0.65 <= p < 0.8)
    uncertain = sum(1 for p in all_posteriors if 0.35 <= p < 0.65)
    strong_doubt = sum(1 for p in all_posteriors if p <= 0.2)
    mean_p = sum(all_posteriors) / len(all_posteriors) if all_posteriors else 0

    lines.append("--- Posterior Distribution ---")
    lines.append(f"  Strong confirm (≥0.80):   {strong_confirm:3d}  "
                 f"({'%5.1f' % (100*strong_confirm/len(all_posteriors))}%)")
    lines.append(f"  Moderate confirm (≥0.65): {moderate_confirm:3d}  "
                 f"({'%5.1f' % (100*moderate_confirm/len(all_posteriors))}%)")
    lines.append(f"  Uncertain (0.35-0.65):    {uncertain:3d}  "
                 f"({'%5.1f' % (100*uncertain/len(all_posteriors))}%)")
    lines.append(f"  Strong doubt (≤0.20):     {strong_doubt:3d}  "
                 f"({'%5.1f' % (100*strong_doubt/len(all_posteriors))}%)")
    lines.append(f"  Mean posterior: {mean_p:.3f}")
    lines.append("")

    # Top confirmed + top doubted
    sorted_by_p = sorted(posteriors.items(), key=lambda x: -x[1]["posterior"])
    lines.append("--- Strongest Evidence (top 8 confirmed) ---")
    for frontier, data in sorted_by_p[:8]:
        vc = data["verdict_counts"]
        lines.append(f"  {frontier:12s}  P={data['posterior']:.3f}  "
                     f"C={vc['CONFIRMED']} P={vc['PARTIAL']} F={vc['FALSIFIED']}  "
                     f"n={data['n_experiments']}  {data['conclusion']}")
    lines.append("")
    lines.append("--- Strongest Doubt (bottom 5) ---")
    for frontier, data in sorted_by_p[-5:]:
        vc = data["verdict_counts"]
        lines.append(f"  {frontier:12s}  P={data['posterior']:.3f}  "
                     f"C={vc['CONFIRMED']} P={vc['PARTIAL']} F={vc['FALSIFIED']}  "
                     f"n={data['n_experiments']}  {data['conclusion']}")
    lines.append("")

    # Domain summary
    lines.append("--- Domain Posteriors ---")
    lines.append(f"  {'Domain':15s}  {'N-F':>4}  {'N-exp':>5}  {'MeanP':>6}  "
                 f"{'EvidGini':>8}  {'StrongConf':>10}")
    for domain, ds in sorted(domain_summary.items(), key=lambda x: -x[1]["mean_posterior"])[:12]:
        lines.append(f"  {domain:15s}  {ds['n_frontiers']:4d}  {ds['total_experiments']:5d}  "
                     f"{ds['mean_posterior']:6.3f}  {ds['evidence_gini']:8.3f}  "
                     f"{ds['strong_confirm']:10d}")
    lines.append("")

    # Calibration
    lines.append("--- Calibration (predicted P vs actual confirmation rate) ---")
    total_error = 0.0
    n_bins = 0
    for bin_range, cal in sorted(calibration.items()):
        lines.append(f"  [{bin_range}]  predicted={cal['mean_predicted_p']:.3f}  "
                     f"actual={cal['mean_actual_rate']:.3f}  "
                     f"error={cal['calibration_error']:.3f}  n={cal['n']}")
        total_error += cal["calibration_error"]
        n_bins += 1
    if n_bins:
        ece = total_error / n_bins
        lines.append(f"  ECE (Expected Calibration Error): {ece:.3f}  "
                     f"{'WELL CALIBRATED' if ece < 0.1 else 'OVERCONFIDENT' if ece >= 0.15 else 'ACCEPTABLE'}")
    lines.append("")

    # Publication bias
    lines.append("--- Publication Bias ---")
    lines.append(f"  r(quality, confirmation) = {pub_bias.get('r_quality_confirmed', 'N/A')}  "
                 f"n={pub_bias.get('n', 0)}")
    lines.append(f"  {pub_bias.get('interpretation', '')}")
    lines.append("")

    # Replication inconsistencies
    if inconsistencies:
        lines.append(f"--- Replication Inconsistencies ({len(inconsistencies)} frontiers) ---")
        for inc in inconsistencies[:6]:
            lines.append(f"  {inc['frontier']:12s}  CONFIRMED×{inc['confirmed']} "
                         f"vs FALSIFIED×{inc['falsified']}  "
                         f"P={inc['posterior']:.3f}  severity={inc['severity']}")
        lines.append("")

    # Bayesian meta-lesson
    n_frontier_multi = sum(1 for d in posteriors.values() if d["n_experiments"] >= 2)
    n_single = len(posteriors) - n_frontier_multi
    lines.append("--- Evidence Structure ---")
    lines.append(f"  Single-experiment frontiers: {n_single}")
    lines.append(f"  Multi-experiment frontiers:  {n_frontier_multi}")
    lines.append(f"  Evidence Gini across frontiers: "
                 f"{gini_coefficient([d['n_experiments'] for d in posteriors.values()]):.3f}")
    lines.append("")
    lines.append("  Recommendation: prior sensitivity dominates single-experiment frontiers.")
    lines.append(f"  Run replications for {n_single} frontiers to reduce prior dependence.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Bayesian meta-analysis for swarm")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--frontier", help="Trace a single frontier")
    parser.add_argument("--domain", help="Filter by domain")
    parser.add_argument("--empirical", action="store_true",
                        help="Use empirical base rate instead of uninformative 0.5 prior (L-909: uninformative default)")
    parser.add_argument("--no-quality-weight", action="store_true",
                        help="Disable quality-weighted Bayes factors")
    args = parser.parse_args()

    experiments = load_experiments()
    base_prior = compute_empirical_prior(experiments) if args.empirical else 0.5
    quality_weighted = not args.no_quality_weight

    posteriors = compute_frontier_posteriors(experiments, base_prior, quality_weighted)

    if args.frontier:
        fid = args.frontier.upper()
        if fid not in posteriors:
            print(f"Frontier {fid} not found. Available: {sorted(posteriors)[:20]}")
            sys.exit(1)
        data = posteriors[fid]
        print(f"\nFrontier: {fid}")
        print(f"Domain: {data['domain']}  |  Base prior: {base_prior:.3f}")
        print(f"Evidence: {data['verdict_counts']}  |  Quality: {data['mean_quality']:.2f}")
        print(f"Posterior P(H=true): {data['posterior']}  →  {data['conclusion']}")
        print("\nEvidence trace:")
        for step in data["trace"]:
            arrow = "→"
            print(f"  S{step['session']}  {step['verdict']:10s}  "
                  f"BF={step['bf']}×w{step['weight']}  "
                  f"{step['prior']:.3f} {arrow} {step['posterior']:.3f}")
        return

    calibration = compute_calibration(posteriors)
    domain_summary = compute_domain_summary(posteriors)
    if args.domain:
        domain_filter = args.domain.lower()
        posteriors = {k: v for k, v in posteriors.items()
                      if v["domain"] == domain_filter}
        if not posteriors:
            print(f"No frontiers found for domain '{domain_filter}'")
            sys.exit(1)

    pub_bias = check_publication_bias(experiments)
    inconsistencies = replication_consistency(posteriors)

    if args.json:
        output = {
            "base_prior": round(base_prior, 3),
            "n_experiments": len(experiments),
            "n_frontiers": len(posteriors),
            "posteriors": posteriors,
            "calibration": calibration,
            "domain_summary": domain_summary,
            "publication_bias": pub_bias,
            "replication_inconsistencies": inconsistencies,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_report(
            experiments, posteriors, calibration, domain_summary,
            pub_bias, inconsistencies, base_prior
        ))


if __name__ == "__main__":
    main()
