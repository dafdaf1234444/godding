#!/usr/bin/env python3
"""close_lane.py — F-META: reduce friction in lane closure + EAD enforcement.

Appends a MERGED/ABANDONED row to tasks/SWARM-LANES.md for a given lane ID
and optionally updates the target FRONTIER.md with a status note.

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
    args = parser.parse_args()

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
