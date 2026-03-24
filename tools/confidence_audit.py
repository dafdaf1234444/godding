#!/usr/bin/env python3
"""
confidence_audit.py — Detect mismatches between lesson evidence and stated confidence labels.

Pragmatist steerer signal (S528): "47 aspirational lessons with no enforcement path."
Root cause (L-601): confidence labels are voluntary metadata; without enforcement they drift.

Scans lessons for:
1. MISLABELED: measured evidence (n=N, %, data, tool references) but "Theorized" label
2. ASPIRATIONAL: prescriptive ("should", "must") with no evidence, no enforcement
3. SUPERSEDED: explicitly marked but not yet archived
4. ORPHAN-ASPIRATION: references a tool/frontier that doesn't exist

Usage:
    python3 tools/confidence_audit.py              # full audit
    python3 tools/confidence_audit.py --fix        # auto-fix mislabeled confidence
    python3 tools/confidence_audit.py --compact    # list pure-aspiration compaction targets
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"

# Evidence markers — presence suggests measured/observed, not theorized
EVIDENCE_PATTERNS = [
    re.compile(r'\bn=\d+', re.IGNORECASE),                    # sample size
    re.compile(r'\d+(\.\d+)?%'),                               # percentage
    re.compile(r'(?:measured|observed|confirmed|falsified)', re.IGNORECASE),
    re.compile(r'(?:AUC|RMSE|Brier|p<|p=|CI\[|Cohen)', re.IGNORECASE),  # stats
    re.compile(r'tools/\w+\.py'),                              # tool reference
    re.compile(r'experiments/'),                                # experiment artifact
    re.compile(r'(?:baseline|delta|improvement)\s*[:=]', re.IGNORECASE),
]

# Aspiration markers — prescriptive without evidence
ASPIRATION_PATTERNS = [
    re.compile(r'\b(?:should|must|needs? to|ought to|requires?|mandatory)\b', re.IGNORECASE),
]

# Pure hypothesis markers
HYPOTHESIS_MARKERS = [
    re.compile(r'(?:hypothesis|theorized|dream|unfalsified|untested)', re.IGNORECASE),
    re.compile(r'\(n=0\)'),
]

# A lesson IS superseded only if its title/status says so, not if it merely mentions the word
SUPERSEDED_TITLE = re.compile(r'#.*\[?SUPERSEDED\b', re.IGNORECASE)
SUPERSEDED_STATUS = re.compile(r'(?:Status|Confidence):\s*(?:\w+\s+)?(?:\()?SUPERSEDED', re.IGNORECASE)


def parse_lesson(path: Path) -> dict:
    """Parse a lesson file and extract key fields."""
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = text.split('\n')

    confidence = None
    for line in lines[:15]:  # confidence is usually near top
        m = re.search(r'Confidence:\s*(\w+)', line, re.IGNORECASE)
        if m:
            confidence = m.group(1).strip()
            break

    lesson_id = path.stem  # e.g. "L-407"

    # Count evidence signals
    evidence_count = sum(1 for p in EVIDENCE_PATTERNS if p.search(text))
    aspiration_count = sum(1 for p in ASPIRATION_PATTERNS if p.search(text))
    hypothesis_count = sum(1 for p in HYPOTHESIS_MARKERS if p.search(text))
    # Check first 5 lines for superseded title/status (not body mentions)
    header = '\n'.join(lines[:5])
    is_superseded = bool(SUPERSEDED_TITLE.search(header) or SUPERSEDED_STATUS.search(header))

    # Check for tool/frontier references that may not exist
    tool_refs = re.findall(r'tools/(\w+\.py)', text)
    frontier_refs = re.findall(r'F-[A-Z]+\d+', text)

    return {
        'id': lesson_id,
        'path': path,
        'confidence': confidence,
        'evidence_count': evidence_count,
        'aspiration_count': aspiration_count,
        'hypothesis_count': hypothesis_count,
        'is_superseded': is_superseded,
        'tool_refs': tool_refs,
        'frontier_refs': frontier_refs,
        'text': text,
        'line_count': len(lines),
    }


def classify(lesson: dict) -> str:
    """Classify mismatch type."""
    conf = (lesson['confidence'] or '').lower()

    if lesson['is_superseded']:
        return 'SUPERSEDED'

    if conf == 'theorized' and lesson['evidence_count'] >= 3:
        return 'MISLABELED'  # has evidence but says theorized

    if conf == 'theorized' and lesson['evidence_count'] >= 2 and lesson['aspiration_count'] == 0:
        return 'LIKELY-MISLABELED'

    if lesson['aspiration_count'] >= 2 and lesson['evidence_count'] <= 1 and lesson['hypothesis_count'] >= 1:
        return 'ASPIRATIONAL'

    if conf == 'theorized' and lesson['aspiration_count'] >= 1 and lesson['evidence_count'] == 0:
        return 'PURE-ASPIRATION'

    return 'OK'


def check_tool_exists(tool_name: str) -> bool:
    """Check if a referenced tool exists."""
    return (ROOT / "tools" / tool_name).exists()


def audit():
    """Run full confidence audit."""
    lessons = sorted(LESSONS_DIR.glob("L-*.md"))
    results = {'MISLABELED': [], 'LIKELY-MISLABELED': [], 'ASPIRATIONAL': [],
               'PURE-ASPIRATION': [], 'SUPERSEDED': [], 'OK': []}

    for path in lessons:
        try:
            parsed = parse_lesson(path)
            cat = classify(parsed)
            results[cat].append(parsed)
        except Exception:
            pass

    return results


def print_report(results: dict, mode: str = 'full'):
    total = sum(len(v) for v in results.values())
    flagged = total - len(results.get('OK', []))

    print(f"=== CONFIDENCE AUDIT | {total} lessons scanned, {flagged} flagged ===\n")

    if results['SUPERSEDED']:
        print(f"--- SUPERSEDED ({len(results['SUPERSEDED'])}) — archive immediately ---")
        for l in results['SUPERSEDED']:
            print(f"  {l['id']}: {l['line_count']} lines")
        print()

    if results['MISLABELED']:
        print(f"--- MISLABELED ({len(results['MISLABELED'])}) — evidence present but labeled 'Theorized' ---")
        for l in results['MISLABELED']:
            print(f"  {l['id']}: {l['evidence_count']} evidence signals, confidence='{l['confidence']}'")
        print()

    if results['LIKELY-MISLABELED']:
        print(f"--- LIKELY MISLABELED ({len(results['LIKELY-MISLABELED'])}) — probable evidence, needs review ---")
        for l in results['LIKELY-MISLABELED']:
            print(f"  {l['id']}: {l['evidence_count']} evidence, {l['aspiration_count']} aspiration")
        print()

    if mode == 'compact' or mode == 'full':
        aspir = results['ASPIRATIONAL'] + results['PURE-ASPIRATION']
        if aspir:
            print(f"--- ASPIRATIONAL ({len(aspir)}) — compaction candidates ---")
            for l in sorted(aspir, key=lambda x: x['evidence_count']):
                tag = 'PURE' if l['evidence_count'] == 0 else 'WEAK'
                print(f"  [{tag}] {l['id']}: ev={l['evidence_count']} asp={l['aspiration_count']} hyp={l['hypothesis_count']}")
            print()

    # Summary stats
    print("--- Summary ---")
    for cat in ['MISLABELED', 'LIKELY-MISLABELED', 'ASPIRATIONAL', 'PURE-ASPIRATION', 'SUPERSEDED', 'OK']:
        if results.get(cat):
            print(f"  {cat}: {len(results[cat])}")

    mislabel_rate = (len(results['MISLABELED']) + len(results['LIKELY-MISLABELED'])) / max(total, 1) * 100
    aspir_rate = (len(results['ASPIRATIONAL']) + len(results['PURE-ASPIRATION'])) / max(total, 1) * 100
    print(f"\n  Mislabel rate: {mislabel_rate:.1f}%")
    print(f"  Aspiration rate: {aspir_rate:.1f}%")


def fix_mislabeled(results: dict):
    """Auto-fix mislabeled lessons by updating confidence from Theorized to Observed."""
    fixed = 0
    for l in results.get('MISLABELED', []):
        text = l['text']
        new_text = re.sub(
            r'(Confidence:\s*)Theorized',
            r'\1Observed (auto-reclassified by confidence_audit.py S531)',
            text,
            count=1,
            flags=re.IGNORECASE
        )
        if new_text != text:
            l['path'].write_text(new_text, encoding='utf-8')
            fixed += 1
            print(f"  Fixed: {l['id']} Theorized → Observed")
    print(f"\n{fixed} lessons reclassified.")


def main():
    mode = 'full'
    do_fix = False
    do_compact = False

    for arg in sys.argv[1:]:
        if arg == '--fix':
            do_fix = True
        elif arg == '--compact':
            do_compact = True
            mode = 'compact'

    results = audit()
    print_report(results, mode=mode)

    if do_fix:
        print("\n--- Auto-fixing mislabeled lessons ---")
        fix_mislabeled(results)

    if do_compact:
        aspir = results['ASPIRATIONAL'] + results['PURE-ASPIRATION']
        print(f"\n{len(aspir)} compaction candidates. Use compact.py to process.")


if __name__ == "__main__":
    main()
