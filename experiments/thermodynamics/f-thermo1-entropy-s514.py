#!/usr/bin/env python3
"""F-THERMO1: Shannon entropy of lesson corpus across session milestones.

Measures character-level and word-level Shannon entropy at S100, S199, S300, S400, S500, S513.
Tests: does entropy per lesson increase monotonically? R² > 0.3 on linear fit?

Pre-registered prediction: entropy per lesson increases monotonically (disorder accumulates).
Falsification: R² < 0.3 — thermodynamic analogy adds no predictive power.
"""

import json
import math
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

MILESTONES = [
    ("S100", "c4b2ff47"),
    ("S199", "62eb5cf6"),
    ("S300", "e1eb559b"),
    ("S400", "6d430ff9"),
    ("S500", "782bb06f"),
    ("S513", "HEAD"),
]


def get_lesson_texts_at_commit(commit_hash):
    """Get all lesson file contents at a specific commit."""
    try:
        # List lesson files at commit
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit_hash, "--", "memory/lessons/"],
            capture_output=True, text=True, timeout=30
        )
        files = [f for f in result.stdout.strip().split("\n") if f.endswith(".md") and f]

        texts = []
        for f in files:
            try:
                content = subprocess.run(
                    ["git", "show", f"{commit_hash}:{f}"],
                    capture_output=True, text=True, timeout=10
                )
                if content.returncode == 0 and content.stdout.strip():
                    texts.append(content.stdout)
            except subprocess.TimeoutExpired:
                continue
        return texts
    except Exception as e:
        print(f"  Error at {commit_hash}: {e}", file=sys.stderr)
        return []


def shannon_entropy_chars(text):
    """Character-level Shannon entropy in bits."""
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)


def shannon_entropy_words(text):
    """Word-level Shannon entropy in bits."""
    words = text.lower().split()
    if not words:
        return 0.0
    counts = Counter(words)
    total = len(words)
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)


def vocab_richness(text):
    """Type-token ratio — vocabulary diversity."""
    words = text.lower().split()
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def linear_regression(xs, ys):
    """Simple OLS: returns slope, intercept, R²."""
    n = len(xs)
    if n < 2:
        return 0, 0, 0
    mx = sum(xs) / n
    my = sum(ys) / n
    ss_xy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    ss_xx = sum((x - mx) ** 2 for x in xs)
    ss_yy = sum((y - my) ** 2 for y in ys)
    if ss_xx == 0 or ss_yy == 0:
        return 0, my, 0
    slope = ss_xy / ss_xx
    intercept = my - slope * mx
    r_sq = (ss_xy ** 2) / (ss_xx * ss_yy)
    return slope, intercept, r_sq


