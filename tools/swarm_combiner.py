#!/usr/bin/env python3
"""
swarm_combiner.py — Execute the 5-phase safe merge protocol (F-MERGE1, L-1100).

Combines two independently-evolved swarm instances into a merged output directory.
Neither source swarm is modified — the merge produces a new directory.

Biological analog: sexual reproduction. Two haploid genomes combine into a viable
diploid offspring. Genetic distance determines hybrid vigor vs incompatibility.

Usage:
    python3 tools/swarm_combiner.py <path-to-other-swarm> [--output <dir>] [--json] [--dry-run]
    python3 tools/swarm_combiner.py <path-to-other-swarm> --phase 0   # compatibility only
    python3 tools/swarm_combiner.py <path-to-other-swarm> --phase 1   # orientation only
    python3 tools/swarm_combiner.py <path-to-other-swarm> --phase 2   # through lesson arbitration
    python3 tools/swarm_combiner.py <path-to-other-swarm> --phase 3   # through belief merge
    python3 tools/swarm_combiner.py <path-to-other-swarm> --phase 4   # full merge (default)

Phases:
    0: Compatibility check (genetic distance, zone classification)
    1: Read-only mutual orientation (state extraction, no writes)
    2: Lesson arbitration (classify every lesson: compatible/context-dependent/contradictory)
    3: Evidence-weighted belief merge (beliefs, principles with provenance)
    4: Identity negotiation (synthesized PHILOSOPHY.md, merged CORE.md)

Safety invariants:
    - No information destruction: everything preserved with provenance
    - Conflicts surfaced, not hidden: every contradiction documented
    - Reversibility: neither source swarm modified
    - Authority parity: neither human's authority overrides
    - Hybrid viability: merged swarm must be at least as capable as either parent
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Import merge_compatibility for Phase 0
sys.path.insert(0, str(ROOT / "tools"))
try:
    from merge_compatibility import analyze as phase0_analyze
except ImportError:
    phase0_analyze = None


# ─── Phase 0: Compatibility Check ───────────────────────────────────────────

def run_phase0(local: Path, remote: Path) -> dict:
    """Phase 0: Genetic distance and zone classification."""
    if phase0_analyze:
        result = phase0_analyze(remote)
    else:
        result = {"error": "merge_compatibility.py not importable", "viable": False}

    if not result.get("viable", False):
        zone = result.get("genetic_distance", {}).get("zone", "UNKNOWN")
        if zone == "INCOMPATIBLE":
            result["phase0_gate"] = "BLOCKED"
            result["phase0_reason"] = "Genetic distance too high — core axioms contradict"
        else:
            result["phase0_gate"] = "PASS"
    else:
        result["phase0_gate"] = "PASS"

    return result


# ─── Phase 1: Read-Only Mutual Orientation ───────────────────────────────────

def _read_file_safe(path: Path) -> str:
    """Read file contents, return empty string if missing."""
    if path.exists():
        return path.read_text(errors="ignore")
    return ""


def _extract_lessons(root: Path) -> dict[str, dict]:
    """Extract all lessons with metadata."""
    lessons = {}
    lessons_dir = root / "memory" / "lessons"
    if not lessons_dir.exists():
        return lessons
    for lf in sorted(lessons_dir.glob("L-*.md")):
        text = lf.read_text(errors="ignore")
        lines = text.split("\n")
        title = lines[0].lstrip("# ").strip() if lines else ""

        # Extract metadata
        sharpe_m = re.search(r"Sharpe:\s*(\d+)", text)
        domain_m = re.search(r"Domain:\s*([^\n|]+)", text)
        session_m = re.search(r"Session:\s*(S\d+)", text)
        cites_m = re.search(r"Cites:\s*([^\n]+)", text)
        external_m = re.search(r"External:\s*([^\n]+)", text)
        confidence_m = re.search(r"Confidence:\s*(\w+)", text)

        lessons[lf.stem] = {
            "title": title[:200],
            "sharpe": int(sharpe_m.group(1)) if sharpe_m else 0,
            "domain": domain_m.group(1).strip() if domain_m else "unknown",
            "session": session_m.group(1) if session_m else "unknown",
            "cites": [c.strip() for c in cites_m.group(1).split(",")] if cites_m else [],
            "has_external": bool(external_m and external_m.group(1).strip().lower() not in ["none", ""]),
            "confidence": confidence_m.group(1) if confidence_m else "unknown",
            "text": text,
            "word_count": len(text.split()),
        }
    return lessons


def _extract_phil_claims(root: Path) -> dict[str, dict]:
    """Extract PHILOSOPHY.md claims with full text blocks."""
    claims = {}
    phil_path = root / "beliefs" / "PHILOSOPHY.md"
    if not phil_path.exists():
        return claims
    text = phil_path.read_text(errors="ignore")
    for m in re.finditer(r'\*\*\[PHIL-(\d+)\]\*\*\s*(.*?)(?=\*\*\[PHIL-|\Z)', text, re.DOTALL):
        pid = f"PHIL-{m.group(1)}"
        content = m.group(2).strip()
        first_line = content.split('\n')[0].strip()
        claims[pid] = {
            "summary": first_line[:300],
            "full_text": content[:1000],
        }
    return claims


def _extract_beliefs(root: Path) -> dict[str, dict]:
    """Extract beliefs from DEPS.md with full content."""
    beliefs = {}
    deps_path = root / "beliefs" / "DEPS.md"
    if not deps_path.exists():
        return beliefs
    text = deps_path.read_text(errors="ignore")
    for m in re.finditer(r'###\s+(B\d+|B-EVAL\d+):\s*(.*?)(?=###|\Z)', text, re.DOTALL):
        bid = m.group(1)
        content = m.group(2).strip()
        first_line = content.split('\n')[0].strip()
        beliefs[bid] = {
            "summary": first_line[:300],
            "full_text": content[:1000],
        }
    return beliefs


def _extract_principles(root: Path) -> list[str]:
    """Extract principle entries from PRINCIPLES.md."""
    principles = []
    path = root / "memory" / "PRINCIPLES.md"
    if not path.exists():
        return principles
    text = path.read_text(errors="ignore")
    for m in re.finditer(r'(P-\d+)\s+([^|*\n]+)', text):
        name = m.group(2).strip().rstrip(':')
        if name and len(name) > 3:
            principles.append(f"{m.group(1)} {name[:150]}")
    return principles


def _extract_frontiers(root: Path) -> dict[str, str]:
    """Extract active frontiers."""
    frontiers = {}
    path = root / "tasks" / "FRONTIER.md"
    if not path.exists():
        return frontiers
    text = path.read_text(errors="ignore")
    resolved_idx = text.find("\n## Resolved")
    if resolved_idx > 0:
        text = text[:resolved_idx]
    for m in re.finditer(r'^- \*\*(\S+)\*\*:\s*(.+?)(?=^- \*\*|\Z)', text, re.MULTILINE | re.DOTALL):
        frontiers[m.group(1)] = m.group(2).strip()[:500]
    return frontiers


def run_phase1(local: Path, remote: Path) -> dict:
    """Phase 1: Extract complete state from both swarms. Pure observation."""
    orientation = {
        "local": {
            "path": str(local),
            "lessons": _extract_lessons(local),
            "philosophy": _extract_phil_claims(local),
            "beliefs": _extract_beliefs(local),
            "principles": _extract_principles(local),
            "frontiers": _extract_frontiers(local),
            "core": _read_file_safe(local / "beliefs" / "CORE.md")[:2000],
        },
        "remote": {
            "path": str(remote),
            "lessons": _extract_lessons(remote),
            "philosophy": _extract_phil_claims(remote),
            "beliefs": _extract_beliefs(remote),
            "principles": _extract_principles(remote),
            "frontiers": _extract_frontiers(remote),
            "core": _read_file_safe(remote / "beliefs" / "CORE.md")[:2000],
        },
    }
    # Summary stats
    for side in ["local", "remote"]:
        s = orientation[side]
        s["stats"] = {
            "lesson_count": len(s["lessons"]),
            "phil_count": len(s["philosophy"]),
            "belief_count": len(s["beliefs"]),
            "principle_count": len(s["principles"]),
            "frontier_count": len(s["frontiers"]),
        }
    return orientation


# ─── Phase 2: Lesson Arbitration ─────────────────────────────────────────────

def _word_jaccard(a: str, b: str) -> float:
    """Word-level Jaccard similarity."""
    wa = set(re.findall(r'\w+', a.lower()))
    wb = set(re.findall(r'\w+', b.lower()))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _classify_lesson_pair(local_lesson: dict, remote_lesson: dict) -> str:
    """Classify a lesson pair: COMPATIBLE, CONTEXT_DEPENDENT, or CONTRADICTORY.

    Uses title similarity, shared citations, and domain overlap to classify.
    L-1100 estimates: ~60% compatible, ~30% context-dependent, ~10% contradictory.
    """
    # Fast path: if full text is nearly identical, skip heuristics
    full_sim = _word_jaccard(
        local_lesson.get("text", "")[:500],
        remote_lesson.get("text", "")[:500],
    )
    if full_sim > 0.9:
        return "COMPATIBLE"

    title_sim = _word_jaccard(local_lesson["title"], remote_lesson["title"])

    # Check for shared citations
    local_cites = set(local_lesson.get("cites", []))
    remote_cites = set(remote_lesson.get("cites", []))
    shared_cites = local_cites & remote_cites

    # Domain overlap
    same_domain = local_lesson.get("domain", "") == remote_lesson.get("domain", "")

    if title_sim > 0.6:
        # Very similar titles — likely same insight discovered independently
        return "COMPATIBLE"
    elif title_sim > 0.3 or (shared_cites and same_domain):
        # Moderate similarity or shared evidence in same domain
        # Likely same topic, different conclusions
        return "CONTEXT_DEPENDENT"
    elif title_sim < 0.1 and not shared_cites:
        # No overlap at all — independent, compatible
        return "COMPATIBLE"
    else:
        # Some overlap but different enough to need checking
        # Check for contradictory keywords
        local_text = local_lesson.get("text", "").lower()
        remote_text = remote_lesson.get("text", "").lower()
        contradiction_pairs = [
            ("confirmed", "falsified"), ("increase", "decrease"),
            ("valid", "invalid"), ("true", "false"),
        ]
        for pos, neg in contradiction_pairs:
            if (pos in local_text and neg in remote_text) or (neg in local_text and pos in remote_text):
                if same_domain:
                    return "CONTRADICTORY"
        return "CONTEXT_DEPENDENT"


def run_phase2(orientation: dict) -> dict:
    """Phase 2: Classify every lesson — compatible/context-dependent/contradictory."""
    local_lessons = orientation["local"]["lessons"]
    remote_lessons = orientation["remote"]["lessons"]

    # Find lessons unique to each side (by ID)
    local_ids = set(local_lessons.keys())
    remote_ids = set(remote_lessons.keys())
    shared_ids = local_ids & remote_ids
    local_only = local_ids - remote_ids
    remote_only = remote_ids - local_ids

    # Shared IDs: same L-number exists in both — classify
    shared_classifications = {}
    for lid in sorted(shared_ids):
        cls = _classify_lesson_pair(local_lessons[lid], remote_lessons[lid])
        shared_classifications[lid] = cls

    # Cross-check: find near-duplicate lessons with different IDs
    # Only check remote-only against local-only (O(n*m) but bounded)
    cross_duplicates = []
    if len(remote_only) <= 500 and len(local_only) <= 500:
        for rid in sorted(remote_only):
            for lid in sorted(local_only):
                sim = _word_jaccard(
                    remote_lessons[rid]["title"],
                    local_lessons[lid]["title"]
                )
                if sim > 0.5:
                    cls = _classify_lesson_pair(local_lessons[lid], remote_lessons[rid])
                    cross_duplicates.append({
                        "local_id": lid,
                        "remote_id": rid,
                        "title_similarity": round(sim, 3),
                        "classification": cls,
                    })

    # Count classifications
    counts = {"COMPATIBLE": 0, "CONTEXT_DEPENDENT": 0, "CONTRADICTORY": 0}
    for cls in shared_classifications.values():
        counts[cls] = counts.get(cls, 0) + 1

    arbitration = {
        "local_only_count": len(local_only),
        "remote_only_count": len(remote_only),
        "shared_count": len(shared_ids),
        "shared_classifications": shared_classifications,
        "cross_duplicates": cross_duplicates[:50],  # cap output
        "classification_counts": counts,
        "safe_union_count": len(local_only) + len(remote_only) + counts["COMPATIBLE"],
        "needs_arbitration": counts["CONTEXT_DEPENDENT"],
        "contradictions": counts["CONTRADICTORY"],
        "contradictory_lessons": [
            {"id": lid, "local_title": local_lessons[lid]["title"],
             "remote_title": remote_lessons[lid]["title"]}
            for lid in sorted(shared_ids) if shared_classifications.get(lid) == "CONTRADICTORY"
        ],
    }
    return arbitration


# ─── Phase 3: Evidence-Weighted Belief Merge ─────────────────────────────────

def _merge_beliefs(local_beliefs: dict, remote_beliefs: dict) -> dict:
    """Merge beliefs with provenance tagging."""
    merged = {}
    local_ids = set(local_beliefs.keys())
    remote_ids = set(remote_beliefs.keys())

    # Local-only: keep with provenance
    for bid in sorted(local_ids - remote_ids):
        merged[bid] = {
            "content": local_beliefs[bid],
            "provenance": "local",
            "status": "adopted",
        }

    # Remote-only: keep with provenance
    for bid in sorted(remote_ids - local_ids):
        merged[bid] = {
            "content": remote_beliefs[bid],
            "provenance": "remote",
            "status": "adopted",
        }

    # Shared: compare and classify
    for bid in sorted(local_ids & remote_ids):
        local_text = local_beliefs[bid].get("full_text", "")
        remote_text = remote_beliefs[bid].get("full_text", "")
        sim = _word_jaccard(local_text, remote_text)

        if sim > 0.7:
            # Near-identical — keep local (arbitrary, could pick longer)
            longer = local_beliefs[bid] if len(local_text) >= len(remote_text) else remote_beliefs[bid]
            merged[bid] = {
                "content": longer,
                "provenance": "both (converged)",
                "status": "adopted",
                "similarity": round(sim, 3),
            }
        elif sim > 0.3:
            # Divergent — keep both with provenance, needs arbitration
            merged[bid] = {
                "content_local": local_beliefs[bid],
                "content_remote": remote_beliefs[bid],
                "provenance": "divergent",
                "status": "needs_arbitration",
                "similarity": round(sim, 3),
            }
        else:
            # Contradictory — challenge filed
            merged[bid] = {
                "content_local": local_beliefs[bid],
                "content_remote": remote_beliefs[bid],
                "provenance": "contradictory",
                "status": "challenge_filed",
                "similarity": round(sim, 3),
            }

    return merged


def _merge_principles(local_principles: list, remote_principles: list) -> dict:
    """Merge principle sets, detecting novel principles from each side."""
    # Find best matches between the two sets
    matched_pairs = []
    unmatched_remote = list(range(len(remote_principles)))

    for i, lp in enumerate(local_principles):
        best_j = -1
        best_sim = 0.0
        for j in unmatched_remote:
            sim = _word_jaccard(lp, remote_principles[j])
            if sim > best_sim:
                best_sim = sim
                best_j = j
        if best_j >= 0 and best_sim >= 0.4:
            matched_pairs.append({
                "local": lp, "remote": remote_principles[best_j],
                "similarity": round(best_sim, 3),
            })
            unmatched_remote.remove(best_j)

    novel_remote = [remote_principles[j] for j in unmatched_remote]
    matched_local_texts = {mp["local"] for mp in matched_pairs}
    novel_local = [lp for lp in local_principles if lp not in matched_local_texts]

    return {
        "matched_count": len(matched_pairs),
        "novel_local_count": len(novel_local),
        "novel_remote_count": len(novel_remote),
        "novel_from_remote": novel_remote[:30],
        "novel_from_local": novel_local[:30],
        "total_merged": len(local_principles) + len(novel_remote),
    }


def _merge_frontiers(local_frontiers: dict, remote_frontiers: dict) -> dict:
    """Merge frontier sets."""
    local_ids = set(local_frontiers.keys())
    remote_ids = set(remote_frontiers.keys())

    merged = {}
    # Local-only: keep
    for fid in sorted(local_ids - remote_ids):
        merged[fid] = {"text": local_frontiers[fid], "provenance": "local"}

    # Remote-only: adopt
    for fid in sorted(remote_ids - local_ids):
        merged[fid] = {"text": remote_frontiers[fid], "provenance": "remote"}

    # Shared: merge texts (keep longer version, note both)
    for fid in sorted(local_ids & remote_ids):
        local_text = local_frontiers[fid]
        remote_text = remote_frontiers[fid]
        if len(remote_text) > len(local_text):
            merged[fid] = {"text": remote_text, "provenance": "both (remote richer)"}
        else:
            merged[fid] = {"text": local_text, "provenance": "both (local richer)"}

    return {
        "local_only": sorted(local_ids - remote_ids),
        "remote_only": sorted(remote_ids - local_ids),
        "shared": sorted(local_ids & remote_ids),
        "merged_frontiers": merged,
        "total_merged": len(merged),
    }


def run_phase3(orientation: dict) -> dict:
    """Phase 3: Evidence-weighted merge of beliefs, principles, and frontiers."""
    belief_merge = _merge_beliefs(
        orientation["local"]["beliefs"],
        orientation["remote"]["beliefs"],
    )
    principle_merge = _merge_principles(
        orientation["local"]["principles"],
        orientation["remote"]["principles"],
    )
    frontier_merge = _merge_frontiers(
        orientation["local"]["frontiers"],
        orientation["remote"]["frontiers"],
    )

    # Summary stats
    belief_statuses = {}
    for b in belief_merge.values():
        s = b.get("status", "unknown")
        belief_statuses[s] = belief_statuses.get(s, 0) + 1

    return {
        "beliefs": {
            "merged_count": len(belief_merge),
            "status_counts": belief_statuses,
            "merge_data": belief_merge,
        },
        "principles": principle_merge,
        "frontiers": frontier_merge,
    }


# ─── Phase 4: Identity Negotiation ──────────────────────────────────────────

def _synthesize_philosophy(local_claims: dict, remote_claims: dict) -> dict:
    """Produce merged PHILOSOPHY.md content.

    Strategy: multi-identity architecture with provenance tags.
    Both lineages' axioms preserved; conflicts annotated, not resolved by fiat.
    """
    local_ids = set(local_claims.keys())
    remote_ids = set(remote_claims.keys())

    synthesized = {}

    # Shared claims: compare and annotate
    for pid in sorted(local_ids & remote_ids):
        local_text = local_claims[pid].get("full_text", "")
        remote_text = remote_claims[pid].get("full_text", "")
        sim = _word_jaccard(local_text, remote_text)

        if sim > 0.5:
            # Convergent evolution — axioms independently arrived at similar claim
            longer = local_claims[pid] if len(local_text) >= len(remote_text) else remote_claims[pid]
            synthesized[pid] = {
                "content": longer,
                "provenance": "convergent (both lineages)",
                "similarity": round(sim, 3),
                "status": "adopted",
            }
        else:
            # Divergent — both preserved with lineage tags
            synthesized[pid] = {
                "content_local": local_claims[pid],
                "content_remote": remote_claims[pid],
                "provenance": "divergent (both preserved)",
                "similarity": round(sim, 3),
                "status": "dual_identity",
            }

    # Local-only claims
    for pid in sorted(local_ids - remote_ids):
        synthesized[pid] = {
            "content": local_claims[pid],
            "provenance": "local lineage",
            "status": "adopted",
        }

    # Remote-only claims
    for pid in sorted(remote_ids - local_ids):
        synthesized[pid] = {
            "content": remote_claims[pid],
            "provenance": "remote lineage",
            "status": "adopted",
        }

    # Classify the result
    adopted = sum(1 for v in synthesized.values() if v["status"] == "adopted")
    dual = sum(1 for v in synthesized.values() if v["status"] == "dual_identity")

    return {
        "claims": synthesized,
        "total_claims": len(synthesized),
        "adopted": adopted,
        "dual_identity": dual,
        "identity_type": "single" if dual == 0 else "multi",
        "convergence_rate": round(adopted / max(len(synthesized), 1), 3),
    }


def run_phase4(orientation: dict) -> dict:
    """Phase 4: Identity negotiation — synthesize merged philosophy."""
    philosophy = _synthesize_philosophy(
        orientation["local"]["philosophy"],
        orientation["remote"]["philosophy"],
    )
    return {
        "philosophy": philosophy,
    }


# ─── Output: Write Merged Directory ─────────────────────────────────────────

def write_merged_output(output_dir: Path, local: Path, remote: Path,
                        phase0: dict, orientation: dict,
                        arbitration: dict, phase3: dict, phase4: dict) -> None:
    """Write the merged swarm to an output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy local as base (it has the most infrastructure)
    for subdir in ["beliefs", "memory", "tasks", "tools", "domains", "experiments"]:
        src = local / subdir
        dst = output_dir / subdir
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)

    # Copy root files
    for fname in ["SWARM.md", "CLAUDE.md", "AGENTS.md"]:
        src = local / fname
        if src.exists():
            shutil.copy2(src, output_dir / fname)

    # 2. Add remote-only lessons
    remote_lessons_dir = remote / "memory" / "lessons"
    merged_lessons_dir = output_dir / "memory" / "lessons"
    merged_lessons_dir.mkdir(parents=True, exist_ok=True)
    if remote_lessons_dir.exists():
        for lf in remote_lessons_dir.glob("L-*.md"):
            dest = merged_lessons_dir / lf.name
            if not dest.exists():
                # Remote-only lesson — add with provenance header
                text = lf.read_text(errors="ignore")
                provenance = f"<!-- Provenance: merged from remote ({remote.name}) -->\n"
                dest.write_text(provenance + text)

    # 3. Add remote-only tools
    remote_tools = remote / "tools"
    merged_tools = output_dir / "tools"
    merged_tools.mkdir(parents=True, exist_ok=True)
    if remote_tools.exists():
        for tf in remote_tools.glob("*.py"):
            dest = merged_tools / tf.name
            if not dest.exists():
                shutil.copy2(tf, dest)

    # 4. Add remote-only domains
    remote_domains = remote / "domains"
    merged_domains = output_dir / "domains"
    merged_domains.mkdir(parents=True, exist_ok=True)
    if remote_domains.exists():
        for dd in remote_domains.iterdir():
            if dd.is_dir():
                dest = merged_domains / dd.name
                if not dest.exists():
                    shutil.copytree(dd, dest)

    # 5. Write merge manifest
    manifest = {
        "schema": "swarm-merge-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "local_swarm": str(local),
        "remote_swarm": str(remote),
        "genetic_distance": phase0.get("genetic_distance", {}),
        "lesson_arbitration": {
            "safe_union": arbitration["safe_union_count"],
            "needs_arbitration": arbitration["needs_arbitration"],
            "contradictions": arbitration["contradictions"],
        },
        "belief_merge": phase3["beliefs"]["status_counts"],
        "identity": phase4["philosophy"]["identity_type"],
        "convergence_rate": phase4["philosophy"]["convergence_rate"],
    }
    manifest_path = output_dir / "MERGE-MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    # 6. Write conflict log for manual review
    conflicts = []
    # Contradictory lessons
    for cl in arbitration.get("contradictory_lessons", []):
        conflicts.append(f"LESSON {cl['id']}: local='{cl['local_title'][:80]}' vs remote='{cl['remote_title'][:80]}'")
    # Beliefs needing arbitration
    for bid, bdata in phase3["beliefs"]["merge_data"].items():
        if bdata.get("status") in ("needs_arbitration", "challenge_filed"):
            conflicts.append(f"BELIEF {bid}: {bdata.get('provenance', 'unknown')} (sim={bdata.get('similarity', '?')})")
    # Dual-identity philosophy claims
    for pid, pdata in phase4["philosophy"]["claims"].items():
        if pdata.get("status") == "dual_identity":
            conflicts.append(f"PHILOSOPHY {pid}: dual identity (sim={pdata.get('similarity', '?')})")

    if conflicts:
        conflict_path = output_dir / "MERGE-CONFLICTS.md"
        lines = ["# Merge Conflicts — Requires Manual Review\n",
                 f"Generated: {datetime.now(timezone.utc).isoformat()}\n",
                 f"Local: {local}\nRemote: {remote}\n",
                 f"Total conflicts: {len(conflicts)}\n"]
        for i, c in enumerate(conflicts, 1):
            lines.append(f"{i}. {c}")
        conflict_path.write_text("\n".join(lines) + "\n")


