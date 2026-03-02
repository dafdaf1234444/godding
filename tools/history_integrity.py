#!/usr/bin/env python3
"""
history_integrity.py — Measure swarm history integrity across 4 dimensions.
L-981: history integrity is a first-class property (SIG-49, human directive 2026-03-02).

Usage:
  python3 tools/history_integrity.py          # full report
  python3 tools/history_integrity.py --json   # JSON output for experiments
"""

import argparse
import json
import re
import subprocess
from pathlib import Path


# Commits that bulk-added files due to catastrophic events, not normal creation.
# Attribution tools should use declared Session field for files added in these commits.
MASS_RESTORE_COMMITS = {
    "2a743a8f",  # [S427] fix: restore 3033 files deleted by catastrophic mass-commit 497a94ef
}


def _get_session(path: str) -> tuple[str | None, bool]:
    """Return (committing_session, is_mass_restore) for a file's creation commit."""
    result = subprocess.run(
        ["git", "log", "--oneline", "--diff-filter=A", "--follow", "--", path],
        capture_output=True, text=True, timeout=10
    )
    if not result.stdout.strip():
        return None, False
    commit_line = result.stdout.strip().split('\n')[0]
    commit_hash = commit_line.split()[0]
    if commit_hash in MASS_RESTORE_COMMITS:
        return None, True
    m = re.search(r'\[S(\d+)\]', commit_line)
    return (f"S{m.group(1)}" if m else None), False


def check_commit_format(n: int = 100) -> dict:
    """Dimension 1: commit message format compliance."""
    log = subprocess.run(
        ["git", "log", "--oneline", f"-{n}"], capture_output=True, text=True
    ).stdout
    lines = [l for l in log.strip().split('\n') if l]
    compliant = sum(1 for l in lines if re.search(r'\[S\d+\]', l))
    non_compliant = [l for l in lines if not re.search(r'\[S\d+\]', l)]
    return {
        "total": len(lines),
        "compliant": compliant,
        "rate": compliant / len(lines) if lines else 0,
        "non_compliant_examples": non_compliant[:3],
    }


def check_lesson_attribution(sample_size: int = 50) -> dict:
    """Dimension 2: lesson declared Session vs. git creation commit."""
    lessons_dir = Path("memory/lessons")
    files = sorted([f for f in lessons_dir.glob("L-*.md") if f.name != "TEMPLATE.md"])
    sample = files[-sample_size:]

    matches = mismatches = no_declared = mass_restore_count = errors = 0
    mismatch_examples = []

    for lf in sample:
        content = lf.read_text()
        declared = re.search(r'Session:\s*S(\d+)', content)
        if not declared:
            no_declared += 1
            continue

        commit_sess, is_restore = _get_session(str(lf))
        if is_restore:
            mass_restore_count += 1
            continue
        if commit_sess is None:
            errors += 1
            continue

        ds = int(declared.group(1))
        cs = int(commit_sess[1:])
        if abs(ds - cs) <= 2:
            matches += 1
        else:
            mismatches += 1
            mismatch_examples.append({
                "lesson": lf.name,
                "declared": f"S{ds}",
                "committed": f"S{cs}",
                "diff": abs(ds - cs),
            })

    scoreable = matches + mismatches
    return {
        "sample": len(sample),
        "mass_restore_excluded": mass_restore_count,
        "matches": matches,
        "mismatches": mismatches,
        "no_declared": no_declared,
        "errors": errors,
        "rate": matches / scoreable if scoreable else None,
        "mismatch_examples": sorted(mismatch_examples, key=lambda x: -x["diff"])[:5],
    }


def check_experiment_outcomes(min_session: int = 400) -> dict:
    """Dimension 3: experiment JSON outcome completeness."""
    exp_dir = Path("experiments")
    total = recent_total = recent_with_actual = recent_with_expected = 0
    old_with_actual = old_total = 0
    missing_examples = []

    for j in exp_dir.rglob("f-*.json"):
        try:
            content = j.read_text()
            sm = re.search(r's(\d{3,})', str(j).lower())
            if not sm:
                sm = re.search(r'"session":\s*"S(\d+)"', content)
            if not sm:
                continue
            sess = int(sm.group(1))
            total += 1

            if sess >= min_session:
                recent_total += 1
                if '"actual"' in content or '"outcome"' in content:
                    recent_with_actual += 1
                else:
                    if len(missing_examples) < 8:
                        missing_examples.append({"session": sess, "file": j.name})
                if '"expected"' in content or '"pre_registration"' in content:
                    recent_with_expected += 1
            else:
                old_total += 1
                if '"actual"' in content or '"outcome"' in content:
                    old_with_actual += 1
        except Exception:
            pass

    return {
        "total_experiment_jsons": total,
        "recent_threshold": f"S{min_session}+",
        "recent_total": recent_total,
        "recent_with_actual": recent_with_actual,
        "recent_with_expected": recent_with_expected,
        "recent_outcome_rate": recent_with_actual / recent_total if recent_total else 0,
        "older_with_actual": old_with_actual,
        "older_total": old_total,
        "older_outcome_rate": old_with_actual / old_total if old_total else 0,
        "missing_examples": sorted(missing_examples, key=lambda x: -x["session"])[:5],
    }


