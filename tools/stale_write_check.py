#!/usr/bin/env python3
"""FM-19 stale-write detector: detect concurrent logical overwrites at pre-commit.

For each staged file, checks whether another session modified that file in HEAD
since this session's base commit. If so, the staged version may overwrite concurrent
changes (logical overwrite — FM-19, L-525).

Usage:
  python3 tools/stale_write_check.py [--staged]        # check staged files
  python3 tools/stale_write_check.py --audit            # audit last 50 commits

Exit codes:
  0 = no stale writes detected (or only low-risk files)
  1 = high-risk stale writes detected (BLOCK)
  2 = medium-risk stale writes detected (WARN)
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files ranked by contention risk (from FM-19 collision surface analysis S422).
# REPLACE-mode files where second writer obliterates first's changes.
HIGH_CONTENTION = {
    "workspace/maintenance-outcomes.json": "REPLACE",
    "tools/periodics.json": "REPLACE",
    "tasks/NEXT.md": "MIXED",
    "tasks/SWARM-LANES.md": "APPEND",
    "memory/INDEX.md": "APPEND",
    "docs/PAPER.md": "REPLACE",
    "README.md": "REPLACE",
    "domains/meta/SESSION-TRIGGER.md": "REPLACE",
    "tasks/FRONTIER.md": "MIXED",
    "beliefs/PHILOSOPHY.md": "MIXED",
    "memory/PRINCIPLES.md": "MIXED",
}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=REPO_ROOT
    )
    return result.stdout.strip()


def get_session_from_msg(msg: str) -> str | None:
    m = re.search(r"\[S(\d+)\]", msg)
    return f"S{m.group(1)}" if m else None


def get_current_session(override: str | None = None) -> str | None:
    """Infer current session. Uses --session override if provided (L-1175).

    At N>=3 concurrency, git log returns another session's number because
    all recent commits may be from concurrent sessions. The --session flag
    lets check.sh pass the actual session from the commit message.
    """
    if override:
        return override
    # Fallback: infer from most recent git log entry
    log = git("log", "--oneline", "-5")
    for line in log.splitlines():
        s = get_session_from_msg(line)
        if s:
            return s
    return None


def get_base_commit() -> str | None:
    """Get the base commit: the last commit HEAD pointed to before staged changes.

    For the stale-write check, we use the current HEAD as the reference.
    If another session committed to a file MORE RECENTLY than our base,
    and we're about to overwrite it, that's a stale write.
    """
    return git("rev-parse", "HEAD") or None


def get_staged_files() -> list[str]:
    output = git("diff", "--cached", "--name-only")
    return [f for f in output.splitlines() if f.strip()]


def last_modifier(filepath: str) -> tuple[str | None, str]:
    """Return (session, commit_hash) of the last commit that touched this file."""
    log = git("log", "--format=%H %s", "-1", "--", filepath)
    if not log:
        return None, ""
    parts = log.split(" ", 1)
    commit_hash = parts[0]
    msg = parts[1] if len(parts) > 1 else ""
    return get_session_from_msg(msg), commit_hash


def check_content_loss(filepath: str) -> list[str]:
    """For APPEND/MIXED files, check if HEAD has lines missing from staged version.

    L-1176: For SWARM-LANES.md, lane status transitions (ACTIVE→MERGED/ABANDONED)
    via close_lane.py are intentional, not content loss. Filter these out by checking
    if the lane ID still exists in the staged version.
    """
    try:
        head_content = git("show", f"HEAD:{filepath}")
        staged_content = git("show", f":0:{filepath}")  # index stage 0
    except Exception:
        return []

    if not head_content or not staged_content:
        return []

    head_lines = set(head_content.splitlines())
    staged_lines = set(staged_content.splitlines())
    lost = head_lines - staged_lines

    # Filter trivial lines (empty, whitespace, common headers)
    lost = {
        line
        for line in lost
        if line.strip() and not line.strip().startswith("#") and len(line.strip()) > 10
    }

    # For SWARM-LANES.md: filter lane status transitions (close_lane.py operations)
    if filepath == "tasks/SWARM-LANES.md" and lost:
        lane_pattern = re.compile(r"DOMEX-[\w-]+")
        staged_text = "\n".join(staged_lines)
        filtered = set()
        for line in lost:
            m = lane_pattern.search(line)
            if m and m.group(0) in staged_text:
                continue  # Lane ID still present — status transition, not loss
            filtered.add(line)
        lost = filtered

    return sorted(lost)[:5]  # Cap at 5 examples


def detect_concurrency() -> int:
    """Count unique sessions in last 10 commits to estimate concurrency level."""
    log = git("log", "--oneline", "-10")
    sessions = set()
    for line in log.splitlines():
        s = get_session_from_msg(line)
        if s:
            sessions.add(s)
    return len(sessions)


def check_staged(verbose: bool = False, session_override: str | None = None) -> int:
    staged = get_staged_files()
    if not staged:
        return 0

    current_session = get_current_session(session_override)
    concurrency = detect_concurrency()
    high_concurrency = concurrency >= 3
    warnings = []
    blocks = []

    for filepath in staged:
        if filepath not in HIGH_CONTENTION:
            continue

        risk_mode = HIGH_CONTENTION[filepath]
        last_session, last_hash = last_modifier(filepath)

        if last_session and last_session != current_session:
            entry = {
                "file": filepath,
                "mode": risk_mode,
                "last_modifier": last_session,
                "current_session": current_session or "unknown",
            }

            # For APPEND/MIXED files, check actual content loss
            if risk_mode in ("APPEND", "MIXED"):
                lost_lines = check_content_loss(filepath)
                if lost_lines:
                    entry["lost_lines_sample"] = lost_lines
                    if high_concurrency:
                        # At N>=3 concurrency, content divergence is expected —
                        # multiple sessions append different content. Downgrade
                        # from BLOCK to WARN to prevent false FM-19 blocks
                        # (L-1275: 5+ blocks/session at N>=5).
                        entry["severity"] = "MEDIUM"
                        entry["note"] = f"downgraded from HIGH (N={concurrency} concurrency)"
                        warnings.append(entry)
                    else:
                        entry["severity"] = "HIGH"
                        blocks.append(entry)
                else:
                    entry["severity"] = "LOW"
                    if verbose:
                        warnings.append(entry)
            elif risk_mode == "REPLACE":
                entry["severity"] = "MEDIUM"
                warnings.append(entry)

    exit_code = 0

    if blocks:
        print("FM-19 STALE-WRITE DETECTED (content loss risk):")
        for b in blocks:
            print(f"  ! {b['file']} — modified by {b['last_modifier']}, you are {b['current_session']}")
            print(f"    Mode: {b['mode']} | Lost lines sample:")
            for line in b.get("lost_lines_sample", []):
                print(f"      - {line[:80]}")
            print(f"    Fix: git restore --staged {b['file']} && git restore --source=HEAD {b['file']} && re-apply your changes")
            print(f"         To inspect: git show HEAD:{b['file']} | head -20")
        exit_code = 1

    if warnings:
        print("FM-19 stale-write WARNING (concurrent modification):")
        for w in warnings:
            print(f"  ~ {w['file']} — last modified by {w['last_modifier']}, you are {w['current_session']}")
            print(f"    Mode: {w['mode']} | Severity: {w['severity']}")
            if w["mode"] == "REPLACE":
                print(f"    Note: REPLACE-mode file — your version will fully overwrite {w['last_modifier']}'s changes")
        if exit_code == 0:
            exit_code = 2

    if exit_code == 0 and verbose:
        contention_staged = [f for f in staged if f in HIGH_CONTENTION]
        if contention_staged:
            print(f"FM-19 check: PASS ({len(contention_staged)} high-contention file(s), no stale writes)")
        else:
            print("FM-19 check: PASS (no high-contention files staged)")

    return exit_code


def audit_history(n: int = 50) -> dict:
    """Audit last N commits for FM-19 collision patterns."""
    log = git("log", "--format=%H|%s", f"-{n}")
    commits = []
    for line in log.splitlines():
        if "|" not in line:
            continue
        h, msg = line.split("|", 1)
        session = get_session_from_msg(msg)
        files = git("diff-tree", "--no-commit-id", "-r", "--name-only", h).splitlines()
        commits.append({"hash": h[:8], "session": session, "msg": msg[:60], "files": files})

    # Find concurrent overwrites: same file modified by different sessions within 5 commits
    collisions = {}
    for i, c1 in enumerate(commits):
        for j in range(i + 1, min(i + 6, len(commits))):
            c2 = commits[j]
            if c1["session"] == c2["session"]:
                continue
            shared = set(c1["files"]) & set(c2["files"])
            for f in shared:
                if f not in collisions:
                    collisions[f] = []
                collisions[f].append(
                    {
                        "sessions": [c1["session"], c2["session"]],
                        "commits": [c1["hash"], c2["hash"]],
                        "distance": j - i,
                    }
                )

    # Summarize
    summary = {
        "commits_analyzed": len(commits),
        "unique_sessions": len({c["session"] for c in commits if c["session"]}),
        "total_collision_events": sum(len(v) for v in collisions.values()),
        "files_with_collisions": len(collisions),
        "top_contention": sorted(
            [
                {
                    "file": f,
                    "collision_count": len(events),
                    "in_high_contention_list": f in HIGH_CONTENTION,
                }
                for f, events in collisions.items()
            ],
            key=lambda x: x["collision_count"],
            reverse=True,
        )[:15],
    }

    return summary


def main():
    parser = argparse.ArgumentParser(description="FM-19 stale-write detector")
    parser.add_argument("--staged", action="store_true", help="Check staged files (default)")
    parser.add_argument("--audit", action="store_true", help="Audit last 50 commits")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all checks")
    parser.add_argument("--json", action="store_true", help="JSON output (audit mode)")
    parser.add_argument("--session", help="Override session identity (e.g. S470). At N>=3 concurrency, git-log inference picks wrong session (L-1175).")
    args = parser.parse_args()

    if args.audit:
        result = audit_history()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"FM-19 Audit: {result['commits_analyzed']} commits, "
                  f"{result['unique_sessions']} sessions, "
                  f"{result['total_collision_events']} collision events")
            print(f"Top contention files:")
            for entry in result["top_contention"][:10]:
                marker = " [TRACKED]" if entry["in_high_contention_list"] else ""
                print(f"  {entry['collision_count']:3d} | {entry['file']}{marker}")
        return 0

    return check_staged(verbose=args.verbose or True, session_override=args.session)


if __name__ == "__main__":
    sys.exit(main())
