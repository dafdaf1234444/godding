#!/usr/bin/env python3
"""F-IS7 experiment→lesson conversion classifier.

Analyzes what discriminates the ~15% of experiments that get cited
by lessons from the ~85% that don't.

Session: S370 | Frontier: F-IS7 | Domain: information-science
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
EXPERIMENTS_DIR = REPO / "experiments"
LESSONS_DIR = REPO / "memory" / "lessons"


def load_all_experiments():
    """Load all experiment JSONs with metadata."""
    experiments = []
    for root, _, files in os.walk(EXPERIMENTS_DIR):
        for f in files:
            if not f.endswith(".json"):
                continue
            path = Path(root) / f
            # Skip non-experiment files
            rel = path.relative_to(EXPERIMENTS_DIR)
            parts = rel.parts
            if len(parts) < 2:
                continue  # top-level files like compact-citation-cache.json
            domain = parts[0]
            try:
                with open(path) as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(data, dict):
                continue

            experiments.append({
                "path": str(path.relative_to(REPO)),
                "domain": domain,
                "filename": f,
                "data": data,
            })
    return experiments


def load_lesson_citations():
    """Find which experiment files are cited in lessons (forward linkage)."""
    cited_experiments = set()
    lesson_texts = {}
    for lf in sorted(LESSONS_DIR.glob("L-*.md")):
        try:
            text = lf.read_text(encoding="utf-8")
        except Exception:
            continue
        lesson_texts[lf.name] = text
        # Look for experiment file paths
        # Patterns: experiments/domain/file.json, f-xxx-s123.json
        for m in re.finditer(r'experiments/[\w\-]+/[\w\-]+\.json', text):
            cited_experiments.add(m.group(0))
        # Also look for artifact references
        for m in re.finditer(r'artifact[=:]\s*`?(experiments/[\w\-/]+\.json)', text):
            cited_experiments.add(m.group(1))
    return cited_experiments, lesson_texts


def extract_features(exp):
    """Extract discriminative features from an experiment."""
    data = exp["data"]
    path = exp["path"]
    keys = set(data.keys()) if isinstance(data, dict) else set()
    text = json.dumps(data)

    # Session number
    session = None
    s_match = re.search(r'[Ss](\d+)', exp["filename"])
    if s_match:
        session = int(s_match.group(1))
    if not session and isinstance(data.get("session"), (int, str)):
        s_val = str(data.get("session", ""))
        s_m = re.search(r'(\d+)', s_val)
        if s_m:
            session = int(s_m.group(1))

    # File size (proxy for effort/detail)
    file_size = len(text)

    # Structural completeness: EAD fields present
    has_expect = "expect" in keys or "hypothesis" in keys
    has_actual = "actual" in keys or "result" in keys or "results" in keys
    has_diff = "diff" in keys or "delta" in keys
    has_verdict = "verdict" in keys or "conclusion" in keys or "finding" in keys
    has_measurements = "measurements" in keys or "data" in keys
    has_next_steps = "next_steps" in keys or "next" in keys
    ead_score = sum([has_expect, has_actual, has_diff])

    # Backward linkage: does this experiment cite lessons?
    l_refs = set(re.findall(r'\bL-(\d+)\b', text))
    cites_lessons = len(l_refs) > 0
    n_lesson_refs = len(l_refs)

    # Frontier linkage
    f_refs = set(re.findall(r'\bF-[A-Z]+\d+\b', text))
    has_frontier = len(f_refs) > 0

    # Outcome clarity: does it have a clear positive/negative/mixed verdict?
    verdict_text = str(data.get("verdict", data.get("conclusion", data.get("finding", ""))))
    outcome_clear = bool(re.search(
        r'CONFIRMED|FALSIFIED|PARTIAL|RESOLVED|REFUTED|MIXED|PROVEN|NULL',
        verdict_text, re.IGNORECASE
    ))

    # Number of top-level keys (complexity proxy)
    n_keys = len(keys)

    # Has candidate lesson ID?
    has_candidate_lesson = "candidate_lesson_id" in keys or "lesson_id" in keys

    # Domain-level DOMEX indicator
    is_domex = bool(re.search(r'DOMEX|domex', text))

    return {
        "domain": exp["domain"],
        "session": session,
        "file_size": file_size,
        "n_keys": n_keys,
        "has_expect": has_expect,
        "has_actual": has_actual,
        "has_diff": has_diff,
        "has_verdict": has_verdict,
        "has_measurements": has_measurements,
        "has_next_steps": has_next_steps,
        "ead_score": ead_score,
        "cites_lessons": cites_lessons,
        "n_lesson_refs": n_lesson_refs,
        "has_frontier": has_frontier,
        "n_frontier_refs": len(f_refs),
        "outcome_clear": outcome_clear,
        "has_candidate_lesson": has_candidate_lesson,
        "is_domex": is_domex,
    }


def analyze_conversion(experiments, cited_set):
    """Analyze what predicts conversion."""
    features_list = []
    labels = []

    for exp in experiments:
        feats = extract_features(exp)
        is_cited = exp["path"] in cited_set
        feats["cited"] = is_cited
        features_list.append(feats)
        labels.append(is_cited)

    n_total = len(features_list)
    n_cited = sum(labels)
    base_rate = n_cited / n_total if n_total else 0

    print(f"\n=== EXPERIMENT→LESSON CONVERSION ANALYSIS ===")
    print(f"Total experiments: {n_total}")
    print(f"Cited by lessons: {n_cited} ({base_rate:.1%})")
    print(f"Uncited:          {n_total - n_cited} ({1 - base_rate:.1%})")

    # Feature-level analysis: for each boolean feature, compute conversion rate
    bool_features = [
        "has_expect", "has_actual", "has_diff", "has_verdict",
        "has_measurements", "has_next_steps", "cites_lessons",
        "has_frontier", "outcome_clear", "has_candidate_lesson", "is_domex",
    ]

    print(f"\n--- Feature Conversion Rates (base rate: {base_rate:.1%}) ---")
    print(f"{'Feature':<25} {'With':<10} {'Rate':<10} {'Without':<10} {'Rate':<10} {'Lift':<8}")
    print("-" * 73)

    feature_lifts = {}
    for feat in bool_features:
        with_feat = [f for f in features_list if f[feat]]
        without_feat = [f for f in features_list if not f[feat]]
        rate_with = sum(1 for f in with_feat if f["cited"]) / len(with_feat) if with_feat else 0
        rate_without = sum(1 for f in without_feat if f["cited"]) / len(without_feat) if without_feat else 0
        lift = rate_with / base_rate if base_rate > 0 else 0
        feature_lifts[feat] = lift
        print(f"{feat:<25} {len(with_feat):<10} {rate_with:<10.1%} {len(without_feat):<10} {rate_without:<10.1%} {lift:<8.2f}x")

    # EAD score analysis
    print(f"\n--- EAD Completeness (expect+actual+diff) ---")
    for score in range(4):
        subset = [f for f in features_list if f["ead_score"] == score]
        if not subset:
            continue
        rate = sum(1 for f in subset if f["cited"]) / len(subset)
        print(f"  EAD={score}: {len(subset):>4} experiments, {rate:.1%} conversion ({rate/base_rate:.2f}x lift)")

    # Domain analysis
    print(f"\n--- Domain Conversion Rates ---")
    domain_stats = defaultdict(lambda: {"total": 0, "cited": 0})
    for f in features_list:
        domain_stats[f["domain"]]["total"] += 1
        if f["cited"]:
            domain_stats[f["domain"]]["cited"] += 1

    domain_sorted = sorted(domain_stats.items(), key=lambda x: x[1]["cited"]/max(x[1]["total"],1), reverse=True)
    print(f"{'Domain':<30} {'Total':<8} {'Cited':<8} {'Rate':<10} {'Lift':<8}")
    print("-" * 64)
    for domain, stats in domain_sorted[:20]:
        rate = stats["cited"] / stats["total"] if stats["total"] else 0
        lift = rate / base_rate if base_rate > 0 else 0
        print(f"{domain:<30} {stats['total']:<8} {stats['cited']:<8} {rate:<10.1%} {lift:<8.2f}x")

    # Session era analysis
    print(f"\n--- Session Era Analysis ---")
    era_bins = [(0, 186, "S0-S186 (early)"), (187, 300, "S187-S300 (growth)"),
                (301, 350, "S301-S350 (maturity)"), (351, 999, "S351+ (recent)")]
    for lo, hi, label in era_bins:
        subset = [f for f in features_list if f["session"] and lo <= f["session"] <= hi]
        if not subset:
            continue
        rate = sum(1 for f in subset if f["cited"]) / len(subset)
        print(f"  {label:<25}: {len(subset):>4} experiments, {rate:.1%} conversion")

    # File size quartile analysis
    print(f"\n--- File Size Quartiles ---")
    sizes = sorted([f["file_size"] for f in features_list])
    quartiles = [sizes[len(sizes)*i//4] for i in range(4)] + [sizes[-1]]
    for i in range(4):
        lo, hi = quartiles[i], quartiles[i+1]
        subset = [f for f in features_list if lo <= f["file_size"] <= hi]
        if not subset:
            continue
        rate = sum(1 for f in subset if f["cited"]) / len(subset)
        label = f"Q{i+1} ({lo:,}-{hi:,} chars)"
        print(f"  {label:<30}: {len(subset):>4} experiments, {rate:.1%} conversion")

    # Simple decision-tree classifier: top features by information gain
    # Use the feature with highest lift as split point
    top_features = sorted(feature_lifts.items(), key=lambda x: abs(x[1] - 1.0), reverse=True)
    print(f"\n--- Feature Importance (by lift distance from base rate) ---")
    for feat, lift in top_features:
        print(f"  {feat:<25}: {lift:.2f}x lift  (importance: {abs(lift - 1.0):.2f})")

    # Simple rule-based classifier: combine top features
    print(f"\n--- Rule-Based Classifier ---")
    # Rule: cited if (has_candidate_lesson OR (ead_score >= 2 AND cites_lessons))
    tp = fp = tn = fn = 0
    for f in features_list:
        predicted = (
            f["has_candidate_lesson"] or
            (f["ead_score"] >= 2 and f["cites_lessons"]) or
            (f["is_domex"] and f["has_verdict"])
        )
        actual = f["cited"]
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and actual:
            fn += 1
        else:
            tn += 1

    accuracy = (tp + tn) / n_total if n_total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    print(f"  Rule: candidate_lesson_id OR (EAD>=2 AND cites_lessons) OR (DOMEX AND verdict)")
    print(f"  Accuracy:  {accuracy:.1%} (baseline: {max(base_rate, 1-base_rate):.1%})")
    print(f"  Precision: {precision:.1%}")
    print(f"  Recall:    {recall:.1%}")
    print(f"  F1:        {f1:.3f}")
    print(f"  TP={tp} FP={fp} FN={fn} TN={tn}")

    # Alternative: stricter rule
    tp2 = fp2 = tn2 = fn2 = 0
    for f in features_list:
        predicted2 = (f["ead_score"] >= 2 and f["n_lesson_refs"] >= 1)
        actual = f["cited"]
        if predicted2 and actual:
            tp2 += 1
        elif predicted2 and not actual:
            fp2 += 1
        elif not predicted2 and actual:
            fn2 += 1
        else:
            tn2 += 1

    acc2 = (tp2 + tn2) / n_total if n_total else 0
    prec2 = tp2 / (tp2 + fp2) if (tp2 + fp2) else 0
    rec2 = tp2 / (tp2 + fn2) if (tp2 + fn2) else 0
    f12 = 2 * prec2 * rec2 / (prec2 + rec2) if (prec2 + rec2) else 0

    print(f"\n  Alt rule: EAD>=2 AND n_lesson_refs>=1")
    print(f"  Accuracy:  {acc2:.1%}  Precision: {prec2:.1%}  Recall: {rec2:.1%}  F1: {f12:.3f}")

    return {
        "n_total": n_total,
        "n_cited": n_cited,
        "base_rate": round(base_rate, 4),
        "feature_lifts": {k: round(v, 3) for k, v in feature_lifts.items()},
        "top_features": [(k, round(v, 3)) for k, v in top_features[:5]],
        "classifier": {
            "rule": "candidate_lesson_id OR (EAD>=2 AND cites_lessons) OR (DOMEX AND verdict)",
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        },
        "alt_classifier": {
            "rule": "EAD>=2 AND n_lesson_refs>=1",
            "accuracy": round(acc2, 4),
            "precision": round(prec2, 4),
            "recall": round(rec2, 4),
            "f1": round(f12, 4),
        },
        "domain_rates": {d: {"total": s["total"], "cited": s["cited"],
                             "rate": round(s["cited"]/max(s["total"],1), 3)}
                        for d, s in domain_sorted[:20]},
        "ead_rates": {},
        "era_rates": {},
    }


def main():
    experiments = load_all_experiments()
    print(f"Loaded {len(experiments)} experiment files")

    cited_set, _ = load_lesson_citations()
    print(f"Found {len(cited_set)} unique experiment paths cited in lessons")

    results = analyze_conversion(experiments, cited_set)

    # Fill in EAD and era rates
    features_list = []
    for exp in experiments:
        feats = extract_features(exp)
        feats["cited"] = exp["path"] in cited_set
        features_list.append(feats)

    for score in range(4):
        subset = [f for f in features_list if f["ead_score"] == score]
        if subset:
            rate = sum(1 for f in subset if f["cited"]) / len(subset)
            results["ead_rates"][str(score)] = {"n": len(subset), "rate": round(rate, 3)}

    era_bins = [(0, 186), (187, 300), (301, 350), (351, 999)]
    for lo, hi in era_bins:
        subset = [f for f in features_list if f["session"] and lo <= f["session"] <= hi]
        if subset:
            rate = sum(1 for f in subset if f["cited"]) / len(subset)
            results["era_rates"][f"S{lo}-S{hi}"] = {"n": len(subset), "rate": round(rate, 3)}

    # Save results
    output = {
        "frontier_id": "F-IS7",
        "session": 370,
        "created_on": "2026-03-01",
        "experiment": "Experiment-to-lesson conversion classifier",
        "hypothesis": "Structural features (EAD completeness, backward lesson refs, domain, DOMEX provenance) predict whether an experiment gets cited by a lesson. Target: >70% classification accuracy.",
        "method": f"Scanned {results['n_total']} experiment JSONs across all domains. Extracted 11 boolean features + 4 continuous features. Computed conversion rates per feature, domain, session era, file size. Built rule-based classifier.",
        "results": results,
        "expect": "Experiment features predict conversion with >70% accuracy. Top predictor identified.",
        "actual": f"Accuracy {results['classifier']['accuracy']:.1%}, F1={results['classifier']['f1']:.3f}. Top predictor: {results['top_features'][0][0]} ({results['top_features'][0][1]}x lift).",
        "diff": "",
        "verdict": "",
    }

    out_path = EXPERIMENTS_DIR / "information-science" / "f-is7-conversion-classifier-s370.json"
    with open(out_path, "w") as fh:
        json.dump(output, fh, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
