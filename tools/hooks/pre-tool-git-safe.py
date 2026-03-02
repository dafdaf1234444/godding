#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block 'git add -A' and 'git add .' in this repo.

WSL mass-deletion bug: 'git add -A' on a WSL-corrupted tree stages mass deletions
(729 files deleted in one incident, L-179 / MEMORY.md). This hook blocks those patterns
at execution time and prints the safe alternative.
"""
import json
import sys
import re


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only intercept Bash tool
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")

    # Block 'git add -A', 'git add .', 'git add --all' only when they appear as
    # an ACTUAL command (line/fragment start), not inside commit messages or heredocs.
    # Strategy: split into command fragments by newlines + shell separators,
    # then check if any fragment STARTS with the forbidden pattern.
    def is_unsafe_git_add(cmd: str) -> bool:
        # Split into fragments by newlines and shell operators (; && ||)
        fragments = []
        for line in cmd.split('\n'):
            for part in re.split(r'(?:;|&&|\|\|)', line):
                fragments.append(part.strip())
        for frag in fragments:
            if re.match(r'^git\s+add\s+(-A|--all|\.(?:\s|$))', frag):
                return True
        return False

    if is_unsafe_git_add(command):
        print(
            "BLOCKED: 'git add -A / git add .' is forbidden in this repo (WSL mass-deletion risk).\n"
            "Safe alternative: git add <specific named files>\n"
            "See: MEMORY.md 'WSL filesystem corruption' section and L-179.",
            file=sys.stderr,
        )
        # exit 2 = block the tool call and show error to LLM
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
