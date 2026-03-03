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
    checkpoints = sorted((root / "workspace").glob("precompact-checkpoint-*.json"),
                         key=lambda p: p.stat().st_mtime)
    if not checkpoints:
        return lines
    latest = checkpoints[-1]  # most recently modified checkpoint
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
            staged = cp.get("staged_files", [])
            if staged:
                lines.append(f"  ⚠ STAGED FILES ({len(staged)}): {', '.join(staged[:5])}")
                lines.append(f"    Run: git reset HEAD -- <files> before staging new work (FM-19 stale-write risk)")
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
        # Mission sufficiency from cached eval-sufficiency artifact (F-EVAL4, L-979)
        # Shows continuous composite score so health is visible without re-running.
        try:
            es_files = sorted((root / "experiments" / "evaluation").glob("eval-sufficiency-s*.json"))
            if es_files:
                es_data = json.loads(es_files[-1].read_text())
                es_m = re.search(r"eval-sufficiency-s(\d+)", es_files[-1].name)
                es_age = (session_num - int(es_m.group(1))) if es_m else -1
                if -5 <= es_age <= 50:
                    overall = es_data.get("overall", "?")
                    cont = es_data.get("continuous_composite", es_data.get("composite_normalized"))
                    nxt = es_data.get("next_improvement_target", "?")
                    age_note = f"S{es_m.group(1)}" + (f", {es_age}s ago" if es_age > 0 else "")
                    cont_str = f" ({cont:.0%} continuous)" if cont is not None else ""
                    lines.append(f"  Mission sufficiency ({age_note}): {overall}{cont_str} — next: {nxt} | refresh: python3 tools/eval_sufficiency.py --save")
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


def section_succession_phase(root=ROOT):
    """Attention carrying capacity / r-K phase indicator (L-1121).

    Nature→swarm prescription: in biological succession, carrying capacity
    shifts the optimal strategy from r-selected (produce many) to K-selected
    (maintain well). In information systems, the carrying capacity is attention
    per lesson (1/N), not storage. Emits NOTICE when attention pressure exceeds
    the functional threshold.
    """
    lines = []
    try:
        import glob as _gl
        lesson_files = _gl.glob(str(root / "memory" / "lessons" / "L-*.md"))
        n_lessons = len(lesson_files)
        if n_lessons < 100:
            return lines

        # Attention pressure: 1/N (fraction of session attention per lesson)
        attention_per_lesson = 1.0 / n_lessons
        # Functional threshold: below this, lessons decay faster than maintained
        # Estimated from integration-bound crossover at N~550 (L-912)
        threshold = 1.0 / 500

        # r/K ratio: count new lessons vs cross-reference additions in recent commits
        try:
            new_result = subprocess.run(
                ["git", "log", "--oneline", "--diff-filter=A", "--name-only", "-10",
                 "--", "memory/lessons/L-*.md"],
                capture_output=True, text=True, cwd=str(root), timeout=5
            )
            new_lessons = len([l for l in new_result.stdout.splitlines()
                              if l.startswith("memory/lessons/L-") and l.endswith(".md")])
            mod_result = subprocess.run(
                ["git", "log", "--oneline", "--diff-filter=M", "--name-only", "-10",
                 "--", "memory/lessons/L-*.md"],
                capture_output=True, text=True, cwd=str(root), timeout=5
            )
            modified_lessons = len([l for l in mod_result.stdout.splitlines()
                                   if l.startswith("memory/lessons/L-") and l.endswith(".md")])
        except Exception:
            new_lessons = 0
            modified_lessons = 0

        if attention_per_lesson < threshold:
            ratio_str = f"{n_lessons / 500:.1f}x"
            lines.append("--- Succession Phase (L-1121) ---")
            lines.append(f"  Attention carrying capacity: {ratio_str} past threshold (N={n_lessons}, K_threshold=500)")
            lines.append(f"  Attention per lesson: {attention_per_lesson:.5f} (threshold: {threshold:.4f})")
            if new_lessons > 0 or modified_lessons > 0:
                r_k = new_lessons / max(modified_lessons, 1)
                mode = "r-mode (producing)" if r_k > 2 else "K-mode (integrating)" if r_k < 0.5 else "balanced"
                lines.append(f"  Recent r/K: {new_lessons} new / {modified_lessons} modified = {r_k:.1f} ({mode})")
                if r_k > 3:
                    lines.append("  \u26a0 High r/K ratio — consider integration: compact, cross-reference, revive DECAYED")
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


