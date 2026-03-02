#!/usr/bin/env python3
"""F-QC3: Cross-domain lesson redundancy matrix.

Identifies domain pairs sharing near-duplicate lessons.
Compares against ISOMORPHISM-ATLAS to test whether ISO-linked
domains produce more redundant knowledge.
"""

import os, re, json, sys
from pathlib import Path
from collections import defaultdict, Counter
from itertools import combinations

LESSONS_DIR = Path("memory/lessons")
ATLAS_PATH = Path("domains/ISOMORPHISM-ATLAS.md")
LANES_PATH = Path("tasks/SWARM-LANES.md")
DOMAINS_DIR = Path("domains")

# Frontier prefix → domain mapping
FRONTIER_DOMAIN = {
    "F-AI": "ai", "F-BRN": "brain", "F-CAT": "catastrophic-risks",
    "F-CC": "claude-code", "F-COMP": "competitions", "F-CON": "conflict",
    "F-CT": "control-theory", "F-CRYPTO": "cryptocurrency",
    "F-CRYPT": "cryptography", "F-DS": "distributed-systems",
    "F-DRM": "dream", "F-ECO": "economy", "F-EMP": "empathy",
    "F-EVAL": "evaluation", "F-EVO": "evolution", "F-EXP": "expert-swarm",
    "F-FAR": "farming", "F-FIN": "finance", "F-FLD": "fluid-dynamics",
    "F-FRAC": "fractals", "F-GAME": "game-theory", "F-GAM": "gaming",
    "F-GOV": "governance", "F-GT": "graph-theory", "F-GUESS": "guesstimates",
    "F-HLT": "health", "F-HLP": "helper-swarm", "F-HIST": "history",
    "F-HS": "human-systems", "F-IS": "information-science",
    "F-LNG": "linguistics", "F-META": "meta", "F-NK": "nk-complexity",
    "F-OR": "operations-research", "F-PHYS": "physics",
    "F-PE": "protocol-engineering", "F-PSY": "psychology",
    "F-QC": "quality", "F-SEC": "security", "F-IC": "security",
    "F-SM": "social-media", "F-STAT": "statistics",
    "F-SP": "stochastic-processes", "F-STR": "strategy",
}

# Domain keyword seeds for classification
DOMAIN_KEYWORDS = {
    "ai": ["llm", "model", "neural", "ai", "machine learning", "claude", "gpt", "transformer"],
    "brain": ["brain", "neuroscience", "cortical", "neuron", "cognitive"],
    "catastrophic-risks": ["catastrophic", "fmea", "failure mode", "risk registry"],
    "economy": ["economy", "proxy-k", "sharpe", "production velocity", "throughput"],
    "evolution": ["evolution", "mutation", "selection pressure", "fitness", "genetic"],
    "expert-swarm": ["expert", "dispatch", "domex", "domain expert"],
    "fluid-dynamics": ["reynolds", "laminar", "turbulent", "fluid"],
    "game-theory": ["game theory", "nash", "prisoner", "payoff"],
    "gaming": ["roguelike", "productive failure", "permadeath"],
    "governance": ["governance", "council", "colony", "voting"],
    "graph-theory": ["graph", "dependency", "hub", "edge", "node"],
    "linguistics": ["linguistic", "language", "syntax", "semantic", "morpheme"],
    "meta": ["meta", "self-model", "contract", "self-referential", "epistemolog"],
    "nk-complexity": ["nk", "citation density", "k_avg", "kauffman", "fitness landscape"],
    "quality": ["quality", "redundanc", "duplicate", "bullshit", "staleness"],
    "security": ["security", "trust tier", "contamination", "bundle integrity"],
    "statistics": ["statistics", "regression", "correlation", "p-value", "confidence interval"],
    "stochastic-processes": ["hawkes", "poisson", "markov", "viterbi", "hmm", "stochastic"],
    "strategy": ["strategy", "priority policy", "value density", "backtest"],
    "control-theory": ["pid", "control", "feedback loop", "anti-windup"],
    "information-science": ["information", "entropy", "compression", "mdl"],
}


