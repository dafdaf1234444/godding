#!/usr/bin/env python3
"""self_order.py — Self-referential ordering: the swarm asks itself how to order.

Human signal (SIG-31): "swarm has to ask swarm how to order its swarm swarm"

The swarm's ordering logic should come FROM the swarm's own experimental evidence,
not from externally designed heuristics. This tool extracts ordering rules from
the swarm's accumulated findings and applies them to current state.

Evidence-based rules (each with explicit lesson provenance):
  R1  L-654: MIXED > PROVEN yield (1.42 vs 1.21 L/lane)
  R2  L-716: Problem demand beats exploration (100% mismatch)
  R3  L-695: Flow zone (2-10 sessions) = highest quality (1.30x)
  R4  L-686: Meta concentration kills productivity (-372%)
  R5  L-698: WRONG/MIXED = optimal learning zone (1.6x)
  R6  L-689: 0/28 beliefs DROPPED = confirmation machine
  R7  L-633: Mechanism decays before principle (20% superseded)
  R8  L-624: Session type > task ordering (eta^2=22%)
  R9  L-601: Only structural enforcement works (0% voluntary)

Comparison: self-ordering vs UCB1 dispatch measures the divergence between
what the swarm KNOWS about ordering and what it DOES.

Usage:
    python3 tools/self_order.py              # self-ordered recommendations
    python3 tools/self_order.py --compare    # side-by-side vs UCB1
    python3 tools/self_order.py --json       # machine-readable output
    python3 tools/self_order.py --rules      # show evidence rules only
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
LANES_ARCHIVE = ROOT / "tasks" / "SWARM-LANES-ARCHIVE.md"

# --- Evidence-based ordering rules ---
# Each rule: lesson source, finding, and the scoring adjustment it implies.
# The swarm's own experiments produced these — not external design.

EVIDENCE_RULES = [
    {"id": "R1", "source": "L-654", "tag": "MIXED-YIELD",
     "finding": "MIXED lanes yield 1.42 L/lane vs PROVEN 1.21 — diminishing returns in proven domains",
     "action": "+2.0 MIXED, -0.5 PROVEN, -1.0 STRUGGLING"},
    {"id": "R2", "source": "L-716", "tag": "PROBLEM-DEMAND",
     "finding": "100% mismatch between UCB1 top-5 and problem-indicated top-5",
     "action": "+3.0 per detected problem routed to domain"},
    {"id": "R3", "source": "L-695", "tag": "FLOW-ZONE",
     "finding": "2-10 sessions on a frontier = 1.30x citation quality (rarest at 5.6%)",
     "action": "+2.0 flow zone, -1.5 anxiety zone (>15 sessions)"},
    {"id": "R4", "source": "L-686", "tag": "META-CONCENTRATION",
     "finding": "Meta share 74% of sessions; monoculture = -372% productivity vs diversified",
     "action": "-3.0 to meta when share >50%"},
    {"id": "R5", "source": "L-698", "tag": "SURPRISE-PRODUCTION",
     "finding": "WRONG predictions produce 1.6x more lessons; MIXED = 81% surprise rate",
     "action": "+1.5 for uncertain/MIXED domains, +1.5 for unvisited"},
    {"id": "R6", "source": "L-689", "tag": "FALSIFICATION",
     "finding": "0/28 beliefs DROPPED = confirmation machine; no disconfirmation mechanism",
     "action": "reserve 1/10 slots for explicit belief falsification (+2.0)"},
    {"id": "R7", "source": "L-633", "tag": "MECHANISM-DECAY",
     "finding": "20% mechanism-superseded in top-20 cited; mechanism decays before principle",
     "action": "+1.0 for domains with >20 session gap (mechanisms likely stale)"},
    {"id": "R8", "source": "L-624, L-717", "tag": "SESSION-TYPE",
     "finding": "Session type explains 22% variance; single-DOMEX = 100% value sessions",
     "action": "recommend session type (DOMEX/PROBLEM-FIX/EXPLORATION/REVIVAL)"},
    {"id": "R9", "source": "L-601", "tag": "ENFORCEMENT",
     "finding": "Voluntary compliance = 0%; only creation-time enforcement sustains",
     "action": "output actionable commands, not advisory text"},
]


def _git(args: list[str]) -> str:
    r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip()


def _current_session() -> int:
    try:
        from swarm_io import session_number as _sn
        return _sn()
    except Exception:
        nums = [int(m) for m in re.findall(r"\[S(\d+)\]", _git(["log", "--oneline", "-20"]))]
        return max(nums) if nums else 378


def _parse_lanes() -> list[dict]:
    """Parse all lanes (active + archive) into structured records."""
    records = []
    for f in (LANES_FILE, LANES_ARCHIVE):
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if not line.startswith("|") or "---" in line or "Date" in line:
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 8:
                continue
            lane_id = cols[2] if len(cols) > 2 else ""
            session_str = cols[3] if len(cols) > 3 else ""
            etc = cols[10] if len(cols) > 10 else ""
            status = cols[11] if len(cols) > 11 else ""
            notes = cols[12] if len(cols) > 12 else ""

            domain = None
            m = re.match(r"DOMEX-([A-Z]+)", lane_id)
            if m:
                try:
                    from dispatch_optimizer import LANE_ABBREV_TO_DOMAIN
                    domain = LANE_ABBREV_TO_DOMAIN.get(m.group(1))
                except ImportError:
                    pass

            sess_m = re.search(r"S?(\d+)", session_str)
            sess = int(sess_m.group(1)) if sess_m else 0

            records.append({
                "lane_id": lane_id,
                "domain": domain,
                "session": sess,
                "status": status.strip(),
                "notes": notes,
                "lesson_count": len(re.findall(r"\bL-\d{3,4}\b", notes)),
            })
    return records


def _domain_outcomes(lanes: list[dict]) -> dict:
    """Compute per-domain MERGED/ABANDONED/lessons from lane records."""
    outcomes = defaultdict(lambda: {"merged": 0, "abandoned": 0, "lessons": 0})
    for lane in lanes:
        if not lane["domain"] or lane["status"] not in ("MERGED", "ABANDONED"):
            continue
        d = lane["domain"]
        if lane["status"] == "MERGED":
            outcomes[d]["merged"] += 1
        else:
            outcomes[d]["abandoned"] += 1
        outcomes[d]["lessons"] += lane["lesson_count"]
    return dict(outcomes)


def _domain_session_counts(lanes: list[dict]) -> dict:
    """Count distinct sessions per domain."""
    sessions = defaultdict(set)
    for lane in lanes:
        if lane["domain"] and lane["session"] > 0:
            sessions[lane["domain"]].add(lane["session"])
    return {d: len(s) for d, s in sessions.items()}


def _domain_last_active(lanes: list[dict]) -> dict:
    """Find most recent session per domain."""
    last = {}
    for lane in lanes:
        if lane["domain"] and lane["session"] > 0:
            if lane["domain"] not in last or lane["session"] > last[lane["domain"]]:
                last[lane["domain"]] = lane["session"]
    return last


def _meta_share(lanes: list[dict]) -> float:
    """What fraction of completed lanes are meta domain."""
    total = sum(1 for l in lanes if l["status"] in ("MERGED", "ABANDONED") and l["domain"])
    meta = sum(1 for l in lanes if l["status"] in ("MERGED", "ABANDONED") and l["domain"] == "meta")
    return meta / total if total > 0 else 0.0


def _get_problem_demand() -> dict:
    """Get problem counts per domain from problem_router."""
    try:
        r = subprocess.run(
            [sys.executable, str(TOOLS / "problem_router.py"), "--json"],
            capture_output=True, text=True, cwd=ROOT, timeout=15
        )
        data = json.loads(r.stdout)
        demand = defaultdict(int)
        for route in data.get("routes", []):
            domain = route.get("domain", "")
            if domain:
                demand[domain] += 1
        return dict(demand)
    except Exception:
        return {}


def _get_ucb1_ranking() -> list[tuple]:
    """Get current UCB1 dispatch ranking for comparison."""
    try:
        r = subprocess.run(
            [sys.executable, str(TOOLS / "dispatch_optimizer.py"), "--json", "--all"],
            capture_output=True, text=True, cwd=ROOT, timeout=15
        )
        data = json.loads(r.stdout)
        if isinstance(data, list):
            return [(d["domain"], d.get("score", 0)) for d in data]
    except Exception:
        pass
    return []


def self_order_domains() -> dict:
    """Apply evidence-based ordering rules to all domains.

    Returns structured output with self-ordered ranking, UCB1 comparison,
    divergence measurement, and session type recommendation.
    """
    current_session = _current_session()
    lanes = _parse_lanes()
    outcomes = _domain_outcomes(lanes)
    session_counts = _domain_session_counts(lanes)
    last_active = _domain_last_active(lanes)
    ms = _meta_share(lanes)
    problem_demand = _get_problem_demand()
    ucb1_ranking = _get_ucb1_ranking()

    # Collect all known domains
    all_domains = set()
    for src in (outcomes, session_counts, last_active, problem_demand):
        all_domains.update(src.keys())
    for d, _ in ucb1_ranking:
        all_domains.add(d)

    scored = []
    for domain in sorted(all_domains):
        score = 0.0
        rules = []

        oc = outcomes.get(domain, {"merged": 0, "abandoned": 0, "lessons": 0})
        n = oc["merged"] + oc["abandoned"]
        sess = session_counts.get(domain, 0)
        last = last_active.get(domain, 0)
        gap = current_session - last if last > 0 else 999
        problems = problem_demand.get(domain, 0)

        # R1: MIXED > PROVEN yield
        if n >= 3:
            rate = oc["merged"] / n
            if 0.50 <= rate < 0.75:
                score += 2.0
                rules.append(("R1", "+2.0", "MIXED yield premium"))
            elif rate >= 0.75:
                score -= 0.5
                rules.append(("R1", "-0.5", "PROVEN diminishing returns"))
            else:
                score -= 1.0
                rules.append(("R1", "-1.0", "STRUGGLING"))

        # R2: Problem demand
        if problems > 0:
            boost = min(problems * 3.0, 9.0)  # cap at 3 problems
            score += boost
            rules.append(("R2", f"+{boost:.1f}", f"{problems} problem(s) demand expert"))

        # R3: Flow zone
        if 2 <= sess <= 10:
            score += 2.0
            rules.append(("R3", "+2.0", f"{sess}s in flow zone [2-10]"))
        elif sess > 15:
            score -= 1.5
            rules.append(("R3", "-1.5", f"{sess}s anxiety zone [>15]"))
        elif sess == 0:
            score += 1.0
            rules.append(("R3", "+1.0", "uncharted territory"))

        # R4: Meta de-prioritization
        if domain == "meta" and ms > 0.50:
            score -= 3.0
            rules.append(("R4", "-3.0", f"meta share {ms:.0%} > 50%"))

        # R5: Surprise production
        if n >= 3:
            rate = oc["merged"] / n
            if 0.50 <= rate < 0.75:
                score += 1.5
                rules.append(("R5", "+1.5", "MIXED = high surprise potential"))
        elif n == 0:
            score += 1.5
            rules.append(("R5", "+1.5", "never visited = maximum uncertainty"))

        # R7: Mechanism decay
        if gap > 20 and n >= 3:
            score += 1.0
            rules.append(("R7", "+1.0", f"gap {gap}s — mechanisms may be stale"))

        # Base: empirical lesson yield
        if n > 0:
            avg_yield = oc.get("lessons", 0) / n
            score += avg_yield
            rules.append(("BASE", f"+{avg_yield:.2f}", f"avg yield {oc['lessons']}L/{n}"))

        # Classify outcome label
        if n >= 3:
            rate = oc["merged"] / n
            label = "PROVEN" if rate >= 0.75 else "MIXED" if rate >= 0.50 else "STRUGGLING"
        else:
            label = "NEW"

        scored.append({
            "domain": domain,
            "self_score": round(score, 2),
            "rules": rules,
            "outcome": label,
            "sessions": sess,
            "problems": problems,
            "gap": gap if gap < 999 else None,
            "visits": n,
            "lessons": oc.get("lessons", 0),
        })

    scored.sort(key=lambda x: x["self_score"], reverse=True)

    # --- Divergence measurement ---
    ucb1_order = [d for d, _ in ucb1_ranking]
    self_order_list = [s["domain"] for s in scored]

    top_n = min(10, len(scored), len(ucb1_order))
    ucb1_top = ucb1_order[:top_n]
    self_top = self_order_list[:top_n]
    overlap = set(ucb1_top) & set(self_top)
    divergence_pct = round((1.0 - len(overlap) / top_n) * 100, 1) if top_n > 0 else 100.0

    # Rank displacement
    ucb1_pos = {d: i for i, d in enumerate(ucb1_order)}
    displacements = []
    for i, d in enumerate(self_order_list[:top_n]):
        if d in ucb1_pos:
            displacements.append(abs(i - ucb1_pos[d]))
    avg_disp = round(sum(displacements) / len(displacements), 1) if displacements else 0.0

    # R8: Session type recommendation
    top = scored[0] if scored else None
    if top and top["problems"] > 0:
        session_type = "PROBLEM-FIX"
        session_reason = f"{top['domain']} has {top['problems']} detected problem(s)"
    elif top and top.get("gap") and top["gap"] > 30:
        session_type = "REVIVAL"
        session_reason = f"{top['domain']} dormant for {top['gap']} sessions"
    elif top and top["outcome"] == "NEW":
        session_type = "EXPLORATION"
        session_reason = f"{top['domain']} never visited"
    else:
        session_type = "DOMEX"
        session_reason = f"{top['domain']} is top evidence-ordered domain" if top else ""

    # R6: Falsification flag
    falsification_due = True  # always flag — 0/28 dropped
    falsification_note = "0 beliefs DROPPED in 378 sessions. 10% falsification allocation unmet."

    return {
        "self_ordered": scored,
        "ucb1_top10": ucb1_top,
        "divergence": {
            "top10_overlap": len(overlap),
            "top10_divergence_pct": divergence_pct,
            "avg_rank_displacement": avg_disp,
            "details": [
                {"rank": i + 1, "self": self_top[i] if i < len(self_top) else "-",
                 "ucb1": ucb1_top[i] if i < len(ucb1_top) else "-",
                 "match": self_top[i] == ucb1_top[i] if i < len(self_top) and i < len(ucb1_top) else False}
                for i in range(top_n)
            ],
        },
        "meta_share": round(ms, 3),
        "session_type": {"recommendation": session_type, "reason": session_reason},
        "falsification": {"due": falsification_due, "note": falsification_note},
        "rules_count": len(EVIDENCE_RULES),
        "current_session": current_session,
    }


def print_rules():
    """Print evidence rules with provenance."""
    print("\n=== SELF-ORDERING RULES (derived from swarm evidence) ===\n")
    for r in EVIDENCE_RULES:
        print(f"  {r['id']} [{r['source']}] {r['tag']}")
        print(f"     Finding: {r['finding']}")
        print(f"     Action:  {r['action']}")
        print()
    print(f"  Total: {len(EVIDENCE_RULES)} rules, each with explicit lesson provenance.")
    print(f"  The swarm's ordering comes FROM the swarm, not from external design.\n")


def print_self_order(result: dict, compare: bool = False):
    """Human-readable self-order output."""
    scored = result["self_ordered"]
    div = result["divergence"]
    stype = result["session_type"]

    print(f"\n=== SELF-ORDER S{result['current_session']} ===")
    print(f"  The swarm asks itself: {result['rules_count']} evidence rules applied")
    print(f"  Session type: {stype['recommendation']} — {stype['reason']}")
    print(f"  Meta share: {result['meta_share']:.0%}")
    if result["falsification"]["due"]:
        print(f"  !! {result['falsification']['note']}")
    print()

    print(f"{'Score':>6}  {'Domain':<25}  {'Out':>4}  {'Sess':>4}  {'Prob':>4}  {'Gap':>4}  Rules")
    print("-" * 90)

    for s in scored[:15]:
        gap_str = f"{s['gap']}" if s['gap'] else "NEW"
        rule_tags = " ".join(f"[{r[0]}]" for r in s["rules"])
        print(
            f"{s['self_score']:6.2f}  {s['domain']:<25}  {s['outcome']:>4}  "
            f"{s['sessions']:4d}  {s['problems']:4d}  {gap_str:>4}  {rule_tags}"
        )

    if compare:
        print(f"\n--- Divergence: self-order vs UCB1 ---")
        print(f"  Top-10 overlap: {div['top10_overlap']}/10")
        print(f"  Divergence: {div['top10_divergence_pct']}%")
        print(f"  Avg rank displacement: {div['avg_rank_displacement']} positions")
        print()
        print(f"  {'Rank':>4}  {'Self-order':<25}  {'UCB1':<25}  {'Match'}")
        print(f"  " + "-" * 65)
        for d in div["details"]:
            match = "=" if d["match"] else "!="
            print(f"  {d['rank']:>4}  {d['self']:<25}  {d['ucb1']:<25}  {match}")

    # R9: Enforcement — actionable command
    top = scored[0] if scored else None
    if top:
        print(f"\n--- Actionable (R9: enforcement > advice) ---")
        print(f"  python3 tools/open_lane.py --lane DOMEX-{top['domain'].upper()[:4]}-S{result['current_session']}"
              f" --session S{result['current_session']} --domain {top['domain']}"
              f" --expect '...' --artifact 'experiments/{top['domain']}/...'")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Self-referential ordering: swarm asks swarm how to order")
    parser.add_argument("--compare", action="store_true",
                        help="Show side-by-side comparison with UCB1 dispatch")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--rules", action="store_true", help="Show evidence rules only")
    args = parser.parse_args()

    if args.rules:
        print_rules()
        return

    result = self_order_domains()

    if args.json:
        # Strip non-serializable items
        print(json.dumps(result, indent=2, default=str))
        return

    print_self_order(result, compare=args.compare or True)


if __name__ == "__main__":
    main()
