#!/usr/bin/env python3
"""
session_tracker.py — Track session metrics and behavioral patterns for the swarm.

Usage:
    python3 tools/session_tracker.py record <session-number>
    python3 tools/session_tracker.py report
    python3 tools/session_tracker.py lambda
    python3 tools/session_tracker.py growth-rate [--n N]
    python3 tools/session_tracker.py trend [--window N]
    python3 tools/session_tracker.py track <session-number> [--elapsed MINUTES]
    python3 tools/session_tracker.py learn

Records per-session metrics by analyzing git history.
Provides λ_swarm calculation (Langton's lambda for the swarm).
Growth-rate implements predictive entropy metrics (P-043).
Track command: Agent history tracking with session outcome classification.
Learn command: Behavioral pattern analysis across sessions (swarm-grade).
"""

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRACKER_FILE = REPO_ROOT / "experiments" / "session-metrics.json"
OUTCOMES_FILE = REPO_ROOT / "workspace" / "session-outcomes.json"


def _git(*args: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT)] + list(args),
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip()
    except Exception:
        return ""


def record_session(session_num: int):
    """Record metrics for a session by analyzing recent commits."""
    # Load existing data
    data = {}
    if TRACKER_FILE.exists():
        data = json.loads(TRACKER_FILE.read_text())

    sessions = data.get("sessions", {})

    # Get all commits (approximate session boundary by looking at commit timestamps)
    log = _git("log", "--oneline", "--format=%H %s")
    all_commits = log.splitlines() if log else []

    # Analyze recent commits for this session
    recent = _git("log", "--oneline", "-10", "--format=%H")
    recent_shas = recent.splitlines() if recent else []

    files_touched = set()
    commit_count = 0
    structural_change = False

    for sha in recent_shas:
        commit_count += 1
        # Get files changed in this commit
        diff_stat = _git("show", "--stat", "--name-only", sha)
        for line in diff_stat.splitlines():
            line = line.strip()
            if "/" in line or "." in line:
                files_touched.add(line)
                # Structural changes: CLAUDE.md, DEPS.md, validator, genesis
                if line in (
                    "CLAUDE.md", "beliefs/DEPS.md",
                    "tools/validate_beliefs.py", "workspace/genesis.sh"
                ):
                    structural_change = True

    # Count current state
    lessons_count = len(list(
        (REPO_ROOT / "memory" / "lessons").glob("L-*.md")
    ))
    principles_count = len(re.findall(
        r"P-\d+",
        (REPO_ROOT / "memory" / "PRINCIPLES.md").read_text()
    )) if (REPO_ROOT / "memory" / "PRINCIPLES.md").exists() else 0

    # Count frontier state
    frontier_path = REPO_ROOT / "tasks" / "FRONTIER.md"
    frontier_open = 0
    frontier_resolved = 0
    if frontier_path.exists():
        ft = frontier_path.read_text()
        frontier_open = len(re.findall(r"^- \*\*F\d+\*\*:", ft, re.MULTILINE))
        frontier_resolved = len(re.findall(r"^\| F\d+", ft, re.MULTILINE))

    # Count entropy
    entropy_count = 0
    try:
        r = subprocess.run(
            ["python3", str(REPO_ROOT / "tools" / "validate_beliefs.py")],
            capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT)
        )
        m = re.search(r"Entropy items: (\d+)", r.stdout)
        if m:
            entropy_count = int(m.group(1))
    except Exception:
        pass

    session_data = {
        "commits": commit_count,
        "files_touched": len(files_touched),
        "structural_change": structural_change,
        "lessons_total": lessons_count,
        "principles_total": principles_count,
        "frontier_open": frontier_open,
        "frontier_resolved": frontier_resolved,
        "entropy_items": entropy_count,
    }

    sessions[str(session_num)] = session_data

    data["sessions"] = sessions
    data["latest_session"] = session_num
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(data, indent=2))

    print(f"Session {session_num} recorded:")
    print(f"  Commits: {commit_count}")
    print(f"  Files touched: {len(files_touched)}")
    print(f"  Structural change: {structural_change}")
    print(f"  Lessons total: {lessons_count}")
    print(f"  Principles total: {principles_count}")


