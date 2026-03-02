#!/usr/bin/env python3
"""
self_evolve.py — Self-directed evolution planner.

Usage:
    python3 tools/self_evolve.py plan [--n N]
    python3 tools/self_evolve.py harvest-all
    python3 tools/self_evolve.py status

Reads FRONTIER.md and identifies questions that can be investigated by
child swarms. Generates batch evolution plans ready for parallel execution.
After agent completion, harvest-all collects and integrates all results.

This is the "self-developing system" — the swarm identifies its own
knowledge gaps and spawns children to fill them.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHILDREN_DIR = REPO_ROOT / "experiments" / "children"
PLAN_FILE = REPO_ROOT / "experiments" / "evolution-plan.json"


def classify_question(question: str) -> str:
    """Classify a frontier question as child-suitable or not."""
    q_lower = question.lower()

    # Questions that need human input
    if any(w in q_lower for w in ["human input", "needs human", "real-world"]):
        return "needs_human"

    # Questions that are already resolved
    if any(w in q_lower for w in ["done", "yes —", "tested —", "moot"]):
        return "resolved"

    # NK analysis questions — great for children
    if any(w in q_lower for w in ["k/n", "nk", "coupling", "decompos"]):
        return "nk_analysis"

    # Theoretical questions — need research
    if any(w in q_lower for w in ["should", "is there", "can", "does"]):
        return "research"

    return "general"


def plan_evolution(max_children: int = 3):
    """Read frontier and plan child swarm tasks."""
    frontier = REPO_ROOT / "tasks" / "FRONTIER.md"
    if not frontier.exists():
        print("No FRONTIER.md found.")
        return

    text = frontier.read_text()
    questions = []

    for m in re.finditer(r"^\- \*\*F(\d+)\*\*:\s*(.+)$", text, re.MULTILINE):
        fid = int(m.group(1))
        question = m.group(2).strip()
        qtype = classify_question(question)
        questions.append({
            "id": f"F{fid}",
            "question": question,
            "type": qtype,
        })

    # Filter to child-suitable questions
    suitable = [
        q for q in questions
        if q["type"] in ("nk_analysis", "research", "general")
    ]

    print(f"=== SELF-EVOLVE PLAN ===\n")
    print(f"Total frontier questions: {len(questions)}")
    print(f"Suitable for children: {len(suitable)}")
    print(f"Max children this batch: {max_children}\n")

    # Select top N questions
    selected = suitable[:max_children]

    if not selected:
        print("No suitable questions found for child swarm investigation.")
        return

    print("Selected for investigation:")
    plan = {"children": [], "status": "planned"}

    for i, q in enumerate(selected, 1):
        # Generate child name and task
        child_name = f"evolve-{q['id'].lower()}"
        task = _generate_task(q)

        plan["children"].append({
            "name": child_name,
            "frontier_id": q["id"],
            "question": q["question"],
            "task": task,
            "status": "planned",
        })

        print(f"\n  {i}. [{q['id']}] {q['question'][:80]}")
        print(f"     Child: {child_name}")
        print(f"     Type: {q['type']}")
        print(f"     Task: {task[:100]}...")

    # Save plan
    PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    PLAN_FILE.write_text(json.dumps(plan, indent=2))
    print(f"\nPlan saved to: {PLAN_FILE}")
    print(f"\nTo execute:")
    print(f"  1. python3 tools/evolve.py init <child-name> \"<task>\"")
    print(f"     (for each child above)")
    print(f"  2. Launch sub-agents in parallel using Task tool")
    print(f"  3. python3 tools/self_evolve.py harvest-all")


def _generate_task(question: dict) -> str:
    """Generate a child swarm task from a frontier question."""
    q = question["question"]
    qtype = question["type"]

    if qtype == "nk_analysis":
        return (
            f"Investigate: {q}\n"
            f"Apply NK landscape analysis. Count N components, map K dependencies, "
            f"calculate K/N. Write your findings as a workspace analysis document. "
            f"Compare with known benchmarks: json (K/N=0.16), http.client (K/N=0.215 core), "
            f"email (K/N=0.06)."
        )
    elif qtype == "research":
        return (
            f"Research: {q}\n"
            f"Investigate this question through analysis, web search if needed, "
            f"and reasoning. Write your findings as a workspace document. "
            f"Conclude with a clear answer or a refined version of the question."
        )
    else:
        return (
            f"Investigate: {q}\n"
            f"Explore this question and document your findings."
        )


def harvest_all():
    """Harvest all children from the current evolution plan."""
    if not PLAN_FILE.exists():
        print("No evolution plan. Run 'plan' first.")
        return

    plan = json.loads(PLAN_FILE.read_text())

    print("=== HARVEST ALL ===\n")
    evolve = REPO_ROOT / "tools" / "evolve.py"

    for child in plan["children"]:
        child_name = child["name"]
        child_dir = CHILDREN_DIR / child_name

        if not child_dir.exists():
            print(f"  {child_name}: NOT SPAWNED (skipping)")
            child["status"] = "not_spawned"
            continue

        # Check if child has any sessions
        lesson_count = len(list((child_dir / "memory" / "lessons").glob("L-*.md"))) if (child_dir / "memory" / "lessons").exists() else 0

        if lesson_count == 0:
            print(f"  {child_name}: NO SESSIONS RUN (skipping)")
            child["status"] = "no_sessions"
            continue

        # Harvest
        print(f"  {child_name}: Harvesting...")
        r = subprocess.run(
            ["python3", str(evolve), "harvest", child_name],
            capture_output=True, text=True
        )

        # Check for novel rules
        novel = 0
        nm = re.search(r"Novel rules: (\d+)/", r.stdout)
        if nm:
            novel = int(nm.group(1))

        child["status"] = "harvested"
        child["novel_rules"] = novel

        print(f"    Novel rules: {novel}")

        # Check if already integrated
        log_path = REPO_ROOT / "experiments" / "integration-log" / f"{child_name}.json"
        if log_path.exists():
            print(f"    Already integrated (skipping)")
            child["status"] = "integrated"
        elif novel > 0:
            r = subprocess.run(
                ["python3", str(evolve), "integrate", child_name],
                capture_output=True, text=True
            )
            child["status"] = "integrated"
            print(f"    Integrated {novel} rule(s)")

    # Save updated plan
    plan["status"] = "harvested"
    PLAN_FILE.write_text(json.dumps(plan, indent=2))
    print(f"\nPlan updated: {PLAN_FILE}")

    # Summary
    harvested = sum(1 for c in plan["children"] if c.get("status") in ("harvested", "integrated"))
    total_novel = sum(c.get("novel_rules", 0) for c in plan["children"])
    print(f"\nSummary: {harvested} harvested, {total_novel} novel rule(s) found")


def show_status():
    """Show current evolution plan status."""
    if not PLAN_FILE.exists():
        print("No evolution plan. Run 'plan' first.")
        return

    plan = json.loads(PLAN_FILE.read_text())
    print(f"=== EVOLUTION PLAN STATUS ===\n")
    print(f"Status: {plan.get('status', 'unknown')}\n")

    for child in plan["children"]:
        status = child.get("status", "?")
        novel = child.get("novel_rules", "?")
        print(f"  {child['name']:<25} [{status}] (novel: {novel})")
        print(f"    {child['frontier_id']}: {child['question'][:70]}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "plan":
        n = 3
        if "--n" in sys.argv:
            idx = sys.argv.index("--n")
            if idx + 1 < len(sys.argv):
                n = int(sys.argv[idx + 1])
        plan_evolution(n)

    elif cmd == "harvest-all":
        harvest_all()

    elif cmd == "status":
        show_status()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
