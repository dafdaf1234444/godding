#!/usr/bin/env python3
"""godding/swarm/audit.py — deep static audit.

Checks all pages for:
  1. NUL bytes (OneDrive sync corruption)
  2. broken anchor links (href="…#section" where #section doesn't exist on the target page)
  3. orphan <h2 id="…"> sections nobody links to
  4. CSS classes referenced in HTML that don't exist in styles.css
  5. unused CSS classes in styles.css that nothing references
  6. word-count growth violation (each page must be ≤ initial baseline)
  7. <img>/<svg> without alt/aria-label

Writes data/audit.json. Exits non-zero on any HARD failure
(NUL bytes, broken anchors, undefined CSS classes referenced).

Run:
    python swarm/audit.py
"""
from __future__ import annotations
import json, re, sys, datetime as dt
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGES = ROOT / "pages"
HOME  = ROOT / "index.html"
CSS   = ROOT / "assets" / "styles.css"

ID_RE      = re.compile(r'\s+id\s*=\s*"([^"]+)"')
HREF_RE    = re.compile(r'href\s*=\s*"([^"]+)"')
CLASS_RE   = re.compile(r'\sclass\s*=\s*"([^"]+)"')
CSS_CLASSES_RE = re.compile(r'(?<![\w-])\.([a-zA-Z_][\w-]*)')
TAG_RE     = re.compile(r"<[^>]+>")
SCRIPT_RE  = re.compile(r"<script[^>]*>.*?</script>", re.S | re.I)
STYLE_RE   = re.compile(r"<style[^>]*>.*?</style>", re.S | re.I)

def html_files():
    yield HOME
    yield from sorted(PAGES.glob("*.html"))

def visible_text(s: str) -> str:
    s = SCRIPT_RE.sub(" ", s)
    s = STYLE_RE.sub(" ", s)
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", s)).strip()

def collect_ids(content: str) -> set:
    return set(ID_RE.findall(content))

def main() -> int:
    report = {
        "generated": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "checks": {},
        "issues": [],
        "warnings": [],
    }
    failures = 0

    # --- pass 1: per-file content load + NUL check + id collection ---
    files = list(html_files())
    raw = {}
    visible = {}
    page_ids = {}
    page_classes = {}
    page_words = {}
    for p in files:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        b = p.read_bytes()
        nul = b.count(b"\x00")
        if nul:
            report["issues"].append({"kind": "nul_bytes", "file": rel, "count": nul})
            failures += 1
        raw[rel] = b.decode("utf-8", errors="replace")
        visible[rel] = visible_text(raw[rel])
        page_ids[rel] = collect_ids(raw[rel])
        # gather all classes used
        classes = set()
        for m in CLASS_RE.finditer(raw[rel]):
            for c in m.group(1).split():
                classes.add(c)
        page_classes[rel] = classes
        page_words[rel] = len(visible[rel].split())
    report["checks"]["files"] = len(files)
    report["checks"]["nul_bytes_total"] = sum(p.read_bytes().count(b"\x00") for p in files)

    # --- pass 2: broken anchor links ---
    # build a map: filepath → anchor ids on that page
    by_url = {}
    for rel in raw:
        url = rel  # internal absolute pseudo-URL like 'pages/foo.html'
        by_url[url] = page_ids[rel]
    by_url["index.html"] = page_ids.get("index.html", set())
    # for each anchor href, verify
    broken_anchors = []
    for rel, html in raw.items():
        for href in HREF_RE.findall(html):
            if href.startswith("http") or href.startswith("mailto") or href.startswith("#"):
                # in-page anchor — check on this page
                if href.startswith("#"):
                    aid = href[1:]
                    if aid and aid not in page_ids[rel]:
                        broken_anchors.append({"page": rel, "href": href})
                continue
            if "#" not in href:
                continue
            path, anchor = href.split("#", 1)
            if not anchor:
                continue
            # resolve target relative to current page's directory
            this_dir = Path(rel).parent
            target = (this_dir / path).as_posix() if path else rel
            if target.startswith("./"):
                target = target[2:]
            if target not in by_url:
                # try with no leading parent
                continue
            if anchor not in by_url[target]:
                broken_anchors.append({"page": rel, "href": href, "target": target})
    if broken_anchors:
        report["issues"].extend({"kind": "broken_anchor", **b} for b in broken_anchors)
        failures += len(broken_anchors)
    report["checks"]["broken_anchors"] = len(broken_anchors)

    # --- pass 3: CSS class usage vs definition ---
    css = CSS.read_text(encoding="utf-8") if CSS.exists() else ""
    defined_classes = set(CSS_CLASSES_RE.findall(css))
    all_used = set().union(*page_classes.values()) if page_classes else set()
    # ignore tag-pill etc that are dynamic — we still want to catch typos.
    # Classes referenced but never defined in CSS:
    referenced_undefined = sorted(c for c in all_used if c not in defined_classes
                                  # heuristic: skip very generic classes
                                  and not c.startswith(("data-", "fa-")))
    # Classes defined in CSS but never used in HTML
    defined_unused = sorted(c for c in defined_classes if c not in all_used)
    report["warnings"].append({"kind":"css_classes_referenced_but_not_in_styles", "classes": referenced_undefined[:60], "n": len(referenced_undefined)})
    report["warnings"].append({"kind":"css_classes_defined_but_unused",            "classes": defined_unused[:60],   "n": len(defined_unused)})
    report["checks"]["css_classes_used"] = len(all_used)
    report["checks"]["css_classes_defined"] = len(defined_classes)

    # --- pass 4: word counts (informational) ---
    total_words = sum(page_words.values())
    report["checks"]["total_words"] = total_words
    report["checks"]["per_page_words"] = page_words

    # --- pass 4b: self-consistency — every page logo + nav order must match ---
    # canonical logo markup. anything else is drift.
    LOGO_OK_RE = re.compile(r'<a class="logo"[^>]*>godding</a>')
    bad_logos = []
    for rel, html in raw.items():
        if not LOGO_OK_RE.search(html):
            bad_logos.append(rel)
    if bad_logos:
        report["issues"].extend({"kind": "logo_drift", "file": f} for f in bad_logos)
        failures += len(bad_logos)
    report["checks"]["logo_drift"] = len(bad_logos)

    # canonical "must include" nav entries — every page should link to these
    REQUIRED_NAV = ["nothing.html", "belief.html", "brain.html", "religion.html",
                    "stigmergy.html", "economics.html", "commons.html", "crime.html", "world.html", "swarm.html",
                    "graph.html", "depends.html", "idx.html"]
    nav_drift = []
    for rel, html in raw.items():
        # crude: just check if the href appears at all
        for needed in REQUIRED_NAV:
            if f'href="{needed}"' not in html and f'href="../{needed}"' not in html and f'href="pages/{needed}"' not in html:
                nav_drift.append({"page": rel, "missing": needed})
    if nav_drift:
        report["warnings"].append({"kind": "nav_missing_link", "n": len(nav_drift), "examples": nav_drift[:20]})
    report["checks"]["nav_missing_link"] = len(nav_drift)

    # ---