def main():
    results = []
    print("=== F-THERMO1: Shannon Entropy Across Session Milestones ===\n")

    for session, commit in MILESTONES:
        print(f"Processing {session} ({commit[:8]})...")
        texts = get_lesson_texts_at_commit(commit)
        n_lessons = len(texts)

        if n_lessons == 0:
            print(f"  No lessons found at {session}")
            continue

        # Concatenate all text
        corpus = "\n".join(texts)
        total_chars = len(corpus)
        total_words = len(corpus.split())

        # Per-lesson entropy (average)
        char_entropies = [shannon_entropy_chars(t) for t in texts]
        word_entropies = [shannon_entropy_words(t) for t in texts]
        vocab_ratios = [vocab_richness(t) for t in texts]

        avg_char_h = sum(char_entropies) / n_lessons
        avg_word_h = sum(word_entropies) / n_lessons
        avg_vocab = sum(vocab_ratios) / n_lessons

        # Corpus-level entropy
        corpus_char_h = shannon_entropy_chars(corpus)
        corpus_word_h = shannon_entropy_words(corpus)
        corpus_vocab = vocab_richness(corpus)

        result = {
            "session": session,
            "commit": commit[:8],
            "n_lessons": n_lessons,
            "total_chars": total_chars,
            "total_words": total_words,
            "avg_char_entropy_bits": round(avg_char_h, 4),
            "avg_word_entropy_bits": round(avg_word_h, 4),
            "avg_vocab_richness": round(avg_vocab, 4),
            "corpus_char_entropy_bits": round(corpus_char_h, 4),
            "corpus_word_entropy_bits": round(corpus_word_h, 4),
            "corpus_vocab_richness": round(corpus_vocab, 4),
        }
        results.append(result)
        print(f"  {n_lessons} lessons | char H={avg_char_h:.3f} | word H={avg_word_h:.3f} | vocab={avg_vocab:.3f}")
        print(f"  corpus: char H={corpus_char_h:.3f} | word H={corpus_word_h:.3f} | vocab={corpus_vocab:.3f}")

    if len(results) < 3:
        print("\nInsufficient data points for trend analysis.")
        return

    # Trend analysis
    print("\n=== Trend Analysis ===")
    sessions_numeric = list(range(len(results)))

    # Per-lesson char entropy trend
    avg_char_hs = [r["avg_char_entropy_bits"] for r in results]
    slope_c, _, r2_c = linear_regression(sessions_numeric, avg_char_hs)
    print(f"Avg char entropy trend: slope={slope_c:.4f}, R²={r2_c:.4f}")

    # Per-lesson word entropy trend
    avg_word_hs = [r["avg_word_entropy_bits"] for r in results]
    slope_w, _, r2_w = linear_regression(sessions_numeric, avg_word_hs)
    print(f"Avg word entropy trend: slope={slope_w:.4f}, R²={r2_w:.4f}")

    # Corpus-level word entropy trend
    corpus_word_hs = [r["corpus_word_entropy_bits"] for r in results]
    slope_cw, _, r2_cw = linear_regression(sessions_numeric, corpus_word_hs)
    print(f"Corpus word entropy trend: slope={slope_cw:.4f}, R²={r2_cw:.4f}")

    # Vocab richness trend (expect decrease — more words reused as corpus grows)
    corpus_vocabs = [r["corpus_vocab_richness"] for r in results]
    slope_v, _, r2_v = linear_regression(sessions_numeric, corpus_vocabs)
    print(f"Corpus vocab richness trend: slope={slope_v:.4f}, R²={r2_v:.4f}")

    # Monotonicity check
    monotonic_char = all(avg_char_hs[i] <= avg_char_hs[i + 1] for i in range(len(avg_char_hs) - 1))
    monotonic_word = all(avg_word_hs[i] <= avg_word_hs[i + 1] for i in range(len(avg_word_hs) - 1))
    print(f"\nMonotonic increase? char={monotonic_char}, word={monotonic_word}")

    # Verdict
    print("\n=== Verdict ===")
    if r2_c >= 0.3 or r2_w >= 0.3:
        verdict = "SUPPORTED"
        detail = f"Entropy trend R² ≥ 0.3 (char: {r2_c:.3f}, word: {r2_w:.3f}). Thermodynamic analogy has predictive power."
    else:
        verdict = "FALSIFIED"
        detail = f"Entropy trend R² < 0.3 (char: {r2_c:.3f}, word: {r2_w:.3f}). No monotonic entropy increase — thermodynamic analogy adds no predictive power beyond 'corpus grows.'"

    if monotonic_char or monotonic_word:
        detail += " Monotonic increase detected in at least one measure."
    else:
        detail += " No monotonic increase — 2nd law analog does NOT hold."

    print(f"{verdict}: {detail}")

    # Compaction effect: look for entropy dips
    dips = []
    for i in range(1, len(corpus_word_hs)):
        if corpus_word_hs[i] < corpus_word_hs[i - 1]:
            dips.append((results[i - 1]["session"], results[i]["session"]))
    if dips:
        print(f"Entropy dips (Maxwell's demon signature): {dips}")
    else:
        print("No corpus entropy dips detected — no Maxwell's demon signature.")

    # Save artifact
    artifact = {
        "experiment": "F-THERMO1",
        "session": "S514",
        "date": "2026-03-23",
        "prediction": "Entropy per lesson increases monotonically; R² > 0.3",
        "falsification": "R² < 0.3 on linear fit",
        "measurements": results,
        "trends": {
            "avg_char_entropy": {"slope": round(slope_c, 4), "r_squared": round(r2_c, 4)},
            "avg_word_entropy": {"slope": round(slope_w, 4), "r_squared": round(r2_w, 4)},
            "corpus_word_entropy": {"slope": round(slope_cw, 4), "r_squared": round(r2_cw, 4)},
            "corpus_vocab_richness": {"slope": round(slope_v, 4), "r_squared": round(r2_v, 4)},
        },
        "monotonic": {"char": monotonic_char, "word": monotonic_word},
        "dips": dips,
        "verdict": verdict,
        "detail": detail,
    }

    out_path = Path("experiments/thermodynamics/f-thermo1-entropy-s514.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact saved: {out_path}")


if __name__ == "__main__":
    main()
