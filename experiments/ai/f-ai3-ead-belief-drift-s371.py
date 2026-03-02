#!/usr/bin/env python3
"""F-AI3 experiment: Does EAD tracking reduce belief drift?

Measures whether sessions with expect-act-diff (EAD) fields in their
DOMEX lanes produce different challenge/revision rates than non-EAD sessions.

Data sources:
- tasks/SWARM-LANES.md + SWARM-LANES-ARCHIVE.md: EAD presence per lane
- beliefs/CHALLENGES.md: challenge filing events
- git log -- beliefs/DEPS.md: belief revision events
- memory/SESSION-LOG.md: session metadata
"""

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def parse_lanes():
    """Parse all closed lanes, classify EAD presence per session."""
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    archive_path = ROOT / "tasks" / "SWARM-LANES-ARCHIVE.md"

    all_text = ""
    for p in [lanes_path, archive_path]:
        if p.exists():
            all_text += p.read_text() + "\n"

    session_ead = defaultdict(lambda: {"ead_lanes": 0, "non_ead_lanes": 0, "total_lanes": 0})

    for line in all_text.split("\n"):
        if not line.startswith("|"):
            continue
        if "MERGED" not in line and "ABANDONED" not in line:
            continue

        # Extract session
        sess_match = re.search(r"\bS(\d+)\b", line)
        if not sess_match:
            continue
        sess = int(sess_match.group(1))

        has_expect = "expect=" in line
        has_actual = "actual=" in line
        has_diff = "diff=" in line
        is_ead = has_expect and has_actual and has_diff

        session_ead[sess]["total_lanes"] += 1
        if is_ead:
            session_ead[sess]["ead_lanes"] += 1
        else:
            session_ead[sess]["non_ead_lanes"] += 1

    return dict(session_ead)


def parse_challenges():
    """Parse CHALLENGES.md for challenge filing sessions."""
    path = ROOT / "beliefs" / "CHALLENGES.md"
    challenges = []
    for line in path.read_text().split("\n"):
        if not line.startswith("|"):
            continue
        m = re.match(r"\|\s*S(\d+)\s*\|", line)
        if m:
            challenges.append(int(m.group(1)))
    return challenges


def parse_deps_revisions():
    """Parse git log for DEPS.md change sessions."""
    result = subprocess.run(
        ["git", "log", "--oneline", "--all", "--", "beliefs/DEPS.md"],
        capture_output=True, text=True, cwd=ROOT
    )
    sessions = []
    for line in result.stdout.strip().split("\n"):
        m = re.search(r"\[S(\d+)\]", line)
        if m:
            sessions.append(int(m.group(1)))
    return sessions


def parse_session_log():
    """Parse SESSION-LOG for session dates and summaries."""
    path = ROOT / "memory" / "SESSION-LOG.md"
    sessions = {}
    for line in path.read_text().split("\n"):
        m = re.match(r"S(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|([^|]*)\|(.+)", line)
        if m:
            sess = int(m.group(1))
            date = m.group(2)
            metrics = m.group(3).strip()
            summary = m.group(4).strip()
            sessions[sess] = {"date": date, "metrics": metrics, "summary": summary}
    return sessions


def compute_ead_ratio(lane_data):
    """Compute EAD ratio for a session's lanes."""
    total = lane_data["total_lanes"]
    if total == 0:
        return 0.0
    return lane_data["ead_lanes"] / total


