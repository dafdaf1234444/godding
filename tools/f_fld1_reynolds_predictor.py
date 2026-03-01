#!/usr/bin/env python3
"""F-FLD1: Reynolds-analog dimensionless ratio for swarm sessions.

Computes Re_swarm and tests whether it predicts session productivity.

Reynolds number analogy (fluid dynamics -> swarm):
  Re = (density * velocity * length) / viscosity

Swarm mapping:
  - Inertial force (task momentum) = lanes_touched (DOMEX lanes active/completed)
  - Velocity = L+P production rate (lessons + 0.5*principles)
  - Viscous force (friction) = overhead_ratio (maintenance keywords / total keywords)
  - Length = domains_touched (scope breadth)

Full formula: Re_swarm = (lanes_touched * productivity_score) / (overhead_ratio + epsilon)

IMPORTANT: The "full" Re includes productivity in the numerator, making it circular
for predicting productivity. We also test "structural" Re variants that use only
session structure (lanes, overhead, domains) as predictors, keeping productivity
as the independent outcome variable.

Structural Re = (lanes_touched * domains_touched) / (overhead_ratio + epsilon)
"""

import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESSION_LOG = ROOT / "memory" / "SESSION-LOG.md"
SWARM_LANES = ROOT / "tasks" / "SWARM-LANES.md"
SWARM_LANES_ARCHIVE = ROOT / "tasks" / "SWARM-LANES-ARCHIVE.md"
OUTPUT_DIR = ROOT / "experiments" / "fluid-dynamics"

# Keywords for overhead vs productive classification
OVERHEAD_KEYWORDS = {
    "maintenance", "state-sync", "trim", "compact", "rescue", "fix",
    "repair", "sync", "cleanup", "dedup", "drift", "stale", "hygiene",
    "backlog", "relay", "compression", "compaction", "health-check",
    "periodics", "consolidation", "reswarm", "validator", "correction",
    "minimal", "push", "setup", "restore", "recovery",
}

PRODUCTIVE_KEYWORDS = {
    "domex", "confirmed", "resolved", "lesson", "experiment", "tested",
    "baseline", "measured", "falsified", "observed", "discovered",
    "council", "harvest", "dream", "investigated", "analysis",
    "built", "created", "implemented", "opened", "seeded",
    "frontier", "hypothesis", "evidence", "correlation",
}

EPSILON = 0.01

DOMAIN_ABBREVS = [
    "META", "NK", "LNG", "SP", "AI", "FIN", "EVO", "CTL",
    "GAM", "OPS", "STAT", "BRN", "HLT", "IS", "GT",
    "CON", "FAR", "ECO", "DS", "QC", "GOV", "HLP",
    "DRM", "PSY", "SEC", "COMP", "PHY", "DNA", "COMM",
    "VVE", "FLD", "CAT", "EXP", "CACHE",
]


def parse_session_log():
    """Parse SESSION-LOG.md into per-session records.

    Returns dict: session_number -> {
        'lessons': float, 'principles': float,
        'descriptions': [str], 'dates': [str]
    }
    """
    sessions = {}
    if not SESSION_LOG.exists():
        return sessions

    text = SESSION_LOG.read_text(encoding="utf-8", errors="replace")

    # Handle the S01-S56 baseline block
    baseline_match = re.search(
        r'S01[–\-]S56\s*\|.*?\|\s*baseline\s*\|\s*(\d+)L[,\s]*(\d+)P',
        text
    )
    if baseline_match:
        total_l = int(baseline_match.group(1))
        total_p = int(baseline_match.group(2))
        per_l = total_l / 56.0
        per_p = total_p / 56.0
        for s in range(1, 57):
            sessions[s] = {
                "lessons": per_l,
                "principles": per_p,
                "descriptions": ["baseline founding session"],
                "dates": ["2026-02-25"],
            }

    # Parse individual session lines
    pattern = re.compile(
        r'^\s*\|?\s*S(\d+)\w*\s*\|?\s*'
        r'(\d{4}-\d{2}-\d{2})\s*\|'
        r'\s*([^|]*)\|'
        r'\s*(.*)',
        re.MULTILINE
    )

    for m in pattern.finditer(text):
        snum = int(m.group(1))
        date = m.group(2).strip()
        lp_field = m.group(3).strip()
        desc = m.group(4).strip()

        l_match = re.search(r'\+(\d+)L', lp_field)
        lessons = int(l_match.group(1)) if l_match else 0

        p_match = re.search(r'([+-]?\d+)P', lp_field)
        principles = 0
        if p_match:
            val = p_match.group(1)
            if val.startswith("+"):
                principles = int(val[1:])
            elif val.startswith("-"):
                principles = int(val)
            else:
                principles = int(val)

        if snum not in sessions:
            sessions[snum] = {
                "lessons": 0, "principles": 0,
                "descriptions": [], "dates": [],
            }

        sessions[snum]["lessons"] += lessons
        sessions[snum]["principles"] += max(0, principles)
        sessions[snum]["descriptions"].append(desc)
        if date not in sessions[snum]["dates"]:
            sessions[snum]["dates"].append(date)

    return sessions


