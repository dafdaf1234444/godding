#!/usr/bin/env python3
"""
F-ACT1: Actionable Actions Recommender
Scores swarm state → ranked ACTION-BOARD.md for all members + human visibility.

Dimensions (each 0–3, max score 12):
  U = urgency   (maintenance DUE / proxy-K / lesson overruns)
  C = coverage  (how many active lanes are already on this)
  I = impact    (unlocks frontiers / cross-domain leverage)
  N = novelty   (not done in recent sessions)

Usage:
    python3 tools/f_act1_action_recommender.py          # write ACTION-BOARD.md
    python3 tools/f_act1_action_recommender.py --json   # JSON output
    python3 tools/f_act1_action_recommender.py --top N  # top N (default 15)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
WORKSPACE = REPO_ROOT / "workspace"
ACTION_BOARD = WORKSPACE / "ACTION-BOARD.md"
SWARM_LANES = REPO_ROOT / "tasks" / "SWARM-LANES.md"
FRONTIER_MD = REPO_ROOT / "tasks" / "FRONTIER.md"
NEXT_MD = REPO_ROOT / "tasks" / "NEXT.md"
PERIODICS = REPO_ROOT / "tools" / "periodics.json"
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
DOMAINS_DIR = REPO_ROOT / "domains"
PROXY_K_URGENT = 10.0
PROXY_K_DUE = 6.0


# ── helpers ────────────────────────────────────────────────────────────────

def _git_log(n: int = 20) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "log", f"-{n}", "--oneline"],
            text=True, stderr=subprocess.DEVNULL
        )
    except Exception:
        return ""


def _current_session() -> int:
    log = _git_log(5)
    m = re.search(r"\[S(\d+)\]", log)
    return int(m.group(1)) if m else 303


def _active_lanes() -> dict[str, int]:
    """Return {scope_key: active_lane_count} for all non-MERGED/ABANDONED lanes."""
    if not SWARM_LANES.exists():
        return {}
    text = SWARM_LANES.read_text(encoding="utf-8", errors="replace")
    counts: dict[str, int] = {}
    active_re = re.compile(r"ACTIVE|CLAIMED|READY|BLOCKED")
    for line in text.splitlines():
        if not line.startswith("| 20"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 12:
            continue
        status = parts[11] if len(parts) > 11 else ""
        if not active_re.search(status):
            continue
        scope_key = parts[9] if len(parts) > 9 else ""
        # extract all F-codes mentioned in scope_key or notes
        for code in re.findall(r"F-?[A-Z0-9]+\d*", scope_key + (parts[12] if len(parts) > 12 else "")):
            counts[code] = counts.get(code, 0) + 1
        # generic scope keys
        if scope_key:
            short = scope_key.split(";")[0].replace("domains/", "").replace("/tasks/FRONTIER.md", "")
            counts[short] = counts.get(short, 0) + 1
    return counts


def _proxy_k() -> float | None:
    """Return proxy-K drift % from compact.py --dry-run (authoritative health metric).

    Rationale: proxy_k.py outputs tier percentages (T0=11.5% of total), not a health
    score. compact.py --dry-run outputs 'Drift: +X.X% (healthy/urgent)' which is the
    intended metric: tokens above the compaction floor.
    """
    try:
        out = subprocess.check_output(
            ["python3", str(REPO_ROOT / "tools" / "compact.py"), "--dry-run"],
            text=True, stderr=subprocess.DEVNULL, cwd=str(REPO_ROOT)
        )
        m = re.search(r"Drift:\s*[+-]?([\d.]+)%", out)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return None


def _overlong_lessons() -> list[str]:
    names = []
    if LESSONS_DIR.exists():
        for f in sorted(LESSONS_DIR.glob("L-*.md")):
            lines = f.read_text(errors="replace").splitlines()
            if len(lines) > 20:
                names.append(f.name)
    return names


def _recent_commit_text() -> str:
    return _git_log(15)


def _periodics_due(current_session: int) -> list[dict]:
    """Return periodics items that are overdue."""
    if not PERIODICS.exists():
        return []
    data = json.loads(PERIODICS.read_text())
    due = []
    for item in data.get("items", []):
        cadence = item.get("cadence_sessions", 99)
        last = item.get("last_reviewed_session", 0)
        if current_session - last >= cadence:
            overdue_by = current_session - last - cadence
            item["overdue_by"] = overdue_by
            due.append(item)
    return due


def _open_frontiers() -> list[dict]:
    """Parse global FRONTIER.md for open items."""
    if not FRONTIER_MD.exists():
        return []
    text = FRONTIER_MD.read_text(errors="replace")
    open_text = text.split("## Archive", 1)[0]
    current_session = _current_session()
    frontiers = []
    for m in re.finditer(r"^- \*\*([^*]+)\*\*[:\s](.+?)(?=\n- \*\*|\Z)", open_text, re.MULTILINE | re.DOTALL):
        fid = m.group(1).strip()
        desc = m.group(2).strip().replace("\n", " ")[:120]
        # crude importance: critical > important > exploratory
        importance = 0
        pos = m.start()
        section_text = open_text[:pos]
        if "## Critical" in section_text:
            importance = 3
        elif "## Important" in section_text:
            importance = 2
        else:
            importance = 1
        # anxiety zone: last session mention >15 sessions ago → needs multi-expert
        body = m.group(2)
        s_nums = [int(x) for x in re.findall(r"\bS(\d+)\b", body)]
        last_active = max(s_nums) if s_nums else 0
        anxiety = last_active > 0 and (current_session - last_active) > 15
        frontiers.append({"id": fid, "desc": desc, "importance": importance,
                          "anxiety": anxiety, "last_active": last_active})
    return frontiers


@dataclass
class Action:
    id: str
    title: str
    reason: str
    u: int = 0  # urgency
    c: int = 0  # coverage gap (inverse: 3=no lanes, 0=many lanes)
    i: int = 0  # impact
    n: int = 0  # novelty
    staleness: int = 0  # sessions since last update (tiebreaker: higher = more urgent)
    tags: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        return self.u + self.c + self.i + self.n

    @property
    def score_str(self) -> str:
        return f"U{self.u}C{self.c}I{self.i}N{self.n}={self.score}"


# ── scoring ────────────────────────────────────────────────────────────────

def _coverage_score(active_lanes: dict[str, int], *keys: str) -> int:
    """Return 0-3 coverage gap: 3=nobody on it, 1=one lane, 0=two+ lanes."""
    total = sum(active_lanes.get(k, 0) for k in keys)
    if total == 0:
        return 3
    elif total == 1:
        return 1
    return 0


def _novelty_score(title_fragment: str, recent_log: str) -> int:
    """3 if not in last 15 commits, 1 if in last 5, 0 if very recent."""
    lower = title_fragment.lower()
    if lower in recent_log.lower():
        return 0
    return 3


def build_actions(top_n: int = 15) -> list[Action]:
    current_session = _current_session()
    active_lanes = _active_lanes()
    recent_log = _recent_commit_text()
    actions: list[Action] = []

    # 1. Proxy-K compaction
    pk = _proxy_k()
    if pk is not None:
        if pk >= PROXY_K_URGENT:
            actions.append(Action(
                id="compact-urgent",
                title=f"Run compact.py — proxy-K {pk:.1f}% (URGENT ≥{PROXY_K_URGENT}%)",
                reason="Knowledge corpus bloated beyond URGENT threshold; blocks learning quality.",
                u=3, c=_coverage_score(active_lanes, "compact", "proxy-k"), i=3,
                n=_novelty_score("compact", recent_log),
                tags=["maintenance", "URGENT"]
            ))
        elif pk >= PROXY_K_DUE:
            actions.append(Action(
                id="compact-due",
                title=f"Run compact.py — proxy-K {pk:.1f}% (DUE ≥{PROXY_K_DUE}%)",
                reason="Corpus past DUE threshold; compaction maintains learning fidelity.",
                u=2, c=_coverage_score(active_lanes, "compact", "proxy-k"), i=2,
                n=_novelty_score("compact", recent_log),
                tags=["maintenance"]
            ))

    # 2. Overlong lessons
    overlong = _overlong_lessons()
    if overlong:
        actions.append(Action(
            id="trim-lessons",
            title=f"Trim {len(overlong)} overlong lesson(s): {', '.join(overlong[:4])}",
            reason="Lessons >20 lines violate protocol; degrade compaction quality.",
            u=2, c=_coverage_score(active_lanes, "trim", "lesson"), i=1,
            n=3 if len(overlong) > 2 else 2,
            tags=["maintenance"]
        ))

    # 3. Periodics DUE
    due_items = _periodics_due(current_session)
    for item in sorted(due_items, key=lambda x: -x.get("overdue_by", 0))[:6]:
        pid = item["id"]
        overdue = item.get("overdue_by", 0)
        urgency = 3 if overdue > 20 else (2 if overdue > 10 else 1)
        actions.append(Action(
            id=f"periodic-{pid}",
            title=f"[periodic] {item['description'][:90]}",
            reason=f"Overdue by {overdue} sessions (cadence={item['cadence_sessions']}).",
            u=urgency,
            c=_coverage_score(active_lanes, pid, pid.replace("-", "_")),
            i=2,
            n=_novelty_score(pid, recent_log),
            tags=["periodic", "DUE"]
        ))

    # 4. Top domain experiments (dispatch_optimizer)
    try:
        out = subprocess.check_output(
            ["python3", str(REPO_ROOT / "tools" / "dispatch_optimizer.py"), "--json"],
            text=True, stderr=subprocess.DEVNULL, cwd=str(REPO_ROOT)
        )
        top_domains = json.loads(out)[:5]
        for d in top_domains:
            domain = d["domain"]
            fid = re.search(r"F-?[A-Z0-9_-]+", d.get("top_frontier", ""))
            fid_str = fid.group(0) if fid else f"F-{domain.upper()[:4]}1"
            cov = _coverage_score(active_lanes, domain, fid_str)
            actions.append(Action(
                id=f"domain-{domain}",
                title=f"Domain experiment: {domain}/{fid_str} (score={d['score']:.1f})",
                reason=d.get("top_frontier", "")[:100],
                u=1,
                c=cov,
                i=min(3, int(d["score"] / 10)),
                n=_novelty_score(domain, recent_log),
                tags=["experiment", domain]
            ))
    except Exception:
        pass

    # 5. Open global frontiers (critical ones with no coverage)
    for f in _open_frontiers():
        if f["importance"] < 2:
            continue
        fid = f["id"]
        cov = _coverage_score(active_lanes, fid, fid.lower())
        if cov < 2:
            continue  # already covered
        staleness = current_session - f.get("last_active", current_session)
        # Graduated urgency: anxiety zones differentiated by staleness
        if f.get("anxiety"):
            u = 3 if staleness > 150 else (2 if staleness > 80 else 1)
        else:
            u = f["importance"] - 1
        # Graduated novelty: use staleness instead of binary commit-log match
        n = 3 if staleness > 150 else (2 if staleness > 80 else (1 if staleness > 30 else 0))
        anxiety_tag = ["anxiety-zone"] if f.get("anxiety") else []
        actions.append(Action(
            id=f"frontier-{fid}",
            title=f"Advance frontier {fid}" + (" [ANXIETY ZONE]" if f.get("anxiety") else ""),
            reason=f["desc"],
            u=u,
            c=cov,
            i=f["importance"],
            n=n,
            staleness=staleness,
            tags=["frontier"] + anxiety_tag
        ))

    # 6. Stale lane cleanup (>36 stale is a known maintenance issue)
    stale_count = _count_stale_lanes()
    if stale_count > 10:
        actions.append(Action(
            id="lane-cleanup",
            title=f"Abandon/archive {stale_count} stale lanes (>3 sessions inactive)",
            reason="Stale lanes pollute orient output and inflate coordination overhead.",
            u=2 if stale_count > 30 else 1,
            c=_coverage_score(active_lanes, "lane-cleanup", "stale"),
            i=2,
            n=_novelty_score("lane-sweep", recent_log),
            tags=["maintenance", "lanes"]
        ))

    # Sort: score desc, urgency desc, staleness desc (tiebreaker — most ignored first)
    actions.sort(key=lambda a: (-a.score, -a.u, -a.staleness))
    # Deduplicate by id
    seen: set[str] = set()
    unique: list[Action] = []
    for a in actions:
        if a.id not in seen:
            seen.add(a.id)
            unique.append(a)
    return unique[:top_n]


def _count_stale_lanes() -> int:
    if not SWARM_LANES.exists():
        return 0
    current = _current_session()
    text = SWARM_LANES.read_text(errors="replace")
    stale = 0
    active_re = re.compile(r"ACTIVE|CLAIMED|READY|BLOCKED")
    for line in text.splitlines():
        if not line.startswith("| 20"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 12:
            continue
        status = parts[11] if len(parts) > 11 else ""
        if not active_re.search(status):
            continue
        session_str = parts[3] if len(parts) > 3 else ""
        m = re.search(r"S(\d+)", session_str)
        if m and current - int(m.group(1)) > 3:
            stale += 1
    return stale


# ── output ─────────────────────────────────────────────────────────────────

def render_board(actions: list[Action], session: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    lines = [
        "# ACTION BOARD",
        f"Updated: {now} S{session} | auto-generated by f_act1_action_recommender.py",
        "",
        "Score = U(rgency)+C(overage-gap)+I(mpact)+N(ovelty), max=12. Higher = do first.",
        "C=3 means nobody's working on it. U=3 means URGENT.",
        "",
        f"| Rank | Score | Tags | Action | Why |",
        f"|------|-------|------|--------|-----|",
    ]
    for i, a in enumerate(actions, 1):
        tags = " ".join(f"`{t}`" for t in a.tags[:3])
        title_safe = a.title.replace("|", "∣")
        reason_safe = a.reason.replace("|", "∣")[:100]
        lines.append(f"| {i} | {a.score_str} | {tags} | {title_safe} | {reason_safe} |")

    lines += [
        "",
        "## Top 5 expanded",
        "",
    ]
    for a in actions[:5]:
        lines += [
            f"### {a.score}/12 — {a.title}",
            f"- **Score**: U={a.u} urgency, C={a.c} coverage-gap, I={a.i} impact, N={a.n} novelty",
            f"- **Why**: {a.reason}",
            f"- **Tags**: {', '.join(a.tags)}",
            "",
        ]

    lines += [
        "---",
        "_This file is swarm-generated. Swarm nodes consume it at session start. Concurrent sessions update it._",
        "_Human: check top rows each session to see what the swarm is prioritizing._",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="F-ACT1 action recommender")
    parser.add_argument("--json", action="store_true", help="JSON output to stdout")
    parser.add_argument("--top", type=int, default=15, help="Number of actions (default 15)")
    parser.add_argument("--dry-run", action="store_true", help="Print board without writing file")
    args = parser.parse_args()

    session = _current_session()
    actions = build_actions(args.top)

    if args.json:
        print(json.dumps([
            {"rank": i + 1, "id": a.id, "score": a.score, "score_str": a.score_str,
             "title": a.title, "reason": a.reason, "tags": a.tags,
             "u": a.u, "c": a.c, "i": a.i, "n": a.n}
            for i, a in enumerate(actions)
        ], indent=2))
        return

    board = render_board(actions, session)

    if args.dry_run:
        print(board)
        return

    WORKSPACE.mkdir(exist_ok=True)
    ACTION_BOARD.write_text(board, encoding="utf-8")
    print(f"[f_act1] ACTION-BOARD.md written: {len(actions)} actions ranked, session S{session}")
    print(f"[f_act1] Top action: {actions[0].title}" if actions else "[f_act1] No actions found")


if __name__ == "__main__":
    main()
