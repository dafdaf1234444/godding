#!/usr/bin/env python3
"""Reactivation Engine — principled revival of dormant knowledge (L-1383).

Implements the dormant-idea reactivation framework as swarm mechanism.
Instead of the simple heuristic `sharpe * active_citers / (age/50)`,
scores DECAYED items using 6-dimensional Q(c) scoring:

  Q = w1·O + w2·D + w3·U + w4·T - w5·L - w6·A

Where:
  O = encoding overlap (INDEX.md themes, domain active lanes)
  D = diagnosticity (how specifically this lesson points to one concept)
  U = utility relevance (frontier connections, Sharpe, active lane links)
  T = tension (unresolved signals, orphaned principles, open challenges)
  L = length cost (cognitive cost to reactivate — line count)
  A = ambiguity (how many similar lessons compete in same domain)

Generates optimal reactivation cues in anchor-context-delta format:
  anchor = lesson ID + title
  context = original domain + encoding session era
  delta = what changed since encoding (new frontiers, new lanes, new evidence)

Timing model: trigger reactivation when dormancy is high, expression is low,
and attention competition is low (succession phase carrying capacity).

Usage:
  python3 tools/reactivation.py              # full scored report
  python3 tools/reactivation.py --brief      # orient.py integration
  python3 tools/reactivation.py --json       # machine-readable artifact
  python3 tools/reactivation.py --top 10     # top N candidates
"""

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from swarm_io import REPO_ROOT, read_text, session_number, lesson_paths

# --- Scoring weights (tunable) ---
W_OVERLAP = 1.0       # encoding overlap with current INDEX themes
W_DIAGNOSTIC = 1.2    # how specifically this lesson points to one concept
W_UTILITY = 1.5       # frontier/lane connections (highest — utility drives revival)
W_TENSION = 1.0       # unresolved loops (signals, orphaned principles)
W_LENGTH = 0.3        # cognitive cost penalty (line count)
W_AMBIGUITY = 0.8     # domain crowding penalty

# --- Thresholds ---
STALE_WINDOW = 50
DORMANT_MIN_AGE = 50   # must be older than this to be dormant
ACTIVE_LANE_BOOST = 2.0


def load_index_themes():
    """Extract theme keywords from INDEX.md for encoding overlap."""
    text = read_text(REPO_ROOT / "memory" / "INDEX.md")
    themes = set()
    for line in text.split("\n"):
        if line.startswith("|") and "Theme" not in line and "---" not in line:
            parts = line.split("|")
            if len(parts) >= 3:
                theme = parts[1].strip().lower()
                # extract individual words from theme name
                for word in re.findall(r"[a-z]{3,}", theme):
                    themes.add(word)
    return themes


def load_active_lanes():
    """Get active SWARM-LANES domains and their keywords."""
    text = read_text(REPO_ROOT / "tasks" / "SWARM-LANES.md")
    lanes = []
    domains = set()
    for line in text.split("\n"):
        if line.startswith("|") and "ACTIVE" in line:
            parts = line.split("|")
            if len(parts) >= 4:
                lane_name = parts[1].strip().lower()
                lanes.append(lane_name)
                for word in re.findall(r"[a-z]{3,}", lane_name):
                    domains.add(word)
    return lanes, domains


def load_open_frontiers():
    """Get open frontier IDs and their referenced lessons."""
    text = read_text(REPO_ROOT / "tasks" / "FRONTIER.md")
    frontier_lessons = set()
    frontier_keywords = set()
    for line in text.split("\n"):
        if "RESOLVED" in line or "Moved to Resolved" in line:
            continue
        refs = re.findall(r"\bL-\d+\b", line)
        frontier_lessons.update(refs)
        for word in re.findall(r"[a-z]{3,}", line.lower()):
            frontier_keywords.add(word)
    return frontier_lessons, frontier_keywords


def load_open_signals():
    """Get open signal content for tension scoring."""
    text = read_text(REPO_ROOT / "tasks" / "SIGNALS.md")
    signal_refs = set()
    signal_keywords = set()
    for line in text.split("\n"):
        if "OPEN" in line or "PENDING" in line:
            refs = re.findall(r"\bL-\d+\b", line)
            signal_refs.update(refs)
            for word in re.findall(r"[a-z]{3,}", line.lower()):
                signal_keywords.add(word)
    return signal_refs, signal_keywords


