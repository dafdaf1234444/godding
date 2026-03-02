#!/usr/bin/env python3
"""
Task Recognizer Accuracy Benchmark

Extracts real task descriptions from NEXT.md/NEXT-ARCHIVE.md session notes,
runs them through task_recognizer.recognize(), and compares predicted domain
to actual domain worked.

Metrics:
- Top-1 accuracy (predicted == actual)
- Top-3 accuracy (actual in top 3 predictions)
- Confusion matrix: which domains get misrouted most
- Mean confidence for correct vs incorrect predictions
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
from task_recognizer import recognize, build_domain_index

# ---- Ground truth dataset ----
# Each entry: (task_description, actual_domain)
# Extracted from NEXT.md and NEXT-ARCHIVE.md session notes.
# task_description = what the session actually did (from session note title/body)
# actual_domain = the lane/dispatch domain recorded in the session note

GROUND_TRUTH = [
    # S358 sessions
    (
        "coordination and concurrent harvest, DUE items cleared, economy health check, proxy-K measurement",
        "meta",
    ),
    (
        "challenge resolution, CORE-P11 DROPPED, EAD contrast generator analysis, n=365 archived entries",
        "meta",
    ),
    (
        "F-META9 opened, autonomous invocation gap, P-219 substrate-tripwire at frontier-opening",
        "meta",
    ),
    (
        "USL concurrency model fit, alpha beta estimates, N* prediction, Universal Scalability Law R-squared",
        "stochastic-processes",
    ),
    (
        "F-SP2 RESOLVED constant throughput model wins AIC, 4-model comparison, USL vs linear vs sqrt",
        "stochastic-processes",
    ),
    (
        "F-EMP1 handoff accuracy measurement, prediction hit rate across 20+ sessions, bimodal distribution",
        "empathy",
    ),
    (
        "F-IS7 statistics harvest, 21 experiments scanned, 6 patterns found, domain conversion 0% to 9.5%",
        "information-science",
    ),
    (
        "multi-lesson quality fixer, orphan citations fixed, Cites headers enriched, 177 orphan lessons",
        "meta",
    ),
    (
        "economy DOMEX F-ECO5 coverage-weighted dispatch scoring, visit saturation penalty, exploration mode, Gini reduction",
        "economy",
    ),
    (
        "PHIL-2 challenge REFINED, human-mediated recursion, stochastic-processes domain confirmed, Hawkes r=0.684",
        "meta",
    ),
    # S357 sessions
    (
        "NK K=2.0 CROSSED, K_avg measurement at N=554, hub z-score, Gini z-score, isolation z-score",
        "nk-complexity",
    ),
    (
        "redundancy audit, principles-dedup, lesson dedup, near-duplicate pairs superseded",
        "meta",
    ),
    (
        "NK falsification, chaos predictions 3/3 FALSIFIED, cycle tracking, Gini declining monotonically",
        "nk-complexity",
    ),
    (
        "epistemic repair, N_e and phase transition terminology correction, 6 lessons corrected, INDEX.md theme fixed",
        "meta",
    ),
    # S356 sessions
    (
        "hallucination challenge filing, 3 belief challenges from L-599 audit, N_e and phase transitions and PHIL-2",
        "meta",
    ),
    (
        "NK S356 tracking, K_avg checkpoint, cross-session Hawkes/NK synthesis, cross-scale integration",
        "nk-complexity",
    ),
    (
        "F-SP1 CONFIRMED Hawkes self-excitation, IoD=3.54, ΔAIC=186, lag-1 autocorrelation, r=0.684",
        "stochastic-processes",
    ),
    (
        "setup-reswarm, orient.py stale lane detection fix, bridge sync, INDEX.md bucket overflow, NK falsification design",
        "meta",
    ),
    (
        "paper-reswarm, docs/PAPER.md v0.18 to v0.19, S332-S355 narrative update, living paper maintenance",
        "meta",
    ),
    (
        "conflict DOMEX F-CON2 C-EDIT measurement, 82% reduction CONFIRMED, claim.py collision prevention",
        "conflict",
    ),
    (
        "hallucination audit, belief challenges filed, epistemic repair, substrate verification P-217",
        "meta",
    ),
    # S355 sessions
    (
        "meta pattern mining F-META8, session-boundary compliance theorem, 167+ meta lessons scanned",
        "meta",
    ),
    (
        "claim.py TTL 300s to 120s, ghost lock reduction, F-CON2 follow-up",
        "conflict",
    ),
    (
        "NK plateau BROKEN, K_avg 1.79 to 1.96, K=2.0 approaching, harvest session citation rate",
        "nk-complexity",
    ),
    (
        "orient.py performance fix, 60s to 17s, 4 root causes profiled, F-CON2 claim integration",
        "conflict",
    ),
    (
        "deep history harvest, 47 experiments analyzed, grounding floor theorem, chronology sawtooth",
        "information-science",
    ),
    (
        "contract_check.py built, F-META8 self-verifying contract, 5 binary validators, 7/7 tests pass",
        "meta",
    ),
    # S354 sessions
    (
        "F119 reswarm, I13 MC-XSUB enforcement gap, ops-research harvest, 54 experiments to 2 lessons",
        "operations-research",
    ),
    (
        "multi-tool bridge audit, 4 untested tools researched, .cursorrules deprecated, bridge files updated",
        "meta",
    ),
    (
        "governance DOMEX drift_scanner.py built, F-GOV2 RESOLVED, requirement gaps between canonical and derivative files",
        "governance",
    ),
    # S353 sessions
    (
        "F-META7 integration session, dark matter 30% to 18.5%, dream.py batch theming, optimal orphan rate",
        "meta",
    ),
    (
        "NK DOMEX plus brain DOMEX F-BRN4, INDEX coverage 76.4% to 83.4%, new theme Phase Science",
        "nk-complexity",
    ),
    (
        "stochastic-processes dark matter PID policy, N_e approximately 15, optimal orphan rate 15-25%",
        "stochastic-processes",
    ),
    (
        "human-signal-harvest P-216 three-signal rule, 3 patterns promoted, mechanism-naming",
        "meta",
    ),
    (
        "info-science DOMEX F-IS7 volume-conversion paradox harvested, Simpson's Paradox, regime splitting",
        "information-science",
    ),
    (
        "Hono S3 F1 resolved, RegExpRouter vs TrieRouter benchmark, ISO-23 regime-crossover",
        "helper-swarm",
    ),
    (
        "council swarming the swarm's code, 3 GAP-1 closures, swarm_io lane parsing, code improvements",
        "meta",
    ),
    (
        "dark matter fixed, dream.py Domain format gap, 77% to 30%, measurement-channel bug",
        "meta",
    ),
    (
        "F-META1 minimal contract, ISO-24 ergodic decomposition, stochastic-processes genesis harvest",
        "meta",
    ),
    (
        "mission-constraint-reswarm, MC-LEARN test fix, F119 hardened, MC-SAFE MC-CONN MC-XSUB healthy",
        "meta",
    ),
]


def run_benchmark():
    """Run all ground truth tasks through recognizer and compute metrics."""
    domain_index = build_domain_index()

    results = []
    top1_correct = 0
    top3_correct = 0
    confidence_correct = []
    confidence_incorrect = []

    # Confusion: actual -> predicted -> count
    confusion = defaultdict(lambda: defaultdict(int))
    # Per-domain stats
    domain_stats = defaultdict(lambda: {"total": 0, "top1": 0, "top3": 0})

    for task_desc, actual_domain in GROUND_TRUTH:
        result = recognize(task_desc, domain_index)

        predicted_domains = [r["domain"] for r in result["routes"]]
        predicted_top1 = predicted_domains[0] if predicted_domains else "NONE"
        confidence = result["confidence"]

        is_top1 = (predicted_top1 == actual_domain)
        is_top3 = (actual_domain in predicted_domains[:3])

        if is_top1:
            top1_correct += 1
            confidence_correct.append(confidence)
        else:
            confidence_incorrect.append(confidence)

        if is_top3:
            top3_correct += 1

        confusion[actual_domain][predicted_top1] += 1
        domain_stats[actual_domain]["total"] += 1
        if is_top1:
            domain_stats[actual_domain]["top1"] += 1
        if is_top3:
            domain_stats[actual_domain]["top3"] += 1

        results.append({
            "task": task_desc[:80] + "..." if len(task_desc) > 80 else task_desc,
            "actual": actual_domain,
            "predicted_top1": predicted_top1,
            "predicted_top3": predicted_domains[:3],
            "confidence": confidence,
            "top1_hit": is_top1,
            "top3_hit": is_top3,
        })

    n = len(GROUND_TRUTH)
    top1_acc = top1_correct / n
    top3_acc = top3_correct / n
    mean_conf_correct = (sum(confidence_correct) / len(confidence_correct)) if confidence_correct else 0
    mean_conf_incorrect = (sum(confidence_incorrect) / len(confidence_incorrect)) if confidence_incorrect else 0

    # Print results
    print("=" * 80)
    print("TASK RECOGNIZER ACCURACY BENCHMARK")
    print("=" * 80)
    print(f"\nSample size: {n} real session tasks")
    print(f"\nTop-1 Accuracy: {top1_correct}/{n} = {top1_acc:.1%}")
    print(f"Top-3 Accuracy: {top3_correct}/{n} = {top3_acc:.1%}")
    print(f"\nMean confidence (correct predictions):   {mean_conf_correct:.4f}")
    print(f"Mean confidence (incorrect predictions): {mean_conf_incorrect:.4f}")
    print(f"Confidence gap (correct - incorrect):    {mean_conf_correct - mean_conf_incorrect:+.4f}")

    # Detailed per-item results
    print("\n" + "-" * 80)
    print("DETAILED RESULTS")
    print("-" * 80)
    for r in results:
        status = "OK" if r["top1_hit"] else ("~3" if r["top3_hit"] else "MISS")
        print(f"\n[{status:4s}] {r['task']}")
        print(f"       actual={r['actual']:22s}  predicted={r['predicted_top1']:22s}  conf={r['confidence']:.3f}")
        if not r["top1_hit"]:
            print(f"       top-3: {r['predicted_top3']}")

    # Confusion matrix
    print("\n" + "-" * 80)
    print("CONFUSION MATRIX (rows=actual, cols=predicted)")
    print("-" * 80)

    # Get all domains that appear
    all_domains = sorted(set(
        list(confusion.keys()) +
        [pred for actuals in confusion.values() for pred in actuals.keys()]
    ))

    # Print header
    header = f"{'actual':22s} | " + " | ".join(f"{d[:8]:>8s}" for d in all_domains)
    print(header)
    print("-" * len(header))

    for actual in sorted(confusion.keys()):
        row = f"{actual:22s} | "
        cells = []
        for pred in all_domains:
            count = confusion[actual].get(pred, 0)
            cells.append(f"{count:8d}" if count > 0 else f"{'·':>8s}")
        row += " | ".join(cells)
        print(row)

    # Per-domain accuracy
    print("\n" + "-" * 80)
    print("PER-DOMAIN ACCURACY")
    print("-" * 80)
    for domain in sorted(domain_stats.keys()):
        s = domain_stats[domain]
        t1 = s["top1"] / s["total"] if s["total"] else 0
        t3 = s["top3"] / s["total"] if s["total"] else 0
        print(f"  {domain:22s}  n={s['total']:2d}  top1={t1:5.1%}  top3={t3:5.1%}")

    # Common failure modes
    print("\n" + "-" * 80)
    print("FAILURE MODE ANALYSIS")
    print("-" * 80)

    misroutes = defaultdict(int)
    for r in results:
        if not r["top1_hit"]:
            key = f"{r['actual']} -> {r['predicted_top1']}"
            misroutes[key] += 1

    if misroutes:
        for route, count in sorted(misroutes.items(), key=lambda x: -x[1]):
            print(f"  {route:45s}  x{count}")
    else:
        print("  No misroutes!")

    # Save JSON artifact
    artifact = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sample_size": n,
        "top1_accuracy": round(top1_acc, 4),
        "top3_accuracy": round(top3_acc, 4),
        "mean_confidence_correct": round(mean_conf_correct, 4),
        "mean_confidence_incorrect": round(mean_conf_incorrect, 4),
        "per_domain": {
            domain: {
                "n": s["total"],
                "top1_acc": round(s["top1"] / s["total"], 4) if s["total"] else 0,
                "top3_acc": round(s["top3"] / s["total"], 4) if s["total"] else 0,
            }
            for domain, s in domain_stats.items()
        },
        "misroutes": dict(misroutes),
        "detailed_results": results,
    }

    out_path = REPO_ROOT / "experiments" / "meta" / "task-recognizer-accuracy.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact saved: {out_path}")


if __name__ == "__main__":
    run_benchmark()
