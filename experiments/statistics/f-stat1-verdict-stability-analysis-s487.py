#!/usr/bin/env python3
"""F-STAT1 verdict stability retest: does n>=100 inflection hold at N>1100?

Scans lesson corpus for:
1. All lessons with explicit sample sizes (n=X in Confidence header)
2. Lessons that reference reversals, contradictions, or falsifications
3. Whether any reversal at n>=100 exists (would falsify L-850)

Output: JSON artifact for experiments/statistics/
"""
import json, os, re, sys
from pathlib import Path

LESSON_DIR = Path("memory/lessons")

def parse_lesson(path):
    """Extract key fields from a lesson file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.strip().split("\n")

    result = {
        "id": path.stem,
        "session": None,
        "domain": None,
        "sharpe": None,
        "confidence": None,
        "sample_sizes": [],
        "cites": [],
        "text": text,
    }

    for line in lines:
        if line.startswith("Session:"):
            m = re.search(r"S(\d+)", line)
            if m:
                result["session"] = int(m.group(1))
            dm = re.search(r"Domain:\s*([^|]+)", line)
            if dm:
                result["domain"] = dm.group(1).strip()
            sm = re.search(r"Sharpe:\s*(\d+)", line)
            if sm:
                result["sharpe"] = int(sm.group(1))

        if line.startswith("Confidence:") or line.startswith("Cites:"):
            # Extract sample sizes
            for m in re.finditer(r"n[=≥](\d+)", line):
                result["sample_sizes"].append(int(m.group(1)))

        if line.startswith("Confidence:"):
            result["confidence"] = line.split(":", 1)[1].strip()

        if line.startswith("Cites:"):
            for m in re.finditer(r"L-(\d+)", line):
                result["cites"].append(f"L-{m.group(1)}")

    # Also check body for sample sizes in Confidence-style declarations
    for m in re.finditer(r"\(n[=≥](\d+)[^)]*\)", text):
        n = int(m.group(1))
        if n not in result["sample_sizes"]:
            result["sample_sizes"].append(n)

    return result

def find_reversal_indicators(text):
    """Check if a lesson describes reversing/contradicting a prior finding."""
    indicators = []
    patterns = [
        (r"revers(?:ed|al|ing)", "reversal"),
        (r"falsif(?:ied|ication|y)", "falsification"),
        (r"contradict(?:ed|s|ing|ion)", "contradiction"),
        (r"overtur(?:ned|n)", "overturned"),
        (r"was wrong", "admission"),
        (r"no longer holds", "invalidation"),
        (r"disproven", "disproven"),
        (r"DROP(?:PED)?", "dropped"),
        (r"prior.*incorrect", "correction"),
        (r"earlier.*incorrect", "correction"),
        (r"previously.*wrong", "correction"),
        (r"supersed(?:ed|es)", "superseded"),
    ]
    lower = text.lower()
    for pattern, label in patterns:
        if re.search(pattern, lower):
            indicators.append(label)
    return list(set(indicators))

def find_cited_reversals(lesson, all_lessons):
    """Find cases where this lesson reverses a specific cited lesson."""
    reversals = []
    text_lower = lesson["text"].lower()

    for cited_id in lesson["cites"]:
        # Check if text near the citation mentions reversal
        patterns = [
            rf"{cited_id.lower()}.*(?:revers|falsif|overtur|contradict|wrong|incorrect)",
            rf"(?:revers|falsif|overtur|contradict).*{cited_id.lower()}",
        ]
        for p in patterns:
            if re.search(p, text_lower):
                # Find the cited lesson's sample sizes
                cited = all_lessons.get(cited_id)
                if cited:
                    reversals.append({
                        "reversed_lesson": cited_id,
                        "reversed_n": cited.get("sample_sizes", []),
                        "reverser_n": lesson["sample_sizes"],
                        "reverser_session": lesson["session"],
                    })
                break
    return reversals

def main():
    lessons = {}
    for p in sorted(LESSON_DIR.glob("L-*.md")):
        try:
            lessons[p.stem] = parse_lesson(p)
        except Exception as e:
            print(f"WARN: {p.stem}: {e}", file=sys.stderr)

    total = len(lessons)

    # Sample size distribution
    with_n = {k: v for k, v in lessons.items() if v["sample_sizes"]}
    n_values = []
    for v in with_n.values():
        n_values.extend(v["sample_sizes"])

    n_distribution = {
        "total_lessons": total,
        "lessons_with_explicit_n": len(with_n),
        "pct_with_n": round(100 * len(with_n) / total, 1) if total else 0,
        "n_under_20": sum(1 for n in n_values if n < 20),
        "n_20_to_50": sum(1 for n in n_values if 20 <= n < 50),
        "n_50_to_100": sum(1 for n in n_values if 50 <= n < 100),
        "n_100_plus": sum(1 for n in n_values if n >= 100),
        "median_n": sorted(n_values)[len(n_values)//2] if n_values else None,
        "mean_n": round(sum(n_values)/len(n_values), 1) if n_values else None,
    }

    # Find reversal candidates
    reversal_candidates = []
    for lid, lesson in lessons.items():
        indicators = find_reversal_indicators(lesson["text"])
        if indicators:
            cited_reversals = find_cited_reversals(lesson, lessons)
            reversal_candidates.append({
                "lesson": lid,
                "session": lesson["session"],
                "indicators": indicators,
                "sample_sizes": lesson["sample_sizes"],
                "cited_reversals": cited_reversals,
                "domain": lesson["domain"],
            })

    # Focus on actual reversal pairs (where a specific lesson is cited as reversed)
    confirmed_reversals = []
    for rc in reversal_candidates:
        for cr in rc["cited_reversals"]:
            max_original_n = max(cr["reversed_n"]) if cr["reversed_n"] else None
            max_reverser_n = max(rc["sample_sizes"]) if rc["sample_sizes"] else None
            confirmed_reversals.append({
                "original": cr["reversed_lesson"],
                "original_n": cr["reversed_n"],
                "original_max_n": max_original_n,
                "reverser": rc["lesson"],
                "reverser_session": cr["reverser_session"],
                "reverser_n": rc["sample_sizes"],
                "reverser_max_n": max_reverser_n,
                "inflection_test": "PASS" if (max_original_n and max_original_n < 100) else
                                   "FAIL_L850" if (max_original_n and max_original_n >= 100) else "UNKNOWN",
            })

    # L-850's specific claim: reversals happen at n<100, stability at n>=100
    n100_failures = [r for r in confirmed_reversals if r["inflection_test"] == "FAIL_L850"]

    # Post-S401 reversals (after L-850 was written)
    post_s401_reversals = [r for r in confirmed_reversals
                           if r["reverser_session"] and r["reverser_session"] > 401]

    # Era distribution of sample sizes
    era_n = {"pre_s200": [], "s200_s400": [], "s400_plus": []}
    for v in with_n.values():
        s = v["session"]
        if s is None:
            continue
        for n in v["sample_sizes"]:
            if s < 200:
                era_n["pre_s200"].append(n)
            elif s < 400:
                era_n["s200_s400"].append(n)
            else:
                era_n["s400_plus"].append(n)

    era_stats = {}
    for era, vals in era_n.items():
        if vals:
            era_stats[era] = {
                "count": len(vals),
                "median": sorted(vals)[len(vals)//2],
                "mean": round(sum(vals)/len(vals), 1),
                "pct_under_50": round(100 * sum(1 for n in vals if n < 50) / len(vals), 1),
                "pct_over_100": round(100 * sum(1 for n in vals if n >= 100) / len(vals), 1),
            }

    verdict = "SURVIVED" if not n100_failures else "FALSIFIED"

    result = {
        "experiment": "DOMEX-STAT-S487",
        "frontier": "F-STAT1",
        "session": "S487",
        "domain": "statistics",
        "date": "2026-03-03",
        "expect": "L-850 n>=100 verdict stability inflection will NOT hold: new reversals at n>=100 should exist",
        "actual": f"{verdict}: {len(n100_failures)} reversals at n>=100 found out of {len(confirmed_reversals)} total confirmed reversals",
        "diff": f"expect=FALSIFIED, actual={verdict}",
        "method": {
            "corpus_scan": f"{total} lessons scanned",
            "reversal_detection": "regex for reversal/falsification/contradiction indicators + cited-lesson cross-reference",
            "inflection_test": "original lesson max_n >= 100 AND later reversed = FAIL_L850",
        },
        "n_distribution": n_distribution,
        "era_sample_sizes": era_stats,
        "reversal_candidates": len(reversal_candidates),
        "confirmed_reversals": confirmed_reversals,
        "post_s401_reversals": post_s401_reversals,
        "n100_failures": n100_failures,
        "verdict": verdict,
        "verdict_detail": (
            f"L-850 {verdict}. "
            f"{len(confirmed_reversals)} confirmed reversal pairs found. "
            f"{len(n100_failures)} involved originals with n>=100. "
            f"{len(post_s401_reversals)} reversals occurred after S401 (when L-850 was written)."
        ),
    }

    out_path = Path("experiments/statistics/f-stat1-verdict-stability-retest-s487.json")
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
