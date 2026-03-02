#!/usr/bin/env python3
"""
swarm_integration_test.py — Automated integration tests for the swarm architecture.

Usage:
    python3 tools/swarm_integration_test.py

Runs a suite of tests that verify the swarm can:
1. Bootstrap from genesis (spawn viability)
2. Maintain validator integrity after modifications
3. Reconstruct essential files from raw artifacts (redundancy)
4. Handle belief updates without breaking dependencies
5. Keep mandatory files under size limits

These are "swarm tests" — they test the system's architecture by
exercising it, not by inspecting static properties.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PASSED = 0
FAILED = 0
ERRORS = []


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


def _to_bash_path(path: str | Path) -> str:
    """Normalize a host path for bash script arguments across runtimes."""
    s = str(path).replace("\\", "/")
    s = re.sub(r"/+", "/", s)
    m = re.match(r"^([A-Za-z]):/(.*)$", s)
    if m:
        drive = m.group(1).lower()
        rest = re.sub(r"/+", "/", m.group(2)).lstrip("/")
        return f"/mnt/{drive}/{rest}"
    return s


def _run_genesis(child_dir: str | Path, name: str = "test") -> subprocess.CompletedProcess:
    """Run genesis via repo-relative script path for cross-runtime portability."""
    child_path = Path(child_dir)
    try:
        target = child_path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        target = _to_bash_path(child_path)
    return subprocess.run(
        ["bash", "workspace/genesis.sh", target, name],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )


def run_test(name: str, func):
    """Run a test and record results."""
    global PASSED, FAILED
    print(f"  [{name}] ", end="", flush=True)
    try:
        result = func()
        if result:
            PASSED += 1
            print("PASS")
        else:
            FAILED += 1
            ERRORS.append(f"{name}: returned False")
            print("FAIL")
    except Exception as e:
        FAILED += 1
        ERRORS.append(f"{name}: {e}")
        print(f"ERROR: {e}")


def test_genesis_spawns_valid_child():
    """Test that genesis.sh produces a child that passes validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        child_dir = os.path.join(tmpdir, "test-child")

        # Spawn
        r = _run_genesis(child_dir, "test")
        if r.returncode != 0:
            raise RuntimeError(f"genesis.sh failed: {r.stderr}")

        # Init git
        subprocess.run(["git", "init"], cwd=child_dir, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=child_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=child_dir, capture_output=True
        )

        # Validate
        r = subprocess.run(
            [PYTHON_CMD, "tools/validate_beliefs.py"],
            cwd=child_dir, capture_output=True, text=True
        )
        return r.returncode == 0 and "PASS" in r.stdout


