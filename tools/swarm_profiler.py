#!/usr/bin/env python3
"""
swarm_profiler.py — Profile swarm tool execution and identify bottlenecks.

Measures wall-clock time for key swarm operations (git, orient, maintenance,
dispatch, etc.), identifies slow paths, and persists results for trend tracking.

Usage:
    python3 tools/swarm_profiler.py               # full profile
    python3 tools/swarm_profiler.py --quick        # git + orient only
    python3 tools/swarm_profiler.py --json         # machine-readable output
    python3 tools/swarm_profiler.py --trend        # show history from past runs
    python3 tools/swarm_profiler.py --compare N    # compare current vs session N
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "workspace"
HISTORY_FILE = RESULTS_DIR / "profiler-history.json"

# Bottleneck thresholds (seconds) — operations slower than these get flagged
THRESHOLDS = {
    "git_status": 1.0,
    "git_log_5": 1.0,
    "git_log_50": 2.0,
    "git_diff_stat": 1.5,
    "git_rev_parse": 0.5,
    "orient_py": 15.0,
    "maintenance_py": 10.0,
    "dispatch_optimizer_py": 5.0,
    "task_order_py": 5.0,
    "contract_check_py": 5.0,
    "sync_state_py": 5.0,
    "validate_beliefs_py": 5.0,
    "compact_py_dry": 10.0,
    "lesson_count": 1.0,
    "file_glob_tools": 1.0,
    "file_glob_lessons": 1.0,
}


def _time_cmd(args: list[str], timeout: int = 30, label: str = "") -> dict:
    """Run a command, return timing + result metadata."""
    start = time.monotonic()
    try:
        r = subprocess.run(
            args, capture_output=True, text=True,
            cwd=ROOT, timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        elapsed = time.monotonic() - start
        return {
            "label": label,
            "elapsed_s": round(elapsed, 3),
            "returncode": r.returncode,
            "stdout_lines": len(r.stdout.splitlines()),
            "stderr_lines": len(r.stderr.splitlines()),
            "ok": r.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return {
            "label": label,
            "elapsed_s": round(elapsed, 3),
            "returncode": -1,
            "stdout_lines": 0,
            "stderr_lines": 0,
            "ok": False,
            "timeout": True,
        }
    except FileNotFoundError:
        return {
            "label": label,
            "elapsed_s": 0.0,
            "returncode": -1,
            "ok": False,
            "missing": True,
        }


def _time_file_op(label: str, func) -> dict:
    """Time a Python file operation."""
    start = time.monotonic()
    try:
        result = func()
        elapsed = time.monotonic() - start
        return {
            "label": label,
            "elapsed_s": round(elapsed, 3),
            "ok": True,
            "result": result,
        }
    except Exception as e:
        elapsed = time.monotonic() - start
        return {
            "label": label,
            "elapsed_s": round(elapsed, 3),
            "ok": False,
            "error": str(e),
        }


def profile_git() -> list[dict]:
    """Profile core git operations."""
    py = sys.executable
    results = []
    results.append(_time_cmd(
        ["git", "rev-parse", "--short=12", "HEAD"],
        label="git_rev_parse", timeout=5,
    ))
    results.append(_time_cmd(
        ["git", "status", "--short"],
        label="git_status", timeout=10,
    ))
    results.append(_time_cmd(
        ["git", "log", "--oneline", "-5"],
        label="git_log_5", timeout=10,
    ))
    results.append(_time_cmd(
        ["git", "log", "--oneline", "-50"],
        label="git_log_50", timeout=10,
    ))
    results.append(_time_cmd(
        ["git", "diff", "--stat", "HEAD"],
        label="git_diff_stat", timeout=10,
    ))
    return results


def profile_tools(quick: bool = False) -> list[dict]:
    """Profile swarm tool execution."""
    py = sys.executable
    results = []

    # orient.py — the main orientation tool
    results.append(_time_cmd(
        [py, str(ROOT / "tools" / "orient.py")],
        label="orient_py", timeout=30,
    ))

    if quick:
        return results

    # maintenance.py --quick
    results.append(_time_cmd(
        [py, str(ROOT / "tools" / "maintenance.py"), "--quick"],
        label="maintenance_py", timeout=20,
    ))

    # dispatch_optimizer.py
    results.append(_time_cmd(
        [py, str(ROOT / "tools" / "dispatch_optimizer.py")],
        label="dispatch_optimizer_py", timeout=15,
    ))

    # task_order.py
    results.append(_time_cmd(
        [py, str(ROOT / "tools" / "task_order.py")],
        label="task_order_py", timeout=15,
    ))

    # contract_check.py
    results.append(_time_cmd(
        [py, str(ROOT / "tools" / "contract_check.py")],
        label="contract_check_py", timeout=15,
    ))

    # sync_state.py --dry-run (if supported, otherwise plain)
    results.append(_time_cmd(
        [py, str(ROOT / "tools" / "sync_state.py")],
        label="sync_state_py", timeout=15,
    ))

    # validate_beliefs.py
    results.append(_time_cmd(
        [py, str(ROOT / "tools" / "validate_beliefs.py")],
        label="validate_beliefs_py", timeout=15,
    ))

    # compact.py --dry-run
    results.append(_time_cmd(
        [py, str(ROOT / "tools" / "compact.py"), "--dry-run"],
        label="compact_py_dry", timeout=20,
    ))

    return results


def profile_filesystem() -> list[dict]:
    """Profile filesystem operations common in swarm tools."""
    results = []

    # Count lesson files
    results.append(_time_file_op("lesson_count", lambda: len(
        list((ROOT / "memory" / "lessons").glob("L-*.md"))
    )))

    # Glob tools/
    results.append(_time_file_op("file_glob_tools", lambda: len(
        list((ROOT / "tools").glob("*.py"))
    )))

    # Glob all lessons
    results.append(_time_file_op("file_glob_lessons", lambda: len(
        list((ROOT / "memory" / "lessons").glob("*.md"))
    )))

    # Read INDEX.md
    results.append(_time_file_op("read_index_md", lambda: len(
        (ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8")
    )))

    # Read FRONTIER.md
    results.append(_time_file_op("read_frontier_md", lambda: len(
        (ROOT / "tasks" / "FRONTIER.md").read_text(encoding="utf-8")
    )))

    return results


def _session_number() -> int:
    """Best-effort current session number."""
    try:
        r = subprocess.run(
            ["git", "log", "--oneline", "-50"],
            capture_output=True, text=True, cwd=ROOT, timeout=5,
        )
        import re
        nums = [int(m) for m in re.findall(r"\[S(\d+)\]", r.stdout)]
        return max(nums) if nums else 0
    except Exception:
        return 0


def analyze(results: list[dict]) -> dict:
    """Analyze profiling results: total time, bottlenecks, distribution."""
    total = sum(r["elapsed_s"] for r in results)
    bottlenecks = []
    for r in results:
        label = r["label"]
        threshold = THRESHOLDS.get(label, 5.0)
        if r["elapsed_s"] > threshold:
            bottlenecks.append({
                "label": label,
                "elapsed_s": r["elapsed_s"],
                "threshold_s": threshold,
                "over_by": round(r["elapsed_s"] - threshold, 3),
            })
    bottlenecks.sort(key=lambda x: x["over_by"], reverse=True)

    # Phase breakdown
    git_time = sum(r["elapsed_s"] for r in results if r["label"].startswith("git_"))
    tool_time = sum(r["elapsed_s"] for r in results if r["label"].endswith("_py"))
    fs_time = sum(r["elapsed_s"] for r in results
                  if r["label"].startswith(("lesson_", "file_glob_", "read_")))
    other_time = total - git_time - tool_time - fs_time

    failed = [r["label"] for r in results if not r.get("ok", True)]
    timed_out = [r["label"] for r in results if r.get("timeout")]

    return {
        "total_s": round(total, 3),
        "phases": {
            "git_s": round(git_time, 3),
            "tools_s": round(tool_time, 3),
            "filesystem_s": round(fs_time, 3),
            "other_s": round(other_time, 3),
        },
        "bottleneck_count": len(bottlenecks),
        "bottlenecks": bottlenecks,
        "failed": failed,
        "timed_out": timed_out,
    }


def load_history() -> list[dict]:
    """Load profiling history."""
    try:
        return json.loads(HISTORY_FILE.read_text())
    except Exception:
        return []


def save_result(session: int, results: list[dict], analysis: dict):
    """Persist profiling result to history."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    history = load_history()

    entry = {
        "session": session,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_s": analysis["total_s"],
        "phases": analysis["phases"],
        "bottleneck_count": analysis["bottleneck_count"],
        "details": {r["label"]: r["elapsed_s"] for r in results},
    }
    history.append(entry)

    # Keep last 50 entries
    if len(history) > 50:
        history = history[-50:]

    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def format_results(results: list[dict], analysis: dict, session: int) -> str:
    """Format profiling results for terminal display."""
    lines = []
    lines.append(f"=== SWARM PROFILER S{session} ===")
    lines.append("")

    # Results table
    lines.append(f"{'Operation':<30} {'Time':>8} {'Status':>8}")
    lines.append("-" * 48)
    for r in results:
        elapsed = f"{r['elapsed_s']:.3f}s"
        if r.get("timeout"):
            status = "TIMEOUT"
        elif r.get("missing"):
            status = "MISSING"
        elif not r.get("ok", True):
            status = "FAIL"
        else:
            threshold = THRESHOLDS.get(r["label"], 5.0)
            if r["elapsed_s"] > threshold:
                status = "SLOW"
            elif r["elapsed_s"] > threshold * 0.7:
                status = "WARN"
            else:
                status = "OK"
        lines.append(f"  {r['label']:<28} {elapsed:>8} {status:>8}")

    # Phase breakdown
    lines.append("")
    lines.append("--- Phase breakdown ---")
    p = analysis["phases"]
    total = analysis["total_s"]
    if total > 0:
        lines.append(f"  Git operations:  {p['git_s']:>7.3f}s ({p['git_s']/total*100:4.1f}%)")
        lines.append(f"  Tool execution:  {p['tools_s']:>7.3f}s ({p['tools_s']/total*100:4.1f}%)")
        lines.append(f"  Filesystem I/O:  {p['filesystem_s']:>7.3f}s ({p['filesystem_s']/total*100:4.1f}%)")
        if p["other_s"] > 0.01:
            lines.append(f"  Other:           {p['other_s']:>7.3f}s ({p['other_s']/total*100:4.1f}%)")
    lines.append(f"  TOTAL:           {total:>7.3f}s")

    # Bottlenecks
    if analysis["bottlenecks"]:
        lines.append("")
        lines.append("--- Bottlenecks (over threshold) ---")
        for b in analysis["bottlenecks"]:
            lines.append(
                f"  ! {b['label']}: {b['elapsed_s']:.3f}s "
                f"(threshold {b['threshold_s']:.1f}s, over by {b['over_by']:.3f}s)"
            )

    if analysis["timed_out"]:
        lines.append("")
        lines.append("--- Timed out ---")
        for t in analysis["timed_out"]:
            lines.append(f"  !! {t}")

    if analysis["failed"]:
        lines.append("")
        lines.append("--- Failed ---")
        for f in analysis["failed"]:
            lines.append(f"  X {f}")

    return "\n".join(lines)


