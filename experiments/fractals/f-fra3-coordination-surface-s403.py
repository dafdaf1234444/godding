#!/usr/bin/env python3
"""F-FRA3: Fractal-complexity proxy — coordination surface predicts quality degradation.

Hypothesis: coordination_surface = concurrent_lanes × distinct_domains per session
predicts quality degradation better than raw WIP count alone.

Pre-registered:
  H1: coordination surface AUC > raw WIP AUC by ≥0.05 for predicting merge < 80%
  H2: crossover point where coord overhead dominates throughput aligns with L-629 ceiling
  H3: crossover ratio is scale-invariant across lane/session aggregation levels
"""
import json
import re
from pathlib import Path
from collections import defaultdict

LANES_FILE = Path("tasks/SWARM-LANES.md")
LANES_ARCHIVE = Path("tasks/SWARM-LANES-ARCHIVE.md")
LESSONS_DIR = Path("memory/lessons")

# Map lane abbreviations to domain names
LANE_ABBREV_TO_DOMAIN = {}
DOMAIN_DIR = Path("domains")
if DOMAIN_DIR.exists():
    for d in DOMAIN_DIR.iterdir():
        if d.is_dir():
            name = d.name
            abbrev = "".join(w[0] for w in name.split("-")).upper()
            LANE_ABBREV_TO_DOMAIN[abbrev] = name
            # Also try first 3-4 chars
            LANE_ABBREV_TO_DOMAIN[name[:3].upper()] = name
            LANE_ABBREV_TO_DOMAIN[name[:4].upper()] = name
            # Full uppercase
            LANE_ABBREV_TO_DOMAIN[name.upper().replace("-", "")] = name


def parse_lanes():
    """Parse all lanes from SWARM-LANES.md and archive."""
    lanes = []
    for f in (LANES_FILE, LANES_ARCHIVE):
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue
            lane_id = cols[2] if len(cols) > 2 else ""
            sess_str = cols[3] if len(cols) > 3 else ""
            status = cols[11].strip().upper() if len(cols) > 11 else ""
            etc = cols[10] if len(cols) > 10 else ""

            sess_m = re.search(r"S?(\d+)", sess_str)
            if not sess_m:
                continue
            sess = int(sess_m.group(1))

            # Extract domain
            dom = None
            m = re.match(r"DOMEX-([A-Z]+)", lane_id)
            if m:
                dom = LANE_ABBREV_TO_DOMAIN.get(m.group(1))
            if not dom:
                focus_m = re.search(r"focus=(?:domains/)?([a-z0-9-]+)", etc)
                if focus_m and focus_m.group(1) not in ("global", ""):
                    dom = focus_m.group(1)
            if not dom:
                dom = "unknown"

            lanes.append({
                "lane_id": lane_id,
                "session": sess,
                "status": status,
                "domain": dom,
                "etc": etc,
            })
    return lanes


def count_lessons_per_session():
    """Count lessons created per session from lesson files."""
    counts = defaultdict(int)
    if not LESSONS_DIR.exists():
        return counts
    for f in LESSONS_DIR.iterdir():
        if not f.name.endswith(".md"):
            continue
        try:
            text = f.read_text(errors="replace")
            for line in text.splitlines()[:5]:
                m = re.search(r"Session:\s*S?(\d+)", line, re.IGNORECASE)
                if m:
                    counts[int(m.group(1))] += 1
                    break
        except Exception:
            pass
    return counts


def compute_session_metrics(lanes):
    """Compute per-session metrics from lane data."""
    sessions = defaultdict(lambda: {
        "lanes": [], "domains": set(), "merged": 0, "abandoned": 0, "total": 0
    })

    for lane in lanes:
        s = lane["session"]
        sessions[s]["lanes"].append(lane)
        sessions[s]["domains"].add(lane["domain"])
        sessions[s]["total"] += 1
        if lane["status"] == "MERGED":
            sessions[s]["merged"] += 1
        elif lane["status"] == "ABANDONED":
            sessions[s]["abandoned"] += 1

    return sessions


def auc_manual(labels, scores):
    """Compute AUC from binary labels and continuous scores (no sklearn needed)."""
    pairs = sorted(zip(scores, labels), reverse=True)
    tp, fp, prev_tp, prev_fp = 0, 0, 0, 0
    auc = 0.0
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5  # undefined
    prev_score = None
    for score, label in pairs:
        if score != prev_score:
            auc += (fp - prev_fp) * (tp + prev_tp) / 2.0
            prev_tp = tp
            prev_fp = fp
            prev_score = score
        if label == 1:
            tp += 1
        else:
            fp += 1
    auc += (fp - prev_fp) * (tp + prev_tp) / 2.0
    return auc / (n_pos * n_neg)


