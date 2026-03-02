#!/usr/bin/env python3
"""anxiety_trigger.py — F-ISG1: auto-select highest-urgency anxiety-zone frontier for dispatch.

Usage:
  python3 tools/anxiety_trigger.py            # print top anxiety-zone frontier + dispatch command
  python3 tools/anxiety_trigger.py --json     # output JSON for pipeline use
  python3 tools/anxiety_trigger.py --list     # list all anxiety zones ranked by age

Anxiety zone: a frontier open >15 sessions without a progress update.
Used as the gate for autonomous dispatch (autoswarm.sh → anxiety_trigger.py → claude --print).
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
FRONTIER_PATH = REPO_ROOT / "tasks" / "FRONTIER.md"
SESSION_LOG_PATH = REPO_ROOT / "memory" / "SESSION-LOG.md"
ANXIETY_THRESHOLD = 15  # sessions


try:
    _tools_path = str(Path(__file__).resolve().parent)
    import sys as _sys; _sys.path.insert(0, _tools_path)
    from swarm_io import session_number as _current_session
except ImportError:
    def _current_session() -> int:
        """Read highest session number from SESSION-LOG.md (handles both | S and S\t| formats)."""
        if not SESSION_LOG_PATH.exists():
            return 0
        text = SESSION_LOG_PATH.read_text()
        nums = [int(m) for m in re.findall(r"(?:^\|?\s*S|S)(\d{3,})\b", text, re.MULTILINE)]
        return max(nums) if nums else 0


def _parse_anxiety_zones(frontier_text: str, current: int) -> list[dict]:
    """Extract frontiers with no update in >ANXIETY_THRESHOLD sessions."""
    zones = []
    # Split on active section only (stop at Archive/Resolved)
    active_text = re.split(r"^## Archive|^## Resolved", frontier_text, flags=re.MULTILINE)[0]

    pattern = re.compile(
        r"^- \*\*([A-Z][^*]+)\*\*:(.*?)(?=^- \*\*[A-Z]|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(active_text):
        fid = m.group(1).strip()
        body = m.group(2).strip()
        s_nums = [int(x) for x in re.findall(r"\bS(\d+)\b", body)]
        if not s_nums:
            continue
        last_active = max(s_nums)
        age = current - last_active
        if age > ANXIETY_THRESHOLD:
            # Extract first sentence as description
            desc_match = re.match(r"([^.?!]{10,120}[.?!]?)", body.replace("\n", " "))
            desc = desc_match.group(1).strip() if desc_match else body[:100]
            zones.append({"id": fid, "last_session": last_active, "age": age, "desc": desc})

    # Sort: oldest first (highest urgency)
    zones.sort(key=lambda z: z["age"], reverse=True)
    return zones


def _dispatch_command(frontier_id: str) -> str:
    """Generate a claude --print dispatch command for the given frontier."""
    return (
        f'claude --print --dangerously-skip-permissions '
        f'"swarm focus on {frontier_id}: pick up where it left off, '
        f'produce one artifact (lesson or experiment JSON), commit."'
    )


def main():
    parser = argparse.ArgumentParser(description="Anxiety-zone frontier trigger for F-ISG1")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--list", action="store_true", help="List all anxiety zones")
    args = parser.parse_args()

    current = _current_session()
    if current == 0:
        print("ERROR: could not determine current session from SESSION-LOG.md", file=sys.stderr)
        sys.exit(1)

    if not FRONTIER_PATH.exists():
        print(f"ERROR: {FRONTIER_PATH} not found", file=sys.stderr)
        sys.exit(1)

    frontier_text = FRONTIER_PATH.read_text()
    zones = _parse_anxiety_zones(frontier_text, current)

    if not zones:
        result = {"status": "no_anxiety_zones", "current_session": current, "threshold": ANXIETY_THRESHOLD}
        if args.json:
            print(json.dumps(result))
        else:
            print(f"No anxiety zones found (threshold: >{ANXIETY_THRESHOLD} sessions). Swarm is current.")
        return

    if args.list:
        print(f"Anxiety zones (>{ANXIETY_THRESHOLD} sessions stale) as of S{current}:\n")
        for z in zones:
            print(f"  {z['id']:15s}  last=S{z['last_session']}  age=+{z['age']}s  {z['desc'][:60]}")
        print(f"\nTotal: {len(zones)}")
        return

    top = zones[0]
    cmd = _dispatch_command(top["id"])

    if args.json:
        result = {
            "status": "anxiety_zone_found",
            "current_session": current,
            "threshold": ANXIETY_THRESHOLD,
            "top_frontier": top,
            "dispatch_command": cmd,
            "all_zones_count": len(zones),
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"[anxiety_trigger] S{current} | {len(zones)} anxiety zone(s) | Top: {top['id']} (+{top['age']} sessions)")
        print(f"Description: {top['desc'][:100]}")
        print(f"\nDispatch:\n  {cmd}")


if __name__ == "__main__":
    main()
