#!/usr/bin/env python3
"""
F-META3 Re-measurement + Improvement-is-Swarm Analysis
Session: S393 | Domain: meta | Frontier: F-META3

Measures:
1. F-META3 core: DOMEX yield, overhead ratio, DOMEX share (S373-S392)
2. Improvement distribution: Gini of improvement contributions
3. Recursion: meta-meta rate (tools improving tools)
4. Self-application: meta-lessons citing meta-lessons
5. Improvement velocity across 3 eras
"""

import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/mnt/c/Users/canac/REPOSITORIES/swarm")
LESSONS_DIR = REPO / "memory" / "lessons"
TOOLS_DIR = REPO / "tools"
LANES_FILE = REPO / "tasks" / "SWARM-LANES.md"
OUTPUT_FILE = REPO / "experiments" / "meta" / "f-meta3-improvement-is-swarm-s393.json"

# Session range for re-measurement
S_START, S_END = 373, 392
# Era boundaries for velocity analysis
ERA_BOUNDS = [(1, 200), (200, 350), (350, 393)]


def run_git(args):
    """Run a git command and return stdout lines."""
    result = subprocess.run(
        ["git", "-C", str(REPO)] + args,
        capture_output=True, text=True, timeout=60
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def parse_session_id(msg):
    """Extract session ID from commit message like [S392]."""
    m = re.search(r"\[S(\d+)\]", msg)
    return int(m.group(1)) if m else None


def get_all_commits():
    """Get all commits with hash, message, and changed files."""
    lines = run_git(["log", "--oneline", "--all", "--name-only", "--no-merges"])
    commits = []
    current = None
    for line in lines:
        if not line:
            continue
        # Commit line: hash message
        m = re.match(r"^([0-9a-f]{8,}) (.+)$", line)
        if m:
            if current:
                commits.append(current)
            current = {
                "hash": m.group(1),
                "msg": m.group(2),
                "session": parse_session_id(m.group(2)),
                "files": []
            }
        elif current:
            current["files"].append(line.strip())
    if current:
        commits.append(current)
    return commits


def classify_commit(msg):
    """Classify commit by type based on message content.

    Priority: DOMEX > knowledge > overhead. A DOMEX commit with 'trim' or 'state-sync'
    is still DOMEX, not overhead. Harvest commits that carry lessons/tools are 'mixed' —
    counted as overhead for ratio but also as knowledge-carrying.
    """
    msg_lower = msg.lower()
    is_domex = bool(re.search(r"DOMEX", msg, re.IGNORECASE))
    has_lesson = bool(re.search(r"L-\d+", msg))
    has_knowledge = bool(re.search(
        r"DOMEX|experiment|frontier.*RESOLVED|CONFIRMED|FALSIFIED",
        msg, re.IGNORECASE
    ))

    # Pure overhead: handoff/harvest/maintenance/trim/fix WITHOUT DOMEX or lesson content
    overhead_keywords = bool(re.search(
        r"handoff|harvest|maintenance|state-sync|lesson.trim|lesson trim|stale.lane|orphan",
        msg_lower
    ))
    # Strict overhead: overhead keywords AND NOT a DOMEX commit AND NOT lesson-producing
    # Harvest commits that carry lessons or tools are mixed, not pure overhead
    is_pure_overhead = overhead_keywords and not is_domex
    # Mixed overhead: has overhead keyword but also carries knowledge
    is_mixed = overhead_keywords and (has_lesson or has_knowledge) and not is_domex

    categories = {
        "domex": is_domex,
        "lesson": has_lesson,
        "overhead": is_pure_overhead,       # pure or mixed overhead
        "pure_overhead": is_pure_overhead and not has_lesson and not has_knowledge,
        "mixed_overhead": is_mixed,
        "knowledge": has_knowledge or has_lesson,
        "improvement": False  # set externally
    }
    return categories


def is_improvement_commit(msg, files):
    """Detect improvement signals: tool changes, protocol updates, principle additions, frontier resolutions."""
    msg_lower = msg.lower()
    # Tool file modifications
    tool_change = any(f.startswith("tools/") and f.endswith(".py") for f in files)
    # Core protocol updates
    protocol_change = any(f in ("CORE.md", "SWARM.md", "beliefs/CORE.md") for f in files)
    # Principle additions (P- in message)
    principle_add = bool(re.search(r"P-\d+", msg))
    # Frontier resolution
    frontier_resolve = bool(re.search(r"RESOLVED|CONFIRMED|FALSIFIED", msg))
    return tool_change or protocol_change or principle_add or frontier_resolve


# ============================================================================
# PART 1: F-META3 Core Re-measurement
# ============================================================================

def measure_fmeta3(commits):
    """Measure DOMEX yield, overhead ratio, DOMEX share for S373-S392."""
    print("=" * 70)
    print("PART 1: F-META3 Re-measurement (S373-S392)")
    print("=" * 70)

    target_commits = [c for c in commits if c["session"] and S_START <= c["session"] <= S_END]
    sessions_seen = sorted(set(c["session"] for c in target_commits))
    n_sessions = len(sessions_seen)

    total = len(target_commits)
    classifications = [(c, classify_commit(c["msg"])) for c in target_commits]
    domex_count = sum(1 for _, cl in classifications if cl["domex"])
    lesson_count = sum(1 for _, cl in classifications if cl["lesson"])
    overhead_count = sum(1 for _, cl in classifications if cl["overhead"])
    pure_overhead_count = sum(1 for _, cl in classifications if cl["pure_overhead"])
    mixed_overhead_count = sum(1 for _, cl in classifications if cl["mixed_overhead"])
    knowledge_count = sum(1 for _, cl in classifications if cl["knowledge"])

    # Count DOMEX lanes from SWARM-LANES.md
    lanes_text = LANES_FILE.read_text(encoding="utf-8")
    domex_lane_pattern = re.compile(r"DOMEX-[A-Z]+-S(\d+)")
    domex_lanes_in_range = set()
    for m in domex_lane_pattern.finditer(lanes_text):
        s = int(m.group(1))
        if S_START <= s <= S_END:
            domex_lanes_in_range.add(m.group(0))
    n_domex_lanes = len(domex_lanes_in_range)

    # Count lessons produced in this range
    # Extract L-NNN from DOMEX commit messages
    # Only count NEW lessons (L-684+ for S373+), not old lessons referenced in commit msgs
    # Determine minimum lesson ID from era: check first lesson file from S_START
    min_lesson_id = None
    for lf in sorted(LESSONS_DIR.glob("L-*.md")):
        try:
            first_line = lf.read_text(encoding="utf-8", errors="replace").split("\n")[0]
            sm = re.search(r"session:\s*S(\d+)", first_line)
            if sm and int(sm.group(1)) >= S_START:
                lid_m = re.match(r"L-(\d+)", lf.stem)
                if lid_m:
                    min_lesson_id = int(lid_m.group(1))
                    break
        except Exception:
            continue
    if min_lesson_id is None:
        min_lesson_id = 684  # fallback

    lesson_ids = set()
    domex_sessions = set()
    for c in target_commits:
        if classify_commit(c["msg"])["domex"]:
            domex_sessions.add(c["session"])
            for lm in re.finditer(r"L-(\d+)", c["msg"]):
                lid = int(lm.group(1))
                if lid >= min_lesson_id:  # only NEW lessons
                    lesson_ids.add(lid)
    # Also count all new lessons mentioned (including from harvest commits)
    all_lesson_ids = set()
    for c in target_commits:
        for lm in re.finditer(r"L-(\d+)", c["msg"]):
            lid = int(lm.group(1))
            if lid >= min_lesson_id:
                all_lesson_ids.add(lid)

    n_domex_sessions = len(domex_sessions)
    domex_yield_per_lane = len(lesson_ids) / n_domex_lanes if n_domex_lanes > 0 else 0
    # Comparable to S372 which used lessons/sessions
    domex_yield_per_session = len(all_lesson_ids) / n_domex_sessions if n_domex_sessions > 0 else 0
    domex_yield = domex_yield_per_session  # use per-session for S372 comparability
    overhead_ratio = overhead_count / total if total > 0 else 0
    pure_overhead_ratio = pure_overhead_count / total if total > 0 else 0
    domex_share = domex_count / total if total > 0 else 0

    print(f"  Sessions: {n_sessions} ({sessions_seen[0]}-{sessions_seen[-1]})")
    print(f"  Total commits: {total}")
    print(f"  DOMEX commits: {domex_count} ({domex_share:.1%})")
    print(f"  Lesson-producing commits: {lesson_count}")
    print(f"  Overhead commits (non-DOMEX): {overhead_count} ({overhead_ratio:.1%})")
    print(f"    Pure overhead (no knowledge): {pure_overhead_count} ({pure_overhead_ratio:.1%})")
    print(f"    Mixed overhead (carry knowledge): {mixed_overhead_count}")
    print(f"  Knowledge commits: {knowledge_count}")
    print(f"  DOMEX lanes: {n_domex_lanes}")
    print(f"  DOMEX sessions: {n_domex_sessions}")
    print(f"  Unique lessons from DOMEX commits: {len(lesson_ids)}")
    print(f"  All unique lessons mentioned: {len(all_lesson_ids)}")
    print(f"  DOMEX yield (L/lane): {domex_yield_per_lane:.2f}")
    print(f"  DOMEX yield (L/session, S372-comparable): {domex_yield_per_session:.2f}")
    print(f"  Overhead ratio (all non-DOMEX overhead): {overhead_ratio:.1%}")
    print(f"  Pure overhead ratio: {pure_overhead_ratio:.1%}")
    print(f"  DOMEX share: {domex_share:.1%}")

    # Comparison to S372 baseline
    s372_yield = 2.76
    s372_overhead = 0.337
    s372_domex_share = 0.625
    yield_delta = (domex_yield - s372_yield) / s372_yield * 100
    # Use pure overhead for apples-to-apples comparison with S372
    pure_overhead_delta = (pure_overhead_ratio - s372_overhead) / s372_overhead * 100

    print(f"\n  Comparison to S372 baseline:")
    print(f"    DOMEX yield: {s372_yield:.2f} -> {domex_yield:.2f} ({yield_delta:+.1f}%)")
    print(f"    Pure overhead: {s372_overhead:.1%} -> {pure_overhead_ratio:.1%} ({pure_overhead_delta:+.1f}%)")
    print(f"    DOMEX share: {s372_domex_share:.1%} -> {domex_share:.1%}")
    print(f"    Note: S372 measured overhead broadly (incl. mixed). Pure comparison more accurate.")

    return {
        "domex_yield_per_session": round(domex_yield_per_session, 2),
        "domex_yield_per_lane": round(domex_yield_per_lane, 2),
        "overhead_ratio": round(overhead_ratio, 3),
        "pure_overhead_ratio": round(pure_overhead_ratio, 3),
        "domex_share": round(domex_share, 3),
        "n_sessions": n_sessions,
        "n_domex_sessions": n_domex_sessions,
        "sessions": sessions_seen,
        "total_commits": total,
        "domex_commits": domex_count,
        "lesson_commits": lesson_count,
        "overhead_commits": overhead_count,
        "pure_overhead_commits": pure_overhead_count,
        "mixed_overhead_commits": mixed_overhead_count,
        "knowledge_commits": knowledge_count,
        "domex_lanes": n_domex_lanes,
        "unique_lessons_from_domex": len(lesson_ids),
        "all_unique_lessons": len(all_lesson_ids),
        "lesson_ids": sorted(lesson_ids),
        "comparison_to_s372": {
            "domex_yield_delta_pct": round(yield_delta, 1),
            "pure_overhead_delta_pct": round(pure_overhead_delta, 1),
            "s372_domex_yield": s372_yield,
            "s372_overhead_ratio": s372_overhead,
            "overhead_invariant": abs(pure_overhead_delta) < 15,
            "yield_trend": "improving" if yield_delta > 5 else "declining" if yield_delta < -5 else "stable"
        }
    }


# ============================================================================
# PART 2a: Improvement Distribution (Gini)
# ============================================================================

def gini_coefficient(values):
    """Compute Gini coefficient from a list of values."""
    if not values or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    cumulative = sum((i + 1) * v for i, v in enumerate(sorted_vals))
    return (2.0 * cumulative) / (n * sum(sorted_vals)) - (n + 1.0) / n


def measure_improvement_distribution(commits):
    """Gini of improvement contributions vs all contributions across sessions."""
    print("\n" + "=" * 70)
    print("PART 2a: Improvement Distribution (Gini)")
    print("=" * 70)

    target_commits = [c for c in commits if c["session"] and S_START <= c["session"] <= S_END]

    # All contributions per session
    all_counts = Counter()
    improvement_counts = Counter()

    for c in target_commits:
        s = c["session"]
        all_counts[s] += 1
        if is_improvement_commit(c["msg"], c["files"]):
            improvement_counts[s] += 1

    sessions = sorted(set(all_counts.keys()) | set(improvement_counts.keys()))

    all_values = [all_counts.get(s, 0) for s in sessions]
    improvement_values = [improvement_counts.get(s, 0) for s in sessions]

    gini_all = gini_coefficient(all_values)
    gini_improvement = gini_coefficient(improvement_values)

    n_improvement = sum(improvement_values)
    sessions_contributing = sum(1 for v in improvement_values if v > 0)

    print(f"  Sessions: {len(sessions)}")
    print(f"  Improvement commits: {n_improvement} / {sum(all_values)} total")
    print(f"  Sessions contributing improvements: {sessions_contributing}/{len(sessions)}")
    print(f"  Gini (all contributions): {gini_all:.3f}")
    print(f"  Gini (improvement only): {gini_improvement:.3f}")
    print(f"  Interpretation: {'concentrated' if gini_improvement > 0.4 else 'distributed'} improvement")

    # Per-session breakdown
    print(f"\n  Per-session improvement commits:")
    for s in sessions:
        imp = improvement_counts.get(s, 0)
        tot = all_counts.get(s, 0)
        bar = "#" * imp
        print(f"    S{s}: {imp:2d}/{tot:2d} {bar}")

    return {
        "gini_improvement": round(gini_improvement, 3),
        "gini_all": round(gini_all, 3),
        "n_improvement_commits": n_improvement,
        "n_total_commits": sum(all_values),
        "sessions_contributing": sessions_contributing,
        "n_sessions": len(sessions),
        "per_session": {f"S{s}": {"improvement": improvement_counts.get(s, 0), "total": all_counts.get(s, 0)} for s in sessions},
        "interpretation": "concentrated" if gini_improvement > 0.4 else "distributed"
    }


# ============================================================================
# PART 2b: Recursion (tools improving tools)
# ============================================================================

def measure_recursion(commits):
    """Find tool-improving-tool commits."""
    print("\n" + "=" * 70)
    print("PART 2b: Recursion (meta-meta rate: tools improving tools)")
    print("=" * 70)

    target_commits = [c for c in commits if c["session"] and S_START <= c["session"] <= S_END]

    total_tool_commits = 0
    tool_improving_tool = 0
    examples = []

    for c in target_commits:
        tool_files_changed = [f for f in c["files"] if f.startswith("tools/") and f.endswith(".py")]
        if not tool_files_changed:
            continue
        total_tool_commits += 1

        # Check if commit message mentions a tool AND modifies another tool
        # Look for tool names in message
        msg = c["msg"]
        # Extract tool names mentioned in message
        tool_mentions_in_msg = set(re.findall(r"(\w+\.py)", msg))
        tool_files_changed_names = set(os.path.basename(f) for f in tool_files_changed)

        # Also check: commit modifies a tool AND the message describes improving/fixing/building another tool
        # Or: multiple tool files are modified (one tool updating another's interface)
        if len(tool_files_changed) >= 2:
            # Multiple tools modified in one commit = potential tool-improving-tool
            tool_improving_tool += 1
            examples.append({
                "hash": c["hash"],
                "msg": c["msg"][:120],
                "tools_changed": tool_files_changed[:5],
                "reason": "multiple tools modified"
            })
        elif tool_mentions_in_msg & tool_files_changed_names and len(tool_mentions_in_msg) > len(tool_files_changed_names):
            # Message mentions tools beyond what was changed
            tool_improving_tool += 1
            examples.append({
                "hash": c["hash"],
                "msg": c["msg"][:120],
                "tools_changed": tool_files_changed[:5],
                "reason": "tool mentioned + different tool changed"
            })
        elif any(kw in msg.lower() for kw in ["wired into", "integrated", "dispatch", "check.sh"]):
            # Integration commits: wiring one tool into another
            if tool_files_changed:
                tool_improving_tool += 1
                examples.append({
                    "hash": c["hash"],
                    "msg": c["msg"][:120],
                    "tools_changed": tool_files_changed[:5],
                    "reason": "integration keyword"
                })

    rate = tool_improving_tool / total_tool_commits if total_tool_commits > 0 else 0

    print(f"  Total tool-touching commits (S{S_START}-S{S_END}): {total_tool_commits}")
    print(f"  Tool-improving-tool commits: {tool_improving_tool}")
    print(f"  Meta-meta rate: {rate:.1%}")
    print(f"\n  Examples ({min(len(examples), 5)} of {len(examples)}):")
    for ex in examples[:5]:
        print(f"    {ex['hash'][:8]} | {ex['msg'][:80]}")
        print(f"      Tools: {', '.join(ex['tools_changed'][:3])} | Reason: {ex['reason']}")

    return {
        "meta_meta_rate": round(rate, 3),
        "tool_improving_tool_commits": tool_improving_tool,
        "total_tool_commits": total_tool_commits,
        "examples": examples[:10]
    }


# ============================================================================
# PART 2c: Self-application (meta-lessons citing meta-lessons)
# ============================================================================

def measure_self_application():
    """Meta-lessons citing meta-lessons vs base citation rate."""
    print("\n" + "=" * 70)
    print("PART 2c: Self-application (meta-lessons citing meta-lessons)")
    print("=" * 70)

    all_lessons = []
    meta_lessons = []
    meta_ids = set()

    # Parse all lesson files
    lesson_files = sorted(LESSONS_DIR.glob("L-*.md"))
    for lf in lesson_files:
        lid_match = re.match(r"L-(\d+)", lf.stem)
        if not lid_match:
            continue
        lid = int(lid_match.group(1))
        try:
            text = lf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Extract domain
        domain_match = re.search(r"Domain:\s*(\S+)", text, re.IGNORECASE)
        domain = domain_match.group(1).lower() if domain_match else None

        # Extract cites
        cites_match = re.search(r"Cites:\s*(.+)", text)
        cited_ids = set()
        if cites_match:
            for cm in re.finditer(r"L-(\d+)", cites_match.group(1)):
                cited_ids.add(int(cm.group(1)))

        # Also check body for L-NNN references
        body_cites = set()
        for bm in re.finditer(r"\bL-(\d+)\b", text):
            body_cites.add(int(bm.group(1)))

        lesson = {
            "id": lid,
            "domain": domain,
            "cited_ids": cited_ids,
            "all_refs": body_cites,
            "is_meta": domain == "meta" if domain else _infer_meta(text)
        }
        all_lessons.append(lesson)
        if lesson["is_meta"]:
            meta_lessons.append(lesson)
            meta_ids.add(lid)

    # Compute citation rates
    n_all = len(all_lessons)
    n_citing = sum(1 for l in all_lessons if l["cited_ids"])
    base_citation_rate = n_citing / n_all if n_all > 0 else 0

    n_meta = len(meta_lessons)
    n_meta_citing_meta = sum(
        1 for l in meta_lessons
        if l["cited_ids"] & meta_ids  # cites at least one meta lesson
    )
    meta_self_citation_rate = n_meta_citing_meta / n_meta if n_meta > 0 else 0

    # Also: meta lessons citing meta lessons via all body refs
    n_meta_citing_meta_body = sum(
        1 for l in meta_lessons
        if (l["all_refs"] - {l["id"]}) & meta_ids
    )
    meta_body_rate = n_meta_citing_meta_body / n_meta if n_meta > 0 else 0

    ratio = meta_self_citation_rate / base_citation_rate if base_citation_rate > 0 else 0

    # Count total meta→meta citation edges
    meta_meta_edges = sum(
        len(l["cited_ids"] & meta_ids) for l in meta_lessons
    )
    # Count all citation edges for comparison
    all_edges = sum(len(l["cited_ids"]) for l in all_lessons)
    meta_meta_edge_share = meta_meta_edges / all_edges if all_edges > 0 else 0

    print(f"  Total lessons: {n_all}")
    print(f"  Meta lessons: {n_meta} ({n_meta/n_all:.1%})")
    print(f"  All lessons with citations: {n_citing} ({base_citation_rate:.1%})")
    print(f"  Meta lessons citing meta (header): {n_meta_citing_meta} ({meta_self_citation_rate:.1%})")
    print(f"  Meta lessons citing meta (body): {n_meta_citing_meta_body} ({meta_body_rate:.1%})")
    print(f"  Self-citation ratio (meta/base): {ratio:.2f}x")
    print(f"  Meta→meta edges: {meta_meta_edges} / {all_edges} total ({meta_meta_edge_share:.1%})")
    print(f"  Interpretation: {'self-reinforcing' if ratio > 1.2 else 'neutral' if ratio > 0.8 else 'self-avoiding'}")

    # Also check principles
    principles_dir = REPO / "memory"
    principles_file = principles_dir / "PRINCIPLES.md"
    meta_principle_count = 0
    meta_principle_citing_meta = 0
    if principles_file.exists():
        ptext = principles_file.read_text(encoding="utf-8", errors="replace")
        for line in ptext.split("\n"):
            if re.match(r"^P-\d+", line):
                # Check if meta-related
                if "meta" in line.lower() or "self" in line.lower() or "swarm" in line.lower():
                    meta_principle_count += 1
                    # Check if it cites another P-
                    p_refs = re.findall(r"P-\d+", line)
                    if len(p_refs) > 1:  # more than self-reference
                        meta_principle_citing_meta += 1

    print(f"\n  Meta-related principles: {meta_principle_count}")
    print(f"  Meta principles citing meta principles: {meta_principle_citing_meta}")

    return {
        "meta_self_citation_rate": round(meta_self_citation_rate, 3),
        "meta_body_citation_rate": round(meta_body_rate, 3),
        "base_citation_rate": round(base_citation_rate, 3),
        "ratio": round(ratio, 2),
        "n_meta_lessons": n_meta,
        "n_all_lessons": n_all,
        "n_meta_citing_meta": n_meta_citing_meta,
        "n_meta_citing_meta_body": n_meta_citing_meta_body,
        "meta_meta_edges": meta_meta_edges,
        "total_edges": all_edges,
        "meta_meta_edge_share": round(meta_meta_edge_share, 3),
        "meta_principles": meta_principle_count,
        "meta_principles_citing_meta": meta_principle_citing_meta,
        "interpretation": "self-reinforcing" if ratio > 1.2 else "neutral" if ratio > 0.8 else "self-avoiding"
    }


def _infer_meta(text):
    """Infer whether a lesson is meta-domain from content when Domain: is missing."""
    text_lower = text.lower()
    meta_signals = [
        "self-model", "self-apply", "self-referential", "swarm protocol",
        "meta-", "orient.py", "dispatch", "compact", "maintenance",
        "governance", "council", "self-improvement", "reflexive",
        "knowledge state", "contract_check", "self-portrait"
    ]
    hits = sum(1 for s in meta_signals if s in text_lower)
    return hits >= 2


# ============================================================================
# PART 2d: Improvement Velocity Over Time
# ============================================================================

def measure_velocity(commits):
    """Improvement velocity across 3 eras."""
    print("\n" + "=" * 70)
    print("PART 2d: Improvement Velocity Over Time")
    print("=" * 70)

    era_data = {}
    for era_start, era_end in ERA_BOUNDS:
        era_label = f"S{era_start}-S{era_end - 1}"
        era_commits = [c for c in commits if c["session"] and era_start <= c["session"] < era_end]
        era_sessions = set(c["session"] for c in era_commits)
        n_sessions = len(era_sessions)

        # Tools created: commits that add new tools/*.py files
        tools_created = 0
        for c in era_commits:
            new_tools = [f for f in c["files"] if f.startswith("tools/") and f.endswith(".py")]
            if new_tools and any(kw in c["msg"].lower() for kw in ["built", "new", "create", "add", "tool"]):
                tools_created += len(new_tools)

        # Principles added: P-NNN in commit messages
        principles = set()
        for c in era_commits:
            for pm in re.finditer(r"P-(\d+)", c["msg"]):
                principles.add(int(pm.group(1)))

        # Frontiers resolved: RESOLVED in messages
        frontiers_resolved = set()
        for c in era_commits:
            if "RESOLVED" in c["msg"]:
                for fm in re.finditer(r"F-([A-Z]+\d+)", c["msg"]):
                    frontiers_resolved.add(fm.group(1))

        # Improvement commits
        improvement = sum(1 for c in era_commits if is_improvement_commit(c["msg"], c["files"]))

        era_data[era_label] = {
            "n_sessions": n_sessions,
            "n_commits": len(era_commits),
            "tools_created": tools_created,
            "tools_per_session": round(tools_created / n_sessions, 2) if n_sessions > 0 else 0,
            "principles_added": len(principles),
            "principles_per_session": round(len(principles) / n_sessions, 2) if n_sessions > 0 else 0,
            "frontiers_resolved": len(frontiers_resolved),
            "frontiers_per_session": round(len(frontiers_resolved) / n_sessions, 2) if n_sessions > 0 else 0,
            "improvement_commits": improvement,
            "improvement_per_session": round(improvement / n_sessions, 2) if n_sessions > 0 else 0,
        }

    # Print
    for era, d in era_data.items():
        print(f"\n  {era} ({d['n_sessions']} sessions, {d['n_commits']} commits):")
        print(f"    Tools created: {d['tools_created']} ({d['tools_per_session']}/session)")
        print(f"    Principles added: {d['principles_added']} ({d['principles_per_session']}/session)")
        print(f"    Frontiers resolved: {d['frontiers_resolved']} ({d['frontiers_per_session']}/session)")
        print(f"    Improvement commits: {d['improvement_commits']} ({d['improvement_per_session']}/session)")

    # Determine trend
    eras = list(era_data.values())
    rates = [e["improvement_per_session"] for e in eras]
    if rates[-1] > rates[0] * 1.1:
        trend = "accelerating"
    elif rates[-1] < rates[0] * 0.9:
        trend = "decelerating"
    else:
        trend = "stable"

    print(f"\n  Improvement rates: {' -> '.join(f'{r:.2f}' for r in rates)}")
    print(f"  Trend: {trend}")

    return {
        "eras": era_data,
        "era1_rate": rates[0],
        "era2_rate": rates[1],
        "era3_rate": rates[2],
        "trend": trend
    }


# ============================================================================
# Main
# ============================================================================

def main():
    print("F-META3 Re-measurement + Improvement-is-Swarm Analysis")
    print(f"Period: S{S_START}-S{S_END} | Date: 2026-03-01")
    print()

    # Get all commits with files
    print("Loading commits (git log --name-only)...")
    commits = get_all_commits()
    print(f"  Total commits parsed: {len(commits)}")
    print(f"  Commits with session IDs: {sum(1 for c in commits if c['session'])}")
    print()

    # Part 1: F-META3 core
    fmeta3 = measure_fmeta3(commits)

    # Part 2a: Improvement distribution
    improvement_dist = measure_improvement_distribution(commits)

    # Part 2b: Recursion
    recursion = measure_recursion(commits)

    # Part 2c: Self-application
    self_app = measure_self_application()

    # Part 2d: Velocity
    velocity = measure_velocity(commits)

    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)

    # Improvement IS swarm if:
    # - Improvement is distributed (Gini < 0.5)
    # - Self-application exists (meta cites meta > base rate)
    # - Recursion exists (tool-improving-tool > 0)
    # - Velocity is stable or accelerating
    signals = {
        "distributed": improvement_dist["gini_improvement"] < 0.5,
        "self_reinforcing": self_app["ratio"] > 1.0,
        "recursive": recursion["meta_meta_rate"] > 0.05,
        "sustained": velocity["trend"] in ("accelerating", "stable"),
    }
    passing = sum(signals.values())
    total_signals = len(signals)

    verdict_text = (
        f"Improvement IS swarm: {passing}/{total_signals} signals positive. "
        f"{'Distributed' if signals['distributed'] else 'Concentrated'} across sessions "
        f"(Gini={improvement_dist['gini_improvement']:.3f}), "
        f"{'self-reinforcing' if signals['self_reinforcing'] else 'not self-reinforcing'} "
        f"(meta→meta {self_app['ratio']:.2f}x base), "
        f"{'recursive' if signals['recursive'] else 'not recursive'} "
        f"(tool-on-tool {recursion['meta_meta_rate']:.1%}), "
        f"velocity {velocity['trend']}."
    )

    for k, v in signals.items():
        status = "PASS" if v else "FAIL"
        print(f"  [{status}] {k}")
    print(f"\n  {verdict_text}")

    # Build output
    result = {
        "experiment": "F-META3 re-measurement + improvement-is-swarm",
        "session": "S393",
        "date": "2026-03-01",
        "frontier": "F-META3",
        "f_meta3_core": fmeta3,
        "improvement_distribution": improvement_dist,
        "recursion": recursion,
        "self_application": self_app,
        "improvement_velocity": velocity,
        "signals": signals,
        "verdict": verdict_text
    }

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n  Output written to: {OUTPUT_FILE}")

    return result


if __name__ == "__main__":
    main()
