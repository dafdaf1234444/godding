#!/usr/bin/env python3
"""
orient_sections.py — Display sections for orient.py main() output.

Extracted from orient.py (DOMEX-META-S426). Each function returns a list of
output lines for one section of the orient display. main() in orient.py
calls these in sequence and prints.

Pattern: section_xxx(data) -> list[str]
"""

import json
import re
import subprocess
import sys
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
    """Open signals (L-703, L-803, L-808)."""
    lines = []
    if open_signals:
        lines.append(f"--- Open signals ({len(open_signals)} unresolved) ---")
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


def section_precompact_checkpoint(session, root=ROOT):
    """PreCompact checkpoint notice (F-CC3, L-342)."""
    lines = []
    checkpoints = sorted((root / "workspace").glob("precompact-checkpoint-*.json"))
    if not checkpoints:
        return lines
    latest = checkpoints[-1]
    try:
        cp = json.loads(latest.read_text())
        uncommitted = cp.get("uncommitted_files", [])
        if uncommitted:
            status_out = subprocess.run(
                ["git", "status", "--short"], capture_output=True, text=True, cwd=str(root)
            ).stdout
            status_files = {line.split()[-1] for line in status_out.strip().split("\n") if line.strip()}
            still_uncommitted = [f for f in uncommitted if f in status_files]
            stale_ratio = 1 - (len(still_uncommitted) / len(uncommitted)) if uncommitted else 1
        else:
            still_uncommitted = []
            stale_ratio = 1
        # Session-age filter
        cp_session = 0
        for log_line in cp.get("recent_git_log", []):
            m = re.search(r'\[S(\d+)\]', log_line)
            if m:
                cp_session = int(m.group(1))
                break
        cur_session_num = int(session[1:]) if session[1:].isdigit() else 0
        session_age = (cur_session_num - cp_session) if cp_session else 999
        if stale_ratio < 0.8 and session_age <= 2:
            lines.append("--- !! COMPACTION RESUME DETECTED ---")
            lines.append(f"  Checkpoint: {latest.name} ({cp.get('trigger', '?')} at {cp.get('timestamp', '?')})")
            hint = cp.get("next_md", {}).get("For next session", "")
            if hint:
                lines.append(f"  In-flight: {hint[:120].splitlines()[0]}")
            if still_uncommitted:
                lines.append(f"  Uncommitted files ({len(still_uncommitted)}/{len(uncommitted)}): {', '.join(still_uncommitted[:5])}")
            lines.append("")
    except Exception:
        pass
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


def section_self_application(session_num, check_fn):
    """Self-application gap — CORE P14: infrastructure subject to swarm dynamics."""
    lines = []
    try:
        stale_infra = check_fn(session_num)
        if stale_infra:
            lines.append(f"--- Self-application gap ({len(stale_infra)} components not evolved >50s) ---")
            for si in stale_infra:
                lines.append(f"  \u2298 {si}")
            if len(stale_infra) >= 1:
                lines.append("  Suggested (pick 1):")
                for si in stale_infra[:3]:
                    tool_name = si.split("(")[0].strip().replace(" ", "-")
                    lines.append(
                        f"    python3 tools/open_lane.py --lane EVOLVE-{tool_name}-S{session_num}"
                        f" --session S{session_num}"
                        f" --expect 'modernize-{tool_name}'"
                        f" --artifact 'tools/{si.split('(')[0].strip()}'"
                        f" --intent 'P14: evolve stale infrastructure'"
                    )
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


