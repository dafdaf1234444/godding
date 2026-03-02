#!/usr/bin/env python3
"""
agent_swarm.py — Create a task file for a sub-agent to run in a child swarm.

Usage:
    python3 tools/agent_swarm.py create <child-name> <task-description>
    python3 tools/agent_swarm.py prompt <child-name>

Creates a child swarm (if not exists) and generates a prompt that
can be given to a Claude Code sub-agent (Task tool) to run a session
in that child swarm. This bridges "agents" with "swarms" — each
sub-agent gets its own knowledge environment.

Workflow:
1. `agent_swarm.py create my-child "research topic X"` → spawns child + writes task
2. Copy the prompt from `agent_swarm.py prompt my-child` → paste into Task tool
3. After agent finishes → `merge_back.py experiments/children/my-child`
4. Review and integrate novel findings

This is the "agents can utilize swarms" pattern the human described.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHILDREN_DIR = REPO_ROOT / "experiments" / "children"


def create_agent_swarm(child_name: str, task_description: str, personality: str = None):
    """Create a child swarm with a specific task for a sub-agent."""
    import subprocess

    child_dir = CHILDREN_DIR / child_name

    # Spawn if not exists
    if not child_dir.exists():
        genesis = Path("workspace/genesis.sh")
        try:
            child_target = child_dir.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            child_target = child_dir.as_posix()
        r = subprocess.run(
            ["bash", genesis.as_posix(), child_target, child_name],
            cwd=str(REPO_ROOT), capture_output=True, text=True
        )
        if r.returncode != 0:
            print(f"Genesis failed: {r.stderr}")
            sys.exit(1)

        # Apply personality overlay if specified
        if personality:
            _apply_personality(child_dir, child_name, personality)

        # Init git
        subprocess.run(["git", "init"], cwd=str(child_dir), capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=str(child_dir), capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"[S] init: genesis{f' ({personality})' if personality else ''}"],
            cwd=str(child_dir), capture_output=True
        )
        print(f"Child swarm '{child_name}' created at {child_dir}")
        if personality:
            print(f"  Personality: {personality} (personality.md written)")
    else:
        print(f"Child swarm '{child_name}' already exists at {child_dir}")

    # Write task file
    task_file = child_dir / "tasks" / "AGENT-TASK.md"
    task_file.write_text(
        f"# Agent Task\n\n"
        f"## Description\n{task_description}\n\n"
        f"## Instructions\n"
        f"1. Follow CLAUDE.md protocol (read CORE.md, INDEX.md first)\n"
        f"2. Complete the task described above\n"
        f"3. Write a lesson about what you learned\n"
        f"4. Update INDEX.md and FRONTIER.md\n"
        f"5. Commit with format: [S] what: why\n"
    )

    # Commit the task
    subprocess.run(
        ["git", "add", "tasks/AGENT-TASK.md"],
        cwd=str(child_dir), capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", f"[S] task: {task_description[:50]}"],
        cwd=str(child_dir), capture_output=True
    )

    # Record spawn metadata in .swarm_meta.json
    from datetime import date as _date
    meta_path = child_dir / ".swarm_meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
        except Exception:
            pass
    meta["task"] = task_description
    meta["spawned"] = str(_date.today())
    meta_path.write_text(json.dumps(meta, indent=2))
    subprocess.run(["git", "add", ".swarm_meta.json"], cwd=str(child_dir), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "[S] meta: record spawn task + date"],
        cwd=str(child_dir), capture_output=True
    )

    print(f"Task file written: {task_file}")
    print(f"\nTo run: python3 tools/agent_swarm.py prompt {child_name}")


def _apply_personality(child_dir: Path, child_name: str, personality: str):
    """Write personality.md overlay and update .swarm_meta.json."""
    personalities_dir = REPO_ROOT / "tools" / "personalities"
    template_path = personalities_dir / f"{personality}.md"
    if not template_path.exists():
        available = [p.stem for p in personalities_dir.glob("*.md")]
        print(f"Personality '{personality}' not found. Available: {available}")
        sys.exit(1)

    # Write personality.md with colony name substituted
    content = template_path.read_text().replace("{{COLONY_NAME}}", child_name)
    (child_dir / "personality.md").write_text(content)

    # Add personality to .swarm_meta.json
    meta_path = child_dir / ".swarm_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
    else:
        meta = {}
    meta["personality"] = personality
    meta_path.write_text(json.dumps(meta, indent=2))

    # Add one line to child's CLAUDE.md session start
    claude_path = child_dir / "CLAUDE.md"
    if claude_path.exists():
        content = claude_path.read_text()
        old_line = "1. Read `beliefs/CORE.md` — purpose and principles"
        new_lines = (
            "0. Read `personality.md` — your persistent character for this colony\n"
            "1. Read `beliefs/CORE.md` — purpose and principles"
        )
        content = content.replace(old_line, new_lines)
        claude_path.write_text(content)


def generate_prompt(child_name: str) -> str:
    """Generate a prompt for a sub-agent to run in a child swarm."""
    child_dir = CHILDREN_DIR / child_name

    if not child_dir.exists():
        print(f"Child swarm '{child_name}' does not exist. Create it first.")
        sys.exit(1)

    # Read the task
    task_file = child_dir / "tasks" / "AGENT-TASK.md"
    task_content = ""
    if task_file.exists():
        task_content = task_file.read_text()

    prompt = f"""You are a session of a child swarm located at {child_dir}.

Follow the CLAUDE.md protocol in the child swarm:
1. Read {child_dir}/beliefs/CORE.md (purpose and principles)
2. Read {child_dir}/memory/INDEX.md (current state)
3. Read {child_dir}/tasks/AGENT-TASK.md (your task)
4. Run: cd {child_dir} && python3 tools/validate_beliefs.py
5. Execute the task
6. Write a lesson (max 20 lines) in {child_dir}/memory/lessons/
7. Update {child_dir}/memory/INDEX.md
8. Update {child_dir}/tasks/FRONTIER.md with new questions
9. Run the validator again
10. Commit with format: [S] what: why

IMPORTANT:
- Work INSIDE the child swarm directory: {child_dir}
- Use absolute paths when writing/editing files
- Make real git commits to the child swarm's git repo
- Do NOT modify any files outside {child_dir}

Task:
{task_content}"""

    return prompt


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "create":
        if len(sys.argv) < 4:
            print("Usage: agent_swarm.py create <child-name> <task-description> [--personality <name>]")
            sys.exit(1)
        args = sys.argv[3:]
        personality = None
        if "--personality" in args:
            idx = args.index("--personality")
            personality = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        create_agent_swarm(sys.argv[2], " ".join(args), personality=personality)

    elif cmd == "prompt":
        prompt = generate_prompt(sys.argv[2])
        print(prompt)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