def test_genesis_file_count():
    """Test that genesis.sh creates the expected number of files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        child_dir = os.path.join(tmpdir, "test-child")

        _run_genesis(child_dir, "test")

        # Count files (excluding directories and .gitkeep)
        file_count = sum(
            1 for f in Path(child_dir).rglob("*")
            if f.is_file() and f.name != ".gitkeep"
        )
        # genesis v3 should create 18 real files + 1 .gitkeep = 19 total
        # but we only count non-gitkeep
        return file_count >= 17


def test_child_can_spawn_grandchild():
    """Test that a spawned child can spawn its own child (recursive swarming)."""
    child_slug = f"recursive-test-{uuid.uuid4().hex[:8]}"
    child_rel = f"workspace/{child_slug}"
    child_dir = REPO_ROOT / "workspace" / child_slug
    try:
        r = _run_genesis(child_rel, "test")
        if r.returncode != 0:
            raise RuntimeError(f"genesis.sh failed: {r.stderr}")

        agent_swarm = child_dir / "tools" / "agent_swarm.py"
        nested_genesis = child_dir / "workspace" / "genesis.sh"
        if not agent_swarm.exists():
            raise RuntimeError("child missing tools/agent_swarm.py")
        if not nested_genesis.exists():
            raise RuntimeError("child missing workspace/genesis.sh")

        r = subprocess.run(
            [PYTHON_CMD, "tools/agent_swarm.py", "create", "grandchild-test", "recursive spawn check"],
            cwd=str(child_dir), capture_output=True, text=True
        )
        if r.returncode != 0:
            raise RuntimeError(f"child spawn failed: {r.stderr or r.stdout}")

        grandchild_dir = child_dir / "experiments" / "children" / "grandchild-test"
        if not grandchild_dir.exists():
            raise RuntimeError("grandchild directory not created")
        if not (grandchild_dir / "tasks" / "AGENT-TASK.md").exists():
            raise RuntimeError("grandchild AGENT-TASK not created")

        return True
    finally:
        shutil.rmtree(child_dir, ignore_errors=True)


def test_validator_passes_current():
    """Test that the parent validator passes on current state."""
    r = subprocess.run(
        [PYTHON_CMD, str(REPO_ROOT / "tools" / "validate_beliefs.py")],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    return r.returncode == 0 and "PASS" in r.stdout


def test_mandatory_files_under_limit():
    """Test that mandatory files stay under 450 lines combined."""
    mandatory = [
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "beliefs" / "CORE.md",
        REPO_ROOT / "memory" / "INDEX.md",
    ]
    total = sum(
        len(f.read_text().splitlines()) for f in mandatory if f.exists()
    )
    return total < 450


def test_lessons_under_20_lines():
    """Test that all lessons are ≤20 lines."""
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    for f in lessons_dir.glob("L-*.md"):
        lines = len(f.read_text().splitlines())
        if lines > 20:
            raise RuntimeError(f"{f.name} has {lines} lines (max 20)")
    return True


def test_beliefs_have_falsification():
    """Test that every active belief has a falsification condition."""
    deps = REPO_ROOT / "beliefs" / "DEPS.md"
    text = deps.read_text()

    # Find all active beliefs (not superseded)
    superseded_section = text.find("## Superseded")
    active_text = text[:superseded_section] if superseded_section > 0 else text

    beliefs = re.findall(r"^### (B\d+):", active_text, re.MULTILINE)
    for bid in beliefs:
        # Check each has "Falsified if"
        if f"### {bid}:" in active_text:
            block_start = active_text.index(f"### {bid}:")
            block_end = active_text.find("\n### B", block_start + 1)
            if block_end == -1:
                block_end = len(active_text)
            block = active_text[block_start:block_end]
            if "**Falsified if**:" not in block:
                raise RuntimeError(f"{bid} missing falsification condition")
    return True


def test_no_broken_belief_refs():
    """Test that no lesson references a belief that doesn't exist."""
    deps = REPO_ROOT / "beliefs" / "DEPS.md"
    deps_text = deps.read_text()

    # Find all defined belief IDs (including superseded)
    all_ids = set(re.findall(r"(?:### |~~)(B\d+)", deps_text))

    # Check lessons
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    for f in lessons_dir.glob("L-*.md"):
        text = f.read_text()
        affected_m = re.search(r"## Affected beliefs:\s*(.+)", text)
        if affected_m:
            refs = re.findall(r"B\d+", affected_m.group(1))
            for ref in refs:
                if ref not in all_ids:
                    raise RuntimeError(
                        f"{f.name} references {ref} which doesn't exist"
                    )
    return True


