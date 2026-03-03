#!/usr/bin/env python3
"""FM-37 defense: detect LLM self-tagging level inflation in lessons.

Checks L3+ lessons for structural evidence markers. Lessons tagged L3+
without structural markers (file changes, tool modifications, architectural
decisions) are flagged as SUSPECT inflation per L-1119.

Usage:
  python3 tools/level_inflation_check.py              # scan all L3+ lessons
  python3 tools/level_inflation_check.py --staged      # scan only staged lessons (for check.sh)
  python3 tools/level_inflation_check.py --json        # JSON output
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import json


# Structural evidence markers that distinguish L3 from L2
# L3 = "changes how the system works" (L-1119 rule)
# L2 = "identifies a pattern" or "measures something"
STRUCTURAL_VERBS = re.compile(
    r'\b(built|wired|added|created|modified|changed|refactored|replaced|'
    r'upgraded|hardened|enforced|implemented|deployed|merged|fixed|removed|'
    r'rewrote|extended|integrated)\b',
    re.IGNORECASE
)

# File path references indicating concrete changes
FILE_PATH_PATTERN = re.compile(
    r'(tools/\w+\.py|check\.sh|orient\.py|compact\.py|dispatch_\w+\.py|'
    r'beliefs/\w+\.md|SWARM\.md|CLAUDE\.md|\.claude/|pre-commit|'
    r'periodics\.json|open_lane\.py|close_lane\.py)',
    re.IGNORECASE
)

# Inflation red flags: vague architectural language without specifics
INFLATION_PATTERNS = re.compile(
    r'\b(architectural implications|systemic pattern|meta-level|'
    r'paradigm|structural insight|deep pattern|fundamental)\b',
    re.IGNORECASE
)


def parse_lesson(path):
    """Parse a lesson file and return metadata + body."""
    with open(path) as f:
        content = f.read()

    lines = content.strip().split('\n')
    title = lines[0].lstrip('# ') if lines else ''

    level_match = re.search(r'Level:\s*(L[1-5])', content)
    level = level_match.group(1) if level_match else None

    session_match = re.search(r'Session:\s*S(\d+)', content)
    session = int(session_match.group(1)) if session_match else None

    # Extract body (everything after the header section)
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('## ') and i > 0:
            body_start = i
            break
    body = '\n'.join(lines[body_start:])

    return {
        'path': path,
        'id': os.path.basename(path).replace('.md', ''),
        'title': title,
        'level': level,
        'session': session,
        'body': body,
        'full': content,
    }


def check_inflation(lesson):
    """Check a lesson for level inflation signals. Returns (suspect, reasons)."""
    if not lesson['level'] or lesson['level'] < 'L3':
        return False, []

    body = lesson['body']
    full = lesson['full']
    reasons = []

    # Check for structural verb evidence
    structural_verbs = STRUCTURAL_VERBS.findall(body)

    # Check for file path references
    file_refs = FILE_PATH_PATTERN.findall(full)

    # Check for inflation red flags
    inflation_flags = INFLATION_PATTERNS.findall(body)

    # Check for quantitative evidence (measurements, n=, %, statistics)
    quant_evidence = re.findall(r'\b(n=\d+|p[=<]\d|r[=²]|d=\d|\d+%|\d+\.\d+x)\b', body)

    # L4+ (theory/paradigm) — more lenient: needs either structural evidence
    # OR quantitative evidence OR cross-domain citations
    # L3 (architecture) — stricter: needs structural evidence per L-1119 rule
    if lesson['level'] >= 'L4':
        has_quant = len(quant_evidence) >= 2
        has_structural = len(structural_verbs) >= 1 or len(file_refs) >= 1
        cross_cites = len(re.findall(r'\bL-\d+\b', full))
        has_cross_refs = cross_cites >= 3

        if not has_structural and not has_quant and not has_cross_refs:
            reasons.append(f'L4+ without structural/quantitative/citation evidence')
    else:  # L3
        has_structural = len(structural_verbs) >= 2
        has_file_refs = len(file_refs) >= 1
        has_quant = len(quant_evidence) >= 2

        if not has_structural and not has_file_refs:
            if has_quant:
                # Measurement-heavy = probably L2, not L3
                reasons.append(f'measurement-heavy without structural changes (likely L2)')
            else:
                reasons.append(f'no structural verbs ({len(structural_verbs)}) or file refs ({len(file_refs)})')

        if inflation_flags and not has_file_refs and not has_quant:
            reasons.append(f'vague architectural language: {inflation_flags[:3]}')

    suspect = len(reasons) > 0
    return suspect, reasons


def get_staged_lessons():
    """Get list of staged lesson files."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
            capture_output=True, text=True, check=True
        )
        return [f for f in result.stdout.strip().split('\n')
                if f.startswith('memory/lessons/L-') and f.endswith('.md')
                and '/archive/' not in f and f.strip()]
    except subprocess.CalledProcessError:
        return []


def main():
    parser = argparse.ArgumentParser(description='FM-37: detect level inflation')
    parser.add_argument('--staged', action='store_true', help='Only check staged lessons')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    if args.staged:
        files = get_staged_lessons()
    else:
        files = sorted(glob.glob('memory/lessons/L-*.md'))

    results = {'total': 0, 'l3_plus': 0, 'suspect': 0, 'suspects': []}

    for f in files:
        if not os.path.exists(f):
            continue
        lesson = parse_lesson(f)
        results['total'] += 1

        if not lesson['level'] or lesson['level'] < 'L3':
            continue

        results['l3_plus'] += 1
        suspect, reasons = check_inflation(lesson)

        if suspect:
            results['suspect'] += 1
            results['suspects'].append({
                'id': lesson['id'],
                'level': lesson['level'],
                'title': lesson['title'][:80],
                'reasons': reasons,
            })

    if args.json:
        print(json.dumps(results, indent=2))
        return

    # Human-readable output
    pct = (results['suspect'] / results['l3_plus'] * 100) if results['l3_plus'] > 0 else 0
    print(f"=== FM-37 Level Inflation Check ===")
    print(f"Scanned: {results['total']} lessons, {results['l3_plus']} L3+")
    print(f"Suspect: {results['suspect']} ({pct:.1f}%)")

    if results['suspects']:
        print(f"\nSUSPECT L3+ lessons (no structural evidence):")
        for s in results['suspects'][:20]:
            print(f"  {s['id']} ({s['level']}): {s['reasons'][0]}")

    # Exit code for check.sh integration
    if args.staged and results['suspect'] > 0:
        print(f"\nNOTICE: {results['suspect']} staged L3+ lesson(s) lack structural evidence (FM-37)")
        sys.exit(0)  # NOTICE level, not blocking


if __name__ == '__main__':
    main()