def report():
    """Print a report of all tracked sessions."""
    if not TRACKER_FILE.exists():
        print("No session data. Run 'record' first.")
        return

    data = json.loads(TRACKER_FILE.read_text())
    sessions = data.get("sessions", {})

    print("=== SESSION METRICS ===\n")
    print(f"{'Session':<10} {'Commits':<10} {'Files':<10} {'Structural':<12} {'Lessons':<10} {'Principles':<12}")
    print("-" * 64)

    for sid in sorted(sessions.keys(), key=int):
        s = sessions[sid]
        struct = "Yes" if s.get("structural_change") else "No"
        print(
            f"{sid:<10} {s.get('commits', '?'):<10} "
            f"{s.get('files_touched', '?'):<10} {struct:<12} "
            f"{s.get('lessons_total', '?'):<10} {s.get('principles_total', '?'):<12}"
        )


def calculate_lambda():
    """Calculate Langton's lambda for the swarm."""
    if not TRACKER_FILE.exists():
        # Estimate from git history
        log = _git("log", "--oneline")
        total_commits = len(log.splitlines()) if log else 0

        # Count commits that touch structural files
        structural_files = [
            "CLAUDE.md", "beliefs/DEPS.md",
            "tools/validate_beliefs.py", "workspace/genesis.sh",
            "memory/OPERATIONS.md"
        ]
        structural_commits = 0
        for f in structural_files:
            flog = _git("log", "--oneline", "--", f)
            structural_commits += len(flog.splitlines()) if flog else 0

        # Rough dedup (some commits touch multiple structural files)
        structural_commits = min(structural_commits, total_commits)

        if total_commits == 0:
            print("No commits found.")
            return

        lambda_val = structural_commits / total_commits
        print(f"=== LANGTON'S λ (estimated from git) ===")
        print(f"Total commits: {total_commits}")
        print(f"Structural commits: {structural_commits}")
        print(f"λ_swarm ≈ {lambda_val:.2f}")
        print()

        if lambda_val < 0.2:
            print("Assessment: TOO LOW (Class I/II — frozen)")
            print("The system is not adapting enough. Consider challenging beliefs.")
        elif lambda_val < 0.4:
            print("Assessment: GOOD (Class IV — edge of chaos)")
            print("Healthy balance of structure and adaptation.")
        elif lambda_val < 0.7:
            print("Assessment: SLIGHTLY HIGH (trending toward Class III)")
            print("Consider more routine work, less structural change.")
        else:
            print("Assessment: TOO HIGH (Class III — chaotic)")
            print("Too much structural change. Stabilize before adding more.")
        return

    data = json.loads(TRACKER_FILE.read_text())
    sessions = data.get("sessions", {})

    total = len(sessions)
    structural = sum(
        1 for s in sessions.values() if s.get("structural_change")
    )

    if total == 0:
        print("No sessions recorded.")
        return

    lambda_val = structural / total
    print(f"=== LANGTON'S λ ===")
    print(f"Sessions: {total}")
    print(f"Structural changes: {structural}")
    print(f"λ_swarm = {lambda_val:.2f}")


