#!/usr/bin/env python3
"""F-NK5 remaining item #3: Predict K_avg from DOMEX session proportion.

Method: rolling-window regression. For each window of W=50 lessons (stride=10),
compute:
  - K_avg: mean outgoing citations per lesson in window
  - DOMEX_pct: fraction of sessions in window classified as DOMEX
  - era: session range (early <S186, mid S186-S310, late S310+)

Models tested:
  1. OLS: K_avg ~ DOMEX_pct
  2. OLS: K_avg ~ DOMEX_pct + era_mid + era_late  (era controls)
  3. Lag model: K_avg(t+1) ~ DOMEX_pct(t)  (does DOMEX CAUSE later K_avg?)
  4. Cumulative: K_avg(1..N) ~ cumulative_DOMEX_pct(1..N)

Hypothesis: R² > 0.6 for bivariate model, DOMEX proportion is monotonically
related to K_avg.
"""
import json, math, re, statistics, sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
LESSONS = ROOT / "memory" / "lessons"
SLOG = ROOT / "memory" / "SESSION-LOG.md"

WINDOW = 50
STRIDE = 10

def parse_lessons():
    """Return sorted list of (lesson_id, session, out_citation_count)."""
    results = []
    cite_re = re.compile(r'\bL-(\d+)\b')
    session_re = re.compile(r'Session:\s*S?(\d+)', re.IGNORECASE)
    existing = set()
    for p in LESSONS.glob("L-*.md"):
        m = re.match(r'L-(\d+)', p.stem)
        if m:
            existing.add(int(m.group(1)))
    for p in sorted(LESSONS.glob("L-*.md")):
        m = re.match(r'L-(\d+)', p.stem)
        if not m:
            continue
        lid = int(m.group(1))
        text = p.read_text(errors='replace')
        sm = session_re.search(text)
        if not sm:
            continue
        session = int(sm.group(1))
        out = set()
        for cm in cite_re.finditer(text):
            cited = int(cm.group(1))
            if cited != lid and cited in existing:
                out.add(cited)
        results.append((lid, session, len(out)))
    results.sort(key=lambda x: x[0])
    return results


def classify_sessions():
    """Classify each session by type from SESSION-LOG.md."""
    types = {}
    if not SLOG.exists():
        return types
    for line in SLOG.read_text(errors='replace').splitlines():
        m = re.match(r'S(\d+)\w*\s*\|', line)
        if not m:
            continue
        sn = int(m.group(1))
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


def ols_regression(x, y):
    """Simple OLS: y = a + b*x. Returns (a, b, r_squared, se_b)."""
    n = len(x)
    if n < 3:
        return (0, 0, 0, float('inf'))
    x_bar = sum(x) / n
    y_bar = sum(y) / n
    ss_xx = sum((xi - x_bar)**2 for xi in x)
    ss_yy = sum((yi - y_bar)**2 for yi in y)
    ss_xy = sum((xi - x_bar) * (yi - y_bar) for xi, yi in zip(x, y))
    if ss_xx == 0 or ss_yy == 0:
        return (y_bar, 0, 0, float('inf'))
    b = ss_xy / ss_xx
    a = y_bar - b * x_bar
    r_sq = (ss_xy**2) / (ss_xx * ss_yy)
    # Standard error of b
    y_pred = [a + b * xi for xi in x]
    sse = sum((yi - yp)**2 for yi, yp in zip(y, y_pred))
    mse = sse / (n - 2) if n > 2 else 0
    se_b = math.sqrt(mse / ss_xx) if ss_xx > 0 and mse >= 0 else float('inf')
    return (a, b, r_sq, se_b)


