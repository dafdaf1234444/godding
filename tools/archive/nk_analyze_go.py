#!/usr/bin/env python3
"""
nk_analyze_go.py — NK landscape analysis for Go projects.

Usage:
    python3 tools/nk_analyze_go.py <go_project_dir>
    python3 tools/nk_analyze_go.py <go_project_dir> --json
    python3 tools/nk_analyze_go.py <go_project_dir> --verbose
    python3 tools/nk_analyze_go.py <go_project_dir> --suggest-refactor

Analyzes internal package dependencies of a Go module and computes:
- N (number of packages), K_total (edges), K_avg, K/N, K_max
- Cycle detection
- Composite score: K_avg * N + Cycles
- Burden score: Cycles + 0.1 * N
- Architecture classification

Works statically — parses import statements from .go files without
needing the Go compiler installed. Requires only a Go module directory
with a go.mod file (or any directory tree containing .go files).

Examples:
    python3 tools/nk_analyze_go.py workspace/gin
    python3 tools/nk_analyze_go.py workspace/gin --verbose
    python3 tools/nk_analyze_go.py workspace/gin --json
    python3 tools/nk_analyze_go.py workspace/gin --suggest-refactor
"""

import json as json_mod
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def find_module_path(project_dir: Path) -> str | None:
    """Extract the module path from go.mod.

    Returns the module path string (e.g., 'github.com/gin-gonic/gin')
    or None if no go.mod found.
    """
    go_mod = project_dir / "go.mod"
    if not go_mod.exists():
        return None

    try:
        text = go_mod.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("module "):
                return line[len("module "):].strip()
    except Exception:
        pass
    return None


def list_packages(project_dir: Path) -> dict[str, list[Path]]:
    """List all Go packages (directories containing .go files).

    Returns dict mapping package import-path-suffix to list of .go file paths.
    Skips test files, vendor/, testdata/, and hidden directories.
    """
    packages: dict[str, list[Path]] = {}
    skip_dirs = {
        "vendor", "testdata", "internal_test", ".git",
        "node_modules", "examples", "example", "docs",
        "_examples", "cmd", "tools",
    }

    for root, dirs, files in os.walk(project_dir):
        # Skip hidden dirs and known non-source dirs
        dirs[:] = [
            d for d in dirs
            if d not in skip_dirs and not d.startswith(".")
        ]

        go_files = []
        for f in sorted(files):
            if f.endswith(".go") and not f.endswith("_test.go"):
                go_files.append(Path(root) / f)

        if go_files:
            # Package path relative to project root
            rel_path = Path(root).relative_to(project_dir)
            pkg_suffix = str(rel_path).replace(os.sep, "/")
            if pkg_suffix == ".":
                pkg_suffix = ""  # root package
            packages[pkg_suffix] = go_files

    return packages


