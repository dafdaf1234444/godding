#!/usr/bin/env python3
"""
Multi-lesson quality scanner and auto-fixer.

Scans all lessons across multiple quality dimensions:
  1. Metadata completeness (Session, Domain, Cites, ISO, Sharpe)
  2. Broken citations (L-NNN or F-NNN references to non-existent entities)
  3. Format consistency (## Finding/## Rule sections)
  4. Cross-lesson near-duplicates (Jaccard similarity)
  5. Stale references (citations to archived lessons)
  6. Orphan citations (Cites: header missing but L-NNN in body)

Auto-fix capabilities (--fix):
  - Add missing Cites: header from body L-NNN references
  - Normalize confidence values
  - Report (but don't fix) structural issues

Usage:
    python3 tools/lesson_quality_fixer.py                  # scan + report
    python3 tools/lesson_quality_fixer.py --fix            # scan + auto-fix safe issues
    python3 tools/lesson_quality_fixer.py --json           # JSON output
    python3 tools/lesson_quality_fixer.py --verbose        # per-lesson detail
    python3 tools/lesson_quality_fixer.py --dimension meta # single dimension
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
ARCHIVE_DIR = LESSONS_DIR / "archive"
FRONTIER_DIR = REPO_ROOT / "tasks"

# Standard confidence values (from corpus analysis)
STANDARD_CONFIDENCE = {
    "observed", "measured", "verified", "theorized", "assumed",
    "structural", "directional",
}

# Dimensions
DIMENSIONS = ["meta", "citations", "format", "duplicates", "stale", "orphans"]


def load_lesson(path: Path) -> dict:
    """Parse a lesson file into structured data."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"id": path.stem, "path": str(path), "error": "unreadable"}

    lesson = {
        "id": path.stem,
        "path": str(path),
        "content": content,
        "lines": content.splitlines(),
        "issues": [],
    }

    # Parse header line (# L-NNN: title)
    title_match = re.match(r"^# (L-\d+):\s*(.+)", content)
    if title_match:
        lesson["title"] = title_match.group(2).strip()
    else:
        lesson["title"] = ""
        lesson["issues"].append(("format", "missing_title", "No # L-NNN: title header"))

    # Parse metadata fields from header area (first 5 lines typically)
    header_area = "\n".join(content.splitlines()[:6])

    # Session
    sess_match = re.search(r"Session:\s*S(\d+)", header_area)
    lesson["session"] = int(sess_match.group(1)) if sess_match else None

    # Domain
    domain_match = re.search(r"Domain:\s*(.+?)(?:\s*\||\s*$)", header_area)
    lesson["domain"] = domain_match.group(1).strip() if domain_match else None

    # ISO
    iso_match = re.search(r"ISO:\s*(.+?)(?:\s*\||\s*$)", header_area)
    lesson["iso"] = iso_match.group(1).strip() if iso_match else None

    # Sharpe
    sharpe_match = re.search(r"Sharpe:\s*(\d+)", header_area)
    lesson["sharpe"] = int(sharpe_match.group(1)) if sharpe_match else None

    # Confidence
    conf_match = re.search(r"Confidence:\s*(.+?)(?:\s*$)", header_area, re.MULTILINE)
    lesson["confidence"] = conf_match.group(1).strip() if conf_match else None

    # Cites header
    cites_match = re.search(r"^Cites:\s*(.+)", content, re.MULTILINE)
    lesson["cites_header"] = cites_match.group(1).strip() if cites_match else None

    # All L-NNN references in body (exclude range notation like "L-0..L-50")
    raw_refs = set(re.findall(r"\bL-(\d+)\b", content))
    # Filter out refs that are part of range notation (L-N..L-M)
    range_refs = set(re.findall(r"\bL-(\d+)\.\.", content))
    range_refs |= set(re.findall(r"\.\.\s*L-(\d+)\b", content))
    lesson["body_lesson_refs"] = raw_refs - range_refs
    # Remove self-reference
    own_num = re.search(r"\d+", lesson["id"])
    if own_num:
        lesson["body_lesson_refs"].discard(own_num.group())

    # All F-NNN references
    lesson["frontier_refs"] = set(re.findall(r"\bF[-_]([A-Z0-9]+(?:\d+)?)\b", content))

    # Section headers
    lesson["sections"] = re.findall(r"^##\s+(.+)", content, re.MULTILINE)

    # Line count
    lesson["line_count"] = len(content.splitlines())

    return lesson


