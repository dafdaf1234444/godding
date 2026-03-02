#!/usr/bin/env python3
"""
F-QC1: Repeated Knowledge Detection
Reads all swarm lessons, computes pairwise Jaccard similarity on word sets,
flags near-duplicate pairs (similarity > 0.4), outputs JSON summary.

Usage:
    python3 tools/f_qc1_repeated_knowledge.py
    python3 tools/f_qc1_repeated_knowledge.py --threshold 0.3
    python3 tools/f_qc1_repeated_knowledge.py --output experiments/quality/custom.json
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
DEFAULT_OUTPUT = REPO_ROOT / "experiments" / "quality" / "f-qc1-repeated-knowledge-s189.json"
DEFAULT_THRESHOLD = 0.4


def tokenize(text: str) -> set:
    """Lowercase, strip punctuation, split into word tokens, remove stop words."""
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "and", "or", "but", "if", "in", "on", "at", "to", "for", "of", "by",
        "with", "from", "into", "through", "during", "before", "after",
        "above", "below", "between", "this", "that", "these", "those",
        "it", "its", "not", "no", "nor", "so", "yet", "both", "either",
        "neither", "each", "few", "more", "most", "other", "such",
        "than", "then", "when", "where", "which", "who", "what", "how",
        "all", "any", "every", "some", "as", "about", "up", "out",
    }
    text = text.lower()
    tokens = re.findall(r"[a-z][a-z0-9_\-]*", text)
    return {t for t in tokens if t not in STOP_WORDS and len(t) > 2}


def extract_key_text(lesson_path: Path, n_lines: int = 3) -> str:
    """Extract first n_lines of a lesson file as the representative text."""
    try:
        content = lesson_path.read_text(encoding="utf-8", errors="replace")
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return " ".join(lines[:n_lines])
    except Exception:
        return ""


def jaccard(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def load_lessons(lessons_dir: Path) -> list:
    """Load all L-*.md lessons, return list of (lesson_id, path, word_set)."""
    lessons = []
    for path in sorted(lessons_dir.glob("L-*.md")):
        lesson_id = path.stem  # e.g. "L-001"
        text = extract_key_text(path, n_lines=3)
        words = tokenize(text)
        if words:  # skip empty/unreadable lessons
            lessons.append({"id": lesson_id, "path": str(path), "words": words, "text": text})
    return lessons


def find_near_duplicates(lessons: list, threshold: float) -> list:
    """
    Compute all pairwise Jaccard similarities.
    Return pairs with similarity >= threshold, sorted descending.
    """
    n = len(lessons)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            sim = jaccard(lessons[i]["words"], lessons[j]["words"])
            if sim >= threshold:
                pairs.append({
                    "lesson_a": lessons[i]["id"],
                    "lesson_b": lessons[j]["id"],
                    "similarity": round(sim, 4),
                    "text_a": lessons[i]["text"][:120],
                    "text_b": lessons[j]["text"][:120],
                })
    pairs.sort(key=lambda x: x["similarity"], reverse=True)
    return pairs


def main():
    parser = argparse.ArgumentParser(description="F-QC1: Repeated knowledge detection")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Jaccard similarity threshold (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--lessons-dir",
        type=str,
        default=str(LESSONS_DIR),
        help=f"Lessons directory (default: {LESSONS_DIR})",
    )
    args = parser.parse_args()

    lessons_dir = Path(args.lessons_dir)
    output_path = Path(args.output)
    threshold = args.threshold

    print(f"[F-QC1] Loading lessons from {lessons_dir} ...")
    lessons = load_lessons(lessons_dir)
    total_lessons = len(lessons)
    print(f"[F-QC1] Loaded {total_lessons} lessons.")

    print(f"[F-QC1] Computing pairwise Jaccard similarity (threshold={threshold}) ...")
    near_duplicate_pairs = find_near_duplicates(lessons, threshold)

    # Count unique lessons involved in at least one near-duplicate pair
    lessons_flagged = set()
    for pair in near_duplicate_pairs:
        lessons_flagged.add(pair["lesson_a"])
        lessons_flagged.add(pair["lesson_b"])

    n_pairs = len(near_duplicate_pairs)
    n_flagged = len(lessons_flagged)
    duplication_rate = round(n_flagged / total_lessons, 4) if total_lessons > 0 else 0.0

    top_10 = near_duplicate_pairs[:10]

    result = {
        "session": "S189",
        "date": "2026-02-28",
        "frontier": "F-QC1",
        "threshold": threshold,
        "total_lessons": total_lessons,
        "near_duplicate_pairs": n_pairs,
        "lessons_flagged": n_flagged,
        "duplication_rate": duplication_rate,
        "top_10_similar_pairs": top_10,
        "interpretation": (
            f"{n_pairs} near-duplicate pairs found among {total_lessons} lessons "
            f"({n_flagged} unique lessons flagged = {duplication_rate*100:.1f}% of corpus). "
            "Inspect top_10_similar_pairs for merge candidates."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\n[F-QC1] Results:")
    print(f"  total_lessons:        {total_lessons}")
    print(f"  near_duplicate_pairs: {n_pairs}")
    print(f"  lessons_flagged:      {n_flagged}")
    print(f"  duplication_rate:     {duplication_rate*100:.1f}%")
    print(f"\n[F-QC1] Top 10 most similar pairs:")
    for i, pair in enumerate(top_10, 1):
        print(f"  {i:2d}. {pair['lesson_a']} ↔ {pair['lesson_b']}  sim={pair['similarity']:.4f}")
        print(f"      A: {pair['text_a'][:80]}")
        print(f"      B: {pair['text_b'][:80]}")
    print(f"\n[F-QC1] Output written to: {output_path}")
    return result


if __name__ == "__main__":
    main()
