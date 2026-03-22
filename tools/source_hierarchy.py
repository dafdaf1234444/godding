#!/usr/bin/env python3
"""
source_hierarchy.py — Classify beliefs/claims by evidence source level (DRM-H21, L-1313).

Implements Islamic usul al-fiqh inspired source hierarchy for swarm epistemology:
  Level 1 (DIRECT):   Measured in this system with n≥100 or external replication
  Level 2 (EMPIRICAL): Observed in this system, n<100 or single measurement
  Level 3 (CONSENSUS): Multiple sessions agree but no controlled measurement
  Level 4 (ANALOGICAL): Derived by analogy from another domain

Key insight (DRM-H21): Source hierarchies evolved as defense against Lakatosian
protective belts. Without formal levels, challenges get reclassified. Higher-level
beliefs should get MORE frequent auditing, not less (inverse-frequency principle).

Also classifies PHIL claims (L-1314: 18/22 PHIL claims score ≥0.6 on dogma finder).
"""

import re
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent


def classify_belief(text, belief_id):
    """Classify a belief by source level based on its evidence description."""
    text_lower = text.lower()

    # Extract evidence type — DEPS.md format: "**Evidence**: observed" or "Evidence: theorized"
    evidence_m = re.search(r'\*?\*?evidence\*?\*?[:\s]+(\w+)', text_lower)
    evidence_type = evidence_m.group(1) if evidence_m else "unknown"

    # Extract last-tested session — DEPS.md: "**Last tested**: S497 (...)"
    tested_m = re.search(r'last tested\*?\*?[:\s]*s(\d+)', text_lower)
    last_tested = int(tested_m.group(1)) if tested_m else 0

    # Extract sample sizes mentioned
    n_matches = re.findall(r'\bn[=≥>]\s*(\d+)', text, re.IGNORECASE)
    n_matches += re.findall(r'\(n\s*[=≥>]\s*(\d+)\)', text, re.IGNORECASE)
    max_n = max((int(x) for x in n_matches), default=0)

    # Check for external references
    has_external = bool(re.search(r'external|paper|benchmark|study|literature', text_lower))

    # Check for controlled measurement vs observation
    has_measurement = bool(re.search(r'measured|quantif|statistic|correlation|regression', text_lower))

    # Classify
    if (max_n >= 100 or has_external) and has_measurement:
        level = 1  # DIRECT
        level_name = "DIRECT"
    elif evidence_type == "observed" and (max_n > 0 or has_measurement):
        level = 2  # EMPIRICAL
        level_name = "EMPIRICAL"
    elif evidence_type == "observed":
        level = 3  # CONSENSUS
        level_name = "CONSENSUS"
    else:
        level = 4  # ANALOGICAL
        level_name = "ANALOGICAL"

    return {
        "id": belief_id,
        "level": level,
        "level_name": level_name,
        "evidence_type": evidence_type,
        "max_n": max_n,
        "last_tested": last_tested,
        "has_external": has_external,
    }


def classify_phil(text, phil_id):
    """Classify a PHIL claim by source level."""
    text_lower = text.lower()

    # PHIL claims are identity/axiom claims — check ground truth sections
    has_ground_truth = "ground truth" in text_lower
    has_measured = "measured" in text_lower or "observed" in text_lower
    has_aspirational = "aspirational" in text_lower
    has_external = bool(re.search(r'external|paper|benchmark|controlled', text_lower))

    if has_ground_truth and has_measured and not has_aspirational:
        level = 2  # EMPIRICAL (observed within system)
        level_name = "EMPIRICAL"
    elif has_ground_truth and has_aspirational:
        level = 3  # CONSENSUS (partially grounded)
        level_name = "CONSENSUS"
    elif has_ground_truth:
        level = 3
        level_name = "CONSENSUS"
    else:
        level = 4  # ANALOGICAL (no ground truth section)
        level_name = "ANALOGICAL"

    return {
        "id": phil_id,
        "level": level,
        "level_name": level_name,
        "has_ground_truth": has_ground_truth,
        "has_external": has_external,
    }


def load_beliefs():
    """Load beliefs from DEPS.md."""
    deps_path = ROOT / "beliefs" / "DEPS.md"
    if not deps_path.exists():
        return {}
    text = deps_path.read_text(encoding="utf-8", errors="replace")
    beliefs = {}
    current_id = None
    current_text = []
    for line in text.split('\n'):
        m = re.match(r'^### (B\d+|B-\w+):', line)
        if m:
            if current_id:
                beliefs[current_id] = '\n'.join(current_text)
            current_id = m.group(1)
            current_text = [line]
        elif current_id:
            current_text.append(line)
    if current_id:
        beliefs[current_id] = '\n'.join(current_text)
    return beliefs


