#!/usr/bin/env python3
"""F-SP8 S540: Rolling-window OU attractor drift + within-regime ceiling prediction.

Hypotheses:
1. Rolling-window OU LR mean has shifted upward (not stable) — attractor itself drifts.
2. Quality approaching within-regime ceiling predicts regime transitions (>60% precision).

Pre-registered expectations:
- LR mean drift: >0.3 Sharpe range across 100-session rolling windows
- Ceiling proximity: >60% precision for predicting transitions
- Falsified if: LR mean stable (±0.3), ceiling proximity <50% (coin flip)
"""
import json, os, glob, sys
import numpy as np
from collections import defaultdict

def load_sharpe_series():
    """Load (lesson_num, session, sharpe) from lesson files."""
    lessons = []
    for f in sorted(glob.glob('memory/lessons/L-*.md')):
        lid = os.path.basename(f).replace('.md', '')
        num = int(lid.split('-')[1])
        sharpe = session = None
        with open(f) as fh:
            for line in fh:
                if 'Sharpe:' in line:
                    parts = line.split('Sharpe:')
                    if len(parts) > 1:
                        try: sharpe = int(parts[1].strip().split()[0].strip('|'))
                        except: pass
                if 'Session:' in line:
                    parts = line.split('Session:')
                    if len(parts) > 1:
                        s = parts[1].strip().split()[0].strip('|')
                        if s.startswith('S'):
                            try: session = int(s[1:])
                            except: pass
        if sharpe is not None and session is not None:
            lessons.append((num, session, sharpe))
    lessons.sort(key=lambda x: x[0])
    return lessons

def rolling_ou_estimation(lessons, window=100, step=25):
    """Estimate OU parameters on rolling windows of sessions."""
    # Group by session
    by_session = defaultdict(list)
    for _, s, sharpe in lessons:
        by_session[s].append(sharpe)

    sessions = sorted(by_session.keys())
    session_means = {s: np.mean(by_session[s]) for s in sessions}

    results = []
    for start_idx in range(0, len(sessions) - window + 1, step):
        win_sessions = sessions[start_idx:start_idx + window]
        win_start, win_end = win_sessions[0], win_sessions[-1]

        # Build era means within window (25-session eras)
        era_size = 25
        era_means = []
        for era_start in range(0, len(win_sessions), era_size):
            era_sess = win_sessions[era_start:era_start + era_size]
            era_sharpes = []
            for s in era_sess:
                era_sharpes.extend(by_session[s])
            if era_sharpes:
                era_means.append(np.mean(era_sharpes))

        if len(era_means) < 3:
            continue

        era_means = np.array(era_means)

        # AR(1) estimation on era means → OU parameters
        x = era_means[:-1]
        y = era_means[1:]
        if len(x) < 2:
            continue

        # OLS: y = a + b*x
        n = len(x)
        xm, ym = np.mean(x), np.mean(y)
        b = np.sum((x - xm) * (y - ym)) / (np.sum((x - xm)**2) + 1e-12)
        a = ym - b * xm

        beta = 1 - b  # mean-reversion speed
        lr_mean = a / (1 - b + 1e-12) if abs(1 - b) > 0.01 else np.mean(era_means)

        results.append({
            'window_start': int(win_start),
            'window_end': int(win_end),
            'window_center': int((win_start + win_end) / 2),
            'n_eras': len(era_means),
            'n_lessons': sum(len(by_session[s]) for s in win_sessions),
            'beta': round(float(beta), 3),
            'lr_mean': round(float(lr_mean), 3),
            'window_mean': round(float(np.mean(era_means)), 3),
            'window_std': round(float(np.std(era_means)), 3),
        })

    return results

