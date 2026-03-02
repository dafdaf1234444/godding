#!/usr/bin/env python3
"""Data loaders for eval_sufficiency.py (extracted S441 — DI pattern from L-941).

All functions read swarm state files and return dicts/lists for goal scoring.
No scoring logic here — pure data access layer.
"""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _get_current_session() -> str:
    """Read current session number from INDEX.md (avoids hardcoded stale session labels)."""
    try:
        text = (ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8")
        m = re.search(r"Sessions:\s*(\d+)", text)
        if m:
            return f"S{m.group(1)}"
    except Exception:
        pass
    return "S?"


def _load_session_log() -> list[dict]:
    """Parse SESSION-LOG.md for per-session L+P entries.

    Aggregates multiple log lines for the same session number into a single
    entry (high-concurrency sessions produce multiple log lines per session).
    Tags sessions as DOMEX if any log line contains 'DOMEX' (F-EVAL4 stratification).
    """
    path = ROOT / "memory" / "SESSION-LOG.md"
    by_session: dict[int, dict] = {}
    pat = re.compile(r"S(\d+)\s*[\t|].*?\+(\d+)L.*?\+(\d+|\?)P")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m:
            s = int(m.group(1))
            if s not in by_session:
                by_session[s] = {"session": s, "lessons": 0, "principles": 0, "is_domex": False}
            by_session[s]["lessons"] += int(m.group(2))
            p_str = m.group(3)
            by_session[s]["principles"] += int(p_str) if p_str != "?" else 0
            if "DOMEX" in line:
                by_session[s]["is_domex"] = True
    return sorted(by_session.values(), key=lambda x: x["session"])


def _count_swarm_lanes() -> dict:
    """Count MERGED, OPEN, ACTIVE, ABANDONED rows in SWARM-LANES.md."""
    path = ROOT / "tasks" / "SWARM-LANES.md"
    text = path.read_text(encoding="utf-8")
    return {
        "merged": len(re.findall(r"\bMERGED\b", text)),
        "open": len(re.findall(r"\bOPEN\b", text)),
        "active": len(re.findall(r"\bACTIVE\b", text)),
        "abandoned": len(re.findall(r"\bABANDONED\b", text)),
        "total_rows": sum(1 for l in text.splitlines()
                         if l.strip().startswith("|") and "---" not in l and "Lane" not in l),
    }


def _load_proxy_k(current_session: int = 193) -> dict:
    """Get proxy-K drift using compact.py --dry-run (authoritative source)."""
    try:
        out = subprocess.check_output(
            ["python3", str(ROOT / "tools" / "compact.py"), "--dry-run"],
            text=True, stderr=subprocess.DEVNULL, cwd=str(ROOT)
        )
        m_total = re.search(r"Current:\s*([\d,]+)\s*tokens", out)
        m_floor = re.search(r"Floor:\s*([\d,]+)\s*tokens", out)
        m_drift = re.search(r"Drift:\s*([+-]?[\d.]+)%", out)
        total = int(m_total.group(1).replace(",", "")) if m_total else 0
        floor = int(m_floor.group(1).replace(",", "")) if m_floor else total
        drift_pct = float(m_drift.group(1)) if m_drift else 0.0
        return {"total": total, "floor": floor, "drift_pct": drift_pct}
    except Exception:
        pass
    return {"total": 0, "floor": 0, "drift_pct": 0.0}


def _count_challenges() -> dict:
    """Count CHALLENGES.md status distribution."""
    path = ROOT / "beliefs" / "CHALLENGES.md"
    text = path.read_text(encoding="utf-8")
    data_rows = [l for l in text.splitlines()
                 if l.startswith("| S") and "---" not in l and "Session" not in l]

    def _status(row: str) -> str:
        parts = row.split("|")
        return parts[-2].strip() if len(parts) >= 3 else ""

    statuses = [_status(r) for r in data_rows]
    confirmed = sum(1 for s in statuses if s.startswith("CONFIRMED"))
    superseded = sum(1 for s in statuses if s.startswith("SUPERSEDED"))
    dropped = sum(1 for s in statuses if s.startswith("DROPPED"))
    partial = sum(1 for s in statuses if s.startswith("PARTIAL") and "CONFIRMED" not in s)
    queued = sum(1 for s in statuses if s.startswith("QUEUED"))
    open_ = sum(1 for s in statuses if s.startswith("OPEN"))
    total = len(data_rows)
    evidence_grounded = confirmed + superseded + partial + dropped
    return {
        "confirmed": confirmed, "superseded": superseded, "partial": partial,
        "dropped": dropped, "open": open_, "queued": queued,
        "total": total, "evidence_grounded": evidence_grounded,
    }


def _count_human_signals() -> dict:
    """Count human signals and compute artifact-ref enforcement completeness."""
    path = ROOT / "memory" / "HUMAN-SIGNALS.md"
    text = path.read_text(encoding="utf-8")
    rows = [l for l in text.splitlines()
            if l.startswith("| S") and "---" not in l and "Session" not in l]
    total = len(rows)
    _ref_pat = re.compile(
        r"\b[LPFB]-?\d+|PHIL-\d+|CORE-P\d+|"
        r"(?:SWARM|CLAUDE|FRONTIER|PRINCIPLES|LANES|INDEX|orient|domain|agent|personality|experiment)",
        re.IGNORECASE,
    )
    with_refs = sum(1 for r in rows
                    if _ref_pat.search(r.split("|")[3] if len(r.split("|")) > 3 else ""))
    return {"total": total, "with_artifact_refs": with_refs}


def _count_frontiers() -> dict:
    """Count open vs resolved frontier questions."""
    path = ROOT / "tasks" / "FRONTIER.md"
    text = path.read_text(encoding="utf-8")
    active_section = re.split(r"^## Archive", text, flags=re.MULTILINE)[0]
    global_open = len(re.findall(r"^\s*-\s*\*\*F[\w-]+\*\*", active_section, re.MULTILINE))

    archive_path = ROOT / "tasks" / "FRONTIER-ARCHIVE.md"
    global_resolved = 0
    if archive_path.exists():
        archive_text = archive_path.read_text(encoding="utf-8")
        archive_rows = [
            l for l in archive_text.splitlines()
            if l.strip().startswith("|") and "---" not in l
            and "ID" not in l and "Answer" not in l
        ]
        global_resolved = len(archive_rows)

    domain_frontier_files = list(ROOT.glob("domains/*/tasks/FRONTIER.md"))
    domain_open = 0
    domain_resolved = 0
    for f in domain_frontier_files:
        t = f.read_text(encoding="utf-8")
        active_part = t.split("## Resolved")[0] if "## Resolved" in t else t
        domain_open += len(re.findall(r"^\s*-\s*\*\*F-?\w+\*\*", active_part, re.MULTILINE))
        if "## Resolved" in t:
            resolved_section = t.split("## Resolved", 1)[1]
            resolved_section = re.split(r"^## ", resolved_section, flags=re.MULTILINE)[0]
            rows = [
                l for l in resolved_section.splitlines()
                if l.strip().startswith("|") and "---" not in l
                and "ID" not in l and "Answer" not in l
                and "(none yet" not in l
            ]
            domain_resolved += len(rows)
    return {
        "global_open": global_open, "global_resolved": global_resolved,
        "domain_open": domain_open, "domain_resolved": domain_resolved,
    }


def _load_con1_baseline() -> dict:
    """Load F-CON1 conflict baseline — dynamic glob picks latest session artifact."""
    conflict_dir = ROOT / "experiments" / "conflict"
    candidates = sorted(conflict_dir.glob("f-con1-baseline-s*.json"))
    if not candidates:
        return {}
    data = json.loads(candidates[-1].read_text(encoding="utf-8"))
    # Normalize: older artifacts had c1_rate_lane_level at top level; newer nest it
    if "c1_rate_lane_level" not in data:
        nested = data.get("c1_duplicate_work", {}).get("rate_lane_level")
        if nested is not None:
            data["c1_rate_lane_level"] = nested
    data["_source_file"] = candidates[-1].name
    return data


def _count_lessons() -> int:
    """Count lesson files."""
    return len(list((ROOT / "memory" / "lessons").glob("L-*.md")))


def _count_domains() -> int:
    """Count domain directories."""
    return len([d for d in (ROOT / "domains").iterdir() if d.is_dir()])
