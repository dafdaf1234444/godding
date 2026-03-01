#!/usr/bin/env python3
"""
orient.py — Single-command session orientation for swarm nodes.

Synthesizes maintenance status, NEXT.md priorities, FRONTIER.md open questions,
and INDEX.md state counts into a decision-ready snapshot.

Replaces the manual pattern of: read NEXT.md + INDEX.md + FRONTIER.md + run maintenance.py.

Usage:
    python3 tools/orient.py                         # full orientation
    python3 tools/orient.py --brief                 # compact one-screen summary
    python3 tools/orient.py --classify "build X"   # route a task to domain+personality
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from swarm_cache import head_cache as _hcache
except ImportError:
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from swarm_cache import head_cache as _hcache
    except ImportError:
        _hcache = None
CORE_SWARM_TOOLS = (
    "tools/orient.py",
    "tools/maintenance.py",
    "tools/sync_state.py",
    "tools/validate_beliefs.py",
    "tools/check.sh",
    "tools/check.ps1",
    "tools/maintenance.sh",
    "tools/maintenance.ps1",
    "tools/compact.py",
    "tools/proxy_k.py",
    "tools/frontier_decay.py",
    "tools/swarm_pr.py",
    "tools/bulletin.py",
    "tools/merge_back.py",
    "tools/propagate_challenges.py",
    "tools/spawn_coordinator.py",
    "tools/colony.py",
    "tools/swarm_test.py",
    "tools/swarm_parse.py",
    "tools/change_quality.py",
    "tools/context_router.py",
    "tools/substrate_detect.py",
    "tools/kill_switch.py",
    "tools/task_recognizer.py",
)


def run_maintenance():
    """Run maintenance --quick and return stdout."""
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "maintenance.py"), "--quick"],
            capture_output=True, text=True, cwd=ROOT, timeout=15
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "[NOTICE] maintenance.py timed out (>15s) — check_uncommitted or check_mission_constraints likely slow on WSL"


def read_file(relpath):
    try:
        return (ROOT / relpath).read_text(encoding="utf-8")
    except Exception:
        return ""


def extract_state_line(index_text):
    """Extract session + counts from INDEX.md header."""
    session = "S?"
    m = re.search(r"Sessions:\s*(\d+)", index_text[:300])
    if m:
        session = f"S{m.group(1)}"
    counts = "?"
    m2 = re.search(r"(\d+)\s+lessons", index_text[:500])
    m3 = re.search(r"(\d+)\s+principles", index_text[:500])
    m4 = re.search(r"(\d+)\s+beliefs", index_text[:500])
    m5 = re.search(r"(\d+)\s+frontier", index_text[:500])
    parts = []
    if m2: parts.append(f"{m2.group(1)}L")
    if m3: parts.append(f"{m3.group(1)}P")
    if m4: parts.append(f"{m4.group(1)}B")
    if m5: parts.append(f"{m5.group(1)}F")
    counts = " ".join(parts) if parts else "?"
    return session, counts


def extract_next_priorities(next_text):
    """Extract numbered items from 'For next session' section."""
    m = re.search(r"## For next session\n(.*?)(?:\n##|\Z)", next_text, re.DOTALL)
    if not m:
        return []
    items = re.findall(r"^\d+\.\s+\*\*(.+?)\*\*", m.group(1), re.MULTILINE)
    if not items:
        items = re.findall(r"^\d+\.\s+(.+)$", m.group(1), re.MULTILINE)
    return [i[:100] for i in items[:6]]


def extract_key_state(next_text):
    """Extract key state lines (compact URGENT, counts, etc.)."""
    m = re.search(r"## Key state\n(.*?)(?:\n##|\Z)", next_text, re.DOTALL)
    if not m:
        return []
    lines = [l.strip("- ").strip() for l in m.group(1).splitlines()
             if l.strip().startswith("-")]
    return [l[:100] for l in lines[:4]]


def extract_critical_frontiers(frontier_text):
    """Extract Critical and Important frontier titles."""
    items = []
    for section in ("## Critical", "## Important"):
        m = re.search(rf"{re.escape(section)}\n(.*?)(?:\n##|\Z)", frontier_text, re.DOTALL)
        if not m:
            continue
        bullets = re.findall(r"^- \*\*(F\d+)\*\*:(.+)", m.group(1), re.MULTILINE)
        for fid, desc in bullets:
            first = desc.strip().split(".")[0][:80]
            items.append(f"{fid}: {first}")
    return items


def classify_maint(maint_out):
    """Return urgency level string from maintenance output."""
    if "URGENT" in maint_out:
        return "URGENT"
    if "[DUE]" in maint_out:
        return "DUE items present"
    if "[PERIODIC]" in maint_out:
        return "periodics due"
    return "NOTICE-only"


def extract_session_log_tail(log_text, n=10):
    """Return last N non-header session log lines (behavioral pattern signal)."""
    lines = [l for l in log_text.splitlines()
             if l.strip() and not l.startswith("#") and "|" in l]
    return lines[-n:]


def get_recent_commits(n=6):
    """Get recent commit summaries for collision-avoidance (L-251, L-283)."""
    result = subprocess.run(
        ["git", "log", "--oneline", f"-{n}"],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        return []
    commits = []
    for line in result.stdout.strip().splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append(parts[1])
    return commits


def get_current_session_from_git() -> int:
    """Derive current session number from git log (last committed session + 1).

    Fixes stale-lane detection bug: INDEX.md Sessions: N lags by one session,
    so lanes from session N aren't flagged as stale until sync_state.py runs.
    Using git log directly gives the correct boundary. (L-515, S347)
    """
    result = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode == 0:
        m = re.search(r"\[S(\d+)\]", result.stdout)
        if m:
            return int(m.group(1)) + 1
    return 0


def check_index_coverage(index_text):
    """Check INDEX.md theme bucket coverage vs total lesson count. F-BRN4.

    Returns a NOTICE string if coverage < 80%, or None if healthy.
    """
    # Extract total lesson count from INDEX.md header (e.g. "294 lessons")
    m_total = re.search(r"(\d+)\s+lessons", index_text[:500])
    if not m_total:
        return None
    total = int(m_total.group(1))
    if total == 0:
        return None

    # Sum the Count column of the Themes table
    # Table rows look like: | Theme | Count | Key insight |
    themed = 0
    bucket_sizes = {}
    in_theme_section = False
    for line in index_text.splitlines():
        if re.match(r"##\s+Themes", line):
            in_theme_section = True
            continue
        if in_theme_section and line.startswith("##"):
            break
        if in_theme_section:
            # Match table data rows (not header or separator)
            m_row = re.match(r"^\s*\|\s*(?![-|])\s*([^|]+?)\s*\|\s*(\d+)\s*\|", line)
            if m_row:
                count = int(m_row.group(2))
                themed += count
                bucket_sizes[m_row.group(1).strip()] = count

    if themed == 0:
        return None

    coverage = themed / total
    unthemed = total - themed
    notices = []
    if coverage < 0.80:
        pct = coverage * 100
        notices.append(
            f"INDEX.md dark matter: {unthemed}/{total} lessons unthemed "
            f"({pct:.1f}% coverage) — F-BRN4: hippocampal index degraded. "
            f"Split theme buckets >40 lessons."
        )
    oversized = [(name, n) for name, n in bucket_sizes.items() if n > 40]
    if oversized:
        buckets_str = ", ".join(f"{name}={n}" for name, n in oversized)
        notices.append(
            f"INDEX.md bucket overflow (F-BRN4): {buckets_str} — "
            f"split each into sub-themes ≤40L."
        )
    if notices:
        return "NOTICE: " + " | ".join(notices)
    return None


def check_stale_lanes(current_session: int) -> list:
    """Find ACTIVE lanes opened in a prior session — guaranteed stall signal (L-515).

    Uses cell-based status parsing (not substring match) and deduplicates by lane ID
    so that a MERGED closing row supersedes an earlier ACTIVE opening row. (S356 fix)
    """
    lanes_text = read_file("tasks/SWARM-LANES.md")
    ACTIVE_STATUSES = {"ACTIVE", "CLAIMED", "READY"}
    # Deduplicate: keep latest row per lane (append-only log — last row wins)
    latest_per_lane: dict[str, dict] = {}
    for line in lanes_text.splitlines():
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 12:
            continue
        status = cells[11].upper() if len(cells) > 11 else ""
        lane = cells[2] if len(cells) > 2 else ""
        if not lane or lane == "Lane":
            continue
        sess_field = cells[3] if len(cells) > 3 else ""
        m = re.search(r"S(\d+)", sess_field)
        if not m:
            continue
        lane_session = int(m.group(1))
        etc = cells[10] if len(cells) > 10 else ""
        artifact_m = re.search(r"artifact=([^;|]+)", etc)
        artifact = artifact_m.group(1).strip() if artifact_m else ""
        latest_per_lane[lane] = {"lane": lane, "opened": lane_session, "status": status, "artifact": artifact}
    stale = []
    for info in latest_per_lane.values():
        if info["status"] not in ACTIVE_STATUSES:
            continue
        if info["opened"] >= current_session:
            continue
        artifact = info["artifact"]
        # T3 guard (L-515): skip lesson refs (L-NNN) and directories — only check file paths
        if artifact and re.match(r"L-\d+", artifact):
            artifact_exists = True
        elif artifact and (ROOT / artifact).is_dir():
            artifact_exists = True
        else:
            artifact_exists = bool(artifact) and (ROOT / artifact).exists()
        gap = current_session - info["opened"]
        stale.append({"lane": info["lane"], "opened": info["opened"], "gap": gap, "artifact": artifact, "has_artifact": artifact_exists})
    return stale


def check_stale_experiments():
    """Scan domain frontier files for active (unrun) experiments. L-246."""
    if _hcache:
        cached = _hcache.get("stale_experiments")
        if cached is not None:
            return cached
    domain_dir = ROOT / "domains"
    if not domain_dir.exists():
        return []
    stale = []
    for frontier_file in sorted(domain_dir.glob("*/tasks/FRONTIER.md")):
        domain = frontier_file.parent.parent.name
        text = frontier_file.read_text(encoding="utf-8")
        active_m = re.search(r"## Active\n(.*?)(?:\n## |\Z)", text, re.DOTALL)
        if not active_m:
            continue
        active_block = active_m.group(1)
        seen = set()
        for line in active_block.splitlines():
            # Canonical frontier entry forms:
            # - **F-XXX1**: ...
            # - F-XXX1: ...
            # | F-XXX1 | ... |
            bullet_bold = re.match(r"^\s*[-*]\s+(~~)?\*\*(F-[A-Z]+\d+)\*\*(?:~~)?", line)
            bullet_plain = re.match(r"^\s*[-*]\s+(~~)?(F-[A-Z]+\d+)(?:~~)?\b", line)
            table_row = re.match(r"^\s*\|\s*(~~)?(F-[A-Z]+\d+)(?:~~)?\s*\|", line)
            m = bullet_bold or bullet_plain or table_row
            if not m:
                continue
            is_struck = bool(m.group(1))
            eid = m.group(2)
            if is_struck or eid in seen:
                continue
            # Treat frontiers with session-tagged evidence/artifacts as already run.
            # This avoids false "unrun" flags for active items carrying S### updates.
            has_run_evidence = (
                re.search(r"\bS\d+\b", line) is not None
                or "experiments/" in line
                or re.search(r"\.json\b", line) is not None
            )
            if has_run_evidence:
                seen.add(eid)
                continue
            stale.append(f"{domain}/{eid}")
            seen.add(eid)
    if _hcache:
        _hcache.set("stale_experiments", stale)
    return stale


def compute_pci(current_session: int) -> dict:
    """Compute Protocol Compliance Index — scientific rigor gap metric.

    PCI = EAD_compliance * belief_freshness * frontier_testability

    - EAD_compliance: fraction of last 20 MERGED lanes with actual= AND diff=
      (both non-TBD) in their Etc column.
    - belief_freshness: fraction of beliefs tested within last 50 sessions.
    - frontier_testability: fraction of active frontiers with session-tagged
      evidence (S\\d+ pattern) in their entry.

    Returns dict with {ead, belief_freshness, frontier_testability, pci, details}.
    """
    details = {}

    # --- EAD compliance (from SWARM-LANES.md) ---
    lanes_text = read_file("tasks/SWARM-LANES.md")
    # Parse table rows (pipe-delimited, skip header/separator)
    lane_rows = []
    for line in lanes_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        # Filter: need at least 12 columns (including empty edge cells),
        # skip header/separator rows
        if len(cells) < 12:
            continue
        if cells[1].startswith("---") or cells[1] == "Date":
            continue
        # cells[10] = Status, cells[9] = Etc (0-indexed after split, but
        # leading empty string from "|..." means cells[0]="" )
        status = cells[11] if len(cells) > 11 else ""
        etc = cells[10] if len(cells) > 10 else ""
        if not status.strip():
            continue
        lane_rows.append({"etc": etc, "status": status.strip()})

    # Take last 20 lanes (any status — the spec says "last 20 lanes")
    recent_lanes = lane_rows[-20:] if len(lane_rows) > 20 else lane_rows
    ead_compliant = 0
    ead_total = len(recent_lanes)
    for lr in recent_lanes:
        etc = lr["etc"]
        has_actual = bool(re.search(r"actual=(?!TBD)", etc))
        has_diff = bool(re.search(r"diff=(?!TBD)", etc))
        if has_actual and has_diff:
            ead_compliant += 1
    ead_score = ead_compliant / ead_total if ead_total > 0 else 0.0
    details["ead"] = f"{ead_compliant}/{ead_total}"

    # --- Belief freshness (from beliefs/DEPS.md) ---
    deps_text = read_file("beliefs/DEPS.md")
    fresh_count = 0
    total_beliefs = 0
    for block in re.split(r"\n(?=### B)", deps_text):
        bid_m = re.match(r"### (B[\w-]*\d+)", block)
        if not bid_m:
            continue
        # Skip superseded beliefs (strikethrough)
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
    # Collect active frontiers from Critical, Important, and Exploratory sections
    # (everything before ## Archive or ## Domain frontiers reference list)
    active_frontiers = 0
    evidenced_frontiers = 0
    # Parse frontier entries: lines starting with "- **F"
    # Consider sections: Critical, Important, Exploratory (stop at Archive)
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
        # Match frontier entry lines
        if re.match(r"^- \*\*F[\w-]+\*\*:", line):
            active_frontiers += 1
            # Check for session-tagged evidence (S followed by digits)
            if re.search(r"\bS\d+\b", line):
                evidenced_frontiers += 1
    ft_score = evidenced_frontiers / active_frontiers if active_frontiers > 0 else 0.0
    details["frontier_testability"] = f"{evidenced_frontiers}/{active_frontiers}"

    pci = ead_score * bf_score * ft_score

    return {
        "ead": ead_score,
        "belief_freshness": bf_score,
        "frontier_testability": ft_score,
        "pci": pci,
        "details": details,
    }


def check_stale_infrastructure(current_session: int, stale_threshold: int = 50) -> list:
    """Find protocol files and core tools not evolved in >stale_threshold sessions.

    CORE P14: total self-application — nothing is sacred infrastructure.
    Components that haven't been touched are candidates for challenge/compaction/evolution.

    Uses a single batched git log instead of per-file calls (31 subprocess calls
    → 1, saves ~5s on WSL cross-filesystem overhead).
    """
    infrastructure = [
        "SWARM.md",
        "beliefs/CORE.md",
        "beliefs/PHILOSOPHY.md",
        "beliefs/INVARIANTS.md",
    ] + list(CORE_SWARM_TOOLS)

    # Batch: get last 200 commits with their changed files in one call
    # HEAD-cached: git log only changes on new commits
    cache_key = f"git_log_name_only_200_s{stale_threshold}"
    if _hcache:
        cached = _hcache.get(cache_key)
        if cached is not None:
            file_last_session = cached
            stale = []
            for path in infrastructure:
                last_session = file_last_session.get(path)
                if last_session is None:
                    continue
                drift = current_session - last_session
                if drift > stale_threshold:
                    name = Path(path).name
                    stale.append(f"{name} (S{last_session}, {drift}s stale)")
            return stale

    result = subprocess.run(
        ["git", "log", "--format=%s", "--name-only", "-200"],
        capture_output=True, text=True, cwd=ROOT, timeout=10,
    )
    if result.returncode != 0:
        return []

    # Parse: map each file to its most recent session number
    file_last_session: dict[str, int] = {}
    current_msg = ""
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        m = re.search(r"\[S(\d+)\]", line)
        if m:
            current_msg = line
            continue
        # This is a filename line
        if current_msg:
            msg_m = re.search(r"\[S(\d+)\]", current_msg)
            if msg_m:
                sess = int(msg_m.group(1))
                fname = line.strip()
                if fname not in file_last_session:
                    file_last_session[fname] = sess

    # Cache the parsed file→session map
    if _hcache:
        _hcache.set(cache_key, file_last_session)

    stale = []
    for path in infrastructure:
        last_session = file_last_session.get(path)
        if last_session is None:
            continue
        drift = current_session - last_session
        if drift > stale_threshold:
            name = Path(path).name
            stale.append(f"{name} (S{last_session}, {drift}s stale)")
    return stale


def evaluate_session_triggers(current_session: int, maint_out: str = "",
                               stale_infra: list | None = None):
    """Read SESSION-TRIGGER.md and evaluate trigger conditions (L-640).

    Accepts pre-computed maint_out and stale_infra to avoid redundant subprocess
    calls (orient.py already runs these in main). Before this fix, maintenance.py
    was called 3 times per orient — ~60s on WSL. Now: 1 call, result reused.
    """
    trigger_path = ROOT / "domains" / "meta" / "SESSION-TRIGGER.md"
    if not trigger_path.exists():
        return None, []

    try:
        trigger_text = trigger_path.read_text(encoding="utf-8")
    except Exception:
        return None, []

    # Extract trigger definitions - look for lines with pattern "- **name**: description | urgency | ..."
    trigger_lines = []
    for line in trigger_text.splitlines():
        if line.startswith("- **") and ": " in line and " | " in line:
            trigger_lines.append(line)

    active_triggers = []
    urgency_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

    for line in trigger_lines:
        parts = line.split(" | ")
        if len(parts) < 2:
            continue

        name_desc = parts[0].replace("- **", "").replace("**", "")
        if ": " not in name_desc:
            continue

        trigger_name, description = name_desc.split(": ", 1)
        urgency = parts[1].strip()

        # Simple heuristic trigger evaluation based on current state
        triggered = False

        if trigger_name == "maintenance_due":
            if "[DUE]" in maint_out:
                triggered = True

        elif trigger_name == "stale_tools":
            stale = stale_infra if stale_infra is not None else check_stale_infrastructure(current_session, 50)
            if len(stale) > 10:
                triggered = True

        elif trigger_name == "periodics_due":
            if "[PERIODIC]" in maint_out and maint_out.count("~") > 5:
                triggered = True

        elif trigger_name == "dispatch_imbalance":
            triggered = True  # Common case - there are usually unworked domains

        elif trigger_name == "belief_staleness":
            stale_beliefs = check_stale_beliefs(current_session, 100)
            if len(stale_beliefs) > 0:
                triggered = True

        if triggered:
            active_triggers.append((trigger_name, description, urgency, urgency_order.get(urgency, 1)))

    # Sort by urgency descending
    active_triggers.sort(key=lambda x: x[3], reverse=True)

    top_trigger = active_triggers[0] if active_triggers else None
    return top_trigger, active_triggers[:5]


def check_stale_beliefs(current_session: int, stale_threshold: int = 50) -> list:
    """Find beliefs not tested in the last stale_threshold sessions. L-483."""
    deps_path = ROOT / "beliefs" / "DEPS.md"
    if not deps_path.exists():
        return []
    deps_text = deps_path.read_text(encoding="utf-8")
    stale = []
    for block in re.split(r"\n(?=### B\d)", deps_text):
        bid_m = re.match(r"### (B\d+)[^:]*: ([^\n]+)", block)
        if not bid_m:
            continue
        bid, desc = bid_m.group(1), bid_m.group(2)
        lt_m = re.search(r"\*\*Last tested\*\*: ([^\n]+)", block)
        if not lt_m:
            continue
        tested_text = lt_m.group(1)
        if "Not yet tested" in tested_text:
            continue
        sessions = [int(s) for s in re.findall(r"S(\d+)", tested_text)]
        if not sessions:
            continue
        last_session = max(sessions)
        drift = current_session - last_session
        if drift > stale_threshold:
            stale.append(f"{bid}: {desc[:45].strip()} (S{last_session}, {drift}s ago)")
    return stale


def check_underused_core_tools(log_text, window_sessions=20):
    """Find core swarm tools not referenced in recent session-log entries."""
    rows = []
    for raw in log_text.splitlines():
        m = re.match(r"^S(\d+)\b", raw)
        if m:
            rows.append((int(m.group(1)), raw.lower().replace("\\", "/")))
    if not rows:
        return [], None, None

    latest_session = max(sid for sid, _ in rows)
    start_session = max(1, latest_session - window_sessions + 1)
    haystack = "\n".join(text for sid, text in rows if sid >= start_session)

    underused = []
    for tool in CORE_SWARM_TOOLS:
        normalized = tool.lower().replace("\\", "/")
        filename = Path(normalized).name
        pattern = rf"(?<![A-Za-z0-9_])(?:{re.escape(normalized)}|{re.escape(filename)})(?![A-Za-z0-9_])"
        if not re.search(pattern, haystack):
            underused.append(tool)
    return underused, latest_session, start_session


def _get_classify_task() -> str | None:
    """Extract --classify value from sys.argv, or None."""
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg == "--classify" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--classify="):
            return arg[len("--classify="):]
    return None


def _run_classify(task: str) -> None:
    """Route a task description to domain + personality via task_recognizer."""
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        from task_recognizer import recognize  # type: ignore
    except ImportError:
        print("ERROR: tools/task_recognizer.py not found — cannot classify")
        return
    result = recognize(task)
    print(f"=== CLASSIFY: {task!r} ===")
    flag = "YES" if result["recognized"] else "NO"
    print(f"Recognized: {flag} | Confidence: {result['confidence']:.2f} | Personality: {result['personality']}")
    if result["routes"]:
        top = result["routes"][0]
        print(f"Primary domain: {top['domain']} (score {top['score']:.2f})")
        frontiers = top.get("open_frontiers", [])
        if frontiers:
            print(f"Open frontiers: {', '.join(frontiers[:3])}")
        if len(result["routes"]) > 1:
            alts = [f"{r['domain']}({r['score']:.2f})" for r in result["routes"][1:3]]
            print(f"Alternatives: {', '.join(alts)}")
    if result.get("new_domain_suggestion"):
        print(f"New domain suggestion: {result['new_domain_suggestion']}")


def _auto_repair_swarm_md() -> None:
    """Auto-repair WSL swarm.md corruption before running maintenance.
    Recurring pattern (every ~5-8 sessions): .claude/commands/swarm.md loses
    permissions or gets deleted on WSL /mnt/* repos. Fix: rm + git checkout HEAD.
    Silently repairs if needed; prints a one-line notice when it fires.
    """
    swarm_cmd = ROOT / ".claude" / "commands" / "swarm.md"
    needs_repair = False
    try:
        content = swarm_cmd.read_text(encoding="utf-8")
        if "# /swarm" not in content:
            needs_repair = True
    except (PermissionError, OSError, FileNotFoundError):
        needs_repair = True
    if needs_repair:
        import os
        try:
            if swarm_cmd.exists():
                os.remove(swarm_cmd)
        except OSError:
            pass
        result = subprocess.run(
            ["git", "checkout", "HEAD", "--", ".claude/commands/swarm.md"],
            capture_output=True, text=True, cwd=ROOT,
        )
        if result.returncode == 0:
            print("[orient] WSL swarm.md auto-repaired (rm + git checkout HEAD)")
        else:
            print(f"[orient] swarm.md repair failed: {result.stderr.strip()}")


def check_foreign_staged_deletions():
    """FM-09 guard: detect staged file deletions at session start.

    At orient time the node has not staged anything yet, so any staged
    deletions are foreign (left by a concurrent/interrupted session).
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--diff-filter=D", "--name-only"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return
        deleted = [l for l in result.stdout.strip().splitlines() if l.strip()]
        if not deleted:
            return
        count = len(deleted)
        print(f"--- !! FM-09: {count} foreign staged file deletion(s) detected ---")
        print("  These were staged by a concurrent/interrupted session, not by you.")
        for f in deleted[:10]:
            print(f"    D {f}")
        if count > 10:
            print(f"    ... and {count - 10} more")
        print("  Fix: git restore --staged . — to clear foreign staged state")
        print()
    except Exception:
        pass


def check_git_object_health():
    """FM-14 guard: detect loose object corruption at session start.

    WSL can corrupt git objects under heavy concurrent I/O (S364, L-658).
    Early detection prevents cascading failures during the session.
    """
    try:
        result = subprocess.run(
            ["git", "fsck", "--no-dangling", "--connectivity-only"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT),
        )
        # fsck outputs errors to stderr
        errors = result.stderr.strip() if result.stderr else ""
        if result.returncode != 0 or errors:
            error_lines = [l for l in errors.splitlines()
                           if l.strip() and not l.startswith("Checking")]
            if error_lines:
                print(f"--- !! FM-14: git object corruption detected ---")
                for line in error_lines[:10]:
                    print(f"    {line}")
                if len(error_lines) > 10:
                    print(f"    ... and {len(error_lines) - 10} more")
                print("  Fix: git reflog expire --expire=now --all && git gc --prune=now")
                print("  Or:  git clone <remote> fresh-copy (nuclear option)")
                print()
    except Exception:
        pass


def _scan_lesson_domains(lesson_dir: Path) -> dict:
    """Scan all lesson files and count domain tags."""
    lesson_domains: dict[str, int] = {}
    for lesson_file in lesson_dir.glob("L-*.md"):
        try:
            text = lesson_file.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"Domain:\s*([^|\n]+)", text)
            if not m:
                continue
            for d in re.split(r"[,/]", m.group(1)):
                d = re.sub(r"\s*\(.*?\)", "", d).strip().lower()
                if d:
                    lesson_domains[d] = lesson_domains.get(d, 0) + 1
        except Exception:
            continue
    return lesson_domains


def check_experiment_harvest_gap(threshold: int = 5) -> list:
    """F-IS7: warn when a domain has ≥threshold experiments but 0 lessons.

    Addresses the volume-conversion paradox (L-578): batch sweeps produce many
    experiments without triggering lesson extraction. Early warning prevents
    knowledge burial in zero-conversion domains.
    """
    exp_dir = ROOT / "experiments"
    lesson_dir = ROOT / "memory" / "lessons"
    if not exp_dir.exists() or not lesson_dir.exists():
        return []

    # Non-domain experiment subdirs to skip
    _EXP_SKIP = {"merge-reports", "complexity-applied", "inter-swarm", "spawn-quality",
                 "self-analysis", "children"}

    # Count experiments per domain
    exp_counts: dict[str, int] = {}
    for domain_dir in sorted(exp_dir.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name in _EXP_SKIP:
            continue
        domain = domain_dir.name
        count = sum(1 for f in domain_dir.iterdir()
                    if f.is_file() and f.suffix in (".json", ".md", ".py"))
        if count > 0:
            exp_counts[domain] = count

    # Count lesson domain tags per domain (HEAD-cached: lessons only change on commit)
    if _hcache:
        cached_ld = _hcache.get("lesson_domain_counts")
        if cached_ld is not None:
            lesson_domains = cached_ld
        else:
            lesson_domains = _scan_lesson_domains(lesson_dir)
            _hcache.set("lesson_domain_counts", lesson_domains)
    else:
        lesson_domains = _scan_lesson_domains(lesson_dir)

    # Only flag domains that have a real domain directory
    known_domains = {d.name for d in (ROOT / "domains").iterdir() if d.is_dir()} if (ROOT / "domains").exists() else set()

    gaps = []
    for domain, exp_count in sorted(exp_counts.items(), key=lambda x: -x[1]):
        if exp_count < threshold:
            continue
        if domain not in known_domains:
            continue
        lesson_count = lesson_domains.get(domain.lower(), 0)
        if lesson_count == 0:
            gaps.append((domain, exp_count))
    return gaps


def check_active_claims():
    """F-CON2: warn about active file claims from concurrent sessions.

    claim.py uses workspace/claims/ for soft-claim collision prevention.
    At orient time, show what's claimed so the current session avoids editing
    those files. Claims older than 5 min are expired (claim.py TTL).
    """
    import json as _json
    claims_dir = ROOT / "workspace" / "claims"
    if not claims_dir.exists():
        return
    my_pid = str(os.getpid())
    active = []
    for claim_file in sorted(claims_dir.glob("*.claim.json")):
        try:
            data = _json.loads(claim_file.read_text())
            # Skip expired claims (>5 min)
            import time as _time
            age = _time.time() - data.get("timestamp", 0)
            if age > 300:
                continue
            owner = data.get("pid", "?")
            if str(owner) == my_pid:
                continue
            filepath = data.get("file", claim_file.stem.replace("__", "/").replace(".claim", ""))
            active.append(f"{filepath} (pid {owner}, {int(age)}s ago)")
        except Exception:
            continue
    if active:
        print(f"--- Active claims ({len(active)} files locked by concurrent sessions) ---")
        for c in active[:8]:
            print(f"  🔒 {c}")
        print(f"  Use `python3 tools/claim.py claim <file>` before editing DUE files")
        print()


def _extract_open_signals(signals_text: str, current_session: int = 0) -> list:
    """Parse SIGNALS.md and return OPEN signals sorted by priority then recency."""
    results = []
    for line in signals_text.splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| ID"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 11:
            continue
        sig_id, _date, sess, _src, _tgt, sig_type, priority, content, status = (
            cols[1], cols[2], cols[3], cols[4], cols[5], cols[6], cols[7], cols[8], cols[9]
        )
        if status.upper() not in ("OPEN", "PARTIALLY RESOLVED"):
            continue
        age = 0
        m = re.search(r"S(\d+)", sess)
        if m and current_session > 0:
            age = current_session - int(m.group(1))
        results.append({"id": sig_id, "session": sess, "priority": priority,
                         "content": content, "age": age, "type": sig_type})
    # Sort: P1 first, then by age DESCENDING (oldest/most-neglected first within priority)
    # L-803: prior ascending sort buried 55-session-old P1 directives behind recent ones
    results.sort(key=lambda x: (0 if x["priority"] == "P1" else 1, -x["age"]))
    return results


def main():
    brief = "--brief" in sys.argv

    _auto_repair_swarm_md()

    # FM-09: detect foreign staged deletions before any work (L-350, F-CAT1)
    check_foreign_staged_deletions()

    # F-CON2: show active claims from concurrent sessions (collision prevention)
    check_active_claims()

    # FM-14: detect git object corruption at session start (WSL loose object, F-CAT1)
    check_git_object_health()

    classify_task = _get_classify_task()
    if classify_task:
        _run_classify(classify_task)
        return

    maint_out = run_maintenance()
    index_text = read_file("memory/INDEX.md")
    next_text = read_file("tasks/NEXT.md")
    frontier_text = read_file("tasks/FRONTIER.md")
    log_text = read_file("memory/SESSION-LOG.md")

    session, counts = extract_state_line(index_text)
    maint_level = classify_maint(maint_out)

    # Header
    print(f"=== ORIENT {session} | {counts} ===")
    print(f"Maintenance: {maint_level}")
    print()

    # Maintenance details (skip if NOTICE-only in brief mode)
    if not brief or maint_level != "NOTICE-only":
        signal_lines = [l for l in maint_out.splitlines()
                        if l.strip() and "===" not in l and "maintenance" not in l.lower()[:10]]
        if signal_lines:
            print("--- Maintenance ---")
            for line in signal_lines[:10]:
                print(f"  {line}")
            print()

    # Session triggers (F-META6: autonomous session initiation)
    try:
        sess_num_m = re.search(r"S(\d+)", session)
        if sess_num_m:
            top_trigger, active_triggers = evaluate_session_triggers(int(sess_num_m.group(1)), maint_out=maint_out)
            if top_trigger:
                print("--- Session Triggers (F-META6) ---")
                print(f"  🔴 {top_trigger[2]}: {top_trigger[0]} — {top_trigger[1][:80]}")
                if len(active_triggers) > 1:
                    print(f"  📋 {len(active_triggers)-1} additional triggers active")
                print()
    except Exception:
        pass

    # Open signals — L-703: SIGNALS.md was write-only / dead. Wire into orient.
    # L-803: sort oldest-first so neglected P1 signals surface; add backlog alert
    # L-808: old P1 signals surface as SIGNAL-DUE in suggested action
    open_signals = []
    try:
        signals_text = read_file("tasks/SIGNALS.md")
        open_signals = _extract_open_signals(signals_text, current_session=int(re.search(r"S(\d+)", session).group(1)) if re.search(r"S(\d+)", session) else 0)
        if open_signals:
            print(f"--- Open signals ({len(open_signals)} unresolved) ---")
            for sig in open_signals[:5]:
                age_tag = f" ({sig['age']}s ago)" if sig['age'] else ""
                print(f"  {'📢' if sig['priority'] == 'P1' else '📋'} {sig['id']}{age_tag}: {sig['content'][:90]}")
            if len(open_signals) > 5:
                print(f"  ... and {len(open_signals) - 5} more")
            neglected = [s for s in open_signals if s.get("age", 0) > 20]
            if neglected:
                p1_neg = [s for s in neglected if s["priority"] == "P1"]
                tag = f" including {len(p1_neg)} P1" if p1_neg else ""
                print(f"  ⚠ BACKLOG: {len(neglected)} signals >20s old{tag} — sensing without acting")
                print(f"    Oldest: {neglected[0]['id']} (age {neglected[0]['age']}s): {neglected[0]['content'][:60]}")
            print()
    except Exception:
        pass

    # INDEX.md coverage check (F-BRN4: hippocampal index health)
    index_notice = check_index_coverage(index_text)
    if index_notice:
        print(f"  {index_notice}")
        print()

    # PreCompact checkpoint notice (F-CC3, L-342)
    checkpoints = sorted((ROOT / "workspace").glob("precompact-checkpoint-*.json"))
    if checkpoints:
        latest = checkpoints[-1]
        import json as _json, subprocess as _sp
        try:
            cp = _json.loads(latest.read_text())
            ts = cp.get("timestamp", "?")
            trigger = cp.get("trigger", "?")
            uncommitted = cp.get("uncommitted_files", [])
            # Staleness check: verify how many files are actually still uncommitted
            if uncommitted:
                status_out = _sp.run(["git", "status", "--short"], capture_output=True, text=True, cwd=str(ROOT)).stdout
                status_files = {line.split()[-1] for line in status_out.strip().split("\n") if line.strip()}
                still_uncommitted = [f for f in uncommitted if f in status_files]
                stale_ratio = 1 - (len(still_uncommitted) / len(uncommitted)) if uncommitted else 1
            else:
                still_uncommitted = []
                stale_ratio = 1
            # Session-age filter: suppress checkpoints >2 sessions old
            import re as _re
            cp_session = 0
            for log_line in cp.get("recent_git_log", []):
                m = _re.search(r'\[S(\d+)\]', log_line)
                if m:
                    cp_session = int(m.group(1))
                    break
            cur_session_num = int(session[1:]) if session[1:].isdigit() else 0
            session_age = (cur_session_num - cp_session) if cp_session else 999
            # Suppress if <20% of files are still uncommitted OR checkpoint is >2 sessions old
            if stale_ratio < 0.8 and session_age <= 2:
                print(f"--- !! COMPACTION RESUME DETECTED ---")
                print(f"  Checkpoint: {latest.name} ({trigger} at {ts})")
                hint = cp.get("next_md", {}).get("For next session", "")
                if hint:
                    print(f"  In-flight: {hint[:120].splitlines()[0]}")
                if still_uncommitted:
                    print(f"  Uncommitted files ({len(still_uncommitted)}/{len(uncommitted)}): {', '.join(still_uncommitted[:5])}")
                print()
        except Exception:
            pass

    # Key state
    key_state = extract_key_state(next_text)
    if key_state:
        print("--- Key state ---")
        for s in key_state:
            print(f"  {s}")
        print()

    # Priorities
    priorities = extract_next_priorities(next_text)
    if priorities:
        print("--- Priorities ---")
        for i, p in enumerate(priorities, 1):
            print(f"  {i}. {p}")
        print()

    # Frontiers
    frontiers = extract_critical_frontiers(frontier_text)
    if frontiers:
        print("--- Open frontiers (critical/important) ---")
        for f in frontiers:
            print(f"  • {f}")
        print()

    # Stale beliefs — beliefs untested >50 sessions are invisible dispatch debt (L-483)
    try:
        sess_num_m = re.search(r"S(\d+)", session)
        if sess_num_m:
            stale_beliefs = check_stale_beliefs(int(sess_num_m.group(1)))
            if stale_beliefs:
                print(f"--- Stale beliefs ({len(stale_beliefs)} not re-tested >50 sessions) ---")
                for b in stale_beliefs[:5]:
                    print(f"  ⚠ {b}")
                print()
    except Exception:
        pass

    # Self-application check — CORE P14: infrastructure subject to swarm dynamics
    try:
        sess_sa_m = re.search(r"S(\d+)", session)
        if sess_sa_m:
            cur_s = int(sess_sa_m.group(1))
            stale_infra = check_stale_infrastructure(cur_s)
            if stale_infra:
                print(f"--- Self-application gap ({len(stale_infra)} components not evolved >50s) ---")
                for si in stale_infra:
                    print(f"  \u2298 {si}")
                # Emit actionable commands for top 3 stale tools (GAP-1 closure, L-561)
                if len(stale_infra) >= 1:
                    print(f"  Suggested (pick 1):")
                    for si in stale_infra[:3]:
                        tool_name = si.split("(")[0].strip().replace(" ", "-")
                        print(f"    python3 tools/open_lane.py --lane EVOLVE-{tool_name}-S{cur_s}"
                              f" --session S{cur_s}"
                              f" --expect 'modernize-{tool_name}'"
                              f" --artifact 'tools/{si.split('(')[0].strip()}'"
                              f" --intent 'P14: evolve stale infrastructure'")
                print()
    except Exception:
        pass

    # Stale lane check — L-515: cross-session open lanes = guaranteed stall
    # Use git-log session (not INDEX.md) so lanes from last session are correctly flagged
    # before sync_state.py runs. (Bug fix S347: INDEX.md lags by one session.)
    try:
        git_session = get_current_session_from_git()
        sess_stale_m = re.search(r"S(\d+)", session)
        current_sess_num = git_session if git_session > 0 else (int(sess_stale_m.group(1)) if sess_stale_m else 0)
        if current_sess_num > 0:
            stale_lanes = check_stale_lanes(current_sess_num)
            if stale_lanes:
                long_gap = [sl for sl in stale_lanes if sl.get("gap", 1) > 2]
                print(f"--- Stale lanes ({len(stale_lanes)} opened in prior session — execute or close) ---")
                for sl in stale_lanes:
                    art_note = "✗ artifact missing" if not sl["has_artifact"] else "✓ artifact exists"
                    gap = sl.get("gap", 1)
                    gap_warn = f" — GAP={gap}s ⚠ 67% abandon rate (L-733)" if gap > 2 else ""
                    print(f"  ⚠ {sl['lane']} (S{sl['opened']}) — {art_note}{gap_warn}")
                # Emit close commands for stale lanes without artifacts (GAP-1, L-561)
                closeable = [sl for sl in stale_lanes if not sl["has_artifact"]]
                if closeable:
                    print(f"  Close stale (no artifact):")
                    for sl in closeable[:3]:
                        print(f"    python3 tools/close_lane.py --lane {sl['lane']}"
                              f" --status ABANDONED --note 'stale — no artifact produced'")
                print()
    except Exception:
        pass

    # Scientific Rigor — Protocol Compliance Index (PCI)
    try:
        sess_pci_m = re.search(r"S(\d+)", session)
        if sess_pci_m:
            pci_result = compute_pci(int(sess_pci_m.group(1)))
            pci_val = pci_result["pci"]
            d = pci_result["details"]
            print("--- Scientific Rigor (PCI) ---")
            print(f"  PCI: {pci_val:.3f} (target >0.10)")
            print(f"  EAD field presence: {pci_result['ead']:.0%} ({d['ead']} lanes with actual+diff — L-813: measures field presence, not prediction quality)")
            print(f"  Belief freshness: {pci_result['belief_freshness']:.0%} ({d['belief_freshness']} tested <50 sessions)")
            print(f"  Frontier testability: {pci_result['frontier_testability']:.0%} ({d['frontier_testability']} with test evidence)")
            # Knowledge state from cached artifact — L-803: sensor must be read to sense
            try:
                import json as _json_pci
                ks_files = sorted((ROOT / "experiments" / "meta").glob("knowledge-state-s*.json"))
                if ks_files:
                    ks_data = _json_pci.loads(ks_files[-1].read_text())
                    ks_m = re.search(r"knowledge-state-s(\d+)", ks_files[-1].name)
                    ks_age = (int(sess_pci_m.group(1)) - int(ks_m.group(1))) if ks_m else -1
                    if 0 <= ks_age <= 20:
                        dist = ks_data.get("global_states", {})
                        total = sum(dist.values()) or 1
                        blind = dist.get("BLIND-SPOT", 0)
                        decayed = dist.get("DECAYED", 0)
                        age_note = f"S{ks_m.group(1)}" + (f", {ks_age}s ago" if ks_age > 0 else "")
                        print(f"  Knowledge attention ({age_note}): BLIND-SPOT {blind/total:.1%} | DECAYED {decayed/total:.1%} (L-813: citation-recency, not validity — actual false knowledge ~5-10%) | refresh: python3 tools/knowledge_state.py --json")
            except Exception:
                pass
            # Science quality from cached artifact — L-807: wired immediately (L-803 principle)
            try:
                sq_files = sorted((ROOT / "experiments" / "meta").glob("science-quality-s*.json"))
                if sq_files:
                    sq_data = _json_pci.loads(sq_files[-1].read_text())
                    sq_m = re.search(r"science-quality-s(\d+)", sq_files[-1].name)
                    sq_age = (int(sess_pci_m.group(1)) - int(sq_m.group(1))) if sq_m else -1
                    if -5 <= sq_age <= 30:
                        mean_q = sq_data.get("mean_quality", 0)
                        pre_reg = sq_data.get("criteria_means", {}).get("pre_registration", 0)
                        falsif = sq_data.get("falsification_lanes", "?/0")
                        age_note = f"S{sq_m.group(1)}" + (f", {sq_age}s ago" if sq_age > 0 else "")
                        print(f"  Science quality ({age_note}): mean {mean_q:.0%} | pre-reg {pre_reg:.0%} | falsif lanes {falsif} | refresh: python3 tools/science_quality.py --json")
            except Exception:
                pass
            # Bayesian calibration (L-903: ECE target <0.10; refresh every 10 sessions)
            try:
                bm_files = sorted((ROOT / "experiments" / "meta").glob("bayes-meta-s*.json"))
                if bm_files:
                    bm_data = _json_pci.loads(bm_files[-1].read_text())
                    bm_m = re.search(r"bayes-meta-s(\d+)", bm_files[-1].name)
                    bm_age = (int(sess_pci_m.group(1)) - int(bm_m.group(1))) if bm_m else -1
                    if -5 <= bm_age <= 30:
                        ece = bm_data.get("results", {}).get("ece", "?")
                        n_front = bm_data.get("n_frontiers_with_posteriors", "?")
                        age_note2 = f"S{bm_m.group(1)}" + (f", {bm_age}s ago" if bm_age > 0 else "")
                        ece_flag = " ⚠ OVERCONFIDENT" if isinstance(ece, float) and ece > 0.15 else ""
                        print(f"  Bayesian calibration ({age_note2}): ECE={ece:.3f}{ece_flag} | {n_front} frontiers | refresh: python3 tools/bayes_meta.py --json > experiments/meta/bayes-meta-s<N>.json")
            except Exception:
                pass
            if pci_val < 0.10:
                print(f"  Tip: check `beliefs/CHALLENGES.md` for untested beliefs and open a DOMEX lane")
            print()
    except Exception:
        pass

    # Prescription gap (L-831/L-843/L-875: enforcement_router with actionable filter)
    try:
        er_path = ROOT / "tools" / "enforcement_router.py"
        if er_path.exists():
            import subprocess as _sp
            er_result = _sp.run(
                [sys.executable, str(er_path), "--json", "--min-sharpe", "9"],
                capture_output=True, text=True, timeout=10
            )
            if er_result.returncode == 0:
                import json as _json_er
                er_data = _json_er.loads(er_result.stdout)
                act_rate = er_data.get("actionable_gap_rate", 0)
                n_act = er_data.get("actionable_aspirational_count", 0)
                n_obs = er_data.get("observational_aspirational_count", 0)
                n_asp = er_data.get("all_aspirational_count", 0)
                hs_asp = er_data.get("high_sharpe_aspirational", [])
                if act_rate > 0.15:
                    print(f"--- Prescription Gap (L-843) ---")
                    print(f"  ASPIRATIONAL (unimplemented): {act_rate:.0%} of rule-bearing lessons ({n_act} actionable, {n_obs} observational)")
                    # Show top actionable gap (L-875: filter observational)
                    act_gaps = [h for h in hs_asp if h.get("actionable")]
                    if act_gaps:
                        top = act_gaps[0]
                        print(f"  Top gap: {top['lesson']} Sh={top['sharpe']} — {top['rule'][:70]}")
                    print(f"  Full report: python3 tools/enforcement_router.py")
                    print()
    except Exception:
        pass

    # Level balance check (L-895/SIG-46: high-level swarming declining monotonically)
    try:
        import glob as _glob_lvl
        lesson_files = sorted(_glob_lvl.glob(str(ROOT / "memory" / "lessons" / "L-*.md")))
        if len(lesson_files) >= 10:
            recent_n = lesson_files[-10:]
            l2_kw = ["measure", "metric", "audit", "calibr", "precision", "accuracy",
                      "compliance", "drift", "ratio", "rate", "correlation", "r=",
                      "n=", "regression", "hypothesis", "replication", "falsif", "confirm"]
            l3plus_kw = ["strategy", "campaign", "architecture", "organizational",
                         "paradigm", "redesign", "direction", "what should", "reframing",
                         "missing layer", "system design", "philosophy", "identity"]
            l3plus_count = 0
            for lf in recent_n:
                try:
                    txt = Path(lf).read_text()
                    # Explicit level tag (highest signal — matches maintenance.py)
                    if re.search(r"[Ll]evel[=:\s]+L[3-5]", txt):
                        l3plus_count += 1
                        continue
                    # Keyword scan on full text (not truncated to 600 chars)
                    txt_lower = txt.lower()
                    if any(k in txt_lower for k in l3plus_kw):
                        l3plus_count += 1
                except Exception:
                    pass
            if l3plus_count == 0:
                print("--- Level Imbalance (L-895, SIG-46) ---")
                print(f"  ⚠ 0/{len(recent_n)} recent lessons at L3+ (strategy/architecture/paradigm)")
                print(f"  Swarm is 100% measurement. Consider: strategic direction, architecture review,")
                print(f"  or paradigm challenge instead of another DOMEX experiment.")
                print()
    except Exception:
        pass

    # Stalled 2-wave campaigns (F-STR3, L-845: 5th escalation layer)
    # Domain dispatch ≠ frontier routing. Surface stalled frontiers directly as DUE items
    # so nodes target them by name, bypassing novelty-bias in domain selection.
    stall_map: dict[str, str] = {}
    try:
        import subprocess as _sp_stall
        stall_result = _sp_stall.run(
            [sys.executable, str(ROOT / "tools" / "dispatch_optimizer.py"), "--json", "--all"],
            capture_output=True, text=True, timeout=15
        )
        if stall_result.returncode == 0:
            import json as _json_stall
            stall_data = _json_stall.loads(stall_result.stdout)
            # Flatten: {frontier_id: domain} for all 2-wave stalls
            for d in stall_data:
                for fid in (d.get("wave_2_stalls") or []):
                    stall_map[fid] = d["domain"]
    except Exception:
        pass
    if stall_map:
        print(f"--- Stalled Campaigns ({len(stall_map)} frontiers in 2-wave valley — 11% resolve) ---")
        for fid, dom in sorted(stall_map.items())[:8]:
            print(f"  ⚠ {fid} ({dom}) — needs hardening lane (mode shift required)")
        print(f"  Fix: open DOMEX-<DOM>-S<N> with --mode hardening for any of the above")
        print()

    # Stale domain experiments (L-246: design debt)
    stale_experiments = check_stale_experiments()
    if stale_experiments:
        print(f"--- Unrun domain experiments ({len(stale_experiments)}) ---")
        for e in stale_experiments[:6]:
            print(f"  ○ {e}")
        print()

    # Experiment harvest gap (F-IS7, L-578: volume-conversion paradox)
    try:
        harvest_gaps = check_experiment_harvest_gap(threshold=5)
        if harvest_gaps:
            print(f"--- Experiment harvest gap ({len(harvest_gaps)} domains: ≥5 experiments, 0 lessons) ---")
            for domain, count in harvest_gaps[:6]:
                print(f"  📦 {domain} ({count} experiments) — no lessons extracted yet")
            print()
    except Exception:
        pass

    # Underused core tools (session-log execution signal)
    underused_tools, latest_sid, start_sid = check_underused_core_tools(log_text)
    if underused_tools:
        window = "recent sessions"
        if latest_sid is not None and start_sid is not None:
            window = f"S{start_sid}..S{latest_sid}"
        print(f"--- Underused core tools ({len(underused_tools)} in {window}) ---")
        for tool in underused_tools[:6]:
            print(f"  ○ {tool}")
        print()

    # Recent commits — collision-avoidance for concurrent nodes (L-251)
    recent_commits = get_recent_commits()
    if recent_commits:
        print("--- Recent commits (avoid repeating) ---")
        for c in recent_commits:
            print(f"  ✓ {c[:100]}")
        print()

    # Session log tail (full mode only — last 10 entries = behavioral signal)
    if not brief and log_text:
        tail = extract_session_log_tail(log_text)
        if tail:
            print("--- Recent sessions (behavioral pattern) ---")
            for entry in tail:
                print(f"  {entry[:120]}")
            print()

    # Agent positions (S340 council: 5/5 convergence on agent registry)
    try:
        from agent_state import get_position_summary
        positions = get_position_summary()
        if positions:
            print(f"--- Active agents ({len(positions)}) ---")
            for p in positions:
                print(f"  {p['session']} → {p['domain']} ({p.get('lane', '?')})")
            # Collision detection
            domains = [p["domain"] for p in positions]
            dupes = [d for d in set(domains) if domains.count(d) > 1]
            if dupes:
                print(f"  ⚠ COLLISION: multiple agents on: {', '.join(dupes)}")
            print()
    except Exception:
        pass

    # dispatch_optimizer.py covers domain prioritization for orient.

    # Active sessions and task claims (L-686: cross-session visibility)
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from claim import get_active_sessions, get_active_task_claims
        sessions = get_active_sessions()
        task_claims = get_active_task_claims()
        if sessions or task_claims:
            print("--- Concurrent activity ---")
            if sessions:
                for s in sessions[:5]:
                    label = s.get("current_task", "(idle)")
                    if s.get("description"):
                        label += f": {s['description'][:40]}"
                    print(f"  {s['session']:15s} {s['age_s']:4d}s ago  {label}")
            if task_claims:
                print(f"  Task claims: {', '.join(task_claims.keys())}")
            print()
    except Exception:
        pass  # graceful degradation

    # Historian repair — SIG-39: all swarm helps meta historian/tooler/meta-x
    try:
        import subprocess as _sp_hist
        hr_result = _sp_hist.run(
            ["python3", "tools/historian_repair.py", "--json"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=15
        )
        if hr_result.returncode == 0:
            import json as _json_hist
            hr_data = _json_hist.loads(hr_result.stdout)
            high_items = [i for i in hr_data.get("items", []) if i.get("severity") == "HIGH"]
            if high_items:
                print(f"--- Historian repair ({hr_data.get('total', 0)} stale, {len(high_items)} HIGH) ---")
                cat_icons = {"beliefs": "🔴", "frontiers": "🟡", "domains": "⚪"}
                for item in high_items[:3]:
                    icon = cat_icons.get(item.get("category", ""), "○")
                    print(f"  {icon} [{item['item_id']}] {item['category']} — stale {item['sessions_stale']}s — {item['description'][:60]}")
                if len(high_items) > 3:
                    print(f"  ... and {len(high_items) - 3} more HIGH items")
                print(f"  Run: python3 tools/historian_repair.py")
                print()
    except Exception:
        pass

    # Suggested action
    print("--- Suggested next action ---")
    if "URGENT" in maint_out:
        # Find what's urgent
        urgent_lines = [l.strip() for l in maint_out.splitlines() if "URGENT" in l]
        for l in urgent_lines[:2]:
            print(f"  URGENT: {l}")
    elif "[DUE]" in maint_out:
        # Find the actual DUE item lines (marked with !)
        due_lines = [l.strip() for l in maint_out.splitlines() if l.strip().startswith("!")]
        for l in due_lines[:2]:
            print(f"  DUE: {l.lstrip('! ')}")
    elif open_signals and any(s["priority"] == "P1" and s.get("age", 0) > 30 for s in open_signals):
        # L-808: P1 signals >30 sessions old are structurally DUE — not just informational
        stale_p1 = [s for s in open_signals if s["priority"] == "P1" and s.get("age", 0) > 30]
        for s in stale_p1[:2]:
            print(f"  SIGNAL-DUE: {s['id']} ({s['age']}s old, P1): {s['content'][:70]}")
        print(f"  Resolve: `python3 tools/swarm_signal.py resolve {stale_p1[0]['id']} \"<resolution>\"`")
    elif "[PERIODIC]" in maint_out:
        periodic_lines = [l.strip() for l in maint_out.splitlines() if l.strip().startswith("~")]
        for l in periodic_lines[:2]:
            print(f"  PERIODIC: {l.lstrip('~ ')}")
    elif stall_map:
        # F-STR3/L-845: stalled 2-wave frontiers are higher-priority than domain dispatch
        top_fid, top_dom = next(iter(sorted(stall_map.items())))
        print(f"  STALL: {top_fid} ({top_dom}) in 2-wave valley — open hardening lane to escape (11%→31%)")
        if len(stall_map) > 1:
            print(f"  ({len(stall_map)} total stalled: {', '.join(sorted(stall_map)[:5])})")
    elif priorities:
        print(f"  {priorities[0]}")
    else:
        print("  State clean — pick a frontier or run a periodic")

    # F-META6/F-META9: write trigger manifest so external executors can read session-needed state
    try:
        _write_trigger_manifest(
            current_sess_num if 'current_sess_num' in locals() else 0,
            maint_out,
            stale_lanes if 'stale_lanes' in locals() else [],
            frontier_text=frontier_text if 'frontier_text' in locals() else ""
        )
    except Exception:
        pass


def _write_trigger_manifest(current_session: int, maint_out: str, stale_lanes: list,
                            frontier_text: str = "") -> None:
    """Update domains/meta/SESSION-TRIGGER.md with live trigger states (F-META6, F-META9).

    Evaluates all 7 triggers (T1-T7) and writes state to SESSION-TRIGGER.md
    so external executors (autoswarm.sh, cron) can determine if a session is needed.
    """
    trigger_path = ROOT / "domains" / "meta" / "SESSION-TRIGGER.md"
    if not trigger_path.exists():
        return
    try:
        content = trigger_path.read_text()
        now_sess = f"S{current_session}"

        def update_row(text: str, tid: str, state: str) -> str:
            import re as _re
            pattern = rf"(\| {_re.escape(tid)} \|[^|]+\|[^|]+\| ?)(FIRING|CLEAR|UNKNOWN)( ?\| S\d+)"
            repl = rf"\g<1>{state}\g<3>"
            new = _re.sub(pattern, repl, text)
            pattern2 = rf"(\| {_re.escape(tid)} \|[^|]+\|[^|]+\| ?(?:FIRING|CLEAR|UNKNOWN) ?\| )S\d+( \|)"
            return _re.sub(pattern2, rf"\g<1>{now_sess}\g<2>", new)

        # T1: Stale lanes opened in prior session without update
        t1 = "FIRING" if any(sl.get("opened", current_session) < current_session for sl in stale_lanes) else "CLEAR"
        content = update_row(content, "T1-STALE-LANE", t1)

        # T2: Active lane with artifact path but file missing on disk
        t2 = "FIRING" if any(not sl.get("has_artifact") and sl.get("artifact") for sl in stale_lanes) else "CLEAR"
        content = update_row(content, "T2-ARTIFACT-MISSING", t2)

        # T3: Maintenance DUE items present
        t3 = "FIRING" if "[DUE]" in maint_out and "!" in maint_out else "CLEAR"
        content = update_row(content, "T3-MAINTENANCE-DUE", t3)

        # T4: Anxiety-zone frontiers (open >15 sessions without update)
        t4 = "CLEAR"
        if frontier_text and current_session > 0:
            # Parse frontier blocks: each starts with "- **F"
            # Find max session reference per frontier, flag if >15 sessions stale
            anxiety_count = 0
            current_frontier_sessions = []
            for line in frontier_text.splitlines():
                if line.strip().startswith("- **F"):
                    # New frontier — check previous
                    if current_frontier_sessions:
                        max_s = max(current_frontier_sessions)
                        if current_session - max_s > 15:
                            anxiety_count += 1
                    current_frontier_sessions = []
                # Collect all S### references in this block
                for m in re.finditer(r'\bS(\d{2,4})\b', line):
                    s_num = int(m.group(1))
                    if 1 <= s_num <= current_session + 5:  # sanity bound
                        current_frontier_sessions.append(s_num)
            # Check last frontier
            if current_frontier_sessions:
                max_s = max(current_frontier_sessions)
                if current_session - max_s > 15:
                    anxiety_count += 1
            if anxiety_count > 0:
                t4 = "FIRING"
        content = update_row(content, "T4-ANXIETY-ZONE", t4)

        # T5: Top-3 dispatch domain has no active DOMEX lane
        t5 = "CLEAR"
        try:
            lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
            if lanes_path.exists():
                lanes_text = lanes_path.read_text(encoding="utf-8")
                has_active_domex = bool(re.search(r'DOMEX-[^|]+\| ACTIVE', lanes_text))
                if not has_active_domex:
                    t5 = "FIRING"
        except Exception:
            pass
        content = update_row(content, "T5-DISPATCH-GAP", t5)

        # T6: Health-check periodic overdue by >2 intervals (interval=5, so >10 sessions)
        t6 = "CLEAR"
        hc_match = re.search(r'\[health-check\].*last: S(\d+)', maint_out)
        if hc_match:
            hc_last = int(hc_match.group(1))
            if current_session - hc_last > 10:
                t6 = "FIRING"
        content = update_row(content, "T6-HEALTH-CHECK", t6)

        # T7: Proxy-K drift > 10% (check maintenance output for drift signals)
        t7 = "CLEAR"
        if "proxy" in maint_out.lower() and "URGENT" in maint_out:
            t7 = "FIRING"
        content = update_row(content, "T7-PROXY-K-DRIFT", t7)

        trigger_path.write_text(content)
    except Exception:
        pass  # trigger manifest is informational; never crash orient.py


if __name__ == "__main__":
    main()