def growth_rate(num_commits: int = 30):
    """Predictive entropy metrics (P-043, F48).

    Three leading indicators:
    1. File growth rates — warns when >1.5 net lines/commit for 5+ commits
    2. Frontier accumulation — open vs resolved question rates
    3. Belief ratio — theorized vs observed
    """
    print("=== PREDICTIVE ENTROPY METRICS ===\n")

    # --- 1. File growth rates ---
    print("## File Growth Rates")
    print(f"   (analyzing last {num_commits} commits)\n")

    # Parse numstat from git log (most recent first)
    raw = _git("log", f"-{num_commits}", "--numstat", "--format=COMMIT:%H")
    if not raw:
        print("  No git history found.")
        return

    # Build per-file growth history: list of net-lines per commit (touched only)
    file_growth = defaultdict(list)

    for line in raw.splitlines():
        if line.startswith("COMMIT:") or not line.strip():
            continue
        if "\t" in line:
            parts = line.split("\t")
            if len(parts) == 3:
                added, removed, filepath = parts
                if added == "-" or removed == "-":
                    continue  # binary file
                net = int(added) - int(removed)
                file_growth[filepath].append(net)

    # Identify files with sustained growth
    warnings = []
    hot_files = []

    # Only look at tracked files (not one-off new files)
    STRUCTURAL_FILES = {
        "CLAUDE.md", "beliefs/CORE.md", "beliefs/DEPS.md",
        "memory/INDEX.md", "memory/PRINCIPLES.md", "memory/OPERATIONS.md",
        "tasks/FRONTIER.md", "tasks/NEXT.md",
        "tools/validate_beliefs.py", "workspace/genesis.sh",
        "tools/session_tracker.py", "tools/evolve.py",
        "tools/self_evolve.py", "tools/swarm_integration_test.py",
        "workspace/README.md",
    }

    for filepath, changes in sorted(file_growth.items()):
        if len(changes) < 2:
            continue

        # Calculate average growth rate
        avg_growth = sum(changes) / len(changes)

        # Check for consecutive high-growth streaks
        streak = 0
        max_streak = 0
        for net in changes:
            if net > 1.5:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0

        is_structural = filepath in STRUCTURAL_FILES

        if max_streak >= 5:
            warnings.append({
                "file": filepath,
                "avg_growth": avg_growth,
                "streak": max_streak,
                "commits": len(changes),
                "structural": is_structural,
            })
        elif avg_growth > 1.0 and len(changes) >= 3:
            hot_files.append({
                "file": filepath,
                "avg_growth": avg_growth,
                "commits": len(changes),
                "structural": is_structural,
            })

    if warnings:
        print("  WARNING — Files needing compaction/restructure:")
        for w in warnings:
            marker = " [STRUCTURAL]" if w["structural"] else ""
            print(f"    {w['file']}{marker}")
            print(f"      avg +{w['avg_growth']:.1f} lines/commit, "
                  f"streak: {w['streak']} consecutive, "
                  f"touched in {w['commits']} commits")
        print()
    else:
        print("  No files exceed P-043 threshold (>1.5 lines/commit for 5+ commits).\n")

    if hot_files:
        print("  Hot files (high growth, below threshold):")
        for h in sorted(hot_files, key=lambda x: -x["avg_growth"])[:10]:
            marker = " [S]" if h["structural"] else ""
            print(f"    {h['file']}{marker}: "
                  f"avg +{h['avg_growth']:.1f} lines/commit "
                  f"({h['commits']} commits)")
        print()

    # --- 2. Frontier accumulation rate ---
    print("## Frontier Health\n")

    frontier_path = REPO_ROOT / "tasks" / "FRONTIER.md"
    if frontier_path.exists():
        frontier_text = frontier_path.read_text()

        # Count open questions
        open_questions = len(re.findall(
            r"^- \*\*F\d+\*\*:", frontier_text, re.MULTILINE
        ))

        # Count resolved questions
        resolved_questions = len(re.findall(
            r"^\| F\d+", frontier_text, re.MULTILINE
        ))

        total = open_questions + resolved_questions
        resolution_rate = resolved_questions / total if total > 0 else 0

        print(f"  Open questions:    {open_questions}")
        print(f"  Resolved:          {resolved_questions}")
        print(f"  Total generated:   {total}")
        print(f"  Resolution rate:   {resolution_rate:.0%}")

        if open_questions > resolved_questions:
            print("  STATUS: Accumulating (more open than resolved)")
            print("  ACTION: Focus on resolving existing questions before opening new ones.")
        elif resolution_rate > 0.8:
            print("  STATUS: Depleting (running low on questions)")
            print("  ACTION: The generative loop may be stalling — challenge more beliefs.")
        else:
            print("  STATUS: Healthy balance")
    else:
        print("  No FRONTIER.md found.")
    print()

    # --- 3. Belief ratio ---
    print("## Belief Ratio\n")

    deps_path = REPO_ROOT / "beliefs" / "DEPS.md"
    if deps_path.exists():
        deps_text = deps_path.read_text()

        observed = len(re.findall(
            r"\*\*Evidence\*\*:\s*observed", deps_text
        ))
        theorized = len(re.findall(
            r"\*\*Evidence\*\*:\s*theorized", deps_text
        ))
        total_beliefs = observed + theorized

        if total_beliefs > 0:
            observed_ratio = observed / total_beliefs
            print(f"  Observed:    {observed}/{total_beliefs} ({observed_ratio:.0%})")
            print(f"  Theorized:   {theorized}/{total_beliefs}")

            if observed_ratio < 0.5:
                print("  STATUS: Too speculative — more theorized than observed")
                print("  ACTION: Test theorized beliefs before adding new ones.")
            elif theorized == 0:
                print("  STATUS: Fully grounded — all beliefs observed")
                print("  NOTE: Consider adding bold theorized beliefs to drive exploration.")
            else:
                print("  STATUS: Healthy mix")
        else:
            print("  No beliefs found.")
    else:
        print("  No DEPS.md found.")

    print()

    # --- Summary ---
    print("## Summary")
    warning_count = len(warnings)
    if warning_count == 0:
        print("  All predictive indicators healthy.")
    else:
        print(f"  {warning_count} file(s) predicted to need restructuring soon.")
    print(f"  Run periodically to detect trends before they become problems.")


