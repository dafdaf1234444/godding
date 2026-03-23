#!/usr/bin/env python3
"""
genesis_extract.py — Produce a compact genesis bundle for daughter swarm (L-1471).

A daughter swarm needs 0.91% of parent repo (439KB) to orient and function.
This tool extracts 3 layers + core tools into a self-contained directory:

  Layer 1 — Identity (genome, lossless): CORE.md, PHILOSOPHY.md, SWARM.md
  Layer 2 — Orientation (epigenetics): PRINCIPLES.md, DEPS.md, CHALLENGES.md,
            INVARIANTS.md, CROSS.md, EXPECT.md, DISTILL.md, VERIFY.md, INDEX.md
  Layer 3 — Hub lessons (lossy scaffold): top-N lessons by citation centrality
  Layer 4 — Core tools: orient.py, dispatch_optimizer.py, compact.py, etc.

Usage:
    python3 tools/genesis_extract.py                    # extract to workspace/genesis-bundle/
    python3 tools/genesis_extract.py --out /tmp/daughter # custom output dir
    python3 tools/genesis_extract.py --top 50           # top-50 hub lessons (default 100)
    python3 tools/genesis_extract.py --no-tools         # skip tools layer
    python3 tools/genesis_extract.py --dry-run          # show what would be extracted
    python3 tools/genesis_extract.py --json             # output manifest as JSON
"""

import argparse
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Layer 1: Identity (genome) — lossless transfer
IDENTITY_FILES = [
    ("beliefs/CORE.md", "beliefs/CORE.md"),
    ("beliefs/PHILOSOPHY.md", "beliefs/PHILOSOPHY.md"),
    ("SWARM.md", "SWARM.md"),
]

# Layer 2: Orientation (epigenetics) — distilled rules
# Split into essential (boot-critical) and reference (enrichment)
ORIENTATION_ESSENTIAL = [
    ("memory/PRINCIPLES.md", "memory/PRINCIPLES.md"),
    ("beliefs/DEPS.md", "beliefs/DEPS.md"),
    ("beliefs/INVARIANTS.md", "beliefs/INVARIANTS.md"),
    ("beliefs/CROSS.md", "beliefs/CROSS.md"),
    ("memory/INDEX.md", "memory/INDEX.md"),
    ("tasks/FRONTIER.md", "tasks/FRONTIER.md"),
]
ORIENTATION_REFERENCE = [
    ("beliefs/CHALLENGES.md", "beliefs/CHALLENGES.md"),
    ("memory/EXPECT.md", "memory/EXPECT.md"),
    ("memory/DISTILL.md", "memory/DISTILL.md"),
    ("memory/VERIFY.md", "memory/VERIFY.md"),
    ("domains/ISOMORPHISM-ATLAS.md", "domains/ISOMORPHISM-ATLAS.md"),
]

# Layer 4: Core tools — minimum viable toolset for orient + dispatch
CORE_TOOLS = [
    "tools/orient.py",
    "tools/orient_checks.py",
    "tools/orient_state.py",
    "tools/orient_sections.py",
    "tools/orient_analysis.py",
    "tools/orient_monitors.py",
    "tools/dispatch_optimizer.py",
    "tools/compact.py",
    "tools/validate_beliefs.py",
    "tools/sync_state.py",
    "tools/cell_blueprint.py",
    "tools/open_lane.py",
    "tools/close_lane.py",
    "tools/claim.py",
    "tools/genesis_seeds.py",
    "tools/genesis_extract.py",
    "tools/check.sh",
]


def _citation_graph():
    """Build in-degree map from lesson Cites: headers and body L-NNN refs."""
    in_degree = defaultdict(int)
    lessons_dir = ROOT / "memory" / "lessons"
    if not lessons_dir.exists():
        return in_degree

    lid_pattern = re.compile(r"L-(\d+)")
    for f in lessons_dir.glob("L-*.md"):
        text = f.read_text(errors="replace")
        # Extract all L-NNN references
        refs = set()
        for m in lid_pattern.finditer(text):
            ref = f"L-{m.group(1)}"
            # Don't count self-references
            own_id_match = re.match(r"L-(\d+)", f.stem)
            if own_id_match and ref == f"L-{own_id_match.group(1)}":
                continue
            refs.add(ref)
        for ref in refs:
            in_degree[ref] += 1
    return in_degree


