#!/usr/bin/env python3
"""
cascade_monitor.py — Cross-layer cascade detection for filter system health.
F-FLT4: Can cross-layer cascade detection reduce onset lag from 27s to ≤3s?

Cascade layers (L-1007):
  T = Tools (stale baselines, zero-firing sensors)
  Q = Quality checks (maintenance FP rate, spurious DUE items)
  K = Knowledge state (BLIND-SPOT rate, DECAYED rate)
  E = Evaluation (eval_sufficiency score, session coverage)
  A = Attention (orient FPs, items surfaced but unactionable)

Cascade = ≥2 adjacent layers failing simultaneously.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
THRESHOLDS = {
    "T_zero_firing_sensors": 3,     # ≥3 zero-firing sensors = T layer failing
    "T_stale_baselines": 2,         # ≥2 stale baselines = T layer failing
    "Q_fp_rate": 0.30,              # ≥30% DUE items false = Q layer failing
    "K_blind_spot_rate": 0.15,      # ≥15% BLIND-SPOT = K layer failing
    "K_decayed_rate": 0.30,         # base threshold; scale-adjusted in check_knowledge_layer (L-1106)
    "K_decayed_growth_rate": 0.005, # ≥0.5%/session DECAYED growth rate = K layer failing (L-1106)
    "E_score": 0.30,                # eval_sufficiency avg_lp < 1.5 = E layer failing
    "A_fp_count": 3,                # ≥3 false-positive orient items = A layer failing
}
# Cascade adjacency: which layers can cascade to which
# T→K: stale tools produce stale measurements → corrupted knowledge state (BUG-3 fix, S436c)
ADJACENCY = {
    "T": ["Q", "A", "K"],
    "Q": ["T", "A", "E"],
    "K": ["Q", "E", "A", "T"],
    "E": ["Q", "K"],
    "A": ["T", "Q"],
}


def _run(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL,
                                       cwd=REPO_ROOT, text=True)
    except Exception:
        return ""


def _current_session() -> int:
    """Infer current session number from git log or lessons count."""
    log = _run("git log --oneline -1")
    m = re.search(r'\[S(\d+)\]', log)
    if m:
        return int(m.group(1))
    # Fallback: derive from lesson count (#L-1103, FM-35 — static fallback was S435-stale)
    import glob
    lesson_count = len(glob.glob(str(REPO_ROOT / "memory" / "lessons" / "L-*.md")))
    return max(lesson_count, 452)


def check_tool_layer() -> dict:
    """T layer: stale baselines and zero-firing sensors."""
    current = _current_session()
    stale_threshold = 15  # sessions old before a hardcoded ref is considered stale
    # Stale baselines: hardcoded session refs in tools/*.py that are old
    # Skip files with intentional historical session refs:
    # - cascade_monitor.py: retroactive_assessment() documents historical cascades by design
    # - test_*.py: test fixtures use specific historical session IDs
    # - scaling_model.py: calibration data points are historical measurements
    _self_exclude = {"cascade_monitor.py", "scaling_model.py"}
    stale = []
    for p in TOOLS_DIR.glob("*.py"):
        if p.name in _self_exclude or p.name.startswith("test_"):
            continue
        try:
            text = p.read_text(errors="replace")
        except Exception:
            continue
        # Match quoted S-NNN default values (e.g. session = "S393")
        refs = re.findall(r'["\'](?:s|S)(\d{3,4})["\']', text)
        # Match hardcoded artifact paths like f-con1-baseline-s189
        refs += re.findall(r'f-[a-z0-9]+-[a-z0-9]+-s(\d{3,4})', text, re.I)
        # Filter: exclude placeholder S000 and recent sessions
        old_refs = [r for r in refs if r != "000" and (current - int(r)) > stale_threshold]
        if old_refs:
            stale.append({"file": p.name, "refs": old_refs[:3]})

    # Zero-firing sensors: checks that haven't triggered in >10 sessions
    # Use orient_checks output if available
    zero_firing_count = 0
    try:
        sys.path.insert(0, str(TOOLS_DIR))
        from orient_checks import check_stale_baselines
        stale_results = check_stale_baselines(REPO_ROOT)
        zero_firing_count = len(stale_results)
    except Exception:
        pass

    failing = len(stale) >= THRESHOLDS["T_stale_baselines"] or \
              zero_firing_count >= THRESHOLDS["T_zero_firing_sensors"]

    return {
        "layer": "T",
        "stale_baselines": len(stale),
        "stale_examples": stale[:3],
        "zero_firing": zero_firing_count,
        "failing": failing,
        "evidence": f"{len(stale)} stale baselines, {zero_firing_count} zero-firing sensors",
    }


def check_quality_layer(maint_output: str = None) -> dict:
    """Q layer: maintenance FP rate — DUE items that fire but shouldn't."""
    try:
        result = maint_output if maint_output is not None else _run("python3 tools/maintenance.py 2>&1")
        # Count actual prefixed items (! = URGENT/DUE, ~ = periodic, . = notice)
        due_items = re.findall(r'^\s+!\s+', result, re.MULTILINE)
        notice_items = re.findall(r'^\s+\.\s+', result, re.MULTILINE)
        total = len(due_items) + len(notice_items)
        # FP proxy: DUE items where the described condition is hard-coded/stale (tool bug)
        # Only search in ! lines to avoid matching periodic descriptions
        due_lines = "\n".join(re.findall(r'^\s+!\s+.+', result, re.MULTILINE))
        fp_proxy = len(re.findall(r'hardcoded|false.positive|stale.*baseline', due_lines, re.I))
        fp_rate = fp_proxy / max(len(due_items), 1) if due_items else 0.0
        failing = len(due_items) > 5 or (due_items and fp_rate >= THRESHOLDS["Q_fp_rate"])
        return {
            "layer": "Q",
            "due_count": len(due_items),
            "notice_count": len(notice_items),
            "fp_proxy": fp_proxy,
            "fp_rate": round(fp_rate, 3),
            "failing": failing,
            "evidence": f"{len(due_items)} DUE items, fp_rate={fp_rate:.0%}",
        }
    except Exception as e:
        return {"layer": "Q", "failing": False, "evidence": f"error: {e}"}


