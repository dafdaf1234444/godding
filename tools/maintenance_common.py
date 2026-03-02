#!/usr/bin/env python3
"""Shared constants, config, and helper functions for maintenance.py and its extracted modules.

Extracted from maintenance.py (DOMEX-META-S425) to reduce token count.
All maintenance_*.py modules import from here instead of receiving DI params.
"""

import hashlib
import importlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Dynamic symbol loading
# ---------------------------------------------------------------------------

def _load_symbol(module_names: tuple[str, ...], symbol: str):
    for name in module_names:
        try: return getattr(importlib.import_module(name), symbol)
        except (ModuleNotFoundError, AttributeError): continue
    return None

_paper_drift = _load_symbol(("tools.paper_drift", "paper_drift"), "check_paper_accuracy")
if _paper_drift is None:
    def run_paper_drift_check(repo_root: Path, session: int) -> list[tuple[str, str]]:
        return [
            ("NOTICE", "paper_drift module missing — skipping PAPER drift check (restore tools/paper_drift.py)")
        ]
else:
    run_paper_drift_check = _paper_drift

_active_principle_ids = _load_symbol(("tools.swarm_parse", "swarm_parse"), "active_principle_ids") or (lambda text: (set(), set()))

# Shared I/O utilities (L-476: deduplicate across 10+ tool files)
_swarm_io = None
for _mod_name in ("tools.swarm_io", "swarm_io"):
    try:
        _swarm_io = importlib.import_module(_mod_name)
        break
    except (ModuleNotFoundError, ImportError):
        continue

