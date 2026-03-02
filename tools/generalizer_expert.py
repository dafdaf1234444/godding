#!/usr/bin/env python3
"""
generalizer_expert.py — Swarm Generalization Analyst

Surfaces cross-domain generalization candidates and atlas gaps.

Usage:
  python3 tools/generalizer_expert.py          # human-readable report
  python3 tools/generalizer_expert.py --json   # machine-readable JSON
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).parent.parent


def build_prefix_map() -> tuple[dict[str, str], dict[str, list[str]]]:
    """Map F-<PREFIX> to domain directory names by scanning domain frontiers."""
    prefixes: dict[str, str] = {}
    collisions: dict[str, set[str]] = {}
    domains_dir = ROOT / "domains"
    if not domains_dir.exists():
        return prefixes, {}

    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        frontier = domain_dir / "tasks" / "FRONTIER.md"
        if not frontier.exists():
            continue
        text = frontier.read_text(encoding="utf-8", errors="replace")
        for match in re.findall(r"\*\*F-([A-Z]{2,6})\d+\*\*", text):
            prefix = match
            if prefix not in prefixes:
                prefixes[prefix] = domain_dir.name
            elif prefixes[prefix] != domain_dir.name:
                collisions.setdefault(prefix, set()).update(
                    [prefixes[prefix], domain_dir.name]
                )

    return prefixes, {k: sorted(v) for k, v in collisions.items()}


def extract_domains(text: str, prefix_map: dict[str, str]) -> list[str]:
    domains = set()
    for prefix, domain in prefix_map.items():
        if re.search(rf"\bF-{re.escape(prefix)}\d+\b", text):
            domains.add(domain)
    return sorted(domains)


def extract_prefixes(text: str) -> set[str]:
    return set(re.findall(r"\bF-([A-Z]{2,6})\d+\b", text))


def analyze_lessons(prefix_map: dict[str, str]) -> dict:
    lessons_dir = ROOT / "memory" / "lessons"
    if not lessons_dir.exists():
        return {}

    total = 0
    cross_count = 0
    lesson_rows: list[dict] = []
    domain_counts: Counter = Counter()
    domain_pair_counts: Counter = Counter()
    unknown_prefixes: Counter = Counter()

    for path in sorted(lessons_dir.glob("L-*.md")):
        if path.stem == "TEMPLATE":
            continue
        total += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        domains = extract_domains(text, prefix_map)
        domain_count = len(domains)
        if domain_count >= 2:
            cross_count += 1
        if domains:
            for d in domains:
                domain_counts[d] += 1
        if domain_count >= 2:
            for a, b in combinations(domains, 2):
                domain_pair_counts[(a, b)] += 1

        for prefix in extract_prefixes(text):
            if prefix not in prefix_map:
                unknown_prefixes[prefix] += 1

        lesson_rows.append(
            {
                "lesson": path.stem,
                "domains": domains,
                "domain_count": domain_count,
            }
        )

    def _lesson_key(row: dict) -> tuple[int, int]:
        try:
            num = int(row["lesson"].split("-")[1])
        except Exception:
            num = 0
        return (-row["domain_count"], num)

    top_lessons = sorted(lesson_rows, key=_lesson_key)[:10]
    domain_pairs = [
        {"pair": list(pair), "count": count}
        for pair, count in domain_pair_counts.most_common(10)
    ]
    domains_with_zero = sorted(
        {d for d in prefix_map.values()} - set(domain_counts.keys())
    )

    return {
        "total_lessons": total,
        "cross_domain_lessons": cross_count,
        "cross_domain_rate": round(cross_count / total, 3) if total else 0.0,
        "top_cross_domain_lessons": top_lessons,
        "domain_reference_counts": dict(sorted(domain_counts.items())),
        "domain_pair_counts": domain_pairs,
        "domains_with_zero_lessons": domains_with_zero,
        "unknown_prefix_counts": dict(sorted(unknown_prefixes.items())),
    }


ISO_KEYWORD_MAP: dict[str, list[str]] = {
    "ISO-1": ["optimization", "gradient", "constraint", "loss function", "minimize"],
    "ISO-2": ["selection pressure", "diversity collapse", "attractor", "brittle"],
    "ISO-3": ["compression", "mdl", "minimum description length", "hierarchical"],
    "ISO-4": ["phase transition", "threshold", "qualitative shift", "tipping", "bursty", "epoch"],
    "ISO-5": ["feedback loop", "positive feedback", "negative feedback", "stabilizing"],
    "ISO-6": ["entropy", "degradation", "decay", "drift", "disorder"],
    "ISO-7": ["emergence", "irreducible", "macro-behavior"],
    "ISO-8": ["power law", "zipf", "pareto", "scaling"],
    "ISO-9": ["bottleneck", "lossy", "relevant signal", "discard"],
    "ISO-10": ["predict-error", "prediction error", "learning loop"],
    "ISO-11": ["diffusion", "random walk", "network spread"],
    "ISO-12": ["max-flow", "min-cut", "bottleneck duality", "throughput"],
    "ISO-13": ["windup", "accumulation", "backlog", "unbounded"],
    "ISO-14": ["recursive", "self-similar", "fractal", "self-referential", "scale-invariant", "self-apply"],
    "ISO-15": ["specialist", "generalizer", "specialization", "comparative advantage", "meta-learner", "division of labor", "expert council"],
}


def analyze_iso_density() -> dict:
    """Measure ISO-density: lessons with ISO-mappable content vs those that cite the atlas.
    This is the true compression utilization signal (L-358).
    """
    lessons_dir = ROOT / "memory" / "lessons"
    if not lessons_dir.exists():
        return {}
    already_citing = 0
    mappable_no_cite = 0
    total = 0
    per_iso: Counter = Counter()
    samples: dict[str, list[str]] = {k: [] for k in ISO_KEYWORD_MAP}
    for path in sorted(lessons_dir.glob("L-*.md")):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        total += 1
        cites = "iso-" in text
        matched = [iso for iso, kws in ISO_KEYWORD_MAP.items() if any(kw in text for kw in kws)]
        if cites:
            already_citing += 1
        elif matched:
            mappable_no_cite += 1
            for iso in matched:
                per_iso[iso] += 1
                if len(samples[iso]) < 3:
                    samples[iso].append(path.stem)
    cite_rate = round(already_citing / total, 3) if total else 0.0
    density_rate = round(mappable_no_cite / total, 3) if total else 0.0
    compression_gap = round(mappable_no_cite / max(already_citing, 1), 1)
    return {
        "total_lessons": total,
        "lessons_citing_iso": already_citing,
        "iso_cite_rate": cite_rate,
        "iso_mappable_uncited": mappable_no_cite,
        "iso_density_rate": density_rate,
        "compression_gap_ratio": compression_gap,
        "per_iso_uncited": dict(per_iso.most_common()),
        "samples": {k: v for k, v in samples.items() if v},
    }


def parse_isomorphism_gaps() -> dict:
    atlas = ROOT / "domains" / "ISOMORPHISM-ATLAS.md"
    if not atlas.exists():
        return {}
    text = atlas.read_text(encoding="utf-8", errors="replace")
    counts: Counter = Counter()
    for match in re.finditer(r"\*\*Gaps\*\*:\s*(.*)", text):
        blob = match.group(1).strip()
        if not blob:
            continue
        for raw in re.split(r",\s*", blob):
            cleaned = re.sub(r"\([^)]*\)", "", raw).strip()
            cleaned = re.split(r"\s+[-–—]\s+", cleaned)[0].strip()
            cleaned = cleaned.strip(".?;")
            if not cleaned:
                continue
            counts[cleaned.lower()] += 1
    return {
        "gap_counts": dict(sorted(counts.items(), key=lambda x: (-x[1], x[0]))),
        "top_gaps": [{"gap": k, "count": v} for k, v in counts.most_common(10)],
        "total_gap_refs": sum(counts.values()),
    }


def build_recommendations(lessons: dict, gaps: dict, collisions: dict[str, list[str]]) -> list[str]:
    recs: list[str] = []
    total = lessons.get("total_lessons", 0)
    cross_rate = lessons.get("cross_domain_rate", 0.0)

    if total:
        if cross_rate < 0.15:
            recs.append(
                f"WARN: only {cross_rate:.0%} of lessons cite multiple domains — generalization low"
            )
        elif cross_rate < 0.3:
            recs.append(
                f"INFO: cross-domain lesson rate {cross_rate:.0%} — room to generalize more"
            )

    iso_density = lessons.get("iso_density", {})
    if iso_density:
        gap = iso_density.get("compression_gap_ratio", 0)
        density = iso_density.get("iso_density_rate", 0.0)
        if gap > 5:
            recs.append(
                f"WARN: compression gap {gap:.0f}x — {density:.0%} of lessons have uncited ISO patterns; run atlas annotation pass"
            )
        elif gap > 2:
            recs.append(
                f"INFO: compression gap {gap:.0f}x — consider retroactive ISO citation pass"
            )

    top_lessons = lessons.get("top_cross_domain_lessons", [])
    if top_lessons:
        recs.append(
            f"Review top {min(5, len(top_lessons))} cross-domain lessons for isomorphism or principle promotion"
        )

    gap_list = gaps.get("top_gaps", [])
    if gap_list:
        top = ", ".join(g["gap"] for g in gap_list[:5])
        recs.append(f"Atlas gaps to verify next: {top}")

    zero_domains = lessons.get("domains_with_zero_lessons", [])
    if zero_domains:
        recs.append(
            f"Domains with zero lesson references: {', '.join(zero_domains[:5])}"
            + (" (and more)" if len(zero_domains) > 5 else "")
        )

    if collisions:
        recs.append(
            f"Resolve prefix collisions in domain frontiers: {', '.join(collisions)}"
        )

    if not recs:
        recs.append("OK: generalization coverage healthy — no urgent gaps detected")

    return recs


def run() -> dict:
    prefix_map, collisions = build_prefix_map()
    lessons = analyze_lessons(prefix_map) if prefix_map else {}
    iso_density = analyze_iso_density()
    if lessons:
        lessons["iso_density"] = iso_density
    gaps = parse_isomorphism_gaps()
    recs = build_recommendations(lessons, gaps, collisions)
    return {
        "prefix_map": prefix_map,
        "prefix_collisions": collisions,
        "lesson_generalization": lessons,
        "iso_density": iso_density,
        "isomorphism_gaps": gaps,
        "recommendations": recs,
    }


def _fmt(report: dict) -> None:
    lessons = report.get("lesson_generalization", {})
    gaps = report.get("isomorphism_gaps", {})
    collisions = report.get("prefix_collisions", {})
    recs = report.get("recommendations", [])

    print("=== SWARM GENERALIZER REPORT ===\n")

    prefix_map = report.get("prefix_map", {})
    print(f"[PREFIXES] {len(prefix_map)} domain prefixes detected")
    if collisions:
        print(f"  Collisions: {', '.join(collisions.keys())}")

    if lessons:
        total = lessons.get("total_lessons", 0)
        cross = lessons.get("cross_domain_lessons", 0)
        rate = lessons.get("cross_domain_rate", 0.0)
        print(f"\n[LESSONS] {cross}/{total} cross-domain ({rate:.0%})")
        top = lessons.get("top_cross_domain_lessons", [])[:5]
        if top:
            print("  Top cross-domain lessons:")
            for row in top:
                domains = ", ".join(row["domains"]) if row["domains"] else "none"
                print(f"  - {row['lesson']}: {row['domain_count']} domains ({domains})")
        pairs = lessons.get("domain_pair_counts", [])[:5]
        if pairs:
            print("  Top domain pairs:")
            for pair in pairs:
                print(f"  - {pair['pair'][0]} ↔ {pair['pair'][1]} ({pair['count']})")
        unknown = lessons.get("unknown_prefix_counts", {})
        if unknown:
            unk = ", ".join(f"{k}({v})" for k, v in list(unknown.items())[:5])
            print(f"  Unknown prefixes: {unk}")

    iso_density = report.get("iso_density", {})
    if iso_density:
        citing = iso_density.get("lessons_citing_iso", 0)
        uncited = iso_density.get("iso_mappable_uncited", 0)
        total_d = iso_density.get("total_lessons", 0)
        gap = iso_density.get("compression_gap_ratio", 0)
        print(f"\n[ISO DENSITY] {citing}/{total_d} cite atlas ({iso_density.get('iso_cite_rate', 0):.1%}); {uncited} mappable-uncited ({iso_density.get('iso_density_rate', 0):.1%}); gap {gap:.0f}x")
        per_iso = iso_density.get("per_iso_uncited", {})
        if per_iso:
            top_isos = list(per_iso.items())[:5]
            print("  Top uncited ISO patterns: " + ", ".join(f"{k}({v})" for k, v in top_isos))

    if gaps:
        top_gaps = gaps.get("top_gaps", [])
        if top_gaps:
            print("\n[ATLAS GAPS] Top gap mentions:")
            for g in top_gaps[:5]:
                print(f"  - {g['gap']} ({g['count']})")

    print("\n[RECOMMENDATIONS]")
    for r in recs:
        print(f"  {r}")
    print()


def main() -> None:
    report = run()
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        _fmt(report)


if __name__ == "__main__":
    main()