def regime_ceiling_prediction(lessons):
    """Test whether quality approaching within-regime ceiling predicts transitions.

    Use structural breaks from S538 (L-555, L-1076) to define regimes.
    Within each regime, test if lessons near the ceiling (>1σ above regime mean)
    cluster before transition points.
    """
    # Structural breaks from L-1598 (lesson indices, not session numbers)
    break_lessons = [555, 1076]

    # Build lesson-level series
    nums = np.array([l[0] for l in lessons])
    sharpes = np.array([l[2] for l in lessons])
    sessions = np.array([l[1] for l in lessons])

    # Define regimes
    regimes = []
    prev_idx = 0
    for bp in break_lessons:
        mask = nums < bp
        if prev_idx > 0:
            mask = mask & (nums >= prev_idx)
        regime_sharpes = sharpes[mask]
        regime_nums = nums[mask]
        regime_sessions = sessions[mask]
        if len(regime_sharpes) > 0:
            regimes.append({
                'start_lesson': int(regime_nums[0]),
                'end_lesson': int(regime_nums[-1]),
                'start_session': int(regime_sessions[0]),
                'end_session': int(regime_sessions[-1]),
                'mean': float(np.mean(regime_sharpes)),
                'std': float(np.std(regime_sharpes)),
                'n': len(regime_sharpes),
            })
        prev_idx = bp

    # Final regime
    mask = nums >= break_lessons[-1]
    regime_sharpes = sharpes[mask]
    regime_nums = nums[mask]
    regime_sessions = sessions[mask]
    if len(regime_sharpes) > 0:
        regimes.append({
            'start_lesson': int(regime_nums[0]),
            'end_lesson': int(regime_nums[-1]),
            'start_session': int(regime_sessions[0]),
            'end_session': int(regime_sessions[-1]),
            'mean': float(np.mean(regime_sharpes)),
            'std': float(np.std(regime_sharpes)),
            'n': len(regime_sharpes),
        })

    # For each regime except the last, check if quality near end is elevated
    # "Ceiling proximity": mean of last 20% of regime vs regime mean
    transition_signals = []
    for i, r in enumerate(regimes[:-1]):
        mask = (nums >= r['start_lesson']) & (nums <= r['end_lesson'])
        reg_sharpes = sharpes[mask]
        reg_nums = nums[mask]

        n = len(reg_sharpes)
        tail_size = max(int(n * 0.2), 5)
        tail_mean = float(np.mean(reg_sharpes[-tail_size:]))
        body_mean = float(np.mean(reg_sharpes[:-tail_size]))

        # Z-score of tail relative to body
        body_std = float(np.std(reg_sharpes[:-tail_size]))
        z_tail = (tail_mean - body_mean) / (body_std + 1e-12)

        # Also check: was the regime mean approached from below?
        # Rolling 20-lesson mean at regime end
        rolling_end = float(np.mean(reg_sharpes[-20:])) if n >= 20 else tail_mean

        transition_signals.append({
            'regime': i + 1,
            'n': n,
            'regime_mean': round(r['mean'], 3),
            'regime_std': round(r['std'], 3),
            'body_mean': round(body_mean, 3),
            'tail_mean': round(tail_mean, 3),
            'z_tail': round(z_tail, 3),
            'rolling_end_20': round(rolling_end, 3),
            'elevated': z_tail > 0.5,
        })

    # Now test: does quality WITHIN a regime show acceleration before transition?
    # Use smaller windows (30-lesson) to detect acceleration
    acceleration_signals = []
    for i, r in enumerate(regimes[:-1]):
        mask = (nums >= r['start_lesson']) & (nums <= r['end_lesson'])
        reg_sharpes = sharpes[mask]

        n = len(reg_sharpes)
        if n < 60:
            continue

        # Split into thirds
        third = n // 3
        first_third = float(np.mean(reg_sharpes[:third]))
        mid_third = float(np.mean(reg_sharpes[third:2*third]))
        last_third = float(np.mean(reg_sharpes[2*third:]))

        # Acceleration: is last-mid > mid-first?
        accel = (last_third - mid_third) - (mid_third - first_third)

        acceleration_signals.append({
            'regime': i + 1,
            'first_third': round(first_third, 3),
            'mid_third': round(mid_third, 3),
            'last_third': round(last_third, 3),
            'acceleration': round(accel, 3),
            'accelerating': accel > 0,
        })

    return regimes, transition_signals, acceleration_signals

