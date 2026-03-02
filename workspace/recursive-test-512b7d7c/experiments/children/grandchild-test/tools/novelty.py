#!/usr/bin/env python3
"""
novelty.py — Shared novelty detection for child swarm integration.

Used by merge_back.py and evolve.py to determine if a child's rule
is genuinely novel vs. a rephrasing of an existing parent rule.

Algorithm: Jaccard similarity with stopword filtering.
Previous: 60% raw word overlap (brittle, missed semantic duplicates).
Current: Jaccard index on content words with configurable threshold.
"""

import re

# Common English stopwords that don't carry semantic meaning
STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "of", "in", "to",
    "for", "with", "on", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out",
    "but", "not", "no", "nor", "or", "and", "if", "then", "else",
    "when", "up", "so", "than", "too", "very", "just", "about", "also",
    "it", "its", "this", "that", "these", "those", "all", "each",
    "every", "any", "both", "few", "more", "most", "other", "some",
    "such", "only", "own", "same", "don't", "doesn't", "didn't",
    "—", "–", "-", "e.g.", "i.e.", "etc.", "vs",
})

# Default similarity threshold (above this = duplicate)
DEFAULT_THRESHOLD = 0.45


def content_words(text: str) -> set[str]:
    """Extract semantically meaningful words from text."""
    words = set(re.findall(r"[a-z][a-z_/]+", text.lower()))
    return words - STOPWORDS


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity: |A∩B| / |A∪B|."""
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def check_novelty(
    candidate: str,
    existing_rules: set[str] | list[str],
    threshold: float = DEFAULT_THRESHOLD,
) -> tuple[bool, float, str]:
    """Check if a candidate rule is novel against existing rules.

    Args:
        candidate: The candidate rule text to check.
        existing_rules: Set/list of existing rule texts to compare against.
        threshold: Jaccard similarity threshold. Above = duplicate.

    Returns:
        Tuple of (is_novel, max_similarity, closest_match).
        is_novel: True if candidate is novel (below threshold for all existing).
        max_similarity: Highest similarity score found.
        closest_match: The existing rule most similar to candidate.
    """
    if not candidate:
        return False, 0.0, ""

    candidate_words = content_words(candidate)
    if not candidate_words:
        return False, 0.0, ""

    max_sim = 0.0
    closest = ""

    for rule in existing_rules:
        rule_words = content_words(rule)
        sim = jaccard_similarity(candidate_words, rule_words)
        if sim > max_sim:
            max_sim = sim
            closest = rule

    return max_sim < threshold, max_sim, closest


def load_parent_rules(principles_path) -> list[str]:
    """Load parent's existing principles as a list of rule texts."""
    from pathlib import Path
    principles = Path(principles_path)
    if not principles.exists():
        return []
    text = principles.read_text()
    return [
        m.group(1).strip()
        for m in re.finditer(r"\*\*P-\d+\*\*:\s*(.+?)(?:\(L-|\(from|\Z)", text)
    ]
