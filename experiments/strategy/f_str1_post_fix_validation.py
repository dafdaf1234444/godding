#!/usr/bin/env python3
"""F-STR1 prospective validation: post-S384 close_lane.py fix.

Compares pre-fix (S380-S383) vs post-fix (S384+) DOMEX lanes on:
  1. EAD compliance (actual+diff filled)
  2. Merge rate
  3. Lessons per lane (L/lane)
  4. Value_density scoring effect

Context: S382 validation showed EAD regression -32.7pp. S384 diagnosed
two close_lane.py bugs (archive search gap + substitution silent failure).
This script tests whether the fix restored compliance.

Usage: python3 experiments/strategy/f_str1_post_fix_validation.py
"""

import json
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANES_FILE = os.path.join(REPO_ROOT, "tasks", "SWARM-LANES.md")
ARCHIVE_FILE = os.path.join(REPO_ROOT, "tasks", "SWARM-LANES-ARCHIVE.md")
OUTPUT_FILE = os.path.join(
    REPO_ROOT, "experiments", "strategy",
    "f-str1-post-fix-validation-s387.json"
)

# Eras for comparison
FIX_SESSION = 384  # close_lane.py bugs fixed in S384
REGRESSION_START = 380  # value_density integration session
UCB1_START = 370  # approximate UCB1 era start


def extract_session_number(lane_id, session_col):
    m = re.search(r'S(\d+)', lane_id)
    if m:
        return int(m.group(1))
    m = re.search(r'S?(\d+)', session_col.strip())
    if m:
        return int(m.group(1))
    return None


def count_lessons(text):
    return len(set(re.findall(r'\bL-(\d+)\b', text)))


def check_ead(etc_col, note_col):
    combined = etc_col + " " + note_col
    fields = {}
    for field in ["expect", "actual", "diff"]:
        m = re.search(rf'{field}=([^;|]+)', combined)
        if m:
            val = m.group(1).strip().upper()
            fields[field] = val not in ("TBD", "", "N/A")
        else:
            fields[field] = False
    has_actual = fields.get("actual", False)
    has_diff = fields.get("diff", False)
    return {
        "expect": fields.get("expect", False),
        "actual": has_actual,
        "diff": has_diff,
        "compliant": has_actual and has_diff,
    }


def is_resolved(note_col, etc_col):
    return "RESOLVED" in (note_col + " " + etc_col).upper()


def parse_lane_row(line):
    parts = [p.strip() for p in line.split("|")]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    if len(parts) < 12:
        return None

    lane_id = parts[1].strip()
    if "DOMEX" not in lane_id:
        return None

    session_col = parts[2].strip()
    etc_col = parts[9].strip()
    status = parts[10].strip().upper()
    note = parts[11].strip() if len(parts) > 11 else ""

    session_num = extract_session_number(lane_id, session_col)
    if session_num is None:
        return None

    # Only closed lanes
    if status not in ("MERGED", "ABANDONED"):
        return None

    lessons = count_lessons(etc_col + " " + note)
    ead = check_ead(etc_col, note)
    resolved = is_resolved(note, etc_col)

    return {
        "lane_id": lane_id,
        "session": session_num,
        "status": status,
        "lessons": lessons,
        "ead": ead,
        "resolved": resolved,
    }


def load_lanes(filepath):
    lanes = []
    if not os.path.exists(filepath):
        return lanes
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            if "---" in line and line.count("|") > 3:
                continue
            if "Lane" in line and "Session" in line:
                continue
            row = parse_lane_row(line)
            if row:
                lanes.append(row)
    return lanes


def deduplicate_lanes(lanes):
    seen = {}
    for lane in lanes:
        seen[lane["lane_id"]] = lane
    return list(seen.values())


