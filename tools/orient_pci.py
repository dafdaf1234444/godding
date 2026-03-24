#!/usr/bin/env python3
"""PCI computation — prediction quality scoring (L-813, L-1526, L-1536).

L-1526: EAD field presence != prediction quality. PCI uses ead_quality
(blended presence + classifiability) instead of raw presence.
L-1536: Epistemic yield — PCI must measure whether falsifications lead to
learning (lesson updates), not just whether predictions are classifiable.

PCI = ead_quality * belief_freshness * frontier_testability * epistemic_yield_factor
"""

import json
import os
import re
from pathlib import Path


def _walk_json_files(exp_root, session_filter=None):
    """Walk experiment directory for JSON files — faster than rglob on WSL/NTFS.
    If session_filter=(min_sess, max_sess), skip files outside that session range
    based on filename pattern *-s{N}.json to avoid stat()ing 1400+ files."""
    _sess_re = re.compile(r"-s(\d+)\.json$", re.I) if session_filter else None
    for dirpath, _dirnames, filenames in os.walk(exp_root):
        for fn in filenames:
            if not fn.endswith(".json"):
                continue
            if _sess_re and session_filter:
                m = _sess_re.search(fn)
                if m:
                    s = int(m.group(1))
                    if s < session_filter[0] or s > session_filter[1]:
                        continue
            yield Path(dirpath) / fn

_FALSIF = re.compile(r"(?:FALSIF|unexpected|surprise|not.{0,10}predict|exceeded|didn.t match|wrong|incorrect)", re.I)
_CONFIRM = re.compile(r"(?:confirm|as expected|matched|expectation met|predicted.{0,10}correct|SUPPORTED)", re.I)
_PARTIAL = re.compile(r"(?:partial|partly|mixed|nuanced)", re.I)


def _scan_experiment_verdicts(root, current_session, window=20):
    """Scan experiment JSONs from recent sessions for verdict fields."""
    counts = {"confirmed": 0, "falsified": 0, "partial": 0, "total": 0}
    min_session = current_session - window
    exp_root = root / "experiments"
    if not exp_root.exists():
        return counts
    for jf in _walk_json_files(exp_root, session_filter=(min_session, current_session)):
        try:
            data = json.loads(jf.read_text())
        except Exception:
            continue
        _res = data.get("result", {})
        _act = data.get("actual", {})
        verdict = (data.get("verdict")
                   or (_res.get("verdict") if isinstance(_res, dict) else "")
                   or (_act.get("verdict") if isinstance(_act, dict) else "")
                   or "")
        if not verdict:
            continue
        counts["total"] += 1
        v = str(verdict)
        if _FALSIF.search(v):
            counts["falsified"] += 1
        elif _PARTIAL.search(v):
            counts["partial"] += 1
        elif _CONFIRM.search(v):
            counts["confirmed"] += 1
    return counts


