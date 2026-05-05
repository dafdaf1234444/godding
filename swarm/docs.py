#!/usr/bin/env python3
"""godding/swarm/docs.py — self-documentation generator.

Walks every page, pulls h1/kicker/h2 list, then writes:
  data/docs.json   — machine-readable, used by demo.html
  pages/demo.html  — auto-generated tour of the site (you can keep this open
                     during a presentation; reload to refresh after a swarm run)

Run:
    python swarm/docs.py
"""
from __future__ import annotations
import json, re, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "pages"
DATA = ROOT / "data"

H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
H2_RE = re.compile(r'<h2(?:\s+[^>]*?id="([^"]+)")?[^>]*>(.*?)</h2>', re.S | re.I)
KICKER_RE = re.compile(r'<p class="kicker">(.*?)</p>', re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")

def strip(s): return re.sub(r"\s+", " ", TAG_RE.sub(" ", s)).strip()

ORDER = [
    ("root", ["belief.html", "religion.html"]),
    ("simulations", ["good-bad.html", "ants.html"]),
    ("crime & justice", ["crime.html", "criminals.html", "justice.html"]),
    ("vote & current claims", ["now.html", "vote.html"]),
    ("world — load-bearing systems", ["world.html"]),
    ("essays", ["politics.html", "health.html", "sustainability.html"]),
    ("engine & meta", ["swarm.html", "depends.html", "idx.html", "search.html", "reach.html", "build.html"]),
]

def extract(p):
    html = p.read_text(encoding="utf-8", errors="ignore")
    h1 = H1_RE.search(html); k = KICKER_RE.search(html)
    return {
        "file":     p.name,
        "title":    strip(h1.group(1)) if h1 else p.stem,
        "kicker":   strip(k.group(1)) if k else "",
        "sections": [{"id": aid or "", "text": strip(t)} for aid, t in H2_RE.findall(html)],
    }

def build_docs():
    out = {"generated": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
           "groups": []}
    for group_name, files in ORDER:
        items = []
        for f in files:
            p = PAGES / f
            if not p.exists(): continue
            items.append(extract(p))
        out["groups"].append({"name": group_name, "items": items})
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "docs.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out

DEMO_TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>demo · godding</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/styles.css">
<style>
  .demo-group{ margin:14px 0 22px }
  .demo-cap{ font-family:var(--mono); font-size:11px; letter-spacing:.18em; text-transform:uppercase; color:var(--ink-mute); border-bottom:1px solid var(--line); padding-bottom:5px; margin-bottom:8px }
  .demo-card{ display:block; background:var(--paper); border:1px solid var(--line); border-radius:var(--radius-sm); padding:12px 16px; margin:8px 0; text-decoration:none; color:var(--ink); transition:transform var(--t), border-color var(--t) }
  .demo-card:hover{ transform:translateY(-1px); border-color:var(--sun) }
  .demo-card h3{ font-family:'Fraunces',Georgia,serif; font-style:italic; font-weight:400; font-size:20px; color:var(--ink); margin:0 0 4px }
  .demo-card .kk{ font-family:var(--mono); font-size:11px; letter-spacing:.10em; text-transform:uppercase; color:var(--ink-mute); margin-bottom:6px }
  .demo-card ul{ list-style:none; padding:0; margin:8px 0 0; display:flex; flex-wrap:wrap; gap:6px }
  .demo-card ul li a{ font-family:var(--mono); font-size:11.5px; padding:3px 10px; border:1px solid var(--line); border-radius:100px; color:var(--ink-2); background:var(--paper-2); text-decoration:none }
  .demo-card ul li a:hover{ border-color:var(--sun); color:var(--sun); background:var(--cream) }
  .stamp{ font-family:var(--mono); font-size:11px; color:var(--ink-mute) }
</style>
</head><body>
<header class="topbar">
  <a class="logo" href="../index.html">g<span class="o">⊙</span>dding</a>
  <nav class="nav">
    <a href="belief.html">belief</a><a href="religion.html">religion</a>
    <a href="good-bad.html">sims · good/bad</a><a href="ants.html">sims · ants</a>
    <a href="crime.html">crime</a><a href="criminals.html">criminals</a>
    <a href="justice.html">justice</a>
    <a href="politics.html">politics</a><a href="now.html">now</a>
    <a href="world.html">world</a>
    <a href="vote.html">vote</a><a href="health.html">health</a>
    <a href="sustainability.html">sustainability</a>
    <a href="swarm.html" class="swarm-link">swarm</a>
    <a href="depends.html">depends</a>
    <a href="idx.html">idx</a>
    <a href="search.html">search</a>
    <a href="reach.html">reach</a><a href="build.html">build</a>
    <a href="../changelog/index.html" class="muted">changelog</a>
  </nav>
</header>

<div class="layout">
<main class="content page fade-in">
  <p class="crumb"><a href="../index.html">godding</a> / demo</p>
  <p class="kicker">demo · auto-generated tour · regenerated daily</p>
  <h1>demo — <em>godding, end to end.</em></h1>
  <p class="dim">This page is built by <code>swarm/docs.py</code> on every run. Each card is a page on the site with its kicker and a list of in-page sections you can jump to. <strong>Use it as a walkthrough.</strong></p>
  <p class="stamp">last regenerated: {generated}</p>

  {body}
</main>

<aside class="sidebar">
  <h4>tour mode</h4>
  <ul>
    <li>regenerated daily</li>
    <li>each card → a page</li>
    <li>each pill → a section</li>
  </ul>
  <h4 style="margin-top:14px">go to</h4>
  <ul>
    <li><a href="search.html">search</a></li>
    <li><a href="idx.html">master index</a></li>
    <li><a href="depends.html">dependency map</a></li>
  </ul>
</aside>
</div>

<footer class="foot">
  <div>godding · <a href="../changelog/index.html">changelog</a> · <a href="https://github.com/dafdaf1234444/godding" target="_blank" rel="noopener">github</a></div>
  <div class="muted">auto-generated. don't hand-edit. run swarm/docs.py.</div>
</footer>
</body></html>
"""

def render_demo(docs: dict) -> str:
    parts = []
    for group in docs["groups"]:
        parts.append(f'<div class="demo-group"><div class="demo-cap">{group["name"]}</div>')
        for item in group["items"]:
            sections_html = ""
            sec_links = [s for s in item["sections"] if s["id"]]
            if sec_links:
                lis = "".join(f'<li><a href="{item["file"]}#{s["id"]}">#{s["id"]} — {s["text"]}</a></li>' for s in sec_links)
                sections_html = f"<ul>{lis}</ul>"
            elif item["sections"]:
                lis = "".join(f'<li><a href="{item["file"]}">{s["text"]}</a></li>' for s in item["sections"][:6])
                sections_html = f"<ul>{lis}</ul>"
            parts.append(
                f'<a class="demo-card" href="{item["file"]}">'
                f'<div class="kk">{item["file"]}</div>'
                f'<h3>{item["title"]}</h3>'
                + (f'<div class="dim" style="font-family:var(--sans);font-size:13.5px;color:var(--ink-2);line-height:1.5">{item["kicker"]}</div>' if item["kicker"] else "")
                + sections_html +
                '</a>'
            )
        parts.append('</div>')
    return "\n".join(parts)

def main() -> None:
    docs = build_docs()
    body = render_demo(docs)
    html = DEMO_TEMPLATE.replace("{generated}", docs["generated"]).replace("{body}", body)
    target = PAGES / "demo.html"
    target.write_text(html, encoding="utf-8")
    print(json.dumps({"docs_file": str(DATA/"docs.json"), "demo_page": str(target),
                      "groups": len(docs["groups"]),
                      "items_total": sum(len(g["items"]) for g in docs["groups"])}))

if __name__ == "__main__":
    main()
