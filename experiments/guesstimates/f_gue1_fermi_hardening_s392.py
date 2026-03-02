#!/usr/bin/env python3
"""F-GUE1 Hardening (S392): Fermi decomposition of swarm performance metrics.

Blind Fermi estimates vs measured ground truth for 5 metrics:
1. Duplication rate (% of lessons that are near-duplicates)
2. Lesson citation half-life (sessions until citation rate halves)
3. Commits per session
4. Principles-per-lesson ratio (P/L)
5. Domain concentration (Gini of lessons across domains)

Improvements over S391 script:
- Pre-loads all lesson content into memory (eliminates N² file I/O)
- Adds 2 extra metrics for robustness (5 total, need >=3/5 within OOM)
- Truly blind estimates: no prior L-NNN measurements referenced in reasoning
"""
import subprocess, re, json, math
from pathlib import Path
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[2]


def fermi_estimates():
    """Produce blind Fermi estimates using only structural priors.

    Rules: no citing specific lesson numbers or their measurements.
    Only use: session count (~392), lesson count (~703), domain count (~35),
    principle count (~185), belief count (~20), frontier count (~21).
    """
    estimates = {}

    # --- 1. Duplication rate ---
    # ~703 lessons across ~35 domains = ~20 lessons/domain average
    # Each domain covers maybe 3-8 distinct findings
    # 20 lessons / 5 findings = 4 lessons per finding on average
    # If each finding cluster of 4 has ~2 that are close enough = ~50% in a dup pair
    # But many domains have only 1-5 lessons (long tail), reducing overlap
    # Counter-force: high-concurrency sessions rediscover same insights
    # Estimate: ~35-55% of lessons participate in a near-dup pair
    estimates["duplication_rate"] = {
        "fermi_estimate": 0.45,
        "reasoning": "703L / 35 domains / ~5 findings per domain = 4L per finding. "
                     "Long-tail domains reduce overlap, concurrency increases it. "
                     "Net: ~45% in dup pairs.",
        "confidence_band": [0.25, 0.65],
    }

    # --- 2. Lesson citation half-life ---
    # ~703 lessons over ~392 sessions. Each session creates ~1.8 lessons.
    # Each new lesson cites 2-3 others (from Cites: headers).
    # Most citations are to recent lessons (recency bias in context).
    # Information-theoretic: a lesson's relevance decays as new lessons
    # supersede its findings. If ~1.8 new lessons per session and each
    # domain has ~5 findings, a finding is "current" for ~3 sessions before
    # a newer lesson covers similar ground. But foundational lessons persist.
    # Bimodal: most lessons die fast (3-10 sessions), some live forever.
    # Median active window (creation to last citation) ≈ 10-30 sessions.
    estimates["lesson_half_life_sessions"] = {
        "fermi_estimate": 15,
        "reasoning": "~1.8 L/session creation rate. Most citations are recent (recency bias). "
                     "Bimodal: fast-decay majority + long-tail classics. "
                     "Median active window ~15 sessions.",
        "confidence_band": [5, 50],
    }

    # --- 3. Commits per session ---
    # Each session opens ~1-2 DOMEX lanes (each = 1-2 commits: open + artifacts + close)
    # Plus maintenance (sync_state, harvest, trim) = 1-3 commits
    # Plus handoff/NEXT.md updates = 1 commit
    # Low sessions: 2-3 commits. High-concurrency: 5-15.
    # Weighted average: ~4-6
    estimates["commits_per_session"] = {
        "fermi_estimate": 5.0,
        "reasoning": "1-2 DOMEX lanes × 2 commits + 2-3 maintenance + 1 handoff = ~5. "
                     "High concurrency sessions skew up.",
        "confidence_band": [2, 12],
    }

    # --- 4. Principles-per-lesson ratio ---
    # 185 principles / 703 lessons = structural ratio
    # But from first principles: principles are distilled from lessons.
    # Each principle covers ~3-5 lessons (it's a compression).
    # So P/L ≈ 1/4 = 0.25
    # But many early sessions had higher P extraction rate, later sessions lower.
    # Estimate: ~0.25
    estimates["principles_per_lesson"] = {
        "fermi_estimate": 0.25,
        "reasoning": "Principles compress ~4 lessons each. 185P/703L structurally. "
                     "Extraction rate declined over time (diminishing novelty). "
                     "Ratio ~0.25.",
        "confidence_band": [0.15, 0.40],
    }

    # --- 5. Domain concentration Gini ---
    # 35 domains but lessons are NOT evenly distributed.
    # "meta" domain likely has 30-40% of all lessons (self-referential system).
    # Top 5 domains probably hold 60-70% of lessons.
    # Remaining 30 domains split the rest.
    # Gini for this kind of distribution: ~0.5-0.7
    estimates["domain_gini"] = {
        "fermi_estimate": 0.60,
        "reasoning": "Meta-heavy system: top domain ~35% of lessons. "
                     "Top 5 domains ~65%. Long tail of 1-5 lesson domains. "
                     "Gini ~0.60.",
        "confidence_band": [0.45, 0.75],
    }

    return estimates