def load_phil():
    """Load PHIL claims from PHILOSOPHY.md."""
    phil_path = ROOT / "beliefs" / "PHILOSOPHY.md"
    if not phil_path.exists():
        return {}
    text = phil_path.read_text(encoding="utf-8", errors="replace")
    phils = {}
    # Find [PHIL-N] markers and capture surrounding context
    for m in re.finditer(r'\[PHIL-(\d+)\]', text):
        phil_id = f"PHIL-{m.group(1)}"
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 1000)
        phils[phil_id] = text[start:end]
    return phils


def audit_frequency(level, current_session):
    """Recommend audit frequency based on source level (inverse-frequency principle).

    DRM-H21: axiom-level beliefs get MORE frequent audits, not fewer.
    L-942: 40x detection asymmetry exists because high-level beliefs get fewer audits.
    """
    # Inverse: higher source level (lower number) = more frequent audit
    cadences = {
        1: 50,   # DIRECT: well-grounded, standard cadence
        2: 30,   # EMPIRICAL: needs periodic revalidation
        3: 15,   # CONSENSUS: under-tested, audit frequently
        4: 10,   # ANALOGICAL: weakest evidence, highest audit frequency
    }
    return cadences.get(level, 30)


def main():
    beliefs = load_beliefs()
    phils = load_phil()

    print("=== SOURCE HIERARCHY CLASSIFIER (DRM-H21, L-1313) ===")
    print("Level 1 DIRECT: measured, n≥100 or external replication")
    print("Level 2 EMPIRICAL: observed, n<100 or single measurement")
    print("Level 3 CONSENSUS: multiple sessions agree, no controlled measurement")
    print("Level 4 ANALOGICAL: derived by analogy, no direct test")
    print()

    # Classify beliefs
    belief_results = []
    for bid, text in sorted(beliefs.items()):
        result = classify_belief(text, bid)
        belief_results.append(result)

    # Classify PHIL claims
    phil_results = []
    for pid, text in sorted(phils.items(), key=lambda x: int(re.search(r'\d+', x[0]).group())):
        result = classify_phil(text, pid)
        phil_results.append(result)

    # Print belief results
    print(f"--- Beliefs ({len(belief_results)}) ---")
    for level in [1, 2, 3, 4]:
        items = [r for r in belief_results if r['level'] == level]
        name = items[0]['level_name'] if items else ['DIRECT', 'EMPIRICAL', 'CONSENSUS', 'ANALOGICAL'][level - 1]
        print(f"\n  Level {level} ({name}): {len(items)}")
        for r in items:
            tested = f"S{r['last_tested']}" if r['last_tested'] else "never"
            n_str = f"n={r['max_n']}" if r['max_n'] else "n=?"
            print(f"    {r['id']:8s}  {r['evidence_type']:10s}  {n_str:8s}  last={tested}")

    # Print PHIL results
    print(f"\n--- PHIL claims ({len(phil_results)}) ---")
    for level in [1, 2, 3, 4]:
        items = [r for r in phil_results if r['level'] == level]
        name = ['DIRECT', 'EMPIRICAL', 'CONSENSUS', 'ANALOGICAL'][level - 1]
        print(f"\n  Level {level} ({name}): {len(items)}")
        for r in items:
            gt = "GT" if r.get('has_ground_truth') else "no-GT"
            print(f"    {r['id']:10s}  {gt}")

    # Audit recommendations
    print(f"\n--- Inverse-frequency audit recommendations ---")
    print("  (DRM-H21: higher source level = more frequent audit)")
    all_results = belief_results + phil_results
    for level in [4, 3, 2, 1]:
        items = [r for r in all_results if r['level'] == level]
        cadence = audit_frequency(level, 500)
        name = ['DIRECT', 'EMPIRICAL', 'CONSENSUS', 'ANALOGICAL'][level - 1]
        print(f"  Level {level} ({name}): {len(items)} items, audit every {cadence} sessions")
        for r in items:
            print(f"    {r['id']}")

    # Summary stats
    level_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for r in all_results:
        level_counts[r['level']] += 1

    print(f"\n--- Summary ---")
    total = len(all_results)
    for level in [1, 2, 3, 4]:
        name = ['DIRECT', 'EMPIRICAL', 'CONSENSUS', 'ANALOGICAL'][level - 1]
        pct = 100 * level_counts[level] / total if total else 0
        print(f"  Level {level} ({name}): {level_counts[level]} ({pct:.0f}%)")

    # JSON output
    if "--json" in sys.argv:
        output = {
            "date": datetime.now().isoformat(),
            "beliefs": belief_results,
            "phil_claims": phil_results,
            "level_distribution": {f"L{k}": v for k, v in level_counts.items()},
            "total_items": total,
            "audit_cadences": {f"L{l}": audit_frequency(l, 500) for l in [1, 2, 3, 4]},
        }
        print(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    main()
