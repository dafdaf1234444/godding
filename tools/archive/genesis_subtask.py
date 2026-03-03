#!/usr/bin/env python3
"""
genesis_subtask.py — Intelligent genesis sub-tasking for efficient swarm spawning.

Makes genesis decomposable into parallelizable sub-tasks. The swarm decides
WHEN sub-tasking is more efficient and HOW to break genesis work down.

Usage:
    python3 tools/genesis_subtask.py profile <task-description>
    python3 tools/genesis_subtask.py select [--task=X] [--ablation]
    python3 tools/genesis_subtask.py decompose <task-description> [--strategy=auto]
    python3 tools/genesis_subtask.py batch-spawn <config.json>
    python3 tools/genesis_subtask.py batch-harvest [--integrate]
    python3 tools/genesis_subtask.py selector-feedback [--apply]

Commands:
    profile           — Analyze task, recommend genesis strategy (mono/parallel/lean/ablation)
    select            — Choose optimal atom set based on F107 ablation data + task type
    decompose         — Break genesis into parallelizable sub-agent prompts
    batch-spawn       — Generate parallel spawn configs + sub-agent prompts
    batch-harvest     — Parallel harvest + compare all children
    selector-feedback — Close the selection loop: fitness → template improvement (P1, L-497)

Closes F-DNA1 selection loop and addresses L-497 P1 (genesis_selector.py).
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHILDREN_DIR = REPO_ROOT / "experiments" / "children"
ABLATION_FILE = REPO_ROOT / "experiments" / "architecture" / "f107-genesis-ablation.md"
INTEGRATION_LOG_DIR = REPO_ROOT / "experiments" / "integration-log"
SELECTOR_STATE_FILE = REPO_ROOT / "workspace" / "genesis-selector-state.json"

# --- F107 Ablation Knowledge (compiled from f107-genesis-ablation.md) ---
# Each atom has a weight: 1.0 = always include, 0.0 = never needed
# Weights derived from: child viability data, parent live test (S57), ablation v1/v2
ATOM_WEIGHTS = {
    # NEVER REMOVE — always 1.0
    "core-beliefs":       {"weight": 1.0, "removable": False, "evidence": "unanimous load-bearing"},
    "validator":           {"weight": 1.0, "removable": False, "evidence": "epistemic backbone"},
    # Load-bearing — high weight
    "session-protocol":    {"weight": 0.95, "removable": False, "evidence": "session entry point"},
    "memory-index":        {"weight": 0.90, "removable": False, "evidence": "structural map"},
    "frontier":            {"weight": 0.85, "removable": False, "evidence": "drives evolution"},
    "lesson-template":     {"weight": 0.80, "removable": False, "evidence": "lesson format"},
    "next-handoff":        {"weight": 0.80, "removable": False, "evidence": "session handoff"},
    # Load-bearing at session 3+ (catalysts)
    "distill-protocol":    {"weight": 0.70, "removable": True,  "evidence": "load-bearing session 2+, v3 ablation pending"},
    "belief-tracking":     {"weight": 0.65, "removable": True,  "evidence": "load-bearing session 3+ (belief updates)"},
    "principles-inherit":  {"weight": 0.60, "removable": True,  "evidence": "P-113 cross-session inheritance"},
    # Catalysts — needed for bootstrap, dispensable after 2-3 sessions
    "conflict-protocol":   {"weight": 0.40, "removable": True,  "evidence": "ablation candidate, rarely invoked"},
    "verify-protocol":     {"weight": 0.35, "removable": True,  "evidence": "3-S rule, partially redundant with falsification"},
    # NOT load-bearing — confirmed by ablation v1/v2 + parent live test S57
    "session-modes":       {"weight": 0.10, "removable": True,  "evidence": "belief-no-modes: viable (22 lessons), S57 parent"},
    "pre-commit-hook":     {"weight": 0.10, "removable": True,  "evidence": "children rarely install hooks"},
    "first-task":          {"weight": 0.30, "removable": True,  "evidence": "helpful for session 1 only"},
    # Recursive tooling — depends on whether child needs to spawn
    "self-swarm-tooling":  {"weight": 0.20, "removable": True,  "evidence": "v7 addition, only for recursive spawning"},
    "sibling-bulletins":   {"weight": 0.15, "removable": True,  "evidence": "only useful if siblings exist"},
}

# Task type → atom relevance multipliers
TASK_PROFILES = {
    "research": {
        # Research doesn't need build modes, hooks, or swarm tooling
        "session-modes": 0.0, "pre-commit-hook": 0.0, "self-swarm-tooling": 0.0,
        "distill-protocol": 1.2,  # extra important for research
        "verify-protocol": 1.3,   # 3-S rule matters for research
    },
    "build": {
        "session-modes": 0.0, "verify-protocol": 0.5,
        "first-task": 1.5,  # structured task helps builders
    },
    "domain-expert": {
        "session-modes": 0.0, "self-swarm-tooling": 0.0,
        "sibling-bulletins": 0.0, "pre-commit-hook": 0.0,
        "distill-protocol": 1.3,
    },
    "ablation": {
        # Ablation needs full template to measure removal effects
        "session-modes": 1.0, "pre-commit-hook": 1.0,
        "self-swarm-tooling": 1.0,
    },
    "foreign": {
        # Foreign repos use genesis_foreign.sh — minimal atoms
        "session-modes": 0.0, "pre-commit-hook": 0.0,
        "self-swarm-tooling": 0.0, "sibling-bulletins": 0.0,
        "conflict-protocol": 0.0, "belief-tracking": 0.5,
        "principles-inherit": 0.0, "first-task": 0.0,
    },
    "peer": {
        # Peers get Genesis DNA — full knowledge inheritance
        "principles-inherit": 1.5, "distill-protocol": 1.3,
        "session-modes": 0.0,
    },
}

# Strategy thresholds
PARALLEL_THRESHOLD = 3    # >= 3 independent dimensions → parallelize
LEAN_KEYWORDS = ["foreign", "external", "codebase", "repo", "stewardship", "quick"]
DEPTH_KEYWORDS = ["expert", "deep", "investigate", "council", "domain", "specialist"]
BREADTH_KEYWORDS = ["survey", "compare", "breadth", "multiple", "all domains", "comprehensive"]
ABLATION_KEYWORDS = ["ablation", "evolve", "test genesis", "mutation", "variation"]


def _pick_python_cmd() -> str:
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
    return sys.executable


PYTHON_CMD = _pick_python_cmd()


def _current_session() -> int:
    session_log = REPO_ROOT / "memory" / "SESSION-LOG.md"
    if not session_log.exists():
        return 0
    text = session_log.read_text()
    nums = [int(m) for m in re.findall(r"S(\d{3,})\b", text)]
    return max(nums) if nums else 0


def _count_children() -> int:
    if not CHILDREN_DIR.exists():
        return 0
    return len([d for d in CHILDREN_DIR.iterdir() if d.is_dir()])


def _classify_task(task: str) -> str:
    """Classify a task into a profile type based on keywords."""
    task_lower = task.lower()
    if any(kw in task_lower for kw in ABLATION_KEYWORDS):
        return "ablation"
    if any(kw in task_lower for kw in LEAN_KEYWORDS):
        return "foreign"
    if any(kw in task_lower for kw in DEPTH_KEYWORDS):
        return "domain-expert"
    if any(kw in task_lower for kw in BREADTH_KEYWORDS):
        return "research"
    return "research"  # default


def _recommend_strategy(task: str) -> dict:
    """Analyze task and recommend optimal genesis strategy."""
    task_lower = task.lower()
    task_type = _classify_task(task)

    # Count independent dimensions in the task
    dimensions = []
    if "domain" in task_lower:
        # Count distinct domains mentioned
        domain_dir = REPO_ROOT / "domains"
        if domain_dir.exists():
            domains = [d.name for d in domain_dir.iterdir() if d.is_dir()]
            mentioned = [d for d in domains if d in task_lower]
            if mentioned:
                dimensions.extend(mentioned)
            elif "all domain" in task_lower or "every domain" in task_lower:
                dimensions.extend(domains[:5])  # cap at 5 parallel
    if "compare" in task_lower or "versus" in task_lower or " vs " in task_lower:
        dimensions.append("comparison-axis")
    if "personality" in task_lower or "perspective" in task_lower:
        dimensions.append("personality-axis")

    # Decision logic
    if any(kw in task_lower for kw in LEAN_KEYWORDS):
        return {
            "strategy": "lean",
            "reason": "Task targets external/foreign repos — use minimal genesis_foreign profile",
            "children": 1,
            "profile": "foreign",
            "parallel": False,
            "script": "genesis_foreign.sh",
        }

    if any(kw in task_lower for kw in ABLATION_KEYWORDS):
        return {
            "strategy": "ablation",
            "reason": "Task is evolution experiment — use full template with systematic variation",
            "children": 3,  # default: control + 2 variants
            "profile": "ablation",
            "parallel": True,
            "script": "genesis.sh",
        }

    if len(dimensions) >= PARALLEL_THRESHOLD or any(kw in task_lower for kw in BREADTH_KEYWORDS):
        n_children = min(len(dimensions), 5) if dimensions else 3
        return {
            "strategy": "parallel",
            "reason": f"Task has {len(dimensions)} independent dimensions — parallelize across children",
            "children": max(n_children, 2),
            "profile": task_type,
            "parallel": True,
            "dimensions": dimensions,
            "script": "genesis.sh",
        }

    return {
        "strategy": "mono",
        "reason": "Task needs focused depth — single child with domain-expert profile",
        "children": 1,
        "profile": task_type,
        "parallel": False,
        "script": "genesis.sh",
    }


def profile_task(task: str):
    """Analyze task, recommend genesis strategy."""
    rec = _recommend_strategy(task)
    task_type = _classify_task(task)

    print(f"=== GENESIS PROFILE: {task[:60]} ===\n")
    print(f"Task type:    {task_type}")
    print(f"Strategy:     {rec['strategy'].upper()}")
    print(f"Children:     {rec['children']}")
    print(f"Parallel:     {'yes' if rec['parallel'] else 'no'}")
    print(f"Script:       {rec['script']}")
    print(f"Reason:       {rec['reason']}")

    if rec.get("dimensions"):
        print(f"Dimensions:   {', '.join(rec['dimensions'])}")

    # Show atom selection
    atoms = select_atoms(task_type)
    included = [a for a, v in atoms.items() if v["include"]]
    excluded = [a for a, v in atoms.items() if not v["include"]]
    print(f"\nAtoms included: {len(included)}/{len(atoms)}")
    if excluded:
        print(f"Atoms excluded: {', '.join(excluded)}")
        saved = sum(1 for a in excluded if a in ATOM_WEIGHTS)
        print(f"  (~{saved * 30}L saved from genesis template)")

    # Efficiency estimate
    if rec["parallel"]:
        print(f"\nEfficiency: {rec['children']}x parallel = ~{rec['children']}x throughput vs sequential")
    if rec["strategy"] == "lean":
        print(f"\nEfficiency: ~7 files vs ~60 files (lean profile)")

    # Sub-agent prompt preview
    print(f"\nTo execute: python3 tools/genesis_subtask.py decompose \"{task}\"")

    return rec


def select_atoms(task_type: str = "research", ablation_atom: str = None) -> dict:
    """Choose optimal atom set based on ablation data + task type."""
    profile_mods = TASK_PROFILES.get(task_type, {})
    selector_state = _load_selector_state()

    result = {}
    for atom, info in ATOM_WEIGHTS.items():
        base_weight = info["weight"]

        # Apply task profile modifier
        modifier = profile_mods.get(atom, 1.0)
        adjusted = base_weight * modifier

        # Apply selector feedback (empirical success rate)
        if atom in selector_state.get("atom_success_rates", {}):
            empirical = selector_state["atom_success_rates"][atom]
            # Blend: 70% structural, 30% empirical
            adjusted = 0.7 * adjusted + 0.3 * empirical

        # Apply ablation exclusion
        if ablation_atom and atom == ablation_atom:
            adjusted = 0.0

        include = adjusted >= 0.25  # inclusion threshold
        if not info["removable"]:
            include = True  # never exclude non-removable atoms

        result[atom] = {
            "weight": round(adjusted, 2),
            "include": include,
            "evidence": info["evidence"],
            "removable": info["removable"],
        }

    return result


def _load_selector_state() -> dict:
    """Load the selector feedback state (empirical atom success rates)."""
    if SELECTOR_STATE_FILE.exists():
        return json.loads(SELECTOR_STATE_FILE.read_text())
    return {"atom_success_rates": {}, "generation": 0, "last_updated": None}


def _save_selector_state(state: dict):
    SELECTOR_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["last_updated"] = datetime.now().isoformat()
    SELECTOR_STATE_FILE.write_text(json.dumps(state, indent=2))


def decompose_task(task: str, strategy: str = "auto"):
    """Break genesis into parallelizable sub-agent prompts."""
    if strategy == "auto":
        rec = _recommend_strategy(task)
        strategy = rec["strategy"]
    else:
        rec = {"strategy": strategy, "children": 1, "profile": _classify_task(task),
               "parallel": strategy in ("parallel", "ablation"), "script": "genesis.sh"}

    task_type = rec["profile"]
    atoms = select_atoms(task_type)
    included_atoms = [a for a, v in atoms.items() if v["include"]]

    print(f"=== GENESIS DECOMPOSITION ===")
    print(f"Strategy: {strategy.upper()}")
    print(f"Atoms: {len(included_atoms)}/{len(atoms)}\n")

    if strategy == "lean":
        print("--- Phase 1: Foreign Genesis (single step) ---")
        print(f"  bash tools/genesis_foreign.sh /path/to/target \"{task[:30]}\"")
        print(f"  # Creates 7 files, ~500 lines")
        print(f"\n--- Phase 2: Run Session ---")
        prompt = _generate_foreign_prompt(task)
        print(f"  Sub-agent prompt ({len(prompt)} chars):")
        print(f"  {prompt[:200]}...")
        return

    if strategy == "mono":
        child_name = f"genesis-{_current_session()}-{task_type}"
        print(f"--- Phase 1: Spawn ({child_name}) ---")
        print(f"  python3 tools/evolve.py init {child_name} \"{task}\"")
        print(f"\n--- Phase 2: Run Sub-Agent ---")
        print(f"  python3 tools/agent_swarm.py prompt {child_name}")
        print(f"\n--- Phase 3: Harvest ---")
        print(f"  python3 tools/evolve.py harvest {child_name}")
        print(f"  python3 tools/evolve.py integrate {child_name} --dry-run")
        return

    if strategy == "parallel":
        n = rec.get("children", 3)
        dimensions = rec.get("dimensions", [f"dim-{i}" for i in range(n)])
        print(f"--- Phase 1: Parallel Spawn ({n} children) ---")
        print(f"  All spawns are independent — launch simultaneously.\n")

        children = []
        for i in range(n):
            dim = dimensions[i] if i < len(dimensions) else f"aspect-{i}"
            child_name = f"genesis-{_current_session()}-{dim}"
            children.append(child_name)
            sub_task = f"{task} — focus on {dim}"
            print(f"  Child {i+1}: {child_name}")
            print(f"    python3 tools/evolve.py init {child_name} \"{sub_task}\"")
            print()

        print(f"--- Phase 2: Parallel Sub-Agents ({n} concurrent) ---")
        for child in children:
            print(f"  Agent tool: python3 tools/agent_swarm.py prompt {child}")

        print(f"\n--- Phase 3: Parallel Harvest ---")
        for child in children:
            print(f"  python3 tools/evolve.py harvest {child}")
        print(f"\n--- Phase 4: Compare + Integrate ---")
        print(f"  python3 tools/evolve.py compare {' '.join(children)}")
        return

    if strategy == "ablation":
        # Control + N variants, each removing one atom
        removable = [a for a, v in atoms.items() if v["removable"] and v["include"]]
        # Pick top 2 ablation candidates (lowest weight among included)
        candidates = sorted(removable, key=lambda a: atoms[a]["weight"])[:2]

        print(f"--- Phase 1: Ablation Spawn (1 control + {len(candidates)} variants) ---\n")
        children = []

        # Control
        control_name = f"ablation-{_current_session()}-control"
        children.append(control_name)
        print(f"  Control: {control_name}")
        print(f"    python3 tools/evolve.py init {control_name} \"{task}\"")
        print()

        # Variants
        for atom in candidates:
            variant_name = f"ablation-{_current_session()}-no-{atom}"
            children.append(variant_name)
            print(f"  Variant (remove {atom}): {variant_name}")
            print(f"    # Remove atom:{atom} from genesis template before spawning")
            print(f"    python3 tools/evolve.py init {variant_name} \"{task}\"")
            print()

        print(f"--- Phase 2: Run All (parallel) ---")
        print(f"  Each child runs 3 sessions (viability gate)\n")

        print(f"--- Phase 3: Compare ---")
        print(f"  python3 tools/evolve.py compare {' '.join(children)}")
        print(f"\n--- Phase 4: Selector Feedback ---")
        print(f"  python3 tools/genesis_subtask.py selector-feedback --apply")
        return


def _generate_foreign_prompt(task: str) -> str:
    """Generate a sub-agent prompt for foreign genesis."""
    return (
        f"You are bootstrapping a swarm protocol onto a foreign repository.\n"
        f"Task: {task}\n\n"
        f"Steps:\n"
        f"1. Run: bash tools/genesis_foreign.sh /path/to/repo\n"
        f"2. Orient: read README, understand project structure\n"
        f"3. Populate beliefs/CORE.md with project context\n"
        f"4. Identify 3-5 open questions → tasks/FRONTIER.md\n"
        f"5. Write first lesson about what you found\n"
        f"6. Commit: [S1] genesis: swarm bootstrap\n"
    )


def batch_spawn(config_path: str):
    """Generate parallel spawn configs from a JSON config file."""
    config = json.loads(Path(config_path).read_text())

    children = config.get("children", [])
    if not children:
        print("ERROR: config must have a 'children' array")
        sys.exit(1)

    session = _current_session()
    print(f"=== BATCH SPAWN: {len(children)} children ===\n")

    prompts = []
    for i, child_cfg in enumerate(children):
        name = child_cfg.get("name", f"batch-{session}-{i}")
        task = child_cfg.get("task", "general research")
        personality = child_cfg.get("personality")
        task_type = child_cfg.get("type", _classify_task(task))

        atoms = select_atoms(task_type)
        included = sum(1 for v in atoms.values() if v["include"])

        print(f"Child {i+1}: {name}")
        print(f"  Task: {task[:60]}")
        print(f"  Type: {task_type}")
        print(f"  Atoms: {included}/{len(atoms)}")
        if personality:
            print(f"  Personality: {personality}")

        # Generate spawn command
        cmd = f"python3 tools/evolve.py init {name} \"{task}\""
        if personality:
            cmd += f" --personality {personality}"
        print(f"  Spawn: {cmd}")

        prompts.append({
            "name": name,
            "task": task,
            "spawn_cmd": cmd,
            "prompt_cmd": f"python3 tools/agent_swarm.py prompt {name}",
            "harvest_cmd": f"python3 tools/evolve.py harvest {name}",
        })
        print()

    # Write batch plan
    plan_path = REPO_ROOT / "workspace" / f"batch-spawn-{session}.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps({
        "session": f"S{session}",
        "created": datetime.now().isoformat(),
        "children": prompts,
        "harvest_all": f"python3 tools/genesis_subtask.py batch-harvest",
    }, indent=2))
    print(f"Batch plan written: {plan_path}")
    print(f"\nTo harvest all: python3 tools/genesis_subtask.py batch-harvest")


def batch_harvest(integrate: bool = False):
    """Parallel harvest + compare all children."""
    if not CHILDREN_DIR.exists():
        print("No children directory.")
        return

    children = sorted([d for d in CHILDREN_DIR.iterdir() if d.is_dir()], key=lambda d: d.name)
    if not children:
        print("No child swarms found.")
        return

    swarm_test = REPO_ROOT / "tools" / "swarm_test.py"

    print(f"=== BATCH HARVEST: {len(children)} children ===\n")
    print(f"{'Name':<30} {'Viability':<12} {'Lessons':<10} {'Status'}")
    print("-" * 65)

    results = []
    for child in children:
        r = subprocess.run(
            [PYTHON_CMD, str(swarm_test), "evaluate", str(child)],
            capture_output=True, text=True
        )
        viability = "?"
        vm = re.search(r"Viability: (\d+)/4", r.stdout)
        score = int(vm.group(1)) if vm else 0
        viability = f"{score}/4"

        lessons = 0
        lessons_dir = child / "memory" / "lessons"
        if lessons_dir.exists():
            lessons = len(list(lessons_dir.glob("L-*.md")))

        status = "VIABLE" if score >= 3 else "DEVELOPING" if score >= 1 else "INERT"

        results.append({
            "name": child.name,
            "viability": viability,
            "score": score,
            "lessons": lessons,
            "status": status,
        })
        print(f"{child.name:<30} {viability:<12} {lessons:<10} {status}")

    if not results:
        return

    # Summary
    viable = [r for r in results if r["score"] >= 3]
    total_lessons = sum(r["lessons"] for r in results)
    print(f"\n--- Summary ---")
    print(f"  Viable: {len(viable)}/{len(results)}")
    print(f"  Total lessons: {total_lessons}")
    print(f"  Best: {max(results, key=lambda r: (r['score'], r['lessons']))['name']}")

    if integrate and viable:
        print(f"\n--- Integration ---")
        for r in viable:
            print(f"  Integrating {r['name']}...")
            subprocess.run(
                [PYTHON_CMD, str(REPO_ROOT / "tools" / "evolve.py"), "integrate", r["name"]],
                capture_output=True, text=True
            )
        print(f"  Integrated {len(viable)} children")

    # Feed back to selector
    print(f"\nTo update selector: python3 tools/genesis_subtask.py selector-feedback")


def selector_feedback(apply: bool = False):
    """Close the selection loop: read child outcomes, update atom weights.

    This is the P1 priority from L-497 (genesis_selector.py).
    Reads integration logs + child viability to compute per-atom success rates.
    When --apply is used, writes updated weights to selector state.
    """
    state = _load_selector_state()

    print(f"=== SELECTOR FEEDBACK (Generation {state.get('generation', 0)}) ===\n")

    # Collect child data
    if not CHILDREN_DIR.exists():
        print("No children to analyze.")
        return

    children = sorted([d for d in CHILDREN_DIR.iterdir() if d.is_dir()])
    if not children:
        print("No child swarms found.")
        return

    # For each child, determine which atoms were present and viability
    atom_trials = {atom: {"present": 0, "absent": 0, "viable_present": 0, "viable_absent": 0}
                   for atom in ATOM_WEIGHTS}

    swarm_test = REPO_ROOT / "tools" / "swarm_test.py"
    child_data = []

    for child in children:
        # Evaluate viability
        r = subprocess.run(
            [PYTHON_CMD, str(swarm_test), "evaluate", str(child)],
            capture_output=True, text=True
        )
        vm = re.search(r"Viability: (\d+)/4", r.stdout)
        score = int(vm.group(1)) if vm else 0
        viable = score >= 3

        # Determine which atoms are present in child
        present_atoms = set()
        if (child / "beliefs" / "CORE.md").exists():
            present_atoms.add("core-beliefs")
        if (child / "tools" / "validate_beliefs.py").exists():
            present_atoms.add("validator")
        if (child / "CLAUDE.md").exists():
            present_atoms.add("session-protocol")
        if (child / "memory" / "INDEX.md").exists():
            present_atoms.add("memory-index")
        if (child / "tasks" / "FRONTIER.md").exists():
            present_atoms.add("frontier")
        if (child / "memory" / "lessons" / "TEMPLATE.md").exists():
            present_atoms.add("lesson-template")
        if (child / "tasks" / "NEXT.md").exists():
            present_atoms.add("next-handoff")
        if (child / "memory" / "DISTILL.md").exists():
            present_atoms.add("distill-protocol")
        if (child / "beliefs" / "DEPS.md").exists():
            present_atoms.add("belief-tracking")
        if (child / "beliefs" / "CONFLICTS.md").exists():
            present_atoms.add("conflict-protocol")
        if (child / "memory" / "VERIFY.md").exists():
            present_atoms.add("verify-protocol")
        if (child / "memory" / "PRINCIPLES.md").exists():
            present_atoms.add("principles-inherit")
        modes_dir = child / "modes"
        if modes_dir.exists() and any(modes_dir.glob("*.md")):
            present_atoms.add("session-modes")
        if (child / "tools" / "pre-commit.hook").exists():
            present_atoms.add("pre-commit-hook")
        if (child / "tasks" / "TASK-001.md").exists():
            present_atoms.add("first-task")
        if (child / "workspace" / "genesis.sh").exists():
            present_atoms.add("self-swarm-tooling")
        bulletin_dir = child / "experiments" / "inter-swarm" / "bulletins"
        if bulletin_dir.exists() and any(bulletin_dir.glob("*.md")):
            present_atoms.add("sibling-bulletins")

        child_data.append({
            "name": child.name,
            "score": score,
            "viable": viable,
            "atoms_present": sorted(present_atoms),
        })

        # Update atom trial counts
        for atom in ATOM_WEIGHTS:
            if atom in present_atoms:
                atom_trials[atom]["present"] += 1
                if viable:
                    atom_trials[atom]["viable_present"] += 1
            else:
                atom_trials[atom]["absent"] += 1
                if viable:
                    atom_trials[atom]["viable_absent"] += 1

    # Compute success rates
    print(f"Children analyzed: {len(children)}")
    viable_count = sum(1 for c in child_data if c["viable"])
    print(f"Viable: {viable_count}/{len(children)}")
    print()

    print(f"{'Atom':<25} {'Present':<10} {'Viable/Present':<16} {'Absent':<10} {'Viable/Absent':<16} {'Signal'}")
    print("-" * 90)

    atom_success = {}
    for atom, trials in sorted(atom_trials.items()):
        p = trials["present"]
        vp = trials["viable_present"]
        a = trials["absent"]
        va = trials["viable_absent"]

        rate_present = vp / p if p > 0 else 0
        rate_absent = va / a if a > 0 else 0

        # Signal: does presence correlate with viability?
        if p > 0 and a > 0:
            signal = rate_present - rate_absent
            signal_str = f"{signal:+.2f}"
        elif p > 0:
            signal = rate_present
            signal_str = f"{rate_present:.2f} (no absence data)"
        else:
            signal = 0
            signal_str = "no data"

        atom_success[atom] = round(max(0.1, min(1.0, 0.5 + signal)), 2)
        print(f"{atom:<25} {p:<10} {vp}/{p:<14} {a:<10} {va}/{a:<14} {signal_str}")

    # Proposals
    print(f"\n--- Selector Proposals ---")
    proposals = []
    for atom, trials in atom_trials.items():
        info = ATOM_WEIGHTS[atom]
        if not info["removable"]:
            continue

        p, a = trials["present"], trials["absent"]
        vp, va = trials["viable_present"], trials["viable_absent"]

        # Proposal: remove atoms that don't help viability
        if a >= 2 and p >= 2:
            rate_p = vp / p
            rate_a = va / a
            if rate_a >= rate_p:
                proposals.append({
                    "atom": atom,
                    "action": "REMOVE",
                    "reason": f"Absence viable rate ({rate_a:.0%}) >= presence rate ({rate_p:.0%})",
                    "confidence": "HIGH" if (a >= 3 and p >= 3) else "MEDIUM",
                })
        elif p >= 3 and vp / p < 0.5:
            proposals.append({
                "atom": atom,
                "action": "INVESTIGATE",
                "reason": f"Present in {p} children but only {vp} viable ({vp/p:.0%})",
                "confidence": "LOW",
            })

    if proposals:
        for prop in proposals:
            print(f"  [{prop['confidence']}] {prop['action']} {prop['atom']}: {prop['reason']}")
    else:
        print("  No proposals — insufficient data or all atoms contributing positively.")
        print(f"  (Need ≥2 children with atom absent to compute removal safety)")

    if apply:
        state["atom_success_rates"] = atom_success
        state["generation"] = state.get("generation", 0) + 1
        state["children_analyzed"] = len(children)
        state["viable_count"] = viable_count
        state["proposals"] = proposals
        _save_selector_state(state)
        print(f"\nSelector state updated (generation {state['generation']})")
        print(f"  Written to: {SELECTOR_STATE_FILE}")
    else:
        print(f"\nDry run. Use --apply to update selector state.")


def print_select(task_type: str, ablation_atom: str = None):
    """Print atom selection for a task type."""
    atoms = select_atoms(task_type, ablation_atom)

    print(f"=== ATOM SELECTION: {task_type} ===")
    if ablation_atom:
        print(f"  Ablation: removing {ablation_atom}")
    print()

    included = []
    excluded = []
    for atom, info in sorted(atoms.items(), key=lambda x: -x[1]["weight"]):
        if info["include"]:
            included.append((atom, info))
        else:
            excluded.append((atom, info))

    print(f"INCLUDED ({len(included)}):")
    for atom, info in included:
        lock = " [LOCKED]" if not info["removable"] else ""
        print(f"  {atom:<25} w={info['weight']:.2f}{lock}  ({info['evidence']})")

    if excluded:
        print(f"\nEXCLUDED ({len(excluded)}):")
        for atom, info in excluded:
            print(f"  {atom:<25} w={info['weight']:.2f}  ({info['evidence']})")

    print(f"\nTemplate compression: {len(excluded)}/{len(atoms)} atoms removed "
          f"(~{len(excluded) * 30}L lighter)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "profile":
        if len(sys.argv) < 3:
            print("Usage: genesis_subtask.py profile <task-description>")
            sys.exit(1)
        profile_task(" ".join(sys.argv[2:]))

    elif cmd == "select":
        task_type = "research"
        ablation_atom = None
        for arg in sys.argv[2:]:
            if arg.startswith("--task="):
                task_type = arg.split("=", 1)[1]
            elif arg.startswith("--ablation="):
                ablation_atom = arg.split("=", 1)[1]
            elif arg == "--ablation":
                ablation_atom = "session-modes"  # default ablation target
        print_select(task_type, ablation_atom)

    elif cmd == "decompose":
        if len(sys.argv) < 3:
            print("Usage: genesis_subtask.py decompose <task-description> [--strategy=auto]")
            sys.exit(1)
        strategy = "auto"
        args = []
        for arg in sys.argv[2:]:
            if arg.startswith("--strategy="):
                strategy = arg.split("=", 1)[1]
            else:
                args.append(arg)
        decompose_task(" ".join(args), strategy)

    elif cmd == "batch-spawn":
        if len(sys.argv) < 3:
            print("Usage: genesis_subtask.py batch-spawn <config.json>")
            sys.exit(1)
        batch_spawn(sys.argv[2])

    elif cmd == "batch-harvest":
        integrate = "--integrate" in sys.argv
        batch_harvest(integrate)

    elif cmd == "selector-feedback":
        apply = "--apply" in sys.argv
        selector_feedback(apply)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
