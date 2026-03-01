#!/usr/bin/env python3
"""swarm_signal.py — Structured inter-node signaling for the swarm.

Any node can post and read signals. Signals are structured messages stored
in tasks/SIGNALS.md. This generalizes the human-only HUMAN-QUEUE into a
universal node-to-node communication channel.

Usage:
    python3 tools/swarm_signal.py post <type> <content> [--source <node>] [--target <node>] [--priority <P>]
    python3 tools/swarm_signal.py read [--type <type>] [--target <node>] [--since <session>] [--status <status>]
    python3 tools/swarm_signal.py resolve <signal-id> <resolution>
    python3 tools/swarm_signal.py stats

Signal types:
    directive    — directional guidance (high impact)
    challenge    — contradiction of existing belief/pattern
    question     — request for information or decision
    correction   — fix to prior signal or action
    observation  — notable finding (no action required)
    handoff      — state transfer between nodes
    blocker      — something preventing progress
    request      — ask another node for help
    response     — answer to a prior signal

Priority: P0 (critical) > P1 (high) > P2 (normal) > P3 (low)
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from swarm_io import REPO_ROOT, read_text, session_number
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from swarm_io import REPO_ROOT, read_text, session_number

try:
    from nodes import VALID_SIGNAL_TARGETS, validate_node
except ImportError:
    from tools.nodes import VALID_SIGNAL_TARGETS, validate_node

SIGNALS_FILE = REPO_ROOT / "tasks" / "SIGNALS.md"

VALID_TYPES = {
    "directive", "challenge", "question", "correction",
    "observation", "handoff", "blocker", "request", "response",
}

VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_STATUSES = {"OPEN", "RESOLVED", "EXPIRED"}


def _ensure_signals_file():
    """Create SIGNALS.md with header if it doesn't exist."""
    if SIGNALS_FILE.exists():
        return
    SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SIGNALS_FILE.write_text(
        "# Swarm Signals\n"
        "Structured node-to-node communication. Any node can post; any node can read.\n"
        "Use `python3 tools/signal.py` to interact.\n\n"
        "| ID | Date | Session | Source | Target | Type | Priority | Content | Status | Resolution |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
        encoding="utf-8",
    )


def _next_signal_id():
    """Get next SIG-N id from existing signals."""
    text = read_text(SIGNALS_FILE)
    ids = re.findall(r"SIG-(\d+)", text)
    return max((int(i) for i in ids), default=0) + 1


def _parse_signals():
    """Parse signal rows from SIGNALS.md."""
    text = read_text(SIGNALS_FILE)
    signals = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("| SIG-"):
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 10:
            signals.append({
                "id": parts[0],
                "date": parts[1],
                "session": parts[2],
                "source": parts[3],
                "target": parts[4],
                "type": parts[5],
                "priority": parts[6],
                "content": parts[7],
                "status": parts[8],
                "resolution": parts[9],
            })
    return signals


def post_signal(sig_type, content, source="ai-session", target="broadcast", priority="P2"):
    """Post a new signal to SIGNALS.md."""
    if sig_type not in VALID_TYPES:
        print(f"ERROR: Invalid type '{sig_type}'. Valid: {sorted(VALID_TYPES)}")
        return False
    if priority not in VALID_PRIORITIES:
        print(f"ERROR: Invalid priority '{priority}'. Valid: {sorted(VALID_PRIORITIES)}")
        return False
    # Validate source/target against NODES.md node model (nodes.py, SIG-1)
    if not validate_node(source):
        print(f"WARN: Unknown source node '{source}' (valid: {sorted(VALID_SIGNAL_TARGETS)})")
    if not validate_node(target, allow_broadcast=True):
        print(f"WARN: Unknown target node '{target}' (valid: {sorted(VALID_SIGNAL_TARGETS)})")

    _ensure_signals_file()
    sid = f"SIG-{_next_signal_id()}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sn = f"S{session_number()}"

    # Escape pipes in content
    safe_content = content.replace("|", "\\|")

    row = f"| {sid} | {now} | {sn} | {source} | {target} | {sig_type} | {priority} | {safe_content} | OPEN | — |\n"

    with open(SIGNALS_FILE, "a", encoding="utf-8") as f:
        f.write(row)

    print(f"Posted {sid}: [{sig_type}] {source}→{target} ({priority}): {content}")
    return True