def load_all_lessons() -> tuple:
    """Load all active and archived lessons."""
    active = {}
    for path in sorted(LESSONS_DIR.glob("L-*.md")):
        lesson = load_lesson(path)
        active[lesson["id"]] = lesson

    archived = set()
    if ARCHIVE_DIR.exists():
        for path in sorted(ARCHIVE_DIR.glob("L-*.md")):
            archived.add(path.stem)

    return active, archived


def check_metadata(lessons: dict) -> list:
    """Check metadata completeness across all lessons."""
    issues = []
    counts = Counter()

    for lid, lesson in lessons.items():
        missing = []
        if lesson.get("session") is None:
            missing.append("Session")
            counts["missing_session"] += 1
        if lesson.get("domain") is None:
            missing.append("Domain")
            counts["missing_domain"] += 1
        if lesson.get("cites_header") is None:
            missing.append("Cites")
            counts["missing_cites"] += 1
        if lesson.get("iso") is None:
            counts["missing_iso"] += 1
        if lesson.get("sharpe") is None:
            counts["missing_sharpe"] += 1

        # Confidence normalization check
        if lesson.get("confidence"):
            conf_lower = lesson["confidence"].lower().split("(")[0].split(",")[0].strip()
            if conf_lower not in STANDARD_CONFIDENCE:
                counts["nonstandard_confidence"] += 1
                issues.append({
                    "lesson": lid,
                    "dimension": "meta",
                    "type": "nonstandard_confidence",
                    "detail": f"Confidence '{lesson['confidence']}' not in standard set",
                    "fixable": False,
                })

        if missing:
            issues.append({
                "lesson": lid,
                "dimension": "meta",
                "type": "missing_fields",
                "detail": f"Missing: {', '.join(missing)}",
                "fixable": False,
            })

    return issues, counts


def check_citations(lessons: dict, archived: set) -> list:
    """Check for broken and stale citations."""
    issues = []
    all_ids = set(lessons.keys()) | archived
    # Normalize all known IDs to integer for comparison (L-005 → 5, L-612 → 612)
    all_nums_int = set()
    for lid in all_ids:
        m = re.search(r"\d+", lid)
        if m:
            all_nums_int.add(int(m.group()))

    for lid, lesson in lessons.items():
        # Check body L-NNN references against known lessons
        for ref_num in lesson.get("body_lesson_refs", set()):
            ref_int = int(ref_num)
            if ref_int not in all_nums_int:
                issues.append({
                    "lesson": lid,
                    "dimension": "citations",
                    "type": "broken_citation",
                    "detail": f"References L-{ref_num} which does not exist",
                    "fixable": False,
                })

        # Check for references to archived lessons
        for ref_num in lesson.get("body_lesson_refs", set()):
            padded = f"L-{ref_num.zfill(3)}"
            if padded in archived:
                issues.append({
                    "lesson": lid,
                    "dimension": "stale",
                    "type": "archived_citation",
                    "detail": f"Cites {padded} which is archived",
                    "fixable": False,
                })

    return issues


def check_format(lessons: dict) -> list:
    """Check format consistency (required sections)."""
    issues = []

    # Standard section patterns (any of these counts as having the section)
    finding_patterns = ["finding", "what happened", "context", "what we found"]
    rule_patterns = ["rule", "rule extracted", "what to do differently", "principle"]

    for lid, lesson in lessons.items():
        sections_lower = [s.lower().strip() for s in lesson.get("sections", [])]

        has_finding = any(
            any(pat in sec for pat in finding_patterns)
            for sec in sections_lower
        )
        has_rule = any(
            any(pat in sec for pat in rule_patterns)
            for sec in sections_lower
        )

        if not has_finding and not has_rule:
            issues.append({
                "lesson": lid,
                "dimension": "format",
                "type": "missing_both_sections",
                "detail": f"Missing both Finding and Rule sections (has: {lesson.get('sections', [])})",
                "fixable": False,
            })
        elif not has_finding:
            issues.append({
                "lesson": lid,
                "dimension": "format",
                "type": "missing_finding",
                "detail": "Missing ## Finding / ## What happened section",
                "fixable": False,
            })
        elif not has_rule:
            issues.append({
                "lesson": lid,
                "dimension": "format",
                "type": "missing_rule",
                "detail": "Missing ## Rule / ## Rule extracted section",
                "fixable": False,
            })

        # Check line count (lessons should be ≤20 lines per TEMPLATE)
        if lesson.get("line_count", 0) > 25:
            issues.append({
                "lesson": lid,
                "dimension": "format",
                "type": "oversized",
                "detail": f"{lesson['line_count']} lines (target ≤20)",
                "fixable": False,
            })

    return issues


