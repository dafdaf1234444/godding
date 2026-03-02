#!/usr/bin/env python3
"""F-EXP10 self-calibration: derive dispatch weights from outcome data.

The swarm directive: expert assessment must be swarmed — weights must be
empirically derived, not hardcoded. This experiment:

1. Parses all DOMEX lane outcomes (SWARM-LANES.md + archive)
2. For each domain, collects structural features (ISO, lessons, beliefs,
   principles, concept_types, resolved, active, experiments)
3. Correlates features with actual lesson yield per lane
4. Derives optimal weights via OLS regression (no external deps — pure Python)
5. Compares derived weights to current hardcoded weights
6. Outputs calibration artifact (JSON) usable by dispatch_optimizer.py

Evidence chain: L-654 (MIXED > PROVEN), L-749 (transient bonuses), L-671
(score fixes ≠ behavior fixes), L-750 (UCB1 +59% L/lane), SIG-32 (human
directive: expert assessment must be swarmed).
"""
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LANES_FILE = ROOT / "tasks" / "SWARM-LANES.md"
ARCHIVE_FILE = ROOT / "tasks" / "SWARM-LANES-ARCHIVE.md"
DOMAINS_DIR = ROOT / "domains"
EXPERIMENTS_DIR = ROOT / "experiments"

# Import domain abbreviation map from dispatch_optimizer
sys.path.insert(0, str(ROOT / "tools"))
try:
    from dispatch_optimizer import LANE_ABBREV_TO_DOMAIN, COUNCIL_TOPIC_TO_DOMAIN
except ImportError:
    LANE_ABBREV_TO_DOMAIN = {}
    COUNCIL_TOPIC_TO_DOMAIN = {}

# Current hardcoded weights from dispatch_optimizer.py (lines 540-571)
CURRENT_WEIGHTS = {
    "iso": 1.5,
    "lessons": 0.8,
    "beliefs": 1.5,
    "principles": 1.5,
    "concept_types": 2.5,
    "resolved": 2.0,
    "active": 1.5,
    "novelty": 2.0,
    "has_index": 1.0,
}


def parse_all_lanes():
    """Parse all DOMEX lanes from SWARM-LANES + archive."""
    lanes = []
    for filepath in (ARCHIVE_FILE, LANES_FILE):
        if not filepath.exists():
            continue
        text = filepath.read_text(encoding="utf-8", errors="ignore")
        for line in text.split("\n"):
            if "|" not in line or "DOMEX-" not in line:
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue

            lane_id = cols[2]
            session_str = cols[3]
            status = cols[11] if len(cols) > 11 else ""
            notes = cols[12] if len(cols) > 12 else ""
            etc = cols[10] if len(cols) > 10 else ""

            # Extract domain
            dom = None
            m = re.match(r"DOMEX-([A-Z0-9]+)-S\d+", lane_id)
            if m:
                dom = LANE_ABBREV_TO_DOMAIN.get(m.group(1), m.group(1).lower())
            if not dom:
                continue

            # Extract session
            sess_m = re.search(r"S(\d+)", session_str)
            if not sess_m:
                sess_m = re.search(r"S(\d+)", lane_id)
            session = int(sess_m.group(1)) if sess_m else None

            # Only closed lanes
            status_upper = status.upper()
            if "MERGED" not in status_upper and "ABANDONED" not in status_upper:
                continue

            merged = "MERGED" in status_upper
            # Count lessons mentioned in notes + etc
            lesson_refs = set(re.findall(r"\bL-(\d+)\b", notes + " " + etc))

            lanes.append({
                "lane_id": lane_id,
                "domain": dom,
                "session": session,
                "merged": merged,
                "lessons_produced": len(lesson_refs),
                "etc": etc,
            })

    # Deduplicate by lane_id (keep last occurrence)
    seen = {}
    for lane in lanes:
        seen[lane["lane_id"]] = lane
    return list(seen.values())