def era_stats(lanes, label):
    n = len(lanes)
    if n == 0:
        return {"label": label, "n": 0}

    merged = [l for l in lanes if l["status"] == "MERGED"]
    ead_compliant = [l for l in lanes if l["ead"]["compliant"]]
    has_actual = [l for l in lanes if l["ead"]["actual"]]
    has_diff = [l for l in lanes if l["ead"]["diff"]]
    total_lessons = sum(l["lessons"] for l in merged)
    resolved = [l for l in lanes if l["resolved"]]

    return {
        "label": label,
        "n": n,
        "merged": len(merged),
        "abandoned": n - len(merged),
        "merge_rate": round(len(merged) / n, 3),
        "ead_compliant": len(ead_compliant),
        "ead_rate": round(len(ead_compliant) / n, 3),
        "has_actual_rate": round(len(has_actual) / n, 3),
        "has_diff_rate": round(len(has_diff) / n, 3),
        "total_lessons": total_lessons,
        "lessons_per_merged_lane": round(total_lessons / len(merged), 2) if merged else 0,
        "resolved_count": len(resolved),
        "session_range": f"S{min(l['session'] for l in lanes)}-S{max(l['session'] for l in lanes)}",
    }


def main():
    lanes_active = load_lanes(LANES_FILE)
    lanes_archive = load_lanes(ARCHIVE_FILE)
    all_lanes = deduplicate_lanes(lanes_archive + lanes_active)

    print("=" * 70)
    print("F-STR1 Post-Fix Prospective Validation (S387)")
    print("=" * 70)
    print(f"\nTotal closed DOMEX lanes: {len(all_lanes)}")

    # Split into eras
    pre_ucb1 = [l for l in all_lanes if l["session"] < UCB1_START]
    regression_era = [l for l in all_lanes if REGRESSION_START <= l["session"] <= FIX_SESSION - 1]
    post_fix = [l for l in all_lanes if l["session"] >= FIX_SESSION]
    ucb1_pre_fix = [l for l in all_lanes if UCB1_START <= l["session"] < FIX_SESSION]

    # Stats
    eras = {
        "pre_ucb1": era_stats(pre_ucb1, f"Pre-UCB1 (<S{UCB1_START})"),
        "ucb1_pre_fix": era_stats(ucb1_pre_fix, f"UCB1 pre-fix (S{UCB1_START}-S{FIX_SESSION-1})"),
        "regression_window": era_stats(regression_era, f"Regression window (S{REGRESSION_START}-S{FIX_SESSION-1})"),
        "post_fix": era_stats(post_fix, f"Post-fix (S{FIX_SESSION}+)"),
    }

    # Print comparison table
    print("\n--- ERA COMPARISON ---")
    print(f"{'Era':<35s} {'N':>4s} {'Merge%':>7s} {'EAD%':>7s} {'L/lane':>7s} {'Resolved':>9s}")
    print("-" * 70)
    for key, era in eras.items():
        if era["n"] == 0:
            continue
        print(f"{era['label']:<35s} {era['n']:>4d} "
              f"{era['merge_rate']:>6.1%} "
              f"{era['ead_rate']:>6.1%} "
              f"{era['lessons_per_merged_lane']:>7.2f} "
              f"{era['resolved_count']:>9d}")

    # Key comparison: regression window vs post-fix
    reg = eras["regression_window"]
    post = eras["post_fix"]

    print("\n--- KEY COMPARISON: Regression Window vs Post-Fix ---")
    if reg["n"] > 0 and post["n"] > 0:
        ead_delta = post["ead_rate"] - reg["ead_rate"]
        merge_delta = post["merge_rate"] - reg["merge_rate"]
        lpl_delta = post["lessons_per_merged_lane"] - reg["lessons_per_merged_lane"]

        print(f"  EAD compliance: {reg['ead_rate']:.1%} → {post['ead_rate']:.1%} (Δ{ead_delta:+.1%})")
        print(f"  Merge rate:     {reg['merge_rate']:.1%} → {post['merge_rate']:.1%} (Δ{merge_delta:+.1%})")
        print(f"  L/lane:         {reg['lessons_per_merged_lane']:.2f} → {post['lessons_per_merged_lane']:.2f} (Δ{lpl_delta:+.2f})")

        # Hypothesis test: EAD recovery
        ead_recovered = post["ead_rate"] >= 0.90
        print(f"\n  H1: Post-fix EAD ≥ 90%? {'CONFIRMED' if ead_recovered else 'NOT YET'} ({post['ead_rate']:.1%})")

        # Hypothesis test: regression was transient
        regression_transient = ead_delta > 0
        print(f"  H2: EAD improved post-fix? {'CONFIRMED' if regression_transient else 'REJECTED'} (Δ{ead_delta:+.1%})")
    else:
        print("  Insufficient data in one or both eras.")

    # Per-session detail for post-fix
    print("\n--- POST-FIX LANE DETAIL ---")
    post_fix_sorted = sorted(post_fix, key=lambda l: l["session"])
    for l in post_fix_sorted:
        ead_mark = "Y" if l["ead"]["compliant"] else "N"
        res_mark = "RES" if l["resolved"] else ""
        print(f"  S{l['session']} {l['lane_id']:<30s} {l['status']:<10s} "
              f"EAD={ead_mark} L={l['lessons']} {res_mark}")

    # UCB1 era overall (context)
    ucb1_all = [l for l in all_lanes if l["session"] >= UCB1_START]
    ucb1_stats = era_stats(ucb1_all, f"UCB1 overall (S{UCB1_START}+)")

    print(f"\n--- UCB1 ERA OVERALL ---")
    print(f"  N={ucb1_stats['n']}, merge={ucb1_stats['merge_rate']:.1%}, "
          f"EAD={ucb1_stats['ead_rate']:.1%}, L/lane={ucb1_stats['lessons_per_merged_lane']:.2f}")

    # Session-by-session EAD rolling average (post-fix)
    if post_fix_sorted:
        sessions = sorted(set(l["session"] for l in post_fix_sorted))
        print(f"\n--- POST-FIX SESSION BREAKDOWN ---")
        for s in sessions:
            s_lanes = [l for l in post_fix_sorted if l["session"] == s]
            s_ead = sum(1 for l in s_lanes if l["ead"]["compliant"])
            s_merged = sum(1 for l in s_lanes if l["status"] == "MERGED")
            s_lessons = sum(l["lessons"] for l in s_lanes if l["status"] == "MERGED")
            print(f"  S{s}: {len(s_lanes)} lanes, "
                  f"EAD={s_ead}/{len(s_lanes)} ({s_ead/len(s_lanes):.0%}), "
                  f"merged={s_merged}, lessons={s_lessons}")

    # Build JSON output
    output = {
        "experiment": "F-STR1 Post-Fix Prospective Validation",
        "session": "S387",
        "frontier": "F-STR1",
        "hypothesis": (
            "Post-S384 close_lane.py fix restores EAD compliance to ≥90% "
            "and confirms value_density regression was transient initialization effect."
        ),
        "method": (
            "Parse all closed DOMEX lanes. Split into pre-UCB1, UCB1-pre-fix, "
            "regression window (S380-S383), and post-fix (S384+). Compare EAD "
            "compliance, merge rate, and L/lane across eras."
        ),
        "fix_session": FIX_SESSION,
        "eras": eras,
        "ucb1_overall": ucb1_stats,
        "post_fix_lanes": [
            {
                "lane_id": l["lane_id"],
                "session": l["session"],
                "status": l["status"],
                "lessons": l["lessons"],
                "ead_compliant": l["ead"]["compliant"],
                "resolved": l["resolved"],
            }
            for l in post_fix_sorted
        ],
        "conclusions": {},
    }

    # Fill conclusions
    if reg["n"] > 0 and post["n"] > 0:
        ead_delta = post["ead_rate"] - reg["ead_rate"]
        output["conclusions"] = {
            "ead_recovery": post["ead_rate"] >= 0.90,
            "ead_rate_post_fix": post["ead_rate"],
            "ead_delta_vs_regression": round(ead_delta, 3),
            "merge_rate_post_fix": post["merge_rate"],
            "lessons_per_lane_post_fix": post["lessons_per_merged_lane"],
            "regression_transient": ead_delta > 0,
            "sample_size_post_fix": post["n"],
        }

    # Write artifact
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nArtifact: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
