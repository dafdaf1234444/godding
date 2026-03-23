#!/usr/bin/env python3
"""human_impact.py — Good/bad for humans extractor + soul distillation.

SIG-81: "swarm good and bad for humans — good/bad extractor, soul extractor
that can be used for better swarm swarm"

Scans swarm knowledge (lessons, principles, beliefs, tools) and classifies
each by human impact:
  GOOD    — helps humans understand, decide, act, learn, avoid harm
  BAD     — misleads, wastes time, overcomplicates, creates false confidence
  NEUTRAL — internal mechanism with no direct human transfer value

The "soul" is the extracted pattern of what makes things good/bad — distilled
into selection pressure that feeds back into dispatch, compact, and orient.

Usage:
    python3 tools/human_impact.py              # full scan + soul extraction
    python3 tools/human_impact.py --lessons     # lessons only
    python3 tools/human_impact.py --soul        # soul extraction only
    python3 tools/human_impact.py --orient      # orient-compatible summary
    python3 tools/human_impact.py --json        # machine-readable output
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lesson_header import parse_domain_field  # noqa: E402 — shared parser (SIG-80, L-1335)

REPO_ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
PRINCIPLES_FILE = REPO_ROOT / "memory" / "PRINCIPLES.md"
PHILOSOPHY_FILE = REPO_ROOT / "beliefs" / "PHILOSOPHY.md"

# ---------------------------------------------------------------------------
# Human-impact classification criteria
# ---------------------------------------------------------------------------

# Signals that a piece of knowledge is GOOD for humans (transferable value)
GOOD_SIGNALS = {
    "external_method": {
        "desc": "Method/pattern usable outside the swarm",
        "patterns": [
            r"(?i)\b(technique|method|pattern|approach|strategy|framework)\b.*(?:can be|is|for)\b",
            r"(?i)\b(any|every|general|universal)\b.*\b(system|team|org|project)\b",
        ],
        "weight": 3.0,
    },
    "teaches_principle": {
        "desc": "Teaches a transferable principle about systems/knowledge/collaboration",
        "patterns": [
            r"(?i)\b(law|theorem|principle|rule)\b.*\b(applies|holds|generalizes)\b",
            r"(?i)\b(whenever|always|never)\b.*\b(system|process|team)\b",
        ],
        "weight": 2.5,
    },
    "world_discovery": {
        "desc": "Discovers something about the world, not about itself",
        "patterns": [
            r"(?i)\b(external|real.world|empiric|measur)\b.*\b(data|evidence|result|finding)\b",
            r"(?i)\b(predict|forecast|estimat)\b.*\b(market|stock|outcome|event)\b",
        ],
        "weight": 3.0,
    },
    "human_efficiency": {
        "desc": "Makes human interaction more efficient or clearer",
        "patterns": [
            r"(?i)\b(human|user|operator|person)\b.*\b(understand|learn|decide|benefit)\b",
            r"(?i)\b(simplif|clar|reduc|sav)\b.*\b(time|effort|complexity|confusion)\b",
        ],
        "weight": 2.0,
    },
    "external_grounding": {
        "desc": "Grounded in external evidence, not self-referential",
        "patterns": [
            r"(?i)\b(Kauffman|Shannon|Zipf|Hawkes|Pareto|Nash|Arrow|Bayes)\b",
            r"(?i)\b(published|paper|study|literature|research|arXiv|journal)\b",
        ],
        "weight": 2.0,
    },
    "tool_transferable": {
        "desc": "Tool/technique portable to other projects",
        "patterns": [
            r"(?i)\b(reusable|portable|general.purpose|any\s+repo|any\s+project)\b",
        ],
        "weight": 2.5,
    },
    "external_citation": {
        "desc": "Explicitly grounded in external knowledge (External: field present)",
        "patterns": [
            r"^External:\s*.+",
        ],
        "weight": 2.5,
    },
    "quantified_finding": {
        "desc": "Quantified comparative finding (transferable measurement insight)",
        "patterns": [
            r"(?i)\b\d+(\.\d+)?x\s+(faster|slower|higher|lower|more|less|better|worse)",
            r"(?i)\b\d+(\.\d+)?%\s+(increase|decrease|improvement|reduction|drop|rise|gain)",
        ],
        "weight": 1.5,
    },
}

# Signals that a piece of knowledge is BAD for humans
BAD_SIGNALS = {
    "self_referential": {
        "desc": "Only refers to swarm's own state, no external transfer",
        "patterns": [
            r"(?i)\b(swarm|INDEX\.md|NEXT\.md|orient\.py|compact\.py|SWARM-LANES)\b.*\b(should|must|needs|has)\b",
            r"(?i)\b(lesson|principle|belief|frontier)\b.*\b(count|rate|drift|threshold)\b",
        ],
        "weight": -2.0,
    },
    "false_confidence": {
        "desc": "Claims certainty without external validation",
        "patterns": [
            r"(?i)\b(confirmed|verified|proven|established)\b.*(?:self|internal|swarm)",
            r"(?i)\b(EXCELLENT|SUFFICIENT)\b.*\b(self|internal)\b",
        ],
        "weight": -2.5,
    },
    "overcomplicated": {
        "desc": "Mechanism too complex for what it does",
        "patterns": [
            r"(?i)\b(meta-meta|recursive\s+recursive|self-self)\b",
            r"(?i)\b(cascade|pipeline|workflow)\b.*\b(of|for)\b.*\b(cascade|pipeline|workflow)\b",
        ],
        "weight": -1.5,
    },
    "zombie_aspiration": {
        "desc": "Aspirational claim maintained despite persistent non-compliance",
        "patterns": [
            r"(?i)\b(0\s+external|aspirational|undemonstrated|0\s+compliance)\b",
            r"(?i)\b(should|must|needs to)\b.*\b(but|however|yet)\b.*\b(0|zero|none|never)\b",
        ],
        "weight": -2.0,
    },
    "exclusionary_complexity": {
        "desc": "Barrier to understanding for non-swarm participants",
        "patterns": [
            r"(?i)\b(DOMEX|PHIL-\d+|F-[A-Z]+\d+|FM-\d+|SIG-\d+)\b.*\b(requires|see|cf)\b",
        ],
        "weight": -1.0,
    },
    "time_waste": {
        "desc": "Documents something that was done but produced no lasting value",
        "patterns": [
            r"(?i)\b(reverted|abandoned|undone|rolled.back)\b",
            r"(?i)\b(no\s+effect|null\s+result|no\s+change)\b.*\b(after|despite)\b",
        ],
        "weight": -0.5,  # Null results ARE valuable if recognized as such
    },
}


def _bootstrap_ratio_ci(
    n_good: int, n_bad: int, n_neutral: int, n_boot: int = 10000, alpha: float = 0.05
) -> dict:
    """Bootstrap 95% CI for benefit_ratio (good/bad).

    Resamples the classification labels and computes the ratio each time.
    Returns {"lower": float, "upper": float, "significant": bool}.
    Addresses skeptical-empiricist steerer signal: "1.02x has no CI."
    """
    import random
    total = n_good + n_bad + n_neutral
    if total == 0 or n_bad == 0:
        return {"lower": 0.0, "upper": 0.0, "significant": False}
    labels = ["good"] * n_good + ["bad"] * n_bad + ["neutral"] * n_neutral
    rng = random.Random(42)  # deterministic for reproducibility
    ratios = []
    for _ in range(n_boot):
        sample = rng.choices(labels, k=total)
        sg = sample.count("good")
        sb = sample.count("bad")
        ratios.append(sg / max(sb, 1))
    ratios.sort()
    lo = ratios[int(n_boot * alpha / 2)]
    hi = ratios[int(n_boot * (1 - alpha / 2))]
    return {
        "lower": round(lo, 2),
        "upper": round(hi, 2),
        "significant": lo > 1.0 or hi < 1.0,  # CI doesn't span 1.0
    }


def _score_text(text: str, signals: dict) -> list[tuple[str, float, str]]:
    """Score text against a signal dictionary. Returns [(signal_name, weight, desc)]."""
    hits = []
    for name, info in signals.items():
        for pat in info["patterns"]:
            if re.search(pat, text, re.MULTILINE):
                hits.append((name, info["weight"], info["desc"]))
                break  # One hit per signal
    return hits


def classify_lesson(path: Path) -> dict:
    """Classify a single lesson by human impact."""
    text = path.read_text(encoding="utf-8", errors="replace")

    # Extract metadata using shared parser for domain (SIG-80, L-1335)
    header_block = "\n".join(text.split("\n")[:10])
    title_match = re.search(r"Title:\s*(.+)", text)
    level_match = re.search(r"Level:\s*(\S+)", text)
    sharpe_match = re.search(r"Sharpe:\s*(\d+)", text)
    lesson_id = path.stem

    title = title_match.group(1).strip() if title_match else ""
    domains = parse_domain_field(header_block)
    domain = domains[0] if domains else "unknown"
    level = level_match.group(1).strip() if level_match else ""
    sharpe = int(sharpe_match.group(1)) if sharpe_match else 0

    good_hits = _score_text(text, GOOD_SIGNALS)
    bad_hits = _score_text(text, BAD_SIGNALS)

    good_score = sum(w for _, w, _ in good_hits)
    bad_score = sum(abs(w) for _, w, _ in bad_hits)
    net_score = good_score + sum(w for _, w, _ in bad_hits)  # bad weights are negative

    # Level bonus: higher-level lessons are more likely transferable
    level_bonus = {"L3": 1.0, "L4": 2.0, "L5": 3.0}.get(level, 0.0)
    net_score += level_bonus

    # Domain bonus: non-meta domains more likely externally relevant
    if domain and domain.lower() not in ("meta", ""):
        net_score += 0.5

    # Classify (L-1355: benefit-blindness fix — threshold lowered, requires signal evidence)
    has_good_signal = len(good_hits) > 0
    if net_score >= 1.5 and has_good_signal:
        classification = "GOOD"
    elif net_score >= 2.5:
        # High-level lessons (L4/L5) with domain bonus still qualify without signal
        classification = "GOOD"
    elif net_score < -1.0:
        classification = "BAD"
    else:
        classification = "NEUTRAL"

    return {
        "id": lesson_id,
        "title": title,
        "domain": domain,
        "level": level,
        "sharpe": sharpe,
        "good_hits": [(n, d) for n, _, d in good_hits],
        "bad_hits": [(n, d) for n, _, d in bad_hits],
        "good_score": round(good_score, 2),
        "bad_score": round(bad_score, 2),
        "net_score": round(net_score, 2),
        "classification": classification,
    }


def scan_lessons() -> list[dict]:
    """Scan all lessons and classify by human impact."""
    results = []
    if not LESSONS_DIR.exists():
        return results
    for path in sorted(LESSONS_DIR.glob("L-*.md")):
        try:
            results.append(classify_lesson(path))
        except Exception as e:
            print(f"  WARN: {path.name}: {e}", file=sys.stderr)
    return results


def extract_soul(results: list[dict]) -> dict:
    """Extract the evaluative pattern — the 'soul' — from classification results.

    The soul is the distilled pattern of what makes swarm outputs good or bad
    for humans. It becomes selection pressure for future swarm evolution.
    """
    good = [r for r in results if r["classification"] == "GOOD"]
    bad = [r for r in results if r["classification"] == "BAD"]
    neutral = [r for r in results if r["classification"] == "NEUTRAL"]

    # What domains produce the most human-good knowledge?
    domain_good = {}
    domain_bad = {}
    for r in results:
        d = r.get("domain", "unknown") or "unknown"
        domain_good.setdefault(d, 0)
        domain_bad.setdefault(d, 0)
        if r["classification"] == "GOOD":
            domain_good[d] += 1
        elif r["classification"] == "BAD":
            domain_bad[d] += 1

    # Which good signals fire most?
    good_signal_freq = {}
    for r in good:
        for name, desc in r["good_hits"]:
            good_signal_freq[name] = good_signal_freq.get(name, 0) + 1

    # Which bad signals fire most?
    bad_signal_freq = {}
    for r in bad:
        for name, desc in r["bad_hits"]:
            bad_signal_freq[name] = bad_signal_freq.get(name, 0) + 1

    # Level distribution of good vs bad
    good_levels = {}
    bad_levels = {}
    for r in good:
        lv = r.get("level", "?") or "?"
        good_levels[lv] = good_levels.get(lv, 0) + 1
    for r in bad:
        lv = r.get("level", "?") or "?"
        bad_levels[lv] = bad_levels.get(lv, 0) + 1

    # Soul: the top patterns
    soul = {
        "total": len(results),
        "good_count": len(good),
        "bad_count": len(bad),
        "neutral_count": len(neutral),
        "good_pct": round(100 * len(good) / max(len(results), 1), 1),
        "bad_pct": round(100 * len(bad) / max(len(results), 1), 1),
        "neutral_pct": round(100 * len(neutral) / max(len(results), 1), 1),
        "human_benefit_ratio": round(len(good) / max(len(bad), 1), 2),
        "benefit_ratio_ci": _bootstrap_ratio_ci(len(good), len(bad), len(neutral)),
        "top_good_domains": sorted(domain_good.items(), key=lambda x: -x[1])[:5],
        "top_bad_domains": sorted(domain_bad.items(), key=lambda x: -x[1])[:5],
        "top_good_signals": sorted(good_signal_freq.items(), key=lambda x: -x[1])[:5],
        "top_bad_signals": sorted(bad_signal_freq.items(), key=lambda x: -x[1])[:5],
        "good_levels": good_levels,
        "bad_levels": bad_levels,
        # Per-domain benefit scores for dispatch weighting (F-SOUL1 Phase 2)
        "domain_benefit_scores": {
            d: {
                "good": domain_good.get(d, 0),
                "bad": domain_bad.get(d, 0),
                "ratio": round(domain_good.get(d, 0) / max(domain_bad.get(d, 0), 1), 2),
            }
            for d in set(list(domain_good.keys()) + list(domain_bad.keys()))
        },
        # The soul extraction — what should swarm optimize for
        "selection_pressure": [],
    }

    # Derive selection pressures from the data
    if soul["good_pct"] < 20:
        soul["selection_pressure"].append(
            "CRITICAL: <20% of knowledge is good for humans. Swarm is mostly talking to itself."
        )

    if soul["bad_pct"] > 30:
        soul["selection_pressure"].append(
            f"WARNING: {soul['bad_pct']}% actively bad for humans. Self-referentiality is the dominant failure mode."
        )

    top_good_sig = soul["top_good_signals"][0] if soul["top_good_signals"] else None
    if top_good_sig:
        soul["selection_pressure"].append(
            f"AMPLIFY: '{top_good_sig[0]}' is the strongest human-good signal ({top_good_sig[1]} hits). "
            f"Dispatch should weight domains that produce this."
        )

    top_bad_sig = soul["top_bad_signals"][0] if soul["top_bad_signals"] else None
    if top_bad_sig:
        soul["selection_pressure"].append(
            f"REDUCE: '{top_bad_sig[0]}' is the strongest human-bad signal ({top_bad_sig[1]} hits). "
            f"Compact should target these first."
        )

    # The ratio is the soul metric
    soul["selection_pressure"].append(
        f"SOUL METRIC: human_benefit_ratio = {soul['human_benefit_ratio']}x "
        f"(good/bad). Target: >3.0x. This replaces self-referential quality metrics."
    )

    return soul


def print_report(results: list[dict], soul: dict, json_mode: bool = False):
    """Print human-readable or JSON report."""
    if json_mode:
        print(json.dumps({"results": results, "soul": soul}, indent=2))
        return

    print(f"=== HUMAN IMPACT SCAN | {soul['total']} items ===\n")
    print(f"  GOOD for humans:    {soul['good_count']} ({soul['good_pct']}%)")
    print(f"  BAD for humans:     {soul['bad_count']} ({soul['bad_pct']}%)")
    print(f"  NEUTRAL:            {soul['neutral_count']} ({soul['neutral_pct']}%)")
    ci = soul.get("benefit_ratio_ci")
    ci_str = f" (95% CI: [{ci.get('lower', '?')}x, {ci.get('upper', '?')}x])" if isinstance(ci, dict) else ""
    sig = " — NOT SIGNIFICANT" if isinstance(ci, dict) and not ci.get("significant") else ""
    print(f"  Human benefit ratio: {soul['human_benefit_ratio']}x{ci_str}{sig}")
    print()

    # Top GOOD lessons
    top_good = sorted([r for r in results if r["classification"] == "GOOD"],
                      key=lambda x: -x["net_score"])[:10]
    if top_good:
        print("--- Top 10 GOOD for humans ---")
        for r in top_good:
            signals = ", ".join(n for n, _ in r["good_hits"])
            print(f"  {r['id']} [{r['domain']}] {r['title'][:60]}")
            print(f"    score={r['net_score']} signals: {signals}")
        print()

    # Top BAD lessons
    top_bad = sorted([r for r in results if r["classification"] == "BAD"],
                     key=lambda x: x["net_score"])[:10]
    if top_bad:
        print("--- Top 10 BAD for humans ---")
        for r in top_bad:
            signals = ", ".join(n for n, _ in r["bad_hits"])
            print(f"  {r['id']} [{r['domain']}] {r['title'][:60]}")
            print(f"    score={r['net_score']} signals: {signals}")
        print()

    # Soul extraction
    print("=== SOUL EXTRACTION ===\n")
    print("What the swarm's evaluative core says about human benefit:\n")

    if soul["top_good_domains"]:
        print("  Domains best for humans:")
        for d, c in soul["top_good_domains"][:5]:
            print(f"    {d}: {c} good items")
    print()

    if soul["top_bad_domains"]:
        print("  Domains worst for humans:")
        for d, c in soul["top_bad_domains"][:5]:
            print(f"    {d}: {c} bad items")
    print()

    print("  Good-for-humans signals (what to amplify):")
    for name, count in soul["top_good_signals"]:
        desc = GOOD_SIGNALS[name]["desc"]
        print(f"    {name} ({count}x): {desc}")
    print()

    print("  Bad-for-humans signals (what to reduce):")
    for name, count in soul["top_bad_signals"]:
        desc = BAD_SIGNALS[name]["desc"]
        print(f"    {name} ({count}x): {desc}")
    print()

    print("--- Selection pressure (feed into dispatch/compact/orient) ---")
    for sp in soul["selection_pressure"]:
        print(f"  → {sp}")
    print()

    # Level analysis
    print("--- Level distribution ---")
    print(f"  Good levels: {soul['good_levels']}")
    print(f"  Bad levels:  {soul['bad_levels']}")


def orient_summary(soul: dict):
    """Print orient-compatible one-liner."""
    print(
        f"  Human impact: {soul['good_pct']}% GOOD / {soul['bad_pct']}% BAD / "
        f"{soul['neutral_pct']}% NEUTRAL | "
        f"benefit ratio {soul['human_benefit_ratio']}x (target >3.0x)"
    )
    ci = soul.get("benefit_ratio_ci")
    if isinstance(ci, dict) and not ci.get("significant"):
        print(f"    → CI [{ci['lower']}x, {ci['upper']}x] spans 1.0 — ratio NOT significant")
    if soul["selection_pressure"]:
        for sp in soul["selection_pressure"][:2]:
            print(f"    → {sp}")


def main():
    parser = argparse.ArgumentParser(description="Human impact extractor + soul distillation")
    parser.add_argument("--lessons", action="store_true", help="Scan lessons only")
    parser.add_argument("--soul", action="store_true", help="Soul extraction only")
    parser.add_argument("--orient", action="store_true", help="Orient-compatible summary")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    results = scan_lessons()
    soul = extract_soul(results)

    if args.orient:
        orient_summary(soul)
    elif args.soul:
        if args.json:
            print(json.dumps(soul, indent=2))
        else:
            print("=== SOUL EXTRACTION ===\n")
            for sp in soul["selection_pressure"]:
                print(f"  → {sp}")
            print(f"\n  Human benefit ratio: {soul['human_benefit_ratio']}x")
            print(f"  Good: {soul['good_count']} | Bad: {soul['bad_count']} | Neutral: {soul['neutral_count']}")
    else:
        print_report(results, soul, json_mode=args.json)


if __name__ == "__main__":
    main()
