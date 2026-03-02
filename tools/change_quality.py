#!/usr/bin/env python3
"""
change_quality.py - Assess per-session change quality vs. historical baseline.

Investigates whether the swarm is improving, stable, or declining over time
by comparing knowledge production and overhead signals across sessions.

Usage:
  python3 tools/change_quality.py              # Recent 5 sessions vs. baseline
  python3 tools/change_quality.py --trend      # Full session trend table
  python3 tools/change_quality.py --session N  # Detail for session N
  python3 tools/change_quality.py --recent N   # Compare last N sessions (default 5)
  python3 tools/change_quality.py --learn      # Save ratings + show persistent trends

Evolved: S176 (initial) → S350 (frontier regex fix, DOMEX tracking, --learn mode)
"""

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent

SESSION_RE = re.compile(r'\[S(\d+)\]')
LESSON_RE = re.compile(r'\bL-(\d{3})\b')
PRINCIPLE_RE = re.compile(r'\bP-(\d{3})\b')
BELIEF_RE = re.compile(r'\bPHIL-(\d+)\b')
# Match both old (F9, F95) and new (F-CON3, F-META1, F-LNG1) frontier formats
_FRONTIER_ID = r'\bF-?[A-Z]*\d+\b'
FRONTIER_ADVANCE_RE = re.compile(
    rf'{_FRONTIER_ID}.*\b(RESOLVED|PARTIAL|CONFIRMED|ADVANCED)\b'
    rf'|\b(RESOLVED|PARTIAL|CONFIRMED|ADVANCED)\b.*{_FRONTIER_ID}',
    re.IGNORECASE)
FRONTIER_OPEN_RE = re.compile(
    rf'{_FRONTIER_ID}.*\bOPEN\b|\bOPEN\b.*{_FRONTIER_ID}'
    rf'|{_FRONTIER_ID}\s+filed\b|\bfiled\s+{_FRONTIER_ID}',
    re.IGNORECASE)

# Patterns that indicate administrative overhead (state-sync, not knowledge work)
OVERHEAD_PATTERNS = [
    r'\bstate-sync\b',
    r'\bscale sync\b',
    r'\bcount sync\b',
    r'\bheader sync\b',
    r'\bcounts corrected\b',
    r'\bprinciple-count sync\b',
    r'\bsession log\b',
    r'\bhandoff\b',
]
OVERHEAD_RE = re.compile('|'.join(OVERHEAD_PATTERNS), re.IGNORECASE)

# Patterns that indicate real knowledge work
KNOWLEDGE_PATTERNS = [
    r'\bL-\d{3}\b',        # lesson reference
    r'\bP-\d{3}\b',        # principle reference
    _FRONTIER_ID + r'.*\bOPEN\b',  # frontier opened
    r'\bharvest\b',
    r'\bdistill\b',
    r'\bexperiment\b',
]
KNOWLEDGE_RE = re.compile('|'.join(KNOWLEDGE_PATTERNS), re.IGNORECASE)

# Expert dispatch signals (DOMEX, council, ISO)
DOMEX_RE = re.compile(r'\bDOMEX\b', re.IGNORECASE)
COUNCIL_RE = re.compile(r'\bcouncil\b', re.IGNORECASE)
ISO_RE = re.compile(r'\bISO-\d+\b')

# Non-lesson production signals (L-939: 25% of commits carry invisible production)
LANE_CLOSE_RE = re.compile(r'\b(MERGED|ABANDONED|close_lane|close:)\b', re.IGNORECASE)
TOOL_CHANGE_RE = re.compile(r'\btools/\S+\.py\b')
CORRECTION_RE = re.compile(r'\b(correction|corrected|propagat|citation.*fix)\b', re.IGNORECASE)
ARTIFACT_RE = re.compile(r'\bartifact|experiments/\S+\.json\b', re.IGNORECASE)

QUALITY_LOG = Path(__file__).parent.parent / 'workspace' / 'change-quality-log.json'
MAX_LOG_SESSIONS = 50


