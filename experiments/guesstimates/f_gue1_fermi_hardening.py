#!/usr/bin/env python3
"""F-GUE1 Hardening: Fermi decomposition of swarm performance metrics.

Blind Fermi estimates vs measured ground truth for 3 metrics:
1. Duplication rate (% of lessons that are near-duplicates)
2. Lesson half-life (sessions until a lesson is no longer actively cited)
3. Commit frequency (commits per session)

Session: S391 | Mode: hardening | Frontier: F-GUE1
"""
import subprocess, re, json, math
from pathlib import Path
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[2]


def fermi_estimates():
    """Produce blind Fermi estimates using only structural priors."""
    estimates = {}

    # --- Estimate 1: Duplication rate ---
    # Prior: L-297 measured 57.5% at ~297 lessons. At ~703 lessons, more topics exhausted.
    # Structural reasoning:
    #   - 703 lessons across ~35 domains ≈ 20 lessons/domain
    #   - Each domain has ~3-5 core findings → ~5 unique themes/domain
    #   - 20/5 = 4 lessons per theme → some overlap expected
    #   - But CRDT/append-only means "near-dup" includes rephrased same insight
    #   - Session-local context means same finding rediscovered ~2x
    #   - Estimate: 40-60% duplication at current scale
    estimates["duplication_rate"] = {
        "fermi_estimate": 0.50,  # 50%
        "reasoning": "703 lessons / 35 domains / ~5 unique themes = 4 per theme. "
                     "CRDT append-only + session context loss → ~50% rephrasing.",
        "confidence_band": [0.30, 0.70],
    }

    # --- Estimate 2: Lesson citation half-life ---
    # Prior: how many sessions until a lesson drops below 50% of peak citation rate?
    # Structural reasoning:
    #   - ~390 sessions, each cites ~2-3 lessons explicitly
    #   - Most citations come within 5-10 sessions of creation (proximity effect L-736)
    #   - Session proximity 27x dominance (L-736): 50.4% of citations within 5 sessions
    #   - So half-life is roughly when citation rate drops below peak/2
    #   - Peak is at creation session (s=0)
    #   - 50% drop happens at ~5-10 sessions based on proximity decay
    #   - Estimate: 8 sessions half-life
    estimates["lesson_half_life_sessions"] = {
        "fermi_estimate": 8,  # sessions
        "reasoning": "Session proximity 27x dominance (L-736). 50.4% of citations "
                     "within 5 sessions. Exponential decay → half-life ~8 sessions.",
        "confidence_band": [3, 20],
    }

    # --- Estimate 3: Commits per session ---
    # Structural reasoning:
    #   - ~390 sessions
    #   - Each session produces 1-3 DOMEX lanes + maintenance
    #   - Each lane = 1 commit (open + close often merged)
    #   - Plus maintenance commits (sync_state, etc)
    #   - High-concurrency sessions: 5-10 commits
    #   - Low-concurrency sessions: 2-4 commits
    #   - Average: ~4-5 commits/session
    estimates["commits_per_session"] = {
        "fermi_estimate": 5,
        "reasoning": "1-3 DOMEX lanes/session × ~1.5 commits/lane + ~2 maintenance "
                     "commits = ~4-5. High concurrency skews up.",
        "confidence_band": [2, 10],
    }

    return estimates


