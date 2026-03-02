#!/usr/bin/env python3
"""
merge_compatibility.py — Cross-lineage swarm merge compatibility checker (F-MERGE1 Phase 0).

Measures genetic distance between two independently-evolved swarm instances
grown by different humans. Predicts merge viability before any state is exchanged.

Five dimensions of compatibility (L-1100):
  1. Axiom compatibility: PHILOSOPHY.md claim alignment
  2. Principle overlap: PRINCIPLES.md shared vs divergent rules
  3. Belief compatibility: DEPS.md hypothesis alignment
  4. Protocol compatibility: CORE.md operating principle alignment
  5. Tool compatibility: shared vs divergent tool ecosystems

Output: compatibility score, conflict inventory, merge strategy recommendation.

Usage:
    python3 tools/merge_compatibility.py <path-to-other-swarm>
    python3 tools/merge_compatibility.py <path-to-other-swarm> --json
    python3 tools/merge_compatibility.py <path-to-other-swarm> --detail
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# --- Extraction helpers ---

def extract_philosophy_claims(path: Path) -> dict[str, str]:
    """Extract PHIL-N claims from PHILOSOPHY.md."""
    claims = {}
    if not path.exists():
        return claims
    text = path.read_text(errors="ignore")
    # Match [PHIL-N] markers and capture surrounding context
    for m in re.finditer(r'\*\*\[PHIL-(\d+)\]\*\*\s*(.*?)(?=\*\*\[PHIL-|\Z)', text, re.DOTALL):
        phil_id = f"PHIL-{m.group(1)}"
        # Take first sentence as the claim summary
        content = m.group(2).strip()
        first_line = content.split('\n')[0].strip()
        claims[phil_id] = first_line[:200]
    return claims


def extract_principles(path: Path) -> list[str]:
    """Extract principle identifiers from PRINCIPLES.md.

    Format: pipe-delimited within category lines, e.g.
    **Structure**: P-008 validate by usage | P-011 flat→hierarchical
    """
    principles = []
    if not path.exists():
        return principles
    text = path.read_text(errors="ignore")
    # Find all P-NNN entries with their short names
    for m in re.finditer(r'P-(\d+)\s+([^|*\n]+)', text):
        name = m.group(2).strip().rstrip(':')
        if name and len(name) > 3:  # skip noise
            principles.append(name[:150])
    return principles


def extract_core_principles(path: Path) -> list[str]:
    """Extract numbered operating principles from CORE.md."""
    principles = []
    if not path.exists():
        return principles
    text = path.read_text(errors="ignore")
    for line in text.splitlines():
        m = re.match(r'^\d+\.\s+\*\*(.*?)\.\*\*', line.strip())
        if m:
            principles.append(m.group(1).strip())
    return principles


def extract_beliefs(path: Path) -> dict[str, str]:
    """Extract B-N beliefs from DEPS.md."""
    beliefs = {}
    if not path.exists():
        return beliefs
    text = path.read_text(errors="ignore")
    for m in re.finditer(r'###\s+(B\d+|B-EVAL\d+):\s*(.*?)(?=###|\Z)', text, re.DOTALL):
        bid = m.group(1)
        content = m.group(2).strip()
        first_line = content.split('\n')[0].strip()
        beliefs[bid] = first_line[:200]
    return beliefs


def extract_tools(path: Path) -> set[str]:
    """List tool filenames in tools/ directory."""
    tools_dir = path / "tools"
    if not tools_dir.exists():
        return set()
    return {f.name for f in tools_dir.glob("*.py") if f.is_file()}


def extract_lessons_count(path: Path) -> int:
    """Count lessons in memory/lessons/."""
    lessons_dir = path / "memory" / "lessons"
    if not lessons_dir.exists():
        return 0
    return len(list(lessons_dir.glob("L-*.md")))


def extract_domains(path: Path) -> set[str]:
    """List domain names."""
    domains_dir = path / "domains"
    if not domains_dir.exists():
        return set()
    return {d.name for d in domains_dir.iterdir() if d.is_dir()}


# --- Comparison engine ---

def word_overlap(a: str, b: str) -> float:
    """Word-level Jaccard similarity between two strings."""
    words_a = set(re.findall(r'\w+', a.lower()))
    words_b = set(re.findall(r'\w+', b.lower()))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def compare_philosophies(local_claims: dict, remote_claims: dict) -> dict:
    """Compare PHILOSOPHY.md claims between two swarms."""
    shared_ids = set(local_claims) & set(remote_claims)
    local_only = set(local_claims) - set(remote_claims)
    remote_only = set(remote_claims) - set(local_claims)

    # For shared IDs, measure content similarity
    aligned = []
    divergent = []
    for pid in sorted(shared_ids):
        sim = word_overlap(local_claims[pid], remote_claims[pid])
        entry = {"id": pid, "similarity": round(sim, 3),
                 "local": local_claims[pid][:100], "remote": remote_claims[pid][:100]}
        if sim >= 0.3:
            aligned.append(entry)
        else:
            divergent.append(entry)

    return {
        "shared_count": len(shared_ids),
        "local_only": sorted(local_only),
        "remote_only": sorted(remote_only),
        "aligned": aligned,
        "divergent": divergent,
        "compatibility": len(aligned) / max(len(shared_ids), 1),
    }


def compare_principles(local_p: list, remote_p: list) -> dict:
    """Compare principle sets using fuzzy matching."""
    if not local_p and not remote_p:
        return {"local_count": 0, "remote_count": 0, "overlap_rate": 1.0,
                "estimated_compatible": 0, "estimated_novel": 0}

    # Find best-match pairs
    matched = 0
    for lp in local_p:
        best = max((word_overlap(lp, rp) for rp in remote_p), default=0)
        if best >= 0.4:
            matched += 1

    total_unique = len(local_p) + len(remote_p) - matched
    return {
        "local_count": len(local_p),
        "remote_count": len(remote_p),
        "matched_pairs": matched,
        "overlap_rate": round(matched / max(len(local_p), 1), 3),
        "estimated_compatible": matched,
        "estimated_novel": total_unique - matched,
    }


def compare_tools(local_t: set, remote_t: set) -> dict:
    """Compare tool ecosystems."""
    shared = local_t & remote_t
    local_only = local_t - remote_t
    remote_only = remote_t - local_t
    total = len(local_t | remote_t)
    return {
        "shared": sorted(shared),
        "local_only": sorted(local_only),
        "remote_only": sorted(remote_only),
        "jaccard": round(len(shared) / max(total, 1), 3),
    }


# --- Genetic distance model ---

def compute_genetic_distance(phil_compat: dict, princ_compat: dict,
                             tool_compat: dict, local_lessons: int,
                             remote_lessons: int) -> dict:
    """Compute overall genetic distance and merge viability.

    Distance model (0=identical, 1=maximally different):
    - Axiom distance (weight 0.35): how different are the PHIL claims
    - Principle distance (weight 0.25): how different are the distilled rules
    - Tool distance (weight 0.15): how different are the tool ecosystems
    - Scale distance (weight 0.25): how different are the evolutionary stages

    Merge viability zones (biological analog):
    - Distance < 0.1: inbreeding zone — merge adds little value
    - Distance 0.1-0.4: heterosis zone — optimal, expect hybrid vigor
    - Distance 0.4-0.7: cautious zone — significant conflicts, careful arbitration
    - Distance > 0.7: incompatibility zone — merge likely destructive
    """
    axiom_dist = 1.0 - phil_compat.get("compatibility", 0)
    princ_dist = 1.0 - princ_compat.get("overlap_rate", 0)
    tool_dist = 1.0 - tool_compat.get("jaccard", 0)

    # Scale distance: how different in evolutionary stage
    max_lessons = max(local_lessons, remote_lessons, 1)
    min_lessons = min(local_lessons, remote_lessons)
    scale_dist = 1.0 - (min_lessons / max_lessons)

    distance = (0.35 * axiom_dist + 0.25 * princ_dist +
                0.15 * tool_dist + 0.25 * scale_dist)

    if distance < 0.1:
        zone = "INBREEDING"
        strategy = "Low value — swarms too similar for meaningful recombination"
    elif distance < 0.4:
        zone = "HETEROSIS"
        strategy = "Optimal — expect hybrid vigor from complementary knowledge"
    elif distance < 0.7:
        zone = "CAUTIOUS"
        strategy = "Significant divergence — careful Phase 2 lesson arbitration required"
    else:
        zone = "INCOMPATIBLE"
        strategy = "High risk — core axioms likely contradict; merge may be destructive"

    return {
        "distance": round(distance, 3),
        "components": {
            "axiom_distance": round(axiom_dist, 3),
            "principle_distance": round(princ_dist, 3),
            "tool_distance": round(tool_dist, 3),
            "scale_distance": round(scale_dist, 3),
        },
        "zone": zone,
        "strategy": strategy,
    }


# --- Main ---

def analyze(remote_path: Path) -> dict:
    """Run full compatibility analysis between local swarm and remote swarm."""
    local_path = ROOT

    # Verify remote is a swarm (full or child genesis)
    remote_swarm = (remote_path / "SWARM.md").exists()
    remote_core = (remote_path / "beliefs" / "CORE.md").exists()
    remote_phil = (remote_path / "beliefs" / "PHILOSOPHY.md").exists()
    if not remote_swarm and not remote_core:
        return {"error": f"{remote_path} is not a swarm (no SWARM.md or beliefs/CORE.md)",
                "viable": False}

    # Extract state from both
    local_claims = extract_philosophy_claims(local_path / "beliefs" / "PHILOSOPHY.md")
    remote_claims = extract_philosophy_claims(remote_path / "beliefs" / "PHILOSOPHY.md") if remote_phil else {}

    local_principles = extract_principles(local_path / "memory" / "PRINCIPLES.md")
    remote_principles = extract_principles(remote_path / "memory" / "PRINCIPLES.md")

    local_core = extract_core_principles(local_path / "beliefs" / "CORE.md")
    remote_core = extract_core_principles(remote_path / "beliefs" / "CORE.md")

    local_beliefs = extract_beliefs(local_path / "beliefs" / "DEPS.md")
    remote_beliefs = extract_beliefs(remote_path / "beliefs" / "DEPS.md")

    local_tools = extract_tools(local_path)
    remote_tools = extract_tools(remote_path)

    local_lessons = extract_lessons_count(local_path)
    remote_lessons = extract_lessons_count(remote_path)

    local_domains = extract_domains(local_path)
    remote_domains = extract_domains(remote_path)

    # Compare dimensions
    phil_compat = compare_philosophies(local_claims, remote_claims)
    princ_compat = compare_principles(local_principles, remote_principles)
    core_compat = compare_principles(local_core, remote_core)
    tool_compat = compare_tools(local_tools, remote_tools)

    # Compute genetic distance
    distance = compute_genetic_distance(
        phil_compat, princ_compat, tool_compat,
        local_lessons, remote_lessons
    )

    # Domain overlap
    shared_domains = local_domains & remote_domains
    novel_domains = (remote_domains - local_domains)

    return {
        "local_swarm": str(local_path),
        "remote_swarm": str(remote_path),
        "summary": {
            "local_stats": {
                "lessons": local_lessons,
                "principles": len(local_principles),
                "phil_claims": len(local_claims),
                "beliefs": len(local_beliefs),
                "tools": len(local_tools),
                "domains": len(local_domains),
            },
            "remote_stats": {
                "lessons": remote_lessons,
                "principles": len(remote_principles),
                "phil_claims": len(remote_claims),
                "beliefs": len(remote_beliefs),
                "tools": len(remote_tools),
                "domains": len(remote_domains),
            },
        },
        "philosophy": phil_compat,
        "principles": princ_compat,
        "core_principles": core_compat,
        "tools": tool_compat,
        "domains": {
            "shared": sorted(shared_domains),
            "remote_novel": sorted(novel_domains),
            "local_novel": sorted(local_domains - remote_domains),
        },
        "genetic_distance": distance,
        "merge_phases": {
            "phase_0_compatible": distance["zone"] != "INCOMPATIBLE",
            "phase_1_ready": True,  # read-only orientation is always safe
            "phase_2_conflicts": phil_compat.get("divergent", []),
            "phase_3_belief_merge": len(local_beliefs) + len(remote_beliefs),
            "phase_4_identity": "Multi-identity architecture required"
                if phil_compat.get("divergent") else "Single-identity may suffice",
        },
        "viable": distance["zone"] != "INCOMPATIBLE",
    }


def print_report(result: dict):
    """Human-readable compatibility report."""
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    d = result["genetic_distance"]
    print("=" * 60)
    print("CROSS-LINEAGE SWARM MERGE COMPATIBILITY (F-MERGE1 Phase 0)")
    print("=" * 60)

    print(f"\nLocal:  {result['local_swarm']}")
    print(f"Remote: {result['remote_swarm']}")

    ls = result["summary"]["local_stats"]
    rs = result["summary"]["remote_stats"]
    print(f"\n  Local:  {ls['lessons']}L {ls['principles']}P {ls['beliefs']}B "
          f"{ls['phil_claims']}PHIL {ls['tools']}T {ls['domains']}D")
    print(f"  Remote: {rs['lessons']}L {rs['principles']}P {rs['beliefs']}B "
          f"{rs['phil_claims']}PHIL {rs['tools']}T {rs['domains']}D")

    print(f"\nGENETIC DISTANCE: {d['distance']:.3f}")
    print(f"  Axiom:     {d['components']['axiom_distance']:.3f}")
    print(f"  Principle: {d['components']['principle_distance']:.3f}")
    print(f"  Tool:      {d['components']['tool_distance']:.3f}")
    print(f"  Scale:     {d['components']['scale_distance']:.3f}")
    print(f"\nZONE: {d['zone']}")
    print(f"  {d['strategy']}")

    phil = result["philosophy"]
    if phil.get("divergent"):
        print(f"\nAXIOM CONFLICTS ({len(phil['divergent'])}):")
        for c in phil["divergent"]:
            print(f"  {c['id']} (sim={c['similarity']:.2f})")
            print(f"    Local:  {c['local']}")
            print(f"    Remote: {c['remote']}")

    if phil.get("local_only"):
        print(f"\nLocal-only axioms: {', '.join(phil['local_only'])}")
    if phil.get("remote_only"):
        print(f"Remote-only axioms: {', '.join(phil['remote_only'])}")

    dom = result["domains"]
    if dom["remote_novel"]:
        print(f"\nNovel domains from remote: {', '.join(dom['remote_novel'][:10])}")

    tool = result["tools"]
    if tool["remote_only"]:
        print(f"Novel tools from remote: {', '.join(list(tool['remote_only'])[:10])}")

    phases = result["merge_phases"]
    print(f"\nMERGE READINESS:")
    print(f"  Phase 0 (compatible):    {'YES' if phases['phase_0_compatible'] else 'NO — INCOMPATIBLE'}")
    print(f"  Phase 1 (read-only):     {'READY' if phases['phase_1_ready'] else 'BLOCKED'}")
    print(f"  Phase 2 (conflicts):     {len(phases['phase_2_conflicts'])} axiom conflicts to arbitrate")
    print(f"  Phase 3 (belief merge):  {phases['phase_3_belief_merge']} total beliefs")
    print(f"  Phase 4 (identity):      {phases['phase_4_identity']}")

    print(f"\nVIABLE: {'YES' if result['viable'] else 'NO'}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if not args:
        print("Usage: python3 tools/merge_compatibility.py <path-to-other-swarm> [--json] [--detail]")
        print("\nMeasures genetic distance between this swarm and another.")
        print("Phase 0 of the 5-phase safe merge protocol (L-1100, F-MERGE1).")
        return 0

    remote = Path(args[0]).resolve()
    if not remote.exists():
        print(f"ERROR: Path does not exist: {remote}")
        return 1

    result = analyze(remote)

    if "--json" in flags:
        print(json.dumps(result, indent=2, default=str))
    else:
        print_report(result)

    return 0 if result.get("viable", False) else 1


if __name__ == "__main__":
    sys.exit(main())
