#!/usr/bin/env python3
"""F-EVO3: Protocol mutation cadence measurement.

Measures correlation between protocol file mutations and knowledge quality/stability.
Rebuilt after S363 tool consolidation. Based on S352 methodology (L-563).
"""

import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESSION_LOG = ROOT / "memory" / "SESSION-LOG.md"

# Core protocol files (same set as S352 measurement)
PROTOCOL_FILES = [
    "SWARM.md", "beliefs/CORE.md", "tools/maintenance.py",
    "tools/check.sh", "tools/check.ps1", "tools/orient.py", "tools/orient.ps1",
]


def build_session_file_map():
    """Bulk scan: one git log call to map session→files changed."""
    session_files = {}
    try:
        # Single git log call: get all commits with session tags
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "--name-only", "--format=%s"],
            capture_output=True, text=True, timeout=60, cwd=ROOT,
        )
        if not result.stdout:
            return session_files

        current_session = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            # Check if this is a commit subject line with [S<N>]
            m = re.search(r'\[S(\d+)\]', line)
            if m:
                current_session = int(m.group(1))
                if current_session not in session_files:
                    session_files[current_session] = set()
            elif current_session is not None and not line.startswith('['):
                # This is a filename
                session_files.setdefault(current_session, set()).add(line)
    except Exception as e:
        print(f"WARN: git log failed: {e}")
    return session_files


def parse_session_log():
    """Parse SESSION-LOG into per-session records."""
    sessions = []
    text = SESSION_LOG.read_text(encoding="utf-8")
    for line in text.splitlines():
        m = re.match(r'S(\d+)\w*\s*\|\s*[\d-]+\s*\|\s*\+(\d+)L.*?\+(\d+)P.*?\|\s*(.*)', line)
        if not m:
            continue
        snum = int(m.group(1))
        lessons = int(m.group(2))
        principles = int(m.group(3))
        summary = m.group(4).strip()

        # Quality indicators from summary
        lp = lessons + principles
        has_frontier = bool(re.search(r'F[-\d]|frontier', summary, re.I))
        has_due_urgent = bool(re.search(r'DUE|URGENT|maintenance|health.check', summary, re.I))
        has_destab = bool(re.search(r'DUE|URGENT|fail|broken|fix|corrupt|collision|bug', summary, re.I))
        has_overhead = bool(re.search(r'maintenance|compact|trim|overhead|periodic|sync', summary, re.I))

        sessions.append({
            "session_num": snum,
            "lessons": lessons,
            "principles": principles,
            "lp": lp,
            "has_frontier": has_frontier,
            "has_due_urgent": has_due_urgent,
            "has_destab": has_destab,
            "has_overhead": has_overhead,
            "summary": summary,
        })

    return sessions


