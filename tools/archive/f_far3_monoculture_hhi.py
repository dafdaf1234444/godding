#!/usr/bin/env python3
"""F-FAR3: Monoculture HHI measurement.

Compute domain Herfindahl-Hirschman Index per rolling window
and correlate with knowledge production (L+P).

Hypothesis: HHI > 0.4 (monoculture) produces >20% less L+P
than diversified windows (HHI < 0.25).
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SESSION_LOG = REPO / "memory" / "SESSION-LOG.md"
LANES_FILE = REPO / "tasks" / "SWARM-LANES.md"
LANES_ARCHIVE = REPO / "tasks" / "SWARM-LANES-ARCHIVE.md"

# Domain detection patterns (F-prefix -> domain)
FRONTIER_DOMAIN = {
    "F-FAR": "farming", "F-FIN": "finance", "F-ECO": "economy",
    "F-IS": "information-science", "F-NK": "nk-complexity",
    "F-SP": "stochastic-processes", "F-BRN": "brain", "F-AI": "ai",
    "F-META": "meta", "F-EXP": "expert-swarm", "F-HLP": "helper-swarm",
    "F-GOV": "governance", "F-CON": "conflict", "F-EMP": "empathy",
    "F-CRY": "cryptography", "F-LNG": "linguistics", "F-GT": "graph-theory",
    "F-EVO": "evolution", "F-DRM": "dream", "F-GAME": "gaming",
    "F-CTL": "control-theory", "F-PSY": "psychology", "F-COMP": "competitions",
    "F-CAT": "catastrophic-risks", "F-PHY": "physics", "F-FLD": "fluid-dynamics",
    "F-EVAL": "evaluation", "F-QC": "quality", "F-COMM": "meta",
    "F-DS": "distributed-systems", "F-DNA": "meta", "F-SEC": "meta",
    "F-SCALE": "meta", "F-VVE": "meta", "F-CC": "cryptocurrency",
    "F-OPS": "operations-research", "F-STAT": "statistics",
    "F-PRO": "protocol-engineering",
}

# DOMEX prefix -> domain
DOMEX_DOMAIN = {
    "NK": "nk-complexity", "LNG": "linguistics", "EXP": "expert-swarm",
    "BRN": "brain", "HLP": "helper-swarm", "ECO": "economy",
    "META": "meta", "SP": "stochastic-processes", "EMP": "empathy",
    "AI": "ai", "CON": "conflict", "CRY": "cryptography",
    "FIN": "finance", "GOV": "governance", "FAR": "farming",
    "GT": "graph-theory", "GAME": "gaming", "STAT": "statistics",
    "PHY": "physics", "FLD": "fluid-dynamics", "EVAL": "evaluation",
    "DS": "distributed-systems", "PSY": "psychology", "CAT": "catastrophic-risks",
    "IS": "information-science", "CTL": "control-theory", "COMP": "competitions",
    "OR": "operations-research",
}

KEYWORD_DOMAIN = {
    "maintenance": "meta", "orient.py": "meta", "compaction": "meta",
    "proxy-K": "meta", "proxy_k": "meta", "health check": "meta",
    "dream": "dream", "council": "governance", "genesis": "meta",
    "human-signal": "meta", "periodics": "meta", "bridge sync": "meta",
    "tool consolidation": "meta", "README": "meta", "stale-lane": "meta",
    "PAPER": "meta",
}


def parse_session_log():
    """Parse SESSION-LOG.md into per-session records."""
    sessions = []
    with open(SESSION_LOG) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("Never ") or line.startswith("Format:"):
                continue
            if "S01" in line and "baseline" in line:
                continue

            m = re.match(r'S(\d+[a-z+]*)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|\s*(.+)', line)
            if not m:
                continue

            sid_raw = m.group(1)
            sid_num = int(re.match(r'(\d+)', sid_raw).group(1))
            date = m.group(2)
            lp_str = m.group(3)
            summary = m.group(4)

            l_match = re.search(r'\+(\d+)L', lp_str)
            p_match = re.search(r'\+(\d+)P', lp_str)
            lessons = int(l_match.group(1)) if l_match else 0
            principles = int(p_match.group(1)) if p_match else 0

            domains = detect_domains(summary)

            sessions.append({
                "session": f"S{sid_raw}",
                "session_num": sid_num,
                "date": date,
                "lessons": lessons,
                "principles": principles,
                "lp": lessons + principles,
                "domains": domains,
                "primary_domain": domains[0] if domains else "meta",
                "is_domex": bool(re.search(r'DOMEX', summary)),
            })

    return sessions


def detect_domains(summary):
    """Extract domain focus from session summary text."""
    domains = []
    seen = set()

    # 1. DOMEX-XXX patterns (strongest signal)
    for m in re.finditer(r'DOMEX-([A-Z]+)', summary):
        abbrev = m.group(1)
        if abbrev in DOMEX_DOMAIN:
            d = DOMEX_DOMAIN[abbrev]
            if d not in seen:
                domains.append(d)
                seen.add(d)

    # 2. F-XXX frontier references
    for m in re.finditer(r'(F-[A-Z]+)\d*', summary):
        prefix = m.group(1)
        if prefix in FRONTIER_DOMAIN:
            d = FRONTIER_DOMAIN[prefix]
            if d not in seen:
                domains.append(d)
                seen.add(d)

    # 3. Standalone frontier references
    for m in re.finditer(r'\bF(\d+)\b', summary):
        fid = int(m.group(1))
        d = "meta"
        if fid == 95:
            d = "distributed-systems"
        elif fid == 136:
            d = "physics"
        if d not in seen:
            domains.append(d)
            seen.add(d)

    # 4. Keyword heuristics
    summary_lower = summary.lower()
    for kw, d in KEYWORD_DOMAIN.items():
        if kw.lower() in summary_lower and d not in seen:
            domains.append(d)
            seen.add(d)

    if not domains:
        domains = ["meta"]

    return domains


def compute_hhi_windows(sessions, window_size=10):
    """Compute HHI per rolling window of sessions."""
    seen_nums = set()
    unique = []
    for s in sessions:
        if s["session_num"] not in seen_nums:
            unique.append(s)
            seen_nums.add(s["session_num"])
    unique.sort(key=lambda x: x["session_num"])

    windows = []
    for i in range(len(unique) - window_size + 1):
        window = unique[i:i + window_size]
        start = window[0]["session_num"]
        end = window[-1]["session_num"]

        domain_counts = Counter()
        total_lp = 0
        total_l = 0
        total_p = 0
        n_domex = 0
        for s in window:
            domain_counts[s["primary_domain"]] += 1
            total_lp += s["lp"]
            total_l += s["lessons"]
            total_p += s["principles"]
            if s.get("is_domex"):
                n_domex += 1

        n = len(window)
        hhi = sum((count / n) ** 2 for count in domain_counts.values())
        n_domains = len(domain_counts)
        top_domain = domain_counts.most_common(1)[0]
        meta_share = domain_counts.get("meta", 0) / n

        windows.append({
            "window_start": start,
            "window_end": end,
            "hhi": round(hhi, 4),
            "n_domains": n_domains,
            "top_domain": top_domain[0],
            "top_domain_share": round(top_domain[1] / n, 3),
            "meta_share": round(meta_share, 3),
            "total_lp": total_lp,
            "mean_lp": round(total_lp / n, 3),
            "total_l": total_l,
            "total_p": total_p,
            "domex_share": round(n_domex / n, 3),
            "domain_distribution": dict(domain_counts.most_common()),
        })

    return windows


def correlate(xs, ys):
    """Pearson correlation."""
    if len(xs) < 3:
        return 0.0
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    sx = (sum((x - mx) ** 2 for x in xs) / n) ** 0.5
    sy = (sum((y - my) ** 2 for y in ys) / n) ** 0.5
    return round(cov / (sx * sy), 4) if sx > 0 and sy > 0 else 0.0


def analyze_windows(windows, label=""):
    """Analyze correlation and regime comparison for a set of windows."""
    if len(windows) < 3:
        return {"error": "insufficient windows", "n": len(windows)}

    hhis = [w["hhi"] for w in windows]
    lps = [w["mean_lp"] for w in windows]
    r = correlate(hhis, lps)

    mono = [w for w in windows if w["hhi"] > 0.4]
    diverse = [w for w in windows if w["hhi"] < 0.25]
    mid = [w for w in windows if 0.25 <= w["hhi"] <= 0.4]

    mono_lp = sum(w["mean_lp"] for w in mono) / len(mono) if mono else 0
    diverse_lp = sum(w["mean_lp"] for w in diverse) / len(diverse) if diverse else 0
    mid_lp = sum(w["mean_lp"] for w in mid) / len(mid) if mid else 0

    pct_diff = ((diverse_lp - mono_lp) / mono_lp * 100) if mono_lp > 0 else 0.0

    # Also check meta_share as confound
    meta_shares = [w["meta_share"] for w in windows]
    r_meta_lp = correlate(meta_shares, lps)
    r_meta_hhi = correlate(meta_shares, hhis)

    # Partial correlation: r(HHI, LP | meta_share)
    # r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1-r_xz^2)(1-r_yz^2))
    r_hhi_lp = r
    r_hhi_meta = r_meta_hhi
    r_lp_meta = r_meta_lp
    denom = ((1 - r_hhi_meta**2) * (1 - r_lp_meta**2)) ** 0.5
    r_partial = (r_hhi_lp - r_hhi_meta * r_lp_meta) / denom if denom > 0 else 0.0

    return {
        "label": label,
        "pearson_r": r,
        "n_windows": len(windows),
        "mean_hhi": round(sum(hhis) / len(hhis), 4),
        "mean_lp": round(sum(lps) / len(lps), 3),
        "monoculture_n": len(mono),
        "monoculture_mean_lp": round(mono_lp, 3),
        "diversified_n": len(diverse),
        "diversified_mean_lp": round(diverse_lp, 3),
        "moderate_n": len(mid),
        "moderate_mean_lp": round(mid_lp, 3),
        "diversified_vs_mono_pct": round(pct_diff, 1),
        "r_meta_share_lp": r_meta_lp,
        "r_meta_share_hhi": r_meta_hhi,
        "r_partial_hhi_lp_given_meta": round(r_partial, 4),
    }


def era_analysis(windows):
    """Split windows by era and compute within-era correlations."""
    eras = {
        "bootstrap_S57_S100": (57, 100),
        "early_growth_S100_S195": (100, 195),
        "gap_S195_S306": (195, 306),
        "domex_era_S306_S370": (306, 370),
        "current_S370_plus": (370, 9999),
    }
    result = {}
    for era_name, (lo, hi) in eras.items():
        ws = [w for w in windows if lo <= w["window_end"] <= hi]
        if len(ws) < 3:
            result[era_name] = {"n": len(ws), "note": "insufficient data"}
            continue
        mean_hhi = sum(w["hhi"] for w in ws) / len(ws)
        mean_lp = sum(w["mean_lp"] for w in ws) / len(ws)
        mean_domains = sum(w["n_domains"] for w in ws) / len(ws)
        r = correlate([w["hhi"] for w in ws], [w["mean_lp"] for w in ws])
        result[era_name] = {
            "n": len(ws),
            "mean_hhi": round(mean_hhi, 4),
            "mean_lp": round(mean_lp, 3),
            "mean_domains": round(mean_domains, 1),
            "within_era_r": r,
        }
    return result


def domex_vs_non_domex(windows):
    """Check if DOMEX presence explains the effect."""
    high_domex = [w for w in windows if w["domex_share"] > 0.3]
    low_domex = [w for w in windows if w["domex_share"] <= 0.1]

    result = {}
    if high_domex:
        result["high_domex"] = {
            "n": len(high_domex),
            "mean_hhi": round(sum(w["hhi"] for w in high_domex) / len(high_domex), 4),
            "mean_lp": round(sum(w["mean_lp"] for w in high_domex) / len(high_domex), 3),
        }
    if low_domex:
        result["low_domex"] = {
            "n": len(low_domex),
            "mean_hhi": round(sum(w["hhi"] for w in low_domex) / len(low_domex), 4),
            "mean_lp": round(sum(w["mean_lp"] for w in low_domex) / len(low_domex), 3),
        }

    # Within high-DOMEX windows, does HHI still predict L+P?
    if len(high_domex) >= 5:
        r = correlate([w["hhi"] for w in high_domex], [w["mean_lp"] for w in high_domex])
        result["within_high_domex_r"] = r

    return result


def top_domain_concentration(sessions):
    """Measure overall domain concentration across all sessions."""
    counts = Counter(s["primary_domain"] for s in sessions)
    total = sum(counts.values())
    ranked = counts.most_common(10)
    return {
        "total_sessions": total,
        "unique_domains": len(counts),
        "top_10": [{"domain": d, "count": c, "share": round(c / total, 3)} for d, c in ranked],
        "overall_hhi": round(sum((c / total) ** 2 for c in counts.values()), 4),
    }


def main():
    sessions = parse_session_log()
    print(f"Parsed {len(sessions)} session entries")

    seen = set()
    unique = []
    for s in sessions:
        if s["session_num"] not in seen:
            unique.append(s)
            seen.add(s["session_num"])
    print(f"Unique sessions: {len(unique)}")

    concentration = top_domain_concentration(unique)
    top5 = ", ".join(f"{d['domain']}={d['share']:.0%}" for d in concentration["top_10"][:5])
    print(f"Unique domains: {concentration['unique_domains']}, Overall HHI: {concentration['overall_hhi']}")
    print(f"Top 5: {top5}")

    # Main analysis: 10-session windows
    windows = compute_hhi_windows(sessions, window_size=10)
    print(f"\n--- 10-session rolling windows: {len(windows)} ---")

    analysis = analyze_windows(windows, "w10_all")
    print(f"Pearson r(HHI, L+P): {analysis['pearson_r']}")
    print(f"r(meta_share, L+P): {analysis['r_meta_share_lp']}")
    print(f"r(meta_share, HHI): {analysis['r_meta_share_hhi']}")
    print(f"PARTIAL r(HHI, L+P | meta_share): {analysis['r_partial_hhi_lp_given_meta']}")
    print(f"Monoculture (HHI>0.4): n={analysis['monoculture_n']}, L+P={analysis['monoculture_mean_lp']}")
    print(f"Diversified (HHI<0.25): n={analysis['diversified_n']}, L+P={analysis['diversified_mean_lp']}")
    print(f"Diversified vs mono: {analysis['diversified_vs_mono_pct']:+.1f}%")

    # Era analysis
    eras = era_analysis(windows)
    print("\nEra analysis:")
    for era, data in eras.items():
        if data["n"] >= 3:
            print(f"  {era}: n={data['n']}, HHI={data['mean_hhi']:.3f}, L+P={data['mean_lp']:.2f}, "
                  f"domains={data['mean_domains']:.1f}, within-r={data['within_era_r']}")
        else:
            print(f"  {era}: n={data['n']} (insufficient)")

    # DOMEX confound check
    domex = domex_vs_non_domex(windows)
    print("\nDOMEX confound check:")
    for k, v in domex.items():
        if isinstance(v, dict):
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")

    # Robustness: different window sizes
    windows_5 = compute_hhi_windows(sessions, window_size=5)
    analysis_5 = analyze_windows(windows_5, "w5_all")
    windows_20 = compute_hhi_windows(sessions, window_size=20)
    analysis_20 = analyze_windows(windows_20, "w20_all")

    print(f"\nRobustness across window sizes:")
    print(f"  w=5:  r={analysis_5['pearson_r']}, partial_r={analysis_5['r_partial_hhi_lp_given_meta']}")
    print(f"  w=10: r={analysis['pearson_r']}, partial_r={analysis['r_partial_hhi_lp_given_meta']}")
    print(f"  w=20: r={analysis_20['pearson_r']}, partial_r={analysis_20['r_partial_hhi_lp_given_meta']}")

    # Verdict
    partial_r = analysis["r_partial_hhi_lp_given_meta"]
    within_domex_era = eras.get("domex_era_S306_S370", {})
    domex_era_r = within_domex_era.get("within_era_r", 0)

    print(f"\n=== VERDICT ===")
    if abs(partial_r) > 0.3:
        print(f"  HHI effect SURVIVES meta-share control (partial r={partial_r})")
    else:
        print(f"  HHI effect WEAKENED by meta-share control (partial r={partial_r})")

    if abs(domex_era_r) > 0.3 and within_domex_era.get("n", 0) >= 5:
        print(f"  Within-DOMEX-era: r={domex_era_r} (n={within_domex_era['n']}) — effect holds")
    elif within_domex_era.get("n", 0) >= 5:
        print(f"  Within-DOMEX-era: r={domex_era_r} (n={within_domex_era['n']}) — effect weakens")

    # Save artifact
    artifact = {
        "frontier": "F-FAR3",
        "session": os.environ.get("SWARM_SESSION", "S374"),
        "method": "HHI per rolling window, Pearson + partial correlation with mean L+P",
        "n_sessions": len(unique),
        "window_sizes_tested": [5, 10, 20],
        "concentration": concentration,
        "analysis_w10": analysis,
        "analysis_w5": analysis_5,
        "analysis_w20": analysis_20,
        "era_analysis": eras,
        "domex_confound": domex,
        "hypothesis": "HHI > 0.4 produces >20% less L+P than HHI < 0.25",
        "windows_sample": windows[:3] + windows[-3:] if len(windows) > 6 else windows,
    }

    out_path = REPO / "experiments" / "farming" / "f-far3-monoculture-hhi-s374.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact: {out_path.relative_to(REPO)}")

    return artifact


if __name__ == "__main__":
    main()
