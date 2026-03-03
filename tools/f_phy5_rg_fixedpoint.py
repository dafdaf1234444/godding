#!/usr/bin/env python3
"""
f_phy5_rg_fixedpoint.py — F-PHY5: RG fixed-point test for Sharpe and yield.

Tests whether Sharpe ratio and session yield are scale-invariant (RG fixed points)
across growth epochs and compaction events, or drift systematically.

Method:
  1. Parse SESSION-LOG.md for per-session L+P production
  2. Define epoch boundaries from self-archaeology (E1-E6) + extensions
  3. Compute per-epoch: mean lesson yield, citation Sharpe (lessons created in epoch)
  4. Test: coefficient of variation (CV) < 0.20 = scale-invariant
  5. Test: monotonic trend (Spearman rho) — drift vs stability

Output: JSON experiment artifact + human-readable summary.

External grounding: Wilson & Cowan (1972) renormalization group in neural systems;
Kadanoff block-spin RG — fixed points are values unchanged under coarse-graining.
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent


def parse_session_log():
    """Extract per-session production from SESSION-LOG.md."""
    log_path = ROOT / "memory" / "SESSION-LOG.md"
    if not log_path.exists():
        return []
    sessions = []
    pat = re.compile(r"S(\d+)\s*[\t|].*?\+(\d+)L.*?\+(\d+)P")
    for line in log_path.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m:
            sessions.append({
                "session": int(m.group(1)),
                "lessons": int(m.group(2)),
                "principles": int(m.group(3)),
            })
    return sorted(sessions, key=lambda s: s["session"])


def get_lesson_creation_session():
    """Map lesson IDs to their creation session from file headers."""
    lessons_dir = ROOT / "memory" / "lessons"
    mapping = {}
    pat = re.compile(r"Session:\s*S(\d+)")
    for lf in sorted(lessons_dir.glob("L-*.md")):
        if lf.stem == "TEMPLATE":
            continue
        try:
            text = lf.read_text(encoding="utf-8", errors="ignore")
            m = pat.search(text[:500])
            if m:
                mapping[lf.stem] = int(m.group(1))
        except Exception:
            continue
    return mapping


def compute_citation_counts():
    """Count how many times each L-NNN is cited in non-lesson corpus."""
    lessons_dir = ROOT / "memory" / "lessons"
    # Build corpus from all .md files except lessons
    corpus_parts = []
    for f in ROOT.rglob("*.md"):
        if "lessons" not in str(f):
            try:
                corpus_parts.append(f.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass
    corpus = "\n".join(corpus_parts)

    counts = {}
    for lf in sorted(lessons_dir.glob("L-*.md")):
        if lf.stem == "TEMPLATE":
            continue
        try:
            lines = len([ln for ln in lf.read_text(encoding="utf-8").splitlines() if ln.strip()])
            cites = corpus.count(lf.stem)
            counts[lf.stem] = {"citations": cites, "lines": lines,
                               "sharpe": cites / max(lines, 1)}
        except Exception:
            continue
    return counts


def define_epochs():
    """Define epoch boundaries — from self-archaeology + extensions."""
    # E1-E6 from L-326 / f_evo5_self_archaeology
    # E7+ extended based on known structural transitions
    return [
        {"name": "E1-Bootstrap", "start": 1, "end": 56},
        {"name": "E2-Foundation", "start": 57, "end": 82},
        {"name": "E3-Consolidation", "start": 83, "end": 93},
        {"name": "E4-Growth", "start": 94, "end": 114},
        {"name": "E5-Plateau", "start": 115, "end": 180},
        {"name": "E6-Explosion", "start": 181, "end": 200},
        {"name": "E7-DomainMaturation", "start": 201, "end": 350},
        {"name": "E8-HighConcurrency", "start": 351, "end": 450},
        {"name": "E9-Succession", "start": 451, "end": 999},
    ]


def spearman_rho(x, y):
    """Simple Spearman rank correlation."""
    n = len(x)
    if n < 3:
        return 0.0
    # Rank
    def rank(vals):
        sorted_vals = sorted(enumerate(vals), key=lambda t: t[1])
        ranks = [0.0] * n
        for r, (i, _) in enumerate(sorted_vals):
            ranks[i] = r + 1
        return ranks
    rx, ry = rank(x), rank(y)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1 - 6 * d2 / (n * (n ** 2 - 1))


def main():
    sessions = parse_session_log()
    if not sessions:
        print("ERROR: No sessions found in SESSION-LOG.md")
        sys.exit(1)

    lesson_sessions = get_lesson_creation_session()
    citation_data = compute_citation_counts()
    epochs = define_epochs()

    # Compute per-epoch metrics
    session_by_num = {s["session"]: s for s in sessions}
    results = []

    for epoch in epochs:
        epoch_sessions = [s for s in sessions
                          if epoch["start"] <= s["session"] <= epoch["end"]]
        if not epoch_sessions:
            continue

        n_sessions = len(epoch_sessions)
        total_l = sum(s["lessons"] for s in epoch_sessions)
        total_p = sum(s["principles"] for s in epoch_sessions)
        yield_l = total_l / n_sessions if n_sessions > 0 else 0
        yield_p = total_p / n_sessions if n_sessions > 0 else 0
        productive = sum(1 for s in epoch_sessions if s["lessons"] + s["principles"] > 0)
        productivity_rate = productive / n_sessions if n_sessions > 0 else 0

        # Sharpe for lessons created in this epoch
        epoch_lessons = [lid for lid, s in lesson_sessions.items()
                         if epoch["start"] <= s <= epoch["end"]]
        sharpe_values = []
        for lid in epoch_lessons:
            if lid in citation_data:
                sharpe_values.append(citation_data[lid]["sharpe"])

        mean_sharpe = (sum(sharpe_values) / len(sharpe_values)) if sharpe_values else 0
        median_sharpe = sorted(sharpe_values)[len(sharpe_values) // 2] if sharpe_values else 0

        results.append({
            "epoch": epoch["name"],
            "session_range": f"S{epoch['start']}-S{epoch['end']}",
            "n_sessions": n_sessions,
            "n_lessons_created": len(epoch_lessons),
            "total_lessons": total_l,
            "total_principles": total_p,
            "yield_lessons_per_session": round(yield_l, 3),
            "yield_principles_per_session": round(yield_p, 3),
            "productivity_rate": round(productivity_rate, 3),
            "mean_sharpe": round(mean_sharpe, 4),
            "median_sharpe": round(median_sharpe, 4),
            "n_sharpe_samples": len(sharpe_values),
        })

    # Scale invariance tests
    yields = [r["yield_lessons_per_session"] for r in results if r["n_sessions"] >= 3]
    sharpes = [r["mean_sharpe"] for r in results if r["n_sharpe_samples"] >= 3]
    epoch_indices_y = list(range(len(yields)))
    epoch_indices_s = list(range(len(sharpes)))

    def cv(vals):
        if not vals:
            return float("inf")
        mean = sum(vals) / len(vals)
        if mean == 0:
            return float("inf")
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        return (var ** 0.5) / mean

    yield_cv = cv(yields)
    sharpe_cv = cv(sharpes)
    yield_rho = spearman_rho(epoch_indices_y, yields) if len(yields) >= 3 else 0
    sharpe_rho = spearman_rho(epoch_indices_s, sharpes) if len(sharpes) >= 3 else 0

    # Verdicts
    yield_invariant = yield_cv < 0.20
    sharpe_invariant = sharpe_cv < 0.20
    yield_drift = abs(yield_rho) > 0.6
    sharpe_drift = abs(sharpe_rho) > 0.6

    summary = {
        "yield": {
            "cv": round(yield_cv, 4),
            "spearman_rho": round(yield_rho, 4),
            "is_fixed_point": yield_invariant and not yield_drift,
            "verdict": "FIXED POINT" if (yield_invariant and not yield_drift)
                       else "DRIFTING" if yield_drift
                       else "VARIABLE (not fixed point)",
            "values": yields,
        },
        "sharpe": {
            "cv": round(sharpe_cv, 4),
            "spearman_rho": round(sharpe_rho, 4),
            "is_fixed_point": sharpe_invariant and not sharpe_drift,
            "verdict": "FIXED POINT" if (sharpe_invariant and not sharpe_drift)
                       else "DRIFTING" if sharpe_drift
                       else "VARIABLE (not fixed point)",
            "values": sharpes,
        },
    }

    # Print report
    print("=== F-PHY5: RG Fixed-Point Test ===\n")
    print(f"{'Epoch':<25} {'N_sess':>6} {'N_les':>6} {'Yield':>8} {'Sharpe':>8} {'ProdRate':>8}")
    print("-" * 70)
    for r in results:
        print(f"{r['epoch']:<25} {r['n_sessions']:>6} {r['n_lessons_created']:>6} "
              f"{r['yield_lessons_per_session']:>8.3f} {r['mean_sharpe']:>8.4f} "
              f"{r['productivity_rate']:>8.3f}")

    print(f"\n--- Scale Invariance Tests ---")
    print(f"Yield CV: {yield_cv:.4f} (threshold <0.20 for invariance)")
    print(f"Yield Spearman rho: {yield_rho:.4f} (|rho|>0.6 = monotonic drift)")
    print(f"Yield verdict: {summary['yield']['verdict']}")
    print()
    print(f"Sharpe CV: {sharpe_cv:.4f} (threshold <0.20 for invariance)")
    print(f"Sharpe Spearman rho: {sharpe_rho:.4f} (|rho|>0.6 = monotonic drift)")
    print(f"Sharpe verdict: {summary['sharpe']['verdict']}")

    # Write experiment artifact
    artifact = {
        "experiment": "DOMEX-PHY-S485",
        "frontier": "F-PHY5",
        "session": "S485",
        "domain": "physics",
        "date": "2026-03-03",
        "method": "Per-epoch Sharpe and yield computation across 9 epochs (S1-S485+). "
                  "CV < 0.20 = scale-invariant. |Spearman rho| > 0.6 = monotonic drift.",
        "external_grounding": "Kadanoff block-spin RG: fixed points are values unchanged "
                              "under coarse-graining. Wilson & Cowan (1972) neural RG.",
        "epochs": results,
        "invariance_tests": summary,
        "expect": "Sharpe is NOT invariant — expect systematic drift with era. "
                  "Yield may be more stable.",
        "actual": summary["yield"]["verdict"] + " (yield) / " + summary["sharpe"]["verdict"] + " (Sharpe)",
        "diff": f"Yield CV={yield_cv:.4f}, rho={yield_rho:.4f}. "
                f"Sharpe CV={sharpe_cv:.4f}, rho={sharpe_rho:.4f}.",
    }

    artifact_path = ROOT / "experiments" / "physics" / "f-phy5-rg-fixedpoint-s485.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"\nArtifact written: {artifact_path}")

    return summary


if __name__ == "__main__":
    main()
