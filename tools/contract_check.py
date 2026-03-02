#!/usr/bin/env python3
"""F-META8: Minimal self-model contract checker (L-586).

Validates 5 components required for swarm coherence:
  1. Identity invariant — {I9, I10, I11, I12} defined in INVARIANTS.md
  2. Monotonic state vector — (L, P, B, F, session#) non-decreasing
  3. Active work pointer — NEXT.md has ≥1 actionable item
  4. Write obligation — current session produced ≥1 verifiable delta
  5. Protocol handshake — CORE.md hash matches INDEX.md stored hash

Usage:
  python3 tools/contract_check.py            # check all 5 components
  python3 tools/contract_check.py --json     # machine-readable output
  python3 tools/contract_check.py --session S355  # check specific session
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_identity_invariant():
    """Component 1: Identity invariant {I9-I12} must be defined."""
    path = os.path.join(REPO_ROOT, "beliefs", "INVARIANTS.md")
    if not os.path.exists(path):
        return False, "beliefs/INVARIANTS.md not found"
    with open(path) as f:
        text = f.read()
    required = {"I9", "I10", "I11", "I12"}
    found = set(re.findall(r"\bI(9|10|11|12)\b", text))
    found = {f"I{n}" for n in found}
    missing = required - found
    if missing:
        return False, f"missing invariants: {sorted(missing)}"
    return True, f"all 4 invariants present"


def check_monotonic_state_vector(session_id=None, strict=False):
    """Component 2: State vector (L, P, B, F, session#) is monotonic."""
    index_path = os.path.join(REPO_ROOT, "memory", "INDEX.md")
    if not os.path.exists(index_path):
        return False, "memory/INDEX.md not found"
    with open(index_path) as f:
        text = f.read()

    # Extract current counts from INDEX.md header (format: **N lessons**, **N beliefs**, etc.)
    counts = {}
    for label, pattern in [
        ("L", r"\*?\*?(\d+)\s*lessons?\*?\*?"),
        ("P", r"\*?\*?(\d+)\s*principles?\*?\*?"),
        ("B", r"\*?\*?(\d+)\s*beliefs?\*?\*?"),
        ("F", r"\*?\*?(\d+)\s*frontier\s*questions?\*?\*?"),
    ]:
        m = re.search(pattern, text[:800], re.IGNORECASE)
        if m:
            counts[label] = int(m.group(1))

    if len(counts) < 3:
        return False, f"state vector incomplete: found only {list(counts.keys())}"

    # Strict mode: verify header counts against actual file system (F-META8 step 3)
    if strict:
        lessons_dir = os.path.join(REPO_ROOT, "memory", "lessons")
        if os.path.isdir(lessons_dir):
            actual_l = len([f for f in os.listdir(lessons_dir)
                           if f.startswith("L-") and f.endswith(".md")])
            if "L" in counts and abs(counts["L"] - actual_l) > 2:
                return False, f"lesson count drift: header={counts['L']} actual={actual_l}"

    # Check session log for monotonicity (last 5 entries)
    session_log = os.path.join(REPO_ROOT, "memory", "SESSION-LOG.md")
    if os.path.exists(session_log):
        with open(session_log) as f:
            log_text = f.read()
        sessions = re.findall(r"\bS(\d+)\b", log_text)
        if len(sessions) >= 2:
            nums = [int(s) for s in sessions[-10:]]
            # Check roughly non-decreasing (allow small gaps from concurrency)
            decreases = sum(1 for i in range(1, len(nums)) if nums[i] < nums[i - 1] - 1)
            if decreases > 2:
                return False, f"session numbers not monotonic: {decreases} decreases in last 10"

    return True, f"state vector {counts}"


def check_active_work_pointer():
    """Component 3: NEXT.md has ≥1 actionable item."""
    path = os.path.join(REPO_ROOT, "tasks", "NEXT.md")
    if not os.path.exists(path):
        return False, "tasks/NEXT.md not found"
    with open(path) as f:
        text = f.read()

    # Look for session notes with **Next**: or active work items
    has_next = bool(re.search(r"\*\*[Nn]ext\*\*:", text))
    has_session_note = bool(re.search(r"## S\d+ session note", text))
    has_frontier_ref = bool(re.search(r"F-[A-Z]+\d+|F\d+", text))

    if has_next or has_session_note:
        return True, "active work pointer found"
    if has_frontier_ref:
        return True, "frontier references present (weak pointer)"
    return False, "no actionable items in NEXT.md"


def check_write_obligation(session_id=None):
    """Component 4: Current session produced ≥1 verifiable delta."""
    if not session_id:
        # Try to detect from recent commits
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True, text=True, cwd=REPO_ROOT,
            )
            m = re.search(r"\[S(\d+)\]", result.stdout)
            if m:
                session_id = f"S{m.group(1)}"
        except Exception:
            pass

    if not session_id:
        # Can't verify without session ID — check uncommitted changes
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=REPO_ROOT,
            )
            changes = [
                l for l in result.stdout.strip().split("\n")
                if l.strip() and not l.strip().startswith("??")
            ]
            if changes:
                return True, f"{len(changes)} uncommitted changes (pre-handoff)"
            return False, "no session ID and no uncommitted changes"
        except Exception:
            return False, "cannot determine session state"

    # Check git log for artifacts from this session
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--all", f"--grep=[{session_id}]", "--fixed-strings", "-20"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        commits = [l for l in result.stdout.strip().split("\n") if l.strip()]
        if commits:
            return True, f"{len(commits)} commits for {session_id}"
    except Exception:
        pass

    # Also check uncommitted state
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        changes = [
            l for l in result.stdout.strip().split("\n")
            if l.strip() and not l.strip().startswith("??")
        ]
        if changes:
            return True, f"{len(changes)} uncommitted changes (in-progress)"
    except Exception:
        pass

    return False, f"no artifacts found for {session_id}"


