#!/usr/bin/env python3
"""external_grounding_check.py — Detect lessons without external grounding (F-GND1, L-1192, L-1125).

Scans lesson files for external references: URLs, paper citations, named external
benchmarks, DOIs, or other non-swarm evidence sources. Emits NOTICE when a lesson
has zero external references — structural pressure toward grounded knowledge.

Usage:
  python3 tools/external_grounding_check.py                    # scan all recent
  python3 tools/external_grounding_check.py --staged           # check.sh hook mode
  python3 tools/external_grounding_check.py --baseline N       # measure last N lessons
  python3 tools/external_grounding_check.py --json             # machine-readable
  python3 tools/external_grounding_check.py --decay            # grounding decay report
  python3 tools/external_grounding_check.py --decay --top 10   # top N decay priorities

Related: F-GND1, L-1192, L-1125, L-1118, L-601, F-COMP1, grounding_audit.py
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LESSON_DIR = ROOT / "memory" / "lessons"

# Patterns that indicate external grounding (not self-referential)
EXTERNAL_PATTERNS = [
    (r'https?://\S+', "URL"),
    (r'arXiv[:\s]\d{4}\.\d+', "arXiv"),
    (r'doi[:\s]10\.\d{4,}', "DOI"),
    (r'\b\w+ et al\.?\b', "paper citation"),
    (r'\b[A-Z][a-z]+\s*\(\d{4}\)', "author-year citation"),
    (r'\b(?:IEEE|ACM|NeurIPS|NIPS|ICML|ICLR|AAAI|Nature|Science|PNAS|OSDI|SOSP)\b', "venue"),
    (r'\b(?:MMLU|HumanEval|GPQA|SWE-bench|ARC|HellaSwag|TruthfulQA|BigBench)\b', "benchmark"),
    (r'\b(?:Kauffman|Anderson|Shannon|Bayes|Pareto|Zipf|Lorenz|Nash|von Neumann|'
     r'Ostrom|Rawls|Goodhart|Campbell|Margulis|Mayr|Amdahl|Turing|Gödel|Dijkstra|'
     r'Arrow|Coase|Hayek|Mandelbrot|Erdős|Boltzmann|Carnot|Heisenberg|Feynman|'
     r'Darwin|Dawkins|Minsky|Simon|Kahneman|Tversky|Dunning|Kruger)\b', "named theory"),
    (r'\bISBN\s*[\d-]+', "ISBN"),
    (r'\bISSN\s*[\d-]+', "ISSN"),
    (r'\b(?:Wikipedia|Stack Overflow|GitHub\.com|arxiv\.org)\b', "external source"),
    (r'\b(?:Jepsen|TPC-C|SPEC|MLPerf)\b', "external benchmark"),
]

# Patterns that are self-referential (swarm-internal)
INTERNAL_PATTERNS = re.compile(
    r'\b(?:L-\d+|P-\d+|B-\w+|F-\w+|PHIL-\d+|ISO-\d+|SIG-\d+|FM-\d+|S\d{3,4}|'
    r'tools/\w+|orient\.py|compact\.py|check\.sh|CORE\.md|INDEX\.md|SWARM\.md|'
    r'FRONTIER\.md|LANES\.md|COLONY\.md|DOMAIN\.md)\b'
)


def scan_lesson(path: Path) -> dict:
    """Scan a single lesson for external references."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return {"file": path.name, "error": "unreadable"}

    external_refs = []
    for pattern, label in EXTERNAL_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            external_refs.append({"type": label, "count": len(matches), "examples": matches[:2]})

    # Check for explicit External: header field with non-"none" content
    ext_field = re.search(r'^(?:\*{0,2})External(?:\*{0,2})\s*:\s*(.+)', content, re.MULTILINE)
    has_ext_field = False
    ext_field_content = ""
    if ext_field:
        ext_field_content = ext_field.group(1).strip()
        # "none" or "none — reason" means explicitly no external refs (conscious opt-out)
        if not ext_field_content.lower().startswith("none"):
            has_ext_field = True
            if not external_refs:  # only add if patterns didn't already detect
                external_refs.append({"type": "explicit-field", "count": 1, "examples": [ext_field_content[:80]]})

    internal_refs = INTERNAL_PATTERNS.findall(content)

    return {
        "file": path.name,
        "has_external": len(external_refs) > 0 or has_ext_field,
        "has_external_field": has_ext_field,
        "external_refs": external_refs,
        "external_count": sum(r["count"] for r in external_refs),
        "internal_count": len(internal_refs),
        "grounding_ratio": (
            sum(r["count"] for r in external_refs)
            / max(1, sum(r["count"] for r in external_refs) + len(internal_refs))
        ),
    }


