#!/usr/bin/env python3
"""Archive old session notes from tasks/NEXT.md to tasks/NEXT-ARCHIVE.md.

Usage: python3 tools/next_compact.py [--keep N] [--dry-run]
"""
import argparse, re, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NEXT_PATH = REPO_ROOT / "tasks" / "NEXT.md"
ARCHIVE_PATH = REPO_ROOT / "tasks" / "NEXT-ARCHIVE.md"
sys.path.insert(0, str(REPO_ROOT / "tools"))
from swarm_io import session_number  # noqa: E402

HEADER_RE = re.compile(r"^## S(\d+) session note", re.IGNORECASE)


def parse_sections(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Split NEXT.md into (first_line, [(session_num, block_text), ...])."""
    lines = text.splitlines(keepends=True)
    if not lines:
        return "", []
    first_line = lines[0]
    sections: list[tuple[int, str]] = []
    cur_s: int | None = None
    cur_lines: list[str] = []
    for line in lines[1:]:
        m = HEADER_RE.match(line)
        if m:
            if cur_s is not None:
                sections.append((cur_s, "".join(cur_lines)))
            cur_s, cur_lines = int(m.group(1)), [line]
        else:
            cur_lines.append(line)
    if cur_s is not None:
        sections.append((cur_s, "".join(cur_lines)))
    return first_line, sections


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Archive old NEXT.md session notes.")
    ap.add_argument("--keep", type=int, default=1, metavar="N",
                     help="Keep N most recent sessions (default: 1 = current only).")
    ap.add_argument("--dry-run", action="store_true",
                     help="Show what would be archived without writing files.")
    args = ap.parse_args(argv)

    current = session_number()
    if current == 0:
        print("ERROR: could not detect current session.", file=sys.stderr)
        return 1
    try:
        text = NEXT_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"ERROR: cannot read {NEXT_PATH}: {exc}", file=sys.stderr)
        return 1

    first_line, sections = parse_sections(text)
    cutoff = current - args.keep + 1  # sessions >= cutoff are kept
    keep = [(s, blk) for s, blk in sections if s >= cutoff]
    archive = [(s, blk) for s, blk in sections if s < cutoff]

    kl = sum(b.count("\n") for _, b in keep)
    al = sum(b.count("\n") for _, b in archive)
    ks = sorted({s for s, _ in keep}, reverse=True)
    as_ = sorted({s for s, _ in archive}, reverse=True)

    print(f"next_compact: current=S{current}, keep={args.keep}, cutoff=S{cutoff}")
    print(f"  kept:     {len(keep)} sections ({kl} lines) sessions={ks}")
    print(f"  archived: {len(archive)} sections ({al} lines) sessions={as_}")

    if not archive:
        print("  nothing to archive.")
        return 0
    if args.dry_run:
        print("  dry-run: no files written.")
        return 0

    # Build new NEXT.md: first_line + blank line + kept sections
    kept_text = first_line + "\n" + "".join(blk for _, blk in keep)
    if not kept_text.endswith("\n"):
        kept_text += "\n"

    # Prepend archived sections to NEXT-ARCHIVE.md (newer first)
    archive_text = "".join(blk for _, blk in archive)
    existing = ARCHIVE_PATH.read_text(encoding="utf-8", errors="replace") if ARCHIVE_PATH.exists() else ""
    new_archive = archive_text + existing

    NEXT_PATH.write_text(kept_text, encoding="utf-8")
    ARCHIVE_PATH.write_text(new_archive, encoding="utf-8")

    ns = len(kept_text.encode("utf-8"))
    ars = len(new_archive.encode("utf-8"))
    print(f"  wrote {NEXT_PATH.name} ({ns} bytes), {ARCHIVE_PATH.name} ({ars} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
