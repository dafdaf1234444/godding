#!/usr/bin/env python3
"""free_energy.py — Active-inference-inspired surprise metric for the swarm.

Inspired by Friston's (2010) free energy principle: a self-organizing system
minimizes the divergence between its generative model (what it predicts) and
observations (what actually happens). High "free energy" = the self-model is
wrong and needs structural updating, not just another lesson.

The swarm's generative model = its beliefs (B-*) + philosophical claims (PHIL-*)
+ principles (P-*). Its observations = experiment outcomes, lane results, and
frontier evidence. This tool computes the surprise: how often does the swarm's
self-model predict incorrectly?

Three surprise components:
  1. Belief surprise: beliefs whose "Falsified if" conditions have evidence
     of being met, but the belief hasn't been updated.
  2. Expectation surprise: DOMEX lane expect→actual divergence (large diffs).
  3. Frontier surprise: frontiers stuck despite multiple experiments (the
     generative model predicts progress, reality says no).

Usage:
    python3 tools/free_energy.py              # full report
    python3 tools/free_energy.py --json       # machine-readable
    python3 tools/free_energy.py --component belief   # single component

L-1516: the medium of coordination IS the memory. This tool embodies its own
lesson: surprise scores route action (orient.py integration), not just report.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOMAINS_DIR = REPO_ROOT / "domains"
PHILOSOPHY_FILE = REPO_ROOT / "beliefs" / "PHILOSOPHY.md"
LANES_FILE = REPO_ROOT / "tasks" / "SWARM-LANES.md"
FRONTIER_FILE = REPO_ROOT / "tasks" / "FRONTIER.md"
EXPERIMENTS_DIR = REPO_ROOT / "experiments"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


# ---------- Component 1: Belief Surprise ----------
def _collect_beliefs() -> list[dict]:
    """Scan domain DOMAIN.md files + PHILOSOPHY.md for belief claims."""
    beliefs = []
    # Pattern: B-XXN or PHIL-N with inline falsification/evidence/tested
    claim_pat = re.compile(r"(B-?\w+\d+|PHIL-\d+)")
    falsif_pat = re.compile(r"[Ff]alsif\w*[\s:]+(.+?)(?:\.|$)", re.MULTILINE)
    tested_pat = re.compile(r"S(\d+)")
    evidence_pat = re.compile(r"\b(theorized|observed|grounded|confirmed)\b", re.IGNORECASE)

    # Scan domain files
    sources = list(DOMAINS_DIR.rglob("DOMAIN.md"))
    sources.append(PHILOSOPHY_FILE)
    for src in sources:
        text = _read(src)
        if not text:
            continue
        lines = text.split("\n")
        for i, line in enumerate(lines):
            claims = claim_pat.findall(line)
            if not claims:
                continue
            # Gather context: this line + next 3 lines
            context = "\n".join(lines[i:i+4])
            for cid in claims:
                falsif = falsif_pat.search(context)
                sessions = tested_pat.findall(context)
                ev = evidence_pat.search(context)
                last_s = max((int(s) for s in sessions), default=0)
                beliefs.append({
                    "id": cid,
                    "source": str(src.relative_to(REPO_ROOT)),
                    "context": line.strip()[:100],
                    "falsification": falsif.group(1).strip()[:100] if falsif else "",
                    "last_session": last_s,
                    "evidence": ev.group(1).lower() if ev else "unknown",
                })
    # Deduplicate by claim ID, keeping the one with most recent session
    by_id = {}
    for b in beliefs:
        if b["id"] not in by_id or b["last_session"] > by_id[b["id"]]["last_session"]:
            by_id[b["id"]] = b
    return list(by_id.values())


def compute_belief_surprise() -> dict:
    """How many beliefs have falsification conditions that may be met?"""
    beliefs = _collect_beliefs()
    if not beliefs:
        return {"score": 0, "details": [], "n_beliefs": 0, "n_surprised": 0}

    current_session = _get_current_session()
    details = []
    n_surprised = 0

    for b in beliefs:
        if not b["falsification"]:
            continue

        session_gap = current_session - b["last_session"]

        surprise = 0.0
        if session_gap > 50:
            surprise += 0.4
        if session_gap > 100:
            surprise += 0.3
        if b["evidence"] == "theorized":
            surprise += 0.2
        elif b["evidence"] == "unknown":
            surprise += 0.15

        if surprise > 0.3:
            n_surprised += 1
            details.append({
                "id": b["id"],
                "source": b["source"],
                "context": b["context"][:80],
                "falsification": b["falsification"],
                "session_gap": session_gap,
                "evidence": b["evidence"],
                "surprise": round(surprise, 2),
            })

    details.sort(key=lambda x: x["surprise"], reverse=True)
    score = n_surprised / max(len(beliefs), 1)
    return {
        "score": round(score, 3),
        "details": details[:10],
        "n_beliefs": len(beliefs),
        "n_surprised": n_surprised,
    }


# ---------- Component 2: Expectation Surprise ----------
def compute_expectation_surprise() -> dict:
    """How often do DOMEX lane expectations diverge from actual outcomes?"""
    text = _read(LANES_FILE)
    if not text:
        return {"score": 0, "details": [], "n_lanes": 0, "n_surprised": 0}

    # Parse MERGED lanes with expect + actual + diff
    lane_pat = re.compile(
        r"\|\s*(DOMEX-\S+)\s*\|.*?\|\s*MERGED\s*\|", re.MULTILINE
    )
    expect_pat = re.compile(r"expect:\s*(.+?)(?:\n|$)", re.MULTILINE)
    actual_pat = re.compile(r"actual:\s*(.+?)(?:\n|$)", re.MULTILINE)
    diff_pat = re.compile(r"diff:\s*(.+?)(?:\n|$)", re.MULTILINE)

    # Alternative: parse the structured fields in lane blocks
    blocks = re.split(r"(?=\|\s*DOMEX-)", text)
    details = []
    n_lanes = 0
    n_surprised = 0

    for block in blocks:
        if "MERGED" not in block:
            continue
        lane_m = re.search(r"(DOMEX-\S+)", block)
        if not lane_m:
            continue
        n_lanes += 1
        lane_id = lane_m.group(1)

        expect = expect_pat.search(block)
        actual = actual_pat.search(block)
        diff = diff_pat.search(block)

        if not (expect and actual):
            continue

        expect_text = expect.group(1).strip()
        actual_text = actual.group(1).strip()
        diff_text = diff.group(1).strip() if diff else ""

        # Surprise heuristics: keywords indicating divergence
        surprise = 0.0
        surprise_keywords = [
            "falsified", "failed", "unexpected", "wrong", "opposite",
            "not confirmed", "rejected", "surprised", "contradicts",
            "overestimated", "underestimated", "missed"
        ]
        confirm_keywords = [
            "confirmed", "as expected", "matches", "predicted correctly",
            "aligned", "consistent"
        ]

        combined = (actual_text + " " + diff_text).lower()
        for kw in surprise_keywords:
            if kw in combined:
                surprise += 0.3
        for kw in confirm_keywords:
            if kw in combined:
                surprise -= 0.1

        surprise = max(0.0, min(1.0, surprise))

        if surprise > 0.2:
            n_surprised += 1
            details.append({
                "lane": lane_id,
                "expect": expect_text[:80],
                "actual": actual_text[:80],
                "diff": diff_text[:60],
                "surprise": round(surprise, 2),
            })

    details.sort(key=lambda x: x["surprise"], reverse=True)
    score = n_surprised / max(n_lanes, 1)
    return {
        "score": round(score, 3),
        "details": details[:10],
        "n_lanes": n_lanes,
        "n_surprised": n_surprised,
    }


# ---------- Component 3: Frontier Surprise ----------
def compute_frontier_surprise() -> dict:
    """Frontiers with multiple experiments but no progress = stuck generative model."""
    text = _read(FRONTIER_FILE)
    if not text:
        return {"score": 0, "details": [], "n_frontiers": 0, "n_surprised": 0}

    # Frontiers use: - **F-XXX**: description... with session refs inline
    frontier_pat = re.compile(
        r"^- \*\*(?:~~)?(F-\S+?)(?:~~)?\*\*:\s*(.+?)(?=\n- \*\*F-|\n##|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    details = []
    n_frontiers = 0
    n_surprised = 0

    for m in frontier_pat.finditer(text):
        fid = m.group(1).strip()
        body = m.group(2).strip()
        n_frontiers += 1

        # Skip resolved
        if "RESOLVED" in body[:200]:
            continue

        # Count session references as proxy for experiment attempts
        session_refs = re.findall(r"S\d+", body)
        exp_count = len(set(session_refs))

        # Detect stuck signals
        blocked = any(kw in body for kw in [
            "BLOCKED", "NEEDS_WORK", "stale", "0 external",
            "unchanged", "gap=", "still undeployed",
        ])
        description = body[:120].replace("\n", " ")

        surprise = 0.0
        if exp_count >= 5 and blocked:
            surprise = 0.7
        elif exp_count >= 3 and blocked:
            surprise = 0.5
        elif exp_count >= 2 and blocked:
            surprise = 0.3

        if surprise > 0.2:
            n_surprised += 1
            details.append({
                "id": fid,
                "description": description[:80],
                "experiments": exp_count,
                "surprise": round(surprise, 2),
            })

    details.sort(key=lambda x: x["surprise"], reverse=True)
    score = n_surprised / max(n_frontiers, 1)
    return {
        "score": round(score, 3),
        "details": details[:10],
        "n_frontiers": n_frontiers,
        "n_surprised": n_surprised,
    }


# ---------- Composite Free Energy ----------
def compute_free_energy() -> dict:
    belief = compute_belief_surprise()
    expectation = compute_expectation_surprise()
    frontier = compute_frontier_surprise()

    # Weighted composite: expectation surprise is most actionable
    weights = {"belief": 0.35, "expectation": 0.40, "frontier": 0.25}
    composite = (
        weights["belief"] * belief["score"]
        + weights["expectation"] * expectation["score"]
        + weights["frontier"] * frontier["score"]
    )

    # Interpret
    if composite > 0.5:
        interpretation = "HIGH — self-model needs structural revision"
    elif composite > 0.25:
        interpretation = "MODERATE — targeted belief updates needed"
    elif composite > 0.1:
        interpretation = "LOW — self-model roughly accurate"
    else:
        interpretation = "MINIMAL — strong model-world alignment"

    return {
        "free_energy": round(composite, 3),
        "interpretation": interpretation,
        "components": {
            "belief": belief,
            "expectation": expectation,
            "frontier": frontier,
        },
        "weights": weights,
        "prescription": _prescribe(belief, expectation, frontier),
    }


def _prescribe(belief, expectation, frontier) -> list[str]:
    """Active inference: high surprise → specific action to reduce it."""
    rx = []
    if belief["n_surprised"] > 0:
        top = belief["details"][0] if belief["details"] else None
        if top:
            rx.append(
                f"RETEST {top['id']} (gap={top['session_gap']}s, "
                f"surprise={top['surprise']}): {top['falsification'][:60]}"
            )
    if expectation["n_surprised"] > 0:
        top = expectation["details"][0] if expectation["details"] else None
        if top:
            rx.append(
                f"REVISE model for {top['lane']} — predicted '{top['expect'][:40]}' "
                f"but got '{top['actual'][:40]}'"
            )
    if frontier["n_surprised"] > 0:
        top = frontier["details"][0] if frontier["details"] else None
        if top:
            rx.append(
                f"RESTRUCTURE {top['id']} ({top['experiments']} attempts, "
                f"surprise={top['surprise']}) — current approach is stuck"
            )
    if not rx:
        rx.append("No high-surprise items — self-model is well-calibrated")
    return rx


def _get_current_session() -> int:
    """Extract current session number from git log."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
            timeout=5,
        )
        m = re.search(r"\[S(\d+)\]", result.stdout)
        return int(m.group(1)) if m else 528
    except Exception:
        return 528


def main():
    parser = argparse.ArgumentParser(description="Swarm free energy (surprise) metric")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--component", choices=["belief", "expectation", "frontier"],
                        help="Single component")
    args = parser.parse_args()

    result = compute_free_energy()

    if args.component:
        result = result["components"][args.component]

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
        return

    # Human-readable report
    print(f"=== SWARM FREE ENERGY (Active Inference) ===")
    print(f"  Composite: {result['free_energy']} — {result['interpretation']}")
    print()

    for name, comp in result["components"].items():
        w = result["weights"][name]
        print(f"  [{name.upper()}] score={comp['score']} (weight={w})")
        print(f"    n={comp.get('n_beliefs', comp.get('n_lanes', comp.get('n_frontiers', '?')))} "
              f"| surprised={comp.get('n_surprised', 0)}")
        for d in comp.get("details", [])[:3]:
            did = d.get("id", d.get("lane", "?"))
            print(f"    → {did}: surprise={d['surprise']}")
        print()

    print("  Prescription:")
    for rx in result["prescription"]:
        print(f"    → {rx}")


if __name__ == "__main__":
    main()
