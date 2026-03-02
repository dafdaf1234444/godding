#!/usr/bin/env python3
"""Claude Code PreCompact hook: checkpoint in-flight state before context compaction.

Fires before both manual (/compact) and auto-compaction.
Writes workspace/precompact-checkpoint-<session_id[:8]>.json with enough
state for the post-compaction session to resume without re-orienting from scratch.

F-CC3: Wired S301 | 2026-02-28
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def read_next_md(cwd: str) -> dict:
    """Extract key state from tasks/NEXT.md."""
    next_path = Path(cwd) / "tasks" / "NEXT.md"
    if not next_path.exists():
        return {"error": "NEXT.md not found"}
    content = next_path.read_text(encoding="utf-8", errors="replace")
    # Grab 'For next session' block and 'Key state' block
    sections = {}
    current = None
    for line in content.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current:
            sections[current].append(line)
    # Return trimmed versions of the most useful sections
    result = {}
    for key in ("For next session", "Key state", "Priorities"):
        if key in sections:
            result[key] = "\n".join(sections[key][:30]).strip()
    return result


def uncommitted_files(cwd: str) -> list:
    """List files with uncommitted changes (staged + unstaged)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=cwd, timeout=10
        )
        lines = [l[3:].strip() for l in result.stdout.splitlines() if l.strip()]
        return lines[:20]  # cap at 20
    except Exception:
        return []


def recent_workspace_files(cwd: str) -> list:
    """List workspace/ files modified in the last hour."""
    ws = Path(cwd) / "workspace"
    if not ws.exists():
        return []
    cutoff = time.time() - 3600
    recent = []
    for f in ws.iterdir():
        if f.is_file() and f.stat().st_mtime > cutoff:
            recent.append(f.name)
    return sorted(recent)[-10:]


def recent_git_log(cwd: str) -> list:
    """Last 5 commit one-liners."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True, text=True, cwd=cwd, timeout=10
        )
        return result.stdout.strip().splitlines()
    except Exception:
        return []


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    cwd = data.get("cwd", os.getcwd())
    session_id = data.get("session_id", "unknown")
    trigger = data.get("trigger", "unknown")  # "manual" or "auto"
    transcript_path = data.get("transcript_path", "")
    custom_instructions = data.get("custom_instructions", "")

    checkpoint = {
        "schema": "precompact-checkpoint-v1",
        "session_id": session_id,
        "session_short": session_id[:8],
        "trigger": trigger,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "transcript_path": transcript_path,
        "custom_instructions": custom_instructions,
        "next_md": read_next_md(cwd),
        "uncommitted_files": uncommitted_files(cwd),
        "recent_workspace_files": recent_workspace_files(cwd),
        "recent_git_log": recent_git_log(cwd),
        "resume_hint": (
            "Context was compacted. Read workspace/precompact-checkpoint-<id>.json "
            "to recover in-flight state. Re-run python3 tools/orient.py to re-orient."
        ),
    }

    # Write checkpoint
    ws = Path(cwd) / "workspace"
    ws.mkdir(exist_ok=True)
    out = ws / f"precompact-checkpoint-{session_id[:8]}.json"
    out.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

    # Human-visible notice (goes to stderr, shown in UI)
    trigger_label = "auto-compaction" if trigger == "auto" else "manual /compact"
    print(
        f"[PreCompact] Checkpoint written ({trigger_label}): {out.name}",
        file=sys.stderr
    )


if __name__ == "__main__":
    main()
