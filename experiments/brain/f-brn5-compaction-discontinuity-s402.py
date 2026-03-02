#!/usr/bin/env python3
"""F-BRN5 compaction-discontinuity experiment (S402).

Hypothesis: K>27k drift degrades session quality (sleep-deprivation analogy).
Compaction = sleep. Post-compaction sessions should show higher quality.

Method: regression-discontinuity around compaction events.
- Identify compaction events from SESSION-LOG and git log
- Measure session quality in ±5 session windows
- Compare pre-compaction (high K, "sleep-deprived") vs post-compaction (low K, "rested")
- Quality metrics: lessons/session, challenges filed, citation density

S345 baseline: CONFOUNDED (K and age collinear, n=24).
This extends with regression-discontinuity design (n~250+ sessions, 5+ events).
"""

import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev, median

REPO = Path(__file__).resolve().parent.parent.parent


def parse_session_log():
    """Parse SESSION-LOG.md into per-session data."""
    sessions = {}
    log_path = REPO / "memory" / "SESSION-LOG.md"
    if not log_path.exists():
        return sessions

    with open(log_path) as f:
        for line in f:
            m = re.match(r"^S(\d+\w*)\s*\|", line)
            if not m:
                continue
            sid = m.group(1)
            base_m = re.match(r"(\d+)", sid)
            if not base_m:
                continue
            s_num = int(base_m.group(1))

            lm = re.search(r"\+(\d+)L", line)
            lessons = int(lm.group(1)) if lm else 0

            pm = re.search(r"\+(\d+)P", line)
            principles = int(pm.group(1)) if pm else 0

            tm = re.search(r"(\d+)L\s+\d+P\s+\d+B\s+\d+F", line)
            total_L = int(tm.group(1)) if tm else None

            # Detect challenge mentions
            challenge = bool(re.search(
                r"challeng|falsif|refut|CHALLENGED|FALSIFIED",
                line, re.IGNORECASE
            ))

            # Detect DOMEX sessions
            domex = bool(re.search(r"DOMEX", line))

            # Detect compaction mentions
            compact_mention = bool(re.search(
                r"compact|compress|proxy.?[Kk].*→|drift.*%|K\s*\d+.*→\s*\d+",
                line, re.IGNORECASE
            ))

            # Extract K values if present
            k_values = re.findall(r"(?:proxy.?K|K)\s*[=:]?\s*([\d,]+)\s*(?:→|->)\s*([\d,]+)", line)
            k_before = None
            k_after = None
            if k_values:
                k_before = int(k_values[0][0].replace(",", ""))
                k_after = int(k_values[0][1].replace(",", ""))

            if s_num not in sessions:
                sessions[s_num] = {
                    "lessons": 0,
                    "principles": 0,
                    "total_L": None,
                    "challenge": False,
                    "domex": False,
                    "compact_mention": False,
                    "k_before": None,
                    "k_after": None,
                }
            sessions[s_num]["lessons"] += lessons
            sessions[s_num]["principles"] += principles
            if total_L:
                sessions[s_num]["total_L"] = total_L
            if challenge:
                sessions[s_num]["challenge"] = True
            if domex:
                sessions[s_num]["domex"] = True
            if compact_mention:
                sessions[s_num]["compact_mention"] = True
            if k_before:
                sessions[s_num]["k_before"] = k_before
                sessions[s_num]["k_after"] = k_after

    return sessions


