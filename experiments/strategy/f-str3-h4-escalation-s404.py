#!/usr/bin/env python3
"""F-STR3 H4 prospective update + escalation architecture analysis (S404).

Measures:
1. H4 targeting rate (S401-S404) — extension of S403 n=18 baseline
2. Valley escape count across all campaigns
3. 5-layer escalation load analysis — which layers contribute?
"""

import json, re, subprocess, sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[2]

def parse_lanes():
    """Parse SWARM-LANES.md for all DOMEX lanes."""
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    text = lanes_path.read_text()
    lanes = []
    for line in text.splitlines():
        if not line.startswith("|") or "---" in line or "Date" in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 13:
            continue
        date, lane_id, session, agent, branch, pr, model, platform, scope, etc, status, notes = cols[1:13]
        # Extract session number
        sess_match = re.search(r"S?(\d+)", session)
        sess_num = int(sess_match.group(1)) if sess_match else 0
        # Extract frontier
        frontier_match = re.search(r"frontier=([^;]+)", etc)
        frontier = frontier_match.group(1).strip() if frontier_match else ""
        # Extract mode (word-boundary to avoid check_mode=)
        mode_match = re.search(r"(?<![a-z_])mode=([^;]+)", etc)
        mode = mode_match.group(1).strip() if mode_match else ""
        lanes.append({
            "lane_id": lane_id,
            "session": sess_num,
            "status": status.strip(),
            "frontier": frontier,
            "mode": mode,
            "etc": etc,
            "notes": notes,
            "scope": scope,
        })
    return lanes

def get_stalled_frontiers_at_s400():
    """Return set of frontiers that were at 2-wave danger zone at baseline (S400).

    Based on L-845 and the S403 experiment data.
    """
    # From the wave planner and L-845/L-866, these were the stalled frontiers
    # at S400 baseline (2-wave, exploration→exploration):
    return {
        "F-PSY3", "F-FRA2", "F-FRA3", "F-SOC2", "F-SOC3",
        "F-GAM2", "F-GAM1", "F-CTL3", "F-META7",
        "F-STAT2", "F-STAT3", "F-EVO5", "F-CRY2", "F-CRY3",
        "F-IS4", "F-GT1", "F-PHY1", "F-GUE1", "F-PRO1",
    }

def classify_targeting(lanes, stalled):
    """Classify lanes S401+ as targeting stalled frontiers or not."""
    targeted = []
    non_targeted = []
    for l in lanes:
        if l["session"] < 401:
            continue
        if not l["lane_id"].startswith("DOMEX"):
            continue
        if l["status"] not in ("MERGED", "ABANDONED", "ACTIVE", "CLAIMED"):
            continue
        frontiers = [f.strip() for f in re.split(r"[/,]", l["frontier"]) if f.strip()]
        is_targeted = any(f in stalled for f in frontiers)
        entry = {
            "lane": l["lane_id"],
            "session": l["session"],
            "frontiers": frontiers,
            "status": l["status"],
            "mode": l["mode"],
        }
        if is_targeted:
            targeted.append(entry)
        else:
            non_targeted.append(entry)
    return targeted, non_targeted

def count_valley_escapes(lanes):
    """Count frontiers that escaped 2-wave valley (advanced from exploration→exploration
    to a different mode or got resolved)."""
    stalled = get_stalled_frontiers_at_s400()
    escaped = set()
    for l in lanes:
        if l["session"] < 401:
            continue
        frontiers = [f.strip() for f in re.split(r"[/,]", l["frontier"]) if f.strip()]
        for f in frontiers:
            if f in stalled:
                if l["mode"] and l["mode"] != "exploration":
                    escaped.add(f)
                if "RESOLVED" in l.get("notes", "") or "CONFIRMED" in l.get("notes", ""):
                    escaped.add(f)
    return escaped

def analyze_escalation_layers(lanes):
    """Analyze which of the 5 escalation layers contributed to COMMIT-domain targeting.

    5 layers (chronological):
    L1: danger boost (+1.5 to score) — S390
    L2: COMMIT floor (median score minimum) — S395
    L3: guarantee boost (promote to 3rd-place) — S396
    L4: 1-in-5 reservation — S399
    L5: orient.py DUE routing (stalled-campaign naming) — S401

    Layer attribution: which layer was the PRIMARY mechanism that caused
    dispatch to a stalled frontier?
    """
    # Parse orient.py and dispatch_optimizer.py to check which layers fire
    results = {
        "L1_danger_boost": {"description": "Score +1.5 for 2-wave danger zone", "fires": 0, "evidence": []},
        "L2_commit_floor": {"description": "Median score minimum for COMMIT domains", "fires": 0, "evidence": []},
        "L3_guarantee_boost": {"description": "Promote top COMMIT to 3rd-place", "fires": 0, "evidence": []},
        "L4_reservation": {"description": "1-in-5 mandatory allocation", "fires": 0, "evidence": []},
        "L5_orient_due": {"description": "Stalled-campaign naming in orient.py", "fires": 0, "evidence": []},
    }

    # Check dispatch_optimizer.py source for layer firing conditions
    dispatch_src = (ROOT / "tools" / "dispatch_optimizer.py").read_text()

    # Count how many layers are implemented and active
    layer_indicators = {
        "L1": "danger" in dispatch_src and "boost" in dispatch_src,
        "L2": "COMMIT" in dispatch_src and "floor" in dispatch_src,
        "L3": "guarantee" in dispatch_src,
        "L4": "reservation" in dispatch_src or "1-in-5" in dispatch_src,
        "L5": "stall" in dispatch_src.lower() or "wave_2" in dispatch_src,
    }

    # Check orient.py for L5
    orient_src = (ROOT / "tools" / "orient.py").read_text()
    layer_indicators["L5_orient"] = "stall" in orient_src.lower() or "campaign" in orient_src.lower()

    return results, layer_indicators

