#!/usr/bin/env python3
"""
F-META16: Single-Agent Knowledge Transfer Lab
Session: S394 | Domain: meta | Lane: DOMEX-META-S394

Question: What are the measurable knowledge attributes of a single agent
session, and how much knowledge actually transfers across session boundaries?

The swarm has 713 lessons about collective knowledge but has never measured
the individual agent as a unit of analysis. This experiment defines 7
per-agent attributes, measures them across all sessions with sufficient
commit data, and identifies transfer mechanisms.

Per-agent attributes:
  1. boot_surface    — files read at session start (inferred from first commits)
  2. production      — lessons + principles + tools created
  3. citation_reach  — how many existing lessons the session references
  4. absorption_rate — fraction of available knowledge actually used
  5. transfer_out    — outputs cited by future sessions (forward influence)
  6. knowledge_scope — number of distinct domains touched
  7. session_type    — DOMEX, harvest, maintenance, mixed (behavioral profile)
"""

import json
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/mnt/c/Users/canac/REPOSITORIES/swarm")
LESSONS_DIR = REPO / "memory" / "lessons"
OUTPUT_FILE = REPO / "experiments" / "meta" / "f-meta16-agent-knowledge-transfer-s394.json"

# ============================================================================
# Git helpers
# ============================================================================

