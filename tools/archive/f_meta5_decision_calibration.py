#!/usr/bin/env python3
"""
Decision Calibration Measurement — F-META5 cal(E)
Mines DOMEX lane expect/actual/diff fields to measure prediction accuracy.

Metrics:
  - Direction accuracy: did the actual match predicted direction?
  - Surprise rate: fraction containing "did NOT predict" in diff
  - Magnitude calibration: ratio of predicted vs actual numeric values
  - Temporal trend: is calibration improving over sessions?
  - Domain variation: which domains have best/worst calibration?

Usage:
    python3 tools/f_meta5_decision_calibration.py
    python3 tools/f_meta5_decision_calibration.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

LANES_FILE = Path("tasks/SWARM-LANES.md")
LANES_ARCHIVE = Path("tasks/SWARM-LANES-ARCHIVE.md")


def extract_etc_field(etc_text: str, field: str) -> str:
    """Extract a field=value from Etc column text."""
    # Match field=...  up to next recognized field or end
    pattern = rf'{field}=([^;]*?)(?:;\s*(?:setup|focus|personality|intent|check_mode|frontier|expect|actual|diff|artifact|progress|available|blocked|next_step|human_open_item|domain_sync|memory_target|slot|dispatch|runtime|historian_check|session_anchor|note)\b|$)'
    m = re.search(pattern, etc_text, re.DOTALL)
    if m:
        return m.group(1).strip().rstrip(';').strip()
    # Simpler fallback: just grab until semicolon
    pattern2 = rf'{field}=([^;]+)'
    m2 = re.search(pattern2, etc_text)
    if m2:
        return m2.group(1).strip()
    return ""


def parse_lane_row(row: str) -> dict | None:
    """Parse a pipe-delimited lane row into a dict."""
    parts = row.split('|')
    if len(parts) < 13:
        return None
    parts = [p.strip() for p in parts]
    # Columns: empty, Date, Lane, Session, Agent, Branch, PR, Model, Platform, Scope-Key, Etc, Status, Notes, empty
    try:
        lane = {
            'date': parts[1],
            'lane_id': parts[2],
            'session': parts[3],
            'model': parts[7],
            'platform': parts[8],
            'scope_key': parts[9],
            'etc': parts[10],
            'status': parts[11],
            'notes': parts[12] if len(parts) > 12 else '',
        }
    except IndexError:
        return None

    if not lane['lane_id'] or lane['lane_id'].startswith('---'):
        return None

    # Extract EAD fields
    lane['expect'] = extract_etc_field(lane['etc'], 'expect')
    lane['actual'] = extract_etc_field(lane['etc'], 'actual')
    lane['diff'] = extract_etc_field(lane['etc'], 'diff')
    lane['intent'] = extract_etc_field(lane['etc'], 'intent')

    # Extract session number
    sm = re.search(r'S(\d+)', lane['session'])
    lane['session_num'] = int(sm.group(1)) if sm else 0

    # Extract domain from lane ID
    dm = re.match(r'DOMEX-([A-Z]+)', lane['lane_id'])
    lane['domain_abbrev'] = dm.group(1) if dm else ''

    return lane


def has_ead(lane: dict) -> bool:
    """Check if lane has meaningful expect+actual+diff fields."""
    return bool(lane['expect']) and bool(lane['actual']) and lane['actual'] != 'TBD'


def classify_direction(lane: dict) -> str:
    """Classify whether the prediction direction was correct, wrong, or mixed.

    Looks for signals in the diff field:
    - "confirmed" / "as predicted" / "expected" → CORRECT
    - "WRONG" / "INVERTED" / "FALSIFIED" → WRONG
    - Both present → MIXED (partially right)
    """
    diff = lane['diff'].lower()

    correct_signals = ['confirmed', 'as predicted', 'as expected', 'exceeded',
                       'prediction correct', 'prediction_met', 'delivered',
                       'completed', 'achieved', 'stronger than expected',
                       'more than expected', 'better than expected',
                       'larger than expected', 'higher than expected',
                       'expected —', 'expected—', 'got .*exceeded']
    wrong_signals = ['wrong', 'inverted', 'falsified',
                     'not predict', 'did not predict', 'unexpected',
                     'worse than expected', 'lower than expected',
                     'weaker than expected', 'prediction was wrong',
                     'overestimate', 'underestimate']

    # First try simple string matching
    has_correct = any(s in diff for s in correct_signals if '.*' not in s)
    has_wrong = any(s in diff for s in wrong_signals if '.*' not in s)

    # Also check for "expected X got Y" / "predicted X got Y" patterns
    if 'expected' in diff or 'predicted' in diff:
        if any(w in diff for w in ['confirm', 'match', 'close']):
            has_correct = True
        if any(w in diff for w in ['but ', 'however', 'instead']):
            has_wrong = True

    if has_correct and has_wrong:
        return 'MIXED'
    elif has_correct:
        return 'CORRECT'
    elif has_wrong:
        return 'WRONG'
    else:
        return 'UNCLEAR'


def count_surprises(lane: dict) -> int:
    """Count surprise markers in diff field."""
    diff = lane['diff']
    surprises = len(re.findall(r'did NOT predict|unexpected|surprise|not predict', diff, re.IGNORECASE))
    return surprises


def extract_numeric_predictions(text: str) -> list[tuple[str, float]]:
    """Extract quantitative predictions like >70%, r=0.6, 2x, etc."""
    predictions = []
    # Percentages
    for m in re.finditer(r'([><≥≤]?\d+(?:\.\d+)?)\s*%', text):
        val = m.group(1).lstrip('<>≥≤')
        try:
            predictions.append(('pct', float(val)))
        except ValueError:
            pass
    # r= or R²= values
    for m in re.finditer(r'[rR]²?\s*[=<>]\s*(\d+\.\d+)', text):
        try:
            predictions.append(('r', float(m.group(1))))
        except ValueError:
            pass
    # multipliers (2x, 3x)
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*x\b', text):
        try:
            predictions.append(('mult', float(m.group(1))))
        except ValueError:
            pass
    return predictions


def compute_magnitude_error(lane: dict) -> float | None:
    """Compute average magnitude error between predicted and actual numbers.

    Returns ratio of actual/predicted (1.0 = perfect calibration).
    """
    pred_nums = extract_numeric_predictions(lane['expect'])
    actual_nums = extract_numeric_predictions(lane['actual'])

    if not pred_nums or not actual_nums:
        return None

    # Match by type
    errors = []
    for ptype, pval in pred_nums:
        for atype, aval in actual_nums:
            if ptype == atype and pval > 0:
                errors.append(aval / pval)
                break

    if not errors:
        return None
    return sum(errors) / len(errors)


def load_lanes(filepath: Path) -> list[dict]:
    """Load and parse lanes from a markdown table file."""
    if not filepath.exists():
        return []
    lanes = []
    text = filepath.read_text(encoding='utf-8')
    for line in text.split('\n'):
        if '|' in line and not line.strip().startswith('| ---') and not line.strip().startswith('| Date'):
            lane = parse_lane_row(line)
            if lane and lane['lane_id']:
                lanes.append(lane)
    return lanes


def main():
    parser = argparse.ArgumentParser(description='Decision calibration measurement')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    # Load all lanes
    lanes = load_lanes(LANES_ARCHIVE) + load_lanes(LANES_FILE)

    # Filter to lanes with full EAD
    ead_lanes = [l for l in lanes if has_ead(l)]

    # Deduplicate: keep last row per lane_id (append-only log)
    seen = {}
    for l in ead_lanes:
        seen[l['lane_id']] = l
    ead_lanes = list(seen.values())

    # Classify directions
    directions = defaultdict(int)
    surprises_total = 0
    surprise_lanes = 0
    mag_errors = []
    domain_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'mixed': 0, 'wrong': 0, 'unclear': 0, 'surprises': 0})
    session_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'mixed': 0, 'wrong': 0, 'unclear': 0})

    for lane in ead_lanes:
        direction = classify_direction(lane)
        directions[direction] += 1

        surprises = count_surprises(lane)
        surprises_total += surprises
        if surprises > 0:
            surprise_lanes += 1

        mag = compute_magnitude_error(lane)
        if mag is not None:
            mag_errors.append({'lane': lane['lane_id'], 'ratio': mag, 'session': lane['session_num']})

        domain = lane['domain_abbrev'] or 'OTHER'
        domain_stats[domain]['total'] += 1
        domain_stats[domain][direction.lower()] += 1
        domain_stats[domain]['surprises'] += surprises

        # Bin sessions into groups of 20
        sbin = (lane['session_num'] // 20) * 20
        session_stats[sbin]['total'] += 1
        session_stats[sbin][direction.lower()] += 1

    total = len(ead_lanes)

    # Compute metrics
    direction_accuracy = (directions['CORRECT'] + 0.5 * directions['MIXED']) / total if total > 0 else 0
    surprise_rate = surprise_lanes / total if total > 0 else 0

    # Magnitude calibration: median ratio (1.0 = perfect)
    mag_ratios = [m['ratio'] for m in mag_errors]
    mag_ratios.sort()
    median_mag = mag_ratios[len(mag_ratios) // 2] if mag_ratios else None
    mean_mag = sum(mag_ratios) / len(mag_ratios) if mag_ratios else None

    # Temporal trend: direction accuracy in early vs late sessions
    session_bins = sorted(session_stats.keys())
    temporal = []
    for sbin in session_bins:
        s = session_stats[sbin]
        if s['total'] >= 3:
            acc = (s.get('correct', 0) + 0.5 * s.get('mixed', 0)) / s['total']
            temporal.append({'session_bin': f'S{sbin}-S{sbin+19}', 'n': s['total'], 'accuracy': round(acc, 3)})

    # Domain ranking by accuracy
    domain_ranking = []
    for domain, stats in sorted(domain_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        if stats['total'] >= 2:
            acc = (stats.get('correct', 0) + 0.5 * stats.get('mixed', 0)) / stats['total']
            surprise_r = stats['surprises'] / stats['total']
            domain_ranking.append({
                'domain': domain, 'n': stats['total'],
                'accuracy': round(acc, 3), 'surprise_rate': round(surprise_r, 2),
                'correct': stats.get('correct', 0), 'mixed': stats.get('mixed', 0),
                'wrong': stats.get('wrong', 0)
            })
    domain_ranking.sort(key=lambda x: x['accuracy'], reverse=True)

    # Magnitude over-/under-estimation
    over_est = len([r for r in mag_ratios if r < 0.8])
    under_est = len([r for r in mag_ratios if r > 1.2])
    well_cal = len([r for r in mag_ratios if 0.8 <= r <= 1.2])

    results = {
        'total_lanes_with_ead': total,
        'total_lanes_parsed': len(lanes),
        'direction_classification': {
            'CORRECT': directions['CORRECT'],
            'MIXED': directions['MIXED'],
            'WRONG': directions['WRONG'],
            'UNCLEAR': directions['UNCLEAR'],
        },
        'direction_accuracy': round(direction_accuracy, 3),
        'surprise_rate': round(surprise_rate, 3),
        'surprises_total': surprises_total,
        'magnitude_calibration': {
            'n_measurable': len(mag_ratios),
            'median_ratio': round(median_mag, 3) if median_mag else None,
            'mean_ratio': round(mean_mag, 3) if mean_mag else None,
            'over_estimated': over_est,
            'well_calibrated': well_cal,
            'under_estimated': under_est,
        },
        'temporal_trend': temporal,
        'domain_ranking': domain_ranking,
        'cal_e': round(direction_accuracy, 3),
    }

    if args.json:
        print(json.dumps(results, indent=2))
        return

    # Human-readable output
    print(f"=== DECISION CALIBRATION (F-META5) ===")
    print(f"Lanes parsed: {len(lanes)} total, {total} with full EAD")
    print()
    print(f"--- Direction Accuracy ---")
    print(f"  CORRECT: {directions['CORRECT']} ({directions['CORRECT']/total*100:.1f}%)" if total else "")
    print(f"  MIXED:   {directions['MIXED']} ({directions['MIXED']/total*100:.1f}%)" if total else "")
    print(f"  WRONG:   {directions['WRONG']} ({directions['WRONG']/total*100:.1f}%)" if total else "")
    print(f"  UNCLEAR: {directions['UNCLEAR']} ({directions['UNCLEAR']/total*100:.1f}%)" if total else "")
    print(f"  cal(E) = {direction_accuracy:.3f}")
    print()
    print(f"--- Surprise Rate ---")
    print(f"  {surprise_lanes}/{total} lanes ({surprise_rate*100:.1f}%) contain surprises")
    print(f"  {surprises_total} total surprise markers")
    print()
    print(f"--- Magnitude Calibration ---")
    if mag_ratios:
        print(f"  {len(mag_ratios)} lanes with measurable numeric predictions")
        print(f"  Median actual/predicted ratio: {median_mag:.2f} (1.0 = perfect)")
        print(f"  Over-estimated (ratio<0.8): {over_est} ({over_est/len(mag_ratios)*100:.0f}%)")
        print(f"  Well-calibrated (0.8-1.2): {well_cal} ({well_cal/len(mag_ratios)*100:.0f}%)")
        print(f"  Under-estimated (ratio>1.2): {under_est} ({under_est/len(mag_ratios)*100:.0f}%)")
    else:
        print(f"  No measurable numeric predictions found")
    print()
    print(f"--- Temporal Trend ---")
    for t in temporal:
        bar = '#' * int(t['accuracy'] * 20)
        print(f"  {t['session_bin']:>12} (n={t['n']:>2}): {t['accuracy']:.3f} {bar}")
    print()
    print(f"--- Domain Ranking (by accuracy, n≥2) ---")
    for d in domain_ranking[:15]:
        print(f"  {d['domain']:>20}: {d['accuracy']:.3f} (n={d['n']}, C={d['correct']} M={d['mixed']} W={d['wrong']}, surprises={d['surprise_rate']:.0%})")


if __name__ == '__main__':
    main()