def section_pci(session_num, compute_fn, root=ROOT):
    """Scientific Rigor — Protocol Compliance Index (PCI)."""
    lines = []
    try:
        pci_result = compute_fn(session_num)
        pci_val = pci_result["pci"]
        d = pci_result["details"]
        lines.append("--- Scientific Rigor (PCI) ---")
        lines.append(f"  PCI: {pci_val:.3f} (target >0.10)")
        lines.append(f"  EAD field presence: {pci_result['ead']:.0%} ({d['ead']} lanes with actual+diff — L-813: measures field presence, not prediction quality)")
        lines.append(f"  Belief freshness: {pci_result['belief_freshness']:.0%} ({d['belief_freshness']} tested <50 sessions)")
        lines.append(f"  Frontier testability: {pci_result['frontier_testability']:.0%} ({d['frontier_testability']} with test evidence)")
        # Knowledge state from cached artifact
        try:
            ks_files = sorted((root / "experiments" / "meta").glob("knowledge-state-s*.json"))
            if ks_files:
                ks_data = json.loads(ks_files[-1].read_text())
                ks_m = re.search(r"knowledge-state-s(\d+)", ks_files[-1].name)
                ks_age = (session_num - int(ks_m.group(1))) if ks_m else -1
                if 0 <= ks_age <= 20:
                    dist = ks_data.get("global_states", {})
                    total = sum(dist.values()) or 1
                    blind = dist.get("BLIND-SPOT", 0)
                    decayed = dist.get("DECAYED", 0)
                    age_note = f"S{ks_m.group(1)}" + (f", {ks_age}s ago" if ks_age > 0 else "")
                    lines.append(f"  Knowledge attention ({age_note}): BLIND-SPOT {blind/total:.1%} | DECAYED {decayed/total:.1%} (L-813: citation-recency, not validity — actual false knowledge ~5-10%) | refresh: python3 tools/knowledge_state.py --json")
        except Exception:
            pass
        # Science quality from cached artifact
        try:
            sq_files = sorted((root / "experiments" / "meta").glob("science-quality-s*.json"))
            if sq_files:
                sq_data = json.loads(sq_files[-1].read_text())
                sq_m = re.search(r"science-quality-s(\d+)", sq_files[-1].name)
                sq_age = (session_num - int(sq_m.group(1))) if sq_m else -1
                if -5 <= sq_age <= 30:
                    mean_q = sq_data.get("mean_quality", 0)
                    pre_reg = sq_data.get("criteria_means", {}).get("pre_registration", 0)
                    falsif = sq_data.get("falsification_lanes", "?/0")
                    age_note = f"S{sq_m.group(1)}" + (f", {sq_age}s ago" if sq_age > 0 else "")
                    lines.append(f"  Science quality ({age_note}): mean {mean_q:.0%} | pre-reg {pre_reg:.0%} | falsif lanes {falsif} | refresh: python3 tools/science_quality.py --json")
        except Exception:
            pass
        # Bayesian calibration
        try:
            bm_files = sorted((root / "experiments" / "meta").glob("bayes-meta-s*.json"))
            if bm_files:
                bm_data = json.loads(bm_files[-1].read_text())
                bm_m = re.search(r"bayes-meta-s(\d+)", bm_files[-1].name)
                bm_age = (session_num - int(bm_m.group(1))) if bm_m else -1
                if -5 <= bm_age <= 30:
                    ece = bm_data.get("results", {}).get("ece", "?")
                    n_front = bm_data.get("n_frontiers_with_posteriors", "?")
                    age_note2 = f"S{bm_m.group(1)}" + (f", {bm_age}s ago" if bm_age > 0 else "")
                    ece_flag = " \u26a0 OVERCONFIDENT" if isinstance(ece, float) and ece > 0.15 else ""
                    lines.append(f"  Bayesian calibration ({age_note2}): ECE={ece:.3f}{ece_flag} | {n_front} frontiers | refresh: python3 tools/bayes_meta.py --json > experiments/meta/bayes-meta-s<N>.json")
        except Exception:
            pass
        if pci_val < 0.10:
            lines.append("  Tip: check `beliefs/CHALLENGES.md` for untested beliefs and open a DOMEX lane")
        lines.append("")
    except Exception:
        pass
    return lines


def section_prescription_gap(root=ROOT):
    """Prescription gap (L-831/L-843/L-875)."""
    lines = []
    try:
        er_path = root / "tools" / "enforcement_router.py"
        if er_path.exists():
            er_result = subprocess.run(
                [sys.executable, str(er_path), "--json", "--min-sharpe", "9"],
                capture_output=True, text=True, timeout=10
            )
            if er_result.returncode == 0:
                er_data = json.loads(er_result.stdout)
                act_rate = er_data.get("actionable_gap_rate", 0)
                n_act = er_data.get("actionable_aspirational_count", 0)
                n_obs = er_data.get("observational_aspirational_count", 0)
                hs_asp = er_data.get("high_sharpe_aspirational", [])
                if act_rate > 0.15:
                    lines.append("--- Prescription Gap (L-843) ---")
                    lines.append(f"  ASPIRATIONAL (unimplemented): {act_rate:.0%} of rule-bearing lessons ({n_act} actionable, {n_obs} observational)")
                    act_gaps = [h for h in hs_asp if h.get("actionable")]
                    if act_gaps:
                        top = act_gaps[0]
                        lines.append(f"  Top gap: {top['lesson']} Sh={top['sharpe']} — {top['rule'][:70]}")
                    lines.append("  Full report: python3 tools/enforcement_router.py")
                    lines.append("")
    except Exception:
        pass
    return lines


def section_level_balance(root=ROOT):
    """Level balance check (L-895/SIG-46)."""
    lines = []
    try:
        import glob as _glob_lvl
        lesson_files = sorted(_glob_lvl.glob(str(root / "memory" / "lessons" / "L-*.md")))
        if len(lesson_files) >= 10:
            recent_n = lesson_files[-10:]
            l3plus_kw = ["strategy", "campaign", "architecture", "organizational",
                         "paradigm", "redesign", "direction", "what should", "reframing",
                         "missing layer", "system design", "philosophy", "identity"]
            l3plus_count = 0
            for lf in recent_n:
                try:
                    txt = Path(lf).read_text()
                    if re.search(r"[Ll]evel[=:\s]+L[3-5]", txt):
                        l3plus_count += 1
                        continue
                    txt_lower = txt.lower()
                    if any(k in txt_lower for k in l3plus_kw):
                        l3plus_count += 1
                except Exception:
                    pass
            if l3plus_count == 0:
                lines.append("--- Level Imbalance (L-895, SIG-46) ---")
                lines.append(f"  \u26a0 0/{len(recent_n)} recent lessons at L3+ (strategy/architecture/paradigm)")
                lines.append("  Swarm is 100% measurement. Consider: strategic direction, architecture review,")
                lines.append("  or paradigm challenge instead of another DOMEX experiment.")
                lines.append("")
    except Exception:
        pass
    return lines


