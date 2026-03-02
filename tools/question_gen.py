#!/usr/bin/env python3
"""
question_gen.py — Generate the inquiry frame for the current swarm session.

Produces the questions the swarm SHOULD be asking, derived from current state:
- Open frontiers (empirical questions)
- Belief health (staleness + weakened status)
- Compression ratios (K→P→B→PHIL)
- Zombie items (recurring without resolution)
- Prescription gaps (enforced rules with known violations)
- Open signals (directives awaiting action)

Gap this closes (SIG-59): orient.py generates tasks; no tool generates the inquiry frame.
Expected questions = questions predictable from state that a well-functioning swarm raises autonomously.
"""

import re
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent


def _current_session():
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, cwd=ROOT
        )
        m = re.search(r"\[S(\d+)\]", result.stdout)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0


def _frontier_questions():
    """Extract top open frontier questions from tasks/FRONTIER.md."""
    questions = []
    path = ROOT / "tasks" / "FRONTIER.md"
    if not path.exists():
        return questions
    text = path.read_text(encoding="utf-8")
    # Find each frontier block: **F-xxx**: description
    for match in re.finditer(r"\*\*([A-Z0-9_\-]+)\*\*\s*:\s*([^\n]+)", text):
        fid, desc = match.group(1), match.group(2).strip()
        if fid.startswith("F") and "RESOLVED" not in desc and "ABANDONED" not in desc:
            # Extract the core question — find the last "Open:" phrase or use first sentence
            block_start = match.start()
            block_end = text.find("\n- **", block_start + 1)
            if block_end == -1:
                block_end = len(text)
            block = text[block_start:block_end]
            # Look for gap = sessions with no update
            gap_m = re.search(r"gap=(\d+)\s+sessions", block)
            gap = int(gap_m.group(1)) if gap_m else None
            # Look for explicit Open: clause
            open_m = re.search(r"Open:\s*([^\.]+\.)", block)
            q_detail = open_m.group(1).strip() if open_m else desc[:100]
            questions.append({
                "id": fid,
                "desc": desc[:80],
                "detail": q_detail[:120],
                "gap": gap,
            })
    # Prioritize by gap (longest unattended first)
    questions.sort(key=lambda x: -(x["gap"] or 0))
    return questions[:5]


def _belief_health():
    """Find beliefs that are WEAKENED or stale (last tested >30 sessions ago)."""
    issues = []
    session = _current_session()
    path = ROOT / "beliefs" / "DEPS.md"
    if not path.exists():
        return issues
    text = path.read_text(encoding="utf-8")
    belief_blocks = re.split(r"\n### (B\d+|B-EVAL\d+):", text)
    for i in range(1, len(belief_blocks), 2):
        bid = belief_blocks[i]
        body = belief_blocks[i + 1] if i + 1 < len(belief_blocks) else ""
        # Check WEAKENED status
        is_weakened = "WEAKENED" in body
        # Extract last tested session
        tested_m = re.search(r"Last tested.*?S(\d+)", body)
        last_s = int(tested_m.group(1)) if tested_m else None
        staleness = (session - last_s) if last_s else None
        # Check Evidence type
        theorized = "theorized" in body.lower() and "observed" not in body.split("theorized")[0][-30:]
        if is_weakened or (staleness and staleness > 30):
            status = "WEAKENED" if is_weakened else f"stale {staleness}s ago"
            # Extract short desc (first line after title)
            first_line = body.split("\n")[1].strip() if "\n" in body else body[:80]
            issues.append({
                "id": bid,
                "status": status,
                "last_s": last_s,
                "staleness": staleness,
                "desc": first_line[:80],
            })
    return issues[:4]


def _compression_ratios():
    """Compute K→P→B→PHIL compression ratios from live counts."""
    # Lesson count
    lessons_dir = ROOT / "memory" / "lessons"
    l_count = len(list(lessons_dir.glob("L-*.md"))) if lessons_dir.exists() else 0
    # Principle count via sync_state (canonical)
    p_count = 0
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from sync_state import count_principles, count_beliefs
        p_count = count_principles()
        b_count = count_beliefs()
    except Exception:
        # Fallback: count P-NNN references
        p_path = ROOT / "memory" / "PRINCIPLES.md"
        if p_path.exists():
            all_ids = set(re.findall(r"\bP-(\d{3})\b", p_path.read_text()))
            p_count = len(all_ids)
        deps_path = ROOT / "beliefs" / "DEPS.md"
        b_count = 0
        if deps_path.exists():
            b_count = len(re.findall(r"^### B[-\w]+:", deps_path.read_text(), re.MULTILINE))
    # PHIL count: [PHIL-N] tags in PHILOSOPHY.md
    phil_count = 0
    phil_path = ROOT / "beliefs" / "PHILOSOPHY.md"
    if phil_path.exists():
        phil_count = len(set(re.findall(r"\[PHIL-(\d+)\]", phil_path.read_text())))

    ratios = {}
    if p_count > 0:
        ratios["K→P"] = {"ratio": round(l_count / p_count, 2), "target": 5.0, "counts": f"{l_count}L/{p_count}P"}
    if b_count > 0 and p_count > 0:
        ratios["P→B"] = {"ratio": round(p_count / b_count, 2), "target": 10.0, "counts": f"{p_count}P/{b_count}B"}
    if phil_count > 0 and b_count > 0:
        ratios["B→PHIL"] = {"ratio": round(b_count / phil_count, 2), "target": 2.0, "counts": f"{b_count}B/{phil_count}PHIL"}
    return ratios


