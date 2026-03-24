#!/usr/bin/env python3
"""F-PLB5 Allelopathy — Do dominant domains suppress structurally similar neighbors?

Hypothesis: After dispatching to domain A, dispatch to structurally similar domain B
is reduced in subsequent sessions (allelopathic suppression). Domains that share
isomorphisms should inhibit each other's dispatch.

Method:
  1. Extract temporal dispatch sequence from lessons.
  2. Build domain similarity matrix from ISO atlas co-occurrence.
  3. For each dispatch to domain A at time t, measure whether similar domains
     are dispatched LESS in [t+1, t+5] vs baseline.
  4. If similar domains are suppressed >20%, allelopathy is confirmed.

Cites: L-1436, L-1127, L-1604
"""
import json, re, sys
from collections import defaultdict, Counter
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"
ATLAS = ROOT / "domains" / "ISOMORPHISM-ATLAS.md"


def extract_dispatch_sequence():
    """Extract (session, domain) pairs from lessons."""
    seq = []
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        session = domain = None
        for line in text.splitlines()[:5]:
            m = re.search(r'Session:\s*S(\d+)', line)
            if m:
                session = int(m.group(1))
            m = re.search(r'Domain:\s*(\S+)', line)
            if m:
                domain = m.group(1).strip().split(',')[0].strip()
        if session and domain:
            seq.append((session, domain))
    seq.sort()
    return seq


def build_iso_similarity():
    """Build domain similarity from ISO atlas."""
    if not ATLAS.exists():
        return {}

    text = ATLAS.read_text(encoding="utf-8", errors="replace")
    # Parse ISO entries: each mentions domains
    iso_domains = defaultdict(set)
    current_iso = None
    for line in text.splitlines():
        m = re.match(r'##\s+(ISO-\d+)', line)
        if m:
            current_iso = m.group(1)
            continue
        if current_iso:
            # Look for domain mentions in the line
            domains_found = re.findall(r'\b([a-z][\w-]+)\b', line.lower())
            for d in domains_found:
                if len(d) > 3 and d not in {'the', 'and', 'for', 'this', 'that', 'with', 'from', 'not', 'but', 'are', 'was', 'has', 'have', 'been', 'more', 'will', 'can', 'than', 'like', 'each', 'when', 'them', 'into', 'some', 'only', 'also', 'very', 'just', 'where', 'most', 'after', 'over', 'such', 'other'}:
                    iso_domains[current_iso].add(d)

    # Build co-occurrence matrix
    cooccur = defaultdict(int)
    for iso, doms in iso_domains.items():
        dom_list = list(doms)
        for i in range(len(dom_list)):
            for j in range(i + 1, len(dom_list)):
                pair = tuple(sorted([dom_list[i], dom_list[j]]))
                cooccur[pair] += 1

    return cooccur


def build_domain_similarity_from_lessons():
    """Build similarity from lesson multi-domain tagging."""
    cooccur = defaultdict(int)
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines()[:5]:
            m = re.search(r'Domain:\s*(.+?)(?:\s*\||\s*$)', line)
            if m:
                domains = [d.strip() for d in m.group(1).split(',')]
                domains = [d for d in domains if d]
                for i in range(len(domains)):
                    for j in range(i + 1, len(domains)):
                        pair = tuple(sorted([domains[i], domains[j]]))
                        cooccur[pair] += 1
                break
    return cooccur


def analyze_allelopathy(sequence, cooccur, window=5):
    """Measure whether similar domains are suppressed after dispatch."""
    # Group dispatches by session
    session_domains = defaultdict(list)
    for session, domain in sequence:
        session_domains[session].append(domain)

    sessions = sorted(session_domains.keys())
    session_idx = {s: i for i, s in enumerate(sessions)}

    # For each domain, find its most similar domains
    domain_neighbors = defaultdict(set)
    for (d1, d2), count in cooccur.items():
        if count >= 2:  # at least 2 co-occurrences
            domain_neighbors[d1].add(d2)
            domain_neighbors[d2].add(d1)

    # Measure: after dispatching to domain A, how often do similar domains
    # appear in the next `window` sessions vs baseline?
    suppression_scores = []
    n_tested = 0

    # Baseline: domain frequency
    all_domains = [d for _, d in sequence]
    domain_freq = Counter(all_domains)
    total = len(all_domains)

    for i, s in enumerate(sessions):
        for dom in session_domains[s]:
            neighbors = domain_neighbors.get(dom, set())
            if not neighbors:
                continue

            # Count neighbor appearances in next `window` sessions
            after_count = 0
            after_total = 0
            for j in range(i + 1, min(i + 1 + window, len(sessions))):
                next_s = sessions[j]
                for nd in session_domains[next_s]:
                    after_total += 1
                    if nd in neighbors:
                        after_count += 1

            if after_total == 0:
                continue

            # Expected baseline for these neighbors
            expected_rate = sum(domain_freq.get(n, 0) for n in neighbors) / total

            actual_rate = after_count / after_total
            if expected_rate > 0:
                suppression = 1.0 - (actual_rate / expected_rate)
                suppression_scores.append({
                    "domain": dom,
                    "session": s,
                    "n_neighbors": len(neighbors),
                    "actual_rate": actual_rate,
                    "expected_rate": expected_rate,
                    "suppression": suppression,
                })
                n_tested += 1

    return suppression_scores, domain_neighbors


