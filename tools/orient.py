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

Modules (extracted DOMEX-META-S423/S426):
    orient_state.py     — state extraction utilities (read_file, extract_*, signals)
    orient_sections.py  — display section functions (each returns list[str])
    orient_checks.py    — health/staleness check functions
    orient_pci.py       — Protocol Compliance Index computation
    orient_triggers.py  — session trigger evaluation + manifest writing
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


# --- Backwards-compat wrappers (orient_state.py, DOMEX-META-S426) ---

def run_maintenance():
    from orient_state import run_maintenance as _impl
    return _impl()

def read_file(relpath):
    from orient_state import read_file as _impl
    return _impl(relpath)

def extract_state_line(index_text):
    from orient_state import extract_state_line as _impl
    return _impl(index_text)

def extract_next_priorities(next_text):
    from orient_state import extract_next_priorities as _impl
    return _impl(next_text)

def extract_key_state(next_text):
    from orient_state import extract_key_state as _impl
    return _impl(next_text)

def extract_critical_frontiers(frontier_text):
    from orient_state import extract_critical_frontiers as _impl
    return _impl(frontier_text)

def classify_maint(maint_out):
    from orient_state import classify_maint as _impl
    return _impl(maint_out)

def extract_session_log_tail(log_text, n=10):
    from orient_state import extract_session_log_tail as _impl
    return _impl(log_text, n)

def get_recent_commits(n=6):
    from orient_state import get_recent_commits as _impl
    return _impl(n)

def get_current_session_from_git() -> int:
    from orient_state import get_current_session_from_git as _impl
    return _impl()

def _extract_open_signals(signals_text: str, current_session: int = 0) -> list:
    from orient_state import extract_open_signals as _impl
    return _impl(signals_text, current_session)


# --- Backwards-compat wrappers (orient_checks.py, DOMEX-META-S423) ---

def check_index_coverage(index_text):
    from orient_checks import check_index_coverage as _impl
    return _impl(index_text)

def check_stale_lanes(current_session: int) -> list:
    from orient_checks import check_stale_lanes as _impl
    return _impl(current_session, ROOT, read_file)

def check_stale_experiments():
    from orient_checks import check_stale_experiments as _impl
    return _impl(ROOT, _hcache)

def compute_pci(current_session: int) -> dict:
    from orient_pci import compute_pci as _impl
    return _impl(current_session, ROOT, read_file)

def check_stale_infrastructure(current_session: int, stale_threshold: int = 50) -> list:
    from orient_checks import check_stale_infrastructure as _impl
    return _impl(current_session, ROOT, CORE_SWARM_TOOLS, _hcache, stale_threshold)

def evaluate_session_triggers(current_session: int, maint_out: str = "",
                               stale_infra: list | None = None):
    from orient_triggers import evaluate_session_triggers as _impl
    from orient_checks import check_stale_beliefs
    return _impl(current_session, ROOT, maint_out, stale_infra, check_stale_beliefs)

def check_stale_beliefs(current_session: int, stale_threshold: int = 50) -> list:
    from orient_checks import check_stale_beliefs as _impl
    return _impl(current_session, ROOT, stale_threshold)

def check_underused_core_tools(log_text, window_sessions=20):
    from orient_checks import check_underused_core_tools as _impl
    return _impl(log_text, CORE_SWARM_TOOLS, window_sessions)

def check_foreign_staged_deletions():
    from orient_checks import check_foreign_staged_deletions as _impl
    _impl(ROOT)

def check_git_object_health():
    from orient_checks import check_git_object_health as _impl
    _impl(ROOT)

def check_experiment_harvest_gap(threshold: int = 5) -> list:
    from orient_checks import check_experiment_harvest_gap as _impl
    return _impl(ROOT, _hcache, threshold)

def check_active_claims():
    from orient_checks import check_active_claims as _impl
    _impl(ROOT)

def check_stale_baselines(current_session: int, stale_threshold: int = 50) -> list:
    from orient_checks import check_stale_baselines as _impl
    return _impl(current_session, ROOT, stale_threshold)


# --- Classify (kept inline — small, orient-specific) ---

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


# --- WSL auto-repair (kept inline — WSL-specific) ---

def _auto_repair_swarm_md() -> None:
    """Auto-repair WSL swarm.md corruption before running maintenance."""
    swarm_cmd = ROOT / ".claude" / "commands" / "swarm.md"
    needs_repair = False
    try:
        content = swarm_cmd.read_text(encoding="utf-8")
        if "# /swarm" not in content:
            needs_repair = True
    except (PermissionError, OSError, FileNotFoundError):
        needs_repair = True
    if needs_repair:
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


# --- Trigger manifest wrapper ---