def get_commits():
    """Extract all commits with session numbers from git log."""
    result = subprocess.run(
        ['git', 'log', '--format=%H|%s', '--no-merges'],
        capture_output=True, text=True, cwd=ROOT
    )
    commits = []
    for line in result.stdout.strip().split('\n'):
        if '|' not in line:
            continue
        hash_, msg = line.split('|', 1)
        m = SESSION_RE.search(msg)
        if not m:
            continue
        commits.append({
            'hash': hash_,
            'msg': msg,
            'session': int(m.group(1)),
        })
    return commits


def extract_session_signals(commits):
    """Group commits by session and extract quality signals."""
    sessions = defaultdict(lambda: {
        'commits': 0,
        'lessons': set(),
        'principles': set(),
        'beliefs': set(),
        'frontier_advances': 0,
        'frontiers_opened': 0,
        'overhead_commits': 0,
        'knowledge_commits': 0,
        'domex_commits': 0,
        'council_commits': 0,
        'iso_refs': set(),
        'lane_closures': 0,
        'tool_changes': 0,
        'corrections': 0,
        'artifact_refs': 0,
        'msgs': [],
    })

    for c in commits:
        s = c['session']
        msg = c['msg']
        d = sessions[s]

        d['commits'] += 1
        d['msgs'].append(msg)

        for lid in LESSON_RE.findall(msg):
            d['lessons'].add(lid)
        for pid in PRINCIPLE_RE.findall(msg):
            d['principles'].add(pid)
        for bid in BELIEF_RE.findall(msg):
            d['beliefs'].add(bid)
        if FRONTIER_ADVANCE_RE.search(msg):
            d['frontier_advances'] += 1
        if FRONTIER_OPEN_RE.search(msg):
            d['frontiers_opened'] += 1
        if DOMEX_RE.search(msg):
            d['domex_commits'] += 1
        if COUNCIL_RE.search(msg):
            d['council_commits'] += 1
        for iso in ISO_RE.findall(msg):
            d['iso_refs'].add(iso)
        if LANE_CLOSE_RE.search(msg):
            d['lane_closures'] += 1
        if TOOL_CHANGE_RE.search(msg):
            d['tool_changes'] += 1
        if CORRECTION_RE.search(msg):
            d['corrections'] += 1
        if ARTIFACT_RE.search(msg):
            d['artifact_refs'] += 1
        if OVERHEAD_RE.search(msg):
            d['overhead_commits'] += 1
        elif KNOWLEDGE_RE.search(msg):
            d['knowledge_commits'] += 1

    return dict(sessions)


def quality_score(sig):
    """
    Composite quality score for a session. Higher = better.

    Components:
      - Knowledge production: lessons + principles touched, frontier advances
      - Expert work: DOMEX lanes, council sessions, ISO annotations
      - Focus: low overhead ratio
      - Commit granularity: 2-15 ideal (widened for concurrent-session era)
    """
    n = sig['commits']
    if n == 0:
        return 0.0

    lessons = len(sig['lessons'])
    principles = len(sig['principles'])
    beliefs = len(sig.get('beliefs', set()))
    frontier_advances = sig['frontier_advances']
    frontiers_opened = sig['frontiers_opened']
    domex = sig.get('domex_commits', 0)
    council = sig.get('council_commits', 0)
    iso_count = len(sig.get('iso_refs', set()))
    overhead_ratio = sig['overhead_commits'] / n

    # Knowledge production (scale: 0-8+)
    knowledge = (
        lessons * 1.2
        + principles * 0.6
        + beliefs * 1.5
        + frontier_advances * 2.0
        + frontiers_opened * 1.5
    )

    # Expert dispatch bonus (DOMEX/council are structured knowledge work)
    expert_bonus = min(2.0, domex * 0.3 + council * 0.4 + iso_count * 0.15)
    knowledge += expert_bonus

    # Non-lesson production bonus (L-939: 25% of commits carry invisible production)
    lane_closures = sig.get('lane_closures', 0)
    tool_changes = sig.get('tool_changes', 0)
    corrections = sig.get('corrections', 0)
    artifact_refs = sig.get('artifact_refs', 0)
    production_bonus = min(3.0,
        tool_changes * 0.8 + lane_closures * 0.5 +
        corrections * 0.3 + artifact_refs * 0.6)
    knowledge += production_bonus

    # Focus penalty: overhead > 25% is waste (baseline ~18% observed)
    focus_multiplier = max(0.5, 1.0 - max(0, overhead_ratio - 0.10) * 2)

    # Commit granularity (widened: concurrent sessions produce 10-20 commits)
    if 2 <= n <= 15:
        granularity = 1.0
    elif n == 1:
        granularity = 0.7
    else:
        granularity = max(0.6, 1.0 - (n - 15) * 0.02)

    return knowledge * focus_multiplier * granularity


