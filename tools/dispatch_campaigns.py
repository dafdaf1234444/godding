#!/usr/bin/env python3
"""Campaign wave tracking for dispatch optimizer (F-STR3, L-755).

Extracted from dispatch_optimizer.py to reduce tool size (F-META17).
Tracks frontier campaign waves, phase classification, and resolution prescriptions.

Key evidence: 1-wave=28%, 2-wave=11% (valley of death), 3-wave=31%, 4+-wave=50%.
"""

import re
from pathlib import Path

DOMAINS_DIR = Path("domains")
LANES_FILE = Path("tasks/SWARM-LANES.md")
LANES_ARCHIVE = Path("tasks/SWARM-LANES-ARCHIVE.md")

# Campaign wave scoring (F-STR3, L-755): non-monotonic resolution rates.
WAVE_DANGER_BOOST = 1.5     # 2-wave -> attract 3rd wave (11% -> 31% resolution)
WAVE_COMMITTED_BOOST = 0.5  # 3-wave -> approaching resolution (31% -> 50%)

# COMMIT reservation (F-STR3, L-815): mandatory allocation for danger-zone domains.
COMMIT_RESERVATION_WINDOW = 5  # check last N lanes for COMMIT-domain presence

# Mode transition matrix (L-755: mode transitions predict success, repeated modes don't)
OPTIMAL_NEXT_MODE = {
    "exploration": "hardening",
    "hardening": "resolution",
    "resolution": "resolution",
}

# Resolution probability by wave count (L-755, n=93 campaigns, 197 lanes)
WAVE_RESOLUTION_PROB = {1: 0.28, 2: 0.11, 3: 0.31}  # 4+ = 0.50


def get_domain_resolved_frontier_ids() -> set[str]:
    """Collect resolved frontier IDs from all domain FRONTIER.md files.

    Handles renames like 'F-CRYPTO2 (was F-CC2)' by extracting both IDs.
    Used to cross-check wave_2_stalls -- prevents false positives when frontiers
    are resolved via rename/alias without a MERGED SWARM-LANES.md entry.
    """
    resolved: set[str] = set()
    if not DOMAINS_DIR.exists():
        return resolved
    for domain_dir in DOMAINS_DIR.iterdir():
        frontier_path = domain_dir / "tasks" / "FRONTIER.md"
        if not frontier_path.exists():
            continue
        try:
            content = frontier_path.read_text()
        except OSError:
            continue
        resolved_match = re.search(r"## Resolved(.*)", content, re.DOTALL)
        if not resolved_match:
            continue
        for fid in re.findall(r"\bF-[A-Z][A-Z0-9]+\b", resolved_match.group()):
            resolved.add(fid)
    return resolved


