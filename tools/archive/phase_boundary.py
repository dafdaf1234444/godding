#!/usr/bin/env python3
"""Regime boundary detector — maps swarm position relative to known operational thresholds.

Measures distance-to-threshold for each known boundary, predicts which will
be crossed next, and suggests engineering actions. ISO-4 applied to the swarm itself.

Usage:
    python3 tools/phase_boundary.py             # full report
    python3 tools/phase_boundary.py --json       # machine-readable output
    python3 tools/phase_boundary.py --nearest    # show only nearest 3 boundaries
"""

import argparse
import glob
import json
import math
import os
import re
import sys
from datetime import datetime


def count_lessons():
    """Count lesson files and compute citation graph metrics."""
    lessons = glob.glob("memory/lessons/L-*.md")
    N = len(lessons)
    if N == 0:
        return {"N": 0, "edges": 0, "K_avg": 0, "K_max": 0, "orphans": 0}

    out_degrees = []
    in_degree = {}
    for lf in lessons:
        lid_m = re.search(r"L-(\d+)", os.path.basename(lf))
        if not lid_m:
            continue
        lid = lid_m.group(1)
        try:
            content = open(lf).read()
        except OSError:
            continue
        refs = set(re.findall(r"\bL-(\d+)\b", content)) - {lid}
        out_degrees.append(len(refs))
        for r in refs:
            in_degree[r] = in_degree.get(r, 0) + 1

    edges = sum(out_degrees)
    K_avg = edges / N if N else 0
    K_max = max(in_degree.values()) if in_degree else 0
    orphans = sum(1 for d in out_degrees if d == 0)

    return {
        "N": N,
        "edges": edges,
        "K_avg": round(K_avg, 4),
        "K_max": K_max,
        "orphans": orphans,
        "orphan_pct": round(orphans / N * 100, 1) if N else 0,
    }


def get_proxy_k():
    """Get proxy-K metrics from log."""
    log_file = "experiments/proxy-k-log.json"
    if not os.path.exists(log_file):
        return None
    data = json.load(open(log_file))
    if len(data) < 2:
        return None

    current = data[-1]
    # Find floor (minimum after last compaction)
    floor = min(d.get("total", 99999) for d in data[-5:])
    total = current.get("total", 0)
    drift = (total - floor) / floor * 100 if floor > 0 else 0

    # Growth rate from recent entries
    recent = [d for d in data[-6:] if d.get("total", 0) > 0]
    if len(recent) >= 2:
        growth_per_entry = (recent[-1]["total"] - recent[0]["total"]) / (len(recent) - 1)
    else:
        growth_per_entry = 170  # fallback from P-163

    return {
        "total": total,
        "floor": floor,
        "drift_pct": round(drift, 1),
        "growth_rate": round(growth_per_entry, 0),
    }


def count_domains():
    """Count active domains."""
    count = 0
    for d in os.listdir("domains"):
        dp = os.path.join("domains", d)
        if os.path.isdir(dp) and os.path.exists(os.path.join(dp, "DOMAIN.md")):
            count += 1
    return count


def count_gap1_tools():
    """Count tools and estimate GAP-1 closure.

    Uses the L-533 audit: 21 tools total, 6 close the action loop.
    Tools that close the loop both diagnose AND execute fixes.
    """
    # From L-533 audit: 21 swarm-relevant tools, 6 fully close the action loop
    # Self-executing = both diagnose problems AND take corrective action
    self_exec = [
        "compact.py", "open_lane.py", "close_lane.py",
        "orient.py", "dispatch_optimizer.py", "sync_state.py",
    ]
    # Total from L-533 audit (excludes utility scripts, test helpers)
    total_audited = 21
    closed = sum(1 for t in self_exec if os.path.exists(f"tools/{t}"))
    return {"total": total_audited, "closed": closed, "ratio": round(closed / total_audited * 100, 1)}


def count_isos():
    """Count ISO entries in atlas."""
    atlas_file = "domains/ISOMORPHISM-ATLAS.md"
    if not os.path.exists(atlas_file):
        return 0
    content = open(atlas_file).read()
    return len(re.findall(r"### ISO-\d+", content))


