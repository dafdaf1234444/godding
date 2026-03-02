#!/usr/bin/env python3
"""Archive old MERGED/ABANDONED rows from tasks/SWARM-LANES.md.

Usage:
    python3 tools/lanes_compact.py [--age 20] [--session N] [--dry-run]

Defaults:
    --age 20        Archive rows whose session number is <= (current_session - age).
    --session N     Override current session (default: auto-detect from memory/INDEX.md).
    --dry-run       Print what would be archived without writing any files.

Row format (12 columns, 1-based after splitting on '|'):
    1=Date  2=Lane  3=Session  4=Agent  5=Branch  6=PR  7=Model
    8=Platform  9=Scope-Key  10=Etc  11=Status  12=Notes
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
LANES_PATH = REPO_ROOT / "tasks" / "SWARM-LANES.md"
ARCHIVE_PATH = REPO_ROOT / "tasks" / "SWARM-LANES-ARCHIVE.md"
INDEX_PATH = REPO_ROOT / "memory" / "INDEX.md"

ARCHIVE_HEADER = """\
# Swarm Lanes Archive
Compacted rows removed from `tasks/SWARM-LANES.md` to keep the active file lean.
Each batch is separated by a `<!-- compacted DATE session=N -->` comment.
"""

CLOSED_STATUSES = {"MERGED", "ABANDONED"}
ACTIVE_STATUSES = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}


def detect_current_session(index_path: Path) -> int:
    """Parse 'Sessions: N' from memory/INDEX.md and return N."""
    try:
        text = index_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SystemExit(f"ERROR: cannot read {index_path}: {exc}") from exc
    m = re.search(r"Sessions:\s*(\d+)", text)
    if not m:
        raise SystemExit(
            f"ERROR: could not find 'Sessions: N' in {index_path}. "
            "Use --session N to specify manually."
        )
    return int(m.group(1))


def parse_session_number(cell: str) -> int | None:
    """Extract integer N from a session cell like 'S186' or ' S186 '."""
    m = re.search(r"S(\d+)", cell.strip())
    if m:
        return int(m.group(1))
    return None


def parse_status(cell: str) -> str:
    """Return the trimmed status string from the Status column cell."""
    return cell.strip()


def split_row(line: str) -> list[str] | None:
    """Split a markdown table data row into cells (strips outer empty elements).

    Returns None if the line is not a data row (e.g. separator or header).
    """
    if not line.startswith("|"):
        return None
    parts = line.split("|")
    # parts[0] is empty (before first |), parts[-1] is empty (after last |)
    cells = parts[1:-1]
    # Separator rows look like | --- | --- | ...
    if all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells):
        return None
    return cells


def is_archivable(cells: list[str], current_session: int, age_threshold: int) -> bool:
    """Return True if this row should be archived.

    Criteria:
    - Status is MERGED or ABANDONED (closed), AND
    - Session number <= current_session - age_threshold
    """
    # Column indices are 1-based in spec; list is 0-based so subtract 1.
    # 3rd column (index 2) = Session, 11th column (index 10) = Status
    if len(cells) < 11:
        return False
    status = parse_status(cells[10])
    if status not in CLOSED_STATUSES:
        return False
    session_num = parse_session_number(cells[2])
    if session_num is None:
        return False
    cutoff = current_session - age_threshold
    return session_num <= cutoff


def compact(
    lanes_text: str,
    current_session: int,
    age_threshold: int,
) -> tuple[list[str], list[str], list[str]]:
    """Partition lines into header_lines, kept_rows, archived_rows.

    header_lines: everything up to and including the separator row (| --- | ... |)
    kept_rows: data rows that should remain in SWARM-LANES.md
    archived_rows: data rows that should move to the archive

    Returns (header_lines, kept_rows, archived_rows).
    """
    lines = lanes_text.splitlines(keepends=True)

    header_lines: list[str] = []
    kept_rows: list[str] = []
    archived_rows: list[str] = []

    separator_seen = False

    for line in lines:
        stripped = line.rstrip("\n").rstrip("\r")

        if not separator_seen:
            header_lines.append(line)
            # Detect the separator row (| --- | --- | ...)
            if stripped.startswith("|"):
                parts = stripped.split("|")
                cells = parts[1:-1]
                if cells and all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells):
                    separator_seen = True
            continue

        # After separator: classify each data row
        cells = split_row(stripped)
        if cells is None:
            # Blank lines, comments, or non-table lines: keep as-is
            kept_rows.append(line)
            continue

        if is_archivable(cells, current_session, age_threshold):
            archived_rows.append(line)
        else:
            kept_rows.append(line)

    return header_lines, kept_rows, archived_rows


def build_lanes_output(header_lines: list[str], kept_rows: list[str]) -> str:
    """Reassemble the kept SWARM-LANES.md content."""
    parts = header_lines + kept_rows
    result = "".join(parts)
    # Ensure file ends with a newline
    if result and not result.endswith("\n"):
        result += "\n"
    return result


def build_archive_append(
    archived_rows: list[str],
    current_session: int,
    today: str,
    archive_exists: bool,
) -> str:
    """Build the text to append to SWARM-LANES-ARCHIVE.md."""
    separator = f"<!-- compacted {today} session={current_session} -->\n"
    rows_text = "".join(archived_rows)
    if not archive_exists:
        return ARCHIVE_HEADER + "\n" + separator + rows_text
    return "\n" + separator + rows_text


def bloat_ratio(total: int, archivable: int) -> float:
    if total == 0:
        return 0.0
    return archivable / total


def count_data_rows(lines: list[str]) -> int:
    """Count non-header, non-separator markdown table rows."""
    count = 0
    separator_seen = False
    for line in lines:
        stripped = line.rstrip("\n").rstrip("\r")
        if not separator_seen:
            if stripped.startswith("|"):
                parts = stripped.split("|")
                cells = parts[1:-1]
                if cells and all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells):
                    separator_seen = True
            continue
        cells = split_row(stripped)
        if cells is not None:
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Archive old MERGED/ABANDONED rows from tasks/SWARM-LANES.md."
    )
    parser.add_argument(
        "--age",
        type=int,
        default=20,
        metavar="N",
        help="Archive rows with session <= (current_session - N). Default: 20.",
    )
    parser.add_argument(
        "--session",
        type=int,
        default=None,
        metavar="N",
        help="Override current session number (default: auto-detect from memory/INDEX.md).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report without writing any files.",
    )
    args = parser.parse_args(argv)

    # Resolve current session
    if args.session is not None:
        current_session = args.session
    else:
        current_session = detect_current_session(INDEX_PATH)

    age_threshold: int = args.age
    cutoff_session = current_session - age_threshold

    # Read SWARM-LANES.md
    try:
        lanes_text = LANES_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SystemExit(f"ERROR: cannot read {LANES_PATH}: {exc}") from exc

    # Partition rows
    header_lines, kept_rows, archived_rows = compact(
        lanes_text, current_session, age_threshold
    )

    # Compute stats
    all_data_lines = [line for line in (kept_rows + archived_rows) if split_row(line.rstrip("\n").rstrip("\r")) is not None]
    total_rows = len(all_data_lines)
    archivable_count = len([l for l in archived_rows if split_row(l.rstrip("\n").rstrip("\r")) is not None])
    remaining_count = total_rows - archivable_count
    before_ratio = bloat_ratio(total_rows, archivable_count)
    after_ratio = bloat_ratio(remaining_count, 0)  # after: nothing archivable remains

    print(f"lanes_compact: current_session=S{current_session}, age_threshold={age_threshold}, cutoff=S{cutoff_session}")
    print(f"  total rows:      {total_rows}")
    print(f"  archivable:      {archivable_count}")
    print(f"  remaining:       {remaining_count}")
    print(f"  bloat ratio (before): {before_ratio:.1%}  ({archivable_count}/{total_rows} rows are archive-eligible)")
    print(f"  bloat ratio (after):  {after_ratio:.1%}  (0 archive-eligible rows remain)")

    if archivable_count == 0:
        print("  nothing to archive.")
        return 0

    if args.dry_run:
        print("  dry-run: no files written.")
        print(f"  would archive {archivable_count} row(s) to {ARCHIVE_PATH}")
        return 0

    today = date.today().isoformat()
    archive_exists = ARCHIVE_PATH.exists()

    # Build updated SWARM-LANES.md
    lanes_output = build_lanes_output(header_lines, kept_rows)

    # Build archive append text
    archive_append = build_archive_append(
        archived_rows, current_session, today, archive_exists
    )

    # Write SWARM-LANES.md
    LANES_PATH.write_text(lanes_output, encoding="utf-8")
    print(f"  wrote {LANES_PATH}")

    # Write/append SWARM-LANES-ARCHIVE.md
    if archive_exists:
        with ARCHIVE_PATH.open("a", encoding="utf-8") as fh:
            fh.write(archive_append)
        print(f"  appended {archivable_count} row(s) to {ARCHIVE_PATH}")
    else:
        ARCHIVE_PATH.write_text(archive_append, encoding="utf-8")
        print(f"  created {ARCHIVE_PATH} with {archivable_count} row(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