def trend(window: int = 5):
    """Analyze trends across sessions to detect stalls (F61).

    Computes slopes for key metrics across a rolling window and
    detects stall conditions:
    - Declining lesson generation rate
    - Frontier resolution rate declining
    - Entropy accumulation increasing
    - Lambda diverging from target range
    """
    if not TRACKER_FILE.exists():
        print("No session data. Run 'record' first.")
        return

    data = json.loads(TRACKER_FILE.read_text())
    sessions = data.get("sessions", {})

    if len(sessions) < 3:
        print(f"Need at least 3 sessions for trend analysis (have {len(sessions)}).")
        return

    # Sort sessions by number
    sorted_keys = sorted(sessions.keys(), key=int)
    recent = sorted_keys[-window:] if len(sorted_keys) >= window else sorted_keys

    print(f"=== TREND ANALYSIS (sessions {recent[0]}–{recent[-1]}) ===\n")

    # --- Metric extraction ---
    def get_metric(key, default=0):
        return [sessions[k].get(key, default) for k in recent]

    lessons = get_metric("lessons_total")
    principles = get_metric("principles_total")
    f_open = get_metric("frontier_open")
    f_resolved = get_metric("frontier_resolved")
    entropy = get_metric("entropy_items")
    structural = [1 if sessions[k].get("structural_change") else 0 for k in recent]

    def slope(values):
        """Simple linear regression slope."""
        n = len(values)
        if n < 2:
            return 0.0
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        return num / den if den > 0 else 0.0

    def direction(s):
        if abs(s) < 0.1:
            return "→ FLAT"
        return "↑ RISING" if s > 0 else "↓ FALLING"

    # --- Report ---
    stall_warnings = []

    # 1. Lessons per session (delta between consecutive sessions)
    lesson_deltas = [lessons[i] - lessons[i-1] for i in range(1, len(lessons))]
    avg_new_lessons = sum(lesson_deltas) / len(lesson_deltas) if lesson_deltas else 0
    lesson_slope = slope(lesson_deltas) if len(lesson_deltas) >= 2 else 0

    print(f"## Learning Rate")
    print(f"  Lessons: {lessons[0]} → {lessons[-1]} (+{lessons[-1]-lessons[0]} over {len(recent)} sessions)")
    print(f"  Avg new lessons/session: {avg_new_lessons:.1f}")
    print(f"  Trend: {direction(lesson_slope)} (slope={lesson_slope:+.2f})")
    if avg_new_lessons < 0.5 and len(recent) >= 3:
        stall_warnings.append("LEARNING STALLED: <0.5 new lessons/session")
        print(f"  ⚠ STALL: Learning rate below threshold")
    print()

    # 2. Frontier health
    if f_open and f_resolved:
        resolution_rates = [
            f_resolved[i] / (f_open[i] + f_resolved[i])
            if (f_open[i] + f_resolved[i]) > 0 else 0
            for i in range(len(recent))
        ]
        res_slope = slope(resolution_rates)

        print(f"## Frontier Health")
        print(f"  Open: {f_open[0]} → {f_open[-1]}")
        print(f"  Resolved: {f_resolved[0]} → {f_resolved[-1]}")
        print(f"  Resolution rate: {resolution_rates[0]:.0%} → {resolution_rates[-1]:.0%}")
        print(f"  Trend: {direction(res_slope)} (slope={res_slope:+.3f})")

        if res_slope < -0.02 and len(recent) >= 3:
            stall_warnings.append("CREATIVE EXHAUSTION: Resolution rate declining")
            print(f"  ⚠ STALL: Resolution rate declining across {len(recent)} sessions")
        elif resolution_rates[-1] > 0.85:
            stall_warnings.append("FRONTIER DEPLETING: >85% resolved, few open questions")
            print(f"  ⚠ WARNING: Running low on open questions")
        print()

    # 3. Entropy
    if any(e > 0 for e in entropy):
        ent_slope = slope(entropy)
        print(f"## Entropy")
        print(f"  Items: {entropy[0]} → {entropy[-1]}")
        print(f"  Trend: {direction(ent_slope)} (slope={ent_slope:+.2f})")
        if ent_slope > 0.3:
            stall_warnings.append("ENTROPY ACCUMULATING: Items increasing across sessions")
            print(f"  ⚠ STALL: Entropy outpacing repair")
        print()
    else:
        print(f"## Entropy")
        print(f"  Zero entropy across all measured sessions — healthy.")
        print()

    # 4. Structural change rate (lambda proxy)
    if len(recent) >= 3:
        lambda_recent = sum(structural) / len(structural)
        print(f"## Structural Change Rate (λ proxy)")
        print(f"  Changes: {sum(structural)}/{len(recent)} sessions ({lambda_recent:.0%})")
        if lambda_recent < 0.1:
            stall_warnings.append("FROZEN: No structural changes in recent sessions")
            print(f"  ⚠ STALL: System may be frozen (no adaptation)")
        elif lambda_recent > 0.8:
            print(f"  NOTE: High structural change rate — verify stability")
        else:
            print(f"  Healthy range")
        print()

    # --- Summary ---
    print(f"## Stall Detection Summary")
    if stall_warnings:
        print(f"  {len(stall_warnings)} warning(s) detected:")
        for w in stall_warnings:
            print(f"    ⚠ {w}")
    else:
        print(f"  No stall signals detected. System is healthy.")

    # Session data summary
    print(f"\n## Session Data")
    print(f"  {'Session':<8} {'Lessons':>8} {'Principles':>11} {'Open':>5} {'Resolved':>9} {'Entropy':>8} {'λ':>3}")
    print(f"  {'-'*55}")
    for k in recent:
        s = sessions[k]
        lam = "Y" if s.get("structural_change") else "N"
        print(
            f"  {k:<8} {s.get('lessons_total', '?'):>8} "
            f"{s.get('principles_total', '?'):>11} "
            f"{s.get('frontier_open', '?'):>5} "
            f"{s.get('frontier_resolved', '?'):>9} "
            f"{s.get('entropy_items', '?'):>8} "
            f"{lam:>3}"
        )


