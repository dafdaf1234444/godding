#!/usr/bin/env python3
"""
colony.py — Spawn and evaluate multiple child swarms as a colony.

Usage:
    python3 tools/colony.py list
    python3 tools/colony.py run <experiment-name>
    python3 tools/colony.py status <experiment-name>
    python3 tools/colony.py compare <experiment-name>
    python3 tools/colony.py swarm <experiment-name>
    python3 tools/colony.py swarm-all

A colony experiment spawns N child swarms with variations, runs
sessions on each, then compares outcomes to identify which
architectural choices produce the most viable offspring.

This is genetic-algorithm-like: the "genome" is the genesis template,
"fitness" is swarm_test viability score, and "selection" is parent
integration of winning strategies.

Experiment configs are stored in experiments/colonies/<name>.json
Children may include optional fields such as "topic" and "personality".
"""

import json
import hashlib
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COLONIES_DIR = REPO_ROOT / "experiments" / "colonies"
CHILDREN_DIR = REPO_ROOT / "experiments" / "children"
PYTHON_BIN = sys.executable or "python3"


def is_colony_config(config: dict) -> bool:
    """Return True when config looks like a runnable colony experiment."""
    children = config.get("children")
    if not isinstance(children, list) or not children:
        return False
    return all(
        isinstance(child, dict)
        and isinstance(child.get("name"), str)
        and child["name"]
        for child in children
    )


def discover_experiments() -> tuple[list[str], list[str]]:
    """Return (valid, skipped) experiment names from experiments/colonies."""
    if not COLONIES_DIR.exists():
        return [], []

    valid: list[str] = []
    skipped: list[str] = []
    for config_path in sorted(COLONIES_DIR.glob("*.json")):
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            skipped.append(config_path.stem)
            continue

        if is_colony_config(config):
            valid.append(config_path.stem)
        else:
            skipped.append(config_path.stem)

    return valid, skipped


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_command_constraints() -> dict[str, bool]:
    return {name: bool(shutil.which(name)) for name in ("python3", "python", "git", "bash")}


def _compact_capabilities(capabilities: dict) -> dict[str, dict[str, int]]:
    compact: dict[str, dict[str, int]] = {}
    if not isinstance(capabilities, dict):
        return compact
    for name, info in capabilities.items():
        if not isinstance(name, str) or not isinstance(info, dict):
            continue
        present = info.get("present")
        total = info.get("total")
        if isinstance(present, int) and isinstance(total, int):
            compact[name] = {"present": present, "total": total}
    return compact


def _inventory_constraints(inventory: dict, captured_at_utc: str) -> dict:
    host = inventory.get("host", {}) if isinstance(inventory, dict) else {}
    commands = dict(_default_command_constraints())
    host_commands = host.get("commands", {}) if isinstance(host, dict) else {}
    if isinstance(host_commands, dict):
        for name, ok in host_commands.items():
            if isinstance(name, str):
                commands[name] = bool(ok)

    missing_bridges = []
    bridges = inventory.get("bridges", []) if isinstance(inventory, dict) else []
    for item in bridges:
        if isinstance(item, dict) and isinstance(item.get("path"), str) and not item.get("exists", False):
            missing_bridges.append(item["path"])

    missing_core = []
    core_state = inventory.get("core_state", []) if isinstance(inventory, dict) else []
    for item in core_state:
        if isinstance(item, dict) and isinstance(item.get("path"), str) and not item.get("exists", False):
            missing_core.append(item["path"])
    capabilities = _compact_capabilities(inventory.get("capabilities", {}) if isinstance(inventory, dict) else {})

    inter_swarm_ready = False
    inter_swarm_missing: list[str] = []
    inter_swarm_connectivity = inventory.get("inter_swarm_connectivity", {}) if isinstance(inventory, dict) else {}
    if isinstance(inter_swarm_connectivity, dict) and inter_swarm_connectivity:
        inter_swarm_ready = bool(inter_swarm_connectivity.get("ready"))
        missing = inter_swarm_connectivity.get("missing", [])
        if isinstance(missing, list):
            inter_swarm_missing = sorted(str(item) for item in missing if str(item).strip())
    else:
        inter_swarm = capabilities.get("inter_swarm", {})
        present = inter_swarm.get("present", 0) if isinstance(inter_swarm, dict) else 0
        total = inter_swarm.get("total", 0) if isinstance(inter_swarm, dict) else 0
        if isinstance(present, int) and isinstance(total, int):
            inter_swarm_ready = total > 0 and present >= total
            if not inter_swarm_ready:
                inter_swarm_missing = [f"inter_swarm_tools:{present}/{total}"]

    return {
        "source": "maintenance_inventory",
        "captured_at_utc": captured_at_utc,
        "platform": host.get("platform", platform.platform()) if isinstance(host, dict) else platform.platform(),
        "python_executable": host.get("python_executable", PYTHON_BIN) if isinstance(host, dict) else PYTHON_BIN,
        "python_command_hint": host.get("python_command_hint", PYTHON_BIN) if isinstance(host, dict) else PYTHON_BIN,
        "commands": commands,
        "capabilities": capabilities,
        "missing_bridges": sorted(missing_bridges),
        "missing_core_state": sorted(missing_core),
        "inter_swarm_connectivity_ready": inter_swarm_ready,
        "inter_swarm_missing": inter_swarm_missing,
    }


