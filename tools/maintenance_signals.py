#!/usr/bin/env python3
"""maintenance_signals.py — Signal/queue/coordination checks extracted from maintenance.py (P-282)."""

import json
import re
import subprocess
from pathlib import Path

from maintenance_common import (
    REPO_ROOT, PYTHON_EXE, PYTHON_CMD,
    _read, _git, _exists, _truncated, _session_number,
    _python_command_runs, _py_launcher_runs, _command_exists,
    _tracked_changed_paths,
)


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
        last_session_raw = item.get("last_session", 0)
        try:
            last = int(str(last_raw).lstrip("S")) if last_raw else 0
        except (ValueError, TypeError):
            last = 0
        try:
            last2 = int(str(last_session_raw).lstrip("S")) if last_session_raw else 0
        except (ValueError, TypeError):
            last2 = 0
        last = max(last, last2)
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