# ---------------------------------------------------------------------------
# Core path constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = sys.executable or "python3"
PRINCIPLE_ID_RE = re.compile(r"\bP-(\d+)\b")
UTILITY_CITATION_MAX_BYTES = 256 * 1024
UTILITY_CITATION_SKIP_PREFIXES = (
    ".git/",
    "workspace/notes/",
    "experiments/colonies/",
)
FILE_REF_ALIAS_MAP = {
    "SWARM.md": "SWARM.md", "CLAUDE.md": "CLAUDE.md", "AGENTS.md": "AGENTS.md",
    "GEMINI.md": "GEMINI.md", "README.md": "README.md",
    "CORE.md": "beliefs/CORE.md", "PHILOSOPHY.md": "beliefs/PHILOSOPHY.md",
    "DEPS.md": "beliefs/DEPS.md", "INVARIANTS.md": "beliefs/INVARIANTS.md",
    "CONFLICTS.md": "beliefs/CONFLICTS.md", "CHALLENGES.md": "beliefs/CHALLENGES.md",
    "INDEX.md": "memory/INDEX.md", "PRINCIPLES.md": "memory/PRINCIPLES.md",
    "SESSION-LOG.md": "memory/SESSION-LOG.md", "OPERATIONS.md": "memory/OPERATIONS.md",
    "HUMAN.md": "memory/HUMAN.md",
    "FRONTIER.md": "tasks/FRONTIER.md", "NEXT.md": "tasks/NEXT.md",
    "HUMAN-QUEUE.md": "tasks/HUMAN-QUEUE.md", "RESOLUTION-CLAIMS.md": "tasks/RESOLUTION-CLAIMS.md",
    "PAPER.md": "docs/PAPER.md",
}
LANE_ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}
LANE_PLACEHOLDERS = {"", "-", "n/a", "na", "none", "pending", "tbd", "unknown"}
LANE_STALE_NOTICE_SESSIONS = 1
LANE_STALE_DUE_SESSIONS = 3
LANE_ANTIWINDUP_ROWS = 10
LANE_REPORT_KEYS = ("capabilities", "intent", "progress", "available", "blocked", "next_step", "human_open_item")
DOMAIN_SYNC_ALLOWED_VALUES = {"queued", "syncing", "synced", "stale", "n/a", "na"}
LANE_AVAILABLE_ALLOWED_VALUES = {"yes", "no", "partial"}
LANE_AVAILABLE_LEGACY_MAP = {"ready": "yes", "now": "yes", "true": "yes", "false": "no"}
HIGH_RISK_LANE_PATTERNS = (
    (re.compile(r"\b(?:git[-_\s]*)?reset[-_\s]*(?:--)?hard\b", re.IGNORECASE), "reset-hard"),
    (re.compile(r"\b(?:git[-_\s]*)?clean[-_\s]*(?:-fd|-fdx|fd|fdx)\b", re.IGNORECASE), "clean-fd"),
    (re.compile(r"\b(?:push[-_\s]*--force|force[-_\s]*push)\b", re.IGNORECASE), "force-push"),
    (re.compile(r"\brm[-_\s]*-?rf\b", re.IGNORECASE), "rm-rf"),
    (re.compile(r"\b(?:branch[-_\s]*delete|delete[-_\s]*branch)\b", re.IGNORECASE), "delete-branch"),
    (re.compile(r"\bdrop[-_\s]*table\b", re.IGNORECASE), "drop-table"),
    (re.compile(r"\bkill[-_\s]*switch[-_\s]*activate\b", re.IGNORECASE), "kill-switch-activate"),
    (re.compile(r"\bshutdown\b", re.IGNORECASE), "shutdown"),
    (re.compile(r"\b(?:irreversible|destructive|wipe[-_\s]*repo|purge)\b", re.IGNORECASE), "irreversible"),
    # External-facing actions (L-366: high-risk tier — visible to others, hard to reverse)
    (re.compile(r"\b(?:create[-_\s]*pr|open[-_\s]*pr|gh[-_\s]*pr[-_\s]*create)\b", re.IGNORECASE), "create-pr"),
    (re.compile(r"\b(?:send[-_\s]*email|send[-_\s]*mail|smtp|mailto)\b", re.IGNORECASE), "send-email"),
    (re.compile(r"\b(?:post[-_\s]*to[-_\s]*external|external[-_\s]*api[-_\s]*write|publish[-_\s]*external)\b", re.IGNORECASE), "external-publish"),
)
IGNORED_UNTRACKED_RUNTIME_FILES = {"tools/check.ps1", "tools/maintenance.ps1"}
OUTCOMES_PATH = REPO_ROOT / "workspace" / "maintenance-outcomes.json"
OUTCOMES_MAX_SESSIONS = 30
LANE_GLOBAL_FOCUS_VALUES = {"global", "system", "all", "coordination", "cross-cutting", "crosscutting"}
CHECK_FOCUS_HISTORIAN_REQUIRED = {"objective", "historian"}
HISTORIAN_SELF_ANCHOR_TOKENS = ("next", "swarm-lanes", "session-log")
HISTORIAN_SURROUNDINGS_ANCHOR_TOKENS = ("frontier", "artifact", "domain", "experiment", "bulletin")
BRIDGE_FILES = ["SWARM.md", "CLAUDE.md", "AGENTS.md", "GEMINI.md",
                ".cursorrules", ".windsurfrules", ".github/copilot-instructions.md"]
KILL_SWITCH_PATH = REPO_ROOT / "tasks" / "KILL-SWITCH.md"
DOMAIN_FRONTIER_ID_PATTERN = r"F(?:-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*|\d+(?:-[A-Za-z0-9]+)?)"
DOMAIN_FRONTIER_ID_RE = re.compile(rf"\b({DOMAIN_FRONTIER_ID_PATTERN})\b", re.IGNORECASE)
DOMAIN_ACTIVE_BULLET_RE = re.compile(rf"^\s*-\s*(?:~~)?\*\*({DOMAIN_FRONTIER_ID_PATTERN})\*\*", re.IGNORECASE)
STRUCTURE_REQUIRED_PATHS = (
    "docs/SWARM-STRUCTURE.md",
    "references/README.md",
    "recordings/README.md",
)
STRUCTURE_ALLOWED_FILENAMES = {"README.md", ".gitkeep"}
STRUCTURE_ALLOWED_EXTENSIONS = {
    "references": {".md", ".json", ".txt", ".csv", ".tsv", ".bib", ".yml", ".yaml"},
    "recordings": {".md", ".json", ".txt", ".csv", ".tsv", ".log", ".yml", ".yaml"},
}
T4_TOOL_TOKEN_WARN = 5_000    # warn above this (chars//4); L-469 finding

