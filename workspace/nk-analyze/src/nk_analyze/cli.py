"""CLI entry point for nk-analyze."""

import json
import sys
from pathlib import Path

from nk_analyze.core import analyze_package, analyze_path, detect_cycles

# Benchmark data for cross-package comparison
BENCHMARKS = [
    ("logging", 1.0),
    ("json", 2.0),
    ("urllib", 6.0),
    ("unittest", 28.0),
    ("importlib", 38.0),
    ("email", 46.0),
    ("requests", 55.0),
    ("click", 68.0),
    ("multiprocessing", 102.0),
    ("jinja2", 109.0),
    ("asyncio", 128.0),
    ("flask", 130.0),
    ("werkzeug", 238.0),
]


def print_report(result: dict, verbose: bool = False):
    """Print a human-readable NK analysis report."""
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    pkg = result["package"]
    print(f"=== NK ANALYSIS: {pkg} ===\n")
    print(f"  Path: {result['path']}")
    print(f"  Total LOC: {result['total_loc']}")
    print(f"  Architecture: {result['architecture']}")
    print()

    print("  NK Metrics:")
    print(f"    N (modules):          {result['n']}")
    print(f"    K_total (edges):      {result['k_total']}")
    print(f"    K_avg:                {result['k_avg']}")
    print(f"    K/N:                  {result['k_n']}")
    print(f"    K_max:                {result['k_max']} ({result['k_max_file']})")
    print(f"    Cycles:               {result['cycles']}")
    print(f"    K_avg*N + Cycles:     {result['composite']}")
    print(f"    Hub concentration:    {result['hub_pct']:.0%}")
    print()

    if result["cycles"] > 0:
        print("  Cycles:")
        for c in result["cycle_details"]:
            print(f"    {c}")
        print()

    if verbose:
        print("  Modules:")
        print(f"    {'Module':<25} {'LOC':>6} {'K_out':>6} {'K_in':>5}  Imports")
        print("    " + "-" * 70)
        for mod in sorted(result["modules"].keys()):
            info = result["modules"][mod]
            k_in = result["in_degree"].get(mod, 0)
            imports_str = ", ".join(info["imports"]) if info["imports"] else "(none)"
            print(f"    {mod:<25} {info['loc']:>6} {info['k_out']:>6} {k_in:>5}  {imports_str}")
        print()

    print("  Cross-Package Comparison:")
    inserted = False
    print(f"    {'Package':<20} {'Score':>8}")
    print("    " + "-" * 30)
    for name, score in BENCHMARKS:
        if not inserted and result["composite"] <= score:
            print(f"  → {pkg:<20} {result['composite']:>8.1f}  ← THIS")
            inserted = True
        print(f"    {name:<20} {score:>8.1f}")
    if not inserted:
        print(f"  → {pkg:<20} {result['composite']:>8.1f}  ← THIS")


def suggest_refactor(result: dict):
    """Suggest which modules to extract for maximum cycle reduction."""
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    if result["cycles"] == 0:
        print(f"\n  {result['package']} has 0 cycles — no refactoring needed.")
        return

    deps = {k: v["imports"] for k, v in result["modules"].items()}

    participation = {}
    for cycle_str in result["cycle_details"]:
        mods = cycle_str.split(" → ")
        for m in mods[:-1]:
            participation[m] = participation.get(m, 0) + 1

    print(f"\n=== REFACTORING SUGGESTIONS: {result['package']} ===\n")
    print(f"  Current: N={result['n']}, Cycles={result['cycles']}, Composite={result['composite']}")
    print()

    ranked = sorted(participation.items(), key=lambda x: -x[1])

    print(f"  {'Module':<25} {'CyclePart':>10} {'Cycles_after':>13} {'Reduction':>10}")
    print("  " + "-" * 60)

    for mod, count in ranked[:7]:
        new_deps = {}
        for m, imports in deps.items():
            if m == mod:
                continue
            new_deps[m] = [i for i in imports if i != mod]

        cycles_after = len(detect_cycles(new_deps))
        reduction = (1 - cycles_after / result["cycles"]) * 100
        marker = " ← BEST" if mod == ranked[0][0] else ""
        print(f"  {mod:<25} {count:>10}/{result['cycles']} {cycles_after:>13} {reduction:>9.0f}%{marker}")

    best_mod = ranked[0][0]
    print(f"\n  Recommendation: Extract '{best_mod}' first")
    print(f"    Participates in {ranked[0][1]}/{result['cycles']} cycles")


def batch_analyze(packages: list[str]):
    """Analyze multiple packages and print a comparison table."""
    results = []
    for pkg in packages:
        r = analyze_package(pkg)
        if "error" not in r:
            results.append(r)
        else:
            print(f"  SKIP: {pkg} — {r['error']}")

    if not results:
        print("No packages analyzed successfully.")
        return

    results.sort(key=lambda r: r["composite"])
    print(f"\n{'Package':<25} {'N':>4} {'K_avg':>6} {'K_max':>6} {'Cycles':>7} {'Composite':>10} {'Architecture':<15}")
    print("-" * 80)
    for r in results:
        print(
            f"{r['package']:<25} {r['n']:>4} {r['k_avg']:>6.2f} "
            f"{r['k_max']:>6} {r['cycles']:>7} {r['composite']:>10.1f} "
            f"{r['architecture']:<15}"
        )


def main():
    if len(sys.argv) < 2:
        print("Usage: nk-analyze <package> [--json] [--verbose] [--suggest-refactor]")
        print("       nk-analyze path <dir> <name> [--json] [--verbose]")
        print("       nk-analyze batch [pkg1 pkg2 ...]")
        sys.exit(1)

    package_name = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    as_json = "--json" in sys.argv
    refactor = "--suggest-refactor" in sys.argv or "--refactor" in sys.argv

    if package_name == "batch":
        packages = [a for a in sys.argv[2:] if not a.startswith("-")]
        if not packages:
            packages = [
                "json", "logging", "http", "unittest", "email",
                "asyncio", "multiprocessing", "xml", "urllib",
                "collections", "importlib",
            ]
        batch_analyze(packages)
        return

    if package_name == "path":
        args = [a for a in sys.argv[2:] if not a.startswith("-")]
        if len(args) < 2:
            print("Usage: nk-analyze path <directory> <package_name>")
            sys.exit(1)
        result = analyze_path(Path(args[0]), args[1])
    else:
        result = analyze_package(package_name, verbose)

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result, verbose)
        if refactor:
            suggest_refactor(result)


if __name__ == "__main__":
    main()
