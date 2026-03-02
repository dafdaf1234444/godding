#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# All shared constants, helpers, and I/O utilities are in maintenance_common.py
from maintenance_common import (
    REPO_ROOT, PYTHON_EXE, PYTHON_CMD, PRINCIPLE_ID_RE,
    UTILITY_CITATION_MAX_BYTES, UTILITY_CITATION_SKIP_PREFIXES,
    FILE_REF_ALIAS_MAP,
    LANE_ACTIVE_STATUSES, LANE_PLACEHOLDERS,
    LANE_STALE_NOTICE_SESSIONS, LANE_STALE_DUE_SESSIONS,
    LANE_ANTIWINDUP_ROWS, LANE_REPORT_KEYS,
    DOMAIN_SYNC_ALLOWED_VALUES, LANE_AVAILABLE_ALLOWED_VALUES, LANE_AVAILABLE_LEGACY_MAP,
    HIGH_RISK_LANE_PATTERNS, IGNORED_UNTRACKED_RUNTIME_FILES,
    OUTCOMES_PATH, OUTCOMES_MAX_SESSIONS,
    LANE_GLOBAL_FOCUS_VALUES, CHECK_FOCUS_HISTORIAN_REQUIRED,
    HISTORIAN_SELF_ANCHOR_TOKENS, HISTORIAN_SURROUNDINGS_ANCHOR_TOKENS,
    BRIDGE_FILES, KILL_SWITCH_PATH,
    DOMAIN_FRONTIER_ID_PATTERN, DOMAIN_FRONTIER_ID_RE, DOMAIN_ACTIVE_BULLET_RE,
    STRUCTURE_REQUIRED_PATHS, STRUCTURE_ALLOWED_FILENAMES, STRUCTURE_ALLOWED_EXTENSIONS,
    T4_TOOL_TOKEN_WARN,
    PRIORITY_ORDER, PRIORITY_SYMBOLS,
    run_paper_drift_check, _active_principle_ids,
    _truncated, _command_exists, _command_runs,
    _python_command_runs, _py_launcher_runs,
    _git, _status_path, _tracked_changed_paths,
    _read, _token_count, _line_count,
    _exists, _is_wsl_mnt_repo, _session_number,
    _is_lane_placeholder, _parse_lane_tags, _lane_has_any_tag, _lane_high_risk_signal,
    _parse_swarm_lane_rows, _normalize_frontier_id, _sorted_frontier_ids,
    _extract_markdown_section,
    _extract_domain_frontier_active_ids, _parse_domain_frontier_active_count,
    _parse_domain_index_active_count, _parse_domain_index_active_line_ids,
    _parse_domain_index_open_ids,
    _active_lane_rows, _format_frontier_id_diff,
    _iter_utility_citation_files, _inter_swarm_connectivity,
)

# ---------------------------------------------------------------------------
# Check functions — inline (not yet extracted to separate modules)
# ---------------------------------------------------------------------------

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
    from maintenance_lanes import check_swarm_lanes as _impl
    return _impl(
        _active_lane_rows, _session_number, _parse_lane_tags, _is_lane_placeholder,
        _lane_high_risk_signal, _truncated,
        LANE_ACTIVE_STATUSES, LANE_STALE_NOTICE_SESSIONS, LANE_STALE_DUE_SESSIONS,
        LANE_ANTIWINDUP_ROWS, DOMAIN_SYNC_ALLOWED_VALUES, LANE_AVAILABLE_ALLOWED_VALUES,
        LANE_AVAILABLE_LEGACY_MAP, LANE_GLOBAL_FOCUS_VALUES,
    )

def check_swarm_coordinator() -> list[tuple[str, str]]:
    from maintenance_lanes import check_swarm_coordinator as _impl
    return _impl(
        _active_lane_rows, _parse_lane_tags, _lane_has_any_tag, _truncated,
        LANE_GLOBAL_FOCUS_VALUES,
    )

def check_lane_reporting_quality() -> list[tuple[str, str]]:
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
    from maintenance_domains import check_frontier_decay as _impl
    return _impl(REPO_ROOT, _read)

def check_anxiety_zones() -> list[tuple[str, str]]:
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
    from maintenance_inventory import check_runtime_portability as _impl
    return _impl(
        REPO_ROOT, PYTHON_CMD, BRIDGE_FILES,
        _exists, _read, _git, _command_exists,
        _python_command_runs, _py_launcher_runs, _is_wsl_mnt_repo,
    )

