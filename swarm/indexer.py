#!/usr/bin/env python3
"""godding/swarm/indexer.py — build search index.

Walks every HTML page on the site, extracts the title, kicker, all headings,
and a compact body snippet, then writes data/search_index.json. The search
page (pages/search.html) loads this file and runs purely client-side filtering.

Indexed per page:
  url        — relative URL the search result links to
  title      — h1 text
  kicker     — `.kicker` paragraph (one-line summary)
  headings   — list of h2 / h3 strings (used as anchors when section ids exist)
  text       — first ~600 chars of visible prose, lowercased for matching
  topic      — guessed bucket (essays / sims / crime / world / engine / etc.)

Run:
    python swarm/indexer.py
"""
from __future__ import annotations
import json, re, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "pages"
DATA = ROOT / "data"
HOME = ROOT / "index.html"

H1_RE   = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
H2_RE   = re.compile(r"<h2(?:\s+[^>]*?id=\"([^\"]+)\")?[^>]*>(.*?)</h2>", re.S | re.I)
H3_RE   = re.compile(r"<h3[^>]*>(.*?)</h3>", re.S | re.I)
KICKER_RE = re.compile(r'<p class="kicker">(.*?)</p>', re.S | re.I)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
TAG_RE   = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>", re.S | re.I)
STYLE_RE  = re.compile(r"<style[^>]*>.*?</style>",   re.S | re.I)
SP_RE    = re.compile(r"\s+")

TOPIC_HINTS = [
    ("essays",     ("belief", "religion", "politics", "health", "sustainability")),
    ("sims",       ("good-bad", "ants")),
    ("crime",      ("crime", "criminals", "justice")),
    ("vote",       ("now", "vote")),
    ("world",      ("world",)),
    ("engine",     ("swarm", "depends", "idx", "reach", "build", "search")),
]

def topic_for(stem: str) -> str:
    for name, stems in TOPIC_HINTS:
        if stem in stems:
            return name
    return "other"

def visible(html: str) -> str:
    html = SCRIPT_RE.sub(" ", html)
    html = STYLE_RE.sub(" ", html)
    return SP_RE.sub(" ", TAG_RE.sub(" ", html)).strip()

def strip_tags(s: str) -> str:
    return SP_RE.sub(" ", TAG_RE.sub(" ", s)).strip()

def extract(p: Path, rel_url: str, stem: str) -> dict:
    html = p.read_text(encoding="utf-8", errors="ignore")
    title_m = TITLE_RE.search(html)
    h1_m = H1_RE.search(html)
    kicker_m = KICKER_RE.search(html)
    h2s = [(an or "", strip_tags(txt)) for an, txt in H2_RE.findall(html)]
    h3s = [strip_tags(t) for t in H3_RE.findall(html)]
    body = visible(html)
    body_low = body.lower()[:1200]
    return {
        "url":      rel_url,
        "stem":     stem,
        "topic":    topic_for(stem),
        "title":    strip_tags(h1_m.group(1)) if h1_m else (strip_tags(title_m.group(1)) if title_m else stem),
        "kicker":   strip_tags(kicker_m.group(1)) if kicker_m else "",
        "headings": [{"id": an, "text": txt} for an, txt in h2s] + [{"id":"", "text":t} for t in h3s],
        "text":     body_low,
    }

def main() -> None:
    docs = []
    if HOME.exists():
        docs.append(extract(HOME, "index.html", "index"))
    for p in sorted(PAGES.glob("*.html")):
        docs.append(extract(p, f"pages/{p.name}", p.stem))

    out = {
        "generated": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "n_docs":    len(docs),
        "docs":      docs,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    target = DATA / "search_index.json"
    target.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"index": str(target), "n_docs": len(docs)}))

if __name__ == "__main__":
    main()
