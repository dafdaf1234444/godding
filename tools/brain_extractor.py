#!/usr/bin/env python3
"""brain_extractor.py — Cognitive architecture extractor for the swarm.

SIG-108: "swarm soul and brain extractor, swarm alan turing"

Complement to human_impact.py (soul = evaluative patterns / good-bad).
Brain = cognitive architecture: how the swarm thinks, decides, processes.

Scans lessons, principles, tools and extracts:
  REASONING TYPES  — what cognitive operations appear (induction, deduction,
                     abduction, analogy, falsification, measurement, synthesis)
  DECISION PATTERNS — how choices are made (threshold, UCB1, scoring, voting)
  INFORMATION FLOW  — citation topology as neural architecture
  COGNITIVE BIASES  — systematic errors (confirmation, self-reference, anchoring)
  MEMORY ARCHITECTURE — short/long/working memory structure
  PROCESSING MODES   — orient→act→compress as cognitive cycle

The "brain" is the extracted pattern of HOW the swarm thinks — complementing
the soul's pattern of WHAT the swarm values.

Usage:
    python3 tools/brain_extractor.py              # full brain scan
    python3 tools/brain_extractor.py --orient     # orient-compatible summary
    python3 tools/brain_extractor.py --json       # machine-readable output
    python3 tools/brain_extractor.py --compare    # brain vs soul comparison

External: Kahneman & Tversky (1979) dual-process theory; Marr (1982) 3 levels
  of analysis (computational/algorithmic/implementational); Turing (1950)
  imitation game criteria for machine intelligence.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lesson_header import parse_domain_field  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
PRINCIPLES_FILE = REPO_ROOT / "memory" / "PRINCIPLES.md"
TOOLS_DIR = REPO_ROOT / "tools"

# ---------------------------------------------------------------------------
# Cognitive pattern detectors
# ---------------------------------------------------------------------------

REASONING_TYPES = {
    "induction": {
        "desc": "Generalizing from specific observations to broader rules",
        "patterns": [
            r"(?i)\b(pattern|trend|observed|empiric|n=\d+|sample|data)\b.*\b(suggest|indicate|show|imply)\b",
            r"(?i)\b(general|universal|always|every)\b.*\b(from|based on|derived)\b.*\b(observation|data|case)\b",
        ],
    },
    "deduction": {
        "desc": "Applying general rules to specific cases",
        "patterns": [
            r"(?i)\b(therefore|thus|hence|implies|follows|entails|must be)\b",
            r"(?i)\b(if|given|since|because)\b.*\b(then|therefore|must)\b",
        ],
    },
    "abduction": {
        "desc": "Inference to best explanation",
        "patterns": [
            r"(?i)\b(best\s+explanation|likely\s+cause|root\s+cause|hypothesis|diagnos)\b",
            r"(?i)\b(explains?\s+why|accounts?\s+for|most\s+likely)\b",
        ],
    },
    "analogy": {
        "desc": "Structural mapping between domains (ISO)",
        "patterns": [
            r"(?i)\b(ISO-\d+|isomorph|analogous|maps?\s+to|corresponds?\s+to|similar\s+to)\b",
            r"(?i)\b(like|just\s+as|same\s+pattern|cross-domain)\b.*\b(in|across|between)\b",
        ],
    },
    "falsification": {
        "desc": "Testing by attempting to disprove",
        "patterns": [
            r"(?i)\b(FALSIF|disprove|refute|counter-?example|fails?\s+if)\b",
            r"(?i)\b(FALSIFIED|CONFIRMED|null\s+result|reject\s+H)\b",
        ],
    },
    "measurement": {
        "desc": "Quantitative observation and comparison",
        "patterns": [
            r"(?i)\b\d+(\.\d+)?[%x]\b",
            r"(?i)\b(measured|count|rate|ratio|metric|score|baseline)\b",
        ],
    },
    "synthesis": {
        "desc": "Combining multiple inputs into novel output",
        "patterns": [
            r"(?i)\b(combin|integrat|merg|synthes|unif|reconcil)\b.*\b(multiple|several|different|diverse)\b",
            r"(?i)\b(L3|L4|L5)\b.*\b(architecture|strategy|paradigm)\b",
        ],
    },
    "self_reflection": {
        "desc": "Reasoning about own reasoning process",
        "patterns": [
            r"(?i)\b(meta-|self-model|self-knowledge|introspect|own\s+process)\b",
            r"(?i)\b(about\s+itself|its\s+own|self-referent|recursive\s+self)\b",
        ],
    },
}

DECISION_PATTERNS = {
    "threshold": {
        "desc": "Binary decision at a numeric cutoff",
        "patterns": [
            r"(?i)\b(threshold|cutoff|limit|cap|ceiling|floor)\b.*\b(\d+|≥|≤|>|<)\b",
            r"(?i)\b(if|when)\b.*\b(exceeds?|below|above|reaches?)\b.*\b\d+\b",
        ],
    },
    "scoring": {
        "desc": "Multi-criteria weighted scoring",
        "patterns": [
            r"(?i)\b(score|weight|rank|priority|tier)\b.*\b(\d+(\.\d+)?|highest|lowest)\b",
            r"(?i)\b(UCB1|Sharpe|proxy-K|composite|Gini)\b",
        ],
    },
    "evidence_routing": {
        "desc": "Decision driven by evidence classification",
        "patterns": [
            r"(?i)\b(evidence|data|result)\b.*\b(shows?|suggests?|confirms?|falsif)\b.*\b(therefore|so|thus)\b",
            r"(?i)\b(CONFIRMED|FALSIFIED|MEASURED|TESTED)\b",
        ],
    },
    "selection_pressure": {
        "desc": "Evolutionary selection among alternatives",
        "patterns": [
            r"(?i)\b(select|evolve|compet|survive|fittest|yield|dispatch)\b",
            r"(?i)\b(variant|candidate|alternative)\b.*\b(chosen|selected|best|won)\b",
        ],
    },
    "consensus": {
        "desc": "Aggregation across multiple opinions/nodes",
        "patterns": [
            r"(?i)\b(council|consensus|vote|agree|disagree|quorum)\b",
            r"(?i)\b(multiple|several)\b.*\b(nodes?|sessions?|agents?)\b.*\b(agree|converge)\b",
        ],
    },
}

COGNITIVE_BIASES = {
    "confirmation_bias": {
        "desc": "Preferring evidence that confirms existing beliefs",
        "patterns": [
            r"(?i)\b(confirm|confirmation)\b.*\b(bias|attractor|only|dominant)\b",
            r"(?i)\b(never\s+challeng|unchallenged|axiom-stuck)\b",
        ],
    },
    "self_reference_loop": {
        "desc": "Reasoning about self using self-generated data",
        "patterns": [
            r"(?i)\b(self-referent|circular|tautolog|unfalsif)\b",
            r"(?i)\b(meta-meta|recursive\s+recursive|measures?\s+itself)\b",
        ],
    },
    "anchoring": {
        "desc": "Over-relying on first measurement or early estimate",
        "patterns": [
            r"(?i)\b(anchor|baseline\s+lock|initial\s+estimate|first\s+measurement)\b",
            r"(?i)\b(sticky|persist|unchanged)\b.*\b(despite|even though|although)\b.*\b(new|later|updated)\b",
        ],
    },
    "goodhart_drift": {
        "desc": "Optimizing metric instead of underlying goal",
        "patterns": [
            r"(?i)\b(Goodhart|metric\s+gaming|optimiz.*wrong|proxy|surrogate)\b.*\b(instead|rather|not)\b",
            r"(?i)\b(measure\s+becomes|target\s+becomes)\b.*\b(not\s+what)\b",
        ],
    },
    "complexity_creep": {
        "desc": "Adding unnecessary mechanism/abstraction",
        "patterns": [
            r"(?i)\b(over-engineer|unnecessar|bloat|too\s+complex)\b",
            r"(?i)\b(added|built|created)\b.*\b(never\s+used|0\s+usage|abandoned|unused)\b",
        ],
    },
}


def _match_patterns(text: str, categories: dict) -> dict[str, int]:
    """Count hits per category in text."""
    hits = {}
    for name, info in categories.items():
        count = 0
        for pat in info["patterns"]:
            count += len(re.findall(pat, text, re.MULTILINE))
        if count > 0:
            hits[name] = count
    return hits


def scan_lesson_brain(path: Path) -> dict:
    """Extract cognitive patterns from a single lesson."""
    text = path.read_text(encoding="utf-8", errors="replace")
    header = "\n".join(text.split("\n")[:10])
    domains = parse_domain_field(header)
    domain = domains[0] if domains else "unknown"

    return {
        "id": path.stem,
        "domain": domain,
        "reasoning": _match_patterns(text, REASONING_TYPES),
        "decisions": _match_patterns(text, DECISION_PATTERNS),
        "biases": _match_patterns(text, COGNITIVE_BIASES),
    }


def scan_all_lessons() -> list[dict]:
    """Scan all lessons for cognitive patterns."""
    results = []
    if not LESSONS_DIR.exists():
        return results
    for path in sorted(LESSONS_DIR.glob("L-*.md")):
        try:
            results.append(scan_lesson_brain(path))
        except Exception as e:
            print(f"  WARN: {path.name}: {e}", file=sys.stderr)
    return results


def extract_brain(results: list[dict]) -> dict:
    """Extract the cognitive architecture — the 'brain' — from scan results.

    The brain is the distilled pattern of HOW the swarm thinks.
    Complements the soul (WHAT the swarm values).
    """
    n = len(results)
    if n == 0:
        return {"total": 0, "error": "no lessons found"}

    # Aggregate reasoning type frequencies
    reasoning_totals = {}
    for r in results:
        for rtype, count in r["reasoning"].items():
            reasoning_totals[rtype] = reasoning_totals.get(rtype, 0) + count

    # Aggregate decision pattern frequencies
    decision_totals = {}
    for r in results:
        for dtype, count in r["decisions"].items():
            decision_totals[dtype] = decision_totals.get(dtype, 0) + count

    # Aggregate bias frequencies
    bias_totals = {}
    for r in results:
        for btype, count in r["biases"].items():
            bias_totals[btype] = bias_totals.get(btype, 0) + count

    # Per-domain cognitive profiles
    domain_profiles = {}
    for r in results:
        d = r["domain"]
        if d not in domain_profiles:
            domain_profiles[d] = {"reasoning": {}, "decisions": {}, "biases": {}, "count": 0}
        domain_profiles[d]["count"] += 1
        for rtype, count in r["reasoning"].items():
            domain_profiles[d]["reasoning"][rtype] = domain_profiles[d]["reasoning"].get(rtype, 0) + count
        for dtype, count in r["decisions"].items():
            domain_profiles[d]["decisions"][dtype] = domain_profiles[d]["decisions"].get(dtype, 0) + count
        for btype, count in r["biases"].items():
            domain_profiles[d]["biases"][btype] = domain_profiles[d]["biases"].get(btype, 0) + count

    # Dominant reasoning mode per domain
    domain_dominant_reasoning = {}
    for d, prof in domain_profiles.items():
        if prof["reasoning"]:
            top = max(prof["reasoning"].items(), key=lambda x: x[1])
            domain_dominant_reasoning[d] = top[0]

    # Reasoning diversity (how many types used per lesson on average)
    reasoning_diversity = []
    for r in results:
        reasoning_diversity.append(len(r["reasoning"]))
    avg_diversity = round(sum(reasoning_diversity) / max(n, 1), 2)

    # Bias-to-reasoning ratio (cognitive health metric)
    total_reasoning = sum(reasoning_totals.values())
    total_bias = sum(bias_totals.values())
    bias_ratio = round(total_bias / max(total_reasoning, 1), 3)

    # System 1 vs System 2 (Kahneman)
    # System 1: fast/automatic = measurement, analogy, threshold
    # System 2: slow/deliberate = falsification, synthesis, evidence_routing
    system1_types = {"measurement", "analogy", "induction"}
    system2_types = {"falsification", "synthesis", "deduction", "abduction"}
    s1_total = sum(reasoning_totals.get(t, 0) for t in system1_types)
    s2_total = sum(reasoning_totals.get(t, 0) for t in system2_types)
    s1_s2_ratio = round(s1_total / max(s2_total, 1), 2)

    # Marr's levels: computational (what) vs algorithmic (how) vs implementational (with what)
    # computational = synthesis, abduction (goals/functions)
    # algorithmic = deduction, induction, scoring (procedures)
    # implementational = measurement, threshold (concrete mechanisms)
    marr_computational = sum(reasoning_totals.get(t, 0) for t in ["synthesis", "abduction"])
    marr_algorithmic = sum(reasoning_totals.get(t, 0) for t in ["deduction", "induction", "analogy"])
    marr_implementational = sum(reasoning_totals.get(t, 0) for t in ["measurement", "self_reflection"])
    marr_total = marr_computational + marr_algorithmic + marr_implementational
    marr_balance = {
        "computational_pct": round(100 * marr_computational / max(marr_total, 1), 1),
        "algorithmic_pct": round(100 * marr_algorithmic / max(marr_total, 1), 1),
        "implementational_pct": round(100 * marr_implementational / max(marr_total, 1), 1),
    }

    brain = {
        "total_lessons": n,
        "reasoning_types": dict(sorted(reasoning_totals.items(), key=lambda x: -x[1])),
        "decision_patterns": dict(sorted(decision_totals.items(), key=lambda x: -x[1])),
        "cognitive_biases": dict(sorted(bias_totals.items(), key=lambda x: -x[1])),
        "reasoning_diversity_avg": avg_diversity,
        "bias_to_reasoning_ratio": bias_ratio,
        "system1_vs_system2": {
            "s1_total": s1_total,
            "s2_total": s2_total,
            "ratio": s1_s2_ratio,
            "interpretation": (
                "measurement-heavy (System 1 dominant)" if s1_s2_ratio > 2.0
                else "deliberation-heavy (System 2 dominant)" if s1_s2_ratio < 0.5
                else "balanced" if 0.8 <= s1_s2_ratio <= 1.25
                else "slight System 1 bias" if s1_s2_ratio > 1.0
                else "slight System 2 bias"
            ),
        },
        "marr_levels": marr_balance,
        "domain_dominant_reasoning": domain_dominant_reasoning,
        # Cognitive health indicators
        "health": {
            "bias_ratio": bias_ratio,
            "bias_health": (
                "HEALTHY" if bias_ratio < 0.1
                else "CAUTION" if bias_ratio < 0.2
                else "WARNING — high bias load"
            ),
            "top_bias": max(bias_totals.items(), key=lambda x: x[1])[0] if bias_totals else "none",
            "diversity_health": (
                "RICH" if avg_diversity >= 3.0
                else "ADEQUATE" if avg_diversity >= 2.0
                else "NARROW — cognitive monoculture risk"
            ),
        },
        # Turing-relevant: self-modeling capacity
        "self_modeling": {
            "self_reflection_count": reasoning_totals.get("self_reflection", 0),
            "self_reflection_pct": round(
                100 * reasoning_totals.get("self_reflection", 0) / max(total_reasoning, 1), 1
            ),
            "self_reference_bias": bias_totals.get("self_reference_loop", 0),
        },
        # Selection pressures (feed into dispatch/orient)
        "selection_pressure": [],
    }

    # Derive selection pressures
    if s1_s2_ratio > 2.0:
        brain["selection_pressure"].append(
            f"IMBALANCE: System 1/System 2 ratio = {s1_s2_ratio}x. "
            "Swarm measures more than it reasons. Dispatch should weight "
            "falsification and synthesis tasks higher."
        )

    if bias_ratio > 0.15:
        top_bias = brain["health"]["top_bias"]
        brain["selection_pressure"].append(
            f"BIAS WARNING: bias/reasoning ratio = {bias_ratio}. "
            f"Dominant bias: {top_bias}. "
            "Orient should flag lessons with high bias load for review."
        )

    if avg_diversity < 2.0:
        brain["selection_pressure"].append(
            f"MONOCULTURE: avg reasoning diversity = {avg_diversity} types/lesson. "
            "Lessons use too few cognitive modes. Multi-type reasoning produces "
            "more robust conclusions."
        )

    brain["selection_pressure"].append(
        f"BRAIN METRIC: {len(reasoning_totals)} reasoning types active, "
        f"S1/S2 = {s1_s2_ratio}x, bias ratio = {bias_ratio}. "
        f"Marr: {marr_balance['computational_pct']}% computational / "
        f"{marr_balance['algorithmic_pct']}% algorithmic / "
        f"{marr_balance['implementational_pct']}% implementational."
    )

    return brain


def compare_brain_soul(brain: dict) -> dict:
    """Compare brain (cognitive) with soul (evaluative) findings.

    The brain-soul comparison reveals whether the swarm thinks well
    about things it values, and values things it thinks well about.
    """
    # Import soul data
    try:
        from human_impact import scan_lessons, extract_soul
        soul_results = scan_lessons()
        soul = extract_soul(soul_results)
    except Exception as e:
        return {"error": f"Could not load soul data: {e}"}

    comparison = {
        "soul_benefit_ratio": soul.get("human_benefit_ratio", 0),
        "brain_bias_ratio": brain.get("bias_to_reasoning_ratio", 0),
        "brain_s1_s2": brain.get("system1_vs_system2", {}).get("ratio", 0),
        "soul_good_pct": soul.get("good_pct", 0),
        "brain_diversity": brain.get("reasoning_diversity_avg", 0),
    }

    # Diagnosis: does thinking quality correlate with human benefit?
    diagnoses = []

    if comparison["brain_bias_ratio"] > 0.15 and comparison["soul_benefit_ratio"] < 2.0:
        diagnoses.append(
            "ALIGNED PROBLEM: high bias AND low human benefit — "
            "cognitive biases may be causing poor-for-humans output"
        )

    if comparison["brain_s1_s2"] > 2.0 and comparison["soul_good_pct"] < 25:
        diagnoses.append(
            "MEASUREMENT TRAP: heavy System 1 (measurement) AND low human-good — "
            "the swarm is counting instead of reasoning about what matters"
        )

    if comparison["brain_diversity"] >= 3.0 and comparison["soul_benefit_ratio"] >= 2.0:
        diagnoses.append(
            "HEALTHY ALIGNMENT: diverse reasoning AND good human benefit — "
            "cognitive richness produces human-valuable output"
        )

    if comparison["brain_bias_ratio"] < 0.1 and comparison["soul_benefit_ratio"] < 1.5:
        diagnoses.append(
            "PARADOX: low bias but low human benefit — "
            "clear thinking but about the wrong things (topic selection problem)"
        )

    comparison["diagnoses"] = diagnoses
    return comparison


def print_brain_report(brain: dict, json_mode: bool = False):
    """Print human-readable or JSON brain report."""
    if json_mode:
        print(json.dumps(brain, indent=2))
        return

    print(f"=== BRAIN EXTRACTION | {brain['total_lessons']} lessons scanned ===\n")

    print("--- Reasoning Types (how the swarm thinks) ---")
    for rtype, count in brain["reasoning_types"].items():
        desc = REASONING_TYPES[rtype]["desc"]
        print(f"  {rtype:20s} {count:5d} hits — {desc}")
    print(f"\n  Reasoning diversity: {brain['reasoning_diversity_avg']} types/lesson avg")

    print(f"\n--- System 1 vs System 2 (Kahneman) ---")
    s = brain["system1_vs_system2"]
    print(f"  System 1 (fast/automatic): {s['s1_total']} hits")
    print(f"  System 2 (slow/deliberate): {s['s2_total']} hits")
    print(f"  Ratio: {s['ratio']}x — {s['interpretation']}")

    print(f"\n--- Marr's Levels of Analysis ---")
    m = brain["marr_levels"]
    print(f"  Computational (what/why):   {m['computational_pct']}%")
    print(f"  Algorithmic (how):          {m['algorithmic_pct']}%")
    print(f"  Implementational (with what): {m['implementational_pct']}%")

    print(f"\n--- Decision Patterns (how the swarm decides) ---")
    for dtype, count in brain["decision_patterns"].items():
        desc = DECISION_PATTERNS[dtype]["desc"]
        print(f"  {dtype:20s} {count:5d} hits — {desc}")

    print(f"\n--- Cognitive Biases (systematic errors) ---")
    for btype, count in brain["cognitive_biases"].items():
        desc = COGNITIVE_BIASES[btype]["desc"]
        print(f"  {btype:20s} {count:5d} hits — {desc}")

    print(f"\n--- Cognitive Health ---")
    h = brain["health"]
    print(f"  Bias/reasoning ratio: {h['bias_ratio']} — {h['bias_health']}")
    print(f"  Reasoning diversity:  {brain['reasoning_diversity_avg']} — {h['diversity_health']}")
    print(f"  Top bias: {h['top_bias']}")

    sm = brain["self_modeling"]
    print(f"\n--- Self-Modeling (Turing relevance) ---")
    print(f"  Self-reflection hits: {sm['self_reflection_count']} ({sm['self_reflection_pct']}% of reasoning)")
    print(f"  Self-reference bias:  {sm['self_reference_bias']} (error count)")

    print(f"\n--- Selection Pressure (feed into dispatch/orient) ---")
    for sp in brain["selection_pressure"]:
        print(f"  -> {sp}")


def orient_summary(brain: dict):
    """Print orient-compatible one-liner."""
    s = brain["system1_vs_system2"]
    h = brain["health"]
    print(
        f"  Brain: S1/S2={s['ratio']}x ({s['interpretation']}) | "
        f"bias={h['bias_ratio']} ({h['bias_health']}) | "
        f"diversity={brain['reasoning_diversity_avg']} ({h['diversity_health']})"
    )
    if brain["selection_pressure"]:
        for sp in brain["selection_pressure"][:1]:
            print(f"    -> {sp}")


def main():
    parser = argparse.ArgumentParser(description="Brain extractor — cognitive architecture analysis")
    parser.add_argument("--orient", action="store_true", help="Orient-compatible summary")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--compare", action="store_true", help="Brain vs soul comparison")
    args = parser.parse_args()

    results = scan_all_lessons()
    brain = extract_brain(results)

    if args.compare:
        comparison = compare_brain_soul(brain)
        if args.json:
            print(json.dumps({"brain": brain, "comparison": comparison}, indent=2))
        else:
            print_brain_report(brain)
            print(f"\n=== BRAIN vs SOUL ===\n")
            print(f"  Soul benefit ratio: {comparison.get('soul_benefit_ratio', '?')}x")
            print(f"  Brain bias ratio:   {comparison.get('brain_bias_ratio', '?')}")
            print(f"  Brain S1/S2:        {comparison.get('brain_s1_s2', '?')}x")
            for d in comparison.get("diagnoses", []):
                print(f"  -> {d}")
    elif args.orient:
        orient_summary(brain)
    else:
        print_brain_report(brain, json_mode=args.json)


if __name__ == "__main__":
    main()