def track_session_outcome(session_num: int, elapsed_minutes: int = None):
    """Track session outcome metrics for pattern recognition."""
    # Load existing outcomes
    outcomes = {"schema": "session-outcomes-v1", "sessions": []}
    if OUTCOMES_FILE.exists():
        outcomes = json.loads(OUTCOMES_FILE.read_text())

    # Get current metrics
    if not TRACKER_FILE.exists():
        print("No session metrics. Run 'record' first.")
        return

    data = json.loads(TRACKER_FILE.read_text())
    sessions = data.get("sessions", {})
    current_session = sessions.get(str(session_num), {})

    # Calculate efficiency metrics
    lessons_gain = 0
    principles_gain = 0
    frontier_resolved_gain = 0

    # Compare with previous session
    prev_sessions = [k for k in sessions.keys() if int(k) < session_num]
    if prev_sessions:
        prev_key = max(prev_sessions, key=int)
        prev_session = sessions[prev_key]

        lessons_gain = current_session.get("lessons_total", 0) - prev_session.get("lessons_total", 0)
        principles_gain = current_session.get("principles_total", 0) - prev_session.get("principles_total", 0)
        frontier_resolved_gain = current_session.get("frontier_resolved", 0) - prev_session.get("frontier_resolved", 0)

    # Calculate efficiency ratios
    commits = current_session.get("commits", 1)
    files_touched = current_session.get("files_touched", 1)

    outcome_data = {
        "session": session_num,
        "timestamp": subprocess.run(["date", "-Iseconds"], capture_output=True, text=True).stdout.strip(),
        "efficiency": {
            "lessons_per_commit": lessons_gain / max(commits, 1),
            "principles_per_commit": principles_gain / max(commits, 1),
            "knowledge_density": (lessons_gain + principles_gain) / max(files_touched, 1),
            "frontier_resolution_rate": frontier_resolved_gain / max(current_session.get("frontier_open", 1), 1)
        },
        "gains": {
            "lessons": lessons_gain,
            "principles": principles_gain,
            "frontier_resolved": frontier_resolved_gain
        },
        "session_type": classify_session_type(current_session, lessons_gain, principles_gain, frontier_resolved_gain),
        "elapsed_minutes": elapsed_minutes
    }

    # Add to outcomes
    outcomes["sessions"].append(outcome_data)

    # Keep only last 50 sessions
    if len(outcomes["sessions"]) > 50:
        outcomes["sessions"] = outcomes["sessions"][-50:]

    # Save outcomes
    OUTCOMES_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTCOMES_FILE.write_text(json.dumps(outcomes, indent=2))

    print(f"Session {session_num} outcome tracked: {outcome_data['session_type']}")
    print(f"  Lessons gain: {lessons_gain}, Principles gain: {principles_gain}")
    print(f"  Knowledge density: {outcome_data['efficiency']['knowledge_density']:.2f}")