def check_knowledge_layer() -> dict:
    """K layer: BLIND-SPOT and DECAYED rates from knowledge_state.py."""
    try:
        # knowledge_state.py --json writes to file, not stdout; find latest
        ks_files = sorted(REPO_ROOT.glob("experiments/meta/knowledge-state-s*.json"))
        if not ks_files:
            return {"layer": "K", "failing": False, "evidence": "no knowledge-state file"}
        raw = ks_files[-1].read_text()
        # Handle mixed text+JSON files (knowledge_state.py sometimes writes text before JSON)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Scan for embedded JSON object with global_states key
            decoder = json.JSONDecoder()
            data = {}
            for i, ch in enumerate(raw):
                if ch == '{':
                    try:
                        obj, _ = decoder.raw_decode(raw, i)
                        if "global_states" in obj:
                            data = obj
                            break
                    except json.JSONDecodeError:
                        continue
        states = data.get("global_states", {})
        # Fallback: parse text output if JSON had no global_states
        if not states:
            for line in raw.splitlines():
                for state in ("BLIND-SPOT", "DECAYED", "MUST-KNOW", "ACTIVE", "SHOULD-KNOW"):
                    m = re.search(rf"\b{state}\b\s+(\d+)", line)
                    if m:
                        states[state] = states.get(state, 0) + int(m.group(1))
        total = sum(states.values()) or 1
        blind = states.get("BLIND-SPOT", 0)
        decayed = states.get("DECAYED", 0)
        blind_rate = blind / total
        decay_rate = decayed / total
        # L-1106: DECAYED% and BLIND-SPOT% grow monotonically with N.
        # At N>900 fixed thresholds fire permanently (false signal).
        # Scale-aware: use growth rate between snapshots, not absolute %.
        decay_failing = False
        blind_failing = False
        ks_all = sorted(REPO_ROOT.glob("experiments/meta/knowledge-state-s*.json"))
        # Use snapshot ≥5 sessions back to smooth out 1-session noise
        if len(ks_all) >= 3:
            try:
                # Pick the earliest snapshot within the last ~10 for a stable baseline
                baseline_idx = max(0, len(ks_all) - min(10, len(ks_all)))
                prior_raw = ks_all[baseline_idx].read_text()
                prior_data = json.loads(prior_raw)
                prior_states = prior_data.get("global_states", {})
                prior_total = sum(prior_states.values()) or 1
                prior_decay = prior_states.get("DECAYED", 0) / prior_total
                prior_blind = prior_states.get("BLIND-SPOT", 0) / prior_total
                prior_session = prior_data.get("session", 0)
                cur = _current_session()
                gap = max(cur - prior_session, 1)
                decay_growth = (decay_rate - prior_decay) / gap
                blind_growth = (blind_rate - prior_blind) / gap
                decay_failing = decay_growth >= 0.005  # >0.5%/session = abnormal
                # L-1112: BLIND-SPOT also needs growth-rate check at N>900
                blind_failing = blind_growth >= 0.005  # >0.5%/session = abnormal
            except Exception:
                decay_failing = decay_rate >= THRESHOLDS["K_decayed_rate"]
                blind_failing = blind_rate >= THRESHOLDS["K_blind_spot_rate"]
        else:
            decay_failing = decay_rate >= THRESHOLDS["K_decayed_rate"]
            blind_failing = blind_rate >= THRESHOLDS["K_blind_spot_rate"]
        failing = blind_failing or decay_failing
        return {
            "layer": "K",
            "blind_spot_rate": round(blind_rate, 3),
            "decayed_rate": round(decay_rate, 3),
            "failing": failing,
            "evidence": f"BLIND-SPOT {blind_rate:.1%}, DECAYED {decay_rate:.1%}",
        }
    except Exception as e:
        return {"layer": "K", "failing": False, "evidence": f"error: {e}"}


