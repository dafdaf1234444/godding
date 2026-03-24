#!/usr/bin/env python3
"""fairness_audit.py — PHIL-25 Fairness Measurement (L-1193)

Measures 5 fairness dimensions:
  1. Attention: BLIND-SPOT % — knowledge receiving zero attention
  2. Dispatch: Gini coefficient of domain dispatch frequency
  3. Authority: Human signal rejection rate (0% = total deference)
  4. Investment: Zombie tool rate (created but never adopted)
  5. External: External beneficiary/output count (PHIL-16)

Fairness is not equal treatment — it is appropriate relationship (PHIL-25).
Each dimension has a threshold below which the swarm is being unfair to
some component (knowledge, domains, AI judgment, tool investment, the world).

Usage:
  python3 tools/fairness_audit.py          # human-readable report
  python3 tools/fairness_audit.py --json   # machine-readable JSON
  python3 tools/fairness_audit.py --save   # save experiment artifact
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from swarm_io import REPO_ROOT, read_text, lesson_paths, session_number

# --- Thresholds (what counts as "fair enough") ---
BLINDSPOT_FAIR = 0.12      # <=12% BLIND-SPOT is fair attention
GINI_FAIR = 0.45           # <=0.45 Gini is fair dispatch
REJECTION_FAIR = 0.05      # >=5% rejection rate = AI exercises judgment
ZOMBIE_FAIR = 0.50         # <=50% zombie rate is fair to investment
EXTERNAL_FAIR = 1          # >=1 external output = fair to the world


def measure_attention() -> dict:
    """Measure BLIND-SPOT rate from INDEX.md and citation data."""
    index_text = read_text(REPO_ROOT / "memory" / "INDEX.md")
    lessons = lesson_paths()
    total = len(lessons)

    # Count lessons that appear in INDEX.md themes
    themed = 0
    for lp in lessons:
        lid = lp.stem  # e.g., L-1193
        if lid in index_text:
            themed += 1

    # Count lessons with zero outbound citations
    zero_cite = 0
    for lp in lessons:
        text = read_text(lp)
        cites_match = re.search(r'Cites:\s*(.+)', text)
        has_body_refs = bool(re.search(r'L-\d+', text.split('Cites:')[0] if 'Cites:' in text else ''))
        if not cites_match and not has_body_refs:
            zero_cite += 1

    # BLIND-SPOT = not in INDEX AND no outbound citations
    blind = 0
    for lp in lessons:
        lid = lp.stem
        text = read_text(lp)
        in_index = lid in index_text
        has_cites = bool(re.search(r'Cites:\s*\S', text))
        has_body_refs = bool(re.search(r'L-\d+', text.split('Cites:')[0] if 'Cites:' in text else ''))
        if not in_index and not has_cites and not has_body_refs:
            blind += 1

    rate = blind / total if total > 0 else 0
    return {
        "dimension": "attention",
        "metric": "blind_spot_rate",
        "value": round(rate, 3),
        "threshold": BLINDSPOT_FAIR,
        "fair": rate <= BLINDSPOT_FAIR,
        "total_lessons": total,
        "blind_spot_count": blind,
        "zero_cite_count": zero_cite,
        "verdict": "FAIR" if rate <= BLINDSPOT_FAIR else "UNFAIR"
    }


def measure_dispatch() -> dict:
    """Measure Gini coefficient of domain dispatch from SWARM-LANES.md."""
    lanes_text = read_text(REPO_ROOT / "tasks" / "SWARM-LANES.md")
    domain_counts: Counter = Counter()

    for line in lanes_text.splitlines():
        if '|' not in line or line.strip().startswith('|') and '---' in line:
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 10:
            continue
        lane_id = parts[2] if len(parts) > 2 else ""
        if not lane_id or not re.match(r'DOMEX-', lane_id):
            continue
        # Extract domain from lane ID: DOMEX-<DOMAIN>-S<N>
        m = re.match(r'DOMEX-(\w+)-S\d+', lane_id)
        if m:
            domain_counts[m.group(1)] += 1

    if not domain_counts:
        return {
            "dimension": "dispatch",
            "metric": "gini_coefficient",
            "value": 0.0,
            "threshold": GINI_FAIR,
            "fair": True,
            "domain_count": 0,
            "verdict": "NO DATA"
        }

    values = sorted(domain_counts.values())
    n = len(values)
    if n == 0 or sum(values) == 0:
        gini = 0.0
    else:
        cumulative = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(values))
        gini = cumulative / (n * sum(values))

    return {
        "dimension": "dispatch",
        "metric": "gini_coefficient",
        "value": round(gini, 3),
        "threshold": GINI_FAIR,
        "fair": gini <= GINI_FAIR,
        "domain_count": n,
        "total_lanes": sum(domain_counts.values()),
        "top_3": domain_counts.most_common(3),
        "verdict": "FAIR" if gini <= GINI_FAIR else "UNFAIR"
    }


def measure_authority() -> dict:
    """Measure human signal rejection rate from SIGNALS.md."""
    signals_text = read_text(REPO_ROOT / "tasks" / "SIGNALS.md")
    total_human = 0
    rejected = 0

    for line in signals_text.splitlines():
        if 'human' in line.lower() and ('SIG-' in line or 'directive' in line.lower()):
            total_human += 1
        if 'REJECTED' in line or 'rejected' in line:
            rejected += 1

    # Also check HUMAN.md for signal count
    human_text = read_text(REPO_ROOT / "memory" / "HUMAN.md")
    m = re.search(r'0/(\d+)\+?\s*signals?\s*rejected', human_text)
    if m:
        total_human = max(total_human, int(m.group(1)))

    rate = rejected / total_human if total_human > 0 else 0
    return {
        "dimension": "authority",
        "metric": "signal_rejection_rate",
        "value": round(rate, 3),
        "threshold": REJECTION_FAIR,
        "fair": rate >= REJECTION_FAIR,
        "total_signals": total_human,
        "rejected": rejected,
        "deference_rate": round(1 - rate, 3),
        "verdict": "FAIR" if rate >= REJECTION_FAIR else "UNFAIR — 100% deference"
    }


def measure_investment() -> dict:
    """Measure zombie tool rate from tools/ directory."""
    tools_dir = REPO_ROOT / "tools"
    if not tools_dir.exists():
        return {"dimension": "investment", "verdict": "NO DATA"}

    tool_files = [f for f in tools_dir.glob("*.py") if f.name != "__pycache__"]
    total = len(tool_files)

    # Check zombie_drops.json for zombie classification
    zombie_data = {}
    zombie_path = REPO_ROOT / "tools" / "zombie_drops.json"
    if zombie_path.exists():
        try:
            zombie_data = json.loads(read_text(zombie_path))
        except (json.JSONDecodeError, Exception):
            pass

    # Count tools referenced in orient.py, check.sh, periodics.json, CLAUDE.md
    referenced = set()
    ref_files = [
        REPO_ROOT / "tools" / "orient.py",
        REPO_ROOT / "tools" / "check.sh",
        REPO_ROOT / "tools" / "periodics.json",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "SWARM.md",
    ]
    for rf in ref_files:
        if rf.exists():
            text = read_text(rf)
            for tf in tool_files:
                if tf.stem in text or tf.name in text:
                    referenced.add(tf.name)

    zombie_count = total - len(referenced)
    rate = zombie_count / total if total > 0 else 0

    return {
        "dimension": "investment",
        "metric": "zombie_tool_rate",
        "value": round(rate, 3),
        "threshold": ZOMBIE_FAIR,
        "fair": rate <= ZOMBIE_FAIR,
        "total_tools": total,
        "referenced": len(referenced),
        "zombie_count": zombie_count,
        "verdict": "FAIR" if rate <= ZOMBIE_FAIR else "UNFAIR"
    }


def measure_external() -> dict:
    """Measure external beneficiary/output count (PHIL-16 compliance)."""
    # Check for external outputs: docs that could serve external users
    external_indicators = [
        REPO_ROOT / "docs" / "QUESTIONS.md",
        REPO_ROOT / "docs" / "HUMAN-GUIDE.md",
    ]
    external_count = sum(1 for p in external_indicators if p.exists())

    # Check PHIL-16 ground truth
    phil_text = read_text(REPO_ROOT / "beliefs" / "PHILOSOPHY.md")
    m = re.search(r'(\d+)\s*external\s*beneficiar', phil_text)
    phil16_beneficiaries = int(m.group(1)) if m else 0

    # Check for any external-facing commits
    try:
        external_commits = subprocess.run(
            ["git", "log", "--oneline", "--grep=external", "-5"],
            capture_output=True, text=True, timeout=5, cwd=str(REPO_ROOT)
        ).stdout.strip().count('\n') + 1 if subprocess.run(
            ["git", "log", "--oneline", "--grep=external", "-5"],
            capture_output=True, text=True, timeout=5, cwd=str(REPO_ROOT)
        ).stdout.strip() else 0
    except Exception:
        external_commits = 0

    return {
        "dimension": "external",
        "metric": "external_output_count",
        "value": external_count,
        "threshold": EXTERNAL_FAIR,
        "fair": external_count >= EXTERNAL_FAIR,
        "phil16_beneficiaries": phil16_beneficiaries,
        "external_docs": external_count,
        "verdict": "FAIR" if external_count >= EXTERNAL_FAIR else "UNFAIR — 0 external benefit"
    }


def run_audit() -> dict:
    """Run all 5 fairness dimensions."""
    results = {
        "session": session_number(),
        "dimensions": [],
        "summary": {}
    }

    measures = [
        measure_attention,
        measure_dispatch,
        measure_authority,
        measure_investment,
        measure_external,
    ]

    fair_count = 0
    for fn in measures:
        try:
            result = fn()
            results["dimensions"].append(result)
            if result.get("fair"):
                fair_count += 1
        except Exception as e:
            results["dimensions"].append({
                "dimension": fn.__name__.replace("measure_", ""),
                "error": str(e),
                "verdict": "ERROR"
            })

    total = len(measures)
    results["summary"] = {
        "fair_dimensions": fair_count,
        "total_dimensions": total,
        "fairness_score": round(fair_count / total, 2) if total > 0 else 0,
        "overall": "FAIR" if fair_count >= 4 else "PARTIALLY FAIR" if fair_count >= 2 else "UNFAIR"
    }
    return results


def print_report(results: dict) -> None:
    """Print human-readable fairness report."""
    print(f"=== FAIRNESS AUDIT — PHIL-25 (S{results['session']}) ===\n")

    for dim in results["dimensions"]:
        name = dim.get("dimension", "?").upper()
        verdict = dim.get("verdict", "?")
        value = dim.get("value", "?")
        threshold = dim.get("threshold", "?")
        fair_mark = "✓" if dim.get("fair") else "✗"

        print(f"  {fair_mark} {name}: {value} (threshold: {threshold}) — {verdict}")

        # Extra detail per dimension
        if name == "ATTENTION":
            print(f"    {dim.get('blind_spot_count', '?')}/{dim.get('total_lessons', '?')} lessons invisible")
        elif name == "DISPATCH":
            top3 = dim.get("top_3", [])
            if top3:
                top_str = ", ".join(f"{d}={c}" for d, c in top3)
                print(f"    {dim.get('domain_count', '?')} domains, top: {top_str}")
        elif name == "AUTHORITY":
            print(f"    {dim.get('rejected', 0)}/{dim.get('total_signals', '?')} signals rejected ({dim.get('deference_rate', '?')} deference)")
        elif name == "INVESTMENT":
            print(f"    {dim.get('zombie_count', '?')}/{dim.get('total_tools', '?')} tools unreferenced")
        elif name == "EXTERNAL":
            print(f"    {dim.get('external_docs', 0)} external-facing documents")

    s = results["summary"]
    print(f"\n  OVERALL: {s['overall']} ({s['fair_dimensions']}/{s['total_dimensions']} dimensions)")
    print(f"  Fairness score: {s['fairness_score']}")


def save_artifact(results: dict) -> str:
    """Save experiment JSON artifact."""
    exp_dir = REPO_ROOT / "experiments" / "meta"
    exp_dir.mkdir(parents=True, exist_ok=True)
    session = results["session"]
    path = exp_dir / f"f-phil25-fairness-audit-s{session}.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return str(path)


def main():
    parser = argparse.ArgumentParser(description="PHIL-25 fairness audit")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--save", action="store_true", help="Save experiment artifact")
    args = parser.parse_args()

    results = run_audit()

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print_report(results)

    if args.save:
        path = save_artifact(results)
        print(f"\n  Artifact saved: {path}")


if __name__ == "__main__":
    main()