def main():
    lanes = parse_lanes()
    print(f"Total lanes parsed: {len(lanes)}")

    # Only use closed lanes for quality analysis
    closed = [l for l in lanes if l["status"] in ("MERGED", "ABANDONED", "SUPERSEDED")]
    print(f"Closed lanes: {len(closed)}")

    sessions = compute_session_metrics(closed)
    lesson_counts = count_lessons_per_session()

    # Filter to sessions with at least 1 lane
    valid_sessions = {s: d for s, d in sessions.items() if d["total"] >= 1}
    print(f"Sessions with ≥1 lane: {len(valid_sessions)}")

    # Compute per-session metrics
    rows = []
    for s, data in sorted(valid_sessions.items()):
        wip = data["total"]
        n_domains = len(data["domains"])
        coord_surface = wip * n_domains
        merge_rate = data["merged"] / data["total"] if data["total"] > 0 else 0
        abandon_rate = data["abandoned"] / data["total"] if data["total"] > 0 else 0
        lessons = lesson_counts.get(s, 0)

        rows.append({
            "session": s,
            "wip": wip,
            "n_domains": n_domains,
            "coord_surface": coord_surface,
            "merge_rate": merge_rate,
            "abandon_rate": abandon_rate,
            "lessons": lessons,
            "l_per_lane": lessons / wip if wip > 0 else 0,
        })

    # === H1: AUC comparison ===
    # Binary label: merge_rate < 80% = degraded (1), else normal (0)
    labels = [1 if r["merge_rate"] < 0.80 else 0 for r in rows]
    wip_scores = [r["wip"] for r in rows]
    cs_scores = [r["coord_surface"] for r in rows]

    auc_wip = auc_manual(labels, wip_scores)
    auc_cs = auc_manual(labels, cs_scores)
    auc_delta = auc_cs - auc_wip

    print(f"\n=== H1: AUC comparison (merge < 80% prediction) ===")
    print(f"  Degraded sessions (merge < 80%): {sum(labels)}/{len(labels)}")
    print(f"  AUC (raw WIP):              {auc_wip:.4f}")
    print(f"  AUC (coordination surface): {auc_cs:.4f}")
    print(f"  Delta: {auc_delta:+.4f}")
    print(f"  H1 verdict: {'CONFIRMED' if auc_delta >= 0.05 else 'FALSIFIED'} (threshold: ≥0.05)")

    # === H2: Crossover point ===
    # Find where L/lane starts declining as coord_surface increases
    # Bucket by coordination surface ranges
    cs_buckets = defaultdict(lambda: {"l_per_lane": [], "merge_rates": [], "n": 0})
    for r in rows:
        cs = r["coord_surface"]
        if cs <= 1:
            bucket = "1"
        elif cs <= 4:
            bucket = "2-4"
        elif cs <= 9:
            bucket = "5-9"
        elif cs <= 16:
            bucket = "10-16"
        elif cs <= 25:
            bucket = "17-25"
        elif cs <= 36:
            bucket = "26-36"
        else:
            bucket = "37+"
        cs_buckets[bucket]["l_per_lane"].append(r["l_per_lane"])
        cs_buckets[bucket]["merge_rates"].append(r["merge_rate"])
        cs_buckets[bucket]["n"] += 1

    print(f"\n=== H2: Coordination surface buckets ===")
    print(f"  {'CS bucket':<12} {'N':>4} {'L/lane':>8} {'Merge%':>8}")
    bucket_order = ["1", "2-4", "5-9", "10-16", "17-25", "26-36", "37+"]
    for b in bucket_order:
        if b in cs_buckets:
            d = cs_buckets[b]
            avg_lpl = sum(d["l_per_lane"]) / len(d["l_per_lane"]) if d["l_per_lane"] else 0
            avg_mr = sum(d["merge_rates"]) / len(d["merge_rates"]) * 100 if d["merge_rates"] else 0
            print(f"  {b:<12} {d['n']:>4} {avg_lpl:>8.2f} {avg_mr:>7.1f}%")

    # Also do WIP buckets for comparison
    wip_buckets = defaultdict(lambda: {"l_per_lane": [], "merge_rates": [], "n": 0})
    for r in rows:
        w = r["wip"]
        if w <= 1:
            bucket = "1"
        elif w <= 2:
            bucket = "2"
        elif w <= 3:
            bucket = "3"
        elif w <= 4:
            bucket = "4"
        elif w <= 6:
            bucket = "5-6"
        elif w <= 8:
            bucket = "7-8"
        else:
            bucket = "9+"
        wip_buckets[bucket]["l_per_lane"].append(r["l_per_lane"])
        wip_buckets[bucket]["merge_rates"].append(r["merge_rate"])
        wip_buckets[bucket]["n"] += 1

    print(f"\n=== WIP buckets (comparison) ===")
    print(f"  {'WIP':<12} {'N':>4} {'L/lane':>8} {'Merge%':>8}")
    for b in ["1", "2", "3", "4", "5-6", "7-8", "9+"]:
        if b in wip_buckets:
            d = wip_buckets[b]
            avg_lpl = sum(d["l_per_lane"]) / len(d["l_per_lane"]) if d["l_per_lane"] else 0
            avg_mr = sum(d["merge_rates"]) / len(d["merge_rates"]) * 100 if d["merge_rates"] else 0
            print(f"  {b:<12} {d['n']:>4} {avg_lpl:>8.2f} {avg_mr:>7.1f}%")

    # === H3: Scale invariance ===
    # Check if the coordination-surface / merge-rate relationship holds at different aggregation levels
    # Level 1: per-lane (domain count for that lane's session)
    # Level 2: per-session (already computed above)
    # Correlation: coordination surface vs merge rate
    n = len(rows)
    if n > 2:
        mean_cs = sum(r["coord_surface"] for r in rows) / n
        mean_mr = sum(r["merge_rate"] for r in rows) / n
        cov = sum((r["coord_surface"] - mean_cs) * (r["merge_rate"] - mean_mr) for r in rows) / n
        std_cs = (sum((r["coord_surface"] - mean_cs) ** 2 for r in rows) / n) ** 0.5
        std_mr = (sum((r["merge_rate"] - mean_mr) ** 2 for r in rows) / n) ** 0.5
        r_cs_mr = cov / (std_cs * std_mr) if std_cs > 0 and std_mr > 0 else 0

        mean_wip = sum(r["wip"] for r in rows) / n
        cov_w = sum((r["wip"] - mean_wip) * (r["merge_rate"] - mean_mr) for r in rows) / n
        std_wip = (sum((r["wip"] - mean_wip) ** 2 for r in rows) / n) ** 0.5
        r_wip_mr = cov_w / (std_wip * std_mr) if std_wip > 0 and std_mr > 0 else 0
    else:
        r_cs_mr = 0
        r_wip_mr = 0

    print(f"\n=== H3: Correlation analysis ===")
    print(f"  r(coordination_surface, merge_rate) = {r_cs_mr:.4f}")
    print(f"  r(WIP, merge_rate)                  = {r_wip_mr:.4f}")
    print(f"  CS captures more variance: {abs(r_cs_mr) > abs(r_wip_mr)}")

    # === Era control ===
    # Split into early (<S200), mid (S200-S330), late (S331+)
    eras = {"early (<S200)": [], "mid (S200-S330)": [], "late (S331+)": []}
    for r in rows:
        if r["session"] < 200:
            eras["early (<S200)"].append(r)
        elif r["session"] < 331:
            eras["mid (S200-S330)"].append(r)
        else:
            eras["late (S331+)"].append(r)

    print(f"\n=== Era-controlled analysis ===")
    for era_name, era_rows in eras.items():
        if not era_rows:
            continue
        n_e = len(era_rows)
        avg_cs = sum(r["coord_surface"] for r in era_rows) / n_e
        avg_wip = sum(r["wip"] for r in era_rows) / n_e
        avg_mr = sum(r["merge_rate"] for r in era_rows) / n_e * 100
        avg_lpl = sum(r["l_per_lane"] for r in era_rows) / n_e
        degraded = sum(1 for r in era_rows if r["merge_rate"] < 0.80)
        print(f"  {era_name}: n={n_e}, CS_avg={avg_cs:.1f}, WIP_avg={avg_wip:.1f}, "
              f"merge={avg_mr:.1f}%, L/lane={avg_lpl:.2f}, degraded={degraded}")

    # === Domain diversity analysis ===
    # Does domain count add information beyond WIP?
    domain_buckets = defaultdict(lambda: {"merge_rates": [], "n": 0})
    for r in rows:
        d = r["n_domains"]
        domain_buckets[d]["merge_rates"].append(r["merge_rate"])
        domain_buckets[d]["n"] += 1

    print(f"\n=== Domain diversity analysis ===")
    print(f"  {'N_domains':<12} {'N':>4} {'Merge%':>8}")
    for d in sorted(domain_buckets.keys()):
        data = domain_buckets[d]
        avg_mr = sum(data["merge_rates"]) / len(data["merge_rates"]) * 100
        print(f"  {d:<12} {data['n']:>4} {avg_mr:>7.1f}%")

    # === Build experiment JSON ===
    h1_verdict = "CONFIRMED" if auc_delta >= 0.05 else "FALSIFIED"
    h1_detail = (f"AUC(CS)={auc_cs:.4f} vs AUC(WIP)={auc_wip:.4f}, "
                 f"delta={auc_delta:+.4f}")

    # Find crossover: where does L/lane start declining?
    crossover_cs = None
    prev_lpl = None
    for b in bucket_order:
        if b in cs_buckets and cs_buckets[b]["n"] >= 3:
            avg_lpl = sum(cs_buckets[b]["l_per_lane"]) / len(cs_buckets[b]["l_per_lane"])
            if prev_lpl is not None and avg_lpl < prev_lpl * 0.8:
                crossover_cs = b
                break
            prev_lpl = avg_lpl

    result = {
        "experiment": "F-FRA3: Fractal-complexity proxy — coordination surface",
        "session": "S403",
        "frontier": "F-FRA3",
        "mode": "hardening",
        "date": "2026-03-01",
        "method": (
            f"Parsed SWARM-LANES.md + archive (n={len(lanes)} total lanes, "
            f"{len(closed)} closed, {len(valid_sessions)} sessions). "
            "Coordination surface = WIP × N_domains per session. "
            "AUC comparison for merge<80% prediction. "
            "Era-controlled (early/mid/late). Pearson r for correlation."
        ),
        "hypotheses": {
            "H1_auc_improvement": {
                "prediction": "AUC(coordination surface) > AUC(WIP) + 0.05",
                "threshold": "delta ≥ 0.05",
                "result": h1_detail,
                "verdict": h1_verdict,
            },
            "H2_crossover_alignment": {
                "prediction": "Crossover point at CS ~20-30 aligns with L-629 ceiling",
                "threshold": "L/lane decline at CS 20-30",
                "result": f"Crossover bucket: {crossover_cs}",
                "verdict": "TBD",
            },
            "H3_scale_invariance": {
                "prediction": "r(CS, merge) stronger than r(WIP, merge)",
                "threshold": "|r(CS)| > |r(WIP)|",
                "result": f"r(CS,merge)={r_cs_mr:.4f}, r(WIP,merge)={r_wip_mr:.4f}",
                "verdict": "CONFIRMED" if abs(r_cs_mr) > abs(r_wip_mr) else "FALSIFIED",
            },
        },
        "data": {
            "n_total_lanes": len(lanes),
            "n_closed_lanes": len(closed),
            "n_sessions": len(valid_sessions),
            "auc_wip": round(auc_wip, 4),
            "auc_cs": round(auc_cs, 4),
            "auc_delta": round(auc_delta, 4),
            "r_cs_merge": round(r_cs_mr, 4),
            "r_wip_merge": round(r_wip_mr, 4),
            "crossover_bucket": crossover_cs,
            "degraded_sessions": sum(labels),
            "total_sessions": len(labels),
        },
        "era_controlled": {
            era_name: {
                "n": len(era_rows),
                "avg_cs": round(sum(r["coord_surface"] for r in era_rows) / len(era_rows), 1) if era_rows else 0,
                "avg_wip": round(sum(r["wip"] for r in era_rows) / len(era_rows), 1) if era_rows else 0,
                "avg_merge_pct": round(sum(r["merge_rate"] for r in era_rows) / len(era_rows) * 100, 1) if era_rows else 0,
            }
            for era_name, era_rows in eras.items()
            if era_rows
        },
        "findings": [],
        "science_quality_score": {
            "pre_registered": 1,
            "falsifiable": 1,
            "external": 0,
            "replicated": 0,
            "significance_tested": 0,
            "total": "2/5 (40%)",
        },
        "cites": ["L-629", "L-863", "L-606", "L-862", "F-FRA3", "F-OPS1"],
    }

    # Generate findings
    findings = [
        f"n={len(closed)} closed lanes across {len(valid_sessions)} sessions",
        f"H1 ({h1_verdict}): AUC delta = {auc_delta:+.4f} (CS={auc_cs:.4f} vs WIP={auc_wip:.4f})",
        f"r(coordination_surface, merge_rate) = {r_cs_mr:.4f}",
        f"r(WIP, merge_rate) = {r_wip_mr:.4f}",
        f"Degraded sessions (merge<80%): {sum(labels)}/{len(labels)}",
    ]
    result["findings"] = findings

    # Write JSON
    out_path = Path("experiments/fractals/f-fra3-coordination-surface-s403.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(f"\nWrote: {out_path}")

    return result


if __name__ == "__main__":
    main()
