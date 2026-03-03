#!/usr/bin/env python3
"""Principles Dedup — surface merge candidates in PRINCIPLES.md.

Pairwise similarity via keyword overlap, extends/absorbs mentions, same-theme weight.

Usage:
    python3 tools/principles_dedup.py              # Top 10 candidates
    python3 tools/principles_dedup.py -n 20        # Top 20
    python3 tools/principles_dedup.py --threshold 0.3
    python3 tools/principles_dedup.py --json       # Machine-readable
"""
import argparse, json, re, sys
from pathlib import Path

PRINCIPLES_PATH = Path(__file__).resolve().parent.parent / "memory" / "PRINCIPLES.md"
STOPWORDS = frozenset((
    "a an the is are was were be been being have has had do does did will would "
    "shall should may might can could of in to for on with at by from as into "
    "through during before after above below between out off over under again "
    "further then once here there when where why how all each every both few "
    "more most other some such no nor not only own same so than too very that "
    "this these those and but or if while because until about against its it "
    "they them their he she his her we you your our which what who whom up "
    "also just don doesn didn isn aren wasn weren hasn haven hadn won wouldn "
    "shouldn couldn mustn needn per via vs ie eg etc").split())


def parse_principles(text):
    """Parse PRINCIPLES.md into list of {id, text, section, theme}."""
    principles, section, theme = [], "", ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            section, theme = line[3:].strip(), ""
            continue
        if line.startswith("**") and "**:" in line:
            idx = line.index("**:", 2)
            theme, content = line[2:idx].strip(), line[idx + 3:].strip()
        elif line.startswith("---") or not line:
            continue
        else:
            content = line
        for part in content.split(" | "):
            m = re.match(r"(P-\d+)\s+(.*)", part.strip())
            if m:
                principles.append({"id": m.group(1), "text": m.group(2),
                                   "section": section, "theme": theme})
    return principles


def keywords(text):
    """Significant keyword set from text."""
    return {w for w in re.findall(r"[a-z][a-z0-9_-]+", text.lower())
            if w not in STOPWORDS and len(w) > 2}


def similarity(p1, p2):
    """Similarity score between two principles (0.0 to ~1.0)."""
    kw1, kw2 = keywords(p1["text"]), keywords(p2["text"])
    if not kw1 or not kw2:
        return 0.0
    inter = kw1 & kw2
    jaccard = len(inter) / len(kw1 | kw2)
    overlap = len(inter) / min(len(kw1), len(kw2))
    base = 0.6 * jaccard + 0.4 * overlap
    # Same theme boost
    if p1["theme"] and p1["theme"] == p2["theme"]:
        base += 0.10
    elif p1["section"] and p1["section"] == p2["section"]:
        base += 0.03
    # Cross-reference boost
    if p2["id"] in p1["text"] or p1["id"] in p2["text"]:
        base += 0.15
    return round(base, 4)


def find_candidates(principles, threshold, top_n):
    """Top N candidate pairs above threshold, sorted by score desc."""
    pairs = []
    for i in range(len(principles)):
        for j in range(i + 1, len(principles)):
            score = similarity(principles[i], principles[j])
            if score >= threshold:
                a, b = principles[i], principles[j]
                pairs.append({"p1": a["id"], "p2": b["id"], "score": score,
                              "section1": a["section"], "section2": b["section"],
                              "theme1": a["theme"], "theme2": b["theme"],
                              "snippet1": a["text"][:80], "snippet2": b["text"][:80]})
    pairs.sort(key=lambda x: x["score"], reverse=True)
    return pairs[:top_n]


def main():
    ap = argparse.ArgumentParser(description="Surface duplicate/overlapping principles")
    ap.add_argument("-n", "--top", type=int, default=10, help="Top N candidates (default 10)")
    ap.add_argument("--threshold", type=float, default=0.5, help="Min similarity (default 0.5)")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--file", default=str(PRINCIPLES_PATH), help="Path to PRINCIPLES.md")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr); sys.exit(1)
    principles = parse_principles(path.read_text(encoding="utf-8"))
    if not principles:
        print("Error: no principles parsed", file=sys.stderr); sys.exit(1)

    candidates = find_candidates(principles, args.threshold, args.top)

    if args.json:
        print(json.dumps({"total_principles": len(principles),
                           "threshold": args.threshold, "candidates": candidates}, indent=2))
        return

    print(f"Parsed {len(principles)} principles, threshold={args.threshold}, top {args.top}")
    print("=" * 80)
    if not candidates:
        print("No candidates above threshold."); return
    for i, c in enumerate(candidates, 1):
        loc1 = f"{c['section1']}/{c['theme1']}" if c['theme1'] else c['section1']
        loc2 = f"{c['section2']}/{c['theme2']}" if c['theme2'] else c['section2']
        print(f"\n#{i}  {c['p1']} <-> {c['p2']}  score={c['score']:.4f}")
        print(f"  [{loc1}] {c['p1']}: {c['snippet1']}...")
        print(f"  [{loc2}] {c['p2']}: {c['snippet2']}...")


if __name__ == "__main__":
    main()