def _compute_epistemic_yield(root, current_session, window=20):
    """Measure whether falsifications lead to lesson updates.

    Scans experiments with falsified verdicts in recent window, then checks
    if the frontier referenced in each experiment has a corresponding lesson
    citing it. Yield = falsifications_with_followup / total_falsifications.

    Returns dict with {yield_rate, falsified_with_lesson, total_falsified, details}.
    """
    exp_root = root / "experiments"
    lessons_root = root / "memory" / "lessons"
    if not exp_root.exists():
        return {"yield_rate": 1.0, "falsified_with_lesson": 0, "total_falsified": 0, "details": []}

    min_session = current_session - window
    falsified_frontiers = []

    # Collect falsified experiments and their frontier references
    for jf in _walk_json_files(exp_root, session_filter=(min_session, current_session)):
        try:
            data = json.loads(jf.read_text())
        except Exception:
            continue
        _res = data.get("result", {})
        _act = data.get("actual", {})
        verdict = (data.get("verdict")
                   or (_res.get("verdict") if isinstance(_res, dict) else "")
                   or (_act.get("verdict") if isinstance(_act, dict) else "")
                   or "")
        if not verdict or not _FALSIF.search(str(verdict)):
            continue
        # Extract frontier ID from experiment
        frontier = data.get("frontier") or data.get("frontier_id") or ""
        if not frontier:
            # Try to extract from filename (e.g., f-epis3-...-s529.json)
            fm = re.match(r"(f-[\w]+-?\d*)", jf.stem, re.I)
            if fm:
                frontier = fm.group(1).upper().replace("-", "-")
        if frontier:
            falsified_frontiers.append(frontier)

    if not falsified_frontiers:
        return {"yield_rate": 1.0, "falsified_with_lesson": 0, "total_falsified": 0, "details": []}

    # Check which falsified frontiers have RECENT lesson follow-ups
    # Only count lessons from within the session window (not all-time)
    recent_lesson_text = ""
    if lessons_root.exists():
        for lf in lessons_root.glob("L-*.md"):
            try:
                txt = lf.read_text()
                # Extract session from lesson header (Session: S529)
                sm = re.search(r"Session:\s*S(\d+)", txt)
                if sm and int(sm.group(1)) >= min_session:
                    recent_lesson_text += txt + "\n"
            except Exception:
                continue

    followed_up = 0
    detail_rows = []
    seen = set()
    for fid in falsified_frontiers:
        if fid in seen:
            continue
        seen.add(fid)
        # Check if a recent lesson references this frontier
        has_lesson = bool(re.search(re.escape(fid), recent_lesson_text, re.I))
        if has_lesson:
            followed_up += 1
        detail_rows.append({"frontier": fid, "has_lesson": has_lesson})

    total = len(seen)
    yield_rate = followed_up / total if total > 0 else 1.0

    return {
        "yield_rate": yield_rate,
        "falsified_with_lesson": followed_up,
        "total_falsified": total,
        "details": detail_rows,
    }


