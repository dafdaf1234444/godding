#!/usr/bin/env python3
"""
pulse.py — Colony pulse: quick session orientation.

Usage:
    python3 tools/pulse.py          # print to stdout
    python3 tools/pulse.py --save   # also write to memory/PULSE.md

Generates a snapshot of system state for fast session start:
- Recent commits and their modes
- Most recently modified files
- Active claims on frontier questions
- Frontier questions sorted by signal strength
- Active children and their status
"""

import io
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DECAY_FILE = REPO_ROOT / "experiments" / "frontier-decay.json"
CLAIMS_FILE = REPO_ROOT / "experiments" / "frontier-claims.json"
CHILDREN_DIR = REPO_ROOT / "experiments" / "children"
PULSE_PATH = REPO_ROOT / "memory" / "PULSE.md"


def _git(*args: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT)] + list(args),
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip()
    except Exception:
        return ""


def generate_pulse(out=None):
    """Generate the colony pulse. Prints to out (default sys.stdout)."""
    if out is None:
        out = sys.stdout

    def p(s=""):
        print(s, file=out)

    p("=== COLONY PULSE ===")
    p(f"Date: {date.today()}")
    p()

    # --- Recent commits ---
    p("## Recent Activity (last 10 commits)")
    log = _git("log", "--oneline", "-10", "--format=%h %s (%ar)")
    if log:
        for line in log.splitlines():
            p(f"  {line}")
    p()

    # --- Most recently modified files ---
    p("## Hot Files (modified in last 5 commits)")
    recent_shas = _git("log", "-5", "--format=%H").splitlines()
    file_counts = {}
    for sha in recent_shas:
        files = _git("diff-tree", "--no-commit-id", "--name-only", "-r", sha)
        for f in files.splitlines():
            f = f.strip()
            if f:
                file_counts[f] = file_counts.get(f, 0) + 1
    for f, count in sorted(file_counts.items(), key=lambda x: -x[1])[:10]:
        p(f"  {f} ({count}x)")
    p()

    # --- Active claims ---
    p("## Active Claims")
    if CLAIMS_FILE.exists():
        claims = json.loads(CLAIMS_FILE.read_text())
        active = {k: v for k, v in claims.items() if v.get("status") == "claimed"}
        if active:
            for fid, info in sorted(active.items()):
                p(f"  {fid}: claimed by {info.get('session', '?')} at {info.get('timestamp', '?')}")
        else:
            p("  No active claims.")
    else:
        p("  No claims file.")
    p()

    # --- Frontier questions by strength ---
    p("## Frontier Questions (by signal strength)")
    frontier_path = REPO_ROOT / "tasks" / "FRONTIER.md"
    if frontier_path.exists():
        text = frontier_path.read_text()
        resolved_pos = text.find("## Resolved")
        open_text = text[:resolved_pos] if resolved_pos > 0 else text

        decay = {}
        if DECAY_FILE.exists():
            decay = json.loads(DECAY_FILE.read_text())

        today = date.today().isoformat()
        questions = []
        for m in re.finditer(r"^- \*\*F(\d+)\*\*:\s*(.+)$", open_text, re.MULTILINE):
            fid = f"F{m.group(1)}"
            q_text = m.group(2).strip()
            last_active = decay.get(fid, {}).get("last_active", today)
            days = (date.fromisoformat(today) - date.fromisoformat(last_active)).days
            strength = 0.9 ** days
            questions.append((strength, fid, q_text))

        questions.sort(reverse=True)
        for strength, fid, q_text in questions[:8]:
            p(f"  [{strength:.2f}] {fid}: {q_text[:65]}")

        resolved_count = len(re.findall(r"^\| F\d+", text, re.MULTILINE))
        p(f"\n  Open: {len(questions)} | Resolved: {resolved_count}")
    p()

    # --- Agents ---
    p("## Agents")
    if CHILDREN_DIR.exists():
        children = sorted([d for d in CHILDREN_DIR.iterdir() if d.is_dir()])
        if children:
            def child_task(child_dir):
                agent_task = child_dir / "tasks" / "AGENT-TASK.md"
                if agent_task.exists():
                    lines = agent_task.read_text().splitlines()
                    for i, line in enumerate(lines):
                        if line.strip() == "## Description" and i + 1 < len(lines):
                            t = lines[i + 1].strip()
                            if t:
                                return (t[:42] + "…") if len(t) > 42 else t
                meta_path = child_dir / ".swarm_meta.json"
                if meta_path.exists():
                    try:
                        t = json.loads(meta_path.read_text()).get("task", "")
                        if t:
                            return (t[:42] + "…") if len(t) > 42 else t
                    except Exception:
                        pass
                return "—"

            def child_last_commit(child_dir):
                r = subprocess.run(
                    ["git", "-C", str(child_dir), "log", "--oneline", "-1",
                     "--format=%cd", "--date=short"],
                    capture_output=True, text=True, timeout=10
                )
                return r.stdout.strip() or "never"

            needs_attention, not_started, active_list, integrated_list = [], [], [], []

            for child_dir in children:
                name = child_dir.name
                lessons = len(list((child_dir / "memory" / "lessons").glob("L-*.md"))) if (child_dir / "memory" / "lessons").exists() else 0
                log_path = REPO_ROOT / "experiments" / "integration-log" / f"{name}.json"
                bulletin_path = REPO_ROOT / "experiments" / "inter-swarm" / "bulletins" / f"{name}.md"
                last = child_last_commit(child_dir)
                task = child_task(child_dir)
                entry = (name, task, last, lessons)

                if log_path.exists():
                    integrated_list.append(entry)
                elif bulletin_path.exists():
                    needs_attention.append(entry)
                elif last == "never":
                    not_started.append(entry)
                else:
                    active_list.append(entry)

            def fmt(name, task, last, lessons, flag=""):
                return f"  {name:<30} {task:<44} {last}  L:{lessons}{flag}"

            if needs_attention:
                p(f"  NEEDS ATTENTION ({len(needs_attention)})")
                for e in needs_attention:
                    p(fmt(*e, "  → bulletin unread"))
                p()
            if not_started:
                p(f"  NOT STARTED ({len(not_started)})")
                for e in not_started:
                    p(fmt(*e))
                p()
            if active_list:
                tasked = [e for e in active_list if e[1] != "—"]
                variants = [e for e in active_list if e[1] == "—"]
                p(f"  ACTIVE ({len(active_list)})")
                for e in tasked:
                    p(fmt(*e))
                if variants:
                    names = ", ".join(e[0] for e in variants)
                    p(f"  {'':30} experiment variants ({len(variants)}): {names}")
                p()
            if integrated_list:
                names = ", ".join(e[0] for e in integrated_list)
                p(f"  INTEGRATED ({len(integrated_list)}): {names}")
        else:
            p("  No children spawned.")
    else:
        p("  No children directory.")
    p()

    # --- System health ---
    p("## System Health")
    r = subprocess.run(
        ["python3", str(REPO_ROOT / "tools" / "validate_beliefs.py")],
        capture_output=True, text=True
    )
    swarmability_m = re.search(r"SWARMABILITY: (\d+/100)", r.stdout)
    entropy_m = re.search(r"Entropy items: (\d+)", r.stdout)
    p(f"  Swarmability: {swarmability_m.group(1) if swarmability_m else '?'}")
    p(f"  Entropy: {entropy_m.group(1) if entropy_m else '?'}")

    lessons_count = len(list((REPO_ROOT / "memory" / "lessons").glob("L-*.md")))
    principles_count = len(re.findall(
        r"P-\d+",
        (REPO_ROOT / "memory" / "PRINCIPLES.md").read_text()
    )) if (REPO_ROOT / "memory" / "PRINCIPLES.md").exists() else 0
    total_commits = len(_git("log", "--oneline").splitlines())

    p(f"  Commits: {total_commits} | Lessons: {lessons_count} | Principles: {principles_count}")


if __name__ == "__main__":
    save = "--save" in sys.argv

    if save:
        buf = io.StringIO()
        generate_pulse(buf)
        output = buf.getvalue()
        sys.stdout.write(output)
        PULSE_PATH.write_text(output)
        print(f"\nSaved to {PULSE_PATH}")
    else:
        generate_pulse()
