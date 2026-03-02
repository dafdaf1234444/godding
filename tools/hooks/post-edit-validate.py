#!/usr/bin/env python3
"""Claude Code PostToolUse hook: validate beliefs after editing beliefs/ files."""
import json
import subprocess
import sys
import os

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only validate when beliefs/ files are edited
    if "/beliefs/" not in file_path:
        sys.exit(0)

    cwd = data.get("cwd", os.getcwd())
    validator = os.path.join(cwd, "tools", "validate_beliefs.py")

    if not os.path.exists(validator):
        sys.exit(0)

    result = subprocess.run(
        ["python3", validator, "--quick"],
        capture_output=True, text=True, cwd=cwd, timeout=30
    )

    # Check for errors (not warnings)
    if "RESULT: FAIL" in result.stdout:
        print(f"BELIEF VALIDATION FAILED after editing {os.path.basename(file_path)}", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        sys.exit(2)

    # Show warning count if any
    if "0 errors" in result.stdout and "warnings" in result.stdout:
        for line in result.stdout.splitlines():
            if "Summary:" in line:
                print(line)
                break

    sys.exit(0)

if __name__ == "__main__":
    main()
