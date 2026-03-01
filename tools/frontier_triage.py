#!/usr/bin/env python3
"""Frontier triage: classify anxiety-zone frontiers for KEEP/ABANDON/MERGE/RESOLVE.

Usage: python3 tools/frontier_triage.py [--json] [--threshold N]

Reads tasks/FRONTIER.md + domain frontiers, cross-references against:
- Citation count in lessons (is the frontier actively referenced?)
- Related frontier resolution status
- Age since last update
- Whether test criteria exist and are measurable

Outputs triage recommendations and optionally a JSON artifact.
"""
import re
import os
import sys
import json
import glob
from datetime import datetime

CURRENT_SESSION = 386
ANXIETY_THRESHOLD = 15  # sessions without update


def parse_frontiers(filepath):
    """Parse frontier entries from a FRONTIER.md file."""
    frontiers = []
    with open(filepath) as f:
        content = f.read()

    # Split by frontier entries
    lines = content.split('\n')
    current_entry = None
    current_text = []
    section = None

    for line in lines:
        # Track section
        if line.startswith('## Critical'):
            section = 'critical'
        elif line.startswith('## Important'):
            section = 'important'
        elif line.startswith('## Exploratory'):
            section = 'exploratory'
        elif line.startswith('## Domain'):
            section = 'domain'
        elif line.startswith('## Archive') or line.startswith('## Resolved'):
            section = 'archive'

        m = re.match(r'[-*\s]*\*\*(F[-\w]*\d+[-\w]*)\*\*:?\s*(.*)', line)
        if m:
            # Save previous entry
            if current_entry:
                current_entry['text'] = '\n'.join(current_text)
                frontiers.append(current_entry)

            fid = m.group(1)
            rest = m.group(2)

            # Extract sessions
            sessions = [int(s) for s in re.findall(r'S(\d+)', rest)]
            last_session = max(sessions) if sessions else 0

            # Extract status
            status_match = re.search(
                r'(RESOLVED|FALSIFIED|CONFIRMED|PARTIALLY CONFIRMED|'
                r'PARTIAL\+*|ADVANCED|OPEN|BASELINE)', rest)
            status = status_match.group(1) if status_match else 'UNKNOWN'

            # Extract related frontiers
            related = re.findall(r'F[-\w]+', rest)
            related = [r for r in related if r != fid]

            current_entry = {
                'id': fid,
                'last_session': last_session,
                'status': status,
                'age': CURRENT_SESSION - last_session if last_session > 0 else 999,
                'section': section,
                'related': related,
                'source': filepath,
                'preview': rest[:200],
            }
            current_text = [line]
        elif current_entry:
            current_text.append(line)

    if current_entry:
        current_entry['text'] = '\n'.join(current_text)
        frontiers.append(current_entry)

    return frontiers


def count_frontier_citations(fid):
    """Count how many lesson files reference this frontier ID."""
    count = 0
    recent_count = 0  # in last 50 lessons
    lesson_dir = 'memory/lessons'
    if not os.path.isdir(lesson_dir):
        return 0, 0

    for fname in os.listdir(lesson_dir):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(lesson_dir, fname)
        try:
            with open(fpath) as f:
                text = f.read()
            if fid in text:
                count += 1
                # Check if recent lesson
                lnum = re.search(r'L-(\d+)', fname)
                if lnum and int(lnum.group(1)) > 630:  # ~last 50
                    recent_count += 1
        except Exception:
            pass
    return count, recent_count


def has_test_criteria(text):
    """Check if the frontier entry has measurable test criteria."""
    indicators = ['target', 'threshold', 'measure', 'test:', 'baseline',
                  'success:', 'hypothesis', 'design:', 'metric:',
                  'open:', 'instrument:']
    text_lower = text.lower()
    matches = sum(1 for ind in indicators if ind in text_lower)
    return matches >= 2


def has_artifact(text):
    """Check if frontier references an experiment artifact."""
    return bool(re.search(r'(experiments/|artifact:|\.json)', text, re.IGNORECASE))


