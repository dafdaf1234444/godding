#!/usr/bin/env python3
"""
enforcement_router.py — Map meta-prescriptions to structural implementations.

L-831: L-601 not applied to itself — prescriptions without enforcement decay.
L-847: Before adding checks, scan for type-1 gaps (rule wired without L-ID). Add # L-NNN.
Finds lessons with ## Rule sections and classifies each as:
  STRUCTURAL  — lesson ID referenced in core tool files (enforced in code)
  PERIODIC    — lesson ID referenced in periodics.json / maintenance periodic section
  ASPIRATIONAL — lesson ID not found in any tool (decays per L-601)

Each lesson also gets an `actionable` flag (L-875): distinguishes imperative prescriptions
("Run X", "Add Y to Z", "Must enforce") from observational findings ("The rate is 50%").
ASPIRATIONAL + actionable = real prescription gap. ASPIRATIONAL + not actionable = finding.

Usage:
  python3 tools/enforcement_router.py [--json] [--min-sharpe N] [--top N] [--actionable-only]
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Core tool files that wire structural enforcement
STRUCTURAL_FILES = [
    "tools/maintenance.py",
    "tools/orient.py",
    "tools/open_lane.py",
    "tools/close_lane.py",
    "tools/check.sh",
    "tools/science_quality.py",
    "tools/dispatch_optimizer.py",
    "tools/contract_check.py",
    "tools/validate_beliefs.py",
    "tools/enforcement_router.py",  # L-847: self-reference — this file enforces prescription tracking
]

# Periodic-tier files (softer enforcement)
PERIODIC_FILES = [
    "tools/periodics.json",
    "memory/OPERATIONS.md",
    "beliefs/CORE.md",
    "SWARM.md",
    "CLAUDE.md",
]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


# Imperative verbs that signal a command (L-875: actionable classifier)
_IMPERATIVE_VERBS = {
    "run", "add", "wire", "enforce", "check", "implement", "use", "ensure",
    "fix", "update", "build", "create", "require", "split", "apply", "extend",
    "track", "flag", "audit", "always", "never", "parse", "move", "log",
    "test", "measure", "migrate", "expose", "prefer", "confirm", "capture",
    "include", "write", "record", "emit", "reset", "route", "assign", "reserve",
    "avoid", "do", "make", "keep", "mark", "open", "close", "commit", "push",
    "scan", "report", "store", "filter", "index", "verify", "validate",
    "pause", "treat", "stop", "start", "follow", "prioritize", "schedule",
    "batch", "target", "limit", "cap", "trim", "merge", "archive", "retire",
    "set", "raise", "lower", "bump", "pin", "upgrade", "downgrade", "drop",
    "defer", "escalate", "trigger", "fire", "seed", "bootstrap", "inject",
}


def classify_actionability(rule_text: str) -> bool:
    """Return True if rule_text is an imperative prescription (not just an observation).

    Actionable = has imperative verb at sentence start, 'must' modal, explicit Fix:/Wire:
    prefix, or backtick code command. Observational = primarily describes a finding.
    (L-875: ~50% of ASPIRATIONAL lessons are observational, not actionable commands.)
    """
    if not rule_text:
        return False

    text = rule_text.strip()

    # Strong actionable signals
    if re.search(r"\bmust\b", text, re.IGNORECASE):
        return True
    if re.search(r"(?:^|\n)\s*(?:Fix|Wire|Enforce|Require|Always|Never)\s*:", text):
        return True
    if re.search(r"`python3?\s+tools/", text):
        return True
    if re.search(r"\badd\s+\S+\s+to\s+\w+\.py\b", text, re.IGNORECASE):
        return True
    # Colon-prefix imperative: "Above 40%: run X" → actionable
    colon_words = re.findall(r":\s+(\w+)", text)
    if any(w.lower() in _IMPERATIVE_VERBS for w in colon_words):
        return True

    # Imperative first word of ANY sentence in the rule text
    sentences = re.split(r"(?<=[.!?])\s+|(?<=\n)", text)
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        first_word = re.split(r"\W+", sentence)[0].lower()
        if first_word in _IMPERATIVE_VERBS:
            return True

    # Imperative first word after "The swarm should/must" → still imperative
    m = re.match(r"The swarm (?:should|must)\s+(\w+)", text, re.IGNORECASE)
    if m and m.group(1).lower() in _IMPERATIVE_VERBS:
        return True

    return False


def scan_lessons(lessons_dir: Path, min_sharpe: int = 0) -> list[dict]:
    """Extract lessons with ## Rule sections."""
    rules = []
    for f in sorted(lessons_dir.glob("L-*.md")):
        content = _read(f)
        lesson_id = f.stem

        sharpe_m = re.search(r"Sharpe:\s*(\d+)", content)
        sharpe = int(sharpe_m.group(1)) if sharpe_m else 0
        if sharpe < min_sharpe:
            continue

        session_m = re.search(r"Session:\s*(S\d+)", content)
        session = session_m.group(1) if session_m else "?"

        domain_m = re.search(r"\|\s*Domain:\s*(\S+)", content)
        domain = domain_m.group(1) if domain_m else "?"

        rule_m = re.search(
            r"^## Rule\s*\n(.*?)(?=\n##|\Z)", content, re.MULTILINE | re.DOTALL
        )
        if not rule_m:
            continue

        rule_text = rule_m.group(1).strip()
        # Extract first meaningful sentence
        first_line = rule_text.split("\n")[0].strip()

        rules.append(
            {
                "lesson": lesson_id,
                "session": session,
                "domain": domain,
                "sharpe": sharpe,
                "rule": first_line[:200],
                "actionable": classify_actionability(rule_text),
            }
        )
    return rules


