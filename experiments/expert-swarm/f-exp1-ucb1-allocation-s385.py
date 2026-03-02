#!/usr/bin/env python3
"""F-EXP1 experiment: UCB1 vs heuristic allocation quality.

Hypothesis: UCB1-era (S374+) top-3 domains produce >=1.2 L/lane;
UCB1 Gini < heuristic Gini (more even coverage).
"""
import json, re, os, math
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
LANES_FILE = ROOT / "tasks" / "SWARM-LANES.md"
ARCHIVE_FILE = ROOT / "tasks" / "SWARM-LANES-ARCHIVE.md"
LESSONS_DIR = ROOT / "memory" / "lessons"

# From dispatch_optimizer.py
LANE_ABBREV_TO_DOMAIN = {
    "AI": "ai", "BRN": "brain", "CAT": "catastrophic-risks",
    "COMP": "competitions", "CRYPTO": "cryptocurrency", "CTL": "control-theory",
    "DS": "distributed-systems", "ECO": "economy", "EVAL": "evaluation",
    "EVO": "evolution", "EXP": "expert-swarm", "FAR": "farming",
    "FIN": "finance", "FLD": "fluid-dynamics", "FRAC": "fractals",
    "GAME": "gaming", "GOV": "governance", "GT": "graph-theory",
    "HLT": "health", "IC": "information-cascade", "IS": "information-science",
    "ISO": "isomorphisms", "LNG": "linguistics", "META": "meta",
    "NK": "nk-complexity", "OPS": "operations-research", "PE": "protocol-engineering",
    "QC": "quality", "SCALE": "scaling", "SEC": "security",
    "SP": "stochastic-processes", "STR": "strategy",
    "SEC2": "security", "SP2": "stochastic-processes",
    "META2": "meta", "META3": "meta", "META4": "meta",
    "CAT2": "catastrophic-risks", "EXP2": "expert-swarm",
    "STR2": "strategy",
}

UCB1_START = 374  # S374 introduced UCB1 mode


def parse_session(text):
    """Extract session number from lane row."""
    m = re.search(r'S(\d+)', text)
    return int(m.group(1)) if m else None


def parse_domain_from_lane(lane_id):
    """Extract domain from DOMEX-<ABBREV>-S<N> pattern."""
    m = re.match(r'DOMEX-([A-Z0-9]+)-S\d+', lane_id)
    if not m:
        return None
    abbrev = m.group(1)
    return LANE_ABBREV_TO_DOMAIN.get(abbrev, abbrev.lower())


def count_lessons_in_notes(notes):
    """Count L-NNN mentions in notes."""
    return len(set(re.findall(r'\bL-(\d+)\b', notes)))


def parse_lanes(filepath):
    """Parse DOMEX lanes from a SWARM-LANES file."""
    lanes = []
    if not filepath.exists():
        return lanes
    text = filepath.read_text(encoding="utf-8")
    for line in text.split("\n"):
        if "|" not in line or "DOMEX-" not in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue
        # cols: ['', date, lane, session, agent, branch, pr, model, platform, scope-key, etc, status, notes, '']
        lane_id = cols[2]
        session_str = cols[3]
        status = cols[11] if len(cols) > 11 else ""
        notes = cols[12] if len(cols) > 12 else ""
        etc = cols[10] if len(cols) > 10 else ""

        domain = parse_domain_from_lane(lane_id)
        if not domain:
            continue

        session = parse_session(session_str)
        if session is None:
            session = parse_session(lane_id)

        # Only count MERGED or ABANDONED (closed lanes)
        if "MERGED" not in status and "ABANDONED" not in status:
            continue

        merged = "MERGED" in status
        lesson_count = count_lessons_in_notes(notes + " " + etc)

        lanes.append({
            "lane_id": lane_id,
            "domain": domain,
            "session": session,
            "merged": merged,
            "lessons": lesson_count,
            "era": "ucb1" if session and session >= UCB1_START else "heuristic",
        })
    return lanes


