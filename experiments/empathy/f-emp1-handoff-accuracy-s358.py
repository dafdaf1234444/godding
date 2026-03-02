#!/usr/bin/env python3
"""F-EMP1: Measure handoff empathic accuracy — does NEXT.md predict next-session actions?

Parses NEXT.md session notes, extracts "Next:" predictions and "actual:" outcomes,
then measures prediction hit rate across session boundaries.

Output: JSON experiment artifact + human-readable summary.
"""

import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

NEXT_MD = Path("tasks/NEXT.md")
NEXT_ARCHIVE = Path("tasks/NEXT-ARCHIVE.md")


def parse_session_notes(text: str) -> list[dict]:
    """Extract session notes with their predictions and actuals."""
    notes = []
    # Split on session note headers
    sections = re.split(r"^## (S\d+ session note \([^)]+\))", text, flags=re.MULTILINE)

    for i in range(1, len(sections), 2):
        header = sections[i]
        body = sections[i + 1] if i + 1 < len(sections) else ""

        # Extract session number
        sess_m = re.match(r"S(\d+)", header)
        if not sess_m:
            continue
        sess_num = int(sess_m.group(1))

        # Extract description from header
        desc_m = re.search(r"\((.+)\)", header)
        desc = desc_m.group(1) if desc_m else ""

        # Extract "actual:" field
        actual_m = re.search(r"\*\*actual\*\*:\s*(.+?)(?=\n- \*\*|\n##|\Z)", body, re.DOTALL)
        actual = actual_m.group(1).strip() if actual_m else ""

        # Extract "Next:" predictions
        next_m = re.search(r"\*\*Next\*\*:\s*(.+?)(?=\n##|\Z)", body, re.DOTALL)
        next_text = next_m.group(1).strip() if next_m else ""

        # Parse individual predictions from "(1) ...; (2) ...; (3) ..."
        predictions = []
        if next_text:
            # Split on numbered items
            items = re.findall(r"\((\d+)\)\s*([^(]+?)(?=\(\d+\)|\Z)", next_text)
            for num, pred_text in items:
                pred = pred_text.strip().rstrip(";").strip()
                if pred:
                    predictions.append(pred)

        # Extract check_mode
        mode_m = re.search(r"\*\*check_mode\*\*:\s*(\w+)", body)
        check_mode = mode_m.group(1) if mode_m else ""

        # Extract lane
        lane_m = re.search(r"\*\*lane\*\*:\s*([^|]+?)(?:\s*\||\n)", body)
        lane = lane_m.group(1).strip() if lane_m else ""

        notes.append({
            "session": sess_num,
            "description": desc,
            "actual": actual,
            "predictions": predictions,
            "check_mode": check_mode,
            "lane": lane,
        })

    return notes


def fuzzy_match(prediction: str, actual: str, threshold: float = 0.25) -> tuple[bool, float]:
    """Check if a prediction matches an actual outcome using fuzzy string matching.

    Combines three signals:
    1. Term overlap (Jaccard on content words)
    2. Identifier overlap (F-xxx, L-xxx, tool names — highly specific)
    3. Sequence similarity (catches partial matches)
    """
    pred_lower = prediction.lower()
    actual_lower = actual.lower()

    # Extract key terms (case-insensitive, include short domain terms)
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
                  "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
                  "if", "not", "no", "do", "does", "did", "will", "would", "should",
                  "can", "could", "may", "might", "shall", "must", "need", "run",
                  "check", "update", "test", "verify", "confirm", "fix", "add", "write",
                  "its", "has", "had", "have", "this", "that", "than", "then"}

    def key_terms(text):
        # Allow uppercase (NK, USL, etc.) and short terms (≥2 chars)
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", text)
        return set(w.lower() for w in words if w.lower() not in stop_words and len(w) >= 2)

    pred_terms = key_terms(prediction)
    actual_terms = key_terms(actual)

    # Term overlap (Jaccard)
    if pred_terms:
        union = pred_terms | actual_terms
        jaccard = len(pred_terms & actual_terms) / len(union) if union else 0
    else:
        jaccard = 0

    # Key identifiers (highly specific — F-ECO5, L-608, orient.py, NK, Hawkes, etc.)
    id_pattern = (
        r"(?:F-[A-Z]+\d*|L-\d{3,4}|P-\d{3}|B-\d+|ISO-\d+|S\d{3}|"
        r"K[=≈_][\d.]+|N[=≈][\d]+|"
        r"orient\.py|dispatch|compact|claim|contract|nk_null|phase_boundary|"
        r"NK|USL|Hawkes|PAPER|PHIL-\d+|B-EVAL\d+|DOMEX|"
        r"NEXT\.md|INDEX\.md|PHILOSOPHY\.md|PRINCIPLES\.md|SWARM-LANES|"
        r"economy|governance|empathy|brain|information-science|"
        r"stochastic|linguistics|evolution|conflict|"
        r"Zipf|Gini|Sharpe|proxy-K|C-EDIT|dark.matter)"
    )
    pred_ids = set(m.lower() for m in re.findall(id_pattern, prediction, re.IGNORECASE))
    actual_ids = set(m.lower() for m in re.findall(id_pattern, actual, re.IGNORECASE))

    if pred_ids:
        id_jaccard = len(pred_ids & actual_ids) / len(pred_ids)  # recall-based: how many predicted IDs appear
    else:
        id_jaccard = 0

    # Sequence similarity (catches "NK K=2.0 monitoring" ~ "NK K=2.0 crossing")
    seq_sim = SequenceMatcher(None, pred_lower[:200], actual_lower[:500]).ratio()

    # Combined score: weight identifiers heavily (they're the most specific signal)
    score = (jaccard * 0.3) + (id_jaccard * 0.5) + (seq_sim * 0.2)

    return score >= threshold, round(score, 3)