def parse_lanes_per_session():
    """Parse SWARM-LANES files for per-session lane counts."""
    session_lanes = defaultdict(set)
    for fpath in [SWARM_LANES, SWARM_LANES_ARCHIVE]:
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if not line.strip().startswith("|"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue
            date_field = parts[1]
            lane_id = parts[2]
            session_field = parts[3]
            if "---" in date_field or "Date" in date_field or "Lane" in lane_id:
                continue
            try:
                snum = int(session_field.strip())
            except (ValueError, TypeError):
                sm = re.search(r'S(\d+)', lane_id)
                if sm:
                    snum = int(sm.group(1))
                else:
                    continue
            session_lanes[snum].add(lane_id)
    return session_lanes


def count_domex_from_git():
    """Count DOMEX lanes per session from git commit messages."""
    session_domex = defaultdict(int)
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "--format=%s"],
            capture_output=True, text=True, timeout=30, cwd=ROOT,
        )
        if not result.stdout:
            return session_domex
        for line in result.stdout.splitlines():
            sm = re.search(r'\[S(\d+)\]', line)
            if sm:
                snum = int(sm.group(1))
                domex_count = len(re.findall(r'DOMEX', line, re.IGNORECASE))
                if domex_count > 0:
                    session_domex[snum] += domex_count
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return session_domex


def count_domex_from_descriptions(sessions):
    """Count DOMEX mentions in session descriptions."""
    session_domex = {}
    for snum, data in sessions.items():
        combined = " ".join(data["descriptions"])
        count = len(re.findall(r'DOMEX', combined, re.IGNORECASE))
        domains = set()
        for d in DOMAIN_ABBREVS:
            if re.search(r'\b' + d + r'\b', combined, re.IGNORECASE):
                domains.add(d)
        session_domex[snum] = max(count, len(domains))
    return session_domex


def compute_overhead_ratio(descriptions):
    """Compute overhead keyword ratio. Returns float in [0.01, 1.0]."""
    combined = " ".join(descriptions).lower()
    words = re.findall(r'[a-z]+(?:-[a-z]+)*', combined)
    if not words:
        return 0.5
    overhead_count = sum(1 for w in words if w in OVERHEAD_KEYWORDS)
    productive_count = sum(1 for w in words if w in PRODUCTIVE_KEYWORDS)
    total = overhead_count + productive_count
    if total == 0:
        return 0.5
    ratio = overhead_count / total
    return max(0.01, min(1.0, ratio))


def compute_productive_keyword_density(descriptions):
    """Compute productive keyword density (productive / total words)."""
    combined = " ".join(descriptions).lower()
    words = re.findall(r'[a-z]+(?:-[a-z]+)*', combined)
    if not words:
        return 0.0
    productive_count = sum(1 for w in words if w in PRODUCTIVE_KEYWORDS)
    return productive_count / len(words)


def compute_domains_touched(descriptions):
    """Count distinct domains mentioned in descriptions."""
    combined = " ".join(descriptions).upper()
    found = set()
    for d in DOMAIN_ABBREVS:
        if re.search(r'\b' + d + r'\b', combined):
            found.add(d)
    return max(1, len(found))


def compute_description_length(descriptions):
    """Count total words in session descriptions."""
    combined = " ".join(descriptions)
    return len(combined.split())


