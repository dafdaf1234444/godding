#!/usr/bin/env python3
"""Deep analysis of vascular transport — which lessons are phloem sinks?

Extension of vascular_transport.py. Identifies the specific early lessons that
receive backward citations (phloem sinks) and characterizes their function.
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cite_parse import parse_all_refs  # noqa: E402


def extract_session(text):
    for line in text.splitlines()[:5]:
        m = re.search(r'Session:\s*S(\d+)', line)
        if m:
            return int(m.group(1))
        m = re.search(r'Task:\s*TASK-(\d+)', line)
        if m:
            return int(m.group(1))
    return None


def main():
    lessons = {}
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        lid = f.stem
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else lid
        session = extract_session(text)
        citations = [t for t in parse_all_refs(text) if t != lid]
        lessons[lid] = {"session": session, "title": title, "citations": citations}

    # Find backward edges (old lesson cites newer lesson)
    backward_edges = []
    backward_sinks = defaultdict(list)  # target -> list of (source, delta)
    backward_sources = defaultdict(list)  # source -> list of (target, delta)

    for lid, data in lessons.items():
        src_s = data["session"]
        if src_s is None:
            continue
        for tgt in data["citations"]:
            if tgt not in lessons:
                continue
            tgt_s = lessons[tgt]["session"]
            if tgt_s is None:
                continue
            if src_s < tgt_s:  # backward: old cites new
                backward_edges.append({
                    "source": lid, "target": tgt,
                    "src_session": src_s, "tgt_session": tgt_s,
                    "delta": tgt_s - src_s,
                })
                backward_sinks[tgt].append((lid, tgt_s - src_s))
                backward_sources[lid].append((tgt, tgt_s - src_s))

    # Top backward-citation sources (phloem pumps — old lessons that cite many newer ones)
    top_sources = sorted(backward_sources.items(), key=lambda x: len(x[1]), reverse=True)[:20]

    # Top backward-citation targets (phloem sinks — newer lessons cited BY older ones)
    top_sinks = sorted(backward_sinks.items(), key=lambda x: len(x[1]), reverse=True)[:20]

    print(f"\n  PHLOEM ANATOMY — Backward Citation Deep Analysis")
    print(f"  {'─' * 60}")
    print(f"  Total backward edges: {len(backward_edges)}")
    print(f"  Unique sources (old lessons citing new): {len(backward_sources)}")
    print(f"  Unique sinks (new lessons cited by old): {len(backward_sinks)}")

    print(f"\n  TOP PHLOEM PUMPS (old lessons updated to cite newer work):")
    for lid, targets in top_sources[:15]:
        s = lessons[lid]["session"]
        title = lessons[lid]["title"][:60]
        avg_delta = sum(d for _, d in targets) / len(targets)
        newest_tgt = max(targets, key=lambda x: x[1])
        print(f"    {lid} (S{s:3d}) → {len(targets):2d} backward cites  avg_reach={avg_delta:.0f}s  newest={newest_tgt[0]}")
        print(f"      {title}")

    print(f"\n  TOP PHLOEM SINKS (newer lessons receiving backward citations):")
    for lid, sources in top_sinks[:15]:
        s = lessons[lid]["session"]
        title = lessons[lid]["title"][:60]
        avg_delta = sum(d for _, d in sources) / len(sources)
        print(f"    {lid} (S{s:3d}) ← {len(sources):2d} backward from   avg_reach={avg_delta:.0f}s")
        print(f"      {title}")

    # Characterize phloem pump lessons — what functions do they serve?
    pump_sessions = [lessons[lid]["session"] for lid, _ in top_sources[:15] if lessons[lid]["session"]]
    sink_sessions = [lessons[lid]["session"] for lid, _ in top_sinks[:15] if lessons[lid]["session"]]

    print(f"\n  PHLOEM PUMP SESSION RANGE: S{min(pump_sessions)}-S{max(pump_sessions)}" if pump_sessions else "")
    print(f"  PHLOEM SINK SESSION RANGE: S{min(sink_sessions)}-S{max(sink_sessions)}" if sink_sessions else "")

    # Biological interpretation
    print(f"\n  BIOLOGICAL INTERPRETATION:")
    print(f"  Phloem pumps = mature leaves (old lessons that actively redistribute)")
    print(f"  Phloem sinks = roots/storage (new lessons that old knowledge feeds into)")
    print(f"  The pump→sink flow is the swarm's knowledge redistribution system")

    # Save extended results
    results = {
        "total_backward_edges": len(backward_edges),
        "unique_sources": len(backward_sources),
        "unique_sinks": len(backward_sinks),
        "top_pumps": [{"lid": lid, "session": lessons[lid]["session"],
                       "title": lessons[lid]["title"][:80],
                       "n_backward": len(t), "avg_reach": round(sum(d for _, d in t) / len(t), 1)}
                      for lid, t in top_sources[:15]],
        "top_sinks": [{"lid": lid, "session": lessons[lid]["session"],
                       "title": lessons[lid]["title"][:80],
                       "n_backward_from": len(s), "avg_reach": round(sum(d for _, d in s) / len(s), 1)}
                      for lid, s in top_sinks[:15]],
    }
    out_path = ROOT / "experiments" / "plant-biology" / "f-plb2-phloem-anatomy-s539.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Artifact: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
