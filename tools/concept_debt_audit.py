#!/usr/bin/env python3
"""Concept debt audit — identify unnamed operational patterns in the swarm.

Scans lessons and tools for patterns with multiple ad-hoc descriptions but no
formal concept name. Reports concept debt: patterns that operate but can't be
cited, challenged, or improved because they lack symbolic handles.

Usage:
    python3 tools/concept_debt_audit.py          # full audit
    python3 tools/concept_debt_audit.py --json   # machine-readable output
"""
import argparse, json, os, re, glob

# Known concept registry: patterns that HAVE been named.
# Add entries here as new concepts are invented.
NAMED_CONCEPTS = {
    "concept-debt": {
        "lesson": "L-1263",
        "phrasings": ["concept debt", "unnamed pattern", "invisible load-bearing", "vocabulary gap"],
    },
    "generative-pressure": {
        "lesson": "L-1263",
        "phrasings": ["generative pressure", "selection-only", "divergence mechanism", "novelty gap"],
    },
    "diagnosis-repair-gap": {
        "lesson": "L-1263",
        "phrasings": ["diagnosis-repair", "diagnosis without repair", "prescription gap", "enforcement gap"],
    },
    "vocabulary-ceiling": {
        "lesson": "L-1266",
        "phrasings": ["vocabulary ceiling", "frontier-depleted", "concept poverty", "question limit"],
    },
    "epistemic-lock": {
        "lesson": "L-1266",
        "phrasings": ["epistemic lock", "closed-loop", "self-referential convergence", "closed system"],
    },
    "goodhart-cascade": {
        "lesson": "L-1269",
        "phrasings": ["goodhart cascade", "metric gaming", "reward channel", "compound error"],
    },
    "phantom-cascade": {
        "lesson": "L-1269",
        "phrasings": ["phantom cascade", "filter cascade", "compound FNR", "retention vs accessibility"],
    },
    "escape-hatch-hollowing": {
        "lesson": "L-1269",
        "phrasings": ["escape hatch", "hollowing", "bypass mechanism", "degenerative programme"],
    },
    "planning-obsolescence": {
        "lesson": "L-526",
        "phrasings": ["planning obsolescence", "orient stale", "preempted plan", "orient-execute gap"],
    },
    "sensor-only-trap": {
        "lesson": "L-1186",
        "phrasings": ["sensor only", "measurement without mechanism", "sensing without acting", "broken reward channel"],
    },
}

# Suspected unnamed patterns — known phrasings without a concept handle.
# These are concept debt: they exist operationally but lack names.
UNNAMED_PATTERNS = {
    "unwired-tool": {
        "phrasings": ["unwired tool", "tool without enforcement", "measurement without integration"],
        "evidence": "L-1148",
        "description": "Tools built but never wired into enforcement (orient, check.sh, periodics)",
    },
    "bootstrap-shadow": {
        "phrasings": ["bootstrap shadow", "presence without discovery", "undiscoverable knowledge"],
        "evidence": "L-1260",
        "description": "Knowledge exists in repo but is invisible to bootstrap sequence",
    },
}


def scan_file(path):
    """Return file content as lowercase string, or empty on error."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().lower()
    except Exception:
        return ""


def count_phrasings(content, phrasings):
    """Count occurrences of phrasings in content."""
    return sum(len(re.findall(re.escape(p), content)) for p in phrasings)


def audit(json_mode=False):
    lessons_dir = "memory/lessons"
    tool_files = glob.glob("tools/*.py")
    belief_files = glob.glob("beliefs/*.md")
    task_files = glob.glob("tasks/*.md")

    # Build corpus
    corpus = ""
    file_count = 0
    for pattern in [f"{lessons_dir}/L-*.md"] + [f for f in tool_files] + belief_files + task_files:
        for path in (glob.glob(pattern) if "*" in pattern else [pattern]):
            if os.path.isfile(path):
                corpus += scan_file(path) + "\n"
                file_count += 1

    # Audit named concepts — how well are they adopted?
    named_results = {}
    for handle, info in NAMED_CONCEPTS.items():
        hits = count_phrasings(corpus, [handle] + info["phrasings"])
        named_results[handle] = {
            "lesson": info["lesson"],
            "total_mentions": hits,
            "handle_mentions": len(re.findall(re.escape(handle), corpus)),
            "status": "ADOPTED" if hits >= 5 else "EMERGING" if hits >= 2 else "ORPHAN",
        }

    # Audit unnamed patterns — how much concept debt?
    unnamed_results = {}
    for pattern_id, info in UNNAMED_PATTERNS.items():
        hits = count_phrasings(corpus, info["phrasings"])
        unnamed_results[pattern_id] = {
            "evidence": info["evidence"],
            "description": info["description"],
            "ad_hoc_mentions": hits,
            "severity": "HIGH" if hits >= 10 else "MEDIUM" if hits >= 5 else "LOW",
        }

    # Summary
    total_named = len(NAMED_CONCEPTS)
    total_unnamed = len(UNNAMED_PATTERNS)
    total_debt = sum(1 for v in unnamed_results.values() if v["severity"] in ("HIGH", "MEDIUM"))
    adopted = sum(1 for v in named_results.values() if v["status"] == "ADOPTED")

    result = {
        "named_concepts": total_named,
        "adopted": adopted,
        "unnamed_patterns": total_unnamed,
        "high_debt": total_debt,
        "named": named_results,
        "unnamed": unnamed_results,
        "files_scanned": file_count,
    }

    if json_mode:
        print(json.dumps(result, indent=2))
        return result

    # Human-readable output
    print(f"=== CONCEPT DEBT AUDIT ===")
    print(f"Named concepts: {total_named} ({adopted} ADOPTED)")
    print(f"Unnamed patterns: {total_unnamed} ({total_debt} HIGH/MEDIUM debt)")
    print(f"Files scanned: {file_count}")
    print()

    print("--- Named Concepts (should be ADOPTED) ---")
    for handle, info in sorted(named_results.items()):
        status_mark = "✓" if info["status"] == "ADOPTED" else "○" if info["status"] == "EMERGING" else "✗"
        print(f"  {status_mark} {handle}: {info['total_mentions']} mentions ({info['handle_mentions']} by handle) [{info['status']}] — {info['lesson']}")

    print()
    print("--- Unnamed Patterns (concept debt) ---")
    for pid, info in sorted(unnamed_results.items(), key=lambda x: -x[1]["ad_hoc_mentions"]):
        sev = "!" if info["severity"] == "HIGH" else "~" if info["severity"] == "MEDIUM" else " "
        print(f"  {sev} {pid}: {info['ad_hoc_mentions']} ad-hoc mentions [{info['severity']}] — {info['evidence']}")
        print(f"    {info['description']}")

    print()
    naming_ratio = total_named / (total_named + total_unnamed) if (total_named + total_unnamed) > 0 else 0
    print(f"Naming ratio: {naming_ratio:.0%} ({total_named}/{total_named + total_unnamed})")
    print(f"Target: ≥60% naming ratio (concept debt < 40%)")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concept debt audit")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    audit(json_mode=args.json)