def check_commit_hooks() -> list[tuple[str, str]]:
    from maintenance_inventory import check_commit_hooks as _impl
    return _impl(REPO_ROOT, _exists, _read)

def check_cross_references() -> list[tuple[str, str]]:
    from maintenance_state import check_cross_references as _impl
    return _impl(REPO_ROOT, _read, _git, _truncated, _active_principle_ids)

def check_domain_frontier_consistency() -> list[tuple[str, str]]:
    from maintenance_domains import check_domain_frontier_consistency as _impl
    return _impl(
        REPO_ROOT, _read, _truncated,
        _extract_domain_frontier_active_ids, _parse_domain_frontier_active_count,
        _parse_domain_index_active_count, _parse_domain_index_active_line_ids,
        _parse_domain_index_open_ids, _format_frontier_id_diff,
    )

def check_frontier_namespace_linkage() -> list[tuple[str, str]]:
    """P-274: flag low domain->global frontier linkage rate (L-938, F-NK6)."""
    results = []
    try:
        from frontier_crosslink import load_global_frontiers, load_domain_frontiers, compute_stats
        gf = load_global_frontiers()
        df = load_domain_frontiers()
        stats = compute_stats(df, gf)
        pct = stats["domain_linkage_pct"]
        if pct < 10:
            results.append(("NOTICE", f"Domain->global frontier linkage {pct:.1f}% ({stats['domain_linked_to_global']}/{stats['total_domain']}): run `python3 tools/frontier_crosslink.py` to find cross-link opportunities (P-274, L-938)"))
    except Exception:
        pass
    return results

def check_readme_snapshot_drift() -> list[tuple[str, str]]:
    from maintenance_state import check_readme_snapshot_drift as _impl
    return _impl(REPO_ROOT, _read, _session_number)

def check_count_drift() -> list[tuple[str, str]]:
    from maintenance_state import check_count_drift as _impl
    return _impl(REPO_ROOT, _read, _git)

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
    from maintenance_domains import check_frontier_registry as _impl
    return _impl(REPO_ROOT, _read, _truncated)

def check_handoff_staleness() -> list[tuple[str, str]]:
    from maintenance_state import check_handoff_staleness as _impl
    return _impl(REPO_ROOT, _read, _session_number)

def check_state_header_sync() -> list[tuple[str, str]]:
    from maintenance_state import check_state_header_sync as _impl
    return _impl(REPO_ROOT, _read, _git, _session_number)

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
    from maintenance_state import check_session_log_integrity as _impl
    return _impl(REPO_ROOT, _read, _truncated)

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
    from maintenance_drift import check_proxy_k_drift as _impl
    return _impl(REPO_ROOT, PYTHON_CMD, _read, _git, _token_count, _session_number)

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
                label = f"{sf.name}->{ref}" + (f" ({resolved})" if resolved != ref else "")
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
    from maintenance_drift import check_observer_staleness as _impl
    return _impl(REPO_ROOT)


def build_inventory() -> dict:
    from maintenance_inventory import build_inventory as _impl
    return _impl(
        REPO_ROOT, PYTHON_EXE, PYTHON_CMD, BRIDGE_FILES,
        _exists, _python_command_runs, _py_launcher_runs,
        _command_runs, _command_exists, _inter_swarm_connectivity,
    )

def print_inventory(inv: dict):
    from maintenance_inventory import print_inventory as _impl
    return _impl(inv)

# --- Swarm-grade outcome tracking (F-MECH1, GAP-1) ---
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
        check_frontier_namespace_linkage,
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
        "check_uncommitted",        # git status (working tree)
        "check_kill_switch",        # env vars + KILL-SWITCH.md (could toggle anytime)
        "check_claim_gc",           # workspace/claims/ (concurrent sessions)
        "check_periodics",          # tools/periodics.json updated in working tree before commit
        "check_level_quota",        # reads uncommitted lessons from working tree
        "check_swarm_lanes",        # tasks/SWARM-LANES.md modified by concurrent sessions
        "check_swarm_coordinator",  # tasks/SWARM-LANES.md modified by concurrent sessions
        "check_lane_reporting_quality",  # tasks/SWARM-LANES.md modified by concurrent sessions
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

    # --auto: Tier 2->Tier 1 bridge (L-533) — open lanes for DUE periodics with no active lane
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
            print(f"  AUTO: opened -> {lane_id}")
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
