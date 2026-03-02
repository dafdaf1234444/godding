"""
F-LNG1: Zipf's law test on swarm lesson citation distribution
Does lesson citation frequency follow a power law (Zipf)?
ISO-8 predicts: freq ∝ rank^(-α), with α ≈ 1.0 for natural language.

Usage: python3 tools/f_lng1_zipf_lessons.py [--save] [--verbose]
"""

import json
import math
import re
import argparse
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
CITATION_CACHE = REPO_ROOT / "experiments" / "compact-citation-cache.json"
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
EXPERIMENTS_DIR = REPO_ROOT / "experiments" / "linguistics"


def get_output_path(session: str) -> Path:
    return EXPERIMENTS_DIR / f"f-lng1-zipf-lessons-{session.lower()}.json"


def load_prior_series() -> list:
    """Load the series array from the most recent existing artifact."""
    artifacts = sorted(EXPERIMENTS_DIR.glob("f-lng1-zipf-lessons-s*.json"))
    for artifact in reversed(artifacts):
        try:
            with open(artifact) as f:
                data = json.load(f)
            if "series" in data:
                return data["series"]
        except Exception:
            continue
    return []


def get_citation_counts_from_cache():
    """Aggregate per-file citations into per-lesson citation counts."""
    if not CITATION_CACHE.exists():
        return {}
    with open(CITATION_CACHE) as f:
        cache = json.load(f)
    counts = defaultdict(int)
    for file_data in cache.values():
        for lesson_id, n in file_data.get("cites", {}).items():
            counts[lesson_id] += n
    return dict(counts)


def get_citation_counts_from_scan():
    """Scan all non-lesson .md files for L-NNN citations (fallback)."""
    citation_pattern = re.compile(r"\bL-(\d+)\b")
    counts = defaultdict(int)
    for md_file in REPO_ROOT.rglob("*.md"):
        # Skip lesson files themselves
        if md_file.parent == LESSONS_DIR:
            continue
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in citation_pattern.finditer(text):
            lesson_id = f"L-{int(match.group(1)):03d}"
            counts[lesson_id] += 1
    return dict(counts)


def fit_power_law(ranked_counts):
    """
    Fit freq ∝ rank^(-α) via linear regression on log-log scale.
    Returns (alpha, r_squared, intercept).
    Only uses lessons with at least 1 citation.
    """
    cited = [(rank, cnt) for rank, (lid, cnt) in enumerate(ranked_counts, 1) if cnt > 0]
    if len(cited) < 3:
        return None, None, None

    n = len(cited)
    log_ranks = [math.log(r) for r, _ in cited]
    log_freqs = [math.log(c) for _, c in cited]

    # OLS: log_freq = -alpha * log_rank + C
    mean_lr = sum(log_ranks) / n
    mean_lf = sum(log_freqs) / n
    ss_xy = sum((log_ranks[i] - mean_lr) * (log_freqs[i] - mean_lf) for i in range(n))
    ss_xx = sum((log_ranks[i] - mean_lr) ** 2 for i in range(n))
    slope = ss_xy / ss_xx  # -alpha
    intercept = mean_lf - slope * mean_lr

    # R²
    y_pred = [slope * log_ranks[i] + intercept for i in range(n)]
    ss_res = sum((log_freqs[i] - y_pred[i]) ** 2 for i in range(n))
    ss_tot = sum((log_freqs[i] - mean_lf) ** 2 for i in range(n))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    alpha = -slope  # alpha > 0 for decreasing curve
    return alpha, r_squared, intercept


