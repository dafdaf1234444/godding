#!/usr/bin/env python3
"""maintenance_health.py — Operational/runtime health checks extracted from maintenance.py (P-282)."""

import json
import os
import re
import subprocess
from pathlib import Path

from maintenance_common import (
    REPO_ROOT, PYTHON_EXE,
    KILL_SWITCH_PATH, T4_TOOL_TOKEN_WARN,
    IGNORED_UNTRACKED_RUNTIME_FILES,
    _git, _read, _status_path, _is_wsl_mnt_repo, _truncated,
    _line_count,
)


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
    results: list[tuple[str, str]] = []
    over_20 = []
    # L-973 TTL: track no-Sharpe + old lessons for archive candidates
    sharpe_re = re.compile(r'Sharpe:\s*\d+')
    session_re = re.compile(r'Session:\s*S?(\d+)')
    ttl_candidates = 0
    max_session = 0
    # First pass: find max session from git log
    log_line = _git("log", "--oneline", "-1")
    sm = re.search(r'\[S(\d+)\]', log_line) if log_line else None
    if sm:
        max_session = int(sm.group(1))
    else:
        max_session = len(list(lessons_dir.glob("L-*.md")))
    for f in lessons_dir.glob("L-*.md"):
        if _line_count(f) > 20:
            # SIG-56: WSL page-cache can return stale content after concurrent trim.
            # If HEAD already has ≤20 lines, the working-tree count is a caching artifact.
            rel = str(f.relative_to(REPO_ROOT))
            committed = _git("show", f"HEAD:{rel}")
            if committed and len(committed.splitlines()) <= 20:
                continue  # already trimmed in HEAD — skip false positive
            over_20.append(f.name)
        # L-973: TTL check — no Sharpe + age > 100 sessions = archive candidate
        try:
            header = f.read_text(encoding="utf-8", errors="replace")[:500]
        except Exception:
            continue
        if sharpe_re.search(header):
            continue  # has Sharpe — not a TTL candidate
        lm = session_re.search(header)
        if lm:
            age = max_session - int(lm.group(1))
            if age > 100:
                ttl_candidates += 1
    if over_20:
        # One item per lesson for unique claim fingerprints (L-933: trim-collision waste).
        # Sessions can claim individual trim tasks: python3 tools/claim.py claim trim:L-NNN
        results.extend([("DUE", f"Lesson over 20 lines: {name}") for name in over_20[:5]])
    # L-973: report TTL candidates (no-Sharpe + age>100) — structural enforcement of sunset clause
    if ttl_candidates > 20:
        results.append(("NOTICE", f"L-973 TTL: {ttl_candidates} lessons with no Sharpe + age>100 sessions — run compact.py for archive candidates"))
    return results


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
    """L-601 self-application: detect tools/*.py with no references in automation entry points.
    L-1017: walks import chain from entry points to reduce false positives on extraction modules."""
    results: list[tuple[str, str]] = []
    tools_dir = REPO_ROOT / "tools"
    if not tools_dir.exists():
        return results
    # Enumerate production tools (exclude tests, archive, __pycache__)
    tool_stems = sorted(
        f.stem for f in tools_dir.glob("*.py")
        if not f.stem.startswith("test_") and f.stem != "__init__"
    )
    if not tool_stems:
        return results
    tool_stem_set = set(tool_stems)

    # Phase 1: scan entry points + protocol files for direct references
    entry_files = ["tools/check.sh", "tools/orient.py", "tools/maintenance.py",
                   "tools/periodics.json", "CLAUDE.md", "SWARM.md",
                   "tools/autoswarm.sh", ".claude/commands/swarm.md"]
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
    reachable = {t for t in tool_stem_set if t in ref_text}

    # Phase 2: walk import chain — tools referenced by reachable tools are also reachable
    import_re = re.compile(r"(?:from|import)\s+([\w]+)")
    subprocess_re = re.compile(r"tools[/\\]([\w]+)\.py")
    # Match Path() concatenation: "tools" / "foo.py" or quoted "foo.py" near "tools"
    quoted_tool_re = re.compile(r'["\'](\w+)\.py["\']')
    frontier = list(reachable)
    while frontier:
        stem = frontier.pop()
        src_path = tools_dir / f"{stem}.py"
        if not src_path.exists():
            continue
        try:
            src = src_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in import_re.finditer(src):
            dep = m.group(1)
            if dep in tool_stem_set and dep not in reachable:
                reachable.add(dep)
                frontier.append(dep)
        for m in subprocess_re.finditer(src):
            dep = m.group(1)
            if dep in tool_stem_set and dep not in reachable:
                reachable.add(dep)
                frontier.append(dep)
        for m in quoted_tool_re.finditer(src):
            dep = m.group(1)
            if dep in tool_stem_set and dep not in reachable:
                reachable.add(dep)
                frontier.append(dep)

    unreferenced = sorted(t for t in tool_stems if t not in reachable)
    if len(unreferenced) > len(tool_stems) * 0.6:
        if len(unreferenced) > 30:
            results.append(("NOTICE", f"{len(unreferenced)}/{len(tool_stems)} tools not referenced by automation/protocol files (L-601 zombie risk). Top: {_truncated(unreferenced, 5)}"))
    elif unreferenced:
        results.append(("NOTICE", f"{len(unreferenced)}/{len(tool_stems)} tools not referenced by automation entry points. {_truncated(unreferenced, 5)}"))
    return results


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