def parse_lesson(path):
    """Parse lesson for reactivation scoring metadata."""
    text = read_text(path)
    if not text:
        return None
    lines = text.split("\n")
    m = re.search(r"L-(\d+)", path.name)
    if not m:
        return None
    lid = f"L-{m.group(1)}"
    title = ""
    session = 0
    domain = "unknown"
    sharpe = -1
    cites = set()
    body_words = set()

    from lesson_header import parse_domain_field
    for line in lines[:5]:
        tm = re.match(r"#\s+L-\d+[:\s]+(.*)", line)
        if tm:
            title = tm.group(1).strip()
        sm = re.search(r"Session:\s*S?(\d+)", line)
        if sm:
            session = int(sm.group(1))
        if domain == "unknown":
            _doms = parse_domain_field(line)
            if _doms:
                domain = _doms[0]
        shm = re.search(r"Sharpe:\s*(\d+)", line)
        if shm:
            sharpe = int(shm.group(1))

    for line in lines:
        cites.update(re.findall(r"\bL-(\d+)\b", line))
    cites = {f"L-{c}" for c in cites}
    cites.discard(lid)

    # Extract body keywords for overlap/diagnosticity
    for line in lines[5:]:
        for word in re.findall(r"[a-z]{3,}", line.lower()):
            body_words.add(word)

    return {
        "id": lid, "title": title[:80], "session": session,
        "domain": domain, "sharpe": sharpe, "cites": cites,
        "line_count": len(lines), "body_words": body_words,
    }


def score_overlap(lesson, index_themes, lane_keywords):
    """O(c): how well this lesson's content overlaps with current active context."""
    words = lesson["body_words"] | set(re.findall(r"[a-z]{3,}", lesson["title"].lower()))
    theme_hits = len(words & index_themes)
    lane_hits = len(words & lane_keywords)
    # Normalize: more overlap = higher score, cap at 1.0
    raw = (theme_hits * 0.1 + lane_hits * 0.2)
    return min(1.0, raw)


def score_diagnosticity(lesson, domain_counts):
    """D(c): how specifically this lesson points to one concept.
    Low citation fan-out + unique domain position = high diagnosticity."""
    cite_count = len(lesson["cites"])
    domain_size = domain_counts.get(lesson["domain"], 1)
    # Fewer outbound citations = more focused/diagnostic
    cite_penalty = 1.0 / (1.0 + cite_count * 0.1)
    # Smaller domain = more distinctive within it
    domain_factor = 1.0 / (1.0 + math.log1p(domain_size) * 0.2)
    return min(1.0, cite_penalty * 0.6 + domain_factor * 0.4)


def score_utility(lesson, frontier_lessons, frontier_keywords):
    """U(c): does this lesson connect to open frontiers or have high Sharpe?"""
    # Direct frontier reference
    frontier_direct = 1.0 if lesson["id"] in frontier_lessons else 0.0
    # Keyword overlap with frontier text
    words = lesson["body_words"]
    frontier_word_hits = len(words & frontier_keywords)
    frontier_semantic = min(1.0, frontier_word_hits * 0.05)
    # Sharpe bonus
    sharpe_score = min(1.0, max(0, lesson["sharpe"]) / 10.0) if lesson["sharpe"] > 0 else 0.0
    return min(1.0, frontier_direct * 0.4 + frontier_semantic * 0.3 + sharpe_score * 0.3)


def score_tension(lesson, signal_refs, signal_keywords):
    """T(c): unresolved loops — signals, challenges pointing at this lesson."""
    # Direct signal reference
    signal_direct = 1.0 if lesson["id"] in signal_refs else 0.0
    # Keyword overlap with open signals
    words = lesson["body_words"]
    signal_word_hits = len(words & signal_keywords)
    signal_semantic = min(1.0, signal_word_hits * 0.05)
    return min(1.0, signal_direct * 0.5 + signal_semantic * 0.5)


def score_length_cost(lesson):
    """L(c): cognitive cost to reactivate. Longer = more expensive."""
    # Normalize line count: 10 lines = 0.1, 50 lines = 0.5, 100+ = 1.0
    return min(1.0, lesson["line_count"] / 100.0)


def score_ambiguity(lesson, domain_counts, domain_word_overlap):
    """A(c): how many similar lessons compete in the same domain."""
    domain_size = domain_counts.get(lesson["domain"], 1)
    overlap = domain_word_overlap.get(lesson["id"], 0)
    # Large domain with high word overlap = high ambiguity
    size_factor = min(1.0, math.log1p(domain_size) / 5.0)
    overlap_factor = min(1.0, overlap / 20.0)
    return size_factor * 0.5 + overlap_factor * 0.5