def format_trend(history: list[dict]) -> str:
    """Format historical profiling trend."""
    if not history:
        return "No profiling history. Run `python3 tools/swarm_profiler.py` first."

    lines = []
    lines.append("=== PROFILER TREND ===")
    lines.append("")
    lines.append(f"{'Session':>8} {'Total':>8} {'Git':>8} {'Tools':>8} {'FS':>8} {'Bottlenecks':>12}")
    lines.append("-" * 60)
    for entry in history[-20:]:
        s = entry.get("session", "?")
        t = entry.get("total_s", 0)
        p = entry.get("phases", {})
        bn = entry.get("bottleneck_count", 0)
        lines.append(
            f"  S{s:<6} {t:>7.1f}s {p.get('git_s', 0):>7.1f}s "
            f"{p.get('tools_s', 0):>7.1f}s {p.get('filesystem_s', 0):>7.1f}s "
            f"{bn:>6}"
        )

    # Trend analysis
    if len(history) >= 3:
        recent = history[-3:]
        totals = [e["total_s"] for e in recent]
        avg = sum(totals) / len(totals)
        first_avg = sum(e["total_s"] for e in history[:3]) / min(3, len(history))
        delta = avg - first_avg
        direction = "FASTER" if delta < -1 else "SLOWER" if delta > 1 else "STABLE"
        lines.append("")
        lines.append(f"  Recent 3-run avg: {avg:.1f}s | First 3-run avg: {first_avg:.1f}s | {direction} ({delta:+.1f}s)")

    return "\n".join(lines)


