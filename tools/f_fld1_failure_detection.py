#!/usr/bin/env python3
"""F-FLD1: Reynolds regime predictor as session failure detector.

Tests whether Re_structural = (lanes × domains) / (overhead + ε)
can predict session failure (abandoned lanes, zero L+P output).

Prior: S376 measured Re_structural AUC=0.870 for productive vs
unproductive. This experiment tests a harder target: failure detection.
"""

import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def parse_session_log():
    """Parse SESSION-LOG.md for per-session L+P production."""
    path = ROOT / "memory" / "SESSION-LOG.md"
    sessions = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("Never") or line.startswith("Format"):
            continue
        # e.g. "S379	| 2026-03-01 | +1L (L-725) +0P | ..."
        m = re.match(r"S(\d+[ab]?)\s*\|", line)
        if not m:
            continue
        sid = m.group(1)
        # Extract L and P counts
        l_match = re.search(r"\+(\d+)L", line)
        p_match = re.search(r"\+(\d+)P", line)
        lessons = int(l_match.group(1)) if l_match else 0
        principles = int(p_match.group(1)) if p_match else 0
        # Aggregate multiple entries for same session
        if sid in sessions:
            sessions[sid]["lessons"] += lessons
            sessions[sid]["principles"] += principles
            sessions[sid]["entries"] += 1
        else:
            sessions[sid] = {
                "lessons": lessons,
                "principles": principles,
                "entries": 1,
                "summary": line.split("|")[-1].strip() if "|" in line else "",
            }
    return sessions


def parse_lanes():
    """Parse SWARM-LANES.md and archive for per-session lane status."""
    lane_data = defaultdict(lambda: {"total": 0, "merged": 0, "abandoned": 0, "domains": set()})

    for fname in ["tasks/SWARM-LANES.md", "tasks/SWARM-LANES-ARCHIVE.md"]:
        path = ROOT / fname
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 12:
                continue
            # | Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |
            lane_id = parts[2] if len(parts) > 2 else ""
            session = parts[3] if len(parts) > 3 else ""
            scope_key = parts[9] if len(parts) > 9 else ""
            etc_field = parts[10] if len(parts) > 10 else ""
            status = parts[11] if len(parts) > 11 else ""

            # Normalize session
            s_match = re.match(r"S?(\d+)", session)
            if not s_match:
                continue
            sid = s_match.group(1)

            # Extract domain from lane ID or scope-key
            domain = ""
            lane_domain = re.match(r"DOMEX-([A-Z]+)-", lane_id)
            if lane_domain:
                domain = lane_domain.group(1).lower()
            elif "domains/" in scope_key:
                dm = re.search(r"domains/([^/]+)", scope_key)
                if dm:
                    domain = dm.group(1)

            lane_data[sid]["total"] += 1
            if domain:
                lane_data[sid]["domains"].add(domain)
            if "MERGED" in status:
                lane_data[sid]["merged"] += 1
            elif "ABANDONED" in status:
                lane_data[sid]["abandoned"] += 1

    return lane_data


def classify_overhead(summary):
    """Classify a session summary as overhead-heavy."""
    overhead_keywords = [
        "state-sync", "sync", "trim", "compact", "cleanup", "maintenance",
        "fix", "repair", "recovery", "push", "handoff", "rescue", "restore",
        "reswarm", "hygiene", "drift", "dedup", "correction", "consolidation",
        "validator", "stale", "backlog", "periodics", "health-check", "minimal",
    ]
    productive_keywords = [
        "domex", "experiment", "frontier", "confirmed", "falsified", "measured",
        "built", "created", "analysis", "hypothesis", "lesson", "discovered",
        "implemented", "resolved", "tested", "council", "dream", "harvest",
        "correlation", "evidence", "investigated", "observed", "baseline",
    ]
    summary_lower = summary.lower()
    overhead_hits = sum(1 for k in overhead_keywords if k in summary_lower)
    productive_hits = sum(1 for k in productive_keywords if k in summary_lower)
    total = overhead_hits + productive_hits
    if total == 0:
        return 0.5
    return overhead_hits / total


def compute_re_structural(n_lanes, n_domains, overhead_ratio, epsilon=0.01):
    """Re_structural = (lanes × domains) / (overhead_ratio + ε)"""
    return (n_lanes * n_domains) / (overhead_ratio + epsilon)


def compute_auc(labels, scores):
    """Compute AUC-ROC from binary labels and continuous scores."""
    if len(labels) < 2 or len(set(labels)) < 2:
        return float("nan")

    # Sort by score descending
    pairs = sorted(zip(scores, labels), key=lambda x: -x[0])

    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")

    # Wilcoxon-Mann-Whitney statistic
    tp = 0
    fp = 0
    auc_sum = 0.0
    prev_score = None

    for score, label in pairs:
        if prev_score is not None and score != prev_score:
            pass  # threshold changed
        if label == 1:
            tp += 1
        else:
            fp += 1
            auc_sum += tp  # count true positives ranked above this false positive

    return auc_sum / (n_pos * n_neg) if (n_pos * n_neg) > 0 else float("nan")