def multi_ols(X_cols, y):
    """Multi-variate OLS using normal equations (no numpy).
    X_cols: list of lists (each inner list is a predictor column).
    Returns: (coeffs, r_squared) where coeffs[0] is intercept."""
    n = len(y)
    k = len(X_cols)
    # Build design matrix with intercept
    X = [[1.0] + [X_cols[j][i] for j in range(k)] for i in range(n)]
    # X^T X
    p = k + 1
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(p)] for a in range(p)]
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(p)]
    # Solve via Gaussian elimination
    M = [XtX[i][:] + [Xty[i]] for i in range(p)]
    for col in range(p):
        # Pivot
        max_row = max(range(col, p), key=lambda r: abs(M[r][col]))
        M[col], M[max_row] = M[max_row], M[col]
        if abs(M[col][col]) < 1e-12:
            return [0] * p, 0
        for row in range(p):
            if row == col:
                continue
            factor = M[row][col] / M[col][col]
            for j in range(p + 1):
                M[row][j] -= factor * M[col][j]
    coeffs = [M[i][p] / M[i][i] if abs(M[i][i]) > 1e-12 else 0 for i in range(p)]
    # R²
    y_bar = sum(y) / n
    ss_tot = sum((yi - y_bar)**2 for yi in y)
    y_pred = [sum(coeffs[a] * X[i][a] for a in range(p)) for i in range(n)]
    ss_res = sum((yi - yp)**2 for yi, yp in zip(y, y_pred))
    r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return coeffs, r_sq


