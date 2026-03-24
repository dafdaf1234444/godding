#!/usr/bin/env python3
"""Tool Reliability Auditor (Goldman's reliabilism, F-EPIS1 L-1390 gap).

Measures tool-level reliability × integration. A tool can't be epistemically
justified if (a) its outputs are frequently falsified, or (b) nothing reads
its output. Combines both into a single R-score per tool.

R[tool] = truth_rate × integration_rate
  truth_rate     = 1 - (falsified_outputs / total_outputs)
  integration_rate = downstream_readers / expected_readers

Usage:
    python3 tools/tool_reliability.py              # summary report
    python3 tools/tool_reliability.py --json       # JSON output
    python3 tools/tool_reliability.py --detail     # per-tool detail
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

TOOLS_DIR = Path("tools")
LESSON_DIR = Path("memory/lessons")


def discover_tools() -> list[dict]:
    """Find all Python tools and their metadata."""
    tools = []
    for p in sorted(TOOLS_DIR.glob("*.py")):
        if p.name.startswith("__"):
            continue
        tools.append({
            "name": p.name,
            "path": str(p),
        })
    return tools


def compute_import_graph() -> dict[str, list[str]]:
    """Map each tool → tools it imports/calls (downstream readers)."""
    graph = defaultdict(set)  # tool_name → set of tools that reference it
    tool_names = {p.name for p in TOOLS_DIR.glob("*.py") if not p.name.startswith("__")}

    for p in TOOLS_DIR.glob("*.py"):
        if p.name.startswith("__"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for other in tool_names:
            if other == p.name:
                continue
            stem = other.replace(".py", "")
            # Check for import or subprocess reference
            if stem in text or other in text:
                graph[other].add(p.name)

    # Also check bridge files and check.sh for tool references
    for ref_file in ["tools/check.sh", "tools/orient.py", "CLAUDE.md", "AGENTS.md"]:
        rp = Path(ref_file)
        if not rp.exists():
            continue
        try:
            text = rp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for tn in tool_names:
            stem = tn.replace(".py", "")
            if tn in text or f"tools/{tn}" in text:
                graph[tn].add(f"[{rp.name}]")

    return {k: sorted(v) for k, v in graph.items()}


def parse_lesson_tool_refs() -> dict[str, list[str]]:
    """Map each tool → lessons that reference it (evidence of usage)."""
    tool_lessons = defaultdict(list)
    tool_names = {p.stem for p in TOOLS_DIR.glob("*.py") if not p.name.startswith("__")}

    for lp in sorted(LESSON_DIR.glob("L-*.md")):
        try:
            text = lp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        lid = lp.stem
        for stem in tool_names:
            if f"{stem}.py" in text or f"tools/{stem}" in text:
                tool_lessons[f"{stem}.py"].append(lid)

    return dict(tool_lessons)


def count_falsified_refs(tool_name: str, lesson_refs: list[str]) -> int:
    """Count how many lessons referencing this tool are themselves falsified."""
    count = 0
    for lid in lesson_refs:
        lp = LESSON_DIR / f"{lid}.md"
        if not lp.exists():
            continue
        try:
            title = lp.read_text(encoding="utf-8", errors="replace").split("\n")[0]
        except Exception:
            continue
        if "FALSIFIED" in title.upper():
            count += 1
    return count


def compute_tool_ages_batch() -> dict[str, int | None]:
    """Batch-fetch last-modified session for all tools (single git call)."""
    ages = {}
    try:
        result = subprocess.run(
            ["git", "log", "--name-only", "--format=%s", "--diff-filter=M", "-200"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return ages
        current_session = None
        for line in result.stdout.strip().split("\n"):
            m = re.search(r"\[S(\d+)\]", line)
            if m:
                current_session = int(m.group(1))
            elif line.startswith("tools/") and line.endswith(".py") and current_session:
                name = line.split("/")[-1]
                if name not in ages:
                    ages[name] = current_session
    except Exception:
        pass
    return ages


def audit_tools() -> dict:
    """Run full tool reliability audit."""
    tools = discover_tools()
    import_graph = compute_import_graph()
    lesson_refs = parse_lesson_tool_refs()

    results = []
    n_tools = len(tools)
    tool_ages = compute_tool_ages_batch()

    for t in tools:
        name = t["name"]
        readers = import_graph.get(name, [])
        lessons = lesson_refs.get(name, [])
        n_lessons = len(lessons)
        n_falsified = count_falsified_refs(name, lessons) if lessons else 0
        n_readers = len(readers)

        # Truth rate: 1 - falsified/total (or 1.0 if no lesson references)
        truth_rate = (n_lessons - n_falsified) / n_lessons if n_lessons > 0 else None

        # Integration rate: normalized reader count
        # Expected: at least 1 reader (orient, check.sh, or another tool)
        integration_rate = min(n_readers / 3.0, 1.0)  # 3 readers = fully integrated

        # R-score
        if truth_rate is not None:
            r_score = truth_rate * integration_rate
        else:
            r_score = integration_rate * 0.5  # penalty for no lesson evidence

        last_session = tool_ages.get(name)

        results.append({
            "name": name,
            "readers": readers,
            "n_readers": n_readers,
            "lesson_refs": lessons[:10],  # cap for readability
            "n_lesson_refs": n_lessons,
            "n_falsified": n_falsified,
            "truth_rate": round(truth_rate, 3) if truth_rate is not None else None,
            "integration_rate": round(integration_rate, 3),
            "r_score": round(r_score, 3),
            "last_session": last_session,
        })

    # Sort by R-score ascending (worst first)
    results.sort(key=lambda x: x["r_score"])

    # Classify
    isolated = [r for r in results if r["n_readers"] == 0]
    write_only = [r for r in results if r["n_readers"] == 0 and r["n_lesson_refs"] > 0]
    low_truth = [r for r in results if r["truth_rate"] is not None and r["truth_rate"] < 0.85]
    well_integrated = [r for r in results if r["n_readers"] >= 3]

    return {
        "n_tools": n_tools,
        "n_isolated": len(isolated),
        "n_write_only": len(write_only),
        "n_low_truth": len(low_truth),
        "n_well_integrated": len(well_integrated),
        "mean_r_score": round(sum(r["r_score"] for r in results) / len(results), 3) if results else 0,
        "mean_integration": round(sum(r["integration_rate"] for r in results) / len(results), 3) if results else 0,
        "tools": results,
        "isolated_tools": [r["name"] for r in isolated],
        "write_only_tools": [r["name"] for r in write_only],
        "low_truth_tools": [{"name": r["name"], "truth_rate": r["truth_rate"]} for r in low_truth],
    }


def print_report(data: dict, detail: bool = False):
    """Print human-readable report."""
    print(f"=== TOOL RELIABILITY AUDIT ({data['n_tools']} tools) ===")
    print(f"  Mean R-score: {data['mean_r_score']}")
    print(f"  Mean integration: {data['mean_integration']}")
    print(f"  Isolated (0 readers): {data['n_isolated']}")
    print(f"  Write-only (referenced in lessons but no tool reads): {data['n_write_only']}")
    print(f"  Low truth rate (<85%): {data['n_low_truth']}")
    print(f"  Well-integrated (≥3 readers): {data['n_well_integrated']}")
    print()

    if data["low_truth_tools"]:
        print("--- LOW TRUTH RATE (reliabilism red flags) ---")
        for t in data["low_truth_tools"]:
            print(f"  ⚠ {t['name']}: {t['truth_rate']:.1%}")
        print()

    if data["write_only_tools"]:
        print("--- WRITE-ONLY TOOLS (integration gap) ---")
        for name in data["write_only_tools"][:10]:
            print(f"  ○ {name}")
        if len(data["write_only_tools"]) > 10:
            print(f"  ... and {len(data['write_only_tools']) - 10} more")
        print()

    if data["isolated_tools"]:
        print(f"--- ISOLATED TOOLS ({len(data['isolated_tools'])} with 0 readers) ---")
        for name in data["isolated_tools"][:15]:
            print(f"  ○ {name}")
        if len(data["isolated_tools"]) > 15:
            print(f"  ... and {len(data['isolated_tools']) - 15} more")
        print()

    if detail:
        print("--- FULL DETAIL (sorted by R-score ascending) ---")
        for r in data["tools"]:
            truth_str = f"{r['truth_rate']:.1%}" if r["truth_rate"] is not None else "N/A"
            print(f"  {r['name']:40s} R={r['r_score']:.3f}  truth={truth_str}  "
                  f"integ={r['integration_rate']:.3f}  readers={r['n_readers']}  "
                  f"lessons={r['n_lesson_refs']}  falsif={r['n_falsified']}")

    # Top 10 most reliable + integrated
    top = sorted(data["tools"], key=lambda x: -x["r_score"])[:10]
    print("--- TOP 10 (highest R-score) ---")
    for r in top:
        truth_str = f"{r['truth_rate']:.1%}" if r["truth_rate"] is not None else "N/A"
        print(f"  {r['name']:40s} R={r['r_score']:.3f}  truth={truth_str}  "
              f"readers={r['n_readers']}  lessons={r['n_lesson_refs']}")


def main():
    parser = argparse.ArgumentParser(description="Tool reliability auditor (Goldman's reliabilism)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--detail", action="store_true", help="Per-tool detail")
    args = parser.parse_args()

    data = audit_tools()

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_report(data, detail=args.detail)


if __name__ == "__main__":
    main()
