#!/usr/bin/env python3
"""
orient_analysis.py — Heavy analysis sections for orient.py display.

Split from orient_sections.py (DOMEX-META-S475, L-1174 T4 ceiling).
Contains: PCI scoring, prescription gap, level balance, succession phase,
stalled campaigns, zombie tracking, closure metric.

Pattern: section_xxx(data) -> list[str]
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _cached_artifact(root, subdir, pattern, session_num, max_age=20, min_age=-5):
    """Load latest cached JSON artifact. Returns (data, age_str) or None."""
    try:
        files = sorted((root / "experiments" / subdir).glob(pattern))
        if not files:
            return None
        data = json.loads(files[-1].read_text())
        m = re.search(r"-s(\d+)", files[-1].name)
        if not m:
            return None
        age = session_num - int(m.group(1))
        if min_age <= age <= max_age:
            return data, f"S{m.group(1)}" + (f", {age}s ago" if age > 0 else "")
    except Exception:
        pass
    return None


def _run_tool_json(tool_name, args=None, timeout=15, root=ROOT):
    """Run a tool and parse JSON output. Returns dict or None."""
    cmd = [sys.executable, str(root / "tools" / f"{tool_name}.py")] + (args or [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
    except Exception:
        return None


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
        # Cached artifact displays
        ks = _cached_artifact(root, "meta", "knowledge-state-s*.json", session_num, max_age=20, min_age=0)
        if ks:
            dist = ks[0].get("global_states", {}); total = sum(dist.values()) or 1
            lines.append(f"  Knowledge attention ({ks[1]}): BLIND-SPOT {dist.get('BLIND-SPOT',0)/total:.1%} | DECAYED {dist.get('DECAYED',0)/total:.1%} (L-813: citation-recency, not validity — actual false knowledge ~5-10%) | refresh: python3 tools/knowledge_state.py --json")
        sq = _cached_artifact(root, "meta", "science-quality-s*.json", session_num, max_age=30)
        if sq:
            lines.append(f"  Science quality ({sq[1]}): mean {sq[0].get('mean_quality',0):.0%} | pre-reg {sq[0].get('criteria_means',{}).get('pre_registration',0):.0%} | falsif lanes {sq[0].get('falsification_lanes','?/0')} | refresh: python3 tools/science_quality.py --json")
        bm = _cached_artifact(root, "meta", "bayes-meta-s*.json", session_num, max_age=30)
        if bm:
            ece = bm[0].get("results", {}).get("ece", "?")
            ece_flag = " \u26a0 OVERCONFIDENT" if isinstance(ece, float) and ece > 0.15 else ""
            lines.append(f"  Bayesian calibration ({bm[1]}): ECE={ece:.3f}{ece_flag} | {bm[0].get('n_frontiers_with_posteriors','?')} frontiers | refresh: python3 tools/bayes_meta.py --json > experiments/meta/bayes-meta-s<N>.json")
        es = _cached_artifact(root, "evaluation", "eval-sufficiency-s*.json", session_num, max_age=50)
        if es:
            cont = es[0].get("continuous_composite", es[0].get("composite_normalized"))
            cont_str = f" ({cont:.0%} continuous)" if cont is not None else ""
            lines.append(f"  Mission sufficiency ({es[1]}): {es[0].get('overall','?')}{cont_str} — next: {es[0].get('next_improvement_target','?')} | refresh: python3 tools/eval_sufficiency.py --save")
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
    """Attention carrying capacity / r-K phase indicator (L-1121)."""
    lines = []
    try:
        import glob as _gl
        n_lessons = len(_gl.glob(str(root / "memory" / "lessons" / "L-*.md")))
        if n_lessons < 100:
            return lines
        attn = 1.0 / n_lessons
        threshold = 1.0 / 500  # integration-bound crossover at N~550 (L-912)
        if attn >= threshold:
            return lines
        def _count_lessons(diff_filter):
            try:
                r = subprocess.run(["git", "log", "--oneline", f"--diff-filter={diff_filter}", "--name-only", "-10", "--", "memory/lessons/L-*.md"], capture_output=True, text=True, cwd=str(root), timeout=5)
                return len([l for l in r.stdout.splitlines() if l.startswith("memory/lessons/L-") and l.endswith(".md")])
            except Exception:
                return 0
        new_l, mod_l = _count_lessons("A"), _count_lessons("M")
        lines.append("--- Succession Phase (L-1121) ---")
        lines.append(f"  Attention carrying capacity: {n_lessons/500:.1f}x past threshold (N={n_lessons}, K_threshold=500)")
        lines.append(f"  Attention per lesson: {attn:.5f} (threshold: {threshold:.4f})")
        if new_l > 0 or mod_l > 0:
            r_k = new_l / max(mod_l, 1)
            mode = "r-mode (producing)" if r_k > 2 else "K-mode (integrating)" if r_k < 0.5 else "balanced"
            lines.append(f"  Recent r/K: {new_l} new / {mod_l} modified = {r_k:.1f} ({mode})")
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
    data = _run_tool_json("dispatch_optimizer", ["--json", "--all"], root=root)
    if data:
        for d in data:
            for fid in (d.get("wave_2_stalls") or []):
                stall_map[fid] = d["domain"]
    if stall_map:
        lines.append(f"--- Stalled Campaigns ({len(stall_map)} frontiers in 2-wave valley — 11% resolve) ---")
        for fid, dom in sorted(stall_map.items())[:8]:
            lines.append(f"  \u26a0 {fid} ({dom}) — needs hardening lane (mode shift required)")
        lines.append("  Fix: open DOMEX-<DOM>-S<N> with --mode hardening for any of the above")
        lines.append("")
    return lines, stall_map


def _item_resolved_by_actual(canon: str, actual_texts: list[str]) -> bool:
    """Check if a canonical next-item was addressed in any actual: field."""
    stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "is",
                  "and", "or", "with", "from", "by", "as", "its", "it", "be",
                  "was", "were", "has", "had", "not", "no", "but", "if", "so",
                  "that", "this", "than", "more", "very", "just", "also", "all",
                  "each", "per", "any", "s", "yet", "re", "vs"}
    raw_tokens = re.findall(r'[A-Za-z0-9_-]{3,}', canon)
    tokens: set[str] = set()
    for t in raw_tokens:
        parts = t.split('-')
        if len(parts) > 1 and all(p.isalpha() and len(p) >= 2 for p in parts):
            tokens.update(p.lower() for p in parts if len(p) >= 3)
        else:
            tokens.add(t.lower())
    tokens -= stop_words
    if len(tokens) < 2:
        return False
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
        from collections import Counter
        next_path = root / "tasks" / "NEXT.md"
        if not next_path.exists():
            return lines
        notes = parse_session_notes(next_path.read_text(encoding="utf-8"))
        if len(notes) < 2:
            return lines
        actual_texts = [n.get("actual_text", "") for n in notes if n.get("actual_text")]
        item_counter = Counter()
        for note in notes:
            seen: set[str] = set()
            for item in note["next_items"]:
                c = canonicalize(item)
                if c not in seen:
                    item_counter[c] += 1; seen.add(c)
        # Exclusion: dropped zombies + resolved by actual: fields
        dropped: set[str] = set()
        try:
            dp = root / "tools" / "zombie_drops.json"
            if dp.exists():
                dropped = {e.get("canonical", "") for e in json.loads(dp.read_text()).get("drops", []) if e.get("canonical")}
        except Exception:
            pass
        resolved = {c for c in item_counter if _item_resolved_by_actual(c, actual_texts)}
        excluded = dropped | resolved
        zombies = [(it, cnt) for it, cnt in item_counter.most_common() if cnt >= 5 and it not in excluded]
        # Carried-over% for latest session (TG-4)
        prior_items = {canonicalize(it) for n in notes[-6:-1] for it in n["next_items"]}
        latest_items = [canonicalize(it) for it in notes[-1]["next_items"] if canonicalize(it) not in excluded]
        carried = sum(1 for it in latest_items if it in prior_items) if latest_items else 0
        pct = (carried / len(latest_items) * 100) if latest_items else 0.0
        if zombies or pct >= 30:
            lines.append("--- Zombie Items (L-978 TG-2/TG-4) ---")
            warn = " — target <30%" if pct >= 30 else ""
            lines.append(f"  {'\u26a0 ' if pct >= 30 else ''}Carried-over: {pct:.0f}% ({carried}/{len(latest_items)}){warn}")
            if zombies:
                lines.append(f"  Zombies ({len(zombies)} items recurring 5+ sessions):")
                for item, count in zombies[:5]:
                    lines.append(f"    \U0001f480 {count:3d}x  {item[:60]}")
            if resolved:
                lines.append(f"  Resolved by actual: {len(resolved)} item(s) excluded")
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
                cites_match = re.search(r"^\*{0,2}Cites\*{0,2}:\s*(.+)", txt, re.MULTILINE)
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
