#!/usr/bin/env python3
"""Renew the constitutional hash in INDEX.md after intentional CORE.md changes.

Usage:
  python3 tools/renew_identity.py          # update INDEX.md with new hash
  python3 tools/renew_identity.py --check  # verify only, don't update

Run this after deliberate changes to beliefs/CORE.md (identity shifts, principle additions).
The validator (validate_beliefs.py) will FAIL if CORE.md changes without this being re-run.

Design (F110-B3): CORE.md is the constitutional document. Any change to it should be
intentional and traceable. Accidental drift (e.g., whitespace, encoding) is caught early.
"""

import hashlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_MD = REPO_ROOT / "beliefs" / "CORE.md"
INDEX_MD = REPO_ROOT / "memory" / "INDEX.md"
HASH_PATTERN = re.compile(r"<!--\s*core_md_hash:\s*([a-f0-9]{64})\s*-->")


def compute_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    check_only = "--check" in sys.argv

    if not CORE_MD.exists():
        print(f"ERROR: {CORE_MD} not found")
        return 1

    current_hash = compute_hash(CORE_MD)
    index_text = INDEX_MD.read_text() if INDEX_MD.exists() else ""
    m = HASH_PATTERN.search(index_text)
    stored_hash = m.group(1) if m else None

    if stored_hash == current_hash:
        print(f"OK: CORE.md hash matches ({current_hash[:12]}...)")
        return 0

    if stored_hash:
        print(f"DRIFT: stored={stored_hash[:12]}...  current={current_hash[:12]}...")
    else:
        print(f"NEW: no hash stored, current={current_hash[:12]}...")

    if check_only:
        print("Run without --check to update INDEX.md.")
        return 1

    new_comment = f"<!-- core_md_hash: {current_hash} -->"
    if stored_hash:
        new_text = HASH_PATTERN.sub(new_comment, index_text)
    else:
        new_text = index_text.rstrip() + f"\n\n{new_comment}\n"

    INDEX_MD.write_text(new_text)
    print(f"UPDATED: INDEX.md now records {current_hash[:12]}...")
    print(f"Full hash: {current_hash}")
    print("Next: commit this change with '[SN] renew identity: CORE.md updated — <why>'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
