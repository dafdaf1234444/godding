#!/usr/bin/env python3
"""F-IC1 Contamination Detector — audits lessons for 5 information contamination patterns.

Patterns (L-402):
  1. n=1 inflation: single-observation cited as measured fact, spreads via citations
  2. Citation loop: A cites B cites A — mutual amplification
  3. Cascade amplification: 1 lesson × 5+ cites × depth → exponential spread
  4. ISO false positive: forced isomorphism with weak evidence, cited ≥5 times
  5. Recency override: new lesson supersedes validated older one silently

Usage:
  python3 tools/contamination_detector.py              # full audit
  python3 tools/contamination_detector.py --json        # JSON output
  python3 tools/contamination_detector.py --threshold 3  # lower citation threshold
"""

import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path

LESSON_DIR = Path("memory/lessons")
DEFAULT_THRESHOLD = 5


def parse_lesson(path: Path) -> dict:
    """Extract structured fields from a lesson file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.strip().split("\n")
    lesson_id = path.stem  # e.g. L-601

    header = lines[0] if lines else ""
    meta_line = lines[1] if len(lines) > 1 else ""

    # Parse confidence
    conf_match = re.search(r"\*{0,2}Confidence\*{0,2}:\s*(.+?)(?:\s*\||$)", meta_line)
    confidence = conf_match.group(1).strip() if conf_match else "unknown"

    # Parse sample size from confidence
    n_match = re.search(r"\(n=(\d+)", confidence)
    sample_size = int(n_match.group(1)) if n_match else None

    # Parse session
    sess_match = re.search(r"\*{0,2}Session\*{0,2}:\s*(S\d+)", meta_line)
    if sess_match:
        session = sess_match.group(1)
    else:
        date_match = re.search(r"\*{0,2}Date\*{0,2}:\s*(\d{4}-\d{2}-\d{2})", meta_line)
        session = date_match.group(1) if date_match else "unknown"
    sess_num = int(session[1:]) if session.startswith("S") else 0

    # Parse ISO tags
    iso_tags = re.findall(r"ISO-\d+", meta_line)

    # Parse Sharpe
    sharpe_match = re.search(r"\*{0,2}Sharpe\*{0,2}:\s*(\d+)", meta_line)
    sharpe = int(sharpe_match.group(1)) if sharpe_match else None

    # Parse domain
    domain_match = re.search(r"\*{0,2}Domain\*{0,2}:\s*(\S+)", meta_line)
    domain = domain_match.group(1).strip() if domain_match else "unknown"

    # Parse Cites: line
    cites_line = ""
    for line in lines[:5]:
        if re.match(r"\*{0,2}Cites\*{0,2}:", line):
            cites_line = line
            break
    explicit_cites = re.findall(r"\bL-(\d+)\b", cites_line)

    # All L-NNN references in body
    body_refs = re.findall(r"\bL-(\d+)\b", text)
    all_refs = set(f"L-{r}" for r in body_refs if f"L-{r}" != lesson_id)

    # Title (from header line)
    title_match = re.match(r"#\s*L-\d+:\s*(.+)", header)
    title = title_match.group(1).strip() if title_match else header

    return {
        "id": lesson_id,
        "title": title,
        "confidence": confidence,
        "sample_size": sample_size,
        "session": session,
        "session_num": sess_num,
        "iso_tags": iso_tags,
        "sharpe": sharpe,
        "domain": domain,
        "explicit_cites": [f"L-{c}" for c in explicit_cites],
        "all_refs": list(all_refs),
        "path": str(path),
    }


def build_citation_graph(lessons: dict) -> dict:
    """Build forward and reverse citation graphs."""
    forward = collections.defaultdict(set)   # A -> {B, C} means A cites B, C
    reverse = collections.defaultdict(set)   # B -> {A} means B is cited by A

    for lid, info in lessons.items():
        for ref in info["all_refs"]:
            if ref in lessons and ref != lid:
                forward[lid].add(ref)
                reverse[ref].add(lid)

    return {"forward": forward, "reverse": reverse}


def citation_counts(graph: dict) -> dict:
    """Count how many times each lesson is cited."""
    counts = collections.Counter()
    for cited_set in graph["reverse"].values():
        pass  # reverse already has the right structure
    for lid, citers in graph["reverse"].items():
        counts[lid] = len(citers)
    return counts


def detect_n1_inflation(lessons: dict, graph: dict, counts: dict, threshold: int) -> list:
    """Pattern 1: n=1 observation cited as measured fact, with >=threshold citations."""
    findings = []
    for lid, info in lessons.items():
        cite_count = counts.get(lid, 0)
        if cite_count < threshold:
            continue

        # Check for n=1 or very small sample with any confidence level
        is_n1 = info["sample_size"] is not None and info["sample_size"] <= 1

        if is_n1:
            findings.append({
                "pattern": "n=1 inflation",
                "lesson": lid,
                "title": info["title"],
                "confidence": info["confidence"],
                "citations": cite_count,
                "severity": "HIGH" if cite_count >= 10 else "MEDIUM",
                "detail": f"Sample size n={info['sample_size']} with {cite_count} citations",
                "fix": f"Re-validate {lid} with larger sample or downgrade confidence tag",
            })

    return findings


def detect_citation_loops(lessons: dict, graph: dict, counts: dict, threshold: int) -> list:
    """Pattern 2: A cites B cites A — mutual citation loops."""
    findings = []
    seen = set()

    for a, a_refs in graph["forward"].items():
        for b in a_refs:
            if b in graph["forward"] and a in graph["forward"][b]:
                pair = tuple(sorted([a, b]))
                if pair not in seen:
                    seen.add(pair)
                    a_count = counts.get(a, 0)
                    b_count = counts.get(b, 0)
                    combined = a_count + b_count
                    if combined >= threshold:
                        findings.append({
                            "pattern": "citation loop",
                            "lesson": f"{a} <-> {b}",
                            "title": f"{lessons[a]['title'][:40]} <-> {lessons[b]['title'][:40]}",
                            "citations": f"{a}:{a_count}, {b}:{b_count}",
                            "severity": "HIGH" if combined >= 20 else "MEDIUM" if combined >= 10 else "LOW",
                            "detail": f"Mutual citation: {a} cites {b} AND {b} cites {a}",
                            "fix": f"Review if mutual citation represents genuine cross-validation or circular reasoning",
                        })

    return findings


def detect_cascade_amplification(lessons: dict, graph: dict, counts: dict, threshold: int) -> list:
    """Pattern 3: Lesson with ≥threshold citations where citing lessons are also highly cited."""
    findings = []

    for lid, cite_count in counts.items():
        if cite_count < threshold:
            continue

        # Check if citers are themselves highly cited (amplification)
        citers = graph["reverse"].get(lid, set())
        amplified_citers = []
        for citer in citers:
            citer_count = counts.get(citer, 0)
            if citer_count >= 3:  # citers that are themselves well-cited
                amplified_citers.append((citer, citer_count))

        if len(amplified_citers) >= 2:
            # Calculate cascade depth
            total_reach = cite_count + sum(c for _, c in amplified_citers)
            depth = len(amplified_citers)

            info = lessons.get(lid, {})
            sample = info.get("sample_size")
            evidence_quality = "LOW" if (sample and sample <= 2) or "assumed" in info.get("confidence", "").lower() else "OK"

            if evidence_quality == "LOW":
                severity = "HIGH"
            elif depth >= 5:
                severity = "HIGH"
            elif depth >= 3:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            findings.append({
                "pattern": "cascade amplification",
                "lesson": lid,
                "title": info.get("title", "?"),
                "citations": cite_count,
                "amplified_citers": depth,
                "total_reach": total_reach,
                "evidence_quality": evidence_quality,
                "severity": severity,
                "detail": f"{cite_count} direct citations, {depth} amplifying citers (reach={total_reach})",
                "fix": f"Verify evidence quality of {lid}; if weak, add grounding note to all {depth} amplifying citers",
            })

    return findings


def detect_iso_false_positives(lessons: dict, graph: dict, counts: dict, threshold: int) -> list:
    """Pattern 4: ISO-tagged lessons with weak evidence that are highly cited."""
    findings = []

    for lid, info in lessons.items():
        cite_count = counts.get(lid, 0)
        if cite_count < threshold or not info["iso_tags"]:
            continue

        # Weak evidence indicators
        weak_signals = []
        if info["sample_size"] is not None and info["sample_size"] <= 1:
            weak_signals.append(f"n={info['sample_size']}")
        if "assumed" in info["confidence"].lower():
            weak_signals.append("Assumed confidence")
        if "theorized" in info["confidence"].lower():
            weak_signals.append("Theorized")
        if info["sharpe"] is not None and info["sharpe"] <= 2:
            weak_signals.append(f"Sharpe={info['sharpe']}")

        if weak_signals:
            findings.append({
                "pattern": "ISO false positive",
                "lesson": lid,
                "title": info["title"],
                "iso_tags": info["iso_tags"],
                "citations": cite_count,
                "weak_signals": weak_signals,
                "severity": "HIGH" if cite_count >= 10 else "MEDIUM",
                "detail": f"ISO-tagged ({', '.join(info['iso_tags'])}) with weak evidence ({', '.join(weak_signals)}), {cite_count} citations",
                "fix": f"Verify ISO mapping in {lid}; downgrade to analogy if evidence is insufficient",
            })

    return findings


def detect_recency_override(lessons: dict, graph: dict, counts: dict, threshold: int) -> list:
    """Pattern 5: New lesson with same topic supersedes older validated lesson."""
    findings = []

    # Group lessons by domain
    by_domain = collections.defaultdict(list)
    for lid, info in lessons.items():
        by_domain[info["domain"]].append(info)

    for domain, domain_lessons in by_domain.items():
        if domain == "unknown" or len(domain_lessons) < 2:
            continue

        # Sort by session number
        sorted_lessons = sorted(domain_lessons, key=lambda x: x["session_num"])

        for i, newer in enumerate(sorted_lessons):
            for older in sorted_lessons[:i]:
                # Check title word overlap
                newer_words = set(newer["title"].lower().split())
                older_words = set(older["title"].lower().split())
                # Remove common stop words
                stop = {"the", "a", "an", "is", "are", "was", "were", "in", "on",
                        "at", "to", "for", "of", "and", "or", "not", "—", "-", "–"}
                newer_words -= stop
                older_words -= stop

                if not newer_words or not older_words:
                    continue

                overlap = len(newer_words & older_words) / min(len(newer_words), len(older_words))

                if overlap < 0.4:
                    continue

                newer_cites = counts.get(newer["id"], 0)
                older_cites = counts.get(older["id"], 0)

                # Recency override: newer has more citations but weaker evidence
                newer_has_more_cites = newer_cites > older_cites
                older_sharpe = older.get("sharpe") or 0
                newer_sharpe = newer.get("sharpe") or 0
                evidence_inversion = newer_sharpe < older_sharpe and older_sharpe >= 5

                if newer_has_more_cites and evidence_inversion and newer_cites >= threshold:
                    findings.append({
                        "pattern": "recency override",
                        "lesson": f"{newer['id']} supersedes {older['id']}",
                        "title": f"'{newer['title'][:40]}' over '{older['title'][:40]}'",
                        "newer_citations": newer_cites,
                        "older_citations": older_cites,
                        "newer_sharpe": newer_sharpe,
                        "older_sharpe": older_sharpe,
                        "word_overlap": f"{overlap:.0%}",
                        "severity": "MEDIUM",
                        "detail": f"Newer {newer['id']} ({newer_cites} cites, Sharpe {newer_sharpe}) overrides older {older['id']} ({older_cites} cites, Sharpe {older_sharpe})",
                        "fix": f"Review {newer['id']} and {older['id']} for genuine supersession vs. recency bias",
                    })

    return findings


def run_audit(threshold: int = DEFAULT_THRESHOLD) -> dict:
    """Run full contamination audit."""
    # Load all lessons
    lessons = {}
    for path in sorted(LESSON_DIR.glob("L-*.md")):
        info = parse_lesson(path)
        lessons[info["id"]] = info

    # Build citation graph
    graph = build_citation_graph(lessons)
    counts = citation_counts(graph)

    # Run all 5 detectors
    findings = []
    findings.extend(detect_n1_inflation(lessons, graph, counts, threshold))
    findings.extend(detect_citation_loops(lessons, graph, counts, threshold))
    findings.extend(detect_cascade_amplification(lessons, graph, counts, threshold))
    findings.extend(detect_iso_false_positives(lessons, graph, counts, threshold))
    findings.extend(detect_recency_override(lessons, graph, counts, threshold))

    # Summary
    by_pattern = collections.Counter(f["pattern"] for f in findings)
    by_severity = collections.Counter(f["severity"] for f in findings)

    # Highly cited lessons with ≥threshold citations
    highly_cited = {lid: c for lid, c in counts.items() if c >= threshold}

    return {
        "total_lessons": len(lessons),
        "highly_cited_count": len(highly_cited),
        "citation_threshold": threshold,
        "findings_count": len(findings),
        "by_pattern": dict(by_pattern),
        "by_severity": dict(by_severity),
        "findings": sorted(findings, key=lambda f: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(f["severity"], 3),
            f["pattern"]
        )),
        "top_cited": sorted(
            [(lid, c) for lid, c in highly_cited.items()],
            key=lambda x: -x[1]
        )[:10],
    }


def main():
    parser = argparse.ArgumentParser(description="F-IC1 Contamination Detector")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                        help=f"Minimum citations to flag (default: {DEFAULT_THRESHOLD})")
    args = parser.parse_args()

    result = run_audit(args.threshold)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    # Human-readable report
    print(f"=== F-IC1 CONTAMINATION AUDIT ===")
    print(f"Lessons: {result['total_lessons']} | Highly cited (≥{result['citation_threshold']}): {result['highly_cited_count']}")
    print(f"Findings: {result['findings_count']}")
    print()

    if result["by_severity"]:
        print(f"Severity: HIGH={result['by_severity'].get('HIGH', 0)}  "
              f"MEDIUM={result['by_severity'].get('MEDIUM', 0)}  "
              f"LOW={result['by_severity'].get('LOW', 0)}")
    if result["by_pattern"]:
        print(f"Patterns: {', '.join(f'{p}={c}' for p, c in sorted(result['by_pattern'].items()))}")
    print()

    # Findings by severity
    for severity in ["HIGH", "MEDIUM", "LOW"]:
        sev_findings = [f for f in result["findings"] if f["severity"] == severity]
        if not sev_findings:
            continue
        print(f"--- {severity} ---")
        for f in sev_findings:
            print(f"  [{f['pattern']}] {f['lesson']}")
            print(f"    {f['detail']}")
            print(f"    Fix: {f['fix']}")
            print()

    # Top cited summary
    if result["top_cited"]:
        print("--- Top 10 most cited ---")
        for lid, count in result["top_cited"]:
            print(f"  {count:3d}  {lid}")


if __name__ == "__main__":
    main()
