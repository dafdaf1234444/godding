#!/usr/bin/env python3
"""godding/swarm/group.py — auto-grouper + tokenizer.

Reads every page under ../pages/, extracts the visible prose, tokenizes it with a
deliberately small dependency-free English tokenizer, computes a tf-idf vector
per page, runs an O(n^2) cosine-similarity clustering at threshold 0.42, and
writes data/groups.json.

The grouper is *suggestive*, not authoritative — the swarm uses it to spot pages
that drift in topic (e.g. a sustainability essay creeping into politics) and to
suggest "see also" links for the next loop run. No file is modified by this
script; it only writes data/groups.json.

Run after loop.py:
    python swarm/group.py
"""
from __future__ import annotations
import json, math, re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "pages"
DATA = ROOT / "data"

# tiny English stoplist — keeps things short and dependency-free
STOP = set("""
a an and are as at be been being but by for from has have he her here him his how i if
in into is it its itself just like may me more most no nor not now of on once one only or
other our out over own same she so some such than that the their them there these they
this those through to too under up us was we were what when where which while who whom
why will with would you your yours
about across after again against all also among any because before below between both can
could did does doing down during each every few first however much must own should some
still then very what which whose
""".split())

WORD_RE = re.compile(r"[a-z][a-z\-']+")
TAG_RE  = re.compile(r"<[^>]+>")
SPACE_RE= re.compile(r"\s+")

def visible_text(html: str) -> str:
    """Strip <script>, <style>, then all tags, normalise whitespace."""
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S|re.I)
    html = re.sub(r"<style[^>]*>.*?</style>",   " ", html, flags=re.S|re.I)
    return SPACE_RE.sub(" ", TAG_RE.sub(" ", html)).strip()

def tokenize(text: str) -> list[str]:
    return [w for w in WORD_RE.findall(text.lower()) if w not in STOP and len(w) > 2]

def tfidf(docs: dict[str, list[str]]) -> dict[str, dict[str, float]]:
    """Plain tf-idf with log-smoothed idf."""
    N = len(docs)
    df = Counter()
    for toks in docs.values():
        for w in set(toks):
            df[w] += 1
    out = {}
    for name, toks in docs.items():
        tf = Counter(toks)
        total = max(1, len(toks))
        vec = {}
        for w, c in tf.items():
            idf = math.log((N + 1) / (df[w] + 1)) + 1.0
            vec[w] = (c / total) * idf
        # L2 normalise
        n = math.sqrt(sum(v*v for v in vec.values())) or 1.0
        out[name] = {w: v / n for w, v in vec.items()}
    return out

def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b): a, b = b, a
    return sum(v * b.get(k, 0) for k, v in a.items())

def cluster(sim: dict[tuple[str, str], float], names: list[str], thresh: float) -> list[list[str]]:
    parent = {n: n for n in names}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    for (a, b), s in sim.items():
        if s >= thresh: union(a, b)
    groups: dict[str, list[str]] = {}
    for n in names:
        groups.setdefault(find(n), []).append(n)
    return sorted(groups.values(), key=lambda g: -len(g))

def label(group: list[str], vecs: dict[str, dict[str, float]], stop_more: set[str]) -> list[str]:
    """Top-3 distinguishing tokens by summed weight, excluding the page-name itself."""
    bag = Counter()
    for n in group:
        for w, v in vecs[n].items():
            if w in stop_more: continue
            bag[w] += v
    return [w for w, _ in bag.most_common(3)]

def main() -> None:
    docs_text: dict[str, str] = {}
    docs_toks: dict[str, list[str]] = {}
    for p in sorted(PAGES.glob("*.html")):
        txt = visible_text(p.read_text(encoding="utf-8"))
        docs_text[p.stem] = txt
        docs_toks[p.stem] = tokenize(txt)

    # also include the home page
    home = ROOT / "index.html"
    if home.exists():
        txt = visible_text(home.read_text(encoding="utf-8"))
        docs_text["index"] = txt
        docs_toks["index"] = tokenize(txt)

    # filter pages whose names appear as common tokens (so a page about "ants"
    # doesn't dominate its own label)
    page_words = {n.replace('-', '') for n in docs_toks}

    vecs = tfidf(docs_toks)
    names = list(vecs.keys())
    sim: dict[tuple[str, str], float] = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sim[(a, b)] = round(cosine(vecs[a], vecs[b]), 4)

    groups = cluster(sim, names, thresh=0.42)
    labelled = []
    for g in groups:
        if len(g) == 1:
            labelled.append({"pages": g, "label_tokens": label(g, vecs, page_words),
                             "size": 1})
        else:
            labelled.append({"pages": sorted(g),
                             "label_tokens": label(g, vecs, page_words),
                             "size": len(g)})

    # for each page, recommend its top-3 sibling pages (highest cosine)
    siblings: dict[str, list[dict]] = {}
    for n in names:
        scored = []
        for m in names:
            if m == n: continue
            s = sim.get((n, m), sim.get((m, n), 0.0))
            scored.append((m, s))
        scored.sort(key=lambda kv: -kv[1])
        siblings[n] = [{"page": m, "sim": s} for m, s in scored[:3]]

    out = {
        "generated": __import__("datetime").datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "n_pages": len(names),
        "thresh": 0.42,
        "groups": labelled,
        "siblings": siblings,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    target = DATA / "groups.json"
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"groups_file": str(target), "n_pages": len(names),
                      "n_groups": len(groups)}))

if __name__ == "__main__":
    main()
