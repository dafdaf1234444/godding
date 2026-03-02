#!/usr/bin/env python3
"""
evolve.py — Automated evolution pipeline for the swarm.

Usage:
    python3 tools/evolve.py init <child-name> <task-description>
    python3 tools/evolve.py harvest <child-name>
    python3 tools/evolve.py integrate <child-name> [--dry-run]
    python3 tools/evolve.py compare <child1> <child2> [child3...]
    python3 tools/evolve.py cycle <child-name> <task-description>

Commands:
    init      — Spawn child swarm with task, output sub-agent prompt
    harvest   — Evaluate child + generate merge-back report
    integrate — Auto-integrate novel rules/questions into parent
    compare   — Compare multiple children side-by-side
    cycle     — Full pipeline summary (init → agent → harvest → integrate)

This closes the evolution loop: spawn → run → evaluate → learn.
The "self-developing system" pattern the human described.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from novelty import check_novelty, load_parent_rules

REPO_ROOT = Path(__file__).resolve().parent.parent
CHILDREN_DIR = REPO_ROOT / "experiments" / "children"


def _pick_python_cmd() -> str:
    """Pick a runnable python command for this host."""
    for candidate in ("python3", "python", sys.executable):
        try:
            probe = subprocess.run(
                [candidate, "-c", "import sys"],
                capture_output=True, text=True
            )
            if probe.returncode == 0:
                return candidate
        except Exception:
            continue
    try:
        probe = subprocess.run(
            ["py", "-3", "-c", "import sys; print(sys.executable)"],
            capture_output=True, text=True
        )
        if probe.returncode == 0:
            exe = probe.stdout.strip().splitlines()[-1].strip()
            if exe:
                return exe
    except Exception:
        pass
    return sys.executable


PYTHON_CMD = _pick_python_cmd()


def _configure_console_errors():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except Exception:
                pass


_configure_console_errors()


def get_next_principle_id() -> int:
    """Find the next available P-NNN id."""
    principles = REPO_ROOT / "memory" / "PRINCIPLES.md"
    if not principles.exists():
        return 1
    text = principles.read_text()
    ids = [int(m.group(1)) for m in re.finditer(r"\*\*P-(\d+)\*\*", text)]
    return max(ids) + 1 if ids else 1


def get_next_lesson_id() -> int:
    """Find the next available L-NNN id."""
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    if not lessons_dir.exists():
        return 1
    ids = []
    for f in lessons_dir.glob("L-*.md"):
        m = re.match(r"L-(\d+)", f.stem)
        if m:
            ids.append(int(m.group(1)))
    return max(ids) + 1 if ids else 1


def get_next_frontier_id() -> int:
    """Find the next available F-NN id."""
    frontier = REPO_ROOT / "tasks" / "FRONTIER.md"
    if not frontier.exists():
        return 1
    text = frontier.read_text()
    ids = [int(m.group(1)) for m in re.finditer(r"F(\d+)", text)]
    return max(ids) + 1 if ids else 1


def init_child(child_name: str, task_description: str, personality: str = None):
    """Spawn child swarm with task, output sub-agent prompt."""
    # Use agent_swarm.py to create
    agent_swarm = REPO_ROOT / "tools" / "agent_swarm.py"
    cmd = [PYTHON_CMD, str(agent_swarm), "create", child_name, task_description]
    if personality:
        cmd += ["--personality", personality]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Failed to create child: {r.stderr}")
        sys.exit(1)
    print(r.stdout)

    # Sync bulletins from siblings
    bulletin_py = REPO_ROOT / "tools" / "bulletin.py"
    if bulletin_py.exists():
        subprocess.run(
            [PYTHON_CMD, str(bulletin_py), "sync", child_name],
            capture_output=True, text=True
        )

    # Generate context route for the task
    context_router = REPO_ROOT / "tools" / "context_router.py"
    if context_router.exists():
        r = subprocess.run(
            [PYTHON_CMD, str(context_router), task_description],
            capture_output=True, text=True
        )
        print("\n" + "=" * 60)
        print("CONTEXT ROUTE (files this spawn needs):")
        print("=" * 60)
        print(r.stdout)

    # Generate prompt
    r = subprocess.run(
        [PYTHON_CMD, str(agent_swarm), "prompt", child_name],
        capture_output=True, text=True
    )
    print("\n" + "=" * 60)
    print("SUB-AGENT PROMPT (copy into Task tool):")
    print("=" * 60)
    print(r.stdout)
    print("=" * 60)

    child_dir = CHILDREN_DIR / child_name
    print(f"\nChild ready at: {child_dir}")
    print(f"Next steps:")
    print(f"  1. Launch sub-agent with the prompt above")
    print(f"  2. After completion: python3 tools/evolve.py harvest {child_name}")
    print(f"  3. Review: python3 tools/evolve.py integrate {child_name} --dry-run")
    print(f"  4. Apply: python3 tools/evolve.py integrate {child_name}")


def harvest_child(child_name: str) -> dict:
    """Evaluate child + generate merge-back report."""
    child_dir = CHILDREN_DIR / child_name
    if not child_dir.exists():
        print(f"Child '{child_name}' does not exist at {child_dir}")
        sys.exit(1)

    # Evaluate viability
    swarm_test = REPO_ROOT / "tools" / "swarm_test.py"
    r = subprocess.run(
        [PYTHON_CMD, str(swarm_test), "evaluate", str(child_dir)],
        capture_output=True, text=True
    )
    print("=== VIABILITY ===")
    print(r.stdout)

    # Merge-back report
    merge_back = REPO_ROOT / "tools" / "merge_back.py"
    r = subprocess.run(
        [PYTHON_CMD, str(merge_back), str(child_dir)],
        capture_output=True, text=True
    )
    print("\n=== MERGE-BACK ===")
    print(r.stdout)

    # Parse results for return
    report_path = REPO_ROOT / "experiments" / "merge-reports" / f"{child_name}.md"
    report = report_path.read_text() if report_path.exists() else ""

    novel_count = 0
    m = re.search(r"Novel rules: (\d+)/", report)
    if m:
        novel_count = int(m.group(1))

    viability = "unknown"
    vm = re.search(r"Viability: (\d+/4)", r.stdout)
    if vm:
        viability = vm.group(1)

    # Auto-generate bulletins from novel findings
    if novel_count > 0:
        _write_harvest_bulletins(child_name, report)

    return {
        "child_name": child_name,
        "viability": viability,
        "novel_rules": novel_count,
        "report": report,
    }


def _write_harvest_bulletins(child_name: str, report: str):
    """Auto-generate bulletins from a child's merge-back report."""
    bulletin_py = REPO_ROOT / "tools" / "bulletin.py"
    if not bulletin_py.exists():
        return

    # Extract novel rules from report
    for m in re.finditer(r"\[NOVEL\]\s*\n\s*Rule:\s*(.+)", report):
        rule_text = m.group(1).strip()
        subprocess.run(
            [PYTHON_CMD, str(bulletin_py), "write", child_name,
             "discovery", rule_text],
            capture_output=True, text=True
        )

    print(f"  Bulletins auto-generated for {child_name}")