def main():
    lessons = load_sharpe_series()
    print(f"Loaded {len(lessons)} lessons")

    # === Hypothesis 1: Rolling-window OU attractor drift ===
    print("\n=== H1: Rolling-window OU attractor drift ===")
    rolling = rolling_ou_estimation(lessons, window=100, step=25)

    lr_means = [r['lr_mean'] for r in rolling]
    lr_range = max(lr_means) - min(lr_means) if lr_means else 0

    print(f"Windows: {len(rolling)}")
    for r in rolling:
        print(f"  S{r['window_start']}-S{r['window_end']}: "
              f"LR_mean={r['lr_mean']:.3f}, beta={r['beta']:.3f}, "
              f"win_mean={r['window_mean']:.3f} ± {r['window_std']:.3f}")

    print(f"\nLR mean range: {lr_range:.3f}")
    print(f"LR mean min: {min(lr_means):.3f} (S{rolling[lr_means.index(min(lr_means))]['window_center']})")
    print(f"LR mean max: {max(lr_means):.3f} (S{rolling[lr_means.index(max(lr_means))]['window_center']})")

    h1_result = "CONFIRMED" if lr_range > 0.3 else "FALSIFIED"
    print(f"\nH1 verdict: {h1_result} (LR mean range {lr_range:.3f} {'>' if lr_range > 0.3 else '<='} 0.3)")

    # Trend in LR mean
    if len(lr_means) >= 3:
        centers = np.array([r['window_center'] for r in rolling])
        lr_arr = np.array(lr_means)
        # Simple regression
        cm, lm = np.mean(centers), np.mean(lr_arr)
        slope = np.sum((centers - cm) * (lr_arr - lm)) / (np.sum((centers - cm)**2) + 1e-12)
        print(f"LR mean trend: {slope:.5f} Sharpe/session")
        print(f"Prediction: LR mean at S600 ≈ {lm + slope * (600 - cm):.3f}")

    # === Hypothesis 2: Within-regime ceiling prediction ===
    print("\n=== H2: Within-regime ceiling prediction ===")
    regimes, transitions, accelerations = regime_ceiling_prediction(lessons)

    print(f"\nRegimes: {len(regimes)}")
    for i, r in enumerate(regimes):
        print(f"  R{i+1}: L-{r['start_lesson']}..L-{r['end_lesson']} "
              f"(S{r['start_session']}-S{r['end_session']}), "
              f"n={r['n']}, mean={r['mean']:.3f} ± {r['std']:.3f}")

    print(f"\nTransition signals:")
    n_elevated = 0
    for t in transitions:
        print(f"  R{t['regime']}: body={t['body_mean']:.3f}, tail={t['tail_mean']:.3f}, "
              f"z={t['z_tail']:.3f}, elevated={t['elevated']}")
        if t['elevated']:
            n_elevated += 1

    precision = n_elevated / len(transitions) if transitions else 0
    h2_result = "CONFIRMED" if precision > 0.6 else "FALSIFIED" if precision < 0.5 else "PARTIAL"
    print(f"\nCeiling precision: {n_elevated}/{len(transitions)} = {precision:.1%}")
    print(f"H2 verdict: {h2_result} (precision {precision:.1%} vs 60% threshold)")

    print(f"\nAcceleration before transitions:")
    for a in accelerations:
        print(f"  R{a['regime']}: {a['first_third']:.3f} → {a['mid_third']:.3f} → {a['last_third']:.3f}, "
              f"accel={a['acceleration']:.3f}, accelerating={a['accelerating']}")

    # === Bonus: Does beta (mean-reversion speed) change? ===
    print("\n=== Bonus: Beta stability across windows ===")
    betas = [r['beta'] for r in rolling]
    print(f"Beta range: {min(betas):.3f} - {max(betas):.3f}")
    print(f"Beta mean: {np.mean(betas):.3f} ± {np.std(betas):.3f}")
    beta_stable = (max(betas) - min(betas)) < 0.5
    print(f"Beta stability: {'STABLE' if beta_stable else 'VARIABLE'}")

    # === Build experiment JSON ===
    result = {
        'experiment': 'DOMEX-SP-S540-ATTRACTOR',
        'frontier': 'F-SP8',
        'session': 'S540',
        'domain': 'stochastic-processes',
        'date': '2026-03-24',
        'expect': 'H1: Rolling-window LR mean range >0.3 (attractor drifts upward). H2: Within-regime ceiling proximity predicts transitions with >60% precision.',
        'actual': f'H1: {h1_result}. LR mean range {lr_range:.3f}. H2: {h2_result}. Ceiling precision {precision:.1%}.',
        'diff': '',  # filled after analysis
        'data': {
            'h1_rolling_ou': {
                'n_windows': len(rolling),
                'window_size': 100,
                'step': 25,
                'lr_mean_range': round(lr_range, 3),
                'lr_mean_min': round(min(lr_means), 3),
                'lr_mean_max': round(max(lr_means), 3),
                'lr_mean_trend_per_session': round(float(slope), 5) if len(lr_means) >= 3 else None,
                'windows': rolling,
                'verdict': h1_result,
            },
            'h2_ceiling_prediction': {
                'n_regimes': len(regimes),
                'regimes': [{k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()} for r in regimes],
                'transition_signals': transitions,
                'acceleration_signals': accelerations,
                'ceiling_precision': round(precision, 3),
                'n_elevated': n_elevated,
                'n_transitions': len(transitions),
                'verdict': h2_result,
            },
            'bonus_beta_stability': {
                'beta_range': [round(min(betas), 3), round(max(betas), 3)],
                'beta_mean': round(float(np.mean(betas)), 3),
                'beta_std': round(float(np.std(betas)), 3),
                'stable': beta_stable,
            },
        },
    }

    out_path = 'experiments/stochastic-processes/f-sp8-attractor-drift-s540.json'
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nArtifact: {out_path}")

    return result

if __name__ == '__main__':
    main()
