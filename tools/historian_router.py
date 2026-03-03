#!/usr/bin/env python3
"""
historian_router.py — Third mechanism for F-NK6 domain→global frontier convergence.

Scans recently-MERGED DOMEX lanes from SWARM-LANES.md, identifies which domain
frontiers link to global frontiers, and produces synthesis routing suggestions.

Three-mechanism model (L-996):
  1. structural_links (frontier_crosslink.py)  — OPERATIONAL 10.1%
  2. enforcement_gate (close_lane.py surfacing) — PARTIAL
  3. historian_routing (THIS TOOL)              — builds the missing piece

Usage:
  python3 tools/historian_router.py              # text report
  python3 tools/historian_router.py --json       # machine-readable
  python3 tools/historian_router.py --window 10  # scan last 10 sessions (default: 5)
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LANES_FILE = REPO_ROOT / "tasks" / "SWARM-LANES.md"
GLOBAL_FRONTIER = REPO_ROOT / "tasks" / "FRONTIER.md"
DOMAINS_DIR = REPO_ROOT / "domains"

ABBREV_MAP = {
    "nk": "nk-complexity", "meta": "meta", "sec": "security", "exp": "expert-swarm",
    "cat": "catastrophic-risks", "brn": "brain", "evo": "evolution", "eco": "economy",
    "ai": "ai", "hs": "human-systems", "gt": "graph-theory", "ling": "linguistics",
    "crypto": "cryptocurrency", "cry": "cryptography", "eval": "evaluation",
    "comp": "competitions", "is": "information-science", "ct": "control-theory",
    "ds": "distributed-systems", "phy": "physics", "his": "history", "rmt": "random-matrix-theory",
    "str": "string-theory", "fra": "fractals", "sta": "statistics", "psy": "psychology",
    "pe": "protocol-engineering", "gam": "gaming", "fin": "finance", "far": "far-future",
}


def _load_global_frontier_ids() -> dict[str, str]:
    """Return {frontier_id: full_text_block} for global frontiers."""
    if not GLOBAL_FRONTIER.exists():
        return {}
    text = GLOBAL_FRONTIER.read_text(encoding="utf-8")
    frontiers = {}
    for block in re.split(r"\n(?=- \*\*)", text):
        m = re.match(r"- \*\*(F-[A-Z0-9]+)\*\*", block.strip())
        if m and "~~" not in block[:30]:
            frontiers[m.group(1)] = block.strip()
    return frontiers


def _domain_frontier_global_links(domain_dir: str) -> list[tuple[str, list[str]]]:
    """Find domain frontier questions that reference global frontier IDs."""
    frontier_path = DOMAINS_DIR / domain_dir / "tasks" / "FRONTIER.md"
    if not frontier_path.exists():
        return []
    global_ids = set(_load_global_frontier_ids().keys())
    content = frontier_path.read_text(encoding="utf-8")
    active = content
    if "## Active" in content:
        active = content.split("## Active")[1]
        for cut in ["## Archived", "## Resolved", "## Closed"]:
            if cut in active:
                active = active.split(cut)[0]
    links = []
    for fq in set(re.findall(r"\*\*(F-[A-Z0-9\-]+)\*\*", active)):
        fq_pat = re.compile(rf"\*\*{re.escape(fq)}\*\*.*?(?=\n- \*\*F-|\Z)", re.DOTALL)
        m = fq_pat.search(active)
        if m:
            grefs = sorted(set(
                r for r in re.findall(r"F-[A-Z][A-Z0-9]+", m.group(0))
                if r in global_ids and r != fq
            ))
            if grefs:
                links.append((fq, grefs))
    return links


def _parse_merged_lanes(window: int) -> list[dict]:
    """Extract recently-MERGED DOMEX lanes from SWARM-LANES.md."""
    if not LANES_FILE.exists():
        return []
    text = LANES_FILE.read_text(encoding="utf-8")
    lanes = []
    for line in text.splitlines():
        if "| MERGED |" not in line or "DOMEX-" not in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 13:
            continue
        lane_id = cols[2]
        session_str = cols[3]
        etc_field = cols[10]
        notes = cols[12]
        # Extract session number
        sess_match = re.search(r"S?(\d+)", session_str)
        if not sess_match:
            continue
        sess_num = int(sess_match.group(1))
        # Extract domain abbreviation from lane ID (anchor to -S\d+ session suffix)
        domex_match = re.match(r"DOMEX-([A-Z]+(?:-[A-Z]+)*)-S\d+", lane_id.upper())
        if not domex_match:
            continue
        abbrev = domex_match.group(1).lower()
        domain = ABBREV_MAP.get(abbrev, abbrev)
        # Extract frontier from Etc
        frontier_match = re.search(r"frontier=(F-[A-Z0-9\-]+)", etc_field)
        frontier = frontier_match.group(1) if frontier_match else None
        # Extract actual outcome
        actual_match = re.search(r"actual=([^;]+)", etc_field)
        actual = actual_match.group(1).strip() if actual_match else ""
        lanes.append({
            "lane_id": lane_id, "session": sess_num, "domain": domain,
            "frontier": frontier, "actual": actual[:200], "notes": notes[:200],
        })
    # Filter to recent window
    if not lanes:
        return []
    max_sess = max(l["session"] for l in lanes)
    return [l for l in lanes if l["session"] >= max_sess - window]


def scan_synthesis_candidates(window: int = 5) -> list[dict]:
    """Main scan: find MERGED domain lanes whose work links to global frontiers."""
    merged = _parse_merged_lanes(window)
    global_frontiers = _load_global_frontier_ids()
    candidates = []
    seen_domains = set()
    for lane in merged:
        domain = lane["domain"]
        if domain in seen_domains:
            continue
        links = _domain_frontier_global_links(domain)
        if links:
            seen_domains.add(domain)
            candidates.append({
                "domain": domain,
                "lane_id": lane["lane_id"],
                "session": lane["session"],
                "domain_frontier": lane.get("frontier", "unknown"),
                "global_links": [{"domain_fq": fq, "global_refs": refs} for fq, refs in links],
                "actual_summary": lane["actual"][:120],
            })
    return candidates


def diagnose_frontier_enforcement(current_session: int = 0) -> list[dict]:
    """L-1143: Classify global frontier enforcement level before routing.

    Determines whether stalled frontiers need enforcement (L-601),
    not just more crosslinks (Goldstone rotations, L-1138).
    #L-1143 #L-601 #L-1138
    """
    global_frontiers = _load_global_frontier_ids()
    tool_dir = REPO_ROOT / "tools"
    periodics_path = tool_dir / "periodics.json"

    # Collect frontier refs from periodics
    periodics_refs: set = set()
    if periodics_path.exists():
        try:
            data = json.loads(periodics_path.read_text(encoding="utf-8"))
            items = data.get("items", []) if isinstance(data, dict) else data
            for p in items:
                if not isinstance(p, dict):
                    continue
                desc = p.get("description", "") + " " + p.get("name", "")
                for fid in re.findall(r"F-[A-Z][A-Z0-9]+|F\d+", desc):
                    periodics_refs.add(fid)
        except (json.JSONDecodeError, KeyError):
            pass

    # Scan tool files for frontier references
    tool_refs: dict = {}
    for fid in global_frontiers:
        tool_refs[fid] = []
    for py in sorted(tool_dir.glob("*.py")):
        try:
            content = py.read_text(encoding="utf-8")
        except OSError:
            continue
        for fid in global_frontiers:
            if fid in content:
                tool_refs[fid].append(py.name)

    results = []
    for fid, text in global_frontiers.items():
        # Skip resolved (strikethrough)
        if "~~" in text[:50]:
            continue

        tool_count = len(tool_refs.get(fid, []))
        in_periodics = fid in periodics_refs

        # Extract most recent session mention
        sess_nums = [int(s) for s in re.findall(r"S(\d+)", text)]
        last_session = max(sess_nums) if sess_nums else 0
        staleness = current_session - last_session if current_session else 0

        # Classify enforcement level (L-1143)
        if tool_count >= 3:
            level = "STRUCTURAL"
        elif tool_count >= 1 or in_periodics:
            level = "PARTIALLY_STRUCTURAL"
        else:
            level = "ASPIRATIONAL"

        # Recommended intervention per L-1143
        if level == "ASPIRATIONAL":
            intervention = "Wire into tool or periodic (L-601)"
        elif level == "PARTIALLY_STRUCTURAL":
            intervention = "Strengthen enforcement gate"
        else:
            intervention = "M4 resolution-intent session"

        results.append({
            "frontier": fid,
            "enforcement": level,
            "tool_refs": tool_count,
            "tool_files": tool_refs.get(fid, []),
            "in_periodics": in_periodics,
            "last_session": last_session,
            "staleness": staleness,
            "intervention": intervention,
        })

    # Sort: ASPIRATIONAL first (most actionable), then by staleness
    order = {"ASPIRATIONAL": 0, "PARTIALLY_STRUCTURAL": 1, "STRUCTURAL": 2}
    results.sort(key=lambda r: (order.get(r["enforcement"], 9), -r["staleness"]))
    return results


def _get_current_session() -> int:
    """Read current session number from INDEX.md."""
    try:
        idx = (REPO_ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8")
        sm = re.search(r"Sessions?:\s*S?(\d+)", idx)
        if sm:
            return int(sm.group(1))
    except OSError:
        pass
    return 0


def main():
    ap = argparse.ArgumentParser(description="Historian routing: domain→global synthesis scanner")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--window", type=int, default=5, help="Session window for MERGED lane scan")
    ap.add_argument("--enforce", action="store_true", help="Show enforcement diagnosis only (L-1143)")
    args = ap.parse_args()

    current_session = _get_current_session()
    enforcement = diagnose_frontier_enforcement(current_session)

    if args.enforce:
        if args.json:
            json.dump({"enforcement": enforcement, "current_session": current_session}, sys.stdout, indent=2)
            print()
            return
        print("=== FRONTIER ENFORCEMENT DIAGNOSIS (L-1143) ===")
        print(f"Session: S{current_session}")
        for e in enforcement:
            stale_tag = f" (+{e['staleness']}s)" if e["staleness"] > 15 else ""
            tools_str = f" [{', '.join(e['tool_files'][:3])}]" if e["tool_files"] else ""
            periodic_tag = " +periodic" if e["in_periodics"] else ""
            print(f"  {e['enforcement']:24s} {e['frontier']:10s} (S{e['last_session']}{stale_tag}) refs={e['tool_refs']}{tools_str}{periodic_tag}")
            print(f"    -> {e['intervention']}")
        asp = sum(1 for e in enforcement if e["enforcement"] == "ASPIRATIONAL")
        print(f"\nASPIRATIONAL: {asp}/{len(enforcement)} -- these stall without L-601 enforcement")
        print("================================================")
        return

    candidates = scan_synthesis_candidates(window=args.window)
    global_frontiers = _load_global_frontier_ids()
    merged_count = len(_parse_merged_lanes(args.window))

    result = {
        "merged_lanes_scanned": merged_count,
        "synthesis_candidates": len(candidates),
        "global_frontiers_reachable": len(set(
            ref for c in candidates for link in c["global_links"] for ref in link["global_refs"]
        )),
        "candidates": candidates,
        "enforcement": enforcement,
    }

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
        return

    print("=== HISTORIAN ROUTING (F-NK6 mechanism 3, L-996) ===")
    print(f"Scanned {merged_count} MERGED lanes (last {args.window} sessions)")
    print(f"Synthesis candidates: {len(candidates)}")
    print(f"Global frontiers reachable: {result['global_frontiers_reachable']}/{len(global_frontiers)}")
    print()
    if not candidates:
        print("No synthesis candidates found. Domain frontiers may lack global refs.")
        print("Run: python3 tools/frontier_crosslink.py --stats")
    for c in candidates:
        print(f"  [{c['domain']}] {c['lane_id']} (S{c['session']})")
        print(f"    Domain frontier: {c['domain_frontier']}")
        for link in c["global_links"]:
            print(f"    {link['domain_fq']} -> global: {', '.join(link['global_refs'])}")
        if c["actual_summary"]:
            print(f"    Outcome: {c['actual_summary']}...")
        print()

    # L-1143: Enforcement diagnosis summary
    asp = [e for e in enforcement if e["enforcement"] == "ASPIRATIONAL"]
    if asp:
        print("--- Enforcement diagnosis (L-1143) ---")
        print(f"  {len(asp)} ASPIRATIONAL frontier(s) -- stall without L-601 enforcement:")
        for e in asp:
            stale = f" (+{e['staleness']}s stale)" if e["staleness"] > 15 else ""
            print(f"    {e['frontier']}{stale} -> {e['intervention']}")
        print()

    print("===================================================")


if __name__ == "__main__":
    main()