def get_domain_features():
    """Extract structural features for each domain (same as score_domain())."""
    features = {}
    if not DOMAINS_DIR.exists():
        return features

    for domain in sorted(os.listdir(DOMAINS_DIR)):
        domain_path = DOMAINS_DIR / domain
        if not domain_path.is_dir():
            continue

        frontier_path = domain_path / "tasks" / "FRONTIER.md"
        domain_md_path = domain_path / "DOMAIN.md"
        index_path = domain_path / "INDEX.md"
        exp_dir = EXPERIMENTS_DIR / domain

        # Active frontier count
        active_count = 0
        resolved_count = 0
        if frontier_path.exists():
            content = frontier_path.read_text(encoding="utf-8", errors="ignore")
            active_match = re.search(r"## Active\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
            if active_match:
                active_count = len(re.findall(r"^- \*\*F", active_match.group(1), re.MULTILINE))
            resolved_match = re.search(r"## Resolved.*", content, re.DOTALL)
            if resolved_match:
                resolved_count = len(re.findall(r"^\| F", resolved_match.group(), re.MULTILINE))

        # Concept counts from DOMAIN.md
        iso_count = lesson_count = belief_count = principle_count = 0
        if domain_md_path.exists():
            dm = domain_md_path.read_text(encoding="utf-8", errors="ignore")
            iso_count = len(set(re.findall(r"ISO-\d+", dm)))
            lesson_count = len(set(re.findall(r"\bL-\d{3,4}\b", dm)))
            belief_count = len(set(re.findall(r"\bB-?\d+\b", dm)))
            principle_count = len(set(re.findall(r"\bP-\d{3}\b", dm)))

        # Experiment count
        exp_count = 0
        if exp_dir.exists():
            exp_count = len(list(exp_dir.glob("*.json")))

        has_index = index_path.exists()

        concept_types = sum([
            iso_count > 0,
            lesson_count > 0,
            belief_count > 0,
            principle_count > 0,
            exp_count > 0,
        ])

        features[domain] = {
            "iso": iso_count,
            "lessons": lesson_count,
            "beliefs": belief_count,
            "principles": principle_count,
            "concept_types": concept_types,
            "resolved": resolved_count,
            "active": active_count,
            "experiments": exp_count,
            "novelty": 1.0 if exp_count == 0 else 0.0,
            "has_index": 1.0 if has_index else 0.0,
        }

    return features


def ridge_regression(X, y, alpha=1.0):
    """Pure-Python ridge regression: y = X @ beta.

    Ridge adds alpha * I to X^T X, handling collinearity that breaks OLS.
    Returns (beta, r_squared, residuals).
    """
    n = len(y)
    p = len(X[0]) if X else 0
    if n < 2 or p == 0:
        return None, 0.0, []

    # X^T X + alpha * I
    XtX = [[sum(X[i][j] * X[i][k] for i in range(n)) + (alpha if j == k else 0)
            for k in range(p)] for j in range(p)]
    # X^T y
    Xty = [sum(X[i][j] * y[i] for i in range(n)) for j in range(p)]

    # Gauss elimination
    aug = [XtX[j][:] + [Xty[j]] for j in range(p)]
    for col in range(p):
        max_row = max(range(col, p), key=lambda r: abs(aug[r][col]))
        aug[col], aug[max_row] = aug[max_row], aug[col]
        if abs(aug[col][col]) < 1e-12:
            return None, 0.0, []
        for row in range(p):
            if row == col:
                continue
            factor = aug[row][col] / aug[col][col]
            for k in range(p + 1):
                aug[row][k] -= factor * aug[col][k]

    beta = [aug[j][p] / aug[j][j] for j in range(p)]

    # R-squared
    y_hat = [sum(X[i][j] * beta[j] for j in range(p)) for i in range(n)]
    y_mean = sum(y) / n
    ss_res = sum((y[i] - y_hat[i]) ** 2 for i in range(n))
    ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
    r_sq = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    residuals = [y[i] - y_hat[i] for i in range(n)]
    return beta, r_sq, residuals


def stepwise_select(X, y, feature_names, max_features=5):
    """Forward stepwise feature selection using ridge regression.

    Returns best subset of features by greedy R² improvement.
    Avoids collinearity by adding one feature at a time.
    """
    n = len(y)
    selected = []
    remaining = list(range(len(feature_names)))
    best_r2 = 0.0
    history = []

    for step in range(min(max_features, len(feature_names))):
        best_candidate = None
        best_candidate_r2 = best_r2

        for j in remaining:
            trial = selected + [j]
            X_trial = [[X[i][k] for k in trial] for i in range(n)]
            beta, r2, _ = ridge_regression(X_trial, y, alpha=0.5)
            if beta is not None and r2 > best_candidate_r2:
                best_candidate = j
                best_candidate_r2 = r2

        if best_candidate is None:
            break

        selected.append(best_candidate)
        remaining.remove(best_candidate)
        best_r2 = best_candidate_r2
        history.append({
            "step": step + 1,
            "added": feature_names[best_candidate],
            "r_squared": round(best_r2, 4),
        })

    return selected, history


def pearson_r(x, y):
    """Pearson correlation coefficient."""
    n = len(x)
    if n < 3:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    dx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    dy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    return num / (dx * dy) if dx * dy > 0 else 0.0


def main():
    # 1. Parse all closed DOMEX lanes
    lanes = parse_all_lanes()
    print(f"Parsed {len(lanes)} closed DOMEX lanes")

    # 2. Aggregate by domain: lessons_produced per lane
    domain_outcomes = defaultdict(lambda: {"lanes": 0, "merged": 0, "lessons": 0, "lesson_list": []})
    for lane in lanes:
        d = domain_outcomes[lane["domain"]]
        d["lanes"] += 1
        if lane["merged"]:
            d["merged"] += 1
        d["lessons"] += lane["lessons_produced"]
        d["lesson_list"].append(lane["lessons_produced"])

    # 3. Get current structural features
    features = get_domain_features()

    # 4. Build regression dataset: one row per domain
    # Only include domains with >=3 closed lanes (sufficient data)
    feature_names = ["iso", "lessons", "beliefs", "principles", "concept_types",
                     "resolved", "active", "novelty", "has_index"]
    X = []
    y = []
    domain_labels = []
    for dom, outcome in sorted(domain_outcomes.items()):
        if outcome["lanes"] < 3:
            continue
        if dom not in features:
            continue
        feat = features[dom]
        row = [feat[f] for f in feature_names]
        X.append(row)
        yield_val = outcome["lessons"] / outcome["lanes"]  # L/lane
        y.append(yield_val)
        domain_labels.append(dom)

    print(f"\nRegression dataset: {len(X)} domains with >=3 lanes")
    print(f"Feature matrix: {len(X)}x{len(feature_names)}")

    # 5. Individual feature correlations with yield
    print(f"\n--- Feature-Yield Correlations (Pearson r) ---")
    correlations = {}
    for j, feat_name in enumerate(feature_names):
        col = [X[i][j] for i in range(len(X))]
        r = pearson_r(col, y)
        correlations[feat_name] = round(r, 3)
        current_w = CURRENT_WEIGHTS.get(feat_name, 0)
        sign_match = (r >= 0 and current_w > 0) or (r < 0 and current_w <= 0)
        indicator = "OK" if sign_match else "MISMATCH"
        print(f"  {feat_name:15s}: r={r:+.3f}  (current weight: {current_w})  [{indicator}]")

    # 6. Ridge regression: derive optimal weights (handles collinearity)
    print(f"\n--- Ridge Regression (L/lane = f(features), alpha=1.0) ---")
    beta, r_sq, residuals = ridge_regression(X, y, alpha=1.0)

    derived_weights = {}
    mismatches = []
    if beta is not None:
        print(f"  R² = {r_sq:.4f}")
        print(f"\n  {'Feature':15s} {'Derived':>8s} {'Current':>8s} {'Ratio':>8s} {'Verdict':>10s}")
        print(f"  {'-'*55}")
        for j, feat_name in enumerate(feature_names):
            derived_w = beta[j]
            current_w = CURRENT_WEIGHTS.get(feat_name, 0)
            ratio = derived_w / current_w if current_w != 0 else float('inf')
            if current_w == 0:
                verdict = "NEW"
            elif abs(ratio - 1.0) < 0.5:
                verdict = "CONFIRMED"
            elif (derived_w > 0) == (current_w > 0) and abs(ratio) < 3:
                verdict = "RESCALE"
            else:
                verdict = "WRONG"
                mismatches.append(feat_name)
            derived_weights[feat_name] = round(derived_w, 4)
            print(f"  {feat_name:15s} {derived_w:+8.4f} {current_w:+8.4f} {ratio:8.2f}x  {verdict}")

        # Residual analysis
        print(f"\n--- Residual Analysis (derived model prediction error) ---")
        residual_pairs = sorted(zip(domain_labels, residuals, y), key=lambda x: -abs(x[1]))
        for dom, res, actual in residual_pairs[:10]:
            direction = "UNDER" if res > 0 else "OVER"
            print(f"  {dom:25s}: actual={actual:.2f}, residual={res:+.3f} ({direction}-predicted)")

    # 6b. Stepwise feature selection — find minimal predictive subset
    print(f"\n--- Stepwise Feature Selection (max 5 features) ---")
    selected_idx, step_history = stepwise_select(X, y, feature_names, max_features=5)
    selected_features = [feature_names[i] for i in selected_idx]
    for step in step_history:
        print(f"  Step {step['step']}: +{step['added']:15s} → R²={step['r_squared']:.4f}")
    print(f"  Selected features: {selected_features}")

    # Re-run ridge on selected features only
    if selected_idx:
        X_sel = [[X[i][k] for k in selected_idx] for i in range(len(X))]
        beta_sel, r_sq_sel, _ = ridge_regression(X_sel, y, alpha=0.5)
        if beta_sel:
            print(f"\n  Reduced-model ridge (alpha=0.5):")
            print(f"  R² = {r_sq_sel:.4f}")
            for j, feat_name in enumerate(selected_features):
                print(f"    {feat_name:15s}: {beta_sel[j]:+.4f}")
    else:
        r_sq_sel = 0.0

    if beta is None:
        print(f"  Ridge regression failed (insufficient data)")
        mismatches = []

    # 7. Structural score vs actual yield
    print(f"\n--- Structural Score vs Actual Yield ---")
    struct_scores = []
    actual_yields = []
    for i, dom in enumerate(domain_labels):
        feat = features[dom]
        # Compute structural score using CURRENT weights
        score = (
            feat["iso"] * CURRENT_WEIGHTS["iso"]
            + feat["lessons"] * CURRENT_WEIGHTS["lessons"]
            + feat["beliefs"] * CURRENT_WEIGHTS["beliefs"]
            + feat["principles"] * CURRENT_WEIGHTS["principles"]
            + feat["concept_types"] * CURRENT_WEIGHTS["concept_types"]
            + feat["resolved"] * CURRENT_WEIGHTS["resolved"]
            + feat["active"] * CURRENT_WEIGHTS["active"]
            + feat["novelty"] * CURRENT_WEIGHTS["novelty"]
            + feat["has_index"] * CURRENT_WEIGHTS["has_index"]
        )
        struct_scores.append(score)
        actual_yields.append(y[i])

    r_struct = pearson_r(struct_scores, actual_yields)
    print(f"  Structural score → L/lane correlation: r={r_struct:+.3f}")
    print(f"  Interpretation: structural score explains ~{r_struct**2*100:.1f}% of yield variance")

    # Compute derived score correlation
    if beta is not None:
        derived_scores = []
        for i, dom in enumerate(domain_labels):
            s = sum(X[i][j] * beta[j] for j in range(len(feature_names)))
            derived_scores.append(s)
        r_derived = pearson_r(derived_scores, actual_yields)
        print(f"  Derived score → L/lane correlation: r={r_derived:+.3f}")
        print(f"  Derived explains ~{r_derived**2*100:.1f}% of yield variance")
        improvement = (r_derived ** 2 - r_struct ** 2) * 100
        print(f"  Improvement: {improvement:+.1f}pp variance explained")

    # 8. UCB1 exploit vs structural: which predicts yield better?
    print(f"\n--- UCB1 Exploit vs Structural as Yield Predictor ---")
    ucb1_exploits = []
    for dom in domain_labels:
        oc = domain_outcomes[dom]
        n = oc["lanes"]
        mr = oc["merged"] / n if n > 0 else 0
        quality = mr * (1 + math.log1p(oc["lessons"]))
        ucb1_exploits.append(quality)

    r_ucb1 = pearson_r(ucb1_exploits, actual_yields)
    print(f"  UCB1 exploit → L/lane: r={r_ucb1:+.3f} ({r_ucb1**2*100:.1f}% variance)")
    print(f"  Structural → L/lane:   r={r_struct:+.3f} ({r_struct**2*100:.1f}% variance)")
    winner = "UCB1" if abs(r_ucb1) > abs(r_struct) else "STRUCTURAL"
    print(f"  Winner: {winner}")

    # 9. Weight stability test: split data in half (first/second half of sessions)
    # If derived weights are stable across halves, they're reliable
    print(f"\n--- Weight Stability (temporal split) ---")
    all_sessions = sorted(set(l["session"] for l in lanes if l["session"]))
    if len(all_sessions) >= 10:
        mid = all_sessions[len(all_sessions) // 2]
        early_outcomes = defaultdict(lambda: {"lanes": 0, "merged": 0, "lessons": 0})
        late_outcomes = defaultdict(lambda: {"lanes": 0, "merged": 0, "lessons": 0})
        for lane in lanes:
            target = early_outcomes if lane["session"] and lane["session"] <= mid else late_outcomes
            d = target[lane["domain"]]
            d["lanes"] += 1
            if lane["merged"]:
                d["merged"] += 1
            d["lessons"] += lane["lessons_produced"]

        # Build separate regression datasets
        for era_name, era_outcomes in [("early (≤S%d)" % mid, early_outcomes),
                                        ("late (>S%d)" % mid, late_outcomes)]:
            X_era, y_era = [], []
            for dom in domain_labels:
                if dom not in era_outcomes or era_outcomes[dom]["lanes"] < 2:
                    continue
                feat = features[dom]
                row = [feat[f] for f in feature_names]
                X_era.append(row)
                y_era.append(era_outcomes[dom]["lessons"] / era_outcomes[dom]["lanes"])

            if len(X_era) >= 5:
                beta_era, r_sq_era, _ = ridge_regression(X_era, y_era, alpha=1.0)
                if beta_era:
                    print(f"  {era_name}: R²={r_sq_era:.3f}, n={len(X_era)}")
                    for j, fn in enumerate(feature_names):
                        full = derived_weights.get(fn, 0)
                        era_w = beta_era[j]
                        drift = abs(era_w - full) / (abs(full) + 0.001)
                        stable = "STABLE" if drift < 0.5 else "DRIFTED"
                        print(f"    {fn:15s}: {era_w:+.3f} (full: {full:+.4f}) [{stable}]")
                else:
                    print(f"  {era_name}: OLS failed (n={len(X_era)})")
            else:
                print(f"  {era_name}: insufficient data (n={len(X_era)})")

    # 10. Build calibration artifact
    artifact = {
        "experiment": "f-exp10-self-calibration",
        "frontier": "F-EXP10",
        "domain": "expert-swarm",
        "session": "S391",
        "date": "2026-03-01",
        "directive": "SIG-32: Expert assessment must be swarmed — weights empirically derived",
        "hypothesis": [
            "H1: ISO weight 1.5 is over-indexed (optimal <1.0)",
            "H2: Structural score explains <30% of actual yield variance",
            "H3: At least 3 constants are empirically unjustified",
        ],
        "method": "OLS regression of structural features → L/lane yield across all DOMEX lanes. Pure Python, no external deps.",
        "n_lanes": len(lanes),
        "n_domains_in_regression": len(X),
        "domains": domain_labels,
        "current_weights": CURRENT_WEIGHTS,
        "derived_weights": derived_weights,
        "feature_yield_correlations": correlations,
        "structural_score_correlation": round(r_struct, 4),
        "structural_variance_explained_pct": round(r_struct ** 2 * 100, 1),
        "ucb1_exploit_correlation": round(r_ucb1, 4) if 'r_ucb1' in dir() else None,
        "regression_r_squared": round(r_sq, 4) if beta else None,
        "mismatched_weights": mismatches,
        "verdicts": {
            "h1_iso_overindexed": None,
            "h2_structural_lt_30pct": None,
            "h3_unjustified_constants_gte_3": None,
        },
        "prescriptions": [],
        "cites": ["L-654", "L-749", "L-671", "L-750", "L-501", "SIG-32"],
        "confidence": f"Measured (n={len(lanes)} lanes, {len(X)} domains in regression)",
    }

    # Fill verdicts
    if correlations:
        iso_r = correlations.get("iso", 0)
        artifact["verdicts"]["h1_iso_overindexed"] = (
            f"{'CONFIRMED' if iso_r < 0.2 else 'FALSIFIED'}: "
            f"ISO→yield r={iso_r:+.3f}, derived weight={derived_weights.get('iso', '?')}"
        )
    if r_struct is not None:
        var_pct = r_struct ** 2 * 100
        artifact["verdicts"]["h2_structural_lt_30pct"] = (
            f"{'CONFIRMED' if var_pct < 30 else 'FALSIFIED'}: "
            f"structural score explains {var_pct:.1f}% of yield variance"
        )
    artifact["verdicts"]["h3_unjustified_constants_gte_3"] = (
        f"{'CONFIRMED' if len(mismatches) >= 3 else 'FALSIFIED'}: "
        f"{len(mismatches)} mismatched weights: {mismatches}"
    )

    # Overall verdict
    confirmed = sum(1 for v in artifact["verdicts"].values() if v and "CONFIRMED" in str(v))
    total = len(artifact["verdicts"])
    if confirmed >= 2:
        artifact["overall_verdict"] = "CONFIRMED"
    elif confirmed >= 1:
        artifact["overall_verdict"] = "PARTIALLY_CONFIRMED"
    else:
        artifact["overall_verdict"] = "FALSIFIED"

    # Prescriptions
    artifact["prescriptions"] = [
        "Replace hardcoded CURRENT_WEIGHTS with calibration loader reading from JSON artifact",
        "Add --recalibrate flag to dispatch_optimizer.py that re-runs this derivation",
        "Wire calibration.json into dispatch scoring (fallback to CURRENT_WEIGHTS if missing)",
        f"Top priority weight corrections: {mismatches[:3]}",
    ]

    # Save
    out_path = ROOT / "experiments" / "expert-swarm" / "f-exp10-self-calibration-s391.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2, default=str)
    print(f"\nArtifact: {out_path.relative_to(ROOT)}")

    # Also save calibration file for dispatch_optimizer.py to consume
    if derived_weights:
        cal_path = ROOT / "tools" / "dispatch_calibration.json"
        cal_data = {
            "calibrated_session": "S391",
            "calibrated_from_n_lanes": len(lanes),
            "calibrated_from_n_domains": len(X),
            "regression_r_squared": round(r_sq, 4) if beta else None,
            "weights": derived_weights,
            "fallback_weights": CURRENT_WEIGHTS,
            "correlations": correlations,
        }
        with open(cal_path, "w") as f:
            json.dump(cal_data, f, indent=2)
        print(f"Calibration: {cal_path.relative_to(ROOT)}")

    return artifact


if __name__ == "__main__":
    main()
