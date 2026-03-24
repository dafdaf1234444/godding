#!/usr/bin/env python3
"""
orient_sections.py — Display sections for orient.py main() output.

Heavy analysis -> orient_analysis.py; monitoring -> orient_monitors.py.
Re-exported here so orient.py needs zero import changes (DOMEX-META-S475).

Pattern: section_xxx(data) -> list[str]
"""

# Re-export from orient_analysis.py
from orient_analysis import (  # noqa: F401
    _cached_artifact, _run_tool_json,
    section_pci, section_prescription_gap, section_level_balance,
    section_succession_phase, section_stalled_campaigns,
    _item_resolved_by_actual, section_zombie_carryover,
    section_closure_metric,
)

# Re-export from orient_monitors.py
from orient_monitors import (  # noqa: F401
    section_precompact_checkpoint, section_cell_blueprint,
    section_cascade_state,
    section_concurrent_activity, section_historian_repair,
    section_meta_tooler, section_knowledge_swarm,
    section_correction_propagation, section_knowledge_recombination,
    _active_domex_domains, section_epsilon_dispatch,
    section_grounding_audit, section_self_inflation,
    section_trace_amplification,
    section_reactivation,
    section_complexity_phase,
)

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def section_maintenance(maint_out, maint_level, brief):
    """Maintenance details section."""
    lines = []
    if not brief or maint_level != "NOTICE-only":
        signal_lines = [l for l in maint_out.splitlines()
                        if l.strip() and "===" not in l and "maintenance" not in l.lower()[:10]]
        if signal_lines:
            lines.append("--- Maintenance ---")
            for line in signal_lines[:10]:
                lines.append(f"  {line}")
            lines.append("")
    return lines


def section_session_triggers(session_num, maint_out, evaluate_fn):
    """Session triggers (F-META6)."""
    lines = []
    try:
        top_trigger, active_triggers = evaluate_fn(session_num, maint_out=maint_out)
        if top_trigger:
            lines.append("--- Session Triggers (F-META6) ---")
            lines.append(f"  \U0001f534 {top_trigger[2]}: {top_trigger[0]} — {top_trigger[1][:80]}")
            if len(active_triggers) > 1:
                lines.append(f"  \U0001f4cb {len(active_triggers)-1} additional triggers active")
            lines.append("")
    except Exception:
        pass
    return lines


def section_open_signals(open_signals):
    """Open signals (L-703, L-803, L-808, L-1577)."""
    lines = []
    if open_signals:
        # Triage breakdown (L-1577)
        try:
            from swarm_signal import _classify_signal
            from swarm_io import session_number
            sn = session_number()
            triage = {"ACTIONABLE": 0, "STALE": 0, "NOISE": 0, "REDUNDANT": 0}
            for sig in open_signals:
                cat, _ = _classify_signal(sig, sn)
                triage[cat] += 1
            stale_noise = triage["STALE"] + triage["NOISE"] + triage["REDUNDANT"]
            triage_tag = f" ({triage['ACTIONABLE']} actionable, {stale_noise} triageable)" if stale_noise > 0 else ""
        except Exception:
            triage_tag = ""

        lines.append(f"--- Open signals ({len(open_signals)} unresolved{triage_tag}) ---")
        for sig in open_signals[:5]:
            age_tag = f" ({sig['age']}s ago)" if sig['age'] else ""
            icon = '\U0001f4e2' if sig['priority'] == 'P1' else '\U0001f4cb'
            lines.append(f"  {icon} {sig['id']}{age_tag}: {sig['content'][:90]}")
        if len(open_signals) > 5:
            lines.append(f"  ... and {len(open_signals) - 5} more")
        neglected = [s for s in open_signals if s.get("age", 0) > 20]
        if neglected:
            p1_neg = [s for s in neglected if s["priority"] == "P1"]
            tag = f" including {len(p1_neg)} P1" if p1_neg else ""
            lines.append(f"  \u26a0 BACKLOG: {len(neglected)} signals >20s old{tag} — sensing without acting")
            lines.append(f"    Oldest: {neglected[0]['id']} (age {neglected[0]['age']}s): {neglected[0]['content'][:60]}")
        if triage_tag and stale_noise > 0:
            lines.append(f"  \U0001f9f9 Run: python3 tools/swarm_signal.py triage")
        lines.append("")
    return lines


def section_index_coverage(index_text, check_fn):
    """INDEX.md coverage check (F-BRN4)."""
    lines = []
    index_notice = check_fn(index_text)
    if index_notice:
        lines.append(f"  {index_notice}")
        lines.append("")
    return lines


def section_key_state(key_state):
    """Key state from NEXT.md."""
    lines = []
    if key_state:
        lines.append("--- Key state ---")
        for s in key_state:
            lines.append(f"  {s}")
        lines.append("")
    return lines