PRIORITY_ORDER = {"URGENT": 0, "DUE": 1, "PERIODIC": 2, "NOTICE": 3}
PRIORITY_SYMBOLS = {"URGENT": "!!!", "DUE": " ! ", "PERIODIC": " ~ ", "NOTICE": " . "}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _truncated(items, n=3, sep=", ", fmt=None):
    show = items[:n]
    parts = [fmt(x) for x in show] if fmt else [str(x) for x in show]
    return sep.join(parts) + ("..." if len(items) > n else "")


def _command_exists(cmd: str) -> bool:
    return bool(shutil.which(cmd))

def _command_runs(cmd: str, args: list[str], timeout: int = 5) -> bool:
    if not _command_exists(cmd): return False
    try: return subprocess.run([cmd] + args, capture_output=True, text=True, timeout=timeout).returncode == 0
    except Exception: return False

def _python_command_runs(cmd: str) -> bool:
    return _command_runs(cmd, ["-c", "import sys"], timeout=8)

def _py_launcher_runs() -> bool:
    return _command_runs("py", ["-3", "-c", "import sys"], timeout=8)

def _select_python_command() -> str:
    for c in ("python3", "python"):
        if _python_command_runs(c): return c
    if _py_launcher_runs(): return "py -3"
    name = Path(PYTHON_EXE).name
    return name if _python_command_runs(name) else PYTHON_EXE

PYTHON_CMD = _select_python_command()

_git_cache: dict[tuple[str, ...], str] = {}

if _swarm_io is not None:
    def _git_raw(*args: str) -> str:
        return _swarm_io.git_cmd(*args)
else:
    def _git_raw(*args: str) -> str:
        try: return subprocess.run(["git", "-C", str(REPO_ROOT)] + list(args),
                                   capture_output=True, text=True, timeout=10).stdout.rstrip("\n")
        except Exception: return ""

def _git(*args: str) -> str:
    """Cached git command -- avoids 6x redundant git status calls (~2s on WSL)."""
    key = args
    if key not in _git_cache:
        _git_cache[key] = _git_raw(*args)
    return _git_cache[key]

def _status_path(line: str) -> str:
    p = (line[3:].strip() if len(line) >= 3 else line.strip())
    if " -> " in p:
        p = p.split(" -> ", 1)[1].strip()
    if p.startswith('"') and p.endswith('"') and len(p) >= 2:
        inner = p[1:-1]
        try:
            unescaped = bytes(inner, "latin1").decode("unicode_escape")
            p = unescaped.encode("latin1", "ignore").decode("utf-8", "replace")
        except Exception:
            p = inner
    p = p.replace("\\", "/").replace("\uf03a", ":")
    if re.match(r"^[A-Za-z]:[^/]", p):
        p = p[:2] + "/" + p[2:]
    return p

def _tracked_changed_paths() -> list[str]:
    status = _git("-c", "core.quotepath=false", "status", "--porcelain")
    return [_status_path(l) for l in status.splitlines() if l.rstrip() and l[:2] != "??"] if status else []

if _swarm_io is not None:
    _read = _swarm_io.read_text
    _token_count = _swarm_io.token_count
    _line_count = _swarm_io.line_count
else:
    def _read(path: Path) -> str:
        try: return path.read_text(encoding="utf-8", errors="replace")
        except Exception: return ""
    def _token_count(path: Path) -> int:
        try: return len(_read(path)) // 4
        except Exception: return 0
    def _line_count(path: Path) -> int:
        try: return len(_read(path).splitlines())
        except Exception: return 0

def _exists(path: str) -> bool:
    return (REPO_ROOT / path).exists()

def _is_wsl_mnt_repo() -> bool:
    if not sys.platform.startswith("linux"): return False
    info = (platform.release() + " " + platform.platform()).lower()
    if "microsoft" not in info: return False
    return str(REPO_ROOT).replace("\\", "/").startswith("/mnt/")

if _swarm_io is not None:
    _session_number = _swarm_io.session_number