def section_cascade_state(maint_output: str = None):
    """Cross-layer cascade monitor (F-FLT4, L-1018, P-303). Only shown when layers failing."""
    lines = []
    try:
        import sys
        from pathlib import Path
        from concurrent.futures import ThreadPoolExecutor
        sys.path.insert(0, str(Path(__file__).parent))
        from cascade_monitor import (
            check_tool_layer, check_quality_layer, check_knowledge_layer,
            check_evaluation_layer, check_attention_layer, detect_cascades,
        )
        # Parallelize independent layer checks (Q=8.5s, E=5s dominate when sequential)
        # Pass maint_output to Q layer to avoid redundant maintenance.py subprocess call
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {
                "T": pool.submit(check_tool_layer),
                "Q": pool.submit(check_quality_layer, maint_output),
                "K": pool.submit(check_knowledge_layer),
                "E": pool.submit(check_evaluation_layer),
                "A": pool.submit(check_attention_layer),
            }
        layers = {k: v.result() for k, v in futures.items()}
        failing = [k for k, v in layers.items() if v.get("failing")]
        cascades = detect_cascades(layers)
        if cascades:
            lines.append(f"--- CASCADE ALERT ({len(cascades)} active cascades) ---")
            for c in cascades:
                lines.append(f"  ! {c['layers']} (severity={c['severity']})")
            lines.append("")
        elif failing:
            failing_str = ", ".join(f"{k}:{layers[k].get('evidence','')}" for k in failing)
            lines.append(f"  NOTICE: cascade layers failing (no cascade yet): {failing_str}")
    except Exception:
        pass
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


def _item_resolved_by_actual(canon: str, actual_texts: list[str]) -> bool:
    """Check if a canonical next-item was addressed in any actual: field.

    Uses keyword overlap: if >=2 significant tokens from the canonical item
    appear in any actual text, consider it resolved.
    """
    stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "is",
                  "and", "or", "with", "from", "by", "as", "its", "it", "be",
                  "was", "were", "has", "had", "not", "no", "but", "if", "so",
                  "that", "this", "than", "more", "very", "just", "also", "all",
                  "each", "per", "any", "s", "yet", "re", "vs"}
    # Extract significant tokens (letters/digits, >=3 chars, not stop words)
    # Split word-compound hyphens (claim-vs-evidence → claim, evidence)
    # but keep identifiers intact (FM-30, ISO-7 stay as-is)
    import re as _re
    raw_tokens = _re.findall(r'[A-Za-z0-9_-]{3,}', canon)
    tokens: set[str] = set()
    for t in raw_tokens:
        # Only split if all hyphen-parts are alphabetic words (not IDs like FM-30)
        parts = t.split('-')
        if len(parts) > 1 and all(p.isalpha() and len(p) >= 2 for p in parts):
            tokens.update(p.lower() for p in parts if len(p) >= 3)
        else:
            tokens.add(t.lower())
    tokens -= stop_words
    if len(tokens) < 2:
        return False  # too few tokens to match reliably
    for actual in actual_texts:
        actual_lower = actual.lower()
        matches = sum(1 for t in tokens if t in actual_lower)
        if matches >= 2 and matches >= len(tokens) * 0.4:
            return True
    return False


def section_zombie_carryover(root=ROOT):
    """Zombie items + carried-over% from NEXT.md session trails (L-978 TG-2/TG-4)."""
    lines = []
    try:
        sys.path.insert(0, str(root / "tools"))
        from trails_generalizer import parse_session_notes, canonicalize
        next_path = root / "tasks" / "NEXT.md"
        if not next_path.exists():
            return lines
        text = next_path.read_text(encoding="utf-8")
        notes = parse_session_notes(text)
        if len(notes) < 2:
            return lines

        # Collect all actual: texts for cross-referencing resolved items
        actual_texts = [n.get("actual_text", "") for n in notes if n.get("actual_text")]

        # Count canonical recurrences across all parsed sessions
        from collections import Counter
        item_counter = Counter()
        for note in notes:
            seen: set[str] = set()
            for item in note["next_items"]:
                canon = canonicalize(item)
                if canon not in seen:
                    item_counter[canon] += 1
                    seen.add(canon)

        # Load explicitly dropped zombies (zombie_drops.json)
        dropped_zombies: set[str] = set()
        try:
            import json as _json
            drops_path = root / "tools" / "zombie_drops.json"
            if drops_path.exists():
                drops_data = _json.loads(drops_path.read_text(encoding="utf-8"))
                dropped_zombies = {e.get("canonical", "") for e in drops_data.get("drops", []) if e.get("canonical")}
        except Exception:
            pass

        # Items resolved by actual: fields (cross-reference fix for false positives)
        resolved_items: set[str] = set()
        for canon in item_counter:
            if _item_resolved_by_actual(canon, actual_texts):
                resolved_items.add(canon)

        # Combined exclusion set
        excluded = dropped_zombies | resolved_items

        # Zombie items: appearing in 5+ sessions (TG-2), excluding dropped + resolved
        zombies = [(item, count) for item, count in item_counter.most_common()
                   if count >= 5 and item not in excluded]

        # Carried-over% for latest session (TG-4) — filter dropped + resolved
        latest = notes[-1]
        prior_items: set[str] = set()
        for note in notes[-6:-1]:  # previous 5 sessions
            for item in note["next_items"]:
                prior_items.add(canonicalize(item))
        latest_items = [canonicalize(it) for it in latest["next_items"]
                        if canonicalize(it) not in excluded]
        if latest_items:
            carried = sum(1 for it in latest_items if it in prior_items)
            pct = carried / len(latest_items) * 100
        else:
            pct = 0.0

        if zombies or pct >= 30:
            lines.append(f"--- Zombie Items (L-978 TG-2/TG-4) ---")
            if pct >= 30:
                lines.append(f"  \u26a0 Carried-over: {pct:.0f}% ({carried}/{len(latest_items)}) — target <30%")
            else:
                lines.append(f"  Carried-over: {pct:.0f}% ({carried}/{len(latest_items)})")
            if zombies:
                lines.append(f"  Zombies ({len(zombies)} items recurring 5+ sessions):")
                for item, count in zombies[:5]:
                    lines.append(f"    \U0001f480 {count:3d}x  {item[:60]}")
            if resolved_items:
                lines.append(f"  Resolved by actual: {len(resolved_items)} item(s) excluded")
            lines.append("")
    except Exception:
        pass
    return lines