def pearson_r(xs, ys):
    """Pearson correlation coefficient."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    sy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    return round(cov / (sx * sy), 4) if sx > 0 and sy > 0 else 0.0


def main():
    sessions = parse_session_log()
    # Deduplicate by session number (keep first entry per session)
    seen = set()
    unique = []
    for s in sessions:
        if s["session_num"] not in seen:
            unique.append(s)
            seen.add(s["session_num"])
    unique.sort(key=lambda x: x["session_num"])

    print(f"Parsed {len(unique)} unique sessions from SESSION-LOG")

    # Check protocol file mutations per session via bulk git log
    print("Scanning git log for protocol file mutations (bulk)...")
    session_file_map = build_session_file_map()
    print(f"  Found file data for {len(session_file_map)} sessions in git log")
    protocol_touches = Counter()
    for s in unique:
        snum = s["session_num"]
        files = session_file_map.get(snum, set())
        mutations = [f for f in PROTOCOL_FILES if f in files]
        s["protocol_mutations"] = len(mutations)
        s["has_mutation"] = len(mutations) > 0
        for f in mutations:
            protocol_touches[f] += 1

    mutation_count = sum(1 for s in unique if s["has_mutation"])
    print(f"Mutation sessions: {mutation_count}/{len(unique)} ({100*mutation_count/len(unique):.1f}%)")
    print(f"Top protocol files: {protocol_touches.most_common(5)}")

    # Compute correlations
    mutations = [1 if s["has_mutation"] else 0 for s in unique]
    quality = [s["lp"] for s in unique]
    overhead = [1 if s["has_overhead"] else 0 for s in unique]
    frontier = [1 if s["has_frontier"] else 0 for s in unique]
    destab = [1 if s["has_destab"] else 0 for s in unique]
    due_urgent = [1 if s["has_due_urgent"] else 0 for s in unique]

    global_corr = {
        "mutation_vs_quality": pearson_r(mutations, quality),
        "mutation_vs_overhead": pearson_r(mutations, overhead),
        "mutation_vs_frontier": pearson_r(mutations, frontier),
    }
    global_stability = {
        "mutation_vs_destabilization": pearson_r(mutations, destab),
        "mutation_vs_due_urgent": pearson_r(mutations, due_urgent),
    }

    print(f"\nGlobal correlations (n={len(unique)}):")
    for k, v in global_corr.items():
        print(f"  {k}: {v}")
    print(f"Global stability:")
    for k, v in global_stability.items():
        print(f"  {k}: {v}")

    # Recent-20 window
    recent = unique[-20:]
    r_mutations = [1 if s["has_mutation"] else 0 for s in recent]
    r_quality = [s["lp"] for s in recent]
    r_destab = [1 if s["has_destab"] else 0 for s in recent]
    r_due = [1 if s["has_due_urgent"] else 0 for s in recent]
    r_frontier = [1 if s["has_frontier"] else 0 for s in recent]

    recent_corr = {
        "mutation_vs_quality": pearson_r(r_mutations, r_quality),
        "mutation_vs_destabilization": pearson_r(r_mutations, r_destab),
        "mutation_vs_due_urgent": pearson_r(r_mutations, r_due),
        "mutation_vs_frontier": pearson_r(r_mutations, r_frontier),
    }
    recent_range = f"S{recent[0]['session_num']}-S{recent[-1]['session_num']}"
    print(f"\nRecent-20 window ({recent_range}):")
    for k, v in recent_corr.items():
        print(f"  {k}: {v}")

    # Bin comparison: mutation vs no-mutation sessions
    mut_sessions = [s for s in unique if s["has_mutation"]]
    no_mut = [s for s in unique if not s["has_mutation"]]
    bin_comp = {
        "mutation": {
            "n": len(mut_sessions),
            "avg_lp": round(sum(s["lp"] for s in mut_sessions) / len(mut_sessions), 3) if mut_sessions else 0,
            "avg_destab": round(sum(1 for s in mut_sessions if s["has_destab"]) / len(mut_sessions), 3) if mut_sessions else 0,
        },
        "no_mutation": {
            "n": len(no_mut),
            "avg_lp": round(sum(s["lp"] for s in no_mut) / len(no_mut), 3) if no_mut else 0,
            "avg_destab": round(sum(1 for s in no_mut if s["has_destab"]) / len(no_mut), 3) if no_mut else 0,
        },
    }
    print(f"\nBin comparison:")
    print(f"  Mutation sessions: n={bin_comp['mutation']['n']}, avg L+P={bin_comp['mutation']['avg_lp']}, destab rate={bin_comp['mutation']['avg_destab']}")
    print(f"  No-mutation: n={bin_comp['no_mutation']['n']}, avg L+P={bin_comp['no_mutation']['avg_lp']}, destab rate={bin_comp['no_mutation']['avg_destab']}")

    # Compare with S352 baseline
    s352_baseline = {
        "mutation_vs_quality": 0.3897,
        "mutation_vs_destabilization": 0.1446,
        "mutation_vs_overhead": 0.0961,
        "recent_destab": -0.2347,
    }
    print(f"\n=== Comparison with S352 baseline ===")
    mv_q = global_corr["mutation_vs_quality"]
    mv_d = global_stability["mutation_vs_destabilization"]
    mv_o = global_corr["mutation_vs_overhead"]
    r_d = recent_corr["mutation_vs_destabilization"]

    print(f"  mutation_vs_quality:  S352={s352_baseline['mutation_vs_quality']:.4f} → S374={mv_q}")
    print(f"  mutation_vs_destab:   S352={s352_baseline['mutation_vs_destabilization']:.4f} → S374={mv_d}")
    print(f"  mutation_vs_overhead: S352={s352_baseline['mutation_vs_overhead']:.4f} → S374={mv_o}")
    print(f"  recent-20 destab:    S352={s352_baseline['recent_destab']:.4f} → S374={r_d}")

    # Stability verdict
    quality_stable = mv_q is not None and 0.25 <= mv_q <= 0.55
    destab_stable = mv_d is not None and -0.05 <= mv_d <= 0.30
    recent_safe = r_d is not None and r_d < 0.20
    all_stable = quality_stable and destab_stable and recent_safe

    print(f"\n=== VERDICT ===")
    print(f"  Quality coupling stable (0.25-0.55): {'YES' if quality_stable else 'NO'} ({mv_q})")
    print(f"  Destab coupling stable (-0.05-0.30): {'YES' if destab_stable else 'NO'} ({mv_d})")
    print(f"  Recent-20 destab safe (<0.20):       {'YES' if recent_safe else 'NO'} ({r_d})")
    print(f"  → F-EVO3: {'RESOLVED (cadence self-regulates)' if all_stable else 'STILL NEAR-RESOLVED'}")

    # Build artifact
    artifact = {
        "frontier": "F-EVO3",
        "session": os.environ.get("SWARM_SESSION", "S374"),
        "method": "Protocol mutation cadence correlation, global + recent-20 window",
        "n_sessions": len(unique),
        "protocol_files": PROTOCOL_FILES,
        "protocol_file_touches": dict(protocol_touches.most_common()),
        "mutation_rate": round(mutation_count / len(unique), 4),
        "correlation_global": global_corr,
        "correlation_stability_global": global_stability,
        "correlation_recent_20": recent_corr,
        "recent_20_range": recent_range,
        "bin_comparison": bin_comp,
        "s352_comparison": {
            "mutation_vs_quality": {"s352": s352_baseline["mutation_vs_quality"], "s374": mv_q},
            "mutation_vs_destab": {"s352": s352_baseline["mutation_vs_destabilization"], "s374": mv_d},
            "mutation_vs_overhead": {"s352": s352_baseline["mutation_vs_overhead"], "s374": mv_o},
            "recent_destab": {"s352": s352_baseline["recent_destab"], "s374": r_d},
        },
        "stability_verdict": {
            "quality_stable": quality_stable,
            "destab_stable": destab_stable,
            "recent_safe": recent_safe,
            "resolved": all_stable,
        },
    }

    outpath = ROOT / "experiments" / "evolution" / "f-evo3-protocol-cadence-s374.json"
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact: {outpath.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
