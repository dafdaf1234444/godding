#!/usr/bin/env python3
"""tools/claim.py — Soft-claim protocol for concurrent session coordination

Prevents C-EDIT DUE-convergence collisions (L-557, F-CON2). Sessions declare
intent before editing shared files; check/release prevents duplicate work.
Lesson-slot pre-claiming (CE-4 fix, F-CON2): sessions atomically reserve the
next available L-NNN slot before writing a new lesson.
Task-level claiming (L-686): sessions claim tasks to prevent duplication at N>=3.
Session heartbeat: broadcasts current work for cross-session visibility.

Usage:
  python3 tools/claim.py claim <file> [--session <id>]   # Claim a file
  python3 tools/claim.py check <file>                     # Check if claimed (exit 0=free, 1=claimed)
  python3 tools/claim.py release <file> [--session <id>] # Release claim
  python3 tools/claim.py list                             # List active claims (files + tasks)
  python3 tools/claim.py gc                               # Garbage collect expired claims
  python3 tools/claim.py next-lesson [--session <id>]    # Claim next L-NNN slot; prints path
  python3 tools/claim.py claim-task <fingerprint> [--desc "..."]  # Claim a task
  python3 tools/claim.py check-task <fingerprint>         # Check if task is claimed
  python3 tools/claim.py release-task <fingerprint>       # Release task claim
  python3 tools/claim.py list-tasks                       # List active task claims
  python3 tools/claim.py heartbeat [--task "..."] [--desc "..."]  # Broadcast session activity
  python3 tools/claim.py sessions                         # Show active sessions
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CLAIMS_DIR = Path("workspace/claims")
CLAIM_TTL_SECONDS = 120  # 2 minutes — sessions that crash leave auto-expiring claims (L-589: 300s→120s, commit cycle ~60s at N≥5)
TASK_CLAIM_TTL_SECONDS = 600  # 10 minutes — tasks take longer than file edits
SESSION_TTL_SECONDS = 600  # 10 minutes — session heartbeat expiry


def get_session_id():
    """Get current session ID from env or generate a stable one from PID."""
    return os.environ.get("SWARM_SESSION_ID", f"pid-{os.getpid()}")


def claim_path(file: str) -> Path:
    """Map a file path to its claim file in workspace/claims/."""
    safe = file.replace("/", "__").replace("\\", "__")
    return CLAIMS_DIR / f"{safe}.claim.json"


def read_claim(path: Path) -> dict | None:
    """Read a claim file; return None if missing or expired."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(data["timestamp"])).total_seconds()
        if age > CLAIM_TTL_SECONDS:
            path.unlink(missing_ok=True)
            return None
        return data
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def cmd_claim(file: str, session: str) -> int:
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
    path = claim_path(file)
    existing = read_claim(path)
    if existing and existing.get("session") != session:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(existing["timestamp"])).total_seconds()
        print(f"CLAIMED: {file} — held by {existing['session']} ({int(age)}s ago). Wait or choose different work.")
        return 1
    data = {"file": file, "session": session, "timestamp": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(data, indent=2))
    print(f"CLAIMED: {file} by {session}")
    return 0


def cmd_check(file: str) -> int:
    path = claim_path(file)
    existing = read_claim(path)
    if existing:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(existing["timestamp"])).total_seconds()
        print(f"CLAIMED by {existing['session']} ({int(age)}s ago) — {file}")
        return 1
    print(f"FREE: {file}")
    return 0


def cmd_release(file: str, session: str) -> int:
    path = claim_path(file)
    existing = read_claim(path)
    if not existing:
        print(f"NOT CLAIMED: {file}")
        return 0
    if existing.get("session") != session:
        print(f"WARN: {file} is claimed by {existing['session']}, not {session} — not releasing")
        return 1
    path.unlink(missing_ok=True)
    print(f"RELEASED: {file} by {session}")
    return 0


def cmd_list() -> int:
    if not CLAIMS_DIR.exists():
        print("No claims directory.")
        return 0
    claims = []
    for p in CLAIMS_DIR.glob("*.claim.json"):
        data = read_claim(p)
        if data:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(data["timestamp"])).total_seconds()
            claims.append((data["file"], data["session"], int(age)))
    if not claims:
        print("No active claims.")
        return 0
    for file, session, age in sorted(claims, key=lambda x: x[2]):
        print(f"  {session:20s} {age:4d}s  {file}")
    return 0


def cmd_gc() -> int:
    if not CLAIMS_DIR.exists():
        return 0
    removed = 0
    for p in CLAIMS_DIR.glob("*.claim.json"):
        if read_claim(p) is None:
            p.unlink(missing_ok=True)
            removed += 1
    print(f"GC: removed {removed} expired claims")
    return 0