def run(save=False, verbose=False, session="S328"):
    # Always use direct scan (correct regex, fresh data).
    # Cache is stale (100% SHA mismatch) and caused 13-point α decline artifact (L-512).
    counts = get_citation_counts_from_scan()
    source = "scan"

    # Get all lesson IDs from files
    all_lessons = sorted(
        [f.stem for f in LESSONS_DIR.glob("L-*.md")],
        key=lambda x: int(x.split("-")[1])
    )
    total_lessons = len(all_lessons)

    # Build full ranked list (including zero-cited)
    lesson_counts = [(lid, counts.get(lid, 0)) for lid in all_lessons]
    lesson_counts.sort(key=lambda x: x[1], reverse=True)

    cited = [(lid, cnt) for lid, cnt in lesson_counts if cnt > 0]
    zero_cited = [(lid, cnt) for lid, cnt in lesson_counts if cnt == 0]

    # Fit power law on cited lessons only
    alpha, r_squared, intercept = fit_power_law(cited)

    # Zipf verdict: α ≈ 1.0 (±0.3 tolerance for natural language variation)
    zipf_holds = (alpha is not None and 0.7 <= alpha <= 1.3)
    zipf_strong = (alpha is not None and 0.9 <= alpha <= 1.1)
    head_heavy = (alpha is not None and alpha > 1.3)  # steeper than Zipf
    tail_flat = (alpha is not None and alpha < 0.7)   # flatter than Zipf

    # Citation percentiles
    all_counts_nonzero = [cnt for _, cnt in cited]
    p90 = sorted(all_counts_nonzero)[int(0.9 * len(all_counts_nonzero))] if all_counts_nonzero else 0
    p50 = sorted(all_counts_nonzero)[int(0.5 * len(all_counts_nonzero))] if all_counts_nonzero else 0

    result = {
        "experiment": "F-LNG1",
        "session": session,
        "description": f"F-LNG1 Zipf law at n={total_lessons} ({session}) — ISO annotation effect + stall check",
        "hypothesis": "Lesson citations follow power law with α ≈ 1.0 (Zipf), confirming ISO-8 isomorphism",
        "data_source": source,
        "total_lessons": total_lessons,
        "cited_lessons": len(cited),
        "zero_cited_lessons": len(zero_cited),
        "citation_coverage_pct": round(100 * len(cited) / total_lessons, 1) if total_lessons else 0,
        "top_10": cited[:10],
        "zero_cited_sample": [lid for lid, _ in zero_cited[:10]],
        "power_law_alpha": round(alpha, 4) if alpha is not None else None,
        "power_law_r_squared": round(r_squared, 4) if r_squared is not None else None,
        "zipf_holds": zipf_holds,
        "zipf_strong": zipf_strong,
        "head_heavy": head_heavy,
        "tail_flat": tail_flat,
        "median_citations_nonzero": p50,
        "p90_citations": p90,
        "verdict": (
            "ZIPF_STRONG" if zipf_strong else
            "ZIPF_WEAK" if zipf_holds else
            "HEAD_HEAVY" if head_heavy else
            "TAIL_FLAT" if tail_flat else
            "INSUFFICIENT_DATA"
        ),
        "interpretation": "",
    }

    # Interpretation
    if zipf_strong:
        result["interpretation"] = (
            f"Lesson citation distribution closely follows Zipf's law (α={alpha:.3f} ≈ 1.0, R²={r_squared:.3f}). "
            f"ISO-8 isomorphism CONFIRMED: swarm knowledge corpus exhibits the same scale-free power law as "
            f"natural language word frequency. A small number of lessons dominate citations (~{len(cited[:10])} "
            f"lessons account for most references)."
        )
    elif zipf_holds:
        result["interpretation"] = (
            f"Lesson citation distribution is approximately Zipfian (α={alpha:.3f}, R²={r_squared:.3f}). "
            f"ISO-8 isomorphism PARTIALLY confirmed. α deviates from 1.0 — "
            f"{'steeper (more head concentration)' if alpha > 1.0 else 'flatter (more even distribution)'} "
            f"than canonical Zipf."
        )
    elif head_heavy:
        result["interpretation"] = (
            f"Lesson citation is HEAD-HEAVY (α={alpha:.3f} > 1.3): citations concentrate more strongly "
            f"than Zipf predicts. A few lessons dominate absolutely. Possible cause: "
            f"CORE principles cited everywhere; compaction cycles created citation monoculture. "
            f"ISO-8 isomorphism present but stronger than natural language."
        )
    elif tail_flat:
        result["interpretation"] = (
            f"Lesson citation is TAIL-FLAT (α={alpha:.3f} < 0.7): distribution more even than Zipf. "
            f"Possible cause: lessons are too specific, few cross-domain citations. "
            f"ISO-8 isomorphism weakly present."
        )
    else:
        result["interpretation"] = "Insufficient cited lessons for reliable power law fit."

    # Load prior series and append current run
    prior_series = load_prior_series()
    current_entry = {"session": session, "n": total_lessons, "alpha": round(alpha, 4) if alpha else None, "r2": round(r_squared, 4) if r_squared else None}
    # Avoid duplicate session entry
    series = [s for s in prior_series if s.get("session") != session] + [current_entry]
    result["series"] = series

    # Stall detection: compare to last 2 prior entries
    prior_alphas = [s["alpha"] for s in series[:-1] if s.get("alpha") is not None]
    if len(prior_alphas) >= 2 and alpha is not None:
        rate = (alpha - prior_alphas[-1]) / max(1, total_lessons - (series[-2].get("n", total_lessons - 10)))
        stall = abs(rate) < 0.0005
        result["rate_per_lesson"] = round(rate, 6)
        result["stall_detected"] = stall
        result["stall_note"] = f"Rate {rate:.5f}/L vs historical -0.00158/L — {'STALL' if stall else 'DECLINING'}" if stall else f"Declining at {rate:.5f}/L"
    else:
        result["rate_per_lesson"] = None
        result["stall_detected"] = False
        result["stall_note"] = "Insufficient prior data"

    if verbose:
        print(f"\n=== F-LNG1: Zipf Law Test on Lesson Citations ===")
        print(f"Total lessons: {total_lessons} | Cited: {len(cited)} ({result['citation_coverage_pct']}%) | Zero-cited: {len(zero_cited)}")
        print(f"\nTop 10 most-cited lessons:")
        for i, (lid, cnt) in enumerate(cited[:10], 1):
            print(f"  {i:2d}. {lid}: {cnt} citations")
        print(f"\nPower law fit: α={alpha:.4f}, R²={r_squared:.4f}" if alpha else "\nInsufficient data for fit")
        print(f"Verdict: {result['verdict']}")
        if result.get("rate_per_lesson") is not None:
            print(f"Rate: {result['rate_per_lesson']:.5f}/L — {'STALL' if result['stall_detected'] else 'DECLINING'}")
        print(f"\n{result['interpretation']}")
        print(f"\nSeries ({len(series)} runs):")
        for s in series:
            print(f"  {s['session']}: n={s['n']}, α={s['alpha']}")

    if save:
        output = get_output_path(session)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Saved: {output}")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F-LNG1: Zipf law test on lesson citations")
    parser.add_argument("--save", action="store_true", help="Save JSON artifact")
    parser.add_argument("--verbose", action="store_true", help="Print results")
    parser.add_argument("--session", default="S328", help="Session label (e.g. S328)")
    args = parser.parse_args()
    run(save=args.save, verbose=args.verbose, session=args.session)
