#!/usr/bin/env python3
"""Check functions extracted from orient.py (DOMEX-META-S423).

Contains: check_index_coverage, check_stale_lanes, check_stale_experiments,
check_stale_infrastructure, check_stale_beliefs, check_underused_core_tools,
check_foreign_staged_deletions, check_git_object_health,
check_experiment_harvest_gap, check_active_claims, _scan_lesson_domains.
"""

import json
import os
import re
import subprocess
import time
from pathlib import Path


def check_index_coverage(index_text):
    """Check INDEX.md theme bucket coverage vs total lesson count. F-BRN4."""
    m_total = re.search(r"(\d+)\s+lessons", index_text[:500])
    if not m_total:
        return None
    total = int(m_total.group(1))
    if total == 0:
        return None

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


def check_stale_lanes(current_session, ROOT, read_file):
    """Find ACTIVE lanes opened in a prior session — guaranteed stall signal (L-515)."""
    lanes_text = read_file("tasks/SWARM-LANES.md")
    ACTIVE_STATUSES = {"ACTIVE", "CLAIMED", "READY"}
    latest_per_lane = {}
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
        if artifact and re.match(r"L-\d+", artifact):
            artifact_exists = True
        elif artifact and (ROOT / artifact).is_dir():
            artifact_exists = True
        else:
            artifact_exists = bool(artifact) and (ROOT / artifact).exists()
        gap = current_session - info["opened"]
        stale.append({"lane": info["lane"], "opened": info["opened"], "gap": gap, "artifact": artifact, "has_artifact": artifact_exists})
    return stale


def check_stale_experiments(ROOT, _hcache=None):
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


def check_stale_infrastructure(current_session, ROOT, CORE_SWARM_TOOLS, _hcache=None, stale_threshold=50):
    """Find protocol files and core tools not evolved in >stale_threshold sessions."""
    infrastructure = [
        "SWARM.md",
        "beliefs/CORE.md",
        "beliefs/PHILOSOPHY.md",
        "beliefs/INVARIANTS.md",
    ] + list(CORE_SWARM_TOOLS)

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

    file_last_session = {}
    current_msg = ""
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        m = re.search(r"\[S(\d+)\]", line)
        if m:
            current_msg = line
            continue
        if current_msg:
            msg_m = re.search(r"\[S(\d+)\]", current_msg)
            if msg_m:
                sess = int(msg_m.group(1))
                fname = line.strip()
                if fname not in file_last_session:
                    file_last_session[fname] = sess

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


def check_stale_beliefs(current_session, ROOT, stale_threshold=50):
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


def check_underused_core_tools(log_text, CORE_SWARM_TOOLS, window_sessions=20):
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


def check_foreign_staged_deletions(ROOT):
    """FM-09 guard: detect staged file deletions at session start."""
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


def check_git_object_health(ROOT):
    """FM-14 guard: detect loose object corruption at session start."""
    try:
        result = subprocess.run(
            ["git", "fsck", "--no-dangling", "--connectivity-only"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT),
        )
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


def _scan_lesson_domains(lesson_dir):
    """Scan all lesson files and count domain tags."""
    lesson_domains = {}
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


def check_experiment_harvest_gap(ROOT, _hcache=None, threshold=5):
    """F-IS7: warn when a domain has >=threshold experiments but 0 lessons."""
    exp_dir = ROOT / "experiments"
    lesson_dir = ROOT / "memory" / "lessons"
    if not exp_dir.exists() or not lesson_dir.exists():
        return []

    _EXP_SKIP = {"merge-reports", "complexity-applied", "inter-swarm", "spawn-quality",
                 "self-analysis", "children"}

    exp_counts = {}
    for domain_dir in sorted(exp_dir.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name in _EXP_SKIP:
            continue
        domain = domain_dir.name
        count = sum(1 for f in domain_dir.iterdir()
                    if f.is_file() and f.suffix in (".json", ".md", ".py"))
        if count > 0:
            exp_counts[domain] = count

    if _hcache:
        cached_ld = _hcache.get("lesson_domain_counts")
        if cached_ld is not None:
            lesson_domains = cached_ld
        else:
            lesson_domains = _scan_lesson_domains(lesson_dir)
            _hcache.set("lesson_domain_counts", lesson_domains)
    else:
        lesson_domains = _scan_lesson_domains(lesson_dir)

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


def check_active_claims(ROOT):
    """F-CON2: warn about active file claims from concurrent sessions."""
    claims_dir = ROOT / "workspace" / "claims"
    if not claims_dir.exists():
        return
    my_pid = str(os.getpid())
    active = []
    for claim_file in sorted(claims_dir.glob("*.claim.json")):
        try:
            data = json.loads(claim_file.read_text())
            age = time.time() - data.get("timestamp", 0)
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


def check_stale_baselines(current_session: int, ROOT, stale_threshold: int = 50) -> list:
    """Scan tool Python files for hardcoded session-number fallbacks (FM-20, L-820).

    Detects hardcoded session-number fallbacks and epoch constants in tool source
    and flags those more than stale_threshold sessions behind current_session.
    Returns list of {file, line, value, age, pattern} dicts.
    """
    if current_session <= 0:
        return []
    tools_dir = ROOT / "tools"
    stale = []
    # Patterns that indicate hardcoded session numbers used as baselines/fallbacks
    patterns = [
        (re.compile(r'(?:return|=)\s+(\d{2,4})\s*#.*(?:fallback|baseline|from S)'), "fallback_comment"),
        (re.compile(r'(?:SESSION|session|EPOCH|epoch)\s*=\s*(\d{2,4})\b'), "session_constant"),
        (re.compile(r'estimated_sessions\s*=\s*(\d{2,4})\b'), "estimated_sessions"),
        (re.compile(r'current_sess(?:ion)?\s*=\s*(\d{2,4})\b'), "session_default"),
    ]
    for pyfile in sorted(tools_dir.glob("*.py")):
        if pyfile.name.startswith("archive"):
            continue
        try:
            lines = pyfile.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for lineno, line in enumerate(lines, 1):
            for pat, ptype in patterns:
                m = pat.search(line)
                if not m:
                    continue
                val = int(m.group(1))
                if val < 10 or val > current_session + 100:
                    continue  # skip non-session numbers
                age = current_session - val
                if age > stale_threshold:
                    stale.append({
                        "file": pyfile.name,
                        "line": lineno,
                        "value": val,
                        "age": age,
                        "pattern": ptype,
                    })
    stale.sort(key=lambda x: x["age"], reverse=True)
    return stale
