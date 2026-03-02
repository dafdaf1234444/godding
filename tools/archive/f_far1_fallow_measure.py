#!/usr/bin/env python3
"""
f_far1_fallow_measure.py — F-FAR1 Fallow Principle Baseline

Tests whether domains skipped for 1+ sessions before re-swarming produce
higher-Sharpe lessons than continuously-worked domains.

Design:
  1. Tag each lesson with domain + session (from lesson metadata)
  2. Build domain-session activity history from SWARM-LANES.md
  3. Classify each lesson as "post_fallow" (domain had 0 activity in prior
     FALLOW_WINDOW sessions) or "continuous" (domain had ≥1 activity)
  4. Compute mean Sharpe for each group
  5. Test if post-fallow mean > continuous mean (>10% uplift = CONFIRMED)

Output: experiments/farming/f-far1-fallow-measure-s189.json
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).parent.parent
ARTIFACT_PATH = ROOT / "experiments" / "farming" / "f-far1-fallow-measure-s189.json"
FALLOW_WINDOW = 3  # sessions to look back for domain activity
UPLIFT_THRESHOLD = 0.10  # 10% uplift to confirm fallow hypothesis

# Normalize common domain name variants to canonical form
DOMAIN_ALIASES = {
    "nk complexity": "nk-complexity",
    "nk-complexity": "nk-complexity",
    "nk": "nk-complexity",
    "distributed systems": "distributed-systems",
    "distributed-systems": "distributed-systems",
    "information-science": "information-science",
    "information science": "information-science",
    "operations-research": "operations-research",
    "operations research": "operations-research",
    "game-theory": "game-theory",
    "game theory": "game-theory",
    "control-theory": "control-theory",
    "control theory": "control-theory",
    "helper-swarm": "helper-swarm",
    "helper swarm": "helper-swarm",
    "protocol-engineering": "protocol-engineering",
    "protocol engineering": "protocol-engineering",
    "meta": "meta",
    "ai": "ai",
    "brain": "brain",
    "conflict": "conflict",
    "economy": "economy",
    "evolution": "evolution",
    "finance": "finance",
    "fractals": "fractals",
    "gaming": "gaming",
    "governance": "governance",
    "health": "health",
    "history": "history",
    "linguistics": "linguistics",
    "physics": "physics",
    "psychology": "psychology",
    "statistics": "statistics",
    "strategy": "strategy",
    "farming": "farming",
    "quality": "quality",
    "tooling": "tooling",
    "compaction": "tooling",
    "safety": "meta",
    "knowledge-lifecycle": "meta",
    "knowledge-structure": "meta",
    "knowledge-management": "quality",
    "swarm-structure": "meta",
    "swarm-behavior": "meta",
    "coordination": "meta",
    "cross-swarm": "meta",
    "isomorphism": "meta",
    "frontier-design": "meta",
    "multi-tool": "meta",
    "wsl": "meta",
}


def _normalize_domain(raw: str) -> str | None:
    """Normalize raw domain string to canonical form, taking primary domain."""
    # Remove parenthetical notes: "health (F-HLT1)" → "health"
    raw = re.sub(r"\([^)]*\)", "", raw).strip()
    # Take primary domain before / or | or ,
    primary = re.split(r"[/|,]", raw)[0].strip().lower()
    return DOMAIN_ALIASES.get(primary)


def _compute_sharpe(text: str) -> float:
    """Compute Sharpe proxy: citation density per non-empty line."""
    citations = len(re.findall(r"\b[FLPB]-\d+\b|\bF-[A-Z]+\d+\b", text))
    lines = sum(1 for ln in text.splitlines() if ln.strip())
    return citations / lines if lines > 0 else 0.0


def _parse_lessons(lessons_dir: Path) -> list[dict]:
    """
    Parse all lessons for session, domain, and Sharpe.
    Only returns lessons with both session number and normalized domain.
    """
    results = []
    for lesson_file in sorted(lessons_dir.glob("L-*.md")):
        text = lesson_file.read_text(encoding="utf-8", errors="ignore")

        # Session number: "Session: S82" or "Session: 41"
        sm = re.search(r"Session:\s*S?(\d+)", text, re.IGNORECASE)
        if not sm:
            continue
        session = int(sm.group(1))

        # Domain field
        dm = re.search(r"Domain:\s*([^\n|]+)", text)
        if not dm:
            continue
        domain = _normalize_domain(dm.group(1).strip())
        if not domain:
            continue

        sharpe = _compute_sharpe(text)
        results.append({
            "file": lesson_file.name,
            "session": session,
            "domain": domain,
            "sharpe": round(sharpe, 4),
        })
    return results


def _parse_swarm_lanes() -> list[dict]:
    """Extract (session, domain) from SWARM-LANES.md focus tags."""
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    if not lanes_path.exists():
        return []
    lanes = []
    for line in lanes_path.read_text(encoding="utf-8").splitlines():
        m = re.search(r"focus=domains/([^,\s|]+)", line)
        s = re.search(r"\|\s*S(\d+)\s*\|", line)
        if m and s:
            raw_domain = m.group(1)
            norm = _normalize_domain(raw_domain) or raw_domain
            lanes.append({"session": int(s.group(1)), "domain": norm})
    return lanes


def _build_domain_activity(lanes: list[dict]) -> dict:
    """Build domain → set[session] activity map."""
    activity: dict = defaultdict(set)
    for lane in lanes:
        activity[lane["domain"]].add(lane["session"])
    return dict(activity)


def _classify_fallow(lesson: dict, domain_activity: dict, window: int) -> str:
    """
    Classify lesson as 'post_fallow' or 'continuous'.
    Post-fallow: domain had 0 activity in [session-window, ..., session-1].
    """
    session = lesson["session"]
    domain = lesson["domain"]
    prior = set(range(max(1, session - window), session))
    active = domain_activity.get(domain, set())
    return "post_fallow" if not (prior & active) else "continuous"


def run() -> dict:
    lessons_dir = ROOT / "memory" / "lessons"
    lessons = _parse_lessons(lessons_dir)

    lanes = _parse_swarm_lanes()
    domain_activity = _build_domain_activity(lanes)

    # Classify and annotate each lesson
    post_fallow_lessons = []
    continuous_lessons = []
    for lesson in lessons:
        cls = _classify_fallow(lesson, domain_activity, FALLOW_WINDOW)
        lesson["classification"] = cls
        if cls == "post_fallow":
            post_fallow_lessons.append(lesson)
        else:
            continuous_lessons.append(lesson)

    pf_sharpes = [l["sharpe"] for l in post_fallow_lessons]
    cont_sharpes = [l["sharpe"] for l in continuous_lessons]

    pf_mean = round(mean(pf_sharpes), 4) if pf_sharpes else None
    cont_mean = round(mean(cont_sharpes), 4) if cont_sharpes else None

    uplift = None
    if pf_mean is not None and cont_mean is not None and cont_mean > 0:
        uplift = round((pf_mean - cont_mean) / cont_mean, 4)

    if uplift is None or len(pf_sharpes) < 3 or len(cont_sharpes) < 3:
        verdict = "INSUFFICIENT_DATA"
    elif uplift > UPLIFT_THRESHOLD:
        verdict = "FALLOW_CONFIRMED"
    elif uplift < -UPLIFT_THRESHOLD:
        verdict = "FALLOW_REFUTED"
    else:
        verdict = "INCONCLUSIVE"

    # Per-domain breakdown
    domain_stats: dict = defaultdict(lambda: {"post_fallow": [], "continuous": []})
    for lesson in lessons:
        domain_stats[lesson["domain"]][lesson["classification"]].append(lesson["sharpe"])

    domain_breakdown = {}
    for domain, groups in sorted(domain_stats.items()):
        pf = groups["post_fallow"]
        cont = groups["continuous"]
        domain_breakdown[domain] = {
            "post_fallow_n": len(pf),
            "continuous_n": len(cont),
            "post_fallow_mean": round(mean(pf), 4) if pf else None,
            "continuous_mean": round(mean(cont), 4) if cont else None,
        }

    # --- Confound analysis: repeat with only sessions where lane data exists ---
    # SWARM-LANES.md coverage begins ~S182; pre-S182 lessons default to post_fallow
    # (no prior lane entries). Recent-only slice removes this artifact.
    lane_sessions = {l["session"] for l in lanes}
    min_lane_session = min(lane_sessions) if lane_sessions else 0
    recent_lessons = [l for l in lessons if l["session"] >= min_lane_session]

    recent_pf = [l for l in recent_lessons if l["classification"] == "post_fallow"]
    recent_cont = [l for l in recent_lessons if l["classification"] == "continuous"]
    recent_pf_sharpes = [l["sharpe"] for l in recent_pf]
    recent_cont_sharpes = [l["sharpe"] for l in recent_cont]

    recent_pf_mean = round(mean(recent_pf_sharpes), 4) if recent_pf_sharpes else None
    recent_cont_mean = round(mean(recent_cont_sharpes), 4) if recent_cont_sharpes else None
    recent_uplift = None
    if recent_pf_mean is not None and recent_cont_mean is not None and recent_cont_mean > 0:
        recent_uplift = round((recent_pf_mean - recent_cont_mean) / recent_cont_mean, 4)

    if recent_uplift is None or len(recent_pf_sharpes) < 3 or len(recent_cont_sharpes) < 3:
        recent_verdict = "INSUFFICIENT_DATA"
    elif recent_uplift > UPLIFT_THRESHOLD:
        recent_verdict = "FALLOW_CONFIRMED"
    elif recent_uplift < -UPLIFT_THRESHOLD:
        recent_verdict = "FALLOW_REFUTED"
    else:
        recent_verdict = "INCONCLUSIVE"

    return {
        "session": "S189",
        "fallow_window": FALLOW_WINDOW,
        "uplift_threshold": UPLIFT_THRESHOLD,
        "total_lessons_with_domain": len(lessons),
        "post_fallow_n": len(post_fallow_lessons),
        "continuous_n": len(continuous_lessons),
        "post_fallow_mean_sharpe": pf_mean,
        "continuous_mean_sharpe": cont_mean,
        "sharpe_uplift": uplift,
        "uplift_pct": round(uplift * 100, 1) if uplift is not None else None,
        "verdict": verdict,
        "confound_note": (
            "Pre-lane-era lessons (before min lane session) default to post_fallow. "
            "See recent_only_* fields for confound-corrected estimate."
        ),
        "min_lane_session": min_lane_session,
        "recent_only": {
            "min_session": min_lane_session,
            "total_lessons": len(recent_lessons),
            "post_fallow_n": len(recent_pf),
            "continuous_n": len(recent_cont),
            "post_fallow_mean_sharpe": recent_pf_mean,
            "continuous_mean_sharpe": recent_cont_mean,
            "sharpe_uplift": recent_uplift,
            "uplift_pct": round(recent_uplift * 100, 1) if recent_uplift is not None else None,
            "verdict": recent_verdict,
        },
        "domain_breakdown": domain_breakdown,
        "lesson_count_by_domain": {
            d: len(v["post_fallow"]) + len(v["continuous"])
            for d, v in domain_stats.items()
        },
        "lessons": lessons,
    }


if __name__ == "__main__":
    result = run()
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("=== F-FAR1 Fallow Principle Baseline ===")
    print(f"Lessons with domain tags: {result['total_lessons_with_domain']}")
    print(f"Post-fallow: {result['post_fallow_n']} | Continuous: {result['continuous_n']}")
    if result["post_fallow_mean_sharpe"] is not None:
        print(f"Post-fallow mean Sharpe:  {result['post_fallow_mean_sharpe']}")
        print(f"Continuous mean Sharpe:   {result['continuous_mean_sharpe']}")
        pct = result["uplift_pct"]
        print(f"Uplift: {pct:+.1f}% → Verdict: {result['verdict']}")
    else:
        print(f"Verdict: {result['verdict']}")
    print(f"\nDomain breakdown (n lessons):")
    for d, n in sorted(result["lesson_count_by_domain"].items(), key=lambda x: -x[1]):
        print(f"  {d}: {n}")
    rc = result["recent_only"]
    print(f"\nRecent-only (S{rc['min_session']}+, confound-corrected):")
    print(f"  Post-fallow: {rc['post_fallow_n']} | Continuous: {rc['continuous_n']}")
    if rc["post_fallow_mean_sharpe"] is not None:
        print(f"  Post-fallow mean Sharpe:  {rc['post_fallow_mean_sharpe']}")
        print(f"  Continuous mean Sharpe:   {rc['continuous_mean_sharpe']}")
        pct = rc["uplift_pct"]
        print(f"  Uplift: {pct:+.1f}% → Verdict: {rc['verdict']}")
    else:
        print(f"  Verdict: {rc['verdict']}")
    print(f"\nArtifact written: {ARTIFACT_PATH}")
