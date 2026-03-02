#!/usr/bin/env python3
"""f_is3_empirical_grounding.py — Empirical test of F-IS3 spawn_math.py model.

Tests whether the theoretical spawn-size model (utility(N) = baseline - risk - coordination)
predicts observed outcomes across 374 sessions of real concurrent swarm behavior.

Method: extract per-session time ranges from git log, compute concurrent N via
overlap detection, then bin by N to measure L+P degradation curve.
"""

from __future__ import annotations
import json, math, re, subprocess, sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parent.parent
SESSION_LOG = ROOT / "memory" / "SESSION-LOG.md"


def parse_session_log() -> dict[int, dict]:
    """Parse SESSION-LOG.md into structured records keyed by session number."""
    sessions = {}
    with open(SESSION_LOG) as f:
        for line in f:
            line = line.strip()
            m = re.match(
                r'^(S\d+\w*)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\+(\d+)L.*?\+(\d+)P\s*\|\s*(.*)',
                line
            )
            if m:
                sid, date_str, lessons, principles, summary = m.groups()
                num_m = re.match(r'S(\d+)', sid)
                num = int(num_m.group(1)) if num_m else 0
                # Keep the entry with highest L+P if multiple entries per session num
                lp = int(lessons) + int(principles)
                if num not in sessions or lp > sessions[num]['lp']:
                    sessions[num] = {
                        'session_id': sid,
                        'session_num': num,
                        'date': date_str,
                        'lessons': int(lessons),
                        'principles': int(principles),
                        'lp': lp,
                    }
    return sessions


def extract_session_time_ranges() -> dict[int, tuple[datetime, datetime]]:
    """Extract first and last commit timestamp per session from git log."""
    result = subprocess.run(
        ['git', 'log', '--format=%aI|%s', '--all'],
        capture_output=True, text=True, cwd=ROOT
    )
    commits_by_session = defaultdict(list)
    for line in result.stdout.strip().split('\n'):
        if '|' not in line:
            continue
        ts_str, msg = line.split('|', 1)
        m = re.search(r'\[S(\d+)\]', msg)
        if not m:
            continue
        session_num = int(m.group(1))
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            continue
        commits_by_session[session_num].append(ts)

    ranges = {}
    for snum, timestamps in commits_by_session.items():
        timestamps.sort()
        ranges[snum] = (timestamps[0], timestamps[-1])
    return ranges


def compute_concurrent_n(ranges: dict[int, tuple[datetime, datetime]]) -> dict[int, int]:
    """For each session, count how many other sessions had overlapping time ranges."""
    concurrent = {}
    session_nums = sorted(ranges.keys())
    for snum in session_nums:
        start, end = ranges[snum]
        # Extend range by 5 min on each side to account for session setup/teardown
        ext_start = start - timedelta(minutes=5)
        ext_end = end + timedelta(minutes=5)
        count = 0
        for other_num in session_nums:
            if other_num == snum:
                continue
            o_start, o_end = ranges[other_num]
            # Check overlap
            if o_start <= ext_end and o_end >= ext_start:
                count += 1
        concurrent[snum] = count + 1  # +1 for self
    return concurrent


