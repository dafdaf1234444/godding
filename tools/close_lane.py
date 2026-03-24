#!/usr/bin/env python3
"""close_lane.py — F-META: reduce friction in lane closure + EAD enforcement (L-785).

Appends a MERGED/ABANDONED row to tasks/SWARM-LANES.md for a given lane ID
and can optionally update the target FRONTIER.md when a lane resolves a
frontier.

EAD enforcement (PCI improvement): when closing as MERGED, requires
--actual and --diff arguments so the expect-act-diff loop is completed.
Use --skip-ead only when abandoning or when lane had no expect field.

By default, prior rows for the lane are removed (merge-on-close) to reduce
SWARM-LANES bloat (L-340, L-527). Use --no-merge to preserve all prior rows.

Usage:
  python3 tools/close_lane.py --lane DOMEX-BRN-S331 --status MERGED \\
      --actual "BRN3 at 60% operational" --diff "small: 60% vs expected 50-70%" \\
      --note "BRN3 baseline complete, Sharpe compaction confirmed (L-268)"
"""

import argparse
import sys
import re
from datetime import date, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LANES_FILE = REPO_ROOT / "tasks" / "SWARM-LANES.md"
LANES_ARCHIVE = REPO_ROOT / "tasks" / "SWARM-LANES-ARCHIVE.md"

VALID_STATUSES = {"MERGED", "ABANDONED", "SUPERSEDED"}

# Colony threshold: a frontier with this many waves qualifies as a colony
# and requires adversarial capstone before final closure (L-1210, L-1215, L-601).
COLONY_WAVE_THRESHOLD = 3


def check_colony_adversarial(lane_id: str) -> tuple[str, int, int, bool]:
    """Check if a frontier has colony-level history and whether adversarial review exists.

    Returns (frontier_id, wave_count, falsification_count, needs_capstone).
    L-1210: Self-assessment of self-improvement inflates ~2-3x.
    Colony TTL final session must be adversarial (mode=falsification).
    """
    # Extract frontier from the lane's Etc field
    latest = find_latest_lane_row(lane_id)
    if not latest:
        return "", 0, 0, False
    etc = latest[10] if len(latest) > 10 else ""
    frontier_match = re.search(r"frontier=(F-[A-Z0-9]+)", etc)
    if not frontier_match:
        return "", 0, 0, False
    frontier_id = frontier_match.group(1)

    # Count all waves and falsification waves for this frontier
    wave_count = 0
    falsification_count = 0
    for lanes_file in (LANES_FILE, LANES_ARCHIVE):
        if not lanes_file.exists():
            continue
        for line in lanes_file.read_text().splitlines():
            if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue
            row_etc = cols[10] if len(cols) > 10 else ""
            fid_match = re.search(r"frontier=(F-[A-Z0-9,/\s-]+?)(?:;|$)", row_etc)
            if not fid_match or frontier_id not in re.findall(r"F-[A-Z0-9]+", fid_match.group(1)):
                continue
            wave_count += 1
            if "mode=falsification" in row_etc:
                falsification_count += 1

    needs_capstone = wave_count >= COLONY_WAVE_THRESHOLD and falsification_count == 0
    return frontier_id, wave_count, falsification_count, needs_capstone


def find_latest_lane_row(lane_id: str) -> dict | None:
    """Return the most recent row for this lane from SWARM-LANES.md (or archive fallback)."""
    rows = []
    for path in [LANES_FILE, LANES_ARCHIVE]:
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                if not line.startswith("|"):
                    continue
                cols = [c.strip() for c in line.split("|")]
                if len(cols) < 13:
                    continue
                if cols[2] == lane_id:
                    rows.append(cols)
    return rows[-1] if rows else None


def count_prior_rows(lane_id: str) -> int:
    """Count existing rows for this lane in SWARM-LANES.md."""
    count = 0
    with open(LANES_FILE) as f:
        for line in f:
            if not line.startswith("|"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) >= 3 and cols[2] == lane_id:
                count += 1
    return count