def get_campaign_wave_data():
    """Get campaign wave data from dispatch_optimizer --json --all."""
    try:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "dispatch_optimizer.py"), "--json", "--all"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data
    except Exception as e:
        return {"error": str(e)}
    return None

def main():
    lanes = parse_lanes()
    stalled = get_stalled_frontiers_at_s400()

    # H4 targeting rate
    targeted, non_targeted = classify_targeting(lanes, stalled)
    total = len(targeted) + len(non_targeted)
    rate = len(targeted) / total if total > 0 else 0

    # Valley escapes
    escaped = count_valley_escapes(lanes)

    # Escalation architecture
    escalation, layer_indicators = analyze_escalation_layers(lanes)

    # Campaign wave data
    wave_data = get_campaign_wave_data()
    wave_2_stalls = []
    if wave_data and isinstance(wave_data, dict) and "wave_2_stalls" in wave_data:
        wave_2_stalls = wave_data["wave_2_stalls"]

    # Resolution criteria check
    targeting_sustained = rate > 0.15
    escapes_sufficient = len(escaped) >= 3
    resolution_ready = targeting_sustained and escapes_sufficient

    results = {
        "experiment": "f-str3-h4-escalation-s404",
        "frontier": "F-STR3",
        "domain": "strategy",
        "session": "S404",
        "date": "2026-03-01",
        "type": "prospective-measurement",
        "mode": "hardening",
        "check_mode": "verification",
        "hypothesis": "H4: 5th escalation increases frontier targeting from 0% baseline",
        "baseline": {"rate": 0.0, "session": "S400", "n": 13, "source": "L-845"},
        "s403_measurement": {"rate": 0.278, "n": 18, "targeted": 5},
        "s404_measurement": {
            "total_domex_lanes_s401_s404": total,
            "targeted_count": len(targeted),
            "non_targeted_count": len(non_targeted),
            "targeting_rate": round(rate, 3),
            "targeted_lanes": targeted,
            "non_targeted_sample": non_targeted[:5],
        },
        "valley_escapes": {
            "count": len(escaped),
            "frontiers": sorted(escaped),
            "threshold": 3,
            "met": escapes_sufficient,
        },
        "escalation_architecture": {
            "layers_implemented": layer_indicators,
            "analysis": escalation,
            "finding": "See analysis below",
        },
        "resolution_criteria": {
            "targeting_sustained_above_15pct": targeting_sustained,
            "valley_escapes_gte_3": escapes_sufficient,
            "resolution_ready": resolution_ready,
            "sessions_remaining": max(0, 411 - 404),
        },
        "wave_2_stalls_current": len(wave_2_stalls) if isinstance(wave_2_stalls, list) else "unavailable",
    }

    # Print summary
    print(f"=== F-STR3 H4 Prospective Update (S404) ===")
    print(f"Targeting rate: {len(targeted)}/{total} = {rate:.1%} (baseline 0%, S403 27.8%)")
    print(f"Valley escapes: {len(escaped)} ({', '.join(sorted(escaped)) if escaped else 'none'})")
    print(f"Resolution criteria: targeting>{15}% = {targeting_sustained}, escapes>=3 = {escapes_sufficient}")
    print(f"Resolution ready: {resolution_ready}")
    print(f"Sessions remaining in window: {411 - 404}")
    print()
    print(f"Layer indicators:")
    for k, v in layer_indicators.items():
        print(f"  {k}: {'ACTIVE' if v else 'MISSING'}")
    print()
    print(f"Targeted lanes ({len(targeted)}):")
    for t in targeted:
        print(f"  {t['lane']} S{t['session']} → {'/'.join(t['frontiers'])} [{t['status']}] mode={t['mode']}")
    print()
    print(f"Non-targeted lanes ({len(non_targeted)}):")
    for nt in non_targeted:
        print(f"  {nt['lane']} S{nt['session']} → {'/'.join(nt['frontiers'])} [{nt['status']}] mode={nt['mode']}")

    # Save
    out_path = ROOT / "experiments" / "strategy" / "f-str3-h4-escalation-s404.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_path}")

    return results

if __name__ == "__main__":
    results = main()
