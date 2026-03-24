#!/usr/bin/env python3
"""
bulletin.py — Inter-swarm communication via bulletins.

Usage:
    python3 tools/bulletin.py write <swarm-name> <type> <message>
    python3 tools/bulletin.py request-help <swarm-name> <need>
    python3 tools/bulletin.py offer-help <swarm-name> <request-id> <response>
    python3 tools/bulletin.py help-queue
    python3 tools/bulletin.py frontier-query <swarm-name>
    python3 tools/bulletin.py frontier-respond <swarm-name> <query-id>
    python3 tools/bulletin.py frontier-inbox
    python3 tools/bulletin.py lane-announce <swarm-name> <lane-id> <frontier-id> [--scope "..."] [--status ACTIVE|MERGED]
    python3 tools/bulletin.py lane-check <swarm-name> <frontier-id> [--intent "..."]
    python3 tools/bulletin.py lane-inbox
    python3 tools/bulletin.py genesis-feedback <swarm-name> <feedback>
    python3 tools/bulletin.py read [swarm-name]
    python3 tools/bulletin.py scan
    python3 tools/bulletin.py sync <child-name>
    python3 tools/bulletin.py genesis-report

Types: discovery, question, warning, principle, belief-challenge, sibling-sync,
       help-request, help-response, genesis-feedback, frontier-query, frontier-response
genesis-feedback format: "used:atom1,atom2 ignored:atom3,atom4"
belief-challenge format: "PHIL-N: challenge text"  (child challenges parent philosophy)
request-help writes structured content:
  Request-ID: H-<timestamp>-<swarm>
  Need: <description>
offer-help links a response to a specific Request-ID.
frontier-query posts a structured query requesting a peer's frontier state.
frontier-respond reads local FRONTIER.md, extracts active frontiers, and posts as response.
Sync copies parent bulletins into a child's workspace for cross-swarm reading.
Run propagate_challenges.py to pull belief-challenges into PHILOSOPHY.md.
"""

import re
import shutil
import sys
import time
import os
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BULLETINS_DIR = REPO_ROOT / "experiments" / "inter-swarm" / "bulletins"
CHILDREN_DIR = REPO_ROOT / "experiments" / "children"
VALID_TYPES = {
    "discovery",
    "question",
    "warning",
    "principle",
    "belief-challenge",
    "sibling-sync",
    "help-request",
    "help-response",
    "frontier-query",
    "frontier-response",
    "lane-announce",
    "lane-check",
}
VALID_TIERS = {"T1", "T2", "T3"}
# Trust-Tier semantics (F-SEC1 Layer 2, domains/security/PROTOCOL.md):
#   T1: parent to child (trusted, no review needed)
#   T2: child to parent (verify: check belief diff before accepting)
#   T3: sibling to sibling (advisory only, logged not integrated)
TYPE_PATTERN = re.compile(r"Type:\s*([a-zA-Z][a-zA-Z0-9-]*)")
HELP_REQUEST_PATTERN = re.compile(
    r"# Bulletin from:\s*(.+?)\nDate:\s*(\S+)\nType:\s*help-request(?:\nTrust-Tier:\s*\S+)?\n\n## Content\n"
    r"Request-ID:\s*(\S+)\nNeed:\s*(.+?)(?:\n---|\Z)",
    re.DOTALL,
)
HELP_RESPONSE_PATTERN = re.compile(
    r"# Bulletin from:\s*(.+?)\nDate:\s*(\S+)\nType:\s*help-response(?:\nTrust-Tier:\s*\S+)?\n\n## Content\n"
    r"Request-ID:\s*(\S+)\nResponse:\s*(.+?)(?:\n---|\Z)",
    re.DOTALL,
)
FRONTIER_QUERY_PATTERN = re.compile(
    r"# Bulletin from:\s*(.+?)\nDate:\s*(\S+)\nType:\s*frontier-query(?:\nTrust-Tier:\s*\S+)?\n\n## Content\n"
    r"Query-ID:\s*(\S+)\nScope:\s*(.+?)(?:\n---|\Z)",
    re.DOTALL,
)
FRONTIER_RESPONSE_PATTERN = re.compile(
    r"# Bulletin from:\s*(.+?)\nDate:\s*(\S+)\nType:\s*frontier-response(?:\nTrust-Tier:\s*\S+)?\n\n## Content\n"
    r"Query-ID:\s*(\S+)\nFrontiers:\s*(.+?)(?:\n---|\Z)",
    re.DOTALL,
)
LANE_ANNOUNCE_PATTERN = re.compile(
    r"# Bulletin from:\s*([^\n]+?)\nDate:\s*(\S+)\nType:\s*lane-announce(?:\nTrust-Tier:\s*\S+)?\n\n## Content\n"
    r"Lane-ID:\s*(\S+)\nFrontier:\s*(\S+)\nScope:\s*([^\n]+?)\nStatus:\s*(\S+)",
)
LANE_CHECK_PATTERN = re.compile(
    r"# Bulletin from:\s*([^\n]+?)\nDate:\s*(\S+)\nType:\s*lane-check(?:\nTrust-Tier:\s*\S+)?\n\n## Content\n"
    r"Check-ID:\s*(\S+)\nFrontier:\s*(\S+)",
)