def section_closure_metric(root=ROOT):
    """Trail-provenance closure metric (L-1118, L-1125)."""
    lines = []
    try:
        import glob as _glob_closure
        lesson_files = sorted(_glob_closure.glob(str(root / "memory" / "lessons" / "L-*.md")))
        if len(lesson_files) < 20:
            return lines
        recent = lesson_files[-20:]
        external_markers = ["arxiv", "doi:", "http://", "https://", "10.", "et al"]
        ext_count = 0
        for lf in recent:
            try:
                txt = Path(lf).read_text(encoding="utf-8")
                cites_match = re.search(r"^\*{0,2}Cites\*{0,2}:\s*(.+)", txt, re.MULTILINE)  # L-1169
                if not cites_match:
                    continue
                cites_line = cites_match.group(1).lower()
                if any(m in cites_line for m in external_markers):
                    ext_count += 1
            except Exception:
                pass
        ext_pct = ext_count / len(recent) * 100
        if ext_pct < 20:
            lines.append("--- External Closure (L-1118, L-1125) ---")
            lines.append(f"  \u26a0 Trail provenance: {ext_pct:.0f}% external ({ext_count}/{len(recent)} recent Cites: headers)")
            lines.append("  Cites: headers reference only internal artifacts.")
            lines.append("  L-1125: trail provenance is cheapest break point.")
            lines.append("")
    except Exception:
        pass
    return lines


def section_knowledge_swarm(root=ROOT):
    """Knowledge self-organization (SIG-62, L-1121, S457): revive/compress/crosslink/orphan."""
    lines = []
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from knowledge_swarm import (
            parse_lesson_meta, build_citation_maps, classify_items,
            revive_candidates, compress_candidates, crosslink_suggestions,
            detect_orphaned_principles, section_output,
        )
        from swarm_io import session_number, lesson_paths
        current = session_number()
        lessons = {}
        for path in lesson_paths():
            meta = parse_lesson_meta(path)
            if meta:
                lessons[meta["id"]] = meta
        if len(lessons) < 100:
            return lines
        outbound, inbound = build_citation_maps(lessons)
        states = classify_items(lessons, inbound, current)
        results = {
            "revival": revive_candidates(lessons, states, inbound, current),
            "compress": compress_candidates(lessons, states, inbound, current),
            "crosslinks": crosslink_suggestions(lessons, states, inbound, outbound),
            "orphaned_principles": detect_orphaned_principles(lessons, states),
        }
        lines = section_output(results, current)
    except Exception:
        pass
    return lines


def section_correction_propagation(root=ROOT):
    """Correction propagation gaps (L-1132, L-1097, F-IC1)."""
    lines = []
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from correction_propagation import run_analysis
        from swarm_io import session_number
        result = run_analysis(session=session_number(), classify=True)
        total = result.get("total_uncorrected_citations", 0)
        rate = result.get("avg_correction_rate", 1.0)
        queue = result.get("correction_queue", [])
        high = [q for q in queue if q.get("priority") == "HIGH"]
        if high:
            lines.append("")
            lines.append("--- Correction Propagation (L-1132) ---")
            lines.append(f"  {total} uncorrected citations | {len(high)} HIGH priority | correction rate {rate:.0%}")
            for item in high[:5]:
                lines.append(f"  -> {item['citer']} cites falsified {item['needs_correction_about']} (content-dependent)")
            lines.append("  Run: python3 tools/correction_propagation.py")
    except Exception:
        pass
    return lines