def section_priorities(priorities):
    """Priorities from NEXT.md."""
    lines = []
    if priorities:
        lines.append("--- Priorities ---")
        for i, p in enumerate(priorities, 1):
            lines.append(f"  {i}. {p}")
        lines.append("")
    return lines


def section_frontiers(frontiers):
    """Open frontiers (critical/important)."""
    lines = []
    if frontiers:
        lines.append("--- Open frontiers (critical/important) ---")
        for f in frontiers:
            lines.append(f"  \u2022 {f}")
        lines.append("")
    return lines


def section_stale_beliefs(session_num, check_fn):
    """Stale beliefs — untested >50 sessions (L-483)."""
    lines = []
    try:
        stale_beliefs = check_fn(session_num)
        if stale_beliefs:
            lines.append(f"--- Stale beliefs ({len(stale_beliefs)} not re-tested >50 sessions) ---")
            for b in stale_beliefs[:5]:
                lines.append(f"  \u26a0 {b}")
            lines.append("")
    except Exception:
        pass
    return lines


def section_dogma_finder():
    """Dogma finder — surfaces ossified claims + prescriptions (L-1314, SIG-82)."""
    lines = []
    try:
        from dogma_finder import detect_dogma, prescribe
        findings = detect_dogma()
        high = [f for f in findings if f["total_score"] >= 0.6]
        meta = [f for f in findings if f["kind"] == "meta"]
        if high:
            lines.append(f"--- Dogma alert ({len(high)} ossified claims, score \u22650.6) ---")
            for item in high[:5]:
                sigs = ", ".join(s["signal"] for s in item["signals"])
                lines.append(
                    f"  \u26a0 {item['id']:12s} ({item['kind']})  "
                    f"score={item['total_score']:.1f}  [{sigs}]"
                )
            if len(high) > 5:
                lines.append(f"  ... and {len(high) - 5} more (run: python3 tools/dogma_finder.py)")
            # Top prescription
            rxs = prescribe(high, top_n=1)
            if rxs:
                rx = rxs[0]
                lines.append(f"  \u2192 Rx for {rx['id']}: {rx['actions'][0]['action']}")
            lines.append("")
        if meta:
            lines.append(f"  \u27f3 Meta-dogma: {len(meta)} assumptions in dogma finder itself untested")
            lines.append("")
    except Exception:
        pass
    return lines


def section_self_application(session_num, check_fn):
    """Self-application gap — CORE P14: infrastructure subject to swarm dynamics."""
    lines = []
    try:
        stale_infra = check_fn(session_num)
        if stale_infra:
            lines.append(f"--- Self-application gap ({len(stale_infra)} components not evolved >50s) ---")
            for si in stale_infra:
                lines.append(f"  \u2298 {si}")
            lines.append("  Suggested (pick 1):")
            for si in stale_infra[:3]:
                name = si.split("(")[0].strip().replace(" ", "-")
                lines.append(f"    python3 tools/open_lane.py --lane EVOLVE-{name}-S{session_num} --session S{session_num} --expect 'modernize-{name}' --artifact 'tools/{si.split('(')[0].strip()}' --intent 'P14: evolve stale infrastructure'")
            lines.append("")
    except Exception:
        pass
    return lines


def section_stale_lanes(current_sess_num, check_fn):
    """Stale lanes — cross-session open lanes (L-515)."""
    lines = []
    try:
        stale_lanes = check_fn(current_sess_num)
        if stale_lanes:
            lines.append(f"--- Stale lanes ({len(stale_lanes)} opened in prior session — execute or close) ---")
            for sl in stale_lanes:
                art_note = "\u2717 artifact missing" if not sl["has_artifact"] else "\u2713 artifact exists"
                gap = sl.get("gap", 1)
                gap_warn = f" — GAP={gap}s \u26a0 67% abandon rate (L-733)" if gap > 2 else ""
                lines.append(f"  \u26a0 {sl['lane']} (S{sl['opened']}) — {art_note}{gap_warn}")
            closeable = [sl for sl in stale_lanes if not sl["has_artifact"]]
            if closeable:
                lines.append("  Close stale (no artifact):")
                for sl in closeable[:3]:
                    lines.append(
                        f"    python3 tools/close_lane.py --lane {sl['lane']}"
                        f" --status ABANDONED --note 'stale — no artifact produced'"
                    )
            lines.append("")
        return lines, stale_lanes
    except Exception:
        return lines, []


def section_stale_experiments(check_fn):
    """Stale domain experiments (L-246)."""
    lines = []
    stale_experiments = check_fn()
    if stale_experiments:
        lines.append(f"--- Unrun domain experiments ({len(stale_experiments)}) ---")
        for e in stale_experiments[:6]:
            lines.append(f"  \u25cb {e}")
        lines.append("")
    return lines


