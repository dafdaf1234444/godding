#!/usr/bin/env python3

import importlib
import json
import hashlib
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
    """Cached git command — avoids 6× redundant git status calls (~2s on WSL)."""
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
        if "–" in body or "..." in body or re.search(r"\bto\b", body, re.IGNORECASE):
            continue
        ids = {_normalize_frontier_id(m.group(1)) for m in DOMAIN_FRONTIER_ID_RE.finditer(body)}
        if ids:
            return ids
    return None

def _parse_domain_index_open_ids(index_text: str) -> tuple[bool, set[str]]:
    section = _extract_markdown_section(index_text, r"What(?:['’]s| is)\s+open")
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

def check_unpushed() -> list[tuple[str, str]]:
    ahead = _git("rev-list", "--count", "@{upstream}..HEAD")
    if not (ahead and ahead.isdigit() and int(ahead) > 0):
        return []
    n = int(ahead)
    items = [(("URGENT" if n >= 10 else "DUE" if n >= 5 else "NOTICE"), f"{n} unpushed commits — git push")]
    if n >= 20:
        items.append(("URGENT", "Commit saturation (>=20 unpushed) — run: python3 tools/agent_swarm.py create <child> \"reduce commit backlog\" --personality commit-swarmer"))
    return items

def check_kill_switch() -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    if (os.environ.get("SWARM_STOP", "") or "").strip().lower() in {"1", "true", "yes", "on"}:
        return [("URGENT", "SWARM_STOP env var is active — halt swarm activity")]
    if not KILL_SWITCH_PATH.exists():
        fields = {}
    else:
        fields = {m.group(1).strip().lower(): m.group(2).strip()
                  for line in _read(KILL_SWITCH_PATH).splitlines()
                  for m in [re.match(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$", line)] if m}
    if not fields:
        if KILL_SWITCH_PATH.exists():
            results.append(("DUE", "Kill switch file exists but no parseable key/value fields were found"))
        return results
    missing_required = [k for k in ("status", "mode", "reason", "requested_by", "since") if not (fields.get(k, "") or "").strip()]
    if missing_required:
        return [("DUE", f"Kill switch missing required field(s): {', '.join(missing_required)}")]
    status = (fields.get("status", "") or "").strip().lower()
    if status in {"inactive", "off", "false", "0"}:
        return results
    if status not in {"active", "on", "true", "1"}:
        return [("DUE", f"Kill switch status is invalid: {fields.get('status', '')}")]
    mode = (fields.get("mode", "halt") or "halt").strip()
    if mode.lower() not in {"halt", "shutdown-request"}:
        return [("DUE", f"Kill switch mode is invalid: {mode}")]
    reason = (fields.get("reason", "unspecified") or "unspecified").strip()
    requested_by = (fields.get("requested_by", "unknown") or "unknown").strip()
    since = (fields.get("since", "") or "").strip()
    ctx = f"mode={mode}, requested_by={requested_by}, reason={reason}" + (f", since={since}" if since else "")
    results.append(("URGENT", f"Kill switch ACTIVE — {ctx}"))
    if mode.lower() == "shutdown-request":
        results.append(("NOTICE", "Shutdown request is declarative only; execute shutdown manually with explicit human confirmation"))
    return results

def check_uncommitted() -> list[tuple[str, str]]:
    results = []
    status = _git("-c", "core.quotepath=false", "status", "--porcelain")
    if not status:
        return results
    lines = [l for l in status.splitlines() if l.strip()]
    tracked = [l for l in lines if not l.startswith("??")]
    wsl_suppressed_crlf = wsl_suppressed_claude = 0

    if tracked and _is_wsl_mnt_repo():
        def _numstat_paths(*args: str) -> set[str]:
            paths: set[str] = set()
            for row in _git("diff", *args, "--numstat", "--ignore-cr-at-eol").splitlines():
                parts = row.split("\t")
                if len(parts) >= 3 and parts[-1].strip():
                    paths.add(parts[-1].strip().replace("\\", "/"))
            return paths
        substantive = _numstat_paths() | _numstat_paths("--cached")
        filtered, suppressed = [], 0
        for line in tracked:
            if any(ch in line[:2] for ch in "ADRCU") or _status_path(line) in substantive: filtered.append(line)
            else: suppressed += 1
        if suppressed: tracked = filtered; wsl_suppressed_crlf = suppressed
        filtered, wsl_hidden = [], []
        for line in tracked:
            path = _status_path(line)
            if "D" in line[:2] and not any(ch in line[:2] for ch in "ARCU") and path.startswith(".claude/"): wsl_hidden.append(path)
            else: filtered.append(line)
        if wsl_hidden: tracked = filtered; wsl_suppressed_claude = len(wsl_hidden)

    untracked_paths = [_status_path(l) for l in lines if l.startswith("??")]
    untracked_actionable = [p for p in untracked_paths if not (
        (p.startswith("workspace/notes/wiki-swarm-") and p.endswith(".md"))
        or re.fullmatch(r"memory/lessons/L-\d+\.md", p)
        or bool(re.search(r"AppData/?Local/?Temp/?tmp[^/]*parent-child/?$", p.replace("\\", "/"), re.IGNORECASE))
        or p in IGNORED_UNTRACKED_RUNTIME_FILES
    )]
    if tracked:
        portability_suffix = ""
        if _is_wsl_mnt_repo():
            filter_parts = ([f"{wsl_suppressed_crlf} CRLF-only"] if wsl_suppressed_crlf else []) + ([f"{wsl_suppressed_claude} .claude"] if wsl_suppressed_claude else [])
            if filter_parts: portability_suffix = f" (WSL filtered: {', '.join(filter_parts)})"
        results.append(("NOTICE", f"{len(tracked)} tracked file(s) uncommitted: {_truncated([_status_path(l) for l in tracked])}{portability_suffix}"))
    if untracked_actionable:
        results.append(("NOTICE", f"{len(untracked_actionable)} untracked file(s): {_truncated(untracked_actionable)} (stage if intentional, or ignore via .gitignore)"))
    return results

def check_open_challenges() -> list[tuple[str, str]]:
    results = []
    n = len(re.findall(r"\|\s*OPEN\s*\|", _read(REPO_ROOT / "beliefs" / "CHALLENGES.md"), re.IGNORECASE))
    if n: results.append(("DUE", f"{n} open challenge(s) in CHALLENGES.md"))
    pt = _read(REPO_ROOT / "beliefs" / "PHILOSOPHY.md")
    ps = pt[pt.find("## Challenges"):] if "## Challenges" in pt else ""
    n = len(re.findall(r"\|\s*open\s*\|", ps, re.IGNORECASE))
    if n: results.append(("DUE", f"{n} open PHIL challenge(s)"))
    return results

def check_human_queue() -> list[tuple[str, str]]:
    results = []
    hq_text = _read(REPO_ROOT / "tasks" / "HUMAN-QUEUE.md")
    if not hq_text: return results
    answered_pos = hq_text.find("## Answered")
    heading_matches = list(re.finditer(r"^###\s+.*$", hq_text, re.MULTILINE))
    open_items, missing_metadata = [], []
    open_by_norm: dict[str, list[str]] = {}
    answered_by_norm: dict[str, list[str]] = {}
    for i, m in enumerate(heading_matches):
        heading = m.group(0).strip()[4:].strip()
        plain = heading.replace("~~", "").strip()
        id_match = re.search(r"\b(HQ-\d+)\b", plain)
        if not id_match: continue
        hq_id = id_match.group(1)
        body = hq_text[m.end():heading_matches[i + 1].start() if i + 1 < len(heading_matches) else len(hq_text)]
        in_answered = answered_pos >= 0 and m.start() >= answered_pos
        is_struck = heading.startswith("~~")
        question = re.sub(r"\s+(?:RESOLVED|ANSWERED|CLOSED)\b.*$", "", (plain.split(":", 1)[1].strip() if ":" in plain else plain), flags=re.IGNORECASE).strip()
        q_norm = re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9\s]", " ", (question or "").lower())).strip()
        if q_norm:
            (answered_by_norm if (in_answered or is_struck) else open_by_norm).setdefault(q_norm, []).append(hq_id)
        if not in_answered and not is_struck:
            open_items.append(hq_id)
            if not re.search(r"\*\*(Asked|Date)\*\*:", body, re.IGNORECASE): missing_metadata.append(hq_id)
    if open_items: results.append(("NOTICE", f"{len(open_items)} open HUMAN-QUEUE item(s)"))
    duplicate_open = [ids for ids in open_by_norm.values() if len(ids) > 1]
    if duplicate_open: results.append(("DUE", f"Possible duplicate open HUMAN-QUEUE items: {'; '.join('/'.join(ids[:3]) for ids in duplicate_open[:3])}"))
    reasked = [f"{'/'.join(open_ids[:2])} (answered: {'/'.join(answered_by_norm[norm][:2])})" for norm, open_ids in open_by_norm.items() if norm in answered_by_norm]
    if reasked: results.append(("DUE", f"Open HUMAN-QUEUE item(s) match already answered question(s): {'; '.join(reasked[:3])}"))
    if missing_metadata: results.append(("NOTICE", f"{len(missing_metadata)} HUMAN-QUEUE item(s) missing ask metadata: {', '.join(missing_metadata[:5])}"))
    return results

def check_swarm_lanes() -> list[tuple[str, str]]:
    # Extracted to maintenance_lanes.py (DOMEX-META-S420)
    from maintenance_lanes import check_swarm_lanes as _impl
    return _impl(
        _active_lane_rows, _session_number, _parse_lane_tags, _is_lane_placeholder,
        _lane_high_risk_signal, _truncated,
        LANE_ACTIVE_STATUSES, LANE_STALE_NOTICE_SESSIONS, LANE_STALE_DUE_SESSIONS,
        LANE_ANTIWINDUP_ROWS, DOMAIN_SYNC_ALLOWED_VALUES, LANE_AVAILABLE_ALLOWED_VALUES,
        LANE_AVAILABLE_LEGACY_MAP, LANE_GLOBAL_FOCUS_VALUES,
    )

def check_swarm_coordinator() -> list[tuple[str, str]]:
    # Extracted to maintenance_lanes.py (DOMEX-META-S420)
    from maintenance_lanes import check_swarm_coordinator as _impl
    return _impl(
        _active_lane_rows, _parse_lane_tags, _lane_has_any_tag, _truncated,
        LANE_GLOBAL_FOCUS_VALUES,
    )

def check_lane_reporting_quality() -> list[tuple[str, str]]:
    # Extracted to maintenance_lanes.py (DOMEX-META-S420)
    from maintenance_lanes import check_lane_reporting_quality as _impl
    return _impl(
        _active_lane_rows, _parse_lane_tags, _is_lane_placeholder, _truncated,
        LANE_REPORT_KEYS, CHECK_FOCUS_HISTORIAN_REQUIRED,
        HISTORIAN_SELF_ANCHOR_TOKENS, HISTORIAN_SURROUNDINGS_ANCHOR_TOKENS,
    )

def check_github_swarm_intake() -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    mission_path = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "swarm-mission.yml"
    blocker_path = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "swarm-blocker.yml"
    workflow_path = REPO_ROOT / ".github" / "workflows" / "swarm-pr-intake.yml"

    missing_paths = [
        str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        for path in (mission_path, blocker_path, workflow_path)
        if not path.exists()
    ]
    if missing_paths:
        results.append(("DUE", f"GitHub swarm intake file(s) missing: {_truncated(missing_paths)}"))
        return results

    def _check_template(path: Path, label: str, required_ids: set[str]) -> None:
        ids = re.findall(r"^\s*id:\s*([A-Za-z0-9_-]+)\s*$", _read(path), re.MULTILINE)
        if not ids: results.append(("NOTICE", f"{label} has no parsed input ids")); return
        counts: dict[str, int] = {}
        for item in ids: counts[item] = counts.get(item, 0) + 1
        dupes = sorted(k for k, v in counts.items() if v > 1)
        if dupes: results.append(("DUE", f"{label} duplicate id(s): {_truncated(dupes)}"))
        missing_ids = sorted(required_ids - set(ids))
        if missing_ids: results.append(("DUE", f"{label} missing core-alignment id(s): {_truncated(missing_ids)}"))

    _check_template(mission_path, "swarm-mission template", {"objective", "expectation", "diff_signal", "scope", "acceptance", "state_sync", "available", "blocked", "human_open_item"})
    _check_template(blocker_path, "swarm-blocker template", {"blocker", "unblocking_ask", "state_sync", "available", "blocked", "human_open_item"})
    for snippet in ("tools/swarm_pr.py plan", "<!-- swarm-pr-plan -->", "Swarm Intake Plan"):
        if snippet not in _read(workflow_path): results.append(("NOTICE", f"swarm-pr-intake workflow missing marker: {snippet}"))
    return results

def check_child_bulletins() -> list[tuple[str, str]]:
    results = []
    bulletin_dir = REPO_ROOT / "experiments" / "inter-swarm" / "bulletins"
    integration_dir = REPO_ROOT / "experiments" / "integration-log"
    children_dir = REPO_ROOT / "experiments" / "children"
    if not bulletin_dir.exists(): return results
    integrated = {f.stem for f in integration_dir.glob("*.json")} if integration_dir.exists() else set()
    known_children = {d.name for d in children_dir.iterdir() if d.is_dir()} if children_dir.exists() else set()
    unprocessed, stale, external = [], [], []
    for f in bulletin_dir.glob("*.md"):
        name = f.stem
        if name not in known_children and name not in integrated: external.append(name); continue
        if name in integrated: stale.append(name)
        elif "<!-- PROCESSED" not in _read(f): unprocessed.append(name)
    if unprocessed: results.append(("DUE", f"{len(unprocessed)} unprocessed bulletin(s): {', '.join(unprocessed[:5])}"))
    if stale: results.append(("NOTICE", f"{len(stale)} stale bulletin(s): {', '.join(stale[:5])}"))
    if external: results.append(("NOTICE", f"{len(external)} external bulletin file(s) ignored: {', '.join(external[:5])}"))
    return results

def check_help_requests() -> list[tuple[str, str]]:
    bulletin_dir = REPO_ROOT / "experiments" / "inter-swarm" / "bulletins"
    if not bulletin_dir.exists(): return []
    req_re = re.compile(r"Type:\s*help-request.*?Request-ID:\s*(\S+)", re.DOTALL)
    resp_re = re.compile(r"Type:\s*help-response.*?Request-ID:\s*(\S+)", re.DOTALL)
    open_ids: set[str] = set()
    responses: set[str] = set()
    for f in bulletin_dir.glob("*.md"):
        text = _read(f)
        open_ids |= {m.group(1).strip() for m in req_re.finditer(text)}
        responses |= {m.group(1).strip() for m in resp_re.finditer(text)}
    remaining = sorted(open_ids - responses)
    if remaining:
        return [("DUE", f"{len(remaining)} open help request(s): {_truncated(remaining)}; respond with `{PYTHON_CMD} tools/bulletin.py offer-help ...`")]
    return []

def check_compaction() -> list[tuple[str, str]]:
    results = []
    idx = _line_count(REPO_ROOT / "memory" / "INDEX.md")
    if idx > 60: results.append(("DUE", f"INDEX.md is {idx} lines (>60)"))
    mandatory = sum(_line_count(REPO_ROOT / p) for p in [Path("CLAUDE.md"), Path("beliefs") / "CORE.md", Path("memory") / "INDEX.md"])
    if mandatory > 200: results.append(("DUE", f"Mandatory load is {mandatory} lines (>200)"))
    return results

def check_lessons() -> list[tuple[str, str]]:
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    if not lessons_dir.exists(): return []
    over_20 = [f.name for f in lessons_dir.glob("L-*.md") if _line_count(f) > 20]
    if over_20:
        # One item per lesson for unique claim fingerprints (L-933: trim-collision waste).
        # Sessions can claim individual trim tasks: python3 tools/claim.py claim trim:L-NNN
        return [("DUE", f"Lesson over 20 lines: {name}") for name in over_20[:5]]
    return []

T4_TOOL_TOKEN_WARN = 5_000    # warn above this (chars//4); L-469 finding

def check_t4_tool_size() -> list[tuple[str, str]]:
    """Flag T4-tools files over token ceiling (anti-cascade L-469)."""
    results = []
    tools_dir = REPO_ROOT / "tools"
    if not tools_dir.exists():
        return results
    oversized = []
    for f in sorted(tools_dir.glob("*.py")):
        try:
            tokens = len(f.read_text(encoding="utf-8", errors="replace")) // 4
            if tokens > T4_TOOL_TOKEN_WARN:
                oversized.append((f.name, tokens))
        except Exception:
            continue
    if oversized:
        names = ", ".join(f"{n}({t}t)" for n, t in sorted(oversized, key=lambda x: -x[1])[:4])
        results.append(("NOTICE", f"T4 anti-cascade: {len(oversized)} tool(s) exceed {T4_TOOL_TOKEN_WARN}t ceiling: {names}"))
    return results

def check_zombie_tools() -> list[tuple[str, str]]:
    """L-601 self-application: detect tools/*.py with no references in automation entry points."""
    results: list[tuple[str, str]] = []
    tools_dir = REPO_ROOT / "tools"
    if not tools_dir.exists():
        return results
    # Enumerate production tools (exclude tests, archive, __pycache__)
    tool_files = sorted(
        f.stem for f in tools_dir.glob("*.py")
        if not f.stem.startswith("test_") and f.stem != "__init__"
    )
    if not tool_files:
        return results
    # Scan automation entry points + protocol files for references
    entry_files = ["tools/check.sh", "tools/orient.py", "tools/maintenance.py",
                   "tools/periodics.json", "CLAUDE.md", "SWARM.md"]
    ref_text = ""
    for ef in entry_files:
        ef_path = REPO_ROOT / ef
        if ef_path.exists():
            try:
                ref_text += ef_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
    if not ref_text:
        return results
    unreferenced = [t for t in tool_files if t not in ref_text]
    if len(unreferenced) > len(tool_files) * 0.6:
        if len(unreferenced) > 30:
            results.append(("NOTICE", f"{len(unreferenced)}/{len(tool_files)} tools not referenced by automation/protocol files (L-601 zombie risk). Top: {_truncated(unreferenced, 5)}"))
    elif unreferenced:
        results.append(("NOTICE", f"{len(unreferenced)}/{len(tool_files)} tools not referenced by automation entry points. {_truncated(unreferenced, 5)}"))
    return results

def check_frontier_decay() -> list[tuple[str, str]]:
    # Extracted to maintenance_domains.py (DOMEX-META-S420)
    from maintenance_domains import check_frontier_decay as _impl
    return _impl(REPO_ROOT, _read)

def check_anxiety_zones() -> list[tuple[str, str]]:
    # Extracted to maintenance_domains.py (DOMEX-META-S420)
    from maintenance_domains import check_anxiety_zones as _impl
    return _impl(REPO_ROOT, _read, _session_number)


def check_dispatch_log() -> list[tuple[str, str]]:
    results = []
    dispatch_log = REPO_ROOT / "workspace" / "DISPATCH-LOG.md"
    if not dispatch_log.exists():
        return [("NOTICE", "workspace/DISPATCH-LOG.md missing — create with: python3 tools/dispatch_tracker.py init (F-EXP1: dispatch tracking not instrumented)")]
    current = _session_number()
    STALE_THRESHOLD = 3
    stale = []
    for match in re.finditer(r"^\|\s*(S\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|", _read(dispatch_log), re.MULTILINE):
        session_str, frontier, status, _ = (match.group(i).strip() for i in range(1, 5))
        if status.lower() != "in-progress": continue
        s_num_match = re.match(r"S(\d+)", session_str)
        if not s_num_match: continue
        age = current - int(s_num_match.group(1))
        if age > STALE_THRESHOLD:
            stale.append((session_str, frontier.strip(), age))
    if stale:
        results.append(("NOTICE", f"{len(stale)} dispatch entry(ies) stale in-progress >{STALE_THRESHOLD} sessions — may be abandoned (F-EXP1 tracking): {', '.join(f'{s}:{f}(+{a})' for s, f, a in stale[:5])}"))
    return results


def check_domain_expert_coverage() -> list[tuple[str, str]]:
    # Extracted to maintenance_domains.py (DOMEX-META-S420)
    from maintenance_domains import check_domain_expert_coverage as _impl
    return _impl(REPO_ROOT, _read)


def check_council_health() -> list[tuple[str, str]]:
    """Check council seat health via gather_council.py --json (L-894)."""
    gather = REPO_ROOT / "tools" / "gather_council.py"
    if not gather.exists():
        return []
    try:
        result = subprocess.run(
            [PYTHON_EXE, str(gather), "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=15
        )
        if result.returncode != 0:
            return [("NOTICE", f"check_council_health: gather_council.py failed — {result.stderr[:120]}")]
        data = json.loads(result.stdout)
    except Exception as e:
        return [("NOTICE", f"check_council_health: {e}")]
    health = data.get("health", "UNKNOWN")
    occupied = data.get("occupied", 0)
    total = data.get("total", 10)
    if health == "CRITICAL":
        vacant_domains = [s["domain"] for s in data.get("seats", []) if s.get("status") == "VACANT"][:3]
        hint = ", ".join(vacant_domains) if vacant_domains else "run gather_council.py --auto"
        return [("DUE", f"Council health CRITICAL ({occupied}/{total} seats occupied). Fill a seat: {hint}")]
    if health == "DEGRADED":
        return [("NOTICE", f"Council health DEGRADED ({occupied}/{total} seats occupied). "
                           "Open DOMEX lane for a top-10 domain to restore seat coverage.")]
    return []


def check_signal_staleness() -> list[tuple[str, str]]:
    """L-908: TTL for signals — flag OPEN/PARTIALLY RESOLVED signals >30 sessions old."""
    results = []
    signals_path = REPO_ROOT / "tasks" / "SIGNALS.md"
    if not signals_path.exists():
        return results
    current = _session_number()
    if current <= 0:
        return results
    stale_signals = []
    for line in _read(signals_path).splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| ID"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 11:
            continue
        sig_id, sess, status = cols[1], cols[3], cols[9]
        if status.upper() not in ("OPEN", "PARTIALLY RESOLVED"):
            continue
        m = re.search(r"S(\d+)", sess)
        if not m:
            continue
        age = current - int(m.group(1))
        if age > 30:
            stale_signals.append(f"{sig_id}(+{age}s)")
    if stale_signals:
        results.append(("DUE", f"{len(stale_signals)} signal(s) >30 sessions without resolution: {', '.join(stale_signals[:5])}. Close or escalate (L-908 TTL)."))
    return results


def check_historian_integrity() -> list[tuple[str, str]]:
    # Extracted to maintenance_domains.py (DOMEX-META-S420)
    from maintenance_domains import check_historian_integrity as _impl
    return _impl(REPO_ROOT, _read, PYTHON_EXE)


def check_periodics() -> list[tuple[str, str]]:
    results = []
    periodics_path = REPO_ROOT / "tools" / "periodics.json"
    if not periodics_path.exists():
        return results

    try: data = json.loads(periodics_path.read_text())
    except Exception as e:
        return [("NOTICE", f"periodics.json parse failed: {e}")]
    session = _session_number()
    if session <= 0: return results
    dirty = bool(_git("status", "--porcelain"))

    for item in data.get("items", []):
        item_id = item.get("id", "<unknown>")
        description = item.get("description", item_id)
        cadence = item.get("cadence_sessions", 10)
        last_raw = item.get("last_reviewed_session", 0)
        try:
            last = int(str(last_raw).lstrip("S")) if last_raw else 0
        except (ValueError, TypeError):
            last = 0
        if last > session:
            if not dirty:
                results.append(("NOTICE", f"periodics marker {item_id} S{last} > session log S{session}"))
            continue
        gap = session - last
        if gap >= cadence:
            overdue = gap - cadence
            urgency = "DUE" if overdue > cadence else "PERIODIC"
            results.append((urgency, f"[{item_id}] {description} (every ~{cadence} sessions, last: S{last})"))

    return results

def check_validator() -> list[tuple[str, str]]:
    try:
        r = subprocess.run([PYTHON_EXE, str(REPO_ROOT / "tools" / "validate_beliefs.py"), "--quick"], capture_output=True, text=True, timeout=30)
        return [("URGENT", "validate_beliefs.py FAIL — fix before other work")] if "RESULT: FAIL" in r.stdout else []
    except Exception as e:
        return [("URGENT", f"validate_beliefs.py failed to run: {e}")]

def check_version_drift() -> list[tuple[str, str]]:
    results = []
    meta_path = REPO_ROOT / ".swarm_meta.json"
    if not meta_path.exists(): return results
    try: meta = json.loads(meta_path.read_text())
    except Exception as e:
        return [("NOTICE", f".swarm_meta.json parse failed: {e}")]
    for label, fpath, key in [("CLAUDE.md", "CLAUDE.md", "claude_md_version"), ("CORE.md", "beliefs/CORE.md", "core_md_version")]:
        ver = re.search(rf"{key}:\s*([\d.]+)", _read(REPO_ROOT / fpath))
        if ver and meta.get(key) and str(ver.group(1)) != str(meta[key]):
            results.append(("URGENT", f"{label} version {ver.group(1)} != meta {meta[key]} — re-read {label}"))
    return results

def check_runtime_portability() -> list[tuple[str, str]]:
    results = []
    has_git = _command_exists("git")
    has_bash = _command_exists("bash")
    has_pwsh = _command_exists("pwsh") or _command_exists("powershell")
    has_python_alias = _python_command_runs("python3") or _python_command_runs("python") or _py_launcher_runs()
    has_bash_wrapper_pair = _exists("tools/check.sh") and _exists("tools/maintenance.sh")
    has_ps_wrapper_pair = _exists("tools/check.ps1") and _exists("tools/maintenance.ps1")
    has_bash_wrappers = has_bash and has_bash_wrapper_pair
    has_pwsh_wrappers = has_pwsh and has_ps_wrapper_pair

    if not has_git:
        results.append(("URGENT", "git not found in PATH — swarm memory/commit workflow cannot run"))
    if not has_python_alias:
        if has_bash_wrappers and has_pwsh_wrappers:
            results.append(("NOTICE", "No python alias in active shell; use wrappers (`bash tools/check.sh --quick` or `pwsh -NoProfile -File tools/check.ps1 --quick`)"))
        elif has_bash_wrappers:
            results.append(("NOTICE", "No python alias in active shell; use bash wrappers (`bash tools/check.sh --quick`, `bash tools/maintenance.sh --inventory`)"))
        else:
            results.append(("DUE", f"No python alias in PATH — use explicit interpreter: {PYTHON_EXE}"))
    if not has_bash and (_exists("workspace/genesis.sh") or _exists("tools/check.sh")):
        if has_python_alias and has_pwsh_wrappers:
            results.append(("NOTICE", "bash not found — use PowerShell wrappers (`pwsh -NoProfile -File tools/check.ps1 --quick`, `pwsh -NoProfile -File tools/maintenance.ps1 --inventory`)"))
        elif has_python_alias:
            results.append(("NOTICE", f"bash not found — use direct python entrypoints (`{PYTHON_CMD} tools/maintenance.py --quick`, `{PYTHON_CMD} tools/maintenance.py --inventory`)"))
        else:
            results.append(("DUE", "bash not found and no python alias — portable startup path is broken"))
    if has_bash and not _exists("tools/maintenance.sh"):
        results.append(("DUE", "tools/maintenance.sh missing — portable maintenance/inventory path is broken"))
    if has_pwsh and not _exists("tools/maintenance.ps1"):
        results.append(("DUE" if not has_bash else "NOTICE", "tools/maintenance.ps1 missing — PowerShell maintenance/inventory path is degraded"))

    if _is_wsl_mnt_repo():
        if not _git("status", "--porcelain"):
            results.append(("NOTICE", "WSL on /mnt/* repo: status/proxy-K may diverge from Windows runtime"))
        swarm_cmd = REPO_ROOT / ".claude" / "commands" / "swarm.md"
        if not swarm_cmd.exists():
            results.append(("DUE", ".claude/commands/swarm.md DELETED — WSL deletion bug (L-279). Fix: rm -f .claude/commands/swarm.md && git checkout HEAD -- .claude/commands/swarm.md"))
        else:
            try:
                if "# /swarm" not in swarm_cmd.read_text(encoding="utf-8"):
                    results.append(("DUE", ".claude/commands/swarm.md exists but has unexpected content — may be corrupted (WSL). Restore: python3 -c \"import os; os.remove('.claude/commands/swarm.md')\" then git show HEAD:.claude/commands/swarm.md > /tmp/s.md && python3 -c \"open('.claude/commands/swarm.md','w').write(open('/tmp/s.md').read())\""))
            except (PermissionError, OSError):
                results.append(("DUE", ".claude/commands/swarm.md inaccessible — WSL permission corruption. Fix: python3 -c \"import os; os.remove('.claude/commands/swarm.md')\" then restore from git show HEAD:.claude/commands/swarm.md"))

    bridges = BRIDGE_FILES
    missing_bridges = [p for p in bridges if not _exists(p)]
    if missing_bridges:
        level = "URGENT" if "SWARM.md" in missing_bridges else "DUE"
        sample = ", ".join(missing_bridges[:3])
        results.append((level, f"{len(missing_bridges)} missing bridge file(s): {sample}"))

    swarm_ref_re = re.compile(r"\bswarm\.md\b", re.IGNORECASE)
    swarm_signal_re = re.compile(r"\bswarm signaling\b", re.IGNORECASE)
    min_swarmed_re = re.compile(r"Minimum Swarmed Cycle", re.IGNORECASE)
    no_ref, no_signal, no_min_swarmed = [], [], []
    for path in bridges:
        if path == "SWARM.md" or path in missing_bridges: continue
        content = _read(REPO_ROOT / path)
        if not swarm_ref_re.search(content): no_ref.append(path)
        if not swarm_signal_re.search(content): no_signal.append(path)
        if not min_swarmed_re.search(content): no_min_swarmed.append(path)
    if no_ref:
        results.append(("DUE", f"{len(no_ref)} bridge file(s) missing SWARM.md protocol reference: {', '.join(no_ref[:3])}"))
    if "SWARM.md" not in missing_bridges and not swarm_signal_re.search(_read(REPO_ROOT / "SWARM.md")):
        results.append(("DUE", "SWARM.md missing explicit swarm signaling rule"))
    if no_signal:
        results.append(("DUE", f"{len(no_signal)} bridge file(s) missing swarm signaling guidance: {', '.join(no_signal[:3])}"))
    if no_min_swarmed:
        results.append(("DUE", f"{len(no_min_swarmed)} bridge file(s) missing 'Minimum Swarmed Cycle' section (F-GOV2, L-351): {', '.join(no_min_swarmed[:3])}"))

    return results

def check_commit_hooks() -> list[tuple[str, str]]:
    results = []
    git_dir = REPO_ROOT / ".git"
    if not git_dir.exists(): return results
    hooks_dir = git_dir / "hooks"
    if not hooks_dir.exists(): return [("NOTICE", ".git/hooks missing — commit quality hooks unavailable")]
    expected = [("pre-commit", "tools/pre-commit.hook"), ("commit-msg", "tools/commit-msg.hook")]
    missing_tpl = [tpl for _, tpl in expected if not _exists(tpl)]
    if missing_tpl: return [("DUE", f"Hook template(s) missing: {', '.join(missing_tpl[:3])}")]
    missing_inst, drifted = [], []
    for hook_name, tpl_rel in expected:
        tpl_text = _read(REPO_ROOT / tpl_rel).replace("\r\n", "\n").strip()
        inst_path = hooks_dir / hook_name
        if not inst_path.exists(): missing_inst.append(hook_name); continue
        if tpl_text != _read(inst_path).replace("\r\n", "\n").strip(): drifted.append(hook_name)
    if missing_inst: results.append(("DUE", f"Missing hook(s): {', '.join(missing_inst)} — run: bash tools/install-hooks.sh"))
    if drifted: results.append(("NOTICE", f"Hook drift detected ({', '.join(drifted)}) — run: bash tools/install-hooks.sh"))
    return results

def check_cross_references() -> list[tuple[str, str]]:
    results = []
    index_text = _read(REPO_ROOT / "memory" / "INDEX.md")
    struct_match = re.search(r"```\n(.*?)```", index_text, re.DOTALL)
    if not struct_match: return results
    broken = [m.group(1).rstrip("/") for line in struct_match.group(1).splitlines()
              for m in [re.match(r"^(\w[\w-]*/)", line.strip())] if m and not (REPO_ROOT / m.group(1).rstrip("/")).exists()]
    if broken: results.append(("DUE", f"{len(broken)} broken directory(s) in INDEX.md structure: {', '.join(broken[:3])}"))

    lessons_dir = REPO_ROOT / "memory" / "lessons"
    if lessons_dir.exists():
        lesson_paths = list(lessons_dir.glob("L-*.md"))
        actual = len(lesson_paths)
        tracked_raw = _git("ls-files", "--", "memory/lessons")
        tracked_lessons = [l.strip() for l in (tracked_raw or "").splitlines() if re.fullmatch(r"memory/lessons/L-\d+\.md", l.strip())]
        tracked = len(tracked_lessons) if tracked_lessons else actual
        tracked_set = {p.replace("\\", "/") for p in tracked_lessons}
        untracked_names = sorted(p.name for p in lesson_paths if p.relative_to(REPO_ROOT).as_posix() not in tracked_set)
        if untracked_names and len(untracked_names) == actual and tracked_lessons:
            if {Path(p).name for p in tracked_lessons} == {p.name for p in lesson_paths}:
                untracked_names = []
        untracked = len(untracked_names)
        count_match = re.search(r"\*\*(\d+) lessons\*\*", index_text)
        claimed = int(count_match.group(1)) if count_match else None
        if claimed is not None and tracked != claimed and not (untracked > 0 and claimed == actual):
            results.append(("NOTICE", f"INDEX lessons {claimed} != tracked {tracked}"))
        if untracked:
            note = "(INDEX includes drafts; tracked count excludes them)" if (claimed == actual if claimed is not None else False) else "(not counted in tracked lesson total)"
            results.append(("NOTICE", f"{untracked} untracked lesson draft(s): {_truncated(untracked_names)} {note}"))

    principles_text = _read(REPO_ROOT / "memory" / "PRINCIPLES.md")
    all_pids, superseded_pids = _active_principle_ids(principles_text)
    actual_active_p = len(all_pids - superseded_pids)
    p_hm = re.search(r"(\d+)\s+(?:live\s+)?principles", principles_text)
    idx_pm = re.search(r"\*\*(\d+) principles\*\*", index_text)
    if p_hm and int(p_hm.group(1)) != actual_active_p:
        results.append(("NOTICE", f"PRINCIPLES header {p_hm.group(1)} != ID-count {actual_active_p}"))
    if idx_pm and int(idx_pm.group(1)) != actual_active_p:
        results.append(("NOTICE", f"INDEX principles {idx_pm.group(1)} != ID-count {actual_active_p}"))

    frontier_text = _read(REPO_ROOT / "tasks" / "FRONTIER.md")
    idx_f_match = re.search(r"\*\*(\d+) frontier questions\*\*", index_text)
    try:
        from swarm_parse import active_frontier_ids as _afi
        actual_frontier = len(_afi(frontier_text))
    except Exception:
        actual_frontier = len(re.findall(r"^- \*\*F\d+\*\*:", frontier_text, re.MULTILINE)) + len(re.findall(r"^- \*\*F-[A-Z][A-Z0-9]*\d*\*\*:", frontier_text, re.MULTILINE))
    if idx_f_match and int(idx_f_match.group(1)) != actual_frontier:
        results.append(("NOTICE", f"INDEX frontier count {idx_f_match.group(1)} != active {actual_frontier}"))
    return results

def check_domain_frontier_consistency() -> list[tuple[str, str]]:
    # Extracted to maintenance_domains.py (DOMEX-META-S420)
    from maintenance_domains import check_domain_frontier_consistency as _impl
    return _impl(
        REPO_ROOT, _read, _truncated,
        _extract_domain_frontier_active_ids, _parse_domain_frontier_active_count,
        _parse_domain_index_active_count, _parse_domain_index_active_line_ids,
        _parse_domain_index_open_ids, _format_frontier_id_diff,
    )

def check_readme_snapshot_drift() -> list[tuple[str, str]]:
    results = []
    readme_text = _read(REPO_ROOT / "README.md")
    if not readme_text: return results
    session = _session_number()
    index_text = _read(REPO_ROOT / "memory" / "INDEX.md")
    m = re.search(r"^Updated:\s*\d{4}-\d{2}-\d{2}\s*\|\s*Sessions:\s*(\d+)\b", index_text, re.MULTILINE)
    index_session = int(m.group(1)) if m else 0
    reference_session = index_session or session
    snap_match = re.search(r"^##\s+Current State Snapshot\s*\([^)]+,\s*S(\d+)\)", readme_text, re.MULTILINE)
    if not snap_match:
        results.append(("NOTICE", "README missing session-stamped 'Current State Snapshot' header")); return results
    snap_session = int(snap_match.group(1))
    if reference_session > 0 and snap_session != reference_session:
        delta = reference_session - snap_session
        target_label = f"INDEX S{reference_session}" if index_session else f"SESSION-LOG S{reference_session}"
        results.append(("DUE" if abs(delta) > 3 else "NOTICE", f"README snapshot session S{snap_session} is {abs(delta)} session(s) {'behind' if delta > 0 else 'ahead'} of {target_label}"))
    scale_match = re.search(r"-\s*Swarm scale:\s*(\d+)\s*lessons,\s*(\d+)\s*principles,\s*(\d+)\s*beliefs,\s*(\d+)\s*active frontier questions\.", readme_text)
    if not scale_match:
        results.append(("NOTICE", "README 'Swarm scale' line missing or unparsable")); return results
    l_m = re.search(r"\*\*(\d+) lessons\*\*", index_text)
    p_m = re.search(r"\*\*(\d+) principles\*\*", index_text)
    b_m = re.search(r"\*\*(\d+) beliefs\*\*", index_text)
    f_m = re.search(r"\*\*(\d+) frontier questions\*\*", index_text)
    if not (l_m and p_m and b_m and f_m): return results
    readme_scale = tuple(int(scale_match.group(i)) for i in range(1, 5))
    index_scale = (int(l_m.group(1)), int(p_m.group(1)), int(b_m.group(1)), int(f_m.group(1)))
    if readme_scale != index_scale:
        results.append(("NOTICE", f"README swarm scale drift vs INDEX (README L/P/B/F={readme_scale[0]}/{readme_scale[1]}/{readme_scale[2]}/{readme_scale[3]}, INDEX={index_scale[0]}/{index_scale[1]}/{index_scale[2]}/{index_scale[3]})"))
    if "tools/orient.py" not in readme_text:
        results.append(("NOTICE", "README onboarding missing orient.py fast-path reference"))
    return results

def check_count_drift() -> list[tuple[str, str]]:
    """Verify INDEX.md L/P/B/F header counts match filesystem reality. (L-887, L-216)
    Numerical claims drift at ~0.7%/session; auto-count verification catches this."""
    results = []
    index_text = _read(REPO_ROOT / "memory" / "INDEX.md")
    if not index_text:
        return results

    # Parse stated counts from INDEX.md
    l_m = re.search(r"\*\*(\d+) lessons\*\*", index_text)
    p_m = re.search(r"\*\*(\d+) principles\*\*", index_text)
    b_m = re.search(r"\*\*(\d+) beliefs\*\*", index_text)
    f_m = re.search(r"\*\*(\d+) frontiers?\*\*", index_text)
    if not (l_m and p_m and b_m and f_m):
        return results  # Can't parse — don't false-alarm

    stated = {
        "L": int(l_m.group(1)),
        "P": int(p_m.group(1)),
        "B": int(b_m.group(1)),
        "F": int(f_m.group(1)),
    }

    # Count actual values from filesystem
    tracked_lessons = _git("ls-files", "memory/lessons/").splitlines()
    actual_L = sum(1 for f in tracked_lessons if re.match(r"memory/lessons/L-\d+\.md$", f))

    principles_text = _read(REPO_ROOT / "memory" / "PRINCIPLES.md")
    # Count non-superseded P-NNN entries (active principles)
    all_p = set(re.findall(r"^### P-(\d+):", principles_text, re.MULTILINE))
    superseded_p = set(re.findall(r"^<!--\s*SUPERSEDED.*?P-(\d+)", principles_text, re.MULTILINE))
    actual_P = len(all_p - superseded_p)

    deps_text = _read(REPO_ROOT / "beliefs" / "DEPS.md")
    actual_B = len(set(re.findall(r"^### B[-\w]+:", deps_text, re.MULTILINE)))

    frontier_text = _read(REPO_ROOT / "tasks" / "FRONTIER.md")
    # Active frontiers: sections starting with ## F-NNN (not archived/resolved)
    active_frontiers = re.findall(r"^## (F-\w+)", frontier_text, re.MULTILINE)
    actual_F = len(active_frontiers)

    drifts = []
    for key, stated_val, actual_val in [
        ("L", stated["L"], actual_L),
        ("P", stated["P"], actual_P),
        ("B", stated["B"], actual_B),
        ("F", stated["F"], actual_F),
    ]:
        if actual_val > 0 and stated_val != actual_val:
            drifts.append(f"{key}: stated {stated_val} vs actual {actual_val}")

    if drifts:
        delta = sum(abs(stated[k[0]] - a) for k, a in [
            ("L", actual_L), ("P", actual_P), ("B", actual_B), ("F", actual_F)
        ])
        level = "DUE" if delta >= 2 else "NOTICE"
        results.append((level, f"Count drift in INDEX.md ({'; '.join(drifts)}) — run python3 tools/sync_state.py"))
    return results

def check_structure_layout() -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    missing_required = [path for path in STRUCTURE_REQUIRED_PATHS if not _exists(path)]
    if missing_required:
        results.append(("DUE", f"Structure policy files missing: {_truncated(missing_required, 5)}"))
    for folder, allowed_exts in STRUCTURE_ALLOWED_EXTENSIONS.items():
        folder_path = REPO_ROOT / folder
        if not folder_path.exists():
            results.append(("DUE", f"Missing required structure folder: {folder}/")); continue
        disallowed = [path.relative_to(REPO_ROOT).as_posix() for path in folder_path.rglob("*")
            if path.is_file() and path.name not in STRUCTURE_ALLOWED_FILENAMES and path.suffix.lower() not in allowed_exts]
        if disallowed:
            results.append(("DUE", f"{folder}/ has disallowed file types: {_truncated(disallowed, 5)} (allowed: {', '.join(sorted(allowed_exts))})"))
    return results

def check_frontier_registry() -> list[tuple[str, str]]:
    # Extracted to maintenance_domains.py (DOMEX-META-S420)
    from maintenance_domains import check_frontier_registry as _impl
    return _impl(REPO_ROOT, _read, _truncated)

def check_handoff_staleness() -> list[tuple[str, str]]:
    next_text = _read(REPO_ROOT / "tasks" / "NEXT.md")
    session = _session_number()
    if not next_text or session <= 0: return []
    stale = []
    for m in re.finditer(r"\(added S(\d+)\)", next_text):
        age = session - int(m.group(1))
        if age > 3:
            line_start = next_text.rfind("\n", 0, m.start()) + 1
            line_end = next_text.find("\n", m.end())
            line = next_text[line_start:line_end if line_end > 0 else len(next_text)].strip()
            item_match = re.search(r"\*\*(.+?)\*\*", line)
            stale.append(f"{item_match.group(1) if item_match else line[:50]} (age: {age})")
    if stale:
        return [("DUE", f"{len(stale)} stale handoff(s) in NEXT.md: {'; '.join(stale[:3])}")]
    return []

def check_state_header_sync() -> list[tuple[str, str]]:
    results = []
    session = _session_number()
    if session <= 0: return results
    values: dict[str, int] = {}
    parse_fail = []
    checks = [
        ("NEXT", _read(REPO_ROOT / "tasks" / "NEXT.md"), r"^Updated:\s*\d{4}-\d{2}-\d{2}\s+S(\d+)\b"),
        ("INDEX", _read(REPO_ROOT / "memory" / "INDEX.md"), r"^Updated:\s*\d{4}-\d{2}-\d{2}\s*\|\s*Sessions:\s*(\d+)\b"),
        ("FRONTIER", _read(REPO_ROOT / "tasks" / "FRONTIER.md"), r"last\s+updated\s*:\s*\d{4}-\d{2}-\d{2}\s*(?:\|\s*)?S(\d+)\b"),
    ]
    for name, text, pat in checks:
        m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
        if m: values[name] = int(m.group(1))
        else: parse_fail.append(name)
    if parse_fail: results.append(("NOTICE", f"State header parse failed: {', '.join(parse_fail)}"))
    dirty = bool(_git("status", "--porcelain"))
    behind = [f"{name}:S{val}" for name, val in values.items() if val < session]
    ahead = [f"{name}:S{val}" for name, val in values.items() if val > session]
    if behind: results.append(("NOTICE", f"State header drift vs SESSION-LOG S{session}: {', '.join(behind)}"))
    if ahead and not dirty: results.append(("NOTICE", f"State header ahead of SESSION-LOG S{session}: {', '.join(ahead)}"))
    return results

def check_mission_constraints() -> list[tuple[str, str]]:
    results = []
    frontier_text = _read(REPO_ROOT / "tasks" / "FRONTIER.md")
    if not re.search(r"^- \*\*F119\*\*:", frontier_text, re.MULTILINE):
        results.append(("DUE", "F119 missing from tasks/FRONTIER.md (mission-constraint swarming)"))
    next_text = _read(REPO_ROOT / "tasks" / "NEXT.md")
    if "F119" not in next_text:
        results.append(("NOTICE", "F119 not tracked in tasks/NEXT.md priorities"))
    invariants_text = _read(REPO_ROOT / "beliefs" / "INVARIANTS.md")
    invariant_ids = re.findall(r"^##\s+(I\d+)\b", invariants_text, re.MULTILINE)
    id_counts: dict[str, int] = {}
    for inv_id in invariant_ids: id_counts[inv_id] = id_counts.get(inv_id, 0) + 1
    duplicate_ids = sorted(inv_id for inv_id, count in id_counts.items() if count > 1)
    if duplicate_ids:
        results.append(("DUE", f"INVARIANTS duplicate ID(s): {_truncated(duplicate_ids, 5)}"))
    mission_rows = {
        "I9": ("mission safety (do no harm)", "MC-SAFE"),
        "I10": ("mission portability (work everywhere)", "MC-PORT"),
        "I11": ("mission learning quality (improve knowledge)", "MC-LEARN"),
        "I12": ("mission continuity (stay connected)", "MC-CONN"),
        "I13": ("mission safety: cross-substrate safe entry", "MC-XSUB"),
    }
    missing_invariants = [f"{inv_id} ({label})" for inv_id, (label, tag) in mission_rows.items()
        if not re.search(rf"^##\s+{re.escape(inv_id)}\b.*\[{re.escape(tag)}\]", invariants_text, re.MULTILINE)]
    if missing_invariants:
        results.append(("DUE", f"F119 mission invariants missing: {_truncated(missing_invariants)}"))
    check_sh = _read(REPO_ROOT / "tools" / "check.sh")
    missing_pm = [m for m in ("choose_python()", "python3", "python", "py -3") if m not in check_sh]
    if missing_pm:
        results.append(("NOTICE", f"F119 portability fallback drift in tools/check.sh: missing {', '.join(missing_pm)}"))

    has_python_alias = _python_command_runs("python3") or _python_command_runs("python") or _py_launcher_runs()
    inter_swarm_tools = all(_exists(p) for p in ("tools/bulletin.py", "tools/merge_back.py", "tools/propagate_challenges.py"))
    if not has_python_alias:
        has_bash = _command_exists("bash")
        has_pwsh = _command_exists("pwsh") or _command_exists("powershell")
        fallback_ready = ((has_bash and _exists("tools/check.sh") and _exists("tools/maintenance.sh"))
                          or (has_pwsh and _exists("tools/check.ps1") and _exists("tools/maintenance.ps1")))
        if not fallback_ready:
            results.append(("DUE", "F119 degraded runtime continuity broken: no python alias and no wrapper path (`tools/check.sh` + `tools/maintenance.sh` or `tools/check.ps1` + `tools/maintenance.ps1`)"))
    if not inter_swarm_tools:
        missing_artifacts = [p for p in ("tasks/PR-QUEUE.json", "tasks/SWARM-LANES.md") if not _exists(p)]
        if missing_artifacts:
            results.append(("DUE", f"F119 offline continuity artifacts missing: {_truncated(missing_artifacts)}"))

    tracked_paths = _tracked_changed_paths()
    if tracked_paths:
        knowledge_state_paths = {"tasks/NEXT.md", "memory/SESSION-LOG.md", "memory/INDEX.md",
            "tasks/FRONTIER.md", "memory/PRINCIPLES.md", "beliefs/CHALLENGES.md", "memory/HEALTH.md"}
        # Exclude operational cache/log files — they accumulate between commits and are not session work
        _cache_pats = (r"experiments/compact-.*-cache\.json", r"experiments/proxy-k-log\.json",
                       r"workspace/maintenance-outcomes\.json", r"domains/.*/SESSION-TRIGGER\.md")
        substantive = [p for p in tracked_paths if not any(re.fullmatch(cp, p) for cp in _cache_pats)]
        has_lesson_delta = any(re.fullmatch(r"memory/lessons/L-\d+\.md", p) for p in substantive)
        if len(substantive) >= 5 and not (has_lesson_delta or any(p in knowledge_state_paths for p in substantive)):
            results.append(("DUE", "F119 learning-quality gap: tracked deltas without knowledge-state update (NEXT/SESSION-LOG/INDEX/FRONTIER/PRINCIPLES/lessons)"))

    # I13 MC-XSUB: cross-substrate safety enforcement
    if not _exists("tools/substrate_detect.py"):
        results.append(("DUE", "F119 I13 cross-substrate safety: substrate_detect.py missing — foreign-repo detection unavailable"))
    else:
        sd_text = _read(REPO_ROOT / "tools" / "substrate_detect.py")
        if "SWARM.md" not in sd_text and "is_swarm" not in sd_text:
            results.append(("NOTICE", "F119 I13 cross-substrate safety: substrate_detect.py may not check for SWARM.md presence"))
    if not re.search(r"^##\s+I13\b", invariants_text, re.MULTILINE):
        results.append(("DUE", "F119 I13 (MC-XSUB) missing from beliefs/INVARIANTS.md"))

    return results

def check_session_log_integrity() -> list[tuple[str, str]]:
    results = []
    text = _read(REPO_ROOT / "memory" / "SESSION-LOG.md")
    if not text: return results
    control_hits = [(ln, ord(ch)) for ln, raw in enumerate(text.splitlines(), 1) for ch in raw if ord(ch) < 32 and ch != "\t"]
    if control_hits:
        results.append(("NOTICE", f"SESSION-LOG contains control character(s): {_truncated(control_hits, 5, fmt=lambda x: f'L{x[0]}:0x{x[1]:02x}')}"))
    rows = []
    for raw in text.splitlines():
        m = re.match(r"^S(\d+)\b", raw)
        if m: rows.append((int(m.group(1)), re.sub(r"\s+", " ", raw.strip())))
    if not rows: return results
    dup_counts: dict[str, int] = {}
    for _, row in rows: dup_counts[row] = dup_counts.get(row, 0) + 1
    dup_rows = [(row, n) for row, n in dup_counts.items() if n > 1]
    if dup_rows:
        results.append(("NOTICE", f"SESSION-LOG exact duplicate row(s): {_truncated(dup_rows, fmt=lambda x: f'{x[0][:40]}... x{x[1]}')}"))
    recent_window = 40
    recent_rows = rows[-recent_window:]
    historical_ids = {sid for sid, _ in rows[:-recent_window]} if len(rows) > recent_window else set()
    non_monotonic = []
    for i in range(1, len(recent_rows)):
        prev_sid, sid = recent_rows[i - 1][0], recent_rows[i][0]
        if sid < prev_sid and not (sid in historical_ids or (prev_sid - sid) == 1):
            non_monotonic.append((prev_sid, sid))
    if non_monotonic:
        results.append(("NOTICE", f"SESSION-LOG recent non-monotonic order: {_truncated(non_monotonic, 5, fmt=lambda x: f'S{x[0]}->S{x[1]}')}"))
    return results

def check_paper_accuracy() -> list[tuple[str, str]]:
    return run_paper_drift_check(REPO_ROOT, _session_number())

def check_utility() -> list[tuple[str, str]]:
    principles_text = _read(REPO_ROOT / "memory" / "PRINCIPLES.md")
    if not principles_text: return []
    active_ids = _active_principle_ids(principles_text)[0] - _active_principle_ids(principles_text)[1]
    # Use git grep for 22x faster citation scan (0.5s vs 11s reading 2200+ files)
    cited: set[int] = set()
    grep_out = _git("grep", "-ohP", r"\bP-\d+\b", "--", "*.md", "*.py", "*.json")
    if grep_out:
        for m in PRINCIPLE_ID_RE.finditer(grep_out):
            cited.add(int(m.group(1)))
    # Remove self-citations from PRINCIPLES.md (active_ids are defined there)
    uncited = sorted(active_ids - cited)
    if uncited:
        return [("NOTICE", f"{len(uncited)} active principle(s) with 0 citations: {_truncated(uncited, 5, fmt=lambda x: f'P-{x}')}")]
    return []

def check_dark_matter() -> list[tuple[str, str]]:
    """L-581 (Sh=9): dark matter PID control — orphan lessons 15-25% optimal.

    Dark matter = lessons with no outbound Cites: header (no explicit citations).
    Above 40%: knowledge graph fragmenting — run integration session.
    Below 15%: citations dense — diversity being eroded, pause citation sprints.
    15-25%: optimal range per L-581 F-META7 operational evidence.
    """
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    if not lessons_dir.exists():
        return []
    total = 0
    no_cites = 0
    for f in lessons_dir.glob("L-*.md"):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        total += 1
        if not re.search(r"^Cites:\s*\S", content, re.MULTILINE):
            no_cites += 1
    if total == 0:
        return []
    pct = no_cites / total * 100
    if pct > 40.0:
        return [("URGENT", f"dark matter {pct:.1f}% > 40% threshold (L-581): "
                 f"{no_cites}/{total} lessons have no outbound citations — run integration session")]
    if pct < 15.0:
        return [("NOTICE", f"dark matter {pct:.1f}% < 15% threshold (L-581): "
                 f"citations dense ({no_cites}/{total} orphans) — consider pausing citation sprints")]
    return [("NOTICE", f"dark matter {pct:.1f}% ({no_cites}/{total} lessons have no outbound citations) "
             f"— within 15-40% safe zone (L-581; optimal 15-25%)")]


def check_meta_tooler_gap() -> list[tuple[str, str]]:
    """L-896: When >20 tools are unreferenced by automation, surface meta-tooler DUE."""
    tools_dir = REPO_ROOT / "tools"
    if not tools_dir.exists():
        return []
    tool_files = sorted(
        f.stem for f in tools_dir.glob("*.py")
        if not f.stem.startswith("test_") and f.stem != "__init__"
    )
    if not tool_files:
        return []
    entry_files = ["tools/check.sh", "tools/orient.py", "tools/maintenance.py",
                   "tools/periodics.json", "CLAUDE.md", "SWARM.md"]
    ref_text = ""
    for ef in entry_files:
        ef_path = REPO_ROOT / ef
        if ef_path.exists():
            try:
                ref_text += ef_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
    unreferenced = [t for t in tool_files if t not in ref_text]
    # Threshold: >40% unreferenced signals wiring gap; below that is normal for
    # mature swarms with many standalone user-invocable tools (S408 audit: 28/80).
    threshold = max(20, int(len(tool_files) * 0.4))
    if len(unreferenced) <= threshold:
        return []
    # Check if a meta-tooler lane is already active
    lanes_path = REPO_ROOT / "tasks" / "SWARM-LANES.md"
    if lanes_path.exists():
        lanes_text = _read(lanes_path)
        if re.search(r"meta.tooler.*(?:ACTIVE|CLAIMED|READY)", lanes_text, re.IGNORECASE):
            return []
    return [("DUE", f"{len(unreferenced)} tools unreferenced by automation (>{threshold} threshold, L-896) "
             f"— open a meta-tooler DOMEX lane to wire or archive")]


def check_level_quota() -> list[tuple[str, str]]:
    """L-895: Emit NOTICE if last 5 sessions lack any L3+ (strategy/architecture) lesson.
    Goodhart's law: measurement infra crowds out strategic work — enforce 1-in-5 L3+.
    L3+ proxy: explicit level tag L3-L5, OR (Sharpe>=9 AND strategic keyword).
    """
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    if not lessons_dir.exists():
        return []

    strategic_keywords = [
        "architecture", "paradigm", "strategy", "governance", "reframe",
        "redesign", "structural design", "L3+", "level=L3", "level=L4", "level=L5",
    ]

    def _is_l3plus(text: str) -> bool:
        if re.search(r"[Ll]evel[=:\s]+[Ll][3-5]", text):
            return True
        high_sharpe = bool(re.search(r"Sharpe:\s*(9|10)\b", text))
        text_lower = text.lower()
        return high_sharpe and any(k.lower() in text_lower for k in strategic_keywords)

    session_has_l3: dict[int, bool] = {}
    for lf in sorted(lessons_dir.glob("L-*.md")):
        try:
            text = lf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = re.search(r"Session:\s*S(\d+)", text)
        if not m:
            continue
        sess = int(m.group(1))
        if not session_has_l3.get(sess):
            session_has_l3[sess] = _is_l3plus(text)

    if not session_has_l3:
        return []

    recent_sessions = sorted(session_has_l3.keys())[-5:]
    if len(recent_sessions) < 5:
        return []
    l3_count = sum(1 for s in recent_sessions if session_has_l3[s])
    if l3_count == 0:
        return [("DUE", f"Level quota: 0/{len(recent_sessions)} recent sessions had L3+ "
                 "(strategy/architecture/paradigm) work (L-895, F-LEVEL1). Produce L3+ "
                 "lesson this session — add level=L3/L4/L5 tag in Session: header.")]
    return []


def check_proxy_k_drift() -> list[tuple[str, str]]:
    results = []
    log_path = REPO_ROOT / "experiments" / "proxy-k-log.json"
    if not log_path.exists():
        return results

    try:
        entries = json.loads(_read(log_path))
    except Exception as e:
        return [("NOTICE", f"proxy-k-log.json parse failed: {e}")]

    if len(entries) < 2:
        return results

    tiers = {
        "T0-mandatory": ["SWARM.md", "CLAUDE.md", "beliefs/CORE.md", "memory/INDEX.md"],
        "T1-identity": ["beliefs/PHILOSOPHY.md", "beliefs/DEPS.md", "beliefs/INVARIANTS.md"],
        "T2-protocols": ["memory/DISTILL.md", "memory/VERIFY.md", "memory/OPERATIONS.md", "beliefs/CONFLICTS.md"],
        "T3-knowledge": ["memory/PRINCIPLES.md", "tasks/FRONTIER.md"],
        "T4-tools": ["tools/validate_beliefs.py", "tools/maintenance.py", "tools/paper_drift.py", "tools/swarm_parse.py"],
    }
    schema_payload = json.dumps(tiers, sort_keys=True, separators=(",", ":")).encode("utf-8")
    current_schema = hashlib.sha256(schema_payload).hexdigest()
    schema_entries = [e for e in entries if e.get("tier_schema") == current_schema]
    clean_schema_entries = [e for e in schema_entries if not e.get("dirty_tree")]
    baseline = clean_schema_entries if len(clean_schema_entries) >= 2 else schema_entries
    if len(baseline) < 2:
        n = len(schema_entries)
        results.append(("NOTICE",
            f"Proxy K schema baseline unavailable ({n} matching snapshot{'s' if n != 1 else ''}); run clean snapshots: {PYTHON_CMD} tools/proxy_k.py --save"))
        return results

    floor_idx = 0
    for i in range(1, len(baseline)):
        if baseline[i]["total"] < baseline[i - 1]["total"]:
            floor_idx = i

    floor_entry = baseline[floor_idx]
    floor = floor_entry["total"]
    if floor <= 0:
        return results

    # If the historical-minimum floor is stale (>= 8 sessions ago) and a more
    # recent clean baseline exists, use that as the floor to acknowledge
    # intentional tool growth without triggering false URGENT compaction. (L-273)
    _cur_s = _session_number()
    _floor_s = int(floor_entry.get("session", 0) or 0)
    if len(clean_schema_entries) >= 2 and _floor_s > 0 and _cur_s > 0 and (_cur_s - _floor_s) >= 8:
        _newer = [e for e in clean_schema_entries if int(e.get("session", 0) or 0) > _floor_s]
        if _newer:
            _latest_clean = max(_newer, key=lambda e: int(e.get("session", 0) or 0))
            if _latest_clean["total"] > floor:
                floor_entry = _latest_clean
                floor = _latest_clean["total"]

    # If floor is very stale (>50 sessions), check dirty entries for more
    # recent post-compaction baselines (where total decreased from prior).
    # Prevents false URGENT signals from legitimate tool growth. (L-550, L-555)
    _floor_s_post = int(floor_entry.get("session", 0) or 0)
    if _cur_s > 0 and _floor_s_post > 0 and (_cur_s - _floor_s_post) > 50:
        for i in range(len(schema_entries) - 1, 0, -1):
            if schema_entries[i]["total"] < schema_entries[i - 1]["total"]:
                _df = schema_entries[i]
                _df_total = _df["total"]
                _df_s = int(_df.get("session", 0) or 0)
                if _df_total > floor and _df_s > _floor_s_post:
                    floor_entry = _df
                    floor = _df_total
                break

    live_tiers: dict[str, int] = {}
    live_total = 0
    for tier, files in tiers.items():
        tier_total = sum(_token_count(REPO_ROOT / f) for f in files)
        live_tiers[tier] = tier_total
        live_total += tier_total

    latest_entry = entries[-1]
    latest_logged = latest_entry["total"]
    latest_session = int(latest_entry.get("session", 0) or 0)
    latest_marked_dirty = bool(latest_entry.get("dirty_tree", False))
    floor_session = int(floor_entry.get("session", 0) or 0)
    current_session = _session_number()
    logged_drift = (latest_logged - floor) / floor
    live_drift = (live_total - floor) / floor
    dirty = bool(_git("status", "--porcelain"))
    stale_clean_baseline = dirty and floor_session > 0 and current_session > 0 and (current_session - floor_session) >= 8

    likely_dirty_logged = latest_marked_dirty
    if not likely_dirty_logged and dirty and latest_session > 0 and current_session > 0:
        if latest_session >= max(0, current_session - 2) and abs(latest_logged - live_total) / max(1, live_total) <= 0.02:
            likely_dirty_logged = True
    same_dirty_snapshot = (likely_dirty_logged and dirty and current_session > 0
        and latest_session >= max(0, current_session - 2)
        and abs(live_total - latest_logged) / max(1, latest_logged) <= 0.01)

    def _tier_targets() -> str:
        floor_tiers = floor_entry.get("tiers", {})
        tier_deltas = [f"{tier}+{live_tiers.get(tier,0)-floor_tiers.get(tier,0)}" for tier in sorted(live_tiers) if live_tiers.get(tier,0) - floor_tiers.get(tier,0) > 0]
        return f" [{', '.join(tier_deltas[:3])}]" if tier_deltas else ""

    if logged_drift > 0.06:
        if dirty and live_drift <= 0.06:
            results.append(("NOTICE", f"Proxy K logged drift {logged_drift:.1%} ({latest_logged} vs {floor}) but live drift is {live_drift:.1%} on dirty tree; re-save clean snapshot: {PYTHON_CMD} tools/proxy_k.py --save"))
        elif likely_dirty_logged:
            if logged_drift > 0.10:
                results.append(("URGENT" if logged_drift > 0.20 else "DUE", f"Proxy K drift {logged_drift:.1%} ({latest_logged} vs {floor}) on dirty tree — compaction overdue{_tier_targets()}; run: {PYTHON_CMD} tools/compact.py"))
            elif not same_dirty_snapshot:
                qualifier = "current dirty" if (current_session > 0 and latest_session >= current_session) else f"likely dirty S{latest_session}"
                results.append(("NOTICE", f"Proxy K logged drift {logged_drift:.1%} ({latest_logged} vs {floor}) from {qualifier}; save clean snapshot when stable: {PYTHON_CMD} tools/proxy_k.py --save"))
        elif stale_clean_baseline:
            results.append(("NOTICE", f"Proxy K baseline S{floor_session} is stale on dirty tree (current S{current_session}); re-save clean snapshot: {PYTHON_CMD} tools/proxy_k.py --save"))
        else:
            results.append(("URGENT" if logged_drift > 0.10 else "DUE", f"Proxy K drift {logged_drift:.1%} ({latest_logged} vs {floor}); run: {PYTHON_CMD} tools/compact.py"))
    elif live_drift > 0.06 and dirty:
        results.append(("NOTICE", f"Proxy K live drift {live_drift:.1%} ({live_total} vs {floor}) on dirty tree{_tier_targets()}; save when stable: {PYTHON_CMD} tools/proxy_k.py --save"))
    elif live_drift > 0.06:
        results.append(("URGENT" if live_drift > 0.10 else "DUE", f"Proxy K drift {live_drift:.1%} ({live_total} vs {floor}){_tier_targets()}; run: {PYTHON_CMD} tools/compact.py"))

    return results

def check_file_graph() -> list[tuple[str, str]]:
    structural = [REPO_ROOT / p for p in ("SWARM.md", "CLAUDE.md", "README.md", "beliefs/CORE.md", "memory/INDEX.md", "memory/OPERATIONS.md", "tasks/NEXT.md")]
    broken = []
    seen = set()
    for sf in structural:
        text = _read(sf)
        if not text: continue
        for ref in re.findall(r"`([a-zA-Z][\w\-/]+\.(?:md|py|json|sh))`", text):
            if ref.startswith(("L-", "P-", "B-")): continue
            resolved = ref if "/" in ref else FILE_REF_ALIAS_MAP.get(ref)
            if not resolved: continue
            if not (REPO_ROOT / resolved).exists():
                label = f"{sf.name}→{ref}" + (f" ({resolved})" if resolved != ref else "")
                if label not in seen:
                    seen.add(label); broken.append(label)
    if broken:
        return [("DUE", f"{len(broken)} broken file reference(s): {', '.join(broken[:5])}")]
    return []

def check_claim_gc() -> list[tuple[str, str]]:
    """F-CON2: garbage-collect expired soft-claim files (workspace/claims/)."""
    claims_dir = REPO_ROOT / "workspace" / "claims"
    if not claims_dir.exists():
        return []
    expired = []
    for f in claims_dir.glob("*.claim.json"):
        try:
            data = json.loads(f.read_text())
            ts = data.get("timestamp", "")
            if ts:
                from datetime import datetime as _dt, timezone as _tz
                age = (_dt.now(_tz.utc) - _dt.fromisoformat(ts)).total_seconds()
                if age > 120:  # claim.py TTL = 120s (L-589)
                    expired.append(f.name)
                    f.unlink()
        except Exception:
            pass
    if expired:
        return [("NOTICE", f"claim GC: removed {len(expired)} expired claim(s)")]
    return []


def check_correction_propagation() -> list[tuple[str, str]]:
    """F-IC1: detect HIGH-priority uncorrected citations of falsified lessons."""
    try:
        cp_path = REPO_ROOT / "tools" / "correction_propagation.py"
        if not cp_path.exists():
            return []
        import importlib.util as _ilu
        import sys as _sys
        _mod = "correction_propagation"
        if _mod not in _sys.modules:
            _spec = _ilu.spec_from_file_location(_mod, cp_path)
            _cp = _ilu.module_from_spec(_spec)
            _sys.modules[_mod] = _cp
            _spec.loader.exec_module(_cp)
        else:
            _cp = _sys.modules[_mod]
        result = _cp.run_analysis(session="S?", classify=True)
        high_items = [q for q in result.get("correction_queue", [])
                      if q.get("priority") == "HIGH"]
        total = result.get("total_uncorrected_citations", 0)
        if high_items:
            ids = ", ".join(q["citer"] for q in high_items[:5])
            extra = f"... +{len(high_items)-5} more" if len(high_items) > 5 else ""
            return [("DUE", f"{len(high_items)} HIGH-priority uncorrected citation(s) "
                     f"of falsified lessons: {ids}{extra} "
                     f"({total} total uncorrected). Run: python3 tools/correction_propagation.py --classify")]
        if total > 20:
            return [("NOTICE", f"{total} uncorrected citations of falsified lessons "
                     f"(0 HIGH). Run: python3 tools/correction_propagation.py --classify")]
    except Exception as e:
        return [("NOTICE", f"correction_propagation check error: {e}")]
    return []


def check_observer_staleness() -> list[tuple[str, str]]:
    """L-820, L-556: detect measurement tools with stale baselines.

    Observers that compare current state to a stored baseline drift silently
    when the baseline ages. Mean staleness was 63 sessions (L-820). This check
    flags any observer baseline older than 50 sessions.
    """
    results: list[tuple[str, str]] = []
    # Extract current session number
    sess = 0
    try:
        idx = (REPO_ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8", errors="replace")
        m = re.search(r"S(\d+)", idx)
        if m:
            sess = int(m.group(1))
    except Exception:
        return []
    if sess < 50:
        return []

    stale: list[str] = []
    threshold = 50  # sessions

    # Check proxy-K baseline in proxy-k-log
    try:
        pk_path = REPO_ROOT / "experiments" / "proxy-k-log.json"
        if pk_path.exists():
            pk_data = json.loads(pk_path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(pk_data, list) and pk_data:
                last_entry = pk_data[-1]
                last_sess_m = re.search(r"S(\d+)", str(last_entry.get("session", "")))
                if last_sess_m:
                    age = sess - int(last_sess_m.group(1))
                    if age > threshold:
                        stale.append(f"proxy-K({age}s)")
    except Exception:
        pass

    # Check dispatch calibration baseline
    try:
        dc_path = REPO_ROOT / "workspace" / "dispatch_calibration.json"
        if dc_path.exists():
            dc_data = json.loads(dc_path.read_text(encoding="utf-8", errors="replace"))
            cal_sess_m = re.search(r"S(\d+)", str(dc_data.get("calibrated_session", "")))
            if cal_sess_m:
                age = sess - int(cal_sess_m.group(1))
                if age > threshold:
                    stale.append(f"dispatch-calibration({age}s)")
    except Exception:
        pass

    # Check compact.py floor baseline
    try:
        for pk_entry in reversed(pk_data if 'pk_data' in dir() else []):
            if isinstance(pk_entry, dict) and pk_entry.get("floor"):
                floor_sess_m = re.search(r"S(\d+)", str(pk_entry.get("session", "")))
                if floor_sess_m:
                    age = sess - int(floor_sess_m.group(1))
                    if age > threshold:
                        stale.append(f"compaction-floor({age}s)")
                break
    except Exception:
        pass

    if stale:
        severity = "DUE" if len(stale) >= 2 else "NOTICE"
        return [(severity, f"{len(stale)} observer baseline(s) stale >{threshold}s: {', '.join(stale)}. "
                 f"Refresh to prevent drift blindness (L-820, L-556)")]
    return []


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

def build_inventory() -> dict:
    # Extracted to maintenance_inventory.py (DOMEX-META-S420)
    from maintenance_inventory import build_inventory as _impl
    return _impl(
        REPO_ROOT, PYTHON_EXE, PYTHON_CMD, BRIDGE_FILES,
        _exists, _python_command_runs, _py_launcher_runs,
        _command_runs, _command_exists, _inter_swarm_connectivity,
    )

def print_inventory(inv: dict):
    # Extracted to maintenance_inventory.py (DOMEX-META-S420)
    from maintenance_inventory import print_inventory as _impl
    return _impl(inv)

PRIORITY_ORDER = {"URGENT": 0, "DUE": 1, "PERIODIC": 2, "NOTICE": 3}
PRIORITY_SYMBOLS = {"URGENT": "!!!", "DUE": " ! ", "PERIODIC": " ~ ", "NOTICE": " . "}

# --- Swarm-grade outcome tracking (F-MECH1, GAP-1) ---
# Extracted to maintenance_outcomes.py (DOMEX-META-S420)
from maintenance_outcomes import load_outcomes as _load_outcomes
from maintenance_outcomes import save_outcomes_direct as _save_outcomes_direct_impl
from maintenance_outcomes import learn_from_outcomes as _learn_from_outcomes_impl

def _save_outcomes_direct(check_items: dict[str, list[tuple[str, str]]], session: int):
    _save_outcomes_direct_impl(check_items, session, OUTCOMES_PATH, OUTCOMES_MAX_SESSIONS)

def _learn_from_outcomes():
    _learn_from_outcomes_impl(OUTCOMES_PATH)

def main():
    if "--inventory" in sys.argv:
        inv = build_inventory()
        if "--json" in sys.argv:
            print(json.dumps(inv, indent=2))
        else:
            print_inventory(inv)
        return

    if "--learn" in sys.argv:
        _learn_from_outcomes()
        return

    quick = "--quick" in sys.argv

    all_checks = [
        check_kill_switch,
        check_validator,
        check_mission_constraints,
        check_runtime_portability,
        check_commit_hooks,
        check_version_drift,
        check_open_challenges,
        check_compaction,
        check_lessons,
        check_child_bulletins,
        check_help_requests,
        check_frontier_decay,
        check_periodics,
        check_human_queue,
        check_swarm_lanes,
        check_swarm_coordinator,
        check_lane_reporting_quality,
        check_github_swarm_intake,
        check_uncommitted,
        check_handoff_staleness,
        check_session_log_integrity,
        check_state_header_sync,
        check_cross_references,
        check_anxiety_zones,
        check_dispatch_log,
        check_domain_expert_coverage,
        check_council_health,
        check_signal_staleness,
        check_historian_integrity,
        check_domain_frontier_consistency,
        check_readme_snapshot_drift,
        check_count_drift,
        check_structure_layout,
        check_frontier_registry,
        check_file_graph,
        check_claim_gc,
        check_correction_propagation,
        check_observer_staleness,
        check_paper_accuracy,
        check_utility,
        check_dark_matter,
        check_proxy_k_drift,
        check_t4_tool_size,
        check_zombie_tools,
        check_meta_tooler_gap,
        check_level_quota,
    ]

    # check_utility was excluded from --quick due to 10s runtime (2200+ file reads).
    # Now uses git grep (0.4s) so it's safe to include. Kept for reference.

    if not quick:
        all_checks.append(check_unpushed)

    # HEAD-keyed caching: checks that only depend on committed state are cached
    # and skip execution when HEAD hasn't changed. Live checks (working tree,
    # env, concurrent claims) always run. Saves ~3-4s on cache hit.
    _LIVE_CHECKS = {
        "check_uncommitted",   # git status (working tree)
        "check_kill_switch",   # env vars + KILL-SWITCH.md (could toggle anytime)
        "check_claim_gc",      # workspace/claims/ (concurrent sessions)
        "check_periodics",     # tools/periodics.json updated in working tree before commit
        "check_level_quota",   # reads uncommitted lessons from working tree
    }
    try:
        from swarm_cache import head_cache as _hcache
    except ImportError:
        _hcache = None

    items: list[tuple[str, str]] = []
    check_items: dict[str, list[tuple[str, str]]] = {fn.__name__: [] for fn in all_checks}
    for check_fn in all_checks:
        name = check_fn.__name__
        try:
            # Try cache for HEAD-dependent checks
            if _hcache and name not in _LIVE_CHECKS:
                cached = _hcache.get(f"maint_{name}")
                if cached is not None:
                    fn_items = [tuple(x) for x in cached]
                    items.extend(fn_items)
                    check_items[name] = fn_items
                    continue
            fn_items = check_fn()
            items.extend(fn_items)
            check_items[name] = fn_items
            # Cache HEAD-dependent results
            if _hcache and name not in _LIVE_CHECKS:
                _hcache.set(f"maint_{name}", [list(x) for x in fn_items])
        except Exception as e:
            items.append(("NOTICE", f"{check_fn.__name__} error: {e}"))

    items.sort(key=lambda x: PRIORITY_ORDER.get(x[0], 99))

    print("=== MAINTENANCE ===")
    print()

    if not items:
        print("  Nothing due. All clear.")
    else:
        current_priority = None
        for priority, msg in items:
            if priority != current_priority:
                current_priority = priority
                print(f"  [{priority}]")
            symbol = PRIORITY_SYMBOLS.get(priority, "   ")
            print(f"  {symbol} {msg}")
        print()
        counts = {}
        for p, _ in items:
            counts[p] = counts.get(p, 0) + 1
        summary = " | ".join(f"{p}: {c}" for p, c in sorted(counts.items(), key=lambda x: PRIORITY_ORDER.get(x[0], 99)))
        print(f"  {summary}")

    # Swarm-grade: save outcomes for learning (F-MECH1)
    session = _session_number()
    if session > 0:
        _save_outcomes_direct(check_items, session)

    print()

    # --auto: Tier 2→Tier 1 bridge (L-533) — open lanes for DUE periodics with no active lane
    if "--auto" in sys.argv and session > 0:
        _auto_open_lanes(items, session)


def _auto_open_lanes(items: list[tuple[str, str]], session: int) -> None:
    """Open maintenance lanes for DUE periodic items that have no active lane. (L-533)"""
    due_periodics = [msg for sev, msg in items if sev == "DUE" and msg.startswith("[") and "]" in msg]
    if not due_periodics:
        print("  AUTO: no DUE periodic items to lane.")
        return

    # Collect active lane Etc content for deduplication
    active_etc = ""
    active_lane_ids: set[str] = set()
    if parsed_lanes := _active_lane_rows():
        _, active = parsed_lanes
        active_etc = " ".join(row.get("etc", "") for row in active).lower()
        active_lane_ids = {row.get("lane", "").strip() for row in active}

    print("\n  AUTO: scanning DUE periodics for lanes to open...")
    opened: list[str] = []
    skipped: list[str] = []

    for msg in due_periodics:
        m = re.match(r"\[([^\]]+)\]", msg)
        if not m:
            continue
        item_id = m.group(1)
        lane_id = f"MAINT-{item_id}-S{session}"

        # Skip if an active lane already covers this periodic
        if item_id.lower() in active_etc or lane_id in active_lane_ids:
            skipped.append(item_id)
            continue

        # Extract description from message (strip cadence/session suffix)
        desc_part = msg.split("]", 1)[1].strip()
        desc_clean = re.sub(r"\s*\(every.*?\)$", "", desc_part).strip()[:100]

        r = subprocess.run(
            [
                PYTHON_EXE, str(REPO_ROOT / "tools" / "open_lane.py"),
                "--lane", lane_id,
                "--session", f"S{session}",
                "--domain", "meta",
                "--frontier", "F-META3",
                "--intent", f"Periodic maintenance: {item_id} — {desc_clean}",
                "--expect", f"Periodic {item_id} completed; last_reviewed_session updated in periodics.json",
                "--artifact", f"experiments/meta/maint-{item_id}-s{session}.json",
                "--mode", "hardening",
                "--check-mode", "objective",
            ],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            opened.append(lane_id)
            print(f"  AUTO: opened → {lane_id}")
        else:
            err = (r.stderr or r.stdout or "").strip()[:120]
            print(f"  AUTO: SKIP {lane_id} — {err}")

    if skipped:
        print(f"  AUTO: {len(skipped)} already covered: {', '.join(skipped)}")
    if opened:
        print(f"  AUTO: {len(opened)} lane(s) created: {', '.join(opened)}")
    else:
        print(f"  AUTO: no new lanes needed.")
    print()


if __name__ == "__main__":
    main()
