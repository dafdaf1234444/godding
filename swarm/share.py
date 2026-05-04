#!/usr/bin/env python3
"""godding/swarm/share.py — daily marketing share-kit generator.
Reads data/last_run.json + data/changelog.json, writes data/share_kit.json
with copy-paste-ready text for X / LinkedIn / HN / blog stub.
Pure templating. Run after loop.py. Nothing is posted automatically.
"""
from __future__ import annotations
import json, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

def now_iso():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def load(p, d):
    p = DATA_DIR / p
    if not p.exists(): return d
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return d

def main():
    last = load("last_run.json", {})
    cl = load("changelog.json", [])
    accepted = [d for d in last.get("details", []) if d.get("status") == "accepted"]
    if accepted:
        page = accepted[0]["page"].replace(".html", "")
        rationale = accepted[0].get("rationale", "tightened a paragraph").rstrip(".")
        tweet = (f"the swarm just tightened /{page} on godding — {rationale}. "
                 f"every accepted edit is logged in public. "
                 f"dafdaf1234444.github.io/godding")
    else:
        tweet = ("godding · a small site with a swarm of language models that "
                 "edits its own pages daily. every change is logged in public. "
                 "dafdaf1234444.github.io/godding")
    tweet = tweet[:220]

    linkedin = (
        "I'm building godding — a small static site about the things we agree "
        "on but rarely act on, paired with a swarm of language models that "
        "reads every page, kills the weak claims, keeps the strong ones, and "
        "logs every change in public. The loop runs daily; today's accepted "
        f"edits: {last.get('accepted_diffs', 0)}/{last.get('proposed_diffs', 0)}. "
        "Source + receipts: github.com/dafdaf1234444/godding"
    )
    hn_title = "Show HN: A static site whose pages are pruned daily by a swarm of LLMs (full logs)"
    blog_stub = (
        f"# the swarm — {last.get('timestamp','')[:10]}\n\n"
        f"this run: {last.get('accepted_diffs', 0)} accepted / "
        f"{last.get('proposed_diffs', 0)} proposed. "
        f"{', '.join('/'+p.replace('.html','') for p in last.get('pages', [])) or 'no diffs'}. "
        f"rationale: {last.get('rationale', '—')}"
    )
    kit = {
        "generated": now_iso(),
        "tweet": tweet,
        "linkedin": linkedin,
        "hn_title": hn_title,
        "blog_stub": blog_stub,
        "recent_changelog": cl[-5:][::-1],
        "policy": [
            "nothing is posted automatically. user copies and sends.",
            "no named living people, no fake controversy.",
            "organic only, paid promotion never.",
        ],
    }
    out = DATA_DIR / "share_kit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"share_kit": str(out), "tweet_chars": len(tweet)}))

if __name__ == "__main__":
    main()