else:
    def _session_number() -> int:
        numbers = re.findall(r"^S(\d+)", _read(REPO_ROOT / "memory" / "SESSION-LOG.md"), re.MULTILINE)
        log_max = max(int(n) for n in numbers) if numbers else 0
        try:
            git_out = subprocess.run(["git", "log", "--oneline", "-50"], capture_output=True, text=True, cwd=REPO_ROOT, timeout=5).stdout
            git_max = max((int(m) for m in re.findall(r"\[S(\d+)\]", git_out)), default=0)
        except Exception:
            git_max = 0
        return max(log_max, git_max)


def _is_lane_placeholder(value: str) -> bool:
    return (value or "").strip().lower() in LANE_PLACEHOLDERS

def _parse_lane_tags(value: str) -> dict[str, str]:
    return {k.strip().lower(): v.strip()
            for k, v in re.findall(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)", value or "")}


def _lane_has_any_tag(tags: dict[str, str], keys: tuple[str, ...]) -> bool:
    return any(key in tags for key in keys)

def _lane_high_risk_signal(row: dict[str, str], tags: dict[str, str]) -> str | None:
    haystack = " ".join(
        part for part in (
            row.get("scope_key", ""),
            row.get("notes", ""),
            tags.get("intent", ""),
            tags.get("next_step", ""),
            tags.get("action", ""),
            tags.get("plan", ""),
            tags.get("objective", ""),
        )
        if part
    )
    for pattern, label in HIGH_RISK_LANE_PATTERNS:
        if pattern.search(haystack):
            return label
    return None


_LANE_KEYS = ("date", "lane", "session", "agent", "branch", "pr", "model", "platform", "scope_key", "etc", "status", "notes")

def _parse_swarm_lane_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|") or re.match(r"^\|\s*(Date\s*\||[-: ]+\|)", line, re.IGNORECASE):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 12:
            continue
        row = dict(zip(_LANE_KEYS, parts))
        row["status"] = row["status"].upper()
        rows.append(row)
    return rows

def _normalize_frontier_id(frontier_id: str) -> str:
    return (frontier_id or "").strip().upper()

def _sorted_frontier_ids(frontier_ids: set[str]) -> list[str]:
    def _id_key(frontier_id: str) -> tuple[int, str]:
        num = re.search(r"\d+", frontier_id or "")
        return (int(num.group(0)) if num else 10 ** 9, frontier_id)

    return sorted(frontier_ids, key=_id_key)

def _extract_markdown_section(text: str, heading_pattern: str) -> str | None:
    heading = re.search(rf"^##\s*{heading_pattern}\b.*$", text, re.IGNORECASE | re.MULTILINE)
    if not heading:
        return None
    start = heading.end()
    tail = text[start:]
    next_heading = re.search(r"^##\s+\S", tail, re.MULTILINE)
    return tail[:next_heading.start()] if next_heading else tail

def _extract_domain_frontier_active_ids(frontier_text: str) -> tuple[set[str], bool]:
    section = _extract_markdown_section(frontier_text, "Active")
    if section is None:
        return set(), False

    active_ids: set[str] = set()
    for line in section.splitlines():
        if "~~" in line and "**F" in line.upper():
            continue
        match = DOMAIN_ACTIVE_BULLET_RE.match(line)
        if match:
            active_ids.add(_normalize_frontier_id(match.group(1)))
    return active_ids, True

def _parse_domain_frontier_active_count(frontier_text: str) -> int | None:
    match = re.search(r"\bActive:\s*(\d+)\b", frontier_text)
    return int(match.group(1)) if match else None

def _parse_domain_index_active_count(index_text: str) -> int | None:
    for line in index_text.splitlines():
        if not re.search(r"active frontiers?", line, re.IGNORECASE):
            continue
        match = re.search(r"\b(\d+)\s+active\b", line, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search(r":\s*(\d+)\b", line)
        if match:
            return int(match.group(1))
    return None

def _parse_domain_index_active_line_ids(index_text: str) -> set[str] | None:
    for line in index_text.splitlines():
        if not re.search(r"active frontiers?", line, re.IGNORECASE):
            continue
        paren = re.search(r"\(([^)]*)\)", line)
        if not paren:
            continue
        body = paren.group(1)
        if "\u2013" in body or "..." in body or re.search(r"\bto\b", body, re.IGNORECASE):
            continue
        ids = {_normalize_frontier_id(m.group(1)) for m in DOMAIN_FRONTIER_ID_RE.finditer(body)}
        if ids:
            return ids
    return None

def _parse_domain_index_open_ids(index_text: str) -> tuple[bool, set[str]]:
    section = _extract_markdown_section(index_text, r"What(?:['\u2019]s| is)\s+open")
    if section is None:
        return False, set()
    ids: set[str] = set()
    for line in section.splitlines():
        if "~~" in line and "**F" in line.upper():
            continue
        match = DOMAIN_ACTIVE_BULLET_RE.match(line)
        if match:
            ids.add(_normalize_frontier_id(match.group(1)))
    return True, ids

def _active_lane_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]] | None:
    lanes_text = _read(REPO_ROOT / "tasks" / "SWARM-LANES.md")
    if not lanes_text: return None
    rows = _parse_swarm_lane_rows(lanes_text)
    if not rows: return None
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        lane = row.get("lane", "").strip()
        if lane: latest[lane] = row
    active = [row for row in latest.values() if row.get("status", "").upper() in LANE_ACTIVE_STATUSES]
    return (rows, active) if active else None