def get_staged_lessons() -> list[Path]:
    """Get lesson files staged for commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--diff-filter=A", "--name-only"],
            capture_output=True, text=True, cwd=ROOT,
        )
        return [
            ROOT / p.strip()
            for p in result.stdout.splitlines()
            if p.strip().startswith("memory/lessons/L-") and p.strip().endswith(".md")
        ]
    except Exception:
        return []


def get_recent_lessons(n: int = 20) -> list[Path]:
    """Get last N lesson files by number."""
    files = sorted(
        [f for f in LESSON_DIR.iterdir() if f.name.startswith("L-") and f.suffix == ".md"],
        key=lambda f: int(re.search(r"L-(\d+)", f.name).group(1)) if re.search(r"L-(\d+)", f.name) else 0,
        reverse=True,
    )
    return files[:n]


def has_external_field(path: Path) -> bool:
    """Check if a lesson has an explicit External: header field."""
    try:
        content = path.read_text(encoding="utf-8")
        # Match "External:" at start of line (with optional bold markers)
        return bool(re.search(r'^\*{0,2}External\*{0,2}\s*:', content, re.MULTILINE))
    except Exception:
        return False


def _current_session() -> int:
    """Get current session number from SESSION-LOG.md or INDEX.md."""
    for fname in ["memory/SESSION-LOG.md", "memory/INDEX.md"]:
        try:
            text = (ROOT / fname).read_text(encoding="utf-8")
            m = re.search(r"S(\d{3,4})", text)
            if m:
                return int(m.group(1))
        except Exception:
            pass
    return 480


def _extract_lesson_meta(path: Path) -> dict:
    """Extract session number and Sharpe from a lesson file."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return {"session": 0, "sharpe": 5}
    session_m = re.search(r'Session:\s*S(\d+)', content)
    sharpe_m = re.search(r'Sharpe:\s*(\d+)', content)
    return {
        "session": int(session_m.group(1)) if session_m else 0,
        "sharpe": int(sharpe_m.group(1)) if sharpe_m else 5,
    }


def grounding_decay_report(top_n: int = 15):
    """Compute grounding decay for all lessons. Ungrounded lessons accumulate
    epistemic debt proportional to age × importance (Sharpe). High-Sharpe lessons
    without external evidence are the highest priority for grounding."""
    cur = _current_session()
    all_lessons = sorted(
        [f for f in LESSON_DIR.iterdir() if f.name.startswith("L-") and f.suffix == ".md"],
        key=lambda f: int(re.search(r"L-(\d+)", f.name).group(1)) if re.search(r"L-(\d+)", f.name) else 0,
    )

    decayed = []
    grounded_count = 0
    for path in all_lessons:
        scan = scan_lesson(path)
        if scan.get("error"):
            continue
        meta = _extract_lesson_meta(path)
        age = max(0, cur - meta["session"])

        # Grounding health: 1.0 if externally grounded, decays from 0.5 over time if not
        if scan["has_external"]:
            health = min(1.0, 0.7 + scan["grounding_ratio"])
            grounded_count += 1
        else:
            # Ungrounded lessons decay: health = 0.5 * exp(-age/200)
            # At age 0: health=0.5, at age 200: health=0.18, at age 400: health=0.07
            import math
            health = 0.5 * math.exp(-age / 200.0)

        # Priority = Sharpe × (1 - health): high Sharpe + low health = urgent
        priority = meta["sharpe"] * (1.0 - health)

        decayed.append({
            "file": scan["file"],
            "sharpe": meta["sharpe"],
            "age": age,
            "has_external": scan["has_external"],
            "health": round(health, 3),
            "priority": round(priority, 2),
            "external_count": scan["external_count"],
            "internal_count": scan["internal_count"],
        })

    # Sort by priority (highest first)
    decayed.sort(key=lambda x: x["priority"], reverse=True)

    total = len(decayed)
    avg_health = sum(d["health"] for d in decayed) / max(1, total)
    critical = sum(1 for d in decayed if d["health"] < 0.1)

    print(f"=== GROUNDING DECAY REPORT — F-GND1 Phase 1 ===\n")
    print(f"  Lessons: {total} | Grounded: {grounded_count} ({grounded_count*100/max(1,total):.0f}%)")
    print(f"  Avg health: {avg_health:.3f} | Critical (<0.1): {critical}")
    print(f"  Session: S{cur} | Decay rate: exp(-age/200)\n")

    print(f"--- Top {top_n} grounding priorities (high Sharpe × low health) ---")
    for d in decayed[:top_n]:
        ext_mark = "✓" if d["has_external"] else "✗"
        print(f"  {d['file']:14s}  Sh={d['sharpe']:2d}  age={d['age']:3d}  "
              f"health={d['health']:.3f}  priority={d['priority']:.1f}  ext={ext_mark}")

    print(f"\n--- Health distribution ---")
    brackets = [(0, 0.1, "CRITICAL"), (0.1, 0.3, "LOW"), (0.3, 0.5, "MODERATE"), (0.5, 1.01, "HEALTHY")]
    for lo, hi, label in brackets:
        count = sum(1 for d in decayed if lo <= d["health"] < hi)
        print(f"  {label:10s}: {count:4d} ({count*100/max(1,total):.0f}%)")


