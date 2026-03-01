#!/usr/bin/env python3
"""open_lane.py — F-META1: enforce evidence fields at lane creation.

Appends an ACTIVE row to tasks/SWARM-LANES.md for a new lane ID.
Requires --expect and --artifact to be specified at creation time,
addressing the F-META1 finding that evidence fields (22% compliance
at S328) must be embedded at lane open, not only at closure.

Usage:
  python3 tools/open_lane.py --lane DOMEX-BRN-S331 --session S331 \\
      --frontier F-BRN2 --focus domains/brain \\
      --intent "F-BRN2 predictive coding audit" \\
      --expect "pred-coding-50-70%-operational" \\
      --artifact "experiments/brain/f-brn2-audit-s331.json"
"""

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LANES_FILE = REPO_ROOT / "tasks" / "SWARM-LANES.md"


def lane_exists(lane_id: str) -> bool:
    with open(LANES_FILE) as f:
        for line in f:
            if not line.startswith("|"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) >= 3 and cols[2] == lane_id:
                return True
    return False


def append_open_row(
    lane_id: str,
    session: str,
    intent: str,
    expect: str,
    artifact: str,
    frontier: str,
    focus: str,
    check_mode: str,
    personality: str,
    scope_key: str,
    author: str,
    model: str,
    branch: str,
    domain: str,
    note: str,
) -> None:
    today = date.today().isoformat()

    # Build scope key from domain or explicit override
    if not scope_key and domain:
        scope_key = f"domains/{domain}/tasks/FRONTIER.md"
    elif not scope_key and focus.startswith("domains/"):
        scope_key = f"{focus}/tasks/FRONTIER.md" if not focus.endswith(".md") else focus

    # Determine domain_sync and memory_target
    if focus.startswith("domains/") or domain:
        domain_path = domain or focus.split("/")[1] if "/" in focus else focus
        memory_target = scope_key or f"domains/{domain_path}/tasks/FRONTIER.md"
        domain_fields = f"; domain_sync=queued; memory_target={memory_target}"
    else:
        domain_fields = ""

    # Build Etc column — L-703: stripped zero-information constant fields
    # (personality=domain-expert, available=yes, blocked=none, human_open_item=none
    #  carried 0 bits across 35+ rows; only include when non-default)
    etc_parts = [
        f"focus={focus}",
        f"intent={intent}",
        f"check_mode={check_mode}",
    ]
    if personality and personality != "domain-expert":
        etc_parts.append(f"personality={personality}")
    if frontier:
        etc_parts.append(f"frontier={frontier}")
    etc_parts += [
        f"expect={expect}",
        f"actual=TBD",
        f"diff=TBD",
        f"artifact={artifact}",
        f"progress=active",
    ]
    if domain_fields:
        etc_parts.append(domain_fields.lstrip("; "))

    etc = "; ".join(etc_parts)

    line = (
        f"| {today} | {lane_id} | {session} | {author} | {branch} | - | {model} | "
        f"claude-code+wsl | {scope_key} | {etc} | ACTIVE | {note} |\n"
    )
    with open(LANES_FILE, "a") as f:
        f.write(line)
    display = LANES_FILE.relative_to(REPO_ROOT) if LANES_FILE.is_relative_to(REPO_ROOT) else LANES_FILE
    print(f"Opened lane {lane_id} → {display} [ACTIVE]")
    print(f"  expect  : {expect}")
    print(f"  artifact: {artifact}")


def main():
    parser = argparse.ArgumentParser(
        description="Open a swarm lane with required evidence fields at creation time."
    )
    parser.add_argument("--lane", required=True, help="Lane ID, e.g. DOMEX-BRN-S331")
    parser.add_argument("--session", required=True, help="Current session tag, e.g. S331")
    parser.add_argument("--expect", required=True,
                        help="Predicted outcome before acting (required — F-META1 enforcement)")
    parser.add_argument("--artifact", required=True,
                        help="Path to experiment artifact to be produced (required — F-META1 enforcement)")
    parser.add_argument("--frontier", default="", help="Frontier ID(s) being advanced, e.g. F-BRN2")
    parser.add_argument("--intent", default="", help="Short intent label for Etc column")
    parser.add_argument("--focus", default="global", help="Scope focus, e.g. domains/brain (default: global)")
    parser.add_argument("--check-mode", default="objective",
                        choices=["objective", "historian", "verification", "coordination", "assumption"],
                        help="Check mode for this lane (default: objective)")
    parser.add_argument("--personality", default="domain-expert",
                        help="Agent personality profile (default: domain-expert)")
    parser.add_argument("--scope-key", default="", help="Override scope-key column (defaults to domain FRONTIER.md)")
    parser.add_argument("--domain", default="", help="Domain shortname for auto-filling domain fields")
    parser.add_argument("--note", default="",
                        help="Opening note for Notes column")
    parser.add_argument("--author", default="claude-code", help="Author identifier")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Model used")
    parser.add_argument("--branch", default="master", help="Branch (default: master)")
    parser.add_argument("--force", action="store_true",
                        help="Open lane even if lane ID already exists (not recommended)")
    args = parser.parse_args()

    if lane_exists(args.lane) and not args.force:
        print(f"ERROR: Lane {args.lane} already exists in SWARM-LANES.md.", file=sys.stderr)
        print("Use --force to open a duplicate row (not recommended).", file=sys.stderr)
        sys.exit(1)

    if not args.intent:
        args.intent = f"advance-{args.frontier}" if args.frontier else "swarm-work"
    if not args.note:
        args.note = f"Lane opened via open_lane.py. Frontier: {args.frontier or 'TBD'}."

    append_open_row(
        lane_id=args.lane,
        session=args.session,
        intent=args.intent,
        expect=args.expect,
        artifact=args.artifact,
        frontier=args.frontier,
        focus=args.focus,
        check_mode=args.check_mode,
        personality=args.personality,
        scope_key=args.scope_key,
        author=args.author,
        model=args.model,
        branch=args.branch,
        domain=args.domain,
        note=args.note,
    )


if __name__ == "__main__":
    main()
