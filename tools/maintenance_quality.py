#!/usr/bin/env python3
"""maintenance_quality.py — Quality/integrity checks extracted from maintenance.py (P-282)."""

import importlib.util
import json
import re
import sys
from pathlib import Path

from maintenance_common import (
    REPO_ROOT, PYTHON_EXE,
    PRINCIPLE_ID_RE, FILE_REF_ALIAS_MAP,
    STRUCTURE_REQUIRED_PATHS, STRUCTURE_ALLOWED_FILENAMES, STRUCTURE_ALLOWED_EXTENSIONS,
    _read, _git, _exists, _truncated, _session_number, _lesson_texts,
    _active_principle_ids, run_paper_drift_check,
)


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
        result = _cp.run_analysis(session="S?", classify=True, preloaded=_lesson_texts())
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
    texts = _lesson_texts()
    if not texts:
        return []
    total = len(texts)
    no_cites = sum(1 for content in texts.values()
                   if not re.search(r"(?:^|\| )\*{0,2}Cites\*{0,2}:\s*\S", content, re.MULTILINE))
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
    texts = _lesson_texts()
    if not texts:
        return []

    strategic_keywords = [
        "architecture", "paradigm", "strategy", "governance", "reframe",
        "redesign", "structural design", "L3+", "level=L3", "level=L4", "level=L5",
    ]

    def _is_l3plus(text: str) -> bool:
        # Handle both plain (Level: L3) and bold (**Level**: L3) formats
        if re.search(r"\*{0,2}[Ll]evel\*{0,2}[=:\s]+[Ll][3-5]", text):
            return True
        high_sharpe = bool(re.search(r"\*{0,2}Sharpe\*{0,2}:\s*(9|10)\b", text))
        text_lower = text.lower()
        return high_sharpe and any(k.lower() in text_lower for k in strategic_keywords)

    session_has_l3: dict[int, bool] = {}
    for text in texts.values():
        m = re.search(r"\*{0,2}Session\*{0,2}:\s*S(\d+)", text)
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


def check_paper_accuracy() -> list[tuple[str, str]]:
    return run_paper_drift_check(REPO_ROOT, _session_number())


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
