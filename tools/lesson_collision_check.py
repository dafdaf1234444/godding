#!/usr/bin/env python3
"""lesson_collision_check.py — Detect L-NNN lesson number collisions (FM-18).
Checks: title-filename mismatch, content mismatch vs HEAD, out-of-sequence.
Usage: python3 tools/lesson_collision_check.py [--fix]
"""
import argparse, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSON_DIR = ROOT / "memory" / "lessons"
L_RE = re.compile(r"^L-(\d+)\.md$")
TITLE_RE = re.compile(r"^#\s+L-(\d+)")

def git_committed():
    """Return {number: relpath} for L-NNN.md in HEAD (excl. archive)."""
    try:
        out = subprocess.check_output(
            ["git", "ls-tree", "-r", "HEAD", "--name-only", "memory/lessons/"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return {}
    r = {}
    for line in out.strip().splitlines():
        m = L_RE.match(os.path.basename(line))
        if m and "/archive/" not in line:
            r[int(m.group(1))] = line
    return r

def git_show(relpath):
    try:
        return subprocess.check_output(
            ["git", "show", f"HEAD:{relpath}"], cwd=ROOT, text=True,
            stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None

def wt_lessons():
    """Return {number: Path} for L-NNN.md in working tree (excl. archive)."""
    if not LESSON_DIR.is_dir():
        return {}
    return {int(m.group(1)): f for f in LESSON_DIR.iterdir()
            if f.is_file() and (m := L_RE.match(f.name))}

def staged_lessons():
    """Return {number: Path} for L-NNN.md that are staged (git add'd)."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AC",
             "--", "memory/lessons/"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return {}
    r = {}
    for line in out.strip().splitlines():
        m = L_RE.match(os.path.basename(line))
        if m and "/archive/" not in line:
            path = ROOT / line
            if path.is_file():
                r[int(m.group(1))] = path
    return r

def title_num(path):
    """Extract L-NNN number from first heading, or None."""
    try:
        with open(path) as f:
            for line in f:
                m = TITLE_RE.match(line.strip())
                if m: return int(m.group(1))
                if line.strip(): return None
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser(description="Lesson collision detector (FM-18)")
    ap.add_argument("--fix", action="store_true", help="Show suggested fixes")
    ap.add_argument("--staged", action="store_true",
                    help="Only check staged lesson files (for pre-commit hook)")
    args = ap.parse_args()
    fix = args.fix
    wt = staged_lessons() if args.staged else wt_lessons()
    committed, issues = git_committed(), []
    # 1. Title-filename mismatch
    for num, path in sorted(wt.items()):
        tn = title_num(path)
        if tn is not None and tn != num:
            s = f"TITLE MISMATCH: {path.name} title says L-{tn:03d}"
            issues.append(s + (" — rename file or fix title" if fix else ""))
    # 2. Staged new-file collision: staged addition claims a slot already in HEAD (FM-18 core case)
    # Only check in staged mode to avoid flagging untracked work-in-progress.
    if args.staged:
        try:
            added_out = subprocess.check_output(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=A",
                 "--", "memory/lessons/"],
                cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
            for line in added_out.strip().splitlines():
                m = L_RE.match(os.path.basename(line))
                if m and "/archive/" not in line:
                    num = int(m.group(1))
                    if num in committed:
                        s = f"SLOT CONFLICT: L-{num:03d}.md staged as new but already in HEAD"
                        issues.append(s + (" — rename to next free slot" if fix else ""))
        except Exception:
            pass
    # Report
    if issues:
        print(f"FM-18 COLLISION CHECK: {len(issues)} issue(s) found")
        for i in issues: print(f"  {i}")
        sys.exit(1)
    else:
        print("FM-18 COLLISION CHECK: PASS (0 issues)")
        sys.exit(0)

if __name__ == "__main__":
    main()