def remove_prior_rows(lane_id: str) -> int:
    """Remove all existing rows for lane_id from SWARM-LANES.md. Returns count removed."""
    with open(LANES_FILE) as f:
        lines = f.readlines()
    kept = []
    removed = 0
    for line in lines:
        if line.startswith("|"):
            cols = [c.strip() for c in line.split("|")]
            if len(cols) >= 3 and cols[2] == lane_id:
                removed += 1
                continue
        kept.append(line)
    with open(LANES_FILE, "w") as f:
        f.writelines(kept)
    return removed


def append_closure_row(
    lane_id: str,
    status: str,
    note: str,
    session: str,
    author: str,
    model: str,
    merge: bool = True,
    actual: str = "",
    diff: str = "",
) -> None:
    today = date.today().isoformat()
    row = latest = find_latest_lane_row(lane_id)
    if row is None:
        print(f"WARNING: lane {lane_id} not found in SWARM-LANES.md — appending stub closure", file=sys.stderr)
        branch = "local"
        scope_key = ""
        tags = f"intent=closure, progress=closed"
    else:
        # Carry forward branch/scope from latest row
        branch = row[5] if len(row) > 5 else "local"
        scope_key = row[9] if len(row) > 9 else ""
        existing_etc = row[10] if len(row) > 10 else ""
        # Update actual and diff fields in Etc (replace TBD or append if missing)
        if actual:
            if "actual=TBD" in existing_etc:
                existing_etc = re.sub(r"actual=TBD", f"actual={actual}", existing_etc)
            elif "actual=" not in existing_etc:
                existing_etc = f"{existing_etc}; actual={actual}"
        if diff:
            if "diff=TBD" in existing_etc:
                existing_etc = re.sub(r"diff=TBD", f"diff={diff}", existing_etc)
            elif "diff=" not in existing_etc:
                existing_etc = f"{existing_etc}; diff={diff}"
        # Strip old next_step, add closed status
        existing_etc_clean = re.sub(r"next_step=[^\s,|]+", "", existing_etc).strip().strip(",")
        tags = f"{existing_etc_clean}, progress=closed, next_step=none".lstrip(", ")

    if merge:
        removed = remove_prior_rows(lane_id)
        if removed:
            print(f"Removed {removed} prior row(s) for {lane_id} (merge-on-close)")

    line = (
        f"| {today} | {lane_id} | {session} | {author} | {branch} | - | {model} | close_lane.py | "
        f"{scope_key} | {tags} | {status} | {note} |\n"
    )
    with open(LANES_FILE, "a") as f:
        f.write(line)
    display = LANES_FILE.relative_to(REPO_ROOT) if LANES_FILE.is_relative_to(REPO_ROOT) else LANES_FILE
    print(f"Appended {status} closure for {lane_id} to {display}")

    # GAP-3: announce closure to inter-swarm bulletin board (fixes stale ACTIVE entries)
    frontier_m = re.search(r"frontier=(F-[A-Z0-9-]+)", tags)
    if frontier_m:
        try:
            sys.path.insert(0, str(REPO_ROOT / "tools"))
            from bulletin import write_lane_announce
            write_lane_announce("swarm", lane_id, frontier_m.group(1), scope_key or "n/a", status)
        except Exception:
            pass  # bulletin.py unavailable — non-fatal