def check_protocol_handshake():
    """Component 5: CORE.md hash matches INDEX.md stored hash."""
    core_path = os.path.join(REPO_ROOT, "beliefs", "CORE.md")
    index_path = os.path.join(REPO_ROOT, "memory", "INDEX.md")

    if not os.path.exists(core_path):
        return False, "beliefs/CORE.md not found"
    if not os.path.exists(index_path):
        return False, "memory/INDEX.md not found"

    with open(core_path, "rb") as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()

    with open(index_path) as f:
        index_text = f.read()

    m = re.search(r"<!--\s*core_md_hash:\s*([a-f0-9]{64})\s*-->", index_text)
    if not m:
        return False, "no core_md_hash found in INDEX.md"

    stored_hash = m.group(1)
    if stored_hash != current_hash:
        return False, f"hash mismatch: stored={stored_hash[:12]}… current={current_hash[:12]}…"

    return True, "CORE.md hash verified"


def run_all(session_id=None, as_json=False, strict=False):
    checks = [
        ("identity_invariant", check_identity_invariant),
        ("monotonic_state_vector", lambda: check_monotonic_state_vector(session_id, strict=strict)),
        ("active_work_pointer", check_active_work_pointer),
        ("write_obligation", lambda: check_write_obligation(session_id)),
        ("protocol_handshake", check_protocol_handshake),
    ]

    results = {}
    all_pass = True
    for name, fn in checks:
        try:
            passed, detail = fn()
        except Exception as e:
            passed, detail = False, f"error: {e}"
        results[name] = {"pass": passed, "detail": detail}
        if not passed:
            all_pass = False

    if as_json:
        output = {
            "contract_version": "1.0",
            "session": session_id or "unknown",
            "all_pass": all_pass,
            "components": results,
            "pass_count": sum(1 for r in results.values() if r["pass"]),
            "total": len(results),
        }
        print(json.dumps(output, indent=2))
    else:
        print("=== CONTRACT CHECK (F-META8) ===")
        for name, r in results.items():
            status = "PASS" if r["pass"] else "FAIL"
            print(f"  [{status}] {name}: {r['detail']}")
        passed = sum(1 for r in results.values() if r["pass"])
        print(f"\nResult: {passed}/{len(results)} components satisfied")
        if all_pass:
            print("CONTRACT: SATISFIED")
        else:
            print("CONTRACT: VIOLATED")

    return all_pass, results


def main():
    parser = argparse.ArgumentParser(description="F-META8 self-model contract checker")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--session", help="Session ID (e.g. S355)")
    parser.add_argument("--strict", action="store_true",
                        help="Verify header counts against file system (F-META8 accuracy mode)")
    args = parser.parse_args()

    all_pass, _ = run_all(session_id=args.session, as_json=args.json, strict=args.strict)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