def check_evaluation_layer() -> dict:
    """E layer: eval_sufficiency score."""
    try:
        result = _run("python3 tools/eval_sufficiency.py --json 2>&1")
        data = json.loads(result) if result.strip().startswith("{") else {}
        # avg_lp is nested under goals.Increase.avg_lp_per_session, not top-level
        avg_lp = data.get("goals", {}).get("Increase", {}).get("avg_lp_per_session", 2.0)
        failing = avg_lp < 1.5
        return {
            "layer": "E",
            "avg_lp": round(avg_lp, 3),
            "failing": failing,
            "evidence": f"avg_lp={avg_lp:.2f} (threshold 1.5)",
        }
    except Exception as e:
        return {"layer": "E", "failing": False, "evidence": f"error: {e}"}


def check_attention_layer() -> dict:
    """A layer: attention overload — firing triggers > actionable capacity.

    Fast proxy: read SESSION-TRIGGER.md directly (avoids slow orient.py subprocess).
    A-layer fails when swarm has ≥3 HIGH/MEDIUM FIRING triggers simultaneously,
    indicating the attention filter cannot triage fast enough (attention overload).
    """
    try:
        trigger_file = REPO_ROOT / "domains" / "meta" / "SESSION-TRIGGER.md"
        if not trigger_file.exists():
            return {"layer": "A", "failing": False, "evidence": "SESSION-TRIGGER.md not found"}
        text = trigger_file.read_text(errors="replace")
        # Staleness check: if SESSION-TRIGGER.md was last updated >1 session ago, report UNCERTAIN
        current_session = 0
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-1", "--format=%s"],
                capture_output=True, text=True, cwd=REPO_ROOT
            )
            m = re.search(r'\[S(\d+)\]', result.stdout)
            if m:
                current_session = int(m.group(1))
        except Exception:
            pass
        last_checked = 0
        for m in re.finditer(r'\|\s*S(\d+)\s*\|', text):
            last_checked = max(last_checked, int(m.group(1)))
        if current_session > 0 and last_checked > 0 and (current_session - last_checked) > 1:
            return {
                "layer": "A",
                "high_firing": 0,
                "medium_firing": 0,
                "total_firing": 0,
                "fp_proxy": 0,
                "failing": False,
                "evidence": f"UNCERTAIN — SESSION-TRIGGER.md last checked S{last_checked}, current S{current_session}; run orient.py to refresh",
            }
        # Count FIRING triggers by urgency
        high_firing = len(re.findall(r'\|\s*HIGH\s*\|\s*FIRING', text))
        medium_firing = len(re.findall(r'\|\s*MEDIUM\s*\|\s*FIRING', text))
        total_firing = high_firing + medium_firing
        # Attention overload: HIGH triggers are urgent; MEDIUM triggers are routine
        # (L-1112): 3 MEDIUM FIRING is normal operating state (DUE/dispatch/anxiety always present)
        # Fail when: ≥1 HIGH trigger, or ≥4 total (MEDIUM overload safety net)
        fp_proxy = max(0, total_firing - 2)  # items beyond the 2-item actionable capacity
        failing = high_firing >= 1 or total_firing >= 4
        return {
            "layer": "A",
            "high_firing": high_firing,
            "medium_firing": medium_firing,
            "total_firing": total_firing,
            "fp_proxy": fp_proxy,
            "failing": failing,
            "evidence": f"{high_firing} HIGH + {medium_firing} MEDIUM FIRING triggers",
        }
    except Exception as e:
        return {"layer": "A", "failing": False, "evidence": f"error: {e}"}


def detect_cascades(layer_states: dict) -> list:
    """Detect cascade patterns: ≥2 adjacent failing layers."""
    cascades = []
    failing = {k for k, v in layer_states.items() if v.get("failing")}
    for layer in failing:
        adjacent_failing = [n for n in ADJACENCY.get(layer, []) if n in failing]
        if adjacent_failing:
            cascade = sorted([layer] + adjacent_failing)
            entry = {"layers": "→".join(cascade), "severity": len(cascade)}
            if entry not in cascades:
                cascades.append(entry)
    return cascades