def cmd_next_lesson(session: str) -> int:
    """Atomically claim the next available L-NNN lesson slot (CE-4 fix, F-CON2).

    Scans existing lessons + active claims to find the highest slot in use, then
    claims max+1. Prints the claimed path so callers can use it directly.

    Returns 0 on success, 1 if claim failed (race with another session).
    """
    import re
    LESSONS_DIR = Path("memory/lessons")
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)

    # Find max existing lesson number
    max_existing = 0
    if LESSONS_DIR.exists():
        for p in LESSONS_DIR.glob("L-*.md"):
            m = re.match(r"L-(\d+)\.md$", p.name)
            if m:
                max_existing = max(max_existing, int(m.group(1)))

    # Find max claimed lesson slot (active claims only)
    max_claimed = max_existing
    for p in CLAIMS_DIR.glob("*.claim.json"):
        data = read_claim(p)
        if data and data.get("slot_type") == "lesson":
            m = re.match(r"L-(\d+)\.md$", Path(data["file"]).name)
            if m:
                max_claimed = max(max_claimed, int(m.group(1)))

    # Claim the next slot
    next_num = max_claimed + 1
    slot_path = f"memory/lessons/L-{next_num}.md"
    claim_file = claim_path(slot_path)

    existing = read_claim(claim_file)
    if existing and existing.get("session") != session:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(existing["timestamp"])).total_seconds()
        print(f"SLOT_CONFLICT: L-{next_num} already claimed by {existing['session']} ({int(age)}s ago)", file=sys.stderr)
        # Try next slot
        next_num += 1
        slot_path = f"memory/lessons/L-{next_num}.md"
        claim_file = claim_path(slot_path)

    data = {
        "file": slot_path,
        "session": session,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "slot_type": "lesson",
    }
    claim_file.write_text(json.dumps(data, indent=2))
    print(slot_path)
    return 0


# --- Task-level claiming (L-686) ---

def task_claim_path(fingerprint: str) -> Path:
    """Map a task fingerprint to its claim file."""
    safe = re.sub(r"[^a-z0-9-]", "-", fingerprint.lower()).strip("-")
    return CLAIMS_DIR / f"task__{safe}.claim.json"


