#!/usr/bin/env python3
"""F-PLB2 Vascular Transport Model — Test xylem-phloem duality in citation flow.

Hypothesis: Raw signals (early-session content) flow forward-in-time only (xylem),
while processed lessons/principles flow bidirectionally (phloem).

Method:
  1. Parse all lessons, extract session numbers from headers.
  2. Build citation graph with temporal direction for each edge.
  3. For each citation edge (A cites B):
     - Forward: session(A) > session(B) — newer lesson cites older (xylem-like)
     - Backward: session(A) < session(B) — older lesson updated to cite newer (phloem-like)
     - Same-session: session(A) == session(B) — contemporary flow
  4. Classify lessons by age-tier (early/mid/late) and measure directionality per tier.
  5. Compare to plant vascular model predictions.

Cites: L-1436, F-PLB2, F-PLB3
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cite_parse import parse_all_refs  # noqa: E402


def extract_session(text):
    """Extract session number from lesson header."""
    for line in text.splitlines()[:5]:
        m = re.search(r'Session:\s*S(\d+)', line)
        if m:
            return int(m.group(1))
        # Old format: "Date: ... | Task: ..."
        m = re.search(r'Task:\s*TASK-(\d+)', line)
        if m:
            return int(m.group(1))  # approximate
    return None


def build_temporal_graph():
    """Build citation graph with temporal metadata."""
    lessons = {}  # lid -> {session, title, citations}

    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        lid = f.stem
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else lid
        session = extract_session(text)
        citations = [t for t in parse_all_refs(text) if t != lid]

        lessons[lid] = {
            "session": session,
            "title": title,
            "citations": citations,
        }

    return lessons


def analyze_directionality(lessons):
    """Analyze citation flow directionality."""
    forward = []     # newer cites older (xylem-like: unidirectional)
    backward = []    # older updated to cite newer (phloem-like: bidirectional)
    same_sess = []   # same-session citations
    unknown = []     # missing session data

    for lid, data in lessons.items():
        src_session = data["session"]
        if src_session is None:
            continue

        for target in data["citations"]:
            if target not in lessons:
                continue
            tgt_session = lessons[target]["session"]
            if tgt_session is None:
                unknown.append((lid, target))
                continue

            edge = {
                "src": lid, "tgt": target,
                "src_session": src_session, "tgt_session": tgt_session,
                "delta": src_session - tgt_session,
            }

            if src_session > tgt_session:
                forward.append(edge)
            elif src_session < tgt_session:
                backward.append(edge)
            else:
                same_sess.append(edge)

    return forward, backward, same_sess, unknown


def analyze_by_age_tier(lessons, forward, backward, same_sess):
    """Split lessons into age tiers and analyze directionality per tier."""
    sessions = [d["session"] for d in lessons.values() if d["session"] is not None]
    if not sessions:
        return {}

    max_s = max(sessions)
    min_s = min(sessions)
    range_s = max_s - min_s
    if range_s == 0:
        return {}

    # Tertiles
    t1 = min_s + range_s / 3
    t2 = min_s + 2 * range_s / 3

    def tier(s):
        if s <= t1:
            return "early"
        elif s <= t2:
            return "mid"
        else:
            return "late"

    tiers = {"early": {"forward": 0, "backward": 0, "same": 0},
             "mid": {"forward": 0, "backward": 0, "same": 0},
             "late": {"forward": 0, "backward": 0, "same": 0}}

    for e in forward:
        t = tier(e["src_session"])
        tiers[t]["forward"] += 1
    for e in backward:
        t = tier(e["src_session"])
        tiers[t]["backward"] += 1
    for e in same_sess:
        t = tier(e["src_session"])
        tiers[t]["same"] += 1

    return tiers


def analyze_hub_flow(lessons, forward, backward):
    """Do highly-cited lessons (hubs) show more phloem-like bidirectional flow?"""
    # Count inbound citations per lesson
    inbound = defaultdict(int)
    for lid, data in lessons.items():
        for t in data["citations"]:
            if t in lessons:
                inbound[t] += 1

    # Top 10% = hubs
    sorted_lessons = sorted(inbound.items(), key=lambda x: x[1], reverse=True)
    n_hub = max(1, len(sorted_lessons) // 10)
    hubs = {lid for lid, _ in sorted_lessons[:n_hub]}

    hub_fwd = sum(1 for e in forward if e["tgt"] in hubs)
    hub_bwd = sum(1 for e in backward if e["tgt"] in hubs)
    nonhub_fwd = sum(1 for e in forward if e["tgt"] not in hubs)
    nonhub_bwd = sum(1 for e in backward if e["tgt"] not in hubs)

    return {
        "n_hubs": len(hubs),
        "hub_forward": hub_fwd,
        "hub_backward": hub_bwd,
        "hub_backward_ratio": hub_bwd / (hub_fwd + hub_bwd) if (hub_fwd + hub_bwd) > 0 else 0,
        "nonhub_forward": nonhub_fwd,
        "nonhub_backward": nonhub_bwd,
        "nonhub_backward_ratio": nonhub_bwd / (nonhub_fwd + nonhub_bwd) if (nonhub_fwd + nonhub_bwd) > 0 else 0,
    }


def temporal_reach(forward, backward):
    """Measure temporal reach: average session-distance for forward vs backward edges."""
    fwd_deltas = [e["delta"] for e in forward]
    bwd_deltas = [abs(e["delta"]) for e in backward]

    return {
        "forward_mean_reach": mean(fwd_deltas) if fwd_deltas else 0,
        "forward_median_reach": sorted(fwd_deltas)[len(fwd_deltas) // 2] if fwd_deltas else 0,
        "forward_max_reach": max(fwd_deltas) if fwd_deltas else 0,
        "backward_mean_reach": mean(bwd_deltas) if bwd_deltas else 0,
        "backward_median_reach": sorted(bwd_deltas)[len(bwd_deltas) // 2] if bwd_deltas else 0,
        "backward_max_reach": max(bwd_deltas) if bwd_deltas else 0,
    }


def main():
    lessons = build_temporal_graph()
    n_total = len(lessons)
    n_with_session = sum(1 for d in lessons.values() if d["session"] is not None)

    forward, backward, same_sess, unknown = analyze_directionality(lessons)
    tiers = analyze_by_age_tier(lessons, forward, backward, same_sess)
    hub_flow = analyze_hub_flow(lessons, forward, backward)
    reach = temporal_reach(forward, backward)

    total_directed = len(forward) + len(backward) + len(same_sess)
    fwd_ratio = len(forward) / total_directed if total_directed else 0
    bwd_ratio = len(backward) / total_directed if total_directed else 0
    same_ratio = len(same_sess) / total_directed if total_directed else 0

    # Xylem-phloem assessment
    # Xylem = forward-only (unidirectional upward). High forward ratio = xylem-like.
    # Phloem = bidirectional. Backward citations = phloem reflux.
    xylem_score = fwd_ratio  # 1.0 = pure xylem
    phloem_index = bwd_ratio / fwd_ratio if fwd_ratio > 0 else 0  # phloem reflux rate

    # Verdict
    has_xylem = fwd_ratio > 0.7  # dominant forward flow
    has_phloem = bwd_ratio > 0.05  # non-trivial backward flow
    vascular_duality = has_xylem and has_phloem
    directionality_ratio = fwd_ratio / bwd_ratio if bwd_ratio > 0 else float('inf')

    results = {
        "frontier": "F-PLB2",
        "session": "S539",
        "hypothesis": "Xylem-phloem duality: forward citations (xylem) dominate, backward citations (phloem) are non-trivial",
        "n_lessons": n_total,
        "n_with_session": n_with_session,
        "total_directed_edges": total_directed,
        "forward_count": len(forward),
        "backward_count": len(backward),
        "same_session_count": len(same_sess),
        "unknown_count": len(unknown),
        "forward_ratio": round(fwd_ratio, 4),
        "backward_ratio": round(bwd_ratio, 4),
        "same_session_ratio": round(same_ratio, 4),
        "directionality_ratio": round(directionality_ratio, 2),
        "xylem_score": round(xylem_score, 4),
        "phloem_index": round(phloem_index, 4),
        "tier_analysis": {
            t: {
                "forward": d["forward"],
                "backward": d["backward"],
                "same": d["same"],
                "backward_ratio": round(d["backward"] / (d["forward"] + d["backward"] + d["same"]), 4)
                    if (d["forward"] + d["backward"] + d["same"]) > 0 else 0,
            }
            for t, d in tiers.items()
        },
        "hub_flow": hub_flow,
        "temporal_reach": reach,
        "verdict": {
            "has_xylem_dominance": has_xylem,
            "has_phloem_reflux": has_phloem,
            "vascular_duality_confirmed": vascular_duality,
            "directionality_ratio_fwd_bwd": round(directionality_ratio, 2),
        },
    }

    # Print summary
    print(f"\n  F-PLB2 Vascular Transport Model — Citation Flow Directionality")
    print(f"  {'─' * 60}")
    print(f"  Lessons: {n_total} ({n_with_session} with session data)")
    print(f"  Directed edges: {total_directed}")
    print(f"")
    print(f"  FLOW DIRECTION:")
    print(f"    Forward (xylem):     {len(forward):5d}  ({fwd_ratio:.1%})")
    print(f"    Backward (phloem):   {len(backward):5d}  ({bwd_ratio:.1%})")
    print(f"    Same-session:        {len(same_sess):5d}  ({same_ratio:.1%})")
    print(f"    Directionality ratio: {directionality_ratio:.1f}x (forward/backward)")
    print(f"")
    print(f"  BY AGE TIER:")
    for t in ["early", "mid", "late"]:
        if t in tiers:
            d = tiers[t]
            total = d["forward"] + d["backward"] + d["same"]
            br = d["backward"] / total if total > 0 else 0
            print(f"    {t:6s}: fwd={d['forward']:4d}  bwd={d['backward']:4d}  same={d['same']:4d}  bwd_ratio={br:.1%}")
    print(f"")
    print(f"  HUB vs NON-HUB FLOW (top 10% = hubs):")
    print(f"    Hubs ({hub_flow['n_hubs']}): backward_ratio = {hub_flow['hub_backward_ratio']:.1%}")
    print(f"    Non-hubs:   backward_ratio = {hub_flow['nonhub_backward_ratio']:.1%}")
    print(f"")
    print(f"  TEMPORAL REACH (sessions):")
    print(f"    Forward:  mean={reach['forward_mean_reach']:.1f}  median={reach['forward_median_reach']}  max={reach['forward_max_reach']}")
    print(f"    Backward: mean={reach['backward_mean_reach']:.1f}  median={reach['backward_median_reach']}  max={reach['backward_max_reach']}")
    print(f"")
    print(f"  VERDICT:")
    if vascular_duality:
        print(f"    ✓ VASCULAR DUALITY CONFIRMED")
        print(f"      Xylem (forward) dominates at {fwd_ratio:.1%}")
        print(f"      Phloem (backward) non-trivial at {bwd_ratio:.1%}")
        print(f"      Ratio: {directionality_ratio:.1f}x — {'strong' if directionality_ratio > 5 else 'moderate'} directionality")
    else:
        if not has_xylem:
            print(f"    ✗ XYLEM DOMINANCE NOT FOUND (forward={fwd_ratio:.1%}, need >70%)")
        if not has_phloem:
            print(f"    ✗ PHLOEM REFLUX NOT FOUND (backward={bwd_ratio:.1%}, need >5%)")
        print(f"    → Vascular model {'partially' if has_xylem or has_phloem else 'NOT'} supported")

    # Save artifact
    out_path = ROOT / "experiments" / "plant-biology" / "f-plb2-vascular-transport-s539.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Artifact: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