def build_reference_maps(repo_root: Path) -> tuple[set[str], set[str]]:
    """Return (structural_refs, periodic_refs) — lesson IDs found in each tier."""
    structural_refs: set[str] = set()
    periodic_refs: set[str] = set()

    lesson_pattern = re.compile(r"\bL-(\d{3,4})\b")

    for rel_path in STRUCTURAL_FILES:
        content = _read(repo_root / rel_path)
        for m in lesson_pattern.finditer(content):
            structural_refs.add(f"L-{m.group(1)}")

    for rel_path in PERIODIC_FILES:
        content = _read(repo_root / rel_path)
        for m in lesson_pattern.finditer(content):
            if f"L-{m.group(1)}" not in structural_refs:
                periodic_refs.add(f"L-{m.group(1)}")

    return structural_refs, periodic_refs


def classify(
    lesson_id: str, structural_refs: set[str], periodic_refs: set[str]
) -> str:
    if lesson_id in structural_refs:
        return "STRUCTURAL"
    if lesson_id in periodic_refs:
        return "PERIODIC"
    return "ASPIRATIONAL"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--min-sharpe", type=int, default=0, help="Minimum Sharpe threshold"
    )
    parser.add_argument(
        "--top", type=int, default=10, help="Top N aspirational prescriptions to show"
    )
    parser.add_argument(
        "--actionable-only", action="store_true",
        help="Filter ASPIRATIONAL output to actionable prescriptions only (L-875)"
    )
    args = parser.parse_args()

    lessons_dir = REPO_ROOT / "memory" / "lessons"
    rules = scan_lessons(lessons_dir, min_sharpe=args.min_sharpe)
    structural_refs, periodic_refs = build_reference_maps(REPO_ROOT)

    classified = []
    for r in rules:
        tier = classify(r["lesson"], structural_refs, periodic_refs)
        classified.append({**r, "tier": tier})

    classified.sort(key=lambda x: (-x["sharpe"], x["lesson"]))

    counts = {
        "STRUCTURAL": sum(1 for r in classified if r["tier"] == "STRUCTURAL"),
        "PERIODIC": sum(1 for r in classified if r["tier"] == "PERIODIC"),
        "ASPIRATIONAL": sum(1 for r in classified if r["tier"] == "ASPIRATIONAL"),
        "total": len(classified),
    }

    aspirational = [r for r in classified if r["tier"] == "ASPIRATIONAL"]
    actionable_asp = [r for r in aspirational if r["actionable"]]
    observational_asp = [r for r in aspirational if not r["actionable"]]
    high_sharpe_asp = [r for r in aspirational if r["sharpe"] >= 8]
    high_sharpe_actionable = [r for r in actionable_asp if r["sharpe"] >= 8]

    # --actionable-only filters the high-sharpe display list
    display_asp = actionable_asp if args.actionable_only else aspirational
    display_hs = high_sharpe_actionable if args.actionable_only else high_sharpe_asp

    if args.json:
        result = {
            "summary": counts,
            "enforcement_rate": round(
                counts["STRUCTURAL"] / counts["total"], 3
            ) if counts["total"] else 0,
            "prescription_gap_rate": round(
                counts["ASPIRATIONAL"] / counts["total"], 3
            ) if counts["total"] else 0,
            "actionable_gap_rate": round(
                len(actionable_asp) / counts["total"], 3
            ) if counts["total"] else 0,
            "actionable_aspirational_count": len(actionable_asp),
            "observational_aspirational_count": len(observational_asp),
            "high_sharpe_aspirational": display_hs[:args.top],
            "all_aspirational_count": len(aspirational),
        }
        print(json.dumps(result, indent=2))
        return

    # Human-readable output
    total = counts["total"]
    print(f"=== ENFORCEMENT ROUTER (L-831/L-875) ===")
    print(f"Rule-bearing lessons: {total}")
    print(
        f"  STRUCTURAL  (wired in code): {counts['STRUCTURAL']} "
        f"({100*counts['STRUCTURAL']//total if total else 0}%)"
    )
    print(
        f"  PERIODIC    (in protocol):   {counts['PERIODIC']} "
        f"({100*counts['PERIODIC']//total if total else 0}%)"
    )
    print(
        f"  ASPIRATIONAL (unimplemented): {counts['ASPIRATIONAL']} "
        f"({100*counts['ASPIRATIONAL']//total if total else 0}%)"
    )
    print(
        f"    → actionable prescriptions: {len(actionable_asp)} "
        f"({100*len(actionable_asp)//counts['ASPIRATIONAL'] if counts['ASPIRATIONAL'] else 0}%)"
    )
    print(
        f"    → observational findings:   {len(observational_asp)} "
        f"({100*len(observational_asp)//counts['ASPIRATIONAL'] if counts['ASPIRATIONAL'] else 0}%)"
    )

    enforcement_rate = counts["STRUCTURAL"] / total if total else 0
    true_gap_rate = len(actionable_asp) / total if total else 0
    print(f"\nEnforcement rate: {enforcement_rate:.1%} (structural only)")
    print(f"Prescription gap (all aspirational): {len(aspirational)}/{total}")
    print(f"True prescription gap (actionable only): {len(actionable_asp)}/{total} ({true_gap_rate:.1%})")

    if display_hs:
        label = "actionable " if args.actionable_only else ""
        print(f"\nTop {label}ASPIRATIONAL prescriptions (Sharpe≥8, n={len(display_hs)}):")
        for r in display_hs[: args.top]:
            act_tag = "[ACT]" if r["actionable"] else "[OBS]"
            print(
                f"  {act_tag} {r['lesson']} Sh={r['sharpe']} ({r['domain']}):"
            )
            print(f"    {r['rule'][:90]}")
    else:
        print("\nNo high-Sharpe aspirational prescriptions found.")

    if aspirational:
        print(
            f"\nFull aspirational list: {len(aspirational)} prescriptions lacking structural wiring."
        )
        print("Priority: enforce lessons with Sharpe≥9 first (highest meta-value).")


if __name__ == "__main__":
    main()
