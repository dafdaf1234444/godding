#!/usr/bin/env python3
"""
citation_mechanism.py — Measure citation-vs-mechanism invocation for Ch2 Goodhart.

Tests whether lesson citation counts (in-degree) reflect actual mechanism use.
Ch2 Goodhart hypothesis: citations reward presence, not mechanism invocation.

Usage:
    python3 tools/citation_mechanism.py              # full report
    python3 tools/citation_mechanism.py --top N      # top-N cited lessons (default 20)
    python3 tools/citation_mechanism.py --json       # JSON output
    python3 tools/citation_mechanism.py --correlation # correlation analysis only

Part of F-SWARMER1 colony: Ch2 citation Goodhart fix (DOMEX-EXPSW-S477).
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Invocation markers: lesson's mechanism is actively applied
INVOKE_PATTERNS = [
    r'(?:per|following|applying|enforce|enforcing|use|using)\s+L-{lid}\b',
    r'L-{lid}\s+(?:requires|says we|says to|demands|enforces|prescribes|mandates)',
    r'L-{lid}[\s:]+structural\s+enforcement',
    r'L-{lid}\s+(?:pattern|mechanism|rule|protocol)\s+applied',
    r'(?:apply|implement|wire|enforce)\s+(?:.*?\s)?L-{lid}\b',
    r'L-{lid}\s+(?:theorem|rule|principle)\b',
]

# Mention markers: lesson referenced for context only
MENTION_PATTERNS = [
    r'L-{lid}\s+(?:found|measured|observed|noted|showed|reported|identified)',
    r'(?:see|related|cf\.?|compare)\s+L-{lid}\b',
    r'^Cites:.*\bL-{lid}\b',  # Cites header (automatic, low signal)
    r'L-{lid}\s+(?:is|was|has been)\s+(?:a|the|an)',
]

# Tool/code invocation: lesson referenced in executable code
TOOL_INVOKE_PATTERN = r'#\s*L-{lid}\b|L-{lid}'


def _get_in_degrees():
    """Compute in-degree for all lessons from citation cache or direct scan."""
    cache_path = ROOT / "experiments" / "compact-citation-cache.json"
    cite_counts = {}

    if cache_path.exists():
        with open(cache_path) as f:
            cache = json.load(f)
        for path_key, entry in cache.items():
            cites = entry.get("cites", {})
            for lid, count in cites.items():
                if lid.startswith("L-"):
                    cite_counts[lid] = cite_counts.get(lid, 0) + count
    else:
        # Fallback: scan lessons directly
        lesson_dir = ROOT / "memory" / "lessons"
        for lf in sorted(lesson_dir.iterdir()):
            if not (lf.name.startswith("L-") and lf.suffix == ".md"):
                continue
            text = lf.read_text(errors="replace")
            for ref in re.findall(r'\bL-(\d+)\b', text):
                lid = f"L-{ref}"
                if lid != lf.stem:
                    cite_counts[lid] = cite_counts.get(lid, 0) + 1

    return cite_counts


def _classify_citation_context(text, lid_num):
    """Classify each citation of L-{lid_num} in text as INVOKE or MENTION."""
    lid = str(lid_num)
    invokes = 0
    mentions = 0

    for pattern_template in INVOKE_PATTERNS:
        pattern = pattern_template.replace("{lid}", lid)
        invokes += len(re.findall(pattern, text, re.IGNORECASE | re.MULTILINE))

    for pattern_template in MENTION_PATTERNS:
        pattern = pattern_template.replace("{lid}", lid)
        mentions += len(re.findall(pattern, text, re.IGNORECASE | re.MULTILINE))

    # Count bare references (no context markers) as mentions
    total_refs = len(re.findall(rf'\bL-{lid}\b', text))
    classified = invokes + mentions
    bare = max(0, total_refs - classified)
    mentions += bare

    return invokes, mentions


def _scan_tool_invocations(lid_num):
    """Count how many tools reference this lesson (implementation evidence)."""
    lid = str(lid_num)
    tool_dir = ROOT / "tools"
    tool_refs = 0

    if not tool_dir.exists():
        return 0

    for tf in tool_dir.iterdir():
        if not tf.suffix == ".py":
            continue
        try:
            text = tf.read_text(errors="replace")
        except Exception:
            continue
        if re.search(rf'\bL-{lid}\b', text):
            tool_refs += 1

    return tool_refs


def _scan_lane_invocations(lid_num):
    """Count lanes that cite this lesson and their merge outcomes."""
    lid = str(lid_num)
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    if not lanes_path.exists():
        return 0, 0, 0

    text = lanes_path.read_text(errors="replace")
    citing_lanes = 0
    merged_citing = 0
    abandoned_citing = 0

    for line in text.split("\n"):
        if rf"L-{lid}" not in line and f"L-{lid}" not in line:
            continue
        if not line.startswith("|"):
            continue
        citing_lanes += 1
        if "MERGED" in line:
            merged_citing += 1
        elif "ABANDONED" in line:
            abandoned_citing += 1

    return citing_lanes, merged_citing, abandoned_citing


def analyze_citation_mechanism(top_n=20):
    """Full analysis: citation count vs mechanism invocation for top-cited lessons."""
    in_degrees = _get_in_degrees()
    if not in_degrees:
        return {"error": "No citation data found"}

    # Get top-N cited lessons
    sorted_lessons = sorted(in_degrees.items(), key=lambda x: -x[1])[:top_n]

    lesson_dir = ROOT / "memory" / "lessons"
    results = []

    # Scan all files for invocation contexts of top-cited lessons
    all_files = []
    for scan_dir in [lesson_dir, ROOT / "tools", ROOT / "tasks", ROOT / "beliefs"]:
        if scan_dir.exists():
            for f in scan_dir.rglob("*"):
                if f.suffix in (".md", ".py", ".json") and f.stat().st_size < 500000:
                    all_files.append(f)

    for lid, in_degree in sorted_lessons:
        lid_num = lid.replace("L-", "")
        total_invokes = 0
        total_mentions = 0

        for f in all_files:
            try:
                text = f.read_text(errors="replace")
            except Exception:
                continue
            if f"L-{lid_num}" not in text:
                continue
            inv, men = _classify_citation_context(text, lid_num)
            total_invokes += inv
            total_mentions += men

        tool_refs = _scan_tool_invocations(lid_num)
        lane_total, lane_merged, lane_abandoned = _scan_lane_invocations(lid_num)

        # Mechanism score: invocations + tool refs + merged lanes
        mechanism_score = total_invokes + tool_refs + lane_merged
        total_refs = total_invokes + total_mentions
        invoke_ratio = total_invokes / total_refs if total_refs > 0 else 0

        results.append({
            "lesson": lid,
            "in_degree": in_degree,
            "invoke_count": total_invokes,
            "mention_count": total_mentions,
            "invoke_ratio": round(invoke_ratio, 3),
            "tool_refs": tool_refs,
            "lane_citations": lane_total,
            "lane_merged": lane_merged,
            "mechanism_score": mechanism_score,
        })

    # Aggregate conversion rate: what % of all citations are invocations?
    total_invokes_all = sum(r["invoke_count"] for r in results)
    total_mentions_all = sum(r["mention_count"] for r in results)
    total_refs_all = total_invokes_all + total_mentions_all
    aggregate_invoke_rate = total_invokes_all / total_refs_all if total_refs_all > 0 else 0

    # Correlation between in_degree and invoke_ratio (not mechanism_score!)
    # This tests: does being highly cited predict higher mechanism use?
    r_ratio = None
    if len(results) >= 3:
        in_deg = [r["in_degree"] for r in results]
        ratios = [r["invoke_ratio"] for r in results]
        n = len(results)
        mean_id = sum(in_deg) / n
        mean_r = sum(ratios) / n
        cov = sum((a - mean_id) * (b - mean_r) for a, b in zip(in_deg, ratios)) / n
        std_id = (sum((a - mean_id)**2 for a in in_deg) / n) ** 0.5
        std_r = (sum((b - mean_r)**2 for b in ratios) / n) ** 0.5
        r_ratio = cov / (std_id * std_r) if std_id > 0 and std_r > 0 else 0

    # Count high-citation-low-mechanism outliers
    low_mechanism = [r for r in results if r["invoke_ratio"] < 0.1]

    # Ch2 verdict based on:
    # 1. Aggregate invoke rate < 10% = most citations are noise
    # 2. Low-mechanism outliers > 30% = Goodhart confirmed
    # 3. r(in_degree, invoke_ratio) near 0 = citation count has no quality signal
    goodhart_confirmed = (
        aggregate_invoke_rate < 0.10
        and len(low_mechanism) / len(results) > 0.30 if results else False
    )

    if goodhart_confirmed:
        verdict = "MISALIGNED"
    elif aggregate_invoke_rate < 0.20:
        verdict = "PARTIALLY_ALIGNED"
    else:
        verdict = "ALIGNED"

    return {
        "top_n": top_n,
        "results": results,
        "aggregate_invoke_rate": round(aggregate_invoke_rate, 4),
        "correlation_indeg_vs_ratio": round(r_ratio, 3) if r_ratio is not None else None,
        "goodhart_confirmed": goodhart_confirmed,
        "low_mechanism_count": len(low_mechanism),
        "low_mechanism_pct": round(len(low_mechanism) / len(results) * 100, 1) if results else 0,
        "total_invokes": total_invokes_all,
        "total_mentions": total_mentions_all,
        "ch2_verdict": verdict,
    }


def print_report(analysis):
    """Print human-readable report."""
    print(f"=== CITATION-MECHANISM ANALYSIS (top {analysis['top_n']}) ===\n")

    if "error" in analysis:
        print(f"ERROR: {analysis['error']}")
        return

    print(f"{'Lesson':<10} {'InDeg':>6} {'Invoke':>7} {'Mention':>8} {'Ratio':>6} {'Tools':>6} {'Lanes':>6} {'Mech':>5}")
    print("-" * 65)

    for r in analysis["results"]:
        ratio_str = f"{r['invoke_ratio']:.1%}"
        marker = " !" if r["invoke_ratio"] < 0.1 else ""
        print(f"{r['lesson']:<10} {r['in_degree']:>6} {r['invoke_count']:>7} {r['mention_count']:>8} {ratio_str:>6} {r['tool_refs']:>6} {r['lane_citations']:>6} {r['mechanism_score']:>5}{marker}")

    print()
    agg = analysis["aggregate_invoke_rate"]
    r_val = analysis["correlation_indeg_vs_ratio"]
    print(f"Aggregate invoke rate: {agg:.1%} ({analysis['total_invokes']} invocations / {analysis['total_invokes'] + analysis['total_mentions']} total refs)")
    if r_val is not None:
        print(f"Correlation (in_degree vs invoke_ratio): r={r_val:.3f}")
    print(f"Low-mechanism outliers (<10% invoke ratio): {analysis['low_mechanism_count']}/{analysis['top_n']} ({analysis['low_mechanism_pct']}%)")
    print(f"Ch2 verdict: {analysis['ch2_verdict']}")

    if analysis["goodhart_confirmed"]:
        print(f"\n** Ch2 Goodhart CONFIRMED: {agg:.1%} of citations involve mechanism use. **")
        print(f"   Citation count rewards presence, not mechanism invocation.")
    elif agg < 0.20:
        print(f"\nCh2 PARTIALLY ALIGNED: {agg:.1%} invoke rate is low but above noise floor.")
    else:
        print(f"\nCh2 ALIGNED: {agg:.1%} invoke rate suggests citations carry mechanism signal.")


def main():
    top_n = 20
    json_mode = "--json" in sys.argv
    corr_only = "--correlation" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--top" and i + 1 < len(sys.argv):
            top_n = int(sys.argv[i + 1])

    analysis = analyze_citation_mechanism(top_n)

    if json_mode:
        print(json.dumps(analysis, indent=2))
    elif corr_only:
        r = analysis.get("correlation_indeg_vs_ratio")
        verdict = analysis.get("ch2_verdict", "UNKNOWN")
        agg = analysis.get("aggregate_invoke_rate", 0)
        print(f"r={r}, agg_invoke={agg:.1%}, verdict={verdict}, outliers={analysis.get('low_mechanism_count', 0)}/{top_n}")
    else:
        print_report(analysis)


if __name__ == "__main__":
    main()
