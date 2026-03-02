#!/usr/bin/env python3
"""
sync_state.py — Auto-sync swarm state counts and session headers.

Addresses the recurring "state-sync" commit pattern (~4% of all commits):
count drift in INDEX.md, FRONTIER.md, and NEXT.md is detected by maintenance
but never auto-fixed. This tool reads live counts and patches the headers.

Usage:
    python3 tools/sync_state.py           # show diff + apply
    python3 tools/sync_state.py --dry-run # show diff only
    python3 tools/sync_state.py --quiet   # apply, no output unless changed
"""

import hashlib
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
DRY = "--dry-run" in sys.argv
QUIET = "--quiet" in sys.argv

try:
    from swarm_parse import active_principle_ids, active_frontier_ids
except ImportError:
    def active_principle_ids(text):
        all_ids = {int(m.group(1)) for m in re.finditer(r"\bP-(\d+)\b", text)}
        sup = {int(m.group(1)) for m in re.finditer(r"\bP-(\d+)→", text)}
        for m in re.finditer(r"\(P-(\d+)\s+(?:merged|superseded|absorbed)\)", text, re.IGNORECASE):
            sup.add(int(m.group(1)))
        return all_ids, sup

    def active_frontier_ids(text):
        # Strip Archive section — closed frontiers don't count as active
        active_text = re.split(r"^## Archive", text, flags=re.MULTILINE)[0]
        # Numeric: F110, F119, etc.
        numeric = {int(m.group(1)) for m in re.finditer(r"^- \*\*F(\d+)\*\*:", active_text, re.MULTILINE)}
        # Named: F-COMP1, F-ISG1, F-SEC1, F-PERS1, etc.
        named = {m.group(1) for m in re.finditer(r"^- \*\*F(-[A-Z][-A-Z0-9]*\d+)\*\*:", active_text, re.MULTILINE)}
        return numeric | named


