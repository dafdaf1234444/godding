#!/usr/bin/env python3
"""State validation checks extracted from maintenance.py (S422 distillation).

Contains: check_cross_references, check_count_drift, check_readme_snapshot_drift,
check_state_header_sync, check_handoff_staleness, check_session_log_integrity.
These checks validate INDEX/PRINCIPLES/FRONTIER count consistency, README snapshot
drift, state header session stamps, NEXT.md handoff freshness, and SESSION-LOG integrity.
"""

import re
from pathlib import Path


def check_cross_references(
    REPO_ROOT: Path,
    _read,
    _git,
    _truncated,
    _active_principle_ids,
) -> list[tuple[str, str]]:
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


def check_count_drift(
    REPO_ROOT: Path,
    _read,
    _git,
) -> list[tuple[str, str]]:
    """Verify INDEX.md L/P/B/F header counts match filesystem reality. (L-887, L-216)"""
    results = []
    index_text = _read(REPO_ROOT / "memory" / "INDEX.md")
    if not index_text:
        return results

    l_m = re.search(r"\*\*(\d+) lessons\*\*", index_text)
    p_m = re.search(r"\*\*(\d+) principles\*\*", index_text)
    b_m = re.search(r"\*\*(\d+) beliefs\*\*", index_text)
    f_m = re.search(r"\*\*(\d+) frontiers?\*\*", index_text)
    if not (l_m and p_m and b_m and f_m):
        return results

    stated = {
        "L": int(l_m.group(1)),
        "P": int(p_m.group(1)),
        "B": int(b_m.group(1)),
        "F": int(f_m.group(1)),
    }

    tracked_lessons = _git("ls-files", "memory/lessons/").splitlines()
    actual_L = sum(1 for f in tracked_lessons if re.match(r"memory/lessons/L-\d+\.md$", f))

    principles_text = _read(REPO_ROOT / "memory" / "PRINCIPLES.md")
    all_p = set(re.findall(r"^### P-(\d+):", principles_text, re.MULTILINE))
    superseded_p = set(re.findall(r"^<!--\s*SUPERSEDED.*?P-(\d+)", principles_text, re.MULTILINE))
    actual_P = len(all_p - superseded_p)

    deps_text = _read(REPO_ROOT / "beliefs" / "DEPS.md")
    actual_B = len(set(re.findall(r"^### B[-\w]+:", deps_text, re.MULTILINE)))

    frontier_text = _read(REPO_ROOT / "tasks" / "FRONTIER.md")
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


def check_readme_snapshot_drift(
    REPO_ROOT: Path,
    _read,
    _session_number,
) -> list[tuple[str, str]]:
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


def check_state_header_sync(
    REPO_ROOT: Path,
    _read,
    _git,
    _session_number,
) -> list[tuple[str, str]]:
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


def check_handoff_staleness(
    REPO_ROOT: Path,
    _read,
    _session_number,
) -> list[tuple[str, str]]:
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


def check_session_log_integrity(
    REPO_ROOT: Path,
    _read,
    _truncated,
) -> list[tuple[str, str]]:
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
