#!/usr/bin/env python3
"""Claude Code Stop hook: session health check before ending."""
import json
import os
import subprocess
import sys

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    # Prevent infinite loop if stop hook already active
    if data.get("stop_hook_active"):
        sys.exit(0)

    cwd = data.get("cwd", os.getcwd())
    issues = []

    # 1. Run validator (quick mode — skip swarmability/entropy)
    validator = os.path.join(cwd, "tools", "validate_beliefs.py")
    if os.path.exists(validator):
        try:
            result = subprocess.run(
                ["python3", validator, "--quick"],
                capture_output=True, text=True, cwd=cwd, timeout=30
            )
            if "RESULT: FAIL" in result.stdout:
                issues.append("Validator FAILED — fix beliefs before ending session")
        except subprocess.TimeoutExpired:
            issues.append("Validator timed out — run manually: python3 tools/validate_beliefs.py")

    # 2. Check how far ahead of origin
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "origin/master..HEAD"],
            capture_output=True, text=True, cwd=cwd, timeout=30
        )
        ahead = int(result.stdout.strip()) if result.returncode == 0 else 0
        if ahead > 0:
            issues.append(f"Repo is {ahead} commit(s) ahead of origin — consider pushing")
    except (ValueError, subprocess.TimeoutExpired):
        pass

    # 3. Check NEXT.md freshness (was it modified in the last commit?)
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1..HEAD"],
            capture_output=True, text=True, cwd=cwd, timeout=30
        )
        if result.returncode == 0 and "tasks/NEXT.md" not in result.stdout:
            issues.append("NEXT.md not updated in last commit — update handoff before ending")
    except subprocess.TimeoutExpired:
        pass

    if issues:
        print("=== SWARM SESSION CHECK ===")
        for issue in issues:
            print(f"  - {issue}")
        # Don't block — just warn
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