def section_experiment_harvest_gap(check_fn):
    """Experiment harvest gap (F-IS7, L-578)."""
    lines = []
    try:
        harvest_gaps = check_fn(threshold=5)
        if harvest_gaps:
            lines.append(f"--- Experiment harvest gap ({len(harvest_gaps)} domains: \u22655 experiments, 0 lessons) ---")
            for domain, count in harvest_gaps[:6]:
                lines.append(f"  \U0001f4e6 {domain} ({count} experiments) — no lessons extracted yet")
            lines.append("")
    except Exception:
        pass
    return lines


def section_stale_baselines(session_num, check_fn):
    """Stale hardcoded baselines in tools (FM-20, L-820)."""
    lines = []
    try:
        stale = check_fn(session_num)
        if stale:
            lines.append(f"--- Stale baselines ({len(stale)} hardcoded session values >50s behind) ---")
            for s in stale[:5]:
                lines.append(f"  ! {s['file']}:{s['line']} = {s['value']} ({s['age']}s stale, {s['pattern']})")
            lines.append("")
    except Exception:
        pass
    return lines


def section_underused_tools(check_fn, log_text):
    """Underused core tools."""
    lines = []
    underused_tools, latest_sid, start_sid = check_fn(log_text)
    if underused_tools:
        window = "recent sessions"
        if latest_sid is not None and start_sid is not None:
            window = f"S{start_sid}..S{latest_sid}"
        lines.append(f"--- Underused core tools ({len(underused_tools)} in {window}) ---")
        for tool in underused_tools[:6]:
            lines.append(f"  \u25cb {tool}")
        lines.append("")
    return lines


def section_recent_commits(recent_commits):
    """Recent commits for collision avoidance (L-251)."""
    lines = []
    if recent_commits:
        lines.append("--- Recent commits (avoid repeating) ---")
        for c in recent_commits:
            lines.append(f"  \u2713 {c[:100]}")
        lines.append("")
    return lines


def section_session_log_tail(log_text, brief):
    """Session log tail (behavioral pattern)."""
    lines = []
    if not brief and log_text:
        from orient_state import extract_session_log_tail
        tail = extract_session_log_tail(log_text)
        if tail:
            lines.append("--- Recent sessions (behavioral pattern) ---")
            for entry in tail:
                lines.append(f"  {entry[:120]}")
            lines.append("")
    return lines


def section_agent_positions():
    """Agent positions (S340 council)."""
    lines = []
    try:
        from agent_state import get_position_summary
        positions = get_position_summary()
        if positions:
            lines.append(f"--- Active agents ({len(positions)}) ---")
            for p in positions:
                lines.append(f"  {p['session']} \u2192 {p['domain']} ({p.get('lane', '?')})")
            domains = [p["domain"] for p in positions]
            dupes = [d for d in set(domains) if domains.count(d) > 1]
            if dupes:
                lines.append(f"  \u26a0 COLLISION: multiple agents on: {', '.join(dupes)}")
            lines.append("")
    except Exception:
        pass
    return lines


def section_fairness(root=ROOT):
    """PHIL-25 fairness summary (L-1193) + F-COL1 concentration check."""
    lines = []
    try:
        from fairness_audit import run_audit
        results = run_audit()
        s = results.get("summary", {})
        score = s.get("fairness_score", 0)
        fair_n = s.get("fair_dimensions", 0)
        total_n = s.get("total_dimensions", 5)
        overall = s.get("overall", "?")
        unfair = [d["dimension"].upper() for d in results.get("dimensions", [])
                  if not d.get("fair")]
        lines.append("--- Fairness (PHIL-25, L-1193) ---")
        lines.append(f"  Score: {score} ({fair_n}/{total_n}) — {overall}")
        if unfair:
            lines.append(f"  Unfair: {', '.join(unfair)}")
        lines.append("  Run: python3 tools/fairness_audit.py")
    except Exception:
        pass
    # F-COL1: dispatch concentration / effective diversity (L-1587)
    try:
        import re
        from collections import Counter
        lanes_path = root / "tasks" / "SWARM-LANES-ARCHIVE.md"
        if lanes_path.exists():
            archive = lanes_path.read_text(errors="replace")
            domain_lanes = re.findall(r"DOMEX-(\w+)-S\d+", archive)
            if len(domain_lanes) > 20:
                counts = Counter(domain_lanes)
                total = sum(counts.values())
                n_domains = len(counts)
                vals = sorted(counts.values())
                n = len(vals)
                numer = sum((2 * i - n - 1) * v for i, v in enumerate(vals, 1))
                gini = numer / (n * total) if total > 0 else 0
                eff_div = round(1 / (1 - gini), 1) if gini < 1 else n_domains
                top_dom, top_count = counts.most_common(1)[0]
                top_share = top_count / total * 100
                lines.append(f"  Dispatch diversity: {eff_div:.0f} effective / {n_domains} named (Gini {gini:.3f})")
                if top_share > 15:
                    lines.append(f"    \u26a0 {top_dom} = {top_share:.1f}% of lanes — mediocrity selection risk (F-COL1)")
    except Exception:
        pass
    lines.append("")
    return lines