def compute_domain_word_overlap(lessons, domain_lessons):
    """How much each lesson's vocabulary overlaps with domain siblings."""
    overlap = {}
    for lid, meta in lessons.items():
        siblings = domain_lessons.get(meta["domain"], [])
        if len(siblings) <= 1:
            overlap[lid] = 0
            continue
        my_words = meta["body_words"]
        sibling_words = set()
        for sib in siblings:
            if sib != lid and sib in lessons:
                sibling_words |= lessons[sib]["body_words"]
        overlap[lid] = len(my_words & sibling_words) if sibling_words else 0
    return overlap


def generate_cue(lesson, current_session):
    """Generate anchor-context-delta reactivation cue."""
    anchor = f"{lesson['id']}: {lesson['title'][:60]}"
    era = "early" if lesson["session"] < 100 else (
        "mid" if lesson["session"] < 300 else "mature")
    context = f"{lesson['domain']} domain, {era} era (S{lesson['session']})"
    age = current_session - lesson["session"]
    delta = f"{age} sessions dormant"
    return {"anchor": anchor, "context": context, "delta": delta}


def timing_recommendation(dormancy_rate, expression_rate, attention_load):
    """Should we reactivate now? Based on D high, A low, U low."""
    if dormancy_rate > 0.25 and expression_rate < 0.1 and attention_load < 2.0:
        return "OPTIMAL"
    elif dormancy_rate > 0.2 and expression_rate < 0.2:
        return "GOOD"
    elif attention_load > 3.0:
        return "DEFER"
    else:
        return "ACCEPTABLE"


def effective_R(lesson_scores, active_citer_counts):
    """R_react: expected downstream reactivation events per revival.
    Analogous to epidemic reproduction number."""
    r_values = {}
    for lid, score in lesson_scores.items():
        citers = active_citer_counts.get(lid, 0)
        # Each active citer has probability proportional to Q score of propagating
        r_values[lid] = round(score * citers * 0.5, 3)
    return r_values


