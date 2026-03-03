#!/usr/bin/env python3

import json
import re
from pathlib import Path

try:
    from tools.swarm_parse import active_principle_ids, active_frontier_ids, archived_frontier_ids
except ModuleNotFoundError:
    from swarm_parse import active_principle_ids, active_frontier_ids, archived_frontier_ids

try:
    from swarm_io import read_text as _read
    _has_swarm_io = True
except ImportError:
    try:
        from tools.swarm_io import read_text as _read
        _has_swarm_io = True
    except ImportError:
        _has_swarm_io = False

if not _has_swarm_io:
    def _read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""


def _philosophy_challenge_stats(text: str) -> tuple[int, int]:
    """Return (confirmed, total_resolved_like) from PHILOSOPHY challenge table."""
    if "## Challenges" in text:
        text = text[text.find("## Challenges"):]

    confirmed = 0
    total = 0
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        if not re.search(r"\|\s*PHIL-\d+", line):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cols:
            continue
        status = cols[-1].upper()
        if not status:
            continue
        if any(k in status for k in ("CONFIRMED", "SUPERSEDED", "DROPPED", "REFINED", "PARTIAL")):
            total += 1
            if "CONFIRMED" in status:
                confirmed += 1
    return confirmed, total


def check_paper_accuracy(repo_root: Path, session: int) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    text = _read(repo_root / "docs" / "PAPER.md")
    if not text:
        return results

    cadence = 20
    try:
        items = json.loads(_read(repo_root / "tools" / "periodics.json")).get("items", [])
        for item in items:
            if item.get("id") == "paper-reswarm":
                cadence = int(item.get("cadence_sessions", cadence))
                break
    except Exception:
        pass

    paper_session = None
    ver = re.search(r"paper_version:\s*[\d.]+\s*\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*S(\d+)", text, re.IGNORECASE)
    if session > 0:
        if ver:
            paper_session = int(ver.group(1))
            age = session - paper_session
            if age >= cadence * 2:
                results.append(("URGENT", f"PAPER stale by {age} sessions (cadence {cadence})"))
            elif age >= cadence:
                results.append(("DUE", f"PAPER refresh due (age {age}, cadence {cadence})"))
        else:
            results.append(("DUE", "PAPER missing parseable paper_version header"))

    scale = re.search(
        r"As of session\s+(\d+),\s+the swarm has accumulated\s+(\d+)\s+lessons,\s+(\d+)\s+principles,\s+(\d+)\s+active beliefs,\s+and\s+(\d+)\s+open frontier questions",
        text,
        re.IGNORECASE,
    )
    if not scale:
        results.append(("DUE", "PAPER missing parseable scale statement"))
        return results

    _, s_lessons, s_principles, s_beliefs, s_frontiers = map(int, scale.groups())
    frontier_ids = active_frontier_ids(_read(repo_root / "tasks" / "FRONTIER.md"))
    all_ids, superseded = active_principle_ids(_read(repo_root / "memory" / "PRINCIPLES.md"))
    actual = {
        "lessons": len(list((repo_root / "memory" / "lessons").glob("L-*.md"))),
        "principles": len(all_ids - superseded),
        "beliefs": len(re.findall(r"^### B(?:\d+|-EVAL\d+):", _read(repo_root / "beliefs" / "DEPS.md"), re.MULTILINE)),
        "frontiers": len(frontier_ids),
    }
    paper = {"lessons": s_lessons, "principles": s_principles, "beliefs": s_beliefs, "frontiers": s_frontiers}
    deltas = {k: abs(actual[k] - paper[k]) for k in paper if actual[k] != paper[k]}
    if deltas:
        diff = ", ".join(f"{k} {paper[k]}->{actual[k]}" for k in deltas)
        lesson_delta = deltas.get("lessons", 0)
        structural = {"principles", "beliefs", "frontiers"} & set(deltas)
        level = "DUE" if structural or lesson_delta >= 10 else "NOTICE" if lesson_delta >= 3 else ""
        if level:
            age = f" (paper age {session - paper_session} sessions)" if paper_session is not None and session > 0 else ""
            results.append((level, f"PAPER scale drift{age}: {diff}"))

    archived = archived_frontier_ids(_read(repo_root / "tasks" / "FRONTIER-ARCHIVE.md"))
    resolved = {int(m.group(1)) for m in re.finditer(r"\bF(\d+)\s+RESOLVED\b", text, re.IGNORECASE)}
    open_ids = {int(m.group(1)) for m in re.finditer(r"\bopen question(?:s)?[^.\n]{0,120}\bF(\d+)\b", text, re.IGNORECASE)}
    if resolved:
        active = sorted(resolved & frontier_ids)
        if active:
            results.append(("DUE", f"PAPER frontier drift: RESOLVED still active: {', '.join(f'F{x}' for x in active[:5])}"))
        missing = sorted((resolved - archived) - set(active))
        if missing:
            results.append(("DUE", f"PAPER frontier drift: RESOLVED missing archive: {', '.join(f'F{x}' for x in missing[:5])}"))
    if open_ids:
        archived_open = sorted(open_ids & archived)
        not_active = sorted((open_ids - frontier_ids) - set(archived_open))
        if not_active:
            results.append(("DUE", f"PAPER frontier drift: open claims not active: {', '.join(f'F{x}' for x in not_active[:5])}"))
        if archived_open:
            results.append(("DUE", f"PAPER frontier drift: open claims archived: {', '.join(f'F{x}' for x in archived_open[:5])}"))

    status_re = re.compile(r"\b(PARTIALLY OBSERVED|THEORIZED|OBSERVED|SPLIT|PENDING|CONTESTED)\b", re.IGNORECASE)
    canon: dict[int, str] = {}
    principles_text = _read(repo_root / "memory" / "PRINCIPLES.md")
    for seg in re.split(r"[|\n]", principles_text):
        # Skip the Removed line — subsumed IDs with embedded status words
        # cause false cross-contamination (e.g. "3-session wait-before-acting")
        if "Removed:" in seg or seg.strip().startswith("Removed"):
            continue
        ids = [int(x) for x in re.findall(r"\bP-(\d+)\b", seg)]
        if not ids:
            continue
        found = status_re.findall(seg)
        if found:
            s = found[-1].upper()
            for pid in ids:
                canon[pid] = s
    claimed: dict[int, str] = {}
    for seg in re.split(r"[.;\n]", text):
        ids = [int(x) for x in re.findall(r"\bP-(\d+)\b", seg)]
        if not ids:
            continue
        found = status_re.findall(seg)
        if found:
            s = found[-1].upper()
            for pid in ids:
                claimed[pid] = s
    mismatch = sorted(pid for pid, c in claimed.items() if pid in canon and canon[pid] != c and pid not in superseded)
    if mismatch:
        sample = ", ".join(f"P-{pid}({claimed[pid]}!={canon[pid]})" for pid in mismatch[:5])
        results.append(("DUE", f"PAPER principle-status drift: {sample}"))

    # Low-noise monitor: explicit "X/Y challenges confirmed" paper claims.
    # Keep NOTICE level because narrative sections can include historical snapshots.
    claimed_ratios = {
        (int(a), int(b))
        for a, b in re.findall(r"\b(\d+)\s*/\s*(\d+)\s+challenges?\s+confirmed\b", text, re.IGNORECASE)
    }
    if claimed_ratios:
        actual_confirmed, actual_total = _philosophy_challenge_stats(_read(repo_root / "beliefs" / "PHILOSOPHY.md"))
        if actual_total > 0:
            mismatched = sorted((c, t) for c, t in claimed_ratios if (c, t) != (actual_confirmed, actual_total))
            if mismatched:
                sample = ", ".join(f"{c}/{t}" for c, t in mismatched[:3])
                results.append((
                    "NOTICE",
                    f"PAPER challenge-ratio drift: claims {sample}; PHILOSOPHY table shows {actual_confirmed}/{actual_total}",
                ))

    return results