def main():
    sequence = extract_dispatch_sequence()
    cooccur = build_domain_similarity_from_lessons()

    if not cooccur:
        print("  No domain co-occurrence found. Cannot test allelopathy.")
        return

    suppression_scores, neighbors = analyze_allelopathy(sequence, cooccur)

    if not suppression_scores:
        print("  No testable domain pairs found.")
        return

    all_supp = [s["suppression"] for s in suppression_scores]
    mean_supp = mean(all_supp)
    pos_supp = sum(1 for s in all_supp if s > 0)
    neg_supp = sum(1 for s in all_supp if s < 0)

    # Per-domain averages
    domain_supp = defaultdict(list)
    for s in suppression_scores:
        domain_supp[s["domain"]].append(s["suppression"])

    domain_means = {d: mean(v) for d, v in domain_supp.items() if len(v) >= 5}
    top_allelopaths = sorted(domain_means.items(), key=lambda x: x[1], reverse=True)[:10]
    top_facilitators = sorted(domain_means.items(), key=lambda x: x[1])[:10]

    confirmed = mean_supp > 0.20

    print(f"\n  F-PLB5 Allelopathy — Domain Attention Suppression")
    print(f"  {'─' * 55}")
    print(f"  Tested: {len(suppression_scores)} dispatch-neighbor events")
    print(f"  Domain pairs with ≥2 co-occurrences: {len(cooccur)}")
    print(f"  Domains with neighbors: {len(neighbors)}")
    print(f"")
    print(f"  OVERALL SUPPRESSION:")
    print(f"    Mean suppression: {mean_supp:.1%}")
    print(f"    Positive (actual suppression): {pos_supp}/{len(all_supp)} = {pos_supp/len(all_supp):.1%}")
    print(f"    Negative (facilitation):       {neg_supp}/{len(all_supp)} = {neg_supp/len(all_supp):.1%}")
    print(f"")
    print(f"  TOP ALLELOPATHS (strongest suppression of neighbors):")
    for d, s in top_allelopaths[:8]:
        n = len(domain_supp[d])
        print(f"    {d:25s}  supp={s:+.1%}  n={n}")
    print(f"")
    print(f"  TOP FACILITATORS (attract neighbors):")
    for d, s in top_facilitators[:8]:
        n = len(domain_supp[d])
        print(f"    {d:25s}  supp={s:+.1%}  n={n}")
    print(f"")
    print(f"  VERDICT:")
    if confirmed:
        print(f"    ✓ ALLELOPATHY CONFIRMED — mean suppression {mean_supp:.1%} > 20% threshold")
    else:
        if mean_supp > 0:
            print(f"    ~ WEAK ALLELOPATHY — {mean_supp:.1%} suppression (threshold 20%)")
        elif mean_supp < -0.05:
            print(f"    ✗ FACILITATION — similar domains ATTRACT each other ({mean_supp:.1%})")
        else:
            print(f"    ✗ NEUTRAL — no significant suppression or facilitation ({mean_supp:.1%})")

    results = {
        "frontier": "F-PLB5",
        "session": "S539",
        "n_events": len(suppression_scores),
        "mean_suppression": round(mean_supp, 4),
        "positive_rate": round(pos_supp / len(all_supp), 4) if all_supp else 0,
        "confirmed": confirmed,
        "top_allelopaths": [(d, round(s, 4)) for d, s in top_allelopaths[:10]],
        "top_facilitators": [(d, round(s, 4)) for d, s in top_facilitators[:10]],
    }
    out_path = ROOT / "experiments" / "plant-biology" / "f-plb5-allelopathy-dispatch-s539.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Artifact: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