def identify_compaction_events(sessions):
    """Identify sessions where compaction occurred (K dropped)."""
    events = []

    # Sessions with explicit K drops in SESSION-LOG
    for s_num, data in sorted(sessions.items()):
        if data["k_before"] and data["k_after"] and data["k_after"] < data["k_before"]:
            drop_pct = (data["k_before"] - data["k_after"]) / data["k_before"] * 100
            if drop_pct >= 2.0:  # meaningful compaction (>2% K drop)
                events.append({
                    "session": s_num,
                    "k_before": data["k_before"],
                    "k_after": data["k_after"],
                    "drop_pct": drop_pct,
                    "source": "session-log-k-drop",
                })

    # Sessions with compaction mentions but no K values
    compact_sessions_from_log = set()
    for s_num, data in sorted(sessions.items()):
        if data["compact_mention"] and not (data["k_before"] and data["k_after"]):
            compact_sessions_from_log.add(s_num)

    # Also scan git log for compaction commits
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "--format=%s"],
            capture_output=True, text=True, cwd=REPO
        )
        for line in result.stdout.strip().split("\n"):
            m = re.search(r"\[S(\d+)\]", line)
            if not m:
                continue
            s_num = int(m.group(1))
            if re.search(r"compact|compress", line, re.IGNORECASE):
                if re.search(r"\d+.*→.*\d+|drift.*\d+%|\d+%.*→.*\d+%", line):
                    compact_sessions_from_log.add(s_num)
    except Exception:
        pass

    # Known compaction events from SESSION-LOG analysis
    known_events = [
        {"session": 60, "note": "S57→S60 -40% K event", "source": "session-log-narrative"},
        {"session": 85, "note": "K 26,277→25,011", "k_before": 26277, "k_after": 25011,
         "drop_pct": 4.8, "source": "session-log-explicit"},
        {"session": 100, "note": "K 24,856→23,916", "k_before": 24856, "k_after": 23916,
         "drop_pct": 3.8, "source": "session-log-explicit"},
        {"session": 338, "note": "T4 compaction analysis",
         "source": "session-log-narrative"},
        {"session": 370, "note": "Compaction 9.1%→5.8%",
         "source": "session-log-explicit"},
        {"session": 399, "note": "historian + compaction + signal-audit",
         "source": "git-commit"},
    ]

    # Add the S83++ event
    if 83 not in [e["session"] for e in events]:
        known_events.append(
            {"session": 83, "note": "MDL K-recompression 26,268→23,394 (-10.9%)",
             "k_before": 26268, "k_after": 23394, "drop_pct": 10.9,
             "source": "session-log-explicit"}
        )

    # Merge: use events from K-drop detection + known events
    seen = set(e["session"] for e in events)
    for ke in known_events:
        if ke["session"] not in seen:
            events.append(ke)
            seen.add(ke["session"])

    return sorted(events, key=lambda e: e["session"])


def measure_window(sessions, center, half_width=5):
    """Measure quality in a window of sessions around a compaction event."""
    all_sessions = sorted(sessions.keys())
    center_idx = None
    for i, s in enumerate(all_sessions):
        if s >= center:
            center_idx = i
            break
    if center_idx is None:
        return None, None

    pre_sessions = all_sessions[max(0, center_idx - half_width):center_idx]
    post_sessions = all_sessions[center_idx + 1:center_idx + 1 + half_width]

    def quality_metrics(session_list):
        if not session_list:
            return None
        lessons = [sessions[s]["lessons"] for s in session_list if s in sessions]
        challenges = sum(1 for s in session_list if s in sessions and sessions[s]["challenge"])
        domex = sum(1 for s in session_list if s in sessions and sessions[s]["domex"])
        return {
            "n": len(lessons),
            "sessions": session_list,
            "lessons_total": sum(lessons),
            "lessons_mean": mean(lessons) if lessons else 0,
            "lessons_median": median(lessons) if lessons else 0,
            "challenge_rate": challenges / len(session_list) if session_list else 0,
            "domex_rate": domex / len(session_list) if session_list else 0,
        }

    return quality_metrics(pre_sessions), quality_metrics(post_sessions)


def citation_density_by_era(sessions):
    """Measure citation density (Cites: headers) in lesson files by era."""
    lessons_dir = REPO / "memory" / "lessons"
    if not lessons_dir.exists():
        return {}

    era_cites = defaultdict(list)
    for lf in lessons_dir.glob("L-*.md"):
        m = re.match(r"L-(\d+)", lf.stem)
        if not m:
            continue
        l_num = int(m.group(1))
        text = lf.read_text(errors="ignore")

        # Find session
        sm = re.search(r"Session:\s*S(\d+)", text)
        s_num = int(sm.group(1)) if sm else None

        # Count citations
        cites_m = re.search(r"Cites:\s*(.+)", text)
        cite_count = 0
        if cites_m:
            cite_count = len(re.findall(r"L-\d+|P-\d+|B-\d+|F-\w+", cites_m.group(1)))

        if s_num:
            era_cites[s_num].append(cite_count)

    return era_cites


