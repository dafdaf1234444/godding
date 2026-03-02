#!/usr/bin/env python3
"""
spawn_coordinator.py — Hierarchical spawn coordinator for the swarm.

Usage:
    python3 tools/spawn_coordinator.py plan <task-description> --decompose <item1> <item2> ...
    python3 tools/spawn_coordinator.py prompts <plan-file>
    python3 tools/spawn_coordinator.py evaluate <plan-file> <result1.json> <result2.json> ...
    python3 tools/spawn_coordinator.py record <plan-file> <quality> <variety> [--novel N] [--lesson TEXT]
    python3 tools/spawn_coordinator.py history
    python3 tools/spawn_coordinator.py recommend

Automates the pattern: decompose → spawn → collect → synthesize.
The top-level swarm decomposes a complex task into sub-tasks by data,
spawns parallel agents for each, and evaluates variety/quality.

Design principle (P-057): Decompose by data, not by method.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLANS_DIR = REPO_ROOT / "experiments" / "spawn-plans"
HISTORY_FILE = PLANS_DIR / "spawn-history.json"


def plan(task: str, items: list[str], tool_cmd: str = "",
         output_format: str = "summary table + answers"):
    """Create a spawn plan: decompose a task across data items."""
    plan_id = f"spawn-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    plan_data = {
        "id": plan_id,
        "task": task,
        "items": items,
        "tool_cmd": tool_cmd,
        "output_format": output_format,
        "created": datetime.now().isoformat(),
        "status": "planned",
        "agents": [],
    }

    for i, item in enumerate(items):
        agent = {
            "id": f"agent-{chr(65 + i)}",
            "item": item,
            "status": "pending",
            "result": None,
        }
        plan_data["agents"].append(agent)

    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    plan_file = PLANS_DIR / f"{plan_id}.json"
    plan_file.write_text(json.dumps(plan_data, indent=2))

    print(f"=== SPAWN PLAN: {plan_id} ===\n")
    print(f"  Task: {task}")
    print(f"  Decomposition: {len(items)} sub-tasks")
    for agent in plan_data["agents"]:
        print(f"    {agent['id']}: {agent['item']}")
    print(f"\n  Plan saved: {plan_file}")
    print(f"\n  Next: run 'prompts {plan_file}' to generate agent prompts")
    return plan_data


def generate_prompts(plan_file: str):
    """Generate Task tool prompts for each agent in the plan."""
    data = json.loads(Path(plan_file).read_text())

    print(f"=== AGENT PROMPTS FOR: {data['id']} ===\n")
    print(f"Task: {data['task']}\n")

    prompts = []
    for agent in data["agents"]:
        prompt = (
            f"You are a sub-agent of the swarm ({agent['id']}). "
            f"Your task: {data['task']}\n\n"
            f"Your specific focus: {agent['item']}\n\n"
        )
        if data.get("tool_cmd"):
            prompt += f"Tool to use: {data['tool_cmd']}\n\n"
        prompt += (
            f"Return your findings as: {data['output_format']}\n"
            f"Do NOT write any files. Return results in your response only."
        )
        prompts.append({"agent": agent["id"], "item": agent["item"], "prompt": prompt})

        print(f"--- {agent['id']}: {agent['item']} ---")
        print(prompt)
        print()

    return prompts


def evaluate(results: list[dict]):
    """Evaluate spawn results for variety and quality.

    Each result should have: agent_id, item, findings (text), metrics (dict).
    """
    print("=== SPAWN EVALUATION ===\n")

    # Quality: did each agent produce findings?
    quality_scores = []
    for r in results:
        has_findings = bool(r.get("findings"))
        has_metrics = bool(r.get("metrics"))
        score = (1 if has_findings else 0) + (1 if has_metrics else 0)
        quality_scores.append(score)
        print(f"  {r['agent_id']}: quality={score}/2 ({'OK' if score == 2 else 'PARTIAL'})")

    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    print(f"\n  Average quality: {avg_quality:.1f}/2")

    # Variety: how different are the findings?
    if len(results) >= 2:
        # Simple: count unique terms across findings
        term_sets = []
        for r in results:
            words = set(r.get("findings", "").lower().split())
            term_sets.append(words)

        # Pairwise Jaccard distance (1 - similarity)
        distances = []
        for i in range(len(term_sets)):
            for j in range(i + 1, len(term_sets)):
                intersection = len(term_sets[i] & term_sets[j])
                union = len(term_sets[i] | term_sets[j])
                jaccard = intersection / union if union > 0 else 0
                distances.append(1 - jaccard)

        avg_distance = sum(distances) / len(distances)
        print(f"\n  Variety (avg Jaccard distance): {avg_distance:.2f}")
        if avg_distance > 0.7:
            print("  Assessment: HIGH variety — agents produced genuinely different insights")
        elif avg_distance > 0.4:
            print("  Assessment: MODERATE variety — some overlap but distinct perspectives")
        else:
            print("  Assessment: LOW variety — agents produced similar findings")

    # Synthesis potential: what patterns emerge across agents?
    print(f"\n  Agents: {len(results)}")
    print(f"  All completed: {'YES' if all(q == 2 for q in quality_scores) else 'NO'}")

    return {
        "quality": avg_quality,
        "variety": avg_distance if len(results) >= 2 else None,
        "count": len(results),
    }


def record_and_learn(plan_file: str, quality: float, variety: float,
                     novel_insights: int = 0, lesson: str = ""):
    """Record spawn outcome and suggest strategy improvements.

    Appends to spawn-history.json and prints recommendations based
    on accumulated experience.
    """
    data = json.loads(Path(plan_file).read_text())
    PLANS_DIR.mkdir(parents=True, exist_ok=True)

    # Load or create history
    history = []
    if HISTORY_FILE.exists():
        history = json.loads(HISTORY_FILE.read_text())

    record = {
        "id": data["id"],
        "task": data["task"],
        "decomposition": "by-data",
        "agents": len(data["agents"]),
        "items": data["items"],
        "quality_avg": round(quality, 2),
        "variety": round(variety, 2),
        "novel_insights": novel_insights,
        "lesson": lesson,
        "date": datetime.now().isoformat(),
    }
    history.append(record)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))

    print(f"=== SPAWN RECORD: {data['id']} ===")
    print(f"  Quality: {quality:.1f}  Variety: {variety:.2f}  Novel: {novel_insights}")

    # Learn from history — recommend strategy adjustments
    if len(history) >= 2:
        avg_var = sum(h["variety"] for h in history) / len(history)
        avg_qual = sum(h["quality_avg"] for h in history) / len(history)
        print(f"\n  History ({len(history)} spawns): avg quality={avg_qual:.1f}, avg variety={avg_var:.2f}")

        if variety < 0.4:
            print("  RECOMMENDATION: Low variety. Try different data splits or add constraints.")
        if quality < 1.0:
            print("  RECOMMENDATION: Low quality. Make prompts more specific or reduce scope.")
        if variety > avg_var + 0.1:
            print(f"  NOTE: Variety above average ({avg_var:.2f}) — this decomposition works well.")

    print(f"\n  Saved to: {HISTORY_FILE}")
    return record


def recommend(task_type: str = ""):
    """Recommend spawn strategy based on history.

    Analyzes past spawns and recommends parallel, sequential, or two-phase
    based on what worked for similar task types.
    """
    history = []
    if HISTORY_FILE.exists():
        history = json.loads(HISTORY_FILE.read_text())

    print("=== SPAWN STRATEGY RECOMMENDATION ===\n")

    if len(history) < 2:
        print("  Not enough history (<2 spawns). Default: parallel with 3 agents.")
        print("  Tip: Use --decompose with different data splits (P-057)")
        return {"strategy": "parallel", "reason": "insufficient history"}

    # Analyze patterns
    parallel = [h for h in history if h["variety"] > 0.5]
    sequential = [h for h in history if h["variety"] <= 0.5]

    avg_novel_par = (sum(h["novel_insights"] for h in parallel) / len(parallel)
                     if parallel else 0)
    avg_novel_seq = (sum(h["novel_insights"] for h in sequential) / len(sequential)
                     if sequential else 0)

    print(f"  History: {len(history)} spawns ({len(parallel)} parallel, {len(sequential)} sequential)")
    print(f"  Parallel avg novel insights: {avg_novel_par:.1f}")
    print(f"  Sequential avg novel insights: {avg_novel_seq:.1f}")

    # Two-phase is always recommended when we have evidence for both
    if parallel and sequential:
        print(f"\n  RECOMMENDED: Two-phase (P-059)")
        print(f"    Phase 1: Parallel exploration ({len(parallel)} precedents, avg variety={sum(h['variety'] for h in parallel)/len(parallel):.2f})")
        print(f"    Phase 2: Sequential drill-down on best finding ({len(sequential)} precedents)")
        strategy = "two-phase"
    elif avg_novel_par >= avg_novel_seq:
        print(f"\n  RECOMMENDED: Parallel (higher novelty: {avg_novel_par:.1f} vs {avg_novel_seq:.1f})")
        strategy = "parallel"
    else:
        print(f"\n  RECOMMENDED: Sequential (higher novelty: {avg_novel_seq:.1f} vs {avg_novel_par:.1f})")
        strategy = "sequential"

    # Best decomposition from history
    best = max(history, key=lambda h: h["novel_insights"])
    print(f"\n  Best past spawn: {best['id']} ({best['novel_insights']} novel insights)")
    print(f"    Task: {best['task'][:80]}")
    print(f"    Items: {', '.join(best['items'][:3])}")

    return {"strategy": strategy, "history_size": len(history)}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "plan":
        if len(sys.argv) < 3:
            print("Usage: spawn_coordinator.py plan <task> --decompose <item1> <item2> ...")
            sys.exit(1)
        task = sys.argv[2]
        items = []
        if "--decompose" in sys.argv:
            idx = sys.argv.index("--decompose")
            items = sys.argv[idx + 1:]
        if not items:
            print("Error: --decompose requires at least 2 items")
            sys.exit(1)
        tool_cmd = ""
        if "--tool" in sys.argv:
            tool_idx = sys.argv.index("--tool")
            tool_cmd = sys.argv[tool_idx + 1]
        plan(task, items, tool_cmd)

    elif cmd == "prompts":
        if len(sys.argv) < 3:
            print("Usage: spawn_coordinator.py prompts <plan-file>")
            sys.exit(1)
        generate_prompts(sys.argv[2])

    elif cmd == "evaluate":
        if len(sys.argv) < 3:
            print("Usage: spawn_coordinator.py evaluate <result1.json> ...")
            sys.exit(1)
        results = []
        for f in sys.argv[2:]:
            results.append(json.loads(Path(f).read_text()))
        evaluate(results)

    elif cmd == "record":
        if len(sys.argv) < 5:
            print("Usage: spawn_coordinator.py record <plan-file> <quality> <variety> [--novel N] [--lesson TEXT]")
            sys.exit(1)
        pf = sys.argv[2]
        quality = float(sys.argv[3])
        variety = float(sys.argv[4])
        novel = 0
        lesson = ""
        if "--novel" in sys.argv:
            novel = int(sys.argv[sys.argv.index("--novel") + 1])
        if "--lesson" in sys.argv:
            lesson = sys.argv[sys.argv.index("--lesson") + 1]
        record_and_learn(pf, quality, variety, novel, lesson)

    elif cmd == "recommend":
        recommend()

    elif cmd == "history":
        if HISTORY_FILE.exists():
            history = json.loads(HISTORY_FILE.read_text())
            print(f"=== SPAWN HISTORY ({len(history)} entries) ===\n")
            for h in history:
                print(f"  {h['id']}: q={h['quality_avg']:.1f} v={h['variety']:.2f} novel={h['novel_insights']} — {h['task'][:60]}")
            avg_v = sum(h["variety"] for h in history) / len(history) if history else 0
            avg_q = sum(h["quality_avg"] for h in history) / len(history) if history else 0
            print(f"\n  Averages: quality={avg_q:.1f}, variety={avg_v:.2f}")
        else:
            print("No spawn history yet.")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
