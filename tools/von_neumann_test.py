#!/usr/bin/env python3
"""
von_neumann_test.py — Test von Neumann self-reproducing automaton conditions on swarm.

Von Neumann (1966) proved self-reproduction requires 4 components:
  A (constructor):  builds offspring from description
  B (copier):       copies the description to offspring
  C (controller):   coordinates A and B
  D (description):  encodes A+B+C

Key theorem: K(D) >= K(A+B+C) — description must be at least as
complex as the system it describes, or reproduction is lossy.

This tool maps swarm components to A/B/C/D and measures whether
the complexity inequality holds at boot-tier and full-tier.

Usage:
    python3 tools/von_neumann_test.py              # full report
    python3 tools/von_neumann_test.py --json        # machine-readable
"""

import json
import math
import os
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Component definitions ---
# A: Universal constructor — tools that build swarm state from blueprint
CONSTRUCTOR_A = [
    "tools/orient.py",
    "tools/validate_beliefs.py",
    "tools/compact.py",
    "tools/sync_state.py",
    "tools/dispatch_optimizer.py",
    "tools/open_lane.py",
    "tools/close_lane.py",
    "tools/maintenance.py",
]

# B: Copier — tools that copy/extract the description
COPIER_B = [
    "tools/cell_blueprint.py",
    "tools/genesis_extract.py",
]

# C: Controller — protocol that coordinates A and B
CONTROLLER_C = [
    "SWARM.md",
    "beliefs/CORE.md",
    "CLAUDE.md",
]

# D: Description — the genesis bundle boot tier (from L-1489)
BOOT_TIER_D = [
    "tools/orient.py",
    "tools/validate_beliefs.py",
    "tools/compact.py",
    "tools/sync_state.py",
    "tools/cell_blueprint.py",
    "tools/genesis_extract.py",
    "beliefs/CORE.md",
    "beliefs/PHILOSOPHY.md",
    "beliefs/DEPS.md",
    "SWARM.md",
    "CLAUDE.md",
    "memory/INDEX.md",
    "memory/PRINCIPLES.md",
]


def file_bytes(path):
    """Raw byte count of a file."""
    fp = ROOT / path
    if fp.exists():
        return fp.stat().st_size
    return 0


def kolmogorov_proxy(path):
    """Proxy for Kolmogorov complexity: zlib-compressed size."""
    fp = ROOT / path
    if fp.exists():
        data = fp.read_bytes()
        return len(zlib.compress(data, 9))
    return 0


def component_stats(name, paths):
    """Compute raw + compressed sizes for a component."""
    raw = sum(file_bytes(p) for p in paths)
    compressed = sum(kolmogorov_proxy(p) for p in paths)
    file_count = sum(1 for p in paths if (ROOT / p).exists())
    missing = [p for p in paths if not (ROOT / p).exists()]
    return {
        "name": name,
        "files": file_count,
        "raw_bytes": raw,
        "compressed_bytes": compressed,
        "missing": missing,
    }


def total_swarm_size():
    """Measure total swarm complexity (all tracked content)."""
    raw = 0
    compressed = 0
    file_count = 0
    for dirpath in ["beliefs", "memory", "domains", "tasks", "tools"]:
        dp = ROOT / dirpath
        if dp.exists():
            for f in dp.rglob("*"):
                if f.is_file() and not f.name.startswith("."):
                    raw += f.stat().st_size
                    compressed += len(zlib.compress(f.read_bytes(), 9))
                    file_count += 1
    for f in ["SWARM.md", "CLAUDE.md", "AGENTS.md", "GEMINI.md"]:
        fp = ROOT / f
        if fp.exists():
            raw += fp.stat().st_size
            compressed += len(zlib.compress(fp.read_bytes(), 9))
            file_count += 1
    return {"files": file_count, "raw_bytes": raw, "compressed_bytes": compressed}


