#!/usr/bin/env python3
"""
swarm_test.py — Spawn and evaluate child swarms as integration tests.

Usage:
    python3 tools/swarm_test.py spawn <name> [topic] [--personality <name>]
    python3 tools/swarm_test.py evaluate <swarm-dir>
    python3 tools/swarm_test.py list

Spawns a child swarm via genesis.sh, then evaluates its health after
sessions have been run. Used to test whether the swarm architecture
produces viable offspring (anti-fragility at the colony level).
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

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


def _apply_personality_overlay(child_dir: Path, child_name: str, personality: str) -> None:
    """Write personality.md and wire CLAUDE.md to load it."""
    personalities_dir = REPO_ROOT / "tools" / "personalities"
    template_path = personalities_dir / f"{personality}.md"
    if not template_path.exists():
        available = [p.stem for p in personalities_dir.glob("*.md")]
        print(f"Personality '{personality}' not found. Available: {available}")
        sys.exit(1)

    content = template_path.read_text().replace("{{COLONY_NAME}}", child_name)
    (child_dir / "personality.md").write_text(content)

    claude_path = child_dir / "CLAUDE.md"
    if claude_path.exists():
        claude = claude_path.read_text()
        if "Read `personality.md`" not in claude:
            old_line = "1. Read `beliefs/CORE.md` — purpose and principles"
            new_lines = (
                "0. Read `personality.md` — your persistent character for this colony\n"
                "1. Read `beliefs/CORE.md` — purpose and principles"
            )
            if old_line in claude:
                claude_path.write_text(claude.replace(old_line, new_lines))


def spawn(name: str, topic: str = "general", personality: str = None) -> Path:
    """Spawn a child swarm and return its path."""
    child_dir = CHILDREN_DIR / name
    if child_dir.exists():
        print(f"Error: {child_dir} already exists")
        sys.exit(1)

    genesis = Path("workspace/genesis.sh")
    try:
        child_target = child_dir.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        child_target = child_dir.as_posix()
    result = subprocess.run(
        ["bash", genesis.as_posix(), child_target, topic],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Genesis failed: {result.stderr}")
        sys.exit(1)

    # Initialize git
    subprocess.run(["git", "init"], cwd=str(child_dir), capture_output=True)
    subprocess.run(
        ["git", "add", "-A"], cwd=str(child_dir), capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "[S] init: genesis"],
        cwd=str(child_dir), capture_output=True
    )

    print(f"Child swarm '{name}' spawned at {child_dir}")
    print(f"Topic: {topic}")
    if personality:
        print(f"Personality: {personality}")

    if personality:
        _apply_personality_overlay(child_dir, name, personality)

    # Write spawn metadata
    meta = {
        "name": name,
        "topic": topic,
        "parent": str(REPO_ROOT),
        "spawned_from_lesson_count": _count_parent_lessons(),
        "spawned_from_belief_count": _count_parent_beliefs(),
        "genesis_version": _get_genesis_version(),
    }
    if personality:
        meta["personality"] = personality
    meta_path = child_dir / ".swarm_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    if personality:
        subprocess.run(
            ["git", "add", "personality.md", "CLAUDE.md"],
            cwd=str(child_dir), capture_output=True
        )
    subprocess.run(
        ["git", "add", ".swarm_meta.json"],
        cwd=str(child_dir), capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "[S] meta: spawn metadata from parent"],
        cwd=str(child_dir), capture_output=True
    )

    return child_dir


def evaluate(swarm_dir: Path) -> dict:
    """Evaluate a child swarm's health and evolution."""
    swarm_dir = Path(swarm_dir).resolve()
    if not swarm_dir.exists():
        print(f"Error: {swarm_dir} does not exist")
        sys.exit(1)

    results = {
        "path": str(swarm_dir),
        "validator_pass": False,
        "belief_count": 0,
        "observed_count": 0,
        "theorized_count": 0,
        "lesson_count": 0,
        "frontier_open": 0,
        "frontier_resolved": 0,
        "commit_count": 0,
        "files_count": 0,
    }

    # Run validator
    validator = swarm_dir / "tools" / "validate_beliefs.py"
    if validator.exists():
        r = subprocess.run(
            [PYTHON_CMD, str(validator)],
            cwd=str(swarm_dir), capture_output=True, text=True
        )
        results["validator_pass"] = r.returncode == 0
        results["validator_output"] = r.stdout

        # Parse belief counts from output
        summary_m = re.search(
            r"(\d+) beliefs, (\d+) observed, (\d+) theorized",
            r.stdout
        )
        if summary_m:
            results["belief_count"] = int(summary_m.group(1))
            results["observed_count"] = int(summary_m.group(2))
            results["theorized_count"] = int(summary_m.group(3))

    # Count lessons
    lessons_dir = swarm_dir / "memory" / "lessons"
    if lessons_dir.exists():
        results["lesson_count"] = len(list(lessons_dir.glob("L-*.md")))

    # Count frontier questions
    frontier = swarm_dir / "tasks" / "FRONTIER.md"
    if frontier.exists():
        text = frontier.read_text()
        results["frontier_open"] = len(
            re.findall(r"^\- \*\*F\d+\*\*:", text, re.MULTILINE)
        )
        results["frontier_resolved"] = len(
            re.findall(r"^\| F\d+", text, re.MULTILINE)
        )

    # Count commits
    r = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=str(swarm_dir), capture_output=True, text=True
    )
    if r.returncode == 0:
        results["commit_count"] = len(r.stdout.strip().splitlines())

    # Count tracked files
    r = subprocess.run(
        ["git", "ls-files"],
        cwd=str(swarm_dir), capture_output=True, text=True
    )
    if r.returncode == 0:
        results["files_count"] = len(r.stdout.strip().splitlines())

    # Read spawn metadata
    meta_path = swarm_dir / ".swarm_meta.json"
    if meta_path.exists():
        results["meta"] = json.loads(meta_path.read_text())

    return results