def _write_trigger_manifest(current_session: int, maint_out: str, stale_lanes: list,
                            frontier_text: str = "") -> None:
    from orient_triggers import write_trigger_manifest as _impl
    _impl(current_session, maint_out, stale_lanes, ROOT, frontier_text)


# --- Main: thin coordinator calling section functions ---

def _print_lines(lines):
    """Print a list of output lines."""
    for line in lines:
        print(line)


def main():
    brief = "--brief" in sys.argv

    _auto_repair_swarm_md()

    # Pre-checks (print directly via orient_checks)
    check_foreign_staged_deletions()
    check_active_claims()
    check_git_object_health()

    # Classify mode
    classify_task = _get_classify_task()
    if classify_task:
        _run_classify(classify_task)
        return

    # Gather state
    from orient_state import (
        run_maintenance as _run_maint, read_file as _read,
        extract_state_line as _state, classify_maint as _classify,
        extract_key_state as _key_state, extract_next_priorities as _priorities,
        extract_critical_frontiers as _frontiers, get_recent_commits as _commits,
        get_current_session_from_git as _git_session, extract_open_signals as _signals,
    )
    from orient_sections import (
        section_maintenance, section_session_triggers, section_open_signals,
        section_index_coverage, section_precompact_checkpoint, section_key_state,
        section_priorities, section_frontiers, section_stale_beliefs,
        section_self_application, section_stale_lanes, section_pci,
        section_prescription_gap, section_level_balance, section_stalled_campaigns,
        section_stale_experiments, section_experiment_harvest_gap, section_stale_baselines,
        section_underused_tools, section_recent_commits, section_session_log_tail,
        section_agent_positions, section_concurrent_activity, section_historian_repair,
        section_meta_tooler, section_suggested_action,
    )

    maint_out = _run_maint()
    index_text = _read("memory/INDEX.md")
    next_text = _read("tasks/NEXT.md")
    frontier_text = _read("tasks/FRONTIER.md")
    log_text = _read("memory/SESSION-LOG.md")
    signals_text = _read("tasks/SIGNALS.md")

    session, counts = _state(index_text)
    maint_level = _classify(maint_out)
    sess_m = re.search(r"S(\d+)", session)
    sess_num = int(sess_m.group(1)) if sess_m else 0

    # Header
    print(f"=== ORIENT {session} | {counts} ===")
    print(f"Maintenance: {maint_level}")
    print()

    # Display sections — each returns list[str]
    _print_lines(section_maintenance(maint_out, maint_level, brief))

    if sess_num:
        _print_lines(section_session_triggers(sess_num, maint_out, evaluate_session_triggers))

    open_signals = _signals(signals_text, current_session=sess_num)
    _print_lines(section_open_signals(open_signals))

    _print_lines(section_index_coverage(index_text, check_index_coverage))
    _print_lines(section_precompact_checkpoint(session))

    _print_lines(section_key_state(_key_state(next_text)))

    priorities = _priorities(next_text)
    _print_lines(section_priorities(priorities))

    _print_lines(section_frontiers(_frontiers(frontier_text)))

    if sess_num:
        _print_lines(section_stale_beliefs(sess_num, check_stale_beliefs))
        _print_lines(section_self_application(sess_num, check_stale_infrastructure))

    # Stale lanes — need return value for trigger manifest
    git_session = _git_session()
    current_sess_num = git_session if git_session > 0 else sess_num
    stale_lanes = []
    if current_sess_num > 0:
        lane_lines, stale_lanes = section_stale_lanes(current_sess_num, check_stale_lanes)
        _print_lines(lane_lines)

    if sess_num:
        _print_lines(section_pci(sess_num, compute_pci))

    _print_lines(section_prescription_gap())
    _print_lines(section_level_balance())

    # Stalled campaigns — need stall_map for suggested action
    stall_lines, stall_map = section_stalled_campaigns()
    _print_lines(stall_lines)

    _print_lines(section_stale_experiments(check_stale_experiments))
    _print_lines(section_experiment_harvest_gap(check_experiment_harvest_gap))
    if current_sess_num > 0:
        _print_lines(section_stale_baselines(current_sess_num, check_stale_baselines))
    _print_lines(section_underused_tools(check_underused_core_tools, log_text))
    _print_lines(section_recent_commits(_commits()))
    _print_lines(section_session_log_tail(log_text, brief))
    _print_lines(section_agent_positions())
    _print_lines(section_concurrent_activity())
    _print_lines(section_historian_repair())
    _print_lines(section_meta_tooler())

    _print_lines(section_suggested_action(maint_out, open_signals, stall_map, priorities))

    # Write trigger manifest
    try:
        _write_trigger_manifest(current_sess_num, maint_out, stale_lanes,
                                frontier_text=frontier_text)
    except Exception:
        pass


if __name__ == "__main__":
    main()