def section_challenge_cadence(session_num, check_fn):
    """Challenge cadence DUE (L-1597, F-MATH12: 497:1 cost ratio, +27.2 EV per challenge)."""
    lines = []
    try:
        result = check_fn(session_num)
        if result["due"]:
            gap = result["gap"]
            lines.append(f"--- Challenge cadence (F-MATH12) ---")
            lines.append(f"  \u26a0 DUE: 0 challenge records detected this session (gap={gap}s)")
            lines.append(f"  Every challenge is +EV (27.2 sessions saved, 497:1 cost ratio)")
            lines.append(f"  Pick one claim and test it adversarially:")
            lines.append(f"    python3 tools/philosophy_audit.py --pick")
            lines.append(f"    Then file a row in beliefs/CHALLENGES.md or beliefs/PHILOSOPHY.md")
            lines.append("")
    except Exception:
        pass
    return lines


def section_suggested_action(maint_out, open_signals, stall_map, priorities):
    """Suggested next action (concurrency-aware via L-526)."""
    lines = ["--- Suggested next action ---"]
    try:
        from claim import get_active_sessions
        n_concurrent = len(get_active_sessions())
    except Exception:
        n_concurrent = 0
    if n_concurrent >= 3:
        lines.append(f"  \u26a0 N={n_concurrent} concurrent: prefer verification/historian/novel work")
    if "URGENT" in maint_out:
        urgent_lines = [l.strip() for l in maint_out.splitlines() if "URGENT" in l]
        for l in urgent_lines[:2]:
            lines.append(f"  URGENT: {l}")
    elif "[DUE]" in maint_out:
        due_lines = [l.strip() for l in maint_out.splitlines() if l.strip().startswith("!")]
        for l in due_lines[:2]:
            lines.append(f"  DUE: {l.lstrip('! ')}")
    elif open_signals and any(s["priority"] == "P1" and s.get("age", 0) > 30 for s in open_signals):
        stale_p1 = [s for s in open_signals if s["priority"] == "P1" and s.get("age", 0) > 30]
        for s in stale_p1[:2]:
            lines.append(f"  SIGNAL-DUE: {s['id']} ({s['age']}s old, P1): {s['content'][:70]}")
        lines.append(f"  Resolve: `python3 tools/swarm_signal.py resolve {stale_p1[0]['id']} \"<resolution>\"`")
    elif "[PERIODIC]" in maint_out:
        periodic_lines = [l.strip() for l in maint_out.splitlines() if l.strip().startswith("~")]
        for l in periodic_lines[:2]:
            lines.append(f"  PERIODIC: {l.lstrip('~ ')}")
    elif stall_map:
        top_fid, top_dom = next(iter(sorted(stall_map.items())))
        lines.append(f"  STALL: {top_fid} ({top_dom}) in 2-wave valley — open hardening lane to escape (11%\u219231%)")
        if len(stall_map) > 1:
            lines.append(f"  ({len(stall_map)} total stalled: {', '.join(sorted(stall_map)[:5])})")
    else:
        # Check r/K ratio for integration debt (L-1382)
        try:
            import subprocess as _sp
            _new = len([l for l in _sp.run(["git", "log", "--oneline", "--diff-filter=A", "--name-only", "-10", "--", "memory/lessons/L-*.md"], capture_output=True, text=True, timeout=5).stdout.splitlines() if l.startswith("memory/lessons/L-") and l.endswith(".md")])
            _mod = len([l for l in _sp.run(["git", "log", "--oneline", "--diff-filter=M", "--name-only", "-10", "--", "memory/lessons/L-*.md"], capture_output=True, text=True, timeout=5).stdout.splitlines() if l.startswith("memory/lessons/L-") and l.endswith(".md")])
            _rk = _new / max(_mod, 1)
            if _rk > 10:
                lines.append(f"  \u26a0 r/K={_rk:.0f} — integration session recommended: archive EXPIRED, revive DECAYED, compress (L-1382)")
                return lines
        except Exception:
            pass
        if priorities:
            lines.append(f"  {priorities[0]}")
        else:
            lines.append("  State clean — pick a frontier or run a periodic")
    return lines
