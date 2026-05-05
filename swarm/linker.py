#!/usr/bin/env python3
"""godding/swarm/linker.py — likelihood-graph builder.

Reads every page under ../pages/ and the home index.html, computes two
independent similarity scores for every pair of pages, blends them, and
writes data/links.json.

The two scores are deliberately *different* so the blend is informative:

  • w_cosine — nonparametric. TF-IDF cosine on tokenised prose. Sensitive
    to wording overlap, scaled by document length and rare-token weight.

  • w_jaccard — parametric on a curated concept lexicon. Each page's
    visible text is intersected with a small set of "concept tokens"
    (cooperation, energy, gulag, …); we then take |A ∩ B| / |A ∪ B|.
    This is a yes/no signal about whether two pages share the SAME
    underlying ideas, independent of how many words they use.

  blend_w  =  0.55 * w_cosine + 0.45 * w_jaccard

The blend is then min-max normalised across the whole graph to the
[0, 1] range so the front-end "see also" widget can render bars.

The swarm uses the resulting graph in two ways:

  1. /assets/related.js renders the top-3 highest-weight neighbours of
     the current page in the sidebar of every page.
  2. swarm/loop.py prefers to tighten pages whose strongest edges
     have grown over the last run (concept drift signal).

Run after group.py:
    python swarm/linker.py
"""
from __future__ import annotations
import json, math, re, datetime
from pathlib import Path
from collections import Counter

ROOT  = Path(__file__).resolve().parent.parent
PAGES = ROOT / "pages"
DATA  = ROOT / "data"

# ── shared with group.py — kept inline so this script is self-contained ──
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

# ── parametric concept lexicon — the load-bearing ideas of the site ──
# Grouped so we know what each token *means* without rewriting the lexicon.
# When the swarm adds a page, the lexicon should grow alongside it.
CONCEPTS: dict[str, list[str]] = {
    "cooperation": ["cooperate", "cooperation", "defector", "defect", "tit-for-tat",
                    "reciprocity", "trust", "punish", "punishment", "norm"],
    "moral_universals": ["theft", "fraud", "kill", "killing", "rape", "betrayal",
                         "cruelty", "innocent", "child", "children", "harm"],
    "atrocity_scale": ["genocide", "famine", "purge", "gulag", "regime",
                       "dictator", "war", "civilian", "death", "atrocity"],
    "religion": ["god", "heaven", "hell", "sin", "afterlife", "religion",
                 "scripture", "prayer", "soul", "ritual"],
    "brain_stack": ["stack", "compression", "channel", "frozen", "ordered",
                    "principle", "rule", "stigmergy", "stigmergic", "habit"],
    "energy": ["energy", "electricity", "grid", "solar", "wind", "nuclear",
               "fossil", "battery", "joule", "watt"],
    "demographics": ["population", "birth", "fertility", "demographic",
                     "pyramid", "ageing", "median", "cohort"],
    "weapons": ["nuclear", "weapon", "warhead", "deterrence", "icbm", "treaty"],
    "money": ["wealth", "income", "tax", "billionaire", "money", "capital",
              "asset", "offshore"],
    "method": ["evidence", "claim", "source", "study", "data", "model",
               "estimate", "uncertainty", "range"],
    "self_govern": ["vote", "voting", "ballot", "election", "court",
                    "judge", "justice", "law"],
    "loop": ["swarm", "drafter", "critic", "fact-checker", "loop", "diff",
             "rewrite", "tighten", "shrink"],
    "sustainability": ["sustainable", "sustainability", "carrying", "footprint",
                       "carbon", "climate", "agriculture", "land", "water"],
    "health": ["health", "doctor", "medicine", "vaccine", "diet", "exercise",
               "screening", "evidence-based"],
    "predator_chain": ["cow", "cattle", "feed", "predator", "prey", "trophic",
                       "consume", "consumption", "eat", "eaten"],
}
LEX = {token for tokens in CONCEPTS.values() for token in tokens}


