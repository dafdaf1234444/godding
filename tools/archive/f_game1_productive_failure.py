#!/usr/bin/env python3
"""F-GAME1: Productive failure test — do early-death sessions with git changes predict bursts?

Hypothesis: Early-death sessions (L+P=0) that leave git changes (files modified/added)
predict higher L+P in subsequent sessions than zero-change early deaths.

This tests Kapur 2014 productive failure: partial recordings in failed sessions
contribute to future breakthroughs via consolidation (git).

Usage:
  python3 tools/f_game1_productive_failure.py [--window 5] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).parent.parent

SESSION_RE = re.compile(
    r"^(S\d+[a-z]*)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\+(\d+)L[^|]*\+(\d+)P",
    re.MULTILINE,
)
COMMIT_SESSION_RE = re.compile(r"\[S(\d+)\]")


def parse_sessions(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    for m in SESSION_RE.finditer(text):
        sid, dt, lessons, principles = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        num_match = re.match(r"S(\d+)", sid)
        num = int(num_match.group(1)) if num_match else 0
        rows.append({"id": sid, "session_num": num, "date": dt,
                      "lessons": lessons, "principles": principles, "lp": lessons + principles})
    # Deduplicate: keep max-lp per session number
    by_num: dict[int, dict] = {}
    for r in rows:
        n = r["session_num"]
        if n not in by_num or r["lp"] > by_num[n]["lp"]:
            by_num[n] = r
    return sorted(by_num.values(), key=lambda x: x["session_num"])


def get_git_changes_per_session() -> dict[int, dict]:
    """Extract per-session file change counts from git log."""
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--numstat", "--format=%H %s"],
            capture_output=True, text=True, timeout=30, cwd=ROOT,
        )
        if result.returncode != 0:
            return {}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {}

    session_changes: dict[int, dict] = {}
    current_session = None

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Commit header line (hash + subject)
        if len(line) > 40 and line[0:40].replace(" ", "").isalnum():
            m = COMMIT_SESSION_RE.search(line)
            current_session = int(m.group(1)) if m else None
            if current_session is not None and current_session not in session_changes:
                session_changes[current_session] = {"files": 0, "insertions": 0, "deletions": 0, "commits": 0}
            if current_session is not None:
                session_changes[current_session]["commits"] += 1
            continue
        # Numstat line: additions\tdeletions\tfilename
        if current_session is not None and "\t" in line:
            parts = line.split("\t")
            if len(parts) >= 3:
                try:
                    adds = int(parts[0]) if parts[0] != "-" else 0
                    dels = int(parts[1]) if parts[1] != "-" else 0
                    session_changes[current_session]["files"] += 1
                    session_changes[current_session]["insertions"] += adds
                    session_changes[current_session]["deletions"] += dels
                except ValueError:
                    pass

    return session_changes


def compute_auc(labels: list[int], scores: list[float]) -> float:
    """Simple AUC via Mann-Whitney U statistic."""
    positives = [s for l, s in zip(labels, scores) if l == 1]
    negatives = [s for l, s in zip(labels, scores) if l == 0]
    if not positives or not negatives:
        return 0.5
    u = sum(1 for p in positives for n in negatives if p > n) + \
        0.5 * sum(1 for p in positives for n in negatives if p == n)
    return u / (len(positives) * len(negatives))


def run_experiment(sessions: list[dict], git_changes: dict[int, dict], window: int) -> dict:
    # Build lookup
    session_by_num = {s["session_num"]: s for s in sessions}
    session_nums = sorted(session_by_num.keys())
    num_to_idx = {n: i for i, n in enumerate(session_nums)}

    # Classify early deaths
    early_deaths = [s for s in sessions if s["lp"] == 0]
    productive = [s for s in sessions if s["lp"] > 0]

    # Split early deaths by git activity
    partial_deaths = []  # have git changes
    empty_deaths = []    # no git changes

    for s in early_deaths:
        gc = git_changes.get(s["session_num"], {"files": 0, "commits": 0})
        s_copy = {**s, "git_files": gc["files"], "git_commits": gc["commits"],
                  "git_insertions": gc.get("insertions", 0), "git_deletions": gc.get("deletions", 0)}
        if gc["files"] > 0:
            partial_deaths.append(s_copy)
        else:
            empty_deaths.append(s_copy)

    # For each early death, compute mean L+P in next <window> sessions
    def future_lp(snum: int) -> float | None:
        idx = num_to_idx.get(snum)
        if idx is None:
            return None
        future = []
        for i in range(idx + 1, min(idx + 1 + window, len(session_nums))):
            future.append(session_by_num[session_nums[i]]["lp"])
        return mean(future) if future else None

    partial_future = [future_lp(s["session_num"]) for s in partial_deaths]
    partial_future = [f for f in partial_future if f is not None]

    empty_future = [future_lp(s["session_num"]) for s in empty_deaths]
    empty_future = [f for f in empty_future if f is not None]

    # Also check if next session specifically is a burst (lp >= 3)
    def next_is_burst(snum: int) -> bool | None:
        idx = num_to_idx.get(snum)
        if idx is None or idx + 1 >= len(session_nums):
            return None
        return session_by_num[session_nums[idx + 1]]["lp"] >= 3

    partial_burst = [next_is_burst(s["session_num"]) for s in partial_deaths]
    partial_burst = [b for b in partial_burst if b is not None]

    empty_burst = [next_is_burst(s["session_num"]) for s in empty_deaths]
    empty_burst = [b for b in empty_burst if b is not None]

    # Burst rate comparison
    partial_burst_rate = sum(partial_burst) / len(partial_burst) if partial_burst else 0
    empty_burst_rate = sum(empty_burst) / len(empty_burst) if empty_burst else 0

    # AUC: can git_files predict whether the next-window mean L+P is above median?
    all_early_future = []
    all_early_git_files = []
    for s in early_deaths:
        gc = git_changes.get(s["session_num"], {"files": 0})
        fl = future_lp(s["session_num"])
        if fl is not None:
            all_early_future.append(fl)
            all_early_git_files.append(gc["files"])

    if all_early_future:
        med = sorted(all_early_future)[len(all_early_future) // 2]
        labels = [1 if f > med else 0 for f in all_early_future]
        auc = compute_auc(labels, all_early_git_files)
    else:
        auc = 0.5
        med = 0

    # Cohen's d between partial and empty future L+P
    if len(partial_future) >= 2 and len(empty_future) >= 2:
        pooled_std = ((stdev(partial_future)**2 * (len(partial_future) - 1) +
                       stdev(empty_future)**2 * (len(empty_future) - 1)) /
                      (len(partial_future) + len(empty_future) - 2)) ** 0.5
        cohens_d = (mean(partial_future) - mean(empty_future)) / pooled_std if pooled_std > 0 else 0
    else:
        cohens_d = 0

    # Git activity distribution among early deaths
    git_files_dist = [git_changes.get(s["session_num"], {"files": 0})["files"] for s in early_deaths]

    return {
        "total_sessions": len(sessions),
        "early_deaths": len(early_deaths),
        "early_death_rate": round(len(early_deaths) / len(sessions), 4) if sessions else 0,
        "partial_deaths": len(partial_deaths),
        "empty_deaths": len(empty_deaths),
        "productive_failure_rate": round(len(partial_deaths) / len(early_deaths), 4) if early_deaths else 0,
        "window_size": window,
        "partial_future_mean_lp": round(mean(partial_future), 3) if partial_future else None,
        "empty_future_mean_lp": round(mean(empty_future), 3) if empty_future else None,
        "lp_difference": round(mean(partial_future) - mean(empty_future), 3) if partial_future and empty_future else None,
        "cohens_d": round(cohens_d, 3),
        "partial_next_burst_rate": round(partial_burst_rate, 4),
        "empty_next_burst_rate": round(empty_burst_rate, 4),
        "burst_rate_ratio": round(partial_burst_rate / empty_burst_rate, 3) if empty_burst_rate > 0 else float("inf"),
        "auc_git_files_predicts_future_lp": round(auc, 3),
        "git_activity_among_early_deaths": {
            "mean_files": round(mean(git_files_dist), 1) if git_files_dist else 0,
            "max_files": max(git_files_dist) if git_files_dist else 0,
            "pct_with_changes": round(100 * sum(1 for f in git_files_dist if f > 0) / len(git_files_dist), 1) if git_files_dist else 0,
        },
        "sample_sizes": {
            "partial_with_future": len(partial_future),
            "empty_with_future": len(empty_future),
            "partial_with_burst": len(partial_burst),
            "empty_with_burst": len(empty_burst),
        },
        "hypothesis_tests": {
            "H1_partial_higher_lp": (mean(partial_future) > mean(empty_future)) if partial_future and empty_future else None,
            "H2_auc_above_0.60": auc > 0.60 if all_early_future else None,
            "H3_burst_ratio_above_1.5": (partial_burst_rate / empty_burst_rate > 1.5) if empty_burst_rate > 0 else None,
            "H4_productive_failure_rate_above_30pct": (len(partial_deaths) / len(early_deaths) > 0.30) if early_deaths else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="F-GAME1: productive failure test")
    parser.add_argument("--window", type=int, default=5, help="Number of future sessions to average (default 5)")
    parser.add_argument("--out", default="experiments/gaming/f-game1-productive-failure-s379.json")
    args = parser.parse_args()

    sessions = parse_sessions(ROOT / "memory" / "SESSION-LOG.md")
    git_changes = get_git_changes_per_session()
    result = run_experiment(sessions, git_changes, args.window)

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "experiment": "F-GAME1",
        "title": "Productive failure: do early-death sessions with git changes predict bursts?",
        "session": "S379",
        "date": date.today().isoformat(),
        **result,
    }
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    print(f"\n=== F-GAME1 Productive Failure Test ===")
    print(f"Sessions: {result['total_sessions']}")
    print(f"Early deaths: {result['early_deaths']} ({100*result['early_death_rate']:.1f}%)")
    print(f"  Partial (git changes>0): {result['partial_deaths']}")
    print(f"  Empty (git changes=0):   {result['empty_deaths']}")
    print(f"  Productive failure rate:  {100*result['productive_failure_rate']:.1f}%")
    print(f"\n--- Future L+P (next {args.window} sessions) ---")
    print(f"  After partial death: {result['partial_future_mean_lp']}")
    print(f"  After empty death:   {result['empty_future_mean_lp']}")
    print(f"  Difference:          {result['lp_difference']}")
    print(f"  Cohen's d:           {result['cohens_d']}")
    print(f"\n--- Next-session burst rate (L+P>=3) ---")
    print(f"  After partial death: {100*result['partial_next_burst_rate']:.1f}%")
    print(f"  After empty death:   {100*result['empty_next_burst_rate']:.1f}%")
    print(f"  Burst ratio:         {result['burst_rate_ratio']}x")
    print(f"\n--- Predictive power ---")
    print(f"  AUC (git files → future L+P): {result['auc_git_files_predicts_future_lp']}")
    print(f"\n--- Hypothesis results ---")
    for k, v in result["hypothesis_tests"].items():
        status = "PASS" if v else ("FAIL" if v is False else "N/A")
        print(f"  {k}: {status}")


if __name__ == "__main__":
    main()