def get_campaign_waves(lane_abbrev_to_domain: dict[str, str]) -> dict[str, dict]:
    """Parse lanes to compute campaign wave state per domain (F-STR3, L-755).

    Groups closed+active lanes by frontier to form campaigns.
    Returns {domain: {
        "frontiers": {fid: {"waves": N, "last_mode": str, "last_session": int,
                            "resolved": bool, "mode_repeat": bool, "all_modes": [str]}},
        "max_wave": int, "wave_2_stalls": [fid], "mode_repeats": [fid]
    }}
    """
    contents: list[str] = []
    for f in (LANES_FILE, LANES_ARCHIVE):
        if f.exists():
            contents.append(f.read_text())
    if not contents:
        return {}

    frontier_lanes: dict[str, list[dict]] = {}
    for line in "\n".join(contents).splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12:
            continue

        lane_id = cols[2] if len(cols) > 2 else ""
        etc = cols[10] if len(cols) > 10 else ""
        status = (cols[11] if len(cols) > 11 else "").upper().strip()

        frontier_str_m = re.search(r"frontier=(F-[A-Z0-9,/\s-]+?)(?:;|$)", etc)
        if not frontier_str_m:
            continue
        frontiers = re.findall(r"F-[A-Z0-9]+", frontier_str_m.group(1))
        if not frontiers:
            continue

        dom = None
        m = re.match(r"DOMEX-([A-Z]+)", lane_id)
        if m:
            dom = lane_abbrev_to_domain.get(m.group(1))
        if not dom:
            focus_m = re.search(r"focus=(?:domains/)?([a-z0-9-]+)", etc)
            if focus_m and focus_m.group(1) not in ("global", ""):
                dom = focus_m.group(1)
        if not dom:
            continue

        sess_str = cols[3] if len(cols) > 3 else ""
        sess_m = re.search(r"S?(\d+)", sess_str)
        sess = int(sess_m.group(1)) if sess_m else 0

        intent = ""
        intent_m = re.search(r"intent=([^;]+)", etc)
        if intent_m:
            intent = intent_m.group(1).lower()

        explicit_mode_m = re.search(r"\bmode=(exploration|hardening|replication|resolution)\b", etc)
        if explicit_mode_m:
            mode = explicit_mode_m.group(1)
        else:
            mode = "exploration"
            if any(kw in intent for kw in ("harden", "validat", "retest", "prospective",
                                            "verify", "audit", "replicat", "correct")):
                mode = "hardening"
            elif any(kw in intent for kw in ("resolve", "close", "final", "build",
                                              "implement", "integrat", "wire")):
                mode = "resolution"

        for frontier in frontiers:
            frontier_lanes.setdefault(frontier, []).append({
                "domain": dom, "session": sess, "status": status,
                "mode": mode, "lane_id": lane_id,
            })

    domain_resolved_ids = get_domain_resolved_frontier_ids()

    domain_campaigns: dict[str, dict] = {}
    for frontier, lanes in frontier_lanes.items():
        lanes.sort(key=lambda x: x["session"])
        dom = lanes[0]["domain"]
        wave_count = len(lanes)
        last_mode = lanes[-1]["mode"]
        last_session = lanes[-1]["session"]
        resolved = (
            any(l["status"] == "MERGED" for l in lanes)
            or frontier in domain_resolved_ids
        )
        modes = [l["mode"] for l in lanes]
        mode_repeat = len(modes) >= 2 and modes[-1] == modes[-2]

        if dom not in domain_campaigns:
            domain_campaigns[dom] = {
                "frontiers": {}, "max_wave": 0,
                "wave_2_stalls": [], "mode_repeats": [],
            }
        domain_campaigns[dom]["frontiers"][frontier] = {
            "waves": wave_count, "last_mode": last_mode,
            "last_session": last_session, "resolved": resolved,
            "mode_repeat": mode_repeat, "all_modes": modes,
        }
        domain_campaigns[dom]["max_wave"] = max(
            domain_campaigns[dom]["max_wave"], wave_count
        )
        if wave_count == 2 and not resolved:
            domain_campaigns[dom]["wave_2_stalls"].append(frontier)
        if mode_repeat and not resolved:
            domain_campaigns[dom]["mode_repeats"].append(frontier)

    return domain_campaigns


def campaign_phase(waves: int) -> tuple[str, str]:
    """Classify campaign phase and prescription based on wave count (F-STR3, L-755)."""
    if waves == 0:
        return "new", ""
    elif waves == 1:
        return "single", "if revisiting, commit to 3+ waves (avoid 2-wave trap)"
    elif waves == 2:
        return "danger", "COMMIT 3rd wave or CLOSE (11% resolution at 2 waves)"
    elif waves == 3:
        return "committed", "continue -- approaching resolution (31%)"
    else:
        return "veteran", f"sustained ({waves} waves, ~50% resolution)"


def wave_prescriptions(campaign_waves: dict[str, dict]) -> list[dict]:
    """Generate per-frontier prescriptions for all unresolved campaigns (F-STR3, L-755).

    Returns sorted list of {frontier, domain, waves, modes, last_mode, next_mode,
    current_prob, next_prob, action, mode_shift_needed} dicts.
    """
    ACTION_PRIORITY = {"COMMIT": 0, "CLOSE": 1, "SUSTAIN": 2, "CONTINUE": 3, "NEW": 4}
    prescriptions = []
    for dom, cw in campaign_waves.items():
        for fid, fdata in cw.get("frontiers", {}).items():
            if fdata["resolved"]:
                continue
            waves = fdata["waves"]
            modes = fdata.get("all_modes", [])
            last_mode = fdata["last_mode"]
            mode_repeat = fdata.get("mode_repeat", False)

            next_mode = OPTIMAL_NEXT_MODE.get(last_mode, "hardening")
            current_prob = WAVE_RESOLUTION_PROB.get(waves, 0.50 if waves >= 4 else 0.28)
            next_prob = WAVE_RESOLUTION_PROB.get(waves + 1, 0.50 if waves + 1 >= 4 else 0.28)

            if waves == 0:
                action = "NEW"
            elif waves == 1:
                action = "CONTINUE"
            elif waves == 2:
                action = "COMMIT"
            elif waves == 3:
                action = "CLOSE"
            else:
                action = "SUSTAIN"

            prescriptions.append({
                "frontier": fid, "domain": dom, "waves": waves,
                "modes": modes, "last_mode": last_mode, "next_mode": next_mode,
                "current_prob": current_prob, "next_prob": next_prob,
                "action": action, "mode_shift_needed": mode_repeat,
            })
    prescriptions.sort(key=lambda p: (ACTION_PRIORITY.get(p["action"], 9), -p["waves"]))
    return prescriptions


