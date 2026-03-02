"""Core NK analysis functions for Go projects."""

import os
import re
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
