#!/usr/bin/env python3
"""Shared I/O utilities for swarm tools.

Eliminates duplication of _read(), _git(), _session_number(), _token_count(),
parse_lane_rows(), parse_lane_tags() across 30+ tool files (L-476, L-561).
Import from here instead of redefining.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def read_text(path: Path) -> str:
    """Read file as UTF-8 with replace errors. Returns '' on any failure."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def git_cmd(*args: str, timeout: int = 10) -> str:
    """Run git command in repo root, return stdout. Returns '' on failure."""
    try:
        return subprocess.run(
            ["git", "-C", str(REPO_ROOT)] + list(args),
            capture_output=True, text=True, timeout=timeout,
        ).stdout.rstrip("\n")
    except Exception:
        return ""


def git_cmd_strict(*args: str, timeout: int = 10) -> str:
    """Run git command in repo root, raise RuntimeError on failure."""
    r = subprocess.run(
        ["git", "-C", str(REPO_ROOT)] + list(args),
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.rstrip("\n")


def session_number() -> int:
    """Best-effort current session number from SESSION-LOG + git log."""
    numbers = re.findall(
        r"^S(\d+)", read_text(REPO_ROOT / "memory" / "SESSION-LOG.md"), re.MULTILINE
    )
    log_max = max(int(n) for n in numbers) if numbers else 0
    try:
        git_out = subprocess.run(
            ["git", "log", "--oneline", "-50"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=5,
        ).stdout
        git_max = max(
            (int(m) for m in re.findall(r"\[S(\d+)\]", git_out)), default=0
        )
    except Exception:
        git_max = 0
    return max(log_max, git_max)


def token_count(path: Path) -> int:
    """Estimate token count (chars / 4). Returns 0 on failure."""
    try:
        return len(read_text(path)) // 4
    except Exception:
        return 0


def line_count(path: Path) -> int:
    """Count lines in file. Returns 0 on failure."""
    try:
        return len(read_text(path).splitlines())
    except Exception:
        return 0


# --- SWARM-LANES parsing (consolidates 14 reimplementations, L-561) ---

LANE_KEYS = (
    "date", "lane", "session", "agent", "branch", "pr",
    "model", "platform", "scope_key", "etc", "status", "notes",
)

_HEADER_RE = re.compile(r"^\|\s*(Date\s*\||[-: ]+\|)", re.IGNORECASE)


def parse_lane_rows(text: str) -> list[dict[str, str]]:
    """Parse SWARM-LANES.md markdown table into list of row dicts.

    Returns dicts keyed by LANE_KEYS with status uppercased.
    Skips header/separator rows automatically.
    """
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|") or _HEADER_RE.match(line):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < len(LANE_KEYS):
            continue
        row = dict(zip(LANE_KEYS, parts))
        row["status"] = row["status"].upper()
        rows.append(row)
    return rows


def parse_lane_tags(etc_value: str) -> dict[str, str]:
    """Parse key=value pairs from the Etc column of a lane row.

    Handles semicolon, comma, and whitespace delimiters.
    Returns lowercase keys mapped to values.
    """
    return {
        k.strip().lower(): v.strip()
        for k, v in re.findall(
            r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)", etc_value or ""
        )
    }


def lesson_paths() -> list[Path]:
    """Return sorted list of lesson file paths (L-*.md)."""
    d = REPO_ROOT / "memory" / "lessons"
    if not d.exists():
        return []
    return sorted(d.glob("L-*.md"),
                  key=lambda p: int(re.search(r"\d+", p.stem).group()))