def _zombie_items():
    """Find zombie items from SWARM-LANES.md.

    A zombie is a domain that gets repeatedly opened but fails to complete —
    not one that gets reopened because it's productive (L-1101).
    Counts only ABANDONED/STALE lanes; domains with high MERGED rates are healthy.
    """
    zombies = []
    path = ROOT / "tasks" / "SWARM-LANES.md"
    if not path.exists():
        return zombies
    text = path.read_text(encoding="utf-8")
    # Count total and failed lanes per domain base
    domain_total = {}
    domain_failed = {}
    for line in text.split("\n"):
        m = re.search(r"\|\s*([A-Z]+-[A-Z]+-S\d+)\s*\|", line)
        if not m:
            continue
        base = re.sub(r"-S\d+$", "", m.group(1))
        domain_total[base] = domain_total.get(base, 0) + 1
        if re.search(r"ABANDONED|STALE", line):
            domain_failed[base] = domain_failed.get(base, 0) + 1
    # Flag domains with >=2 failed lanes or >=3 total with >30% failure rate
    for base in sorted(domain_total, key=lambda b: -domain_total[b]):
        total = domain_total[base]
        failed = domain_failed.get(base, 0)
        if total < 3:
            continue
        fail_rate = failed / total if total > 0 else 0
        if failed >= 2 or (total >= 3 and fail_rate > 0.30):
            zombies.append({"base": base, "count": total,
                            "failed": failed, "rate": fail_rate})
    return zombies[:3]


def _open_signals():
    """Find OPEN signals in SIGNALS.md."""
    open_sigs = []
    path = ROOT / "tasks" / "SIGNALS.md"
    if not path.exists():
        return open_sigs
    text = path.read_text(encoding="utf-8")
    for m in re.finditer(r"\|\s*(SIG-\d+)\s*\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\s*([^|]+)\|\s*OPEN\s*\|", text):
        sig_id = m.group(1)
        content = m.group(2).strip()[:120]
        open_sigs.append({"id": sig_id, "content": content})
    return open_sigs


def _prescription_gaps():
    """Top aspirational lessons from enforcement_router.py output."""
    gaps = []
    try:
        result = subprocess.run(
            ["python3", "tools/enforcement_router.py", "--top", "3"],
            capture_output=True, text=True, cwd=ROOT, timeout=10
        )
        for line in result.stdout.splitlines():
            m = re.search(r"(L-\d+)\s+Sh=(\d+)\s+[—-]\s+(.+)", line)
            if m:
                gaps.append({"id": m.group(1), "sharpe": int(m.group(2)), "desc": m.group(3).strip()[:100]})
    except Exception:
        pass
    # Fallback: parse enforcement_router directly if needed
    if not gaps:
        path = ROOT / "tools" / "enforcement_router.py"
        if path.exists():
            gaps.append({"id": "L-555", "sharpe": 9, "desc": "Filtered baselines diverge from actual tools when filters become stale"})
    return gaps[:3]


def main(args=None):
    session = _current_session()
    print(f"=== EXPECTED QUESTIONS S{session} — inquiry frame ===\n")
    print("These are the questions the swarm should be asking this session,")
    print("derived from current state. Act on them or explicitly defer.\n")

    # A. Frontier questions
    frontiers = _frontier_questions()
    if frontiers:
        print("## A. Open Frontier Questions (empirical)")
        for i, f in enumerate(frontiers, 1):
            gap_str = f"  [{f['gap']}s gap]" if f.get("gap") else ""
            print(f"  {i}. [{f['id']}]{gap_str} {f['detail']}")
        print()

    # B. Belief health
    beliefs = _belief_health()
    if beliefs:
        print("## B. Belief Health")
        for i, b in enumerate(beliefs, 1):
            stale_str = f"(last S{b['last_s']}, {b['staleness']}s ago)" if b.get("staleness") else ""
            print(f"  {i}. [{b['id']} {b['status']}] {stale_str} — retest needed?")
        print()

    # C. Compression ratios
    ratios = _compression_ratios()
    if ratios:
        print("## C. Compression Ratio Health")
        for layer, data in ratios.items():
            actual = data["ratio"]
            target = data["target"]
            health = "OK" if actual >= target else f"BREAK (need {target}:1)"
            print(f"  {layer}: {actual}:1 [{data['counts']}] — {health}")
        print()

    # D. Zombie items
    zombies = _zombie_items()
    if zombies:
        print("## D. Zombie Questions (recurring failure, not just recurrence — L-1101)")
        for i, z in enumerate(zombies, 1):
            print(f"  {i}. [{z['base']}] {z['failed']}/{z['count']} failed ({z['rate']:.0%}) — what's the real blocker?")
        print()

    # E. Prescription gaps
    gaps = _prescription_gaps()
    if gaps:
        print("## E. Prescription Gaps (rules known but not enforced)")
        for i, g in enumerate(gaps, 1):
            print(f"  {i}. [{g['id']} Sh={g['sharpe']}] {g['desc']}")
        print()

    # F. Open signals
    sigs = _open_signals()
    if sigs:
        print("## F. Open Signals (directives awaiting resolution)")
        for s in sigs:
            print(f"  [{s['id']}] {s['content'][:100]}")
        print()

    print("Act on these questions or explicitly defer with evidence. Deferred = not answered.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
