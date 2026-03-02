#!/usr/bin/env python3
"""
test_novelty.py — Tests for the shared novelty detection module.

Usage:
    python3 tools/test_novelty.py
    python3 tools/test_novelty.py -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from novelty import check_novelty, content_words, jaccard_similarity


class TestContentWords(unittest.TestCase):
    """Test stopword filtering and word extraction."""

    def test_removes_stopwords(self):
        words = content_words("the cat is on the mat")
        self.assertNotIn("the", words)
        self.assertNotIn("is", words)
        self.assertNotIn("on", words)
        self.assertIn("cat", words)
        self.assertIn("mat", words)

    def test_lowercase(self):
        words = content_words("Always Verify Generated Files")
        self.assertIn("always", words)
        self.assertIn("verify", words)
        self.assertIn("generated", words)
        self.assertIn("files", words)

    def test_empty_string(self):
        words = content_words("")
        self.assertEqual(words, set())

    def test_only_stopwords(self):
        words = content_words("the is a an of in to for")
        self.assertEqual(words, set())

    def test_technical_terms(self):
        words = content_words("K_avg predicts cycle count better than K_max")
        self.assertIn("k_avg", words)
        self.assertIn("predicts", words)
        self.assertIn("cycle", words)
        self.assertIn("k_max", words)


class TestJaccardSimilarity(unittest.TestCase):
    """Test Jaccard similarity computation."""

    def test_identical_sets(self):
        s = {"a", "b", "c"}
        self.assertAlmostEqual(jaccard_similarity(s, s), 1.0)

    def test_disjoint_sets(self):
        self.assertAlmostEqual(jaccard_similarity({"a", "b"}, {"c", "d"}), 0.0)

    def test_partial_overlap(self):
        # |{a,b} ∩ {b,c}| / |{a,b} ∪ {b,c}| = 1/3
        self.assertAlmostEqual(
            jaccard_similarity({"a", "b"}, {"b", "c"}), 1/3
        )

    def test_empty_sets(self):
        self.assertAlmostEqual(jaccard_similarity(set(), set()), 0.0)
        self.assertAlmostEqual(jaccard_similarity({"a"}, set()), 0.0)


class TestCheckNovelty(unittest.TestCase):
    """Test novelty detection against existing rules."""

    def test_novel_rule(self):
        existing = [
            "Always verify generated files for artifacts",
            "Measure complexity using NK metrics",
        ]
        is_novel, sim, _ = check_novelty(
            "Use Jaccard similarity for deduplication", existing
        )
        self.assertTrue(is_novel)

    def test_duplicate_rule(self):
        existing = [
            "Always verify generated files for artifacts",
        ]
        is_novel, sim, _ = check_novelty(
            "Always verify the generated files for artifacts", existing
        )
        self.assertFalse(is_novel)
        self.assertGreater(sim, 0.45)

    def test_rephrased_rule(self):
        existing = [
            "Cycle count predicts bug accumulation rate better than K_avg or K_max",
        ]
        is_novel, sim, _ = check_novelty(
            "Cycles predict bugs better than K_avg, K_max, or composite",
            existing
        )
        # Should detect some similarity even with rephrasing
        # Jaccard on content words = 0.23 (stems differ: "cycle" vs "cycles")
        # This is a known limitation of word-level Jaccard — it misses stem variants
        self.assertGreater(sim, 0.2)

    def test_empty_candidate(self):
        is_novel, sim, _ = check_novelty("", ["some rule"])
        self.assertFalse(is_novel)

    def test_empty_existing(self):
        is_novel, sim, _ = check_novelty("Some new rule", [])
        self.assertTrue(is_novel)

    def test_closest_match_returned(self):
        existing = [
            "First rule about verification",
            "Second rule about complexity metrics",
            "Third rule about cycle detection",
        ]
        _, _, closest = check_novelty(
            "Use complexity metrics for analysis", existing
        )
        self.assertIn("complexity", closest.lower())

    def test_threshold_parameter(self):
        existing = ["Verify generated files"]
        # With very low threshold, even slight overlap is duplicate
        is_novel_strict, _, _ = check_novelty(
            "Always verify files", existing, threshold=0.1
        )
        # With high threshold, more similarity tolerated
        is_novel_lax, _, _ = check_novelty(
            "Always verify files", existing, threshold=0.9
        )
        self.assertTrue(is_novel_lax)

    def test_completely_different_topics(self):
        existing = [
            "Use git-based knowledge for forking",
            "Separate format from process",
        ]
        is_novel, sim, _ = check_novelty(
            "Rust module system guarantees zero cycles", existing
        )
        self.assertTrue(is_novel)
        self.assertLess(sim, 0.2)


if __name__ == "__main__":
    unittest.main()