def visible_text(html: str) -> str:
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style[^>]*>.*?</style>",   " ", html, flags=re.S | re.I)
    return SPACE_RE.sub(" ", TAG_RE.sub(" ", html)).strip()


def tokenize(text: str) -> list[str]:
    return [w for w in WORD_RE.findall(text.lower()) if w not in STOP and len(w) > 2]


def tfidf(docs: dict[str, list[str]]) -> dict[str, dict[str, float]]:
    n = len(docs)
    df = Counter()
    for toks in docs.values():
        for w in set(toks):
            df[w] += 1
    out: dict[str, dict[str, float]] = {}
    for name, toks in docs.items():
        tf = Counter(toks)
        total = max(1, len(toks))
        vec = {}
        for w, c in tf.items():
            idf = math.log((n + 1) / (df[w] + 1)) + 1.0
            vec[w] = (c / total) * idf
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        out[name] = {w: v / norm for w, v in vec.items()}
    return out


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0) for k, v in a.items())


def concept_set(toks: list[str]) -> set[str]:
    return {t for t in toks if t in LEX}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def shared_concept_label(a: set[str], b: set[str]) -> list[str]:
    """Return the concept buckets that both pages touch — so we can tooltip
    the edge as e.g. 'cooperation, moral_universals'."""
    shared = a & b
    out = []
    for bucket, tokens in CONCEPTS.items():
        if any(t in shared for t in tokens):
            out.append(bucket)
    return out


def main() -> None:
    docs_toks: dict[str, list[str]] = {}
    for p in sorted(PAGES.glob("*.html")):
        txt = visible_text(p.read_text(encoding="utf-8", errors="ignore"))
        docs_toks[p.stem] = tokenize(txt)
    home = ROOT / "index.html"
    if home.exists():
        txt = visible_text(home.read_text(encoding="utf-8", errors="ignore"))
        docs_toks["index"] = tokenize(txt)

    names = sorted(docs_toks.keys())
    vecs  = tfidf(docs_toks)
    csets = {n: concept_set(docs_toks[n]) for n in names}

    edges: list[dict] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            wc = cosine(vecs[a], vecs[b])
            wj = jaccard(csets[a], csets[b])
            blend = 0.55 * wc + 0.45 * wj
            shared = shared_concept_label(csets[a], csets[b])
            edges.append({
                "source":     a,
                "target":     b,
                "w_cosine":   round(wc, 4),
                "w_jaccard":  round(wj, 4),
                "w_blend":    round(blend, 4),
                "shared":     shared,
            })

    # min-max normalise blend to [0,1] for downstream rendering
    if edges:
        lo = min(e["w_blend"] for e in edges)
        hi = max(e["w_blend"] for e in edges)
        span = hi - lo or 1.0
        for e in edges:
            e["w_norm"] = round((e["w_blend"] - lo) / span, 4)

    # neighbours-of-each-page (top 5 by w_norm) — small enough to ship inline
    neighbours: dict[str, list[dict]] = {n: [] for n in names}
    for e in edges:
        neighbours[e["source"]].append({
            "page": e["target"], "w": e["w_norm"], "shared": e["shared"]
        })
        neighbours[e["target"]].append({
            "page": e["source"], "w": e["w_norm"], "shared": e["shared"]
        })
    for n in names:
        neighbours[n] = sorted(neighbours[n], key=lambda r: -r["w"])[:5]

    out = {
        "generated":   datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "n_pages":     len(names),
        "n_edges":     len(edges),
        "method":      "0.55*cosine(tfidf) + 0.45*jaccard(concept_lexicon), min-max normalised",
        "concepts":    list(CONCEPTS.keys()),
        "edges":       edges,
        "neighbours":  neighbours,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    target = DATA / "links.json"
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"links_file": str(target),
                      "n_pages": len(names),
                      "n_edges": len(edges)}))


if __name__ == "__main__":
    main()
