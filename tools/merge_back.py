#!/usr/bin/env python3
"""
merge_back.py — Colony belief drift threshold (F-SEC1 Layer 3).

Computes belief drift between a colony's local beliefs and the parent
swarm's canonical beliefs. Enforces thresholds from PROTOCOL.md:
  - drift < 10%: auto-merge safe
  - 10% <= drift < 30%: merge with [CHILD-DERIVED n=1] flagging
  - drift >= 30%: Genesis Council review required

Usage:
    python3 tools/merge_back.py <domain>         # check one colony
    python3 tools/merge_back.py --all             # check all colonies
    python3 tools/merge_back.py --check           # exit 1 if any colony >= 30%
    python3 tools/merge_back.py --json            # machine-readable output
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ROOT / "domains"

# Drift thresholds from domains/security/PROTOCOL.md Layer 3
DRIFT_AUTO_MERGE = 0.10    # < 10%: safe auto-merge
DRIFT_FLAG_MERGE = 0.30    # 10-30%: merge with flagging
# >= 30%: council review required


def _extract_beliefs(text: str) -> list[str]:
    """Extract belief-like statements from markdown text.

    Handles multiple formats found in the codebase:
    - DEPS.md: '### B1:', '### B-EVAL1:' (heading format)
    - INVARIANTS.md: '### I9:' (heading format)
    - COLONY.md: '- CB-1:' (list format under ## Colony beliefs)
    """
    beliefs = []
    in_belief_section = False
    for line in text.splitlines():
        stripped = line.strip()
        # Track belief sections
        if re.match(r"^##\s+(Colony )?[Bb]eliefs", stripped):
            in_belief_section = True
            continue
        elif re.match(r"^## ", stripped) and in_belief_section:
            in_belief_section = False
            continue

        # Heading-format beliefs (### B1:, ### B-EVAL1:, ### I9:)
        if re.match(r"^###\s+(B\d+|B-EVAL\d+|I\d+):", stripped):
            beliefs.append(stripped)
        # List-format beliefs (- B-N:, - CB-N:, - I-N:)
        elif re.match(r"^-\s+(B-\d+|CB-\d+|I-\d+)\b", stripped):
            beliefs.append(stripped)
        # Freeform belief lines in belief section
        elif in_belief_section and stripped.startswith("- "):
            beliefs.append(stripped)
    return beliefs


def _extract_parent_beliefs() -> list[str]:
    """Extract canonical parent beliefs from DEPS.md, CORE.md, INVARIANTS.md."""
    beliefs = []
    for relpath in ["beliefs/DEPS.md", "beliefs/CORE.md", "beliefs/INVARIANTS.md"]:
        fp = ROOT / relpath
        if fp.exists():
            beliefs.extend(_extract_beliefs(fp.read_text(errors="ignore")))
    return beliefs


def _normalize(belief: str) -> str:
    """Normalize a belief string for comparison."""
    # Strip leading '- ', identifiers, confidence tags
    s = re.sub(r"^-\s+", "", belief)
    s = re.sub(r"^(B-\d+|CB-\d+|I-\d+|P-\d+):\s*", "", s)
    s = re.sub(r"\[.*?\]", "", s)  # remove [THEORIZED n=0] etc
    return s.strip().lower()


def compute_drift(domain: str) -> dict:
    """Compute belief drift for a colony domain."""
    colony_path = DOMAINS / domain / "COLONY.md"
    result = {
        "domain": domain,
        "colony_exists": colony_path.exists(),
    }

    if not colony_path.exists():
        result["status"] = "NO_COLONY"
        result["drift"] = 0.0
        result["verdict"] = "N/A"
        return result

    colony_text = colony_path.read_text(errors="ignore")
    colony_beliefs = _extract_beliefs(colony_text)
    parent_beliefs = _extract_parent_beliefs()

    if not parent_beliefs:
        result["status"] = "NO_PARENT_BELIEFS"
        result["drift"] = 0.0
        result["verdict"] = "N/A"
        return result

    # Normalize for comparison
    parent_normalized = {_normalize(b) for b in parent_beliefs if _normalize(b)}
    colony_normalized = {_normalize(b) for b in colony_beliefs if _normalize(b)}

    # Drift = beliefs in colony that don't appear in parent / total parent beliefs
    novel_beliefs = colony_normalized - parent_normalized
    drift = len(novel_beliefs) / len(parent_normalized) if parent_normalized else 0.0

    # Determine verdict
    if drift < DRIFT_AUTO_MERGE:
        verdict = "AUTO_MERGE"
    elif drift < DRIFT_FLAG_MERGE:
        verdict = "FLAG_MERGE"
    else:
        verdict = "COUNCIL_REVIEW"

    result.update({
        "parent_belief_count": len(parent_normalized),
        "colony_belief_count": len(colony_normalized),
        "novel_count": len(novel_beliefs),
        "novel_beliefs": sorted(novel_beliefs)[:10],  # cap for readability
        "drift": round(drift, 4),
        "drift_pct": f"{drift*100:.1f}%",
        "threshold_auto": f"{DRIFT_AUTO_MERGE*100:.0f}%",
        "threshold_flag": f"{DRIFT_FLAG_MERGE*100:.0f}%",
        "verdict": verdict,
        "status": "MEASURED",
    })
    return result


def check_bulletin_tiers(domain: str = None) -> list[dict]:
    """Check Trust-Tier compliance for bulletins (F-SEC1 Layer 2).

    T1: auto-trust (parent→child)
    T2: verify drift before merge (child→parent)
    T3: advisory only, never auto-merge (sibling→sibling)
    """
    bulletins_dir = ROOT / "experiments" / "inter-swarm" / "bulletins"
    if not bulletins_dir.exists():
        return [{"status": "NO_BULLETINS", "verdict": "N/A"}]

    results = []
    for f in sorted(bulletins_dir.glob("*.md")):
        if domain and f.stem != domain:
            continue
        text = f.read_text(errors="ignore")
        # Parse bulletin entries
        entries = re.split(r"\n---\n", text)
        for entry in entries:
            tier_match = re.search(r"Trust-Tier:\s*(T[123])", entry)
            type_match = re.search(r"Type:\s*(\S+)", entry)
            if not type_match:
                continue
            btype = type_match.group(1)
            tier = tier_match.group(1) if tier_match else "MISSING"
            # Enforce: T3 bulletins must never trigger belief merges
            results.append({
                "source": f.stem,
                "type": btype,
                "trust_tier": tier,
                "mergeable": tier == "T1",
                "requires_review": tier == "T2",
                "advisory_only": tier == "T3" or tier == "MISSING",
            })
    return results


def check_all_colonies() -> list[dict]:
    """Check drift for all bootstrapped colonies."""
    results = []
    if not DOMAINS.exists():
        return results
    for d in sorted(DOMAINS.iterdir()):
        if d.is_dir() and (d / "COLONY.md").exists():
            results.append(compute_drift(d.name))
    return results


def print_report(results: list[dict]):
    print("=== MERGE-BACK DRIFT CHECK (F-SEC1 Layer 3) ===\n")
    for r in results:
        if r["status"] == "NO_COLONY":
            continue
        icon = {"AUTO_MERGE": "+", "FLAG_MERGE": "~", "COUNCIL_REVIEW": "!",
                "N/A": "-"}.get(r["verdict"], "?")
        print(f"  [{icon}] {r['domain']}: drift={r.get('drift_pct', '?')} "
              f"({r.get('novel_count', 0)} novel / {r.get('parent_belief_count', '?')} parent) "
              f"— {r['verdict']}")
        if r.get("novel_beliefs"):
            for nb in r["novel_beliefs"][:3]:
                print(f"        novel: {nb[:80]}")

    # Summary
    measured = [r for r in results if r["status"] == "MEASURED"]
    if measured:
        max_drift = max(r["drift"] for r in measured)
        council_needed = [r["domain"] for r in measured if r["verdict"] == "COUNCIL_REVIEW"]
        print(f"\n  Max drift: {max_drift*100:.1f}%")
        if council_needed:
            print(f"  COUNCIL REVIEW REQUIRED: {', '.join(council_needed)}")
        else:
            print(f"  All colonies within auto-merge/flag thresholds.")


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    check_mode = "--check" in args
    check_all = "--all" in args
    args = [a for a in args if not a.startswith("--")]

    if check_all or check_mode:
        results = check_all_colonies()
    elif args:
        results = [compute_drift(args[0])]
    else:
        results = check_all_colonies()

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)

    # Check mode: exit 1 if any colony needs council review
    if check_mode:
        measured = [r for r in results if r["status"] == "MEASURED"]
        if any(r["verdict"] == "COUNCIL_REVIEW" for r in measured):
            print("\nFAIL: Colony drift exceeds 30% — council review required.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