def main():
    parser = argparse.ArgumentParser(description="Reactivation Engine")
    parser.add_argument("--brief", action="store_true", help="Orient.py integration")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--top", type=int, default=10, help="Top N candidates")
    args = parser.parse_args()

    current = session_number()

    # Load context for scoring
    index_themes = load_index_themes()
    active_lanes, lane_keywords = load_active_lanes()
    frontier_lessons, frontier_keywords = load_open_frontiers()
    signal_refs, signal_keywords = load_open_signals()

    # Load and classify lessons
    from knowledge_swarm import build_citation_maps, classify_items
    lessons = {}
    for path in lesson_paths():
        meta = parse_lesson(path)
        if meta:
            lessons[meta["id"]] = meta
    if not lessons:
        print("No lessons found.")
        return

    outbound, inbound = build_citation_maps(lessons)
    states = classify_items(lessons, inbound, current)

    # Pre-compute domain stats
    domain_counts = defaultdict(int)
    domain_lessons = defaultdict(list)
    for lid, meta in lessons.items():
        domain_counts[meta["domain"]] += 1
        domain_lessons[meta["domain"]].append(lid)
    domain_word_overlap = compute_domain_word_overlap(lessons, domain_lessons)

    # Score all DECAYED items
    scored = []
    for lid, state in states.items():
        if state != "DECAYED":
            continue
        meta = lessons[lid]
        O = score_overlap(meta, index_themes, lane_keywords)
        D = score_diagnosticity(meta, domain_counts)
        U = score_utility(meta, frontier_lessons, frontier_keywords)
        T = score_tension(meta, signal_refs, signal_keywords)
        L = score_length_cost(meta)
        A = score_ambiguity(meta, domain_counts, domain_word_overlap)

        Q = (W_OVERLAP * O + W_DIAGNOSTIC * D + W_UTILITY * U
             + W_TENSION * T - W_LENGTH * L - W_AMBIGUITY * A)

        active_citers = sum(
            1 for c in inbound.get(lid, set())
            if states.get(c) in ("ACTIVE", "MUST-KNOW"))

        cue = generate_cue(meta, current)

        scored.append({
            "id": lid, "title": meta["title"], "domain": meta["domain"],
            "sharpe": meta["sharpe"], "age": current - meta["session"],
            "Q": round(Q, 3),
            "components": {"O": round(O, 3), "D": round(D, 3),
                          "U": round(U, 3), "T": round(T, 3),
                          "L": round(L, 3), "A": round(A, 3)},
            "active_citers": active_citers,
            "cue": cue,
        })

    scored.sort(key=lambda x: x["Q"], reverse=True)

    # Compute timing
    total = len(lessons)
    decayed_count = sum(1 for s in states.values() if s == "DECAYED")
    active_count = sum(1 for s in states.values() if s in ("ACTIVE", "MUST-KNOW"))
    dormancy_rate = decayed_count / max(1, total)
    expression_rate = active_count / max(1, total)
    # Attention load from succession phase (approximation)
    attention_load = total / 500.0  # K_threshold ~ 500
    timing = timing_recommendation(dormancy_rate, expression_rate, attention_load)

    # R_react values
    active_citer_map = {}
    for item in scored:
        active_citer_map[item["id"]] = item["active_citers"]
    r_react = effective_R(
        {item["id"]: item["Q"] for item in scored},
        active_citer_map)

    for item in scored:
        item["R_react"] = r_react.get(item["id"], 0)

    # Categorize by revival strategy
    for item in scored:
        if item["R_react"] > 1.0:
            item["strategy"] = "seed"  # will propagate — simple contagion
        elif item["active_citers"] > 0:
            item["strategy"] = "cite_in_lane"  # needs reinforcement — complex contagion
        elif item["components"]["U"] > 0.3:
            item["strategy"] = "frontier_link"  # connect to open frontier
        elif item["components"]["T"] > 0.3:
            item["strategy"] = "signal_resolve"  # addresses open tension
        else:
            item["strategy"] = "archive_or_merge"  # low value — compress

    top = scored[:args.top]

    if args.brief:
        lines = []
        if top:
            lines.append(f"--- Reactivation Engine (S{current}) ---")
            lines.append(f"  Timing: {timing} | Dormancy={dormancy_rate:.1%} "
                        f"Expression={expression_rate:.1%} "
                        f"Attention={attention_load:.1f}x")
            lines.append(f"  Top-{min(5, len(top))} revival targets "
                        f"(of {len(scored)} DECAYED):")
            for item in top[:5]:
                lines.append(f"    {item['id']} Q={item['Q']:.2f} "
                            f"R={item['R_react']:.2f} [{item['strategy']}]: "
                            f"{item['cue']['anchor'][:50]}")
            lines.append("")
        for line in lines:
            print(line)
        return

    if args.json:
        artifact = {
            "session": current,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "timing": {
                "recommendation": timing,
                "dormancy_rate": round(dormancy_rate, 3),
                "expression_rate": round(expression_rate, 3),
                "attention_load": round(attention_load, 3),
            },
            "weights": {
                "O": W_OVERLAP, "D": W_DIAGNOSTIC, "U": W_UTILITY,
                "T": W_TENSION, "L": W_LENGTH, "A": W_AMBIGUITY,
            },
            "total_decayed": len(scored),
            "top_candidates": top,
            "strategy_distribution": {
                s: sum(1 for i in scored if i["strategy"] == s)
                for s in {"seed", "cite_in_lane", "frontier_link",
                         "signal_resolve", "archive_or_merge"}
            },
        }
        out_dir = REPO_ROOT / "experiments" / "meta"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"reactivation-s{current}.json"
        with open(out_path, "w") as f:
            json.dump(artifact, f, indent=2, default=str)
        print(f"Artifact: {out_path}")
        return

    # Full report
    print(f"=== REACTIVATION ENGINE S{current} | {len(scored)} DECAYED items ===\n")
    print(f"Timing: {timing}")
    print(f"  Dormancy rate: {dormancy_rate:.1%} (target trigger: >25%)")
    print(f"  Expression rate: {expression_rate:.1%} (target trigger: <10%)")
    print(f"  Attention load: {attention_load:.1f}x carrying capacity\n")

    strategy_counts = defaultdict(int)
    for item in scored:
        strategy_counts[item["strategy"]] += 1
    print("Strategy distribution:")
    for s, c in sorted(strategy_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c} ({c/max(1,len(scored))*100:.0f}%)")
    print()

    print(f"--- Top {len(top)} Revival Candidates (by Q score) ---")
    for i, item in enumerate(top, 1):
        print(f"\n  {i}. {item['id']} — Q={item['Q']:.3f}  R_react={item['R_react']:.3f}")
        print(f"     Title: {item['title']}")
        print(f"     Domain: {item['domain']} | Sharpe: {item['sharpe']} | Age: {item['age']}s")
        c = item["components"]
        print(f"     Scores: O={c['O']:.2f} D={c['D']:.2f} U={c['U']:.2f} "
              f"T={c['T']:.2f} L={c['L']:.2f} A={c['A']:.2f}")
        print(f"     Strategy: {item['strategy']} | Active citers: {item['active_citers']}")
        cue = item["cue"]
        print(f"     Cue: [{cue['anchor']}] | {cue['context']} | {cue['delta']}")


if __name__ == "__main__":
    main()