def list_children():
    """List all child swarms and their status."""
    if not CHILDREN_DIR.exists():
        print("No children directory. Spawn a child first.")
        return

    children = [d for d in CHILDREN_DIR.iterdir() if d.is_dir()]
    if not children:
        print("No child swarms found.")
        return

    print(f"{'Name':<20} {'Beliefs':<10} {'Lessons':<10} {'Commits':<10} {'Validator':<10}")
    print("-" * 60)
    for child in sorted(children):
        results = evaluate(child)
        status = "PASS" if results["validator_pass"] else "FAIL"
        print(
            f"{child.name:<20} {results['belief_count']:<10} "
            f"{results['lesson_count']:<10} {results['commit_count']:<10} "
            f"{status:<10}"
        )


def print_evaluation(results: dict):
    """Print a detailed evaluation report."""
    print(f"\n=== CHILD SWARM EVALUATION ===")
    print(f"Path: {results['path']}")
    if "meta" in results:
        print(f"Topic: {results['meta'].get('topic', 'unknown')}")
        print(f"Parent lessons at spawn: {results['meta'].get('spawned_from_lesson_count', '?')}")
    print(f"\nValidator: {'PASS' if results['validator_pass'] else 'FAIL'}")
    print(f"Beliefs: {results['belief_count']} ({results['observed_count']} observed, {results['theorized_count']} theorized)")
    print(f"Lessons: {results['lesson_count']}")
    print(f"Frontier: {results['frontier_open']} open, {results['frontier_resolved']} resolved")
    print(f"Commits: {results['commit_count']}")
    print(f"Files: {results['files_count']}")

    # Health assessment
    print(f"\n--- Health Assessment ---")
    score = 0
    if results["validator_pass"]:
        score += 1
        print("  [+] Validator passes")
    else:
        print("  [-] Validator fails")

    if results["lesson_count"] > 0:
        score += 1
        print(f"  [+] Has {results['lesson_count']} lesson(s)")
    else:
        print("  [-] No lessons written")

    if results["observed_count"] > 0:
        score += 1
        print(f"  [+] Has {results['observed_count']} observed belief(s)")
    else:
        print("  [-] No beliefs upgraded to observed")

    if results["frontier_resolved"] > 0:
        score += 1
        print(f"  [+] Resolved {results['frontier_resolved']} frontier question(s)")
    else:
        print("  [-] No frontier questions resolved")

    print(f"\nViability: {score}/4 ({'viable' if score >= 3 else 'developing' if score >= 1 else 'inert'})")


def _count_parent_lessons() -> int:
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    return len(list(lessons_dir.glob("L-*.md"))) if lessons_dir.exists() else 0


def _get_genesis_version() -> str:
    """Extract genesis version from genesis.sh header comment."""
    genesis = REPO_ROOT / "workspace" / "genesis.sh"
    if genesis.exists():
        text = genesis.read_text()
        m = re.search(r"genesis\.sh (v\d+)", text)
        if m:
            return m.group(1)
    return "unknown"


def _count_parent_beliefs() -> int:
    deps = REPO_ROOT / "beliefs" / "DEPS.md"
    if deps.exists():
        return len(re.findall(r"^### B\d+:", deps.read_text(), re.MULTILINE))
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "spawn":
        if len(sys.argv) < 3:
            print("Usage: swarm_test.py spawn <name> [topic] [--personality <name>]")
            sys.exit(1)
        name = sys.argv[2]
        args = sys.argv[3:]
        personality = None
        if "--personality" in args:
            idx = args.index("--personality")
            if idx + 1 >= len(args):
                print("Error: --personality requires a value")
                sys.exit(1)
            personality = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        topic = args[0] if args else "general"
        spawn(name, topic, personality)

    elif cmd == "evaluate":
        if len(sys.argv) < 3:
            print("Usage: swarm_test.py evaluate <swarm-dir>")
            sys.exit(1)
        results = evaluate(Path(sys.argv[2]))
        print_evaluation(results)

    elif cmd == "list":
        list_children()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