def compute_baseline(sessions_data, exclude_last_n=5):
    """Compute historical baseline stats, excluding the most recent N sessions."""
    sorted_sessions = sorted(sessions_data.keys())
    if exclude_last_n == 0 or len(sorted_sessions) <= exclude_last_n:
        baseline_sessions = sorted_sessions
    else:
        baseline_sessions = sorted_sessions[:-exclude_last_n]

    if not baseline_sessions:
        return None

    scores = [quality_score(sessions_data[s]) for s in baseline_sessions]
    lessons = [len(sessions_data[s]['lessons']) for s in baseline_sessions]
    principles = [len(sessions_data[s]['principles']) for s in baseline_sessions]
    overhead = [sessions_data[s]['overhead_commits'] / max(1, sessions_data[s]['commits'])
                for s in baseline_sessions]

    n = len(scores)
    return {
        'mean_score': sum(scores) / n,
        'mean_lessons': sum(lessons) / n,
        'mean_principles': sum(principles) / n,
        'mean_overhead': sum(overhead) / n,
        'sessions': n,
    }


def rating(score, baseline_mean):
    """Return human-readable rating vs. baseline."""
    if baseline_mean <= 0:
        return '?'
    ratio = score / baseline_mean
    if ratio >= 1.4:
        return 'STRONG'
    if ratio >= 1.1:
        return 'ABOVE'
    if ratio >= 0.9:
        return 'ON PAR'
    if ratio >= 0.6:
        return 'BELOW'
    return 'WEAK'


def show_comparison(sessions_data, n_recent=5):
    sorted_s = sorted(sessions_data.keys())
    if len(sorted_s) < 2:
        print("Not enough session history to compare.")
        return

    recent = sorted_s[-n_recent:]
    baseline = compute_baseline(sessions_data, exclude_last_n=n_recent)

    if not baseline:
        print("Not enough history for baseline.")
        return

    print(f"=== CHANGE QUALITY: RECENT {n_recent} vs. BASELINE ({baseline['sessions']} sessions) ===")
    print(f"Baseline averages: score={baseline['mean_score']:.2f} | "
          f"L/session={baseline['mean_lessons']:.1f} | "
          f"P/session={baseline['mean_principles']:.1f} | "
          f"overhead={baseline['mean_overhead']:.0%}")
    print()
    print(f"{'Session':>8}  {'Commits':>7}  {'Lessons':>7}  {'Princ':>6}  "
          f"{'FAdv':>5}  {'Overhead':>9}  {'Score':>6}  {'Rating':>8}")
    print("-" * 78)

    for s in recent:
        sig = sessions_data[s]
        score = quality_score(sig)
        overhead_pct = sig['overhead_commits'] / max(1, sig['commits'])
        r = rating(score, baseline['mean_score'])
        print(f"  S{s:>5}  {sig['commits']:>7}  {len(sig['lessons']):>7}  "
              f"{len(sig['principles']):>6}  {sig['frontier_advances']:>5}  "
              f"{overhead_pct:>8.0%}  {score:>6.2f}  {r:>8}")

    # Trend signal
    print()
    if len(sorted_s) >= 10:
        mid = len(sorted_s) // 2
        early = [quality_score(sessions_data[s]) for s in sorted_s[:mid]]
        late = [quality_score(sessions_data[s]) for s in sorted_s[mid:]]
        avg_early = sum(early) / len(early)
        avg_late = sum(late) / len(late)
        ratio = avg_late / avg_early if avg_early > 0 else 1.0
        if ratio >= 1.15:
            trend = f"IMPROVING (+{(ratio-1):.0%})"
        elif ratio <= 0.85:
            trend = f"DECLINING ({(ratio-1):.0%})"
        else:
            trend = f"STABLE ({(ratio-1):+.0%})"
        print(f"Long-term trend: {trend}  "
              f"(early avg={avg_early:.2f}, recent avg={avg_late:.2f})")