def classify_session_type(session_data: dict, lessons_gain: int, principles_gain: int, frontier_resolved: int) -> str:
    """Classify session type based on behavioral patterns."""
    structural = session_data.get("structural_change", False)
    commits = session_data.get("commits", 0)
    files_touched = session_data.get("files_touched", 0)

    total_knowledge = lessons_gain + principles_gain

    if total_knowledge >= 3:
        return "BREAKTHROUGH"
    elif principles_gain > lessons_gain and principles_gain > 0:
        return "CONSOLIDATION"  # More principles than lessons = compaction
    elif lessons_gain > 2 and frontier_resolved > 0:
        return "EXPLOITATION"   # High lessons + frontier resolution
    elif session_data.get("frontier_open", 0) > frontier_resolved:
        return "EXPLORATION"    # More opening than resolving
    elif structural and total_knowledge == 0:
        return "MAINTENANCE"    # Structural changes without knowledge gain
    elif files_touched > commits * 3:
        return "THRASHING"      # High file churn relative to commits
    elif total_knowledge == 0:
        return "STALLED"        # No knowledge production
    else:
        return "BALANCED"       # Moderate progress across metrics


def learn_session_patterns():
    """Analyze session patterns for behavioral insights (--learn mode)."""
    if not OUTCOMES_FILE.exists():
        print("No session outcomes tracked. Run with session number first to track outcomes.")
        return

    outcomes = json.loads(OUTCOMES_FILE.read_text())
    sessions = outcomes.get("sessions", [])

    if len(sessions) < 3:
        print(f"Need at least 3 sessions for pattern analysis (have {len(sessions)}).")
        return

    print("=== SESSION PATTERN ANALYSIS ===\n")

    # Session type distribution
    type_counts = {}
    efficiency_by_type = {}

    for session in sessions:
        session_type = session.get("session_type", "UNKNOWN")
        type_counts[session_type] = type_counts.get(session_type, 0) + 1

        knowledge_density = session.get("efficiency", {}).get("knowledge_density", 0)
        if session_type not in efficiency_by_type:
            efficiency_by_type[session_type] = []
        efficiency_by_type[session_type].append(knowledge_density)

    print("## Session Type Distribution")
    for session_type, count in sorted(type_counts.items()):
        percentage = (count / len(sessions)) * 100
        avg_efficiency = sum(efficiency_by_type.get(session_type, [0])) / max(count, 1)
        print(f"  {session_type:<15}: {count:>3} sessions ({percentage:5.1f}%) - avg efficiency: {avg_efficiency:.2f}")

    # Efficiency trends
    recent_efficiency = [s.get("efficiency", {}).get("knowledge_density", 0) for s in sessions[-5:]]
    avg_recent = sum(recent_efficiency) / len(recent_efficiency)

    all_efficiency = [s.get("efficiency", {}).get("knowledge_density", 0) for s in sessions]
    avg_all = sum(all_efficiency) / len(all_efficiency)

    print(f"\n## Efficiency Trends")
    print(f"  Recent 5 sessions: {avg_recent:.2f} knowledge/file")
    print(f"  Overall average:   {avg_all:.2f} knowledge/file")
    trend = "IMPROVING" if avg_recent > avg_all * 1.1 else "DECLINING" if avg_recent < avg_all * 0.9 else "STABLE"
    print(f"  Trend: {trend}")

    # Pattern insights
    productive_types = ["BREAKTHROUGH", "EXPLOITATION", "CONSOLIDATION"]
    productive_count = sum(type_counts.get(t, 0) for t in productive_types)
    productive_rate = (productive_count / len(sessions)) * 100

    print(f"\n## Pattern Insights")
    print(f"  Productive sessions: {productive_rate:.1f}% (BREAKTHROUGH/EXPLOITATION/CONSOLIDATION)")

    # Recommendations
    print(f"\n## Recommendations")
    if type_counts.get("STALLED", 0) > len(sessions) * 0.2:
        print("  ⚠  High stall rate - consider dispatch optimization")
    if type_counts.get("THRASHING", 0) > len(sessions) * 0.15:
        print("  ⚠  High thrashing rate - consider focus discipline")
    if type_counts.get("EXPLORATION", 0) > type_counts.get("EXPLOITATION", 0) * 2:
        print("  📈 High exploration/exploitation ratio - consider frontier resolution focus")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "record":
        if len(sys.argv) < 3:
            print("Usage: session_tracker.py record <session-number>")
            sys.exit(1)
        session_num = int(sys.argv[2])
        record_session(session_num)
    elif cmd == "report":
        report()
    elif cmd == "lambda":
        calculate_lambda()
    elif cmd == "growth-rate":
        n = 30
        if "--n" in sys.argv:
            idx = sys.argv.index("--n")
            if idx + 1 < len(sys.argv):
                n = int(sys.argv[idx + 1])
        growth_rate(n)
    elif cmd == "trend":
        w = 5
        if "--window" in sys.argv:
            idx = sys.argv.index("--window")
            if idx + 1 < len(sys.argv):
                w = int(sys.argv[idx + 1])
        trend(w)
    elif cmd == "track":
        if len(sys.argv) < 3:
            print("Usage: session_tracker.py track <session-number> [--elapsed MINUTES]")
            sys.exit(1)
        session_num = int(sys.argv[2])
        elapsed_minutes = None
        if "--elapsed" in sys.argv:
            idx = sys.argv.index("--elapsed")
            if idx + 1 < len(sys.argv):
                elapsed_minutes = int(sys.argv[idx + 1])
        track_session_outcome(session_num, elapsed_minutes)
    elif cmd == "learn":
        learn_session_patterns()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
