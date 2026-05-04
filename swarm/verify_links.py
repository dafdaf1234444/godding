#!/usr/bin/env python3
"""
verify every internal href / src / link target on the godding site actually
resolves to a file. exits non-zero if any link is broken.
"""
from __future__ import annotations
import re, sys
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent
HTML_FILES = sorted(ROOT.rglob("*.html"))

# capture href="..." and src="..." values
ATTR_RE = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"', re.IGNORECASE)

def is_internal(url: str) -> bool:
    p = urlparse(url)
    if p.scheme and p.scheme not in ("file",):    # http(s), mailto, javascript: → external
        return False
    return True

ok, broken = 0, []
for f in HTML_FILES:
    text = f.read_text(encoding="utf-8", errors="ignore")
    for raw in ATTR_RE.findall(text):
        url = raw.strip()
        if not url or url.startswith("#") or url.startswith("data:"):
            continue
        if not is_internal(url):
            continue
        # split off fragment / query
        target_path = unquote(urlparse(url).path)
        # resolve relative to current file's dir
        candidate = (f.parent / target_path).resolve()
        if candidate.is_file():
            ok += 1
        elif candidate.is_dir():
            # treat dir/ as dir/index.html
            if (candidate / "index.html").is_file():
                ok += 1
            else:
                broken.append((f.relative_to(ROOT), url, "dir-without-index"))
        else:
            broken.append((f.relative_to(ROOT), url, "missing"))

print(f"checked {len(HTML_FILES)} files, {ok} internal links resolved.")
if broken:
    print(f"BROKEN ({len(broken)}):")
    for src, url, why in broken:
        print(f"  {src} -> {url}  [{why}]")
    sys.exit(1)
print("all internal links OK.")