def check_memory_md_size() -> list[tuple[str, str]]:
    """Check Claude auto-memory MEMORY.md line count to prevent always-visible truncation (B2, L-1057)."""
    try:
        encoded = str(REPO_ROOT).replace("/", "-")
        memory_path = Path.home() / ".claude" / "projects" / encoded / "memory" / "MEMORY.md"
        if not memory_path.exists():
            return []
        lines = len(memory_path.read_text(encoding="utf-8").splitlines())
        if lines > 180:
            return [("DUE", f"MEMORY.md approaching 200-line limit ({lines}L) — archive session findings to session-findings.md (B2, L-1057)")]
        if lines > 160:
            return [("NOTICE", f"MEMORY.md at {lines}/200 lines — archive session findings soon (B2)")]
    except Exception:
        pass
    return []


def check_scale_waypoints() -> list[tuple[str, str]]:
    """Detect crossed scale-break waypoints requiring architectural action (L-1066).

    Three measured waypoints: N≈550 (integration-bound), N≈750 (reliability-break),
    N≈1000 (enforcement-dilution). Each shifts the binding constraint.

    FM-33 hardening (S453): auto-apply cadence changes instead of advisory DUE (L-601).
    All remediation paths with deterministic actions use detect→write→NOTICE, not
    detect→DUE→hope. DUE is reserved for items requiring human judgment.
    """
    results = []
    try:
        index_text = _read(REPO_ROOT / "memory" / "INDEX.md")
        m = re.search(r"\*\*(\d+) lessons\*\*", index_text)
        if not m:
            return results
        n = int(m.group(1))

        # Waypoints are cumulative — higher N includes all lower thresholds (L-1094 fix S456)
        # Waypoint 1: N≥550 — integration-bound, route ≥1/3 sessions to historian-mode (L-1094, L-912)
        if n >= 550:
            results.append(("NOTICE", f"L-1094 N≥550 integration-bound ({n}L): route ≥1/3 sessions to historian-mode (L-912, L-1094)"))

        # Waypoint 2: N≥750 — reliability-break, O(N²) and hardcoded value audit (L-1066, L-788)
        if n >= 750:
            results.append(("NOTICE", f"L-1066 N≥750 waypoint ({n}L): O(N²) tool audit — run python3 tools/enforcement_router.py + check_stale_baselines for hardcoded values (L-788)"))

        # Waypoint 3: N≥1000 — enforcement dilution (L-1066, L-1062)
        # Action: auto-reduce enforcement-audit cadence to 3 sessions
        # FM-33 hardening (S453): auto-apply instead of advisory DUE (L-601)
        # FM-34 hardening (S455): retention-vs-accessibility audit (L-1096)
        if n >= 1000:
            results.extend(_auto_apply_enforcement_cadence(n))
            results.extend(_check_retention_accessibility(n, index_text))
            # L-1104: monitoring tools have self-referential failures at scale.
            # Surface enforcement diagnosis to detect ASPIRATIONAL frontiers.
            results.append(("NOTICE", f"L-1104 N≥1000 monitoring audit ({n}L): run python3 tools/historian_router.py --enforce to diagnose frontier enforcement gaps"))

    except Exception as e:
        results.append(("NOTICE", f"check_scale_waypoints error: {e}"))
    return results


# Target cadences per waypoint (FM-33 auto-apply table).
# Each entry: (periodic_id, max_cadence_at_waypoint, waypoint_label)
_N1000_CADENCE_TARGETS = [
    ("enforcement-audit", 3, "enforcement-dilution"),
]


