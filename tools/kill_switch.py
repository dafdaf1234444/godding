#!/usr/bin/env python3
"""Manage swarm kill switch state.

Usage:
  python3 tools/kill_switch.py status
  python3 tools/kill_switch.py activate --reason "human kill" --requested-by "human" [--mode halt|shutdown-request]
  python3 tools/kill_switch.py deactivate --reason "resume" --requested-by "human"
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KILL_FILE = ROOT / "tasks" / "KILL-SWITCH.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nodes import NODE_HUMAN, VALID_NODE_TYPES  # noqa: E402


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_fields() -> dict[str, str]:
    if not KILL_FILE.exists():
        return {}
    fields: dict[str, str] = {}
    for line in KILL_FILE.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip()
    return fields


def _write_fields(*, status: str, mode: str, reason: str, requested_by: str) -> None:
    body = [
        "# Swarm Kill Switch",
        "",
        f"status: {status}",
        f"mode: {mode}",
        f"reason: {reason}",
        f"requested_by: {requested_by}",
        f"since: {_now_utc()}",
        "",
        "notes: When status is ACTIVE, maintenance emits URGENT and swarm nodes should halt.",
    ]
    KILL_FILE.write_text("\n".join(body) + "\n", encoding="utf-8")


def cmd_status() -> int:
    fields = _read_fields()
    if not fields:
        print("Kill switch file not found. Status: INACTIVE")
        return 0
    status = fields.get("status", "INACTIVE")
    mode = fields.get("mode", "halt")
    reason = fields.get("reason", "")
    requested_by = fields.get("requested_by", "")
    since = fields.get("since", "")
    print(f"status={status} mode={mode} requested_by={requested_by} since={since}")
    if reason:
        print(f"reason={reason}")
    return 0


def cmd_activate(args: argparse.Namespace) -> int:
    _write_fields(
        status="ACTIVE",
        mode=args.mode,
        reason=args.reason,
        requested_by=args.requested_by,
    )
    print(f"Kill switch ACTIVATED ({args.mode}).")
    return 0


def cmd_deactivate(args: argparse.Namespace) -> int:
    _write_fields(
        status="INACTIVE",
        mode="halt",
        reason=args.reason,
        requested_by=args.requested_by,
    )
    print("Kill switch DEACTIVATED.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Swarm kill switch manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show current kill switch status")

    a = sub.add_parser("activate", help="Activate kill switch")
    a.add_argument("--reason", required=True)
    a.add_argument("--requested-by", default=NODE_HUMAN,
                   help=f"Node type (default: {NODE_HUMAN}). Valid: {sorted(VALID_NODE_TYPES)}")
    a.add_argument("--mode", choices=("halt", "shutdown-request"), default="halt")

    d = sub.add_parser("deactivate", help="Deactivate kill switch")
    d.add_argument("--reason", required=True)
    d.add_argument("--requested-by", default=NODE_HUMAN,
                   help=f"Node type (default: {NODE_HUMAN}). Valid: {sorted(VALID_NODE_TYPES)}")

    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "activate":
        return cmd_activate(args)
    if args.cmd == "deactivate":
        return cmd_deactivate(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