def integrate_child(child_name: str, dry_run: bool = False):
    """Auto-integrate novel rules/questions into parent."""
    child_dir = CHILDREN_DIR / child_name
    if not child_dir.exists():
        print(f"Child '{child_name}' does not exist")
        sys.exit(1)

    # Load merge-back report
    report_path = REPO_ROOT / "experiments" / "merge-reports" / f"{child_name}.md"
    if not report_path.exists():
        print(f"No merge-back report. Run 'harvest' first.")
        sys.exit(1)

    report = report_path.read_text()

    # Extract novel rules from child lessons
    child_lessons_dir = child_dir / "memory" / "lessons"
    parent_principles = REPO_ROOT / "memory" / "PRINCIPLES.md"
    parent_principles_text = parent_principles.read_text() if parent_principles.exists() else ""

    parent_rules = load_parent_rules(parent_principles)

    novel_rules = []
    if child_lessons_dir.exists():
        for f in sorted(child_lessons_dir.glob("L-*.md")):
            if f.name == "TEMPLATE.md":
                continue
            text = f.read_text()
            rule_m = re.search(
                r"## Rule extracted.*?\n(.+?)(?:\n\n|\n##|\Z)",
                text, re.DOTALL
            )
            if rule_m:
                rule = rule_m.group(1).strip()
                is_novel, sim, closest = check_novelty(rule, parent_rules)
                if is_novel:
                    novel_rules.append(rule)

    # Extract novel frontier questions
    child_frontier = child_dir / "tasks" / "FRONTIER.md"
    parent_frontier = REPO_ROOT / "tasks" / "FRONTIER.md"
    parent_frontier_text = parent_frontier.read_text() if parent_frontier.exists() else ""

    novel_questions = []
    # Common genesis questions that are child-specific, not worth importing
    skip_patterns = [
        "validate the setup",
        "does this structure work",
        "knowledge domain",
    ]
    if child_frontier.exists():
        child_text = child_frontier.read_text()
        child_qs = re.findall(r"^\- \*\*F\d+\*\*:\s*(.+)$", child_text, re.MULTILINE)
        for q in child_qs:
            q_lower = q.lower()
            # Skip common genesis boilerplate questions
            if any(pat in q_lower for pat in skip_patterns):
                continue
            # Skip if parent already has a similar question
            q_words = set(q_lower.split())
            is_novel = True
            for line in parent_frontier_text.lower().splitlines():
                if not line.strip().startswith("-") and "| f" not in line:
                    continue
                p_words = set(line.split())
                if len(q_words & p_words) > 0.5 * len(q_words):
                    is_novel = False
                    break
            if is_novel:
                novel_questions.append(q)

    # Report what we'd integrate
    print(f"=== INTEGRATION PLAN for {child_name} ===\n")

    if novel_rules:
        next_p = get_next_principle_id()
        next_l = get_next_lesson_id()
        print(f"Novel rules to add to PRINCIPLES.md ({len(novel_rules)}):")
        for i, rule in enumerate(novel_rules):
            pid = next_p + i
            print(f"  P-{pid:03d}: {rule} (from {child_name})")
    else:
        print("No novel rules to integrate.")

    if novel_questions:
        next_f = get_next_frontier_id()
        print(f"\nNovel frontier questions to add ({len(novel_questions)}):")
        for i, q in enumerate(novel_questions):
            fid = next_f + i
            print(f"  F{fid}: {q}")
    else:
        print("\nNo novel frontier questions.")

    if dry_run:
        print("\n[DRY RUN — no changes made]")
        return

    if not novel_rules and not novel_questions:
        print("\nNothing to integrate. Child confirmed existing knowledge.")
        return

    # Actually integrate
    changes_made = []

    # Add novel rules to PRINCIPLES.md
    if novel_rules:
        next_p = get_next_principle_id()
        additions = []
        for i, rule in enumerate(novel_rules):
            pid = next_p + i
            additions.append(
                f"- **P-{pid:03d}**: {rule} (from child:{child_name})"
            )

        # Append to the end of the last section in PRINCIPLES.md
        new_section = (
            f"\n## From child:{child_name}\n" +
            "\n".join(additions) + "\n"
        )
        with open(parent_principles, "a") as f:
            f.write(new_section)
        changes_made.append(f"Added {len(novel_rules)} rule(s) to PRINCIPLES.md")
        print(f"\nAdded {len(novel_rules)} rule(s) to PRINCIPLES.md")

    # Add novel questions to FRONTIER.md
    if novel_questions:
        next_f = get_next_frontier_id()
        additions = []
        for i, q in enumerate(novel_questions):
            fid = next_f + i
            additions.append(f"- **F{fid}**: {q} (from child:{child_name})")

        # Insert before ## Resolved section
        if "## Resolved" in parent_frontier_text:
            insert_point = parent_frontier_text.index("## Resolved")
            new_text = (
                parent_frontier_text[:insert_point] +
                "\n".join(additions) + "\n\n" +
                parent_frontier_text[insert_point:]
            )
        else:
            new_text = parent_frontier_text + "\n" + "\n".join(additions) + "\n"

        parent_frontier.write_text(new_text)
        changes_made.append(f"Added {len(novel_questions)} question(s) to FRONTIER.md")
        print(f"Added {len(novel_questions)} question(s) to FRONTIER.md")

    # Post-integration validation
    validator = REPO_ROOT / "tools" / "validate_beliefs.py"
    if validator.exists():
        r = subprocess.run(
            [PYTHON_CMD, str(validator)],
            cwd=str(REPO_ROOT), capture_output=True, text=True
        )
        if r.returncode == 0:
            print("\n  Post-integration validation: PASS")
        else:
            print(f"\n  WARNING: Post-integration validation FAILED!")
            print(f"  {r.stdout}")
            changes_made.append("WARNING: validator failed after integration")

    # Write integration log
    log_dir = REPO_ROOT / "experiments" / "integration-log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "child": child_name,
        "date": datetime.now().isoformat(),
        "novel_rules": len(novel_rules),
        "novel_questions": len(novel_questions),
        "changes": changes_made,
    }
    log_path = log_dir / f"{child_name}.json"
    log_path.write_text(json.dumps(log_entry, indent=2))
    print(f"\nIntegration logged to: {log_path}")


