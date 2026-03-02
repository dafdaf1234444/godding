#!/usr/bin/env python3
"""F-NK5 experiment: citation density by session type.

Hypothesis: DOMEX sessions produce lower citation density (~1.6 edges/L)
than harvest sessions (~3.5 edges/L). Session type is the primary
structural driver of K_avg trajectory.

Method: parse all lessons for session + outgoing L-NNN citations,
classify sessions from SESSION-LOG.md, aggregate by type.
"""
import os, re, json, statistics
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
LESSONS = ROOT / "memory" / "lessons"
SLOG = ROOT / "memory" / "SESSION-LOG.md"

def parse_lessons():
    """Return list of (lesson_id, session, out_citations)."""
    results = []
    cite_re = re.compile(r'\bL-(\d+)\b')
    session_re = re.compile(r'Session:\s*S?(\d+)', re.IGNORECASE)
    for p in sorted(LESSONS.glob("L-*.md")):
        lid = int(re.search(r'L-(\d+)', p.stem).group(1))
        text = p.read_text(errors='replace')
        # Extract session
        m = session_re.search(text)
        if not m:
            continue
        session = int(m.group(1))
        # Extract outgoing citations (exclude self)
        out = set()
        for cm in cite_re.finditer(text):
            cited = int(cm.group(1))
            if cited != lid:
                out.add(cited)
        results.append((lid, session, len(out)))
    return results

def classify_sessions():
    """Classify each session by type from SESSION-LOG.md."""
    types = {}
    if not SLOG.exists():
        return types
    for line in SLOG.read_text().splitlines():
        m = re.match(r'S(\d+)\w*\s*\|', line)
        if not m:
            continue
        sn = int(m.group(1))
        summary = line.split('|')[-1].strip() if '|' in line else ''
        full = line.lower()
        if 'domex' in full:
            types[sn] = 'DOMEX'
        elif 'harvest' in full or re.search(r'\bR\d\b', line):
            types[sn] = 'HARVEST'
        elif 'health' in full or 'periodic' in full or 'maintenance' in full or 'sync' in full:
            types[sn] = 'MAINTENANCE'
        elif re.search(r'F-\w+', line) and 'domex' not in full:
            types[sn] = 'FRONTIER'
        else:
            types[sn] = 'OTHER'
    return types

