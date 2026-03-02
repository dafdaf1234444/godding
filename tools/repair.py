#!/usr/bin/env python3
"""repair.py — apply deterministic, low-risk maintenance fixes.

Usage:
    python3 tools/repair.py
    python3 tools/repair.py --dry-run
    python3 tools/repair.py --full
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = sys.executable or "python3"


@dataclass(frozen=True)
class RepairAction:
    action_id: str
    description: str
    command: tuple[str, ...]


def _command_exists(name: str) -> bool:
    return bool(shutil.which(name))


def _run_capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _run_passthrough(command: tuple[str, ...]) -> int:
    r = subprocess.run(list(command), cwd=REPO_ROOT)
    return r.returncode


def _git_clean_tree() -> bool:
    r = _run_capture(["git", "status", "--porcelain"])
    if r.returncode != 0:
        return False
    return not bool(r.stdout.strip())


def run_maintenance(quick: bool) -> str:
    command = [PYTHON_EXE, "tools/maintenance.py"]
    if quick:
        command.append("--quick")
    r = _run_capture(command)
    out = (r.stdout or "") + (r.stderr or "")
    return out


def run_validator() -> str:
    command = [PYTHON_EXE, "tools/validate_beliefs.py"]
    r = _run_capture(command)
    out = (r.stdout or "") + (r.stderr or "")
    return out


def plan_repairs(
    maintenance_output: str,
    *,
    has_bash: bool,
    clean_tree: bool,
    python_executable: str,
) -> list[RepairAction]:
    """Map maintenance output to deterministic repair actions."""
    actions: list[RepairAction] = []
    seen: set[str] = set()

    hook_signal = bool(
        re.search(r"Missing hook\(s\):|Hook drift detected", maintenance_output, re.IGNORECASE)
    )
    if hook_signal and has_bash and "install-hooks" not in seen:
        actions.append(
            RepairAction(
                action_id="install-hooks",
                description="Install/update git commit hooks",
                command=("bash", "tools/install-hooks.sh"),
            )
        )
        seen.add("install-hooks")

    proxy_signal = bool(
        re.search(
            r"save clean snapshot(?: when stable)?:\s*(?:python3|python|py -3)\s+tools/proxy_k\.py\s+--save",
            maintenance_output,
            re.IGNORECASE,
        )
    )
    if proxy_signal and clean_tree and "proxy-k-save" not in seen:
        actions.append(
            RepairAction(
                action_id="proxy-k-save",
                description="Save clean proxy-K snapshot",
                command=(python_executable, "tools/proxy_k.py", "--save"),
            )
        )
        seen.add("proxy-k-save")

    identity_signal = bool(
        re.search(r"FAIL IDENTITY:|CORE\.md changed without renewal", maintenance_output, re.IGNORECASE)
    )
    if identity_signal and clean_tree and "renew-identity" not in seen:
        actions.append(
            RepairAction(
                action_id="renew-identity",
                description="Refresh CORE.md identity hash in memory/INDEX.md",
                command=(python_executable, "tools/renew_identity.py"),
            )
        )
        seen.add("renew-identity")

    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply deterministic swarm maintenance repairs.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned repairs without executing them.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Read full maintenance output (default uses --quick).",
    )
    args = parser.parse_args()

    quick = not args.full
    print(f"=== SWARM REPAIR ({'quick' if quick else 'full'}) ===")
    baseline = run_maintenance(quick=quick)
    print(baseline.strip() or "(no maintenance output)")
    print()

    plan_input = baseline
    if "validate_beliefs.py FAIL" in baseline:
        validator = run_validator()
        if validator.strip():
            print("Validator detail:")
            print(validator.strip())
            print()
            plan_input = f"{baseline}\n{validator}"

    actions = plan_repairs(
        plan_input,
        has_bash=_command_exists("bash"),
        clean_tree=_git_clean_tree(),
        python_executable=PYTHON_EXE,
    )
    if not actions:
        print("No deterministic repairs available for current maintenance output.")
        return 0

    print("Planned repairs:")
    for action in actions:
        print(f"  - {action.action_id}: {action.description}")
    print()

    if args.dry_run:
        print("Dry-run mode: no changes applied.")
        return 0

    failures: list[str] = []
    for action in actions:
        print(f"Applying {action.action_id}: {' '.join(action.command)}")
        rc = _run_passthrough(action.command)
        if rc != 0:
            failures.append(action.action_id)

    print()
    print("Post-repair maintenance (--quick):")
    print(run_maintenance(quick=True).strip() or "(no maintenance output)")

    if failures:
        print()
        print(f"Repair failures: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