def _lane_tags(value: str) -> dict[str, str]:
    return {
        key.strip().lower(): val.strip()
        for key, val in re.findall(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*([^\s,;|]+)", value or "")
    }


def _extract_frontier_ids(value: str) -> list[str]:
    return re.findall(r"\bF(?:-[A-Z0-9-]*\d+|\d+)\b", value or "", re.IGNORECASE)


def _markdown_section_bounds(text: str, heading: str) -> tuple[int, int] | None:
    match = re.search(rf"^##\s*{heading}\b.*$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    start = match.end()
    tail = text[start:]
    next_heading = re.search(r"^##\s+\S", tail, re.MULTILINE)
    end = start + (next_heading.start() if next_heading else len(tail))
    return start, end


def _count_active_frontier_bullets(section: str) -> int:
    return len(re.findall(r"^\s*-\s*\*\*F(?:-[A-Z0-9-]*\d+|\d+)\*\*", section, re.MULTILINE | re.IGNORECASE))


def _count_resolved_rows(section: str) -> int:
    return len(re.findall(r"^\|\s*F(?:-[A-Z0-9-]*\d+|\d+)\s*\|", section, re.MULTILINE | re.IGNORECASE))


def _mark_frontier_resolved_line(line: str, frontier_id: str, session: str) -> str:
    if f"~~**{frontier_id}**~~" not in line:
        line = line.replace(f"**{frontier_id}**", f"~~**{frontier_id}**~~", 1)

    if "Moved to Resolved" in line or "RESOLVED" in line.upper():
        return line

    marker = f"Moved to Resolved ({session})."
    if ":" in line:
        head, tail = line.split(":", 1)
        return f"{head}: {marker} {tail.lstrip()}"
    return line.rstrip("\n") + f" {marker}\n"


def update_frontier_file(frontier_path: Path, frontier_id: str, session: str, answer: str, today: str | None = None) -> bool:
    today = today or date.today().isoformat()
    text = frontier_path.read_text(encoding="utf-8")

    active_bounds = _markdown_section_bounds(text, "Active")
    if active_bounds is None:
        raise ValueError(f"{frontier_path} has no ## Active section")
    active_start, active_end = active_bounds
    active_section = text[active_start:active_end]

    lines = active_section.splitlines(keepends=True)
    lead_line_found = False
    for idx, line in enumerate(lines):
        if not re.match(r"^\s*-\s*", line):
            continue
        if re.search(rf"\*\*{re.escape(frontier_id)}\*\*", line, re.IGNORECASE):
            lines[idx] = _mark_frontier_resolved_line(line, frontier_id, session)
            lead_line_found = True
            break
    if not lead_line_found:
        raise ValueError(f"{frontier_id} not found in ## Active section of {frontier_path}")

    active_section = "".join(lines)
    text = text[:active_start] + active_section + text[active_end:]

    resolved_bounds = _markdown_section_bounds(text, "Resolved")
    row = f"| {frontier_id} | {answer} | {session} | {today} |\n"
    table_header = "| ID | Answer | Session | Date |\n|----|--------|---------|------|\n"

    if resolved_bounds is None:
        addition = f"\n## Resolved\n{table_header}{row}"
        text = text.rstrip() + "\n" + addition
    else:
        resolved_start, resolved_end = resolved_bounds
        resolved_section = text[resolved_start:resolved_end]
        if not re.search(r"^\|\s*ID\s*\|", resolved_section, re.MULTILINE):
            resolved_section = "\n" + table_header + resolved_section.lstrip("\n")

        lines = resolved_section.splitlines(keepends=True)
        table_start = next((i for i, line in enumerate(lines) if line.startswith("| ID |")), None)
        if table_start is None:
            lines = [table_header, row]
        else:
            table_end = table_start + 2
            while table_end < len(lines) and lines[table_end].startswith("|"):
                table_end += 1

            replaced = False
            for idx in range(table_start + 2, table_end):
                if re.match(rf"^\|\s*{re.escape(frontier_id)}\s*\|", lines[idx], re.IGNORECASE):
                    lines[idx] = row
                    replaced = True
                    break
            if not replaced:
                lines.insert(table_end, row)
        resolved_section = "".join(lines)
        text = text[:resolved_start] + resolved_section + text[resolved_end:]

    active_bounds = _markdown_section_bounds(text, "Active")
    resolved_bounds = _markdown_section_bounds(text, "Resolved")
    active_count = _count_active_frontier_bullets(text[active_bounds[0]:active_bounds[1]]) if active_bounds else 0
    resolved_count = _count_resolved_rows(text[resolved_bounds[0]:resolved_bounds[1]]) if resolved_bounds else 0

    text = re.sub(r"Updated:\s*\d{4}-\d{2}-\d{2}\s+S\d+", f"Updated: {today} {session}", text, count=1)
    text = re.sub(r"(\bActive:\s*)\d+\b", rf"\g<1>{active_count}", text, count=1)
    if re.search(r"\bResolved:\s*\d+\b", text):
        text = re.sub(r"(\bResolved:\s*)\d+\b", rf"\g<1>{resolved_count}", text, count=1)

    frontier_path.write_text(text, encoding="utf-8")
    return True


def resolve_frontier_for_lane(
    lane_id: str,
    session: str,
    answer: str,
    frontier_id: str = "",
    frontier_file: str = "",
) -> Path:
    latest = find_latest_lane_row(lane_id)
    if latest is None:
        raise ValueError(f"lane {lane_id} not found")

    etc_field = latest[10] if len(latest) > 10 else ""
    tags = _lane_tags(etc_field)

    if frontier_id:
        resolved_frontier = frontier_id
    else:
        frontiers = _extract_frontier_ids(tags.get("frontier", ""))
        unique_frontiers = list(dict.fromkeys(frontiers))
        if len(unique_frontiers) != 1:
            raise ValueError(
                f"{lane_id} tracks {len(unique_frontiers)} frontiers; pass --frontier-id explicitly"
            )
        resolved_frontier = unique_frontiers[0]

    frontier_candidates = [frontier_file, tags.get("memory_target", ""), latest[9] if len(latest) > 9 else ""]
    resolved_path = None
    for candidate in frontier_candidates:
        candidate = (candidate or "").strip()
        if candidate.endswith("FRONTIER.md"):
            resolved_path = REPO_ROOT / candidate
            break

    if resolved_path is None or not resolved_path.exists():
        raise ValueError(f"could not infer a domain FRONTIER.md for {lane_id}; pass --frontier-file")

    update_frontier_file(resolved_path, resolved_frontier, session, answer)
    print(f"Updated frontier file: {resolved_path.relative_to(REPO_ROOT)} [{resolved_frontier}]")
    return resolved_path


def main():
    parser = argparse.ArgumentParser(description="Close a swarm lane with minimal friction.")
    parser.add_argument("--lane", required=True, help="Lane ID, e.g. L-S186-DOMEX-BRN")
    parser.add_argument("--status", default="MERGED", choices=sorted(VALID_STATUSES),
                        help="Closure status (default: MERGED)")
    parser.add_argument("--note", default="", help="Closure note / summary")
    # Dynamic session detection via swarm_io (fixes hardcoded S186 bug — L-488)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from swarm_io import session_number
        _default_session = f"S{session_number()}"
    except Exception:
        _default_session = "S000"
    parser.add_argument("--session", default=_default_session, help="Current session tag (auto-detected)")
    parser.add_argument("--author", default="claude-code", help="Author identifier")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Model used")
    parser.add_argument("--actual", default="", help="What actually happened (EAD: actual outcome)")
    parser.add_argument("--diff", default="", help="Diff between expected and actual (EAD: gap analysis)")
    parser.add_argument("--skip-ead", action="store_true",
                        help="Skip EAD enforcement (use for ABANDONED or lanes without expect)")
    parser.add_argument("--no-merge", action="store_true",
                        help="Disable merge-on-close: keep all prior rows (append-only mode)")
    parser.add_argument("--skip-adversarial-capstone", default="",
                        metavar="REASON",
                        help=(
                            "Override adversarial capstone block for colony closures (L-1210). "
                            "Required when closing a colony (≥3 waves) with no mode=falsification wave. "
                            "Example: --skip-adversarial-capstone 'adversarial review pending in successor lane'"
                        ))
    parser.add_argument("--resolve-frontier", action="store_true",
                        help=(
                            "When this lane resolves a frontier, update the matching domain FRONTIER.md "
                            "by marking the frontier non-active and syncing the Resolved table."
                        ))
    parser.add_argument("--frontier-id", default="",
                        help="Explicit frontier ID to resolve when the lane tracks multiple frontiers.")
    parser.add_argument("--frontier-file", default="",
                        help="Explicit domain FRONTIER.md path to update with --resolve-frontier.")
    parser.add_argument("--resolution-answer", default="",
                        help="Resolved-table answer text written when --resolve-frontier is used.")
    args = parser.parse_args()

    if args.resolve_frontier and args.status != "MERGED":
        print("ERROR: --resolve-frontier is only valid with --status MERGED.", file=sys.stderr)
        sys.exit(1)
    if args.resolve_frontier and not args.resolution_answer:
        print("ERROR: --resolve-frontier requires --resolution-answer.", file=sys.stderr)
        sys.exit(1)

    # EAD enforcement: ALL MERGED lanes must provide actual/diff (L-741, L-601)
    # Previous gate: only enforced if lane had expect= set. This allowed stub closures
    # and manually-created lanes to bypass EAD entirely, causing -32.7pp compliance drop.
    # Fix: require actual/diff for ALL MERGED closures regardless of expect presence.
    if args.status == "MERGED" and not args.skip_ead:
        missing = []
        if not args.actual:
            missing.append("--actual (what happened)")
        if not args.diff:
            missing.append("--diff (expected vs actual gap)")
        if missing:
            print(f"ERROR: MERGED lanes require {' and '.join(missing)} for EAD compliance.", file=sys.stderr)
            print("  Every MERGED lane must document its outcome. Use --skip-ead only for", file=sys.stderr)
            print("  ABANDONED lanes or lanes with no meaningful work.", file=sys.stderr)
            sys.exit(1)

        # Lesson-link check: warn if artifact JSON has no L- lesson reference (F-IS7, L-531)
        latest = find_latest_lane_row(args.lane)
        if args.status == "MERGED":
            etc_field = latest[10] if latest and len(latest) > 10 else ""
            artifact_match = re.search(r"artifact=([^\s,;|]+)", etc_field)
            if artifact_match:
                artifact_path = REPO_ROOT / artifact_match.group(1).strip()
                if artifact_path.suffix == ".json" and artifact_path.exists():
                    import json as _json
                    try:
                        artifact_text = artifact_path.read_text()
                        if not re.search(r'\bL-\d+\b', artifact_text):
                            print(f"NOTICE: artifact {artifact_match.group(1)} has no L- lesson reference.", file=sys.stderr)
                            print("  F-IS7: experiment→lesson loss is 72.9%. Link a lesson to close the loop.", file=sys.stderr)
                        # Outcome completeness check (L-984, SIG-49): experiment JSON must document actual outcome
                        actual_match = re.search(r'"actual"\s*:\s*"([^"]*)"', artifact_text)
                        has_outcome = bool(re.search(r'"actual"\s*:', artifact_text)) or bool(re.search(r'"outcome"\s*:', artifact_text))
                        is_tbd = actual_match and actual_match.group(1).strip() == "TBD"
                        if is_tbd:
                            # TBD = skeleton not filled — hard block (open_lane.py created it, author must fill it)
                            print(f"ERROR: artifact {artifact_match.group(1)} has actual=TBD (skeleton not filled).", file=sys.stderr)
                            print("  Fill in 'actual' field before merging (L-984: open_lane.py skeleton).", file=sys.stderr)
                            sys.exit(1)
                        elif not has_outcome:
                            # Legacy experiment without 'actual' — warn but don't block
                            print(f"NOTICE: artifact {artifact_match.group(1)} lacks 'actual' or 'outcome' field.", file=sys.stderr)
                            print("  L-984: 61% of experiments missing outcomes. Consider adding 'actual' for future sessions.", file=sys.stderr)
                    except Exception:
                        pass

        # Principle-extraction prompt: warn if MERGED lane has lessons but no P- reference (L-659, F-META2)
        # Level-aware: L1/L2 (measurement/replication) rarely yield principles; suppress noise (L-1041 meta)
        if args.status == "MERGED":
            closure_text = f"{args.note} {args.actual} {args.diff}"
            has_lesson = bool(re.search(r'\bL-\d+\b', closure_text))
            has_principle = bool(re.search(r'\bP-\d+\b', closure_text))
            lane_level_match = re.search(r'level=(L\d+)', etc_field)
            lane_level = lane_level_match.group(1) if lane_level_match else "L3"  # default to L3 if unknown
            is_low_level = lane_level in ("L1", "L2")
            if has_lesson and not has_principle and not is_low_level:
                print(f"NOTICE: lane produced lesson(s) but no principle reference.", file=sys.stderr)
                print("  L-659: lesson→principle rate declining (20.4%→16.5%). Consider:", file=sys.stderr)
                print("  - Does this lesson generalize beyond its specific context?", file=sys.stderr)
                print("  - Could it become a P-NNN in memory/PRINCIPLES.md?", file=sys.stderr)
                print("  - Add --note 'P-NNN extracted' or 'no principle: <reason>'", file=sys.stderr)

    # L-1210 adversarial capstone enforcement: colony closures require falsification review.
    # Self-assessment of self-improvement inflates ~2-3x (F-SWARMER1 measured 3/5, adversarial
    # found 1-1.5/5). Structural fix: any frontier with ≥3 waves (colony) must have at least
    # one mode=falsification wave before the colony can be MERGED. L-601: voluntary → structural.
    if args.status == "MERGED":
        frontier_id, wave_count, falsif_count, needs_capstone = check_colony_adversarial(args.lane)
        if needs_capstone:
            if args.skip_adversarial_capstone:
                print(
                    f"INFO: Adversarial capstone override: '{args.skip_adversarial_capstone}'. "
                    f"Colony {frontier_id} ({wave_count} waves, 0 falsification). "
                    f"L-1210: self-assessment inflates ~2-3x without adversarial review.",
                )
            else:
                print(
                    f"ERROR: Colony {frontier_id} has {wave_count} waves but 0 falsification lanes. "
                    f"L-1210: self-assessment inflates ~2-3x. Before closing this colony, either:\n"
                    f"  (1) Run a mode=falsification session for {frontier_id} (recommended), or\n"
                    f"  (2) --skip-adversarial-capstone 'reason' to override with justification.",
                    file=sys.stderr,
                )
                sys.exit(1)
        elif frontier_id and wave_count >= COLONY_WAVE_THRESHOLD:
            print(
                f"INFO: Colony {frontier_id} ({wave_count} waves, {falsif_count} falsification) — "
                f"adversarial capstone satisfied.",
            )

    # False-abandon guard for ABANDONED lanes (L-756, L-783, F-STR1)
    # At high concurrency, commit-by-proxy causes nodes to self-classify
    # as ABANDONED when their artifact was committed by another session.
    # 13.2% false-abandon rate at n=38 (S385-S393). Two detection signals:
    # (1) artifact file exists on disk, (2) actual= field is populated (not TBD).
    # Either signal alone is sufficient evidence of completed work.
    if args.status == "ABANDONED":
        latest = find_latest_lane_row(args.lane)
        if latest:
            etc_field = latest[10] if len(latest) > 10 else ""
            has_actual = bool(re.search(r'actual=(?!TBD)[^;|]+', etc_field))
            artifact_exists = False
            artifact_match = re.search(r"artifact=([^\s,;|]+)", etc_field)
            if artifact_match:
                artifact_path = REPO_ROOT / artifact_match.group(1).strip()
                artifact_exists = artifact_path.exists()

            if artifact_exists or has_actual:
                signals = []
                if artifact_exists:
                    signals.append(f"artifact '{artifact_match.group(1)}' EXISTS on disk")
                if has_actual:
                    signals.append("actual= field is populated (work was done)")
                print(f"WARNING: {'; '.join(signals)}.", file=sys.stderr)
                print("  This lane may have been completed by a concurrent session (commit-by-proxy, L-526).", file=sys.stderr)
                print("  Consider using --status MERGED instead of ABANDONED.", file=sys.stderr)
                if has_actual and artifact_exists:
                    print("  STRONG evidence: both signals present — almost certainly false-abandon.", file=sys.stderr)

    if not args.note:
        args.note = f"Lane closed via close_lane.py (no note provided)"

    # Concurrent-overwrite guard (L-525): check if lane already MERGED in HEAD.
    # If another session committed a MERGED closure before us, skip to prevent
    # the second session from silently overwriting the first session's EAD docs.
    try:
        import subprocess as _sp
        head_lanes = _sp.check_output(
            ["git", "show", "HEAD:tasks/SWARM-LANES.md"],
            cwd=str(REPO_ROOT), text=True, stderr=_sp.DEVNULL
        )
        # Pattern: | LANE_ID | ... | MERGED | ...
        already_merged = bool(re.search(
            r"\|\s*" + re.escape(args.lane) + r"\s*\|[^|]*\|\s*MERGED\s*\|",
            head_lanes
        ))
        if already_merged and args.status == "MERGED":
            print(f"NOTICE: {args.lane} is already MERGED in HEAD (concurrent session committed first).")
            print("  Skipping close to prevent EAD overwrite (L-525 concurrent-close guard).")
            print("  Your close_lane.py invocation was valid — the other session beat you to it.")
            return
    except Exception:
        pass  # git show failed (no HEAD, etc.) — proceed normally

    append_closure_row(
        lane_id=args.lane,
        status=args.status,
        note=args.note,
        session=args.session,
        author=args.author,
        model=args.model,
        merge=not args.no_merge,
        actual=args.actual,
        diff=args.diff,
    )

    if args.resolve_frontier:
        try:
            resolve_frontier_for_lane(
                lane_id=args.lane,
                session=args.session,
                answer=args.resolution_answer,
                frontier_id=args.frontier_id,
                frontier_file=args.frontier_file,
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

    # Federated convergence check (F-NK6, L-960): when a DOMEX domain lane closes as MERGED,
    # scan the domain's FRONTIER.md for FQs with "Global synthesis: F-XXXX" tags and surface
    # any global frontiers that could now be synthesized. L-601: tags alone decay; this gate
    # at closure time is the enforcement half of the domain-global linkage intervention.
    if args.status == "MERGED":
        _check_global_synthesis_links(args.lane)


def _check_global_synthesis_links(lane_id: str) -> None:
    """Surface global frontier synthesis opportunities at DOMEX domain lane closure (F-NK6, L-960)."""
    import re as _re
    domex_match = _re.match(r"DOMEX-([A-Z]+(?:-[A-Z]+)*)-S\d+", lane_id.upper())
    if not domex_match:
        return
    domain_abbrev = domex_match.group(1).lower()
    _abbrev_map = {
        "nk": "nk-complexity", "meta": "meta", "sec": "security", "exp": "expert-swarm",
        "cat": "catastrophic-risks", "brn": "brain", "evo": "evolution", "eco": "economy",
        "ai": "ai", "gov": "governance", "hs": "human-systems", "gt": "graph-theory",
        "ling": "linguistics", "crypto": "cryptocurrency", "cry": "cryptography",
        "eval": "evaluation", "comp": "competitions", "is": "information-science",
        "sp": "spawn-harvest", "ct": "control-theory", "ds": "distributed-systems",
        "phy": "physics", "his": "history", "far": "far-future", "cache": "caching",
    }
    domain_dir = _abbrev_map.get(domain_abbrev, domain_abbrev)
    frontier_path = REPO_ROOT / "domains" / domain_dir / "tasks" / "FRONTIER.md"
    global_frontier = REPO_ROOT / "tasks" / "FRONTIER.md"
    if not frontier_path.exists() or not global_frontier.exists():
        return
    global_ids = set(_re.findall(r'\*\*(F-[A-Z0-9]+)\*\*', global_frontier.read_text()))
    content_f = frontier_path.read_text()
    active_section = ""
    if "## Active" in content_f:
        active_section = content_f.split("## Active")[1]
        for cutoff in ["## Archived", "## Resolved"]:
            if cutoff in active_section:
                active_section = active_section.split(cutoff)[0]
    global_links = []
    for fq in set(_re.findall(r'\*\*(F-[A-Z0-9\-]+)\*\*', active_section)):
        fq_pat = _re.compile(rf'\*\*{_re.escape(fq)}\*\*.*?(?=\n- \*\*F-|\Z)', _re.DOTALL)
        m = fq_pat.search(active_section)
        if m:
            grefs = list(set(
                r for r in _re.findall(r'F-[A-Z][A-Z0-9]+', m.group(0))
                if r in global_ids and r != fq
            ))
            if grefs:
                global_links.append((fq, grefs))
    if global_links:
        print(f"\n=== GLOBAL SYNTHESIS CHECK (F-NK6 federated convergence, L-960) ===")
        print(f"Domain {domain_dir}: {len(global_links)} FQ(s) with global frontier links.")
        print("Before closing out, check if any global frontier can now be synthesized:")
        for fq, grefs in sorted(global_links):
            grefs_str = ", ".join(sorted(grefs))
            print(f"  {fq} -> global: {grefs_str}")
        print("Review tasks/FRONTIER.md and update if domain work closes them.")
        print("=================================================================\n")


if __name__ == "__main__":
    main()