def _append_with_lock(path: Path, entry: str, timeout_s: float = 10.0):
    """Append text with a simple cross-process lock file."""
    lock_path = path.with_name(path.name + ".lock")
    start = time.monotonic()

    while True:
        try:
            # O_EXCL provides cross-process mutual exclusion on lock creation.
            lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(lock_fd, str(os.getpid()).encode("utf-8"))
            os.close(lock_fd)
            break
        except FileExistsError:
            # Recover from stale locks left by crashed writers.
            try:
                if time.time() - lock_path.stat().st_mtime > 30:
                    lock_path.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() - start > timeout_s:
                raise TimeoutError(f"Lock timeout for {path}")
            time.sleep(0.01)

    try:
        with open(path, "a", encoding="utf-8", newline="") as f:
            f.write(entry)
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def write_genesis_feedback(swarm_name: str, feedback: str):
    """Write a genesis-feedback bulletin. feedback: 'used:atom1,atom2 ignored:atom3'"""
    BULLETINS_DIR.mkdir(parents=True, exist_ok=True)
    bulletin_file = BULLETINS_DIR / f"{swarm_name}.md"

    entry = (
        f"\n---\n"
        f"# Genesis Feedback from: {swarm_name}\n"
        f"Date: {date.today()}\n"
        f"Type: genesis-feedback\n"
        f"Trust-Tier: T2\n\n"
        f"## F107 Atom Usage\n"
        f"{feedback}\n"
    )

    _append_with_lock(bulletin_file, entry)

    print(f"Genesis feedback written to {bulletin_file}")


def genesis_report():
    """Aggregate genesis-feedback bulletins to find least-used atoms."""
    if not BULLETINS_DIR.exists():
        print("No bulletins directory found.")
        return

    used_counts: dict[str, int] = {}
    ignored_counts: dict[str, int] = {}
    reporters = []

    for f in sorted(BULLETINS_DIR.glob("*.md")):
        text = f.read_text()
        for m in re.finditer(r"Type:\s*genesis-feedback\n\n## F107 Atom Usage\n(.+?)(?:\n---|\Z)", text, re.DOTALL):
            reporters.append(f.stem)
            feedback = m.group(1)
            used_m = re.search(r"used:([\w,:-]+)", feedback)
            ignored_m = re.search(r"ignored:([\w,:-]+)", feedback)
            if used_m:
                for atom in used_m.group(1).split(","):
                    atom = atom.strip()
                    if atom:
                        used_counts[atom] = used_counts.get(atom, 0) + 1
            if ignored_m:
                for atom in ignored_m.group(1).split(","):
                    atom = atom.strip()
                    if atom:
                        ignored_counts[atom] = ignored_counts.get(atom, 0) + 1

    print("=== GENESIS ATOM USAGE REPORT (F107) ===")
    print(f"Reporters: {len(reporters)} ({', '.join(sorted(set(reporters)))})\n")
    if not used_counts and not ignored_counts:
        print("No genesis-feedback bulletins yet.")
        return

    all_atoms = sorted(set(list(used_counts.keys()) + list(ignored_counts.keys())))
    print(f"{'Atom':<35} {'Used':>6} {'Ignored':>8}  {'Verdict'}")
    print("-" * 65)
    for atom in all_atoms:
        u = used_counts.get(atom, 0)
        i = ignored_counts.get(atom, 0)
        verdict = "ABLATION CANDIDATE" if i > u else "load-bearing" if u > 0 else "?"
        print(f"{atom:<35} {u:>6} {i:>8}  {verdict}")


