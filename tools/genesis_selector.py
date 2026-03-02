#!/usr/bin/env python3
"""genesis_selector.py — Close the Darwinian selection loop (C2, L-497).

Reads child swarm outcomes from experiments/children/, ranks by fitness,
identifies which genesis atoms correlate with fitness, and produces
genesis.sh modification recommendations.

Council-approved: S367 (APPROVE 4/4, first F-GOV4 approval).
"""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHILDREN_DIR = REPO / "experiments" / "children"

# Genesis atoms defined in genesis.sh v7 — detect by content presence
ATOM_DETECTORS = {
    "session-protocol": lambda p: (p / "CLAUDE.md").exists(),
    "core-beliefs": lambda p: (p / "beliefs" / "CORE.md").exists(),
    "belief-tracking": lambda p: (p / "beliefs" / "DEPS.md").exists(),
    "conflict-protocol": lambda p: (p / "beliefs" / "CONFLICTS.md").exists(),
    "memory-index": lambda p: (p / "memory" / "INDEX.md").exists(),
    "distill-protocol": lambda p: (p / "memory" / "DISTILL.md").exists(),
    "verify-protocol": lambda p: (p / "memory" / "VERIFY.md").exists(),
    "lesson-template": lambda p: (p / "memory" / "lessons" / "TEMPLATE.md").exists(),
    "session-modes": lambda p: (p / "modes").is_dir() and any((p / "modes").iterdir()),
    "validator": lambda p: (p / "tools" / "validate_beliefs.py").exists(),
    "pre-commit-hook": lambda p: (p / "tools" / "pre-commit.hook").exists(),
    "frontier": lambda p: (p / "tasks" / "FRONTIER.md").exists(),
    "first-task": lambda p: (p / "tasks" / "TASK-001.md").exists(),
    "next-handoff": lambda p: (p / "tasks" / "NEXT.md").exists(),
    "principles-inherit": lambda p: (p / "memory" / "PRINCIPLES.md").exists(),
}


def scan_child(child_path: Path) -> dict:
    """Extract fitness metrics from a child swarm directory."""
    lessons_dir = child_path / "memory" / "lessons"
    lesson_files = [
        f for f in lessons_dir.glob("*.md")
        if f.name != "TEMPLATE.md"
    ] if lessons_dir.exists() else []

    # Count beliefs
    deps = child_path / "beliefs" / "DEPS.md"
    n_beliefs = 0
    if deps.exists():
        n_beliefs = len(re.findall(r"^### B\d+:", deps.read_text(), re.M))

    # Session count from INDEX.md
    idx = child_path / "memory" / "INDEX.md"
    n_sessions = 0
    if idx.exists():
        m = re.search(r"Sessions completed:\s*(\d+)", idx.read_text())
        if m:
            n_sessions = int(m.group(1))

    # Frontier questions resolved
    frontier = child_path / "tasks" / "FRONTIER.md"
    n_resolved = 0
    if frontier.exists():
        n_resolved = len(re.findall(r"^\|\s*F\d+", frontier.read_text(), re.M))

    # Detect atoms present
    atoms = {name: detect(child_path) for name, detect in ATOM_DETECTORS.items()}

    return {
        "name": child_path.name,
        "lessons": len(lesson_files),
        "beliefs": n_beliefs,
        "sessions": n_sessions,
        "resolved_frontiers": n_resolved,
        "atoms_present": atoms,
        "atom_count": sum(atoms.values()),
    }


def fitness(child: dict) -> float:
    """Compute fitness proxy. Primary: lessons/session. Secondary: beliefs/session."""
    s = max(child["sessions"], 1)  # avoid /0
    lps = child["lessons"] / s
    bps = child["beliefs"] / s
    rps = child["resolved_frontiers"] / s
    return round(lps * 0.6 + bps * 0.3 + rps * 0.1, 3)


def atom_correlation(children: list[dict]) -> dict:
    """Compute mean fitness for children with vs without each atom."""
    results = {}
    for atom in ATOM_DETECTORS:
        with_atom = [c for c in children if c["atoms_present"][atom]]
        without = [c for c in children if not c["atoms_present"][atom]]
        if not with_atom or not without:
            results[atom] = {
                "with_mean": round(sum(c["fitness"] for c in with_atom) / len(with_atom), 3) if with_atom else None,
                "without_mean": round(sum(c["fitness"] for c in without) / len(without), 3) if without else None,
                "n_with": len(with_atom),
                "n_without": len(without),
                "lift": None,
                "note": "no variance (all children have or lack this atom)",
            }
            continue
        mean_with = sum(c["fitness"] for c in with_atom) / len(with_atom)
        mean_without = sum(c["fitness"] for c in without) / len(without)
        lift = (mean_with - mean_without) / mean_without if mean_without else float("inf")
        results[atom] = {
            "with_mean": round(mean_with, 3),
            "without_mean": round(mean_without, 3),
            "n_with": len(with_atom),
            "n_without": len(without),
            "lift": round(lift, 3),
        }
    return results