def classify_frontier(f, resolved_ids):
    """Classify a frontier into KEEP/ABANDON/MERGE/RESOLVE."""
    reasons = []
    score = 0  # positive = keep, negative = abandon

    age = f['age']
    status = f['status']
    text = f.get('text', '')

    # Age factor
    if age > 200:
        score -= 3
        reasons.append(f'extremely stale (age={age})')
    elif age > 100:
        score -= 2
        reasons.append(f'very stale (age={age})')
    elif age > 50:
        score -= 1
        reasons.append(f'stale (age={age})')

    # Citation count
    total_cites, recent_cites = count_frontier_citations(f['id'])
    f['total_citations'] = total_cites
    f['recent_citations'] = recent_cites

    if recent_cites > 0:
        score += 2
        reasons.append(f'recently cited ({recent_cites} recent)')
    elif total_cites > 2:
        score += 1
        reasons.append(f'has citations ({total_cites} total)')
    elif total_cites == 0:
        score -= 1
        reasons.append('zero citations')

    # Status factor
    if 'PARTIAL' in status or 'ADVANCED' in status:
        score += 1
        reasons.append(f'has progress ({status})')
    elif status == 'OPEN' and age > 50:
        score -= 1
        reasons.append('OPEN with no progress for 50+ sessions')

    # Test criteria
    if has_test_criteria(text):
        score += 1
        reasons.append('has test criteria')
    else:
        score -= 1
        reasons.append('no clear test criteria')

    # Artifact
    if has_artifact(text):
        score += 1
        reasons.append('has artifact')

    # Section importance
    if f['section'] == 'critical':
        score += 2
        reasons.append('critical section')
    elif f['section'] == 'important':
        score += 1
        reasons.append('important section')

    # Related frontier resolution
    resolved_related = [r for r in f.get('related', []) if r in resolved_ids]
    if resolved_related:
        reasons.append(f'related resolved: {",".join(resolved_related)}')
        # Could be mergeable or already covered
        if len(resolved_related) > len(f.get('related', [])) / 2:
            score -= 1
            reasons.append('majority of related frontiers resolved')

    # Classification
    if score <= -3:
        recommendation = 'ABANDON'
    elif score <= -1:
        recommendation = 'REVIEW'  # needs human decision
    elif any(r in resolved_ids for r in f.get('related', [])):
        recommendation = 'MERGE'  # could be folded
    else:
        recommendation = 'KEEP'

    f['score'] = score
    f['recommendation'] = recommendation
    f['reasons'] = reasons
    return f


def main():
    json_mode = '--json' in sys.argv

    # Parse global frontiers
    frontiers = parse_frontiers('tasks/FRONTIER.md')

    # Parse domain frontiers
    for path in sorted(glob.glob('domains/*/tasks/FRONTIER.md')):
        domain_frontiers = parse_frontiers(path)
        frontiers.extend(domain_frontiers)

    # Build resolved set
    resolved_ids = set()
    for f in frontiers:
        if f['status'] in ('RESOLVED', 'FALSIFIED', 'CONFIRMED'):
            resolved_ids.add(f['id'])
    # Also check FRONTIER-ARCHIVE.md
    if os.path.exists('tasks/FRONTIER-ARCHIVE.md'):
        with open('tasks/FRONTIER-ARCHIVE.md') as af:
            for m in re.finditer(r'\*\*(F[-\w]+)\*\*', af.read()):
                resolved_ids.add(m.group(1))

    # Filter to anxiety zone
    anxiety = [f for f in frontiers
               if f['age'] > ANXIETY_THRESHOLD
               and f['status'] not in ('RESOLVED', 'FALSIFIED', 'CONFIRMED')
               and f['section'] != 'archive']

    # Classify each
    results = []
    for f in anxiety:
        classified = classify_frontier(f, resolved_ids)
        results.append(classified)

    results.sort(key=lambda x: x['score'])

    # Summary
    abandon_count = sum(1 for r in results if r['recommendation'] == 'ABANDON')
    review_count = sum(1 for r in results if r['recommendation'] == 'REVIEW')
    merge_count = sum(1 for r in results if r['recommendation'] == 'MERGE')
    keep_count = sum(1 for r in results if r['recommendation'] == 'KEEP')

    print(f'=== FRONTIER TRIAGE — S{CURRENT_SESSION} ===')
    print(f'Total anxiety-zone: {len(results)}')
    print(f'ABANDON: {abandon_count} | REVIEW: {review_count} | '
          f'MERGE: {merge_count} | KEEP: {keep_count}')
    print()

    for rec in ['ABANDON', 'REVIEW', 'MERGE', 'KEEP']:
        group = [r for r in results if r['recommendation'] == rec]
        if not group:
            continue
        print(f'--- {rec} ({len(group)}) ---')
        for r in group:
            cites = f'cites={r["total_citations"]}({r["recent_citations"]}r)'
            print(f'  {r["id"]:15s} age={r["age"]:3d}  score={r["score"]:+d}  '
                  f'{cites}  {r["status"]}')
            for reason in r['reasons']:
                print(f'    • {reason}')
        print()

    if json_mode:
        # Build artifact
        artifact = {
            'session': CURRENT_SESSION,
            'timestamp': datetime.now().isoformat(),
            'total_anxiety': len(results),
            'summary': {
                'abandon': abandon_count,
                'review': review_count,
                'merge': merge_count,
                'keep': keep_count,
            },
            'frontiers': [{
                'id': r['id'],
                'age': r['age'],
                'status': r['status'],
                'score': r['score'],
                'recommendation': r['recommendation'],
                'total_citations': r['total_citations'],
                'recent_citations': r['recent_citations'],
                'reasons': r['reasons'],
                'source': r['source'],
            } for r in results],
        }
        outpath = 'experiments/meta/f-meta2-frontier-triage-s386.json'
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, 'w') as f:
            json.dump(artifact, f, indent=2)
        print(f'Artifact: {outpath}')


if __name__ == '__main__':
    main()