def main():
    sessions = parse_session_log()
    lane_data = parse_lanes()

    # Build feature matrix
    records = []
    for sid, sdata in sessions.items():
        # Filter to numeric sessions only
        if not sid.isdigit():
            continue
        sid_int = int(sid)
        if sid_int < 180:  # pre-structured era
            continue

        lp = sdata["lessons"] + sdata["principles"]
        overhead_ratio = classify_overhead(sdata.get("summary", ""))

        lanes = lane_data.get(sid, {})
        n_lanes = lanes.get("total", 0) if isinstance(lanes, dict) else 0
        n_domains = len(lanes.get("domains", set())) if isinstance(lanes, dict) else 0
        n_abandoned = lanes.get("abandoned", 0) if isinstance(lanes, dict) else 0
        n_merged = lanes.get("merged", 0) if isinstance(lanes, dict) else 0

        # Use at least 1 for lanes/domains to avoid zero
        effective_lanes = max(n_lanes, 1)
        effective_domains = max(n_domains, 1)

        re_structural = compute_re_structural(effective_lanes, effective_domains, overhead_ratio)

        # Failure definitions
        zero_output = 1 if lp == 0 else 0
        has_abandoned = 1 if n_abandoned > 0 else 0
        high_abandon_rate = 1 if (n_lanes > 0 and n_abandoned / n_lanes > 0.5) else 0
        # Composite: zero output OR majority abandoned
        failed = 1 if (zero_output or high_abandon_rate) else 0

        records.append({
            "session": sid_int,
            "lp": lp,
            "lessons": sdata["lessons"],
            "principles": sdata["principles"],
            "n_lanes": n_lanes,
            "n_domains": n_domains,
            "n_merged": n_merged,
            "n_abandoned": n_abandoned,
            "overhead_ratio": round(overhead_ratio, 3),
            "re_structural": round(re_structural, 3),
            "zero_output": zero_output,
            "has_abandoned": has_abandoned,
            "high_abandon_rate": high_abandon_rate,
            "failed": failed,
        })

    records.sort(key=lambda r: r["session"])

    # ---- Analysis ----
    n = len(records)
    n_failed = sum(r["failed"] for r in records)
    n_zero = sum(r["zero_output"] for r in records)
    n_abandoned_sessions = sum(r["has_abandoned"] for r in records)

    print(f"=== F-FLD1: Reynolds Failure Detection (S180-S{records[-1]['session']}) ===")
    print(f"Sessions analyzed: {n}")
    print(f"Failed (zero output OR >50% abandoned): {n_failed} ({100*n_failed/n:.1f}%)")
    print(f"  Zero output: {n_zero} ({100*n_zero/n:.1f}%)")
    print(f"  Any abandoned lanes: {n_abandoned_sessions} ({100*n_abandoned_sessions/n:.1f}%)")
    print()

    # AUC for failure detection (higher Re = less failure expected)
    # Invert Re for AUC calculation: low Re should predict failure
    labels_failed = [r["failed"] for r in records]
    scores_inv_re = [-r["re_structural"] for r in records]  # negate so low Re → high score → failure
    auc_failed = compute_auc(labels_failed, scores_inv_re)

    # AUC for zero output
    labels_zero = [r["zero_output"] for r in records]
    auc_zero = compute_auc(labels_zero, scores_inv_re)

    print(f"AUC (Re_structural → failure): {auc_failed:.3f}")
    print(f"AUC (Re_structural → zero_output): {auc_zero:.3f}")
    print()

    # Regime analysis at Re_crit = 1.575 (from S376)
    re_crit = 1.575
    turbulent = [r for r in records if r["re_structural"] > re_crit]
    laminar = [r for r in records if r["re_structural"] <= re_crit]

    turb_fail = sum(r["failed"] for r in turbulent)
    lam_fail = sum(r["failed"] for r in laminar)

    print(f"--- Regime Analysis (Re_crit = {re_crit}) ---")
    print(f"Turbulent (Re > {re_crit}): {len(turbulent)} sessions, {turb_fail} failed ({100*turb_fail/max(len(turbulent),1):.1f}%)")
    print(f"Laminar (Re ≤ {re_crit}): {len(laminar)} sessions, {lam_fail} failed ({100*lam_fail/max(len(laminar),1):.1f}%)")
    print()

    # Sweep thresholds for optimal Re_crit
    best_sep = 0
    best_crit = 0
    for r in records:
        crit = r["re_structural"]
        above = [x for x in records if x["re_structural"] > crit]
        below = [x for x in records if x["re_structural"] <= crit]
        if len(above) < 5 or len(below) < 5:
            continue
        fail_above = sum(x["failed"] for x in above) / len(above)
        fail_below = sum(x["failed"] for x in below) / len(below)
        sep = fail_below - fail_above
        if sep > best_sep:
            best_sep = sep
            best_crit = crit

    print(f"--- Threshold Sweep ---")
    print(f"Optimal Re_crit: {best_crit:.3f} (failure rate separation: {100*best_sep:.1f}pp)")
    above_opt = [r for r in records if r["re_structural"] > best_crit]
    below_opt = [r for r in records if r["re_structural"] <= best_crit]
    fail_above = sum(r["failed"] for r in above_opt) / max(len(above_opt), 1)
    fail_below = sum(r["failed"] for r in below_opt) / max(len(below_opt), 1)
    print(f"  Above (Re > {best_crit:.3f}): {len(above_opt)} sessions, fail rate {100*fail_above:.1f}%")
    print(f"  Below (Re ≤ {best_crit:.3f}): {len(below_opt)} sessions, fail rate {100*fail_below:.1f}%")
    print()

    # Era analysis
    eras = [
        ("Pre-DOMEX", 180, 309),
        ("Early-DOMEX", 310, 359),
        ("Mature", 360, 999),
    ]
    print("--- Era Analysis ---")
    for era_name, lo, hi in eras:
        era_recs = [r for r in records if lo <= r["session"] <= hi]
        if not era_recs:
            continue
        era_fail = sum(r["failed"] for r in era_recs)
        era_re_mean = sum(r["re_structural"] for r in era_recs) / len(era_recs)
        print(f"{era_name} (S{lo}-S{hi}): n={len(era_recs)}, failed={era_fail} ({100*era_fail/len(era_recs):.1f}%), mean Re={era_re_mean:.2f}")
    print()

    # Simple commit count comparison (from S376: R²=0.37)
    # Test if L+P alone predicts failure better
    print("--- Alternative Predictors ---")
    auc_lp = compute_auc(labels_failed, [-r["lp"] for r in records])
    auc_lanes = compute_auc(labels_failed, [-r["n_lanes"] for r in records])
    print(f"AUC (L+P → failure): {auc_lp:.3f} (trivially perfect)")
    print(f"AUC (n_lanes → failure): {auc_lanes:.3f}")
    print()

    # Summary statistics
    re_values = [r["re_structural"] for r in records]
    print(f"--- Re_structural Distribution ---")
    print(f"Mean: {sum(re_values)/len(re_values):.2f}, Median: {sorted(re_values)[len(re_values)//2]:.2f}")
    print(f"Min: {min(re_values):.2f}, Max: {max(re_values):.2f}")

    # Build experiment JSON
    result = {
        "experiment": "f-fld1-failure-detection-s380",
        "frontier": "F-FLD1",
        "domain": "fluid-dynamics",
        "session": "S380",
        "date": "2026-03-01",
        "type": "empirical-measurement",
        "description": "Test Re_structural as session failure predictor (not just productivity proxy). Failure = zero L+P output OR >50% lanes abandoned.",
        "expect": "Re_structural predicts failure with AUC>0.70. Failure rate <20% for Re>1.575 vs >40% for Re<1.575. Turbulent sessions fail less.",
        "actual": {
            "n_sessions": n,
            "n_failed": n_failed,
            "failure_rate": round(n_failed / n, 3),
            "n_zero_output": n_zero,
            "n_abandoned_sessions": n_abandoned_sessions,
            "auc_failure": round(auc_failed, 3),
            "auc_zero_output": round(auc_zero, 3),
            "regime_at_1575": {
                "turbulent": {
                    "n": len(turbulent),
                    "failed": turb_fail,
                    "failure_rate": round(turb_fail / max(len(turbulent), 1), 3),
                },
                "laminar": {
                    "n": len(laminar),
                    "failed": lam_fail,
                    "failure_rate": round(lam_fail / max(len(laminar), 1), 3),
                },
            },
            "optimal_threshold": {
                "re_crit": round(best_crit, 3),
                "separation_pp": round(100 * best_sep, 1),
                "above_failure_rate": round(fail_above, 3),
                "below_failure_rate": round(fail_below, 3),
            },
            "alternative_predictors": {
                "auc_lp": round(auc_lp, 3),
                "auc_n_lanes": round(auc_lanes, 3),
            },
            "re_distribution": {
                "mean": round(sum(re_values) / len(re_values), 2),
                "median": round(sorted(re_values)[len(re_values) // 2], 2),
                "min": round(min(re_values), 2),
                "max": round(max(re_values), 2),
            },
        },
        "diff": "",  # filled after analysis
        "methodology": "SESSION-LOG parsed for L+P production. SWARM-LANES parsed for abandoned/merged counts. Overhead classified by keyword matching (26 overhead vs 22 productive keywords). Re_structural = (lanes × domains) / (overhead_ratio + 0.01). AUC computed via Wilcoxon-Mann-Whitney. Threshold sweep for optimal Re_crit.",
        "per_session": records,
    }

    # Write experiment
    out_path = ROOT / "experiments" / "fluid-dynamics" / "f-fld1-failure-detection-s380.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nArtifact written: {out_path.relative_to(ROOT)}")

    return result


if __name__ == "__main__":
    main()