def show_trend(sessions_data):
    """Full session-by-session trend table."""
    sorted_s = sorted(sessions_data.keys())
    all_scores = [quality_score(sessions_data[s]) for s in sorted_s]
    if not all_scores:
        print("No session data found.")
        return

    global_mean = sum(all_scores) / len(all_scores)

    print(f"=== CHANGE QUALITY TREND ({len(sorted_s)} sessions) ===")
    print(f"Global mean score: {global_mean:.2f}")
    print()
    print(f"{'Session':>8}  {'Commits':>7}  {'Lessons':>7}  {'Princ':>6}  "
          f"{'FAdv':>5}  {'Overhead':>9}  {'Score':>6}  Bar")
    print("-" * 80)

    for s in sorted_s:
        sig = sessions_data[s]
        score = quality_score(sig)
        overhead_pct = sig['overhead_commits'] / max(1, sig['commits'])
        bar_len = min(20, int(score * 2))
        bar = '#' * bar_len
        marker = '*' if score > global_mean * 1.3 else (' ' if score >= global_mean * 0.7 else '!')
        print(f"  S{s:>5}  {sig['commits']:>7}  {len(sig['lessons']):>7}  "
              f"{len(sig['principles']):>6}  {sig['frontier_advances']:>5}  "
              f"{overhead_pct:>8.0%}  {score:>6.2f}  {marker}{bar}")


def show_session_detail(sessions_data, session_num):
    """Detailed breakdown for a specific session."""
    if session_num not in sessions_data:
        available = sorted(sessions_data.keys())
        print(f"Session S{session_num} not found.")
        print(f"Available: {available[-10:]}")
        return

    sig = sessions_data[session_num]
    score = quality_score(sig)
    baseline = compute_baseline(sessions_data, exclude_last_n=0)
    r = rating(score, baseline['mean_score']) if baseline else '?'

    print(f"=== SESSION S{session_num} QUALITY DETAIL ===")
    print(f"Score: {score:.2f}  Rating: {r}  (global mean: {baseline['mean_score']:.2f})")
    print()
    print(f"Commits:             {sig['commits']}")
    print(f"Lessons referenced:  {sorted(sig['lessons'])} ({len(sig['lessons'])} unique)")
    print(f"Principles ref'd:    {sorted(sig['principles'])} ({len(sig['principles'])} unique)")
    print(f"Beliefs changed:     PHIL-{sorted(sig.get('beliefs', set()))} ({len(sig.get('beliefs', set()))} unique)")
    print(f"Frontier advances:   {sig['frontier_advances']}")
    print(f"Frontiers opened:    {sig['frontiers_opened']}")
    print(f"DOMEX commits:       {sig.get('domex_commits', 0)}")
    print(f"Council commits:     {sig.get('council_commits', 0)}")
    print(f"ISO references:      {sorted(sig.get('iso_refs', set()))}")
    print(f"Overhead commits:    {sig['overhead_commits']} "
          f"({sig['overhead_commits']/max(1,sig['commits']):.0%})")
    print(f"Knowledge commits:   {sig['knowledge_commits']}")
    print()
    print("Commit messages:")
    for m in sig['msgs']:
        tag = '[overhead]' if OVERHEAD_RE.search(m) else '[  work  ]'
        print(f"  {tag} {m[:80]}")


