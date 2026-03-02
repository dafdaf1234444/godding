#!/usr/bin/env python3
"""F-FIN1 extension: Concurrent session complementarity analysis.

Tests whether parallel DOMEX sessions produce complementary (cross-citing)
knowledge or redundant knowledge. Maps to portfolio diversification theory:
if parallel agents diversify, cross-citation rate should exceed random baseline.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANES_FILE = ROOT / "tasks" / "SWARM-LANES.md"
LESSONS_DIR = ROOT / "memory" / "lessons"
CITE_RE = re.compile(r"\bL-(\d+)\b")


def parse_lessons():
    """Parse all lessons: number -> {session, domain, cites, in_citations}."""
    lessons = {}
    for p in LESSONS_DIR.glob("L-*.md"):
        m = re.match(r"L-(\d+)\.md$", p.name)
        if not m:
            continue
        num = int(m.group(1))
        text = p.read_text(errors="replace")
        # Extract session — multiple formats across eras
        sess_m = (
            re.search(r"session:\s*S(\d+)", text, re.IGNORECASE)
            or re.search(r"\*\*Session\*\*:\s*S?(\d+)", text)
            or re.search(r"Session:\s*S?(\d+)", text)
            or re.search(r"\|\s*S(\d+)\s*\|", text)
        )
        session = int(sess_m.group(1)) if sess_m else None
        # Extract domain
        dom_m = re.search(r"domain:\s*(\S+)", text, re.IGNORECASE)
        domain = dom_m.group(1).rstrip(",|") if dom_m else None
        # Extract citations (from full text, excluding self)
        cites = {int(c.group(1)) for c in CITE_RE.finditer(text) if int(c.group(1)) != num}
        lessons[num] = {"session": session, "domain": domain, "cites": cites, "in_degree": 0}
    # Compute in-degree
    for num, info in lessons.items():
        for cited in info["cites"]:
            if cited in lessons:
                lessons[cited]["in_degree"] += 1
    return lessons


def parse_lanes():
    """Parse SWARM-LANES.md for DOMEX lanes with session info."""
    text = LANES_FILE.read_text(errors="replace")
    lanes = []
    for line in text.split("\n"):
        if "|" not in line or "DOMEX" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 12:
            continue
        lane_id = parts[2] if len(parts) > 2 else ""
        session_raw = parts[3] if len(parts) > 3 else ""
        status = parts[11] if len(parts) > 11 else ""
        notes = parts[12] if len(parts) > 12 else ""
        # Extract session number
        sess_m = re.search(r"S?(\d+)", session_raw)
        if not sess_m:
            continue
        session = int(sess_m.group(1))
        # Extract domain from lane ID
        dom_m = re.search(r"DOMEX-([A-Z]+)-", lane_id)
        domain = dom_m.group(1) if dom_m else "UNKNOWN"
        # Extract lesson references from notes
        lesson_refs = {int(m.group(1)) for m in re.finditer(r"\bL-(\d+)\b", notes)}
        lanes.append({
            "lane_id": lane_id,
            "session": session,
            "domain": domain,
            "status": status,
            "lesson_refs": lesson_refs,
        })
    return lanes


def find_concurrent_sessions(lanes):
    """Group lanes by session to find concurrent work."""
    by_session = defaultdict(list)
    for lane in lanes:
        if "MERGED" in lane["status"]:
            by_session[lane["session"]].append(lane)
    # Only sessions with 2+ concurrent DOMEX lanes
    return {s: ls for s, ls in by_session.items() if len(ls) >= 2}


def compute_cross_citation(concurrent, lessons):
    """For each concurrent session, measure cross-citation between its lessons."""
    results = []
    for session, session_lanes in sorted(concurrent.items()):
        # Collect all lessons produced in this session
        session_lessons = set()
        for lane in session_lanes:
            session_lessons.update(lane["lesson_refs"])
        # Also find lessons by session number
        for num, info in lessons.items():
            if info["session"] == session:
                session_lessons.add(num)

        if len(session_lessons) < 2:
            continue

        # Count cross-citations within session's lessons
        cross_cites = 0
        possible_pairs = 0
        lesson_list = sorted(session_lessons)
        for i, l1 in enumerate(lesson_list):
            for l2 in lesson_list[i + 1:]:
                possible_pairs += 1
                if l1 in lessons and l2 in lessons:
                    if l2 in lessons[l1]["cites"] or l1 in lessons[l2]["cites"]:
                        cross_cites += 1

        domains = set()
        for lane in session_lanes:
            domains.add(lane["domain"])

        results.append({
            "session": session,
            "n_lanes": len(session_lanes),
            "n_lessons": len(session_lessons),
            "lessons": sorted(session_lessons),
            "domains": sorted(domains),
            "n_domains": len(domains),
            "cross_cites": cross_cites,
            "possible_pairs": possible_pairs,
            "cross_rate": cross_cites / possible_pairs if possible_pairs > 0 else 0,
        })
    return results


def compute_random_baseline(lessons, n_samples=5000):
    """Random baseline: pick 2 random lessons, measure citation rate."""
    import random
    random.seed(42)
    lesson_nums = [n for n in lessons if lessons[n]["session"] is not None]
    if len(lesson_nums) < 2:
        return 0.0
    hits = 0
    for _ in range(n_samples):
        l1, l2 = random.sample(lesson_nums, 2)
        if l2 in lessons[l1]["cites"] or l1 in lessons[l2]["cites"]:
            hits += 1
    return hits / n_samples


def compute_same_session_baseline(lessons, n_samples=5000):
    """Baseline: random pairs from same session (not necessarily concurrent DOMEX)."""
    import random
    random.seed(43)
    by_session = defaultdict(list)
    for num, info in lessons.items():
        if info["session"] is not None:
            by_session[info["session"]].append(num)
    multi_sessions = {s: ls for s, ls in by_session.items() if len(ls) >= 2}
    if not multi_sessions:
        return 0.0
    sessions = list(multi_sessions.keys())
    hits = 0
    for _ in range(n_samples):
        s = random.choice(sessions)
        l1, l2 = random.sample(multi_sessions[s], 2)
        if l2 in lessons[l1]["cites"] or l1 in lessons[l2]["cites"]:
            hits += 1
    return hits / n_samples


def analyze_domain_diversity(concurrent_results):
    """Analyze whether domain diversity predicts cross-citation."""
    mono = [r for r in concurrent_results if r["n_domains"] == 1]
    diverse = [r for r in concurrent_results if r["n_domains"] >= 2]
    mono_rate = sum(r["cross_rate"] for r in mono) / len(mono) if mono else 0
    diverse_rate = sum(r["cross_rate"] for r in diverse) / len(diverse) if diverse else 0
    return {
        "mono_domain_sessions": len(mono),
        "diverse_domain_sessions": len(diverse),
        "mono_cross_rate": round(mono_rate, 4),
        "diverse_cross_rate": round(diverse_rate, 4),
        "diversity_lift": round(diverse_rate / mono_rate, 2) if mono_rate > 0 else None,
    }


def main():
    lessons = parse_lessons()
    print(f"Parsed {len(lessons)} lessons")

    lanes = parse_lanes()
    print(f"Parsed {len(lanes)} DOMEX lanes")

    concurrent = find_concurrent_sessions(lanes)
    print(f"Found {len(concurrent)} sessions with 2+ concurrent DOMEX lanes")

    cross_results = compute_cross_citation(concurrent, lessons)
    print(f"Analyzed {len(cross_results)} concurrent sessions with 2+ lessons")

    random_baseline = compute_random_baseline(lessons)
    same_session_baseline = compute_same_session_baseline(lessons)

    # Aggregate
    if cross_results:
        avg_cross_rate = sum(r["cross_rate"] for r in cross_results) / len(cross_results)
        total_cross = sum(r["cross_cites"] for r in cross_results)
        total_pairs = sum(r["possible_pairs"] for r in cross_results)
        overall_cross_rate = total_cross / total_pairs if total_pairs > 0 else 0
    else:
        avg_cross_rate = 0
        total_cross = 0
        total_pairs = 0
        overall_cross_rate = 0

    diversity_analysis = analyze_domain_diversity(cross_results)

    # Complementarity ratio
    ratio_vs_random = overall_cross_rate / random_baseline if random_baseline > 0 else None

    result = {
        "experiment": "F-FIN1 concurrent session complementarity",
        "session": "S374",
        "date": "2026-03-01",
        "method": "Parse SWARM-LANES for concurrent DOMEX sessions, measure cross-citation rate between co-produced lessons vs random baseline",
        "n_lessons": len(lessons),
        "n_lanes": len(lanes),
        "n_concurrent_sessions": len(concurrent),
        "n_analyzed_sessions": len(cross_results),
        "random_baseline_cross_rate": round(random_baseline, 4),
        "same_session_baseline_cross_rate": round(same_session_baseline, 4),
        "concurrent_domex_cross_rate": round(overall_cross_rate, 4),
        "concurrent_domex_avg_per_session": round(avg_cross_rate, 4),
        "total_cross_citations": total_cross,
        "total_possible_pairs": total_pairs,
        "complementarity_ratio_vs_random": round(ratio_vs_random, 2) if ratio_vs_random else None,
        "domain_diversity": diversity_analysis,
        "per_session": cross_results,
        "interpretation": "",
        "prediction_check": {
            "expect": "Cross-citation rate within concurrent sessions >2x random baseline",
            "actual": f"Ratio = {round(ratio_vs_random, 2) if ratio_vs_random else 'N/A'}x",
        },
    }

    # Print summary
    print(f"\n=== RESULTS ===")
    print(f"Random baseline cross-rate: {random_baseline:.4f}")
    print(f"Same-session baseline:      {same_session_baseline:.4f}")
    print(f"Concurrent DOMEX cross-rate: {overall_cross_rate:.4f}")
    print(f"Complementarity ratio:      {ratio_vs_random:.2f}x" if ratio_vs_random else "N/A")
    print(f"Total cross-citations:      {total_cross}/{total_pairs} pairs")
    print(f"\nDomain diversity analysis:")
    for k, v in diversity_analysis.items():
        print(f"  {k}: {v}")
    print(f"\nTop concurrent sessions:")
    for r in sorted(cross_results, key=lambda x: x["cross_rate"], reverse=True)[:5]:
        print(f"  S{r['session']}: {r['n_lessons']}L, {r['n_domains']} domains, "
              f"cross={r['cross_cites']}/{r['possible_pairs']} ({r['cross_rate']:.2f}), "
              f"domains={r['domains']}")

    # Save
    out = ROOT / "experiments" / "finance" / "f-fin1-complementarity-s374.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    # Convert sets for JSON
    for r in result["per_session"]:
        r["lessons"] = sorted(r["lessons"])
        r["domains"] = sorted(r["domains"])
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out}")

    return result


if __name__ == "__main__":
    result = main()
