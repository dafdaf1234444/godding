#!/usr/bin/env python3
"""
correction_propagation.py — Detect and queue correction gaps in the lesson graph.

When a lesson is falsified or superseded, citers may still treat the original
framing as valid. This tool walks the citation graph to find those gaps.

v2 (S383): Direction-aware falsification detection. Prior version had 75% FP rate
because corrector lessons (containing "FALSIFIED" while describing another lesson's
falsification) were flagged as falsified themselves. Fix: scan bidirectionally —
a lesson is falsified only when OTHER lessons point at it with falsification language.
Citation-type classification: content-dependent vs structural vs citation-only (L-739).

Usage:
  python3 tools/correction_propagation.py                  # report mode
  python3 tools/correction_propagation.py --json           # machine-readable
  python3 tools/correction_propagation.py --save           # save artifact
  python3 tools/correction_propagation.py --no-classify     # skip citation-type breakdown

Related: F-IC1, L-734, L-739, L-025, L-613
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"

# Falsification keywords (for detecting direction)
_FALSIF_KW = (
    r"(?:FALSIFIED|falsified|retracted|disproven|refuted|overturned|invalidated)"
)
# Supersession keywords
_SUPERSEDE_KW = r"(?:supersed(?:es|ed)|replac(?:es|ed)\s+by|obsolet)"

CITE_PAT = re.compile(r"\bL-(\d+)\b")

# Known indirect falsifications: corrector doesn't cite falsified lesson directly.
# Format: {falsified_id: {corrector_ids}}
_KNOWN_FALSIFICATIONS: dict[str, set[str]] = {
    "L-025": {"L-613", "L-618"},  # edge-of-chaos → architectural maturity
}


def _parse_lessons() -> dict[str, dict]:
    """Parse all lessons: extract citations, title, and text."""
    lessons = {}
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        lid = f.stem
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else ""

        # Extract Cites: header
        cites_header: list[str] = []
        for line in lines:
            m = re.match(r"^Cites:\s*(.*)", line)
            if m:
                cites_header = [f"L-{x}" for x in CITE_PAT.findall(m.group(1))]
                break

        # Extract all L-NNN references in body
        all_refs = set(f"L-{x}" for x in CITE_PAT.findall(text))
        all_refs.discard(lid)  # don't count self-reference

        lessons[lid] = {
            "title": title,
            "text": text,
            "cites_header": cites_header,
            "all_refs": all_refs,
        }
    return lessons


def _build_citation_graph(lessons: dict[str, dict]) -> dict[str, set[str]]:
    """Build reverse citation graph: for each lesson, who cites it."""
    cited_by: dict[str, set[str]] = defaultdict(set)
    for lid, data in lessons.items():
        for ref in data["all_refs"]:
            cited_by[ref].add(lid)
    return dict(cited_by)


def _detect_falsified_lessons(
    lessons: dict[str, dict],
) -> dict[str, set[str]]:
    """Detect genuinely falsified lessons using bidirectional evidence.

    Returns: {falsified_lesson_id: {corrector_ids}}

    Key insight (L-739 S383): A lesson is falsified when OTHER lessons say so,
    not when it mentions 'FALSIFIED' (which usually means it's the corrector).
    Two patterns:
      1. Forward: lesson Y says "L-025 ... FALSIFIED" → L-025 is falsified, Y corrects
      2. Reverse: lesson X says "falsified by L-613" → X is falsified, L-613 corrects
    """
    # Collect directed edges: (falsified_target, corrector)
    edges: list[tuple[str, str]] = []

    for lid, data in lessons.items():
        text = data["text"]

        for ref_match in CITE_PAT.finditer(text):
            ref = f"L-{ref_match.group(1)}"
            if ref == lid:
                continue

            # Get surrounding context (100 chars around the reference)
            start = max(0, ref_match.start() - 100)
            end = min(len(text), ref_match.end() + 100)
            context = text[start:end]

            # Pattern 1: "L-NNN ... FALSIFIED/falsified" — ref is falsified, lid corrects
            if re.search(
                rf"{re.escape(ref)}\b.{{0,60}}{_FALSIF_KW}", context
            ):
                edges.append((ref, lid))

            # Pattern 2: "FALSIFIED ... L-NNN" — ref is falsified, lid corrects
            # (lid describes the falsification of ref)
            if re.search(
                rf"{_FALSIF_KW}.{{0,60}}\b{re.escape(ref)}\b", context
            ):
                edges.append((ref, lid))

            # Pattern 3: "falsified by L-NNN" — lid is falsified, ref corrects
            if re.search(
                rf"(?:falsified|corrected|superseded|replaced)\s+by\s+{re.escape(ref)}",
                context,
                re.IGNORECASE,
            ):
                edges.append((lid, ref))

            # Pattern 4: "L-NNN supersedes/replaces" — lid is superseded, ref corrects
            # Actually: if lid says "ref supersedes this" → lid falsified, ref corrects
            if re.search(
                rf"{re.escape(ref)}\s+{_SUPERSEDE_KW}", context, re.IGNORECASE
            ):
                edges.append((lid, ref))

    # Aggregate: build falsified→correctors map
    result: dict[str, set[str]] = {}
    for target, corrector in edges:
        if target in lessons:
            result.setdefault(target, set()).add(corrector)

    # Merge known indirect falsifications (seed)
    for fid, correctors in _KNOWN_FALSIFICATIONS.items():
        if fid in lessons:
            result.setdefault(fid, set()).update(correctors)

    # Remove self-falsification artifacts (lesson can't falsify itself)
    for lid in list(result):
        result[lid].discard(lid)
        if not result[lid]:
            del result[lid]

    # Remove false positives: lessons that contain FALSIFIED because they're
    # REPORTING a falsification (correctors), not because they ARE falsified.
    # A lesson is genuinely falsified only if it self-declares via:
    #   - SUPERSEDED / retracted markers at the top
    #   - "falsified by L-NNN" pattern
    # A lesson that describes "X FALSIFIED" or "hypothesis FALSIFIED" is a
    # corrector — remove it from the falsified list.
    all_correctors = set()
    for correctors in result.values():
        all_correctors.update(correctors)

    for cid in list(result.keys()):
        own_text = lessons.get(cid, {}).get("text", "")

        # Self-declares as superseded/retracted/archived → genuinely falsified
        if re.search(
            r"^<!--\s*(?:SUPERSEDED|ARCHIVED)"
            r"|^\s*SUPERSEDED"
            r"|\[SUPERSEDED"
            r"|retracted",
            own_text,
            re.IGNORECASE | re.MULTILINE,
        ):
            continue  # keep in list

        # Explicitly says "falsified/superseded by L-NNN" → genuinely falsified
        if re.search(
            r"(?:falsified|superseded|replaced)\s+by\s+L-\d+",
            own_text,
            re.IGNORECASE,
        ):
            continue  # keep in list

        # In the known seed → keep
        if cid in _KNOWN_FALSIFICATIONS:
            continue

        # If the lesson itself reports falsification of something else
        # (e.g., "predictions FALSIFIED", "hypothesis FALSIFIED", "X FALSIFIED"),
        # it's a corrector — not falsified.
        if re.search(
            r"(?:predictions?|hypothesis|model|claim)\s+FALSIFIED",
            own_text,
        ):
            del result[cid]
            continue

        # If it's known as a corrector elsewhere and doesn't self-declare, remove it
        if cid in all_correctors:
            del result[cid]
            continue

        # Default: no self-declaration found. The lesson was flagged by
        # context-matching (L-NNN near FALSIFIED/SUPERSEDED in another lesson's
        # text about something else). Require positive self-declaration to
        # confirm falsification. Without it, remove as false positive.
        # (S405 audit: 60% FP rate without this guard — L-879)
        del result[cid]

    return result


def _classify_citation_type(
    citer_text: str,
    citer_refs: set[str],
    citer_cites_header: list[str],
    falsified_lid: str,
    falsified_title: str,
) -> str:
    """Classify how a citer uses a falsified lesson (L-739 taxonomy).

    Returns: 'content_dependent' | 'structural' | 'citation_only'
    """
    # Citation-only: appears only in metadata header (before first ## section)
    # Structural fix: strip all lines before first ## heading instead of enumerating prefixes (L-601 decay prevention)
    citer_lines = citer_text.splitlines()
    first_section = next((i for i, l in enumerate(citer_lines) if l.startswith("## ")), None)
    body_without_header = "\n".join(citer_lines[first_section:]) if first_section is not None else citer_text

    ref_in_body = bool(re.search(rf"\b{re.escape(falsified_lid)}\b", body_without_header))

    if not ref_in_body:
        return "citation_only"

    # Content-dependent: references specific falsified claims
    # Extract key claim words from the falsified title
    claim_keywords = set()
    for word in re.findall(r"\b[a-z]{4,}\b", falsified_title.lower()):
        if word not in {"lesson", "from", "that", "this", "with", "about", "into",
                        "does", "what", "when", "where", "which", "more", "than",
                        "also", "have", "been", "were", "they", "their", "there"}:
            claim_keywords.add(word)

    # Check if citer uses 2+ claim keywords from the falsified lesson's title
    citer_lower = citer_text.lower()
    keyword_hits = sum(1 for kw in claim_keywords if kw in citer_lower)

    if keyword_hits >= 2:
        return "content_dependent"

    return "structural"


def _find_correction_gaps(
    lessons: dict[str, dict],
    cited_by: dict[str, set[str]],
    classify: bool = True,
) -> list[dict]:
    """Find lessons that cite falsified content without acknowledging corrections."""
    falsified_map = _detect_falsified_lessons(lessons)
    gaps = []

    for falsified_lid, correctors in sorted(falsified_map.items()):
        if falsified_lid not in lessons:
            continue

        citers = cited_by.get(falsified_lid, set())
        uncorrected = []
        classifications: dict[str, str] = {}

        # Detect if falsified lesson is SUPERSEDED (L-752: 100% content-dependent)
        falsified_text = lessons[falsified_lid]["text"]
        is_superseded = bool(re.search(
            r"(?:SUPERSEDED|superseded\s+by\s+L-\d+|\[SUPERSEDED)",
            falsified_text,
            re.IGNORECASE,
        ))

        for citer in sorted(citers):
            if citer == falsified_lid:
                continue
            if citer in correctors:
                continue

            citer_data = lessons.get(citer, {})
            citer_refs = citer_data.get("all_refs", set())
            citer_text = citer_data.get("text", "")

            # Check if citer acknowledges the correction
            acknowledges = False
            # 1. Does citer cite any of the correcting lessons?
            if citer_refs & correctors:
                acknowledges = True
            # 2. Does citer mention falsification of the target?
            if re.search(
                rf"{re.escape(falsified_lid)}.*?(?:falsif|supersed|wrong|correct)",
                citer_text,
                re.IGNORECASE,
            ):
                acknowledges = True

            if not acknowledges:
                uncorrected.append(citer)
                if classify:
                    if is_superseded:
                        # SUPERSEDED→AUTO-HIGH (F-IC1 item 2, L-752):
                        # superseded chains are 100% content-dependent
                        classifications[citer] = "content_dependent"
                    else:
                        classifications[citer] = _classify_citation_type(
                            citer_text,
                            citer_refs,
                            citer_data.get("cites_header", []),
                            falsified_lid,
                            lessons[falsified_lid]["title"],
                        )

        if uncorrected:
            gap = {
                "falsified": falsified_lid,
                "falsified_title": lessons[falsified_lid]["title"][:80],
                "correctors": sorted(correctors),
                "total_citers": len(citers),
                "uncorrected_citers": uncorrected,
                "uncorrected_count": len(uncorrected),
                "correction_rate": round(
                    1 - len(uncorrected) / max(len(citers), 1), 3
                ),
            }
            if classify:
                gap["citation_types"] = classifications
                gap["content_dependent"] = [
                    c for c, t in classifications.items() if t == "content_dependent"
                ]
                gap["structural"] = [
                    c for c, t in classifications.items() if t == "structural"
                ]
                gap["citation_only"] = [
                    c for c, t in classifications.items() if t == "citation_only"
                ]
            gaps.append(gap)

    return sorted(gaps, key=lambda g: -g["uncorrected_count"])


def run_analysis(session: str = "S393", classify: bool = True) -> dict:
    """Run full correction propagation analysis."""
    lessons = _parse_lessons()
    cited_by = _build_citation_graph(lessons)
    falsified_map = _detect_falsified_lessons(lessons)
    gaps = _find_correction_gaps(lessons, cited_by, classify=classify)

    total_gaps = sum(g["uncorrected_count"] for g in gaps)
    total_falsified_detected = len(falsified_map)
    total_with_gaps = len(gaps)
    avg_correction_rate = (
        sum(g["correction_rate"] for g in gaps) / len(gaps)
        if gaps else 1.0
    )

    result = {
        "session": session,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "frontier": "F-IC1",
        "version": "v2-directional",
        "total_lessons": len(lessons),
        "total_falsified_detected": total_falsified_detected,
        "falsified_ids": sorted(falsified_map.keys()),
        "total_falsified_with_gaps": total_with_gaps,
        "total_uncorrected_citations": total_gaps,
        "avg_correction_rate": round(avg_correction_rate, 3),
        "gaps": gaps,
        "correction_queue": [
            {
                "citer": citer,
                "needs_correction_about": g["falsified"],
                "correctors_to_cite": g["correctors"],
                "citation_type": g.get("citation_types", {}).get(citer, "unknown"),
                "priority": (
                    "HIGH" if g.get("citation_types", {}).get(citer) == "content_dependent"
                    else "LOW" if g.get("citation_types", {}).get(citer) == "citation_only"
                    else "MEDIUM"
                ),
            }
            for g in gaps
            for citer in g["uncorrected_citers"]
        ][:50],
    }
    return result


def print_report(result: dict) -> None:
    """Human-readable correction propagation report."""
    print(f"=== CORRECTION PROPAGATION ANALYSIS — {result['session']} "
          f"({result.get('version', 'v1')}) ===\n")
    print(f"Total lessons: {result['total_lessons']}")
    print(f"Falsified lessons detected: {result['total_falsified_detected']} "
          f"({', '.join(result.get('falsified_ids', []))})")
    print(f"Falsified with uncorrected citers: {result['total_falsified_with_gaps']}")
    print(f"Total uncorrected citations: {result['total_uncorrected_citations']}")
    print(f"Average correction rate: {result['avg_correction_rate']:.0%}\n")

    for g in result["gaps"]:
        print(f"  {g['falsified']} ({g['falsified_title']})")
        print(f"    Correctors: {', '.join(g['correctors'])}")
        print(f"    Citers: {g['total_citers']} total, {g['uncorrected_count']} uncorrected")
        print(f"    Correction rate: {g['correction_rate']:.0%}")
        if "citation_types" in g:
            ct = g["citation_types"]
            content = [c for c, t in ct.items() if t == "content_dependent"]
            structural = [c for c, t in ct.items() if t == "structural"]
            citation_only = [c for c, t in ct.items() if t == "citation_only"]
            print(f"    Types: {len(content)} content-dependent, "
                  f"{len(structural)} structural, {len(citation_only)} citation-only")
            if content:
                print(f"    NEEDS FIX: {', '.join(content)}")
        else:
            print(f"    Uncorrected: {', '.join(g['uncorrected_citers'][:10])}")
            if len(g["uncorrected_citers"]) > 10:
                print(f"      ... and {len(g['uncorrected_citers']) - 10} more")
        print()

    queue = result.get("correction_queue", [])
    high_priority = [q for q in queue if q.get("priority") == "HIGH"]
    print(f"--- Correction queue: {len(queue)} total, {len(high_priority)} HIGH priority ---")
    for item in queue[:20]:
        prio = item.get("priority", "?")
        ctype = item.get("citation_type", "?")
        print(f"  [{prio}] {item['citer']} ← {item['needs_correction_about']} "
              f"({ctype})")


if __name__ == "__main__":
    save = "--save" in sys.argv
    as_json = "--json" in sys.argv or save
    classify = "--no-classify" not in sys.argv  # always-on by default (L-904)

    # Auto-detect session from git log
    session = "S393"
    try:
        import subprocess
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        m = re.search(r"\[S(\d+)\]", log.stdout)
        if m:
            session = f"S{int(m.group(1)) + 1}"
    except Exception:
        pass

    result = run_analysis(session=session, classify=classify)

    if as_json:
        output = json.dumps(result, indent=2)
        if save:
            out_path = (
                ROOT / "experiments" / "security"
                / f"f-ic1-correction-propagation-{result['session'].lower()}.json"
            )
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output + "\n", encoding="utf-8")
            print(f"Artifact saved: {out_path}")
        else:
            print(output)
    else:
        print_report(result)