def measure_accuracy(notes: list[dict], window: int = 3) -> dict:
    """Measure prediction accuracy across session boundaries.

    For each note's predictions, check if any of the next `window` notes' actuals match.
    """
    results = []
    total_predictions = 0
    total_hits = 0
    per_session_accuracy = []

    for i, note in enumerate(notes):
        if not note["predictions"]:
            continue

        # Look at next `window` notes for matches
        future_actuals = []
        future_descs = []
        for j in range(i + 1, min(i + 1 + window, len(notes))):
            future_actuals.append(notes[j]["actual"])
            future_descs.append(notes[j]["description"])

        if not future_actuals:
            continue

        combined_future = " ".join(future_actuals) + " " + " ".join(future_descs)
        pred_results = []
        hits = 0

        for pred in note["predictions"]:
            matched, score = fuzzy_match(pred, combined_future)
            pred_results.append({
                "prediction": pred[:100],
                "matched": matched,
                "score": score,
            })
            if matched:
                hits += 1

        accuracy = hits / len(note["predictions"]) if note["predictions"] else 0
        total_predictions += len(note["predictions"])
        total_hits += hits
        per_session_accuracy.append(accuracy)

        results.append({
            "session": note["session"],
            "description": note["description"][:60],
            "n_predictions": len(note["predictions"]),
            "n_hits": hits,
            "accuracy": round(accuracy, 3),
            "predictions": pred_results,
        })

    overall_accuracy = total_hits / total_predictions if total_predictions > 0 else 0
    mean_session_accuracy = sum(per_session_accuracy) / len(per_session_accuracy) if per_session_accuracy else 0

    return {
        "total_notes_with_predictions": len(results),
        "total_predictions": total_predictions,
        "total_hits": total_hits,
        "overall_hit_rate": round(overall_accuracy, 3),
        "mean_session_accuracy": round(mean_session_accuracy, 3),
        "window": window,
        "per_note": results,
    }