def load_lessons():
    """Load all lessons, return list of (id, domain_hints, words, raw_text)."""
    lessons = []
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        text = f.read_text(errors="replace")
        lid = f.stem  # L-NNN

        # Extract Domain: header
        domains = set()
        m = re.search(r"^Domain:\s*(.+)", text, re.MULTILINE)
        if m:
            domains.add(m.group(1).strip().lower())

        # Extract Frontier: header
        m = re.search(r"^Frontier:\s*(.+)", text, re.MULTILINE)
        if m:
            for fref in re.findall(r"F-[A-Z]+\d*", m.group(1)):
                prefix = re.match(r"F-[A-Z]+", fref).group()
                if prefix in FRONTIER_DOMAIN:
                    domains.add(FRONTIER_DOMAIN[prefix])

        # Keyword classification (only if no domain yet)
        lower_text = text.lower()
        if not domains:
            scores = {}
            for domain, keywords in DOMAIN_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in lower_text)
                if score >= 2:
                    scores[domain] = score
            if scores:
                top = max(scores.values())
                for d, s in scores.items():
                    if s >= top:
                        domains.add(d)

        # Tokenize for similarity
        words = set(re.findall(r"[a-z]{3,}", lower_text))
        # Remove common stop words
        stops = {"the", "and", "for", "that", "this", "with", "from", "are",
                 "was", "were", "has", "have", "had", "not", "but", "can",
                 "will", "more", "than", "each", "when", "which", "their",
                 "its", "also", "been", "would", "could", "should", "into",
                 "about", "between", "only", "over", "after", "before",
                 "session", "lesson", "swarm", "domain", "frontier"}
        words -= stops

        lessons.append((lid, domains, words, text))
    return lessons