def main():
    lessons = parse_lessons()
    session_types = classify_sessions()

    # Group by session type
    by_type = defaultdict(list)
    unclassified = 0
    for lid, session, out_cites in lessons:
        stype = session_types.get(session, 'UNCLASSIFIED')
        if stype == 'UNCLASSIFIED':
            unclassified += 1
        by_type[stype].append((lid, session, out_cites))

    print(f"=== F-NK5: Citation Density by Session Type ===")
    print(f"Total lessons parsed: {len(lessons)}")
    print(f"Unclassified sessions: {unclassified}")
    print()

    # Summary table
    print(f"{'Type':<16} {'N_lessons':>9} {'Total_edges':>11} {'Edges/L':>8} {'Median':>7} {'Std':>6} {'Sessions':>8}")
    print("-" * 75)

    type_stats = {}
    for stype in sorted(by_type.keys()):
        items = by_type[stype]
        n = len(items)
        edges = [x[2] for x in items]
        total = sum(edges)
        mean = total / n if n else 0
        med = statistics.median(edges) if edges else 0
        std = statistics.stdev(edges) if len(edges) > 1 else 0
        sessions = len(set(x[1] for x in items))
        print(f"{stype:<16} {n:>9} {total:>11} {mean:>8.2f} {med:>7.1f} {std:>6.2f} {sessions:>8}")
        type_stats[stype] = {
            'n_lessons': n, 'total_edges': total,
            'edges_per_lesson': round(mean, 3),
            'median': med, 'std': round(std, 3),
            'n_sessions': sessions
        }

    # Temporal analysis: early vs late sessions
    print(f"\n=== Temporal Breakdown (session windows) ===")
    windows = [(1, 100), (101, 200), (201, 300), (301, 400)]
    # Find max session
    max_s = max(x[1] for x in lessons) if lessons else 0
    if max_s > 400:
        windows.append((301, max_s))

    print(f"{'Window':<12} {'N':>5} {'Edges/L':>8} {'DOMEX_n':>8} {'DOMEX_e/L':>10} {'Other_n':>8} {'Other_e/L':>10}")
    print("-" * 72)
    window_stats = {}
    for lo, hi in windows:
        w_lessons = [(l, s, e) for l, s, e in lessons if lo <= s <= hi]
        if not w_lessons:
            continue
        w_n = len(w_lessons)
        w_edges = [x[2] for x in w_lessons]
        w_mean = sum(w_edges) / w_n

        # DOMEX subset
        d_lessons = [(l, s, e) for l, s, e in w_lessons if session_types.get(s) == 'DOMEX']
        d_n = len(d_lessons)
        d_mean = sum(x[2] for x in d_lessons) / d_n if d_n else 0

        # Non-DOMEX
        o_lessons = [(l, s, e) for l, s, e in w_lessons if session_types.get(s) != 'DOMEX']
        o_n = len(o_lessons)
        o_mean = sum(x[2] for x in o_lessons) / o_n if o_n else 0

        label = f"S{lo}-S{hi}"
        print(f"{label:<12} {w_n:>5} {w_mean:>8.2f} {d_n:>8} {d_mean:>10.2f} {o_n:>8} {o_mean:>10.2f}")
        window_stats[label] = {
            'total_n': w_n, 'total_epl': round(w_mean, 3),
            'domex_n': d_n, 'domex_epl': round(d_mean, 3),
            'other_n': o_n, 'other_epl': round(o_mean, 3)
        }

    # Distribution of edges/L for DOMEX vs non-DOMEX
    domex_edges = [x[2] for x in by_type.get('DOMEX', [])]
    non_domex_edges = []
    for stype, items in by_type.items():
        if stype != 'DOMEX':
            non_domex_edges.extend([x[2] for x in items])

    print(f"\n=== DOMEX vs Non-DOMEX Distribution ===")
    if domex_edges:
        print(f"DOMEX:     n={len(domex_edges)} mean={statistics.mean(domex_edges):.2f} "
              f"median={statistics.median(domex_edges):.1f} "
              f"p25={sorted(domex_edges)[len(domex_edges)//4]:.0f} "
              f"p75={sorted(domex_edges)[3*len(domex_edges)//4]:.0f}")
    if non_domex_edges:
        print(f"Non-DOMEX: n={len(non_domex_edges)} mean={statistics.mean(non_domex_edges):.2f} "
              f"median={statistics.median(non_domex_edges):.1f} "
              f"p25={sorted(non_domex_edges)[len(non_domex_edges)//4]:.0f} "
              f"p75={sorted(non_domex_edges)[3*len(non_domex_edges)//4]:.0f}")

    # Effect size (Cohen's d if both have variance)
    if domex_edges and non_domex_edges and len(domex_edges) > 1 and len(non_domex_edges) > 1:
        d_std = statistics.stdev(domex_edges)
        nd_std = statistics.stdev(non_domex_edges)
        pooled_std = ((d_std**2 * (len(domex_edges)-1) + nd_std**2 * (len(non_domex_edges)-1)) /
                      (len(domex_edges) + len(non_domex_edges) - 2)) ** 0.5
        cohens_d = (statistics.mean(domex_edges) - statistics.mean(non_domex_edges)) / pooled_std if pooled_std else 0
        print(f"Cohen's d: {cohens_d:.3f} ({'small' if abs(cohens_d)<0.5 else 'medium' if abs(cohens_d)<0.8 else 'large'})")

    # Top-citing and zero-citing lessons
    zero_out = [(l, s, e) for l, s, e in lessons if e == 0]
    high_out = sorted(lessons, key=lambda x: -x[2])[:10]
    print(f"\n=== Extremes ===")
    print(f"Zero-citation lessons: {len(zero_out)} ({100*len(zero_out)/len(lessons):.1f}%)")
    print(f"Top 10 most-citing:")
    for lid, s, e in high_out:
        stype = session_types.get(s, '?')
        print(f"  L-{lid} (S{s}, {stype}): {e} outgoing")

    # Save JSON artifact
    artifact = {
        'experiment': 'F-NK5',
        'session': 'S367',
        'description': 'Citation density by session type',
        'n_lessons': len(lessons),
        'k_avg': round(sum(x[2] for x in lessons) / len(lessons), 4) if lessons else 0,
        'type_stats': type_stats,
        'window_stats': window_stats,
        'domex_mean': round(statistics.mean(domex_edges), 3) if domex_edges else None,
        'non_domex_mean': round(statistics.mean(non_domex_edges), 3) if non_domex_edges else None,
        'cohens_d': round(cohens_d, 3) if 'cohens_d' in dir() else None,
        'zero_citation_count': len(zero_out),
        'zero_citation_pct': round(100 * len(zero_out) / len(lessons), 1) if lessons else 0
    }
    out_path = ROOT / "experiments" / "nk-complexity" / "f-nk5-session-type-citation-s367.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact: {out_path.relative_to(ROOT)}")

if __name__ == '__main__':
    main()