def check_lane_history() -> dict:
    """Dimension 4: SWARM-LANES per-lane history preservation."""
    lanes_path = Path("tasks/SWARM-LANES.md")
    archive_path = Path("tasks/SWARM-LANES-ARCHIVE.md")

    active_text = lanes_path.read_text() if lanes_path.exists() else ""
    archive_text = archive_path.read_text() if archive_path.exists() else ""

    active_ids = re.findall(r'\| (DOMEX-[^\|]+)\|', active_text)
    archive_ids = re.findall(r'\| (DOMEX-[^\|]+)\|', archive_text)

    from collections import Counter
    active_counts = Counter(active_ids)
    multi_row = sum(1 for v in active_counts.values() if v > 1)

    return {
        "active_lanes": len(active_ids),
        "archived_lanes": len(archive_ids),
        "total_historical": len(active_ids) + len(archive_ids),
        "multi_row_lanes": multi_row,
        "history_preserved": multi_row > 0,
        "design_note": "merge-on-close (L-527) deliberately erases per-lane history to prevent bloat",
    }


def run_all(args) -> dict:
    results = {}
    print("=== HISTORY INTEGRITY REPORT ===\n")

    print("[1] Commit message format")
    r1 = check_commit_format()
    results["commit_format"] = r1
    print(f"    Last {r1['total']} commits: {r1['compliant']} compliant ({r1['rate']*100:.0f}%)")
    if r1["non_compliant_examples"]:
        for ex in r1["non_compliant_examples"]:
            print(f"    ⚠ {ex[:70]}")
    print()

    print("[2] Lesson attribution (declared Session vs. git creation commit)")
    r2 = check_lesson_attribution()
    results["lesson_attribution"] = r2
    print(f"    Sample: {r2['sample']} lessons | mass-restore excluded: {r2['mass_restore_excluded']}")
    rate = r2["rate"]
    rate_str = f"{rate*100:.0f}%" if rate is not None else "N/A (all mass-restore)"
    print(f"    Attribution rate: {rate_str} ({r2['matches']} matches, {r2['mismatches']} mismatches)")
    if r2["mismatch_examples"]:
        for ex in r2["mismatch_examples"][:3]:
            print(f"    ⚠ {ex['lesson']}: declared {ex['declared']}, committed {ex['committed']} (diff={ex['diff']})")
    print()

    print("[3] Experiment outcome completeness")
    r3 = check_experiment_outcomes()
    results["experiment_outcomes"] = r3
    print(f"    Total JSONs: {r3['total_experiment_jsons']}")
    print(f"    {r3['recent_threshold']}: {r3['recent_with_actual']}/{r3['recent_total']} have outcome = {r3['recent_outcome_rate']*100:.0f}%")
    print(f"    Older: {r3['older_with_actual']}/{r3['older_total']} = {r3['older_outcome_rate']*100:.0f}%")
    if r3["missing_examples"]:
        print(f"    Recent missing (top {len(r3['missing_examples'])}):")
        for ex in r3["missing_examples"]:
            print(f"      S{ex['session']} {ex['file']}")
    print()

    print("[4] SWARM-LANES lane history")
    r4 = check_lane_history()
    results["lane_history"] = r4
    print(f"    Active lanes: {r4['active_lanes']} | Archived: {r4['archived_lanes']}")
    print(f"    Per-lane history preserved: {'YES' if r4['history_preserved'] else 'NO (merge-on-close, L-527)'}")
    print()

    # Summary
    outcome_rate = r3["recent_outcome_rate"]
    commit_rate = r1["rate"]
    attr_rate = r2["rate"]
    print("--- SUMMARY ---")
    print(f"  Commit format:       {'✓' if commit_rate == 1.0 else '⚠'} {commit_rate*100:.0f}%")
    if attr_rate is not None:
        print(f"  Lesson attribution:  {'✓' if attr_rate > 0.95 else '⚠'} {attr_rate*100:.0f}% (excl. mass-restore)")
    else:
        print(f"  Lesson attribution:  — (all mass-restore, use declared Session field)")
    print(f"  Experiment outcomes: {'⚠' if outcome_rate < 0.80 else '✓'} {outcome_rate*100:.0f}% (target 80%)")
    print(f"  Lane history:        — intentional (L-527 merge-on-close)")

    return results


def main():
    parser = argparse.ArgumentParser(description="Swarm history integrity checker")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--sample", type=int, default=50, help="Lesson sample size")
    parser.add_argument("--min-session", type=int, default=400, help="Min session for experiment check")
    args = parser.parse_args()

    results = run_all(args)

    if args.json:
        print("\n" + json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