def _domain_reach(lessons_dir):
    """Map lesson ID to set of citing domains."""
    reach = defaultdict(set)
    lid_pattern = re.compile(r"L-(\d+)")
    domain_pattern = re.compile(r"\*\*Domain\*\*:\s*(\S+)")

    for f in lessons_dir.glob("L-*.md"):
        text = f.read_text(errors="replace")
        # Get this lesson's domain
        dm = domain_pattern.search(text[:500])
        domain = dm.group(1) if dm else "unknown"
        # Find all L-NNN refs and add this domain to their reach
        for m in lid_pattern.finditer(text):
            ref = f"L-{m.group(1)}"
            reach[ref].add(domain)
    return reach


def select_hub_lessons(top_n=100):
    """Select top-N lessons by citation centrality (in-degree * domain reach)."""
    lessons_dir = ROOT / "memory" / "lessons"
    if not lessons_dir.exists():
        return []

    in_degree = _citation_graph()
    reach = _domain_reach(lessons_dir)

    # Score: in_degree * log2(domain_reach + 1)
    import math
    scores = {}
    for lid, deg in in_degree.items():
        dr = len(reach.get(lid, set()))
        scores[lid] = deg * math.log2(dr + 1) if dr > 0 else deg

    # Sort by score descending, take top N
    ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_n]

    results = []
    for lid, score in ranked:
        # Find the file
        num = re.match(r"L-(\d+)", lid)
        if not num:
            continue
        fpath = lessons_dir / f"{lid}.md"
        if not fpath.exists():
            continue
        results.append({
            "id": lid,
            "path": str(fpath.relative_to(ROOT)),
            "in_degree": in_degree[lid],
            "domain_reach": len(reach.get(lid, set())),
            "score": round(score, 1),
        })
    return results


def extract_genesis(out_dir, top_n=100, include_tools=True, minimal=False,
                    dry_run=False):
    """Extract genesis bundle to out_dir. Returns manifest dict."""
    out = Path(out_dir)
    manifest = {
        "layers": {},
        "total_files": 0,
        "total_bytes": 0,
    }

    def _copy(src_rel, dst_rel, layer_name):
        src = ROOT / src_rel
        if not src.exists():
            return None
        dst = out / dst_rel
        size = src.stat().st_size
        entry = {"src": src_rel, "dst": dst_rel, "bytes": size}

        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))

        if layer_name not in manifest["layers"]:
            manifest["layers"][layer_name] = {"files": [], "bytes": 0}
        manifest["layers"][layer_name]["files"].append(entry)
        manifest["layers"][layer_name]["bytes"] += size
        manifest["total_files"] += 1
        manifest["total_bytes"] += size
        return entry

    # Layer 1: Identity
    for src, dst in IDENTITY_FILES:
        _copy(src, dst, "identity")

    # Layer 2: Orientation (essential always, reference unless --minimal)
    for src, dst in ORIENTATION_ESSENTIAL:
        _copy(src, dst, "orientation")
    if not minimal:
        for src, dst in ORIENTATION_REFERENCE:
            _copy(src, dst, "orientation_ref")

    # Layer 3: Hub lessons
    hubs = select_hub_lessons(top_n)
    manifest["hub_lesson_count"] = len(hubs)
    manifest["hub_lessons_top5"] = [h["id"] for h in hubs[:5]]
    for hub in hubs:
        _copy(hub["path"], hub["path"], "hub_lessons")

    # Layer 4: Core tools (only explicit list — deps are optional per L-1467)
    if include_tools:
        for tool_path in CORE_TOOLS:
            _copy(tool_path, tool_path, "core_tools")

    # Write bridge files and init git for daughter
    if not dry_run:
        _write_daughter_bridge(out)
        _init_daughter_git(out)

    # Summary
    manifest["compression_ratio"] = f"{manifest['total_bytes'] / 1024:.0f}KB"

    return manifest