def _git(*args):
    r = subprocess.run(["git", "-C", str(ROOT)] + list(args),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


try:
    from swarm_io import session_number as _session_number
except ImportError:
    def _session_number() -> int:
        log = _git("log", "--pretty=format:%s", "-200")
        sessions = re.findall(r"\[S(\d+)\]", log)
        return max((int(s) for s in sessions), default=0)


def count_lessons() -> int:
    tracked = _git("ls-files", "memory/lessons/").splitlines()
    return sum(1 for f in tracked if re.match(r"memory/lessons/L-\d+\.md$", f))


def count_principles() -> int:
    text = (ROOT / "memory" / "PRINCIPLES.md").read_text(encoding="utf-8")
    all_ids, superseded = active_principle_ids(text)
    return len(all_ids - superseded)


def count_beliefs() -> int:
    text = (ROOT / "beliefs" / "DEPS.md").read_text(encoding="utf-8")
    # Format: "### B1: ..." or "### B-EVAL1: ..." headings
    ids = set(re.findall(r"^### B[-\w]+:", text, re.MULTILINE))
    return len(ids)


def count_frontiers() -> int:
    text = (ROOT / "tasks" / "FRONTIER.md").read_text(encoding="utf-8")
    return len(active_frontier_ids(text))


def patch_file(path: Path, old: str, new: str, label: str) -> bool:
    """Replace old with new in file. Return True if changed."""
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return False
    if not QUIET:
        print(f"  {label}: {old!r} → {new!r}")
    if not DRY:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def main():
    session = _session_number()
    lessons = count_lessons()
    principles = count_principles()
    beliefs = count_beliefs()
    frontiers = count_frontiers()
    today = date.today().isoformat()

    # Sanity guard: transient git issues (index lock, concurrent rebase) can return
    # implausibly small counts (0, 1, 2...). Read the current INDEX.md lesson count
    # and reject any new count that is <50% of the current — indicates transient error.
    # (L-232: originally guarded only 0; extended to ratio guard after "1 lesson" corruption)
    _index_text = (ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8")
    _m = re.search(r"\*\*(\d+) lessons\*\*", _index_text)
    _current_lessons = int(_m.group(1)) if _m else 0
    if lessons == 0 or (_current_lessons > 10 and lessons < _current_lessons * 0.5):
        print(f"sync_state: WARNING — lesson count {lessons} implausible (current: {_current_lessons}), skipping lesson-count patches")
        return

    if not QUIET:
        print(f"sync_state: S{session} | {lessons}L {principles}P {beliefs}B {frontiers}F | {today}")
        if DRY:
            print("(dry-run — no files written)")

    changed = []

    # --- INDEX.md ---
    index = ROOT / "memory" / "INDEX.md"
    text = index.read_text(encoding="utf-8")

    # Session header
    m = re.search(r"Updated: \d{4}-\d{2}-\d{2} \| Sessions: (\d+)", text)
    if m and int(m.group(1)) != session:
        old = m.group(0)
        new = f"Updated: {today} | Sessions: {session}"
        if patch_file(index, old, new, "INDEX session"):
            changed.append("INDEX session")

    # Lesson count
    m = re.search(r"\*\*(\d+) lessons\*\*", text)
    if m and int(m.group(1)) != lessons:
        old = m.group(0)
        new = f"**{lessons} lessons**"
        if patch_file(index, old, new, "INDEX lessons"):
            changed.append("INDEX lessons")

    # Principle count
    m = re.search(r"\*\*(\d+) principles\*\*", text)
    if m and int(m.group(1)) != principles:
        old = m.group(0)
        new = f"**{principles} principles**"
        if patch_file(index, old, new, "INDEX principles"):
            changed.append("INDEX principles")

    # Belief count
    m = re.search(r"\*\*(\d+) beliefs\*\*", text)
    if m and int(m.group(1)) != beliefs:
        old = m.group(0)
        new = f"**{beliefs} beliefs**"
        if patch_file(index, old, new, "INDEX beliefs"):
            changed.append("INDEX beliefs")

    # Frontier count
    m = re.search(r"\*\*(\d+) frontier questions\*\*", text)
    if m and int(m.group(1)) != frontiers:
        old = m.group(0)
        new = f"**{frontiers} frontier questions**"
        if patch_file(index, old, new, "INDEX frontiers"):
            changed.append("INDEX frontiers")

    # Themes line lesson count
    m = re.search(r"## Themes \((\d+) lessons\)", text)
    if m and int(m.group(1)) != lessons:
        old = m.group(0)
        new = f"## Themes ({lessons} lessons)"
        if patch_file(index, old, new, "INDEX themes count"):
            changed.append("INDEX themes")

    # core_md_hash (prevents recurring validator FAIL when CORE.md is updated without hash renewal)
    core_md = ROOT / "beliefs" / "CORE.md"
    if core_md.exists():
        current_hash = hashlib.sha256(core_md.read_bytes()).hexdigest()
        m_hash = re.search(r"(<!--\s*core_md_hash:\s*)([a-f0-9]{64})(\s*-->)", text)
        if m_hash and m_hash.group(2) != current_hash:
            old_tag = m_hash.group(0)
            new_tag = f"{m_hash.group(1)}{current_hash}{m_hash.group(3)}"
            if patch_file(index, old_tag, new_tag, "INDEX core_md_hash"):
                changed.append("INDEX core_md_hash")

    # --- FRONTIER.md ---
    frontier = ROOT / "tasks" / "FRONTIER.md"
    text = frontier.read_text(encoding="utf-8")
    m = re.search(r"(\d+) active \| Last updated: \d{4}-\d{2}-\d{2} S(\d+)", text)
    if m:
        if int(m.group(1)) != frontiers or int(m.group(2)) != session:
            old = m.group(0)
            new = f"{frontiers} active | Last updated: {today} S{session}"
            if patch_file(frontier, old, new, "FRONTIER header"):
                changed.append("FRONTIER header")

    # --- PRINCIPLES.md header ---
    principles_md = ROOT / "memory" / "PRINCIPLES.md"
    text = principles_md.read_text(encoding="utf-8")
    m = re.search(r"(\d+) live principles", text)
    if m and int(m.group(1)) != principles:
        old = m.group(0)
        new = f"{principles} live principles"
        if patch_file(principles_md, old, new, "PRINCIPLES header"):
            changed.append("PRINCIPLES header")

    # --- NEXT.md ---
    next_md = ROOT / "tasks" / "NEXT.md"
    text = next_md.read_text(encoding="utf-8")
    m = re.search(r"Updated: \d{4}-\d{2}-\d{2} S(\d+)", text)
    if m and int(m.group(1)) != session:
        old = m.group(0)
        new = f"Updated: {today} S{session}"
        if patch_file(next_md, old, new, "NEXT session"):
            changed.append("NEXT session")

    # Key state count line in NEXT.md (e.g. "208L 149P 14B 15F")
    m = re.search(r"(\d+)L (\d+)P (\d+)B (\d+)F\b", text)
    if m:
        l, p, b, f = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        if (l, p, b, f) != (lessons, principles, beliefs, frontiers):
            old = m.group(0)
            new = f"{lessons}L {principles}P {beliefs}B {frontiers}F"
            if patch_file(next_md, old, new, "NEXT counts"):
                changed.append("NEXT counts")

    # --- README.md snapshot ---
    readme_md = ROOT / "README.md"
    if readme_md.exists():
        rtext = readme_md.read_text(encoding="utf-8")
        # "N sessions later, this repo contains X lessons, Y principles, Z beliefs, W active knowledge domains, and M commits"
        m = re.search(r"(\d+) sessions later, this repo contains (\d+) lessons, (\d+) principles, (\d+) beliefs, (\d+) active knowledge domains, and ([\d,]+)\+? commits", rtext)
        if m:
            rs, rl, rp, rb, rd = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
            # Count commits
            try:
                commit_count = int(_git("rev-list", "--count", "HEAD"))
                commit_bucket = f"{(commit_count // 100) * 100:,}+"
            except Exception:
                commit_count = 0
                commit_bucket = m.group(6) + "+"
            needs_update = (rs != session or rl != lessons or rp != principles or rb != beliefs)
            if needs_update:
                old = m.group(0)
                new = f"{session} sessions later, this repo contains {lessons} lessons, {principles} principles, {beliefs} beliefs, {rd} active knowledge domains, and {commit_bucket} commits"
                if patch_file(readme_md, old, new, "README snapshot"):
                    changed.append("README snapshot")
            # "Session N builds on what session N-1 discovered, which built on N-2"
            m2 = re.search(r"Session (\d+) builds on what session (\d+) discovered, which built on (\d+)", rtext)
            if m2 and int(m2.group(1)) != session:
                old2 = m2.group(0)
                new2 = f"Session {session} builds on what session {session-1} discovered, which built on {session-2}"
                if patch_file(readme_md, old2, new2, "README session ref"):
                    changed.append("README session ref")

    # --- PAPER.md scale line ---
    paper_md = ROOT / "docs" / "PAPER.md"
    if paper_md.exists():
        text = paper_md.read_text(encoding="utf-8")
        m = re.search(r"(\d+) lessons, (\d+) principles", text)
        if m and (int(m.group(1)) != lessons or int(m.group(2)) != principles):
            old = m.group(0)
            new = f"{lessons} lessons, {principles} principles"
            if patch_file(paper_md, old, new, "PAPER scale"):
                changed.append("PAPER scale")

    if not changed:
        if not QUIET:
            print("  all counts in sync — no changes needed")
    elif not DRY:
        print(f"  patched: {', '.join(changed)}")

    # Update periodics.json state-sync entry so maintenance.py doesn't fire false DUE
    # every session (S412 meta-swarm reflection — fix target: tools/sync_state.py)
    if not DRY:
        periodics_path = ROOT / "tools" / "periodics.json"
        if periodics_path.exists():
            try:
                import json as _json
                pdata = _json.loads(periodics_path.read_text(encoding="utf-8"))
                for item in pdata.get("items", []):
                    if item.get("id") == "state-sync":
                        item["last_reviewed_session"] = session
                        item["last_session"] = f"S{session}"
                        break
                periodics_path.write_text(_json.dumps(pdata, indent=2) + "\n", encoding="utf-8")
            except Exception:
                pass  # non-fatal — periodics.json update is best-effort


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"sync_state: ABORTED — {e}")
        print("  (git lock contention or command failure; no files patched)")
        sys.exit(1)