def recommend(correlations: dict) -> list[str]:
    """Produce genesis.sh recommendations based on atom-fitness correlations."""
    recs = []
    for atom, data in sorted(correlations.items(), key=lambda x: x[1].get("lift") or 0, reverse=True):
        if data["lift"] is None:
            continue
        if data["lift"] > 0.15 and data["n_without"] >= 3:
            recs.append(f"KEEP {atom}: +{data['lift']:.0%} fitness lift (n_with={data['n_with']}, n_without={data['n_without']})")
        elif data["lift"] < -0.15 and data["n_with"] >= 3:
            recs.append(f"ABLATE-CANDIDATE {atom}: {data['lift']:.0%} fitness drag (n_with={data['n_with']}, n_without={data['n_without']})")
        else:
            recs.append(f"NEUTRAL {atom}: {data['lift']:+.0%} lift (n_with={data['n_with']}, n_without={data['n_without']})")
    return recs


def main():
    if not CHILDREN_DIR.exists():
        print(f"ERROR: {CHILDREN_DIR} not found")
        return 1

    children_dirs = sorted([d for d in CHILDREN_DIR.iterdir() if d.is_dir()])
    if not children_dirs:
        print("ERROR: no children found")
        return 1

    # Scan all children
    children = [scan_child(d) for d in children_dirs]
    for c in children:
        c["fitness"] = fitness(c)

    # Sort by fitness descending
    children.sort(key=lambda c: c["fitness"], reverse=True)

    # Unique atom configurations
    configs = set()
    for c in children:
        config = tuple(sorted(k for k, v in c["atoms_present"].items() if v))
        configs.add(config)

    # Atom correlations
    corrs = atom_correlation(children)

    # Recommendations
    recs = recommend(corrs)

    # Output report
    print("=== GENESIS SELECTOR (C2 closure, L-497) ===\n")
    print(f"Children scanned: {len(children)}")
    print(f"Unique atom configurations: {len(configs)}")
    print(f"Session range: {min(c['sessions'] for c in children)}-{max(c['sessions'] for c in children)}")
    print(f"Lesson range: {min(c['lessons'] for c in children)}-{max(c['lessons'] for c in children)}")
    print(f"Fitness range: {min(c['fitness'] for c in children)}-{max(c['fitness'] for c in children)}")

    print("\n--- Top 10 children by fitness (lessons/session weighted) ---")
    for c in children[:10]:
        print(f"  {c['fitness']:5.3f}  {c['name']}  ({c['lessons']}L/{c['sessions']}S/{c['beliefs']}B, atoms={c['atom_count']}/{len(ATOM_DETECTORS)})")

    print("\n--- Bottom 5 children ---")
    for c in children[-5:]:
        print(f"  {c['fitness']:5.3f}  {c['name']}  ({c['lessons']}L/{c['sessions']}S/{c['beliefs']}B, atoms={c['atom_count']}/{len(ATOM_DETECTORS)})")

    print("\n--- Atom-fitness correlations ---")
    for atom, data in sorted(corrs.items(), key=lambda x: x[1].get("lift") or 0, reverse=True):
        lift_str = f"{data['lift']:+.0%}" if data["lift"] is not None else "N/A"
        print(f"  {lift_str:>6}  {atom}  (with={data['n_with']}, without={data['n_without']})")

    print("\n--- Recommendations for genesis.sh ---")
    for r in recs:
        print(f"  {r}")

    # Write JSON artifact
    artifact = {
        "session": "S367",
        "tool": "genesis_selector.py",
        "frontier": "F-GOV4 + F-DNA1",
        "council_decision": "APPROVE (4/4, first F-GOV4 approval)",
        "children_scanned": len(children),
        "unique_atom_configs": len(configs),
        "fitness_proxy": "0.6*lessons/session + 0.3*beliefs/session + 0.1*resolved/session",
        "top_5": [
            {"name": c["name"], "fitness": c["fitness"], "lessons": c["lessons"],
             "sessions": c["sessions"], "beliefs": c["beliefs"]}
            for c in children[:5]
        ],
        "atom_correlations": corrs,
        "recommendations": recs,
    }
    out_path = REPO / "experiments" / "governance" / "f-gov4-first-approve-s367.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact written: {out_path.relative_to(REPO)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