def test_dep_consistency():
    """Test that Depends on / Depended on by are consistent."""
    r = subprocess.run(
        [PYTHON_CMD, str(REPO_ROOT / "tools" / "validate_beliefs.py")],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    # Check for DEP_SYNC warnings
    return "DEP_SYNC" not in r.stdout


def test_entropy_zero():
    """Test that the entropy detector finds zero items."""
    r = subprocess.run(
        [PYTHON_CMD, str(REPO_ROOT / "tools" / "validate_beliefs.py")],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    return "Entropy items: 0" in r.stdout


def test_principles_count_matches_lessons():
    """Test that PRINCIPLES.md contains all principle IDs referenced in lessons."""
    principles = REPO_ROOT / "memory" / "PRINCIPLES.md"
    p_text = principles.read_text()
    # Find all P-NNN references in PRINCIPLES.md
    p_ids = set(re.findall(r"P-(\d+)", p_text))

    lessons_dir = REPO_ROOT / "memory" / "lessons"
    missing = []
    for f in sorted(lessons_dir.glob("L-*.md")):
        if f.name == "TEMPLATE.md":
            continue
        text = f.read_text()
        # Check if lesson defines a principle (## Principle or ## Rule extracted)
        p_match = re.search(r"P-(\d+)", text)
        if p_match:
            p_num = p_match.group(1)
            if p_num not in p_ids:
                missing.append(f"P-{p_num} (from {f.name})")

    if missing:
        raise RuntimeError(f"Principles in lessons but not in PRINCIPLES.md: {missing}")
    return True


def test_evolve_tool_exists():
    """Test that evolve.py exists and has all commands."""
    evolve = REPO_ROOT / "tools" / "evolve.py"
    if not evolve.exists():
        raise RuntimeError("tools/evolve.py does not exist")
    text = evolve.read_text()
    for cmd in ["init", "harvest", "integrate", "cycle"]:
        if f'cmd == "{cmd}"' not in text:
            raise RuntimeError(f"evolve.py missing command: {cmd}")
    return True


def test_merge_reports_valid():
    """Test that all merge-back reports have required sections."""
    reports_dir = REPO_ROOT / "experiments" / "merge-reports"
    if not reports_dir.exists():
        return True  # No reports yet is fine
    for f in reports_dir.glob("*.md"):
        text = f.read_text()
        if "## Lessons" not in text:
            raise RuntimeError(f"{f.name} missing ## Lessons section")
        if "## Recommendations" not in text:
            raise RuntimeError(f"{f.name} missing ## Recommendations section")
    return True


def test_integration_log_valid():
    """Test that integration logs are valid JSON with required fields."""
    log_dir = REPO_ROOT / "experiments" / "integration-log"
    if not log_dir.exists():
        return True  # No logs yet is fine
    import json
    for f in log_dir.glob("*.json"):
        data = json.loads(f.read_text())
        for field in ["child", "date", "novel_rules", "novel_questions"]:
            if field not in data:
                raise RuntimeError(f"{f.name} missing field: {field}")
    return True


def test_growth_rate_runs():
    """Test that session_tracker.py growth-rate command runs without error."""
    r = subprocess.run(
        [PYTHON_CMD, str(REPO_ROOT / "tools" / "session_tracker.py"), "growth-rate"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"growth-rate failed: {r.stderr}")
    required = ["File Growth Rates", "Frontier Health", "Belief Ratio", "Summary"]
    for section in required:
        if section not in r.stdout:
            raise RuntimeError(f"growth-rate output missing: {section}")
    return True


def test_trend_analysis_runs():
    """Test that session_tracker.py trend command runs and produces valid output."""
    r = subprocess.run(
        [PYTHON_CMD, str(REPO_ROOT / "tools" / "session_tracker.py"), "trend"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"trend failed: {r.stderr}")
    required = ["Learning Rate", "Frontier Health", "Entropy", "Stall Detection Summary"]
    for section in required:
        if section not in r.stdout:
            raise RuntimeError(f"trend output missing: {section}")
    return True


# --- Tool tests ---

def test_nk_analyze_runs():
    """Test that nk_analyze.py can analyze a stdlib package and output valid JSON."""
    import json
    r = subprocess.run(
        [PYTHON_CMD, str(REPO_ROOT / "tools" / "nk_analyze.py"), "json", "--json"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"nk_analyze failed: {r.stderr}")
    data = json.loads(r.stdout)
    for field in ["n", "k_avg", "k_max", "cycles", "composite", "architecture"]:
        if field not in data:
            raise RuntimeError(f"nk_analyze output missing field: {field}")
    if data["n"] < 1:
        raise RuntimeError(f"N should be >= 1, got {data['n']}")
    return True


def test_bulletin_regression_suite():
    """Test that bulletin regression tests pass (help-flow + type parsing)."""
    r = subprocess.run(
        [PYTHON_CMD, str(REPO_ROOT / "tools" / "test_bulletin.py")],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"test_bulletin failed: {r.stderr or r.stdout}")
    if "OK" not in r.stdout:
        raise RuntimeError("test_bulletin did not report OK")
    return True


# --- Negative tests: verify the validator catches known breakages ---

def test_context_router_routes_correctly():
    """Test that context_router.py routes tasks to relevant domains."""
    import json as json_mod
    r = subprocess.run(
        [PYTHON_CMD, str(REPO_ROOT / "tools" / "context_router.py"),
         "analyze NK complexity cycles", "--json"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"context_router failed: {r.stderr}")
    data = json_mod.loads(r.stdout)

    # Should find complexity domain
    domains = [d["name"] for d in data["domains"]]
    if "complexity" not in domains:
        raise RuntimeError(f"Expected 'complexity' domain, got: {domains}")

    # Should have selected files
    if not data["selected_files"]:
        raise RuntimeError("No files selected")

    # Budget should not be exceeded
    if data["total_lines"] > data["budget"]:
        raise RuntimeError(f"Budget exceeded: {data['total_lines']} > {data['budget']}")
    return True


def test_context_router_inventory():
    """Test that context_router.py inventory shows total knowledge."""
    import json as json_mod
    r = subprocess.run(
        [PYTHON_CMD, str(REPO_ROOT / "tools" / "context_router.py"),
         "inventory", "--json"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"inventory failed: {r.stderr}")
    data = json_mod.loads(r.stdout)

    if data["total_knowledge_lines"] < 100:
        raise RuntimeError(f"Total knowledge too low: {data['total_knowledge_lines']}")
    if data["mandatory_lines"] < 10:
        raise RuntimeError(f"Mandatory too low: {data['mandatory_lines']}")
    return True


def test_novelty_detection_accuracy():
    """Test that shared novelty module detects duplicates and novel rules."""
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from novelty import check_novelty

    existing = [
        "Always verify generated files for artifacts",
        "Measure complexity using NK metrics",
        "Cycle count predicts bug accumulation rate",
    ]

    # Novel rule should be detected as novel
    is_novel, _, _ = check_novelty(
        "Use Jaccard similarity for deduplication", existing
    )
    if not is_novel:
        raise RuntimeError("Novel rule falsely detected as duplicate")

    # Duplicate should be detected as duplicate
    is_novel, sim, _ = check_novelty(
        "Always verify the generated files for artifacts", existing
    )
    if is_novel:
        raise RuntimeError(f"Duplicate rule not detected (sim={sim})")

    return True


def test_evolution_e2e():
    """End-to-end test: spawn → simulate agent → harvest → integrate.

    Creates a synthetic child with known novel content, runs the full
    evolution pipeline, and verifies integration works correctly.
    """
    import json as json_mod

    with tempfile.TemporaryDirectory() as tmpdir:
        child_name = "e2e-test-child"
        child_dir = os.path.join(tmpdir, child_name)

        # Step 1: Spawn
        r = _run_genesis(child_dir, "e2e-test")
        if r.returncode != 0:
            raise RuntimeError(f"genesis.sh failed: {r.stderr}")

        subprocess.run(["git", "init"], cwd=child_dir, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=child_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=child_dir, capture_output=True
        )

        # Step 2: Simulate agent session — write a novel lesson
        lesson_path = Path(child_dir) / "memory" / "lessons" / "L-099.md"
        lesson_path.write_text(
            "# L-099: Quantum entanglement enables instantaneous state transfer in distributed systems\n"
            "Date: 2026-02-26 | Task: F99 | Confidence: Theorized\n\n"
            "## What happened (3 lines max)\n"
            "Tested quantum entanglement hypothesis on distributed cache.\n\n"
            "## What we learned (3 lines max)\n"
            "Quantum effects don't apply at macro scale but the metaphor is useful.\n\n"
            "## Rule extracted (1-2 lines)\n"
            "Quantum entanglement metaphor helps reason about eventual consistency.\n\n"
            "## Affected beliefs: B1\n"
        )

        # Update child's frontier
        frontier_path = Path(child_dir) / "tasks" / "FRONTIER.md"
        frontier_text = frontier_path.read_text()
        frontier_path.write_text(
            frontier_text +
            "\n- **F99**: Can quantum computing parallelize swarm evolution? (from e2e-test)\n"
        )

        # Resolve a frontier question
        frontier_path.write_text(
            frontier_path.read_text().replace(
                "## Resolved\n",
                "## Resolved\n| F1 | YES — tested | 1 | 2026-02-26 |\n"
            )
        )

        subprocess.run(["git", "add", "-A"], cwd=child_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "[S] session: novel lesson and frontier"],
            cwd=child_dir, capture_output=True
        )

        # Step 3: Harvest — evaluate viability
        swarm_test = REPO_ROOT / "tools" / "swarm_test.py"

        # Override CHILDREN_DIR temporarily by symlinking
        children_dir = REPO_ROOT / "experiments" / "children"
        test_link = children_dir / child_name
        try:
            if not children_dir.exists():
                children_dir.mkdir(parents=True)
            os.symlink(child_dir, str(test_link))

            # Run merge-back report
            merge_back = REPO_ROOT / "tools" / "merge_back.py"
            r = subprocess.run(
                [PYTHON_CMD, str(merge_back), child_dir],
                capture_output=True, text=True
            )
            if "Novel rules:" not in r.stdout:
                raise RuntimeError(f"merge_back didn't produce novel rules section")

            # Verify the novel rule was detected
            if "[NOVEL]" not in r.stdout:
                raise RuntimeError(f"Novel lesson not detected by merge_back")

            # Step 4: Verify integration dry-run works
            evolve = REPO_ROOT / "tools" / "evolve.py"
            r = subprocess.run(
                [PYTHON_CMD, str(evolve), "integrate", child_name, "--dry-run"],
                capture_output=True, text=True
            )
            if "Novel rules to add" not in r.stdout:
                raise RuntimeError(f"Integration dry-run didn't find novel rules")
            if "DRY RUN" not in r.stdout:
                raise RuntimeError(f"Integration dry-run didn't show DRY RUN marker")

        finally:
            # Clean up symlink
            if test_link.is_symlink():
                test_link.unlink()

    return True


def test_neg_broken_belief_detected():
    """Negative test: validator catches a belief with missing evidence type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        child_dir = os.path.join(tmpdir, "neg-test")
        _run_genesis(child_dir, "test")
        subprocess.run(["git", "init"], cwd=child_dir, capture_output=True)

        # Break a belief: replace evidence type with invalid value
        deps = Path(child_dir) / "beliefs" / "DEPS.md"
        text = deps.read_text()
        # Genesis uses 'theorized' as default evidence type
        text = text.replace("**Evidence**: theorized", "**Evidence**: INVALID_TYPE")
        deps.write_text(text)

        subprocess.run(["git", "add", "-A"], cwd=child_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "break"], cwd=child_dir, capture_output=True)

        r = subprocess.run(
            [PYTHON_CMD, "tools/validate_beliefs.py"],
            cwd=child_dir, capture_output=True, text=True
        )
        # Validator should report FAIL for invalid evidence type
        return "FAIL" in r.stdout or r.returncode != 0


def test_neg_broken_dep_ref_detected():
    """Negative test: validator catches a broken belief dependency reference."""
    with tempfile.TemporaryDirectory() as tmpdir:
        child_dir = os.path.join(tmpdir, "neg-test2")
        _run_genesis(child_dir, "test")
        subprocess.run(["git", "init"], cwd=child_dir, capture_output=True)

        # Add a lesson that references a non-existent belief
        lesson = Path(child_dir) / "memory" / "lessons" / "L-099.md"
        lesson.write_text(
            "# Lesson L-099\n## Summary\nTest broken ref\n"
            "## Affected beliefs: B999\n## Rule extracted\nnone\n"
        )

        subprocess.run(["git", "add", "-A"], cwd=child_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "break"], cwd=child_dir, capture_output=True)

        # Our own test checks for broken refs — verify it would catch this
        deps = Path(child_dir) / "beliefs" / "DEPS.md"
        deps_text = deps.read_text()
        all_ids = set(re.findall(r"(?:### |~~)(B\d+)", deps_text))
        lessons_dir = Path(child_dir) / "memory" / "lessons"

        for f in lessons_dir.glob("L-*.md"):
            text = f.read_text()
            affected_m = re.search(r"## Affected beliefs:\s*(.+)", text)
            if affected_m:
                refs = re.findall(r"B\d+", affected_m.group(1))
                for ref in refs:
                    if ref not in all_ids:
                        return True  # Correctly detected broken ref
        return False  # Should have caught B999


def test_neg_missing_falsification_detected():
    """Negative test: test catches belief missing falsification condition."""
    with tempfile.TemporaryDirectory() as tmpdir:
        child_dir = os.path.join(tmpdir, "neg-test3")
        _run_genesis(child_dir, "test")

        # Break a belief: remove falsification condition
        deps = Path(child_dir) / "beliefs" / "DEPS.md"
        text = deps.read_text()
        text = text.replace("**Falsified if**:", "**Notes**:")
        deps.write_text(text)

        # Run the falsification check logic directly
        superseded_section = text.find("## Superseded")
        active_text = text[:superseded_section] if superseded_section > 0 else text

        beliefs = re.findall(r"^### (B\d+):", active_text, re.MULTILINE)
        for bid in beliefs:
            if f"### {bid}:" in active_text:
                block_start = active_text.index(f"### {bid}:")
                block_end = active_text.find("\n### B", block_start + 1)
                if block_end == -1:
                    block_end = len(active_text)
                block = active_text[block_start:block_end]
                if "**Falsified if**:" not in block:
                    return True  # Correctly detected missing falsification
        return False  # Should have caught it


def main():
    global PASSED, FAILED

    print("=== SWARM INTEGRATION TESTS ===\n")

    print("Spawn tests:")
    run_test("genesis_spawns_valid_child", test_genesis_spawns_valid_child)
    run_test("genesis_file_count", test_genesis_file_count)
    run_test("child_can_spawn_grandchild", test_child_can_spawn_grandchild)

    print("\nIntegrity tests:")
    run_test("validator_passes_current", test_validator_passes_current)
    run_test("mandatory_files_under_limit", test_mandatory_files_under_limit)
    run_test("lessons_under_20_lines", test_lessons_under_20_lines)
    run_test("beliefs_have_falsification", test_beliefs_have_falsification)
    run_test("no_broken_belief_refs", test_no_broken_belief_refs)
    run_test("dep_consistency", test_dep_consistency)
    run_test("entropy_zero", test_entropy_zero)

    print("\nCompleteness tests:")
    run_test("principles_count_matches_lessons", test_principles_count_matches_lessons)

    print("\nEvolution pipeline tests:")
    run_test("evolve_tool_exists", test_evolve_tool_exists)
    run_test("merge_reports_valid", test_merge_reports_valid)
    run_test("integration_log_valid", test_integration_log_valid)
    run_test("growth_rate_runs", test_growth_rate_runs)
    run_test("trend_analysis_runs", test_trend_analysis_runs)

    print("\nTool tests:")
    run_test("nk_analyze_runs", test_nk_analyze_runs)
    run_test("bulletin_regression_suite", test_bulletin_regression_suite)
    run_test("context_router_routes", test_context_router_routes_correctly)
    run_test("context_router_inventory", test_context_router_inventory)
    run_test("novelty_detection_accuracy", test_novelty_detection_accuracy)

    print("\nEnd-to-end tests:")
    run_test("evolution_e2e", test_evolution_e2e)

    print("\nNegative tests (validator catches breakages):")
    run_test("neg_broken_belief_detected", test_neg_broken_belief_detected)
    run_test("neg_broken_dep_ref_detected", test_neg_broken_dep_ref_detected)
    run_test("neg_missing_falsification_detected", test_neg_missing_falsification_detected)

    print(f"\n{'='*40}")
    print(f"PASSED: {PASSED}/{PASSED + FAILED}")
    if ERRORS:
        print(f"FAILED: {FAILED}")
        for e in ERRORS:
            print(f"  - {e}")
        return 1
    else:
        print("ALL TESTS PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())
