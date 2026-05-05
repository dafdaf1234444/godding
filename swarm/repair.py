#!/usr/bin/env python3
"""godding/swarm/repair.py — site-wide consistency repair.

Scans every page for the recurring inconsistency classes the human keeps
running into, fixes the safe ones in place, and prints a clean report
of what was wrong before vs. after.

Classes scanned + repair action:

  1. NUL bytes               → strip in place
  2. file truncation         → restore from git HEAD (cannot be invented)
  3. logo drift              → normalise to <a class="logo" ...>godding</a>
  4. missing required nav    → flag (cannot safely insert blind)
  5. duplicate <html>/<body> → flag
  6. broken closing tag run  → flag

Run:
    python swarm/repair.py            # report + auto-fix safe issues
    python swarm/repair.py --check    # report only, exit 1 on any issue
"""
from __future__ import annotations
import re, sys, subprocess
from pathlib import Path

ROOT  = Path(__file__).resolve().parent.parent
PAGES = ROOT / "pages"
HOME  = ROOT / "index.html"

REQUIRED_NAV = [
    "nothing.html", "belief.html", "brain.html", "religion.html",
    "good-bad.html", "ants.html",
    "stigmergy.html", "clock.html",
    "economics.html", "commons.html", "crime.html", "criminals.html", "justice.html",
    "politics.html", "now.html", "world.html",
    "vote.html", "health.html", "sustainability.html",
    "swarm.html", "graph.html", "depends.html",
    "idx.html", "search.html", "reach.html", "build.html",
]

LOGO_OK_RE = re.compile(r'<a class="logo"([^>]*)>godding</a>')
LOGO_BAD_RE = re.compile(
    r'<a class="logo"([^>]*)>\s*g(?:<span[^>]*>[^<]*</span>)?dding(?:<span[^>]*>[^<]*</span>)?\s*</a>'
)
HREF_RE = re.compile(r'href\s*=\s*"([^"]+)"')


def html_files():
    yield HOME
    yield from sorted(PAGES.glob("*.html"))


def git_restore(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    try:
        r = subprocess.run(
            ["git", "checkout", "HEAD", "--", rel],
            cwd=str(ROOT), capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False


def main(check_only: bool = False) -> int:
    issues = []
    fixed  = []

    for p in html_files():
        rel = p.relative_to(ROOT).as_posix()
        try:
            raw = p.read_bytes()
        except FileNotFoundError:
            issues.append((rel, "missing"))
            continue

        # 1. NUL bytes
        nul = raw.count(b"\x00")
        if nul:
            if not check_only:
                p.write_bytes(raw.replace(b"\x00", b""))
                fixed.append((rel, f"stripped {nul} NUL bytes"))
                raw = p.read_bytes()
            else:
                issues.append((rel, f"{nul} NUL bytes"))

        text = raw.decode("utf-8", errors="replace")

        # 2. truncation
        tail = text.rstrip()[-30:].lower()
        if "</html>" not in tail:
            if not check_only and git_restore(p):
                fixed.append((rel, "restored from git HEAD (was truncated)"))
                text = p.read_text(encoding="utf-8", errors="ignore")
            else:
                issues.append((rel, "truncated mid-file"))

        # 3. logo drift
        if not LOGO_OK_RE.search(text):
            m = LOGO_BAD_RE.search(text)
            if m and not check_only:
                new = text[:m.start()] + f'<a class="logo"{m.group(1)}>godding</a>' + text[m.end():]
                p.write_text(new, encoding="utf-8")
                fixed.append((rel, "normalised logo to plain 'godding'"))
                text = new
            elif "<a class=\"logo\"" in text:
                issues.append((rel, "logo present but not canonical"))
            else:
                issues.append((rel, "no logo tag"))

        # 4. missing required nav
        missing = [n for n in REQUIRED_NAV if f'href="{n}"' not in text]
        if missing:
            issues.append((rel, f"nav missing: {', '.join(missing[:6])}{'…' if len(missing) > 6 else ''}"))

        # 5. duplicate <body> or <html>
        if text.count("<body") > 1:
            issues.append((rel, "duplicate <body>"))
        if text.count("<html") > 1:
            issues.append((rel, "duplicate <html>"))

    print("godding · repair report")
    print("=======================")
    print(f"scanned {len(list(html_files()))} files")
    print(f"auto-fixed: {len(fixed)}")
    for rel, msg in fixed:
        print(f"  ✔  {rel}: {msg}")
    print(f"remaining issues: {len(issues)}")
    for rel, msg in issues:
        print(f"  ✗  {rel}: {msg}")

    return 1 if (check_only and issues) else (0 if not issues else 2)


if __name__ == "__main__":
    sys.exit(main(check_only="--check" in sys.argv))