def _auto_apply_enforcement_cadence(n: int) -> list[tuple[str, str]]:
    """FM-33 structural remediation: auto-write cadence changes to periodics.json.

    Pattern: detect→write→NOTICE (not detect→DUE→hope).
    If periodics.json is unreadable/unwritable, emit URGENT (not DUE) so the failure
    of the fix itself is visible rather than silently decaying to advisory (L-601).
    """
    results: list[tuple[str, str]] = []
    periodics_path = REPO_ROOT / "tools" / "periodics.json"
    try:
        data = json.loads(periodics_path.read_text(encoding="utf-8"))
    except Exception as e:
        results.append(("URGENT", f"FM-33 auto-apply FAILED: cannot read periodics.json: {e} — manual fix required (L-1066)"))
        return results

    items = data.get("items", [])
    changed = False
    for periodic_id, max_cadence, label in _N1000_CADENCE_TARGETS:
        entry = next((e for e in items if e.get("id") == periodic_id), None)
        if entry is None:
            results.append(("URGENT", f"FM-33: periodic '{periodic_id}' missing from periodics.json — N≥1000 {label} cadence cannot be enforced"))
            continue
        current = entry.get("cadence_sessions", max_cadence + 1)
        if current > max_cadence:
            entry["cadence_sessions"] = max_cadence
            changed = True
            results.append(("NOTICE", f"L-1066 N≥1000 waypoint: auto-applied {periodic_id} cadence {current}→{max_cadence} in periodics.json (FM-33 hardening)"))

    if changed:
        try:
            periodics_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        except Exception as e:
            results.append(("URGENT", f"FM-33 auto-apply FAILED: cannot write periodics.json: {e} — manual fix required"))

    return results


def _check_retention_accessibility(n: int, index_text: str) -> list[tuple[str, str]]:
    """FM-34 (L-1096): detect retention-accessibility divergence at N≥1000.

    Storage completeness masks access degradation. Five independent findings
    show storage stays near 100% while access degrades to 5-31% — and the
    system reports only the storage metric.

    Measures:
    1. Dark matter (unthemed lessons): retained but not indexed for retrieval.
    2. Citation isolation: recent lessons that cite 0 prior lessons — knowledge
       stored but not connected.
    """
    results: list[tuple[str, str]] = []

    # 1. Dark matter: unthemed lessons = stored without access infrastructure
    total_match = re.search(r"\*\*(\d+) lessons\*\*", index_text)
    if not total_match:
        return results
    total = int(total_match.group(1))

    themed_count = 0
    in_themes = False
    for line in index_text.splitlines():
        if re.match(r"^## Themes", line):
            in_themes = True
            continue
        if in_themes and line.startswith("## "):
            break
        if in_themes and line.startswith("|") and not line.startswith("| Theme") and not line.startswith("| ---"):
            cols = [c.strip() for c in line.split("|")]
            # Table format: | Theme | Count | Key insight |
            if len(cols) >= 3:
                try:
                    themed_count += int(cols[2])
                except (ValueError, IndexError):
                    pass

    dark_matter = total - themed_count
    dark_pct = (dark_matter / total * 100) if total > 0 else 0

    if dark_pct > 40:
        results.append(("DUE", f"FM-34 retention-accessibility: {dark_pct:.0f}% lessons unthemed ({dark_matter}/{total}) — access degraded, storage intact (L-1096)"))
    elif dark_pct > 30:
        results.append(("NOTICE", f"FM-34 retention-accessibility: {dark_pct:.0f}% unthemed ({dark_matter}/{total}) — approaching access threshold (L-1096)"))
    # L-1111: theme count staleness — absolute gap triggers remediation earlier than %
    if dark_matter > 200:
        results.append(("DUE", f"INDEX.md theme counts stale: {dark_matter} lessons unthemed — refresh theme table counts (L-1111, F-BRN4 sawtooth cycle)"))

    # 2. Citation isolation in recent lessons
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    if lessons_dir.exists():
        lesson_files = sorted(lessons_dir.glob("L-*.md"), key=lambda f: f.stem)
        recent = lesson_files[-50:] if len(lesson_files) >= 50 else lesson_files
        isolated = 0
        for lf in recent:
            try:
                content = lf.read_text(encoding="utf-8", errors="replace")
                # Check Cites: header for L-NNN references to other lessons
                cites_match = re.search(r"^\*{0,2}Cites\*{0,2}:(.+)$", content, re.MULTILINE)  # L-1169
                if cites_match:
                    if re.search(r"L-\d+", cites_match.group(1)):
                        continue
                isolated += 1
            except Exception:
                continue
        iso_pct = (isolated / len(recent) * 100) if recent else 0
        if iso_pct > 50:
            results.append(("NOTICE", f"FM-34 citation isolation: {iso_pct:.0f}% of last {len(recent)} lessons cite 0 prior lessons — knowledge stored but disconnected (L-1096)"))

    return results