def learn_mode(sessions_data, n_recent=5):
    """Save quality ratings persistently and show trends across sessions."""
    sorted_s = sorted(sessions_data.keys())
    if len(sorted_s) < 2:
        print("Not enough session data for --learn.")
        return

    baseline = compute_baseline(sessions_data, exclude_last_n=n_recent)
    if not baseline:
        print("Not enough history for baseline.")
        return

    # Load existing log
    log = {'schema': 'change-quality-log-v1', 'entries': []}
    if QUALITY_LOG.exists():
        try:
            log = json.loads(QUALITY_LOG.read_text())
        except (json.JSONDecodeError, KeyError):
            pass

    existing_sessions = {e['session'] for e in log.get('entries', [])}
    recent = sorted_s[-n_recent:]
    new_entries = 0

    for s in recent:
        if s in existing_sessions:
            continue
        sig = sessions_data[s]
        score = quality_score(sig)
        r = rating(score, baseline['mean_score'])
        entry = {
            'session': s,
            'score': round(score, 2),
            'rating': r,
            'lessons': len(sig['lessons']),
            'principles': len(sig['principles']),
            'frontier_advances': sig['frontier_advances'],
            'domex': sig.get('domex_commits', 0),
            'council': sig.get('council_commits', 0),
            'overhead_pct': round(sig['overhead_commits'] / max(1, sig['commits']), 2),
            'commits': sig['commits'],
        }
        log['entries'].append(entry)
        new_entries += 1

    # Trim to MAX_LOG_SESSIONS
    log['entries'] = sorted(log['entries'], key=lambda e: e['session'])[-MAX_LOG_SESSIONS:]

    QUALITY_LOG.write_text(json.dumps(log, indent=2) + '\n')

    # Analyze persistent trends
    entries = log['entries']
    print(f"=== CHANGE QUALITY --learn ({len(entries)} logged, {new_entries} new) ===")

    if len(entries) >= 5:
        recent_scores = [e['score'] for e in entries[-5:]]
        older_scores = [e['score'] for e in entries[:-5]] if len(entries) > 5 else recent_scores
        avg_recent = sum(recent_scores) / len(recent_scores)
        avg_older = sum(older_scores) / len(older_scores) if older_scores else avg_recent
        ratio = avg_recent / avg_older if avg_older > 0 else 1.0

        if ratio >= 1.15:
            trend = f"IMPROVING (+{(ratio-1):.0%})"
        elif ratio <= 0.85:
            trend = f"DECLINING ({(ratio-1):.0%})"
        else:
            trend = f"STABLE ({(ratio-1):+.0%})"

        print(f"Persistent trend: {trend} (recent avg={avg_recent:.2f}, older avg={avg_older:.2f})")

        # Consecutive WEAK detection
        weak_streak = 0
        for e in reversed(entries):
            if e['rating'] == 'WEAK':
                weak_streak += 1
            else:
                break
        if weak_streak >= 2:
            print(f"  !! WARNING: {weak_streak} consecutive WEAK sessions — root-cause diagnosis needed")

        # DOMEX utilization across logged sessions
        domex_sessions = sum(1 for e in entries if e.get('domex', 0) > 0)
        print(f"Expert utilization: {domex_sessions}/{len(entries)} sessions have DOMEX commits "
              f"({domex_sessions/len(entries):.0%})")

    print(f"Log saved: {QUALITY_LOG.relative_to(ROOT)}")


def main():
    args = sys.argv[1:]
    commits = get_commits()
    if not commits:
        print("No sessions found in git log.")
        sys.exit(1)

    sessions_data = extract_session_signals(commits)

    if '--learn' in args:
        show_comparison(sessions_data)
        print()
        learn_mode(sessions_data)
    elif '--trend' in args:
        show_trend(sessions_data)
    elif '--session' in args:
        idx = args.index('--session')
        if idx + 1 < len(args):
            try:
                target = int(args[idx + 1])
                show_session_detail(sessions_data, target)
            except ValueError:
                print("--session requires a numeric session number")
                sys.exit(1)
        else:
            print("--session requires a session number")
            sys.exit(1)
    else:
        n_recent = 5
        if '--recent' in args:
            idx = args.index('--recent')
            if idx + 1 < len(args):
                try:
                    n_recent = int(args[idx + 1])
                except ValueError:
                    pass
        show_comparison(sessions_data, n_recent=n_recent)


if __name__ == '__main__':
    main()
