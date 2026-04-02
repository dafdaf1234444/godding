#!/usr/bin/env python3
"""
generate_rank.py — The simplest possible page. A ranked list. Worst first.

One line per person. One sentence. One color. Scroll.
If you can read a menu, you can read this.
"""

import json
import glob
from classify import SINS, classify_facts, highest_tier


def load_all_records():
    records = []
    for path in sorted(glob.glob("records/*.json")):
        if "examples" in path:
            continue
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            records.extend(data)
        else:
            records.append(data)
    return records


def worst_thing(record):
    """Pick the single most impactful DID statement."""
    did = record.get("did", [])
    # Prioritize ones with numbers (deaths, money, convictions)
    for d in did:
        for word in ["killed", "dead", "died", "conviction", "million", "billion", "trafficking", "torture", "massacre"]:
            if word in d.lower():
                return d
    return did[0] if did else "See full record."


def score(record):
    """Simple score: tier * 100 + number of facts."""
    matches = classify_facts(record.get("facts", []) + record.get("did", []))
    tier = highest_tier(matches)
    n_sins = len(matches)
    n_facts = len(record.get("facts", []))
    return tier * 1000 + n_sins * 100 + n_facts


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def generate_rank_page(records):
    records.sort(key=score, reverse=True)

    max_score = max(score(r) for r in records) or 1

    rows = ""
    for i, r in enumerate(records):
        s = score(r)
        matches = classify_facts(r.get("facts", []) + r.get("did", []))
        tier = highest_tier(matches)
        sin_names = [SINS[c]["name"] for c in matches]

        pct = int(s / max_score * 100)
        color = {0: "#555", 1: "#d4a574", 2: "#c47474", 3: "#8a4a4a"}.get(tier, "#555")
        tier_label = {0: "", 1: "CORRUPTION", 2: "MURDER / SLAVERY", 3: "CHILDREN HARMED"}.get(tier, "")

        worst = worst_thing(r)
        if len(worst) > 120:
            worst = worst[:117] + "..."

        rows += f"""
<div class="row" style="--bar-width:{pct}%;--bar-color:{color};">
  <div class="rank">#{i+1}</div>
  <div class="info">
    <div class="name">{esc(r['name'])}</div>
    <div class="role">{esc(r.get('role',''))} — {esc(r.get('country',''))}</div>
    <div class="worst">{esc(worst)}</div>
    <div class="tags">
      <span class="tier-tag" style="background:{color};">{tier_label}</span>
      <span class="grade-tag">Grade {esc(r.get('grade','?'))}</span>
    </div>
  </div>
  <div class="bar"></div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Rank — Worst first</title>
<meta name="description" content="{len(records)} leaders and CEOs ranked by documented harm. Evidence graded.">
<meta property="og:title" content="The Rank — {len(records)} people. Worst first.">
<meta property="og:description" content="Ranked by documented harm. Court records. ICC warrants. Federal convictions. You decide.">
<meta property="og:image" content="https://dafdaf1234444.github.io/godding/card.png">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#128065;</text></svg>">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: Georgia, serif; background: #111; color: #ddd; }}
.top {{
    text-align: center;
    padding: 48px 20px 24px;
}}
.top h1 {{
    font-size: 32px;
    font-weight: normal;
    color: #fff;
}}
.top h1 span {{ color: #d4756a; }}
.top p {{ color: #666; font-size: 14px; margin-top: 8px; }}
.count {{
    font-size: 64px;
    color: #d4756a;
    margin: 16px 0 4px;
}}
.count-label {{ color: #555; font-size: 14px; margin-bottom: 16px; }}

.legend {{
    display: flex;
    justify-content: center;
    gap: 20px;
    padding: 8px 20px 24px;
    flex-wrap: wrap;
}}
.legend span {{
    font-size: 12px;
    padding: 4px 12px;
    border-radius: 20px;
    color: #fff;
}}

.list {{
    max-width: 700px;
    margin: 0 auto;
    padding: 0 12px 60px;
}}
.row {{
    position: relative;
    display: flex;
    align-items: flex-start;
    padding: 16px 16px 16px 0;
    border-bottom: 1px solid #1a1a1a;
    overflow: hidden;
}}
.bar {{
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: var(--bar-width);
    background: var(--bar-color);
    opacity: 0.1;
    z-index: 0;
}}
.rank {{
    flex-shrink: 0;
    width: 48px;
    text-align: center;
    font-size: 18px;
    color: #555;
    padding-top: 2px;
    z-index: 1;
}}
.info {{
    flex: 1;
    z-index: 1;
}}
.name {{
    font-size: 17px;
    color: #eee;
    margin-bottom: 2px;
}}
.role {{
    font-size: 12px;
    color: #777;
    margin-bottom: 6px;
}}
.worst {{
    font-size: 14px;
    color: #c99;
    line-height: 1.5;
    margin-bottom: 6px;
}}
.tags {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}}
.tier-tag {{
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 4px;
    color: #fff;
    font-weight: bold;
    letter-spacing: 0.5px;
}}
.grade-tag {{
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 4px;
    background: #2a3a2a;
    color: #7a9a7a;
}}

.bottom {{
    text-align: center;
    padding: 40px 20px 60px;
    max-width: 500px;
    margin: 0 auto;
}}
.bottom a {{
    color: #666;
    text-decoration: none;
    font-size: 13px;
    margin: 0 6px;
}}
.bottom a:hover {{ color: #999; }}
.bottom .big {{
    display: inline-block;
    background: #1a1a1a;
    color: #bbb;
    padding: 14px 28px;
    border-radius: 10px;
    border: 1px solid #333;
    font-size: 15px;
    font-family: inherit;
    text-decoration: none;
    margin: 8px;
}}
.bottom .big:hover {{ background: #222; color: #fff; }}
.bottom p {{ color: #333; font-size: 11px; margin-top: 24px; }}
</style>
</head>
<body>

<div class="top">
    <h1><span>Worst first.</span></h1>
    <div class="count">{len(records)}</div>
    <div class="count-label">leaders &middot; CEOs &middot; networks &middot; ranked by documented harm</div>
    <p>Scroll down. The worst are at the top. Every line is sourced.</p>
</div>

<div class="legend">
    <span style="background:#8a4a4a;">CHILDREN HARMED</span>
    <span style="background:#c47474;">MURDER / SLAVERY</span>
    <span style="background:#d4a574;">CORRUPTION</span>
</div>

<div class="list">
{rows}
</div>

<div class="bottom">
    <a class="big" href="network.html">See the connections</a>
    <a class="big" href="records.html">Full evidence</a>
    <a class="big" href="door.html">Said vs Did</a>
    <div style="margin-top:20px;">
        <a href="all.html">The six sins</a>
        <a href="spread.html">Share this</a>
        <a href="index.html">Godding</a>
    </div>
    <p>
        No tracking. No ads. No owner. Open source. Public records only.<br>
        You decide what it means. The tool just shows you.
    </p>
</div>

</body>
</html>"""


if __name__ == "__main__":
    records = load_all_records()
    html = generate_rank_page(records)
    with open("docs/rank.html", "w") as f:
        f.write(html)
    print(f"Generated docs/rank.html — {len(records)} people ranked")