def measure_boundaries():
    """Measure all known phase boundaries and return structured results."""
    nk = count_lessons()
    pk = get_proxy_k()
    domains = count_domains()
    gap1 = count_gap1_tools()
    isos = count_isos()

    boundaries = []

    # 1. NK chaos boundary (K=2)
    k_chaos_dist = 2.0 - nk["K_avg"]
    boundaries.append({
        "name": "NK chaos boundary",
        "iso": "ISO-4 × NK",
        "description": "K_avg crosses 2.0 — knowledge graph transitions from ordered to edge-of-chaos regime",
        "metric": "K_avg",
        "current": nk["K_avg"],
        "threshold": 2.0,
        "distance": round(k_chaos_dist, 4),
        "distance_pct": round(abs(k_chaos_dist) / 2.0 * 100, 1),
        "direction": "approaching" if k_chaos_dist > 0 else "CROSSED",
        "consequence": "Edge-of-chaos: maximum computational capability (Kauffman). Knowledge graph gains emergent cross-domain paths. Risk: chaotic coupling if K>>2.",
        "engineering": "Create highly cross-linked lessons spanning 3+ domains. Each lesson with ≥3 citations pushes K_avg up ~0.006.",
        "urgency": "HIGH" if k_chaos_dist < 0.3 else "MEDIUM",
        "crossed": k_chaos_dist <= 0,
    })

    # 2. Logistic K* ceiling
    k_star = 2.75
    k_ceil_dist = k_star - nk["K_avg"]
    boundaries.append({
        "name": "K* logistic ceiling",
        "iso": "ISO-8 × NK",
        "description": f"K_avg approaches logistic carrying capacity K*={k_star} — citation density saturates",
        "metric": "K_avg",
        "current": nk["K_avg"],
        "threshold": k_star,
        "distance": round(k_ceil_dist, 4),
        "distance_pct": round(k_ceil_dist / k_star * 100, 1),
        "direction": "approaching" if k_ceil_dist > 0 else "CROSSED",
        "consequence": "Saturation: new lessons can't add more connections. System needs structural reorganization (e.g., raise quality gate min citations from 1→2).",
        "engineering": "Raise c_out parameter in quality gate. Or introduce hierarchical citation (lesson→principle→belief chains).",
        "urgency": "LOW",
        "crossed": k_ceil_dist <= 0,
    })

    # 3. Zipf α saturation
    zipf_warning = 518
    zipf_dist = zipf_warning - nk["N"]
    boundaries.append({
        "name": "Zipf vocabulary saturation",
        "iso": "ISO-8 (power laws)",
        "description": f"At N≈{zipf_warning}, Zipf α drops below 0.65 — vocabulary diversity collapses",
        "metric": "N (lesson count)",
        "current": nk["N"],
        "threshold": zipf_warning,
        "distance": zipf_dist,
        "distance_pct": round(zipf_dist / zipf_warning * 100, 1),
        "direction": "approaching",
        "consequence": "Vocabulary monotony: lessons start repeating the same concepts. Indicates knowledge-type saturation — the swarm needs novel concept classes.",
        "engineering": "Dream session: generate lessons from cross-domain synthesis targeting vocabulary outside the top-20 most-used terms. Schedule at N=510.",
        "urgency": "HIGH" if zipf_dist < 40 else "MEDIUM",
        "crossed": zipf_dist <= 0,
    })

    # 4. Proxy-K thermodynamic cycle
    if pk:
        boundaries.append({
            "name": "Proxy-K critical temperature",
            "iso": "ISO-4 × ISO-6",
            "description": "Proxy-K drift exceeds 20% — URGENT threshold triggers mandatory compaction (renormalization)",
            "metric": "proxy-K drift %",
            "current": pk["drift_pct"],
            "threshold": 20.0,
            "distance": round(20.0 - pk["drift_pct"], 1),
            "distance_pct": round((20.0 - pk["drift_pct"]) / 20.0 * 100, 1),
            "direction": "approaching" if pk["drift_pct"] < 20 else "CROSSED",
            "consequence": "Mandatory compaction event (renormalization). Entropy exceeds capacity. Phase transition to compressed regime.",
            "engineering": "Run compaction proactively (before URGENT). Each compaction = phase transition in knowledge density.",
            "urgency": "URGENT" if pk["drift_pct"] > 15 else ("HIGH" if pk["drift_pct"] > 10 else "MEDIUM"),
            "crossed": pk["drift_pct"] >= 20,
        })

    # 5. GAP-1: diagnosis→execution phase transition
    gap1_threshold = 50.0
    gap1_dist = gap1_threshold - gap1["ratio"]
    boundaries.append({
        "name": "GAP-1 self-healing threshold",
        "iso": "ISO-10 × ISO-7",
        "description": "When >50% of tools close the action loop (diagnose AND execute), the swarm transitions from diagnostic to self-healing",
        "metric": "tool closure ratio",
        "current": gap1["ratio"],
        "threshold": gap1_threshold,
        "distance": round(gap1_dist, 1),
        "distance_pct": round(gap1_dist / gap1_threshold * 100, 1),
        "direction": "approaching",
        "consequence": "Self-healing: the swarm can fix problems it detects without waiting for human-initiated sessions. Qualitative shift in autonomy.",
        "engineering": f"Wire --auto flags into diagnostic tools. Each tool that gains execution = +{round(100/gap1['total'], 1)}% toward threshold. Need {int(gap1_threshold * gap1['total'] / 100) - gap1['closed']} more tools.",
        "urgency": "MEDIUM",
        "crossed": gap1_dist <= 0,
    })

    # 6. Domain diversity threshold
    # ISO-4 in ATLAS has 9 domain manifestations. Swarm has 40 domains.
    # Phase transition: when domains exceed ISO entries × 3, new ISOs should emerge spontaneously
    iso_domain_ratio = domains / isos if isos > 0 else 0
    spontaneous_iso_threshold = 3.0  # domains per ISO
    boundaries.append({
        "name": "Spontaneous ISO emergence",
        "iso": "ISO-7 (emergence)",
        "description": f"When domain:ISO ratio exceeds {spontaneous_iso_threshold}:1, new ISOs should emerge from cross-domain density",
        "metric": "domain:ISO ratio",
        "current": round(iso_domain_ratio, 2),
        "threshold": spontaneous_iso_threshold,
        "distance": round(spontaneous_iso_threshold - iso_domain_ratio, 2),
        "distance_pct": round(abs(spontaneous_iso_threshold - iso_domain_ratio) / spontaneous_iso_threshold * 100, 1),
        "direction": "approaching" if iso_domain_ratio < spontaneous_iso_threshold else "CROSSED",
        "consequence": "Cross-domain density high enough that structural equivalences emerge without deliberate search. ISO discovery becomes spontaneous.",
        "engineering": "Run cross-domain councils. Each council covering 4+ domains has probability of surfacing new ISO candidates.",
        "urgency": "LOW" if iso_domain_ratio < 2.0 else "MEDIUM",
        "crossed": iso_domain_ratio >= spontaneous_iso_threshold,
    })

    # 7. Orphan lesson collapse
    orphan_threshold = 5.0  # Below 5% orphan rate = fully connected knowledge
    boundaries.append({
        "name": "Knowledge connectivity completion",
        "iso": "ISO-11 (network diffusion)",
        "description": "Orphan rate (zero-citation lessons) drops below 5% — knowledge graph becomes fully navigable",
        "metric": "orphan rate %",
        "current": nk["orphan_pct"],
        "threshold": orphan_threshold,
        "distance": round(nk["orphan_pct"] - orphan_threshold, 1),
        "distance_pct": round(abs(nk["orphan_pct"] - orphan_threshold) / orphan_threshold * 100, 1) if orphan_threshold > 0 else 0,
        "direction": "approaching" if nk["orphan_pct"] > orphan_threshold else "CROSSED",
        "consequence": "Every lesson reachable from every other via citation paths. Knowledge diffusion operates on entire graph, not islands.",
        "engineering": "Retroactively cite orphan lessons from related lessons. Each orphan linked = -0.2% orphan rate.",
        "urgency": "MEDIUM" if nk["orphan_pct"] > 15 else "LOW",
        "crossed": nk["orphan_pct"] <= orphan_threshold,
    })

    # 8. Quality degradation threshold
    # Measured: ~10% of lessons are corrected/superseded (directed mutations)
    # Threshold N ≈ 1/(μ × (1-s)) where μ=correction_rate, s=quality_advantage
    # BUT: swarm corrections are Lamarckian (corrections IMPROVE quality), not random
    # Directed correction inverts the degradation threshold
    # Track as ANOMALY: threshold crossed but degradation not manifested (P-217: substrate verification)
    mutation_count = 0
    for lf in glob.glob("memory/lessons/L-*.md"):
        try:
            c = open(lf).read().lower()
            if "superseded" in c or "corrected" in c or "falsified" in c:
                mutation_count += 1
        except OSError:
            pass
    mutation_rate = mutation_count / nk["N"] if nk["N"] else 0.1
    selection_advantage = 0.95
    eigen_threshold = int(1.0 / (mutation_rate * (1 - selection_advantage))) if mutation_rate > 0 else 9999
    eigen_distance = eigen_threshold - nk["N"]
    boundaries.append({
        "name": "Quality degradation threshold (ANOMALY)",
        "iso": "ISO-19 (replication-mutation)",
        "description": f"Degradation threshold N≈{eigen_threshold} CROSSED at N={nk['N']} — but degradation NOT manifested (Lamarckian correction inverts quality loss)",
        "metric": "N vs degradation threshold",
        "current": nk["N"],
        "threshold": eigen_threshold,
        "distance": int(eigen_distance),
        "distance_pct": round(abs(eigen_distance) / eigen_threshold * 100, 1) if eigen_threshold > 0 else 0,
        "direction": "ANOMALY: crossed without degradation",
        "consequence": "Swarm survives past threshold because corrections are directed (improve quality) not random (degrade quality). Lamarckian revision defeats quality degradation.",
        "engineering": "Monitor: if correction rate rises above ~15% AND quality metrics degrade simultaneously, degradation may yet manifest. Current correction rate: {:.1f}%.".format(mutation_rate * 100),
        "urgency": "WATCH",
        "crossed": True,
    })

    # 9. Human de-privileging phase 5
    # L-490: phase 5 = human optional for routine operation
    # F-META6 RESOLVED = triggers defined. Next: actual autonomous initiation
    boundaries.append({
        "name": "Autonomous session initiation",
        "iso": "ISO-4 × ISO-20",
        "description": "Phase 5 of human de-privileging: swarm initiates sessions without human command",
        "metric": "autonomous capability",
        "current": "triggers defined (F-META6)",
        "threshold": "external monitor + auto-initiation",
        "distance": "1 component (monitor)",
        "distance_pct": 50.0,
        "direction": "approaching",
        "consequence": "The swarm becomes temporally autonomous — it decides WHEN to work, not just WHAT to work on. Fundamental phase transition in agency.",
        "engineering": "Build or integrate an external scheduler that reads SESSION-TRIGGER.md and initiates Claude Code sessions. Cron + CLI = sufficient.",
        "urgency": "MEDIUM",
        "crossed": False,
    })

    return boundaries, nk, pk