def _find_tool_deps():
    """Find Python files in tools/ that core tools import."""
    deps = set()
    import_pattern = re.compile(r"(?:from|import)\s+([\w.]+)")
    tools_dir = ROOT / "tools"

    for tool_path in CORE_TOOLS:
        src = ROOT / tool_path
        if not src.exists() or not src.suffix == ".py":
            continue
        text = src.read_text(errors="replace")
        for m in import_pattern.finditer(text):
            mod = m.group(1).split(".")[0]
            candidate = tools_dir / f"{mod}.py"
            if candidate.exists() and str(candidate.relative_to(ROOT)) not in CORE_TOOLS:
                deps.add(str(candidate.relative_to(ROOT)))
    return sorted(deps)


def _init_daughter_git(out_dir):
    """Initialize git repo in daughter bundle so orient.py can function."""
    import subprocess
    try:
        subprocess.run(["git", "init"], cwd=str(out_dir),
                       capture_output=True, timeout=10)
        subprocess.run(["git", "add", "."], cwd=str(out_dir),
                       capture_output=True, timeout=10)
        subprocess.run(["git", "commit", "-m", "Genesis: daughter swarm born"],
                       cwd=str(out_dir), capture_output=True, timeout=10)
    except Exception:
        pass  # Git init is best-effort


def _write_daughter_bridge(out_dir):
    """Write a minimal CLAUDE.md bridge file for the daughter swarm."""
    bridge = out_dir / "CLAUDE.md"
    bridge.write_text(
        "# Daughter Swarm (Genesis Bundle)\n\n"
        "This is a genesis bundle extracted from a parent swarm.\n"
        "Read `SWARM.md` for the full protocol.\n\n"
        "## Quick start\n"
        "- `python3 tools/orient.py` — orient\n"
        "- `python3 tools/dispatch_optimizer.py` — choose domain work\n"
        "- Read `beliefs/CORE.md` for identity\n"
        "- Read `beliefs/PHILOSOPHY.md` for claims about what you are\n"
        "- Read `memory/PRINCIPLES.md` for distilled rules\n"
        "- Lessons in `memory/lessons/` are your hub knowledge scaffold\n\n"
        "You are a daughter cell. Grow your own lessons, principles, and experiments.\n"
        "Your parent's raw phenotype (1200+ lessons, 30MB experiments) was not transferred.\n"
        "You inherit genome (identity) + epigenetics (principles) + hub knowledge.\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Extract compact genesis bundle")
    parser.add_argument("--out", default=str(ROOT / "workspace" / "genesis-bundle"),
                        help="Output directory (default: workspace/genesis-bundle/)")
    parser.add_argument("--top", type=int, default=100,
                        help="Number of hub lessons to include (default: 100)")
    parser.add_argument("--no-tools", action="store_true",
                        help="Skip core tools layer")
    parser.add_argument("--minimal", action="store_true",
                        help="Minimal bundle: skip reference orientation files + ISO atlas")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be extracted without copying")
    parser.add_argument("--json", action="store_true",
                        help="Output manifest as JSON")
    args = parser.parse_args()

    if not args.dry_run and os.path.exists(args.out):
        shutil.rmtree(args.out)

    manifest = extract_genesis(
        args.out,
        top_n=args.top,
        include_tools=not args.no_tools,
        minimal=args.minimal,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(manifest, indent=2))
    else:
        print(f"{'[DRY RUN] ' if args.dry_run else ''}Genesis bundle → {args.out}")
        print()
        for layer, info in manifest["layers"].items():
            kb = info["bytes"] / 1024
            print(f"  {layer:15s}  {len(info['files']):3d} files  {kb:7.1f} KB")
        print(f"  {'─' * 40}")
        print(f"  {'TOTAL':15s}  {manifest['total_files']:3d} files  "
              f"{manifest['total_bytes'] / 1024:7.1f} KB")
        print()
        if manifest.get("hub_lessons_top5"):
            print(f"  Hub lessons (top 5): {', '.join(manifest['hub_lessons_top5'])}")
        print(f"  Compression: {manifest['compression_ratio']} "
              f"(target <500KB for functional daughter)")


if __name__ == "__main__":
    main()