def print_wave_plan(prescriptions: list[dict]) -> None:
    """Print the prescriptive wave plan table."""
    if not prescriptions:
        print("\n--- Wave Plan (F-STR3, L-755) ---")
        print("  No unresolved campaigns found.")
        return
    print(f"\n--- Wave Plan (F-STR3, L-755) — {len(prescriptions)} unresolved campaigns ---")
    print(f"  {'Action':<8} {'Domain':<22} {'Frontier':<10} {'W':>2} {'Modes':<30} {'Next':<12} {'P(now)':>6} {'P(+1)':>6}")
    print(f"  " + "-" * 100)
    for p in prescriptions:
        mode_str = "->".join(p["modes"][:4])
        if len(p["modes"]) > 4:
            mode_str += f"..({len(p['modes'])})"
        shift_mark = " !" if p["mode_shift_needed"] else ""
        print(
            f"  {p['action']:<8} {p['domain']:<22} {p['frontier']:<10} {p['waves']:>2} "
            f"{mode_str:<30} -> {p['next_mode']:<9} "
            f"{p['current_prob']:5.0%} {p['next_prob']:>5.0%}{shift_mark}"
        )
    commit_count = sum(1 for p in prescriptions if p["action"] == "COMMIT")
    shift_count = sum(1 for p in prescriptions if p["mode_shift_needed"])
    if commit_count:
        print(f"\n  {commit_count} COMMIT (escape 2-wave valley of death: 11% -> 31%)")
    if shift_count:
        print(f"  {shift_count} mode stalls (! = same mode repeated, shift needed)")
    print(f"  Rule: >=3 waves with mode shifts -> 50% resolution (L-755)")


def print_campaign_advisory(results: list[dict], campaign_waves: dict[str, dict]) -> None:
    """Print campaign advisory section in dispatch output (F-STR3, L-755)."""
    danger_doms = [r for r in results if r.get("campaign_phase") == "danger"]
    committed_doms = [r for r in results if r.get("campaign_phase") == "committed"]
    veteran_doms = [r for r in results if r.get("campaign_phase") == "veteran"]
    mode_stall_items = []
    for r in results:
        for fid in r.get("mode_repeats", []):
            cw = campaign_waves.get(r["domain"], {})
            fdata = cw.get("frontiers", {}).get(fid, {})
            modes = fdata.get("all_modes", [])
            mode_stall_items.append((r["domain"], fid, modes))

    prescriptions = wave_prescriptions(campaign_waves)
    commits = [p for p in prescriptions if p["action"] == "COMMIT"]
    closes = [p for p in prescriptions if p["action"] == "CLOSE"]

    if not (danger_doms or committed_doms or veteran_doms or mode_stall_items):
        return

    print(f"\n--- Campaign Advisory (F-STR3, L-755) ---")
    print(f"  Resolution: 1w=28%, 2w=11% (valley), 3w=31%, 4w+=50%")
    if commits:
        print(f"  COMMIT ({len(commits)} frontiers in valley of death — 11% -> 31%):")
        for p in commits:
            mode_str = " -> ".join(p["modes"])
            shift = " !" if p["mode_shift_needed"] else ""
            print(f"    ⚠ {p['domain']}: {p['frontier']} ({mode_str}) -> {p['next_mode']}{shift}")
    elif danger_doms:
        print(f"  Valley of death (2 waves — 11% resolution):")
        for r in danger_doms:
            print(f"    ⚠ {r['domain']} — {r['campaign_rx']}")
    if closes:
        print(f"  CLOSE ({len(closes)} frontiers approaching resolution — 31% -> 50%):")
        for p in closes:
            mode_str = " -> ".join(p["modes"][:3])
            shift = " !" if p["mode_shift_needed"] else ""
            print(f"    -> {p['domain']}: {p['frontier']} ({mode_str}) -> {p['next_mode']}{shift}")
    elif committed_doms:
        print(f"  Approaching resolution (3 waves — 31%):")
        for r in committed_doms:
            print(f"    -> {r['domain']} — {r['campaign_rx']}")
    if veteran_doms:
        print(f"  Veteran campaigns (4+ waves — ~50%):")
        for r in veteran_doms[:5]:
            cw = campaign_waves.get(r["domain"], {})
            fids = [f for f, d in cw.get("frontiers", {}).items() if not d["resolved"]]
            fid_str = f" ({', '.join(fids[:2])})" if fids else ""
            print(f"    + {r['domain']}{fid_str}")
    if mode_stall_items:
        print(f"  Mode stalls (same mode >=2 consecutive waves):")
        for dom, fid, modes in mode_stall_items[:5]:
            mode_str = " -> ".join(modes)
            next_mode = OPTIMAL_NEXT_MODE.get(modes[-1], "hardening")
            print(f"    ! {dom}: {fid} ({mode_str}) -> MODE SHIFT to {next_mode}")
    print(f"  Full plan: python3 tools/dispatch_optimizer.py --wave-plan")