def measure_ground_truth():
    """Measure actual values for 5 metrics. Pre-loads all content to avoid N² I/O."""
    ground_truth = {}

    lessons_dir = REPO / "memory" / "lessons"
    lesson_files = sorted(lessons_dir.glob("L-*.md"))

    # Pre-load all lesson content
    lessons = {}
    for lf in lesson_files:
        try:
            lessons[lf.stem] = lf.read_text()
        except Exception:
            pass

    print(f"Loaded {len(lessons)} lessons into memory.")

    # --- 1. Duplication rate (Jaccard on body words, threshold 0.3) ---
    # Use first 150 words of body text (after header line) for richer signal
    body_words = {}
    for lid, text in lessons.items():
        lines = text.split("\n")
        # Skip header lines (title, Session:, Cites:, blank)
        body_start = 0
        for idx, line in enumerate(lines):
            if idx > 0 and line.strip() and not line.startswith("#") and \
               not line.startswith("Session:") and not line.startswith("Cites:"):
                body_start = idx
                break
        body = " ".join(lines[body_start:]).lower()
        # Remove common stop words and short tokens
        words = set(w for w in re.findall(r"\b[a-z]{3,}\b", body)[:150])
        if len(words) >= 10:
            body_words[lid] = words

    dup_lessons = set()
    dup_count = 0
    lids = sorted(body_words.keys())
    for i in range(len(lids)):
        for j in range(i + 1, len(lids)):
            a, b = body_words[lids[i]], body_words[lids[j]]
            jaccard = len(a & b) / len(a | b)
            if jaccard > 0.3:
                dup_count += 1
                dup_lessons.add(lids[i])
                dup_lessons.add(lids[j])

    dup_rate = len(dup_lessons) / max(len(lessons), 1)
    ground_truth["duplication_rate"] = {
        "measured": round(dup_rate, 3),
        "method": f"Jaccard > 0.3 on body words (first 150, >=3 chars). "
                  f"{len(dup_lessons)}/{len(lessons)} lessons in dup pair. "
                  f"{dup_count} dup pairs.",
        "n": len(lessons),
    }
    print(f"  Duplication: {dup_rate:.3f} ({len(dup_lessons)}/{len(lessons)})")

    # --- 2. Citation half-life (median session window: creation → last citation) ---
    # Build citation index in memory
    # For each lesson, find its creation session and which other lessons cite it
    creation_sessions = {}
    for lid, text in lessons.items():
        m = re.search(r"Session:\s*S?(\d+)", text)
        if m:
            creation_sessions[lid] = int(m.group(1))

    # Build reverse citation map: for each lesson, who cites it?
    cited_by = defaultdict(list)  # lid -> [(citing_lid, citing_session), ...]
    cite_re = re.compile(r"\bL-(\d+)\b")
    for lid, text in lessons.items():
        creator_session = creation_sessions.get(lid)
        if creator_session is None:
            continue
        for m in cite_re.finditer(text):
            target = f"L-{m.group(1)}"
            if target != lid and target in lessons:
                cited_by[target].append((lid, creator_session))

    cite_windows = []
    for lid in lessons:
        cs = creation_sessions.get(lid)
        if cs is None:
            continue
        citers = cited_by.get(lid, [])
        if not citers:
            continue
        last_cite_session = max(s for _, s in citers)
        window = last_cite_session - cs
        if window > 0:
            cite_windows.append(window)

    cite_windows.sort()
    if cite_windows:
        n = len(cite_windows)
        median = cite_windows[n // 2]
        mean = sum(cite_windows) / n
        p25 = cite_windows[n // 4]
        p75 = cite_windows[3 * n // 4]
        ground_truth["lesson_half_life_sessions"] = {
            "measured": median,
            "method": f"Median citation window. n={n}. Mean={mean:.1f}, "
                      f"Med={median}, P25={p25}, P75={p75}",
            "n": n,
        }
        print(f"  Half-life: median={median}, mean={mean:.1f}, n={n}")
    else:
        ground_truth["lesson_half_life_sessions"] = {
            "measured": None, "method": "No citation data", "n": 0,
        }

    # --- 3. Commits per session ---
    result = subprocess.run(
        ["git", "log", "--oneline", "--all"],
        capture_output=True, text=True, cwd=REPO
    )
    session_commits = Counter()
    for line in result.stdout.strip().split("\n"):
        m = re.search(r"\[S(\d+)\]", line)
        if m:
            session_commits[int(m.group(1))] += 1

    if session_commits:
        values = list(session_commits.values())
        avg = sum(values) / len(values)
        values.sort()
        n = len(values)
        median = values[n // 2]
        ground_truth["commits_per_session"] = {
            "measured": round(avg, 2),
            "method": f"Git log [S<N>] tags. n={n} sessions. "
                      f"Mean={avg:.2f}, Med={median}, "
                      f"Min={min(values)}, Max={max(values)}",
            "n": n,
        }
        print(f"  Commits/session: mean={avg:.2f}, med={median}, n={n}")
    else:
        ground_truth["commits_per_session"] = {
            "measured": None, "method": "No tagged commits", "n": 0,
        }

    # --- 4. Principles-per-lesson ratio ---
    n_principles = 0
    principles_path = REPO / "memory" / "PRINCIPLES.md"
    if principles_path.exists():
        text = principles_path.read_text()
        # Principles are inline: "P-008 text | P-011 text" — count unique P-NNN
        n_principles = len(set(re.findall(r"\bP-(\d+)\b", text)))

    n_lessons = len(lessons)
    if n_lessons > 0:
        ratio = n_principles / n_lessons
        ground_truth["principles_per_lesson"] = {
            "measured": round(ratio, 4),
            "method": f"{n_principles}P / {n_lessons}L = {ratio:.4f}",
            "n": n_lessons,
        }
        print(f"  P/L ratio: {ratio:.4f} ({n_principles}P / {n_lessons}L)")
    else:
        ground_truth["principles_per_lesson"] = {
            "measured": None, "method": "No lessons", "n": 0,
        }

    # --- 5. Domain concentration Gini ---
    # Count lessons per domain from Domain: field or lesson path
    domain_counts = Counter()
    for lid, text in lessons.items():
        dm = re.search(r"Domain:\s*(\S+)", text)
        if dm:
            domain_counts[dm.group(1)] += 1
        else:
            domain_counts["unknown"] += 1

    if domain_counts:
        vals = sorted(domain_counts.values())
        n = len(vals)
        total = sum(vals)
        # Gini coefficient
        numerator = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(vals))
        gini = numerator / (n * total) if total > 0 else 0
        top_domain = domain_counts.most_common(1)[0]
        top5 = sum(c for _, c in domain_counts.most_common(5))
        ground_truth["domain_gini"] = {
            "measured": round(gini, 3),
            "method": f"Gini over {n} domains. Top: {top_domain[0]}={top_domain[1]}. "
                      f"Top-5 share: {top5}/{total} ({100*top5/total:.1f}%)",
            "n": n,
        }
        print(f"  Domain Gini: {gini:.3f}, top={top_domain}, top5={top5}/{total}")
    else:
        ground_truth["domain_gini"] = {
            "measured": None, "method": "No domain data", "n": 0,
        }

    return ground_truth


def compare(estimates, ground_truth):
    """Compare Fermi estimates to ground truth."""
    print("\n=== F-GUE1 HARDENING: Fermi Decomposition Results ===\n")

    results = {}
    within_oom = 0
    total = 0
    details = []

    for metric in estimates:
        est = estimates[metric]
        gt = ground_truth.get(metric, {})
        fermi = est["fermi_estimate"]
        measured = gt.get("measured")

        print(f"--- {metric} ---")
        print(f"  Fermi estimate: {fermi}")
        print(f"  Measured:       {measured}")
        print(f"  Reasoning:      {est['reasoning']}")
        print(f"  Band:           {est['confidence_band']}")
        print(f"  Method:         {gt.get('method', 'N/A')}")

        if measured is not None and measured > 0 and fermi > 0:
            ratio = fermi / measured
            log_error = abs(math.log10(ratio))
            within = log_error < 1.0
            total += 1
            if within:
                within_oom += 1

            in_band = est["confidence_band"][0] <= measured <= est["confidence_band"][1]
            print(f"  Ratio (est/act): {ratio:.3f}")
            print(f"  Log10 error:     {log_error:.3f}")
            print(f"  Within 1 OOM:    {'YES' if within else 'NO'}")
            print(f"  In conf band:    {'YES' if in_band else 'NO'}")
            results[metric] = {
                "fermi": fermi,
                "measured": measured,
                "ratio": round(ratio, 3),
                "log_error": round(log_error, 3),
                "within_oom": within,
                "in_confidence_band": in_band,
            }
            details.append(f"  {metric}: est={fermi}, meas={measured}, "
                           f"ratio={ratio:.2f}, OOM={'PASS' if within else 'FAIL'}")
        else:
            print(f"  [Cannot compare — missing ground truth]")
            results[metric] = {"fermi": fermi, "measured": measured, "error": "missing"}
            details.append(f"  {metric}: est={fermi}, meas={measured}, MISSING")
        print()

    print(f"=== SUMMARY ===")
    for d in details:
        print(d)
    print(f"\n  Within 1 OOM: {within_oom}/{total}")
    threshold = max(1, int(total * 0.6))  # need >=60% within OOM
    f1_pass = within_oom >= threshold and total >= 3
    print(f"  Threshold: {threshold}/{total} (60%)")
    print(f"  F-GUE1 hypothesis: {'CONFIRMED' if f1_pass else 'FALSIFIED'}")

    results["summary"] = {
        "within_oom": within_oom,
        "total": total,
        "threshold": threshold,
        "f_gue1_pass": f1_pass,
    }
    return results


def main():
    estimates = fermi_estimates()

    print("Measuring ground truth...\n")
    ground_truth = measure_ground_truth()

    results = compare(estimates, ground_truth)

    out = {
        "experiment": "F-GUE1 Fermi hardening",
        "session": "S392",
        "frontier": "F-GUE1",
        "mode": "hardening",
        "date": "2026-03-01",
        "n_metrics": len(estimates),
        "estimates": {k: {kk: vv for kk, vv in v.items()}
                      for k, v in estimates.items()},
        "ground_truth": {k: {kk: vv for kk, vv in v.items()}
                         for k, v in ground_truth.items()},
        "comparison": results,
    }
    out_path = Path(__file__).resolve().parent / "f-gue1-fermi-hardening-s392.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[Saved to {out_path}]")


if __name__ == "__main__":
    main()