def section_stalled_campaigns(root=ROOT):
    """Stalled 2-wave campaigns (F-STR3, L-845)."""
    stall_map: dict[str, str] = {}
    lines = []
    try:
        stall_result = subprocess.run(
            [sys.executable, str(root / "tools" / "dispatch_optimizer.py"), "--json", "--all"],
            capture_output=True, text=True, timeout=15
        )
        if stall_result.returncode == 0:
            stall_data = json.loads(stall_result.stdout)
            for d in stall_data:
                for fid in (d.get("wave_2_stalls") or []):
                    stall_map[fid] = d["domain"]
    except Exception:
        pass
    if stall_map:
        lines.append(f"--- Stalled Campaigns ({len(stall_map)} frontiers in 2-wave valley — 11% resolve) ---")
        for fid, dom in sorted(stall_map.items())[:8]:
            lines.append(f"  \u26a0 {fid} ({dom}) — needs hardening lane (mode shift required)")
        lines.append("  Fix: open DOMEX-<DOM>-S<N> with --mode hardening for any of the above")
        lines.append("")
    return lines, stall_map


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


def section_concurrent_activity(root=ROOT):
    """Active sessions and task claims (L-686)."""
    lines = []
    try:
        sys.path.insert(0, str(root / "tools"))
        from claim import get_active_sessions, get_active_task_claims
        sessions = get_active_sessions()
        task_claims = get_active_task_claims()
        if sessions or task_claims:
            lines.append("--- Concurrent activity ---")
            if sessions:
                for s in sessions[:5]:
                    label = s.get("current_task", "(idle)")
                    if s.get("description"):
                        label += f": {s['description'][:40]}"
                    lines.append(f"  {s['session']:15s} {s['age_s']:4d}s ago  {label}")
            if task_claims:
                lines.append(f"  Task claims: {', '.join(task_claims.keys())}")
            lines.append("")
    except Exception:
        pass
    return lines


def section_historian_repair(root=ROOT):
    """Historian repair — SIG-39."""
    lines = []
    try:
        hr_result = subprocess.run(
            ["python3", "tools/historian_repair.py", "--json"],
            capture_output=True, text=True, cwd=str(root), timeout=15
        )
        if hr_result.returncode == 0:
            hr_data = json.loads(hr_result.stdout)
            high_items = [i for i in hr_data.get("items", []) if i.get("severity") == "HIGH"]
            if high_items:
                lines.append(f"--- Historian repair ({hr_data.get('total', 0)} stale, {len(high_items)} HIGH) ---")
                cat_icons = {"beliefs": "\U0001f534", "frontiers": "\U0001f7e1", "domains": "\u26aa"}
                for item in high_items[:3]:
                    icon = cat_icons.get(item.get("category", ""), "\u25cb")
                    lines.append(f"  {icon} [{item['item_id']}] {item['category']} — stale {item['sessions_stale']}s — {item['description'][:60]}")
                if len(high_items) > 3:
                    lines.append(f"  ... and {len(high_items) - 3} more HIGH items")
                lines.append("  Run: python3 tools/historian_repair.py")
                lines.append("")
    except Exception:
        pass
    return lines


def section_meta_tooler(root=ROOT):
    """Meta-tooler scan — SIG-39."""
    lines = []
    try:
        mt_result = subprocess.run(
            ["python3", "tools/meta_tooler.py", "--json"],
            capture_output=True, text=True, cwd=str(root), timeout=30
        )
        if mt_result.returncode == 0:
            mt_data = json.loads(mt_result.stdout)
            mt_high = mt_data.get("high", 0)
            mt_med = mt_data.get("medium", 0)
            if mt_high > 0 or mt_med > 5:
                lines.append(f"--- Meta-tooler ({mt_data['total_tools']} tools, "
                             f"HIGH={mt_high} MEDIUM={mt_med}) ---")
                for f in mt_data.get("findings", []):
                    if f["severity"] == "HIGH":
                        lines.append(f"  \U0001f534 [{f['category']}] {f['tool']}: {f['message']}")
                lines.append("  Run: python3 tools/meta_tooler.py")
                lines.append("")
    except Exception:
        pass
    return lines


def section_suggested_action(maint_out, open_signals, stall_map, priorities):
    """Suggested next action."""
    lines = ["--- Suggested next action ---"]
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
    elif priorities:
        lines.append(f"  {priorities[0]}")
    else:
        lines.append("  State clean — pick a frontier or run a periodic")
    return lines