def run_experiment():
    sessions = parse_session_log()
    events = identify_compaction_events(sessions)
    citation_eras = citation_density_by_era(sessions)

    print(f"=== F-BRN5 Compaction-Discontinuity Experiment (S402) ===")
    print(f"Total sessions parsed: {len(sessions)}")
    print(f"Compaction events identified: {len(events)}")
    print()

    # Show events
    print("--- Compaction Events ---")
    for e in events:
        note = e.get("note", "")
        drop = f" ({e['drop_pct']:.1f}% drop)" if "drop_pct" in e else ""
        print(f"  S{e['session']:>4}{drop}: {note} [{e.get('source', '?')}]")
    print()

    # Regression discontinuity: pre vs post around each event
    print("--- Regression Discontinuity (±5 sessions) ---")
    all_pre_lessons = []
    all_post_lessons = []
    all_pre_challenge = []
    all_post_challenge = []

    for e in events:
        pre, post = measure_window(sessions, e["session"])
        if not pre or not post:
            print(f"  S{e['session']}: insufficient data")
            continue

        delta_lessons = post["lessons_mean"] - pre["lessons_mean"]
        delta_challenge = post["challenge_rate"] - pre["challenge_rate"]

        all_pre_lessons.append(pre["lessons_mean"])
        all_post_lessons.append(post["lessons_mean"])
        all_pre_challenge.append(pre["challenge_rate"])
        all_post_challenge.append(post["challenge_rate"])

        print(f"\n  S{e['session']} ({e.get('note', '')})")
        print(f"    PRE  (n={pre['n']}): {pre['lessons_mean']:.1f} L/s, "
              f"challenge={pre['challenge_rate']:.0%}, domex={pre['domex_rate']:.0%}")
        print(f"    POST (n={post['n']}): {post['lessons_mean']:.1f} L/s, "
              f"challenge={post['challenge_rate']:.0%}, domex={post['domex_rate']:.0%}")
        print(f"    Δ: lessons={delta_lessons:+.1f}, challenge={delta_challenge:+.0%}")

    # Aggregate results
    print("\n--- Aggregate (all events) ---")
    if all_pre_lessons and all_post_lessons:
        pre_mean_l = mean(all_pre_lessons)
        post_mean_l = mean(all_post_lessons)
        pre_mean_c = mean(all_pre_challenge)
        post_mean_c = mean(all_post_challenge)

        print(f"  PRE-compaction  mean: {pre_mean_l:.2f} L/s, challenge rate={pre_mean_c:.1%}")
        print(f"  POST-compaction mean: {post_mean_l:.2f} L/s, challenge rate={post_mean_c:.1%}")
        print(f"  Δ lessons/session: {post_mean_l - pre_mean_l:+.2f}")
        print(f"  Δ challenge rate:  {post_mean_c - pre_mean_c:+.1%}")

        # Effect size (Cohen's d)
        if len(all_pre_lessons) > 1 and len(all_post_lessons) > 1:
            pooled_sd = ((stdev(all_pre_lessons)**2 + stdev(all_post_lessons)**2) / 2) ** 0.5
            if pooled_sd > 0:
                d = (post_mean_l - pre_mean_l) / pooled_sd
                print(f"  Cohen's d (lessons): {d:.3f}")

        # Sign test: how many events show improvement?
        n_events = len(all_pre_lessons)
        n_improved = sum(1 for i in range(n_events) if all_post_lessons[i] > all_pre_lessons[i])
        print(f"  Sign test: {n_improved}/{n_events} events show post-compaction improvement")
    else:
        print("  Insufficient data for aggregate analysis")

    # Citation density analysis around compaction events
    print("\n--- Citation Density Around Compaction ---")
    for e in events:
        s = e["session"]
        pre_cites = []
        post_cites = []
        for ds in range(-5, 0):
            if s + ds in citation_eras:
                pre_cites.extend(citation_eras[s + ds])
        for ds in range(1, 6):
            if s + ds in citation_eras:
                post_cites.extend(citation_eras[s + ds])
        if pre_cites and post_cites:
            print(f"  S{s}: pre-cites mean={mean(pre_cites):.1f} (n={len(pre_cites)}), "
                  f"post-cites mean={mean(post_cites):.1f} (n={len(post_cites)})")

    # Era-level analysis: early (low K) vs mid (moderate K) vs late (high K)
    print("\n--- Era Analysis (maturation control) ---")
    sorted_s = sorted(sessions.keys())
    if len(sorted_s) >= 30:
        tercile = len(sorted_s) // 3
        early = sorted_s[:tercile]
        mid = sorted_s[tercile:2*tercile]
        late = sorted_s[2*tercile:]

        for label, era in [("EARLY", early), ("MID", mid), ("LATE", late)]:
            les = [sessions[s]["lessons"] for s in era if s in sessions]
            chal = sum(1 for s in era if s in sessions and sessions[s]["challenge"])
            domex = sum(1 for s in era if s in sessions and sessions[s]["domex"])
            if les:
                print(f"  {label} (S{era[0]}-S{era[-1]}, n={len(les)}): "
                      f"mean={mean(les):.2f} L/s, challenge={chal/len(era):.1%}, "
                      f"domex={domex/len(era):.1%}")

    # Verdict
    print("\n--- VERDICT ---")
    if all_pre_lessons and all_post_lessons:
        delta = mean(all_post_lessons) - mean(all_pre_lessons)
        if abs(delta) >= 0.5:  # meaningful effect = 0.5 L/s
            direction = "IMPROVEMENT" if delta > 0 else "DEGRADATION"
            print(f"  Post-compaction shows {direction} ({delta:+.2f} L/s)")
            if delta > 0:
                print("  F-BRN5 SUPPORTED: compaction (sleep analog) improves quality")
            else:
                print("  F-BRN5 INVERTED: compaction disrupts productivity")
        else:
            print(f"  NULL EFFECT: Δ={delta:+.2f} L/s (below 0.5 threshold)")
            print("  F-BRN5 sleep-deprivation analogy has no operational quality effect")
            print("  Brain isomorphism: structural (both consolidate) but not functional")
    else:
        print("  INSUFFICIENT DATA")

    # Build result JSON
    result = {
        "experiment": "F-BRN5",
        "session": "S402",
        "method": "regression-discontinuity",
        "hypothesis": "Post-compaction sessions show >=10pp improvement in quality",
        "n_sessions": len(sessions),
        "n_events": len(events),
        "events": events,
        "aggregate": {
            "pre_lessons_mean": mean(all_pre_lessons) if all_pre_lessons else None,
            "post_lessons_mean": mean(all_post_lessons) if all_post_lessons else None,
            "pre_challenge_rate": mean(all_pre_challenge) if all_pre_challenge else None,
            "post_challenge_rate": mean(all_post_challenge) if all_post_challenge else None,
            "delta_lessons": (mean(all_post_lessons) - mean(all_pre_lessons)) if all_pre_lessons and all_post_lessons else None,
            "delta_challenge": (mean(all_post_challenge) - mean(all_pre_challenge)) if all_pre_challenge and all_post_challenge else None,
            "n_improved": sum(1 for i in range(len(all_pre_lessons)) if all_post_lessons[i] > all_pre_lessons[i]) if all_pre_lessons else 0,
            "n_events_measured": len(all_pre_lessons),
        },
    }

    out_path = REPO / "experiments" / "brain" / "f-brn5-compaction-discontinuity-s402.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nArtifact written: {out_path.relative_to(REPO)}")

    return result


if __name__ == "__main__":
    run_experiment()
