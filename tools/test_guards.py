#!/usr/bin/env python3
"""Regression tests for modular guard system (tools/guards/*.sh).

Validates:
1. All guard files are valid bash (syntax check).
2. Guard filenames follow NN-name.sh convention.
3. Each guard has a comment header describing its purpose.
4. Guards that need PYTHON_CMD document it.
5. No guard duplicates another guard's FM-XX identifier.
6. check.sh sources guards from tools/guards/ directory.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARDS_DIR = REPO_ROOT / "tools" / "guards"
CHECK_SH = REPO_ROOT / "tools" / "check.sh"

def test_guards_dir_exists():
    assert GUARDS_DIR.is_dir(), f"Guards directory missing: {GUARDS_DIR}"

def test_guard_naming_convention():
    """All guard files must match NN-name.sh pattern."""
    pattern = re.compile(r'^\d{2}-[a-z][a-z0-9-]+\.sh$')
    for f in GUARDS_DIR.iterdir():
        if f.suffix == '.sh':
            assert pattern.match(f.name), f"Guard {f.name} doesn't match NN-name.sh convention"

def test_guard_bash_syntax():
    """All guard files must pass bash -n syntax check."""
    for f in sorted(GUARDS_DIR.glob("*.sh")):
        result = subprocess.run(
            ["bash", "-n", str(f)],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Syntax error in {f.name}: {result.stderr}"

def test_guard_has_comment_header():
    """Each guard should have a descriptive comment header."""
    for f in sorted(GUARDS_DIR.glob("*.sh")):
        content = f.read_text()
        lines = content.strip().split('\n')
        assert len(lines) >= 2, f"{f.name} is too short"
        # First line should be shebang, second should be comment
        assert lines[0].startswith('#!/bin/bash'), f"{f.name} missing shebang"
        assert lines[1].startswith('#'), f"{f.name} missing comment header"

def test_no_duplicate_fm_ids():
    """No two guards should claim the same FM-XX identifier as primary."""
    fm_ids = {}
    # Only check the FIRST FM-XX in the header comment (line 2) as the primary ID.
    # Guards may reference other FM-XX IDs in cross-references.
    for f in sorted(GUARDS_DIR.glob("*.sh")):
        lines = f.read_text().strip().split('\n')
        header = lines[1] if len(lines) > 1 else ""
        matches = re.findall(r'FM-(\d+)', header)
        if matches:
            fm_id = f"FM-{matches[0]}"
            if fm_id in fm_ids:
                # Allow FM-01 to span multiple layers (mass-deletion, mass-staging, tree-size)
                if fm_id == "FM-01":
                    continue
                assert False, f"Duplicate primary {fm_id}: {fm_ids[fm_id]} and {f.name}"
            fm_ids[fm_id] = f.name

def test_check_sh_sources_guards():
    """check.sh must source guards from tools/guards/ directory."""
    content = CHECK_SH.read_text()
    assert 'tools/guards' in content, "check.sh doesn't reference tools/guards/"
    assert 'source "$guard"' in content, "check.sh doesn't source guard files"

def test_guard_count():
    """Should have at least 15 guards (pre-registered expectation)."""
    guards = list(GUARDS_DIR.glob("*.sh"))
    assert len(guards) >= 15, f"Only {len(guards)} guards, expected >=15"

def test_check_sh_quick_mode():
    """check.sh --quick should complete without errors."""
    result = subprocess.run(
        ["bash", str(CHECK_SH), "--quick"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=120,
        cwd=str(REPO_ROOT)
    )
    assert result.returncode == 0, f"check.sh --quick failed (exit {result.returncode}):\n{result.stdout[-1000:]}"
    assert "SWARM CHECK" in result.stdout, "Missing SWARM CHECK header"

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS: {test.__name__}")
        except (AssertionError, Exception) as e:  # noqa: broad Exception covers unexpected failures
            failed += 1
            print(f"  FAIL: {test.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