def main():
    print("=== F-AI3: EAD Tracking and Belief Drift ===\n")

    lane_data = parse_lanes()
    challenges = parse_challenges()
    deps_revisions = parse_deps_revisions()
    session_log = parse_session_log()

    # Classify sessions into EAD eras
    # Pre-enforcement: S178-S310 (voluntary EAD)
    # Post-enforcement: S311+ (open_lane.py enforces EAD fields)
    # Pre-EAD: <S178

    all_sessions = sorted(set(lane_data.keys()) | set(session_log.keys()))
    min_s = min(all_sessions) if all_sessions else 0
    max_s = max(all_sessions) if all_sessions else 0

    print(f"Session range: S{min_s}-S{max_s} ({len(all_sessions)} sessions)")
    print(f"Challenges filed: {len(challenges)} (sessions: {sorted(set(challenges))})")
    print(f"DEPS.md revisions: {len(deps_revisions)} (sessions: {sorted(set(deps_revisions))})")
    print()

    # Challenge sessions as set
    challenge_sessions = set(challenges)
    deps_sessions = set(deps_revisions)

    # Era analysis
    eras = {
        "pre-EAD (S1-S177)": (1, 177),
        "voluntary-EAD (S178-S310)": (178, 310),
        "enforced-EAD (S311-S371)": (311, 371),
    }

    print("--- Era Analysis ---")
    for era_name, (lo, hi) in eras.items():
        era_sessions = [s for s in all_sessions if lo <= s <= hi]
        era_with_lanes = [s for s in era_sessions if s in lane_data]
        era_ead = [s for s in era_with_lanes if lane_data[s]["ead_lanes"] > 0]
        era_challenges = [s for s in era_sessions if s in challenge_sessions]
        era_deps = [s for s in era_sessions if s in deps_sessions]

        n = len(era_sessions)
        if n == 0:
            continue

        ead_pct = len(era_ead) / len(era_with_lanes) * 100 if era_with_lanes else 0
        challenge_rate = len(era_challenges) / n * 100
        deps_rate = len(era_deps) / n * 100

        print(f"  {era_name}: {n} sessions")
        print(f"    EAD coverage: {len(era_ead)}/{len(era_with_lanes)} sessions ({ead_pct:.1f}%)")
        print(f"    Challenge rate: {len(era_challenges)}/{n} ({challenge_rate:.1f}%)")
        print(f"    DEPS revision rate: {len(era_deps)}/{n} ({deps_rate:.1f}%)")
        print()

    # Within-era comparison: S178-S310 (voluntary)
    # Split by EAD presence in that session's lanes
    print("--- Within-Era Comparison (S178-S371, EAD vs non-EAD sessions) ---")
    ead_sessions_list = []
    non_ead_sessions_list = []
    for s in all_sessions:
        if s < 178:
            continue
        if s in lane_data and lane_data[s]["ead_lanes"] > 0:
            ead_sessions_list.append(s)
        elif s in lane_data:
            non_ead_sessions_list.append(s)

    for label, slist in [("EAD-present", ead_sessions_list), ("EAD-absent", non_ead_sessions_list)]:
        n = len(slist)
        if n == 0:
            print(f"  {label}: 0 sessions (skip)")
            continue
        chal = sum(1 for s in slist if s in challenge_sessions)
        deps = sum(1 for s in slist if s in deps_sessions)
        print(f"  {label}: {n} sessions")
        print(f"    Challenges: {chal}/{n} ({chal/n*100:.1f}%)")
        print(f"    DEPS revisions: {deps}/{n} ({deps/n*100:.1f}%)")

    print()

    # EAD compliance over time (rolling window)
    print("--- EAD Compliance Trend (10-session windows) ---")
    sorted_lane_sessions = sorted(lane_data.keys())
    window = 10
    for i in range(0, len(sorted_lane_sessions), window):
        chunk = sorted_lane_sessions[i:i+window]
        if len(chunk) < 3:
            continue
        ead_count = sum(1 for s in chunk if lane_data[s]["ead_lanes"] > 0)
        total = len(chunk)
        lo_s, hi_s = chunk[0], chunk[-1]
        print(f"  S{lo_s}-S{hi_s}: {ead_count}/{total} ({ead_count/total*100:.0f}%) EAD")

    print()

    # Belief revision density per era
    print("--- Belief Activity Density ---")
    # Count unique belief-related events (challenges + DEPS revisions) per session
    for era_name, (lo, hi) in eras.items():
        era_sessions = [s for s in all_sessions if lo <= s <= hi]
        n = len(era_sessions)
        if n == 0:
            continue
        events = sum(1 for s in era_sessions if s in challenge_sessions or s in deps_sessions)
        density = events / n * 100
        print(f"  {era_name}: {events} belief events / {n} sessions = {density:.1f}%")

    # Output JSON
    result = {
        "experiment": "F-AI3 EAD belief drift",
        "session": "S371",
        "date": "2026-03-01",
        "method": "Observational: parse SWARM-LANES for EAD fields, CHALLENGES.md for filings, git log for DEPS.md revisions",
        "n_sessions": len(all_sessions),
        "n_challenges": len(challenges),
        "n_deps_revisions": len(deps_revisions),
        "eras": {},
        "within_era": {},
    }

    for era_name, (lo, hi) in eras.items():
        era_sessions = [s for s in all_sessions if lo <= s <= hi]
        era_with_lanes = [s for s in era_sessions if s in lane_data]
        era_ead = [s for s in era_with_lanes if lane_data[s]["ead_lanes"] > 0]
        era_challenges = [s for s in era_sessions if s in challenge_sessions]
        era_deps = [s for s in era_sessions if s in deps_sessions]
        n = len(era_sessions)
        result["eras"][era_name] = {
            "sessions": n,
            "ead_sessions": len(era_ead),
            "lane_sessions": len(era_with_lanes),
            "challenges": len(era_challenges),
            "deps_revisions": len(era_deps),
            "challenge_rate": len(era_challenges) / n if n else 0,
            "deps_rate": len(era_deps) / n if n else 0,
        }

    result["within_era"]["ead_present"] = {
        "n": len(ead_sessions_list),
        "challenges": sum(1 for s in ead_sessions_list if s in challenge_sessions),
        "deps_revisions": sum(1 for s in ead_sessions_list if s in deps_sessions),
    }
    result["within_era"]["ead_absent"] = {
        "n": len(non_ead_sessions_list),
        "challenges": sum(1 for s in non_ead_sessions_list if s in challenge_sessions),
        "deps_revisions": sum(1 for s in non_ead_sessions_list if s in deps_sessions),
    }

    out_path = ROOT / "experiments" / "ai" / "f-ai3-ead-belief-drift-s371.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nArtifact: {out_path.relative_to(ROOT)}")

    return result


if __name__ == "__main__":
    main()
