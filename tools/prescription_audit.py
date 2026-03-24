#!/usr/bin/env python3
"""prescription_audit.py — Classify lessons as prescriptive vs descriptive,
check enforcement linkage, measure citation decay. F-EPIS1 epistemological tool.

Prescriptive lessons tell the swarm what to do ("should", "must", "avoid").
Descriptive lessons record observations ("confirmed", "measured", "found").
Dead-letter prescriptions: prescriptive + unenforced + zero incoming citations.

Usage:
  python3 tools/prescription_audit.py              # summary report
  python3 tools/prescription_audit.py --dead       # list dead-letter candidates
  python3 tools/prescription_audit.py --json       # machine-readable output
  python3 tools/prescription_audit.py --compact    # suggest compaction targets
"""
import argparse, json, os, re, sys
from pathlib import Path

LESSON_DIR = Path("memory/lessons")

# Two-threshold classification: need >=2 pattern matches to classify
PRESCRIPTIVE_PATTERNS = [
    r'\bshould\b', r'\bmust\b', r'\bneed to\b', r'\bdon.t\b', r'\bavoid\b',
    r'\balways\b', r'\bnever\b', r'\brequire', r'\bensure\b', r'\bprefer\b',
]
ENFORCEMENT_PATTERNS = [
    r'tools/', r'check\.sh', r'hook', r'contract', r'wired into', r'enforc',
    r'validate', r'\.py\b', r'pre-commit', r'automated', r'structural',
]


def load_lessons():
    lessons = {}
    for f in sorted(LESSON_DIR.iterdir()):
        if f.suffix != '.md':
            continue
        text = f.read_text(errors='replace')
        m = re.search(r'# (L-\d+)', text)
        if not m:
            continue
        lid = m.group(1)
        num = int(lid.split('-')[1])
        # Extract session
        sm = re.search(r'\bS(\d+)\b', text)
        session = int(sm.group(1)) if sm else 0
        # Extract title
        tm = re.search(r'# L-\d+:?\s*(.*)', text)
        title = tm.group(1).strip()[:80] if tm else ''
        lessons[lid] = {
            'file': f.name, 'text': text, 'num': num,
            'session': session, 'title': title,
            'lines': len(text.strip().split('\n')),
            'cited_by': 0, 'cites_out': 0,
        }
    return lessons


def build_citation_graph(lessons):
    for lid, info in lessons.items():
        refs = set(re.findall(r'L-(\d+)', info['text']))
        for ref in refs:
            ref_lid = f'L-{ref}'
            if ref_lid in lessons and ref_lid != lid:
                lessons[ref_lid]['cited_by'] += 1
                info['cites_out'] += 1


def classify(lessons):
    for lid, info in lessons.items():
        text = info['text']
        prescriptive_hits = sum(
            1 for p in PRESCRIPTIVE_PATTERNS if re.search(p, text, re.I)
        )
        enforcement_hits = sum(
            1 for p in ENFORCEMENT_PATTERNS if re.search(p, text, re.I)
        )
        info['prescriptive_score'] = prescriptive_hits
        info['enforcement_score'] = enforcement_hits
        info['is_prescriptive'] = prescriptive_hits >= 2
        info['is_enforced'] = enforcement_hits >= 2

        if info['is_prescriptive'] and info['is_enforced']:
            info['category'] = 'prescriptive_enforced'
        elif info['is_prescriptive']:
            info['category'] = 'prescriptive_unenforced'
        else:
            info['category'] = 'descriptive'

        info['is_dead_letter'] = (
            info['category'] == 'prescriptive_unenforced'
            and info['cited_by'] == 0
        )


def report_summary(lessons):
    cats = {}
    for info in lessons.values():
        cat = info['category']
        cats.setdefault(cat, []).append(info)

    total = len(lessons)
    print(f"=== PRESCRIPTION AUDIT ({total} lessons) ===\n")

    for cat in ['prescriptive_enforced', 'prescriptive_unenforced', 'descriptive']:
        items = cats.get(cat, [])
        citations = [i['cited_by'] for i in items]
        mean_c = sum(citations) / len(citations) if citations else 0
        zero_cite = sum(1 for c in citations if c == 0)
        pct = 100 * len(items) / total
        print(f"  {cat}: {len(items)} ({pct:.1f}%) — mean citations {mean_c:.2f}, zero-cite {zero_cite}")

    # Effect size: enforced vs unenforced citation difference
    enf = cats.get('prescriptive_enforced', [])
    unenf = cats.get('prescriptive_unenforced', [])
    if enf and unenf:
        mean_enf = sum(i['cited_by'] for i in enf) / len(enf)
        mean_unenf = sum(i['cited_by'] for i in unenf) / len(unenf)
        lift = (mean_enf - mean_unenf) / mean_unenf if mean_unenf > 0 else float('inf')
        print(f"\n  Citation lift (enforced vs unenforced): +{lift:.1%}")
        print(f"  Enforced mean: {mean_enf:.2f}, Unenforced mean: {mean_unenf:.2f}")

    dead = [i for i in lessons.values() if i['is_dead_letter']]
    print(f"\n  Dead letters (prescriptive + unenforced + 0 cites): {len(dead)}")
    print(f"  Dead-letter token estimate: ~{sum(i['lines'] * 8 for i in dead)} tokens")


def report_dead_letters(lessons):
    dead = [(lid, info) for lid, info in lessons.items() if info['is_dead_letter']]
    dead.sort(key=lambda x: x[1]['num'])
    print(f"=== DEAD-LETTER LESSONS ({len(dead)}) ===")
    print(f"Prescriptive, unenforced, zero incoming citations.\n")
    for lid, info in dead:
        print(f"  {lid} ({info['lines']}L, S{info['session']}): {info['title']}")


def report_compact(lessons):
    dead = [(lid, info) for lid, info in lessons.items() if info['is_dead_letter']]
    dead.sort(key=lambda x: -x[1]['lines'])
    total_lines = sum(info['lines'] for _, info in dead)
    print(f"=== COMPACTION TARGETS ({len(dead)} dead letters, ~{total_lines} lines) ===")
    print("Options: (a) add enforcement, (b) downgrade to descriptive, (c) archive\n")
    for lid, info in dead[:20]:
        print(f"  {lid} ({info['lines']}L): {info['title']}")
        # Suggest action based on content
        if info['prescriptive_score'] <= 2:
            print(f"    → Low prescriptive signal ({info['prescriptive_score']}): likely descriptive, reclassify")
        elif info['lines'] <= 12:
            print(f"    → Short ({info['lines']}L): candidate for merge into related lesson")
        else:
            print(f"    → Add enforcement or archive")


def main():
    parser = argparse.ArgumentParser(description='Prescription audit for lessons')
    parser.add_argument('--dead', action='store_true', help='List dead-letter lessons')
    parser.add_argument('--compact', action='store_true', help='Suggest compaction targets')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    lessons = load_lessons()
    build_citation_graph(lessons)
    classify(lessons)

    if args.json:
        out = {}
        for lid, info in lessons.items():
            out[lid] = {
                'category': info['category'],
                'is_dead_letter': info['is_dead_letter'],
                'cited_by': info['cited_by'],
                'prescriptive_score': info['prescriptive_score'],
                'enforcement_score': info['enforcement_score'],
                'session': info['session'],
                'title': info['title'],
            }
        json.dump(out, sys.stdout, indent=2)
    elif args.dead:
        report_dead_letters(lessons)
    elif args.compact:
        report_compact(lessons)
    else:
        report_summary(lessons)


if __name__ == '__main__':
    main()