def main():
    lessons = parse_lessons()
    session_types = classify_sessions()
    n_total = len(lessons)

    print(f"=== F-NK5: K_avg Prediction from DOMEX Proportion ===")
    print(f"Total lessons: {n_total}")
    print(f"Window: {WINDOW}, Stride: {STRIDE}")
    print()

    # Build rolling windows
    windows = []
    for start in range(0, n_total - WINDOW + 1, STRIDE):
        chunk = lessons[start:start + WINDOW]
        # K_avg for this window
        edges = [c[2] for c in chunk]
        k_avg = sum(edges) / len(edges)
        # Session set
        sessions = set(c[1] for c in chunk)
        # DOMEX fraction
        domex_count = sum(1 for s in sessions if session_types.get(s) == 'DOMEX')
        domex_pct = domex_count / len(sessions) if sessions else 0
        # Era
        med_session = sorted(sessions)[len(sessions) // 2]
        if med_session < 186:
            era = 'early'
        elif med_session < 310:
            era = 'mid'
        else:
            era = 'late'
        # Lesson range
        l_min = chunk[0][0]
        l_max = chunk[-1][0]
        s_min = min(c[1] for c in chunk)
        s_max = max(c[1] for c in chunk)

        windows.append({
            'start_idx': start,
            'l_range': (l_min, l_max),
            's_range': (s_min, s_max),
            'k_avg': k_avg,
            'domex_pct': domex_pct,
            'domex_count': domex_count,
            'n_sessions': len(sessions),
            'era': era,
            'med_session': med_session
        })

    print(f"Rolling windows: {len(windows)}")
    print()

    # === Model 1: Bivariate OLS K_avg ~ DOMEX_pct ===
    x_domex = [w['domex_pct'] for w in windows]
    y_kavg = [w['k_avg'] for w in windows]

    a1, b1, r2_1, se1 = ols_regression(x_domex, y_kavg)
    t_stat = b1 / se1 if se1 > 0 else 0
    print(f"=== Model 1: K_avg ~ DOMEX_pct (bivariate OLS) ===")
    print(f"  intercept = {a1:.4f}")
    print(f"  slope     = {b1:.4f} (SE={se1:.4f}, t={t_stat:.2f})")
    print(f"  R²        = {r2_1:.4f}")
    print(f"  n_windows = {len(windows)}")
    sig = "***" if abs(t_stat) > 3.29 else "**" if abs(t_stat) > 2.58 else "*" if abs(t_stat) > 1.96 else "ns"
    print(f"  significance: {sig}")
    print()

    # === Model 2: K_avg ~ DOMEX_pct + era_mid + era_late ===
    era_mid = [1.0 if w['era'] == 'mid' else 0.0 for w in windows]
    era_late = [1.0 if w['era'] == 'late' else 0.0 for w in windows]
    coeffs2, r2_2 = multi_ols([x_domex, era_mid, era_late], y_kavg)
    print(f"=== Model 2: K_avg ~ DOMEX_pct + era_mid + era_late ===")
    print(f"  intercept  = {coeffs2[0]:.4f}")
    print(f"  DOMEX_pct  = {coeffs2[1]:.4f}")
    print(f"  era_mid    = {coeffs2[2]:.4f}")
    print(f"  era_late   = {coeffs2[3]:.4f}")
    print(f"  R²         = {r2_2:.4f}")
    # Adjusted R² (k=3 predictors, n=len(windows))
    n = len(windows)
    adj_r2_2 = 1 - (1 - r2_2) * (n - 1) / (n - 4) if n > 4 else r2_2
    print(f"  Adj. R²    = {adj_r2_2:.4f}")
    print()

    # === Model 3: Lag model K_avg(t+1) ~ DOMEX_pct(t) ===
    if len(windows) > 2:
        x_lag = [windows[i]['domex_pct'] for i in range(len(windows) - 1)]
        y_lag = [windows[i + 1]['k_avg'] for i in range(len(windows) - 1)]
        a3, b3, r2_3, se3 = ols_regression(x_lag, y_lag)
        t3 = b3 / se3 if se3 > 0 else 0
        print(f"=== Model 3: K_avg(t+1) ~ DOMEX_pct(t) (lagged) ===")
        print(f"  intercept = {a3:.4f}")
        print(f"  slope     = {b3:.4f} (SE={se3:.4f}, t={t3:.2f})")
        print(f"  R²        = {r2_3:.4f}")
        sig3 = "***" if abs(t3) > 3.29 else "**" if abs(t3) > 2.58 else "*" if abs(t3) > 1.96 else "ns"
        print(f"  significance: {sig3}")
        print()

    # === Model 4: Cumulative model ===
    # For each lesson index i, compute K_avg(1..i) and cumulative DOMEX%
    cum_kavg = []
    cum_domex = []
    cum_edges = 0
    all_sessions_seen = set()
    domex_sessions_seen = set()
    for i, (lid, session, out) in enumerate(lessons, 1):
        cum_edges += out
        all_sessions_seen.add(session)
        if session_types.get(session) == 'DOMEX':
            domex_sessions_seen.add(session)
        if i >= 20:  # Need at least 20 lessons
            cum_kavg.append(cum_edges / i)
            cum_domex.append(len(domex_sessions_seen) / len(all_sessions_seen) if all_sessions_seen else 0)

    a4, b4, r2_4, se4 = ols_regression(cum_domex, cum_kavg)
    t4 = b4 / se4 if se4 > 0 else 0
    print(f"=== Model 4: Cumulative K_avg ~ Cumulative DOMEX% ===")
    print(f"  intercept = {a4:.4f}")
    print(f"  slope     = {b4:.4f} (SE={se4:.4f}, t={t4:.2f})")
    print(f"  R²        = {r2_4:.4f}")
    sig4 = "***" if abs(t4) > 3.29 else "**" if abs(t4) > 2.58 else "*" if abs(t4) > 1.96 else "ns"
    print(f"  significance: {sig4}")
    print(f"  WARNING: cumulative model has spurious correlation risk (both increase over time)")
    print()

    # === Spearman rank correlation (non-parametric check) ===
    def spearman(x, y):
        n = len(x)
        rx = [0] * n
        ry = [0] * n
        for ranked, original in [(rx, x), (ry, y)]:
            order = sorted(range(n), key=lambda i: original[i])
            for rank, idx in enumerate(order):
                ranked[idx] = rank + 1
        d_sq = sum((rx[i] - ry[i])**2 for i in range(n))
        return 1 - (6 * d_sq) / (n * (n**2 - 1))

    rho = spearman(x_domex, y_kavg)
    print(f"=== Spearman Rank Correlation (DOMEX_pct vs K_avg) ===")
    print(f"  rho = {rho:.4f}")
    print()

    # === Monotonicity check ===
    # Group windows by DOMEX_pct bins
    bins = [(0, 0.05), (0.05, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)]
    print(f"=== DOMEX% Bins → K_avg ===")
    print(f"{'Bin':<12} {'N':>4} {'Mean K':>8} {'Std K':>8}")
    print("-" * 36)
    bin_data = []
    for lo, hi in bins:
        ws = [w for w in windows if lo <= w['domex_pct'] < hi]
        if ws:
            ks = [w['k_avg'] for w in ws]
            mean_k = sum(ks) / len(ks)
            std_k = statistics.stdev(ks) if len(ks) > 1 else 0
            print(f"[{lo:.0%}-{hi:.0%}){' ':<4} {len(ws):>4} {mean_k:>8.3f} {std_k:>8.3f}")
            bin_data.append({'bin': f'{lo:.0%}-{hi:.0%}', 'n': len(ws), 'mean_k': round(mean_k, 4), 'std_k': round(std_k, 4)})
    print()

    # Check monotonicity
    bin_means = [b['mean_k'] for b in bin_data]
    is_monotonic = all(bin_means[i] <= bin_means[i+1] for i in range(len(bin_means)-1))
    print(f"Monotonic: {'YES' if is_monotonic else 'NO'}")

    # === Window scatter (first/last 5 for inspection) ===
    print(f"\n=== Sample Windows ===")
    print(f"{'Idx':<5} {'Sessions':<12} {'DOMEX%':>7} {'K_avg':>7} {'Era':<6}")
    for w in windows[:5] + windows[-5:]:
        print(f"{w['start_idx']:<5} S{w['s_range'][0]}-S{w['s_range'][1]:<5} {w['domex_pct']:>7.1%} {w['k_avg']:>7.3f} {w['era']:<6}")

    # === Save artifact ===
    artifact = {
        'experiment': 'F-NK5-kavg-prediction',
        'session': 'S372',
        'description': 'Predict K_avg from DOMEX session proportion via rolling-window regression',
        'n_lessons': n_total,
        'window_size': WINDOW,
        'stride': STRIDE,
        'n_windows': len(windows),
        'model_1_bivariate': {
            'formula': 'K_avg ~ DOMEX_pct',
            'intercept': round(a1, 4),
            'slope': round(b1, 4),
            'se_slope': round(se1, 4),
            't_stat': round(t_stat, 2),
            'r_squared': round(r2_1, 4),
            'significant': sig
        },
        'model_2_era_controls': {
            'formula': 'K_avg ~ DOMEX_pct + era_mid + era_late',
            'coefficients': {
                'intercept': round(coeffs2[0], 4),
                'DOMEX_pct': round(coeffs2[1], 4),
                'era_mid': round(coeffs2[2], 4),
                'era_late': round(coeffs2[3], 4)
            },
            'r_squared': round(r2_2, 4),
            'adj_r_squared': round(adj_r2_2, 4)
        },
        'model_3_lagged': {
            'formula': 'K_avg(t+1) ~ DOMEX_pct(t)',
            'intercept': round(a3, 4),
            'slope': round(b3, 4),
            'r_squared': round(r2_3, 4),
            'significant': sig3
        },
        'model_4_cumulative': {
            'formula': 'Cumulative_K_avg ~ Cumulative_DOMEX%',
            'intercept': round(a4, 4),
            'slope': round(b4, 4),
            'r_squared': round(r2_4, 4),
            'significant': sig4,
            'warning': 'spurious correlation risk (both increase over time)'
        },
        'spearman_rho': round(rho, 4),
        'monotonic': is_monotonic,
        'bin_analysis': bin_data,
        'windows_sample': [
            {'sessions': f"S{w['s_range'][0]}-S{w['s_range'][1]}",
             'domex_pct': round(w['domex_pct'], 3),
             'k_avg': round(w['k_avg'], 3),
             'era': w['era']}
            for w in windows
        ]
    }

    out_path = ROOT / "experiments" / "nk-complexity" / "f-nk5-kavg-prediction-s372.json"
    with open(out_path, 'w') as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact: {out_path.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
