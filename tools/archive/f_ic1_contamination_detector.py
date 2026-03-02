#!/usr/bin/env python3
"""F-IC1 contamination detector — audits high-citation lessons for 5 patterns.

Patterns (L-402):
  1. n=1 inflation: single observation cited as measured fact
  2. Citation loop: A cites B cites A (mutual authority amplification)
  3. Cascade amplification: ≥10 transitive citations from a flagged lesson
  4. ISO false positive: ISO tag without structural mapping evidence
  5. Recency override: newer lesson supersedes older without explicit update

Usage:
  python3 tools/f_ic1_contamination_detector.py [--threshold N] [--json]
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"

CITE_RE = re.compile(r"\bL-(\d+)\b")
CONFIDENCE_RE = re.compile(r"^Confidence:\s*(.+)", re.MULTILINE)
ISO_RE = re.compile(r"^.*\bISO[-:].*$", re.MULTILINE)
SESSION_RE = re.compile(r"^Session:\s*S?(\d+)", re.MULTILINE)


def parse_all_lessons() -> dict:
    """Return {lesson_id: {text, cites, confidence, session, iso_tags, title}}."""
    lessons = {}
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        lid = int(f.stem.split("-")[1])
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.strip().splitlines()
        title = lines[0].lstrip("# ").strip() if lines else ""

        # Parse Cites: header
        cites_match = re.search(r"^Cites:\s*(.+)", text, re.MULTILINE)
        cited_ids = set()
        if cites_match:
            cited_ids = {int(m) for m in CITE_RE.findall(cites_match.group(1))}

        # Parse Confidence
        conf_match = CONFIDENCE_RE.search(text)
        confidence = conf_match.group(1).strip() if conf_match else ""

        # Parse Session
        sess_match = SESSION_RE.search(text)
        session = int(sess_match.group(1)) if sess_match else 0

        # Parse ISO tags
        iso_lines = ISO_RE.findall(text)

        lessons[lid] = {
            "text": text,
            "cites": cited_ids,
            "confidence": confidence,
            "session": session,
            "iso_tags": iso_lines,
            "title": title,
        }
    return lessons


def build_citation_graph(lessons: dict) -> tuple[dict, dict]:
    """Return (out_edges, in_edges) as {id: set(ids)}."""
    out_edges = defaultdict(set)
    in_edges = defaultdict(set)
    for lid, data in lessons.items():
        for cited in data["cites"]:
            if cited in lessons and cited != lid:
                out_edges[lid].add(cited)
                in_edges[cited].add(lid)
    return dict(out_edges), dict(in_edges)


def detect_n1_inflation(lessons: dict, in_edges: dict, threshold: int) -> list:
    """Pattern 1: Highly-cited lessons with n=1 or no sample size."""
    flags = []
    n1_patterns = [
        re.compile(r"\bn[=\s]*1\b", re.IGNORECASE),
        re.compile(r"single.{0,20}observation", re.IGNORECASE),
        re.compile(r"\(n=1\)", re.IGNORECASE),
    ]
    weak_confidence = ["theorized", "hypothesized", "speculative", "anecdotal"]
    for lid, data in lessons.items():
        in_deg = len(in_edges.get(lid, set()))
        if in_deg < threshold:
            continue
        conf = data["confidence"].lower()
        # Check for n=1 in confidence field
        is_n1 = any(p.search(conf) for p in n1_patterns)
        # Check for weak confidence labels
        is_weak = any(w in conf for w in weak_confidence)
        # Check for "Measured" without sample size
        is_measured_no_n = (
            "measured" in conf
            and not re.search(r"n\s*[=>]\s*\d{2,}", conf)
        )
        if is_n1 or is_weak:
            flags.append({
                "lesson": f"L-{lid}",
                "in_degree": in_deg,
                "confidence": data["confidence"],
                "pattern": "n=1 inflation",
                "reason": "n=1" if is_n1 else "weak confidence",
                "title": data["title"],
            })
        elif is_measured_no_n:
            flags.append({
                "lesson": f"L-{lid}",
                "in_degree": in_deg,
                "confidence": data["confidence"],
                "pattern": "n=1 inflation (possible)",
                "reason": "measured without explicit sample size ≥10",
                "title": data["title"],
            })
    return flags


def detect_citation_loops(lessons: dict, out_edges: dict, threshold: int,
                          in_edges: dict) -> list:
    """Pattern 2: Mutual citation loops (A→B→A or A→B→C→A)."""
    flags = []
    seen_pairs = set()
    for lid in lessons:
        if lid not in out_edges:
            continue
        for cited in out_edges[lid]:
            if cited in out_edges and lid in out_edges[cited]:
                pair = tuple(sorted([lid, cited]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    combined_in = len(in_edges.get(lid, set())) + len(
                        in_edges.get(cited, set())
                    )
                    flags.append({
                        "lessons": [f"L-{lid}", f"L-{cited}"],
                        "combined_in_degree": combined_in,
                        "pattern": "citation loop",
                        "titles": [
                            lessons[lid]["title"],
                            lessons[cited]["title"],
                        ],
                    })
    return sorted(flags, key=lambda x: -x["combined_in_degree"])


def detect_cascade(lessons: dict, out_edges: dict, in_edges: dict,
                   threshold: int) -> list:
    """Pattern 3: Flagged lessons with large transitive citation trees."""
    flags = []
    # Find lessons that are both highly cited and have quality concerns
    for lid in lessons:
        in_deg = len(in_edges.get(lid, set()))
        if in_deg < threshold:
            continue
        # BFS to count transitive citers
        visited = set()
        queue = list(in_edges.get(lid, set()))
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            queue.extend(in_edges.get(node, set()) - visited)
        if len(visited) >= 10:
            flags.append({
                "lesson": f"L-{lid}",
                "direct_citers": in_deg,
                "transitive_citers": len(visited),
                "pattern": "cascade amplification risk",
                "title": lessons[lid]["title"],
                "confidence": lessons[lid]["confidence"],
            })
    return sorted(flags, key=lambda x: -x["transitive_citers"])


def detect_iso_false_positive(lessons: dict, in_edges: dict,
                              threshold: int) -> list:
    """Pattern 4: ISO tags without structural mapping evidence."""
    flags = []
    structural_words = [
        "maps to", "isomorphic", "structurally", "corresponds",
        "homomorphism", "preserves", "functor", "morphism",
    ]
    for lid, data in lessons.items():
        in_deg = len(in_edges.get(lid, set()))
        if in_deg < threshold:
            continue
        if not data["iso_tags"]:
            continue
        text_lower = data["text"].lower()
        has_structural = any(w in text_lower for w in structural_words)
        if not has_structural:
            flags.append({
                "lesson": f"L-{lid}",
                "in_degree": in_deg,
                "iso_tags": [t.strip() for t in data["iso_tags"][:3]],
                "pattern": "ISO false positive (possible)",
                "reason": "ISO tag present without structural mapping language",
                "title": data["title"],
            })
    return flags


def detect_recency_override(lessons: dict, in_edges: dict,
                            threshold: int) -> list:
    """Pattern 5: Newer lesson that cites an older one and may supersede it."""
    flags = []
    supersede_words = [
        "supersede", "replaces", "obsoletes", "corrects",
        "contradicts", "overrides", "falsif",
    ]
    for lid, data in lessons.items():
        text_lower = data["text"].lower()
        if not any(w in text_lower for w in supersede_words):
            continue
        for cited_id in data["cites"]:
            if cited_id not in lessons:
                continue
            old_in_deg = len(in_edges.get(cited_id, set()))
            if old_in_deg < threshold:
                continue
            if data["session"] > lessons[cited_id]["session"]:
                flags.append({
                    "newer": f"L-{lid}",
                    "older": f"L-{cited_id}",
                    "older_in_degree": old_in_deg,
                    "pattern": "recency override",
                    "newer_title": data["title"],
                    "older_title": lessons[cited_id]["title"],
                })
    return sorted(flags, key=lambda x: -x["older_in_degree"])


def main():
    parser = argparse.ArgumentParser(description="F-IC1 contamination detector")
    parser.add_argument("--threshold", type=int, default=5,
                        help="Minimum in-degree to audit (default: 5)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON instead of summary")
    args = parser.parse_args()

    lessons = parse_all_lessons()
    out_edges, in_edges = build_citation_graph(lessons)

    # Count high-citation lessons
    high_cite = [lid for lid in lessons
                 if len(in_edges.get(lid, set())) >= args.threshold]

    results = {
        "total_lessons": len(lessons),
        "high_citation_lessons": len(high_cite),
        "threshold": args.threshold,
        "patterns": {},
    }

    # Run all 5 detectors
    n1 = detect_n1_inflation(lessons, in_edges, args.threshold)
    loops = detect_citation_loops(lessons, out_edges, args.threshold, in_edges)
    cascade = detect_cascade(lessons, out_edges, in_edges, args.threshold)
    iso_fp = detect_iso_false_positive(lessons, in_edges, args.threshold)
    recency = detect_recency_override(lessons, in_edges, args.threshold)

    results["patterns"] = {
        "n1_inflation": {"count": len(n1), "flags": n1},
        "citation_loops": {"count": len(loops), "flags": loops[:20]},
        "cascade_amplification": {"count": len(cascade), "flags": cascade[:20]},
        "iso_false_positive": {"count": len(iso_fp), "flags": iso_fp},
        "recency_override": {"count": len(recency), "flags": recency[:20]},
    }

    total_flags = sum(p["count"] for p in results["patterns"].values())
    results["total_flags"] = total_flags

    if args.json:
        print(json.dumps(results, indent=2))
        return

    # Summary output
    print(f"=== F-IC1 CONTAMINATION AUDIT ===")
    print(f"Lessons: {len(lessons)} total | {len(high_cite)} with ≥{args.threshold} citations")
    print(f"Total flags: {total_flags}")
    print()

    for name, data in results["patterns"].items():
        label = name.replace("_", " ").title()
        print(f"--- {label}: {data['count']} flags ---")
        for flag in data["flags"][:10]:
            if "lesson" in flag:
                print(f"  {flag['lesson']} ({flag.get('in_degree', '?')} cites): "
                      f"{flag.get('reason', flag.get('pattern', ''))}")
                if flag.get("title"):
                    print(f"    → {flag['title'][:80]}")
            elif "lessons" in flag:
                print(f"  {' ↔ '.join(flag['lessons'])} "
                      f"(combined {flag['combined_in_degree']} cites)")
            elif "newer" in flag:
                print(f"  {flag['newer']} may override {flag['older']} "
                      f"({flag['older_in_degree']} cites)")
                if flag.get("older_title"):
                    print(f"    → {flag['older_title'][:80]}")
        print()


if __name__ == "__main__":
    main()