def extract_package_name(filepath: Path) -> str | None:
    """Extract the 'package X' declaration from a Go file."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            # Skip comments
            if line.startswith("//") or line.startswith("/*"):
                continue
            # Skip build constraints
            if line.startswith("//go:build") or line.startswith("// +build"):
                continue
            m = re.match(r'^package\s+(\w+)', line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


def extract_imports(filepath: Path) -> list[str]:
    """Extract all import paths from a Go source file.

    Handles both single imports and grouped imports:
        import "fmt"
        import (
            "fmt"
            "net/http"
            alias "github.com/foo/bar"
        )

    Returns a list of import path strings.
    """
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    imports = []

    # Remove block comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    # Remove line comments (but preserve the line structure)
    text = re.sub(r'//[^\n]*', '', text)

    # Match grouped imports: import ( ... )
    grouped_pattern = re.compile(r'import\s*\((.*?)\)', re.DOTALL)
    for match in grouped_pattern.finditer(text):
        block = match.group(1)
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            # Handle: "path", alias "path", . "path", _ "path"
            m = re.match(r'(?:\w+\s+|[._]\s+)?"([^"]+)"', line)
            if m:
                imports.append(m.group(1))

    # Match single imports: import "path" or import alias "path"
    single_pattern = re.compile(r'import\s+(?:\w+\s+)?"([^"]+)"')
    for match in single_pattern.finditer(text):
        imp = match.group(1)
        # Don't double-count if it was inside a group
        if imp not in imports:
            imports.append(imp)

    return imports


def filter_internal_imports(
    imports: list[str],
    module_path: str,
    known_packages: set[str],
) -> list[str]:
    """Filter imports to only internal package references.

    An import is internal if it starts with the module path.
    Returns package suffixes (relative to module root).
    """
    internal = []
    prefix = module_path + "/"

    for imp in imports:
        if imp == module_path:
            # Import of the root package itself
            if "" in known_packages:
                internal.append("")
        elif imp.startswith(prefix):
            suffix = imp[len(prefix):]
            if suffix in known_packages:
                internal.append(suffix)

    return internal


def count_lines(filepath: Path) -> int:
    """Count lines in a file."""
    try:
        return len(filepath.read_text(encoding="utf-8", errors="replace").splitlines())
    except Exception:
        return 0


def detect_cycles(deps: dict[str, list[str]]) -> list[list[str]]:
    """Find all cycles in the dependency graph using DFS.

    Same algorithm as nk_analyze.py for consistency.
    """
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in deps.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                min_idx = cycle[:-1].index(min(cycle[:-1]))
                normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
                if normalized not in cycles:
                    cycles.append(normalized)

        path.pop()
        rec_stack.discard(node)

    for node in sorted(deps.keys()):
        if node not in visited:
            dfs(node)

    return cycles


def classify_architecture(
    n: int, k_avg: float, k_max: int, cycles: int, hub_pct: float
) -> str:
    """Classify the project's architecture pattern.

    Same classification as nk_analyze.py for cross-language comparability.
    """
    if n <= 3:
        return "monolith"
    if cycles > 3:
        return "tangled"
    if hub_pct > 0.5 and k_max > n * 0.3:
        return "hub-and-spoke"
    if k_avg > 2.0:
        return "framework"
    if k_max > n * 0.4:
        return "registry"
    if hub_pct > 0.3:
        return "facade"
    return "distributed"


def pkg_display_name(pkg_suffix: str) -> str:
    """Create a display name for a package suffix."""
    if pkg_suffix == "":
        return "(root)"
    return pkg_suffix


def analyze_go_project(project_dir: Path, verbose: bool = False) -> dict:
    """Perform full NK analysis on a Go project.

    Analyzes at package (directory) granularity, matching Go's
    natural unit of compilation and dependency.
    """
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        return {"error": f"'{project_dir}' is not a directory"}

    # Find module path
    module_path = find_module_path(project_dir)
    if not module_path:
        return {"error": f"No go.mod found in '{project_dir}'"}

    # List packages
    packages = list_packages(project_dir)
    if not packages:
        return {"error": f"No Go packages found in '{project_dir}'"}

    known_packages = set(packages.keys())

    # Build dependency map: package -> [packages it imports]
    deps: dict[str, list[str]] = {}
    pkg_info: dict[str, dict] = {}

    for pkg_suffix, go_files in packages.items():
        # Collect all internal imports from all files in this package
        all_internal_imports: set[str] = set()
        total_loc = 0
        file_count = 0

        for filepath in go_files:
            imports = extract_imports(filepath)
            internal = filter_internal_imports(imports, module_path, known_packages)
            # Don't count self-imports (files in same package importing same package)
            for imp in internal:
                if imp != pkg_suffix:
                    all_internal_imports.add(imp)
            total_loc += count_lines(filepath)
            file_count += 1

        dep_list = sorted(all_internal_imports)
        deps[pkg_suffix] = dep_list

        # Get package name from first file
        pkg_name = None
        if go_files:
            pkg_name = extract_package_name(go_files[0])

        pkg_info[pkg_suffix] = {
            "go_package_name": pkg_name or "unknown",
            "loc": total_loc,
            "files": file_count,
            "k_out": len(dep_list),
            "imports": dep_list,
        }

    # Compute NK metrics
    n = len(pkg_info)
    if n == 0:
        return {"error": "No analyzable packages found"}

    k_total = sum(len(d) for d in deps.values())
    k_avg = k_total / n if n > 0 else 0
    k_n = k_avg / n if n > 0 else 0
    k_max = max((len(d) for d in deps.values()), default=0)
    k_max_pkg = max(deps.keys(), key=lambda k: len(deps[k]), default="")

    # In-degree
    in_degree: dict[str, int] = defaultdict(int)
    for pkg, imports in deps.items():
        for imp in imports:
            in_degree[imp] += 1

    # Cycles
    cycles = detect_cycles(deps)
    cycle_count = len(cycles)

    # Composite score (same formula as nk_analyze.py)
    composite = k_avg * n + cycle_count

    # Burden score (same formula as nk_analyze.py)
    burden = cycle_count + 0.1 * n

    # Hub analysis
    hub_pct = k_max / k_total if k_total > 0 else 0

    # Architecture classification
    arch = classify_architecture(n, k_avg, k_max, cycle_count, hub_pct)

    # Total LOC
    total_loc = sum(p["loc"] for p in pkg_info.values())
    total_files = sum(p["files"] for p in pkg_info.values())

    result = {
        "project": module_path,
        "path": str(project_dir),
        "language": "Go",
        "granularity": "package",
        "n": n,
        "k_total": k_total,
        "k_avg": round(k_avg, 2),
        "k_n": round(k_n, 3),
        "k_max": k_max,
        "k_max_pkg": pkg_display_name(k_max_pkg),
        "cycles": cycle_count,
        "cycle_details": [" -> ".join(pkg_display_name(c) for c in cyc) for cyc in cycles],
        "composite": round(composite, 1),
        "burden": round(burden, 1),
        "architecture": arch,
        "hub_pct": round(hub_pct, 2),
        "total_loc": total_loc,
        "total_files": total_files,
        "packages": {
            pkg_display_name(k): v for k, v in pkg_info.items()
        },
        "in_degree": {
            pkg_display_name(k): v for k, v in in_degree.items()
        },
    }

    return result


def print_report(result: dict, verbose: bool = False):
    """Print a human-readable NK analysis report."""
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    project = result["project"]
    print(f"=== NK ANALYSIS (Go): {project} ===\n")

    print(f"  Path: {result['path']}")
    print(f"  Language: {result['language']}")
    print(f"  Granularity: {result['granularity']}")
    print(f"  Total LOC: {result['total_loc']}")
    print(f"  Total .go files: {result['total_files']}")
    print(f"  Architecture: {result['architecture']}")
    print()

    # Metrics table
    print("  NK Metrics:")
    print(f"    N (packages):         {result['n']}")
    print(f"    K_total (edges):      {result['k_total']}")
    print(f"    K_avg:                {result['k_avg']}")
    print(f"    K/N:                  {result['k_n']}")
    print(f"    K_max:                {result['k_max']} ({result['k_max_pkg']})")
    print(f"    Cycles:               {result['cycles']}")
    print(f"    K_avg*N + Cycles:     {result['composite']}")
    print(f"    Burden (Cyc+0.1N):    {result['burden']}")
    print(f"    Hub concentration:    {result['hub_pct']:.0%}")
    print()

    if result["cycles"] > 0:
        print("  Cycles:")
        for c in result["cycle_details"]:
            print(f"    {c}")
        print()

    # Package table
    if verbose:
        print("  Packages:")
        print(f"    {'Package':<30} {'Files':>5} {'LOC':>6} {'K_out':>6} {'K_in':>5}  Imports")
        print("    " + "-" * 80)
        for pkg_name in sorted(result["packages"].keys()):
            info = result["packages"][pkg_name]
            k_in = result["in_degree"].get(pkg_name, 0)
            imports_str = ", ".join(info["imports"]) if info["imports"] else "(none)"
            print(
                f"    {pkg_name:<30} {info['files']:>5} {info['loc']:>6} "
                f"{info['k_out']:>6} {k_in:>5}  {imports_str}"
            )
        print()

    # Cross-language comparison
    print("  Cross-Language Comparison:")
    benchmarks = [
        ("logging", "Py", 1.0),
        ("json", "Py", 2.0),
        ("urllib", "Py", 6.0),
        ("Express 5", "JS", 6.0),
        ("Express 4", "JS", 15.0),
        ("http.client", "Py", 26.4),
        ("unittest", "Py", 28.0),
        ("Rust serde", "Rust", 30.0),
        ("importlib", "Py", 38.0),
        ("xml", "Py", 38.0),
        ("email", "Py", 46.0),
        ("argparse", "Py", 48.1),
        ("requests", "Py", 55.0),
        ("click", "Py", 68.0),
        ("Go net/http", "Go", 89.0),
        ("multiprocessing", "Py", 102.0),
        ("jinja2", "Py", 109.0),
        ("asyncio", "Py", 128.0),
        ("flask", "Py", 130.0),
        ("werkzeug", "Py", 238.0),
    ]

    inserted = False
    # Get a clean short name, handling Go version suffixes like /v5
    parts = result["project"].split("/")
    short_name = parts[-1]
    if re.match(r'^v\d+$', short_name) and len(parts) > 1:
        short_name = parts[-2]
    print(f"    {'Package':<20} {'Lang':<6} {'Score':>8}")
    print("    " + "-" * 36)
    for name, lang, score in benchmarks:
        if not inserted and result["composite"] <= score:
            print(f"  > {short_name:<20} {'Go':<6} {result['composite']:>8.1f}  <- THIS")
            inserted = True
        print(f"    {name:<20} {lang:<6} {score:>8.1f}")
    if not inserted:
        print(f"  > {short_name:<20} {'Go':<6} {result['composite']:>8.1f}  <- THIS")


def suggest_refactor(result: dict):
    """Suggest which packages to extract for maximum cycle reduction."""
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    if result["cycles"] == 0:
        print(f"\n  {result['project']} has 0 cycles -- no refactoring needed for cycle reduction.")
        print(f"  Composite score: {result['composite']}")
        return

    deps = {k: v["imports"] for k, v in result["packages"].items()}

    # Count cycle participation for each package
    participation = {}
    for cycle_str in result["cycle_details"]:
        pkgs = cycle_str.split(" -> ")
        for p in pkgs[:-1]:
            participation[p] = participation.get(p, 0) + 1

    print(f"\n=== REFACTORING SUGGESTIONS: {result['project']} ===\n")
    print(f"  Current: N={result['n']}, Cycles={result['cycles']}, Composite={result['composite']}")
    print()

    ranked = sorted(participation.items(), key=lambda x: -x[1])

    print(f"  {'Package':<30} {'CyclePart':>10} {'Cycles_after':>13} {'Composite_after':>16} {'CycleReduction':>15}")
    print("  " + "-" * 87)

    for pkg, count in ranked[:7]:
        new_deps = {}
        for p, imports in deps.items():
            if p == pkg:
                continue
            new_deps[p] = [i for i in imports if i != pkg]

        n_after = len(new_deps)
        k_total = sum(len(d) for d in new_deps.values())
        k_avg = k_total / n_after if n_after > 0 else 0
        cycles_after = len(detect_cycles(new_deps))
        composite_after = k_avg * n_after + cycles_after
        cycle_reduction = (1 - cycles_after / result["cycles"]) * 100

        marker = " <- BEST" if pkg == ranked[0][0] else ""
        print(
            f"  {pkg:<30} {count:>10}/{result['cycles']}"
            f" {cycles_after:>13} {composite_after:>16.1f} {cycle_reduction:>14.0f}%{marker}"
        )

    best_pkg = ranked[0][0]
    best_info = result["packages"].get(best_pkg, {})
    k_in = result["in_degree"].get(best_pkg, 0)
    k_out = best_info.get("k_out", 0)

    print(f"\n  Recommendation: Extract '{best_pkg}' first")
    print(f"    - Participates in {ranked[0][1]}/{result['cycles']} cycles ({ranked[0][1]*100//result['cycles']}%)")
    print(f"    - K_in={k_in} (imported by {k_in} packages), K_out={k_out}")
    if k_in > k_out:
        print(f"    - High K_in/K_out ratio -> 'cycle passenger' (good extraction candidate)")
    else:
        print(f"    - Low K_in/K_out ratio -> 'cycle driver' (extraction may require interface changes)")
    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    as_json = "--json" in sys.argv
    refactor = "--suggest-refactor" in sys.argv or "--refactor" in sys.argv

    result = analyze_go_project(project_dir, verbose)

    if as_json:
        print(json_mod.dumps(result, indent=2))
    else:
        print_report(result, verbose)
        if refactor:
            suggest_refactor(result)


if __name__ == "__main__":
    main()