def jaccard(a, b):
    """Jaccard similarity between two word sets."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def extract_atlas_pairs():
    """Extract domain pairs from ISOMORPHISM-ATLAS entries."""
    if not ATLAS_PATH.exists():
        return set()
    text = ATLAS_PATH.read_text(errors="replace")

    pairs = set()
    # Split by ISO entries
    entries = re.split(r"### ISO-\d+:", text)
    for entry in entries[1:]:  # skip preamble
        # Find domain column entries
        domains_in_entry = set()
        for line in entry.split("\n"):
            if line.startswith("|") and not line.startswith("|-"):
                cols = [c.strip() for c in line.split("|")]
                if len(cols) >= 3:
                    domain_cell = cols[1].lower()
                    # Map atlas domain names to our domain dirs
                    for dname in DOMAIN_KEYWORDS:
                        if dname.replace("-", " ") in domain_cell or dname in domain_cell:
                            domains_in_entry.add(dname)
                    # Special mappings
                    if "swarm" in domain_cell:
                        domains_in_entry.add("meta")
                    if "evolution" in domain_cell:
                        domains_in_entry.add("evolution")
                    if "economics" in domain_cell or "market" in domain_cell:
                        domains_in_entry.add("economy")
                    if "physics" in domain_cell:
                        domains_in_entry.add("stochastic-processes")
                    if "neuroscience" in domain_cell or "brain" in domain_cell:
                        domains_in_entry.add("brain")
                    if "machine learning" in domain_cell:
                        domains_in_entry.add("ai")
                    if "ecology" in domain_cell:
                        domains_in_entry.add("evolution")
                    if "governance" in domain_cell or "political" in domain_cell:
                        domains_in_entry.add("governance")
                    if "linguistics" in domain_cell or "language" in domain_cell:
                        domains_in_entry.add("linguistics")
                    if "game" in domain_cell:
                        domains_in_entry.add("game-theory")
                    if "information" in domain_cell:
                        domains_in_entry.add("information-science")

        # Generate pairs
        for a, b in combinations(sorted(domains_in_entry), 2):
            pairs.add((a, b))

    return pairs


def main():
    lessons = load_lessons()
    atlas_pairs = extract_atlas_pairs()

    # Domain assignment stats
    classified = sum(1 for _, d, _, _ in lessons if d)
    print(f"=== F-QC3: CROSS-DOMAIN REDUNDANCY MATRIX ===")
    print(f"Lessons: {len(lessons)} | Classified: {classified} ({100*classified/len(lessons):.1f}%)")
    print(f"Atlas domain pairs: {len(atlas_pairs)}")

    # Group lessons by domain
    domain_lessons = defaultdict(list)
    for lid, domains, words, text in lessons:
        for d in domains:
            domain_lessons[d].append((lid, words, text))

    active_domains = sorted(d for d in domain_lessons if len(domain_lessons[d]) >= 2)
    print(f"Domains with >=2 lessons: {len(active_domains)}")
    print()

    # Compute cross-domain redundancy
    THRESHOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 0.25  # F-QC3 default
    redundancy_matrix = {}
    pair_examples = {}

    for d1, d2 in combinations(active_domains, 2):
        dupes = []
        for lid1, w1, t1 in domain_lessons[d1]:
            for lid2, w2, t2 in domain_lessons[d2]:
                if lid1 == lid2:
                    continue  # same lesson assigned to both domains
                sim = jaccard(w1, w2)
                if sim >= THRESHOLD:
                    dupes.append((lid1, lid2, sim))

        if dupes:
            pair_key = f"{d1}|{d2}"
            total_pairs = len(domain_lessons[d1]) * len(domain_lessons[d2])
            redundancy_rate = len(dupes) / total_pairs if total_pairs else 0
            redundancy_matrix[pair_key] = {
                "count": len(dupes),
                "total_pairs": total_pairs,
                "rate": redundancy_rate,
                "max_sim": max(s for _, _, s in dupes),
                "avg_sim": sum(s for _, _, s in dupes) / len(dupes),
            }
            # Keep top 3 examples
            dupes.sort(key=lambda x: -x[2])
            pair_examples[pair_key] = [(l1, l2, round(s, 3)) for l1, l2, s in dupes[:3]]

    # Rank by redundancy rate
    ranked = sorted(redundancy_matrix.items(), key=lambda x: -x[1]["rate"])

    print("--- Top 15 redundant domain pairs ---")
    print(f"{'Pair':<45} {'Count':>5} {'Rate':>7} {'MaxSim':>7} {'Atlas':>5}")
    for pair_key, stats in ranked[:15]:
        d1, d2 = pair_key.split("|")
        in_atlas = "YES" if (d1, d2) in atlas_pairs or (d2, d1) in atlas_pairs else "no"
        print(f"  {d1} × {d2:<20} {stats['count']:>5} {stats['rate']:>6.1%} {stats['max_sim']:>7.3f} {in_atlas:>5}")

    # Compare atlas vs non-atlas
    atlas_rates = []
    non_atlas_rates = []
    for pair_key, stats in redundancy_matrix.items():
        d1, d2 = pair_key.split("|")
        if (d1, d2) in atlas_pairs or (d2, d1) in atlas_pairs:
            atlas_rates.append(stats["rate"])
        else:
            non_atlas_rates.append(stats["rate"])

    print()
    print("--- Atlas vs non-Atlas redundancy ---")
    if atlas_rates:
        avg_atlas = sum(atlas_rates) / len(atlas_rates)
        print(f"  Atlas pairs:     n={len(atlas_rates)}, avg rate={avg_atlas:.4f}")
    if non_atlas_rates:
        avg_non = sum(non_atlas_rates) / len(non_atlas_rates)
        print(f"  Non-atlas pairs: n={len(non_atlas_rates)}, avg rate={avg_non:.4f}")
    if atlas_rates and non_atlas_rates:
        ratio = avg_atlas / avg_non if avg_non > 0 else float("inf")
        print(f"  Ratio: {ratio:.2f}x")

    # Overall stats
    all_rates = [s["rate"] for s in redundancy_matrix.values()]
    total_cross_dupes = sum(s["count"] for s in redundancy_matrix.values())
    total_cross_pairs = sum(s["total_pairs"] for s in redundancy_matrix.values())
    overall_rate = total_cross_dupes / total_cross_pairs if total_cross_pairs else 0

    print()
    print("--- Overall ---")
    print(f"  Total cross-domain near-duplicates: {total_cross_dupes}")
    print(f"  Total cross-domain pairs checked: {total_cross_pairs}")
    print(f"  Overall cross-domain redundancy: {overall_rate:.2%}")
    print(f"  Redundant domain pairs: {len(redundancy_matrix)}")
    print(f"  Non-redundant domain pairs: {len(list(combinations(active_domains, 2))) - len(redundancy_matrix)}")

    # Top examples
    print()
    print("--- Top examples (highest similarity) ---")
    all_examples = []
    for pair_key, exs in pair_examples.items():
        for lid1, lid2, sim in exs:
            all_examples.append((pair_key, lid1, lid2, sim))
    all_examples.sort(key=lambda x: -x[3])
    for pair_key, lid1, lid2, sim in all_examples[:10]:
        print(f"  {lid1} × {lid2} (sim={sim:.3f}) [{pair_key}]")

    # Domain assignment distribution
    print()
    print("--- Domain lesson counts (top 15) ---")
    for d in sorted(domain_lessons, key=lambda x: -len(domain_lessons[x]))[:15]:
        print(f"  {d:<25} {len(domain_lessons[d]):>4} lessons")

    # F-QC3 hypothesis test
    print()
    print("--- F-QC3 Hypothesis Test ---")
    high_pairs = [(k, v) for k, v in ranked if v["rate"] >= 0.05]
    print(f"  High-redundancy pairs (rate>=5%): {len(high_pairs)}")
    expected_pairs = ["evolution", "meta", "brain", "ai"]
    found_expected = 0
    for pair_key, _ in ranked[:10]:
        d1, d2 = pair_key.split("|")
        if d1 in expected_pairs or d2 in expected_pairs:
            found_expected += 1
    print(f"  Expected domains in top-10: {found_expected}/10")
    if atlas_rates and non_atlas_rates:
        print(f"  Atlas ratio: {ratio:.2f}x (target: >2x)")
        verdict = "CONFIRMED" if ratio >= 2.0 else "PARTIALLY CONFIRMED" if ratio >= 1.5 else "REFUTED"
        print(f"  Verdict: {verdict}")

    # Save experiment JSON
    result = {
        "frontier": "F-QC3",
        "session": "S381",
        "method": "Jaccard word-set similarity, threshold=0.25, keyword domain classification",
        "total_lessons": len(lessons),
        "classified_lessons": classified,
        "classification_rate": round(classified / len(lessons), 3),
        "domains_with_lessons": len(active_domains),
        "threshold": THRESHOLD,
        "total_cross_dupes": total_cross_dupes,
        "total_cross_pairs": total_cross_pairs,
        "overall_redundancy_rate": round(overall_rate, 4),
        "redundant_domain_pairs": len(redundancy_matrix),
        "atlas_pairs_tested": len(atlas_rates),
        "atlas_avg_rate": round(avg_atlas, 4) if atlas_rates else None,
        "non_atlas_avg_rate": round(avg_non, 4) if non_atlas_rates else None,
        "atlas_ratio": round(ratio, 2) if atlas_rates and non_atlas_rates else None,
        "top_15_pairs": [
            {
                "domains": pair_key,
                "count": stats["count"],
                "rate": round(stats["rate"], 4),
                "max_sim": round(stats["max_sim"], 3),
                "in_atlas": (pair_key.split("|")[0], pair_key.split("|")[1]) in atlas_pairs
                            or (pair_key.split("|")[1], pair_key.split("|")[0]) in atlas_pairs,
                "examples": pair_examples.get(pair_key, [])[:2],
            }
            for pair_key, stats in ranked[:15]
        ],
        "domain_lesson_counts": {d: len(domain_lessons[d]) for d in active_domains},
    }

    out_path = Path("experiments/quality/f-qc3-redundancy-matrix-s381.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
