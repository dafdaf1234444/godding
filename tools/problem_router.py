#!/usr/bin/env python3
"""problem_router.py — Route detected problems to domain experts.

Bridges the gap between orient.py (detects problems) and dispatch_optimizer.py
(scores domains). Without this, dispatch is problem-agnostic: it picks domains
by UCB1 exploration/exploitation balance, not by which domain can actually solve
the current problem.

The router:
  1. Ingests problems from orient.py (DUE items, stale lanes, signals, triggers)
  2. Maps each problem to domain expert(s) using keyword + structural matching
  3. Compares problem-indicated domains vs UCB1 top recommendations
  4. Outputs routing table: problem → expert → action

Usage:
    python3 tools/problem_router.py              # human-readable routing table
    python3 tools/problem_router.py --json       # JSON output
    python3 tools/problem_router.py --dispatch    # augmented dispatch with problem weighting
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

LANES_FILE = ROOT / "tasks" / "SWARM-LANES.md"
SIGNALS_FILE = ROOT / "tasks" / "SIGNALS.md"
TRIGGER_FILE = ROOT / "domains" / "meta" / "SESSION-TRIGGER.md"

# --- Problem → Domain mapping rules ---
# Each rule: (pattern_in_problem, mapped_domain, confidence)
# Patterns match against orient.py DUE item names, signal content, trigger IDs

KEYWORD_ROUTES = [
    # Maintenance DUE items
    (r"health[- ]?check", "economy", 0.9),
    (r"economy[_ ]?expert", "economy", 1.0),
    (r"state[- ]?sync", "meta", 0.8),
    (r"sync_state", "meta", 0.8),
    (r"change[- ]?quality", "evaluation", 0.9),
    (r"action[- ]?board", "strategy", 0.8),
    (r"fundamental[- ]?setup|setup[- ]?reswarm", "meta", 0.7),
    (r"lesson.*over.*\d+.*lines?", "meta", 0.6),
    (r"proxy[- ]?k|compaction|compact", "economy", 0.8),
    (r"contract[_ ]?check", "meta", 0.9),

    # Signal content keywords
    (r"dependency|dependencies", "graph-theory", 0.8),
    (r"epistemolog|knowledge[_ ]?state", "meta", 0.9),
    (r"dispatch|scheduling|expert", "expert-swarm", 0.8),
    (r"node[_ ]?generalization", "meta", 0.7),
    (r"communication|signal", "meta", 0.6),
    (r"security|audit|integrity", "security", 0.9),
    (r"DNA|replication|mutation", "meta", 0.7),
    (r"evolution|cadence|era", "evolution", 0.8),
    (r"compet|benchmark|external", "competitions", 0.8),
    (r"document|docs|paper", "meta", 0.6),
    (r"self[- ]?apply|recursive|self[- ]?swarm", "meta", 0.7),
    (r"personality|psych", "psychology", 0.8),
    (r"game|roguelike", "gaming", 0.8),
    (r"bureaucra|human[- ]?system", "human-systems", 0.8),
    (r"stochastic|burst|hawkes|HMM", "stochastic-processes", 0.9),
    (r"NK|complexity|chaos", "nk-complexity", 0.8),
    (r"citation|graph|network", "graph-theory", 0.7),
    (r"isomorphi|cross[- ]?domain", "meta", 0.6),
    (r"governance|council|vote", "governance", 0.9),
    (r"crypt|blockchain|bitcoin", "cryptocurrency", 0.9),
    (r"econom|Sharpe|throughput|yield", "economy", 0.8),
    (r"jepsen|distributed|consensus", "distributed-systems", 0.9),
    (r"Reynolds|turbul|laminar", "fluid-dynamics", 0.9),
    (r"brain|predict|neuro", "brain", 0.8),
    (r"linguis|language|vocab", "linguistics", 0.7),
    (r"farming|fallow|companion", "farming", 0.8),
    (r"fractal|self[- ]?similar", "fractals", 0.8),
    (r"control[- ]?theory|anti[- ]?windup|PID", "control-theory", 0.9),

    # Trigger IDs
    (r"T1-STALE", "meta", 0.5),  # generic, domain depends on which lane
    (r"T2-ARTIFACT", "meta", 0.5),
    (r"T3-MAINTENANCE", "meta", 0.6),
    (r"T4-ANXIETY", "meta", 0.5),  # depends on which frontier
    (r"T5-DISPATCH", "expert-swarm", 0.7),
    (r"T6-HEALTH", "economy", 0.8),
    (r"T7-PROXY", "economy", 0.8),
]

# Lane prefix → domain (reuse dispatch_optimizer mapping)
LANE_ABBREV_TO_DOMAIN = {
    "NK": "nk-complexity", "LNG": "linguistics", "EXP": "expert-swarm",
    "STAT": "statistics", "PHI": "philosophy", "CTX": "meta", "MECH": "meta",
    "FLD": "fluid-dynamics", "BRN": "brain", "HLP": "helper-swarm",
    "ECO": "economy", "PHY": "physics", "SCI": "evaluation", "EVO": "evolution",
    "DNA": "meta", "IS": "information-science", "HS": "human-systems",
    "COMP": "competitions", "INFO": "information-science",
    "META": "meta", "SP": "stochastic-processes", "EMP": "empathy",
    "AI": "ai", "CON": "conflict", "CONFLICT": "conflict",
    "CAT": "catastrophic-risks", "DS": "distributed-systems",
    "FIN": "finance", "GOV": "governance", "EVAL": "evaluation",
    "FRA": "fractals", "FRACTALS": "fractals", "GT": "game-theory",
    "GTH": "graph-theory", "GAME": "game-theory", "GAMING": "gaming",
    "GUE": "guesstimates", "GAM": "game-theory", "PSY": "psychology",
    "SOC": "social-media", "STR": "strategy", "QC": "quality",
    "SEC": "security", "PRO": "protocol-engineering",
    "FARMING": "farming", "FAR": "farming", "COORD": "meta",
    "HUMAN": "human-systems", "CT": "meta", "CTL": "control-theory",
    "CC": "cryptocurrency", "CRY": "cryptography", "CRYPTO": "cryptocurrency",
}


def _current_session() -> int:
    try:
        out = subprocess.check_output(
            ["git", "log", "--oneline", "-20"], cwd=str(ROOT),
            stderr=subprocess.DEVNULL, text=True, timeout=5
        )
        nums = [int(m) for m in re.findall(r"\[S(\d+)\]", out)]
        return max(nums) if nums else 0
    except Exception:
        return 0


# --- Problem detection ---

def detect_due_items() -> list[dict]:
    """Run orient.py and parse DUE maintenance items."""
    try:
        out = subprocess.check_output(
            [sys.executable, str(TOOLS / "orient.py")],
            cwd=str(ROOT), stderr=subprocess.DEVNULL, text=True, timeout=30
        )
    except Exception:
        return []

    problems = []
    in_due = False
    for line in out.splitlines():
        if "[DUE]" in line:
            in_due = True
            continue
        if in_due and line.strip().startswith("!"):
            text = line.strip().lstrip("! ").strip()
            problems.append({
                "source": "maintenance-DUE",
                "text": text,
                "urgency": "MEDIUM",
            })
        elif in_due and not line.strip().startswith("!") and not line.strip().startswith("-"):
            in_due = False

    # Stale lanes
    for m in re.finditer(r"⚠ (DOMEX-\S+)\s+\(S(\d+)\)", out):
        lane_id, session = m.group(1), m.group(2)
        problems.append({
            "source": "stale-lane",
            "text": f"Stale lane {lane_id} from S{session}",
            "urgency": "HIGH",
            "lane_id": lane_id,
        })

    # Scope collisions
    for m in re.finditer(r"Active lane scope collision.*?:\s*(.+)", out):
        problems.append({
            "source": "scope-collision",
            "text": f"Lane scope collision: {m.group(1).strip()}",
            "urgency": "MEDIUM",
        })

    return problems


def detect_firing_triggers() -> list[dict]:
    """Read SESSION-TRIGGER.md for FIRING triggers."""
    if not TRIGGER_FILE.exists():
        return []

    problems = []
    text = TRIGGER_FILE.read_text()
    for m in re.finditer(
        r"^\|\s*(T\d+-\S+)\s*\|([^|]+)\|([^|]+)\|\s*FIRING\s*\|([^|]+)\|([^|]+)\|",
        text, re.MULTILINE
    ):
        tid, condition, urgency = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        action = m.group(5).strip()
        problems.append({
            "source": "trigger",
            "text": f"{tid}: {condition}",
            "urgency": urgency,
            "action": action,
            "trigger_id": tid,
        })
    return problems


def detect_open_signals() -> list[dict]:
    """Read SIGNALS.md for OPEN signals as problems/directives."""
    if not SIGNALS_FILE.exists():
        return []

    problems = []
    text = SIGNALS_FILE.read_text()
    for m in re.finditer(
        r"^\| (SIG-\d+)\s*\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|",
        text, re.MULTILINE
    ):
        fields = [s.strip() for s in m.groups()]
        sid, _, session, source, _, sig_type, priority, content, status = fields
        if status != "OPEN":
            continue
        # Directives are problems to address; observations are context
        if sig_type in ("directive", "question"):
            problems.append({
                "source": "signal",
                "text": f"{sid}: {content[:120]}",
                "urgency": "LOW" if priority == "P2" else "MEDIUM",
                "signal_id": sid,
                "signal_type": sig_type,
            })
    return problems


# --- Routing ---

def route_problem(problem: dict) -> list[dict]:
    """Map a problem to domain expert(s) using keyword matching."""
    text = problem["text"].lower()
    routes = []

    # Special case: stale lanes → extract domain from lane ID
    if problem.get("lane_id"):
        lane_id = problem["lane_id"]
        m = re.match(r"DOMEX-([A-Z]+)", lane_id)
        if m:
            abbrev = m.group(1)
            domain = LANE_ABBREV_TO_DOMAIN.get(abbrev)
            if domain:
                routes.append({
                    "domain": domain,
                    "confidence": 0.95,
                    "reason": f"Lane prefix {abbrev} maps to {domain}",
                })

    # Keyword matching
    for pattern, domain, confidence in KEYWORD_ROUTES:
        if re.search(pattern, text, re.IGNORECASE):
            # Don't duplicate if already routed to same domain
            if not any(r["domain"] == domain for r in routes):
                routes.append({
                    "domain": domain,
                    "confidence": confidence,
                    "reason": f"Keyword '{pattern}' matched",
                })

    # Sort by confidence
    routes.sort(key=lambda r: r["confidence"], reverse=True)
    return routes


def get_dispatch_top(n: int = 5) -> list[str]:
    """Get top-N domains from dispatch_optimizer."""
    try:
        out = subprocess.check_output(
            [sys.executable, str(TOOLS / "dispatch_optimizer.py"),
             "--json", "--mode", "ucb1"],
            cwd=str(ROOT), stderr=subprocess.DEVNULL, text=True, timeout=30
        )
        data = json.loads(out)
        return [d["domain"] for d in data[:n]]
    except Exception:
        return []


# --- Analysis ---

def analyze_routing(routed_problems: list[dict], dispatch_top: list[str]) -> dict:
    """Compare problem-routed domains vs dispatch recommendations."""
    # Domains indicated by problems
    problem_domains = defaultdict(float)
    for rp in routed_problems:
        for route in rp.get("routes", []):
            problem_domains[route["domain"]] += route["confidence"]

    # Sort by weighted urgency
    ranked_problem_domains = sorted(
        problem_domains.items(), key=lambda x: x[1], reverse=True
    )

    # Mismatch analysis
    problem_top5 = [d for d, _ in ranked_problem_domains[:5]]
    dispatch_top5 = dispatch_top[:5]

    overlap = set(problem_top5) & set(dispatch_top5)
    mismatch_rate = 1.0 - (len(overlap) / max(len(problem_top5), 1))

    # Problems with no route
    unmapped = [rp for rp in routed_problems if len(rp.get("routes", [])) == 0]
    mapped = [rp for rp in routed_problems if len(rp.get("routes", [])) > 0]
    mapping_rate = len(mapped) / max(len(routed_problems), 1)

    # Domain demand vs dispatch supply
    demand_without_supply = [
        d for d in problem_top5 if d not in dispatch_top5
    ]
    supply_without_demand = [
        d for d in dispatch_top5 if d not in problem_top5
    ]

    return {
        "total_problems": len(routed_problems),
        "mapped_count": len(mapped),
        "unmapped_count": len(unmapped),
        "mapping_rate": round(mapping_rate, 3),
        "problem_top5": problem_top5,
        "dispatch_top5": dispatch_top5,
        "overlap": sorted(overlap),
        "mismatch_rate": round(mismatch_rate, 3),
        "demand_without_supply": demand_without_supply,
        "supply_without_demand": supply_without_demand,
        "domain_demand_scores": dict(ranked_problem_domains[:10]),
    }


def augmented_dispatch(routed_problems: list[dict], dispatch_top: list[str]) -> list[dict]:
    """Produce problem-augmented dispatch recommendations.

    Combines UCB1 exploration score with problem-demand urgency.
    """
    # Aggregate problem demand per domain
    demand = defaultdict(lambda: {"score": 0.0, "problems": []})
    for rp in routed_problems:
        urgency_weight = {"HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}.get(
            rp.get("urgency", "LOW"), 1.0
        )
        for route in rp.get("routes", []):
            dom = route["domain"]
            demand[dom]["score"] += route["confidence"] * urgency_weight
            demand[dom]["problems"].append(rp["text"][:60])

    # Build augmented list
    recommendations = []
    for domain in set(list(demand.keys()) + dispatch_top):
        ucb1_rank = dispatch_top.index(domain) + 1 if domain in dispatch_top else len(dispatch_top) + 1
        problem_score = demand.get(domain, {"score": 0.0})["score"]
        problems = demand.get(domain, {"problems": []})["problems"]

        # Combined score: UCB1 rank-inverse + problem demand
        ucb1_component = max(0, (len(dispatch_top) + 1 - ucb1_rank)) / max(len(dispatch_top), 1)
        combined = ucb1_component + problem_score

        recommendations.append({
            "domain": domain,
            "combined_score": round(combined, 2),
            "ucb1_rank": ucb1_rank,
            "problem_demand": round(problem_score, 2),
            "problem_count": len(problems),
            "problems": problems[:3],
        })

    recommendations.sort(key=lambda r: r["combined_score"], reverse=True)
    return recommendations


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Route detected problems to domain experts"
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--dispatch", action="store_true",
                        help="Show augmented dispatch with problem weighting")
    parser.add_argument("--problems-only", action="store_true",
                        help="Only show detected problems, no routing")
    args = parser.parse_args()

    session = _current_session()

    # Detect all problems
    problems = []
    problems.extend(detect_due_items())
    problems.extend(detect_firing_triggers())
    problems.extend(detect_open_signals())

    if args.problems_only:
        for p in problems:
            print(f"  [{p['urgency']:6s}] {p['source']:18s} | {p['text'][:80]}")
        print(f"\nTotal: {len(problems)} problems detected")
        return

    # Route each problem
    routed = []
    for p in problems:
        routes = route_problem(p)
        routed.append({**p, "routes": routes})

    # Get dispatch state
    dispatch_top = get_dispatch_top(10)

    # Analyze
    analysis = analyze_routing(routed, dispatch_top)

    if args.json:
        output = {
            "session": f"S{session}",
            "problems": [{k: v for k, v in rp.items() if k != "routes"} | {
                "routes": rp.get("routes", [])
            } for rp in routed],
            "analysis": analysis,
        }
        json_path = ROOT / "experiments" / "meta" / f"problem-router-s{session + 1}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(output, indent=2) + "\n")
        print(json.dumps(output, indent=2))
        print(f"\nWritten to {json_path.relative_to(ROOT)}")
        return

    if args.dispatch:
        recommendations = augmented_dispatch(routed, dispatch_top)
        print(f"\n=== PROBLEM-AUGMENTED DISPATCH — S{session + 1} ===")
        print(f"Problems detected: {len(routed)} | Mapped: {analysis['mapped_count']} | Unmapped: {analysis['unmapped_count']}")
        print(f"\n{'Score':>6}  {'Domain':<25}  {'UCB1#':>5}  {'PDemand':>7}  {'#Prob':>5}  Top Problem")
        print("-" * 90)
        for r in recommendations[:15]:
            top_prob = r["problems"][0][:40] if r["problems"] else "-"
            ucb1_str = f"#{r['ucb1_rank']}" if r["ucb1_rank"] <= len(dispatch_top) else "—"
            print(
                f"{r['combined_score']:6.2f}  {r['domain']:<25}  {ucb1_str:>5}  "
                f"{r['problem_demand']:7.2f}  {r['problem_count']:5d}  {top_prob}"
            )
        return

    # Default: routing table
    print(f"\n=== PROBLEM ROUTER — S{session + 1} ===")
    print(f"Detected {len(routed)} problems from orient.py / triggers / signals\n")

    # Group by source
    by_source = defaultdict(list)
    for rp in routed:
        by_source[rp["source"]].append(rp)

    for source in ["trigger", "stale-lane", "maintenance-DUE", "scope-collision", "signal"]:
        items = by_source.get(source, [])
        if not items:
            continue
        print(f"--- {source.upper()} ({len(items)}) ---")
        for rp in items:
            routes = rp.get("routes", [])
            if routes:
                domain_str = ", ".join(
                    f"{r['domain']}({r['confidence']:.1f})" for r in routes[:3]
                )
            else:
                domain_str = "NO ROUTE"
            urgency_icon = {"HIGH": "!!", "MEDIUM": "!", "LOW": "~"}.get(
                rp.get("urgency", "LOW"), " "
            )
            print(f"  {urgency_icon} {rp['text'][:70]}")
            print(f"     → Expert: {domain_str}")
        print()

    # Mismatch summary
    print("--- ROUTING vs DISPATCH ANALYSIS ---")
    print(f"  Mapping rate: {analysis['mapping_rate']*100:.0f}% ({analysis['mapped_count']}/{analysis['total_problems']} problems routable)")
    print(f"  Problem top-5: {', '.join(analysis['problem_top5'])}")
    print(f"  UCB1 top-5:    {', '.join(analysis['dispatch_top5'])}")
    print(f"  Overlap:       {', '.join(analysis['overlap']) or 'NONE'}")
    print(f"  Mismatch rate: {analysis['mismatch_rate']*100:.0f}%")
    if analysis["demand_without_supply"]:
        print(f"  DEMAND (no UCB1 supply): {', '.join(analysis['demand_without_supply'])}")
    if analysis["supply_without_demand"]:
        print(f"  SUPPLY (no problem demand): {', '.join(analysis['supply_without_demand'])}")


if __name__ == "__main__":
    main()