def format_compare(current: dict, history: list[dict], target_session: int) -> str:
    """Compare current profile against a historical session."""
    target = None
    for entry in history:
        if entry.get("session") == target_session:
            target = entry
            break
    if not target:
        return f"No profiling data for session S{target_session}."

    lines = []
    lines.append(f"=== COMPARE: current vs S{target_session} ===")
    lines.append("")
    lines.append(f"{'Metric':<25} {'Current':>10} {'S' + str(target_session):>10} {'Delta':>10}")
    lines.append("-" * 58)

    # Total
    ct = current["total_s"]
    tt = target["total_s"]
    lines.append(f"  {'Total':<23} {ct:>9.1f}s {tt:>9.1f}s {ct - tt:>+9.1f}s")

    # Phases
    for phase in ("git_s", "tools_s", "filesystem_s"):
        cv = current["phases"].get(phase, 0)
        tv = target["phases"].get(phase, 0)
        name = phase.replace("_s", "").title()
        lines.append(f"  {name:<23} {cv:>9.1f}s {tv:>9.1f}s {cv - tv:>+9.1f}s")

    # Per-operation comparison
    cd = current.get("details", {})
    td = target.get("details", {})
    all_ops = sorted(set(list(cd.keys()) + list(td.keys())))
    if all_ops:
        lines.append("")
        lines.append(f"  {'Operation':<23} {'Current':>10} {'S' + str(target_session):>10} {'Delta':>10}")
        lines.append("  " + "-" * 54)
        for op in all_ops:
            cv = cd.get(op, 0)
            tv = td.get(op, 0)
            delta = cv - tv
            flag = " !" if abs(delta) > 2.0 else ""
            lines.append(f"  {op:<23} {cv:>9.3f}s {tv:>9.3f}s {delta:>+9.3f}s{flag}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Profile swarm tool execution")
    parser.add_argument("--quick", action="store_true", help="Git + orient only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--trend", action="store_true", help="Show historical trend")
    parser.add_argument("--compare", type=int, metavar="N", help="Compare vs session N")
    parser.add_argument("--no-save", action="store_true", help="Don't persist results")
    args = parser.parse_args()

    session = _session_number()

    if args.trend:
        print(format_trend(load_history()))
        return

    # Run profiling
    all_results = []

    print(f"Profiling swarm tools (S{session})...", file=sys.stderr)

    # Phase 1: Git operations
    print("  [1/3] Git operations...", file=sys.stderr)
    all_results.extend(profile_git())

    # Phase 2: Tool execution
    print("  [2/3] Tool execution...", file=sys.stderr)
    all_results.extend(profile_tools(quick=args.quick))

    # Phase 3: Filesystem (skip in quick mode)
    if not args.quick:
        print("  [3/3] Filesystem I/O...", file=sys.stderr)
        all_results.extend(profile_filesystem())
    else:
        print("  [3/3] Filesystem I/O... (skipped --quick)", file=sys.stderr)

    analysis = analyze(all_results)

    # Compare mode
    if args.compare is not None:
        history = load_history()
        current_entry = {
            "total_s": analysis["total_s"],
            "phases": analysis["phases"],
            "details": {r["label"]: r["elapsed_s"] for r in all_results},
        }
        print(format_compare(current_entry, history, args.compare))
        return

    # Save
    if not args.no_save:
        save_result(session, all_results, analysis)

    # Output
    if args.json:
        output = {
            "session": session,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "results": all_results,
            "analysis": analysis,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_results(all_results, analysis, session))


if __name__ == "__main__":
    main()
