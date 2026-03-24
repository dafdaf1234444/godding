#!/usr/bin/env python3
"""F-GOV9: Does implementing a formal opposition mechanism improve decision quality?

Cross-references session expect/actual/diff data (S530-S540) with steerer signals
to measure: (a) what % of decisions had unexpected outcomes, (b) what % of those
had relevant steerer signals that were not acted on, (c) Sharpe score comparison
for lessons born with vs without steerer activity.

Output: experiments/governance/f-gov9-opposition-mechanism-s541.json
"""

import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
NEXT_MD = REPO / "tasks" / "NEXT.md"
SIGNAL_HISTORY = REPO / "tools" / "synthetic-steerers" / "signal-history.json"
LESSONS_DIR = REPO / "memory" / "lessons"
OUTPUT = REPO / "experiments" / "governance" / "f-gov9-opposition-mechanism-s541.json"

# ---------------------------------------------------------------------------
# 1. Parse NEXT.md session notes for S530-S540
# ---------------------------------------------------------------------------

def parse_session_notes(path: Path) -> list[dict]:
    """Extract session notes with expect/actual/diff fields from NEXT.md.

    Returns list of dicts with keys: session, title, expect, actual, diff, artifacts.
    Only includes sessions S530-S540 (including sub-sessions like S530b, S540c).
    """
    text = path.read_text(encoding="utf-8")
    # Split on session note headers
    # Pattern: ## S<number><optional letter> session note (...)
    header_pat = re.compile(
        r"^## (S5(?:3[0-9]|40)[a-z]?) session note \((.+?)\)",
        re.MULTILINE,
    )

    notes = []
    matches = list(header_pat.finditer(text))

    for i, m in enumerate(matches):
        session_id = m.group(1)
        title = m.group(2)

        # Extract the numeric part to filter S530-S540
        num_match = re.match(r"S(\d+)", session_id)
        if not num_match:
            continue
        num = int(num_match.group(1))
        if num < 530 or num > 540:
            continue

        # Get the body text until the next header or end
        start = m.end()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            # Go until next ## or end of file
            next_header = re.search(r"^## ", text[start:], re.MULTILINE)
            end = start + next_header.start() if next_header else len(text)

        body = text[start:end]

        # Extract fields
        def extract_field(field_name: str) -> str:
            pat = re.compile(
                rf"^\- \*\*{field_name}\*\*:\s*(.+?)(?=\n- \*\*|\n##|\Z)",
                re.MULTILINE | re.DOTALL,
            )
            fm = pat.search(body)
            return fm.group(1).strip() if fm else ""

        expect = extract_field("expect")
        actual = extract_field("actual")
        diff = extract_field("diff")
        artifacts = extract_field("artifacts")

        notes.append({
            "session": session_id,
            "session_num": num,
            "title": title,
            "expect": expect,
            "actual": actual,
            "diff": diff,
            "artifacts": artifacts,
        })

    return notes


# ---------------------------------------------------------------------------
# 2. Load steerer signal history
# ---------------------------------------------------------------------------