def section_grounding_decay() -> str:
    """Orient.py integration: one-line grounding decay summary."""
    cur = _current_session()
    all_lessons = sorted(
        [f for f in LESSON_DIR.iterdir() if f.name.startswith("L-") and f.suffix == ".md"],
        key=lambda f: int(re.search(r"L-(\d+)", f.name).group(1)) if re.search(r"L-(\d+)", f.name) else 0,
    )
    import math
    critical = 0
    grounded = 0
    total = 0
    for path in all_lessons:
        scan = scan_lesson(path)
        if scan.get("error"):
            continue
        total += 1
        meta = _extract_lesson_meta(path)
        age = max(0, cur - meta["session"])
        if scan["has_external"]:
            grounded += 1
        else:
            health = 0.5 * math.exp(-age / 200.0)
            if health < 0.1:
                critical += 1
    rate = grounded * 100 / max(1, total)
    return (f"  Grounded: {grounded}/{total} ({rate:.0f}%) | "
            f"Critical decay: {critical} lessons\n"
            f"  Run: python3 tools/external_grounding_check.py --decay")


def main():
    args = sys.argv[1:]
    staged_mode = "--staged" in args
    enforce_mode = "--enforce" in args
    as_json = "--json" in args
    decay_mode = "--decay" in args
    baseline_n = 20
    top_n = 15

    for i, a in enumerate(args):
        if a == "--baseline" and i + 1 < len(args):
            baseline_n = int(args[i + 1])
        if a == "--top" and i + 1 < len(args):
            top_n = int(args[i + 1])

    if decay_mode:
        grounding_decay_report(top_n)
        return

    if staged_mode:
        lessons = get_staged_lessons()
        if not lessons:
            return  # nothing staged, silent exit for check.sh
    else:
        lessons = get_recent_lessons(baseline_n)

    results = [scan_lesson(p) for p in lessons]

    if as_json:
        summary = {
            "total": len(results),
            "with_external": sum(1 for r in results if r.get("has_external")),
            "without_external": sum(1 for r in results if not r.get("has_external")),
            "grounding_rate": (
                sum(1 for r in results if r.get("has_external")) / max(1, len(results))
            ),
            "lessons": results,
        }
        print(json.dumps(summary, indent=2, default=str))
        return

    if staged_mode:
        # check.sh hook mode: check for ungrounded lessons
        # In enforce mode (--enforce), also check for explicit External: field
        # A lesson passes if it has external references OR an explicit External: field
        # (External: none — <reason> is an accepted conscious opt-out)
        ungrounded = []
        for r in results:
            if r.get("has_external"):
                continue
            # In enforce mode, check if lesson has explicit External: header
            lesson_path = LESSON_DIR / r["file"]
            if enforce_mode and has_external_field(lesson_path):
                continue  # explicit External: field present (even "none — reason")
            ungrounded.append(r)

        if ungrounded:
            for r in ungrounded:
                label = "FAIL" if enforce_mode else "NOTICE"
                print(f"  F-GND1 {label}: {r['file']} has no external references — "
                      f"add External: header (L-1125, F-GND1, L-601)")
                print(f"    Internal refs: {r['internal_count']} | External: 0")
                print(f"    Add: 'External: <url, paper, benchmark, named theory>'")
                print(f"    Or:  'External: none — <reason this is purely internal>'")
        # report pass/fail
        total = len(results)
        if ungrounded:
            label = "FAIL" if enforce_mode else "NOTICE"
            print(f"  F-GND1 external grounding: {len(ungrounded)}/{total} lesson(s) "
                  f"without external refs ({label})")
            if enforce_mode:
                sys.exit(1)
        else:
            print(f"  F-GND1 external grounding: PASS ({total} lesson(s), all grounded or explicitly marked)")
        return

    # Baseline report mode
    with_ext = sum(1 for r in results if r.get("has_external"))
    without_ext = len(results) - with_ext
    rate = with_ext / max(1, len(results)) * 100

    print(f"=== EXTERNAL GROUNDING CHECK — F-GND1, L-1125 ===\n")
    print(f"  Lessons scanned: {len(results)} (most recent)")
    print(f"  With external refs: {with_ext} ({rate:.0f}%)")
    print(f"  Without external refs: {without_ext} ({100-rate:.0f}%)")
    print()

    # Show ungrounded lessons
    if without_ext > 0:
        print(f"--- Ungrounded lessons (no external references) ---")
        for r in results:
            if not r.get("has_external"):
                print(f"  {r['file']}  (internal: {r['internal_count']}, external: 0)")

    # Show grounded lessons with what they cite
    if with_ext > 0:
        print(f"\n--- Grounded lessons (have external references) ---")
        for r in results:
            if r.get("has_external"):
                types = ", ".join(f"{ref['type']}({ref['count']})" for ref in r["external_refs"])
                ratio = r["grounding_ratio"]
                print(f"  {r['file']}  ext: {r['external_count']} [{types}]  ratio: {ratio:.2f}")

    print(f"\n  Grounding rate: {rate:.0f}% (target: increase from baseline)")
    print(f"  Wired into check.sh: --staged mode emits NOTICE for ungrounded lessons")


if __name__ == "__main__":
    main()