def pearson_r(xs, ys):
    """Compute Pearson correlation coefficient."""
    n = len(xs)
    if n < 3:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / (sx * sy)


def spearman_rho(xs, ys):
    """Compute Spearman rank correlation."""
    n = len(xs)
    if n < 3:
        return 0.0

    def rank(vals):
        indexed = sorted(enumerate(vals), key=lambda p: p[1])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and indexed[j + 1][1] == indexed[j][1]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                ranks[indexed[k][0]] = avg_rank
            i = j + 1
        return ranks

    rx = rank(xs)
    ry = rank(ys)
    return pearson_r(rx, ry)


def compute_auc(labels, scores):
    """Compute AUC using trapezoid rule."""
    n = len(labels)
    if n == 0:
        return 0.5
    paired = sorted(zip(scores, labels), key=lambda p: -p[0])
    total_pos = sum(labels)
    total_neg = n - total_pos
    if total_pos == 0 or total_neg == 0:
        return 0.5
    tp = 0
    fp = 0
    prev_tpr = 0.0
    prev_fpr = 0.0
    auc = 0.0
    for _, label in paired:
        if label == 1:
            tp += 1
        else:
            fp += 1
        tpr = tp / total_pos
        fpr = fp / total_neg
        auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2.0
        prev_tpr = tpr
        prev_fpr = fpr
    return auc


def find_optimal_threshold(labels, scores):
    """Find Re_crit that maximizes classification accuracy."""
    if not labels:
        return 0.0, 0.0, {}
    unique_scores = sorted(set(scores))
    best_acc = 0.0
    best_thresh = 0.0
    best_details = {}
    for thresh in unique_scores:
        predicted = [1 if s >= thresh else 0 for s in scores]
        correct = sum(1 for p, l in zip(predicted, labels) if p == l)
        acc = correct / len(labels)
        if acc > best_acc:
            best_acc = acc
            best_thresh = thresh
            tp = sum(1 for p, l in zip(predicted, labels) if p == 1 and l == 1)
            fp = sum(1 for p, l in zip(predicted, labels) if p == 1 and l == 0)
            tn = sum(1 for p, l in zip(predicted, labels) if p == 0 and l == 0)
            fn = sum(1 for p, l in zip(predicted, labels) if p == 0 and l == 1)
            best_details = {
                "threshold": round(thresh, 4),
                "accuracy": round(acc, 4),
                "tp": tp, "fp": fp, "tn": tn, "fn": fn,
                "precision": round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0,
                "recall": round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0,
            }
    return best_thresh, best_acc, best_details