def section_knowledge_recombination(root=ROOT):
    """Knowledge recombination candidates (SIG-62, knowledge_recombine.py).

    Lesson pairs with shared citations but no direct link — semantic gaps
    where new knowledge can be synthesized. Reads cached JSON artifact.
    """
    lines = []
    try:
        kr_dir = root / "experiments" / "meta"
        kr_files = sorted(kr_dir.glob("knowledge-recombine-s*.json"))
        if not kr_files:
            return lines
        data = json.loads(kr_files[-1].read_text(encoding="utf-8"))
        candidates = data.get("top", [])
        cross = [
            c for c in candidates
            if c.get("cross_domain") and c.get("score", 0) >= 40
        ]
        if not cross:
            return lines
        lines.append("--- Knowledge Recombination (SIG-62) ---")
        lines.append(
            f"  {data.get('total_candidates', '?')} candidate pairs"
            f" ({data.get('cross_domain_candidates', '?')} cross-domain)"
        )
        for i, c in enumerate(cross[:3], 1):
            ta = c.get("title_a", "")[:55]
            tb = c.get("title_b", "")[:55]
            shared = ", ".join(c.get("shared_refs", [])[:4])
            lines.append(
                f"  [{i}] {c['parent_a']} x {c['parent_b']}"
                f" (score={c['score']})"
            )
            lines.append(f"      {ta}")
            lines.append(f"      x {tb}")
            lines.append(f"      Shared: {shared}")
        lines.append(
            "  Refresh: python3 tools/knowledge_recombine.py --json"
            " > experiments/meta/knowledge-recombine-s<N>.json"
        )
        lines.append("")
    except Exception:
        pass
    return lines


def _active_domex_domains(root=ROOT):
    """Return set of domains with active DOMEX lanes (L-1169: concurrency check)."""
    lanes_path = root / "tasks" / "SWARM-LANES.md"
    active = set()
    if not lanes_path.exists():
        return active
    for line in lanes_path.read_text().splitlines():
        if "DOMEX-" not in line:
            continue
        # Active statuses are not MERGED/ABANDONED
        if "| MERGED |" in line or "| ABANDONED |" in line:
            continue
        # Extract domain from lane ID: DOMEX-<DOMAIN>-S<N>
        m = re.search(r"DOMEX-([A-Z]+)-S\d+", line)
        if m:
            active.add(m.group(1).lower())
    return active


def section_epsilon_dispatch(session_num, root=ROOT):
    """ε-dispatch diversity recommendation (F-RAND1, L-601 structural enforcement).

    With probability ε=0.15, recommends a random non-top domain to break UCB1
    rich-get-richer lock. Surfaced in orient so sessions see it (L-1138: naming > ranking).
    L-1169: checks active DOMEX lanes to avoid recommending already-claimed domains.
    """
    import random as _random
    lines = []
    epsilon = 0.15
    if session_num <= 0:
        return lines
    rng = _random.Random(session_num)
    roll = rng.random()
    if roll >= epsilon:
        return lines
    try:
        result = subprocess.run(
            [sys.executable, str(root / "tools" / "dispatch_optimizer.py"), "--json", "--all"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return lines
        data = json.loads(result.stdout)
        if len(data) < 2:
            return lines
        top_domain = data[0].get("domain", "unknown")
        active_domains = _active_domex_domains(root)
        # Filter out domains with active DOMEX lanes (L-1169)
        candidates = [d for i, d in enumerate(data) if i > 0
                      and d.get("domain", "").lower() not in active_domains]
        if not candidates:
            lines.append("--- \u26a1 \u03b5-dispatch fired but all candidates have active lanes ---")
            lines.append(f"  {len(active_domains)} domains claimed. Skipping diversity override.")
            lines.append("")
            return lines
        rand_idx = rng.randint(0, len(candidates) - 1)
        pick = candidates[rand_idx]
        pick_domain = pick.get("domain", "unknown")
        pick_frontier = pick.get("first_frontier", "")
        lines.append("--- \u26a1 \u03b5-dispatch fired (F-RAND1, L-601) ---")
        lines.append(f"  Diversity override: work on **{pick_domain}** instead of {top_domain}")
        if pick_frontier:
            lines.append(f"  Target frontier: {pick_frontier}")
        lines.append(f"  \u03b5-roll {roll:.3f} < {epsilon} \u2014 breaking UCB1 concentration (Gini 0.506)")
        if active_domains:
            lines.append(f"  ({len(active_domains)} domains filtered: active DOMEX lanes)")
        lines.append(f"  Open a DOMEX lane for {pick_domain}.")
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