def compute_pci(current_session, ROOT, read_file):
    """Compute Protocol Compliance Index — scientific rigor metric.

    PCI = ead_quality * belief_freshness * frontier_testability * epistemic_yield_factor

    epistemic_yield_factor = 0.5 + 0.5 * yield_rate (floor of 0.5 so doing
    science without follow-up still gets partial credit).

    Returns dict with {ead, ead_quality, belief_freshness, frontier_testability,
    epistemic_yield, pci, pred_quality, details}.
    """
    details = {}

    # --- EAD compliance (from SWARM-LANES.md) ---
    lanes_text = read_file("tasks/SWARM-LANES.md")
    lane_rows = []
    for line in lanes_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 12:
            continue
        if cells[1].startswith("---") or cells[1] == "Date":
            continue
        status = cells[11] if len(cells) > 11 else ""
        etc = cells[10] if len(cells) > 10 else ""
        if not status.strip():
            continue
        lane_rows.append({"etc": etc, "status": status.strip()})

    recent_lanes = lane_rows[-20:] if len(lane_rows) > 20 else lane_rows
    ead_compliant = 0
    ead_total = len(recent_lanes)
    pc, pf, pp = 0, 0, 0
    for lr in recent_lanes:
        etc = lr["etc"]
        has_actual = bool(re.search(r"actual=(?!TBD)", etc))
        has_diff = bool(re.search(r"diff=(?!TBD)", etc))
        if has_actual and has_diff:
            ead_compliant += 1
            dm = re.search(r"diff=([^;|]+)", etc)
            ds = dm.group(1) if dm else ""
            if _FALSIF.search(ds):
                pf += 1
            elif _PARTIAL.search(ds):
                pp += 1
            elif _CONFIRM.search(ds):
                pc += 1

    ead_presence = ead_compliant / ead_total if ead_total > 0 else 0.0
    details["ead"] = f"{ead_compliant}/{ead_total}"

    # --- Experiment-JSON verdict scanning (richer than lane diff= text) ---
    exp_verdicts = _scan_experiment_verdicts(ROOT, current_session)

    if exp_verdicts["total"] > 0:
        ec = exp_verdicts["confirmed"]
        ef = exp_verdicts["falsified"]
        ep = exp_verdicts["partial"]
        exp_total = exp_verdicts["total"]
        classifiable_rate = (ec + ef + ep) / exp_total
    elif ead_compliant > 0:
        ec, ef, ep = pc, pf, pp
        exp_total = ead_compliant
        classifiable_rate = (pc + pf + pp) / ead_compliant
    else:
        ec, ef, ep, exp_total = 0, 0, 0, 0
        classifiable_rate = 0.0

    sr = (ef + ep) / (ec + ef + ep) if (ec + ef + ep) > 0 else 0.0

    # EAD quality = presence * classifiability blend (L-1526)
    ead_quality = ead_presence * (0.5 + 0.5 * classifiable_rate)
    details["ead_quality"] = f"{ead_quality:.0%}"

    pred_quality = {
        "confirmed": ec, "falsified": ef, "partial": ep,
        "unclassified": exp_total - ec - ef - ep, "total": exp_total,
        "surprise_rate": round(sr, 3),
        "classifiable_rate": round(classifiable_rate, 3),
        "source": "experiments" if exp_verdicts["total"] > 0 else "lanes",
    }

    # --- Belief freshness (from beliefs/DEPS.md) ---
    deps_text = read_file("beliefs/DEPS.md")
    fresh_count = 0
    total_beliefs = 0
    for block in re.split(r"\n(?=### B)", deps_text):
        bid_m = re.match(r"### (B[\w-]*\d+)", block)
        if not bid_m:
            continue
        if "~~" in block.split("\n")[0]:
            continue
        total_beliefs += 1
        lt_m = re.search(r"\*\*Last tested\*\*:\s*([^\n]+)", block)
        if not lt_m:
            continue
        tested_text = lt_m.group(1)
        if "Not yet tested" in tested_text:
            continue
        sessions = [int(s) for s in re.findall(r"S(\d+)", tested_text)]
        if not sessions:
            continue
        last_session = max(sessions)
        if current_session - last_session <= 50:
            fresh_count += 1
    bf_score = fresh_count / total_beliefs if total_beliefs > 0 else 0.0
    details["belief_freshness"] = f"{fresh_count}/{total_beliefs}"

    # --- Frontier testability (from tasks/FRONTIER.md) ---
    frontier_text = read_file("tasks/FRONTIER.md")
    active_frontiers = 0
    evidenced_frontiers = 0
    in_active_section = False
    for line in frontier_text.splitlines():
        if re.match(r"^## (Critical|Important|Exploratory)", line):
            in_active_section = True
            continue
        if re.match(r"^## (Archive|Domain frontiers)", line):
            in_active_section = False
            continue
        if not in_active_section:
            continue
        if re.match(r"^- \*\*F[\w-]+\*\*:", line):
            active_frontiers += 1
            if re.search(r"\bS\d+\b", line):
                evidenced_frontiers += 1
    ft_score = evidenced_frontiers / active_frontiers if active_frontiers > 0 else 0.0
    details["frontier_testability"] = f"{evidenced_frontiers}/{active_frontiers}"

    # --- Epistemic yield (falsification → learning rate) ---
    ey = _compute_epistemic_yield(ROOT, current_session)
    ey_factor = 0.5 + 0.5 * ey["yield_rate"]
    details["epistemic_yield"] = f"{ey['falsified_with_lesson']}/{ey['total_falsified']}" if ey["total_falsified"] > 0 else "n/a"

    pci = ead_quality * bf_score * ft_score * ey_factor

    return {
        "ead": ead_presence,
        "ead_quality": ead_quality,
        "belief_freshness": bf_score,
        "frontier_testability": ft_score,
        "epistemic_yield": ey,
        "epistemic_yield_factor": ey_factor,
        "pci": pci,
        "pred_quality": pred_quality,
        "details": details,
    }