def measure_ground_truth():
    """Measure actual values for the 3 metrics."""
    ground_truth = {}

    # --- Ground truth 1: Duplication rate ---
    # Use near-dup detection from check.sh logic
    lessons_dir = REPO / "memory" / "lessons"
    lessons = sorted(lessons_dir.glob("L-*.md"))
    # Simplified: count lessons with same first-line title words (>60% overlap = near-dup)
    titles = {}
    for lf in lessons:
        try:
            text = lf.read_text()
            first_line = text.split("\n")[0].strip()
            # Extract title after "# L-NNN: "
            m = re.match(r"# L-\d+:\s*(.*)", first_line)
            if m:
                title_words = set(m.group(1).lower().split())
                titles[lf.stem] = title_words
        except Exception:
            pass

    # Count near-dup pairs (Jaccard > 0.5 on title words)
    dup_count = 0
    total_pairs = 0
    dup_lessons = set()
    lesson_ids = sorted(titles.keys())
    for i in range(len(lesson_ids)):
        for j in range(i + 1, len(lesson_ids)):
            a, b = titles[lesson_ids[i]], titles[lesson_ids[j]]
            if len(a) < 3 or len(b) < 3:
                continue
            total_pairs += 1
            jaccard = len(a & b) / len(a | b)
            if jaccard > 0.5:
                dup_count += 1
                dup_lessons.add(lesson_ids[i])
                dup_lessons.add(lesson_ids[j])

    dup_rate = len(dup_lessons) / max(len(lessons), 1)
    ground_truth["duplication_rate"] = {
        "measured": round(dup_rate, 3),
        "method": f"Jaccard > 0.5 on title words. {len(dup_lessons)}/{len(lessons)} "
                  f"lessons in a near-dup pair. {dup_count} dup pairs total.",
        "n": len(lessons),
    }

    # --- Ground truth 2: Lesson citation half-life ---
    # Read all lessons once, build citation graph, compute active windows
    lesson_data = {}  # lid -> (session, text)
    for lf in lessons:
        try:
            text = lf.read_text()
            lid = lf.stem
            s_match = re.search(r"Session:\s*S?(\d+)", text)
            if s_match:
                lesson_data[lid] = (int(s_match.group(1)), text)
        except Exception:
            pass

    # Build citation edges: for each lesson, find all L-NNN references
    cite_windows = []
    last_cited_session = {}  # lid -> max session of any citer
    for lid, (session, text) in lesson_data.items():
        last_cited_session.setdefault(lid, session)
        # Find all L-NNN citations in this lesson's text
        cited = set(re.findall(r"\bL-(\d+)\b", text))
        for cited_num in cited:
            cited_lid = f"L-{cited_num}"
            if cited_lid != lid and cited_lid in lesson_data:
                if session > last_cited_session.get(cited_lid, 0):
                    last_cited_session[cited_lid] = session

    for lid, (created, _) in lesson_data.items():
        active_window = last_cited_session.get(lid, created) - created
        if active_window > 0:
            cite_windows.append(active_window)

    if cite_windows:
        cite_windows.sort()
        median_window = cite_windows[len(cite_windows) // 2]
        # Half-life = median active window (rough approximation)
        ground_truth["lesson_half_life_sessions"] = {
            "measured": median_window,
            "method": f"Median citation window (creation→last citation). "
                      f"n={len(cite_windows)} lessons with citations. "
                      f"Mean={sum(cite_windows)/len(cite_windows):.1f}, "
                      f"Median={median_window}, "
                      f"P25={cite_windows[len(cite_windows)//4]}, "
                      f"P75={cite_windows[3*len(cite_windows)//4]}",
            "n": len(cite_windows),
        }
    else:
        ground_truth["lesson_half_life_sessions"] = {
            "measured": None, "method": "No citation data found", "n": 0,
        }

    # --- Ground truth 3: Commits per session ---
    # Count commits in git log, extract session tags
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
        median = values[len(values) // 2]
        ground_truth["commits_per_session"] = {
            "measured": round(avg, 2),
            "method": f"Git log [S<N>] tag extraction. "
                      f"n={len(session_commits)} sessions with tagged commits. "
                      f"Mean={avg:.2f}, Median={median}, "
                      f"Min={min(values)}, Max={max(values)}",
            "n": len(session_commits),
        }
    else:
        ground_truth["commits_per_session"] = {
            "measured": None, "method": "No session-tagged commits found", "n": 0,
        }

    return ground_truth


def compare(estimates, ground_truth):
    """Compare Fermi estimates to ground truth."""
    print("=== F-GUE1 HARDENING: Fermi Decomposition Results ===\n")

    results = {}
    within_oom = 0
    total = 0

    for metric in estimates:
        est = estimates[metric]
        gt = ground_truth.get(metric, {})
        fermi = est["fermi_estimate"]
        measured = gt.get("measured")

        print(f"--- {metric} ---")
        print(f"  Fermi estimate: {fermi}")
        print(f"  Measured:       {measured}")
        print(f"  Reasoning:      {est['reasoning']}")
        print(f"  Confidence:     {est['confidence_band']}")
        print(f"  Method:         {gt.get('method', 'N/A')}")

        if measured is not None and measured > 0 and fermi > 0:
            ratio = fermi / measured
            log_error = abs(math.log10(ratio))
            within = log_error < 1.0  # within 1 OOM
            total += 1
            if within:
                within_oom += 1

            print(f"  Ratio (est/actual): {ratio:.3f}")
            print(f"  Log10 error:        {log_error:.3f}")
            print(f"  Within 1 OOM:       {'YES' if within else 'NO'}")
            results[metric] = {
                "fermi": fermi,
                "measured": measured,
                "ratio": round(ratio, 3),
                "log_error": round(log_error, 3),
                "within_oom": within,
            }
        else:
            print(f"  [Cannot compare — missing ground truth]")
            results[metric] = {"fermi": fermi, "measured": measured, "error": "missing"}
        print()

    print(f"=== SUMMARY ===")
    print(f"  Within 1 OOM: {within_oom}/{total}")
    f1_pass = within_oom >= 2 and total >= 3
    print(f"  F-GUE1 hypothesis (>=2/3 within OOM): {'CONFIRMED' if f1_pass else 'FALSIFIED'}")

    results["summary"] = {
        "within_oom": within_oom,
        "total": total,
        "f_gue1_pass": f1_pass,
    }
    return results


def main():
    # Step 1: Produce blind estimates
    estimates = fermi_estimates()

    # Step 2: Measure ground truth
    print("Measuring ground truth (may take a moment)...")
    ground_truth = measure_ground_truth()

    # Step 3: Compare
    results = compare(estimates, ground_truth)

    # Save
    out = {
        "session": "S391",
        "frontier": "F-GUE1",
        "mode": "hardening",
        "estimates": estimates,
        "ground_truth": ground_truth,
        "comparison": results,
    }
    out_path = Path(__file__).resolve().parent / "f-gue1-fermi-hardening-s391.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[Saved to {out_path}]")


if __name__ == "__main__":
    main()
