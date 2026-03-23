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

RESTORE_COMMIT_RE = re.compile(r"\brestore\b.*\bfiles?\b.*\b(dropped|deleted)\b", re.IGNORECASE)
SESSION_RE = re.compile(r"\[S(\d+)\]")
OUTCOME_KEYS = {
    "actual",
    "conclusion",
    "finding",
    "findings",
    "key_finding",
    "key_findings",
    "outcome",
    "result",
    "results",
    "verdict",
}
EXPECTED_KEYS = {
    "expect",
    "expectation",
    "expected",
    "hypothesis",
    "prediction",
    "pre_registration",
    "question",
    "falsification",
    "falsification_criterion",
    "falsification_criteria",
    "falsified_if",
}
DIFF_OUTCOME_KEYS = {
    "diff",
    "diff_from_expect",
    "diff_vs_expectation",
    "expect_vs_actual",
    "prediction_vs_actual",
}


def _declared_session(content: str) -> int | None:
    """Extract a declared lesson session from markdown content."""
    match = re.search(r"\*{0,2}Session\*{0,2}:\s*S(\d+)", content)
    return int(match.group(1)) if match else None


def _lesson_number(path: Path) -> int:
    """Extract numeric lesson id for stable recency ordering."""
    match = re.search(r"L-(\d+)", path.name)
    return int(match.group(1)) if match else -1


def _sample_lessons(files: list[Path], sample_size: int) -> list[tuple[Path, str, int | None]]:
    """Sample lessons by numeric lesson id, not lexicographic filename order."""
    annotated = []
    for lesson_file in files:
        content = lesson_file.read_text(encoding="utf-8", errors="replace")
        annotated.append((lesson_file, content, _declared_session(content)))
    annotated.sort(key=lambda item: (_lesson_number(item[0]), item[0].name))
    return annotated[-sample_size:]


def _collect_json_keys(obj) -> set[str]:
    """Collect lower-cased keys from nested JSON objects."""
    keys: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                keys.add(key.lower())
            keys.update(_collect_json_keys(value))
    elif isinstance(obj, list):
        for item in obj:
            keys.update(_collect_json_keys(item))
    return keys


def _has_expectation_schema(keys: set[str]) -> bool:
    return bool(
        EXPECTED_KEYS & keys
        or any(key.endswith("_prediction") for key in keys)
        or any(key.startswith("falsification") for key in keys)
    )


def _has_outcome_schema(keys: set[str]) -> bool:
    if OUTCOME_KEYS & keys:
        return True
    if any(key.endswith("_verdict") for key in keys):
        return True
    return _has_expectation_schema(keys) and bool(DIFF_OUTCOME_KEYS & keys)


def _get_session(path: str) -> tuple[str | None, bool]:
    """Return (committing_session, is_mass_restore) for a file's creation commit."""
    result = subprocess.run(
        ["git", "log", "--format=%H\t%s", "--diff-filter=A", "--follow", "--", path],
        capture_output=True, text=True, timeout=10
    )
    if not result.stdout.strip():
        return None, False

    saw_restore = False
    commit_lines = [line for line in result.stdout.strip().split('\n') if line.strip()]
    for commit_line in reversed(commit_lines):
        if not commit_line.strip():
            continue
        if "\t" in commit_line:
            commit_hash, subject = commit_line.split("\t", 1)
        else:
            parts = commit_line.split(maxsplit=1)
            commit_hash = parts[0]
            subject = parts[1] if len(parts) > 1 else ""
        if commit_hash in MASS_RESTORE_COMMITS or RESTORE_COMMIT_RE.search(subject):
            saw_restore = True
            continue
        m = SESSION_RE.search(subject)
        return (f"S{m.group(1)}" if m else None), False

    return None, saw_restore


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
    sample = _sample_lessons(files, sample_size)

    matches = mismatches = no_declared = mass_restore_count = errors = 0
    mismatch_examples = []

    for lf, content, declared_session in sample:
        if declared_session is None:
            no_declared += 1
            continue

        commit_sess, is_restore = _get_session(str(lf))
        if is_restore:
            mass_restore_count += 1
            continue
        if commit_sess is None:
            errors += 1
            continue

        ds = declared_session
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
    total = recent_total = recent_with_outcome = recent_with_expected = 0
    old_with_outcome = old_total = 0
    missing_examples = []

    for j in exp_dir.rglob("f-*.json"):
        try:
            data = json.loads(j.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(data, dict):
                continue
            sm = re.search(r's(\d{3,})', str(j).lower())
            if not sm:
                sm = re.search(r"S(\d+)", str(data.get("session", "")))
            if not sm:
                continue
            sess = int(sm.group(1))
            total += 1
            keys = _collect_json_keys(data)

            if sess >= min_session:
                recent_total += 1
                if _has_outcome_schema(keys):
                    recent_with_outcome += 1
                else:
                    if len(missing_examples) < 8:
                        missing_examples.append({
                            "session": sess,
                            "file": j.name,
                            "keys": sorted(list(keys))[:10],
                        })
                if _has_expectation_schema(keys):
                    recent_with_expected += 1
            else:
                old_total += 1
                if _has_outcome_schema(keys):
                    old_with_outcome += 1
        except Exception:
            pass

    return {
        "total_experiment_jsons": total,
        "recent_threshold": f"S{min_session}+",
        "recent_total": recent_total,
        "recent_with_actual": recent_with_outcome,
        "recent_with_outcome": recent_with_outcome,
        "recent_with_expected": recent_with_expected,
        "recent_outcome_rate": recent_with_outcome / recent_total if recent_total else 0,
        "older_with_actual": old_with_outcome,
        "older_with_outcome": old_with_outcome,
        "older_total": old_total,
        "older_outcome_rate": old_with_outcome / old_total if old_total else 0,
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
    r2 = check_lesson_attribution(sample_size=args.sample)
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
    r3 = check_experiment_outcomes(min_session=args.min_session)
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
