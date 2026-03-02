#!/usr/bin/env python3
"""maintenance.py — Central maintenance check system.

P-282 thin-wrapper bridge: check functions are extracted to thematic modules.
This file delegates to them and orchestrates execution + outcome tracking.

Modules:
  maintenance_common.py    — shared constants, helpers, I/O utilities
  maintenance_health.py    — operational/runtime health checks (S433)
  maintenance_quality.py   — quality/integrity checks (S433)
  maintenance_signals.py   — signal/queue/coordination checks (S433)
  maintenance_lanes.py     — lane lifecycle checks
  maintenance_domains.py   — domain/frontier checks
  maintenance_state.py     — state consistency checks
  maintenance_drift.py     — drift/staleness checks
  maintenance_inventory.py — inventory/portability checks
  maintenance_outcomes.py  — outcome tracking
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from maintenance_common import (
    REPO_ROOT, PYTHON_EXE, PYTHON_CMD,
    LANE_ACTIVE_STATUSES, LANE_STALE_NOTICE_SESSIONS, LANE_STALE_DUE_SESSIONS,
    LANE_ANTIWINDUP_ROWS, LANE_REPORT_KEYS,
    DOMAIN_SYNC_ALLOWED_VALUES, LANE_AVAILABLE_ALLOWED_VALUES, LANE_AVAILABLE_LEGACY_MAP,
    LANE_GLOBAL_FOCUS_VALUES, CHECK_FOCUS_HISTORIAN_REQUIRED,
    HISTORIAN_SELF_ANCHOR_TOKENS, HISTORIAN_SURROUNDINGS_ANCHOR_TOKENS,
    BRIDGE_FILES,
    OUTCOMES_PATH, OUTCOMES_MAX_SESSIONS,
    PRIORITY_ORDER, PRIORITY_SYMBOLS,
    _extract_domain_frontier_active_ids, _parse_domain_frontier_active_count,
    _parse_domain_index_active_count, _parse_domain_index_active_line_ids,
    _parse_domain_index_open_ids, _format_frontier_id_diff,
    _truncated, _read, _git, _token_count, _session_number,
    _exists, _python_command_runs, _py_launcher_runs,
    _command_runs, _command_exists, _inter_swarm_connectivity,
    _active_lane_rows, _parse_lane_tags, _is_lane_placeholder,
    _lane_has_any_tag, _lane_high_risk_signal,
    _active_principle_ids,
)

# ---------------------------------------------------------------------------
# Delegation stubs — maintenance_health.py (S433 extraction)
# ---------------------------------------------------------------------------

def check_unpushed() -> list[tuple[str, str]]:
    from maintenance_health import check_unpushed as _impl
    return _impl()

def check_kill_switch() -> list[tuple[str, str]]:
    from maintenance_health import check_kill_switch as _impl
    return _impl()

def check_uncommitted() -> list[tuple[str, str]]:
    from maintenance_health import check_uncommitted as _impl
    return _impl()

def check_compaction() -> list[tuple[str, str]]:
    from maintenance_health import check_compaction as _impl
    return _impl()

def check_lessons() -> list[tuple[str, str]]:
    from maintenance_health import check_lessons as _impl
    return _impl()

def check_t4_tool_size() -> list[tuple[str, str]]:
    from maintenance_health import check_t4_tool_size as _impl
    return _impl()

def check_zombie_tools() -> list[tuple[str, str]]:
    from maintenance_health import check_zombie_tools as _impl
    return _impl()

def check_claim_gc() -> list[tuple[str, str]]:
    from maintenance_health import check_claim_gc as _impl
    return _impl()

def check_validator() -> list[tuple[str, str]]:
    from maintenance_health import check_validator as _impl
    return _impl()

def check_version_drift() -> list[tuple[str, str]]:
    from maintenance_health import check_version_drift as _impl
    return _impl()

# ---------------------------------------------------------------------------
# Delegation stubs — maintenance_quality.py (S433 extraction)
# ---------------------------------------------------------------------------

def check_correction_propagation() -> list[tuple[str, str]]:
    from maintenance_quality import check_correction_propagation as _impl
    return _impl()

def check_utility() -> list[tuple[str, str]]:
    from maintenance_quality import check_utility as _impl
    return _impl()

def check_dark_matter() -> list[tuple[str, str]]:
    from maintenance_quality import check_dark_matter as _impl
    return _impl()

def check_meta_tooler_gap() -> list[tuple[str, str]]:
    from maintenance_quality import check_meta_tooler_gap as _impl
    return _impl()

def check_level_quota() -> list[tuple[str, str]]:
    from maintenance_quality import check_level_quota as _impl
    return _impl()

def check_paper_accuracy() -> list[tuple[str, str]]:
    from maintenance_quality import check_paper_accuracy as _impl
    return _impl()

def check_file_graph() -> list[tuple[str, str]]:
    from maintenance_quality import check_file_graph as _impl
    return _impl()

def check_structure_layout() -> list[tuple[str, str]]:
    from maintenance_quality import check_structure_layout as _impl
    return _impl()

# ---------------------------------------------------------------------------
# Delegation stubs — maintenance_signals.py (S433 extraction)
# ---------------------------------------------------------------------------

def check_open_challenges() -> list[tuple[str, str]]:
    from maintenance_signals import check_open_challenges as _impl
    return _impl()

def check_human_queue() -> list[tuple[str, str]]:
    from maintenance_signals import check_human_queue as _impl
    return _impl()

def check_signal_staleness() -> list[tuple[str, str]]:
    from maintenance_signals import check_signal_staleness as _impl
    return _impl()

def check_council_health() -> list[tuple[str, str]]:
    from maintenance_signals import check_council_health as _impl
    return _impl()

def check_dispatch_log() -> list[tuple[str, str]]:
    from maintenance_signals import check_dispatch_log as _impl
    return _impl()

def check_help_requests() -> list[tuple[str, str]]:
    from maintenance_signals import check_help_requests as _impl
    return _impl()

def check_child_bulletins() -> list[tuple[str, str]]:
    from maintenance_signals import check_child_bulletins as _impl
    return _impl()

def check_github_swarm_intake() -> list[tuple[str, str]]:
    from maintenance_signals import check_github_swarm_intake as _impl
    return _impl()

def check_periodics() -> list[tuple[str, str]]:
    from maintenance_signals import check_periodics as _impl
    return _impl()

def check_mission_constraints() -> list[tuple[str, str]]:
    from maintenance_signals import check_mission_constraints as _impl
    return _impl()

def check_frontier_namespace_linkage() -> list[tuple[str, str]]:
    from maintenance_signals import check_frontier_namespace_linkage as _impl
    return _impl()

# ---------------------------------------------------------------------------
# Delegation stubs — maintenance_lanes.py (pre-existing)
# ---------------------------------------------------------------------------

def check_swarm_lanes() -> list[tuple[str, str]]:
    from maintenance_lanes import check_swarm_lanes as _impl
    return _impl(
        _active_lane_rows, _session_number, _parse_lane_tags, _is_lane_placeholder,
        _lane_high_risk_signal, _truncated,
        LANE_ACTIVE_STATUSES, LANE_STALE_NOTICE_SESSIONS, LANE_STALE_DUE_SESSIONS,
        LANE_ANTIWINDUP_ROWS, DOMAIN_SYNC_ALLOWED_VALUES, LANE_AVAILABLE_ALLOWED_VALUES,
        LANE_AVAILABLE_LEGACY_MAP, LANE_GLOBAL_FOCUS_VALUES,
    )

def check_swarm_coordinator() -> list[tuple[str, str]]:
    from maintenance_lanes import check_swarm_coordinator as _impl
    return _impl(
        _active_lane_rows, _parse_lane_tags, _lane_has_any_tag, _truncated,
        LANE_GLOBAL_FOCUS_VALUES,
    )

def check_lane_reporting_quality() -> list[tuple[str, str]]:
    from maintenance_lanes import check_lane_reporting_quality as _impl
    return _impl(
        _active_lane_rows, _parse_lane_tags, _is_lane_placeholder, _truncated,
        LANE_REPORT_KEYS, CHECK_FOCUS_HISTORIAN_REQUIRED,
        HISTORIAN_SELF_ANCHOR_TOKENS, HISTORIAN_SURROUNDINGS_ANCHOR_TOKENS,
    )

# ---------------------------------------------------------------------------
# Delegation stubs — maintenance_domains.py (pre-existing)
# ---------------------------------------------------------------------------

def check_frontier_decay() -> list[tuple[str, str]]:
    from maintenance_domains import check_frontier_decay as _impl
    return _impl(REPO_ROOT, _read)

def check_anxiety_zones() -> list[tuple[str, str]]:
    from maintenance_domains import check_anxiety_zones as _impl
    return _impl(REPO_ROOT, _read, _session_number)

def check_domain_expert_coverage() -> list[tuple[str, str]]:
    from maintenance_domains import check_domain_expert_coverage as _impl
    return _impl(REPO_ROOT, _read)

def check_historian_integrity() -> list[tuple[str, str]]:
    from maintenance_domains import check_historian_integrity as _impl
    return _impl(REPO_ROOT, _read, PYTHON_EXE)

def check_domain_frontier_consistency() -> list[tuple[str, str]]:
    from maintenance_domains import check_domain_frontier_consistency as _impl
    return _impl(
        REPO_ROOT, _read, _truncated,
        _extract_domain_frontier_active_ids, _parse_domain_frontier_active_count,
        _parse_domain_index_active_count, _parse_domain_index_active_line_ids,
        _parse_domain_index_open_ids, _format_frontier_id_diff,
    )

def check_frontier_registry() -> list[tuple[str, str]]:
    from maintenance_domains import check_frontier_registry as _impl
    return _impl(REPO_ROOT, _read, _truncated)

# ---------------------------------------------------------------------------
# Delegation stubs — maintenance_state.py (pre-existing)
# ---------------------------------------------------------------------------

def check_cross_references() -> list[tuple[str, str]]:
    from maintenance_state import check_cross_references as _impl
    return _impl(REPO_ROOT, _read, _git, _truncated, _active_principle_ids)

def check_readme_snapshot_drift() -> list[tuple[str, str]]:
    from maintenance_state import check_readme_snapshot_drift as _impl
    return _impl(REPO_ROOT, _read, _session_number)

def check_count_drift() -> list[tuple[str, str]]:
    from maintenance_state import check_count_drift as _impl
    return _impl(REPO_ROOT, _read, _git)

def check_handoff_staleness() -> list[tuple[str, str]]:
    from maintenance_state import check_handoff_staleness as _impl
    return _impl(REPO_ROOT, _read, _session_number)

def check_state_header_sync() -> list[tuple[str, str]]:
    from maintenance_state import check_state_header_sync as _impl
    return _impl(REPO_ROOT, _read, _git, _session_number)

def check_session_log_integrity() -> list[tuple[str, str]]:
    from maintenance_state import check_session_log_integrity as _impl
    return _impl(REPO_ROOT, _read, _truncated)

# ---------------------------------------------------------------------------
# Delegation stubs — maintenance_drift.py (pre-existing)
# ---------------------------------------------------------------------------

def check_proxy_k_drift() -> list[tuple[str, str]]:
    from maintenance_drift import check_proxy_k_drift as _impl
    return _impl(REPO_ROOT, PYTHON_CMD, _read, _git, _token_count, _session_number)

def check_observer_staleness() -> list[tuple[str, str]]:
    from maintenance_drift import check_observer_staleness as _impl
    return _impl(REPO_ROOT)

# ---------------------------------------------------------------------------
# Delegation stubs — maintenance_inventory.py (pre-existing)
# ---------------------------------------------------------------------------

def check_runtime_portability() -> list[tuple[str, str]]:
    from maintenance_inventory import check_runtime_portability as _impl
    return _impl(
        REPO_ROOT, PYTHON_CMD, BRIDGE_FILES,
        _exists, _read, _git, _command_exists,
        _python_command_runs, _py_launcher_runs,
        lambda: __import__('maintenance_common')._is_wsl_mnt_repo(),
    )

def check_commit_hooks() -> list[tuple[str, str]]:
    from maintenance_inventory import check_commit_hooks as _impl
    return _impl(REPO_ROOT, _exists, _read)

def build_inventory() -> dict:
    from maintenance_inventory import build_inventory as _impl
    return _impl(
        REPO_ROOT, PYTHON_EXE, PYTHON_CMD, BRIDGE_FILES,
        _exists, _python_command_runs, _py_launcher_runs,
        _command_runs, _command_exists, _inter_swarm_connectivity,
    )

def print_inventory(inv: dict):
    from maintenance_inventory import print_inventory as _impl
    return _impl(inv)

# --- Swarm-grade outcome tracking (F-MECH1, GAP-1) ---
from maintenance_outcomes import load_outcomes as _load_outcomes
from maintenance_outcomes import save_outcomes_direct as _save_outcomes_direct_impl
from maintenance_outcomes import learn_from_outcomes as _learn_from_outcomes_impl

def _save_outcomes_direct(check_items: dict[str, list[tuple[str, str]]], session: int):
    _save_outcomes_direct_impl(check_items, session, OUTCOMES_PATH, OUTCOMES_MAX_SESSIONS)

def _learn_from_outcomes():
    _learn_from_outcomes_impl(OUTCOMES_PATH)

def main():
    if "--inventory" in sys.argv:
        inv = build_inventory()
        if "--json" in sys.argv:
            print(json.dumps(inv, indent=2))
        else:
            print_inventory(inv)
        return

    if "--learn" in sys.argv:
        _learn_from_outcomes()
        return

    quick = "--quick" in sys.argv

    all_checks = [
        check_kill_switch,
        check_validator,
        check_mission_constraints,
        check_runtime_portability,
        check_commit_hooks,
        check_version_drift,
        check_open_challenges,
        check_compaction,
        check_lessons,
        check_child_bulletins,
        check_help_requests,
        check_frontier_decay,
        check_periodics,
        check_human_queue,
        check_swarm_lanes,
        check_swarm_coordinator,
        check_lane_reporting_quality,
        check_github_swarm_intake,
        check_uncommitted,
        check_handoff_staleness,
        check_session_log_integrity,
        check_state_header_sync,
        check_cross_references,
        check_anxiety_zones,
        check_dispatch_log,
        check_domain_expert_coverage,
        check_council_health,
        check_signal_staleness,
        check_historian_integrity,
        check_domain_frontier_consistency,
        check_frontier_namespace_linkage,
        check_readme_snapshot_drift,
        check_count_drift,
        check_structure_layout,
        check_frontier_registry,
        check_file_graph,
        check_claim_gc,
        check_correction_propagation,
        check_observer_staleness,
        check_paper_accuracy,
        check_utility,
        check_dark_matter,
        check_proxy_k_drift,
        check_t4_tool_size,
        check_zombie_tools,
        check_meta_tooler_gap,
        check_level_quota,
    ]

    if not quick:
        all_checks.append(check_unpushed)

    # HEAD-keyed caching: checks that only depend on committed state are cached
    # and skip execution when HEAD hasn't changed. Live checks (working tree,
    # env, concurrent claims) always run. Saves ~3-4s on cache hit.
    _LIVE_CHECKS = {
        "check_uncommitted",        # git status (working tree)
        "check_kill_switch",        # env vars + KILL-SWITCH.md (could toggle anytime)
        "check_claim_gc",           # workspace/claims/ (concurrent sessions)
        "check_periodics",          # tools/periodics.json updated in working tree before commit
        "check_level_quota",        # reads uncommitted lessons from working tree
        "check_swarm_lanes",        # tasks/SWARM-LANES.md modified by concurrent sessions
        "check_swarm_coordinator",  # tasks/SWARM-LANES.md modified by concurrent sessions
        "check_lane_reporting_quality",  # tasks/SWARM-LANES.md modified by concurrent sessions
    }
    try:
        from swarm_cache import head_cache as _hcache
    except ImportError:
        _hcache = None

    items: list[tuple[str, str]] = []
    check_items: dict[str, list[tuple[str, str]]] = {fn.__name__: [] for fn in all_checks}
    for check_fn in all_checks:
        name = check_fn.__name__
        try:
            # Try cache for HEAD-dependent checks
            if _hcache and name not in _LIVE_CHECKS:
                cached = _hcache.get(f"maint_{name}")
                if cached is not None:
                    fn_items = [tuple(x) for x in cached]
                    items.extend(fn_items)
                    check_items[name] = fn_items
                    continue
            fn_items = check_fn()
            items.extend(fn_items)
            check_items[name] = fn_items
            # Cache HEAD-dependent results
            if _hcache and name not in _LIVE_CHECKS:
                _hcache.set(f"maint_{name}", [list(x) for x in fn_items])
        except Exception as e:
            items.append(("NOTICE", f"{check_fn.__name__} error: {e}"))

    items.sort(key=lambda x: PRIORITY_ORDER.get(x[0], 99))

    print("=== MAINTENANCE ===")
    print()

    if not items:
        print("  Nothing due. All clear.")
    else:
        current_priority = None
        for priority, msg in items:
            if priority != current_priority:
                current_priority = priority
                print(f"  [{priority}]")
            symbol = PRIORITY_SYMBOLS.get(priority, "   ")
            print(f"  {symbol} {msg}")
        print()
        counts = {}
        for p, _ in items:
            counts[p] = counts.get(p, 0) + 1
        summary = " | ".join(f"{p}: {c}" for p, c in sorted(counts.items(), key=lambda x: PRIORITY_ORDER.get(x[0], 99)))
        print(f"  {summary}")

    # Swarm-grade: save outcomes for learning (F-MECH1)
    session = _session_number()
    if session > 0:
        _save_outcomes_direct(check_items, session)

    print()

    # --auto: Tier 2->Tier 1 bridge (L-533) — open lanes for DUE periodics with no active lane
    if "--auto" in sys.argv and session > 0:
        _auto_open_lanes(items, session)


def _auto_open_lanes(items: list[tuple[str, str]], session: int) -> None:
    """Open maintenance lanes for DUE periodic items that have no active lane. (L-533)"""
    due_periodics = [msg for sev, msg in items if sev == "DUE" and msg.startswith("[") and "]" in msg]
    if not due_periodics:
        print("  AUTO: no DUE periodic items to lane.")
        return

    # Collect active lane Etc content for deduplication
    active_etc = ""
    active_lane_ids: set[str] = set()
    if parsed_lanes := _active_lane_rows():
        _, active = parsed_lanes
        active_etc = " ".join(row.get("etc", "") for row in active).lower()
        active_lane_ids = {row.get("lane", "").strip() for row in active}

    print("\n  AUTO: scanning DUE periodics for lanes to open...")
    opened: list[str] = []
    skipped: list[str] = []

    for msg in due_periodics:
        m = re.match(r"\[([^\]]+)\]", msg)
        if not m:
            continue
        item_id = m.group(1)
        lane_id = f"MAINT-{item_id}-S{session}"

        # Skip if an active lane already covers this periodic
        if item_id.lower() in active_etc or lane_id in active_lane_ids:
            skipped.append(item_id)
            continue

        # Extract description from message (strip cadence/session suffix)
        desc_part = msg.split("]", 1)[1].strip()
        desc_clean = re.sub(r"\s*\(every.*?\)$", "", desc_part).strip()[:100]

        r = subprocess.run(
            [
                PYTHON_EXE, str(REPO_ROOT / "tools" / "open_lane.py"),
                "--lane", lane_id,
                "--session", f"S{session}",
                "--domain", "meta",
                "--frontier", "F-META3",
                "--intent", f"Periodic maintenance: {item_id} — {desc_clean}",
                "--expect", f"Periodic {item_id} completed; last_reviewed_session updated in periodics.json",
                "--artifact", f"experiments/meta/maint-{item_id}-s{session}.json",
                "--mode", "hardening",
                "--check-mode", "objective",
            ],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            opened.append(lane_id)
            print(f"  AUTO: opened -> {lane_id}")
        else:
            err = (r.stderr or r.stdout or "").strip()[:120]
            print(f"  AUTO: SKIP {lane_id} — {err}")

    if skipped:
        print(f"  AUTO: {len(skipped)} already covered: {', '.join(skipped)}")
    if opened:
        print(f"  AUTO: {len(opened)} lane(s) created: {', '.join(opened)}")
    else:
        print(f"  AUTO: no new lanes needed.")
    print()


if __name__ == "__main__":
    main()
