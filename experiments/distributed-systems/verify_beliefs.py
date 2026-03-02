#!/usr/bin/env python3
"""Verify distributed systems beliefs against evidence catalog.

Checks B13 (error handling dominates), B14 (small-scale reproducibility),
B15 (CAP tradeoff) against documented evidence sources.

Usage: python3 experiments/distributed-systems/verify_beliefs.py
"""

import json
import sys

# Evidence catalog: each entry maps a belief to its supporting evidence
EVIDENCE = {
    "B13": {
        "claim": "Incorrect error handling causes ~92% of catastrophic distributed systems failures",
        "sources": [
            {
                "study": "Yuan et al. OSDI 2014",
                "sample_size": 198,
                "systems": ["Cassandra", "HBase", "HDFS", "MapReduce", "Redis"],
                "finding_pct": 92,
                "anti_patterns": [
                    "swallowed errors (log-only, no recovery)",
                    "placeholder handlers (TODO/FIXME)",
                    "overly-broad catch-then-abort (Exception→System.exit)"
                ],
                "reproducibility": "peer-reviewed, OSDI 2014"
            }
        ],
        "status": "theorized",
        "path_to_observed": "Analyze error paths in 3+ real codebases, correlate with bug severity"
    },
    "B14": {
        "claim": "98% of distributed bugs reproducible with ≤3 nodes, 74% deterministic",
        "sources": [
            {
                "study": "Yuan et al. OSDI 2014",
                "sample_size": 198,
                "pct_3_nodes": 98,
                "pct_2_nodes": 84,
                "pct_deterministic": 74,
                "pct_logged": 84,
                "pct_preventable": 58,
                "reproducibility": "peer-reviewed, OSDI 2014"
            }
        ],
        "status": "theorized",
        "path_to_observed": "Reproduce 10+ known bugs from Jepsen/bug trackers in ≤3 node setups"
    },
    "B15": {
        "claim": "During partitions, linearizability and availability are mutually exclusive (CAP)",
        "sources": [
            {
                "study": "Gilbert & Lynch 2002",
                "type": "formal_proof",
                "model": "asynchronous network, read/write register",
                "reproducibility": "mathematical proof, SIGACT News 2002"
            },
            {
                "study": "Brewer 2012 retrospective",
                "type": "author_correction",
                "key_point": "'Pick 2 of 3' was always misleading",
                "reproducibility": "IEEE Computer 2012"
            },
            {
                "study": "Kleppmann 2015 critique",
                "type": "refinement",
                "key_point": "CP/AP classification fails for most real systems",
                "reproducibility": "arXiv:1509.05393"
            }
        ],
        "status": "theorized",
        "path_to_observed": "3-node KV store + iptables partition + linearizability check",
        "caveats": [
            "Weaker consistency models (causal, eventual) escape CAP",
            "PACELC extends to latency-consistency tradeoff in normal operation",
            "Real systems rarely fit clean CP/AP labels"
        ]
    }
}

# Jepsen results confirming or challenging beliefs
JEPSEN_EVIDENCE = {
    "confirms_B13": [
        {"system": "NATS 2.12.1", "finding": "2-min fsync default = premature ack → data loss", "pattern": "swallowed error"},
        {"system": "MongoDB 3.x", "finding": "unsafe replication protocol, majority writes lost", "pattern": "protocol bug"},
        {"system": "RDS PostgreSQL 17.4", "finding": "different visibility on primary/secondary → anomalies", "pattern": "error handling gap"},
        {"system": "Kafka", "finding": "ordered delivery assumption violated by multi-TCP", "pattern": "protocol design flaw"},
    ],
    "confirms_B15": [
        {"system": "TigerBeetle 0.16.11", "finding": "meets Strong Serializability (CP verified)", "verified": True},
        {"system": "Cassandra (R=W=1)", "finding": "stale reads during partition (AP verified)", "verified": True},
    ]
}


def check_belief(belief_id):
    """Check a single belief against its evidence catalog."""
    if belief_id not in EVIDENCE:
        return {"belief": belief_id, "result": "NOT_FOUND"}

    ev = EVIDENCE[belief_id]
    result = {
        "belief": belief_id,
        "claim": ev["claim"],
        "status": ev["status"],
        "source_count": len(ev["sources"]),
        "peer_reviewed": any("peer-reviewed" in s.get("reproducibility", "") or "proof" in s.get("type", "")
                            for s in ev["sources"]),
        "path_to_observed": ev["path_to_observed"],
    }

    if belief_id in ("B13", "B14"):
        s = ev["sources"][0]
        result["sample_size"] = s["sample_size"]
        if "systems" in s:
            result["systems_tested"] = len(s["systems"])

    if "caveats" in ev:
        result["caveats"] = len(ev["caveats"])

    return result


def main():
    print("=== DISTRIBUTED SYSTEMS BELIEF VERIFICATION ===\n")

    all_pass = True
    for bid in ["B13", "B14", "B15"]:
        result = check_belief(bid)
        status_icon = "✓" if result["peer_reviewed"] else "?"
        print(f"[{status_icon}] {bid}: {result['claim']}")
        print(f"    Status: {result['status']} | Sources: {result['source_count']} | Peer-reviewed: {result['peer_reviewed']}")
        if "sample_size" in result:
            systems = f" across {result['systems_tested']} systems" if "systems_tested" in result else ""
            print(f"    Sample: {result['sample_size']} failures{systems}")
        if "caveats" in result:
            print(f"    Caveats: {result['caveats']}")
        print(f"    Path to observed: {result['path_to_observed']}")
        print()

    print("=== JEPSEN CORROBORATION ===\n")
    for category, entries in JEPSEN_EVIDENCE.items():
        print(f"  {category}:")
        for e in entries:
            verified = "✓" if e.get("verified") else "~"
            print(f"    [{verified}] {e['system']}: {e['finding']}")
        print()

    # Summary
    theorized = sum(1 for b in EVIDENCE.values() if b["status"] == "theorized")
    observed = sum(1 for b in EVIDENCE.values() if b["status"] == "observed")
    print(f"Summary: {len(EVIDENCE)} beliefs, {observed} observed, {theorized} theorized")
    print(f"Jepsen corroboration: {sum(len(v) for v in JEPSEN_EVIDENCE.values())} data points")
    print("RESULT: ALL THEORIZED — need empirical verification to upgrade")
    return 0


if __name__ == "__main__":
    sys.exit(main())