def compute_n_bins(data: list[dict], bins: list[tuple[int, int]]) -> list[dict]:
    """Bin sessions by concurrent N and compute statistics."""
    results = []
    for lo, hi in bins:
        label = f"N={lo}" if lo == hi else f"N={lo}-{hi}"
        matching = [d for d in data if lo <= d['concurrent_n'] <= hi]
        if not matching:
            results.append({
                'bin': label, 'n_sessions': 0,
                'mean_lp': 0, 'mean_l': 0, 'std_lp': 0, 'total_lp': 0,
            })
            continue
        n = len(matching)
        lps = [d['lp'] for d in matching]
        ls = [d['lessons'] for d in matching]
        mean_lp = sum(lps) / n
        mean_l = sum(ls) / n
        var_lp = sum((x - mean_lp)**2 for x in lps) / max(n - 1, 1)
        results.append({
            'bin': label,
            'n_sessions': n,
            'mean_lp': round(mean_lp, 3),
            'mean_l': round(mean_l, 3),
            'std_lp': round(var_lp**0.5, 3),
            'total_lp': sum(lps),
            'median_lp': sorted(lps)[n // 2],
        })
    return results


def estimate_coordination_cost(data: list[dict]) -> dict:
    """Estimate coordination cost via regression: L+P = alpha + beta*N."""
    if len(data) < 10:
        return {'error': 'insufficient data'}
    ns = [d['concurrent_n'] for d in data]
    lps = [d['lp'] for d in data]
    n_mean = sum(ns) / len(ns)
    lp_mean = sum(lps) / len(lps)
    cov = sum((n - n_mean) * (lp - lp_mean) for n, lp in zip(ns, lps))
    var_n = sum((n - n_mean)**2 for n in ns)
    if var_n < 1e-10:
        return {'error': 'no variance in N'}
    beta = cov / var_n
    alpha = lp_mean - beta * n_mean
    # R²
    ss_res = sum((lp - (alpha + beta * n))**2 for n, lp in zip(ns, lps))
    ss_tot = sum((lp - lp_mean)**2 for lp in lps)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return {
        'alpha': round(alpha, 4),
        'beta': round(beta, 4),
        'baseline_at_n1': round(alpha + beta, 3),
        'coordination_cost_per_agent': round(-beta, 4),
        'r_squared': round(r2, 4),
        'n_points': len(data),
        'n_range': [min(ns), max(ns)],
    }


def estimate_rho_from_sessions(data: list[dict]) -> dict:
    """Estimate error correlation (rho) using within-group vs between-group variance."""
    # Group sessions by concurrent N
    by_n = defaultdict(list)
    for d in data:
        by_n[d['concurrent_n']].append(d['lp'])

    # Compute within-group variance for groups with multiple sessions
    within_vars = []
    for n, lps in by_n.items():
        if len(lps) >= 3:
            mean_lp = sum(lps) / len(lps)
            var = sum((x - mean_lp)**2 for x in lps) / (len(lps) - 1)
            within_vars.append((len(lps), var, n))

    all_lps = [d['lp'] for d in data]
    overall_mean = sum(all_lps) / len(all_lps)
    overall_var = sum((x - overall_mean)**2 for x in all_lps) / (len(all_lps) - 1)

    if not within_vars:
        return {'rho_estimate': 0.0, 'method': 'no_groups', 'overall_var': round(overall_var, 4)}

    total_n = sum(v[0] for v in within_vars)
    avg_within = sum(v[0] * v[1] for v in within_vars) / total_n
    between = max(0, overall_var - avg_within)
    avg_k = total_n / len(within_vars)
    denom = between + (avg_k - 1) * avg_within
    icc = between / denom if denom > 0 else 0

    return {
        'rho_estimate': round(max(0, icc), 4),
        'overall_var': round(overall_var, 4),
        'avg_within_var': round(avg_within, 4),
        'n_groups': len(within_vars),
        'method': 'ICC',
    }


def model_predictions(baseline, std, rho, coord_cost, n_max=15):
    """Generate spawn_math.py model predictions."""
    preds = []
    for n in range(1, n_max + 1):
        sf = math.sqrt((1 + (n - 1) * rho) / n)
        u = baseline - std * sf - coord_cost * (n - 1)
        preds.append({'n': n, 'utility': round(u, 4)})
    best_n = max(preds, key=lambda p: p['utility'])['n']
    return preds, best_n


def main():
    import argparse
    parser = argparse.ArgumentParser(description='F-IS3 empirical grounding')
    parser.add_argument('--out', default='experiments/information-science/f-is3-empirical-grounding-s374.json')
    parser.add_argument('--session', default='S374')
    args = parser.parse_args()
    out_path = ROOT / args.out

    # 1. Parse session data from SESSION-LOG
    log_sessions = parse_session_log()
    print(f"Parsed {len(log_sessions)} unique sessions from SESSION-LOG.md")

    # 2. Extract time ranges from git log
    ranges = extract_session_time_ranges()
    print(f"Found {len(ranges)} session time ranges in git log")

    # 3. Compute concurrent N per session
    concurrent_n = compute_concurrent_n(ranges)

    # 4. Merge: only sessions in both SESSION-LOG and git log
    merged = []
    for snum, sdata in log_sessions.items():
        if snum in concurrent_n:
            merged.append({
                **sdata,
                'concurrent_n': concurrent_n[snum],
            })
    merged.sort(key=lambda d: d['session_num'])
    print(f"Merged {len(merged)} sessions with both L+P data and git timestamps")

    # Distribution of concurrent N
    n_dist = defaultdict(int)
    for d in merged:
        n_dist[d['concurrent_n']] += 1
    print(f"\nConcurrent N distribution: {dict(sorted(n_dist.items()))}")

    # 5. Bin by concurrent N
    bins = [(1, 1), (2, 2), (3, 4), (5, 8), (9, 15), (16, 50)]
    n_bins = compute_n_bins(merged, bins)
    print("\n=== Empirical L+P by concurrent N ===")
    for b in n_bins:
        if b['n_sessions'] > 0:
            print(f"  {b['bin']:>8s}: {b['mean_lp']:.2f} L+P/session "
                  f"(std={b['std_lp']:.2f}, n={b['n_sessions']})")

    # 6. Estimate coordination cost
    coord = estimate_coordination_cost(merged)
    print(f"\n=== Coordination cost (linear regression) ===")
    if 'error' not in coord:
        print(f"  L+P = {coord['alpha']:.2f} + {coord['beta']:.3f}*N")
        print(f"  Baseline at N=1: {coord['baseline_at_n1']:.2f}")
        print(f"  Coordination cost/agent: {coord['coordination_cost_per_agent']:.4f}")
        print(f"  R² = {coord['r_squared']}")
    else:
        print(f"  {coord['error']}")

    # 7. Estimate rho
    rho = estimate_rho_from_sessions(merged)
    print(f"\n=== Error correlation (rho) ===")
    print(f"  rho (ICC): {rho['rho_estimate']}")

    # 8. S186 model predictions
    s186_params = {'baseline': 0.65, 'std': 0.20, 'rho': 0.032, 'coord_cost': 0.01}
    s186_preds, s186_n = model_predictions(**s186_params)
    print(f"\n=== S186 model: N*={s186_n} ===")

    # 9. Empirical model predictions
    emp_n = 0
    emp_params = {}
    if 'error' not in coord:
        all_lps = [d['lp'] for d in merged]
        emp_std = (sum((x - sum(all_lps)/len(all_lps))**2 for x in all_lps)
                   / max(len(all_lps) - 1, 1)) ** 0.5
        emp_params = {
            'baseline': coord['baseline_at_n1'],
            'std': round(emp_std, 4),
            'rho': rho['rho_estimate'],
            'coord_cost': coord['coordination_cost_per_agent'],
        }
        emp_preds, emp_n = model_predictions(**emp_params)
        print(f"\n=== Empirical model: N*={emp_n} ===")
        print(f"  baseline={emp_params['baseline']}, std={emp_params['std']}, "
              f"rho={emp_params['rho']}, coord_cost={emp_params['coord_cost']}")

    # 10. Era comparison (pre-S186 vs S186-S306 vs S306+)
    eras = {
        'pre_S186': [d for d in merged if d['session_num'] < 186],
        'S186_S306': [d for d in merged if 186 <= d['session_num'] < 306],
        'S306_plus': [d for d in merged if d['session_num'] >= 306],
    }
    era_stats = {}
    for era_name, era_data in eras.items():
        if era_data:
            lps = [d['lp'] for d in era_data]
            ns = [d['concurrent_n'] for d in era_data]
            era_stats[era_name] = {
                'n_sessions': len(era_data),
                'mean_lp': round(sum(lps)/len(lps), 3),
                'mean_concurrent_n': round(sum(ns)/len(ns), 2),
                'max_concurrent_n': max(ns),
            }
    print(f"\n=== Era comparison ===")
    for era, stats in era_stats.items():
        print(f"  {era}: mean_lp={stats['mean_lp']}, "
              f"mean_N={stats['mean_concurrent_n']}, n={stats['n_sessions']}")

    # 11. Compile results
    result = {
        'session': args.session,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'frontier': 'F-IS3',
        'experiment': 'empirical_grounding',
        'method': 'git-log timestamp overlap for concurrency detection',
        'expect': (
            "spawn_math.py N* predictions diverge from observed. "
            "Coordination cost floor (0.01) understates reality by 10-50x. "
            "Effective rho > 0.2. L-629 ceiling constrains N* to 1-2."
        ),
        'n_sessions_parsed': len(log_sessions),
        'n_sessions_merged': len(merged),
        'concurrent_n_distribution': dict(sorted(n_dist.items())),
        'n_bins': n_bins,
        'coordination_cost': coord,
        'rho_estimate': rho,
        's186_model': {'params': s186_params, 'best_n': s186_n},
        'empirical_model': {'params': emp_params, 'best_n': emp_n},
        'era_comparison': era_stats,
    }

    # Verdicts
    verdicts = []
    if 'error' not in coord:
        cc = coord['coordination_cost_per_agent']
        if cc > 0:
            verdicts.append(f"coordination_cost={cc:.4f} vs S186=0.01 ({cc/0.01:.1f}x)")
        else:
            verdicts.append(f"coordination_cost={cc:.4f} (NEGATIVE — more agents help)")
    verdicts.append(f"rho={rho['rho_estimate']} vs S186=0.032")
    if emp_n > 0:
        verdicts.append(f"empirical_N*={emp_n} vs S186_N*={s186_n}")

    result['verdicts'] = verdicts
    result['actual'] = '; '.join(verdicts)

    # Diff computation
    diffs = []
    if 'error' not in coord:
        if coord['coordination_cost_per_agent'] > 0.01:
            diffs.append("Cost higher than S186 — confirmed understated")
        elif coord['coordination_cost_per_agent'] <= 0:
            diffs.append("Cost NEGATIVE or zero — adding agents increases per-session output (unexpected)")
    if rho['rho_estimate'] < 0.2:
        diffs.append("rho < 0.2 — predicted rho > 0.2 was WRONG")
    result['diff'] = '; '.join(diffs) if diffs else 'no surprises'

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nArtifact: {out_path}")
    print(f"Verdicts: {'; '.join(verdicts)}")
    if diffs:
        print(f"Diff: {'; '.join(diffs)}")


if __name__ == '__main__':
    main()