def read_task_claim(path: Path) -> dict | None:
    """Read a task claim; return None if missing or expired."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(data["timestamp"])).total_seconds()
        if age > TASK_CLAIM_TTL_SECONDS:
            path.unlink(missing_ok=True)
            return None
        return data
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def cmd_claim_task(fingerprint: str, session: str, description: str = "") -> int:
    """Claim a task by fingerprint. Returns 0 on success, 1 if already claimed."""
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
    path = task_claim_path(fingerprint)
    existing = read_task_claim(path)
    if existing and existing.get("session") != session:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(existing["timestamp"])).total_seconds()
        print(f"TASK CLAIMED: {fingerprint} — held by {existing['session']} ({int(age)}s ago)")
        return 1
    data = {
        "fingerprint": fingerprint,
        "session": session,
        "description": description,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "task",
    }
    path.write_text(json.dumps(data, indent=2))
    print(f"TASK CLAIMED: {fingerprint} by {session}")
    return 0


def cmd_check_task(fingerprint: str) -> int:
    """Check if a task is claimed."""
    path = task_claim_path(fingerprint)
    existing = read_task_claim(path)
    if existing:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(existing["timestamp"])).total_seconds()
        print(f"TASK CLAIMED by {existing['session']} ({int(age)}s ago) — {fingerprint}")
        return 1
    print(f"TASK FREE: {fingerprint}")
    return 0


def cmd_release_task(fingerprint: str, session: str) -> int:
    """Release a task claim."""
    path = task_claim_path(fingerprint)
    existing = read_task_claim(path)
    if not existing:
        print(f"TASK NOT CLAIMED: {fingerprint}")
        return 0
    if existing.get("session") != session:
        print(f"WARN: {fingerprint} claimed by {existing['session']}, not {session}")
        return 1
    path.unlink(missing_ok=True)
    print(f"TASK RELEASED: {fingerprint} by {session}")
    return 0


def cmd_list_tasks() -> int:
    """List active task claims."""
    if not CLAIMS_DIR.exists():
        print("No active task claims.")
        return 0
    claims = []
    for p in CLAIMS_DIR.glob("task__*.claim.json"):
        data = read_task_claim(p)
        if data:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(data["timestamp"])).total_seconds()
            claims.append((data["fingerprint"], data["session"], data.get("description", ""), int(age)))
    if not claims:
        print("No active task claims.")
        return 0
    for fp, session, desc, age in sorted(claims, key=lambda x: x[3]):
        print(f"  {session:20s} {age:4d}s  {fp}" + (f": {desc[:60]}" if desc else ""))
    return 0


def get_active_task_claims(exclude_session: str | None = None) -> dict[str, dict]:
    """Get all active task claims, optionally excluding a session.

    Importable by task_order.py and orient.py for claim-aware task filtering.
    Returns dict mapping fingerprint → claim data.
    """
    claims = {}
    if not CLAIMS_DIR.exists():
        return claims
    for p in CLAIMS_DIR.glob("task__*.claim.json"):
        data = read_task_claim(p)
        if data and (exclude_session is None or data.get("session") != exclude_session):
            claims[data["fingerprint"]] = data
    return claims


# --- Session heartbeat (L-686) ---

def session_path(session: str) -> Path:
    """Map a session ID to its heartbeat file."""
    safe = re.sub(r"[^a-z0-9-]", "-", session.lower()).strip("-")
    return CLAIMS_DIR / f"session__{safe}.json"


def cmd_heartbeat(session: str, task: str = "", description: str = "") -> int:
    """Broadcast session activity — what this session is working on."""
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
    path = session_path(session)
    data = {
        "session": session,
        "current_task": task,
        "description": description,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "session",
    }
    path.write_text(json.dumps(data, indent=2))
    print(f"HEARTBEAT: {session} → {task or '(idle)'}")
    return 0


def cmd_sessions() -> int:
    """Show active sessions and their current work."""
    if not CLAIMS_DIR.exists():
        print("No active sessions.")
        return 0
    sessions = []
    for p in CLAIMS_DIR.glob("session__*.json"):
        try:
            data = json.loads(p.read_text())
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(data["timestamp"])).total_seconds()
            if age > SESSION_TTL_SECONDS:
                p.unlink(missing_ok=True)
                continue
            sessions.append((data["session"], data.get("current_task", ""), data.get("description", ""), int(age)))
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    if not sessions:
        print("No active sessions.")
        return 0
    print(f"--- Active sessions ({len(sessions)}) ---")
    for sess, task, desc, age in sorted(sessions, key=lambda x: x[3]):
        label = task or "(idle)"
        if desc:
            label += f": {desc[:50]}"
        print(f"  {sess:15s} {age:4d}s ago  {label}")
    return 0


def get_active_sessions(exclude_session: str | None = None) -> list[dict]:
    """Get all active session heartbeats, optionally excluding a session.

    Importable by orient.py for cross-session visibility.
    Returns list of session dicts with session, current_task, description, age_s.
    """
    sessions = []
    if not CLAIMS_DIR.exists():
        return sessions
    for p in CLAIMS_DIR.glob("session__*.json"):
        try:
            data = json.loads(p.read_text())
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(data["timestamp"])).total_seconds()
            if age > SESSION_TTL_SECONDS:
                p.unlink(missing_ok=True)
                continue
            if exclude_session and data.get("session") == exclude_session:
                continue
            data["age_s"] = int(age)
            sessions.append(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return sorted(sessions, key=lambda x: x["age_s"])


def main():
    parser = argparse.ArgumentParser(description="Soft-claim protocol for concurrent session coordination (L-557, F-CON2, L-686)")
    parser.add_argument("command", choices=[
        "claim", "check", "release", "list", "gc", "next-lesson",
        "claim-task", "check-task", "release-task", "list-tasks",
        "heartbeat", "sessions",
    ])
    parser.add_argument("file", nargs="?", help="File or task fingerprint to claim/check/release")
    parser.add_argument("--session", default=None, help="Session ID (defaults to SWARM_SESSION_ID env or PID)")
    parser.add_argument("--desc", default="", help="Description for task claim or heartbeat")
    parser.add_argument("--task", default="", help="Current task for heartbeat")
    args = parser.parse_args()

    session = args.session or get_session_id()

    if args.command in ("claim", "check", "release") and not args.file:
        parser.error(f"'{args.command}' requires a file argument")
    if args.command in ("claim-task", "check-task", "release-task") and not args.file:
        parser.error(f"'{args.command}' requires a task fingerprint argument")

    if args.command == "claim":
        return cmd_claim(args.file, session)
    elif args.command == "check":
        return cmd_check(args.file)
    elif args.command == "release":
        return cmd_release(args.file, session)
    elif args.command == "list":
        return cmd_list()
    elif args.command == "gc":
        return cmd_gc()
    elif args.command == "next-lesson":
        return cmd_next_lesson(session)
    elif args.command == "claim-task":
        return cmd_claim_task(args.file, session, args.desc)
    elif args.command == "check-task":
        return cmd_check_task(args.file)
    elif args.command == "release-task":
        return cmd_release_task(args.file, session)
    elif args.command == "list-tasks":
        return cmd_list_tasks()
    elif args.command == "heartbeat":
        return cmd_heartbeat(session, args.task, args.desc)
    elif args.command == "sessions":
        return cmd_sessions()


if __name__ == "__main__":
    sys.exit(main())