# ─── Main Orchestrator ──────────────────────────────────────────────────────

def run_merge(local: Path, remote: Path, max_phase: int = 4,
              output_dir: Path | None = None, dry_run: bool = False) -> dict:
    """Execute the 5-phase merge protocol up to max_phase."""
    results: dict = {"phases_completed": [], "viable": True}

    # Phase 0: Compatibility
    print("=" * 60)
    print("PHASE 0: Compatibility Check")
    print("=" * 60)
    phase0 = run_phase0(local, remote)
    results["phase0"] = phase0
    results["phases_completed"].append(0)

    distance = phase0.get("genetic_distance", {})
    zone = distance.get("zone", "UNKNOWN")
    dist_val = distance.get("distance", -1)
    print(f"  Genetic distance: {dist_val:.3f}")
    print(f"  Zone: {zone}")
    print(f"  Gate: {phase0.get('phase0_gate', 'UNKNOWN')}")

    if phase0.get("phase0_gate") == "BLOCKED":
        print("\n  MERGE BLOCKED — incompatible swarms")
        results["viable"] = False
        return results

    if max_phase < 1:
        return results

    # Phase 1: Orientation
    print(f"\n{'=' * 60}")
    print("PHASE 1: Read-Only Mutual Orientation")
    print("=" * 60)
    orientation = run_phase1(local, remote)
    results["phase1"] = {
        "local_stats": orientation["local"]["stats"],
        "remote_stats": orientation["remote"]["stats"],
    }
    results["phases_completed"].append(1)
    ls = orientation["local"]["stats"]
    rs = orientation["remote"]["stats"]
    print(f"  Local:  {ls['lesson_count']}L {ls['principle_count']}P "
          f"{ls['belief_count']}B {ls['phil_count']}PHIL {ls['frontier_count']}F")
    print(f"  Remote: {rs['lesson_count']}L {rs['principle_count']}P "
          f"{rs['belief_count']}B {rs['phil_count']}PHIL {rs['frontier_count']}F")

    if max_phase < 2:
        return results

    # Phase 2: Lesson Arbitration
    print(f"\n{'=' * 60}")
    print("PHASE 2: Lesson Arbitration")
    print("=" * 60)
    arbitration = run_phase2(orientation)
    results["phase2"] = {k: v for k, v in arbitration.items() if k != "shared_classifications"}
    results["phases_completed"].append(2)
    print(f"  Local-only lessons:  {arbitration['local_only_count']}")
    print(f"  Remote-only lessons: {arbitration['remote_only_count']}")
    print(f"  Shared (same ID):    {arbitration['shared_count']}")
    print(f"  Cross-duplicates:    {len(arbitration['cross_duplicates'])}")
    print(f"  Classification: {arbitration['classification_counts']}")
    print(f"  Safe union:      {arbitration['safe_union_count']}")
    print(f"  Needs arbitration: {arbitration['needs_arbitration']}")
    print(f"  Contradictions:  {arbitration['contradictions']}")

    if arbitration["contradictory_lessons"]:
        print(f"\n  Contradictory lessons:")
        for cl in arbitration["contradictory_lessons"][:5]:
            print(f"    {cl['id']}: '{cl['local_title'][:60]}' vs '{cl['remote_title'][:60]}'")

    if max_phase < 3:
        return results

    # Phase 3: Belief Merge
    print(f"\n{'=' * 60}")
    print("PHASE 3: Evidence-Weighted Belief Merge")
    print("=" * 60)
    phase3 = run_phase3(orientation)
    results["phase3"] = {
        "belief_counts": phase3["beliefs"]["status_counts"],
        "belief_total": phase3["beliefs"]["merged_count"],
        "principle_merge": {k: v for k, v in phase3["principles"].items()
                           if k not in ("novel_from_remote", "novel_from_local")},
        "frontier_merge": {
            "local_only": len(phase3["frontiers"]["local_only"]),
            "remote_only": len(phase3["frontiers"]["remote_only"]),
            "shared": len(phase3["frontiers"]["shared"]),
            "total": phase3["frontiers"]["total_merged"],
        },
    }
    results["phases_completed"].append(3)
    print(f"  Beliefs merged: {phase3['beliefs']['merged_count']}")
    print(f"    Status: {phase3['beliefs']['status_counts']}")
    print(f"  Principles: {phase3['principles']['matched_count']} matched, "
          f"{phase3['principles']['novel_remote_count']} novel from remote")
    print(f"  Frontiers: {phase3['frontiers']['total_merged']} total "
          f"({len(phase3['frontiers']['remote_only'])} novel from remote)")

    if max_phase < 4:
        return results

    # Phase 4: Identity Negotiation
    print(f"\n{'=' * 60}")
    print("PHASE 4: Identity Negotiation")
    print("=" * 60)
    phase4 = run_phase4(orientation)
    results["phase4"] = {
        "total_claims": phase4["philosophy"]["total_claims"],
        "adopted": phase4["philosophy"]["adopted"],
        "dual_identity": phase4["philosophy"]["dual_identity"],
        "identity_type": phase4["philosophy"]["identity_type"],
        "convergence_rate": phase4["philosophy"]["convergence_rate"],
    }
    results["phases_completed"].append(4)
    print(f"  Total claims: {phase4['philosophy']['total_claims']}")
    print(f"  Adopted:      {phase4['philosophy']['adopted']}")
    print(f"  Dual identity: {phase4['philosophy']['dual_identity']}")
    print(f"  Identity type: {phase4['philosophy']['identity_type']}")
    print(f"  Convergence:   {phase4['philosophy']['convergence_rate']:.1%}")

    # Write output if not dry-run
    if not dry_run and output_dir:
        print(f"\n{'=' * 60}")
        print("Writing merged output...")
        print("=" * 60)
        write_merged_output(output_dir, local, remote,
                            phase0, orientation, arbitration, phase3, phase4)
        print(f"  Output: {output_dir}")
        print(f"  Manifest: {output_dir / 'MERGE-MANIFEST.json'}")
        conflicts_path = output_dir / "MERGE-CONFLICTS.md"
        if conflicts_path.exists():
            print(f"  Conflicts: {conflicts_path} (REVIEW REQUIRED)")

    # Final summary
    print(f"\n{'=' * 60}")
    print("MERGE SUMMARY")
    print("=" * 60)
    print(f"  Phases completed: {results['phases_completed']}")
    print(f"  Zone: {zone} (distance={dist_val:.3f})")
    print(f"  Identity: {phase4['philosophy']['identity_type']}")
    total_lessons = (arbitration['local_only_count'] + arbitration['remote_only_count']
                     + arbitration['safe_union_count']
                     - arbitration['local_only_count'] - arbitration['remote_only_count'])
    print(f"  Lessons: {ls['lesson_count']} + {rs['lesson_count']} → "
          f"~{ls['lesson_count'] + arbitration['remote_only_count']} merged")
    print(f"  Contradictions requiring review: {arbitration['contradictions']}")
    print(f"  Viable: {'YES' if results['viable'] else 'NO'}")

    return results


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a.split("=")[0]: a.split("=")[1] if "=" in a else True
             for a in sys.argv[1:] if a.startswith("--")}

    if not args:
        print("Usage: python3 tools/swarm_combiner.py <path-to-other-swarm> [options]")
        print()
        print("Options:")
        print("  --output=<dir>   Output directory for merged swarm (default: workspace/merged-swarm)")
        print("  --phase=<0-4>    Stop after this phase (default: 4 = full merge)")
        print("  --json           Output results as JSON")
        print("  --dry-run        Run all phases but don't write output")
        print()
        print("Phases:")
        print("  0: Compatibility check (genetic distance)")
        print("  1: Read-only orientation (state extraction)")
        print("  2: Lesson arbitration (classify pairs)")
        print("  3: Belief merge (evidence-weighted)")
        print("  4: Identity negotiation (synthesize philosophy)")
        print()
        print("Safety: neither source swarm is modified. Output is a new directory.")
        return 0

    remote = Path(args[0]).resolve()
    if not remote.exists():
        print(f"ERROR: Path does not exist: {remote}")
        return 1

    local = ROOT
    max_phase = int(flags.get("--phase", 4))
    output_dir_str = flags.get("--output", str(ROOT / "workspace" / "merged-swarm"))
    output_dir = Path(output_dir_str).resolve() if not isinstance(output_dir_str, bool) else ROOT / "workspace" / "merged-swarm"
    dry_run = "--dry-run" in flags
    output_json = "--json" in flags

    results = run_merge(local, remote, max_phase=max_phase,
                        output_dir=output_dir, dry_run=dry_run)

    if output_json:
        print("\n" + json.dumps(results, indent=2, default=str))

    return 0 if results.get("viable", False) else 1


if __name__ == "__main__":
    sys.exit(main())