def load_steerer_signals(path: Path) -> dict:
    """Load signal history, return dict[steerer_name] -> list of signal entries.

    Each entry has: session, signals (list of strings), date, state_snapshot.
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_signals_by_session(signal_data: dict) -> dict[str, list[dict]]:
    """Reorganize signals by session.

    Returns dict[session_id] -> list of {steerer, signal_text} dicts.
    """
    by_session: dict[str, list[dict]] = {}
    for steerer, entries in signal_data.items():
        for entry in entries:
            sid = entry.get("session", "")
            for sig in entry.get("signals", []):
                if not sig:
                    continue
                by_session.setdefault(sid, []).append({
                    "steerer": steerer,
                    "signal": sig,
                })
    return by_session


# ---------------------------------------------------------------------------
# 3. Load lesson files and extract Sharpe scores + session info
# ---------------------------------------------------------------------------

def load_lessons(lessons_dir: Path) -> list[dict]:
    """Parse all lesson .md files, extract lesson ID, session, Sharpe, domain."""
    lessons = []
    for f in sorted(lessons_dir.glob("L-*.md")):
        text = f.read_text(encoding="utf-8")

        # Extract lesson ID from filename
        lid_match = re.match(r"L-(\d+)", f.stem)
        if not lid_match:
            continue
        lid = int(lid_match.group(1))

        # Extract session from "Session: S<num>" line
        sess_match = re.search(r"Session:\s*(S\d+)", text)
        session = sess_match.group(1) if sess_match else ""

        sess_num = 0
        if session:
            sn_match = re.match(r"S(\d+)", session)
            if sn_match:
                sess_num = int(sn_match.group(1))

        # Extract Sharpe from "Sharpe: <num>"
        sharpe_match = re.search(r"Sharpe:\s*(\d+(?:\.\d+)?)", text)
        sharpe = float(sharpe_match.group(1)) if sharpe_match else None

        # Extract domain
        domain_match = re.search(r"Domain:\s*([^\|]+?)(?:\s*\||\s*$)", text, re.MULTILINE)
        domain = domain_match.group(1).strip() if domain_match else ""

        # Extract level
        level_match = re.search(r"level\s*=\s*(L\d+)", text, re.IGNORECASE)
        level = level_match.group(1) if level_match else ""

        lessons.append({
            "id": f"L-{lid}",
            "lid": lid,
            "session": session,
            "session_num": sess_num,
            "sharpe": sharpe,
            "domain": domain,
            "level": level,
        })

    return lessons


# ---------------------------------------------------------------------------
# 4. Determine if a session "diff" indicates a surprise outcome
# ---------------------------------------------------------------------------

def has_significant_diff(note: dict) -> bool:
    """Return True if the session note indicates a significant expect != actual gap.

    Heuristics:
    - Contains FALSIFIED, WRONG, surprise, unexpected, worse, completely wrong
    - Contains negative diff language (predicted X got Y, expected X found Y)
    - Has a non-empty diff field with substantive content
    """
    diff = note.get("diff", "").lower()
    actual = note.get("actual", "").lower()

    if not diff:
        return False

    # Strong surprise indicators
    strong_indicators = [
        "falsified", "completely wrong", "worse than", "unexpected",
        "surprise", "surprising", "misleading", "wrong",
        "not detected", "dormant", "inconclusive",
    ]

    # Moderate indicators (expect/actual mismatch language)
    moderate_indicators = [
        "expected", "predicted", "got", "found",
        "but", "however", "instead",
    ]

    strong_count = sum(1 for ind in strong_indicators if ind in diff or ind in actual)
    moderate_count = sum(1 for ind in moderate_indicators if ind in diff)

    # Strong surprise: any strong indicator
    # Moderate surprise: expect != actual with mismatch language
    return strong_count >= 1 or moderate_count >= 3


# ---------------------------------------------------------------------------
# 5. Check if steerer signals are relevant to a session's surprise
# ---------------------------------------------------------------------------

def compute_keyword_overlap(text_a: str, text_b: str, min_word_len: int = 4) -> float:
    """Compute Jaccard-like keyword overlap between two texts.

    Strips common stop words and short words. Returns overlap fraction.
    """
    stop_words = {
        "the", "that", "this", "with", "from", "have", "been", "were",
        "will", "would", "could", "should", "into", "than", "more",
        "each", "also", "some", "when", "what", "where", "which",
        "their", "there", "about", "after", "before", "between",
        "through", "during", "above", "below", "does", "just",
        "only", "very", "most", "other", "over", "such", "much",
        "both", "same", "then", "them", "they", "your", "need",
        "signal", "swarm",
    }

    def tokenize(text: str) -> set[str]:
        words = re.findall(r"[a-z]+", text.lower())
        return {w for w in words if len(w) >= min_word_len and w not in stop_words}

    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    return len(intersection) / len(union) if union else 0.0


def find_relevant_signals(
    note: dict,
    signals_by_session: dict[str, list[dict]],
    relevance_threshold: float = 0.08,
) -> list[dict]:
    """Find steerer signals relevant to a session note's diff/actual.

    Checks signals from:
    - The same base session number (e.g., S530 signals for S530b note)
    - The prior 5 sessions (opposition signals may precede the decision)

    Returns list of {steerer, signal, overlap_score} for relevant signals.
    """
    note_text = f"{note.get('expect', '')} {note.get('actual', '')} {note.get('diff', '')} {note.get('title', '')}"
    session_num = note["session_num"]

    relevant = []

    # Check signals from nearby sessions (session_num - 5 through session_num)
    for offset in range(-5, 1):
        check_session = f"S{session_num + offset}"
        if check_session not in signals_by_session:
            continue
        for sig_entry in signals_by_session[check_session]:
            overlap = compute_keyword_overlap(note_text, sig_entry["signal"])
            if overlap >= relevance_threshold:
                relevant.append({
                    "steerer": sig_entry["steerer"],
                    "signal": sig_entry["signal"],
                    "signal_session": check_session,
                    "overlap_score": round(overlap, 3),
                })

    # Deduplicate by signal text
    seen = set()
    deduped = []
    for r in sorted(relevant, key=lambda x: -x["overlap_score"]):
        if r["signal"] not in seen:
            seen.add(r["signal"])
            deduped.append(r)

    return deduped


# ---------------------------------------------------------------------------
# 6. Compute Sharpe comparison: sessions with steerer signals vs without
# ---------------------------------------------------------------------------

def compute_sharpe_comparison(
    lessons: list[dict],
    signal_data: dict,
) -> dict:
    """Compare mean Sharpe of lessons born in sessions with steerer activity vs without.

    Only considers lessons from S505-S540 (steerer era + recent).
    """
    # Build set of sessions that had steerer signals
    sessions_with_signals: set[str] = set()
    for steerer, entries in signal_data.items():
        for entry in entries:
            if entry.get("signals"):
                # Only count non-empty signal lists
                non_empty = [s for s in entry["signals"] if s]
                if non_empty:
                    sessions_with_signals.add(entry["session"])

    # Filter lessons to S505-S540 range with valid Sharpe
    target_lessons = [
        l for l in lessons
        if 505 <= l["session_num"] <= 540 and l["sharpe"] is not None
    ]

    with_signals = [l for l in target_lessons if l["session"] in sessions_with_signals]
    without_signals = [l for l in target_lessons if l["session"] not in sessions_with_signals]

    def mean_sharpe(lst: list[dict]) -> float:
        sharpes = [l["sharpe"] for l in lst]
        return sum(sharpes) / len(sharpes) if sharpes else 0.0

    def std_sharpe(lst: list[dict]) -> float:
        sharpes = [l["sharpe"] for l in lst]
        if len(sharpes) < 2:
            return 0.0
        m = sum(sharpes) / len(sharpes)
        var = sum((s - m) ** 2 for s in sharpes) / (len(sharpes) - 1)
        return var ** 0.5

    return {
        "sessions_with_steerer_signals": sorted(sessions_with_signals),
        "n_lessons_with_signals": len(with_signals),
        "n_lessons_without_signals": len(without_signals),
        "mean_sharpe_with_signals": round(mean_sharpe(with_signals), 3),
        "mean_sharpe_without_signals": round(mean_sharpe(without_signals), 3),
        "std_sharpe_with_signals": round(std_sharpe(with_signals), 3),
        "std_sharpe_without_signals": round(std_sharpe(without_signals), 3),
        "sharpe_delta": round(
            mean_sharpe(with_signals) - mean_sharpe(without_signals), 3
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("F-GOV9: Opposition Mechanism — Steerer Signal vs Decision Surprise")
    print("=" * 70)

    # 1. Parse session notes
    print("\n[1] Parsing NEXT.md session notes (S530-S540)...")
    notes = parse_session_notes(NEXT_MD)
    print(f"    Found {len(notes)} session notes in range S530-S540")

    if not notes:
        print("ERROR: No session notes found. Check NEXT.md format.")
        sys.exit(1)

    # 2. Load steerer signals
    print("\n[2] Loading steerer signal history...")
    signal_data = load_steerer_signals(SIGNAL_HISTORY)
    signals_by_session = get_signals_by_session(signal_data)
    total_signals = sum(len(sigs) for sigs in signals_by_session.values())
    print(f"    {len(signal_data)} steerers, {total_signals} signals across {len(signals_by_session)} sessions")

    # 3. Load lessons
    print("\n[3] Loading lesson files...")
    lessons = load_lessons(LESSONS_DIR)
    s530_540_lessons = [l for l in lessons if 530 <= l["session_num"] <= 540]
    print(f"    {len(lessons)} total lessons, {len(s530_540_lessons)} from S530-S540")

    # 4. Identify decisions with significant diff (surprise outcomes)
    print("\n[4] Identifying surprise outcomes (expect != actual)...")
    surprise_notes = []
    non_surprise_notes = []
    for note in notes:
        if has_significant_diff(note):
            surprise_notes.append(note)
        else:
            non_surprise_notes.append(note)

    surprise_pct = (len(surprise_notes) / len(notes) * 100) if notes else 0
    print(f"    {len(surprise_notes)}/{len(notes)} sessions had significant diffs ({surprise_pct:.1f}%)")

    # 5. Cross-reference: did steerer signals predict the surprise?
    print("\n[5] Cross-referencing steerer signals with surprise outcomes...")
    surprises_with_relevant_signals = []
    surprises_without_signals = []

    for note in surprise_notes:
        relevant = find_relevant_signals(note, signals_by_session)
        if relevant:
            surprises_with_relevant_signals.append({
                "session": note["session"],
                "title": note["title"],
                "diff_summary": note["diff"][:200],
                "relevant_signals": relevant[:5],  # top 5
            })
        else:
            surprises_without_signals.append({
                "session": note["session"],
                "title": note["title"],
                "diff_summary": note["diff"][:200],
            })

    signal_coverage_pct = (
        len(surprises_with_relevant_signals) / len(surprise_notes) * 100
        if surprise_notes else 0
    )

    print(f"    {len(surprises_with_relevant_signals)}/{len(surprise_notes)} surprises had relevant steerer signals ({signal_coverage_pct:.1f}%)")
    print(f"    {len(surprises_without_signals)} surprises had NO relevant steerer signals")

    # 6. Sharpe comparison
    print("\n[6] Computing Sharpe score comparison (steerer-active vs inactive sessions)...")
    sharpe_comp = compute_sharpe_comparison(lessons, signal_data)
    print(f"    Lessons with steerer signals:    n={sharpe_comp['n_lessons_with_signals']}, "
          f"mean Sharpe={sharpe_comp['mean_sharpe_with_signals']}")
    print(f"    Lessons without steerer signals: n={sharpe_comp['n_lessons_without_signals']}, "
          f"mean Sharpe={sharpe_comp['mean_sharpe_without_signals']}")
    print(f"    Delta: {sharpe_comp['sharpe_delta']:+.3f}")

    # 7. Build results
    results = {
        "experiment": "F-GOV9",
        "title": "Does implementing a formal opposition mechanism improve decision quality?",
        "session": "S541",
        "date": "2026-03-24",
        "method": {
            "description": "Cross-reference session expect/actual/diff data (S530-S540) with steerer signal history to measure opposition effectiveness",
            "session_range": "S530-S540",
            "steerer_sessions": sorted(signals_by_session.keys()),
            "n_session_notes": len(notes),
            "n_steerers": len(signal_data),
            "relevance_method": "keyword Jaccard overlap >= 0.08 between note text and signal text",
        },
        "metrics": {
            "a_surprise_rate": {
                "total_decisions": len(notes),
                "decisions_with_unexpected_outcomes": len(surprise_notes),
                "surprise_rate_pct": round(surprise_pct, 1),
            },
            "b_steerer_signal_coverage": {
                "surprises_with_relevant_signals": len(surprises_with_relevant_signals),
                "surprises_without_signals": len(surprises_without_signals),
                "signal_coverage_pct": round(signal_coverage_pct, 1),
                "interpretation": (
                    "% of surprise outcomes where a steerer signal existed "
                    "that was relevant to the gap but not acted on"
                ),
            },
            "c_sharpe_comparison": sharpe_comp,
        },
        "detail": {
            "surprises_with_signals": surprises_with_relevant_signals,
            "surprises_without_signals": surprises_without_signals,
            "non_surprise_sessions": [
                {"session": n["session"], "title": n["title"]}
                for n in non_surprise_notes
            ],
        },
        "verdict": "",  # filled below
        "interpretation": "",
        "prescription": [],
    }

    # Verdict logic
    if signal_coverage_pct > 50:
        verdict = "CONFIRMED"
        interp = (
            f"Steerer signals were relevant to {signal_coverage_pct:.0f}% of surprise outcomes. "
            f"The opposition mechanism (synthetic steerers) IS generating signals that predict "
            f"decision gaps, but these signals are not being systematically acted on. "
            f"Formalizing opposition would improve decision quality."
        )
    elif signal_coverage_pct > 20:
        verdict = "PARTIAL"
        interp = (
            f"Steerer signals covered {signal_coverage_pct:.0f}% of surprise outcomes. "
            f"Opposition mechanism shows partial predictive value but insufficient coverage. "
            f"Steerer signals are too generic or misaligned with actual decision domains."
        )
    else:
        verdict = "WEAK"
        interp = (
            f"Steerer signals covered only {signal_coverage_pct:.0f}% of surprise outcomes. "
            f"Current opposition mechanism does not meaningfully predict decision gaps. "
            f"Steerers may need domain-specific training or tighter coupling to session planning."
        )

    # Add Sharpe interpretation
    if sharpe_comp["sharpe_delta"] > 0.5:
        interp += (
            f" Sharpe delta {sharpe_comp['sharpe_delta']:+.3f} favors steerer-active sessions, "
            f"suggesting opposition improves lesson quality."
        )
    elif sharpe_comp["sharpe_delta"] < -0.5:
        interp += (
            f" Sharpe delta {sharpe_comp['sharpe_delta']:+.3f} favors steerer-inactive sessions, "
            f"suggesting opposition may distract from quality work."
        )
    else:
        interp += (
            f" Sharpe delta {sharpe_comp['sharpe_delta']:+.3f} is negligible, "
            f"suggesting steerer activity does not yet measurably affect lesson quality."
        )

    results["verdict"] = verdict
    results["interpretation"] = interp
    results["prescription"] = [
        "Wire steerer signals into session planning (orient.py) so they are visible before decisions",
        "Add domain-specific steerer matching: each session's dispatched domain should trigger relevant steerer signals",
        "Track opposition-acted-on rate: when a steerer signal IS shown, does the session act differently?",
        "Target: signal_coverage_pct > 60% within 10 sessions of formal opposition wiring",
    ]

    # Save
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Verdict: {verdict}")
    print(f"  Surprise rate:       {surprise_pct:.1f}% ({len(surprise_notes)}/{len(notes)} sessions)")
    print(f"  Signal coverage:     {signal_coverage_pct:.1f}% of surprises had relevant steerer signals")
    print(f"  Sharpe (with):       {sharpe_comp['mean_sharpe_with_signals']:.2f} (n={sharpe_comp['n_lessons_with_signals']})")
    print(f"  Sharpe (without):    {sharpe_comp['mean_sharpe_without_signals']:.2f} (n={sharpe_comp['n_lessons_without_signals']})")
    print(f"  Sharpe delta:        {sharpe_comp['sharpe_delta']:+.3f}")
    print(f"\n  Output: {OUTPUT.relative_to(REPO)}")
    print(f"\n  {interp}")
    print("=" * 70)


if __name__ == "__main__":
    main()
