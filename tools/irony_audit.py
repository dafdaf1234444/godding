#!/usr/bin/env python3
"""Detect structural ironies in the swarm: claims whose behavior contradicts their content."""

import argparse
import json
import sys

IRONY_CASES = [
    {
        "claim_id": "PHIL-13",
        "claim_content": "truth routes through evidence",
        "contradicting_evidence": "PHIL-13 itself is evidence-immune (dogma score 1.9, 9 challenges 0 DROPPED)",
        "evidence_source": "L-1293, dogma_finder.py",
        "irony_type": "self-exemption",
        "severity": 1.0,
        "proposed_fix": "run adversarial DROP attempt with rated evidence quality",
    },
    {
        "claim_id": "I8",
        "claim_content": "challenges serve the system",
        "contradicting_evidence": "challenges are structurally reversed — 3.4% DROP rate means challenges confirm, not test",
        "evidence_source": "L-950, challenge history",
        "irony_type": "behavioral-reversal",
        "severity": 0.9,
        "proposed_fix": "structural falsification incentive (reward DROPs not SUSTAINs)",
    },
    {
        "claim_id": "L-601",
        "claim_content": "voluntary protocols decay to structural floor",
        "contradicting_evidence": "most-cited lesson yet swarm keeps creating voluntary protocols (45% zombie tools)",
        "evidence_source": "L-601 citation graph, zombie audits",
        "irony_type": "self-exemption",
        "severity": 0.8,
        "proposed_fix": "wire zombie detection into creation pipeline (enforce at birth, not audit)",
    },
    {
        "claim_id": "PHIL-15",
        "claim_content": "universal reach",
        "contradicting_evidence": "0 external contacts in 529 sessions",
        "evidence_source": "inter-swarm bulletins, external log",
        "irony_type": "measurement-gap",
        "severity": 0.8,
        "proposed_fix": "external grounding requirement before claiming reach",
    },
    {
        "claim_id": "PHIL-25",
        "claim_content": "fairness as identity",
        "contradicting_evidence": "fairness score 0.4/1.0",
        "evidence_source": "dispatch_optimizer.py fairness metric",
        "irony_type": "behavioral-reversal",
        "severity": 0.7,
        "proposed_fix": "structural fairness enforcement in dispatch scoring",
    },
    {
        "claim_id": "PHIL-16b",
        "claim_content": "benefit of more than itself",
        "contradicting_evidence": "0 external beneficiaries across all sessions",
        "evidence_source": "human_impact.py, benefit_ratio",
        "irony_type": "measurement-gap",
        "severity": 0.7,
        "proposed_fix": "external beneficiary tracking with concrete count",
    },
    {
        "claim_id": "PHIL-4",
        "claim_content": "self-knowledge is primary output",
        "contradicting_evidence": "52.9% meta/self-referential treated as success, but this IS the L-1293 self-referentiality trap",
        "evidence_source": "L-1293, domain distribution",
        "irony_type": "self-reference-loop",
        "severity": 0.6,
        "proposed_fix": "target external knowledge ratio (invert success metric)",
    },
    {
        "claim_id": "dogma-finder",
        "claim_content": "detects dogma in the system",
        "contradicting_evidence": "dogma finder has 4 untested assumptions about itself",
        "evidence_source": "dogma_finder.py source inspection",
        "irony_type": "self-reference-loop",
        "severity": 0.5,
        "proposed_fix": "test dogma finder's own assumptions as first-class cases",
    },
    {
        "claim_id": "PHIL-5a",
        "claim_content": "always learn",
        "contradicting_evidence": "DECAYED 30.4% + BLIND-SPOT 10% of knowledge states",
        "evidence_source": "knowledge_state.py output",
        "irony_type": "measurement-gap",
        "severity": 0.5,
        "proposed_fix": "net-accessible knowledge metric (learned minus decayed)",
    },
    {
        "claim_id": "L-468",
        "claim_content": "L-396 about raising citation rates",
        "contradicting_evidence": "L-396 itself has zero citations",
        "evidence_source": "citation graph",
        "irony_type": "self-exemption",
        "severity": 0.3,
        "proposed_fix": "meta-lesson self-application check at creation time",
    },
]


def compute_irony_score():
    """Return the composite irony index (mean severity of all cases)."""
    if not IRONY_CASES:
        return 0.0
    return sum(c["severity"] for c in IRONY_CASES) / len(IRONY_CASES)


def type_counts():
    counts = {}
    for c in IRONY_CASES:
        counts[c["irony_type"]] = counts.get(c["irony_type"], 0) + 1
    return counts


def main():
    parser = argparse.ArgumentParser(description="Detect structural ironies in the swarm")
    parser.add_argument("--json", action="store_true", help="output JSON to stdout")
    parser.add_argument("--top", type=int, default=0, help="show only top N ironies")
    args = parser.parse_args()

    ranked = sorted(IRONY_CASES, key=lambda c: c["severity"], reverse=True)
    if args.top > 0:
        ranked = ranked[: args.top]

    if args.json:
        output = {
            "ironies": ranked,
            "composite_irony_index": round(compute_irony_score(), 3),
            "count_by_type": type_counts(),
            "total": len(IRONY_CASES),
        }
        print(json.dumps(output, indent=2))
        return

    # Table header
    print(f"{'#':<3} {'Severity':<9} {'Type':<20} {'Claim':<12} {'Content'}")
    print("-" * 90)
    for i, c in enumerate(ranked, 1):
        print(f"{i:<3} {c['severity']:<9.1f} {c['irony_type']:<20} {c['claim_id']:<12} {c['claim_content']}")
        print(f"    CONTRA: {c['contradicting_evidence']}")
        print(f"    FIX:    {c['proposed_fix']}")
        print()

    # Aggregate stats
    counts = type_counts()
    score = compute_irony_score()
    most_severe = ranked[0] if ranked else None

    print("=" * 90)
    print(f"Composite irony index: {score:.3f}  |  Total cases: {len(IRONY_CASES)}")
    print(f"By type: {', '.join(f'{t}={n}' for t, n in sorted(counts.items(), key=lambda x: -x[1]))}")
    if most_severe:
        print(f"Most severe: {most_severe['claim_id']} ({most_severe['severity']:.1f}) — {most_severe['claim_content']}")


if __name__ == "__main__":
    main()
