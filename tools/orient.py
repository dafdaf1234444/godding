#!/usr/bin/env python3
"""
orient.py — Single-command session orientation for swarm nodes.

Synthesizes maintenance status, NEXT.md priorities, FRONTIER.md open questions,
and INDEX.md state counts into a decision-ready snapshot.

Replaces the manual pattern of: read NEXT.md + INDEX.md + FRONTIER.md + run maintenance.py.

Usage:
    python3 tools/orient.py                         # full orientation
    python3 tools/orient.py --brief                 # compact one-screen summary
    python3 tools/orient.py --coord                 # coordination-only (for concurrent sessions)
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
    "tools/question_gen.py",
    "tools/cell_blueprint.py",
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
    try:
        from orient_checks import check_foreign_staged_deletions as _impl
        _impl(ROOT)
    except (ImportError, ModuleNotFoundError):
        pass  # graceful degradation for daughter bundles (L-1467)

def check_git_object_health():
    from orient_checks import check_git_object_health as _impl
    return _impl(ROOT)

def check_genesis_hash():
    from orient_checks import check_genesis_hash as _impl
    return _impl(ROOT)

def check_git_index_health():
    from orient_checks import check_git_index_health as _impl
    return _impl(ROOT)

def check_ghost_lessons():
    from orient_checks import check_ghost_lessons as _impl
    return _impl(ROOT)

def check_experiment_harvest_gap(threshold: int = 5) -> list:
    from orient_checks import check_experiment_harvest_gap as _impl
    return _impl(ROOT, _hcache, threshold)

def check_active_claims():
    try:
        from orient_checks import check_active_claims as _impl
        _impl(ROOT)
    except (ImportError, ModuleNotFoundError):
        pass  # graceful degradation for daughter bundles (L-1467)

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
        check = subprocess.run(
            ["git", "cat-file", "-t", "HEAD:.claude/commands/swarm.md"],
            capture_output=True, text=True, cwd=ROOT,
        )
        if check.returncode != 0:
            return
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
    coord = "--coord" in sys.argv  # coordination-only: skip static analysis (L-1425)

    _auto_repair_swarm_md()

    # Fast pre-checks (non-blocking print)
    check_foreign_staged_deletions()
    check_active_claims()

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
        section_index_coverage, section_precompact_checkpoint, section_cell_blueprint,
        section_key_state,
        section_priorities, section_frontiers, section_stale_beliefs, section_dogma_finder,
        section_self_application, section_stale_lanes, section_pci,
        section_prescription_gap, section_level_balance, section_succession_phase,
        section_stalled_campaigns,
        section_stale_experiments, section_experiment_harvest_gap, section_stale_baselines,
        section_underused_tools, section_recent_commits, section_session_log_tail,
        section_agent_positions, section_concurrent_activity, section_historian_repair,
        section_meta_tooler, section_zombie_carryover, section_closure_metric,
        section_knowledge_swarm, section_knowledge_recombination, section_correction_propagation,
        section_suggested_action, section_cascade_state, section_epsilon_dispatch,
        section_grounding_audit, section_fairness, section_self_inflation,
        section_trace_amplification,
        section_complexity_phase,
    )
    try:
        from external_grounding_check import section_grounding_decay
    except (ImportError, ModuleNotFoundError):
        section_grounding_decay = lambda: []
    try:
        from closeable_frontiers import section_closeable_frontiers
    except (ImportError, ModuleNotFoundError):
        section_closeable_frontiers = lambda *a, **kw: []

    # Parallelize ALL slow independent operations (S506 perf fix, L-1349):
    # At N=1211, sequential total was ~135s. Parallelizing brings wall time to ~30s.
    # L-1349: any new section MUST be added to this executor block.
    from concurrent.futures import ThreadPoolExecutor, as_completed
    _futures = {}
    _pool = ThreadPoolExecutor(max_workers=12)
    if True:  # was 'with' block — explicit shutdown to avoid hang on stuck threads (L-1542)
        # Pre-checks (~3s each)
        _futures['git_health'] = _pool.submit(check_git_object_health)
        _futures['genesis'] = _pool.submit(check_genesis_hash)
        _futures['index_health'] = _pool.submit(check_git_index_health)
        _futures['ghost'] = _pool.submit(check_ghost_lessons)
        # Heavy sections (~7-29s each when sequential)
        _futures['historian'] = _pool.submit(section_historian_repair)
        _futures['meta_tooler'] = _pool.submit(section_meta_tooler)
        _futures['prescription'] = _pool.submit(section_prescription_gap)
        _futures['dogma'] = _pool.submit(section_dogma_finder)
        _futures['succession'] = _pool.submit(section_succession_phase)
        _futures['knowledge_swarm'] = _pool.submit(section_knowledge_swarm)
        _futures['correction'] = _pool.submit(section_correction_propagation)
        _futures['fairness'] = _pool.submit(section_fairness)
        _futures['trace'] = _pool.submit(section_trace_amplification)
        _futures['stalled'] = _pool.submit(section_stalled_campaigns)
        _futures['cascade'] = _pool.submit(lambda: section_cascade_state(maint_output=""))
        _futures['stale_exp'] = _pool.submit(check_stale_experiments)
        _futures['exp_harvest'] = _pool.submit(check_experiment_harvest_gap)
        # self_app needs session_num which we don't have yet — use orient_checks directly
        try:
            from orient_checks import check_stale_infrastructure as _check_infra_impl
            _futures['self_app'] = _pool.submit(lambda: _check_infra_impl(500, ROOT, CORE_SWARM_TOOLS, _hcache, 50))
        except (ImportError, ModuleNotFoundError):
            _futures['self_app'] = _pool.submit(lambda: [])
        # Inline slow sections
        _futures['grounding_decay'] = _pool.submit(section_grounding_decay)
        def _run_human_impact():
            try:
                from human_impact import scan_lessons as _hi_scan, extract_soul as _hi_soul
                return _hi_soul(_hi_scan())
            except Exception:
                return None
        _futures['human_impact'] = _pool.submit(_run_human_impact)
        def _run_brain_turing():
            try:
                from brain_extractor import scan_all_lessons as _br_scan, extract_brain as _br_extract
                from turing_test import run_all_tests as _tt_run
                _br = _br_extract(_br_scan())
                _tt = _tt_run()
                return {"brain": _br, "turing": _tt}
            except Exception:
                return None
        _futures['brain_turing'] = _pool.submit(_run_brain_turing)
        def _run_concept_debt():
            try:
                from concept_debt_audit import audit as _cda
                import io, contextlib
                _cda_buf = io.StringIO()
                with contextlib.redirect_stdout(_cda_buf):
                    return _cda(json_mode=False)
            except Exception:
                return None
        _futures['concept_debt'] = _pool.submit(_run_concept_debt)
        maint_out = _run_maint()  # run in main thread while others execute
        # Re-submit cascade with actual maint_out if needed
        _futures['cascade_real'] = _pool.submit(lambda mo=maint_out: section_cascade_state(maint_output=mo))
    # Collect pre-check results (10s timeout per future to prevent orient hang — L-1542)
    for _line in _futures['git_health'].result(timeout=10):
        print(_line)
    for _line in _futures['genesis'].result(timeout=10):
        print(_line)
    def _safe_result(key, default=None, timeout=10):
        """Fault-isolated future result — optional sections fail independently (L-1413).
        Timeout prevents a single hung future from blocking all of orient (L-1542)."""
        try:
            return _futures[key].result(timeout=timeout)
        except Exception:
            return default if default is not None else []

    for _line in _safe_result('index_health'):
        print(_line)
    for _line in _safe_result('ghost'):
        print(_line)
    # Store heavy section results for ordered printing later
    _historian_repair_lines = _safe_result('historian')
    _meta_tooler_lines = _safe_result('meta_tooler')
    _prescription_gap_lines = _safe_result('prescription')
    _dogma_lines = _safe_result('dogma')
    _succession_lines = _safe_result('succession')
    _knowledge_swarm_lines = _safe_result('knowledge_swarm')
    _correction_lines = _safe_result('correction')
    _fairness_lines = _safe_result('fairness')
    _trace_lines = _safe_result('trace')
    _stall_result = _safe_result('stalled', default=([], {}))
    _stall_lines, _stall_map = _stall_result if isinstance(_stall_result, tuple) else ([], {})
    _cascade_lines = _safe_result('cascade_real')
    _stale_exp_lines = _safe_result('stale_exp')
    _exp_harvest_lines = _safe_result('exp_harvest')
    _self_app_result = _safe_result('self_app')
    _grounding_decay_result = _safe_result('grounding_decay')
    _human_impact_result = _safe_result('human_impact')
    _brain_turing_result = _safe_result('brain_turing')
    _concept_debt_result = _safe_result('concept_debt')

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
    mode_tag = " [COORD]" if coord else ""
    print(f"=== ORIENT {session} | {counts}{mode_tag} ===")
    print(f"Maintenance: {maint_level}")
    print()

    # Display sections — each returns list[str]
    _print_lines(section_maintenance(maint_out, maint_level, brief))

    if sess_num:
        _print_lines(section_session_triggers(sess_num, maint_out, evaluate_session_triggers))

    open_signals = _signals(signals_text, current_session=sess_num)
    _print_lines(section_open_signals(open_signals))

    if not coord:
        _print_lines(section_index_coverage(index_text, check_index_coverage))
        _print_lines(section_precompact_checkpoint(session))
        _print_lines(section_cell_blueprint(session))
        _print_lines(section_key_state(_key_state(next_text)))

    priorities = _priorities(next_text)
    if not coord:
        _print_lines(section_priorities(priorities))
        _print_lines(section_frontiers(_frontiers(frontier_text)))

    if sess_num and not coord:
        _print_lines(section_stale_beliefs(sess_num, check_stale_beliefs))
        _print_lines(_dogma_lines)
        # self_application uses pre-computed stale infrastructure
        _sa_result = _self_app_result or []
        if _sa_result:
            print(f"--- Self-application gap ({len(_sa_result)} components not evolved >50s) ---")
            for si in _sa_result:
                print(f"  \u2298 {si}")
            print("  Suggested (pick 1):")
            for si in _sa_result[:3]:
                name = si.split("(")[0].strip().replace(" ", "-")
                print(f"    python3 tools/open_lane.py --lane EVOLVE-{name}-S{sess_num} --session S{sess_num} --expect 'modernize-{name}' --artifact 'tools/{si.split('(')[0].strip()}' --intent 'P14: evolve stale infrastructure'")

    # Stale lanes — need return value for trigger manifest
    git_session = _git_session()
    current_sess_num = git_session if git_session > 0 else sess_num
    stale_lanes = []
    if current_sess_num > 0:
        lane_lines, stale_lanes = section_stale_lanes(current_sess_num, check_stale_lanes)
        _print_lines(lane_lines)

    if sess_num and not coord:
        _print_lines(section_pci(sess_num, compute_pci))

    if not coord:
        _print_lines(_prescription_gap_lines)
        _print_lines(section_level_balance())
        _print_lines(_succession_lines)
        _print_lines(section_zombie_carryover())
        _print_lines(section_closure_metric())
        _print_lines(section_grounding_audit())
        print(f"\n--- Lesson Grounding Decay (F-GND1 Phase 1) ---")
        try:
            if _grounding_decay_result is not None:
                print(_grounding_decay_result)
            else:
                print("  (grounding decay: no result)")
        except Exception as e:
            print(f"  (grounding decay error: {e})")
        _print_lines(_knowledge_swarm_lines)
        _print_lines(section_closeable_frontiers(session_num=current_sess_num))
        _print_lines(section_knowledge_recombination())
        _print_lines(_correction_lines)
        _print_lines(_fairness_lines)
        _print_lines(section_complexity_phase())

    if not coord:
        # Human impact / soul extraction (SIG-81, F-SOUL1) — pre-computed in parallel
        _hi_soul_data = _human_impact_result
        if _hi_soul_data:
            print(f"\n--- Human Impact (F-SOUL1, SIG-81) ---")
            _hi_ci = _hi_soul_data.get("benefit_ratio_ci")
            _hi_ci_str = f" CI:[{_hi_ci['lower']}x,{_hi_ci['upper']}x]" if isinstance(_hi_ci, dict) else ""
            print(f"  {_hi_soul_data['good_pct']}% GOOD / {_hi_soul_data['bad_pct']}% BAD / "
                  f"{_hi_soul_data['neutral_pct']}% NEUTRAL | "
                  f"benefit ratio {_hi_soul_data['human_benefit_ratio']}x{_hi_ci_str} (target >3.0x)")
            for _sp in _hi_soul_data.get("selection_pressure", [])[:2]:
                print(f"    \u2192 {_sp}")
            print(f"  Run: python3 tools/human_impact.py")

        # Brain + Turing (SIG-108, L-1508) — cognitive architecture + intelligence criteria
        if _brain_turing_result:
            _br = _brain_turing_result.get("brain")
            _tt = _brain_turing_result.get("turing")
            if _br:
                _s12 = _br.get("system1_vs_system2", {})
                _bh = _br.get("health", {})
                _marr = _br.get("marr_levels", {})
                print(f"\n--- Brain (SIG-108, L-1508) ---")
                print(f"  S1/S2={_s12.get('ratio','?')}x ({_s12.get('interpretation','?')}) | "
                      f"bias={_bh.get('bias_ratio','?')} ({_bh.get('bias_health','?')}) | "
                      f"diversity={_br.get('reasoning_diversity_avg','?')} ({_bh.get('diversity_health','?')})")
                print(f"  Marr: {_marr.get('computational_pct','?')}% computational / "
                      f"{_marr.get('algorithmic_pct','?')}% algorithmic / "
                      f"{_marr.get('implementational_pct','?')}% implementational")
                for _sp in _br.get("selection_pressure", [])[:1]:
                    print(f"    \u2192 {_sp}")
            if _tt:
                _tc = _tt.get("composite", {})
                print(f"  Turing: TQ={_tc.get('turing_quotient','?')} "
                      f"({_tc.get('pass',0)}P/{_tc.get('partial',0)}M/{_tc.get('fail',0)}F)")
                print(f"  Run: python3 tools/brain_extractor.py | python3 tools/turing_test.py")

        # Steerer voices (L-1337, L-1350) — synthetic humans challenging the swarm
        try:
            import json as _json_steerer
            _steerer_hist_path = ROOT / "tools" / "synthetic-steerers" / "signal-history.json"
            if _steerer_hist_path.exists():
                _steerer_hist = _json_steerer.loads(_steerer_hist_path.read_text())
                _recent_signals = []
                for _sname, _entries in _steerer_hist.items():
                    if _entries:
                        _last = _entries[-1]
                        for _sig in _last.get("signals", []):
                            _recent_signals.append((_sname, _last.get("session", "?"), _sig))
                if _recent_signals:
                    print(f"\n--- Steerer Voices ({len(_recent_signals)} signals, L-1337) ---")
                    for _sname, _ssess, _sig in _recent_signals[-8:]:
                        print(f"  [{_sname}] ({_ssess}): {_sig}")
                    _cc_path = ROOT / "tools" / "synthetic-steerers" / "cross-challenges.md"
                    if _cc_path.exists():
                        print(f"  Cross-challenges: {_cc_path.name}")
        except Exception:
            pass

        _print_lines(section_self_inflation())
        _print_lines(_trace_lines)

        # Concept debt (F-INV1, L-1269) — pre-computed in parallel
        _cda_result = _concept_debt_result
        if _cda_result:
            _named = _cda_result.get("named_concepts", 0)
            _unnamed = _cda_result.get("unnamed_patterns", 0)
            _total = _named + _unnamed
            _ratio = _named / _total if _total > 0 else 0
            _high = _cda_result.get("high_debt", 0)
            if _ratio < 0.60 or _high > 0:
                print(f"\n--- Concept Debt (F-INV1) ---")
                print(f"  Naming ratio: {_ratio:.0%} ({_named}/{_total}) | HIGH/MEDIUM debt: {_high}")
                if _high > 0:
                    for _pid, _info in sorted(_cda_result.get("unnamed", {}).items(),
                                               key=lambda x: -x[1].get("ad_hoc_mentions", 0)):
                        if _info.get("severity") in ("HIGH", "MEDIUM"):
                            print(f"  ! {_pid}: {_info['ad_hoc_mentions']} mentions [{_info['severity']}]")
                print(f"  Run: python3 tools/concept_debt_audit.py")

        # Stalled campaigns — pre-computed in parallel
        _print_lines(_stall_lines)
        stall_map = _stall_map

        # stale_experiments and experiment_harvest_gap — pre-computed in parallel
        if _stale_exp_lines:
            print(f"--- Unrun domain experiments ({len(_stale_exp_lines)}) ---")
            for e in _stale_exp_lines[:6]:
                print(f"  \u25cb {e}")
            print()
        if _exp_harvest_lines:
            print(f"--- Experiment harvest gap ({len(_exp_harvest_lines)} domains: \u22655 experiments, 0 lessons) ---")
            for domain, count in _exp_harvest_lines[:6]:
                print(f"  \U0001f4e6 {domain} ({count} experiments) \u2014 no lessons extracted yet")
            print()
        if current_sess_num > 0:
            _print_lines(section_stale_baselines(current_sess_num, check_stale_baselines))
        _print_lines(section_underused_tools(check_underused_core_tools, log_text))
        _print_lines(_historian_repair_lines)
        _print_lines(_meta_tooler_lines)
    else:
        stall_map = {}

    # Coordination-relevant sections (always shown)
    _print_lines(_cascade_lines)
    _print_lines(section_recent_commits(_commits()))
    _print_lines(section_session_log_tail(log_text, brief))
    _print_lines(section_agent_positions())
    _print_lines(section_concurrent_activity())

    # Prediction deadlines (F-FORE1, L-1439)
    try:
        import json as _json_pred
        from datetime import datetime as _dt_pred
        _pred_reg = ROOT / "experiments" / "finance" / "predictions" / "registry.json"
        if _pred_reg.exists():
            _pred_data = _json_pred.loads(_pred_reg.read_text())
            _today = _dt_pred.now().date()
            _due_soon = []
            for _p in _pred_data.get("predictions", []):
                if _p.get("status") != "OPEN":
                    continue
                _rb = _p.get("resolve_by")
                if _rb:
                    _rd = _dt_pred.strptime(_rb, "%Y-%m-%d").date()
                    _days = (_rd - _today).days
                    if _days <= 7:
                        _due_soon.append((_days, _p))
            _overdue = [d for d in _due_soon if d[0] < 0]
            _thisweek = [d for d in _due_soon if d[0] >= 0]
            if _due_soon:
                print(f"\n--- Prediction Deadlines (F-FORE1) ---")
                for _days, _p in sorted(_due_soon):
                    _label = f"{abs(_days)}d OVERDUE" if _days < 0 else ("TODAY" if _days == 0 else f"in {_days}d")
                    _flag = "\u26a0" if _days <= 0 else "\u2192"
                    print(f"  {_flag} {_p['id']} {_p['direction']} {_p['asset']} "
                          f"(conf={_p['confidence']}) — {_label} ({_p['resolve_by']})")
                print(f"  Resolve: python3 tools/market_predict.py resolve --id <ID> --outcome-price <price>")
    except Exception:
        pass

    _print_lines(section_epsilon_dispatch(current_sess_num))
    # Per-agent empathy — affective transduction (F-EMP5, L-1511, L-1523)
    try:
        from agent_empathy import model_agents, compute_priority_adjustments
        _emp_m = model_agents()
        _emp_a = compute_priority_adjustments(_emp_m)
        if _emp_a:
            print(f"\n--- Agent empathy ({len(_emp_a)} adjustments) ---")
            for _ea in sorted(_emp_a, key=lambda a: -a["strength"])[:4]:
                _ei = {"elevate": "\u2191", "deprioritize": "\u2193",
                       "notice": "\u2192"}.get(_ea["type"], "\u00b7")
                print(f"  {_ei} {_ea['reason']}")
            if len(_emp_a) > 4:
                print(f"  ... and {len(_emp_a) - 4} more")
            print("  Run: python3 tools/agent_empathy.py\n")
    except Exception:
        pass

    _print_lines(section_suggested_action(maint_out, open_signals, stall_map, priorities))

    # Write trigger manifest
    try:
        _write_trigger_manifest(current_sess_num, maint_out, stale_lanes,
                                frontier_text=frontier_text)
    except Exception:
        pass

    # Shut down pool without waiting for stuck threads (L-1542: brain_turing hangs)
    _pool.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()