def main():
    # Read NEXT.md (and archive if available)
    text = ""
    if NEXT_MD.exists():
        text += NEXT_MD.read_text()
    if NEXT_ARCHIVE.exists():
        text += "\n" + NEXT_ARCHIVE.read_text()

    notes = parse_session_notes(text)
    # NEXT.md has newest first — reverse to chronological order
    notes.reverse()
    print(f"Parsed {len(notes)} session notes (chronological order)")

    # Filter to notes with predictions
    with_preds = [n for n in notes if n["predictions"]]
    print(f"Notes with predictions: {len(with_preds)}")
    print(f"Total predictions: {sum(len(n['predictions']) for n in with_preds)}")

    # Measure accuracy with different windows
    for window in [1, 3, 5]:
        result = measure_accuracy(notes, window=window)
        print(f"\n=== Window={window} (check next {window} sessions) ===")
        print(f"  Hit rate: {result['overall_hit_rate']:.1%} ({result['total_hits']}/{result['total_predictions']})")
        print(f"  Mean per-session accuracy: {result['mean_session_accuracy']:.1%}")

    # Primary measurement: window=3 (reasonable lookahead for concurrent swarm)
    primary = measure_accuracy(notes, window=3)

    # Analyze by session range
    recent = [r for r in primary["per_note"] if r["session"] >= 350]
    old = [r for r in primary["per_note"] if r["session"] < 350]

    if recent:
        recent_acc = sum(r["accuracy"] for r in recent) / len(recent)
        print(f"\n=== Recent (S350+): {len(recent)} notes, mean accuracy {recent_acc:.1%} ===")
    if old:
        old_acc = sum(r["accuracy"] for r in old) / len(old)
        print(f"=== Older (<S350): {len(old)} notes, mean accuracy {old_acc:.1%} ===")

    # Analyze by concurrency (sessions with same number = high concurrency)
    session_counts = {}
    for n in notes:
        session_counts[n["session"]] = session_counts.get(n["session"], 0) + 1

    high_conc = [r for r in primary["per_note"] if session_counts.get(r["session"], 1) >= 3]
    low_conc = [r for r in primary["per_note"] if session_counts.get(r["session"], 1) < 3]

    if high_conc:
        hc_acc = sum(r["accuracy"] for r in high_conc) / len(high_conc)
        print(f"\n=== High concurrency (N≥3): {len(high_conc)} notes, mean accuracy {hc_acc:.1%} ===")
    if low_conc:
        lc_acc = sum(r["accuracy"] for r in low_conc) / len(low_conc)
        print(f"=== Low concurrency (N<3): {len(low_conc)} notes, mean accuracy {lc_acc:.1%} ===")

    # Top missed predictions (most common predictions that don't match)
    missed = []
    for r in primary["per_note"]:
        for p in r["predictions"]:
            if not p["matched"]:
                missed.append(p["prediction"])

    print(f"\n=== Missed predictions: {len(missed)} total ===")
    # Show sample
    for m in missed[:5]:
        print(f"  - {m[:80]}")

    # Build experiment artifact
    artifact = {
        "experiment": "F-EMP1",
        "session": "S358",
        "date": "2026-03-01",
        "question": "Does handoff quality correlate with empathic accuracy?",
        "method": "Parse NEXT.md predictions vs actual next-session work. Fuzzy matching with term overlap + identifier matching.",
        "n_notes": len(notes),
        "n_with_predictions": len(with_preds),
        "total_predictions": sum(len(n["predictions"]) for n in with_preds),
        "results": {
            "window_1": {
                "hit_rate": measure_accuracy(notes, 1)["overall_hit_rate"],
                "mean_session_accuracy": measure_accuracy(notes, 1)["mean_session_accuracy"],
            },
            "window_3": {
                "hit_rate": primary["overall_hit_rate"],
                "mean_session_accuracy": primary["mean_session_accuracy"],
            },
            "window_5": {
                "hit_rate": measure_accuracy(notes, 5)["overall_hit_rate"],
                "mean_session_accuracy": measure_accuracy(notes, 5)["mean_session_accuracy"],
            },
        },
        "concurrency_effect": {
            "high_n": len(high_conc) if high_conc else 0,
            "high_accuracy": round(sum(r["accuracy"] for r in high_conc) / len(high_conc), 3) if high_conc else None,
            "low_n": len(low_conc) if low_conc else 0,
            "low_accuracy": round(sum(r["accuracy"] for r in low_conc) / len(low_conc), 3) if low_conc else None,
        },
        "recency_effect": {
            "recent_n": len(recent) if recent else 0,
            "recent_accuracy": round(recent_acc, 3) if recent else None,
            "old_n": len(old) if old else 0,
            "old_accuracy": round(old_acc, 3) if old else None,
        },
        "sample_missed": missed[:10] if missed else [],
        "accuracy_distribution": {},
        "sample_matches": [],
        "falsification": "If prediction accuracy >70% but wasted work unchanged, prediction without action = noise",
    }

    # Accuracy distribution
    from collections import Counter
    bins = Counter()
    for r in primary["per_note"]:
        a = r["accuracy"]
        if a == 0: bins["0%"] += 1
        elif a < 0.25: bins["1-24%"] += 1
        elif a < 0.50: bins["25-49%"] += 1
        elif a < 0.75: bins["50-74%"] += 1
        elif a < 1.0: bins["75-99%"] += 1
        else: bins["100%"] += 1
    artifact["accuracy_distribution"] = dict(bins)

    print(f"\n=== Accuracy distribution (n={len(primary['per_note'])}) ===")
    for label in ["0%", "1-24%", "25-49%", "50-74%", "75-99%", "100%"]:
        n = bins.get(label, 0)
        pct = n / len(primary["per_note"]) * 100 if primary["per_note"] else 0
        bar = "#" * int(pct / 2)
        print(f"  {label:>6}: {n:3d} ({pct:4.1f}%) {bar}")

    # Sample successful matches
    matches = []
    for r in primary["per_note"]:
        for p in r["predictions"]:
            if p["matched"]:
                matches.append({"session": r["session"], "prediction": p["prediction"], "score": p["score"]})
    artifact["sample_matches"] = matches[:15]

    print(f"\n=== Sample matched predictions ({len(matches)} total) ===")
    for m in matches[:8]:
        print(f"  S{m['session']} (score={m['score']}): {m['prediction'][:70]}")

    # Write artifact
    artifact_path = Path("experiments/empathy/f-emp1-handoff-accuracy-s358.json")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    with open(artifact_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact written: {artifact_path}")

    # Also dump per-note details for inspection
    print(f"\n=== Per-note accuracy (last 10) ===")
    for r in primary["per_note"][-10:]:
        hits_detail = " ".join("✓" if p["matched"] else "✗" for p in r["predictions"])
        print(f"  S{r['session']} {r['accuracy']:.0%} [{hits_detail}] {r['description'][:50]}")


if __name__ == "__main__":
    main()
