#!/usr/bin/env python3
"""F-STR1 Prospective Validation: UCB1+value_density dispatch impact.

Compares DOMEX lane outcomes BEFORE (S370-S379) vs AFTER (S380-S382)
the UCB1+value_density dispatch integration (L-729, S380).

Metrics:
  1. Merge rate: MERGED / (MERGED + ABANDONED)
  2. Lesson yield: avg new lessons per MERGED lane (L-NNN count in note/etc)
  3. Domain diversity: unique domains touched
  4. EAD compliance: lanes with actual+diff filled (not TBD)

Usage:
  python3 tools/f_str1_prospective_validation.py
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """Handle numpy types in JSON serialization."""
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANES_FILE = os.path.join(REPO_ROOT, "tasks", "SWARM-LANES.md")
ARCHIVE_FILE = os.path.join(REPO_ROOT, "tasks", "SWARM-LANES-ARCHIVE.md")
OUTPUT_FILE = os.path.join(
    REPO_ROOT, "experiments", "strategy",
    "f-str1-prospective-validation-s382.json"
)

BASELINE_RANGE = (370, 379)   # S370-S379
TREATMENT_RANGE = (380, 382)  # S380-S382


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def extract_session_number(lane_id: str, session_col: str) -> int | None:
    """Extract session number from lane_id (preferred) or session column."""
    # Try lane_id first: e.g. DOMEX-META-S377 -> 377
    m = re.search(r'S(\d+)', lane_id)
    if m:
        return int(m.group(1))
    # Fallback to session column
    m = re.search(r'S?(\d+)', session_col.strip())
    if m:
        return int(m.group(1))
    return None


def extract_domain(lane_id: str) -> str:
    """Extract domain abbreviation from lane_id.

    e.g. DOMEX-META-S377 -> META, DOMEX-CAT2-S381 -> CAT
    """
    m = re.match(r'DOMEX-([A-Z]+)', lane_id)
    if m:
        return m.group(1)
    return "UNKNOWN"


def count_lessons(text: str) -> int:
    """Count unique L-NNN references in a text string."""
    matches = re.findall(r'\bL-(\d+)\b', text)
    return len(set(matches))


def check_ead_compliance(etc_col: str, note_col: str) -> bool:
    """Check if actual and diff EAD fields are filled (not TBD or empty)."""
    combined = etc_col + " " + note_col
    actual_match = re.search(r'actual=([^;|]+)', combined)
    diff_match = re.search(r'diff=([^;|]+)', combined)

    if not actual_match or not diff_match:
        return False

    actual_val = actual_match.group(1).strip()
    diff_val = diff_match.group(1).strip()

    # TBD or empty means non-compliant
    if actual_val.upper() in ("TBD", "", "N/A"):
        return False
    if diff_val.upper() in ("TBD", "", "N/A"):
        return False

    return True


def parse_lane_row(line: str) -> dict | None:
    """Parse a pipe-delimited lane row into a dict.

    Columns: Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes
    """
    parts = [p.strip() for p in line.split("|")]
    # Remove empty strings from leading/trailing pipes
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]

    if len(parts) < 12:
        return None

    lane_id = parts[1].strip()
    if "DOMEX" not in lane_id:
        return None

    session_col = parts[2].strip()
    etc_col = parts[9].strip()
    status = parts[10].strip().upper()
    note = parts[11].strip() if len(parts) > 11 else ""

    session_num = extract_session_number(lane_id, session_col)
    if session_num is None:
        return None

    domain = extract_domain(lane_id)
    lessons = count_lessons(etc_col + " " + note)
    ead_ok = check_ead_compliance(etc_col, note)

    return {
        "lane_id": lane_id,
        "session_num": session_num,
        "domain": domain,
        "status": status,
        "lessons": lessons,
        "ead_compliant": ead_ok,
        "etc": etc_col,
        "note": note,
    }


def load_lanes(filepath: str) -> list[dict]:
    """Load and parse all DOMEX lanes from a file."""
    lanes = []
    if not os.path.exists(filepath):
        return lanes
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            if "---" in line and line.count("|") > 3:
                continue  # header separator
            if "Lane" in line and "Session" in line and "Status" in line:
                continue  # header row
            row = parse_lane_row(line)
            if row:
                lanes.append(row)
    return lanes


def deduplicate_lanes(lanes: list[dict]) -> list[dict]:
    """Keep only the LATEST row per lane_id (append-only log -> last wins)."""
    seen = {}
    for lane in lanes:
        lid = lane["lane_id"]
        seen[lid] = lane  # last occurrence wins
    return list(seen.values())


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def classify_period(session_num: int) -> str | None:
    if BASELINE_RANGE[0] <= session_num <= BASELINE_RANGE[1]:
        return "baseline"
    if TREATMENT_RANGE[0] <= session_num <= TREATMENT_RANGE[1]:
        return "treatment"
    return None


def compute_metrics(lanes: list[dict]) -> dict:
    """Compute the 4 metrics for a set of lanes."""
    merged = [l for l in lanes if l["status"] == "MERGED"]
    abandoned = [l for l in lanes if l["status"] == "ABANDONED"]
    closed = merged + abandoned

    n_merged = len(merged)
    n_abandoned = len(abandoned)
    n_total = n_merged + n_abandoned

    # 1. Merge rate
    merge_rate = n_merged / n_total if n_total > 0 else None

    # 2. Lesson yield (per MERGED lane)
    if n_merged > 0:
        lesson_counts = [l["lessons"] for l in merged]
        avg_lessons = sum(lesson_counts) / len(lesson_counts)
    else:
        lesson_counts = []
        avg_lessons = None

    # 3. Domain diversity
    domains = set(l["domain"] for l in lanes)

    # 4. EAD compliance
    n_ead_ok = sum(1 for l in lanes if l["ead_compliant"])
    ead_rate = n_ead_ok / len(lanes) if lanes else None

    return {
        "n_lanes": len(lanes),
        "n_closed": n_total,
        "n_merged": n_merged,
        "n_abandoned": n_abandoned,
        "merge_rate": round(merge_rate, 4) if merge_rate is not None else None,
        "lesson_counts": lesson_counts,
        "avg_lessons_per_merged": round(avg_lessons, 3) if avg_lessons is not None else None,
        "domains": sorted(domains),
        "n_domains": len(domains),
        "ead_compliant": n_ead_ok,
        "ead_rate": round(ead_rate, 4) if ead_rate is not None else None,
        "lane_ids": [l["lane_id"] for l in lanes],
    }


def run_statistical_tests(baseline: dict, treatment: dict) -> dict:
    """Run Fisher exact test (merge rate) and Mann-Whitney (lesson yield)."""
    results = {}

    try:
        from scipy.stats import fisher_exact, mannwhitneyu
    except ImportError:
        return {"error": "scipy not available"}

    # Fisher exact for merge rate (2x2 table)
    b_merged = baseline["n_merged"]
    b_abandoned = baseline["n_abandoned"]
    t_merged = treatment["n_merged"]
    t_abandoned = treatment["n_abandoned"]

    if b_merged + b_abandoned > 0 and t_merged + t_abandoned > 0:
        table = [[t_merged, t_abandoned], [b_merged, b_abandoned]]
        odds_ratio, p_value = fisher_exact(table, alternative="two-sided")
        results["merge_rate_fisher"] = {
            "contingency_table": table,
            "odds_ratio": round(odds_ratio, 4) if odds_ratio != float("inf") else "inf",
            "p_value": round(p_value, 4),
            "significant_005": p_value < 0.05,
            "direction": "treatment_higher" if (treatment["merge_rate"] or 0) > (baseline["merge_rate"] or 0) else "baseline_higher_or_equal",
        }
    else:
        results["merge_rate_fisher"] = {"error": "insufficient data"}

    # Mann-Whitney U for lesson yield (per-lane lesson counts)
    b_lessons = baseline["lesson_counts"]
    t_lessons = treatment["lesson_counts"]

    if len(b_lessons) >= 2 and len(t_lessons) >= 2:
        try:
            stat, p_value = mannwhitneyu(t_lessons, b_lessons, alternative="two-sided")
            results["lesson_yield_mannwhitney"] = {
                "U_statistic": round(stat, 2),
                "p_value": round(p_value, 4),
                "significant_005": p_value < 0.05,
                "treatment_median": sorted(t_lessons)[len(t_lessons) // 2],
                "baseline_median": sorted(b_lessons)[len(b_lessons) // 2],
            }
        except ValueError as e:
            results["lesson_yield_mannwhitney"] = {"error": str(e)}
    else:
        results["lesson_yield_mannwhitney"] = {
            "error": f"insufficient data (baseline n={len(b_lessons)}, treatment n={len(t_lessons)})"
        }

    # Domain diversity comparison (simple ratio + per-lane normalized)
    b_per_lane = baseline["n_domains"] / baseline["n_lanes"] if baseline["n_lanes"] > 0 else 0
    t_per_lane = treatment["n_domains"] / treatment["n_lanes"] if treatment["n_lanes"] > 0 else 0
    results["domain_diversity"] = {
        "baseline_domains": baseline["n_domains"],
        "treatment_domains": treatment["n_domains"],
        "ratio": round(treatment["n_domains"] / baseline["n_domains"], 3)
            if baseline["n_domains"] > 0 else None,
        "baseline_domains_per_lane": round(b_per_lane, 3),
        "treatment_domains_per_lane": round(t_per_lane, 3),
        "note": "Raw count comparison confounded by unequal window size (10 vs 3 sessions). Per-lane ratio is more informative.",
    }

    # EAD compliance comparison (Fisher exact)
    if baseline["n_lanes"] > 0 and treatment["n_lanes"] > 0:
        b_ead_ok = baseline["ead_compliant"]
        b_ead_fail = baseline["n_lanes"] - b_ead_ok
        t_ead_ok = treatment["ead_compliant"]
        t_ead_fail = treatment["n_lanes"] - t_ead_ok
        table_ead = [[t_ead_ok, t_ead_fail], [b_ead_ok, b_ead_fail]]
        odds_ead, p_ead = fisher_exact(table_ead, alternative="two-sided")
        results["ead_compliance_fisher"] = {
            "contingency_table": table_ead,
            "odds_ratio": round(odds_ead, 4) if odds_ead != float("inf") else "inf",
            "p_value": round(p_ead, 4),
            "significant_005": p_ead < 0.05,
        }
    else:
        results["ead_compliance_fisher"] = {"error": "insufficient data"}

    return results


def determine_verdict(baseline: dict, treatment: dict, stats: dict) -> dict:
    """Produce a summary verdict."""
    improvements = []
    regressions = []
    neutral = []

    # Merge rate
    if baseline["merge_rate"] is not None and treatment["merge_rate"] is not None:
        delta = treatment["merge_rate"] - baseline["merge_rate"]
        if delta > 0.05:
            improvements.append(f"merge_rate +{delta:.1%}")
        elif delta < -0.05:
            regressions.append(f"merge_rate {delta:.1%}")
        else:
            neutral.append(f"merge_rate delta={delta:+.1%}")

    # Lesson yield
    if baseline["avg_lessons_per_merged"] is not None and treatment["avg_lessons_per_merged"] is not None:
        delta = treatment["avg_lessons_per_merged"] - baseline["avg_lessons_per_merged"]
        if delta > 0.2:
            improvements.append(f"lesson_yield +{delta:.2f}")
        elif delta < -0.2:
            regressions.append(f"lesson_yield {delta:+.2f}")
        else:
            neutral.append(f"lesson_yield delta={delta:+.2f}")

    # Domain diversity (per-lane normalized to account for unequal window size)
    d_base = baseline["n_domains"]
    d_treat = treatment["n_domains"]
    b_per_lane = d_base / baseline["n_lanes"] if baseline["n_lanes"] > 0 else 0
    t_per_lane = d_treat / treatment["n_lanes"] if treatment["n_lanes"] > 0 else 0
    d_delta = t_per_lane - b_per_lane
    if d_delta > 0.05:
        improvements.append(f"domain_diversity_per_lane {b_per_lane:.2f}->{t_per_lane:.2f}")
    elif d_delta < -0.05:
        regressions.append(f"domain_diversity_per_lane {b_per_lane:.2f}->{t_per_lane:.2f}")
    else:
        neutral.append(f"domain_diversity_per_lane {b_per_lane:.2f}->{t_per_lane:.2f} (delta={d_delta:+.2f})")

    # EAD compliance
    if baseline["ead_rate"] is not None and treatment["ead_rate"] is not None:
        delta = treatment["ead_rate"] - baseline["ead_rate"]
        if delta > 0.05:
            improvements.append(f"ead_compliance +{delta:.1%}")
        elif delta < -0.05:
            regressions.append(f"ead_compliance {delta:.1%}")
        else:
            neutral.append(f"ead_compliance delta={delta:+.1%}")

    # Statistical significance
    any_significant = False
    for key in ["merge_rate_fisher", "lesson_yield_mannwhitney", "ead_compliance_fisher"]:
        if key in stats and isinstance(stats[key], dict):
            if stats[key].get("significant_005", False):
                any_significant = True

    if len(improvements) >= 2 and any_significant:
        verdict = "CONFIRMED"
        summary = "UCB1+value_density dispatch shows statistically significant improvement on 2+ metrics."
    elif len(improvements) >= 2:
        verdict = "PARTIALLY_CONFIRMED"
        summary = "Treatment shows improvement on 2+ metrics but statistical significance not reached (small n)."
    elif len(improvements) >= 1:
        verdict = "WEAK_SIGNAL"
        summary = "Treatment shows improvement on 1 metric; insufficient evidence for confirmation."
    elif len(regressions) > len(improvements):
        verdict = "REGRESSION"
        summary = "Treatment shows regression on more metrics than improvement."
    else:
        verdict = "NULL"
        summary = "No meaningful difference detected between baseline and treatment periods."

    return {
        "verdict": verdict,
        "summary": summary,
        "improvements": improvements,
        "regressions": regressions,
        "neutral": neutral,
        "any_statistically_significant": any_significant,
        "caveat": (
            "Observational study with small treatment window (3 sessions). "
            "Confounders include session maturity, concurrent tooling changes, "
            "and domain selection effects. Causal attribution requires longer observation."
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Load from both files
    lanes_active = load_lanes(LANES_FILE)
    lanes_archive = load_lanes(ARCHIVE_FILE)
    all_lanes = lanes_archive + lanes_active

    # Deduplicate: keep last occurrence per lane_id
    all_lanes = deduplicate_lanes(all_lanes)

    # Classify into periods
    baseline_lanes = []
    treatment_lanes = []
    excluded = 0

    for lane in all_lanes:
        period = classify_period(lane["session_num"])
        if period == "baseline":
            baseline_lanes.append(lane)
        elif period == "treatment":
            treatment_lanes.append(lane)
        else:
            excluded += 1

    # Only keep closed lanes (MERGED or ABANDONED) for merge rate analysis
    # but use all lanes for domain diversity and EAD compliance
    baseline_metrics = compute_metrics(baseline_lanes)
    treatment_metrics = compute_metrics(treatment_lanes)

    # Statistical tests
    stats = run_statistical_tests(baseline_metrics, treatment_metrics)

    # Verdict
    verdict = determine_verdict(baseline_metrics, treatment_metrics, stats)

    # Build output
    output = {
        "experiment": "F-STR1 prospective validation: UCB1+value_density dispatch impact",
        "session": "S382",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "frontier": "F-STR1",
        "method": (
            "Quasi-experimental pre/post comparison of DOMEX lane outcomes. "
            "Baseline: S370-S379 (before UCB1+value_density integration). "
            "Treatment: S380-S382 (after L-729 dispatch change). "
            "4 metrics: merge rate, lesson yield, domain diversity, EAD compliance. "
            "Fisher exact test for proportions, Mann-Whitney U for continuous."
        ),
        "data_sources": [
            "tasks/SWARM-LANES.md",
            "tasks/SWARM-LANES-ARCHIVE.md",
        ],
        "intervention": {
            "description": "UCB1+value_density integrated into dispatch_optimizer.py",
            "commit": "L-729",
            "session": "S380",
        },
        "total_domex_lanes_parsed": len(all_lanes),
        "excluded_outside_range": excluded,
        "baseline": {
            "period": f"S{BASELINE_RANGE[0]}-S{BASELINE_RANGE[1]}",
            "n_lanes": baseline_metrics["n_lanes"],
            "n_merged": baseline_metrics["n_merged"],
            "n_abandoned": baseline_metrics["n_abandoned"],
            "merge_rate": baseline_metrics["merge_rate"],
            "avg_lessons_per_merged": baseline_metrics["avg_lessons_per_merged"],
            "n_domains": baseline_metrics["n_domains"],
            "domains": baseline_metrics["domains"],
            "ead_compliant": baseline_metrics["ead_compliant"],
            "ead_rate": baseline_metrics["ead_rate"],
            "lane_ids": baseline_metrics["lane_ids"],
        },
        "treatment": {
            "period": f"S{TREATMENT_RANGE[0]}-S{TREATMENT_RANGE[1]}",
            "n_lanes": treatment_metrics["n_lanes"],
            "n_merged": treatment_metrics["n_merged"],
            "n_abandoned": treatment_metrics["n_abandoned"],
            "merge_rate": treatment_metrics["merge_rate"],
            "avg_lessons_per_merged": treatment_metrics["avg_lessons_per_merged"],
            "n_domains": treatment_metrics["n_domains"],
            "domains": treatment_metrics["domains"],
            "ead_compliant": treatment_metrics["ead_compliant"],
            "ead_rate": treatment_metrics["ead_rate"],
            "lane_ids": treatment_metrics["lane_ids"],
        },
        "statistical_comparison": stats,
        "verdict": verdict,
    }

    # Write JSON artifact
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)

    # Print summary
    print("=" * 70)
    print("F-STR1 Prospective Validation: UCB1+value_density Dispatch Impact")
    print("=" * 70)
    print()
    print(f"Total DOMEX lanes parsed: {len(all_lanes)}")
    print(f"Excluded (outside range): {excluded}")
    print()

    print(f"--- BASELINE (S{BASELINE_RANGE[0]}-S{BASELINE_RANGE[1]}) ---")
    print(f"  Lanes: {baseline_metrics['n_lanes']}")
    print(f"  Merged/Abandoned: {baseline_metrics['n_merged']}/{baseline_metrics['n_abandoned']}")
    print(f"  Merge rate: {baseline_metrics['merge_rate']}")
    print(f"  Avg lessons/merged: {baseline_metrics['avg_lessons_per_merged']}")
    print(f"  Domains ({baseline_metrics['n_domains']}): {', '.join(baseline_metrics['domains'])}")
    print(f"  EAD compliance: {baseline_metrics['ead_compliant']}/{baseline_metrics['n_lanes']} ({baseline_metrics['ead_rate']})")
    print()

    print(f"--- TREATMENT (S{TREATMENT_RANGE[0]}-S{TREATMENT_RANGE[1]}) ---")
    print(f"  Lanes: {treatment_metrics['n_lanes']}")
    print(f"  Merged/Abandoned: {treatment_metrics['n_merged']}/{treatment_metrics['n_abandoned']}")
    print(f"  Merge rate: {treatment_metrics['merge_rate']}")
    print(f"  Avg lessons/merged: {treatment_metrics['avg_lessons_per_merged']}")
    print(f"  Domains ({treatment_metrics['n_domains']}): {', '.join(treatment_metrics['domains'])}")
    print(f"  EAD compliance: {treatment_metrics['ead_compliant']}/{treatment_metrics['n_lanes']} ({treatment_metrics['ead_rate']})")
    print()

    print("--- STATISTICAL COMPARISON ---")
    for key, val in stats.items():
        if isinstance(val, dict):
            sig = val.get("significant_005", "N/A")
            p = val.get("p_value", "N/A")
            err = val.get("error", None)
            if err:
                print(f"  {key}: {err}")
            else:
                print(f"  {key}: p={p}, significant={sig}")
    print()

    print("--- VERDICT ---")
    print(f"  {verdict['verdict']}: {verdict['summary']}")
    if verdict["improvements"]:
        print(f"  Improvements: {', '.join(verdict['improvements'])}")
    if verdict["regressions"]:
        print(f"  Regressions: {', '.join(verdict['regressions'])}")
    if verdict["neutral"]:
        print(f"  Neutral: {', '.join(verdict['neutral'])}")
    print(f"  Caveat: {verdict['caveat']}")
    print()
    print(f"Artifact written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
