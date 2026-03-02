#!/usr/bin/env python3
"""
swarm_pr.py - Branch/PR intake planning for swarm execution.

Usage:
    python3 tools/swarm_pr.py plan <base-ref> <head-ref>
    python3 tools/swarm_pr.py plan <base-ref> <head-ref> --json
    python3 tools/swarm_pr.py enqueue <base-ref> <head-ref>
    python3 tools/swarm_pr.py queue

This tool turns a git diff range into a swarm execution plan:
- partitions changed files into lanes
- marks each lane as fanout-safe or coordination-heavy
- computes a stable diff fingerprint for de-dup
- optionally queues intake requests for repeated contributor traffic
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUEUE_PATH = REPO_ROOT / "tasks" / "PR-QUEUE.json"

BRIDGE_FILES = {
    "SWARM.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".cursorrules",
    ".windsurfrules",
    ".github/copilot-instructions.md",
}

LANE_META = {
    "core-state": {
        "topology": "cooperative-single-writer",
        "reason": "Hot shared state/protocol files; merge risk is high without coordination.",
    },
    "tooling": {
        "topology": "independent-fanout",
        "reason": "Code/tool edits are typically partitionable by file/module.",
    },
    "docs": {
        "topology": "independent-fanout",
        "reason": "Narrative docs can be parallelized then reconciled by one reviewer.",
    },
    "experiments": {
        "topology": "independent-fanout",
        "reason": "Experiment artifacts are usually append-style and lane-isolated.",
    },
    "workspace": {
        "topology": "independent-fanout",
        "reason": "Workspace sandboxes are isolated from core state.",
    },
    "domains": {
        "topology": "independent-fanout",
        "reason": "Domain subtrees can be delegated by domain.",
    },
    "other": {
        "topology": "cooperative-review",
        "reason": "Unclassified paths need explicit coordination before fanout.",
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_path(path: str) -> str:
    return (path or "").strip().replace("\\", "/")


def _git_diff_name_status(base_ref: str, head_ref: str) -> str:
    range_expr = f"{base_ref}...{head_ref}"
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-status", range_expr],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        error = (proc.stderr or proc.stdout).strip() or "git diff failed"
        raise RuntimeError(error)
    return proc.stdout


def parse_name_status(diff_text: str) -> list[dict]:
    changes: list[dict] = []
    for raw_line in (diff_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        fields = raw_line.split("\t")
        if not fields:
            continue

        raw_status = fields[0].strip()
        status = raw_status[:1] if raw_status else "?"
        item: dict[str, str] = {"status": status, "raw_status": raw_status}

        if status in {"R", "C"} and len(fields) >= 3:
            item["old_path"] = _normalize_path(fields[1])
            item["path"] = _normalize_path(fields[2])
        elif len(fields) >= 2:
            item["path"] = _normalize_path(fields[1])
        else:
            # Fallback for malformed rows. Keep data instead of dropping it.
            item["path"] = _normalize_path(fields[-1])

        changes.append(item)
    return changes


def lane_for_path(path: str) -> str:
    p = _normalize_path(path)
    if not p:
        return "other"

    if (
        p in BRIDGE_FILES
        or p.startswith("beliefs/")
        or p.startswith("memory/")
        or p.startswith("tasks/")
    ):
        return "core-state"
    if p.startswith("tools/"):
        return "tooling"
    if p == "README.md" or p.startswith("docs/"):
        return "docs"
    if p.startswith("experiments/"):
        return "experiments"
    if p.startswith("workspace/"):
        return "workspace"
    if p.startswith("domains/"):
        return "domains"
    return "other"


def _fingerprint(base_ref: str, head_ref: str, changes: list[dict]) -> str:
    stable_rows = []
    for c in changes:
        stable_rows.append(
            "|".join(
                [
                    c.get("status", "?"),
                    c.get("old_path", ""),
                    c.get("path", ""),
                ]
            )
        )
    payload = {
        "base": base_ref,
        "head": head_ref,
        "rows": sorted(stable_rows),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def build_plan(base_ref: str, head_ref: str, changes: list[dict]) -> dict:
    lane_map: dict[str, dict] = {}
    status_counts: dict[str, int] = {}

    for change in changes:
        status = change.get("status", "?")
        status_counts[status] = status_counts.get(status, 0) + 1

        lane = lane_for_path(change.get("path", ""))
        if lane not in lane_map:
            meta = LANE_META.get(lane, LANE_META["other"])
            lane_map[lane] = {
                "name": lane,
                "topology": meta["topology"],
                "reason": meta["reason"],
                "changes": [],
            }
        lane_map[lane]["changes"].append(change)

    lanes = [lane_map[name] for name in sorted(lane_map)]
    has_core_state = "core-state" in lane_map
    if has_core_state and len(lanes) > 1:
        mode = "hybrid"
    elif has_core_state:
        mode = "cooperative"
    else:
        mode = "fanout"

    summary = {
        "changed_files": len(changes),
        "status_counts": status_counts,
        "lane_count": len(lanes),
    }

    return {
        "created_at_utc": _utc_now(),
        "base_ref": base_ref,
        "head_ref": head_ref,
        "range": f"{base_ref}...{head_ref}",
        "mode": mode,
        "fingerprint": _fingerprint(base_ref, head_ref, changes),
        "summary": summary,
        "lanes": lanes,
    }


def analyze_range(base_ref: str, head_ref: str) -> dict:
    raw = _git_diff_name_status(base_ref, head_ref)
    changes = parse_name_status(raw)
    return build_plan(base_ref, head_ref, changes)


def _read_queue(path: Path) -> dict:
    if not path.exists():
        return {"schema": "swarm-pr-queue-v1", "items": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema": "swarm-pr-queue-v1", "items": []}
    if not isinstance(data, dict):
        return {"schema": "swarm-pr-queue-v1", "items": []}
    items = data.get("items")
    if not isinstance(items, list):
        data["items"] = []
    if not data.get("schema"):
        data["schema"] = "swarm-pr-queue-v1"
    return data


def _next_queue_id(items: list[dict]) -> str:
    max_n = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        raw_id = str(item.get("id", ""))
        if raw_id.startswith("PRQ-"):
            tail = raw_id[4:]
            if tail.isdigit():
                max_n = max(max_n, int(tail))
    return f"PRQ-{max_n + 1:03d}"


def enqueue_range(base_ref: str, head_ref: str, queue_path: Path) -> dict:
    plan = analyze_range(base_ref, head_ref)
    queue = _read_queue(queue_path)
    items = queue.get("items", [])

    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("status") != "open":
            continue
        if item.get("fingerprint") == plan["fingerprint"]:
            return {
                "enqueued": False,
                "duplicate_of": item.get("id"),
                "plan": plan,
                "queue_file": str(queue_path),
            }

    entry = {
        "id": _next_queue_id(items),
        "status": "open",
        "created_at_utc": _utc_now(),
        "base_ref": base_ref,
        "head_ref": head_ref,
        "range": plan["range"],
        "mode": plan["mode"],
        "fingerprint": plan["fingerprint"],
        "summary": plan["summary"],
    }
    items.append(entry)
    queue["items"] = items
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    return {
        "enqueued": True,
        "entry": entry,
        "plan": plan,
        "queue_file": str(queue_path),
    }


def print_plan(plan: dict):
    print("=== SWARM PR PLAN ===")
    print(f"Range: {plan['range']}")
    print(f"Mode:  {plan['mode']}")
    print(f"Diff fingerprint: {plan['fingerprint']}")
    print(
        "Changed files: "
        f"{plan['summary']['changed_files']} "
        f"(lanes={plan['summary']['lane_count']})"
    )
    if plan["summary"]["status_counts"]:
        counts = ", ".join(
            f"{k}={v}" for k, v in sorted(plan["summary"]["status_counts"].items())
        )
        print(f"Status counts: {counts}")
    print()

    for lane in plan["lanes"]:
        print(f"[{lane['name']}] {lane['topology']}")
        print(f"  Why: {lane['reason']}")
        for change in lane["changes"]:
            status = change.get("raw_status", change.get("status", "?"))
            path = change.get("path", "")
            old_path = change.get("old_path")
            if old_path:
                print(f"  - {status}: {old_path} -> {path}")
            else:
                print(f"  - {status}: {path}")
        print()

    print("Execution sketch:")
    print("  0. Claim lanes in `tasks/SWARM-LANES.md` (agent/branch/model/platform/scope/etc).")
    if plan["mode"] == "hybrid":
        print("  1. Assign one coordinator lane for core-state changes.")
        print("  2. Fan out independent lanes in parallel.")
        print("  3. Reconcile with `bash tools/check.sh --quick` before merge.")
    elif plan["mode"] == "cooperative":
        print("  1. Keep a single writer/coordinator for this change set.")
        print("  2. Use short commits with frequent rebase/pull.")
    else:
        print("  1. Fan out all lanes to parallel workers.")
        print("  2. Aggregate and run `bash tools/check.sh --quick`.")


def print_queue(queue_path: Path, as_json: bool):
    queue = _read_queue(queue_path)
    if as_json:
        print(json.dumps(queue, indent=2))
        return

    items = [i for i in queue.get("items", []) if isinstance(i, dict)]
    open_items = [i for i in items if i.get("status") == "open"]

    print("=== SWARM PR QUEUE ===")
    print(f"File: {queue_path}")
    print(f"Open items: {len(open_items)}")
    print()
    if not open_items:
        print("No open intake items.")
        return

    for item in open_items:
        sid = item.get("id", "?")
        rng = item.get("range", "?")
        mode = item.get("mode", "?")
        changed = item.get("summary", {}).get("changed_files", "?")
        print(f"- {sid}: {rng} | mode={mode} | changed_files={changed}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Branch/PR swarm intake planner")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_cmd = sub.add_parser("plan", help="Analyze a ref range and print swarm plan")
    plan_cmd.add_argument("base_ref")
    plan_cmd.add_argument("head_ref")
    plan_cmd.add_argument("--json", action="store_true", dest="as_json")

    enqueue_cmd = sub.add_parser("enqueue", help="Analyze and enqueue a ref range")
    enqueue_cmd.add_argument("base_ref")
    enqueue_cmd.add_argument("head_ref")
    enqueue_cmd.add_argument(
        "--queue-file",
        default=str(DEFAULT_QUEUE_PATH),
        help=f"Queue file path (default: {DEFAULT_QUEUE_PATH.as_posix()})",
    )
    enqueue_cmd.add_argument("--json", action="store_true", dest="as_json")

    queue_cmd = sub.add_parser("queue", help="Show intake queue")
    queue_cmd.add_argument(
        "--queue-file",
        default=str(DEFAULT_QUEUE_PATH),
        help=f"Queue file path (default: {DEFAULT_QUEUE_PATH.as_posix()})",
    )
    queue_cmd.add_argument("--json", action="store_true", dest="as_json")

    return parser


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    try:
        if args.command == "plan":
            plan = analyze_range(args.base_ref, args.head_ref)
            if args.as_json:
                print(json.dumps(plan, indent=2))
            else:
                print_plan(plan)
            return 0

        if args.command == "enqueue":
            queue_path = Path(args.queue_file)
            result = enqueue_range(args.base_ref, args.head_ref, queue_path)
            if args.as_json:
                print(json.dumps(result, indent=2))
                return 0
            if result.get("enqueued"):
                entry = result["entry"]
                print(
                    f"Queued {entry['id']} ({entry['range']}) "
                    f"mode={entry['mode']} in {result['queue_file']}"
                )
            else:
                print(
                    f"Duplicate intake detected: {result['duplicate_of']} "
                    f"(fingerprint {result['plan']['fingerprint']})"
                )
            return 0

        if args.command == "queue":
            print_queue(Path(args.queue_file), args.as_json)
            return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