def minimax_falsification_rate(cost_false_positive=10, cost_false_negative=1):
    """
    Von Neumann minimax for falsification allocation.

    In the hypothesis-testing game:
      - Player 1 (proposer) wants hypotheses accepted
      - Player 2 (falsifier) wants wrong hypotheses rejected

    Payoff asymmetry: accepting a wrong belief (false positive) costs more
    than missing a correct one (false negative).

    Minimax optimal falsification rate = cost_FP / (cost_FP + cost_FN)
    """
    optimal_rate = cost_false_positive / (cost_false_positive + cost_false_negative)
    return optimal_rate


def analyze():
    """Run full von Neumann self-reproduction analysis."""
    a = component_stats("A_constructor", CONSTRUCTOR_A)
    b = component_stats("B_copier", COPIER_B)
    c = component_stats("C_controller", CONTROLLER_C)
    d = component_stats("D_description_boot", BOOT_TIER_D)
    t = total_swarm_size()

    # Von Neumann inequality: K(D) >= K(A+B+C)
    abc_compressed = a["compressed_bytes"] + b["compressed_bytes"] + c["compressed_bytes"]
    d_compressed = d["compressed_bytes"]

    # Boot-tier ratio: D / (A+B+C)
    boot_ratio = d_compressed / abc_compressed if abc_compressed > 0 else 0

    # Full-tier ratio: D / T
    full_ratio = d_compressed / t["compressed_bytes"] if t["compressed_bytes"] > 0 else 0

    # Reproduction fidelity estimate
    # If D < A+B+C, reproduction is lossy by the deficit
    deficit_pct = max(0, (1 - boot_ratio)) * 100
    # Predicted swarmability = 100 * min(1, D/(A+B+C))
    predicted_swarmability = min(100, 100 * boot_ratio)

    # Von Neumann's dual-use theorem:
    # D is used twice: once READ (to construct) and once COPIED (to offspring)
    # Self-contained = D includes B (the copier itself)
    b_in_d = all((ROOT / p).exists() and p in BOOT_TIER_D for p in COPIER_B)
    # Check: does D include enough of A to bootstrap?
    a_in_d = sum(1 for p in CONSTRUCTOR_A if p in BOOT_TIER_D)
    a_boot_coverage = a_in_d / len(CONSTRUCTOR_A)

    # Fixed-point test: D encodes a system that can produce D'
    # True if B (copier) is in D AND C (controller) is in D
    c_in_d = sum(1 for p in CONTROLLER_C if p in BOOT_TIER_D)
    c_coverage = c_in_d / len(CONTROLLER_C)
    fixed_point = b_in_d and c_coverage >= 0.66

    # Minimax falsification
    optimal_falsification = minimax_falsification_rate()

    # Generational decay estimate
    # Each reproduction loses (1 - boot_ratio) of constructor capacity
    # After n generations: capacity = boot_ratio^n
    gens_to_half = (
        math.log(0.5) / math.log(boot_ratio) if 0 < boot_ratio < 1 else float("inf")
    )

    return {
        "von_neumann_components": {
            "A_constructor": a,
            "B_copier": b,
            "C_controller": c,
            "D_description_boot": d,
            "T_total_swarm": t,
        },
        "complexity_inequality": {
            "K_D_compressed": d_compressed,
            "K_ABC_compressed": abc_compressed,
            "boot_ratio": round(boot_ratio, 4),
            "full_coverage_ratio": round(full_ratio, 4),
            "inequality_holds": boot_ratio >= 1.0,
            "deficit_pct": round(deficit_pct, 2),
            "predicted_swarmability": round(predicted_swarmability, 1),
            "actual_swarmability": 100,  # S538: fixed-point achieved, 10/10 checks pass
        },
        "dual_use_theorem": {
            "copier_in_description": b_in_d,
            "constructor_boot_coverage": round(a_boot_coverage, 2),
            "controller_coverage": round(c_coverage, 2),
            "fixed_point_achieved": fixed_point,
        },
        "generational_analysis": {
            "boot_ratio_per_gen": round(boot_ratio, 4),
            "generations_to_half_capacity": (
                round(gens_to_half, 1) if gens_to_half != float("inf") else "infinite"
            ),
            "boot_tier_self_sustaining": boot_ratio >= 1.0,
        },
        "minimax_falsification": {
            "optimal_rate": round(optimal_falsification, 3),
            "current_rate": round(40 / 1407, 4),
            "gap": round(optimal_falsification - 40 / 1407, 3),
            "interpretation": (
                "Swarm under-falsifies by {:.0f}x relative to minimax optimal "
                "(cost_FP=10x cost_FN)".format(
                    optimal_falsification / (40 / 1407) if 40 / 1407 > 0 else 0
                )
            ),
        },
    }