def read_signals(sig_type=None, target=None, since_session=None, status=None):
    """Read and filter signals."""
    _ensure_signals_file()
    signals = _parse_signals()

    if sig_type:
        signals = [s for s in signals if s["type"] == sig_type]
    if target:
        signals = [s for s in signals if s["target"] in (target, "broadcast")]
    if since_session:
        sn = int(since_session.lstrip("S"))
        signals = [s for s in signals if int(s["session"].lstrip("S")) >= sn]
    if status:
        signals = [s for s in signals if s["status"] == status]

    if not signals:
        print("No signals match filters.")
        return signals

    for s in signals:
        marker = "*" if s["status"] == "OPEN" else " "
        print(f"  {marker} {s['id']} [{s['type']}] {s['source']}→{s['target']} "
              f"({s['priority']}, {s['session']}): {s['content']}")
        if s["resolution"] and s["resolution"] != "—":
            print(f"    → {s['resolution']}")

    return signals


def resolve_signal(signal_id, resolution):
    """Mark a signal as resolved."""
    _ensure_signals_file()
    text = read_text(SIGNALS_FILE)

    pattern = re.compile(
        r"(\| " + re.escape(signal_id) + r" \|.*?\| )OPEN( \| )(—)( \|)"
    )
    match = pattern.search(text)
    if not match:
        print(f"ERROR: Signal {signal_id} not found or already resolved.")
        return False

    safe_res = resolution.replace("|", "\\|")
    new_text = pattern.sub(rf"\g<1>RESOLVED\g<2>{safe_res}\g<4>", text)
    SIGNALS_FILE.write_text(new_text, encoding="utf-8")
    print(f"Resolved {signal_id}: {resolution}")
    return True


def signal_stats():
    """Print signal statistics."""
    _ensure_signals_file()
    signals = _parse_signals()

    total = len(signals)
    open_count = sum(1 for s in signals if s["status"] == "OPEN")
    by_type = {}
    by_source = {}
    for s in signals:
        by_type[s["type"]] = by_type.get(s["type"], 0) + 1
        by_source[s["source"]] = by_source.get(s["source"], 0) + 1

    print(f"Signals: {total} total, {open_count} OPEN")
    if by_type:
        print("By type:", ", ".join(f"{k}={v}" for k, v in sorted(by_type.items())))
    if by_source:
        print("By source:", ", ".join(f"{k}={v}" for k, v in sorted(by_source.items())))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0]

    if cmd == "post":
        if len(args) < 3:
            print("Usage: signal.py post <type> <content> [--source S] [--target T] [--priority P]")
            return
        sig_type = args[1]
        content = args[2]
        kwargs = {}
        i = 3
        while i < len(args):
            if args[i] == "--source" and i + 1 < len(args):
                kwargs["source"] = args[i + 1]
                i += 2
            elif args[i] == "--target" and i + 1 < len(args):
                kwargs["target"] = args[i + 1]
                i += 2
            elif args[i] == "--priority" and i + 1 < len(args):
                kwargs["priority"] = args[i + 1]
                i += 2
            else:
                i += 1
        post_signal(sig_type, content, **kwargs)

    elif cmd == "read":
        kwargs = {}
        i = 1
        while i < len(args):
            if args[i] == "--type" and i + 1 < len(args):
                kwargs["sig_type"] = args[i + 1]
                i += 2
            elif args[i] == "--target" and i + 1 < len(args):
                kwargs["target"] = args[i + 1]
                i += 2
            elif args[i] == "--since" and i + 1 < len(args):
                kwargs["since_session"] = args[i + 1]
                i += 2
            elif args[i] == "--status" and i + 1 < len(args):
                kwargs["status"] = args[i + 1]
                i += 2
            else:
                i += 1
        read_signals(**kwargs)

    elif cmd == "resolve":
        if len(args) < 3:
            print("Usage: signal.py resolve <signal-id> <resolution>")
            return
        resolve_signal(args[1], args[2])

    elif cmd == "stats":
        signal_stats()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
