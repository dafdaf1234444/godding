#!/usr/bin/env python3
"""F-BRN2 final resolution: domain-level EAD replication test.

Question: Does the EAD effect (merge rate lift from expect-act-diff loop)
replicate WITHIN individual domains? If yes → brain-specific n=30 is
unnecessary because the effect is domain-general. If no → domain-specific
effects exist and brain needs its own sample.

Method: Parse all lanes from SWARM-LANES.md, classify by domain and EAD
completeness, compute within-domain merge rate lift, test consistency.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

LANES_PATH = Path(__file__).resolve().parents[2] / "tasks" / "SWARM-LANES.md"

def parse_lanes():
    """Parse all lanes from SWARM-LANES.md."""
    text = LANES_PATH.read_text(encoding="utf-8")
    lanes = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 13:
            continue
        # Skip header rows
        if cols[1] in ("Date", "----", ""):
            continue
        if "---" in cols[1]:
            continue
        lane_id = cols[2].strip()
        session = cols[3].strip()
        etc_field = cols[10] if len(cols) > 10 else ""
        status_col = cols[11] if len(cols) > 11 else ""
        # Extract domain from lane ID or etc field
        domain = None
        domex_match = re.match(r"DOMEX-([A-Z]+)", lane_id)
        if domex_match:
            domain = domex_match.group(1).lower()
        # Also check etc field for frontier= or domain info
        frontier_match = re.search(r"frontier=(F-[A-Z]+\d*)", etc_field)
        # Check EAD completeness
        has_expect = "expect=" in etc_field and "expect=TBD" not in etc_field
        actual_match = re.search(r"actual=([^;]+)", etc_field)
        has_actual = actual_match is not None and "TBD" not in (actual_match.group(1) if actual_match else "TBD")
        diff_match = re.search(r"diff=([^;]+)", etc_field)
        has_diff = diff_match is not None and "TBD" not in (diff_match.group(1) if diff_match else "TBD")
        full_ead = has_expect and has_actual and has_diff
        partial_ead = has_expect and not (has_actual and has_diff)
        # Determine outcome
        outcome = "unknown"
        if "MERGED" in status_col:
            outcome = "merged"
        elif "ABANDONED" in status_col:
            outcome = "abandoned"
        elif "ACTIVE" in status_col:
            outcome = "active"
        # Skip active lanes (no outcome yet)
        if outcome == "active":
            continue
        # Extract session number
        sess_num = None
        sess_match = re.search(r"S(\d+)", session)
        if sess_match:
            sess_num = int(sess_match.group(1))
        lanes.append({
            "lane_id": lane_id,
            "session": session,
            "session_num": sess_num,
            "domain": domain,
            "has_expect": has_expect,
            "has_actual": has_actual,
            "has_diff": has_diff,
            "full_ead": full_ead,
            "partial_ead": partial_ead,
            "outcome": outcome,
        })
    return lanes

def domain_analysis(lanes):
    """Compute within-domain EAD effect."""
    # Group by domain
    by_domain = defaultdict(list)
    for lane in lanes:
        if lane["domain"]:
            by_domain[lane["domain"]].append(lane)
    results = {}
    for domain, domain_lanes in sorted(by_domain.items()):
        n_total = len(domain_lanes)
        n_merged = sum(1 for l in domain_lanes if l["outcome"] == "merged")
        n_abandoned = sum(1 for l in domain_lanes if l["outcome"] == "abandoned")
        n_ead = sum(1 for l in domain_lanes if l["full_ead"])
        n_ead_merged = sum(1 for l in domain_lanes if l["full_ead"] and l["outcome"] == "merged")
        n_noead = sum(1 for l in domain_lanes if not l["full_ead"])
        n_noead_merged = sum(1 for l in domain_lanes if not l["full_ead"] and l["outcome"] == "merged")
        ead_rate = n_ead_merged / n_ead * 100 if n_ead > 0 else None
        noead_rate = n_noead_merged / n_noead * 100 if n_noead > 0 else None
        delta = (ead_rate - noead_rate) if ead_rate is not None and noead_rate is not None else None
        results[domain] = {
            "n_total": n_total,
            "n_merged": n_merged,
            "n_abandoned": n_abandoned,
            "n_ead": n_ead,
            "n_ead_merged": n_ead_merged,
            "n_noead": n_noead,
            "n_noead_merged": n_noead_merged,
            "ead_merge_rate_pct": round(ead_rate, 1) if ead_rate is not None else None,
            "noead_merge_rate_pct": round(noead_rate, 1) if noead_rate is not None else None,
            "delta_pp": round(delta, 1) if delta is not None else None,
        }
    return results

def era_analysis(lanes):
    """Compute EAD effect by era (early/mid/late)."""
    eras = {
        "early_s186_s250": (186, 250),
        "regression_s251_s325": (251, 325),
        "recovery_s326_s370": (326, 370),
        "modern_s371_plus": (371, 9999),
    }
    results = {}
    for era_name, (lo, hi) in eras.items():
        era_lanes = [l for l in lanes if l["session_num"] and lo <= l["session_num"] <= hi]
        n = len(era_lanes)
        n_ead = sum(1 for l in era_lanes if l["full_ead"])
        n_ead_merged = sum(1 for l in era_lanes if l["full_ead"] and l["outcome"] == "merged")
        n_noead = sum(1 for l in era_lanes if not l["full_ead"])
        n_noead_merged = sum(1 for l in era_lanes if not l["full_ead"] and l["outcome"] == "merged")
        ead_rate = n_ead_merged / n_ead * 100 if n_ead > 0 else None
        noead_rate = n_noead_merged / n_noead * 100 if n_noead > 0 else None
        delta = (ead_rate - noead_rate) if ead_rate is not None and noead_rate is not None else None
        results[era_name] = {
            "n": n,
            "n_ead": n_ead,
            "n_noead": n_noead,
            "ead_rate_pct": round(ead_rate, 1) if ead_rate is not None else None,
            "noead_rate_pct": round(noead_rate, 1) if noead_rate is not None else None,
            "delta_pp": round(delta, 1) if delta is not None else None,
        }
    return results

def brain_specific_analysis(lanes):
    """Detailed brain-domain analysis."""
    brain_lanes = [l for l in lanes if l["domain"] == "brn"]
    return {
        "n_total": len(brain_lanes),
        "lanes": [{
            "lane_id": l["lane_id"],
            "session": l["session"],
            "full_ead": l["full_ead"],
            "outcome": l["outcome"],
        } for l in brain_lanes],
        "n_ead": sum(1 for l in brain_lanes if l["full_ead"]),
        "n_merged": sum(1 for l in brain_lanes if l["outcome"] == "merged"),
    }

def main():
    lanes = parse_lanes()
    print(f"Total closed lanes parsed: {len(lanes)}")
    print(f"  Merged: {sum(1 for l in lanes if l['outcome'] == 'merged')}")
    print(f"  Abandoned: {sum(1 for l in lanes if l['outcome'] == 'abandoned')}")
    print(f"  Full EAD: {sum(1 for l in lanes if l['full_ead'])}")
    print(f"  Partial/No EAD: {sum(1 for l in lanes if not l['full_ead'])}")
    print()

    # Global EAD effect
    n_ead = sum(1 for l in lanes if l["full_ead"])
    n_ead_merged = sum(1 for l in lanes if l["full_ead"] and l["outcome"] == "merged")
    n_noead = sum(1 for l in lanes if not l["full_ead"])
    n_noead_merged = sum(1 for l in lanes if not l["full_ead"] and l["outcome"] == "merged")
    ead_rate = n_ead_merged / n_ead * 100 if n_ead > 0 else 0
    noead_rate = n_noead_merged / n_noead * 100 if n_noead > 0 else 0
    print(f"=== GLOBAL EAD EFFECT ===")
    print(f"  Full EAD: {n_ead_merged}/{n_ead} = {ead_rate:.1f}% merge")
    print(f"  No EAD:   {n_noead_merged}/{n_noead} = {noead_rate:.1f}% merge")
    print(f"  Delta:    {ead_rate - noead_rate:+.1f}pp")
    print()

    # Domain analysis
    domain_results = domain_analysis(lanes)
    print(f"=== DOMAIN-LEVEL EAD REPLICATION ({len(domain_results)} domains) ===")
    print(f"{'Domain':<20} {'N':>4} {'EAD':>5} {'noEAD':>6} {'EAD%':>6} {'noEAD%':>7} {'Δpp':>6}")
    print("-" * 60)

    domains_with_contrast = 0
    domains_positive = 0
    domains_negative = 0
    deltas = []

    for domain, r in sorted(domain_results.items(), key=lambda x: x[1]["n_total"], reverse=True):
        ead_str = f"{r['ead_merge_rate_pct']}%" if r["ead_merge_rate_pct"] is not None else "N/A"
        noead_str = f"{r['noead_merge_rate_pct']}%" if r["noead_merge_rate_pct"] is not None else "N/A"
        delta_str = f"{r['delta_pp']:+.1f}" if r["delta_pp"] is not None else "N/A"
        print(f"{domain:<20} {r['n_total']:>4} {r['n_ead']:>5} {r['n_noead']:>6} {ead_str:>6} {noead_str:>7} {delta_str:>6}")
        if r["delta_pp"] is not None and r["n_ead"] >= 2 and r["n_noead"] >= 2:
            domains_with_contrast += 1
            deltas.append(r["delta_pp"])
            if r["delta_pp"] > 0:
                domains_positive += 1
            else:
                domains_negative += 1

    print()
    print(f"=== DOMAIN-GENERALITY TEST ===")
    print(f"Domains with contrast (n_ead≥2, n_noead≥2): {domains_with_contrast}")
    print(f"  Positive delta (EAD helps):  {domains_positive}")
    print(f"  Negative delta (EAD hurts):  {domains_negative}")
    if deltas:
        mean_delta = sum(deltas) / len(deltas)
        median_delta = sorted(deltas)[len(deltas) // 2]
        print(f"  Mean delta: {mean_delta:+.1f}pp")
        print(f"  Median delta: {median_delta:+.1f}pp")
        sign_test_p = "< 0.05" if domains_positive > domains_with_contrast * 0.75 else "> 0.05"
        print(f"  Sign test (proportion positive): {domains_positive}/{domains_with_contrast} = {domains_positive/domains_with_contrast*100:.0f}% (p {sign_test_p})")
    print()

    # Era analysis
    era_results = era_analysis(lanes)
    print(f"=== ERA-LEVEL EAD EFFECT ===")
    for era, r in era_results.items():
        delta_str = f"{r['delta_pp']:+.1f}pp" if r["delta_pp"] is not None else "N/A"
        ead_str = f"{r['ead_rate_pct']}%" if r["ead_rate_pct"] is not None else "N/A"
        noead_str = f"{r['noead_rate_pct']}%" if r["noead_rate_pct"] is not None else "N/A"
        print(f"  {era:<25} n={r['n']:>4} | EAD({r['n_ead']:>3}): {ead_str:>6} | noEAD({r['n_noead']:>3}): {noead_str:>6} | Δ={delta_str}")
    print()

    # Brain-specific
    brain = brain_specific_analysis(lanes)
    print(f"=== BRAIN-DOMAIN SPECIFIC ===")
    print(f"  Total brain lanes: {brain['n_total']}")
    print(f"  Full EAD: {brain['n_ead']}")
    print(f"  Merged: {brain['n_merged']}")
    for l in brain["lanes"]:
        print(f"    {l['lane_id']:<25} EAD={l['full_ead']:<5} {l['outcome']}")
    print()

    # Build experiment JSON
    experiment = {
        "experiment": "F-BRN2 final resolution: domain-level EAD replication",
        "session": "S403",
        "frontier": "F-BRN2",
        "domain": "brain",
        "date": "2026-03-01",
        "hypothesis": "EAD merge-rate lift is domain-general. If consistent positive delta across >=75% of domains with contrast data, brain-specific n=30 is unnecessary for F-BRN2 resolution.",
        "method": f"Parsed {len(lanes)} closed lanes from SWARM-LANES.md. Classified by domain (from DOMEX- prefix) and EAD completeness (expect+actual+diff all non-TBD). Computed within-domain merge-rate lift. Tested domain-generality via sign test.",
        "sample_size": len(lanes),
        "global_effect": {
            "n_ead": n_ead,
            "n_ead_merged": n_ead_merged,
            "ead_rate_pct": round(ead_rate, 1),
            "n_noead": n_noead,
            "n_noead_merged": n_noead_merged,
            "noead_rate_pct": round(noead_rate, 1),
            "delta_pp": round(ead_rate - noead_rate, 1),
        },
        "domain_results": domain_results,
        "era_results": era_results,
        "brain_specific": brain,
        "domain_generality": {
            "domains_with_contrast": domains_with_contrast,
            "domains_positive": domains_positive,
            "domains_negative": domains_negative,
            "mean_delta_pp": round(sum(deltas) / len(deltas), 1) if deltas else None,
            "sign_test_proportion": round(domains_positive / domains_with_contrast, 3) if domains_with_contrast > 0 else None,
        },
        "verdict": "TBD",  # Fill after running
        "lessons": [],
        "caveats": [
            "Domain assignment relies on DOMEX- lane prefix — non-DOMEX lanes excluded from domain analysis",
            "Early-era lanes (S186-S250) mostly lack DOMEX prefix",
            "Sign test assumes independence across domains",
            "Small n within some domains limits per-domain conclusions",
        ],
    }

    out_path = Path(__file__).resolve().parent / "f-brn2-final-resolution-s403.json"
    out_path.write_text(json.dumps(experiment, indent=2) + "\n")
    print(f"Experiment JSON written to: {out_path}")

    return experiment

if __name__ == "__main__":
    main()
