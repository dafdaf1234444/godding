#!/usr/bin/env python3
"""Inventory and portability maintenance checks extracted from maintenance.py (DOMEX-META-S420).

Contains: build_inventory, print_inventory, check_runtime_portability, check_commit_hooks.
These functions enumerate swarm capabilities, bridge files, command availability,
inter-swarm connectivity, and runtime/hook health.
"""

import platform
import re
from pathlib import Path


def build_inventory(
    REPO_ROOT: Path,
    PYTHON_EXE: str,
    PYTHON_CMD: str,
    BRIDGE_FILES: list[str],
    _exists,
    _python_command_runs,
    _py_launcher_runs,
    _command_runs,
    _command_exists,
    _inter_swarm_connectivity,
) -> dict:
    T = lambda *ns: [f"tools/{n}" for n in ns]
    cap_sets: dict[str, list[str]] = {
        "orientation": T("maintenance.py", "orient.py", "sync_state.py", "pulse.py", "context_router.py", "substrate_detect.py"),
        "validation": T("validate_beliefs.py", "check.sh", "check.ps1", "maintenance.sh", "maintenance.ps1", "install-hooks.sh", "repair.py", "pre-commit.hook", "commit-msg.hook"),
        "evolution": T("evolve.py", "swarm_test.py", "agent_swarm.py", "colony.py", "swarm_colony.py", "spawn_coordinator.py"),
        "collaboration": T("swarm_pr.py"),
        "inter_swarm": T("bulletin.py", "merge_back.py", "propagate_challenges.py", "close_lane.py"),
        "compaction": T("compact.py", "proxy_k.py", "frontier_decay.py"),
        "analysis": T("nk_analyze.py", "nk_analyze_go.py", "dream.py", "change_quality.py", "task_recognizer.py"),
        "benchmarks": T("f92_benchmark.py", "f92_real_coop_benchmark.py", "spawn_quality.py", "p155_live_trace.py"),
        "support": T("swarm_parse.py", "novelty.py", "validate_beliefs_extras.py"),
    }
    commands = {"python3": _python_command_runs("python3"), "python": _python_command_runs("python"),
                "git": _command_runs("git", ["--version"]), "bash": _command_runs("bash", ["--version"])}
    if platform.system().lower().startswith("windows") or _command_exists("pwsh"):
        commands["pwsh"] = _command_runs("pwsh", ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.Major"], timeout=8)
    elif _command_exists("powershell"):
        commands["powershell"] = _command_runs("powershell", ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.Major"], timeout=8)
    if platform.system().lower().startswith("windows") or _command_exists("py"):
        commands["py -3"] = _py_launcher_runs()
    capabilities = {name: {"present": sum(1 for p in files if _exists(p)), "total": len(files), "files": files}
                    for name, files in cap_sets.items()}
    return {
        "host": {"platform": platform.platform(), "python_executable": PYTHON_EXE, "python_command_hint": PYTHON_CMD, "commands": commands},
        "bridges": [{"path": p, "exists": _exists(p)} for p in BRIDGE_FILES],
        "core_state": [{"path": p, "exists": _exists(p)} for p in ("beliefs/CORE.md", "memory/INDEX.md", "tasks/FRONTIER.md", "tasks/NEXT.md", "memory/PRINCIPLES.md")],
        "capabilities": capabilities,
        "inter_swarm_connectivity": _inter_swarm_connectivity(capabilities, commands),
    }


def print_inventory(inv: dict):
    _ok = lambda v: "OK " if v else "NO "
    host = inv["host"]
    print(f"=== SWARM INVENTORY ===\nHost: {host['platform']}\nPython: {host['python_executable']}  hint: {host['python_command_hint']}\n")
    print("Commands:")
    for name, ok in host["commands"].items():
        print(f"  {_ok(ok)}{name}")
    for section, key in (("Bridge files", "bridges"), ("Core state", "core_state")):
        print(f"\n{section}:")
        for item in inv[key]:
            print(f"  {_ok(item['exists'])}{item['path']}")
    print("\nCapabilities:")
    for name, info in inv["capabilities"].items():
        print(f"  {name:<12} {info['present']}/{info['total']}")
    inter_swarm = inv.get("inter_swarm_connectivity", {})
    if isinstance(inter_swarm, dict) and inter_swarm:
        tooling = inter_swarm.get("tooling", {}) if isinstance(inter_swarm.get("tooling"), dict) else {}
        status = "READY" if inter_swarm.get("ready") else "NOT READY"
        print(f"\nInter-swarm: {status} (tooling {tooling.get('present', '?')}/{tooling.get('total', '?')}, python {_ok(inter_swarm.get('python_command_ready'))})")
        missing = inter_swarm.get("missing", [])
        if isinstance(missing, list) and missing:
            print(f"  Missing: {', '.join(str(item) for item in missing)}")
    print()


def check_runtime_portability(
    REPO_ROOT: Path,
    PYTHON_CMD: str,
    BRIDGE_FILES: list[str],
    _exists,
    _read,
    _git,
    _command_exists,
    _python_command_runs,
    _py_launcher_runs,
    _is_wsl_mnt_repo,
) -> list[tuple[str, str]]:
    results = []
    has_git = _command_exists("git")
    has_bash = _command_exists("bash")
    has_pwsh = _command_exists("pwsh") or _command_exists("powershell")
    has_python_alias = _python_command_runs("python3") or _python_command_runs("python") or _py_launcher_runs()
    has_bash_wrapper_pair = _exists("tools/check.sh") and _exists("tools/maintenance.sh")
    has_ps_wrapper_pair = _exists("tools/check.ps1") and _exists("tools/maintenance.ps1")
    has_bash_wrappers = has_bash and has_bash_wrapper_pair
    has_pwsh_wrappers = has_pwsh and has_ps_wrapper_pair

    if not has_git:
        results.append(("URGENT", "git not found in PATH -- swarm memory/commit workflow cannot run"))
    if not has_python_alias:
        if has_bash_wrappers and has_pwsh_wrappers:
            results.append(("NOTICE", "No python alias in active shell; use wrappers (`bash tools/check.sh --quick` or `pwsh -NoProfile -File tools/check.ps1 --quick`)"))
        elif has_bash_wrappers:
            results.append(("NOTICE", "No python alias in active shell; use bash wrappers (`bash tools/check.sh --quick`, `bash tools/maintenance.sh --inventory`)"))
        else:
            results.append(("DUE", f"No python alias in PATH -- use explicit interpreter: {PYTHON_CMD}"))
    if not has_bash and (_exists("workspace/genesis.sh") or _exists("tools/check.sh")):
        if has_python_alias and has_pwsh_wrappers:
            results.append(("NOTICE", "bash not found -- use PowerShell wrappers (`pwsh -NoProfile -File tools/check.ps1 --quick`, `pwsh -NoProfile -File tools/maintenance.ps1 --inventory`)"))
        elif has_python_alias:
            results.append(("NOTICE", f"bash not found -- use direct python entrypoints (`{PYTHON_CMD} tools/maintenance.py --quick`, `{PYTHON_CMD} tools/maintenance.py --inventory`)"))
        else:
            results.append(("DUE", "bash not found and no python alias -- portable startup path is broken"))
    if has_bash and not _exists("tools/maintenance.sh"):
        results.append(("DUE", "tools/maintenance.sh missing -- portable maintenance/inventory path is broken"))
    if has_pwsh and not _exists("tools/maintenance.ps1"):
        results.append(("DUE" if not has_bash else "NOTICE", "tools/maintenance.ps1 missing -- PowerShell maintenance/inventory path is degraded"))

    if _is_wsl_mnt_repo():
        if not _git("status", "--porcelain"):
            results.append(("NOTICE", "WSL on /mnt/* repo: status/proxy-K may diverge from Windows runtime"))
        swarm_cmd = REPO_ROOT / ".claude" / "commands" / "swarm.md"
        if not swarm_cmd.exists():
            results.append(("DUE", ".claude/commands/swarm.md DELETED -- WSL deletion bug (L-279). Fix: rm -f .claude/commands/swarm.md && git checkout HEAD -- .claude/commands/swarm.md"))
        else:
            try:
                if "# /swarm" not in swarm_cmd.read_text(encoding="utf-8"):
                    results.append(("DUE", ".claude/commands/swarm.md exists but has unexpected content -- may be corrupted (WSL). Restore: python3 -c \"import os; os.remove('.claude/commands/swarm.md')\" then git show HEAD:.claude/commands/swarm.md > /tmp/s.md && python3 -c \"open('.claude/commands/swarm.md','w').write(open('/tmp/s.md').read())\""))
            except (PermissionError, OSError):
                results.append(("DUE", ".claude/commands/swarm.md inaccessible -- WSL permission corruption. Fix: python3 -c \"import os; os.remove('.claude/commands/swarm.md')\" then restore from git show HEAD:.claude/commands/swarm.md"))

    bridges = BRIDGE_FILES
    missing_bridges = [p for p in bridges if not _exists(p)]
    if missing_bridges:
        level = "URGENT" if "SWARM.md" in missing_bridges else "DUE"
        sample = ", ".join(missing_bridges[:3])
        results.append((level, f"{len(missing_bridges)} missing bridge file(s): {sample}"))

    swarm_ref_re = re.compile(r"\bswarm\.md\b", re.IGNORECASE)
    swarm_signal_re = re.compile(r"\bswarm signaling\b", re.IGNORECASE)
    min_swarmed_re = re.compile(r"Minimum Swarmed Cycle", re.IGNORECASE)
    no_ref, no_signal, no_min_swarmed = [], [], []
    for path in bridges:
        if path == "SWARM.md" or path in missing_bridges: continue
        content = _read(REPO_ROOT / path)
        if not swarm_ref_re.search(content): no_ref.append(path)
        if not swarm_signal_re.search(content): no_signal.append(path)
        if not min_swarmed_re.search(content): no_min_swarmed.append(path)
    if no_ref:
        results.append(("DUE", f"{len(no_ref)} bridge file(s) missing SWARM.md protocol reference: {', '.join(no_ref[:3])}"))
    if "SWARM.md" not in missing_bridges and not swarm_signal_re.search(_read(REPO_ROOT / "SWARM.md")):
        results.append(("DUE", "SWARM.md missing explicit swarm signaling rule"))
    if no_signal:
        results.append(("DUE", f"{len(no_signal)} bridge file(s) missing swarm signaling guidance: {', '.join(no_signal[:3])}"))
    if no_min_swarmed:
        results.append(("DUE", f"{len(no_min_swarmed)} bridge file(s) missing 'Minimum Swarmed Cycle' section (F-GOV2, L-351): {', '.join(no_min_swarmed[:3])}"))

    return results


def check_commit_hooks(
    REPO_ROOT: Path,
    _exists,
    _read,
) -> list[tuple[str, str]]:
    results = []
    git_dir = REPO_ROOT / ".git"
    if not git_dir.exists(): return results
    hooks_dir = git_dir / "hooks"
    if not hooks_dir.exists(): return [("NOTICE", ".git/hooks missing -- commit quality hooks unavailable")]
    expected = [("pre-commit", "tools/pre-commit.hook"), ("commit-msg", "tools/commit-msg.hook")]
    missing_tpl = [tpl for _, tpl in expected if not _exists(tpl)]
    if missing_tpl: return [("DUE", f"Hook template(s) missing: {', '.join(missing_tpl[:3])}")]
    missing_inst, drifted = [], []
    for hook_name, tpl_rel in expected:
        tpl_text = _read(REPO_ROOT / tpl_rel).replace("\r\n", "\n").strip()
        inst_path = hooks_dir / hook_name
        if not inst_path.exists(): missing_inst.append(hook_name); continue
        if tpl_text != _read(inst_path).replace("\r\n", "\n").strip(): drifted.append(hook_name)
    if missing_inst: results.append(("DUE", f"Missing hook(s): {', '.join(missing_inst)} -- run: bash tools/install-hooks.sh"))
    if drifted: results.append(("NOTICE", f"Hook drift detected ({', '.join(drifted)}) -- run: bash tools/install-hooks.sh"))
    return results
