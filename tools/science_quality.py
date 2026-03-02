#!/usr/bin/env python3
"""science_quality.py — P-243: Score experiment quality for the swarm.

Scans experiment JSON artifacts and scores each on 5 science-quality criteria:
1. Pre-registered hypothesis (expect field present + quantitative)
2. Control/baseline (before/after, train/test, or explicit comparison)
3. Significance testing (p-value, BIC, CI, effect size reported)
4. External validation (tests against non-swarm data or independent system)
5. Falsification design (explicit conditions under which hypothesis fails)

Also reports:
- Confirm/discover ratio across recent sessions
- Falsification lane count (mode=falsification in SWARM-LANES.md)
- % of experiments with vague thresholds

Usage:
    python3 tools/science_quality.py                  # full report
    python3 tools/science_quality.py --recent 20      # last 20 sessions only
    python3 tools/science_quality.py --json            # machine-readable output
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
LANES_FILE = REPO_ROOT / "tasks" / "SWARM-LANES.md"
LANES_ARCHIVE = REPO_ROOT / "tasks" / "SWARM-LANES-ARCHIVE.md"
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"


def extract_session_number(filename: str) -> int:
    """Extract session number from filename like f-str1-hardening-s393.json."""
    m = re.search(r"[sS](\d+)", filename)
    return int(m.group(1)) if m else 0


def score_experiment(data: dict) -> dict:
    """Score a single experiment artifact on P-243 criteria."""
    scores = {}
    text = json.dumps(data, default=str).lower()

    # 1. Pre-registered hypothesis (quantitative expect)
    expect = str(data.get("expect", data.get("hypothesis", "")))
    has_number = bool(re.search(r"\d", expect))
    has_threshold = any(kw in expect.lower() for kw in (
        ">", "<", ">=", "<=", "~", "within", "threshold", "%", "bic", "r=", "rho",
        "p<", "n=", "n>=", "δ", "delta",
    ))
    scores["pre_registration"] = 1.0 if (has_number and has_threshold) else (0.5 if has_number else 0.0)

    # 2. Control/baseline
    control_keywords = ("baseline", "control", "before", "train/test", "train_", "test_",
                        "comparison", "counterfactual", "pre-", "post-", "treatment",
                        "split", "holdout", "oos", "out-of-sample")
    scores["control"] = 1.0 if any(kw in text for kw in control_keywords) else 0.0

    # 3. Significance testing
    stat_keywords = ("p-value", "p<", "p =", "bic", "aic", "confidence interval",
                     "effect size", "cohen", "t-test", "chi-square", "anova",
                     "regression", "r²", "r-squared", "significance", "z-score",
                     "log-likelihood", "permutation test", "bootstrap")
    stat_count = sum(1 for kw in stat_keywords if kw in text)
    scores["significance"] = min(1.0, stat_count / 2.0)  # need at least 2 indicators

    # 4. External validation
    external_keywords = ("external", "independent", "non-swarm", "wikipedia", "arxiv",
                         "other repo", "outside", "cross-system", "real-world",
                         "ground truth", "benchmark")
    scores["external_validation"] = 1.0 if any(kw in text for kw in external_keywords) else 0.0

    # 5. Falsification design
    falsify_keywords = ("falsified if", "falsification", "reject if", "would fail if",
                        "contradicted if", "null hypothesis", "h0", "disprove",
                        "conditions for failure", "drop if", "wrong if")
    scores["falsification"] = 1.0 if any(kw in text for kw in falsify_keywords) else 0.0

    # Falsification outcome bonus (L-900: actual falsifications get 2.4x citation attractor —
    # reward experiments that produced a genuine null/falsified/overturned outcome beyond just
    # having a falsification condition planned in the design)
    outcome_text = str(data.get("actual", data.get("verdict", ""))).lower()
    outcome_mode = str(data.get("mode", "")).lower()
    is_falsified_outcome = any(kw in outcome_text for kw in (
        " falsified", "null result", "overturned", "rejected", "null:", "falsified:",
        "falsified —", "no effect", "zero effect",
    ))
    is_falsification_mode = outcome_mode == "falsification"
    scores["falsification_outcome"] = 1.0 if (is_falsified_outcome or is_falsification_mode) else 0.0

    base = sum(scores[k] for k in ("pre_registration", "control", "significance",
                                   "external_validation", "falsification")) / 5.0
    scores["total"] = min(1.0, base + scores["falsification_outcome"] * 0.10)
    return scores


def count_confirmation_ratio() -> tuple[int, int]:
    """Count CONFIRMED vs FALSIFIED/OVERTURNED/NULL lane outcomes — measures discovery rate.

    Uses SWARM-LANES.md status column outcomes, not keyword counting. This correctly
    measures whether lanes produce confirmations or surprises (L-807 methodology fix).
    """
    confirmed = 0
    discovered = 0  # falsified + null + overturned outcomes
    for lanes_file in (LANES_FILE, LANES_ARCHIVE):
        if not lanes_file.exists():
            continue
        for line in lanes_file.read_text().splitlines():
            if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue
            etc = cols[10] if len(cols) > 10 else ""
            note = cols[11] if len(cols) > 11 else ""
            combined = (etc + " " + note).lower()
            if "confirmed" in combined and "falsified" not in combined and "null" not in combined:
                confirmed += 1
            elif any(kw in combined for kw in ("falsified", "null result", "overturned",
                                                "unexpected", "inverted", "wrong", "failed")):
                discovered += 1
    return confirmed, max(1, discovered)


def count_falsification_lanes(recent_sessions: int = 20) -> tuple[int, int]:
    """Count falsification-mode lanes in recent sessions."""
    falsification = 0
    total = 0
    for lanes_file in (LANES_FILE, LANES_ARCHIVE):
        if not lanes_file.exists():
            continue
        for line in lanes_file.read_text().splitlines():
            if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue
            total += 1
            etc = cols[10] if len(cols) > 10 else ""
            if "mode=falsification" in etc:
                falsification += 1
    return falsification, total


def main():
    parser = argparse.ArgumentParser(description="P-243: Score swarm experiment quality")
    parser.add_argument("--recent", type=int, default=0, help="Only score experiments from last N sessions")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not EXPERIMENTS_DIR.exists():
        print("ERROR: experiments/ directory not found", file=sys.stderr)
        sys.exit(1)

    # Score all experiment JSON files
    results = []
    for json_file in sorted(EXPERIMENTS_DIR.rglob("*.json")):
        session = extract_session_number(json_file.name)
        if args.recent and session < max(1, 396 - args.recent):
            continue
        try:
            data = json.loads(json_file.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        scores = score_experiment(data)
        results.append({
            "file": str(json_file.relative_to(REPO_ROOT)),
            "session": session,
            "scores": scores,
        })

    if not results:
        print("No experiment artifacts found.")
        return

    # Aggregate statistics
    totals = [r["scores"]["total"] for r in results]
    criteria_means = {}
    for criterion in ("pre_registration", "control", "significance", "external_validation",
                      "falsification", "falsification_outcome"):
        vals = [r["scores"][criterion] for r in results]
        criteria_means[criterion] = sum(vals) / len(vals) if vals else 0

    confirmed, discovered = count_confirmation_ratio()
    falsif_lanes, total_lanes = count_falsification_lanes()

    n_falsif_outcome = sum(1 for r in results if r["scores"]["falsification_outcome"] > 0)
    report = {
        "n_experiments": len(results),
        "mean_quality": sum(totals) / len(totals),
        "median_quality": sorted(totals)[len(totals) // 2],
        "criteria_means": criteria_means,
        "confirm_discover_ratio": f"{confirmed}:{discovered}",
        "falsification_lanes": f"{falsif_lanes}/{total_lanes}",
        "falsification_outcome_rate": round(n_falsif_outcome / len(results), 3) if results else 0,
        "falsification_outcome_count": n_falsif_outcome,
        "bottom_5": sorted(results, key=lambda r: r["scores"]["total"])[:5],
        "top_5": sorted(results, key=lambda r: r["scores"]["total"], reverse=True)[:5],
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== SCIENCE QUALITY REPORT (P-243) ===")
        print(f"Experiments scored: {len(results)}")
        print(f"Mean quality:  {report['mean_quality']:.1%}")
        print(f"Median quality: {report['median_quality']:.1%}")
        print()
        print("--- Criteria breakdown ---")
        for criterion, mean in criteria_means.items():
            bar = "█" * int(mean * 20) + "░" * (20 - int(mean * 20))
            status = "PASS" if mean >= 0.5 else "FAIL"
            print(f"  {criterion:<25} {bar} {mean:.0%} [{status}]")
        print()
        print(f"Confirm/discover ratio:    {confirmed}:{discovered} ({confirmed/discovered:.0f}:1)")
        print(f"Falsification lanes:       {falsif_lanes}/{total_lanes} (target: 1-in-5 = 20%)")
        print(f"Falsified outcomes (bonus): {n_falsif_outcome}/{len(results)} (L-900: +10% quality bonus)")
        print()
        print("--- Top 5 (best science) ---")
        for r in report["top_5"]:
            print(f"  {r['scores']['total']:.0%}  {r['file']}")
        print()
        print("--- Bottom 5 (weakest science) ---")
        for r in report["bottom_5"]:
            print(f"  {r['scores']['total']:.0%}  {r['file']}")


if __name__ == "__main__":
    main()