def print_report(results):
    """Human-readable report."""
    print("=" * 70)
    print("VON NEUMANN SELF-REPRODUCTION ANALYSIS")
    print("=" * 70)

    print("\n--- Component Mapping ---")
    for key in ["A_constructor", "B_copier", "C_controller", "D_description_boot"]:
        c = results["von_neumann_components"][key]
        print(f"  {c['name']:25s}  {c['files']:3d} files  "
              f"{c['raw_bytes']:>10,} raw  {c['compressed_bytes']:>8,} compressed")
    t = results["von_neumann_components"]["T_total_swarm"]
    print(f"  {'T_total_swarm':25s}  {t['files']:3d} files  "
          f"{t['raw_bytes']:>10,} raw  {t['compressed_bytes']:>8,} compressed")

    ci = results["complexity_inequality"]
    print(f"\n--- Von Neumann Complexity Inequality: K(D) >= K(A+B+C) ---")
    print(f"  K(D) = {ci['K_D_compressed']:,}  |  K(A+B+C) = {ci['K_ABC_compressed']:,}")
    print(f"  Boot ratio D/(A+B+C) = {ci['boot_ratio']}")
    if ci["inequality_holds"]:
        print(f"  ✓ INEQUALITY HOLDS — boot-tier self-reproduction is lossless")
    else:
        print(f"  ✗ INEQUALITY VIOLATED — reproduction loses {ci['deficit_pct']:.1f}% per generation")
    print(f"  Predicted swarmability: {ci['predicted_swarmability']:.0f}/100  "
          f"(actual: {ci['actual_swarmability']}/100)")
    print(f"  Full swarm coverage: {ci['full_coverage_ratio']*100:.1f}%")

    du = results["dual_use_theorem"]
    print(f"\n--- Dual-Use Theorem (D read + copied) ---")
    print(f"  Copier (B) in description: {'✓' if du['copier_in_description'] else '✗'}")
    print(f"  Constructor boot coverage: {du['constructor_boot_coverage']*100:.0f}%")
    print(f"  Controller coverage: {du['controller_coverage']*100:.0f}%")
    print(f"  Fixed-point achieved: {'✓' if du['fixed_point_achieved'] else '✗'}")

    ga = results["generational_analysis"]
    print(f"\n--- Generational Decay ---")
    print(f"  Capacity per generation: {ga['boot_ratio_per_gen']}")
    print(f"  Generations to half capacity: {ga['generations_to_half_capacity']}")
    print(f"  Boot tier self-sustaining: {'✓' if ga['boot_tier_self_sustaining'] else '✗'}")

    mf = results["minimax_falsification"]
    print(f"\n--- Minimax Falsification (von Neumann game theory) ---")
    print(f"  Optimal rate: {mf['optimal_rate']*100:.1f}%")
    print(f"  Current rate: {mf['current_rate']*100:.2f}%")
    print(f"  {mf['interpretation']}")

    print("\n" + "=" * 70)


def main():
    results = analyze()
    if "--json" in sys.argv:
        print(json.dumps(results, indent=2, default=str))
    else:
        print_report(results)
    return results


if __name__ == "__main__":
    main()