def detect_phase_transition(re_values, lp_values, n_bins=10):
    """Look for phase transition: sharp change in productivity vs Re."""
    if len(re_values) < 10:
        return {"detected": False, "reason": "insufficient data"}
    paired = sorted(zip(re_values, lp_values))
    n = len(paired)
    bin_size = max(1, n // n_bins)
    bins = []
    for i in range(0, n, bin_size):
        chunk = paired[i:i + bin_size]
        if not chunk:
            continue
        re_mean = sum(r for r, _ in chunk) / len(chunk)
        lp_mean = sum(lp for _, lp in chunk) / len(chunk)
        productive_frac = sum(1 for _, lp in chunk if lp > 0) / len(chunk)
        bins.append({
            "re_mean": round(re_mean, 4),
            "lp_mean": round(lp_mean, 4),
            "productive_frac": round(productive_frac, 4),
            "n": len(chunk),
        })
    max_jump = 0.0
    jump_location = None
    for i in range(len(bins) - 1):
        jump = abs(bins[i + 1]["productive_frac"] - bins[i]["productive_frac"])
        if jump > max_jump:
            max_jump = jump
            jump_location = i
    detected = max_jump > 0.3
    result = {
        "detected": detected,
        "max_jump_magnitude": round(max_jump, 4),
        "bins": bins,
    }
    if jump_location is not None:
        result["jump_between_bins"] = [jump_location, jump_location + 1]
        result["jump_re_range"] = [
            bins[jump_location]["re_mean"],
            bins[jump_location + 1]["re_mean"],
        ]
    return result


def evaluate_formulation(name, re_values, lp_values, labels):
    """Evaluate a single Re formulation."""
    if not re_values:
        return {"name": name, "error": "no data"}
    auc = compute_auc(labels, re_values)
    r_pearson = pearson_r(re_values, lp_values)
    r_spearman = spearman_rho(re_values, lp_values)
    _, _, details = find_optimal_threshold(labels, re_values)
    phase = detect_phase_transition(re_values, lp_values)
    median_re = sorted(re_values)[len(re_values) // 2]
    laminar = [lp for rval, lp in zip(re_values, lp_values) if rval < median_re]
    turbulent = [lp for rval, lp in zip(re_values, lp_values) if rval >= median_re]
    return {
        "name": name,
        "n": len(re_values),
        "auc": round(auc, 4),
        "pearson_r": round(r_pearson, 4),
        "spearman_rho": round(r_spearman, 4),
        "optimal_threshold": details,
        "phase_transition": phase,
        "median_re": round(median_re, 4),
        "mean_re": round(sum(re_values) / len(re_values), 4),
        "max_re": round(max(re_values), 4),
        "min_re": round(min(re_values), 4),
        "laminar_mean_lp": round(sum(laminar) / len(laminar), 4) if laminar else 0,
        "turbulent_mean_lp": round(sum(turbulent) / len(turbulent), 4) if turbulent else 0,
    }


def main():
    """Run Reynolds-analog analysis and output results."""
    print("=" * 70)
    print("F-FLD1: Reynolds-Analog Dimensionless Ratio for Swarm Sessions")
    print("=" * 70)

    # Step 1: Parse session log
    print("\n[1] Parsing SESSION-LOG.md...")
    sessions = parse_session_log()
    print(f"    Parsed {len(sessions)} sessions")

    # Step 2: Parse lanes
    print("\n[2] Parsing SWARM-LANES.md + archive for lane counts...")
    session_lanes = parse_lanes_per_session()
    domex_git = count_domex_from_git()
    domex_desc = count_domex_from_descriptions(sessions)
    print(f"    Lane data for {len(session_lanes)} sessions from SWARM-LANES")
    print(f"    DOMEX data for {len(domex_git)} sessions from git log")
    print(f"    DOMEX data for {len(domex_desc)} sessions from descriptions")

    # Step 3: Compute per-session metrics
    print("\n[3] Computing per-session metrics...")
    all_sessions = sorted(sessions.keys())
    time_series = []

    for snum in all_sessions:
        data = sessions[snum]
        lessons = data["lessons"]
        principles = data["principles"]
        productivity = lessons + 0.5 * principles

        lanes_from_file = len(session_lanes.get(snum, set()))
        lanes_from_git = domex_git.get(snum, 0)
        lanes_from_desc = domex_desc.get(snum, 0)
        lanes_touched = max(1, lanes_from_file, lanes_from_git, lanes_from_desc)

        overhead_ratio = compute_overhead_ratio(data["descriptions"])
        productive_density = compute_productive_keyword_density(data["descriptions"])
        domains = compute_domains_touched(data["descriptions"])
        desc_length = compute_description_length(data["descriptions"])

        lp_total = lessons + principles
        label = 1 if lp_total > 0 else 0

        # --- FORMULATIONS ---

        # 1. Full Re (CIRCULAR — includes productivity in numerator)
        re_full = (lanes_touched * productivity) / (overhead_ratio + EPSILON)

        # 2. Full Re log-scaled
        re_full_log = math.log1p(re_full)

        # 3. Structural Re: lanes * domains / overhead (NO productivity)
        #    This is the non-circular predictor
        re_structural = (lanes_touched * domains) / (overhead_ratio + EPSILON)

        # 4. Structural Re log-scaled
        re_structural_log = math.log1p(re_structural)

        # 5. Structural Re with description length as "length scale"
        #    Longer descriptions = more complex sessions = higher Re
        re_scope = (lanes_touched * domains * math.log1p(desc_length)) / (overhead_ratio + EPSILON)

        # 6. Inverse viscosity only: 1 / overhead_ratio
        #    Tests whether low overhead alone predicts productivity
        re_inv_visc = 1.0 / (overhead_ratio + EPSILON)

        # 7. Momentum only: lanes * domains
        #    Tests whether session scope alone predicts productivity
        re_momentum = lanes_touched * domains

        # 8. Productive keyword density (proxy for "intent to produce")
        #    This is NOT circular — it measures words in descriptions, not outcomes
        re_intent = (lanes_touched * productive_density) / (overhead_ratio + EPSILON)

        entry = {
            "session": snum,
            "lessons": round(lessons, 2),
            "principles": round(principles, 2),
            "productivity_score": round(productivity, 2),
            "lp_total": round(lp_total, 2),
            "lanes_touched": lanes_touched,
            "overhead_ratio": round(overhead_ratio, 4),
            "productive_density": round(productive_density, 4),
            "domains_touched": domains,
            "desc_length": desc_length,
            "label_productive": label,
            "re_full": round(re_full, 4),
            "re_full_log": round(re_full_log, 4),
            "re_structural": round(re_structural, 4),
            "re_structural_log": round(re_structural_log, 4),
            "re_scope": round(re_scope, 4),
            "re_inv_visc": round(re_inv_visc, 4),
            "re_momentum": round(re_momentum, 4),
            "re_intent": round(re_intent, 4),
        }
        time_series.append(entry)

    print(f"    Computed metrics for {len(time_series)} sessions")

    # Step 4: Evaluate formulations
    print("\n[4] Evaluating Re formulations...")
    print("    (Formulations marked * are CIRCULAR — they include productivity)")

    lp_values = [e["lp_total"] for e in time_series]
    labels = [e["label_productive"] for e in time_series]
    productivity_scores = [e["productivity_score"] for e in time_series]

    formulation_defs = [
        ("Re_full*", "re_full", True),
        ("Re_full_log*", "re_full_log", True),
        ("Re_structural", "re_structural", False),
        ("Re_structural_log", "re_structural_log", False),
        ("Re_scope", "re_scope", False),
        ("Re_inv_viscosity", "re_inv_visc", False),
        ("Re_momentum", "re_momentum", False),
        ("Re_intent", "re_intent", False),
    ]

    formulations = {}
    for fname, key, circular in formulation_defs:
        values = [e[key] for e in time_series]
        result = evaluate_formulation(fname, values, lp_values, labels)
        result["circular"] = circular
        formulations[fname] = result
        tag = " (CIRCULAR)" if circular else ""
        print(f"\n    {fname}{tag}:")
        print(f"      AUC = {result['auc']:.4f}")
        print(f"      Pearson r = {result['pearson_r']:.4f}")
        print(f"      Spearman rho = {result['spearman_rho']:.4f}")
        if result.get("optimal_threshold"):
            ot = result["optimal_threshold"]
            print(f"      Optimal accuracy = {ot.get('accuracy', 'N/A')}"
                  f" at Re_crit = {ot.get('threshold', 'N/A')}")
        print(f"      Phase transition: {result['phase_transition']['detected']}"
              f" (max jump = {result['phase_transition'].get('max_jump_magnitude', 0):.2f})")
        print(f"      Laminar mean L+P = {result['laminar_mean_lp']:.2f}  |  "
              f"Turbulent mean L+P = {result['turbulent_mean_lp']:.2f}")

    # Step 5: Find best NON-CIRCULAR formulation
    non_circular = {k: v for k, v in formulations.items() if not v.get("circular")}
    best_nc_name = max(non_circular, key=lambda k: non_circular[k]["auc"])
    best_nc = non_circular[best_nc_name]

    best_all_name = max(formulations, key=lambda k: formulations[k]["auc"])
    best_all = formulations[best_all_name]

    print(f"\n{'=' * 70}")
    print(f"BEST NON-CIRCULAR: {best_nc_name}")
    print(f"  AUC = {best_nc['auc']:.4f}")
    print(f"  Pearson r = {best_nc['pearson_r']:.4f}")
    print(f"  Spearman rho = {best_nc['spearman_rho']:.4f}")
    if best_nc.get("optimal_threshold"):
        print(f"  Optimal accuracy = {best_nc['optimal_threshold']['accuracy']:.4f}")
    print(f"\nBEST OVERALL (circular): {best_all_name}")
    print(f"  AUC = {best_all['auc']:.4f}")
    print(f"  Pearson r = {best_all['pearson_r']:.4f}")
    print(f"{'=' * 70}")

    # Step 6: Summary statistics
    total_productive = sum(labels)
    total_unproductive = len(labels) - total_productive
    baseline_rate = total_productive / len(labels) if labels else 0

    print(f"\nDataset summary:")
    print(f"  Total sessions: {len(time_series)}")
    print(f"  Productive (L+P > 0): {total_productive} ({baseline_rate:.1%})")
    print(f"  Unproductive (L+P = 0): {total_unproductive} ({1-baseline_rate:.1%})")

    # Era analysis
    eras = [
        ("S01-S56 (baseline)", 1, 56),
        ("S57-S100 (early growth)", 57, 100),
        ("S101-S186 (Codex era)", 101, 186),
        ("S187-S300 (expansion)", 187, 300),
        ("S301-S376 (maturity)", 301, 376),
    ]
    era_stats = []
    for era_name, s_start, s_end in eras:
        era_entries = [e for e in time_series if s_start <= e["session"] <= s_end]
        if not era_entries:
            continue
        era_re = [e["re_structural"] for e in era_entries]
        era_lp = [e["lp_total"] for e in era_entries]
        era_productive = sum(1 for e in era_entries if e["label_productive"])
        era_overhead = [e["overhead_ratio"] for e in era_entries]
        era_lanes = [e["lanes_touched"] for e in era_entries]
        stat = {
            "era": era_name,
            "n_sessions": len(era_entries),
            "mean_re_structural": round(sum(era_re) / len(era_re), 4),
            "median_re_structural": round(sorted(era_re)[len(era_re) // 2], 4),
            "mean_lp": round(sum(era_lp) / len(era_lp), 4),
            "productive_rate": round(era_productive / len(era_entries), 4),
            "mean_overhead": round(sum(era_overhead) / len(era_overhead), 4),
            "mean_lanes": round(sum(era_lanes) / len(era_lanes), 4),
        }
        era_stats.append(stat)
        print(f"\n  {era_name}:")
        print(f"    n={stat['n_sessions']}, Re_struct={stat['mean_re_structural']:.1f}, "
              f"L+P={stat['mean_lp']:.2f}, productive={stat['productive_rate']:.1%}, "
              f"overhead={stat['mean_overhead']:.3f}, lanes={stat['mean_lanes']:.1f}")

    # Step 7: Correlation matrix
    print(f"\n  Correlation matrix (key variables):")
    vars_for_corr = [
        ("Re_structural", [e["re_structural"] for e in time_series]),
        ("lanes_touched", [float(e["lanes_touched"]) for e in time_series]),
        ("overhead_ratio", [e["overhead_ratio"] for e in time_series]),
        ("domains_touched", [float(e["domains_touched"]) for e in time_series]),
        ("productive_density", [e["productive_density"] for e in time_series]),
        ("L+P", [e["lp_total"] for e in time_series]),
    ]
    print(f"    {'':20s}", end="")
    for name, _ in vars_for_corr:
        print(f" {name:>12s}", end="")
    print()
    for name_i, vals_i in vars_for_corr:
        print(f"    {name_i:20s}", end="")
        for name_j, vals_j in vars_for_corr:
            r = pearson_r(vals_i, vals_j)
            print(f" {r:12.4f}", end="")
        print()

    # Step 8: Detailed component analysis
    print(f"\n  Component predictive power (AUC for each component alone):")
    component_aucs = {}
    for cname, ckey in [
        ("lanes_touched", "lanes_touched"),
        ("overhead_ratio", "overhead_ratio"),
        ("domains_touched", "domains_touched"),
        ("productive_density", "productive_density"),
        ("desc_length", "desc_length"),
    ]:
        cvals = [float(e[ckey]) for e in time_series]
        # For overhead, lower = better, so invert
        if cname == "overhead_ratio":
            cvals_pred = [-v for v in cvals]
        else:
            cvals_pred = cvals
        cauc = compute_auc(labels, cvals_pred)
        cr = pearson_r(cvals, lp_values)
        component_aucs[cname] = {"auc": round(cauc, 4), "pearson_r_vs_lp": round(cr, 4)}
        print(f"    {cname:25s}: AUC={cauc:.4f}, r(vs L+P)={cr:.4f}")

    # Step 9: Build output JSON
    output = {
        "experiment": "F-FLD1 Reynolds-Analog Dimensionless Ratio",
        "session": "S376",
        "date": "2026-03-01",
        "method": "Reynolds number analog for swarm sessions",
        "formula": {
            "full_circular": "Re = (lanes * (L + 0.5*P)) / (overhead_ratio + 0.01)",
            "structural_non_circular": "Re = (lanes * domains) / (overhead_ratio + 0.01)",
            "scope": "Re = (lanes * domains * log(1+desc_len)) / (overhead + 0.01)",
            "inv_viscosity": "1 / (overhead_ratio + 0.01)",
            "momentum": "lanes * domains",
            "intent": "(lanes * productive_keyword_density) / (overhead + 0.01)",
        },
        "circularity_note": (
            "Re_full includes productivity in the numerator, making it trivially "
            "perfect (AUC=1.0) for predicting productivity. The scientifically "
            "interesting question is whether STRUCTURAL Re (using only lanes, "
            "domains, overhead) predicts productivity."
        ),
        "parameters": {
            "epsilon": EPSILON,
            "overhead_keywords": sorted(OVERHEAD_KEYWORDS),
            "productive_keywords": sorted(PRODUCTIVE_KEYWORDS),
        },
        "dataset": {
            "n_sessions": len(time_series),
            "n_productive": total_productive,
            "n_unproductive": total_unproductive,
            "baseline_productive_rate": round(baseline_rate, 4),
        },
        "results": {
            "best_non_circular": best_nc_name,
            "best_circular": best_all_name,
            "formulations": formulations,
            "component_predictive_power": component_aucs,
            "era_analysis": era_stats,
        },
        "interpretation": {},
        "time_series": time_series,
    }

    # Build interpretation
    interp = output["interpretation"]
    interp["analogy_validity"] = (
        "Re_swarm captures session 'task momentum' vs 'friction'. "
        "High Re = many lanes, broad scope, low overhead. "
        "Low Re = few lanes, narrow scope, high maintenance."
    )
    interp["circularity"] = (
        f"Full Re (AUC={best_all['auc']:.3f}) is circular — productivity is in the numerator. "
        f"Structural Re (AUC={best_nc['auc']:.3f}) is the honest test."
    )
    if best_nc["auc"] > 0.7:
        interp["structural_finding"] = (
            f"STRONG: Structural Re ({best_nc_name}) achieves AUC={best_nc['auc']:.3f}. "
            "Session structure (lanes, domains, overhead) predicts productivity well. "
            "The Reynolds analogy has genuine predictive power."
        )
    elif best_nc["auc"] > 0.6:
        interp["structural_finding"] = (
            f"MODERATE: Structural Re ({best_nc_name}) achieves AUC={best_nc['auc']:.3f}. "
            "Session structure has some predictive power for productivity, "
            "but other factors also matter."
        )
    else:
        interp["structural_finding"] = (
            f"WEAK: Structural Re ({best_nc_name}) achieves AUC={best_nc['auc']:.3f}. "
            "Session structure alone does not strongly predict productivity. "
            "The Reynolds analogy is descriptive, not predictive."
        )

    interp["phase_transition"] = (
        "Sharp Re_crit detected" if best_nc["phase_transition"]["detected"]
        else "No sharp phase transition; productivity varies smoothly with Re"
    )
    interp["laminar_vs_turbulent"] = (
        f"Below median Re ('laminar'): mean L+P = {best_nc['laminar_mean_lp']:.2f}. "
        f"Above median Re ('turbulent'): mean L+P = {best_nc['turbulent_mean_lp']:.2f}. "
    )
    if best_nc['turbulent_mean_lp'] > 0 and best_nc['laminar_mean_lp'] > 0:
        ratio = best_nc['turbulent_mean_lp'] / best_nc['laminar_mean_lp']
        interp["laminar_vs_turbulent"] += (
            f"Ratio = {ratio:.2f}x. "
            f"{'Strong regime separation.' if ratio > 2 else 'Moderate regime separation.'}"
        )

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "f-fld1-reynolds-measure-s376.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[Output] Written to {out_path}")

    return output


if __name__ == "__main__":
    main()