def count_domain_lessons():
    """Count lessons per domain from lesson files."""
    domain_counts = defaultdict(int)
    if not LESSONS_DIR.exists():
        return domain_counts
    for f in LESSONS_DIR.glob("L-*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'Domain:\s*(\S+)', text)
        if m:
            domain_counts[m.group(1).lower()] += 1
    return domain_counts


def gini(values):
    """Compute Gini coefficient."""
    if not values or sum(values) == 0:
        return 0.0
    vals = sorted(values)
    n = len(vals)
    total = sum(vals)
    cum = 0
    weighted_sum = 0
    for i, v in enumerate(vals):
        cum += v
        weighted_sum += (2 * (i + 1) - n - 1) * v
    return weighted_sum / (n * total)


def main():
    # Parse all lanes
    all_lanes = parse_lanes(ARCHIVE_FILE) + parse_lanes(LANES_FILE)

    # Deduplicate by lane_id (keep last occurrence = most recent status)
    seen = {}
    for lane in all_lanes:
        seen[lane["lane_id"]] = lane
    all_lanes = list(seen.values())

    # Split by era
    heuristic = [l for l in all_lanes if l["era"] == "heuristic"]
    ucb1 = [l for l in all_lanes if l["era"] == "ucb1"]

    def analyze_era(lanes, era_name):
        domain_stats = defaultdict(lambda: {"lanes": 0, "merged": 0, "lessons": 0})
        for l in lanes:
            d = domain_stats[l["domain"]]
            d["lanes"] += 1
            if l["merged"]:
                d["merged"] += 1
            d["lessons"] += l["lessons"]

        # Per-domain L/lane
        domain_yield = {}
        for dom, s in domain_stats.items():
            domain_yield[dom] = {
                "lanes": s["lanes"],
                "merged": s["merged"],
                "lessons": s["lessons"],
                "l_per_lane": s["lessons"] / s["lanes"] if s["lanes"] > 0 else 0,
                "merge_rate": s["merged"] / s["lanes"] if s["lanes"] > 0 else 0,
            }

        # Sort by L/lane
        sorted_domains = sorted(domain_yield.items(), key=lambda x: -x[1]["l_per_lane"])

        # Coverage Gini
        visit_counts = [s["lanes"] for s in domain_stats.values()]
        g = gini(visit_counts)

        # Top-3 / bottom-5
        top3 = sorted_domains[:3] if len(sorted_domains) >= 3 else sorted_domains
        bottom5 = sorted_domains[-5:] if len(sorted_domains) >= 5 else sorted_domains

        top3_yield = sum(d[1]["l_per_lane"] for d in top3) / len(top3) if top3 else 0
        bottom5_yield = sum(d[1]["l_per_lane"] for d in bottom5) / len(bottom5) if bottom5 else 0

        return {
            "era": era_name,
            "total_lanes": len(lanes),
            "merged": sum(1 for l in lanes if l["merged"]),
            "domains_touched": len(domain_stats),
            "total_lessons": sum(l["lessons"] for l in lanes),
            "avg_l_per_lane": sum(l["lessons"] for l in lanes) / len(lanes) if lanes else 0,
            "merge_rate": sum(1 for l in lanes if l["merged"]) / len(lanes) if lanes else 0,
            "gini": round(g, 4),
            "top3_domains": [(d[0], round(d[1]["l_per_lane"], 2)) for d in top3],
            "top3_avg_yield": round(top3_yield, 2),
            "bottom5_domains": [(d[0], round(d[1]["l_per_lane"], 2)) for d in bottom5],
            "bottom5_avg_yield": round(bottom5_yield, 2),
            "domain_detail": {k: v for k, v in sorted_domains},
        }

    h_result = analyze_era(heuristic, "heuristic (<=S373)")
    u_result = analyze_era(ucb1, "ucb1 (S374+)")

    # Verdict
    ucb1_top3_yield = u_result["top3_avg_yield"]
    heuristic_gini = h_result["gini"]
    ucb1_gini = u_result["gini"]

    h1_pass = ucb1_top3_yield >= 1.2
    h2_pass = ucb1_gini < heuristic_gini

    if h1_pass and h2_pass:
        verdict = "CONFIRMED"
    elif h1_pass or h2_pass:
        verdict = "PARTIALLY_CONFIRMED"
    else:
        verdict = "FALSIFIED"

    artifact = {
        "experiment": "f-exp1-ucb1-allocation-quality",
        "frontier": "F-EXP1",
        "domain": "expert-swarm",
        "session": "S385",
        "date": "2026-03-01",
        "hypothesis": "UCB1-era (S374+) top-3 domains produce >=1.2 L/lane; UCB1 Gini < heuristic Gini",
        "method": "Parse all DOMEX lanes from SWARM-LANES + archive. Split by era (heuristic <=S373, UCB1 S374+). Calculate per-domain L/lane yield, merge rate, coverage Gini.",
        "ucb1_start_session": UCB1_START,
        "heuristic_era": h_result,
        "ucb1_era": u_result,
        "comparison": {
            "avg_l_per_lane_delta": round(u_result["avg_l_per_lane"] - h_result["avg_l_per_lane"], 3),
            "merge_rate_delta_pp": round((u_result["merge_rate"] - h_result["merge_rate"]) * 100, 1),
            "gini_delta": round(u_result["gini"] - h_result["gini"], 4),
            "domains_touched_delta": u_result["domains_touched"] - h_result["domains_touched"],
            "h1_ucb1_top3_yield_gte_1.2": h1_pass,
            "h2_ucb1_gini_lt_heuristic": h2_pass,
        },
        "verdict": verdict,
        "key_findings": [],
        "unexpected": "",
        "prescriptions": [],
        "cites": ["L-697", "L-654", "L-444", "L-685", "L-572"],
        "confidence": f"Measured (n={len(all_lanes)} DOMEX lanes, {h_result['total_lanes']} heuristic + {u_result['total_lanes']} UCB1)",
    }

    # Print summary
    print(f"\n=== F-EXP1: UCB1 vs Heuristic Allocation Quality ===")
    print(f"\nHeuristic era (<=S373): {h_result['total_lanes']} lanes, {h_result['domains_touched']} domains, {h_result['total_lessons']}L")
    print(f"  avg L/lane: {h_result['avg_l_per_lane']:.2f}, merge rate: {h_result['merge_rate']:.1%}, Gini: {h_result['gini']}")
    print(f"  Top-3: {h_result['top3_domains']}")
    print(f"  Bottom-5: {h_result['bottom5_domains']}")
    print(f"\nUCB1 era (S374+): {u_result['total_lanes']} lanes, {u_result['domains_touched']} domains, {u_result['total_lessons']}L")
    print(f"  avg L/lane: {u_result['avg_l_per_lane']:.2f}, merge rate: {u_result['merge_rate']:.1%}, Gini: {u_result['gini']}")
    print(f"  Top-3: {u_result['top3_domains']}")
    print(f"  Bottom-5: {u_result['bottom5_domains']}")
    print(f"\nComparison:")
    print(f"  L/lane delta: {artifact['comparison']['avg_l_per_lane_delta']:+.3f}")
    print(f"  Merge rate delta: {artifact['comparison']['merge_rate_delta_pp']:+.1f}pp")
    print(f"  Gini delta: {artifact['comparison']['gini_delta']:+.4f} ({'more even' if artifact['comparison']['gini_delta'] < 0 else 'less even'})")
    print(f"  H1 (top-3 >=1.2): {h1_pass} (actual: {ucb1_top3_yield})")
    print(f"  H2 (Gini lower): {h2_pass} ({ucb1_gini} vs {heuristic_gini})")
    print(f"\nVerdict: {verdict}")

    # Save artifact
    out = ROOT / "experiments" / "expert-swarm" / "f-exp1-ucb1-allocation-s385.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(artifact, f, indent=2, default=str)
    print(f"\nArtifact: {out.relative_to(ROOT)}")

    return artifact


if __name__ == "__main__":
    main()