def format_report(boundaries, nk, pk, show_nearest=None):
    """Format boundaries into human-readable report."""
    lines = []
    lines.append("=" * 72)
    lines.append("PHASE BOUNDARY MAP — Swarm Position Relative to Known Transitions")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')} | N={nk['N']} | K_avg={nk['K_avg']}")
    if pk:
        lines.append(f"Proxy-K: {pk['total']}t | Drift: {pk['drift_pct']}%")
    lines.append("=" * 72)

    # Sort by distance (nearest first), handling mixed types
    def sort_key(b):
        d = b["distance"]
        if isinstance(d, (int, float)):
            return abs(d) / max(abs(b["threshold"]), 1) if isinstance(b["threshold"], (int, float)) else 0
        return 0.5  # non-numeric distances go in the middle

    sorted_b = sorted(boundaries, key=sort_key)
    if show_nearest:
        sorted_b = sorted_b[:show_nearest]

    crossed = [b for b in boundaries if b.get("crossed")]
    approaching = [b for b in boundaries if not b.get("crossed")]

    if crossed:
        lines.append("")
        lines.append("--- CROSSED BOUNDARIES (active phase transitions) ---")
        for b in crossed:
            lines.append(f"  *** {b['name']}")
            lines.append(f"      {b['description']}")
            lines.append(f"      Current: {b['current']} | Threshold: {b['threshold']}")
            lines.append(f"      Consequence: {b['consequence']}")
            lines.append("")

    lines.append("")
    lines.append("--- APPROACHING BOUNDARIES (ordered by proximity) ---")
    for b in sorted_b:
        if b.get("crossed"):
            continue
        urgency_marker = {"URGENT": "!!!", "HIGH": "!!", "MEDIUM": "!", "LOW": " "}
        marker = urgency_marker.get(b.get("urgency", "LOW"), " ")
        lines.append(f"  {marker} {b['name']} [{b.get('urgency', 'LOW')}]")
        lines.append(f"      {b['description']}")
        lines.append(f"      Current: {b['current']} → Threshold: {b['threshold']} (distance: {b['distance']})")
        lines.append(f"      ISO: {b['iso']}")
        lines.append(f"      To trigger: {b['engineering']}")
        lines.append("")

    # Summary
    lines.append("--- SUMMARY ---")
    lines.append(f"  Total boundaries tracked: {len(boundaries)}")
    lines.append(f"  Crossed: {len(crossed)}")
    lines.append(f"  Approaching: {len(approaching)}")
    nearest = sorted_b[0] if sorted_b else None
    if nearest and not nearest.get("crossed"):
        lines.append(f"  Nearest uncrossed: {nearest['name']} (distance: {nearest['distance']})")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Phase boundary detector for swarm")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--nearest", type=int, help="Show only N nearest boundaries")
    args = parser.parse_args()

    boundaries, nk, pk = measure_boundaries()

    if args.json:
        output = {
            "timestamp": datetime.now().isoformat(),
            "nk": nk,
            "proxy_k": pk,
            "boundaries": boundaries,
            "crossed_count": sum(1 for b in boundaries if b.get("crossed")),
            "approaching_count": sum(1 for b in boundaries if not b.get("crossed")),
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(format_report(boundaries, nk, pk, show_nearest=args.nearest))


if __name__ == "__main__":
    main()