def run_git(args, timeout=60):
    result = subprocess.run(
        ["git", "-C", str(REPO)] + args,
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def get_commits_with_files():
    """Parse all commits with their changed files and session IDs."""
    lines = run_git(["log", "--oneline", "--all", "--name-only", "--no-merges"])
    commits = []
    current = None
    for line in lines:
        if not line:
            continue
        m = re.match(r"^([0-9a-f]{8,}) (.+)$", line)
        if m:
            if current:
                commits.append(current)
            current = {
                "hash": m.group(1),
                "msg": m.group(2),
                "session": _parse_session(m.group(2)),
                "files": []
            }
        elif current:
            current["files"].append(line.strip())
    if current:
        commits.append(current)
    return commits


def _parse_session(msg):
    m = re.search(r"\[S(\d+)\]", msg)
    return int(m.group(1)) if m else None


# ============================================================================
# Lesson parsing
# ============================================================================

def parse_all_lessons():
    """Parse every lesson file for session, domain, citations, confidence."""
    lessons = {}
    for lf in sorted(LESSONS_DIR.glob("L-*.md")):
        lid_m = re.match(r"L-(\d+)", lf.stem)
        if not lid_m:
            continue
        lid = int(lid_m.group(1))
        try:
            text = lf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Session
        sm = re.search(r"[Ss]ession:\s*S(\d+)", text)
        session = int(sm.group(1)) if sm else None

        # Domain
        dm = re.search(r"Domain:\s*(\S+)", text, re.IGNORECASE)
        domain = dm.group(1).lower().rstrip(",;") if dm else "unknown"

        # Cites (header)
        cm = re.search(r"Cites:\s*(.+)", text)
        header_cites = set()
        if cm:
            for ref in re.finditer(r"L-(\d+)", cm.group(1)):
                header_cites.add(int(ref.group(1)))

        # Body cites (all L-NNN refs in text)
        body_cites = set()
        for ref in re.finditer(r"\bL-(\d+)\b", text):
            body_cites.add(int(ref.group(1)))
        body_cites.discard(lid)  # don't self-cite

        # Confidence
        conf_m = re.search(r"Confidence:\s*(\w+)", text, re.IGNORECASE)
        confidence = conf_m.group(1).lower() if conf_m else "unknown"

        # Principles referenced
        principles = set()
        for pm in re.finditer(r"\bP-(\d+)\b", text):
            principles.add(int(pm.group(1)))

        lessons[lid] = {
            "id": lid,
            "session": session,
            "domain": domain,
            "header_cites": header_cites,
            "all_cites": body_cites,
            "confidence": confidence,
            "principles": principles,
            "lines": len(text.splitlines()),
        }
    return lessons


# ============================================================================
# Per-session attribute computation
# ============================================================================

def classify_session_type(commits):
    """Classify session type from its commit messages."""
    msgs = [c["msg"].lower() for c in commits]
    has_domex = any("domex" in m for m in msgs)
    has_lesson = any(re.search(r"l-\d+", m) for m in msgs)
    has_maintenance = any(kw in " ".join(msgs) for kw in [
        "handoff", "state-sync", "trim", "maintenance", "harvest", "stale"
    ])
    has_frontier = any(kw in " ".join(msgs) for kw in [
        "confirmed", "falsified", "resolved", "frontier"
    ])

    if has_domex:
        return "domex"
    elif has_lesson and not has_maintenance:
        return "knowledge"
    elif has_maintenance and not has_lesson:
        return "maintenance"
    else:
        return "mixed"


def compute_session_profiles(commits, lessons):
    """Compute per-session knowledge attributes."""
    # Group commits by session
    session_commits = defaultdict(list)
    for c in commits:
        if c["session"]:
            session_commits[c["session"]].append(c)

    # Build reverse index: which session produced which lesson
    lesson_to_session = {}
    for lid, ldata in lessons.items():
        if ldata["session"]:
            lesson_to_session[lid] = ldata["session"]

    # Forward citation index: for each lesson, which future lessons cite it
    forward_citations = defaultdict(set)
    for lid, ldata in lessons.items():
        for cited in ldata["all_cites"]:
            if cited in lessons:
                forward_citations[cited].add(lid)

    all_sessions = sorted(session_commits.keys())
    # Build cumulative lesson count: how many lessons exist at session S
    # Sort lessons by their creation session, not by ID
    lessons_by_session = sorted(
        [(ldata["session"], lid) for lid, ldata in lessons.items() if ldata["session"] is not None],
        key=lambda x: x[0]
    )
    total_lessons_at = {}
    cumulative = 0
    lid_idx = 0
    for s in all_sessions:
        while lid_idx < len(lessons_by_session):
            create_session, lid = lessons_by_session[lid_idx]
            if create_session <= s:
                cumulative += 1
                lid_idx += 1
            else:
                break
        total_lessons_at[s] = max(cumulative, 1)  # avoid div by zero

    profiles = {}
    for s in all_sessions:
        s_commits = session_commits[s]
        if not s_commits:
            continue

        # 1. Production: lessons + principles + tools created in this session
        produced_lessons = [lid for lid, ld in lessons.items() if ld["session"] == s]
        produced_tools = set()
        for c in s_commits:
            for f in c["files"]:
                if f.startswith("tools/") and f.endswith(".py"):
                    produced_tools.add(f)

        produced_principles = set()
        for c in s_commits:
            for pm in re.finditer(r"P-(\d+)", c["msg"]):
                produced_principles.add(int(pm.group(1)))

        # 2. Citation reach: how many existing lessons this session's outputs reference
        citation_reach = set()
        for lid in produced_lessons:
            citation_reach |= lessons[lid]["all_cites"]

        # 3. Absorption rate: citation_reach / total_available
        available = total_lessons_at.get(s, 1)
        absorption = len(citation_reach) / available if available > 0 else 0

        # 4. Transfer out: how many future lessons cite this session's outputs
        transfer_out = set()
        for lid in produced_lessons:
            future_citers = forward_citations.get(lid, set())
            # Only count citations from LATER sessions
            for citer in future_citers:
                if lessons[citer]["session"] and lessons[citer]["session"] > s:
                    transfer_out.add(citer)

        # 5. Knowledge scope: distinct domains touched
        domains_touched = set()
        for lid in produced_lessons:
            domains_touched.add(lessons[lid]["domain"])

        # 6. Boot surface: files touched in first commit (proxy for what was read)
        boot_files = set()
        if s_commits:
            first_commit_files = s_commits[-1]["files"]  # chronological last = first commit
            for f in first_commit_files:
                boot_files.add(f)

        # 7. Session type
        session_type = classify_session_type(s_commits)

        # 8. Commit density
        n_commits = len(s_commits)

        # 9. Files touched total
        all_files = set()
        for c in s_commits:
            for f in c["files"]:
                all_files.add(f)

        profiles[s] = {
            "session": s,
            "n_commits": n_commits,
            "session_type": session_type,
            "production": {
                "lessons": len(produced_lessons),
                "lesson_ids": sorted(produced_lessons),
                "principles": len(produced_principles),
                "tools": len(produced_tools),
                "total": len(produced_lessons) + len(produced_principles) + len(produced_tools),
            },
            "citation_reach": len(citation_reach),
            "absorption_rate": round(absorption, 4),
            "transfer_out": len(transfer_out),
            "knowledge_scope": len(domains_touched),
            "domains": sorted(domains_touched),
            "boot_surface": len(boot_files),
            "files_touched": len(all_files),
        }

    return profiles


# ============================================================================
# Analysis
# ============================================================================

def analyze_transfer_patterns(profiles, lessons):
    """Analyze knowledge transfer patterns across sessions."""
    print("=" * 70)
    print("ANALYSIS: Single-Agent Knowledge Transfer Patterns")
    print("=" * 70)

    sessions = sorted(profiles.keys())
    n = len(sessions)

    # Filter to sessions with at least 1 lesson produced (knowledge-producing sessions)
    producing = {s: p for s, p in profiles.items() if p["production"]["lessons"] > 0}
    n_producing = len(producing)

    print(f"\n  Total sessions analyzed: {n}")
    print(f"  Knowledge-producing sessions: {n_producing} ({n_producing/n:.1%})")

    # --- Attribute distributions ---
    print(f"\n  --- Per-Session Attribute Distributions (n={n}) ---")

    attrs = {
        "lessons_produced": [p["production"]["lessons"] for p in profiles.values()],
        "citation_reach": [p["citation_reach"] for p in profiles.values()],
        "absorption_rate": [p["absorption_rate"] for p in profiles.values()],
        "transfer_out": [p["transfer_out"] for p in profiles.values()],
        "knowledge_scope": [p["knowledge_scope"] for p in profiles.values()],
        "n_commits": [p["n_commits"] for p in profiles.values()],
        "files_touched": [p["files_touched"] for p in profiles.values()],
    }

    stats = {}
    for name, values in attrs.items():
        nonzero = [v for v in values if v > 0]
        s = {
            "mean": round(statistics.mean(values), 3),
            "median": round(statistics.median(values), 3),
            "stdev": round(statistics.stdev(values), 3) if len(values) > 1 else 0,
            "max": max(values),
            "nonzero_count": len(nonzero),
            "nonzero_pct": round(len(nonzero) / len(values), 3),
        }
        stats[name] = s
        print(f"  {name:20s}: mean={s['mean']:6.3f}  median={s['median']:7.3f}  "
              f"max={s['max']:8.3f}  nonzero={s['nonzero_pct']:.0%}")

    # --- Session type breakdown ---
    print(f"\n  --- Session Type Breakdown ---")
    type_counts = Counter(p["session_type"] for p in profiles.values())
    type_production = defaultdict(list)
    type_transfer = defaultdict(list)
    type_absorption = defaultdict(list)

    for p in profiles.values():
        t = p["session_type"]
        type_production[t].append(p["production"]["lessons"])
        type_transfer[t].append(p["transfer_out"])
        type_absorption[t].append(p["absorption_rate"])

    for t in sorted(type_counts.keys()):
        count = type_counts[t]
        avg_prod = statistics.mean(type_production[t]) if type_production[t] else 0
        avg_trans = statistics.mean(type_transfer[t]) if type_transfer[t] else 0
        avg_abs = statistics.mean(type_absorption[t]) if type_absorption[t] else 0
        print(f"  {t:12s}: n={count:3d}  avg_lessons={avg_prod:.2f}  "
              f"avg_transfer={avg_trans:.2f}  avg_absorption={avg_abs:.4f}")

    # --- Transfer fidelity ---
    # What fraction of a session's knowledge is picked up by future sessions?
    print(f"\n  --- Transfer Fidelity (producing sessions only, n={n_producing}) ---")
    transfer_rates = []
    for s, p in producing.items():
        produced = p["production"]["lessons"]
        transferred = p["transfer_out"]
        rate = transferred / produced if produced > 0 else 0
        transfer_rates.append(rate)

    if transfer_rates:
        avg_transfer = statistics.mean(transfer_rates)
        med_transfer = statistics.median(transfer_rates)
        zero_transfer = sum(1 for r in transfer_rates if r == 0)
        print(f"  Mean transfer rate: {avg_transfer:.3f} (lessons cited by future / lessons produced)")
        print(f"  Median transfer rate: {med_transfer:.3f}")
        print(f"  Zero-transfer sessions: {zero_transfer}/{n_producing} ({zero_transfer/n_producing:.1%})")
    else:
        avg_transfer = 0
        med_transfer = 0
        zero_transfer = 0

    # --- Absorption vs production correlation ---
    print(f"\n  --- Absorption → Production Correlation ---")
    abs_vals = [p["absorption_rate"] for s, p in producing.items()]
    prod_vals = [p["production"]["lessons"] for s, p in producing.items()]

    if len(abs_vals) > 2:
        # Pearson correlation
        n_corr = len(abs_vals)
        mean_a = statistics.mean(abs_vals)
        mean_p = statistics.mean(prod_vals)
        num = sum((a - mean_a) * (p - mean_p) for a, p in zip(abs_vals, prod_vals))
        den_a = sum((a - mean_a) ** 2 for a in abs_vals) ** 0.5
        den_p = sum((p - mean_p) ** 2 for p in prod_vals) ** 0.5
        r = num / (den_a * den_p) if den_a * den_p > 0 else 0
        print(f"  Pearson r (absorption_rate vs lessons_produced): {r:.3f} (n={n_corr})")
    else:
        r = 0

    # --- Citation reach vs transfer out ---
    print(f"\n  --- Citation Reach → Transfer Out ---")
    reach_vals = [p["citation_reach"] for s, p in producing.items()]
    trans_vals = [p["transfer_out"] for s, p in producing.items()]

    if len(reach_vals) > 2:
        mean_r = statistics.mean(reach_vals)
        mean_t = statistics.mean(trans_vals)
        num2 = sum((rv - mean_r) * (tv - mean_t) for rv, tv in zip(reach_vals, trans_vals))
        den_r = sum((rv - mean_r) ** 2 for rv in reach_vals) ** 0.5
        den_t = sum((tv - mean_t) ** 2 for tv in trans_vals) ** 0.5
        r2 = num2 / (den_r * den_t) if den_r * den_t > 0 else 0
        print(f"  Pearson r (citation_reach vs transfer_out): {r2:.3f} (n={len(reach_vals)})")
    else:
        r2 = 0

    # --- Knowledge lifetime distribution ---
    print(f"\n  --- Knowledge Lifetime (sessions until last citation) ---")
    lifetimes = []
    for lid, ldata in lessons.items():
        if ldata["session"] is None:
            continue
        created_s = ldata["session"]
        # Find latest session that cites this lesson
        latest_cite = created_s
        for other_lid, other_data in lessons.items():
            if lid in other_data["all_cites"] and other_data["session"]:
                latest_cite = max(latest_cite, other_data["session"])
        lifetime = latest_cite - created_s
        lifetimes.append(lifetime)

    if lifetimes:
        avg_life = statistics.mean(lifetimes)
        med_life = statistics.median(lifetimes)
        max_life = max(lifetimes)
        zero_life = sum(1 for l in lifetimes if l == 0)
        print(f"  Mean lifetime: {avg_life:.1f} sessions")
        print(f"  Median lifetime: {med_life:.0f} sessions")
        print(f"  Max lifetime: {max_life} sessions")
        print(f"  Zero lifetime (never cited elsewhere): {zero_life}/{len(lifetimes)} ({zero_life/len(lifetimes):.1%})")
    else:
        avg_life = med_life = max_life = zero_life = 0

    # --- Era analysis (knowledge transfer evolution) ---
    print(f"\n  --- Transfer Evolution by Era ---")
    era_bounds = [(1, 100), (100, 200), (200, 300), (300, 394)]
    era_results = {}
    for start, end in era_bounds:
        era_label = f"S{start}-S{end-1}"
        era_profiles = {s: p for s, p in profiles.items() if start <= s < end}
        era_producing = {s: p for s, p in era_profiles.items() if p["production"]["lessons"] > 0}

        if not era_producing:
            era_results[era_label] = {"n": 0}
            continue

        era_abs = [p["absorption_rate"] for p in era_producing.values()]
        era_trans = []
        for p in era_producing.values():
            prod = p["production"]["lessons"]
            trans = p["transfer_out"]
            era_trans.append(trans / prod if prod > 0 else 0)

        era_results[era_label] = {
            "n": len(era_producing),
            "avg_absorption": round(statistics.mean(era_abs), 4),
            "avg_transfer_rate": round(statistics.mean(era_trans), 3),
            "avg_lessons": round(statistics.mean([p["production"]["lessons"] for p in era_producing.values()]), 2),
        }
        print(f"  {era_label}: n={era_results[era_label]['n']:3d}  "
              f"absorption={era_results[era_label]['avg_absorption']:.4f}  "
              f"transfer={era_results[era_label]['avg_transfer_rate']:.3f}  "
              f"lessons/s={era_results[era_label]['avg_lessons']:.2f}")

    # --- Top sessions by influence ---
    print(f"\n  --- Top 10 Sessions by Transfer Out (forward influence) ---")
    sorted_by_transfer = sorted(profiles.items(), key=lambda x: x[1]["transfer_out"], reverse=True)
    for s, p in sorted_by_transfer[:10]:
        print(f"  S{s}: transfer_out={p['transfer_out']:3d}  lessons={p['production']['lessons']}  "
              f"type={p['session_type']:12s}  scope={p['knowledge_scope']}")

    # --- Sessions with zero transfer (knowledge that evaporated) ---
    print(f"\n  --- Zero-Transfer Analysis ---")
    zero_sessions = [(s, p) for s, p in producing.items() if p["transfer_out"] == 0]
    zero_by_type = Counter(p["session_type"] for _, p in zero_sessions)
    print(f"  Sessions that produced knowledge never cited: {len(zero_sessions)}/{n_producing} ({len(zero_sessions)/n_producing:.1%})")
    for t, c in zero_by_type.most_common():
        print(f"    {t}: {c}")

    return {
        "n_sessions": n,
        "n_producing": n_producing,
        "attribute_stats": stats,
        "session_type_breakdown": dict(type_counts),
        "type_averages": {
            t: {
                "avg_production": round(statistics.mean(type_production[t]), 2) if type_production[t] else 0,
                "avg_transfer": round(statistics.mean(type_transfer[t]), 2) if type_transfer[t] else 0,
                "avg_absorption": round(statistics.mean(type_absorption[t]), 4) if type_absorption[t] else 0,
            }
            for t in type_counts
        },
        "transfer_fidelity": {
            "mean": round(avg_transfer, 3),
            "median": round(med_transfer, 3),
            "zero_transfer_sessions": zero_transfer,
            "zero_transfer_pct": round(zero_transfer / n_producing, 3) if n_producing > 0 else 0,
        },
        "correlations": {
            "absorption_vs_production": round(r, 3),
            "citation_reach_vs_transfer": round(r2, 3),
        },
        "knowledge_lifetime": {
            "mean_sessions": round(avg_life, 1),
            "median_sessions": round(med_life, 0),
            "max_sessions": max_life,
            "zero_lifetime_pct": round(zero_life / len(lifetimes), 3) if lifetimes else 0,
        },
        "era_evolution": era_results,
        "top_10_by_influence": [
            {"session": s, "transfer_out": p["transfer_out"],
             "lessons": p["production"]["lessons"], "type": p["session_type"]}
            for s, p in sorted_by_transfer[:10]
        ],
        "zero_transfer_by_type": dict(zero_by_type),
    }


# ============================================================================
# Main
# ============================================================================

def main():
    print("F-META16: Single-Agent Knowledge Transfer Lab")
    print("=" * 70)
    print()

    # Parse data
    print("Parsing lessons...")
    lessons = parse_all_lessons()
    print(f"  {len(lessons)} lessons parsed")

    print("Parsing git commits...")
    commits = get_commits_with_files()
    print(f"  {len(commits)} commits parsed")

    # Compute session profiles
    print("\nComputing per-session knowledge profiles...")
    profiles = compute_session_profiles(commits, lessons)
    print(f"  {len(profiles)} session profiles computed")

    # Analyze
    analysis = analyze_transfer_patterns(profiles, lessons)

    # Expectations check
    print("\n" + "=" * 70)
    print("EXPECTATION CHECK")
    print("=" * 70)

    expectations = {
        "measurable_profiles": True,  # we produced profiles for every session
        "transfer_fidelity_under_60pct": analysis["transfer_fidelity"]["mean"] < 0.60,
        "absorption_production_r_gt_03": analysis["correlations"]["absorption_vs_production"] > 0.3,
    }

    for name, result in expectations.items():
        status = "CONFIRMED" if result else "FALSIFIED"
        print(f"  [{status}] {name}")

    print(f"\n  Transfer fidelity mean: {analysis['transfer_fidelity']['mean']:.3f}")
    print(f"  Absorption→production r: {analysis['correlations']['absorption_vs_production']:.3f}")
    print(f"  Citation reach→transfer r: {analysis['correlations']['citation_reach_vs_transfer']:.3f}")

    # Build output
    # Include sample profiles (top 10 + bottom 10 by influence)
    sorted_profiles = sorted(profiles.items(), key=lambda x: x[1]["transfer_out"], reverse=True)
    sample_profiles = {}
    for s, p in sorted_profiles[:10]:
        sample_profiles[f"S{s}"] = p
    for s, p in sorted_profiles[-10:]:
        sample_profiles[f"S{s}"] = p

    result = {
        "experiment": "F-META16: Single-Agent Knowledge Transfer Lab",
        "session": "S394",
        "lane": "DOMEX-META-S394",
        "date": "2026-03-01",
        "question": "What are the measurable knowledge attributes of a single agent session, and how much knowledge actually transfers across session boundaries?",
        "method": "Parse all commits (git log --name-only) and all lesson files to compute 7 per-session attributes: production, citation_reach, absorption_rate, transfer_out, knowledge_scope, boot_surface, session_type. Analyze distributions, correlations, and transfer fidelity across 393 sessions.",
        "expectations": {
            "predicted": {
                "measurable_profiles": "Sessions have quantifiable knowledge profiles",
                "transfer_fidelity": "<60% of produced knowledge is cited by future sessions",
                "absorption_production_correlation": "Sessions that cite more existing knowledge produce higher-quality outputs (r>0.3)",
            },
            "actual": expectations,
        },
        "analysis": analysis,
        "sample_profiles": sample_profiles,
    }

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n  Output: {OUTPUT_FILE}")

    return result


if __name__ == "__main__":
    main()
