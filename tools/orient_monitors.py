#!/usr/bin/env python3
"""
orient_monitors.py — Monitoring and tracking sections for orient.py display.

Split from orient_sections.py (DOMEX-META-S475, L-1174 T4 ceiling).
Contains: precompact checkpoint, cascade state, concurrent activity,
historian repair, meta-tooler, knowledge swarm, correction propagation,
knowledge recombination, epsilon dispatch.

Pattern: section_xxx(data) -> list[str]
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def section_precompact_checkpoint(session, root=ROOT):
    """PreCompact checkpoint notice (F-CC3, L-342)."""
    lines = []
    checkpoints = sorted((root / "workspace").glob("precompact-checkpoint-*.json"),
                         key=lambda p: p.stat().st_mtime)
    if not checkpoints:
        return lines
    try:
        cp = json.loads(checkpoints[-1].read_text())
        uncommitted = cp.get("uncommitted_files", [])
        still_uncommitted, stale_ratio = [], 1
        if uncommitted:
            status_out = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=str(root)).stdout
            status_files = {l.split()[-1] for l in status_out.strip().split("\n") if l.strip()}
            still_uncommitted = [f for f in uncommitted if f in status_files]
            stale_ratio = 1 - (len(still_uncommitted) / len(uncommitted))
        cp_session = next((int(re.search(r'\[S(\d+)\]', l).group(1)) for l in cp.get("recent_git_log", []) if re.search(r'\[S(\d+)\]', l)), 0)
        cur_num = int(session[1:]) if session[1:].isdigit() else 0
        if stale_ratio < 0.8 and (cur_num - cp_session if cp_session else 999) <= 2:
            absorbed = []
            if still_uncommitted and cp_session:
                try:
                    log_out = subprocess.run(["git", "log", "--name-only", "--format=", "--diff-filter=M", "HEAD~10..HEAD"], capture_output=True, text=True, cwd=str(root)).stdout
                    committed = {l.strip() for l in log_out.splitlines() if l.strip()}
                    absorbed = [f for f in still_uncommitted if f in committed]
                except Exception:
                    pass
            lines.append("--- !! COMPACTION RESUME DETECTED ---")
            lines.append(f"  Checkpoint: {checkpoints[-1].name} ({cp.get('trigger', '?')} at {cp.get('timestamp', '?')})")
            hint = cp.get("next_md", {}).get("For next session", "")
            if hint:
                lines.append(f"  In-flight: {hint[:120].splitlines()[0]}")
            if still_uncommitted:
                lines.append(f"  Uncommitted files ({len(still_uncommitted)}/{len(uncommitted)}): {', '.join(still_uncommitted[:5])}")
            if absorbed:
                lines.append(f"  \u26a0 Likely proxy-absorbed ({len(absorbed)}/{len(still_uncommitted)}): working tree diffs may be stale (L-526)")
            staged = cp.get("staged_files", [])
            if staged:
                lines.append(f"  \u26a0 STAGED FILES ({len(staged)}): {', '.join(staged[:5])}")
                lines.append(f"    Run: git reset HEAD -- <files> before staging new work (FM-19 stale-write risk)")
            lines.append("")
    except Exception:
        pass
    return lines


def section_cascade_state(maint_output: str = None):
    """Cross-layer cascade monitor (F-FLT4, L-1018, P-303). Only shown when layers failing."""
    lines = []
    try:
        from concurrent.futures import ThreadPoolExecutor
        sys.path.insert(0, str(Path(__file__).parent))
        from cascade_monitor import (
            check_tool_layer, check_quality_layer, check_knowledge_layer,
            check_evaluation_layer, check_attention_layer, detect_cascades,
        )
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


def section_concurrent_activity(root=ROOT):
    """Active sessions, task claims, and concurrency-level recommendation (L-686, L-526)."""
    lines = []
    try:
        sys.path.insert(0, str(root / "tools"))
        from claim import get_active_sessions, get_active_task_claims
        sessions = get_active_sessions()
        task_claims = get_active_task_claims()
        n = len(sessions)
        if not sessions and not task_claims:
            return lines
        level, icon = (("EXTREME", "\U0001f534") if n >= 5 else ("HIGH", "\U0001f7e0") if n >= 3 else ("MODERATE", "\U0001f7e1") if n >= 1 else ("LOW", "\U0001f7e2"))
        lines.append(f"--- Concurrent activity ({n} sessions, {icon} {level}) ---")
        for s in sessions[:5]:
            label = s.get("current_task", "(idle)") + (f": {s['description'][:40]}" if s.get("description") else "")
            lines.append(f"  {s['session']:15s} {s['age_s']:4d}s ago  {label}")
        if task_claims:
            lines.append(f"  Task claims: {', '.join(task_claims.keys())}")
        if n >= 5:
            lines.append(f"  \u26a0 EXTREME concurrency (N={n}): commit-by-proxy likely (L-526). Recommend: verification/historian mode. Re-check git log before EACH task.")
        elif n >= 3:
            lines.append(f"  \u26a0 HIGH concurrency (N={n}): planned tasks may be pre-empted (L-1133, L-526). Recommend: verification/historian/meta-reflection. Re-check git log --oneline -3 before each task.")
        lines.append("")
    except Exception:
        pass
    return lines


def section_historian_repair(root=ROOT):
    """Historian repair — SIG-39."""
    from orient_analysis import _run_tool_json
    lines = []
    hr_data = _run_tool_json("historian_repair", ["--json"], root=root)
    if hr_data:
        high_items = [i for i in hr_data.get("items", []) if i.get("severity") == "HIGH"]
        if high_items:
            cat_icons = {"beliefs": "\U0001f534", "frontiers": "\U0001f7e1", "domains": "\u26aa"}
            lines.append(f"--- Historian repair ({hr_data.get('total', 0)} stale, {len(high_items)} HIGH) ---")
            for item in high_items[:3]:
                lines.append(f"  {cat_icons.get(item.get('category',''),chr(0x25cb))} [{item['item_id']}] {item['category']} — stale {item['sessions_stale']}s — {item['description'][:60]}")
            if len(high_items) > 3:
                lines.append(f"  ... and {len(high_items) - 3} more HIGH items")
            lines.append("  Run: python3 tools/historian_repair.py")
            lines.append("")
    return lines


def section_meta_tooler(root=ROOT):
    """Meta-tooler scan — SIG-39."""
    from orient_analysis import _run_tool_json
    lines = []
    mt = _run_tool_json("meta_tooler", ["--json"], timeout=30, root=root)
    if mt and (mt.get("high", 0) > 0 or mt.get("medium", 0) > 5):
        lines.append(f"--- Meta-tooler ({mt['total_tools']} tools, HIGH={mt['high']} MEDIUM={mt['medium']}) ---")
        for f in mt.get("findings", []):
            if f["severity"] == "HIGH":
                lines.append(f"  \U0001f534 [{f['category']}] {f['tool']}: {f['message']}")
        lines.append("  Run: python3 tools/meta_tooler.py")
        lines.append("")
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
    """Knowledge recombination candidates (SIG-62, knowledge_recombine.py)."""
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
        if "| MERGED |" in line or "| ABANDONED |" in line:
            continue
        m = re.search(r"DOMEX-([A-Z]+)-S\d+", line)
        if m:
            active.add(m.group(1).lower())
    return active


def section_epsilon_dispatch(session_num, root=ROOT):
    """epsilon-dispatch diversity recommendation (F-RAND1, L-601 structural enforcement)."""
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


def section_grounding_audit(root=ROOT):
    """Grounding audit summary (F-GND1, L-1192): claim grounding health."""
    lines = []
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from grounding_audit import run_audit
        audit = run_audit(detail=False)
        if "error" in audit:
            return lines
        total = audit["total_claims"]
        avg = audit["avg_grounding_score"]
        well_pct = audit["well_grounded_pct"]
        poorly = audit["poorly_grounded"]
        stale = audit["stale"]
        lines.append("--- Grounding Audit (F-GND1) ---")
        lines.append(f"  {total} claims | avg score {avg:.3f} | {well_pct}% well-grounded")
        if poorly > 0:
            lines.append(f"  {poorly} poorly grounded (<0.2)")
        if stale > 0:
            lines.append(f"  {stale} stale (>50 sessions without retest)")
        bottom = audit.get("bottom_5", [])
        if bottom:
            worst = bottom[0]
            lines.append(f"  Worst: {worst.get('id', '?')} (score {worst.get('score', 0):.3f})")
        lines.append("")
    except Exception:
        pass
    return lines


def section_cell_blueprint(current_session_str="S0"):
    """Cell blueprint summary — pre-computed daughter cell state (L-1184, L-601).

    Shows parent session's pre-computed dispatch, absorption targets, and
    next actions so the daughter session can skip re-derivation.
    """
    lines = []
    bp_path = ROOT / "workspace" / "cell-blueprint-latest.json"
    if not bp_path.exists():
        return lines
    try:
        bp = json.loads(bp_path.read_text())
    except (json.JSONDecodeError, OSError):
        return lines

    parent = bp.get("session", "?")
    # Skip if blueprint is from same or later session (stale / self-referential)
    parent_num = int(re.search(r"(\d+)", str(parent)).group(1)) if re.search(r"(\d+)", str(parent)) else 0
    cur_num = int(re.search(r"(\d+)", str(current_session_str)).group(1)) if re.search(r"(\d+)", str(current_session_str)) else 0
    if parent_num >= cur_num and cur_num > 0:
        return lines  # blueprint is current or future — no inheritance value

    lines.append(f"\n--- Cell Blueprint (from {parent}) ---")

    # Absorption targets — the primary boot bottleneck (76% of sessions)
    artifacts = bp.get("untracked_artifacts", [])
    if artifacts:
        lines.append(f"  Absorb ({len(artifacts)} artifacts from parent):")
        for a in artifacts[:5]:
            lines.append(f"    ?? {a}")

    # Pre-computed dispatch — saves 30s dispatch_optimizer.py run
    top3 = bp.get("dispatch_top3", [])
    if top3:
        parts = []
        for t in top3:
            collision = " !" if t.get("collision") else ""
            parts.append(f"{t['domain']}({t['score']}){collision}")
        lines.append(f"  Dispatch hint: {', '.join(parts)}")

    # Parent's next actions — context for what was planned
    actions = bp.get("next_actions", [])
    if actions:
        lines.append(f"  Parent planned ({len(actions)} items):")
        for a in actions[:3]:
            lines.append(f"    {a}")

    # Periodics due from parent's perspective
    due = bp.get("periodics_due", [])
    if due:
        ids = [d["id"] for d in due[:3]]
        lines.append(f"  Periodics due: {', '.join(ids)}")

    lines.append("")
    return lines


def section_self_inflation(root=ROOT):
    """Self-inflation index (FM-21 defense layer)."""
    lines = []
    try:
        result = subprocess.run(
            [sys.executable, str(root / "tools" / "self_inflation_index.py"), "--orient"],
            capture_output=True, text=True, timeout=10, cwd=str(root)
        )
        if result.returncode == 0 and result.stdout.strip():
            lines.append("--- Self-Inflation Index (FM-21) ---")
            for line in result.stdout.strip().splitlines():
                lines.append(line)
            lines.append("")
    except Exception:
        pass
    return lines


def section_trace_amplification(root=ROOT):
    """Stigmergic amplification — surface high-in-degree lessons not cited recently.

    Closes the amplification loop (F-STIG1, L-1296): success should amplify
    source traces. Shows top-cited lessons absent from recent Cites: headers.
    """
    lines = []
    try:
        from citation_mechanism import _get_in_degrees

        in_deg = _get_in_degrees()
        if not in_deg:
            return lines

        # Find lessons cited in last 50 lessons (recent activity)
        lesson_dir = root / "memory" / "lessons"
        recent_files = sorted(lesson_dir.glob("L-*.md"),
                              key=lambda p: p.stat().st_mtime, reverse=True)[:50]
        recently_cited = set()
        for lf in recent_files:
            for line in lf.read_text(errors="replace").splitlines()[:5]:
                if line.startswith("Cites:"):
                    for m in re.findall(r'L-\d+', line):
                        recently_cited.add(m)
                    break

        # Top-cited lessons NOT in recent citations = amplification gap
        top = sorted(in_deg.items(), key=lambda x: -x[1])[:30]
        gap = [(lid, deg) for lid, deg in top if lid not in recently_cited][:8]
        if gap:
            lines.append(f"--- Trace Amplification (F-STIG1, {len(gap)} high-impact underused) ---")
            for lid, deg in gap:
                lines.append(f"  {lid} (in-deg={deg}) — high-cited but not in recent 50 Cites: headers")
            lines.append(f"  Amplify: cite these when relevant — success should strengthen source trails")
            lines.append("")
    except Exception:
        pass
    return lines


def section_reactivation(session_num, root=ROOT):
    """Dormant-idea reactivation — surface high-value decayed lessons for revival."""
    lines = []
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(root / "tools" / "reactivation.py"), "--brief"],
            capture_output=True, text=True, timeout=30, cwd=str(root),
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                lines.append(line)
            lines.append("")
    except Exception:
        pass
    return lines


def section_complexity_phase(root=ROOT):
    """Complexity theory measurement — phase, small-world, percolation (L-1430)."""
    lines = []
    try:
        result = subprocess.run(
            ["python3", str(root / "tools" / "complexity_measure.py"), "--json"],
            capture_output=True, text=True, timeout=60, cwd=str(root),
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            crit = data.get("criticality", {})
            sw = data.get("small_world", {})
            perc = data.get("percolation", {})
            deg = data.get("degree_distribution", {})
            cc = data.get("clustering_coefficient", 0)
            pl = data.get("avg_path_length", 0)

            phase = crit.get("phase", "?")
            k_avg = crit.get("k_avg", 0)
            sigma = sw.get("sigma", 0)
            vuln = perc.get("vulnerability_ratio", 0)
            iso = deg.get("isolated_nodes", 0)
            n = max(deg.get("n_nodes", 1), 1)

            lines.append("--- Complexity Phase (L-1430) ---")
            lines.append(
                f"  Phase: {phase} | k_avg={k_avg:.2f} | "
                f"small-world \u03c3={sigma:.1f} | C={cc:.3f} | L={pl:.1f}"
            )
            lines.append(
                f"  Percolation: random={perc.get('random_threshold', 0):.0%} "
                f"targeted={perc.get('targeted_threshold', 0):.0%} "
                f"vulnerability={vuln:.1f}x | "
                f"isolated={iso} ({iso/n:.0%})"
            )
            recs = data.get("recommendations", [])
            high = [r for r in recs if r.get("priority") == "HIGH"]
            for r in high[:1]:
                lines.append(f"  \u26a0 {r['area']}: {r['recommendation'][:100]}")
            lines.append("  Run: python3 tools/complexity_measure.py")
            lines.append("")
    except Exception:
        pass
    return lines
