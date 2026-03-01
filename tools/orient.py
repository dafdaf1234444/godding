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
    "tools/citation_retrieval.py",
    "tools/session_classifier.py",
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
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_index_coverage as _impl
    return _impl(index_text)


def check_stale_lanes(current_session: int) -> list:
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_stale_lanes as _impl
    return _impl(current_session, ROOT, read_file)


def check_stale_experiments():
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_stale_experiments as _impl
    return _impl(ROOT, _hcache)


def compute_pci(current_session: int) -> dict:
    # Extracted to orient_pci.py (DOMEX-META-S423)
    from orient_pci import compute_pci as _impl
    return _impl(current_session, ROOT, read_file)


def check_stale_infrastructure(current_session: int, stale_threshold: int = 50) -> list:
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_stale_infrastructure as _impl
    return _impl(current_session, ROOT, CORE_SWARM_TOOLS, _hcache, stale_threshold)


def evaluate_session_triggers(current_session: int, maint_out: str = "",
                               stale_infra: list | None = None):
    # Extracted to orient_triggers.py (DOMEX-META-S423)
    from orient_triggers import evaluate_session_triggers as _impl
    from orient_checks import check_stale_beliefs
    return _impl(current_session, ROOT, maint_out, stale_infra, check_stale_beliefs)


def check_stale_beliefs(current_session: int, stale_threshold: int = 50) -> list:
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_stale_beliefs as _impl
    return _impl(current_session, ROOT, stale_threshold)


def check_underused_core_tools(log_text, window_sessions=20):
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_underused_core_tools as _impl
    return _impl(log_text, CORE_SWARM_TOOLS, window_sessions)


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
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_foreign_staged_deletions as _impl
    _impl(ROOT)


def check_git_object_health():
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_git_object_health as _impl
    _impl(ROOT)


def check_experiment_harvest_gap(threshold: int = 5) -> list:
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_experiment_harvest_gap as _impl
    return _impl(ROOT, _hcache, threshold)


def check_active_claims():
    # Extracted to orient_checks.py (DOMEX-META-S423)
    from orient_checks import check_active_claims as _impl
    _impl(ROOT)


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

    # Meta-tooler scan — SIG-39: symmetric with historian repair
    try:
        import subprocess as _sp_mt
        mt_result = _sp_mt.run(
            ["python3", "tools/meta_tooler.py", "--json"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30
        )
        if mt_result.returncode == 0:
            import json as _json_mt
            mt_data = _json_mt.loads(mt_result.stdout)
            mt_high = mt_data.get("high", 0)
            mt_med = mt_data.get("medium", 0)
            if mt_high > 0 or mt_med > 5:
                print(f"--- Meta-tooler ({mt_data['total_tools']} tools, "
                      f"HIGH={mt_high} MEDIUM={mt_med}) ---")
                for f in mt_data.get("findings", []):
                    if f["severity"] == "HIGH":
                        print(f"  🔴 [{f['category']}] {f['tool']}: {f['message']}")
                print(f"  Run: python3 tools/meta_tooler.py")
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
    # Extracted to orient_triggers.py (DOMEX-META-S423)
    from orient_triggers import write_trigger_manifest as _impl
    _impl(current_session, maint_out, stale_lanes, ROOT, frontier_text)


if __name__ == "__main__":
    main()