def write_bulletin(swarm_name: str, bulletin_type: str, message: str, tier: str = "T3"):
    """Append a bulletin to a swarm's bulletin file.

    tier: Trust-Tier (T1/T2/T3). Default T3 (advisory only, most restrictive).
    """
    if bulletin_type not in VALID_TYPES:
        print(f"Invalid type: {bulletin_type}. Use: {sorted(VALID_TYPES)}")
        sys.exit(1)
    if tier not in VALID_TIERS:
        print(f"Invalid tier: {tier}. Use: {sorted(VALID_TIERS)}")
        sys.exit(1)

    BULLETINS_DIR.mkdir(parents=True, exist_ok=True)
    bulletin_file = BULLETINS_DIR / f"{swarm_name}.md"

    entry = (
        f"\n---\n"
        f"# Bulletin from: {swarm_name}\n"
        f"Date: {date.today()}\n"
        f"Type: {bulletin_type}\n"
        f"Trust-Tier: {tier}\n\n"
        f"## Content\n"
        f"{message}\n"
    )

    _append_with_lock(bulletin_file, entry)

    print(f"Bulletin written to {bulletin_file} (Trust-Tier: {tier})")


def _new_request_id(swarm_name: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", swarm_name.lower()).strip("-") or "swarm"
    return f"H-{stamp}-{slug[:12]}"


def write_help_request(swarm_name: str, need: str):
    """Write a structured help-request bulletin with a generated request id."""
    request_id = _new_request_id(swarm_name)
    message = f"Request-ID: {request_id}\nNeed: {need}"
    write_bulletin(swarm_name, "help-request", message, tier="T2")
    print(f"Help request id: {request_id}")


def write_help_response(swarm_name: str, request_id: str, response: str):
    """Write a structured help-response bulletin linked to a request id."""
    message = f"Request-ID: {request_id}\nResponse: {response}"
    write_bulletin(swarm_name, "help-response", message, tier="T3")
    print(f"Linked response to request id: {request_id}")


def help_queue():
    """List open help requests and responders."""
    if not BULLETINS_DIR.exists():
        print("No bulletins directory found.")
        return

    requests: dict[str, dict[str, str]] = {}
    responses: dict[str, list[str]] = {}

    for f in sorted(BULLETINS_DIR.glob("*.md")):
        text = f.read_text()
        for m in HELP_REQUEST_PATTERN.finditer(text):
            requester, req_date, request_id, need = m.groups()
            requests[request_id] = {
                "requester": requester.strip(),
                "date": req_date,
                "need": " ".join(need.strip().split()),
            }
        for m in HELP_RESPONSE_PATTERN.finditer(text):
            responder, _, request_id, _ = m.groups()
            responses.setdefault(request_id, [])
            responses[request_id].append(responder.strip())

    if not requests:
        print("No help requests found.")
        return

    open_ids = [rid for rid in sorted(requests) if rid not in responses]
    print("=== HELP QUEUE ===")
    print(f"Requests: {len(requests)}")
    print(f"Responded: {len(responses)}")
    print(f"Open: {len(open_ids)}")
    print()

    if not open_ids:
        print("No open help requests.")
        return

    print("Open requests:")
    for rid in open_ids:
        req = requests[rid]
        print(f"- {rid} | from {req['requester']} ({req['date']}): {req['need']}")


def _new_query_id(swarm_name: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", swarm_name.lower()).strip("-") or "swarm"
    return f"FQ-{stamp}-{slug[:12]}"


def _extract_active_frontiers() -> list[str]:
    """Read local FRONTIER.md and extract active (non-resolved) frontier IDs + one-line summaries."""
    frontier_path = REPO_ROOT / "tasks" / "FRONTIER.md"
    if not frontier_path.exists():
        return []

    text = frontier_path.read_text()
    # Stop at ## Resolved section if present
    resolved_idx = text.find("\n## Resolved")
    if resolved_idx > 0:
        text = text[:resolved_idx]

    frontiers = []
    # Match non-struck-through frontier entries (skip ~~**F-xxx**~~ which are resolved/moved)
    for m in re.finditer(
        r"^- \*\*(\S+)\*\*:\s*(.+?)$", text, re.MULTILINE
    ):
        fid = m.group(1)
        summary = m.group(2).strip()[:120]
        frontiers.append(f"{fid}: {summary}")

    return frontiers


def write_frontier_query(swarm_name: str, scope: str = "all"):
    """Post a frontier-query bulletin requesting a peer's active frontiers."""
    query_id = _new_query_id(swarm_name)
    message = f"Query-ID: {query_id}\nScope: {scope}"
    write_bulletin(swarm_name, "frontier-query", message, tier="T3")
    print(f"Frontier query id: {query_id}")
    return query_id


def write_frontier_response(swarm_name: str, query_id: str):
    """Read local frontiers and post as response to a frontier-query."""
    frontiers = _extract_active_frontiers()
    if not frontiers:
        summary = "(no active frontiers)"
    else:
        summary = "\n".join(f"  - {f}" for f in frontiers)

    message = f"Query-ID: {query_id}\nFrontiers:\n{summary}"
    write_bulletin(swarm_name, "frontier-response", message, tier="T3")
    print(f"Responded to {query_id} with {len(frontiers)} active frontiers")


def frontier_inbox():
    """List unanswered frontier queries across all bulletins."""
    if not BULLETINS_DIR.exists():
        print("No bulletins directory found.")
        return

    queries: dict[str, dict[str, str]] = {}
    responses: dict[str, list[str]] = {}

    for f in sorted(BULLETINS_DIR.glob("*.md")):
        text = f.read_text()
        for m in FRONTIER_QUERY_PATTERN.finditer(text):
            requester, req_date, query_id, scope = m.groups()
            queries[query_id] = {
                "requester": requester.strip(),
                "date": req_date,
                "scope": scope.strip(),
            }
        for m in FRONTIER_RESPONSE_PATTERN.finditer(text):
            responder, _, query_id, _ = m.groups()
            responses.setdefault(query_id, [])
            responses[query_id].append(responder.strip())

    print("=== FRONTIER QUERY INBOX ===")
    print(f"Queries: {len(queries)} | Responded: {len(responses)}")

    open_ids = [qid for qid in sorted(queries) if qid not in responses]
    if not open_ids:
        print("No unanswered frontier queries.")
        return

    print(f"\nUnanswered ({len(open_ids)}):")
    for qid in open_ids:
        q = queries[qid]
        print(f"  {qid} | from {q['requester']} ({q['date']}) scope={q['scope']}")
    print(f"\nRespond: python3 tools/bulletin.py frontier-respond <your-name> <query-id>")


def write_lane_announce(swarm_name: str, lane_id: str, frontier: str,
                        scope: str = "n/a", status: str = "ACTIVE"):
    """Announce a lane to peers (GAP-3 shared work coordination, L-1328)."""
    message = f"Lane-ID: {lane_id}\nFrontier: {frontier}\nScope: {scope}\nStatus: {status}"
    write_bulletin(swarm_name, "lane-announce", message, tier="T3")
    print(f"Lane announced: {lane_id} on {frontier} [{status}]")


def write_lane_check(swarm_name: str, frontier: str, intent: str = ""):
    """Check if any peer is working on a frontier (GAP-3)."""
    check_id = f"LC-{int(time.time())}-{swarm_name}"
    msg = f"Check-ID: {check_id}\nFrontier: {frontier}"
    if intent:
        msg += f"\nIntent: {intent}"
    write_bulletin(swarm_name, "lane-check", msg, tier="T3")
    # Immediately scan for existing lane-announce on this frontier
    conflicts = _scan_lane_conflicts(frontier)
    if conflicts:
        print(f"CONFLICT: {len(conflicts)} peer(s) already working on {frontier}:")
        for c in conflicts:
            print(f"  {c['swarm']} | {c['lane_id']} | {c['status']} ({c['date']})")
    else:
        print(f"No peer conflicts on {frontier}. Check-ID: {check_id}")
    return check_id


def _scan_lane_conflicts(frontier: str) -> list:
    """Scan bulletins for lane-announce entries matching a frontier.

    Cross-checks SWARM-LANES.md to filter out lanes that were MERGED/ABANDONED
    but still have stale ACTIVE bulletins (L-1553 process reflection).
    """
    if not BULLETINS_DIR.exists():
        return []

    # Read SWARM-LANES.md to know which lanes are actually closed
    closed_lanes = set()
    lanes_path = REPO_ROOT / "tasks" / "SWARM-LANES.md"
    if lanes_path.exists():
        import re as _re
        for line in lanes_path.read_text().split('\n'):
            if '| MERGED |' in line or '| ABANDONED |' in line:
                # Extract lane ID from table row
                cols = [c.strip() for c in line.split('|')]
                if len(cols) >= 3:
                    closed_lanes.add(cols[2])  # lane ID column

    conflicts = []
    for f in sorted(BULLETINS_DIR.glob("*.md")):
        text = f.read_text()
        for m in LANE_ANNOUNCE_PATTERN.finditer(text):
            swarm, dt, lane_id, fr, scope, status = m.groups()
            lane_id_stripped = lane_id.strip() if lane_id else ""
            if (fr.strip() == frontier
                    and status.strip() in ("ACTIVE", "CLAIMED")
                    and lane_id_stripped not in closed_lanes):
                conflicts.append({
                    "swarm": swarm.strip(), "lane_id": lane_id_stripped,
                    "frontier": fr.strip(), "scope": scope.strip(),
                    "status": status.strip(), "date": dt,
                })
    return conflicts


def lane_inbox():
    """List all lane announcements across peers (GAP-3)."""
    if not BULLETINS_DIR.exists():
        print("No bulletins directory found.")
        return
    announcements = []
    for f in sorted(BULLETINS_DIR.glob("*.md")):
        text = f.read_text()
        for m in LANE_ANNOUNCE_PATTERN.finditer(text):
            swarm, dt, lane_id, frontier, scope, status = m.groups()
            announcements.append({
                "swarm": swarm.strip(), "date": dt, "lane_id": lane_id,
                "frontier": frontier.strip(), "scope": scope.strip(),
                "status": status.strip(),
            })
    print(f"=== LANE COORDINATION INBOX (GAP-3) ===")
    print(f"Announcements: {len(announcements)}")
    active = [a for a in announcements if a["status"] in ("ACTIVE", "CLAIMED")]
    if active:
        print(f"\nActive ({len(active)}):")
        for a in active:
            print(f"  {a['lane_id']} | {a['frontier']} | {a['swarm']} ({a['date']}) scope={a['scope']}")
    else:
        print("No active peer lanes.")


def read_bulletins(swarm_name: str = None):
    """Read bulletins, optionally filtered by swarm name."""
    if not BULLETINS_DIR.exists():
        print("No bulletins directory found.")
        return

    files = (
        [BULLETINS_DIR / f"{swarm_name}.md"]
        if swarm_name
        else sorted(BULLETINS_DIR.glob("*.md"))
    )

    for f in files:
        if not f.exists():
            if swarm_name:
                print(f"No bulletins from {swarm_name}")
            continue
        print(f.read_text())


def scan_bulletins():
    """Scan all bulletins and produce a summary."""
    if not BULLETINS_DIR.exists():
        print("No bulletins directory found.")
        return

    files = sorted(BULLETINS_DIR.glob("*.md"))
    if not files:
        print("No bulletins found.")
        return

    stats = {"total": 0, "swarms": set(), "types": {}}

    for f in files:
        text = f.read_text()
        swarm_name = f.stem
        stats["swarms"].add(swarm_name)

        for m in TYPE_PATTERN.finditer(text):
            btype = m.group(1).lower()
            stats["total"] += 1
            stats["types"][btype] = stats["types"].get(btype, 0) + 1

    print("=== BULLETIN SCAN ===")
    print(f"Swarms reporting: {len(stats['swarms'])} ({', '.join(sorted(stats['swarms']))})")
    print(f"Total bulletins: {stats['total']}")
    for btype in sorted(stats["types"]):
        print(f"  {btype}: {stats['types'][btype]}")


def sync_to_child(child_name: str):
    """Copy parent bulletins into a child swarm for cross-swarm reading."""
    child_dir = CHILDREN_DIR / child_name
    if not child_dir.exists():
        print(f"Child '{child_name}' not found at {child_dir}")
        sys.exit(1)

    if not BULLETINS_DIR.exists():
        print("No bulletins to sync.")
        return

    # Create bulletins dir in child workspace
    child_bulletins = child_dir / "workspace" / "bulletins"
    child_bulletins.mkdir(parents=True, exist_ok=True)

    # Copy all bulletins EXCEPT the child's own
    copied = 0
    for f in sorted(BULLETINS_DIR.glob("*.md")):
        if f.stem == child_name:
            continue  # Don't copy own bulletins
        shutil.copy2(f, child_bulletins / f.name)
        copied += 1

    print(f"Synced {copied} bulletin file(s) to {child_bulletins}")
    print(f"Child '{child_name}' can now read sibling discoveries.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "write":
        if len(sys.argv) < 5:
            print("Usage: bulletin.py write <swarm-name> <type> <message> [--tier T1|T2|T3]")
            sys.exit(1)
        tier = "T3"
        remaining = sys.argv[4:]
        if "--tier" in remaining:
            idx = remaining.index("--tier")
            if idx + 1 < len(remaining):
                tier = remaining[idx + 1]
                remaining = remaining[:idx] + remaining[idx + 2:]
        write_bulletin(sys.argv[2], sys.argv[3], " ".join(remaining), tier=tier)

    elif cmd == "request-help":
        if len(sys.argv) < 4:
            print("Usage: bulletin.py request-help <swarm-name> <need>")
            sys.exit(1)
        write_help_request(sys.argv[2], " ".join(sys.argv[3:]))

    elif cmd == "offer-help":
        if len(sys.argv) < 5:
            print("Usage: bulletin.py offer-help <swarm-name> <request-id> <response>")
            sys.exit(1)
        write_help_response(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))

    elif cmd == "help-queue":
        help_queue()

    elif cmd == "frontier-query":
        if len(sys.argv) < 3:
            print("Usage: bulletin.py frontier-query <swarm-name> [scope]")
            sys.exit(1)
        scope = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "all"
        write_frontier_query(sys.argv[2], scope)

    elif cmd == "frontier-respond":
        if len(sys.argv) < 4:
            print("Usage: bulletin.py frontier-respond <swarm-name> <query-id>")
            sys.exit(1)
        write_frontier_response(sys.argv[2], sys.argv[3])

    elif cmd == "frontier-inbox":
        frontier_inbox()

    elif cmd == "lane-announce":
        if len(sys.argv) < 5:
            print("Usage: bulletin.py lane-announce <swarm-name> <lane-id> <frontier-id> [--scope ...] [--status ...]")
            sys.exit(1)
        scope, status = "n/a", "ACTIVE"
        remaining = sys.argv[5:]
        if "--scope" in remaining:
            idx = remaining.index("--scope")
            if idx + 1 < len(remaining):
                scope = remaining[idx + 1]
                remaining = remaining[:idx] + remaining[idx + 2:]
        if "--status" in remaining:
            idx = remaining.index("--status")
            if idx + 1 < len(remaining):
                status = remaining[idx + 1]
                remaining = remaining[:idx] + remaining[idx + 2:]
        write_lane_announce(sys.argv[2], sys.argv[3], sys.argv[4], scope, status)

    elif cmd == "lane-check":
        if len(sys.argv) < 4:
            print("Usage: bulletin.py lane-check <swarm-name> <frontier-id> [--intent ...]")
            sys.exit(1)
        intent = ""
        remaining = sys.argv[4:]
        if "--intent" in remaining:
            idx = remaining.index("--intent")
            if idx + 1 < len(remaining):
                intent = " ".join(remaining[idx + 1:])
        write_lane_check(sys.argv[2], sys.argv[3], intent)

    elif cmd == "lane-inbox":
        lane_inbox()

    elif cmd == "genesis-feedback":
        if len(sys.argv) < 4:
            print("Usage: bulletin.py genesis-feedback <swarm-name> <feedback>")
            print("  feedback: 'used:atom1,atom2 ignored:atom3,atom4'")
            sys.exit(1)
        write_genesis_feedback(sys.argv[2], " ".join(sys.argv[3:]))

    elif cmd == "genesis-report":
        genesis_report()

    elif cmd == "read":
        swarm_name = sys.argv[2] if len(sys.argv) > 2 else None
        read_bulletins(swarm_name)

    elif cmd == "scan":
        scan_bulletins()

    elif cmd == "sync":
        if len(sys.argv) < 3:
            print("Usage: bulletin.py sync <child-name>")
            sys.exit(1)
        sync_to_child(sys.argv[2])

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