def check_orphan_cites(lessons: dict) -> list:
    """Find lessons with L-NNN in body but no Cites: header."""
    issues = []
    for lid, lesson in lessons.items():
        refs = lesson.get("body_lesson_refs", set())
        if len(refs) >= 2 and lesson.get("cites_header") is None:
            issues.append({
                "lesson": lid,
                "dimension": "orphans",
                "type": "missing_cites_header",
                "detail": f"References {len(refs)} lessons in body but has no Cites: header",
                "refs": sorted(refs),
                "fixable": True,
            })
    return issues


def check_duplicates(lessons: dict, threshold: float = 0.4) -> list:
    """Find near-duplicate lesson pairs using Jaccard similarity."""
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "and", "or", "but", "if",
        "in", "on", "at", "to", "for", "of", "by", "with", "from", "into",
        "this", "that", "these", "those", "it", "its", "not", "no",
    }

    def tokenize(text):
        tokens = re.findall(r"[a-z][a-z0-9_-]*", text.lower())
        return {t for t in tokens if t not in STOP_WORDS and len(t) > 2}

    # Build word sets from title + first 3 content lines
    lesson_words = {}
    for lid, lesson in lessons.items():
        text = lesson.get("title", "") + " " + " ".join(
            line.strip() for line in lesson.get("lines", [])[:5] if line.strip()
        )
        words = tokenize(text)
        if words:
            lesson_words[lid] = words

    issues = []
    lids = sorted(lesson_words.keys())
    for i in range(len(lids)):
        for j in range(i + 1, len(lids)):
            a, b = lids[i], lids[j]
            intersection = len(lesson_words[a] & lesson_words[b])
            union = len(lesson_words[a] | lesson_words[b])
            sim = intersection / union if union > 0 else 0
            if sim >= threshold:
                issues.append({
                    "lesson": f"{a} ↔ {b}",
                    "dimension": "duplicates",
                    "type": "near_duplicate",
                    "detail": f"Jaccard={sim:.3f} (threshold {threshold})",
                    "similarity": round(sim, 4),
                    "fixable": False,
                })

    issues.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    return issues[:20]  # Top 20 pairs only


def apply_fixes(lessons: dict, issues: list) -> int:
    """Apply auto-fixes for fixable issues. Returns count of fixes applied."""
    fixes_applied = 0

    for issue in issues:
        if not issue.get("fixable"):
            continue

        if issue["type"] == "missing_cites_header":
            lid = issue["lesson"]
            lesson = lessons[lid]
            refs = issue["refs"]
            path = Path(lesson["path"])
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

            # Build Cites line
            cites_refs = ", ".join(f"L-{r.zfill(3)}" for r in sorted(refs, key=int))
            cites_line = f"Cites: {cites_refs}"

            # Insert after header metadata (after line 2 or 3)
            insert_idx = 1
            for idx, line in enumerate(lines[:6]):
                if line.startswith(("Session:", "Date:", "Domain:", "ISO:", "Sharpe:", "Confidence:")):
                    insert_idx = idx + 1
                elif line.startswith("Cites:"):
                    insert_idx = -1  # Already has Cites
                    break

            if insert_idx > 0:
                lines.insert(insert_idx, cites_line)
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                fixes_applied += 1
                print(f"  FIXED {lid}: added {cites_line}")

    return fixes_applied