def _format_frontier_id_diff(expected: set[str], actual: set[str]) -> str:
    parts = []
    if (m := _sorted_frontier_ids(expected - actual)): parts.append(f"missing {_truncated(m, 4)}")
    if (x := _sorted_frontier_ids(actual - expected)): parts.append(f"extra {_truncated(x, 4)}")
    return "; ".join(parts) if parts else "matched"

def _iter_utility_citation_files() -> list[Path]:
    def _accept(rel: str, path: Path) -> bool:
        if any(rel.startswith(prefix) for prefix in UTILITY_CITATION_SKIP_PREFIXES):
            return False
        try:
            return path.exists() and path.is_file() and path.stat().st_size <= UTILITY_CITATION_MAX_BYTES
        except Exception:
            return False

    tracked = _git("ls-files", "*.md", "*.py", "*.json")
    if tracked:
        files: list[Path] = []
        for rel in tracked.splitlines():
            rel = rel.strip().replace("\\", "/")
            if rel and _accept(rel, REPO_ROOT / rel):
                files.append(REPO_ROOT / rel)
        return files

    files: list[Path] = []
    for ext in ("*.md", "*.py", "*.json"):
        for path in REPO_ROOT.rglob(ext):
            if _accept(path.relative_to(REPO_ROOT).as_posix(), path):
                files.append(path)
    return files

def _inter_swarm_connectivity(capabilities: dict, commands: dict[str, bool]) -> dict:
    protocol_paths = ["experiments/inter-swarm/PROTOCOL.md", "memory/OPERATIONS.md"]
    protocol_state = [{"path": p, "exists": _exists(p)} for p in protocol_paths]
    missing_protocols = [s["path"] for s in protocol_state if not s["exists"]]
    inter_swarm = capabilities.get("inter_swarm", {}) if isinstance(capabilities, dict) else {}
    present = inter_swarm.get("present", 0) if isinstance(inter_swarm, dict) else 0
    total = inter_swarm.get("total", 0) if isinstance(inter_swarm, dict) else 0
    if not isinstance(present, int): present = 0
    if not isinstance(total, int): total = 0
    tooling_ready = total > 0 and present >= total
    python_ready = any(bool(commands.get(n)) for n in ("python3", "python", "py -3"))
    missing: list[str] = []
    if not tooling_ready: missing.append(f"inter_swarm_tools:{present}/{total}")
    if not python_ready: missing.append("python-command")
    missing.extend(missing_protocols)
    return {"ready": tooling_ready and python_ready and not missing_protocols,
            "tooling": {"present": present, "total": total}, "python_command_ready": python_ready,
            "protocols": protocol_state, "missing": missing}
