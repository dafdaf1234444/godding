#!/usr/bin/env python3
"""
f_far1_gap_regression.py — F-FAR1 Fallow Effect: Gap-Length Regression

Replaces the S189 binary fallow/continuous classification (which produced
continuous_n=0) with a continuous gap-length regression:

  Sharpe ~ gap_length + session_number

Where gap_length = sessions since domain was last active before this lesson.
If positive coefficient on gap_length → fallow effect confirmed.
If near-zero or negative → fallow effect falsified.

Controls for era (session_number) since early-era lessons have different
Sharpe distributions than late-era lessons.

Output: experiments/farming/f-far1-gap-regression-s466.json
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"
LANES_PATH = ROOT / "tasks" / "SWARM-LANES.md"


def _current_session() -> int:
    """Derive current session number from git log or lesson count."""
    import subprocess
    try:
        out = subprocess.check_output(
            ["git", "log", "--oneline", "-1", "--format=%s"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        )
        m = re.search(r'\[S(\d+)\]', out)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return len(list(LESSONS_DIR.glob("L-*.md")))


def _artifact_path() -> Path:
    return ROOT / "experiments" / "farming" / f"f-far1-gap-regression-s{_current_session()}.json"

# Domain aliases (from archived f_far1_fallow_measure.py)
DOMAIN_ALIASES = {
    "nk complexity": "nk-complexity", "nk-complexity": "nk-complexity",
    "nk": "nk-complexity", "distributed systems": "distributed-systems",
    "distributed-systems": "distributed-systems",
    "information-science": "information-science",
    "information science": "information-science",
    "operations-research": "operations-research",
    "operations research": "operations-research",
    "game-theory": "game-theory", "game theory": "game-theory",
    "control-theory": "control-theory", "control theory": "control-theory",
    "helper-swarm": "helper-swarm", "helper swarm": "helper-swarm",
    "protocol-engineering": "protocol-engineering",
    "protocol engineering": "protocol-engineering",
    "expert-swarm": "expert-swarm", "expert swarm": "expert-swarm",
    "catastrophic-risks": "catastrophic-risks",
    "catastrophic risks": "catastrophic-risks",
    "human-systems": "human-systems", "human systems": "human-systems",
    "random-matrix-theory": "random-matrix-theory",
    "social-media": "social-media", "string-theory": "string-theory",
    "meta": "meta", "ai": "ai", "brain": "brain", "conflict": "conflict",
    "economy": "economy", "evolution": "evolution", "finance": "finance",
    "gaming": "gaming", "governance": "governance", "health": "health",
    "history": "history", "linguistics": "linguistics", "physics": "physics",
    "psychology": "psychology", "statistics": "statistics",
    "strategy": "strategy", "farming": "farming", "quality": "quality",
    "tooling": "tooling", "dream": "dream", "empathy": "empathy",
    "evaluation": "evaluation", "cryptocurrency": "cryptocurrency",
    "cryptography": "cryptography", "guesstimates": "guesstimates",
    "competitions": "competitions", "graph-theory": "graph-theory",
    "security": "meta", "safety": "meta", "filtering": "meta",
    "knowledge-lifecycle": "meta", "knowledge-structure": "meta",
    "swarm-structure": "meta", "swarm-behavior": "meta",
    "coordination": "meta", "isomorphism": "meta",
}


def _normalize_domain(raw: str) -> str | None:
    raw = re.sub(r"\([^)]*\)", "", raw).strip()
    primary = re.split(r"[/|,]", raw)[0].strip().lower()
    return DOMAIN_ALIASES.get(primary, primary if primary else None)


def _parse_lessons() -> list[dict]:
    """Parse all lessons for session, domain, and explicit Sharpe from header."""
    results = []
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        lines = text[:1000]  # header is in first few lines

        sm = re.search(r"Session:\s*S?(\d+)", lines, re.IGNORECASE)
        if not sm:
            continue
        session = int(sm.group(1))

        dm = re.search(r"Domain:\s*([^\n|]+)", lines)
        if not dm:
            continue
        domain = _normalize_domain(dm.group(1).strip())
        if not domain:
            continue

        # Use explicit Sharpe from header (more reliable than computed)
        sh = re.search(r"Sharpe:\s*(\d+(?:\.\d+)?)", lines)
        if not sh:
            continue
        sharpe = float(sh.group(1))

        results.append({
            "file": f.name,
            "session": session,
            "domain": domain,
            "sharpe": sharpe,
        })
    return results


def _build_domain_session_map(lessons: list[dict]) -> dict[str, list[int]]:
    """Build domain → sorted list of sessions where domain appears."""
    dm: dict[str, set[int]] = defaultdict(set)
    for l in lessons:
        dm[l["domain"]].add(l["session"])
    return {d: sorted(s) for d, s in dm.items()}


def _compute_gap(session: int, domain: str, domain_sessions: dict) -> int | None:
    """Compute gap: sessions since domain was last active before this session."""
    sessions = domain_sessions.get(domain, [])
    # Find the most recent session BEFORE this one
    prior = [s for s in sessions if s < session]
    if not prior:
        return None  # first appearance — no gap to measure
    return session - max(prior)


def _ols_regression(x_vars: list[list[float]], y: list[float], var_names: list[str]) -> dict:
    """
    Simple OLS regression without external dependencies.
    x_vars: list of variable vectors (each same length as y)
    Returns coefficients, R², and basic stats.
    """
    n = len(y)
    k = len(x_vars)  # number of predictors (excluding intercept)

    if n < k + 2:
        return {"error": "insufficient data", "n": n}

    # Add intercept
    X = [[1.0] + [x_vars[j][i] for j in range(k)] for i in range(n)]

    # X^T X
    p = k + 1  # intercept + predictors
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(p)] for a in range(p)]
    # X^T y
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(p)]

    # Solve via Gaussian elimination
    aug = [XtX[i][:] + [Xty[i]] for i in range(p)]
    for col in range(p):
        # Pivot
        max_row = max(range(col, p), key=lambda r: abs(aug[r][col]))
        aug[col], aug[max_row] = aug[max_row], aug[col]
        if abs(aug[col][col]) < 1e-12:
            return {"error": "singular matrix", "n": n}
        for row in range(p):
            if row == col:
                continue
            factor = aug[row][col] / aug[col][col]
            for j in range(p + 1):
                aug[row][j] -= factor * aug[col][j]

    beta = [aug[i][p] / aug[i][i] for i in range(p)]

    # Predictions and R²
    y_hat = [sum(X[i][j] * beta[j] for j in range(p)) for i in range(n)]
    y_mean = sum(y) / n
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum((y[i] - y_hat[i]) ** 2 for i in range(n))
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    # Standard errors
    mse = ss_res / (n - p) if n > p else 0
    # Diagonal of (X^T X)^{-1} via already-solved augmented matrix
    # Re-solve for each unit vector to get inverse diagonal
    se = []
    for j in range(p):
        # Approximate: use the diagonal of the elimination result
        # For simplicity, compute (X^T X)^{-1} diagonal directly
        aug2 = [XtX[i][:] + [1.0 if i == j else 0.0] for i in range(p)]
        for col in range(p):
            max_row = max(range(col, p), key=lambda r: abs(aug2[r][col]))
            aug2[col], aug2[max_row] = aug2[max_row], aug2[col]
            if abs(aug2[col][col]) < 1e-12:
                se.append(None)
                break
            for row in range(p):
                if row == col:
                    continue
                factor = aug2[row][col] / aug2[col][col]
                for c in range(p + 1):
                    aug2[row][c] -= factor * aug2[col][c]
        else:
            diag_val = aug2[j][p] / aug2[j][j]
            se.append((mse * diag_val) ** 0.5 if mse * diag_val >= 0 else None)

    # T-statistics
    t_stats = []
    for j in range(p):
        if se[j] and se[j] > 0:
            t_stats.append(beta[j] / se[j])
        else:
            t_stats.append(None)

    names = ["intercept"] + var_names
    coefficients = {}
    for j in range(p):
        coefficients[names[j]] = {
            "beta": round(beta[j], 6),
            "se": round(se[j], 6) if se[j] else None,
            "t": round(t_stats[j], 4) if t_stats[j] else None,
        }

    return {
        "n": n,
        "k": k,
        "r_squared": round(r_squared, 6),
        "adj_r_squared": round(1 - (1 - r_squared) * (n - 1) / (n - p), 6) if n > p else None,
        "mse": round(mse, 6),
        "coefficients": coefficients,
    }


def run() -> dict:
    lessons = _parse_lessons()
    domain_sessions = _build_domain_session_map(lessons)

    # Compute gaps
    data_points = []
    skipped_first_appearance = 0
    for l in lessons:
        gap = _compute_gap(l["session"], l["domain"], domain_sessions)
        if gap is None:
            skipped_first_appearance += 1
            continue
        data_points.append({
            "file": l["file"],
            "session": l["session"],
            "domain": l["domain"],
            "sharpe": l["sharpe"],
            "gap": gap,
        })

    if len(data_points) < 10:
        return {
            "session": f"S{_current_session()}",
            "verdict": "INSUFFICIENT_DATA",
            "n": len(data_points),
            "skipped_first_appearance": skipped_first_appearance,
        }

    gaps = [d["gap"] for d in data_points]
    sessions = [d["session"] for d in data_points]
    sharpes = [d["sharpe"] for d in data_points]

    # Summary stats
    gap_mean = sum(gaps) / len(gaps)
    sharpe_mean = sum(sharpes) / len(sharpes)

    # Model 1: Sharpe ~ gap (simple)
    model_simple = _ols_regression([gaps], sharpes, ["gap"])

    # Model 2: Sharpe ~ gap + session (controlled for era)
    model_controlled = _ols_regression([gaps, sessions], sharpes, ["gap", "session"])

    # Model 3: Sharpe ~ gap + session + gap² (nonlinear fallow effect)
    gaps_sq = [g * g for g in gaps]
    model_nonlinear = _ols_regression(
        [gaps, sessions, gaps_sq], sharpes, ["gap", "session", "gap_squared"]
    )

    # Pearson correlation: gap vs sharpe
    cov = sum((gaps[i] - gap_mean) * (sharpes[i] - sharpe_mean) for i in range(len(gaps)))
    var_gap = sum((g - gap_mean) ** 2 for g in gaps)
    var_sharpe = sum((s - sharpe_mean) ** 2 for s in sharpes)
    r_pearson = cov / (var_gap * var_sharpe) ** 0.5 if var_gap > 0 and var_sharpe > 0 else 0

    # Gap distribution
    gap_quartiles = sorted(gaps)
    q25 = gap_quartiles[len(gap_quartiles) // 4]
    q50 = gap_quartiles[len(gap_quartiles) // 2]
    q75 = gap_quartiles[3 * len(gap_quartiles) // 4]

    # Domain-level analysis: mean Sharpe by gap quartile
    short_gap = [d for d in data_points if d["gap"] <= q25]
    medium_gap = [d for d in data_points if q25 < d["gap"] <= q50]
    long_gap = [d for d in data_points if q50 < d["gap"] <= q75]
    very_long_gap = [d for d in data_points if d["gap"] > q75]

    def _group_mean(group):
        return round(sum(d["sharpe"] for d in group) / len(group), 4) if group else None

    # Determine verdict
    gap_beta = model_controlled["coefficients"]["gap"]["beta"]
    gap_t = model_controlled["coefficients"]["gap"]["t"]

    if gap_t is not None and abs(gap_t) > 1.96:
        if gap_beta > 0:
            verdict = "FALLOW_CONFIRMED"
        else:
            verdict = "FALLOW_REFUTED"
    elif gap_t is not None and abs(gap_t) > 1.0:
        verdict = "WEAK_SIGNAL"
    else:
        verdict = "NO_EFFECT"

    # Per-domain gap effect (top 5 domains by lesson count)
    domain_counts = defaultdict(int)
    for d in data_points:
        domain_counts[d["domain"]] += 1
    top_domains = sorted(domain_counts.items(), key=lambda x: -x[1])[:8]

    domain_effects = {}
    for domain, count in top_domains:
        dom_points = [d for d in data_points if d["domain"] == domain]
        if len(dom_points) < 5:
            continue
        dom_gaps = [d["gap"] for d in dom_points]
        dom_sharpes = [d["sharpe"] for d in dom_points]
        dom_model = _ols_regression([dom_gaps], dom_sharpes, ["gap"])
        domain_effects[domain] = {
            "n": len(dom_points),
            "gap_beta": dom_model["coefficients"]["gap"]["beta"],
            "gap_t": dom_model["coefficients"]["gap"]["t"],
            "r_squared": dom_model["r_squared"],
        }

    result = {
        "session": f"S{_current_session()}",
        "experiment": f"DOMEX-FAR-S{_current_session()}",
        "frontier": "F-FAR1",
        "date": "2026-03-03",
        "methodology": "Gap-length OLS regression (continuous IV) replacing binary fallow/continuous",
        "improvement_over_s189": "S189 binary classification produced continuous_n=0. Gap regression uses continuous variable.",
        "n_total_lessons": len(lessons),
        "n_with_gap": len(data_points),
        "n_skipped_first_appearance": skipped_first_appearance,
        "gap_distribution": {
            "mean": round(gap_mean, 2),
            "q25": q25, "q50_median": q50, "q75": q75,
            "min": min(gaps), "max": max(gaps),
        },
        "sharpe_distribution": {
            "mean": round(sharpe_mean, 4),
            "min": min(sharpes), "max": max(sharpes),
        },
        "pearson_r_gap_sharpe": round(r_pearson, 6),
        "model_simple": model_simple,
        "model_controlled": model_controlled,
        "model_nonlinear": model_nonlinear,
        "quartile_analysis": {
            "short_gap_le_q25": {"n": len(short_gap), "mean_sharpe": _group_mean(short_gap), "gap_range": f"≤{q25}"},
            "medium_gap": {"n": len(medium_gap), "mean_sharpe": _group_mean(medium_gap), "gap_range": f"{q25+1}-{q50}"},
            "long_gap": {"n": len(long_gap), "mean_sharpe": _group_mean(long_gap), "gap_range": f"{q50+1}-{q75}"},
            "very_long_gap_gt_q75": {"n": len(very_long_gap), "mean_sharpe": _group_mean(very_long_gap), "gap_range": f">{q75}"},
        },
        "domain_effects": domain_effects,
        "verdict": verdict,
        "interpretation": (
            f"Gap coefficient β={gap_beta:.6f} (t={gap_t:.2f}) in era-controlled model. "
            f"Pearson r={r_pearson:.4f}. "
            f"{'Positive gap→Sharpe relationship supports fallow hypothesis.' if gap_beta > 0 else 'Negative/zero gap→Sharpe relationship challenges fallow hypothesis.'}"
        ),
        "expect": "Gap-length regression over domain-tagged lessons (N>>50) shows either positive correlation (gap predicts higher Sharpe, confirming fallow effect) or no correlation (falsifying B-FAR2). Effect size reported.",
        "actual": "TBD",
        "diff": "TBD",
    }

    return result


def main():
    result = run()

    out_path = _artifact_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    sess = _current_session()
    print(f"=== F-FAR1 Gap-Length Regression (S{sess}) ===")
    print(f"Total lessons parsed: {result.get('n_total_lessons', '?')}")
    print(f"Lessons with computable gap: {result.get('n_with_gap', '?')}")
    print(f"Skipped (first appearance): {result.get('n_skipped_first_appearance', '?')}")

    if "gap_distribution" in result:
        gd = result["gap_distribution"]
        print(f"\nGap distribution: mean={gd['mean']}, median={gd['q50_median']}, "
              f"Q25={gd['q25']}, Q75={gd['q75']}, max={gd['max']}")

    print(f"\nPearson r(gap, Sharpe): {result.get('pearson_r_gap_sharpe', '?')}")

    if "model_controlled" in result:
        mc = result["model_controlled"]
        print(f"\nControlled model (Sharpe ~ gap + session):")
        print(f"  R² = {mc['r_squared']}, adj R² = {mc.get('adj_r_squared', '?')}")
        for name, stats in mc["coefficients"].items():
            print(f"  {name}: β={stats['beta']}, t={stats.get('t', '?')}")

    if "quartile_analysis" in result:
        print(f"\nQuartile analysis (mean Sharpe by gap length):")
        for label, qa in result["quartile_analysis"].items():
            print(f"  {qa['gap_range']}: n={qa['n']}, mean_sharpe={qa['mean_sharpe']}")

    if "domain_effects" in result:
        print(f"\nPer-domain gap effects (top domains):")
        for domain, de in result["domain_effects"].items():
            print(f"  {domain}: n={de['n']}, β={de['gap_beta']}, t={de.get('gap_t', '?')}")

    print(f"\nVerdict: {result.get('verdict', '?')}")
    print(f"Interpretation: {result.get('interpretation', '?')}")
    print(f"\nArtifact: {out_path}")


if __name__ == "__main__":
    main()
