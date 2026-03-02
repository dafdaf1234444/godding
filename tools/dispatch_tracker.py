#!/usr/bin/env python3
"""
dispatch_tracker.py — Session dispatch tracking for the swarm. (F-EXP1)

Solves the C1 duplication problem: nodes start the same frontier because they can't see
what other concurrent sessions are working on. This tool maintains a shared dispatch log
so nodes can claim a frontier before working on it, and release it when done.

Usage:
  python3 tools/dispatch_tracker.py init               -- create workspace/DISPATCH-LOG.md
  python3 tools/dispatch_tracker.py claim <frontier>   -- declare intent to work on <frontier>
  python3 tools/dispatch_tracker.py release <frontier> [done|abandoned]  -- mark complete/abandoned
  python3 tools/dispatch_tracker.py status             -- show currently claimed frontiers
  python3 tools/dispatch_tracker.py report             -- throughput report (F-EXP1 measurement)
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DISPATCH_LOG = ROOT / "workspace" / "DISPATCH-LOG.md"

HEADER = """\
# Dispatch Log
<!-- F-EXP1: Track which session is working on which frontier.
     Nodes claim frontiers before starting, release when done.
     Prevents C1 duplication (concurrent nodes working on same frontier).
     Format: | Session | Frontier | Status | Timestamp |  -->

| Session | Frontier | Status | Timestamp |
|---------|----------|--------|-----------|
"""


try:
    _tools_path = str(Path(__file__).resolve().parent)
    import sys as _sys; _sys.path.insert(0, _tools_path)
    from swarm_io import session_number as _sn_int
    def _current_session(): return f"S{_sn_int()}"
except ImportError:
    def _current_session() -> str:
        try:
            import subprocess
            r = subprocess.run(["git", "log", "--oneline", "-30"],
                               capture_output=True, text=True, cwd=ROOT)
            nums = [int(m) for m in re.findall(r"\[S(\d+)\]", r.stdout)]
            return f"S{max(nums) + 1}" if nums else "S?"
        except Exception:
            return "S?"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def _read_log() -> str:
    return DISPATCH_LOG.read_text() if DISPATCH_LOG.exists() else ""


def _write_row(session: str, frontier: str, status: str) -> None:
    now = _now()
    row = f"| {session} | {frontier} | {status} | {now} |\n"
    if not DISPATCH_LOG.exists():
        DISPATCH_LOG.parent.mkdir(parents=True, exist_ok=True)
        DISPATCH_LOG.write_text(HEADER + row)
    else:
        DISPATCH_LOG.write_text(_read_log() + row)


def cmd_init() -> None:
    if DISPATCH_LOG.exists():
        print(f"Already exists: {DISPATCH_LOG.relative_to(ROOT)}")
        return
    DISPATCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    DISPATCH_LOG.write_text(HEADER)
    print(f"Created {DISPATCH_LOG.relative_to(ROOT)}")


def cmd_claim(frontier: str) -> None:
    session = _current_session()
    # Check for existing in-progress claim on this frontier
    text = _read_log()
    rows = re.findall(
        r"^\|\s*(S\d+)\s*\|\s*" + re.escape(frontier) + r"\s*\|\s*in-progress\s*\|",
        text, re.MULTILINE | re.IGNORECASE
    )
    if rows:
        print(f"WARNING: {frontier} already claimed by {rows[-1]}. You may be duplicating work.")
        print("Proceed anyway? [y/N]", end=" ", flush=True)
        if sys.stdin.readline().strip().lower() != "y":
            print("Aborted.")
            return

    _write_row(session, frontier, "in-progress")
    print(f"[{session}] Claimed {frontier} as in-progress")


def cmd_release(frontier: str, outcome: str = "done") -> None:
    if outcome not in ("done", "abandoned"):
        print(f"Error: outcome must be 'done' or 'abandoned', got '{outcome}'")
        sys.exit(1)
    session = _current_session()
    _write_row(session, frontier, outcome)
    print(f"[{session}] Released {frontier} as {outcome}")


def cmd_status() -> None:
    text = _read_log()
    if not text:
        print("No dispatch log found. Run: python3 tools/dispatch_tracker.py init")
        return

    # For each frontier, find its most recent status row
    rows = re.findall(
        r"^\|\s*(S\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|",
        text, re.MULTILINE
    )
    # Build most recent status per frontier
    latest: dict[str, tuple[str, str, str]] = {}
    for session, frontier, status, ts in rows:
        frontier = frontier.strip()
        latest[frontier] = (session.strip(), status.strip(), ts.strip())

    in_progress = [(f, s, ts) for f, (s, status, ts) in latest.items()
                   if status.lower() == "in-progress"]
    done = [(f, s) for f, (s, status, _) in latest.items() if status.lower() == "done"]

    print("=== DISPATCH STATUS ===")
    print(f"In-progress ({len(in_progress)}):")
    if in_progress:
        for frontier, session, ts in in_progress:
            print(f"  [{session}] {frontier}  (since {ts})")
    else:
        print("  (none)")
    print(f"Completed ({len(done)}):")
    for frontier, session in done[:5]:
        print(f"  {frontier} by {session}")
    if len(done) > 5:
        print(f"  ... +{len(done)-5} more")


def cmd_report() -> None:
    text = _read_log()
    if not text:
        print("No dispatch log. Run: python3 tools/dispatch_tracker.py init")
        return

    rows = re.findall(
        r"^\|\s*(S\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|",
        text, re.MULTILINE
    )
    total = len(rows)
    done = sum(1 for _, _, s, _ in rows if s.strip().lower() == "done")
    in_prog = sum(1 for _, _, s, _ in rows if s.strip().lower() == "in-progress")
    abandoned = sum(1 for _, _, s, _ in rows if s.strip().lower() == "abandoned")

    print("=== F-EXP1 DISPATCH REPORT ===")
    print(f"Total dispatch events: {total}")
    print(f"  done:       {done}")
    print(f"  in-progress:{in_prog}")
    print(f"  abandoned:  {abandoned}")
    if total > 0:
        completion_rate = done / (done + abandoned) if (done + abandoned) > 0 else 0.0
        print(f"Completion rate (done / done+abandoned): {completion_rate:.1%}")
    print()
    print("Use this data to measure F-EXP1: does dispatch_optimizer score-ranked selection")
    print("increase domain experiment throughput vs random dispatch?")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "init":
        cmd_init()
    elif cmd == "claim":
        if not args:
            print("Usage: dispatch_tracker.py claim <frontier>")
            sys.exit(1)
        cmd_claim(args[0])
    elif cmd == "release":
        if not args:
            print("Usage: dispatch_tracker.py release <frontier> [done|abandoned]")
            sys.exit(1)
        outcome = args[1] if len(args) > 1 else "done"
        cmd_release(args[0], outcome)
    elif cmd == "status":
        cmd_status()
    elif cmd == "report":
        cmd_report()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
