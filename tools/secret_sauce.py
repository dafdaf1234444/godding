#!/usr/bin/env python3
"""
secret_sauce.py — Extract the highest-leverage mechanisms of the swarm.

Scores lessons by: Sharpe × level_weight × (1 + times_cited_by_others)
Surfaces the irreplaceable core — what to preserve if the swarm had to be rebuilt.

Usage:
  python3 tools/secret_sauce.py              # top-20 secret sauce elements
  python3 tools/secret_sauce.py --top 10     # top 10
  python3 tools/secret_sauce.py --json       # JSON output for experiment artifact
  python3 tools/secret_sauce.py --min-sharpe 8  # higher bar

Output:
  Ranked list of lessons + principle citation frequencies + cluster summary
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
PRINCIPLES_FILE = REPO_ROOT / "beliefs" / "PRINCIPLES.md"

LEVEL_WEIGHTS = {"L1": 0.5, "L2": 1.0, "L3": 2.0, "L4": 3.0, "L5": 4.0}

MECHANISM_KEYWORDS = {
    "structural_enforcement": ["structural", "enforce", "creation-time", "wired", "L-601"],
    "expert_dispatch": ["dispatch", "DOMEX", "UCB1", "expert", "F-EXP7"],
    "expect_act_diff": ["expect", "predict", "diff", "EAD", "P11", "P-182"],
    "distillation": ["distill", "synthesis", "synthesize", "L3+", "L-1062"],
    "compaction": ["compact", "proxy_k", "proxy-K", "dark matter", "orphan"],
    "concurrency": ["concurrent", "collision", "anti-repeat", "claim", "F-CON"],
    "science_quality": ["falsif", "pre-reg", "adversar", "PCI", "Sharpe"],
    "meta_reflection": ["meta-reflection", "friction", "process improve", "swarming process"],
}


def parse_lesson(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    num_m = re.search(r"\d+", path.stem)
    if not num_m:
        return None

    # Title
    title_m = re.match(r"^# L-\d+:\s*(.+)", text)
    title = title_m.group(1).strip() if title_m else ""

    # Header area (first 5 lines)
    header = "\n".join(text.splitlines()[:5])

    # Sharpe
    sharpe_m = re.search(r"Sharpe\*{0,2}:\s*(\d+)", header)
    sharpe = int(sharpe_m.group(1)) if sharpe_m else 0

    # Level: "level=L3" or "| level=L3 |" pattern in header
    level_m = re.search(r"\blevel[=:]\s*(L[1-5])\b", text[:200], re.I)
    level = level_m.group(1).upper() if level_m else "L2"  # default L2

    # Domain
    domain_m = re.search(r"Domain\*{0,2}:\s*([^\n|]+)", header)
    domain = domain_m.group(1).strip().split(",")[0].strip() if domain_m else "unknown"

    # Session
    sess_m = re.search(r"Session\*{0,2}:\s*S(\d+)", header)
    session = int(sess_m.group(1)) if sess_m else 0

    # Cites: header — extract all L-NNN and P-NNN and F-NNN
    cites_m = re.search(r"^Cites?\s*:\s*(.+)", text, re.M)
    cited_lessons: set[str] = set()
    cited_principles: set[str] = set()
    cited_frontiers: set[str] = set()
    if cites_m:
        cites_line = cites_m.group(1)
        cited_lessons = {f"L-{x}" for x in re.findall(r"\bL-(\d+)\b", cites_line)}
        cited_principles = {f"P-{x}" for x in re.findall(r"\bP-(\d+)\b", cites_line)}
        cited_frontiers = {f"F-{x}" for x in re.findall(r"\bF-([A-Z0-9]+\d+)\b", cites_line)}

    # Also scan body for lesson refs
    own = num_m.group()
    body_lesson_refs = {f"L-{x}" for x in re.findall(r"\bL-(\d+)\b", text) if x != own}
    body_lesson_refs -= cited_lessons  # only additional body refs

    # Mechanism detection — use body text only (skip header lines)
    body_lines = text.splitlines()[5:]
    body_text = "\n".join(body_lines).lower()
    mechanisms = []
    for mech, keywords in MECHANISM_KEYWORDS.items():
        if any(k.lower() in body_text for k in keywords):
            mechanisms.append(mech)

    return {
        "id": path.stem,
        "title": title,
        "sharpe": sharpe,
        "level": level,
        "domain": domain,
        "session": session,
        "cites_lessons": cited_lessons,
        "cites_principles": cited_principles,
        "cites_frontiers": cited_frontiers,
        "body_refs": body_lesson_refs,
        "mechanisms": mechanisms,
        "text": text,
    }


def score_lesson(lesson: dict, cited_by_count: int) -> float:
    lw = LEVEL_WEIGHTS.get(lesson["level"], 1.0)
    sh = max(lesson["sharpe"], 1)
    return sh * lw * (1 + cited_by_count)


def parse_principles() -> list[dict]:
    try:
        text = PRINCIPLES_FILE.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    principles = []
    for m in re.finditer(r"^\*{0,2}(P-\d+)\*{0,2}[:\s]+(.+)", text, re.M):
        principles.append({"id": m.group(1), "text": m.group(2).strip()[:100]})
    return principles


def build_citation_graph(lessons: list[dict]) -> dict[str, int]:
    """Count how many times each lesson is cited by others."""
    cited_by: Counter = Counter()
    for les in lessons:
        for ref in les["cites_lessons"]:
            cited_by[ref] += 1
        for ref in les["body_refs"]:
            cited_by[ref] += 0.3  # body refs count less
    return dict(cited_by)


def cluster_summary(top_lessons: list[dict]) -> dict[str, list[str]]:
    clusters: dict[str, list[str]] = defaultdict(list)
    for les in top_lessons:
        for mech in les["mechanisms"]:
            clusters[mech].append(les["id"])
    return dict(clusters)


def run(top: int = 20, min_sharpe: int = 6, json_output: bool = False) -> dict:
    all_lessons = []
    for path in sorted(LESSONS_DIR.glob("L-*.md")):
        les = parse_lesson(path)
        if les:
            all_lessons.append(les)

    # Build citation counts
    cited_by = build_citation_graph(all_lessons)

    # Score and filter
    scored = []
    for les in all_lessons:
        if les["sharpe"] < min_sharpe and les["level"] not in ("L3", "L4", "L5"):
            continue
        cb = cited_by.get(les["id"], 0)
        s = score_lesson(les, cb)
        scored.append((s, cb, les))

    scored.sort(key=lambda x: -x[0])
    top_items = scored[:top]

    # Principle citation frequencies across ALL lessons
    principle_counts: Counter = Counter()
    for les in all_lessons:
        for p in les["cites_principles"]:
            principle_counts[p] += 1
    top_principles = principle_counts.most_common(10)

    # Cluster summary
    top_lessons_data = [les for _, _, les in top_items]
    clusters = cluster_summary(top_lessons_data)

    # Mechanism frequency
    mech_freq: Counter = Counter()
    for les in top_lessons_data:
        for m in les["mechanisms"]:
            mech_freq[m] += 1

    results = {
        "total_lessons": len(all_lessons),
        "eligible": len(scored),
        "top_lessons": [
            {
                "id": les["id"],
                "title": les["title"][:80],
                "sharpe": les["sharpe"],
                "level": les["level"],
                "domain": les["domain"],
                "cited_by": round(cb, 1),
                "score": round(s, 1),
                "mechanisms": les["mechanisms"],
            }
            for s, cb, les in top_items
        ],
        "top_principles": [{"id": p, "cited_by_lessons": n} for p, n in top_principles],
        "mechanism_clusters": {k: len(v) for k, v in sorted(clusters.items(), key=lambda x: -len(x[1]))},
        "mechanism_lesson_ids": clusters,
        "params": {"top": top, "min_sharpe": min_sharpe},
    }
    return results


def print_results(r: dict) -> None:
    print(f"\n=== SECRET SAUCE EXTRACTOR ({r['total_lessons']}L total, {r['eligible']} eligible) ===\n")

    print("── TOP LESSONS (secret sauce score = Sharpe × level_weight × (1 + cited_by)) ──")
    for i, les in enumerate(r["top_lessons"], 1):
        mechs = ", ".join(les["mechanisms"][:3]) if les["mechanisms"] else "—"
        print(
            f"  {i:2}. [{les['id']}] {les['level']} Sh={les['sharpe']} "
            f"cited_by={les['cited_by']} score={les['score']}"
        )
        print(f"      {les['title'][:75]}")
        print(f"      domain={les['domain']} | mechanisms: {mechs}")

    print("\n── TOP PRINCIPLES (by lesson citation frequency) ──")
    for p in r["top_principles"]:
        print(f"  {p['id']:8s}  cited by {p['cited_by_lessons']} lessons")

    print("\n── MECHANISM CLUSTERS (in top lessons) ──")
    for mech, count in r["mechanism_clusters"].items():
        bar = "█" * count
        print(f"  {mech:<28} {bar} ({count})")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract swarm secret sauce")
    parser.add_argument("--top", type=int, default=20, help="Number of top lessons to surface")
    parser.add_argument("--min-sharpe", type=int, default=6, help="Min Sharpe score (default 6)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    results = run(top=args.top, min_sharpe=args.min_sharpe, json_output=args.json)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results)


if __name__ == "__main__":
    main()
