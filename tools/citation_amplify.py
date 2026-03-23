#!/usr/bin/env python3
"""citation_amplify.py — F-STIG1: Close the amplification loop.

Identifies high-value sink lessons (0 incoming citations) that deserve
visibility, and top-cited hubs for orient.py trace weighting.

The swarm's stigmergic amplification is open-loop: UCB1 boosts domains
but doesn't feed citation in-degree back to lesson visibility. This tool
closes that loop by surfacing undervisible high-Sharpe sinks alongside
overconcentrated hubs.

Usage:
    python3 tools/citation_amplify.py              # full report
    python3 tools/citation_amplify.py --sinks      # sink analysis only
    python3 tools/citation_amplify.py --hubs       # hub analysis only
    python3 tools/citation_amplify.py --json       # machine-readable
    python3 tools/citation_amplify.py --orient     # orient.py integration lines
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"


def build_citation_graph():
    """Build citation in-degree map from lesson cross-references."""
    citations = {}  # L-NNN -> set of citers
    lesson_meta = {}  # L-NNN -> {sharpe, domain, title, session}

    for f in LESSONS_DIR.iterdir():
        if not f.name.startswith("L-") or not f.name.endswith(".md"):
            continue
        lid = f.name.replace(".md", "")
        text = f.read_text()

        # Skip archived lessons
        if text.startswith("<!--"):
            continue

        # Extract metadata
        sharpe = 5  # default
        m = re.search(r"Sharpe:\s*(\d+)", text)
        if m:
            sharpe = int(m.group(1))
        domain = ""
        m = re.search(r"Domain:\s*(\S+)", text)
        if m:
            domain = m.group(1).strip()
        title_line = ""
        for line in text.split("\n")[:5]:
            if line.startswith("Title:") or line.startswith("# L-"):
                title_line = line.strip()
                break
        session = 0
        m = re.search(r"Session:\s*S?(\d+)", text)
        if m:
            session = int(m.group(1))

        lesson_meta[lid] = {
            "sharpe": sharpe,
            "domain": domain,
            "title": title_line[:80],
            "session": session,
        }

        # Find outgoing citations
        refs = set(re.findall(r"L-\d+", text))
        refs.discard(lid)
        for ref in refs:
            citations.setdefault(ref, set()).add(lid)

    return citations, lesson_meta


def analyze(citations, lesson_meta):
    """Produce amplification analysis."""
    all_lessons = set(lesson_meta.keys())
    cited_lessons = set(citations.keys())
    sinks = all_lessons - cited_lessons

    # Score sinks by Sharpe (high-Sharpe sinks are undervisible)
    sink_data = []
    for lid in sinks:
        meta = lesson_meta.get(lid, {})
        sink_data.append({
            "id": lid,
            "sharpe": meta.get("sharpe", 0),
            "domain": meta.get("domain", ""),
            "title": meta.get("title", ""),
            "session": meta.get("session", 0),
        })
    sink_data.sort(key=lambda x: (-x["sharpe"], -x["session"]))

    # Hub analysis
    hub_data = []
    for lid, citers in sorted(citations.items(), key=lambda x: -len(x[1]))[:20]:
        meta = lesson_meta.get(lid, {})
        hub_data.append({
            "id": lid,
            "in_degree": len(citers),
            "sharpe": meta.get("sharpe", 0),
            "domain": meta.get("domain", ""),
            "title": meta.get("title", ""),
        })

    total_cites = sum(len(c) for c in citations.values())
    top10_cites = sum(d["in_degree"] for d in hub_data[:10])

    return {
        "total_lessons": len(all_lessons),
        "total_citations": total_cites,
        "sink_count": len(sinks),
        "sink_pct": round(len(sinks) / len(all_lessons) * 100, 1),
        "high_sharpe_sinks": [s for s in sink_data if s["sharpe"] >= 7][:15],
        "hub_concentration": round(top10_cites / max(total_cites, 1) * 100, 1),
        "top_hub": hub_data[0] if hub_data else None,
        "hub_gap": (hub_data[0]["in_degree"] / max(hub_data[1]["in_degree"], 1)
                    if len(hub_data) >= 2 else 0),
        "hubs": hub_data,
        "sinks_sample": sink_data[:20],
    }


def orient_lines(analysis):
    """Generate orient.py integration lines."""
    lines = []
    sink_pct = analysis["sink_pct"]
    if sink_pct > 20:
        lines.append(f"AMPLIFICATION: {analysis['sink_count']} sink lessons ({sink_pct}%) — "
                      f"high-Sharpe sinks need citation")
    high_sharpe = analysis["high_sharpe_sinks"]
    if high_sharpe:
        top3 = ", ".join(f"{s['id']} (S{s['sharpe']})" for s in high_sharpe[:3])
        lines.append(f"  Undervisible high-Sharpe: {top3}")
    hub = analysis["top_hub"]
    if hub and analysis["hub_gap"] > 5:
        lines.append(f"  Hub monopoly: {hub['id']} ({hub['in_degree']} citations, "
                      f"{analysis['hub_gap']:.1f}x gap to #2)")
    return lines


def main():
    parser = argparse.ArgumentParser(description="F-STIG1: Citation amplification loop")
    parser.add_argument("--sinks", action="store_true", help="Sink analysis only")
    parser.add_argument("--hubs", action="store_true", help="Hub analysis only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--orient", action="store_true", help="Orient integration lines")
    args = parser.parse_args()

    citations, lesson_meta = build_citation_graph()
    analysis = analyze(citations, lesson_meta)

    if args.json:
        print(json.dumps(analysis, indent=2))
        return

    if args.orient:
        for line in orient_lines(analysis):
            print(line)
        return

    if not args.hubs:
        print(f"=== SINK ANALYSIS (F-STIG1) ===")
        print(f"Sink lessons (0 citations): {analysis['sink_count']}/{analysis['total_lessons']} "
              f"({analysis['sink_pct']}%)")
        print()
        print("High-Sharpe sinks (undervisible, Sharpe ≥ 7):")
        for s in analysis["high_sharpe_sinks"]:
            print(f"  {s['id']} S{s['sharpe']} [{s['domain']}] {s['title'][:60]}")
        print()

    if not args.sinks:
        print(f"=== HUB ANALYSIS ===")
        print(f"Total citations: {analysis['total_citations']}")
        print(f"Hub concentration (top-10): {analysis['hub_concentration']}%")
        if analysis["top_hub"]:
            print(f"Top hub: {analysis['top_hub']['id']} ({analysis['top_hub']['in_degree']} citations, "
                  f"{analysis['hub_gap']:.1f}x gap to #2)")
        print()
        print("Top 20 hubs:")
        for h in analysis["hubs"]:
            print(f"  {h['id']:>8}: {h['in_degree']:>4} citations [{h['domain']}]")


if __name__ == "__main__":
    main()