def capture_environment_constraints() -> dict:
    captured_at_utc = _utc_now()
    fallback = {
        "source": "fallback",
        "captured_at_utc": captured_at_utc,
        "platform": platform.platform(),
        "python_executable": PYTHON_BIN,
        "python_command_hint": PYTHON_BIN,
        "commands": _default_command_constraints(),
        "capabilities": {},
        "missing_bridges": [],
        "missing_core_state": [],
        "inter_swarm_connectivity_ready": False,
        "inter_swarm_missing": ["inventory-unavailable"],
    }

    maintenance = REPO_ROOT / "tools" / "maintenance.py"
    if not maintenance.exists():
        return fallback

    try:
        r = subprocess.run(
            [PYTHON_BIN, str(maintenance), "--inventory", "--json"],
            capture_output=True, text=True, timeout=20
        )
    except Exception:
        return fallback

    if r.returncode != 0:
        return fallback

    try:
        inventory = json.loads(r.stdout)
    except json.JSONDecodeError:
        return fallback

    return _inventory_constraints(inventory, captured_at_utc)


def environment_signature(constraints: dict) -> str:
    stable_payload = {
        "platform": constraints.get("platform"),
        "python_command_hint": constraints.get("python_command_hint"),
        "commands": constraints.get("commands", {}),
        "capabilities": constraints.get("capabilities", {}),
        "missing_bridges": constraints.get("missing_bridges", []),
        "missing_core_state": constraints.get("missing_core_state", []),
        "inter_swarm_connectivity_ready": constraints.get("inter_swarm_connectivity_ready", False),
        "inter_swarm_missing": constraints.get("inter_swarm_missing", []),
    }
    blob = json.dumps(stable_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def _print_constraints_summary(constraints: dict, signature: str):
    print(f"Environment constraints: {signature}")
    commands = constraints.get("commands", {})
    if isinstance(commands, dict):
        missing_cmds = sorted(name for name, ok in commands.items() if not ok)
        if missing_cmds:
            print(f"  Missing commands: {', '.join(missing_cmds)}")
    capabilities = constraints.get("capabilities", {})
    if isinstance(capabilities, dict):
        constrained = [
            name for name, info in capabilities.items()
            if isinstance(info, dict)
            and isinstance(info.get("present"), int)
            and isinstance(info.get("total"), int)
            and info["present"] < info["total"]
        ]
        if constrained:
            print(f"  Partial capability sets: {', '.join(sorted(constrained))}")
    if constraints.get("inter_swarm_connectivity_ready"):
        print("  Inter-swarm connectivity: READY")
    else:
        missing = constraints.get("inter_swarm_missing", [])
        if isinstance(missing, list) and missing:
            print(f"  Inter-swarm connectivity: NOT READY ({', '.join(missing[:3])})")
        else:
            print("  Inter-swarm connectivity: NOT READY")


def list_experiments():
    """List runnable colony experiments and non-colony JSON files."""
    valid, skipped = discover_experiments()
    print("=== Colony Experiments ===")
    if valid:
        for name in valid:
            config_path = COLONIES_DIR / f"{name}.json"
            config = json.loads(config_path.read_text())
            children = len(config.get("children", []))
            status = config.get("status", "unknown")
            print(f"  {name:<32} children={children:<3} status={status}")
    else:
        print("  No runnable colony experiments found.")

    if skipped:
        sample = ", ".join(skipped[:5])
        extra = "" if len(skipped) <= 5 else f" (+{len(skipped) - 5} more)"
        print(f"\nSkipped non-colony JSON files: {sample}{extra}")


def create_experiment(name: str, config: dict) -> Path:
    """Create a colony experiment config."""
    COLONIES_DIR.mkdir(parents=True, exist_ok=True)
    config_path = COLONIES_DIR / f"{name}.json"
    config_path.write_text(json.dumps(config, indent=2))
    return config_path


def run_experiment(name: str) -> bool:
    """Run a colony experiment: spawn children, run sessions, evaluate."""
    config_path = COLONIES_DIR / f"{name}.json"
    if not config_path.exists():
        print(f"No experiment config at {config_path}")
        print("Creating default experiment...")
        config = {
            "name": name,
            "children": [
                {"name": f"{name}-baseline", "topic": "baseline"},
                {"name": f"{name}-minimal", "topic": "minimal-structure-test"},
            ],
            "sessions_per_child": 1,
            "status": "created",
        }
        create_experiment(name, config)
        print(f"Config created at {config_path}")
        print("Edit the config, then run again.")
        return False

    config = json.loads(config_path.read_text())
    if not is_colony_config(config):
        print(f"Config '{name}' is not a runnable colony experiment (missing/invalid children[]).")
        return False

    if config.get("status") == "completed":
        print(f"Experiment '{name}' already completed. Use 'compare' to see results.")
        return True

    # Spawn children
    print(f"=== Colony Experiment: {name} ===")
    print(f"Children: {len(config['children'])}")
    run_constraints = capture_environment_constraints()
    run_signature = environment_signature(run_constraints)
    _print_constraints_summary(run_constraints, run_signature)
    print()

    swarm_test = REPO_ROOT / "tools" / "swarm_test.py"
    results = []

    for child_config in config["children"]:
        child_name = child_config["name"]
        child_topic = child_config.get("topic", "general")
        child_personality = child_config.get("personality")
        child_dir = CHILDREN_DIR / child_name

        personality_note = f", personality: {child_personality}" if child_personality else ""
        print(f"--- Spawning: {child_name} (topic: {child_topic}{personality_note}) ---")

        # Spawn
        spawn_cmd = [PYTHON_BIN, str(swarm_test), "spawn", child_name, child_topic]
        if child_personality:
            spawn_cmd.extend(["--personality", child_personality])
        r = subprocess.run(spawn_cmd, capture_output=True, text=True)
        if r.returncode != 0:
            # Re-running experiments is common; reuse already spawned children.
            if child_dir.exists():
                print("  Child already exists; reusing current state")
                status = "existing"
            else:
                error = (r.stderr or r.stdout).strip() or "unknown error"
                print(f"  Spawn failed: {error}")
                results.append({
                    "name": child_name,
                    "topic": child_topic,
                    "personality": child_personality,
                    "status": "spawn_failed",
                    "error": error,
                    "environment_signature": run_signature,
                })
                continue
        else:
            print("  Spawned successfully")
            status = "spawned"

        # Evaluate current child state.
        r = subprocess.run(
            [PYTHON_BIN, str(swarm_test), "evaluate", str(child_dir)],
            capture_output=True, text=True
        )
        print(f"  Pre-session evaluation:\n{r.stdout}")

        results.append({
            "name": child_name,
            "topic": child_topic,
            "personality": child_personality,
            "status": status,
            "path": str(child_dir),
            "environment_signature": run_signature,
        })

    # Save results
    has_viable_children = any(r.get("status") in {"spawned", "existing"} for r in results)
    config["status"] = "spawned" if has_viable_children else "spawn_failed"
    config["environment_constraints"] = run_constraints
    config["environment_signature"] = run_signature
    config["results"] = results
    config_path.write_text(json.dumps(config, indent=2))

    active = sum(1 for r in results if r.get("status") in {"spawned", "existing"})
    failed = sum(1 for r in results if r.get("status") == "spawn_failed")
    print(f"\nChildren active: {active} | spawn failures: {failed}")
    print(f"Next: Run sessions on each child, then use 'compare' to evaluate.")
    return has_viable_children


def compare_experiment(name: str):
    """Compare children in a colony experiment."""
    config_path = COLONIES_DIR / f"{name}.json"
    if not config_path.exists():
        print(f"No experiment at {config_path}")
        sys.exit(1)

    config = json.loads(config_path.read_text())
    if not is_colony_config(config):
        print(f"Config '{name}' is not a runnable colony experiment (missing/invalid children[]).")
        return

    print(f"=== Colony Comparison: {name} ===\n")
    recorded_constraints = config.get("environment_constraints", {})
    recorded_signature = config.get("environment_signature")
    if not recorded_signature and isinstance(recorded_constraints, dict) and recorded_constraints:
        recorded_signature = environment_signature(recorded_constraints)

    current_constraints = capture_environment_constraints()
    current_signature = environment_signature(current_constraints)
    if recorded_signature:
        print(f"Recorded run constraints: {recorded_signature}")
    print(f"Current compare constraints: {current_signature}")
    if recorded_signature and recorded_signature != current_signature:
        print("NOTE: environment constraints changed since run; compare outcomes may include runtime effects.")
    child_signatures = sorted({
        child.get("environment_signature")
        for child in config.get("results", [])
        if isinstance(child, dict) and child.get("environment_signature")
    })
    if len(child_signatures) > 1:
        print(f"Mixed child environments: {', '.join(child_signatures)}")
    print()

    swarm_test = REPO_ROOT / "tools" / "swarm_test.py"
    merge_back = REPO_ROOT / "tools" / "merge_back.py"

    evaluations = []
    for child_config in config.get("results", config.get("children", [])):
        child_name = child_config.get("name", "unknown")
        child_dir = CHILDREN_DIR / child_name

        if not child_dir.exists():
            print(f"  {child_name}: NOT FOUND")
            continue

        # Evaluate
        r = subprocess.run(
            [PYTHON_BIN, str(swarm_test), "evaluate", str(child_dir)],
            capture_output=True, text=True
        )

        # Extract viability score from output
        viability_m = None
        for line in r.stdout.splitlines():
            if "Viability:" in line:
                viability_m = line.strip()
                break

        evaluations.append({
            "name": child_name,
            "viability": viability_m or "unknown",
            "output": r.stdout,
        })

    # Print comparison table
    print(f"{'Child':<30} {'Viability':<30}")
    print("-" * 60)
    for e in evaluations:
        print(f"{e['name']:<30} {e['viability']:<30}")

    # Find winner
    if evaluations:
        # Sort by viability score (extract number)
        def extract_score(e):
            import re
            m = re.search(r"(\d+)/4", e["viability"])
            return int(m.group(1)) if m else 0

        evaluations.sort(key=extract_score, reverse=True)
        winner = evaluations[0]
        print(f"\nMost viable: {winner['name']} ({winner['viability']})")

        # Generate merge-back report for winner
        winner_dir = CHILDREN_DIR / winner["name"]
        r = subprocess.run(
            [PYTHON_BIN, str(merge_back), str(winner_dir)],
            capture_output=True, text=True
        )
        if r.stdout:
            print(f"\n--- Merge-back report for {winner['name']} ---")
            print(r.stdout)


def swarm_experiment(name: str):
    """Run + compare one colony experiment."""
    print(f"=== Swarming colony: {name} ===")
    if run_experiment(name):
        print()
        compare_experiment(name)


def swarm_all_experiments():
    """Run + compare every runnable colony experiment."""
    valid, skipped = discover_experiments()
    if not valid:
        print("No runnable colony experiments found.")
        if skipped:
            print(f"Found non-colony JSON files: {', '.join(skipped[:5])}")
        return

    for i, name in enumerate(valid):
        if i > 0:
            print("\n" + "=" * 72 + "\n")
        swarm_experiment(name)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        list_experiments()
    elif cmd == "swarm-all":
        swarm_all_experiments()
    elif cmd in {"run", "status", "compare", "swarm"}:
        if len(sys.argv) < 3:
            print(__doc__)
            sys.exit(1)
        name = sys.argv[2]
        if cmd == "run":
            run_experiment(name)
        elif cmd == "compare":
            compare_experiment(name)
        elif cmd == "swarm":
            swarm_experiment(name)
        else:
            config_path = COLONIES_DIR / f"{name}.json"
            if config_path.exists():
                print(json.dumps(json.loads(config_path.read_text()), indent=2))
            else:
                print(f"No experiment at {config_path}")
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