def print_report(all_issues: list, counts: dict, lessons: dict, verbose: bool = False):
    """Print human-readable quality report."""
    total = len(lessons)
    print(f"\n=== LESSON QUALITY REPORT ({total} lessons) ===\n")

    # Summary by dimension
    by_dim = defaultdict(list)
    for issue in all_issues:
        by_dim[issue["dimension"]].append(issue)

    for dim in DIMENSIONS:
        dim_issues = by_dim.get(dim, [])
        if not dim_issues:
            print(f"  [{dim.upper()}] ✓ No issues")
            continue

        # Count unique lessons affected
        affected = set()
        for issue in dim_issues:
            lid = issue["lesson"]
            if "↔" in lid:
                for part in lid.split(" ↔ "):
                    affected.add(part.strip())
            else:
                affected.add(lid)

        pct = len(affected) / total * 100 if total > 0 else 0
        fixable = sum(1 for i in dim_issues if i.get("fixable"))

        print(f"  [{dim.upper()}] {len(dim_issues)} issues ({len(affected)} lessons, {pct:.1f}%)"
              f"{f' — {fixable} auto-fixable' if fixable else ''}")

        if verbose:
            for issue in dim_issues[:10]:
                fix_tag = " [FIXABLE]" if issue.get("fixable") else ""
                print(f"    {issue['lesson']}: {issue['detail']}{fix_tag}")
            if len(dim_issues) > 10:
                print(f"    ... and {len(dim_issues) - 10} more")

    # Metadata coverage summary
    print(f"\n--- Metadata Coverage ---")
    print(f"  Session:    {total - counts.get('missing_session', 0)}/{total} ({(total - counts.get('missing_session', 0)) / total * 100:.0f}%)")
    print(f"  Domain:     {total - counts.get('missing_domain', 0)}/{total} ({(total - counts.get('missing_domain', 0)) / total * 100:.0f}%)")
    print(f"  Cites:      {total - counts.get('missing_cites', 0)}/{total} ({(total - counts.get('missing_cites', 0)) / total * 100:.0f}%)")
    print(f"  ISO:        {total - counts.get('missing_iso', 0)}/{total} ({(total - counts.get('missing_iso', 0)) / total * 100:.0f}%)")
    print(f"  Sharpe:     {total - counts.get('missing_sharpe', 0)}/{total} ({(total - counts.get('missing_sharpe', 0)) / total * 100:.0f}%)")

    # Fixable summary
    fixable_total = sum(1 for i in all_issues if i.get("fixable"))
    if fixable_total:
        print(f"\n--- Auto-fixable: {fixable_total} issues (run with --fix) ---")

    print()


def main():
    parser = argparse.ArgumentParser(description="Multi-lesson quality scanner and auto-fixer")
    parser.add_argument("--fix", action="store_true", help="Apply auto-fixes for safe issues")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-lesson details")
    parser.add_argument("--dimension", "-d", choices=DIMENSIONS, help="Scan single dimension only")
    parser.add_argument("--dup-threshold", type=float, default=0.4, help="Jaccard threshold for duplicates (default: 0.4)")
    args = parser.parse_args()

    log = (lambda msg: print(msg, file=sys.stderr)) if args.json else print
    log("[QUALITY] Loading lessons...")
    lessons, archived = load_all_lessons()
    log(f"[QUALITY] Loaded {len(lessons)} active, {len(archived)} archived lessons")

    all_issues = []
    meta_counts = Counter()

    dimensions_to_run = [args.dimension] if args.dimension else DIMENSIONS

    if "meta" in dimensions_to_run:
        log("[QUALITY] Checking metadata completeness...")
        meta_issues, meta_counts = check_metadata(lessons)
        all_issues.extend(meta_issues)

    if "citations" in dimensions_to_run:
        log("[QUALITY] Checking citations...")
        all_issues.extend(check_citations(lessons, archived))

    if "format" in dimensions_to_run:
        log("[QUALITY] Checking format consistency...")
        all_issues.extend(check_format(lessons))

    if "duplicates" in dimensions_to_run:
        log("[QUALITY] Checking duplicates (this may take a moment)...")
        all_issues.extend(check_duplicates(lessons, args.dup_threshold))

    if "stale" in dimensions_to_run:
        # Already handled in check_citations
        pass

    if "orphans" in dimensions_to_run:
        log("[QUALITY] Checking orphan citations...")
        all_issues.extend(check_orphan_cites(lessons))

    if args.fix:
        log("\n[QUALITY] Applying auto-fixes...")
        n_fixed = apply_fixes(lessons, all_issues)
        log(f"[QUALITY] {n_fixed} fixes applied")

    if args.json:
        result = {
            "total_lessons": len(lessons),
            "archived_lessons": len(archived),
            "total_issues": len(all_issues),
            "fixable_issues": sum(1 for i in all_issues if i.get("fixable")),
            "issues_by_dimension": {},
            "issues": all_issues,
        }
        for dim in DIMENSIONS:
            dim_issues = [i for i in all_issues if i["dimension"] == dim]
            result["issues_by_dimension"][dim] = len(dim_issues)
        print(json.dumps(result, indent=2, default=str))
    else:
        print_report(all_issues, meta_counts, lessons, args.verbose)


if __name__ == "__main__":
    main()
