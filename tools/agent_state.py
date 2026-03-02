#!/usr/bin/env python3
"""agent_state.py — Agent position registry for swarm coordination.

Council finding (S340): 5/5 experts converged on agent registry as #1 priority.
Agents need to know where other agents are to avoid duplication and spread work.

This tool provides:
  - register: write current agent position at session start
  - show: display all active agent positions
  - sweep: remove stale entries (>90min heartbeat)
  - check-collision: warn if another agent claims the same domain

Data stored in workspace/agent_positions.json (gitignored — ephemeral state).

Usage:
    python3 tools/agent_state.py register --session S340 --domain meta --lane DOMEX-META-S340
    python3 tools/agent_state.py show
    python3 tools/agent_state.py sweep
    python3 tools/agent_state.py check-collision --domain meta
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "workspace" / "agent_positions.json"
STALE_MINUTES = 90


def _load() -> list[dict]:
    if not STATE_FILE.exists():
        return []
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(entries, indent=2) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _is_stale(entry: dict) -> bool:
    try:
        hb = datetime.fromisoformat(entry["heartbeat"])
        age = (datetime.now(timezone.utc) - hb).total_seconds()
        return age > STALE_MINUTES * 60
    except (KeyError, ValueError):
        return True


def sweep(entries: list[dict]) -> list[dict]:
    """Remove stale entries (>90min since last heartbeat)."""
    live = [e for e in entries if not _is_stale(e)]
    return live


def register(session: str, domain: str, lane: str) -> None:
    """Register or update agent position."""
    entries = sweep(_load())

    # Update existing entry for this session, or add new
    now = _now_iso()
    found = False
    for e in entries:
        if e.get("session") == session:
            e["domain"] = domain
            e["lane"] = lane
            e["heartbeat"] = now
            found = True
            break

    if not found:
        entries.append({
            "session": session,
            "domain": domain,
            "lane": lane,
            "started": now,
            "heartbeat": now,
        })

    _save(entries)
    print(f"Registered: session={session} domain={domain} lane={lane}")

    # Check for collision
    collisions = [e for e in entries
                  if e["domain"] == domain and e["session"] != session]
    if collisions:
        for c in collisions:
            print(f"  COLLISION: {c['session']} also claims domain={domain} (lane={c['lane']})")


def show() -> None:
    """Display all active agent positions."""
    entries = sweep(_load())
    _save(entries)  # persist sweep

    if not entries:
        print("No active agents registered.")
        return

    print(f"\n=== AGENT POSITIONS ({len(entries)} active) ===")
    print(f"{'Session':<10} {'Domain':<24} {'Lane':<30} {'Since':<12} {'Heartbeat':<12}")
    print("-" * 90)
    for e in entries:
        started = e.get("started", "?")[:19]
        hb = e.get("heartbeat", "?")[:19]
        print(f"{e['session']:<10} {e['domain']:<24} {e['lane']:<30} {started:<12} {hb:<12}")


def check_collision(domain: str) -> bool:
    """Check if any active agent claims this domain. Returns True if collision."""
    entries = sweep(_load())
    claims = [e for e in entries if e.get("domain") == domain]
    if claims:
        for c in claims:
            print(f"COLLISION: {c['session']} holds domain={domain} (lane={c['lane']})")
        return True
    print(f"CLEAR: no active agent on domain={domain}")
    return False


def get_active_domains() -> list[str]:
    """Return list of domains currently claimed by active agents."""
    entries = sweep(_load())
    return list({e["domain"] for e in entries if e.get("domain")})


def get_position_summary() -> list[dict]:
    """Return active positions for orient.py integration."""
    return sweep(_load())


def main():
    parser = argparse.ArgumentParser(description="Agent position registry")
    sub = parser.add_subparsers(dest="command")

    reg = sub.add_parser("register", help="Register agent position")
    reg.add_argument("--session", required=True)
    reg.add_argument("--domain", required=True)
    reg.add_argument("--lane", default="")

    sub.add_parser("show", help="Show active agent positions")
    sub.add_parser("sweep", help="Remove stale entries")

    col = sub.add_parser("check-collision", help="Check domain collision")
    col.add_argument("--domain", required=True)

    args = parser.parse_args()

    if args.command == "register":
        register(args.session, args.domain, args.lane)
    elif args.command == "show":
        show()
    elif args.command == "sweep":
        entries = sweep(_load())
        _save(entries)
        print(f"Sweep complete: {len(entries)} active agents remain.")
    elif args.command == "check-collision":
        has_collision = check_collision(args.domain)
        sys.exit(1 if has_collision else 0)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
