#!/usr/bin/env python3
"""
farming_expert.py — Swarm Farming Analyst

Models swarm knowledge production through the farming lens:
  seed → grow → harvest → compost → fallow → rotate → pollinate

Computes:
  1. Domain coverage map: which domains are active, stale, or overworked
  2. Rotation health: HHI concentration index over recent sessions (F-FAR3)
  3. Fallow candidates: domains with no recent sessions (F-FAR1)
  4. Companion pairs: domains with mutual cross-citations (F-FAR2)
  5. Compost status: Sharpe health and zero-Sharpe backlog

Usage:
  python3 tools/farming_expert.py          # human-readable report
  python3 tools/farming_expert.py --json   # machine-readable JSON
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Domain session coverage
# ---------------------------------------------------------------------------

KNOWN_DOMAINS = [
    "ai", "brain", "conflict", "control-theory", "distributed-systems",
    "economy", "evolution", "experiments", "finance", "fractals", "game-theory",
    "gaming", "governance", "health", "helper-swarm", "history",
    "information-science", "linguistics", "meta", "nk-complexity",
    "operations-research", "physics", "protocol-engineering", "psychology",
    "statistics", "strategy", "farming",
]

DOMAIN_CROP = {
    "economy": "wheat (staple grain — foundational production model)",
    "statistics": "legumes (fixes soil for other crops)",
    "operations-research": "corn (high throughput, scheduler infrastructure)",
    "ai": "soybeans (versatile; cross-domain protein)",
    "evolution": "perennial grass (self-seeding, long timescale)",
    "brain": "root vegetables (slow-growing, deep substrate)",
    "game-theory": "fruit trees (coordination payoff takes seasons)",
    "information-science": "herbs (dense, small-batch high-value)",
    "farming": "cover crop (improves soil for all other domains)",
}


def _parse_session_log() -> list[dict]:
    """Extract per-session data from SESSION-LOG.md."""
    log_path = ROOT / "memory" / "SESSION-LOG.md"
    if not log_path.exists():
        return []
    sessions = []
    pat = re.compile(r"S(\d+)\s*[\t|].*?\+(\d+)L.*?\+(\d+)P")
    for line in log_path.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m:
            sessions.append({
                "session": int(m.group(1)),
                "lessons": int(m.group(2)),
                "principles": int(m.group(3)),
                "raw": line.strip(),
            })
    return sorted(sessions, key=lambda s: s["session"])


def _parse_swarm_lanes() -> list[dict]:
    """Extract domain focus tags from SWARM-LANES.md."""
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    if not lanes_path.exists():
        return []
    lanes = []
    for line in lanes_path.read_text(encoding="utf-8").splitlines():
        m = re.search(r"focus=domains/([a-z0-9-]+)", line, re.I)
        s = re.search(r"\|\s*S(\d+)\s*\|", line)
        if m and s:
            domain = m.group(1).lower()
            lanes.append({"session": int(s.group(1)), "domain": domain})
    return lanes


def compute_rotation_health(lanes: list[dict], window: int = 10) -> dict:
    """
    Compute HHI (Herfindahl-Hirschman Index) for domain concentration.
    HHI = sum of squared market shares. Range [0,1].
    HHI > 0.4 = monoculture alert (one domain dominates).
    HHI < 0.15 = healthy diversification.
    """
    recent = [l["domain"] for l in lanes[-window:]] if lanes else []
    if not recent:
        return {"hhi": None, "window": window, "domain_shares": {}, "status": "NO_DATA"}

    counts = Counter(recent)
    total = len(recent)
    shares = {d: c / total for d, c in counts.items()}
    hhi = sum(s ** 2 for s in shares.values())

    if hhi > 0.4:
        status = "MONOCULTURE_ALERT"
    elif hhi > 0.25:
        status = "MODERATE_CONCENTRATION"
    else:
        status = "HEALTHY_ROTATION"

    return {
        "hhi": round(hhi, 4),
        "window": window,
        "total_lanes": total,
        "domain_shares": {d: round(s, 3) for d, s in sorted(shares.items(), key=lambda x: -x[1])},
        "dominant_domain": max(shares, key=shares.get) if shares else None,
        "status": status,
    }


def compute_fallow_candidates(lanes: list[dict], stale_threshold: int = 3) -> list[dict]:
    """
    Identify domains that haven't had a session in stale_threshold recent lanes.
    These are fallow candidates — may yield higher Sharpe if re-swarmed (B-FAR2).
    """
    if not lanes:
        return []
    recent_sessions = {l["domain"] for l in lanes[-stale_threshold:]}
    all_active = {l["domain"] for l in lanes}
    fallow = []
    for domain in sorted(all_active - recent_sessions):
        last = max((l["session"] for l in lanes if l["domain"] == domain), default=0)
        fallow.append({"domain": domain, "last_session": last, "fallow_periods": stale_threshold})
    return sorted(fallow, key=lambda x: x["last_session"])


def compute_companion_pairs(lessons_dir: Path) -> list[dict]:
    """
    Scan lesson files for cross-domain citations (F-FAR2).
    Domain prefix = first segment of frontier ID (e.g. F-ECO → economy, F-BRN → brain).
    Returns domain pairs sorted by co-citation count.
    """
    prefix_to_domain = {
        "ECO": "economy", "BRN": "brain", "AI": "ai", "EVO": "evolution",
        "GAM": "game-theory", "FIN": "finance", "IS": "information-science",
        "STAT": "statistics", "OPS": "operations-research", "CTL": "control-theory",
        "HLP": "helper-swarm", "META": "meta", "FAR": "farming",
        "CON": "conflict", "GVN": "governance", "PHY": "physics",
        "PSY": "psychology", "LING": "linguistics", "HIST": "history",
        "NK": "nk-complexity", "DS": "distributed-systems", "FRAC": "fractals",
        "STRAT": "strategy", "HEAL": "health", "GAME": "gaming",
    }
    co_citations: Counter = Counter()
    domain_citations: dict[str, set] = defaultdict(set)

    if not lessons_dir.exists():
        return []

    for lesson_file in lessons_dir.glob("L-*.md"):
        text = lesson_file.read_text(encoding="utf-8", errors="ignore")
        found_domains: set[str] = set()
        for prefix, domain in prefix_to_domain.items():
            if re.search(rf"\bF-{prefix}\d", text):
                found_domains.add(domain)
        for d in found_domains:
            domain_citations[d].add(lesson_file.name)
        domains_list = sorted(found_domains)
        for i in range(len(domains_list)):
            for j in range(i + 1, len(domains_list)):
                pair = (domains_list[i], domains_list[j])
                co_citations[pair] += 1

    return [
        {"pair": list(pair), "co_citations": count}
        for pair, count in sorted(co_citations.items(), key=lambda x: -x[1])
        if count >= 2
    ]


def compute_sharpe_health(lessons_dir: Path) -> dict:
    """Compute mean Sharpe and zero-Sharpe backlog for compost readiness."""
    if not lessons_dir.exists():
        return {}
    sharpes = []
    zero_sharpe = 0
    total = 0
    for lesson_file in sorted(lessons_dir.glob("L-*.md")):
        text = lesson_file.read_text(encoding="utf-8", errors="ignore")
        # Count non-trivial citations (F-, L-, P-, B- references)
        citations = len(re.findall(r'\b[FLPB]-\d+\b|\bF-[A-Z]+\d+\b', text))
        lines = sum(1 for l in text.splitlines() if l.strip())
        if lines > 0:
            sharpe = citations / lines
            sharpes.append(sharpe)
            if sharpe == 0:
                zero_sharpe += 1
            total += 1

    if not sharpes:
        return {"total": 0, "mean_sharpe": None, "zero_sharpe_count": 0, "zero_sharpe_rate": None}

    mean_s = sum(sharpes) / len(sharpes)
    zero_rate = zero_sharpe / total
    compost_status = "OVERDUE" if zero_rate > 0.6 else ("DUE" if zero_rate > 0.4 else "HEALTHY")
    return {
        "total": total,
        "mean_sharpe": round(mean_s, 4),
        "zero_sharpe_count": zero_sharpe,
        "zero_sharpe_rate": round(zero_rate, 3),
        "compost_status": compost_status,
    }


def domain_coverage_map() -> dict:
    """Which domains have FRONTIER.md files vs missing."""
    has_frontier = []
    missing_frontier = []
    for d in KNOWN_DOMAINS:
        frontier = ROOT / "domains" / d / "tasks" / "FRONTIER.md"
        if frontier.exists():
            has_frontier.append(d)
        elif (ROOT / "domains" / d).exists():
            missing_frontier.append(d)
    return {"active_domains": len(has_frontier), "has_frontier": has_frontier, "missing_frontier": missing_frontier}


# ---------------------------------------------------------------------------
# Main report
# ---------------------------------------------------------------------------

def build_report() -> dict:
    sessions = _parse_session_log()
    lanes = _parse_swarm_lanes()
    lessons_dir = ROOT / "memory" / "lessons"

    coverage = domain_coverage_map()
    rotation = compute_rotation_health(lanes)
    fallow = compute_fallow_candidates(lanes)
    companions = compute_companion_pairs(lessons_dir)
    sharpe = compute_sharpe_health(lessons_dir)

    return {
        "domain_coverage": coverage,
        "rotation_health": rotation,
        "fallow_candidates": fallow,
        "companion_pairs": companions[:10],  # top 10
        "compost_status": sharpe,
        "session_count": len(sessions),
        "lane_count": len(lanes),
    }


def render_human(report: dict) -> str:
    lines = ["=== SWARM FARMING REPORT ===\n"]

    cov = report["domain_coverage"]
    lines.append(f"[COVERAGE] {cov['active_domains']} domains with FRONTIER.md")
    if cov["missing_frontier"]:
        lines.append(f"  Missing frontier: {', '.join(cov['missing_frontier'])}")

    rot = report["rotation_health"]
    if rot["hhi"] is not None:
        lines.append(f"\n[ROTATION] HHI={rot['hhi']} over last {rot['window']} lanes → {rot['status']}")
        if rot["domain_shares"]:
            top3 = list(rot["domain_shares"].items())[:3]
            lines.append(f"  Top domains: {', '.join(f'{d}({int(s*100)}%)' for d,s in top3)}")
    else:
        lines.append("\n[ROTATION] No lane data available")

    fallow = report["fallow_candidates"]
    if fallow:
        lines.append(f"\n[FALLOW] {len(fallow)} candidate(s) — resting, may yield higher Sharpe on revival:")
        for f in fallow[:5]:
            lines.append(f"  • {f['domain']} (last session S{f['last_session']})")
    else:
        lines.append("\n[FALLOW] No fallow candidates (all domains recently active)")

    companions = report["companion_pairs"]
    if companions:
        lines.append(f"\n[COMPANION PAIRS] {len(companions)} pairs with ≥2 co-citations:")
        for c in companions[:5]:
            lines.append(f"  • {c['pair'][0]} ↔ {c['pair'][1]} ({c['co_citations']} co-citations)")
    else:
        lines.append("\n[COMPANION PAIRS] No pairs found (≥2 threshold) — cross-domain pollination sparse")

    sharpe = report["compost_status"]
    if sharpe.get("total"):
        lines.append(f"\n[COMPOST] {sharpe['total']} lessons | mean Sharpe={sharpe['mean_sharpe']} | "
                     f"zero-Sharpe={sharpe['zero_sharpe_count']} ({int(sharpe['zero_sharpe_rate']*100)}%) → {sharpe['compost_status']}")
    else:
        lines.append("\n[COMPOST] No lessons found")

    lines.append(f"\n[SESSIONS] {report['session_count']} in log | {report['lane_count']} lanes parsed")
    return "\n".join(lines)


if __name__ == "__main__":
    report = build_report()
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print(render_human(report))