def show_cycle(child_name: str, task: str):
    """Show the full evolution cycle for reference."""
    print(f"=== EVOLUTION CYCLE: {child_name} ===\n")
    print(f"Task: {task}\n")
    print("Steps:")
    print(f"  1. INIT:      python3 tools/evolve.py init {child_name} \"{task}\"")
    print(f"  2. RUN:       Use Task tool with the generated prompt")
    print(f"  3. HARVEST:   python3 tools/evolve.py harvest {child_name}")
    print(f"  4. REVIEW:    python3 tools/evolve.py integrate {child_name} --dry-run")
    print(f"  5. INTEGRATE: python3 tools/evolve.py integrate {child_name}")
    print()
    print("Or for parallel evolution:")
    print(f"  - Spawn multiple children with different tasks")
    print(f"  - Launch sub-agents in parallel")
    print(f"  - Harvest all → compare viability → integrate best")


def compare_children(child_names: list[str]):
    """Compare multiple children side-by-side: viability, rules, questions."""
    swarm_test = REPO_ROOT / "tools" / "swarm_test.py"

    print("=== COLONY COMPARISON ===\n")
    print(f"{'Child':<25} {'Viability':<12} {'Lessons':<10} {'Beliefs':<10} {'Novel':<8}")
    print("-" * 65)

    results = []
    for name in child_names:
        child_dir = CHILDREN_DIR / name
        if not child_dir.exists():
            print(f"{name:<25} NOT FOUND")
            continue

        # Evaluate viability
        r = subprocess.run(
            [PYTHON_CMD, str(swarm_test), "evaluate", str(child_dir)],
            capture_output=True, text=True
        )
        viability = "?"
        vm = re.search(r"Viability: (\d+/4)", r.stdout)
        if vm:
            viability = vm.group(1)

        # Count lessons and beliefs
        lesson_count = len(list((child_dir / "memory" / "lessons").glob("L-*.md"))) if (child_dir / "memory" / "lessons").exists() else 0
        belief_count = 0
        deps = child_dir / "beliefs" / "DEPS.md"
        if deps.exists():
            belief_count = len(re.findall(r"^### B\d+:", deps.read_text(), re.MULTILINE))

        # Check for novel rules via merge-back
        merge_back = REPO_ROOT / "tools" / "merge_back.py"
        r = subprocess.run(
            [PYTHON_CMD, str(merge_back), str(child_dir)],
            capture_output=True, text=True
        )
        novel = 0
        nm = re.search(r"Novel rules: (\d+)/", r.stdout)
        if nm:
            novel = int(nm.group(1))

        results.append({
            "name": name,
            "viability": viability,
            "lessons": lesson_count,
            "beliefs": belief_count,
            "novel": novel,
        })
        print(f"{name:<25} {viability:<12} {lesson_count:<10} {belief_count:<10} {novel:<8}")

    if not results:
        print("\nNo children found.")
        return

    # Find best performer
    def score(r):
        vm = re.search(r"(\d+)/4", r["viability"])
        return (int(vm.group(1)) if vm else 0, r["novel"], r["lessons"])

    results.sort(key=score, reverse=True)
    winner = results[0]
    print(f"\nBest performer: {winner['name']} ({winner['viability']} viability, {winner['novel']} novel rules)")
    print(f"Recommended: python3 tools/evolve.py integrate {winner['name']} --dry-run")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        if len(sys.argv) < 4:
            print("Usage: evolve.py init <child-name> <task-description> [--personality <name>]")
            sys.exit(1)
        args = sys.argv[3:]
        personality = None
        if "--personality" in args:
            idx = args.index("--personality")
            personality = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        init_child(sys.argv[2], " ".join(args), personality=personality)

    elif cmd == "fanout":
        # evolve.py fanout <frontier-id> <task-desc> --personalities p1,p2,p3
        if len(sys.argv) < 4:
            print("Usage: evolve.py fanout <frontier-id> <task-description> [--personalities p1,p2,p3]")
            sys.exit(1)
        frontier_id = sys.argv[2]
        args = sys.argv[3:]
        personalities = ["skeptic", "builder", "explorer", "adversary"]
        if "--personalities" in args:
            idx = args.index("--personalities")
            personalities = args[idx + 1].split(",")
            args = args[:idx] + args[idx + 2:]
        task_desc = " ".join(args)
        print(f"Fanning out {len(personalities)} personalities on {frontier_id}: {personalities}")
        for p in personalities:
            child_name = f"{frontier_id}-{p}"
            print(f"\n--- Spawning {child_name} ---")
            init_child(child_name, task_desc, personality=p)

    elif cmd == "harvest":
        if len(sys.argv) < 3:
            print("Usage: evolve.py harvest <child-name>")
            sys.exit(1)
        harvest_child(sys.argv[2])

    elif cmd == "integrate":
        if len(sys.argv) < 3:
            print("Usage: evolve.py integrate <child-name> [--dry-run]")
            sys.exit(1)
        dry_run = "--dry-run" in sys.argv
        integrate_child(sys.argv[2], dry_run)

    elif cmd == "compare":
        if len(sys.argv) < 4:
            print("Usage: evolve.py compare <child1> <child2> [child3...]")
            sys.exit(1)
        compare_children(sys.argv[2:])

    elif cmd == "cycle":
        if len(sys.argv) < 4:
            print("Usage: evolve.py cycle <child-name> <task-description>")
            sys.exit(1)
        show_cycle(sys.argv[2], " ".join(sys.argv[3:]))

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
