#!/usr/bin/env python3
"""
genesis_evolve.py — Propose genesis template improvements from child swarm data.

Usage:
    python3 tools/genesis_evolve.py analyze
    python3 tools/genesis_evolve.py report
    python3 tools/genesis_evolve.py bundle [--session=SNNN] [--out=PATH]

Reads integration logs and child evaluation data to identify patterns
that could improve the genesis template. This is the "selection" step
in the genetic algorithm: what worked in children should inform the
template that produces the next generation.

F38: Colony-level selection to improve the genesis template.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHILDREN_DIR = REPO_ROOT / "experiments" / "children"
INTEGRATION_LOG_DIR = REPO_ROOT / "experiments" / "integration-log"
MERGE_REPORTS_DIR = REPO_ROOT / "experiments" / "merge-reports"
SESSION_LOG_PATH = REPO_ROOT / "memory" / "SESSION-LOG.md"

SESSION_RE = re.compile(r"(?:^\|?\s*S|S)(\d{3,})\b", re.MULTILINE)


def _current_session() -> int | None:
    if not SESSION_LOG_PATH.exists():
        return None
    text = SESSION_LOG_PATH.read_text()
    nums = [int(m) for m in SESSION_RE.findall(text)]
    return max(nums) if nums else None


def _bundle_files() -> tuple[list[Path], str]:
    genesis = REPO_ROOT / "workspace" / "genesis.sh"
    core = REPO_ROOT / "beliefs" / "CORE.md"
    principles = REPO_ROOT / "beliefs" / "PRINCIPLES.md"
    principles_note = "beliefs/PRINCIPLES.md"
    if not principles.exists():
        alt = REPO_ROOT / "memory" / "PRINCIPLES.md"
        if alt.exists():
            principles = alt
            principles_note = "memory/PRINCIPLES.md"
    files = [genesis, core, principles]
    missing = [p for p in files if not p.exists()]
    if missing:
        missing_list = ", ".join(str(p) for p in missing)
        raise FileNotFoundError(f"Missing bundle file(s): {missing_list}")
    return files, principles_note


def compute_genesis_bundle_hash() -> tuple[str, list[Path], str]:
    files, principles_note = _bundle_files()
    hasher = hashlib.sha256()
    for path in files:
        hasher.update(path.read_bytes())
    return hasher.hexdigest(), files, principles_note


def write_genesis_bundle_hash(session: str, out_path: Path | None = None) -> tuple[str, Path, list[Path], str]:
    bundle_hash, files, principles_note = compute_genesis_bundle_hash()
    out = out_path or (REPO_ROOT / "workspace" / f"genesis-bundle-{session}.hash")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"{bundle_hash}\n")
    return bundle_hash, out, files, principles_note


def analyze_children() -> dict:
    """Analyze all children to find patterns for genesis improvement."""
    swarm_test = REPO_ROOT / "tools" / "swarm_test.py"
    results = {
        "children_analyzed": 0,
        "total_novel_rules": 0,
        "total_novel_questions": 0,
        "viability_scores": [],
        "common_patterns": [],
        "genesis_proposals": [],
    }

    if not CHILDREN_DIR.exists():
        return results

    children = [d for d in CHILDREN_DIR.iterdir() if d.is_dir()]
    results["children_analyzed"] = len(children)

    for child_dir in sorted(children):
        # Evaluate
        r = subprocess.run(
            ["python3", str(swarm_test), "evaluate", str(child_dir)],
            capture_output=True, text=True
        )
        vm = re.search(r"Viability: (\d+)/4", r.stdout)
        score = int(vm.group(1)) if vm else 0
        results["viability_scores"].append({
            "name": child_dir.name,
            "score": score,
        })

    # Read integration logs
    if INTEGRATION_LOG_DIR.exists():
        for f in INTEGRATION_LOG_DIR.glob("*.json"):
            data = json.loads(f.read_text())
            results["total_novel_rules"] += data.get("novel_rules", 0)
            results["total_novel_questions"] += data.get("novel_questions", 0)

    # Analyze patterns across children
    avg_viability = (
        sum(v["score"] for v in results["viability_scores"])
        / len(results["viability_scores"])
        if results["viability_scores"] else 0
    )

    # Generate proposals based on data
    if avg_viability < 3.0:
        results["genesis_proposals"].append({
            "type": "structure",
            "proposal": "Children average < 3/4 viability. Consider adding a NEXT.md template to genesis to improve first-session onboarding.",
            "evidence": f"avg viability = {avg_viability:.1f}/4",
        })

    # Check if children commonly fail to resolve frontier questions
    low_resolve = [
        v for v in results["viability_scores"]
        if v["score"] < 4
    ]
    if len(low_resolve) > len(results["viability_scores"]) * 0.5:
        results["genesis_proposals"].append({
            "type": "frontier",
            "proposal": "Most children don't resolve F1 in first session. Consider making F1 auto-resolvable or replacing with a more tractable first question.",
            "evidence": f"{len(low_resolve)}/{len(results['viability_scores'])} children below 4/4",
        })

    # Check if novel rules are being produced
    if results["total_novel_rules"] > 0:
        results["genesis_proposals"].append({
            "type": "knowledge",
            "proposal": f"Children producing novel rules ({results['total_novel_rules']} total). Evolution pipeline is working — continue spawning domain-specific children.",
            "evidence": f"{results['total_novel_rules']} novel rules from {results['children_analyzed']} children",
        })

    # Check principles template in genesis
    genesis = REPO_ROOT / "workspace" / "genesis.sh"
    if genesis.exists():
        genesis_text = genesis.read_text()
        if "PRINCIPLES.md" not in genesis_text:
            results["genesis_proposals"].append({
                "type": "missing_file",
                "proposal": "Genesis doesn't create PRINCIPLES.md. Children can't track building blocks without it.",
                "evidence": "PRINCIPLES.md absent from genesis template",
            })

    return results


def print_report(results: dict):
    """Print the genesis evolution report."""
    print("=== GENESIS EVOLUTION REPORT ===\n")
    print(f"Children analyzed: {results['children_analyzed']}")
    print(f"Novel rules produced: {results['total_novel_rules']}")
    print(f"Novel questions produced: {results['total_novel_questions']}")

    if results["viability_scores"]:
        print(f"\n--- Viability Scores ---")
        for v in sorted(results["viability_scores"], key=lambda x: x["score"], reverse=True):
            bar = "#" * v["score"] + "." * (4 - v["score"])
            print(f"  {v['name']:<25} [{bar}] {v['score']}/4")

        avg = sum(v["score"] for v in results["viability_scores"]) / len(results["viability_scores"])
        print(f"\n  Average: {avg:.1f}/4")

    if results["genesis_proposals"]:
        print(f"\n--- Proposals for Genesis v5 ---")
        for i, p in enumerate(results["genesis_proposals"], 1):
            print(f"\n  {i}. [{p['type'].upper()}] {p['proposal']}")
            print(f"     Evidence: {p['evidence']}")
    else:
        print("\n  No proposals — genesis template is performing well.")

    # Current genesis version
    genesis = REPO_ROOT / "workspace" / "genesis.sh"
    if genesis.exists():
        first_line = genesis.read_text().splitlines()[1] if genesis.read_text() else ""
        print(f"\n  Current: {first_line.strip()}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd in ("analyze", "report"):
        results = analyze_children()
        print_report(results)
    elif cmd == "bundle":
        session = None
        out_path = None
        for arg in sys.argv[2:]:
            if arg.startswith("--session="):
                session = arg.split("=", 1)[1].strip()
            elif arg.startswith("--out="):
                out_path = Path(arg.split("=", 1)[1].strip())

        if session is None:
            current = _current_session()
            if current is None:
                print("ERROR: could not determine session (pass --session=SNNN)", file=sys.stderr)
                sys.exit(1)
            session = f"S{current}"
        elif re.fullmatch(r"\d+", session):
            session = f"S{session}"

        bundle_hash, out, files, principles_note = write_genesis_bundle_hash(session, out_path)
        rel_files = [str(p.relative_to(REPO_ROOT)) for p in files]
        print("=== GENESIS BUNDLE HASH ===")
        print(f"Session: {session}")
        print(f"Hash: {bundle_hash}")
        print(f"Files: {', '.join(rel_files)}")
        if principles_note != "beliefs/PRINCIPLES.md":
            print(f"Note: using {principles_note} (beliefs/PRINCIPLES.md not found)")
        print(f"Wrote: {out}")
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