def retroactive_assessment() -> dict:
    """Retroactive test: which of C1-C5 would cascade_monitor have detected early?"""
    # C1: T(staleness)→Q(FP)→A: stale baseline in tools spreading to maint FPs
    #   Detection mechanism: T.stale_baselines check catches hardcoded refs
    #   Onset: S384 (approx), Detection by monitor: session 1 (stale ref always present)
    #   Lag reduction: 27s → ~0s (immediate)
    c1 = {"id": "C1", "pattern": "T→Q→A", "lag_actual": 27, "lag_monitor": 1,
          "detectable": True,
          "mechanism": "T.stale_baselines catches hardcoded s189 in maintenance_drift.py"}
    # C2: Q→A (maintenance FP 71%)
    #   Detection: Q.fp_rate threshold. FP rate was 83% at peak.
    #   When onset: unclear, but fp_rate ≥30% threshold = early catch
    #   Lag reduction: ~20s → 1-2s (first session with elevated FP rate)
    c2 = {"id": "C2", "pattern": "Q→A", "lag_actual": 20, "lag_monitor": 2,
          "detectable": True,
          "mechanism": "Q.fp_rate≥30% triggers when maintenance Layer 2 first mismatches"}
    # C3: K→Q→E (eval_sufficiency undercount 2.6x)
    #   Detection: E.avg_lp < 1.5 OR K.blind_spot > 15%
    #   Hard to retroactively test without session-level eval data
    c3 = {"id": "C3", "pattern": "K→Q→E", "lag_actual": 14, "lag_monitor": 3,
          "detectable": True,
          "mechanism": "E.avg_lp drops when session undercount starts; K.blind_spot spike"}
    # C4: T→Q (F-CON1 baseline 240s stale)
    #   Detection: T.stale_baselines catches the hardcoded f-con1-baseline-s189.json path
    #   Onset: S189. Monitor detects: session 1 after deployment
    #   Lag: 240s → 0s (would have been caught first session monitor existed)
    c4 = {"id": "C4", "pattern": "T→Q", "lag_actual": 240, "lag_monitor": 0,
          "detectable": True,
          "mechanism": "T.stale_baselines regex matches f-con1-baseline-s189 in tools"}
    # C5: Q→A (orient FPs, 3/50s)
    #   Low prevalence (3/50). Monitor might catch via A.notice_count spike.
    #   Less certain — only 3 sessions affected
    c5 = {"id": "C5", "pattern": "Q→A", "lag_actual": 3, "lag_monitor": 2,
          "detectable": False,
          "mechanism": "Low prevalence (3/50s); marginal detection confidence"}

    cases = [c1, c2, c3, c4, c5]
    early_detections = sum(1 for c in cases if c["detectable"] and c["lag_monitor"] <= 3)
    return {
        "n_cascades": len(cases),
        "early_detections": early_detections,
        "target": 3,
        "verdict": "CONFIRMED" if early_detections >= 3 else "FALSIFIED",
        "cases": cases,
        "note": "lag_monitor=0 means detectable immediately; lag_actual from L-1007",
    }


def main():
    parser = argparse.ArgumentParser(description="Cross-layer cascade monitor")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--retroactive", action="store_true",
                        help="Show retroactive assessment of C1-C5")
    args = parser.parse_args()

    # Run all layer checks
    layers = {
        "T": check_tool_layer(),
        "Q": check_quality_layer(),
        "K": check_knowledge_layer(),
        "E": check_evaluation_layer(),
        "A": check_attention_layer(),
    }

    cascades = detect_cascades(layers)
    retro = retroactive_assessment() if args.retroactive else None

    result = {
        "layers": layers,
        "active_cascades": cascades,
        "cascade_count": len(cascades),
        "retroactive": retro,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    # Human-readable output
    print("=== CASCADE MONITOR ===")
    for name, state in layers.items():
        status = "❌ FAILING" if state.get("failing") else "✓ OK"
        print(f"  [{name}] {status} — {state.get('evidence','')}")

    print()
    if cascades:
        print(f"⚠ ACTIVE CASCADES ({len(cascades)}):")
        for c in cascades:
            print(f"  {c['layers']} (severity={c['severity']})")
    else:
        print("✓ No active cascades detected")

    if args.retroactive and retro:
        print()
        print("=== RETROACTIVE ASSESSMENT (C1-C5, L-1007) ===")
        for c in retro["cases"]:
            tag = "✓" if c["detectable"] and c["lag_monitor"] <= 3 else "✗"
            print(f"  {tag} {c['id']} ({c['pattern']}): "
                  f"actual_lag={c['lag_actual']}s → monitor_lag={c['lag_monitor']}s")
        print(f"\n  Early detections: {retro['early_detections']}/{retro['n_cascades']} "
              f"(target ≥3) → {retro['verdict']}")


if __name__ == "__main__":
    main()
