#!/usr/bin/env python3
"""
reward_theory.py — Map, measure, and audit the swarm's implicit reward channels.

L-1127 identified 6 reward channels with 5/6 Goodharted. This tool makes the
reward structure visible so it can be improved.

Usage:
    python3 tools/reward_theory.py              # full audit
    python3 tools/reward_theory.py --summary    # one-line alignment score
    python3 tools/reward_theory.py --channel N  # deep-dive channel N (1-6)

Part of F-SWARMER1 colony: swarmer-swarm anti-attractor intervention #1.
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _count_lessons():
    """Count total lessons."""
    lesson_dir = ROOT / "memory" / "lessons"
    if not lesson_dir.exists():
        return 0
    return len([f for f in lesson_dir.iterdir() if f.name.startswith("L-") and f.suffix == ".md"])


def _count_principles():
    """Count principles from PRINCIPLES.md header."""
    pfile = ROOT / "memory" / "PRINCIPLES.md"
    if not pfile.exists():
        return 0
    text = pfile.read_text(errors="replace")
    # Count P-NNN patterns in active section (before any "Removed:" section)
    removed_idx = text.find("Removed:")
    active = text[:removed_idx] if removed_idx > 0 else text
    return len(re.findall(r'\bP-\d+\b', active))


def _measure_channel_1_compaction():
    """Channel 1: Context window selection pressure — favors compactness."""
    # Measure: ratio of compacted vs total lessons
    lesson_dir = ROOT / "memory" / "lessons"
    if not lesson_dir.exists():
        return {"aligned": False, "metric": "unknown", "detail": "no lessons"}

    total = 0
    under_20 = 0
    for f in lesson_dir.iterdir():
        if f.name.startswith("L-") and f.suffix == ".md":
            total += 1
            lines = f.read_text(errors="replace").strip().split("\n")
            if len(lines) <= 20:
                under_20 += 1

    compact_rate = under_20 / total if total > 0 else 0
    # Goodhart: compactness is rewarded regardless of content quality
    # Aligned if: compact AND high Sharpe (quality preserved during compression)
    return {
        "aligned": False,  # structural Goodhart — compactness proxy for value
        "metric": f"{compact_rate:.1%} lessons ≤20 lines",
        "detail": f"{under_20}/{total} compact. Goodhart: shorter != better. Fix: reward Sharpe*compactness, not compactness alone.",
        "goodhart_type": "proxy_for_value"
    }


def _measure_channel_2_citations():
    """Channel 2: Citation in-degree — rewards being mentioned, not mechanism quality."""
    lesson_dir = ROOT / "memory" / "lessons"
    if not lesson_dir.exists():
        return {"aligned": False, "metric": "unknown"}

    cite_counts = {}
    total = 0
    for f in sorted(lesson_dir.iterdir()):
        if not (f.name.startswith("L-") and f.suffix == ".md"):
            continue
        total += 1
        text = f.read_text(errors="replace")
        # Count L-NNN references
        refs = re.findall(r'\bL-(\d+)\b', text)
        for ref in refs:
            lid = f"L-{ref}"
            if lid != f.stem:  # exclude self-references
                cite_counts[lid] = cite_counts.get(lid, 0) + 1

    cited = len([v for v in cite_counts.values() if v > 0])
    uncited = total - cited
    top_5 = sorted(cite_counts.items(), key=lambda x: -x[1])[:5]

    return {
        "aligned": False,  # being mentioned != being valuable
        "metric": f"{cited}/{total} cited ({cited/total:.0%}), {uncited} orphans",
        "detail": f"Top 5: {', '.join(f'{k}={v}' for k,v in top_5)}. Goodhart: citation rewards presence, not mechanism invocation (L-1057).",
        "goodhart_type": "presence_not_mechanism"
    }


def _measure_channel_3_dispatch():
    """Channel 3: UCB1 dispatch — rewards high merge-rate, not value produced."""
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    if not lanes_path.exists():
        return {"aligned": False, "metric": "unknown"}

    text = lanes_path.read_text(errors="replace")
    merged = len(re.findall(r'\bMERGED\b', text))
    abandoned = len(re.findall(r'\bABANDONED\b', text))
    total = merged + abandoned
    merge_rate = merged / total if total > 0 else 0

    # Dynamic alignment check: is dispatch_scoring.py Sharpe-weighted? (L-1127 fix)
    scoring_path = ROOT / "tools" / "dispatch_scoring.py"
    sharpe_weighted = False
    if scoring_path.exists():
        scoring_text = scoring_path.read_text(errors="replace")
        sharpe_weighted = "sharpe_factor" in scoring_text and "sharpe_sum" in scoring_text

    if sharpe_weighted:
        return {
            "aligned": True,
            "metric": f"{merge_rate:.0%} merge rate ({merged}/{total})",
            "detail": f"ALIGNED (S463). UCB1 exploit term now Sharpe-weighted: quality = merge_rate × log(lessons) × (avg_sharpe/7.7). High-Sharpe domains score higher regardless of merge rate.",
            "goodhart_type": None
        }

    return {
        "aligned": False,
        "metric": f"{merge_rate:.0%} merge rate ({merged}/{total})",
        "detail": f"Goodhart: easy/safe lanes merge more. Value-producing but risky lanes get ABANDONED. Fix: weight by Sharpe of produced lessons, not merge/abandon binary.",
        "goodhart_type": "mergeability_not_value"
    }


def _measure_channel_4_sharpe():
    """Channel 4: Sharpe ratio — rewards recency, not depth."""
    lesson_dir = ROOT / "memory" / "lessons"
    if not lesson_dir.exists():
        return {"aligned": False, "metric": "unknown"}

    sharpe_vals = []
    for f in sorted(lesson_dir.iterdir()):
        if not (f.name.startswith("L-") and f.suffix == ".md"):
            continue
        text = f.read_text(errors="replace")
        m = re.search(r'Sharpe:\s*(\d+)', text)
        if m:
            sharpe_vals.append(int(m.group(1)))

    if not sharpe_vals:
        return {"aligned": False, "metric": "no Sharpe data"}

    avg = sum(sharpe_vals) / len(sharpe_vals)
    recent_50 = sharpe_vals[-50:] if len(sharpe_vals) >= 50 else sharpe_vals
    recent_avg = sum(recent_50) / len(recent_50)

    return {
        "aligned": False,  # Sharpe formula uses recency as a component
        "metric": f"avg {avg:.1f}, recent-50 avg {recent_avg:.1f}",
        "detail": f"n={len(sharpe_vals)} lessons with Sharpe. Goodhart: recency inflates score. Fix: separate depth score from freshness score.",
        "goodhart_type": "recency_not_depth"
    }


def _measure_channel_5_falsification():
    """Channel 5: Falsification premium — the ONLY correctly-aligned channel."""
    lesson_dir = ROOT / "memory" / "lessons"
    if not lesson_dir.exists():
        return {"aligned": True, "metric": "unknown"}

    falsified_count = 0
    total = 0
    for f in sorted(lesson_dir.iterdir()):
        if not (f.name.startswith("L-") and f.suffix == ".md"):
            continue
        total += 1
        text = f.read_text(errors="replace").lower()
        if "falsif" in text:
            falsified_count += 1

    rate = falsified_count / total if total > 0 else 0

    return {
        "aligned": True,  # 2.4x citation premium for productive wrongness is correctly aligned
        "metric": f"{rate:.1%} lessons mention falsification ({falsified_count}/{total})",
        "detail": "ALIGNED. Productive wrongness gets 2.4x citation (L-698). Incentive correct: being wrong and learning > being right and stagnant.",
        "goodhart_type": None
    }


def _measure_channel_6_survival():
    """Channel 6: Compactification survival — used tools persist, unused die."""
    tools_dir = ROOT / "tools"
    if not tools_dir.exists():
        return {"aligned": False, "metric": "unknown"}

    py_tools = [f for f in tools_dir.iterdir() if f.suffix == ".py"]
    total = len(py_tools)

    return {
        "aligned": False,  # survival is proxy for use, not merit
        "metric": f"{total} tools in tools/",
        "detail": "Goodhart: survival rewards being referenced in orient/maintenance, not producing value. Zombie tools persist because nothing actively removes them. Fix: tool sunset protocol (unused >30 sessions → archive).",
        "goodhart_type": "survival_not_merit"
    }


CHANNELS = [
    ("Context selection pressure", _measure_channel_1_compaction),
    ("Citation in-degree", _measure_channel_2_citations),
    ("UCB1 dispatch allocation", _measure_channel_3_dispatch),
    ("Sharpe ratio", _measure_channel_4_sharpe),
    ("Falsification premium", _measure_channel_5_falsification),
    ("Compactification survival", _measure_channel_6_survival),
]


def audit_all():
    """Run full reward channel audit."""
    results = []
    aligned = 0
    for name, fn in CHANNELS:
        r = fn()
        r["name"] = name
        results.append(r)
        if r.get("aligned"):
            aligned += 1
    return results, aligned, len(CHANNELS)


def print_audit(results, aligned, total):
    """Print formatted audit."""
    print(f"=== REWARD THEORY AUDIT (L-1127, F-SWARMER1) ===")
    print(f"Alignment: {aligned}/{total} = {aligned/total:.0%}\n")

    for i, r in enumerate(results, 1):
        status = "ALIGNED" if r.get("aligned") else "GOODHARTED"
        icon = "✓" if r.get("aligned") else "✗"
        print(f"  {icon} Channel {i}: {r['name']} [{status}]")
        print(f"    Metric: {r.get('metric', 'unknown')}")
        if r.get("detail"):
            print(f"    {r['detail']}")
        if r.get("goodhart_type"):
            print(f"    Goodhart type: {r['goodhart_type']}")
        print()

    print(f"--- Prescription ---")
    print(f"  Target: {aligned}/{total} → {aligned+1}/{total} (next channel to fix)")
    goodharted = [r for r in results if not r.get("aligned")]
    if goodharted:
        easiest = goodharted[0]  # Channel 1 is easiest to fix
        print(f"  Lowest-effort fix: {easiest['name']}")
        print(f"  Mechanism: replace proxy metric with composite (proxy × quality)")
    print()


def print_summary():
    """Print one-line alignment score."""
    _, aligned, total = audit_all()
    print(f"Reward alignment: {aligned}/{total} = {aligned/total:.0%} (target: ≥33%, L-1127)")


def main():
    args = sys.argv[1:]
    if "--summary" in args:
        print_summary()
    elif "--channel" in args:
        idx = args.index("--channel")
        if idx + 1 < len(args):
            ch = int(args[idx + 1]) - 1
            if 0 <= ch < len(CHANNELS):
                name, fn = CHANNELS[ch]
                r = fn()
                r["name"] = name
                print_audit([r], 1 if r.get("aligned") else 0, 1)
            else:
                print(f"Channel must be 1-{len(CHANNELS)}")
        else:
            print("Usage: --channel N")
    else:
        results, aligned, total = audit_all()
        print_audit(results, aligned, total)


if __name__ == "__main__":
    main()
